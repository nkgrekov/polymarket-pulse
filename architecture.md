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
/movers  
/watchlist  
/inbox  
/plan  
/help  
/menu  

Advanced (typed or via `/help`):

/upgrade  
/limits  
/threshold  
/inbox20  
/watchlist_list  
/watchlist_add  
/watchlist_remove  
/admin_stats

Also runs:

• scheduled push loop  
• freemium enforcement (watchlist + daily alert caps)
• onboarding/plan UX layer (`/start`, `/help`, `/limits`, `/upgrade`) for conversion to paid plan
• compact Telegram command menu with advanced commands moved to `/help`
• quick-reply keyboard on `/start` for core actions (`/movers`, `/watchlist`, `/inbox`, `/plan`)
• callback action menu (`/menu`) with inline buttons for movers/watchlist/inbox/plan/picker/threshold
• watchlist picker flow from live movers (callback tokens mapped in bot memory)
• `/upgrade` command writes conversion intent into `app.upgrade_intents`

Site + Email API:

• FastAPI app in `api/main.py`  
• waitlist form + double opt-in  
• daily digest worker in `api/digest_job.py` via Resend
• geo/lang-aware landing renderer (`api/web/*.ru.html`, `api/web/*.en.html`)
• SEO endpoints: `/robots.txt`, `/sitemap.xml`, `/og-card.svg`
• SEO intent endpoints: `/analytics`, `/dashboard`, `/signals`, `/telegram-bot`, `/top-movers`, `/watchlist-alerts`
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

# UI System Contract

All web surfaces (landing + SEO intent pages) must use one visual contract.

Hard rules:

• Dark-only backgrounds (`#0d0f0e` / `#0a0c0b`) and dark cards (`#131714`, border `#1e2520`)  
• Off-white text (`#e8ede9`) + muted data text (`#8fa88f` / `#6b7a6e`)  
• Green (`#00ff88`) only for CTA/positive/active states  
• Red (`#ff4444`) only for negative deltas  
• No light sections, no yellow CTA variants, no bullet lists on SEO pages  
• Data blocks use shared primitives: dark feature rows, dark intent pills, dark FAQ callouts

Enforcement points in code:

• `api/web/index.en.html`  
• `api/web/index.ru.html`  
• `api/main.py::render_seo_page`

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

Growth ops:

• competitor scan script: `scripts/growth/competitive_scan.py` (parses polymark.et tool index)  
• social draft generator: `scripts/growth/generate_social_drafts.py` (DB live views -> RU/EN post drafts)  
• visual post templates in `assets/social/` (Top3, Breakout, Weekly recap)

Operational deploy notes (2026-03-08):

• monorepo Railway deploy must use service path roots:
  - `site`: `railway up -s site --path-as-root api`
  - `bot`: `railway up -s bot --path-as-root bot`
• deploying from repo root without `--path-as-root` can fail Railpack autodetection and leave previous deployment active

---

# Future Components

Public API

Web dashboard

User settings

Subscription management

Enterprise forecasting module
