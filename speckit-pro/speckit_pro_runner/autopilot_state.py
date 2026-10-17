"""The run-state read/modify/write owner; file publication stays in atomic_write.

This policy module owns existing autopilot-state.json updates for nesting,
formal checkpoints and plan bookkeeping. atomic_write remains format agnostic.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .atomic_write import file_identity, open_safe_parent_fd, snapshot_write_target_fd, write_bytes_atomic
from .strict_input import require_text, unique_object


MAX_STATE_BYTES = 1_048_576
UUID_PATTERN = re.compile(r"[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}")


def snapshot(root: Path, target: Path) -> dict[str, Any]:
    """Capture the bounded existing object through safe directory descriptors."""
    try:
        opened = open_safe_parent_fd(target, root, create=False)
        if opened is None:
            raise ValueError("state_file parent is missing")
        parent_fd, name, _ = opened
        try:
            captured = snapshot_write_target_fd(parent_fd, name, byte_limit=MAX_STATE_BYTES)
            captured["parent"] = file_identity(os.fstat(parent_fd))
            captured["byte_limit"] = MAX_STATE_BYTES
        finally:
            os.close(parent_fd)
        return captured
    except OSError as error:
        raise ValueError(f"state_file must be a readable regular file with no symlink parents: {error}") from error


def update(root: Path, state_file: Any, mutate: Callable[[dict[str, Any]], None]) -> None:
    """Update one existing state object, refusing unsafe targets and stale writes."""
    relative = Path(require_text(state_file, "state_file"))
    if relative.is_absolute() or any(part.casefold() == ".git" for part in relative.parts):
        raise ValueError("state_file must be a repository-relative state path outside .git")
    if relative.name != "autopilot-state.json":
        raise ValueError("state_file must name an autopilot-state.json file")
    target = root / relative
    captured = snapshot(root, target)
    if not captured["exists"]:
        raise ValueError("state_file must already exist")
    state = json.loads(captured["content"], object_pairs_hook=unique_object)
    if not isinstance(state, dict):
        raise ValueError("state_file must hold a JSON object")
    mutate(state)
    content = (json.dumps(state, indent=2, allow_nan=False) + "\n").encode("utf-8")
    write_bytes_atomic(target, content, trust_root=root, expected_snapshot=captured)
