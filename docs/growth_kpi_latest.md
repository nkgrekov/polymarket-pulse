# Growth KPI Report (2026-04-28T06:07:32.908150+00:00)

Window: `2026-04-21T06:07:32.908150+00:00` -> `2026-04-28T06:07:32.908150+00:00` (`7d`)

## Funnel

- page_view: **36**
- tg_click: **4** (`11.1%` from page_view)
- tg_start (all entrypoints): **7**
- tg_start from site payloads: **1** (`25.0%` from tg_click)
- watchlist_add events: **0**
- watchlist_add users: **0** (`0.0%` from all tg_start)
- watchlist_add users from site-attributed starts: **0** (`0.0%` from site-attributed tg_start)
- first_watchlist_add users: **0** (`0.0%` from tg_start)
- waitlist_submit: **0** (`0.0%` from page_view)
- confirm_success: **0** (`n/a` from waitlist_submit)

## Website -> Telegram Watchlist Loop

- page_view: **36**
- live_board_impression: **0** (`0.0%` from page_view)
- watchlist_add_click: **0** (`0.0%` from page_view)
- watchlist_add_success: **0** (`n/a` from watchlist_add_click)
- telegram_login_click: **0** (`n/a` from watchlist_add_click)
- site_login_completed: **0** (`n/a` from telegram_login_click)
- tg_start: **7**
- bell_click: **0** (`n/a` from watchlist_add_success)
- alert_setup_started: **0** (`n/a` from bell_click)
- alert_enabled: **0** (`n/a` from bell_click)
- alert_sent: **0** (`n/a` from alert_enabled)
- alert_click_back_to_site: **0** (`n/a` from alert_sent)
- pricing_seen: **0**
- pricing_cta_click: **0** (`n/a` from pricing_seen)

## Telegram Activation Cross-Check

- started_users (`app.identities provider=telegram`): **2**
- users_with_watchlist_add proxy (`bot.watchlist`): **0**
- start_to_watchlist_add proxy: **0.0%**
- event_to_proxy gap (`watchlist_add users` vs `bot.watchlist` proxy): **+0**
- note: `tg_start` includes site, direct Telegram opens, and other bot entrypoints like `/upgrade`

## Core Data Health

- latest bucket lag: **7355s**
- latest yes-quote coverage: **86.2%**
- universe coverage (latest): **182/182**
- universe coverage (prev): **182/182**
- non-zero movers: **latest 108 / 1h 108 / 24h 116**

## tg_click by UTM Source

| Source | tg_click | Share |
|---|---:|---:|
| chatgpt.com | 2 | 50.0% |
| site | 2 | 50.0% |

## tg_start by Start Payload

| Start payload | tg_start | Share |
|---|---:|---:|
| seo_telegram-bot_en | 3 | 42.9% |
| telegram_direct | 3 | 42.9% |
| site_watchlist_add_2036170_UEHGz56U5S96SKTkN6FIZa-NBXpfLs6K | 1 | 14.3% |

## Top tg_click Placements

| Placement | tg_click |
|---|---:|
| seo_telegram-bot | 3 |
| mobile_sticky | 1 |

## CTA Surface Performance

| Placement | Seen | tg_click | CTR |
|---|---:|---:|---:|
| hero_panel | 19 | 0 | 0.0% |
| mobile_sticky | 0 | 1 | n/a |
| proof_bridge | 8 | 0 | 0.0% |
| seo_bridge | 2 | 0 | 0.0% |

## Action Notes

- Scale sources with highest tg_click share (`x`, `threads`, or direct).
- If `tg_start/tg_click` is low: inspect Telegram deep-link friction and social CTA clarity.
- If `watchlist_add/tg_start` is low: simplify first add, quiet-state recovery, and returning-user resume paths.
- If `watchlist_add_success/watchlist_add_click` is low: inspect web save friction, auth prompt clarity, and workspace error states.
- If `bell_click/watchlist_add_success` is low: the site may still be underselling the bell as a second deliberate action.
- If `alert_enabled/bell_click` is low: inspect Telegram sensitivity setup and payload handoff.
- If `alert_click_back_to_site/alert_enabled` is low: strengthen the return loop from alert into the website watchlist.
- If one `start_payload` consistently wins: keep posting into that pain theme.
- If `tg_click/page_view` is low: iterate hero and CTA copy on landing.
- If `confirm_success/waitlist_submit` is low: review email deliverability and confirm page UX.
- If core freshness or universe coverage slips: fix the analytical core before iterating user-facing Pulse UX.
