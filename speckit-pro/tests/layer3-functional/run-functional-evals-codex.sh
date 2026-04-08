#!/usr/bin/env bash
# run-functional-evals-codex.sh — Manual Layer 3 functional eval helper for Codex
#
# Usage: run-functional-evals-codex.sh [skill-name]
#   skill-name: any Codex skill with a matching
#               tests/layer3-functional/codex-evals/<skill>-evals.json
#               or shared tests/layer3-functional/evals/<skill>-evals.json
#
# The existing skill-creator functional workflow is Claude-oriented. This
# helper prints the Codex eval set and expectations for manual runs.

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKILL="${1:-speckit-coach}"

if [ -f "$PLUGIN_ROOT/tests/layer3-functional/codex-evals/${SKILL}-evals.json" ]; then
  EVAL_FILE="$PLUGIN_ROOT/tests/layer3-functional/codex-evals/${SKILL}-evals.json"
elif [ -f "$PLUGIN_ROOT/tests/layer3-functional/evals/${SKILL}-evals.json" ]; then
  EVAL_FILE="$PLUGIN_ROOT/tests/layer3-functional/evals/${SKILL}-evals.json"
else
  EVAL_FILE=""
fi

SKILL_PATH="$PLUGIN_ROOT/codex-skills/${SKILL}"

if [ -z "$EVAL_FILE" ]; then
  echo "ERROR: Eval file not found for: $SKILL" >&2
  echo "Available Codex functional evals:" >&2
  find "$PLUGIN_ROOT/tests/layer3-functional/codex-evals" "$PLUGIN_ROOT/tests/layer3-functional/evals" \
    -maxdepth 1 -name '*-evals.json' 2>/dev/null | sort -u | while read -r f; do
    basename "$f" -evals.json
  done >&2
  exit 1
fi

if [ ! -d "$SKILL_PATH" ]; then
  echo "ERROR: Codex skill not found: $SKILL_PATH" >&2
  exit 1
fi

EVAL_COUNT=$(python3 -c "
import json
data = json.load(open('$EVAL_FILE'))
print(len(data.get('evals', [])))
" 2>/dev/null || echo "?")

echo "Layer 3 Codex Functional Evals: $SKILL"
echo "======================================"
echo "Eval file:  $EVAL_FILE"
echo "Skill path: $SKILL_PATH"
echo "Eval count: $EVAL_COUNT"
echo ""
echo "To run manually in Codex:"
echo "  1. Start a Codex session with SpecKit Pro installed"
echo "  2. Invoke /$SKILL, load \$$SKILL, or route through @SpecKit Pro"
echo "  3. Send each prompt from the evals JSON"
echo "  4. Verify the response matches the expectations"
echo ""
echo "Eval prompts:"
echo ""

python3 -c "
import json
data = json.load(open('$EVAL_FILE'))
for e in data.get('evals', []):
    print(f\"  [{e['id']}] {e['prompt'][:100]}...\")
    for exp in e.get('expectations', []):
        print(f\"      - {exp[:80]}\")
    print()
"
