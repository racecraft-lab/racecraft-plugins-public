#!/usr/bin/env bash
# run-trigger-evals.sh — Run Layer 2 trigger evals via skill-creator's run_eval.py
#
# Usage: run-trigger-evals.sh [skill-name]
#   skill-name: speckit-autopilot | speckit-coach (default: speckit-coach)
#
# Requires: skill-creator plugin installed at $SKILL_CREATOR_ROOT or default path
# Output:   JSON results to stdout, summary to stderr

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

echo "Running trigger evals for: $SKILL" >&2
echo "Eval file: $EVAL_FILE" >&2
echo "Skill path: $SKILL_PATH" >&2
echo "" >&2

cd "$SKILL_CREATOR"

python3 -m scripts.run_eval \
  --eval-set "$EVAL_FILE" \
  --skill-path "$SKILL_PATH" \
  --runs-per-query 3 \
  --trigger-threshold 0.5 \
  --verbose
