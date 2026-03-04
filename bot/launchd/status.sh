#!/usr/bin/env bash
set -euo pipefail

LABEL="com.nikitagrekov.polymarket-pulse-bot"
DOMAIN="gui/$(id -u)"
PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"

if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
  launchctl print "$DOMAIN/$LABEL"
else
  echo "Service is not loaded: $LABEL"
  echo "plist: $PLIST_DST"
fi
