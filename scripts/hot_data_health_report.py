#!/usr/bin/env python3
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


SQL_HOT_HEALTH = """
with registry as (
  select count(*)::bigint as registry_rows
  from public.hot_market_registry_latest
),
quotes as (
  select
    count(*)::bigint as quote_rows,
    count(*) filter (where has_two_sided_quote)::bigint as two_sided_quote_rows
  from public.hot_market_quotes_latest
),
watchlist as (
  select count(*)::bigint as watchlist_rows
  from public.hot_watchlist_snapshot_latest
),
alerts as (
  select count(*)::bigint as alert_candidate_rows
  from public.hot_alert_candidates_latest
)
select
  h.*,
  r.registry_rows,
  q.quote_rows,
  q.two_sided_quote_rows,
  w.watchlist_rows,
  a.alert_candidate_rows
from public.hot_ingest_health_latest h
cross join registry r
cross join quotes q
cross join watchlist w
cross join alerts a
limit 1;
"""


def status_line(ok: bool, label: str, detail: str) -> str:
    badge = "OK" if ok else "CHECK"
    return f"- `{badge}` {label}: {detail}"


def phase_line(label: str, detail: str) -> str:
    return f"- `{label}` {detail}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a read-only hot data layer health report from Supabase")
    parser.add_argument("--output", default="docs/hot_data_health_latest.md", help="Output markdown path")
    parser.add_argument("--max-registry-age-seconds", type=int, default=180, help="Healthy registry freshness threshold")
    parser.add_argument("--max-quotes-age-seconds", type=int, default=120, help="Healthy quotes freshness threshold")
    args = parser.parse_args()

    pg = os.environ.get("PG_CONN", "")
    if not pg:
        raise SystemExit("PG_CONN is required")

    with psycopg.connect(pg, connect_timeout=10) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(SQL_HOT_HEALTH)
            row = cur.fetchone()

    if not row:
        raise SystemExit("public.hot_ingest_health_latest returned no rows")

    now = datetime.now(timezone.utc)
    registry_age = row.get("registry_age_seconds")
    quotes_age = row.get("quotes_age_seconds")
    registry_rows = int(row.get("registry_rows") or 0)
    quote_rows = int(row.get("quote_rows") or 0)
    two_sided_quote_rows = int(row.get("two_sided_quote_rows") or 0)
    hot_movers_1m_count = int(row.get("hot_movers_1m_count") or 0)
    hot_movers_5m_count = int(row.get("hot_movers_5m_count") or 0)
    watchlist_rows = int(row.get("watchlist_rows") or 0)
    alert_candidate_rows = int(row.get("alert_candidate_rows") or 0)

    lines = [
        f"# Hot Data Health Report ({now.isoformat()})",
        "",
        "Source: `public.hot_ingest_health_latest` + direct counts from V1 hot tables",
        "",
        "## Hot Contract",
        "",
        "- `public.hot_market_registry_latest`",
        "- `public.hot_market_quotes_latest`",
        "- `public.hot_top_movers_1m`",
        "- `public.hot_top_movers_5m`",
        "- `public.hot_watchlist_snapshot_latest`",
        "- `public.hot_alert_candidates_latest`",
        "- `public.hot_ingest_health_latest`",
        "",
        "## Health Checks",
        "",
        status_line(
            registry_age is not None and int(registry_age) <= args.max_registry_age_seconds,
            "Registry freshness",
            f"{registry_age if registry_age is not None else 'n/a'}s (threshold `{args.max_registry_age_seconds}s`)",
        ),
        status_line(
            quotes_age is not None and int(quotes_age) <= args.max_quotes_age_seconds,
            "Quotes freshness",
            f"{quotes_age if quotes_age is not None else 'n/a'}s (threshold `{args.max_quotes_age_seconds}s`)",
        ),
        status_line(
            registry_rows > 0,
            "Registry rows present",
            f"{registry_rows} rows",
        ),
        status_line(
            quote_rows > 0,
            "Quote rows present",
            f"{quote_rows} rows",
        ),
        status_line(
            two_sided_quote_rows > 0,
            "Two-sided quote coverage",
            f"{two_sided_quote_rows}/{quote_rows}",
        ),
        "",
        "## Phase Notes",
        "",
        phase_line("V1 now", "registry + quotes are expected to be live."),
        phase_line("V1 now", "hot 5m movers are expected to be live once the mover publish phase is deployed."),
        phase_line("V1 now", "hot watchlist snapshots and hot alert candidates are expected to be live now."),
        phase_line("V1 now", "hot 1m movers are expected to be live now."),
        "",
        "## Snapshot",
        "",
        f"- active_market_count: **{int(row.get('active_market_count') or 0)}**",
        f"- registry_rows: **{registry_rows}**",
        f"- quote_rows: **{quote_rows}**",
        f"- two_sided_quote_rows: **{two_sided_quote_rows}**",
        f"- hot_movers_1m_count: **{hot_movers_1m_count}**",
        f"- hot_movers_5m_count: **{hot_movers_5m_count}**",
        f"- hot_watchlist_snapshot_latest rows: **{watchlist_rows}**",
        f"- hot_alert_candidates_latest rows: **{alert_candidate_rows}**",
        f"- updated_at: **{row.get('updated_at')}**",
        "",
        "## Review Notes",
        "",
        "- Treat this as the first operational heartbeat for the new hot layer.",
        "- `hot_top_movers_5m` should now be non-empty during healthy market conditions; `hot_watchlist_snapshot_latest` and `hot_alert_candidates_latest` should also stay non-empty when users track markets.",
        "- `hot_top_movers_1m` should now be non-empty during healthy market conditions as the live worker publishes it from the previous hot quote anchor.",
        "- Do not cut over homepage or bot reads until this report stays healthy over repeated ticks.",
        "",
    ]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(str(output))


if __name__ == "__main__":
    main()
