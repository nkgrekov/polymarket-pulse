# Mobile Homepage + Watchlist Scan Pass (2026-04-29)

Applied a mobile-first cleanup pass to the homepage and website watchlist workspace.

Files updated:

• `api/web/index.en.html`
• `api/main.py`
• `progress.md`
• `architecture.md`

What changed:

• reduced homepage mobile scroll debt before the first live board:
  - hid the secondary signal badge on small screens
  - removed the product-split chip row on small screens
  - tightened header spacing and hid the secondary brand copy
• made homepage mobile rows read more like tappable market cards:
  - taller sparklines
  - slightly denser row paddings
  - action pills now wrap more cleanly into a 2-up mobile pattern
• improved mobile watchlist scan speed:
  - summary cards stay compact across the top on normal phones and collapse only on very narrow screens
  - controls now use a 2-column mobile layout with search and view toggle spanning full width
  - watchlist cards use taller charts, stacked title/bell layout, 2-column metric chips, and a clearer action hierarchy

What did not change:

• no watchlist persistence logic changed
• no auth flow changed
• no delivery semantics changed

# Homepage Full-Width Scene Pass (2026-04-29)

Applied a third homepage refinement pass to make the first screen behave like a real wide monitoring surface instead of a left-heavy landing block.

Files updated:

• `api/web/index.en.html`
• `progress.md`
• `architecture.md`

What changed:

• widened the desktop shell again so the homepage spends more of the browser width on actual product surface instead of side gutters
• removed the split-top hero composition:
  - the copy now owns the full top width first
  - the live board and explainer now sit together underneath as one operational scene
• kept the homepage H1 short and desktop-first:
  - `Track Live Movers`
  - now uses the available horizontal space with one-line intent on wide screens
• simplified the right-side explainer card down to one visual grammar:
  - one title
  - one paragraph
  - one three-step list
  - one footnote
• replaced the long hero product-split sentence with three compact chips so the logic reads at a glance
• increased live-board spark height again so the top board earns more visual weight

What did not change:

• no backend logic changed
• no watchlist sync/auth logic changed
• no pricing backend changed

# Homepage Width + Hero Discipline Pass (2026-04-29)

Applied a second homepage refinement pass after live visual feedback.

Files updated:

• `api/web/index.en.html`
• `progress.md`
• `architecture.md`

What changed:

• expanded the desktop shell width substantially to reduce black side gutters on wide screens
• fixed the hero-top alignment bug that created dead air above the left copy
• made the homepage H1 desktop-first and one-line:
  - `Track Live Movers`
  - now uses the available horizontal space instead of stacking into an awkward two-line block on wide screens
• replaced the long hero footer sentence with compact chips so the product split reads faster
• simplified the right-side hero card again:
  - one kicker
  - one heading
  - one explanatory paragraph
  - one three-item list
  - one plain footnote
• removed the extra visual styles from the old right-card trust-pill treatment
• increased homepage spark height again so the board reads more like a real monitoring surface on desktop

What did not change:

• no backend logic changed
• no watchlist/auth flow changed
• no pricing semantics changed beyond presentation

# Homepage De-Noise + Stars-Only Pricing Pass (2026-04-29)

Addressed the latest homepage UX review in one focused cleanup pass.

Files updated:

• `api/web/index.en.html`
• `progress.md`
• `architecture.md`

What changed:

• reduced the homepage headline from a four-line slogan to a short three-word value statement:
  - `Track Live Movers`
  - removed the trailing period
  - trimmed the supporting copy so the first screen is not prose-heavy
• rebalanced the hero to use the full top width more effectively:
  - added a `hero-top` split where the left side owns the main promise and CTA
  - reduced the right-side panel to a compact decision card instead of a second giant headline
  - moved the live board into a full-width block directly under the hero top instead of sharing the first-screen budget with a dense side stack
• made the static homepage live board look like a real board even in local file preview:
  - increased the default row count from 3 to 5
  - added visible placeholder spark charts to the static HTML rows
  - the runtime fetch path now also requests `limit=5`
• removed the duplicate mid-page Telegram bridge CTA:
  - deleted the old `proof-bridge` section
  - kept the main top CTA plus the sticky/mobile CTA and pricing CTA only
• simplified homepage pricing around the new payment doctrine:
  - homepage pricing is now framed as `Telegram Stars only`
  - removed the Stripe email field and `Pay with card (Stripe)` button from the visible product path
  - replaced the right column with one clean Stars CTA plus a short explanatory card
• moved the noisy secondary content behind one disclosure:
  - preview screens
  - historical examples
  - search/SEO entry pages
  - FAQ
  - email backup form
• improved the search-path block readability:
  - added small icon-like badges to each entry card
  - reduced the list to the more useful six entry surfaces

What did not change:

• no bot logic changed
• no watchlist auth/session logic changed
• no payment backend migration changed in this pass
• no RU homepage redesign changed in this pass

Checks run:

• `python3 -m py_compile api/main.py`
• `git diff --check`

Follow-up:

• the next homepage pass should be a real browser/device QA round, especially mobile height and sticky CTA behavior
• the next billing step remains product/backend work inside Telegram rather than another homepage checkout experiment

# Homepage Priority + Bulk Watchlist Sync + Bigger Charts (2026-04-29)

Pushed the next focused polish pass on the two user-facing pain points:

• homepage first-screen hierarchy
• slow post-login watchlist reconciliation

Files updated:

• `api/main.py`
• `api/web/index.en.html`
• `api/web/index.ru.html`
• `api/web/watchlist-client.js`
• `progress.md`
• `architecture.md`

What changed:

• moved the homepage live board into the real first-screen budget:
  - `homepage-live-board` now sits directly under the hero CTAs instead of below explanatory blocks
  - the first visible promise is now board-first, not prose-first
  - the right-side hero panel was compacted so the board owns more of the attention budget on desktop and mobile
• reduced homepage visual noise without changing the design identity:
  - workflow explanation is now behind a compact disclosure block instead of always expanded
  - plan / backup-email / bot-flow support is now behind a separate compact drawer
  - the visible hero copy now stays closer to:
    - headline
    - CTA
    - live board
• accelerated post-login watchlist reconciliation:
  - added `/api/watchlist/sync`
  - pending browser-local watchlist rows now sync in one request instead of one request per market after Telegram login
  - this removes the most obvious N-request slowdown from the bridge loop
• upgraded watchlist row charting:
  - the old micro-sparklines were replaced with larger framed mini-charts
  - desktop workspace rows now get substantially wider/higher chart real estate
  - cards also inherit the larger chart treatment
• hardened watchlist client delivery:
  - the site now points the client loader at a fresh API-served asset path instead of relying only on the legacy shared path
  - this is meant to reduce stale-client mismatches when HTML updates reach prod faster than JS caches do

What did not change:

• no bot delivery semantics changed
• no payment migration happened yet
• no Telegram Stars-only cutover happened in this pass
• no ingest logic or live ranking logic changed
• no RU homepage redesign was introduced; only the shared watchlist client include path was updated

Checks run:

• `python3 -m py_compile api/main.py`
• `node --check api/web/watchlist-client.js`
• `git diff --check`

Deployment / verification notes:

• site was redeployed through Railway multiple times during this pass
• prod HTML confirms the homepage hierarchy changes (`Live board first`, compact drawers, `homepage-live-board`)
• anonymous `POST /api/watchlist/sync` on prod correctly returns `telegram_login_required`
• there is still edge-cache inconsistency around the watchlist client asset path on prod:
  - homepage HTML and API runtime are not always surfacing the same newest script reference immediately
  - this likely needs one clean CDN cache purge or a calmer propagation window before final prod verification of the faster sync loop

Risks / follow-up:

• once the fresh watchlist client path is visibly live on prod, we should run one real end-to-end login test:
  - add pending market
  - Telegram login
  - return to site
  - confirm batch sync feels materially faster
• after that, the next product task remains the billing simplification:
  - Telegram Stars as the primary paid path inside the bot

# Watchlist Truthfulness + Post-Login Sync Fix (2026-04-28)

Closed the first real watchlist UX bug loop after live user feedback.

Files updated:

• `api/main.py`
• `api/web/watchlist-client.js`
• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• fixed the misleading logged-out `Add to watchlist` state:
  - the row action no longer pretends a browser-local pending item is fully persisted
  - pending rows/buttons now read as `Pending login` instead of indistinguishable `Saved`
  - a second click on a pending row reopens the Telegram bridge instead of silently redirecting
• added post-login pending reconciliation on the website:
  - after a valid Telegram website session appears, the client now attempts to sync locally pending markets into the server-backed watchlist
  - successful sync clears local pending state and refreshes the real workspace
  - if some pending items still fail to sync, they remain visible in the workspace as pending instead of disappearing
• made the Telegram bridge copy more explicit:
  - bot replies now tell the user to tap `Return to site` to finish the website session loop
  - the site prompt now also explains that Telegram login is not finished until the user returns to the website
• promoted the real watchlist workspace to the top of `/watchlist`:
  - workspace now renders before the large explainer hero
  - the watchlist hero is compacted
  - the redundant preview block is removed for `/watchlist`
• fixed rollout correctness for the watchlist client:
  - the website now loads `watchlist-client.js` through a versioned asset URL
  - the JS endpoint now advertises a shorter cache window so UI logic updates do not stay stale for hours behind edge cache
• made the workspace itself easier to scan:
  - added a top summary strip for `saved`, `bell on`, and `pending login`
  - logged-out banners now distinguish plain logged-out browsing from unsynced local pending markets
  - workspace header copy now clearly says that the real saved-market surface is the table/card workspace, not the explainer copy
• added another polish layer for watchlist confidence:
  - workspace rows now render mini sparkline charts from recent market snapshot history when available
  - the first site load after `tg_auth=1` now shows an explicit success banner:
    - `Telegram connected`
    - or `Telegram connected. Watchlist synced.`
  - this makes the post-login bridge visible instead of implicit

What did not change:

• no DB schema change
• no public grant or auth surface expansion
• no delivery semantics change
• no direct frontend-to-Polymarket runtime fetch
• RU homepage was not touched

Manual test focus:

• logged out:
  - click `Add to watchlist` on a live row
  - confirm the button changes to `Pending login`, not plain `Saved`
  - open `/watchlist` and confirm the pending row is visible immediately
• Telegram bridge:
  - complete login through the bot
  - tap `Return to site`
  - confirm pending rows become real saved rows on the site
• watchlist page:
  - confirm the workspace table/cards appear above the explainer card
  - confirm summary counters render
  - confirm filters/sorting still work

Risks / follow-up:

• the website can now reconcile pending rows after login, but we still need one fresh live user pass to verify behavior across Telegram app/browser combinations
• if Telegram opens the return link in a different browser context, the user can still miss the cookie attach step; the copy is clearer now, but a later fallback UX may still help

# Prompt 8-10 UX + Instrumentation Pass (2026-04-28)

Implemented the next `new horizon` cycle across the web UI, Telegram bot UX, and measurement layer.

Files updated:

• `api/main.py`
• `api/web/index.en.html`
• `api/web/watchlist-client.js`
• `bot/main.py`
• `scripts/growth/weekly_kpi_report.py`
• `progress.md`
• `architecture.md`

What changed:

• fixed a critical recursion bug in `bot.main.save_watchlist_market_sync(...)`
  - site bridge save / bell flows now persist watchlist membership + alert settings safely
  - removed the accidental self-call loop risk before taking the new UX deeper into production
• aligned Telegram bot copy with the website-first watchlist model:
  - `/start` now explains website = workspace, Telegram = identity + bell + delivery
  - `/watchlist` now surfaces saved vs bell-on vs bell-paused counts inline
  - `/inbox` keeps threshold clarity and now logs `inbox_opened`
  - `/plan` and plan summary copy now explicitly distinguish saved markets from bell-enabled alerts
• improved alert setup completion flow in Telegram:
  - after sensitivity selection, users now get a tighter return action set
  - website return from alert is now attributable through `from=alert`
• polished component roles on the site without changing the design identity:
  - action buttons no longer overuse uppercase
  - metadata chips gained explanatory tooltips for freshness / liquidity / spread / quality / state
  - live boards now use clearer empty / unavailable / filtered states instead of going blank or vague
  - homepage live board label is now product-native (`Markets moving now`) instead of dev-facing wording
• expanded website instrumentation:
  - `live_board_impression`
  - `watchlist_add_click`
  - `watchlist_add_success`
  - `bell_click`
  - `telegram_login_click`
  - `pricing_seen`
  - `pricing_cta_click`
  - `alert_click_back_to_site`
• expanded Telegram / bot-side instrumentation:
  - `site_login_completed`
  - `watchlist_add_from_site_payload`
  - `alert_setup_started`
  - `alert_sensitivity_selected`
  - `alert_enabled`
  - `watchlist_opened`
  - `inbox_opened`
  - `alert_sent`
• updated weekly KPI reporting:
  - legacy funnel stays intact
  - added a dedicated website -> Telegram watchlist loop section
  - added pricing visibility / CTA visibility checks
  - added alert-enabled / alert-sent / click-back loop readout

What did not change:

• no direct frontend-to-Polymarket fetches were introduced
• no public Supabase grants were reopened
• no hot-first delivery cutover happened
• RU homepage was not redesigned
• no broad schema rewrite happened
• trader services remain outside this pass

Manual test:

• open homepage and confirm:
  - live board still renders
  - row actions are visually distinct from metadata
  - pricing section is still intact
• open `/signals`, `/top-movers`, `/analytics`, `/telegram-bot`, `/watchlist`, `/watchlist-alerts`
  - confirm live board / workspace empty states are honest and actionable
  - confirm watchlist / bell buttons still exist
• from the site:
  - click `Add to watchlist`
  - click bell
  - complete Telegram login / sensitivity path
  - return to `/watchlist`
  - confirm event loop and bell state remain coherent
• in Telegram:
  - `/start` with plain open
  - `/start` from login payload
  - `/start` from site watchlist add payload
  - `/start` from site bell payload
  - `/watchlist`
  - `/inbox`
  - `/plan`
• run `python3 scripts/growth/weekly_kpi_report.py --days 7`

Risks / follow-up:

• website and bot event taxonomies are now broader, so the next useful step is a live KPI snapshot after a few real user sessions
• alert pause / disable remains a narrower flow than full alert-state management; the copy is now honest, but the control surface can still improve later
• homepage instrumentation now records pricing visibility and board impressions, but GA/GSC review is still needed for external traffic interpretation

# Polymarket Pulse — Implementation Progress

This document tracks the current state of the project.

---

# SEO Intent Pages First-Screen Split (2026-04-28)

Started the `PROMPT 7` pass by making the English dynamic intent pages feel like different product surfaces instead of one shared template with different H1 text.

Files updated:

• `api/main.py`
• `progress.md`
• `architecture.md`

What changed:

• added page-specific first-screen stat blocks for:
  - `/signals`
  - `/top-movers`
  - `/analytics`
  - `/telegram-bot`
  - `/watchlist-alerts`
  - `/dashboard`
  - `/watchlist`
• added page-specific hero support surfaces:
  - `/signals` now opens with signal-filter framing
  - `/top-movers` now opens with movers-specific row/action framing
  - `/analytics` now opens with category-view context derived from live mover samples
  - `/telegram-bot` now shows `BOT FLOW` in the hero area instead of only lower on the page
  - `/watchlist-alerts` now explains the save -> bell -> Telegram threshold -> alert return loop
  - `/dashboard` now explicitly compares dashboard habit vs Pulse workflow
• moved the live board higher for:
  - `/signals`
  - `/top-movers`
  so first-screen value is visible before users scan generic preview cards
• specialized live-board labels:
  - `/signals` -> signal board
  - `/top-movers` -> top movers board
  - `/analytics` -> live analytics tape
• kept `/how-it-works` and `/commands` unchanged in this step because they were already scenario-first vs reference-first and did not share the same first-screen problem as the dynamic pages

What did not change:

• no bot runtime changed
• no DB schema changed
• no alert delivery semantics changed
• no RU-first redesign work was added
• `/how-it-works` and `/commands` copy/layout were not rewritten in this step

Manual test:

• open each English page and confirm the first screen is meaningfully different:
  - `/signals`
  - `/top-movers`
  - `/analytics`
  - `/telegram-bot`
  - `/watchlist-alerts`
  - `/dashboard`
• confirm page-specific markers exist:
  - `Signal filters`
  - `Top movers workflow`
  - `Category view`
  - `BOT FLOW`
  - `Watchlist -> bell -> alert`
  - `Why this is not another dashboard`
• confirm live board remains present and actionable on the pages that need it

Risks / follow-up:

• this is the EN-first dynamic core of `PROMPT 7`; broader static-page restyling can still happen later if we decide the first screens of `/how-it-works` or `/commands` need more product polish
• analytics category cards are derived from current live mover samples, so the mix can shift over time by design

# Homepage Workspace Clarity Pass (2026-04-28)

Implemented `PROMPT 2` from `new horizon` and tightened the homepage so it explains the new product model without requiring scroll: website as live market workspace, Telegram as login + bell + alert layer.

Files updated:

• `api/web/index.en.html`
• `progress.md`
• `architecture.md`

What changed:

• rewrote the English homepage hero around the new core promise:
  - see live movers now
  - save markets to watchlist
  - use Telegram only when the bell and thresholded alerts are needed
• added a new above-the-fold CTA hierarchy:
  - primary `Open Telegram Bot`
  - secondary `View live movers`
  - email pushed down into backup-only role
• changed hero metrics so they explain:
  - what moved
  - what watchlist means
  - what bell / threshold means
• added a compact website-vs-Telegram explainer strip directly in the hero
• rewrote the right-side hero panel so it no longer reads like a pure Telegram landing panel:
  - live workspace copy
  - bell semantics copy
  - early Free vs Pro teaser
• demoted email signup to explicit backup positioning:
  - “Don’t use Telegram? Get digest updates by email.”
• moved pricing clarity higher in the journey and updated the full pricing section copy so it reflects:
  - site research first
  - plan limits matter when saving markets and enabling bells
What did not change:

• no bot runtime changed
• no ingest logic changed
• no DB schema or API contract changed
• no watchlist persistence semantics changed
• no alert delivery semantics changed
• no RU homepage copy or structure changed in this step

Manual test:

• open the English homepage
• confirm above the fold now explains:
  - what moved
  - what watchlist does
  - what bell does
  - why Telegram is still needed
• confirm `Open Telegram Bot` and `View live movers` are both visible before scroll
• confirm email reads as backup-only, not equal primary CTA
• confirm pricing teaser appears in the hero panel and full pricing still anchors from `/#pricing`

Risks / follow-up:

• homepage copy is now aligned with the new model, but the deeper SEO/intent pages still need their own distinct first-screen redesign in later prompts
• plan copy stays truthful to current runtime limits; this step does not introduce broader “unlimited web watchlist” claims that the backend does not yet enforce

# Telegram Identity Bridge + Bell Model + Hot Alert Alignment (2026-04-27)

Implemented the next `new horizon` core step: website watchlist persistence now has a real Telegram identity bridge, bell alerts are separated from saved markets at the model level, and hot alert candidates no longer treat every saved watchlist row as alert-eligible by default.

Files updated:

• `db/migrations/017_web_watchlist_identity_and_alerts.sql`
• `api/main.py`
• `api/web/watchlist-client.js`
• `api/web/index.en.html`
• `api/web/index.ru.html`
• `bot/main.py`
• `ingest/live_main.py`
• `progress.md`
• `architecture.md`

What changed:

• added a repo-managed schema step for three new server-side objects:
  - `app.web_auth_requests`
  - `app.web_sessions`
  - `bot.watchlist_alert_settings`
• backfilled `bot.watchlist_alert_settings` for existing Telegram/legacy watchlist rows with:
  - `alert_enabled = true`
  - `alert_paused = false`
  - `source = 'legacy_backfill'`
  so existing users do not silently lose alerts
• added server-side website identity/session flow in `api/main.py`:
  - `/api/watchlist/session`
  - `/api/watchlist/auth/start`
  - `/api/watchlist/save`
  - `/api/watchlist/remove`
  - `/auth/telegram/complete`
• website session now uses Telegram as the identity resolver:
  - logged-out browsing still works
  - save/bell persistence now requires Telegram identity
  - return loop sets an httpOnly cookie instead of exposing DB credentials client-side
• implemented new Telegram deep-link families across site and bot:
  - `site_login_<token>`
  - `site_watchlist_add_<market_id>_<token>`
  - `site_alert_<market_id>_<token>`
  - `site_return_watchlist_<token>`
  - plus tokenless `site_alert_<market_id>` for manage-alert reentry inside Telegram
• website watchlist workspace now loads from real server-backed watchlist rows when logged in
• logged-out workspace remains additive:
  - market context is kept locally
  - hydration still happens through the existing read-only workspace API
  - persistence flips to server-backed only after Telegram login completes
• added bell surfaces to live market rows and watchlist rows:
  - homepage mover rows now expose bell action
  - dynamic live signal boards already expose bell action
  - `/watchlist` now shows bell state, sensitivity, and last alert timestamp when available
• changed watchlist product semantics:
  - saved web watchlist rows can exist with `alert_enabled = false`
  - bell state is no longer implied by simple watchlist membership
• changed hot alert candidate generation in `ingest/live_main.py`:
  - source rows now come only from `bot.watchlist_alert_settings` where:
    - `alert_enabled = true`
    - `alert_paused = false`
  - per-market threshold now prefers `watchlist_alert_settings.threshold_value`, then user global `/threshold`
• kept hot watchlist snapshot broad:
  - it still represents all saved markets
  - only hot alert candidate generation narrows to bell-enabled rows
• hardened legacy-primary delivery without cutover:
  - push loop now suppresses watchlist sends when `alert_enabled = false`
  - push loop now suppresses watchlist sends when `alert_paused = true`
  - current conservative legacy delivery posture stays intact otherwise
• Telegram bot now supports bell setup flow:
  - website alert bridge deep-link lands in Telegram
  - bot asks for sensitivity options:
    - `1pp`
    - `2pp`
    - `3pp`
    - `5pp`
    - `10pp`
    - `Major`
  - chosen value is persisted into `bot.watchlist_alert_settings`
• watchlist push alerts now include action buttons:
  - open on site
  - open on Polymarket
  - manage alert

What did not change:

• no public DB credentials or direct client DB access were introduced
• no public grants were reopened
• no hot-first delivery cutover happened
• no rewrite of `bot.watchlist` membership storage happened
• no direct frontend calls to Polymarket were added
• no existing `/threshold` command semantics were broken

Manual test:

• logged out on `/signals` or `/top-movers`, click `Add to watchlist`
• confirm Telegram bridge prompt opens instead of fake persistence
• finish Telegram `/start` bridge and open the return link back to the site
• confirm `/watchlist` now persists after refresh
• click bell on a saved market
• confirm Telegram asks for sensitivity
• choose one threshold option
• refresh `/watchlist`
• confirm bell state, sensitivity, and last alert metadata appear from server-backed state
• confirm a saved-but-bell-off market stays visible in watchlist workspace
• confirm bell-disabled market is not considered a hot alert candidate anymore

Risks / follow-up:

• production still needs migration `017_web_watchlist_identity_and_alerts.sql` applied before the new auth/bell path can work end-to-end
• existing Telegram-first watchlist rows were intentionally backfilled as bell-enabled for compatibility, so the old bot contract stays alive until a later cleanup pass
• the website now has a real identity/session bridge, but bell pause/off management inside Telegram is still a narrow callback flow rather than a full standalone command surface
• next logical step is `PROMPT 6` follow-through validation in prod and then the page-distinction/SEO redesign phase, not another local-only watchlist prototype

# Website Watchlist UX Workspace (2026-04-27)

Implemented the first real web watchlist workflow so saved markets now behave like a website object, while alerts remain a separate Telegram-first layer.

Files updated:

• `api/main.py`
• `api/web/index.en.html`
• `api/web/index.ru.html`
• `api/web/watchlist-client.js`
• `progress.md`
• `architecture.md`

What changed:

• added `Add to watchlist` actions to live market rows on:
  - homepage live movers board
  - `/signals`
  - `/top-movers`
  - `/analytics`
  - `/telegram-bot`
• added browser-backed watchlist storage through a shared client script:
  - local saved markets
  - local alert state (`off / on / paused`)
  - local sensitivity presets
  - pending Telegram context when user is not logged in
• added a new read-only API surface:
  - `/api/watchlist-workspace`
  which hydrates saved market ids from existing hot/legacy DB surfaces
• upgraded `/watchlist` from doctrine page into a real workspace surface with:
  - search
  - category filter
  - status filter
  - alert-state filter
  - sort by delta / liquidity / spread / freshness / saved time
  - compact table toggle
  - mobile card view
• workspace rows now expose:
  - question
  - current mid
  - delta
  - 1m / 5m movement
  - liquidity
  - spread
  - freshness
  - market status
  - signal quality
  - alert state
  - sensitivity
  - actions
• logged-out add / alert actions now trigger a lightweight Telegram prompt while keeping the selected market context in local browser state

What did not change:

• no Telegram bot commands changed
• no DB write path for watchlist identity was introduced yet
• no frontend direct calls to Polymarket were added
• no live ingest / ranking / delivery semantics changed
• alert persistence is still not server-backed; this step stays additive and reversible

Manual test:

• from `/` save a live market with `Add to watchlist`
• confirm a logged-out Telegram prompt appears
• open `/watchlist`
• confirm the row appears with current metrics and actions
• test search, category filter, status filter, alert-state filter, and sort controls
• toggle alert state and sensitivity locally
• remove a market
• confirm mobile card layout below mobile breakpoint

Risks / follow-up:

• current watchlist persistence is browser-local until the Telegram identity/login layer lands in later prompts
• alert state shown on the site is currently local planning state, not yet a server-backed Telegram truth source
• next logical step is the Telegram login / identity handshake so local watchlist state can become cross-device and real


# Global Site Header And Watchlist Entry Surface (2026-04-27)

Started the `new horizon` site-model pass by aligning the public web surface with the product doctrine: website as research workspace, Telegram as identity and alert loop.

Files updated:

• `api/main.py`
• `api/web/index.en.html`
• `api/web/index.ru.html`
• `api/web/how-it-works.en.html`
• `api/web/how-it-works.ru.html`
• `api/web/commands.en.html`
• `api/web/commands.ru.html`
• `progress.md`
• `architecture.md`

What changed:

• added a consistent sticky global header across:
  - `/`
  - `/signals`
  - `/top-movers`
  - `/analytics`
  - `/telegram-bot`
  - `/watchlist-alerts`
  - `/dashboard`
  - `/how-it-works`
  - `/commands`
• header now standardizes:
  - `Live Movers`
  - `Signals`
  - `Watchlist`
  - `Commands`
  - `Pricing`
  - primary `Open Telegram Bot` CTA
• added compact mobile navigation through a `details` menu instead of a separate JS nav system
• introduced a new `/watchlist` SEO/product page as a safe entry surface for the watchlist concept
• `/watchlist` copy now makes the product doctrine explicit:
  - watchlist and alerts are separate concepts
  - Telegram remains the current identity / threshold / alert control loop
• added `#pricing` anchor targeting on the homepage and wired the new header pricing link to it
• cleaned related-link copy on dynamic SEO pages so internal links use concise product labels instead of long H1 strings

What did not change:

• no Telegram bot command behavior changed
• no ingest, hot-surface, DB schema, or delivery semantics changed
• no live market ranking logic changed
• no homepage visual identity rewrite happened; the dark terminal language remains intact

Manual test:

• open `/`, `/signals`, `/top-movers`, `/analytics`, `/telegram-bot`, `/watchlist`, `/watchlist-alerts`, `/dashboard`, `/how-it-works`, `/commands`
• confirm sticky header is visible
• confirm `Open Telegram Bot` works from header and mobile menu
• confirm `Pricing` lands on the homepage pricing block
• confirm `Commands` is active on `/commands`
• confirm `Watchlist` is active on `/watchlist` and `/watchlist-alerts`
• confirm mobile menu does not overlap the hero permanently

Risks / follow-up:

• local `api.main` render smoke is currently limited by missing `psycopg` in the shell environment, so final validation should happen on deployed Railway site
• `/watchlist` is currently a product-structure page, not the full saved-market workspace from later prompts
• next logical prompt is the actual watchlist-vs-alert interaction model on web, not another design pass


# Legacy Push Shock Hardening (2026-04-27)

Added a conservative suppression layer in the bot push loop so legacy watchlist alerts do not send when hot state already says the market is closed or the legacy bucket shock has already cooled below threshold.

Files updated:

• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `SQL_PUSH_CANDIDATES` now carries current hot state alongside legacy inbox rows:
  - `hot_candidate_state`
  - `hot_quote_ts`
  - `hot_threshold_value`
  - `hot_market_status`
• `dispatch_push_alerts(...)` now suppresses only `watchlist` pushes when:
  - hot says `closed`
  - hot says `below_threshold` and the hot quote is newer than the legacy bucket
• suppression is logged with explicit reasons:
  - `hot_closed`
  - `hot_below_threshold_reverted`

Why this matters:

• this directly targets the two mismatch families we just isolated:
  - closed markets still echoed by legacy bucket state
  - stale legacy bucket shocks after hot has already cooled below threshold
• the change is conservative: it does not alter inbox reads, mover reads, ranking, or the main legacy delivery source
• it reduces the chance of obviously stale push alerts without forcing a hot-first delivery cutover


# Delivery Mismatch Lifecycle Context (2026-04-27)

Extended the delivery mismatch report one level deeper by attaching current market lifecycle state to the recurring mismatch market rollups.

Files updated:

• `scripts/ops/delivery_parity_report.py`
• `docs/delivery_parity_latest.md`
• `progress.md`
• `architecture.md`

What changed:

• top mismatch market rows now include:
  - current lifecycle state
  - current hot candidate states
  - current watchlist row count
• regenerated the 168-hour report from live Railway/Supabase data

Current finding:

• the main recurring mismatch markets split into two useful groups:
  - `closed`: `1919417`, `2007076`
  - `active` but currently `below_threshold`: `1919421`, `1919425`
• this confirms that the mismatch is partly historical bucket shock behavior and partly current below-threshold semantics, not a missing telemetry problem

Why this matters:

• the next safe engineering step is not hot-first delivery
• the next safe engineering step is a conservative stale/shock hardening plan:
  - suppress or age out legacy bucket shocks when hot now says `closed`
  - treat active-but-below-threshold legacy-only rows as candidates for tighter recency/bucket-age filtering
• runtime delivery remains unchanged in this step


# Delivery Mismatch Market Rollup (2026-04-27)

Extended the delivery parity report so mismatch diagnostics identify the repeat market ids behind `hot_only` and `legacy_only`, not just aggregate classifications.

Files updated:

• `scripts/ops/delivery_parity_report.py`
• `docs/delivery_parity_latest.md`
• `progress.md`
• `architecture.md`

What changed:

• added `Top Hot-Only Mismatch Markets`
• added `Top Legacy-Only Mismatch Markets`
• each row now includes:
  - `market_id`
  - classification
  - sample count
  - max absolute delta
  - threshold
  - latest seen timestamp
  - question text
• regenerated the 168-hour report from live Railway/Supabase data

Current finding:

• the mismatch is not random across the universe
• recent examples concentrate around a small cluster:
  - `1919417`
  - `1919421`
  - `1919425`
  - `2007076`
• those markets appear in both directions:
  - `legacy_stale_bucket` when hot leads the legacy bucket
  - `legacy_shock_reverted` when legacy keeps surfacing a bucket shock after hot cools below threshold

Why this matters:

• the next delivery task should target the stale-bucket / shock-reversion semantics
• hot-first delivery remains blocked, but the blocker is now narrow enough to investigate by market lifecycle and bucket timing
• runtime delivery semantics remain unchanged


# Delivery Parity Decision Report Refresh (2026-04-27)

Refreshed the delivery parity evidence and tightened the report script so the delivery decision is based on the full selected window, not only recent examples.

Files updated:

• `scripts/ops/delivery_parity_report.py`
• `docs/delivery_parity_latest.md`
• `progress.md`
• `architecture.md`

What changed:

• regenerated `docs/delivery_parity_latest.md` from live `bot.delivery_parity_log` data for the latest 168-hour window
• changed `scripts/ops/delivery_parity_report.py` so `Classification Totals` aggregate across the whole report window
• added a `Decision Readout` section to the report
• current 168-hour result:
  - `non_quiet_samples = 999`
  - `classified_non_quiet_samples = 993`
  - `hot_only_samples = 105`
  - `legacy_only_samples = 488`
  - main classified reason: `legacy_shock_reverted`

Decision:

• keep legacy push delivery as primary for now
• do not enable hot-first delivery yet
• continue using hot diagnostics and hybrid/fallback analysis until `legacy_only` no longer materially dominates

Why this matters:

• mismatch diagnostics are now decision-grade enough to say “not yet” with evidence
• the blocker is semantic/product parity, not lack of telemetry
• delivery semantics remain unchanged in runtime


# Telegram Bot Intent Page Pass (2026-04-27)

Strengthened `/telegram-bot` as the primary search-intent page for users looking for a Polymarket Telegram bot.

Files updated:

• `api/main.py`
• `progress.md`
• `architecture.md`

What changed:

• updated English title, description, H1, intro, and feature rows around the exact `Polymarket Telegram bot` intent
• added a dedicated command-flow block covering:
  - `/start`
  - `/movers`
  - `/watchlist`
  - `/threshold`
  - `/inbox`
• added a FAQ item for `best Polymarket Telegram bot` intent
• enabled the live signal board on `/telegram-bot` with Telegram-specific copy:
  - `Markets you can track right now`
  - `Track in Telegram`

Why this matters:

• GSC already shows `/telegram-bot` impressions for bot-intent queries, but CTR is still thin
• the page now explains the actual bot workflow instead of only describing the product at a high level
• live rows make the page feel like a working product surface and give visitors an immediate action path into Telegram
• this is additive and does not change bot behavior, delivery semantics, ingest, or database schema


# Signals Page Board Promotion (2026-04-27)

Promoted the live signal board from a supporting section into a primary product surface on `/signals`.

Files updated:

• `api/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `/signals` now renders the live signal board inside the first hero card, immediately after the primary CTA and trust notes
• `/top-movers` and `/analytics` keep the board below the generic preview section
• live rows now highlight the first quality pill and show a `1m` tape cue when the short-window delta is non-zero

Why this matters:

• `/signals` should feel like a live product surface, not just an SEO explainer
• the page now puts real movement, quality gates, and Telegram tracking closer to the first viewport
• this keeps the same data path and tracking behavior while improving the perceived value of the page


# Signals Page Live Board (2026-04-27)

Turned the quality-context work into a real site surface instead of keeping it only inside the homepage preview.

Files updated:

• `api/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `/signals`, `/top-movers`, and `/analytics` can now server-render a live signal board
• the live board uses `/api/live-movers-preview` data through `fetch_live_movers_preview(...)`
• each row shows:
  - market question
  - mid previous/current
  - probability-point delta
  - quality context
  - `Open market`
  - `Track in Telegram`
• clicks inside the board are tracked as:
  - `market_click`
  - `tg_click`
  with placement `seo_live_signal_board`

Why this matters:

• the site now has a stronger live analytics surface for search-intent pages
• `/signals` can show real market movement immediately, not only describe what the bot does
• server-rendering keeps the content visible to users and crawlers even before client JS runs


# Homepage Live Signal Quality Context (2026-04-27)

Started the week with a small analytics-quality improvement on the public live preview and the `Pulse` movers surface.

Files updated:

• `api/main.py`
• `api/web/index.en.html`
• `api/web/index.ru.html`
• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `/api/live-movers-preview` now returns signal-quality context for hot rows:
  - `source`
  - `signal_quality`
  - `freshness_seconds`
  - `liquidity`
  - `spread`
• legacy fallback rows are explicitly marked as `legacy_fallback`
• homepage live mover rows now render compact quality chips:
  - live quality gate
  - quote freshness
  - liquidity
  - spread
• `/movers` now also prints a compact `quality:` line for hot rows:
  - live quality gate
  - quote age
  - liquidity
  - spread

Why this matters:

• the site should increasingly behave like a live analytics surface, not only a marketing page
• showing why a mover passed quality gates makes the signal feel more trustworthy
• this is additive and does not change ranking, delivery semantics, or the hot ingest contract


# Trader Services Parked On Railway Hobby (2026-04-23)

Parked the non-core trader services on Railway so the current Hobby footprint matches the product focus and cost posture.

Files updated:

• `progress.md`
• `architecture.md`

What changed:

• `trader-bot` current deployment was removed in Railway
• `trade-worker` current deployment was removed in Railway
• both services now have no active deployment attached
• the core runtime remained unchanged:
  - `site`
  - `bot`
  - `ingest`

Why this matters:

• the current critical path is still `Pulse`, not `Trader`
• keeping inactive trader services live on Hobby adds avoidable operational and cost noise
• parking them now makes the runtime posture match the current plan:
  - keep `site`, `bot`, `ingest` always-on
  - keep `trader-bot` and `trade-worker` parked-by-default until alpha work resumes


# Inbox Empty Recovery (2026-04-21)

Added one more small `Pulse` UX improvement so an actually empty watchlist no longer reads as a generic empty inbox state.

Files updated:

• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `send_inbox_view(...)` now checks `watchlist_count == 0` before entering the normal inbox read path
• if the user is not tracking any markets yet, the bot now says so explicitly instead of falling into generic “no alerts / no deltas” copy
• the empty state points to the next useful move:
  - add one live market first
  - then return to Inbox for thresholded alerts
• the screen still keeps the normal inline recovery/navigation buttons

Why this matters:

• an empty watchlist and a quiet inbox are not the same product state
• treating them as the same makes the bot feel vague for new and reactivated users
• this keeps the first-return logic honest without changing delivery semantics or the data layer


# Watchlist Empty Recovery (2026-04-20)

Added another small `Pulse` UX improvement so a truly empty watchlist no longer looks like a quiet or broken live window.

Files updated:

• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `send_watchlist_view(...)` now checks for `watchlist_count == 0` before running the normal live read path
• if the list is empty, the bot now says so explicitly instead of falling through into generic “no live changes” logic
• the empty state points to the next useful action:
  - add one live market first
  - then come back for live deltas
• the screen also renders the normal inline recovery/navigation buttons

Why this matters:

• an empty watchlist and a quiet live window are different product states
• treating them the same makes the bot feel confusing for new or returning users
• this keeps the first-return flow honest without touching any SQL, alerting, or delivery behavior


# Picker Empty-State Recovery (2026-04-16)

Added another small `Pulse` UX improvement so the watchlist picker does not dead-end when the current live filter has no candidates.

Files updated:

• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `send_watchlist_picker(...)` no longer returns a text-only empty state when the chosen live filter has no candidates
• the picker empty state now explains the best next step more explicitly:
  - refresh the picker
  - check `Top movers`
  - or add a specific market manually via `/watchlist_add <market_id|slug>`
• the empty state now also renders inline recovery buttons:
  - `Refresh list`
  - `Top movers`
  - `Watchlist`
  - `Inbox`

Why this matters:

• the picker is one of the main first-value paths in `Pulse`
• when a live filter temporarily dries up, a text-only response feels like the flow is broken
• this keeps the user inside the normal navigation loop and makes the next action obvious without changing any data or delivery behavior


# Watchlist Empty-State Recovery (2026-04-15)

Added one more small `Pulse` UX improvement so cleanup and review flows do not dead-end when the list is already empty or when the user opens manual removal without an argument.

Files updated:

• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `/watchlist_list` empty state now explains the next useful move instead of only showing a raw command format
• that empty state now also shows inline navigation buttons:
  - `Add market`
  - `Watchlist`
  - `Inbox`
  - `Top movers`
• `/watchlist_remove` without an argument now keeps the existing usage hint but also shows the same inline action path, so the user can recover without typing more commands first

Why this matters:

• the review/cleanup loop already got stronger, but an empty list still felt like a dead end
• this change keeps users inside the normal button-driven flow instead of pushing them back into command memorization
• it is fully additive and does not touch any SQL, delivery semantics, or runtime data flow


# Legacy Push Candidate Budget Hardening (2026-04-15)

Applied one more safe reliability pass to the legacy push delivery path without changing delivery semantics.

Files updated:

• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `dispatch_push_alerts()` now gives the legacy candidate query a more realistic single-attempt budget:
  - `PUSH_CANDIDATE_STATEMENT_TIMEOUT_MS = 15000`
  - `PUSH_CANDIDATE_TIMEOUT_SECONDS = 22`
  - `PUSH_CANDIDATE_RETRY_ATTEMPTS = 1`
• candidate fetch no longer uses the previous retry pattern that could spend time on multiple doomed attempts and then still die at the outer async timeout
• timeout/failure logs now include the actual candidate-query budgets, so future runtime diagnosis can separate:
  - statement budget issues
  - outer timeout issues
  - retry posture issues

Why this matters:

• read-only `EXPLAIN ANALYZE` already showed the legacy candidate path is not a cheap query
• for a heavy deterministic view, “retry quickly with the same short statement timeout” is often worse than “one realistic attempt”
• this change is meant to reduce avoidable `TimeoutError` cascades while the delivery surface still stays on legacy

Early runtime signal:

• after the deploy, fresh `bot` logs showed multiple parity cycles in a row without:
  - `push_loop iteration failed`
  - `TimeoutError`
  - `push_loop candidates skipped`
• this is only an early signal, not a final verdict, but it is directionally good

What did not change:

• no delivery semantics change
• no hot-first cutover
• no alert ranking change
• no SQL surface change


# Delivery Mismatch Diagnostics Upgrade (2026-04-15)

Upgraded the delivery parity instrumentation so non-quiet windows can carry mismatch reasons and concrete example rows, not just raw counts.

Files updated:

• `bot/main.py`
• `scripts/ops/delivery_parity_report.py`
• `docs/delivery_parity_latest.md`
• `progress.md`
• `architecture.md`

What changed:

• `dispatch_push_alerts()` still keeps parity best-effort and non-fatal
• but for non-quiet windows it now also tries a second best-effort detail query that captures:
  - top `hot_only` examples
  - top `legacy_only` examples
  - classification counts
• detail is written into the existing `bot.delivery_parity_log.payload` JSON field, so no schema change was needed
• current classification vocabulary is:
  - `legacy_shock_reverted`
  - `hot_below_threshold`
  - `legacy_stale_bucket`
  - `hot_missing_quote`
  - `unknown`
• the parity report now reads those payload details and renders:
  - classification totals
  - recent hot-only examples
  - recent legacy-only examples
• the report now also separates:
  - `classified_non_quiet_samples`
  - `unclassified_non_quiet_samples`
  so we can tell how much of the parity window still predates the richer instrumentation

Why this matters:

• the delivery question is no longer blocked on “do we have any divergence?”
• we already know divergence exists
• the real blocker is “what kind of divergence is it?”
• this upgrade makes the next non-quiet window much more useful because it will explain the mismatch instead of just counting it

Current limitation:

• the production snapshot taken immediately after this upgrade still showed a quiet current window
• so the richer sections in `docs/delivery_parity_latest.md` are structurally ready, but they still need the next fresh non-quiet sample written by the upgraded bot loop

First useful outcome:

• the next fresh non-quiet sample arrived after deployment
• it showed:
  - `hot_only = 1`
  - `legacy_only = 0`
  - market `1919425`
  - classification `legacy_stale_bucket`
• that is our first concrete evidence that at least some `hot_only` divergence is a legitimate hot freshness lead, not just unexplained noise
• a few fresh cycles later, the same market cluster also produced the first classified `legacy_only` case:
  - markets `1919425` and `1919417`
  - classification `legacy_shock_reverted`
• this makes the mismatch story much clearer:
  - `hot_only` is now explainable as current live freshness lead
  - `legacy_only` is now explainable as bucket shock persistence after live reversion
• the latest 7-day refresh now shows this is no longer a small-sample interpretation:
  - `classified_non_quiet_samples = 987`
  - `hot_only_samples = 215`
  - `legacy_only_samples = 511`
  - `both_non_quiet_samples = 464`
• this strengthens the current decision:
  - push delivery still should not move to blind hot-first
  - if we continue delivery work, it should be via hybrid/fallback refinement rather than outright replacement


# Telegram Bot CTR Pass (2026-04-15)

Made a focused CTR/SEO pass on the `/telegram-bot` intent page after GSC showed it had the highest impression count among our search landing pages but still produced zero clicks.

Files updated:

• `api/main.py`
• `progress.md`
• `architecture.md`

What changed:

• strengthened `/telegram-bot` English title, description, `h1`, and intro around the exact search intent:
  - `Polymarket Telegram Bot`
  - live movers
  - watchlist alerts
  - low-noise Telegram flow
• tightened the comparison / bridge copy so the page explains the value more directly in Telegram-first terms
• added one more FAQ entry that answers what the bot actually does for Polymarket users
• parameterized SEO-page URLs now emit `noindex,follow`
  - this is a soft duplicate-control guard for paths such as:
    - `?lang=en`
    - tracking / placement query variants

Why this matters:

• GSC now clearly shows `/telegram-bot` as the strongest search-impression page in the project
• the problem is no longer “Google does not see us there”
• the problem is “Google sees us there, but the snippet is not earning clicks yet”
• duplicate-ish query-param variants were also showing up in GSC, so letting canonical pages stay indexable while parameterized variants become `noindex` is the safer posture

Practical effect:

• the `/telegram-bot` page is now a cleaner bot-intent landing page
• new crawls of parameterized SEO-page variants should be less likely to compete with canonical paths in the index

# Delivery Decision Pass (2026-04-15)

Took the first real delivery decision pass using a full week of parity history instead of waiting for one lucky non-quiet window.

Files updated:

• `docs/delivery_decision_pass_2026-04-15.md`
• `progress.md`
• `architecture.md`

What we concluded:

• push delivery should **not** move to hot-first yet
• this is no longer because of missing data
• it is because we now have enough data to see real semantic divergence:
  - meaningful `hot_only`
  - meaningful `legacy_only`
  - some clean overlap windows too
• the current blocker is therefore:
  - not “wait for more signal”
  - but “understand mismatched signal quality”

Practical consequence:

• keep read surfaces hot-first
• keep push delivery on legacy for now
• next step should be richer shadow diagnostics on non-quiet parity windows, not a blind cutover

# Weekly Status Checkpoint (2026-04-15)

Took a fresh runtime and data-layer checkpoint nearly a week after the telemetry and push-loop fixes so we could separate real recovery from wishful thinking.

Files updated:

• `docs/weekly_status_2026-04-15.md`
• `progress.md`
• `architecture.md`

What we confirmed:

• core Railway services are healthy:
  - `site` `SUCCESS`
  - `bot` `SUCCESS`
  - `ingest` `SUCCESS`
• the hot layer is healthy and populated:
  - registry / quotes fresh at roughly `~60s`
  - movers `1m` and `5m` populated
  - watchlist and alert candidate hot surfaces populated
• the site telemetry path fix is now genuinely working in production for new rows
• internal `page_view` traffic recovered from the `2026-04-07` low point, but the top-of-funnel is still very small
• `tg_click` volume is still extremely thin over the last 7 days
• delivery parity is no longer blocked by quiet windows:
  - we now have meaningful `hot_only`
  - meaningful `legacy_only`
  - and overlap windows too
• push-loop hardening reduced blast radius, but intermittent legacy-query `statement timeout` windows still exist

Practical consequence:

• we are no longer waiting for "any non-quiet sample" to discuss delivery
• the delivery question is now a real semantic/parity decision with reliability constraints, not a data-absence problem
• growth-wise, the bigger constraint still looks like tiny acquisition volume rather than a fresh full-site outage

# Site Event Route Hardening (2026-04-10)

Tightened the `/api/events` write path after confirming that `app.site_events.path` was still collapsing to `/api/events` in real runtime samples even though `details.page_path` and `details.page_url` were already reaching the database.

Files updated:

• `api/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `site_event(...)` now resolves the page path explicitly at the route boundary
• that resolved path is passed into `log_site_event(...)` as a dedicated `path_override`
• `log_site_event(...)` now prefers the explicit override before falling back to generic resolution logic

Why this matters:

• the database itself is not rewriting the path column
• direct inserts into `app.site_events` preserve custom paths correctly
• this means the ambiguity lived in the runtime `/api/events` path, not in the table schema
• route-level override removes that ambiguity and gives us a more deterministic telemetry write path

Practical effect:

• new `page_view` and other site events coming through `/api/events` should persist the real page path more reliably
• this is a safe hardening step before we do any larger telemetry cleanup or reporting changes
• final production verification confirmed the fix only after deploying with the monorepo-aware command:
  - `railway up -s site --path-as-root api`
• a plain `railway redeploy --service site` was not sufficient for this source change because it reused the latest service snapshot rather than pushing the updated local source

# Site Event Path Recovery (2026-04-10)

Recovered real page-context persistence for `app.site_events` without changing the site event taxonomy or rewriting every frontend tracker.

Files updated:

• `api/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `/api/events` no longer writes `request.url.path` blindly into `app.site_events.path`
• event trackers on the main public pages now explicitly attach:
  - `page_path`
  - `page_url`
• server-side event path resolution now prefers:
  - `details.page_path`
  - `details.page_url`
  - `Referer`
  - only then the event endpoint path itself

Why this matters:

• the current telemetry surface was still capturing placements, but page-level diagnosis was degraded because every `page_view` looked like `/api/events`
• this fix preserves the existing event contract while making `app.site_events.path` useful again for runtime and growth analysis

Practical effect:

• future `page_view` rows should once again distinguish `/`, `/telegram-bot`, `/signals`, and other entry pages instead of collapsing into one event endpoint path

# Push Loop Hardening (2026-04-10)

Applied a safe hardening pass to the bot push loop after confirming that recent failures were coming from the legacy delivery SQL path plus conflicting timeout budgets.

Files updated:

• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• DB helpers now allow call-site override of:
  - retry attempts
  - statement timeout budget
• `dispatch_push_alerts()` no longer treats parity as a fatal prerequisite:
  - parity timeout/failure now logs and skips
  - the rest of the push loop can continue
• parity log writes are also non-fatal
• push candidate fetch now uses a more realistic outer timeout budget that fits the helper's retry behavior instead of cutting it off too aggressively
• individual Telegram send failures now skip only that recipient instead of risking the whole iteration

Why this matters:

• the previous loop shape could fail the entire push iteration because:
  - the DB helper had its own retry/statement-timeout logic
  - but `asyncio.wait_for(...)` outside it was shorter than the realistic full retry path
• this hardening does not change delivery semantics
• it simply reduces the blast radius of transient slow windows on the legacy push path

Practical effect:

• parity is now diagnostic rather than a single point of failure
• push delivery should degrade more gracefully under slow DB windows while we continue evaluating the later hot-first delivery cutover

# Traffic Dip Diagnostic (2026-04-10)

Checked the recent traffic drop from our side before touching any product or growth surfaces.

Updated artifacts:

• `docs/traffic_dip_diagnostic_2026-04-10.md`
• `progress.md`
• `architecture.md`

What we confirmed:

• there is no fresh broad site outage pattern this week:
  - homepage returns `200`
  - site logs do not show a matching cluster of `5xx` / timeout failures
  - ingest logs are also clean over the same window
• the previous weekend outage caused by the expired Railway plan is still the clearest hard uptime event in the recent period
• on our side, the strongest current reliability issue is now the bot push loop:
  - repeated `push_loop iteration failed`
  - repeated `TimeoutError`
  - observed across `2026-04-07` through `2026-04-10`
• internal telemetry in `app.site_events` shows a real low-traffic week, with a sharp low point on `2026-04-07`
• however, the site telemetry shape is also weaker than it should be:
  - `event_type='page_view'` rows currently store `path='/api/events'`
  - real page context survives mainly in `details.placement`
  - this makes path-level diagnosis much noisier than it should be
• current samples still show live placements firing:
  - `page`
  - `hero_panel`
  - `proof_bridge`
  - `seo_*`
  so this is not a total tracking blackout
• manual crawl smoke is not showing an obvious Google block:
  - homepage `200` for a browser UA
  - homepage `200` for `Googlebot`
  - `robots.txt` also returns `200` for `Googlebot`

Operational conclusion:

• the main issue on our side does not currently look like a fresh whole-site uptime failure
• the two things worth taking seriously are:
  - bot push-loop instability hurting return/retention traffic
  - weak page attribution in `app.site_events`, which makes diagnosis less trustworthy than it should be
• deeper push-loop diagnosis identified a concrete technical cause:
  - repeated `statement_timeout` on the legacy delivery query path
  - then a larger `TimeoutError` at the outer async wrapper level
• current `dispatch_push_alerts()` still pays the historical-bucket cost of `bot.watchlist_snapshot_latest` on every loop through `bot.alerts_inbox_latest`
• read-only `EXPLAIN ANALYZE` confirmed that the expensive side is the legacy watchlist branch, not the hot candidate table
• the traffic drop may therefore be a mix of:
  - the previous weekend Railway outage
  - very small top-of-funnel volume
  - degraded bot reliability on recent days
  - plus whatever GSC / GA4 later confirm on the acquisition side

# Worker Follow-Up: Railway Ops + Legacy Compatibility + Threshold UX (2026-04-06)

Consolidated three safe worker follow-ups into repo-owned docs plus one additive bot UX improvement.

Files updated:

• `docs/railway_hobby_ops_runbook_2026-04-06.md`
• `docs/legacy_watchlist_compatibility_plan_2026-04-06.md`
• `bot/main.py`
• `progress.md`
• `architecture.md`

What we fixed or clarified:

• added a local Railway Hobby ops runbook based on read-only CLI checks
• documented current production service posture separately from recommended Hobby posture:
  - always-on: `site`, `bot`, `ingest`
  - park-by-default: `trader-bot`, `trade-worker` unless alpha is active
• mapped the still-live ingest dependency on:
  - `public.user_watchlist`
  - `public.user_positions`
• documented the smallest safe compatibility-first path to retire `public.watchlist` / `public.watchlist_markets` later without breaking ingest
• improved threshold explanation in the bot without changing behavior:
  - `/threshold`
  - `menu:threshold`
  - quiet `/inbox` below-threshold state

Practical effect:

• we now have a stable local ops reference for Railway Hobby instead of relying on memory
• the next watchlist cleanup step is better framed as compatibility work, not delete-first cleanup
• users now get a clearer explanation that:
  - Inbox alerts only when `abs(delta) >= threshold`
  - `0.03` means `3 percentage points`
  - Watchlist can move while Inbox stays empty

# Delivery Parity Report Hardening (2026-04-06)

Made the delivery parity report runnable from the current local shell posture instead of assuming `psycopg` is always installed.

Files updated:

• `scripts/ops/delivery_parity_report.py`
• `progress.md`
• `architecture.md`

What changed:

• the report now prefers `psycopg` but falls back to `psycopg2` if needed
• this matches the repo reality better:
  - `bot` / `api` envs use `psycopg`
  - `ingest` requirements still expose `psycopg2-binary`
• the script can now be re-run more safely through local shells or `railway run --service bot ...`

Why this matters:

• the main delivery decision path depends on fast parity snapshots
• we should not block that decision on local package drift

# Pulse Cleanup UX Clarification (2026-04-06)

Added one small additive UX clarification around watchlist cleanup so stale-market handling is easier to understand without changing behavior.

Files updated:

• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `/help` now frames:
  - `/watchlist_list` as review + cleanup
  - `/watchlist_remove` as manual cleanup
• `/watchlist_remove` without args now points users to `/watchlist_list` for one-tap Remove buttons on `closed` / `date_passed_active` rows
• `/watchlist_remove` miss/empty result now points users back to `Review list` inline remove flow instead of only saying “refresh”

Why this matters:

• it makes the cleanup path more discoverable
• it matches the real product shape after we added inline Remove actions to `Review list`
• it reduces the chance that users think stale rows require memorizing manual commands first

# Pulse Plan / Limits Cleanup Hint (2026-04-06)

Added one more small UX clarification so slot pressure is easier to understand on FREE and cleanup is easier to discover.

Files updated:

• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `plan_message_text()` now explicitly tells FREE users when `closed` markets are still occupying watchlist slots
• `/limits` now adds a cleanup hint pointing to `/watchlist_list` when closed rows are consuming capacity

Why this matters:

• this connects plan pressure to a concrete action
• it reduces the chance that users think they need PRO immediately when the real issue is stale slots

# Supabase Security Audit (2026-04-02)

Turned the Supabase security warnings into a reproducible audit plus remediation plan.

Files updated:

• `scripts/ops/supabase_public_security_audit.py`
• `docs/supabase_public_security_latest.md`
• `docs/supabase_security_remediation_plan_2026-04-02.md`
• `progress.md`
• `architecture.md`

What we confirmed:

• the failing GitHub ingest run was not caused by Node 20 deprecation
• real failure cause was:
  - statement timeout during batch upsert into `public.markets`
• Supabase warnings are not just cosmetic:
  - many `public` objects are granted to `anon` / `authenticated`
  - legacy `public` tables still have RLS disabled
• `public.watchlist_markets` is especially suspicious because it exists live in DB but is not clearly managed in current repo migrations

Practical effect:

• we now have a reproducible grant/rls snapshot instead of relying on the Supabase UI alone
• the next security step can be an additive revoke migration instead of ad-hoc dashboard edits

# Supabase Grant Hardening Phase 1 (2026-04-02)

Prepared the first narrow revoke migration for the highest-risk `public` relations.

Files updated:

• `db/migrations/014_public_surface_grant_hardening_phase1.sql`
• `progress.md`
• `architecture.md`

What this migration targets:

• legacy public watchlist / alert relations
• hot user-specific watchlist / alert tables
• legacy user-linked tables such as:
  - `public.user_positions`
  - `public.sent_alerts_log`
  - `public.sent_alerts_log_legacy`

What it does not touch:

• `service_role`
• `postgres`
• public analytical views like `top_movers_latest`
• schema names
• runtime read paths

Why this is the right first step:

• it closes the most dangerous user-specific public objects first
• it stays additive and reversible
• it avoids mixing permission hardening with schema refactors

# Supabase Grant Hardening Phase 2 (2026-04-06)

Closed the remaining analytical and hot-layer `public` relations for `anon` / `authenticated`.

Files updated:

• `db/migrations/015_public_surface_grant_hardening_phase2.sql`
• `docs/supabase_public_security_latest.md`
• `docs/supabase_security_remediation_plan_2026-04-02.md`
• `progress.md`
• `architecture.md`

What this migration targets:

• remaining analytical `public` views:
  - `top_movers_*`
  - `snapshot_health`
  - `global_bucket_latest`
  - `buckets_latest`
  - `analytics_core_health_latest`
• remaining hot-layer analytical tables:
  - `hot_market_registry_latest`
  - `hot_market_quotes_latest`
  - `hot_top_movers_1m`
  - `hot_top_movers_5m`
  - `hot_ingest_health_latest`
• legacy analytical tables/views still exposed through `public`:
  - `markets`
  - `market_snapshots`
  - `market_universe`
  - `live_markets_latest`
  - `user_watchlist`

Why this is the right second step:

• current repo runtime does not use client-side Supabase access
• these relations are consumed server-side only
• closing them removes the rest of the unnecessary `public` grant surface without changing schemas or app contracts

Verification:

• applied in production DB
• fresh security snapshot now shows:
  - `objects_granted_to_anon = 0`
  - `objects_granted_to_authenticated = 0`
• runtime smoke stayed healthy:
  - site API responded normally
  - bot polling stayed on `200 OK`
  - live ingest ticks kept writing hot surfaces

# Delivery Parity History (2026-04-06)

Upgraded the delivery decision path from transient log lines to persistent parity history plus a reusable report.

Files updated:

• `db/migrations/016_delivery_parity_log.sql`
• `bot/main.py`
• `scripts/ops/delivery_parity_report.py`
• `docs/delivery_parity_latest.md`
• `progress.md`
• `architecture.md`

What changed:

• new append-only table:
  - `bot.delivery_parity_log`
• `dispatch_push_alerts()` now persists each parity sample before reading legacy push candidates
• parity now stores:
  - `hot_ready_count`
  - `legacy_watchlist_count`
  - `overlap_count`
  - `hot_only_count`
  - `legacy_only_count`
  - top market ids / top abs deltas for hot vs legacy
• new ops report:
  - `scripts/ops/delivery_parity_report.py`
  - writes `docs/delivery_parity_latest.md`

Verification:

• migration `016` applied in production
• first sample inserted successfully
• current 24h snapshot now shows:
  - `samples_total = 1`
  - quiet window at sample time

Why this matters:

• the next hot-first delivery decision no longer depends on spotting a single prod log line
• we can now judge cutover readiness from accumulated windows, especially:
  - `hot_only_samples`
  - `legacy_only_samples`
  - `both_non_quiet_samples`

# Parallel Workstreams Map (2026-04-06)

Locked the current project split so the next days of work do not drift or collide.

Files updated:

• `docs/parallel_workstreams_2026-04-06.md`
• `progress.md`
• `architecture.md`

Main critical path:

• accumulate `bot.delivery_parity_log`
• wait for meaningful non-quiet windows
• use parity history to decide whether push delivery can move to hot-first

Safe parallel tracks:

• GSC / GA4 review
• Railway / Hobby ops hygiene
• small `Pulse` UX wins
• legacy DB drift cleanup planning
• SEO / intent-page polish

Why this matters:

• keeps the team moving while delivery evidence accumulates
• reduces the chance of accidental collisions between runtime migration and side work

# Review List Stale Marker (2026-03-31)

Made `Review list` more honest about markets that look dead to users but still remain `active` in source data.

Files updated:

• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `SQL_WATCHLIST_LIST` now carries:
  - `end_date`
  - additive `date_passed_active` marker
• `send_watchlist_list_view()` now surfaces this marker directly in the list:
  - `[ready · date_passed_active] ...`
  - `[partial · date_passed_active] ...`
• coverage summary now includes `date_passed_active`
• the guide now explains that these rows are not auto-cleaned because source data still marks them `active`
• `Review list` now gives explicit manual cleanup guidance:
  - use `/watchlist_remove <market_id|slug>`

Practical effect:

• users can distinguish:
  - truly `closed` markets removable by `Remove closed`
  - from stale-looking markets whose question date already passed but source still keeps them active
• this should reduce confusion around “I pressed Remove closed, but this one stayed”

# Review List Inline Remove (2026-03-31)

Added direct inline removal for problematic rows in `Review list`.

Files updated:

• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `send_watchlist_list_view()` now adds inline `Remove ...` buttons for up to 3 rows that are:
  - `closed`
  - or marked `date_passed_active`
• new callback flow:
  - `wlremove:<token>`
• inline removal refreshes `Review list` immediately after deletion

Practical effect:

• users no longer need to copy `market_id` into `/watchlist_remove` for the most obvious cleanup cases
• the stale/dead market cleanup loop is now much closer to one tap

# Push Loop Parity Logging (2026-03-31)

Added delivery parity visibility directly into the bot push loop.

Files updated:

• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `dispatch_push_alerts()` now logs a compact parity summary on every push iteration:
  - `hot_ready_count`
  - `legacy_watchlist_count`
  - `overlap_count`
• this uses a new additive SQL summary over:
  - `public.hot_alert_candidates_latest`
  - `bot.alerts_inbox_latest`

Practical effect:

• we no longer need to wait blind for the first non-quiet window
• the first meaningful hot-vs-legacy divergence will show up directly in prod bot logs
• delivery semantics are still unchanged

# Inbox Near-Miss Hint (2026-03-31)

Made quiet inbox states more informative when signals exist but remain below threshold.

Files updated:

• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• added hot-only `below_threshold` lookup for `/inbox`
• when `candidates_total > 0` and `over_threshold = 0`, the bot now shows the strongest near-miss:
  - question
  - current absolute delta
  - current threshold
• this keeps the inbox honest:
  - the user sees that movement exists
  - but the bot still refuses to spam because it stays below threshold

Smoke result:

• real quiet-user diagnostics returned:
  - `candidates_total = 2`
  - `over_threshold = 0`
• strongest near-miss resolved to:
  - `Will the price of Bitcoin be between $70,000 and $72,000 on April 3?`
  - `Δ 0.010`
  - `threshold 0.030`

Practical effect:

• quiet inbox now feels less like “nothing is happening”
• threshold tuning becomes much easier because the user sees the closest candidate immediately
• no alert delivery logic changed

# Homepage 1m Freshness Cue (2026-03-31)

Added a minimal `1m` tape cue to homepage live movers without changing the preview ranking or CTA hierarchy.

Files updated:

• `api/main.py`
• `api/web/index.en.html`
• `api/web/index.ru.html`
• `progress.md`
• `architecture.md`

What changed:

• `/api/live-movers-preview` now includes additive `delta_1m` when a row is present in `public.hot_top_movers_1m`
• homepage live mover rows now render a compact monospace `1m` chip only when `delta_1m != 0`
• the main mover ordering remains unchanged:
  - preview still ranks by the existing hot preview logic
  - `delta_yes` remains the primary movement number
• `1m` is used only as a freshness cue, not as a new ranked surface

Smoke result:

• local API smoke returned live rows with both:
  - `delta_yes`
  - `delta_1m`
• example output:
  - `1800064 ... delta_yes=-0.045 delta_1m=-0.075`
  - `1777503 ... delta_yes=0.03 delta_1m=0.05`

Practical effect:

• homepage preview now hints when a mover is also moving in the latest minute
• this strengthens the “live right now” feeling without turning the preview into a different product surface
• no read-path ranking, no hero CTA structure, and no waitlist logic changed

# Hot 1m Movers Published (2026-03-31)

Added the first true tape-style mover surface to the live worker without switching any new runtime reads.

Files updated:

• `ingest/live_main.py`
• `progress.md`
• `architecture.md`

What changed:

• `ingest/live_main.py` now publishes `public.hot_top_movers_1m`
• the 1m surface uses the previous live quote snapshot from `public.hot_market_quotes_latest` as its anchor
• this keeps the 1m mover surface genuinely live instead of trying to fake a minute view from 5m historical buckets
• current 1m gates:
  - `status = active`
  - two-sided quote required
  - liquidity `>= 1000`
  - spread `<= 0.25`
  - `HOT_MOVERS_1M_MIN_ABS_DELTA` default `0.002`

Smoke result:

• local live tick wrote:
  - `registry=423`
  - `quotes=423`
  - `two_sided=315`
  - `movers_1m=22`
  - `movers_5m=39`
  - `watchlist_hot=9`
  - `alerts_hot=9`

Practical effect:

• the hot layer now has both:
  - a tape-style `1m` mover surface
  - an action-style `5m` mover surface
• no bot or site read-path changed in this step
• this is additive publish-only work, which keeps the migration low-risk

# Hot vs Legacy Delivery Comparison (2026-03-31)

Captured the first explicit comparison pass for delivery semantics after the inbox hot-first migration.

Files updated:

• `scripts/compare_hot_vs_legacy_delivery.py`
• `docs/hot_vs_legacy_delivery_latest.md`
• `progress.md`
• `architecture.md`

What the report compares:

• `public.hot_alert_candidates_latest`
• `bot.alerts_inbox_latest`
• `bot.sent_alerts_log`

Current snapshot result:

• `hot_all_count = 9`
• `hot_ready_count = 0`
• `legacy_watchlist_count = 0`
• `legacy_all_count = 0`
• `sent_recent_count (24h) = 3`

Interpretation:

• the current live window is quiet on both hot and legacy inbox surfaces
• this confirms there is no obvious false divergence in the latest window
• but it is not yet enough evidence for a delivery cutover by itself
• `sent_alerts_log` still shows historical tail from earlier buckets, which is expected even when both current inbox surfaces are empty

What the current hot layer is saying:

• `hot_alert_candidates_latest` is not empty
• but the latest rows are currently:
  - `closed`
  - `below_threshold`
• that means the hot layer is already helping explain *why* inbox is quiet, even when there is nothing ready to send

Decision:

• do not move push delivery to hot-first yet
• keep using comparison passes until we capture at least one window with:
  - non-zero `hot_ready_count`
  - and a meaningful overlap or difference against current legacy delivery candidates

# Hot Inbox Migration Started (2026-03-31)

Moved the `Pulse` inbox toward the hot layer without touching the legacy push delivery loop.

Files updated:

• `ingest/live_main.py`
• `bot/main.py`
• `progress.md`
• `architecture.md`

What changed:

• `ingest/live_main.py` now publishes `public.hot_alert_candidates_latest`
• worker classification is derived from hot watchlist state plus per-user threshold:
  - `ready`
  - `below_threshold`
  - `stale_quotes`
  - `no_quotes`
  - `closed`
  - `filtered_liquidity`
  - `filtered_spread`
• current worker gates for hot alert candidates are:
  - threshold from `bot.user_settings` with default `0.03`
  - minimum liquidity `1000`
  - maximum spread `0.25`
• `bot/main.py` now reads `/inbox` hot-first:
  - watchlist alerts come from `public.hot_alert_candidates_latest` + `public.hot_watchlist_snapshot_latest`
  - portfolio alerts still come from legacy `bot.portfolio_alerts_latest`
  - full legacy fallback remains `bot.alerts_inbox_latest`
• inbox diagnostics are also hot-first now:
  - `below_threshold` watchlist candidates are visible to quiet-state messaging
  - portfolio diagnostics still use the legacy snapshot path

What intentionally did not change:

• push delivery still reads `bot.alerts_inbox_latest`
• `SQL_PUSH_CANDIDATES` is unchanged
• `sent_alerts_log` semantics are unchanged
• no Trader changes
• no legacy deletion

Smoke results:

• local live tick wrote:
  - `registry=393`
  - `quotes=393`
  - `two_sided=346`
  - `movers_5m=60`
  - `watchlist_hot=9`
  - `alerts_hot=9`
• hot diagnostics for a real user with quiet inbox returned:
  - `candidates_total=2`
  - `over_threshold=0`
• this confirms the next-step copy can now distinguish:
  - “no live deltas at all”
  - from
  - “signals exist but are below threshold”

Practical effect:

• `/inbox` now has a hot read path with safe fallback
• quiet inbox states are more truthful because they can see hot watchlist candidates before they cross threshold
• alert delivery itself is still insulated on the legacy path until we validate hot candidate behavior over repeated ticks

# Clickable Market Rows Pass (2026-03-27)

Made the homepage live mover rows action-oriented without changing the landing architecture, CTA hierarchy, or the current read path.

Files updated:

• `api/main.py`
• `api/web/index.en.html`
• `api/web/index.ru.html`
• `progress.md`
• `architecture.md`

What changed:

• `/api/live-movers-preview` now enriches homepage mover rows with additive handoff fields:
  - `slug`
  - `market_url` when a reliable Polymarket slug is present
  - `track_url` for Telegram handoff
• homepage live mover rows on both EN and RU templates now support action-oriented behavior:
  - row body opens Polymarket when `market_url` is available
  - secondary inline action opens Telegram tracking flow
• row actions stay visually subordinate to the existing CTA stack:
  - small chip-style actions only
  - hero panel CTA hierarchy remains intact
  - waitlist email form and POST logic remain untouched
• site analytics now accept additive `market_click` events for Polymarket handoff measurement

What intentionally did not change:

• no data-layer migration work
• no hot-layer read-path change
• no bot contract change
• no Trader changes
• no hero metrics / hero right panel rewrite
• no unrelated SEO rewrite

Intent-page limitation confirmed:

• current intent/SEO pages in `api/main.py` render generic feature preview cards, not market-specific rows
• because there is no real market object on those surfaces today, no per-market Polymarket link was invented there
• market-specific clickable actions were added only where the site already has real market data:
  - homepage live movers preview

Practical effect:

• homepage movers are no longer passive proof-only rows
• users now have a direct handoff path from live signal proof to:
  - Polymarket market page
  - Telegram tracking flow
• `site_track_<market_id>` is now a real product handoff, not attribution-only noise:
  - `/start` in `bot/main.py` now detects the payload
  - tries to add that market to watchlist immediately
  - keeps the existing add/recovery logic and attribution logging
• this closes the biggest semantics gap in the clickable rows pass:
  - `Open on Polymarket` opens the market
  - `Track in Telegram` now actually attempts to track that exact market
• follow-up production fix:
  - Polymarket market rows must open `/market/<slug>`, not `/event/<slug>`
  - some market slugs 404 under `/event/...` even though they resolve correctly under `/market/...`
• started the next hot-layer migration step for `watchlist`:
  - `ingest/live_main.py` now publishes `public.hot_watchlist_snapshot_latest`
  - `bot/main.py` now reads `watchlist` snapshot hot-first with legacy fallback
• migration boundary stays safe:
  - only the primary live snapshot read is switched
  - fallback windows, diagnostics, and inbox remain on the existing legacy/runtime path for now

---

# Hot Data Contract V1 Schema Scaffold Drafted (2026-03-27)

Prepared the additive schema scaffold for Hot Data Contract V1 without switching any runtime reads.

Files updated:

• `db/migrations/013_hot_data_contract_v1_scaffold.sql`
• `progress.md`
• `architecture.md`

What was added in the migration draft:

• new hot latest tables in `public`:
  - `hot_market_registry_latest`
  - `hot_market_quotes_latest`
  - `hot_top_movers_1m`
  - `hot_top_movers_5m`
  - `hot_watchlist_snapshot_latest`
  - `hot_alert_candidates_latest`
• new read-only operational view:
  - `hot_ingest_health_latest`
• supporting additive schema only:
  - indexes for future live read patterns
  - comments clarifying no-cutover semantics
  - a narrow `public.hot_touch_updated_at()` trigger helper for registry row refreshes
  - basic sanity checks for probability, spread, liquidity, and threshold ranges

Surface field set now scaffolded:

• `public.hot_market_registry_latest`
  - `market_id`, `slug`, `question`, `status`, `end_date`, `event_title`, `category`, `token_yes`, `token_no`, `updated_at`, `source_ts`
• `public.hot_market_quotes_latest`
  - `market_id`, `bid_yes`, `ask_yes`, `mid_yes`, `liquidity`, `spread`, `quote_ts`, `ingested_at`, `freshness_seconds`, `has_two_sided_quote`
• `public.hot_top_movers_1m`
  - `market_id`, `question`, `slug`, `prev_mid`, `current_mid`, `delta_mid`, `delta_abs`, `liquidity`, `spread`, `score`, `window_start`, `window_end`, `quote_ts`, `ingested_at`
• `public.hot_top_movers_5m`
  - `market_id`, `question`, `slug`, `prev_mid`, `current_mid`, `delta_mid`, `delta_abs`, `liquidity`, `spread`, `score`, `window_start`, `window_end`, `quote_ts`, `ingested_at`
• `public.hot_watchlist_snapshot_latest`
  - `app_user_id`, `market_id`, `question`, `slug`, `status`, `mid_current`, `mid_prev_5m`, `delta_mid`, `liquidity`, `spread`, `live_state`, `quote_ts`, `ingested_at`
• `public.hot_alert_candidates_latest`
  - `app_user_id`, `market_id`, `question`, `delta_mid`, `delta_abs`, `threshold_value`, `liquidity`, `spread`, `quote_ts`, `ingested_at`, `candidate_state`
• `public.hot_ingest_health_latest`
  - `registry_age_seconds`, `quotes_age_seconds`, `active_market_count`, `two_sided_quote_count`, `hot_movers_1m_count`, `hot_movers_5m_count`, `updated_at`

What intentionally remains for the worker layer:

• live cadence and ownership:
  - long-running hot worker still needs to own refresh timing and full-table upsert/delete semantics
• hot registry publishing:
  - fetch Gamma metadata and populate `hot_market_registry_latest`
• hot quote publishing:
  - fetch CLOB quotes and populate `hot_market_quotes_latest`
  - maintain `freshness_seconds` and `has_two_sided_quote`
• mover computation:
  - calculate 1m / 5m windows
  - enforce freshness, liquidity, and spread gates
  - compute `score`
  - publish + prune `hot_top_movers_*`
• watchlist and alert derivation:
  - join against `bot.watchlist` / `bot.user_settings`
  - materialize `hot_watchlist_snapshot_latest`
  - materialize `hot_alert_candidates_latest`
• runtime migration:
  - homepage preview, `/movers`, watchlist, inbox, and alert delivery still read legacy surfaces until later additive cutovers

Initial worker publish semantics now clarified:

• global latest-state tables:
  - `hot_market_registry_latest`
  - `hot_market_quotes_latest`
  - worker should treat these as latest snapshots: upsert current rows and prune rows that fall out of hot coverage
• global movers windows:
  - `hot_top_movers_1m`
  - `hot_top_movers_5m`
  - worker should rebuild/prune these as scored window outputs, not append history into them
• per-user derived latest-state tables:
  - `hot_watchlist_snapshot_latest`
  - `hot_alert_candidates_latest`
  - worker should upsert current per-user rows and prune rows that disappear because of membership, status, freshness, or gating changes

Initial worker gate shape now clarified:

• quotes:
  - probabilities and spread stay in the bounded `0..1` domain
  - liquidity stays non-negative
  - `has_two_sided_quote` is the primary quality flag
• movers:
  - require active market metadata, current quote, previous comparison point, and acceptable quote quality
• watchlist snapshot:
  - `live_state` remains the user-readable readiness contract
• alert candidates:
  - table stays pre-delivery
  - worker still owns candidate classification before any bot/inbox cutover

Candidate-state vocabulary is now locked for V1 scaffold:

• `hot_alert_candidates_latest.candidate_state`
  - `ready`
  - `below_threshold`
  - `stale_quotes`
  - `no_quotes`
  - `closed`
  - `date_passed_active`
  - `filtered_spread`
  - `filtered_liquidity`

Initial V1 worker publish contract now clarified:

• recommended write order:
  1. `hot_market_registry_latest`
  2. `hot_market_quotes_latest`
  3. `hot_top_movers_1m`
  4. `hot_top_movers_5m`
  5. `hot_watchlist_snapshot_latest`
  6. `hot_alert_candidates_latest`
  7. `hot_ingest_health_latest` stays derived-only
• rationale:
  - downstream hot surfaces should always derive from the same registry/quote pass
  - movers should exist before per-user watchlist and alert derivations
  - health should observe the tables, not be written independently

Initial compare and rollback shape now clarified:

• first compare target:
  - `hot_top_movers_5m` vs `public.top_movers_latest`
• follow-up compare targets:
  - `hot_watchlist_snapshot_latest` vs `bot.watchlist_snapshot_latest`
  - `hot_alert_candidates_latest` vs `bot.alerts_inbox_latest`
• rollback rule:
  - keep legacy readers untouched and flip one runtime surface at a time only after side-by-side output checks

Migration draft is now closer to ready-to-apply shape:

• additive only
• wrapped in a single transaction
• idempotent object creation where practical (`if not exists`, `create or replace`)
• no legacy object drops
• no runtime reader rewiring
• V1 state vocabulary is pinned in schema instead of left implicit

Why this is the safe next step:

• the schema contract now exists before any live read switch
• legacy `public.*` and `bot.*` compatibility surfaces remain untouched
• the next implementation step can focus on worker writes and output comparison instead of schema negotiation

---

# Pulse/Site Read-Path Audit (2026-03-27)

Audited the current user-facing read paths in `Pulse`/site for:

• `public.top_movers_*`  
• `public.market_snapshots`  
• `bot.watchlist_snapshot_latest`  
• `bot.alerts_inbox_latest`

Current runtime readers:

• site homepage live preview:
  - `api/main.py` `/api/live-movers-preview`
  - reads `public.top_movers_latest`
  - reads `public.market_snapshots` for sparklines
• bot `/movers`:
  - `bot/main.py`
  - reads `public.top_movers_latest`
  - fallback reads `public.market_snapshots`
  - wider fallback reads `public.top_movers_1h`
• bot `/watchlist`:
  - `bot/main.py`
  - reads `bot.watchlist_snapshot_latest`
  - fallback + diagnostics read `public.market_snapshots`
• bot `/inbox`:
  - `bot/main.py`
  - reads `bot.alerts_inbox_latest`
• bot push delivery:
  - `bot/main.py`
  - reads `bot.alerts_inbox_latest`
• bot watchlist review + picker + post-add readiness:
  - `bot/main.py`
  - read `public.market_snapshots`
  - picker also reads `public.top_movers_latest` + `public.top_movers_1h`

Hot-layer migration priority from this audit:

1. site homepage live movers preview  
2. bot `/movers`  
3. bot `/watchlist` + post-add live readiness  
4. bot `/inbox` + push alert candidate delivery  
5. watchlist review/picker/recovery helpers later

Reason:

• these first surfaces are the first-value live loop for discovery, proof, retention, and alert usefulness  
• later helper surfaces are mainly coverage/status aids, not the primary live decision moment

---

# Ingest Contour Mapped (2026-03-27)

Mapped the current ingest contour so the next hot/live worker can be placed without a broad refactor.

Files reviewed:

• `.github/workflows/ingest.yml`
• `ingest/main.py`
• `ingest/worker.py`
• `docs/railway-deploy.md`
• `db/migrations/002_live_universe_views.sql`
• `db/migrations/005_live_only_hardening.sql`
• `db/migrations/007_market_universe_auto_balance.sql`

Current runtime map:

• primary batch ingest implementation is `ingest/main.py`
• scheduled GitHub Actions backup path runs `python ingest/main.py` hourly
• long-running service path runs `python ingest/worker.py`, which loops the same batch ingest function on an env-driven interval
• direct DB writes in the ingest path are:
  - `public.markets`
  - `public.market_snapshots`
  - `public.market_universe` via `public.refresh_market_universe(...)`
• product-facing read surfaces are downstream SQL views over those tables, mainly:
  - `public.top_movers_latest`
  - `public.portfolio_snapshot_latest`
  - `public.watchlist_snapshot_latest`
  - `bot.watchlist_snapshot_latest`

Cadence sources verified:

• GitHub Actions cron: hourly at minute `17`
• worker loop default: `INGEST_INTERVAL_SECONDS=900`
• storage bucket granularity in `ingest/main.py`: `floor_to_5min(...)`

External APIs verified:

• `https://gamma-api.polymarket.com/events`
• `https://gamma-api.polymarket.com/markets/{id}`
• `https://clob.polymarket.com/prices`

Safest hot/live insertion points identified:

1. split a faster quote-only worker beside `fetch_best_bid_ask(...)` + snapshot write path, while leaving market metadata + universe refresh on the slower loop
2. add a hot worker after forced-id resolution (`manual_ids` / `market_universe` / `position_ids`) so it reuses the current coverage contract instead of inventing a new market-selection rule
3. publish a new hot table/view family in parallel to `public.top_movers_latest` / `bot.watchlist_snapshot_latest`, then migrate reads incrementally without touching the historical write-through first

Practical conclusion:

• the repo already has the right boundary shape for a new live worker
• the lowest-risk move is additive and should preserve:
  - current batch ingest
  - current Postgres history writes
  - current SQL view contracts for bot/site

---

# Realtime Data Layer Direction Locked (2026-03-27)

Locked the next infrastructure direction for `Pulse`: user-facing analytics should move toward a faster internal live layer fed from Polymarket APIs, while historical snapshots remain in Postgres and GitHub Actions move into a backup/reconciliation role.

Files updated:

• `manifest.md`
• `progress.md`
• `architecture.md`

What we decided:

• current scheduled ingest cadence is too slow for the product layer:
  - user-facing movers / watchlists / alerts need fresher data
  - GitHub Actions should not remain the primary live ingestion engine
• we are **not** replacing the database or switching the bot/site to direct external API calls on every request
• instead we are introducing a safer split:
  - **live ingest / hot layer** for bot + site relevance
  - **historical snapshots** in Postgres for analytics and history
  - **GitHub Actions** as backup / reconciliation path

Guardrails:

• do not break the current `bot.*` runtime while introducing the new layer
• do not do a big-bang rewrite
• do not remove legacy surfaces before the new hot path is proven
• migrate user-facing reads step by step:
  - homepage movers preview
  - `/movers`
  - `watchlist`
  - alert candidates

Phased plan now fixed in project memory:

1. define the hot/live data contract
2. stand up a primary live worker outside GitHub Actions
3. keep historical write-through into Postgres
4. switch product reads incrementally
5. keep actions for repair/backfill/reconciliation only

Practical implication:

• the next infrastructure work should be modernization, not replacement
• `Pulse` remains Telegram-first and signal-first
• the data layer is being upgraded so the product can become more live without losing the analytical spine we already built

---

# Watchlist Cleanup Truthfulness Fix (2026-03-25)

Fixed a confusing `Pulse` watchlist-cleanup behavior where users could press `Remove closed`, see a success message, and still keep receiving alerts from another market that looked stale but was still active in source data.

Files updated:

• `bot/main.py`

What changed:

• added `execute_db_write_count(...)` so watchlist removals can report actual affected rows
• `cmd_watchlist_remove` now distinguishes between:
  - a real delete
  - a market that is already not in the watchlist
• `menu:cleanup_closed` now:
  - refreshes user context after cleanup
  - explains that only `public.markets.status = 'closed'` rows are removed automatically
  - tells the user to use `/watchlist_remove <market_id|slug>` for still-active markets they want gone manually
  - sends the refreshed review screen after cleanup instead of leaving the user with a stale earlier view
• returning `watchlist` guidance now states more clearly that closed tracked markets can be hidden from the live rows

Operational note:

• investigated market `1633348` directly in production data
• root cause of the confusion was not a fake alert:
  - the market was still `status='active'` in `public.markets`
  - it also had fresh bid/ask quotes and liquidity in `public.market_snapshots`
• because of that, it was correctly eligible for alerting and was not eligible for `Remove closed`
• the product bug was the misleading cleanup UX, not the alert loop itself

---

# CTA Surface Measurement Pass (2026-03-25)

Added placement-level impression tracking so the weekly growth review can compare `seen -> tg_click` on the main site CTA surfaces without breaking the canonical `page_view` denominator.

Files updated:

• `api/web/index.en.html`
• `api/main.py`
• `scripts/growth/weekly_kpi_report.py`
• `docs/growth_kpi_latest.md`

What changed:

• homepage now emits one-time surface impressions via `page_view` for:
  - `hero_panel`
  - `proof_bridge`
• EN `/telegram-bot` now emits one-time surface impressions via `page_view` for:
  - `seo_bridge`
• all surface impression events carry:
  - `surface_impression = true`
• weekly KPI report now excludes those surface-impression events from the top-level funnel `page_view` count
• weekly KPI report now adds a `CTA Surface Performance` table:
  - placement
  - seen
  - tg_click
  - CTR

Practical effect:

• we can now evaluate hero vs bridge surfaces on a real denominator instead of raw click counts alone
• the main funnel stays comparable week over week because generic `page_view` is no longer inflated by surface instrumentation

---

# Telegram-Bot Landing Bridge Pass (2026-03-25)

Improved the EN `/telegram-bot` intent page with a second Telegram-first conversion moment so search users have a cleaner path from intent to action without relying only on the first CTA block.

Files updated:

• `api/main.py`

What changed:

• added a dedicated `FASTEST NEXT STEP` bridge section on the EN `/telegram-bot` page
• the new block explains:
  - open the bot now
  - add one live market
  - use Watchlist or Inbox to judge whether the move matters
  - keep email as backup, not as a competing path
• added separate tracking for this intent-page bridge:
  - `seo_bridge`
  - `seo_bridge_guide`

Practical effect:

• the `/telegram-bot` page now has a second search-intent conversion surface beyond the hero CTA
• this gives us a safer way to test whether bot-intent traffic clicks better when proof and next-step guidance are repeated lower on the page

---

# Landing Proof Bridge Pass (2026-03-25)

Added a mid-page Telegram conversion bridge on the EN homepage so users who scroll past the hero still get a clean proof-to-action step before dropping into SEO links and pricing.

Files updated:

• `api/web/index.en.html`

What changed:

• inserted a new proof-driven conversion strip directly after the historical examples block
• the strip now tells the user:
  - you already saw the live DB preview
  - you already saw real repricing examples
  - the next useful action is still to open `Pulse` in Telegram and add one market
• added separate tracking placements for this strip:
  - `proof_bridge`
  - `proof_bridge_guide`

Practical effect:

• the homepage now has a second strong Telegram decision moment without touching the reverted hero-right panel
• this gives us a safer way to improve `page_view -> tg_click` while keeping the existing hero contract intact

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

---

# Recent Data Layer Update (2026-03-27)

• locked `Realtime Data Layer V1` as the next safe modernization step:
  - doc: `docs/realtime_data_layer_v1_2026-03-27.md`
• this does **not** switch the runtime yet; it fixes the contract first
• the new planned hot surfaces are:
  - `public.hot_market_registry_latest`
  - `public.hot_market_quotes_latest`
  - `public.hot_top_movers_1m`
  - `public.hot_top_movers_5m`
  - `public.hot_watchlist_snapshot_latest`
  - `public.hot_alert_candidates_latest`
  - `public.hot_ingest_health_latest`
• primary ingest direction is now explicit:
  - one centralized live worker talks to Gamma + CLOB
  - the worker writes hot user-facing state
  - the same path still writes historical snapshots into Postgres
• GitHub Actions remain backup / reconciliation / repair, not the primary live engine
• first planned cutover order is now fixed:
  - homepage live movers proof
  - `/movers`
  - watchlist latest state
  - alert candidate generation
• important boundary kept intact:
  - `bot.*` remains the live Pulse runtime this week
  - no watchlist source-of-truth rewrite
  - no legacy view deletion

• added first live-worker skeleton beside the historical ingest path:
  - `ingest/live_main.py`
  - `ingest/live_worker.py`
• current skeleton scope is intentionally narrow:
  - reuses current market coverage contract (`watchlist` + `market_universe` + `positions`)
  - writes only:
    - `public.hot_market_registry_latest`
    - `public.hot_market_quotes_latest`
  - prunes stale rows inside those hot tables
• current skeleton does **not** cut over any runtime reads yet:
  - no homepage preview switch
  - no `/movers` switch
  - no watchlist/inbox switch
• current default live cadence is env-driven:
  - `LIVE_INGEST_INTERVAL_SECONDS` default `60`
  - `LIVE_INGEST_FAIL_SLEEP_SECONDS` default `15`
• this is the first real “hot heartbeat” layer that can support the first read cutover later
• migration `013_hot_data_contract_v1_scaffold.sql` was applied to the live database
• smoke check for the new worker passed against the real DB:
  - `ingest/live_main.py`
  - wrote `public.hot_market_registry_latest=402`
  - wrote `public.hot_market_quotes_latest=402`
  - `has_two_sided_quote=293`
  - `public.hot_ingest_health_latest` returned fresh non-null ages (`~28s` at capture time)
• still no runtime cutover after smoke:
  - `hot_top_movers_*` remain empty by design
  - homepage `/api/live-movers-preview` still reads legacy surfaces
• added first hot-layer ops report:
  - script: `scripts/hot_data_health_report.py`
  - output: `docs/hot_data_health_latest.md`
• report reads:
  - `public.hot_ingest_health_latest`
  - direct table counts from V1 hot tables
• report is phase-aware:
  - registry/quotes must be live now
  - movers/watchlist/alert rows may still be empty until later worker phases
• added env-driven ingest bootstrap for Railway:
  - `ingest/bootstrap.py`
  - `ingest/Procfile` now runs `python bootstrap.py`
• runtime split is now explicit without duplicating the service tree:
  - `INGEST_RUNTIME=batch` -> historical worker (`worker.py`)
  - `INGEST_RUNTIME=live` -> hot worker (`live_worker.py`)
• Railway plan reality changed the deployment shape:
  - creating a separate `live-ingest` service hit the current resource limit
  - so the existing Railway `ingest` service is now the target hot-layer runtime
  - GitHub Actions remains the batch/history backup path
• deploy contract updated in `docs/railway-deploy.md` accordingly:
  - `ingest` now runs `INGEST_RUNTIME=live`
  - batch runtime remains available in the same source tree, but not as the primary Railway service
• verified the live Railway runtime end-to-end:
  - deployment `8b13b91c-b02d-4047-9bf1-e989ae581af5` reached `SUCCESS`
  - logs show `live ingest worker started` and repeated `live ingest tick` writes
  - regenerated `docs/hot_data_health_latest.md`
  - latest captured health is green for the V1-now surfaces:
    - registry freshness `42s`
    - quotes freshness `42s`
• completed the first safe runtime cutover:
  - homepage `/api/live-movers-preview` now reads hot current state first
  - source order is:
    1. `public.hot_market_registry_latest` + `public.hot_market_quotes_latest`
    2. legacy fallback only if the hot query yields no usable rows
• hot preview gates are now explicit at the site edge:
  - max freshness: `120s`
  - min liquidity: `1000`
  - max spread: `0.25`
• sparkline behavior stays safe during the transition:
  - historical points still come from `public.market_snapshots`
  - the current hot midpoint is appended so the preview can show fresher “now” without waiting for the next batch bucket
• local smoke for the new preview path passed:
  - `fetch_live_movers_preview(limit=3)` returned live rows from the hot-first path
• completed the first hot mover publish phase in the live worker:
  - `ingest/live_main.py` now publishes `public.hot_top_movers_5m`
  - publish stays additive-only; no `/movers` cutover yet
• current hot 5m mover gates:
  - min liquidity: `1000`
  - max spread: `0.25`
  - min abs delta: `0.005`
  - two-sided YES quote required
  - status must remain `active`
• first smoke after publish succeeded:
  - `movers_5m=19`
  - top rows now overlap the expected legacy mover set instead of being dominated by zero-delta high-liquidity markets
• deployed the mover publish phase to the live Railway ingest runtime:
  - deployment `e964e520-2012-4738-82a0-2b50f56382d0` reached `SUCCESS`
  - logs now show `movers_5m=` on live ticks
• regenerated `docs/hot_data_health_latest.md` after deploy:
  - `hot_movers_5m_count` is now non-zero on the live heartbeat
  - registry freshness remains comfortably inside the green threshold
  - quotes freshness remains comfortably inside the green threshold
• added a dedicated comparison report before `/movers` cutover:
  - script: `scripts/compare_hot_vs_legacy_movers.py`
  - output: `docs/hot_vs_legacy_movers_latest.md`
• current comparison result says **do not cut over `/movers` yet**:
  - observed summary: `hot_count=30`, `legacy_count=50`, `overlap_count=12`
  - many top legacy rows are already covered in `public.hot_market_quotes_latest`
  - but they do not survive the hot 5m mover gates because the current live delta has already reverted
• conclusion from this pass:
  - homepage hot-first preview is still correct
  - `/movers` needs one more product/data decision pass before we switch it
• fixed the product meaning of `/movers` in:
  - `docs/movers_surface_decision_2026-03-27.md`
• explicit decision:
  - `/movers` should mean **current actionable movers**
  - not just the largest completed bucket shocks
• implication:
  - `public.hot_top_movers_5m` remains the long-term target
  - `public.top_movers_latest` remains comparison + fallback until the hot surface is calibrated enough for that meaning
• upgraded the comparison tooling with explicit exclusion diagnostics:
  - `docs/hot_vs_legacy_movers_latest.md` now shows `exclusion_reason`
  - the dominant current reason is `below_abs_delta_gate`
• this is a useful calibration result:
  - mismatch is no longer “mysterious”
  - the hot layer is mostly excluding reverted legacy movers because their current live 5m delta no longer clears the action threshold
• first threshold calibration step improved the comparison signal:
  - trial lowering `HOT_MOVERS_MIN_ABS_DELTA` from `0.005` to `0.003` materially improved overlap
  - live trial run wrote `movers_5m=65`
• decision:
  - promote `0.003` as the new calibrated default for hot 5m movers
  - accept hot-first `/movers` with legacy fallback
• after calibration, `/movers` was switched to hot-first with legacy fallback:
  - `bot/main.py`
  - `fetch_top_movers_async()` now tries `public.hot_top_movers_5m` first
  - falls back to `public.top_movers_latest` only if the hot query returns no rows
• regenerated the canonical comparison report after accepting the new threshold:
  - `docs/hot_vs_legacy_movers_latest.md`
  - current snapshot shows `hot_count=50`, `legacy_count=50`, `overlap_count=34`
• local bot smoke after the cutover passed:
  - `fetch_top_movers_async(limit=3)` returned 3 rows from the hot-first path
