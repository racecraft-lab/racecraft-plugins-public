"""The run-state read/modify/write owner; file publication stays in atomic_write.

This policy module owns existing autopilot-state.json updates for nesting,
formal checkpoints and plan bookkeeping. atomic_write remains format agnostic.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .atomic_write import file_identity, open_safe_parent_fd, snapshot_write_target_fd, write_bytes_atomic
from .strict_input import require_text, unique_object
from .execution_control import confined_path, execution_control


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


def update(root: Path, state_file: Any, mutate: Callable[[dict[str, Any]], None], *, workflow: str | None = None) -> None:
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
    if workflow is not None:
        refresh_run_facts(root, workflow, state)
    content = (json.dumps(state, indent=2, allow_nan=False) + "\n").encode("utf-8")
    write_bytes_atomic(target, content, trust_root=root, expected_snapshot=captured)


MIRROR_FIELDS = ("ledger_path", "disposition", "reasons", "elapsed_seconds", "checkpoint_due")


def execution_snapshot(root: Path, workflow: str, state: dict[str, Any]) -> dict[str, Any] | None:
    """Read the mirror's bound ledger without creating, resetting, or changing it."""
    mirror = state.get("execution_control")
    if mirror is None:
        return None
    if not isinstance(mirror, dict) or not mirror.get("ledger_path") or not mirror.get("run_id"):
        raise ValueError("execution_control requires its ledger_path and run_id")
    return execution_control(root, {"workflow_file": workflow, "action": "status",
                                   "ledger_path": mirror["ledger_path"], "expected_run_id": mirror["run_id"]}, "read_only")


def refresh_run_facts(root: Path, workflow: str, state: dict[str, Any]) -> None:
    """Project the bound ledger and current UTC time into an existing state."""
    snapshot = execution_snapshot(root, workflow, state)
    if snapshot is not None:
        state["execution_control"] = {key: snapshot[key] for key in MIRROR_FIELDS}
        state["execution_control"]["run_id"] = snapshot["ledger"]["run_id"]
    state["updated_at"] = datetime.now(timezone.utc).isoformat()


def write_state(root: Path, workflow: str, state: dict[str, Any]) -> None:
    """Publish current run facts through the guarded existing-state writer."""
    state_file = str(Path(workflow).with_name("autopilot-state.json"))
    update(root, state_file, lambda current: current.update(state), workflow=workflow)


def mirror_execution_result(root: Path, workflow: str, result: dict[str, Any]) -> None:
    """Refresh an existing status file after an applied execution-control helper call."""
    path = confined_path(root, str(Path(workflow).with_name("autopilot-state.json")))
    if not path.exists():
        return
    state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise ValueError("autopilot state must be a JSON object")
    state["execution_control"] = {key: result[key] for key in MIRROR_FIELDS}
    state["execution_control"]["run_id"] = result["ledger"]["run_id"]
    write_state(root, workflow, state)
