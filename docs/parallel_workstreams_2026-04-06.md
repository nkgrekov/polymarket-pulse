# Parallel Workstreams (2026-04-06)

## Purpose

Keep the main `Pulse` modernization moving without losing time on safe parallel work.

This document separates:

- the main critical path
- additive parallel tracks
- things that should *not* run in parallel

## Main Critical Path

### Current primary path

1. Accumulate `bot.delivery_parity_log`
2. Wait for the first meaningful non-quiet windows
3. Evaluate:
   - `hot_only_samples`
   - `legacy_only_samples`
   - `both_non_quiet_samples`
   - overlap behavior
4. Decide whether push delivery can move to hot-first with fallback

### Why this is the main path

- homepage preview is already hot-first
- `/movers` is already hot-first
- `watchlist` is already hot-first
- `/inbox` is already hot-first
- push delivery is the last meaningful runtime surface still intentionally held on legacy

## Parallel Workstreams

### W1. Growth Measurement Review

Goal:

- understand current top-of-funnel performance while delivery parity history accumulates

Good inputs:

- GSC top queries
- GSC top pages
- GA4 landing pages
- GA4 `tg_click` by placement

Safe outputs:

- identify strongest search intents
- identify weakest landing pages
- identify whether the next growth iteration should target:
  - homepage
  - `/telegram-bot`
  - `/signals`
  - activation flow after `/start`

Why this is safe:

- no conflict with bot delivery semantics
- no conflict with hot-layer migration

### W2. Railway / Ops Hygiene

Goal:

- reduce operational fragility and cost risk on the new Hobby plan

Scope:

- define which services must stay always-on
- define which services can stay parked
- document spending alerts / limits
- confirm login / deploy / restart workflow remains healthy

Why this is safe:

- operational only
- no product contract change

### W3. Small Pulse UX Wins

Goal:

- continue improving trust and clarity in the bot without touching the delivery contract

Good candidates:

- `Review list` clarity
- stale / closed cleanup loops
- quiet-state wording
- threshold explanation
- post-add and return-loop guidance

Why this is safe:

- additive UX only
- no cutover risk

### W4. Legacy Drift Cleanup Planning

Goal:

- prepare the next DB cleanup step after grant hardening

Focus:

- `public.watchlist_markets`
- other unmanaged or suspicious legacy `public` objects
- decide:
  - archive
  - migrate
  - or delete later

Why this is safe:

- planning only
- no runtime refactor mixed into the current delivery decision

### W5. SEO / Intent Page Polish

Goal:

- improve search-entry quality without another broad landing rewrite

Focus:

- `/telegram-bot`
- `/signals`
- `/analytics`
- `/top-movers`

Good changes:

- titles / descriptions
- internal links
- proof-to-action clarity

Why this is safe:

- separate from delivery/runtime migration

## Work That Should Not Run In Parallel

Do not mix these into the current cycle:

1. Push-delivery hot-first cutover before parity history is meaningful
2. Broad landing redesign
3. Large new `Trader` feature work
4. Mass schema rename in Postgres
5. Broad RLS rollout while delivery decision is still open

## Delegation Rules

### Good delegation candidates

- GSC / GA4 interpretation
- Railway cost / service inventory
- small site SEO polishing
- legacy DB inventory
- Pulse UX micro-improvements

### Bad delegation candidates

- changing push delivery semantics
- changing hot-layer write logic and bot read logic at the same time
- removing legacy fallbacks
- touching multiple runtime surfaces in one task

## Decision Gates

### Delivery cutover gate

Evidence we want before changing delivery:

- repeated non-quiet samples in `bot.delivery_parity_log`
- explainable or low `legacy_only_samples`
- either:
  - strong overlap
  - or repeated `hot_only_samples` that look product-correct

### Growth iteration gate

Evidence we want before the next landing/growth push:

- fresh GSC query/page picture
- fresh GA4 landing/CTA picture
- updated `tg_click -> /start -> watchlist_add` reading

## Recommended Sequence From Here

1. Keep `delivery parity` history accumulating
2. In parallel, review `GSC + GA4`
3. In parallel, tighten Railway ops and service posture
4. If needed, take one small `Pulse UX` improvement
5. Reassess delivery on the first meaningful non-quiet parity window
