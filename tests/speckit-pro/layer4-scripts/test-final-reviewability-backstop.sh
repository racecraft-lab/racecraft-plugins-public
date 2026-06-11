#!/usr/bin/env bash
# test-final-reviewability-backstop.sh - PRSG-010A final hatch tests.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh"
FIXTURE_ROOT="$TEST_DIR/fixtures/final-reviewability-backstop"

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

run_backstop() {
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

write_shared_inputs() {
  layer_plan="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/layer-plan.json"
  sizing_result="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/atomicity-route.json"
  changed_files="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/changed-files.txt"
  full_verification="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/emission/full-regression.txt"
  mkdir -p "$(dirname "$layer_plan")" "$(dirname "$full_verification")"

  jq -n '{
    tool: "plan-layers",
    contract_version: 1,
    status: "ok",
    feature_dir: "specs/prsg-010-harden-the-hatch",
    tasks_file: "specs/prsg-010-harden-the-hatch/tasks.md",
    increments: [
      {
        id: "us1",
        order: 1,
        title: "Final reviewability hatch",
        depends_on: [],
        files: [
          "speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh",
          "speckit-pro/skills/speckit-autopilot/contracts/reslicing-packet.schema.json"
        ],
        tests: [
          "tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh"
        ],
        advisory_size: {reviewable_loc: 620, production_files: 3, total_files: 10}
      },
      {
        id: "polish",
        order: 2,
        title: "Guidance parity",
        depends_on: ["us1"],
        files: [
          "speckit-pro/skills/speckit-autopilot/SKILL.md",
          "speckit-pro/codex-skills/speckit-autopilot/SKILL.md"
        ],
        tests: [],
        advisory_size: {reviewable_loc: 120, production_files: 0, total_files: 4}
      }
    ],
    warnings: [],
    errors: [],
    summary: {
      increment_count: 2,
      task_count: 17,
      warning_count: 0,
      error_count: 0,
      message: "Layer plan ok"
    }
  }' > "$layer_plan"

  jq -n '{
    tool: "atomicity-route",
    route: "split-PR",
    releasable: true,
    signals: ["size:split-required"],
    hints: [],
    warnings: [],
    thresholds: {
      reviewable_loc: 800,
      production_files: 8,
      total_files: 25
    },
    summary: "Split PR route required by final diff size."
  }' > "$sizing_result"

  cat > "$changed_files" <<'EOF'
speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh
speckit-pro/skills/speckit-autopilot/contracts/final-reviewability-gate-state.schema.json
speckit-pro/skills/speckit-autopilot/contracts/reslicing-packet.schema.json
tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh
EOF
  printf '%s\n' 'Layer 4 focused verification passed before final gate.' > "$full_verification"
}

invoke_backstop() {
  local gate_result="$1" gate_exit_code="$2" state_output="$3" packet_output="$4"
  shift 4
  run_backstop output stderr_output "$SCRIPT" \
    --gate-result "$gate_result" \
    --gate-exit-code "$gate_exit_code" \
    --state-output "$state_output" \
    --packet-output "$packet_output" \
    "$@" \
    --feature-dir specs/prsg-010-harden-the-hatch \
    --feature-branch prsg-010-harden-the-hatch \
    --spec-id PRSG-010A \
    --title "Final reviewability hatch" \
    --base-ref main \
    --head-ref prsg-010-harden-the-hatch \
    --base-sha 0123456789abcdef \
    --layer-plan "$layer_plan" \
    --sizing-result "$sizing_result" \
    --changed-files "$changed_files" \
    --full-verification-evidence "$full_verification" \
    --timestamp 2026-06-11T12:00:00Z
}

section "script presence"

set_test "final-reviewability-backstop.sh exists"
assert_file_exists "$SCRIPT"

set_test "final-reviewability-backstop.sh is executable"
assert_file_executable "$SCRIPT"

write_shared_inputs

section "unexcepted final gate block"

block_state="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/final-reviewability/gate-state.json"
block_packet="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/final-reviewability/reslicing-packet.json"

set_test "Block without exception exits 1 before PR emission"
result=0
invoke_backstop "$FIXTURE_ROOT/block-no-exception/gate-result.json" 1 "$block_state" "$block_packet" || result=$?
assert_eq "1" "$result" "exit code"

set_test "Block writes top-level final gate state"
assert_file_exists "$block_state"

set_test "Block writes re-slicing packet"
assert_file_exists "$block_packet"

block_state_json=$(cat "$block_state")
block_packet_json=$(cat "$block_packet")

set_test "Block state status is block"
assert_json_field "$block_state_json" "status" "block"

set_test "Block state asserts no PR was created"
assert_json_field "$block_state_json" "pr_created" "False"

set_test "Block state includes packet path"
assert_json_field "$block_state_json" "reslicing_packet_path" "specs/prsg-010-harden-the-hatch/.process/final-reviewability/reslicing-packet.json"

set_test "Block state records all stopped operations"
json_check "$block_state_json" \
  '"pr-body-generation" in data["blocked_operations"] and "single-pr-create" in data["blocked_operations"] and "multi-pr-emission" in data["blocked_operations"]' \
  "blocked_operations must include every PR boundary"

set_test "Packet keeps all PR creation assertions false"
json_check "$block_packet_json" \
  'data["no_pr_assertions"] == {"pr_created": False, "pr": None, "pr_body_generated": False, "single_pr_create_invoked": False, "gh_pr_create_invoked": False, "multi_pr_emission_invoked": False}' \
  "no_pr_assertions must all be false/null"

set_test "Packet includes PRSG-007 routing operator step"
json_check "$block_packet_json" \
  'any(step["phase"] == "prsg-007-routing" and "atomicity-route.sh" in step["command"] for step in data["operator_steps"])' \
  "operator_steps missing PRSG-007 reroute"

set_test "Packet includes PRSG-008 layer-plan operator step"
json_check "$block_packet_json" \
  'any(step["phase"] == "prsg-008-layer-planning" and "plan-layers.sh" in step["command"] for step in data["operator_steps"])' \
  "operator_steps missing PRSG-008 regeneration"

set_test "Packet includes PRSG-009 handoff operator step"
json_check "$block_packet_json" \
  'any(step["phase"] == "prsg-009-multi-pr-emission" and "multi-pr-emission.sh" in step["command"] for step in data["operator_steps"])' \
  "operator_steps missing PRSG-009 handoff"

set_test "Packet resumes from PRSG-009 when routing and layer plan are valid"
assert_json_field "$block_packet_json" "resume.resume_from" "prsg-009-multi-pr-emission"

section "valid typed exception"

exception_state="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/final-reviewability/exception-state.json"
exception_packet="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/final-reviewability/exception-packet.json"

set_test "Valid refactor exception exits 0"
result=0
invoke_backstop "$FIXTURE_ROOT/valid-refactor-exception/gate-result.json" 0 "$exception_state" "$exception_packet" || result=$?
assert_eq "0" "$result" "exit code"

set_test "Valid exception writes state"
assert_file_exists "$exception_state"

set_test "Valid exception does not write re-slicing packet"
assert_file_not_exists "$exception_packet"

exception_state_json=$(cat "$exception_state")

set_test "Valid exception state status is exception"
assert_json_field "$exception_state_json" "status" "exception"

set_test "Valid exception records class"
assert_json_field "$exception_state_json" "exception.class" "refactor"

set_test "Valid exception records honored evidence"
json_check "$exception_state_json" \
  'data["exception"]["honored"] is True and len(data["exception"]["evidence"]) == 1 and data["exception"]["evidence"][0]["provenance"] == "contract"' \
  "honored exception evidence missing"

section "generated exception provenance"

generated_state="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/final-reviewability/generated-state.json"
generated_packet="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/final-reviewability/generated-packet.json"

set_test "Generated boilerplate exception is rejected and exits 1"
result=0
invoke_backstop "$FIXTURE_ROOT/generated-boilerplate/gate-result.json" 0 "$generated_state" "$generated_packet" || result=$?
assert_eq "1" "$result" "exit code"

generated_state_json=$(cat "$generated_state")
generated_packet_json=$(cat "$generated_packet")

set_test "Generated provenance block state is block"
assert_json_field "$generated_state_json" "status" "block"

set_test "Generated provenance is recorded as rejected evidence"
json_check "$generated_packet_json" \
  'len(data["exceptions"]["accepted"]) == 0 and any(item["provenance"] == "template" and item["honored"] is False for item in data["exceptions"]["rejected"])' \
  "template evidence must move to rejected"

section "gate error"

error_state="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/final-reviewability/error-state.json"
error_packet="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/final-reviewability/error-packet.json"

set_test "Gate error exits 2"
result=0
invoke_backstop "$FIXTURE_ROOT/gate-error/gate-result.json" 2 "$error_state" "$error_packet" || result=$?
assert_eq "2" "$result" "exit code"

set_test "Gate error writes state"
assert_file_exists "$error_state"

set_test "Gate error does not write packet"
assert_file_not_exists "$error_packet"

error_state_json=$(cat "$error_state")

set_test "Gate error state status is error"
assert_json_field "$error_state_json" "status" "error"

set_test "Gate error packet path is null"
assert_json_field "$error_state_json" "reslicing_packet_path" "None"

section "warn proceed"

warn_gate="$SANDBOX/warn-gate-result.json"
warn_state="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/final-reviewability/warn-state.json"
warn_packet="$SANDBOX/specs/prsg-010-harden-the-hatch/.process/final-reviewability/warn-packet.json"

jq -n '{
  mode: "diff",
  status: "warn",
  pass: true,
  reviewable_loc: 420,
  production_files: 2,
  total_files: 4,
  primary_surface_count: 1,
  primary_surfaces: ["harness/adapter"],
  greenfield: false,
  thresholds: {
    warn: {reviewable_loc: 400, production_files: 6, total_files: 15, primary_surfaces: 1},
    block: {reviewable_loc: 800, production_files: 8, total_files: 25, primary_surfaces: 1}
  },
  exception_honored: false,
  exception_class: null,
  warnings: ["reviewable LOC 420 exceeds warn threshold 400"],
  blockers: [],
  exceptions: {accepted: [], rejected: []}
}' > "$warn_gate"

set_test "Warn exits 0 and writes no packet"
result=0
invoke_backstop "$warn_gate" 0 "$warn_state" "$warn_packet" || result=$?
assert_eq "0" "$result" "exit code"

set_test "Warn state status is warn"
assert_json_field "$(cat "$warn_state")" "status" "warn"

set_test "Warn does not write packet"
assert_file_not_exists "$warn_packet"

test_summary
