# Delivery Parity Snapshot (2026-04-15T14:19:07.462669+00:00)

Source:

- `bot.delivery_parity_log`

## Window

- hours: **168**

## Summary

- samples_total: **1919**
- non_quiet_samples: **577**
- classified_non_quiet_samples: **27**
- unclassified_non_quiet_samples: **550**
- hot_only_samples: **158**
- legacy_only_samples: **286**
- both_non_quiet_samples: **133**
- max_hot_ready_count: **2**
- max_legacy_watchlist_count: **2**
- max_overlap_count: **2**

## Latest Non-Quiet Sample

- sampled_at: **2026-04-15 14:14:50.859779+00:00**
- hot_ready_count: **0**
- legacy_watchlist_count: **2**
- overlap_count: **0**
- hot_only_count: **0**
- legacy_only_count: **2**
- top_hot_market_id: **none**
- top_legacy_market_id: **1919425**
- top_hot_abs_delta: **none**
- top_legacy_abs_delta: **0.09000000000000000000**

## Classification Totals

- legacy_stale_bucket: **34**
- legacy_shock_reverted: **2**

## Recent Hot-Only Examples

- sampled_at=2026-04-15 14:04:03.287209+00:00 | market_id=1919425 | classification=legacy_stale_bucket | delta_abs=0.06 | threshold_value=0.03 | live_state=ready | quote_ts=2026-04-15T14:02:52.862025+00:00
- sampled_at=2026-04-15 14:04:03.287209+00:00 | market_id=1919417 | classification=legacy_stale_bucket | delta_abs=0.04000000000000001 | threshold_value=0.03 | live_state=ready | quote_ts=2026-04-15T14:02:52.862025+00:00

## Recent Legacy-Only Examples

- sampled_at=2026-04-15 14:14:50.859779+00:00 | market_id=1919425 | classification=legacy_shock_reverted | abs_delta=0.09 | threshold_value=0.03 | candidate_state=below_threshold | live_state=ready | legacy_last_bucket=2026-04-15T14:05:00+00:00
- sampled_at=2026-04-15 14:14:50.859779+00:00 | market_id=1919417 | classification=legacy_shock_reverted | abs_delta=0.04 | threshold_value=0.03 | candidate_state=below_threshold | live_state=ready | legacy_last_bucket=2026-04-15T14:05:00+00:00

## Interpretation

- `hot_only_samples > 0` means the hot layer saw watchlist-ready candidates that legacy delivery did not expose in the same window.
- `legacy_only_samples > 0` means legacy delivery still surfaces watchlist alerts that the hot layer did not mark `ready`.
- `both_non_quiet_samples > 0` plus a healthy `max_overlap_count` is the strongest evidence for a safe hot-first delivery cutover.
- `Classification Totals` help separate semantic mismatch types from raw count drift so delivery decisions are based on reasons, not just volumes.
