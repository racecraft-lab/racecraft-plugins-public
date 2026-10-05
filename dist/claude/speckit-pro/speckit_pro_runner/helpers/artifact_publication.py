"""Runner-owned artifact publication, final read and cleanup under anchored directories."""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Any

from ..atomic_write import (AtomicWriteOptions, cleanup_atomic_temporaries_at, open_safe_parent_fd,
                           read_file_snapshot_at, write_bytes_atomic_at)
from ..envelope import diagnostic, response
from ..strict_input import require_text
from ..trusted_io import resolve_repo_root, trusted_open_directory
from .artifact_selection import select_artifact_pages

PLANNING_INPUTS = frozenset({"repo_root", "plan_file", "research_file", "design_concept_file"})
INPUTS = PLANNING_INPUTS | {"page_id", "rendered_html", "action", "expected_sha256"}
MAX_PAGE_BYTES = 1024 * 1024
DESCRIPTOR_IO_AVAILABLE = os.name != "nt" and hasattr(os, "O_NOFOLLOW") and os.listdir in os.supports_fd and all(
    operation in os.supports_dir_fd for operation in (os.open, os.stat, os.unlink, os.mkdir, os.rename))


def publication_inputs(inputs: dict[str, Any], root: Path) -> tuple[str, str, bytes | None]:
    if set(inputs) - INPUTS:
        raise ValueError("publish-artifact-page received unknown inputs")
    selection = select_artifact_pages({key: value for key, value in inputs.items() if key in PLANNING_INPUTS}, root)
    identifier = require_text(inputs.get("page_id"), "page_id")
    if identifier not in selection["selected_pages"]:
        raise ValueError("page_id must be a runner-selected draft page")
    action = inputs.get("action", "publish")
    if action == "publish":
        if "expected_sha256" in inputs:
            raise ValueError("expected_sha256 is only supported for cleanup")
        content = require_text(inputs.get("rendered_html"), "rendered_html").encode("utf-8")
        if len(content) > MAX_PAGE_BYTES:
            raise ValueError("rendered_html exceeds the artifact page byte limit")
    elif action == "cleanup":
        if "rendered_html" in inputs:
            raise ValueError("cleanup does not accept rendered_html")
        expected = inputs.get("expected_sha256")
        if expected is not None and (not isinstance(expected, str) or len(expected) != 64
                                     or any(character not in "0123456789abcdef" for character in expected)):
            raise ValueError("expected_sha256 must be a lowercase SHA-256 digest")
        content = None
    else:
        raise ValueError("action must be publish or cleanup")
    return action, selection["output_paths"][identifier], content


def read_artifact_at(directory_fd: int, name: str, identity: list[int] | None = None) -> tuple[bytes, list[int]]:
    snapshot = read_file_snapshot_at(directory_fd, name, MAX_PAGE_BYTES)
    if not snapshot["exists"]:
        raise FileNotFoundError("artifact is absent")
    if identity is not None and snapshot["file_identity"] != identity:
        raise ValueError("published artifact identity differs from the written temporary")
    return snapshot["content"], snapshot["file_identity"]


def verify_directory_binding(directory: Path, root: Path, identity: list[int]) -> None:
    fd = trusted_open_directory(root / directory, root)
    if fd is None:
        raise ValueError("artifact directory binding is unsafe")
    try:
        observed = os.fstat(fd)
        if [observed.st_dev, observed.st_ino] != identity:
            raise ValueError("artifact directory identity changed during publication")
    finally:
        os.close(fd)


def cleanup_owned_artifact(directory_fd: int, name: str, identity: list[int]) -> bool:
    try:
        observed = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    if [observed.st_dev, observed.st_ino] != identity or not stat.S_ISREG(observed.st_mode):
        return False
    os.unlink(name, dir_fd=directory_fd)
    return True


def publish_artifact_at(directory_fd: int, name: str, content: bytes) -> dict[str, Any]:
    receipt = write_bytes_atomic_at(directory_fd, name, content, AtomicWriteOptions(mode=0o644, verify_content=True))
    try:
        final, identity = read_artifact_at(directory_fd, name, receipt["file_identity"])
        if final != content:
            raise ValueError("published artifact bytes differ from the rendered page")
        return {"sha256": receipt["digest"], "file_identity": identity, "verified_html": final.decode("utf-8")}
    except (OSError, ValueError):
        cleanup_owned_artifact(directory_fd, name, receipt["file_identity"])
        raise


def apply_artifact_operation(action: str, path: str, content: bytes | None,
                             inputs: dict[str, Any], root: Path) -> dict[str, Any]:
    if not DESCRIPTOR_IO_AVAILABLE:
        raise OSError("descriptor-relative artifact operations are unavailable; report an artifact gap")
    opened = open_safe_parent_fd(root / path, root, create=action == "publish")
    if opened is None:
        return {"outcome": "removed", "removed": False, "writes_state": False}
    directory_fd, name, _ = opened
    try:
        directory_stat = os.fstat(directory_fd)
        directory_identity = [directory_stat.st_dev, directory_stat.st_ino]
        verify_directory_binding(Path(path).parent, root, directory_identity)
        if content is None:
            try:
                current, identity = read_artifact_at(directory_fd, name)
            except FileNotFoundError:
                temporaries = cleanup_atomic_temporaries_at(directory_fd, name)
                return {"outcome": "removed", "removed": False, "removed_temporaries": temporaries,
                        "writes_state": bool(temporaries)}
            expected = inputs.get("expected_sha256")
            if expected is not None and hashlib.sha256(current).hexdigest() != expected:
                raise ValueError("cleanup digest differs from the current-run artifact")
            temporaries = cleanup_atomic_temporaries_at(directory_fd, name)
            removed = cleanup_owned_artifact(directory_fd, name, identity)
            return {"outcome": "removed", "removed": removed, "removed_temporaries": temporaries,
                    "writes_state": removed or bool(temporaries)}
        receipt = publish_artifact_at(directory_fd, name, content)
        try:
            verify_directory_binding(Path(path).parent, root, directory_identity)
        except (OSError, ValueError):
            cleanup_owned_artifact(directory_fd, name, receipt["file_identity"])
            raise
        return {"outcome": "generated", "writes_state": True, **receipt}
    finally:
        os.close(directory_fd)


def run_artifact_publication_helper(entry: Any, request: Any) -> dict[str, Any]:
    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    try:
        action, path, content = publication_inputs(request.inputs, root)
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
        return publication_error(request.request_id, "input_error", str(error))
    data = {"helper_id": entry.helper_id, "operation": entry.operation, "mode": request.mode,
            "action": action, "path": path, "writes_state": False, "outcome": "dry_run"}
    if request.mode == "apply":
        try:
            data.update(apply_artifact_operation(action, path, content, request.inputs, root))
        except (OSError, ValueError, RuntimeError) as error:
            data.pop("writes_state")
            data["writes_state_unknown"] = True
            data["outcome"] = "gap"
            return publication_error(request.request_id, "expected_failure", str(error), data)
    return response("ok", request_id=request.request_id, data=data)


def publication_error(request_id: str, status: str, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return response(status, request_id=request_id, data=data, diagnostics=[diagnostic(
        "artifact_publication_invalid", message, remediation_summary="Record an artifact gap; use runner-owned I/O.",
        remediation_actions=["Correct the inputs or directory state and retry publication through the runner."])])
