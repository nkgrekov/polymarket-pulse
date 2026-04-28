#!/usr/bin/env python3
import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

SQL_FUNNEL = """
with events as (
  select
    event_type,
    created_at,
    coalesce(nullif(details->>'utm_source', ''), source, 'unknown') as utm_source,
    coalesce(nullif(details->>'placement', ''), 'unknown') as placement,
    coalesce(details->>'surface_impression', 'false') as surface_impression
  from app.site_events
  where created_at >= %s
)
select
  event_type,
  count(*)::bigint as events
from events
where not (event_type = 'page_view' and surface_impression = 'true')
group by event_type
order by events desc, event_type;
"""

SQL_SOURCE_SPLIT = """
with events as (
  select
    coalesce(nullif(details->>'utm_source', ''), source, 'unknown') as utm_source
  from app.site_events
  where created_at >= %s
    and event_type = 'tg_click'
)
select
  utm_source,
  count(*)::bigint as clicks
from events
group by utm_source
order by clicks desc, utm_source;
"""

SQL_TG_START_SPLIT = """
select
  coalesce(nullif(details->>'start_payload', ''), nullif(details->>'entrypoint', ''), 'direct') as start_source,
  count(*)::bigint as starts
from app.site_events
where created_at >= %s
  and event_type = 'tg_start'
group by start_source
order by starts desc, start_source;
"""

SQL_WATCHLIST_ADD = """
select
  count(*)::bigint as watchlist_add_events,
  count(distinct nullif(details->>'app_user_id', ''))::bigint as watchlist_add_users,
  count(
    distinct case
      when coalesce(details->>'site_attributed_start', 'false') = 'true'
      then nullif(details->>'app_user_id', '')
      else null
    end
  )::bigint as site_watchlist_add_users,
  count(
    distinct case
      when coalesce(details->>'first_watchlist_add', 'false') = 'true'
      then nullif(details->>'app_user_id', '')
      else null
    end
  )::bigint as first_watchlist_add_users
from app.site_events
where created_at >= %s
  and event_type = 'watchlist_add';
"""

SQL_TOP_PLACEMENTS = """
select
  coalesce(nullif(details->>'placement', ''), 'unknown') as placement,
  count(*)::bigint as clicks
from app.site_events
where created_at >= %s
  and event_type = 'tg_click'
group by placement
order by clicks desc, placement
limit %s;
"""

SQL_CTA_SURFACES = """
with surfaces as (
  select * from (values
    ('hero_panel'),
    ('proof_bridge'),
    ('seo_bridge'),
    ('mobile_sticky')
  ) as s(placement)
),
impressions as (
  select
    coalesce(nullif(details->>'placement', ''), 'unknown') as placement,
    count(*)::bigint as seen
  from app.site_events
  where created_at >= %s
    and event_type = 'page_view'
    and coalesce(details->>'surface_impression', 'false') = 'true'
  group by placement
),
clicks as (
  select
    coalesce(nullif(details->>'placement', ''), 'unknown') as placement,
    count(*)::bigint as clicks
  from app.site_events
  where created_at >= %s
    and event_type = 'tg_click'
  group by placement
)
select
  surfaces.placement,
  coalesce(impressions.seen, 0)::bigint as seen,
  coalesce(clicks.clicks, 0)::bigint as clicks
from surfaces
left join impressions using (placement)
left join clicks using (placement)
order by surfaces.placement;
"""

SQL_BOT_ACTIVATION = """
with tg as (
  select count(*)::bigint as started_users
  from app.identities
  where provider = 'telegram'
    and created_at >= %s
),
wl as (
  select count(distinct user_id)::bigint as users_with_watchlist_add
  from bot.watchlist
  where created_at >= %s
)
select
  tg.started_users,
  wl.users_with_watchlist_add
from tg, wl;
"""

SQL_CORE_HEALTH = """
select
  latest_bucket_lag_seconds,
  latest_yes_coverage_pct,
  universe_count,
  latest_universe_coverage,
  prev_universe_coverage,
  movers_latest_nonzero,
  movers_1h_nonzero,
  movers_24h_nonzero
from public.analytics_core_health_latest
limit 1;
"""


def pct(num: float, den: float) -> str:
    if den <= 0:
        return "n/a"
    return f"{(num / den) * 100:.1f}%"


def to_map(rows: list[dict], key: str, value: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        out[str(row.get(key))] = int(row.get(value) or 0)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate weekly growth KPI report from DB")
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days")
    parser.add_argument("--top-placements", type=int, default=8, help="Top TG click placements to show")
    parser.add_argument("--output", default="docs/growth_kpi_latest.md", help="Output markdown path")
    args = parser.parse_args()

    pg = os.environ.get("PG_CONN", "")
    if not pg:
        raise SystemExit("PG_CONN is required")

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=max(args.days, 1))

    with psycopg.connect(pg, connect_timeout=10) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(SQL_FUNNEL, (since,))
            funnel_rows = cur.fetchall()
            cur.execute(SQL_SOURCE_SPLIT, (since,))
            source_rows = cur.fetchall()
            cur.execute(SQL_TG_START_SPLIT, (since,))
            tg_start_rows = cur.fetchall()
            cur.execute(SQL_WATCHLIST_ADD, (since,))
            watchlist_add_row = cur.fetchone() or {
                "watchlist_add_events": 0,
                "watchlist_add_users": 0,
                "site_watchlist_add_users": 0,
                "first_watchlist_add_users": 0,
            }
            cur.execute(SQL_TOP_PLACEMENTS, (since, args.top_placements))
            placement_rows = cur.fetchall()
            cur.execute(SQL_CTA_SURFACES, (since, since))
            cta_surface_rows = cur.fetchall()
            cur.execute(SQL_BOT_ACTIVATION, (since, since))
            activation_row = cur.fetchone() or {"started_users": 0, "users_with_watchlist_add": 0}
            cur.execute(SQL_CORE_HEALTH)
            core_health_row = cur.fetchone() or {}

    funnel = to_map(funnel_rows, "event_type", "events")
    sources = to_map(source_rows, "utm_source", "clicks")
    tg_start_sources = to_map(tg_start_rows, "start_source", "starts")
    site_tg_start = sum(starts for source, starts in tg_start_sources.items() if source.startswith("site_"))

    page_view = funnel.get("page_view", 0)
    tg_click = funnel.get("tg_click", 0)
    tg_start = funnel.get("tg_start", 0)
    live_board_impression = funnel.get("live_board_impression", 0)
    watchlist_add_click = funnel.get("watchlist_add_click", 0)
    watchlist_add_success = funnel.get("watchlist_add_success", 0)
    telegram_login_click = funnel.get("telegram_login_click", 0)
    bell_click = funnel.get("bell_click", 0)
    site_login_completed = funnel.get("site_login_completed", 0)
    alert_setup_started = funnel.get("alert_setup_started", 0)
    alert_enabled = funnel.get("alert_enabled", 0)
    alert_sent = funnel.get("alert_sent", 0)
    alert_click_back_to_site = funnel.get("alert_click_back_to_site", 0)
    pricing_seen = funnel.get("pricing_seen", 0)
    pricing_cta_click = funnel.get("pricing_cta_click", 0)
    watchlist_add_events = int(watchlist_add_row.get("watchlist_add_events") or 0)
    watchlist_add_users = int(watchlist_add_row.get("watchlist_add_users") or 0)
    site_watchlist_add_users = int(watchlist_add_row.get("site_watchlist_add_users") or 0)
    first_watchlist_add_users = int(watchlist_add_row.get("first_watchlist_add_users") or 0)
    waitlist_submit = funnel.get("waitlist_submit", 0)
    confirm_success = funnel.get("confirm_success", 0)
    started_users = int(activation_row.get("started_users") or 0)
    watchlist_add_users_proxy = int(activation_row.get("users_with_watchlist_add") or 0)
    latest_bucket_lag_seconds = int(core_health_row.get("latest_bucket_lag_seconds") or 0)
    latest_yes_coverage_pct = float(core_health_row.get("latest_yes_coverage_pct") or 0.0)
    universe_count = int(core_health_row.get("universe_count") or 0)
    latest_universe_coverage = int(core_health_row.get("latest_universe_coverage") or 0)
    prev_universe_coverage = int(core_health_row.get("prev_universe_coverage") or 0)
    movers_latest_nonzero = int(core_health_row.get("movers_latest_nonzero") or 0)
    movers_1h_nonzero = int(core_health_row.get("movers_1h_nonzero") or 0)
    movers_24h_nonzero = int(core_health_row.get("movers_24h_nonzero") or 0)

    lines: list[str] = [
        f"# Growth KPI Report ({now.isoformat()})",
        "",
        f"Window: `{since.isoformat()}` -> `{now.isoformat()}` (`{args.days}d`)",
        "",
        "## Funnel",
        "",
        f"- page_view: **{page_view}**",
        f"- tg_click: **{tg_click}** (`{pct(tg_click, page_view)}` from page_view)",
        f"- tg_start (all entrypoints): **{tg_start}**",
        f"- tg_start from site payloads: **{site_tg_start}** (`{pct(site_tg_start, tg_click)}` from tg_click)",
        f"- watchlist_add events: **{watchlist_add_events}**",
        f"- watchlist_add users: **{watchlist_add_users}** (`{pct(watchlist_add_users, tg_start)}` from all tg_start)",
        f"- watchlist_add users from site-attributed starts: **{site_watchlist_add_users}** (`{pct(site_watchlist_add_users, site_tg_start)}` from site-attributed tg_start)",
        f"- first_watchlist_add users: **{first_watchlist_add_users}** (`{pct(first_watchlist_add_users, tg_start)}` from tg_start)",
        f"- waitlist_submit: **{waitlist_submit}** (`{pct(waitlist_submit, page_view)}` from page_view)",
        f"- confirm_success: **{confirm_success}** (`{pct(confirm_success, waitlist_submit)}` from waitlist_submit)",
        "",
        "## Website -> Telegram Watchlist Loop",
        "",
        f"- page_view: **{page_view}**",
        f"- live_board_impression: **{live_board_impression}** (`{pct(live_board_impression, page_view)}` from page_view)",
        f"- watchlist_add_click: **{watchlist_add_click}** (`{pct(watchlist_add_click, page_view)}` from page_view)",
        f"- watchlist_add_success: **{watchlist_add_success}** (`{pct(watchlist_add_success, watchlist_add_click)}` from watchlist_add_click)",
        f"- telegram_login_click: **{telegram_login_click}** (`{pct(telegram_login_click, watchlist_add_click)}` from watchlist_add_click)",
        f"- site_login_completed: **{site_login_completed}** (`{pct(site_login_completed, telegram_login_click)}` from telegram_login_click)",
        f"- tg_start: **{tg_start}**",
        f"- bell_click: **{bell_click}** (`{pct(bell_click, watchlist_add_success)}` from watchlist_add_success)",
        f"- alert_setup_started: **{alert_setup_started}** (`{pct(alert_setup_started, bell_click)}` from bell_click)",
        f"- alert_enabled: **{alert_enabled}** (`{pct(alert_enabled, bell_click)}` from bell_click)",
        f"- alert_sent: **{alert_sent}** (`{pct(alert_sent, alert_enabled)}` from alert_enabled)",
        f"- alert_click_back_to_site: **{alert_click_back_to_site}** (`{pct(alert_click_back_to_site, alert_sent)}` from alert_sent)",
        f"- pricing_seen: **{pricing_seen}**",
        f"- pricing_cta_click: **{pricing_cta_click}** (`{pct(pricing_cta_click, pricing_seen)}` from pricing_seen)",
        "",
        "## Telegram Activation Cross-Check",
        "",
        f"- started_users (`app.identities provider=telegram`): **{started_users}**",
        f"- users_with_watchlist_add proxy (`bot.watchlist`): **{watchlist_add_users_proxy}**",
        f"- start_to_watchlist_add proxy: **{pct(watchlist_add_users_proxy, started_users)}**",
        f"- event_to_proxy gap (`watchlist_add users` vs `bot.watchlist` proxy): **{watchlist_add_users - watchlist_add_users_proxy:+d}**",
        f"- note: `tg_start` includes site, direct Telegram opens, and other bot entrypoints like `/upgrade`",
        "",
        "## Core Data Health",
        "",
        f"- latest bucket lag: **{latest_bucket_lag_seconds}s**",
        f"- latest yes-quote coverage: **{latest_yes_coverage_pct:.1f}%**",
        f"- universe coverage (latest): **{latest_universe_coverage}/{universe_count}**",
        f"- universe coverage (prev): **{prev_universe_coverage}/{universe_count}**",
        f"- non-zero movers: **latest {movers_latest_nonzero} / 1h {movers_1h_nonzero} / 24h {movers_24h_nonzero}**",
        "",
        "## tg_click by UTM Source",
        "",
        "| Source | tg_click | Share |",
        "|---|---:|---:|",
    ]

    total_clicks = max(sum(sources.values()), 1)
    for source, clicks in sorted(sources.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| {source} | {clicks} | {pct(clicks, total_clicks)} |")
    if not sources:
        lines.append("| n/a | 0 | n/a |")

    lines += [
        "",
        "## tg_start by Start Payload",
        "",
        "| Start payload | tg_start | Share |",
        "|---|---:|---:|",
    ]
    total_starts = max(sum(tg_start_sources.values()), 1)
    for start_source, starts in sorted(tg_start_sources.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| {start_source} | {starts} | {pct(starts, total_starts)} |")
    if not tg_start_sources:
        lines.append("| n/a | 0 | n/a |")

    lines += [
        "",
        "## Top tg_click Placements",
        "",
        "| Placement | tg_click |",
        "|---|---:|",
    ]
    if placement_rows:
        for row in placement_rows:
            lines.append(f"| {row['placement']} | {int(row['clicks'] or 0)} |")
    else:
        lines.append("| n/a | 0 |")

    lines += [
        "",
        "## CTA Surface Performance",
        "",
        "| Placement | Seen | tg_click | CTR |",
        "|---|---:|---:|---:|",
    ]
    if cta_surface_rows:
        for row in cta_surface_rows:
            seen = int(row.get("seen") or 0)
            clicks = int(row.get("clicks") or 0)
            ctr = pct(clicks, seen) if seen > 0 else "n/a"
            lines.append(f"| {row['placement']} | {seen} | {clicks} | {ctr} |")
    else:
        lines.append("| n/a | 0 | 0 | n/a |")

    lines += [
        "",
        "## Action Notes",
        "",
        "- Scale sources with highest tg_click share (`x`, `threads`, or direct).",
        "- If `tg_start/tg_click` is low: inspect Telegram deep-link friction and social CTA clarity.",
        "- If `watchlist_add/tg_start` is low: simplify first add, quiet-state recovery, and returning-user resume paths.",
        "- If `watchlist_add_success/watchlist_add_click` is low: inspect web save friction, auth prompt clarity, and workspace error states.",
        "- If `bell_click/watchlist_add_success` is low: the site may still be underselling the bell as a second deliberate action.",
        "- If `alert_enabled/bell_click` is low: inspect Telegram sensitivity setup and payload handoff.",
        "- If `alert_click_back_to_site/alert_enabled` is low: strengthen the return loop from alert into the website watchlist.",
        "- If one `start_payload` consistently wins: keep posting into that pain theme.",
        "- If `tg_click/page_view` is low: iterate hero and CTA copy on landing.",
        "- If `confirm_success/waitlist_submit` is low: review email deliverability and confirm page UX.",
        "- If core freshness or universe coverage slips: fix the analytical core before iterating user-facing Pulse UX.",
        "",
    ]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(str(output))


if __name__ == "__main__":
    main()
