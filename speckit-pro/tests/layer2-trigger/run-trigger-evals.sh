#!/usr/bin/env bash
# run-trigger-evals.sh — Run Layer 2 trigger evals via skill-creator's run_eval.py
#
# Usage: run-trigger-evals.sh [skill-name]
#   skill-name: any skill with a matching tests/layer2-trigger/evals/<skill>-trigger.json
#
# Requires: skill-creator plugin installed at $SKILL_CREATOR_ROOT or default path
# Output:   JSON results to stdout, summary to stderr

set -euo pipefail

SKILL_CREATOR="${SKILL_CREATOR_ROOT:-$HOME/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator}"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKILL="${1:-speckit-coach}"

# Create a wrapper around `claude` that adds --bare to prevent installed
# plugin skills from shadowing the test command file during evaluation.
# Without this, Claude picks the real `speckit-pro:coach` (or autopilot)
# plugin skill instead of the test command, causing all true-positive
# evals to fail.
WRAPPER_DIR=$(mktemp -d)
trap 'rm -rf "$WRAPPER_DIR"' EXIT
cat > "$WRAPPER_DIR/claude" << 'WRAPPER'
#!/usr/bin/env bash
real_claude=""
IFS=: read -ra dirs <<< "$PATH"
for d in "${dirs[@]}"; do
  [[ "$d" == "$(dirname "$0")" ]] && continue
  if [[ -x "$d/claude" ]]; then
    real_claude="$d/claude"
    break
  fi
done
exec "$real_claude" "$@" --bare
WRAPPER
chmod +x "$WRAPPER_DIR/claude"
export PATH="$WRAPPER_DIR:$PATH"

EVAL_FILE="$PLUGIN_ROOT/tests/layer2-trigger/evals/${SKILL}-trigger.json"
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
  ls "$PLUGIN_ROOT/tests/layer2-trigger/evals/"*.json 2>/dev/null | while read -r f; do
    basename "$f" -trigger.json
  done >&2
  exit 1
fi

if [ -z "$SKILL_PATH" ] || [ ! -d "$SKILL_PATH" ]; then
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
