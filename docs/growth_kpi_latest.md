# Growth KPI Report (2026-03-18T15:21:39.738844+00:00)

Window: `2026-03-11T15:21:39.738844+00:00` -> `2026-03-18T15:21:39.738844+00:00` (`7d`)

## Funnel

- page_view: **90**
- tg_click: **6** (`6.7%` from page_view)
- tg_start: **0** (`0.0%` from tg_click)
- waitlist_submit: **0** (`0.0%` from page_view)
- confirm_success: **0** (`n/a` from waitlist_submit)

## Telegram Activation (DB proxy)

- started_users (`app.identities provider=telegram`): **3**
- users_with_watchlist_add (`bot.watchlist`): **0**
- start_to_watchlist_add proxy: **0.0%**

## tg_click by UTM Source

| Source | tg_click | Share |
|---|---:|---:|
| site | 5 | 83.3% |
| qa | 1 | 16.7% |

## tg_start by Start Payload

| Start payload | tg_start | Share |
|---|---:|---:|
| n/a | 0 | n/a |

## Top tg_click Placements

| Placement | tg_click |
|---|---:|
| hero_panel | 4 |
| mobile_sticky | 2 |

## Action Notes

- Scale sources with highest tg_click share (`x`, `threads`, or direct).
- If `tg_start/tg_click` is low: inspect Telegram deep-link friction and social CTA clarity.
- If one `start_payload` consistently wins: keep posting into that pain theme.
- If `tg_click/page_view` is low: iterate hero and CTA copy on landing.
- If `start_to_watchlist_add` is low: simplify `/start -> /watchlist_add` flow in bot.
- If `confirm_success/waitlist_submit` is low: review email deliverability and confirm page UX.
