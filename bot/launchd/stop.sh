#!/usr/bin/env bash
set -euo pipefail

LABEL="com.nikitagrekov.polymarket-pulse-bot"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/${LABEL}.plist"
echo "Stopped: $LABEL"
