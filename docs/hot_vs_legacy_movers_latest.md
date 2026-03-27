# Hot vs Legacy Movers (2026-03-27T17:51:45.257275+00:00)

Source tables:
- `public.hot_top_movers_5m`
- `public.top_movers_latest`
- `public.hot_market_quotes_latest`

## Summary

- hot_count: **50**
- legacy_count: **50**
- overlap_count: **34**

## Interpretation

- This report is meant to decide whether `/movers` is ready for hot-first cutover.
- High overlap with sane rank drift is a good sign.
- Low overlap with strong live quote coverage usually means the hot layer is seeing fresher reversion than the legacy bucket view.

## Active Gates

- min_liquidity: **1000**
- max_spread: **0.250**
- min_abs_delta: **0.0030**

## Overlap Rows

- `1741898` hot_rank=1 legacy_rank=1
- `1733236` hot_rank=2 legacy_rank=3
- `1733246` hot_rank=3 legacy_rank=2
- `1731384` hot_rank=4 legacy_rank=4
- `1743683` hot_rank=5 legacy_rank=5
- `1717483` hot_rank=6 legacy_rank=8
- `1743685` hot_rank=9 legacy_rank=6
- `1717488` hot_rank=7 legacy_rank=9
- `1739490` hot_rank=11 legacy_rank=7
- `1668621` hot_rank=8 legacy_rank=20
- `1741872` hot_rank=14 legacy_rank=10
- `1668617` hot_rank=10 legacy_rank=26
- `1743681` hot_rank=13 legacy_rank=11
- `1743636` hot_rank=21 legacy_rank=12
- `1668619` hot_rank=12 legacy_rank=32
- `1743692` hot_rank=18 legacy_rank=15
- `1717491` hot_rank=15 legacy_rank=23
- `1743634` hot_rank=20 legacy_rank=16
- `1731486` hot_rank=16 legacy_rank=21
- `1717477` hot_rank=17 legacy_rank=17
- `1743765` hot_rank=19 legacy_rank=18
- `1743638` hot_rank=23 legacy_rank=19
- `1743621` hot_rank=25 legacy_rank=22
- `1743687` hot_rank=24 legacy_rank=25
- `1743639` hot_rank=27 legacy_rank=24
- `1734020` hot_rank=26 legacy_rank=39
- `1559117` hot_rank=31 legacy_rank=27
- `1734017` hot_rank=28 legacy_rank=29
- `1743629` hot_rank=38 legacy_rank=28
- `1734026` hot_rank=29 legacy_rank=40
- `1577035` hot_rank=30 legacy_rank=38
- `1743635` hot_rank=39 legacy_rank=30
- `1559115` hot_rank=37 legacy_rank=31
- `1743679` hot_rank=32 legacy_rank=34
- `1743689` hot_rank=36 legacy_rank=36
- `1559116` hot_rank=46 legacy_rank=37

## Legacy Top Rows Diagnostic

| legacy_rank | market_id | legacy_delta | in_hot_quotes | two_sided | liquidity | spread | in_hot_movers | hot_delta | hot_score | exclusion_reason |
| --- | --- | ---: | --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| 1 | 1741898 | -0.1950 | yes | yes | 7033.15 | 0.0800 | yes | -0.1950 | 28.3585 | published |
| 2 | 1733246 | 0.0500 | yes | yes | 33349.12 | 0.0100 | yes | 0.0500 | 15.4148 | published |
| 3 | 1733236 | 0.0500 | yes | yes | 38926.17 | 0.0100 | yes | 0.0500 | 15.5694 | published |
| 4 | 1731384 | -0.0450 | yes | yes | 29667.59 | 0.0200 | yes | -0.0450 | 14.7978 | published |
| 5 | 1743683 | -0.0350 | yes | yes | 9314.44 | 0.0100 | yes | -0.0350 | 12.6394 | published |
| 6 | 1743685 | -0.0250 | yes | yes | 9840.43 | 0.0700 | yes | -0.0250 | 11.6944 | published |
| 7 | 1739490 | 0.0230 | yes | yes | 15272.52 | 0.0080 | yes | 0.0170 | 11.3339 | published |
| 8 | 1717483 | -0.0200 | yes | yes | 20497.76 | 0.0300 | yes | -0.0200 | 11.9281 | published |
| 9 | 1717488 | -0.0200 | yes | yes | 19461.71 | 0.0300 | yes | -0.0200 | 11.8763 | published |
| 10 | 1741872 | -0.0200 | yes | yes | 8016.71 | 0.0800 | yes | -0.0200 | 10.9894 | published |
| 11 | 1743681 | -0.0200 | yes | yes | 9118.03 | 0.0800 | yes | -0.0200 | 11.1181 | published |
| 12 | 1743636 | -0.0150 | yes | yes | 7543.00 | 0.0700 | yes | -0.0150 | 10.4285 | published |
| 13 | 1728908 | -0.0150 | yes | yes | 71.81 | 0.4300 | no | n/a | n/a | below_liquidity_gate |
| 14 | 1741924 | 0.0150 | yes | yes | 0.80 | 0.9100 | no | n/a | n/a | below_liquidity_gate |
| 15 | 1743692 | -0.0150 | yes | yes | 9765.76 | 0.0300 | yes | -0.0150 | 10.6867 | published |

## Reading Guide

- `in_hot_quotes=yes` but `in_hot_movers=no` means the market is covered live, and `exclusion_reason` tells us which gate blocked it.
- That is the key distinction between a fresher action surface and a laggier bucket surface.
- This report now serves as the calibration and fallback-quality check for the hot-first `/movers` runtime.
