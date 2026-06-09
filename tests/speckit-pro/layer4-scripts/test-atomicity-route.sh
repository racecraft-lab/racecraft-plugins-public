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
# Cross-cutting assertions (T023, FR-011/FR-012/SC-006; quickstart 10, 11).
# These lock behaviors the finished script ALREADY has (the error path from
# T004 and the read-only guarantee from FR-011), so they pass GREEN with no RED
# phase — the point is to GUARD them permanently. Each is authored to be
# non-vacuous: the error-path block asserts a real exit 2 + a parsed top-level
# `error` key + the ABSENCE of `route`, and the read-only block compares a
# byte-level snapshot (file list + sha) of a fixture dir taken before and after
# a successful run, so a script that ever wrote a file would flip it to FAIL.
# ---------------------------------------------------------------------------

section "cross-cutting: error path is exit 2 + {\"error\"} + no route (T023, FR-012; quickstart 11)"

set_test "missing dir error path exits 2"
missing="$SANDBOX/cc-missing-dir"
result=0
output=$("$SCRIPT" "$missing" 2>/dev/null) || result=$?
assert_eq "2" "$result" "unreadable/absent input → exit 2 (never a block)"

set_test "error path emits a parseable top-level error string"
err_val=$(field_of "$output" "error")
assert_not_contains "$err_val" "<<missing>>" "error object carries a top-level error key"
assert_not_contains "$err_val" "<<parse-fail>>" "error object is valid JSON"

set_test "error path carries NO route key (FR-011a)"
has_route=$(printf '%s' "$output" | python3 -c "import sys,json; print('yes' if 'route' in json.load(sys.stdin) else 'no')" 2>/dev/null || echo "parse-fail")
assert_eq "no" "$has_route" "error branch must not include a route key"

section "cross-cutting: read-only — a successful run writes no files (T023, FR-011, SC-006; quickstart 10)"

# Copy a real fixture into the sandbox, snapshot it (sorted relative paths +
# per-file sha), run the classifier successfully against the COPY, then re-snapshot
# and assert byte-for-byte equality. Driving off a copy (not the committed fixture
# tree) keeps the assertion hermetic AND means a stray write would be caught here
# rather than mutating a tracked fixture. find|sort|shasum is portable on macOS+Linux.
snapshot_dir() {
  # print "<relpath> <sha>" for every file under $1, sorted — a deterministic
  # fingerprint of the directory's contents (names + bytes).
  ( cd "$1" && find . -type f | LC_ALL=C sort | while IFS= read -r f; do
      printf '%s %s\n' "$f" "$(shasum "$f" | awk '{print $1}')"
    done )
}

ro_src="$FIXTURE_ROOT/modify-heavy"
ro_copy="$SANDBOX/readonly-modify-heavy"
rm -rf "$ro_copy"
cp -R "$ro_src" "$ro_copy"
before_snap=$(snapshot_dir "$ro_copy")
result=0
output=$("$SCRIPT" "$ro_copy") || result=$?
after_snap=$(snapshot_dir "$ro_copy")

set_test "read-only fixture run still succeeds (exit 0)"
assert_eq "0" "$result" "classifier completes on the copied fixture"

set_test "read-only run leaves the fixture dir byte-identical (no files written)"
assert_eq "$before_snap" "$after_snap" "directory contents (names + sha) unchanged after a successful run"

# ---------------------------------------------------------------------------
# Dogfood self-check (T024, load-bearing per FR-007a; D4, D10; quickstart
# "Dogfood self-check"). Run the FINISHED script against PRSG-007's OWN feature
# dir and assert it does NOT spuriously self-classify off its own definitional
# vocabulary. PRSG-007's artifacts enumerate auth/payment/lock/mutex/rename and
# concurrency keywords as the detectors' vocabulary, and saturate the corpus with
# modify keywords (UPDATE/DELETE/DROP/CHECK) — so the CORRECT real output is
# route=one-navigable-PR (modify-heavy), releasable=true, no releasability token.
# This is encoded against the REAL output (verified by hand); if the firewall
# ever regresses, this is the assertion that catches it. The feature dir is
# resolved ABSOLUTELY from this test file's location (not cwd) so it holds under
# any working directory.
# ---------------------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DOGFOOD_DIR="$REPO_ROOT/specs/prsg-007-atomicity-router"

section "dogfood self-check: PRSG-007 classifies its own artifacts safely (T024, FR-007a)"

set_test "dogfood feature dir exists (sanity — non-vacuous guard target)"
if [ -d "$DOGFOOD_DIR" ]; then _pass; else _fail "expected PRSG-007 feature dir at $DOGFOOD_DIR"; fi

dogfood_out=$("$SCRIPT" "$DOGFOOD_DIR")
dogfood_route=$(field_of "$dogfood_out" "route")
dogfood_signals=$(array_of "$dogfood_out" "signals")

set_test "dogfood (1): route != single-atomic-PR (no spurious hard-atomic self-classify)"
assert_not_contains "$dogfood_route" "single-atomic-PR" "PRSG-007 vocabulary must not trip the hard-atomic override"

set_test "dogfood (2): route is a non-split route (no spurious split off its own vocabulary)"
assert_not_contains "$dogfood_route" "split-PR" "PRSG-007 must not spuriously route split-PR"

set_test "dogfood (3): releasable == true (concurrency probe must not fire on vocabulary)"
assert_json_field "$dogfood_out" "releasable" "True" "implementing a concurrency detector is not a concurrency-sensitive change"

set_test "dogfood (4a): no releasability:concurrency token in signals[]"
assert_not_contains "$dogfood_signals" "releasability:concurrency" "no spurious concurrency releasability token"

set_test "dogfood (4b): no releasability:destructive-migration token in signals[]"
assert_not_contains "$dogfood_signals" "releasability:destructive-migration" "no spurious destructive-migration releasability token"

# ---------------------------------------------------------------------------
# Contract validation (T028, FR-001/FR-011a/SC-001/SC-008; quickstart "Contract
# validation"). Validate EVERY emitted object — all ten success fixtures, the
# error branch, and the dogfood run — against routing-decision.schema.json. The
# validator is python-stdlib ONLY (no jsonschema dependency, matching the suite's
# bash+jq+stdlib norm): it loads the schema, picks the success/error arm by key
# presence, and enforces required keys, key-set equality (additionalProperties:
# false), types, and the route/signals/warnings enum membership the schema
# declares. Membership is asserted POSITIVELY (route ∈ the five enum values), so a
# parse failure or an empty string fails LOUD rather than passing vacuously — and
# `branch-by-abstraction`, while a legal enum member, is separately asserted to be
# absent from every emitted object (SC-008: reserved, never emitted by the MVP).
# ---------------------------------------------------------------------------
SCHEMA="$REPO_ROOT/specs/prsg-007-atomicity-router/contracts/routing-decision.schema.json"

# validate_against_schema <json> — exit 0 if <json> satisfies the success OR error
# arm of the schema AND (for success objects) does NOT carry branch-by-abstraction;
# prints a one-line reason and exits 1 otherwise. Stdlib only. The candidate JSON
# is passed as the SCHEMA_OBJECT env var (not stdin) because the python program
# itself arrives on stdin via the `python3 - <<'PY'` heredoc — they cannot share
# the same stream.
validate_against_schema() {
  SCHEMA_OBJECT="$1" python3 - "$SCHEMA" <<'PY'
import os, sys, json
schema_path = sys.argv[1]
with open(schema_path) as fh:
    schema = json.load(fh)
try:
    obj = json.loads(os.environ["SCHEMA_OBJECT"])
except Exception as e:
    print(f"invalid JSON: {e}"); sys.exit(1)

arms = {a["title"]: a for a in schema["oneOf"]}
success = arms["Success decision"]
error = arms["Error decision"]

def fail(msg):
    print(msg); sys.exit(1)

if "error" in obj:
    arm = error
    if set(obj.keys()) != set(arm["required"]):
        fail(f"error object key-set {sorted(obj)} != required {sorted(arm['required'])}")
    if not isinstance(obj["error"], str):
        fail("error value must be a string")
    sys.exit(0)

# Success arm.
arm = success
if "route" not in obj:
    fail("object has neither 'error' nor 'route'")
# additionalProperties:false → key set must equal the required set exactly.
if set(obj.keys()) != set(arm["required"]):
    fail(f"success object key-set {sorted(obj)} != required {sorted(arm['required'])}")
props = arm["properties"]
route_enum = props["route"]["enum"]
if obj["route"] not in route_enum:
    fail(f"route '{obj['route']}' not in enum {route_enum}")
if not isinstance(obj["releasable"], bool):
    fail("releasable must be boolean")
sig_enum = props["signals"]["items"]["enum"]
for s in obj["signals"]:
    if s not in sig_enum:
        fail(f"signal '{s}' not in controlled vocabulary")
if not isinstance(obj["hints"], list) or not all(isinstance(h, str) for h in obj["hints"]):
    fail("hints must be a string array")
warn_enum = props["warnings"]["items"]["enum"]
for w in obj["warnings"]:
    if w not in warn_enum:
        fail(f"warning '{w}' is not a canonical CI-green sentence")
# SC-008: branch-by-abstraction is reserved and must NEVER be emitted.
if obj["route"] == "branch-by-abstraction":
    fail("route is the reserved branch-by-abstraction (MUST NOT be emitted)")
if "branch-by-abstraction" in obj["signals"]:
    fail("branch-by-abstraction must never appear in signals[]")
sys.exit(0)
PY
}

section "contract: every emitted object validates against routing-decision.schema.json (T028, SC-001/SC-008)"

set_test "schema file exists (non-vacuous guard target)"
assert_file_exists "$SCHEMA"

# All ten per-class fixtures (one per change class) — each success object.
for fixture in \
  additive-multi-seam single-additive-seam modify-heavy out-of-scope-empty \
  hard-atomic-rename hard-atomic-version-pin hard-atomic-mutual-exclusion \
  hard-atomic-out-of-tree-contract hard-atomic-destructive-migration concurrency; do
  set_test "fixture $fixture emits a schema-valid object (no branch-by-abstraction)"
  reason=0
  msg=$(validate_against_schema "$("$SCRIPT" "$FIXTURE_ROOT/$fixture")") || reason=$?
  if [ "$reason" -eq 0 ]; then _pass; else _fail "$fixture: $msg"; fi
done

set_test "error branch emits a schema-valid error object"
reason=0
msg=$(validate_against_schema "$("$SCRIPT" "$SANDBOX/does-not-exist" 2>/dev/null)") || reason=$?
if [ "$reason" -eq 0 ]; then _pass; else _fail "error branch: $msg"; fi

set_test "dogfood run emits a schema-valid object (no branch-by-abstraction)"
reason=0
msg=$(validate_against_schema "$dogfood_out") || reason=$?
if [ "$reason" -eq 0 ]; then _pass; else _fail "dogfood: $msg"; fi

test_summary
