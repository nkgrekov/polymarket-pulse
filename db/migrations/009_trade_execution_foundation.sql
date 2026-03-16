begin;

create schema if not exists trade;

create table if not exists trade.accounts (
  id bigserial primary key,
  user_id uuid not null unique references app.users(id) on delete cascade,
  status text not null default 'active',
  execution_mode text not null default 'manual',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (status in ('active', 'paused', 'blocked')),
  check (execution_mode in ('manual', 'rule_auto'))
);

create table if not exists trade.wallet_links (
  id bigserial primary key,
  account_id bigint not null references trade.accounts(id) on delete cascade,
  wallet_address text not null,
  chain text not null default 'polygon',
  signer_kind text not null default 'delegated',
  signer_ref text,
  label text,
  is_primary boolean not null default false,
  status text not null default 'pending',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (wallet_address),
  check (status in ('pending', 'active', 'revoked')),
  check (signer_kind in ('delegated', 'manual', 'session'))
);

create index if not exists idx_trade_wallet_links_account
  on trade.wallet_links (account_id, status, is_primary desc);

create table if not exists trade.positions_cache (
  account_id bigint not null references trade.accounts(id) on delete cascade,
  market_id text not null references public.markets(market_id) on delete cascade,
  outcome_side text not null,
  size numeric not null default 0,
  avg_price numeric,
  current_price numeric,
  unrealized_pnl numeric,
  as_of_bucket timestamptz,
  updated_at timestamptz not null default now(),
  primary key (account_id, market_id, outcome_side),
  check (outcome_side in ('yes', 'no'))
);

create table if not exists trade.orders (
  id bigserial primary key,
  account_id bigint not null references trade.accounts(id) on delete cascade,
  market_id text not null references public.markets(market_id) on delete cascade,
  side text not null,
  outcome_side text not null,
  order_type text not null default 'market',
  status text not null default 'pending',
  source text not null default 'manual',
  requested_size_usd numeric not null,
  requested_price numeric,
  limit_price numeric,
  slippage_bps integer,
  client_order_key text unique,
  external_order_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (side in ('buy', 'sell')),
  check (outcome_side in ('yes', 'no')),
  check (order_type in ('market', 'limit')),
  check (status in ('pending', 'submitted', 'partially_filled', 'filled', 'canceled', 'rejected', 'failed')),
  check (source in ('manual', 'agent', 'follow'))
);

create index if not exists idx_trade_orders_account_created
  on trade.orders (account_id, created_at desc);

create table if not exists trade.executions (
  id bigserial primary key,
  order_id bigint not null references trade.orders(id) on delete cascade,
  account_id bigint not null references trade.accounts(id) on delete cascade,
  market_id text not null references public.markets(market_id) on delete cascade,
  side text not null,
  outcome_side text not null,
  fill_size_usd numeric not null,
  fill_price numeric not null,
  external_fill_id text unique,
  payload jsonb not null default '{}'::jsonb,
  filled_at timestamptz not null default now(),
  check (side in ('buy', 'sell')),
  check (outcome_side in ('yes', 'no'))
);

create index if not exists idx_trade_executions_account_filled
  on trade.executions (account_id, filled_at desc);

create table if not exists trade.follow_sources (
  id bigserial primary key,
  account_id bigint not null references trade.accounts(id) on delete cascade,
  source_kind text not null default 'wallet',
  source_ref text not null,
  label text,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (account_id, source_kind, source_ref),
  check (source_kind in ('wallet', 'trader', 'feed')),
  check (status in ('active', 'paused', 'removed'))
);

create table if not exists trade.follow_rules (
  id bigserial primary key,
  account_id bigint not null references trade.accounts(id) on delete cascade,
  follow_source_id bigint not null references trade.follow_sources(id) on delete cascade,
  enabled boolean not null default true,
  copy_mode text not null default 'mirror',
  max_order_usd numeric not null default 25,
  max_slippage_bps integer not null default 150,
  daily_trade_cap integer not null default 5,
  daily_loss_cap_usd numeric not null default 25,
  allowed_categories text[] not null default '{}'::text[],
  blocked_markets text[] not null default '{}'::text[],
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (copy_mode in ('mirror', 'assist', 'observe'))
);

create table if not exists trade.agent_rules (
  account_id bigint primary key references trade.accounts(id) on delete cascade,
  enabled boolean not null default true,
  paused boolean not null default false,
  mode text not null default 'manual',
  require_confirm boolean not null default true,
  max_order_usd numeric not null default 25,
  daily_trade_cap integer not null default 5,
  daily_loss_cap_usd numeric not null default 25,
  per_market_exposure_usd numeric not null default 50,
  slippage_bps integer not null default 150,
  cooldown_minutes integer not null default 15,
  allowed_categories text[] not null default '{}'::text[],
  allowlisted_markets text[] not null default '{}'::text[],
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (mode in ('manual', 'rule_auto'))
);

create table if not exists trade.agent_decisions (
  id bigserial primary key,
  account_id bigint not null references trade.accounts(id) on delete cascade,
  market_id text references public.markets(market_id) on delete set null,
  decision_type text not null,
  reason text,
  source_rule text,
  confidence numeric,
  proposed_side text,
  proposed_outcome_side text,
  proposed_size_usd numeric,
  proposed_price numeric,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  check (decision_type in ('suggest', 'execute', 'skip', 'block')),
  check (proposed_side is null or proposed_side in ('buy', 'sell')),
  check (proposed_outcome_side is null or proposed_outcome_side in ('yes', 'no'))
);

create index if not exists idx_trade_agent_decisions_account_created
  on trade.agent_decisions (account_id, created_at desc);

create table if not exists trade.risk_state (
  account_id bigint primary key references trade.accounts(id) on delete cascade,
  paused boolean not null default false,
  kill_switch boolean not null default false,
  daily_orders_count integer not null default 0,
  daily_loss_usd numeric not null default 0,
  daily_volume_usd numeric not null default 0,
  current_exposure_usd numeric not null default 0,
  last_trade_at timestamptz,
  updated_at timestamptz not null default now()
);

create table if not exists trade.activity_events (
  id bigserial primary key,
  user_id uuid not null references app.users(id) on delete cascade,
  account_id bigint references trade.accounts(id) on delete set null,
  event_type text not null,
  source text not null default 'pulse_bot',
  market_id text,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  check (source in ('pulse_bot', 'telegram_bot', 'site', 'x', 'threads', 'worker', 'manual'))
);

create index if not exists idx_trade_activity_events_user_created
  on trade.activity_events (user_id, created_at desc);

create table if not exists trade.alpha_waitlist (
  id bigserial primary key,
  email text not null unique,
  user_id uuid references app.users(id) on delete set null,
  telegram_id bigint,
  chat_id bigint,
  source text not null default 'site',
  status text not null default 'new',
  use_case text not null default 'execution_alpha',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (source in ('site', 'pulse_bot', 'telegram_bot', 'x', 'threads', 'manual')),
  check (status in ('new', 'review', 'approved', 'declined'))
);

create or replace function trade.ensure_account(p_user_id uuid)
returns bigint
language plpgsql
as $$
declare
  v_account_id bigint;
begin
  select id
    into v_account_id
  from trade.accounts
  where user_id = p_user_id
  limit 1;

  if v_account_id is null then
    insert into trade.accounts (user_id)
    values (p_user_id)
    returning id into v_account_id;

    insert into trade.agent_rules (account_id)
    values (v_account_id)
    on conflict (account_id) do nothing;

    insert into trade.risk_state (account_id)
    values (v_account_id)
    on conflict (account_id) do nothing;
  end if;

  return v_account_id;
end;
$$;

drop trigger if exists trg_trade_accounts_updated_at on trade.accounts;
create trigger trg_trade_accounts_updated_at before update on trade.accounts
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_trade_wallet_links_updated_at on trade.wallet_links;
create trigger trg_trade_wallet_links_updated_at before update on trade.wallet_links
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_trade_orders_updated_at on trade.orders;
create trigger trg_trade_orders_updated_at before update on trade.orders
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_trade_follow_sources_updated_at on trade.follow_sources;
create trigger trg_trade_follow_sources_updated_at before update on trade.follow_sources
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_trade_follow_rules_updated_at on trade.follow_rules;
create trigger trg_trade_follow_rules_updated_at before update on trade.follow_rules
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_trade_agent_rules_updated_at on trade.agent_rules;
create trigger trg_trade_agent_rules_updated_at before update on trade.agent_rules
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_trade_risk_state_updated_at on trade.risk_state;
create trigger trg_trade_risk_state_updated_at before update on trade.risk_state
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_trade_alpha_waitlist_updated_at on trade.alpha_waitlist;
create trigger trg_trade_alpha_waitlist_updated_at before update on trade.alpha_waitlist
for each row execute function bot.touch_updated_at();

commit;
