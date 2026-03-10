# Reels/TikTok Scripts (15-30s) - 2026-03-08

## Format
- Hook (0-3s)
- Data (4-12s)
- Insight (13-20s)
- CTA (last 5s)

## Script Pack (10)
1. **"Market jumped while you slept"**  
Hook: "This Polymarket moved hard overnight."  
Data: `prev -> now`, delta, window.  
Insight: "Move cleared noise threshold."  
CTA: "Track live in @polymarket_pulse_bot"

2. **"Top 3 movers in one shot"**  
Hook: "Three markets that just repriced."  
Data: 3 deltas on screen.  
Insight: "Momentum is concentrated, not broad."  
CTA: "Open bot from bio."

3. **"Why /movers can be zero"**  
Hook: "No, bot is not broken when movers = 0."  
Data: last/prev flat + 1h fallback logic.  
Insight: "Signals > spam."  
CTA: "Set threshold and watchlist."

4. **"One-market breakout"**  
Hook: "This one moved before most people noticed."  
Data: single market prev/now + delta.  
Insight: "Info shock > random noise."  
CTA: "Catch the next one in Telegram."

5. **"Watchlist in 1 tap"**  
Hook: "You can add a market in one tap now."  
Data: /menu -> Add market -> selected mover.  
Insight: "No manual market_id copy needed."  
CTA: "Try /menu in bot."

6. **"Threshold demo 0.03 vs 0.01"**  
Hook: "Want less noise? Keep 0.03."  
Data: compare alert counts on screen.  
Insight: "Lower threshold means more noise."  
CTA: "Tune with /threshold."

7. **"Free vs Pro limits"**  
Hook: "Here is what free gives you today."  
Data: 3 markets + 20 alerts/day; Pro unlimited.  
Insight: "Enough to validate value before upgrade."  
CTA: "Check /plan and /upgrade."

8. **"Signal inbox tour"**  
Hook: "What exactly arrives in inbox?"  
Data: question + delta + window screenshot.  
Insight: "Actionable context, not raw feed spam."  
CTA: "Run /inbox now."

9. **"Weekly recap short"**  
Hook: "Biggest 5 shifts this week."  
Data: top deltas list.  
Insight: "Same categories keep repricing fast."  
CTA: "Daily updates in Telegram."

10. **"From site click to live signal"**  
Hook: "Full flow in 20 seconds."  
Data: landing -> tg click -> /start -> /movers -> watchlist add.  
Insight: "60-second activation path."  
CTA: "Link in bio."

## Production notes
- Use `assets/social/top3-template.svg`, `assets/social/breakout-template.svg`, `assets/social/weekly-recap-template.svg`.
- Keep on-screen numbers in pp (`+7.0pp`) and include time window.
- Always end with CTA to `@polymarket_pulse_bot`.
