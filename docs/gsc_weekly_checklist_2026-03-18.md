# Google Search Console Weekly Checklist

Use this once or twice per week while the domain is still young and Google is still deciding what to keep indexed.

## Main goals

• keep Google focused on English acquisition pages  
• catch canonical / redirect regressions early  
• push crawl attention toward pages that actually feed Telegram activation

## Canonical source of truth

Current public SEO layer is English-first.

Indexable pages:

• `https://polymarketpulse.app/`
• `https://polymarketpulse.app/analytics`
• `https://polymarketpulse.app/dashboard`
• `https://polymarketpulse.app/signals`
• `https://polymarketpulse.app/telegram-bot`
• `https://polymarketpulse.app/top-movers`
• `https://polymarketpulse.app/watchlist-alerts`
• `https://polymarketpulse.app/how-it-works`
• `https://polymarketpulse.app/commands`
• `https://polymarketpulse.app/trader-bot`

Non-goals:

• `http://` URLs indexing  
• `www.` URLs indexing  
• Russian query variants indexing  
• `/privacy` and `/terms` ranking

## Every-week checklist

1. Resubmit sitemap if the site structure changed:

• `https://polymarketpulse.app/sitemap.xml`

2. Check these GSC buckets:

• `Indexed`
• `Discovered, currently not indexed`
• `Alternate page with proper canonical tag`
• `Page with redirect`

3. Treat these as normal:

• `http://polymarketpulse.app/`
• `http://www.polymarketpulse.app/`
• `https://www.polymarketpulse.app/`

Those should stay in `Page with redirect`.

4. Treat these as action items if they show up:

• English acquisition pages in `Discovered, not indexed`
• English acquisition pages in `Alternate page with proper canonical`
• any English page with an unexpected canonical target

5. Request indexing manually only for the core 4 when needed:

• `https://polymarketpulse.app/`
• `https://polymarketpulse.app/analytics`
• `https://polymarketpulse.app/telegram-bot`
• `https://polymarketpulse.app/trader-bot`

Do not spam manual indexing for every page every day.

## What counts as success

Good movement:

• more EN pages in `Indexed`
• fewer EN pages in `Discovered, not indexed`
• redirect bucket stays stable

Bad movement:

• RU variants reappearing as indexed pages
• legal pages consuming index attention
• homepage and `/telegram-bot` losing index state

## If something regresses

Check in this order:

1. `https://polymarketpulse.app/sitemap.xml`
2. canonical tags on homepage + intent pages
3. `robots` meta on EN pages vs RU/legal pages
4. homepage internal links to:
   - `/analytics`
   - `/signals`
   - `/telegram-bot`
   - `/top-movers`
   - `/watchlist-alerts`
   - `/dashboard`
   - `/how-it-works`
   - `/commands`
   - `/trader-bot`

## Why this matters

At this stage the domain does not need more page variants.
It needs a cleaner crawl graph, clearer canonical intent, and more authority flowing into the pages that can actually send users into Telegram.
