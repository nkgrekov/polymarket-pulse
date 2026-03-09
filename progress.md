# Polymarket Pulse — Implementation Progress

This document tracks the current state of the project.

---

# Active 14-Day Plan

Current execution plan is tracked in:

`docs/plan_14day_seo_bot_growth_2026-03-09.md`

Scope: SEO + Bot UX + Multi-channel growth with Telegram activation as the primary KPI.

---

# DB Hardening Update (2026-03-09)

Applied migration:

`db/migrations/005_live_only_hardening.sql`

Changes:

• `public.refresh_market_universe(...)` now filters out `closed` markets for all sources (`manual`, `position`, `auto`)  
• `public.top_movers_latest`, `public.portfolio_snapshot_latest`, `public.watchlist_snapshot_latest` additionally enforce `markets.status='active'`  
• `bot.watchlist_snapshot_latest` aligned to same active-only universe contract  

Post-migration snapshot:

• `public.market_universe`: 200 total, `closed=0`  
• live-only scope is now consistent at universe + snapshot-view layer

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
app.upgrade_intents  
app.site_events  
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

Primary commands in Telegram menu:

/start  
/movers  
/watchlist  
/inbox  
/plan  
/help  

Advanced commands (kept available via typing and `/help`):

/menu  
/upgrade  
/limits  
/threshold  
/inbox20  
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

Onboarding UX update:

• `/start` now includes “what bot does” + 60-second quick start flow  
• `/start` now adds reply keyboard + inline `/menu` actions for core flow  
• added callback-driven action menu (`/menu`) with fast entry to movers/watchlist/inbox/plan/upgrade  
• `/watchlist_add` without args now opens top-movers picker (no manual market_id copy)  
• watchlist picker expanded: `movers + liquid live + fresh active markets` (fallback), plus “Обновить список” action  
• picker relevance tuning: candidate ranking now prioritizes live movers by liquidity (volume proxy), then live-liquidity fallback; removed noisy fresh-feed bias
• watchlist picker now supports quick category filters (`All`, `Crypto`, `Politics`, `Macro`) via inline callbacks
• category fallback fixed: filters no longer leak unrelated markets; if category has no live candidates, bot explains it explicitly
• `/help` reorganized by use-case (plan, signals, watchlist, threshold)  
• `/limits` shows FREE/PRO constraints and current usage  
• `/upgrade` provides explicit conversion path to PRO
• `/upgrade` now logs lead intents into `app.upgrade_intents` for manual sales follow-up
• `/movers` now uses adaptive fallback windows (latest -> 30m -> 1h)
• `/watchlist` now uses adaptive fallback windows (latest -> 30m -> 1h)
• `/inbox` and `/watchlist` now return diagnostic zero-state reasons (threshold too high vs no live quotes/closed markets)

SEO/Conversion update:

• added 6 SEO intent pages: `/analytics`, `/dashboard`, `/signals`, `/telegram-bot`, `/top-movers`, `/watchlist-alerts`  
• sitemap now includes SEO pages  
• main landing (EN/RU) now links to these intent pages and includes FAQ block for `/movers` zero-state
• dark design consistency pass completed from `better site.md` rules:
  - landing and SEO pages now share one dark terminal palette
  - no light blocks / no yellow CTA variants / no bullet lists
  - historical proof cards and intent tags now use unified card+pill system
  - FAQ block is rendered as dark callout with terminal-style prefix marker
• technical SEO hardening completed:
  - canonical/og:url/twitter:url moved to absolute URLs
  - `hreflang` now includes `x-default`
  - sitemap expanded to EN/RU URL variants for home/privacy/terms/intent pages
• conversion polish on SEO intent pages:
  - primary CTA remains Telegram bot
  - secondary CTA added: Email waitlist (`#waitlist-form`) with event tracking (`waitlist_intent`)

SMM engine update:

• added competitor sweep script: `scripts/growth/competitive_scan.py`  
• generated extended competitor report: `docs/competitive_sweep_full_2026-03-08.md`  
• added social draft generator from live views: `scripts/growth/generate_social_drafts.py`  
• added visual templates: `assets/social/*.svg` and operation doc `docs/social_pipeline.md`

Deploy status update (2026-03-08):

• Railway `site` redeployed from `api/` path root (fixed build context)  
• Railway `bot` redeployed from `bot/` path root (fixed build context)  
• smoke checks passed on `/analytics`, `/dashboard`, `/signals`, `/telegram-bot`, `/top-movers`, `/watchlist-alerts`  
• `sitemap.xml` now includes all SEO intent pages

Competitive strategy update:

• added market landscape memo: `docs/competitive_landscape_2026-03-08.md`  
• positioning fixed on mainstream Telegram activation and simple signal-first UX

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
• waitslist/confirm/unsubscribe funnel events are logged into `app.site_events`  
• Resend integration for confirmation/welcome  
• `api/digest_job.py` sends daily digest from `bot.alert_events`
• `.github/workflows/digest.yml` runs digest daily (and supports manual trigger)
• Landing is localized (`RU`/`EN`) with auto-detection by geo/lang headers
• SEO baseline added: `robots.txt`, `sitemap.xml`, `og-card.svg`
• Added browser favicon (`/favicon.svg`) and Telegram CTA on landing
• Added site event endpoint (`/api/events`) for `page_view` and `tg_click`
• `app.site_events.details` now stores attribution payload: `placement`, `lang`, `utm_source`, `utm_medium`, `utm_campaign`
• Waitlist flow now forwards attribution into confirm/unsubscribe funnel events
• Landing fully redesigned (RU/EN): dark trading-terminal aesthetic, pain-driven hero, live mock “Top movers”, dual CTA hierarchy (Telegram primary + email waitlist secondary)
• Added conversion UX upgrades: “what you get in 60 seconds”, mobile sticky Telegram CTA, and clear CTA hierarchy
• Added static social-proof block `Historical examples` (Dec–Mar sample cards, explicitly non-live)
• Google Analytics tag (`G-J901VRQH4G`) embedded in all landing variants (`index.en.html`, `index.ru.html`, `index.html`)
• `site` sender configured to use `welcome@polymarketpulse.app` (Resend from-address)
• Resend DNS records configured in Cloudflare (`resend._domainkey`, `send` MX/TXT)
• Resend domain status is `verified`; confirmation/welcome flow can send from `welcome@polymarketpulse.app`
• Production custom domain active: `https://polymarketpulse.app`
• `www.polymarketpulse.app` redirects to apex via Cloudflare page rule
• Existing Railway `site` service redeployed from local source root `api/`; production serves redesigned landing
• Competitive sweep + social distribution plan documented in `docs/growth_sweep_2026-03-06.md`

---

# Next Milestones

Railway deploy (bot + site)

Payment integration for `pro`

Web auth linking to Telegram identity

iOS client integration
