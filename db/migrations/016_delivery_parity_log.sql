begin;

create table if not exists bot.delivery_parity_log (
  id bigserial primary key,
  sampled_at timestamptz not null default now(),
  hot_ready_count bigint not null default 0,
  legacy_watchlist_count bigint not null default 0,
  overlap_count bigint not null default 0,
  hot_only_count bigint not null default 0,
  legacy_only_count bigint not null default 0,
  top_hot_market_id text,
  top_legacy_market_id text,
  top_hot_abs_delta numeric,
  top_legacy_abs_delta numeric,
  payload jsonb not null default '{}'::jsonb
);

create index if not exists idx_bot_delivery_parity_log_sampled_at
  on bot.delivery_parity_log (sampled_at desc);

commit;
