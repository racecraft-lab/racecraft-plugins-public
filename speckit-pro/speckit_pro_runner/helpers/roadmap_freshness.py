"""Scaffold roadmap freshness: is the checkout's roadmap the one on the remote default branch?

Scaffold parses the technical roadmap from the session checkout. A checkout that
sits behind the remote default branch yields a stale entry and misleading gate
results. This helper fetches the remote default branch, compares the roadmap file
in the checkout with the one at the remote revision, and returns one verdict:

- `proceed`: the two files are identical. `base_revision` is the remote default
  branch revision, the revision a new spec worktree branch is based on.
- `stop`: they differ (`stale`), or the comparison could not be made
  (`unverified`). `cause` names why and `stop_message` carries both revisions.

The fetch updates only the object database and the remote-tracking ref; no
working-tree file, branch, or worktree changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import cli_probe
from ..cli_probe import BRANCH
from ..envelope import diagnostic, response
from .archive_sweep import canonical_target
from .read_only import resolve_repo_root

ALLOWED_INPUTS = frozenset({"roadmap_path", "repo_root"})
PROBE_TIMEOUT_SECONDS = 60
PREFERRED_REMOTE = "origin"
HEAD_REF_PREFIX = "ref: refs/heads/"


def probe(root: Path, argv: list[str]) -> dict[str, Any]:
    """Run one fixed read-only `git` query; any failure to run is reported, not raised."""
    return cli_probe.probe(root, argv, allowed=("git",), timeout=PROBE_TIMEOUT_SECONDS)


def git_output(root: Path, *args: str) -> str | None:
    """The trimmed stdout of a succeeding `git` query, else None."""
    result = probe(root, ["git", *args])
    return str(result["stdout_tail"]) if result.get("exit_status") == 0 else None


def choose_remote(root: Path) -> str | None:
    remotes = (git_output(root, "remote") or "").split()
    if PREFERRED_REMOTE in remotes:
        return PREFERRED_REMOTE
    return remotes[0] if len(remotes) == 1 else None


def remote_head(root: Path, remote: str) -> tuple[str, str] | None:
    """The remote default branch name and its revision, from the live remote."""
    listing = git_output(root, "ls-remote", "--symref", remote, "HEAD")
    branch = revision = ""
    for line in (listing or "").splitlines():
        fields = line.split("\t")
        if line.startswith(HEAD_REF_PREFIX):
            branch = fields[0][len(HEAD_REF_PREFIX):]
        elif len(fields) == 2 and fields[1] == "HEAD":
            revision = fields[0]
    if not BRANCH.fullmatch(branch) or not revision:
        return None
    return branch, revision


def outcome(roadmap: str, status: str, cause: str | None, **fields: Any) -> dict[str, Any]:
    stopped = status != "current"
    data: dict[str, Any] = {
        "helper_id": "check-roadmap-freshness",
        "operation": "check-roadmap-freshness",
        "writes_state": False,
        "roadmap_path": roadmap,
        "freshness_status": status,
        "cause": cause,
        "verdict": "stop" if stopped else "proceed",
    }
    data.update(fields)
    if stopped:
        data["stop_message"] = stop_message(roadmap, cause, data)
    return data


def stop_message(roadmap: str, cause: str | None, data: dict[str, Any]) -> str:
    remote_ref = f"{data.get('remote')}/{data.get('default_branch')}"
    checkout, remote = data.get("checkout_revision"), data.get("remote_revision")
    revisions = f"checkout revision {checkout}, {remote_ref} revision {remote}"
    if cause == "checkout_behind_remote":
        return (
            f"Stale checkout: {roadmap} differs from {remote_ref} and the checkout is behind it "
            f"({revisions}). Update the checkout to {remote_ref}, then rerun scaffold."
        )
    if cause == "roadmap_differs_from_remote":
        return (
            f"{roadmap} in the checkout differs from {remote_ref}, and the checkout is not behind it "
            f"({revisions}). Land or discard the local roadmap change, then rerun scaffold."
        )
    if cause == "roadmap_missing_on_remote_default":
        return (
            f"{roadmap} does not exist on {remote_ref} ({revisions}). "
            "Push the roadmap to the default branch, then rerun scaffold."
        )
    return (
        f"Cannot compare {roadmap} with the remote default branch ({cause}). "
        "Fix the remote and rerun scaffold; scaffold does not parse an unverified roadmap."
    )


def check_freshness(root: Path, roadmap: str) -> dict[str, Any]:
    """Compare the checkout's roadmap with the remote default branch's, after a fetch."""
    remote = choose_remote(root)
    if remote is None or not BRANCH.fullmatch(remote):
        return outcome(roadmap, "unverified", "no_remote")
    head = remote_head(root, remote)
    if head is None:
        return outcome(roadmap, "unverified", "remote_unreachable", remote=remote)
    branch, remote_revision = head
    fetched = probe(root, ["git", "fetch", "--quiet", "--no-tags", "--no-write-fetch-head", remote, f"refs/heads/{branch}"])
    checkout_revision = git_output(root, "rev-parse", "HEAD")
    if fetched.get("exit_status") != 0 or git_output(root, "cat-file", "-e", f"{remote_revision}^{{commit}}") is None:
        return outcome(roadmap, "unverified", "remote_unreachable", remote=remote, default_branch=branch)
    fields: dict[str, Any] = {
        "remote": remote,
        "default_branch": branch,
        "checkout_revision": checkout_revision,
        "remote_revision": remote_revision,
    }
    checkout_blob = git_output(root, "hash-object", "--", roadmap)
    remote_blob = git_output(root, "rev-parse", "--verify", "--quiet", f"{remote_revision}:./{roadmap}")
    fields.update(checkout_roadmap_blob=checkout_blob, remote_roadmap_blob=remote_blob)
    if checkout_blob is None or checkout_revision is None:
        return outcome(roadmap, "unverified", "checkout_unreadable", **fields)
    if remote_blob is None:
        return outcome(roadmap, "stale", "roadmap_missing_on_remote_default", **fields)
    if checkout_blob == remote_blob:
        return outcome(roadmap, "current", None, base_revision=remote_revision, **fields)
    behind = (
        checkout_revision != remote_revision
        and probe(root, ["git", "merge-base", "--is-ancestor", checkout_revision, remote_revision]).get("exit_status") == 0
    )
    return outcome(roadmap, "stale", "checkout_behind_remote" if behind else "roadmap_differs_from_remote", **fields)


def usable_roadmap_file(root: Path, roadmap: str) -> bool:
    path = root / roadmap
    return not path.is_symlink() and path.is_file() and path.resolve().is_relative_to(root.resolve())


def input_error(request: Any, message: str, details: dict[str, Any]) -> dict[str, Any]:
    return response(
        "input_error",
        request_id=request.request_id,
        diagnostics=[
            diagnostic(
                "invalid_input",
                message,
                details=details,
                remediation_summary="Send roadmap_path as the repo-relative path of an existing roadmap file.",
                remediation_actions=[
                    "Set inputs.roadmap_path to the technical roadmap file inside the repository.",
                    "Remove any other input field and retry.",
                ],
            )
        ],
    )


def run_roadmap_freshness_helper(entry: Any, request: Any) -> dict[str, Any]:
    inputs = request.inputs if isinstance(request.inputs, dict) else {}
    unexpected = sorted(set(inputs) - ALLOWED_INPUTS)
    if unexpected:
        return input_error(request, "check-roadmap-freshness got unknown inputs", {"unexpected_inputs": unexpected})
    repo_root = resolve_repo_root(inputs)
    if isinstance(repo_root, dict):
        status = "missing_prerequisite" if repo_root["code"] == "missing_prerequisite" else "input_error"
        return response(status, request_id=request.request_id, diagnostics=[repo_root])
    roadmap = canonical_target(inputs.get("roadmap_path"), repo_root)
    if roadmap is None or not usable_roadmap_file(repo_root, roadmap):
        return input_error(request, "roadmap_path must be an existing repo-relative file", {"field": "roadmap_path"})
    data = check_freshness(repo_root, roadmap)
    return response("ok" if data["verdict"] == "proceed" else "expected_failure", request_id=request.request_id, data=data)
