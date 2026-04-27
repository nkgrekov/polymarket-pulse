# Delivery Parity Snapshot (2026-04-27T12:54:57.898466+00:00)

Source:

- `bot.delivery_parity_log`

## Window

- hours: **168**

## Summary

- samples_total: **1887**
- non_quiet_samples: **994**
- classified_non_quiet_samples: **988**
- unclassified_non_quiet_samples: **6**
- hot_only_samples: **105**
- legacy_only_samples: **486**
- both_non_quiet_samples: **403**
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

- legacy_shock_reverted: **1136**
- legacy_stale_bucket: **576**

## Top Hot-Only Mismatch Markets

- market_id=1919417 | classification=legacy_stale_bucket | samples=185 | max_abs_delta=0.0800 | threshold=0.0300 | current=closed | candidate_states=closed | watchlist_rows=3 | last_seen=2026-04-21 15:42:33.213927+00:00 | question=US x Iran permanent peace deal by April 22, 2026?
- market_id=2007076 | classification=legacy_stale_bucket | samples=114 | max_abs_delta=0.1200 | threshold=0.0300 | current=closed | candidate_states=closed | watchlist_rows=1 | last_seen=2026-04-24 10:44:57.884725+00:00 | question=Will the price of Bitcoin be above $76,000 on April 24?
- market_id=1919421 | classification=legacy_stale_bucket | samples=114 | max_abs_delta=0.1100 | threshold=0.0300 | current=active | candidate_states=below_threshold | watchlist_rows=1 | last_seen=2026-04-24 17:13:32.206378+00:00 | question=US x Iran permanent peace deal by April 30, 2026?
- market_id=1919425 | classification=legacy_stale_bucket | samples=113 | max_abs_delta=0.1400 | threshold=0.0300 | current=active | candidate_states=below_threshold | watchlist_rows=1 | last_seen=2026-04-25 18:35:04.510590+00:00 | question=US x Iran permanent peace deal by May 31, 2026?

## Top Legacy-Only Mismatch Markets

- market_id=2007076 | classification=legacy_shock_reverted | samples=358 | max_abs_delta=0.1800 | threshold=0.0300 | current=closed | candidate_states=closed | watchlist_rows=1 | last_seen=2026-04-24 12:04:18.788793+00:00 | question=Will the price of Bitcoin be above $76,000 on April 24?
- market_id=1919425 | classification=legacy_shock_reverted | samples=271 | max_abs_delta=0.1100 | threshold=0.0300 | current=active | candidate_states=below_threshold | watchlist_rows=1 | last_seen=2026-04-25 21:54:59.223341+00:00 | question=US x Iran permanent peace deal by May 31, 2026?
- market_id=1919421 | classification=legacy_shock_reverted | samples=259 | max_abs_delta=0.1100 | threshold=0.0300 | current=active | candidate_states=below_threshold | watchlist_rows=1 | last_seen=2026-04-24 18:01:43.477507+00:00 | question=US x Iran permanent peace deal by April 30, 2026?
- market_id=1919417 | classification=legacy_shock_reverted | samples=163 | max_abs_delta=0.0650 | threshold=0.0300 | current=closed | candidate_states=closed | watchlist_rows=3 | last_seen=2026-04-21 17:14:54.874219+00:00 | question=US x Iran permanent peace deal by April 22, 2026?

## Recent Hot-Only Examples

- sampled_at=2026-04-25 18:35:04.510590+00:00 | market_id=1919425 | classification=legacy_stale_bucket | delta_abs=0.030000000000000027 | threshold_value=0.03 | live_state=ready | quote_ts=2026-04-25T18:33:53.929039+00:00

## Recent Legacy-Only Examples

- sampled_at=2026-04-25 21:54:59.223341+00:00 | market_id=1919425 | classification=legacy_shock_reverted | abs_delta=0.03 | threshold_value=0.03 | candidate_state=below_threshold | live_state=ready | legacy_last_bucket=2026-04-25T20:55:00+00:00

## Interpretation

- `hot_only_samples > 0` means the hot layer saw watchlist-ready candidates that legacy delivery did not expose in the same window.
- `legacy_only_samples > 0` means legacy delivery still surfaces watchlist alerts that the hot layer did not mark `ready`.
- `both_non_quiet_samples > 0` plus a healthy `max_overlap_count` is the strongest evidence for a safe hot-first delivery cutover.
- `Classification Totals` help separate semantic mismatch types from raw count drift so delivery decisions are based on reasons, not just volumes.
- `current=closed` in top mismatch markets means the historical mismatch came from a market that has since exited live delivery.
- `current=active` plus `candidate_states=below_threshold` means the market is still tracked, but hot currently sees no threshold-clearing move.
