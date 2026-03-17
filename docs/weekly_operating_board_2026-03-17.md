# Weekly Operating Board (2026-03-17)

This board translates the current 14-day growth plan and the `Polycule` competition plan into a practical operating model.

Core rule:

- `Pulse` remains the acquisition + signal product
- `Trader` remains the execution extension
- growth work must stay tied to real product activation, not vanity output

---

# Now

## 1. Pulse Activation

Primary KPI:

- `tg_click -> /start -> watchlist_add -> first useful signal`

Current mission:

- reduce time-to-value for new Telegram users
- make quiet states intelligible instead of confusing
- keep users inside `Pulse` until they actually feel signal value

This week:

- keep `/start` -> first market flow tight
- keep replacement flow for dead markets tight
- improve first-value messaging after `watchlist_add`
- validate whether users who add one market actually come back to `/watchlist` or `/inbox`

Success looks like:

- a new user can understand the product in under a minute
- a quiet market does not feel like a broken product

Owner:

- Codex main thread

Can be delegated safely:

- copy-only bot message tightening
- small UX audits on empty states

---

## 2. Search + Site Conversion

Primary KPI:

- indexed pages
- impressions
- `page_view -> tg_click`

Current mission:

- turn the website into a clean EN-only acquisition layer
- keep all pages pushing the same Telegram-first funnel

This week:

- continue GSC cleanup and resubmissions
- monitor indexing movement after EN-only switch
- keep strengthening internal links across acquisition pages
- keep sharpening page copy around real user pains:
  - manual scanning
  - alert fatigue
  - dashboard overload

Success looks like:

- more EN pages move from discovered to indexed
- pages read like direct answers to search intent, not keyword shells

Owner:

- Codex main thread

Can be delegated safely:

- copy QA across EN pages
- schema/metadata spot checks

---

## 3. JIT Social Distribution

Primary KPI:

- `utm_source=x|threads -> tg_click`

Current mission:

- post fewer, fresher, more credible pieces
- keep social tied to current live windows and real market movement

This week:

- use the just-in-time social generation flow before every post
- manually publish the current pain-first series:
  - manual workflow pain
  - alert fatigue
  - dashboard overload
- keep using branded short videos only when the underlying live window is still fresh
- run one lightweight retro after 3-5 posts:
  - which message got clicks
  - which post got ignored

Success looks like:

- manual posting becomes a repeatable operator flow
- we stop publishing stale content

Owner:

- shared: Codex prepares, Nikita posts manually

Can be delegated safely:

- new pain-first post drafts
- new short-video briefs
- visual QA on clips

---

## 4. Trader Execution Foundation

Primary KPI:

- `Pulse -> Trader handoff`
- `Trader /start -> /connect -> /signer -> readiness`

Current mission:

- keep `Trader` honest as an alpha execution surface
- move from “draft bot” toward a real execution path, one safe layer at a time

This week:

- keep signer session flow stable
- keep operator activation path usable
- keep dry-run worker status visible in the bot
- prepare the bridge from verified signer to executable order lifecycle

Success looks like:

- a user can understand where they are blocked
- a user can see a path from signal to execution, even if real routing is not live yet

Owner:

- Codex main thread

Can be delegated safely:

- UX copy audits inside `Trader`
- state-machine review for order statuses

---

# Next

## 1. Pulse Retention Loop

- email confirm + welcome + digest fully operational
- more explicit “come back later” logic for quiet states
- smarter post-add follow-up if market stays dead

## 2. Real Growth Measurement

- turn weekly KPI retro into a fixed rhythm
- compare:
  - search
  - direct
  - X
  - Threads
- identify which message actually causes `/start`

## 3. Trader Execution Bridge V1

- signer verification contract hardens
- worker moves from dry-run-only semantics toward execution-ready lifecycle
- positions/order sync becomes more user-visible

## 4. Product Positioning Sharpening

- keep tightening site + bot language around:
  - signal quality
  - low-noise trust
  - execution as extension, not as product confusion

---

# Later

## 1. Real Trader Monetization

- only after real execution value exists
- possible path:
  - `Trader Alpha Access`
  - or `Pulse Pro -> Trader priority access`

## 2. AI Trader-Agent Layer

- only after:
  - signer
  - routing
  - order lifecycle
  - reconciliation
- agent should be a decision layer, not a fake marketing layer

## 3. Broader Distribution

- Reels/TikTok as reuse channel, not core channel yet
- X API automation only after credits exist

---

# Blocked

## 1. X API Autopost

Blocked by:

- `402 CreditsDepleted`

Current rule:

- manual posting remains correct

## 2. Real Trader Execution

Blocked by:

- no real signer verification contract yet
- no live routing client yet
- no reconciliation loop yet

## 3. Revenue From Trader

Blocked by:

- current `Trader` alpha does not yet provide real execution value

---

# Channel Map

## Website

Role:

- search acquisition
- product explanation
- email backup capture
- Trader alpha positioning

## Pulse Bot

Role:

- main activation surface
- live signals
- watchlist habit formation

## Trader Bot

Role:

- execution alpha surface
- power-user handoff from `Pulse`

## X

Role:

- primary top-of-funnel social channel
- pain-first message testing

## Threads

Role:

- softer mirror of X
- secondary social distribution

## Email

Role:

- retention and backup channel

---

# Delegation Guide

## Safe to delegate

- content drafts
- short-video briefs
- metadata/schema audits
- UX copy reviews
- competitive scan refreshes

## Keep in main thread

- DB migrations
- bot behavior changes
- execution/trader state machine changes
- site routing/indexing changes
- monetization logic

---

# Weekly Decision Rules

1. If `Pulse` activation is weak, prioritize `Pulse` over `Trader`.
2. If social content is stale, skip posting rather than fake activity.
3. If `Trader` does not yet execute real value, do not oversell it.
4. If indexing and CTR improve, expand search pages carefully rather than multiplying thin pages.
5. Every new growth asset must stay inside the current brand system and product truth.
