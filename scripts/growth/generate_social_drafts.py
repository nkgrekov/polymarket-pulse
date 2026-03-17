#!/usr/bin/env python3
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import psycopg
from psycopg.rows import dict_row

SQL_MOVERS = """
with latest_liquidity as (
    select
        ms.market_id,
        max(ms.liquidity) as liquidity
    from public.market_snapshots ms
    join public.global_bucket_latest g on g.last_bucket = ms.ts_bucket
    group by ms.market_id
)
select
    t.market_id,
    t.question,
    t.delta_yes,
    t.yes_mid_prev,
    t.yes_mid_now,
    t.prev_bucket,
    t.last_bucket,
    coalesce(ll.liquidity, 0) as liquidity
from public.top_movers_latest t
left join latest_liquidity ll using (market_id)
where abs(t.delta_yes) >= %s
  and t.last_bucket >= (now() - make_interval(mins => %s))
  and coalesce(ll.liquidity, 0) >= %s
order by abs(t.delta_yes) desc nulls last, coalesce(ll.liquidity, 0) desc nulls last
limit %s;
"""

SQL_ALERTS = """
with latest_liquidity as (
    select
        ms.market_id,
        max(ms.liquidity) as liquidity
    from public.market_snapshots ms
    join public.global_bucket_latest g on g.last_bucket = ms.ts_bucket
    group by ms.market_id
)
select
    a.question,
    a.market_id,
    a.delta_mid,
    a.mid_prev,
    a.mid_now,
    a.prev_bucket,
    a.last_bucket,
    a.abs_delta,
    coalesce(ll.liquidity, 0) as liquidity
from bot.alerts_inbox_latest a
left join latest_liquidity ll using (market_id)
where a.abs_delta >= %s
  and a.mid_prev is not null
  and a.mid_now is not null
  and a.last_bucket >= (now() - make_interval(mins => %s))
  and coalesce(ll.liquidity, 0) >= %s
order by a.abs_delta desc nulls last, coalesce(ll.liquidity, 0) desc nulls last
limit %s;
"""


def fmt_pct(v: object) -> str:
    if v is None:
        return "n/a"
    return f"{float(v) * 100:.1f}%"


def fmt_delta(v: object) -> str:
    if v is None:
        return "n/a"
    return f"{float(v) * 100:+.1f}pp"


def estimate_window(prev_bucket, last_bucket) -> str:
    if prev_bucket is None or last_bucket is None:
        return "live window"
    minutes = int((last_bucket - prev_bucket).total_seconds() // 60)
    return f"{max(minutes, 1)}m window"


def truncate_question(text: str, limit: int = 88) -> str:
    raw = (text or "").strip()
    if len(raw) <= limit:
        return raw
    return raw[: limit - 1].rstrip() + "…"


def build_links(base_url: str, *, channel: str, lang: str, campaign: str) -> tuple[str, str]:
    params = urlencode(
        {
            "utm_source": channel,
            "utm_medium": "social",
            "utm_campaign": campaign,
            "lang": lang,
            "placement": f"{channel}_{campaign}",
        }
    )
    site_link = f"{base_url.rstrip('/')}/?{params}"
    bot_link = f"https://t.me/polymarket_pulse_bot?start={channel}_{campaign}_{lang}"
    return site_link, bot_link


def hashtags(lang: str, channel: str) -> str:
    if lang == "ru":
        core = "#Polymarket #PredictionMarkets #Крипто #Трейдинг"
    else:
        core = "#Polymarket #PredictionMarkets #Crypto #TradingSignals"
    if channel == "threads":
        return core + " #Threads"
    return core + " #X"


def fmt_liquidity(v: object) -> str:
    if v is None:
        return "n/a"
    try:
        value = float(v)
    except (TypeError, ValueError):
        return "n/a"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.0f}"


def parse_csv_choices(raw: str, *, allowed: set[str], name: str) -> list[str]:
    values = [v.strip().lower() for v in (raw or "").split(",") if v.strip()]
    if not values:
        raise SystemExit(f"{name} is empty")
    bad = [v for v in values if v not in allowed]
    if bad:
        raise SystemExit(f"Unsupported {name}: {', '.join(sorted(set(bad)))}")
    # Keep order, deduplicate.
    return list(dict.fromkeys(values))


def post_from_mover(row: dict, *, lang: str, channel: str, base_url: str, campaign: str = "live_movers") -> str:
    question = truncate_question(row.get("question") or "Unknown market")
    prev = fmt_pct(row.get("yes_mid_prev"))
    now = fmt_pct(row.get("yes_mid_now"))
    delta = fmt_delta(row.get("delta_yes"))
    window = estimate_window(row.get("prev_bucket"), row.get("last_bucket"))
    liq = fmt_liquidity(row.get("liquidity"))
    site_link, bot_link = build_links(base_url, channel=channel, lang=lang, campaign=campaign)
    tags = hashtags(lang, channel)
    if lang == "ru":
        return (
            f"Рынок резко сдвинулся: {question}\n"
            f"Вероятность: {prev} -> {now} ({delta}, {window}, L {liq})\n"
            "Почему это важно: движение вышло за шумовой диапазон.\n"
            f"Bot: {bot_link}\n"
            f"Site: {site_link}\n"
            f"{tags}"
        )
    return (
        f"Market moved fast: {question}\n"
        f"Probability: {prev} -> {now} ({delta}, {window}, L {liq})\n"
        "Why it matters: action-first signal, not dashboard noise.\n"
        f"Bot: {bot_link}\n"
        f"Site: {site_link}\n"
        f"{tags}"
    )


def post_from_alert(row: dict, *, lang: str, channel: str, base_url: str) -> str:
    question = truncate_question(row.get("question") or "Unknown market")
    prev = fmt_pct(row.get("mid_prev"))
    now = fmt_pct(row.get("mid_now"))
    delta = fmt_delta(row.get("delta_mid"))
    window = estimate_window(row.get("prev_bucket"), row.get("last_bucket"))
    liq = fmt_liquidity(row.get("liquidity"))
    site_link, bot_link = build_links(base_url, channel=channel, lang=lang, campaign="breakout")
    tags = hashtags(lang, channel)
    if lang == "ru":
        return (
            f"Breakout market: {question}\n"
            f"Движение: {prev} -> {now} ({delta}, {window}, L {liq})\n"
            "Контекст: сигнал из live inbox.\n"
            f"Bot: {bot_link}\n"
            f"Site: {site_link}\n"
            f"{tags}"
        )
    return (
        f"Breakout market: {question}\n"
        f"Move: {prev} -> {now} ({delta}, {window}, L {liq})\n"
        "Context: live-only move with thresholded signal quality.\n"
        f"Bot: {bot_link}\n"
        f"Site: {site_link}\n"
        f"{tags}"
    )


def render_block(
    *,
    lang: str,
    channel: str,
    movers: list[dict],
    alerts: list[dict],
    base_url: str,
) -> list[str]:
    label = f"{channel.upper()} - {lang.upper()}"
    lines: list[str] = [f"## {label}", ""]

    if not movers and not alerts:
        lines += ["No non-zero live data in this window. Skip posting.", ""]
        return lines

    if movers:
        for i, row in enumerate(movers, start=1):
            lines += [
                f"### Top Movers Post {i}",
                "",
                post_from_mover(row, lang=lang, channel=channel, base_url=base_url, campaign="live_movers"),
                "",
            ]

    if alerts:
        for i, row in enumerate(alerts, start=1):
            lines += [
                f"### Single-Market Breakout {i}",
                "",
                post_from_alert(row, lang=lang, channel=channel, base_url=base_url),
                "",
            ]
    elif movers:
        lines += [
            "### Single-Market Breakout 1",
            "",
            post_from_mover(movers[0], lang=lang, channel=channel, base_url=base_url, campaign="breakout"),
            "",
        ]

    weekly_site, weekly_bot = build_links(base_url, channel=channel, lang=lang, campaign="weekly_recap")
    if lang == "ru":
        recap = (
            "### Weekly Recap Skeleton\n\n"
            "Главные сдвиги недели: [вставьте 3 маркета и 1 тезис].\n"
            "Bot: " + weekly_bot + "\n"
            "Site: " + weekly_site + "\n"
            + hashtags(lang, channel)
            + "\n"
        )
    else:
        recap = (
            "### Weekly Recap Skeleton\n\n"
            "Week recap: [insert top 3 shifts + one interpretation line].\n"
            "Bot: " + weekly_bot + "\n"
            "Site: " + weekly_site + "\n"
            + hashtags(lang, channel)
            + "\n"
        )
    lines += [recap, ""]
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate social draft posts from DB live views")
    parser.add_argument("--output", default="docs/social_drafts_latest.md", help="Output markdown path")
    parser.add_argument("--movers", type=int, default=3, help="Number of top movers to include")
    parser.add_argument("--alerts", type=int, default=2, help="Number of alert breakout posts")
    parser.add_argument(
        "--min-abs-delta",
        type=float,
        default=0.01,
        help="Minimum absolute delta to include (0.01 = 1 percentage point)",
    )
    parser.add_argument(
        "--max-age-minutes",
        type=int,
        default=30,
        help="Maximum age of the latest bucket in minutes before draft candidates are considered stale",
    )
    parser.add_argument(
        "--min-liquidity",
        type=float,
        default=5000.0,
        help="Minimum latest-bucket liquidity required for social candidates",
    )
    parser.add_argument(
        "--langs",
        default="en",
        help="Comma-separated languages (en,ru). Default: en",
    )
    parser.add_argument(
        "--channels",
        default="x,threads",
        help="Comma-separated channels (x,threads). Default: x,threads",
    )
    parser.add_argument("--base-url", default="https://polymarketpulse.app", help="Base URL for UTM links")
    args = parser.parse_args()
    langs = parse_csv_choices(args.langs, allowed={"en", "ru"}, name="langs")
    channels = parse_csv_choices(args.channels, allowed={"x", "threads"}, name="channels")

    pg = os.environ.get("PG_CONN", "")
    if not pg:
        raise SystemExit("PG_CONN is required")

    with psycopg.connect(pg, connect_timeout=10) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(SQL_MOVERS, (args.min_abs_delta, args.max_age_minutes, args.min_liquidity, args.movers))
            movers = cur.fetchall()
            cur.execute(SQL_ALERTS, (args.min_abs_delta, args.max_age_minutes, args.min_liquidity, args.alerts))
            alerts = cur.fetchall()

    now = datetime.now(timezone.utc).isoformat()
    lines = [
        f"# Social Drafts ({now})",
        "",
        "Generated from: `public.top_movers_latest` + `bot.alerts_inbox_latest`",
        f"Freshness gate: <= {args.max_age_minutes}m | Liquidity gate: >= {fmt_liquidity(args.min_liquidity)}",
        f"Mode: langs={','.join(langs)} | channels={','.join(channels)}",
        "",
    ]
    for lang in langs:
        for channel in channels:
            lines += render_block(lang=lang, channel=channel, movers=movers, alerts=alerts, base_url=args.base_url)

    p = Path(args.output)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines), encoding="utf-8")
    print(str(p))


if __name__ == "__main__":
    main()
