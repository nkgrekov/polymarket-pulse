# Polymarket Pulse — System Architecture

This document describes the technical architecture.

---

# Data Pipeline

Polymarket API  
→ ingest pipeline  
→ Postgres storage  
→ analytics views  
→ delivery layer

---

# Components

## Ingest

Python service.

Responsibilities:

• fetch market data  
• normalize responses  
• write snapshots  
• maintain universe coverage

Snapshot writes are the critical path.

Universe refresh runs after snapshot commit and is allowed to fail without failing the whole ingest run.

Runs periodically.

---

## Database

Supabase Postgres.

Stores:

markets  
market_snapshots  
market_universe  
user_positions  
user_watchlist

Derived views compute analytics.

---

## Analytics Layer

SQL views calculate signals.

Examples:

top_movers_latest  
portfolio_snapshot_latest  
alerts_latest  
alerts_inbox_latest

These views produce:

• probability deltas  
• spread signals  
• portfolio changes

---

## Delivery Layer

Telegram bot.

Reads alerts from database.

Commands:

/inbox  
/inbox20  
/movers  
/watchlist

Future:

push alerts.

---

# Universe System

Universe defines markets actively tracked.

Sources:

manual — explicit user watchlist markets  
position — user portfolio markets  
auto — live liquid markets with both latest and previous buckets

Universe ensures ingest coverage.

Current forced list in ingest:

manual watchlist  
market universe  
user positions

Universe refresh is a post-write step with its own timeout budget.

---

# Alert Engine

Alerts are generated when:

probability change exceeds threshold.

Alert flow:

market_snapshots  
→ analytics views  
→ alerts_latest  
→ alerts_inbox_latest  
→ bot

Live movers flow:

market_snapshots  
→ market_universe  
→ top_movers_latest  
→ /movers command

---

# Future Components

Public API

Web dashboard

User settings

Subscription management

Enterprise forecasting module
