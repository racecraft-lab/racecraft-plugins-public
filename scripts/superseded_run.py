"""Tell whether a cancelled pull-request run was replaced by a newer run of the same commit.

GitHub often delivers two ``pull_request`` events for one head commit (for
example two ``synchronize`` events when a stack push moves a branch and its
base). The workflow concurrency group then cancels the older run, and its
``if: always()`` verdict job reports failure beside the newer run's verdict.
The commit's status rollup stays red until someone reruns the cancelled run.

A verdict job may report the older run as superseded, instead of failed, only
when this module finds a newer run of the same workflow for the same head
commit. That newer run reports the real verdict on the same commit. Every
missing input or API error means "not superseded", so the verdict fails
closed exactly as before.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any

Fetch = Callable[[str], Any]

_SHA = re.compile(r"[0-9a-f]{40}")
_REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


def github_fetch(token: str, api_url: str, timeout: float = 15.0) -> Fetch:
    """Return a single-attempt JSON GET against the GitHub REST API."""

    def fetch(path: str) -> Any:
        request = urllib.request.Request(
            f"{api_url.rstrip('/')}{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "racecraft-superseded-run-check",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    return fetch


def newer_run_id(env: Mapping[str, str], fetch: Fetch | None = None) -> int | None:
    """Return the id of a newer run of this workflow for the same head commit, else None."""
    if env.get("GITHUB_EVENT_NAME") != "pull_request":
        return None
    repository = env.get("GITHUB_REPOSITORY", "")
    head_sha = env.get("PR_HEAD_SHA", "")
    raw_run_id = env.get("GITHUB_RUN_ID", "")
    if not (_REPOSITORY.fullmatch(repository) and _SHA.fullmatch(head_sha) and raw_run_id.isdigit()):
        return None
    run_id = int(raw_run_id)
    if fetch is None:
        token = env.get("GITHUB_TOKEN", "")
        if not token:
            return None
        fetch = github_fetch(token, env.get("GITHUB_API_URL", "https://api.github.com"))
    try:
        current = fetch(f"/repos/{repository}/actions/runs/{run_id}")
        workflow_id = current["workflow_id"]
        if current["id"] != run_id or current["head_sha"] != head_sha or type(workflow_id) is not int:
            return None
        listing = fetch(
            f"/repos/{repository}/actions/workflows/{workflow_id}/runs"
            f"?head_sha={head_sha}&event=pull_request&per_page=100"
        )
        newer = [
            run["id"] for run in listing["workflow_runs"]
            if type(run.get("id")) is int and run["id"] > run_id
            and run.get("head_sha") == head_sha
            and run.get("workflow_id") == workflow_id
            and run.get("event") == "pull_request"
        ]
    except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError):
        return None
    return min(newer) if newer else None


def superseded_notice(env: Mapping[str, str] | None = None, fetch: Fetch | None = None) -> str | None:
    """Return a notice naming the newer run when this run was superseded, else None."""
    values = os.environ if env is None else env
    newer = newer_run_id(values, fetch)
    if newer is None:
        return None
    return (
        f"This run was cancelled and superseded by run {newer} for the same head commit; "
        "that run reports the verdict."
    )
