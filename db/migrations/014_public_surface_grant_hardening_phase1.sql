begin;

-- Phase 1: close the highest-risk user-specific relations in `public`
-- without touching service_role/postgres or changing runtime schemas.

revoke all privileges on table public.watchlist from anon, authenticated;
revoke all privileges on table public.watchlist_markets from anon, authenticated;
revoke all privileges on table public.watchlist_snapshot_latest from anon, authenticated;
revoke all privileges on table public.watchlist_alerts_latest from anon, authenticated;
revoke all privileges on table public.alerts_latest from anon, authenticated;
revoke all privileges on table public.alerts_inbox_latest from anon, authenticated;
revoke all privileges on table public.v_watchlist_tokens from anon, authenticated;
revoke all privileges on table public.v_watchlist_movers_1h from anon, authenticated;
revoke all privileges on table public.portfolio_snapshot_latest from anon, authenticated;

-- Hot user-specific surfaces should never be public client surfaces.
revoke all privileges on table public.hot_watchlist_snapshot_latest from anon, authenticated;
revoke all privileges on table public.hot_alert_candidates_latest from anon, authenticated;

-- Legacy user-linked tables also should not stay open to anon/authenticated.
revoke all privileges on table public.user_positions from anon, authenticated;
revoke all privileges on table public.sent_alerts_log from anon, authenticated;
revoke all privileges on table public.sent_alerts_log_legacy from anon, authenticated;

commit;
