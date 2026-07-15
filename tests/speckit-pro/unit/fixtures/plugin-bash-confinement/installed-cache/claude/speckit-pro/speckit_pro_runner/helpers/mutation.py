"""Mutation-capable helper primitives for the stdlib runner."""

from __future__ import annotations

import os
import secrets
import stat
import tempfile
from pathlib import Path
from types import SimpleNamespace
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

    if (target_root / "docs" / "ai" / "knowledge" / "manifest.json").is_file():
        from .knowledge import KnowledgeError, _build_plan, run_knowledge_update_apply

        try:
            rendered, specs_present = render_spec_index(target_root)
            plan = _build_plan(target_root, {"action": "rebuild"})
        except (KnowledgeError, SpecIndexRenderError) as exc:
            diag = diagnostic(
                exc.code if isinstance(exc, KnowledgeError) else "invalid_spec_index",
                str(exc),
                details=exc.details if isinstance(exc, KnowledgeError) else {},
                remediation_summary="Repair the canonical knowledge bundle before rebuilding compatibility maps.",
                remediation_actions=["Run knowledge-health.", "Create a fresh knowledge-update-plan for rebuild."],
            )
            return response("input_error", request_id=request.request_id, diagnostics=[diag])
        apply_request = SimpleNamespace(
            request_id=request.request_id,
            mode=request.mode,
            inputs={
                "repo_root": request.inputs.get("repo_root") or ".",
                "plan": plan,
                "plan_hash": plan["plan_hash"],
                "expected_snapshot": plan["expected_snapshot"],
            },
        )
        result = run_knowledge_update_apply(entry, apply_request)
        data = result.get("data")
        if isinstance(data, dict) and isinstance(data.get("mutation"), dict):
            parity_data = _spec_index_write_data(
                entry,
                request,
                data["mutation"],
                specs_present=specs_present,
                rendered=rendered,
                writes_state=bool(data.get("writes_state")),
            )
            parity_data["expected_snapshot"] = data.get("expected_snapshot")
            parity_data["resulting_snapshot"] = data.get("resulting_snapshot")
            result["data"] = parity_data
        return result

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
            try:
                mode = current.lstat().st_mode
            except FileNotFoundError:
                return False
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                return False
        try:
            target_mode = target.lstat().st_mode
        except FileNotFoundError:
            return True
    except OSError:
        return False
    return not stat.S_ISLNK(target_mode) and stat.S_ISREG(target_mode)


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


def write_file_atomic(target: Path, content: str | bytes, *, trust_root: Path | None = None) -> None:
    if trust_root is not None:
        if os.name == "posix":
            _write_file_atomic_posix(target, content, trust_root)
            return
        if os.name == "nt":
            _write_file_atomic_windows(target, content, trust_root)
            return
        raise OSError("trusted atomic writes are unsupported on this platform")

    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor = -1
    tmp: Path | None = None
    try:
        try:
            target_mode = stat.S_IMODE(target.lstat().st_mode)
        except FileNotFoundError:
            previous_umask = os.umask(0)
            os.umask(previous_umask)
            target_mode = 0o666 & ~previous_umask
        descriptor, raw_tmp = tempfile.mkstemp(prefix=f".{target.name}.tmp-", dir=target.parent)
        tmp = Path(raw_tmp)
        os.fchmod(descriptor, target_mode)
        with os.fdopen(descriptor, "wb") as fh:
            descriptor = -1
            fh.write(_atomic_payload(content))
            fh.flush()
            os.fsync(fh.fileno())
        if tmp.is_symlink() or not tmp.is_file():
            raise OSError("temporary target path changed before replace")
        os.replace(tmp, target)
        if os.name == "posix":
            parent_descriptor = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(parent_descriptor)
            finally:
                os.close(parent_descriptor)
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if tmp is not None and tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                # Best-effort cleanup only; the write outcome is already determined.
                pass


def _write_relative_parts(target: Path, trust_root: Path) -> tuple[tuple[str, ...], str]:
    try:
        relative = target.relative_to(trust_root)
    except ValueError as exc:
        raise OSError("atomic write target is outside the trust root") from exc
    parts = relative.parts
    if not parts or any(part in {"", ".", ".."} or "\x00" in part for part in parts):
        raise OSError("atomic write target is not a safe relative path")
    return parts[:-1], parts[-1]


def remove_path_trusted(
    target: Path,
    *,
    trust_root: Path,
    directory: bool = False,
) -> None:
    """Remove one trusted path without following a swapped parent chain."""

    if os.name == "posix":
        _remove_path_trusted_posix(target, trust_root, directory=directory)
        return
    if os.name == "nt":
        _remove_path_trusted_windows(target, trust_root, directory=directory)
        return
    raise OSError("trusted path removal is unsupported on this platform")


def _remove_path_trusted_posix(target: Path, trust_root: Path, *, directory: bool) -> None:
    parents, leaf = _write_relative_parts(target, trust_root)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptors: list[int] = []
    try:
        descriptors.append(os.open(trust_root, directory_flags))
        for part in parents:
            try:
                descriptors.append(os.open(part, directory_flags, dir_fd=descriptors[-1]))
            except FileNotFoundError:
                return
        parent_descriptor = descriptors[-1]
        try:
            target_stat = os.stat(leaf, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            return
        expected = stat.S_ISDIR(target_stat.st_mode) if directory else stat.S_ISREG(target_stat.st_mode)
        if not expected:
            raise OSError("trusted removal target has an unexpected file type")
        if directory:
            os.rmdir(leaf, dir_fd=parent_descriptor)
        else:
            os.unlink(leaf, dir_fd=parent_descriptor)
        os.fsync(parent_descriptor)
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _remove_path_trusted_windows(target: Path, trust_root: Path, *, directory: bool) -> None:
    import ctypes
    from ctypes import wintypes

    parents, leaf = _write_relative_parts(target, trust_root)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    invalid_handle = wintypes.HANDLE(-1).value
    file_share_read = 0x00000001
    file_share_write = 0x00000002
    file_share_delete = 0x00000004
    file_read_attributes = 0x00000080
    delete_access = 0x00010000
    open_existing = 3
    file_flag_backup_semantics = 0x02000000
    file_flag_open_reparse_point = 0x00200000
    file_attribute_directory = 0x00000010
    file_attribute_reparse_point = 0x00000400
    file_attribute_tag_info = 9
    file_disposition_info = 4

    class FileAttributeTagInfo(ctypes.Structure):
        _fields_ = [("FileAttributes", wintypes.DWORD), ("ReparseTag", wintypes.DWORD)]

    class FileDispositionInfo(ctypes.Structure):
        _fields_ = [("DeleteFile", wintypes.BOOL)]

    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel32.GetFileInformationByHandleEx.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
    kernel32.SetFileInformationByHandle.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    kernel32.SetFileInformationByHandle.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    def win_error(message: str) -> OSError:
        return OSError(ctypes.get_last_error(), message)

    def open_directory(path: Path) -> int:
        handle = kernel32.CreateFileW(
            str(path),
            file_read_attributes,
            file_share_read | file_share_write,
            None,
            open_existing,
            file_flag_backup_semantics | file_flag_open_reparse_point,
            None,
        )
        if handle == invalid_handle:
            error = ctypes.get_last_error()
            if error in {2, 3}:
                raise FileNotFoundError(error, "trusted removal directory is missing")
            raise win_error("could not pin trusted removal directory")
        attributes = FileAttributeTagInfo()
        if not kernel32.GetFileInformationByHandleEx(
            handle,
            file_attribute_tag_info,
            ctypes.byref(attributes),
            ctypes.sizeof(attributes),
        ):
            kernel32.CloseHandle(handle)
            raise win_error("could not validate trusted removal directory")
        if not attributes.FileAttributes & file_attribute_directory or attributes.FileAttributes & file_attribute_reparse_point:
            kernel32.CloseHandle(handle)
            raise OSError("trusted removal directory must be a non-reparse directory")
        return int(handle)

    root = Path(os.path.abspath(trust_root))
    target_path = root.joinpath(*parents, leaf)
    handles: list[int] = []
    target_handle = invalid_handle
    try:
        anchor = Path(root.anchor)
        current = anchor
        handles.append(open_directory(current))
        try:
            for part in (*root.parts[1:], *parents):
                current = current / part
                handles.append(open_directory(current))
        except FileNotFoundError:
            return
        target_handle = kernel32.CreateFileW(
            str(target_path),
            delete_access | file_read_attributes,
            file_share_read | file_share_write | file_share_delete,
            None,
            open_existing,
            file_flag_open_reparse_point | (file_flag_backup_semantics if directory else 0),
            None,
        )
        if target_handle == invalid_handle:
            error = ctypes.get_last_error()
            if error in {2, 3}:
                return
            raise win_error("could not open trusted removal target")
        attributes = FileAttributeTagInfo()
        if not kernel32.GetFileInformationByHandleEx(
            target_handle,
            file_attribute_tag_info,
            ctypes.byref(attributes),
            ctypes.sizeof(attributes),
        ):
            raise win_error("could not validate trusted removal target")
        is_directory = bool(attributes.FileAttributes & file_attribute_directory)
        if attributes.FileAttributes & file_attribute_reparse_point or is_directory != directory:
            raise OSError("trusted removal target has an unexpected file type")
        disposition = FileDispositionInfo(True)
        if not kernel32.SetFileInformationByHandle(
            target_handle,
            file_disposition_info,
            ctypes.byref(disposition),
            ctypes.sizeof(disposition),
        ):
            raise win_error("could not remove trusted target")
    finally:
        if target_handle != invalid_handle:
            kernel32.CloseHandle(target_handle)
        for handle in reversed(handles):
            kernel32.CloseHandle(handle)


def _write_file_atomic_posix(target: Path, content: str | bytes, trust_root: Path) -> None:
    parents, leaf = _write_relative_parts(target, trust_root)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptors: list[int] = []
    temporary_descriptor = -1
    temporary_name: str | None = None
    committed = False
    try:
        descriptors.append(os.open(trust_root, directory_flags))
        for part in parents:
            try:
                descriptor = os.open(part, directory_flags, dir_fd=descriptors[-1])
            except FileNotFoundError:
                os.mkdir(part, mode=0o777, dir_fd=descriptors[-1])
                descriptor = os.open(part, directory_flags, dir_fd=descriptors[-1])
            descriptors.append(descriptor)
        parent_descriptor = descriptors[-1]
        try:
            target_stat = os.stat(leaf, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            target_mode = None
        else:
            if not stat.S_ISREG(target_stat.st_mode):
                raise OSError("atomic write target must be a regular non-symlink file")
            target_mode = stat.S_IMODE(target_stat.st_mode)

        temporary_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
        for _ in range(128):
            candidate = f".{leaf}.tmp-{secrets.token_hex(8)}"
            try:
                temporary_descriptor = os.open(
                    candidate,
                    temporary_flags,
                    0o666,
                    dir_fd=parent_descriptor,
                )
            except FileExistsError:
                continue
            temporary_name = candidate
            break
        if temporary_descriptor < 0 or temporary_name is None:
            raise OSError("could not allocate a unique atomic-write temporary file")
        if target_mode is not None:
            os.fchmod(temporary_descriptor, target_mode)
        payload = _atomic_payload(content)
        offset = 0
        while offset < len(payload):
            offset += os.write(temporary_descriptor, payload[offset:])
        os.fsync(temporary_descriptor)
        if not stat.S_ISREG(os.fstat(temporary_descriptor).st_mode):
            raise OSError("atomic-write temporary handle is not a regular file")
        os.replace(
            temporary_name,
            leaf,
            src_dir_fd=parent_descriptor,
            dst_dir_fd=parent_descriptor,
        )
        committed = True
        os.fsync(parent_descriptor)
    finally:
        if temporary_descriptor >= 0:
            try:
                os.close(temporary_descriptor)
            except OSError:
                pass
        if not committed and temporary_name is not None and descriptors:
            try:
                os.unlink(temporary_name, dir_fd=descriptors[-1])
            except OSError:
                pass
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _write_file_atomic_windows(target: Path, content: str | bytes, trust_root: Path) -> None:
    # Windows lacks Python-level dir_fd mutation APIs. Pin every directory with
    # non-delete-sharing Win32 handles and rename the open temporary handle.
    import ctypes
    from ctypes import wintypes

    parents, leaf = _write_relative_parts(target, trust_root)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    invalid_handle = wintypes.HANDLE(-1).value
    file_share_read = 0x00000001
    file_share_write = 0x00000002
    open_existing = 3
    create_new = 1
    file_flag_backup_semantics = 0x02000000
    file_flag_open_reparse_point = 0x00200000
    file_attribute_normal = 0x00000080
    file_attribute_directory = 0x00000010
    file_attribute_reparse_point = 0x00000400
    generic_write = 0x40000000
    delete_access = 0x00010000
    file_attribute_tag_info = 9
    file_id_info = 18
    file_rename_info = 3

    class FileAttributeTagInfo(ctypes.Structure):
        _fields_ = [("FileAttributes", wintypes.DWORD), ("ReparseTag", wintypes.DWORD)]

    class FileIdInfo(ctypes.Structure):
        _fields_ = [("VolumeSerialNumber", ctypes.c_ulonglong), ("FileId", ctypes.c_byte * 16)]

    class FileRenameInfo(ctypes.Structure):
        _fields_ = [
            ("ReplaceIfExists", wintypes.BOOLEAN),
            ("RootDirectory", wintypes.HANDLE),
            ("FileNameLength", wintypes.DWORD),
            ("FileName", wintypes.WCHAR * 1),
        ]

    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel32.GetFileInformationByHandleEx.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
    kernel32.CreateDirectoryW.argtypes = [wintypes.LPCWSTR, wintypes.LPVOID]
    kernel32.CreateDirectoryW.restype = wintypes.BOOL
    kernel32.WriteFile.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    kernel32.WriteFile.restype = wintypes.BOOL
    kernel32.FlushFileBuffers.argtypes = [wintypes.HANDLE]
    kernel32.FlushFileBuffers.restype = wintypes.BOOL
    kernel32.SetFileInformationByHandle.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    kernel32.SetFileInformationByHandle.restype = wintypes.BOOL
    kernel32.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetFileAttributesW.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.DeleteFileW.argtypes = [wintypes.LPCWSTR]
    kernel32.DeleteFileW.restype = wintypes.BOOL

    def win_error(message: str) -> OSError:
        return OSError(ctypes.get_last_error(), message)

    def open_directory(path: Path) -> int:
        handle = kernel32.CreateFileW(
            str(path),
            0,
            file_share_read | file_share_write,
            None,
            open_existing,
            file_flag_backup_semantics | file_flag_open_reparse_point,
            None,
        )
        if handle == invalid_handle:
            raise win_error("could not pin atomic-write directory")
        attributes = FileAttributeTagInfo()
        identity = FileIdInfo()
        if not kernel32.GetFileInformationByHandleEx(
            handle,
            file_attribute_tag_info,
            ctypes.byref(attributes),
            ctypes.sizeof(attributes),
        ) or not kernel32.GetFileInformationByHandleEx(
            handle,
            file_id_info,
            ctypes.byref(identity),
            ctypes.sizeof(identity),
        ):
            kernel32.CloseHandle(handle)
            raise win_error("could not validate atomic-write directory identity")
        if not attributes.FileAttributes & file_attribute_directory or attributes.FileAttributes & file_attribute_reparse_point:
            kernel32.CloseHandle(handle)
            raise OSError("atomic-write directory must be a non-reparse directory")
        return int(handle)

    root = Path(os.path.abspath(trust_root))
    target_path = root.joinpath(*parents, leaf)
    handles: list[int] = []
    temporary_handle = invalid_handle
    temporary_path: Path | None = None
    committed = False
    try:
        anchor = Path(root.anchor)
        current = anchor
        handles.append(open_directory(current))
        for part in (*root.parts[1:], *parents):
            current = current / part
            try:
                handles.append(open_directory(current))
            except OSError:
                if not kernel32.CreateDirectoryW(str(current), None) and ctypes.get_last_error() != 183:
                    raise win_error("could not create atomic-write directory")
                handles.append(open_directory(current))
        attributes = kernel32.GetFileAttributesW(str(target_path))
        if attributes == 0xFFFFFFFF:
            if ctypes.get_last_error() not in {2, 3}:
                raise win_error("could not inspect atomic write target")
        elif attributes & file_attribute_directory or attributes & file_attribute_reparse_point:
            raise OSError("atomic write target must be a regular non-reparse file")
        for _ in range(128):
            candidate = current / f".{leaf}.tmp-{secrets.token_hex(8)}"
            temporary_handle = kernel32.CreateFileW(
                str(candidate),
                generic_write | delete_access,
                file_share_read | file_share_write,
                None,
                create_new,
                file_attribute_normal | file_flag_open_reparse_point,
                None,
            )
            if temporary_handle != invalid_handle:
                temporary_path = candidate
                break
            if ctypes.get_last_error() != 80:
                raise win_error("could not create atomic-write temporary file")
        if temporary_handle == invalid_handle or temporary_path is None:
            raise OSError("could not allocate a unique atomic-write temporary file")
        temporary_attributes = FileAttributeTagInfo()
        temporary_identity = FileIdInfo()
        if not kernel32.GetFileInformationByHandleEx(
            temporary_handle,
            file_attribute_tag_info,
            ctypes.byref(temporary_attributes),
            ctypes.sizeof(temporary_attributes),
        ) or not kernel32.GetFileInformationByHandleEx(
            temporary_handle,
            file_id_info,
            ctypes.byref(temporary_identity),
            ctypes.sizeof(temporary_identity),
        ):
            raise win_error("could not validate atomic-write temporary identity")
        if temporary_attributes.FileAttributes & (
            file_attribute_directory | file_attribute_reparse_point
        ):
            raise OSError("atomic-write temporary handle must be a regular non-reparse file")
        payload = _atomic_payload(content)
        offset = 0
        while offset < len(payload):
            chunk = payload[offset : offset + 64 * 1024]
            buffer = ctypes.create_string_buffer(chunk)
            written = wintypes.DWORD()
            if not kernel32.WriteFile(
                temporary_handle,
                buffer,
                len(chunk),
                ctypes.byref(written),
                None,
            ):
                raise win_error("could not write atomic-write temporary file")
            if written.value == 0:
                raise OSError("atomic-write temporary file accepted zero bytes")
            offset += written.value
        if not kernel32.FlushFileBuffers(temporary_handle):
            raise win_error("could not flush atomic-write temporary file")
        encoded_name = str(target_path).encode("utf-16-le")
        name_offset = FileRenameInfo.FileName.offset
        rename_buffer = ctypes.create_string_buffer(name_offset + len(encoded_name))
        rename_info = ctypes.cast(rename_buffer, ctypes.POINTER(FileRenameInfo)).contents
        rename_info.ReplaceIfExists = 1
        rename_info.RootDirectory = None
        rename_info.FileNameLength = len(encoded_name)
        ctypes.memmove(ctypes.addressof(rename_buffer) + name_offset, encoded_name, len(encoded_name))
        if not kernel32.SetFileInformationByHandle(
            temporary_handle,
            file_rename_info,
            rename_buffer,
            len(rename_buffer),
        ):
            raise win_error("could not commit atomic-write temporary file")
        committed = True
    finally:
        if temporary_handle != invalid_handle:
            kernel32.CloseHandle(temporary_handle)
        if not committed and temporary_path is not None:
            kernel32.DeleteFileW(str(temporary_path))
        for handle in reversed(handles):
            kernel32.CloseHandle(handle)


def ensure_final_newline(content: str) -> str:
    return content if content.endswith("\n") else f"{content}\n"


def _atomic_payload(content: str | bytes) -> bytes:
    if isinstance(content, bytes):
        return content
    return ensure_final_newline(content).encode("utf-8")


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
