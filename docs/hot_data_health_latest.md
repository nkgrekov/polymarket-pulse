# Hot Data Health Report (2026-03-27T11:06:15.250426+00:00)

Source: `public.hot_ingest_health_latest` + direct counts from V1 hot tables

## Hot Contract

- `public.hot_market_registry_latest`
- `public.hot_market_quotes_latest`
- `public.hot_top_movers_1m`
- `public.hot_top_movers_5m`
- `public.hot_watchlist_snapshot_latest`
- `public.hot_alert_candidates_latest`
- `public.hot_ingest_health_latest`

## Health Checks

- `OK` Registry freshness: 42s (threshold `180s`)
- `OK` Quotes freshness: 42s (threshold `120s`)
- `OK` Registry rows present: 411 rows
- `OK` Quote rows present: 411 rows
- `OK` Two-sided quote coverage: 277/411

## Phase Notes

- `V1 now` registry + quotes are expected to be live.
- `V1 later` hot movers, watchlist snapshots, and alert candidates may still be empty until those worker writes are added.

## Snapshot

- active_market_count: **402**
- registry_rows: **411**
- quote_rows: **411**
- two_sided_quote_rows: **277**
- hot_movers_1m_count: **0**
- hot_movers_5m_count: **0**
- hot_watchlist_snapshot_latest rows: **0**
- hot_alert_candidates_latest rows: **0**
- updated_at: **2026-03-27 11:05:33.325011+00:00**

## Review Notes

- Treat this as the first operational heartbeat for the new hot layer.
- Empty movers/watchlist/alert tables are expected until the worker publishes those surfaces.
- Do not cut over homepage or bot reads until this report stays healthy over repeated ticks.
