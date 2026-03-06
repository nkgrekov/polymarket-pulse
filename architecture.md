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
app.upgrade_intents  
app.site_events  
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
/limits  
/upgrade  
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
• onboarding/plan UX layer (`/start`, `/help`, `/limits`, `/upgrade`) for conversion to paid plan
• `/upgrade` command writes conversion intent into `app.upgrade_intents`

Site + Email API:

• FastAPI app in `api/main.py`  
• waitlist form + double opt-in  
• daily digest worker in `api/digest_job.py` via Resend
• geo/lang-aware landing renderer (`api/web/*.ru.html`, `api/web/*.en.html`)
• SEO endpoints: `/robots.txt`, `/sitemap.xml`, `/og-card.svg`
• favicon endpoint: `/favicon.svg` (and `/favicon.ico` fallback)
• site telemetry endpoint: `/api/events` (`page_view`, `tg_click`)
• attribution enrichment in telemetry: `placement`, `lang`, `utm_source`, `utm_medium`, `utm_campaign`
• landing uses dark trading-terminal UI with pain-driven hero, live “Top movers” mock widget, scarcity line, and dual CTA (Telegram primary + email waitlist)
• landing includes conversion modules: “what you get in 60 seconds”, mobile sticky Telegram CTA, and static `Historical examples` proof block
• Google Analytics gtag (`G-J901VRQH4G`) injected in landing heads
• site funnel event tracking in `app.site_events`
• Cloudflare edge DNS + TLS + apex domain (`polymarketpulse.app`)
• Resend mail-auth DNS hosted in Cloudflare (`resend._domainkey` + `send.polymarketpulse.app` SPF)
• Resend domain `polymarketpulse.app` is `verified`

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

Attribution flow:

landing query params (`utm_*`)
→ `/api/events` and `/api/waitlist` payload
→ `app.site_events.details`
→ funnel analysis split by source/channel

Digest orchestration:

• GitHub Actions workflow `.github/workflows/digest.yml` runs daily
• manual run is available via `workflow_dispatch`

---

# Future Components

Public API

Web dashboard

User settings

Subscription management

Enterprise forecasting module
