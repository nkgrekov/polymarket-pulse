# Delivery Parity Snapshot (2026-04-15T11:41:48.066778+00:00)

Source:

- `bot.delivery_parity_log`

## Window

- hours: **168**

## Summary

- samples_total: **1919**
- non_quiet_samples: **571**
- hot_only_samples: **133**
- legacy_only_samples: **296**
- both_non_quiet_samples: **142**
- max_hot_ready_count: **2**
- max_legacy_watchlist_count: **2**
- max_overlap_count: **1**

## Latest Non-Quiet Sample

- sampled_at: **2026-04-15 11:15:09.632598+00:00**
- hot_ready_count: **0**
- legacy_watchlist_count: **2**
- overlap_count: **0**
- hot_only_count: **0**
- legacy_only_count: **2**
- top_hot_market_id: **none**
- top_legacy_market_id: **1919425**
- top_hot_abs_delta: **none**
- top_legacy_abs_delta: **0.10000000000000000000**

## Classification Totals

- none

## Recent Hot-Only Examples

- none

## Recent Legacy-Only Examples

- none

## Interpretation

- `hot_only_samples > 0` means the hot layer saw watchlist-ready candidates that legacy delivery did not expose in the same window.
- `legacy_only_samples > 0` means legacy delivery still surfaces watchlist alerts that the hot layer did not mark `ready`.
- `both_non_quiet_samples > 0` plus a healthy `max_overlap_count` is the strongest evidence for a safe hot-first delivery cutover.
- `Classification Totals` help separate semantic mismatch types from raw count drift so delivery decisions are based on reasons, not just volumes.
