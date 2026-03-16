begin;

create table if not exists trade.signer_sessions (
  id bigserial primary key,
  account_id bigint not null references trade.accounts(id) on delete cascade,
  wallet_link_id bigint not null references trade.wallet_links(id) on delete cascade,
  session_token text not null unique,
  status text not null default 'new',
  challenge_text text not null,
  signed_payload jsonb not null default '{}'::jsonb,
  verified_at timestamptz,
  expires_at timestamptz not null default (now() + interval '30 minutes'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (status in ('new', 'opened', 'signed', 'verified', 'expired', 'revoked'))
);

create index if not exists idx_trade_signer_sessions_account_status
  on trade.signer_sessions (account_id, status, expires_at desc);

create index if not exists idx_trade_signer_sessions_wallet_status
  on trade.signer_sessions (wallet_link_id, status, expires_at desc);

drop trigger if exists trg_trade_signer_sessions_updated_at on trade.signer_sessions;
create trigger trg_trade_signer_sessions_updated_at before update on trade.signer_sessions
for each row execute function bot.touch_updated_at();

commit;
