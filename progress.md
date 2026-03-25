# Polymarket Pulse — Implementation Progress

This document tracks the current state of the project.

---

# Return Loop Guidance Pass (2026-03-25)

Improved the returning-user experience inside `Pulse` so `/watchlist` and `/inbox` behave more like guided “what to check first” screens and less like raw dumps.

Files updated:

• `bot/main.py`

What changed:

• added a shared `active_followup_text(...)` helper for non-empty `watchlist` and `inbox` states
• non-empty `watchlist` now tells the user how to read the screen:
  - the first row is the strongest current live delta
  - quiet markets in the same window are normal
  - closed markets should push the user toward `Review list`
• non-empty `inbox` now explains:
  - the first alert is the strongest thresholded move right now
  - when to raise threshold
  - when to review the list instead of forcing more alerts
• watchlist fallback windows (`30m`, `1h`) now explain that:
  - the list may be slow, not broken
  - broader-window rows are still useful
  - the right next step is to wait or review, not assume failure

Practical effect:

• returning users now get more help with interpretation, not just more buttons
• this should reduce the “quiet = broken” failure mode after the first successful add
• it supports retention inside the current weekly path:
  - `tg_start -> watchlist_add -> watchlist/inbox reuse`

---

# Post-Add First-Value Reinforcement (2026-03-25)

Improved the `Pulse` watchlist add/replace path so the user gets a more honest and actionable next step immediately after adding a market.

Files updated:

• `bot/main.py`

What changed:

• added a shared `market_live_state_summary(...)` helper for post-add messaging
• successful add/replace responses now distinguish between:
  - `ready`
  - `partial`
  - `no_quotes`
  - `closed`
• for `ready` markets the user is pushed straight toward `Watchlist`
• for `ready` markets the add/replace confirmation now also shows a compact live preview:
  - current mid
  - previous mid
  - delta
  - bucket window
• for quiet states the user now gets:
  - an honest status line
  - a concrete next-step line
  - recovery/review markup instead of the generic “added” keyboard
• replaced markets now also return the same state-aware guidance instead of a generic “check Watchlist or Inbox” follow-up

Practical effect:

• the first add is now closer to a real value moment:
  - if the market is already live, the user knows to check `Watchlist` immediately
  - and gets a first live delta preview directly in the confirmation
  - if the market is weak, the user is told to swap/review it instead of waiting in confusion
• this directly supports the current weekly KPI around `tg_start -> watchlist_add -> first useful signal`

---

# Digest Usefulness Pass 2 (2026-03-25)

Improved the email digest so it behaves less like a raw alert dump and more like a backup retention surface that helps the user decide whether to return to `Pulse` right now.

Files updated:

• `api/digest_job.py`

What changed:

• the digest email now includes a dedicated `Watchlist coverage` block above the alert list
• each email now explains:
  - how many tracked markets have live last+prev coverage right now
  - how many tracked markets actually crossed the user threshold in the digest window
• the digest now gives a context-aware next step:
  - replace closed markets first
  - swap in a stronger live market if coverage is zero
  - accept a quiet window as normal and review threshold/list in Telegram if needed
  - or treat the email as a healthy backup pass when coverage is already good

Practical effect:

• the daily digest now better answers both:
  - “what moved?”
  - “what should I do next in Pulse?”
• email remains a backup channel, but the return path into the live Telegram loop is now much clearer

---

# Active 14-Day Plan

Current execution plan is tracked in:

`docs/plan_14day_seo_bot_growth_2026-03-09.md`

Current operating board for weekly prioritization is tracked in:

`docs/weekly_operating_board_2026-03-17.md`

Scope: SEO + Bot UX + Multi-channel growth with Telegram activation as the primary KPI.

---

# New-User Start Funnel Tightening (2026-03-25)

Simplified the new-user `/start` path in `Pulse` so the first useful action is more obvious and the bot spends less of the first screen budget on command-reference text.

Files updated:

• `bot/main.py`

What changed:

• the initial `/start` message for brand-new users is now lighter:
  - keeps the core product framing
  - removes the old longer quick-start checklist from the top block
• new users now get a separate action-first message:
  - add one live market
  - open Watchlist
  - let Inbox stay quiet until the move matters
• the live-candidate picker prompt is now more concrete:
  - “Three live candidates right now”
  - instead of a more generic add prompt

Practical effect:

• `/start` for a new user now points harder at the first add instead of making the user read the bot before using it
• this is aimed directly at the current funnel gap between measured `tg_start` and `watchlist_add`

---

# Funnel Attribution Repair Pass (2026-03-25)

Repaired the weekly measurement layer so the core `site -> tg_start -> watchlist_add` funnel reads more honestly and so future watchlist adds can be attributed back to the last Telegram start context.

Files updated:

• `bot/main.py`
• `scripts/growth/weekly_kpi_report.py`
• `docs/growth_kpi_latest.md`

What changed:

• `watchlist_add` events now inherit the latest `/start` context for the same user:
  - `start_payload`
  - `start_entrypoint`
  - `site_attributed_start`
• weekly KPI report no longer presents misleading `tg_start / tg_click` math when direct Telegram opens or `/upgrade` starts are mixed into the same window
• weekly report now splits:
  - `tg_start (all entrypoints)`
  - `tg_start from site payloads`
  - `watchlist_add users from site-attributed starts`

Practical effect:

• the growth loop is now closer to the actual weekly KPI:
  - `Search / site -> tg_click -> /start -> watchlist_add`
• the current report shows the real bottleneck more clearly:
  - `tg_click` is still low
  - site-attributed starts exist
  - but `watchlist_add` is still not materializing in measured events yet

---

# Brand Query and Digest Retention Pass (2026-03-23)

Improved two safe supporting layers for the current weekly focus:

• branded search/entity recognition around `Polymarket Pulse + Telegram bot`  
• daily digest usefulness as a return-to-Pulse retention surface

Files updated:

• `api/web/index.en.html`
• `api/main.py`
• `api/digest_job.py`

What changed:

• homepage metadata now ties the brand more explicitly to the Telegram-bot use case:
  - title and description mention `Polymarket Pulse Telegram Bot`
  - Organization / WebSite JSON-LD now describe the product as a Telegram-first signal layer
  - homepage ItemList now names the key path as `Polymarket Pulse Telegram Bot`
• `/telegram-bot` EN page now carries the brand phrase more explicitly in:
  - title
  - description
  - h1 / intro
  - FAQ
  - `WebPage.about`
• daily digest now behaves more like a useful backup loop:
  - subject can use the strongest market label
  - CTA now says `Resume in Telegram`
  - kicker calls out the strongest move by market name, not only by raw delta

Practical effect:

• Google now gets a clearer entity hint that `Polymarket Pulse` is specifically a Telegram bot / Telegram-first signal product for Polymarket
• email digest is better positioned to bring a confirmed subscriber back into the live Pulse loop instead of acting like a generic recap mail

---

# Homepage Brand Layer Rebalance (2026-03-23)

Softened the homepage brand metadata back to the broader product layer after the first brand-query pass over-narrowed the whole site toward `Telegram bot` wording.

Files updated:

• `api/web/index.en.html`

What changed:

• homepage title / description are back to the wider brand surface:
  - `Polymarket Pulse`
  - signal terminal / live movers / watchlists / Telegram alerts
• removed the overly narrow homepage `alternateName` that made the whole brand read like only a Telegram-bot landing
• kept the sharper `Telegram bot` pairing on the dedicated `/telegram-bot` page, where that search intent belongs

Practical effect:

• homepage now represents the broader product again
• `/telegram-bot` still carries the stronger search-intent targeting for bot-specific discovery

---

# Pulse Watchlist Review Flow Pass (2026-03-23)

Improved the `Pulse` watchlist review surface so it works consistently from both slash commands and inline buttons, and so weak watchlist coverage gets an obvious next action instead of a passive status list.

Files updated:

• `bot/main.py`

What changed:

• added a real callback handler for `menu:watchlist_list`, so existing `Review list` buttons no longer dead-end
• extracted a shared `send_watchlist_list_view(...)` surface used by both:
  - `/watchlist_list`
  - inline `Review list`
• `watchlist_list` now detects when coverage is weak:
  - too many `no_quotes`
  - `closed` markets
  - zero `ready` markets with only `partial` coverage
• in those cases the screen now:
  - tells the user the best next step
  - merges live recovery candidates directly into the inline actions
• if coverage is merely thin, the screen nudges the user to add one more live market instead of stopping at diagnostics

Practical effect:

• the watchlist review path is now a real retention surface instead of a static debug-ish list
• users can move from “my watchlist coverage is weak” to “here is the next live market to swap in” in one screen

---

# Homepage Hero Right Panel Revert (2026-03-23)

Reverted the right panel of the EN homepage hero back to the simpler conversion panel contract after the workflow-heavy version drifted away from the intended landing behavior.

Files updated:

• `api/web/index.en.html`

What changed:

• restored the right panel to the tighter structure:
  - `FASTEST WAY TO GET VALUE`
  - `CATCH THE MOVE BEFORE EVERYONE ELSE.`
  - short Telegram-first subline
  - three stacked dark feature rows
  - primary green Telegram CTA
  - secondary outlined `How it works?` button
  - `WAITLIST EMAIL` kicker
  - existing waitlist form
  - confirmation note below the form
• removed from the right panel:
  - workflow/step blocks
  - “You stop scanning...” style callouts
  - explanation box about the left panel
  - the `TELEGRAM-FIRST WORKFLOW` kicker

Practical effect:

• the hero-right decision surface is back to a simpler landing-first conversion contract
• the left movers panel, the metrics row, and the rest of the page remain untouched

---

# Weekly Focus Implementation: Pulse, Search, Retention, Core Hardening (2026-03-23)

Implemented the next weekly slice around the agreed focus:

• `Pulse` stays the main product surface  
• the site stays Telegram-first  
• email remains a backup/retention channel  
• `Trader` stays frozen outside of its existing alpha contour  
• the `public` analytical core is now hardened through read-only health/reporting rather than runtime rewiring  

Files updated:

• `api/web/index.en.html`  
• `api/main.py`  
• `bot/main.py`  
• `api/digest_job.py`  
• `db/migrations/012_analytics_core_health.sql`  
• `scripts/growth/weekly_kpi_report.py`  
• `scripts/data_core_health_report.py`  
• `docs/data_core_contract_2026-03-23.md`  
• `docs/data_core_health_latest.md`  
• `docs/growth_kpi_latest.md`  

What changed:

• homepage hero now uses a cleaner proof line:
  - live DB preview on the left
  - Telegram bot live now
• EN SEO pages now keep the CTA hierarchy stricter:
  - Telegram primary
  - bot-flow/proof secondary
  - email backup tertiary
• the main Pulse bot no longer pushes Trader from core analytics views like `/movers`, fallback watchlist windows, `/start`, `/help`, `/limits`, or free-plan followups
• `/watchlist_list` now shows compact coverage counts before the per-market rows:
  - `ready`
  - `partial`
  - `no_quotes`
  - `closed`
• daily digest now reads more like a product surface:
  - joins market question labels
  - summarizes alert breadth
  - highlights the strongest move in the backup pass
• added `public.analytics_core_health_latest` as the new read-only health view for the canonical Layer II core
• added a dedicated data-core contract doc and a generated data-core health report
• weekly KPI reporting now includes a compact core-health section alongside the growth funnel

Practical effect:

• acquisition pages now push one clearer path into Telegram without treating email as an equal first-screen choice
• Pulse core screens stay inside the analytics loop instead of leaking execution-alpha prompts into the main retention surfaces
• weekly review now has two live readouts:
  - funnel health (`docs/growth_kpi_latest.md`)
  - analytical core health (`docs/data_core_health_latest.md`)
• the data-layer audit is now converted into a safe hardening layer rather than a reason to rewrite the live `bot.*` runtime

---

# Public Data Layer Audit Snapshot (2026-03-20)

Captured a dedicated read-only audit of the live Supabase `public` schema so the Layer II analytical core has a current health snapshot alongside the ongoing growth work.

Files updated:

• `docs/data_layer_public_schema_audit_2026-03-20.md`

What was documented:

• the current live-state of `market_snapshots`, `market_universe`, and the movers views
• the distinction between the healthy analytical core and the weaker transitional/legacy shell in `public`
• specific drift points around:
  - `watchlist` vs `watchlist_markets`
  - empty alert surfaces
  - semantically weak metadata such as `markets.category`

Practical effect:

• the project now has a dedicated written snapshot of how the Layer II data substrate actually behaves in production
• this gives us a clearer baseline before any future cleanup of public-schema contracts or alert/watchlist derivations

---

# Landing -> Telegram Conversion Pass 2 (2026-03-20)

Tightened the EN homepage around one clearer activation story: open Telegram, add one market, and get to first value without treating email like an equal primary action.

Files updated:

• `api/web/index.en.html`

What changed:

• hero subcopy now explains the exact friction more directly:
  - dashboard/tab babysitting
  - noisy feeds
  - fast move visibility in Telegram
• the right-side CTA panel now frames activation as a concrete 3-step path:
  - open the bot
  - add one market
  - get the move
• added a compact trust strip under the main Telegram CTA:
  - `No signup required`
  - `1 tap to open`
  - `Email optional backup`
• the “why this loop feels better” bullets now speak more directly to real pains:
  - manual dashboard confirmation
  - one-loop watchlist + movers
  - low-trust alert spam
• the email form remains on the page, but now explicitly explains its role as a secondary backup channel for digest and updates

Practical effect:

• the homepage now makes the Telegram path feel lower-friction and more obvious
• email is still available, but no longer reads like a competing primary choice
• the top-of-funnel narrative aligns more tightly with the weekly KPI:
  - `tg_click -> /start -> watchlist_add`

---

# EN Intent Pages CTA Alignment (2026-03-20)

Aligned the main EN acquisition pages with the homepage CTA hierarchy so `/telegram-bot` and `/signals` no longer feel like slightly different funnels.

Files updated:

• `api/main.py`

What changed:

• the shared SEO-page CTA block now includes a compact trust strip under the Telegram button:
  - `No signup required`
  - `1 tap to open`
  - `Email backup only`
• shared CTA copy now explicitly frames email as a secondary backup channel for digest and launch updates
• this alignment applies to the dynamic EN intent pages generated through `render_seo_page(...)`, including:
  - `/analytics`
  - `/signals`
  - `/telegram-bot`
  - `/top-movers`
  - `/watchlist-alerts`
  - `/dashboard`

Practical effect:

• the main search-entry pages now reinforce the same hierarchy as the homepage:
  - Telegram primary
  - guide/support secondary
  - email backup tertiary
• users arriving from search should now hit less copy drift between homepage and deeper intent pages

---

# Landing -> Telegram Conversion Pass 3 (2026-03-20)

Ran a third homepage conversion pass after the fresh KPI report confirmed that the weakest point in the funnel is still `page_view -> tg_click`.

Files updated:

• `api/web/index.en.html`

What changed:

• the hero CTA panel now uses a tighter decision pattern:
  - stronger primary CTA copy (`Open Telegram Bot in 1 Tap`)
  - smaller, lower-contrast guide link
  - backup email wrapped in its own optional shell instead of reading like a competing primary form
• added a compact proof note above the CTA path clarifying that the movers panel is powered by the live DB preview, not static screenshots
• CTA copy now speaks more directly to the conversion moment:
  - decide whether the move matters
  - avoid losing attention to more dashboard tabs

Practical effect:

• the first-screen decision panel now has less visual competition around the Telegram click
• guide/help remains available, but no longer competes with the primary action like a second button-level CTA
• email still exists for retention, but reads more clearly as a tertiary backup channel

---

# Pulse Retention Pass: Watchlist and Inbox Next Steps (2026-03-20)

Improved the main analytics bot screens after first activation so `/watchlist`, `/inbox`, and `/watchlist_list` lead users toward the next useful action instead of acting like static dumps.

Files updated:

• `bot/main.py`

What changed:

• `/watchlist` now ends with a clearer next-step hint when live deltas exist:
  - open Inbox
  - review list health
  - add one more live market if coverage feels thin
• `/inbox` now ends with a clearer next-step hint when alerts exist:
  - compare against Watchlist
  - review quiet markets
  - adjust threshold if needed
• quiet-state versions of `/watchlist` and `/inbox` now use Pulse-native action keyboards instead of routing the user toward Trader surfaces
• `/watchlist_list` now includes a plain-English state legend for:
  - `ready`
  - `partial`
  - `no_quotes`
  - `closed`

Practical effect:

• the main retention screens now behave more like product surfaces and less like raw output
• users get a clearer answer to “what should I do next?” after opening watchlist or inbox
• the main analytics bot is now cleaner about staying inside the Pulse loop instead of mixing in unnecessary execution cues

---

# Email Backup + Digest Retention Pass (2026-03-19)

Upgraded the email layer from a bare confirmation transport into a clearer retention surface that matches the current Pulse-first product story.

Files updated:

• `api/main.py`
• `api/digest_job.py`
• `docs/social_pipeline.md`

What changed:

• confirmation emails now explain the real contract:
  - Telegram is the live signal loop
  - email is the backup channel for digest and updates
• confirmation emails now use a branded dark/green shell instead of a raw HTML link
• confirm-success pages now render as branded status screens instead of plain `<h3>` responses
• invalid-confirm and unsubscribe states now also render as branded status screens with a clear next action back into Pulse
• welcome emails now reinforce the same product hierarchy:
  - Telegram first
  - email backup second
• digest emails now render inside a branded shell and include:
  - summary framing
  - clearer alert list
  - direct CTA back into the Telegram bot
  - working unsubscribe link via `confirm_token`
• `docs/social_pipeline.md` funnel notes were updated so the weekly growth documentation no longer points only at the older waitlist-confirm path
• production smoke caught and fixed a real route-order bug where `/{slug}` intercepted `/confirm` and `/unsubscribe`
• after moving the SEO catch-all route below the explicit email routes, the full production flow passed with a temporary test subscriber:
  - `/api/waitlist`
  - `/confirm`
  - `/unsubscribe`
• production DB smoke confirmed:
  - `confirmed_at` populated
  - `unsubscribed_at` populated
  - `waitlist_submit`, `confirm_success`, and `unsubscribe_success` events logged with the expected placement/UTM context

Practical effect:

• email now behaves more like a real backup/retention layer and less like a generic form receipt
• the product story stays coherent across landing, Telegram, and email
• digest unsubscribe links now point at the correct token contract
• the public email confirmation path is now actually reachable in production, not shadowed by the generic SEO route

---

# TG Activation First: Pulse-First Site + Real watchlist_add Attribution (2026-03-19)

Shifted the weekly execution layer away from Trader expansion and tightened the real Pulse funnel around the agreed KPI: `tg_click -> /start -> watchlist_add`.

Files updated:

• `api/web/index.en.html`
• `api/main.py`
• `bot/main.py`
• `scripts/growth/weekly_kpi_report.py`
• `docs/growth_kpi_latest.md`

What changed:

• homepage hero copy now speaks more directly to dashboard overload and delayed discovery pain
• homepage CTA panel now frames the product as a Telegram-first relief valve for:
  - too many tabs
  - stale discovery
  - noisy alerts
• homepage Trader Alpha strip was removed from the main acquisition path
• homepage intent/search hub no longer links to Trader Alpha during this weekly focus window
• EN SEO pages now keep related links and comparison blocks focused on Pulse, not Pulse+Trader
• `/telegram-bot` style SEO surfaces no longer push Trader as a secondary CTA for this week’s funnel
• the Pulse bot now logs real `watchlist_add` events into `app.site_events`
• watchlist-add attribution now includes:
  - app user id
  - Telegram identity
  - market id
  - outcome
  - live state
  - previous watchlist count
  - `first_watchlist_add`
  - placement source (`watchlist_add_command`, `watchlist_picker`, `watchlist_replace_picker`)
• weekly KPI reporting now shows:
  - `watchlist_add events`
  - `watchlist_add users`
  - `first_watchlist_add users`
  - cross-check against the older `bot.watchlist` proxy

Practical effect:

• the public acquisition layer now stays centered on one main job: get the user into the Pulse Telegram bot
• weekly reporting no longer depends only on indirect DB proxies for first activation
• we can now inspect the real drop-off from:
  - page_view
  - tg_click
  - tg_start
  - watchlist_add

---

# Pulse Watchlist Add Activation Unification (2026-03-17)

Closed an activation gap between the slash-command path and the picker path for watchlist onboarding.

Files updated:

• `bot/main.py`

What changed:

• `/watchlist_add <market_id|slug>` now reuses the same smart add contract as the picker flow
• post-add replies now stay consistent between:
  - manual slash add
  - picker add
  - replacement add
• when the user hits the Free/Pro watchlist limit through `/watchlist_add`, the bot now shows the same recovery/replacement surface instead of returning a dead-end limit message
• add/replacement helpers now return structured outcomes (`added`, `replaced`, `exists`, `limit`, `missing`) so reply UX can stay coherent across handlers

Practical effect:

• first-value onboarding no longer depends on whether the user added a market via button flow or typed the market manually
• users who add via slash command get the same momentum-preserving recovery path when the watchlist is already full
• if a newly added market is still quiet (`partial`, `no quotes`, or `closed`), the same reply can now include live replacement candidates instead of forcing the user to discover the next step manually

---

# Pulse Plan + Upgrade Conversion Pass (2026-03-18)

Tightened the subscription-facing UX inside the Pulse bot so `/plan` and `/upgrade` help the user act, not just read limits.

Files updated:

• `bot/main.py`

What changed:

• `/plan` now uses a dedicated message layer instead of a generic status dump
• FREE users now see:
  - current threshold
  - watchlist slots left
  - alerts used today
  - what PRO unlocks
• PRO users now see:
  - current threshold
  - free watchlist capacity
  - whether closed markets are parked in watchlist
  - the most useful next step
• `/upgrade` no longer sends a payment flow to users who already have PRO
• free upgrade copy now points to the clean EN-only Stripe landing path (`/telegram-bot#pro`)
• plan/upgrade inline actions were simplified around the core Pulse loop:
  - add market
  - watchlist
  - inbox / threshold
  - upgrade only where it is actually relevant

Practical effect:

• plan state now reads like a product status view instead of a debug summary
• upgrade flow stops feeling broken for existing PRO users
• the subscription surface stays aligned with the current EN-only public site

---

# Homepage Search Hub + GSC Weekly Runbook (2026-03-18)

Strengthened the public English homepage as a crawl/conversion hub and added a repeatable Search Console operating checklist.

Files updated:

• `api/web/index.en.html`
• `docs/gsc_weekly_checklist_2026-03-18.md`

What changed:

• homepage intent links were expanded into a richer search-path block
• the block now links directly to:
  - analytics
  - signals
  - telegram-bot
  - top-movers
  - watchlist-alerts
  - dashboard
  - how-it-works
  - commands
  - trader-bot
• each link now explains the intent it serves instead of appearing as a bare label
• homepage now emits an `ItemList` JSON-LD block for the main search-entry pages
• added a weekly GSC checklist so index-state review is now operationalized rather than handled ad hoc

Practical effect:

• the homepage is now a stronger internal-linking surface for the EN acquisition layer
• crawl paths into the key Telegram-activation pages are clearer
• GSC follow-up now has a single documented routine

---

# JIT Social Execution Queue (2026-03-18)

Turned the social layer into a daily operator queue instead of a loose set of drafts and video files.

Files updated:

• `scripts/growth/build_social_queue.py`
• `docs/social_pipeline.md`
• `docs/social_queue_latest.md`

What changed:

• added a queue builder that reads fresh/liquid movers from `public.top_movers_latest`
• the queue maps live data into the current pain-first posting order:
  - manual workflow pain
  - threads mirror
  - alert fatigue
  - dashboard overload
• each queue slot now includes the correct current video asset path
• if no mover passes the freshness/liquidity gate, the system now explicitly returns `skip posting`

Practical effect:

• daily social ops now has one file that answers “what do we post right now?”
• the operator no longer has to manually stitch together live data, text drafts, and video assets
• stale windows correctly produce no-post guidance instead of dead content

---

# Daily Social Operator Routine (2026-03-18)

Wrapped the just-in-time social system in a single operator command so daily publishing stops depending on memory or ad hoc shell snippets.

Files updated:

• `scripts/growth/run_social_cycle.sh`
• `docs/social_pipeline.md`
• `docs/social_daily_operator_routine_2026-03-18.md`

What changed:

• added a one-command daily operator flow:
  - loads `PG_CONN` from `bot/.env` if needed
  - rebuilds the live posting queue
  - rebuilds the EN draft pack
  - prints a single `POST` / `SKIP` decision
• documented the routine as a strict manual publishing loop
• clarified that every posting block should re-run the cycle instead of relying on older drafts

Practical effect:

• daily social ops is now executable by habit instead of by remembering flags
• the team gets one answer before posting anything: publish now or wait
• this makes the social layer behave more like the product itself: no stale signals, no forced output

---

# Telegram Deep-Link Start Attribution (2026-03-18)

Added bot-side `/start` attribution so social and deep-link traffic can now be measured after the user actually enters Telegram.

Files updated:

• `bot/main.py`
• `scripts/growth/weekly_kpi_report.py`

What changed:

• `/start` now captures Telegram deep-link payloads via `context.args`
• the bot writes a `tg_start` event into `app.site_events`
• stored details now include:
  - `start_payload`
  - `entrypoint` (`telegram_direct` vs `telegram_deep_link`)
  - app user id
  - telegram id / chat id
  - plan / watchlist context at start time
• weekly KPI reporting now includes:
  - `tg_start`
  - `tg_start / tg_click`
  - `tg_start by Start Payload`

Practical effect:

• we can now see whether a social pain theme actually drives people from deep-link click into a real Telegram `/start`
• today’s X post can now be measured beyond raw `tg_click`

---

# Pulse Quiet-State Guidance + Trader Readiness Surface (2026-03-18)

Moved both bots one step closer to “explain what to do next” instead of only showing state.

Files updated:

• `bot/main.py`
• `trader_bot/main.py`

What changed:

• `Pulse` quiet states in `/watchlist` and `/inbox` now add a direct next-step line based on context:
  - closed markets in watchlist
  - no quotes in both windows yet
  - threshold filtering out signals
  - empty watchlist
• `Trader` now has a dedicated `/ready` command
• `/ready` combines:
  - wallet state
  - signer state
  - risk state
  - latest worker status when present
• `Trader` reply keyboard now includes a human-labeled readiness entry

Practical effect:

• `Pulse` no longer leaves quiet users with only diagnostics; it now tells them what to do next
• `Trader` now has one obvious command for “am I actually ready to use this thing?”

---

# Watchlist Status Review + Trader Ready Hand-Off (2026-03-18)

Improved the “what do I do now?” layer after onboarding by making watchlist review and trader readiness easier to interpret.

Files updated:

• `bot/main.py`
• `trader_bot/main.py`

What changed:

• `/watchlist_list` now shows per-market status labels:
  - `ready`
  - `partial`
  - `no_quotes`
  - `closed`
• watchlist review now explicitly points users toward:
  - `/watchlist`
  - `/watchlist_remove <market_id|slug>`
• `Trader` empty positions copy now points users to `/ready`
• `Trader` order-save confirmation now also points users to `/ready` as the one-screen readiness summary

Practical effect:

• Pulse users can now audit whether their watchlist is actually alive instead of seeing a raw list only
• Trader users get a clearer next action after creating a draft or finding no positions

---

# Trader `/ready` Tap UX Fix (2026-03-18)

Fixed the last small but important Telegram UX issue around the new readiness command.

Files updated:

• `trader_bot/main.py`

What changed:

• removed `<code>` wrapping around `/ready` in user-facing guidance
• `/ready` now appears as a normal Telegram command in:
  - empty positions state
  - order draft saved confirmation

Practical effect:

• tapping `/ready` now behaves like a command hint instead of a copy-only code fragment

---

# Manual Tabs Pain Video Render + X Credits Reality (2026-03-17)

Built the first pain-first branded short for manual posting and corrected the X API blocker in project memory.

Artifacts added:

• `scripts/growth/render_manual_tabs_short.py`
• `assets/social/out/manual-tabs-pain-5s.mp4`
• `assets/social/out/manual-tabs-preview-01.png`
• `assets/social/out/manual-tabs-preview-02.png`
• `assets/social/out/manual-tabs-preview-03.png`

What the new render does:

• uses real `public.top_movers_latest` data from Postgres
• renders a 5-second vertical short around the `Manual Tabs Pain` thesis:
  - `12 tabs open`
  - `move already happened`
  - real mover question + delta
  - `workflow too manual`
  - Telegram CTA
• stays inside the current dark terminal + neon green brand system

X posting state was also clarified:

• OAuth1 write access now works with the latest app tokens
• automated posting is blocked by `402 CreditsDepleted`, not by missing write permissions
• manual posting remains the correct operating mode until X credits are added

---

# Alert Fatigue + Dashboard Overload Video Pack (2026-03-17)

Extended the first short-form social pack beyond the manual-tabs clip.

Artifacts added:

• `scripts/growth/render_pain_short.py`
• `assets/social/out/alert-fatigue-5s.mp4`
• `assets/social/out/dashboard-overload-5s.mp4`
• `assets/social/out/alert-fatigue-preview-01.png`
• `assets/social/out/alert-fatigue-preview-02.png`
• `assets/social/out/alert-fatigue-preview-03.png`
• `assets/social/out/dashboard-overload-preview-01.png`
• `assets/social/out/dashboard-overload-preview-02.png`
• `assets/social/out/dashboard-overload-preview-03.png`

What these cover:

• Brief 2 — `Alert Fatigue`
• Brief 3 — `Dashboard Overload`

Render behavior:

• uses the same live DB source (`public.top_movers_latest`)
• keeps the brand-safe dark/green terminal system
• stays pain-first instead of hype-first
• gives us the first complete 3-clip manual posting batch:
  - manual tabs pain
  - alert fatigue
  - dashboard overload

---

# Just-In-Time Social Draft Gate (2026-03-17)

Tightened the social draft generator so we stop producing stale-but-pretty content.

Files updated:

• `scripts/growth/generate_social_drafts.py`
• `docs/social_pipeline.md`
• refreshed `docs/social_drafts_latest.md`

What changed:

• social drafts now filter on latest-bucket freshness (`--max-age-minutes`, default `30`)
• social drafts now filter on live liquidity (`--min-liquidity`, default `5000`)
• mover and breakout posts now include liquidity context (`L 34.7K`, etc.)
• current operating rule is now explicit: generate right before posting, not hours earlier

Practical effect:

• the latest draft pack is now built from the current 15m live window
• weak or stale markets are dropped before they reach the posting queue
• social ops stays aligned with the “signal > noise” product principle

---

# GSC Indexing Hygiene Pass (2026-03-16)

Addressed the first structural SEO inconsistency that was hurting indexing clarity in Google Search Console.

What was wrong before:

• sitemap listed localized `?lang=en|ru` URLs
• many page templates declared canonical URLs without the `?lang=` parameter
• Google therefore saw part of the site as "localized URL in sitemap" vs "different canonical target"
• legal pages (`/privacy`, `/terms`) were also spending crawl attention despite not being acquisition pages

What was changed:

• `api/main.py` sitemap now emits a single consistent set of localized URLs with `xhtml:link` hreflang alternates
• SEO page renderer now uses self-canonical localized URLs for query-param language variants
• static templates for:
  - landing
  - commands
  - how-it-works
  - trader-bot
  now self-canonicalize to their own `?lang=` URL and align OG metadata to the same URL
• `/privacy` and `/terms` were downgraded to `noindex,follow`
• legal pages were removed from sitemap so crawl budget stays focused on acquisition/intent pages

Expected outcome:

• fewer "canonical variant" signals in GSC
• clearer indexing contract for English/Russian content pages
• better crawl focus on homepage, intent pages, `/telegram-bot`, `/trader-bot`, `/commands`, and `/how-it-works`

Important note:

• GSC redirect examples for `http://` and `www.` are still normal and expected as long as they resolve to `https://polymarketpulse.app/`

---

# Ready-to-Post Social Batch (2026-03-16)

Converted the social sprint into a manual operator batch that can be published immediately.

Artifact added:

• `docs/social_posting_batch_2026-03-16.md`

What is inside:

• 5 ready-to-post X posts
• 3 Threads variants
• 1 X thread outline
• UTM-tagged links for each pain theme
• mapping to the first 3 short-form clips worth rendering

Operational reality:

• X write auth is valid now
• API posting is still blocked by `402 CreditsDepleted`
• manual posting is the correct mode until X credits are added

---

# Pain-First Social Sprint + X Access Check (2026-03-16)

Prepared the next growth layer as an operational social sprint instead of abstract marketing notes.

Artifacts added:

• `docs/social_sprint_pain_first_2026-03-16.md`
• `docs/social_video_briefs_2026-03-16.md`

What is in the sprint:

• 5 audience pain pillars
• 7-day posting cadence for X + Threads
• concrete post drafts in English
• strict brand-safe rules for visuals and CTA structure
• 3-5 second short-form video briefs mapped to the strongest posts

Important external blocker confirmed:

• X write auth was fixed after this pass
• current blocker is now API credits/quota, not app permissions
• direct OAuth1 write check now returns:
  - `402 CreditsDepleted`
  - account has no available credits for `POST /2/tweets`

---

# Remaining EN Intent Pages Copy Pass (2026-03-16)

Closed the same CTR/copy gap on the remaining English acquisition pages.

Pages tightened:

• `/dashboard`
• `/top-movers`
• `/watchlist-alerts`

What changed:

• stronger search-facing titles and descriptions
• H1/intro copy now leans into action, speed, and low-noise market tracking
• clearer feature bullets around adaptive windows, watchlist flow, and action-first Telegram UX
• added page-aware CTA support note for the dashboard-alternative page as well

Result:

• the EN intent layer now has a more consistent voice across all primary acquisition pages
• pages describe a single funnel more clearly: search -> Telegram -> watchlist -> signal

---

# EN Intent CTR Copy Polish (2026-03-16)

Applied a tighter conversion-oriented copy pass to the highest-intent English SEO pages.

Pages touched conceptually:

• `/analytics`
• `/signals`
• `/telegram-bot`

What changed:

• stronger H1/intro copy focused on action instead of passive dashboard browsing
• clearer value props around low-noise signals, thresholding, and Telegram-first execution
• more explicit secondary CTA wording on high-intent pages (`Keep Email as Backup`)
• added a short CTA support note under the button row to reduce hesitation before the Telegram click

Why this matters:

• better CTR from search pages into the bot
• clearer distinction between `Pulse` and generic dashboard products
• better alignment between SEO copy and the current product funnel (`search -> Telegram -> watchlist -> signal`)

---

# Intent Page Enrichment + GA4 Alignment (2026-03-16)

Strengthened the English intent-page layer after the EN-only SEO switch.

What changed:

• `api/main.py` SEO renderer now injects per-page FAQ blocks for:
  - analytics
  - dashboard
  - signals
  - telegram-bot
  - top-movers
  - watchlist-alerts
• the same FAQ content is now emitted as `FAQPage` structured data
• related-page linking is no longer generic; each intent page now points to a curated set of next-step pages
• dynamic SEO pages now send events into both tracking layers:
  - `gtag` / GA4
  - `app.site_events` via `/api/events`

Why this matters:

• richer intent pages give Google more useful page-specific content than a thin keyword shell
• curated internal links make the crawl graph and user path cleaner
• dual-tracking is now consistent between static pages and dynamically rendered SEO pages

---

# EN-Only Site SEO Mode (2026-03-16)

Shifted the public website into an English-first indexing mode to reduce duplicate-localization noise on a young domain.

What changed:

• public site routes now default to English instead of geo/accept-language auto-switching
• Russian site pages still exist as fallback when `?lang=ru` is explicitly used
• Russian site pages are now `noindex,follow`
• English pages are the only sitemap targets and the only indexable site layer
• canonical URLs for English pages are now clean paths without `?lang=en`
• internal site links were simplified to clean English URLs:
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
• EN/RU switchers were removed from the public site templates

Why this was done:

• concentrate crawl/indexing signals on one language layer
• reduce query-param duplicate pressure in GSC
• align the site with current growth reality:
  - X/Threads content is English-only
  - global acquisition is English-first
  - Telegram bots can remain bilingual independently of site SEO

Boundary:

• this changes site SEO strategy, not product localization strategy
• bots remain multilingual
• RU site content is not deleted yet; it is retained as a non-indexed fallback while the domain is still young

---

# Signer Session Layer V0 (2026-03-15)

Added the first signer/delegation bridge for the sibling `Trader` product.

New DB foundation:

• `db/migrations/010_trade_signer_sessions.sql`
• new table: `trade.signer_sessions`

What now works:

• `/signer` in `@PolymarketPulse_trader_bot` creates or reuses a signer session for the user's primary wallet
• bot returns:
  - wallet
  - signer session status
  - challenge text
  - direct verification URL
• new site route: `GET /trader-connect?token=...`
• new API endpoint: `POST /api/trader-signer/submit`
• opening the page moves signer session state from `new -> opened`
• submitting a signed payload stores it in DB and moves signer session state to `signed`

Smoke status:

• migration applied successfully in Supabase
• local smoke passed end-to-end:
  - signer page `GET /trader-connect` -> `200`
  - signer submit `POST /api/trader-signer/submit` -> `200`
  - DB state updated to `trade.signer_sessions.status='signed'`

Important boundary:

• this is still not live signer verification
• `trade.wallet_links.status` remains non-active
• `trade-worker` continues to reject real execution attempts while signer activation is not implemented

Product value of this step:

• gives us a real signer funnel to test with users
• makes the future delegated-signer phase concrete
• keeps the UX honest: signer payload can be captured now, but execution is still alpha-gated

---

# Manual Signer Activation + Pulse Start Funnel (2026-03-15)

Closed the next missing link on both active rails.

Trader side:

• added migration `db/migrations/011_trade_signer_activation.sql`
• added DB function `trade.activate_signer_session(...)`
• added operator script `scripts/ops/activate_signer_session.py`

What this activation contract now does:

• accepts only `trade.signer_sessions.status='signed'`
• moves signer session to `verified`
• stamps `verified_at`
• updates linked wallet to:
  - `trade.wallet_links.status='active'`
  - `trade.wallet_links.signer_kind='session'`
  - `trade.wallet_links.signer_ref=<operator value or session token>`
• writes `trade.activity_events.event_type='signer_activated'`

Smoke status:

• migration applied successfully in Supabase
• activation smoke passed:
  - signer session became `verified`
  - wallet link became `active`
  - `signer_ref` persisted correctly

Pulse side:

• `/start` now includes a dedicated one-tap activation block before the generic quick menu
• new onboarding CTA layer sends the user toward:
  - `Add first market`
  - `Top movers`
  - `Plan`
  - `Help`

Why this matters for the 14-day plan:

• Trader rail is no longer stuck at `payload stored but forever pending`
• Pulse rail now shortens `/start -> first useful action`, which is the unresolved B2 activation step in the current growth plan

Additional runtime follow-up from the same pass:

• added operator review helper: `scripts/ops/list_signer_sessions.py`
• operators can now inspect pending signer queue (`new/opened/signed`) without manual SQL
• `/start` now shows up to 3 live one-tap watchlist candidates when the user has an empty watchlist

Why this matters:

• Trader alpha review loop is now operational instead of ad-hoc
• Pulse reduces one more click between `/start` and the first watchlist market

Follow-up UX tightening:

• `Trader` now surfaces execution readiness more explicitly:
  - `/connect` shows whether the wallet is already `ready_for_dry_run`
  - `/risk` now includes an explicit next-step line instead of only raw wallet status
  - `/buy` / `/sell` draft confirmation now tells the user whether worker execution is currently signer-blocked or dry-run-ready
  - `/order` now renders user-facing worker states instead of raw machine hints:
    - `queued_for_worker`
    - `blocked` with concrete next action (`/signer`, `/pause off`, `/rules`, `/risk`)
    - `accepted_by_dry_run_worker` with alpha-only execution disclaimer
• `Pulse` post-add flow is now less dead-end:
  - after one-tap add from picker or `/watchlist_add`, bot shows next-step inline actions for `Watchlist`, `Inbox`, `Threshold`, and `Add one more`
  - watchlist add success now also explains the first-value state of the specific market:
    - live quotes exist in `last+prev`
    - partial quotes only
    - no quotes yet
    - already closed
  - `/start` empty-watchlist onboarding still renders up to 3 one-tap live candidates first
  - when `/watchlist` or `/inbox` are empty, the bot now proposes up to 2 one-tap live replacement candidates instead of dead-ending on text-only fallback
  - execution handoff from `Pulse` no longer routes through the website when triggered inside Telegram; it now deep-links directly into `@PolymarketPulse_trader_bot`
  - reply keyboard in `Pulse` now uses human-readable labels instead of raw slash commands, with internal text routing kept in bot handlers
  - recovery candidates can now act as true replacements when watchlist is already full:
    - bot removes the oldest/closed market first
    - then inserts the live candidate
    - user gets replacement confirmation instead of a limit error
  - `/plan` is now shorter and more action-oriented:
    - current usage first
    - then either remaining FREE slots or current PRO advantage
    - action buttons for add / threshold / upgrade / trade
  - `/upgrade` now reuses the same action-oriented button layer instead of ending as isolated payment copy
• `Trader` signer path is now easier to read without opening `/signer` every time:
  - `/connect` includes signer state summary (`not_started`, `opened`, `signed`, `verified`)
  - `/risk` includes the same signer-state summary next to wallet readiness
  - this makes the path `connect -> signer -> approval -> ready_for_dry_run` visible directly in the bot surface
  - `/start` now also shows current execution readiness when a primary wallet already exists, so returning alpha users immediately see whether they are blocked, pending, or ready
  - reply keyboard in `Trader` now uses human-readable labels instead of raw slash commands, with text taps routed to the existing command handlers

---

# Trader Bot V0 Runtime (2026-03-14)

Execution-lane rollout moved from pure waitlist/funnel state into a real sibling Telegram bot runtime.

New bot:

• `@PolymarketPulse_trader_bot`

New runtime surface added in repository:

• `trader_bot/main.py`
• `trader_bot/.env.example`
• `trader_bot/Procfile`
• `trader_bot/requirements.txt`
• `trader_bot/README.md`

What now works in the trader-bot alpha:

• `/start` and `/help` onboard the user into the execution lane
• `/connect <wallet>` stores a non-custodial wallet registration in `trade.wallet_links`
• `/markets` shows the current trade queue from live movers
• `/buy` and `/sell` create manual order drafts in `trade.orders`
• `/order` shows latest draft orders
• `/positions` reads `trade.positions_cache`
• `/follow <wallet>` stores follow-source intent in `trade.follow_sources` + `trade.follow_rules`
• `/rules`, `/risk`, `/pause`, `/agent` expose the rule/risk/agent control plane from `trade.*`
• trader-bot command/menu registration is live via Telegram Bot API

Smoke status:

• local syntax check passed for `trader_bot/main.py`
• DB smoke confirmed user/account provisioning through existing `bot.resolve_or_create_user_from_telegram(...)` + `trade.ensure_account(...)`
• live startup smoke passed: bot successfully called `getMe`, `setMyCommands`, `deleteWebhook`, and entered polling
• Railway production deploy succeeded for service `trader-bot`
• production logs confirmed startup sequence for `@PolymarketPulse_trader_bot` and active polling loop in Railway

Related rollout completed in parallel:

• `site` service was redeployed successfully with current `/trader-bot` handoff page and direct CTA into `@PolymarketPulse_trader_bot`

---

# Trade Worker V0 Dry-Run Layer (2026-03-14)

Added the first execution state-machine worker in `trade_worker/`.

New runtime surface:

• `trade_worker/main.py`
• `trade_worker/requirements.txt`
• `trade_worker/Procfile`
• `trade_worker/.env.example`
• `trade_worker/README.md`

Current behavior:

• polls `trade.orders` where `status='pending'`
• validates wallet/signer/risk prerequisites from `trade.wallet_links`, `trade.agent_rules`, and `trade.risk_state`
• rejects orders with explicit machine reasons when execution prerequisites are missing:
  - `missing_wallet`
  - `requires_signer:*`
  - `paused`
  - `kill_switch`
  - `max_order_exceeded`
  - `daily_trade_cap`
  - `daily_loss_cap`
• in `dry_run` mode, promotes valid drafts to `status='submitted'` with synthetic `external_order_id`
• logs worker actions into `trade.activity_events`
• bumps `trade.risk_state` counters on dry-run submission

Validation:

• local smoke created a real pending order, worker processed it, and DB state moved:
  - `pending -> submitted`
  - `trade.activity_events.event_type = order_submitted_dry_run`
• separate Railway production service created: `trade-worker`
• env configured in production with `EXECUTION_MODE=dry_run`

Follow-up UX pass shipped after the first runtime:

• `trader_bot` now exposes clearer execution-readiness context:
  - `/connect` without args shows the current primary wallet + signer status
  - `/connect` success copy now explains the `pending signer` blocker explicitly
  - `/order` now surfaces the latest worker outcome for each draft (`order_submitted_dry_run` / `order_rejected`)
  - `/risk` now includes wallet/signer readiness in the same view

Parallel Pulse traffic/positioning pass:

• `api/main.py` SEO renderer for `/telegram-bot` now includes a stronger comparison block:
  - dashboards vs Pulse
  - copy-trading vs Pulse + Trader
  - signal-first stack positioning

Boundary that remains explicit:

• this is still execution alpha scaffolding
• order drafts are stored, not routed to Polymarket yet
• custody, delegated signer, and execution worker remain next-phase work

---

# Execution Product Foundation (2026-03-13)

Started the competitive response layer against Telegram-native execution products such as `Polycule`.

Decision now implemented in codebase:

• `Polymarket Pulse` remains the signal-first product (`discover + decide`)  
• execution is introduced as a separate sibling surface (`Trader Alpha`) instead of being merged into the existing Pulse bot  
• current rollout is foundation-first, not full execution release

What was added in this pass:

• new DB migration: `db/migrations/009_trade_execution_foundation.sql`
• new `trade` schema foundation:
  - `trade.accounts`
  - `trade.wallet_links`
  - `trade.positions_cache`
  - `trade.orders`
  - `trade.executions`
  - `trade.follow_sources`
  - `trade.follow_rules`
  - `trade.agent_rules`
  - `trade.agent_decisions`
  - `trade.risk_state`
  - `trade.activity_events`
  - `trade.alpha_waitlist`
• new site/API surfaces:
  - `GET /trader-bot`
  - `POST /api/trader-alpha`
• homepage now contains a secondary execution-lane strip linking into Trader Alpha while keeping Pulse as the primary CTA
• current SEO renderer cross-links into Trader Alpha from the Telegram bot acquisition page
• Pulse bot now exposes execution handoff primitives:
  - new `/trade` command
  - market-level execution CTA from `/movers`, `/watchlist`, `/inbox`
  - limit/plan UX now points power users to execution alpha where relevant

Current product state after this pass:

• execution bot is still alpha / waitlist state
• no live trading / wallet execution shipped yet
• no custody layer shipped
• no autonomous trading beyond schema and UX contract foundation

This is intentional: we now have a real acquisition + data foundation for the sibling execution product without collapsing the Pulse brand into a generic trading bot.

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

# Scope Analysis Snapshot (2026-03-11)

Requested scope pass across DB + bot + landing and compared against code-level contracts.

Runtime evidence sources:

`db/migrations/*.sql` + `bot/main.py` + `api/main.py` + `api/web/index.*.html` + live DB read snapshot via local `PG_CONN`.

Live DB snapshot (captured 2026-03-11 08:38 UTC):

• ingest freshness: latest `market_snapshots.ts_bucket=2026-03-11 08:30:00+00`, lag ~`540s`
• `public.market_snapshots` rows in last 24h: `32413`
• `public.markets`: `162741` total (`162037 active`, `704 closed`)
• `public.market_universe`: `200` rows (`199 auto`, `1 manual`, `0 closed`)
• universe category mix: `crypto=136`, `other=50`, `politics=13`, `macro=1`
• app/bot identities: `app.users=4`, `app.identities(telegram)=3`, `bot.profiles=3`
• watchlist state: `bot.watchlist=8` rows across `2` users
• monetization state: `app.subscriptions=0`, `app.payment_events=0`, `app.upgrade_intents(30d)=5` (`new`)
• funnel events (7d): `page_view=178`, `waitlist_submit=14`, `tg_click=8`, `waitlist_intent=2`, `checkout_intent=1`, `confirm_success=1`

Observed operational notes:

• bot poller conflict was present in logs on `2026-03-05` (`telegram.error.Conflict: terminated by other getUpdates request`)
• current local launchd status: bot service not loaded
• current bot inbox surface is valid but low-signal: `bot.alerts_inbox_latest=0` at snapshot time
• one free-profile currently has watchlist count above configured free cap (legacy state); add-flow limit checks still enforce cap for new additions

Reference estimate for new branded page (based on attached `polycule.pdf` style adapted to current dark/green brand contract):

• implementation + responsive + RU/EN copy + API template wiring: `8-12 hours`
• if copy finalization is provided upfront and no new backend endpoints are required: `6-8 hours`
• if animations/custom illustrations/extra telemetry A/B variants are added: `12-16 hours`

---

# Referral Program Discovery + Feasibility Pass (2026-03-12)

Completed research pass for "can Pulse participate in Polymarket referral economics via market promotion":

• confirmed Builder Program path in current Polymarket docs: participation is tied to attributed CLOB execution (builder headers + credentials), with tiered weekly rewards/revshare.
• no separate consumer-style invite-link referral flow was found in current developer/help surfaces for `polymarket.com`.
• identified separate US exchange referral notice (`polymarketexchange.com` Terms; notice date 2026-01-16, effective 2026-02-02), treated as a different track from builder API integration.

Current system readiness vs referral monetization:

• ready: market discovery/signals (`top_movers_latest`, watchlist/picker flows), distribution (site/bot/email), and attribution scaffolding (`app.site_events` with placement + utm fields).
• missing: order execution surface under Pulse control and builder-attributed order routing.
• conclusion: current architecture can optimize traffic + activation immediately, but Builder Program monetization requires adding a trade execution layer.

Implementation direction captured in architecture:

• phase 1: outbound market-link instrumentation (bot/landing/newsletter) and campaign analytics.
• phase 2: attributed trade execution integration for web/app entry points.
• phase 3: automated builder rewards/trades reconciliation to internal reporting.

---

# Bot Guide Pages Rollout (2026-03-11)

Implemented the approved v2 scope for human-friendly command guidance.

New web pages (RU/EN):

• `/how-it-works` (scenario-first command guidance in strict dark card format)
• `/commands` (full command reference with restricted/admin note)

Added templates:

• `api/web/how-it-works.en.html`
• `api/web/how-it-works.ru.html`
• `api/web/commands.en.html`
• `api/web/commands.ru.html`

Routing/API updates:

• `GET /how-it-works`
• `GET /commands`
• sitemap now includes EN/RU variants for both pages

Integration updates:

• main landing (EN/RU): added `How it works? / Как это работает?` near primary Telegram CTA
• SEO `/telegram-bot` page now includes explicit CTA to `/how-it-works`
• cross-links wired:
  - `/how-it-works` -> `/commands` with `placement=how_it_works_footer`
  - `/commands` -> `/how-it-works` with `placement=commands_crosslink`

Telemetry contract:

• no new `event_type` introduced
• attribution uses existing `page_view` with `placement` on destination page (`main_cta`, `telegram_bot_page`, `how_it_works_footer`, `commands_crosslink`)

---

# Hero Grid Alignment Fix (2026-03-12)

Main landing RU/EN hero grid was adjusted to remove visual seam between movers chart block and CTA panel.

Updated templates:

• `api/web/index.en.html`
• `api/web/index.ru.html`

Layout updates:

• forced equal-height behavior in hero grid (`align-items: stretch`)
• made both hero columns vertical flex containers (`.ticker`, `.cta-panel`) with `height: 100%`
• stabilized movers rows block alignment (`align-content: start`) to avoid jagged visual join at the column boundary

---

# Live Movers Sparkline API Fix (2026-03-12)

Fixed landing preview API bug where sparkline arrays were often flat due to weak history sampling.

Updated backend:

• `api/main.py` -> `/api/live-movers-preview` now builds `spark` from last per-market snapshots (up to 16), ordered by `ts_bucket ASC`  
• spark source now uses per-bucket yes mid fallback logic (`(yes_bid+yes_ask)/2`, fallback to available side)  
• if a market has fewer than 2 snapshot points, API returns `spark: []`  
• preview selection now prioritizes movers with richer spark history (`distinct >= 6`) to avoid flat-line cards on landing

Local verification:

• endpoint returns 3 rows with `spark` arrays of length 16  
• each returned row had `6+` distinct float values in current live dataset

---

# Bot Watchlist Picker Widening + UX Cleanup (2026-03-12)

Improved `/watchlist_add` picker quality and reduced callback noise in Telegram.

Updated backend/runtime:

• `bot/main.py` picker SQL now uses the latest available quotes per market from a rolling 6h window (instead of strict latest bucket only)  
• candidate pool excludes markets already present in the user’s watchlist  
• `all` filter now returns a broader balanced set (up to 16 candidates) across `politics/macro/crypto/other`  
• category filter callbacks now edit the existing picker message instead of appending a new message each tap

Validation against live DB:

• `all` filter produced 16 candidates with category mix (`4 politics / 4 macro / 4 crypto / 4 other`)  
• for a user with existing watchlist entries, picker result had zero intersection with current watchlist

---

# B2 Activation Funnel Tightening (2026-03-13)

Started the next unresolved 14-day-plan step: make `/watchlist_add` reliably useful for first-market activation.

Updated runtime in `bot/main.py`:

• added explicit picker liquidity floor via env/config: `WATCHLIST_PICKER_MIN_LIQUIDITY` (default `1000`)
• picker candidate query now requires live bid/ask quotes within the rolling 6h window **and** liquidity above the configured floor
• removed stale `recent_seen` fallback from the picker path so the button flow no longer surfaces merely “recent” but not truly live markets
• `liquid_live` candidate source is now constrained to `public.market_universe`, keeping picker suggestions aligned with the curated live coverage layer
• ranking is now hybrid instead of raw delta-first:
  - `hybrid_score = abs(delta) * 100 + ln(1 + liquidity)`
  - `prio` remains only as a tiebreak, not the primary sort key
• picker zero-state now explicitly explains the current liquidity floor, so empty states are operationally clear

Smoke result:

• syntax check passed for `bot/main.py`
• live query smoke produced category-balanced candidates with current live liquidity and non-trivial deltas
• top returned candidates now come from live/liquid markets rather than the broader “recently seen” pool

---

# Site Conversion Tracking Hardening (2026-03-12)

Strengthened event delivery reliability for website-to-Telegram conversion tracking.

Updated templates:

• `api/web/index.en.html`  
• `api/web/index.ru.html`  
• `api/web/how-it-works.en.html`  
• `api/web/how-it-works.ru.html`  
• `api/web/commands.en.html`  
• `api/web/commands.ru.html`

What changed:

• `trackEvent(...)` now mirrors events to GA4 (`gtag`) and to internal `app.site_events` in parallel  
• primary transport for `app.site_events` switched to `navigator.sendBeacon(...)` with `fetch(... keepalive)` fallback for better click capture before navigation  
• added explicit conversion touchpoint tracking on landing:
  - `waitlist_intent` for “How it works?” CTA
  - `checkout_intent` for Telegram Stars CTA in PRO section

Current 24h baseline before this hardening:

• `page_view=28`, `tg_click=1` (placement observed: `mobile_sticky`)

---

# Competitive C1 Refresh (2026-03-12)

Completed the current `C1` step from the 14-day plan (competitive intelligence update).

Delivered artifacts:

• refreshed directory scan output: `docs/competitive_sweep_latest.md` (from `scripts/growth/competitive_scan.py`)  
• new decision-layer gap matrix: `docs/competitive_gap_matrix_2026-03-12.md`  
• refreshed positioning pack: `docs/positioning_messages_latest.md`

C1 outputs locked:

• top-7 competitor gap table with interception angles  
• 3 finalized positioning messages for site + bot + social  
• 7-day execution list for search + Telegram activation + social capture

---

# C1 Implementation on Site Surfaces (2026-03-12)

Applied the finalized C1 positioning pack directly to user-facing web surfaces.

Updated:

• `api/web/index.en.html`  
• `api/web/index.ru.html`  
• `api/main.py` (`SEO_PAGES["telegram-bot"]` RU/EN copy)

Implementation details:

• landing hero subcopy now explicitly carries “action over dashboards”  
• landing FAQ now includes “Why Telegram-first?” with the 60-second activation argument  
• `/telegram-bot` SEO page now uses the finalized 3-message frame:
  - action over dashboard overload
  - 60-second activation
  - signal quality over noise

---

# C2 Social Pipeline EN-Only Mode (2026-03-12)

Started C2 execution with an English-only social publishing mode.

Updated:

• `scripts/growth/generate_social_drafts.py`  
• `docs/social_pipeline.md`  
• `docs/social_drafts_latest.md`  
• `docs/reels_tiktok_scripts_2026-03-08.md`

Changes:

• social draft generator now supports explicit `--langs` and `--channels` filters (with validation)  
• default workflow switched to `EN-only` (`--langs en`) for X + Threads  
• refreshed latest social draft pack generated from live DB with EN-only posts and UTM links  
• Reels/TikTok script pack marked as EN-only operating mode and aligned with C1 message frame

---

# App Store Visual Refresh (2026-03-10)

Upgraded web visual system to an App Store-grade presentation while keeping the existing dark/green brand contract.

Updated surfaces:

• `api/web/index.en.html`
• `api/web/index.ru.html`
• `api/main.py::render_seo_page`

What changed:

• typography switched to `Space Grotesk` (display) + `JetBrains Mono` (data/terminal copy)
• hero now includes rating/product badges + three compact performance metrics cards
• added `Preview screens` section (three product-surface cards with micro visual bars) between hero and proof blocks
• SEO pages now share the same visual language (badge row, stat cards, preview cards, upgraded CTA hierarchy)
• motion model updated to one-shot reveal animations (`~280ms`) with `prefers-reduced-motion` support and without infinite decorative loops
• removed the “App Store-grade UX” hero badge text from EN/RU landing and SEO templates to keep messaging tighter

Expected product impact:

• stronger “premium app” perception on first screen
• clearer surface-level understanding of product value before Telegram click
• tighter visual consistency across landing and SEO intent pages

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
• connected Placid MCP template workflow for rendered social creatives:
  - validated template UUIDs: `qpfepwdjvsuxv`, `1h9uyopu3rarv`, `m6nbvjbbyarrj`
  - new script: `scripts/growth/generate_social_visuals.py`
  - script reads live DB (`top_movers_latest` + `alerts_inbox_latest`) and renders:
    - `top3` card
    - `breakout` card
    - `weekly` card
  - output manifest: `docs/social_visuals_latest.md`
  - added runbook section in `docs/social_pipeline.md`
• added brand-native social card renderer (replaces stock-looking backgrounds for daily posting):
  - script: `scripts/growth/render_social_cards.py`
  - output cards: `assets/social/out/top3-latest.svg`, `assets/social/out/breakout-latest.svg`, `assets/social/out/weekly-latest.svg`
  - style synced with landing contract: dark terminal palette (`#0d0f0e`, `#131714`, `#1e2520`, `#e8ede9`, `#00ff88`)
• added short-form meme video renderer for growth testing:
  - script: `scripts/growth/render_shitpost_short.py`
  - output: `assets/social/out/shitpost-live-5s.mp4`
  - runtime: 5s vertical clip (`1080x1920`, 30fps) with live market deltas from `public.top_movers_latest`
  - visual contract remains brand-consistent (dark terminal + neon green accents), while edit rhythm is intentionally “cursed” for social hooks

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

---

# Recent Operating Updates (2026-03-18)

• `Pulse` activation loop was tightened further:
  - `/watchlist_list` now doubles as a return screen with action buttons (`Watchlist`, `Add market`, `Inbox`, `Top movers`)
  - when the list contains closed markets, it also exposes one-tap `Remove closed`
• `Trader` connect flow is shorter:
  - after `/connect <wallet>`, the bot now creates or reuses a signer session automatically
  - users get the signer page CTA immediately instead of having to discover `/signer` as a separate step
  - `/connect` without args also surfaces the signer step again for non-ready wallets
• `Pulse` `/start` now distinguishes between new and returning users:
  - new users get the one-tap onboarding market flow
  - returning users get a lighter “resume” screen with direct actions into watchlist, inbox, threshold and movers
• `Trader` `/ready` and `/order` now reuse the signer CTA surface for non-ready wallets, so the next execution step is actionable right from the lifecycle screens
