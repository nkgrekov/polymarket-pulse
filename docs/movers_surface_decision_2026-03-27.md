# Movers Surface Decision (2026-03-27)

This document fixes the product meaning of `/movers` before the runtime cutover.

## Decision

`/movers` should be an **action-first** surface, not a legacy bucket-shock leaderboard.

That means:

- show markets whose move is still visible in the current live quote state
- prefer freshness and tradability over historical shock magnitude
- accept that some large legacy bucket jumps will disappear if the market has already reverted

## Why

The comparison pass between:

- `public.hot_top_movers_5m`
- `public.top_movers_latest`

showed a real semantic difference:

- legacy often surfaces the largest bucket shock
- hot 5m often surfaces the markets that are still moving *now*

Many strong legacy rows were already present in:

- `public.hot_market_quotes_latest`

but were absent from:

- `public.hot_top_movers_5m`

because the current live delta had already compressed or reverted.

That is not a data-loss bug.

It is the difference between:

- "what just shocked the last bucket"
- and
- "what still looks actionable right now"

For Pulse, the second meaning is more aligned with the product.

## Product Contract

When a user opens `/movers`, they should be able to interpret it as:

- the strongest currently tradable or watch-worthy moves
- filtered for live quality
- honest about quiet states

They should **not** have to interpret it as:

- a forensic replay of the largest completed bucket jump

So `/movers` should optimize for:

1. current live relevance
2. quote quality
3. sufficient liquidity
4. understandable delta

not for:

1. maximum historical bucket shock at any cost

## Consequence For Legacy

`public.top_movers_latest` remains valuable, but its role changes:

- analytical comparison surface
- fallback runtime surface during migration
- possible future "shock" surface if we want one explicitly

It should not automatically define the user-facing meaning of `/movers`.

## Consequence For Hot Layer

`public.hot_top_movers_5m` is the correct long-term target for `/movers`, but only after it is stable enough.

That means:

- stable non-zero population on repeated ticks
- sane overlap with legacy on obviously important rows
- no obvious garbage from zero-delta liquidity or one-sided quotes
- no surprising omissions caused by worker bugs

## Cutover Rule

We do **not** cut over `/movers` just because hot data exists.

We cut over `/movers` when both conditions hold:

1. the hot surface matches the intended product meaning better than legacy
2. the remaining differences are explainable as freshness/actionability improvements, not data-quality failures

## Next Implementation Step

Do not switch `/movers` yet.

Next:

1. improve or calibrate `public.hot_top_movers_5m` until the comparison report looks intentionally different, not suspiciously different
2. then switch `/movers` to hot-first with legacy fallback

## Summary

`/movers` is now defined as:

- **current actionable movers**

not:

- **largest recent bucket shocks**
