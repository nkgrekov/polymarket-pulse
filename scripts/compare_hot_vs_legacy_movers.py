#!/usr/bin/env python3
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


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
  hm.market_id is not null as in_hot_movers,
  hm.delta_mid as hot_delta,
  hm.score as hot_score
from legacy l
left join public.hot_market_quotes_latest hq on hq.market_id = l.market_id
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
            cur.execute(SQL_TOP_COMPARE, {"top_n": args.top_n})
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
        "| legacy_rank | market_id | legacy_delta | in_hot_quotes | two_sided | liquidity | spread | in_hot_movers | hot_delta | hot_score |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | --- | ---: | ---: |",
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
                ]
            )
            + " |"
        )

    lines += [
        "",
        "## Reading Guide",
        "",
        "- `in_hot_quotes=yes` but `in_hot_movers=no` usually means the market is covered live, but the current 5m delta no longer clears the mover gates.",
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
