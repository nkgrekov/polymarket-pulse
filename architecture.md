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

Runs periodically.

---

## Database

Supabase Postgres.

Stores:

markets  
market_snapshots  
market_universe  
user_positions

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

Future:

push alerts.

---

# Universe System

Universe defines markets actively tracked.

Sources:

auto — top liquidity markets  
position — user portfolio markets

Universe ensures ingest coverage.

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

---

# Future Components

Public API

Web dashboard

User settings

Subscription management

Enterprise forecasting module