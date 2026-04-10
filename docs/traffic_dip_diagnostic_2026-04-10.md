# Traffic Dip Diagnostic (2026-04-10)

This note captures what we can confirm from our own runtime, database, and Railway surfaces about the recent traffic dip.

## Scope

Checked from our side only:

• Railway deploy / runtime health
• internal telemetry in `app.site_events`
• bot / ingest / site logs
• manual crawl smoke against the public site

Not available in this pass:

• GA4 query data through MCP, because the configured analytics auth currently needs reauthentication
• GSC data, which still needs user-provided screenshots / exports

## Confirmed Findings

### 1. No fresh broad site outage this week

What we checked:

• homepage returned `200`
• recent `site` logs did not show a meaningful cluster of `500` / `502` / `503` / `504` / timeout failures
• recent `ingest` logs did not show a matching runtime failure pattern either

Conclusion:

• there is no evidence of a fresh whole-site outage pattern during the current week

### 2. The previous weekend Railway-plan outage still matters

Context:

• the Railway plan expiration that took down site + bot over the previous weekend remains the clearest recent uptime incident

Conclusion:

• part of the observed traffic softness can still plausibly be explained by that outage and its after-effects

### 3. Bot reliability is currently the strongest runtime-side weakness

What we found in `bot` logs:

• repeated `push_loop iteration failed`
• repeated `TimeoutError`
• observed across multiple windows from `2026-04-07` through `2026-04-10`

Why this matters:

• the push / retention loop is more fragile than site serving right now
• even if acquisition is already small, bot instability can reduce return behavior, perceived usefulness, and follow-on engagement

### 3a. The push-loop failure mode is now identified more precisely

The failures are not pointing at Telegram send instability first.

Confirmed in logs:

• repeated `db query retry=1/3 failed: canceling statement due to statement timeout`
• these warnings line up with later:
  - `push_loop iteration failed`
  - `TimeoutError`

Code path:

• `dispatch_push_alerts()` in `/Users/nikitagrekov/polymarket-pulse/bot/main.py`
• still reads the legacy delivery surface:
  - `bot.alerts_inbox_latest`
• parity also compares against that legacy path

Important implementation detail:

• the DB helper itself uses:
  - `connect_timeout = 10s`
  - `statement_timeout = 8000ms`
  - up to `3` retries
• but `dispatch_push_alerts()` wraps the query calls in:
  - `asyncio.wait_for(..., timeout=10.0)` for parity
  - `asyncio.wait_for(..., timeout=15.0)` for push candidates

Meaning:

• the outer async timeout can cut off the query helper before its own retry budget has a chance to complete
• so degraded DB windows become full push-loop failures more easily than they should

### 3b. The legacy watchlist delivery view is materially expensive

Read-only `EXPLAIN ANALYZE` showed:

• parity summary around `3.9s`
• push candidates around `1.9s`

The expensive side is not the hot table.

The expensive side is the legacy watchlist path under `bot.alerts_inbox_latest`, which still depends on:

• `bot.watchlist_alerts_latest`
• `bot.watchlist_snapshot_latest`
• `public.market_snapshots`
• `public.global_bucket_latest`

`bot.watchlist_snapshot_latest` still recomputes:

• latest bucket
• previous bucket
• per-market last/prev mids

from the large historical `market_snapshots` relation.

Interpretation:

• push delivery is still paying the historical-bucket tax on every loop
• this is consistent with the observed statement timeout failures
• it also fits the current architecture, because push delivery has deliberately remained on the legacy path while read surfaces already moved to hot-first

### 4. Internal telemetry shows a real low-traffic week

Read-only DB check of `app.site_events`:

• `2026-04-10`: `4` `page_view`
• `2026-04-09`: `11` `page_view`
• `2026-04-08`: `10` `page_view`
• `2026-04-07`: `2` `page_view`
• `2026-04-06`: `18` `page_view`
• `2026-03-30`: `22` `page_view`

Conclusion:

• the dip is not just a feeling; our own low-volume telemetry shows a real trough, especially on `2026-04-07`

### 5. Telemetry quality is weaker than intended

Important finding:

• `event_type='page_view'` currently persists with `path='/api/events'`
• actual page/surface context mainly survives in `details.placement`

Recent placement samples still show life:

• `page`
• `hero_panel`
• `proof_bridge`
• `seo_analytics`
• `seo_telegram-bot`
• `seo_bridge`

Conclusion:

• this is not a total telemetry blackout
• but it does mean page-level diagnosis is much weaker than it should be

### 6. No obvious Google crawl block from our side

Manual smoke:

• homepage returned `200` for a browser-like UA
• homepage returned `200` for `Googlebot`
• `/robots.txt` returned `200` for `Googlebot`

Conclusion:

• no direct evidence yet that Googlebot is being blocked by the site runtime

## Working Interpretation

From our side, the traffic dip currently looks like a mix of:

• the previous weekend Railway outage
• genuinely very small top-of-funnel volume
• current bot push-loop instability on recent days
• incomplete measurement clarity because `page_view.path` is not preserving the real page path

What it does **not** currently look like:

• a fresh whole-site serving outage this week
• a full tracking blackout
• an obvious Googlebot block

## Best Next Checks

### Runtime / product side

1. De-risk `dispatch_push_alerts()` before any full hot-delivery cutover:
   - make parity failure non-fatal
   - stop nesting tight `asyncio.wait_for` around a helper that already has DB retry/timeout behavior
   - reduce the amount of legacy watchlist recomputation done on every push loop
2. Preserve real page context in `app.site_events` for `page_view`, not just `/api/events`

### Acquisition side

Need user-provided data next:

1. GSC top queries
2. GSC top pages
3. GA4 landing pages
4. GA4 `tg_click` breakdown if available

Those are required to separate:

• true search / acquisition drop
from
• runtime-side degradation and measurement ambiguity
