# Polymarket Pulse — Implementation Progress

This document tracks the current state of the project.

---

# Active 14-Day Plan

Current execution plan is tracked in:

`docs/plan_14day_seo_bot_growth_2026-03-09.md`

Scope: SEO + Bot UX + Multi-channel growth with Telegram activation as the primary KPI.

---

# User Path Snapshot (2026-03-10)

Source of truth for this snapshot:

`manifest.md` + `progress.md` + `architecture.md` + `api/main.py` + `bot/main.py` + growth docs in `docs/`.

Current user-facing surfaces:

• website (`https://polymarketpulse.app`) with localized landing + SEO intent pages  
• Telegram bot (`@polymarket_pulse_bot`) as primary activation and retention surface  
• email waitlist + double opt-in + digest follow-up

Acquisition/distribution channels currently operated:

• X  
• Threads  
• Reels/TikTok

Observed activation funnel:

• `page_view -> tg_click -> /start -> watchlist_add -> /inbox + push alerts`  
• optional parallel branch: `page_view -> waitlist_submit -> confirm_success`

Latest 7-day KPI snapshot (`docs/growth_kpi_latest.md`, generated 2026-03-10):

• `page_view=155`, `tg_click=7` (`4.5%`)  
• `started_users=3`, `users_with_watchlist_add=2` (`66.7%` proxy start->watchlist_add)

---

# Landing PRO Block Refresh (2026-03-10)

Updated both localized landing templates (`api/web/index.en.html`, `api/web/index.ru.html`) to a strict dark-system PRO section:

• full-width section on `#0d0f0e` with no outer rounded wrapper  
• monospace kicker + display headline (`20 markets. No cap. Email digest included.`)  
• two-column layout: FREE/PRO comparison rows (left) + stacked Stars/Stripe CTAs (right)  
• primary CTA uses green-only button (`Upgrade in Telegram -> ⭐ 454 Stars`)  
• Stripe checkout keeps existing `/api/stripe/checkout-session` email flow, restyled as outlined secondary action  
• mobile stacks columns and keeps both CTA buttons full-width

---

# Bot Upgrade Flow Refresh (2026-03-10)

Updated Telegram upgrade UX in `bot/main.py`:

• `/upgrade` now sends a compact signal-style PRO message (Stars price + FREE/PRO delta + Stripe fallback link)  
• invoice is sent immediately after the message in the same handler (no intermediate inline keyboard step)  
• `/menu -> Upgrade` path aligned to the same message + immediate invoice sequence  
• `/plan` now ends with explicit CTA line: `→ /upgrade — перейти на PRO` (or EN equivalent by Telegram locale)

---

# Bot Bilingual UX (2026-03-10)

Bot command layer now supports RU/EN response rendering by Telegram `language_code`:

• locale resolver added (`ru` default, `en` for `en-*`)  
• key flows localized: `/start`, `/help`, `/plan`, `/limits`, `/upgrade`, `/threshold`, `/movers`, `/inbox`, `/watchlist`, `/watchlist_add`, `/watchlist_remove`, `/watchlist_list`, callback menu paths  
• Telegram command menu now published in two language sets (`ru`, `en`) via `setMyCommands(language_code=...)`  
• payment flow texts localized for pre-checkout errors, invoice description, and successful payment confirmations

---

# Bot Profile Metadata (2026-03-10)

Bot startup now sets profile metadata for both locales:

• `setMyDescription` for `en` and `ru`  
• `setMyShortDescription` for `en` and `ru`

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

# Universe Diversification Update (2026-03-10)

Applied migration:

`db/migrations/007_market_universe_auto_balance.sql`

Changes:

• `public.refresh_market_universe(...)` auto branch is now category-aware with caps (`politics`/`macro`/`crypto`) + weight-based top-up  
• ingest now reads `public.market_universe` through balanced selection (instead of raw top-by-weight only) for forced coverage on each tick  
• ingest logs now include `universe_mix` (politics/macro/crypto/other) for quick operator diagnostics  
• ingest `fetch_markets()` now uses category-aware rebalancing and root-question dedup, reducing minute-market spam in top fetch

Note:

• current live supply remains crypto-heavy in latest buckets, but universe composition improved from `199 crypto / 1 politics` to `149 crypto / 50 other / 1 politics` after rebalance

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
• Pro: 20 watchlist markets  
• Pro: email digest included  
• Pro pricing target (iteration 1): ~$10/month equivalent in Telegram Stars
• Telegram Stars pricing fixed for current run: `454 XTR`

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
• picker now uses balanced category ordering in `All` mode (politics -> macro -> crypto -> other) with per-category caps
• picker labels now include category tag (`POL/CRY/MAC/OTH`) and suppress near-zero deltas (`abs(delta)<0.001` shows as `LIVE`)
• picker message now shows current live candidate count and explains when live window is narrow
• picker candidate pool now includes recent active markets seen in last 72h snapshots (fallback when live movers are too narrow)
• `/help` reorganized by use-case (plan, signals, watchlist, threshold)  
• `/limits` shows FREE/PRO constraints and current usage  
• `/upgrade` provides explicit conversion path to PRO
• `/plan`, `/limits`, `/upgrade` now explicitly communicate first monetization offer:
  - PRO expands watchlist from 3 to 20
  - includes email digest
  - monthly price target is USD-equivalent in Telegram Stars
• `/upgrade` now logs lead intents into `app.upgrade_intents` for manual sales follow-up
• `/upgrade` now sends Telegram Stars invoice (`XTR`) directly in chat
• successful Stars payment activates PRO immediately via `app.subscriptions` + `bot.profiles`
• payment idempotency guard added through `app.payment_events` (provider/external_id)
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
• schema.org baseline added:
  - landing EN/RU now includes `Organization` + `WebSite` JSON-LD
  - intent pages now include `WebPage` JSON-LD from `render_seo_page`

SMM engine update:

• added competitor sweep script: `scripts/growth/competitive_scan.py`  
• generated extended competitor report: `docs/competitive_sweep_full_2026-03-08.md`  
• generated refreshed competitor snapshot: `docs/competitive_sweep_latest.md` (162 tools parsed from polymark.et)
• extracted 3 interception positioning messages for site/bot/social: `docs/positioning_messages_latest.md`
• upgraded social draft generator: `scripts/growth/generate_social_drafts.py`
  - EN/RU drafts for both `x` and `threads`
  - UTM-tagged site links + Telegram deep links with source/campaign tags
  - configurable minimum delta threshold (`--min-abs-delta`) to avoid low-signal posts
  - weekly recap skeleton included in generated file
• added weekly KPI retro script: `scripts/growth/weekly_kpi_report.py`
  - funnel from `app.site_events`: `page_view -> tg_click -> waitlist_submit -> confirm_success`
  - `tg_click` split by `utm_source` and by placement
  - activation proxy from DB: `telegram identities -> users_with_watchlist_add`
• refreshed operational docs:
  - `docs/social_pipeline.md`
  - generated snapshots: `docs/social_drafts_latest.md`, `docs/growth_kpi_latest.md`
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
• Added browser favicon pack (`/favicon.ico`, `/favicon-32x32.png`, `/favicon-48x48.png`, `/apple-touch-icon.png`) and Telegram CTA on landing
• Added site event endpoint (`/api/events`) for `page_view` and `tg_click`
• `app.site_events.details` now stores attribution payload: `placement`, `lang`, `utm_source`, `utm_medium`, `utm_campaign`
• Waitlist flow now forwards attribution into confirm/unsubscribe funnel events
• Landing fully redesigned (RU/EN): dark trading-terminal aesthetic, pain-driven hero, live DB-powered “Top movers” preview (3 markets + mini-sparklines), dual CTA hierarchy (Telegram primary + email waitlist secondary)
• Added landing API endpoint `/api/live-movers-preview` (reads `public.top_movers_latest` + recent `market_snapshots`) for real-time homepage proof
• Added integration checklist for monetization/distribution credentials: `docs/credentials_checklist.md`
• Added Stripe checkout flow:
  - `POST /api/stripe/checkout-session`
  - `GET /stripe/success` (server-side session confirmation + PRO activation)
  - `POST /api/stripe/webhook` (signature-verified event intake)
• Checkout CTA moved out of main hero flow into a separate bottom `PRO` section to keep primary activation focused on Telegram + waitlist
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
