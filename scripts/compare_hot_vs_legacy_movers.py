#!/usr/bin/env python3
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

DEFAULT_MIN_LIQUIDITY = float(os.environ.get("HOT_MOVERS_MIN_LIQUIDITY", "1000"))
DEFAULT_MAX_SPREAD = float(os.environ.get("HOT_MOVERS_MAX_SPREAD", "0.25"))
DEFAULT_MIN_ABS_DELTA = float(os.environ.get("HOT_MOVERS_MIN_ABS_DELTA", "0.003"))


SQL_SUMMARY = """
with hot as (
  select market_id, row_number() over(order by score desc, delta_abs desc) as rn
  from public.hot_top_movers_5m
  limit %(limit)s
),
legacy as (
  select market_id, row_number() over(order by abs(delta_yes) desc nulls last) as rn
  from public.top_movers_latest
  limit %(limit)s
)
select
  (select count(*) from hot) as hot_count,
  (select count(*) from legacy) as legacy_count,
  (select count(*) from hot join legacy using (market_id)) as overlap_count;
"""


SQL_OVERLAP = """
with hot as (
  select market_id, row_number() over(order by score desc, delta_abs desc) as hot_rank
  from public.hot_top_movers_5m
  limit %(limit)s
),
legacy as (
  select market_id, row_number() over(order by abs(delta_yes) desc nulls last) as legacy_rank
  from public.top_movers_latest
  limit %(limit)s
)
select h.market_id, h.hot_rank, l.legacy_rank
from hot h
join legacy l using (market_id)
order by least(h.hot_rank, l.legacy_rank), greatest(h.hot_rank, l.legacy_rank);
"""


SQL_TOP_COMPARE = """
with legacy as (
  select market_id, question, delta_yes, row_number() over(order by abs(delta_yes) desc nulls last) as legacy_rank
  from public.top_movers_latest
  limit %(top_n)s
), prev_anchor as (
  select distinct on (market_id)
    market_id,
    ts_bucket,
    mid_yes_prev
  from (
    select
      ms.market_id,
      ms.ts_bucket,
      max(coalesce(((ms.yes_bid + ms.yes_ask) / 2.0), ms.yes_bid, ms.yes_ask))::double precision as mid_yes_prev
    from public.market_snapshots ms
    where ms.market_id in (select market_id from legacy)
      and (ms.yes_bid is not null or ms.yes_ask is not null)
      and ms.ts_bucket <= (now() at time zone 'utc') - interval '4 minutes'
    group by ms.market_id, ms.ts_bucket
  ) per_bucket
  order by market_id, ts_bucket desc
)
select
  l.legacy_rank,
  l.market_id,
  l.question,
  l.delta_yes,
  hq.market_id is not null as in_hot_quotes,
  hq.has_two_sided_quote,
  hq.mid_yes as hot_mid,
  hq.liquidity,
  hq.spread,
  p.ts_bucket as prev_bucket,
  p.mid_yes_prev,
  hm.market_id is not null as in_hot_movers,
  hm.delta_mid as hot_delta,
  hm.score as hot_score,
  case
    when hm.market_id is not null then 'published'
    when hq.market_id is null then 'no_hot_quote_row'
    when not coalesce(hq.has_two_sided_quote, false) then 'no_two_sided_quote'
    when hq.mid_yes is null then 'missing_current_mid'
    when p.market_id is null or p.mid_yes_prev is null then 'missing_prev_5m_anchor'
    when coalesce(hq.liquidity, 0) < %(min_liquidity)s then 'below_liquidity_gate'
    when hq.spread is not null and hq.spread > %(max_spread)s then 'above_spread_gate'
    when abs(hq.mid_yes - p.mid_yes_prev) < %(min_abs_delta)s then 'below_abs_delta_gate'
    else 'other_unclassified'
  end as exclusion_reason
from legacy l
left join public.hot_market_quotes_latest hq on hq.market_id = l.market_id
left join prev_anchor p on p.market_id = l.market_id
left join public.hot_top_movers_5m hm on hm.market_id = l.market_id
order by l.legacy_rank;
"""


def fmt_num(v: object, digits: int = 4) -> str:
    if v is None:
        return "n/a"
    try:
        return f"{float(v):.{digits}f}"
    except Exception:
        return str(v)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare hot 5m movers against legacy top_movers_latest")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--top-n", type=int, default=15)
    parser.add_argument("--min-liquidity", type=float, default=DEFAULT_MIN_LIQUIDITY)
    parser.add_argument("--max-spread", type=float, default=DEFAULT_MAX_SPREAD)
    parser.add_argument("--min-abs-delta", type=float, default=DEFAULT_MIN_ABS_DELTA)
    parser.add_argument("--output", default="docs/hot_vs_legacy_movers_latest.md")
    args = parser.parse_args()

    pg = os.environ.get("PG_CONN", "")
    if not pg:
        raise SystemExit("PG_CONN is required")

    with psycopg.connect(pg, connect_timeout=10, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(SQL_SUMMARY, {"limit": args.limit})
            summary = cur.fetchone()
            cur.execute(SQL_OVERLAP, {"limit": args.limit})
            overlap = cur.fetchall()
            cur.execute(
                SQL_TOP_COMPARE,
                {
                    "top_n": args.top_n,
                    "min_liquidity": args.min_liquidity,
                    "max_spread": args.max_spread,
                    "min_abs_delta": args.min_abs_delta,
                },
            )
            top_compare = cur.fetchall()

    now = datetime.now(timezone.utc).isoformat()
    overlap_count = int(summary["overlap_count"] or 0)
    hot_count = int(summary["hot_count"] or 0)
    legacy_count = int(summary["legacy_count"] or 0)

    lines = [
        f"# Hot vs Legacy Movers ({now})",
        "",
        "Source tables:",
        "- `public.hot_top_movers_5m`",
        "- `public.top_movers_latest`",
        "- `public.hot_market_quotes_latest`",
        "",
        "## Summary",
        "",
        f"- hot_count: **{hot_count}**",
        f"- legacy_count: **{legacy_count}**",
        f"- overlap_count: **{overlap_count}**",
        "",
        "## Interpretation",
        "",
        "- This report is meant to decide whether `/movers` is ready for hot-first cutover.",
        "- High overlap with sane rank drift is a good sign.",
        "- Low overlap with strong live quote coverage usually means the hot layer is seeing fresher reversion than the legacy bucket view.",
        "",
        "## Active Gates",
        "",
        f"- min_liquidity: **{args.min_liquidity:.0f}**",
        f"- max_spread: **{args.max_spread:.3f}**",
        f"- min_abs_delta: **{args.min_abs_delta:.4f}**",
        "",
        "## Overlap Rows",
        "",
    ]

    if overlap:
        for row in overlap:
            lines.append(f"- `{row['market_id']}` hot_rank={row['hot_rank']} legacy_rank={row['legacy_rank']}")
    else:
        lines.append("- No overlap rows in the compared window.")

    lines += [
        "",
        "## Legacy Top Rows Diagnostic",
        "",
        "| legacy_rank | market_id | legacy_delta | in_hot_quotes | two_sided | liquidity | spread | in_hot_movers | hot_delta | hot_score | exclusion_reason |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | --- | ---: | ---: | --- |",
    ]

    for row in top_compare:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["legacy_rank"]),
                    str(row["market_id"]),
                    fmt_num(row["delta_yes"]),
                    "yes" if row["in_hot_quotes"] else "no",
                    "yes" if row["has_two_sided_quote"] else "no",
                    fmt_num(row["liquidity"], 2),
                    fmt_num(row["spread"]),
                    "yes" if row["in_hot_movers"] else "no",
                    fmt_num(row["hot_delta"]),
                    fmt_num(row["hot_score"]),
                    str(row["exclusion_reason"]),
                ]
            )
            + " |"
        )

    lines += [
        "",
        "## Reading Guide",
        "",
        "- `in_hot_quotes=yes` but `in_hot_movers=no` means the market is covered live, and `exclusion_reason` tells us which gate blocked it.",
        "- That is the key distinction between a fresher action surface and a laggier bucket surface.",
        "- Do not cut over `/movers` until this report shows the behavior we actually want as a product decision.",
        "",
    ]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(str(output))


if __name__ == "__main__":
    main()
