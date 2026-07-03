"""Mutation-capable helper primitives for the stdlib runner."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from .read_only import (
    find_repo_root,
    is_relative_to,
    looks_like_windows_absolute_path,
    normalize_display,
    normalize_path_input,
    path_diagnostic,
    repo_relative,
)

DEFAULT_ROLLBACK = "Review touched_paths and restore the previous file content before retrying."


def run_mutation_helper(
    entry: Any,
    request: Any,
    *,
    operations: list[dict[str, Any]] | None = None,
    extra_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        return response(
            "missing_prerequisite",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "missing_prerequisite",
                    "could not locate repository root for mutation helper request",
                    details={"cwd": normalize_display(Path.cwd())},
                    remediation_summary="Retry from a SpecKit Pro source checkout.",
                    remediation_actions=["Run the request from the repository root.", "Verify speckit_pro_runner exists."],
                )
            ],
        )

    operations_result = normalize_operations(operations if operations is not None else request.inputs.get("operations"))
    if isinstance(operations_result, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[operations_result])
    normalized = operations_result

    mutation = empty_mutation(request.mode)
    mutation["planned_operations"] = operation_records(normalized)
    mutation["planned_paths"] = sorted(
        {
            repo_relative(resolve_candidate_path(op["target"], repo_root), repo_root)
            for op in normalized
            if op["kind"] == "write_file"
        }
    )

    base_data = mutation_response_data(entry, request, mutation, extra_data)
    if request.mode == "read_only":
        if normalized:
            diag = diagnostic(
                "unsupported_mode",
                "mutation helper write operations require dry_run or apply mode",
                details={"helper_id": entry.helper_id, "mode": request.mode},
                remediation_summary="Use dry_run to plan mutation work or apply to perform it.",
                remediation_actions=["Change mode to dry_run or apply.", "Retry with the same structured operations."],
            )
            return response("input_error", request_id=request.request_id, data=base_data, diagnostics=[diag])
        mutation["mutation_status"] = "no_op"
        return response("ok", request_id=request.request_id, data=base_data)

    for op in normalized:
        if op["kind"] != "write_file":
            continue
        path_diag = validate_target_path(op["target"], repo_root)
        if path_diag is not None:
            return response("input_error", request_id=request.request_id, data=base_data, diagnostics=[path_diag])

    batch_diag = validate_batch_write_conflicts(normalized, repo_root)
    if batch_diag is not None:
        return response("input_error", request_id=request.request_id, data=base_data, diagnostics=[batch_diag])

    if request.mode == "dry_run":
        mutation["mutation_status"] = "planned" if normalized else "no_op"
        return response("ok", request_id=request.request_id, data=base_data)

    if request.mode != "apply":
        diag = diagnostic(
            "unsupported_mode",
            "mutation helper mode is not supported",
            details={"helper_id": entry.helper_id, "mode": request.mode},
            remediation_summary="Use dry_run or apply for mutation helpers.",
            remediation_actions=["Retry with a supported mode."],
        )
        return response("input_error", request_id=request.request_id, data=base_data, diagnostics=[diag])

    if not normalized:
        mutation["mutation_status"] = "no_op"
        return response("ok", request_id=request.request_id, data=base_data)

    command_plan_diag = command_plan_apply_diagnostic(normalized, entry.helper_id)
    if command_plan_diag is not None:
        mutation["mutation_status"] = "blocked"
        return response("expected_failure", request_id=request.request_id, data=base_data, diagnostics=[command_plan_diag])

    dirty_diag = dirty_worktree_diagnostic(request.inputs, repo_root)
    if dirty_diag is not None:
        mutation["mutation_status"] = "blocked"
        mutation["dirty_worktree"] = dirty_diag["code"] == "dirty_worktree"
        return response("expected_failure", request_id=request.request_id, data=base_data, diagnostics=[dirty_diag])

    simulate_failure_after = request.inputs.get("simulate_failure_after")
    if simulate_failure_after is not None and not isinstance(simulate_failure_after, int):
        diag = diagnostic(
            "invalid_input",
            "simulate_failure_after must be an integer when provided",
            details={"helper_id": entry.helper_id},
            remediation_summary="Send deterministic fixture controls.",
            remediation_actions=["Remove simulate_failure_after or set it to a non-negative integer."],
        )
        return response("input_error", request_id=request.request_id, data=base_data, diagnostics=[diag])

    for index, op in enumerate(normalized):
        if isinstance(simulate_failure_after, int) and index >= simulate_failure_after:
            mutation["mutation_status"] = "partial_failure"
            mutation["failure_operation"] = operation_record(op)
            mutation["manual_remediation"] = [
                "Inspect applied_operations and touched_paths.",
                "Manually revert or complete the failed operation before retrying.",
            ]
            diag = diagnostic(
                "partial_failure",
                "mutation helper stopped after a deterministic partial failure",
                details={"helper_id": entry.helper_id, "operation_id": op["operation_id"]},
                remediation_summary="Reconcile already-applied operations before retrying.",
                remediation_actions=mutation["manual_remediation"],
            )
            return response("expected_failure", request_id=request.request_id, data=base_data, diagnostics=[diag])

        if op["kind"] == "write_file":
            target = resolve_candidate_path(op["target"], repo_root)
            try:
                write_file_atomic(target, str(op["content"]))
            except OSError as exc:
                mutation["mutation_status"] = "partial_failure" if mutation["applied_operations"] else "blocked"
                mutation["failure_operation"] = operation_record(op)
                mutation["manual_remediation"] = [
                    "Inspect the target path and parent directory.",
                    "Restore any applied_operations before retrying.",
                ]
                diag = diagnostic(
                    "write_failure",
                    "mutation helper could not complete an atomic file write",
                    details={"helper_id": entry.helper_id, "operation_id": op["operation_id"], "error": type(exc).__name__},
                    remediation_summary="Fix the target path or reconcile partial writes before retrying.",
                    remediation_actions=mutation["manual_remediation"],
                )
                return response("expected_failure", request_id=request.request_id, data=base_data, diagnostics=[diag])
            rel = repo_relative(target, repo_root)
            mutation["applied_operations"].append(operation_record(op))
            mutation["touched_paths"].append(rel)
        else:
            mutation["skipped_operations"].append(operation_record(op))

    mutation["mutation_status"] = "applied" if mutation["applied_operations"] else "no_op"
    return response("ok", request_id=request.request_id, data=base_data)


def normalize_operations(raw: Any) -> list[dict[str, Any]] | dict[str, Any]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        return invalid_operation("operations must be an array")
    normalized: list[dict[str, Any]] = []
    for index, op in enumerate(raw):
        if not isinstance(op, dict):
            return invalid_operation("each operation must be an object", index=index)
        operation_id = op.get("operation_id")
        kind = op.get("kind")
        if not isinstance(operation_id, str) or not operation_id:
            return invalid_operation("operation_id is required", index=index)
        if kind not in {"write_file", "command_plan"}:
            return invalid_operation("operation kind is unsupported", index=index)
        if kind == "write_file":
            target = op.get("target")
            content = op.get("content")
            if not isinstance(target, str) or not target:
                return invalid_operation("write_file target is required", index=index)
            if not isinstance(content, str):
                return invalid_operation("write_file content must be a string", index=index)
            normalized.append(
                {
                    "operation_id": operation_id,
                    "kind": "write_file",
                    "target": target,
                    "content": ensure_final_newline(content),
                }
            )
            continue
        command = op.get("command")
        if not isinstance(command, list) or not all(isinstance(part, str) and part for part in command):
            return invalid_operation("command_plan command must be a non-empty string array", index=index)
        normalized.append({"operation_id": operation_id, "kind": "command_plan", "command": command})
    return normalized


def invalid_operation(message: str, *, index: int | None = None) -> dict[str, Any]:
    details: dict[str, Any] = {}
    if index is not None:
        details["operation_index"] = index
    return diagnostic(
        "invalid_input",
        message,
        details=details,
        remediation_summary="Send normalized mutation operation records.",
        remediation_actions=["Use kind write_file or command_plan.", "Retry with operation_id and required fields."],
    )


def validate_target_path(raw: str, repo_root: Path) -> dict[str, Any] | None:
    if "\x00" in raw:
        return path_diagnostic("invalid_input", "path contains a NUL byte", {"field": "target"})
    if looks_like_windows_absolute_path(raw) and os.name != "nt":
        return path_diagnostic(
            "unsupported_path",
            "path escapes the repo/plugin trust boundary",
            {"field": "target", "path": normalize_display(raw)},
        )
    target = resolve_candidate_path(raw, repo_root)
    resolved = target.resolve(strict=False)
    if not is_relative_to(resolved, repo_root):
        return path_diagnostic(
            "unsupported_path",
            "path escapes the repo/plugin trust boundary",
            {"field": "target", "path": normalize_display(raw)},
        )
    if target.is_symlink():
        return path_diagnostic(
            "unsupported_path",
            "mutation target must not be a symlink",
            {"field": "target", "path": repo_relative(target, repo_root)},
        )
    if target.exists() and not target.is_file():
        return path_diagnostic(
            "unsupported_path",
            "mutation target must be a regular file path",
            {"field": "target", "path": repo_relative(target, repo_root)},
        )
    parent = target.parent
    if not is_relative_to(parent.resolve(strict=False), repo_root):
        return path_diagnostic(
            "unsupported_path",
            "mutation target parent escapes the repo/plugin trust boundary",
            {"field": "target", "path": normalize_display(raw)},
        )
    current = parent
    while is_relative_to(current.resolve(strict=False), repo_root):
        if current.exists():
            if current.is_symlink():
                return path_diagnostic(
                    "unsupported_path",
                    "mutation target parent must not be a symlink",
                    {"field": "target", "path": repo_relative(current, repo_root)},
                )
            if not current.is_dir():
                return path_diagnostic(
                    "unsupported_path",
                    "mutation target parent must be a directory",
                    {"field": "target", "path": repo_relative(current, repo_root)},
                )
        if current == repo_root:
            break
        current = current.parent
    return None


def validate_batch_write_conflicts(operations: list[dict[str, Any]], repo_root: Path) -> dict[str, Any] | None:
    write_targets: list[tuple[dict[str, Any], Path]] = [
        (op, resolve_candidate_path(op["target"], repo_root).resolve(strict=False))
        for op in operations
        if op["kind"] == "write_file"
    ]
    seen: dict[Path, str] = {}
    for op, target in write_targets:
        previous = seen.get(target)
        if previous is not None:
            return conflicting_operations(
                "duplicate mutation write target",
                op,
                previous_operation_id=previous,
                target=target,
                repo_root=repo_root,
            )
        seen[target] = op["operation_id"]

    for parent_op, parent_target in write_targets:
        for child_op, child_target in write_targets:
            if parent_op["operation_id"] == child_op["operation_id"]:
                continue
            if is_relative_to(child_target, parent_target):
                return conflicting_operations(
                    "mutation write target conflicts with another planned target parent",
                    child_op,
                    previous_operation_id=parent_op["operation_id"],
                    target=child_target,
                    repo_root=repo_root,
                )
    return None


def conflicting_operations(
    message: str,
    operation: dict[str, Any],
    *,
    previous_operation_id: str,
    target: Path,
    repo_root: Path,
) -> dict[str, Any]:
    return diagnostic(
        "conflicting_operations",
        message,
        details={
            "operation_id": operation["operation_id"],
            "conflicts_with": previous_operation_id,
            "target": repo_relative(target, repo_root),
        },
        remediation_summary="Preflight mutation batches must not contain internally conflicting write paths.",
        remediation_actions=["Split conflicting writes into separate requests.", "Use unique file targets that are not parent/child paths."],
    )


def command_plan_apply_diagnostic(operations: list[dict[str, Any]], helper_id: str) -> dict[str, Any] | None:
    if not any(op["kind"] == "command_plan" for op in operations):
        return None
    return diagnostic(
        "deferred_live_mutation",
        "command-plan apply mode is deferred until the active mutation cutover",
        details={"helper_id": helper_id},
        remediation_summary="Use dry_run for command planning; execute live command plans outside the runner until cutover.",
        remediation_actions=["Switch to dry_run.", "Use the existing approved path for live command work."],
        deferred_to="XPLAT-007/XPLAT-008",
    )


def resolve_candidate_path(raw: str, repo_root: Path) -> Path:
    value = normalize_path_input(raw)
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def dirty_worktree_diagnostic(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any] | None:
    overrides = inputs.get("test_overrides")
    if isinstance(overrides, dict) and overrides.get("dirty_worktree") is True:
        return dirty_worktree_block(repo_root, "test_override")
    if isinstance(overrides, dict) and overrides.get("git_status_error") is True:
        return git_status_unavailable(repo_root, "test_override")
    status = git_worktree_status(repo_root)
    if isinstance(status, dict):
        return status
    if status:
        return dirty_worktree_block(repo_root, "git_status")
    return None


def dirty_worktree_block(repo_root: Path, source: str) -> dict[str, Any]:
    return diagnostic(
        "dirty_worktree",
        "mutation helper refused apply mode because the worktree is dirty",
        details={"repo_root": repo_relative(repo_root, repo_root), "source": source},
        remediation_summary="Start mutation apply from a clean worktree or use dry_run.",
        remediation_actions=["Commit or stash unrelated changes.", "Retry apply mode or use dry_run."],
    )


def git_status_unavailable(repo_root: Path, source: str) -> dict[str, Any]:
    return diagnostic(
        "git_status_unavailable",
        "mutation helper refused apply mode because git status could not prove the worktree is clean",
        details={"repo_root": repo_relative(repo_root, repo_root), "source": source},
        remediation_summary="Start mutation apply only after git status can verify a clean worktree.",
        remediation_actions=["Run git status --porcelain.", "Fix the git status error or use dry_run."],
    )


def git_worktree_status(repo_root: Path) -> bool | dict[str, Any]:
    import subprocess

    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain=v1", "--untracked-files=all"],
            text=True,
            capture_output=True,
            shell=False,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return git_status_unavailable(repo_root, "git_status")
    if completed.returncode != 0:
        return git_status_unavailable(repo_root, "git_status")
    return bool(completed.stdout.strip())


def write_file_atomic(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(ensure_final_newline(content))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def ensure_final_newline(content: str) -> str:
    return content if content.endswith("\n") else f"{content}\n"


def empty_mutation(mode: str) -> dict[str, Any]:
    return {
        "mode": mode,
        "mutation_status": "planned",
        "planned_operations": [],
        "applied_operations": [],
        "skipped_operations": [],
        "no_op_operations": [],
        "planned_paths": [],
        "touched_paths": [],
        "dirty_worktree": False,
        "failure_operation": None,
        "rollback_notes": [DEFAULT_ROLLBACK],
        "manual_remediation": [],
        "live_mutation": False,
    }


def operation_records(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [operation_record(op) for op in operations]


def operation_record(operation: dict[str, Any]) -> dict[str, Any]:
    record = {"operation_id": operation["operation_id"], "kind": operation["kind"]}
    if operation["kind"] == "write_file":
        record["target"] = normalize_display(operation["target"])
    elif operation["kind"] == "command_plan":
        record["command"] = list(operation["command"])
    return record


def mutation_response_data(
    entry: Any,
    request: Any,
    mutation: dict[str, Any],
    extra_data: dict[str, Any] | None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "helper_id": entry.helper_id,
        "operation": entry.operation,
        "mode": request.mode,
        "promotion_status": entry.promotion_status,
        "comparison_mode": entry.comparison_mode,
        "writes_state": request.mode == "apply",
        "mutation": mutation,
    }
    if extra_data:
        data.update(extra_data)
    return data
