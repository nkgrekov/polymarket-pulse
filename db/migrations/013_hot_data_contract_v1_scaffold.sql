begin;

create or replace function public.hot_touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists public.hot_market_registry_latest (
  market_id text primary key,
  slug text not null,
  question text not null,
  status text not null default 'active',
  end_date timestamptz,
  event_title text,
  category text,
  token_yes text,
  token_no text,
  updated_at timestamptz not null default now(),
  source_ts timestamptz not null,
  check (char_length(trim(slug)) > 0),
  check (char_length(trim(question)) > 0),
  check (char_length(trim(status)) > 0)
);

comment on table public.hot_market_registry_latest is
'Hot Data Contract V1: latest live market registry for product-facing reads. Worker is expected to upsert current active rows and prune stale rows. Additive scaffold only; no runtime cutover.';

create index if not exists idx_hot_market_registry_latest_slug
  on public.hot_market_registry_latest (slug);

create index if not exists idx_hot_market_registry_latest_status_source
  on public.hot_market_registry_latest (status, source_ts desc);

drop trigger if exists trg_hot_market_registry_latest_updated_at on public.hot_market_registry_latest;
create trigger trg_hot_market_registry_latest_updated_at
before update on public.hot_market_registry_latest
for each row execute function public.hot_touch_updated_at();

create table if not exists public.hot_market_quotes_latest (
  market_id text primary key,
  bid_yes numeric,
  ask_yes numeric,
  mid_yes numeric,
  liquidity numeric,
  spread numeric,
  quote_ts timestamptz not null,
  ingested_at timestamptz not null default now(),
  freshness_seconds integer not null default 0,
  has_two_sided_quote boolean not null default false,
  check (bid_yes is null or (bid_yes >= 0 and bid_yes <= 1)),
  check (ask_yes is null or (ask_yes >= 0 and ask_yes <= 1)),
  check (mid_yes is null or (mid_yes >= 0 and mid_yes <= 1)),
  check (liquidity is null or liquidity >= 0),
  check (spread is null or (spread >= 0 and spread <= 1)),
  check (freshness_seconds >= 0)
);

comment on table public.hot_market_quotes_latest is
'Hot Data Contract V1: latest live quote state per market. Worker is expected to overwrite latest quote state per market and prune stale rows when coverage changes.';

comment on column public.hot_market_quotes_latest.freshness_seconds is
'Worker-maintained age of the underlying quote at write time. Intended for hot read gating, not historical analysis.';

comment on column public.hot_market_quotes_latest.has_two_sided_quote is
'True when both sides of the YES quote are present and internally valid for hot read quality checks.';

create index if not exists idx_hot_market_quotes_latest_quote_ts
  on public.hot_market_quotes_latest (quote_ts desc);

create index if not exists idx_hot_market_quotes_latest_quality
  on public.hot_market_quotes_latest (has_two_sided_quote, freshness_seconds, liquidity desc);

create table if not exists public.hot_top_movers_1m (
  market_id text primary key,
  question text not null,
  slug text not null,
  prev_mid numeric not null,
  current_mid numeric not null,
  delta_mid numeric not null,
  delta_abs numeric not null,
  liquidity numeric,
  spread numeric,
  score numeric not null,
  window_start timestamptz not null,
  window_end timestamptz not null,
  quote_ts timestamptz not null,
  ingested_at timestamptz not null default now(),
  check (char_length(trim(question)) > 0),
  check (char_length(trim(slug)) > 0),
  check (prev_mid >= 0 and prev_mid <= 1),
  check (current_mid >= 0 and current_mid <= 1),
  check (liquidity is null or liquidity >= 0),
  check (spread is null or (spread >= 0 and spread <= 1)),
  check (delta_abs >= 0),
  check (window_end >= window_start)
);

comment on table public.hot_top_movers_1m is
'Hot Data Contract V1: very fresh tape-style movers. Worker is expected to rebuild/prune this latest window output as a scored snapshot; no runtime reads switched yet.';

comment on column public.hot_top_movers_1m.score is
'Composite worker-owned ranking score combining delta magnitude with quote quality, freshness, and liquidity gates.';

create index if not exists idx_hot_top_movers_1m_score
  on public.hot_top_movers_1m (score desc, delta_abs desc, quote_ts desc);

create table if not exists public.hot_top_movers_5m (
  market_id text primary key,
  question text not null,
  slug text not null,
  prev_mid numeric not null,
  current_mid numeric not null,
  delta_mid numeric not null,
  delta_abs numeric not null,
  liquidity numeric,
  spread numeric,
  score numeric not null,
  window_start timestamptz not null,
  window_end timestamptz not null,
  quote_ts timestamptz not null,
  ingested_at timestamptz not null default now(),
  check (char_length(trim(question)) > 0),
  check (char_length(trim(slug)) > 0),
  check (prev_mid >= 0 and prev_mid <= 1),
  check (current_mid >= 0 and current_mid <= 1),
  check (liquidity is null or liquidity >= 0),
  check (spread is null or (spread >= 0 and spread <= 1)),
  check (delta_abs >= 0),
  check (window_end >= window_start)
);

comment on table public.hot_top_movers_5m is
'Hot Data Contract V1: primary user-facing hot movers surface. Worker is expected to rebuild/prune this latest window output before any additive read cutover.';

comment on column public.hot_top_movers_5m.score is
'Composite worker-owned ranking score combining delta magnitude with quote quality, freshness, and liquidity gates.';

create index if not exists idx_hot_top_movers_5m_score
  on public.hot_top_movers_5m (score desc, delta_abs desc, quote_ts desc);

create table if not exists public.hot_watchlist_snapshot_latest (
  app_user_id uuid not null references app.users(id) on delete cascade,
  market_id text not null,
  question text not null,
  slug text not null,
  status text not null,
  mid_current numeric,
  mid_prev_5m numeric,
  delta_mid numeric,
  liquidity numeric,
  spread numeric,
  live_state text not null,
  quote_ts timestamptz,
  ingested_at timestamptz not null default now(),
  primary key (app_user_id, market_id),
  check (char_length(trim(question)) > 0),
  check (char_length(trim(slug)) > 0),
  check (char_length(trim(status)) > 0),
  check (mid_current is null or (mid_current >= 0 and mid_current <= 1)),
  check (mid_prev_5m is null or (mid_prev_5m >= 0 and mid_prev_5m <= 1)),
  check (liquidity is null or liquidity >= 0),
  check (spread is null or (spread >= 0 and spread <= 1)),
  check (live_state in ('ready', 'partial', 'no_quotes', 'closed', 'date_passed_active'))
);

comment on table public.hot_watchlist_snapshot_latest is
'Hot Data Contract V1: latest per-user watchlist state from hot registry + quotes. Worker is expected to upsert current rows for tracked markets and prune rows when membership/status changes; legacy watchlist runtime stays unchanged for now.';

comment on column public.hot_watchlist_snapshot_latest.live_state is
'Suggested V1 state vocabulary: ready, partial, no_quotes, closed, date_passed_active.';

create index if not exists idx_hot_watchlist_snapshot_latest_user_quote
  on public.hot_watchlist_snapshot_latest (app_user_id, quote_ts desc, ingested_at desc);

create index if not exists idx_hot_watchlist_snapshot_latest_state
  on public.hot_watchlist_snapshot_latest (live_state, ingested_at desc);

create index if not exists idx_hot_watchlist_snapshot_latest_user_state
  on public.hot_watchlist_snapshot_latest (app_user_id, live_state, ingested_at desc);

create table if not exists public.hot_alert_candidates_latest (
  app_user_id uuid not null references app.users(id) on delete cascade,
  market_id text not null,
  question text not null,
  delta_mid numeric not null,
  delta_abs numeric not null,
  threshold_value numeric not null,
  liquidity numeric,
  spread numeric,
  quote_ts timestamptz not null,
  ingested_at timestamptz not null default now(),
  candidate_state text not null,
  primary key (app_user_id, market_id),
  check (char_length(trim(question)) > 0),
  check (liquidity is null or liquidity >= 0),
  check (spread is null or (spread >= 0 and spread <= 1)),
  check (delta_abs >= 0),
  check (threshold_value >= 0 and threshold_value <= 1),
  check (char_length(trim(candidate_state)) > 0)
);

comment on table public.hot_alert_candidates_latest is
'Hot Data Contract V1: latest pre-delivery alert candidates. Worker is expected to upsert/prune per-user latest candidate rows; thresholding/delivery runtime is unchanged until a later cutover.';

comment on column public.hot_alert_candidates_latest.candidate_state is
'Worker-owned candidate classification for the latest hot alert pass, intended to distinguish publishable rows from filtered rows before downstream delivery cutover.';

create index if not exists idx_hot_alert_candidates_latest_user_delta
  on public.hot_alert_candidates_latest (app_user_id, delta_abs desc, quote_ts desc);

create index if not exists idx_hot_alert_candidates_latest_state
  on public.hot_alert_candidates_latest (candidate_state, ingested_at desc);

create index if not exists idx_hot_alert_candidates_latest_user_state
  on public.hot_alert_candidates_latest (app_user_id, candidate_state, delta_abs desc, quote_ts desc);

create or replace view public.hot_ingest_health_latest as
with registry as (
  select
    count(*) filter (where coalesce(status, 'active') = 'active')::bigint as active_market_count,
    max(source_ts) as latest_source_ts,
    max(updated_at) as latest_registry_updated_at
  from public.hot_market_registry_latest
),
quotes as (
  select
    count(*) filter (where has_two_sided_quote)::bigint as two_sided_quote_count,
    max(quote_ts) as latest_quote_ts,
    max(ingested_at) as latest_quotes_ingested_at
  from public.hot_market_quotes_latest
),
movers_1m as (
  select
    count(*)::bigint as hot_movers_1m_count,
    max(ingested_at) as latest_1m_ingested_at
  from public.hot_top_movers_1m
),
movers_5m as (
  select
    count(*)::bigint as hot_movers_5m_count,
    max(ingested_at) as latest_5m_ingested_at
  from public.hot_top_movers_5m
)
select
  case
    when r.latest_source_ts is null then null
    else greatest(extract(epoch from (now() - r.latest_source_ts))::bigint, 0)
  end as registry_age_seconds,
  case
    when q.latest_quote_ts is null then null
    else greatest(extract(epoch from (now() - q.latest_quote_ts))::bigint, 0)
  end as quotes_age_seconds,
  coalesce(r.active_market_count, 0::bigint) as active_market_count,
  coalesce(q.two_sided_quote_count, 0::bigint) as two_sided_quote_count,
  coalesce(m1.hot_movers_1m_count, 0::bigint) as hot_movers_1m_count,
  coalesce(m5.hot_movers_5m_count, 0::bigint) as hot_movers_5m_count,
  nullif(
    greatest(
      coalesce(r.latest_registry_updated_at, r.latest_source_ts, 'epoch'::timestamptz),
      coalesce(q.latest_quotes_ingested_at, q.latest_quote_ts, 'epoch'::timestamptz),
      coalesce(m1.latest_1m_ingested_at, 'epoch'::timestamptz),
      coalesce(m5.latest_5m_ingested_at, 'epoch'::timestamptz)
    ),
    'epoch'::timestamptz
  ) as updated_at
from registry r
cross join quotes q
cross join movers_1m m1
cross join movers_5m m5;

comment on view public.hot_ingest_health_latest is
'Hot Data Contract V1: read-only operational freshness surface over the new hot tables. Safe to add before any runtime cutover.';

commit;
