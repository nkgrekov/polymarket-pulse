import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

load_dotenv()

PG_CONN = os.environ["PG_CONN"]
EXECUTION_MODE = os.environ.get("EXECUTION_MODE", "dry_run")
EXECUTION_POLL_SECONDS = int(os.environ.get("EXECUTION_POLL_SECONDS", "15"))
DB_CONNECT_TIMEOUT_SECONDS = int(os.environ.get("DB_CONNECT_TIMEOUT_SECONDS", "10"))
WORKER_BATCH_LIMIT = int(os.environ.get("WORKER_BATCH_LIMIT", "25"))
WORKER_SOURCE = os.environ.get("WORKER_SOURCE", "worker")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("polymarket_pulse_trade_worker")

SQL_PENDING_ORDERS = """
select
  o.id,
  o.account_id,
  a.user_id,
  o.market_id,
  o.side,
  o.outcome_side,
  o.order_type,
  o.status,
  o.requested_size_usd,
  o.requested_price,
  o.limit_price,
  o.slippage_bps,
  o.client_order_key,
  o.created_at,
  r.paused as risk_paused,
  r.kill_switch,
  r.daily_orders_count,
  r.daily_loss_usd,
  r.current_exposure_usd,
  ar.mode,
  ar.require_confirm,
  ar.paused as agent_paused,
  ar.max_order_usd,
  ar.daily_trade_cap,
  ar.daily_loss_cap_usd,
  ar.per_market_exposure_usd,
  ar.slippage_bps as rule_slippage_bps,
  ar.cooldown_minutes,
  ar.allowlisted_markets,
  wl.wallet_address,
  wl.status as wallet_status,
  wl.signer_kind
from trade.orders o
join trade.accounts a on a.id = o.account_id
left join trade.risk_state r on r.account_id = o.account_id
left join trade.agent_rules ar on ar.account_id = o.account_id
left join lateral (
  select wallet_address, status, signer_kind
  from trade.wallet_links
  where account_id = o.account_id
    and is_primary = true
  order by updated_at desc, created_at desc
  limit 1
) wl on true
where o.status = 'pending'
order by o.created_at asc
limit %s;
"""

SQL_UPDATE_ORDER_SUBMITTED = """
update trade.orders
set status = 'submitted',
    external_order_id = %s,
    updated_at = now()
where id = %s;
"""

SQL_UPDATE_ORDER_REJECTED = """
update trade.orders
set status = 'rejected',
    updated_at = now()
where id = %s;
"""

SQL_INSERT_ACTIVITY = """
insert into trade.activity_events (
  user_id,
  account_id,
  event_type,
  source,
  market_id,
  details
) values (%s::uuid, %s, %s, %s, %s, %s::jsonb);
"""

SQL_BUMP_RISK = """
update trade.risk_state
set daily_orders_count = daily_orders_count + 1,
    daily_volume_usd = daily_volume_usd + %s,
    last_trade_at = now(),
    updated_at = now()
where account_id = %s;
"""


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


def log_event(user_id: str, account_id: int, event_type: str, market_id: str | None, details: dict[str, Any]) -> None:
    db_execute(SQL_INSERT_ACTIVITY, (user_id, account_id, event_type, WORKER_SOURCE, market_id, Jsonb(details)))


def rejection_reason(row: dict[str, Any]) -> str | None:
    wallet_status = row.get("wallet_status")
    if not row.get("wallet_address"):
        return "missing_wallet"
    if wallet_status != "active":
        return f"requires_signer:{wallet_status or 'unknown'}"
    if row.get("kill_switch"):
        return "kill_switch"
    if row.get("risk_paused") or row.get("agent_paused"):
        return "paused"
    if row.get("requested_size_usd") is not None and row.get("max_order_usd") is not None:
        if row["requested_size_usd"] > row["max_order_usd"]:
            return "max_order_exceeded"
    if row.get("daily_orders_count") is not None and row.get("daily_trade_cap") is not None:
        if row["daily_orders_count"] >= row["daily_trade_cap"]:
            return "daily_trade_cap"
    if row.get("daily_loss_usd") is not None and row.get("daily_loss_cap_usd") is not None:
        if row["daily_loss_usd"] >= row["daily_loss_cap_usd"]:
            return "daily_loss_cap"
    return None


def process_order(row: dict[str, Any]) -> None:
    order_id = row["id"]
    user_id = str(row["user_id"])
    account_id = row["account_id"]
    market_id = row["market_id"]
    reason = rejection_reason(row)

    if reason:
        db_execute(SQL_UPDATE_ORDER_REJECTED, (order_id,))
        log_event(
            user_id,
            account_id,
            "order_rejected",
            market_id,
            {
                "order_id": order_id,
                "reason": reason,
                "execution_mode": EXECUTION_MODE,
            },
        )
        log.info("order=%s rejected reason=%s", order_id, reason)
        return

    external_order_id = f"dryrun:{order_id}:{int(time.time())}"
    db_execute(SQL_UPDATE_ORDER_SUBMITTED, (external_order_id, order_id))
    db_execute(SQL_BUMP_RISK, (row["requested_size_usd"], account_id))
    log_event(
        user_id,
        account_id,
        "order_submitted_dry_run",
        market_id,
        {
            "order_id": order_id,
            "external_order_id": external_order_id,
            "side": row["side"],
            "outcome_side": row["outcome_side"],
            "requested_size_usd": str(row["requested_size_usd"]),
            "order_type": row["order_type"],
            "execution_mode": EXECUTION_MODE,
        },
    )
    log.info("order=%s submitted dry_run external_id=%s", order_id, external_order_id)


def run_once() -> int:
    rows = db_fetch_all(SQL_PENDING_ORDERS, (WORKER_BATCH_LIMIT,))
    if not rows:
        log.info("no pending orders")
        return 0
    for row in rows:
        process_order(row)
    return len(rows)


def main() -> None:
    log.info("starting trade worker mode=%s poll=%ss batch_limit=%s", EXECUTION_MODE, EXECUTION_POLL_SECONDS, WORKER_BATCH_LIMIT)
    while True:
        try:
            processed = run_once()
            if processed == 0:
                time.sleep(EXECUTION_POLL_SECONDS)
            else:
                time.sleep(2)
        except KeyboardInterrupt:
            raise
        except Exception:
            log.exception("trade worker loop failed")
            time.sleep(min(EXECUTION_POLL_SECONDS, 15))


if __name__ == "__main__":
    main()
