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
# US2 hard-atomic override + releasability assertions (T018, FR-007/FR-007a/
# FR-008/FR-009/FR-011b; SC-003/SC-004; quickstart 3, 4, 5, 6). Authored to FAIL
# against the US1-only spine: before T019-T022 the hard-atomic-* fixtures route by
# US1 rules (modify-heavy/abstain → one-navigable-PR, or additive-multi-seam →
# split-PR) and carry no hard-atomic:*/releasability:* token, so every
# `single-atomic-PR` / token / releasable:false assertion below is a real VALUE
# mismatch, not a parse/file-not-found error.
#
# The two CI-green warning strings MUST be byte-identical to data-model.md Entity 3
# (including the "≠" character). Membership is checked against the `signals`/
# `warnings` arrays SPECIFICALLY via array_of (defined in the US1 section).
# ---------------------------------------------------------------------------

WARN_DESTRUCTIVE="destructive migration: a passing CI run does not prove this change is releasable (CI-green ≠ releasable)"
WARN_CONCURRENCY="concurrency-sensitive change: a passing CI run does not prove this change is releasable (CI-green ≠ releasable)"

section "US2: hard-atomic override → single-atomic-PR over seams (FR-007, SC-003; quickstart 3)"

# Each hard-atomic-* fixture carries APPARENT seams; the override MUST win → single-atomic-PR
# AND emit exactly its matching hard-atomic:* token in signals[].

# hard-atomic-rename is authored as a PROVEN additive multi-seam change (CREATE TABLE
# on a schema/migration surface + a UI panel, zero modify keywords) so US1 ALONE
# would route it split-PR. The override must therefore beat an ACTIVE split signal —
# this is the SC-003 "even when seams are present" property and the precedence guard
# from the design notes (the US1 split branch must NOT re-set the route after the
# override). The suppression assertion below fails if the dispatch is ever refactored
# from the if/elif chain into a separate preceding if-block.
set_test "hard-atomic-rename routes single-atomic-PR (override beats an ACTIVE split signal, SC-003)"
output=$("$SCRIPT" "$FIXTURE_ROOT/hard-atomic-rename")
assert_json_field "$output" "route" "single-atomic-PR" "exported-symbol rename → single-atomic-PR over split"

set_test "hard-atomic-rename emits hard-atomic:exported-symbol-rename in signals[]"
signals=$(array_of "$output" "signals")
assert_contains "$signals" "'hard-atomic:exported-symbol-rename'" "rename token in signals[]"

set_test "hard-atomic-rename SUPPRESSES the split branch (no change-shape:additive-multi-seam, FR-007/SC-003)"
assert_not_contains "$signals" "change-shape:additive-multi-seam" "override must suppress, not co-exist with, the split signal"

set_test "hard-atomic-version-pin routes single-atomic-PR (override beats seams)"
output=$("$SCRIPT" "$FIXTURE_ROOT/hard-atomic-version-pin")
assert_json_field "$output" "route" "single-atomic-PR" "global version pin → single-atomic-PR"

set_test "hard-atomic-version-pin emits hard-atomic:global-version-pin in signals[]"
signals=$(array_of "$output" "signals")
assert_contains "$signals" "'hard-atomic:global-version-pin'" "version-pin token in signals[]"

set_test "hard-atomic-mutual-exclusion routes single-atomic-PR (override beats seams)"
output=$("$SCRIPT" "$FIXTURE_ROOT/hard-atomic-mutual-exclusion")
assert_json_field "$output" "route" "single-atomic-PR" "mutual-exclusion primitive → single-atomic-PR"

set_test "hard-atomic-mutual-exclusion emits hard-atomic:mutual-exclusion-primitive in signals[]"
signals=$(array_of "$output" "signals")
assert_contains "$signals" "'hard-atomic:mutual-exclusion-primitive'" "mutual-exclusion token in signals[]"

set_test "hard-atomic-out-of-tree-contract routes single-atomic-PR (override beats seams)"
output=$("$SCRIPT" "$FIXTURE_ROOT/hard-atomic-out-of-tree-contract")
assert_json_field "$output" "route" "single-atomic-PR" "out-of-tree contract break → single-atomic-PR"

set_test "hard-atomic-out-of-tree-contract emits hard-atomic:out-of-tree-contract-break in signals[]"
signals=$(array_of "$output" "signals")
assert_contains "$signals" "'hard-atomic:out-of-tree-contract-break'" "out-of-tree token in signals[]"

set_test "hard-atomic-destructive-migration routes single-atomic-PR (override beats seams)"
output=$("$SCRIPT" "$FIXTURE_ROOT/hard-atomic-destructive-migration")
assert_json_field "$output" "route" "single-atomic-PR" "destructive migration → single-atomic-PR"

set_test "hard-atomic-destructive-migration emits hard-atomic:destructive-migration in signals[]"
signals=$(array_of "$output" "signals")
assert_contains "$signals" "'hard-atomic:destructive-migration'" "destructive-migration hard-atomic token in signals[]"

section "US2: releasability is orthogonal to route (FR-008, FR-009, SC-004; quickstart 4, 5, 6)"

# Destructive migration: single-atomic-PR AND releasable:false with the exact CI-green sentence.
set_test "destructive-migration is releasable:false"
output=$("$SCRIPT" "$FIXTURE_ROOT/hard-atomic-destructive-migration")
assert_json_field "$output" "releasable" "False" "destructive migration is not releasable"

set_test "destructive-migration emits releasability:destructive-migration in signals[]"
signals=$(array_of "$output" "signals")
assert_contains "$signals" "'releasability:destructive-migration'" "destructive-migration releasability token in signals[]"

set_test "destructive-migration carries the destructive-migration CI-green sentence in warnings[]"
warnings=$(array_of "$output" "warnings")
assert_contains "$warnings" "$WARN_DESTRUCTIVE" "exact destructive-migration warning string in warnings[]"

# Concurrency: releasable:false with the exact CI-green sentence (route per other detectors).
set_test "concurrency is releasable:false"
output=$("$SCRIPT" "$FIXTURE_ROOT/concurrency")
assert_json_field "$output" "releasable" "False" "concurrency change is not releasable"

set_test "concurrency emits releasability:concurrency in signals[]"
signals=$(array_of "$output" "signals")
assert_contains "$signals" "'releasability:concurrency'" "concurrency releasability token in signals[]"

set_test "concurrency carries the concurrency CI-green sentence in warnings[]"
warnings=$(array_of "$output" "warnings")
assert_contains "$warnings" "$WARN_CONCURRENCY" "exact concurrency warning string in warnings[]"

set_test "concurrency never routes branch-by-abstraction (reserved, SC-008)"
route=$(field_of "$output" "route")
assert_not_contains "$route" "branch-by-abstraction" "reserved enum is never emitted"

# A hard-atomic fixture with NO releasability risk: releasable:true, empty warnings (FR-009).
set_test "hard-atomic-rename is releasable with no CI-green warning (FR-009)"
output=$("$SCRIPT" "$FIXTURE_ROOT/hard-atomic-rename")
assert_json_field "$output" "releasable" "True" "rename carries no releasability risk"
assert_json_field "$output" "warnings" "[]" "rename has no CI-green warning"

set_test "hard-atomic-rename emits no releasability:* token in signals[] (FR-009)"
signals=$(array_of "$output" "signals")
assert_not_contains "$signals" "releasability:" "no spurious releasability token on a non-risk change"

# ---------------------------------------------------------------------------
# Cross-cutting / dogfood assertions are added by later tasks (T023, T024)
# against the error path and PRSG-007's own feature dir.
# ---------------------------------------------------------------------------

test_summary
