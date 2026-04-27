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
  count(*) filter (
    where (hot_ready_count > 0 or legacy_watchlist_count > 0)
      and coalesce(payload, '{}'::jsonb) ? 'classification_counts'
  )::bigint as classified_non_quiet_samples,
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

SQL_CLASSIFICATION_TOTALS = """
with recent as (
  select payload
  from bot.delivery_parity_log
  where sampled_at >= now() - (%s::int * interval '1 hour')
    and payload is not null
), expanded as (
  select
    coalesce(item->>'classification', 'unknown') as classification,
    coalesce(nullif(item->>'count', '')::bigint, 0) as row_count
  from recent
  cross join lateral jsonb_array_elements(
    coalesce(payload->'classification_counts', '[]'::jsonb)
  ) item
)
select
  classification,
  sum(row_count)::bigint as row_count
from expanded
group by classification
order by row_count desc, classification asc;
"""

SQL_TOP_MISMATCH_MARKETS = """
with recent as (
  select
    sampled_at,
    payload
  from bot.delivery_parity_log
  where sampled_at >= now() - (%s::int * interval '1 hour')
    and payload is not null
), expanded as (
  select
    r.sampled_at,
    'hot_only'::text as side,
    item
  from recent r
  cross join lateral jsonb_array_elements(coalesce(r.payload->'hot_only_top', '[]'::jsonb)) item
  union all
  select
    r.sampled_at,
    'legacy_only'::text as side,
    item
  from recent r
  cross join lateral jsonb_array_elements(coalesce(r.payload->'legacy_only_top', '[]'::jsonb)) item
), normalized as (
  select
    side,
    item->>'market_id' as market_id,
    coalesce(item->>'classification', 'unknown') as classification,
    max(nullif(item->>'question', '')) as question,
    count(*)::bigint as sample_count,
    min(sampled_at) as first_seen,
    max(sampled_at) as last_seen,
    max(abs(coalesce(nullif(item->>'delta_abs', '')::double precision, nullif(item->>'abs_delta', '')::double precision, 0))) as max_abs_delta,
    max(nullif(item->>'threshold_value', '')::double precision) as max_threshold_value,
    max(nullif(item->>'liquidity', '')::double precision) as max_liquidity,
    max(nullif(item->>'spread', '')::double precision) as max_spread
  from expanded
  where coalesce(item->>'market_id', '') <> ''
  group by side, item->>'market_id', coalesce(item->>'classification', 'unknown')
), ranked as (
  select
    *,
    row_number() over (
      partition by side
      order by sample_count desc, max_abs_delta desc nulls last, market_id
    ) as rn
  from normalized
), current_candidates as (
  select
    market_id::text as market_id,
    string_agg(distinct candidate_state, ',' order by candidate_state) as current_candidate_states,
    count(*)::bigint as current_candidate_rows
  from public.hot_alert_candidates_latest
  group by market_id::text
), current_watchlist as (
  select
    w.market_id::text as market_id,
    count(*)::bigint as current_watchlist_rows,
    count(*) filter (where coalesce(m.status, 'unknown') = 'closed')::bigint as current_closed_watchlist_rows
  from bot.watchlist w
  left join public.markets m on m.market_id::text = w.market_id::text
  group by w.market_id::text
)
select
  r.side,
  r.market_id,
  r.classification,
  r.question,
  r.sample_count,
  r.first_seen,
  r.last_seen,
  r.max_abs_delta,
  r.max_threshold_value,
  r.max_liquidity,
  r.max_spread,
  coalesce(m.status, 'unknown') as current_market_status,
  coalesce(h.status, 'unknown') as current_hot_status,
  h.end_date as current_hot_end_date,
  case
    when coalesce(m.status, h.status, 'unknown') = 'closed' then 'closed'
    when h.end_date is not null and h.end_date < now() then 'date_passed_active'
    else coalesce(h.status, m.status, 'unknown')
  end as current_lifecycle_state,
  coalesce(c.current_candidate_states, 'none') as current_candidate_states,
  coalesce(c.current_candidate_rows, 0) as current_candidate_rows,
  coalesce(w.current_watchlist_rows, 0) as current_watchlist_rows,
  coalesce(w.current_closed_watchlist_rows, 0) as current_closed_watchlist_rows
from ranked r
left join public.markets m on m.market_id::text = r.market_id
left join public.hot_market_registry_latest h on h.market_id::text = r.market_id
left join current_candidates c on c.market_id = r.market_id
left join current_watchlist w on w.market_id = r.market_id
where r.rn <= %s
order by r.side, r.rn;
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


def fmt_float(value: object, digits: int = 4) -> str:
    if value is None:
        return "none"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def short_text(value: object, limit: int = 90) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1]}..."


def fmt_mismatch_market_rows(rows: list[dict], side: str) -> list[str]:
    selected = [row for row in rows if row.get("side") == side]
    if not selected:
        return ["- none"]
    out: list[str] = []
    for row in selected:
        out.append(
            "- "
            f"market_id={row.get('market_id')} | "
            f"classification={row.get('classification')} | "
            f"samples={row.get('sample_count')} | "
            f"max_abs_delta={fmt_float(row.get('max_abs_delta'))} | "
            f"threshold={fmt_float(row.get('max_threshold_value'))} | "
            f"current={row.get('current_lifecycle_state')} | "
            f"candidate_states={row.get('current_candidate_states')} | "
            f"watchlist_rows={row.get('current_watchlist_rows')} | "
            f"last_seen={row.get('last_seen')} | "
            f"question={short_text(row.get('question'))}"
        )
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


def fetch_report_data(pg: str, hours: int, recent_limit: int, top_market_limit: int) -> tuple[dict, dict | None, list[dict], list[dict], list[dict]]:
    if psycopg is not None:
        with psycopg.connect(pg, connect_timeout=10) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(SQL_SUMMARY, (hours,))
                summary = cur.fetchone() or {}
                cur.execute(SQL_LATEST_NON_QUIET, (hours,))
                latest = cur.fetchone()
                cur.execute(SQL_RECENT_NON_QUIET, (hours, recent_limit))
                recent = cur.fetchall()
                cur.execute(SQL_CLASSIFICATION_TOTALS, (hours,))
                classification_rows = cur.fetchall()
                cur.execute(SQL_TOP_MISMATCH_MARKETS, (hours, top_market_limit))
                top_mismatch_markets = cur.fetchall()
        return summary, latest, recent, classification_rows, top_mismatch_markets

    with psycopg2.connect(pg, connect_timeout=10) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(SQL_SUMMARY, (hours,))
            summary = cur.fetchone() or {}
            cur.execute(SQL_LATEST_NON_QUIET, (hours,))
            latest = cur.fetchone()
            cur.execute(SQL_RECENT_NON_QUIET, (hours, recent_limit))
            recent = cur.fetchall()
            cur.execute(SQL_CLASSIFICATION_TOTALS, (hours,))
            classification_rows = cur.fetchall()
            cur.execute(SQL_TOP_MISMATCH_MARKETS, (hours, top_market_limit))
            top_mismatch_markets = cur.fetchall()
    return summary, latest, recent, classification_rows, top_mismatch_markets


def int_value(row: dict, key: str) -> int:
    return int(row.get(key) or 0)


def build_decision_readout(summary: dict, classification_totals: Counter[str]) -> list[str]:
    hot_only_samples = int_value(summary, "hot_only_samples")
    legacy_only_samples = int_value(summary, "legacy_only_samples")
    non_quiet_samples = int_value(summary, "non_quiet_samples")
    classified_non_quiet_samples = int_value(summary, "classified_non_quiet_samples")
    max_overlap_count = int_value(summary, "max_overlap_count")

    lines = ["## Decision Readout", ""]
    if non_quiet_samples <= 0:
        lines.append("- Verdict: keep accumulating parity. The selected window has no non-quiet delivery evidence.")
        return lines

    coverage = classified_non_quiet_samples / non_quiet_samples if non_quiet_samples else 0.0
    if legacy_only_samples > max(hot_only_samples * 2, 25):
        verdict = "keep legacy delivery as primary"
        reason = "legacy-only windows still materially outweigh hot-only windows"
    elif max_overlap_count >= 3 and coverage >= 0.90 and legacy_only_samples <= hot_only_samples:
        verdict = "candidate for limited hot-first rollout"
        reason = "overlap is healthy and legacy-only evidence is no longer dominant"
    else:
        verdict = "continue hybrid/fallback diagnostics"
        reason = "the window is informative but not yet clean enough for a delivery cutover"

    lines.extend(
        [
            f"- Verdict: **{verdict}**.",
            f"- Reason: {reason}.",
            f"- Classification coverage: **{coverage:.1%}** of non-quiet samples.",
            f"- Main classified reason: **{classification_totals.most_common(1)[0][0]}**." if classification_totals else "- Main classified reason: **none yet**.",
            "- Delivery semantics: unchanged; this report is evidence for the next decision, not a runtime cutover.",
        ]
    )
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize hot-vs-legacy delivery parity history.")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--recent-limit", type=int, default=25)
    parser.add_argument("--top-market-limit", type=int, default=8)
    parser.add_argument("--output", default="docs/delivery_parity_latest.md")
    args = parser.parse_args()

    pg = os.environ.get("PG_CONN", "")
    if not pg:
        raise SystemExit("PG_CONN is required")

    summary, latest, recent, classification_rows, top_mismatch_markets = fetch_report_data(
        pg,
        args.hours,
        args.recent_limit,
        args.top_market_limit,
    )

    classification_totals: Counter[str] = Counter()
    hot_examples: list[dict] = []
    legacy_examples: list[dict] = []
    seen_hot: set[tuple[object, object, object]] = set()
    seen_legacy: set[tuple[object, object, object]] = set()

    for row in classification_rows:
        classification = str(row.get("classification") or "unknown")
        classification_totals[classification] += int(row.get("row_count") or 0)

    for sample in recent:
        payload = normalize_payload(sample.get("payload"))
        sampled_at = sample.get("sampled_at")
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
        bullet("classified_non_quiet_samples", str(summary.get("classified_non_quiet_samples", 0))),
        bullet(
            "unclassified_non_quiet_samples",
            str(max(int(summary.get("non_quiet_samples", 0) or 0) - int(summary.get("classified_non_quiet_samples", 0) or 0), 0)),
        ),
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

    lines.extend(["", *build_decision_readout(summary, classification_totals)])

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
            "## Top Hot-Only Mismatch Markets",
            "",
            *fmt_mismatch_market_rows(top_mismatch_markets, "hot_only"),
            "",
            "## Top Legacy-Only Mismatch Markets",
            "",
            *fmt_mismatch_market_rows(top_mismatch_markets, "legacy_only"),
        ]
    )

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
            "- `current=closed` in top mismatch markets means the historical mismatch came from a market that has since exited live delivery.",
            "- `current=active` plus `candidate_states=below_threshold` means the market is still tracked, but hot currently sees no threshold-clearing move.",
            "",
        ]
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
