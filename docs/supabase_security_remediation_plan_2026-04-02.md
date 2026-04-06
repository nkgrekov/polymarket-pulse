# Supabase Security Remediation Plan (2026-04-02)

## Goal

Close the risky parts of the legacy `public` surface without breaking the current server-side runtime.

This is a modernization plan, not a dashboard click spree.

## Confirmed Problems

1. Many `public` tables and views currently have broad grants for:
   - `anon`
   - `authenticated`
2. Legacy `public` tables such as `public.watchlist_markets` have RLS disabled.
3. Supabase Security Advisor warnings about `SECURITY DEFINER`-style views are amplified by those open grants.
4. Some risky objects are not represented cleanly in current repo migrations, so they need careful handling.

## Safe Principles

1. Do not change app runtime and DB permissions in the same step.
2. Revoke access before redesigning schema names.
3. Keep server-side roles working:
   - `service_role`
   - `postgres`
4. Treat `public` as an attack surface, not as an internal namespace.
5. Do not rely on manual Supabase dashboard edits as source of truth.

## Priority Order

### P0. Inventory Lock-In

Artifacts:

- `scripts/ops/supabase_public_security_audit.py`
- `docs/supabase_public_security_latest.md`

Purpose:

- freeze a reproducible picture of current grants and public exposure
- avoid “we think this was public” ambiguity

### P1. Close Legacy User-Specific Public Objects

First candidates:

- `public.watchlist_markets`
- `public.watchlist`
- `public.watchlist_snapshot_latest`
- `public.watchlist_alerts_latest`
- `public.alerts_latest`
- `public.alerts_inbox_latest`
- `public.v_watchlist_tokens`
- `public.v_watchlist_movers_1h`
- `public.portfolio_snapshot_latest`

Safe action:

- revoke `anon` / `authenticated` privileges
- do not change server-side service roles yet

Why first:

- these objects look most likely to leak user-specific or delivery-specific state
- they are not part of the current intended public website contract

### P2. Tighten Public Analytical Views

Candidates:

- `public.top_movers_latest`
- `public.top_movers_1h`
- `public.global_bucket_latest`
- `public.buckets_latest`
- `public.snapshot_health`
- `public.hot_ingest_health_latest`

Questions to answer per object:

1. Should `anon` be able to read this?
2. Should `authenticated` be able to read this directly?
3. Should this move to a server-only schema later?
4. If it remains public, should it be `security_invoker = true`?

Current decision after Phase 1:

- treat these as server-only relations first
- close `anon` / `authenticated` grants before debating `security_invoker`
- only keep a relation publicly readable later if a concrete client-side need appears

### P3. Clean Up Legacy Drift

Special candidate:

- `public.watchlist_markets`

Why it is special:

- live in prod
- flagged by Supabase
- not clearly managed by current repo migrations

Safe action:

- first close access
- then decide whether to archive, migrate, or delete

### P4. GitHub Ingest Hygiene

Separate from Supabase security, but related operationally:

- failed run `23830942316` was caused by statement timeout during batch upsert to `public.markets`
- not caused by Node 20 deprecation warning

Safe action:

- keep GitHub Actions as backup / reconciliation path
- reduce batch pressure later if needed

## Recommended Implementation Sequence

1. Add a grant-hardening migration for `anon` / `authenticated` revokes on P1 objects.
2. Add a second grant-hardening migration for the remaining analytical/hot `public` objects.
3. Apply and verify that:
   - site still works
   - bot still works
   - live ingest still works
4. Generate a fresh security snapshot.
5. Only then decide whether to:
   - add `security_invoker = true`
   - move some views out of `public`
   - enable RLS on any still-user-facing tables

## Non-Goals Right Now

1. No immediate schema rename.
2. No broad RLS rollout across all `public`.
3. No simultaneous runtime refactor and privilege refactor.
4. No manual dashboard-only fixes that drift from repo history.
