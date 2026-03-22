#!/usr/bin/env bash
# run-trigger-loop.sh — Run Layer 2 trigger eval+improve loop via skill-creator
#
# Usage: run-trigger-loop.sh [skill-name]
#   skill-name: speckit-autopilot | speckit-coach (default: speckit-coach)
#
# Iteratively runs trigger evals and improves the skill description until
# all queries pass or --max-iterations is reached. Uses a 40% holdout split
# to prevent overfitting.
#
# Requires: skill-creator plugin installed at $SKILL_CREATOR_ROOT or default path
# Output:   HTML report opened in browser on completion

set -euo pipefail

SKILL_CREATOR="${SKILL_CREATOR_ROOT:-$HOME/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator}"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKILL="${1:-speckit-coach}"

EVAL_FILE="$PLUGIN_ROOT/tests/layer2-trigger/evals/${SKILL}-trigger.json"
SKILL_PATH="$PLUGIN_ROOT/skills/${SKILL}"

if [ ! -f "$EVAL_FILE" ]; then
  echo "ERROR: Eval file not found: $EVAL_FILE" >&2
  echo "Available evals:" >&2
  ls "$PLUGIN_ROOT/tests/layer2-trigger/evals/"*.json 2>/dev/null | while read -r f; do
    basename "$f" -trigger.json
  done >&2
  exit 1
fi

if [ ! -d "$SKILL_PATH" ]; then
  echo "ERROR: Skill not found: $SKILL_PATH" >&2
  exit 1
fi

if [ ! -d "$SKILL_CREATOR" ]; then
  echo "ERROR: skill-creator not found at: $SKILL_CREATOR" >&2
  echo "Set SKILL_CREATOR_ROOT to the skill-creator skill directory." >&2
  exit 1
fi

echo "Running trigger eval+improve loop for: $SKILL" >&2
echo "Eval file: $EVAL_FILE" >&2
echo "Skill path: $SKILL_PATH" >&2
echo "Max iterations: 5, Holdout: 0.4" >&2
echo "" >&2

cd "$SKILL_CREATOR"

python3 -m scripts.run_loop \
  --eval-set "$EVAL_FILE" \
  --skill-path "$SKILL_PATH" \
  --max-iterations 5 \
  --holdout 0.4 \
  --runs-per-query 3 \
  --trigger-threshold 0.5 \
  --verbose
