# Social Pipeline (Semi-Auto)

## Inputs
- `public.top_movers_latest`
- `bot.alerts_inbox_latest`
- `app.site_events` + `app.identities` + `bot.watchlist` for KPI retro
- UTM CTA target: `https://polymarketpulse.app/?utm_source=<x|threads>&utm_medium=social&utm_campaign=<live_movers|breakout|weekly_recap>`

## Draft generation
Run:

```bash
PG_CONN="postgresql://..." api/.venv/bin/python scripts/growth/generate_social_drafts.py
```

Output:
- `docs/social_drafts_latest.md`

Notes:
- Generates EN/RU drafts for both channels: `X` and `Threads`
- Includes both links:
  - deep link to bot (`t.me/...start=...`)
  - UTM-tagged site link for attribution
- Includes fallback behavior when live window is flat

## Competitor scan refresh
Run:

```bash
python3 scripts/growth/competitive_scan.py > docs/competitive_sweep_full_2026-03-08.md
```

## Weekly KPI retro
Run:

```bash
PG_CONN="postgresql://..." api/.venv/bin/python scripts/growth/weekly_kpi_report.py --days 7
```

Output:
- `docs/growth_kpi_latest.md`

Metrics:
- `page_view -> tg_click -> waitlist_submit -> confirm_success`
- `tg_click` split by `utm_source`
- activation proxy: `telegram identities -> users_with_watchlist_add`

## Visual assets
- `assets/social/top3-template.svg`
- `assets/social/breakout-template.svg`
- `assets/social/weekly-recap-template.svg`

## Daily cadence (manual publishing)
1. X: 2-3 posts/day (Top3 + Breakout)
2. Threads: 1-2 posts/day (best signal from X)
3. Reels/TikTok: 1 short/day from script pack

## Weekly review
- Compare `tg_click` split by `utm_source` in `app.site_events`
- Track `start_to_watchlist_add proxy` from `docs/growth_kpi_latest.md`
