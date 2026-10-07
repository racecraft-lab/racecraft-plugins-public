"""Run-owned Tasks input copies and consumption; G4 owns bounded capture and judgment."""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from ..strict_input import require_fields, require_text
from .read_only import G4InputDrift, checked_g4_judged, check_g4_inputs, g4_input_kind


def snapshot_bytes(directory: str, judged: dict[str, str]) -> dict[str, bytes]:
    """Check and consume snapshot bytes together, never authorize a later path read."""
    with g4_input_kind("snapshot entry"):
        path = Path(directory)
        if not path.is_absolute() or ".." in path.parts:
            raise ValueError("snapshot requires an absolute path")
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700 or info.st_uid != os.getuid():
            raise ValueError("snapshot requires a private owned directory")
    return check_g4_inputs(path, path.parent, judged)


def create_tasks_snapshot(captured: dict[str, bytes], judged: dict[str, str]) -> dict[str, Any]:
    """Exclusively copy checked bytes into a private run directory and rehash the copy."""
    with g4_input_kind("snapshot entry"):
        path = Path(tempfile.mkdtemp(prefix="speckit-tasks-", dir=Path(tempfile.gettempdir()).resolve()))
        directory = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        with g4_input_kind("snapshot checklist entry"):
            os.mkdir("checklists", mode=0o700, dir_fd=directory)
            reports = os.open("checklists", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
        try:
            for name, content in captured.items():
                shared = name in ("spec.md", "plan.md")
                with g4_input_kind(name if shared else "checklist report"):
                    descriptor = os.open(name if shared else name.removeprefix("checklists/"),
                                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                         0o600, dir_fd=directory if shared else reports)
                    with os.fdopen(descriptor, "wb") as stream:
                        if stream.write(content) != len(content):
                            raise OSError("snapshot write incomplete")
        finally:
            os.close(reports)
        with g4_input_kind("snapshot entry"):
            if os.fstat(directory).st_ino != path.lstat().st_ino:
                raise ValueError("snapshot directory replaced")
        snapshot_bytes(str(path), judged)
        return {"snapshot_dir": str(path), "judged": dict(judged)}
    finally:
        os.close(directory)


def bind_tasks_snapshot(data: dict[str, Any], captured: dict[str, bytes], judged: dict[str, str]) -> None:
    """Bind dispatch input paths to private checked copies; retain the live output target."""
    with g4_input_kind("snapshot entry"):
        snapshot = create_tasks_snapshot(captured, judged)
    feature = data["inputs"]["feature_dir"]
    data["inputs"]["tasks_snapshot"] = snapshot
    bound_paths = {feature + "/" + name: snapshot["snapshot_dir"] + "/" + name for name in judged}
    data["readable_files"] = [bound_paths.get(path, path) for path in data["readable_files"]]
    data["readable_files"] += [snapshot["snapshot_dir"] + "/" + name for name in judged if name.startswith("checklists/")]


def run_read_tasks_inputs_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Closed read-tasks-inputs: snapshot_dir and judged; return verified text for direct use."""
    try:
        inputs = require_fields(request.inputs, {"snapshot_dir", "judged"}, "Tasks snapshot inputs")
        directory = require_text(inputs["snapshot_dir"], "snapshot_dir")
        judged = checked_g4_judged(inputs["judged"])
        captured = snapshot_bytes(directory, judged)
        files = {name: content.decode("utf-8", errors="strict") for name, content in captured.items()}
    except G4InputDrift as exc:
        return response("input_error", request_id=request.request_id,
                        diagnostics=[diagnostic("g4_input_drift", str(exc))])
    except (OSError, ValueError):
        return response("input_error", request_id=request.request_id,
                        diagnostics=[diagnostic("g4_input_drift", "Tasks snapshot input kind is unsafe, changed or unreadable")])
    return response("ok", request_id=request.request_id, data={"files": files, "judged": judged})
