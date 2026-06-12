#!/usr/bin/env bash
# test-validate-pr-packet.sh - PRSG-012 failing contract tests for PR packet validation.
#
# This harness intentionally lands before validate-pr-packet.sh exists. Until
# T008 creates the validator, the script presence and behavior assertions fail
# with real missing-executable evidence.

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

mkdir -p "$RUN_DIR" "$FAKE_BIN" "$TEST_REPO/tests/speckit-pro/layer4-scripts/fixtures" "$TEST_REPO/specs"
cp -R "$FIXTURE_ROOT" "$TEST_REPO/tests/speckit-pro/layer4-scripts/fixtures/pr-packet"
cp -R "$REPO_ROOT/$FEATURE_DIR_REL" "$TEST_REPO/specs/"

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

safe_builtins = {"any": any, "all": all, "len": len, "list": list, "sorted": sorted}
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

  if [ "$result_path" != "no-path" ]; then
    set_test "$packet_id validation result file exists"
    assert_file_exists "$TEST_REPO/$result_path"

    set_test "$packet_id writes the emitted failure JSON"
    assert_json_files_equivalent "$LAST_STDOUT" "$TEST_REPO/$result_path" \
      "stdout and validation result file should match"
  else
    set_test "$packet_id stdout records no-path result"
    assert_json_file_field "$LAST_STDOUT" "validation_result_path" "no-path"
  fi
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
