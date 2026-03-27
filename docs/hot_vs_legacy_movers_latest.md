# Hot vs Legacy Movers (2026-03-27T17:41:57.907009+00:00)

Source tables:
- `public.hot_top_movers_5m`
- `public.top_movers_latest`
- `public.hot_market_quotes_latest`

## Summary

- hot_count: **28**
- legacy_count: **50**
- overlap_count: **11**

## Interpretation

- This report is meant to decide whether `/movers` is ready for hot-first cutover.
- High overlap with sane rank drift is a good sign.
- Low overlap with strong live quote coverage usually means the hot layer is seeing fresher reversion than the legacy bucket view.

## Active Gates

- min_liquidity: **1000**
- max_spread: **0.250**
- min_abs_delta: **0.0050**

## Overlap Rows

- `1741898` hot_rank=1 legacy_rank=1
- `1732923` hot_rank=2 legacy_rank=2
- `1731384` hot_rank=3 legacy_rank=4
- `1717483` hot_rank=5 legacy_rank=7
- `1743683` hot_rank=9 legacy_rank=5
- `1743692` hot_rank=6 legacy_rank=10
- `1743627` hot_rank=7 legacy_rank=12
- `1743629` hot_rank=8 legacy_rank=19
- `1743685` hot_rank=11 legacy_rank=9
- `1743693` hot_rank=13 legacy_rank=27
- `1743645` hot_rank=18 legacy_rank=33

## Legacy Top Rows Diagnostic

| legacy_rank | market_id | legacy_delta | in_hot_quotes | two_sided | liquidity | spread | in_hot_movers | hot_delta | hot_score | exclusion_reason |
| --- | --- | ---: | --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| 1 | 1741898 | 0.1450 | yes | yes | 5377.60 | 0.0800 | yes | -0.1650 | 25.0902 | published |
| 2 | 1732923 | -0.0450 | yes | yes | 8912.49 | 0.0100 | yes | 0.1100 | 20.0953 | published |
| 3 | 1741888 | -0.0400 | yes | yes | 8013.40 | 0.0800 | no | n/a | n/a | below_abs_delta_gate |
| 4 | 1731384 | -0.0300 | yes | yes | 29354.08 | 0.0100 | yes | 0.0100 | 11.2872 | published |
| 5 | 1743683 | -0.0250 | yes | yes | 9312.44 | 0.0300 | yes | 0.0150 | 10.6392 | published |
| 6 | 1743695 | -0.0190 | yes | yes | 9749.19 | 0.0150 | no | n/a | n/a | below_abs_delta_gate |
| 7 | 1717483 | -0.0150 | yes | yes | 18916.18 | 0.0100 | yes | -0.0100 | 10.8478 | published |
| 8 | 1743638 | -0.0150 | yes | yes | 9486.46 | 0.0400 | no | n/a | n/a | below_abs_delta_gate |
| 9 | 1743685 | -0.0150 | yes | yes | 9903.44 | 0.0400 | yes | 0.0100 | 10.2007 | published |
| 10 | 1743692 | -0.0150 | yes | yes | 9759.16 | 0.0100 | yes | -0.0150 | 10.6861 | published |
| 11 | 1743765 | -0.0110 | yes | yes | 11936.37 | 0.0060 | no | n/a | n/a | below_abs_delta_gate |
| 12 | 1743627 | 0.0100 | yes | yes | 9416.44 | 0.0300 | yes | 0.0150 | 10.6503 | published |
| 13 | 1581306 | 0.0100 | yes | yes | 300145.93 | 0.0100 | no | n/a | n/a | below_abs_delta_gate |
| 14 | 1743633 | 0.0100 | yes | yes | 9409.44 | 0.0600 | no | n/a | n/a | below_abs_delta_gate |
| 15 | 1668623 | -0.0100 | yes | yes | 52814.53 | 0.0100 | no | n/a | n/a | below_abs_delta_gate |

## Reading Guide

- `in_hot_quotes=yes` but `in_hot_movers=no` means the market is covered live, and `exclusion_reason` tells us which gate blocked it.
- That is the key distinction between a fresher action surface and a laggier bucket surface.
- Do not cut over `/movers` until this report shows the behavior we actually want as a product decision.
