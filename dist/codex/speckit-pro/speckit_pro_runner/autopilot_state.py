"""One-run state projections; execution-control retains ownership of ledger accounting."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .atomic_write import write_bytes_atomic
from .execution_control import confined_path, execution_control

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


def write_state(root: Path, workflow: str, state: dict[str, Any]) -> None:
    """Publish state with current UTC time and ledger-derived run facts, preserving plan/status."""
    snapshot = execution_snapshot(root, workflow, state)
    recorded = dict(state)
    if snapshot is not None:
        recorded["execution_control"] = {key: snapshot[key] for key in MIRROR_FIELDS}
        recorded["execution_control"]["run_id"] = snapshot["ledger"]["run_id"]
    recorded["updated_at"] = datetime.now(timezone.utc).isoformat()
    path = confined_path(root, str(Path(workflow).with_name("autopilot-state.json")))
    write_bytes_atomic(path, (json.dumps(recorded, indent=2) + "\n").encode("utf-8"), trust_root=root)


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
