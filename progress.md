# Polymarket Pulse — Implementation Progress

This document tracks the current state of the project.

---

# Layer 0 — Data Infrastructure

The data pipeline collects probability market data from Polymarket.

This infrastructure powers all analytics layers.

---

# Current Stack

Data ingestion:

Python pipeline.

Database:

Supabase (Postgres).

---

# Current Tables

markets

market_snapshots

market_universe

user_positions

sent_alerts_log

---

# Snapshot System

Snapshots store market states over time.

Columns include:

market_id  
ts_bucket  
yes_price  
no_price  
liquidity  
yes_bid  
yes_ask  
no_bid  
no_ask  

Snapshots allow:

• probability change detection  
• liquidity tracking  
• historical analysis

---

# Market Universe

Table:

public.market_universe

Purpose:

Defines active markets tracked by the system.

Sources:

auto — top markets by liquidity  
position — markets from user positions  

Universe guarantees:

• ingest coverage  
• consistent analytics scope

---

# Live Market Detection

Markets are considered live when:

• they appear in recent snapshots  
• they exist in market_universe

Expired markets are excluded from alerts.

---

# Analytics Views

Key derived views:

top_movers_latest  
portfolio_snapshot_latest  
alerts_latest  
alerts_inbox_latest

These views power signal generation.

---

# Telegram Bot MVP

Minimal Telegram bot implemented.

Commands:

/start  
/inbox  
/inbox20  

The bot reads signals from:

alerts_inbox_latest

The bot does not call Polymarket API directly.

All data comes from the database layer.

---

# Current System Pipeline

Polymarket API  
→ ingest pipeline  
→ Supabase database  
→ analytics views  
→ Telegram alerts

---

# Current Product State

The project currently operates as:

Live market alert engine.

---

# Next Milestones

Push alerts (scheduled signals)

Multi-user configuration

Billing layer

Hosted infrastructure