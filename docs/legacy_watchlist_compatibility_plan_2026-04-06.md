# Legacy Watchlist Compatibility Plan (2026-04-06)

## Goal

Document the smallest repo-managed path to retire legacy watchlist surfaces later without breaking ingest or the bot.

This is a compatibility plan only.

No schema or runtime change is proposed here.

## Confirmed Current Dependency

`/Users/nikitagrekov/polymarket-pulse/ingest/main.py` still reads two legacy public surfaces directly:

1. `public.user_watchlist`
- function: `fetch_watchlist_market_ids()`
- query:
  - `select market_id from public.user_watchlist where user_id=%s`

2. `public.user_positions`
- function: `fetch_position_market_ids()`
- query:
  - `select distinct market_id from public.user_positions where user_id=%s`

These are used to build the manual/position coverage inputs that flow into:

- `refresh_market_universe(...)`
- `try_refresh_market_universe(...)`

So the ingest path still depends on legacy public compatibility, even though the user-facing product has largely moved to `bot.*` and hot-layer reads.

## Why We Should Not Rip Them Out

Because this would break the current ingest contract:

- manual watchlist coverage would disappear
- position-aware coverage would disappear
- `refresh_market_universe()` would stop reflecting those legacy user-specific sources

That means the next cleanup must be compatibility-first, not delete-first.

## Smallest Safe Repo-Managed Plan

### Phase A. Freeze the Compatibility Contract

Treat these as the only legacy inputs that ingest is still allowed to consume:

- `public.user_watchlist`
- `public.user_positions`

Everything else in the old watchlist family should be treated as non-canonical unless explicitly needed:

- `public.watchlist`
- `public.watchlist_markets`

### Phase B. Introduce a Repo-Managed Compatibility View Later

When we are ready to retire legacy base tables, the smallest safe move is:

- keep ingest reading the same shape
- but change the source behind that shape

Preferred compatibility target:

- keep `public.user_watchlist` available as the ingest-facing compatibility surface
- back it with repo-managed projection from the modern source of truth later

Likewise:

- keep `public.user_positions` until a real replacement exists

This is safer than rewriting ingest and cleanup in one step.

### Phase C. Separate Base Tables From Compatibility Names

Future order:

1. define the modern canonical watchlist source
   - today that is functionally closer to `bot.watchlist`
2. project that source into a compatibility surface shaped like `public.user_watchlist`
3. migrate ingest reads only after that projection is stable
4. only then retire:
   - `public.watchlist`
   - `public.watchlist_markets`

## Why `public.watchlist` Should Not Be Retired First

Because the old family is messy:

- `public.watchlist`
- `public.user_watchlist`
- `public.watchlist_markets`

and they do not all mean the same thing.

The safest approach is:

- first preserve the ingest-facing API shape
- then reduce the base-table sprawl

## Recommended Cleanup Order Later

1. keep `public.user_watchlist` and `public.user_positions` intact for now
2. inventory all remaining reads of:
   - `public.watchlist`
   - `public.watchlist_markets`
3. define a repo-managed compatibility projection for `public.user_watchlist`
4. switch ingest to that projection without changing its external query shape
5. only then archive or remove:
   - `public.watchlist`
   - `public.watchlist_markets`

## Practical Rule

Until a compatibility projection exists:

- `public.user_watchlist` is legacy, but still operationally required
- `public.user_positions` is legacy, but still operationally required
- `public.watchlist` and `public.watchlist_markets` are cleanup candidates, not immediate delete candidates
