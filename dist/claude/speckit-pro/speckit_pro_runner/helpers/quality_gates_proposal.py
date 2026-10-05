"""Scaffold's quality-gates proposal (ADR 0007): measure, show, write only on a yes.

``dry_run`` reads the measurement report the CRAP script left at ``REPORT_FILE``
and returns the proposed file and the files whose functions would fail it
today; it writes nothing. ``apply`` takes the user's answer as a boolean
``confirmed``: ``true`` writes ``.specify/quality-gates.json``, ``false`` writes
nothing and stores no decline. The scratch report is removed after every apply. A
file that is already valid is never overwritten.
"""

from __future__ import annotations

import json
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import quality_gates
from ..atomic_write import write_bytes_atomic
from ..canonical_json import canonical_bytes
from ..envelope import diagnostic, response
from ..strict_input import SelectionError
from ..trusted_io import find_repo_root, trusted_text

REPORT_FILE = ".specify/quality-gates-report.json"
INPUT_KEYS = frozenset({"measured", "confirmed", "proposal_digest"})
MAX_FAILING_FILES = 20
MAX_FAILING_FUNCTIONS = 20
MAX_PATH_LENGTH = 400
MAX_NAME_LENGTH = 200


def measured_report(root: Path, measured: bool) -> Any:
    """The scratch report's JSON, or an empty report when nothing was measured or it cannot be read."""
    text = trusted_text(root / REPORT_FILE, root) if measured else None
    try:
        return json.loads(text) if text is not None else {}
    except (ValueError, RecursionError):
        return {}


def report_path(value: Any, root: Path) -> str | None:
    """Return a bounded checkout-relative display path, including for in-checkout absolute inputs."""
    if (not isinstance(value, str) or not value or len(value) > MAX_PATH_LENGTH
            or "\\" in value or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        return None
    path = Path(value)
    if ".." in path.parts:
        return None
    try:
        return (root / path).resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError, RuntimeError):
        return None


def failing_files(report: Any, ceiling: int, root: Path) -> list[dict[str, Any]]:
    """Group the measured functions above ``ceiling`` by repository-relative file."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for fn in quality_gates.measured_functions(report):
        complexity = fn["complexity"]
        crap = fn.get("crap")
        crap_failure = (isinstance(crap, (int, float)) and not isinstance(crap, bool)
                        and quality_gates.SHIPPED_DEFAULTS["crap"] < crap <= 10**18)
        path = report_path(fn.get("file"), root)
        if path is None or (complexity <= ceiling and not crap_failure):
            continue
        name = fn.get("name")
        name = name if isinstance(name, str) else "?"
        row: dict[str, Any] = {"name": "".join(char for char in name[:MAX_NAME_LENGTH] if char.isprintable()),
               "complexity": complexity}
        if crap_failure:
            row["crap"] = crap
        groups.setdefault(path, []).append(row)
    rows: list[dict[str, Any]] = [{"file": name, "functions": sorted(groups[name], key=lambda row: -row["complexity"])}
            for name in groups]
    return sorted(rows, key=lambda row: (-row["functions"][0]["complexity"], row["file"]))


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
    if request.mode == "apply" and inputs.get("confirmed") is True and not isinstance(inputs.get("proposal_digest"), str):
        return "a yes needs proposal_digest from the displayed dry run"
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
        data["proposal_digest"] = hashlib.sha256(canonical_bytes(proposal)).hexdigest()
        rows = failing_files(report, proposal["thresholds"]["complexity"], root)
        data["failing_files"] = rows[:MAX_FAILING_FILES]  # worst offenders first
        data["failing_files_truncated"] = len(rows) > MAX_FAILING_FILES
        data["failing_file_count"] = len(rows)
        data["failing_function_count"] = sum(len(row["functions"]) for row in rows)
        for row in data["failing_files"]:
            row["functions_truncated"] = len(row["functions"]) > MAX_FAILING_FUNCTIONS
            row["functions"] = row["functions"][:MAX_FAILING_FUNCTIONS]
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
        if request.inputs["proposal_digest"] != data["proposal_digest"]:
            data["outcome"] = "proposal_changed"
            data["report_removed"] = consume_report(root)
            return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diagnostic(
                "proposal_changed", "The proposal changed after confirmation; no file was written.",
                remediation_summary="Continue on shipped defaults; the next scaffold offers again.",
                remediation_actions=["Report the changed proposal.", "Rerun scaffold to confirm a fresh proposal."])])
        try:
            write_proposal(root, proposal)
        except (OSError, SelectionError) as error:
            data["outcome"] = "write_failed"
            data["report_removed"] = consume_report(root)
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
    """Remove the scratch report so a decline leaves nothing behind; True when it is gone."""
    try:
        os.unlink(root / REPORT_FILE)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return True
