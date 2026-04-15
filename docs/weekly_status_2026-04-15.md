# Weekly Status — 2026-04-15

## Runtime

- `site` is healthy on Railway:
  - deployment `02ce830a-1ba6-4fea-97ee-5254128d21cc`
  - status `SUCCESS`
- `bot` is healthy on Railway:
  - deployment `1579c5e5-cb37-4a4c-b7c8-e429d2f376a6`
  - status `SUCCESS`
- `ingest` is healthy on Railway:
  - deployment `aa7bbe26-52c8-45c8-83fe-e1fbdb561302`
  - status `SUCCESS`

## Hot Layer

- `public.hot_ingest_health_latest` looks healthy:
  - `registry_age_seconds = 61`
  - `quotes_age_seconds = 61`
  - `active_market_count = 407`
  - `two_sided_quote_count = 305`
  - `hot_movers_1m_count = 9`
  - `hot_movers_5m_count = 44`
- current hot surfaces are populated:
  - `hot_market_registry_latest = 420`
  - `hot_market_quotes_latest = 420`
  - `hot_top_movers_1m = 9`
  - `hot_top_movers_5m = 44`
  - `hot_watchlist_snapshot_latest = 13`
  - `hot_alert_candidates_latest = 13`

## Site Telemetry

- the telemetry path fix is now working in production
- fresh verification row:
  - `placement = diag_path_fix_8`
  - `path = /telegram-bot?utm_source=diag&utm_medium=codex&utm_campaign=pathfix8`
- important ops lesson:
  - for `site` source changes, deploy with `railway up -s site --path-as-root api`
  - plain `railway redeploy --service site` can preserve the previous monorepo snapshot

## Internal Funnel Snapshot

- recent `page_view` counts:
  - `2026-04-15`: `14`
  - `2026-04-14`: `7`
  - `2026-04-12`: `5`
  - `2026-04-11`: `5`
  - `2026-04-10`: `19`
  - `2026-04-09`: `11`
  - `2026-04-08`: `10`
  - `2026-04-07`: `2`
  - `2026-04-06`: `18`
- recent `tg_click` counts remain very small:
  - only `1` tracked `tg_click` in the last 7 days
  - placement: `hero_panel`
- the traffic dip looks real, but not like a fresh whole-site outage
- the top-of-funnel is still extremely thin

## Delivery Parity

- last 7 days:
  - `samples_total = 1918`
  - `non_quiet_samples = 570`
  - `hot_only_samples = 133`
  - `legacy_only_samples = 294`
  - `both_non_quiet_samples = 143`
- this means hot vs legacy delivery is no longer a quiet-window question
- there is real semantic divergence in both directions
- current recent windows show:
  - some periods with full overlap
  - some `legacy_only`
  - some `hot_only`

## Bot Reliability

- push-loop hardening helped, but the legacy path is still not fully calm
- fresh logs still show intermittent failures:
  - `db query retry=1/3 failed: canceling statement due to statement timeout`
  - `push_loop iteration failed`
  - `TimeoutError`
- so delivery is not ready for a blind hot-first cutover yet

## Practical Conclusion

- the hot read layer is now real and healthy
- site telemetry is now trustworthy again for new events
- the next main technical decision is still delivery, but it is now a **real comparison problem**, not a quiet-data problem
- the biggest growth constraint still appears to be tiny top-of-funnel volume, not a fresh site outage
