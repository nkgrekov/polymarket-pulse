#!/usr/bin/env python3
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

SQL_QUEUE = """
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


def fmt_pct(v: object) -> str:
    if v is None:
        return "n/a"
    return f"{float(v) * 100:.1f}%"


def fmt_delta(v: object) -> str:
    if v is None:
        return "n/a"
    return f"{float(v) * 100:+.1f}pp"


def fmt_liquidity(v: object) -> str:
    if v is None:
        return "n/a"
    value = float(v)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.0f}"


def fmt_window(prev_bucket, last_bucket) -> str:
    if prev_bucket is None or last_bucket is None:
        return "live window"
    minutes = int((last_bucket - prev_bucket).total_seconds() // 60)
    return f"{max(minutes, 1)}m window"


def truncate(text: str, limit: int = 120) -> str:
    raw = (text or "").strip()
    if len(raw) <= limit:
        return raw
    return raw[: limit - 1].rstrip() + "…"


def mover_line(row: dict) -> str:
    return (
        f"{truncate(row.get('question') or 'Unknown market')}\n"
        f"{fmt_pct(row.get('yes_mid_prev'))} -> {fmt_pct(row.get('yes_mid_now'))} "
        f"({fmt_delta(row.get('delta_yes'))}, {fmt_window(row.get('prev_bucket'), row.get('last_bucket'))}, "
        f"L {fmt_liquidity(row.get('liquidity'))})"
    )


def manual_tabs_post(row: dict) -> str:
    return (
        "Most Polymarket workflows are still too manual.\n\n"
        "By the time you notice a move, it usually isn't discovery anymore. "
        "It's confirmation that your tab stack was too slow.\n\n"
        "Current live example:\n"
        f"{mover_line(row)}\n\n"
        "We'd rather answer three things fast:\n"
        "- what moved\n"
        "- by how much\n"
        "- whether it still matters\n\n"
        "Track repricing in Telegram: https://t.me/polymarket_pulse_bot?start=social_manual_tabs\n"
        "Landing: https://polymarketpulse.app/telegram-bot?utm_source=x&utm_medium=social&utm_campaign=manual_workflow_pain"
    )


def alert_fatigue_post(row: dict) -> str:
    return (
        "If your alert feed cries wolf all day, you stop trusting it.\n\n"
        "That is the real problem with most signal products.\n\n"
        "Live move that deserves attention right now:\n"
        f"{mover_line(row)}\n\n"
        "More alerts is not better.\n"
        "Thresholds, dedup, and honest quiet states matter more than volume.\n\n"
        "Signals page: https://polymarketpulse.app/signals?utm_source=x&utm_medium=social&utm_campaign=alert_fatigue\n"
        "Telegram bot: https://t.me/polymarket_pulse_bot?start=social_alert_fatigue"
    )


def dashboard_overload_post(row: dict) -> str:
    return (
        "The issue with most Polymarket dashboards isn't lack of data.\n"
        "It's too much browsing.\n\n"
        "You do not need another screen full of widgets.\n"
        "You need one clear answer:\n"
        "- what moved\n"
        "- by how much\n"
        "- does it matter now\n\n"
        "Current live example:\n"
        f"{mover_line(row)}\n\n"
        "That is the workflow we're building into Telegram.\n\n"
        "Dashboard alternative: https://polymarketpulse.app/dashboard?utm_source=x&utm_medium=social&utm_campaign=dashboard_overload"
    )


def threads_variant(row: dict) -> str:
    return (
        "A lot of Polymarket friction is still workflow friction.\n\n"
        "You keep too many tabs open, notice a move late, and only then realize it would've mattered earlier.\n\n"
        "Live example:\n"
        f"{mover_line(row)}\n\n"
        "We're building around a smaller question:\n"
        "what moved, by how much, and does it matter right now?\n\n"
        "Telegram flow here:\n"
        "https://polymarketpulse.app/telegram-bot?utm_source=threads&utm_medium=social&utm_campaign=manual_workflow_pain"
    )


def render_queue(rows: list[dict], *, generated_at: str, max_age_minutes: int, min_liquidity: float) -> str:
    lines: list[str] = [
        f"# Social Queue ({generated_at})",
        "",
        f"Freshness gate: <= {max_age_minutes}m | Liquidity gate: >= {fmt_liquidity(min_liquidity)}",
        "",
    ]
    if not rows:
        lines += [
            "## Status",
            "",
            "No fresh/liquid movers passed the current gate.",
            "Correct action: skip posting and regenerate later.",
            "",
        ]
        return "\n".join(lines)

    first = rows[0]
    second = rows[1] if len(rows) > 1 else rows[0]
    third = rows[2] if len(rows) > 2 else rows[0]

    lines += [
        "## Posting Order",
        "",
        "1. X now — Manual Tabs Pain",
        "2. Threads mirror — Manual Tabs Pain",
        "3. X later — Alert Fatigue",
        "4. X optional evening post — Dashboard Overload",
        "",
        "## Slot 1 — X now",
        "",
        f"Attach video: `/Users/nikitagrekov/polymarket-pulse/assets/social/out/manual-tabs-pain-5s.mp4`",
        "",
        manual_tabs_post(first),
        "",
        "## Slot 2 — Threads mirror",
        "",
        f"Attach video: `/Users/nikitagrekov/polymarket-pulse/assets/social/out/manual-tabs-pain-5s.mp4`",
        "",
        threads_variant(first),
        "",
        "## Slot 3 — X later",
        "",
        f"Attach video: `/Users/nikitagrekov/polymarket-pulse/assets/social/out/alert-fatigue-5s.mp4`",
        "",
        alert_fatigue_post(second),
        "",
        "## Slot 4 — X optional evening",
        "",
        f"Attach video: `/Users/nikitagrekov/polymarket-pulse/assets/social/out/dashboard-overload-5s.mp4`",
        "",
        dashboard_overload_post(third),
        "",
        "## Rule",
        "",
        "Regenerate this file before every posting block. If the top queue is stale or thin, skip posting instead of forcing content.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a fresh daily social posting queue from live movers")
    parser.add_argument("--min-delta", type=float, default=0.02)
    parser.add_argument("--max-age-minutes", type=int, default=30)
    parser.add_argument("--min-liquidity", type=float, default=5000)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--output", default="docs/social_queue_latest.md")
    args = parser.parse_args()

    pg_conn = os.environ.get("PG_CONN", "")
    if not pg_conn:
        raise SystemExit("PG_CONN is required")

    with psycopg.connect(pg_conn, connect_timeout=10) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                SQL_QUEUE,
                (args.min_delta, args.max_age_minutes, args.min_liquidity, args.limit),
            )
            rows = list(cur.fetchall())

    generated_at = datetime.now(timezone.utc).isoformat()
    content = render_queue(
        rows,
        generated_at=generated_at,
        max_age_minutes=args.max_age_minutes,
        min_liquidity=args.min_liquidity,
    )
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
