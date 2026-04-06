# Railway Hobby Ops Runbook (2026-04-06)

## Goal

Keep the current Railway Hobby posture stable without changing production runtime impulsively.

This is a local ops runbook, not a deploy playbook.

## Current Production Services

Confirmed via read-only Railway CLI on `2026-04-06`:

- `site`
  - latest deployment: `6868c117-5600-4173-981d-ccf18c755605`
  - status: `SUCCESS`
- `bot`
  - latest deployment: `ba41e914-b3a0-4be6-a517-8b49201e9b23`
  - status: `SUCCESS`
- `ingest`
  - latest deployment: `aa7bbe26-52c8-45c8-83fe-e1fbdb561302`
  - status: `SUCCESS`
- `trader-bot`
  - latest deployment: `541177fb-68da-4800-a208-a76c5b4ae50e`
  - status: `SUCCESS`
- `trade-worker`
  - latest deployment: `41fb90d1-52d8-4753-9f0d-d2e8623722a5`
  - status: `SUCCESS`

Important distinction:

- this is the **current deployed posture**
- it is not automatically the **recommended Hobby posture**

## Recommended Hobby Posture

### Always-On

These should stay alive by default:

- `site`
- `bot`
- `ingest`

Why:

- `site` is the public acquisition surface
- `bot` must keep Telegram polling stable
- `ingest` is now the primary live data runtime

### Park By Default

These should be parked unless actively needed:

- `trade-worker`
- `trader-bot`

Recommended rule:

- keep both parked unless `Trader` alpha is actively being tested or demoed
- if `Trader` is dormant, do not spend Hobby budget keeping these alive

## Main Hobby Risks

1. Silent spend creep from non-core services
- the main risk is not `site/bot/ingest`
- it is leaving `trader-bot` and `trade-worker` running when they are not needed

2. Auth drift in local Railway CLI
- we already saw the local CLI session expire
- this can slow incident response even when the services are healthy

3. Restart confusion during bot deploys
- brief Telegram `409 Conflict` during restart is normal
- panic-restarting the bot twice can create false outage noise

## Billing Guardrails

### Minimum guardrails

- set a soft usage alert above normal Hobby expectations
- set a hard stop above “worth investigating” but below “surprise bill”

Suggested starting numbers:

- soft alert: `$7`
- hard limit: `$10` to `$12`

Why:

- base `Hobby` is cheap
- the goal is to catch accidental always-on non-core services early

### Service discipline

- `site`, `bot`, `ingest`: budget as the baseline core stack
- `trader-bot`, `trade-worker`: treat as opt-in spend

## Read-Only Smoke Commands

Use these when you want to verify posture without mutating production:

```bash
cd /Users/nikitagrekov/polymarket-pulse
railway whoami
railway status
railway service status
railway deployment list --service site | sed -n '1,20p'
railway deployment list --service bot | sed -n '1,20p'
railway deployment list --service ingest | sed -n '1,20p'
railway deployment list --service trader-bot | sed -n '1,20p'
railway deployment list --service trade-worker | sed -n '1,20p'
```

App/runtime smoke:

```bash
curl -sS https://polymarketpulse.app/api/live-movers-preview?limit=1 | jq '.[0]'
```

Bot/ingest log smoke:

```bash
railway service logs --service bot --lines 50
railway service logs --service ingest --lines 50
```

## Practical Next Ops Actions

1. Keep `site`, `bot`, and `ingest` as the explicit core runtime.
2. Park `trader-bot` and `trade-worker` whenever alpha is not actively in use.
3. Add Hobby spend alerts/limit in the Railway dashboard and treat them as operational guardrails, not finance cleanup later.
