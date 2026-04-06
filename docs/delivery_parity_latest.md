# Delivery Parity Snapshot (2026-04-06T10:04:44.176187+00:00)

Source:

- `bot.delivery_parity_log`

## Window

- hours: **24**

## Summary

- samples_total: **2**
- non_quiet_samples: **0**
- hot_only_samples: **0**
- legacy_only_samples: **0**
- both_non_quiet_samples: **0**
- max_hot_ready_count: **0**
- max_legacy_watchlist_count: **0**
- max_overlap_count: **0**

## Latest Non-Quiet Sample

- none

## Interpretation

- `hot_only_samples > 0` means the hot layer saw watchlist-ready candidates that legacy delivery did not expose in the same window.
- `legacy_only_samples > 0` means legacy delivery still surfaces watchlist alerts that the hot layer did not mark `ready`.
- `both_non_quiet_samples > 0` plus a healthy `max_overlap_count` is the strongest evidence for a safe hot-first delivery cutover.
