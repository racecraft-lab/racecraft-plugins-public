#!/usr/bin/env python3
"""Validate that a Codex autopilot workflow/state pair keeps every phase visible."""

from __future__ import annotations

import argparse
import hashlib
import json
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
COMPLETE_CHECKPOINT_STRING_FIELDS = (
    "evidence_path",
    "checkpoint_evidence_sha",
    "checkpoint_evidence_commit_sha",
    "verification_evidence_path",
    "commit_sha",
    "head_sha",
    "completed_at",
    "summary",
)
COMPLETE_CHECKPOINT_LIST_FIELDS = ("completed_task_ids", "validation")
COMPLETE_CHECKPOINT_OBJECT_FIELDS = ("freshness",)


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


def load_state(path: Path) -> dict[str, Any]:
    try:
        state = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
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


def _git_file_at_commit(repo_root: Path, commit_sha: object, relative_path: str) -> bytes | None:
    if not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        return None
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit_sha}:{relative_path}"],
        capture_output=True,
        shell=False,
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else None


def _load_json_object(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(read_text(path))
    except (ValidationError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _load_json_bytes(value: bytes | None) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        parsed = json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def validate_changed_file_manifest(state: dict[str, Any], state_path: Path) -> dict[str, list[str]]:
    manifest_ref = state.get("changed_file_manifest")
    if manifest_ref is None:
        return {"changed_file_manifest_errors": []}
    repo_root = _repository_root(state_path)
    if repo_root is None:
        return {"changed_file_manifest_errors": ["repository root is unavailable"]}
    manifest_path = _repo_file(repo_root, manifest_ref)
    manifest = _load_json_object(manifest_path) if manifest_path and manifest_path.is_file() else None
    if manifest is None:
        return {"changed_file_manifest_errors": ["changed-file manifest is missing or invalid"]}
    base_commit = manifest.get("base_commit")
    entries = manifest.get("files")
    if not isinstance(base_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", base_commit):
        return {"changed_file_manifest_errors": ["changed-file manifest base_commit is invalid"]}
    if not isinstance(entries, list):
        return {"changed_file_manifest_errors": ["changed-file manifest files must be an array"]}

    declared: dict[str, str] = {}
    expected_owners: dict[str, set[str]] = {}
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
        declared[path] = operation
        expected_owners[path] = set(marker_values or ())
    if structural_errors:
        return {"changed_file_manifest_errors": structural_errors}

    completed = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--name-status", f"{base_commit}..HEAD"],
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        return {"changed_file_manifest_errors": ["git diff for changed-file manifest failed"]}
    observed: dict[str, str] = {}
    status_map = {"A": "NEW", "M": "MODIFIED", "D": "DELETED"}
    for line in completed.stdout.splitlines():
        fields = line.split("\t")
        status = fields[0]
        if status.startswith("R") and len(fields) == 3:
            observed[fields[2]] = "RENAMED"
        elif status[:1] in status_map and len(fields) == 2:
            observed[fields[1]] = status_map[status[:1]]
        else:
            return {"changed_file_manifest_errors": [f"unsupported git diff record: {line}"]}
    errors = [
        f"declared changed-file manifest does not match {base_commit}..HEAD"
    ] if declared != observed else []

    marker_plan = state.get("pr_marker_plan")
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
    marker_operations: dict[str, str] = {}
    actual_owners: dict[str, set[str]] = {}
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
            if not isinstance(path, str) or not path or path in seen_marker_paths:
                errors.append(
                    f"pr_marker_plan.markers[{marker_index}].declared_files[{file_index}].path is invalid or duplicated"
                )
                continue
            seen_marker_paths.add(path)
            if operation != declared.get(path):
                errors.append(
                    f"pr_marker_plan marker {marker_id} operation for {path} does not match changed-file manifest"
                )
            if path in marker_operations and marker_operations[path] != operation:
                errors.append(f"pr_marker_plan declared operation conflict for {path}")
            marker_operations[path] = operation
            actual_owners.setdefault(path, set()).add(marker_id)
    if set(marker_operations) != set(declared):
        errors.append("pr_marker_plan declared_files union does not match changed-file manifest")
    for path, owners in expected_owners.items():
        if actual_owners.get(path, set()) != owners:
            errors.append(f"pr_marker_plan marker ownership for {path} does not match changed-file manifest")
    return {"changed_file_manifest_errors": errors}


def validate_projection_integrity(
    state: dict[str, Any], steps: list[PlanStep], state_path: Path,
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

    phases = phase_results if isinstance(phase_results, dict) else {}
    for phase_name, raw_result in phases.items():
        if not isinstance(phase_name, str) or not isinstance(raw_result, dict):
            continue
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

    markers = marker_plan.get("markers") if isinstance(marker_plan, dict) else None
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
                    if strict_contract and (
                        not _is_normalized_repo_path(path)
                        or repo_root and _repo_file(repo_root, path) is None
                    ):
                        marker_plan_status_errors.append(
                            f"pr_marker_plan.markers[{index}].declared_files[{file_index}].path is not a normalized repository-relative path"
                        )
                        continue
                    owner = file_owners.get(path)
                    if owner is not None:
                        marker_plan_status_errors.append(
                            f"pr_marker_plan file {path!r} is owned by both {owner!r} and {marker_id!r}"
                        )
                    else:
                        file_owners[path] = marker_id

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
                        if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
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
                        for required in ("evidence_path", "verification_evidence_path"):
                            target = _repo_file(repo_root, checkpoint.get(required))
                            if target is None or not target.is_file():
                                checkpoint_file_errors.append(
                                    f"pr_marker_plan.markers[{index}].implementation_checkpoint.{required}"
                                )
                        evidence_target = _repo_file(repo_root, checkpoint.get("evidence_path"))
                        evidence_ref = checkpoint.get("evidence_path")
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

                evidence_ref = checkpoint.get("evidence_path")
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
                evidence = _load_json_bytes(immutable_evidence_bytes)
                if checkpoint_status != "complete":
                    evidence_path = _repo_file(repo_root, evidence_ref) if repo_root else None
                    evidence = _load_json_object(evidence_path) if evidence_path and evidence_path.is_file() else None
                if strict_contract and evidence is not None and tasks_path and current_tasks_sha:
                    marker_task_values = _string_list(raw_marker.get("task_ids"))
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


def build_report(workflow: Path, state: Path) -> dict[str, Any]:
    workflow_text = read_text(workflow)
    state_data = load_state(state)
    plan_steps = extract_plan_steps(state_data)

    workflow_result = validate_workflow(workflow_text)
    state_result = validate_state(plan_steps)
    projection_result = validate_projection_integrity(state_data, plan_steps, state)
    manifest_result = validate_changed_file_manifest(state_data, state)
    problems = {**workflow_result, **state_result, **projection_result, **manifest_result}
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
    args = parser.parse_args(argv)

    try:
        report = build_report(args.workflow, args.state)
    except ValidationError as exc:
        print(json.dumps({"status": "input_error", "code": exc.code, "message": str(exc)}, sort_keys=True))
        return 2

    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
