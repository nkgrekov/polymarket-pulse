begin;

create or replace function trade.activate_signer_session(
  p_session_token text,
  p_signer_ref text default null,
  p_operator_note text default null
)
returns table (
  session_id bigint,
  wallet_link_id bigint,
  wallet_address text,
  session_status text,
  wallet_status text,
  verified_at timestamptz
)
language plpgsql
as $$
declare
  v_session record;
  v_note text;
begin
  select
    ss.id,
    ss.account_id,
    ss.wallet_link_id,
    ss.session_token,
    ss.status,
    ss.expires_at,
    wl.wallet_address,
    a.user_id
  into v_session
  from trade.signer_sessions ss
  join trade.wallet_links wl on wl.id = ss.wallet_link_id
  join trade.accounts a on a.id = ss.account_id
  where ss.session_token = p_session_token
  limit 1;

  if v_session.id is null then
    raise exception 'signer session not found';
  end if;

  if v_session.expires_at <= now() then
    update trade.signer_sessions
    set status = 'expired',
        updated_at = now()
    where id = v_session.id
      and status <> 'verified';
    raise exception 'signer session expired';
  end if;

  if v_session.status not in ('signed', 'verified') then
    raise exception 'signer session must be signed before activation';
  end if;

  update trade.signer_sessions ss
  set status = 'verified',
      verified_at = coalesce(ss.verified_at, now()),
      signed_payload = ss.signed_payload || jsonb_build_object(
        'operator_note', coalesce(p_operator_note, ''),
        'activated_at', now(),
        'activation_source', 'manual_operator'
      ),
      updated_at = now()
  where id = v_session.id;

  update trade.wallet_links
  set status = 'active',
      signer_kind = 'session',
      signer_ref = coalesce(p_signer_ref, p_session_token),
      updated_at = now()
  where id = v_session.wallet_link_id;

  v_note := coalesce(p_operator_note, '');

  insert into trade.activity_events (
    user_id,
    account_id,
    event_type,
    source,
    market_id,
    details
  ) values (
    v_session.user_id,
    v_session.account_id,
    'signer_activated',
    'manual',
    null,
    jsonb_build_object(
      'session_token', p_session_token,
      'wallet', v_session.wallet_address,
      'signer_ref', coalesce(p_signer_ref, p_session_token),
      'operator_note', v_note
    )
  );

  return query
  select
    ss.id,
    wl.id,
    wl.wallet_address,
    ss.status,
    wl.status,
    ss.verified_at
  from trade.signer_sessions ss
  join trade.wallet_links wl on wl.id = ss.wallet_link_id
  where ss.id = v_session.id;
end;
$$;

commit;
