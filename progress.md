# Polymarket Pulse — Implementation Progress

This document tracks the current state of the project.

---

# Layer 0 — Data Infrastructure

The data pipeline collects probability market data from Polymarket.

This infrastructure powers all analytics layers.

---

# Current Stack

Data ingestion:

Python pipeline.

Database:

Supabase (Postgres).

---

# Current Tables

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

---

# Snapshot System

Snapshots store market states over time.

Columns include:

market_id  
ts_bucket  
yes_price  
no_price  
liquidity  
yes_bid  
yes_ask  
no_bid  
no_ask  

Snapshots allow:

• probability change detection  
• liquidity tracking  
• historical analysis

---

# Market Universe

Table:

public.market_universe

Purpose:

Defines active markets tracked by the system.

Sources:

manual — user-selected live markets  
position — markets from user positions  
auto — live liquid markets with both latest and previous buckets  

Universe guarantees:

• ingest coverage  
• consistent analytics scope  
• live-only movers surface for the bot

Universe refresh is best-effort:

• snapshot writes commit first  
• universe refresh runs after that  
• refresh timeout must not fail the whole ingest run

Forced ingest coverage now merges:

• `public.user_watchlist` legacy manual list  
• `bot.watchlist` multi-user manual list  
• `public.market_universe` auto live scope  
• `public.user_positions` markets

---

# Live Market Detection

Markets are considered live when:

• they appear in recent snapshots  
• they exist in market_universe

Expired markets are excluded from alerts.

---

# Analytics Views

Key derived views:

top_movers_latest  
portfolio_snapshot_latest  
watchlist_snapshot_latest  
alerts_latest  
watchlist_alerts_latest  
alerts_inbox_latest

These views power signal generation.

---

# Telegram Bot MVP

Telegram bot upgraded to multi-user with native onboarding.

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

Bot reads signals from:

bot.alerts_inbox_latest

Movers mode reads from:

top_movers_latest

Watchlist mode reads from:

bot.watchlist_snapshot_latest

The bot does not call Polymarket API directly.

All signals come from the database layer.

Freemium v1:

• Free: 3 watchlist markets  
• Free: 20 push alerts/day  
• Pro: unlimited

Threshold policy:

• Global baseline 0.03  
• Per-user override in `bot.user_settings.threshold`

---

# Current System Pipeline

Polymarket API  
→ ingest pipeline  
→ Supabase database  
→ analytics views  
→ bot + site + email channels

---

# Current Product State

The project currently operates as:

Live market data and movers engine with Telegram + site waitlist + email foundation.

Current limitation:

if selected markets have no usable live midpoint data in latest/previous buckets, watchlist and inbox may be empty by design.

Operational note:

market_universe refresh can be slower than snapshot writes and is treated as non-fatal for ingest stability.

Ingest cadence update:

• Added Railway-ready loop runner `ingest/worker.py`  
• Interval is env-configurable (`INGEST_INTERVAL_SECONDS`)  
• GitHub Actions ingest moved to hourly backup trigger

Site/email status:

• `api/main.py` provides waitlist submit + confirm + unsubscribe  
• Resend integration for confirmation/welcome  
• `api/digest_job.py` sends daily digest from `bot.alert_events`

---

# Next Milestones

Railway deploy (bot + site)

Payment integration for `pro`

Web auth linking to Telegram identity

iOS client integration
