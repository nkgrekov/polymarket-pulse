#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
QUEUE_SCRIPT="$ROOT_DIR/scripts/growth/build_social_queue.py"
DRAFTS_SCRIPT="$ROOT_DIR/scripts/growth/generate_social_drafts.py"
QUEUE_OUTPUT="$ROOT_DIR/docs/social_queue_latest.md"
DRAFTS_OUTPUT="$ROOT_DIR/docs/social_drafts_latest.md"

if [[ -z "${PG_CONN:-}" ]]; then
  if [[ -f "$ROOT_DIR/bot/.env" ]]; then
    set -a
    source "$ROOT_DIR/bot/.env"
    set +a
  fi
fi

if [[ -z "${PG_CONN:-}" ]]; then
  echo "PG_CONN is required. Export it or add it to $ROOT_DIR/bot/.env" >&2
  exit 1
fi

PYTHON_BIN=""
for candidate in \
  "$ROOT_DIR/bot/.venv/bin/python" \
  "$ROOT_DIR/api/.venv/bin/python" \
  "$(command -v python3 2>/dev/null || true)"
do
  if [[ -n "$candidate" && -x "$candidate" ]]; then
    PYTHON_BIN="$candidate"
    break
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  echo "No usable python interpreter found." >&2
  exit 1
fi

MAX_AGE_MINUTES="${MAX_AGE_MINUTES:-30}"
MIN_LIQUIDITY="${MIN_LIQUIDITY:-5000}"
MIN_DELTA="${MIN_DELTA:-0.02}"

echo "Building fresh social queue..."
"$PYTHON_BIN" "$QUEUE_SCRIPT" \
  --max-age-minutes "$MAX_AGE_MINUTES" \
  --min-liquidity "$MIN_LIQUIDITY"

echo "Building fresh social drafts..."
"$PYTHON_BIN" "$DRAFTS_SCRIPT" \
  --langs en \
  --channels x,threads \
  --movers 5 \
  --alerts 3 \
  --max-age-minutes "$MAX_AGE_MINUTES" \
  --min-liquidity "$MIN_LIQUIDITY"

if grep -q "No fresh/liquid movers passed the current gate." "$QUEUE_OUTPUT"; then
  DECISION="SKIP"
else
  DECISION="POST"
fi

echo
echo "Decision: $DECISION"
echo "Queue: $QUEUE_OUTPUT"
echo "Drafts: $DRAFTS_OUTPUT"
echo

if [[ "$DECISION" == "POST" ]]; then
  sed -n '1,80p' "$QUEUE_OUTPUT"
else
  sed -n '1,40p' "$QUEUE_OUTPUT"
  echo "Regenerate later when the live window is fresher or more liquid."
fi
