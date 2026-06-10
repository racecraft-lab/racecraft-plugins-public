#!/usr/bin/env bash
# plan-layers.sh - Read-only PRSG-008 layer planner for SpecKit tasks.md files.

set -euo pipefail

CALLER_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)"
REPO_ROOT="$CALLER_ROOT"

json_value() {
  printf '%s' "$1" | jq -Rs .
}

normalize_for_display() {
  python3 - "$REPO_ROOT" "$1" <<'PY'
from pathlib import Path
import os
import sys

root = Path(sys.argv[1]).resolve()
raw = sys.argv[2]
path = Path(raw)
try:
    resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
    if os.path.commonpath([str(root), str(resolved)]) == str(root):
        print(resolved.relative_to(root).as_posix())
    else:
        print(path.as_posix())
except Exception:
    print(path.as_posix())
PY
}

emit_input_error() {
  local code="$1" message="$2" feature="${3:-}" tasks="${4:-}" details_json="$5"
  local feature_json tasks_json source_path_json

  if [ -n "$feature" ]; then
    feature_json=$(json_value "$(normalize_for_display "$feature")")
  else
    feature_json=null
  fi

  if [ -n "$tasks" ]; then
    tasks_json=$(json_value "$(normalize_for_display "$tasks")")
    source_path_json="$tasks_json"
  else
    tasks_json=null
    if [ -n "$feature" ]; then
      source_path_json="$feature_json"
    else
      source_path_json=null
    fi
  fi

  jq -cn \
    --arg code "$code" \
    --arg message "$message" \
    --argjson feature_dir "$feature_json" \
    --argjson tasks_file "$tasks_json" \
    --argjson source_path "$source_path_json" \
    --argjson details "$details_json" \
    '{
      tool: "plan-layers",
      contract_version: 1,
      status: "input_error",
      feature_dir: $feature_dir,
      tasks_file: $tasks_file,
      increments: [],
      warnings: [],
      errors: [
        {
          code: $code,
          severity: "error",
          message: $message,
          source: {path: $source_path, line: null},
          details: $details
        }
      ],
      summary: {
        increment_count: 0,
        task_count: 0,
        warning_count: 0,
        error_count: 1,
        message: $message
      }
    }'
  printf 'plan-layers: input_error: %s\n' "$message" >&2
  exit 2
}

if [ "$#" -ne 1 ]; then
  details=$(jq -cn --argjson received "$#" '{expected_args: 1, received_args: $received}')
  emit_input_error "invalid_invocation" "Usage: plan-layers.sh <feature-dir>" "" "" "$details"
fi

FEATURE_DIR="$1"
TASKS_FILE="$FEATURE_DIR/tasks.md"

if [ ! -e "$FEATURE_DIR" ]; then
  details=$(jq -cn --arg feature_dir "$(normalize_for_display "$FEATURE_DIR")" '{feature_dir: $feature_dir}')
  emit_input_error "feature_dir_not_found" "Feature directory not found: $(normalize_for_display "$FEATURE_DIR")" "$FEATURE_DIR" "" "$details"
fi

if [ ! -d "$FEATURE_DIR" ] || [ ! -r "$FEATURE_DIR" ] || [ ! -x "$FEATURE_DIR" ]; then
  details=$(jq -cn --arg feature_dir "$(normalize_for_display "$FEATURE_DIR")" '{feature_dir: $feature_dir}')
  emit_input_error "feature_dir_unreadable" "Feature directory unreadable: $(normalize_for_display "$FEATURE_DIR")" "$FEATURE_DIR" "" "$details"
fi

REPO_ROOT="$(git -C "$FEATURE_DIR" rev-parse --show-toplevel 2>/dev/null || printf '%s\n' "$CALLER_ROOT")"

if [ ! -e "$TASKS_FILE" ]; then
  details=$(jq -cn --arg tasks_file "$(normalize_for_display "$TASKS_FILE")" '{tasks_file: $tasks_file}')
  emit_input_error "tasks_file_missing" "tasks.md missing: $(normalize_for_display "$TASKS_FILE")" "$FEATURE_DIR" "$TASKS_FILE" "$details"
fi

if [ ! -f "$TASKS_FILE" ] || [ ! -r "$TASKS_FILE" ]; then
  details=$(jq -cn --arg tasks_file "$(normalize_for_display "$TASKS_FILE")" '{tasks_file: $tasks_file}')
  emit_input_error "tasks_file_unreadable" "tasks.md unreadable: $(normalize_for_display "$TASKS_FILE")" "$FEATURE_DIR" "$TASKS_FILE" "$details"
fi

planner_model=$(python3 - "$REPO_ROOT" "$FEATURE_DIR" "$TASKS_FILE" <<'PY'
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
feature_dir = Path(sys.argv[2]).resolve()
tasks_file = Path(sys.argv[3]).resolve()


def display_path(path: Path | str) -> str:
    candidate = Path(path)
    try:
        resolved = candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()
        if os.path.commonpath([str(repo_root), str(resolved)]) == str(repo_root):
            return resolved.relative_to(repo_root).as_posix()
        return candidate.as_posix()
    except Exception:
        return candidate.as_posix()


feature_rel = display_path(feature_dir)
tasks_rel = display_path(tasks_file)
lines = tasks_file.read_text(encoding="utf-8").splitlines()


def source(line: int | None = None, heading: str | None = None, path: str | None = None) -> dict:
    payload = {"path": tasks_rel if path is None else path, "line": line}
    if heading is not None:
        payload["heading"] = heading
    return payload


def diagnostic(code: str, severity: str, message: str, line: int | None, details: dict) -> dict:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "source": source(line),
        "details": details,
    }


errors: list[dict] = []
warnings: list[dict] = []


def label_to_id(label: str) -> str | None:
    cleaned = re.sub(r"`|\*", "", label).strip()
    cleaned = re.sub(r"\bunknown\b", "", cleaned, flags=re.IGNORECASE).strip()
    if re.fullmatch(r"Foundation", cleaned, flags=re.IGNORECASE):
        return "foundation"
    if re.search(r"\bPolish\b", cleaned, flags=re.IGNORECASE):
        return "polish"
    match = re.search(r"\b(?:US|User Story)\s*([1-9][0-9]*)\b", cleaned, flags=re.IGNORECASE)
    if match:
        return f"us{match.group(1)}"
    return None


def increment_from_heading(line: str, line_no: int) -> dict | None:
    text = line.strip()
    if not text.startswith("## Phase "):
        return None
    if re.match(r"^## Phase [0-9]+:\s+Foundation\b", text):
        return {
            "id": "foundation",
            "name": "Foundation",
            "kind": "foundation",
            "heading": text,
            "line": line_no,
            "tasks": [],
        }
    story = re.match(r"^## Phase [0-9]+:\s+User Story\s+([1-9][0-9]*)\s+-\s+(.+?)\s*(?:\((?:Priority|P):.*\))?\s*$", text)
    if story:
        number = story.group(1)
        title = story.group(2).strip()
        return {
            "id": f"us{number}",
            "name": f"User Story {number} - {title}",
            "kind": "story",
            "heading": text,
            "line": line_no,
            "tasks": [],
        }
    polish = re.match(r"^## Phase [0-9]+:\s+(.+Polish.+|Polish.+)$", text)
    if polish:
        return {
            "id": "polish",
            "name": polish.group(1).strip(),
            "kind": "polish",
            "heading": text,
            "line": line_no,
            "tasks": [],
        }
    return None


sections: list[dict] = []
section_by_id: dict[str, dict] = {}
task_by_id: dict[str, dict] = {}
current: dict | None = None

supported_task = re.compile(r"^\s*-\s+\[( |x|X)\]\s+(T[0-9]{3,})\b(.*)$")
task_like = re.compile(r"^\s*-\s+\[[^\]]+\]\s+T[0-9]{3,}\b")
path_token = re.compile(r"`([^`]+)`|((?:\./|\.\./|[A-Za-z0-9_.-]+/)[A-Za-z0-9_./-]*[A-Za-z0-9_-](?:\.[A-Za-z0-9]+)?)")


def clean_token(token: str) -> str:
    return token.strip().strip("`'\"()[]{}<>,;:")


def normalize_reference(raw: str) -> tuple[str | None, bool]:
    token = clean_token(raw)
    if not token:
        return None, False
    path = Path(token)
    try:
        resolved = (repo_root / path).resolve() if not path.is_absolute() else path.resolve()
        if os.path.commonpath([str(repo_root), str(resolved)]) != str(repo_root):
            return token, False
        return resolved.relative_to(repo_root).as_posix(), True
    except Exception:
        return token, False


def reference_kind(ref: str) -> str:
    normalized = ref.lstrip("./")
    if normalized.startswith("tests/") or "/tests/" in normalized or re.search(r"(^|/)test-[^/]+\.sh$", normalized):
        return "test"
    return "file"


def extract_references(title: str, task_id: str, increment_id: str, line_no: int) -> tuple[list[str], list[str]]:
    files: list[str] = []
    tests: list[str] = []
    seen_files: set[str] = set()
    seen_tests: set[str] = set()

    for match in path_token.finditer(title):
        raw = match.group(1) or match.group(2) or ""
        normalized, inside_root = normalize_reference(raw)
        if not normalized:
            continue
        kind = reference_kind(normalized)
        if not inside_root:
            warnings.append(
                diagnostic(
                    "reference_not_found",
                    "warning",
                    f"{kind} reference is outside the worktree: {raw}",
                    line_no,
                    {"kind": kind, "reference": clean_token(raw), "task_id": task_id},
                )
            )
            continue

        target = repo_root / normalized
        if not target.exists():
            warnings.append(
                diagnostic(
                    "reference_not_found",
                    "warning",
                    f"{kind} reference not found: {normalized}",
                    line_no,
                    {"kind": kind, "reference": normalized, "task_id": task_id},
                )
            )

        if kind == "test":
            if normalized not in seen_tests:
                seen_tests.add(normalized)
                tests.append(normalized)
        else:
            if normalized not in seen_files:
                seen_files.add(normalized)
                files.append(normalized)

    if not files and not tests:
        warnings.append(
            diagnostic(
                "task_without_references",
                "warning",
                f"Task {task_id} has no file or test references.",
                line_no,
                {"task_id": task_id, "increment_id": increment_id},
            )
        )

    return sorted(files), sorted(tests)


def parse_task(line: str, line_no: int, section: dict) -> dict | None:
    match = supported_task.match(line)
    if not match:
        if task_like.match(line):
            errors.append(
                diagnostic(
                    "malformed_task",
                    "error",
                    "Task-like checkbox line uses unsupported syntax.",
                    line_no,
                    {"line_text": line.strip()},
                )
            )
        return None

    marker, task_id, rest = match.groups()
    rest = rest.strip()
    parallel = False
    story = None
    while True:
        if rest.startswith("[P]"):
            parallel = True
            rest = rest[3:].strip()
            continue
        story_match = re.match(r"^\[US([1-9][0-9]*)\]\s*", rest, flags=re.IGNORECASE)
        if story_match:
            story = f"us{story_match.group(1)}"
            rest = rest[story_match.end():].strip()
            continue
        break
    if section["kind"] == "story" and story is None:
        story = section["id"]

    status = "done" if marker in {"x", "X"} else "todo"
    files, tests = extract_references(rest, task_id, section["id"], line_no)
    task = {
        "id": task_id,
        "title": rest,
        "story": story,
        "increment_id": section["id"],
        "status": status,
        "parallel": parallel,
        "source": source(line_no),
        "files": files,
        "tests": tests,
    }

    if task_id in task_by_id:
        errors.append(
            diagnostic(
                "duplicate_task_id",
                "error",
                f"Task ID {task_id} is duplicated.",
                line_no,
                {
                    "task_id": task_id,
                    "first_source": task_by_id[task_id]["source"],
                    "duplicate_source": source(line_no),
                },
            )
        )
    else:
        task_by_id[task_id] = task
    return task


for index, line in enumerate(lines, start=1):
    heading = increment_from_heading(line, index)
    if heading is not None:
        current = heading
        sections.append(current)
        if heading["id"] in section_by_id:
            errors.append(
                diagnostic(
                    "duplicate_increment_id",
                    "error",
                    f"Increment {heading['id']} is duplicated.",
                    index,
                    {
                        "increment_id": heading["id"],
                        "first_source": source(section_by_id[heading["id"]]["line"], section_by_id[heading["id"]]["heading"]),
                        "duplicate_source": source(index, heading["heading"]),
                    },
                )
            )
        else:
            section_by_id[heading["id"]] = heading
        continue

    if line.startswith("## "):
        current = None
        continue

    if current is not None:
        task = parse_task(line, index, current)
        if task is not None:
            current["tasks"].append(task)


dependency_heading_present = any(line.strip() == "## Dependencies & Execution Order" for line in lines)
delivery_heading_present = any(line.strip() == "### Incremental Delivery" for line in lines)
if not dependency_heading_present:
    errors.append(
        diagnostic(
            "missing_required_heading",
            "error",
            "Missing required dependency heading.",
            None,
            {"required_heading": "## Dependencies & Execution Order"},
        )
    )
if not delivery_heading_present:
    errors.append(
        diagnostic(
            "missing_required_heading",
            "error",
            "Missing required incremental delivery heading.",
            None,
            {"required_heading": "### Incremental Delivery"},
        )
    )


def section_bounds(heading_text: str) -> tuple[int, int] | None:
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == heading_text:
            start = idx + 1
            break
    if start is None:
        return None
    end = len(lines)
    for idx in range(start, len(lines)):
        stripped = lines[idx].strip()
        if idx >= start and stripped.startswith("### ") and stripped != heading_text:
            end = idx
            break
    return start, end


delivery_order: list[str] = []
delivery_bounds = section_bounds("### Incremental Delivery")
if delivery_bounds:
    for line in lines[delivery_bounds[0] : delivery_bounds[1]]:
        match = re.match(r"^\s*[0-9]+\.\s+Complete\s+([^:]+):", line)
        if not match:
            continue
        inc_id = label_to_id(match.group(1))
        if inc_id and inc_id not in delivery_order:
            delivery_order.append(inc_id)
            if inc_id not in section_by_id:
                errors.append(
                    diagnostic(
                        "unknown_increment",
                        "error",
                        f"Delivery order references unknown increment {inc_id}.",
                        lines.index(line) + 1,
                        {"increment_id": inc_id},
                    )
                )

if not delivery_order:
    delivery_order = [section["id"] for section in sections if section["id"] in section_by_id]

for section in sections:
    if section["id"] in section_by_id and not section["tasks"]:
        errors.append(
            diagnostic(
                "empty_increment",
                "error",
                f"Increment {section['id']} has no parseable tasks.",
                section["line"],
                {"increment_id": section["id"]},
            )
        )

dependencies: dict[str, list[str]] = {inc_id: [] for inc_id in section_by_id}
for idx, line in enumerate(lines, start=1):
    match = re.match(r"^\s*-\s+\*\*([^*]+)\*\*:\s+Depends on\s+(.+?)(?:\.|$)", line)
    if not match:
        continue
    inc_id = label_to_id(match.group(1))
    if inc_id is None:
        continue
    dep_text = match.group(2).strip()
    if re.search(r"No prerequisites|Foundation only", dep_text, flags=re.IGNORECASE):
        dependencies.setdefault(inc_id, [])
        continue
    found = [dep for dep in (label_to_id(part) for part in re.split(r",| and ", dep_text)) if dep]
    if not found:
        found = [f"us{num}" for num in re.findall(r"\bUS([1-9][0-9]*)\b", dep_text, flags=re.IGNORECASE)]
        if re.search(r"\bFoundation\b", dep_text, flags=re.IGNORECASE):
            found.insert(0, "foundation")
        if re.search(r"\bPolish\b", dep_text, flags=re.IGNORECASE):
            found.append("polish")
    dep_list = dependencies.setdefault(inc_id, [])
    for dep in found:
        if dep not in section_by_id:
            errors.append(
                diagnostic(
                    "unknown_increment",
                    "error",
                    f"Dependency references unknown increment {dep}.",
                    idx,
                    {"increment_id": dep},
                )
            )
        if dep not in dep_list:
            dep_list.append(dep)

known_order = [inc for inc in delivery_order if inc in section_by_id]
for inc_id in section_by_id:
    if inc_id not in known_order:
        known_order.append(inc_id)

order_index = {inc_id: idx for idx, inc_id in enumerate(known_order)}
for inc_id, deps in dependencies.items():
    if inc_id not in order_index:
        continue
    for dep in deps:
        if dep in order_index and order_index[dep] > order_index[inc_id]:
            errors.append(
                diagnostic(
                    "contradictory_increment_order",
                    "error",
                    f"Increment {inc_id} is ordered before dependency {dep}.",
                    section_by_id.get(inc_id, {}).get("line"),
                    {"expected_order": [], "observed_order": known_order},
                )
            )
            break


def stable_topological_order() -> list[str]:
    result: list[str] = []
    temporary: set[str] = set()
    permanent: set[str] = set()

    def visit(node: str) -> None:
        if node in permanent:
            return
        if node in temporary:
            return
        temporary.add(node)
        for dep in dependencies.get(node, []):
            if dep in section_by_id:
                visit(dep)
        temporary.remove(node)
        permanent.add(node)
        if node not in result:
            result.append(node)

    for node in known_order:
        visit(node)
    return result


expected_order = stable_topological_order()
for err in errors:
    if err["code"] == "contradictory_increment_order":
        err["details"]["expected_order"] = expected_order


def find_cycle() -> list[str] | None:
    visiting: list[str] = []
    visited: set[str] = set()

    def dfs(node: str) -> list[str] | None:
        if node in visiting:
            start = visiting.index(node)
            return visiting[start:] + [node]
        if node in visited:
            return None
        visiting.append(node)
        for dep in dependencies.get(node, []):
            if dep in section_by_id:
                found = dfs(dep)
                if found:
                    return found
        visiting.pop()
        visited.add(node)
        return None

    for node in known_order:
        found = dfs(node)
        if found:
            return found
    return None


cycle = find_cycle()
if cycle:
    first = cycle[0]
    errors.append(
        diagnostic(
            "dependency_cycle",
            "error",
            "Dependency graph contains a cycle.",
            section_by_id.get(first, {}).get("line"),
            {"cycle": cycle},
        )
    )


def aggregate(items: list[dict], key: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for item in items:
        for value in item[key]:
            if value not in seen:
                seen.add(value)
                values.append(value)
    return sorted(values)


increments: list[dict] = []
for inc_id in known_order:
    section = section_by_id.get(inc_id)
    if section is None:
        continue
    tasks = section["tasks"]
    files_flat = [value for task in tasks for value in task["files"]]
    tests_flat = [value for task in tasks for value in task["tests"]]
    depends_on = [dep for dep in dependencies.get(inc_id, []) if dep in section_by_id and order_index.get(dep, 10**9) < order_index.get(inc_id, -1)]
    dedup_depends: list[str] = []
    for prior in known_order:
        if prior in depends_on and prior not in dedup_depends:
            dedup_depends.append(prior)
    increments.append(
        {
            "id": inc_id,
            "name": section["name"],
            "kind": section["kind"],
            "order": len(increments),
            "depends_on": dedup_depends,
            "source": source(section["line"], section["heading"]),
            "tasks": tasks,
            "files": aggregate(tasks, "files"),
            "tests": aggregate(tasks, "tests"),
            "advisory_size": {
                "task_count": len(tasks),
                "file_reference_count": len(files_flat),
                "distinct_file_count": len(set(files_flat)),
                "test_reference_count": len(tests_flat),
                "distinct_test_count": len(set(tests_flat)),
            },
        }
    )

status = "invalid_plan" if errors else "ok"
if status == "ok":
    message = f"Planned {len(increments)} increment(s) with {sum(len(item['tasks']) for item in increments)} task(s)."
else:
    message = f"Layer plan invalid: {len(errors)} error(s)."

model = {
    "status": status,
    "feature_dir": feature_rel,
    "tasks_file": tasks_rel,
    "increments": increments,
    "warnings": warnings,
    "errors": errors,
    "summary": {
        "increment_count": len(increments),
        "task_count": sum(len(item["tasks"]) for item in increments),
        "warning_count": len(warnings),
        "error_count": len(errors),
        "message": message,
    },
}

print(json.dumps(model, separators=(",", ":"), ensure_ascii=True))
PY
)

jq -cn --argjson model "$planner_model" '{
  tool: "plan-layers",
  contract_version: 1,
  status: $model.status,
  feature_dir: $model.feature_dir,
  tasks_file: $model.tasks_file,
  increments: $model.increments,
  warnings: $model.warnings,
  errors: $model.errors,
  summary: $model.summary
}'

status=$(printf '%s' "$planner_model" | jq -r '.status')
error_count=$(printf '%s' "$planner_model" | jq -r '.summary.error_count')
warning_count=$(printf '%s' "$planner_model" | jq -r '.summary.warning_count')
if [ "$status" = "invalid_plan" ]; then
  printf 'plan-layers: invalid_plan: %s error(s)\n' "$error_count" >&2
  exit 1
fi
if [ "$warning_count" -gt 0 ]; then
  printf 'plan-layers: ok with %s warning(s)\n' "$warning_count" >&2
fi
exit 0
