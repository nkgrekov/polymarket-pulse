# Polymarket Pulse — System Architecture

This document describes the technical architecture.

---

# Active Execution Plan Link

Operational 14-day delivery plan is versioned in:

`docs/plan_14day_seo_bot_growth_2026-03-09.md`

Current weekly operating priorities are tracked in:

`docs/weekly_operating_board_2026-03-17.md`

Architecture and rollout priorities must stay aligned with that plan and with `manifest.md`.

---

# Pulse Watchlist Add Outcome Contract (2026-03-17)

The Pulse bot now uses a single watchlist-add outcome contract across both manual and picker-driven onboarding.

Updated artifact:

• `bot/main.py`

Contract additions:

• `add_watchlist_market_sync(...)` now returns a structured outcome payload instead of only a raw string
• current outcome types:
  - `added`
  - `replaced`
  - `exists`
  - `limit`
  - `missing`
• `added` outcomes now also carry `live_state` metadata:
  - `ready`
  - `partial`
  - `no_quotes`
  - `closed`
• `/watchlist_add <market_id|slug>` now routes through the same contract as picker callbacks
• when the watchlist is full, handlers can now attach the same recovery/replacement inline surface instead of diverging into a dead-end limit response
• post-add handlers can now merge the standard watchlist actions with live replacement candidates when the selected market is still quiet

Why this matters:

• Telegram activation should not depend on whether the user taps a picker button or types a market id/slug manually
• keeping one post-add/recovery contract reduces handler drift and preserves momentum during the first-value flow

---

# Pulse Plan / Upgrade Messaging Layer (2026-03-18)

The Pulse bot now treats `/plan` and `/upgrade` as product-state surfaces rather than generic command replies.

Updated artifact:

• `bot/main.py`

Contract additions:

• `plan_message_text(user_ctx, locale=...)` now centralizes the plan-state copy for both slash commands and callback menu entrypoints
• plan responses now branch by commercial state:
  - `FREE`
  - `PRO`
• FREE responses expose:
  - remaining watchlist capacity
  - current threshold
  - alerts used today
  - concise PRO delta
• PRO responses expose:
  - current threshold
  - remaining watchlist capacity
  - closed-market residue in watchlist, when present
  - best next step
• `/upgrade` now short-circuits for `PRO` users and redirects them back into product usage rather than payment
• Stripe fallback links now target the current EN-only acquisition surface (`/telegram-bot#pro`)

Why this matters:

• the monetization layer should reinforce the core Pulse loop, not interrupt it with stale or redundant payment messaging
• keeping `/plan` and `/upgrade` state-aware reduces confusion for both free and upgraded users

---

# Manual Tabs Pain Video Layer (2026-03-17)

The growth stack now has a first post-specific short-form render, not just generic social cards or a generic glitch clip.

New artifact path:

• `scripts/growth/render_manual_tabs_short.py`

Output contract:

• `assets/social/out/manual-tabs-pain-5s.mp4`
• `assets/social/out/manual-tabs-preview-01.png`
• `assets/social/out/manual-tabs-preview-02.png`
• `assets/social/out/manual-tabs-preview-03.png`

Render contract:

• source of truth is still live DB data (`public.top_movers_latest`)
• thesis is fixed to the paired pain-first post:
  - `12 tabs open`
  - `move already happened`
  - real market delta
  - `workflow too manual`
  - Telegram CTA
• visual grammar must stay inside the current brand system rather than using stock promo backgrounds

Operational implication:

• short-form growth is now split into:
  - generic branded glitch testing (`render_shitpost_short.py`)
  - post-specific pain-first clips (`render_manual_tabs_short.py`)

---

# Pain Short Renderer Pack (2026-03-17)

The social video layer now has a reusable renderer for additional post-specific pain clips.

New artifact path:

• `scripts/growth/render_pain_short.py`

Current supported themes:

• `alert-fatigue`
• `dashboard-overload`

Output contract:

• `assets/social/out/alert-fatigue-5s.mp4`
• `assets/social/out/dashboard-overload-5s.mp4`
• matching preview PNG triplets for each clip

Render contract:

• still uses live DB input from `public.top_movers_latest`
• each theme has its own micro-sequence and messaging contract
• this keeps short-form growth tied to the written pain-first social batch rather than drifting into generic promo visuals

Operational implication:

• the first manual posting batch now has a complete top-3 video set:
  - manual tabs pain
  - alert fatigue
  - dashboard overload

---

# Just-In-Time Social Candidate Contract (2026-03-17)

The social draft layer now has explicit freshness and quality gates.

Updated artifact:

• `scripts/growth/generate_social_drafts.py`

Current candidate contract:

• data source remains:
  - `public.top_movers_latest`
  - `bot.alerts_inbox_latest`
• candidates must also pass:
  - latest-bucket freshness gate (`--max-age-minutes`, default `30`)
  - latest-bucket liquidity gate (`--min-liquidity`, default `5000`)
• latest-bucket liquidity is resolved from `public.market_snapshots`

Operational implication:

• social generation is now explicitly just-in-time
• we should generate the draft pack immediately before manual posting
• if the live window is stale or too thin, skipping the post is the correct behavior

Why this matters:

• protects the social layer from posting dead market moves
• keeps content closer to real user FOMO/friction
• aligns the growth layer with the core product rule: signal quality over feed volume

---

# Search Indexing Contract Pass (2026-03-16)

The public site now uses a more explicit indexing contract for localized pages.

Previous inconsistency:

• localized pages were discoverable and listed in sitemap as `?lang=en|ru`
• several templates and the SEO renderer pointed canonical URLs to the same path without the query parameter
• this created a weak duplicate/variant signal for Google on a young domain

Current contract:

• acquisition/content pages self-canonicalize to their own localized URL
  - `/?lang=en`
  - `/?lang=ru`
  - `/<slug>?lang=en|ru`
• `hreflang` alternates remain explicit for `en`, `ru`, and `x-default`
• sitemap now includes only indexable acquisition/content surfaces:
  - homepage
  - SEO intent pages
  - `/how-it-works`
  - `/commands`
  - `/trader-bot`
• sitemap now includes `xhtml:link` hreflang alternates per URL entry

Legal-page contract:

• `/privacy` and `/terms` remain available to users
• but they are now `noindex,follow`
• they are intentionally excluded from sitemap so crawl focus remains on acquisition and product pages

Operational implication:

• GSC redirect reports for `http://` and `www.` should still be treated as normal canonicalization behavior
• the meaningful indexing KPI is whether the canonical localized URLs start moving from "discovered" into "indexed"

---

# Manual Social Operator Batch (2026-03-16)

The growth layer now includes a ready-to-publish operator artifact for manual distribution.

Artifact:

• `docs/social_posting_batch_2026-03-16.md`

Contract:

• social publishing can continue even while API posting is blocked
• UTM-tagged manual posting remains compatible with GA4 + `app.site_events` attribution
• short-form videos are prioritized only for the strongest first 3 posts, not for the whole batch

X delivery state:

• auth/write scope is valid
• automated posting remains blocked by account credits rather than by permissions
• current API failure mode is `402 CreditsDepleted`, so manual posting stays the live distribution mode until credits are added

---

# Pain-First Social Content Layer (2026-03-16)

The growth layer now has a defined content operating model instead of ad-hoc posting ideas.

Artifacts:

• `docs/social_sprint_pain_first_2026-03-16.md`
• `docs/social_video_briefs_2026-03-16.md`

Contract:

• social messaging is pain-first, not slogan-first
• X/Threads posts must map back to concrete product friction:
  - manual scanning
  - alert fatigue
  - dashboard overload
  - watchlist decay
  - signal/execution gap
• short-form videos are support assets for specific posts, not standalone hype clips
• all social visuals must stay inside the current terminal/dark-green brand system

External delivery blocker currently confirmed:

• X OAuth1 posting permissions are now fixed
• the active blocker is API credits/quota on the enrolled X account

---

# Full EN Acquisition Copy Consistency (2026-03-16)

The shared SEO renderer now carries a more consistent action-first copy layer across the full English acquisition set.

Additional surfaces aligned in this pass:

• `/dashboard`
• `/top-movers`
• `/watchlist-alerts`

Renderer implication:

• the same page-aware CTA note and conversion copy model now spans the complete EN acquisition set, not just the initial high-intent trio
• this reduces messaging drift between intent pages and keeps the acquisition layer closer to the actual Telegram-first product flow

---

# EN Intent CTR Layer (2026-03-16)

The FastAPI-rendered SEO pages now carry a slightly stronger conversion contract on the highest-intent English surfaces.

Renderer-level additions:

• high-intent pages can now override secondary CTA wording through page-aware copy logic
• CTA rows now include a small support note (`cta-note`) that explains the next step in plain language
• English copy for `analytics`, `signals`, and `telegram-bot` now emphasizes action, thresholding, and low-noise delivery over generic dashboard language

Architectural reason:

• these pages are acquisition surfaces, not documentation pages
• the copy must move users into the Telegram activation funnel, not just describe features
• keeping this logic in the shared renderer preserves consistency while avoiding page-template sprawl

---

# Intent Page Enrichment Layer (2026-03-16)

The English SEO pages now have a stronger content and telemetry contract.

Renderer contract additions in `api/main.py`:

• each SEO intent page can now expose a dedicated FAQ block from `SEO_PAGE_FAQ`
• the same FAQ content is serialized into `FAQPage` JSON-LD
• related links are now curated via `SEO_PAGE_LINKS` rather than generated as a flat list of every other page
• dynamic SEO pages now emit the same dual-tracking behavior as static pages:
  - GA4 via `window.gtag(...)`
  - backend telemetry via `/api/events` into `app.site_events`

Why this shape is preferable:

• it increases page specificity without exploding the number of templates
• it keeps internal linking aligned with the actual acquisition funnel (`analytics -> signals -> telegram-bot -> trader-bot`)
• it preserves the current FastAPI-rendered SEO page model while making those pages less thin and more measurable

---

# EN-Only Public Site Mode (2026-03-16)

The public website now operates in an English-first SEO mode.

Routing contract:

• public site routes default to English
• Russian pages are still renderable only when `?lang=ru` is explicit
• this is implemented via a separate `detect_site_lang(...)` path instead of changing the generic request-language helper used elsewhere

Indexing contract:

• English pages are the only indexable public layer
• Russian public pages are fallback-only and explicitly `noindex,follow`
• sitemap now contains only English canonical URLs
• clean English paths are the canonical layer:
  - `/`
  - `/analytics`
  - `/dashboard`
  - `/signals`
  - `/telegram-bot`
  - `/top-movers`
  - `/watchlist-alerts`
  - `/how-it-works`
  - `/commands`
  - `/trader-bot`

Template contract:

• EN/RU switchers were removed from public site templates
• internal site links now point to clean English paths
• Russian templates remain in repository, but are treated as non-indexed fallback surfaces rather than primary search targets

Why this architecture is preferable now:

• the domain is young and should not split crawl/indexing signals across two query-param language layers
• current growth and content distribution are English-first
• Telegram bots can stay multilingual without forcing the site layer to carry the same indexing complexity

---

# Signer Session Layer (2026-03-15)

Execution alpha now includes a dedicated signer-session bridge between `trader_bot` and the main site runtime.

New data contract:

• `trade.signer_sessions`

State model:

• `new`
• `opened`
• `signed`
• `verified`
• `expired`
• `revoked`

Current runtime behavior:

• `trader_bot:/signer` creates/reuses signer sessions tied to the primary wallet in `trade.wallet_links`
• the bot emits:
  - challenge text
  - signer-session status
  - direct URL into `GET /trader-connect?token=...`
• `GET /trader-connect` is served by `api/main.py` and marks `new -> opened`
• `POST /api/trader-signer/submit` stores signed payload into `trade.signer_sessions.signed_payload` and marks the session `signed`
• `trade.activity_events` receives site-side signer submission telemetry

Boundary that remains explicit:

• signer session storage is now real
• signer verification is not yet real
• wallet activation is still not granted automatically from signer-session submission
• execution worker therefore still uses `trade.wallet_links.status` as the hard execution gate

Why this shape is correct:

• keeps `Pulse` and `Trader` separate while reusing the main site runtime for signer UX
• creates a production-safe transition layer before cryptographic verification and live routing
• avoids faking "connected signer" state before actual verification exists

---

# Manual Signer Activation Contract (2026-03-15)

Added the next alpha bridge after signer payload capture.

Runtime shape:

• site captures signer payload -> `trade.signer_sessions.status='signed'`
• operator review activates session through `trade.activate_signer_session(...)`
• activation updates both signer-session state and wallet execution readiness

Activation side-effects:

• `trade.signer_sessions.status='verified'`
• `trade.signer_sessions.verified_at` populated
• `trade.wallet_links.status='active'`
• `trade.wallet_links.signer_kind='session'`
• `trade.wallet_links.signer_ref` set to operator-provided ref or session token fallback
• `trade.activity_events.event_type='signer_activated'`

Operational interface:

• local/manual alpha review script:
  - `scripts/ops/activate_signer_session.py`

Why this is the right interim architecture:

• it keeps live execution gated behind explicit human approval during alpha
• it avoids pretending we have cryptographic auto-verification before we actually do
• it gives `trade-worker` a real transition path from `requires_signer:*` to executable wallet state

---

# Pulse Start Activation Layer (2026-03-15)

`Pulse` onboarding now includes a dedicated activation CTA layer before the general menu.

Runtime behavior in `/start`:

• first message still explains the product and current limits
• second message now presents focused onboarding actions:
  - add first market
  - top movers
  - plan
  - help
• generic quick menu is still sent after that for broader navigation

Reason:

• this preserves the compact command architecture from the 14-day plan
• but it reduces friction on the `tg_click -> /start -> watchlist_add` path, which remains the primary KPI on the Pulse rail

Extended onboarding behavior:

• if watchlist is empty, `/start` now also renders up to 3 live one-tap candidate markets
• these buttons reuse the same picker token/callback contract as the full watchlist picker
• fallback remains the full picker (`menu:pick`) if the user wants a broader set

Trader operator loop extension:

• pending signer review is now supported by `scripts/ops/list_signer_sessions.py`
• activation remains explicit and human-gated through `scripts/ops/activate_signer_session.py`

Readiness UX extension:

• `Trader` command layer now computes a user-visible readiness line from primary wallet state
• readiness states are still simple but operational:
  - `ready_for_dry_run` when primary wallet is `active`
  - signer-blocked when wallet is still `pending`
• this readiness copy is surfaced in `/connect`, `/risk`, and draft-order confirmations
• `/order` now acts as the first user-facing execution-state surface on top of `trade-worker`:
  - pending drafts render as `queued_for_worker`
  - rejected drafts render `blocked` with actionable next steps
  - accepted dry-run drafts render `accepted_by_dry_run_worker` with explicit alpha-only wording

Pulse post-add flow extension:

• watchlist add success is no longer a dead-end text response
• bot now returns next-step inline actions after add:
  - `Watchlist`
  - `Inbox`
  - `Threshold`
  - `Add one more`
• add success now also computes a per-market first-value state from live data:
  - has quotes in `last+prev`
  - has partial quotes only
  - has no quotes in `last+prev`
  - is already closed
• this keeps activation honest: user sees immediately whether the chosen market is ready for signal surfaces or likely to stay quiet for now
• empty-state recovery is now action-oriented:
  - `/watchlist` and `/inbox` can render up to 2 one-tap live replacement candidates
  - fallback still keeps access to `Top movers` and full picker
  - closed-market cleanup action remains available when relevant
• recovery candidates now support watchlist replacement semantics:
  - if user is already at watchlist limit, callback path switches from `add` to `replace`
  - replacement target is selected deterministically from current watchlist (`closed` first, then oldest)
  - this avoids dead-end limit errors in first-value recovery states
• execution handoff from `Pulse` inline surfaces now uses a Telegram deep-link into `@PolymarketPulse_trader_bot` instead of bouncing the user through the website inside Telegram
• `/plan` and `/upgrade` are now treated as activation surfaces, not just information surfaces:
  - current usage is summarized first
  - next action buttons are embedded directly in the reply
  - this keeps upgrade/threshold/add flows one tap away from plan-state inspection

Trader signer-state extension:

• signer status is no longer isolated inside `/signer`
• `/connect` and `/risk` now surface signer-session state as a separate UX layer:
  - `not_started`
  - `opened`
  - `signed`
  - `verified`
• this makes the alpha approval funnel legible without exposing internal DB terminology or requiring site navigation on every check
• `/start` now also includes current execution readiness when a primary wallet already exists, so returning users see status before diving into deeper commands
• both bots now use human-labeled reply keyboards rather than slash-command text on the keyboard surface
• a thin text-routing layer maps those labels back into the same command handlers, so the UX is cleaner without changing bot logic contracts

---

# Trader Bot Runtime Layer (2026-03-14)

The dual-product architecture now includes an actual sibling Telegram runtime for execution alpha:

• `Pulse bot` = signal/discovery/intelligence (`@polymarket_pulse_bot`)
• `Trader bot` = execution-control alpha (`@PolymarketPulse_trader_bot`)

Implementation boundary:

• the trader bot is isolated in `trader_bot/`
• it reuses the shared identity layer (`app.*`, `bot.resolve_or_create_user_from_telegram(...)`)
• it writes only into the dedicated execution schema (`trade.*`) for trader-specific state and telemetry

Current trader-bot runtime contract:

• `/connect` -> `trade.wallet_links`
• `/buy` + `/sell` -> `trade.orders` (`pending` draft state only)
• `/positions` -> `trade.positions_cache`
• `/follow` -> `trade.follow_sources` + `trade.follow_rules`
• `/rules` -> `trade.agent_rules`
• `/risk` + `/pause` -> `trade.risk_state`
• `/agent` -> `trade.agent_decisions`
• all command intent -> `trade.activity_events`

Deployment state:

• trader-bot now runs as a separate Railway production service: `trader-bot`
• deploy path is monorepo-scoped via `railway up -s trader-bot --path-as-root trader_bot`
• production runtime confirms Telegram polling for `@PolymarketPulse_trader_bot`

Execution worker layer:

• separate service `trade-worker` now owns the first execution state-machine loop
• deploy path is monorepo-scoped via `railway up -s trade-worker --path-as-root trade_worker`
• current worker mode is deliberately `dry_run`
• worker contract:
  - reads `trade.orders.status='pending'`
  - checks signer/wallet/risk constraints
  - updates order status to `submitted` (dry-run) or `rejected`
  - emits `trade.activity_events`
  - increments `trade.risk_state` counters on accepted dry-run submissions

Trader UX/readiness contract:

• `/connect` acts as both setter and readiness inspector
• `/order` now reflects worker-state feedback per draft order via `trade.activity_events`
• `/risk` includes wallet/signature readiness context so the user sees why execution is not yet live

Pulse acquisition/positioning contract:

• `/telegram-bot` SEO page now includes an explicit comparison layer:
  - dashboard overload vs action-first Telegram flow
  - copy-trading vs signal-first execution handoff
  - `Pulse -> Trader` as the core product stack

Important operational truth:

• trader-bot v0 is a control-plane/runtime scaffold, not a live execution engine
• no signer delegation, order routing, fill reconciliation, or Polymarket submission is active yet
• stored orders represent alpha drafts so the next execution worker layer has a clean contract

---

# Dual-Product Extension (2026-03-13)

Competitive response architecture is now explicitly dual-product:

• `Pulse` = signal/discovery/intelligence layer  
• `Trader` = execution layer (alpha foundation only, sibling product)

Hard boundary:

• current Pulse bot remains signal-first and does not absorb trade execution codepaths
• execution is exposed as a sibling lane through handoff surfaces, not as a hidden submenu inside Pulse

Current implementation level:

• site + Pulse bot can now hand users into execution alpha intent
• data layer and schema contract for future execution bot exist
• actual order-routing / wallet signing / execution worker are not public yet

This keeps the manifesto intact:

• we are still building the intelligence layer first  
• trade execution becomes an adjacent expansion, not a pivot away from signals

---

# Operational Snapshot (2026-03-11)

Latest scope verification covered `db` migrations/views, ingest code path, bot runtime path, and web/SEO rendering path.

Current live-state highlights:

• ingest freshness is within one 5-minute bucket (`latest market_snapshots bucket lag ~540s` at capture time)
• live universe contract remains `200` markets with active-only filtering and balanced category rebalance in function layer
• universe source split at snapshot time: `auto=199`, `manual=1`; no closed markets present in universe
• bot/user layer remains multi-tenant schema-first (`app.*` + `bot.*`) with Telegram identity resolution and plan lookup through `bot.current_plan(...)`
• monetization plumbing is deployed (`app.payment_events`, Stars handlers, Stripe endpoints), but no successful payment event is currently stored
• landing + SEO pages are running one visual contract (dark palette, `Space Grotesk` + `JetBrains Mono`, short reveal animations, shared CTA hierarchy)

Operational risks observed in runtime evidence:

• polling conflict occurred in bot logs (`getUpdates 409`) indicating concurrent bot instance overlap on 2026-03-05
• local launchd bot service currently not loaded, so local process state does not represent persistent production uptime
• free-plan historical watchlist rows can exceed current add-flow cap due to legacy records; cap is enforced on new writes in bot command handlers

---

# Polymarket Referral / Builder Feasibility Snapshot (2026-03-12)

External program state validated against current public docs:

• `polymarket.com` public docs currently expose Builder Program mechanics (tiers, weekly rewards, order attribution, and revshare), not a simple consumer invite-link flow in developer/help surfaces.
• order attribution in Builder Program is tied to CLOB order flow and requires builder credentials plus attribution metadata in requests (`POLY_BET_ID`, `POLY_SIGNATURE`, `POLY_TIMESTAMP`, `POLY_API_KEY`, `POLY_PASS_PHRASE`, `X-BUILDER-ID`).
• Help Center geoblock policy still applies to platform usage (regional restrictions and anti-VPN enforcement).
• separate `polymarketexchange.com` Terms publish a Referral Incentive Program notice dated 2026-01-16, effective 2026-02-02 (US exchange track, distinct from builder API docs).

Architecture implication for Polymarket Pulse:

• current product surfaces (site + Telegram + email) are signal/discovery only and do not route user orders through our own execution layer.
• without our own attributed execution path, market promotion links can drive traffic but do not create Builder Program-attributed trading volume on our side.
• to monetize via Builder Program, referral path must be `our surface -> our trade execution integration -> CLOB order with builder attribution`.

Minimal extension points that fit current stack:

• add market deep-link entity to delivery payloads (`market_id`, `slug`, destination url, campaign tag).
• extend `app.site_events` taxonomy for outbound market clicks and downstream trade intent correlation.
• add scheduled builder reconciliation job (builder trades + rewards sync) into existing worker model (GitHub Actions/Railway cadence).

---

# Bot Guide Surface Update (2026-03-11)

Added dedicated bot guidance surfaces into the web layer:

• `GET /how-it-works` -> scenario-first command onboarding (RU/EN templates)
• `GET /commands` -> full command reference (RU/EN templates)

Routing and discovery contract:

• both pages are localized through existing `detect_lang(...)` + `?lang=...`
• both pages are published in `sitemap.xml` (`en` + `ru` variants)
• landing and SEO `/telegram-bot` include explicit handoff to `/how-it-works`
• bidirectional nav between guide surfaces:
  - `/how-it-works` -> `/commands`
  - `/commands` -> `/how-it-works`

Telemetry contract remains stable:

• no new site event types
• attribution is captured via existing `page_view` + `details.placement`

---

# Live Movers Preview Contract Update (2026-03-12)

Landing endpoint `GET /api/live-movers-preview` now uses a snapshot-window spark contract:

• spark source is per-market `market_snapshots` history (up to last 16 points), not a short fixed-hour cut only  
• points are ordered strictly `ts_bucket ASC` (old -> new) for left-to-right chart consistency  
• value extraction is yes-side mid with fallback to available side quote when only one side is present  
• if fewer than 2 points exist for a market, API returns `spark: []` (frontend handles empty sparkline)

To keep visual signal quality on landing, preview row selection prioritizes movers with richer spark history.

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
trade.accounts
trade.wallet_links
trade.positions_cache
trade.orders
trade.executions
trade.follow_sources
trade.follow_rules
trade.agent_rules
trade.agent_decisions
trade.risk_state
trade.activity_events
trade.alpha_waitlist

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
/trade
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
• picker data source uses latest per-market quote from a rolling 6h snapshot window (not strictly one latest bucket), improving candidate breadth during sparse windows
• picker excludes markets already in user watchlist to keep “add next market” flow actionable
• category filter behavior is strict: no cross-category fallback; empty category returns explicit UX guidance
• `all` picker mode applies category-balanced quotas and ordering to reduce crypto dominance in candidate list
• category/refresh picker callbacks edit existing picker message instead of appending new bot messages, reducing chat noise
• picker UI includes category tags and live-supply hint (candidate count in current window)
• picker activation hardening update:
  - explicit liquidity floor (`WATCHLIST_PICKER_MIN_LIQUIDITY`, default `1000`)
  - picker now accepts only markets with live bid/ask quotes in the last 6h window above that liquidity floor
  - `recent_seen` fallback has been removed from picker suggestions; manual `/watchlist_add <market_id|slug>` remains the escape hatch for edge cases
  - ranking uses a hybrid score (`abs(delta) * 100 + ln(1 + liquidity)`) so onboarding suggestions are both active and tradable, instead of being ranked by raw delta only
  - `public.market_universe` is used as the fallback live-liquidity pool to keep picker suggestions aligned with the curated coverage layer
• `/upgrade` command writes conversion intent into `app.upgrade_intents`
• `/trade` command writes execution-interest intent into `trade.activity_events`
• signal views now support market-level handoff into Trader Alpha (`/trader-bot`) from movers/watchlist/inbox
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
• bilingual delivery contract:
  - bot locale is resolved from Telegram `language_code` (`en-*` -> EN, fallback RU)
  - command/menu copy has RU and EN variants for core command set
  - Telegram command catalog is registered in two language scopes (`ru`, `en`)
  - bot profile metadata is set at startup for both locales (`setMyDescription`, `setMyShortDescription`)
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
• execution launch page: `/trader-bot`
• SEO intent endpoints: `/analytics`, `/dashboard`, `/signals`, `/telegram-bot`, `/top-movers`, `/watchlist-alerts`
• favicon endpoint: `/favicon.svg` (and `/favicon.ico` fallback)
• site telemetry endpoint: `/api/events` (`page_view`, `tg_click`, `waitlist_intent`, `checkout_intent`)
• live landing data endpoint: `/api/live-movers-preview` (top 3 movers + sparkline points from DB)
• attribution enrichment in telemetry: `placement`, `lang`, `utm_source`, `utm_medium`, `utm_campaign`
• landing uses dark trading-terminal UI with pain-driven hero, live DB-powered “Top movers” widget (3 markets + sparkline mini-charts), scarcity line, and dual CTA (Telegram primary + email waitlist)
• landing visual contract upgraded to App Store-grade presentation:
  - typography pair: `Space Grotesk` (display) + `JetBrains Mono` (data/terminal copy)
  - hero includes product/rating badges and compact signal-performance metrics cards
  - dedicated `Preview screens` section (3 product-surface cards) added between hero and proof modules
  - “App Store-grade UX” badge copy removed from EN/RU templates and SEO renderer to reduce marketing noise
  - hero two-column block (`movers` + `CTA`) now uses equal-height grid/flex alignment to prevent visual seam at column join
• landing includes conversion modules: “what you get in 60 seconds”, mobile sticky Telegram CTA, and static `Historical examples` proof block
• Google Analytics gtag (`G-J901VRQH4G`) injected in landing heads
• site funnel event tracking in `app.site_events` with dual-delivery:
  - GA4 mirror via `gtag('event', ...)`
  - `sendBeacon` primary delivery + `fetch keepalive` fallback for outbound-click reliability
• landing conversion placements explicitly tracked: `hero_panel`, `mobile_sticky`, `how_it_works_link`, `pro_offer`, `pro_stars`, `waitlist_form`
• Trader Alpha conversion placements added through existing telemetry taxonomy:
  - `landing_trade_strip`
  - `seo_trader_alpha`
  - `trader_alpha_form`
  - `trader_alpha_to_pulse`
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
• SEO page renderer (`render_seo_page`) now mirrors landing visual system:
  - badge row, compact stats cards, preview-surface cards, and CTA row hierarchy
  - same dark palette + typography pair as landing
• Motion contract for web surfaces:
  - one-shot reveal animations (`<= 300ms`) for entry/stagger
  - no infinite decorative animations
  - mandatory `prefers-reduced-motion` fallback

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
• Typography: `Space Grotesk` for display/headings, `JetBrains Mono` for data labels/copy
• Motion: short one-shot reveal/stagger transitions only (`<=300ms`), no infinite decorative loops
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
• competitive decision docs:
  - `docs/competitive_gap_matrix_2026-03-12.md` (top-7 gap matrix + interception angles + 7-day execution list)
  - `docs/competitive_sweep_latest.md` (top-30 directory baseline and cluster mix)
• social draft generator: `scripts/growth/generate_social_drafts.py` (DB live views -> EN/RU drafts for X/Threads, with UTM links + Telegram deep links)
  - current production mode: EN-only publishing (`--langs en`) for X/Threads
• weekly KPI retro generator: `scripts/growth/weekly_kpi_report.py` (`app.site_events` + activation proxy from `app.identities`/`bot.watchlist`)
• visual post templates in `assets/social/` (Top3, Breakout, Weekly recap)
• template-render pipeline now supports Placid MCP renders from live DB:
  - script: `scripts/growth/generate_social_visuals.py`
  - output contract: `docs/social_visuals_latest.md`
  - current template UUID mapping:
    - `top3` -> `qpfepwdjvsuxv`
    - `breakout` -> `1h9uyopu3rarv`
    - `weekly` -> `m6nbvjbbyarrj`
• brand-first render path added for social publishing:
  - `scripts/growth/render_social_cards.py` fills local SVG templates from live DB
  - output stored in `assets/social/out/*.svg` with landing-consistent visual tokens
  - this path is now preferred for daily posting to avoid template-style drift
• short-video growth path added:
  - `scripts/growth/render_shitpost_short.py` renders a 5-second branded glitch clip from live top movers
  - output file: `assets/social/out/shitpost-live-5s.mp4`
  - source contract: `public.top_movers_latest` (real deltas per current bucket window)
• positioning message pack: `docs/positioning_messages_latest.md` (site/bot/social interception copy)
• C1 site implementation contract:
  - landing hero carries “action over dashboard” framing
  - landing FAQ includes explicit “Why Telegram-first?” answer
  - `/telegram-bot` SEO page copy is synchronized with the 3-message C1 frame

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
