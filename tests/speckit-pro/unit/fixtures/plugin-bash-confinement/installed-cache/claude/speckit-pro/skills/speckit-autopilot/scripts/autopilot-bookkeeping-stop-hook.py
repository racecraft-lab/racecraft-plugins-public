#!/usr/bin/env python3
"""Stop hook: block only while the active workflow file's status table contradicts its own gate evidence.

Scoped and fail-open. The hook is a no-op unless the project has an autopilot
state file whose run status is in flight and which names a workflow file that
exists. Every unexpected condition -- missing state, unparseable payload,
unreadable file, import failure -- exits 0, because a hook that cannot run must
never strand an operator. The hard guarantee lives in
``tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py``,
which runs in CI and cannot be skipped by any agent.

Blocking contract, identical on both platforms: exit 0 and emit
``{"decision": "block", "reason": ...}`` on stdout, which both platforms read
on a successful exit. Exit 2 is deliberately NOT used: ``python3`` itself exits
2 when it cannot open the script, so a plugin-root that fails to resolve would
be indistinguishable from a real block and would strand the operator with an
interpreter error as the reason. This script therefore never returns nonzero,
and the hook command lines swallow any launch failure. The reason is also
written to stderr as a diagnostic.

Re-entry is bounded. Codex supplies ``stop_hook_active`` in the Stop payload;
Claude Code documents no such field, so Claude sessions are keyed by
``session_id`` into a temp-directory marker and the hook blocks at most once per
session per workflow file.

Both platforms export ``CLAUDE_PLUGIN_ROOT`` into the hook process, but only
Claude Code documents substituting it inside the command string, so this script
never depends on that substitution: it locates its sibling validator relative to
its own resolved path.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

STATE_CANDIDATES = (
    Path(".specify") / "autopilot-state.json",
    Path("docs") / "ai" / "specs" / ".process" / "autopilot-state.json",
)
# No shipped contract requires a top-level ``status``: the canonical
# state shape carries ``status`` only per plan step. Gating on an
# allowlist of in-flight values would therefore make this hook inert on
# every project that follows the contract exactly. Skip only when the run
# declares itself finished; absent or unrecognized means "still running".
FINISHED_STATUSES = frozenset({"completed", "completed_pr_open", "completed_archived"})
COVERAGE_VALIDATOR = Path(__file__).resolve().parent / "validate-autopilot-phase-coverage.py"
MARKER_PREFIX = "speckit-autopilot-bookkeeping-stop-"


def _payload() -> dict[str, object]:
    try:
        raw = sys.stdin.read()
    except OSError:
        return {}
    try:
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _project_root(payload: dict[str, object]) -> Path:
    for key in ("cwd", "project_dir", "workspace_root"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            candidate = Path(value)
            if candidate.is_dir():
                return candidate
    return Path.cwd()


def _state_file(root: Path) -> tuple[Path, dict[str, object]] | None:
    """Pick the state file that actually names a workflow, not merely the first one.

    A project can carry more than one ``autopilot-state.json`` -- a legacy
    ``.specify/`` copy alongside the workflow-directory copy the run writes.
    Only the one declaring ``workflow_file`` can drive this hook, so a candidate
    without it must never shadow one that has it.
    """
    fallback: tuple[Path, dict[str, object]] | None = None
    for relative in STATE_CANDIDATES:
        candidate = root / relative
        if not candidate.is_file():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        declared = data.get("workflow_file")
        if isinstance(declared, str) and declared:
            return candidate, data
        if fallback is None:
            fallback = (candidate, data)
    return fallback


def _workflow_file(root: Path, state: dict[str, object]) -> Path | None:
    declared = state.get("workflow_file")
    if not isinstance(declared, str) or not declared:
        return None
    candidate = (root / declared).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def _coverage_module():
    spec = importlib.util.spec_from_file_location(
        "speckit_autopilot_phase_coverage", COVERAGE_VALIDATOR
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _already_blocked(payload: dict[str, object], workflow: Path) -> bool:
    """Bounded re-entry guard: one block per session per workflow file.

    Returning True suppresses the block. When the payload carries neither
    ``stop_hook_active`` nor a usable ``session_id`` there is no way to bound
    re-entry, so the hook declines to block rather than risk an unbounded
    continuation loop -- the same fail-open principle as the outer guard.
    """
    if payload.get("stop_hook_active") is True:
        return True
    session = payload.get("session_id")
    if not isinstance(session, str) or not session:
        return True
    digest = hashlib.sha256(f"{session}\n{workflow}".encode("utf-8")).hexdigest()[:32]
    marker = Path(tempfile.gettempdir()) / f"{MARKER_PREFIX}{digest}"
    if marker.exists():
        return True
    try:
        marker.touch()
    except OSError:
        # The bound cannot be recorded, so blocking now would repeat forever.
        return True
    return False


def main() -> int:
    payload = _payload()
    try:
        root = _project_root(payload)
        located = _state_file(root)
        if located is None:
            return 0
        _state_path, state = located
        status = state.get("status")
        if isinstance(status, str) and status in FINISHED_STATUSES:
            return 0
        workflow = _workflow_file(root, state)
        if workflow is None:
            return 0
        module = _coverage_module()
        if module is None:
            return 0
        errors = module.workflow_status_evidence_errors(
            workflow.read_text(encoding="utf-8")
        )
        if not errors:
            return 0
        if _already_blocked(payload, workflow):
            return 0
    except Exception:  # noqa: BLE001 - a hook that cannot run must not block
        return 0

    try:
        relative = workflow.relative_to(root.resolve()).as_posix()
    except ValueError:
        relative = os.path.relpath(workflow, root.resolve())
    reason = (
        f"Autopilot bookkeeping is inconsistent in {relative}. "
        "Update the Workflow Overview status rows to match the gate evidence "
        "recorded in the same file, then stop again:\n  - "
        + "\n  - ".join(errors)
    )
    sys.stderr.write(reason + "\n")
    print(json.dumps({"decision": "block", "reason": reason}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
