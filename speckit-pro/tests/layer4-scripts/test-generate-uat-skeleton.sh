#!/usr/bin/env bash
# test-generate-uat-skeleton.sh — Unit tests for the deterministic UAT runbook generator (FR-015).

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT_UNDER_TEST="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh"
FIXTURES_DIR="$(cd "$(dirname "$0")" && pwd)/fixtures"
FULL_SPEC="$FIXTURES_DIR/spec-full-snapshot.md"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# ---------------------------------------------------------------------------
# US1 — full-spec snapshot renders a complete runbook (FR-001, FR-010, SC-001)
# ---------------------------------------------------------------------------
section "US1 — full-spec snapshot"

us1_out="$FIXTURE_DIR/us1-runbook.md"
us1_rc=0
us1_stdout=$("$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$us1_out" 2>/dev/null) || us1_rc=$?

set_test "Script exits 0 on the full-spec snapshot"
assert_eq "0" "$us1_rc" "exit code"

set_test "Runbook file is written"
assert_file_exists "$us1_out"

us1_body=$(cat "$us1_out" 2>/dev/null || true)

set_test "Per-story block count matches grep -c story count (SC-001)"
expected_stories=$(grep -c '^### User Story [0-9]' "$FULL_SPEC")
actual_stories=$(grep -c '^<a id="us-' "$us1_out" 2>/dev/null || echo 0)
assert_eq "$expected_stories" "$actual_stories" "per-story anchor count"

set_test "All eight FR-010 section headers present"
assert_contains "$us1_body" "# UAT Runbook:"
assert_contains "$us1_body" "## Env Setup"
assert_contains "$us1_body" "## Per-Story Acceptance Tests"
assert_contains "$us1_body" "## FR Coverage Matrix"
assert_contains "$us1_body" "## Negative-Path Tests"
assert_contains "$us1_body" "## Self-Review Findings"
assert_contains "$us1_body" "## Sign-off"
assert_contains "$us1_body" "## Rollback"

set_test "Eight section headers appear in FR-010 fixed order"
order=$(grep -nE '^(# UAT Runbook:|## (Env Setup|Per-Story Acceptance Tests|FR Coverage Matrix|Negative-Path Tests|Self-Review Findings|Sign-off|Rollback))' "$us1_out" | cut -d: -f1 | paste -sd, -)
sorted=$(printf '%s' "$order" | tr ',' '\n' | sort -n | paste -sd, -)
assert_eq "$sorted" "$order" "section order is monotonic"

set_test "FR Coverage Matrix links to a deterministic per-story anchor"
assert_contains "$us1_body" "(#us-1)"

set_test "Header carries the static PR placeholder (FR-011)"
assert_contains "$us1_body" "<set on PR open>"

# ---------------------------------------------------------------------------
# US3 — deterministic overwrite, no merge (FR-007)
# ---------------------------------------------------------------------------
section "US3 — deterministic overwrite"

us3_a="$FIXTURE_DIR/us3-run-a.md"
us3_b="$FIXTURE_DIR/us3-run-b.md"
"$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$us3_a" >/dev/null 2>&1
"$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$us3_b" >/dev/null 2>&1

set_test "Two runs against an unchanged spec are byte-identical (FR-007)"
diff_rc=0
diff "$us3_a" "$us3_b" >/dev/null 2>&1 || diff_rc=$?
assert_eq "0" "$diff_rc" "diff of two runs"

set_test "Re-run overwrites a hand-edited runbook (no merge/append/skip)"
printf '\nUAT_HANDEDIT_SENTINEL_SHOULD_BE_GONE\n' >> "$us3_a"
"$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$us3_a" >/dev/null 2>&1
us3_after=$(cat "$us3_a")
assert_not_contains "$us3_after" "UAT_HANDEDIT_SENTINEL_SHOULD_BE_GONE"

# ---------------------------------------------------------------------------
# US4 — Self-Review echo via --workflow-file (FR-009)
# ---------------------------------------------------------------------------
section "US4 — Self-Review echo"

wf_file="$FIXTURE_DIR/workflow-with-selfreview.md"
cat > "$wf_file" <<'EOF'
# Workflow

## Self-Review

UAT_SELFREVIEW_ECHOED_LINE: checked all the boxes.

## Next Section

Should not be echoed.
EOF

us4_out="$FIXTURE_DIR/us4-runbook.md"
us4_rc=0
"$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$us4_out" --workflow-file "$wf_file" >/dev/null 2>&1 || us4_rc=$?

set_test "Script exits 0 with --workflow-file supplied"
assert_eq "0" "$us4_rc" "exit code"

us4_body=$(cat "$us4_out" 2>/dev/null || true)

set_test "Self-Review Findings echoes the extracted block"
assert_contains "$us4_body" "UAT_SELFREVIEW_ECHOED_LINE"

set_test "Self-Review echo stops at the next H2 (boundary)"
assert_not_contains "$us4_body" "Should not be echoed."

# Flag absent → graceful stub, exit 0.
us4_stub_out="$FIXTURE_DIR/us4-stub-runbook.md"
us4_stub_rc=0
"$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$us4_stub_out" >/dev/null 2>&1 || us4_stub_rc=$?

set_test "Script exits 0 with no --workflow-file"
assert_eq "0" "$us4_stub_rc" "exit code"

set_test "Self-Review section emits the stub line when flag absent"
assert_contains "$(cat "$us4_stub_out")" "<not available — workflow file not provided>"

# Flag present but file lacks ## Self-Review → stub, exit 0.
wf_noheading="$FIXTURE_DIR/workflow-no-selfreview.md"
printf '# Workflow\n\n## Other\n\nNothing relevant.\n' > "$wf_noheading"
us4_nh_out="$FIXTURE_DIR/us4-nh-runbook.md"
us4_nh_rc=0
"$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$us4_nh_out" --workflow-file "$wf_noheading" >/dev/null 2>&1 || us4_nh_rc=$?

set_test "Script exits 0 when workflow file lacks a Self-Review heading"
assert_eq "0" "$us4_nh_rc" "exit code"

set_test "Self-Review section emits the stub line when heading missing"
assert_contains "$(cat "$us4_nh_out")" "<not available — workflow file not provided>"

# ---------------------------------------------------------------------------
# US2 — zero-stories spec → FR/SC fallback keying (FR-003, SC-002)
# ---------------------------------------------------------------------------
section "US2 — zero-stories fallback"

zero_spec="$FIXTURE_DIR/zero-stories-spec.md"
cat > "$zero_spec" <<'EOF'
# Feature Specification: Infra Only

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST apply branch protection to main.
- **FR-002**: The system MUST enforce squash-only merges.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A failing required check blocks merge 100% of the time.
EOF

zero_out="$FIXTURE_DIR/zero-runbook.md"
zero_rc=0
"$SCRIPT_UNDER_TEST" "$zero_spec" "$zero_out" >/dev/null 2>&1 || zero_rc=$?

set_test "Zero-stories spec still exits 0 (never skipped)"
assert_eq "0" "$zero_rc" "exit code"

zero_body=$(cat "$zero_out" 2>/dev/null || true)

set_test "Zero-stories runbook carries the FR/SC fallback header note"
assert_contains "$zero_body" "no user stories"

set_test "Zero-stories runbook contains an FR-keyed test section"
assert_contains "$zero_body" "FR-001"

set_test "Zero-stories runbook contains an SC-keyed test section"
assert_contains "$zero_body" "SC-001"

# ---------------------------------------------------------------------------
# Cross-cutting: UAT_PROJECT_COMMANDS Env Setup formatter (FR-008)
# ---------------------------------------------------------------------------
section "FR-008 — Env Setup formatter"

env_out="$FIXTURE_DIR/env-runbook.md"

set_test "Unset UAT_PROJECT_COMMANDS emits the unknown placeholder"
( unset UAT_PROJECT_COMMANDS; "$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$env_out" >/dev/null 2>&1 )
assert_contains "$(cat "$env_out")" "<unknown — autopilot did not pass PROJECT_COMMANDS>"

set_test "Malformed JSON degrades to the unknown placeholder (fail-soft)"
UAT_PROJECT_COMMANDS='{not valid json' "$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$env_out" >/dev/null 2>&1
assert_contains "$(cat "$env_out")" "<unknown — autopilot did not pass PROJECT_COMMANDS>"

set_test "Malformed JSON still exits 0 (does not abort)"
env_malformed_rc=0
UAT_PROJECT_COMMANDS='{not valid json' "$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$env_out" >/dev/null 2>&1 || env_malformed_rc=$?
assert_eq "0" "$env_malformed_rc" "exit code"

set_test "A populated key renders its command value"
UAT_PROJECT_COMMANDS='{"BUILD":"make build","UNIT_TEST":"make test"}' "$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$env_out" >/dev/null 2>&1
assert_contains "$(cat "$env_out")" "make build"

set_test "A key with literal N/A renders as unavailable, distinct from unset"
# detect-commands.sh always emits the full 7-key object; N/A is its undetected sentinel.
env_full_json='{"BUILD":"make build","TYPECHECK":"make check","LINT":"N/A","LINT_FIX":"make fix","UNIT_TEST":"make test","INTEGRATION_TEST":"make itest","SINGLE_FILE_INTEGRATION":"make itest-one"}'
UAT_PROJECT_COMMANDS="$env_full_json" "$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$env_out" >/dev/null 2>&1
env_body=$(cat "$env_out")
assert_contains "$env_body" "not available for this project"
set_test "N/A path does not emit the unset placeholder (full 7-key object)"
assert_not_contains "$env_body" "<unknown — autopilot did not pass PROJECT_COMMANDS>"

# ---------------------------------------------------------------------------
# Cross-cutting: Rollback section (FR-012)
# ---------------------------------------------------------------------------
section "FR-012 — Rollback"

# (a) spec carries a ## Rollback heading → extract it.
rb_dir="$FIXTURE_DIR/rb-spec"
mkdir -p "$rb_dir"
cat > "$rb_dir/spec.md" <<'EOF'
# Feature Specification: Rollback Demo

### Functional Requirements

- **FR-001**: System MUST do a thing.

## Rollback

UAT_ROLLBACK_FROM_SPEC: run the documented teardown.
EOF
rb_out="$FIXTURE_DIR/rb-runbook.md"
"$SCRIPT_UNDER_TEST" "$rb_dir/spec.md" "$rb_out" >/dev/null 2>&1

set_test "Rollback section extracts the spec's ## Rollback block"
assert_contains "$(cat "$rb_out")" "UAT_ROLLBACK_FROM_SPEC"

# (b) plan.md carries ## Rollback, spec does not → fall back to plan.
rb_dir2="$FIXTURE_DIR/rb-plan"
mkdir -p "$rb_dir2"
cat > "$rb_dir2/spec.md" <<'EOF'
# Feature Specification: Plan Rollback Demo

### Functional Requirements

- **FR-001**: System MUST do a thing.
EOF
cat > "$rb_dir2/plan.md" <<'EOF'
# Plan

## Rollback

UAT_ROLLBACK_FROM_PLAN: revert the migration first.
EOF
rb_out2="$FIXTURE_DIR/rb-runbook2.md"
"$SCRIPT_UNDER_TEST" "$rb_dir2/spec.md" "$rb_out2" >/dev/null 2>&1

set_test "Rollback falls back to plan.md when spec lacks the heading"
assert_contains "$(cat "$rb_out2")" "UAT_ROLLBACK_FROM_PLAN"

# (c) neither spec nor plan has ## Rollback → synthesized stanza.
set_test "Rollback synthesizes a stanza when neither spec nor plan has the heading"
synth_body=$(cat "$env_out")  # env_out was generated from FULL_SPEC, which has no ## Rollback
assert_contains "$synth_body" "git revert <SHA>"

# ---------------------------------------------------------------------------
# Cross-cutting: clarification-marker propagation (FR-005, Decision 3)
# ---------------------------------------------------------------------------
section "FR-005 — clarification markers"

clar_spec="$FIXTURE_DIR/clarification-spec.md"
cat > "$clar_spec" <<'EOF'
# Feature Specification: Clarify Demo

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST do a clear thing.
- **FR-002**: System MUST handle the bare case [NEEDS CLARIFICATION] before shipping.
- **FR-003**: System MUST pick a default [NEEDS CLARIFICATION: which timeout value?].

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The clear thing happens 100% of the time.
EOF

clar_out="$FIXTURE_DIR/clarification-runbook.md"
clar_rc=0
"$SCRIPT_UNDER_TEST" "$clar_spec" "$clar_out" >/dev/null 2>&1 || clar_rc=$?

set_test "Clarification-marker spec still exits 0"
assert_eq "0" "$clar_rc" "exit code"

clar_body=$(cat "$clar_out" 2>/dev/null || true)

set_test "Bare NEEDS CLARIFICATION bullet is reproduced (not dropped)"
assert_contains "$clar_body" "handle the bare case"

set_test "Colon-question NEEDS CLARIFICATION bullet is reproduced (not dropped)"
assert_contains "$clar_body" "which timeout value?"

set_test "Marked bullets carry an unresolved-clarification annotation"
clar_warn_count=$(grep -c 'unresolved clarification' "$clar_out" || true)
assert_eq "2" "$clar_warn_count" "annotation count (one per marked bullet)"

set_test "Clean bullet is not annotated"
clean_line=$(grep 'do a clear thing' "$clar_out" || true)
assert_not_contains "$clean_line" "unresolved clarification"

# ---------------------------------------------------------------------------
# Cross-cutting: duplicate IDs + exit codes + silent stdout (FR-004, FR-006)
# ---------------------------------------------------------------------------
section "FR-004/FR-006 — duplicate IDs, exit codes, streams"

# (a) duplicate FR ID → first-seen kept + plain stderr warning naming the ID, exit 0.
dup_spec="$FIXTURE_DIR/duplicate-fr-spec.md"
cat > "$dup_spec" <<'EOF'
# Feature Specification: Duplicate Demo

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST do the first thing.
- **FR-005**: FIRST_SEEN_FR005 — keep this one.
- **FR-005**: SECOND_SEEN_FR005 — drop this one.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: It works.
EOF

dup_out="$FIXTURE_DIR/duplicate-runbook.md"
dup_rc=0
dup_err=$("$SCRIPT_UNDER_TEST" "$dup_spec" "$dup_out" 2>&1 >/dev/null) || dup_rc=$?

set_test "Duplicate-ID spec exits 0 (non-fatal)"
assert_eq "0" "$dup_rc" "exit code"

set_test "stderr names the duplicated ID"
assert_contains "$dup_err" "FR-005"

set_test "Runbook keeps the first-seen FR-005 entry"
assert_contains "$(cat "$dup_out")" "FIRST_SEEN_FR005"

set_test "Runbook drops the second-seen FR-005 entry"
assert_not_contains "$(cat "$dup_out")" "SECOND_SEEN_FR005"

# (b) usage error: missing argv → exit 2.
set_test "Missing both argv → exit 2"
usage_rc=0
"$SCRIPT_UNDER_TEST" >/dev/null 2>&1 || usage_rc=$?
assert_eq "2" "$usage_rc" "exit code"

set_test "Only one positional → exit 2"
usage_rc2=0
"$SCRIPT_UNDER_TEST" "$FULL_SPEC" >/dev/null 2>&1 || usage_rc2=$?
assert_eq "2" "$usage_rc2" "exit code"

set_test "Extra positional → exit 2"
usage_rc3=0
"$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$FIXTURE_DIR/x.md" "$FIXTURE_DIR/extra.md" >/dev/null 2>&1 || usage_rc3=$?
assert_eq "2" "$usage_rc3" "exit code"

set_test "Unknown flag → exit 2"
usage_rc4=0
"$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$FIXTURE_DIR/x.md" --bogus >/dev/null 2>&1 || usage_rc4=$?
assert_eq "2" "$usage_rc4" "exit code"

# (c) missing/unreadable spec → exit 1, NO partial runbook written.
set_test "Missing spec → exit 1"
missing_out="$FIXTURE_DIR/should-not-be-written.md"
missing_rc=0
"$SCRIPT_UNDER_TEST" "$FIXTURE_DIR/does-not-exist.md" "$missing_out" >/dev/null 2>&1 || missing_rc=$?
assert_eq "1" "$missing_rc" "exit code"

set_test "Missing spec writes NO partial runbook"
assert_file_not_exists "$missing_out"

# (d) silent stdout on success.
set_test "Successful run is silent on stdout"
ok_out="$FIXTURE_DIR/silent-runbook.md"
stdout_capture=$("$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$ok_out" 2>/dev/null)
assert_eq "" "$stdout_capture" "stdout must be empty"

# ---------------------------------------------------------------------------
# BUG-1 regression: a very large ## Self-Review section must NOT crash the script
# via SIGPIPE through the head -40 pipeline (FR-006 + FR-009). The autopilot always
# passes --workflow-file and Self-Review can be long.
# ---------------------------------------------------------------------------
section "BUG-1 — large Self-Review must not SIGPIPE-abort"

big_wf="$FIXTURE_DIR/big-workflow.md"
{
  printf '# Workflow\n\n## Self-Review\n\n'
  for i in $(seq 1 5000); do
    printf -- '- finding %04d: reviewed and resolved.\n' "$i"
  done
  printf '\n## Next Section\n\nShould not be echoed.\n'
} > "$big_wf"

bug1_out="$FIXTURE_DIR/bug1-runbook.md"
bug1_rc=0
"$SCRIPT_UNDER_TEST" "$FULL_SPEC" "$bug1_out" --workflow-file "$big_wf" >/dev/null 2>&1 || bug1_rc=$?

set_test "Large Self-Review still exits 0 (no SIGPIPE abort)"
assert_eq "0" "$bug1_rc" "exit code"

set_test "Large Self-Review still writes the runbook"
assert_file_exists "$bug1_out"

# ---------------------------------------------------------------------------
# BUG-2 regression: a spec WITH a ### Edge Cases section must populate Negative-Path
# Tests with those bullets (verbatim, nested lines preserved) and annotate any
# NEEDS CLARIFICATION marker (FR-001, FR-005, FR-010). The stub is ABSENT-only.
# ---------------------------------------------------------------------------
section "BUG-2 — Edge Cases parsed into Negative-Path Tests"

edge_spec="$FIXTURE_DIR/edge-cases-spec.md"
cat > "$edge_spec" <<'EOF'
# Feature Specification: Edge Demo

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core flow (Priority: P1)

Walk the core flow.

### Edge Cases

- **Empty input**: the system rejects an empty payload with a 400.
  - Nested: the error body names the missing field.
- **Timeout boundary**: behavior at the exact timeout [NEEDS CLARIFICATION: which value?].

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST validate input.
EOF

edge_out="$FIXTURE_DIR/edge-runbook.md"
edge_rc=0
"$SCRIPT_UNDER_TEST" "$edge_spec" "$edge_out" >/dev/null 2>&1 || edge_rc=$?

set_test "Edge-cases spec exits 0"
assert_eq "0" "$edge_rc" "exit code"

edge_body=$(cat "$edge_out" 2>/dev/null || true)

set_test "Negative-Path reproduces the first edge bullet"
assert_contains "$edge_body" "rejects an empty payload with a 400"

set_test "Negative-Path reproduces the second edge bullet"
assert_contains "$edge_body" "behavior at the exact timeout"

set_test "Negative-Path preserves the nested continuation line"
assert_contains "$edge_body" "the error body names the missing field"

set_test "Edge bullet with NEEDS CLARIFICATION is annotated (FR-005)"
edge_neg_block=$(awk '/^## Negative-Path Tests/{f=1;next} /^## /{f=0} f' "$edge_out")
assert_contains "$edge_neg_block" "unresolved clarification"

set_test "Present Edge Cases section does NOT show the absent-stub line"
assert_not_contains "$edge_body" "No edge cases identified in spec.md"

test_summary
