#!/usr/bin/env bash
# validate-scripts.sh — Structural validation for zero live plugin script files
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/.." && pwd)"

section "plugin source zero script files (XPLAT-009)"

set_test "speckit-pro: contains zero live shell/command script files"
script_count=$(
  PLUGIN_ROOT="$PLUGIN_ROOT" python3 - <<'PY'
import os
import re
from pathlib import Path

root = Path(os.environ["PLUGIN_ROOT"])
suffixes = {".sh", ".ps1", ".bat", ".cmd"}
count = 0
for path in root.rglob("*"):
    if not path.is_file():
        continue
    if path.suffix.lower() in suffixes:
        count += 1
        continue
    if path.suffix:
        continue
    try:
        first_line = path.open("r", encoding="utf-8").readline(4096)
    except (OSError, UnicodeDecodeError):
        continue
    if re.search(r"^#!.*\b(?:bash|sh|zsh|powershell|pwsh)\b", first_line, re.IGNORECASE):
        count += 1
print(count)
PY
)
if [ "$script_count" = "0" ]; then
  _pass
else
  _fail "expected zero live plugin script files, found $script_count"
fi

section "autopilot JSON contracts"

CONTRACT_FILES=(
  "$PLUGIN_ROOT/skills/speckit-autopilot/contracts/final-reviewability-gate-state.schema.json"
  "$PLUGIN_ROOT/skills/speckit-autopilot/contracts/reslicing-packet.schema.json"
  "$PLUGIN_ROOT/skills/speckit-autopilot/contracts/routing-decision.schema.json"
  "$PLUGIN_ROOT/skills/speckit-autopilot/contracts/o5-parent-manifest.schema.json"
)

for CONTRACT_FILE in "${CONTRACT_FILES[@]}"; do
  contract="${CONTRACT_FILE#$PLUGIN_ROOT/}"

  set_test "${contract}: exists"
  assert_file_exists "$CONTRACT_FILE"

  set_test "${contract}: parses as JSON"
  if python3 -m json.tool "$CONTRACT_FILE" >/dev/null 2>&1; then
    _pass
  else
    _fail "contract JSON parse failed"
  fi
done

section "technical-roadmap-template reviewability vocabulary"

ROADMAP_TEMPLATE="$PLUGIN_ROOT/skills/speckit-coach/templates/technical-roadmap-template.md"

set_test "technical-roadmap-template.md: exists"
assert_file_exists "$ROADMAP_TEMPLATE"

roadmap_content=$(cat "$ROADMAP_TEMPLATE")

set_test "technical-roadmap-template.md: has Reviewability Contract section"
assert_contains "$roadmap_content" "## Reviewability Contract"

set_test "technical-roadmap-template.md: advertises the production-LOC warn threshold"
assert_contains "$roadmap_content" "400 reviewable production LOC"

set_test "technical-roadmap-template.md: advertises the production-LOC block threshold"
assert_contains "$roadmap_content" "800 reviewable production LOC"

set_test "technical-roadmap-template.md: documents surface-count-as-warning rule"
assert_contains "$roadmap_content" "more than one primary surface is also a warning"

set_test "technical-roadmap-template.md: documents the typed exception pragma"
assert_contains "$roadmap_content" "Reviewability-Exception: <class>"

set_test "technical-roadmap-template.md: names the refactor exception class"
assert_contains "$roadmap_content" "refactor"

set_test "technical-roadmap-template.md: names the infra exception class"
assert_contains "$roadmap_content" "infra"

set_test "technical-roadmap-template.md: names the upgrade exception class"
assert_contains "$roadmap_content" "upgrade"

set_test "technical-roadmap-template.md: no concrete 'refactor' exception pragma"
assert_not_contains "$roadmap_content" "Reviewability-Exception: refactor"

set_test "technical-roadmap-template.md: no concrete 'infra' exception pragma"
assert_not_contains "$roadmap_content" "Reviewability-Exception: infra"

set_test "technical-roadmap-template.md: no concrete 'upgrade' exception pragma"
assert_not_contains "$roadmap_content" "Reviewability-Exception: upgrade"

section "spec templates generated-exception safety"

SPEC_TEMPLATES=(
  "$REPO_ROOT/.specify/presets/speckit-pro-reviewability/templates/spec-template.md"
  "$REPO_ROOT/.specify/templates/spec-template.md"
)

for SPEC_TEMPLATE in "${SPEC_TEMPLATES[@]}"; do
  template_name="${SPEC_TEMPLATE#$REPO_ROOT/}"

  set_test "${template_name}: exists"
  assert_file_exists "$SPEC_TEMPLATE"

  if [ ! -f "$SPEC_TEMPLATE" ]; then
    continue
  fi

  template_content=$(cat "$SPEC_TEMPLATE")

  set_test "${template_name}: names accepted exception classes"
  assert_contains "$template_content" "refactor, infra, and upgrade"

  set_test "${template_name}: explains invalid generated/template provenance"
  assert_contains "$template_content" "generated templates"

  set_test "${template_name}: no concrete refactor exception pragma"
  assert_not_contains "$template_content" "Reviewability-Exception: refactor"

  set_test "${template_name}: no concrete infra exception pragma"
  assert_not_contains "$template_content" "Reviewability-Exception: infra"

  set_test "${template_name}: no concrete upgrade exception pragma"
  assert_not_contains "$template_content" "Reviewability-Exception: upgrade"
done

section "reviewability-preset plan-template declared-files format"

PRESET_PLAN_TEMPLATE="$REPO_ROOT/.specify/presets/speckit-pro-reviewability/templates/plan-template.md"

set_test "reviewability-preset plan-template.md: exists"
assert_file_exists "$PRESET_PLAN_TEMPLATE"

if [ -f "$PRESET_PLAN_TEMPLATE" ]; then
  preset_plan_content=$(cat "$PRESET_PLAN_TEMPLATE")

  set_test "reviewability-preset plan-template.md: has Declared File Operations section"
  assert_contains "$preset_plan_content" "## Declared File Operations"

  set_test "reviewability-preset plan-template.md: teaches the '- NEW' list-marker format the parser requires"
  assert_contains "$preset_plan_content" "- NEW "

  set_test "reviewability-preset plan-template.md: teaches the '- MODIFIED' list-marker format the parser requires"
  assert_contains "$preset_plan_content" "- MODIFIED "
fi

test_summary
