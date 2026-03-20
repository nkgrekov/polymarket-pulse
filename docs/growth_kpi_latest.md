# Growth KPI Report (2026-03-20T11:29:03.497451+00:00)

Window: `2026-03-13T11:29:03.497451+00:00` -> `2026-03-20T11:29:03.497451+00:00` (`7d`)

## Funnel

- page_view: **86**
- tg_click: **4** (`4.7%` from page_view)
- tg_start: **1** (`25.0%` from tg_click)
- watchlist_add events: **0**
- watchlist_add users: **0** (`0.0%` from tg_start)
- first_watchlist_add users: **0** (`0.0%` from tg_start)
- waitlist_submit: **0** (`0.0%` from page_view)
- confirm_success: **0** (`n/a` from waitlist_submit)

## Telegram Activation Cross-Check

- started_users (`app.identities provider=telegram`): **3**
- users_with_watchlist_add proxy (`bot.watchlist`): **1**
- start_to_watchlist_add proxy: **33.3%**
- event_to_proxy gap (`watchlist_add users` vs `bot.watchlist` proxy): **-1**

## tg_click by UTM Source

| Source | tg_click | Share |
|---|---:|---:|
| site | 4 | 100.0% |

## tg_start by Start Payload

| Start payload | tg_start | Share |
|---|---:|---:|
| upgrade | 1 | 100.0% |

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
