# Growth KPI Report (2026-03-10T10:11:42.015998+00:00)

Window: `2026-03-03T10:11:42.015998+00:00` -> `2026-03-10T10:11:42.015998+00:00` (`7d`)

## Funnel

- page_view: **155**
- tg_click: **7** (`4.5%` from page_view)
- waitlist_submit: **12** (`7.7%` from page_view)
- confirm_success: **1** (`8.3%` from waitlist_submit)

## Telegram Activation (DB proxy)

- started_users (`app.identities provider=telegram`): **3**
- users_with_watchlist_add (`bot.watchlist`): **2**
- start_to_watchlist_add proxy: **66.7%**

## tg_click by UTM Source

| Source | tg_click | Share |
|---|---:|---:|
| site | 4 | 57.1% |
| chatgpt.com | 2 | 28.6% |
| x | 1 | 14.3% |

## Top tg_click Placements

| Placement | tg_click |
|---|---:|
| mobile_sticky | 3 |
| hero_panel | 2 |
| smoke | 1 |
| unknown | 1 |

## Action Notes

- Scale sources with highest tg_click share (`x`, `threads`, or direct).
- If `tg_click/page_view` is low: iterate hero and CTA copy on landing.
- If `start_to_watchlist_add` is low: simplify `/start -> /watchlist_add` flow in bot.
- If `confirm_success/waitlist_submit` is low: review email deliverability and confirm page UX.
