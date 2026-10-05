"""Scaffold's quality-gates proposal (ADR 0007): measure, show, write only on a yes.

``dry_run`` reads the measurement report the CRAP script left at ``REPORT_FILE``
and returns the proposed file and the files whose functions would fail it
today; it writes nothing. ``apply`` takes the user's answer as a boolean
``confirmed``: ``true`` writes ``.specify/quality-gates.json``, ``false`` writes
nothing and stores no decline. Either way the scratch report is removed. A
file that is already valid is never overwritten.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import quality_gates
from ..atomic_write import write_bytes_atomic
from ..envelope import diagnostic, response
from ..strict_input import SelectionError
from ..trusted_io import find_repo_root, trusted_bytes, trusted_text

REPORT_FILE = ".specify/quality-gates-report.json"
INPUT_KEYS = frozenset({"measured", "confirmed"})
MAX_FAILING_FILES = 20


def measured_report(root: Path, measured: bool) -> Any:
    """The scratch report's JSON, or an empty report when nothing was measured or it cannot be read."""
    text = trusted_text(root / REPORT_FILE, root) if measured else None
    try:
        return json.loads(text) if text is not None else {}
    except ValueError:
        return {}


def failing_files(report: Any, ceiling: int, root: Path) -> list[dict[str, Any]]:
    """Group the measured functions above ``ceiling`` by repository-relative file."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for fn in report.get("functions", []) if isinstance(report, dict) else []:
        complexity = fn.get("complexity") if isinstance(fn, dict) else None
        if (not isinstance(complexity, int) or isinstance(complexity, bool) or complexity <= ceiling
                or not isinstance(fn.get("file"), str)):
            continue
        path = Path(fn["file"])
        try:
            path = path.relative_to(root) if path.is_absolute() else path
        except ValueError:
            path = Path(path.name)
        groups.setdefault(path.as_posix(), []).append({"name": str(fn.get("name", "?")), "complexity": complexity})
    return [{"file": name, "functions": sorted(groups[name], key=lambda row: -row["complexity"])}
            for name in sorted(groups)]


def propose(report: Any) -> dict[str, Any]:
    proposal = quality_gates.recommend(report)
    proposal["basis"]["recorded"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return proposal


def input_problem(request: Any) -> str | None:
    inputs = request.inputs
    if not isinstance(inputs, dict) or not inputs.keys() <= INPUT_KEYS or not isinstance(inputs.get("measured"), bool):
        return f"inputs take {sorted(INPUT_KEYS)}; measured must be true or false"
    if request.mode == "apply" and not isinstance(inputs.get("confirmed"), bool):
        return "apply needs confirmed: true after a yes, false after a decline"
    if request.mode == "dry_run" and "confirmed" in inputs:
        return "a dry run takes no confirmed answer"
    return None


def describe(root: Path, entry: Any, request: Any) -> tuple[dict[str, Any], Any]:
    """The observed file status, the proposal (None when a confirmed file stands) and the files it would fail."""
    status, problems, _ = quality_gates.observe(trusted_text(root / quality_gates.FILE_PATH, root))
    report = measured_report(root, request.inputs["measured"])
    proposal = None if status == "present" else propose(report)
    data: dict[str, Any] = {"helper_id": entry.helper_id, "operation": entry.operation, "mode": request.mode,
                            "writes_state": False, "file": quality_gates.FILE_PATH, "status": status,
                            "problems": problems, "proposal": proposal}
    if proposal is not None:
        rows = failing_files(report, proposal["thresholds"]["complexity"], root)
        data["failing_files"] = rows[:MAX_FAILING_FILES]
        data["failing_file_count"] = len(rows)
        data["failing_function_count"] = sum(len(row["functions"]) for row in rows)
    return data, proposal


def write_proposal(root: Path, proposal: dict[str, Any]) -> None:
    write_bytes_atomic(root / quality_gates.FILE_PATH, (json.dumps(proposal, indent=2) + "\n").encode("utf-8"),
                       trust_root=root, mode=0o644)


def run_quality_gates_proposal_helper(entry: Any, request: Any) -> dict[str, Any]:
    root = find_repo_root(Path.cwd())
    if root is None or not (root / ".specify").is_dir():
        return response("missing_prerequisite", request_id=request.request_id, diagnostics=[diagnostic(
            "missing_prerequisite", "the quality-gates proposal needs a SpecKit project with a .specify directory",
            remediation_summary="Initialize SpecKit in this project, then rerun scaffold.",
            remediation_actions=["Run the SpecKit install flow.", "Rerun scaffold."])])
    problem = input_problem(request)
    if problem is not None:
        return response("input_error", request_id=request.request_id, diagnostics=[diagnostic(
            "invalid_input", problem, remediation_summary="Send the fields this helper takes.",
            remediation_actions=["Correct the named field.", "Retry the request."])])
    data, proposal = describe(root, entry, request)
    if request.mode != "apply":
        return response("ok", request_id=request.request_id, data=data)
    data["outcome"] = "already_present" if proposal is None else "declined"
    if proposal is not None and request.inputs["confirmed"]:
        try:
            write_proposal(root, proposal)
        except (OSError, SelectionError) as error:
            return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diagnostic(
                "write_failure", f"the quality-gates file could not be written: {getattr(error, 'strerror', None) or error}",
                remediation_summary="Scaffold continues on the shipped defaults; the next scaffold offers again.",
                remediation_actions=["Report the failure in the scaffold closing report.",
                                     "Fix the .specify directory and rerun scaffold."])])
        data["outcome"] = "written"
        data["writes_state"] = True
    data["report_removed"] = consume_report(root)
    return response("ok", request_id=request.request_id, data=data)


def consume_report(root: Path) -> bool:
    """Remove the scratch report so a decline leaves nothing behind; True when it is gone.

    A report that cannot be read safely (a link, an unreadable file) or removed stays, and the caller learns so.
    """
    if trusted_bytes(root / REPORT_FILE, root) is None:
        return not os.path.lexists(root / REPORT_FILE)
    try:
        os.unlink(root / REPORT_FILE)
    except OSError:
        return False
    return True
