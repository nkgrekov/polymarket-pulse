# Growth KPI Report (2026-03-23T08:32:18.955333+00:00)

Window: `2026-03-16T08:32:18.955333+00:00` -> `2026-03-23T08:32:18.955333+00:00` (`7d`)

## Funnel

- page_view: **87**
- tg_click: **4** (`4.6%` from page_view)
- tg_start: **2** (`50.0%` from tg_click)
- watchlist_add events: **0**
- watchlist_add users: **0** (`0.0%` from tg_start)
- first_watchlist_add users: **0** (`0.0%` from tg_start)
- waitlist_submit: **0** (`0.0%` from page_view)
- confirm_success: **0** (`n/a` from waitlist_submit)

## Telegram Activation Cross-Check

- started_users (`app.identities provider=telegram`): **2**
- users_with_watchlist_add proxy (`bot.watchlist`): **1**
- start_to_watchlist_add proxy: **50.0%**
- event_to_proxy gap (`watchlist_add users` vs `bot.watchlist` proxy): **-1**

## Core Data Health

- latest bucket lag: **1041s**
- latest yes-quote coverage: **92.4%**
- universe coverage (latest): **200/200**
- universe coverage (prev): **200/200**
- non-zero movers: **latest 33 / 1h 60 / 24h 69**

## tg_click by UTM Source

| Source | tg_click | Share |
|---|---:|---:|
| site | 4 | 100.0% |

## tg_start by Start Payload

| Start payload | tg_start | Share |
|---|---:|---:|
| site_en_sticky | 1 | 50.0% |
| upgrade | 1 | 50.0% |

## Top tg_click Placements

| Placement | tg_click |
|---|---:|
| hero_panel | 2 |
| mobile_sticky | 2 |

## Action Notes

- Scale sources with highest tg_click share (`x`, `threads`, or direct).
- If `tg_start/tg_click` is low: inspect Telegram deep-link friction and social CTA clarity.
- If `watchlist_add/tg_start` is low: simplify first add, quiet-state recovery, and returning-user resume paths.
- If one `start_payload` consistently wins: keep posting into that pain theme.
- If `tg_click/page_view` is low: iterate hero and CTA copy on landing.
- If `confirm_success/waitlist_submit` is low: review email deliverability and confirm page UX.
- If core freshness or universe coverage slips: fix the analytical core before iterating user-facing Pulse UX.
