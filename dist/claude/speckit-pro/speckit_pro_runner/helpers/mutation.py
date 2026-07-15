"""Mutation-capable helper primitives for the stdlib runner."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from .read_only import (
    RenderedSpecIndexMap,
    SpecIndexRenderError,
    find_repo_root,
    is_relative_to,
    looks_like_windows_absolute_path,
    normalize_display,
    normalize_path_input,
    path_diagnostic,
    render_spec_index,
    repo_relative,
    resolve_input_path,
    resolve_repo_root,
    trusted_dir_exists,
)

DEFAULT_ROLLBACK = "Review touched_paths and restore the previous file content before retrying."
SECURE_DIR_FD_WRITES = (
    os.name == "posix"
    and hasattr(os, "O_DIRECTORY")
    and hasattr(os, "O_NOFOLLOW")
    and all(function in os.supports_dir_fd for function in (os.open, os.mkdir, os.stat, os.unlink))
)


def run_spec_index_write(entry: Any, request: Any) -> dict[str, Any]:
    invocation_root_result = resolve_repo_root(request.inputs)
    if isinstance(invocation_root_result, dict):
        status = "missing_prerequisite" if invocation_root_result["code"] == "missing_prerequisite" else "input_error"
        return response(status, request_id=request.request_id, diagnostics=[invocation_root_result])
    invocation_root = invocation_root_result
    target_root = resolve_input_path(request.inputs.get("repo_root") or ".", invocation_root).resolve(strict=False)
    if not trusted_dir_exists(target_root, invocation_root):
        diag = diagnostic(
            "invalid_input",
            "repo_root must be a directory inside the runner trust boundary",
            details={"helper_id": entry.helper_id, "repo_root": normalize_display(target_root)},
            remediation_summary="Use an existing consumer repository root.",
            remediation_actions=["Set inputs.repo_root to the repository being regenerated.", "Retry the request."],
        )
        return response("input_error", request_id=request.request_id, diagnostics=[diag])

    try:
        rendered, specs_present = render_spec_index(target_root)
    except SpecIndexRenderError as exc:
        diag = diagnostic(
            "invalid_spec_index",
            str(exc),
            details={"helper_id": entry.helper_id, "repo_root": repo_relative(target_root, invocation_root)},
            remediation_summary="Repair the reported generated-zone marker or PRS manifest before writing.",
            remediation_actions=["Correct the malformed source file.", "Run generate-spec-index-check again."],
        )
        return response("input_error", request_id=request.request_id, diagnostics=[diag])

    changed = [record for record in rendered if record.changed]
    operations = _spec_index_write_operations(changed, target_root)
    mutation = empty_mutation(request.mode)
    mutation["planned_operations"] = operation_records(operations)
    mutation["planned_paths"] = [repo_relative(record.path, target_root) for record in changed]
    mutation["live_mutation"] = request.mode == "apply" and bool(changed)

    if request.mode == "dry_run":
        mutation["mutation_status"] = "planned" if changed else "no_op"
        return response(
            "ok",
            request_id=request.request_id,
            data=_spec_index_write_data(
                entry,
                request,
                mutation,
                specs_present=specs_present,
                rendered=rendered,
                writes_state=False,
            ),
        )

    if request.mode != "apply":
        diag = diagnostic(
            "unsupported_mode",
            "generate-spec-index-write requires dry_run or apply mode",
            details={"helper_id": entry.helper_id, "mode": request.mode},
            remediation_summary="Choose a registered mutation mode.",
            remediation_actions=["Use dry_run to inspect planned paths.", "Use apply to regenerate stale maps."],
        )
        return response("input_error", request_id=request.request_id, diagnostics=[diag])

    conflict = _spec_index_source_conflict(changed, target_root)
    if conflict is not None:
        mutation["mutation_status"] = "blocked"
        return response(
            "expected_failure",
            request_id=request.request_id,
            data=_spec_index_write_data(
                entry,
                request,
                mutation,
                specs_present=specs_present,
                rendered=rendered,
                writes_state=False,
            ),
            diagnostics=[conflict],
        )

    for record, operation in zip(changed, operations):
        try:
            write_file_atomic(record.path, record.rendered, trust_root=target_root)
        except OSError as exc:
            mutation["mutation_status"] = "partial_failure" if mutation["applied_operations"] else "blocked"
            mutation["failure_operation"] = operation_record(operation)
            mutation["manual_remediation"] = [
                "Inspect touched_paths and the failed map.",
                "Restore any already-written maps before retrying.",
            ]
            diag = diagnostic(
                "write_failure",
                "generate-spec-index-write could not complete an atomic map update",
                details={
                    "helper_id": entry.helper_id,
                    "target": repo_relative(record.path, target_root),
                    "error": type(exc).__name__,
                },
                remediation_summary="Reconcile any applied map writes and fix the target path before retrying.",
                remediation_actions=mutation["manual_remediation"],
            )
            return response(
                "expected_failure",
                request_id=request.request_id,
                data=_spec_index_write_data(
                    entry,
                    request,
                    mutation,
                    specs_present=specs_present,
                    rendered=rendered,
                    writes_state=bool(mutation["applied_operations"]),
                ),
                diagnostics=[diag],
            )
        mutation["applied_operations"].append(operation_record(operation))
        mutation["touched_paths"].append(repo_relative(record.path, target_root))

    mutation["mutation_status"] = "applied" if changed else "no_op"
    return response(
        "ok",
        request_id=request.request_id,
        data=_spec_index_write_data(
            entry,
            request,
            mutation,
            specs_present=specs_present,
            rendered=rendered,
            writes_state=bool(changed),
        ),
    )


def _spec_index_write_operations(
    rendered: list[RenderedSpecIndexMap],
    target_root: Path,
) -> list[dict[str, Any]]:
    return [
        {
            "operation_id": f"generate-spec-index:{index}",
            "kind": "write_file",
            "target": repo_relative(record.path, target_root),
            "content": record.rendered,
        }
        for index, record in enumerate(rendered, start=1)
    ]


def _spec_index_source_conflict(
    rendered: list[RenderedSpecIndexMap],
    target_root: Path,
) -> dict[str, Any] | None:
    for record in rendered:
        if not _spec_index_target_chain_is_safe(record.path, target_root):
            return diagnostic(
                "source_changed",
                "a rendered spec-index target is no longer a regular in-repository file",
                details={"target": record.path.as_posix()},
                remediation_summary="Do not write through replaced or redirected map paths.",
                remediation_actions=["Inspect the target path.", "Retry from a stable repository tree."],
            )
        try:
            current = record.path.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return diagnostic(
                "source_changed",
                "a rendered spec-index source could not be re-read before apply",
                details={"target": record.path.as_posix(), "error": type(exc).__name__},
                remediation_summary="Re-run from a stable set of source files.",
                remediation_actions=["Inspect the target file.", "Retry generate-spec-index-write."],
            )
        if current != record.original:
            return diagnostic(
                "source_changed",
                "a spec-index source changed after the in-memory render",
                details={"target": record.path.as_posix()},
                remediation_summary="Do not overwrite concurrent edits with a stale render plan.",
                remediation_actions=["Review the concurrent edit.", "Retry to render from current bytes."],
            )
    return None


def _spec_index_target_chain_is_safe(target: Path, trust_root: Path) -> bool:
    if not is_relative_to(target, trust_root):
        return False
    try:
        root_mode = trust_root.lstat().st_mode
        relative = target.relative_to(trust_root)
    except (OSError, ValueError):
        return False
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode) or not relative.parts:
        return False
    current = trust_root
    try:
        for part in relative.parts[:-1]:
            current = current / part
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                return False
        target_mode = target.lstat().st_mode
    except OSError:
        return False
    return not stat.S_ISLNK(target_mode) and stat.S_ISREG(target_mode)


def _mutation_target_chain_is_safe(target: Path, trust_root: Path) -> bool:
    """Allow new write paths while rejecting symlinks at every existing component."""

    if not is_relative_to(target, trust_root):
        return False
    try:
        root_mode = trust_root.lstat().st_mode
        relative = target.relative_to(trust_root)
    except (OSError, ValueError):
        return False
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode) or not relative.parts:
        return False
    current = trust_root
    for index, part in enumerate(relative.parts):
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            continue
        except OSError:
            return False
        if stat.S_ISLNK(mode):
            return False
        is_target = index == len(relative.parts) - 1
        if (is_target and not stat.S_ISREG(mode)) or (not is_target and not stat.S_ISDIR(mode)):
            return False
    return True


def _spec_index_write_data(
    entry: Any,
    request: Any,
    mutation: dict[str, Any],
    *,
    specs_present: bool,
    rendered: list[RenderedSpecIndexMap],
    writes_state: bool,
) -> dict[str, Any]:
    return {
        "helper_id": entry.helper_id,
        "operation": entry.operation,
        "mode": request.mode,
        "promotion_status": entry.promotion_status,
        "comparison_mode": entry.comparison_mode,
        "writes_state": writes_state,
        "specs_present": specs_present,
        "rendered_map_count": len(rendered),
        "stale_map_count": sum(record.changed for record in rendered),
        "mutation": mutation,
    }


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
                write_file_atomic(target, str(op["content"]), trust_root=repo_root)
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


def write_file_atomic(target: Path, content: str, *, trust_root: Path | None = None) -> None:
    if trust_root is not None:
        if not _mutation_target_chain_is_safe(target, trust_root):
            raise OSError("unsafe target path")
        _write_file_atomic_trusted(target, content, trust_root)
        return
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
                # Best-effort cleanup only; the write outcome is already determined.
                pass


def _write_file_atomic_trusted(target: Path, content: str, trust_root: Path) -> None:
    """Write through pinned no-follow directory descriptors or fail closed."""

    if not SECURE_DIR_FD_WRITES:
        raise OSError("secure descriptor-relative writes are unavailable")

    relative = target.relative_to(trust_root)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    parent_fd = os.open(trust_root, directory_flags)
    try:
        for part in relative.parts[:-1]:
            try:
                next_fd = os.open(part, directory_flags, dir_fd=parent_fd)
            except FileNotFoundError:
                try:
                    os.mkdir(part, mode=0o755, dir_fd=parent_fd)
                except FileExistsError:
                    # Another actor won the create race; the no-follow open below validates the directory.
                    pass
                next_fd = os.open(part, directory_flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = next_fd

        target_name = relative.name
        try:
            target_mode = os.stat(target_name, dir_fd=parent_fd, follow_symlinks=False).st_mode
        except FileNotFoundError:
            target_mode = None
        if target_mode is not None and not stat.S_ISREG(target_mode):
            raise OSError("unsafe target path")

        tmp_name = ""
        tmp_fd = -1
        file_flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
        )
        for counter in range(100):
            candidate = f".{target_name}.tmp-{os.getpid()}-{counter}"
            try:
                tmp_fd = os.open(candidate, file_flags, 0o600, dir_fd=parent_fd)
                tmp_name = candidate
                break
            except FileExistsError:
                continue
        if tmp_fd < 0:
            raise OSError("unable to reserve atomic temporary file")

        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8", newline="\n") as fh:
                tmp_fd = -1
                fh.write(ensure_final_newline(content))
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, target_name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
            tmp_name = ""
            os.fsync(parent_fd)
        finally:
            if tmp_fd >= 0:
                os.close(tmp_fd)
            if tmp_name:
                try:
                    os.unlink(tmp_name, dir_fd=parent_fd)
                except FileNotFoundError:
                    # A completed replace or concurrent cleanup may already have removed the temp file.
                    pass
    finally:
        os.close(parent_fd)


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
