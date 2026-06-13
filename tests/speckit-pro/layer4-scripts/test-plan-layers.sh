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
FIXTURE_ROOT="$TEST_DIR/fixtures/plan-layers"
SCHEMA="$FIXTURE_ROOT/contracts/plan-layers.schema.json"
MARKER_FIXTURE_ROOT="$TEST_DIR/fixtures/marker-plan"
MARKER_SCHEMA="$REPO_ROOT/speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json"

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

run_marker_planner_capture() {
  local name="$1"
  local feature_dir="$2"
  local reviewability_result="$3"
  local hazard_route="$4"
  local state_file="$5"
  local marker_output="$6"

  LAST_STDOUT="$RUN_DIR/$name.stdout"
  LAST_STDERR="$RUN_DIR/$name.stderr"
  LAST_EXIT_FILE="$RUN_DIR/$name.exit"
  LAST_ELAPSED_FILE="$RUN_DIR/$name.elapsed_ms"

  local start_ns end_ns exit_code
  start_ns=$(monotonic_ns)
  set +e
  bash "$SCRIPT" marker-plan "$feature_dir" "$reviewability_result" "$hazard_route" "$state_file" "$marker_output" >"$LAST_STDOUT" 2>"$LAST_STDERR"
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

assert_marker_schema_contract_file() {
  local schema_file="$1"
  local errors
  errors=$(python3 - "$schema_file" <<'PY' 2>&1 || true
import json
import sys

schema_path = sys.argv[1]
with open(schema_path, "r", encoding="utf-8") as handle:
    schema = json.load(handle)

problems = []
required = set(schema.get("required", []))
expected_required = {
    "schema_version",
    "kind",
    "feature_id",
    "status",
    "source_fingerprint",
    "markers",
    "warnings",
}
if required != expected_required:
    problems.append(f"top-level required mismatch: {sorted(required)!r}")
if schema.get("properties", {}).get("schema_version", {}).get("const") != "pr-marker-plan.v1":
    problems.append("schema_version const mismatch")
if schema.get("properties", {}).get("kind", {}).get("const") != "pr_marker_plan":
    problems.append("kind const mismatch")
status_enum = schema.get("properties", {}).get("status", {}).get("enum", [])
for status in ("planned", "collapsed", "stale", "invalid"):
    if status not in status_enum:
        problems.append(f"missing status {status}")

defs = schema.get("$defs", {})
fingerprint = defs.get("source_fingerprint", {})
fingerprint_required = set(fingerprint.get("required", []))
if fingerprint_required != {
    "feature_spec_sha",
    "plan_declared_scope_sha",
    "tasks_sha",
    "reviewability_sha",
    "hazard_route_sha",
}:
    problems.append(f"fingerprint required mismatch: {sorted(fingerprint_required)!r}")

marker_required = set(defs.get("marker", {}).get("required", []))
for key in (
    "id",
    "review_order",
    "kind",
    "parent_marker_id",
    "source_boundary",
    "task_ids",
    "folded_polish_task_ids",
    "folded_polish_target_reason",
    "declared_files",
    "declared_tests",
    "reviewability",
    "hazards",
    "subdivision",
    "implementation_checkpoint",
    "emission_mapping",
    "warnings",
):
    if key not in marker_required:
        problems.append(f"marker missing required key {key}")

warning_required = set(defs.get("warning", {}).get("required", []))
if warning_required != {"code", "severity", "message", "source", "details"}:
    problems.append("warning object contract mismatch")

if problems:
    print("; ".join(problems))
    sys.exit(1)
PY
)

  if [ -z "$errors" ]; then
    _pass
  else
    _fail "marker schema contract failed: $errors"
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
    schema = json.load(handle)

try:
    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except Exception as exc:
    print(f"invalid JSON: {exc}")
    sys.exit(1)

def resolve_ref(ref):
    current = schema
    for part in ref.removeprefix("#/").split("/"):
        current = current[part]
    return current

def matches_type(value, expected_type):
    if expected_type == "null":
        return value is None
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    return True

def validate_schema(value, node, path="$"):
    local = []
    if "$ref" in node:
        local.extend(validate_schema(value, resolve_ref(node["$ref"]), path))
    if "allOf" in node:
        for index, child in enumerate(node["allOf"]):
            local.extend(validate_schema(value, child, f"{path}.allOf[{index}]"))
    if "oneOf" in node:
        matches = [child for child in node["oneOf"] if not validate_schema(value, child, path)]
        if len(matches) != 1:
            local.append(f"{path}: oneOf matched {len(matches)} schemas")
    if "if" in node and "then" in node and not validate_schema(value, node["if"], path):
        local.extend(validate_schema(value, node["then"], path))
    if "const" in node and value != node["const"]:
        local.append(f"{path}: expected const {node['const']!r}")
    if "enum" in node and value not in node["enum"]:
        local.append(f"{path}: expected one of {node['enum']!r}")
    if "type" in node:
        types = node["type"] if isinstance(node["type"], list) else [node["type"]]
        if not any(matches_type(value, typ) for typ in types):
            local.append(f"{path}: expected type {node['type']!r}")
            return local
    if isinstance(value, dict):
        required_keys = node.get("required", [])
        for key in required_keys:
            if key not in value:
                local.append(f"{path}: missing required key {key}")
        if node.get("additionalProperties") is False and "properties" in node:
            extra = set(value) - set(node["properties"])
            if extra:
                local.append(f"{path}: unexpected keys {sorted(extra)!r}")
        for key, child in node.get("properties", {}).items():
            if key in value:
                local.extend(validate_schema(value[key], child, f"{path}.{key}"))
    if isinstance(value, list):
        if "minItems" in node and len(value) < node["minItems"]:
            local.append(f"{path}: expected at least {node['minItems']} item(s)")
        if "maxItems" in node and len(value) > node["maxItems"]:
            local.append(f"{path}: expected at most {node['maxItems']} item(s)")
        if "items" in node:
            for index, item in enumerate(value):
                local.extend(validate_schema(item, node["items"], f"{path}[{index}]"))
    if isinstance(value, int) and not isinstance(value, bool) and "minimum" in node and value < node["minimum"]:
        local.append(f"{path}: expected >= {node['minimum']}")
    if isinstance(value, str):
        if "minLength" in node and len(value) < node["minLength"]:
            local.append(f"{path}: expected length >= {node['minLength']}")
        if "pattern" in node and re.search(node["pattern"], value) is None:
            local.append(f"{path}: pattern mismatch {node['pattern']!r}")
    return local

problems.extend(validate_schema(data, schema))

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

assert_payload_expectation_file() {
  local json_file="$1"
  local expectation="$2"
  local expected_feature_dir="${3:-}"
  local errors
  errors=$(python3 - "$json_file" "$expectation" "$expected_feature_dir" <<'PY' 2>&1 || true
import json
import pathlib
import sys

json_path = pathlib.Path(sys.argv[1])
expectation = sys.argv[2]
expected_feature_dir = sys.argv[3]
problems = []

try:
    data = json.loads(json_path.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"invalid JSON: {exc}")
    sys.exit(1)

def problem(message):
    problems.append(message)

def require(condition, message):
    if not condition:
        problem(message)

def by_id(items):
    result = {}
    for item in items:
        if isinstance(item, dict) and "id" in item:
            result[item["id"]] = item
    return result

def diagnostic_codes(field):
    return [item.get("code") for item in data.get(field, []) if isinstance(item, dict)]

def diagnostics_by_code(field, code):
    return [item for item in data.get(field, []) if isinstance(item, dict) and item.get("code") == code]

def assert_common(status):
    require(data.get("status") == status, f"status must be {status}")
    if expected_feature_dir:
        require(data.get("feature_dir") == expected_feature_dir, "feature_dir must be repo-relative fixture path")
        require(data.get("tasks_file") == f"{expected_feature_dir}/tasks.md", "tasks_file must be repo-relative tasks.md path")
    summary = data.get("summary", {})
    require(isinstance(summary, dict), "summary must be an object")
    if isinstance(summary, dict):
        require(summary.get("error_count") == len(data.get("errors", [])), "summary.error_count must match errors length")
        require(summary.get("warning_count") == len(data.get("warnings", [])), "summary.warning_count must match warnings length")

def assert_source(source, path, line, heading=None):
    require(isinstance(source, dict), "source must be an object")
    if not isinstance(source, dict):
        return
    require(source.get("path") == path, f"source.path must be {path}")
    require(source.get("line") == line, f"source.line must be {line}")
    if heading is not None:
        require(source.get("heading") == heading, f"source.heading must be {heading}")

def assert_task(task, task_id, line, status, parallel, story, increment_id, files, tests):
    require(isinstance(task, dict), f"{task_id} task must be an object")
    if not isinstance(task, dict):
        return
    require(task.get("id") == task_id, f"{task_id} id mismatch")
    require(task.get("status") == status, f"{task_id} status must be {status}")
    require(task.get("parallel") is parallel, f"{task_id} parallel marker mismatch")
    require(task.get("story") == story, f"{task_id} story must be {story}")
    require(task.get("increment_id") == increment_id, f"{task_id} increment_id must be {increment_id}")
    assert_source(task.get("source"), f"{expected_feature_dir}/tasks.md", line)
    require(task.get("files") == files, f"{task_id} files mismatch: {task.get('files')!r}")
    require(task.get("tests") == tests, f"{task_id} tests mismatch: {task.get('tests')!r}")

def assert_increment(increment, increment_id, name, kind, order, depends_on, line, heading, task_ids, advisory, files, tests):
    require(isinstance(increment, dict), f"{increment_id} increment must be an object")
    if not isinstance(increment, dict):
        return
    require(increment.get("id") == increment_id, f"{increment_id} id mismatch")
    require(isinstance(increment.get("name"), str) and increment.get("name"), f"{increment_id} name must be non-empty")
    require(increment.get("kind") == kind, f"{increment_id} kind mismatch")
    require(increment.get("order") == order, f"{increment_id} order mismatch")
    require(increment.get("depends_on") == depends_on, f"{increment_id} depends_on mismatch")
    assert_source(increment.get("source"), f"{expected_feature_dir}/tasks.md", line, heading)
    tasks = increment.get("tasks")
    require(isinstance(tasks, list), f"{increment_id} tasks must be an array")
    if isinstance(tasks, list):
        require([task.get("id") for task in tasks if isinstance(task, dict)] == task_ids, f"{increment_id} task order mismatch")
    require(increment.get("advisory_size") == advisory, f"{increment_id} advisory_size mismatch")
    require(increment.get("files") == files, f"{increment_id} files mismatch")
    require(increment.get("tests") == tests, f"{increment_id} tests mismatch")

test_file = "tests/speckit-pro/layer4-scripts/test-plan-layers.sh"
script_file = "speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh"
schema_file = "speckit-pro/codex-skills/speckit-autopilot/SKILL.md"
contract_file = "speckit-pro/skills/speckit-autopilot/SKILL.md"
tasks_file = "speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh"

if expectation == "valid-real":
    assert_common("ok")
    require(data.get("warnings") == [], "valid-real warnings must be empty")
    require(data.get("errors") == [], "valid-real errors must be empty")
    increments = data.get("increments", [])
    require([item.get("id") for item in increments if isinstance(item, dict)] == ["foundation", "us1", "us2", "polish"], "increments must be dependency ordered")
    summary = data.get("summary", {})
    require(summary.get("increment_count") == 4, "summary.increment_count must be 4")
    require(summary.get("task_count") == 8, "summary.task_count must be 8")

    inc = by_id(increments)
    assert_increment(
        inc.get("foundation"),
        "foundation",
        "Foundation",
        "foundation",
        0,
        [],
        3,
        "## Phase 1: Foundation",
        ["T001", "T002", "T003"],
        {
            "task_count": 3,
            "file_reference_count": 2,
            "distinct_file_count": 2,
            "test_reference_count": 1,
            "distinct_test_count": 1,
        },
        [schema_file, contract_file],
        [test_file],
    )
    assert_increment(
        inc.get("us1"),
        "us1",
        "User Story 1 - Emit Stable Plan",
        "story",
        1,
        ["foundation"],
        9,
        "## Phase 2: User Story 1 - Emit Stable Plan (Priority: P1)",
        ["T004", "T005"],
        {
            "task_count": 2,
            "file_reference_count": 2,
            "distinct_file_count": 2,
            "test_reference_count": 1,
            "distinct_test_count": 1,
        },
        [schema_file, script_file],
        [test_file],
    )
    assert_increment(
        inc.get("us2"),
        "us2",
        "User Story 2 - Parse Ordered Increments",
        "story",
        2,
        ["us1"],
        14,
        "## Phase 3: User Story 2 - Parse Ordered Increments (Priority: P1)",
        ["T006", "T007"],
        {
            "task_count": 2,
            "file_reference_count": 2,
            "distinct_file_count": 2,
            "test_reference_count": 1,
            "distinct_test_count": 1,
        },
        [contract_file, tasks_file],
        [test_file],
    )
    assert_increment(
        inc.get("polish"),
        "polish",
        "Polish and Validation",
        "polish",
        3,
        ["us2"],
        19,
        "## Phase 4: Polish and Validation",
        ["T008"],
        {
            "task_count": 1,
            "file_reference_count": 1,
            "distinct_file_count": 1,
            "test_reference_count": 1,
            "distinct_test_count": 1,
        },
        [tasks_file],
        [test_file],
    )

    tasks = {}
    for increment in increments:
        for task in increment.get("tasks", []):
            tasks[task.get("id")] = task
    assert_task(tasks.get("T001"), "T001", 5, "todo", False, None, "foundation", [contract_file], [])
    assert_task(tasks.get("T002"), "T002", 6, "todo", True, None, "foundation", [schema_file], [])
    assert_task(tasks.get("T003"), "T003", 7, "done", False, None, "foundation", [], [test_file])
    assert_task(tasks.get("T004"), "T004", 11, "todo", True, "us1", "us1", [script_file], [test_file])
    assert_task(tasks.get("T005"), "T005", 12, "todo", False, "us1", "us1", [schema_file], [])
    assert_task(tasks.get("T006"), "T006", 16, "todo", True, "us2", "us2", [tasks_file], [test_file])
    assert_task(tasks.get("T007"), "T007", 17, "todo", False, "us2", "us2", [contract_file], [])
    assert_task(tasks.get("T008"), "T008", 21, "todo", False, None, "polish", [tasks_file], [test_file])

elif expectation == "checkbox-state":
    assert_common("ok")
    increments = data.get("increments", [])
    tasks = {}
    for increment in increments:
        for task in increment.get("tasks", []):
            tasks[task.get("id")] = task
    assert_task(tasks.get("T001"), "T001", 5, "todo", False, None, "foundation", [schema_file], [])
    assert_task(tasks.get("T002"), "T002", 6, "done", False, None, "foundation", [contract_file], [])
    assert_task(tasks.get("T003"), "T003", 7, "done", False, None, "foundation", [], [test_file])
    assert_task(tasks.get("T004"), "T004", 11, "todo", True, "us1", "us1", [script_file], [])

elif expectation == "invalid-reference":
    assert_common("ok")
    require(data.get("errors") == [], "warning fixture must not emit errors")
    codes = diagnostic_codes("warnings")
    require(codes.count("reference_not_found") == 2, "invalid-reference must emit two reference_not_found warnings")
    details = [item.get("details", {}) for item in diagnostics_by_code("warnings", "reference_not_found")]
    require({"kind": "file", "reference": "speckit-pro/skills/speckit-autopilot/scripts/no-such-plan-layers-helper.sh", "task_id": "T002"} in details, "missing file warning details mismatch")
    require({"kind": "test", "reference": "tests/speckit-pro/layer4-scripts/no-such-plan-layers-test.sh", "task_id": "T003"} in details, "missing test warning details mismatch")

elif expectation == "missing-references":
    assert_common("ok")
    require(data.get("errors") == [], "missing-reference warning fixture must not emit errors")
    warnings = diagnostics_by_code("warnings", "task_without_references")
    require(len(warnings) == 2, "missing-references must warn for both reference-free tasks")
    details = [item.get("details", {}) for item in warnings]
    require({"task_id": "T001", "increment_id": "foundation"} in details, "T001 task_without_references details mismatch")
    require({"task_id": "T002", "increment_id": "us1"} in details, "T002 task_without_references details mismatch")

elif expectation == "path-normalization":
    assert_common("ok")
    increments = by_id(data.get("increments", []))
    foundation = increments.get("foundation", {})
    us1 = increments.get("us1", {})
    require(foundation.get("files") == [contract_file], "foundation files must normalize and de-duplicate leading-dot references")
    require(foundation.get("tests") == [], "foundation tests must remain empty")
    require(us1.get("files") == [], "out-of-tree reference must not be emitted as a repo file")
    require(us1.get("tests") == [test_file], "US1 test paths must normalize without leading ./")
    tasks = {}
    for increment in data.get("increments", []):
        for task in increment.get("tasks", []):
            tasks[task.get("id")] = task
    assert_task(tasks.get("T001"), "T001", 5, "todo", False, None, "foundation", [contract_file], [])
    assert_task(tasks.get("T002"), "T002", 6, "todo", False, None, "foundation", [contract_file], [])
    assert_task(tasks.get("T003"), "T003", 10, "todo", False, "us1", "us1", [], [test_file])
    assert_task(tasks.get("T004"), "T004", 11, "todo", False, "us1", "us1", [], [])
    warnings = data.get("warnings", [])
    reference_details = [item.get("details", {}) for item in warnings if item.get("code") == "reference_not_found"]
    taskless_details = [item.get("details", {}) for item in warnings if item.get("code") == "task_without_references"]
    require({"kind": "file", "reference": "../outside-worktree-plan.md", "task_id": "T004"} in reference_details, "out-of-tree warning details mismatch")
    require({"task_id": "T004", "increment_id": "us1"} in taskless_details, "out-of-tree-only task should warn as reference-free")

else:
    problem(f"unknown expectation: {expectation}")

if problems:
    print("; ".join(problems))
    sys.exit(1)
PY
)

  if [ -z "$errors" ]; then
    _pass
  else
    _fail "$expectation payload assertion failed: $errors"
  fi
}

assert_marker_result_and_plan_file() {
  local stdout_file="$1"
  local plan_file="$2"
  local scenario="$3"
  local feature_dir="$4"
  local reviewability_file="$5"
  local hazard_file="$6"
  local expected_output_path="$7"
  local errors
  errors=$(python3 - "$stdout_file" "$plan_file" "$scenario" "$REPO_ROOT" "$feature_dir" "$reviewability_file" "$hazard_file" "$expected_output_path" <<'PY' 2>&1 || true
import hashlib
import json
import pathlib
import re
import sys

stdout_path = pathlib.Path(sys.argv[1])
plan_path = pathlib.Path(sys.argv[2])
scenario = sys.argv[3]
repo_root = pathlib.Path(sys.argv[4])
feature_dir = pathlib.Path(sys.argv[5])
reviewability_file = pathlib.Path(sys.argv[6])
hazard_file = pathlib.Path(sys.argv[7])
expected_output_path = sys.argv[8]
problems = []

def problem(message):
    problems.append(message)

def require(condition, message):
    if not condition:
        problems.append(message)

def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rel(path):
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path)

def by_id(items):
    return {item.get("id"): item for item in items if isinstance(item, dict)}

try:
    result = load(stdout_path)
except Exception as exc:
    print(f"invalid stdout JSON: {exc}")
    sys.exit(1)
try:
    plan = load(plan_path)
except Exception as exc:
    print(f"invalid marker plan JSON: {exc}")
    sys.exit(1)

require(result.get("tool") == "plan-layers", "result tool mismatch")
require(result.get("contract_version") == 2, "marker mode must use contract_version 2")
require(result.get("mode") == "marker-plan", "result mode must be marker-plan")
require(result.get("status") == "ok", "result status must be ok")
require(result.get("feature_dir") == rel(feature_dir), "result feature_dir mismatch")
require(result.get("marker_plan_file") == expected_output_path, "result marker_plan_file mismatch")
require(result.get("errors") == [], "ok result errors must be empty")

require(plan.get("schema_version") == "pr-marker-plan.v1", "plan schema_version mismatch")
require(plan.get("kind") == "pr_marker_plan", "plan kind mismatch")
require(plan.get("feature_id") == feature_dir.name, "plan feature_id must use feature directory basename")
require(isinstance(plan.get("warnings"), list), "plan warnings must be an array")
require(result.get("marker_ids") == [marker.get("id") for marker in plan.get("markers", [])], "result marker_ids must mirror plan order")

fingerprint = plan.get("source_fingerprint", {})
expected_fingerprint = {
    "feature_spec_sha": sha(feature_dir / "spec.md"),
    "plan_declared_scope_sha": sha(feature_dir / "plan.md"),
    "tasks_sha": sha(feature_dir / "tasks.md"),
    "reviewability_sha": sha(reviewability_file),
    "hazard_route_sha": sha(hazard_file),
}
require(fingerprint == expected_fingerprint, "source_fingerprint must match current spec/plan/tasks/reviewability/hazard inputs")
for key, value in fingerprint.items():
    require(re.fullmatch(r"[0-9a-f]{64}", value or "") is not None, f"{key} must be sha256 hex")

markers = plan.get("markers", [])
ids = [marker.get("id") for marker in markers if isinstance(marker, dict)]
orders = [marker.get("review_order") for marker in markers if isinstance(marker, dict)]
require(orders == list(range(1, len(markers) + 1)), "review_order must be one-based and match marker array order")
for marker in markers:
    require(marker.get("implementation_checkpoint", {}).get("status") == "pending", f"{marker.get('id')} checkpoint must start pending")
    require(marker.get("emission_mapping", {}).get("status") in {"pending", "hazard_collapsed"}, f"{marker.get('id')} emission status mismatch")
    require(marker.get("reviewability", {}).get("mode") == "tasks", f"{marker.get('id')} reviewability mode mismatch")

marker_map = by_id(markers)

if scenario == "canonical":
    require(plan.get("status") == "planned", "canonical status must be planned")
    require(ids == ["foundation", "us1", "us2"], f"canonical marker order mismatch: {ids!r}")
    require("polish" not in ids, "polish must not create a cleanup-only marker")
    require(marker_map["foundation"].get("task_ids") == ["T001", "T002"], "foundation task_ids mismatch")
    require(marker_map["us1"].get("task_ids") == ["T003", "T004"], "us1 task_ids mismatch")
    require(marker_map["us2"].get("task_ids") == ["T005", "T006"], "us2 task_ids mismatch")
    require(marker_map["us2"].get("folded_polish_task_ids") == ["T007"], "polish task must fold into last non-polish marker")
    require(marker_map["us2"].get("folded_polish_target_reason") == "nearest_preceding_non_polish_scope", "polish fold reason mismatch")
    require(marker_map["us2"].get("declared_tests") == ["tests/speckit-pro/layer4-scripts/test-plan-layers.sh"], "folded polish test must join us2 declared tests")
    warning_codes = [item.get("code") for item in plan.get("warnings", [])]
    require("reviewability_size_warning" in warning_codes, "warn reviewability result must become structured plan warning")
    require(result.get("summary", {}).get("hazard_collapsed") is False, "canonical must not hazard-collapse")

elif scenario == "safe-subdivision":
    require(plan.get("status") == "planned", "safe-subdivision status must be planned")
    require(ids == ["foundation", "us1-part1", "us1-part2"], f"safe subdivision marker order mismatch: {ids!r}")
    require("us1" not in ids, "subdivided parent us1 must not emit as a separate marker")
    require(marker_map["us1-part1"].get("parent_marker_id") == "us1", "part1 parent mismatch")
    require(marker_map["us1-part2"].get("parent_marker_id") == "us1", "part2 parent mismatch")
    require(marker_map["us1-part1"].get("kind") == "user_story_part", "part1 kind mismatch")
    require(marker_map["us1-part2"].get("kind") == "user_story_part", "part2 kind mismatch")
    require(marker_map["us1-part1"].get("task_ids") == ["T002", "T003"], "part1 task ids mismatch")
    require(marker_map["us1-part2"].get("task_ids") == ["T004", "T005"], "part2 task ids mismatch")
    for marker_id in ("us1-part1", "us1-part2"):
        require(marker_map[marker_id].get("subdivision", {}).get("status") == "safe_split", f"{marker_id} subdivision status mismatch")
    warning_codes = [item.get("code") for item in plan.get("warnings", [])]
    require("reviewability_size_warning" in warning_codes, "safe split must preserve reviewability size warning")

elif scenario == "no-safe-boundary":
    require(plan.get("status") == "planned", "no-safe-boundary status must remain planned")
    require(ids == ["foundation", "us1"], f"no-safe marker order mismatch: {ids!r}")
    us1 = marker_map["us1"]
    require(us1.get("subdivision", {}).get("status") == "no_safe_boundary", "us1 subdivision must be no_safe_boundary")
    marker_warning_codes = [item.get("code") for item in us1.get("warnings", [])]
    require("no_safe_boundary" in marker_warning_codes, "us1 must carry no_safe_boundary marker warning")
    plan_warning_codes = [item.get("code") for item in plan.get("warnings", [])]
    require("no_safe_boundary" in plan_warning_codes, "plan must carry no_safe_boundary warning")

elif scenario == "hazard-collapse":
    require(plan.get("status") == "collapsed", "hazard-collapse plan status must be collapsed")
    require(ids == ["foundation", "us1", "us2"], f"hazard collapse must preserve original marker order: {ids!r}")
    require("full-spec" not in ids, "planning must preserve original markers instead of inventing full-spec")
    require(result.get("summary", {}).get("hazard_collapsed") is True, "stdout summary must report hazard collapse")
    plan_warning_codes = [item.get("code") for item in plan.get("warnings", [])]
    require("hazard_collapse_required" in plan_warning_codes, "hazard collapse warning missing")
    for marker in markers:
        require(marker.get("emission_mapping", {}).get("status") == "hazard_collapsed", f"{marker.get('id')} emission must be hazard_collapsed")
        require(marker.get("emission_mapping", {}).get("source_marker_ids") == ids, f"{marker.get('id')} source_marker_ids mismatch")

else:
    problem(f"unknown scenario: {scenario}")

if problems:
    print("; ".join(problems))
    sys.exit(1)
PY
)

  if [ -z "$errors" ]; then
    _pass
  else
    _fail "$scenario marker plan assertion failed: $errors"
  fi
}

assert_marker_error_result_file() {
  local stdout_file="$1"
  local expected_status="$2"
  local expected_code="$3"
  local output_file="$4"
  local errors
  errors=$(python3 - "$stdout_file" "$expected_status" "$expected_code" <<'PY' 2>&1 || true
import json
import sys

stdout_path, expected_status, expected_code = sys.argv[1:4]
problems = []

try:
    with open(stdout_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except Exception as exc:
    print(f"invalid stdout JSON: {exc}")
    sys.exit(1)

if data.get("tool") != "plan-layers":
    problems.append("tool mismatch")
if data.get("contract_version") != 2:
    problems.append("contract_version mismatch")
if data.get("mode") != "marker-plan":
    problems.append("mode mismatch")
if data.get("status") != expected_status:
    problems.append(f"status must be {expected_status}, got {data.get('status')!r}")
if data.get("marker_ids") != []:
    problems.append("error result marker_ids must be empty")
codes = [item.get("code") for item in data.get("errors", []) if isinstance(item, dict)]
if expected_code not in codes:
    problems.append(f"missing expected code {expected_code}; got {codes!r}")
summary = data.get("summary", {})
if not isinstance(summary, dict) or summary.get("error_count") != len(data.get("errors", [])):
    problems.append("summary error_count mismatch")

if problems:
    print("; ".join(problems))
    sys.exit(1)
PY
)

  if [ -z "$errors" ]; then
    _pass
  else
    _fail "marker error assertion failed: $errors"
  fi

  assert_file_not_exists "$output_file" "marker error path must not write a candidate plan"
}

assert_error_payload_file() {
  local json_file="$1"
  local expected_status="$2"
  local expected_codes_csv="$3"
  local expected_feature_dir="${4:-}"
  local errors
  errors=$(python3 - "$json_file" "$expected_status" "$expected_codes_csv" "$expected_feature_dir" <<'PY' 2>&1 || true
import json
import sys

json_path, expected_status, expected_codes_csv, expected_feature_dir = sys.argv[1:5]
expected_codes = [code for code in expected_codes_csv.split(",") if code]
problems = []

try:
    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except Exception as exc:
    print(f"invalid JSON: {exc}")
    sys.exit(1)

if data.get("status") != expected_status:
    problems.append(f"status must be {expected_status}, got {data.get('status')!r}")

if expected_feature_dir:
    if data.get("feature_dir") != expected_feature_dir:
        problems.append("feature_dir mismatch")
    if data.get("tasks_file") != f"{expected_feature_dir}/tasks.md":
        problems.append("tasks_file mismatch")

if expected_status == "input_error" and data.get("increments") != []:
    problems.append("input_error increments must be empty")

field = "errors"
actual_codes = [item.get("code") for item in data.get(field, []) if isinstance(item, dict)]
for expected_code in expected_codes:
    if expected_code not in actual_codes:
        problems.append(f"missing diagnostic code {expected_code}")

summary = data.get("summary", {})
if not isinstance(summary, dict):
    problems.append("summary must be an object")
else:
    if summary.get("error_count") != len(data.get("errors", [])):
        problems.append("summary.error_count must match errors length")
    if summary.get("warning_count") != len(data.get("warnings", [])):
        problems.append("summary.warning_count must match warnings length")

for diagnostic in data.get("errors", []):
    if not isinstance(diagnostic, dict):
        problems.append("error diagnostic must be an object")
        continue
    if diagnostic.get("severity") != "error":
        problems.append(f"{diagnostic.get('code')} severity must be error")
    source = diagnostic.get("source", {})
    if not isinstance(source, dict) or "path" not in source or "line" not in source:
        problems.append(f"{diagnostic.get('code')} source must include path and line")
    details = diagnostic.get("details")
    if not isinstance(details, dict) or not details:
        problems.append(f"{diagnostic.get('code')} details must be non-empty")

if expected_status == "invalid_plan":
    checks = {
        "missing_required_heading": lambda d: "required_heading" in d,
        "empty_increment": lambda d: d.get("increment_id") in {"foundation", "polish"} or str(d.get("increment_id", "")).startswith("us"),
        "unknown_increment": lambda d: d.get("increment_id") == "us3",
        "dependency_cycle": lambda d: isinstance(d.get("cycle"), list) and len(d.get("cycle")) >= 4 and d.get("cycle", [None])[0] == d.get("cycle", [None])[-1],
        "contradictory_increment_order": lambda d: set(d) == {"expected_order", "observed_order"} and d.get("expected_order") != d.get("observed_order"),
        "duplicate_increment_id": lambda d: {"increment_id", "first_source", "duplicate_source"} <= set(d),
        "duplicate_task_id": lambda d: {"task_id", "first_source", "duplicate_source"} <= set(d),
        "malformed_task": lambda d: "line_text" in d,
    }
elif expected_status == "input_error":
    checks = {
        "invalid_invocation": lambda d: set(d) == {"expected_args", "received_args"},
        "feature_dir_not_found": lambda d: "feature_dir" in d,
        "feature_dir_unreadable": lambda d: "feature_dir" in d,
        "tasks_file_missing": lambda d: "tasks_file" in d,
        "tasks_file_unreadable": lambda d: "tasks_file" in d,
    }
else:
    checks = {}

for expected_code in expected_codes:
    diagnostics = [item for item in data.get("errors", []) if isinstance(item, dict) and item.get("code") == expected_code]
    if not diagnostics:
        continue
    if expected_code in checks and not any(checks[expected_code](item.get("details", {})) for item in diagnostics):
        problems.append(f"{expected_code} details mismatch")

if problems:
    print("; ".join(problems))
    sys.exit(1)
PY
)

  if [ -z "$errors" ]; then
    _pass
  else
    _fail "$expected_status payload assertion failed: $errors"
  fi
}

assert_stderr_concise_file() {
  local stderr_file="$1"
  local max_lines="${2:-3}"
  local max_bytes="${3:-500}"
  local line_count byte_count stderr_text
  line_count=$(wc -l <"$stderr_file")
  byte_count=$(wc -c <"$stderr_file")
  stderr_text=$(cat "$stderr_file")
  if [ "$line_count" -ge 1 ] &&
    [ "$line_count" -le "$max_lines" ] &&
    [ "$byte_count" -le "$max_bytes" ] &&
    [[ "$stderr_text" != *"Traceback"* ]]; then
    _pass
  else
    _fail "stderr must be 1-${max_lines} lines, <=${max_bytes} bytes, and free of stack traces"
  fi
}

assert_script_safety_file() {
  local script_file="$1"
  local errors
  errors=$(python3 - "$script_file" <<'PY' 2>&1 || true
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
problems = []

if not path.exists():
    print(f"script not found: {path}")
    sys.exit(1)

text = path.read_text(encoding="utf-8")
lines = text.splitlines()

if not lines or lines[0] != "#!/usr/bin/env bash":
    problems.append("script must start with #!/usr/bin/env bash")
if "set -euo pipefail" not in text:
    problems.append("script must enable set -euo pipefail")

for line_no, line in enumerate(lines, start=1):
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        continue
    if re.search(r"\bgit\s+(add|branch|checkout|commit|merge|mv|push|rebase|reset|restore|stash|switch|tag)\b", stripped):
        problems.append(f"line {line_no} uses a repository-mutating git command")
    if re.search(r"\bgh\s+pr\s+(create|edit|merge|ready|review)\b", stripped):
        problems.append(f"line {line_no} uses PR mutation")

if problems:
    print("; ".join(problems))
    sys.exit(1)
PY
)

  if [ -z "$errors" ]; then
    _pass
  else
    _fail "script safety assertion failed: $errors"
  fi
}

assert_bash_syntax_file() {
  local script_file="$1"
  if [ -f "$script_file" ] && bash -n "$script_file" >/dev/null 2>&1; then
    _pass
  else
    _fail "script must pass bash -n"
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
      printf -- '- [ ] T%03d Prepare generated foundation file speckit-pro/skills/speckit-autopilot/SKILL.md and test tests/speckit-pro/layer4-scripts/test-plan-layers.sh\n' "$index"
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

section "marker-plan schema and marker-aware mode (PRSG-013 T002-T008, T016-T026)"

set_test "PR marker plan schema JSON is well formed"
if python3 -m json.tool "$MARKER_SCHEMA" >/dev/null 2>&1; then
  _pass
else
  _fail "pr-marker-plan.schema.json must parse as JSON"
fi

set_test "PR marker plan schema declares durable marker invariants"
assert_marker_schema_contract_file "$MARKER_SCHEMA"

canonical_feature="$MARKER_FIXTURE_ROOT/canonical"
canonical_reviewability="$canonical_feature/reviewability-result.json"
canonical_hazard="$canonical_feature/hazard-route.json"
canonical_state="$canonical_feature/state.json"
canonical_output="$RUN_DIR/canonical-pr-marker-plan.json"
canonical_snapshot_before=$(snapshot_tree "$MARKER_FIXTURE_ROOT")
canonical_state_before=$(python3 -m json.tool "$canonical_state")
run_marker_planner_capture "marker-canonical" "$canonical_feature" "$canonical_reviewability" "$canonical_hazard" "$canonical_state" "$canonical_output"

set_test "marker-aware canonical fixture exits 0"
assert_captured_exit "0"

set_test "marker-aware canonical stdout is valid JSON"
assert_valid_json_file "$LAST_STDOUT"

set_test "marker-aware canonical writes candidate marker plan only at requested output path"
assert_file_exists "$canonical_output" "canonical marker plan output"

set_test "marker-aware canonical derives Foundation/user-story markers and folds Polish"
assert_marker_result_and_plan_file "$LAST_STDOUT" "$canonical_output" "canonical" "$canonical_feature" "$canonical_reviewability" "$canonical_hazard" "$canonical_output"

set_test "marker-aware canonical leaves fixtures and current state read-only"
canonical_snapshot_after=$(snapshot_tree "$MARKER_FIXTURE_ROOT")
canonical_state_after=$(python3 -m json.tool "$canonical_state")
if [ "$canonical_snapshot_before" = "$canonical_snapshot_after" ] && [ "$canonical_state_before" = "$canonical_state_after" ]; then
  _pass
else
  _fail "marker planning must not mutate fixture inputs or current state"
fi

safe_feature="$MARKER_FIXTURE_ROOT/safe-subdivision"
safe_reviewability="$safe_feature/reviewability-result.json"
safe_hazard="$safe_feature/hazard-route.json"
safe_state="$safe_feature/state.json"
safe_output="$RUN_DIR/safe-subdivision-pr-marker-plan.json"
run_marker_planner_capture "marker-safe-subdivision" "$safe_feature" "$safe_reviewability" "$safe_hazard" "$safe_state" "$safe_output"

set_test "marker-aware safe-subdivision fixture exits 0"
assert_captured_exit "0"

set_test "marker-aware safe-subdivision creates ordered user-story part markers"
assert_marker_result_and_plan_file "$LAST_STDOUT" "$safe_output" "safe-subdivision" "$safe_feature" "$safe_reviewability" "$safe_hazard" "$safe_output"

no_safe_feature="$MARKER_FIXTURE_ROOT/no-safe-boundary"
no_safe_reviewability="$no_safe_feature/reviewability-result.json"
no_safe_hazard="$no_safe_feature/hazard-route.json"
no_safe_state="$no_safe_feature/state.json"
no_safe_output="$RUN_DIR/no-safe-boundary-pr-marker-plan.json"
run_marker_planner_capture "marker-no-safe-boundary" "$no_safe_feature" "$no_safe_reviewability" "$no_safe_hazard" "$no_safe_state" "$no_safe_output"

set_test "marker-aware no-safe-boundary fixture exits 0"
assert_captured_exit "0"

set_test "marker-aware no-safe-boundary keeps story marker with structured warning"
assert_marker_result_and_plan_file "$LAST_STDOUT" "$no_safe_output" "no-safe-boundary" "$no_safe_feature" "$no_safe_reviewability" "$no_safe_hazard" "$no_safe_output"

hazard_feature="$MARKER_FIXTURE_ROOT/hazard-collapse"
hazard_reviewability="$hazard_feature/reviewability-result.json"
hazard_route="$hazard_feature/hazard-route.json"
hazard_state="$hazard_feature/state.json"
hazard_output="$RUN_DIR/hazard-collapse-pr-marker-plan.json"
run_marker_planner_capture "marker-hazard-collapse" "$hazard_feature" "$hazard_reviewability" "$hazard_route" "$hazard_state" "$hazard_output"

set_test "marker-aware hazard-collapse fixture exits 0"
assert_captured_exit "0"

set_test "marker-aware hazard-collapse preserves source markers with collapsed emission warning"
assert_marker_result_and_plan_file "$LAST_STDOUT" "$hazard_output" "hazard-collapse" "$hazard_feature" "$hazard_reviewability" "$hazard_route" "$hazard_output"

malformed_output="$RUN_DIR/malformed-reviewability-pr-marker-plan.json"
run_marker_planner_capture "marker-malformed-reviewability" "$canonical_feature" "$MARKER_FIXTURE_ROOT/malformed-reviewability/reviewability-result.json" "$canonical_hazard" "$canonical_state" "$malformed_output"

set_test "marker-aware malformed reviewability evidence exits 1"
assert_captured_exit "1"

set_test "marker-aware malformed reviewability evidence is a correctness stop"
assert_marker_error_result_file "$LAST_STDOUT" "invalid_plan" "malformed_reviewability_result" "$malformed_output"

stale_output="$RUN_DIR/stale-state-pr-marker-plan.json"
run_marker_planner_capture "marker-stale-state" "$canonical_feature" "$canonical_reviewability" "$canonical_hazard" "$MARKER_FIXTURE_ROOT/stale-state/state.json" "$stale_output"

set_test "marker-aware stale marker fingerprint exits 1"
assert_captured_exit "1"

set_test "marker-aware stale marker fingerprint is rejected before writing a candidate"
assert_marker_error_result_file "$LAST_STDOUT" "invalid_plan" "stale_marker_fingerprint" "$stale_output"

section "valid fixture capture, schema, and read-only checks (T003-T004)"

valid_snapshot_before=$(snapshot_tree "$FIXTURE_ROOT/valid-real")
run_planner_capture "valid-real" "$FIXTURE_ROOT/valid-real"

set_test "valid-real exits 0"
assert_captured_exit "0"

set_test "valid-real stdout is valid JSON"
assert_valid_json_file "$LAST_STDOUT"

set_test "valid-real stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

set_test "valid-real payload preserves ordered increments and advisory counts"
assert_payload_expectation_file "$LAST_STDOUT" "valid-real" "tests/speckit-pro/layer4-scripts/fixtures/plan-layers/valid-real"

set_test "valid-real stderr capture exists"
assert_file_exists "$LAST_STDERR" "stderr capture"

set_test "valid-real fixture remains read-only"
valid_snapshot_after=$(snapshot_tree "$FIXTURE_ROOT/valid-real")
assert_snapshot_unchanged "$valid_snapshot_before" "$valid_snapshot_after"

section "checkbox status and parallel metadata (T014)"

run_planner_capture "checkbox-state" "$FIXTURE_ROOT/checkbox-state"

set_test "checkbox-state exits 0"
assert_captured_exit "0"

set_test "checkbox-state stdout is valid JSON"
assert_valid_json_file "$LAST_STDOUT"

set_test "checkbox-state stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

set_test "checkbox-state preserves todo, done, [X], and [P] metadata"
assert_payload_expectation_file "$LAST_STDOUT" "checkbox-state" "tests/speckit-pro/layer4-scripts/fixtures/plan-layers/checkbox-state"

section "invalid-plan diagnostics (T016)"

run_planner_capture "missing-headings" "$FIXTURE_ROOT/missing-headings"
set_test "missing-headings exits 1"
assert_captured_exit "1"

set_test "missing-headings stdout is structured invalid_plan JSON"
assert_valid_json_file "$LAST_STDOUT"

set_test "missing-headings stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

set_test "missing-headings reports missing_required_heading"
assert_error_payload_file "$LAST_STDOUT" "invalid_plan" "missing_required_heading" "tests/speckit-pro/layer4-scripts/fixtures/plan-layers/missing-headings"

run_planner_capture "invalid-dependency" "$FIXTURE_ROOT/invalid-dependency"
set_test "invalid-dependency exits 1"
assert_captured_exit "1"

set_test "invalid-dependency stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

set_test "invalid-dependency reports unknown_increment and contradictory order"
assert_error_payload_file "$LAST_STDOUT" "invalid_plan" "unknown_increment,contradictory_increment_order" "tests/speckit-pro/layer4-scripts/fixtures/plan-layers/invalid-dependency"

run_planner_capture "dependency-cycle" "$FIXTURE_ROOT/dependency-cycle"
set_test "dependency-cycle exits 1"
assert_captured_exit "1"

set_test "dependency-cycle stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

set_test "dependency-cycle reports dependency_cycle details"
assert_error_payload_file "$LAST_STDOUT" "invalid_plan" "dependency_cycle" "tests/speckit-pro/layer4-scripts/fixtures/plan-layers/dependency-cycle"

run_planner_capture "empty-increment" "$FIXTURE_ROOT/empty-increment"
set_test "empty-increment exits 1"
assert_captured_exit "1"

set_test "empty-increment stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

set_test "empty-increment reports empty_increment details"
assert_error_payload_file "$LAST_STDOUT" "invalid_plan" "empty_increment" "tests/speckit-pro/layer4-scripts/fixtures/plan-layers/empty-increment"

run_planner_capture "malformed-task" "$FIXTURE_ROOT/malformed-task"
set_test "malformed-task exits 1"
assert_captured_exit "1"

set_test "malformed-task stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

set_test "malformed-task reports duplicate IDs and malformed task"
assert_error_payload_file "$LAST_STDOUT" "invalid_plan" "duplicate_task_id,duplicate_increment_id,malformed_task" "tests/speckit-pro/layer4-scripts/fixtures/plan-layers/malformed-task"

section "warning diagnostics (T017)"

run_planner_capture "invalid-reference" "$FIXTURE_ROOT/invalid-reference"
set_test "invalid-reference warning fixture exits 0"
assert_captured_exit "0"

set_test "invalid-reference stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

set_test "invalid-reference warning fixture remains status ok"
assert_payload_expectation_file "$LAST_STDOUT" "invalid-reference" "tests/speckit-pro/layer4-scripts/fixtures/plan-layers/invalid-reference"

run_planner_capture "missing-references" "$FIXTURE_ROOT/missing-references"
set_test "missing-references warning fixture exits 0"
assert_captured_exit "0"

set_test "missing-references stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

set_test "missing-references warning fixture remains status ok"
assert_payload_expectation_file "$LAST_STDOUT" "missing-references" "tests/speckit-pro/layer4-scripts/fixtures/plan-layers/missing-references"

run_planner_capture "path-normalization" "$FIXTURE_ROOT/path-normalization"
set_test "path-normalization warning fixture exits 0"
assert_captured_exit "0"

set_test "path-normalization stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

set_test "path-normalization normalizes, deduplicates, and warns for out-of-tree references"
assert_payload_expectation_file "$LAST_STDOUT" "path-normalization" "tests/speckit-pro/layer4-scripts/fixtures/plan-layers/path-normalization"

section "input errors (T018)"

run_planner_capture "invalid-invocation"
set_test "no-argument invocation exits 2"
assert_captured_exit "2"

set_test "no-argument invocation emits structured input_error JSON"
assert_error_payload_file "$LAST_STDOUT" "input_error" "invalid_invocation"

set_test "no-argument invocation stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

set_test "no-argument invocation emits concise stderr"
assert_stderr_concise_file "$LAST_STDERR"

run_planner_capture "too-many-arguments" "$FIXTURE_ROOT/valid-real" "$FIXTURE_ROOT/checkbox-state"
set_test "too-many-arguments exits 2"
assert_captured_exit "2"

set_test "too-many-arguments emits structured input_error JSON"
assert_error_payload_file "$LAST_STDOUT" "input_error" "invalid_invocation"

set_test "too-many-arguments stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

missing_feature="$SANDBOX/no-such-feature"
run_planner_capture "missing-feature-dir" "$missing_feature"
set_test "missing feature directory exits 2"
assert_captured_exit "2"

set_test "missing feature directory emits feature_dir_not_found"
assert_error_payload_file "$LAST_STDOUT" "input_error" "feature_dir_not_found"

set_test "missing feature directory stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

unreadable_feature="$SANDBOX/unreadable-feature"
mkdir -p "$unreadable_feature"
chmod 000 "$unreadable_feature"
run_planner_capture "unreadable-feature-dir" "$unreadable_feature"
chmod 700 "$unreadable_feature"
set_test "unreadable feature directory exits 2"
assert_captured_exit "2"

set_test "unreadable feature directory emits feature_dir_unreadable"
assert_error_payload_file "$LAST_STDOUT" "input_error" "feature_dir_unreadable"

set_test "unreadable feature directory stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

missing_tasks_feature="$SANDBOX/missing-tasks-feature"
mkdir -p "$missing_tasks_feature"
run_planner_capture "missing-tasks-file" "$missing_tasks_feature"
set_test "missing tasks.md exits 2"
assert_captured_exit "2"

set_test "missing tasks.md emits tasks_file_missing"
assert_error_payload_file "$LAST_STDOUT" "input_error" "tasks_file_missing"

set_test "missing tasks.md stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

unreadable_tasks_feature="$SANDBOX/unreadable-tasks-feature"
mkdir -p "$unreadable_tasks_feature"
printf '# Tasks: unreadable\n' >"$unreadable_tasks_feature/tasks.md"
chmod 000 "$unreadable_tasks_feature/tasks.md"
run_planner_capture "unreadable-tasks-file" "$unreadable_tasks_feature"
chmod 600 "$unreadable_tasks_feature/tasks.md"
set_test "unreadable tasks.md exits 2"
assert_captured_exit "2"

set_test "unreadable tasks.md emits tasks_file_unreadable"
assert_error_payload_file "$LAST_STDOUT" "input_error" "tasks_file_unreadable"

set_test "unreadable tasks.md stdout conforms to planner envelope schema"
assert_plan_schema_file "$LAST_STDOUT"

section "script safety (T019)"

set_test "Planner script is executable"
assert_file_executable "$SCRIPT" "plan-layers.sh"

set_test "Planner script passes bash syntax validation"
assert_bash_syntax_file "$SCRIPT"

set_test "Planner script uses safe Bash entrypoint conventions"
assert_script_safety_file "$SCRIPT"

section "determinism and generated performance input (T015)"

determinism_ok="true"
first_stdout=""
determinism_snapshot_before=$(snapshot_tree "$FIXTURE_ROOT/valid-real")
for run in 1 2 3 4 5; do
  run_planner_capture "determinism-$run" "$FIXTURE_ROOT/valid-real"
  if [ "$(cat "$LAST_EXIT_FILE")" != "0" ]; then
    determinism_ok="false"
  fi
  if ! python3 -m json.tool "$LAST_STDOUT" >/dev/null 2>&1; then
    determinism_ok="false"
  elif ! python3 - "$LAST_STDOUT" <<'PY' >/dev/null 2>&1
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
assert data["status"] == "ok"
assert data["summary"]["task_count"] == 8
PY
  then
    determinism_ok="false"
  fi
  if [ "$run" -eq 1 ]; then
    first_stdout="$LAST_STDOUT"
  elif ! cmp -s "$first_stdout" "$LAST_STDOUT"; then
    determinism_ok="false"
  fi
done
determinism_snapshot_after=$(snapshot_tree "$FIXTURE_ROOT/valid-real")

set_test "valid-real emits byte-stable output across five runs"
if [ "$determinism_ok" = "true" ]; then
  _pass
else
  _fail "five runs must all exit 0 and produce identical stdout"
fi

set_test "valid-real remains read-only across five repeated runs"
assert_snapshot_unchanged "$determinism_snapshot_before" "$determinism_snapshot_after"

perf_feature="$SANDBOX/generated-200-task"
generate_performance_fixture "$perf_feature"
perf_snapshot_before=$(snapshot_tree "$perf_feature")
run_planner_capture "generated-200-task" "$perf_feature"
elapsed_ms=$(cat "$LAST_ELAPSED_FILE")

set_test "generated 200-task fixture exits 0"
assert_captured_exit "0"

set_test "generated 200-task stdout is valid status ok JSON"
if python3 - "$LAST_STDOUT" <<'PY' >/dev/null 2>&1
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
assert data["status"] == "ok"
assert data["summary"]["task_count"] == 200
PY
then
  _pass
else
  _fail "generated 200-task output must be status ok with 200 tasks"
fi

max_perf_ms="${PLAN_LAYERS_PERF_BUDGET_MS:-2000}"
set_test "generated 200-task fixture completes under ${max_perf_ms}ms"
if [ "$elapsed_ms" -lt "$max_perf_ms" ]; then
  _pass
else
  _fail "expected under ${max_perf_ms}ms, got ${elapsed_ms}ms"
fi

set_test "generated 200-task fixture remains read-only"
perf_snapshot_after=$(snapshot_tree "$perf_feature")
assert_snapshot_unchanged "$perf_snapshot_before" "$perf_snapshot_after"

test_summary
