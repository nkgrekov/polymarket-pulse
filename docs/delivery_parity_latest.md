# Delivery Parity Snapshot (2026-04-30T11:44:30.123358+00:00)

Source:

- `bot.delivery_parity_log`

## Window

- hours: **168**

## Summary

- samples_total: **1912**
- non_quiet_samples: **819**
- classified_non_quiet_samples: **816**
- unclassified_non_quiet_samples: **3**
- hot_only_samples: **26**
- legacy_only_samples: **620**
- both_non_quiet_samples: **173**
- max_hot_ready_count: **4**
- max_legacy_watchlist_count: **9**
- max_overlap_count: **4**

## Latest Non-Quiet Sample

- sampled_at: **2026-04-30 11:40:25.980770+00:00**
- hot_ready_count: **0**
- legacy_watchlist_count: **2**
- overlap_count: **0**
- hot_only_count: **0**
- legacy_only_count: **2**
- top_hot_market_id: **none**
- top_legacy_market_id: **2036170**
- top_hot_abs_delta: **none**
- top_legacy_abs_delta: **0.29500000000000000000**

## Decision Readout

- Verdict: **keep legacy delivery as primary**.
- Reason: legacy-only windows still materially outweigh hot-only windows.
- Classification coverage: **99.6%** of non-quiet samples.
- Main classified reason: **hot_missing_quote**.
- Delivery semantics: unchanged; this report is evidence for the next decision, not a runtime cutover.

## Operational Readout

- hot_only_closed_samples: **29**
- legacy_only_closed_samples: **117**
- hot_only_active_below_threshold_samples: **40**
- legacy_only_active_below_threshold_samples: **109**
- hot_only_date_passed_active_samples: **0**
- legacy_only_date_passed_active_samples: **0**
- distinct_top_mismatch_markets: **8**

- Recommendation: Next safest investigation is hot quote coverage for live watchlist markets; delivery semantics should stay unchanged until `hot_missing_quote` stops dominating.
- Concentration: Mismatch remains concentrated in a small set of recurring markets (1919421, 1919425, 2007076, 2086943).

## Classification Totals

- hot_missing_quote: **1424**
- legacy_shock_reverted: **402**
- legacy_stale_bucket: **111**
- unknown: **18**

## Top Hot-Only Mismatch Markets

- market_id=1919425 | classification=legacy_stale_bucket | samples=42 | max_abs_delta=0.1400 | threshold=0.0300 | current=active | candidate_states=ready | watchlist_rows=1 | last_seen=2026-04-25 18:35:04.510590+00:00 | question=US x Iran permanent peace deal by May 31, 2026?
- market_id=1919421 | classification=legacy_stale_bucket | samples=40 | max_abs_delta=0.1100 | threshold=0.0300 | current=active | candidate_states=below_threshold | watchlist_rows=1 | last_seen=2026-04-24 17:13:32.206378+00:00 | question=US x Iran permanent peace deal by April 30, 2026?
- market_id=2007076 | classification=legacy_stale_bucket | samples=29 | max_abs_delta=0.1200 | threshold=0.0300 | current=closed | candidate_states=closed | watchlist_rows=1 | last_seen=2026-04-24 10:44:57.884725+00:00 | question=Will the price of Bitcoin be above $76,000 on April 24?

## Top Legacy-Only Mismatch Markets

- market_id=2086943 | classification=hot_missing_quote | samples=314 | max_abs_delta=0.2850 | threshold=none | current=active | candidate_states=none | watchlist_rows=1 | last_seen=2026-04-30 06:43:55.738145+00:00 | question=Will the price of XRP be between $1.80 and $1.90 on May 3?
- market_id=2086897 | classification=hot_missing_quote | samples=253 | max_abs_delta=0.3150 | threshold=none | current=active | candidate_states=none | watchlist_rows=1 | last_seen=2026-04-30 11:40:25.980770+00:00 | question=Will the price of Solana be between $80 and $90 on May 3?
- market_id=2086903 | classification=hot_missing_quote | samples=239 | max_abs_delta=0.4795 | threshold=none | current=active | candidate_states=none | watchlist_rows=1 | last_seen=2026-04-29 18:50:58.454567+00:00 | question=Will the price of Solana be between $110 and $120 on May 3?
- market_id=2036170 | classification=hot_missing_quote | samples=216 | max_abs_delta=0.2950 | threshold=none | current=active | candidate_states=none | watchlist_rows=1 | last_seen=2026-04-30 11:40:25.980770+00:00 | question=Gaza flotilla enters Israeli waters by May 31?
- market_id=2007076 | classification=legacy_shock_reverted | samples=117 | max_abs_delta=0.1100 | threshold=0.0300 | current=closed | candidate_states=closed | watchlist_rows=1 | last_seen=2026-04-24 12:04:18.788793+00:00 | question=Will the price of Bitcoin be above $76,000 on April 24?
- market_id=1919421 | classification=legacy_shock_reverted | samples=109 | max_abs_delta=0.4970 | threshold=0.0300 | current=active | candidate_states=below_threshold | watchlist_rows=1 | last_seen=2026-04-28 18:53:14.986188+00:00 | question=US x Iran permanent peace deal by April 30, 2026?
- market_id=1919425 | classification=legacy_shock_reverted | samples=90 | max_abs_delta=0.1100 | threshold=0.0300 | current=active | candidate_states=ready | watchlist_rows=1 | last_seen=2026-04-25 21:54:59.223341+00:00 | question=US x Iran permanent peace deal by May 31, 2026?
- market_id=2072226 | classification=hot_missing_quote | samples=24 | max_abs_delta=0.2510 | threshold=none | current=active | candidate_states=none | watchlist_rows=1 | last_seen=2026-04-28 20:42:58.189661+00:00 | question=Will WTI Crude Oil (WTI) hit (LOW) $90 Week of April 27 2026?

## Recent Hot-Only Examples

- none

## Recent Legacy-Only Examples

- sampled_at=2026-04-30 11:40:25.980770+00:00 | market_id=2036170 | classification=hot_missing_quote | abs_delta=0.295 | threshold_value=None | candidate_state=None | live_state=ready | legacy_last_bucket=2026-04-30T09:25:00+00:00
- sampled_at=2026-04-30 11:40:25.980770+00:00 | market_id=2086897 | classification=hot_missing_quote | abs_delta=0.05 | threshold_value=None | candidate_state=None | live_state=ready | legacy_last_bucket=2026-04-30T09:25:00+00:00

## Interpretation

- `hot_only_samples > 0` means the hot layer saw watchlist-ready candidates that legacy delivery did not expose in the same window.
- `legacy_only_samples > 0` means legacy delivery still surfaces watchlist alerts that the hot layer did not mark `ready`.
- `both_non_quiet_samples > 0` plus a healthy `max_overlap_count` is the strongest evidence for a safe hot-first delivery cutover.
- `Classification Totals` help separate semantic mismatch types from raw count drift so delivery decisions are based on reasons, not just volumes.
- `current=closed` in top mismatch markets means the historical mismatch came from a market that has since exited live delivery.
- `current=active` plus `candidate_states=below_threshold` means the market is still tracked, but hot currently sees no threshold-clearing move.
