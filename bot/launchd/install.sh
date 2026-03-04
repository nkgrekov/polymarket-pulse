#!/usr/bin/env bash
set -euo pipefail

LABEL="com.nikitagrekov.polymarket-pulse-bot"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_SRC="$SRC_DIR/${LABEL}.plist"
PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"

mkdir -p "$HOME/Library/LaunchAgents"

if [[ ! -f "$PLIST_SRC" ]]; then
  echo "Missing plist: $PLIST_SRC" >&2
  exit 1
fi

cp "$PLIST_SRC" "$PLIST_DST"

if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  launchctl bootout "gui/$(id -u)" "$PLIST_DST" || true
fi

launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/$LABEL"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

echo "Installed and started: $LABEL"
echo "plist: $PLIST_DST"
