# Hot vs Legacy Delivery Comparison (2026-03-31T07:13:27.692947+00:00)

Source surfaces:

- `public.hot_alert_candidates_latest`
- `bot.alerts_inbox_latest`
- `bot.sent_alerts_log`

## Summary

- hot_all_count: **9**
- hot_ready_count: **0**
- legacy_watchlist_count: **0**
- legacy_all_count: **0**
- sent_recent_count (24h): **3**
- hot_legacy_watchlist_overlap: **0**
- hot_sent_overlap (24h): **0**

Verdict: Current window is quiet on both hot and legacy watchlist inbox surfaces.

## Hot Candidate State Breakdown

- closed: **6**
- below_threshold: **3**

## Hot Candidate Sample

- user_id=4c0301d1-20fc-4fdf-949e-028c5c9acc42 | market_id=1743638 | candidate_state=below_threshold | delta_abs=0.0050000000000000044 | threshold_value=0.03 | quote_ts=2026-03-31 07:12:46.770593+00:00
- user_id=59ffaefc-0c85-4825-9dbb-65ff5d6d2d9a | market_id=1559112 | candidate_state=below_threshold | delta_abs=0.0 | threshold_value=0.03 | quote_ts=2026-03-31 07:12:46.770593+00:00
- user_id=59ffaefc-0c85-4825-9dbb-65ff5d6d2d9a | market_id=1634432 | candidate_state=closed | delta_abs=0.0 | threshold_value=0.03 | quote_ts=2026-03-31 07:12:46.770593+00:00
- user_id=b2e0403d-af8d-4d0f-b88e-a50e76488fc3 | market_id=1498833 | candidate_state=closed | delta_abs=0.0 | threshold_value=0.03 | quote_ts=2026-03-31 07:12:46.770593+00:00
- user_id=b2e0403d-af8d-4d0f-b88e-a50e76488fc3 | market_id=1498834 | candidate_state=closed | delta_abs=0.0 | threshold_value=0.03 | quote_ts=2026-03-31 07:12:46.770593+00:00
- user_id=b2e0403d-af8d-4d0f-b88e-a50e76488fc3 | market_id=1498835 | candidate_state=closed | delta_abs=0.0 | threshold_value=0.03 | quote_ts=2026-03-31 07:12:46.770593+00:00
- user_id=b2e0403d-af8d-4d0f-b88e-a50e76488fc3 | market_id=1498836 | candidate_state=closed | delta_abs=0.0 | threshold_value=0.03 | quote_ts=2026-03-31 07:12:46.770593+00:00
- user_id=4c0301d1-20fc-4fdf-949e-028c5c9acc42 | market_id=1529720 | candidate_state=below_threshold | delta_abs=0.0 | threshold_value=0.03 | quote_ts=2026-03-31 07:12:46.770593+00:00
- user_id=b2e0403d-af8d-4d0f-b88e-a50e76488fc3 | market_id=1498928 | candidate_state=closed | delta_abs=0.0 | threshold_value=0.03 | quote_ts=2026-03-31 07:12:46.770593+00:00

## Legacy Inbox Sample

- none

## Recent Sent Alerts (24h)

- user_id=4c0301d1-20fc-4fdf-949e-028c5c9acc42 | market_id=1743638 | alert_type=watchlist | bucket=2026-03-31 03:30:00+00:00 | sent_at=2026-03-31 03:33:31.883985+00:00
- user_id=4c0301d1-20fc-4fdf-949e-028c5c9acc42 | market_id=1743638 | alert_type=watchlist | bucket=2026-03-30 23:50:00+00:00 | sent_at=2026-03-31 02:41:52.985359+00:00
- user_id=4c0301d1-20fc-4fdf-949e-028c5c9acc42 | market_id=1743638 | alert_type=watchlist | bucket=2026-03-30 08:00:00+00:00 | sent_at=2026-03-30 08:06:04.538450+00:00

## Notes

- `hot_ready_count` reflects only watchlist candidates with `candidate_state = 'ready'` in the latest hot pass.
- `legacy_watchlist_count` reflects only `alert_type='watchlist'` rows currently visible in `bot.alerts_inbox_latest`.
- `sent_recent_count` is historical tail, so it may stay non-zero even when both current surfaces are quiet.
- Use this report to decide whether push delivery can move to hot-first safely.
