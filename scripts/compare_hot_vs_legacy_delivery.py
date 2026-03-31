#!/usr/bin/env python3
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


SQL_COUNTS = """
with hot_all as (
  select
    app_user_id::text as user_id,
    market_id,
    candidate_state,
    delta_abs,
    quote_ts
  from public.hot_alert_candidates_latest
), hot_ready as (
  select *
  from hot_all
  where candidate_state = 'ready'
), legacy_watchlist as (
  select
    user_id::text as user_id,
    market_id,
    abs_delta,
    last_bucket
  from bot.alerts_inbox_latest
  where alert_type = 'watchlist'
), legacy_all as (
  select
    user_id::text as user_id,
    market_id,
    alert_type,
    abs_delta,
    last_bucket
  from bot.alerts_inbox_latest
), sent_recent as (
  select
    user_id::text as user_id,
    market_id,
    alert_type,
    bucket,
    sent_at
  from bot.sent_alerts_log
  where channel = 'bot'
    and sent_at >= now() - (%s::int * interval '1 hour')
)
select
  (select count(*)::bigint from hot_all) as hot_all_count,
  (select count(*)::bigint from hot_ready) as hot_ready_count,
  (select count(*)::bigint from legacy_watchlist) as legacy_watchlist_count,
  (select count(*)::bigint from legacy_all) as legacy_all_count,
  (select count(*)::bigint from sent_recent) as sent_recent_count,
  (
    select count(*)::bigint
    from hot_ready h
    join legacy_watchlist l using (user_id, market_id)
  ) as hot_legacy_watchlist_overlap,
  (
    select count(*)::bigint
    from hot_ready h
    join sent_recent s
      on s.user_id = h.user_id
     and s.market_id = h.market_id
     and s.alert_type = 'watchlist'
  ) as hot_sent_overlap
;
"""


SQL_HOT_STATE_BREAKDOWN = """
select
  candidate_state,
  count(*)::bigint as row_count
from public.hot_alert_candidates_latest
group by candidate_state
order by row_count desc, candidate_state asc;
"""


SQL_HOT_SAMPLE = """
select
  app_user_id::text as user_id,
  market_id,
  question,
  candidate_state,
  delta_abs,
  threshold_value,
  quote_ts
from public.hot_alert_candidates_latest
order by
  case when candidate_state = 'ready' then 0 else 1 end,
  delta_abs desc,
  quote_ts desc
limit %s;
"""


SQL_LEGACY_SAMPLE = """
select
  user_id::text as user_id,
  market_id,
  question,
  alert_type,
  abs_delta,
  last_bucket
from bot.alerts_inbox_latest
order by abs_delta desc nulls last, last_bucket desc
limit %s;
"""


SQL_SENT_SAMPLE = """
select
  user_id::text as user_id,
  market_id,
  alert_type,
  bucket,
  sent_at
from bot.sent_alerts_log
where channel = 'bot'
  and sent_at >= now() - (%s::int * interval '1 hour')
order by sent_at desc
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare hot alert candidates against legacy inbox and recent sent alerts.")
    parser.add_argument("--hours", type=int, default=24, help="Recent sent-alert lookback window")
    parser.add_argument("--limit", type=int, default=10, help="Sample row limit")
    parser.add_argument("--output", default="docs/hot_vs_legacy_delivery_latest.md", help="Output markdown path")
    args = parser.parse_args()

    pg = os.environ.get("PG_CONN", "")
    if not pg:
        raise SystemExit("PG_CONN is required")

    with psycopg.connect(pg, connect_timeout=10) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(SQL_COUNTS, (args.hours,))
            counts = cur.fetchone()
            cur.execute(SQL_HOT_STATE_BREAKDOWN)
            hot_breakdown = cur.fetchall()
            cur.execute(SQL_HOT_SAMPLE, (args.limit,))
            hot_sample = cur.fetchall()
            cur.execute(SQL_LEGACY_SAMPLE, (args.limit,))
            legacy_sample = cur.fetchall()
            cur.execute(SQL_SENT_SAMPLE, (args.hours, args.limit))
            sent_sample = cur.fetchall()

    if not counts:
        raise SystemExit("No comparison data returned")

    now = datetime.now(timezone.utc)
    hot_ready = int(counts["hot_ready_count"] or 0)
    legacy_watchlist = int(counts["legacy_watchlist_count"] or 0)
    sent_recent = int(counts["sent_recent_count"] or 0)
    overlap = int(counts["hot_legacy_watchlist_overlap"] or 0)
    hot_sent_overlap = int(counts["hot_sent_overlap"] or 0)

    if hot_ready == 0 and legacy_watchlist == 0:
        verdict = "Current window is quiet on both hot and legacy watchlist inbox surfaces."
    elif hot_ready > 0 and legacy_watchlist == 0:
        verdict = "Hot layer sees ready watchlist alerts earlier than the legacy inbox surface."
    elif hot_ready == 0 and legacy_watchlist > 0:
        verdict = "Legacy inbox still shows watchlist alerts that the hot layer no longer considers actionable."
    else:
        verdict = "Both surfaces have active watchlist alerts; compare overlap before cutover."

    lines = [
        f"# Hot vs Legacy Delivery Comparison ({now.isoformat()})",
        "",
        "Source surfaces:",
        "",
        "- `public.hot_alert_candidates_latest`",
        "- `bot.alerts_inbox_latest`",
        "- `bot.sent_alerts_log`",
        "",
        "## Summary",
        "",
        bullet("hot_all_count", str(int(counts["hot_all_count"] or 0))),
        bullet("hot_ready_count", str(hot_ready)),
        bullet("legacy_watchlist_count", str(legacy_watchlist)),
        bullet("legacy_all_count", str(int(counts["legacy_all_count"] or 0))),
        bullet(f"sent_recent_count ({args.hours}h)", str(sent_recent)),
        bullet("hot_legacy_watchlist_overlap", str(overlap)),
        bullet(f"hot_sent_overlap ({args.hours}h)", str(hot_sent_overlap)),
        "",
        f"Verdict: {verdict}",
        "",
        "## Hot Candidate State Breakdown",
        "",
    ]
    lines.extend([bullet(str(row["candidate_state"]), str(int(row["row_count"] or 0))) for row in hot_breakdown] or ["- none"])
    lines.extend(
        [
            "",
            "## Hot Candidate Sample",
            "",
            *fmt_rows(hot_sample, ["user_id", "market_id", "candidate_state", "delta_abs", "threshold_value", "quote_ts"]),
            "",
            "## Legacy Inbox Sample",
            "",
            *fmt_rows(legacy_sample, ["user_id", "market_id", "alert_type", "abs_delta", "last_bucket"]),
            "",
            f"## Recent Sent Alerts ({args.hours}h)",
            "",
            *fmt_rows(sent_sample, ["user_id", "market_id", "alert_type", "bucket", "sent_at"]),
            "",
            "## Notes",
            "",
            "- `hot_ready_count` reflects only watchlist candidates with `candidate_state = 'ready'` in the latest hot pass.",
            "- `legacy_watchlist_count` reflects only `alert_type='watchlist'` rows currently visible in `bot.alerts_inbox_latest`.",
            "- `sent_recent_count` is historical tail, so it may stay non-zero even when both current surfaces are quiet.",
            "- Use this report to decide whether push delivery can move to hot-first safely.",
            "",
        ]
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(str(output))


if __name__ == "__main__":
    main()
