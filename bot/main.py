import asyncio
import logging
import os
import time
from decimal import Decimal, InvalidOperation
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

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
    where w.user_id = p.user_id
  ) as watchlist_count,
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
select
  market_id,
  question,
  last_bucket,
  prev_bucket,
  yes_mid_now,
  yes_mid_prev,
  delta_yes
from public.top_movers_latest
where abs(delta_yes) > 0
order by abs(delta_yes) desc nulls last
limit %s;
"""

SQL_TOP_MOVERS_1H = """
select
  market_id,
  question,
  ts_now as last_bucket,
  ts_prev as prev_bucket,
  yes_mid_now,
  yes_mid_1h as yes_mid_prev,
  delta_yes_1h as delta_yes
from public.top_movers_1h
where abs(delta_yes_1h) > 0
order by abs(delta_yes_1h) desc nulls last
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

SQL_WATCHLIST_LIST = """
select w.market_id, m.question, w.created_at
from bot.watchlist w
join public.markets m on m.market_id = w.market_id
where w.user_id = %s::uuid
order by w.created_at desc
limit %s;
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


def user_limits_block(user_ctx: dict) -> str:
    plan = str(user_ctx.get("plan") or "free")
    watchlist_count = int(user_ctx.get("watchlist_count") or 0)
    alerts_today = int(user_ctx.get("alerts_sent_today") or 0)
    threshold = _fmt_num(user_ctx.get("threshold"), 3)
    if plan == "pro":
        return (
            "План: PRO\n"
            f"Threshold: {threshold}\n"
            f"Watchlist: {watchlist_count} (без лимита)\n"
            f"Alerts today: {alerts_today} (без лимита)"
        )
    return (
        "План: FREE\n"
        f"Threshold: {threshold}\n"
        f"Watchlist: {watchlist_count}/{FREE_WATCHLIST_LIMIT}\n"
        f"Alerts today: {alerts_today}/{FREE_DAILY_ALERT_LIMIT}"
    )


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


async def fetch_watchlist_snapshot_async(user_id: str, limit: int = 10, timeout_sec: float = 10.0) -> list[dict]:
    return await asyncio.wait_for(
        asyncio.to_thread(lambda: run_db_query(SQL_WATCHLIST_SNAPSHOT, (user_id, limit), row_factory=dict_row)),
        timeout=timeout_sec,
    )


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
    try:
        user_ctx = await resolve_user_context(update)
    except Exception:
        log.exception("/start resolve_user failed")
        await update.message.reply_text("Не удалось инициализировать профиль. Попробуйте позже.")
        return

    await update.message.reply_text(
        "Профиль активирован.\n\n"
        "Что бот делает:\n"
        "• показывает top live movers\n"
        "• отслеживает ваши рынки в watchlist\n"
        "• присылает push по движению вероятностей\n\n"
        "Быстрый старт за 60 секунд:\n"
        "1) /movers — посмотреть 3 live движения\n"
        "2) /watchlist_add <market_id|slug> — добавить рынок\n"
        "3) /watchlist — увидеть live-дельту по вашему списку\n"
        "4) /threshold 0.03 — настроить чувствительность\n\n"
        f"{user_limits_block(user_ctx)}\n\n"
        "Полезно дальше:\n"
        "/help — все команды\n"
        "/limits — текущие лимиты\n"
        "/upgrade — как перейти на PRO"
    )
    log.info("cmd=/start chat_id=%s tg_user=%s app_user=%s", update.effective_chat.id, update.effective_user.id, user_ctx["user_id"])


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text(
        "Команды бота:\n\n"
        "Онбординг и план:\n"
        "/start — активация профиля и быстрый старт\n"
        "/plan — ваш план, threshold и usage\n"
        "/limits — лимиты FREE/PRO\n"
        "/upgrade — переход на PRO\n\n"
        "Сигналы:\n"
        "/movers — top 3 live movers\n"
        "/inbox — последние алерты\n"
        "/inbox20 — расширенный inbox\n\n"
        "Watchlist:\n"
        "/watchlist_list — ваш список рынков\n"
        "/watchlist_add <market_id|slug>\n"
        "/watchlist_remove <market_id|slug>\n"
        "/watchlist — live изменения по вашему списку\n\n"
        "Настройка чувствительности:\n"
        "/threshold 0.03"
    )


async def cmd_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    try:
        user_ctx = await resolve_user_context(update)
    except Exception:
        await update.message.reply_text("Не удалось прочитать профиль.")
        return

    await update.message.reply_text(
        "Текущий статус:\n"
        f"{user_limits_block(user_ctx)}\n\n"
        "Изменить порог: /threshold 0.03\n"
        "Смотреть лимиты: /limits\n"
        "Переход на PRO: /upgrade"
    )


async def cmd_limits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    try:
        user_ctx = await resolve_user_context(update)
    except Exception:
        await update.message.reply_text("Не удалось прочитать лимиты.")
        return

    await update.message.reply_text(
        "Лимиты и доступ:\n\n"
        "FREE:\n"
        f"• до {FREE_WATCHLIST_LIMIT} рынков в watchlist\n"
        f"• до {FREE_DAILY_ALERT_LIMIT} push-алертов в день\n\n"
        "PRO:\n"
        "• watchlist без лимита\n"
        "• push-алерты без лимита\n\n"
        f"Ваш текущий usage:\n{user_limits_block(user_ctx)}\n\n"
        "Чтобы перейти на PRO: /upgrade"
    )


async def cmd_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user_ctx = await resolve_user_context(update)
    try:
        await asyncio.to_thread(log_upgrade_intent_sync, update, user_ctx)
    except Exception:
        log.exception("/upgrade intent insert failed")
    await update.message.reply_text(
        "Переход на PRO:\n"
        "1) Откройте сайт: https://polymarketpulse.app/?lang=ru\n"
        "2) Оставьте email в waitlist (если ещё не оставляли)\n"
        "3) Напишите сюда \"хочу PRO\" — мы активируем доступ на вашем user_id\n\n"
        "Скоро добавим self-serve оплату прямо в боте."
    )


async def cmd_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if not context.args:
        user_ctx = await resolve_user_context(update)
        await update.message.reply_text(
            f"Ваш текущий порог: {_fmt_num(user_ctx['threshold'], 3)}\n"
            "Формат изменения: /threshold 0.03"
        )
        return
    try:
        value = Decimal(context.args[0])
    except Exception:
        await update.message.reply_text("Некорректное значение. Пример: /threshold 0.03")
        return

    if value < 0 or value > 1:
        await update.message.reply_text("Порог должен быть в диапазоне 0..1")
        return

    user_ctx = await resolve_user_context(update)
    execute_db_write(SQL_SET_THRESHOLD, (user_ctx["user_id"], value))
    await update.message.reply_text(f"Порог обновлен: {_fmt_num(value, 3)}")


async def cmd_movers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text("Смотрю live movers...")
    try:
        rows = await fetch_top_movers_async(limit=3, timeout_sec=10.0)
    except asyncio.TimeoutError:
        await update.message.reply_text("База отвечает слишком долго. Повторите через 10-20 секунд.")
        return
    except Exception:
        log.exception("/movers failed")
        await update.message.reply_text("Ошибка чтения movers из БД.")
        return

    if rows:
        await update.message.reply_text("Top live movers (up to 3):\n\n" + "\n\n".join(fmt_mover_row(r) for r in rows))
        return

    # Fallback to 1h movers so UX is not dead in flat short-window periods.
    try:
        rows_1h = await fetch_top_movers_1h_async(limit=3, timeout_sec=10.0)
    except Exception:
        rows_1h = []

    if rows_1h:
        await update.message.reply_text(
            "В текущем окне last/prev движение плоское. Показываю 1h movers:\n\n"
            + "\n\n".join(fmt_mover_row(r) for r in rows_1h)
        )
        return

    await update.message.reply_text("Сейчас нет ненулевых live movers ни в текущем окне last/prev, ни в 1h окне.")


async def cmd_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE, limit: int = 10):
    if not update.message:
        return
    user_ctx = await resolve_user_context(update)
    await update.message.reply_text("Читаю ваш inbox...")
    try:
        rows = await fetch_inbox_async(user_ctx["user_id"], limit=limit, timeout_sec=10.0)
    except asyncio.TimeoutError:
        await update.message.reply_text("База отвечает слишком долго. Повторите через 10-20 секунд.")
        return
    except Exception:
        log.exception("/inbox failed")
        await update.message.reply_text("Ошибка чтения inbox из БД.")
        return

    if not rows:
        await update.message.reply_text("Нет алертов по вашему порогу в текущем окне.")
        return

    header = "Inbox alerts:" if limit == 10 else "Inbox alerts (20):"
    await update.message.reply_text(header + "\n\n" + "\n\n".join(fmt_alert_row(r) for r in rows))


async def cmd_inbox10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_inbox(update, context, limit=10)


async def cmd_inbox20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_inbox(update, context, limit=20)


async def cmd_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user_ctx = await resolve_user_context(update)
    await update.message.reply_text("Смотрю live изменения вашего watchlist...")
    try:
        rows = await fetch_watchlist_snapshot_async(user_ctx["user_id"], limit=10, timeout_sec=10.0)
    except asyncio.TimeoutError:
        await update.message.reply_text("База отвечает слишком долго. Повторите через 10-20 секунд.")
        return
    except Exception:
        log.exception("/watchlist failed")
        await update.message.reply_text("Ошибка чтения watchlist из БД.")
        return

    if not rows:
        await update.message.reply_text("По вашему watchlist сейчас нет live-изменений.")
        return

    await update.message.reply_text("Watchlist live changes:\n\n" + "\n\n".join(fmt_mover_row(r) for r in rows))


async def cmd_watchlist_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user_ctx = await resolve_user_context(update)
    rows = run_db_query(SQL_WATCHLIST_LIST, (user_ctx["user_id"], 50), row_factory=dict_row)
    if not rows:
        await update.message.reply_text("Ваш watchlist пуст. Используйте /watchlist_add <market_id|slug>.")
        return

    lines = []
    for idx, row in enumerate(rows, start=1):
        lines.append(f"{idx}. {row['market_id']} — {row['question']}")
    await update.message.reply_text("Ваш watchlist:\n" + "\n".join(lines))


async def cmd_watchlist_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if not context.args:
        await update.message.reply_text(
            "Формат: /watchlist_add <market_id|slug>\n"
            "Подсказка: сначала откройте /movers и скопируйте market_id нужного рынка."
        )
        return

    ref = context.args[0].strip()
    user_ctx = await resolve_user_context(update)

    market_rows = run_db_query(SQL_FIND_MARKET, (ref, ref), row_factory=dict_row)
    if not market_rows:
        await update.message.reply_text("Рынок не найден. Укажите market_id или slug.")
        return

    market = market_rows[0]
    market_id = str(market["market_id"])

    exists = bool(run_db_query(SQL_WATCHLIST_EXISTS, (user_ctx["user_id"], market_id)))
    if exists:
        await update.message.reply_text("Этот рынок уже в вашем watchlist.")
        return

    if user_ctx["plan"] == "free" and int(user_ctx["watchlist_count"]) >= FREE_WATCHLIST_LIMIT:
        await update.message.reply_text(
            f"Лимит FREE: {FREE_WATCHLIST_LIMIT} рынка. Удалите один через /watchlist_remove или перейдите на PRO: /upgrade"
        )
        return

    execute_db_write(SQL_WATCHLIST_ADD, (user_ctx["user_id"], market_id))
    await update.message.reply_text(f"Добавлено в watchlist: {market_id} — {market['question']}")


async def cmd_watchlist_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if not context.args:
        await update.message.reply_text("Формат: /watchlist_remove <market_id|slug>")
        return

    ref = context.args[0].strip()
    user_ctx = await resolve_user_context(update)

    market_rows = run_db_query(SQL_FIND_MARKET, (ref, ref), row_factory=dict_row)
    market_id = ref if not market_rows else str(market_rows[0]["market_id"])
    execute_db_write(SQL_WATCHLIST_REMOVE, (user_ctx["user_id"], market_id))
    await update.message.reply_text(f"Удалено из watchlist: {market_id}")


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
    await update.message.reply_text(
        "Неизвестная команда.\n"
        "Используйте /help.\n"
        "Быстрый старт: /movers, /watchlist_add, /watchlist, /inbox"
    )


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled bot error. update=%s", update, exc_info=context.error)


async def on_post_init(application: Application):
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Онбординг и профиль"),
            BotCommand("help", "Список команд"),
            BotCommand("plan", "Текущий план и лимиты"),
            BotCommand("limits", "Лимиты Free/Pro"),
            BotCommand("upgrade", "Как перейти на Pro"),
            BotCommand("threshold", "Порог алертов"),
            BotCommand("movers", "Top live movers"),
            BotCommand("inbox", "Последние алерты"),
            BotCommand("watchlist", "Live изменения watchlist"),
            BotCommand("watchlist_list", "Показать watchlist"),
            BotCommand("watchlist_add", "Добавить рынок"),
            BotCommand("watchlist_remove", "Удалить рынок"),
        ]
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
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("plan", cmd_plan))
    app.add_handler(CommandHandler("limits", cmd_limits))
    app.add_handler(CommandHandler("upgrade", cmd_upgrade))
    app.add_handler(CommandHandler("threshold", cmd_threshold))
    app.add_handler(CommandHandler("movers", cmd_movers))
    app.add_handler(CommandHandler("inbox", cmd_inbox10))
    app.add_handler(CommandHandler("inbox20", cmd_inbox20))
    app.add_handler(CommandHandler("watchlist", cmd_watchlist))
    app.add_handler(CommandHandler("watchlist_list", cmd_watchlist_list))
    app.add_handler(CommandHandler("watchlist_add", cmd_watchlist_add))
    app.add_handler(CommandHandler("watchlist_remove", cmd_watchlist_remove))
    app.add_handler(CommandHandler("admin_stats", cmd_admin_stats))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    log.info("Starting bot polling for @polymarket_pulse_bot")
    app.run_polling(drop_pending_updates=True)
