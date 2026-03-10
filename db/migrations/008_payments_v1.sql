begin;

create table if not exists app.payment_events (
  id bigserial primary key,
  provider text not null,
  external_id text not null,
  event_type text not null,
  status text not null default 'succeeded',
  user_id uuid references app.users(id) on delete set null,
  email text,
  amount_cents bigint,
  currency text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (provider, external_id)
);

create index if not exists idx_payment_events_provider_created
  on app.payment_events (provider, created_at desc);

create index if not exists idx_payment_events_user_created
  on app.payment_events (user_id, created_at desc);

create index if not exists idx_payment_events_status_created
  on app.payment_events (status, created_at desc);

drop trigger if exists trg_payment_events_updated_at on app.payment_events;
create trigger trg_payment_events_updated_at
before update on app.payment_events
for each row execute function bot.touch_updated_at();

commit;
