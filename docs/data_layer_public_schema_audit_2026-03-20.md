# Polymarket Pulse — Public Data Layer Audit

Date:

`2026-03-20`

Scope:

Read-only audit of the live Supabase data layer with emphasis on the `public` schema as the analytical core for Layer II.

Context alignment:

• `manifest.md` still defines Polymarket Pulse primarily as the data and intelligence layer on top of Polymarket  
• current `progress.md` and `architecture.md` are focused on Telegram acquisition and retention loops  
• because of that, this audit treats `public` first as the analytical substrate and only secondarily as a user-facing product surface

---

## Executive Summary

The core analytical spine in `public` is healthy.

The strongest part of the schema is:

• `market_snapshots`  
• `market_universe`  
• `snapshot_health`  
• the movers views

These objects are fresh, internally coherent, and good enough to support the current Layer II intelligence story.

The weakest part of the schema is not raw market data, but the older user-facing derived layer:

• watchlist tables and views  
• alert views  
• legacy log surfaces  
• semantically weak metadata fields such as `markets.category`

So the right mental model today is:

`public` contains both the live analytical core and a noticeable transition/legacy shell around it.

---

## Live Snapshot

Checked around:

`2026-03-20 11:36 UTC`

Key live signals:

• latest `market_snapshots.ts_bucket`: `2026-03-20 11:30:00+00:00`  
• freshness lag at check time: `6.2 min`  
• 24h bucket count: `110`  
• max bucket gap in 24h: `15 min`  
• latest bucket rows: `396`  
• latest bucket `yes` quote coverage: `97.5%`  
• 7d average `yes` quote coverage: `96.56%`  
• `market_universe`: `200` rows, `198 auto / 2 manual`  
• universe coverage in latest and previous buckets: complete  
• orphan checks: `0`

---

## Public Schema Table

| Object | Status | Why it matters | Current state |
|---|---|---|---|
| `public.market_snapshots` | Green | Main live time-series source for market analytics | Healthy. Latest bucket is fresh, cadence is stable, and quote coverage is high enough for movers and live comparisons. |
| `public.markets` | Yellow | Main market catalog and metadata layer | Useful as a registry, but semantically weak for analytics. `category` is effectively collapsed to one value and most active rows are not token-complete. |
| `public.market_universe` | Green | Curated live subset that powers the actual analytical layer | Very clean. Current universe is complete, active-only, and fully covered by both latest and previous buckets. |
| `public.snapshot_health` | Green | Fast operational quality view over bucket health | Good operational surface. It correctly exposes bucket row counts and quote coverage without needing deep raw-table queries. |
| `public.top_movers_latest` | Green | Main current movers output used by the intelligence layer | Healthy and full. Produces a complete `200`-row current movers surface from the current live universe. |
| `public.top_movers_1h` | Green | Higher-signal short-horizon movers view | Useful and alive. Carries real movement signal and is a good candidate for alerts or public widgets. |
| `public.top_movers_24h` | Green | Longer-horizon movers summary | Useful, though naturally sparser than the short-horizon layer. Still analytically relevant. |
| `public.portfolio_snapshot_latest` | Yellow | Portfolio state view for user position analytics | Empty right now, but this looks like a product-usage gap rather than a broken derived view. |
| `public.user_positions` | Yellow | Basis for position-level and portfolio analytics | Structurally present, but not yet a live analytical surface in production usage. |
| `public.watchlist` | Red | Current user watchlist source according to downstream public views | Looks stale. Only `5` rows, and none of them are active, in-universe, or quote-covered enough to surface downstream. |
| `public.watchlist_markets` | Red | Older watchlist market pool | Large enough to be real (`3,734` rows), but current user-facing watchlist views do not seem to depend on it. Strong legacy smell. |
| `public.user_watchlist` | Yellow | Compatibility view intended to normalize watchlist access | Currently just proxies `watchlist`, so it inherits the staleness of that narrow base table. |
| `public.watchlist_snapshot_latest` | Red | User watchlist delta surface | Empty because the current watchlist rows do not intersect the active live analytical universe. This is structural drift, not just “low usage.” |
| `public.v_watchlist_tokens` | Yellow | Token lookup for watchlist-related flows | Potentially useful, but only as healthy as the watchlist contract underneath it. |
| `public.v_watchlist_movers_1h` | Yellow | Movers view scoped to watchlist | Same dependency problem as the rest of the watchlist layer. |
| `public.alerts_latest` | Red | Current alert output layer | Empty. The analytical core is alive, but the user-facing alert layer is not producing signal. |
| `public.watchlist_alerts_latest` | Red | Watchlist-scoped alert output | Empty and downstream from the stale watchlist plus dormant alert chain. |
| `public.alerts_inbox_latest` | Red | Last-mile inbox surface for delivered alerts | Empty, which means the public user-facing signal loop is effectively inactive. |
| `public.sent_alerts_log` | Yellow | Alert delivery history | Fine as a log surface, but current activity is very low, so it does not yet validate the alert product loop. |
| `public.sent_alerts_log_legacy` | Red | Historical legacy alert log | Looks like a pure legacy tail and adds confusion to the public schema surface. |
| `public.live_markets_latest` | Yellow | Supposed quick-access live market view | Misleadingly named. In practice it behaves more like a metadata slice than a true live quote surface. |
| `public.buckets_latest` | Green | Technical helper for latest bucket references | Healthy utility view. |
| `public.global_bucket_latest` | Green | Single latest-bucket anchor for derived views | Healthy utility view and important for keeping downstream logic consistent. |

---

## Updated Conclusion

If the question is whether the core data foundation is trustworthy enough for Layer II analytics, the answer is yes.

What to trust as core:

• `market_snapshots` as the main raw live source  
• `market_universe` as the filtered analytical working set  
• `snapshot_health` as the operational pulse  
• `top_movers_*` as the current main derived intelligence layer

What to treat as legacy or transitional:

• `watchlist` versus `watchlist_markets` split  
• `sent_alerts_log_legacy`  
• naming/contracts that imply “live” while exposing mostly metadata  
• metadata fields that look analytical but are not, especially `markets.category`

What to rebuild or clarify first:

1. the watchlist contract in `public`
2. the alert-generation and inbox chain on top of the healthy data core
3. the semantic metadata layer so analytics do not depend on regex over `question`
4. the schema surface itself, so live core objects and legacy helper objects are easier to distinguish

The key takeaway is simple:

The live market data core is in good shape.

The public schema around it is not yet a clean product API surface.

Right now it behaves more like a mix of:

• a solid analytical engine room  
• a partially stale transitional application layer

---

## Suggested Follow-Up

Without changing production behavior immediately, the most valuable next documentation or design steps would be:

1. define which `public` objects are canonical for Layer II analytics
2. mark which `public` objects are legacy or compatibility-only
3. specify the intended watchlist source of truth
4. define a small permanent data-quality checklist:
   - freshness
   - bucket cadence
   - quote coverage
   - universe coverage
   - alert output health
