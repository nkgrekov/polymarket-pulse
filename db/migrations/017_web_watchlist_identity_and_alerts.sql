begin;

create table if not exists app.web_auth_requests (
  id bigserial primary key,
  request_token text not null unique,
  user_id uuid references app.users(id) on delete set null,
  telegram_id bigint,
  chat_id bigint,
  market_id text references public.markets(market_id) on delete set null,
  intent text not null default 'login',
  return_path text not null default '/watchlist',
  locale text not null default 'en',
  status text not null default 'pending',
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  claimed_at timestamptz,
  expires_at timestamptz not null default (now() + interval '30 minutes'),
  check (intent in ('login', 'watchlist_add', 'alert', 'return_watchlist')),
  check (status in ('pending', 'completed', 'claimed', 'expired')),
  check (char_length(trim(request_token)) >= 16),
  check (char_length(trim(return_path)) > 0),
  check (locale in ('ru', 'en'))
);

create index if not exists idx_web_auth_requests_status_expires
  on app.web_auth_requests (status, expires_at desc);

create index if not exists idx_web_auth_requests_user_created
  on app.web_auth_requests (user_id, created_at desc);

create table if not exists app.web_sessions (
  id bigserial primary key,
  session_token text not null unique,
  user_id uuid not null references app.users(id) on delete cascade,
  source text not null default 'telegram',
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default (now() + interval '30 days'),
  last_seen_at timestamptz not null default now(),
  user_agent text,
  ip inet,
  payload jsonb not null default '{}'::jsonb,
  check (source in ('telegram', 'site')),
  check (char_length(trim(session_token)) >= 16)
);

create index if not exists idx_web_sessions_user_expires
  on app.web_sessions (user_id, expires_at desc);

create index if not exists idx_web_sessions_last_seen
  on app.web_sessions (last_seen_at desc);

create table if not exists bot.watchlist_alert_settings (
  user_id uuid not null references app.users(id) on delete cascade,
  market_id text not null references public.markets(market_id) on delete cascade,
  alert_enabled boolean not null default false,
  alert_paused boolean not null default false,
  threshold_value numeric,
  last_alert_at timestamptz,
  source text not null default 'web',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, market_id),
  check (threshold_value is null or (threshold_value >= 0 and threshold_value <= 1)),
  check (source in ('web', 'telegram', 'legacy_backfill', 'site_bridge'))
);

create index if not exists idx_watchlist_alert_settings_user_state
  on bot.watchlist_alert_settings (user_id, alert_enabled, alert_paused, updated_at desc);

create index if not exists idx_watchlist_alert_settings_market
  on bot.watchlist_alert_settings (market_id);

insert into bot.watchlist_alert_settings (
  user_id,
  market_id,
  alert_enabled,
  alert_paused,
  threshold_value,
  source
)
select
  w.user_id,
  w.market_id,
  true,
  false,
  null,
  'legacy_backfill'
from bot.watchlist w
on conflict (user_id, market_id) do nothing;

drop trigger if exists trg_bot_watchlist_alert_settings_updated_at on bot.watchlist_alert_settings;
create trigger trg_bot_watchlist_alert_settings_updated_at
before update on bot.watchlist_alert_settings
for each row execute function bot.touch_updated_at();

commit;
