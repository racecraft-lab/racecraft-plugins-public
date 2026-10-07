"""Run-owned Tasks input copies and consumption; G4 owns bounded capture and judgment."""

from __future__ import annotations

import os
import stat
import tempfile
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from ..atomic_write import WriteBinding, ensure_safe_write_target_fd, snapshot_write_target_fd, write_bytes_atomic
from ..trusted_io import BOUNDED_TEXT_INPUT_BYTES, read_tree_entry, resolve_repo_root, trusted_open_directory
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
    """Bind dispatch input paths to private checked copies; bind the run-owned output directory."""
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


def checked_feature_identity(raw: Any) -> dict[str, int]:
    """Accept only G4's device/inode pair, without echoing rejected caller values."""
    with g4_input_kind("feature entry"):
        identity = require_fields(raw, {"device", "inode"}, "feature identity")
        if any(type(value) is not int or value < 0 for value in identity.values()):
            raise ValueError("invalid feature identity")
        return dict(identity)


def open_tasks_parent(feature: Path, root: Path, identity: dict[str, int], stack: ExitStack) -> int:
    """Acquire and verify a contained parent; the caller holds it until publication ends."""
    with g4_input_kind("feature entry"):
        descriptor = trusted_open_directory(feature, root)
        if descriptor is None:
            raise ValueError("unsafe feature entry")
        stack.callback(os.close, descriptor)
        info = os.fstat(descriptor)
        if (info.st_dev, info.st_ino) != (identity["device"], identity["inode"]):
            raise ValueError("replaced feature entry")
        return descriptor


def check_tasks_parent(feature: Path, root: Path, identity: dict[str, int]) -> None:
    """Reverify the G4 directory identity without retaining a cross-process descriptor."""
    with ExitStack() as stack:
        open_tasks_parent(feature, root, identity, stack)


def tasks_output_failure(request_id: str | None, published: bool, exc: Exception) -> dict[str, Any]:
    """Report whether a failed publication may already have reached disk, with sanitized diagnostics."""
    kind = str(exc) if isinstance(exc, G4InputDrift) else "Tasks output kind is unsafe, changed or unreadable"
    if published:
        return response("expected_failure", request_id=request_id,
                        diagnostics=[diagnostic("tasks_output_unconfirmed", kind)],
                        data={"publication": "unconfirmed", "published": "tasks.md"})
    return response("input_error", request_id=request_id,
                    diagnostics=[diagnostic("tasks_output_unsafe", kind)])


def run_publish_tasks_output_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Publish only snapshot tasks.md through the G4-bound parent, using the atomic writer."""
    published = False
    try:
        with g4_input_kind("tasks.md"):
            inputs = require_fields(request.inputs, {"feature_dir", "snapshot_dir", "feature_identity"}, "Tasks output")
            feature_name = require_text(inputs["feature_dir"], "feature_dir")
            relative = Path(feature_name)
            if relative.is_absolute() or ".." in relative.parts or not relative.parts:
                raise ValueError("unsafe output parent")
            directory = require_text(inputs["snapshot_dir"], "snapshot_dir")
        identity = checked_feature_identity(inputs["feature_identity"])
        root = resolve_repo_root({})
        if isinstance(root, dict):
            raise G4InputDrift("G4 input drift: feature entry")
        feature = root / relative
        with ExitStack() as stack:
            parent = open_tasks_parent(feature, root, identity, stack)
            with g4_input_kind("snapshot tasks.md"):
                path = Path(directory)
                info = path.lstat()
                if not path.is_absolute() or ".." in path.parts or not stat.S_ISDIR(info.st_mode):
                    raise ValueError("unsafe snapshot entry")
                if stat.S_IMODE(info.st_mode) != 0o700 or info.st_uid != os.getuid():
                    raise ValueError("unsafe snapshot entry")
                source = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                stack.callback(os.close, source)
                opened = os.fstat(source)
                if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                    raise ValueError("changed snapshot entry")
                leaf = os.stat("tasks.md", dir_fd=source, follow_symlinks=False)
                if not stat.S_ISREG(leaf.st_mode):
                    raise ValueError("unsafe output")
                content = read_tree_entry(source, "tasks.md", leaf, byte_limit=BOUNDED_TEXT_INPUT_BYTES)[Path()][1]
                if content is None:
                    raise ValueError("missing output")
                content.decode("utf-8", errors="strict")
            with g4_input_kind("tasks.md"):
                ensure_safe_write_target_fd(parent, "tasks.md", single_link=True)
                expected = snapshot_write_target_fd(parent, "tasks.md")
                # A rename replaces the leaf rather than opening/truncating its target.
                # The parent descriptor and expected parent identity constrain every write.
                expected.pop("identity", None)
                expected["parent"] = (identity["device"], identity["inode"])
            check_tasks_parent(feature, root, identity)
            with g4_input_kind("tasks.md"):
                result = write_bytes_atomic(feature / "tasks.md", content, trust_root=root,
                                            expected_snapshot=expected, binding=WriteBinding(parent, True,
                                                lambda: check_tasks_parent(feature, root, identity)))
            published = True
            check_tasks_parent(feature, root, identity)
    except (G4InputDrift, OSError, ValueError) as exc:
        return tasks_output_failure(request.request_id, published, exc)
    return response("ok", request_id=request.request_id,
                    data={"published": "tasks.md", "digest": result["digest"], "after_hooks_ready": True})
