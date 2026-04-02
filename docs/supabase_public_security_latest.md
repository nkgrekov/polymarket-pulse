# Supabase Public Security Snapshot (2026-04-02T12:46:31.834154+00:00)

Source:

- `pg_class` / `pg_namespace` for public relations
- `information_schema.role_table_grants` for public grants

## Summary

- public_objects: **31**
- objects_granted_to_anon: **17**
- objects_granted_to_authenticated: **17**
- rls_disabled_public_tables: **14**

## Priority Findings

- `anon` and `authenticated` currently have broad grants on many `public` views and tables, not just read-only analytics surfaces.
- legacy watchlist / alert relations in `public` are the highest-risk objects because they look user-specific yet sit in the public schema with open grants.
- `SECURITY DEFINER`-style advisor noise matters more here because underlying grants are also too broad.
- `public.watchlist_markets` is especially suspicious because it is live in the database but not managed in current repo migrations.

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
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

### `public.hot_market_registry_latest`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

### `public.hot_top_movers_1m`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

### `public.hot_top_movers_5m`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

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
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

### `public.market_universe`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

### `public.markets`
- kind: **table**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

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
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

### `public.buckets_latest`
- kind: **view**
- classification: **keep-public-review-grants**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

### `public.global_bucket_latest`
- kind: **view**
- classification: **keep-public-review-grants**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

### `public.hot_ingest_health_latest`
- kind: **view**
- classification: **keep-public-review-grants**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

### `public.live_markets_latest`
- kind: **view**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

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
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

### `public.top_movers_1h`
- kind: **view**
- classification: **keep-public-review-grants**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

### `public.top_movers_24h`
- kind: **view**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

### `public.top_movers_latest`
- kind: **view**
- classification: **keep-public-review-grants**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

### `public.user_watchlist`
- kind: **view**
- classification: **review**
- rls_enabled: **false**
- rls_forced: **false**
- reloptions: **none**
- anon/authenticated grants: **anon:DELETE, anon:INSERT, anon:REFERENCES, anon:SELECT, anon:TRIGGER, anon:TRUNCATE, anon:UPDATE, authenticated:DELETE, authenticated:INSERT, authenticated:REFERENCES, authenticated:SELECT, authenticated:TRIGGER, authenticated:TRUNCATE, authenticated:UPDATE**

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
