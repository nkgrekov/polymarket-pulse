# Polymarket Pulse — System Architecture

This document describes the technical architecture.

---

# Homepage Preview 1m Freshness Cue (2026-03-31)

The homepage live movers preview now consumes a minimal additive signal from `public.hot_top_movers_1m`.

Updated artifacts:

• `api/main.py`
• `api/web/index.en.html`
• `api/web/index.ru.html`

API-side:

• `fetch_live_movers_preview()` now includes:
  - `delta_1m`
• this comes from a left join to `public.hot_top_movers_1m`
• the preview ranking itself is unchanged:
  - `delta_yes` and the existing hot preview gates still determine which rows appear

UI-side:

• homepage mover rows render a compact `1m` chip only when `delta_1m` is non-zero
• the chip is secondary:
  - it sits beside the existing move line
  - it does not replace the main 5m-style move context
• if `delta_1m` is absent or zero, the UI stays exactly as before

Boundary:

• no new preview endpoint
• no ranking change
• no new click path
• no hero structural change

Why this is safe:

• the homepage remains anchored on the already accepted hot preview semantics
• `1m` is only a freshness accent
• this lets the site feel more “live now” without prematurely promoting the 1m tape into a primary product surface

# Hot 1m Movers Publish (2026-03-31)

The live worker now publishes a true tape-style 1 minute mover surface.

Updated artifacts:

• `ingest/live_main.py`

Worker-side:

• `public.hot_top_movers_1m` now reads its previous anchor from the prior `public.hot_market_quotes_latest` state
• this means the 1m surface is derived from the previous live tick, not from 5m historical buckets
• current 1m gates:
  - `status = active`
  - two-sided quote required
  - minimum liquidity `1000`
  - maximum spread `0.25`
  - `HOT_MOVERS_1M_MIN_ABS_DELTA` default `0.002`

Boundary:

• no new read surface is cut over in this step
• homepage preview stays on hot preview logic already shipped
• `/movers` continues to use `hot_top_movers_5m` as its primary hot semantic layer

Why this matters:

• the hot layer now has both:
  - `1m` tape-style movers for very fresh movement
  - `5m` action-style movers for product-facing decision surfaces
• this keeps future calibration explicit instead of overloading one mover table with two different jobs

# Hot vs Legacy Delivery Comparison (2026-03-31)

The first delivery comparison pass is now explicit and repeatable.

Updated artifacts:

• `scripts/compare_hot_vs_legacy_delivery.py`
• `docs/hot_vs_legacy_delivery_latest.md`

Compared surfaces:

• `public.hot_alert_candidates_latest`
• `bot.alerts_inbox_latest`
• `bot.sent_alerts_log`

Current observed state:

• latest hot snapshot contains candidates, but no `ready` rows
• latest legacy inbox window is also empty
• recent sent-alert history still shows older delivered watchlist events

Architectural implication:

• the latest quiet inbox state is currently consistent across hot and legacy read surfaces
• this is useful parity, but it is not sufficient evidence for a push-delivery cutover yet
• the comparison report is therefore the decision gate for the next step:
  - wait for a non-zero `hot_ready_count`
  - compare overlap or drift against legacy inbox rows
  - only then evaluate hot-first delivery with fallback

Why this matters:

• the read-path migration can be validated independently from the delivery loop
• quiet-state truthfulness is improving before delivery risk is introduced
• `bot.sent_alerts_log` must be interpreted as historical tail, not as proof that the current hot window should still deliver alerts

# Hot Inbox Migration (2026-03-31)

The next additive `Pulse` cutover now sits at the inbox read surface.

Updated artifacts:

• `ingest/live_main.py`
• `bot/main.py`

Worker-side:

• `ingest/live_main.py` now publishes `public.hot_alert_candidates_latest`
• source input for candidate classification is:
  - `public.hot_watchlist_snapshot_latest`
  - per-user threshold from `bot.user_settings`
• current candidate-state mapping:
  - `ready`
  - `below_threshold`
  - `stale_quotes`
  - `no_quotes`
  - `closed`
  - `filtered_liquidity`
  - `filtered_spread`
• current hot alert gates:
  - threshold default `0.03`
  - minimum liquidity `1000`
  - maximum spread `0.25`

Bot-side:

• `fetch_inbox_async()` is now hot-first
• watchlist rows come from:
  - `public.hot_alert_candidates_latest`
  - joined to `public.hot_watchlist_snapshot_latest`
• portfolio rows remain legacy for now:
  - `bot.portfolio_alerts_latest`
• full fallback remains:
  - `bot.alerts_inbox_latest`

Diagnostics:

• `fetch_inbox_diagnostics_async()` is now hot-first for watchlist candidates
• `below_threshold` hot rows are visible to quiet-state messaging
• portfolio diagnostics still reuse the legacy snapshot path

Boundary:

• only inbox read semantics are migrated
• push delivery is intentionally unchanged and still reads `bot.alerts_inbox_latest`
• `SQL_PUSH_CANDIDATES`, delivery dedupe, and sent-log semantics remain legacy
• rollback remains trivial because the legacy inbox query is still present and used automatically when the hot read yields no rows

Why this is safe:

• the worker now materializes watchlist candidate truth separately from delivery
• `/inbox` gains a fresher read path without coupling product UX to the alert sending loop
• quiet-state guidance gets better before we touch any delivery guarantees

# Landing Clickable Market Rows Contract (2026-03-27)

The site homepage live movers preview now exposes a lightweight action handoff contract on top of the existing homepage read surface.

Updated artifacts:

• `api/main.py`
• `api/web/index.en.html`
• `api/web/index.ru.html`

Surface affected:

• homepage live movers proof surface
  - `api/main.py` `/api/live-movers-preview`
  - `api/web/index.en.html`
  - `api/web/index.ru.html`

Additive contract extension:

• live mover preview rows now carry:
  - `market_id`
  - `question`
  - `slug`
  - `last_bucket`
  - `prev_bucket`
  - `yes_mid_now`
  - `yes_mid_prev`
  - `delta_yes`
  - `spark`
  - `market_url`
  - `track_url`

UI behavior:

• homepage row body opens Polymarket when a reliable slug-based `market_url` exists
• homepage row always exposes a secondary `Track in Telegram` handoff
• if `market_url` is unavailable, the site should not invent a brittle Polymarket path:
  - only Telegram tracking remains actionable
• the stable market handoff path is:
  - `https://polymarket.com/market/<slug>`
  - not `https://polymarket.com/event/<slug>`
  - Polymarket handles any deeper canonical redirect from there

## Hot Watchlist Snapshot Migration (2026-03-27)

The next additive hot-layer step is now the `watchlist` live snapshot.

Worker-side:

• `ingest/live_main.py` now publishes `public.hot_watchlist_snapshot_latest`
• source inputs remain:
  - `public.hot_market_registry_latest`
  - `public.hot_market_quotes_latest`
  - legacy `public.market_snapshots` only for the previous 5m anchor
• state vocabulary currently used:
  - `ready`
  - `partial`
  - `no_quotes`
  - `closed`

Bot-side:

• `fetch_watchlist_snapshot_async()` in `bot/main.py` is now hot-first
• fallback remains:
  - `bot.watchlist_snapshot_latest`

Boundary:

• only the primary live `watchlist` snapshot read is migrated
• diagnostics, wider fallback windows, and inbox delivery logic remain on the existing path
• rollback remains trivial because the legacy query is still present and used automatically when the hot surface yields no rows

Hierarchy guardrail:

• these are tertiary row-level actions only
• no change to:
  - hero panel CTA position
  - proof bridge CTA position
  - waitlist form logic
  - page section order

Instrumentation note:

• `tg_click` continues to capture Telegram handoff
• additive `market_click` now captures Polymarket handoff
• `site_track_<market_id>` is no longer attribution-only:
  - `cmd_start()` now resolves this payload as a watchlist-add handoff
  - the selected market is added immediately when possible
  - fallback behavior stays inside the existing watchlist add / recovery contract

Intent-page limitation:

• current intent/SEO pages rendered from `api/main.py` contain generic feature preview cards, not market-specific rows
• therefore no new per-market Polymarket links were added to those surfaces
• the clickable market-row contract currently applies only to homepage live movers, where real market objects already exist

Why this remains low-risk:

• homepage still reads the same preview source and sparkline history
• no ingest or migration boundary changed
• no legacy surfaces were removed
• rollback remains trivial because the change is presentation-layer additive

---

# Hot Data Contract V1 Schema Scaffold (2026-03-27)

The Hot Data Contract V1 schema scaffold is now defined as an additive layer beside the analytical core.

Migration draft:

• `db/migrations/013_hot_data_contract_v1_scaffold.sql`

No runtime read path is switched by this migration.

Legacy compatibility remains intact:

• `public.market_snapshots`
• `public.top_movers_*`
• `public.watchlist_snapshot_latest`
• `bot.watchlist_snapshot_latest`
• `bot.alerts_inbox_latest`

New V1 hot surfaces introduced:

• `public.hot_market_registry_latest`
  - table
  - purpose: latest live market metadata for product-facing reads
  - fields:
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
• `public.hot_market_quotes_latest`
  - table
  - purpose: latest live quote state per market
  - fields:
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
• `public.hot_top_movers_1m`
  - table
  - purpose: worker-owned latest 1m hot movers output
  - fields:
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
    - `ingested_at`
• `public.hot_top_movers_5m`
  - table
  - purpose: worker-owned latest 5m hot movers output and first likely read-cutover target
  - fields:
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
    - `ingested_at`
• `public.hot_watchlist_snapshot_latest`
  - table
  - purpose: per-user hot watchlist state
  - fields:
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
  - current allowed `live_state` values:
    - `ready`
    - `partial`
    - `no_quotes`
    - `closed`
    - `date_passed_active`
• `public.hot_alert_candidates_latest`
  - table
  - purpose: per-user pre-delivery candidate alert surface
  - fields:
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
• `public.hot_ingest_health_latest`
  - view
  - purpose: read-only freshness and population health over the hot layer
  - fields:
    - `registry_age_seconds`
    - `quotes_age_seconds`
    - `active_market_count`
    - `two_sided_quote_count`
    - `hot_movers_1m_count`
    - `hot_movers_5m_count`
    - `updated_at`

Why the scaffold uses latest-state tables:

• it keeps the V1 contract explicit and queryable before any worker code ships
• it lets the future hot worker own full refresh semantics with simple upsert/prune behavior
• it does not force a cutover to views over legacy `market_snapshots`
• it keeps the hot layer independent from bucketed historical timing
• it now encodes basic domain guardrails directly in schema for price/spread/liquidity/threshold ranges

What the migration deliberately does not do:

• no rewrite of `ingest/main.py`
• no rewrite of `ingest/worker.py`
• no runtime reader changes in `api/main.py` or `bot/main.py`
• no deletion or replacement of legacy movers/watchlist/alert surfaces
• no change to Trader or any runtime read path

Worker boundary after scaffold:

• hot worker still needs to:
  - fetch Gamma market metadata
  - fetch CLOB quotes
  - compute freshness/liquidity/spread gates
  - calculate 1m and 5m mover windows plus `score`
  - materialize watchlist state from `bot.watchlist`
  - materialize alert candidates from user threshold settings
  - publish/prune rows in the new hot tables
  - keep writing historical snapshots through to `public.market_snapshots`
• the database now provides stable sink contracts for that work without requiring any runtime read cutover first

Worker publish lifecycle by surface:

• `public.hot_market_registry_latest`
  - latest-snapshot table
  - expected lifecycle: upsert current covered markets, prune markets no longer in hot coverage
• `public.hot_market_quotes_latest`
  - latest-snapshot table
  - expected lifecycle: overwrite latest quote state per covered market, prune stale/uncovered rows
• `public.hot_top_movers_1m`
  - latest-window scored output
  - expected lifecycle: rebuild/prune each worker window, not append historical rows
• `public.hot_top_movers_5m`
  - latest-window scored output
  - expected lifecycle: rebuild/prune each worker window, not append historical rows
• `public.hot_watchlist_snapshot_latest`
  - per-user latest-state output
  - expected lifecycle: upsert tracked-market rows for active watchlists, prune rows that disappear because of membership or state changes
• `public.hot_alert_candidates_latest`
  - per-user latest-state output
  - expected lifecycle: upsert current candidate rows, prune rows filtered out by quality, freshness, status, or watchlist changes
• `public.hot_ingest_health_latest`
  - derived view
  - expected lifecycle: no direct writes; reflects freshness/population of the worker-owned hot tables

Initial worker gate guidance after scaffold:

• quote-domain guardrails are now encoded in schema:
  - probability-like fields stay within `0..1`
  - `spread` stays within `0..1`
  - `liquidity` stays non-negative
  - `threshold_value` stays within `0..1`
• quality gating still belongs to the worker:
  - freshness threshold
  - two-sided quote requirement for primary hot reads
  - minimum liquidity threshold
  - maximum acceptable spread
• state derivation still belongs to the worker:
  - `live_state` for watchlist rows
  - `candidate_state` for alert rows
  - mover `score`

Pinned V1 state vocabulary after scaffold:

• watchlist `live_state`:
  - `ready`
  - `partial`
  - `no_quotes`
  - `closed`
  - `date_passed_active`
• alert `candidate_state`:
  - `ready`
  - `below_threshold`
  - `stale_quotes`
  - `no_quotes`
  - `closed`
  - `date_passed_active`
  - `filtered_spread`
  - `filtered_liquidity`

Recommended V1 worker publish order:

1. publish `public.hot_market_registry_latest`
2. publish `public.hot_market_quotes_latest`
3. publish `public.hot_top_movers_1m`
4. publish `public.hot_top_movers_5m`
5. publish `public.hot_watchlist_snapshot_latest`
6. publish `public.hot_alert_candidates_latest`
7. let `public.hot_ingest_health_latest` reflect the new state passively

Reason for this order:

• registry and quotes are the base contracts every downstream hot surface depends on
• movers should be derived before watchlist and alert surfaces so user-specific rows can reuse the same fresh market state
• health should remain derived-only so it never becomes a second source of truth

Recommended V1 worker compare strategy before any cutover:

• homepage preview candidate:
  - compare `public.hot_top_movers_5m` against `public.top_movers_latest`
  - check overlap, ordering drift, freshness difference, and missing high-liquidity rows
• `/movers` candidate:
  - compare bot-facing top rows from `public.hot_top_movers_5m` against `public.top_movers_latest`
  - keep `public.top_movers_1h` as fallback during evaluation
• watchlist candidate:
  - compare per-user coverage and deltas in `public.hot_watchlist_snapshot_latest` against `bot.watchlist_snapshot_latest`
  - focus on `live_state` truthfulness and quote freshness
• alert candidate layer:
  - compare `public.hot_alert_candidates_latest` against `bot.alerts_inbox_latest`
  - focus on threshold parity, quiet-state truthfulness, and stale-row suppression

Recommended rollback posture for first cutovers:

• keep all legacy readers and legacy SQL surfaces unchanged while hot outputs are being compared
• flip one product surface at a time
• preserve one obvious switch-back path to the legacy query for each surface
• do not mix a worker publish contract change and a runtime read cutover in the same step

Why this draft is ready-to-apply from a schema perspective:

• all objects are additive to the existing runtime
• migration stays transactional
• legacy tables/views remain untouched
• hot tables are explicit latest-state sinks instead of ambiguous history tables
• core V1 state vocabulary is pinned in schema for watchlist and alert derivations
• first cutover still remains a separate future step, not part of this migration

Cutover implication:

• output comparison can happen surface-by-surface after the worker exists
• the first intended consumer remains `public.hot_top_movers_5m`
• rollback stays trivial because the legacy surfaces remain untouched

---

# Pulse/Site Runtime Read Paths (2026-03-27)

Current user-facing runtime reads against the legacy Postgres live surfaces are concentrated in a small set of `Pulse`/site paths:

• site homepage proof surface:
  - `api/main.py` `/api/live-movers-preview`
  - `public.top_movers_latest` for current mover rows
  - `public.market_snapshots` for sparkline history
• bot discovery/read surfaces:
  - `/movers` reads `public.top_movers_latest`
  - `/movers` fallback reads `public.market_snapshots`
  - `/movers` wider fallback reads `public.top_movers_1h`
• bot retention/read surfaces:
  - `/watchlist` reads `bot.watchlist_snapshot_latest`
  - `/inbox` reads `bot.alerts_inbox_latest`
  - push delivery also reads `bot.alerts_inbox_latest`
• bot helper/recovery surfaces:
  - watchlist review, picker, and post-add readiness checks read `public.market_snapshots`
  - picker also reads `public.top_movers_latest` and `public.top_movers_1h`

Migration implication:

• the first hot layer should cover the surfaces that users feel directly as “live product truth”:
  - homepage movers preview
  - `/movers`
  - `/watchlist`
  - `/inbox`
  - push alert candidates
• helper/recovery reads can remain on the slower SQL path longer:
  - watchlist review coverage
  - picker balancing
  - quote-presence diagnostics

Minimal hot-contract orientation:

• movers contract:
  - `market_id`
  - `question`
  - `mid_now`
  - `mid_prev`
  - `delta`
  - `last_ts`
  - `prev_ts`
  - optional spark series for site
• watchlist latest contract:
  - `user_id`
  - `market_id`
  - `question`
  - `mid_now`
  - `mid_prev`
  - `delta`
  - `last_ts`
  - `prev_ts`
• alert candidate contract:
  - `user_id`
  - `market_id`
  - `question`
  - `alert_type`
  - `mid_now`
  - `mid_prev`
  - `delta`
  - `abs_delta`
  - `last_ts`
  - `prev_ts`

---

# Current Ingest Contour Map (2026-03-27)

This is the current ingestion contour as implemented in code today.

Reviewed artifacts:

• `.github/workflows/ingest.yml`
• `ingest/main.py`
• `ingest/worker.py`
• `docs/railway-deploy.md`
• `db/migrations/002_live_universe_views.sql`
• `db/migrations/005_live_only_hardening.sql`
• `db/migrations/007_market_universe_auto_balance.sql`

Execution paths:

1. GitHub Actions scheduled batch
   - runs `python ingest/main.py`
   - schedule: hourly via cron
   - role today: real ingest path, even if product direction says it should become backup/reconciliation later

2. Long-running ingest worker
   - runs `python ingest/worker.py`
   - internally loops `ingest.main.main()`
   - cadence controlled by `INGEST_INTERVAL_SECONDS`

Core ingest flow in `ingest/main.py`:

1. fetch active event/market metadata from Gamma
2. rebalance and cap fetched market set
3. read forced coverage ids from:
   - `public.user_watchlist`
   - `bot.watchlist`
   - `public.market_universe`
   - `public.user_positions`
4. enrich forced ids via Gamma `/markets/{id}` with DB fallback from `public.markets`
5. fetch bid/ask quotes from CLOB `/prices`
6. upsert `public.markets`
7. upsert bucketed rows into `public.market_snapshots`
8. rebuild `public.market_universe` through `public.refresh_market_universe(...)`

Direct write targets:

• `public.markets`
• `public.market_snapshots`
• `public.market_universe`

Downstream live read surfaces fed by those writes:

• `public.top_movers_latest`
• `public.portfolio_snapshot_latest`
• `public.watchlist_snapshot_latest`
• `bot.watchlist_snapshot_latest`

Cadence layers:

• scheduler cadence:
  - GitHub Actions: hourly at minute `17`
  - worker service: default `900s`
• storage cadence:
  - snapshots are bucketed to 5-minute boundaries via `floor_to_5min(...)`
• universe refresh cadence:
  - tied to each successful ingest tick

External source APIs:

• Gamma events: `https://gamma-api.polymarket.com/events`
• Gamma market detail: `https://gamma-api.polymarket.com/markets/{id}`
• CLOB prices: `https://clob.polymarket.com/prices`

Lowest-risk insertion points for a new hot/live worker:

1. after forced-id resolution and before `fetch_best_bid_ask(...)`
   - reuse existing market coverage rules
   - substitute only the faster quote-refresh leg

2. parallel to the current snapshot write block
   - keep `public.market_snapshots` as historical write-through
   - add a separate hot surface write without breaking existing analytical SQL

3. parallel to the downstream read-surface family
   - add new hot movers/watchlist outputs beside `public.top_movers_latest` and `bot.watchlist_snapshot_latest`
   - migrate readers incrementally

Boundary note:

• `trade_worker/main.py` is a separate order-execution loop and is not part of the data ingest contour

---

# Realtime Data Layer Modernization Direction (2026-03-27)

The next infrastructure direction for `Pulse` is now explicitly defined: user-facing analytics should move onto a faster internal live layer fed from Polymarket APIs, while Postgres remains the historical and analytical backbone.

Updated artifacts:

• `manifest.md`
• `progress.md`
• `architecture.md`

Problem statement:

• current ingest cadence is still too slow for product-facing signal delivery
• GitHub Actions and slower scheduled writes are acceptable as backup/reconciliation, but too weak as the primary live runtime
• bot/site first-value UX should not depend on 15m+ stale-ish refresh cycles when the source can move much faster

Direction we are taking:

• do **not** switch bot/site into direct external API calls per request
• do **not** throw away Postgres as the source of historical truth
• do **not** do a big-bang refactor of the existing runtime
• instead introduce a split between:
  - **live ingest / hot layer** for user-facing reads
  - **historical write-through** into Postgres
  - **backup / reconciliation jobs** in GitHub Actions

Target shape:

1. **Market registry layer**
   - active markets
   - slug / question / token ids / status
   - refreshed frequently from Polymarket APIs

2. **Quote / midpoint layer**
   - best bid / ask
   - midpoint
   - liquidity
   - spread
   - freshness timestamp
   - refreshed on a much shorter cadence than the current batch loop

3. **Hot derived surfaces**
   - live movers
   - watchlist latest state
   - alert candidates
   - homepage preview rows
   - these are the surfaces bot/site should read first

4. **Historical storage**
   - append/write-through snapshots in Postgres
   - preserve bucketized history for analytics, digests, and future charts

Migration rule:

• keep the current `bot.*` runtime stable while the hot path is introduced
• add new hot contracts first
• move reads incrementally:
  - homepage movers preview
  - `/movers`
  - `watchlist`
  - alert candidate generation
• only remove or de-prioritize old slower paths after the new layer is stable

GitHub Actions role after modernization:

• backfill
• repair
• reconciliation
• sanity rebuilds

Not the primary live engine.

Operational implication:

• this is a modernization plan, not a rewrite plan
• the analytical spine (`market_snapshots`, `top_movers_*`, history, health checks) remains valuable
• the product gets a faster live contract without losing the core Layer II data asset

Next concrete step:

• define the first hot data contract and worker boundary before any runtime migration begins

---

# Watchlist Cleanup and Removal Truth Contract (2026-03-25)

The `Pulse` watchlist cleanup flow now distinguishes between automatically removable `closed` markets and still-active markets that only look stale from the user’s point of view.

Updated artifact:

• `bot/main.py`

Contract changes:

• introduced `execute_db_write_count(...)` so watchlist removal handlers can report actual affected rows
• `/watchlist_remove <market_id|slug>` now reports truthfully whether a market was actually removed from the current watchlist
• `menu:cleanup_closed` now only claims success for rows actually deleted by:
  - `public.markets.status = 'closed'`
• after cleanup, the bot now refreshes the review surface instead of leaving the user on an earlier stale live screen
• cleanup follow-up copy now makes the distinction explicit:
  - automatically removable: source-marked `closed`
  - manually removable: still `active` in source data, even if the question date already passed
• `watchlist` live guidance now states more clearly that closed tracked markets may be hidden from the live rows and require `Review list` for cleanup

Operational implication:

• alert delivery remains driven by the current analytical/runtime contour:
  - if a market is still `active` in `public.markets`
  - and still has live quotes in `public.market_snapshots`
  - it remains eligible for watchlist alerting
• the cleanup UX no longer implies that `Remove closed` deletes any market that simply “looks dead” from the question wording
• this is a truthfulness fix around the existing source-of-truth contract, not a change to alert eligibility logic

---

# CTA Surface Impression Contract (2026-03-25)

The weekly acquisition loop now distinguishes between whole-page visits and CTA-surface visibility on the main Telegram decision blocks.

Updated artifacts:

• `api/web/index.en.html`
• `api/main.py`
• `scripts/growth/weekly_kpi_report.py`
• `docs/growth_kpi_latest.md`

Contract changes:

• homepage now emits one-time `page_view` events with `surface_impression = true` for:
  - `hero_panel`
  - `proof_bridge`
• EN `/telegram-bot` now emits one-time `page_view` events with `surface_impression = true` for:
  - `seo_bridge`
• these impression events reuse the existing `page_view` event family and do not introduce a new public event type
• weekly KPI reporting now explicitly excludes `surface_impression = true` rows from the canonical funnel `page_view` count
• weekly reporting now adds a dedicated `CTA Surface Performance` section to compare:
  - surface seen count
  - `tg_click`
  - click-through rate

Operational implication:

• the acquisition loop can now evaluate hero and bridge surfaces on a meaningful denominator instead of raw click totals alone
• the canonical growth funnel remains stable:
  - `page_view`
  - `tg_click`
  - `tg_start`
  - `watchlist_add`
• this remains a read-only measurement-layer improvement; no routing, no bot contract, and no new source-of-truth changes are introduced

---

# Telegram-Bot Intent Bridge Contract (2026-03-25)

The EN `/telegram-bot` landing now includes a second conversion bridge for search-intent traffic so the page can repeat the action path without changing the overall site-wide homepage contract.

Updated artifact:

• `api/main.py`

Contract changes:

• the EN `telegram-bot` SEO page now renders an additional `FASTEST NEXT STEP` section after the compare block
• that section restates the intended search-intent path:
  - open the bot
  - add one live market
  - use `Watchlist` / `Inbox` to judge whether the repricing matters
  - keep email as backup only
• added new tracking placements on the SEO page:
  - `seo_bridge`
  - `seo_bridge_guide`

Operational implication:

• `/telegram-bot` can now be optimized as a narrower bot-intent landing independently from the homepage
• this gives the acquisition loop a second measurable CTA surface on a page that is already closer to search intent than the broad brand root

---

# Homepage Proof-Bridge Contract (2026-03-25)

The EN homepage now includes a second Telegram-first decision surface below the historical proof block so scrolling users get another clear conversion moment without modifying the hero-right contract.

Updated artifact:

• `api/web/index.en.html`

Contract changes:

• inserted a dedicated mid-page conversion strip after the historical examples section
• the strip frames the transition explicitly:
  - live DB preview already seen
  - historical repricing proof already seen
  - next useful step is to open `Pulse` in Telegram and add one market
• added new homepage attribution placements:
  - `proof_bridge` for the Telegram CTA
  - `proof_bridge_guide` for the support/guide CTA

Operational implication:

• homepage conversion work can now test a second proof-to-action moment without destabilizing the reverted hero-right panel
• this preserves the current hero contract while giving the weekly KPI a new measurable `page_view -> tg_click` surface

---

# Return-Loop Interpretation Contract (2026-03-25)

The `Pulse` read surfaces for returning users now distinguish more clearly between “useful but quiet”, “healthy thresholded feed”, and “review this list before adding more noise”.

Updated artifact:

• `bot/main.py`

Contract changes:

• introduced `active_followup_text(...)` for non-empty `watchlist` and `inbox` responses
• `watchlist` non-empty responses now frame the first row as the strongest current live delta and interpret the rest of the list relative to:
  - total tracked markets
  - closed markets
  - quiet-but-normal coverage
• `inbox` non-empty responses now frame the first row as the strongest thresholded alert and tie the next step back to:
  - threshold tuning
  - list review
  - not forcing noise on quiet windows
• watchlist fallback windows (`30m`, `1h`) now explicitly explain that broader-window output still has meaning and that “slow” does not imply “broken”

Operational implication:

• `Pulse` return screens are now more interpretive, not only navigational
• this reduces the chance that users misread healthy quiet states as product failure after the first add
• the external command contract stays unchanged; this is a guidance-layer upgrade inside the existing `bot.*` runtime

---

# Post-Add State-Aware Contract (2026-03-25)

The `Pulse` watchlist add/replace flow now classifies the newly added market before deciding what follow-up text and inline actions to show.

Updated artifact:

• `bot/main.py`

Contract changes:

• introduced a shared `market_live_state_summary(market_id, locale)` helper that derives a compact post-add state from `SQL_MARKET_LIVE_STATUS`
• introduced `SQL_MARKET_SNAPSHOT_PREVIEW` + `market_live_preview_line(...)` so `ready` markets can render a compact delta preview directly in the add/replace confirmation
• add/replace results now carry `live_state` with one of:
  - `ready`
  - `partial`
  - `no_quotes`
  - `closed`
• `watchlist_post_add_markup(...)` now branches on that state:
  - `exists` and `ready` keep the normal “added” action surface
  - quiet states switch to the review/recovery action surface
• add/replace confirmation copy now contains:
  - a state-specific status line
  - a state-specific next-step line

Operational implication:

• the first watchlist add is now closer to a guided product contract instead of a generic CRUD confirmation
• the user gets immediate reinforcement toward either:
  - checking `Watchlist` for live deltas after already seeing a compact preview
  - or replacing/reviewing a weak market before the first-value moment stalls
• this is still fully inside the current `bot.*` runtime and does not alter the external command contract

---

# Digest Return Contract Tightening (2026-03-25)

The email digest now includes explicit watchlist-coverage context so the backup channel can direct the user back into the live `Pulse` loop with a clearer next step.

Updated artifact:

• `api/digest_job.py`

Contract changes:

• each digest still centers on recent `bot.alert_events`, but now also computes compact watchlist context per subscriber:
  - total tracked markets
  - currently ready markets from `bot.watchlist_snapshot_latest`
  - closed tracked markets
  - current user threshold from `bot.user_settings`
• the rendered email now contains a `Watchlist coverage` block before the alert list
• that block emits a context-aware return instruction:
  - replace closed markets first
  - swap in a stronger live market if there is no ready coverage
  - review list/threshold in Telegram if some tracked markets stayed quiet
  - otherwise treat the digest as a healthy backup pass and return to Telegram for the live feed

Operational implication:

• the digest is now less of a passive recap and more of a retention surface that mirrors `Pulse` quiet-state logic
• this remains a read-only enrichment of the existing email path; no new public routes, no source-of-truth changes, and no change to the primary Telegram-first product contract are introduced

---

# Active Execution Plan Link

Operational 14-day delivery plan is versioned in:

`docs/plan_14day_seo_bot_growth_2026-03-09.md`

Current weekly operating priorities are tracked in:

`docs/weekly_operating_board_2026-03-17.md`

Architecture and rollout priorities must stay aligned with that plan and with `manifest.md`.

---

# New-User `/start` Contract Tightening (2026-03-25)

The new-user activation path in `Pulse` is now more explicitly action-first.

Updated artifact:

• `bot/main.py`

Contract changes:

• `/start` still logs attribution before any user-facing branch
• for a new user (`watchlist_count == 0`), the bot now separates:
  - lightweight product framing
  - explicit first-value instructions
  - immediate live candidate picker
• the old longer quick-start checklist has been reduced so the first activation screen spends less time on commands and more time on the first add

Operational implication:

• the new-user `/start` surface is now tuned more directly toward the current KPI:
  - `tg_start -> watchlist_add`
• command discovery still exists through `/help` and the menu system, but is no longer prioritized above the first live-market add

---

# Funnel Attribution Contract Repair (2026-03-25)

The weekly growth review now distinguishes between raw Telegram starts and starts that were actually site-attributed, and `watchlist_add` events now carry the latest start context forward.

Updated artifacts:

• `bot/main.py`
• `scripts/growth/weekly_kpi_report.py`
• `docs/growth_kpi_latest.md`

Contract changes:

• `log_watchlist_add_sync(...)` now augments each event with the latest known Telegram-start context for that user:
  - `start_payload`
  - `start_entrypoint`
  - `site_attributed_start`
• weekly KPI reporting now separates:
  - `tg_start (all entrypoints)`
  - `tg_start from site payloads`
  - `watchlist_add users from site-attributed starts`
• the report now explicitly notes that raw `tg_start` can exceed `tg_click` because direct Telegram opens and bot-internal paths are counted too

Operational implication:

• the decision loop is now better aligned with the actual weekly KPI
• future watchlist-add events can be read as part of the acquisition funnel instead of as isolated bot-side actions
• this remains a read-only attribution repair on top of the existing runtime; no product contract or source-of-truth migration is introduced

---

# Brand Query and Digest Return Contract (2026-03-23)

The weekly acquisition/retention layer now includes a safer brand-entity pass and a sharper digest-return surface without changing public routing or the live Pulse runtime.

Updated artifacts:

• `api/web/index.en.html`
• `api/main.py`
• `api/digest_job.py`

Contract changes:

• homepage metadata now identifies the product more explicitly as `Polymarket Pulse Telegram Bot`
• Organization and WebSite JSON-LD on the homepage now reinforce the Telegram-first product identity instead of leaving the brand too abstract
• the EN `/telegram-bot` page now makes the brand-query contract clearer:
  - the page title includes `Polymarket Pulse Telegram Bot`
  - the description ties the brand to the Polymarket Telegram-bot use case
  - FAQ and `WebPage.about` reinforce the same entity pairing
• daily digest now uses a more return-oriented contract:
  - strongest market label can appear in the subject / kicker
  - primary CTA becomes `Resume in Telegram`
  - the email stays a backup surface, but the return path into Pulse is more explicit

Operational implication:

• this is a safe SEO/entity hardening step, not a structural content expansion
• the goal is not to chase more keywords blindly, but to help Google connect:
  - `Polymarket Pulse`
  - `Telegram bot`
  - `Polymarket signals`
• digest continues to serve as backup retention, but now pushes the reader back into the live bot loop more clearly

---

# Homepage Brand Scope Guardrail (2026-03-23)

The homepage brand layer should stay broader than the dedicated `/telegram-bot` landing.

Updated artifact:

• `api/web/index.en.html`

Contract changes:

• homepage metadata now represents `Polymarket Pulse` as the wider signal/analytics product
• the exact `Polymarket Pulse + Telegram Bot` pairing remains strongest on `/telegram-bot`, not on the whole brand root
• Organization / WebSite metadata on the homepage now describe the broader signal terminal rather than reducing the whole product identity to only the bot

Operational implication:

• brand-query SEO work should distinguish between:
  - homepage = broad product/entity layer
  - `/telegram-bot` = bot-intent landing
• this avoids over-narrowing the brand while still giving Google a stronger bot-specific target page

---

# Pulse Watchlist Review Surface Contract (2026-03-23)

The watchlist review screen now acts as a genuine retention surface instead of a passive list dump.

Updated artifact:

• `bot/main.py`

Contract changes:

• `/watchlist_list` and inline `Review list` now share the same renderer:
  - `send_watchlist_list_view(...)`
• `menu:watchlist_list` is now a live callback route, so buttons from watchlist/inbox quiet states and related screens resolve correctly
• the review surface now classifies list-health into actionable states:
  - `ready`
  - `partial`
  - `no_quotes`
  - `closed`
• when the list is weak, the screen now upgrades from diagnostics to action:
  - explicit “best next step” guidance
  - merged live recovery candidates through the existing picker/replacement contract
• when coverage is only thin, the review screen nudges toward adding one more live market rather than stopping at status text

Operational implication:

• `watchlist_list` is now part of the main retention loop, not just a support/debug command
• recovery and cleanup stay inside the current `bot.*` runtime and reuse the existing add/replace picker contract, so no source-of-truth migration is introduced

---

# Homepage Hero Right Panel Contract Revert (2026-03-23)

The EN homepage hero-right panel has been explicitly reverted to the simpler conversion panel contract.

Updated artifact:

• `api/web/index.en.html`

Contract changes:

• the right panel now follows this fixed order again:
  - value kicker
  - short all-caps headline
  - monospace subline
  - three stacked feature rows
  - primary Telegram CTA
  - secondary `How it works?` button
  - waitlist email kicker
  - existing waitlist form
  - confirmation note
• workflow-step cards and extra explanatory callouts are removed from the panel
• the left movers panel, the metrics row, and lower homepage sections remain unchanged

Operational implication:

• homepage hero experimentation should not reintroduce workflow-heavy explanation blocks into the right panel without an explicit decision
• the right panel is again treated as a compact conversion surface, not a mini onboarding page

---

# Weekly Focus Contract: Pulse, Search, Retention, Core Hardening (2026-03-23)

The current weekly execution layer now treats the system as four connected tracks:

• site/search acquisition  
• Pulse bot activation + retention  
• email as backup retention  
• read-only analytical core health  

Trader remains deployed, but is intentionally outside the main weekly optimization path.

Updated artifacts:

• `api/web/index.en.html`
• `api/main.py`
• `bot/main.py`
• `api/digest_job.py`
• `db/migrations/012_analytics_core_health.sql`
• `scripts/growth/weekly_kpi_report.py`
• `scripts/data_core_health_report.py`
• `docs/data_core_contract_2026-03-23.md`

Contract changes:

• EN acquisition pages now use one stricter CTA hierarchy:
  - Telegram primary
  - bot-flow/proof secondary
  - email backup tertiary
• homepage proof language now references the live DB preview directly instead of social-proof/waitlist framing
• core Pulse analytics views no longer default to Trader/execution prompts during the current weekly focus
• `/movers`, watchlist fallback windows, `/start`, `/help`, `/limits`, and free-plan followups now keep the user inside the Pulse loop first
• `/watchlist_list` now exposes compact list-health counts before the detailed rows, making review/cleanup decisions faster
• `public.analytics_core_health_latest` now acts as the compact read-only health surface for the canonical analytical core:
  - freshness lag
  - latest quote coverage
  - universe coverage
  - movers output health
• `scripts/growth/weekly_kpi_report.py` now includes a core-health block, so weekly review can see both:
  - growth funnel health
  - analytical core health

Operational implication:

• the canonical Layer II spine is now clearer:
  - `public.market_snapshots`
  - `public.market_universe`
  - `public.snapshot_health`
  - `public.top_movers_*`
  - `public.analytics_core_health_latest`
• the live Pulse runtime still stays on `bot.*`; this weekly slice does not re-plumb watchlist or alert source-of-truth
• growth and bot UX iterations can now use a shared weekly review without confusing a weak compatibility surface in `public` with a broken runtime

---

# Public Data Layer Contract Snapshot (2026-03-20)

The live Supabase `public` schema currently acts as both the Layer II analytical core and a compatibility shell for older user-facing derived objects.

Updated artifact:

• `docs/data_layer_public_schema_audit_2026-03-20.md`

Current contract understanding:

• the canonical analytical core is centered on:
  - `market_snapshots`
  - `market_universe`
  - `snapshot_health`
  - `top_movers_*`
• this core is healthy enough to support the current intelligence-layer product story
• the weakest part of `public` is not raw market data but the transitional application surface around it, especially:
  - watchlist-derived objects
  - alert-derived objects
  - legacy log tables
  - semantically weak metadata fields such as `markets.category`

Operational implication:

• future data-layer work should distinguish clearly between:
  - canonical analytical surfaces
  - legacy or compatibility surfaces
• cleanup priority should start with public watchlist and alert contracts before deeper changes to the raw market ingestion layer

---

# Homepage Conversion Contract: Telegram First, Email Backup (2026-03-20)

The EN homepage acquisition layer now treats Telegram activation as the only primary action and frames email explicitly as a secondary backup channel.

Updated artifact:

• `api/web/index.en.html`

Contract changes:

• hero and CTA copy now describe a concrete first-value path:
  - open the bot
  - add one market
  - get the move
• the CTA panel now includes a compact trust strip reinforcing lower-friction activation:
  - no signup required
  - one-tap open
  - email optional backup
• the supporting bullets now emphasize real acquisition pains:
  - too much manual dashboard scanning
  - movers + watchlist in one loop
  - quiet states instead of low-trust alert spam
• the email form remains below the Telegram CTA, but its helper copy now explicitly says:
  - email is for digest and updates
  - Telegram is the primary live loop

Operational implication:

• homepage changes should continue to optimize for `tg_click` first, not for email capture parity
• any future homepage CTA work must preserve the hierarchy:
  - Telegram primary
  - guide secondary
  - email backup tertiary
• visual changes on the homepage still need to stay inside the current dark/green terminal system defined by the active brand tokens

---

# EN SEO Page CTA Hierarchy Contract (2026-03-20)

The shared EN intent-page template now mirrors the homepage conversion order so search-entry pages do not drift into a softer or more ambiguous funnel.

Updated artifact:

• `api/main.py`

Contract changes:

• the shared `render_seo_page(...)` CTA block now includes a compact trust strip below the Telegram CTA:
  - no signup required
  - one-tap open
  - email backup only
• the shared CTA helper copy now explicitly frames email as:
  - backup for digest and launch updates
  - secondary to the Telegram live loop
• this contract applies across the EN acquisition pages built from the shared SEO template, so homepage and intent pages keep the same CTA hierarchy

Operational implication:

• landing and SEO-page conversion work should stay synchronized through the shared hierarchy:
  - Telegram primary
  - guide/support secondary
  - email tertiary
• future copy changes to EN intent pages should preserve this order rather than reintroducing email as an equal first-screen action

---

# Homepage Decision Panel Contract (2026-03-20)

The homepage hero-right CTA panel is now treated as a dedicated decision panel whose main job is to reduce `page_view -> tg_click` friction.

Updated artifact:

• `api/web/index.en.html`

Contract changes:

• the primary Telegram CTA now carries stronger immediacy (`Open Telegram Bot in 1 Tap`)
• guide/help remains present but is intentionally de-emphasized as an inline support link rather than a second full-width CTA block
• email capture is now visually isolated inside an optional backup shell
• the panel includes a compact proof line clarifying that the adjacent movers preview is fed from live DB data, not static marketing imagery

Operational implication:

• future homepage CTA experiments should keep the decision panel focused on one main click
• support/help and email backup can exist, but should not visually compete with the Telegram action at the same level
• if `tg_click/page_view` remains weak after this, the next iteration should target proof density and first-screen trust rather than re-expanding CTA choice

---

# Pulse Retention Surface Contract: Watchlist, Inbox, Review (2026-03-20)

The main analytics bot screens now act as retention surfaces with explicit next actions, rather than as isolated text views.

Updated artifact:

• `bot/main.py`

Contract changes:

• `/watchlist` and `/inbox` responses with real data now append short next-step guidance instead of ending immediately after the list of rows
• quiet-state `/watchlist` and `/inbox` now prefer Pulse-native action keyboards:
  - watchlist
  - inbox
  - review list
  - add market
  - threshold
  - remove closed, when relevant
• `/watchlist_list` now includes a compact state legend for:
  - `ready`
  - `partial`
  - `no_quotes`
  - `closed`

Operational implication:

• retention improvements in the analytics bot should keep the user inside the Pulse workflow first
• execution/trader surfaces should not be the default follow-up path for core analytics views during the current weekly Pulse focus
• future bot UX work should treat `/watchlist`, `/inbox`, and `/watchlist_list` as a connected loop:
  - see movement
  - review list health
  - adjust threshold or coverage

---

# Email Backup Retention Contract (2026-03-19)

The email layer now acts as a branded Pulse backup surface instead of a bare confirmation transport.

Updated artifacts:

• `api/main.py`
• `api/digest_job.py`
• `docs/social_pipeline.md`

Contract changes:

• confirmation emails now explicitly frame email as:
  - backup for digest and updates
  - secondary to the Telegram live loop
• confirm, invalid-confirm, and unsubscribe pages now render through a shared branded status-page helper
• welcome emails now reinforce the Pulse-first hierarchy and direct the user back into the Telegram bot
• digest emails now use a shared branded email shell and include:
  - summary framing
  - formatted alert list
  - CTA back into Pulse
  - unsubscribe path via `confirm_token`
• explicit system/email routes such as `/confirm` and `/unsubscribe` must stay registered above the generic `/{slug}` SEO route

Operational implication:

• email remains a supporting retention channel, not a primary acquisition surface
• the product story is now consistent across site -> Telegram -> email
• digest output is safer operationally because unsubscribe URLs now use the same token contract as the rest of the email system
• route ordering is now part of the site contract; otherwise generic SEO routing can silently break product-critical flows in production

---

# TG Activation First Funnel Contract (2026-03-19)

The weekly operating focus now treats the Pulse acquisition funnel as the primary system boundary. Trader remains deployed, but acquisition and measurement are now deliberately centered on Pulse.

Updated artifacts:

• `api/web/index.en.html`
• `api/main.py`
• `bot/main.py`
• `scripts/growth/weekly_kpi_report.py`

Contract changes:

• the homepage EN acquisition layer now prioritizes only the Pulse path:
  - primary CTA: Telegram bot
  - secondary CTA: email backup / waitlist
• Trader Alpha is no longer linked from the homepage search/intents hub during this weekly focus window
• EN SEO pages no longer append Trader Alpha into their related-link cluster
• `/telegram-bot` comparison content is now framed around:
  - dashboard overload
  - noisy alert feeds
  - signal trust
  rather than Pulse -> Trader expansion

Measurement additions:

• the Pulse bot now emits `event_type='watchlist_add'` into `app.site_events`
• event details include:
  - `app_user_id`
  - Telegram identity metadata
  - `market_id`
  - `outcome`
  - `live_state`
  - `previous_watchlist_count`
  - `first_watchlist_add`
  - `placement`
• this makes the intended weekly funnel measurable as real event stages:
  - `page_view`
  - `tg_click`
  - `tg_start`
  - `watchlist_add`

Operational implication:

• growth decisions this week should optimize the Pulse acquisition funnel first
• any Trader work is now out of scope unless it is a production bugfix
• KPI reporting should prefer event-based `watchlist_add` counts and use the older `bot.watchlist` proxy only as a cross-check

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

# Homepage Search-Hub Contract (2026-03-18)

The public English homepage now acts as a clearer crawl and intent-distribution hub for the acquisition layer.

Updated artifacts:

• `api/web/index.en.html`
• `docs/gsc_weekly_checklist_2026-03-18.md`

Contract additions:

• the homepage now links directly to the full EN acquisition cluster:
  - `/analytics`
  - `/signals`
  - `/telegram-bot`
  - `/top-movers`
  - `/watchlist-alerts`
  - `/dashboard`
  - `/how-it-works`
  - `/commands`
  - `/trader-bot`
• these links now carry small descriptive summaries, not just bare route labels
• the homepage now emits an `ItemList` JSON-LD block for the main search-entry pages

Operational implication:

• the crawl graph is less dependent on sitemap-only discovery
• the homepage becomes a stronger internal-link source for pages that feed Telegram activation and Trader handoff
• GSC review is now supported by an explicit weekly checklist instead of ad hoc manual memory

---

# JIT Social Queue Contract (2026-03-18)

The growth layer now has an explicit operator-facing execution queue for manual posting.

Updated artifacts:

• `scripts/growth/build_social_queue.py`
• `docs/social_pipeline.md`
• `docs/social_queue_latest.md`

Contract:

• the queue builder reads fresh/liquid candidates from `public.top_movers_latest`
• the queue builder applies the same freshness and liquidity constraints as the draft layer
• output is a single markdown file that maps:
  - current live move
  - post copy theme
  - video asset
  - posting order
• when the market window is too stale or too thin, the correct contract is:
  - generate queue
  - return `skip posting`
  - wait for a better window

Operational implication:

• social execution is now a repeatable loop rather than a collection of one-off manual decisions
• manual posting stays aligned with the same “signal > noise” rule as the product itself

---

# Daily Social Operator Contract (2026-03-18)

The social layer now has a single operator entrypoint.

Updated artifacts:

• `scripts/growth/run_social_cycle.sh`
• `docs/social_pipeline.md`
• `docs/social_daily_operator_routine_2026-03-18.md`

Contract:

• `run_social_cycle.sh` is the daily human-facing entrypoint for social execution
• it is responsible for:
  - loading `PG_CONN`
  - rebuilding `docs/social_queue_latest.md`
  - rebuilding `docs/social_drafts_latest.md`
  - returning one operator decision:
    - `POST`
    - `SKIP`
• the routine assumes fresh regeneration before every posting block, not once per day

Operational implication:

• social publishing is now a bounded operating procedure instead of a loose collection of scripts
• the operator does not need to remember flags or file names to decide whether the window deserves a post

---

# Telegram Start Attribution Contract (2026-03-18)

The Pulse bot now emits a measured Telegram-entry event when a user lands in `/start`.

Updated artifacts:

• `bot/main.py`
• `scripts/growth/weekly_kpi_report.py`

Contract:

• `/start` reads the optional deep-link payload from `context.args`
• the bot writes `event_type='tg_start'` into `app.site_events`
• event details include:
  - `start_payload`
  - `entrypoint`
  - Telegram identity metadata
  - current plan / threshold / watchlist context
• weekly KPI reporting now exposes:
  - total `tg_start`
  - `tg_start / tg_click`
  - `tg_start` split by payload

Operational implication:

• social and deep-link attribution now survives the handoff from site/X into Telegram
• we can compare which pain themes produce not just clicks, but actual product entry

---

# Pulse Quiet-State Guidance Contract (2026-03-18)

Quiet-state responses in the Pulse bot now include an explicit next-step layer.

Updated artifact:

• `bot/main.py`

Contract:

• `/watchlist` and `/inbox` quiet states now append a context-aware follow-up line
• the guidance branches on:
  - threshold-filtered candidates
  - closed markets parked in watchlist
  - active markets without quotes in both windows yet
  - empty watchlist

Operational implication:

• diagnostics remain visible, but the user is no longer left to infer the next move
• this supports post-start retention by reducing “the bot feels dead” moments

---

# Trader Readiness Surface Contract (2026-03-18)

The Trader bot now has a dedicated user-facing readiness surface.

Updated artifact:

• `trader_bot/main.py`

Contract:

• `/ready` is the single command for execution readiness
• it combines:
  - wallet status
  - signer summary
  - risk state
  - latest worker state if an order exists
• the reply keyboard now exposes this surface through a human label rather than forcing the user to infer it from `/connect`, `/risk`, and `/order`

Operational implication:

• the execution alpha path is easier to read as a sequence
• this reduces confusion around what still blocks the user after wallet connection

---

# Watchlist Review Status Contract (2026-03-18)

The Pulse bot now exposes per-market watchlist state in the list view.

Updated artifact:

• `bot/main.py`

Contract:

• `/watchlist_list` now resolves, per market:
  - lifecycle status (`active` / `closed`)
  - quote presence in `last`
  - quote presence in `prev`
• the command maps those fields to user-facing states:
  - `ready`
  - `partial`
  - `no_quotes`
  - `closed`

Operational implication:

• watchlist review is now an audit surface, not just a raw list of ids
• this supports retention by helping the user prune dead markets before the product feels broken

---

# Trader Ready Hand-Off Contract (2026-03-18)

The Trader bot now uses `/ready` as the explicit follow-up surface after low-information states.

Updated artifact:

• `trader_bot/main.py`

Contract:

• order-save confirmations now point users to `/ready`
• empty positions state now also points users to `/ready`

Operational implication:

• `/ready` becomes the canonical “what blocks me now?” surface
• this reduces command drift between wallet, order, and risk flows

---

# Trader Command-Tap Contract Fix (2026-03-18)

The readiness hand-off now respects Telegram command interaction semantics.

Updated artifact:

• `trader_bot/main.py`

Contract:

• `/ready` references that are intended for direct invocation should not be wrapped in `<code>`
• code formatting remains for examples and structured values, not for tappable next-step commands

Operational implication:

• the readiness command now behaves like a real next action inside Telegram instead of a copy-only snippet

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

---

# Recent Flow Adjustments (2026-03-18)

Pulse bot:

• `/watchlist_list` is now a review-and-act surface, not just a text dump
• action row after the list:
  - `Watchlist`
  - `Add market`
  - `Inbox`
  - `Top movers`
  - conditional `Remove closed`

Trader bot:

• `/connect` now auto-hands users into the signer flow when the wallet is still non-ready
• signer session creation/reuse no longer depends on the user discovering `/signer` separately
• this shortens the execution alpha path to:
  - `/connect <wallet>`
  - signer page
  - signed payload
  - manual alpha approval
  - `/ready`
• `/ready` and `/order` now expose the signer URL directly for non-ready wallets, so lifecycle review screens double as action surfaces

Pulse bot:

• `/start` now has two activation branches:
  - zero-watchlist users → onboarding picker / one-tap add
  - returning users with existing watchlist → resume flow with direct actions into `Watchlist`, `Inbox`, `Threshold`, `Top movers`, `Plan`

---

# Realtime Modernization Contract (2026-03-27)

## Why The Next Step Exists

The current analytical spine is still valuable:

- `public.market_snapshots`
- `public.market_universe`
- `public.snapshot_health`
- `public.top_movers_*`

But current user-facing analytics are still too dependent on batch-shaped timing:

- GitHub Actions is hourly backup
- the ingest worker cadence is still slower than product-grade “live” UX
- homepage proof, `/movers`, and watchlist/alert derivation still lean on bucketed history too early

So the next safe move is not a rewrite.

It is a new internal hot layer.

## Runtime Decision

We will not:

- make bot/site call Polymarket directly on every request
- replace Postgres as the historical backbone
- rewrite `bot.watchlist` this week
- delete legacy analytical surfaces first

We will:

- centralize live fetch in one worker
- write a hot internal read layer for product surfaces
- keep historical write-through into `public.market_snapshots`
- migrate reads one surface at a time

## Hot Data Contract V1

Planned hot surfaces:

- `public.hot_market_registry_latest`
- `public.hot_market_quotes_latest`
- `public.hot_top_movers_1m`
- `public.hot_top_movers_5m`
- `public.hot_watchlist_snapshot_latest`
- `public.hot_alert_candidates_latest`
- `public.hot_ingest_health_latest`

Meaning:

- `hot_market_registry_latest` = freshest active market metadata
- `hot_market_quotes_latest` = freshest quote state per market
- `hot_top_movers_*` = scored hot movers for 1m / 5m horizons
- `hot_watchlist_snapshot_latest` = fast per-user watchlist state from hot data
- `hot_alert_candidates_latest` = pre-threshold candidate alerts from hot data
- `hot_ingest_health_latest` = hot-layer freshness / coverage heartbeat

## Worker Boundary

The live worker should own:

- Gamma market/event pulls
- CLOB quote pulls
- hot registry writes
- hot quote writes
- hot movers computation
- hot watchlist snapshot computation
- hot alert candidate computation
- historical write-through to `public.market_snapshots`

The live worker should not own:

- Telegram delivery
- email delivery
- user command handling

## Planned Read Cutover Order

We keep migration additive and reversible.

Cutover order:

1. homepage live movers proof (`/api/live-movers-preview`)
2. bot `/movers`
3. watchlist latest state
4. alert candidate generation
5. inbox derivation

Rules:

- keep old reads alive during comparison
- do one surface at a time
- keep rollback available
- do not change the public bot command contract during cutover

## Compatibility Boundary

These surfaces remain valid during V1:

- `public.market_snapshots`
- `public.market_universe`
- `public.snapshot_health`
- `public.top_movers_*`
- `bot.watchlist_snapshot_latest`
- `bot.alerts_inbox_latest`

But the architectural direction is now explicit:

- historical analytics stay on the current analytical spine
- live user-facing reads progressively move to the new hot layer

## Parallelizable Workstreams

Safe parallel work:

- map read-path dependencies for homepage, `/movers`, watchlist, and inbox
- scaffold hot tables/views without switching reads
- build the live worker skeleton with heartbeat-only writes first
- define mover scoring gates and thresholds
- add clickable market links on the site
- add hot-layer operational reports

Unsafe to parallelize with a live cutover:

- deleting old views
- rewriting watchlist source of truth
- switching multiple product surfaces at once
- changing bot command contracts during the same rollout

## First Worker Skeleton Added

The first live-worker scaffold now exists beside the historical ingest path:

- `ingest/live_main.py`
- `ingest/live_worker.py`

Current behavior:

- reuses the current market coverage contract from the existing ingest path
- pulls the live market set through the same forced-id logic
- writes only the first hot tables:
  - `public.hot_market_registry_latest`
  - `public.hot_market_quotes_latest`
- prunes stale rows in those two tables

Current non-goals:

- no runtime cutover yet
- no `hot_top_movers_*` writes yet
- no `hot_watchlist_snapshot_latest` writes yet
- no `hot_alert_candidates_latest` writes yet

This is intentional.

The first worker step is meant to prove:

- a centralized hot ingest loop can run independently of the historical batch path
- hot registry/quote freshness can be observed safely
- the homepage preview cutover can happen later on a real hot base instead of a paper contract

Smoke state after first live run:

- migration `013_hot_data_contract_v1_scaffold.sql` is applied in the live DB
- `ingest/live_main.py` successfully wrote:
  - `public.hot_market_registry_latest`
  - `public.hot_market_quotes_latest`
- observed first live counts:
  - registry rows: `402`
  - quote rows: `402`
  - two-sided quotes: `293`
- `public.hot_ingest_health_latest` is now a working heartbeat over real rows

This means the first hot layer already exists in production data storage, even though no product read has been cut over yet.

## First Hot-Layer Ops Report Added

The hot layer now has its own operator-facing report:

- `scripts/hot_data_health_report.py`
- output: `docs/hot_data_health_latest.md`

Report contract:

- reads `public.hot_ingest_health_latest`
- augments it with direct counts from:
  - `public.hot_market_registry_latest`
  - `public.hot_market_quotes_latest`
  - `public.hot_watchlist_snapshot_latest`
  - `public.hot_alert_candidates_latest`

Interpretation rule:

- registry and quotes must be healthy now
- movers/watchlist/alert rows are allowed to stay empty until their worker publish phases are added

## Railway Runtime Split For Ingest

We now have an explicit runtime selector in the ingest path:

- `ingest/bootstrap.py`
- `ingest/Procfile` → `python bootstrap.py`

Runtime branches:

- `INGEST_RUNTIME=batch`
  - runs `ingest/worker.py`
  - keeps the historical batch/write-through path
- `INGEST_RUNTIME=live`
  - runs `ingest/live_worker.py`
  - keeps the new hot-layer heartbeat path

Why this shape is good:

- same source directory
- no duplicate deploy tree
- no forced rewrite of the current ingest service
- Railway can run both services in parallel with different env contracts

Current operational choice on the active Railway plan:

- because the plan hit the resource limit for provisioning a separate service,
  the existing `ingest` service should run `INGEST_RUNTIME=live`
- GitHub Actions keeps the historical/batch backup role
- this runtime has now been verified in production:
  - Railway deployment `8b13b91c-b02d-4047-9bf1-e989ae581af5` reached `SUCCESS`
  - logs show `live ingest worker started` plus successful `live ingest tick` writes
  - `docs/hot_data_health_latest.md` is now green for the V1-now surfaces
    (`public.hot_market_registry_latest` and `public.hot_market_quotes_latest`)

So the architecture stays the same in principle:

- live runtime on Railway
- batch/reconciliation in Actions

Only the service-count implementation detail changed.

## First Runtime Cutover Completed: Homepage Preview

The first additive read migration is now in place:

- `/api/live-movers-preview` in `api/main.py` reads the hot layer first
- it prefers:
  - `public.hot_market_registry_latest`
  - `public.hot_market_quotes_latest`
- it falls back to the legacy preview query only if the hot query yields no usable rows

Current homepage-preview gate policy:

- freshness <= `120s`
- liquidity >= `1000`
- spread <= `0.25`
- two-sided YES quote required
- market status must still be `active`

Comparison anchor during this phase:

- current value (`yes_mid_now`) comes from the hot quote table
- previous value (`yes_mid_prev`) still comes from the latest historical point at least ~5 minutes back in `public.market_snapshots`
- sparklines still use historical bucket points, with the current hot midpoint appended when it is newer than the last historical point

Why this is the correct first cut:

- homepage proof is the safest high-value reader to modernize first
- it benefits immediately from fresher “now” data
- it does not yet force mover-window publication or bot runtime changes
- legacy fallback keeps the hero resilient while the hot worker matures

## Second Hot Publish Phase Completed: `hot_top_movers_5m`

The live worker now publishes the first scored mover surface:

- `public.hot_top_movers_5m`

Current worker gate policy for this table:

- two-sided YES quote required
- market status must still be `active`
- liquidity >= `1000`
- spread <= `0.25`
- abs(delta) >= `0.005`

Current scoring rule:

- `score = abs(delta_mid) * 100 + ln(1 + liquidity)`

Why this matters:

- it turns the hot layer into a product-usable mover surface, not just a registry/quote heartbeat
- it keeps the selection resistant to zero-delta high-liquidity noise
- it gives us the right next migration target for `/movers`

Boundary still preserved:

- `/movers` has not been cut over yet
- legacy `public.top_movers_latest` remains the active runtime reader there until we compare overlap/order/freshness against `public.hot_top_movers_5m`
- this publish phase is now verified in production:
  - Railway deployment `e964e520-2012-4738-82a0-2b50f56382d0` reached `SUCCESS`
  - live logs show `movers_5m=` on ingest ticks
  - `docs/hot_data_health_latest.md` now reports non-zero `hot_movers_5m_count`

## `/movers` Comparison Decision: Hold

We now have an explicit comparison pass between:

- `public.hot_top_movers_5m`
- `public.top_movers_latest`

Artifacts:

- `scripts/compare_hot_vs_legacy_movers.py`
- `docs/hot_vs_legacy_movers_latest.md`

Current decision:

- do **not** cut over `/movers` yet

Why:

- observed overlap is still too weak for a safe runtime switch
- many top legacy rows are present in `public.hot_market_quotes_latest`, so this is not mainly a coverage failure
- the bigger difference is semantic:
  - legacy bucket movers still show large recent bucket jumps
  - the hot 5m surface often sees those markets after partial reversion, so their *current* actionable delta is smaller or filtered out

This is a real product decision point, not just a technical mismatch.

Before `/movers` cutover, we need to decide which surface should define “top movers”:

- latest bucket shock (`public.top_movers_latest`)
- or fresher current-action delta (`public.hot_top_movers_5m`)

## `/movers` Product Meaning Fixed

Decision artifact:

- `docs/movers_surface_decision_2026-03-27.md`

Decision:

- `/movers` is an action-first surface
- it should represent current live relevance, not just the largest completed bucket shock

Architectural consequence:

- `public.hot_top_movers_5m` is still the correct long-term target for `/movers`
- `public.top_movers_latest` remains:
  - comparison surface
  - migration fallback
  - possible future explicit "shock" surface if needed

So the remaining work before cutover is not “make hot look identical to legacy”.

It is:

- make hot sufficiently trustworthy for the action-first meaning of `/movers`

## `/movers` Calibration Insight

The comparison tooling now exposes `exclusion_reason` for legacy rows that do not survive the hot 5m publish gates.

Current dominant reason:

- `below_abs_delta_gate`

Meaning:

- the market is still covered in `public.hot_market_quotes_latest`
- quotes are often two-sided and liquid enough
- but the *current* 5m live move has already compressed below the action threshold

Architectural takeaway:

- the main semantic drift is currently caused by live reversion vs bucket shock, not by missing live coverage
- that is exactly the kind of difference we expect between an action-first surface and a shock-first surface

## First Gate Calibration Accepted

The first calibration step for `public.hot_top_movers_5m` is now accepted:

- `HOT_MOVERS_MIN_ABS_DELTA`
  - from `0.005`
  - to `0.003`

Why:

- comparison overlap improved materially
- the hot surface kept its action-first character
- the result looked good enough to support a safe hot-first cutover with fallback

## `/movers` Runtime Cutover Completed

After the first gate calibration, `/movers` now uses a safe runtime split:

- hot-first:
  - `public.hot_top_movers_5m`
- legacy fallback:
  - `public.top_movers_latest`

Implementation point:

- `fetch_top_movers_async()` in `bot/main.py`

Why this cutover is acceptable now:

- comparison overlap improved materially after lowering `HOT_MOVERS_MIN_ABS_DELTA` to `0.003`
- the hot surface now better matches the action-first product meaning of `/movers`
- fallback keeps the command resilient if the hot mover publish phase temporarily yields no rows
