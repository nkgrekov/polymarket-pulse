begin;

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

create table if not exists bot.app_users (
  app_user_id bigserial primary key,
  app_user_key text not null unique,
  source text not null default 'manual',
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (char_length(app_user_key) > 0)
);

comment on table bot.app_users is 'Stable bot-facing user identity. app_user_key matches existing public.watchlist.user_id and alert user_id values.';

create table if not exists bot.telegram_chats (
  telegram_chat_id bigint primary key,
  chat_type text not null,
  title text,
  username text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (chat_type in ('private', 'group', 'supergroup', 'channel'))
);

comment on table bot.telegram_chats is 'Telegram chat registry used as the delivery target for bot notifications.';

create table if not exists bot.telegram_users (
  telegram_user_id bigint primary key,
  username text,
  first_name text,
  last_name text,
  language_code text,
  is_bot boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table bot.telegram_users is 'Telegram user metadata captured from updates.';

create table if not exists bot.chat_links (
  chat_link_id bigserial primary key,
  app_user_id bigint not null references bot.app_users(app_user_id) on delete cascade,
  telegram_chat_id bigint not null references bot.telegram_chats(telegram_chat_id) on delete cascade,
  telegram_user_id bigint references bot.telegram_users(telegram_user_id) on delete set null,
  link_status text not null default 'active',
  is_default boolean not null default true,
  linked_at timestamptz not null default now(),
  unlinked_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (app_user_id, telegram_chat_id),
  check (link_status in ('pending', 'active', 'revoked')),
  check ((link_status = 'revoked' and unlinked_at is not null) or (link_status <> 'revoked'))
);

comment on table bot.chat_links is 'Maps one app user to one or more Telegram delivery chats.';

create table if not exists bot.chat_settings (
  telegram_chat_id bigint primary key references bot.telegram_chats(telegram_chat_id) on delete cascade,
  inbox_limit integer not null default 10,
  locale text not null default 'ru',
  timezone text not null default 'UTC',
  notifications_enabled boolean not null default true,
  command_scope text not null default 'owner',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (inbox_limit between 1 and 50),
  check (command_scope in ('owner', 'shared'))
);

comment on table bot.chat_settings is 'Per-chat delivery and UX defaults for Telegram commands and alerts.';

create table if not exists bot.market_subscriptions (
  subscription_id bigserial primary key,
  app_user_id bigint not null references bot.app_users(app_user_id) on delete cascade,
  market_id text not null references public.markets(market_id) on delete cascade,
  subscription_source text not null default 'manual',
  notify_inbox boolean not null default true,
  notify_realtime boolean not null default true,
  min_abs_delta numeric,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (app_user_id, market_id),
  check (subscription_source in ('manual', 'watchlist', 'auto')),
  check (min_abs_delta is null or min_abs_delta >= 0)
);

comment on table bot.market_subscriptions is 'Bot-specific market subscriptions. Can later replace or mirror public.watchlist.';

create table if not exists bot.alert_rules (
  alert_rule_id bigserial primary key,
  app_user_id bigint not null references bot.app_users(app_user_id) on delete cascade,
  rule_name text not null,
  rule_kind text not null,
  side text,
  min_abs_delta numeric,
  min_pnl numeric,
  cooldown_minutes integer not null default 15,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (rule_kind in ('price_delta', 'pnl', 'inbox_digest')),
  check (side is null or side in ('yes', 'no')),
  check (min_abs_delta is null or min_abs_delta >= 0),
  check (cooldown_minutes >= 0)
);

comment on table bot.alert_rules is 'Per-user alert thresholds and digests for Telegram delivery.';

create table if not exists bot.outbound_messages (
  outbound_message_id bigserial primary key,
  telegram_chat_id bigint not null references bot.telegram_chats(telegram_chat_id) on delete cascade,
  app_user_id bigint references bot.app_users(app_user_id) on delete set null,
  message_kind text not null,
  dedupe_key text,
  payload jsonb not null default '{}'::jsonb,
  status text not null default 'pending',
  telegram_message_id bigint,
  sent_at timestamptz,
  failed_at timestamptz,
  error_text text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (telegram_chat_id, dedupe_key),
  check (message_kind in ('alert', 'inbox', 'system', 'command_reply')),
  check (status in ('pending', 'sent', 'failed', 'cancelled'))
);

comment on table bot.outbound_messages is 'Outbound delivery log and idempotency layer for Telegram sends.';

create table if not exists bot.command_audit (
  command_audit_id bigserial primary key,
  telegram_chat_id bigint references bot.telegram_chats(telegram_chat_id) on delete set null,
  telegram_user_id bigint references bot.telegram_users(telegram_user_id) on delete set null,
  app_user_id bigint references bot.app_users(app_user_id) on delete set null,
  command_name text not null,
  command_text text,
  status text not null default 'received',
  error_text text,
  created_at timestamptz not null default now(),
  check (status in ('received', 'handled', 'failed', 'ignored'))
);

comment on table bot.command_audit is 'Audit trail of incoming Telegram commands.';

create index if not exists idx_chat_links_app_user_active
  on bot.chat_links (app_user_id, link_status, is_default);

create index if not exists idx_market_subscriptions_user_active
  on bot.market_subscriptions (app_user_id, is_active);

create index if not exists idx_market_subscriptions_market_active
  on bot.market_subscriptions (market_id, is_active);

create index if not exists idx_alert_rules_user_active
  on bot.alert_rules (app_user_id, is_active);

create index if not exists idx_outbound_messages_status_created
  on bot.outbound_messages (status, created_at);

create index if not exists idx_outbound_messages_chat_created
  on bot.outbound_messages (telegram_chat_id, created_at desc);

create index if not exists idx_command_audit_chat_created
  on bot.command_audit (telegram_chat_id, created_at desc);

drop trigger if exists trg_app_users_updated_at on bot.app_users;
create trigger trg_app_users_updated_at
before update on bot.app_users
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_telegram_chats_updated_at on bot.telegram_chats;
create trigger trg_telegram_chats_updated_at
before update on bot.telegram_chats
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_telegram_users_updated_at on bot.telegram_users;
create trigger trg_telegram_users_updated_at
before update on bot.telegram_users
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_chat_links_updated_at on bot.chat_links;
create trigger trg_chat_links_updated_at
before update on bot.chat_links
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_chat_settings_updated_at on bot.chat_settings;
create trigger trg_chat_settings_updated_at
before update on bot.chat_settings
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_market_subscriptions_updated_at on bot.market_subscriptions;
create trigger trg_market_subscriptions_updated_at
before update on bot.market_subscriptions
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_alert_rules_updated_at on bot.alert_rules;
create trigger trg_alert_rules_updated_at
before update on bot.alert_rules
for each row execute function bot.touch_updated_at();

drop trigger if exists trg_outbound_messages_updated_at on bot.outbound_messages;
create trigger trg_outbound_messages_updated_at
before update on bot.outbound_messages
for each row execute function bot.touch_updated_at();

create or replace view bot.v_chat_targets as
select
  au.app_user_id,
  au.app_user_key,
  cl.telegram_chat_id,
  cl.telegram_user_id,
  cl.is_default,
  cs.inbox_limit,
  cs.locale,
  cs.timezone,
  cs.notifications_enabled
from bot.app_users au
join bot.chat_links cl
  on cl.app_user_id = au.app_user_id
 and cl.link_status = 'active'
join bot.telegram_chats tc
  on tc.telegram_chat_id = cl.telegram_chat_id
 and tc.is_active = true
left join bot.chat_settings cs
  on cs.telegram_chat_id = cl.telegram_chat_id
where au.is_active = true;

comment on view bot.v_chat_targets is 'Resolved active Telegram delivery targets per app user.';

create or replace view bot.v_watchlist_market_subscriptions as
select
  ms.subscription_id,
  au.app_user_key as user_id,
  ms.market_id,
  ms.subscription_source,
  ms.notify_inbox,
  ms.notify_realtime,
  ms.min_abs_delta,
  ms.is_active,
  ms.created_at,
  ms.updated_at
from bot.market_subscriptions ms
join bot.app_users au on au.app_user_id = ms.app_user_id;

comment on view bot.v_watchlist_market_subscriptions is 'Bot subscriptions projected into the legacy user_id shape used by current ingest/bot code.';

commit;
