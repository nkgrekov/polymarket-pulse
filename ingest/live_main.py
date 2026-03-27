import os
from datetime import datetime, timezone
import math

import psycopg2
from psycopg2.extras import execute_batch

from main import (
    GAMMA_MARKET_BY_ID,
    SESSION,
    fetch_best_bid_ask,
    fetch_bot_watchlist_market_ids,
    fetch_market_universe_ids,
    fetch_markets,
    fetch_position_market_ids,
    fetch_stored_market_rows,
    fetch_watchlist_market_ids,
    load_env,
    normalize_market_row,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _compute_mid(bid: float | None, ask: float | None) -> float | None:
    if bid is None or ask is None:
        return None
    return (float(bid) + float(ask)) / 2.0


def _compute_spread(bid: float | None, ask: float | None) -> float | None:
    if bid is None or ask is None:
        return None
    return max(float(ask) - float(bid), 0.0)


def _score_delta(delta_mid: float, liquidity: float) -> float:
    return abs(float(delta_mid)) * 100.0 + math.log1p(max(float(liquidity), 0.0))


def _fetch_market_detail(market_id: str) -> dict | None:
    try:
        r = SESSION.get(GAMMA_MARKET_BY_ID.format(market_id), timeout=30)
        r.raise_for_status()
        return normalize_market_row(r.json())
    except Exception as exc:
        print(f"WARN: live forced fetch failed for {market_id}: {exc}")
        return None


def _load_forced_ids(pg_conn: str, watch_user: str, universe_limit: int, bot_wl_limit: int) -> tuple[list[str], list[str], list[str]]:
    conn = psycopg2.connect(pg_conn)
    try:
        manual_legacy_ids = fetch_watchlist_market_ids(conn, watch_user)
        manual_bot_ids = fetch_bot_watchlist_market_ids(conn, limit=bot_wl_limit)
        manual_ids = list(dict.fromkeys([*manual_legacy_ids, *manual_bot_ids]))
        universe_ids = fetch_market_universe_ids(conn, limit=universe_limit)
        position_ids = fetch_position_market_ids(conn, watch_user)
        forced_ids = list(dict.fromkeys([*manual_ids, *universe_ids, *position_ids]))
        return forced_ids, manual_ids, position_ids
    finally:
        conn.close()


def _build_live_market_set(pg_conn: str) -> tuple[list[dict], dict[str, tuple[str | None, str | None]]]:
    limit = int(os.environ.get("LIVE_FETCH_LIMIT", "240"))
    auto_universe_limit = int(os.environ.get("LIVE_UNIVERSE_LIMIT", "200"))
    bot_wl_limit = int(os.environ.get("LIVE_BOT_WL_LIMIT", "500"))
    watch_user = os.environ.get("WATCHLIST_USER") or os.environ.get("WL_USER", "nikita")

    mkts = fetch_markets(limit=limit)
    forced_ids, _manual_ids, _position_ids = _load_forced_ids(pg_conn, watch_user, auto_universe_limit, bot_wl_limit)

    forced_rows = []
    for market_id in forced_ids:
        row = _fetch_market_detail(market_id)
        if row:
            forced_rows.append(row)

    fetched_forced_ids = {str(row["market_id"]) for row in forced_rows}
    missing_forced_ids = [mid for mid in forced_ids if mid not in fetched_forced_ids]
    if missing_forced_ids:
        conn = psycopg2.connect(pg_conn)
        try:
            forced_rows.extend(fetch_stored_market_rows(conn, missing_forced_ids))
        finally:
            conn.close()

    merged = forced_rows + mkts
    dedup: dict[str, dict] = {}
    for row in merged:
        dedup[str(row["market_id"])] = row
    rows = list(dedup.values())

    market_tokens: dict[str, tuple[str | None, str | None]] = {}
    token_ids: list[str] = []
    for row in rows:
        market_id = str(row["market_id"])
        yes_tid = row.get("yes_token_id")
        no_tid = row.get("no_token_id")
        if yes_tid and no_tid:
            market_tokens[market_id] = (str(yes_tid), str(no_tid))
            token_ids.extend([str(yes_tid), str(no_tid)])

    unique_tokens = list(dict.fromkeys(token_ids))
    prices = fetch_best_bid_ask(unique_tokens) if unique_tokens else {}

    for row in rows:
        market_id = str(row["market_id"])
        yes_tid, _ = market_tokens.get(market_id, (None, None))
        if yes_tid:
            yes_quote = prices.get(yes_tid, {}) or {}
            row["bid_yes"] = yes_quote.get("bid")
            row["ask_yes"] = yes_quote.get("ask")
        else:
            row["bid_yes"] = None
            row["ask_yes"] = None
        row["mid_yes"] = _compute_mid(row["bid_yes"], row["ask_yes"])
        row["spread"] = _compute_spread(row["bid_yes"], row["ask_yes"])
        row["has_two_sided_quote"] = row["bid_yes"] is not None and row["ask_yes"] is not None

    return rows, market_tokens


def _upsert_registry_and_quotes(pg_conn: str, rows: list[dict]) -> tuple[int, int]:
    if not rows:
        return 0, 0

    now = _utc_now()
    market_ids = [str(row["market_id"]) for row in rows]

    registry_rows = [
        (
            str(row["market_id"]),
            row.get("slug") or str(row["market_id"]),
            row.get("question") or "n/a",
            row.get("status") or "active",
            None,
            None,
            row.get("category") or "general",
            row.get("yes_token_id"),
            row.get("no_token_id"),
            now,
        )
        for row in rows
    ]

    quote_rows = [
        (
            str(row["market_id"]),
            row.get("bid_yes"),
            row.get("ask_yes"),
            row.get("mid_yes"),
            float(row.get("liquidity") or 0.0),
            row.get("spread"),
            now,
            now,
            0,
            bool(row.get("has_two_sided_quote")),
        )
        for row in rows
    ]

    conn = psycopg2.connect(pg_conn)
    try:
        with conn.cursor() as cur:
            execute_batch(
                cur,
                """
                insert into public.hot_market_registry_latest
                  (market_id, slug, question, status, end_date, event_title, category, token_yes, token_no, source_ts)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (market_id) do update
                set slug = excluded.slug,
                    question = excluded.question,
                    status = excluded.status,
                    end_date = excluded.end_date,
                    event_title = excluded.event_title,
                    category = excluded.category,
                    token_yes = excluded.token_yes,
                    token_no = excluded.token_no,
                    source_ts = excluded.source_ts;
                """,
                registry_rows,
                page_size=200,
            )
            execute_batch(
                cur,
                """
                insert into public.hot_market_quotes_latest
                  (market_id, bid_yes, ask_yes, mid_yes, liquidity, spread, quote_ts, ingested_at, freshness_seconds, has_two_sided_quote)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (market_id) do update
                set bid_yes = excluded.bid_yes,
                    ask_yes = excluded.ask_yes,
                    mid_yes = excluded.mid_yes,
                    liquidity = excluded.liquidity,
                    spread = excluded.spread,
                    quote_ts = excluded.quote_ts,
                    ingested_at = excluded.ingested_at,
                    freshness_seconds = excluded.freshness_seconds,
                    has_two_sided_quote = excluded.has_two_sided_quote;
                """,
                quote_rows,
                page_size=200,
            )
            cur.execute(
                "delete from public.hot_market_registry_latest where not (market_id = any(%s))",
                (market_ids,),
            )
            cur.execute(
                "delete from public.hot_market_quotes_latest where not (market_id = any(%s))",
                (market_ids,),
            )
        conn.commit()
    finally:
        conn.close()

    return len(registry_rows), len(quote_rows)


def _load_prev_5m_mids(pg_conn: str, market_ids: list[str], *, quote_ts: datetime) -> dict[str, tuple[datetime, float]]:
    if not market_ids:
        return {}

    cutoff = quote_ts.replace(second=0, microsecond=0)
    conn = psycopg2.connect(pg_conn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                with latest_prev as (
                  select distinct on (market_id)
                    market_id,
                    ts_bucket,
                    mid_yes_prev
                  from (
                    select
                      ms.market_id,
                      ms.ts_bucket,
                      max(coalesce(((ms.yes_bid + ms.yes_ask) / 2.0), ms.yes_bid, ms.yes_ask))::double precision as mid_yes_prev
                    from public.market_snapshots ms
                    where ms.market_id = any(%s)
                      and (ms.yes_bid is not null or ms.yes_ask is not null)
                      and ms.ts_bucket <= (%s::timestamptz - interval '4 minutes')
                    group by ms.market_id, ms.ts_bucket
                  ) per_bucket
                  order by market_id, ts_bucket desc
                )
                select market_id, ts_bucket, mid_yes_prev
                from latest_prev
                where mid_yes_prev is not null
                """,
                (market_ids, cutoff),
            )
            out: dict[str, tuple[datetime, float]] = {}
            for market_id, ts_bucket, mid_yes_prev in cur.fetchall():
                out[str(market_id)] = (ts_bucket, float(mid_yes_prev))
            return out
    finally:
        conn.close()


def _publish_hot_top_movers_5m(pg_conn: str, rows: list[dict], *, quote_ts: datetime) -> int:
    market_ids = [str(row["market_id"]) for row in rows if row.get("market_id")]
    prev_by_market = _load_prev_5m_mids(pg_conn, market_ids, quote_ts=quote_ts)

    min_liquidity = float(os.environ.get("HOT_MOVERS_MIN_LIQUIDITY", "1000"))
    max_spread = float(os.environ.get("HOT_MOVERS_MAX_SPREAD", "0.25"))
    min_abs_delta = float(os.environ.get("HOT_MOVERS_MIN_ABS_DELTA", "0.005"))

    mover_rows = []
    mover_market_ids: list[str] = []
    for row in rows:
        market_id = str(row.get("market_id") or "")
        if not market_id:
            continue
        if (row.get("status") or "active") != "active":
            continue
        if not row.get("has_two_sided_quote"):
            continue
        current_mid = row.get("mid_yes")
        if current_mid is None:
            continue
        liquidity = float(row.get("liquidity") or 0.0)
        spread = row.get("spread")
        spread_f = float(spread) if spread is not None else None
        if liquidity < min_liquidity:
            continue
        if spread_f is not None and spread_f > max_spread:
            continue
        prev = prev_by_market.get(market_id)
        if not prev:
            continue
        window_start, prev_mid = prev
        delta_mid = float(current_mid) - float(prev_mid)
        if abs(float(delta_mid)) < min_abs_delta:
            continue
        mover_rows.append(
            (
                market_id,
                row.get("question") or "n/a",
                row.get("slug") or market_id,
                float(prev_mid),
                float(current_mid),
                float(delta_mid),
                abs(float(delta_mid)),
                liquidity,
                spread_f,
                _score_delta(delta_mid, liquidity),
                window_start,
                quote_ts,
                quote_ts,
                quote_ts,
            )
        )
        mover_market_ids.append(market_id)

    conn = psycopg2.connect(pg_conn)
    try:
        with conn.cursor() as cur:
            if mover_rows:
                execute_batch(
                    cur,
                    """
                    insert into public.hot_top_movers_5m
                      (market_id, question, slug, prev_mid, current_mid, delta_mid, delta_abs, liquidity, spread, score, window_start, window_end, quote_ts, ingested_at)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    on conflict (market_id) do update
                    set question = excluded.question,
                        slug = excluded.slug,
                        prev_mid = excluded.prev_mid,
                        current_mid = excluded.current_mid,
                        delta_mid = excluded.delta_mid,
                        delta_abs = excluded.delta_abs,
                        liquidity = excluded.liquidity,
                        spread = excluded.spread,
                        score = excluded.score,
                        window_start = excluded.window_start,
                        window_end = excluded.window_end,
                        quote_ts = excluded.quote_ts,
                        ingested_at = excluded.ingested_at;
                    """,
                    mover_rows,
                    page_size=200,
                )
            if mover_market_ids:
                cur.execute(
                    "delete from public.hot_top_movers_5m where not (market_id = any(%s))",
                    (mover_market_ids,),
                )
            else:
                cur.execute("delete from public.hot_top_movers_5m")
        conn.commit()
    finally:
        conn.close()

    return len(mover_rows)


def main() -> None:
    load_env()
    pg_conn = os.environ.get("PG_CONN", "")
    if not pg_conn:
        raise SystemExit("PG_CONN is required for live hot ingest")

    started_at = _utc_now()
    rows, _market_tokens = _build_live_market_set(pg_conn)
    if not rows:
        print("WARN: live ingest skipped because no markets were resolved")
        return

    registry_count, quote_count = _upsert_registry_and_quotes(pg_conn, rows)
    movers_5m_count = _publish_hot_top_movers_5m(pg_conn, rows, quote_ts=started_at)
    two_sided_count = sum(1 for row in rows if row.get("has_two_sided_quote"))
    print(
        "OK: live hot ingest wrote "
        f"registry={registry_count} quotes={quote_count} two_sided={two_sided_count} movers_5m={movers_5m_count} "
        f"started_at={started_at.isoformat()}"
    )


if __name__ == "__main__":
    main()
