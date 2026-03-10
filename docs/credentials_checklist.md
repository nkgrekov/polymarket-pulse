# Credentials Checklist (Monetization + Distribution)

## Telegram Stars (Bot)

- Bot token (`BOT_TOKEN`) in Railway bot service.
- Product offer (fixed for iteration 1):
  - PRO monthly only
  - Watchlist limit: 20 markets
  - Includes email digest
  - Price: USD-equivalent of $10 in Stars at payment time
- Payment/support metadata:
  - support contact (`paysupport` email or username)
  - refund policy short text
  - links to terms/privacy pages
- Runtime config envs:
  - `PRO_WATCHLIST_LIMIT=20`
  - `PRO_MONTHLY_USD=10`
  - `TELEGRAM_STARS_PRICE_XTR=454`
  - `TELEGRAM_STARS_ENABLED=1`
  - `PRO_SUBSCRIPTION_DAYS=30`

## Stripe (Landing + Email channel)

- `STRIPE_SECRET_KEY` (test + live)
- `STRIPE_PUBLISHABLE_KEY` (optional for frontend SDK usage)
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID_MONTHLY` (and optional yearly id)
- `STRIPE_SUCCESS_URL` (optional override, default uses `/stripe/success`)
- `STRIPE_CANCEL_URL` (optional override)
- Stripe customer portal enabled (recommended)
- Domain for webhook and success/cancel URLs (`APP_BASE_URL`)

## Email (Resend)

- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL` (target: `Polymarket Pulse <welcome@polymarketpulse.app>`)
- Domain status in Resend must stay `Verified`

## Social API (semi-auto content)

### X API
- app/client id + secret
- user access token with post/write scope
- account/user ids used for posting

### Threads API
- Meta app id + secret
- long-lived user token
- app in live mode with required permissions

### TikTok Content Posting API
- app client key + secret
- creator OAuth token
- app review/approval status for public posting

## Security rules

- Do not send secrets in chats/commits.
- Put secrets only in Railway variables and GitHub Actions secrets.
- Rotate keys immediately if exposed.
