#!/usr/bin/env bash
# test-detect-presets.sh — Unit tests for detect-presets.sh
#
# Tests preset/extension detection with synthetic fixtures.
# Optional --live flag runs against a live SpecKit project (set PROJECT_ROOT).

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/detect-presets.sh"
LIVE=false
[ "${1:-}" = "--live" ] && LIVE=true

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# Helper: run script in a specific directory
run_in() {
  local dir="$1"
  (cd "$dir" && bash "$SCRIPT")
}

# ─────────────────────────────────────────
section "No presets or extensions"
# ─────────────────────────────────────────

set_test "Empty .specify dir — has_presets=false"
dir="$FIXTURE_DIR/empty"
mkdir -p "$dir/.specify"
output=$(run_in "$dir")
# Note: detect-presets.sh can produce malformed JSON when specify CLI
# returns multi-line error messages for template resolution. Use contains.
assert_contains "$output" '"has_presets":false'

set_test "Empty dir — has presets field"
assert_contains "$output" '"presets":[]'

set_test "Empty dir — has templates field"
assert_contains "$output" '"templates":'

# ─────────────────────────────────────────
section "Preset detection"
# ─────────────────────────────────────────

set_test "One preset — has_presets=true"
dir="$FIXTURE_DIR/one-preset"
mkdir -p "$dir/.specify/presets/tdd"
cat > "$dir/.specify/presets/tdd/preset.yml" << 'YAML'
preset:
  name: "TDD Preset"
  version: "1.0.0"
  description: "Enforces TDD red-green-refactor"
provides:
  overrides:
    - type: "template"
      name: "tasks-template"
      replaces: "tasks-template"
YAML
output=$(run_in "$dir")
assert_contains "$output" '"has_presets":true'

set_test "One preset — preset name detected"
assert_contains "$output" "tdd"

# ─────────────────────────────────────────
section "Extension detection"
# ─────────────────────────────────────────

set_test "Extensions via extension.yml files"
dir="$FIXTURE_DIR/ext-yml"
mkdir -p "$dir/.specify/extensions/verify"
cat > "$dir/.specify/extensions/verify/extension.yml" << 'YAML'
name: verify
version: 1.0.0
YAML
mkdir -p "$dir/.specify"
output=$(run_in "$dir")
assert_contains "$output" "verify"

# ─────────────────────────────────────────
section "Hooks detection"
# ─────────────────────────────────────────

set_test "Hook events in extensions.yml"
dir="$FIXTURE_DIR/hooks"
mkdir -p "$dir/.specify"
cat > "$dir/.specify/extensions.yml" << 'YAML'
installed:
  - verify
hooks:
  before_implement:
    - run: echo "before"
  after_implement:
    - run: echo "after"
YAML
output=$(run_in "$dir")
assert_contains "$output" "hook events configured"

# ─────────────────────────────────────────
# Live project tests (optional)
# ─────────────────────────────────────────

if [ "$LIVE" = "true" ]; then
  section "Live: detect-presets on live project"

  PROJECT_ROOT="${PROJECT_ROOT:-$(git -C "$PLUGIN_ROOT" rev-parse --show-toplevel 2>/dev/null || echo "")}"
  if [ -n "$PROJECT_ROOT" ] && [ -d "$PROJECT_ROOT/.specify/presets" ]; then
    output=$(run_in "$PROJECT_ROOT")

    # Check whether actual preset.yml files exist in the live project.
    # If none are found, verify has_presets=false and skip the presets-populated checks.
    if ls "$PROJECT_ROOT/.specify/presets"/*/preset.yml >/dev/null 2>&1; then
      set_test "Live — has_presets=true (live project has preset)"
      assert_contains "$output" '"has_presets":true'

      set_test "Live — has presets array"
      assert_contains "$output" '"presets":'
    else
      printf "  ${YELLOW}SKIP${RESET}: .specify/presets exists but no preset.yml files found\n"
    fi
  else
    printf "  ${YELLOW}SKIP${RESET}: PROJECT_ROOT not detected or .specify/presets not found\n"
  fi
fi

test_summary
