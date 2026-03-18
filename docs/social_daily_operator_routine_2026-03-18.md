# Daily Social Operator Routine

This is the shortest valid manual publishing loop for `Pulse`.

## Goal

Answer one question before we post anything:

`Is the current Polymarket window fresh and liquid enough to deserve a post?`

If the answer is no, we skip. No filler posts.

## One-command start

From the repo root:

```bash
./scripts/growth/run_social_cycle.sh
```

Default gates:
- freshness: `<= 30m`
- liquidity: `>= 5000`
- delta floor: `>= 2pp`

## Outputs

The command refreshes:

- `docs/social_queue_latest.md`
- `docs/social_drafts_latest.md`

It also prints a single operator decision:

- `POST`
- `SKIP`

## If the decision is POST

1. Open `docs/social_queue_latest.md`
2. Publish `Slot 1 — X now`
3. Attach the video path listed in that slot
4. Wait before the next block
5. Re-run `./scripts/growth/run_social_cycle.sh`
6. Only then decide whether to publish the next slot

Reason:
- each posting block should use the freshest window we have, not stale leftovers from earlier in the day

## If the decision is SKIP

1. Do not post
2. Do not try to rescue the window with generic copy
3. Re-run later when the live set has refreshed

Reason:
- stale content harms trust faster than silence

## Publishing order

Current default order:

1. `X now — Manual Tabs Pain`
2. `Threads mirror — Manual Tabs Pain`
3. `X later — Alert Fatigue`
4. `X optional evening — Dashboard Overload`

## Rule of thumb

- X: at most `2–3` posts/day
- Threads: `1` mirror/adaptation for the strongest X post
- if the window is weak, publish less
- if the window is dead, publish nothing

## Asset contract

Current short videos:

- `assets/social/out/manual-tabs-pain-5s.mp4`
- `assets/social/out/alert-fatigue-5s.mp4`
- `assets/social/out/dashboard-overload-5s.mp4`

Always use the asset path specified in `docs/social_queue_latest.md`.

## Why this routine exists

We are deliberately avoiding:

- stale-but-pretty posting
- manual guesswork
- hype posts that are not tied to a real live move

The operator routine should feel as strict as the product itself:

`signal > noise`
