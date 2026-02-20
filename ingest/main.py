import os
import requests
import time
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import execute_batch

API_URL = "https://gamma-api.polymarket.com/events"
GAMMA_MARKET_BY_ID = "https://gamma-api.polymarket.com/markets/{}"
CLOB_PRICES_URL = "https://clob.polymarket.com/prices"

import json

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

def fetch_yes_no_token_ids(market_id: str) -> tuple[str | None, str | None, int | None]:
    max_attempts = 3
    backoff_sec = 1.0
    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.get(GAMMA_MARKET_BY_ID.format(market_id), timeout=30)
            if r.status_code == 404:
                return None, None, 404
            r.raise_for_status()
            m = r.json()
            break
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            is_retryable = status is not None and 500 <= status < 600 and attempt < max_attempts
            if is_retryable:
                time.sleep(backoff_sec)
                backoff_sec *= 2
                continue
            raise
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt < max_attempts:
                time.sleep(backoff_sec)
                backoff_sec *= 2
                continue
            raise

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

    return yes_token, no_token, None

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

        r = requests.post(CLOB_PRICES_URL, json=params, timeout=30)

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
    params = {
        "order": "id",
        "ascending": "false",
        "closed": "false",
        "limit": "100",   # событий за раз
        "offset": "0",
    }
    r = requests.get(API_URL, params=params, timeout=30)
    r.raise_for_status()
    events = r.json()

    out = []
    for ev in events:
        for m in (ev.get("markets") or []):
            market_id = m.get("id") or m.get("marketId") or m.get("slug")
            if not market_id:
                continue

            # В gamma структура полей может отличаться; MVP-логика: берём, что есть
            out.append({
                "market_id": str(market_id),
                "slug": m.get("slug") or str(market_id),
                "question": m.get("question") or ev.get("title") or "n/a",
                "category": (m.get("category") or ev.get("category") or "general"),
                "status": "active" if not ev.get("closed") else "closed",
                "yes_price": None,
                "no_price": None,
                "liquidity": float(m.get("liquidity") or 0),
            })

            if len(out) >= limit:
                return out

    return out

def main():
    load_env()
    pg = os.environ.get("PG_CONN")
    if not pg:
        raise SystemExit("Нет PG_CONN. Добавь PG_CONN в ingest/.env")

    now = datetime.now(timezone.utc)
    bucket = floor_to_5min(now)

    mkts = fetch_markets(limit=80)
    if not mkts:
        print("No markets fetched")
        return

    # --- Layer II: resolve YES/NO token ids for each market ---
    mid_to_tokens = {}
    all_tokens = []
    resolved_count = 0
    skipped_404 = 0
    skipped_other_errors = 0

    for m in mkts:
        mid = str(m["market_id"])
        try:
            yes_tid, no_tid, status = fetch_yes_no_token_ids(mid)
        except requests.exceptions.RequestException as e:
            skipped_other_errors += 1
            print(f"SKIP market {mid}: token id fetch failed ({type(e).__name__})")
            continue

        if status == 404:
            skipped_404 += 1
            continue

        if yes_tid and no_tid:
            mid_to_tokens[mid] = (yes_tid, no_tid)
            all_tokens.extend([yes_tid, no_tid])
            resolved_count += 1
        else:
            skipped_other_errors += 1
            print(f"SKIP market {mid}: missing YES/NO token ids")

    # --- Layer II: fetch best bid/ask for all tokens in one batch ---
    prices = fetch_best_bid_ask(list(dict.fromkeys(all_tokens)))

    conn = psycopg2.connect(pg)
    with conn.cursor() as cur:
        execute_batch(cur, """
            insert into markets (market_id, slug, question, category, status)
            values (%s,%s,%s,%s,%s)
            on conflict (market_id) do update
            set slug=excluded.slug,
                question=excluded.question,
                category=excluded.category,
                status=excluded.status;
        """, [(m["market_id"], m["slug"], m["question"], m["category"], m["status"]) for m in mkts], page_size=200)

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
        """, [
            (
                m["market_id"],
                bucket,
                # YES bid/ask
                (prices.get(mid_to_tokens.get(str(m["market_id"]), (None, None))[0], {}) or {}).get("bid"),
                (prices.get(mid_to_tokens.get(str(m["market_id"]), (None, None))[0], {}) or {}).get("ask"),
                # NO bid/ask
                (prices.get(mid_to_tokens.get(str(m["market_id"]), (None, None))[1], {}) or {}).get("bid"),
                (prices.get(mid_to_tokens.get(str(m["market_id"]), (None, None))[1], {}) or {}).get("ask"),
                # liquidity
                m["liquidity"],
            )
            for m in mkts
        ], page_size=200)

    conn.commit()
    conn.close()

    print(
        f"OK: wrote {len(mkts)} markets at bucket {bucket.isoformat()} "
        f"(resolved={resolved_count}, skipped_404={skipped_404}, skipped_other={skipped_other_errors})"
    )

if __name__ == "__main__":
    main()
