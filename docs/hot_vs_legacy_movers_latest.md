# Hot vs Legacy Movers (2026-03-27T17:21:38.525958+00:00)

Source tables:
- `public.hot_top_movers_5m`
- `public.top_movers_latest`
- `public.hot_market_quotes_latest`

## Summary

- hot_count: **30**
- legacy_count: **50**
- overlap_count: **12**

## Interpretation

- This report is meant to decide whether `/movers` is ready for hot-first cutover.
- High overlap with sane rank drift is a good sign.
- Low overlap with strong live quote coverage usually means the hot layer is seeing fresher reversion than the legacy bucket view.

## Overlap Rows

- `1732884` hot_rank=1 legacy_rank=20
- `1731384` hot_rank=2 legacy_rank=17
- `1561326` hot_rank=3 legacy_rank=19
- `1741888` hot_rank=4 legacy_rank=28
- `1741872` hot_rank=6 legacy_rank=23
- `1741898` hot_rank=8 legacy_rank=30
- `1743625` hot_rank=18 legacy_rank=9
- `1743638` hot_rank=15 legacy_rank=10
- `1717483` hot_rank=11 legacy_rank=18
- `1717491` hot_rank=13 legacy_rank=31
- `1731486` hot_rank=14 legacy_rank=29
- `1743689` hot_rank=17 legacy_rank=16

## Legacy Top Rows Diagnostic

| legacy_rank | market_id | legacy_delta | in_hot_quotes | two_sided | liquidity | spread | in_hot_movers | hot_delta | hot_score |
| --- | --- | ---: | --- | --- | ---: | ---: | --- | ---: | ---: |
| 1 | 1732673 | 0.5000 | yes | no | 0.00 | n/a | no | n/a | n/a |
| 2 | 1743645 | -0.4655 | yes | yes | 9643.25 | 0.0410 | no | n/a | n/a |
| 3 | 1743695 | -0.4615 | yes | yes | 9537.50 | 0.0230 | no | n/a | n/a |
| 4 | 1743693 | -0.3950 | yes | yes | 9663.44 | 0.0400 | no | n/a | n/a |
| 5 | 1743683 | 0.3100 | yes | yes | 9183.42 | 0.0700 | no | n/a | n/a |
| 6 | 1743692 | -0.3000 | yes | yes | 9616.44 | 0.0400 | no | n/a | n/a |
| 7 | 1743642 | -0.2850 | yes | yes | 9530.63 | 0.0290 | no | n/a | n/a |
| 8 | 1743640 | -0.2700 | yes | yes | 9432.41 | 0.0700 | no | n/a | n/a |
| 9 | 1743625 | -0.2350 | yes | yes | 9388.65 | 0.0700 | yes | 0.0050 | 9.6474 |
| 10 | 1743638 | -0.2350 | yes | yes | 9457.54 | 0.0500 | yes | 0.0100 | 10.1547 |
| 11 | 1743635 | -0.2000 | yes | yes | 9303.52 | 0.0700 | no | n/a | n/a |
| 12 | 1743627 | -0.2000 | yes | yes | 9300.14 | 0.0800 | no | n/a | n/a |
| 13 | 1743633 | -0.1850 | yes | yes | 9287.63 | 0.0800 | no | n/a | n/a |
| 14 | 1743629 | -0.1800 | yes | yes | 9223.62 | 0.0900 | no | n/a | n/a |
| 15 | 1743685 | 0.1700 | yes | yes | 9450.94 | 0.0600 | no | n/a | n/a |

## Reading Guide

- `in_hot_quotes=yes` but `in_hot_movers=no` usually means the market is covered live, but the current 5m delta no longer clears the mover gates.
- That is the key distinction between a fresher action surface and a laggier bucket surface.
- Do not cut over `/movers` until this report shows the behavior we actually want as a product decision.
