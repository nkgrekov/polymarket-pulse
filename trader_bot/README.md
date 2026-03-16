# Polymarket Pulse Trader Bot

Sibling Telegram bot for the execution lane of Polymarket Pulse.

Current scope:
- wallet registration (`/connect`)
- live market queue (`/markets`)
- manual order drafts (`/buy`, `/sell`, `/order`)
- positions cache (`/positions`)
- follow-source setup (`/follow`)
- rule and risk inspection/update (`/rules`, `/risk`, `/pause`, `/agent`)

The bot is alpha-only and does not route real orders yet.
It writes execution intent into `trade.*` and prepares the operator/worker layer.

## Local run

```bash
cd /Users/nikitagrekov/polymarket-pulse
set -a && source trader_bot/.env && set +a
bot/.venv/bin/python trader_bot/main.py
```

## Env

Copy `trader_bot/.env.example` to `trader_bot/.env` and fill:
- `TRADER_BOT_TOKEN`
- `PG_CONN`
- `APP_BASE_URL`
- `TRADER_SITE_URL`
- `PULSE_BOT_URL`
