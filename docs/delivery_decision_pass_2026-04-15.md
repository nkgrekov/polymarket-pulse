# Delivery Decision Pass — 2026-04-15

## Question

Should push delivery move to hot-first now?

## Evidence

### Parity history (last 7 days)

- `samples_total = 1918`
- `non_quiet_samples = 570`
- `hot_only_samples = 133`
- `legacy_only_samples = 294`
- `both_non_quiet_samples = 143`

### Recent examples

- some windows show full overlap:
  - `hot_ready=1`
  - `legacy_watchlist=1`
  - `overlap=1`
- some windows show `hot_only`
- some windows show `legacy_only`
- the first richer post-upgrade non-quiet sample already produced one explainable `hot_only` case:
  - market `1919425`
  - `delta_abs ~= 0.04`
  - classification: `legacy_stale_bucket`
  - meaning: hot saw a current ready move while the legacy bucket surface had not yet caught up

### Runtime reliability

- `bot` push loop is healthier than before the hardening pass
- but the legacy path still intermittently hits:
  - `statement timeout`
  - `push_loop iteration failed`
  - `TimeoutError`

## Interpretation

This is no longer a quiet-window problem.

We now have enough evidence to say:

1. The hot layer is real and product-meaningful.
2. Legacy delivery is also still surfacing alerts that hot does not always mark `ready`.
3. The two surfaces are not yet interchangeable.
4. At least some `hot_only` divergence is already explainable as a freshness lead rather than random hot-layer noise.

That means a blind hot-first cutover would be irresponsible for two separate reasons:

1. **Semantics**
   - `hot_only` shows that hot sees some actionable windows earlier or differently.
   - `legacy_only` shows that legacy still catches some watchlist alerts that hot would currently miss.
   - the first classified `hot_only` case points toward a real stale-bucket lag on legacy, which is encouraging for hot, but still not enough to justify a cutover alone.

2. **Reliability**
   - the legacy path is still operationally expensive and occasionally stalls the loop
   - but hot is not yet parity-clean enough to replace it outright

## Decision

Do **not** switch push delivery to hot-first yet.

Current best posture:

- keep user-facing read surfaces hot-first
- keep push delivery on legacy for now
- treat the delivery decision as a **semantic narrowing problem**, not just an infra migration problem

## Safest Next Move

Run a shadow-delivery calibration step before any cutover:

1. persist richer parity diagnostics for non-quiet windows
2. inspect which specific markets generate:
   - `hot_only`
   - `legacy_only`
3. classify those mismatches into buckets:
   - hot is correctly earlier
   - legacy is noisy/stale
   - hot is too strict
   - hot is missing a valid case

Only after that should we choose one of these paths:

### Path A — hot-first with fallback

Use only if:

- `legacy_only` becomes small and explainable
- hot mismatches mostly look product-correct

### Path B — semantic split

If divergence remains meaningful:

- keep push delivery on legacy longer
- or split concepts explicitly:
  - hot = live actionable tape
  - legacy = slower bucket-confirmed alert loop

## Practical Recommendation

The next useful implementation step is **not** the cutover itself.

The next useful implementation step is:

- add richer shadow diagnostics for non-quiet parity windows
- then review the actual mismatched markets

That is the smallest step that reduces uncertainty without risking user-facing alert quality.
