#!/usr/bin/env python3
"""Validate that a Codex autopilot workflow/state pair keeps every phase visible."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


WORKFLOW_SECTIONS = (
    "## Phase 1: Specify",
    "## Phase 2: Clarify",
    "## Phase 3: Plan",
    "## Phase 4: Domain Checklists",
    "## Phase 5: Tasks",
    "## Phase 6: Analyze",
    "## Phase 6.5:",
    "## Phase 7: Implement",
    "## Post-Implementation Checklist",
)

WORKFLOW_TOKENS = (
    "| Confidence Gate | G6.5 |",
    "| Post |",
    "| G6.5 |",
)

STATE_PREFIXES = (
    "Archive Sweep:",
    "Phase 0: Prerequisites",
    "Phase 1: Specify",
    "Phase 2: Clarify",
    "Phase 3: Plan",
    "Phase 4: Checklist",
    "Phase 5: Tasks",
    "Phase 6: Analyze",
    "Phase 6.5: Confidence Gate",
    "Phase 7: Implement",
)

POST_STEPS = (
    "Post: Doctor Extension Check",
    "Post: Verify Implementation",
    "Post: Verify Tasks Phantom Check",
    "Post: Code Review",
    "Post: Integration Suite",
    "Post: Reviewability Diff Gate",
    "Post: Self-Review",
    "Post: UAT Runbook Generation",
    "Post: PR Body Generation",
    "Post: PR Creation",
    "Post: Review Remediation",
    "Post: Retrospective",
)

ORDERED_STATE_CHECKPOINTS = (
    "Archive Sweep:",
    "Phase 0: Prerequisites",
    "Phase 1: Specify",
    "Phase 2: Clarify",
    "Phase 3: Plan",
    "Phase 4: Checklist",
    "Phase 5: Tasks",
    "Phase 6: Analyze",
    "Phase 6.5: Confidence Gate",
    "Phase 7: Implement",
    "Post: Doctor Extension Check",
    "Post: Retrospective",
)

TASK_LINE_RE = re.compile(r"^- \[[ xX]\] (T[0-9]+)\b")
UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
WINDOWS_ABSOLUTE_PATH_RE = re.compile(r"^[A-Za-z]:")
SUPPORTED_MARKER_PLAN_VERSIONS = frozenset({"pr-marker-plan.v1", "pr-marker-plan.v2"})
MARKER_PLAN_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "contracts" / "pr-marker-plan.schema.json"
CHANGED_FILE_MANIFEST_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "contracts" / "changed-file-manifest.schema.json"
)
VERIFICATION_REPORT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "contracts" / "verification-report.schema.json"
)
MARKER_PLAN_STATUSES = frozenset({
    "planned", "checkpointing", "emission_ready", "emitting", "emitted",
    "collapsed", "stale", "invalid",
})
COMPLETE_CHECKPOINT_STRING_FIELDS = (
    "evidence_path",
    "checkpoint_evidence_sha",
    "checkpoint_evidence_commit_sha",
    "verification_evidence_path",
    "verification_evidence_sha",
    "commit_sha",
    "head_sha",
    "completed_at",
    "summary",
)
COMPLETE_CHECKPOINT_LIST_FIELDS = (
    "completed_task_ids", "required_verification_gate_ids", "validation",
)
COMPLETE_CHECKPOINT_OBJECT_FIELDS = ("freshness",)
PHASE_VERIFICATION_GATE_ALIASES = {
    "independent_critical_high_review": "independent_review",
}
WORKFLOW_CHECKPOINT_CLAIM_RE = re.compile(
    r"(?m)^-\s+(?:Implementation checkpoint|Current remediation source head)\s+\[([a-z0-9][a-z0-9_-]*)\]:\s+`([0-9a-f]{40})`\s*$"
)
WORKFLOW_SUPERSEDED_CHECKPOINT_CLAIM_RE = re.compile(
    r"(?m)^-\s+Superseded marker checkpoint\s+\[([a-z0-9][a-z0-9_-]*)\]:\s+`([0-9a-f]{40})`\s*$"
)
WORKFLOW_UNSCOPED_CHECKPOINT_CLAIM_RE = re.compile(
    r"(?m)^-\s+(?:Implementation checkpoint|Current remediation source head|Superseded marker checkpoint):\s+`[0-9a-f]{40}`\s*$"
)


@dataclass(frozen=True)
class PlanStep:
    step: str
    status: str | None


class ValidationError(Exception):
    def __init__(self, message: str, code: str = "input_error") -> None:
        super().__init__(message)
        self.code = code


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"could not read file: {path}: {exc}") from exc


def _strict_json_loads(value: str | bytes) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = item
        return result

    def reject_non_finite_constant(constant: str) -> None:
        raise ValueError(f"non-finite JSON number is not allowed: {constant}")

    return json.loads(
        value,
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_non_finite_constant,
    )


def load_state(path: Path) -> dict[str, Any]:
    try:
        state = _strict_json_loads(read_text(path))
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ValidationError(f"invalid state JSON: {path}: {exc}") from exc
    if not isinstance(state, dict):
        raise ValidationError("autopilot state must be a JSON object")
    return state


def extract_plan_steps(state: dict[str, Any]) -> list[PlanStep]:
    raw_plan = state.get("plan")
    if not isinstance(raw_plan, list):
        raise ValidationError("autopilot state must contain a plan array")
    steps: list[PlanStep] = []
    for index, item in enumerate(raw_plan):
        if not isinstance(item, dict):
            raise ValidationError(f"plan item {index} must be an object")
        step = item.get("step")
        if not isinstance(step, str) or not step.strip():
            raise ValidationError(f"plan item {index} must contain a non-empty step")
        status = item.get("status")
        if status is not None and not isinstance(status, str):
            raise ValidationError(f"plan item {index} status must be a string when present")
        steps.append(PlanStep(step=step, status=status))
    return steps


def first_index_with_prefix(steps: list[str], prefix: str) -> int | None:
    for index, step in enumerate(steps):
        if step.startswith(prefix):
            return index
    return None


def first_index_exact(steps: list[str], value: str) -> int | None:
    for index, step in enumerate(steps):
        if step == value:
            return index
    return None


def validate_workflow(text: str) -> dict[str, list[str]]:
    missing_sections = [section for section in WORKFLOW_SECTIONS if section not in text]
    missing_tokens = [token for token in WORKFLOW_TOKENS if token not in text]
    missing_post_items = [post for post in POST_STEPS if post not in text]
    return {
        "missing_workflow_sections": missing_sections,
        "missing_workflow_tokens": missing_tokens,
        "missing_workflow_post_items": missing_post_items,
    }


def validate_workflow_checkpoint_bindings(
    text: str, state: dict[str, Any],
) -> dict[str, list[str]]:
    errors: list[str] = []
    marker_plan = state.get("pr_marker_plan")
    if not isinstance(marker_plan, dict):
        return {"workflow_checkpoint_errors": errors}
    markers = marker_plan.get("markers")
    if not isinstance(markers, list):
        return {"workflow_checkpoint_errors": errors}

    expected: dict[str, str] = {}
    expected_superseded: dict[str, str] = {}
    for marker in markers:
        if not isinstance(marker, dict) or not isinstance(marker.get("id"), str):
            continue
        checkpoint = marker.get("implementation_checkpoint")
        commit_sha = checkpoint.get("commit_sha") if isinstance(checkpoint, dict) else None
        if isinstance(commit_sha, str) and re.fullmatch(r"[0-9a-f]{40}", commit_sha):
            expected[marker["id"]] = commit_sha
        superseded_sha = (
            checkpoint.get("superseded_commit_sha")
            if isinstance(checkpoint, dict)
            else None
        )
        if isinstance(superseded_sha, str) and re.fullmatch(r"[0-9a-f]{40}", superseded_sha):
            expected_superseded[marker["id"]] = superseded_sha
    if not expected:
        return {"workflow_checkpoint_errors": errors}

    for marker_id, claimed_sha in WORKFLOW_CHECKPOINT_CLAIM_RE.findall(text):
        if expected.get(marker_id) != claimed_sha:
            errors.append(
                f"workflow checkpoint claim for marker {marker_id!r} does not match its pr_marker_plan commit_sha"
            )
    for marker_id, claimed_sha in WORKFLOW_SUPERSEDED_CHECKPOINT_CLAIM_RE.findall(text):
        if expected_superseded.get(marker_id) != claimed_sha:
            errors.append(
                f"workflow superseded checkpoint claim for marker {marker_id!r} does not match its pr_marker_plan superseded_commit_sha"
            )
    if WORKFLOW_UNSCOPED_CHECKPOINT_CLAIM_RE.search(text):
        errors.append("workflow checkpoint claims must name their marker")

    section_token = "## PR Marker Plan Evidence"
    if section_token in text:
        section = text.split(section_token, 1)[1].split("\n## ", 1)[0]
        found_markers: set[str] = set()
        for line in section.splitlines():
            if not line.startswith("|") or not line.endswith("|"):
                continue
            cells = [cell.strip() for cell in line[1:-1].split("|")]
            if len(cells) < 5:
                continue
            marker_id = cells[1].strip("` ")
            if marker_id not in expected:
                continue
            found_markers.add(marker_id)
            checkpoint_shas = set(re.findall(r"\b[0-9a-f]{40}\b", cells[4]))
            if expected[marker_id] not in checkpoint_shas:
                errors.append(
                    f"workflow PR Marker Plan Evidence marker {marker_id!r} checkpoint does not bind {expected[marker_id]}"
                )
        for marker_id in expected:
            if marker_id not in found_markers:
                errors.append(
                    f"workflow PR Marker Plan Evidence is missing marker {marker_id!r}"
                )
    return {"workflow_checkpoint_errors": errors}


def validate_state(steps: list[PlanStep]) -> dict[str, list[str]]:
    names = [step.step for step in steps]
    missing_prefixes = [prefix for prefix in STATE_PREFIXES if first_index_with_prefix(names, prefix) is None]
    missing_posts = [post for post in POST_STEPS if first_index_exact(names, post) is None]

    duplicate_steps: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name in seen and name not in duplicate_steps:
            duplicate_steps.append(name)
        seen.add(name)

    order_errors: list[str] = []
    last_index = -1
    for checkpoint in ORDERED_STATE_CHECKPOINTS:
        if checkpoint.startswith("Post:"):
            index = first_index_exact(names, checkpoint)
        else:
            index = first_index_with_prefix(names, checkpoint)
        if index is None:
            continue
        if index < last_index:
            order_errors.append(checkpoint)
        last_index = max(last_index, index)

    in_progress = [step.step for step in steps if step.status == "in_progress"]
    in_progress_errors: list[str] = []
    if len(in_progress) > 1:
        in_progress_errors = in_progress

    return {
        "missing_state_prefixes": missing_prefixes,
        "missing_state_post_items": missing_posts,
        "duplicate_state_steps": duplicate_steps,
        "state_order_errors": order_errors,
        "in_progress_errors": in_progress_errors,
    }


def _pending_value_paths(value: Any, path: str) -> list[str]:
    if isinstance(value, str):
        return [path] if "pending" in value.casefold() else []
    if isinstance(value, list):
        paths: list[str] = []
        for index, item in enumerate(value):
            paths.extend(_pending_value_paths(item, f"{path}[{index}]"))
        return paths
    if isinstance(value, dict):
        paths = []
        for key, item in value.items():
            paths.extend(_pending_value_paths(item, f"{path}.{key}"))
        return paths
    return []


def _repository_root(path: Path) -> Path | None:
    for candidate in (path.parent, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _repo_file(repo_root: Path, raw_path: object) -> Path | None:
    if not _is_normalized_repo_path(raw_path):
        return None
    relative = Path(str(raw_path))
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return resolved


def _sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _string_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        return None
    return value


def _is_normalized_repo_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    if value.startswith("/") or WINDOWS_ABSOLUTE_PATH_RE.match(value):
        return False
    path = PurePosixPath(value)
    return path.as_posix() == value and all(part not in {"", ".", ".."} for part in path.parts)


def _is_utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not UTC_TIMESTAMP_RE.fullmatch(value):
        return False
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == value


def _timestamp_errors(value: object, prefix: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else key
            if key.endswith("_at") and item is not None and not _is_utc_timestamp(item):
                errors.append(f"{child} must be an RFC 3339 UTC timestamp")
            errors.extend(_timestamp_errors(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_timestamp_errors(item, f"{prefix}[{index}]"))
    return errors


def _marker_plan_version_errors(marker_plan: object) -> list[str]:
    if marker_plan is None:
        return []
    if not isinstance(marker_plan, dict):
        return ["pr_marker_plan must be an object"]
    version = marker_plan.get("schema_version")
    if version not in SUPPORTED_MARKER_PLAN_VERSIONS:
        return ["pr_marker_plan.schema_version must be pr-marker-plan.v1 or pr-marker-plan.v2"]
    return []


def _json_values_equal(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return type(left) is type(right) and left == right


def _json_schema_type_matches(value: object, expected: object) -> bool:
    expected_types = expected if isinstance(expected, list) else [expected]
    checks = {
        "array": lambda candidate: isinstance(candidate, list),
        "boolean": lambda candidate: isinstance(candidate, bool),
        "integer": lambda candidate: isinstance(candidate, int) and not isinstance(candidate, bool),
        "null": lambda candidate: candidate is None,
        "number": lambda candidate: isinstance(candidate, (int, float)) and not isinstance(candidate, bool),
        "object": lambda candidate: isinstance(candidate, dict),
        "string": lambda candidate: isinstance(candidate, str),
    }
    return any(
        isinstance(name, str) and name in checks and checks[name](value)
        for name in expected_types
    )


def _resolve_schema_reference(root: dict[str, Any], reference: object) -> object | None:
    if not isinstance(reference, str) or not reference.startswith("#/"):
        return None
    resolved: object = root
    for token in reference[2:].split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(resolved, dict) or key not in resolved:
            return None
        resolved = resolved[key]
    return resolved


def _json_schema_matches(value: object, schema: object, root: dict[str, Any]) -> bool:
    return not _json_schema_errors(value, schema, root, "candidate")


def _json_schema_errors(
    value: object,
    schema: object,
    root: dict[str, Any],
    path: str,
) -> list[str]:
    if schema is True:
        return []
    if schema is False or not isinstance(schema, dict):
        return [f"{path} is rejected by schema"]

    errors: list[str] = []
    if "$ref" in schema:
        resolved = _resolve_schema_reference(root, schema["$ref"])
        if resolved is None:
            errors.append(f"{path} uses an unresolved schema reference")
        else:
            errors.extend(_json_schema_errors(value, resolved, root, path))

    for branch in schema.get("allOf", ()) if isinstance(schema.get("allOf"), list) else ():
        errors.extend(_json_schema_errors(value, branch, root, path))
    any_of = schema.get("anyOf")
    if isinstance(any_of, list) and not any(
        _json_schema_matches(value, branch, root) for branch in any_of
    ):
        errors.append(f"{path} does not match any allowed schema shape")
    one_of = schema.get("oneOf")
    if isinstance(one_of, list) and sum(
        _json_schema_matches(value, branch, root) for branch in one_of
    ) != 1:
        errors.append(f"{path} does not match exactly one allowed schema shape")
    negated = schema.get("not")
    if isinstance(negated, dict) and _json_schema_matches(value, negated, root):
        errors.append(f"{path} matches a prohibited schema shape")
    condition = schema.get("if")
    if isinstance(condition, dict):
        branch = schema.get("then") if _json_schema_matches(value, condition, root) else schema.get("else")
        if branch is not None:
            errors.extend(_json_schema_errors(value, branch, root, path))

    if "const" in schema and not _json_values_equal(value, schema["const"]):
        errors.append(f"{path} does not match its schema constant")
    enum = schema.get("enum")
    if isinstance(enum, list) and not any(_json_values_equal(value, item) for item in enum):
        errors.append(f"{path} is outside its schema enum")
    expected_type = schema.get("type")
    if expected_type is not None and not _json_schema_type_matches(value, expected_type):
        errors.append(f"{path} has the wrong schema type")
        return errors

    if isinstance(value, str):
        minimum_length = schema.get("minLength")
        if isinstance(minimum_length, int) and len(value) < minimum_length:
            errors.append(f"{path} is shorter than allowed")
        pattern = schema.get("pattern")
        if isinstance(pattern, str):
            try:
                matched = re.search(pattern, value) is not None
            except re.error:
                matched = False
            if not matched:
                errors.append(f"{path} does not match its schema pattern")
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isinstance(schema.get("minimum"), (int, float))
        and value < schema["minimum"]
    ):
        errors.append(f"{path} is below its schema minimum")
    if isinstance(value, list):
        minimum_items = schema.get("minItems")
        if isinstance(minimum_items, int) and len(value) < minimum_items:
            errors.append(f"{path} has too few items")
        if schema.get("uniqueItems") is True:
            try:
                serialized = [
                    json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False)
                    for item in value
                ]
            except (RecursionError, TypeError, ValueError) as exc:
                raise ValidationError(
                    f"could not safely compare unique JSON values at {path}"
                ) from exc
            if len(set(serialized)) != len(serialized):
                errors.append(f"{path} must contain unique items")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                errors.extend(_json_schema_errors(item, item_schema, root, f"{path}[{index}]"))
        contains = schema.get("contains")
        if contains is not None and not any(
            _json_schema_matches(item, contains, root) for item in value
        ):
            errors.append(f"{path} does not contain a required schema item")
    if isinstance(value, dict):
        required = schema.get("required") if isinstance(schema.get("required"), list) else []
        missing = sorted(
            key for key in required if isinstance(key, str) and key not in value
        )
        if missing:
            errors.append(f"{path} is missing required fields: {', '.join(missing)}")
        minimum_properties = schema.get("minProperties")
        if isinstance(minimum_properties, int) and len(value) < minimum_properties:
            errors.append(f"{path} has too few properties")
        properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        for key, child_schema in properties.items():
            if key in value:
                errors.extend(
                    _json_schema_errors(value[key], child_schema, root, f"{path}.{key}")
                )
        additional = schema.get("additionalProperties")
        extra = sorted(str(key) for key in value.keys() - properties.keys())
        if additional is False and extra:
            errors.append(f"{path} has unsupported fields: {', '.join(extra)}")
        elif isinstance(additional, dict):
            for key in value.keys() - properties.keys():
                errors.extend(
                    _json_schema_errors(value[key], additional, root, f"{path}.{key}")
                )
    return errors


def _marker_plan_shape_errors(marker_plan: object) -> list[str]:
    if not isinstance(marker_plan, dict) or marker_plan.get("schema_version") != "pr-marker-plan.v2":
        return []
    try:
        schema = _strict_json_loads(read_text(MARKER_PLAN_SCHEMA_PATH))
    except (json.JSONDecodeError, ValueError):
        return ["canonical pr-marker-plan schema is malformed"]
    if not isinstance(schema, dict):
        return ["canonical pr-marker-plan schema root must be an object"]
    return _json_schema_errors(marker_plan, schema, schema, "pr_marker_plan")


def _marker_tasks_sha_text(tasks_text: str, task_ids: set[str]) -> str | None:
    selected: list[str] = []
    found: set[str] = set()
    for line in tasks_text.splitlines():
        match = TASK_LINE_RE.match(line)
        if match and match.group(1) in task_ids:
            selected.append(line)
            found.add(match.group(1))
    if found != task_ids:
        return None
    return _sha256_bytes(("\n".join(selected) + "\n").encode("utf-8"))


def _marker_tasks_sha(tasks_path: Path, task_ids: set[str]) -> str | None:
    return _marker_tasks_sha_text(read_text(tasks_path), task_ids)


def _git_env() -> dict[str, str]:
    return {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"}


def _git_file_at_commit(repo_root: Path, commit_sha: object, relative_path: str) -> bytes | None:
    if not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        return None
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit_sha}:{relative_path}"],
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else None


def _git_commit_exists(repo_root: Path, commit_sha: object) -> bool:
    if not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        return False
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e", f"{commit_sha}^{{commit}}"],
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    return completed.returncode == 0


def _git_commit_is_ancestor(repo_root: Path, ancestor_sha: str, descendant_sha: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", ancestor_sha, descendant_sha],
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    return completed.returncode == 0


def _git_commit_is_ancestor_of_head(repo_root: Path, commit_sha: str) -> bool:
    return _git_commit_is_ancestor(repo_root, commit_sha, "HEAD")


def _git_tree_entries(repo_root: Path, commit_sha: object) -> dict[str, str] | None:
    if not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        return None
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "ls-tree", "-r", "-z", "--full-tree", commit_sha],
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        return None
    entries: dict[str, str] = {}
    for raw_record in completed.stdout.split(b"\0"):
        if not raw_record:
            continue
        try:
            raw_identity, raw_path = raw_record.split(b"\t", 1)
            identity = raw_identity.decode("ascii")
            path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError):
            return None
        if path in entries:
            return None
        entries[path] = identity
    return entries


def _load_json_object(path: Path) -> dict[str, Any] | None:
    try:
        value = _strict_json_loads(read_text(path))
    except (ValidationError, json.JSONDecodeError, RecursionError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _load_json_bytes(value: bytes | None) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        parsed = _strict_json_loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def validate_changed_file_manifest(
    state: dict[str, Any],
    state_path: Path,
    *,
    expected_base_commit: str | None = None,
    expected_head_commit: str | None = None,
) -> dict[str, list[str]]:
    marker_plan = state.get("pr_marker_plan")
    repo_root = _repository_root(state_path)
    resolved_head = (
        subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--verify", "HEAD^{commit}"],
            text=True,
            capture_output=True,
            env=_git_env(),
            shell=False,
            check=False,
        )
        if repo_root
        else None
    )
    current_head = (
        resolved_head.stdout.strip()
        if resolved_head is not None and resolved_head.returncode == 0
        else None
    )
    authority_head = (
        expected_head_commit
        if isinstance(expected_head_commit, str)
        and re.fullmatch(r"[0-9a-f]{40}", expected_head_commit)
        else current_head
    )
    state_ref: str | None = None
    committed_state_bytes: bytes | None = None
    committed_state: dict[str, Any] | None = None
    if repo_root and isinstance(authority_head, str):
        try:
            state_ref = state_path.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            state_ref = None
        if state_ref and _is_normalized_repo_path(state_ref):
            committed_state_bytes = _git_file_at_commit(repo_root, authority_head, state_ref)
            committed_state = _load_json_bytes(committed_state_bytes)
    committed_marker_plan = (
        committed_state.get("pr_marker_plan") if isinstance(committed_state, dict) else None
    )
    strict_contract = any(
        isinstance(candidate, dict)
        and candidate.get("schema_version") == "pr-marker-plan.v2"
        for candidate in (marker_plan, committed_marker_plan)
    )
    authority_errors: list[str] = []
    if strict_contract:
        if committed_state_bytes is None or committed_state is None:
            authority_errors.append(
                "autopilot state is absent or invalid at the authorized PR head"
            )
        else:
            try:
                worktree_state_bytes = state_path.read_bytes()
            except OSError:
                worktree_state_bytes = None
            if worktree_state_bytes != committed_state_bytes:
                authority_errors.append(
                    "autopilot state differs from the authorized PR head"
                )
    manifest_ref = state.get("changed_file_manifest")
    if manifest_ref is None:
        if strict_contract:
            return {
                "changed_file_manifest_errors": [
                    "pr-marker-plan.v2 requires a changed_file_manifest reference",
                ],
            }
        return {"changed_file_manifest_errors": []}
    if not _is_normalized_repo_path(manifest_ref):
        return {"changed_file_manifest_errors": ["changed-file manifest reference is invalid"]}
    if repo_root is None:
        return {"changed_file_manifest_errors": ["repository root is unavailable"]}
    manifest_path = _repo_file(repo_root, manifest_ref)
    manifest = _load_json_object(manifest_path) if manifest_path and manifest_path.is_file() else None
    if manifest is None:
        return {"changed_file_manifest_errors": ["changed-file manifest is missing or invalid"]}
    if strict_contract:
        committed_manifest_bytes = (
            _git_file_at_commit(repo_root, authority_head, manifest_ref)
            if isinstance(authority_head, str)
            else None
        )
        try:
            worktree_manifest_bytes = manifest_path.read_bytes() if manifest_path else None
        except OSError:
            worktree_manifest_bytes = None
        if committed_manifest_bytes is None:
            authority_errors.append(
                "changed-file manifest is absent from the authorized PR head"
            )
        elif worktree_manifest_bytes != committed_manifest_bytes:
            authority_errors.append(
                "changed-file manifest differs from the authorized PR head"
            )
    try:
        manifest_schema = _strict_json_loads(read_text(CHANGED_FILE_MANIFEST_SCHEMA_PATH))
    except (ValidationError, json.JSONDecodeError, ValueError):
        return {"changed_file_manifest_errors": ["canonical changed-file manifest schema is malformed"]}
    if not isinstance(manifest_schema, dict):
        return {"changed_file_manifest_errors": ["canonical changed-file manifest schema root is invalid"]}
    schema_errors = _json_schema_errors(
        manifest,
        manifest_schema,
        manifest_schema,
        "changed_file_manifest",
    )
    expected_feature_id = state.get("spec_id")
    marker_feature_id = marker_plan.get("feature_id") if isinstance(marker_plan, dict) else None
    identity_errors: list[str] = []
    if not isinstance(expected_feature_id, str) or not expected_feature_id:
        identity_errors.append("autopilot state spec_id is invalid")
    if manifest.get("feature_id") != expected_feature_id:
        identity_errors.append("changed-file manifest feature_id does not match state authority")
    if manifest.get("feature_id") != marker_feature_id:
        identity_errors.append("changed-file manifest feature_id does not match marker-plan authority")
    if manifest.get("comparison_ref") != "HEAD":
        identity_errors.append("changed-file manifest comparison_ref must be HEAD")
    if schema_errors or identity_errors:
        return {
            "changed_file_manifest_errors": [
                *authority_errors,
                *(f"changed-file manifest schema: {error}" for error in schema_errors),
                *identity_errors,
            ],
        }
    base_commit = manifest.get("base_commit")
    entries = manifest.get("files")
    if not isinstance(base_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", base_commit):
        return {"changed_file_manifest_errors": ["changed-file manifest base_commit is invalid"]}
    if not isinstance(entries, list):
        return {"changed_file_manifest_errors": ["changed-file manifest files must be an array"]}
    base_errors: list[str] = []
    if strict_contract:
        if not isinstance(expected_base_commit, str) or not re.fullmatch(
            r"[0-9a-f]{40}", expected_base_commit
        ):
            base_errors.append(
                "pr-marker-plan.v2 changed-file manifest requires external expected_base_commit authority"
            )
        elif base_commit != expected_base_commit:
            base_errors.append(
                "changed-file manifest base_commit does not match external PR base authority"
            )
        if not isinstance(expected_head_commit, str) or not re.fullmatch(
            r"[0-9a-f]{40}", expected_head_commit
        ):
            base_errors.append(
                "pr-marker-plan.v2 changed-file manifest requires external expected_head_commit authority"
            )
        declared_base = state.get("changed_file_manifest_base_commit")
        if not isinstance(declared_base, str) or not re.fullmatch(r"[0-9a-f]{40}", declared_base):
            base_errors.append("pr-marker-plan.v2 requires changed_file_manifest_base_commit")
        elif declared_base != base_commit:
            base_errors.append("changed-file manifest base_commit does not match state authority")
    comparison_commit = expected_head_commit if strict_contract else "HEAD"
    if strict_contract and current_head != expected_head_commit:
        base_errors.append("repository HEAD does not match external PR head authority")
    if not _git_commit_exists(repo_root, base_commit):
        base_errors.append("changed-file manifest base_commit is not an existing commit")
    elif not isinstance(comparison_commit, str) or not _git_commit_exists(
        repo_root, comparison_commit
    ):
        base_errors.append("external PR head authority is not an existing commit")
    elif not _git_commit_is_ancestor(repo_root, base_commit, comparison_commit):
        base_errors.append("changed-file manifest base_commit is not an ancestor of the authorized head")
    if base_errors:
        return {"changed_file_manifest_errors": [*authority_errors, *base_errors]}

    declared: dict[str, tuple[str, str | None]] = {}
    expected_owners: dict[str, set[str]] = {}
    expected_source_owners: dict[str, set[str]] = {}
    rename_sources: set[str] = set()
    structural_errors: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            structural_errors.append(f"files[{index}] must be an object")
            continue
        path = entry.get("path")
        operation = entry.get("operation")
        if not _is_normalized_repo_path(path) or path in declared:
            structural_errors.append(f"files[{index}].path is invalid, unsafe, or duplicated")
            continue
        if operation not in {"NEW", "MODIFIED", "DELETED", "RENAMED"}:
            structural_errors.append(f"files[{index}].operation is invalid")
            continue
        if entry.get("category") not in {
            "generated_artifact", "implementation", "plugin_source", "process", "research", "test",
        }:
            structural_errors.append(f"files[{index}].category is invalid")
        if entry.get("provenance") not in {"authored", "generated"}:
            structural_errors.append(f"files[{index}].provenance is invalid")
        marker_ids = entry.get("marker_ids")
        marker_values = _string_list(marker_ids)
        if marker_values is None or len(marker_values) != 1:
            structural_errors.append(f"files[{index}].marker_ids must contain exactly one marker owner")
        source_path = entry.get("source_path")
        if operation == "RENAMED":
            if (
                not _is_normalized_repo_path(source_path)
                or source_path == path
                or source_path in rename_sources
            ):
                structural_errors.append(
                    f"files[{index}].source_path is invalid, unsafe, duplicated, or unchanged"
                )
            else:
                rename_sources.add(source_path)
                expected_source_owners[source_path] = set(marker_values or ())
        elif source_path is not None:
            structural_errors.append(f"files[{index}].source_path is only valid for RENAMED")
        declared[path] = (operation, source_path if isinstance(source_path, str) else None)
        expected_owners[path] = set(marker_values or ())
    if rename_sources & set(declared):
        structural_errors.append("changed-file manifest rename source paths overlap destination paths")
    if structural_errors:
        return {
            "changed_file_manifest_errors": [*authority_errors, *structural_errors]
        }

    completed = subprocess.run(
        [
            "git", "-C", str(repo_root),
            "-c", "diff.renames=true",
            "-c", "diff.renameLimit=0",
            "diff", "--no-ext-diff", "--find-renames=50%",
            "--ignore-submodules=none", "--name-status",
            f"{base_commit}..{comparison_commit}",
        ],
        text=True,
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        return {"changed_file_manifest_errors": ["git diff for changed-file manifest failed"]}
    observed: dict[str, tuple[str, str | None]] = {}
    status_map = {"A": "NEW", "M": "MODIFIED", "D": "DELETED"}
    for line in completed.stdout.splitlines():
        fields = line.split("\t")
        status = fields[0]
        if status.startswith("R") and len(fields) == 3:
            observed[fields[2]] = ("RENAMED", fields[1])
        elif status[:1] in status_map and len(fields) == 2:
            observed[fields[1]] = (status_map[status[:1]], None)
        else:
            return {"changed_file_manifest_errors": [f"unsupported git diff record: {line}"]}
    errors = list(authority_errors)
    if declared != observed:
        errors.append(
            f"declared changed-file manifest does not match {base_commit}..{comparison_commit}"
        )

    expected_manifest_sha = _sha256_bytes(manifest_path.read_bytes())
    current_fingerprint = state.get("current_source_fingerprint")
    plan_fingerprint = marker_plan.get("source_fingerprint") if isinstance(marker_plan, dict) else None
    for label, fingerprint in (
        ("current_source_fingerprint", current_fingerprint),
        ("pr_marker_plan.source_fingerprint", plan_fingerprint),
    ):
        if not isinstance(fingerprint, dict) or fingerprint.get("changed_file_manifest_sha") != expected_manifest_sha:
            errors.append(f"{label}.changed_file_manifest_sha does not match the changed-file manifest")
    if isinstance(current_fingerprint, dict) and isinstance(plan_fingerprint, dict):
        if current_fingerprint != plan_fingerprint:
            errors.append("current and marker-plan source fingerprints do not match")

    markers = marker_plan.get("markers") if isinstance(marker_plan, dict) else None
    if not isinstance(markers, list):
        errors.append("changed-file manifest requires pr_marker_plan.markers")
        return {"changed_file_manifest_errors": errors}
    marker_operations: dict[str, tuple[str, str | None]] = {}
    actual_owners: dict[str, set[str]] = {}
    actual_source_owners: dict[str, set[str]] = {}
    declared_marker_ids = {
        marker.get("id") for marker in markers
        if isinstance(marker, dict) and isinstance(marker.get("id"), str)
    }
    for path, owners in expected_owners.items():
        if not owners <= declared_marker_ids:
            errors.append(f"changed-file manifest marker owner for {path} is not declared")
    for marker_index, marker in enumerate(markers):
        if not isinstance(marker, dict) or not isinstance(marker.get("id"), str):
            errors.append(f"pr_marker_plan.markers[{marker_index}] is invalid")
            continue
        marker_id = marker["id"]
        marker_files = marker.get("declared_files")
        if not isinstance(marker_files, list):
            errors.append(f"pr_marker_plan.markers[{marker_index}].declared_files must be an array")
            continue
        seen_marker_paths: set[str] = set()
        for file_index, record in enumerate(marker_files):
            if not isinstance(record, dict):
                errors.append(
                    f"pr_marker_plan.markers[{marker_index}].declared_files[{file_index}] must be an object"
                )
                continue
            path = record.get("path")
            operation = record.get("operation")
            source_path = record.get("source_path")
            if not isinstance(path, str) or not path or path in seen_marker_paths:
                errors.append(
                    f"pr_marker_plan.markers[{marker_index}].declared_files[{file_index}].path is invalid or duplicated"
                )
                continue
            seen_marker_paths.add(path)
            operation_record = (
                operation,
                source_path if isinstance(source_path, str) else None,
            )
            if operation_record != declared.get(path):
                errors.append(
                    f"pr_marker_plan marker {marker_id} operation/source for {path} does not match changed-file manifest"
                )
            if path in marker_operations and marker_operations[path] != operation_record:
                errors.append(f"pr_marker_plan declared operation conflict for {path}")
            marker_operations[path] = operation_record
            actual_owners.setdefault(path, set()).add(marker_id)
            if operation == "RENAMED" and isinstance(source_path, str):
                actual_source_owners.setdefault(source_path, set()).add(marker_id)
    if set(marker_operations) != set(declared):
        errors.append("pr_marker_plan declared_files union does not match changed-file manifest")
    for path, owners in expected_owners.items():
        if actual_owners.get(path, set()) != owners:
            errors.append(f"pr_marker_plan marker ownership for {path} does not match changed-file manifest")
    if set(actual_source_owners) != set(expected_source_owners):
        errors.append("pr_marker_plan rename source union does not match changed-file manifest")
    for source_path, owners in expected_source_owners.items():
        if actual_source_owners.get(source_path, set()) != owners:
            errors.append(
                f"pr_marker_plan marker ownership for rename source {source_path} does not match changed-file manifest"
            )
    if strict_contract:
        authorized_tree = _git_tree_entries(repo_root, comparison_commit)
        if authorized_tree is None:
            errors.append("authorized PR head tree is unavailable for checkpoint content binding")
        else:
            verified_trees: dict[str, dict[str, str] | None] = {}
            for marker_index, marker in enumerate(markers):
                if not isinstance(marker, dict):
                    continue
                checkpoint = marker.get("implementation_checkpoint")
                if not isinstance(checkpoint, dict) or checkpoint.get("status") != "complete":
                    continue
                marker_id = marker.get("id")
                verified_commit = checkpoint.get("commit_sha")
                if isinstance(verified_commit, str) and verified_commit not in verified_trees:
                    verified_trees[verified_commit] = _git_tree_entries(repo_root, verified_commit)
                verified_tree = (
                    verified_trees.get(verified_commit)
                    if isinstance(verified_commit, str)
                    else None
                )
                if verified_tree is None:
                    errors.append(
                        f"completed marker {marker_id or marker_index} verified commit tree is unavailable"
                    )
                    continue
                carrier_paths = {
                    path
                    for path in (
                        state_ref,
                        manifest_ref,
                        checkpoint.get("evidence_path"),
                        checkpoint.get("verification_evidence_path"),
                    )
                    if isinstance(path, str)
                }
                marker_files = marker.get("declared_files")
                if not isinstance(marker_files, list):
                    continue
                for record in marker_files:
                    if not isinstance(record, dict):
                        continue
                    path = record.get("path")
                    if not isinstance(path, str) or path in carrier_paths:
                        continue
                    if verified_tree.get(path) != authorized_tree.get(path):
                        errors.append(
                            f"completed marker {marker_id or marker_index} file {path} differs from its verified commit"
                        )
                    source_path = record.get("source_path")
                    if (
                        record.get("operation") == "RENAMED"
                        and isinstance(source_path, str)
                        and source_path not in carrier_paths
                        and verified_tree.get(source_path) != authorized_tree.get(source_path)
                    ):
                        errors.append(
                            f"completed marker {marker_id or marker_index} rename source {source_path} differs from its verified commit"
                        )
    return {"changed_file_manifest_errors": errors}


def validate_projection_integrity(
    state: dict[str, Any],
    steps: list[PlanStep],
    state_path: Path,
    *,
    expected_head_commit: str | None = None,
) -> dict[str, list[str]]:
    phase_results = state.get("phase_results")
    marker_plan = state.get("pr_marker_plan")
    completed_phase_pending_fields: list[str] = []
    projection_status_errors: list[str] = []
    checkpoint_evidence_errors: list[str] = []
    checkpoint_source_fingerprint_errors: list[str] = []
    checkpoint_file_errors: list[str] = []
    emission_mapping_errors: list[str] = []
    marker_plan_status_errors: list[str] = []
    repo_root = _repository_root(state_path)
    feature_dir = state.get("feature_dir")
    tasks_path = _repo_file(repo_root, f"{feature_dir}/tasks.md") if repo_root and isinstance(feature_dir, str) else None
    current_tasks_sha = _sha256_bytes(tasks_path.read_bytes()) if tasks_path and tasks_path.is_file() else None
    strict_contract = (
        isinstance(marker_plan, dict)
        and marker_plan.get("schema_version") == "pr-marker-plan.v2"
    )
    marker_plan_status_errors.extend(_marker_plan_version_errors(marker_plan))
    marker_plan_status_errors.extend(_marker_plan_shape_errors(marker_plan))

    markers = marker_plan.get("markers") if isinstance(marker_plan, dict) else None
    declared_marker_ids = {
        marker.get("id")
        for marker in markers or []
        if isinstance(marker, dict)
        and isinstance(marker.get("id"), str)
        and marker["id"]
    }
    phases = phase_results if isinstance(phase_results, dict) else {}
    phases_by_marker: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for phase_name, raw_result in phases.items():
        if not isinstance(phase_name, str) or not isinstance(raw_result, dict):
            continue
        phase_marker_id = raw_result.get("marker_id")
        if isinstance(phase_marker_id, str) and phase_marker_id:
            phases_by_marker.setdefault(phase_marker_id, []).append(
                (phase_name, raw_result)
            )
        if strict_contract and phase_name.startswith("Phase 7: Implement"):
            if not isinstance(phase_marker_id, str) or not phase_marker_id:
                marker_plan_status_errors.append(
                    f"phase_results[{phase_name}] must declare exactly one marker_id"
                )
            elif phase_marker_id not in declared_marker_ids:
                marker_plan_status_errors.append(
                    f"phase_results[{phase_name}] marker_id {phase_marker_id!r} is not declared by pr_marker_plan"
                )
        result_status = raw_result.get("status")
        matching_steps = [step for step in steps if step.step == phase_name or step.step.startswith(f"{phase_name} (")]
        if result_status in {"completed", "in_progress", "pending", "checkpointing"} and matching_steps:
            expected_plan_status = "completed" if result_status == "completed" else result_status
            if matching_steps[0].status != expected_plan_status:
                projection_status_errors.append(
                    f"plan[{matching_steps[0].step}]={matching_steps[0].status!r} "
                    f"does not match phase_results[{phase_name}].status={result_status!r}"
                )
        if result_status == "completed":
            completed_phase_pending_fields.extend(
                _pending_value_paths(raw_result, f"phase_results.{phase_name}")
            )

    if isinstance(markers, list):
        if strict_contract:
            marker_plan_status_errors.extend(_timestamp_errors(marker_plan, "pr_marker_plan"))
        seen_marker_ids: set[str] = set()
        seen_review_orders: set[int] = set()
        task_owners: dict[str, str] = {}
        file_owners: dict[str, str] = {}
        for index, raw_marker in enumerate(markers):
            if not isinstance(raw_marker, dict):
                continue
            marker_id = raw_marker.get("id")
            if not isinstance(marker_id, str) or not marker_id:
                marker_plan_status_errors.append(f"pr_marker_plan.markers[{index}].id is invalid")
                marker_id = f"marker[{index}]"
            elif marker_id in seen_marker_ids:
                marker_plan_status_errors.append(f"pr_marker_plan marker id {marker_id!r} is duplicated")
            else:
                seen_marker_ids.add(marker_id)
            review_order = raw_marker.get("review_order")
            if not isinstance(review_order, int) or isinstance(review_order, bool) or review_order < 1:
                marker_plan_status_errors.append(
                    f"pr_marker_plan.markers[{index}].review_order is invalid"
                )
            elif review_order in seen_review_orders:
                marker_plan_status_errors.append(
                    f"pr_marker_plan review_order {review_order} is duplicated"
                )
            else:
                seen_review_orders.add(review_order)

            source_boundary = raw_marker.get("source_boundary")
            story_id = source_boundary.get("story_id") if isinstance(source_boundary, dict) else None
            kind = raw_marker.get("kind")
            parent_marker_id = raw_marker.get("parent_marker_id")
            expected_identity: tuple[str, object, object] | None = None
            if kind == "user_story" and isinstance(story_id, int):
                expected_identity = (f"us{story_id}", story_id, None)
            elif kind == "user_story_part" and isinstance(story_id, int):
                if not isinstance(marker_id, str) or not re.fullmatch(fr"us{story_id}-part[0-9]+", marker_id):
                    marker_plan_status_errors.append(
                        f"pr_marker_plan.markers[{index}] user_story_part id does not match story_id {story_id}"
                    )
                if parent_marker_id != f"us{story_id}":
                    marker_plan_status_errors.append(
                        f"pr_marker_plan.markers[{index}] user_story_part parent does not match story_id {story_id}"
                    )
            elif kind == "foundation":
                expected_identity = ("foundation", None, None)
            elif kind == "full_spec":
                expected_identity = ("full-spec", None, None)
            elif kind == "polish":
                expected_identity = ("polish", None, None)
            else:
                marker_plan_status_errors.append(
                    f"pr_marker_plan.markers[{index}] kind/story_id combination is invalid"
                )
            if expected_identity is not None:
                expected_id, expected_story_id, expected_parent = expected_identity
                if marker_id != expected_id or story_id != expected_story_id or parent_marker_id != expected_parent:
                    marker_plan_status_errors.append(
                        f"pr_marker_plan.markers[{index}] id, kind, story_id, and parent_marker_id are inconsistent"
                    )

            task_values = _string_list(raw_marker.get("task_ids"))
            folded_values = _string_list(raw_marker.get("folded_polish_task_ids"))
            if task_values is not None and len(set(task_values)) != len(task_values):
                marker_plan_status_errors.append(
                    f"pr_marker_plan.markers[{index}].task_ids contains duplicates"
                )
            if folded_values is not None and len(set(folded_values)) != len(folded_values):
                marker_plan_status_errors.append(
                    f"pr_marker_plan.markers[{index}].folded_polish_task_ids contains duplicates"
                )
            for task_id in (task_values or []) + (folded_values or []):
                owner = task_owners.get(task_id)
                if owner is not None:
                    marker_plan_status_errors.append(
                        f"pr_marker_plan task {task_id!r} is owned by both {owner!r} and {marker_id!r}"
                    )
                else:
                    task_owners[task_id] = marker_id

            declared_files = raw_marker.get("declared_files")
            if isinstance(declared_files, list):
                for file_index, record in enumerate(declared_files):
                    path = record.get("path") if isinstance(record, dict) else None
                    operation = record.get("operation") if isinstance(record, dict) else None
                    source_path = record.get("source_path") if isinstance(record, dict) else None
                    if strict_contract and (
                        not _is_normalized_repo_path(path)
                        or repo_root and _repo_file(repo_root, path) is None
                    ):
                        marker_plan_status_errors.append(
                            f"pr_marker_plan.markers[{index}].declared_files[{file_index}].path is not a normalized repository-relative path"
                        )
                        continue
                    owned_paths = [("file", path)]
                    if operation == "RENAMED":
                        if strict_contract and (
                            not _is_normalized_repo_path(source_path)
                            or source_path == path
                            or repo_root and _repo_file(repo_root, source_path) is None
                        ):
                            marker_plan_status_errors.append(
                                f"pr_marker_plan.markers[{index}].declared_files[{file_index}].source_path is not a normalized repository-relative rename source"
                            )
                            continue
                        owned_paths.append(("rename source", source_path))
                    elif source_path is not None:
                        marker_plan_status_errors.append(
                            f"pr_marker_plan.markers[{index}].declared_files[{file_index}].source_path is only valid for RENAMED"
                        )
                    for path_kind, owned_path in owned_paths:
                        owner = file_owners.get(owned_path)
                        if owner is not None:
                            marker_plan_status_errors.append(
                                f"pr_marker_plan {path_kind} {owned_path!r} is owned by both {owner!r} and {marker_id!r}"
                            )
                        else:
                            file_owners[owned_path] = marker_id

            reviewability = raw_marker.get("reviewability")
            if strict_contract and isinstance(reviewability, dict) and "evidence_path" in reviewability:
                evidence_path_value = reviewability.get("evidence_path")
                if not _is_normalized_repo_path(evidence_path_value) or repo_root and _repo_file(repo_root, evidence_path_value) is None:
                    marker_plan_status_errors.append(
                        f"pr_marker_plan.markers[{index}].reviewability.evidence_path is not a normalized repository-relative path"
                    )
            checkpoint = raw_marker.get("implementation_checkpoint")
            if isinstance(checkpoint, dict):
                checkpoint_status = checkpoint.get("status")
                for path_field in ("evidence_path", "verification_evidence_path") if strict_contract else ():
                    path_value = checkpoint.get(path_field)
                    if path_value is not None and (
                        not _is_normalized_repo_path(path_value)
                        or repo_root and _repo_file(repo_root, path_value) is None
                    ):
                        checkpoint_file_errors.append(
                            f"pr_marker_plan.markers[{index}].implementation_checkpoint.{path_field} is not a normalized repository-relative path"
                        )
                if checkpoint_status == "complete" and strict_contract:
                    for required in COMPLETE_CHECKPOINT_STRING_FIELDS:
                        if not isinstance(checkpoint.get(required), str) or not checkpoint[required].strip():
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.{required}"
                            )
                    for required in COMPLETE_CHECKPOINT_LIST_FIELDS:
                        value = checkpoint.get(required)
                        if (
                            not isinstance(value, list)
                            or not value
                            or not all(isinstance(item, str) and item for item in value)
                            or len(set(value)) != len(value)
                        ):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.{required}"
                            )
                    for required in COMPLETE_CHECKPOINT_OBJECT_FIELDS:
                        if not isinstance(checkpoint.get(required), dict):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.{required}"
                            )
                    task_ids = _string_list(raw_marker.get("task_ids"))
                    folded_task_ids = _string_list(raw_marker.get("folded_polish_task_ids"))
                    expected_tasks = set(task_ids or ()) | set(folded_task_ids or ())
                    completed_tasks = _string_list(checkpoint.get("completed_task_ids"))
                    if task_ids is None or folded_task_ids is None:
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] marker task coverage"
                        )
                    elif completed_tasks is not None and set(completed_tasks) != expected_tasks:
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}].implementation_checkpoint.completed_task_ids coverage"
                        )
                    if checkpoint.get("commit_sha") != checkpoint.get("head_sha"):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}].implementation_checkpoint commit/head mismatch"
                        )
                    reviewability = raw_marker.get("reviewability")
                    reviewed_head = reviewability.get("head_sha") if isinstance(reviewability, dict) else None
                    if reviewed_head != checkpoint.get("head_sha"):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] checkpoint/reviewability head mismatch"
                        )
                    if repo_root:
                        committed_verification_bytes: bytes | None = None
                        evidence_commit_sha = checkpoint.get("checkpoint_evidence_commit_sha")
                        claimed_commit_sha = checkpoint.get("commit_sha")
                        if not _git_commit_exists(repo_root, evidence_commit_sha):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.checkpoint_evidence_commit_sha is not an existing commit"
                            )
                        elif not _git_commit_is_ancestor_of_head(repo_root, evidence_commit_sha):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.checkpoint_evidence_commit_sha is not an ancestor of HEAD"
                            )
                        elif (
                            _git_commit_exists(repo_root, claimed_commit_sha)
                            and not _git_commit_is_ancestor(
                                repo_root, claimed_commit_sha, evidence_commit_sha,
                            )
                        ):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}] implementation commit is not an ancestor of evidence commit"
                            )
                        for required in ("evidence_path", "verification_evidence_path"):
                            target = _repo_file(repo_root, checkpoint.get(required))
                            if target is None or not target.is_file():
                                checkpoint_file_errors.append(
                                    f"pr_marker_plan.markers[{index}].implementation_checkpoint.{required}"
                                )
                        evidence_target = _repo_file(repo_root, checkpoint.get("evidence_path"))
                        evidence_ref = checkpoint.get("evidence_path")
                        verification_target = _repo_file(
                            repo_root, checkpoint.get("verification_evidence_path")
                        )
                        verification_ref = checkpoint.get("verification_evidence_path")
                        if evidence_ref == verification_ref:
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}] checkpoint and verification evidence paths must differ"
                            )
                        committed_evidence_bytes = (
                            _git_file_at_commit(
                                repo_root,
                                checkpoint.get("checkpoint_evidence_commit_sha"),
                                evidence_ref,
                            )
                            if isinstance(evidence_ref, str)
                            else None
                        )
                        if committed_evidence_bytes is None:
                            checkpoint_file_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.checkpoint_evidence_commit_sha"
                            )
                        else:
                            expected_evidence_sha = _sha256_bytes(committed_evidence_bytes)
                            if checkpoint.get("checkpoint_evidence_sha") != expected_evidence_sha:
                                checkpoint_file_errors.append(
                                    f"pr_marker_plan.markers[{index}].implementation_checkpoint.checkpoint_evidence_sha"
                                )
                            if evidence_target is None or not evidence_target.is_file() or evidence_target.read_bytes() != committed_evidence_bytes:
                                checkpoint_file_errors.append(
                                    f"pr_marker_plan.markers[{index}].implementation_checkpoint immutable evidence differs from checkpoint commit"
                                )
                        committed_verification_bytes = (
                            _git_file_at_commit(
                                repo_root,
                                checkpoint.get("checkpoint_evidence_commit_sha"),
                                verification_ref,
                            )
                            if isinstance(verification_ref, str)
                            else None
                        )
                        if committed_verification_bytes is None:
                            checkpoint_file_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint verification evidence is absent from checkpoint commit"
                            )
                        else:
                            expected_verification_sha = _sha256_bytes(committed_verification_bytes)
                            if checkpoint.get("verification_evidence_sha") != expected_verification_sha:
                                checkpoint_file_errors.append(
                                    f"pr_marker_plan.markers[{index}].implementation_checkpoint.verification_evidence_sha"
                                )
                            if (
                                verification_target is None
                                or not verification_target.is_file()
                                or verification_target.read_bytes() != committed_verification_bytes
                            ):
                                checkpoint_file_errors.append(
                                    f"pr_marker_plan.markers[{index}].implementation_checkpoint immutable verification evidence differs from checkpoint commit"
                                )

                evidence_ref = checkpoint.get("evidence_path")
                authorized_evidence_bytes: bytes | None = None
                if strict_contract and repo_root and isinstance(evidence_ref, str):
                    authorized_evidence_bytes = _git_file_at_commit(
                        repo_root, expected_head_commit, evidence_ref,
                    )
                    if authorized_evidence_bytes is None:
                        checkpoint_file_errors.append(
                            f"pr_marker_plan.markers[{index}] checkpoint evidence is absent from the authorized PR head"
                        )
                    else:
                        evidence_path = _repo_file(repo_root, evidence_ref)
                        if (
                            evidence_path is None
                            or not evidence_path.is_file()
                            or evidence_path.read_bytes() != authorized_evidence_bytes
                        ):
                            checkpoint_file_errors.append(
                                f"pr_marker_plan.markers[{index}] checkpoint evidence differs from the authorized PR head"
                            )
                immutable_evidence_bytes = (
                    _git_file_at_commit(
                        repo_root,
                        checkpoint.get("checkpoint_evidence_commit_sha"),
                        evidence_ref,
                    )
                    if checkpoint_status == "complete"
                    and repo_root
                    and isinstance(evidence_ref, str)
                    else None
                )
                evidence = _load_json_bytes(
                    authorized_evidence_bytes
                    if strict_contract
                    else immutable_evidence_bytes
                )
                if checkpoint_status != "complete" and not strict_contract:
                    evidence_path = _repo_file(repo_root, evidence_ref) if repo_root else None
                    evidence = _load_json_object(evidence_path) if evidence_path and evidence_path.is_file() else None
                if (
                    strict_contract
                    and repo_root is not None
                    and expected_head_commit is not None
                    and isinstance(evidence_ref, str)
                    and not isinstance(evidence, dict)
                ):
                    checkpoint_evidence_errors.append(
                        f"pr_marker_plan.markers[{index}] checkpoint evidence must be a JSON object"
                    )
                if strict_contract and isinstance(evidence, dict):
                    for phase_name, phase_result in phases_by_marker.get(marker_id, []):
                        direct_bindings = {
                            "capability_fixture_digest": "capability_fixture_digest",
                            "treatment_fixture_digest": "treatment_fixture_digest",
                            "replay_digest": "replay_digest",
                            "implementation_commit": "implementation_checkpoint_sha",
                            "checkpoint": "implementation_checkpoint_sha",
                        }
                        for phase_field, evidence_field in direct_bindings.items():
                            if (
                                phase_field in phase_result
                                and evidence_field in evidence
                                and phase_result[phase_field] != evidence[evidence_field]
                            ):
                                checkpoint_evidence_errors.append(
                                    f"pr_marker_plan.markers[{index}] phase_results[{phase_name}] {phase_field} does not match checkpoint evidence"
                                )
                        verification = evidence.get("verification")
                        if isinstance(verification, dict):
                            for gate_id, result in verification.items():
                                expected = result.get("evidence") if isinstance(result, dict) else result
                                phase_gate_id = PHASE_VERIFICATION_GATE_ALIASES.get(
                                    gate_id, gate_id,
                                )
                                if (
                                    phase_gate_id in phase_result
                                    and phase_result[phase_gate_id] != expected
                                ):
                                    checkpoint_evidence_errors.append(
                                        f"pr_marker_plan.markers[{index}] phase_results[{phase_name}] {phase_gate_id} does not match checkpoint evidence"
                                    )
                if checkpoint_status == "complete" and strict_contract and repo_root:
                    claimed_commit = checkpoint.get("commit_sha")
                    verification_report = _load_json_bytes(committed_verification_bytes)
                    if not isinstance(verification_report, dict):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] verification report must be a JSON object"
                        )
                    else:
                        try:
                            verification_schema = _strict_json_loads(
                                read_text(VERIFICATION_REPORT_SCHEMA_PATH)
                            )
                        except (ValidationError, json.JSONDecodeError, ValueError):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}] canonical verification report schema is malformed"
                            )
                        else:
                            if not isinstance(verification_schema, dict):
                                checkpoint_evidence_errors.append(
                                    f"pr_marker_plan.markers[{index}] canonical verification report schema root is invalid"
                                )
                            else:
                                checkpoint_evidence_errors.extend(
                                    f"pr_marker_plan.markers[{index}] verification report schema: {error}"
                                    for error in _json_schema_errors(
                                        verification_report,
                                        verification_schema,
                                        verification_schema,
                                        "verification_report",
                                    )
                                )
                    if not isinstance(evidence, dict):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] checkpoint evidence must be a JSON object"
                        )
                    else:
                        expected_feature_id = marker_plan.get("feature_id") if isinstance(marker_plan, dict) else None
                        required_gate_ids = _string_list(
                            checkpoint.get("required_verification_gate_ids")
                        )
                        evidence_gate_ids = _string_list(
                            evidence.get("required_verification_gate_ids")
                        )
                        verification = evidence.get("verification")
                        report_gate_ids = (
                            _string_list(verification_report.get("required_gate_ids"))
                            if isinstance(verification_report, dict)
                            else None
                        )
                        report_results = (
                            verification_report.get("results")
                            if isinstance(verification_report, dict)
                            else None
                        )
                        gate_sets_match = (
                            required_gate_ids is not None
                            and evidence_gate_ids is not None
                            and len(required_gate_ids) == len(set(required_gate_ids))
                            and len(evidence_gate_ids) == len(set(evidence_gate_ids))
                            and set(required_gate_ids) == set(evidence_gate_ids)
                            and isinstance(verification, dict)
                            and set(verification) == set(required_gate_ids)
                        )
                        passing_results = (
                            gate_sets_match
                            and all(
                                isinstance(result, dict)
                                and set(result) == {"status", "evidence"}
                                and result.get("status") == "pass"
                                and isinstance(result.get("evidence"), str)
                                and bool(result["evidence"].strip())
                                for result in verification.values()
                            )
                        )
                        report_gate_sets_match = (
                            gate_sets_match
                            and report_gate_ids is not None
                            and required_gate_ids == evidence_gate_ids == report_gate_ids
                            and isinstance(report_results, dict)
                            and set(report_results) == set(required_gate_ids)
                        )
                        report_passing_results = (
                            report_gate_sets_match
                            and all(
                                isinstance(result, dict)
                                and set(result) == {"status", "evidence"}
                                and result.get("status") == "pass"
                                and isinstance(result.get("evidence"), str)
                                and bool(result["evidence"].strip())
                                for result in report_results.values()
                            )
                        )
                        report_results_match = (
                            report_passing_results
                            and report_results == verification
                        )
                        evidence_checks = {
                            "schema_version": evidence.get("schema_version") == "marker-checkpoint.v1",
                            "feature_id": evidence.get("feature_id") == expected_feature_id,
                            "marker_id": evidence.get("marker_id") == marker_id,
                            "status": evidence.get("status") == "complete",
                            "completed_at": _is_utc_timestamp(evidence.get("completed_at")),
                            "tasks_sha": (
                                isinstance(evidence.get("tasks_sha"), str)
                                and re.fullmatch(r"sha256:[0-9a-f]{64}", evidence["tasks_sha"]) is not None
                            ),
                            "source_fingerprint_status": evidence.get("source_fingerprint_status") == "current",
                            "verification_evidence_sha": (
                                committed_verification_bytes is not None
                                and evidence.get("verification_evidence_sha")
                                == checkpoint.get("verification_evidence_sha")
                                == _sha256_bytes(committed_verification_bytes)
                            ),
                            "required_verification_gate_ids": gate_sets_match,
                            "verification": passing_results,
                        }
                        checkpoint_evidence_errors.extend(
                            f"pr_marker_plan.markers[{index}] checkpoint evidence {field} is invalid"
                            for field, passed in evidence_checks.items() if not passed
                        )
                        verification_report_checks = {
                            "schema_version": (
                                isinstance(verification_report, dict)
                                and verification_report.get("schema_version")
                                == "verification-report.v1"
                            ),
                            "feature_id": (
                                isinstance(verification_report, dict)
                                and verification_report.get("feature_id") == expected_feature_id
                            ),
                            "marker_id": (
                                isinstance(verification_report, dict)
                                and verification_report.get("marker_id") == marker_id
                            ),
                            "status": (
                                isinstance(verification_report, dict)
                                and verification_report.get("status") == "pass"
                            ),
                            "generated_at": (
                                isinstance(verification_report, dict)
                                and _is_utc_timestamp(verification_report.get("generated_at"))
                            ),
                            "verified_commit_sha": (
                                isinstance(verification_report, dict)
                                and verification_report.get("verified_commit_sha")
                                == claimed_commit
                            ),
                            "required_gate_ids": report_gate_sets_match,
                            "results": report_results_match,
                        }
                        checkpoint_evidence_errors.extend(
                            f"pr_marker_plan.markers[{index}] verification report {field} is invalid"
                            for field, passed in verification_report_checks.items() if not passed
                        )
                        if evidence.get("implementation_checkpoint_sha") != claimed_commit:
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}] checkpoint/evidence implementation commit mismatch"
                            )
                        checkpoint_schema = (
                            _repo_file(
                                repo_root,
                                f"{feature_dir}/contracts/marker-checkpoint.schema.json",
                            )
                            if isinstance(feature_dir, str)
                            else None
                        )
                        if checkpoint_schema is not None and checkpoint_schema.is_file():
                            try:
                                schema_value = _strict_json_loads(read_text(checkpoint_schema))
                            except (json.JSONDecodeError, ValueError):
                                checkpoint_evidence_errors.append(
                                    f"pr_marker_plan.markers[{index}] checkpoint evidence schema is malformed"
                                )
                            else:
                                if not isinstance(schema_value, dict):
                                    checkpoint_evidence_errors.append(
                                        f"pr_marker_plan.markers[{index}] checkpoint evidence schema root is invalid"
                                    )
                                else:
                                    checkpoint_evidence_errors.extend(
                                        f"pr_marker_plan.markers[{index}] checkpoint evidence schema: {error}"
                                        for error in _json_schema_errors(
                                            evidence,
                                            schema_value,
                                            schema_value,
                                            "checkpoint_evidence",
                                        )
                                    )
                    if repo_root:
                        if not _git_commit_exists(repo_root, claimed_commit):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.commit_sha is not an existing commit"
                            )
                        elif not _git_commit_is_ancestor_of_head(repo_root, claimed_commit):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.commit_sha is not an ancestor of HEAD"
                            )
                if strict_contract and evidence is not None and tasks_path and current_tasks_sha:
                    primary_task_values = _string_list(raw_marker.get("task_ids"))
                    folded_task_values = _string_list(raw_marker.get("folded_polish_task_ids"))
                    marker_task_values = (
                        [*primary_task_values, *folded_task_values]
                        if primary_task_values is not None and folded_task_values is not None
                        else None
                    )
                    marker_task_ids = set(marker_task_values or ())
                    evidence_task_values = _string_list(evidence.get("task_ids"))
                    freshness = checkpoint.get("freshness") if checkpoint_status == "complete" else evidence
                    freshness = freshness if isinstance(freshness, dict) else {}
                    expected_current_marker_sha = (
                        _marker_tasks_sha(tasks_path, marker_task_ids)
                        if marker_task_values is not None
                        else None
                    )
                    feature_tasks_path = f"{feature_dir}/tasks.md"
                    checkpoint_tasks_bytes = (
                        _git_file_at_commit(
                            repo_root,
                            evidence.get("implementation_checkpoint_sha"),
                            feature_tasks_path,
                        )
                        if repo_root and isinstance(feature_dir, str)
                        else None
                    )
                    try:
                        checkpoint_tasks_text = checkpoint_tasks_bytes.decode("utf-8") if checkpoint_tasks_bytes else None
                    except UnicodeDecodeError:
                        checkpoint_tasks_text = None
                    expected_checkpoint_marker_sha = (
                        _marker_tasks_sha_text(checkpoint_tasks_text, marker_task_ids)
                        if checkpoint_tasks_text is not None and marker_task_values is not None
                        else None
                    )
                    checkpoint_tasks_sha = (
                        _sha256_bytes(checkpoint_tasks_bytes) if checkpoint_tasks_bytes is not None else None
                    )
                    checks = {
                        "marker_id": evidence.get("marker_id") == marker_id,
                        "task_ids": (
                            marker_task_values is not None
                            and evidence_task_values is not None
                            and set(evidence_task_values) == marker_task_ids
                        ),
                        "tasks_sha": evidence.get("tasks_sha") == checkpoint_tasks_sha,
                        "source_fingerprint_contract": freshness.get("source_fingerprint_contract") == "marker-task-lines.v2",
                        "source_fingerprint_status": freshness.get("source_fingerprint_status") == "current_marker_scope",
                        "tasks_sha_scope": freshness.get("tasks_sha_scope") == "checkpoint_time_whole_file",
                        "current_tasks_sha": freshness.get("current_tasks_sha") == current_tasks_sha,
                        "checkpoint_marker_tasks_sha": (
                            freshness.get("checkpoint_marker_tasks_sha") == expected_checkpoint_marker_sha
                        ),
                        "current_marker_tasks_sha": (
                            freshness.get("current_marker_tasks_sha") == expected_current_marker_sha
                        ),
                        "marker_scope_unchanged": (
                            expected_checkpoint_marker_sha is not None
                            and expected_checkpoint_marker_sha == expected_current_marker_sha
                        ),
                    }
                    checkpoint_source_fingerprint_errors.extend(
                        f"pr_marker_plan.markers[{index}] checkpoint {field}"
                        for field, passed in checks.items() if not passed
                    )
                matching_phases = [
                    (phase_name, result)
                    for phase_name, result in phases.items()
                    if isinstance(result, dict) and result.get("marker_id") == marker_id
                ]
                for phase_name, result in matching_phases:
                    phase_complete = result.get("status") == "completed"
                    checkpoint_complete = checkpoint_status == "complete"
                    if phase_complete != checkpoint_complete:
                        projection_status_errors.append(
                            f"marker {marker_id!r} checkpoint={checkpoint_status!r} "
                            f"does not match phase_results[{phase_name}].status={result.get('status')!r}"
                        )

            emission = raw_marker.get("emission_mapping")
            if strict_contract and isinstance(emission, dict):
                emission_status = emission.get("status")
                required_fields: tuple[str, ...] = ()
                if emission_status == "marker_split":
                    required_fields = ("packet_path",)
                elif emission_status == "emitted":
                    required_fields = ("packet_path", "pr_number", "pr_url")
                for required in required_fields:
                    value = emission.get(required)
                    if value is None or isinstance(value, str) and not value.strip():
                        emission_mapping_errors.append(
                            f"pr_marker_plan.markers[{index}].emission_mapping.{required}"
                        )
                packet_path = emission.get("packet_path")
                if packet_path is not None and (
                    not _is_normalized_repo_path(packet_path)
                    or repo_root and _repo_file(repo_root, packet_path) is None
                ):
                    emission_mapping_errors.append(
                        f"pr_marker_plan.markers[{index}].emission_mapping.packet_path is not a normalized repository-relative path"
                    )
                if emission_status != "emitted":
                    for field in ("pr_number", "pr_url"):
                        if field in emission:
                            emission_mapping_errors.append(
                                f"pr_marker_plan.markers[{index}].emission_mapping.{field} is only valid after emission"
                            )
                if emission_status in {"marker_split", "emitted", "hazard_collapsed"}:
                    if not isinstance(checkpoint, dict) or checkpoint.get("status") != "complete":
                        emission_mapping_errors.append(
                            f"pr_marker_plan.markers[{index}] emission requires a complete checkpoint"
                        )

        status_constraints = {
            "planned": ({"pending"}, {"pending"}),
            "checkpointing": ({"pending", "complete"}, {"pending"}),
            "emission_ready": ({"complete"}, {"pending", "marker_split"}),
            "emitting": ({"complete"}, {"pending", "marker_split", "emitted"}),
            "emitted": ({"complete"}, {"emitted"}),
            "collapsed": ({"complete"}, {"hazard_collapsed"}),
            "stale": ({"pending", "complete"}, {"pending", "marker_split", "emitted", "hazard_collapsed"}),
            "invalid": ({"pending", "complete"}, {"pending", "marker_split", "emitted", "hazard_collapsed"}),
        }
        plan_status = marker_plan.get("status")
        if strict_contract and plan_status in status_constraints:
            allowed_checkpoints, allowed_emissions = status_constraints[plan_status]
            for index, raw_marker in enumerate(markers):
                checkpoint = raw_marker.get("implementation_checkpoint") if isinstance(raw_marker, dict) else None
                emission = raw_marker.get("emission_mapping") if isinstance(raw_marker, dict) else None
                checkpoint_status = checkpoint.get("status") if isinstance(checkpoint, dict) else None
                emission_status = emission.get("status") if isinstance(emission, dict) else None
                if checkpoint_status not in allowed_checkpoints:
                    marker_plan_status_errors.append(
                        f"pr_marker_plan.status {plan_status} rejects marker {index} checkpoint {checkpoint_status!r}"
                    )
                if emission_status not in allowed_emissions:
                    marker_plan_status_errors.append(
                        f"pr_marker_plan.status {plan_status} rejects marker {index} emission {emission_status!r}"
                    )
            if plan_status == "emitting":
                emission_statuses = {
                    raw_marker.get("emission_mapping", {}).get("status")
                    for raw_marker in markers
                    if isinstance(raw_marker, dict) and isinstance(raw_marker.get("emission_mapping"), dict)
                }
                if "emitted" not in emission_statuses or emission_statuses <= {"emitted"}:
                    marker_plan_status_errors.append(
                        "pr_marker_plan.status emitting requires both emitted and unfinished marker mappings"
                    )
        diagnostic_warnings = {
            "stale": ("MARKER_PLAN_STALE", {"warning", "error"}),
            "invalid": ("MARKER_PLAN_INVALID", {"error"}),
        }
        if strict_contract and plan_status in diagnostic_warnings:
            code, severities = diagnostic_warnings[plan_status]
            warnings = marker_plan.get("warnings")
            if not isinstance(warnings, list) or not any(
                isinstance(warning, dict)
                and warning.get("code") == code
                and warning.get("severity") in severities
                for warning in warnings
            ):
                marker_plan_status_errors.append(
                    f"pr_marker_plan.status {plan_status} requires diagnostic warning {code}"
                )

    return {
        "completed_phase_pending_fields": completed_phase_pending_fields,
        "projection_status_errors": projection_status_errors,
        "checkpoint_evidence_errors": checkpoint_evidence_errors,
        "checkpoint_source_fingerprint_errors": checkpoint_source_fingerprint_errors,
        "checkpoint_file_errors": checkpoint_file_errors,
        "emission_mapping_errors": emission_mapping_errors,
        "marker_plan_status_errors": marker_plan_status_errors,
    }


def build_report(
    workflow: Path,
    state: Path,
    *,
    expected_base_commit: str | None = None,
    expected_head_commit: str | None = None,
) -> dict[str, Any]:
    workflow_text = read_text(workflow)
    state_data = load_state(state)
    plan_steps = extract_plan_steps(state_data)

    workflow_result = validate_workflow(workflow_text)
    workflow_checkpoint_result = validate_workflow_checkpoint_bindings(
        workflow_text, state_data,
    )
    state_result = validate_state(plan_steps)
    projection_result = validate_projection_integrity(
        state_data,
        plan_steps,
        state,
        expected_head_commit=expected_head_commit,
    )
    manifest_result = validate_changed_file_manifest(
        state_data,
        state,
        expected_base_commit=expected_base_commit,
        expected_head_commit=expected_head_commit,
    )
    problems = {
        **workflow_result,
        **workflow_checkpoint_result,
        **state_result,
        **projection_result,
        **manifest_result,
    }
    passed = all(not values for values in problems.values())

    return {
        "status": "pass" if passed else "fail",
        "workflow_file": str(workflow),
        "state_file": str(state),
        "plan_step_count": len(plan_steps),
        **problems,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", required=True, type=Path, help="Autopilot workflow markdown file")
    parser.add_argument("--state", required=True, type=Path, help="autopilot-state.json file")
    parser.add_argument(
        "--expected-base-commit",
        help="live PR baseRefOid authority required when pr-marker-plan.v2 uses a changed-file manifest",
    )
    parser.add_argument(
        "--expected-head-commit",
        help="live PR headRefOid authority required when pr-marker-plan.v2 uses a changed-file manifest",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(
            args.workflow,
            args.state,
            expected_base_commit=args.expected_base_commit,
            expected_head_commit=args.expected_head_commit,
        )
    except ValidationError as exc:
        print(json.dumps({"status": "input_error", "code": exc.code, "message": str(exc)}, sort_keys=True))
        return 2

    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
