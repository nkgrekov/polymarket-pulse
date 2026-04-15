#!/usr/bin/env python3
import argparse
from collections import Counter
import json
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

SQL_RECENT_NON_QUIET = """
select
  sampled_at,
  hot_ready_count,
  legacy_watchlist_count,
  overlap_count,
  hot_only_count,
  legacy_only_count,
  payload
from bot.delivery_parity_log
where sampled_at >= now() - (%s::int * interval '1 hour')
  and (hot_ready_count > 0 or legacy_watchlist_count > 0)
order by sampled_at desc
limit %s;
"""


def bullet(label: str, value: str) -> str:
    return f"- {label}: **{value}**"


def fmt_rows(rows: list[dict], keys: list[str]) -> list[str]:
    if not rows:
        return ["- none"]
    out: list[str] = []
    for row in rows:
        parts = [f"{key}={row.get(key)}" for key in keys]
        out.append(f"- {' | '.join(parts)}")
    return out


def normalize_payload(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {}
    return {}


def fetch_report_data(pg: str, hours: int, recent_limit: int) -> tuple[dict, dict | None, list[dict]]:
    if psycopg is not None:
        with psycopg.connect(pg, connect_timeout=10) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(SQL_SUMMARY, (hours,))
                summary = cur.fetchone() or {}
                cur.execute(SQL_LATEST_NON_QUIET, (hours,))
                latest = cur.fetchone()
                cur.execute(SQL_RECENT_NON_QUIET, (hours, recent_limit))
                recent = cur.fetchall()
        return summary, latest, recent

    with psycopg2.connect(pg, connect_timeout=10) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(SQL_SUMMARY, (hours,))
            summary = cur.fetchone() or {}
            cur.execute(SQL_LATEST_NON_QUIET, (hours,))
            latest = cur.fetchone()
            cur.execute(SQL_RECENT_NON_QUIET, (hours, recent_limit))
            recent = cur.fetchall()
    return summary, latest, recent


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize hot-vs-legacy delivery parity history.")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--recent-limit", type=int, default=25)
    parser.add_argument("--output", default="docs/delivery_parity_latest.md")
    args = parser.parse_args()

    pg = os.environ.get("PG_CONN", "")
    if not pg:
        raise SystemExit("PG_CONN is required")

    summary, latest, recent = fetch_report_data(pg, args.hours, args.recent_limit)

    classification_totals: Counter[str] = Counter()
    hot_examples: list[dict] = []
    legacy_examples: list[dict] = []
    seen_hot: set[tuple[object, object, object]] = set()
    seen_legacy: set[tuple[object, object, object]] = set()

    for sample in recent:
        payload = normalize_payload(sample.get("payload"))
        sampled_at = sample.get("sampled_at")
        for item in payload.get("classification_counts", []) or []:
            classification = str(item.get("classification") or "unknown")
            classification_totals[classification] += int(item.get("count") or 0)
        for item in payload.get("hot_only_top", []) or []:
            key = (item.get("user_id"), item.get("market_id"), item.get("classification"))
            if key in seen_hot:
                continue
            seen_hot.add(key)
            hot_examples.append({"sampled_at": sampled_at, **item})
            if len(hot_examples) >= 5:
                break
        for item in payload.get("legacy_only_top", []) or []:
            key = (item.get("user_id"), item.get("market_id"), item.get("classification"))
            if key in seen_legacy:
                continue
            seen_legacy.add(key)
            legacy_examples.append({"sampled_at": sampled_at, **item})
            if len(legacy_examples) >= 5:
                break

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
            "## Classification Totals",
            "",
        ]
    )
    if classification_totals:
        for classification, count in classification_totals.most_common():
            lines.append(bullet(classification, str(count)))
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Recent Hot-Only Examples",
            "",
            *fmt_rows(
                hot_examples,
                [
                    "sampled_at",
                    "market_id",
                    "classification",
                    "delta_abs",
                    "threshold_value",
                    "live_state",
                    "quote_ts",
                ],
            ),
            "",
            "## Recent Legacy-Only Examples",
            "",
            *fmt_rows(
                legacy_examples,
                [
                    "sampled_at",
                    "market_id",
                    "classification",
                    "abs_delta",
                    "threshold_value",
                    "candidate_state",
                    "live_state",
                    "legacy_last_bucket",
                ],
            ),
        ]
    )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `hot_only_samples > 0` means the hot layer saw watchlist-ready candidates that legacy delivery did not expose in the same window.",
            "- `legacy_only_samples > 0` means legacy delivery still surfaces watchlist alerts that the hot layer did not mark `ready`.",
            "- `both_non_quiet_samples > 0` plus a healthy `max_overlap_count` is the strongest evidence for a safe hot-first delivery cutover.",
            "- `Classification Totals` help separate semantic mismatch types from raw count drift so delivery decisions are based on reasons, not just volumes.",
            "",
        ]
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
