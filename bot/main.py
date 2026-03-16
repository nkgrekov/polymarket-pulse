import asyncio
import hashlib
import logging
import os
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import quote

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    LabeledPrice,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
PG_CONN = os.environ["PG_CONN"]
PUSH_INTERVAL_SECONDS = int(os.environ.get("PUSH_INTERVAL_SECONDS", "300"))
PUSH_FETCH_LIMIT = int(os.environ.get("PUSH_FETCH_LIMIT", "50"))
DB_CONNECT_TIMEOUT_SECONDS = int(os.environ.get("DB_CONNECT_TIMEOUT_SECONDS", "10"))
DB_RETRY_ATTEMPTS = int(os.environ.get("DB_RETRY_ATTEMPTS", "3"))
DB_RETRY_SLEEP_SECONDS = float(os.environ.get("DB_RETRY_SLEEP_SECONDS", "1.5"))
PUSH_INITIAL_DELAY_SECONDS = int(os.environ.get("PUSH_INITIAL_DELAY_SECONDS", "20"))
FREE_WATCHLIST_LIMIT = int(os.environ.get("FREE_WATCHLIST_LIMIT", "3"))
FREE_DAILY_ALERT_LIMIT = int(os.environ.get("FREE_DAILY_ALERT_LIMIT", "20"))
PRO_WATCHLIST_LIMIT = int(os.environ.get("PRO_WATCHLIST_LIMIT", "20"))
PRO_MONTHLY_USD = os.environ.get("PRO_MONTHLY_USD", "10")
PRO_SUBSCRIPTION_DAYS = int(os.environ.get("PRO_SUBSCRIPTION_DAYS", "30"))
TELEGRAM_STARS_ENABLED = os.environ.get("TELEGRAM_STARS_ENABLED", "1").strip() not in {"0", "false", "False"}
TELEGRAM_STARS_PRICE_XTR = int(os.environ.get("TELEGRAM_STARS_PRICE_XTR", "454"))
PRO_STARS_PAYLOAD_PREFIX = "pro_monthly_stars"
WATCHLIST_PICKER_MIN_LIQUIDITY = Decimal(os.environ.get("WATCHLIST_PICKER_MIN_LIQUIDITY", "1000"))
TRADER_ALPHA_URL = os.environ.get("TRADER_ALPHA_URL", "https://polymarketpulse.app/trader-bot")
TRADER_BOT_USERNAME = os.environ.get("TRADER_BOT_USERNAME", "PolymarketPulse_trader_bot")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("polymarket_pulse_bot")

SQL_RESOLVE_USER = """
select bot.resolve_or_create_user_from_telegram(%s, %s, %s, %s, %s, %s) as user_id;
"""

SQL_USER_CONTEXT = """
with p as (
  select
    %s::uuid as user_id,
    bot.current_plan(%s::uuid) as plan
), s as (
  select coalesce(threshold, 0.03) as threshold
  from bot.user_settings
  where user_id = %s::uuid
)
select
  p.user_id,
  p.plan,
  coalesce((select threshold from s), 0.03) as threshold,
  (
    select count(*)
    from bot.watchlist w
    join public.markets m on m.market_id = w.market_id
    where w.user_id = p.user_id
      and coalesce(m.status, 'active') = 'active'
  ) as watchlist_count,
  (
    select count(*)
    from bot.watchlist w
    join public.markets m on m.market_id = w.market_id
    where w.user_id = p.user_id
      and coalesce(m.status, 'active') = 'closed'
  ) as watchlist_closed_count,
  (
    select count(*)
    from bot.sent_alerts_log l
    where l.user_id = p.user_id
      and l.channel = 'bot'
      and l.sent_at >= date_trunc('day', now())
  ) as alerts_sent_today
from p;
"""

SQL_SET_THRESHOLD = """
insert into bot.user_settings (user_id, threshold)
values (%s::uuid, %s)
on conflict (user_id) do update
set threshold = excluded.threshold,
    updated_at = now();
"""

SQL_INBOX = """
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
from bot.alerts_inbox_latest
where user_id = %s::uuid
order by abs_delta desc nulls last
limit %s;
"""

SQL_TOP_MOVERS = """
with base as (
  select
    market_id,
    question,
    last_bucket,
    prev_bucket,
    yes_mid_now,
    yes_mid_prev,
    delta_yes,
    coalesce(nullif(regexp_replace(question, ' - .*$', ''), ''), market_id) as root_key
  from public.top_movers_latest
  where abs(delta_yes) > 0
), ranked as (
  select distinct on (root_key)
    market_id,
    question,
    last_bucket,
    prev_bucket,
    yes_mid_now,
    yes_mid_prev,
    delta_yes
  from base
  order by root_key, abs(delta_yes) desc nulls last
)
select *
from ranked
order by abs(delta_yes) desc nulls last
limit %s;
"""

SQL_TOP_MOVERS_1H = """
with base as (
  select
    market_id,
    question,
    ts_now as last_bucket,
    ts_prev as prev_bucket,
    yes_mid_now,
    yes_mid_1h as yes_mid_prev,
    delta_yes_1h as delta_yes,
    coalesce(nullif(regexp_replace(question, ' - .*$', ''), ''), market_id) as root_key
  from public.top_movers_1h
  where abs(delta_yes_1h) > 0
), ranked as (
  select distinct on (root_key)
    market_id,
    question,
    last_bucket,
    prev_bucket,
    yes_mid_now,
    yes_mid_prev,
    delta_yes
  from base
  order by root_key, abs(delta_yes) desc nulls last
)
select *
from ranked
order by abs(delta_yes) desc nulls last
limit %s;
"""

SQL_TOP_MOVERS_WINDOW = """
with lb as (
  select last_bucket from public.global_bucket_latest
), prev as (
  select max(ms.ts_bucket) as prev_bucket
  from public.market_snapshots ms, lb
  where ms.ts_bucket < lb.last_bucket - make_interval(mins => %s)
), universe as (
  select distinct u.market_id
  from public.market_universe u
  join public.markets m on m.market_id = u.market_id
  where m.status = 'active'
), last_rows as (
  select
    ms.market_id,
    max((ms.yes_bid + ms.yes_ask) / 2.0) as yes_mid_now
  from public.market_snapshots ms
  join lb on ms.ts_bucket = lb.last_bucket
  join universe u on u.market_id = ms.market_id
  where ms.yes_bid is not null and ms.yes_ask is not null
  group by ms.market_id
), prev_rows as (
  select
    ms.market_id,
    max((ms.yes_bid + ms.yes_ask) / 2.0) as yes_mid_prev
  from public.market_snapshots ms
  join prev p on ms.ts_bucket = p.prev_bucket
  join universe u on u.market_id = ms.market_id
  where ms.yes_bid is not null and ms.yes_ask is not null
  group by ms.market_id
), base as (
  select
    l.market_id,
    m.question,
    (select last_bucket from lb) as last_bucket,
    (select prev_bucket from prev) as prev_bucket,
    l.yes_mid_now,
    p.yes_mid_prev,
    (l.yes_mid_now - p.yes_mid_prev) as delta_yes,
    coalesce(nullif(regexp_replace(m.question, ' - .*$', ''), ''), l.market_id) as root_key
  from last_rows l
  join prev_rows p on p.market_id = l.market_id
  join public.markets m on m.market_id = l.market_id
  where abs(l.yes_mid_now - p.yes_mid_prev) > 0
), ranked as (
  select distinct on (root_key)
    market_id,
    question,
    last_bucket,
    prev_bucket,
    yes_mid_now,
    yes_mid_prev,
    delta_yes
  from base
  order by root_key, abs(delta_yes) desc nulls last
)
select *
from ranked
order by abs(delta_yes) desc nulls last
limit %s;
"""

SQL_WATCHLIST_SNAPSHOT = """
select
  market_id,
  question,
  last_bucket,
  prev_bucket,
  mid_now as yes_mid_now,
  mid_prev as yes_mid_prev,
  delta_mid as delta_yes
from bot.watchlist_snapshot_latest
where user_id = %s::uuid
order by abs(delta_mid) desc nulls last
limit %s;
"""

SQL_WATCHLIST_SNAPSHOT_WINDOW = """
with lb as (
  select last_bucket from public.global_bucket_latest
), prev as (
  select max(ms.ts_bucket) as prev_bucket
  from public.market_snapshots ms, lb
  where ms.ts_bucket < lb.last_bucket - make_interval(mins => %s)
), universe as (
  select distinct u.market_id
  from public.market_universe u
  join public.markets m on m.market_id = u.market_id
  where m.status = 'active'
), wl as (
  select w.user_id, w.market_id
  from bot.watchlist w
  join universe u on u.market_id = w.market_id
  where w.user_id = %s::uuid
), last_mid as (
  select
    ms.market_id,
    max((ms.yes_bid + ms.yes_ask) / 2.0) as mid_now
  from public.market_snapshots ms
  join lb on ms.ts_bucket = lb.last_bucket
  join wl on wl.market_id = ms.market_id
  where ms.yes_bid is not null and ms.yes_ask is not null
  group by ms.market_id
), prev_mid as (
  select
    ms.market_id,
    max((ms.yes_bid + ms.yes_ask) / 2.0) as mid_prev
  from public.market_snapshots ms
  join prev p on ms.ts_bucket = p.prev_bucket
  join wl on wl.market_id = ms.market_id
  where ms.yes_bid is not null and ms.yes_ask is not null
  group by ms.market_id
)
select
  wl.market_id,
  m.question,
  (select last_bucket from lb) as last_bucket,
  (select prev_bucket from prev) as prev_bucket,
  lm.mid_now as yes_mid_now,
  pm.mid_prev as yes_mid_prev,
  (lm.mid_now - pm.mid_prev) as delta_yes
from wl
join last_mid lm on lm.market_id = wl.market_id
join prev_mid pm on pm.market_id = wl.market_id
join public.markets m on m.market_id = wl.market_id
where abs(lm.mid_now - pm.mid_prev) > 0
order by abs(lm.mid_now - pm.mid_prev) desc nulls last
limit %s;
"""

SQL_WATCHLIST_LIST = """
select w.market_id, m.question, w.created_at
from bot.watchlist w
join public.markets m on m.market_id = w.market_id
where w.user_id = %s::uuid
order by w.created_at desc
limit %s;
"""

SQL_WATCHLIST_PICKER_CANDIDATES = """
with params as (
  select
    %s::text as cat,
    %s::uuid as user_id,
    %s::numeric as min_liquidity
), wl as (
  select w.market_id
  from bot.watchlist w
  where w.user_id = (select user_id from params)
), quote_src as (
  select
    s.market_id,
    s.ts_bucket,
    coalesce(s.liquidity, 0)::numeric as liquidity
  from public.market_snapshots s
  where s.ts_bucket >= now() - interval '6 hours'
    and s.yes_bid is not null
    and s.yes_ask is not null
    and coalesce(s.liquidity, 0)::numeric >= (select min_liquidity from params)
), quotes as (
  select distinct on (qs.market_id)
    qs.market_id,
    qs.ts_bucket as quote_bucket,
    qs.liquidity
  from quote_src qs
  order by qs.market_id, qs.ts_bucket desc
), movers_now as (
  select
    t.market_id,
    t.question,
    t.delta_yes as delta_yes,
    q.liquidity,
    q.quote_bucket,
    1 as prio,
    (coalesce(abs(t.delta_yes), 0) * 100.0 + ln(1 + greatest(coalesce(q.liquidity, 0), 0)))::numeric as hybrid_score,
    coalesce(nullif(regexp_replace(t.question, ' - .*$', ''), ''), t.market_id) as root_key,
    lower(t.question) like '%%up or down - %%' as is_micro
  from public.top_movers_latest t
  join quotes q on q.market_id = t.market_id
  join public.markets m on m.market_id = t.market_id
  where coalesce(m.status, 'active') = 'active'
), movers_1h as (
  select
    t.market_id,
    t.question,
    t.delta_yes_1h as delta_yes,
    q.liquidity,
    q.quote_bucket,
    2 as prio,
    (coalesce(abs(t.delta_yes_1h), 0) * 100.0 + ln(1 + greatest(coalesce(q.liquidity, 0), 0)))::numeric as hybrid_score,
    coalesce(nullif(regexp_replace(t.question, ' - .*$', ''), ''), t.market_id) as root_key,
    lower(t.question) like '%%up or down - %%' as is_micro
  from public.top_movers_1h t
  join quotes q on q.market_id = t.market_id
  join public.markets m on m.market_id = t.market_id
  where coalesce(m.status, 'active') = 'active'
), liquid_live as (
  select
    m.market_id,
    m.question,
    null::numeric as delta_yes,
    q.liquidity,
    q.quote_bucket,
    3 as prio,
    ln(1 + greatest(coalesce(q.liquidity, 0), 0))::numeric as hybrid_score,
    coalesce(nullif(regexp_replace(m.question, ' - .*$', ''), ''), m.market_id) as root_key,
    lower(m.question) like '%%up or down - %%' as is_micro
  from public.market_universe u
  join public.markets m on m.market_id = u.market_id
  join quotes q on q.market_id = m.market_id
  where coalesce(m.status, 'active') = 'active'
  order by q.liquidity desc, m.market_id
  limit 120
), pool as (
  select * from movers_now
  union all
  select * from movers_1h
  union all
  select * from liquid_live
), ranked as (
  select distinct on (root_key)
    market_id,
    question,
    delta_yes,
    liquidity,
    quote_bucket,
    prio,
    hybrid_score,
    is_micro
  from pool
  order by root_key, is_micro, hybrid_score desc nulls last, prio, quote_bucket desc nulls last, abs(delta_yes) desc nulls last, liquidity desc nulls last
), tagged as (
  select
    r.*,
    case
      when lower(r.question) similar to '%%(trump|biden|election|senate|house|president|iran|putin|zelensky|congress|war|ceasefire|nato|israel|ukraine|rfk)%%'
        then 'politics'
      when lower(r.question) similar to '%%(fed|inflation|recession|gdp|cpi|interest rate|oil|yield|tariff|unemployment|jobs report|treasury)%%'
        then 'macro'
      when lower(r.question) similar to '%%(bitcoin|ethereum|solana|xrp|bnb|dogecoin|crypto|fdv|btc|eth|memecoin)%%'
        then 'crypto'
      else 'other'
    end as cat_tag
  from ranked r
), filtered as (
  select *
  from tagged
  where
    (
      (select cat from params) = 'all'
      or ((select cat from params) = cat_tag)
    )
    and not exists (
      select 1
      from wl
      where wl.market_id = tagged.market_id
    )
), balanced as (
  select
    f.*,
    row_number() over (
      partition by cat_tag
      order by is_micro, hybrid_score desc nulls last, prio, quote_bucket desc nulls last, coalesce(liquidity, 0) desc, abs(delta_yes) desc nulls last, market_id
    ) as cat_rank
  from filtered f
), final as (
  select *
  from balanced
  where
    (select cat from params) <> 'all'
    or (
      (cat_tag = 'politics' and cat_rank <= 4)
      or (cat_tag = 'macro' and cat_rank <= 4)
      or (cat_tag = 'crypto' and cat_rank <= 4)
      or (cat_tag = 'other' and cat_rank <= 10)
    )
)
select
  market_id,
  question,
  case when abs(delta_yes) < 0.001 then null else delta_yes end as delta_yes,
  liquidity,
  prio,
  cat_tag
from final
order by
  case
    when (select cat from params) = 'all' then
      case cat_tag when 'politics' then 1 when 'macro' then 2 when 'crypto' then 3 else 4 end
    else 1
  end,
  is_micro,
  hybrid_score desc nulls last,
  prio,
  quote_bucket desc nulls last,
  coalesce(liquidity, 0) desc,
  abs(delta_yes) desc nulls last,
  market_id
limit %s;
"""

SQL_WATCHLIST_DIAGNOSTICS = """
with lb as (
  select last_bucket from public.global_bucket_latest
), prev as (
  select max(ms.ts_bucket) as prev_bucket
  from public.market_snapshots ms, lb
  where ms.ts_bucket < lb.last_bucket
), wl as (
  select w.user_id, w.market_id
  from bot.watchlist w
  where w.user_id = %s::uuid
), wl_status as (
  select wl.market_id, coalesce(m.status, 'unknown') as status
  from wl
  left join public.markets m on m.market_id = wl.market_id
), live_last as (
  select distinct ms.market_id
  from public.market_snapshots ms, lb
  where ms.ts_bucket = lb.last_bucket
    and ms.yes_bid is not null
    and ms.yes_ask is not null
), live_prev as (
  select distinct ms.market_id
  from public.market_snapshots ms, prev
  where ms.ts_bucket = prev.prev_bucket
    and ms.yes_bid is not null
    and ms.yes_ask is not null
)
select
  (select count(*) from wl) as wl_total,
  (select count(*) from wl_status where status = 'active') as wl_active,
  (select count(*) from wl_status where status = 'closed') as wl_closed,
  (
    select count(*)
    from wl
    join live_last ll on ll.market_id = wl.market_id
    join live_prev lp on lp.market_id = wl.market_id
  ) as wl_with_quotes_both;
"""

SQL_INBOX_DIAGNOSTICS = """
with d as (
  select abs(delta_mid) as abs_delta
  from bot.watchlist_snapshot_latest
  where user_id = %s::uuid
  union all
  select abs(delta_mid) as abs_delta
  from bot.portfolio_snapshot_latest
  where user_id = %s::uuid
)
select
  count(*) as candidates_total,
  count(*) filter (where abs_delta >= %s) as over_threshold
from d;
"""

SQL_MARKET_BRIEF = """
select market_id, question
from public.markets
where market_id = %s
limit 1;
"""

SQL_MARKET_LIVE_STATUS = """
with lb as (
  select last_bucket from public.global_bucket_latest
), prev as (
  select max(ms.ts_bucket) as prev_bucket
  from public.market_snapshots ms, lb
  where ms.ts_bucket < lb.last_bucket
), market_base as (
  select
    m.market_id,
    m.question,
    coalesce(m.status, 'unknown') as market_status
  from public.markets m
  where m.market_id = %s
)
select
  mb.market_id,
  mb.question,
  mb.market_status,
  exists (
    select 1
    from public.market_snapshots ms, lb
    where ms.market_id = mb.market_id
      and ms.ts_bucket = lb.last_bucket
      and ms.yes_bid is not null
      and ms.yes_ask is not null
  ) as has_last_quotes,
  exists (
    select 1
    from public.market_snapshots ms, prev
    where ms.market_id = mb.market_id
      and ms.ts_bucket = prev.prev_bucket
      and ms.yes_bid is not null
      and ms.yes_ask is not null
  ) as has_prev_quotes,
  (select last_bucket from lb) as last_bucket,
  (select prev_bucket from prev) as prev_bucket
from market_base mb;
"""

SQL_FIND_MARKET = """
select market_id, question, slug
from public.markets
where market_id = %s
   or slug = %s
limit 1;
"""

SQL_WATCHLIST_EXISTS = """
select 1
from bot.watchlist
where user_id = %s::uuid
  and market_id = %s;
"""

SQL_WATCHLIST_ADD = """
insert into bot.watchlist (user_id, market_id)
values (%s::uuid, %s)
on conflict (user_id, market_id) do nothing;
"""

SQL_WATCHLIST_REMOVE = """
delete from bot.watchlist
where user_id = %s::uuid
  and market_id = %s;
"""

SQL_WATCHLIST_REMOVE_CLOSED = """
delete from bot.watchlist w
using public.markets m
where w.user_id = %s::uuid
  and m.market_id = w.market_id
  and m.status = 'closed';
"""

SQL_PUSH_CANDIDATES = """
select
  i.alert_type,
  i.user_id,
  i.market_id,
  i.question,
  i.side,
  i.mid_now,
  i.mid_prev,
  i.delta_mid,
  i.pnl,
  i.last_bucket,
  i.prev_bucket,
  i.abs_delta,
  p.chat_id,
  bot.current_plan(i.user_id) as plan
from bot.alerts_inbox_latest i
join bot.profiles p on p.user_id = i.user_id
where p.chat_id is not null
order by i.abs_delta desc nulls last
limit %s;
"""

SQL_SENT_ALERT_EXISTS = """
select 1
from bot.sent_alerts_log
where channel = %s
  and recipient = %s
  and market_id = %s
  and alert_type = %s
  and bucket = %s;
"""

SQL_SENT_ALERT_INSERT = """
insert into bot.sent_alerts_log (
  channel,
  user_id,
  recipient,
  market_id,
  alert_type,
  bucket,
  payload
)
values (%s, %s::uuid, %s, %s, %s, %s, %s)
on conflict (channel, recipient, market_id, alert_type, bucket) do nothing;
"""

SQL_ALERT_EVENT_UPSERT = """
insert into bot.alert_events (
  user_id,
  market_id,
  alert_type,
  bucket,
  abs_delta,
  payload
)
values (%s::uuid, %s, %s, %s, %s, %s)
on conflict (user_id, market_id, alert_type, bucket) do update
set abs_delta = excluded.abs_delta,
    payload = excluded.payload;
"""

SQL_ALERTS_SENT_TODAY = """
select count(*)
from bot.sent_alerts_log
where user_id = %s::uuid
  and channel = 'bot'
  and sent_at >= date_trunc('day', now());
"""

SQL_UPGRADE_INTENT_INSERT = """
insert into app.upgrade_intents (
  user_id,
  telegram_id,
  chat_id,
  source,
  details
)
values (%s::uuid, %s, %s, %s, %s);
"""

SQL_TRADE_ACTIVITY_INSERT = """
insert into trade.activity_events (
  user_id,
  event_type,
  source,
  market_id,
  details
)
values (%s::uuid, %s, %s, %s, %s);
"""

SQL_ENSURE_PAYMENT_EVENTS = """
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
"""

SQL_PAYMENT_EVENT_EXISTS = """
select 1
from app.payment_events
where provider = %s
  and external_id = %s
limit 1;
"""

SQL_PAYMENT_EVENT_INSERT = """
insert into app.payment_events (
  provider,
  external_id,
  event_type,
  status,
  user_id,
  email,
  amount_cents,
  currency,
  payload
)
values (%s, %s, %s, %s, %s::uuid, %s, %s, %s, %s);
"""

SQL_SUBSCRIPTION_INSERT_PRO = """
insert into app.subscriptions (
  user_id,
  plan,
  status,
  source,
  started_at,
  renew_at
)
values (
  %s::uuid,
  'pro',
  'active',
  %s,
  now(),
  now() + make_interval(days => %s)
)
returning renew_at;
"""

SQL_PROFILE_SET_PRO = """
update bot.profiles
set plan = 'pro',
    updated_at = now()
where user_id = %s::uuid;
"""


def run_db_query(query: str, params: tuple[Any, ...], *, row_factory=None):
    last_error = None
    for attempt in range(1, DB_RETRY_ATTEMPTS + 1):
        try:
            with psycopg.connect(PG_CONN, connect_timeout=DB_CONNECT_TIMEOUT_SECONDS) as conn:
                with conn.cursor(row_factory=row_factory) as cur:
                    cur.execute("set statement_timeout = '8000ms'")
                    cur.execute(query, params)
                    return cur.fetchall()
        except Exception as exc:
            last_error = exc
            if attempt == DB_RETRY_ATTEMPTS:
                raise
            log.warning("db query retry=%s/%s failed: %s", attempt, DB_RETRY_ATTEMPTS, exc)
            time.sleep(DB_RETRY_SLEEP_SECONDS)
    raise last_error


def execute_db_write(query: str, params: tuple[Any, ...]) -> None:
    last_error = None
    for attempt in range(1, DB_RETRY_ATTEMPTS + 1):
        try:
            with psycopg.connect(PG_CONN, connect_timeout=DB_CONNECT_TIMEOUT_SECONDS) as conn:
                with conn.cursor() as cur:
                    cur.execute("set statement_timeout = '8000ms'")
                    cur.execute(query, params)
                conn.commit()
                return
        except Exception as exc:
            last_error = exc
            if attempt == DB_RETRY_ATTEMPTS:
                raise
            log.warning("db write retry=%s/%s failed: %s", attempt, DB_RETRY_ATTEMPTS, exc)
            time.sleep(DB_RETRY_SLEEP_SECONDS)
    raise last_error


def ensure_payment_schema_sync() -> None:
    execute_db_write(SQL_ENSURE_PAYMENT_EVENTS, ())


def activate_pro_subscription_sync(
    *,
    user_id: str,
    provider: str,
    external_id: str,
    source: str,
    amount_cents: int | None,
    currency: str | None,
    payload: dict,
    email: str | None = None,
    event_type: str = "purchase",
) -> tuple[bool, datetime | None]:
    for attempt in range(1, DB_RETRY_ATTEMPTS + 1):
        try:
            with psycopg.connect(PG_CONN, connect_timeout=DB_CONNECT_TIMEOUT_SECONDS) as conn:
                with conn.cursor() as cur:
                    cur.execute("set statement_timeout = '8000ms'")
                    cur.execute(SQL_ENSURE_PAYMENT_EVENTS)
                    cur.execute(SQL_PAYMENT_EVENT_EXISTS, (provider, external_id))
                    if cur.fetchone():
                        conn.commit()
                        return False, None

                    cur.execute(
                        SQL_PAYMENT_EVENT_INSERT,
                        (
                            provider,
                            external_id,
                            event_type,
                            "succeeded",
                            user_id,
                            (email or "").strip().lower() or None,
                            amount_cents,
                            currency,
                            Jsonb(payload),
                        ),
                    )
                    cur.execute(SQL_SUBSCRIPTION_INSERT_PRO, (user_id, source, PRO_SUBSCRIPTION_DAYS))
                    renew_at = cur.fetchone()[0]
                    cur.execute(SQL_PROFILE_SET_PRO, (user_id,))
                conn.commit()
                return True, renew_at
        except Exception as exc:
            if attempt == DB_RETRY_ATTEMPTS:
                raise
            log.warning("activate pro retry=%s/%s failed: %s", attempt, DB_RETRY_ATTEMPTS, exc)
            time.sleep(DB_RETRY_SLEEP_SECONDS)
    return False, None


def _fmt_num(value: object, digits: int, signed: bool = False) -> str:
    if value is None:
        return "n/a"
    try:
        num = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return "n/a"
    pattern = f"{{:{'+' if signed else ''}.{digits}f}}"
    return pattern.format(num)


def fmt_alert_row(row: dict) -> str:
    window = fmt_window(row.get("last_bucket"), row.get("prev_bucket"))
    return (
        f"[{row.get('alert_type')}] {row.get('question') or 'n/a'}\n"
        f"market: {row.get('market_id')}\n"
        f"mid: {_fmt_num(row.get('mid_now'), 3)} -> {_fmt_num(row.get('mid_prev'), 3)} | "
        f"Δ {_fmt_num(row.get('delta_mid'), 3, signed=True)}\n"
        f"window: {window}"
    )


def fmt_mover_row(row: dict) -> str:
    window = fmt_window(row.get("last_bucket"), row.get("prev_bucket"))
    return (
        f"{row.get('question') or 'n/a'}\n"
        f"market: {row.get('market_id')}\n"
        f"mid: {_fmt_num(row.get('yes_mid_now'), 3)} -> {_fmt_num(row.get('yes_mid_prev'), 3)} | "
        f"Δ {_fmt_num(row.get('delta_yes'), 3, signed=True)}\n"
        f"window: {window}"
    )


def fmt_window(last_bucket: Any, prev_bucket: Any) -> str:
    if last_bucket is None or prev_bucket is None:
        return "n/a"
    try:
        delta = last_bucket - prev_bucket
        mins = int(delta.total_seconds() // 60)
        return f"{prev_bucket} -> {last_bucket} ({mins}m)"
    except Exception:
        return f"{prev_bucket} -> {last_bucket}"


def user_limits_block(user_ctx: dict, *, locale: str = "ru") -> str:
    plan = str(user_ctx.get("plan") or "free")
    watchlist_count = int(user_ctx.get("watchlist_count") or 0)
    closed_count = int(user_ctx.get("watchlist_closed_count") or 0)
    alerts_today = int(user_ctx.get("alerts_sent_today") or 0)
    threshold = _fmt_num(user_ctx.get("threshold"), 3)
    closed_line = ""
    if closed_count > 0:
        closed_line = (
            f"\nArchived closed markets: {closed_count}"
            if locale == "en"
            else f"\nЗакрытых в архиве: {closed_count}"
        )
    if plan == "pro":
        if locale == "en":
            return (
                "Plan: PRO\n"
                f"Threshold: {threshold}\n"
                f"Watchlist: {watchlist_count}/{PRO_WATCHLIST_LIMIT}\n"
                f"Alerts today: {alerts_today} (unlimited)"
                f"{closed_line}"
            )
        return (
            "План: PRO\n"
            f"Threshold: {threshold}\n"
            f"Watchlist: {watchlist_count}/{PRO_WATCHLIST_LIMIT}\n"
            f"Alerts today: {alerts_today} (без лимита)"
            f"{closed_line}"
        )
    if locale == "en":
        return (
            "Plan: FREE\n"
            f"Threshold: {threshold}\n"
            f"Watchlist: {watchlist_count}/{FREE_WATCHLIST_LIMIT}\n"
            f"Alerts today: {alerts_today}/{FREE_DAILY_ALERT_LIMIT}"
            f"{closed_line}"
        )
    return (
        "План: FREE\n"
        f"Threshold: {threshold}\n"
        f"Watchlist: {watchlist_count}/{FREE_WATCHLIST_LIMIT}\n"
        f"Alerts today: {alerts_today}/{FREE_DAILY_ALERT_LIMIT}"
        f"{closed_line}"
    )


def watchlist_limit_for_plan(plan: str) -> int:
    if plan == "pro":
        return PRO_WATCHLIST_LIMIT
    return FREE_WATCHLIST_LIMIT


def is_english_locale(update: Update) -> bool:
    tg_user = update.effective_user
    code = (tg_user.language_code or "").lower() if tg_user else ""
    return code.startswith("en")


def locale_from_update(update: Update) -> str:
    return "en" if is_english_locale(update) else "ru"


def upgrade_pitch_text(update: Update) -> str:
    if is_english_locale(update):
        return (
            f"⭐ <b>PRO — {TELEGRAM_STARS_PRICE_XTR} Stars / month</b>\n\n"
            f"<code>FREE</code> → {FREE_WATCHLIST_LIMIT} watchlist markets · {FREE_DAILY_ALERT_LIMIT} alerts/day\n"
            f"<code>PRO</code>  → {PRO_WATCHLIST_LIMIT} markets · unlimited · email digest\n\n"
            "Upgrade instantly via Stars below.\n"
            'Prefer card? → <a href="https://polymarketpulse.app/?lang=en#pro">Pay with Stripe</a>'
        )
    return (
        f"⭐ <b>PRO — {TELEGRAM_STARS_PRICE_XTR} Stars / month</b>\n\n"
        f"<code>FREE</code> → {FREE_WATCHLIST_LIMIT} watchlist markets · {FREE_DAILY_ALERT_LIMIT} alerts/day\n"
        f"<code>PRO</code>  → {PRO_WATCHLIST_LIMIT} markets · unlimited · email digest\n\n"
        "Upgrade instantly via Stars below.\n"
        'Prefer card? → <a href="https://polymarketpulse.app/?lang=en#pro">Pay with Stripe</a>'
    )


def build_trader_alpha_url(
    *,
    locale: str = "ru",
    placement: str,
    market_id: str | None = None,
) -> str:
    lang = "en" if locale == "en" else "ru"
    placement_safe = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "-" for ch in placement)[:24]
    parts = [f"lang-{lang}", f"src-{placement_safe}"]
    if market_id:
        market_safe = "".join(ch for ch in str(market_id) if ch.isalnum() or ch in {"_", "-"})[:24]
        if market_safe:
            parts.append(f"m-{market_safe}")
    payload = "_".join(parts)[:64]
    return f"tg://resolve?domain={TRADER_BOT_USERNAME}&start={quote(payload)}"


def trade_pitch_text(update: Update, *, market_id: str | None = None) -> str:
    locale = locale_from_update(update)
    market_hint = (
        f"\n\nMarket handoff: <code>{market_id}</code>"
        if market_id
        else ""
    )
    if locale == "en":
        return (
            "<b>Trader Alpha</b>\n"
            "Pulse stays the signal layer.\n"
            "Trader becomes the execution layer for Polymarket only.\n\n"
            "What is in alpha:\n"
            "• non-custodial first\n"
            "• buy / sell / limit order in Telegram\n"
            "• follow flow + AI trader agent\n"
            "• auto only inside your own rules"
            f"{market_hint}"
        )
    return (
        "<b>Trader Alpha</b>\n"
        "Pulse остаётся signal-слоем.\n"
        "Trader становится execution-слоем только для Polymarket.\n\n"
        "Что входит в alpha:\n"
        "• non-custodial first\n"
        "• buy / sell / limit order в Telegram\n"
        "• follow-flow + AI trader agent\n"
        "• auto только внутри ваших правил"
        f"{market_hint}"
    )


def trader_alpha_keyboard(*, locale: str = "ru", placement: str, market_id: str | None = None) -> InlineKeyboardMarkup:
    launch_url = build_trader_alpha_url(locale=locale, placement=placement, market_id=market_id)
    if locale == "en":
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("Join Trader Alpha", url=launch_url)]]
        )
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Вступить в Trader Alpha", url=launch_url)]]
    )


def trader_surface_keyboard(
    *,
    locale: str = "ru",
    placement: str,
    market_id: str | None = None,
    extra_buttons: list[InlineKeyboardButton] | None = None,
) -> InlineKeyboardMarkup:
    launch_url = build_trader_alpha_url(locale=locale, placement=placement, market_id=market_id)
    primary = (
        InlineKeyboardButton("Trade this market", url=launch_url)
        if locale == "en"
        else InlineKeyboardButton("Торговать этот рынок", url=launch_url)
    )
    rows = [[primary]]
    if extra_buttons:
        rows.append(extra_buttons)
    return InlineKeyboardMarkup(rows)


def plan_upgrade_hint(update: Update) -> str:
    if is_english_locale(update):
        return "→ /upgrade — move to PRO"
    return "→ /upgrade — перейти на PRO"


def main_menu_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Top movers", callback_data="menu:movers"), InlineKeyboardButton("Watchlist", callback_data="menu:watchlist")],
            [InlineKeyboardButton("Inbox", callback_data="menu:inbox"), InlineKeyboardButton("Plan", callback_data="menu:plan")],
            [InlineKeyboardButton("Add market", callback_data="menu:pick"), InlineKeyboardButton("Threshold", callback_data="menu:threshold")],
            [InlineKeyboardButton("Upgrade", callback_data="menu:upgrade"), InlineKeyboardButton("Help", callback_data="menu:help")],
        ]
    )


def onboarding_start_inline(locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Add first market" if locale == "en" else "Добавить первый рынок",
                    callback_data="menu:pick",
                ),
                InlineKeyboardButton(
                    "Top movers" if locale == "en" else "Топ муверы",
                    callback_data="menu:movers",
                ),
            ],
            [
                InlineKeyboardButton(
                    "Plan" if locale == "en" else "План",
                    callback_data="menu:plan",
                ),
                InlineKeyboardButton(
                    "Help" if locale == "en" else "Помощь",
                    callback_data="menu:help",
                ),
            ],
        ]
    )


def onboarding_picker_inline(chat_id: int, rows: list[dict], bot_data: dict, *, locale: str = "ru") -> InlineKeyboardMarkup:
    picker_map = bot_data.setdefault("picker_map", {})
    buttons: list[list[InlineKeyboardButton]] = []
    for row in rows[:3]:
        market_id = str(row["market_id"])
        token = _picker_token(chat_id, market_id)
        picker_map[f"{chat_id}:{token}"] = market_id
        delta = row.get("delta_yes")
        cat = (row.get("cat_tag") or "other").upper()[:3]
        prefix = _fmt_num(delta, 3, signed=True) if delta is not None else "LIVE"
        label = f"{cat} {prefix} | {(row.get('question') or 'n/a')[:32]}".strip()
        buttons.append([InlineKeyboardButton(label, callback_data=f"wlpick:{token}")])
    buttons.append(
        [
            InlineKeyboardButton(
                "Open full picker" if locale == "en" else "Открыть полный picker",
                callback_data="menu:pick",
            )
        ]
    )
    return InlineKeyboardMarkup(buttons)


def watchlist_added_inline(locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Watchlist", callback_data="menu:watchlist"),
                InlineKeyboardButton("Inbox", callback_data="menu:inbox"),
            ],
            [
                InlineKeyboardButton("Threshold", callback_data="menu:threshold"),
                InlineKeyboardButton(
                    "Add one more" if locale == "en" else "Добавить ещё",
                    callback_data="menu:pick",
                ),
            ],
        ]
    )


async def build_recovery_inline(
    message,
    context: ContextTypes.DEFAULT_TYPE,
    user_ctx: dict,
    *,
    locale: str = "ru",
) -> InlineKeyboardMarkup:
    try:
        rows = await fetch_watchlist_picker_candidates_async(
            user_id=user_ctx["user_id"], category="all", limit=2, timeout_sec=10.0
        )
    except Exception:
        log.exception("recovery picker failed")
        rows = []

    if not rows:
        return InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("Add market" if locale == "en" else "Добавить рынок", callback_data="menu:pick"),
                InlineKeyboardButton("Top movers", callback_data="menu:movers"),
            ]]
        )

    chat_id = message.chat_id
    picker_map = context.application.bot_data.setdefault("picker_map", {})
    buttons: list[list[InlineKeyboardButton]] = []
    for row in rows[:2]:
        market_id = str(row["market_id"])
        token = _picker_token(chat_id, market_id)
        picker_map[f"{chat_id}:{token}"] = market_id
        delta = row.get("delta_yes")
        prefix = _fmt_num(delta, 3, signed=True) if delta is not None else "LIVE"
        label = f"{prefix} | {(row.get('question') or 'n/a')[:28]}".strip()
        buttons.append([InlineKeyboardButton(label, callback_data=f"wlpick:{token}")])
    buttons.append(
        [
            InlineKeyboardButton("Top movers", callback_data="menu:movers"),
            InlineKeyboardButton("Full picker" if locale == "en" else "Полный picker", callback_data="menu:pick"),
        ]
    )
    return InlineKeyboardMarkup(buttons)


def quick_reply_keyboard(locale: str = "ru") -> ReplyKeyboardMarkup:
    labels = (
        [
            ["Top movers", "Watchlist"],
            ["Inbox", "Plan"],
            ["Menu", "Upgrade"],
        ]
        if locale == "en"
        else [
            ["Топ муверы", "Вотчлист"],
            ["Инбокс", "План"],
            ["Меню", "Апгрейд"],
        ]
    )
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(cell) for cell in row] for row in labels],
        resize_keyboard=True,
    )


def _build_pro_payload(user_id: str) -> str:
    return f"{PRO_STARS_PAYLOAD_PREFIX}:{user_id}:{int(time.time())}"


def _parse_pro_payload(payload: str) -> str | None:
    if not payload or not payload.startswith(PRO_STARS_PAYLOAD_PREFIX + ":"):
        return None
    parts = payload.split(":")
    if len(parts) < 3:
        return None
    return parts[1]


async def send_stars_invoice_for_pro(bot, chat_id: int, user_ctx: dict, *, locale: str = "ru") -> bool:
    if not TELEGRAM_STARS_ENABLED or TELEGRAM_STARS_PRICE_XTR <= 0:
        return False

    payload = _build_pro_payload(user_ctx["user_id"])
    title = "Polymarket Pulse PRO (30 days)"
    if locale == "en":
        description = (
            f"PRO: up to {PRO_WATCHLIST_LIMIT} watchlist markets, "
            "unlimited push alerts, and email digest."
        )
    else:
        description = (
            f"PRO: до {PRO_WATCHLIST_LIMIT} рынков в watchlist, "
            "push-алерты без лимита и email-дайджест."
        )
    prices = [LabeledPrice(label="PRO Monthly", amount=TELEGRAM_STARS_PRICE_XTR)]
    await bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        currency="XTR",
        prices=prices,
        provider_token=None,
        start_parameter="pro-monthly",
    )
    return True


def _picker_token(chat_id: int, market_id: str) -> str:
    return hashlib.sha1(f"{chat_id}:{market_id}".encode("utf-8")).hexdigest()[:10]


async def send_movers_view(message, *, locale: str = "ru", show_loader: bool = True) -> None:
    if show_loader:
        await message.reply_text("Scanning live movers..." if locale == "en" else "Смотрю live movers...")
    try:
        rows = await fetch_top_movers_async(limit=3, timeout_sec=10.0)
    except asyncio.TimeoutError:
        await message.reply_text(
            "Database response timeout. Retry in 10-20 seconds."
            if locale == "en"
            else "База отвечает слишком долго. Повторите через 10-20 секунд."
        )
        return
    except Exception:
        log.exception("/movers failed")
        await message.reply_text("Failed to read movers from DB." if locale == "en" else "Ошибка чтения movers из БД.")
        return

    if rows:
        await message.reply_text(
            "Top live movers (up to 3):\n\n" + "\n\n".join(fmt_mover_row(r) for r in rows),
            reply_markup=trader_surface_keyboard(
                locale=locale,
                placement="bot_movers",
                market_id=str(rows[0].get("market_id")) if rows else None,
                extra_buttons=[
                    InlineKeyboardButton("Add market" if locale == "en" else "Добавить рынок", callback_data="menu:pick"),
                ],
            ),
        )
        return

    try:
        rows_30m = await fetch_top_movers_window_async(minutes=30, limit=3, timeout_sec=10.0)
    except Exception:
        rows_30m = []

    if rows_30m:
        await message.reply_text(
            (
                "Current window is flat. Showing fallback 30m movers:\n\n"
                if locale == "en"
                else "В текущем окне движение плоское. Показываю fallback 30m movers:\n\n"
            )
            + "\n\n".join(fmt_mover_row(r) for r in rows_30m),
            reply_markup=trader_surface_keyboard(
                locale=locale,
                placement="bot_movers_30m",
                market_id=str(rows_30m[0].get("market_id")) if rows_30m else None,
            ),
        )
        return

    try:
        rows_1h = await fetch_top_movers_1h_async(limit=3, timeout_sec=10.0)
    except Exception:
        rows_1h = []

    if rows_1h:
        await message.reply_text(
            (
                "Current last/prev window is flat. Showing 1h movers:\n\n"
                if locale == "en"
                else "В текущем окне last/prev движение плоское. Показываю 1h movers:\n\n"
            )
            + "\n\n".join(fmt_mover_row(r) for r in rows_1h),
            reply_markup=trader_surface_keyboard(
                locale=locale,
                placement="bot_movers_1h",
                market_id=str(rows_1h[0].get("market_id")) if rows_1h else None,
            ),
        )
        return

    await message.reply_text(
        (
            "No non-zero movers right now.\n"
            "Checked windows: latest, 30m and 1h. Movement is flat."
            if locale == "en"
            else "Сейчас нет ненулевых movers.\n"
            "Проверил окна: latest, 30m и 1h — движение плоское."
        ),
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("Add market" if locale == "en" else "Добавить рынок", callback_data="menu:pick"),
                InlineKeyboardButton("Change threshold" if locale == "en" else "Сменить threshold", callback_data="menu:threshold"),
            ]]
        ),
    )


async def send_inbox_view(
    message,
    user_ctx: dict,
    *,
    locale: str = "ru",
    limit: int = 10,
    show_loader: bool = True,
    context: ContextTypes.DEFAULT_TYPE | None = None,
) -> None:
    if show_loader:
        await message.reply_text("Reading your inbox..." if locale == "en" else "Читаю ваш inbox...")
    try:
        rows = await fetch_inbox_async(user_ctx["user_id"], limit=limit, timeout_sec=10.0)
    except asyncio.TimeoutError:
        await message.reply_text(
            "Database response timeout. Retry in 10-20 seconds."
            if locale == "en"
            else "База отвечает слишком долго. Повторите через 10-20 секунд."
        )
        return
    except Exception:
        log.exception("/inbox failed")
        await message.reply_text("Failed to read inbox from DB." if locale == "en" else "Ошибка чтения inbox из БД.")
        return

    if not rows:
        try:
            diag = await fetch_inbox_diagnostics_async(user_ctx["user_id"], user_ctx.get("threshold"), timeout_sec=10.0)
        except Exception:
            log.exception("inbox diagnostics failed")
            diag = {}
        total = int(diag.get("candidates_total") or 0)
        over = int(diag.get("over_threshold") or 0)
        threshold = _fmt_num(user_ctx.get("threshold"), 3)
        if total > 0 and over == 0:
            reason = (
                f"Signals exist ({total}), but all are below your threshold {threshold}.\n"
                "Try /threshold 0.02 or open /movers."
                if locale == "en"
                else f"Сигналы есть ({total}), но ниже вашего threshold {threshold}.\n"
                "Попробуйте /threshold 0.02 или откройте /movers."
            )
        elif total == 0:
            reason = (
                "No live deltas for your watchlist/positions in the current window.\n"
                "Common reason: closed markets or missing bid/ask quotes."
                if locale == "en"
                else "Нет live-дельт по вашему watchlist/positions в текущем окне.\n"
                "Частая причина: закрытые рынки или отсутствие котировок bid/ask."
            )
        else:
            reason = "No alerts in the current window." if locale == "en" else "Нет алертов в текущем окне."
        reply_markup = (
            await build_recovery_inline(message, context, user_ctx, locale=locale)
            if context is not None
            else InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("Top movers", callback_data="menu:movers"),
                    InlineKeyboardButton("Change threshold" if locale == "en" else "Сменить threshold", callback_data="menu:threshold"),
                ]]
            )
        )
        await message.reply_text(
            reason + (f"\nCurrent threshold: {threshold}" if locale == "en" else f"\nТекущий threshold: {threshold}"),
            reply_markup=reply_markup,
        )
        return

    header = "Inbox alerts:" if limit == 10 else ("Inbox alerts (20):" if locale == "en" else "Inbox alerts (20):")
    await message.reply_text(
        header + "\n\n" + "\n\n".join(fmt_alert_row(r) for r in rows),
        reply_markup=trader_surface_keyboard(
            locale=locale,
            placement="bot_inbox",
            market_id=str(rows[0].get("market_id")) if rows else None,
        ),
    )


async def send_watchlist_view(
    message,
    user_ctx: dict,
    *,
    locale: str = "ru",
    show_loader: bool = True,
    context: ContextTypes.DEFAULT_TYPE | None = None,
) -> None:
    if show_loader:
        await message.reply_text(
            "Checking live changes in your watchlist..." if locale == "en" else "Смотрю live изменения вашего watchlist..."
        )
    try:
        rows = await fetch_watchlist_snapshot_async(user_ctx["user_id"], limit=10, timeout_sec=10.0)
    except asyncio.TimeoutError:
        await message.reply_text(
            "Database response timeout. Retry in 10-20 seconds."
            if locale == "en"
            else "База отвечает слишком долго. Повторите через 10-20 секунд."
        )
        return
    except Exception:
        log.exception("/watchlist failed")
        await message.reply_text("Failed to read watchlist from DB." if locale == "en" else "Ошибка чтения watchlist из БД.")
        return

    if not rows:
        try:
            rows_30m = await fetch_watchlist_snapshot_window_async(user_ctx["user_id"], minutes=30, limit=10, timeout_sec=10.0)
        except Exception:
            log.exception("watchlist 30m fallback failed")
            rows_30m = []
        if rows_30m:
            await message.reply_text(
                (
                    "No changes in latest window. Showing 30m fallback:\n\n"
                    if locale == "en"
                    else "В latest-окне изменений нет. Показываю fallback 30m:\n\n"
                )
                + "\n\n".join(fmt_mover_row(r) for r in rows_30m),
                reply_markup=trader_surface_keyboard(
                    locale=locale,
                    placement="bot_watchlist_30m",
                    market_id=str(rows_30m[0].get("market_id")) if rows_30m else None,
                ),
            )
            return
        try:
            rows_1h = await fetch_watchlist_snapshot_window_async(user_ctx["user_id"], minutes=60, limit=10, timeout_sec=10.0)
        except Exception:
            log.exception("watchlist 1h fallback failed")
            rows_1h = []
        if rows_1h:
            await message.reply_text(
                (
                    "No changes in latest/30m windows. Showing 1h fallback:\n\n"
                    if locale == "en"
                    else "В latest/30m изменениях пусто. Показываю fallback 1h:\n\n"
                )
                + "\n\n".join(fmt_mover_row(r) for r in rows_1h),
                reply_markup=trader_surface_keyboard(
                    locale=locale,
                    placement="bot_watchlist_1h",
                    market_id=str(rows_1h[0].get("market_id")) if rows_1h else None,
                ),
            )
            return
        try:
            diag = await fetch_watchlist_diagnostics_async(user_ctx["user_id"], timeout_sec=10.0)
        except Exception:
            log.exception("watchlist diagnostics failed")
            diag = {}
        reply_markup = (
            await build_recovery_inline(message, context, user_ctx, locale=locale)
            if context is not None
            else InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Add market" if locale == "en" else "Добавить рынок", callback_data="menu:pick"),
                        InlineKeyboardButton("Top movers", callback_data="menu:movers"),
                    ],
                    [InlineKeyboardButton("Remove closed" if locale == "en" else "Очистить закрытые", callback_data="menu:cleanup_closed")],
                ]
            )
        )
        if context is not None and int(diag.get("wl_closed", 0) or 0) > 0:
            rows = list(reply_markup.inline_keyboard)
            rows.append([InlineKeyboardButton("Remove closed" if locale == "en" else "Очистить закрытые", callback_data="menu:cleanup_closed")])
            reply_markup = InlineKeyboardMarkup(rows)
        await message.reply_text(
            (
                "No live changes in your watchlist right now.\n"
                f"watchlist: {diag.get('wl_total', 0)} | active: {diag.get('wl_active', 0)} | "
                f"closed: {diag.get('wl_closed', 0)} | with quotes in last+prev: {diag.get('wl_with_quotes_both', 0)}"
                if locale == "en"
                else "По вашему watchlist сейчас нет live-изменений.\n"
                f"watchlist: {diag.get('wl_total', 0)} | active: {diag.get('wl_active', 0)} | "
                f"closed: {diag.get('wl_closed', 0)} | с котировками в last+prev: {diag.get('wl_with_quotes_both', 0)}"
            ),
            reply_markup=reply_markup,
        )
        return

    await message.reply_text(
        ("Watchlist live changes:\n\n" if locale == "en" else "Live-изменения watchlist:\n\n") + "\n\n".join(fmt_mover_row(r) for r in rows),
        reply_markup=trader_surface_keyboard(
            locale=locale,
            placement="bot_watchlist",
            market_id=str(rows[0].get("market_id")) if rows else None,
        ),
    )


def add_watchlist_market_sync(user_ctx: dict, market_id: str, *, locale: str = "ru") -> str:
    market_rows = run_db_query(SQL_MARKET_BRIEF, (market_id,), row_factory=dict_row)
    if not market_rows:
        return "Market not found." if locale == "en" else "Рынок не найден."

    exists = bool(run_db_query(SQL_WATCHLIST_EXISTS, (user_ctx["user_id"], market_id)))
    if exists:
        return "This market is already in your watchlist." if locale == "en" else "Этот рынок уже в вашем watchlist."

    plan = str(user_ctx.get("plan") or "free")
    limit = watchlist_limit_for_plan(plan)
    if int(user_ctx["watchlist_count"]) >= limit:
        plan_label = "PRO" if plan == "pro" else "FREE"
        if locale == "en":
            return (
                f"{plan_label} limit: {limit} markets. "
                "Remove one via /watchlist_remove, upgrade via /upgrade, or join execution alpha via /trade"
            )
        return (
            f"Лимит {plan_label}: {limit} рынка. "
            "Удалите один через /watchlist_remove, измените план через /upgrade или идите в execution alpha через /trade"
        )

    execute_db_write(SQL_WATCHLIST_ADD, (user_ctx["user_id"], market_id))
    live_rows = run_db_query(SQL_MARKET_LIVE_STATUS, (market_id,), row_factory=dict_row)
    live = live_rows[0] if live_rows else None
    market_status = str((live or {}).get("market_status") or "unknown")
    has_last = bool((live or {}).get("has_last_quotes"))
    has_prev = bool((live or {}).get("has_prev_quotes"))
    live_line = ""
    if market_status == "closed":
        live_line = (
            "Status now: market is already closed, so watchlist/inbox will likely stay silent."
            if locale == "en"
            else "Статус сейчас: рынок уже закрыт, поэтому watchlist/inbox, скорее всего, будут молчать."
        )
    elif has_last and has_prev:
        live_line = (
            "Status now: live quotes exist in last+prev, so this market is ready for watchlist/inbox tracking."
            if locale == "en"
            else "Статус сейчас: есть live-котировки в last+prev, значит рынок уже готов для watchlist/inbox."
        )
    elif has_last or has_prev:
        live_line = (
            "Status now: partial quotes only. The market is added, but inbox/watchlist may be quiet until both windows are live."
            if locale == "en"
            else "Статус сейчас: котировки только частично. Рынок добавлен, но inbox/watchlist могут молчать, пока оба окна не станут live."
        )
    else:
        live_line = (
            "Status now: no bid/ask quotes in last+prev yet. The market is added, but first live value may appear later."
            if locale == "en"
            else "Статус сейчас: пока нет bid/ask-котировок в last+prev. Рынок добавлен, но первая live-ценность может появиться позже."
        )
    if locale == "en":
        return (
            f"Added to watchlist: {market_id} — {market_rows[0]['question']}\n"
            f"{live_line}\n"
            "Next: open Watchlist for live changes or Inbox for alerts."
        )
    return (
        f"Добавлено в watchlist: {market_id} — {market_rows[0]['question']}\n"
        f"{live_line}\n"
        "Дальше: откройте Watchlist для live-изменений или Inbox для алертов."
    )


def cleanup_closed_watchlist_sync(user_id: str) -> int:
    with psycopg.connect(PG_CONN, connect_timeout=DB_CONNECT_TIMEOUT_SECONDS) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            cur.execute(SQL_WATCHLIST_REMOVE_CLOSED, (user_id,))
            deleted = cur.rowcount or 0
        conn.commit()
    return int(deleted)


def _picker_category_label(category: str) -> str:
    return {
        "all": "All",
        "crypto": "Crypto",
        "politics": "Politics",
        "macro": "Macro",
    }.get(category, "All")


async def send_watchlist_picker(
    message,
    context: ContextTypes.DEFAULT_TYPE,
    user_ctx: dict,
    *,
    category: str = "all",
    locale: str = "ru",
    edit_message: bool = False,
) -> None:
    rows = await fetch_watchlist_picker_candidates_async(
        user_id=user_ctx["user_id"], category=category, limit=16, timeout_sec=10.0
    )
    if not rows:
        text = (
            f"No live candidates for {_picker_category_label(category)} filter right now.\n"
            f"Current picker floor: liquidity >= {int(WATCHLIST_PICKER_MIN_LIQUIDITY)}.\n"
            "Try another filter or /watchlist_add <market_id|slug>."
            if locale == "en"
            else f"Для фильтра {_picker_category_label(category)} сейчас нет live-кандидатов.\n"
            f"Текущий порог picker: liquidity >= {int(WATCHLIST_PICKER_MIN_LIQUIDITY)}.\n"
            "Попробуйте другой фильтр или /watchlist_add <market_id|slug>."
        )
        if edit_message:
            try:
                await message.edit_text(text)
                return
            except Exception:
                log.debug("watchlist picker edit failed; fallback to reply", exc_info=True)
        await message.reply_text(text)
        return

    chat_id = message.chat_id
    picker_map = context.application.bot_data.setdefault("picker_map", {})
    picker_category = context.application.bot_data.setdefault("picker_category", {})
    picker_category[str(chat_id)] = category
    buttons: list[list[InlineKeyboardButton]] = []
    buttons.append(
        [
            InlineKeyboardButton("All", callback_data="menu:pick_cat:all"),
            InlineKeyboardButton("Crypto", callback_data="menu:pick_cat:crypto"),
            InlineKeyboardButton("Politics", callback_data="menu:pick_cat:politics"),
            InlineKeyboardButton("Macro", callback_data="menu:pick_cat:macro"),
        ]
    )
    for row in rows:
        market_id = str(row["market_id"])
        token = _picker_token(chat_id, market_id)
        picker_map[f"{chat_id}:{token}"] = market_id
        delta = row.get("delta_yes")
        liq = row.get("liquidity")
        cat = (row.get("cat_tag") or "other").upper()[:3]
        prefix = "MOV" if delta is not None else "LIVE"
        delta_part = _fmt_num(delta, 3, signed=True) if delta is not None else ""
        liq_part = f" L:{_fmt_num(liq, 0)}" if liq is not None else ""
        label = f"{cat} {prefix} {delta_part}{liq_part} | {(row.get('question') or 'n/a')[:36]}".strip()
        buttons.append([InlineKeyboardButton(label, callback_data=f"wlpick:{token}")])

    buttons.append(
        [
            InlineKeyboardButton("Refresh list" if locale == "en" else "Обновить список", callback_data="menu:pick_refresh"),
            InlineKeyboardButton("Open full movers" if locale == "en" else "Открыть full movers", callback_data="menu:movers"),
        ]
    )
    availability = (
        f"Live high-liquidity candidates now: {len(rows)}. Floor: {int(WATCHLIST_PICKER_MIN_LIQUIDITY)}."
        if locale == "en"
        else f"Live high-liquidity кандидатов сейчас: {len(rows)}. Порог: {int(WATCHLIST_PICKER_MIN_LIQUIDITY)}."
    )
    if category == "all" and len(rows) < 6:
        availability += (
            " Narrow live window: add market_id/slug manually if you need a specific market."
            if locale == "en"
            else " Live-окно узкое: добавьте market_id/slug вручную, если нужен конкретный рынок."
        )
    picker_text = (
        f"Choose a market for watchlist. Filter: {_picker_category_label(category)}.\n"
        "Tap a row to add market immediately.\n"
        f"{availability}\n"
        "If missing: /watchlist_add <market_id|slug>"
        if locale == "en"
        else f"Выберите рынок для watchlist. Фильтр: {_picker_category_label(category)}.\n"
        "Нажмите на строку — рынок добавится сразу.\n"
        f"{availability}\n"
        "Если нужного рынка нет: /watchlist_add <market_id|slug>"
    )
    if edit_message:
        try:
            await message.edit_text(picker_text, reply_markup=InlineKeyboardMarkup(buttons))
            return
        except Exception:
            log.debug("watchlist picker edit failed; fallback to reply", exc_info=True)
    await message.reply_text(picker_text, reply_markup=InlineKeyboardMarkup(buttons))


def resolve_user_context_sync(update: Update) -> dict:
    tg_user = update.effective_user
    tg_chat = update.effective_chat
    if tg_user is None or tg_chat is None:
        raise RuntimeError("telegram context missing")

    user_row = run_db_query(
        SQL_RESOLVE_USER,
        (
            tg_user.id,
            tg_chat.id,
            tg_user.username,
            tg_user.first_name,
            tg_user.last_name,
            tg_user.language_code or "ru",
        ),
        row_factory=dict_row,
    )[0]

    user_id = str(user_row["user_id"])
    context_row = run_db_query(
        SQL_USER_CONTEXT,
        (user_id, user_id, user_id),
        row_factory=dict_row,
    )[0]
    context_row["user_id"] = user_id
    return context_row


async def resolve_user_context(update: Update) -> dict:
    return await asyncio.to_thread(resolve_user_context_sync, update)


async def fetch_inbox_async(user_id: str, limit: int = 10, timeout_sec: float = 10.0) -> list[dict]:
    return await asyncio.wait_for(
        asyncio.to_thread(lambda: run_db_query(SQL_INBOX, (user_id, limit), row_factory=dict_row)),
        timeout=timeout_sec,
    )


async def fetch_top_movers_async(limit: int = 3, timeout_sec: float = 10.0) -> list[dict]:
    return await asyncio.wait_for(
        asyncio.to_thread(lambda: run_db_query(SQL_TOP_MOVERS, (limit,), row_factory=dict_row)),
        timeout=timeout_sec,
    )

async def fetch_top_movers_1h_async(limit: int = 3, timeout_sec: float = 10.0) -> list[dict]:
    return await asyncio.wait_for(
        asyncio.to_thread(lambda: run_db_query(SQL_TOP_MOVERS_1H, (limit,), row_factory=dict_row)),
        timeout=timeout_sec,
    )


async def fetch_top_movers_window_async(minutes: int, limit: int = 3, timeout_sec: float = 10.0) -> list[dict]:
    return await asyncio.wait_for(
        asyncio.to_thread(lambda: run_db_query(SQL_TOP_MOVERS_WINDOW, (minutes, limit), row_factory=dict_row)),
        timeout=timeout_sec,
    )


async def fetch_watchlist_snapshot_async(user_id: str, limit: int = 10, timeout_sec: float = 10.0) -> list[dict]:
    return await asyncio.wait_for(
        asyncio.to_thread(lambda: run_db_query(SQL_WATCHLIST_SNAPSHOT, (user_id, limit), row_factory=dict_row)),
        timeout=timeout_sec,
    )


async def fetch_watchlist_snapshot_window_async(
    user_id: str, *, minutes: int, limit: int = 10, timeout_sec: float = 10.0
) -> list[dict]:
    return await asyncio.wait_for(
        asyncio.to_thread(
            lambda: run_db_query(SQL_WATCHLIST_SNAPSHOT_WINDOW, (minutes, user_id, limit), row_factory=dict_row)
        ),
        timeout=timeout_sec,
    )


async def fetch_watchlist_diagnostics_async(user_id: str, timeout_sec: float = 10.0) -> dict:
    rows = await asyncio.wait_for(
        asyncio.to_thread(lambda: run_db_query(SQL_WATCHLIST_DIAGNOSTICS, (user_id,), row_factory=dict_row)),
        timeout=timeout_sec,
    )
    return rows[0] if rows else {}


async def fetch_watchlist_picker_candidates_async(
    *, user_id: str, category: str = "all", limit: int = 12, timeout_sec: float = 10.0
) -> list[dict]:
    return await asyncio.wait_for(
        asyncio.to_thread(
            lambda: run_db_query(
                SQL_WATCHLIST_PICKER_CANDIDATES,
                (category, user_id, WATCHLIST_PICKER_MIN_LIQUIDITY, limit),
                row_factory=dict_row,
            )
        ),
        timeout=timeout_sec,
    )


async def fetch_inbox_diagnostics_async(user_id: str, threshold: Any, timeout_sec: float = 10.0) -> dict:
    thr = Decimal(str(threshold or 0.03))
    rows = await asyncio.wait_for(
        asyncio.to_thread(lambda: run_db_query(SQL_INBOX_DIAGNOSTICS, (user_id, user_id, thr), row_factory=dict_row)),
        timeout=timeout_sec,
    )
    return rows[0] if rows else {}


def sent_today_sync(user_id: str) -> int:
    return int(run_db_query(SQL_ALERTS_SENT_TODAY, (user_id,))[0][0])


def is_sent_sync(channel: str, recipient: str, market_id: str, alert_type: str, bucket: Any) -> bool:
    rows = run_db_query(SQL_SENT_ALERT_EXISTS, (channel, recipient, market_id, alert_type, bucket))
    return bool(rows)


def log_sent_sync(channel: str, user_id: str, recipient: str, row: dict) -> None:
    payload = Jsonb(
        {
            "question": row.get("question"),
            "delta_mid": str(row.get("delta_mid")),
            "abs_delta": str(row.get("abs_delta")),
        }
    )
    execute_db_write(
        SQL_SENT_ALERT_INSERT,
        (
            channel,
            user_id,
            recipient,
            str(row.get("market_id")),
            row.get("alert_type"),
            row.get("last_bucket"),
            payload,
        ),
    )


def upsert_event_sync(user_id: str, row: dict) -> None:
    payload = Jsonb(
        {
            "question": row.get("question"),
            "mid_now": str(row.get("mid_now")),
            "mid_prev": str(row.get("mid_prev")),
            "delta_mid": str(row.get("delta_mid")),
        }
    )
    execute_db_write(
        SQL_ALERT_EVENT_UPSERT,
        (
            user_id,
            str(row.get("market_id")),
            row.get("alert_type"),
            row.get("last_bucket"),
            row.get("abs_delta") or abs(Decimal(str(row.get("delta_mid") or 0))),
            payload,
        ),
    )


def log_upgrade_intent_sync(update: Update, user_ctx: dict) -> None:
    tg_user = update.effective_user
    tg_chat = update.effective_chat
    payload = Jsonb(
        {
            "plan": user_ctx.get("plan"),
            "watchlist_count": user_ctx.get("watchlist_count"),
            "alerts_sent_today": user_ctx.get("alerts_sent_today"),
            "threshold": str(user_ctx.get("threshold")),
            "username": tg_user.username if tg_user else None,
            "first_name": tg_user.first_name if tg_user else None,
            "last_name": tg_user.last_name if tg_user else None,
            "lang": tg_user.language_code if tg_user else None,
        }
    )
    execute_db_write(
        SQL_UPGRADE_INTENT_INSERT,
        (
            user_ctx["user_id"],
            tg_user.id if tg_user else None,
            tg_chat.id if tg_chat else None,
            "telegram_bot",
            payload,
        ),
    )


def log_trade_interest_sync(update: Update, user_ctx: dict, *, market_id: str | None = None, source: str = "pulse_bot") -> None:
    tg_user = update.effective_user
    tg_chat = update.effective_chat
    payload = Jsonb(
        {
            "plan": user_ctx.get("plan"),
            "watchlist_count": user_ctx.get("watchlist_count"),
            "alerts_sent_today": user_ctx.get("alerts_sent_today"),
            "threshold": str(user_ctx.get("threshold")),
            "telegram_id": tg_user.id if tg_user else None,
            "chat_id": tg_chat.id if tg_chat else None,
            "username": tg_user.username if tg_user else None,
            "lang": tg_user.language_code if tg_user else None,
        }
    )
    execute_db_write(
        SQL_TRADE_ACTIVITY_INSERT,
        (
            user_ctx["user_id"],
            "trader_alpha_interest",
            source,
            market_id,
            payload,
        ),
    )


async def dispatch_push_alerts(application: Application) -> None:
    rows = await asyncio.wait_for(
        asyncio.to_thread(lambda: run_db_query(SQL_PUSH_CANDIDATES, (PUSH_FETCH_LIMIT,), row_factory=dict_row)),
        timeout=15.0,
    )
    if not rows:
        return

    sent_count = 0
    sent_today_cache: dict[str, int] = {}
    for row in rows:
        user_id = str(row["user_id"])
        recipient = str(row["chat_id"])
        market_id = str(row["market_id"])
        alert_type = row["alert_type"]
        bucket = row["last_bucket"]
        plan = row.get("plan") or "free"

        if user_id not in sent_today_cache:
            sent_today_cache[user_id] = await asyncio.to_thread(sent_today_sync, user_id)

        if plan == "free" and sent_today_cache[user_id] >= FREE_DAILY_ALERT_LIMIT:
            continue

        already_sent = await asyncio.to_thread(is_sent_sync, "bot", recipient, market_id, alert_type, bucket)
        if already_sent:
            continue

        await application.bot.send_message(chat_id=int(recipient), text="🔔 Alert\n\n" + fmt_alert_row(row))
        await asyncio.to_thread(upsert_event_sync, user_id, row)
        await asyncio.to_thread(log_sent_sync, "bot", user_id, recipient, row)
        sent_today_cache[user_id] += 1
        sent_count += 1

    if sent_count:
        log.info("push_loop delivered=%s", sent_count)


async def push_loop(application: Application) -> None:
    log.info("push_loop started interval=%ss", PUSH_INTERVAL_SECONDS)
    if PUSH_INITIAL_DELAY_SECONDS > 0:
        await asyncio.sleep(PUSH_INITIAL_DELAY_SECONDS)
    while True:
        try:
            await dispatch_push_alerts(application)
        except asyncio.CancelledError:
            log.info("push_loop cancelled")
            raise
        except Exception:
            log.exception("push_loop iteration failed")
        await asyncio.sleep(PUSH_INTERVAL_SECONDS)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    locale = locale_from_update(update)
    try:
        user_ctx = await resolve_user_context(update)
    except Exception:
        log.exception("/start resolve_user failed")
        await update.message.reply_text(
            "Failed to initialize profile. Try again later."
            if locale == "en"
            else "Не удалось инициализировать профиль. Попробуйте позже."
        )
        return

    await update.message.reply_text(
        (
            "Profile activated.\n\n"
            "What the bot does:\n"
            "• shows top live movers\n"
            "• tracks your watchlist markets\n"
            "• sends push alerts on probability shifts\n\n"
            "Quick start in 60 seconds:\n"
            "1) /menu — open quick actions\n"
            "2) /movers — view 3 live moves\n"
            "3) /watchlist — view live delta for your list\n"
            "4) /threshold 0.03 — set sensitivity\n\n"
            f"{user_limits_block(user_ctx, locale=locale)}\n\n"
            "Next:\n"
            "/help — command reference\n"
            "/upgrade — move to PRO\n"
            "/trade — join execution alpha"
            if locale == "en"
            else "Профиль активирован.\n\n"
            "Что бот делает:\n"
            "• показывает top live movers\n"
            "• отслеживает ваши рынки в watchlist\n"
            "• присылает push по движению вероятностей\n\n"
            "Быстрый старт за 60 секунд:\n"
            "1) /menu — открыть быстрые кнопки\n"
            "2) /movers — посмотреть 3 live движения\n"
            "3) /watchlist — увидеть live-дельту по вашему списку\n"
            "4) /threshold 0.03 — настроить чувствительность\n\n"
            f"{user_limits_block(user_ctx, locale=locale)}\n\n"
            "Полезно дальше:\n"
            "/help — все команды и расширенные опции\n"
            "/upgrade — как перейти на PRO\n"
            "/trade — execution alpha"
        ),
        reply_markup=quick_reply_keyboard(locale),
    )
    await update.message.reply_text(
        (
            "First useful step: add one live market to your watchlist."
            if locale == "en"
            else "Первый полезный шаг: добавьте один live-рынок в watchlist."
        ),
        reply_markup=onboarding_start_inline(locale),
    )
    if int(user_ctx.get("watchlist_count") or 0) == 0:
        try:
            starter_rows = await fetch_watchlist_picker_candidates_async(
                user_id=user_ctx["user_id"],
                category="all",
                limit=3,
                timeout_sec=10.0,
            )
        except Exception:
            log.exception("/start onboarding picker fetch failed")
            starter_rows = []
        if starter_rows:
            await update.message.reply_text(
                (
                    "Tap one market below to add it instantly:"
                    if locale == "en"
                    else "Нажмите на один рынок ниже, чтобы добавить его сразу:"
                ),
                reply_markup=onboarding_picker_inline(
                    update.effective_chat.id,
                    starter_rows,
                    context.application.bot_data,
                    locale=locale,
                ),
            )
    await update.message.reply_text(
        "Quick menu:" if locale == "en" else "Быстрое меню:",
        reply_markup=main_menu_inline(),
    )
    log.info("cmd=/start chat_id=%s tg_user=%s app_user=%s", update.effective_chat.id, update.effective_user.id, user_ctx["user_id"])


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    locale = locale_from_update(update)
    await update.message.reply_text(
        (
            "Core commands:\n"
            "/start — onboarding and profile\n"
            "/movers — top 3 live movers\n"
            "/watchlist — live changes for your watchlist\n"
            "/inbox — latest alerts\n"
            "/plan — current plan and usage\n"
            "/menu — inline action menu\n"
            "/upgrade — move to PRO\n\n"
            "Advanced commands:\n"
            "/watchlist_list — list markets\n"
            "/watchlist_add <market_id|slug>\n"
            "/watchlist_remove <market_id|slug>\n"
            "/threshold 0.03 — personal threshold\n"
            "/limits — FREE/PRO limits\n"
            "/inbox20 — extended inbox\n"
            "/trade — execution alpha handoff"
            if locale == "en"
            else "Основные команды:\n"
            "/start — активация профиля\n"
            "/movers — top 3 live movers\n"
            "/watchlist — live изменения по вашему watchlist\n"
            "/inbox — последние алерты\n"
            "/plan — текущий план и usage\n"
            "/menu — inline-меню действий\n"
            "/upgrade — переход на PRO\n\n"
            "Расширенные команды:\n"
            "/watchlist_list — список рынков\n"
            "/watchlist_add <market_id|slug>\n"
            "/watchlist_remove <market_id|slug>\n"
            "/threshold 0.03 — персональный порог\n"
            "/limits — лимиты FREE/PRO\n"
            "/inbox20 — расширенный inbox\n"
            "/trade — переход в execution alpha"
        )
    )


async def cmd_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    locale = locale_from_update(update)
    try:
        user_ctx = await resolve_user_context(update)
    except Exception:
        await update.message.reply_text("Failed to read profile." if locale == "en" else "Не удалось прочитать профиль.")
        return

    await update.message.reply_text(
        (
            "Current status:\n"
            f"{user_limits_block(user_ctx, locale=locale)}\n\n"
            f"PRO offer: up to {PRO_WATCHLIST_LIMIT} markets + email digest, "
            f"about ${PRO_MONTHLY_USD}/month in Telegram Stars.\n\n"
            "Next step:\n"
            "1) Add a market via /watchlist_add\n"
            "2) Set threshold via /threshold 0.03\n"
            "3) Upgrade: /upgrade\n"
            "4) Execution alpha: /trade\n\n"
            f"{plan_upgrade_hint(update)}"
            if locale == "en"
            else "Текущий статус:\n"
            f"{user_limits_block(user_ctx, locale=locale)}\n\n"
            f"PRO оффер: до {PRO_WATCHLIST_LIMIT} рынков + email-дайджест, эквивалент ${PRO_MONTHLY_USD}/мес в Telegram Stars.\n\n"
            "Следующий шаг:\n"
            "1) Добавьте рынок через /watchlist_add\n"
            "2) Настройте порог через /threshold 0.03\n"
            "3) Для PRO: /upgrade\n"
            "4) Для execution alpha: /trade\n\n"
            f"{plan_upgrade_hint(update)}"
        ),
        reply_markup=main_menu_inline(),
    )


async def cmd_limits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    locale = locale_from_update(update)
    try:
        user_ctx = await resolve_user_context(update)
    except Exception:
        await update.message.reply_text("Failed to read limits." if locale == "en" else "Не удалось прочитать лимиты.")
        return

    await update.message.reply_text(
        (
            "Limits and access:\n\n"
            "FREE:\n"
            f"• up to {FREE_WATCHLIST_LIMIT} markets in watchlist\n"
            f"• up to {FREE_DAILY_ALERT_LIMIT} push alerts/day\n\n"
            "PRO:\n"
            f"• up to {PRO_WATCHLIST_LIMIT} markets in watchlist\n"
            "• unlimited push alerts\n"
            "• email digest included\n\n"
            f"PRO price: about ${PRO_MONTHLY_USD}/month in Telegram Stars\n\n"
            f"Your current usage:\n{user_limits_block(user_ctx, locale=locale)}\n\n"
            "Upgrade: /upgrade\n"
            "Need execution alpha? /trade"
            if locale == "en"
            else "Лимиты и доступ:\n\n"
            "FREE:\n"
            f"• до {FREE_WATCHLIST_LIMIT} рынков в watchlist\n"
            f"• до {FREE_DAILY_ALERT_LIMIT} push-алертов в день\n\n"
            "PRO:\n"
            f"• до {PRO_WATCHLIST_LIMIT} рынков в watchlist\n"
            "• push-алерты без лимита\n\n"
            "• email-дайджест включен\n\n"
            f"Цена PRO: эквивалент ${PRO_MONTHLY_USD}/месяц в Telegram Stars\n\n"
            f"Ваш текущий usage:\n{user_limits_block(user_ctx, locale=locale)}\n\n"
            "Чтобы перейти на PRO: /upgrade\n"
            "Нужен execution alpha? /trade"
        )
    )


async def cmd_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    locale = locale_from_update(update)
    user_ctx = await resolve_user_context(update)
    try:
        await asyncio.to_thread(log_upgrade_intent_sync, update, user_ctx)
    except Exception:
        log.exception("/upgrade intent insert failed")
    await update.message.reply_text(
        upgrade_pitch_text(update),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    try:
        invoice_sent = await send_stars_invoice_for_pro(context.bot, update.effective_chat.id, user_ctx, locale=locale)
    except Exception:
        log.exception("stars invoice send failed")
        invoice_sent = False

    if not invoice_sent:
        await update.message.reply_text(
            (
                "Stars checkout is temporarily unavailable.\n"
                "Use the site: https://polymarketpulse.app/telegram-bot?lang=en"
                if locale == "en"
                else "Stars-счет временно недоступен.\n"
                "Используйте сайт: https://polymarketpulse.app/telegram-bot?lang=ru"
            ),
            disable_web_page_preview=True,
        )


async def cmd_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    locale = locale_from_update(update)
    user_ctx = await resolve_user_context(update)
    try:
        await asyncio.to_thread(log_trade_interest_sync, update, user_ctx, market_id=None, source="pulse_bot_command")
    except Exception:
        log.exception("/trade interest insert failed")
    await update.message.reply_text(
        trade_pitch_text(update),
        parse_mode="HTML",
        reply_markup=trader_alpha_keyboard(locale=locale, placement="bot_trade_command"),
        disable_web_page_preview=True,
    )


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    locale = locale_from_update(update)
    await update.message.reply_text("Choose action:" if locale == "en" else "Выберите действие:", reply_markup=main_menu_inline())


async def cmd_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    locale = locale_from_update(update)
    if not context.args:
        user_ctx = await resolve_user_context(update)
        await update.message.reply_text(
            (
                f"Your current threshold: {_fmt_num(user_ctx['threshold'], 3)}\n"
                "Format: /threshold 0.03"
                if locale == "en"
                else f"Ваш текущий порог: {_fmt_num(user_ctx['threshold'], 3)}\n"
                "Формат изменения: /threshold 0.03"
            )
        )
        return
    try:
        value = Decimal(context.args[0])
    except Exception:
        await update.message.reply_text(
            "Invalid value. Example: /threshold 0.03"
            if locale == "en"
            else "Некорректное значение. Пример: /threshold 0.03"
        )
        return

    if value < 0 or value > 1:
        await update.message.reply_text("Threshold must be between 0 and 1." if locale == "en" else "Порог должен быть в диапазоне 0..1")
        return

    user_ctx = await resolve_user_context(update)
    execute_db_write(SQL_SET_THRESHOLD, (user_ctx["user_id"], value))
    await update.message.reply_text(
        f"Threshold updated: {_fmt_num(value, 3)}" if locale == "en" else f"Порог обновлен: {_fmt_num(value, 3)}"
    )


async def cmd_movers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await send_movers_view(update.message, locale=locale_from_update(update), show_loader=True)


async def cmd_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE, limit: int = 10):
    if not update.message:
        return
    user_ctx = await resolve_user_context(update)
    await send_inbox_view(
        update.message,
        user_ctx,
        locale=locale_from_update(update),
        limit=limit,
        show_loader=True,
        context=context,
    )


async def cmd_inbox10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_inbox(update, context, limit=10)


async def cmd_inbox20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_inbox(update, context, limit=20)


async def cmd_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user_ctx = await resolve_user_context(update)
    await send_watchlist_view(
        update.message,
        user_ctx,
        locale=locale_from_update(update),
        show_loader=True,
        context=context,
    )


async def cmd_watchlist_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    locale = locale_from_update(update)
    user_ctx = await resolve_user_context(update)
    rows = run_db_query(SQL_WATCHLIST_LIST, (user_ctx["user_id"], 50), row_factory=dict_row)
    if not rows:
        await update.message.reply_text(
            "Your watchlist is empty. Use /watchlist_add <market_id|slug>."
            if locale == "en"
            else "Ваш watchlist пуст. Используйте /watchlist_add <market_id|slug>."
        )
        return

    lines = []
    for idx, row in enumerate(rows, start=1):
        lines.append(f"{idx}. {row['market_id']} — {row['question']}")
    await update.message.reply_text(("Your watchlist:\n" if locale == "en" else "Ваш watchlist:\n") + "\n".join(lines))


async def cmd_watchlist_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    locale = locale_from_update(update)
    if not context.args:
        user_ctx = await resolve_user_context(update)
        await send_watchlist_picker(update.message, context, user_ctx, locale=locale)
        return

    ref = context.args[0].strip()
    user_ctx = await resolve_user_context(update)

    market_rows = run_db_query(SQL_FIND_MARKET, (ref, ref), row_factory=dict_row)
    if not market_rows:
        await update.message.reply_text(
            "Market not found. Provide market_id or slug."
            if locale == "en"
            else "Рынок не найден. Укажите market_id или slug."
        )
        return

    market = market_rows[0]
    market_id = str(market["market_id"])

    exists = bool(run_db_query(SQL_WATCHLIST_EXISTS, (user_ctx["user_id"], market_id)))
    if exists:
        await update.message.reply_text(
            "This market is already in your watchlist."
            if locale == "en"
            else "Этот рынок уже в вашем watchlist."
        )
        return

    plan = str(user_ctx.get("plan") or "free")
    limit = watchlist_limit_for_plan(plan)
    if int(user_ctx["watchlist_count"]) >= limit:
        plan_label = "PRO" if plan == "pro" else "FREE"
        await update.message.reply_text(
            (
                f"{plan_label} limit: {limit} markets. Remove one via /watchlist_remove or upgrade: /upgrade"
                if locale == "en"
                else f"Лимит {plan_label}: {limit} рынка. Удалите один через /watchlist_remove или измените план: /upgrade"
            )
        )
        return

    execute_db_write(SQL_WATCHLIST_ADD, (user_ctx["user_id"], market_id))
    await update.message.reply_text(
        f"Added to watchlist: {market_id} — {market['question']}"
        if locale == "en"
        else f"Добавлено в watchlist: {market_id} — {market['question']}"
        ,
        reply_markup=watchlist_added_inline(locale),
    )


async def cmd_watchlist_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    locale = locale_from_update(update)
    if not context.args:
        await update.message.reply_text(
            "Format: /watchlist_remove <market_id|slug>"
            if locale == "en"
            else "Формат: /watchlist_remove <market_id|slug>"
        )
        return

    ref = context.args[0].strip()
    user_ctx = await resolve_user_context(update)

    market_rows = run_db_query(SQL_FIND_MARKET, (ref, ref), row_factory=dict_row)
    market_id = ref if not market_rows else str(market_rows[0]["market_id"])
    execute_db_write(SQL_WATCHLIST_REMOVE, (user_ctx["user_id"], market_id))
    await update.message.reply_text(
        f"Removed from watchlist: {market_id}" if locale == "en" else f"Удалено из watchlist: {market_id}"
    )


async def cmd_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    allow = os.environ.get("ADMIN_TELEGRAM_IDS", "")
    allow_set = {x.strip() for x in allow.split(",") if x.strip()}
    tg_id = str(update.effective_user.id if update.effective_user else "")
    if tg_id not in allow_set:
        await update.message.reply_text("Команда недоступна.")
        return

    q = """
    select
      (select count(*) from app.users) as users_total,
      (select count(*) from bot.profiles where bot.current_plan(user_id) = 'free') as free_total,
      (select count(*) from bot.profiles where bot.current_plan(user_id) = 'pro') as pro_total,
      (select count(*) from bot.sent_alerts_log where channel = 'bot' and sent_at >= date_trunc('day', now())) as alerts_today
    """
    row = run_db_query(q, (), row_factory=dict_row)[0]
    await update.message.reply_text(
        "Admin stats:\n"
        f"users: {row['users_total']}\n"
        f"free: {row['free_total']}\n"
        f"pro: {row['pro_total']}\n"
        f"alerts today: {row['alerts_today']}"
    )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    locale = locale_from_update(update)
    await update.message.reply_text(
        (
            "Unknown command.\n"
            "Use /help.\n"
            "Quick start: /menu, /movers, /watchlist, /inbox"
            if locale == "en"
            else "Неизвестная команда.\n"
            "Используйте /help.\n"
            "Быстрый старт: /menu, /movers, /watchlist, /inbox"
        )
    )


async def on_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return
    text = message.text.strip()
    routes = {
        "Top movers": cmd_movers,
        "Топ муверы": cmd_movers,
        "Watchlist": cmd_watchlist,
        "Вотчлист": cmd_watchlist,
        "Inbox": cmd_inbox10,
        "Инбокс": cmd_inbox10,
        "Plan": cmd_plan,
        "План": cmd_plan,
        "Menu": cmd_menu,
        "Меню": cmd_menu,
        "Upgrade": cmd_upgrade,
        "Апгрейд": cmd_upgrade,
        "Help": cmd_help,
        "Помощь": cmd_help,
    }
    handler = routes.get(text)
    if handler is None:
        return
    await handler(update, context)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.message:
        return
    locale = locale_from_update(update)
    await query.answer()
    data = query.data or ""

    if data == "menu:movers":
        await send_movers_view(query.message, locale=locale, show_loader=False)
        return
    if data == "menu:watchlist":
        user_ctx = await resolve_user_context(update)
        await send_watchlist_view(query.message, user_ctx, locale=locale, show_loader=False, context=context)
        return
    if data == "menu:inbox":
        user_ctx = await resolve_user_context(update)
        await send_inbox_view(query.message, user_ctx, locale=locale, limit=10, show_loader=False, context=context)
        return
    if data == "menu:plan":
        user_ctx = await resolve_user_context(update)
        await query.message.reply_text(
            (
                f"Current status:\n{user_limits_block(user_ctx, locale=locale)}"
                if locale == "en"
                else f"Текущий статус:\n{user_limits_block(user_ctx, locale=locale)}"
            ),
            reply_markup=main_menu_inline(),
        )
        return
    if data == "menu:upgrade":
        user_ctx = await resolve_user_context(update)
        await query.message.reply_text(
            upgrade_pitch_text(update),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        try:
            invoice_sent = await send_stars_invoice_for_pro(context.bot, query.message.chat_id, user_ctx, locale=locale)
        except Exception:
            log.exception("stars invoice send failed from callback")
            invoice_sent = False
        if not invoice_sent:
            await query.message.reply_text(
                (
                    "Stars checkout is temporarily unavailable.\n"
                    "Use the site: https://polymarketpulse.app/telegram-bot?lang=en"
                    if locale == "en"
                    else "Stars-счет временно недоступен.\n"
                    "Используйте сайт: https://polymarketpulse.app/telegram-bot?lang=ru"
                ),
                disable_web_page_preview=True,
            )
        return
    if data == "menu:help":
        await query.message.reply_text("Command list: /help" if locale == "en" else "Список команд: /help")
        return
    if data == "menu:threshold":
        user_ctx = await resolve_user_context(update)
        await query.message.reply_text(
            (
                f"Your threshold: {_fmt_num(user_ctx['threshold'], 3)}\n"
                "Change: /threshold 0.03"
                if locale == "en"
                else f"Ваш порог: {_fmt_num(user_ctx['threshold'], 3)}\n"
                "Изменить: /threshold 0.03"
            )
        )
        return
    if data == "menu:pick":
        user_ctx = await resolve_user_context(update)
        await send_watchlist_picker(query.message, context, user_ctx, category="all", locale=locale, edit_message=True)
        return
    if data.startswith("menu:pick_cat:"):
        category = data.split(":", 2)[2]
        if category not in {"all", "crypto", "politics", "macro"}:
            category = "all"
        user_ctx = await resolve_user_context(update)
        await send_watchlist_picker(
            query.message, context, user_ctx, category=category, locale=locale, edit_message=True
        )
        return
    if data == "menu:pick_refresh":
        picker_category = context.application.bot_data.get("picker_category", {})
        category = picker_category.get(str(query.message.chat_id), "all")
        user_ctx = await resolve_user_context(update)
        await send_watchlist_picker(
            query.message, context, user_ctx, category=category, locale=locale, edit_message=True
        )
        return
    if data == "menu:cleanup_closed":
        user_ctx = await resolve_user_context(update)
        removed = await asyncio.to_thread(cleanup_closed_watchlist_sync, user_ctx["user_id"])
        await query.message.reply_text(
            (
                f"Removed closed markets from watchlist: {removed}\n"
                "Now add a live market via “Add market”."
                if locale == "en"
                else f"Удалено закрытых рынков из watchlist: {removed}\n"
                "Теперь добавьте live рынок через кнопку «Добавить рынок»."
            ),
            reply_markup=main_menu_inline(),
        )
        return
    if data.startswith("wlpick:"):
        token = data.split(":", 1)[1]
        chat_key = f"{query.message.chat_id}:{token}"
        picker_map = context.application.bot_data.get("picker_map", {})
        market_id = picker_map.get(chat_key)
        if not market_id:
            await query.message.reply_text(
                "Selection item is expired. Open /menu and retry."
                if locale == "en"
                else "Элемент выбора устарел. Откройте /menu и повторите."
            )
            return
        user_ctx = await resolve_user_context(update)
        result = await asyncio.to_thread(add_watchlist_market_sync, user_ctx, market_id, locale=locale)
        await query.message.reply_text(result, reply_markup=watchlist_added_inline(locale))
        return


async def on_precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if not query:
        return
    payload_user = _parse_pro_payload(query.invoice_payload or "")
    if not payload_user:
        locale = "en" if ((query.from_user.language_code or "").lower().startswith("en")) else "ru"
        await query.answer(
            ok=False,
            error_message="Unknown product. Retry /upgrade" if locale == "en" else "Неизвестный продукт. Повторите /upgrade",
        )
        return
    await query.answer(ok=True)


async def on_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.successful_payment:
        return
    locale = locale_from_update(update)
    payment = update.message.successful_payment
    if payment.currency != "XTR":
        await update.message.reply_text(
            "Payment received, but this currency is not supported."
            if locale == "en"
            else "Платеж получен, но валюта не поддерживается."
        )
        return

    user_ctx = await resolve_user_context(update)
    payload_user = _parse_pro_payload(payment.invoice_payload or "")
    if payload_user and payload_user != user_ctx["user_id"]:
        log.warning("payment payload user mismatch payload=%s ctx=%s", payload_user, user_ctx["user_id"])

    external_id = payment.telegram_payment_charge_id or payment.provider_payment_charge_id or payment.invoice_payload
    payload = {
        "invoice_payload": payment.invoice_payload,
        "telegram_payment_charge_id": payment.telegram_payment_charge_id,
        "provider_payment_charge_id": payment.provider_payment_charge_id,
        "currency": payment.currency,
        "total_amount": payment.total_amount,
    }
    try:
        applied, renew_at = await asyncio.to_thread(
            activate_pro_subscription_sync,
            user_id=user_ctx["user_id"],
            provider="telegram_stars",
            external_id=external_id,
            source="telegram_stars",
            amount_cents=int(payment.total_amount),
            currency=payment.currency,
            payload=payload,
            email=None,
            event_type="stars_payment",
        )
    except Exception:
        log.exception("successful payment apply failed")
        await update.message.reply_text(
            (
                "Payment received, but activation did not complete automatically.\n"
                "Send “payment completed” and we will activate manually."
                if locale == "en"
                else "Платеж получен, но активация не завершилась автоматически.\n"
                "Напишите \"оплата прошла\" — активируем вручную."
            )
        )
        return

    if not applied:
        await update.message.reply_text(
            "This payment was already processed. PRO is active."
            if locale == "en"
            else "Платеж уже обработан ранее. PRO активен."
        )
        return

    renew_text = ""
    if isinstance(renew_at, datetime):
        renew_text = (
            f"\nActive until: {renew_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            if locale == "en"
            else f"\nДействует до: {renew_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        )
    await update.message.reply_text(
        (
            "Payment received. PRO activated.\n"
            f"Watchlist limit: {PRO_WATCHLIST_LIMIT}\n"
            "Email digest enabled."
            f"{renew_text}"
            if locale == "en"
            else "Оплата получена. PRO активирован.\n"
            f"Лимит watchlist: {PRO_WATCHLIST_LIMIT}\n"
            "Email-дайджест включен."
            f"{renew_text}"
        )
    )


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled bot error. update=%s", update, exc_info=context.error)


async def on_post_init(application: Application):
    try:
        await asyncio.to_thread(ensure_payment_schema_sync)
    except Exception:
        log.exception("payment schema ensure failed")
    await application.bot.set_my_description(
        (
            "Live probability shifts from Polymarket.\n"
            "Top movers, watchlist alerts, and signal-first inbox.\n"
            "FREE: 3 markets. PRO: 20 markets + email digest."
        ),
        language_code="en",
    )
    await application.bot.set_my_description(
        (
            "Live-сдвиги вероятностей Polymarket.\n"
            "Top movers, алерты watchlist и signal-first inbox.\n"
            "FREE: 3 рынка. PRO: 20 рынков + email-дайджест."
        ),
        language_code="ru",
    )
    await application.bot.set_my_short_description(
        "Live Polymarket signals: movers, watchlist alerts, inbox.",
        language_code="en",
    )
    await application.bot.set_my_short_description(
        "Live сигналы Polymarket: movers, watchlist-алерты, inbox.",
        language_code="ru",
    )
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Онбординг и профиль"),
            BotCommand("movers", "Top live movers"),
            BotCommand("watchlist", "Live изменения watchlist"),
            BotCommand("inbox", "Последние алерты"),
            BotCommand("plan", "Текущий план и лимиты"),
            BotCommand("help", "Все команды"),
        ],
        language_code="ru",
    )
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Onboarding and profile"),
            BotCommand("movers", "Top live movers"),
            BotCommand("watchlist", "Live watchlist changes"),
            BotCommand("inbox", "Latest alerts"),
            BotCommand("plan", "Current plan and limits"),
            BotCommand("help", "All commands"),
        ],
        language_code="en",
    )
    application.bot_data["push_task"] = application.create_task(push_loop(application))
    log.info("Bot commands menu configured")


async def on_post_shutdown(application: Application):
    push_task = application.bot_data.get("push_task")
    if push_task:
        push_task.cancel()
        try:
            await push_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.set_event_loop(asyncio.new_event_loop())
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(on_post_init)
        .post_shutdown(on_post_shutdown)
        .build()
    )
    app.add_error_handler(on_error)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("plan", cmd_plan))
    app.add_handler(CommandHandler("limits", cmd_limits))
    app.add_handler(CommandHandler("upgrade", cmd_upgrade))
    app.add_handler(CommandHandler("trade", cmd_trade))
    app.add_handler(CommandHandler("threshold", cmd_threshold))
    app.add_handler(CommandHandler("movers", cmd_movers))
    app.add_handler(CommandHandler("inbox", cmd_inbox10))
    app.add_handler(CommandHandler("inbox20", cmd_inbox20))
    app.add_handler(CommandHandler("watchlist", cmd_watchlist))
    app.add_handler(CommandHandler("watchlist_list", cmd_watchlist_list))
    app.add_handler(CommandHandler("watchlist_add", cmd_watchlist_add))
    app.add_handler(CommandHandler("watchlist_remove", cmd_watchlist_remove))
    app.add_handler(CommandHandler("admin_stats", cmd_admin_stats))
    app.add_handler(PreCheckoutQueryHandler(on_precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, on_successful_payment))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_menu_text))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    log.info("Starting bot polling for @polymarket_pulse_bot")
    app.run_polling(drop_pending_updates=True)
