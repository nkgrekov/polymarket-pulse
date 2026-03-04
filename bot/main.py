import asyncio
import logging
import os
import time
from decimal import Decimal, InvalidOperation
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
PG_CONN = os.environ["PG_CONN"]
DEFAULT_USER_ID = os.environ.get("USER_ID", "nikita")
DEFAULT_TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
PUSH_INTERVAL_SECONDS = int(os.environ.get("PUSH_INTERVAL_SECONDS", "300"))
PUSH_FETCH_LIMIT = int(os.environ.get("PUSH_FETCH_LIMIT", "20"))
DB_CONNECT_TIMEOUT_SECONDS = int(os.environ.get("DB_CONNECT_TIMEOUT_SECONDS", "10"))
DB_RETRY_ATTEMPTS = int(os.environ.get("DB_RETRY_ATTEMPTS", "3"))
DB_RETRY_SLEEP_SECONDS = float(os.environ.get("DB_RETRY_SLEEP_SECONDS", "1.5"))
PUSH_INITIAL_DELAY_SECONDS = int(os.environ.get("PUSH_INITIAL_DELAY_SECONDS", "20"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("polymarket_pulse_bot")

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
from public.alerts_inbox_latest
where user_id = %s
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

SQL_WATCHLIST_MOVERS = """
with lb as (
  select last_bucket
  from public.global_bucket_latest
),
prev as (
  select max(ms.ts_bucket) as prev_bucket
  from public.market_snapshots ms
  join lb on true
  where ms.ts_bucket < lb.last_bucket
),
wl as (
  select distinct market_id
  from public.user_watchlist
  where user_id = %s
),
last_rows as (
  select
    ms.market_id,
    max(((ms.yes_bid + ms.yes_ask) / 2::numeric)) as yes_mid_now
  from public.market_snapshots ms
  join lb on ms.ts_bucket = lb.last_bucket
  join wl on wl.market_id = ms.market_id
  group by ms.market_id
),
prev_rows as (
  select
    ms.market_id,
    max(((ms.yes_bid + ms.yes_ask) / 2::numeric)) as yes_mid_prev
  from public.market_snapshots ms
  join prev on ms.ts_bucket = prev.prev_bucket
  join wl on wl.market_id = ms.market_id
  group by ms.market_id
)
select
  l.market_id,
  m.question,
  (select last_bucket from lb) as last_bucket,
  (select prev_bucket from prev) as prev_bucket,
  l.yes_mid_now,
  p.yes_mid_prev,
  (l.yes_mid_now - p.yes_mid_prev) as delta_yes
from last_rows l
join prev_rows p using (market_id)
join public.markets m on m.market_id = l.market_id
where l.yes_mid_now is not null
  and p.yes_mid_prev is not null
order by abs(l.yes_mid_now - p.yes_mid_prev) desc nulls last
limit %s;
"""

SQL_SENT_ALERT_EXISTS = """
select 1
from public.sent_alerts_log
where user_id = %s
  and market_id = %s
  and alert_type = %s
  and last_bucket = %s;
"""

SQL_SENT_ALERT_INSERT = """
insert into public.sent_alerts_log (
  user_id,
  market_id,
  alert_type,
  last_bucket
)
values (%s, %s, %s, %s)
on conflict (user_id, market_id, alert_type, last_bucket) do nothing;
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


def fetch_inbox(user_id: str, limit: int = 10) -> list[dict]:
    return run_db_query(SQL_INBOX, (user_id, limit), row_factory=dict_row)

def fetch_top_movers(limit: int = 3) -> list[dict]:
    return run_db_query(SQL_TOP_MOVERS, (limit,), row_factory=dict_row)

def fetch_watchlist_movers(user_id: str, limit: int = 10) -> list[dict]:
    return run_db_query(SQL_WATCHLIST_MOVERS, (user_id, limit), row_factory=dict_row)


async def fetch_inbox_async(user_id: str, limit: int = 10, timeout_sec: float = 10.0) -> list[dict]:
    return await asyncio.wait_for(
        asyncio.to_thread(fetch_inbox, user_id, limit),
        timeout=timeout_sec,
    )

async def fetch_top_movers_async(limit: int = 3, timeout_sec: float = 10.0) -> list[dict]:
    return await asyncio.wait_for(
        asyncio.to_thread(fetch_top_movers, limit),
        timeout=timeout_sec,
    )

async def fetch_watchlist_movers_async(user_id: str, limit: int = 10, timeout_sec: float = 10.0) -> list[dict]:
    return await asyncio.wait_for(
        asyncio.to_thread(fetch_watchlist_movers, user_id, limit),
        timeout=timeout_sec,
    )


def _fmt_num(value: object, digits: int, signed: bool = False) -> str:
    if value is None:
        return "n/a"
    try:
        num = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return "n/a"
    pattern = f"{{:{'+' if signed else ''}.{digits}f}}"
    return pattern.format(num)


def fmt_row(row: dict) -> str:
    question = (row.get("question") or "n/a").strip()
    alert_type = row.get("alert_type") or "alert"
    return (
        f"• [{alert_type}] {question}\n"
        f"  market_id: {row.get('market_id')} | side: {row.get('side') or '-'}\n"
        f"  mid: {_fmt_num(row.get('mid_now'), 3)} (prev {_fmt_num(row.get('mid_prev'), 3)})"
        f" | Δ {_fmt_num(row.get('delta_mid'), 3, signed=True)}"
        f" | PnL {_fmt_num(row.get('pnl'), 2, signed=True)}\n"
        f"  bucket: {row.get('last_bucket')} (prev {row.get('prev_bucket')})"
    )

def fmt_mover_row(row: dict) -> str:
    question = (row.get("question") or "n/a").strip()
    return (
        f"• {question}\n"
        f"  market_id: {row.get('market_id')}\n"
        f"  mid: {_fmt_num(row.get('yes_mid_now'), 3)} (prev {_fmt_num(row.get('yes_mid_prev'), 3)})"
        f" | Δ {_fmt_num(row.get('delta_yes'), 3, signed=True)}\n"
        f"  bucket: {row.get('last_bucket')} (prev {row.get('prev_bucket')})"
    )


def is_alert_sent(user_id: str, market_id: str, alert_type: str, last_bucket: Any) -> bool:
    rows = run_db_query(SQL_SENT_ALERT_EXISTS, (user_id, market_id, alert_type, last_bucket))
    return bool(rows)


def mark_alert_sent(user_id: str, market_id: str, alert_type: str, last_bucket: Any) -> None:
    execute_db_write(SQL_SENT_ALERT_INSERT, (user_id, market_id, alert_type, last_bucket))


async def is_alert_sent_async(row: dict) -> bool:
    return await asyncio.to_thread(
        is_alert_sent,
        row["user_id"],
        str(row["market_id"]),
        row["alert_type"],
        row["last_bucket"],
    )


async def mark_alert_sent_async(row: dict) -> None:
    await asyncio.to_thread(
        mark_alert_sent,
        row["user_id"],
        str(row["market_id"]),
        row["alert_type"],
        row["last_bucket"],
    )


async def dispatch_push_alerts(application: Application) -> None:
    if not DEFAULT_TELEGRAM_CHAT_ID:
        return

    rows = await fetch_inbox_async(DEFAULT_USER_ID, limit=PUSH_FETCH_LIMIT, timeout_sec=15.0)
    if not rows:
        return

    sent_count = 0
    for row in rows:
        if await is_alert_sent_async(row):
            continue
        await application.bot.send_message(
            chat_id=DEFAULT_TELEGRAM_CHAT_ID,
            text="Push alert:\n\n" + fmt_row(row),
        )
        await mark_alert_sent_async(row)
        sent_count += 1
        log.info(
            "push_sent user_id=%s market_id=%s alert_type=%s last_bucket=%s",
            row["user_id"],
            row["market_id"],
            row["alert_type"],
            row["last_bucket"],
        )

    if sent_count:
        log.info("push_loop delivered=%s", sent_count)


async def push_loop(application: Application) -> None:
    if not DEFAULT_TELEGRAM_CHAT_ID:
        log.warning("push_loop disabled: TELEGRAM_CHAT_ID is not set")
        return

    log.info(
        "push_loop started user_id=%s chat_id=%s interval=%ss",
        DEFAULT_USER_ID,
        DEFAULT_TELEGRAM_CHAT_ID,
        PUSH_INTERVAL_SECONDS,
    )
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    log.info("cmd=/start chat_id=%s user_id=%s", update.effective_chat.id, update.effective_user.id if update.effective_user else None)
    await update.message.reply_text(
        "Bot is live.\n"
        "Commands:\n"
        "/inbox - latest alerts (10)\n"
        "/inbox20 - latest alerts (20)\n"
        "/movers - top live movers (up to 3)\n"
        "/watchlist - live changes for your watchlist"
    )


async def inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    log.info("cmd=/inbox chat_id=%s user_id=%s", update.effective_chat.id, update.effective_user.id if update.effective_user else None)
    await update.message.reply_text("Ищу алерты, это займет пару секунд...")
    try:
        rows = await fetch_inbox_async(DEFAULT_USER_ID, limit=10, timeout_sec=10.0)
    except asyncio.TimeoutError:
        await update.message.reply_text("База ответила слишком долго. Попробуйте /inbox еще раз через 10-20 секунд.")
        return
    except Exception:
        await update.message.reply_text("Ошибка при чтении алертов из БД. Проверьте PG_CONN и доступность Supabase.")
        return
    if not rows:
        await update.message.reply_text("Нет алертов по текущему порогу за последний интервал.")
        return
    text = "Latest alerts:\n\n" + "\n\n".join(fmt_row(r) for r in rows)
    await update.message.reply_text(text)


async def inbox20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    log.info("cmd=/inbox20 chat_id=%s user_id=%s", update.effective_chat.id, update.effective_user.id if update.effective_user else None)
    await update.message.reply_text("Ищу алерты, это займет пару секунд...")
    try:
        rows = await fetch_inbox_async(DEFAULT_USER_ID, limit=20, timeout_sec=10.0)
    except asyncio.TimeoutError:
        await update.message.reply_text("База ответила слишком долго. Попробуйте /inbox20 еще раз через 10-20 секунд.")
        return
    except Exception:
        await update.message.reply_text("Ошибка при чтении алертов из БД. Проверьте PG_CONN и доступность Supabase.")
        return
    if not rows:
        await update.message.reply_text("Нет алертов по текущему порогу за последний интервал.")
        return
    text = "Latest alerts (20):\n\n" + "\n\n".join(fmt_row(r) for r in rows)
    await update.message.reply_text(text)

async def movers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    log.info("cmd=/movers chat_id=%s user_id=%s", update.effective_chat.id, update.effective_user.id if update.effective_user else None)
    await update.message.reply_text("Смотрю top movers, это займет пару секунд...")
    try:
        rows = await fetch_top_movers_async(limit=3, timeout_sec=10.0)
    except asyncio.TimeoutError:
        await update.message.reply_text("База ответила слишком долго. Попробуйте /movers еще раз через 10-20 секунд.")
        return
    except Exception:
        await update.message.reply_text("Ошибка при чтении movers из БД. Проверьте Supabase.")
        return
    if not rows:
        await update.message.reply_text("Сейчас нет live movers: не накопилась пара bucket для market_universe.")
        return
    text = "Top live movers (up to 3):\n\n" + "\n\n".join(fmt_mover_row(r) for r in rows)
    await update.message.reply_text(text)

async def watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    log.info("cmd=/watchlist chat_id=%s user_id=%s", update.effective_chat.id, update.effective_user.id if update.effective_user else None)
    await update.message.reply_text("Смотрю live изменения по watchlist, это займет пару секунд...")
    try:
        rows = await fetch_watchlist_movers_async(DEFAULT_USER_ID, limit=10, timeout_sec=10.0)
    except asyncio.TimeoutError:
        await update.message.reply_text("База ответила слишком долго. Попробуйте /watchlist еще раз через 10-20 секунд.")
        return
    except Exception:
        await update.message.reply_text("Ошибка при чтении watchlist из БД. Проверьте Supabase.")
        return
    if not rows:
        await update.message.reply_text("По вашему watchlist сейчас нет live-изменений между последним и предыдущим bucket.")
        return
    text = "Watchlist live changes:\n\n" + "\n\n".join(fmt_mover_row(r) for r in rows)
    await update.message.reply_text(text)


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    log.info("cmd=unknown text=%s chat_id=%s user_id=%s", update.message.text, update.effective_chat.id, update.effective_user.id if update.effective_user else None)
    await update.message.reply_text("Unknown command. Try /start, /inbox, /inbox20")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled bot error. update=%s", update, exc_info=context.error)


async def on_post_init(application: Application):
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Show help"),
            BotCommand("inbox", "Latest alerts (10)"),
            BotCommand("inbox20", "Latest alerts (20)"),
            BotCommand("movers", "Top live movers (up to 3)"),
            BotCommand("watchlist", "Live changes for your watchlist"),
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
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("inbox", inbox))
    app.add_handler(CommandHandler("inbox20", inbox20))
    app.add_handler(CommandHandler("movers", movers))
    app.add_handler(CommandHandler("watchlist", watchlist))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    log.info("Starting bot polling for @polymarket_pulse_bot")
    app.run_polling(drop_pending_updates=True)
