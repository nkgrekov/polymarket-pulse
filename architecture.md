# Polymarket Pulse — System Architecture

This document describes the technical architecture.

---

# Active Execution Plan Link

Operational 14-day delivery plan is versioned in:

`docs/plan_14day_seo_bot_growth_2026-03-09.md`

Architecture and rollout priorities must stay aligned with that plan and with `manifest.md`.

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
• rebalance fetched market pool by category + root-question dedup  
• normalize responses  
• write snapshots  
• maintain universe coverage with balanced category pull

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
• watchlist picker flow uses mover-first candidates ranked by live liquidity (volume proxy), with live-liquidity fallback and callback tokens in bot memory
• picker supports category-level callback filters (`all`, `crypto`, `politics`, `macro`) on top of liquidity-ranked candidates
• category filter behavior is strict: no cross-category fallback; empty category returns explicit UX guidance
• `all` picker mode applies category-balanced quotas and ordering to reduce crypto dominance in candidate list
• picker UI includes category tags and live-supply hint (candidate count in current window)
• picker candidate pool includes recent active markets (last 72h seen in snapshots) as fallback when live movers are too narrow
• `/upgrade` command writes conversion intent into `app.upgrade_intents`
• monetization offer v1 in bot UX:
  - FREE: 3 watchlist markets, 20 push/day
  - PRO: 20 watchlist markets + email digest
  - pricing target: USD-equivalent monthly payment in Telegram Stars
  - current configured Stars invoice: `454 XTR`
• upgrade command UX contract:
  - send concise PRO offer message first (FREE vs PRO delta + Stripe fallback link)
  - send Telegram Stars invoice immediately after, in the same handler
  - no intermediate inline keyboard between message and invoice
  - `/plan` ends with explicit upgrade CTA line (`/upgrade`) localized by Telegram user locale
• Telegram Stars payment handlers:
  - pre-checkout validation handler
  - successful payment handler that upserts `app.payment_events` and activates `app.subscriptions`
• adaptive signal windows in read path (`latest`, then `30m`, then `1h`) for movers/watchlist views
• zero-state diagnostics for inbox/watchlist to distinguish threshold filtering vs missing live quotes

Site + Email API:

• FastAPI app in `api/main.py`  
• waitlist form + double opt-in  
• daily digest worker in `api/digest_job.py` via Resend
• geo/lang-aware landing renderer (`api/web/*.ru.html`, `api/web/*.en.html`)
• SEO endpoints: `/robots.txt`, `/sitemap.xml`, `/og-card.svg`
• SEO intent endpoints: `/analytics`, `/dashboard`, `/signals`, `/telegram-bot`, `/top-movers`, `/watchlist-alerts`
• favicon endpoint: `/favicon.svg` (and `/favicon.ico` fallback)
• site telemetry endpoint: `/api/events` (`page_view`, `tg_click`, `waitlist_intent`)
• live landing data endpoint: `/api/live-movers-preview` (top 3 movers + sparkline points from DB)
• attribution enrichment in telemetry: `placement`, `lang`, `utm_source`, `utm_medium`, `utm_campaign`
• landing uses dark trading-terminal UI with pain-driven hero, live DB-powered “Top movers” widget (3 markets + sparkline mini-charts), scarcity line, and dual CTA (Telegram primary + email waitlist)
• landing includes conversion modules: “what you get in 60 seconds”, mobile sticky Telegram CTA, and static `Historical examples` proof block
• Google Analytics gtag (`G-J901VRQH4G`) injected in landing heads
• site funnel event tracking in `app.site_events`
• SEO telemetry events include `waitlist_intent` on intent pages
• Cloudflare edge DNS + TLS + apex domain (`polymarketpulse.app`)
• Resend mail-auth DNS hosted in Cloudflare (`resend._domainkey` + `send.polymarketpulse.app` SPF)
• Resend domain `polymarketpulse.app` is `verified`
• canonical/og/twitter metadata is absolute URL based
• `hreflang` includes `x-default`
• sitemap publishes localized EN/RU variants for crawl coverage
• schema.org JSON-LD is present on landing (`Organization`, `WebSite`) and SEO intent pages (`WebPage`)
• ops credential inventory for monetization + social distribution lives in `docs/credentials_checklist.md`
• Stripe monetization endpoints:
  - `POST /api/stripe/checkout-session`
  - `GET /stripe/success` (checkout confirmation fallback when webhook is absent)
  - `POST /api/stripe/webhook` (HMAC-verified)
• Landing conversion hierarchy preserved: Telegram + waitlist remain primary; Stripe checkout is isolated in a lower-page PRO block
• Landing PRO block contract (EN/RU):
  - full-width dark section (`#0d0f0e`), no outer rounded card wrapper
  - split layout: FREE/PRO comparison rows + stacked CTAs
  - primary green Stars CTA + secondary outlined Stripe CTA (existing checkout-session flow)
  - mobile behavior: single-column stack with full-width CTA buttons

## Current User Interaction Surfaces (2026-03-10)

End-user entry points and flows:

• Web entry: `polymarketpulse.app` landing and intent pages (`/analytics`, `/dashboard`, `/signals`, `/telegram-bot`, `/top-movers`, `/watchlist-alerts`)  
• Primary CTA path: web Telegram CTA (hero/sticky/SEO CTA) -> `@polymarket_pulse_bot` with `start` payload attribution  
• Secondary CTA path: web waitlist form -> `/api/waitlist` -> `/confirm` double opt-in -> email digest channel  
• Bot activation core: `/start` -> `/menu` + `/movers` -> watchlist add (`/watchlist_add` or picker) -> `/inbox` + push alerts  
• Signal fallback behavior in bot read paths: `latest -> 30m -> 1h` before zero-state explanation

Telemetry and attribution contract:

• site events: `page_view`, `tg_click`, `waitlist_intent` via `/api/events`  
• waitlist events: `waitlist_submit`, `confirm_success`, `unsubscribe_success` in `app.site_events`  
• attribution fields: `placement`, `lang`, `utm_source`, `utm_medium`, `utm_campaign`

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

Universe read selection in ingest is category-balanced (caps + top-up), not pure weight sort, to avoid single-topic dominance.

Ingest observability:

• startup log prints fetched market mix (`p/m/c/o`) for top fetch  
• forced-list log prints selected universe mix (`p/m/c/o`) before snapshot write

Live-only hardening:

• migration `db/migrations/005_live_only_hardening.sql` enforces `active` status across universe rebuild and snapshot views  
• `closed` markets are excluded from `public.market_universe` even when passed from manual/position sources  
• bot watchlist snapshot view is aligned to active-only universe contract

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
• social draft generator: `scripts/growth/generate_social_drafts.py` (DB live views -> EN/RU drafts for X/Threads, with UTM links + Telegram deep links)  
• weekly KPI retro generator: `scripts/growth/weekly_kpi_report.py` (`app.site_events` + activation proxy from `app.identities`/`bot.watchlist`)  
• visual post templates in `assets/social/` (Top3, Breakout, Weekly recap)
• positioning message pack: `docs/positioning_messages_latest.md` (site/bot/social interception copy)

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
