"""Digest-bound Tasks consumers shared by publication, hooks and G5.

The binding is a value passed unchanged by the orchestrator, not a certificate
for a mutable pathname or authentication of an arbitrary caller's input.
"""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from ..strict_input import require_fields, require_text
from ..trusted_io import (
    BOUNDED_TEXT_INPUT_BYTES, TreeEntryReadOptions, read_tree_entry,
    resolve_repo_root, trusted_open_directory,
)


def bind_tasks_text(content: bytes) -> dict[str, str]:
    """Carry the captured snapshot bytes across the JSON boundary without a path."""
    return {"text": content.decode("utf-8", errors="strict"), "sha256": hashlib.sha256(content).hexdigest()}


def checked_tasks_text(raw: Any) -> str:
    """Validate and return the exact text a consumer will use."""
    binding = require_fields(raw, {"text", "sha256"}, "Tasks binding")
    text = binding["text"]
    if not isinstance(text, str) or len(text) > BOUNDED_TEXT_INPUT_BYTES:
        raise ValueError("invalid Tasks text")
    content = text.encode("utf-8", errors="strict")
    if len(content) > BOUNDED_TEXT_INPUT_BYTES or hashlib.sha256(content).hexdigest() != binding["sha256"]:
        raise ValueError("Tasks digest mismatch")
    return text


def check_live_tasks(path: Path, root: Path, binding: dict[str, str]) -> None:
    """A requested live read is bounded and compared; consumers still use bound text."""
    text = checked_tasks_text(binding)
    parent = trusted_open_directory(path.parent, root)
    if parent is None:
        raise ValueError("unsafe Tasks parent")
    try:
        info = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("unsafe Tasks leaf")
        content = read_tree_entry(parent, path.name, info,
                                  options=TreeEntryReadOptions(byte_limit=BOUNDED_TEXT_INPUT_BYTES))[Path()][1]
        if content != text.encode("utf-8"):
            raise ValueError("Tasks live output changed")
    finally:
        os.close(parent)


def run_read_tasks_output_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Return verified text for an after_tasks hook, optionally checking a live read."""
    try:
        fields = {"tasks_binding"} | ({"live_path"} if "live_path" in request.inputs else set())
        inputs = require_fields(request.inputs, fields, "Tasks consumer")
        text = checked_tasks_text(inputs["tasks_binding"])
        if "live_path" in inputs:
            relative = Path(require_text(inputs["live_path"], "live_path"))
            root = resolve_repo_root({})
            if isinstance(root, dict) or relative.is_absolute() or ".." in relative.parts or relative.name != "tasks.md":
                raise ValueError("unsafe Tasks path")
            check_live_tasks(root / relative, root, inputs["tasks_binding"])
    except (OSError, ValueError):
        return response("input_error", request_id=request.request_id,
                        diagnostics=[diagnostic("tasks_output_drift", "Tasks consumer bytes are unsafe, changed or unreadable")],
                        data={"after_hooks_ready": False})
    return response("ok", request_id=request.request_id,
                    data={"text": text, "sha256": inputs["tasks_binding"]["sha256"], "after_hooks_ready": True})
