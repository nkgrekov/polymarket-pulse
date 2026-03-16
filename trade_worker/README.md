# Trade Worker

Dry-run execution worker for the Trader alpha lane.

Current behavior:
- polls `trade.orders` with `status='pending'`
- validates wallet/signer/risk guardrails
- writes either:
  - `submitted` + `trade.activity_events` (`order_submitted_dry_run`)
  - or `rejected` + `trade.activity_events` (`order_rejected`)
- bumps `trade.risk_state` counters on dry-run submit

This worker does not place real Polymarket orders yet.
It is the first execution state-machine layer before signer + routing integration.
