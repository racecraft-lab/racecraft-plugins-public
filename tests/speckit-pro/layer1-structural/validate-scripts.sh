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
  "$PLUGIN_ROOT/skills/speckit-autopilot/scripts/estimate-reviewable-loc.sh"
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

# FR-007: the estimator's per-file LOC constant and the gate's per-task ×40
# multiplier are deliberately NOT a shared variable (same magnitude, different
# unit; the estimator value is tunable). The drift guard is the repo's
# comment-only keep-in-sync convention — assert the marker is present in BOTH
# scripts. This is comment-presence only, never numeric value-equality.
section "reviewability LOC keep-in-sync markers (FR-007)"

ESTIMATOR_SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/estimate-reviewable-loc.sh"
GATE_SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/reviewability-gate.sh"

set_test "estimate-reviewable-loc.sh: has KEEP IN SYNC marker"
assert_contains "$(cat "$ESTIMATOR_SCRIPT")" "KEEP IN SYNC"

set_test "reviewability-gate.sh: has KEEP IN SYNC marker"
assert_contains "$(cat "$GATE_SCRIPT")" "KEEP IN SYNC"

# SC-007/FR-014: the roadmap template must advertise the same vocabulary the
# reviewability gate honors, so setup-mode parsing never false-fails on a
# template↔gate mismatch. Assert the contract heading and the honored phrasing.
section "technical-roadmap-template reviewability vocabulary (SC-007, FR-014)"

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

# PR #119 review (PRRT_kwDORvqw086HoVpr): the template must keep the exception
# pragma as the NON-matching `<class>` placeholder. A concrete class line
# (`Reviewability-Exception: refactor` etc.) in the template would be honored by
# the live setup-mode matcher if a roadmap is derived from it — so assert the
# template contains NO concrete honored pragma, only the placeholder.
set_test "technical-roadmap-template.md: no concrete 'refactor' exception pragma (placeholder only)"
assert_not_contains "$roadmap_content" "Reviewability-Exception: refactor"

set_test "technical-roadmap-template.md: no concrete 'infra' exception pragma (placeholder only)"
assert_not_contains "$roadmap_content" "Reviewability-Exception: infra"

set_test "technical-roadmap-template.md: no concrete 'upgrade' exception pragma (placeholder only)"
assert_not_contains "$roadmap_content" "Reviewability-Exception: upgrade"

# FR-001/US1: the reviewability-preset plan-template's `## Declared File Operations`
# stub is the sole author-facing source of the block the estimator parses. It MUST
# demonstrate the `- ` list-marker format the parser requires
# (estimate-reviewable-loc.sh ENTRY_RE: `^[[:space:]]*[-*][[:space:]]+(NEW|MODIFIED)...`).
# A stub that shows a bare `NEW path` (no leading `- `) teaches a format the parser
# silently drops → every wired plan run degrades to `not_estimated`, making the
# preventive budget a no-op through its own delivery vehicle. Guard against that.
section "reviewability-preset plan-template declared-files format (FR-001/US1)"

PRESET_PLAN_TEMPLATE="$(cd "$PLUGIN_ROOT/.." && pwd)/.specify/presets/speckit-pro-reviewability/templates/plan-template.md"

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
