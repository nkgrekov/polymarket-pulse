# Polymarket Pulse — System Architecture

This document describes the technical architecture.

---

# Data Pipeline

Polymarket API  
→ ingest pipeline  
→ Postgres storage  
→ analytics views  
→ delivery layer

---

# Components

## Ingest

Python service.

Responsibilities:

• fetch market data  
• normalize responses  
• write snapshots  
• maintain universe coverage

Snapshot writes are the critical path.

Universe refresh runs after snapshot commit and is allowed to fail without failing the whole ingest run.

Runs as:

• GitHub Actions scheduled job (backup)
• Railway worker loop (`ingest/worker.py`) for stable cadence

Worker interval is controlled by `INGEST_INTERVAL_SECONDS`.
GitHub backup schedule is hourly.

---

## Database

Supabase Postgres.

Stores:

markets  
market_snapshots  
market_universe  
user_positions  
user_watchlist  
app.users  
app.identities  
app.subscriptions  
app.email_subscribers  
bot.profiles  
bot.user_settings  
bot.watchlist  
bot.alert_events  
bot.sent_alerts_log

Derived views compute analytics.

---

## Analytics Layer

SQL views calculate signals.

Examples:

top_movers_latest  
portfolio_snapshot_latest  
watchlist_snapshot_latest  
alerts_latest  
watchlist_alerts_latest  
alerts_inbox_latest

These views produce:

• probability deltas  
• spread signals  
• portfolio changes

---

## Delivery Layer

Telegram bot.

Reads alerts from `bot` analytics views only.

Commands:

/start  
/help  
/plan  
/threshold  
/inbox  
/inbox20  
/movers  
/watchlist  
/watchlist_list  
/watchlist_add  
/watchlist_remove  
/admin_stats

Also runs:

• scheduled push loop  
• freemium enforcement (watchlist + daily alert caps)

Site + Email API:

• FastAPI app in `api/main.py`  
• waitlist form + double opt-in  
• daily digest worker in `api/digest_job.py` via Resend

---

# Universe System

Universe defines markets actively tracked.

Sources:

manual — explicit user watchlist markets  
position — user portfolio markets  
auto — live liquid markets with both latest and previous buckets

Universe ensures ingest coverage.

Current forced list in ingest:

manual watchlist (`public.user_watchlist` + `bot.watchlist`)  
market universe  
user positions

Universe refresh is a post-write step with its own timeout budget.

---

# Alert Engine

Alerts are generated when:

probability change exceeds per-user threshold.

Alert flow:

market_snapshots  
→ bot.portfolio_snapshot_latest / bot.watchlist_snapshot_latest  
→ bot.portfolio_alerts_latest / bot.watchlist_alerts_latest  
→ bot.alerts_inbox_latest  
→ bot

Live movers flow:

market_snapshots  
→ market_universe  
→ top_movers_latest  
→ /movers command

Watchlist flow:

market_snapshots
→ market_universe
→ bot.watchlist_snapshot_latest
→ bot.watchlist_alerts_latest
→ bot.alerts_inbox_latest
→ /watchlist and push

Email flow:

site form / bot opt-in
→ app.email_subscribers (confirm_token)
→ /confirm (double opt-in)
→ bot.alert_events aggregation
→ api/digest_job.py
→ bot.sent_alerts_log (channel=email)
→ subscriber inbox

---

# Future Components

Public API

Web dashboard

User settings

Subscription management

Enterprise forecasting module
