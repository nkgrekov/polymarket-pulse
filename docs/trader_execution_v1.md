# Trader Execution V1

Date: 2026-03-13

This document captures the first public contract for the sibling execution product.

## Product Split

`Pulse`:
- live movers
- watchlist alerts
- inbox signals
- AI explainer / market interpretation

`Trader`:
- execution in Telegram
- positions / orders / fills
- follow flow
- rule-based AI trader agent

## Public Scope

Platform:
- Polymarket only

Custody:
- non-custodial first

Autonomy:
- manual by default
- `rule_auto` only inside explicit user rules

## Command Surface

Planned public commands:
- `/start`
- `/connect`
- `/markets`
- `/buy`
- `/sell`
- `/order`
- `/positions`
- `/follow`
- `/rules`
- `/agent`
- `/risk`
- `/pause`
- `/help`

## Rule Primitives

Required for public alpha:
- max order size
- category allowlist
- market allowlist
- daily trade cap
- daily loss cap
- per-market exposure cap
- slippage ceiling
- cooldown window
- kill switch
- confirm mode toggle

## Data Contract

Execution data is isolated in `trade.*`:
- `trade.accounts`
- `trade.wallet_links`
- `trade.positions_cache`
- `trade.orders`
- `trade.executions`
- `trade.follow_sources`
- `trade.follow_rules`
- `trade.agent_rules`
- `trade.agent_decisions`
- `trade.risk_state`
- `trade.activity_events`
- `trade.alpha_waitlist`

## Rollout Sequence

1. Alpha waitlist and product handoff from Pulse.
2. Wallet connect + manual execution skeleton.
3. Positions/order state reconciliation.
4. Follow flow.
5. Rule-based AI trader agent.


## V0 Alpha Runtime (2026-03-14)

Implemented sibling bot runtime in `trader_bot/`.

Shipped commands:
- `/start`
- `/help`
- `/connect`
- `/markets`
- `/buy`
- `/sell`
- `/order`
- `/positions`
- `/follow`
- `/rules`
- `/risk`
- `/pause`
- `/agent`

What this runtime does today:
- resolves Telegram identity into existing `app.*` + `bot.*` user model
- ensures `trade.accounts` row exists for each trader-bot user
- logs bot activity into `trade.activity_events`
- stores primary wallet registration in `trade.wallet_links`
- stores manual order drafts in `trade.orders` with status `pending`
- exposes `trade.positions_cache`, `trade.agent_rules`, `trade.risk_state`, and `trade.agent_decisions`
- stores follow-source intent in `trade.follow_sources` + `trade.follow_rules`

Important boundary:
- this is still non-custodial alpha scaffolding
- no live order routing is enabled yet
- order creation in v0 means `draft recorded`, not `executed on Polymarket`

## Execution Worker V0 (2026-03-14)

Implemented a separate dry-run worker in `trade_worker/`.

Current worker contract:
- polls `trade.orders` with `status='pending'`
- validates:
  - primary wallet presence
  - signer readiness (`trade.wallet_links.status`)
  - pause / kill-switch state
  - order-size and daily-cap guardrails
- writes outcome in-place to `trade.orders`
- emits worker telemetry to `trade.activity_events`

Status transitions in current mode:
- valid draft -> `submitted` with synthetic `external_order_id` (`dryrun:*`)
- invalid draft -> `rejected` with explicit reason in worker event payload

This worker is intentionally pre-routing:
- no Polymarket execution request yet
- no fill reconciliation yet
- no live `trade.executions` writes yet

## Signer Session Layer V0 (2026-03-15)

Implemented the first honest signer/delegation bridge instead of a fake "execution unlocked" toggle.

New foundation:
- migration `db/migrations/010_trade_signer_sessions.sql`
- table `trade.signer_sessions`

Current contract:
- `/signer` in `trader_bot` creates or reuses a live signer session for the user's primary wallet
- bot returns:
  - wallet
  - signer session status
  - challenge text
  - direct verification page URL
- `GET /trader-connect?token=...` opens a branded signer page in the main site runtime
- page view moves session from `new` -> `opened`
- `POST /api/trader-signer/submit` stores pasted signed payload in `trade.signer_sessions.signed_payload`
- payload submission moves session from `opened/new` -> `signed`

Important boundary:
- this is still not cryptographic verification
- wallet status in `trade.wallet_links` remains non-active until a real signer verification / activation layer is implemented
- worker will still reject real execution attempts while wallet status remains `pending`

Why this matters:
- gives us a real end-to-end signer funnel to test in production
- creates the correct DB + UX contract for the next phase
- avoids pretending that execution is live before actual signature verification exists

## Manual Activation Contract V0 (2026-03-15)

Added the first honest operator-review activation path for alpha users.

New DB function:
- `trade.activate_signer_session(session_token, signer_ref, operator_note)`

What it does:
- requires signer session status `signed`
- moves signer session to `verified`
- stamps `verified_at`
- activates the linked wallet in `trade.wallet_links`
- switches wallet signer mode to `session`
- stores `signer_ref`
- emits `trade.activity_events.event_type='signer_activated'`

Operator runtime:
- script: `scripts/ops/activate_signer_session.py`
- review queue helper: `scripts/ops/list_signer_sessions.py`

Example:

```bash
bot/.venv/bin/python scripts/ops/activate_signer_session.py <session_token> --signer-ref operator:alpha --note "manual alpha approval"
```

Boundary:
- this is still manual operator review, not automatic cryptographic verification
- it is the bridge that lets alpha testing move from `payload captured` to `wallet active`

Suggested operator loop:

```bash
bot/.venv/bin/python scripts/ops/list_signer_sessions.py --statuses signed --limit 20
bot/.venv/bin/python scripts/ops/activate_signer_session.py <session_token> --signer-ref operator:alpha --note "manual alpha approval"
```
