#!/usr/bin/env bash
# test-validate-uat-runbook.sh - Regression tests for UAT runbook quality guard.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/validate-uat-runbook.sh"

TMP_ROOT=$(mktemp -d)
trap 'rm -rf "$TMP_ROOT"' EXIT

section "Validator script shape"

set_test "validator script exists"
assert_file_exists "$SCRIPT"

set_test "validator script is executable"
assert_file_executable "$SCRIPT"

section "Authored runbook"

valid="$TMP_ROOT/valid-uat-runbook.md"
cat > "$valid" <<'EOF'
# UAT Runbook: demo-feature

## Env Setup

From the repository root, run `bash tests/speckit-pro/run-all.sh --layer 4`.
No browser setup is required for this docs-only change.

## Per-Story Acceptance Tests

### User Story 1 - Reviewer sees usable UAT

1. Open the rendered PR body.
   Expected: the UAT Runbook section tells the reviewer exactly which command to run.
2. Run the command from Env Setup.
   Expected: the command completes and reports the focused script checks.

- [ ] The reviewer can complete the story without reading the implementation.

## FR Coverage Matrix

| Requirement | Acceptance check |
|-------------|------------------|
| The PR body includes actionable UAT guidance. | User Story 1, steps 1-2 |

## Negative-Path Tests

Try opening the PR body without a generated runbook.
Expected: validation blocks the packet before PR creation.
EOF

set_test "authored runbook passes"
result=0
output=$("$SCRIPT" "$valid" 2>&1) || result=$?
assert_eq "0" "$result" "exit code"

set_test "authored runbook reports ok"
assert_contains "$output" "validate-uat-runbook.sh: ok"

section "Skeleton placeholders"

skeleton="$TMP_ROOT/skeleton-uat-runbook.md"
cat > "$skeleton" <<'EOF'
# UAT Runbook: demo-feature

## Env Setup

| Command | Value |
|---------|-------|
| BUILD | <unknown - autopilot did not pass PROJECT_COMMANDS> |

## Per-Story Acceptance Tests

<a id="us-1"></a>

### User Story 1 - Demo

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| [User Story 1 - Demo](#us-1) | see the Per-Story Acceptance Tests block above |
EOF

set_test "skeleton runbook fails"
result=0
output=$("$SCRIPT" "$skeleton" 2>&1) || result=$?
assert_eq "1" "$result" "exit code"

set_test "skeleton failure identifies a UAT rule"
assert_contains "$output" "validation_failure: uat."

section "Raw anchors and PR placeholders"

anchor_runbook="$TMP_ROOT/anchor-runbook.md"
cat > "$anchor_runbook" <<'EOF'
# UAT Runbook: demo-feature

| Field | Value |
|-------|-------|
| PR | **PR:** <set on PR open> |

## Env Setup

Run `bash tests/speckit-pro/run-all.sh --layer 4`.

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Demo

1. Open the generated body.
   Expected: the body shows concrete acceptance steps.

- [ ] Reviewer completed the check.

## FR Coverage Matrix

| Requirement | Acceptance check |
|-------------|------------------|
| Reviewer sees concrete UAT. | User Story 1, step 1 |
EOF

set_test "raw HTML anchor fails"
result=0
output=$("$SCRIPT" "$anchor_runbook" 2>&1) || result=$?
assert_eq "1" "$result" "exit code"

set_test "raw HTML anchor failure is explicit"
assert_contains "$output" "validation_failure: uat.html_anchor"

pr_placeholder_runbook="$TMP_ROOT/pr-placeholder-runbook.md"
sed '/<a id=/d' "$anchor_runbook" > "$pr_placeholder_runbook"

set_test "old PR placeholder fails"
result=0
output=$("$SCRIPT" "$pr_placeholder_runbook" 2>&1) || result=$?
assert_eq "1" "$result" "exit code"

set_test "old PR placeholder failure is explicit"
assert_contains "$output" "validation_failure: uat.pr_placeholder"

section "Absent runbook"

set_test "missing runbook fails"
result=0
output=$("$SCRIPT" "$TMP_ROOT/missing.md" 2>&1) || result=$?
assert_eq "1" "$result" "exit code"

set_test "missing failure identifies absent runbook"
assert_contains "$output" "validation_failure: uat.missing"

test_summary
