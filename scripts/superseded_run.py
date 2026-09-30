"""Tell whether a cancelled pull-request run was replaced by another run of the same commit.

GitHub often delivers two ``pull_request`` events for one head commit (for
example two ``synchronize`` events when a stack push moves a branch and its
base). The workflow concurrency group then cancels one of the two runs, and its
``if: always()`` verdict job reports failure beside the other run's verdict.
The commit's status rollup stays red until someone reruns the cancelled run.
Runs created in the same second carry no reliable order: the cancelled one may
have the higher run id.

A verdict job may report a cancelled run as superseded, instead of failed, only
when this module finds another run of the same workflow for the same head
commit that was not itself cancelled. That run reports the real verdict on the
same commit. Every missing input or API error means "not superseded", so the
verdict fails closed exactly as before.
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


def event_head_sha(event_path: str) -> str:
    """Return the pull request head commit from the Actions event payload, or ""."""
    try:
        with open(event_path, encoding="utf-8") as handle:
            head_sha = json.load(handle)["pull_request"]["head"]["sha"]
    except (OSError, ValueError, KeyError, TypeError):
        return ""
    return head_sha if isinstance(head_sha, str) else ""


def sibling_run_id(env: Mapping[str, str], fetch: Fetch | None = None) -> int | None:
    """Return the id of another, not cancelled run of this workflow for the same head commit, else None.

    Run ids do not order same-second runs: GitHub may cancel either of two runs
    created together, so any live or finished sibling that was not itself
    cancelled reports the verdict.
    """
    if env.get("GITHUB_EVENT_NAME") != "pull_request":
        return None
    repository = env.get("GITHUB_REPOSITORY", "")
    head_sha = event_head_sha(env.get("GITHUB_EVENT_PATH", ""))
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
        siblings = [
            run["id"] for run in listing["workflow_runs"]
            if type(run.get("id")) is int and run["id"] != run_id
            and run.get("head_sha") == head_sha
            and run.get("workflow_id") == workflow_id
            and run.get("event") == "pull_request"
            and run.get("conclusion") != "cancelled"
        ]
    except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError):
        return None
    return max(siblings) if siblings else None


def superseded_notice(env: Mapping[str, str] | None = None, fetch: Fetch | None = None) -> str | None:
    """Return a notice naming the sibling run when this run was superseded, else None."""
    values = os.environ if env is None else env
    sibling = sibling_run_id(values, fetch)
    if sibling is None:
        return None
    return (
        f"This run was cancelled and superseded by run {sibling} for the same head commit; "
        "that run reports the verdict."
    )
