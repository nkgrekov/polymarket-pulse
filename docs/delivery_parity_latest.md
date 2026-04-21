# Delivery Parity Snapshot (2026-04-21T14:48:49.758997+00:00)

Source:

- `bot.delivery_parity_log`

## Window

- hours: **168**

## Summary

- samples_total: **1887**
- non_quiet_samples: **1190**
- classified_non_quiet_samples: **987**
- unclassified_non_quiet_samples: **203**
- hot_only_samples: **215**
- legacy_only_samples: **511**
- both_non_quiet_samples: **464**
- max_hot_ready_count: **6**
- max_legacy_watchlist_count: **5**
- max_overlap_count: **5**

## Latest Non-Quiet Sample

- sampled_at: **2026-04-21 14:48:44.820914+00:00**
- hot_ready_count: **2**
- legacy_watchlist_count: **2**
- overlap_count: **2**
- hot_only_count: **0**
- legacy_only_count: **0**
- top_hot_market_id: **2007076**
- top_legacy_market_id: **2007076**
- top_hot_abs_delta: **0.06500000000000006**
- top_legacy_abs_delta: **0.12000000000000000000**

## Classification Totals

- legacy_shock_reverted: **12**
- legacy_stale_bucket: **12**

## Recent Hot-Only Examples

- sampled_at=2026-04-21 14:05:33.367293+00:00 | market_id=1919421 | classification=legacy_stale_bucket | delta_abs=0.050000000000000044 | threshold_value=0.03 | live_state=ready | quote_ts=2026-04-21T14:03:53.769871+00:00

## Recent Legacy-Only Examples

- sampled_at=2026-04-21 14:27:10.374951+00:00 | market_id=1919421 | classification=legacy_shock_reverted | abs_delta=0.05 | threshold_value=0.03 | candidate_state=below_threshold | live_state=ready | legacy_last_bucket=2026-04-21T14:10:00+00:00
- sampled_at=2026-04-21 14:16:20.123140+00:00 | market_id=2007076 | classification=legacy_shock_reverted | abs_delta=0.12 | threshold_value=0.03 | candidate_state=below_threshold | live_state=ready | legacy_last_bucket=2026-04-21T14:10:00+00:00

## Interpretation

- `hot_only_samples > 0` means the hot layer saw watchlist-ready candidates that legacy delivery did not expose in the same window.
- `legacy_only_samples > 0` means legacy delivery still surfaces watchlist alerts that the hot layer did not mark `ready`.
- `both_non_quiet_samples > 0` plus a healthy `max_overlap_count` is the strongest evidence for a safe hot-first delivery cutover.
- `Classification Totals` help separate semantic mismatch types from raw count drift so delivery decisions are based on reasons, not just volumes.
