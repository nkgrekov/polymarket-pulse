# Competitive Landscape — 2026-03-08

## Scope
Fast market scan for Polymarket tooling with focus on:
- `analytics`
- `dashboard(s)`
- `signal(s)`
- Telegram-native alert products

## Primary competitors

| Product | Positioning | Strengths | Weakness vs Polymarket Pulse |
|---|---|---|---|
| `polymark.et` | Ecosystem directory of tools | Huge catalog and discovery SEO footprint | Not a simple end-user signal product; no focused activation funnel |
| `betmoar.fun` | Trading terminal | Strong power-user UX, dense filters, trader-centric tooling | High cognitive load for mainstream users; weak “start in 60s” path |
| `polymarketanalytics.com` | Analytics dashboards + pricing tiers | Mature analytics IA, SEO structure, clear paid tiers | More dashboard-heavy than push-first actionable workflow |

## Secondary competitor clusters from directory scan
- Wallet/whale tracking bots
- Arbitrage scanners
- AI-agent wrappers
- Data terminals and Dune dashboards
- Telegram alert bots with narrow use-cases

Implication: competition is crowded on “more data” and “more features”, but fragmented on “simple activation + clean signals”.

## Proposed UTP (live-first and manifesto-aligned)

`Polymarket Pulse = fastest path from noise to actionable live moves for an average user in Telegram.`

Core message:
1. Open bot.
2. Get top live movers instantly.
3. Track only chosen markets with personal threshold.

This differentiates from “terminal UX” and “dashboard overload”.

## Product messaging pillars
1. `Signals > noise`: thresholded, deduplicated alerts.
2. `60-second activation`: Telegram-first onboarding.
3. `Human-readable output`: clear delta + time window + market context.
4. `Freemium with clear edge`: free enough to start, paid to scale.

## UX decisions to keep
1. Keep Telegram command menu short (top commands only).
2. Hide advanced commands in `/help` (discoverable but not cluttering menu).
3. Keep primary CTA everywhere: `Open Telegram Bot`.

## 7-day intercept plan
1. Publish 2x daily `Top 3 movers` posts on X with UTM links.
2. Publish 1x daily `single-market breakout` post on Threads.
3. Post weekly recap thread with biggest deltas and CTA to bot.
4. Keep site funnel split by source in `app.site_events` (`x`, `threads`, `organic`).
5. Iterate onboarding copy weekly based on `/start -> /watchlist_add` conversion.

## Sources
- https://polymark.et
- https://www.betmoar.fun/home
- https://polymarketanalytics.com
- https://polymarketanalytics.com/pricing
