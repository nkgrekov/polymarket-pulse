# Hot Data Health Report (2026-03-31T07:26:06.882326+00:00)

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

- `OK` Registry freshness: 13s (threshold `180s`)
- `OK` Quotes freshness: 13s (threshold `120s`)
- `OK` Registry rows present: 423 rows
- `OK` Quote rows present: 423 rows
- `OK` Two-sided quote coverage: 308/423

## Phase Notes

- `V1 now` registry + quotes are expected to be live.
- `V1 now` hot 5m movers are expected to be live once the mover publish phase is deployed.
- `V1 now` hot watchlist snapshots and hot alert candidates are expected to be live now.
- `V1 now` hot 1m movers are expected to be live now.

## Snapshot

- active_market_count: **414**
- registry_rows: **423**
- quote_rows: **423**
- two_sided_quote_rows: **308**
- hot_movers_1m_count: **22**
- hot_movers_5m_count: **44**
- hot_watchlist_snapshot_latest rows: **9**
- hot_alert_candidates_latest rows: **9**
- updated_at: **2026-03-31 07:25:54.052701+00:00**

## Review Notes

- Treat this as the first operational heartbeat for the new hot layer.
- `hot_top_movers_5m` should now be non-empty during healthy market conditions; `hot_watchlist_snapshot_latest` and `hot_alert_candidates_latest` should also stay non-empty when users track markets.
- `hot_top_movers_1m` should now be non-empty during healthy market conditions as the live worker publishes it from the previous hot quote anchor.
- Do not cut over homepage or bot reads until this report stays healthy over repeated ticks.
