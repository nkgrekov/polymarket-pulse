# Hot Data Health Report (2026-03-27T11:24:03.019096+00:00)

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

- `OK` Registry freshness: 26s (threshold `180s`)
- `OK` Quotes freshness: 26s (threshold `120s`)
- `OK` Registry rows present: 411 rows
- `OK` Quote rows present: 411 rows
- `OK` Two-sided quote coverage: 275/411

## Phase Notes

- `V1 now` registry + quotes are expected to be live.
- `V1 now` hot 5m movers are expected to be live once the mover publish phase is deployed.
- `V1 later` hot 1m movers, watchlist snapshots, and alert candidates may still be empty until those worker writes are added.

## Snapshot

- active_market_count: **402**
- registry_rows: **411**
- quote_rows: **411**
- two_sided_quote_rows: **275**
- hot_movers_1m_count: **0**
- hot_movers_5m_count: **14**
- hot_watchlist_snapshot_latest rows: **0**
- hot_alert_candidates_latest rows: **0**
- updated_at: **2026-03-27 11:23:38.320059+00:00**

## Review Notes

- Treat this as the first operational heartbeat for the new hot layer.
- `hot_top_movers_5m` should now be non-empty during healthy market conditions; `hot_top_movers_1m`, watchlist, and alert tables may still be empty until their publish phases land.
- Do not cut over homepage or bot reads until this report stays healthy over repeated ticks.
