#!/usr/bin/env python3
"""Phase lock: keep agents on the open phase of the health program.

`.github/open-phase` names the open phase. `check-pr` fails a pull request that
closes an issue labelled with a later phase. `unlock` runs when the file changes
on main: it swaps `phase-locked` for each newly open issue's pickup label.

The check takes the earlier of the PR's file and the default branch's, so a pull
request cannot open a phase for itself; the default branch may lack the file only
before it first lands. Missing, unreadable or unknown evidence fails closed.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any


PHASES = ("phase-0", "phase-1", "phase-2", "phase-3", "phase-4", "phase-5", "part-d")
LOCK_LABEL = "phase-locked"
PICKUP_LABELS = ("ready-for-agent", "ready-for-human")
OPEN_PHASE_PATH = ".github/open-phase"
OPEN_PHASE_FILE = Path(__file__).resolve().parents[1] / OPEN_PHASE_PATH
PICKUP_LINE = re.compile(r"^\s*(?:[-*]\s+)?Pickup label when unlocked:\s*(?P<label>\S+)\s*$", re.MULTILINE)
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
UNLOCK_LIMIT = 500

CLOSING_ISSUES_QUERY = f"""
query($owner:String!,$name:String!,$number:Int!){{
  repository(owner:$owner,name:$name){{
    object(expression:"HEAD:{OPEN_PHASE_PATH}"){{... on Blob{{text}}}}
    pullRequest(number:$number){{
      closingIssuesReferences(first:50){{
        pageInfo{{hasNextPage}}
        nodes{{number labels(first:100){{pageInfo{{hasNextPage}} nodes{{name}}}}}}
      }}
    }}
  }}
}}
""".strip()


class PhaseLockError(RuntimeError):
    """Evidence the phase lock needs is missing, unreadable or unknown."""


def run_gh(argv: Sequence[str]) -> Any:
    completed = subprocess.run(["gh", *argv], text=True, capture_output=True, check=False, shell=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown gh error"
        raise PhaseLockError(f"gh {' '.join(argv[:2])} failed: {detail}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise PhaseLockError("gh returned malformed JSON") from exc


def parse_phase(text: str, source: str) -> str:
    phase = text.strip()
    if phase not in PHASES:
        raise PhaseLockError(f"{source} must name one of {', '.join(PHASES)}; found {phase!r}")
    return phase


def read_open_phase(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise PhaseLockError(f"cannot read {path.name}: {exc}") from exc
    return parse_phase(text, path.name)


def issue_phase(labels: Sequence[str]) -> str | None:
    """The latest phase among an issue's labels; None when it carries no phase."""
    phases = [label for label in labels if label in PHASES]
    return max(phases, key=PHASES.index) if phases else None


def page_nodes(connection: Any, what: str) -> list[dict[str, Any]]:
    """The nodes of one complete GraphQL page; a missing or truncated page fails closed."""
    if not isinstance(connection, dict) or not isinstance(connection.get("nodes"), list):
        raise PhaseLockError(f"GitHub returned no {what} list")
    if (connection.get("pageInfo") or {}).get("hasNextPage") is not False:
        raise PhaseLockError(f"{what} list is truncated")
    return [node for node in connection["nodes"] if isinstance(node, dict)]


def check_pr(
    repository: str,
    pr_number: int,
    *,
    open_phase_file: Path = OPEN_PHASE_FILE,
    api: Callable[[Sequence[str]], Any] = run_gh,
) -> int:
    try:
        open_phase = read_open_phase(open_phase_file)
        owner, name = repository.split("/", 1)
        payload = api(
            ["api", "graphql", "-f", f"query={CLOSING_ISSUES_QUERY}", "-f", f"owner={owner}",
             "-f", f"name={name}", "-F", f"number={pr_number}"]
        )
        repo = (payload or {}).get("data", {}).get("repository") or {}
        pr = repo.get("pullRequest")
        if not isinstance(pr, dict):
            raise PhaseLockError(f"pull request #{pr_number} was not found")
        if repo.get("object") is not None:
            main_phase = parse_phase(str(repo["object"].get("text")), "default-branch open-phase")
            open_phase = min(open_phase, main_phase, key=PHASES.index)
        locked = []
        for issue in page_nodes(pr.get("closingIssuesReferences"), "closing issue"):
            phase = issue_phase([str(label.get("name")) for label in page_nodes(issue.get("labels"), "label")])
            if phase is not None and PHASES.index(phase) > PHASES.index(open_phase):
                locked.append(f"#{issue.get('number')} ({phase})")
    except PhaseLockError as exc:
        print(f"phase-lock: {exc}", file=sys.stderr)
        return 1
    if locked:
        print(f"phase-lock: the open phase is {open_phase}; this PR closes locked issue(s): "
              + ", ".join(locked), file=sys.stderr)
        return 1
    print(f"phase-lock: every closed issue is in {open_phase} or earlier")
    return 0


def pickup_label(body: str) -> str:
    match = PICKUP_LINE.search(body)
    label = match.group("label") if match else PICKUP_LABELS[0]
    if label not in PICKUP_LABELS:
        raise PhaseLockError(f"unknown pickup label {label!r}")
    return label


def unlock_plan(issues: Sequence[dict[str, Any]], open_phase: str) -> list[tuple[int, str]]:
    """(issue number, pickup label) for each locked issue whose latest phase is the open one."""
    plan = []
    for issue in issues:
        labels = [str(label.get("name")) for label in issue.get("labels", [])]
        if LOCK_LABEL in labels and issue_phase(labels) == open_phase:
            plan.append((int(issue["number"]), pickup_label(str(issue.get("body") or ""))))
    return plan


def unlock(repository: str, *, open_phase_file: Path = OPEN_PHASE_FILE, api: Callable[[Sequence[str]], Any] = run_gh) -> int:
    open_phase = read_open_phase(open_phase_file)
    issues = api(["issue", "list", "--repo", repository, "--state", "open", "--label", open_phase,
                  "--label", LOCK_LABEL, "--limit", str(UNLOCK_LIMIT), "--json", "number,body,labels"])
    if not isinstance(issues, list) or len(issues) >= UNLOCK_LIMIT:
        raise PhaseLockError("issue list is missing or truncated")
    for number, label in unlock_plan(issues, open_phase):
        subprocess.run(["gh", "issue", "edit", str(number), "--repo", repository,
                        "--remove-label", LOCK_LABEL, "--add-label", label], check=True, shell=False)
        print(f"phase-lock: unlocked #{number} as {label}")
    return 0


def main(argv: Sequence[str]) -> int:
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if len(argv) != 1 or argv[0] not in {"check-pr", "unlock"} or not REPOSITORY_RE.fullmatch(repository):
        print("usage: GITHUB_REPOSITORY=owner/name [PR_NUMBER=n] phase-lock.py check-pr|unlock", file=sys.stderr)
        return 2
    try:
        if argv[0] == "unlock":
            return unlock(repository)
        pr_number = int(os.environ.get("PR_NUMBER", ""))
    except (PhaseLockError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"phase-lock: {exc}", file=sys.stderr)
        return 1
    return check_pr(repository, pr_number)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
