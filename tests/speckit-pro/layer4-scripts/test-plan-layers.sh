#!/usr/bin/env bash
# test-plan-layers.sh - RED contract harness for plan-layers.sh (PRSG-008).
#
# This file intentionally lands before the production planner implementation.
# Until plan-layers.sh exists, the script-discovery and planner outcome checks
# fail with real exit-code/JSON assertion mismatches.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh"
SCHEMA="$REPO_ROOT/specs/prsg-008-layer-planner/contracts/plan-layers.schema.json"
FIXTURE_ROOT="$TEST_DIR/fixtures/plan-layers"

SANDBOX=$(mktemp -d)
RUN_DIR="$SANDBOX/runs"
mkdir -p "$RUN_DIR"
trap 'rm -rf "$SANDBOX"' EXIT

LAST_STDOUT=""
LAST_STDERR=""
LAST_EXIT_FILE=""
LAST_ELAPSED_FILE=""

monotonic_ns() {
  python3 -c 'import time; print(time.monotonic_ns())'
}

run_planner_capture() {
  local name="$1"
  shift

  LAST_STDOUT="$RUN_DIR/$name.stdout"
  LAST_STDERR="$RUN_DIR/$name.stderr"
  LAST_EXIT_FILE="$RUN_DIR/$name.exit"
  LAST_ELAPSED_FILE="$RUN_DIR/$name.elapsed_ms"

  local start_ns end_ns exit_code
  start_ns=$(monotonic_ns)
  set +e
  bash "$SCRIPT" "$@" >"$LAST_STDOUT" 2>"$LAST_STDERR"
  exit_code=$?
  set -e
  end_ns=$(monotonic_ns)

  printf '%s\n' "$exit_code" >"$LAST_EXIT_FILE"
  printf '%s\n' "$(((end_ns - start_ns) / 1000000))" >"$LAST_ELAPSED_FILE"
}

assert_captured_exit() {
  local expected="$1"
  local actual
  actual=$(cat "$LAST_EXIT_FILE")
  assert_eq "$expected" "$actual" "planner exit code"
}

assert_valid_json_file() {
  local json_file="$1"
  if python3 -m json.tool "$json_file" >/dev/null 2>&1; then
    _pass
  else
    _fail "stdout must be valid JSON"
  fi
}

assert_schema_contract_file() {
  local schema_file="$1"
  if python3 - "$schema_file" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    schema = json.load(handle)

status = schema["properties"]["status"]["enum"]
assert status == ["ok", "invalid_plan", "input_error"]
assert schema["definitions"]["semantic_increment_id"]["pattern"] == "^(foundation|polish|us[1-9][0-9]*)$"
assert set(schema["definitions"]["advisory_size"]["required"]) == {
    "task_count",
    "file_reference_count",
    "distinct_file_count",
    "test_reference_count",
    "distinct_test_count",
}
PY
  then
    _pass
  else
    _fail "contract schema must declare PRSG-008 planner invariants"
  fi
}

assert_plan_schema_file() {
  local json_file="$1"
  local errors
  errors=$(python3 - "$json_file" "$SCHEMA" <<'PY' 2>&1 || true
import json
import re
import sys

json_path = sys.argv[1]
schema_path = sys.argv[2]

invalid_codes = {
    "missing_required_heading",
    "empty_increment",
    "unknown_increment",
    "dependency_cycle",
    "contradictory_increment_order",
    "duplicate_increment_id",
    "duplicate_task_id",
    "malformed_task",
}
input_codes = {
    "invalid_invocation",
    "feature_dir_not_found",
    "feature_dir_unreadable",
    "tasks_file_missing",
    "tasks_file_unreadable",
}
warning_codes = {"task_without_references", "reference_not_found"}
required_detail_keys = {
    "missing_required_heading": {"required_heading"},
    "empty_increment": {"increment_id"},
    "unknown_increment": {"increment_id"},
    "dependency_cycle": {"cycle"},
    "contradictory_increment_order": {"expected_order", "observed_order"},
    "duplicate_increment_id": {"increment_id", "first_source", "duplicate_source"},
    "duplicate_task_id": {"task_id", "first_source", "duplicate_source"},
    "malformed_task": {"line_text"},
    "task_without_references": {"task_id", "increment_id"},
    "reference_not_found": {"kind", "reference", "task_id"},
    "invalid_invocation": {"expected_args", "received_args"},
    "feature_dir_not_found": {"feature_dir"},
    "feature_dir_unreadable": {"feature_dir"},
    "tasks_file_missing": {"tasks_file"},
    "tasks_file_unreadable": {"tasks_file"},
}
increment_re = re.compile(r"^(foundation|polish|us[1-9][0-9]*)$")
story_re = re.compile(r"^us[1-9][0-9]*$")
problems = []

with open(schema_path, "r", encoding="utf-8") as handle:
    json.load(handle)

try:
    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except Exception as exc:
    print(f"invalid JSON: {exc}")
    sys.exit(1)

required = {
    "tool",
    "contract_version",
    "status",
    "feature_dir",
    "tasks_file",
    "increments",
    "warnings",
    "errors",
    "summary",
}
if set(data) != required:
    problems.append(f"top-level keys mismatch: {sorted(data)}")

if data.get("tool") != "plan-layers":
    problems.append("tool must be plan-layers")
if not isinstance(data.get("contract_version"), int) or data.get("contract_version", 0) < 1:
    problems.append("contract_version must be a positive integer")

status = data.get("status")
if status not in {"ok", "invalid_plan", "input_error"}:
    problems.append(f"invalid status: {status!r}")

increments = data.get("increments")
warnings = data.get("warnings")
errors = data.get("errors")
summary = data.get("summary")
for field, value in (("increments", increments), ("warnings", warnings), ("errors", errors)):
    if not isinstance(value, list):
        problems.append(f"{field} must be an array")

if isinstance(summary, dict):
    expected_summary = {"increment_count", "task_count", "warning_count", "error_count", "message"}
    if set(summary) != expected_summary:
        problems.append("summary keys mismatch")
else:
    problems.append("summary must be an object")

if status == "ok":
    if not increments:
        problems.append("ok status requires at least one increment")
    if errors:
        problems.append("ok status requires an empty errors array")
elif status == "invalid_plan":
    if not errors:
        problems.append("invalid_plan status requires errors")
    elif any(item.get("code") not in invalid_codes for item in errors if isinstance(item, dict)):
        problems.append("invalid_plan errors must use invalid-plan diagnostic codes")
elif status == "input_error":
    if increments:
        problems.append("input_error status requires no increments")
    if not errors:
        problems.append("input_error status requires errors")
    elif any(item.get("code") not in input_codes for item in errors if isinstance(item, dict)):
        problems.append("input_error errors must use input diagnostic codes")

for diag in list(warnings or []) + list(errors or []):
    if not isinstance(diag, dict):
        problems.append("diagnostic must be an object")
        continue
    if set(diag) != {"code", "severity", "message", "source", "details"}:
        problems.append(f"diagnostic keys mismatch: {diag!r}")
        continue
    code = diag["code"]
    severity = diag["severity"]
    if code in warning_codes and severity != "warning":
        problems.append(f"{code} must use warning severity")
    if code in invalid_codes | input_codes and severity != "error":
        problems.append(f"{code} must use error severity")
    if code not in required_detail_keys:
        problems.append(f"unknown diagnostic code: {code}")
    elif set(diag["details"]) != required_detail_keys[code]:
        problems.append(f"{code} details keys mismatch")
    if code == "reference_not_found" and diag["details"].get("kind") not in {"file", "test"}:
        problems.append("reference_not_found kind must be file or test")

for increment in increments or []:
    if not isinstance(increment, dict):
        problems.append("increment must be an object")
        continue
    if not increment_re.match(str(increment.get("id", ""))):
        problems.append(f"bad increment id: {increment.get('id')!r}")
    if increment.get("kind") not in {"foundation", "story", "polish"}:
        problems.append(f"bad increment kind: {increment.get('kind')!r}")
    advisory = increment.get("advisory_size")
    if not isinstance(advisory, dict) or set(advisory) != {
        "task_count",
        "file_reference_count",
        "distinct_file_count",
        "test_reference_count",
        "distinct_test_count",
    }:
        problems.append("advisory_size must be counts-only")
    for dep in increment.get("depends_on", []):
        if not increment_re.match(str(dep)):
            problems.append(f"bad dependency id: {dep!r}")
    for task in increment.get("tasks", []):
        if task.get("status") not in {"todo", "done"}:
            problems.append(f"bad task status: {task.get('status')!r}")
        if not isinstance(task.get("parallel"), bool):
            problems.append("task parallel must be boolean")
        story = task.get("story")
        if story is not None and not story_re.match(str(story)):
            problems.append(f"bad story id: {story!r}")
        if not increment_re.match(str(task.get("increment_id", ""))):
            problems.append(f"bad task increment id: {task.get('increment_id')!r}")

if problems:
    print("; ".join(problems))
    sys.exit(1)
PY
)

  if [ -z "$errors" ]; then
    _pass
  else
    _fail "schema validation failed: $errors"
  fi
}

snapshot_tree() {
  local root="$1"
  python3 - "$root" <<'PY'
import hashlib
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
for path in sorted(item for item in root.rglob("*") if item.is_file()):
    rel = path.relative_to(root).as_posix()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"{digest}  {rel}")
PY
}

assert_snapshot_unchanged() {
  local before="$1"
  local after="$2"
  if [ "$before" = "$after" ]; then
    _pass
  else
    _fail "planner must not modify fixture files"
  fi
}

generate_performance_fixture() {
  local feature_dir="$1"
  mkdir -p "$feature_dir"
  {
    printf '# Tasks: Generated Layer Plan\n\n'
    printf '## Phase 1: Foundation\n\n'
    for index in $(seq 1 50); do
      printf -- '- [ ] T%03d Prepare generated foundation file specs/prsg-008-layer-planner/contracts/plan-layers.output.md and test tests/speckit-pro/layer4-scripts/test-plan-layers.sh\n' "$index"
    done
    printf '\n## Phase 2: User Story 1 - Generated Parser (Priority: P1)\n\n'
    for index in $(seq 51 150); do
      printf -- '- [ ] T%03d [P] [US1] Parse generated task %03d in speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh and tests/speckit-pro/layer4-scripts/test-plan-layers.sh\n' "$index" "$index"
    done
    printf '\n## Phase 3: Polish and Validation\n\n'
    for index in $(seq 151 200); do
      printf -- '- [ ] T%03d Validate generated task %03d in tests/speckit-pro/layer4-scripts/test-plan-layers.sh\n' "$index" "$index"
    done
    printf '\n## Dependencies & Execution Order\n\n'
    printf '### Phase Dependencies\n\n'
    printf -- '- **Foundation**: No prerequisites.\n'
    printf -- '- **US1**: Depends on Foundation.\n'
    printf -- '- **Polish**: Depends on US1.\n'
    printf '\n### Incremental Delivery\n\n'
    printf '1. Complete Foundation: T001-T050\n'
    printf '2. Complete US1: T051-T150\n'
    printf '3. Complete Polish: T151-T200\n'
  } >"$feature_dir/tasks.md"
}

section "contract schema surface (T001-T003)"

set_test "Planner schema JSON is well formed"
if python3 -m json.tool "$SCHEMA" >/dev/null 2>&1; then
  _pass
else
  _fail "schema file must parse as JSON"
fi

set_test "Planner schema declares core PRSG-008 invariants"
assert_schema_contract_file "$SCHEMA"

set_test "Planner script is discoverable"
assert_file_exists "$SCRIPT" "plan-layers.sh path"

section "valid fixture capture, schema, and read-only checks (T003-T004)"

valid_snapshot_before=$(snapshot_tree "$FIXTURE_ROOT/valid-real")
run_planner_capture "valid-real" "$FIXTURE_ROOT/valid-real"

set_test "valid-real exits 0"
assert_captured_exit "0"

set_test "valid-real stdout is valid JSON"
assert_valid_json_file "$LAST_STDOUT"

set_test "valid-real stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

set_test "valid-real stderr capture exists"
assert_file_exists "$LAST_STDERR" "stderr capture"

set_test "valid-real fixture remains read-only"
valid_snapshot_after=$(snapshot_tree "$FIXTURE_ROOT/valid-real")
assert_snapshot_unchanged "$valid_snapshot_before" "$valid_snapshot_after"

section "fixture exit-code front door (T005-T013)"

run_planner_capture "missing-headings" "$FIXTURE_ROOT/missing-headings"
set_test "missing-headings exits 1"
assert_captured_exit "1"

run_planner_capture "invalid-reference" "$FIXTURE_ROOT/invalid-reference"
set_test "invalid-reference warning fixture exits 0"
assert_captured_exit "0"

run_planner_capture "invalid-invocation"
set_test "no-argument invocation exits 2"
assert_captured_exit "2"

section "determinism and generated performance input (T003)"

determinism_ok="true"
first_stdout=""
for run in 1 2 3 4 5; do
  run_planner_capture "determinism-$run" "$FIXTURE_ROOT/valid-real"
  if [ "$(cat "$LAST_EXIT_FILE")" != "0" ]; then
    determinism_ok="false"
  fi
  if [ "$run" -eq 1 ]; then
    first_stdout="$LAST_STDOUT"
  elif ! cmp -s "$first_stdout" "$LAST_STDOUT"; then
    determinism_ok="false"
  fi
done

set_test "valid-real emits byte-stable output across five runs"
if [ "$determinism_ok" = "true" ]; then
  _pass
else
  _fail "five runs must all exit 0 and produce identical stdout"
fi

perf_feature="$SANDBOX/generated-200-task"
generate_performance_fixture "$perf_feature"
perf_snapshot_before=$(snapshot_tree "$perf_feature")
run_planner_capture "generated-200-task" "$perf_feature"
elapsed_ms=$(cat "$LAST_ELAPSED_FILE")

set_test "generated 200-task fixture exits 0"
assert_captured_exit "0"

set_test "generated 200-task fixture completes under 1000ms"
if [ "$elapsed_ms" -lt 1000 ]; then
  _pass
else
  _fail "expected under 1000ms, got ${elapsed_ms}ms"
fi

set_test "generated 200-task fixture remains read-only"
perf_snapshot_after=$(snapshot_tree "$perf_feature")
assert_snapshot_unchanged "$perf_snapshot_before" "$perf_snapshot_after"

test_summary
