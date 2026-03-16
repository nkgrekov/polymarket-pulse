# Short-Form Video Briefs For Pain-First Social Posts (2026-03-16)

These are not generic ads. Each clip exists to intensify one concrete audience pain from the social sprint.

Global render rules:
- Duration: 3-5 seconds
- Aspect ratio: 9:16
- Palette: `#0d0f0e`, `#131714`, `#1e2520`, `#e8ede9`, `#8fa88f`, `#00ff88`
- Typography: terminal/editorial, readable, no playful motion
- Motion: glitch/editorial cuts, not random chaos
- Data: use real current DB values where available
- Final button: Telegram handle or clean CTA, never a hype slogan

## Brief 1 — Manual Tabs Pain
Post pairing:
- Day 1 / Post A1

Thesis:
- This video makes manual Polymarket tab-scanning feel like a laggy emergency room waiting area.

On-screen sequence:
1. `12 tabs open` on dark browser chrome
2. `move already happened` over one highlighted market card
3. `workflow too manual` hard cut on black/green terminal card
4. `@polymarket_pulse_bot` final button

Data layer:
- one real mover question
- `prev -> now`
- one delta line

Audio:
- muted UI clicks
- one low hit
- no voice required

## Brief 2 — Alert Fatigue
Post pairing:
- Day 2 / Post B1

Thesis:
- This video makes a noisy alert feed feel like an alarm system people stopped listening to.

On-screen sequence:
1. stacked fake alert cards flicker in
2. one line freezes: `too many alerts = no trust`
3. clean green card: `threshold + dedup`
4. final button: `Signals > spam`

Audio:
- short stutter beeps
- one silence cut before final frame

## Brief 3 — Dashboard Overload
Post pairing:
- Day 3 / Post C1

Thesis:
- This video makes a dashboard wall feel like decorative delay.

On-screen sequence:
1. many tiny boxes/charts flash for under a second
2. one card punches through: `what moved?`
3. follow-up card: `by how much?`
4. final card: `does it matter now?`

Audio:
- newsroom/terminal pulse
- restrained, no hype riser

## Brief 4 — Watchlist Decay
Post pairing:
- Day 6 / Post F2

Thesis:
- This video makes a stale watchlist feel like a graveyard of old convictions.

On-screen sequence:
1. list of three markets, two dim to `closed`
2. `quotes missing` flashes on one line
3. `replace dead markets fast`
4. final button to bot handle

Audio:
- low drone
- one dry click per list change

## Brief 5 — Signal To Execution Gap
Post pairing:
- Day 5 / Post E1

Thesis:
- This video makes signal and execution feel like two windows that should have been one workflow.

On-screen sequence:
1. market move card appears
2. second panel: `now what?`
3. split frame: `Pulse finds` / `Trader acts`
4. final button: `Powered by signal quality`

Audio:
- subtle dual-tone pulse
- short dropout before final frame

## Brief 6 — Quiet State Is A Feature
Post pairing:
- Day 6 / Post F1

Thesis:
- This video makes silence in a flat market feel like product discipline, not absence.

On-screen sequence:
1. flat sparkline
2. `no meaningful move` appears cleanly
3. `good` flashes in muted green/gray
4. final frame: `less noise, more trust`

Audio:
- almost silent
- one clean low click

## Brief 7 — Top Movers To Watchlist Flow
Post pairing:
- Day 4 / Post D1

Thesis:
- This video makes a mover feel unfinished until it turns into a tracked decision.

On-screen sequence:
1. `top mover` card with real delta
2. `add to watchlist` card
3. `set threshold` card
4. `inbox ready` final card

Audio:
- three short action ticks
- no TTS required

## Render Prompt Template
Use this template with the video workflow:

- Query: `<pain theme> Polymarket Pulse vertical short 5s, dark terminal, pain-first, brand-safe, no hype, real market data`
- Material summary: `<paired post text> + <real mover/watchlist data> + <brief thesis and scene sequence above>`
- Output: `1080x1920`, `3-5s`, H.264 MP4

## Production Rule
Do not render a clip just because a post exists.
Render only when:
- the pain is clear
- the CTA is clear
- the visual contrast can be understood in under 5 seconds
