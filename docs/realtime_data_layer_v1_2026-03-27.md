# Realtime Data Layer V1 (2026-03-27)

This document defines the first safe modernization step for live user-facing analytics.

It does not replace the current runtime yet.

It defines the contract we will add next.

## Why We Are Doing This

The current analytical spine is valuable, but the user-facing signal loop is still too batch-shaped:

- GitHub Actions ingest is hourly backup, not a live engine
- the Railway ingest worker still defaults to a slow interval for product-grade signal UX
- homepage movers, `/movers`, watchlist snapshots, and alert candidates still depend on bucketed historical writes as the primary timing source

That is acceptable for history and reconciliation.

It is not good enough for the part of the product that is supposed to feel live.

## Current Runtime Constraints

Today the same batch-shaped ingest logic is entered through two real paths:

- `.github/workflows/ingest.yml` as hourly backup
- `ingest/worker.py` as a looping service around `ingest.main.main()`

That matters because the main ingest path currently does three different jobs at once:

- pulls live market metadata from Gamma
- pulls live prices from CLOB
- writes 5-minute historical buckets into `public.market_snapshots`

Important constraint:

- `market_snapshots` are still bucketed to 5-minute storage windows
- increasing the current worker frequency alone would mostly overwrite the same bucket faster
- that helps freshness a bit, but it does not create a true hot user-facing contract

So V1 is not “turn the current loop knob harder”.

It is “add a distinct hot read layer beside the historical write-through path”.

## Core Decision

We are not switching product requests to direct Polymarket API calls.

We are adding a centralized hot layer:

- one internal live ingest path talks to Polymarket APIs
- it writes a fast internal state for bot/site reads
- it also writes historical snapshots to Postgres

So the product reads our own hot layer, not the external API on every request.

## Design Rules

Hard rules for V1:

- no big-bang rewrite
- no deletion of current analytical tables or views
- no immediate switch of every bot/site surface
- no change to the public bot command contract
- no migration of watchlist source of truth away from `bot.*` this week

Instead:

- add a hot ingest contract beside the current historical path
- keep historical write-through intact
- migrate reads one surface at a time
- keep GitHub Actions as backup / reconciliation / repair

## V1 Scope

V1 introduces a hot internal layer for these user-facing cases:

- live homepage movers proof
- `/movers`
- watchlist latest state
- alert candidate generation

V1 does not yet redesign:

- `public.watchlist*`
- `public.alerts*`
- long-horizon analytical history
- semantic taxonomy replacement for `public.markets.category`

## New Hot Surfaces

These are the read contracts we want to add.

They can be implemented as tables plus refresh logic, or as views over hot tables, but the product contract should use these names and meanings.

### 1. `public.hot_market_registry_latest`

Purpose:

- the latest active market registry for product/runtime reads

Minimum fields:

- `market_id`
- `slug`
- `question`
- `status`
- `end_date`
- `event_title`
- `category`
- `token_yes`
- `token_no`
- `updated_at`
- `source_ts`

Rules:

- source of truth for live market metadata
- should refresh much more often than the current scheduled analytical cadence
- should not be treated as historical storage

### 2. `public.hot_market_quotes_latest`

Purpose:

- the latest fast quote state per market

Minimum fields:

- `market_id`
- `bid_yes`
- `ask_yes`
- `mid_yes`
- `liquidity`
- `spread`
- `quote_ts`
- `ingested_at`
- `freshness_seconds`
- `has_two_sided_quote`

Rules:

- this is the primary hot quote layer for user-facing reads
- this surface should prefer freshness over bucketed stability
- it should be safe to read directly from bot/site handlers

### 3. `public.hot_top_movers_1m`

Purpose:

- very fresh tape-style movers

Minimum fields:

- `market_id`
- `question`
- `slug`
- `prev_mid`
- `current_mid`
- `delta_mid`
- `delta_abs`
- `liquidity`
- `spread`
- `score`
- `window_start`
- `window_end`
- `quote_ts`

Rules:

- should be filtered by freshness, liquidity, and quote quality
- should not surface clearly illiquid / stale / one-sided garbage

### 4. `public.hot_top_movers_5m`

Purpose:

- primary user-facing movers surface

Minimum fields:

- same as `public.hot_top_movers_1m`

Rules:

- this is the first target for homepage and bot migration
- this should become the default “live enough to act on” movers layer

### 5. `public.hot_watchlist_snapshot_latest`

Purpose:

- latest per-user watchlist state built from hot registry + hot quotes

Minimum fields:

- `app_user_id`
- `market_id`
- `question`
- `slug`
- `status`
- `mid_current`
- `mid_prev_5m`
- `delta_mid`
- `liquidity`
- `spread`
- `live_state`
- `quote_ts`
- `ingested_at`

Rules:

- `live_state` should remain product-readable:
  - `ready`
  - `partial`
  - `no_quotes`
  - `closed`
  - optional future extension: `date_passed_active`
- this is a runtime surface, not a history table

### 6. `public.hot_alert_candidates_latest`

Purpose:

- candidate alert rows before user thresholding/delivery

Minimum fields:

- `app_user_id`
- `market_id`
- `question`
- `delta_mid`
- `delta_abs`
- `threshold_value`
- `liquidity`
- `spread`
- `quote_ts`
- `ingested_at`
- `candidate_state`

Rules:

- should only include markets that pass minimum quote/freshness gates
- should not send noise caused by stale or low-quality quotes

### 7. `public.hot_ingest_health_latest`

Purpose:

- operational read-only health surface for the hot layer

Minimum fields:

- `registry_age_seconds`
- `quotes_age_seconds`
- `active_market_count`
- `two_sided_quote_count`
- `hot_movers_1m_count`
- `hot_movers_5m_count`
- `updated_at`

Rules:

- this is the fast operational companion to `public.analytics_core_health_latest`
- this should tell us when the hot layer is stale before the product starts feeling stale

## Hot Worker Responsibilities

V1 assumes a long-running live worker.

This worker is responsible for:

- fetching active market metadata from Gamma
- fetching live quotes from CLOB
- writing the hot registry surface
- writing the hot quotes surface
- computing hot movers
- computing hot watchlist snapshots
- computing hot alert candidates
- writing historical snapshots through to the existing analytical layer

This worker is not responsible for:

- Telegram delivery
- email sending
- user command handling

## Safest Insertion Points In The Current Codebase

We already know where the first implementation can attach without ripping up the runtime.

### Ingest selection contract reuse

Best safe reuse point:

- `ingest/main.py` after forced coverage resolution and before quote fetch/write stages

Reason:

- it already resolves the product-critical market set from:
  - `bot.watchlist`
  - `public.market_universe`
  - `public.user_positions`
- that means V1 can reuse the current “which markets matter” logic before it improves “how fresh the reads are”

### Hot sink insertion

Best safe sink point:

- alongside the current `public.markets` / `public.market_snapshots` writes in `ingest/main.py`

Reason:

- we can keep the historical path intact
- and add hot writes in parallel
- without changing the current history-producing contract

### Read migration point

Best safe migration point:

- add new hot read surfaces beside current downstream views
- compare outputs before any switch

Reason:

- homepage, `/movers`, watchlist, and alert candidates can move one-by-one
- the old read path stays available for rollback

## External Sources

Expected upstream sources stay the same as today:

- Gamma API for market/event metadata
- CLOB API for live quotes

What changes is not the external dependency.

What changes is:

- cadence
- runtime placement
- product read contract

## Historical Write-Through

The historical analytical layer remains valuable and stays in place.

The hot worker should continue writing through into:

- `public.market_snapshots`
- supporting analytical rebuilds already based on `market_snapshots`

Meaning:

- the hot layer is not “instead of history”
- it is “in front of history for user-facing speed”

## Migration Order

We do not switch everything at once.

V1 migration order:

1. homepage movers proof (`/api/live-movers-preview`)
2. bot `/movers`
3. watchlist latest snapshot reads
4. alert candidate generation
5. inbox derivation from the new candidate layer

Only move to the next step after the previous one is stable.

## Read Cutover Rules

For every cutover:

- keep the old surface alive during the transition
- compare outputs before flipping the main read
- prefer additive reads over destructive rewiring
- keep one rollback path

No cutover should require changing the public bot command surface.

## Scoring Rules For Hot Movers

The hot layer should not rank purely by absolute delta.

Base gates:

- market must be active
- quotes must be fresh
- both sides should be present for the main path
- liquidity must clear a minimum threshold
- spread should not be extreme

Expected scoring shape:

- delta magnitude matters
- liquidity matters
- freshness matters
- spread quality matters

This is intentionally a scored signal surface, not a raw ticker dump.

## Compatibility Boundary

These current surfaces remain valid during V1:

- `public.market_snapshots`
- `public.market_universe`
- `public.snapshot_health`
- `public.top_movers_*`
- `bot.watchlist_snapshot_latest`
- `bot.alerts_inbox_latest`

But the target direction is:

- historical analytics remain on the current analytical spine
- live user-facing reads progressively move onto the hot layer

## Explicit Non-Goals For V1

- no full schema cleanup in `public`
- no deletion of legacy compatibility views
- no rewrite of `bot.watchlist`
- no rewrite of `bot.alerts*`
- no replacement of email/bot/site delivery logic
- no direct per-request Polymarket API reads from product handlers

## Definition Of Done For V1

We consider V1 successful when:

- the hot contract exists and is documented
- a live worker owns hot surfaces centrally
- homepage live proof no longer depends primarily on slow bucket history
- `/movers` can read from a fresher hot movers surface
- historical snapshots continue to accumulate in Postgres
- rollback to the current read path remains possible

## Safe Parallel Work

These tasks can run in parallel without breaking the current runtime:

- map current read-path dependencies for homepage, `/movers`, watchlist, and inbox
- scaffold hot tables/views without switching reads
- build the live worker skeleton with heartbeat-only writes first
- define mover scoring gates and thresholds
- add clickable market links on the site
- add operational dashboards/reports for hot-layer freshness

These tasks should not run in parallel with a live read cutover:

- deleting old views
- rewriting watchlist source of truth
- changing bot command contracts
- switching multiple product surfaces to the hot layer at once
