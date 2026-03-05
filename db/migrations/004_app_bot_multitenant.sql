begin;

create extension if not exists pgcrypto;

create schema if not exists app;
create schema if not exists bot;

create or replace function bot.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists app.users (
  id uuid primary key default gen_random_uuid(),
  legacy_user_key text unique,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (status in ('active', 'blocked', 'deleted'))
);

create table if not exists app.identities (
  id bigserial primary key,
  user_id uuid not null references app.users(id) on delete cascade,
  provider text not null,
  provider_user_id text not null,
  created_at timestamptz not null default now(),
  unique (provider, provider_user_id),
  check (provider in ('telegram', 'email', 'ios'))
);

create table if not exists app.subscriptions (
  id bigserial primary key,
  user_id uuid not null references app.users(id) on delete cascade,
  plan text not null default 'pro',
  status text not null default 'active',
  source text not null default 'manual',
  started_at timestamptz not null default now(),
  renew_at timestamptz,
  created_at timestamptz not null default now(),
  check (plan in ('free', 'pro')),
  check (status in ('active', 'trialing', 'past_due', 'canceled', 'expired'))
);

create index if not exists idx_subscriptions_user_status
  on app.subscriptions (user_id, status, renew_at);

create table if not exists app.email_subscribers (
  id bigserial primary key,
  email text not null unique,
  user_id uuid references app.users(id) on delete set null,
  source text not null default 'site',
  confirm_token text unique,
  confirmed_at timestamptz,
  unsubscribed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (source in ('site', 'telegram', 'ios', 'import'))
);

create index if not exists idx_email_subscribers_confirmed
  on app.email_subscribers (confirmed_at, unsubscribed_at);

create table if not exists bot.profiles (
  user_id uuid primary key references app.users(id) on delete cascade,
  telegram_id bigint unique,
  chat_id bigint,
  username text,
  first_name text,
  last_name text,
  locale text default 'ru',
  timezone text not null default 'UTC',
  plan text not null default 'free',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (plan in ('free', 'pro'))
);

create table if not exists bot.user_settings (
  user_id uuid primary key references app.users(id) on delete cascade,
  threshold numeric not null default 0.03,
  quiet_hours text,
  digest_enabled boolean not null default true,
  digest_hour smallint not null default 10,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (threshold >= 0 and threshold <= 1),
  check (digest_hour between 0 and 23)
);

create table if not exists bot.watchlist (
  user_id uuid not null references app.users(id) on delete cascade,
  market_id text not null references public.markets(market_id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, market_id)
);

create index if not exists idx_bot_watchlist_market
  on bot.watchlist (market_id);

create table if not exists bot.alert_events (
  id bigserial primary key,
  user_id uuid not null references app.users(id) on delete cascade,
  market_id text not null,
  alert_type text not null,
  bucket timestamptz not null,
  abs_delta numeric not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (user_id, market_id, alert_type, bucket)
);

create index if not exists idx_bot_alert_events_user_day
  on bot.alert_events (user_id, created_at desc);

create table if not exists bot.sent_alerts_log (
  id bigserial primary key,
  channel text not null,
  user_id uuid references app.users(id) on delete cascade,
  recipient text not null,
  market_id text,
  alert_type text,
  bucket timestamptz,
  payload jsonb not null default '{}'::jsonb,
  sent_at timestamptz not null default now(),
  unique (channel, recipient, market_id, alert_type, bucket),
  check (channel in ('bot', 'email'))
);

create index if not exists idx_bot_sent_alerts_user_day
  on bot.sent_alerts_log (user_id, sent_at desc);

insert into app.users (legacy_user_key)
select distinct user_id
from (
  select user_id from public.user_watchlist
  union
  select user_id from public.user_positions
) src
where user_id is not null
on conflict (legacy_user_key) do nothing;

insert into bot.user_settings (user_id)
select id from app.users
on conflict (user_id) do nothing;

insert into bot.watchlist (user_id, market_id)
select u.id, w.market_id
from public.user_watchlist w
join app.users u on u.legacy_user_key = w.user_id
on conflict (user_id, market_id) do nothing;

create or replace function bot.resolve_or_create_user_from_telegram(
  p_telegram_id bigint,
  p_chat_id bigint,
  p_username text,
  p_first_name text,
  p_last_name text,
  p_locale text default 'ru'
)
returns uuid
language plpgsql
as $$
declare
  v_user_id uuid;
begin
  select i.user_id
    into v_user_id
  from app.identities i
  where i.provider = 'telegram'
    and i.provider_user_id = p_telegram_id::text
  limit 1;

  if v_user_id is null then
    insert into app.users (legacy_user_key)
    values ('tg:' || p_telegram_id::text)
    returning id into v_user_id;

    insert into app.identities (user_id, provider, provider_user_id)
    values (v_user_id, 'telegram', p_telegram_id::text)
    on conflict (provider, provider_user_id) do nothing;
  end if;

  insert into bot.profiles (
    user_id, telegram_id, chat_id, username, first_name, last_name, locale
  ) values (
    v_user_id, p_telegram_id, p_chat_id, p_username, p_first_name, p_last_name, coalesce(p_locale, 'ru')
  )
  on conflict (user_id) do update
    set telegram_id = excluded.telegram_id,
        chat_id = excluded.chat_id,
        username = excluded.username,
        first_name = excluded.first_name,
        last_name = excluded.last_name,
        locale = excluded.locale,
        updated_at = now();

  insert into bot.user_settings (user_id)
  values (v_user_id)
  on conflict (user_id) do nothing;

  return v_user_id;
end;
$$;

create or replace function bot.current_plan(p_user_id uuid)
returns text
language sql
stable
as $$
  select coalesce(
    (
      select s.plan
      from app.subscriptions s
      where s.user_id = p_user_id
        and s.status in ('active', 'trialing')
        and (s.renew_at is null or s.renew_at > now())
      order by s.started_at desc
      limit 1
    ),
    (
      select p.plan
      from bot.profiles p
      where p.user_id = p_user_id
      limit 1
    ),
    'free'
  );
$$;

drop view if exists bot.portfolio_snapshot_latest cascade;
drop view if exists bot.watchlist_snapshot_latest cascade;
drop view if exists bot.portfolio_alerts_latest cascade;
drop view if exists bot.watchlist_alerts_latest cascade;
drop view if exists bot.alerts_inbox_latest cascade;

create view bot.portfolio_snapshot_latest as
select
  u.id as user_id,
  p.market_id,
  p.question,
  p.side,
  p.mid_now,
  p.mid_prev,
  p.delta_mid,
  p.pnl,
  p.last_bucket,
  p.prev_bucket
from public.portfolio_snapshot_latest p
join app.users u on u.legacy_user_key = p.user_id;

create view bot.watchlist_snapshot_latest as
with lb as (
  select last_bucket
  from public.global_bucket_latest
),
prev as (
  select max(ms.ts_bucket) as prev_bucket
  from public.market_snapshots ms
  join lb on true
  where ms.ts_bucket < lb.last_bucket
),
universe as (
  select distinct market_id
  from public.market_universe
),
last_mid as (
  select
    ms.market_id,
    max(((ms.yes_bid + ms.yes_ask) / 2::numeric)) as yes_mid_now
  from public.market_snapshots ms
  join lb on ms.ts_bucket = lb.last_bucket
  join universe u on u.market_id = ms.market_id
  group by ms.market_id
),
prev_mid as (
  select
    ms.market_id,
    max(((ms.yes_bid + ms.yes_ask) / 2::numeric)) as yes_mid_prev
  from public.market_snapshots ms
  join prev on ms.ts_bucket = prev.prev_bucket
  join universe u on u.market_id = ms.market_id
  group by ms.market_id
)
select
  w.user_id,
  w.market_id,
  m.question,
  (select last_bucket from lb) as last_bucket,
  (select prev_bucket from prev) as prev_bucket,
  lm.yes_mid_now as mid_now,
  pm.yes_mid_prev as mid_prev,
  (lm.yes_mid_now - pm.yes_mid_prev) as delta_mid
from bot.watchlist w
join public.markets m on m.market_id = w.market_id
join last_mid lm on lm.market_id = w.market_id
join prev_mid pm on pm.market_id = w.market_id
where lm.yes_mid_now is not null
  and pm.yes_mid_prev is not null;

create view bot.portfolio_alerts_latest as
select
  p.user_id,
  p.market_id,
  p.question,
  p.side,
  p.mid_now,
  p.mid_prev,
  p.delta_mid,
  p.pnl,
  p.last_bucket,
  p.prev_bucket,
  abs(p.delta_mid) as abs_delta
from bot.portfolio_snapshot_latest p
left join bot.user_settings s on s.user_id = p.user_id
where abs(p.delta_mid) >= coalesce(s.threshold, 0.03);

create view bot.watchlist_alerts_latest as
select
  w.user_id,
  w.market_id,
  w.question,
  null::text as side,
  w.mid_now,
  w.mid_prev,
  w.delta_mid,
  null::numeric as pnl,
  w.last_bucket,
  w.prev_bucket,
  abs(w.delta_mid) as abs_delta
from bot.watchlist_snapshot_latest w
left join bot.user_settings s on s.user_id = w.user_id
where abs(w.delta_mid) >= coalesce(s.threshold, 0.03);

create view bot.alerts_inbox_latest as
select
  alert_type,
  user_id,
  market_id,
  question,
  side,
  mid_now,
  mid_prev,
  delta_mid,
  pnl,
  last_bucket,
  prev_bucket,
  abs_delta
from (
  select
    'portfolio'::text as alert_type,
    p.user_id,
    p.market_id,
    p.question,
    p.side,
    p.mid_now,
    p.mid_prev,
    p.delta_mid,
    p.pnl,
    p.last_bucket,
    p.prev_bucket,
    p.abs_delta
  from bot.portfolio_alerts_latest p
  union all
  select
    'watchlist'::text as alert_type,
    w.user_id,
    w.market_id,
    w.question,
    w.side,
    w.mid_now,
    w.mid_prev,
    w.delta_mid,
    w.pnl,
    w.last_bucket,
    w.prev_bucket,
    w.abs_delta
  from bot.watchlist_alerts_latest w
) t
order by abs_delta desc nulls last;

alter table app.users enable row level security;
alter table app.identities enable row level security;
alter table app.subscriptions enable row level security;
alter table app.email_subscribers enable row level security;
alter table bot.profiles enable row level security;
alter table bot.user_settings enable row level security;
alter table bot.watchlist enable row level security;
alter table bot.alert_events enable row level security;
alter table bot.sent_alerts_log enable row level security;

drop policy if exists app_users_select_own on app.users;
create policy app_users_select_own on app.users
for select using (id = auth.uid());

drop policy if exists app_users_update_own on app.users;
create policy app_users_update_own on app.users
for update using (id = auth.uid()) with check (id = auth.uid());

drop policy if exists bot_profiles_select_own on bot.profiles;
create policy bot_profiles_select_own on bot.profiles
for select using (user_id = auth.uid());

drop policy if exists bot_profiles_update_own on bot.profiles;
create policy bot_profiles_update_own on bot.profiles
for update using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists bot_user_settings_select_own on bot.user_settings;
create policy bot_user_settings_select_own on bot.user_settings
for select using (user_id = auth.uid());

drop policy if exists bot_user_settings_update_own on bot.user_settings;
create policy bot_user_settings_update_own on bot.user_settings
for update using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists bot_watchlist_select_own on bot.watchlist;
create policy bot_watchlist_select_own on bot.watchlist
for select using (user_id = auth.uid());

drop policy if exists bot_watchlist_modify_own on bot.watchlist;
create policy bot_watchlist_modify_own on bot.watchlist
for all using (user_id = auth.uid()) with check (user_id = auth.uid());

drop trigger if exists trg_app_users_updated_at on app.users;
create trigger trg_app_users_updated_at
before update on app.users
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_email_subscribers_updated_at on app.email_subscribers;
create trigger trg_email_subscribers_updated_at
before update on app.email_subscribers
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_bot_profiles_updated_at on bot.profiles;
create trigger trg_bot_profiles_updated_at
before update on bot.profiles
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_bot_user_settings_updated_at on bot.user_settings;
create trigger trg_bot_user_settings_updated_at
before update on bot.user_settings
for each row execute function bot.touch_updated_at();

commit;
