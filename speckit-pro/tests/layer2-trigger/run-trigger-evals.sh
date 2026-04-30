#!/usr/bin/env bash
# run-trigger-evals.sh — Run Claude Layer 2 trigger evals via skill-creator
#
# Usage: run-trigger-evals.sh [skill-name]
#   skill-name: any Claude skill with a matching
#               tests/layer2-trigger/evals/<skill>-trigger.json
#
# Requires: skill-creator plugin installed at $SKILL_CREATOR_ROOT or default path
# Output:   JSON results to stdout, summary to stderr
#
# For Codex-specific trigger evals, use run-trigger-evals-codex.sh instead.

set -euo pipefail

SKILL_CREATOR="${SKILL_CREATOR_ROOT:-$HOME/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator}"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKILL="${1:-speckit-coach}"

# Detect whether the test skill collides with an installed speckit-pro plugin
# skill. The eval works by writing a test command file at .claude/commands/
# `<skill>-skill-<uuid>.md`; if the same `<skill>` name is also exposed as
# `speckit-pro:<skill>` from the installed plugin, the matcher prefers the
# installed plugin skill and the test variant never fires (all true-positive
# triggers report 0/3). The historical fix was to wrap `claude` with `--bare`,
# which disables plugin loading. But `--bare` requires `ANTHROPIC_API_KEY`
# (OAuth + keychain are explicitly disabled in --bare mode), so it auth-fails
# on developer machines that authenticate via Claude Max / claude.ai.
#
# The fix: only enable --bare when there is a real installed-plugin name
# collision. For new skills (like `grill-me` before v1.10.0), no installed
# skill conflicts, so --bare is unnecessary and just blocks auth. Set
# `EVAL_FORCE_BARE=1` to opt back into --bare regardless of collision.
INSTALLED_PLUGIN_DIR="$HOME/.claude/plugins/marketplaces/racecraft-plugins-public/speckit-pro/skills/${SKILL}"
NEED_BARE="${EVAL_FORCE_BARE:-}"
if [ -z "$NEED_BARE" ] && [ -d "$INSTALLED_PLUGIN_DIR" ]; then
  NEED_BARE="1"
fi

WRAPPER_DIR=$(mktemp -d)
trap 'rm -rf "$WRAPPER_DIR"' EXIT
if [ "$NEED_BARE" = "1" ]; then
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
  echo "Using --bare mode (installed plugin skill '${SKILL}' detected)" >&2
else
  echo "Skipping --bare mode (no installed plugin skill collision for '${SKILL}')" >&2
fi

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
  echo "ERROR: Skill not found for requested skill '$SKILL'." >&2
  echo "Searched locations:" >&2
  echo "  - $PLUGIN_ROOT/skills/${SKILL}" >&2
  echo "  - $PLUGIN_ROOT/codex-skills/${SKILL}" >&2
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
