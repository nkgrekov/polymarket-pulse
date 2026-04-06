#!/usr/bin/env python3
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - fallback for local shells that only have psycopg2
    psycopg = None
    dict_row = None
    import psycopg2
    import psycopg2.extras


SQL_SUMMARY = """
with recent as (
  select *
  from bot.delivery_parity_log
  where sampled_at >= now() - (%s::int * interval '1 hour')
)
select
  count(*)::bigint as samples_total,
  count(*) filter (where hot_ready_count > 0 or legacy_watchlist_count > 0)::bigint as non_quiet_samples,
  count(*) filter (where hot_only_count > 0 and legacy_watchlist_count = 0)::bigint as hot_only_samples,
  count(*) filter (where legacy_only_count > 0 and hot_ready_count = 0)::bigint as legacy_only_samples,
  count(*) filter (where hot_ready_count > 0 and legacy_watchlist_count > 0)::bigint as both_non_quiet_samples,
  coalesce(max(hot_ready_count), 0)::bigint as max_hot_ready_count,
  coalesce(max(legacy_watchlist_count), 0)::bigint as max_legacy_watchlist_count,
  coalesce(max(overlap_count), 0)::bigint as max_overlap_count
from recent;
"""

SQL_LATEST_NON_QUIET = """
select
  sampled_at,
  hot_ready_count,
  legacy_watchlist_count,
  overlap_count,
  hot_only_count,
  legacy_only_count,
  top_hot_market_id,
  top_legacy_market_id,
  top_hot_abs_delta,
  top_legacy_abs_delta
from bot.delivery_parity_log
where sampled_at >= now() - (%s::int * interval '1 hour')
  and (hot_ready_count > 0 or legacy_watchlist_count > 0)
order by sampled_at desc
limit 1;
"""


def bullet(label: str, value: str) -> str:
    return f"- {label}: **{value}**"


def fetch_report_data(pg: str, hours: int) -> tuple[dict, dict | None]:
    if psycopg is not None:
        with psycopg.connect(pg, connect_timeout=10) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(SQL_SUMMARY, (hours,))
                summary = cur.fetchone() or {}
                cur.execute(SQL_LATEST_NON_QUIET, (hours,))
                latest = cur.fetchone()
        return summary, latest

    with psycopg2.connect(pg, connect_timeout=10) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(SQL_SUMMARY, (hours,))
            summary = cur.fetchone() or {}
            cur.execute(SQL_LATEST_NON_QUIET, (hours,))
            latest = cur.fetchone()
    return summary, latest


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize hot-vs-legacy delivery parity history.")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--output", default="docs/delivery_parity_latest.md")
    args = parser.parse_args()

    pg = os.environ.get("PG_CONN", "")
    if not pg:
        raise SystemExit("PG_CONN is required")

    summary, latest = fetch_report_data(pg, args.hours)

    now = datetime.now(timezone.utc).isoformat()
    lines = [
        f"# Delivery Parity Snapshot ({now})",
        "",
        "Source:",
        "",
        "- `bot.delivery_parity_log`",
        "",
        "## Window",
        "",
        bullet("hours", str(args.hours)),
        "",
        "## Summary",
        "",
        bullet("samples_total", str(summary.get("samples_total", 0))),
        bullet("non_quiet_samples", str(summary.get("non_quiet_samples", 0))),
        bullet("hot_only_samples", str(summary.get("hot_only_samples", 0))),
        bullet("legacy_only_samples", str(summary.get("legacy_only_samples", 0))),
        bullet("both_non_quiet_samples", str(summary.get("both_non_quiet_samples", 0))),
        bullet("max_hot_ready_count", str(summary.get("max_hot_ready_count", 0))),
        bullet("max_legacy_watchlist_count", str(summary.get("max_legacy_watchlist_count", 0))),
        bullet("max_overlap_count", str(summary.get("max_overlap_count", 0))),
        "",
        "## Latest Non-Quiet Sample",
        "",
    ]

    if latest:
        lines.extend(
            [
                bullet("sampled_at", str(latest.get("sampled_at"))),
                bullet("hot_ready_count", str(latest.get("hot_ready_count"))),
                bullet("legacy_watchlist_count", str(latest.get("legacy_watchlist_count"))),
                bullet("overlap_count", str(latest.get("overlap_count"))),
                bullet("hot_only_count", str(latest.get("hot_only_count"))),
                bullet("legacy_only_count", str(latest.get("legacy_only_count"))),
                bullet("top_hot_market_id", str(latest.get("top_hot_market_id") or "none")),
                bullet("top_legacy_market_id", str(latest.get("top_legacy_market_id") or "none")),
                bullet("top_hot_abs_delta", str(latest.get("top_hot_abs_delta") or "none")),
                bullet("top_legacy_abs_delta", str(latest.get("top_legacy_abs_delta") or "none")),
            ]
        )
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `hot_only_samples > 0` means the hot layer saw watchlist-ready candidates that legacy delivery did not expose in the same window.",
            "- `legacy_only_samples > 0` means legacy delivery still surfaces watchlist alerts that the hot layer did not mark `ready`.",
            "- `both_non_quiet_samples > 0` plus a healthy `max_overlap_count` is the strongest evidence for a safe hot-first delivery cutover.",
            "",
        ]
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
