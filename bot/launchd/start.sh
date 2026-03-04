#!/usr/bin/env bash
set -euo pipefail

LABEL="com.nikitagrekov.polymarket-pulse-bot"
PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"
DOMAIN="gui/$(id -u)"

if [[ ! -f "$PLIST_DST" ]]; then
  echo "Missing plist: $PLIST_DST" >&2
  echo "Run install.sh first." >&2
  exit 1
fi

if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
  launchctl kickstart -k "$DOMAIN/$LABEL"
else
  launchctl bootstrap "$DOMAIN" "$PLIST_DST"
  launchctl enable "$DOMAIN/$LABEL"
  launchctl kickstart -k "$DOMAIN/$LABEL"
fi

echo "Started: $LABEL"
