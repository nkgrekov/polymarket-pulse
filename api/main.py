import os
import json
import secrets
import hashlib
import hmac
import html
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import quote, urlencode, urlparse

import psycopg
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel, EmailStr
from psycopg.types.json import Jsonb

load_dotenv()

PG_CONN = os.environ.get("PG_CONN", "")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000")
PULSE_BOT_URL = "https://t.me/polymarket_pulse_bot?start=email_backup"
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "Polymarket Pulse <onboarding@resend.dev>")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_PRICE_ID_MONTHLY = os.environ.get("STRIPE_PRICE_ID_MONTHLY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_SUCCESS_URL = os.environ.get("STRIPE_SUCCESS_URL", "")
STRIPE_CANCEL_URL = os.environ.get("STRIPE_CANCEL_URL", "")
PRO_SUBSCRIPTION_DAYS = int(os.environ.get("PRO_SUBSCRIPTION_DAYS", "30"))

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"

app = FastAPI(title="Polymarket Pulse Site API")

SEO_PAGES: dict[str, dict[str, dict[str, str]]] = {
    "analytics": {
        "en": {
            "title": "Polymarket Analytics - Live Probability Shifts That Matter | Polymarket Pulse",
            "description": "Polymarket analytics for real probability shifts: top movers, watchlist deltas, and signal-first Telegram alerts without dashboard overload.",
            "h1": "Polymarket analytics for people who act, not browse.",
            "intro": "See live repricing fast, filter out terminal noise, and move from discovery to action inside Telegram instead of babysitting a dashboard tab.",
            "k1": "Top movers from the current live repricing window",
            "k2": "Watchlist deltas filtered by your own threshold",
            "k3": "Telegram-first handoff from signal to action",
        },
        "ru": {
            "title": "Polymarket аналитика - live сигналы вероятностей | Polymarket Pulse",
            "description": "Аналитика Polymarket по реальным сдвигам вероятностей: top movers, watchlist-дельты и signal-first алерты в Telegram.",
            "h1": "Polymarket аналитика без перегруза дашбордами.",
            "intro": "Отслеживайте значимые движения рынка, а не шум терминала. Только live-дельты по делу.",
            "k1": "Top movers в последнем live-окне",
            "k2": "Персональный watchlist с порогом сигналов",
            "k3": "Telegram-first алерты для быстрой реакции",
        },
    },
    "dashboard": {
        "en": {
            "title": "Polymarket Dashboard Alternative - Fast Signals, Not Dashboard Overload",
            "description": "A Polymarket dashboard alternative built for action: live movers, watchlists, and clear Telegram alerts without terminal overload.",
            "h1": "A Polymarket dashboard alternative built for action.",
            "intro": "Skip the widget sprawl. Pulse gives you one fast surface for movers, watchlist deltas, and inbox signals so you can react instead of browsing.",
            "k1": "One feed for movers, inbox, and watchlist deltas",
            "k2": "Clear delta plus time-window context on every signal",
            "k3": "Freemium path into Pro without dashboard clutter",
        },
        "ru": {
            "title": "Альтернатива Polymarket dashboard - signal feed | Polymarket Pulse",
            "description": "Простая альтернатива dashboard для Polymarket: live movers, watchlist и actionable алерты.",
            "h1": "Альтернатива dashboard для обычного пользователя.",
            "intro": "Без сложного терминала. Открываете Telegram и сразу видите, что реально сдвинулось.",
            "k1": "Одна лента для movers, inbox и watchlist",
            "k2": "Понятные delta + временное окно у каждого сигнала",
            "k3": "Freemium-модель и апгрейд до Pro",
        },
    },
    "signals": {
        "en": {
            "title": "Polymarket Signals - Low-Noise Live Alerts in Telegram | Polymarket Pulse",
            "description": "Get Polymarket signals based on real probability shifts. Set your threshold, cut the noise, and receive clean live alerts in Telegram.",
            "h1": "Live signals with an actual noise filter.",
            "intro": "Most signal feeds spam every twitch. Pulse filters by threshold, deduplicates repeated moves, and stays quiet when the market is flat.",
            "k1": "Per-user threshold in Telegram settings",
            "k2": "Deduplicated alerts instead of repeat spam",
            "k3": "Fast activation path from /start to first signal",
        },
        "ru": {
            "title": "Polymarket Signals - live алерты в Telegram | Polymarket Pulse",
            "description": "Получайте сигналы Polymarket по реальным сдвигам вероятностей. Настройте порог и получайте чистые алерты в Telegram.",
            "h1": "Сигналы, а не шум.",
            "intro": "Выставляете порог, выбираете рынки и получаете только значимые движения в inbox.",
            "k1": "Персональный threshold в настройках бота",
            "k2": "Дедупликация алертов и дневные free-лимиты",
            "k3": "Онбординг меньше чем за 60 секунд",
        },
    },
    "telegram-bot": {
        "en": {
            "title": "Polymarket Pulse Telegram Bot - Live Movers, Watchlists, and Signals",
            "description": "Use the Polymarket Pulse Telegram bot for top movers, watchlist tracking, and low-noise probability alerts built for fast action on Polymarket.",
            "h1": "Polymarket Pulse, as a Telegram bot.",
            "intro": "If you are looking for a Polymarket Telegram bot, this is the Pulse flow: open Telegram, add one live market, and get a useful signal before dashboard scanning catches up.",
            "k1": "One-tap path from /start to live market tracking",
            "k2": "Clear movers, inbox, and watchlist flow in one bot",
            "k3": "Signal quality over noise with threshold and dedup",
        },
        "ru": {
            "title": "Polymarket Telegram bot - live movers и watchlist алерты",
            "description": "Используйте Telegram-бота Polymarket Pulse для top movers, отслеживания watchlist и live алертов вероятности.",
            "h1": "Telegram-бот для action-first сигналов Polymarket.",
            "intro": "Большинство решений заточено под дашборды. Pulse заточен под действие: /start -> один рынок в watchlist -> первый live-сигнал меньше чем за 60 секунд.",
            "k1": "Action вместо перегруза dashboard-ами",
            "k2": "Активация за 60 секунд",
            "k3": "Качество сигнала: threshold + дедуп",
        },
    },
    "top-movers": {
        "en": {
            "title": "Polymarket Top Movers - Fastest Live Probability Shifts",
            "description": "See Polymarket top movers by probability change, catch the fastest repricing, and push the move straight into Telegram.",
            "h1": "Catch the fastest movers before the tab crowd does.",
            "intro": "When a live window wakes up, Pulse surfaces the move fast. When it stays flat, fallback logic expands the view instead of faking activity.",
            "k1": "Latest repricing window ranked by meaningful delta",
            "k2": "Adaptive fallback when the short window is quiet",
            "k3": "One-tap move from mover to watchlist tracking",
        },
        "ru": {
            "title": "Polymarket Top Movers - live сдвиги вероятностей",
            "description": "Смотрите top movers в Polymarket по изменению вероятности и отслеживайте momentum через Telegram.",
            "h1": "Top movers в один тап.",
            "intro": "Если короткое окно плоское, fallback логика показывает самые сильные движения за 1 час.",
            "k1": "Movers по последнему окну с дельтой",
            "k2": "Fallback на 1h при плоском рынке",
            "k3": "Прямой сценарий добавления в watchlist",
        },
    },
    "watchlist-alerts": {
        "en": {
            "title": "Polymarket Watchlist Alerts - Low-Noise Market Tracking in Telegram",
            "description": "Build a Polymarket watchlist, tune your threshold, and get low-noise Telegram alerts when selected markets actually move.",
            "h1": "Watchlist alerts for markets you actually care about.",
            "intro": "Pin the markets that matter, set your own threshold, and let Telegram surface only the repricing worth reacting to.",
            "k1": "Free plan: 3 markets and 20 alerts per day",
            "k2": "Pro plan: 20 markets, unlimited alerts, email digest",
            "k3": "Clear /plan and /upgrade path inside the bot",
        },
        "ru": {
            "title": "Polymarket Watchlist Alerts - кастомное отслеживание рынков",
            "description": "Соберите свой watchlist Polymarket и получайте кастомные Telegram-алерты, когда выбранные рынки двигаются.",
            "h1": "Watchlist-алерты, которые помогают действовать.",
            "intro": "Добавьте важные для вас рынки и настройте чувствительность персональным threshold.",
            "k1": "Free: 3 рынка и 20 алертов в день",
            "k2": "Pro: 20 рынков в watchlist, безлимит алертов и email-дайджест",
            "k3": "Понятный сценарий /plan и /upgrade в Telegram",
        },
    },
}

SEO_PAGE_FAQ: dict[str, dict[str, list[dict[str, str]]]] = {
    "analytics": {
        "en": [
            {
                "q": "What makes this different from a normal Polymarket dashboard?",
                "a": "Polymarket Pulse prioritizes live repricing and actionability. Instead of asking you to scan charts manually, it surfaces movers, watchlist deltas, and alert-ready changes directly in Telegram.",
            },
            {
                "q": "Do I need to connect a wallet to use the analytics layer?",
                "a": "No. The analytics and signal layer works without wallet connection. Wallet and execution flows live in the separate Trader product.",
            },
        ],
        "ru": [
            {
                "q": "Чем это отличается от обычного Polymarket dashboard?",
                "a": "Polymarket Pulse делает упор на live-переоценку и actionability. Вместо того чтобы заставлять вас вручную сканировать графики, он приносит movers, watchlist-дельты и алерты прямо в Telegram.",
            },
            {
                "q": "Нужно ли подключать кошелёк для аналитического слоя?",
                "a": "Нет. Analytics и signal-слой работают без кошелька. Wallet и execution живут в отдельном Trader-продукте.",
            },
        ],
    },
    "dashboard": {
        "en": [
            {
                "q": "Why use this instead of a dashboard tab that shows more widgets?",
                "a": "Because most users do not need more widgets. They need one clear answer: what moved, by how much, and whether it matters right now.",
            },
            {
                "q": "Can I still track specific markets?",
                "a": "Yes. The watchlist flow lets you pin markets that matter and only surface them when their move clears your threshold.",
            },
        ],
        "ru": [
            {
                "q": "Зачем это вместо dashboard-а с большим количеством виджетов?",
                "a": "Потому что большинству пользователей не нужны новые виджеты. Им нужен один ясный ответ: что сдвинулось, насколько и важно ли это прямо сейчас.",
            },
            {
                "q": "Можно ли всё равно отслеживать конкретные рынки?",
                "a": "Да. Watchlist позволяет закрепить важные рынки и показывать их только когда движение проходит ваш порог.",
            },
        ],
    },
    "signals": {
        "en": [
            {
                "q": "How do Polymarket signals stay low-noise?",
                "a": "Signals are filtered by user threshold, deduplicated across repeated windows, and intentionally return quiet states when the market is flat.",
            },
            {
                "q": "What happens if the short window shows no meaningful move?",
                "a": "Pulse falls back to a wider window instead of forcing fake activity. If nothing meaningful moved, it stays quiet on purpose.",
            },
        ],
        "ru": [
            {
                "q": "Как сигналы Polymarket остаются низкошумными?",
                "a": "Сигналы фильтруются персональным threshold, дедуплицируются между повторяющимися окнами и специально показывают тихое состояние, если рынок плоский.",
            },
            {
                "q": "Что происходит, если в коротком окне нет значимого движения?",
                "a": "Pulse делает fallback на более широкое окно, а не выдумывает активность. Если ничего важного не сдвинулось, бот специально молчит.",
            },
        ],
    },
    "telegram-bot": {
        "en": [
            {
                "q": "How fast can a new user get to first value?",
                "a": "The intended path is simple: open the bot, add one live market, and get your first useful signal in under 60 seconds.",
            },
            {
                "q": "Is Polymarket Pulse a Telegram bot for Polymarket?",
                "a": "Yes. Polymarket Pulse is a Telegram-first signal product for Polymarket. It focuses on top movers, watchlist tracking, and low-noise alerts rather than dashboard overload.",
            },
            {
                "q": "Why do /movers or /inbox sometimes show zero?",
                "a": "That is intentional. If current repricing is flat, Pulse falls back to a wider window and stays quiet if the market still is not moving.",
            },
        ],
        "ru": [
            {
                "q": "Как быстро новый пользователь получает первую ценность?",
                "a": "Сценарий простой: открыть бота, добавить один live-рынок и получить первый полезный сигнал меньше чем за 60 секунд.",
            },
            {
                "q": "Почему /movers или /inbox иногда показывают ноль?",
                "a": "Это намеренно. Если текущий repricing плоский, Pulse делает fallback на более широкое окно и молчит, если рынок всё ещё не движется.",
            },
        ],
    },
    "top-movers": {
        "en": [
            {
                "q": "Are top movers ranked only by raw delta?",
                "a": "The public movers surface is delta-first, but the broader product also uses liquidity and live coverage logic for better candidate quality and watchlist suggestions.",
            },
            {
                "q": "Can I add a mover directly to my watchlist?",
                "a": "Yes. The bot supports one-tap add and replacement flows so live movers can become watchlist markets immediately.",
            },
        ],
        "ru": [
            {
                "q": "Ранжируются ли top movers только по сырой дельте?",
                "a": "Публичная movers-поверхность delta-first, но сам продукт также использует ликвидность и live-coverage логику для лучшего качества кандидатов и watchlist-подсказок.",
            },
            {
                "q": "Можно ли добавить mover прямо в watchlist?",
                "a": "Да. Бот поддерживает сценарий one-tap add и replacement, так что live movers можно сразу превращать в watchlist-рынки.",
            },
        ],
    },
    "watchlist-alerts": {
        "en": [
            {
                "q": "What does the free plan include?",
                "a": "Free currently includes 3 watchlist markets and 20 alerts per day. Pro extends that to 20 markets, unlimited alerts, and email digest.",
            },
            {
                "q": "Why might a watchlist market stay quiet after I add it?",
                "a": "The market may be closed, may not have current bid/ask quotes, or may not have cleared your threshold in the latest window.",
            },
        ],
        "ru": [
            {
                "q": "Что входит в free-план?",
                "a": "Free сейчас включает 3 рынка в watchlist и 20 алертов в день. Pro расширяет это до 20 рынков, безлимитных алертов и email-дайджеста.",
            },
            {
                "q": "Почему рынок в watchlist может молчать после добавления?",
                "a": "Рынок может быть закрыт, может не иметь текущих bid/ask котировок или не пройти ваш threshold в последнем окне.",
            },
        ],
    },
}

SEO_PAGE_LINKS: dict[str, list[str]] = {
    "analytics": ["signals", "top-movers", "telegram-bot", "watchlist-alerts"],
    "dashboard": ["analytics", "telegram-bot", "signals", "watchlist-alerts"],
    "signals": ["telegram-bot", "watchlist-alerts", "top-movers", "analytics"],
    "telegram-bot": ["signals", "top-movers", "watchlist-alerts", "analytics"],
    "top-movers": ["watchlist-alerts", "telegram-bot", "signals", "analytics"],
    "watchlist-alerts": ["signals", "telegram-bot", "top-movers", "analytics"],
}

SEO_PAGE_CTA_NOTE: dict[str, dict[str, str]] = {
    "dashboard": {
        "en": "Use the bot for the move itself, not for another dashboard tab that waits to be ignored.",
        "ru": "Используйте бота ради самого движения, а не ради ещё одной dashboard-вкладки, которую легко забыть.",
    },
    "analytics": {
        "en": "Open the bot, pin one market, and see whether the latest repricing actually deserves attention.",
        "ru": "Откройте бота, закрепите один рынок и сразу увидите, заслуживает ли последнее движение внимания.",
    },
    "signals": {
        "en": "Set a threshold, keep noise low, and let Telegram surface only the repricing that matters.",
        "ru": "Выставьте threshold, уберите шум и получайте в Telegram только действительно значимый repricing.",
    },
    "telegram-bot": {
        "en": "No wallet and no dashboard required. Start with movers, add one live market, and get to first value fast.",
        "ru": "Не нужен ни кошелёк, ни dashboard. Начните с movers, добавьте один live-рынок и быстро получите первую ценность.",
    },
    "top-movers": {
        "en": "When the short window wakes up, the fastest route to action is one tap into the bot.",
        "ru": "Когда короткое окно оживает, самый быстрый путь к действию — один тап в бота.",
    },
    "watchlist-alerts": {
        "en": "Use Telegram for action now, keep email as backup for digest and launch updates.",
        "ru": "Используйте Telegram для действий сейчас, а email оставьте как backup для дайджеста и обновлений.",
    },
}


class WaitlistRequest(BaseModel):
    email: EmailStr
    source: str = "site"
    details: dict | None = None


class SiteEventRequest(BaseModel):
    event_type: str
    source: str = "site"
    details: dict | None = None


class StripeCheckoutRequest(BaseModel):
    email: EmailStr
    user_id: str | None = None
    source: str = "site"
    lang: Literal["ru", "en"] | None = None


class TraderAlphaRequest(BaseModel):
    email: EmailStr
    user_id: str | None = None
    telegram_id: int | None = None
    chat_id: int | None = None
    source: str = "site"
    details: dict | None = None


class TraderSignerSubmitRequest(BaseModel):
    token: str
    signed_payload: str


HOT_PREVIEW_MAX_FRESHNESS_SECONDS = int(os.environ.get("HOT_PREVIEW_MAX_FRESHNESS_SECONDS", "120"))
HOT_PREVIEW_MIN_LIQUIDITY = float(os.environ.get("HOT_PREVIEW_MIN_LIQUIDITY", "1000"))
HOT_PREVIEW_MAX_SPREAD = float(os.environ.get("HOT_PREVIEW_MAX_SPREAD", "0.25"))


SQL_HOT_LIVE_MOVERS_PREVIEW = """
with hot as (
  select
    r.market_id,
    r.question,
    r.slug,
    q.quote_ts as last_bucket,
    prev.ts_bucket as prev_bucket,
    q.mid_yes as yes_mid_now,
    prev.mid_yes_prev as yes_mid_prev,
    (q.mid_yes - prev.mid_yes_prev)::double precision as delta_yes,
    m1.delta_mid::double precision as delta_1m,
    coalesce(q.liquidity, 0)::double precision as liquidity,
    q.spread::double precision as spread
  from public.hot_market_registry_latest r
  join public.hot_market_quotes_latest q using (market_id)
  left join public.hot_top_movers_1m m1 using (market_id)
  join lateral (
    with per_bucket as (
      select
        ms.ts_bucket,
        max(coalesce(((ms.yes_bid + ms.yes_ask) / 2.0), ms.yes_bid, ms.yes_ask))::double precision as mid_yes_prev
      from public.market_snapshots ms
      where ms.market_id = r.market_id
        and (ms.yes_bid is not null or ms.yes_ask is not null)
      group by ms.ts_bucket
    )
    select ts_bucket, mid_yes_prev
    from per_bucket
    where mid_yes_prev is not null
      and ts_bucket <= q.quote_ts - interval '4 minutes'
    order by ts_bucket desc
    limit 1
  ) prev on true
  where coalesce(r.status, 'active') = 'active'
    and q.has_two_sided_quote
    and q.mid_yes is not null
    and q.freshness_seconds <= %s
    and coalesce(q.liquidity, 0) >= %s
    and coalesce(q.spread, 0) <= %s
)
select
  market_id,
  question,
  slug,
  last_bucket,
  prev_bucket,
  yes_mid_now,
  yes_mid_prev,
  delta_yes,
  delta_1m
from hot
order by abs(delta_yes) desc nulls last, liquidity desc nulls last
limit %s;
"""

SQL_LIVE_MOVERS_PREVIEW_LEGACY = """
select
  tm.market_id,
  coalesce(tm.question, m.question) as question,
  m.slug,
  tm.last_bucket,
  tm.prev_bucket,
  tm.yes_mid_now,
  tm.yes_mid_prev,
  tm.delta_yes
from public.top_movers_latest tm
join public.markets m on m.market_id = tm.market_id
where tm.yes_mid_now is not null
  and tm.yes_mid_prev is not null
order by abs(delta_yes) desc nulls last
limit %s;
"""

SQL_LIVE_SPARKLINE_POINTS = """
with per_bucket as (
  select
    ms.market_id,
    ms.ts_bucket,
    max(coalesce(((ms.yes_bid + ms.yes_ask) / 2.0), ms.yes_bid, ms.yes_ask))::double precision as yes_mid
  from public.market_snapshots ms
  where ms.market_id = any(%s::text[])
    and (ms.yes_bid is not null or ms.yes_ask is not null)
  group by ms.market_id, ms.ts_bucket
),
ranked as (
  select
    market_id,
    ts_bucket,
    yes_mid as mid,
    row_number() over (partition by market_id order by ts_bucket desc) as rn
  from per_bucket
  where yes_mid is not null
)
select
  market_id,
  ts_bucket,
  mid
from ranked
where rn <= %s
order by market_id, ts_bucket asc;
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

SQL_ENSURE_TRADE_ALPHA_WAITLIST = """
create schema if not exists trade;

create table if not exists trade.alpha_waitlist (
  id bigserial primary key,
  email text not null unique,
  user_id uuid references app.users(id) on delete set null,
  telegram_id bigint,
  chat_id bigint,
  source text not null default 'site',
  status text not null default 'new',
  use_case text not null default 'execution_alpha',
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (source in ('site', 'pulse_bot', 'telegram_bot', 'x', 'threads', 'manual')),
  check (status in ('new', 'review', 'approved', 'declined'))
);
"""

SQL_TRADE_ALPHA_WAITLIST_UPSERT = """
insert into trade.alpha_waitlist (
  email,
  user_id,
  telegram_id,
  chat_id,
  source,
  status,
  use_case,
  details
)
values (%s, %s::uuid, %s, %s, %s, 'new', 'execution_alpha', %s)
on conflict (email) do update
set user_id = coalesce(trade.alpha_waitlist.user_id, excluded.user_id),
    telegram_id = coalesce(trade.alpha_waitlist.telegram_id, excluded.telegram_id),
    chat_id = coalesce(trade.alpha_waitlist.chat_id, excluded.chat_id),
    source = excluded.source,
    details = trade.alpha_waitlist.details || excluded.details,
    updated_at = now()
returning id;
"""

SQL_SIGNER_SESSION_LOOKUP = """
select
  ss.id,
  ss.account_id,
  a.user_id,
  ss.wallet_link_id,
  ss.session_token,
  ss.status,
  ss.challenge_text,
  ss.signed_payload,
  ss.verified_at,
  ss.expires_at,
  ss.created_at,
  wl.wallet_address,
  wl.status as wallet_status,
  wl.signer_kind
from trade.signer_sessions ss
join trade.accounts a on a.id = ss.account_id
join trade.wallet_links wl on wl.id = ss.wallet_link_id
where ss.session_token = %s
limit 1;
"""

SQL_SIGNER_SESSION_OPEN = """
update trade.signer_sessions
set status = 'opened',
    updated_at = now()
where id = %s
  and status = 'new'
returning id;
"""

SQL_SIGNER_SESSION_SUBMIT = """
update trade.signer_sessions
set status = case when status = 'verified' then 'verified' else 'signed' end,
    signed_payload = %s::jsonb,
    updated_at = now()
where id = %s
returning id, status, expires_at, verified_at;
"""

SQL_SIGNER_ACTIVITY = """
insert into trade.activity_events (
  user_id,
  account_id,
  event_type,
  source,
  market_id,
  details
) values (%s::uuid, %s, %s, 'site', null, %s::jsonb);
"""


def detect_lang(request: Request, explicit: str | None = None) -> Literal["ru", "en"]:
    if explicit in {"ru", "en"}:
        return explicit

    q_lang = (request.query_params.get("lang") or "").strip().lower()
    if q_lang in {"ru", "en"}:
        return q_lang

    country_headers = [
        "cf-ipcountry",
        "x-vercel-ip-country",
        "x-geo-country",
        "x-country-code",
    ]
    for h in country_headers:
        country = (request.headers.get(h) or "").strip().upper()
        if country == "RU":
            return "ru"
        if country:
            return "en"

    accept_lang = (request.headers.get("accept-language") or "").lower()
    if "ru" in accept_lang:
        return "ru"
    return "en"


def detect_site_lang(request: Request) -> Literal["ru", "en"]:
    q_lang = (request.query_params.get("lang") or "").strip().lower()
    if q_lang == "ru":
        return "ru"
    return "en"


def load_page(base_name: str, lang: Literal["ru", "en"]) -> str:
    localized = WEB_DIR / f"{base_name}.{lang}.html"
    if localized.exists():
        return localized.read_text(encoding="utf-8")
    fallback = WEB_DIR / f"{base_name}.html"
    return fallback.read_text(encoding="utf-8")


def base_url() -> str:
    return APP_BASE_URL.rstrip("/")


def render_seo_page(slug: str, lang: Literal["ru", "en"]) -> str:
    page = SEO_PAGES[slug][lang]
    faq_items = SEO_PAGE_FAQ.get(slug, {}).get(lang, [])
    related_page_slugs = SEO_PAGE_LINKS.get(slug, [name for name in SEO_PAGES if name != slug])
    page_label = slug.replace("-", " ").upper()
    cta_text = "Open Telegram Bot" if lang == "en" else "Открыть Telegram-бота"
    cta_guide_text = "See the bot flow" if lang == "en" else "Как это работает?"
    cta_backup_link_text = "Keep email as backup" if lang == "en" else "Email как backup"
    back_text = "Back to homepage" if lang == "en" else "На главную"
    links_head = "Related pages" if lang == "en" else "Связанные страницы"
    faq_head = "Common questions" if lang == "en" else "Частые вопросы"
    preview_head = "Preview surfaces" if lang == "en" else "Ключевые экраны"
    cta_note = SEO_PAGE_CTA_NOTE.get(slug, {}).get(
        lang,
        "Open the bot first. Add markets second. Let the signal layer tell you when to care."
        if lang == "en"
        else "Сначала откройте бота. Потом добавьте рынки. Пусть signal-слой сам подскажет, когда пора реагировать.",
    )
    cta_backup_note = (
        "Keep email only as a backup for digest and launch updates. Telegram stays the primary live loop."
        if lang == "en"
        else "Оставляйте email только как backup для дайджеста и обновлений. Telegram остаётся основным live-каналом."
    )
    preview_copy_1 = (
        "Catch the fastest repricing in the current live window."
        if lang == "en"
        else "Показывает самые быстрые переоценки в текущем live-окне."
    )
    preview_copy_2 = (
        "Tune sensitivity per user and keep your feed clean."
        if lang == "en"
        else "Настраивает чувствительность под пользователя и убирает шум."
    )
    preview_copy_3 = (
        "Telegram delivery loop with clear time-window context."
        if lang == "en"
        else "Telegram-доставка с понятным контекстом временного окна."
    )
    stat_1_label = "Signal delay" if lang == "en" else "Задержка сигнала"
    stat_1_value = "< 12 sec" if lang == "en" else "< 12 сек"
    stat_1_copy = "market move -> bot inbox" if lang == "en" else "движение рынка -> inbox бота"
    stat_2_label = "Activation path" if lang == "en" else "Путь активации"
    stat_2_value = "1 tap" if lang == "en" else "1 тап"
    stat_2_copy = "landing -> /start -> watchlist" if lang == "en" else "лендинг -> /start -> watchlist"
    stat_3_label = "Live scope" if lang == "en" else "Live-охват"
    stat_3_value = "200 markets" if lang == "en" else "200 рынков"
    stat_3_copy = "active-only balanced universe" if lang == "en" else "active-only сбалансированный universe"
    badge_1 = "4.8/5 trader score" if lang == "en" else "4.8/5 оценка трейдеров"
    badge_3 = "Telegram-first flow" if lang == "en" else "Telegram-first сценарий"
    screen_label = "Screen" if lang == "en" else "Экран"
    page_view_js_lang = "en" if lang == "en" else "ru"
    base = base_url()
    canonical_url = f"{base}/{slug}"
    robots_meta = "index,follow" if lang == "en" else "noindex,follow"
    og_image_url = f"{base}/og-card.svg"
    page_schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "@id": canonical_url,
            "url": canonical_url,
            "name": page["title"],
            "description": page["description"],
            "inLanguage": "en-US" if lang == "en" else "ru-RU",
            "isPartOf": {"@type": "WebSite", "url": base, "name": "Polymarket Pulse"},
            "about": {
                "@type": "Thing",
                "name": "Polymarket Pulse Telegram bot for live analytics and signals"
                if slug == "telegram-bot" and lang == "en"
                else "Polymarket live analytics and Telegram signals"
            },
        },
        ensure_ascii=False,
    )
    faq_schema = ""
    if faq_items:
        faq_schema = json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
                    }
                    for item in faq_items
                ],
            },
            ensure_ascii=False,
        )
    faq_schema_tag = f'<script type="application/ld+json">{faq_schema}</script>' if faq_schema else ""
    faq_cards = "".join(
        f'<article class="faq-card"><h3 class="faq-question">{html.escape(item["q"])}</h3><p class="faq-answer">{html.escape(item["a"])}</p></article>'
        for item in faq_items
    )
    faq_block = (
        f"""
    <section class="links-wrap reveal delay-4">
      <p class="links-title">{faq_head}</p>
      <div class="faq-grid">
        {faq_cards}
      </div>
    </section>
"""
        if faq_items
        else ""
    )

    links = "".join(
        f'<a href="/{name}">{SEO_PAGES[name]["en"]["h1"]}</a>'
        for name in related_page_slugs
        if name in SEO_PAGES and name != slug and name != "trader-bot"
    )
    guide_href = f"/how-it-works?placement=seo_{slug}_guide"
    backup_href = f"/?placement=seo_{slug}_backup#waitlist-form"
    guide_cta = f'<a id="guide-link" class="cta-secondary" href="{guide_href}">{cta_guide_text}</a>'
    backup_cta = f'<a id="backup-link" class="cta-backup-link" href="{backup_href}">{cta_backup_link_text}</a>'
    compare_head = "Why Pulse instead of another dashboard" if lang == "en" else "Почему Pulse, а не ещё один dashboard"
    compare_title = (
        "Normal-user speed beats terminal cosplay."
        if lang == "en"
        else "Скорость для нормального пользователя важнее терминального косплея."
    )
    compare_1 = (
        "<strong>Dashboard tools</strong> make you search for a move. <strong>Pulse</strong> pushes the move into Telegram."
        if lang == "en"
        else "<strong>Dashboard-инструменты</strong> заставляют вас искать движение. <strong>Pulse</strong> приносит его прямо в Telegram."
    )
    compare_2 = (
        "<strong>Noisy alert feeds</strong> force you to second-guess every ping. <strong>Pulse</strong> starts from actual repricing and honest quiet states."
        if lang == "en"
        else "<strong>Шумные алерты</strong> заставляют сомневаться в каждом пинге. <strong>Pulse</strong> стартует с реального repricing и честных quiet-state."
    )
    compare_3 = (
        "<strong>Our edge</strong>: signal first, watchlist second, action only when the move is worth caring about."
        if lang == "en"
        else "<strong>Наш угол атаки</strong>: сначала сигнал, потом watchlist, а действие только когда движение реально заслуживает внимания."
    )
    compare_block = (
        f"""
    <section id="seo-bridge" class="links-wrap reveal delay-4">
      <p class="links-title">{compare_head}</p>
      <div class="preview-grid">
        <article class="preview-card">
          <p class="preview-kicker">01</p>
          <h3 class="preview-title">{compare_title}</h3>
          <p class="preview-copy">{compare_1}</p>
        </article>
        <article class="preview-card">
          <p class="preview-kicker">02</p>
          <h3 class="preview-title">Trust the feed</h3>
          <p class="preview-copy">{compare_2}</p>
        </article>
        <article class="preview-card">
          <p class="preview-kicker">03</p>
          <h3 class="preview-title">Signal-first stack</h3>
          <p class="preview-copy">{compare_3}</p>
        </article>
      </div>
    </section>
"""
        if slug == "telegram-bot"
        else ""
    )
    bridge_block = (
        """
    <section class="links-wrap reveal delay-4">
      <p class="links-title">FASTEST NEXT STEP</p>
      <div class="preview-grid">
        <article class="preview-card">
          <p class="preview-kicker">01</p>
          <h3 class="preview-title">Open the bot now</h3>
          <p class="preview-copy">Do not keep reading if the intent is clear. Open Telegram, hit /start, and add one live market before the move becomes old news.</p>
        </article>
        <article class="preview-card">
          <p class="preview-kicker">02</p>
          <h3 class="preview-title">What happens next</h3>
          <p class="preview-copy">You land in movers, add one market, and use Watchlist or Inbox to decide whether the repricing actually matters.</p>
        </article>
        <article class="preview-card">
          <p class="preview-kicker">03</p>
          <h3 class="preview-title">Backup, not a detour</h3>
          <p class="preview-copy">Email stays optional and secondary. Telegram is still the shortest path to first value.</p>
        </article>
      </div>
      <div class="cta-row" style="margin-top:14px;">
        <a id="tg-link-bridge" class="cta" href="https://t.me/polymarket_pulse_bot?start=seo_telegram-bot_bridge_en" target="_blank" rel="noopener noreferrer">Open Telegram Bot -></a>
        <a id="guide-link-bridge" class="cta-secondary" href="/how-it-works?placement=seo_telegram-bot_bridge_guide">See the bot flow</a>
      </div>
      <p class="cta-note">The goal here is not another dashboard. It is one clean move from search intent to a live market in Telegram.</p>
    </section>
"""
        if slug == "telegram-bot" and lang == "en"
        else ""
    )

    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{page["title"]}</title>
  <meta name="description" content="{page["description"]}" />
  <meta name="robots" content="{robots_meta}" />
  <meta property="og:title" content="{page["title"]}" />
  <meta property="og:description" content="{page["description"]}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{canonical_url}" />
  <meta property="og:image" content="{og_image_url}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{page["title"]}" />
  <meta name="twitter:description" content="{page["description"]}" />
  <meta name="twitter:image" content="{og_image_url}" />
  <meta name="twitter:url" content="{canonical_url}" />
  <link rel="canonical" href="{canonical_url}" />
  <link rel="icon" type="image/svg+xml" sizes="any" href="/favicon.svg" />
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
  <link rel="icon" type="image/png" sizes="48x48" href="/favicon-48x48.png" />
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
  <link rel="shortcut icon" href="/favicon.ico" />
  <script type="application/ld+json">{page_schema}</script>
  {faq_schema_tag}
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-J901VRQH4G"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-J901VRQH4G');
  </script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root {{
      --bg: #0d0f0e;
      --bg-2: #0a0c0b;
      --panel: #131714;
      --line: #1e2520;
      --line-soft: #2a332b;
      --text: #e8ede9;
      --muted: #8fa88f;
      --muted-soft: #6b7a6e;
      --accent: #00ff88;
      --negative: #ff4444;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
      background:
        radial-gradient(1200px 800px at 85% -20%, rgba(0, 255, 136, 0.08) 0%, transparent 60%),
        radial-gradient(900px 600px at -10% 10%, rgba(0, 255, 136, 0.05) 0%, transparent 58%),
        linear-gradient(180deg, var(--bg-2) 0%, var(--bg) 60%, var(--bg-2) 100%);
      color: var(--text);
      min-height: 100vh;
      overflow-x: hidden;
    }}
    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
      background-size: 28px 28px;
      opacity: 0.16;
    }}
    @keyframes rise-in {{
      from {{ opacity: 0; transform: translateY(14px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .reveal {{
      opacity: 0;
      animation: rise-in 0.28s ease forwards;
    }}
    .reveal.delay-1 {{ animation-delay: 0.08s; }}
    .reveal.delay-2 {{ animation-delay: 0.16s; }}
    .reveal.delay-3 {{ animation-delay: 0.24s; }}
    .reveal.delay-4 {{ animation-delay: 0.32s; }}
    body.ready .reveal {{ opacity: 1; }}
    .wrap {{
      width: min(1080px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 48px;
      position: relative;
      z-index: 1;
    }}
    .top {{
      display:flex; justify-content:space-between; align-items:center; gap: 12px;
      font-family:"JetBrains Mono", monospace; font-size:12px; color: var(--muted);
    }}
    .top a {{
      color: var(--muted);
      text-decoration: none;
      border:1px solid var(--line-soft);
      border-radius:999px;
      padding:6px 10px;
    }}
    .top a:hover, .top a:focus-visible {{ border-color: var(--accent); color: var(--text); outline: none; }}
    .card {{
      margin-top: 16px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 24px;
      box-shadow: 0 24px 72px rgba(0, 0, 0, 0.42), inset 0 0 0 1px rgba(255, 255, 255, 0.015);
    }}
    .badge-row {{
      margin-bottom: 14px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      color: var(--muted);
      letter-spacing: 0.07em;
      text-transform: uppercase;
    }}
    .badge {{
      border: 1px solid var(--line-soft);
      border-radius: 999px;
      padding: 6px 10px;
      background: rgba(19, 23, 20, 0.72);
    }}
    .badge.active {{
      border-color: rgba(0, 255, 136, 0.45);
      color: var(--text);
      box-shadow: 0 0 0 1px rgba(0, 255, 136, 0.18) inset;
    }}
    h1 {{
      margin: 0;
      line-height: 0.95;
      font-size: clamp(36px, 7vw, 72px);
      letter-spacing: -0.02em;
      text-transform: uppercase;
    }}
    .intro {{
      margin: 12px 0 0;
      color: var(--muted);
      font-size: clamp(15px, 2vw, 20px);
      line-height: 1.45;
      font-family: "JetBrains Mono", monospace;
    }}
    .feature-rows {{
      margin-top: 16px;
      display: grid;
      gap: 10px;
    }}
    .feature-row {{
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #131714;
      padding: 11px 12px;
      font-family: "JetBrains Mono", monospace;
      color: var(--muted);
      font-size: 13px;
    }}
    .stats {{
      margin-top: 16px;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 11px 12px;
      background: rgba(19, 23, 20, 0.88);
    }}
    .stat-label {{
      margin: 0;
      color: var(--muted-soft);
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    .stat-value {{
      margin: 6px 0 0;
      font-size: clamp(19px, 3vw, 27px);
      line-height: 1;
      letter-spacing: -0.02em;
    }}
    .stat-copy {{
      margin: 6px 0 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.4;
    }}
    .cta-row {{
      margin-top: 18px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
    }}
    .cta {{
      display:inline-flex; align-items:center; justify-content:center;
      min-height: 48px; padding: 10px 16px; border-radius: 12px; text-decoration: none;
      font-family: "JetBrains Mono", monospace; font-weight: 700;
      color: var(--bg-2); background: linear-gradient(180deg, #00ff88 0%, #00d874 100%);
      border: 1px solid var(--accent);
    }}
    .cta-secondary {{
      display:inline-flex; align-items:center; justify-content:center;
      min-height: 48px; padding: 10px 16px; border-radius: 12px; text-decoration: none;
      font-family: "JetBrains Mono", monospace; font-weight: 700;
      color: var(--text); background: #131714;
      border: 1px solid var(--line-soft);
    }}
    .cta-secondary:hover, .cta-secondary:focus-visible {{ border-color: var(--accent); outline: none; }}
    .cta-trust {{
      margin-top: 10px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .trust-pill {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      background: #131714;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      line-height: 1;
    }}
    .cta-note {{
      margin: 10px 0 0;
      color: var(--muted-soft);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.55;
    }}
    .cta-backup-note {{
      margin: 8px 0 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.5;
    }}
    .cta-backup-link-wrap {{
      margin: 8px 0 0;
    }}
    .cta-backup-link {{
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.5;
      text-decoration: underline;
      text-underline-offset: 2px;
    }}
    .cta-backup-link:hover, .cta-backup-link:focus-visible {{
      color: var(--text);
      outline: none;
    }}
    .preview {{
      margin-top: 16px;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      background: #131714;
    }}
    .preview-grid {{
      margin-top: 10px;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .preview-card {{
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      background: #131714;
      transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .preview-card:hover {{
      transform: translateY(-2px);
      border-color: rgba(0, 255, 136, 0.36);
    }}
    .preview-kicker {{
      margin: 0;
      color: var(--muted-soft);
      font-family: "JetBrains Mono", monospace;
      font-size: 11px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    .preview-title {{
      margin: 8px 0 0;
      font-size: 17px;
      line-height: 1.15;
      letter-spacing: -0.01em;
    }}
    .preview-copy {{
      margin: 8px 0 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.45;
    }}
    .preview-bar {{
      margin-top: 10px;
      height: 7px;
      border-radius: 999px;
      background: #0c0f0d;
      border: 1px solid var(--line);
      overflow: hidden;
      position: relative;
    }}
    .preview-bar > span {{
      position: absolute;
      inset: 0 auto 0 0;
      width: var(--w, 50%);
      border-radius: 999px;
      background: linear-gradient(90deg, #00cc6f 0%, #00ff88 100%);
    }}
    .preview-bar.down > span {{
      background: linear-gradient(90deg, #ff4444 0%, #ff6d6d 100%);
    }}
    .links-wrap {{
      margin-top: 16px;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      background: #131714;
    }}
    .faq-grid {{
      margin-top: 10px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .faq-card {{
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px;
      background: #0f1410;
    }}
    .faq-question {{
      margin: 0;
      color: var(--text);
      font-size: 16px;
      line-height: 1.25;
    }}
    .faq-answer {{
      margin: 10px 0 0;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.55;
    }}
    .links-title {{
      margin: 0 0 8px;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.07em;
    }}
    .links {{
      margin-top: 0;
      display:grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }}
    .links a {{
      text-decoration: none;
      color: var(--muted);
      border:1px solid var(--line-soft);
      border-radius: 999px;
      padding: 9px 12px;
      background: #131714;
      font-family: "JetBrains Mono", monospace;
      font-size:13px;
      text-align: center;
    }}
    .links a:hover, .links a:focus-visible {{ border-color: var(--accent); color: var(--text); outline: none; }}
    .back {{
      margin-top: 14px;
      display: inline-block;
      color: var(--muted-soft);
      text-decoration: underline;
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
    }}
    .back:hover, .back:focus-visible {{ color: var(--text); outline: none; }}
    @media (max-width: 900px) {{
      .stats {{ grid-template-columns: 1fr; }}
      .preview-grid {{ grid-template-columns: 1fr 1fr; }}
      .links {{ grid-template-columns: 1fr 1fr; }}
      .faq-grid {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 640px) {{
      .wrap {{ width: calc(100% - 20px); }}
      .card {{ padding: 16px; border-radius: 16px; }}
      .badge-row {{ gap: 6px; }}
      .cta {{ width: 100%; }}
      .cta-secondary {{ width: 100%; }}
      .preview-grid {{ grid-template-columns: 1fr; }}
      .links {{ grid-template-columns: 1fr; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        animation: none !important;
        transition: none !important;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top reveal delay-1">
      <span>POLYMARKET PULSE // {page_label}</span>
      <div>
        <a href="/{slug}">EN</a>
      </div>
    </div>
    <article class="card reveal delay-2">
      <div class="badge-row">
        <span class="badge active">{badge_1}</span>
        <span class="badge">{badge_3}</span>
      </div>
      <h1>{page["h1"]}</h1>
      <p class="intro">{page["intro"]}</p>
      <div class="stats">
        <article class="stat">
          <p class="stat-label">{stat_1_label}</p>
          <p class="stat-value">{stat_1_value}</p>
          <p class="stat-copy">{stat_1_copy}</p>
        </article>
        <article class="stat">
          <p class="stat-label">{stat_2_label}</p>
          <p class="stat-value">{stat_2_value}</p>
          <p class="stat-copy">{stat_2_copy}</p>
        </article>
        <article class="stat">
          <p class="stat-label">{stat_3_label}</p>
          <p class="stat-value">{stat_3_value}</p>
          <p class="stat-copy">{stat_3_copy}</p>
        </article>
      </div>
      <div class="feature-rows">
        <div class="feature-row">{page["k1"]}</div>
        <div class="feature-row">{page["k2"]}</div>
        <div class="feature-row">{page["k3"]}</div>
      </div>
      <div class="cta-row">
        <a id="tg-link" class="cta" href="https://t.me/polymarket_pulse_bot?start=seo_{slug}_{lang}" target="_blank" rel="noopener noreferrer">{cta_text} -></a>
        {guide_cta}
      </div>
      <div class="cta-trust" aria-label="Telegram trust strip">
        <span class="trust-pill">No signup required</span>
        <span class="trust-pill">1 tap to open</span>
        <span class="trust-pill">Email backup only</span>
      </div>
      <p class="cta-note">{cta_note}</p>
      <p class="cta-backup-note">{cta_backup_note}</p>
      <p class="cta-backup-link-wrap">{backup_cta}</p>
    </article>
    <section class="preview reveal delay-3">
      <p class="links-title">{preview_head}</p>
      <div class="preview-grid">
        <article class="preview-card">
          <p class="preview-kicker">{screen_label} 01</p>
          <h3 class="preview-title">{page["k1"]}</h3>
          <p class="preview-copy">{preview_copy_1}</p>
          <div class="preview-bar" style="--w:72%;"><span></span></div>
        </article>
        <article class="preview-card">
          <p class="preview-kicker">{screen_label} 02</p>
          <h3 class="preview-title">{page["k2"]}</h3>
          <p class="preview-copy">{preview_copy_2}</p>
          <div class="preview-bar" style="--w:58%;"><span></span></div>
        </article>
        <article class="preview-card">
          <p class="preview-kicker">{screen_label} 03</p>
          <h3 class="preview-title">{page["k3"]}</h3>
          <p class="preview-copy">{preview_copy_3}</p>
          <div class="preview-bar down" style="--w:36%;"><span></span></div>
        </article>
      </div>
    </section>
    {compare_block}
    {bridge_block}
    {faq_block}
    <section class="links-wrap reveal delay-4">
      <p class="links-title">{links_head}</p>
      <div class="links" aria-label="{links_head}">
        {links}
      </div>
    </section>
      <a class="back" href="/">{back_text}</a>
  </div>
  <script>
    document.body.classList.add('ready');

    async function trackEvent(eventType, details = {{}}) {{
      const eventDetails = {{
        page_path: window.location.pathname + window.location.search,
        page_url: window.location.href,
        ...details
      }};
      try {{
        if (typeof window.gtag === 'function') {{
          window.gtag('event', eventType, eventDetails);
        }}
      }} catch (_) {{}}
      try {{
        await fetch('/api/events', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ event_type: eventType, source: 'site', details: eventDetails }}),
          keepalive: true
        }});
      }} catch (_) {{}}
    }}
    const p = new URLSearchParams(window.location.search);
    const details = {{
      lang: '{page_view_js_lang}',
      placement: 'seo_{slug}',
      utm_source: p.get('utm_source') || '',
      utm_medium: p.get('utm_medium') || '',
      utm_campaign: p.get('utm_campaign') || ''
    }};
    trackEvent('page_view', details);
    const seoBridge = document.getElementById('seo-bridge');
    if ('IntersectionObserver' in window && seoBridge) {{
      const observer = new IntersectionObserver((entries) => {{
        entries.forEach((entry) => {{
          if (!entry.isIntersecting || entry.target.dataset.seen === 'true') return;
          entry.target.dataset.seen = 'true';
          trackEvent('page_view', {{ ...details, placement: 'seo_bridge', surface_impression: true }});
          observer.unobserve(entry.target);
        }});
      }}, {{ threshold: 0.35 }});
      observer.observe(seoBridge);
    }}
    document.getElementById('tg-link')?.addEventListener('click', () => {{
      trackEvent('tg_click', details);
    }});
    document.getElementById('tg-link-bridge')?.addEventListener('click', () => {{
      trackEvent('tg_click', {{ ...details, placement: 'seo_bridge' }});
    }});
    document.getElementById('guide-link')?.addEventListener('click', () => {{
      trackEvent('waitlist_intent', {{ ...details, placement: 'seo_guide' }});
    }});
    document.getElementById('guide-link-bridge')?.addEventListener('click', () => {{
      trackEvent('waitlist_intent', {{ ...details, placement: 'seo_bridge_guide' }});
    }});
    document.getElementById('backup-link')?.addEventListener('click', () => {{
      trackEvent('waitlist_intent', {{ ...details, placement: 'seo_backup' }});
    }});
  </script>
</body>
</html>
"""


def fetch_signer_session(token: str) -> dict | None:
    if not PG_CONN:
        return None
    with psycopg.connect(PG_CONN, connect_timeout=5, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            cur.execute(SQL_SIGNER_SESSION_LOOKUP, (token,))
            return cur.fetchone()


def touch_signer_session_open(session_id: int) -> None:
    if not PG_CONN:
        return
    with psycopg.connect(PG_CONN, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '5000ms'")
            cur.execute(SQL_SIGNER_SESSION_OPEN, (session_id,))
        conn.commit()


def save_signer_payload(token: str, signed_payload: str, request: Request) -> dict:
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")
    session = fetch_signer_session(token)
    if not session:
        raise HTTPException(status_code=404, detail="signer_session_not_found")
    expires_at = session.get("expires_at")
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="signer_session_expired")

    clean_payload = signed_payload.strip()
    if not clean_payload:
        raise HTTPException(status_code=400, detail="signed_payload_required")

    payload_obj = {
        "raw": clean_payload,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "user_agent": request.headers.get("user-agent"),
        "ip": request.client.host if request.client else None,
    }

    with psycopg.connect(PG_CONN, connect_timeout=8, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            cur.execute(SQL_SIGNER_SESSION_SUBMIT, (Jsonb(payload_obj), session["id"]))
            updated = cur.fetchone()
            cur.execute(
                SQL_SIGNER_ACTIVITY,
                (
                    session["user_id"],
                    session["account_id"],
                    "signer_payload_submitted",
                    Jsonb(
                        {
                            "session_token": token,
                            "wallet": session["wallet_address"],
                            "status": updated["status"] if updated else "signed",
                        }
                    ),
                ),
            )
        conn.commit()

    return {
        "wallet": session["wallet_address"],
        "status": updated["status"] if updated else "signed",
        "expires_at": _to_iso(updated["expires_at"] if updated else session.get("expires_at")),
        "verified_at": _to_iso(updated["verified_at"] if updated else session.get("verified_at")),
    }


def render_trader_connect_page(session: dict, lang: Literal["ru", "en"]) -> str:
    base = base_url()
    title = "Trader signer session" if lang == "en" else "Signer-session Trader"
    intro = (
        "This page stores your signed payload for alpha review. It does not unlock live execution by itself."
        if lang == "en"
        else "Эта страница сохраняет signed payload для alpha-review. Сама по себе она не включает live execution."
    )
    kicker = "SIGNER SESSION · ALPHA" if lang == "en" else "SIGNER SESSION · ALPHA"
    submit_label = "Store signed payload" if lang == "en" else "Сохранить signed payload"
    challenge_label = "Challenge" if lang == "en" else "Challenge"
    payload_label = "Signed payload" if lang == "en" else "Signed payload"
    payload_placeholder = (
        "Paste signature / signed message / wallet-exported payload here"
        if lang == "en"
        else "Вставьте сюда signature / signed message / payload из кошелька"
    )
    status_note = (
        "// After submit, session moves to signed. A real verify/activation layer is still required."
        if lang == "en"
        else "// После submit сессия перейдёт в signed. Реальный verify/activation слой всё ещё нужен."
    )
    open_bot = "Open Trader bot" if lang == "en" else "Открыть Trader-бота"
    open_trader_page = "Trader page" if lang == "en" else "Страница Trader"
    success_wait = (
        "Payload stored. Session is now signed and ready for the next verify layer."
        if lang == "en"
        else "Payload сохранён. Сессия теперь в статусе signed и готова к следующему verify-слою."
    )
    expired = False
    if session.get("expires_at"):
        try:
            expired = session["expires_at"] < datetime.now(timezone.utc)
        except Exception:
            expired = False
    wallet = html.escape(str(session.get("wallet_address") or "n/a"))
    status = html.escape(str(session.get("status") or "n/a"))
    wallet_status = html.escape(str(session.get("wallet_status") or "n/a"))
    signer_kind = html.escape(str(session.get("signer_kind") or "n/a"))
    challenge = html.escape(str(session.get("challenge_text") or ""))
    expires_at = html.escape(_to_iso(session.get("expires_at")) or "n/a")
    verified_at = html.escape(_to_iso(session.get("verified_at")) or "n/a")
    token = html.escape(str(session.get("session_token") or ""))
    disabled_attr = "disabled" if expired else ""
    disabled_copy = (
        "This signer session has expired. Return to Telegram and run /signer again."
        if lang == "en"
        else "Эта signer-session истекла. Вернитесь в Telegram и снова запустите /signer."
    )
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="robots" content="noindex,nofollow" />
  <link rel="icon" type="image/svg+xml" sizes="any" href="/favicon.svg" />
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root {{
      --bg: #0d0f0e;
      --bg-2: #0a0c0b;
      --panel: #131714;
      --line: #1e2520;
      --line-soft: #2a332b;
      --text: #e8ede9;
      --muted: #8fa88f;
      --muted-soft: #6b7a6e;
      --accent: #00ff88;
      --danger: #ff5a5a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(1200px 800px at 85% -20%, rgba(0, 255, 136, 0.08) 0%, transparent 60%),
        linear-gradient(180deg, var(--bg-2) 0%, var(--bg) 55%, var(--bg-2) 100%);
    }}
    .wrap {{
      width: min(980px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 48px;
    }}
    .top {{
      display:flex;
      justify-content:space-between;
      align-items:center;
      gap: 12px;
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      color: var(--muted);
    }}
    .card {{
      margin-top: 16px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 24px;
      box-shadow: 0 24px 72px rgba(0,0,0,0.42);
    }}
    .kicker {{
      margin: 0 0 12px;
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      color: var(--muted-soft);
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0;
      line-height: 0.96;
      font-size: clamp(32px, 7vw, 56px);
      text-transform: uppercase;
      letter-spacing: -0.03em;
    }}
    .intro {{
      margin: 12px 0 0;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.5;
      font-family: "JetBrains Mono", monospace;
    }}
    .grid {{
      margin-top: 20px;
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 18px;
      align-items: start;
    }}
    .stack {{
      display: grid;
      gap: 12px;
    }}
    .panel {{
      background: #131714;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px;
    }}
    .label {{
      margin: 0 0 8px;
      color: var(--muted-soft);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .value, .mono, textarea {{
      font-family: "JetBrains Mono", monospace;
    }}
    .value {{
      color: var(--text);
      font-size: 14px;
      line-height: 1.6;
      word-break: break-word;
    }}
    .status-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .status-pill {{
      border: 1px solid var(--line-soft);
      border-radius: 10px;
      padding: 10px 12px;
      background: #0f1410;
    }}
    .status-pill strong {{
      display: block;
      margin-top: 6px;
      font-family: "JetBrains Mono", monospace;
      font-size: 13px;
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: "JetBrains Mono", monospace;
      font-size: 13px;
      line-height: 1.55;
      color: var(--text);
    }}
    textarea {{
      width: 100%;
      min-height: 220px;
      background: #0d0f0e;
      color: var(--text);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 14px;
      font-size: 13px;
      resize: vertical;
    }}
    button, .cta {{
      width: 100%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 48px;
      padding: 12px 16px;
      border-radius: 12px;
      border: 1px solid var(--accent);
      background: linear-gradient(180deg, #00ff88 0%, #00d874 100%);
      color: #0a0c0b;
      text-decoration: none;
      font-family: "JetBrains Mono", monospace;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
    }}
    .ghost {{
      width: 100%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 48px;
      padding: 12px 16px;
      border-radius: 12px;
      border: 1px solid var(--line-soft);
      background: transparent;
      color: var(--muted);
      text-decoration: none;
      font-family: "JetBrains Mono", monospace;
      font-size: 14px;
      font-weight: 700;
    }}
    .note {{
      color: var(--muted-soft);
      font-family: "JetBrains Mono", monospace;
      font-size: 12px;
      line-height: 1.5;
    }}
    .result {{
      min-height: 18px;
      color: var(--muted);
      font-family: "JetBrains Mono", monospace;
      font-size: 13px;
      line-height: 1.5;
    }}
    .result.ok {{ color: var(--accent); }}
    .result.err {{ color: var(--danger); }}
    @media (max-width: 760px) {{
      .wrap {{ width: calc(100% - 20px); }}
      .card {{ padding: 16px; border-radius: 16px; }}
      .grid {{ grid-template-columns: 1fr; }}
      .status-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <span>POLYMARKET PULSE // SIGNER</span>
      <span>{kicker}</span>
    </div>
    <article class="card">
      <p class="kicker">{kicker}</p>
      <h1>{title}</h1>
      <p class="intro">{intro}</p>
      <div class="grid">
        <div class="stack">
          <section class="panel">
            <p class="label">Session</p>
            <div class="status-grid">
              <div class="status-pill">
                <span class="label">wallet</span>
                <strong>{wallet}</strong>
              </div>
              <div class="status-pill">
                <span class="label">session status</span>
                <strong id="status-value">{status}</strong>
              </div>
              <div class="status-pill">
                <span class="label">wallet status</span>
                <strong>{wallet_status}</strong>
              </div>
              <div class="status-pill">
                <span class="label">signer kind</span>
                <strong>{signer_kind}</strong>
              </div>
              <div class="status-pill">
                <span class="label">expires_at</span>
                <strong>{expires_at}</strong>
              </div>
              <div class="status-pill">
                <span class="label">verified_at</span>
                <strong id="verified-value">{verified_at}</strong>
              </div>
            </div>
          </section>
          <section class="panel">
            <p class="label">{challenge_label}</p>
            <pre>{challenge}</pre>
          </section>
        </div>
        <div class="stack">
          <section class="panel">
            <p class="label">{payload_label}</p>
            <textarea id="signed-payload" placeholder="{html.escape(payload_placeholder)}" {disabled_attr}></textarea>
            <div style="height:10px"></div>
            <button id="submit-btn" {disabled_attr}>{submit_label}</button>
            <p class="note">{status_note}</p>
            <p id="result" class="result">{html.escape(disabled_copy if expired else "")}</p>
          </section>
          <section class="panel">
            <a class="cta" href="https://t.me/PolymarketPulse_trader_bot">{open_bot}</a>
            <div style="height:10px"></div>
            <a class="ghost" href="{base}/trader-bot">{open_trader_page}</a>
            <p class="note">{html.escape(success_wait)}</p>
          </section>
        </div>
      </div>
    </article>
  </div>
  <script>
    const token = {json.dumps(session.get("session_token") or "")};
    const lang = {json.dumps(lang)};
    const resultEl = document.getElementById("result");
    const statusEl = document.getElementById("status-value");
    const verifiedEl = document.getElementById("verified-value");
    const submitBtn = document.getElementById("submit-btn");
    const textarea = document.getElementById("signed-payload");

    async function submitPayload() {{
      const signedPayload = textarea.value.trim();
      if (!signedPayload) {{
        resultEl.className = "result err";
        resultEl.textContent = lang === "en"
          ? "Paste the signed payload first."
          : "Сначала вставьте signed payload.";
        return;
      }}
      submitBtn.disabled = true;
      resultEl.className = "result";
      resultEl.textContent = lang === "en" ? "Saving..." : "Сохраняю...";
      try {{
        const res = await fetch("/api/trader-signer/submit", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ token, signed_payload: signedPayload }})
        }});
        const data = await res.json();
        if (!res.ok) {{
          throw new Error(data.detail || "request_failed");
        }}
        statusEl.textContent = data.status || "signed";
        verifiedEl.textContent = data.verified_at || "n/a";
        resultEl.className = "result ok";
        resultEl.textContent = lang === "en"
          ? "Payload stored. Session is now signed."
          : "Payload сохранён. Сессия теперь в статусе signed.";
      }} catch (err) {{
        resultEl.className = "result err";
        resultEl.textContent = (lang === "en"
          ? "Could not save signer payload: "
          : "Не удалось сохранить signer payload: ") + err.message;
      }} finally {{
        submitBtn.disabled = false;
      }}
    }}

    submitBtn?.addEventListener("click", submitPayload);
  </script>
</body>
</html>
"""


def enrich_details(
    request: Request,
    details: dict | None = None,
    fallback_lang: str | None = None,
    fallback_placement: str | None = None,
) -> dict:
    payload = dict(details or {})
    qp = request.query_params

    for key in ("utm_source", "utm_medium", "utm_campaign"):
        if not payload.get(key):
            v = (qp.get(key) or "").strip()
            if v:
                payload[key] = v

    if not payload.get("placement") and fallback_placement:
        payload["placement"] = fallback_placement
    if not payload.get("placement"):
        placement_q = (qp.get("placement") or "").strip()
        if placement_q:
            payload["placement"] = placement_q

    if not payload.get("lang") and fallback_lang in {"ru", "en"}:
        payload["lang"] = fallback_lang

    return payload


def log_site_event(
    *,
    event_type: str,
    request: Request,
    lang: str,
    email: str | None = None,
    source: str | None = None,
    details: dict | None = None,
    path_override: str | None = None,
) -> None:
    if not PG_CONN:
        return
    event_path = (path_override or "").strip()[:512] or resolve_site_event_path(request, details)
    try:
        with psycopg.connect(PG_CONN, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into app.site_events (
                      event_type, email, source, lang, path, user_agent, ip, details
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        event_type,
                        (email or "").strip().lower() or None,
                        source,
                        lang,
                        event_path,
                        request.headers.get("user-agent"),
                        request.client.host if request.client else None,
                        Jsonb(details or {}),
                    ),
                )
            conn.commit()
    except Exception:
        # analytics must never break user-facing flow
        return


def resolve_site_event_path(request: Request, details: dict | None = None) -> str:
    payload = details or {}

    raw_page_path = str(payload.get("page_path") or "").strip()
    if raw_page_path:
        return raw_page_path[:512]

    raw_page_url = str(payload.get("page_url") or "").strip()
    if raw_page_url:
        try:
            parsed = urlparse(raw_page_url)
            candidate = parsed.path or request.url.path
            if parsed.query:
                candidate = f"{candidate}?{parsed.query}"
            return candidate[:512]
        except Exception:
            pass

    referer = (request.headers.get("referer") or "").strip()
    if referer:
        try:
            parsed = urlparse(referer)
            candidate = parsed.path or request.url.path
            if parsed.query:
                candidate = f"{candidate}?{parsed.query}"
            return candidate[:512]
        except Exception:
            pass

    return request.url.path[:512]


def render_email_shell(*, title: str, body_html: str, cta_label: str, cta_url: str, footer_html: str = "") -> str:
    return f"""
    <div style="margin:0;padding:24px;background:#0d0f0e;color:#e8ede9;font-family:'JetBrains Mono','SFMono-Regular',Consolas,monospace;">
      <div style="max-width:640px;margin:0 auto;background:#131714;border:1px solid #1e2520;border-radius:16px;padding:28px;">
        <div style="color:#6b7a6e;font-size:12px;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:14px;">Polymarket Pulse // email backup</div>
        <h1 style="margin:0 0 16px;font-size:28px;line-height:1.05;color:#e8ede9;">{title}</h1>
        <div style="font-size:14px;line-height:1.65;color:#8fa88f;">{body_html}</div>
        <p style="margin:24px 0 0;">
          <a href="{cta_url}" style="display:inline-block;background:#00ff88;color:#0a0c0b;text-decoration:none;font-weight:700;border-radius:12px;padding:13px 18px;">{cta_label}</a>
        </p>
        {footer_html}
      </div>
    </div>
    """


def render_status_page(*, title: str, body_html: str, primary_label: str, primary_url: str, secondary_html: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="noindex,follow" />
  <title>{title}</title>
  <style>
    :root {{
      --bg: #0d0f0e;
      --panel: #131714;
      --line: #1e2520;
      --text: #e8ede9;
      --muted: #8fa88f;
      --muted-soft: #6b7a6e;
      --accent: #00ff88;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
      background:
        radial-gradient(1200px 800px at 85% -20%, rgba(0, 255, 136, 0.08) 0%, transparent 60%),
        linear-gradient(180deg, #0a0c0b 0%, var(--bg) 100%);
      color: var(--text);
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
    }}
    .card {{
      width: min(640px, 100%);
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 28px;
      box-shadow: 0 24px 72px rgba(0,0,0,0.38);
    }}
    .kicker {{
      margin: 0 0 12px;
      color: var(--muted-soft);
      font: 12px/1.4 "JetBrains Mono", monospace;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0 0 14px;
      font-size: clamp(28px, 5vw, 42px);
      line-height: 0.98;
      text-transform: uppercase;
    }}
    .body {{
      color: var(--muted);
      font: 15px/1.65 "JetBrains Mono", monospace;
    }}
    .cta {{
      display: inline-block;
      margin-top: 22px;
      padding: 14px 18px;
      border-radius: 12px;
      background: var(--accent);
      color: #0a0c0b;
      text-decoration: none;
      font-weight: 700;
    }}
    .secondary {{
      margin-top: 16px;
      color: var(--muted-soft);
      font: 13px/1.6 "JetBrains Mono", monospace;
    }}
    .secondary a {{ color: var(--text); }}
  </style>
</head>
<body>
  <div class="card">
    <p class="kicker">Polymarket Pulse // email backup</p>
    <h1>{title}</h1>
    <div class="body">{body_html}</div>
    <a class="cta" href="{primary_url}">{primary_label}</a>
    <div class="secondary">{secondary_html}</div>
  </div>
</body>
</html>"""


def send_email(to_email: str, subject: str, html: str) -> None:
    if not RESEND_API_KEY:
        return

    payload = {
        "from": RESEND_FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail=f"Resend error: {resp.text[:200]}")


def stripe_enabled() -> bool:
    return bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID_MONTHLY)


def stripe_api_call(path: str, data: dict[str, str | int | None]) -> dict:
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured")
    payload = {k: v for k, v in data.items() if v is not None}
    resp = requests.post(
        f"https://api.stripe.com{path}",
        auth=(STRIPE_SECRET_KEY, ""),
        data=payload,
        timeout=20,
    )
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail=f"Stripe API error: {resp.text[:200]}")
    return resp.json()


def stripe_get(path: str, params: dict[str, str] | None = None) -> dict:
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured")
    resp = requests.get(
        f"https://api.stripe.com{path}",
        auth=(STRIPE_SECRET_KEY, ""),
        params=params or {},
        timeout=20,
    )
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail=f"Stripe API error: {resp.text[:200]}")
    return resp.json()


def verify_stripe_signature(payload: bytes, signature_header: str) -> bool:
    if not STRIPE_WEBHOOK_SECRET:
        return False
    if not signature_header:
        return False
    fields = {}
    for part in signature_header.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            fields.setdefault(k.strip(), []).append(v.strip())
    ts = (fields.get("t") or [None])[0]
    sigs = fields.get("v1") or []
    if not ts or not sigs:
        return False
    signed_payload = f"{ts}.{payload.decode('utf-8')}".encode("utf-8")
    expected = hmac.new(STRIPE_WEBHOOK_SECRET.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, s) for s in sigs)


def ensure_payment_schema(cur) -> None:
    cur.execute(SQL_ENSURE_PAYMENT_EVENTS)


def ensure_trade_alpha_schema(cur) -> None:
    cur.execute(SQL_ENSURE_TRADE_ALPHA_WAITLIST)


def resolve_user_id_for_email(cur, email: str, preferred_user_id: str | None = None) -> str:
    clean_email = email.strip().lower()
    if preferred_user_id:
        cur.execute("select id from app.users where id = %s::uuid", (preferred_user_id,))
        row = cur.fetchone()
        if row:
            user_id = str(row[0])
            cur.execute(
                """
                insert into app.identities (user_id, provider, provider_user_id)
                values (%s::uuid, 'email', %s)
                on conflict (provider, provider_user_id) do update
                set user_id = excluded.user_id
                """,
                (user_id, clean_email),
            )
            cur.execute(
                """
                insert into app.email_subscribers (email, user_id, source)
                values (%s, %s::uuid, 'site')
                on conflict (email) do update
                set user_id = coalesce(app.email_subscribers.user_id, excluded.user_id),
                    updated_at = now()
                """,
                (clean_email, user_id),
            )
            return user_id

    cur.execute("select user_id from app.email_subscribers where email = %s", (clean_email,))
    row = cur.fetchone()
    if row and row[0]:
        return str(row[0])

    cur.execute(
        "select user_id from app.identities where provider = 'email' and provider_user_id = %s limit 1",
        (clean_email,),
    )
    row = cur.fetchone()
    if row and row[0]:
        user_id = str(row[0])
    else:
        cur.execute(
            """
            insert into app.users (legacy_user_key)
            values (%s)
            on conflict (legacy_user_key) do update
            set updated_at = now()
            returning id
            """,
            (f"email:{clean_email}",),
        )
        user_id = str(cur.fetchone()[0])
        cur.execute(
            """
            insert into app.identities (user_id, provider, provider_user_id)
            values (%s::uuid, 'email', %s)
            on conflict (provider, provider_user_id) do update
            set user_id = excluded.user_id
            """,
            (user_id, clean_email),
        )

    cur.execute(
        """
        insert into app.email_subscribers (email, user_id, source)
        values (%s, %s::uuid, 'site')
        on conflict (email) do update
        set user_id = coalesce(app.email_subscribers.user_id, excluded.user_id),
            updated_at = now()
        """,
        (clean_email, user_id),
    )
    return user_id


def activate_pro_from_payment(
    *,
    provider: str,
    external_id: str,
    event_type: str,
    email: str,
    preferred_user_id: str | None,
    amount_cents: int | None,
    currency: str | None,
    source: str,
    payload: dict,
) -> tuple[bool, str]:
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")
    with psycopg.connect(PG_CONN, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '10000ms'")
            ensure_payment_schema(cur)
            cur.execute(SQL_PAYMENT_EVENT_EXISTS, (provider, external_id))
            if cur.fetchone():
                conn.commit()
                return False, "already_processed"

            user_id = resolve_user_id_for_email(cur, email, preferred_user_id=preferred_user_id)
            cur.execute(
                SQL_PAYMENT_EVENT_INSERT,
                (
                    provider,
                    external_id,
                    event_type,
                    "succeeded",
                    user_id,
                    email.strip().lower(),
                    amount_cents,
                    currency,
                    Jsonb(payload),
                ),
            )
            cur.execute(SQL_SUBSCRIPTION_INSERT_PRO, (user_id, source, PRO_SUBSCRIPTION_DAYS))
            cur.execute(SQL_PROFILE_SET_PRO, (user_id,))
        conn.commit()
    return True, user_id


def upsert_trade_alpha_waitlist(data: TraderAlphaRequest) -> int:
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")

    clean_email = data.email.strip().lower()
    with psycopg.connect(PG_CONN, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            ensure_trade_alpha_schema(cur)
            cur.execute(
                SQL_TRADE_ALPHA_WAITLIST_UPSERT,
                (
                    clean_email,
                    data.user_id,
                    data.telegram_id,
                    data.chat_id,
                    data.source,
                    Jsonb(data.details or {}),
                ),
            )
            row_id = int(cur.fetchone()[0])
        conn.commit()
    return row_id


def _to_iso(v: datetime | None) -> str | None:
    if v is None:
        return None
    try:
        return v.astimezone(timezone.utc).isoformat()
    except Exception:
        return str(v)


def _compact_series(values: list[float], max_points: int) -> list[float]:
    if len(values) <= max_points:
        return values
    if max_points <= 1:
        return [values[-1]]
    step = (len(values) - 1) / (max_points - 1)
    return [values[round(i * step)] for i in range(max_points)]


def _safe_market_token(value: str | None, *, max_len: int = 24) -> str:
    return "".join(ch for ch in str(value or "") if ch.isalnum() or ch in {"_", "-"})[:max_len]


def _polymarket_market_url(slug: str | None) -> str | None:
    clean_slug = (slug or "").strip().strip("/")
    if not clean_slug:
        return None
    return f"https://polymarket.com/market/{quote(clean_slug, safe='-_~')}"


def _pulse_track_market_url(market_id: str | None) -> str:
    token = _safe_market_token(market_id)
    payload = f"site_track_{token}" if token else "site_track"
    return f"https://t.me/polymarket_pulse_bot?start={payload}"


def fetch_live_movers_preview(
    limit: int = 3,
    spark_snapshots: int = 16,
    max_points: int = 16,
    min_distinct_points: int = 6,
) -> list[dict]:
    if not PG_CONN:
        return []

    with psycopg.connect(PG_CONN, connect_timeout=5) as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("set statement_timeout = '8000ms'")
            candidate_limit = min(36, max(limit, limit * 12))
            cur.execute(
                SQL_HOT_LIVE_MOVERS_PREVIEW,
                (
                    HOT_PREVIEW_MAX_FRESHNESS_SECONDS,
                    HOT_PREVIEW_MIN_LIQUIDITY,
                    HOT_PREVIEW_MAX_SPREAD,
                    candidate_limit,
                ),
            )
            movers = cur.fetchall()
            source = "hot"
            if not movers:
                cur.execute(SQL_LIVE_MOVERS_PREVIEW_LEGACY, (candidate_limit,))
                movers = cur.fetchall()
                source = "legacy"
            if not movers:
                return []

            market_ids = [str(r["market_id"]) for r in movers if r.get("market_id")]
            cur.execute(SQL_LIVE_SPARKLINE_POINTS, (market_ids, max(2, int(spark_snapshots))))
            points = cur.fetchall()

    series_by_market: dict[str, list[float]] = defaultdict(list)
    for row in points:
        market_id = str(row.get("market_id") or "")
        mid = row.get("mid")
        if market_id and mid is not None:
            series_by_market[market_id].append(float(mid))

    rich_rows: list[dict] = []
    fallback_rows: list[dict] = []
    for row in movers:
        market_id = str(row.get("market_id") or "")
        spark_source = list(series_by_market.get(market_id, []))
        hot_now = row.get("yes_mid_now")
        if source == "hot" and hot_now is not None:
            hot_now_f = float(hot_now)
            if not spark_source or abs(float(spark_source[-1]) - hot_now_f) > 1e-9:
                spark_source.append(hot_now_f)
        spark = _compact_series(spark_source, max_points=max_points)
        if len(spark) < 2:
            spark = []
        distinct_points = len({round(v, 6) for v in spark})

        payload = {
            "market_id": market_id,
            "question": row.get("question") or "",
            "slug": row.get("slug") or "",
            "last_bucket": _to_iso(row.get("last_bucket")),
            "prev_bucket": _to_iso(row.get("prev_bucket")),
            "yes_mid_now": float(row.get("yes_mid_now") or 0.0),
            "yes_mid_prev": float(row.get("yes_mid_prev") or 0.0),
            "delta_yes": float(row.get("delta_yes") or 0.0),
            "delta_1m": float(row.get("delta_1m") or 0.0),
            "spark": spark,
            "market_url": _polymarket_market_url(row.get("slug")),
            "track_url": _pulse_track_market_url(market_id),
        }

        if distinct_points >= min_distinct_points:
            rich_rows.append(payload)
        else:
            fallback_rows.append(payload)

    out = (rich_rows + fallback_rows)[:limit]
    return out


def upsert_waitlist(email: str, source: str) -> str:
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")

    token = secrets.token_urlsafe(24)
    with psycopg.connect(PG_CONN, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            cur.execute(
                """
                insert into app.email_subscribers (email, source, confirm_token)
                values (%s, %s, %s)
                on conflict (email) do update
                set source = excluded.source,
                    confirm_token = excluded.confirm_token,
                    updated_at = now()
                returning confirm_token
                """,
                (email.lower().strip(), source, token),
            )
            saved = cur.fetchone()[0]
        conn.commit()
    return saved


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"ok": True, "ts": datetime.now(timezone.utc).isoformat()})


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots() -> PlainTextResponse:
    return PlainTextResponse(
        "User-agent: *\nAllow: /\nSitemap: " + f"{base_url()}/sitemap.xml\n"
    )


@app.get("/sitemap.xml")
def sitemap() -> Response:
    u = base_url()

    def sitemap_entry(path: str) -> str:
        resolved_path = path or "/"
        href = f"{u}{resolved_path}"
        return f"  <url><loc>{href}</loc></url>\n"

    content_urls = ["", *[f"/{slug}" for slug in SEO_PAGES], "/how-it-works", "/commands", "/trader-bot"]
    entries = "".join(sitemap_entry(path) for path in content_urls)
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}"
        "</urlset>\n"
    )
    return Response(content=content, media_type="application/xml")


@app.get("/og-card.svg")
def og_card() -> Response:
    p = WEB_DIR / "og-card.svg"
    if not p.exists():
        return Response(status_code=404)
    return Response(content=p.read_text(encoding="utf-8"), media_type="image/svg+xml")


@app.get("/favicon.svg")
def favicon_svg() -> Response:
    p = WEB_DIR / "favicon.svg"
    if not p.exists():
        return Response(status_code=404)
    return Response(content=p.read_text(encoding="utf-8"), media_type="image/svg+xml")


@app.get("/favicon.ico")
def favicon_ico() -> Response:
    p = WEB_DIR / "favicon.ico"
    if p.exists():
        return Response(content=p.read_bytes(), media_type="image/x-icon")
    # Fallback for environments where only SVG is present.
    return favicon_svg()


@app.get("/favicon-32x32.png")
def favicon_32() -> Response:
    p = WEB_DIR / "favicon-32x32.png"
    if not p.exists():
        return Response(status_code=404)
    return Response(content=p.read_bytes(), media_type="image/png")


@app.get("/favicon-48x48.png")
def favicon_48() -> Response:
    p = WEB_DIR / "favicon-48x48.png"
    if not p.exists():
        return Response(status_code=404)
    return Response(content=p.read_bytes(), media_type="image/png")


@app.get("/apple-touch-icon.png")
def apple_touch_icon() -> Response:
    p = WEB_DIR / "apple-touch-icon.png"
    if not p.exists():
        return Response(status_code=404)
    return Response(content=p.read_bytes(), media_type="image/png")


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    lang = detect_site_lang(request)
    return HTMLResponse(load_page("index", lang))


@app.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request) -> HTMLResponse:
    lang = detect_site_lang(request)
    return HTMLResponse(load_page("privacy", lang))


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request) -> HTMLResponse:
    lang = detect_site_lang(request)
    return HTMLResponse(load_page("terms", lang))


@app.get("/how-it-works", response_class=HTMLResponse)
def how_it_works(request: Request) -> HTMLResponse:
    lang = detect_site_lang(request)
    return HTMLResponse(load_page("how-it-works", lang))


@app.get("/commands", response_class=HTMLResponse)
def commands_page(request: Request) -> HTMLResponse:
    lang = detect_site_lang(request)
    return HTMLResponse(load_page("commands", lang))


@app.get("/trader-bot", response_class=HTMLResponse)
def trader_bot_page(request: Request) -> HTMLResponse:
    lang = detect_site_lang(request)
    return HTMLResponse(load_page("trader-bot", lang))


@app.get("/trader-connect", response_class=HTMLResponse)
def trader_connect_page(request: Request, token: str) -> HTMLResponse:
    lang = detect_lang(request)
    session = fetch_signer_session(token)
    if not session:
        raise HTTPException(status_code=404, detail="signer_session_not_found")
    if session.get("status") == "new":
        touch_signer_session_open(int(session["id"]))
        session = fetch_signer_session(token) or session

    log_site_event(
        event_type="page_view",
        request=request,
        lang=lang,
        source="site",
        details={
            "placement": "trader_signer_page",
            "product": "trader",
            "session_status": session.get("status"),
        },
    )
    return HTMLResponse(render_trader_connect_page(session, lang))


@app.post("/api/events")
def site_event(data: SiteEventRequest, request: Request) -> JSONResponse:
    req_lang = detect_lang(request)
    merged_details = enrich_details(request, data.details, fallback_lang=req_lang)
    detail_lang = merged_details.get("lang")
    event_lang = detail_lang if detail_lang in {"ru", "en"} else req_lang
    resolved_event_path = resolve_site_event_path(request, merged_details)
    allowed = {"tg_click", "page_view", "waitlist_intent", "checkout_intent", "market_click"}
    event_type = (data.event_type or "").strip().lower()
    if event_type not in allowed:
        raise HTTPException(status_code=400, detail="unsupported event_type")

    log_site_event(
        event_type=event_type,
        request=request,
        lang=event_lang,
        source=(data.source or "site").strip()[:64] or "site",
        details=merged_details,
        path_override=resolved_event_path,
    )
    return JSONResponse({"ok": True})


@app.post("/api/trader-alpha")
def trader_alpha(data: TraderAlphaRequest, request: Request) -> JSONResponse:
    req_lang = detect_lang(request)
    details = enrich_details(request, data.details, fallback_lang=req_lang, fallback_placement="trader_alpha_form")
    row_id = upsert_trade_alpha_waitlist(data)
    log_site_event(
        event_type="waitlist_submit",
        request=request,
        lang=req_lang,
        email=data.email,
        source=(data.source or "site").strip()[:64] or "site",
        details={**details, "product": "trader_alpha", "alpha_id": row_id},
    )
    return JSONResponse({"ok": True, "message": "alpha_waitlist_saved", "id": row_id})


@app.post("/api/trader-signer/submit")
def trader_signer_submit(data: TraderSignerSubmitRequest, request: Request) -> JSONResponse:
    req_lang = detect_lang(request)
    saved = save_signer_payload(data.token, data.signed_payload, request)
    log_site_event(
        event_type="page_view",
        request=request,
        lang=req_lang,
        source="site",
        details={
            "placement": "trader_signer_submit",
            "product": "trader",
            "status": saved["status"],
            "wallet": saved["wallet"],
        },
    )
    return JSONResponse({"ok": True, **saved})


@app.get("/api/live-movers-preview")
def live_movers_preview(limit: int = 3) -> JSONResponse:
    safe_limit = max(1, min(int(limit), 6))
    try:
        rows = fetch_live_movers_preview(limit=safe_limit, spark_snapshots=16, max_points=16)
    except Exception:
        rows = []
    return JSONResponse(
        {
            "ok": True,
            "rows": rows,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.post("/api/stripe/checkout-session")
def stripe_checkout_session(data: StripeCheckoutRequest, request: Request) -> JSONResponse:
    if not stripe_enabled():
        raise HTTPException(status_code=503, detail="Stripe checkout is not configured")

    req_lang = detect_lang(request, explicit=data.lang)
    details = enrich_details(request, fallback_lang=req_lang, fallback_placement="stripe_checkout")
    email = data.email.strip().lower()
    source = (data.source or "site").strip()[:64] or "site"
    success_url = STRIPE_SUCCESS_URL or f"{base_url()}/stripe/success?session_id={{CHECKOUT_SESSION_ID}}&lang={req_lang}"
    cancel_url = STRIPE_CANCEL_URL or f"{base_url()}/?lang={req_lang}&checkout=cancel"

    session = stripe_api_call(
        "/v1/checkout/sessions",
        {
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "customer_email": email,
            "line_items[0][price]": STRIPE_PRICE_ID_MONTHLY,
            "line_items[0][quantity]": "1",
            "allow_promotion_codes": "true",
            "metadata[email]": email,
            "metadata[user_id]": data.user_id or "",
            "metadata[source]": source,
            "metadata[lang]": req_lang,
            "metadata[plan]": "pro_monthly",
        },
    )

    log_site_event(
        event_type="checkout_intent",
        request=request,
        lang=req_lang,
        email=email,
        source=source,
        details={**details, "provider": "stripe", "session_id": session.get("id")},
    )
    return JSONResponse(
        {
            "ok": True,
            "provider": "stripe",
            "session_id": session.get("id"),
            "url": session.get("url"),
            "publishable_key": STRIPE_PUBLISHABLE_KEY,
        }
    )


@app.get("/stripe/success", response_class=HTMLResponse)
def stripe_success(session_id: str, request: Request) -> HTMLResponse:
    req_lang = detect_lang(request)
    if not stripe_enabled():
        if req_lang == "ru":
            return HTMLResponse("<h3>Stripe пока не настроен.</h3>", status_code=503)
        return HTMLResponse("<h3>Stripe is not configured yet.</h3>", status_code=503)

    session = stripe_get(
        f"/v1/checkout/sessions/{session_id}",
        params={"expand[]": "subscription"},
    )
    status = (session.get("status") or "").lower()
    payment_status = (session.get("payment_status") or "").lower()
    metadata = session.get("metadata") or {}
    email = (
        metadata.get("email")
        or session.get("customer_email")
        or ((session.get("customer_details") or {}).get("email"))
        or ""
    ).strip().lower()
    preferred_user_id = (metadata.get("user_id") or "").strip() or None
    currency = (session.get("currency") or "").upper() or None
    amount_total = session.get("amount_total")

    if not email or status != "complete" or payment_status not in {"paid", "no_payment_required"}:
        if req_lang == "ru":
            return HTMLResponse("<h3>Платеж не подтвержден. Если списание было, напишите в поддержку.</h3>", status_code=400)
        return HTMLResponse("<h3>Payment is not confirmed yet. If charged, contact support.</h3>", status_code=400)

    applied, _user_id = activate_pro_from_payment(
        provider="stripe_checkout",
        external_id=str(session.get("id") or session_id),
        event_type="checkout.session.completed",
        email=email,
        preferred_user_id=preferred_user_id,
        amount_cents=int(amount_total) if amount_total is not None else None,
        currency=currency,
        source="stripe_checkout",
        payload=session,
    )

    if req_lang == "ru":
        if applied:
            return HTMLResponse("<h3>Оплата подтверждена. PRO активирован.</h3>")
        return HTMLResponse("<h3>Оплата уже обработана ранее. PRO активен.</h3>")
    if applied:
        return HTMLResponse("<h3>Payment confirmed. PRO is active.</h3>")
    return HTMLResponse("<h3>Payment was already processed. PRO is active.</h3>")


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request) -> JSONResponse:
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe webhook secret is not configured")

    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    if not verify_stripe_signature(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    event = json.loads(payload.decode("utf-8"))
    event_type = (event.get("type") or "").strip()
    data_obj = ((event.get("data") or {}).get("object")) or {}
    event_id = str(event.get("id") or "")

    if event_type == "checkout.session.completed":
        metadata = data_obj.get("metadata") or {}
        email = (
            metadata.get("email")
            or data_obj.get("customer_email")
            or ((data_obj.get("customer_details") or {}).get("email"))
            or ""
        ).strip().lower()
        if email:
            activate_pro_from_payment(
                provider="stripe_event",
                external_id=event_id or str(data_obj.get("id") or ""),
                event_type=event_type,
                email=email,
                preferred_user_id=(metadata.get("user_id") or "").strip() or None,
                amount_cents=data_obj.get("amount_total"),
                currency=(data_obj.get("currency") or "").upper() or None,
                source="stripe_webhook",
                payload=event,
            )

    return JSONResponse({"ok": True})


@app.post("/api/waitlist")
def waitlist(data: WaitlistRequest, request: Request) -> JSONResponse:
    req_lang = detect_lang(request)
    source = data.source.strip() if data.source else "site"
    details = enrich_details(request, data.details, fallback_lang=req_lang, fallback_placement="waitlist_form")

    token = upsert_waitlist(data.email, source)
    confirm_q = {"token": token}
    for key in ("utm_source", "utm_medium", "utm_campaign", "placement", "lang"):
        value = details.get(key)
        if value:
            confirm_q[key] = value
    confirm_link = f"{base_url()}/confirm?{urlencode(confirm_q)}"
    log_site_event(
        event_type="waitlist_submit",
        request=request,
        lang=req_lang,
        email=data.email,
        source=source,
        details=details,
    )

    if req_lang == "ru":
        html = render_email_shell(
            title="Подтвердите email backup",
            body_html=(
                "<p>Подтвердите email, чтобы включить резервный канал Polymarket Pulse.</p>"
                "<p>Что дальше:</p>"
                "<ul>"
                "<li>Telegram остаётся основным live-каналом</li>"
                "<li>Email будет нужен для дайджеста и product updates</li>"
                "<li>Подписку можно выключить из любого письма</li>"
                "</ul>"
            ),
            cta_label="Подтвердить email",
            cta_url=confirm_link,
            footer_html='<p style="margin:20px 0 0;color:#6b7a6e;font-size:12px;line-height:1.6;">Сначала бот для live-сигналов. Email нужен как backup и для digest.</p>',
        )
        subject = "Подтвердите подписку Polymarket Pulse"
        message = "Письмо отправлено. Подтвердите email, чтобы включить backup и digest."
    else:
        html = render_email_shell(
            title="Confirm your email backup",
            body_html=(
                "<p>Confirm your email to enable the backup channel for Polymarket Pulse.</p>"
                "<p>What this does:</p>"
                "<ul>"
                "<li>Telegram stays the primary live signal loop</li>"
                "<li>Email handles digest delivery and launch updates</li>"
                "<li>You can unsubscribe from any message</li>"
                "</ul>"
            ),
            cta_label="Confirm email",
            cta_url=confirm_link,
            footer_html='<p style="margin:20px 0 0;color:#6b7a6e;font-size:12px;line-height:1.6;">Use Telegram for action now. Keep email as backup for digest and updates.</p>',
        )
        subject = "Confirm your Polymarket Pulse subscription"
        message = "Confirmation email sent. Check your inbox to enable digest backup."

    try:
        send_email(data.email, subject, html)
    except Exception:
        return JSONResponse({"ok": True, "message": message + " (email queue delay possible)"})
    return JSONResponse({"ok": True, "message": message})


@app.get("/confirm", response_class=HTMLResponse)
def confirm(token: str, request: Request) -> HTMLResponse:
    req_lang = detect_lang(request)
    details = enrich_details(request, fallback_lang=req_lang, fallback_placement="email_confirm")
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")

    with psycopg.connect(PG_CONN, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            cur.execute(
                """
                update app.email_subscribers
                set confirmed_at = coalesce(confirmed_at, now()),
                    updated_at = now()
                where confirm_token = %s
                  and unsubscribed_at is null
                returning email
                """,
                (token,),
            )
            row = cur.fetchone()
        conn.commit()

    if not row:
        log_site_event(
            event_type="confirm_failed",
            request=request,
            lang=req_lang,
            details={**details, "reason": "invalid_or_expired_token"},
        )
        if req_lang == "ru":
            return HTMLResponse(
                render_status_page(
                    title="Ссылка недействительна",
                    body_html="Токен подтверждения недействителен или уже использован. Если нужно, просто отправьте email заново с главной страницы.",
                    primary_label="Открыть Telegram-бота",
                    primary_url=PULSE_BOT_URL,
                    secondary_html=f'Вернитесь на <a href="{base_url()}">главную</a> и отправьте email ещё раз.',
                ),
                status_code=400,
            )
        return HTMLResponse(
            render_status_page(
                title="Link expired",
                body_html="This confirmation token is invalid or already used. If needed, resubmit your email from the homepage and we will send a fresh link.",
                primary_label="Open Telegram Bot",
                primary_url=PULSE_BOT_URL,
                secondary_html=f'Go back to the <a href="{base_url()}">homepage</a> and request a fresh email.',
            ),
            status_code=400,
        )

    email = row[0]
    log_site_event(
        event_type="confirm_success",
        request=request,
        lang=req_lang,
        email=email,
        details=details,
    )
    unsub = f"{base_url()}/unsubscribe?token={token}"
    if req_lang == "ru":
        try:
            send_email(
                email,
                "Добро пожаловать в Polymarket Pulse",
                render_email_shell(
                    title="Email подтверждён",
                    body_html=(
                        "<p>Подписка подтверждена. Email-дайджест включён.</p>"
                        "<p>Что теперь:</p>"
                        "<ul>"
                        "<li>Следите за live-сигналами в Telegram</li>"
                        "<li>Email будет приходить как backup и digest</li>"
                        "<li>Если сигналов нет, это нормально: quiet-state тоже часть продукта</li>"
                        "</ul>"
                    ),
                    cta_label="Открыть Telegram-бота",
                    cta_url=PULSE_BOT_URL,
                    footer_html=f'<p style="margin:20px 0 0;color:#6b7a6e;font-size:12px;line-height:1.6;"><a href="{unsub}" style="color:#8fa88f;">Отписаться</a></p>',
                ),
            )
        except Exception:
            pass
        return HTMLResponse(
            render_status_page(
                title="Email подтверждён",
                body_html="Дайджест включён. Лучше всего использовать Telegram как основной live-канал, а email оставить как backup для digest и updates.",
                primary_label="Открыть Telegram-бота",
                primary_url=PULSE_BOT_URL,
                secondary_html=f'<a href="{unsub}">Отписаться</a>',
            )
        )
    try:
        send_email(
            email,
            "Welcome to Polymarket Pulse",
            render_email_shell(
                title="Email confirmed",
                body_html=(
                    "<p>You are now confirmed for Polymarket Pulse email updates.</p>"
                    "<p>What to expect:</p>"
                    "<ul>"
                    "<li>Telegram stays your primary live signal loop</li>"
                    "<li>Email works as backup for digest and launch updates</li>"
                    "<li>Quiet days are expected; we do not force noise into the feed</li>"
                    "</ul>"
                ),
                cta_label="Open Telegram Bot",
                cta_url=PULSE_BOT_URL,
                footer_html=f'<p style="margin:20px 0 0;color:#6b7a6e;font-size:12px;line-height:1.6;"><a href="{unsub}" style="color:#8fa88f;">Unsubscribe</a></p>',
            ),
        )
    except Exception:
        pass
    return HTMLResponse(
        render_status_page(
            title="Email confirmed",
            body_html="Daily digest is enabled. Use Telegram for the live loop now, and keep email as backup for digest and updates.",
            primary_label="Open Telegram Bot",
            primary_url=PULSE_BOT_URL,
            secondary_html=f'<a href="{unsub}">Unsubscribe</a>',
        )
    )


@app.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe(token: str, request: Request) -> HTMLResponse:
    req_lang = detect_lang(request)
    details = enrich_details(request, fallback_lang=req_lang, fallback_placement="email_unsubscribe")
    if not PG_CONN:
        raise HTTPException(status_code=500, detail="PG_CONN is not configured")

    with psycopg.connect(PG_CONN, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = '8000ms'")
            cur.execute(
                """
                update app.email_subscribers
                set unsubscribed_at = now(),
                    updated_at = now()
                where confirm_token = %s
                  and unsubscribed_at is null
                returning email
                """,
                (token,),
            )
            row = cur.fetchone()
        conn.commit()

    if not row:
        log_site_event(
            event_type="unsubscribe_failed",
            request=request,
            lang=req_lang,
            details={**details, "reason": "token_not_found_or_already_unsubscribed"},
        )
        if req_lang == "ru":
            return HTMLResponse(
                render_status_page(
                    title="Отписка не сработала",
                    body_html="Токен не найден или этот email уже был отписан.",
                    primary_label="Открыть Telegram-бота",
                    primary_url=PULSE_BOT_URL,
                    secondary_html=f'<a href="{base_url()}">Вернуться на сайт</a>',
                ),
                status_code=400,
            )
        return HTMLResponse(
            render_status_page(
                title="Unsubscribe failed",
                body_html="This token was not found or the email was already unsubscribed.",
                primary_label="Open Telegram Bot",
                primary_url=PULSE_BOT_URL,
                secondary_html=f'<a href="{base_url()}">Back to homepage</a>',
            ),
            status_code=400,
        )

    log_site_event(
        event_type="unsubscribe_success",
        request=request,
        lang=req_lang,
        email=row[0],
        details=details,
    )
    if req_lang == "ru":
        return HTMLResponse(
            render_status_page(
                title="Вы отписаны",
                body_html="Email-дайджест и product updates больше не будут приходить на этот адрес.",
                primary_label="Открыть Telegram-бота",
                primary_url=PULSE_BOT_URL,
                secondary_html=f'<a href="{base_url()}">Вернуться на сайт</a>',
            )
        )
    return HTMLResponse(
        render_status_page(
            title="You are unsubscribed",
            body_html="Daily digest and product updates will no longer be sent to this email.",
            primary_label="Open Telegram Bot",
            primary_url=PULSE_BOT_URL,
            secondary_html=f'<a href="{base_url()}">Back to homepage</a>',
        )
    )


@app.get("/{slug}", response_class=HTMLResponse)
def seo_page(slug: str, request: Request) -> HTMLResponse:
    if slug not in SEO_PAGES:
        raise HTTPException(status_code=404, detail="Not found")
    lang = detect_site_lang(request)
    return HTMLResponse(render_seo_page(slug, lang))
