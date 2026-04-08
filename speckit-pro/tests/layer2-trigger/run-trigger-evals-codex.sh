#!/usr/bin/env bash
# run-trigger-evals-codex.sh — Manual Layer 2 trigger eval helper for Codex
#
# Usage: run-trigger-evals-codex.sh [skill-name]
#   skill-name: any Codex skill with a matching
#               tests/layer2-trigger/codex-evals/<skill>-trigger.json
#               or shared tests/layer2-trigger/evals/<skill>-trigger.json
#
# The automated skill-creator trigger workflow is Claude-specific. This helper
# prints the Codex eval set and the expected trigger decisions for manual runs.

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKILL="${1:-speckit-coach}"

if [ -f "$PLUGIN_ROOT/tests/layer2-trigger/codex-evals/${SKILL}-trigger.json" ]; then
  EVAL_FILE="$PLUGIN_ROOT/tests/layer2-trigger/codex-evals/${SKILL}-trigger.json"
elif [ -f "$PLUGIN_ROOT/tests/layer2-trigger/evals/${SKILL}-trigger.json" ]; then
  EVAL_FILE="$PLUGIN_ROOT/tests/layer2-trigger/evals/${SKILL}-trigger.json"
else
  EVAL_FILE=""
fi

SKILL_PATH="$PLUGIN_ROOT/codex-skills/${SKILL}"

if [ -z "$EVAL_FILE" ]; then
  echo "ERROR: Eval file not found for: $SKILL" >&2
  echo "Available Codex trigger evals:" >&2
  find "$PLUGIN_ROOT/tests/layer2-trigger/codex-evals" "$PLUGIN_ROOT/tests/layer2-trigger/evals" \
    -maxdepth 1 -name '*-trigger.json' 2>/dev/null | sort -u | while read -r f; do
    basename "$f" -trigger.json
  done >&2
  exit 1
fi

if [ ! -d "$SKILL_PATH" ]; then
  echo "ERROR: Codex skill not found: $SKILL_PATH" >&2
  exit 1
fi

QUERY_COUNT=$(python3 -c "
import json
data = json.load(open('$EVAL_FILE'))
print(len(data))
" 2>/dev/null || echo "?")

echo "Layer 2 Codex Trigger Evals: $SKILL"
echo "==================================="
echo "Eval file:  $EVAL_FILE"
echo "Skill path: $SKILL_PATH"
echo "Query count: $QUERY_COUNT"
echo ""
echo "To run manually in Codex:"
echo "  1. Start a Codex session with SpecKit Pro installed"
echo "  2. Send each query exactly as written without explicitly invoking the skill"
echo "  3. Verify Codex routes to the expected bundled skill"
echo ""
echo "Trigger queries:"
echo ""

python3 -c "
import json
data = json.load(open('$EVAL_FILE'))
for i, item in enumerate(data, 1):
    expected = 'TRIGGER' if item['should_trigger'] else 'NO TRIGGER'
    print(f\"  [{i}] {expected}: {item['query']}\")
    print()
"
