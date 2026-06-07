#!/usr/bin/env bash
# validate-scripts.sh — Structural validation for autopilot bash scripts
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"

SCRIPT_FILES=(
  "$PLUGIN_ROOT/skills/speckit-autopilot/scripts/check-prerequisites.sh"
  "$PLUGIN_ROOT/skills/speckit-autopilot/scripts/validate-gate.sh"
  "$PLUGIN_ROOT/skills/speckit-autopilot/scripts/confidence-gate.sh"
  "$PLUGIN_ROOT/skills/speckit-autopilot/scripts/resolve-confidence-mode.sh"
  "$PLUGIN_ROOT/skills/speckit-autopilot/scripts/detect-commands.sh"
  "$PLUGIN_ROOT/skills/speckit-autopilot/scripts/detect-presets.sh"
  "$PLUGIN_ROOT/skills/speckit-autopilot/scripts/reviewability-gate.sh"
  "$PLUGIN_ROOT/skills/speckit-autopilot/scripts/generate-pr-body.sh"
  "$PLUGIN_ROOT/skills/speckit-coach/scripts/ensure-reviewability-preset.sh"
  "$PLUGIN_ROOT/skills/speckit-coach/scripts/estimate-spec-size.sh"
  "$PLUGIN_ROOT/skills/speckit-coach/scripts/project-fixup.sh"
  "$PLUGIN_ROOT/scripts/install-curated-set.sh"
)

for SCRIPT_FILE in "${SCRIPT_FILES[@]}"; do
  script="${SCRIPT_FILE#$PLUGIN_ROOT/skills/}"

  section "$script"

  set_test "${script}: file exists"
  assert_file_exists "$SCRIPT_FILE"

  if [ ! -f "$SCRIPT_FILE" ]; then
    continue
  fi

  first_line=$(head -n1 "$SCRIPT_FILE")

  set_test "${script}: has shebang line"
  assert_match "$first_line" '^#!/' "first line must be a shebang"

  set_test "${script}: passes bash -n syntax check"
  if bash -n "$SCRIPT_FILE" 2>/dev/null; then
    _pass
  else
    _fail "bash -n syntax check failed"
  fi

  content=$(cat "$SCRIPT_FILE")

  set_test "${script}: has set -euo pipefail"
  assert_contains "$content" "set -euo pipefail"

  set_test "${script}: has executable permission"
  assert_file_executable "$SCRIPT_FILE"
done

test_summary
