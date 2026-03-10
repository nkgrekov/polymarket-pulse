# 14-Day Execution Plan (2026-03-09)

KPI focus: increase `tg_click -> /start -> watchlist_add` without breaking live-only product logic.

---

# Direction A — Website SEO + Conversion

## A1. Technical SEO Hardening
- Canonical/hreflang consistency for EN/RU.
- Validate robots/sitemap coverage for intent pages.
- Validate OG/Twitter cards for homepage + intent pages.

## A2. Intent SEO Pages
- Maintain and improve pages:
  - `/analytics`
  - `/dashboard`
  - `/signals`
  - `/telegram-bot`
  - `/top-movers`
  - `/watchlist-alerts`
- Keep strong internal linking and Telegram CTA on every page.

## A3. Conversion UX
- Primary CTA: `Open Telegram Bot`.
- Secondary CTA: waitlist email.
- Keep “How it works in 60 sec” and clear FAQ for zero-state movers.
- Keep mobile sticky Telegram CTA.

---

# Direction B — Telegram Bot UX + Activation

## B1. Command Architecture
- Menu core only: `/start`, `/movers`, `/watchlist`, `/inbox`, `/plan`, `/help`.
- Advanced flows via `/menu` and `/help`.
- Keep command list compact so it fits Telegram command UI.

## B2. Activation Funnel
- `/start` must drive user to add first market quickly.
- `/watchlist_add` should support picker flow from current movers.
- `/plan` and `/upgrade` should show clear limits and next action.

## B3. Signal Clarity
- Improve empty-state explanations for `/movers`, `/watchlist`, `/inbox`.
- Add adaptive window fallback for low-cadence ingest windows.
- Preserve low-noise behavior (signals > spam).

---

# Direction C — Multi-Channel Growth (X/Threads/Reels/TikTok)

## C1. Competitive Intelligence
- Maintain competitor scan and gap matrix.
- Track categories: analytics dashboards, signals bots, whale tools.
- Refresh weekly.

## C2. Content Pipeline
- Daily formats:
  - Top 3 movers
  - Single-market breakout
  - Weekly recap
- Source content from live DB views, not manual scraping.
- Use UTM-tagged links for source attribution.

## C3. Distribution Cadence
- X: 2-3 posts/day.
- Threads: 1-2 posts/day.
- Reels/TikTok: 1 short/day, 5 days/week.
- Weekly retro by source: `x` vs `threads` vs direct.

---

# Branding/Visual Identity Track (cross-channel)

- Use one brand mark system across:
  - favicon/browser tab
  - OG/social preview
  - Telegram bot avatar
  - X/Threads/TikTok avatar
  - website header lockup
- Keep dark-terminal palette and positive green accent from UX Manifest.
- Export set:
  - SVG master
  - PNG: `16, 32, 48, 180, 512, 1024`

---

# Execution Order (ascending impact)

1. Bot activation reliability (`/movers`/`/inbox` non-confusing zero-state + adaptive window).
2. Watchlist-first onboarding (1-tap add flow after `/start`).
3. SEO page content and internal linking polish.
4. Brand asset unification and replacement in web+bot+socials.
5. Content distribution cadence with weekly KPI retro.

---

# Acceptance Targets for 14 Days

- `tg_click -> /start`: +40% vs current baseline.
- `/start -> watchlist_add`: >=25%.
- Organic sessions on intent pages: +30%.
- Source split: X/Threads contribute >=20% of `tg_click`.
- Telegram command UX remains compact and readable in menu UI.
