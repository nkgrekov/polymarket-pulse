# Polymarket Pulse — Product Manifest

## Core Idea

Prediction markets are one of the cleanest signals about the future.

Polymarket provides the trading infrastructure.
We build the **intelligence layer on top of it**.

Our mission:

Build the analytics, signals, and decision infrastructure for probability markets.

We are not building an exchange.

We are building the **data and intelligence layer for forecasting markets.**

---

# Layer Philosophy

The product evolves in layers.

Each layer:

• consumes data from the previous layer  
• creates new user value  
• unlocks a new revenue stream  

We do not build everything at once.

We move layer by layer.

---

# System Layers

Layer I — Polymarket (external platform)

Layer II — Data Layer  
Layer III — Trading Tools  
Layer IV — News & Sentiment  
Layer V — AI & Community  
Layer VI — Enterprise Forecasting

---

# Layer II — Data Layer

## Value Hypothesis

People want signals about market probability shifts.

Not the raw interface.

They want answers like:

• Which markets moved the most in the last hour  
• Where liquidity is suddenly increasing  
• What markets are trending now

## Product

Market Movers Dashboard

Public:

• Top probability shifts  
• Trending markets  
• Liquidity spikes  

Delivery doctrine:

• user-facing analytics must feel live, not batch-delayed  
• the primary signal loop should not depend on slow scheduled rebuilds  
• live relevance comes first, historical storage comes second  
• history still matters, but it should not bottleneck first-value UX

Runtime principle:

• user surfaces should read from a fast internal live layer fed by Polymarket APIs  
• the same ingest path should still write historical data into our database  
• we do not query Polymarket directly on every user request if that adds latency or instability  
• we centralize live fetch once, then serve bot/site from our own hot derived surfaces

Private API:

• /api/movers  
• /api/liquidity  
• /api/trending_new

## Monetization

Subscription API access.

Price range:

$19–29/month

Target users:

• crypto traders  
• political analysts  
• Telegram signal channels  

## Success Metric

Layer II succeeds when:

• 100+ daily visitors to dashboard  
• 10+ paying API users

Operational success condition:

• `Pulse` can show live market changes on a cadence closer to market reality than the current scheduled ingest path  
• live movers, watchlists, and alerts stay useful even when historical bucket writes are delayed  
• the live layer and the historical layer reinforce each other instead of blocking each other

## Layer II Modernization Rule

We will modernize the data layer carefully.

That means:

• no big-bang rewrite  
• no direct-to-API product requests as the default runtime  
• no replacement of the current database history layer  
• no breaking change to the existing bot contract first

Instead we will:

• add a faster live ingest path  
• add fast internal hot surfaces for user-facing analytics  
• keep writing historical snapshots to the database  
• migrate the bot and the site step by step onto the new hot layer  
• keep GitHub Actions as backup / reconciliation, not as the primary live engine

---

# Layer III — Trading Tools

## Hypothesis

Polymarket users lack portfolio analytics.

Pain points:

• no portfolio overview  
• unclear PnL  
• no probability alerts  

## Product

Portfolio Tracker

Features:

• wallet connection  
• position overview  
• entry probability  
• current probability  
• exposure distribution  

Alerts example:

"Your position in BTC > $100k dropped from 42% to 29%."

## Monetization

$15/month subscription

Pro bundle:

$29/month including Data API.

## Success Metric

30+ paying users.

Retention > 1 month.

---

# Layer IV — News & Sentiment

## Hypothesis

Traders see probability changes but not the cause.

## Product

Movement explanation feed.

Example:

"ETH ETF probability jumped from 37% to 51% after WSJ report."

The system connects:

news → market → probability change.

## Monetization

Sentiment Digest subscription.

Price:

$49/month.

Audience:

• funds  
• analysts  
• media

---

# Layer V — AI & Community

## Hypothesis

Users struggle to formulate prediction markets.

## Product

AI Market Creator.

User enters:

"Will Apple release Vision Pro 2 before 2026?"

System generates:

• clear question  
• resolution criteria  
• verification rules  

Also includes:

• trading discussions  
• private community  
• learning resources

## Monetization

Community subscription.

$20–30/month.

---

# Layer VI — Enterprise

## Hypothesis

Prediction markets improve internal decision making.

Example questions:

• Will feature X ship before June  
• Will revenue exceed $5M  

## Product

Enterprise forecasting platform.

Internal prediction markets.

No crypto required.

Gamified forecasting.

## Monetization

Enterprise SaaS.

$1000+ per month.

---

# Strategic Vision

Start as a tool for traders.

Evolve into a forecasting intelligence platform.

Eventually become the infrastructure layer for decision forecasting.

---

# UX Manifest (Mandatory)

Live-first value must be matched by interface consistency.

Design system is product logic, not decoration.

Rules:

• All site pages use one dark terminal aesthetic (`#0d0f0e` / `#0a0c0b` backgrounds, dark cards, off-white text).  
• Accent green (`#00ff88`) is reserved for positive/active/CTA states only.  
• Accent red (`#ff4444`) is reserved for negative deltas only.  
• No light-theme sections, no yellow CTA variants, no visual drift between landing and subpages.  
• Data rows, tags, and callouts must use the same component language across pages.  
• Signal clarity beats ornament: no noisy effects that hide numeric meaning.
