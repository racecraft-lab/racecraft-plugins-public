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
# US1 / US2 / cross-cutting / dogfood assertions are added by later tasks
# (T010, T018, T023, T024) against the semantic per-class fixtures.
# FIXTURE_ROOT is resolved above so those tasks have a stable anchor.
# ---------------------------------------------------------------------------

test_summary
