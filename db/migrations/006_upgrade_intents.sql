create table if not exists app.upgrade_intents (
    id bigserial primary key,
    user_id uuid references app.users(id) on delete set null,
    telegram_id bigint,
    chat_id bigint,
    source text not null default 'telegram_bot',
    status text not null default 'new',
    details jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    handled_at timestamptz,
    check (status in ('new', 'contacted', 'converted', 'rejected')),
    check (source in ('telegram_bot', 'site', 'manual', 'import'))
);

create index if not exists idx_upgrade_intents_created
  on app.upgrade_intents (created_at desc);

create index if not exists idx_upgrade_intents_user_created
  on app.upgrade_intents (user_id, created_at desc);

create index if not exists idx_upgrade_intents_status_created
  on app.upgrade_intents (status, created_at desc);
