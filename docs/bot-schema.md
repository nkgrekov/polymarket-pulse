# Bot Schema Proposal

## Goal

Move Telegram-specific state into a dedicated `bot` schema without breaking the current market/ingest flow in `public`.

## Why This Shape

- Current bot code uses a hardcoded `DEFAULT_USER_ID` and does not know real Telegram identities.
- Current ingest already depends on `public.watchlist.user_id`.
- The clean migration path is to introduce a bot-owned identity layer first, then gradually move reads from `public.watchlist` to `bot.market_subscriptions`.

## Proposed Core Model

- `bot.app_users`
  - Stable internal user identity for bot workflows.
  - `app_user_key` matches current legacy `user_id` values like `nikita`.

- `bot.telegram_users`
  - Telegram user profile metadata from updates.

- `bot.telegram_chats`
  - Delivery target registry for private chats / groups / channels.

- `bot.chat_links`
  - Bridge between `bot.app_users` and Telegram chats/users.
  - Lets one internal user receive alerts in one or many chats.

- `bot.chat_settings`
  - Per-chat defaults such as inbox size, locale, timezone, notifications flag.

- `bot.market_subscriptions`
  - Bot-owned replacement for user market watchlists/subscriptions.
  - References `public.markets(market_id)`.

- `bot.alert_rules`
  - Per-user alert thresholds and cooldowns.

- `bot.outbound_messages`
  - Delivery log + idempotency layer for Telegram sends.
  - Prevents duplicate alerts when retries happen.

- `bot.command_audit`
  - Audit trail of commands and failures.

## Compatibility Layer

The migration also defines two views:

- `bot.v_chat_targets`
  - Resolved active delivery targets per internal user.

- `bot.v_watchlist_market_subscriptions`
  - Projects bot subscriptions into a legacy `user_id` shape.
  - Intended as a bridge for current ingest/bot code while `public.watchlist` is still in use.

## Recommended Rollout

### Phase 1

- Apply `db/migrations/001_bot_schema.sql`.
- Seed `bot.app_users` with existing legacy users from `public.watchlist.user_id`.
- On `/start`, upsert:
  - `bot.telegram_users`
  - `bot.telegram_chats`
  - `bot.chat_links`
  - `bot.chat_settings`

### Phase 2

- Replace `DEFAULT_USER_ID` in the bot with a lookup:
  - `telegram_chat_id -> bot.chat_links -> bot.app_users.app_user_key`
- Read inbox using resolved `app_user_key`.

### Phase 3

- Add `/watch`, `/unwatch`, `/watchlist` commands on top of `bot.market_subscriptions`.
- Optionally mirror writes into `public.watchlist` during transition.

### Phase 4

- Move alert delivery dedupe from `public.sent_alerts_log` into `bot.outbound_messages`.
- Add worker flow for queued sends if needed.

## Important Caveats

- This migration is created locally only; it has not been applied to Supabase.
- Current MCP runtime can read table metadata, but `execute_sql` still hangs, so applying or validating DDL through MCP is not safe yet.
- `public.sent_alerts_log.market_id bigint` does not match `public.markets.market_id text`; do not copy that mismatch into the new bot schema.
