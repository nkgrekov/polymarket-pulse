# Data Core Health Report (2026-03-23T08:33:00.202163+00:00)

Source: `public.analytics_core_health_latest`

## Core Contract

- `public.market_snapshots`
- `public.market_universe`
- `public.snapshot_health`
- `public.top_movers_latest`
- `public.top_movers_1h`
- `public.top_movers_24h`

## Health Checks

- `CHECK` Freshness lag: 1078s (latest bucket `2026-03-23 08:15:00+00:00`; threshold `900s`)
- `OK` Latest yes-quote coverage: 92.4% (threshold `90.0%`)
- `OK` Latest universe coverage: 200/200
- `OK` Previous-bucket universe coverage: 200/200
- `OK` Current movers output: 33 non-zero movers out of 200 rows
- `OK` 1h movers output: 60 non-zero movers out of 230 rows
- `OK` 24h movers output: 69 non-zero movers out of 105 rows

## Snapshot

- latest_bucket_rows: **303**
- latest_yes_quoted: **280**
- movers_latest_max_abs_delta: **0.360**
- movers_1h_max_abs_delta: **0.499**
- movers_24h_max_abs_delta: **0.235**

## Review Notes

- Treat this as a read-only health view over the analytical core.
- Do not use it as a reason to re-plumb the live Pulse runtime from `bot.*` this week.
- If freshness or universe coverage degrades, fix ingest/core first before touching user-facing bot UX.
