#!/usr/bin/env bash
# test-restack.sh - PRSG-009 foundation tests for dry-run-first restack entrypoint.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/speckit-pro/skills/speckit-autopilot/scripts/restack.sh"
FIXTURE_ROOT="$TEST_DIR/fixtures/multi-pr-emission/restack"

SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT

json_check() {
  local json="$1" expr="$2" msg="$3"
  local file="$SANDBOX/json-check.json"
  printf '%s' "$json" > "$file"
  if python3 - "$file" "$expr" >/dev/null 2>&1 <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)

expr = sys.argv[2]
safe_builtins = {"any": any, "all": all, "len": len, "list": list, "sorted": sorted}
if not eval(expr, {"__builtins__": safe_builtins}, {"data": data}):
    raise SystemExit(1)
PY
  then
    _pass
  else
    _fail "$msg"
  fi
}

run_restack() {
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

write_fake_restack_tools() {
  local bin_dir="$1"
  mkdir -p "$bin_dir"
  cat > "$bin_dir/git" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'git %s\n' "$*" >> "${RESTACK_FAKE_LOG:?}"
if [ "${1:-}" = "status" ] && [ "${2:-}" = "--porcelain" ]; then
  if [ "${RESTACK_FAKE_MODE:-clean}" = "dirty" ]; then
    printf ' M docs/us1.md\n'
  fi
  exit 0
fi
exit 0
EOF
  cat > "$bin_dir/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'gh %s\n' "$*" >> "${RESTACK_FAKE_LOG:?}"
case "${RESTACK_FAKE_MODE:-clean}" in
  gh-fail)
    printf 'gh unavailable\n' >&2
    exit 1
    ;;
  conflict)
    printf 'merge conflict while retargeting\n' >&2
    exit 1
    ;;
esac
exit 0
EOF
  chmod +x "$bin_dir/git" "$bin_dir/gh"
}

section "script presence"

set_test "restack.sh exists"
assert_file_exists "$SCRIPT"

set_test "restack.sh is executable"
assert_file_executable "$SCRIPT"

section "CLI validation"

state="$FIXTURE_ROOT/remaining-stack-state.json"
manifest="$FIXTURE_ROOT/remaining-prs-manifest.json"
two_state="$SANDBOX/two-remaining-stack-state.json"
two_manifest="$SANDBOX/two-remaining-prs-manifest.json"
float_state="$SANDBOX/float-review-order-state.json"

cat > "$two_state" <<'EOF'
{
  "multi_pr_emission": {
    "schema_version": 1,
    "status": "emitting",
    "source_layer_plan": { "path": "tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/layer-plans/valid-three-slice.json" },
    "base_branch": "main",
    "base_sha": "0123456789abcdef",
    "next_slice_id": "us1",
    "reconciled_at": "",
    "slices": [
      {
        "slice_id": "foundation",
        "review_order": 1,
        "expected_branch": "prsg-009-multi-pr-emission/01-foundation",
        "expected_base_branch": "main",
        "declared_files": ["docs/foundation.md"],
        "declared_scoped_tests": [],
        "status": "merged"
      },
      {
        "slice_id": "us1",
        "review_order": 2,
        "expected_branch": "prsg-009-multi-pr-emission/02-us1",
        "expected_base_branch": "prsg-009-multi-pr-emission/01-foundation",
        "declared_files": ["docs/us1.md"],
        "declared_scoped_tests": [],
        "status": "pr_opened"
      },
      {
        "slice_id": "us2",
        "review_order": 3,
        "expected_branch": "prsg-009-multi-pr-emission/03-us2",
        "expected_base_branch": "prsg-009-multi-pr-emission/02-us1",
        "declared_files": ["docs/us2.md"],
        "declared_scoped_tests": [],
        "status": "pr_opened"
      }
    ]
  }
}
EOF

cat > "$two_manifest" <<'EOF'
{
  "schemaVersion": 2,
  "records": [
    {
      "review_order": 1,
      "slice_id": "foundation",
      "branch": "prsg-009-multi-pr-emission/01-foundation",
      "base_branch": "main",
      "pr_number": 201,
      "pr_url": "https://github.com/racecraft-lab/Paddock/pull/201",
      "declared_files": ["docs/foundation.md"],
      "verification_evidence": "specs/prsg-009-multi-pr-emission/.process/emission/foundation/layer4.log",
      "status": "merged",
      "head_sha": "headabc1",
      "merged_sha": "mergeabc1"
    },
    {
      "review_order": 2,
      "slice_id": "us1",
      "branch": "prsg-009-multi-pr-emission/02-us1",
      "base_branch": "prsg-009-multi-pr-emission/01-foundation",
      "pr_number": 202,
      "pr_url": "https://github.com/racecraft-lab/Paddock/pull/202",
      "declared_files": ["docs/us1.md"],
      "verification_evidence": "specs/prsg-009-multi-pr-emission/.process/emission/us1/layer4.log",
      "status": "opened",
      "head_sha": "headabc2",
      "merged_sha": null
    },
    {
      "review_order": 3,
      "slice_id": "us2",
      "branch": "prsg-009-multi-pr-emission/03-us2",
      "base_branch": "prsg-009-multi-pr-emission/02-us1",
      "pr_number": 203,
      "pr_url": "https://github.com/racecraft-lab/Paddock/pull/203",
      "declared_files": ["docs/us2.md"],
      "verification_evidence": "specs/prsg-009-multi-pr-emission/.process/emission/us2/layer4.log",
      "status": "opened",
      "head_sha": "headabc3",
      "merged_sha": null
    }
  ]
}
EOF

cat > "$float_state" <<'EOF'
{
  "multi_pr_emission": {
    "schema_version": 1,
    "status": "emitting",
    "slices": [
      {
        "slice_id": "foundation",
        "review_order": 1.5,
        "expected_branch": "prsg-009-multi-pr-emission/01-foundation",
        "expected_base_branch": "main",
        "status": "merged"
      }
    ]
  }
}
EOF

set_test "missing required --manifest exits 2"
result=0
run_restack output stderr_output "$SCRIPT" \
  --state "$state" \
  --base main \
  --remote origin \
  --start-after prsg-009-multi-pr-emission/01-foundation || result=$?
assert_eq "2" "$result" "exit code"

set_test "missing required option uses deterministic stderr"
assert_eq "restack.sh: input_error: missing required option --manifest" "$stderr_output" "stderr"

set_test "input error JSON exit_code matches process exit"
json_check "$output" \
  "data['status'] == 'input_error' and data['exit_code'] == 2 and data['dry_run'] == True" \
  "input-error stdout should carry matching status/exit_code"

set_test "non-integer state review_order exits 2"
result=0
run_restack output stderr_output "$SCRIPT" \
  --state "$float_state" \
  --manifest "$manifest" \
  --base main \
  --remote origin \
  --start-after prsg-009-multi-pr-emission/01-foundation || result=$?
assert_eq "2" "$result" "exit code"

set_test "non-integer state review_order emits deterministic stderr"
assert_eq "restack.sh: input_error: invalid restack state shape" "$stderr_output" "stderr"

section "dry-run default"

set_test "valid restack invocation defaults to dry-run and exits 0"
result=0
run_restack output stderr_output env RESTACK_GH_STACK_BIN="$SANDBOX/missing-gh-stack" "$SCRIPT" \
  --state "$state" \
  --manifest "$manifest" \
  --base main \
  --remote origin \
  --start-after prsg-009-multi-pr-emission/01-foundation || result=$?
assert_eq "0" "$result" "exit code"

set_test "dry-run success emits no stderr"
assert_eq "" "$stderr_output" "stderr"

set_test "dry-run stdout matches foundation output schema"
json_check "$output" \
  "data['dry_run'] == True and data['status'] == 'success' and data['exit_code'] == 0 and data['base'] == 'main' and data['remote'] == 'origin' and data['start_after'] == 'prsg-009-multi-pr-emission/01-foundation' and data['scope_preserved'] == True and data['operations'][0]['slice_id'] == 'us1' and data['operations'][0]['old_base'] == 'prsg-009-multi-pr-emission/01-foundation' and data['operations'][0]['new_base'] == 'main' and data['operations'][0]['applied'] == False" \
  "dry-run output should plan remaining retarget operations without applying them"

set_test "dry-run stdout is one compact JSON object"
if printf '%s' "$output" | python3 -c 'import json,sys; data=json.load(sys.stdin); sys.exit(0 if isinstance(data, dict) else 1)' >/dev/null 2>&1 \
  && [[ "$output" != *$'\n'* ]]; then
  _pass
else
  _fail "expected one compact JSON object on stdout"
fi

set_test "dry-run preserves remaining branch order and new base topology"
result=0
run_restack output stderr_output env RESTACK_GH_STACK_BIN="$SANDBOX/missing-gh-stack" "$SCRIPT" \
  --state "$two_state" \
  --manifest "$two_manifest" \
  --base main \
  --remote origin \
  --start-after prsg-009-multi-pr-emission/01-foundation || result=$?
assert_eq "0" "$result" "exit code"
json_check "$output" \
  "[op['slice_id'] for op in data['operations']] == ['us1', 'us2'] and [op['new_base'] for op in data['operations']] == ['main', 'prsg-009-multi-pr-emission/02-us1'] and all(op['result'] == 'planned_scope_preserved' for op in data['operations'])" \
  "dry-run should retarget first remaining slice to base and later slices to the preceding remaining branch"

set_test "dry-run does not call git or gh mutation tools"
fake_bin="$SANDBOX/fake-bin-dry-run"
fake_log="$SANDBOX/fake-dry-run.log"
write_fake_restack_tools "$fake_bin"
result=0
run_restack output stderr_output env PATH="$fake_bin:$PATH" RESTACK_FAKE_LOG="$fake_log" RESTACK_FAKE_MODE=clean RESTACK_GH_STACK_BIN="$SANDBOX/missing-gh-stack" "$SCRIPT" \
  --state "$two_state" \
  --manifest "$two_manifest" \
  --base main \
  --remote origin \
  --start-after prsg-009-multi-pr-emission/01-foundation || result=$?
assert_eq "0" "$result" "exit code"
assert_file_not_exists "$fake_log"

set_test "optional gh-stack inspection is non-mutating when available"
gh_stack_bin="$SANDBOX/fake-gh-stack"
gh_stack_log="$SANDBOX/fake-gh-stack.log"
cat > "$gh_stack_bin" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'gh-stack %s\n' "$*" >> "${RESTACK_GH_STACK_LOG:?}"
printf '{"active":true}\n'
EOF
chmod +x "$gh_stack_bin"
result=0
run_restack output stderr_output env RESTACK_GH_STACK_BIN="$gh_stack_bin" RESTACK_GH_STACK_LOG="$gh_stack_log" "$SCRIPT" \
  --state "$state" \
  --manifest "$manifest" \
  --base main \
  --remote origin \
  --start-after prsg-009-multi-pr-emission/01-foundation || result=$?
assert_eq "0" "$result" "exit code"
json_check "$output" \
  "data['gh_stack']['available'] == True and data['gh_stack']['inspected'] == True and data['gh_stack']['mutating'] == False" \
  "gh-stack should be optional, detected, and used only for non-mutating inspection"
assert_eq "gh-stack status --json" "$(cat "$gh_stack_log" 2>/dev/null || true)" "gh-stack inspection command"

section "apply and failure mapping"

set_test "--apply retargets PR bases with fake gh and records applied operations"
apply_bin="$SANDBOX/fake-bin-apply"
apply_log="$SANDBOX/fake-apply.log"
write_fake_restack_tools "$apply_bin"
result=0
run_restack output stderr_output env PATH="$apply_bin:$PATH" RESTACK_FAKE_LOG="$apply_log" RESTACK_FAKE_MODE=clean RESTACK_GH_STACK_BIN="$SANDBOX/missing-gh-stack" "$SCRIPT" \
  --state "$two_state" \
  --manifest "$two_manifest" \
  --base main \
  --remote origin \
  --start-after prsg-009-multi-pr-emission/01-foundation \
  --apply || result=$?
assert_eq "0" "$result" "exit code"
assert_eq "" "$stderr_output" "stderr"
json_check "$output" \
  "data['dry_run'] == False and data['status'] == 'success' and data['exit_code'] == 0 and all(op['applied'] == True and op['result'] == 'applied_scope_preserved' for op in data['operations'])" \
  "apply output should mark planned retarget operations as applied"
assert_contains "$(cat "$apply_log" 2>/dev/null || true)" "gh pr edit 202 --base main"
assert_contains "$(cat "$apply_log" 2>/dev/null || true)" "gh pr edit 203 --base prsg-009-multi-pr-emission/02-us1"

set_test "--apply emits stack-manager decision before retarget mutation"
json_check "$output" \
  "data['stack_manager_decision']['schema_version'] == 'stack-manager-decision.v1' and data['stack_manager_decision']['phase'] == 'restack' and data['stack_manager_decision']['operation'] == 'restack'" \
  "apply output should include stack-manager decision evidence"

set_test "dirty worktree maps to exit code 3 with deterministic stderr"
dirty_bin="$SANDBOX/fake-bin-dirty"
dirty_log="$SANDBOX/fake-dirty.log"
write_fake_restack_tools "$dirty_bin"
result=0
run_restack output stderr_output env PATH="$dirty_bin:$PATH" RESTACK_FAKE_LOG="$dirty_log" RESTACK_FAKE_MODE=dirty RESTACK_GH_STACK_BIN="$SANDBOX/missing-gh-stack" "$SCRIPT" \
  --state "$state" \
  --manifest "$manifest" \
  --base main \
  --remote origin \
  --start-after prsg-009-multi-pr-emission/01-foundation \
  --apply || result=$?
assert_eq "3" "$result" "exit code"
assert_eq "restack.sh: dirty_worktree: worktree has uncommitted changes" "$stderr_output" "stderr"
json_check "$output" \
  "data['status'] == 'dirty_worktree' and data['exit_code'] == 3 and data['dry_run'] == False and data['recovery_evidence']['retry_policy'] == 'clean worktree and rerun restack.sh --apply'" \
  "dirty worktree JSON should carry exit-code parity and retry evidence"

set_test "gh failure maps to exit code 4 with deterministic stderr"
gh_fail_bin="$SANDBOX/fake-bin-gh-fail"
gh_fail_log="$SANDBOX/fake-gh-fail.log"
write_fake_restack_tools "$gh_fail_bin"
result=0
run_restack output stderr_output env PATH="$gh_fail_bin:$PATH" RESTACK_FAKE_LOG="$gh_fail_log" RESTACK_FAKE_MODE=gh-fail RESTACK_GH_STACK_BIN="$SANDBOX/missing-gh-stack" "$SCRIPT" \
  --state "$state" \
  --manifest "$manifest" \
  --base main \
  --remote origin \
  --start-after prsg-009-multi-pr-emission/01-foundation \
  --apply || result=$?
assert_eq "4" "$result" "exit code"
assert_eq "restack.sh: git_gh_failure: gh pr edit failed for prsg-009-multi-pr-emission/02-us1" "$stderr_output" "stderr"
json_check "$output" \
  "data['status'] == 'git_gh_failure' and data['exit_code'] == 4 and data['recovery_evidence']['failed_operation']['slice_id'] == 'us1'" \
  "gh failures should map to exit 4 and identify the failed operation"

set_test "retarget conflict maps to exit code 1 with deterministic stderr"
conflict_bin="$SANDBOX/fake-bin-conflict"
conflict_log="$SANDBOX/fake-conflict.log"
write_fake_restack_tools "$conflict_bin"
result=0
run_restack output stderr_output env PATH="$conflict_bin:$PATH" RESTACK_FAKE_LOG="$conflict_log" RESTACK_FAKE_MODE=conflict RESTACK_GH_STACK_BIN="$SANDBOX/missing-gh-stack" "$SCRIPT" \
  --state "$state" \
  --manifest "$manifest" \
  --base main \
  --remote origin \
  --start-after prsg-009-multi-pr-emission/01-foundation \
  --apply || result=$?
assert_eq "1" "$result" "exit code"
assert_eq "restack.sh: conflicts: restack conflict while retargeting prsg-009-multi-pr-emission/02-us1" "$stderr_output" "stderr"
json_check "$output" \
  "data['status'] == 'conflicts' and data['exit_code'] == 1 and data['recovery_evidence']['retry_policy'] == 'resolve conflict and rerun restack.sh --apply'" \
  "conflicts should map to exit 1 with retry evidence"

test_summary
