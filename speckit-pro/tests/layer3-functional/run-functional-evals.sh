#!/usr/bin/env bash
# run-functional-evals.sh — Run Claude Layer 3 functional evals
#
# Usage: run-functional-evals.sh [skill-name]
#   skill-name: any Claude skill with a matching
#               tests/layer3-functional/evals/<skill>-evals.json
#
# Functional evals test whether the skill produces correct, complete responses
# when invoked with realistic prompts. Unlike trigger evals (Layer 2), these
# verify output quality against expected behaviors.
#
# How to run:
#   These evals are designed for use with skill-creator's evaluation framework.
#   Each eval has a prompt, expected_output summary, and specific expectations
#   that the response must satisfy.
#
#   Manual run (via Claude):
#     1. Load the skill: /speckit-coach or /speckit-autopilot
#     2. Send each eval prompt from the evals JSON
#     3. Verify the response matches the expectations list
#
#   Automated run (via skill-creator, when supported):
#     cd $SKILL_CREATOR_ROOT
#     python3 -m scripts.run_eval \
#       --eval-set <eval-file> \
#       --skill-path <skill-path> \
#       --mode functional
#
# Requires: skill-creator plugin installed at $SKILL_CREATOR_ROOT or default path
#
# For Codex-specific functional evals, use run-functional-evals-codex.sh instead.

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKILL="${1:-speckit-coach}"

EVAL_FILE="$PLUGIN_ROOT/tests/layer3-functional/evals/${SKILL}-evals.json"
if [ -d "$PLUGIN_ROOT/skills/${SKILL}" ]; then
  SKILL_PATH="$PLUGIN_ROOT/skills/${SKILL}"
elif [ -d "$PLUGIN_ROOT/codex-skills/${SKILL}" ]; then
  SKILL_PATH="$PLUGIN_ROOT/codex-skills/${SKILL}"
else
  SKILL_PATH=""
fi

if [ ! -f "$EVAL_FILE" ]; then
  echo "ERROR: Eval file not found: $EVAL_FILE" >&2
  echo "Available evals:" >&2
  ls "$PLUGIN_ROOT/tests/layer3-functional/evals/"*.json 2>/dev/null | while read -r f; do
    basename "$f" -evals.json
  done >&2
  exit 1
fi

if [ -z "$SKILL_PATH" ] || [ ! -d "$SKILL_PATH" ]; then
  echo "ERROR: Skill not found for requested skill '$SKILL'." >&2
  echo "Searched locations:" >&2
  echo "  - $PLUGIN_ROOT/skills/${SKILL}" >&2
  echo "  - $PLUGIN_ROOT/codex-skills/${SKILL}" >&2
  exit 1
fi

# Display eval summary
EVAL_COUNT=$(python3 -c "
import json, sys
data = json.load(open('$EVAL_FILE'))
evals = data.get('evals', [])
print(len(evals))
" 2>/dev/null || echo "?")

echo "Layer 3 Functional Evals: $SKILL"
echo "================================"
echo "Eval file:  $EVAL_FILE"
echo "Skill path: $SKILL_PATH"
echo "Eval count: $EVAL_COUNT"
echo ""
echo "To run manually:"
echo "  1. Start a session that can load the target skill"
echo "  2. Invoke /$SKILL or explicitly load \$$SKILL"
echo "  3. Send each prompt from the evals JSON"
echo "  4. Verify responses match the expectations"
echo ""
echo "Eval prompts:"
echo ""

python3 -c "
import json, sys
data = json.load(open('$EVAL_FILE'))
for e in data.get('evals', []):
    print(f\"  [{e['id']}] {e['prompt'][:100]}...\")
    for exp in e.get('expectations', []):
        print(f\"      - {exp[:80]}\")
    print()
"
