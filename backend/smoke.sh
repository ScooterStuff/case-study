#!/usr/bin/env bash
# Smoke test: the three canonical spec queries through the streaming /chat API.
# Usage: BASE=http://localhost:8000 bash backend/smoke.sh
set -euo pipefail
BASE="${BASE:-http://localhost:8000}"
SESSION="smoke-$RANDOM"
HERE="$(cd "$(dirname "$0")" && pwd)"

if ! curl -sf "$BASE/health" > /dev/null; then
  echo "Backend not reachable at $BASE - start it first (make dev)" >&2
  exit 1
fi
echo "health: $(curl -sf "$BASE/health")"

ask() {
  echo
  echo "================================================================"
  echo ">>> $1"
  echo "----------------------------------------------------------------"
  PAYLOAD=$(python3 -c 'import json,sys; print(json.dumps({"session_id": sys.argv[1], "message": sys.argv[2]}))' "$SESSION" "$1")
  curl -sN "$BASE/chat" -H 'Content-Type: application/json' -d "$PAYLOAD" \
    | python3 "$HERE/_sse_pretty.py"
}

# The three canonical spec queries. Query 2 deliberately follows query 1 in the
# SAME session - it must resolve "this part" from the conversation history.
ask "How can I install part number PS11752778?"
ask "Is this part compatible with my WDT780SAEM1 model?"
ask "The ice maker on my Whirlpool fridge is not working. How can I fix it?"
