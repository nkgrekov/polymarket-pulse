# Growth KPI Report (2026-03-25T11:51:16.644485+00:00)

Window: `2026-03-18T11:51:16.644485+00:00` -> `2026-03-25T11:51:16.644485+00:00` (`7d`)

## Funnel

- page_view: **112**
- tg_click: **4** (`3.6%` from page_view)
- tg_start (all entrypoints): **5**
- tg_start from site payloads: **3** (`75.0%` from tg_click)
- watchlist_add events: **0**
- watchlist_add users: **0** (`0.0%` from all tg_start)
- watchlist_add users from site-attributed starts: **0** (`0.0%` from site-attributed tg_start)
- first_watchlist_add users: **0** (`0.0%` from tg_start)
- waitlist_submit: **0** (`0.0%` from page_view)
- confirm_success: **0** (`n/a` from waitlist_submit)

## Telegram Activation Cross-Check

- started_users (`app.identities provider=telegram`): **2**
- users_with_watchlist_add proxy (`bot.watchlist`): **1**
- start_to_watchlist_add proxy: **50.0%**
- event_to_proxy gap (`watchlist_add users` vs `bot.watchlist` proxy): **-1**
- note: `tg_start` includes site, direct Telegram opens, and other bot entrypoints like `/upgrade`

## Core Data Health

- latest bucket lag: **378s**
- latest yes-quote coverage: **96.9%**
- universe coverage (latest): **200/200**
- universe coverage (prev): **200/200**
- non-zero movers: **latest 24 / 1h 122 / 24h 69**

## tg_click by UTM Source

| Source | tg_click | Share |
|---|---:|---:|
| site | 4 | 100.0% |

## tg_start by Start Payload

| Start payload | tg_start | Share |
|---|---:|---:|
| site_en | 2 | 40.0% |
| site_en_sticky | 1 | 20.0% |
| telegram_direct | 1 | 20.0% |
| upgrade | 1 | 20.0% |

## Top tg_click Placements

| Placement | tg_click |
|---|---:|
| hero_panel | 3 |
| mobile_sticky | 1 |

## Action Notes

- Scale sources with highest tg_click share (`x`, `threads`, or direct).
- If `tg_start/tg_click` is low: inspect Telegram deep-link friction and social CTA clarity.
- If `watchlist_add/tg_start` is low: simplify first add, quiet-state recovery, and returning-user resume paths.
- If one `start_payload` consistently wins: keep posting into that pain theme.
- If `tg_click/page_view` is low: iterate hero and CTA copy on landing.
- If `confirm_success/waitlist_submit` is low: review email deliverability and confirm page UX.
- If core freshness or universe coverage slips: fix the analytical core before iterating user-facing Pulse UX.
