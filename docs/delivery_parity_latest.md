# Delivery Parity Snapshot (2026-04-27T12:30:33.348944+00:00)

Source:

- `bot.delivery_parity_log`

## Window

- hours: **168**

## Summary

- samples_total: **1887**
- non_quiet_samples: **999**
- classified_non_quiet_samples: **993**
- unclassified_non_quiet_samples: **6**
- hot_only_samples: **105**
- legacy_only_samples: **488**
- both_non_quiet_samples: **406**
- max_hot_ready_count: **6**
- max_legacy_watchlist_count: **5**
- max_overlap_count: **4**

## Latest Non-Quiet Sample

- sampled_at: **2026-04-25 21:54:59.223341+00:00**
- hot_ready_count: **0**
- legacy_watchlist_count: **1**
- overlap_count: **0**
- hot_only_count: **0**
- legacy_only_count: **1**
- top_hot_market_id: **none**
- top_legacy_market_id: **1919425**
- top_hot_abs_delta: **none**
- top_legacy_abs_delta: **0.03000000000000000000**

## Decision Readout

- Verdict: **keep legacy delivery as primary**.
- Reason: legacy-only windows still materially outweigh hot-only windows.
- Classification coverage: **99.4%** of non-quiet samples.
- Main classified reason: **legacy_shock_reverted**.
- Delivery semantics: unchanged; this report is evidence for the next decision, not a runtime cutover.

## Classification Totals

- legacy_shock_reverted: **1145**
- legacy_stale_bucket: **581**

## Recent Hot-Only Examples

- sampled_at=2026-04-25 18:35:04.510590+00:00 | market_id=1919425 | classification=legacy_stale_bucket | delta_abs=0.030000000000000027 | threshold_value=0.03 | live_state=ready | quote_ts=2026-04-25T18:33:53.929039+00:00

## Recent Legacy-Only Examples

- sampled_at=2026-04-25 21:54:59.223341+00:00 | market_id=1919425 | classification=legacy_shock_reverted | abs_delta=0.03 | threshold_value=0.03 | candidate_state=below_threshold | live_state=ready | legacy_last_bucket=2026-04-25T20:55:00+00:00

## Interpretation

- `hot_only_samples > 0` means the hot layer saw watchlist-ready candidates that legacy delivery did not expose in the same window.
- `legacy_only_samples > 0` means legacy delivery still surfaces watchlist alerts that the hot layer did not mark `ready`.
- `both_non_quiet_samples > 0` plus a healthy `max_overlap_count` is the strongest evidence for a safe hot-first delivery cutover.
- `Classification Totals` help separate semantic mismatch types from raw count drift so delivery decisions are based on reasons, not just volumes.
