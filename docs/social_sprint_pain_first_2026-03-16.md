# Pain-First Social Sprint (2026-03-16)

Goal: drive qualified `tg_click -> /start -> watchlist_add` by speaking to Polymarket users in the language of their real friction, not generic crypto hype.

Channels:
- X: primary
- Threads: secondary, softer versions of the same posts
- Shorts/Reels/TikTok reuse: only for the strongest pain-first posts

Core messaging rules:
- Speak to manual workflow pain, alert fatigue, and delayed reaction time.
- No generic alpha slang, no empty FOMO slogans, no shallow “before everyone else” spam.
- Every post must describe:
  - one real market workflow problem
  - one cleaner alternative
  - one next step
- CTA hierarchy:
  - primary: `Open Telegram Bot`
  - secondary only when relevant: `Keep Email as Backup`
  - trader CTA only for power-user/execution posts

Brand rules:
- Visual palette: `#0d0f0e`, `#131714`, `#1e2520`, `#e8ede9`, `#8fa88f`, `#6b7a6e`, `#00ff88`
- Typography feel: terminal/editorial, readable, high-contrast, no candy colors
- Tone: sharp, credible, slightly dry, helpful, not loud

## Audience Pain Pillars

### 1. Manual tab-scanning is too slow
What they feel:
- by the time they notice a move, it is already old
- they keep too many tabs open and still miss repricing

Message shape:
- “The problem isn’t lack of data. It’s how manual your workflow still is.”

### 2. Most signal feeds are spam
What they feel:
- too many alerts, too little trust
- repeated pushes train them to ignore the feed

Message shape:
- “If your alerts fire on every twitch, you stop checking them.”

### 3. Dashboards create browsing, not action
What they feel:
- too much chart theater
- too little clarity about what changed and whether it matters

Message shape:
- “You don’t need another dashboard tab. You need one clear answer.”

### 4. Watchlists decay silently
What they feel:
- markets close
- quotes disappear
- their watchlist gets stale without them noticing

Message shape:
- “Your watchlist shouldn’t become a graveyard just because markets rotated.”

### 5. Signal and execution still live in different places
What they feel:
- they see the move in one place and act in another
- too many steps between noticing and deciding

Message shape:
- “Seeing the move is one workflow. Acting on it is another. We’re collapsing that gap.”

## 7-Day Posting Plan

### Day 1
Post A1 (X + Threads)
- Hook: Most Polymarket workflows are still manual.
- Body: By the time you notice a move, it usually isn’t a discovery anymore. It’s just confirmation that your tab stack is too slow.
- CTA: Track repricing in Telegram: https://t.me/polymarket_pulse_bot
- UTM: `utm_source=x&utm_medium=social&utm_campaign=manual_workflow_pain`

Post A2 (X only)
- Hook: The issue isn’t “not enough data.”
- Body: It’s too much scanning. What moved, by how much, and does it matter right now? That’s the whole job.
- CTA: https://polymarketpulse.app/analytics

### Day 2
Post B1 (X + Threads)
- Hook: If your alert feed cries wolf all day, you stop trusting it.
- Body: Low-noise signals are more useful than high-volume signals. Thresholds and dedup matter more than “more alerts.”
- CTA: https://polymarketpulse.app/signals

Post B2 (X only)
- Hook: Flat market? Good.
- Body: A decent signal product should stay quiet when the market is quiet instead of inventing urgency.
- CTA: https://t.me/polymarket_pulse_bot

### Day 3
Post C1 (X + Threads)
- Hook: Dashboard overload is not the same thing as intelligence.
- Body: Most Polymarket tools are built to be browsed. We’re trying to build one that gets you to action faster.
- CTA: https://polymarketpulse.app/telegram-bot

Post C2 (X only)
- Hook: One useful market in your watchlist beats twenty dead ones.
- Body: A good watchlist should tell you what still deserves attention, not just preserve old decisions.
- CTA: https://polymarketpulse.app/watchlist-alerts

### Day 4
Post D1 (X + Threads)
- Hook: Top movers should be the beginning of a workflow, not the end of one.
- Body: Move -> add -> threshold -> inbox. If a tool stops at “here’s a chart,” it left the useful part to you.
- CTA: https://polymarketpulse.app/top-movers

Post D2 (X only)
- Hook: Telegram is not the gimmick.
- Body: Telegram is just the shortest distance between “that market moved” and “I should look at this now.”
- CTA: https://t.me/polymarket_pulse_bot

### Day 5
Post E1 (X + Threads)
- Hook: Most execution bots start with action. Ours starts with signal quality.
- Body: There is no point trading faster if the thing you’re reacting to was noisy in the first place.
- CTA: https://polymarketpulse.app/trader-bot

Post E2 (X only)
- Hook: Copy-trading without signal context is just outsourced conviction.
- Body: We care more about what actually repriced than who clicked first.
- CTA: https://polymarketpulse.app/trader-bot

### Day 6
Post F1 (X + Threads)
- Hook: The best quiet-state is the one that makes sense.
- Body: If nothing meaningful moved, the product should tell you that plainly and move on.
- CTA: https://polymarketpulse.app/signals

Post F2 (X only)
- Hook: Watchlists decay.
- Body: Closed markets, missing quotes, stale assumptions. A decent workflow has to acknowledge that instead of pretending your old list is still live.
- CTA: https://t.me/polymarket_pulse_bot

### Day 7
Post G1 (X thread)
- Hook: 3 things Polymarket users actually need from a signal product.
- Body outline:
  1. less manual scanning
  2. fewer useless alerts
  3. a cleaner path from signal to action
- CTA: https://polymarketpulse.app/telegram-bot

Post G2 (Threads)
- Softer recap version of the thread with one real example and a Telegram CTA.

## Conversion Notes
- Every post should map back to one product layer:
  - `Pulse` for discovery/signals
  - `Trader` only when the post is specifically about execution gap
- We should not over-send people to Trader while Pulse traffic is still thin.
- Rough split:
  - 75% Pulse
  - 25% Trader

## UTM Rules
- X: `utm_source=x&utm_medium=social`
- Threads: `utm_source=threads&utm_medium=social`
- Campaign names should match pain theme, not generic dates:
  - `manual_workflow_pain`
  - `alert_fatigue`
  - `dashboard_overload`
  - `watchlist_decay`
  - `signal_to_execution`

## Operational Blocker: X Posting Access
Current status:
- OAuth1 auth works for read-level identity access
- posting is currently blocked by X app permissions

Verified result:
- `POST /2/tweets` returns:
  - `403 Forbidden`
  - `Your client app is not configured with the appropriate oauth1 app permissions for this endpoint.`

What needs to be changed in X Developer Portal:
1. Set app permissions to `Read and write`
2. Save the auth settings
3. Regenerate:
  - Access Token
  - Access Token Secret
4. Give the new pair back to Codex

After that, we can test safely again before real posting.
