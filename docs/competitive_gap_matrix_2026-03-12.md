# Competitive Gap Matrix — 2026-03-12

## Scope
Goal of this pass: finalize `C1` for the 14-day plan:
- refresh competitive baseline
- lock a clear gap-matrix
- define 3 interception messages for site + bot + social
- output a focused 7-day execution list

## Fresh Inputs
- Directory scan (today): `docs/competitive_sweep_latest.md`
  - tools parsed from polymark.et: `162`
  - cluster mix: `analytics/dashboard=51`, `trading terminal=30`, `signals/alerts=10`
- Primary benchmark sites:
  - `https://polymark.et`
  - `https://www.betmoar.fun/home`
  - `https://polymarketanalytics.com`
  - `https://polymarketanalytics.com/pricing`

## Quick Market Read
Competition is crowded in “more dashboards” and “power-user terminals”.
The under-served lane remains:
`simple activation + clean live signals + Telegram-native delivery`.

This is exactly aligned with the manifesto’s live-first principle.

## Top-7 Gap Matrix (for positioning decisions)
| Competitor | Core Position | Strong Side | Weak Side (vs Pulse) | Intercept Angle |
|---|---|---|---|---|
| `polymark.et` | Tool directory / discovery hub | Massive catalog + discovery footprint | Not a focused end-user signal product | “Skip directory hunting. Open one bot and get live movers now.” |
| `betmoar.fun` | High-speed trading interface | Strong trader narrative, deep terminal UX | Higher cognitive load for average users | “No terminal required: `/start -> /watchlist_add -> /inbox` in under 60 sec.” |
| `polymarketanalytics.com` | Analytics dashboards + trader data | Mature analytics IA + strong SEO packaging | Dashboard-first flow, less push-first action loop | “From dashboard reading to immediate signal action in Telegram.” |
| `MobyScreener` (directory) | Analytics tools / dashboards | Market data density | Mainly dashboard consumption pattern | “Action feed, not dashboard tab-switching.” |
| `Polysights` (directory) | Dashboard analytics | Familiar analytics framing | Less explicit activation funnel | “Signal-first onboarding with instant watchlist state.” |
| `TradeFox` (directory) | Trading aggregation / bots | Trader utility depth | Built for advanced users | “Human-readable alerts for normal users, not pro-only tooling.” |
| `Polymarket Live Ticker` (directory) | Official ticker stream | Fast raw market stream | Raw stream != personalized alerting | “Personalized thresholds + deduped alerts, not raw tape noise.” |

## 3 Interception Messages (final copy set)
Use these consistently across landing hero, `/start`/`/help`, and social hooks.

### 1) Action Over Dashboard
`Most tools optimize for dashboards. We optimize for action: live movers and watchlist deltas in one Telegram feed.`

### 2) 60-Second Activation
`No setup friction: open bot, add one market, get first usable signal in under a minute.`

### 3) Signal Quality Over Noise
`Live-only buckets, threshold filtering, and deduped alerts — so you react to movement, not spam.`

## Channel-Level Capture Plan (3 channels)
### A) SEO Capture (high-intent search)
Target intents:
- `polymarket analytics`
- `polymarket dashboard`
- `polymarket signals`

Execution:
- keep intent pages interlinked with Telegram-first CTA
- emphasize “action vs dashboard overload” above fold

### B) Telegram Activation Capture (onsite -> bot)
Critical path:
- `page_view -> tg_click -> /start -> watchlist_add`

Execution:
- keep primary CTA to bot
- keep watchlist picker broad + low-friction
- keep zero-state explanations actionable (`what next`)

### C) Social Capture (X + Threads)
Content units:
- Top-3 live movers (daily)
- Single-market breakout (daily)
- Weekly recap (weekly)

Execution:
- always include Telegram CTA + UTM links
- keep post format delta-first (`prev -> now`, `Δ`, `window`)

## 7-Day Action List (C1 follow-through)
1. Publish one comparison snippet on site (`Pulse vs dashboard overload`) linking to `/telegram-bot`.
2. Update bot `/start` short copy to include “action over dashboard” phrase (RU/EN parity).
3. Pin one X post with the 3 positioning messages + Telegram deep link.
4. Post one “Terminal vs Signal feed” visual in Threads (soft educational tone).
5. Add one FAQ line on landing: “Why Telegram-first instead of full dashboard?”
6. Track split in `app.site_events` by source and placement (`hero_panel`, `mobile_sticky`, social UTMs).
7. Weekly retro: keep top-performing message, rewrite weakest one.

## Notes
- Full top-30 list and cluster counts remain in `docs/competitive_sweep_latest.md`.
- This document is the decision layer for messaging and channel priorities.
