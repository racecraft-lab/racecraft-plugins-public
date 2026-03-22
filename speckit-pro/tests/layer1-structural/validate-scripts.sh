#!/usr/bin/env bash
# validate-scripts.sh — Structural validation for autopilot bash scripts
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

SCRIPTS_DIR="$PLUGIN_ROOT/skills/speckit-autopilot/scripts"
SCRIPTS=(check-prerequisites.sh validate-gate.sh detect-commands.sh detect-presets.sh)

for script in "${SCRIPTS[@]}"; do
  SCRIPT_FILE="$SCRIPTS_DIR/$script"

  section "scripts/${script}"

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
