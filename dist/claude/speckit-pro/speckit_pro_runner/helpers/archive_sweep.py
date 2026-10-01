"""Read-only Archive Sweep enumeration: which prior specs have a merged pull request.

The stock archive extension archives one feature per run, so the autopilot owns
the sweep: this helper lists `specs/*/spec.md`, drops the current target, and
asks `gh` for each remaining spec's merged pull request. Only a spec with a
readable merged pull request enters `archive_order`; every spec whose evidence
cannot be read is reported as `unknown` and stays active.
"""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any

from .. import cli_probe
from ..cli_probe import BRANCH
from ..envelope import diagnostic, response
from .read_only import resolve_repo_root

SPECS_ROOT = "specs"
ALLOWED_INPUTS = frozenset({"current_target", "repo_root"})
# SpecKit names a feature branch after its spec directory, so a spec name is
# checked with the shared branch pattern before it reaches `gh`.
PR_LIST_LIMIT = "20"
PROBE_TIMEOUT_SECONDS = 30


def probe(root: Path, argv: list[str]) -> dict[str, Any]:
    """Run one fixed read-only `gh` query; any failure to run is reported, not raised."""
    return cli_probe.probe(root, argv, allowed=("gh",), timeout=PROBE_TIMEOUT_SECONDS)


def merged_pr_query(branch: str) -> list[str]:
    return [
        "gh", "pr", "list", "--head", branch, "--state", "merged",
        "--json", "number,url,mergeCommit", "--limit", PR_LIST_LIMIT,
    ]


WINDOWS_ABSOLUTE = re.compile(r"^(?:[A-Za-z]:/|//)")


def canonical_target(raw: Any, repo_root: Path) -> str | None:
    """The current target as a repo-relative POSIX path, or None when unusable."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    value = raw.strip().replace("\\", "/")
    if WINDOWS_ABSOLUTE.match(value):
        return None
    if os.path.isabs(value):
        try:
            value = Path(value).resolve(strict=False).relative_to(repo_root).as_posix()
        except ValueError:
            return None
    path = PurePosixPath(value.rstrip("/"))
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def spec_directories(repo_root: Path) -> list[str]:
    """Names of real (non-symlink) `specs/*` directories holding a regular `spec.md`."""
    specs = repo_root / SPECS_ROOT
    try:
        if not stat.S_ISDIR(specs.lstat().st_mode):
            return []
        names = os.listdir(specs)
    except FileNotFoundError:
        return []
    found: list[str] = []
    for name in names:
        entry = specs / name
        try:
            if not stat.S_ISDIR(entry.lstat().st_mode):
                continue
            if not stat.S_ISREG((entry / "spec.md").lstat().st_mode):
                continue
        except OSError:
            continue
        found.append(name)
    return sorted(found, key=lambda name: name.encode("utf-8"))


def merged_evidence(entries: Any) -> dict[str, Any] | None:
    """The first merged pull request when every entry is well formed, else None."""
    if not isinstance(entries, list):
        return None
    for entry in entries:
        if not isinstance(entry, dict):
            return None
        number = entry.get("number")
        commit = entry.get("mergeCommit")
        if (
            not isinstance(number, int)
            or isinstance(number, bool)
            or not isinstance(entry.get("url"), str)
            or not isinstance(commit, dict)
            or not isinstance(commit.get("oid"), str)
            or not commit["oid"]
        ):
            return None
    if not entries:
        return {}
    first = entries[0]
    return {"pr_number": first["number"], "pr_url": first["url"], "merge_sha": first["mergeCommit"]["oid"]}


def classify(repo_root: Path, name: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "spec_dir": f"{SPECS_ROOT}/{name}",
        "branch": name,
        "merge_evidence": "unknown",
        "pr_number": None,
        "pr_url": None,
        "merge_sha": None,
        "reason": None,
    }
    if not BRANCH.fullmatch(name):
        row["reason"] = "spec directory name is not a usable branch name"
        return row
    result = probe(repo_root, merged_pr_query(name))
    if result.get("exit_status") != 0:
        detail = str(result.get("stderr_tail") or "").splitlines()
        row["reason"] = "gh pr list did not succeed" + (f": {detail[-1][:200]}" if detail else "")
        return row
    try:
        entries = json.loads(str(result.get("stdout_tail") or ""))
    except json.JSONDecodeError:
        row["reason"] = "gh pr list returned output that is not JSON"
        return row
    evidence = merged_evidence(entries)
    if evidence is None:
        row["reason"] = "gh pr list returned an unexpected shape"
        return row
    if not evidence:
        row["merge_evidence"] = "not_merged"
        row["reason"] = "no merged pull request has this head branch"
        return row
    row.update(evidence)
    row["merge_evidence"] = "merged"
    return row


def input_error(request: Any, code: str, message: str, details: dict[str, Any]) -> dict[str, Any]:
    return response(
        "input_error",
        request_id=request.request_id,
        diagnostics=[
            diagnostic(
                code,
                message,
                details=details,
                remediation_summary="Send current_target as the repo-relative current spec directory.",
                remediation_actions=[
                    "Set inputs.current_target to the workflow's Spec Directory, for example specs/007-feature.",
                    "Remove any other input field and retry.",
                ],
            )
        ],
    )


def run_archive_sweep_helper(entry: Any, request: Any) -> dict[str, Any]:
    inputs = request.inputs if isinstance(request.inputs, dict) else {}
    unexpected = sorted(set(inputs) - ALLOWED_INPUTS)
    if unexpected:
        return input_error(request, "invalid_input", "list-archive-candidates got unknown inputs", {"unexpected_inputs": unexpected})
    repo_root = resolve_repo_root(inputs)
    if isinstance(repo_root, dict):
        status = "missing_prerequisite" if repo_root["code"] == "missing_prerequisite" else "input_error"
        return response(status, request_id=request.request_id, diagnostics=[repo_root])
    current = canonical_target(inputs.get("current_target"), repo_root)
    if current is None:
        return input_error(
            request, "invalid_input", "current_target must be a repo-relative spec directory",
            {"field": "current_target"},
        )
    rows = [
        classify(repo_root, name)
        for name in spec_directories(repo_root)
        if f"{SPECS_ROOT}/{name}" != current
    ]

    def dirs(kind: str) -> list[str]:
        return [row["spec_dir"] for row in rows if row["merge_evidence"] == kind]

    data = {
        "helper_id": entry.helper_id,
        "operation": entry.operation,
        "writes_state": False,
        "specs_root": SPECS_ROOT,
        "excluded_current_spec": current,
        "candidates": rows,
        "archive_order": dirs("merged"),
        "not_merged": dirs("not_merged"),
        "unknown": dirs("unknown"),
    }
    return response("ok", request_id=request.request_id, data=data)
