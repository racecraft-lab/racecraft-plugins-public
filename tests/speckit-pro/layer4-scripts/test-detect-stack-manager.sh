#!/usr/bin/env bash
# test-detect-stack-manager.sh - PRSG-014 stack-manager detector tests.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh"
FIXTURE_ROOT="$TEST_DIR/fixtures/stack-manager"

SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT

run_detect() {
  local out_var="$1" err_var="$2"
  shift 2
  local stdout_file="$SANDBOX/stdout.$RANDOM"
  local stderr_file="$SANDBOX/stderr.$RANDOM"
  local rc=0
  "$@" >"$stdout_file" 2>"$stderr_file" || rc=$?
  printf -v "$out_var" '%s' "$(cat "$stdout_file")"
  printf -v "$err_var" '%s' "$(cat "$stderr_file")"
  return "$rc"
}

json_check() {
  local json="$1" expr="$2" msg="$3"
  local file="$SANDBOX/json-check.$RANDOM.json"
  printf '%s' "$json" > "$file"
  if python3 - "$file" "$expr" >/dev/null 2>&1 <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)

expr = sys.argv[2]
safe_builtins = {"any": any, "all": all, "len": len, "list": list, "range": range, "sorted": sorted}
if not eval(expr, {"__builtins__": safe_builtins}, {"data": data}):
    raise SystemExit(1)
PY
  then
    _pass
  else
    _fail "$msg"
  fi
}

section "script presence"

set_test "detect-stack-manager.sh exists"
assert_file_exists "$SCRIPT"

set_test "detect-stack-manager.sh is executable"
assert_file_executable "$SCRIPT"

section "supported detection"

prs="tests/speckit-pro/layer4-scripts/fixtures/stack-manager/topology/prsg-014-prs.json"
supported_evidence="specs/prsg-014-optional-gh-stack-stack-manager-integration/.process/stack-manager/emission/link/preflight/decision.json"
supported_log="$SANDBOX/supported-gh.log"

result=0
run_detect output stderr_output env PATH="$FIXTURE_ROOT/fake-gh/supported:$PATH" STACK_MANAGER_FAKE_LOG="$supported_log" "$SCRIPT" \
  --phase emission \
  --operation link \
  --feature-dir specs/prsg-014-optional-gh-stack-stack-manager-integration \
  --prs "$prs" \
  --base main \
  --evidence-path "$supported_evidence" || result=$?

set_test "supported detection exits 0"
assert_eq "0" "$result" "exit code"

set_test "supported detection emits gh-stack decision"
json_check "$output" \
  "data['selected_manager'] == 'gh-stack' and data['gh_stack']['supported'] == True and data['gh_stack']['support_status'] == 'supported' and data['read_only_proof']['parsed'] == True and data['read_only_proof']['matched_expected_topology'] == True" \
  "supported fake gh should select gh-stack"

set_test "supported command plan uses PR-number gh stack link argv"
json_check "$output" \
  "data['command_plan'][0]['argv'] == ['gh', 'stack', 'link', '--base', 'main', '301', '302'] and data['command_plan'][0]['mutates'] == True and data['command_plan'][0]['mutation_boundary'] == True" \
  "supported command plan should link by PR number after packet reconciliation"

set_test "supported evidence path is deterministic and repo-relative"
json_check "$output" \
  "data['evidence_path'] == 'specs/prsg-014-optional-gh-stack-stack-manager-integration/.process/stack-manager/emission/link/preflight/decision.json'" \
  "evidence path should be deterministic"

set_test "fake CLI log records only canonical gh stack checks"
assert_contains "$(cat "$supported_log")" "gh stack --version"
assert_contains "$(cat "$supported_log")" "gh stack view --json"

section "fallback detection"

result=0
run_detect output stderr_output env PATH="$FIXTURE_ROOT/fake-gh/missing:$PATH" "$SCRIPT" \
  --phase emission \
  --operation link \
  --feature-dir specs/prsg-014-optional-gh-stack-stack-manager-integration \
  --prs "$prs" \
  --base main \
  --evidence-path specs/prsg-014-optional-gh-stack-stack-manager-integration/.process/stack-manager/emission/link/missing/decision.json || result=$?

set_test "missing gh-stack exits 0"
assert_eq "0" "$result" "exit code"

set_test "missing gh-stack selects explicit fallback before mutation"
json_check "$output" \
  "data['selected_manager'] == 'explicit-gh' and data['fallback_allowed'] == True and data['gh_stack']['supported'] == False and data['command_plan'][0]['argv'][:3] == ['gh', 'pr', 'create']" \
  "missing gh-stack should select explicit gh fallback"

result=0
run_detect output stderr_output env PATH="$FIXTURE_ROOT/fake-gh/unsupported:$PATH" "$SCRIPT" \
  --phase emission \
  --operation link \
  --feature-dir specs/prsg-014-optional-gh-stack-stack-manager-integration \
  --prs "$prs" \
  --base main \
  --evidence-path specs/prsg-014-optional-gh-stack-stack-manager-integration/.process/stack-manager/emission/link/unsupported/decision.json || result=$?

set_test "unsupported version exits 0"
assert_eq "0" "$result" "exit code"

set_test "unsupported version records explicit reason"
json_check "$output" \
  "data['selected_manager'] == 'explicit-gh' and data['gh_stack']['support_status'] == 'unsupported_version' and data['gh_stack']['version'] == '0.0.1' and data['fallback_reason']" \
  "unsupported version should record fallback reason"

result=0
run_detect output stderr_output env PATH="$FIXTURE_ROOT/fake-gh/supported:$PATH" STACK_MANAGER_FAKE_MODE=mismatch "$SCRIPT" \
  --phase emission \
  --operation link \
  --feature-dir specs/prsg-014-optional-gh-stack-stack-manager-integration \
  --prs "$prs" \
  --base main \
  --evidence-path specs/prsg-014-optional-gh-stack-stack-manager-integration/.process/stack-manager/emission/link/mismatch/decision.json || result=$?

set_test "topology mismatch exits 0"
assert_eq "0" "$result" "exit code"

set_test "topology mismatch selects fallback before mutation"
json_check "$output" \
  "data['selected_manager'] == 'explicit-gh' and data['gh_stack']['support_status'] == 'topology_incompatible' and data['topology_compatibility']['compatible'] == False" \
  "topology mismatch should not select gh-stack"

section "input guards"

result=0
run_detect output stderr_output "$SCRIPT" \
  --phase emission \
  --operation link \
  --feature-dir ../bad \
  --prs "$prs" || result=$?

set_test "unsafe feature dir exits 2"
assert_eq "2" "$result" "exit code"

set_test "unsafe feature dir emits input error"
assert_contains "$stderr_output" "detect-stack-manager.sh: input_error: unsafe feature dir"

result=0
run_detect output stderr_output "$SCRIPT" \
  --phase emission \
  --operation link \
  --feature-dir specs/prsg-014-optional-gh-stack-stack-manager-integration \
  --prs "$prs" \
  --base "bad branch" || result=$?

set_test "unsafe base branch exits 2"
assert_eq "2" "$result" "exit code"

set_test "unsafe base branch emits input error"
assert_contains "$stderr_output" "detect-stack-manager.sh: input_error: unsafe base branch"

test_summary
