#!/usr/bin/env bash
# test-o5-topology.sh - PRSG-010C O5 topology and rollup tests.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/speckit-pro/skills/speckit-autopilot/scripts/o5-topology.sh"
FIXTURE_ROOT="$TEST_DIR/fixtures/o5-topology"

json_check() {
  local json="$1" expr="$2" msg="$3"
  if JSON_OBJECT="$json" python3 - "$expr" >/dev/null 2>&1 <<'PY'
import json
import os
import sys

data = json.loads(os.environ["JSON_OBJECT"])
expr = sys.argv[1]
safe_builtins = {"any": any, "all": all, "len": len, "list": list, "sorted": sorted, "set": set}
if not eval(expr, {"__builtins__": safe_builtins}, {"data": data}):
    raise SystemExit(1)
PY
  then
    _pass
  else
    _fail "$msg"
  fi
}

run_o5() {
  local out_var="$1"
  shift
  local rc=0 output
  output=$("$SCRIPT" "$@" 2>/dev/null) || rc=$?
  printf -v "$out_var" '%s' "$output"
  return "$rc"
}

section "script presence"

set_test "o5-topology.sh exists"
assert_file_exists "$SCRIPT"

set_test "o5-topology.sh is executable"
assert_file_executable "$SCRIPT"

section "valid parent topology"

valid_parent="$FIXTURE_ROOT/valid-parent/specs/prsg-500-o5-parent"

set_test "valid parent exits 0"
result=0
run_o5 valid_json "$valid_parent" || result=$?
assert_eq "0" "$result" "valid O5 topology exit code"

set_test "valid parent reports topologyStatus valid"
assert_json_field "$valid_json" "topologyStatus" "valid"

set_test "valid parent computes in_progress from child precedence"
assert_json_field "$valid_json" "computedStatus" "in_progress"

set_test "valid parent has no declared status drift"
assert_json_field "$valid_json" "declaredStatusDrift" "False"

set_test "valid parent emits children in manifest order"
json_check "$valid_json" \
  '[child["id"] for child in data["children"]] == ["PRSG-500A", "PRSG-500B", "PRSG-500C"]' \
  "children must stay in manifest order"

set_test "valid parent preserves dependency order in rows"
json_check "$valid_json" \
  'data["children"][2]["dependsOn"] == ["PRSG-500A", "PRSG-500B"]' \
  "dependsOn should round-trip in child row"

section "invalid topology"

invalid_parent="$FIXTURE_ROOT/invalid-topology/specs/prsg-501-o5-parent"

set_test "invalid topology exits 0 with report"
result=0
run_o5 invalid_json "$invalid_parent" || result=$?
assert_eq "0" "$result" "invalid topology is reported, not a usage error"

set_test "invalid topology reports invalid_topology"
assert_json_field "$invalid_json" "computedStatus" "invalid_topology"

set_test "invalid topology includes duplicate child diagnostic"
assert_contains "$invalid_json" '"duplicate_child_id"' "duplicate child id must be actionable"

set_test "invalid topology includes nested path diagnostic"
assert_contains "$invalid_json" '"nested_child_path"' "nested child path must be actionable"

set_test "invalid topology includes missing child diagnostic"
assert_contains "$invalid_json" '"missing_child"' "missing child must be actionable"

set_test "invalid topology includes unknown dependency diagnostic"
assert_contains "$invalid_json" '"unknown_dependency"' "unknown dependency must be actionable"

set_test "invalid topology includes later dependency diagnostic"
assert_contains "$invalid_json" '"later_dependency"' "later dependency/cycle risk must be actionable"

section "mixed child status rollup"

mixed_parent="$FIXTURE_ROOT/mixed-child-states/specs/prsg-502-o5-parent"

set_test "mixed child states exit 0"
result=0
run_o5 mixed_json "$mixed_parent" || result=$?
assert_eq "0" "$result" "mixed O5 topology exit code"

set_test "mixed child topology is valid"
assert_json_field "$mixed_json" "topologyStatus" "valid"

set_test "mixed child rollup applies blocked precedence"
assert_json_field "$mixed_json" "computedStatus" "blocked"

set_test "mixed child rollup reports declared drift"
assert_json_field "$mixed_json" "declaredStatusDrift" "True"

set_test "mixed child rollup emits exactly one row per declared child"
json_check "$mixed_json" \
  'len(data["children"]) == 7 and len(set(child["id"] for child in data["children"])) == 7' \
  "each declared child must appear exactly once"

set_test "mixed child rollup includes blocked, failed, in-progress, pending, complete, archived, and missing-state"
json_check "$mixed_json" \
  'set(child["status"] for child in data["children"]) == set(["blocked", "failed", "in_progress", "pending", "complete", "archived", "missing-state"])' \
  "child statuses should cover all mixed-state rows"

set_test "mixed child rollup keeps manifest order"
json_check "$mixed_json" \
  '[child["id"] for child in data["children"]] == ["PRSG-502A", "PRSG-502B", "PRSG-502C", "PRSG-502D", "PRSG-502E", "PRSG-502F", "PRSG-502G"]' \
  "mixed child rows must stay in manifest order"

section "read-only behavior"

before="$(cd "$FIXTURE_ROOT" && find . -type f -exec shasum {} + | LC_ALL=C sort)"
"$SCRIPT" "$valid_parent" >/dev/null
"$SCRIPT" "$invalid_parent" >/dev/null
"$SCRIPT" "$mixed_parent" >/dev/null
after="$(cd "$FIXTURE_ROOT" && find . -type f -exec shasum {} + | LC_ALL=C sort)"

set_test "o5-topology reads fixtures without writing"
assert_eq "$before" "$after" "fixture bytes must be unchanged"

section "input errors"

set_test "missing input exits 2"
result=0
run_o5 error_json "$FIXTURE_ROOT/does-not-exist" || result=$?
assert_eq "2" "$result" "missing manifest is usage/input error"

set_test "missing input emits top-level error"
assert_contains "$error_json" '"error"' "input error must be JSON"

test_summary
