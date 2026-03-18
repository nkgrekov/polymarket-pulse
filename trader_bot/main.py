import asyncio
import logging
import os
import re
import secrets
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

TRADER_BOT_TOKEN = os.environ["TRADER_BOT_TOKEN"]
PG_CONN = os.environ["PG_CONN"]
APP_BASE_URL = os.environ.get("APP_BASE_URL", "https://polymarketpulse.app").rstrip("/")
TRADER_SITE_URL = os.environ.get("TRADER_SITE_URL", f"{APP_BASE_URL}/trader-bot")
PULSE_BOT_URL = os.environ.get("PULSE_BOT_URL", "https://t.me/polymarket_pulse_bot")
TRADER_SOURCE = os.environ.get("TRADER_SOURCE", "telegram_bot")
DEFAULT_ORDER_USD = Decimal(os.environ.get("TRADER_DEFAULT_ORDER_USD", "10"))
TOP_MARKETS_LIMIT = int(os.environ.get("TRADER_TOP_MARKETS_LIMIT", "5"))
DB_CONNECT_TIMEOUT_SECONDS = int(os.environ.get("DB_CONNECT_TIMEOUT_SECONDS", "10"))
TRADER_SIGNER_URL = os.environ.get("TRADER_SIGNER_URL", f"{APP_BASE_URL}/trader-connect")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("polymarket_pulse_trader_bot")

WALLET_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

TEXTS: dict[str, dict[str, str]] = {
    "start": {
        "en": (
            "<b>Polymarket Pulse Trader alpha</b>\n\n"
            "From signal to execution in Telegram.\n\n"
            "<b>Live now</b>\n"
            "• wallet registration without custody\n"
            "• manual order drafts\n"
            "• positions, rules, risk and agent views\n"
            "• follow-source setup for alpha testing\n\n"
            "<b>Next</b>\n"
            "• delegated signer\n"
            "• routed execution\n"
            "• auto-on-rules inside your limits"
        ),
        "ru": (
            "<b>Polymarket Pulse Trader alpha</b>\n\n"
            "Путь от сигнала к исполнению прямо в Telegram.\n\n"
            "<b>Уже работает</b>\n"
            "• регистрация кошелька без custody\n"
            "• черновики ручных ордеров\n"
            "• просмотр positions, rules, risk и agent\n"
            "• настройка follow-источников для alpha\n\n"
            "<b>Дальше</b>\n"
            "• delegated signer\n"
            "• routed execution\n"
            "• auto-on-rules в ваших лимитах"
        ),
    },
    "help": {
        "en": (
            "<b>Trader commands</b>\n\n"
            "/ready — execution readiness in one view\n"
            "/connect &lt;wallet&gt; — register primary wallet\n"
            "/signer — create or inspect signer session\n"
            "/markets — live markets to trade from\n"
            "/buy &lt;market_id&gt; &lt;yes|no&gt; &lt;usd&gt; [limit_price]\n"
            "/sell &lt;market_id&gt; &lt;yes|no&gt; &lt;usd&gt; [limit_price]\n"
            "/order — latest order drafts\n"
            "/positions — cached open positions\n"
            "/follow &lt;wallet&gt; — attach a follow source\n"
            "/rules [field value] — view or update rules\n"
            "/risk — current risk state\n"
            "/pause [on|off] — pause agent execution\n"
            "/agent — latest agent decisions"
        ),
        "ru": (
            "<b>Команды Trader</b>\n\n"
            "/ready — readiness в одном экране\n"
            "/connect &lt;wallet&gt; — зарегистрировать основной кошелёк\n"
            "/signer — создать или посмотреть signer-session\n"
            "/markets — live рынки для исполнения\n"
            "/buy &lt;market_id&gt; &lt;yes|no&gt; &lt;usd&gt; [limit_price]\n"
            "/sell &lt;market_id&gt; &lt;yes|no&gt; &lt;usd&gt; [limit_price]\n"
            "/order — последние черновики ордеров\n"
            "/positions — кэш открытых позиций\n"
            "/follow &lt;wallet&gt; — добавить follow-источник\n"
            "/rules [field value] — посмотреть или обновить правила\n"
            "/risk — текущее risk-state\n"
            "/pause [on|off] — пауза agent execution\n"
            "/agent — последние agent decisions"
        ),
    },
    "connect_usage": {
        "en": "Use <code>/connect 0xYourWallet</code> to register a primary wallet. Non-custodial only in alpha.",
        "ru": "Используйте <code>/connect 0xYourWallet</code>, чтобы зарегистрировать основной кошелёк. В alpha только non-custodial сценарий.",
    },
    "connect_saved": {
        "en": (
            "Primary wallet saved:\n<code>{wallet}</code>\n"
            "status: <code>{status}</code> | signer: <code>{signer_kind}</code>\n"
            "{next_line}"
        ),
        "ru": (
            "Основной кошелёк сохранён:\n<code>{wallet}</code>\n"
            "status: <code>{status}</code> | signer: <code>{signer_kind}</code>\n"
            "{next_line}"
        ),
    },
    "connect_current": {
        "en": (
            "<b>Primary wallet</b>\n\n"
            "<code>{wallet}</code>\n"
            "status: <code>{status}</code> | signer: <code>{signer_kind}</code>\n"
            "{next_line}\n"
            "Use <code>/connect 0xYourWallet</code> to replace it."
        ),
        "ru": (
            "<b>Основной кошелёк</b>\n\n"
            "<code>{wallet}</code>\n"
            "status: <code>{status}</code> | signer: <code>{signer_kind}</code>\n"
            "{next_line}\n"
            "Используйте <code>/connect 0xYourWallet</code>, чтобы заменить его."
        ),
    },
    "markets_empty": {
        "en": "No live trade-ready markets right now. Universe is likely flat in the current window.",
        "ru": "Сейчас нет live рынков, готовых для trade-flow. Скорее всего, universe плоский в текущем окне.",
    },
    "positions_empty": {
        "en": "No cached positions yet. Connect a wallet first, then execution sync can populate positions. Use /ready for the full readiness path.",
        "ru": "Кэшированных позиций пока нет. Сначала подключите кошелёк, после этого execution sync сможет подтянуть позиции. Используйте /ready для полного readiness-пути.",
    },
    "orders_empty": {
        "en": "No order drafts yet. Try <code>/buy market_id yes 10</code> or <code>/sell market_id no 10</code>.",
        "ru": "Черновиков ордеров пока нет. Попробуйте <code>/buy market_id yes 10</code> или <code>/sell market_id no 10</code>.",
    },
    "order_status_hint": {
        "en": "worker: <code>{event_type}</code>{reason_line}{external_line}",
        "ru": "worker: <code>{event_type}</code>{reason_line}{external_line}",
    },
    "follow_usage": {
        "en": "Use <code>/follow 0xWallet</code> to add a wallet/trader source for copy-monitoring alpha.",
        "ru": "Используйте <code>/follow 0xWallet</code>, чтобы добавить кошелёк/трейдера в copy-monitoring alpha.",
    },
    "follow_saved": {
        "en": "Follow source saved:\n<code>{wallet}</code>\nMode: observe -> mirror rules editable later.",
        "ru": "Follow-источник сохранён:\n<code>{wallet}</code>\nРежим: observe -> mirror rules можно подкрутить позже.",
    },
    "signer_missing_wallet": {
        "en": "Connect a wallet first with <code>/connect 0xYourWallet</code>, then open <code>/signer</code>.",
        "ru": "Сначала подключите кошелёк через <code>/connect 0xYourWallet</code>, затем откройте <code>/signer</code>.",
    },
    "signer_title": {
        "en": "<b>Signer session</b>",
        "ru": "<b>Signer session</b>",
    },
    "signer_copy": {
        "en": (
            "<b>Signer session</b>\n\n"
            "wallet: <code>{wallet}</code>\n"
            "status: <code>{status}</code>\n"
            "expires_at: <code>{expires_at}</code>\n\n"
            "challenge:\n<code>{challenge}</code>\n\n"
            "Open verification page:\n{verify_url}\n\n"
            "This is the first signer/delegation layer. Web verification is the next step before live execution."
        ),
        "ru": (
            "<b>Signer session</b>\n\n"
            "wallet: <code>{wallet}</code>\n"
            "status: <code>{status}</code>\n"
            "expires_at: <code>{expires_at}</code>\n\n"
            "challenge:\n<code>{challenge}</code>\n\n"
            "Откройте verification page:\n{verify_url}\n\n"
            "Это первый signer/delegation слой. Web verification — следующий шаг перед live execution."
        ),
    },
    "pause_on": {
        "en": "Agent execution paused. Manual order drafts remain available.",
        "ru": "Agent execution поставлен на паузу. Ручные черновики ордеров по-прежнему доступны.",
    },
    "pause_off": {
        "en": "Agent execution resumed. Rule checks stay active.",
        "ru": "Agent execution снова активен. Проверки правил остаются включены.",
    },
    "pause_usage": {
        "en": "Use <code>/pause on</code> or <code>/pause off</code>.",
        "ru": "Используйте <code>/pause on</code> или <code>/pause off</code>.",
    },
    "rules_usage": {
        "en": (
            "Examples:\n"
            "<code>/rules mode manual</code>\n"
            "<code>/rules mode auto</code>\n"
            "<code>/rules max_order 25</code>\n"
            "<code>/rules daily_cap 5</code>\n"
            "<code>/rules loss_cap 25</code>\n"
            "<code>/rules exposure 50</code>\n"
            "<code>/rules slippage 150</code>\n"
            "<code>/rules cooldown 15</code>\n"
            "<code>/rules confirm on</code>"
        ),
        "ru": (
            "Примеры:\n"
            "<code>/rules mode manual</code>\n"
            "<code>/rules mode auto</code>\n"
            "<code>/rules max_order 25</code>\n"
            "<code>/rules daily_cap 5</code>\n"
            "<code>/rules loss_cap 25</code>\n"
            "<code>/rules exposure 50</code>\n"
            "<code>/rules slippage 150</code>\n"
            "<code>/rules cooldown 15</code>\n"
            "<code>/rules confirm on</code>"
        ),
    },
    "invalid_wallet": {
        "en": "Wallet should look like a Polygon/EVM address: <code>0x...</code>",
        "ru": "Кошелёк должен выглядеть как Polygon/EVM адрес: <code>0x...</code>",
    },
    "invalid_order": {
        "en": "Format: <code>/{side} market_id yes|no usd [limit_price]</code>",
        "ru": "Формат: <code>/{side} market_id yes|no usd [limit_price]</code>",
    },
    "market_not_found": {
        "en": "Market not found. Use <code>/markets</code> to get current IDs.",
        "ru": "Рынок не найден. Используйте <code>/markets</code>, чтобы взять актуальные ID.",
    },
    "order_saved": {
        "en": (
            "<b>Order draft saved</b>\n\n"
            "Market: <code>{market_id}</code>\n"
            "Side: <b>{side}</b> {outcome}\n"
            "Size: <b>${usd}</b>\n"
            "Type: <b>{order_type}</b>{limit_line}\n"
            "Risk gate: mode=<code>{mode}</code>, paused=<code>{paused}</code>, max_order=<code>{max_order}</code>\n"
            "{next_line}\n\n"
            "Execution routing is not live yet. This draft is stored for alpha workflow and operator testing.\n"
            "Need the full picture? Open /ready."
        ),
        "ru": (
            "<b>Черновик ордера сохранён</b>\n\n"
            "Market: <code>{market_id}</code>\n"
            "Side: <b>{side}</b> {outcome}\n"
            "Size: <b>${usd}</b>\n"
            "Type: <b>{order_type}</b>{limit_line}\n"
            "Risk gate: mode=<code>{mode}</code>, paused=<code>{paused}</code>, max_order=<code>{max_order}</code>\n"
            "{next_line}\n\n"
            "Роутинг исполнения ещё не включён. Этот draft сохранён для alpha workflow и операторского теста.\n"
            "Нужна полная картина? Откройте /ready."
        ),
    },
    "order_blocked": {
        "en": "Order blocked by current rules: {reason}",
        "ru": "Ордер заблокирован текущими правилами: {reason}",
    },
    "risk_title": {
        "en": "<b>Risk state</b>",
        "ru": "<b>Risk state</b>",
    },
    "rules_title": {
        "en": "<b>Agent rules</b>",
        "ru": "<b>Agent rules</b>",
    },
    "agent_empty": {
        "en": "No agent decisions yet. The agent layer is wired, but no suggestions/executions have been logged.",
        "ru": "Agent decisions пока нет. Слой агента уже разведен, но suggestions/executions ещё не логировались.",
    },
    "rules_updated": {
        "en": "Rules updated: <code>{field}</code> -> <code>{value}</code>",
        "ru": "Rules updated: <code>{field}</code> -> <code>{value}</code>",
    },
}

SQL_RESOLVE_USER = """
select bot.resolve_or_create_user_from_telegram(%s, %s, %s, %s, %s, %s) as user_id;
"""

SQL_ENSURE_ACCOUNT = "select trade.ensure_account(%s::uuid) as account_id;"

SQL_PROFILE = """
select locale
from bot.profiles
where user_id = %s::uuid
limit 1;
"""

SQL_LOG_ACTIVITY = """
insert into trade.activity_events (
  user_id,
  account_id,
  event_type,
  source,
  market_id,
  details
) values (%s::uuid, %s, %s, %s, %s, %s::jsonb);
"""

SQL_PRIMARY_WALLET = """
select id, wallet_address, status, signer_kind, label
from trade.wallet_links
where account_id = %s
order by is_primary desc, updated_at desc, created_at desc
limit 1;
"""

SQL_SIGNER_SESSION_CURRENT = """
select id, session_token, status, challenge_text, expires_at, verified_at
from trade.signer_sessions
where account_id = %s
  and wallet_link_id = %s
  and status in ('new', 'opened', 'signed', 'verified')
  and expires_at > now()
order by created_at desc
limit 1;
"""

SQL_SIGNER_SESSION_CREATE = """
insert into trade.signer_sessions (
  account_id,
  wallet_link_id,
  session_token,
  status,
  challenge_text
) values (%s, %s, %s, 'new', %s)
returning id, session_token, status, challenge_text, expires_at, verified_at;
"""

SQL_CONNECT_WALLET = """
with reset_primary as (
  update trade.wallet_links
  set is_primary = false,
      updated_at = now()
  where account_id = %s
)
insert into trade.wallet_links (
  account_id,
  wallet_address,
  chain,
  signer_kind,
  label,
  is_primary,
  status
) values (
  %s,
  %s,
  'polygon',
  'delegated',
  %s,
  true,
  'pending'
)
on conflict (wallet_address) do update
set account_id = excluded.account_id,
    label = excluded.label,
    is_primary = true,
    signer_kind = excluded.signer_kind,
    status = 'pending',
    updated_at = now();
"""

SQL_TOP_MARKETS = """
select market_id, question, yes_mid_now, yes_mid_prev, delta_yes, last_bucket, prev_bucket
from public.top_movers_latest
where yes_mid_now is not null and yes_mid_prev is not null
order by abs(delta_yes) desc nulls last
limit %s;
"""

SQL_MARKET = """
select market_id, question
from public.markets
where market_id = %s
limit 1;
"""

SQL_ORDER_GUARD = """
with rules as (
  select *
  from trade.agent_rules
  where account_id = %s
), risk as (
  select *
  from trade.risk_state
  where account_id = %s
), order_counts as (
  select count(*)::int as orders_today
  from trade.orders
  where account_id = %s
    and created_at >= date_trunc('day', now())
)
select
  coalesce((select mode from rules), 'manual') as mode,
  coalesce((select paused from rules), false) as agent_paused,
  coalesce((select require_confirm from rules), true) as require_confirm,
  coalesce((select max_order_usd from rules), 25) as max_order_usd,
  coalesce((select daily_trade_cap from rules), 5) as daily_trade_cap,
  coalesce((select daily_loss_cap_usd from rules), 25) as daily_loss_cap_usd,
  coalesce((select per_market_exposure_usd from rules), 50) as per_market_exposure_usd,
  coalesce((select slippage_bps from rules), 150) as slippage_bps,
  coalesce((select cooldown_minutes from rules), 15) as cooldown_minutes,
  coalesce((select paused from risk), false) as risk_paused,
  coalesce((select kill_switch from risk), false) as kill_switch,
  coalesce((select daily_orders_count from risk), 0) as risk_daily_orders_count,
  coalesce((select daily_loss_usd from risk), 0) as daily_loss_usd,
  coalesce((select daily_volume_usd from risk), 0) as daily_volume_usd,
  coalesce((select current_exposure_usd from risk), 0) as current_exposure_usd,
  coalesce((select orders_today from order_counts), 0) as orders_today;
"""

SQL_INSERT_ORDER = """
insert into trade.orders (
  account_id,
  market_id,
  side,
  outcome_side,
  order_type,
  status,
  source,
  requested_size_usd,
  requested_price,
  limit_price,
  slippage_bps,
  client_order_key
) values (
  %s,
  %s,
  %s,
  %s,
  %s,
  'pending',
  'manual',
  %s,
  %s,
  %s,
  %s,
  md5(random()::text || clock_timestamp()::text || %s)
)
returning id, created_at;
"""

SQL_RECENT_ORDERS = """
select
  o.id,
  o.market_id,
  o.side,
  o.outcome_side,
  o.order_type,
  o.status,
  o.requested_size_usd,
  o.limit_price,
  o.created_at,
  ev.event_type as worker_event_type,
  ev.details as worker_event_details
from trade.orders o
left join lateral (
  select e.event_type, e.details
  from trade.activity_events e
  where e.account_id = o.account_id
    and e.market_id = o.market_id
    and e.details ->> 'order_id' = o.id::text
    and e.event_type in ('order_submitted_dry_run', 'order_rejected')
  order by e.created_at desc
  limit 1
) ev on true
where o.account_id = %s
order by o.created_at desc
limit 5;
"""

SQL_POSITIONS = """
select market_id, outcome_side, size, avg_price, current_price, unrealized_pnl, updated_at
from trade.positions_cache
where account_id = %s
order by updated_at desc
limit 8;
"""

SQL_RULES = """
select enabled, paused, mode, require_confirm, max_order_usd, daily_trade_cap,
       daily_loss_cap_usd, per_market_exposure_usd, slippage_bps, cooldown_minutes,
       allowed_categories, allowlisted_markets, updated_at
from trade.agent_rules
where account_id = %s;
"""

SQL_RISK = """
select paused, kill_switch, daily_orders_count, daily_loss_usd, daily_volume_usd,
       current_exposure_usd, last_trade_at, updated_at
from trade.risk_state
where account_id = %s;
"""

SQL_DECISIONS = """
select decision_type, market_id, reason, source_rule, confidence, proposed_side,
       proposed_outcome_side, proposed_size_usd, proposed_price, created_at
from trade.agent_decisions
where account_id = %s
order by created_at desc
limit 5;
"""

SQL_UPD_RULE_MODE = "update trade.agent_rules set mode = %s, updated_at = now() where account_id = %s;"
SQL_UPD_RULE_MAX_ORDER = "update trade.agent_rules set max_order_usd = %s, updated_at = now() where account_id = %s;"
SQL_UPD_RULE_DAILY_CAP = "update trade.agent_rules set daily_trade_cap = %s, updated_at = now() where account_id = %s;"
SQL_UPD_RULE_LOSS_CAP = "update trade.agent_rules set daily_loss_cap_usd = %s, updated_at = now() where account_id = %s;"
SQL_UPD_RULE_EXPOSURE = "update trade.agent_rules set per_market_exposure_usd = %s, updated_at = now() where account_id = %s;"
SQL_UPD_RULE_SLIPPAGE = "update trade.agent_rules set slippage_bps = %s, updated_at = now() where account_id = %s;"
SQL_UPD_RULE_COOLDOWN = "update trade.agent_rules set cooldown_minutes = %s, updated_at = now() where account_id = %s;"
SQL_UPD_RULE_CONFIRM = "update trade.agent_rules set require_confirm = %s, updated_at = now() where account_id = %s;"
SQL_UPD_RULE_PAUSE = "update trade.agent_rules set paused = %s, updated_at = now() where account_id = %s;"
SQL_UPD_RISK_PAUSE = "update trade.risk_state set paused = %s, updated_at = now() where account_id = %s;"

SQL_FOLLOW_INSERT = """
insert into trade.follow_sources (
  account_id,
  source_kind,
  source_ref,
  label,
  status
) values (%s, 'wallet', %s, %s, 'active')
on conflict (account_id, source_kind, source_ref) do update
set label = excluded.label,
    status = 'active',
    updated_at = now()
returning id;
"""

SQL_FOLLOW_RULES = """
insert into trade.follow_rules (
  account_id,
  follow_source_id,
  enabled,
  copy_mode
) values (%s, %s, true, 'observe')
on conflict do nothing;
"""


def db_fetch_one(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with psycopg.connect(PG_CONN, connect_timeout=DB_CONNECT_TIMEOUT_SECONDS, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def db_fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with psycopg.connect(PG_CONN, connect_timeout=DB_CONNECT_TIMEOUT_SECONDS, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def db_execute(sql: str, params: tuple[Any, ...] = ()) -> None:
    with psycopg.connect(PG_CONN, connect_timeout=DB_CONNECT_TIMEOUT_SECONDS) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()


def db_execute_fetchone(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with psycopg.connect(PG_CONN, connect_timeout=DB_CONNECT_TIMEOUT_SECONDS, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        conn.commit()
        return row


def detect_lang(update: Update) -> str:
    code = (update.effective_user.language_code or "en").lower() if update.effective_user else "en"
    return "ru" if code.startswith("ru") else "en"


def txt(lang: str, key: str, **kwargs: Any) -> str:
    template = TEXTS[key][lang]
    return template.format(**kwargs)


def main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    labels = (
        [
            ["Markets", "Positions"],
            ["Rules", "Connect wallet"],
            ["Ready", "Agent"],
            ["Help"],
        ]
        if lang == "en"
        else [
            ["Рынки", "Позиции"],
            ["Правила", "Подключить кошелёк"],
            ["Готовность", "Агент"],
            ["Помощь"],
        ]
    )
    return ReplyKeyboardMarkup(
        labels,
        resize_keyboard=True,
    )


def links_keyboard(lang: str) -> InlineKeyboardMarkup:
    page_label = "Trader page" if lang == "en" else "Страница Trader"
    pulse_label = "Pulse signals" if lang == "en" else "Pulse сигналы"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(page_label, url=TRADER_SITE_URL)],
            [InlineKeyboardButton(pulse_label, url=PULSE_BOT_URL)],
        ]
    )


def signer_keyboard(lang: str, verify_url: str) -> InlineKeyboardMarkup:
    verify_label = "Open signer page" if lang == "en" else "Открыть signer page"
    trader_label = "Trader page" if lang == "en" else "Страница Trader"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(verify_label, url=verify_url)],
            [InlineKeyboardButton(trader_label, url=TRADER_SITE_URL)],
        ]
    )


def trade_label(lang: str, side: str, outcome: str) -> str:
    if lang == "ru":
        return ("BUY" if side == "buy" else "SELL") + f" {outcome.upper()}"
    return ("BUY" if side == "buy" else "SELL") + f" {outcome.upper()}"


def format_money(value: Any) -> str:
    if value is None:
        return "n/a"
    dec = Decimal(str(value))
    return f"{dec:.2f}".rstrip("0").rstrip(".") if dec % 1 else f"{dec:.0f}"


def resolve_identity(update: Update) -> tuple[str, int, str]:
    user = update.effective_user
    chat = update.effective_chat
    lang = detect_lang(update)
    row = db_execute_fetchone(
        SQL_RESOLVE_USER,
        (
            user.id,
            chat.id if chat else None,
            user.username,
            user.first_name,
            user.last_name,
            lang,
        ),
    )
    if not row:
        raise RuntimeError("failed to resolve trader user")
    user_id = row["user_id"]
    acc = db_execute_fetchone(SQL_ENSURE_ACCOUNT, (user_id,))
    account_id = acc["account_id"] if acc else None
    return str(user_id), int(account_id), lang


def log_event(user_id: str, account_id: int, event_type: str, details: dict[str, Any] | None = None, market_id: str | None = None) -> None:
    payload = Jsonb(details or {})
    db_execute(SQL_LOG_ACTIVITY, (user_id, account_id, event_type, TRADER_SOURCE, market_id, payload))


def parse_decimal(raw: str) -> Decimal:
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(raw) from exc


def validate_wallet(wallet: str) -> str | None:
    w = wallet.strip()
    return w if WALLET_RE.match(w) else None


def render_rules(lang: str, rules: dict[str, Any]) -> str:
    return (
        f"{txt(lang, 'rules_title')}\n\n"
        f"mode: <code>{rules['mode']}</code>\n"
        f"require_confirm: <code>{rules['require_confirm']}</code>\n"
        f"paused: <code>{rules['paused']}</code>\n"
        f"max_order_usd: <code>{format_money(rules['max_order_usd'])}</code>\n"
        f"daily_trade_cap: <code>{rules['daily_trade_cap']}</code>\n"
        f"daily_loss_cap_usd: <code>{format_money(rules['daily_loss_cap_usd'])}</code>\n"
        f"per_market_exposure_usd: <code>{format_money(rules['per_market_exposure_usd'])}</code>\n"
        f"slippage_bps: <code>{rules['slippage_bps']}</code>\n"
        f"cooldown_minutes: <code>{rules['cooldown_minutes']}</code>"
    )


def render_risk(lang: str, risk: dict[str, Any]) -> str:
    return (
        f"{txt(lang, 'risk_title')}\n\n"
        f"paused: <code>{risk['paused']}</code>\n"
        f"kill_switch: <code>{risk['kill_switch']}</code>\n"
        f"daily_orders_count: <code>{risk['daily_orders_count']}</code>\n"
        f"daily_loss_usd: <code>{format_money(risk['daily_loss_usd'])}</code>\n"
        f"daily_volume_usd: <code>{format_money(risk['daily_volume_usd'])}</code>\n"
        f"current_exposure_usd: <code>{format_money(risk['current_exposure_usd'])}</code>\n"
        f"last_trade_at: <code>{risk['last_trade_at'] or 'n/a'}</code>"
    )


def render_wallet_status(lang: str, wallet: dict[str, Any] | None) -> str:
    if not wallet:
        return "wallet: <code>missing</code>" if lang == "en" else "wallet: <code>missing</code>"
    return (
        f"wallet: <code>{wallet['wallet_address']}</code>\n"
        f"wallet_status: <code>{wallet['status']}</code> | signer: <code>{wallet['signer_kind']}</code>"
    )


def wallet_is_execution_ready(wallet: dict[str, Any] | None) -> bool:
    return bool(wallet and wallet.get("status") == "active")


def wallet_next_line(lang: str, wallet: dict[str, Any] | None) -> str:
    if wallet_is_execution_ready(wallet):
        return (
            "Execution readiness: <code>ready_for_dry_run</code>. Next: <code>/markets</code> then <code>/buy ...</code>."
            if lang == "en"
            else "Execution readiness: <code>ready_for_dry_run</code>. Дальше: <code>/markets</code>, затем <code>/buy ...</code>."
        )
    return (
        "Next blocker: signer is not active yet, so worker will reject execution until this changes. Next step: <code>/signer</code>."
        if lang == "en"
        else "Следующий блокер: signer ещё не active, поэтому worker будет отклонять execution, пока это не изменится. Следующий шаг: <code>/signer</code>."
    )


def render_readiness(lang: str, account_id: int, wallet: dict[str, Any] | None, risk: dict[str, Any], recent_orders: list[dict[str, Any]]) -> str:
    header = "<b>Execution readiness</b>" if lang == "en" else "<b>Execution readiness</b>"
    lines = [
        header,
        "",
        render_wallet_status(lang, wallet),
        wallet_next_line(lang, wallet),
        signer_status_summary(lang, account_id, wallet),
        "",
        render_risk(lang, risk),
    ]
    if recent_orders:
        latest = recent_orders[0]
        lines += [
            "",
            "<b>Latest worker state</b>" if lang == "en" else "<b>Последний worker state</b>",
            f"order: <code>#{latest['id']}</code> | status: <code>{latest['status']}</code>",
            render_order_worker_state(lang, latest),
        ]
    else:
        lines += [
            "",
            (
                "No order drafts yet. Next: <code>/markets</code> then <code>/buy market_id yes 10</code>."
                if lang == "en"
                else "Черновиков ордеров пока нет. Дальше: <code>/markets</code>, затем <code>/buy market_id yes 10</code>."
            )
        ]
    return "\n".join(lines)


def readiness_reply_markup(lang: str, account_id: int, wallet: dict[str, Any] | None) -> InlineKeyboardMarkup:
    if wallet and not wallet_is_execution_ready(wallet):
        session = ensure_signer_session(account_id, wallet)
        verify_url = signer_verify_url(session["session_token"], lang)
        return signer_keyboard(lang, verify_url)
    return links_keyboard(lang)


def worker_reason_message(lang: str, reason: str | None) -> tuple[str, str]:
    if not reason:
        return (
            ("Blocked by worker rules.", "Next: check <code>/risk</code> and <code>/rules</code>.")
            if lang == "en"
            else ("Заблокировано правилами worker.", "Дальше: проверьте <code>/risk</code> и <code>/rules</code>.")
        )
    mapping_en = {
        "missing_wallet": ("Blocked: wallet is missing.", "Next: <code>/connect 0xYourWallet</code>."),
        "kill_switch": ("Blocked: kill switch is active.", "Next: inspect <code>/risk</code>."),
        "paused": ("Blocked: account is paused.", "Next: resume via <code>/pause off</code>."),
        "max_order_exceeded": ("Blocked: order is larger than current max_order.", "Next: lower size or update <code>/rules max_order ...</code>."),
        "daily_trade_cap": ("Blocked: daily trade cap reached.", "Next: wait for reset or update <code>/rules daily_cap ...</code>."),
        "daily_loss_cap": ("Blocked: daily loss cap reached.", "Next: inspect <code>/risk</code> before trying again."),
    }
    mapping_ru = {
        "missing_wallet": ("Блокер: кошелёк не подключён.", "Дальше: <code>/connect 0xВашКошелёк</code>."),
        "kill_switch": ("Блокер: активен kill switch.", "Дальше: проверьте <code>/risk</code>."),
        "paused": ("Блокер: аккаунт на паузе.", "Дальше: снимите паузу через <code>/pause off</code>."),
        "max_order_exceeded": ("Блокер: размер ордера больше текущего max_order.", "Дальше: уменьшите размер или обновите <code>/rules max_order ...</code>."),
        "daily_trade_cap": ("Блокер: достигнут дневной trade cap.", "Дальше: дождитесь сброса или обновите <code>/rules daily_cap ...</code>."),
        "daily_loss_cap": ("Блокер: достигнут дневной loss cap.", "Дальше: сначала проверьте <code>/risk</code>."),
    }
    if reason.startswith("requires_signer:"):
        return (
            ("Blocked: signer is not active yet.", "Next: finish <code>/signer</code> and wait for approval.")
            if lang == "en"
            else ("Блокер: signer ещё не active.", "Дальше: завершите <code>/signer</code> и дождитесь активации.")
        )
    message, next_step = (mapping_en if lang == "en" else mapping_ru).get(
        reason,
        (
            ("Blocked by worker rules.", "Next: check <code>/risk</code> and <code>/rules</code>.")
            if lang == "en"
            else ("Заблокировано правилами worker.", "Дальше: проверьте <code>/risk</code> и <code>/rules</code>.")
        ),
    )
    return message, next_step


def render_order_worker_state(lang: str, row: dict[str, Any]) -> str:
    event_type = row.get("worker_event_type")
    details = row.get("worker_event_details") or {}
    if event_type == "order_submitted_dry_run":
        external_id = details.get("external_order_id")
        external_line = f"\nexternal_id: <code>{external_id}</code>" if external_id else ""
        return (
            "execution: <code>accepted_by_dry_run_worker</code>\n"
            "Next: draft passed guardrails. Real routing is still not live, so this is an alpha acceptance only."
            f"{external_line}"
            if lang == "en"
            else "execution: <code>accepted_by_dry_run_worker</code>\n"
            "Дальше: draft прошёл guardrails. Реальный routing ещё не включён, это только alpha-acceptance."
            f"{external_line}"
        )
    if event_type == "order_rejected":
        reason = details.get("reason")
        message, next_step = worker_reason_message(lang, reason)
        return (
            f"execution: <code>blocked</code>\n{message}\n{next_step}"
            + (f"\nreason: <code>{reason}</code>" if reason else "")
        )
    return (
        "execution: <code>queued_for_worker</code>\nNext: refresh <code>/order</code> in a few seconds."
        if lang == "en"
        else "execution: <code>queued_for_worker</code>\nДальше: обновите <code>/order</code> через несколько секунд."
    )


def build_signer_challenge(wallet: str, token: str) -> str:
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return (
        "Polymarket Pulse Trader signer verification\n"
        f"wallet={wallet}\n"
        f"session={token}\n"
        f"timestamp={ts}"
    )


def signer_verify_url(session_token: str, lang: str) -> str:
    join = "&" if "?" in TRADER_SIGNER_URL else "?"
    return f"{TRADER_SIGNER_URL}{join}token={session_token}&lang={lang}"


def signer_status_summary(lang: str, account_id: int, wallet: dict[str, Any] | None) -> str:
    if not wallet:
        return (
            "signer: <code>not_started</code>\nNext: connect a wallet first."
            if lang == "en"
            else "signer: <code>not_started</code>\nДальше: сначала подключите кошелёк."
        )
    session = db_fetch_one(SQL_SIGNER_SESSION_CURRENT, (account_id, wallet["id"]))
    if not session:
        return (
            "signer: <code>not_started</code>\nNext: open <code>/signer</code>."
            if lang == "en"
            else "signer: <code>not_started</code>\nДальше: откройте <code>/signer</code>."
        )
    status = str(session.get("status") or "new")
    if status == "verified":
        return (
            "signer: <code>verified</code>\nNext: signer is approved and this wallet can pass dry-run execution checks."
            if lang == "en"
            else "signer: <code>verified</code>\nДальше: signer уже одобрен, и этот кошелёк может проходить dry-run execution checks."
        )
    if status == "signed":
        return (
            "signer: <code>signed</code>\nNext: payload is captured, waiting for manual alpha approval."
            if lang == "en"
            else "signer: <code>signed</code>\nДальше: payload уже получен, ждём ручного alpha-одобрения."
        )
    if status == "opened":
        return (
            "signer: <code>opened</code>\nNext: finish the web signer step and submit the payload."
            if lang == "en"
            else "signer: <code>opened</code>\nДальше: завершите web signer step и отправьте payload."
        )
    return (
        "signer: <code>new</code>\nNext: open <code>/signer</code> and complete the signer step."
        if lang == "en"
        else "signer: <code>new</code>\nДальше: откройте <code>/signer</code> и завершите signer step."
    )


def ensure_signer_session(account_id: int, wallet: dict[str, Any]) -> dict[str, Any]:
    session = db_fetch_one(SQL_SIGNER_SESSION_CURRENT, (account_id, wallet["id"]))
    if session:
        return session
    token = secrets.token_urlsafe(24)
    challenge = build_signer_challenge(wallet["wallet_address"], token)
    return db_execute_fetchone(SQL_SIGNER_SESSION_CREATE, (account_id, wallet["id"], token, challenge))


async def maybe_send_signer_handoff(
    message,
    *,
    lang: str,
    user_id: str,
    account_id: int,
    wallet: dict[str, Any] | None,
    force: bool = False,
) -> None:
    if not wallet or wallet_is_execution_ready(wallet):
        return
    session = ensure_signer_session(account_id, wallet)
    if not force and str(session.get("status") or "") == "verified":
        return
    verify_url = signer_verify_url(session["session_token"], lang)
    log_event(
        user_id,
        account_id,
        "signer_handoff",
        {
            "wallet": wallet["wallet_address"],
            "session_token": session["session_token"],
            "status": session["status"],
            "source": "connect",
        },
    )
    handoff_text = (
        "<b>Next step: signer</b>\n\n"
        f"wallet: <code>{wallet['wallet_address']}</code>\n"
        f"signer_status: <code>{session['status']}</code>\n"
        "Open the signer page below and submit the payload there. Once the payload is captured, the wallet can move toward alpha approval."
        if lang == "en"
        else "<b>Следующий шаг: signer</b>\n\n"
        f"wallet: <code>{wallet['wallet_address']}</code>\n"
        f"signer_status: <code>{session['status']}</code>\n"
        "Откройте signer-страницу ниже и отправьте там payload. После этого кошелёк сможет перейти к alpha approval."
    )
    await message.reply_text(
        handoff_text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=signer_keyboard(lang, verify_url),
    )


def order_guard_reason(lang: str, guard: dict[str, Any], usd: Decimal) -> str | None:
    if guard["kill_switch"]:
        return "kill switch is active" if lang == "en" else "активен kill switch"
    if guard["risk_paused"] or guard["agent_paused"]:
        return "account is paused" if lang == "en" else "аккаунт на паузе"
    if usd > Decimal(str(guard["max_order_usd"])):
        return (
            f"size ${format_money(usd)} exceeds max_order ${format_money(guard['max_order_usd'])}"
            if lang == "en"
            else f"размер ${format_money(usd)} превышает max_order ${format_money(guard['max_order_usd'])}"
        )
    if int(guard["orders_today"]) >= int(guard["daily_trade_cap"]):
        return "daily trade cap reached" if lang == "en" else "дневной trade cap исчерпан"
    return None


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, account_id, lang = resolve_identity(update)
    payload = context.args[0] if context.args else None
    log_event(user_id, account_id, "start", {"entry": "start", "payload": payload})
    wallet = db_fetch_one(SQL_PRIMARY_WALLET, (account_id,))
    await update.effective_message.reply_text(
        txt(lang, "start"),
        parse_mode="HTML",
        reply_markup=main_keyboard(lang),
    )
    if wallet:
        await update.effective_message.reply_text(
            (
                "<b>Current execution readiness</b>\n\n"
                if lang == "en"
                else "<b>Текущая execution readiness</b>\n\n"
            )
            + render_wallet_status(lang, wallet)
            + "\n"
            + wallet_next_line(lang, wallet)
            + "\n"
            + signer_status_summary(lang, account_id, wallet),
            parse_mode="HTML",
            reply_markup=readiness_reply_markup(lang, account_id, wallet),
        )
    await update.effective_message.reply_text(
        txt(lang, "help"),
        parse_mode="HTML",
        reply_markup=links_keyboard(lang),
        disable_web_page_preview=True,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, account_id, lang = resolve_identity(update)
    log_event(user_id, account_id, "help_open")
    await update.effective_message.reply_text(txt(lang, "help"), parse_mode="HTML", reply_markup=main_keyboard(lang))


async def on_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text:
        return
    text = message.text.strip()
    routes = {
        "Markets": cmd_markets,
        "Рынки": cmd_markets,
        "Positions": cmd_positions,
        "Позиции": cmd_positions,
        "Rules": cmd_rules,
        "Правила": cmd_rules,
        "Connect wallet": cmd_connect,
        "Подключить кошелёк": cmd_connect,
        "Ready": cmd_ready,
        "Готовность": cmd_ready,
        "Agent": cmd_agent,
        "Агент": cmd_agent,
        "Help": cmd_help,
        "Помощь": cmd_help,
    }
    handler = routes.get(text)
    if handler is None:
        return
    await handler(update, context)


async def cmd_connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, account_id, lang = resolve_identity(update)
    args = context.args
    if not args:
        wallet = db_fetch_one(SQL_PRIMARY_WALLET, (account_id,))
        if wallet:
            await update.effective_message.reply_text(
                txt(
                    lang,
                    "connect_current",
                    wallet=wallet["wallet_address"],
                    status=wallet["status"],
                    signer_kind=wallet["signer_kind"],
                    next_line=wallet_next_line(lang, wallet),
                )
                + "\n"
                + signer_status_summary(lang, account_id, wallet),
                parse_mode="HTML",
                reply_markup=links_keyboard(lang),
            )
            await maybe_send_signer_handoff(
                update.effective_message,
                lang=lang,
                user_id=user_id,
                account_id=account_id,
                wallet=wallet,
            )
            return
        await update.effective_message.reply_text(txt(lang, "connect_usage"), parse_mode="HTML", reply_markup=links_keyboard(lang))
        return
    wallet = validate_wallet(args[0])
    if not wallet:
        await update.effective_message.reply_text(txt(lang, "invalid_wallet"), parse_mode="HTML")
        return
    db_execute(SQL_CONNECT_WALLET, (account_id, account_id, wallet, update.effective_user.full_name))
    log_event(user_id, account_id, "wallet_connect", {"wallet": wallet})
    saved = db_fetch_one(SQL_PRIMARY_WALLET, (account_id,))
    await update.effective_message.reply_text(
        txt(
            lang,
            "connect_saved",
            wallet=wallet,
            status=saved["status"] if saved else "pending",
            signer_kind=saved["signer_kind"] if saved else "delegated",
            next_line=wallet_next_line(lang, saved),
        )
        + "\n"
        + signer_status_summary(lang, account_id, saved),
        parse_mode="HTML",
    )
    await maybe_send_signer_handoff(
        update.effective_message,
        lang=lang,
        user_id=user_id,
        account_id=account_id,
        wallet=saved,
        force=True,
    )


async def cmd_ready(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, account_id, lang = resolve_identity(update)
    wallet = db_fetch_one(SQL_PRIMARY_WALLET, (account_id,))
    risk = db_fetch_one(SQL_RISK, (account_id,))
    recent_orders = db_fetch_all(SQL_RECENT_ORDERS, (account_id,))
    log_event(user_id, account_id, "ready_open", {"has_wallet": bool(wallet), "orders": len(recent_orders)})
    await update.effective_message.reply_text(
        render_readiness(lang, account_id, wallet, risk, recent_orders),
        parse_mode="HTML",
        reply_markup=readiness_reply_markup(lang, account_id, wallet),
    )


async def cmd_markets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, account_id, lang = resolve_identity(update)
    rows = db_fetch_all(SQL_TOP_MARKETS, (TOP_MARKETS_LIMIT,))
    log_event(user_id, account_id, "markets_open", {"rows": len(rows)})
    if not rows:
        await update.effective_message.reply_text(txt(lang, "markets_empty"), parse_mode="HTML")
        return
    lines = ["<b>Live trade queue</b>" if lang == "en" else "<b>Live trade queue</b>"]
    for row in rows:
        delta = Decimal(str(row["delta_yes"]))
        arrow = "+" if delta >= 0 else "-"
        lines.append(
            "\n" +
            f"<b>{row['question']}</b>\n"
            f"market: <code>{row['market_id']}</code>\n"
            f"mid: {Decimal(str(row['yes_mid_prev'])):.3f} -> {Decimal(str(row['yes_mid_now'])):.3f} | Δ {arrow}{abs(delta):.3f}\n"
            f"try: <code>/buy {row['market_id']} yes {format_money(DEFAULT_ORDER_USD)}</code>"
        )
    await update.effective_message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_signer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, account_id, lang = resolve_identity(update)
    wallet = db_fetch_one(SQL_PRIMARY_WALLET, (account_id,))
    if not wallet:
        await update.effective_message.reply_text(txt(lang, "signer_missing_wallet"), parse_mode="HTML")
        return
    session = ensure_signer_session(account_id, wallet)
    verify_url = signer_verify_url(session["session_token"], lang)
    log_event(
        user_id,
        account_id,
        "signer_session_open",
        {
            "wallet": wallet["wallet_address"],
            "session_token": session["session_token"],
            "status": session["status"],
        },
    )
    await update.effective_message.reply_text(
        txt(
            lang,
            "signer_copy",
            wallet=wallet["wallet_address"],
            status=session["status"],
            expires_at=session["expires_at"],
            challenge=session["challenge_text"],
            verify_url=verify_url,
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=signer_keyboard(lang, verify_url),
    )


async def cmd_positions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, account_id, lang = resolve_identity(update)
    rows = db_fetch_all(SQL_POSITIONS, (account_id,))
    log_event(user_id, account_id, "positions_open", {"rows": len(rows)})
    if not rows:
        await update.effective_message.reply_text(txt(lang, "positions_empty"), parse_mode="HTML")
        return
    lines = ["<b>Positions cache</b>"]
    for row in rows:
        lines.append(
            "\n"
            f"market: <code>{row['market_id']}</code>\n"
            f"side: <code>{row['outcome_side']}</code> | size: <code>{format_money(row['size'])}</code>\n"
            f"avg: <code>{format_money(row['avg_price'])}</code> | current: <code>{format_money(row['current_price'])}</code>\n"
            f"uPnL: <code>{format_money(row['unrealized_pnl'])}</code>"
        )
    await update.effective_message.reply_text("\n".join(lines), parse_mode="HTML")


async def create_order(update: Update, context: ContextTypes.DEFAULT_TYPE, side: str) -> None:
    user_id, account_id, lang = resolve_identity(update)
    args = context.args
    if len(args) < 3:
        await update.effective_message.reply_text(txt(lang, "invalid_order", side=side), parse_mode="HTML")
        return
    market_id = args[0]
    outcome = args[1].lower()
    if outcome not in {"yes", "no"}:
        await update.effective_message.reply_text(txt(lang, "invalid_order", side=side), parse_mode="HTML")
        return
    try:
        usd = parse_decimal(args[2])
        limit_price = parse_decimal(args[3]) if len(args) > 3 else None
    except ValueError:
        await update.effective_message.reply_text(txt(lang, "invalid_order", side=side), parse_mode="HTML")
        return
    market = db_fetch_one(SQL_MARKET, (market_id,))
    if not market:
        await update.effective_message.reply_text(txt(lang, "market_not_found"), parse_mode="HTML")
        return
    guard = db_fetch_one(SQL_ORDER_GUARD, (account_id, account_id, account_id)) or {}
    reason = order_guard_reason(lang, guard, usd)
    if reason:
        log_event(user_id, account_id, "order_blocked", {"market_id": market_id, "side": side, "outcome": outcome, "usd": str(usd), "reason": reason}, market_id)
        await update.effective_message.reply_text(txt(lang, "order_blocked", reason=reason), parse_mode="HTML")
        return
    order_type = "limit" if limit_price is not None else "market"
    row = db_execute_fetchone(
        SQL_INSERT_ORDER,
        (
            account_id,
            market_id,
            side,
            outcome,
            order_type,
            usd,
            limit_price,
            limit_price,
            int(guard["slippage_bps"]),
            f"{user_id}:{market_id}:{side}:{outcome}:{usd}",
        ),
    )
    log_event(
        user_id,
        account_id,
        "order_draft_created",
        {
            "order_id": row["id"] if row else None,
            "market_id": market_id,
            "side": side,
            "outcome": outcome,
            "usd": str(usd),
            "limit_price": str(limit_price) if limit_price is not None else None,
        },
        market_id,
    )
    limit_line = "" if limit_price is None else f"\nLimit: <code>{limit_price}</code>"
    wallet = db_fetch_one(SQL_PRIMARY_WALLET, (account_id,))
    await update.effective_message.reply_text(
        txt(
            lang,
            "order_saved",
            market_id=market_id,
            side=trade_label(lang, side, outcome),
            outcome=market["question"],
            usd=format_money(usd),
            order_type=order_type,
            limit_line=limit_line,
            mode=guard["mode"],
            paused=str(bool(guard["risk_paused"] or guard["agent_paused"])).lower(),
            max_order=format_money(guard["max_order_usd"]),
            next_line=wallet_next_line(lang, wallet),
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


async def cmd_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await create_order(update, context, "buy")


async def cmd_sell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await create_order(update, context, "sell")


async def cmd_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, account_id, lang = resolve_identity(update)
    rows = db_fetch_all(SQL_RECENT_ORDERS, (account_id,))
    wallet = db_fetch_one(SQL_PRIMARY_WALLET, (account_id,))
    log_event(user_id, account_id, "orders_open", {"rows": len(rows)})
    if not rows:
        await update.effective_message.reply_text(
            txt(lang, "orders_empty"),
            parse_mode="HTML",
            reply_markup=readiness_reply_markup(lang, account_id, wallet),
        )
        return
    lines = [
        "<b>Latest order drafts + worker status</b>" if lang == "en" else "<b>Последние черновики ордеров + статус worker</b>"
    ]
    for row in rows:
        limit_line = f" | limit {format_money(row['limit_price'])}" if row["limit_price"] is not None else ""
        worker_hint = "\n" + render_order_worker_state(lang, row)
        lines.append(
            "\n"
            f"#{row['id']} <code>{row['status']}</code>\n"
            f"market: <code>{row['market_id']}</code>\n"
            f"{row['side'].upper()} {row['outcome_side'].upper()} | ${format_money(row['requested_size_usd'])} | {row['order_type']}{limit_line}"
            f"{worker_hint}"
        )
    await update.effective_message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=readiness_reply_markup(lang, account_id, wallet),
    )


async def cmd_follow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, account_id, lang = resolve_identity(update)
    args = context.args
    if not args:
        await update.effective_message.reply_text(txt(lang, "follow_usage"), parse_mode="HTML")
        return
    wallet = validate_wallet(args[0])
    if not wallet:
        await update.effective_message.reply_text(txt(lang, "invalid_wallet"), parse_mode="HTML")
        return
    row = db_execute_fetchone(SQL_FOLLOW_INSERT, (account_id, wallet, f"follow:{wallet[:8]}"))
    if row:
        db_execute(SQL_FOLLOW_RULES, (account_id, row["id"]))
    log_event(user_id, account_id, "follow_source_added", {"wallet": wallet})
    await update.effective_message.reply_text(txt(lang, "follow_saved", wallet=wallet), parse_mode="HTML")


async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, account_id, lang = resolve_identity(update)
    args = context.args
    if not args:
        rules = db_fetch_one(SQL_RULES, (account_id,))
        log_event(user_id, account_id, "rules_open")
        text = render_rules(lang, rules) + "\n\n" + txt(lang, "rules_usage")
        await update.effective_message.reply_text(text, parse_mode="HTML")
        return

    field = args[0].lower()
    if len(args) < 2:
        await update.effective_message.reply_text(txt(lang, "rules_usage"), parse_mode="HTML")
        return
    raw_value = args[1].lower()

    sql = None
    value: Any = raw_value
    if field == "mode":
        value = "rule_auto" if raw_value in {"auto", "rule_auto"} else "manual"
        sql = SQL_UPD_RULE_MODE
    elif field == "max_order":
        value = parse_decimal(raw_value)
        sql = SQL_UPD_RULE_MAX_ORDER
    elif field == "daily_cap":
        value = int(raw_value)
        sql = SQL_UPD_RULE_DAILY_CAP
    elif field == "loss_cap":
        value = parse_decimal(raw_value)
        sql = SQL_UPD_RULE_LOSS_CAP
    elif field == "exposure":
        value = parse_decimal(raw_value)
        sql = SQL_UPD_RULE_EXPOSURE
    elif field == "slippage":
        value = int(raw_value)
        sql = SQL_UPD_RULE_SLIPPAGE
    elif field == "cooldown":
        value = int(raw_value)
        sql = SQL_UPD_RULE_COOLDOWN
    elif field == "confirm":
        value = raw_value in {"on", "true", "1", "yes"}
        sql = SQL_UPD_RULE_CONFIRM
    else:
        await update.effective_message.reply_text(txt(lang, "rules_usage"), parse_mode="HTML")
        return

    db_execute(sql, (value, account_id))
    log_event(user_id, account_id, "rules_updated", {"field": field, "value": str(value)})
    await update.effective_message.reply_text(txt(lang, "rules_updated", field=field, value=value), parse_mode="HTML")


async def cmd_risk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, account_id, lang = resolve_identity(update)
    risk = db_fetch_one(SQL_RISK, (account_id,))
    wallet = db_fetch_one(SQL_PRIMARY_WALLET, (account_id,))
    log_event(user_id, account_id, "risk_open")
    await update.effective_message.reply_text(
        render_risk(lang, risk)
        + "\n\n"
        + render_wallet_status(lang, wallet)
        + "\n"
        + wallet_next_line(lang, wallet)
        + "\n"
        + signer_status_summary(lang, account_id, wallet),
        parse_mode="HTML",
    )


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, account_id, lang = resolve_identity(update)
    args = context.args
    if not args or args[0].lower() not in {"on", "off"}:
        await update.effective_message.reply_text(txt(lang, "pause_usage"), parse_mode="HTML")
        return
    paused = args[0].lower() == "on"
    db_execute(SQL_UPD_RULE_PAUSE, (paused, account_id))
    db_execute(SQL_UPD_RISK_PAUSE, (paused, account_id))
    log_event(user_id, account_id, "pause_toggled", {"paused": paused})
    await update.effective_message.reply_text(txt(lang, "pause_on" if paused else "pause_off"), parse_mode="HTML")


async def cmd_agent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, account_id, lang = resolve_identity(update)
    rules = db_fetch_one(SQL_RULES, (account_id,))
    decisions = db_fetch_all(SQL_DECISIONS, (account_id,))
    log_event(user_id, account_id, "agent_open", {"decisions": len(decisions)})
    if not decisions:
        await update.effective_message.reply_text(render_rules(lang, rules) + "\n\n" + txt(lang, "agent_empty"), parse_mode="HTML")
        return
    lines = [render_rules(lang, rules), "", "<b>Latest decisions</b>"]
    for row in decisions:
        conf = "n/a" if row["confidence"] is None else f"{Decimal(str(row['confidence'])):.2f}"
        lines.append(
            "\n"
            f"{row['decision_type']} | market: <code>{row['market_id'] or 'n/a'}</code>\n"
            f"reason: {row['reason'] or 'n/a'}\n"
            f"rule: <code>{row['source_rule'] or 'n/a'}</code> | confidence: <code>{conf}</code>\n"
            f"proposal: <code>{row['proposed_side'] or '-'} {row['proposed_outcome_side'] or '-'} {format_money(row['proposed_size_usd'])}</code>"
        )
    await update.effective_message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = detect_lang(update)
    await update.effective_message.reply_text(txt(lang, "help"), parse_mode="HTML")


async def post_init(app: Application) -> None:
    commands = [
        BotCommand("start", "open trader alpha"),
        BotCommand("ready", "execution readiness"),
        BotCommand("connect", "register wallet"),
        BotCommand("signer", "open signer session"),
        BotCommand("markets", "live trade queue"),
        BotCommand("buy", "create buy draft"),
        BotCommand("sell", "create sell draft"),
        BotCommand("order", "latest order drafts"),
        BotCommand("positions", "positions cache"),
        BotCommand("follow", "follow source"),
        BotCommand("rules", "view or update rules"),
        BotCommand("risk", "risk state"),
        BotCommand("pause", "pause agent"),
        BotCommand("agent", "agent state"),
        BotCommand("help", "command list"),
    ]
    await app.bot.set_my_commands(commands)
    me = await app.bot.get_me()
    log.info("Starting trader bot polling for @%s", me.username)


def build_application() -> Application:
    app = Application.builder().token(TRADER_BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ready", cmd_ready))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("connect", cmd_connect))
    app.add_handler(CommandHandler("signer", cmd_signer))
    app.add_handler(CommandHandler("markets", cmd_markets))
    app.add_handler(CommandHandler("positions", cmd_positions))
    app.add_handler(CommandHandler("buy", cmd_buy))
    app.add_handler(CommandHandler("sell", cmd_sell))
    app.add_handler(CommandHandler("order", cmd_order))
    app.add_handler(CommandHandler("follow", cmd_follow))
    app.add_handler(CommandHandler("rules", cmd_rules))
    app.add_handler(CommandHandler("risk", cmd_risk))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("agent", cmd_agent))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_menu_text))
    return app


def main() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())
    app = build_application()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
