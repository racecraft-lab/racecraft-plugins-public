#!/usr/bin/env bash
# test-validate-gate.sh — Unit tests for validate-gate.sh
#
# Tests all 7 gates (pass/fail), missing files, marker counting,
# invalid gate, and no-args scenarios using synthetic fixtures.
# Optional --live flag runs against real completed spec.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/validate-gate.sh"
LIVE=false
[ "${1:-}" = "--live" ] && LIVE=true

# Temp fixture dir with cleanup
FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# Helper: create spec fixtures
make_spec() {
  local dir="$FIXTURE_DIR/$1"
  mkdir -p "$dir"
  echo "$dir"
}

# ─────────────────────────────────────────
section "Gate: No arguments / Invalid"
# ─────────────────────────────────────────

set_test "No arguments → exit 2"
result=0
output=$("$SCRIPT" 2>/dev/null) || result=$?
assert_eq "2" "$result" "exit code"

set_test "Invalid gate G8 → exit 2"
dir=$(make_spec "invalid")
result=0
output=$("$SCRIPT" G8 "$dir" 2>/dev/null) || result=$?
assert_eq "2" "$result" "exit code"

set_test "Invalid gate output contains error"
assert_contains "$output" "Unknown gate"

# ─────────────────────────────────────────
section "G1: Specify complete"
# ─────────────────────────────────────────

set_test "G1 pass — spec.md exists, no markers"
dir=$(make_spec "g1-pass")
printf '# Spec\nAll requirements defined.\n' > "$dir/spec.md"
result=0
output=$("$SCRIPT" G1 "$dir") || result=$?
assert_eq "0" "$result" "exit code"

set_test "G1 pass — JSON gate field"
assert_json_field "$output" "gate" "G1"

set_test "G1 pass — JSON pass field"
assert_json_field "$output" "pass" "True"

set_test "G1 fail — spec.md missing"
dir=$(make_spec "g1-nospec")
result=0
output=$("$SCRIPT" G1 "$dir") || result=$?
assert_eq "1" "$result" "exit code"

set_test "G1 fail — spec.md has markers"
dir=$(make_spec "g1-markers")
printf '# Spec\n[NEEDS CLARIFICATION] What about auth?\n[NEEDS CLARIFICATION] What about rate limits?\n[NEEDS CLARIFICATION] Unclear scope.\n' > "$dir/spec.md"
result=0
output=$("$SCRIPT" G1 "$dir") || result=$?
assert_eq "1" "$result" "exit code"

set_test "G1 fail — marker count is 3"
# Note: validate-gate.sh produces JSON with unescaped newlines in details
# field when markers exist, so we grep for the markers field instead
assert_contains "$output" '"markers":3'

# ─────────────────────────────────────────
section "G2: Clarify complete"
# ─────────────────────────────────────────

set_test "G2 pass — no markers"
dir=$(make_spec "g2-pass")
printf '# Spec\nClarified.\n' > "$dir/spec.md"
result=0
output=$("$SCRIPT" G2 "$dir") || result=$?
assert_eq "0" "$result" "exit code"

set_test "G2 fail — 2 markers"
dir=$(make_spec "g2-fail")
printf '# Spec\n[NEEDS CLARIFICATION] A\n[NEEDS CLARIFICATION] B\n' > "$dir/spec.md"
result=0
output=$("$SCRIPT" G2 "$dir") || result=$?
assert_eq "1" "$result" "exit code"

set_test "G2 fail — markers=2"
assert_contains "$output" '"markers":2'

# ─────────────────────────────────────────
section "G3: Plan complete"
# ─────────────────────────────────────────

set_test "G3 pass — plan.md no markers"
dir=$(make_spec "g3-pass")
printf '# Plan\nAll decided.\n' > "$dir/plan.md"
result=0
output=$("$SCRIPT" G3 "$dir") || result=$?
assert_eq "0" "$result" "exit code"

set_test "G3 fail — plan.md missing"
dir=$(make_spec "g3-noplan")
result=0
output=$("$SCRIPT" G3 "$dir") || result=$?
assert_eq "1" "$result" "exit code"

set_test "G3 fail — plan has TODO"
dir=$(make_spec "g3-todo")
printf '# Plan\nTODO: decide on approach\n' > "$dir/plan.md"
result=0
output=$("$SCRIPT" G3 "$dir") || result=$?
assert_eq "1" "$result" "exit code"

# ─────────────────────────────────────────
section "G4: Checklist complete"
# ─────────────────────────────────────────

set_test "G4 pass — no [Gap] markers"
dir=$(make_spec "g4-pass")
printf '# Spec\nClean.\n' > "$dir/spec.md"
printf '# Plan\nClean.\n' > "$dir/plan.md"
result=0
output=$("$SCRIPT" G4 "$dir") || result=$?
assert_eq "0" "$result" "exit code"

set_test "G4 fail — gaps in both files"
dir=$(make_spec "g4-fail")
printf '# Spec\n[Gap] Missing error handling.\n' > "$dir/spec.md"
printf '# Plan\n[Gap] Missing auth.\n[Gap] Missing logging.\n' > "$dir/plan.md"
result=0
output=$("$SCRIPT" G4 "$dir") || result=$?
assert_eq "1" "$result" "exit code"

set_test "G4 fail — markers=3"
assert_json_field "$output" "markers" "3"

# ─────────────────────────────────────────
section "G5: Tasks exist"
# ─────────────────────────────────────────

set_test "G5 pass — tasks.md has task entries"
dir=$(make_spec "g5-pass")
printf '# Tasks\n- [ ] T001 Create schemas\n- [ ] T002 Implement logic\n- [ ] T003 Write tests\n' > "$dir/tasks.md"
result=0
output=$("$SCRIPT" G5 "$dir") || result=$?
assert_eq "0" "$result" "exit code"

set_test "G5 pass — task_count=3"
assert_json_field "$output" "task_count" "3"

set_test "G5 fail — tasks.md missing"
dir=$(make_spec "g5-notasks")
result=0
output=$("$SCRIPT" G5 "$dir") || result=$?
assert_eq "1" "$result" "exit code"

set_test "G5 fail — tasks.md no entries"
dir=$(make_spec "g5-empty")
printf '# Tasks\nNo tasks yet.\n' > "$dir/tasks.md"
result=0
output=$("$SCRIPT" G5 "$dir") || result=$?
assert_eq "1" "$result" "exit code"

# ─────────────────────────────────────────
section "G6: Analyze complete"
# ─────────────────────────────────────────

set_test "G6 pass — no CRITICAL/HIGH"
dir=$(make_spec "g6-pass")
printf '# Spec\nClean.\n' > "$dir/spec.md"
printf '# Plan\nClean.\n' > "$dir/plan.md"
printf '# Tasks\nClean.\n' > "$dir/tasks.md"
result=0
output=$("$SCRIPT" G6 "$dir") || result=$?
assert_eq "0" "$result" "exit code"

set_test "G6 fail — CRITICAL in spec"
dir=$(make_spec "g6-fail")
printf '# Spec\n[CRITICAL] Missing validation.\n' > "$dir/spec.md"
printf '# Plan\n[HIGH] Needs review.\n' > "$dir/plan.md"
printf '# Tasks\nOk.\n' > "$dir/tasks.md"
result=0
output=$("$SCRIPT" G6 "$dir") || result=$?
assert_eq "1" "$result" "exit code"

# ─────────────────────────────────────────
section "G7: Implement complete"
# ─────────────────────────────────────────

set_test "G7 pass — all tasks [x]"
dir=$(make_spec "g7-pass")
printf '# Tasks\n- [x] T001 Done\n- [x] T002 Done\n- [x] T003 Done\n' > "$dir/tasks.md"
result=0
output=$("$SCRIPT" G7 "$dir") || result=$?
assert_eq "0" "$result" "exit code"

set_test "G7 pass — total=3 done=3"
assert_json_field "$output" "total" "3"

set_test "G7 fail — 2 of 4 incomplete"
dir=$(make_spec "g7-fail")
printf '# Tasks\n- [x] T001 Done\n- [x] T002 Done\n- [ ] T003 Pending\n- [ ] T004 Pending\n' > "$dir/tasks.md"
result=0
output=$("$SCRIPT" G7 "$dir") || result=$?
assert_eq "1" "$result" "exit code"

set_test "G7 fail — remaining=2"
assert_json_field "$output" "done" "2"

# ─────────────────────────────────────────
# Live project tests (optional)
# ─────────────────────────────────────────

if [ "$LIVE" = "true" ]; then
  section "Live: validate-gate against completed specs"

  # Find a completed spec with all tasks marked [x]
  PROJECT_ROOT="${PROJECT_ROOT:-$(git -C "$PLUGIN_ROOT" rev-parse --show-toplevel 2>/dev/null || echo "")}"
  if [ -n "$PROJECT_ROOT" ] && [ -d "$PROJECT_ROOT/specs/008-perspectives" ]; then
    SPEC_DIR="$PROJECT_ROOT/specs/008-perspectives"

    set_test "Live G1 on completed spec → pass"
    if [ -f "$SPEC_DIR/spec.md" ]; then
      result=0
      "$SCRIPT" G1 "$SPEC_DIR" >/dev/null 2>&1 || result=$?
      assert_eq "0" "$result" "G1 should pass on completed spec"
    else
      _fail "spec.md not found at $SPEC_DIR"
    fi
  else
    printf "  ${YELLOW}SKIP${RESET}: PROJECT_ROOT not detected or specs/008-perspectives not found\n"
  fi
fi

test_summary
