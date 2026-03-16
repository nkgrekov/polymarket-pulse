# Railway Deploy (Bot + Site + Ingest)

## Prerequisites

- Railway CLI installed and logged in.
- Railway MCP server installed (`npx add-mcp @railway/mcp-server --name railway`).
- Repo root: `/Users/nikitagrekov/polymarket-pulse`.

## Service 1: bot

Start command:

```bash
python bot/main.py
```

Required variables:

- `BOT_TOKEN`
- `PG_CONN`
- `PUSH_INTERVAL_SECONDS`
- `PUSH_FETCH_LIMIT`
- `FREE_WATCHLIST_LIMIT`
- `FREE_DAILY_ALERT_LIMIT`
- `RESEND_API_KEY` (optional)
- `RESEND_FROM_EMAIL` (optional)
- `APP_BASE_URL`

## Service 1b: trader-bot

Start command:

```bash
python trader_bot/main.py
```

Monorepo deploy command:

```bash
railway up -s trader-bot --path-as-root trader_bot
```

Required variables:

- `TRADER_BOT_TOKEN`
- `PG_CONN`
- `APP_BASE_URL`
- `TRADER_SITE_URL`
- `TRADER_SIGNER_URL` (`https://polymarketpulse.app/trader-connect` in prod)
- `PULSE_BOT_URL`
- `TRADER_SOURCE`
- `TRADER_DEFAULT_ORDER_USD`
- `TRADER_TOP_MARKETS_LIMIT`
- `DB_CONNECT_TIMEOUT_SECONDS`

## Service 1c: trade-worker

Start command:

```bash
python trade_worker/main.py
```

Monorepo deploy command:

```bash
railway up -s trade-worker --path-as-root trade_worker
```

Required variables:

- `PG_CONN`
- `EXECUTION_MODE` (`dry_run` for current alpha)
- `EXECUTION_POLL_SECONDS`
- `DB_CONNECT_TIMEOUT_SECONDS`
- `WORKER_BATCH_LIMIT`
- `WORKER_SOURCE`

## Service 2: site

Start command:

```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

Required variables:

- `PG_CONN`
- `APP_BASE_URL`
- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL`

## Service 3: ingest

Start command:

```bash
python ingest/worker.py
```

Required variables:

- `PG_CONN`
- `FETCH_LIMIT` (default `200`)
- `AUTO_WL_LIMIT` (default `200`)
- `BOT_WL_LIMIT` (default `500`)
- `WATCHLIST_USER` (default `nikita`, legacy fallback)
- `INGEST_INTERVAL_SECONDS` (recommended `900`)
- `UNIVERSE_REFRESH_TIMEOUT_MS` (recommended `15000`)

## Daily digest job

Command:

```bash
python api/digest_job.py
```

Schedule recommendation:

- Daily at 10:00 user-local baseline (today run once manually for smoke).

## Smoke checklist

1. Bot: `/start`, `/plan`, `/watchlist_list`, `/movers`, `/inbox`
2. Site: submit email form, receive confirmation email
3. Confirm link marks `app.email_subscribers.confirmed_at`
4. Ingest: verify periodic logs every `INGEST_INTERVAL_SECONDS` and fresh `market_snapshots.ts_bucket`
5. Run `python api/digest_job.py` and verify `bot.sent_alerts_log` channel=`email`
