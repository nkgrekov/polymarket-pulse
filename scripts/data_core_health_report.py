#!/usr/bin/env python3
import argparse
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


SQL_CORE_HEALTH = """
select *
from public.analytics_core_health_latest
limit 1;
"""


def fmt_decimal(value: Decimal | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}"


def status_line(ok: bool, label: str, detail: str) -> str:
    badge = "OK" if ok else "CHECK"
    return f"- `{badge}` {label}: {detail}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a read-only data-core health report from Supabase")
    parser.add_argument("--output", default="docs/data_core_health_latest.md", help="Output markdown path")
    parser.add_argument("--max-lag-seconds", type=int, default=900, help="Healthy freshness threshold")
    parser.add_argument("--min-yes-coverage", type=float, default=90.0, help="Healthy latest yes quote coverage percent")
    args = parser.parse_args()

    pg = os.environ.get("PG_CONN", "")
    if not pg:
        raise SystemExit("PG_CONN is required")

    with psycopg.connect(pg, connect_timeout=10) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(SQL_CORE_HEALTH)
            row = cur.fetchone()

    if not row:
        raise SystemExit("public.analytics_core_health_latest returned no rows")

    now = datetime.now(timezone.utc)
    lag_seconds = int(row.get("latest_bucket_lag_seconds") or 0)
    universe_count = int(row.get("universe_count") or 0)
    latest_universe_coverage = int(row.get("latest_universe_coverage") or 0)
    prev_universe_coverage = int(row.get("prev_universe_coverage") or 0)
    latest_yes_coverage_pct = float(row.get("latest_yes_coverage_pct") or 0.0)
    movers_latest_nonzero = int(row.get("movers_latest_nonzero") or 0)
    movers_1h_nonzero = int(row.get("movers_1h_nonzero") or 0)
    movers_24h_nonzero = int(row.get("movers_24h_nonzero") or 0)

    lines = [
        f"# Data Core Health Report ({now.isoformat()})",
        "",
        "Source: `public.analytics_core_health_latest`",
        "",
        "## Core Contract",
        "",
        "- `public.market_snapshots`",
        "- `public.market_universe`",
        "- `public.snapshot_health`",
        "- `public.top_movers_latest`",
        "- `public.top_movers_1h`",
        "- `public.top_movers_24h`",
        "",
        "## Health Checks",
        "",
        status_line(
            lag_seconds <= args.max_lag_seconds,
            "Freshness lag",
            f"{lag_seconds}s (latest bucket `{row.get('latest_bucket')}`; threshold `{args.max_lag_seconds}s`)",
        ),
        status_line(
            latest_yes_coverage_pct >= args.min_yes_coverage,
            "Latest yes-quote coverage",
            f"{latest_yes_coverage_pct:.1f}% (threshold `{args.min_yes_coverage:.1f}%`)",
        ),
        status_line(
            latest_universe_coverage >= universe_count and universe_count > 0,
            "Latest universe coverage",
            f"{latest_universe_coverage}/{universe_count}",
        ),
        status_line(
            prev_universe_coverage >= universe_count and universe_count > 0,
            "Previous-bucket universe coverage",
            f"{prev_universe_coverage}/{universe_count}",
        ),
        status_line(
            movers_latest_nonzero > 0,
            "Current movers output",
            f"{movers_latest_nonzero} non-zero movers out of {int(row.get('movers_latest_count') or 0)} rows",
        ),
        status_line(
            movers_1h_nonzero > 0,
            "1h movers output",
            f"{movers_1h_nonzero} non-zero movers out of {int(row.get('movers_1h_count') or 0)} rows",
        ),
        status_line(
            movers_24h_nonzero > 0,
            "24h movers output",
            f"{movers_24h_nonzero} non-zero movers out of {int(row.get('movers_24h_count') or 0)} rows",
        ),
        "",
        "## Snapshot",
        "",
        f"- latest_bucket_rows: **{int(row.get('latest_bucket_rows') or 0)}**",
        f"- latest_yes_quoted: **{int(row.get('latest_yes_quoted') or 0)}**",
        f"- movers_latest_max_abs_delta: **{fmt_decimal(row.get('movers_latest_max_abs_delta'))}**",
        f"- movers_1h_max_abs_delta: **{fmt_decimal(row.get('movers_1h_max_abs_delta'))}**",
        f"- movers_24h_max_abs_delta: **{fmt_decimal(row.get('movers_24h_max_abs_delta'))}**",
        "",
        "## Review Notes",
        "",
        "- Treat this as a read-only health view over the analytical core.",
        "- Do not use it as a reason to re-plumb the live Pulse runtime from `bot.*` this week.",
        "- If freshness or universe coverage degrades, fix ingest/core first before touching user-facing bot UX.",
        "",
    ]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(str(output))


if __name__ == "__main__":
    main()
