# Data Core Contract (2026-03-23)

This document fixes the current Layer II data contract without changing the live Pulse runtime.

## Canonical Analytical Core

These are the objects we currently treat as the trustworthy analytical spine:

- `public.market_snapshots`
- `public.market_universe`
- `public.snapshot_health`
- `public.top_movers_latest`
- `public.top_movers_1h`
- `public.top_movers_24h`
- `public.analytics_core_health_latest`

What they mean:

- `market_snapshots` is the raw live time-series source.
- `market_universe` is the curated active-only working set used by the analytics layer.
- `snapshot_health` is the operational pulse for bucket row-count and quote coverage.
- `top_movers_*` are the main derived intelligence surfaces.
- `analytics_core_health_latest` is the compact read-only health summary for weekly review.

## Compatibility / Transitional Shell

The following areas still exist, but should not be treated as the canonical analytical core:

- `public.watchlist*`
- `public.alerts*`
- `public.v_watchlist_tokens`
- metadata fields in `public.markets` that look analytical but are not, especially `category`

These surfaces can still be useful, but they are not the source of truth for the live analytical spine.

## Product Runtime Boundary

Important distinction:

- the canonical analytical core lives in `public`
- the current Pulse product runtime for watchlist / inbox / alert delivery remains on the `bot.*` contour

That means:

- we can harden the analytical core without rewriting the live Pulse runtime
- we should not treat weak `public` watchlist/alert surfaces as a reason to refactor the product loop this week

## Weekly Data-Quality Checklist

Use `public.analytics_core_health_latest` as the compact weekly review surface.

Minimum checks:

- latest bucket freshness lag
- latest bucket row count
- latest yes-quote coverage
- universe coverage in latest bucket
- universe coverage in previous bucket
- movers row counts for latest / 1h / 24h
- non-zero movers presence for latest / 1h / 24h

## Explicit Non-Goals This Week

- no migration of Pulse runtime from `bot.*` to `public.*`
- no rewrite of `public.watchlist*`
- no rewrite of `public.alerts*`
- no semantic taxonomy migration yet

This week is for hardening and clarifying the core, not re-plumbing the live bot.
