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
#
# Optional environment variables:
#   EVAL_FORCE_BARE=1
#     Force --bare mode (disables ALL plugins; requires ANTHROPIC_API_KEY).
#
#   EVAL_DISABLE_PLUGINS="plugin1@market,plugin2@market"
#     Comma-separated list of plugins to disable for this eval run via
#     --settings. Use this to suppress competing skills whose descriptions
#     outrank the skill under test (e.g., superpowers' brainstorming skill
#     beats grill-me on natural-language pre-spec scoping prompts). Unlike
#     --bare, this keeps OAuth / keychain auth working.
#
# Per-skill defaults are baked in for known plugin competitors (see
# DISABLE_PLUGINS_DEFAULT block below).

set -euo pipefail

SKILL_CREATOR="${SKILL_CREATOR_ROOT:-$HOME/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator}"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKILL="${1:-speckit-coach}"

# ── Installed-plugin collision detection ────────────────────────────────────
# The eval works by writing a test command file at
# `.claude/commands/<skill>-skill-<uuid>.md`. If the user also has speckit-pro
# installed as a plugin (typical case for plugin authors), Claude sees both:
# the test variant AND `speckit-pro:<skill>`. Because they share the same
# description verbatim, the plugin variant routinely wins the selector and
# every true-positive query scores 0/3.
#
# We solve this by detecting which marketplace publishes speckit-pro from
# ~/.claude/settings.json (the marketplace name can vary per user — e.g.,
# `racecraft-public-plugins`, `racecraft-plugins-public`, etc.) and adding
# `speckit-pro@<marketplace>` to the --settings disable list. This works
# with OAuth/keychain auth, unlike `--bare` which requires ANTHROPIC_API_KEY.
INSTALLED_MARKETPLACE=""
if command -v jq >/dev/null 2>&1 && [ -f "$HOME/.claude/settings.json" ]; then
  INSTALLED_MARKETPLACE=$(
    jq -r '
      (.enabledPlugins // {})
      | to_entries[]
      | select(.key | startswith("speckit-pro@"))
      | .key | sub("^speckit-pro@"; "")
    ' "$HOME/.claude/settings.json" 2>/dev/null | head -1
  )
fi

# Per-skill defaults for plugin competitors. Overridable via EVAL_DISABLE_PLUGINS.
# - grill-me: outranked by superpowers:brainstorming on natural-language SDD
#   pre-spec scoping prompts. Disabling superpowers reflects the standalone
#   production install and measures grill-me on its own merits.
# - All speckit-pro skills collide with their installed counterpart when the
#   plugin is enabled; auto-add `speckit-pro@<detected-marketplace>` so the
#   test variant has no rival.
DISABLE_PLUGINS_DEFAULT=""
case "$SKILL" in
  grill-me)
    DISABLE_PLUGINS_DEFAULT="superpowers@claude-plugins-official"
    ;;
esac
if [ -n "$INSTALLED_MARKETPLACE" ]; then
  INSTALLED_PLUGIN_DIR="$HOME/.claude/plugins/marketplaces/${INSTALLED_MARKETPLACE}/speckit-pro/skills/${SKILL}"
  if [ -d "$INSTALLED_PLUGIN_DIR" ]; then
    if [ -n "$DISABLE_PLUGINS_DEFAULT" ]; then
      DISABLE_PLUGINS_DEFAULT="${DISABLE_PLUGINS_DEFAULT},speckit-pro@${INSTALLED_MARKETPLACE}"
    else
      DISABLE_PLUGINS_DEFAULT="speckit-pro@${INSTALLED_MARKETPLACE}"
    fi
  fi
fi
DISABLE_PLUGINS="${EVAL_DISABLE_PLUGINS:-$DISABLE_PLUGINS_DEFAULT}"

# `--bare` is the strongest isolation (disables ALL plugins) but requires
# ANTHROPIC_API_KEY (OAuth + keychain are disabled in --bare mode), so it
# auth-fails on developer machines authenticated via Claude Max / claude.ai.
# By default we prefer --settings (works with OAuth). Set EVAL_FORCE_BARE=1
# to opt back into --bare regardless of collision state.
INSTALLED_PLUGIN_DIR="${INSTALLED_PLUGIN_DIR:-}"
NEED_BARE="${EVAL_FORCE_BARE:-}"

WRAPPER_DIR=$(mktemp -d)
SETTINGS_FILE=""
trap 'rm -rf "$WRAPPER_DIR"; [ -n "$SETTINGS_FILE" ] && rm -f "$SETTINGS_FILE"' EXIT

# Build optional --settings JSON if EVAL_DISABLE_PLUGINS is set.
WRAPPER_EXTRA_ARGS=""
if [ -n "$DISABLE_PLUGINS" ]; then
  SETTINGS_FILE=$(mktemp -t eval-disable-plugins-XXXXXX.json)
  DISABLE_PLUGINS="$DISABLE_PLUGINS" python3 -c '
import json, os, sys
plugins_csv = os.environ["DISABLE_PLUGINS"]
disabled = {p.strip(): False for p in plugins_csv.split(",") if p.strip()}
print(json.dumps({"enabledPlugins": disabled}))
' > "$SETTINGS_FILE"
  WRAPPER_EXTRA_ARGS="--settings $SETTINGS_FILE"
  echo "Disabling competing plugins for eval: $DISABLE_PLUGINS" >&2
fi

if [ "$NEED_BARE" = "1" ] || [ -n "$WRAPPER_EXTRA_ARGS" ]; then
  # Wrapper script: prepend WRAPPER_EXTRA_ARGS, optionally append --bare.
  WRAPPER_BARE_FLAG=""
  if [ "$NEED_BARE" = "1" ]; then
    WRAPPER_BARE_FLAG="--bare"
    echo "Using --bare mode (installed plugin skill '${SKILL}' detected)" >&2
  else
    echo "Skipping --bare mode (no installed plugin skill collision for '${SKILL}')" >&2
  fi
  cat > "$WRAPPER_DIR/claude" << WRAPPER
#!/usr/bin/env bash
real_claude=""
IFS=: read -ra dirs <<< "\$PATH"
for d in "\${dirs[@]}"; do
  [[ "\$d" == "\$(dirname "\$0")" ]] && continue
  if [[ -x "\$d/claude" ]]; then
    real_claude="\$d/claude"
    break
  fi
done
exec "\$real_claude" $WRAPPER_EXTRA_ARGS "\$@" $WRAPPER_BARE_FLAG
WRAPPER
  chmod +x "$WRAPPER_DIR/claude"
  export PATH="$WRAPPER_DIR:$PATH"
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

# When plugins are disabled via --settings, force sequential execution.
# The skill-creator harness defaults to ProcessPoolExecutor(max_workers=10),
# and parallel claude --settings invocations are racy: roughly half the
# workers fail to apply the enabledPlugins override, so the disabled plugin
# (e.g. superpowers:brainstorming) outranks the skill under test on those
# runs and the skill never fires. Sequential execution is the only reliable
# fix; without it, this wrapper regresses to ~10/20 on grill-me.
EXTRA_RUN_ARGS=""
if [ -n "$DISABLE_PLUGINS" ]; then
  EXTRA_RUN_ARGS="--num-workers 1"
  echo "Forcing --num-workers 1 (parallelism + --settings is racy)" >&2
fi

python3 -m scripts.run_eval \
  --eval-set "$EVAL_FILE" \
  --skill-path "$SKILL_PATH" \
  --runs-per-query 3 \
  --trigger-threshold 0.5 \
  --verbose \
  $EXTRA_RUN_ARGS
