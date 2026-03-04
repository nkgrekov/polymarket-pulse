#!/usr/bin/env bash
set -euo pipefail

BOT_DIR="/Users/nikitagrekov/polymarket-pulse/bot"
touch "$BOT_DIR/launchd.stdout.log" "$BOT_DIR/launchd.stderr.log" "$BOT_DIR/bot.log"
tail -f "$BOT_DIR/launchd.stdout.log" "$BOT_DIR/launchd.stderr.log" "$BOT_DIR/bot.log"
