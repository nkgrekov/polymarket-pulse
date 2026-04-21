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
  - markets `1919425` and `1919417`
  - classification: `legacy_stale_bucket`
  - meaning: hot saw current ready moves while the legacy bucket surface had not yet caught up
- the next classified `legacy_only` sample now also exists:
  - the same two markets later appeared as `legacy_only`
  - classification: `legacy_shock_reverted`
  - meaning: legacy still exposed the bucket shock after hot had already reclassified the current move as `below_threshold`

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
5. At least some `legacy_only` divergence is now explainable as bucket persistence after the live move has already cooled below threshold.

That means a blind hot-first cutover would be irresponsible for two separate reasons:

1. **Semantics**
   - `hot_only` shows that hot sees some actionable windows earlier or differently.
   - `legacy_only` shows that legacy still catches some watchlist alerts that hot would currently miss.
   - classified `hot_only` currently points toward real stale-bucket lag on legacy.
   - classified `legacy_only` currently points toward bucket shock persistence after live reversion.
   - together, that looks less like random disagreement and more like a genuine semantic split:
     - hot = current actionable live state
     - legacy = slower bucket-confirmed shock memory

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

Current evidence is now pointing more strongly toward this semantic split than toward an immediate hot-first push cutover.

## Fresh Follow-Up (2026-04-21)

The latest regenerated parity snapshot strengthens this conclusion instead of weakening it.

### Parity history refresh (last 7 days)

- `samples_total = 1887`
- `non_quiet_samples = 1190`
- `classified_non_quiet_samples = 987`
- `hot_only_samples = 215`
- `legacy_only_samples = 511`
- `both_non_quiet_samples = 464`
- `max_overlap_count = 5`

### What changed

1. The classified sample is now large enough to trust as an actual operating picture.
2. Overlap is real and frequent, so this is not a simple “hot and legacy never agree” story.
3. `legacy_only` still materially outweighs `hot_only`, so hot is not yet safe as a drop-in delivery replacement.
4. The mismatch vocabulary still points to the same semantic split:
   - `legacy_stale_bucket`
   - `legacy_shock_reverted`

### Current reading

- hot is clearly useful and often fresher
- legacy is clearly slower and noisier in some windows
- but legacy still owns a larger share of currently surfaced push-only cases

That keeps the recommendation unchanged:

- do **not** cut over push delivery to hot-first yet
- if we continue delivery work, the safest next move is a hybrid/fallback refinement path, not a blind replacement

## Practical Recommendation

The next useful implementation step is **not** the cutover itself.

The next useful implementation step is:

- add richer shadow diagnostics for non-quiet parity windows
- then review the actual mismatched markets

That is the smallest step that reduces uncertainty without risking user-facing alert quality.
