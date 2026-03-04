import os
import requests
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import execute_batch
from psycopg2 import Error as PsycopgError

import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import (
    ChunkedEncodingError,
    ConnectionError,
    HTTPError,
    ReadTimeout,
    Timeout,
)

API_URL = "https://gamma-api.polymarket.com/events"
GAMMA_MARKET_BY_ID = "https://gamma-api.polymarket.com/markets/{}"
CLOB_PRICES_URL = "https://clob.polymarket.com/prices"

import json

def make_session():
    retry = Retry(
        total=4,                 # всего попыток
        connect=4,
        read=4,
        backoff_factor=1.0,      # 1s, 2s, 4s...
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    s = requests.Session()
    s.mount("https://", adapter)
    s.mount("http://", adapter)

    # Нормальные заголовки, иногда помогают против странных блоков
    s.headers.update({
        "User-Agent": "polymarket-pulse/1.0 (+github-actions)",
        "Accept": "application/json",
    })
    return s


SESSION = make_session()

def _as_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return []
        # иногда Gamma отдаёт массив строкой: '["Yes","No"]'
        if s[0] in "[{":
            try:
                return json.loads(s)
            except Exception:
                pass
        return [s]
    return [x]

def fetch_yes_no_token_ids(market_id: str) -> tuple[str | None, str | None]:
    try:
        r = SESSION.get(GAMMA_MARKET_BY_ID.format(market_id), timeout=30)
    except (ChunkedEncodingError, ConnectionError, ReadTimeout, Timeout) as e:
        print(f"WARN: gamma fetch failed transiently: {type(e).__name__}: {e}")
        return (None, None)

    try:
        r.raise_for_status()
    except HTTPError as e:
        print(f"WARN: gamma market {market_id} returned HTTP error: {e}")
        return (None, None)
    m = r.json()

    outcomes = _as_list(m.get("outcomes"))
    token_ids = _as_list(m.get("clobTokenIds") or m.get("clob_token_ids") or m.get("clobTokenIDs"))

    # ожидаем две штуки: Yes/No
    # на всякий — пытаемся сопоставить по названию outcome
    yes_token = no_token = None

    if len(token_ids) >= 2 and len(outcomes) >= 2:
        # обычно порядок совпадает
        pairs = list(zip(outcomes, token_ids))
        for name, tok in pairs:
            n = str(name).strip().lower()
            if n == "yes":
                yes_token = str(tok)
            elif n == "no":
                no_token = str(tok)

        # если не нашли по именам — возьмём по умолчанию 0/1
        if yes_token is None:
            yes_token = str(token_ids[0])
        if no_token is None:
            no_token = str(token_ids[1])

    return yes_token, no_token

def fetch_best_bid_ask(token_ids: list[str], chunk_tokens: int = 40) -> dict[str, dict[str, float | None]]:
    """
    chunk_tokens=40 => 40 token_ids -> 80 params (BUY+SELL)
    Это почти наверняка пролезает без 400.
    """
    # нормализация и дедуп
    token_ids = [str(t).strip() for t in token_ids if t]
    token_ids = list(dict.fromkeys(token_ids))

    out: dict[str, dict[str, float | None]] = {}

    def _chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i+n]

    for chunk in _chunks(token_ids, chunk_tokens):
        params = []
        for tid in chunk:
            params.append({"token_id": tid, "side": "BUY"})
            params.append({"token_id": tid, "side": "SELL"})

        try:
            r = SESSION.post(CLOB_PRICES_URL, json=params, timeout=30)
        except (ChunkedEncodingError, ConnectionError, ReadTimeout, Timeout) as e:
            raise RuntimeError(f"CLOB /prices transient network error: {type(e).__name__}: {e}")

        if r.status_code >= 400:
            # покажем настоящую причину (CLOB обычно кладёт её в body)
            raise RuntimeError(f"CLOB /prices failed: {r.status_code} {r.text[:500]}")

        data = r.json()

        # ожидается: {[asset_id]: {[side]: price}}
        for tid in chunk:
            rec = data.get(str(tid), {}) if isinstance(data, dict) else {}
            bid = rec.get("BUY")
            ask = rec.get("SELL")
            out[str(tid)] = {
                "bid": float(bid) if bid is not None else None,
                "ask": float(ask) if ask is not None else None,
            }

    return out

def floor_to_5min(dt: datetime) -> datetime:
    minute = (dt.minute // 5) * 5
    return dt.replace(minute=minute, second=0, microsecond=0)

def load_env():
    # очень простой парсер .env (без python-dotenv, чтобы не добавлять зависимость)
    if not os.path.exists(".env"):
        return
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k.strip(), v)

def fetch_markets(limit: int = 80):
    out = []
    offset = 0
    page = 100

    while len(out) < limit:
        params = {
            "order": "id",
            "ascending": "false",
            "closed": "false",
            "limit": str(page),
            "offset": str(offset),
        }

        try:
            r = SESSION.get(API_URL, params=params, timeout=30)
        except (ChunkedEncodingError, ConnectionError, ReadTimeout, Timeout) as e:
            print(f"WARN: gamma fetch failed transiently: {type(e).__name__}: {e}")
            return []

        try:
            r.raise_for_status()
        except HTTPError as e:
            print(f"WARN: gamma events returned HTTP error: {e}")
            return []
        events = r.json() or []
        if not events:
            break

        for ev in events:
            for m in (ev.get("markets") or []):
                market_id = m.get("id") or m.get("marketId") or m.get("slug")
                if not market_id:
                    continue

                outs = m.get("outcomes")
                tids = m.get("clobTokenIds")

                if isinstance(outs, str):
                    try: outs = json.loads(outs)
                    except: outs = None
                if isinstance(tids, str):
                    try: tids = json.loads(tids)
                    except: tids = None

                yes_tid = no_tid = None
                if isinstance(outs, list) and isinstance(tids, list) and len(outs) == len(tids):
                    norm = [str(x).strip().lower() for x in outs]
                    for o, tid in zip(norm, tids):
                        if o in ("yes", "up"):
                            yes_tid = tid
                        elif o in ("no", "down"):
                            no_tid = tid

                out.append({
                    "market_id": str(market_id),
                    "slug": m.get("slug") or str(market_id),
                    "question": m.get("question") or ev.get("title") or "n/a",
                    "category": (m.get("category") or ev.get("category") or "general"),
                    "status": "active" if not ev.get("closed") else "closed",
                    "yes_price": None,
                    "no_price": None,
                    "liquidity": float(m.get("liquidity") or 0),
                    "yes_token_id": yes_tid,
                    "no_token_id": no_tid,
                })

                if len(out) >= limit:
                    return out

        offset += page

    return out

def extract_yes_no_token_ids(m: dict):
    """
    Пытаемся достать token ids максимально устойчиво: у Polymarket в разных эндпойнтах структура может отличаться.
    Возвращаем (yes_token_id, no_token_id) или (None, None) если не нашли.
    """
    # Вариант 1: tokens = [{"outcome":"Yes","token_id":"..."}, {"outcome":"No","token_id":"..."}]
    tokens = m.get("tokens") or m.get("clobTokens") or m.get("outcomeTokens")
    if isinstance(tokens, list):
        yes = no = None
        for t in tokens:
            outcome = (t.get("outcome") or t.get("name") or "").strip().lower()
            tid = t.get("token_id") or t.get("tokenId") or t.get("clobTokenId")
            if not tid:
                continue
            if outcome == "yes":
                yes = tid
            elif outcome == "no":
                no = tid
        if yes or no:
            return yes, no

    # Вариант 2: outcomes = ["Yes","No"] и рядом массив tokenIds/clobTokenIds
    outcomes = m.get("outcomes")
    ids = m.get("clobTokenIds") or m.get("tokenIds")
    if isinstance(outcomes, list) and isinstance(ids, list) and len(outcomes) == len(ids):
        norm = [str(x).strip().lower() for x in outcomes]
        yes = no = None
        for o, tid in zip(norm, ids):
            if o == "yes":
                yes = tid
            elif o == "no":
                no = tid
        if yes or no:
            return yes, no

    # Не нашли
    return None, None

def fetch_watchlist_market_ids(conn, user_id: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            "select market_id from public.user_watchlist where user_id=%s",
            (user_id,),
        )
        return [str(r[0]) for r in cur.fetchall()]

def fetch_market_universe_ids(conn, limit: int = 60) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select market_id
            from public.market_universe
            order by weight desc nulls last, updated_at desc, market_id
            limit %s
            """,
            (limit,),
        )
        return [str(r[0]) for r in cur.fetchall()]

def fetch_position_market_ids(conn, user_id: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select distinct market_id
            from public.user_positions
            where user_id=%s
            """,
            (user_id,),
        )
        return [str(r[0]) for r in cur.fetchall()]

def refresh_market_universe(conn, limit: int, manual_ids: list[str], position_ids: list[str]) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "select public.refresh_market_universe(%s, %s, %s)",
            (limit, manual_ids, position_ids),
        )
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else 0

def try_refresh_market_universe(pg_conn: str, limit: int, manual_ids: list[str], position_ids: list[str]) -> tuple[bool, int | None, str | None]:
    timeout_ms = int(os.environ.get("UNIVERSE_REFRESH_TIMEOUT_MS", "15000"))
    conn = psycopg2.connect(pg_conn)
    try:
        with conn.cursor() as cur:
            cur.execute("set statement_timeout = %s", (str(timeout_ms),))
            refreshed = refresh_market_universe(conn, limit, manual_ids, position_ids)
        conn.commit()
        return (True, refreshed, None)
    except PsycopgError as e:
        conn.rollback()
        return (False, None, f"{type(e).__name__}: {e}")
    finally:
        conn.close()

def fetch_stored_market_rows(conn, market_ids: list[str]) -> list[dict]:
    if not market_ids:
        return []
    with conn.cursor() as cur:
        cur.execute(
            """
            select market_id, slug, question, category, status, yes_token_id, no_token_id
            from public.markets
            where market_id = any(%s)
            """,
            (market_ids,),
        )
        rows = cur.fetchall()

    out = []
    for market_id, slug, question, category, status, yes_tid, no_tid in rows:
        out.append({
            "market_id": str(market_id),
            "slug": slug or str(market_id),
            "question": question or "n/a",
            "category": category or "general",
            "status": status or "active",
            "yes_price": None,
            "no_price": None,
            "liquidity": 0.0,
            "yes_token_id": str(yes_tid) if yes_tid else None,
            "no_token_id": str(no_tid) if no_tid else None,
        })
    return out


def normalize_market_row(m: dict) -> dict:
    market_id = m.get("id") or m.get("marketId") or m.get("slug")
    outs = m.get("outcomes")
    tids = m.get("clobTokenIds")

    if isinstance(outs, str):
        try: outs = json.loads(outs)
        except: outs = None
    if isinstance(tids, str):
        try: tids = json.loads(tids)
        except: tids = None

    yes_tid = no_tid = None
    if isinstance(outs, list) and isinstance(tids, list) and len(outs) == len(tids):
        norm = [str(x).strip().lower() for x in outs]
        for o, tid in zip(norm, tids):
            if o in ("yes", "up"):
                yes_tid = str(tid)
            elif o in ("no", "down"):
                no_tid = str(tid)

    return {
        "market_id": str(market_id),
        "slug": m.get("slug") or str(market_id),
        "question": m.get("question") or "n/a",
        "category": (m.get("category") or "general"),
        "status": "active" if not m.get("closed") else "closed",
        "yes_price": None,
        "no_price": None,
        "liquidity": float(m.get("liquidity") or 0),
        "yes_token_id": yes_tid,
        "no_token_id": no_tid,
    }


def main():
    load_env()
    pg = os.environ.get("PG_CONN")
    if not pg:
        raise SystemExit("Нет PG_CONN. Добавь PG_CONN в .env корня репозитория или передай через env")

    now = datetime.now(timezone.utc)
    bucket = floor_to_5min(now)

    LIMIT = int(os.environ.get("FETCH_LIMIT", "200"))
    watch_user = os.environ.get("WATCHLIST_USER") or os.environ.get("WL_USER", "nikita")
    AUTO_WL_LIMIT = int(os.environ.get("AUTO_WL_LIMIT", "200"))

    mkts = fetch_markets(limit=LIMIT)

    # --- Forced list: manual watchlist + market universe + user positions ---
    forced_ids = []
    universe_ids = []
    manual_ids = []
    position_ids = []

    # Важно: коннектимся раньше, чтобы прочитать forced lists
    conn = psycopg2.connect(pg)
    try:
        manual_ids = fetch_watchlist_market_ids(conn, watch_user)
        universe_ids = fetch_market_universe_ids(conn, limit=AUTO_WL_LIMIT)
        position_ids = fetch_position_market_ids(conn, watch_user)
    finally:
        conn.close()

    forced_ids = list(dict.fromkeys([*manual_ids, *universe_ids, *position_ids]))

    print(
        "INFO: forced ids: "
        f"manual={len(manual_ids)} universe={len(universe_ids)} positions={len(position_ids)} total={len(forced_ids)}"
    )

    # догружаем рынки из gamma /markets/{id}
    forced_rows = []
    for mid in forced_ids:
        try:
            r = SESSION.get(GAMMA_MARKET_BY_ID.format(mid), timeout=30)
            r.raise_for_status()
            forced_rows.append(normalize_market_row(r.json()))
        except Exception as e:
            print(f"WARN: forced fetch failed for {mid}: {e}")

    fetched_forced_ids = {str(row["market_id"]) for row in forced_rows}
    missing_forced_ids = [mid for mid in forced_ids if mid not in fetched_forced_ids]
    if missing_forced_ids:
        conn = psycopg2.connect(pg)
        try:
            stored_rows = fetch_stored_market_rows(conn, missing_forced_ids)
        finally:
            conn.close()
        forced_rows.extend(stored_rows)
        print(
            f"INFO: forced fallback from markets table rows={len(stored_rows)} missing_after_gamma={len(missing_forced_ids)}"
        )

    # мерджим: forced list + обычная выборка, дедуп по market_id
    merged = forced_rows + mkts
    dedup = {}
    for x in merged:
        dedup[str(x["market_id"])] = x
    mkts = list(dedup.values())

    # conn пока не закрываем — используем ниже для записи (или закрой, если хочешь)

    if not mkts:
        print("No markets fetched")
        return

    # 1) собираем токены и маппинг market_id -> (yes_tid, no_tid) для общего списка рынков
    mid_to_tokens = {}
    all_tokens = []
    for m in mkts:
        mid = str(m["market_id"])
        yes_tid = m.get("yes_token_id")
        no_tid = m.get("no_token_id")
        if yes_tid and no_tid:
            mid_to_tokens[mid] = (str(yes_tid), str(no_tid))
            all_tokens.extend([str(yes_tid), str(no_tid)])

    all_tokens = list(dict.fromkeys(all_tokens))  # дедуп

    try:
        prices = fetch_best_bid_ask(all_tokens)
    except RuntimeError as e:
        print(f"WARN: skipping tick due to CLOB failure: {e}")
        return


    refreshed_universe = None
    refresh_ok = False
    refresh_error = None

    conn = psycopg2.connect(pg)
    try:
        with conn.cursor() as cur:
            execute_batch(cur, """
                insert into markets (market_id, slug, question, category, status, yes_token_id, no_token_id)
                values (%s,%s,%s,%s,%s,%s,%s)
                on conflict (market_id) do update
                set slug=excluded.slug,
                    question=excluded.question,
                    category=excluded.category,
                    status=excluded.status,
                    yes_token_id=excluded.yes_token_id,
                    no_token_id=excluded.no_token_id;
            """, [
                (
                    m["market_id"],
                    m["slug"],
                    m["question"],
                    m["category"],
                    m["status"],
                    m.get("yes_token_id"),
                    m.get("no_token_id"),
                )
                for m in mkts
            ], page_size=200)

            # 5) снапшоты пишем для общего списка рынков (top fetch + forced list)
            snapshot_rows = []
            for m in mkts:
                mid = str(m["market_id"])
                yes_tid, no_tid = mid_to_tokens.get(mid, (None, None))
                if not yes_tid or not no_tid:
                    continue
                snapshot_rows.append((
                    mid,
                    bucket,
                    (prices.get(yes_tid, {}) or {}).get("bid"),
                    (prices.get(yes_tid, {}) or {}).get("ask"),
                    (prices.get(no_tid, {}) or {}).get("bid"),
                    (prices.get(no_tid, {}) or {}).get("ask"),
                    m.get("liquidity", 0.0) or 0.0,
                ))

            execute_batch(cur, """
                insert into market_snapshots
                  (market_id, ts_bucket,
                   yes_bid, yes_ask,
                   no_bid, no_ask,
                   liquidity)
                values (%s,%s,%s,%s,%s,%s,%s)
                on conflict (market_id, ts_bucket) do update
                set yes_bid = excluded.yes_bid,
                    yes_ask = excluded.yes_ask,
                    no_bid  = excluded.no_bid,
                    no_ask  = excluded.no_ask,
                    liquidity = excluded.liquidity;
            """, snapshot_rows, page_size=200)
        conn.commit()
    finally:
        conn.close()

    refresh_ok, refreshed_universe, refresh_error = try_refresh_market_universe(
        pg,
        AUTO_WL_LIMIT,
        manual_ids,
        position_ids,
    )

    if not refresh_ok:
        print(f"WARN: market_universe refresh skipped: {refresh_error}")

    print(
        f"OK: wrote mkts={len(mkts)} forced={len(forced_ids)} "
        f"snapshots={len(snapshot_rows)} "
        f"universe_refresh={'ok' if refresh_ok else 'skipped'} "
        f"universe_total={refreshed_universe if refreshed_universe is not None else 'n/a'} "
        f"bucket={bucket.isoformat()}"
    )

if __name__ == "__main__":
    main()
