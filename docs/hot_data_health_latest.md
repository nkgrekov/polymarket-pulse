# Hot Data Health Report (2026-03-31T07:06:56.495883+00:00)

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

- `OK` Registry freshness: 60s (threshold `180s`)
- `OK` Quotes freshness: 60s (threshold `120s`)
- `OK` Registry rows present: 403 rows
- `OK` Quote rows present: 403 rows
- `OK` Two-sided quote coverage: 333/403

## Phase Notes

- `V1 now` registry + quotes are expected to be live.
- `V1 now` hot 5m movers are expected to be live once the mover publish phase is deployed.
- `V1 now` hot watchlist snapshots and hot alert candidates are expected to be live now.
- `V1 later` hot 1m movers may still be empty until that worker write is added.

## Snapshot

- active_market_count: **394**
- registry_rows: **403**
- quote_rows: **403**
- two_sided_quote_rows: **333**
- hot_movers_1m_count: **0**
- hot_movers_5m_count: **64**
- hot_watchlist_snapshot_latest rows: **9**
- hot_alert_candidates_latest rows: **9**
- updated_at: **2026-03-31 07:05:56.735637+00:00**

## Review Notes

- Treat this as the first operational heartbeat for the new hot layer.
- `hot_top_movers_5m` should now be non-empty during healthy market conditions; `hot_watchlist_snapshot_latest` and `hot_alert_candidates_latest` should also stay non-empty when users track markets.
- `hot_top_movers_1m` may still be empty until its publish phase lands.
- Do not cut over homepage or bot reads until this report stays healthy over repeated ticks.
