#!/usr/bin/env bash
# test-validate-pr-packet.sh - PRSG-012 contract tests for PR packet validation.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh"
PACKET_FIXTURE_REL="tests/speckit-pro/layer4-scripts/fixtures/pr-packet"
FIXTURE_ROOT="$REPO_ROOT/$PACKET_FIXTURE_REL"
FEATURE_DIR_REL="specs/prsg-012-reviewer-ready-pr-packet-contract"

SANDBOX=$(mktemp -d)
TEST_REPO="$SANDBOX/repo"
RUN_DIR="$SANDBOX/runs"
FAKE_BIN="$SANDBOX/bin"
GH_CAPTURE="$RUN_DIR/gh-calls.log"
trap 'rm -rf "$SANDBOX"' EXIT

mkdir -p "$RUN_DIR" "$FAKE_BIN" "$TEST_REPO/tests/speckit-pro/layer4-scripts/fixtures" "$TEST_REPO/specs" "$TEST_REPO/docs/ai/specs/.process"
cp -R "$FIXTURE_ROOT" "$TEST_REPO/tests/speckit-pro/layer4-scripts/fixtures/pr-packet"
cp -R "$REPO_ROOT/$FEATURE_DIR_REL" "$TEST_REPO/specs/"
cat > "$TEST_REPO/docs/ai/specs/.process/PRSG-012-workflow.md" <<'EOF'
# PRSG-012 Workflow Fixture

## Phase 7: Implement
EOF
printf '{}\n' > "$TEST_REPO/$PACKET_FIXTURE_REL/unreadable-packet.json"
chmod 000 "$TEST_REPO/$PACKET_FIXTURE_REL/unreadable-packet.json" 2>/dev/null || {
  printf 'test setup failed: unable to make unreadable packet fixture\n' >&2
  exit 1
}

cat > "$FAKE_BIN/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'gh %s\n' "$*" >> "${GH_CAPTURE:?}"
exit 0
EOF
chmod +x "$FAKE_BIN/gh"

LAST_STDOUT=""
LAST_STDERR=""
LAST_EXIT_FILE=""

validation_result_rel() {
  local packet_id="$1"
  printf '%s/.process/pr-packets/%s/validation.json' "$FEATURE_DIR_REL" "$packet_id"
}

validation_result_file() {
  local packet_id="$1"
  printf '%s/%s' "$TEST_REPO" "$(validation_result_rel "$packet_id")"
}

reset_gh_capture() {
  rm -f "$GH_CAPTURE"
}

run_validator_capture() {
  local name="$1"
  shift

  LAST_STDOUT="$RUN_DIR/$name.stdout"
  LAST_STDERR="$RUN_DIR/$name.stderr"
  LAST_EXIT_FILE="$RUN_DIR/$name.exit"

  local rc=0
  set +e
  (
    cd "$TEST_REPO"
    GH_CAPTURE="$GH_CAPTURE" PATH="$FAKE_BIN:$PATH" "$SCRIPT" "$@"
  ) >"$LAST_STDOUT" 2>"$LAST_STDERR"
  rc=$?
  set -e

  printf '%s\n' "$rc" > "$LAST_EXIT_FILE"
}

assert_captured_exit() {
  local expected="$1"
  local actual
  actual=$(cat "$LAST_EXIT_FILE")
  assert_eq "$expected" "$actual" "validator exit code"
}

assert_captured_stderr_empty() {
  local stderr
  stderr=$(cat "$LAST_STDERR")
  assert_eq "" "$stderr" "stderr"
}

assert_captured_stderr_contains() {
  local needle="$1" msg="${2:-stderr}"
  local stderr
  stderr=$(cat "$LAST_STDERR")
  assert_contains "$stderr" "$needle" "$msg"
}

assert_json_file_field() {
  local json_file="$1" field="$2" expected="$3" msg="${4:-}"
  local actual
  actual=$(
    python3 - "$json_file" "$field" 2>/dev/null <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)

value = data
for key in sys.argv[2].split("."):
    value = value[key]

print(value)
PY
  ) || {
    _fail "${msg:+$msg: }failed to parse JSON field '$field'"
    return
  }

  if [ "$expected" = "$actual" ]; then
    _pass
  else
    _fail "${msg:+$msg: }field '$field': expected '$expected', got '$actual'"
  fi
}

assert_json_file_check() {
  local json_file="$1" expr="$2" msg="$3"
  if python3 - "$json_file" "$expr" <<'PY' >/dev/null 2>&1
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)

safe_builtins = {"any": any, "all": all, "isinstance": isinstance, "len": len, "list": list, "sorted": sorted, "str": str}
if not eval(sys.argv[2], {"__builtins__": safe_builtins}, {"data": data}):
    raise SystemExit(1)
PY
  then
    _pass
  else
    _fail "$msg"
  fi
}

assert_json_files_equivalent() {
  local left="$1" right="$2" msg="$3"
  if python3 - "$left" "$right" <<'PY' >/dev/null 2>&1
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    left = json.load(handle)
with open(sys.argv[2], encoding="utf-8") as handle:
    right = json.load(handle)

if left != right:
    raise SystemExit(1)
PY
  then
    _pass
  else
    _fail "$msg"
  fi
}

assert_no_pr_create_attempts() {
  if [ ! -s "$GH_CAPTURE" ]; then
    _pass
  else
    _fail "validator must not attempt gh pr create; captured: $(cat "$GH_CAPTURE")"
  fi
}

assert_success_json() {
  local packet_id="$1" mode="$2" title="$3" body_file="$4"
  local result_file
  result_file="$(validation_result_file "$packet_id")"

  set_test "$packet_id stdout is deterministic success JSON"
  assert_json_file_field "$LAST_STDOUT" "schema_version" "1.0.0"

  set_test "$packet_id stdout records packet id"
  assert_json_file_field "$LAST_STDOUT" "packet_id" "$packet_id"

  set_test "$packet_id stdout records mode"
  assert_json_file_field "$LAST_STDOUT" "mode" "$mode"

  set_test "$packet_id stdout records success status"
  assert_json_file_field "$LAST_STDOUT" "status" "passed"

  set_test "$packet_id stdout records non-blocking class"
  assert_json_file_field "$LAST_STDOUT" "error_class" "none"

  set_test "$packet_id stdout records exit 0"
  assert_json_file_field "$LAST_STDOUT" "exit_code" "0"

  set_test "$packet_id stdout records title"
  assert_json_file_field "$LAST_STDOUT" "title_value" "$title"

  set_test "$packet_id stdout records body file"
  assert_json_file_field "$LAST_STDOUT" "body_file" "$body_file"

  set_test "$packet_id stdout records pr_blocked false"
  assert_json_file_field "$LAST_STDOUT" "pr_blocked" "False"

  set_test "$packet_id stdout matches validation_result schema shape"
  assert_json_file_check "$LAST_STDOUT" \
    "'validation_result_path' not in data and data['stderr_line'] == '' and data['target']['base_branch'] and data['target']['head_branch'] and len(data['rule_outcomes']) >= 1 and data['timestamp']" \
    "success JSON should use validation_result contract fields"

  set_test "$packet_id validation result file exists"
  assert_file_exists "$result_file"

  set_test "$packet_id writes the emitted success JSON"
  assert_json_files_equivalent "$LAST_STDOUT" "$result_file" "stdout and validation result file should match"
}

assert_failure_json() {
  local packet_id="$1" expected_class="$2" expected_exit="$3" result_path="$4"

  set_test "$packet_id stdout records failure status"
  assert_json_file_field "$LAST_STDOUT" "status" "failed"

  set_test "$packet_id stdout records error class"
  assert_json_file_field "$LAST_STDOUT" "error_class" "$expected_class"

  set_test "$packet_id stdout records exit code"
  assert_json_file_field "$LAST_STDOUT" "exit_code" "$expected_exit"

  set_test "$packet_id stdout records pr_blocked true"
  assert_json_file_field "$LAST_STDOUT" "pr_blocked" "True"

  set_test "$packet_id stdout carries remediation evidence"
  assert_json_file_check "$LAST_STDOUT" "len(data['failures']) >= 1 and len(data['remediation_evidence']) >= 1" \
    "failure JSON should include at least one failure and remediation item"

  set_test "$packet_id stdout matches validation_result schema shape"
  assert_json_file_check "$LAST_STDOUT" \
    "'validation_result_path' not in data and 'target' in data and data['stderr_line'] and len(data['rule_outcomes']) >= 1 and data['timestamp'] and all(isinstance(item, str) for item in data['remediation_evidence']) and all('rule_id' not in f and 'affected_field' not in f and 'rule' in f and 'field' in f and 'message' in f for f in data['failures'])" \
    "failure JSON should use validation_result contract fields"

  if [ "$result_path" != "no-path" ]; then
    set_test "$packet_id validation result file exists"
    assert_file_exists "$TEST_REPO/$result_path"

    set_test "$packet_id writes the emitted failure JSON"
    assert_json_files_equivalent "$LAST_STDOUT" "$TEST_REPO/$result_path" \
      "stdout and validation result file should match"
  else
    set_test "$packet_id stdout records no-path in stderr_line"
    assert_json_file_check "$LAST_STDOUT" "data['stderr_line'].endswith(': no-path')" \
      "input-error JSON should carry no-path in stderr_line"
  fi
}

assert_failure_rule() {
  local rule_id="$1"
  assert_json_file_check "$LAST_STDOUT" \
    "any(f.get('rule') == '$rule_id' for f in data['failures'])" \
    "failure JSON should include rule $rule_id"
}

assert_no_failure_rule() {
  local rule_id="$1"
  assert_json_file_check "$LAST_STDOUT" \
    "not any(f.get('rule') == '$rule_id' for f in data['failures'])" \
    "failure JSON should not include rule $rule_id"
}

section "script presence"

set_test "validate-pr-packet.sh exists"
assert_file_exists "$SCRIPT"

set_test "validate-pr-packet.sh is executable"
assert_file_executable "$SCRIPT"

section "valid packets"

valid_single="$PACKET_FIXTURE_REL/valid-single.json"
valid_single_body="$PACKET_FIXTURE_REL/bodies/valid-single.md"
run_validator_capture "valid-single" "$valid_single"

set_test "valid single packet exits 0"
assert_captured_exit "0"

set_test "valid single packet emits no stderr"
assert_captured_stderr_empty

assert_success_json "valid-single" "single" \
  "feat(speckit-pro): Add reviewer-ready PR packets" \
  "$valid_single_body"

valid_prsg_scope_rel="$PACKET_FIXTURE_REL/valid-prsg-scope.json"
jq \
  --arg packet_id "valid-prsg-scope" \
  --arg title "feat(PRSG-012): Add reviewer-ready PR packets" \
  --arg scope "PRSG-012" \
  --arg result "$(validation_result_rel valid-prsg-scope)" \
  '.packet_id = $packet_id
    | .generated_title.value = $title
    | .generated_title.scope = $scope
    | .validation_result_path = $result' \
  "$TEST_REPO/$PACKET_FIXTURE_REL/valid-single.json" > "$TEST_REPO/$valid_prsg_scope_rel"

run_validator_capture "valid-prsg-scope" "$valid_prsg_scope_rel"

set_test "valid PRSG-scoped packet exits 0"
assert_captured_exit "0"

assert_success_json "valid-prsg-scope" "single" \
  "feat(PRSG-012): Add reviewer-ready PR packets" \
  "$valid_single_body"

valid_spec_scope_rel="$PACKET_FIXTURE_REL/valid-spec-scope.json"
jq \
  --arg packet_id "valid-spec-scope" \
  --arg title "feat(SPEC-014C): Add future title contract" \
  --arg scope "SPEC-014C" \
  --arg description "Add future title contract" \
  --arg result "$(validation_result_rel valid-spec-scope)" \
  '.packet_id = $packet_id
    | .generated_title.value = $title
    | .generated_title.scope = $scope
    | .generated_title.description = $description
    | .validation_result_path = $result' \
  "$TEST_REPO/$PACKET_FIXTURE_REL/valid-single.json" > "$TEST_REPO/$valid_spec_scope_rel"

run_validator_capture "valid-spec-scope" "$valid_spec_scope_rel"

set_test "valid future SPEC-scoped packet exits 0"
assert_captured_exit "0"

assert_success_json "valid-spec-scope" "single" \
  "feat(SPEC-014C): Add future title contract" \
  "$valid_single_body"

valid_split="$PACKET_FIXTURE_REL/valid-split.json"
valid_split_body="$PACKET_FIXTURE_REL/bodies/valid-split.md"
run_validator_capture "valid-split" "$valid_split"

set_test "valid split packet exits 0"
assert_captured_exit "0"

set_test "valid split packet emits no stderr"
assert_captured_stderr_empty

assert_success_json "valid-split" "split" \
  "feat(speckit-pro): Validate reviewer packet slices" \
  "$valid_split_body"

section "safe prose refinement"

valid_edited_rel="$PACKET_FIXTURE_REL/valid-single-edited.json"
valid_edited_body_rel="$PACKET_FIXTURE_REL/bodies/valid-single-edited.md"
jq \
  --arg packet_id "valid-single-edited" \
  --arg body "$valid_edited_body_rel" \
  --arg result "$(validation_result_rel valid-single-edited)" \
  '.packet_id = $packet_id | .body_file = $body | .validation_result_path = $result' \
  "$TEST_REPO/$PACKET_FIXTURE_REL/valid-single.json" > "$TEST_REPO/$valid_edited_rel"

run_validator_capture "valid-single-edited" "$valid_edited_rel"

set_test "valid single edited packet exits 0"
assert_captured_exit "0"

assert_success_json "valid-single-edited" "single" \
  "feat(speckit-pro): Add reviewer-ready PR packets" \
  "$valid_edited_body_rel"

host_coexist_rel="$PACKET_FIXTURE_REL/valid-host-coexist.json"
host_coexist_body_rel="$PACKET_FIXTURE_REL/bodies/valid-host-coexist.md"
cp "$TEST_REPO/$valid_edited_body_rel" "$TEST_REPO/$host_coexist_body_rel"
cat >> "$TEST_REPO/$host_coexist_body_rel" <<'EOF'

# Host Required

- [ ] Keep the host repository checklist outside the canonical packet block.
EOF
jq \
  --arg packet_id "valid-host-coexist" \
  --arg body "$host_coexist_body_rel" \
  --arg result "$(validation_result_rel valid-host-coexist)" \
  '.packet_id = $packet_id | .body_file = $body | .validation_result_path = $result' \
  "$TEST_REPO/$PACKET_FIXTURE_REL/valid-single.json" > "$TEST_REPO/$host_coexist_rel"

run_validator_capture "valid-host-coexist" "$host_coexist_rel"

set_test "host template content outside canonical packet block exits 0"
assert_captured_exit "0"

invalid_protected_result="$(validation_result_rel invalid-protected-edit)"
reset_gh_capture
run_validator_capture "invalid-protected-edit" "$PACKET_FIXTURE_REL/invalid-protected-edit.json"

set_test "invalid protected edit exits 1"
assert_captured_exit "1"

assert_failure_json "invalid-protected-edit" "validation_failure" "1" "$invalid_protected_result"

set_test "invalid protected edit reports fingerprint rule"
assert_failure_rule "body.protected_fingerprint"

invalid_boundary_rel="$PACKET_FIXTURE_REL/invalid-editable-boundary.json"
invalid_boundary_body_rel="$PACKET_FIXTURE_REL/bodies/invalid-editable-boundary.md"
sed '/speckit-pro-editable:summary:end/d' "$TEST_REPO/$valid_edited_body_rel" > "$TEST_REPO/$invalid_boundary_body_rel"
jq \
  --arg packet_id "invalid-editable-boundary" \
  --arg body "$invalid_boundary_body_rel" \
  --arg result "$(validation_result_rel invalid-editable-boundary)" \
  '.packet_id = $packet_id | .body_file = $body | .validation_result_path = $result' \
  "$TEST_REPO/$PACKET_FIXTURE_REL/valid-single.json" > "$TEST_REPO/$invalid_boundary_rel"

run_validator_capture "invalid-editable-boundary" "$invalid_boundary_rel"

set_test "invalid editable boundary exits 1"
assert_captured_exit "1"

set_test "invalid editable boundary reports boundary rule"
assert_failure_rule "body.editable_boundaries"

unknown_comment_rel="$PACKET_FIXTURE_REL/invalid-unknown-comment.json"
unknown_comment_body_rel="$PACKET_FIXTURE_REL/bodies/invalid-unknown-comment.md"
cp "$TEST_REPO/$valid_edited_body_rel" "$TEST_REPO/$unknown_comment_body_rel"
cat >> "$TEST_REPO/$unknown_comment_body_rel" <<'EOF'

<!-- stale host template comment -->
EOF
jq \
  --arg packet_id "invalid-unknown-comment" \
  --arg body "$unknown_comment_body_rel" \
  --arg result "$(validation_result_rel invalid-unknown-comment)" \
  '.packet_id = $packet_id | .body_file = $body | .validation_result_path = $result' \
  "$TEST_REPO/$PACKET_FIXTURE_REL/valid-single.json" > "$TEST_REPO/$unknown_comment_rel"

run_validator_capture "invalid-unknown-comment" "$unknown_comment_rel"

set_test "invalid unknown comment exits 1"
assert_captured_exit "1"

set_test "invalid unknown comment reports comment rule"
assert_failure_rule "body.unknown_comment"

section "rendered-content validation failures"

invalid_title_result="$(validation_result_rel invalid-title-token)"
reset_gh_capture
run_validator_capture "invalid-title-token" "$PACKET_FIXTURE_REL/invalid-title-token.json"

set_test "invalid title token exits 1"
assert_captured_exit "1"

set_test "invalid title token stderr identifies validation failure"
assert_captured_stderr_contains "validate-pr-packet.sh: validation_failure: invalid-title-token:" \
  "validation failure stderr"

set_test "invalid title token stderr includes result path"
assert_captured_stderr_contains "$invalid_title_result" "validation failure result path"

assert_failure_json "invalid-title-token" "validation_failure" "1" "$invalid_title_result"

set_test "invalid title token makes no PR creation attempts"
assert_no_pr_create_attempts

generic_title_rel="$PACKET_FIXTURE_REL/invalid-generic-title.json"
jq \
  --arg packet_id "invalid-generic-title" \
  --arg title "feat(PRSG-012): User Story 1 - Specific Conventional PR Titles (Priority: P1) MVP" \
  --arg scope "PRSG-012" \
  --arg description "User Story 1 - Specific Conventional PR Titles (Priority: P1) MVP" \
  --arg result "$(validation_result_rel invalid-generic-title)" \
  '.packet_id = $packet_id
    | .generated_title.value = $title
    | .generated_title.scope = $scope
    | .generated_title.description = $description
    | .validation_result_path = $result' \
  "$TEST_REPO/$PACKET_FIXTURE_REL/valid-single.json" > "$TEST_REPO/$generic_title_rel"

generic_title_result="$(validation_result_rel invalid-generic-title)"
reset_gh_capture
run_validator_capture "invalid-generic-title" "$generic_title_rel"

set_test "invalid generic title exits 1"
assert_captured_exit "1"

assert_failure_json "invalid-generic-title" "validation_failure" "1" "$generic_title_result"

set_test "invalid generic title reports public description rule"
assert_failure_rule "title.public_description"

set_test "invalid generic title makes no PR creation attempts"
assert_no_pr_create_attempts

git_ref_title_rel="$PACKET_FIXTURE_REL/invalid-git-ref-title.json"
jq \
  --arg packet_id "invalid-git-ref-title" \
  --arg title "feat(PRSG-012): Update refs/heads/internal-branch packet title" \
  --arg description "Update refs/heads/internal-branch packet title" \
  --arg result "$(validation_result_rel invalid-git-ref-title)" \
  '.packet_id = $packet_id
    | .generated_title.value = $title
    | .generated_title.description = $description
    | .validation_result_path = $result' \
  "$TEST_REPO/$PACKET_FIXTURE_REL/valid-single.json" > "$TEST_REPO/$git_ref_title_rel"

git_ref_title_result="$(validation_result_rel invalid-git-ref-title)"
reset_gh_capture
run_validator_capture "invalid-git-ref-title" "$git_ref_title_rel"

set_test "invalid git ref title exits 1"
assert_captured_exit "1"

assert_failure_json "invalid-git-ref-title" "validation_failure" "1" "$git_ref_title_result"

set_test "invalid git ref title reports banned public text"
assert_failure_rule "text.banned_or_placeholder"

set_test "invalid git ref title makes no PR creation attempts"
assert_no_pr_create_attempts

invalid_missing_result="$(validation_result_rel invalid-missing-evidence)"
reset_gh_capture
run_validator_capture "invalid-missing-evidence" "$PACKET_FIXTURE_REL/invalid-missing-evidence.json"

set_test "invalid missing evidence exits 1"
assert_captured_exit "1"

set_test "invalid missing evidence stderr identifies validation failure"
assert_captured_stderr_contains "validate-pr-packet.sh: validation_failure: invalid-missing-evidence:" \
  "validation failure stderr"

set_test "invalid missing evidence stderr includes result path"
assert_captured_stderr_contains "$invalid_missing_result" "validation failure result path"

assert_failure_json "invalid-missing-evidence" "validation_failure" "1" "$invalid_missing_result"

set_test "invalid missing evidence makes no PR creation attempts"
assert_no_pr_create_attempts

invalid_body_rel="$PACKET_FIXTURE_REL/invalid-body-content.json"
invalid_body_body_rel="$PACKET_FIXTURE_REL/bodies/invalid-body-content.md"
invalid_body_json="$TEST_REPO/$invalid_body_rel"
invalid_body_body="$TEST_REPO/$invalid_body_body_rel"
mkdir -p "$(dirname "$invalid_body_body")"
cat > "$invalid_body_body" <<'EOF'
<!-- speckit-pro-review-packet-source: tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-body-content.json -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Plain-English Summary: TODO replace {{SUMMARY}}.
<!-- speckit-pro-editable:summary:end -->

## Summary

Duplicate heading should fail canonical heading validation.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
<!-- TODO: hidden template comment must not survive rendering -->
Example: replace this text before opening a PR.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
Reviewer evidence is incomplete.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

Inspect the invalid fixture.

## How To UAT

Placeholder UAT text.

## UAT Runbook

Compatibility heading is present.

## Scope

Changed files are missing.

## Known Gaps

Verification, source markers, and traceability are missing.
EOF
jq \
  --arg packet_id "invalid-body-content" \
  --arg body "$invalid_body_body_rel" \
  --arg result "$(validation_result_rel invalid-body-content)" \
  '.packet_id = $packet_id | .body_file = $body | .validation_result_path = $result' \
  "$TEST_REPO/$PACKET_FIXTURE_REL/valid-single.json" > "$invalid_body_json"

invalid_body_result="$(validation_result_rel invalid-body-content)"
reset_gh_capture
run_validator_capture "invalid-body-content" "$invalid_body_rel"

set_test "invalid body content exits 1"
assert_captured_exit "1"

set_test "invalid body content stderr identifies validation failure"
assert_captured_stderr_contains "validate-pr-packet.sh: validation_failure: invalid-body-content:" \
  "validation failure stderr"

assert_failure_json "invalid-body-content" "validation_failure" "1" "$invalid_body_result"

set_test "invalid body content reports heading order rule"
assert_failure_rule "body.heading_order"

set_test "invalid body content reports stale body text rule"
assert_failure_rule "body.banned_or_placeholder"

set_test "invalid body content reports traceability rule"
assert_failure_rule "body.traceability"

set_test "invalid body content makes no PR creation attempts"
assert_no_pr_create_attempts

hidden_evidence_rel="$PACKET_FIXTURE_REL/invalid-hidden-evidence.json"
hidden_evidence_body_rel="$PACKET_FIXTURE_REL/bodies/invalid-hidden-evidence.md"
hidden_evidence_json="$TEST_REPO/$hidden_evidence_rel"
hidden_evidence_body="$TEST_REPO/$hidden_evidence_body_rel"
mkdir -p "$(dirname "$hidden_evidence_body")"
cat > "$hidden_evidence_body" <<'EOF'
<!-- speckit-pro-review-packet-source: tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-hidden-evidence.json -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Adds reviewer-facing packet validation.
<!-- speckit-pro-editable:summary:end -->

```md
## Summary
Source: hidden inside fenced code.
Traceability: hidden inside fenced code.
```

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Validates only reviewer-visible evidence.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
Reviewers can scan the rendered body without hidden evidence satisfying the contract.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

Inspect the visible body content.

## How To UAT

Run the packet validator fixture.

## UAT Runbook

Manual UAT is not required for this fixture.

## Verification

- Focused packet validation fixture.

## Scope

- Reviewable LOC: fixture-only evidence.

## Known Gaps

No known gaps.
EOF
jq \
  --arg packet_id "invalid-hidden-evidence" \
  --arg body "$hidden_evidence_body_rel" \
  --arg result "$(validation_result_rel invalid-hidden-evidence)" \
  '.packet_id = $packet_id | .body_file = $body | .validation_result_path = $result' \
  "$TEST_REPO/$PACKET_FIXTURE_REL/valid-single.json" > "$hidden_evidence_json"

hidden_evidence_result="$(validation_result_rel invalid-hidden-evidence)"
reset_gh_capture
run_validator_capture "invalid-hidden-evidence" "$hidden_evidence_rel"

set_test "invalid hidden evidence exits 1"
assert_captured_exit "1"

assert_failure_json "invalid-hidden-evidence" "validation_failure" "1" "$hidden_evidence_result"

set_test "hidden fenced traceability does not satisfy rendered evidence"
assert_failure_rule "body.traceability"

set_test "hidden fenced source does not satisfy rendered evidence"
assert_failure_rule "body.required_content"

set_test "fenced headings do not affect canonical heading order"
assert_no_failure_rule "body.heading_order"

set_test "invalid hidden evidence makes no PR creation attempts"
assert_no_pr_create_attempts

generic_body_rel="$PACKET_FIXTURE_REL/invalid-generic-body.json"
generic_body_body_rel="$PACKET_FIXTURE_REL/bodies/invalid-generic-body.md"
cp "$TEST_REPO/$valid_edited_body_rel" "$TEST_REPO/$generic_body_body_rel"
cat >> "$TEST_REPO/$generic_body_body_rel" <<'EOF'

Prepared `prsg-012-reviewer-ready-pr-packet-contract/02-us1` for review against `prsg-012-reviewer-ready-pr-packet-contract/01-foundation`.
EOF
jq \
  --arg packet_id "invalid-generic-body" \
  --arg body "$generic_body_body_rel" \
  --arg result "$(validation_result_rel invalid-generic-body)" \
  '.packet_id = $packet_id | .body_file = $body | .validation_result_path = $result' \
  "$TEST_REPO/$PACKET_FIXTURE_REL/valid-single.json" > "$TEST_REPO/$generic_body_rel"

generic_body_result="$(validation_result_rel invalid-generic-body)"
reset_gh_capture
run_validator_capture "invalid-generic-body" "$generic_body_rel"

set_test "invalid generic body exits 1"
assert_captured_exit "1"

assert_failure_json "invalid-generic-body" "validation_failure" "1" "$generic_body_result"

set_test "invalid generic body reports packet prose rule"
assert_failure_rule "body.generic_packet_prose"

set_test "invalid generic body makes no PR creation attempts"
assert_no_pr_create_attempts

workflow_fixture="$TEST_REPO/docs/ai/specs/.process/PRSG-012-workflow.md"

set_test "invalid body content writes deterministic workflow event"
assert_contains "$(cat "$workflow_fixture" 2>/dev/null || true)" "speckit-pro-pr-packet-validation:event-id=invalid-body-content"

run_validator_capture "invalid-body-content-repeat" "$invalid_body_rel"

set_test "invalid body content repeat still exits 1"
assert_captured_exit "1"

set_test "invalid body content supersedes previous workflow event"
event_count=$(grep -Fc "speckit-pro-pr-packet-validation:event-id=invalid-body-content" "$workflow_fixture" 2>/dev/null || true)
assert_eq "1" "$event_count" "workflow event count"

set_test "input-error fixture args file exists"
assert_file_exists "$TEST_REPO/$PACKET_FIXTURE_REL/invalid-missing-packet.args"

section "input errors from packet paths"

missing_packet_rel="$PACKET_FIXTURE_REL/missing-packet.json"
reset_gh_capture
run_validator_capture "missing-packet-file" "$missing_packet_rel"

set_test "missing packet file exits 2"
assert_captured_exit "2"

set_test "missing packet file stderr records no-path"
assert_captured_stderr_contains "no-path" "missing packet no-path"

assert_failure_json "missing-packet" "input_error" "2" "no-path"

set_test "missing packet file makes no PR creation attempts"
assert_no_pr_create_attempts

unreadable_packet_rel="$PACKET_FIXTURE_REL/unreadable-packet.json"
reset_gh_capture
run_validator_capture "unreadable-packet-file" "$unreadable_packet_rel"

set_test "unreadable packet exits 2"
assert_captured_exit "2"

set_test "unreadable packet stderr records no-path"
assert_captured_stderr_contains "no-path" "unreadable packet no-path"

assert_failure_json "unreadable-packet" "input_error" "2" "no-path"

set_test "unreadable packet makes no PR creation attempts"
assert_no_pr_create_attempts

directory_packet_rel="$PACKET_FIXTURE_REL"
reset_gh_capture
run_validator_capture "directory-packet-path" "$directory_packet_rel"

set_test "directory packet path exits 2"
assert_captured_exit "2"

set_test "directory packet path stderr records no-path"
assert_captured_stderr_contains "no-path" "directory packet no-path"

assert_failure_json "pr-packet" "input_error" "2" "no-path"

set_test "directory packet path makes no PR creation attempts"
assert_no_pr_create_attempts

invalid_no_feature_result="no-path"
reset_gh_capture
run_validator_capture "invalid-no-feature-dir" "$PACKET_FIXTURE_REL/invalid-no-feature-dir.json"

set_test "invalid no-feature-dir packet exits 2"
assert_captured_exit "2"

set_test "invalid no-feature-dir stderr records no-path"
assert_captured_stderr_contains "no-path" "no-feature-dir no-path"

assert_failure_json "invalid-no-feature-dir" "input_error" "2" "$invalid_no_feature_result"

set_test "invalid no-feature-dir makes no PR creation attempts"
assert_no_pr_create_attempts

mismatched_result_rel="$PACKET_FIXTURE_REL/invalid-mismatched-result-path.json"
jq \
  --arg packet_id "invalid-mismatched-result-path" \
  --arg result "$FEATURE_DIR_REL/.process/pr-packets/other-packet/validation.json" \
  '.packet_id = $packet_id | .validation_result_path = $result' \
  "$TEST_REPO/$PACKET_FIXTURE_REL/valid-single.json" > "$TEST_REPO/$mismatched_result_rel"

reset_gh_capture
run_validator_capture "invalid-mismatched-result-path" "$mismatched_result_rel"

set_test "mismatched validation result path exits 2"
assert_captured_exit "2"

set_test "mismatched validation result path stderr records no-path"
assert_captured_stderr_contains "no-path" "mismatched result no-path"

assert_failure_json "invalid-mismatched-result-path" "input_error" "2" "no-path"

set_test "mismatched validation result path makes no PR creation attempts"
assert_no_pr_create_attempts

schema_invalid_result="$(validation_result_rel invalid-schema-with-feature-dir)"
reset_gh_capture
run_validator_capture "invalid-schema-with-feature-dir" "$PACKET_FIXTURE_REL/invalid-schema-with-feature-dir.json"

set_test "schema-invalid packet with feature dir exits 1"
assert_captured_exit "1"

set_test "schema-invalid packet with feature dir writes derived result path"
assert_file_exists "$TEST_REPO/$schema_invalid_result"

assert_failure_json "invalid-schema-with-feature-dir" "validation_failure" "1" "$schema_invalid_result"

set_test "schema-invalid packet reports required field rule"
assert_failure_rule "packet.required"

set_test "schema-invalid packet makes no PR creation attempts"
assert_no_pr_create_attempts

section "input errors"

reset_gh_capture
run_validator_capture "invalid-malformed-json" "$PACKET_FIXTURE_REL/invalid-malformed-json.json"

set_test "malformed packet JSON exits 2"
assert_captured_exit "2"

set_test "malformed packet JSON stderr identifies input error"
assert_captured_stderr_contains "validate-pr-packet.sh: input_error:" "input error stderr"

set_test "malformed packet JSON stderr records no-path"
assert_captured_stderr_contains "no-path" "input error no-path"

assert_failure_json "invalid-malformed-json" "input_error" "2" "no-path"

set_test "malformed packet JSON makes no PR creation attempts"
assert_no_pr_create_attempts

reset_gh_capture
run_validator_capture "missing-packet-path"

set_test "missing packet path exits 2"
assert_captured_exit "2"

set_test "missing packet path stderr identifies input error"
assert_captured_stderr_contains "validate-pr-packet.sh: input_error:" "input error stderr"

set_test "missing packet path stderr records no-path"
assert_captured_stderr_contains "no-path" "input error no-path"

assert_failure_json "missing-packet-path" "input_error" "2" "no-path"

set_test "missing packet path makes no PR creation attempts"
assert_no_pr_create_attempts

test_summary
