begin;

-- Phase 2: close the remaining analytical and hot-layer relations in `public`
-- for anon/authenticated. Current runtime uses server-side DB access only.

revoke all privileges on table public.analytics_core_health_latest from anon, authenticated;
revoke all privileges on table public.buckets_latest from anon, authenticated;
revoke all privileges on table public.global_bucket_latest from anon, authenticated;
revoke all privileges on table public.hot_ingest_health_latest from anon, authenticated;
revoke all privileges on table public.hot_market_quotes_latest from anon, authenticated;
revoke all privileges on table public.hot_market_registry_latest from anon, authenticated;
revoke all privileges on table public.hot_top_movers_1m from anon, authenticated;
revoke all privileges on table public.hot_top_movers_5m from anon, authenticated;
revoke all privileges on table public.live_markets_latest from anon, authenticated;
revoke all privileges on table public.market_snapshots from anon, authenticated;
revoke all privileges on table public.market_universe from anon, authenticated;
revoke all privileges on table public.markets from anon, authenticated;
revoke all privileges on table public.snapshot_health from anon, authenticated;
revoke all privileges on table public.top_movers_1h from anon, authenticated;
revoke all privileges on table public.top_movers_24h from anon, authenticated;
revoke all privileges on table public.top_movers_latest from anon, authenticated;
revoke all privileges on table public.user_watchlist from anon, authenticated;

commit;
