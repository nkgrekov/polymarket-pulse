# Supabase Public Security Snapshot (2026-04-06T09:48:57.571422+00:00)

Source:

- `pg_class` / `pg_namespace` for public relations
- `information_schema.role_table_grants` for public grants

## Summary

- public_objects: **31**
- objects_granted_to_anon: **0**
- objects_granted_to_authenticated: **0**
- rls_disabled_public_tables: **14**

## Priority Findings

- `anon` and `authenticated` no longer have grants on the audited `public` relations in this snapshot.
- the remaining risk is structural rather than grant-based:
  - legacy public tables still have RLS disabled
  - Supabase Security Advisor can still complain about view semantics in `public`
- `public.watchlist_markets` remains suspicious legacy drift because it exists live in the database but is not clearly managed in current repo migrations.
- the next security work should focus on legacy drift cleanup and whether any remaining public views need `security_invoker = true` or a schema move.

## Object Inventory

### `public.hot_alert_candidates_latest`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.hot_market_quotes_latest`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.hot_market_registry_latest`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.hot_top_movers_1m`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.hot_top_movers_5m`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.hot_watchlist_snapshot_latest`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.market_snapshots`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.market_universe`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.markets`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.sent_alerts_log`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.sent_alerts_log_legacy`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.user_positions`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.watchlist`
- kind: **table**
- classification: **close-first**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.watchlist_markets`
- kind: **table**
- classification: **close-first**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.alerts_inbox_latest`
- kind: **view**
- classification: **close-first**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.alerts_latest`
- kind: **view**
- classification: **close-first**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.analytics_core_health_latest`
- kind: **view**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.buckets_latest`
- kind: **view**
- classification: **keep-public-review-grants**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.global_bucket_latest`
- kind: **view**
- classification: **keep-public-review-grants**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.hot_ingest_health_latest`
- kind: **view**
- classification: **keep-public-review-grants**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.live_markets_latest`
- kind: **view**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.portfolio_snapshot_latest`
- kind: **view**
- classification: **close-first**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.snapshot_health`
- kind: **view**
- classification: **keep-public-review-grants**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.top_movers_1h`
- kind: **view**
- classification: **keep-public-review-grants**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.top_movers_24h`
- kind: **view**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.top_movers_latest`
- kind: **view**
- classification: **keep-public-review-grants**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.user_watchlist`
- kind: **view**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.v_watchlist_movers_1h`
- kind: **view**
- classification: **close-first**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.v_watchlist_tokens`
- kind: **view**
- classification: **close-first**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.watchlist_alerts_latest`
- kind: **view**
- classification: **close-first**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

### `public.watchlist_snapshot_latest`
- kind: **view**
- classification: **close-first**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **none**

## Recommended Buckets

### Close First

- `public.alerts_inbox_latest`
- `public.alerts_latest`
- `public.portfolio_snapshot_latest`
- `public.v_watchlist_movers_1h`
- `public.v_watchlist_tokens`
- `public.watchlist`
- `public.watchlist_alerts_latest`
- `public.watchlist_markets`
- `public.watchlist_snapshot_latest`

### Keep Public, But Tighten

- `public.buckets_latest`
- `public.global_bucket_latest`
- `public.hot_ingest_health_latest`
- `public.snapshot_health`
- `public.top_movers_1h`
- `public.top_movers_latest`

### Review Manually

- `public.analytics_core_health_latest`
- `public.hot_alert_candidates_latest`
- `public.hot_market_quotes_latest`
- `public.hot_market_registry_latest`
- `public.hot_top_movers_1m`
- `public.hot_top_movers_5m`
- `public.hot_watchlist_snapshot_latest`
- `public.live_markets_latest`
- `public.market_snapshots`
- `public.market_universe`
- `public.markets`
- `public.sent_alerts_log`
- `public.sent_alerts_log_legacy`
- `public.top_movers_24h`
- `public.user_positions`
- `public.user_watchlist`

## Notes

- This snapshot is intentionally grant-focused. It does not change any runtime permissions by itself.
- `SECURITY DEFINER` advisories become materially important when `anon` / `authenticated` also have open grants.
- Use this report to drive additive revoke / schema-hardening migrations, not ad-hoc dashboard clicks.
