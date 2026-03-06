# Growth Quick Sweep — 2026-03-06

## Objective
Increase Telegram activations using dual acquisition channels (`X` + `Threads`) while preserving live-first positioning.

## Competitive Snapshot (5-7)
| Competitor | Focus | Strength | Weakness vs Polymarket Pulse | Source |
|---|---|---|---|---|
| PredictFolio | Portfolio analytics + alerts | Clear analytics positioning and tracker UX | Less Telegram-first urgency narrative | https://predictfolio.com/ |
| PredictPM | Real-time monitoring stack | Broad feature language (cross-platform + signals) | Messaging is feature-heavy, weak instant CTA | https://predictpm.com/ |
| PolyWatch | Whale tracking + alerts | Clear social proof around whales + TG bot | Niche around wallet-following, less delta-first | https://www.polywatch.tech/ |
| PolyFire | Telegram bot + copy signals | Fast path for users who want copy behavior | Copy-trade centric; weaker universal mover onboarding | https://polyfire.co/ |
| IYKYK Markets | Smart-money analytics | Public analytics framing and multi-platform angle | Lower "instant actionable" emphasis | https://www.iykykmarkets.io/ |
| Polyar | Arbitrage scanner | Multi-platform arbitrage narrative | Not focused on simple activation + alert clarity | https://www.polyar.io/ |
| Filezon bot | Telegram headline/news alerts | Very narrow and easy use-case | News-first, not probability-delta intelligence | https://filezon.com/ |

## Intercept Channels (Top 3)
1. `Search intent`: "polymarket alerts", "polymarket analytics", "polymarket telegram bot".
2. `Social intent`: traders browsing live movers on `X` and `Threads`.
3. `Community intent`: Polymarket/Kalshi subreddit traffic where users ask for alert tools.

## 7-Day Action List
1. Ship daily `Live Movers` cards to X + Threads with UTM links (`utm_source=x|threads`).
2. Pin one canonical post with product promise + Telegram CTA.
3. Post 1 weekly recap thread with top deltas + links to site and bot.
4. Add `?utm_source=` links to all CTA entry points on website + profile bios.
5. Add social-proof block on site (`Historical examples`) and keep it clearly non-live.
6. Track funnel split in `app.site_events`: `page_view -> tg_click -> waitlist_submit -> confirm_success` by source.
7. End-of-week review: compare `x` vs `threads` CTR, `tg_click -> /start`, and `confirm rate`.

## Content Templates (MVP)
### Live Movers Post (daily)
- Hook: `Market moved fast: [question]`
- Data: `prev -> now`, `delta`, `window`
- Insight: one-line interpretation
- CTA: `Track live in Telegram: @polymarket_pulse_bot`
- Link: site with UTM (`utm_source=x` or `utm_source=threads`)

### Single-Market Breakout (daily)
- Hook on one sharp delta
- One chart/screenshot or compact data line
- Why it matters now (one line)
- CTA to Telegram bot

### Weekly Recap (weekly)
- Top 5 shifts of week
- 1-2 learnings about market behavior
- CTA to join Telegram alerts

## KPIs (weekly)
- `tg_click` count split by `utm_source=x|threads`
- `waitlist_submit -> confirm_success` conversion rate
- `tg_click -> /start` activation rate

## Execution Mode
- Today: manual posting from live outputs (`top_movers_latest`, bot alerts).
- Next: semi-auto draft generator (no auto-post), using the same live views.
