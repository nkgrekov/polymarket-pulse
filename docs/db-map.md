# Database Map (Supabase)

Generated at (UTC): 2026-03-02T12:35:00Z
Project ref: `phoxorscorapbzhhpijl`
Source: Supabase MCP (`list_tables` verified working on 2026-03-02; `execute_sql` still times out in this session)

## Is This a Skill or Live DB Access?
- This is **not** a new Codex skill.
- This is a **live MCP integration** to your Supabase project.
- Yes, with this setup we can operate on DB changes and code changes in one workflow (repo code + Telegram bot code), including applying migrations via MCP tools.
- Current runtime state on 2026-03-02: MCP auth/login is healthy again, metadata reads via `list_tables` work, but SQL execution via `execute_sql` still hangs.

## Schemas Discovered
- `public`
- `auth`
- `storage`
- `realtime`
- `vault`

## Public Schema

### `public.markets`
- Row estimate: `129318`
- RLS enabled: `false`
- Primary key: `market_id`
- Foreign keys (incoming references seen via metadata):
  - `public.watchlist.market_id -> public.markets.market_id`
  - `public.market_snapshots.market_id -> public.markets.market_id`
- Columns:
  - `market_id text not null`
  - `slug text null`
  - `question text null`
  - `category text null`
  - `status text null`
  - `created_at timestamptz null default now()`
  - `yes_token_id text null`
  - `no_token_id text null`

### `public.market_snapshots`
- Row estimate: `263871`
- RLS enabled: `false`
- Primary key: `(market_id, ts_bucket)`
- Foreign keys:
  - `market_snapshots_market_id_fkey: public.market_snapshots.market_id -> public.markets.market_id`
- Columns:
  - `market_id text not null`
  - `ts_bucket timestamptz not null`
  - `yes_price numeric null`
  - `no_price numeric null`
  - `liquidity numeric null`
  - `yes_bid numeric null`
  - `yes_ask numeric null`
  - `no_bid numeric null`
  - `no_ask numeric null`

### `public.watchlist_markets`
- Row estimate: `3734`
- RLS enabled: `false`
- Primary key: `market_id`
- Foreign keys: none exposed by `list_tables`
- Columns:
  - `market_id text not null`
  - `added_at timestamptz null default now()`

### `public.watchlist`
- Row estimate: `5`
- RLS enabled: `false`
- Primary key: `(user_id, market_id)`
- Foreign keys:
  - `watchlist_market_id_fkey: public.watchlist.market_id -> public.markets.market_id`
- Columns:
  - `user_id text not null`
  - `market_id text not null`
  - `created_at timestamptz not null default now()`

### `public.user_positions`
- Row estimate: `3`
- RLS enabled: `false`
- Primary key: `id`
- Foreign keys: none exposed by `list_tables`
- Check constraints (column-level metadata):
  - `side IN ('yes','no')`
  - `size > 0`
  - `avg_price >= 0 AND avg_price <= 1`
- Columns:
  - `id bigint not null default nextval('user_positions_id_seq')`
  - `user_id text not null`
  - `market_id text not null`
  - `side text not null`
  - `size numeric not null`
  - `avg_price numeric not null`
  - `created_at timestamptz not null default now()`
  - `updated_at timestamptz not null default now()`

### `public.sent_alerts_log`
- Row estimate: `0`
- RLS enabled: `false`
- Primary key: `id`
- Foreign keys: none exposed by `list_tables`
- Columns:
  - `id bigint not null default nextval('sent_alerts_log_id_seq')`
  - `user_id text null`
  - `market_id bigint null`
  - `side text null`
  - `bucket timestamptz null`
  - `created_at timestamptz null default now()`

## Public Indexes
- Status: `unavailable in this run`
- Note: attempted via MCP `execute_sql` (`pg_indexes` query), but call did not return in the current CLI session.
- Health-check: `execute_sql` also did not return for `select 1 as ok`, so this is currently an MCP SQL-channel issue in this environment, not a query-size issue.

## Public RLS Policies
- RLS flag from table metadata: `false` for all `public` tables.
- Policies detail: `unavailable in this run`
- Note: attempted via MCP `execute_sql` (`pg_policies` query), but call did not return in the current CLI session.

## Runtime Verification
- `codex mcp login supabase` re-run successfully on `2026-03-02`.
- `supabase.list_tables({\"schemas\":[\"public\"]})` succeeded after re-login.
- `mcp__supabase__execute_sql` still timed out after re-login, including on `select 1 as ok`.

## Fast Follow-Up (When SQL Channel Responds)
- Public indexes SQL:
  - `select schemaname, tablename, indexname, indexdef from pg_indexes where schemaname='public' order by tablename, indexname;`
- Public policies SQL:
  - `select schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check from pg_policies where schemaname='public' order by tablename, policyname;`

## Consistency / Risk Notes
- `public` tables have RLS disabled; if app/Telegram bot endpoints become user-facing with Supabase auth tokens, data access may be broader than expected.
- `watchlist_markets` appears denormalized relative to `watchlist`; verify intended ownership and source-of-truth.
- `sent_alerts_log.market_id` is `bigint`, while primary market key in core tables is `text`; type mismatch can create join friction and weak referential integrity.
- `user_positions.market_id` has no FK to `markets.market_id`; consider adding FK if historical orphan rows are not required.
