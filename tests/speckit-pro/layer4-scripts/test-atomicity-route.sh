#!/usr/bin/env bash
# test-atomicity-route.sh — Unit tests for atomicity-route.sh (PRSG-007 Layer-4).
#
# Mirrors test-reviewability-gate.sh conventions: sources lib/assertions.sh, resolves
# the script + fixture root from this file's location, and drives most cases off a
# mktemp sandbox so the assertions do not depend on per-class fixture *content* (which
# later tasks author). The semantic per-class fixtures under
# fixtures/atomicity-route/<class>/ are exercised by the US1/US2 assertions (T010/T018).

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/atomicity-route.sh"
FIXTURE_ROOT="$(cd "$(dirname "$0")/fixtures/atomicity-route" && pwd)"

SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT

# ---------------------------------------------------------------------------
# Foundational (Phase 2) assertions — CLI front door, exit contract, JSON
# emitter shape, and the out-of-scope short-circuit. These are authored to FAIL
# against the T001 sentinel stub (value mismatch) and pass once T004-T006 land.
# ---------------------------------------------------------------------------

section "atomicity-route usage / error path (FR-011a, FR-012)"

set_test "No arguments exits 2"
result=0
output=$("$SCRIPT" 2>/dev/null) || result=$?
assert_eq "2" "$result" "exit code"

set_test "No arguments emits a top-level error object"
assert_contains "$output" '"error"' "error key present on usage error"

set_test "Absent feature dir exits 2"
result=0
output=$("$SCRIPT" "$SANDBOX/does-not-exist" 2>/dev/null) || result=$?
assert_eq "2" "$result" "exit code"

set_test "Absent feature dir emits a top-level error object"
assert_contains "$output" '"error"' "error key present on unreadable input"

set_test "Error object carries no route key (FR-011a)"
has_route=$(printf '%s' "$output" | python3 -c "import sys,json; print('yes' if 'route' in json.load(sys.stdin) else 'no')" 2>/dev/null || echo "parse-fail")
assert_eq "no" "$has_route" "error path must not include route"

section "out-of-scope short-circuit (FR-003, T006)"

set_test "Missing tasks.md routes out-of-scope (exit 0)"
nodir="$SANDBOX/no-tasks"
mkdir -p "$nodir"
result=0
output=$("$SCRIPT" "$nodir") || result=$?
assert_eq "0" "$result" "exit code"
assert_json_field "$output" "route" "out-of-scope" "missing tasks.md → out-of-scope"

set_test "Missing tasks.md is releasable with empty arrays"
assert_json_field "$output" "releasable" "True" "out-of-scope is releasable"
assert_json_field "$output" "signals" "[]" "out-of-scope signals empty"
assert_json_field "$output" "warnings" "[]" "out-of-scope warnings empty"
assert_json_field "$output" "hints" "[]" "out-of-scope hints empty"

set_test "Empty tasks.md routes out-of-scope (exit 0)"
emptydir="$SANDBOX/empty-tasks"
mkdir -p "$emptydir"
: > "$emptydir/tasks.md"
result=0
output=$("$SCRIPT" "$emptydir") || result=$?
assert_eq "0" "$result" "exit code"
assert_json_field "$output" "route" "out-of-scope" "empty tasks.md → out-of-scope"

section "success JSON shape + abstain floor (FR-005, FR-006, FR-011a, T005)"

set_test "Minimal non-empty tasks.md classifies (exit 0)"
absdir="$SANDBOX/abstain"
mkdir -p "$absdir"
cat > "$absdir/tasks.md" <<'EOF'
# Tasks
- [ ] T001 Wire one capability into the existing handler.
EOF
result=0
output=$("$SCRIPT" "$absdir") || result=$?
assert_eq "0" "$result" "exit code"

set_test "Abstain floor is one-navigable-PR (FR-006)"
assert_json_field "$output" "route" "one-navigable-PR" "no decisive signal → abstain"

set_test "Abstain emits no change-shape token (FR-006, FR-011b)"
assert_json_field "$output" "signals" "[]" "abstain signals empty"

set_test "Success object exposes all five contract keys (FR-011a)"
assert_json_field_exists "$output" "route" "route key"
assert_json_field_exists "$output" "releasable" "releasable key"
assert_json_field_exists "$output" "signals" "signals key"
assert_json_field_exists "$output" "hints" "hints key"
assert_json_field_exists "$output" "warnings" "warnings key"

set_test "Success object is releasable with empty warnings (FR-009)"
assert_json_field "$output" "releasable" "True" "abstain is releasable"
assert_json_field "$output" "warnings" "[]" "abstain has no warning"

# ---------------------------------------------------------------------------
# US1 routing assertions (T010, FR-002/FR-004/FR-005/FR-006/FR-011b;
# SC-002/SC-005/SC-008; quickstart 1, 2, 7, 8, 9). Authored to FAIL against the
# pre-detector spine (the spine abstains to one-navigable-PR with empty signals,
# so additive-multi-seam → split-PR and modify-heavy → change-shape:modify-heavy
# are real VALUE mismatches, not parse/file-not-found errors) and to pass once
# T011-T016 land.
#
# Membership is checked against the `signals` array SPECIFICALLY (not the whole
# object) so an advisory hint can never false-pass a signals[] assertion. We
# extract the named array as a python list-repr string and substring-match the
# quoted token, mirroring the foundational tests' assert_contains convention.
# ---------------------------------------------------------------------------

# array_of <json> <field> — print a named top-level array as its python list
# repr (e.g. "['change-shape:modify-heavy']"); empty array prints "[]".
array_of() {
  printf '%s' "$1" | python3 -c "import sys,json; print(json.load(sys.stdin).get('$2', '<<missing>>'))" 2>/dev/null || echo "<<parse-fail>>"
}

# field_of <json> <field> — print a named top-level scalar field.
field_of() {
  printf '%s' "$1" | python3 -c "import sys,json; print(json.load(sys.stdin).get('$2', '<<missing>>'))" 2>/dev/null || echo "<<parse-fail>>"
}

section "US1: additive multi-seam → split-PR (FR-004, SC-002, FR-011b; quickstart 1)"

set_test "additive-multi-seam fixture routes split-PR"
output=$("$SCRIPT" "$FIXTURE_ROOT/additive-multi-seam")
assert_json_field "$output" "route" "split-PR" "proven additive multi-seam → split-PR"

set_test "additive-multi-seam emits change-shape:additive-multi-seam in signals[]"
signals=$(array_of "$output" "signals")
assert_contains "$signals" "'change-shape:additive-multi-seam'" "decisive split token in signals[]"

section "US1: single additive seam → single-PR-style, never split (US1 AS2; quickstart 2)"

set_test "single-additive-seam fixture is single-PR-style"
output=$("$SCRIPT" "$FIXTURE_ROOT/single-additive-seam")
route=$(field_of "$output" "route")
# .route ∈ {one-navigable-PR, single-atomic-PR}
case "$route" in
  one-navigable-PR|single-atomic-PR) _pass ;;
  *) _fail "single additive seam: expected one-navigable-PR or single-atomic-PR, got '$route'" ;;
esac

set_test "single-additive-seam never routes split-PR"
assert_not_contains "$route" "split-PR" "one indivisible seam must not split"

section "US1: modify-heavy → one-navigable-PR, never branch-by-abstraction (SC-008; quickstart 8)"

set_test "modify-heavy fixture routes one-navigable-PR"
output=$("$SCRIPT" "$FIXTURE_ROOT/modify-heavy")
assert_json_field "$output" "route" "one-navigable-PR" "modify-heavy non-hard-atomic → one-navigable-PR"

set_test "modify-heavy emits change-shape:modify-heavy in signals[]"
signals=$(array_of "$output" "signals")
assert_contains "$signals" "'change-shape:modify-heavy'" "decisive modify token in signals[]"

set_test "modify-heavy never routes branch-by-abstraction (reserved, SC-008)"
route=$(field_of "$output" "route")
assert_not_contains "$route" "branch-by-abstraction" "reserved enum is never emitted"

set_test "modify-heavy is releasable with no warning (FR-009, SC-008)"
assert_json_field "$output" "releasable" "True" "modify-heavy is releasable"
assert_json_field "$output" "warnings" "[]" "modify-heavy carries no CI-green warning"

section "US1: out-of-scope empty fixture → out-of-scope (FR-003; quickstart 9)"

set_test "out-of-scope-empty fixture routes out-of-scope"
output=$("$SCRIPT" "$FIXTURE_ROOT/out-of-scope-empty")
assert_json_field "$output" "route" "out-of-scope" "empty/absent tasks.md → out-of-scope"

section "US1: advisory probes emit into hints[] only, never signals[] (T015, FR-010/FR-011b)"

# Regression lock for the three advisory probes (flag-system/release-cadence/
# consumer-locality). Driven off a sandbox tasks.md (not a per-class fixture) so
# it stays isolated from the routing fixtures. Asserts the probe→hints[] path
# works AND the FR-011b invariant signals[] ∩ hints[] == ∅ holds.
hintdir="$SANDBOX/flag-hint"
mkdir -p "$hintdir"
cat > "$hintdir/tasks.md" <<'EOF'
# Tasks
- [ ] T001 Gate the new path behind a feature flag in the existing handler.
EOF
output=$("$SCRIPT" "$hintdir")

set_test "flag-system signal surfaces as an advisory hint"
hints=$(array_of "$output" "hints")
assert_contains "$hints" "flag-system" "flag keyword → hints[]"

set_test "advisory probe output never leaks into signals[] (FR-011b disjointness)"
signals=$(array_of "$output" "signals")
assert_not_contains "$signals" "flag-system" "advisory hint must not appear in signals[]"

# ---------------------------------------------------------------------------
# US2 / cross-cutting / dogfood assertions are added by later tasks
# (T018, T023, T024) against the semantic per-class fixtures.
# ---------------------------------------------------------------------------

test_summary
