"""Mutation-capable helper primitives for the stdlib runner."""

from __future__ import annotations

import os
import stat
import uuid
import hashlib
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


def atomic_write_cleanup_errors(exc: OSError) -> list[str]:
    errors = getattr(exc, "cleanup_errors", None)
    return errors if isinstance(errors, list) else []


def descriptor_mutation_supported() -> bool:
    return os.name != "nt" and hasattr(os, "O_NOFOLLOW")


def unsupported_mutation_platform(helper_id: str) -> dict[str, Any]:
    return diagnostic(
        "unsupported_platform",
        "mutation helper apply mode requires POSIX descriptor-relative filesystem operations",
        details={"helper_id": helper_id, "platform": os.name},
        remediation_summary="Run apply-mode mutation helpers on a platform with descriptor-relative no-follow filesystem APIs.",
        remediation_actions=["Retry on Linux or macOS.", "Use dry_run on unsupported platforms."],
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

    if changed and not descriptor_mutation_supported():
        mutation["mutation_status"] = "blocked"
        diag = unsupported_mutation_platform(entry.helper_id)
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
            diagnostics=[diag],
        )

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
            mutation["live_mutation"] = True
            write_file_atomic(record.path, record.rendered, trust_root=target_root)
        except OSError as exc:
            mutation["mutation_status"] = "partial_failure" if mutation["applied_operations"] else "blocked"
            mutation["failure_operation"] = operation_record(operation)
            cleanup_errors = atomic_write_cleanup_errors(exc)
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
                    "rollback_errors": cleanup_errors,
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
                    writes_state=bool(mutation["applied_operations"]) or bool(cleanup_errors),
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

    if any(op["kind"] == "write_file" for op in normalized) and not descriptor_mutation_supported():
        mutation["mutation_status"] = "blocked"
        return response(
            "expected_failure",
            request_id=request.request_id,
            data=base_data,
            diagnostics=[unsupported_mutation_platform(entry.helper_id)],
        )

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

    snapshots = capture_write_snapshots(normalized, repo_root)
    if isinstance(snapshots, dict) and "diagnostic" in snapshots:
        mutation["mutation_status"] = "blocked"
        return response("expected_failure", request_id=request.request_id, data=base_data, diagnostics=[snapshots["diagnostic"]])

    for index, op in enumerate(normalized):
        if isinstance(simulate_failure_after, int) and index >= simulate_failure_after:
            mutation["mutation_status"] = "partial_failure"
            mutation["failure_operation"] = operation_record(op)
            rollback_errors = rollback_applied_writes(mutation["touched_paths"], snapshots, repo_root)
            mutation["manual_remediation"] = [
                "Inspect applied_operations and touched_paths.",
                "Retry after the deterministic failure condition is removed.",
            ]
            if rollback_errors:
                mutation["manual_remediation"].append("Manual rollback is required for the reported rollback errors.")
            else:
                mutation["rollback_notes"] = ["Already-applied writes were rolled back before returning partial_failure."]
            diag = diagnostic(
                "partial_failure",
                "mutation helper stopped after a deterministic partial failure",
                details={"helper_id": entry.helper_id, "operation_id": op["operation_id"], "rollback_errors": rollback_errors},
                remediation_summary="Reconcile already-applied operations before retrying.",
                remediation_actions=mutation["manual_remediation"],
            )
            base_data["writes_state"] = bool(rollback_errors)
            return response("expected_failure", request_id=request.request_id, data=base_data, diagnostics=[diag])

        if op["kind"] == "write_file":
            target = resolve_candidate_path(op["target"], repo_root)
            rel = repo_relative(target, repo_root)
            source_precondition_changed = operation_source_fingerprint_diagnostic(op, repo_root)
            if source_precondition_changed is not None:
                mutation["mutation_status"] = "partial_failure" if mutation["applied_operations"] else "blocked"
                mutation["failure_operation"] = operation_record(op)
                rollback_errors = rollback_applied_writes(mutation["touched_paths"], snapshots, repo_root)
                mutation["live_mutation"] = bool(mutation["applied_operations"])
                mutation["manual_remediation"] = [
                    "Inspect the source packet/body files used by this mutation.",
                    "Retry after validation and write preconditions are refreshed from current content.",
                ]
                if rollback_errors:
                    mutation["manual_remediation"].append("Manual rollback is required for the reported rollback errors.")
                base_data["writes_state"] = bool(rollback_errors)
                return response("expected_failure", request_id=request.request_id, data=base_data, diagnostics=[source_precondition_changed])
            source_changed = snapshot_changed_diagnostic(rel, target, snapshots, repo_root)
            if source_changed is not None:
                mutation["mutation_status"] = "partial_failure" if mutation["applied_operations"] else "blocked"
                mutation["failure_operation"] = operation_record(op)
                rollback_errors = rollback_applied_writes(mutation["touched_paths"], snapshots, repo_root)
                mutation["live_mutation"] = bool(mutation["applied_operations"])
                mutation["manual_remediation"] = [
                    "Inspect the target path and parent directory.",
                    "Retry after the write target is stable.",
                ]
                if rollback_errors:
                    mutation["manual_remediation"].append("Manual rollback is required for the reported rollback errors.")
                base_data["writes_state"] = bool(rollback_errors)
                return response("expected_failure", request_id=request.request_id, data=base_data, diagnostics=[source_changed])
            try:
                mutation["live_mutation"] = True
                write_result = write_file_atomic(target, str(op["content"]), trust_root=repo_root)
            except OSError as exc:
                mutation["mutation_status"] = "partial_failure" if mutation["applied_operations"] else "blocked"
                mutation["failure_operation"] = operation_record(op)
                rollback_errors = rollback_applied_writes(mutation["touched_paths"], snapshots, repo_root)
                rollback_errors.extend(atomic_write_cleanup_errors(exc))
                mutation["manual_remediation"] = [
                    "Inspect the target path and parent directory.",
                    "Retry after the write target is stable.",
                ]
                if rollback_errors:
                    mutation["manual_remediation"].append("Manual rollback is required for the reported rollback errors.")
                elif mutation["applied_operations"]:
                    mutation["rollback_notes"] = ["Already-applied writes were rolled back after the failed operation."]
                diag = diagnostic(
                    "write_failure",
                    "mutation helper could not complete an atomic file write",
                    details={
                        "helper_id": entry.helper_id,
                        "operation_id": op["operation_id"],
                        "error": type(exc).__name__,
                        "rollback_errors": rollback_errors,
                    },
                    remediation_summary="Fix the target path or reconcile partial writes before retrying.",
                    remediation_actions=mutation["manual_remediation"],
                )
                base_data["writes_state"] = bool(rollback_errors)
                return response("expected_failure", request_id=request.request_id, data=base_data, diagnostics=[diag])
            mutation["applied_operations"].append(operation_record(op))
            mutation["touched_paths"].append(rel)
            applied_snapshot = snapshot_changed_diagnostic_after_write(
                rel,
                target,
                snapshots,
                repo_root,
                expected_digest=write_result["digest"],
                expected_mode=write_result["mode"],
            )
            if applied_snapshot is not None:
                mutation["mutation_status"] = "partial_failure" if mutation["applied_operations"] else "blocked"
                mutation["failure_operation"] = operation_record(op)
                rollback_errors = rollback_applied_writes(mutation["touched_paths"], snapshots, repo_root)
                mutation["live_mutation"] = True
                mutation["manual_remediation"] = [
                    "Inspect the target path and parent directory.",
                    "Retry after the write target is stable.",
                ]
                if rollback_errors:
                    mutation["manual_remediation"].append("Manual rollback is required for the reported rollback errors.")
                base_data["writes_state"] = bool(rollback_errors)
                return response("expected_failure", request_id=request.request_id, data=base_data, diagnostics=[applied_snapshot])
            source_postcondition_changed = operation_source_fingerprint_diagnostic(op, repo_root)
            if source_postcondition_changed is not None:
                mutation["mutation_status"] = "partial_failure"
                mutation["failure_operation"] = operation_record(op)
                rollback_errors = rollback_applied_writes(mutation["touched_paths"], snapshots, repo_root)
                mutation["live_mutation"] = True
                mutation["manual_remediation"] = [
                    "Inspect the source packet/body files used by this mutation.",
                    "Retry after validation and write preconditions are refreshed from current content.",
                ]
                if rollback_errors:
                    mutation["manual_remediation"].append("Manual rollback is required for the reported rollback errors.")
                base_data["writes_state"] = bool(rollback_errors)
                return response("expected_failure", request_id=request.request_id, data=base_data, diagnostics=[source_postcondition_changed])
        else:
            mutation["skipped_operations"].append(operation_record(op))

    mutation["mutation_status"] = "applied" if mutation["applied_operations"] else "no_op"
    mutation["live_mutation"] = bool(mutation["applied_operations"])
    base_data["writes_state"] = bool(mutation["applied_operations"])
    return response("ok", request_id=request.request_id, data=base_data)


def normalize_operations(raw: Any) -> list[dict[str, Any]] | dict[str, Any]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        return invalid_operation("operations must be an array")
    normalized: list[dict[str, Any]] = []
    seen_operation_ids: set[str] = set()
    for index, op in enumerate(raw):
        if not isinstance(op, dict):
            return invalid_operation("each operation must be an object", index=index)
        operation_id = op.get("operation_id")
        kind = op.get("kind")
        if not isinstance(operation_id, str) or not operation_id:
            return invalid_operation("operation_id is required", index=index)
        if operation_id in seen_operation_ids:
            return invalid_operation("operation_id values must be unique", index=index)
        seen_operation_ids.add(operation_id)
        if kind not in {"write_file", "command_plan"}:
            return invalid_operation("operation kind is unsupported", index=index)
        if kind == "write_file":
            target = op.get("target")
            content = op.get("content")
            if not isinstance(target, str) or not target:
                return invalid_operation("write_file target is required", index=index)
            if not isinstance(content, str):
                return invalid_operation("write_file content must be a string", index=index)
            source_fingerprints = op.get("source_fingerprints")
            if source_fingerprints is not None:
                source_fingerprints_result = normalize_source_fingerprints(source_fingerprints, index=index)
                if isinstance(source_fingerprints_result, dict) and "diagnostic" in source_fingerprints_result:
                    return source_fingerprints_result["diagnostic"]
                source_fingerprints = source_fingerprints_result
            normalized_op = {
                "operation_id": operation_id,
                "kind": "write_file",
                "target": target,
                "content": ensure_final_newline(content),
            }
            if source_fingerprints is not None:
                normalized_op["source_fingerprints"] = source_fingerprints
            normalized.append(
                normalized_op
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


def normalize_source_fingerprints(raw: Any, *, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict) or not raw:
        return {"diagnostic": invalid_operation("source_fingerprints must be a non-empty object", index=index)}
    normalized: dict[str, Any] = {}
    for label, record in raw.items():
        if not isinstance(label, str) or not label:
            return {"diagnostic": invalid_operation("source_fingerprints keys must be non-empty strings", index=index)}
        if not isinstance(record, dict):
            return {"diagnostic": invalid_operation("source_fingerprints records must be objects", index=index)}
        path = record.get("path")
        sha256 = record.get("sha256")
        size_bytes = record.get("size_bytes")
        algorithm = record.get("algorithm", "sha256")
        if not isinstance(path, str) or not path:
            return {"diagnostic": invalid_operation("source_fingerprints records require path", index=index)}
        if algorithm != "sha256" or not isinstance(sha256, str) or not re_fullmatch_sha256(sha256):
            return {"diagnostic": invalid_operation("source_fingerprints records require sha256", index=index)}
        if not isinstance(size_bytes, int) or size_bytes < 0:
            return {"diagnostic": invalid_operation("source_fingerprints records require non-negative size_bytes", index=index)}
        normalized[label] = {
            "path": path,
            "algorithm": "sha256",
            "sha256": sha256,
            "size_bytes": size_bytes,
        }
    return normalized


def re_fullmatch_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


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

    for parent_index, (parent_op, parent_target) in enumerate(write_targets):
        for child_index, (child_op, child_target) in enumerate(write_targets):
            if parent_index == child_index:
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


def capture_write_snapshots(
    operations: list[dict[str, Any]],
    repo_root: Path,
) -> dict[str, dict[str, Any]] | dict[str, Any]:
    snapshots: dict[str, dict[str, Any]] = {}
    for op in operations:
        if op["kind"] != "write_file":
            continue
        target = resolve_candidate_path(op["target"], repo_root)
        rel = repo_relative(target, repo_root)
        if rel in snapshots:
            continue
        try:
            snapshots[rel] = snapshot_write_target(target, repo_root)
        except OSError as exc:
            return {
                "diagnostic": diagnostic(
                    "source_changed",
                    "mutation helper could not snapshot write targets before apply",
                    details={"target": rel, "error": type(exc).__name__},
                    remediation_summary="Retry from a stable repository tree.",
                    remediation_actions=["Inspect the target path.", "Remove symlinks or concurrent edits.", "Retry apply mode."],
                )
            }
    return snapshots


def rollback_applied_writes(touched_paths: list[str], snapshots: dict[str, dict[str, Any]], repo_root: Path) -> list[str]:
    errors: list[str] = []
    for rel in reversed(touched_paths):
        target = resolve_candidate_path(rel, repo_root)
        try:
            original = snapshots.get(rel) or {"exists": False, "created_parent_dirs": []}
            current = snapshot_write_target(target, repo_root)
            if not target_matches_applied_snapshot(current, original):
                errors.append(f"{rel}:source_changed")
                continue
            if not original.get("exists"):
                safe_unlink(target, repo_root)
                errors.extend(remove_created_parent_dirs(original.get("created_parent_dirs", []), repo_root))
            else:
                write_bytes_atomic(
                    target,
                    original["content"],
                    trust_root=repo_root,
                    mode=original.get("mode"),
                )
        except OSError as exc:
            errors.append(f"{rel}:{type(exc).__name__}")
    return errors


def safe_unlink(target: Path, trust_root: Path) -> None:
    opened = open_safe_parent_fd(target, trust_root, create=False)
    if opened is None:
        return
    parent_fd, target_name, _created_dirs = opened
    try:
        try:
            mode = os.stat(target_name, dir_fd=parent_fd, follow_symlinks=False).st_mode
        except FileNotFoundError:
            return
        if stat.S_ISDIR(mode):
            raise OSError("refusing to unlink directory")
        os.unlink(target_name, dir_fd=parent_fd)
        try:
            os.fsync(parent_fd)
        except OSError:
            # Directory fsync is best-effort after unlink; cleanup already succeeded.
            pass
    finally:
        os.close(parent_fd)


def write_file_atomic(target: Path, content: str, *, trust_root: Path | None = None) -> dict[str, Any]:
    return write_bytes_atomic(target, ensure_final_newline(content).encode("utf-8"), trust_root=trust_root)


def write_bytes_atomic(target: Path, content: bytes, *, trust_root: Path | None = None, mode: int | None = None) -> dict[str, Any]:
    created_dirs: list[str] = []
    if trust_root is None:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp_name = f".{target.name}.tmp-{os.getpid()}-{uuid.uuid4().hex}"
        parent_fd = os.open(target.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
        target_name = target.name
    else:
        opened = open_safe_parent_fd(target, trust_root, create=True)
        if opened is None:
            raise OSError("target parent missing")
        parent_fd, target_name, created_dirs = opened
        tmp_name = f".{target_name}.tmp-{os.getpid()}-{uuid.uuid4().hex}"
    tmp_fd = -1
    failure: OSError | None = None
    replaced = False
    applied_mode: int | None = None
    try:
        try:
            if trust_root is not None:
                ensure_safe_write_target_fd(parent_fd, target_name)
            existing_mode = mode if mode is not None else current_file_mode_fd(parent_fd, target_name)
            write_mode = existing_mode if existing_mode is not None else 0o666
            tmp_fd = os.open(
                tmp_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                write_mode,
                dir_fd=parent_fd,
            )
            if existing_mode is not None:
                os.fchmod(tmp_fd, existing_mode)
            applied_mode = stat.S_IMODE(os.fstat(tmp_fd).st_mode)
            with os.fdopen(tmp_fd, "wb") as fh:
                tmp_fd = -1
                fh.write(content)
                fh.flush()
                os.fsync(fh.fileno())
            if trust_root is not None:
                ensure_safe_write_target_fd(parent_fd, target_name)
            os.replace(tmp_name, target_name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
            replaced = True
            try:
                os.fsync(parent_fd)
            except OSError:
                # Directory fsync is best-effort after replace; the atomic swap already succeeded.
                pass
        except OSError as exc:
            failure = exc
            raise
    finally:
        if tmp_fd >= 0:
            try:
                os.close(tmp_fd)
            except OSError:
                pass
        try:
            os.unlink(tmp_name, dir_fd=parent_fd)
        except FileNotFoundError:
            # The temp name is absent after successful replace; cleanup is already complete.
            pass
        except OSError:
            # Best-effort cleanup only; the write outcome is already determined.
            pass
        os.close(parent_fd)
        if trust_root is not None and failure is not None and not replaced and created_dirs:
            cleanup_errors = remove_created_parent_dirs(created_dirs, trust_root)
            if cleanup_errors:
                setattr(failure, "cleanup_errors", cleanup_errors)
    return {
        "digest": hashlib.sha256(content).hexdigest(),
        "mode": applied_mode,
        "created_parent_dirs": created_dirs,
    }


def ensure_safe_write_parent(target: Path, trust_root: Path, *, create: bool = True) -> None:
    opened = open_safe_parent_fd(target, trust_root, create=create)
    if opened is not None:
        os.close(opened[0])


def open_safe_parent_fd(target: Path, trust_root: Path, *, create: bool) -> tuple[int, str, list[str]] | None:
    trust_root = trust_root.resolve(strict=False)
    target = target if target.is_absolute() else trust_root / target
    try:
        relative = target.relative_to(trust_root)
    except ValueError as exc:
        raise OSError("target escapes trust root") from exc
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise OSError("unsafe target path")
    target_name = relative.parts[-1]
    if "/" in target_name or target_name in {"", ".", ".."}:
        raise OSError("unsafe target name")
    root_mode = trust_root.lstat().st_mode
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
        raise OSError("unsafe trust root")

    parent_fd = os.open(trust_root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
    created_dirs: list[str] = []
    current_rel = Path()
    try:
        for part in relative.parts[:-1]:
            current_rel = current_rel / part
            try:
                next_fd = os.open(
                    part,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=parent_fd,
                )
            except FileNotFoundError:
                if not create:
                    os.close(parent_fd)
                    return None
                os.mkdir(part, 0o777, dir_fd=parent_fd)
                created_dirs.append(current_rel.as_posix())
                next_fd = os.open(
                    part,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=parent_fd,
                )
            os.close(parent_fd)
            parent_fd = next_fd
    except Exception:
        os.close(parent_fd)
        raise
    return parent_fd, target_name, created_dirs


def ensure_safe_write_target_fd(parent_fd: int, name: str) -> None:
    if "/" in name or name in {"", ".", ".."}:
        raise OSError("unsafe target name")
    try:
        mode = os.stat(name, dir_fd=parent_fd, follow_symlinks=False).st_mode
    except FileNotFoundError:
        return
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise OSError("unsafe existing target")


def current_file_mode_fd(parent_fd: int, name: str) -> int | None:
    try:
        file_stat = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
        raise OSError("unsafe existing target")
    return stat.S_IMODE(file_stat.st_mode)


def snapshot_write_target(target: Path, repo_root: Path) -> dict[str, Any]:
    created_parent_dirs = missing_parent_dirs(target, repo_root)
    opened = open_safe_parent_fd(target, repo_root, create=False)
    if opened is None:
        return {
            "exists": False,
            "content": None,
            "mode": None,
            "digest": None,
            "created_parent_dirs": created_parent_dirs,
        }
    parent_fd, target_name, _created_dirs = opened
    try:
        try:
            fd = os.open(target_name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
        except FileNotFoundError:
            return {
                "exists": False,
                "content": None,
                "mode": None,
                "digest": None,
                "created_parent_dirs": created_parent_dirs,
            }
        try:
            file_stat = os.fstat(fd)
            if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
                raise OSError("unsafe existing target")
            with os.fdopen(fd, "rb") as stream:
                fd = -1
                content = stream.read()
        finally:
            if fd >= 0:
                os.close(fd)
        return {
            "exists": True,
            "content": content,
            "mode": stat.S_IMODE(file_stat.st_mode),
            "digest": hashlib.sha256(content).hexdigest(),
            "created_parent_dirs": created_parent_dirs,
        }
    finally:
        os.close(parent_fd)


def snapshot_changed_diagnostic(rel: str, target: Path, snapshots: dict[str, dict[str, Any]], repo_root: Path) -> dict[str, Any] | None:
    original = snapshots.get(rel)
    if original is None:
        return None
    try:
        current = snapshot_write_target(target, repo_root)
    except OSError as exc:
        return diagnostic(
            "source_changed",
            "mutation helper could not re-snapshot a write target before apply",
            details={"target": rel, "error": type(exc).__name__},
            remediation_summary="Retry from a stable repository tree.",
            remediation_actions=["Inspect the target path.", "Remove symlinks or concurrent edits.", "Retry apply mode."],
        )
    if original.get("exists") != current.get("exists"):
        changed = True
    elif original.get("exists"):
        changed = original.get("digest") != current.get("digest") or original.get("mode") != current.get("mode")
    else:
        changed = False
    if not changed:
        return None
    return diagnostic(
        "source_changed",
        "mutation helper refused to overwrite a target that changed after snapshot capture",
        details={"target": rel},
        remediation_summary="Retry from a stable repository tree.",
        remediation_actions=["Inspect the target path.", "Retry apply mode after concurrent edits stop."],
    )


def snapshot_changed_diagnostic_after_write(
    rel: str,
    target: Path,
    snapshots: dict[str, dict[str, Any]],
    repo_root: Path,
    *,
    expected_digest: str,
    expected_mode: int | None,
) -> dict[str, Any] | None:
    original = snapshots.setdefault(rel, {"exists": False, "created_parent_dirs": []})
    try:
        applied = snapshot_write_target(target, repo_root)
    except OSError as exc:
        return diagnostic(
            "source_changed",
            "mutation helper could not snapshot the applied write for rollback safety",
            details={"target": rel, "error": type(exc).__name__},
            remediation_summary="Inspect the target path before retrying.",
            remediation_actions=["Review the target file.", "Manually reconcile any partial write.", "Retry from a stable repository tree."],
        )
    if not applied.get("exists"):
        return diagnostic(
            "source_changed",
            "mutation helper wrote a target but could not verify the applied file for rollback safety",
            details={"target": rel},
            remediation_summary="Inspect the target path before retrying.",
            remediation_actions=["Review the target file.", "Manually reconcile any partial write.", "Retry from a stable repository tree."],
        )
    if applied.get("digest") != expected_digest or applied.get("mode") != expected_mode:
        return diagnostic(
            "source_changed",
            "mutation helper wrote a target but observed different content or mode before rollback tracking",
            details={"target": rel},
            remediation_summary="Inspect the target path before retrying.",
            remediation_actions=["Review the target file.", "Manually reconcile any partial write.", "Retry from a stable repository tree."],
        )
    original["applied_digest"] = expected_digest
    original["applied_mode"] = expected_mode
    return None


def target_matches_applied_snapshot(current: dict[str, Any], original: dict[str, Any]) -> bool:
    applied_digest = original.get("applied_digest")
    applied_mode = original.get("applied_mode")
    if not applied_digest:
        return False
    return bool(current.get("exists")) and current.get("digest") == applied_digest and current.get("mode") == applied_mode


def operation_source_fingerprint_diagnostic(operation: dict[str, Any], repo_root: Path) -> dict[str, Any] | None:
    fingerprints = operation.get("source_fingerprints")
    if not isinstance(fingerprints, dict):
        return None
    for label, expected in sorted(fingerprints.items()):
        if not isinstance(expected, dict):
            return source_fingerprint_changed(label, "malformed")
        path_value = expected.get("path")
        if not isinstance(path_value, str) or not path_value:
            return source_fingerprint_changed(label, "missing-path")
        target = resolve_candidate_path(path_value, repo_root)
        if validate_target_path(path_value, repo_root) is not None:
            return source_fingerprint_changed(label, "unsafe-path")
        try:
            opened = open_safe_parent_fd(target, repo_root, create=False)
        except OSError as exc:
            return source_fingerprint_changed(label, type(exc).__name__)
        if opened is None:
            return source_fingerprint_changed(label, "missing-parent")
        parent_fd, target_name, _created_dirs = opened
        try:
            try:
                fd = os.open(target_name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
            except FileNotFoundError:
                return source_fingerprint_changed(label, "missing-file")
            try:
                file_stat = os.fstat(fd)
                if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
                    return source_fingerprint_changed(label, "unsafe-file")
                with os.fdopen(fd, "rb") as stream:
                    fd = -1
                    content = stream.read()
            finally:
                if fd >= 0:
                    os.close(fd)
        finally:
            os.close(parent_fd)
        current_sha256 = hashlib.sha256(content).hexdigest()
        if expected.get("sha256") != current_sha256 or expected.get("size_bytes") != len(content):
            return source_fingerprint_changed(label, "content-changed", path=repo_relative(target, repo_root))
    return None


def source_fingerprint_changed(label: str, reason: str, *, path: str | None = None) -> dict[str, Any]:
    details = {"source": label, "reason": reason}
    if path is not None:
        details["path"] = path
    return diagnostic(
        "source_changed",
        "mutation helper refused to write because a source fingerprint changed after validation",
        details=details,
        remediation_summary="Rerun read-only validation and retry the write from the current packet/body content.",
        remediation_actions=["Regenerate or refresh the validation result.", "Retry the mutation helper from a clean, stable worktree."],
    )


def missing_parent_dirs(target: Path, repo_root: Path) -> list[str]:
    repo_root = repo_root.resolve(strict=False)
    target = target if target.is_absolute() else repo_root / target
    try:
        relative = target.relative_to(repo_root)
    except ValueError as exc:
        raise OSError("target escapes trust root") from exc
    missing: list[str] = []
    current = repo_root
    missing_started = False
    for part in relative.parts[:-1]:
        current = current / part
        rel = current.relative_to(repo_root).as_posix()
        if missing_started:
            missing.append(rel)
            continue
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            missing_started = True
            missing.append(rel)
            continue
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise OSError("unsafe parent path")
    return missing


def remove_created_parent_dirs(relative_dirs: list[str], repo_root: Path) -> list[str]:
    errors: list[str] = []
    for rel in reversed(relative_dirs):
        if not isinstance(rel, str) or not rel:
            continue
        path = resolve_candidate_path(rel, repo_root)
        try:
            path.rmdir()
        except FileNotFoundError:
            continue
        except OSError as exc:
            errors.append(f"{rel}:{type(exc).__name__}")
    return errors


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
        "writes_state": False,
        "mutation": mutation,
    }
    if extra_data:
        data.update(extra_data)
    return data
