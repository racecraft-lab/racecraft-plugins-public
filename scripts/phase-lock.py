#!/usr/bin/env python3
"""Phase lock: keep agents on the open phase of the health program.

`.github/open-phase` names the open phase. `check-pr` fails a pull request that
closes an issue still labelled `phase-locked` or labelled with a later phase.
`unlock` runs when the file changes on main: it swaps `phase-locked` for the
pickup label on every locked issue up to the open phase, so a skipped phase
unlocks too.

The check takes the earlier of the PR's file and the default branch's, so editing
the file cannot open a phase for the PR that edits it; the default branch may
lack the file only before it first lands. Missing, unreadable or unknown evidence
fails closed.
"""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Callable, Sequence
from functools import partial
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gh_json import run_gh_json  # noqa: E402


PHASES = ("phase-0", "phase-1", "phase-2", "phase-3", "phase-4", "phase-5", "part-d")
PHASE_RANK = {phase: rank for rank, phase in enumerate(PHASES)}
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


Api = Callable[[Sequence[str]], Any]
GH: Api = partial(run_gh_json, error=PhaseLockError)


def parse_phase(text: str, source: str) -> str:
    phase = text.strip()
    if phase not in PHASE_RANK:
        raise PhaseLockError(f"{source} must name one of {', '.join(PHASES)}; found {phase!r}")
    return phase


def read_open_phase(path: Path) -> str:
    try:
        return parse_phase(path.read_text(encoding="utf-8"), path.name)
    except (OSError, UnicodeDecodeError) as exc:
        raise PhaseLockError(f"cannot read {path.name}: {exc}") from exc


def label_names(labels: Sequence[Any]) -> list[str]:
    return [str(label.get("name")) for label in labels if isinstance(label, dict)]


def issue_phase(labels: Sequence[str]) -> str | None:
    """The latest phase among an issue's labels; None when it carries no phase."""
    phases = [label for label in labels if label in PHASE_RANK]
    return max(phases, key=PHASE_RANK.__getitem__) if phases else None


def page_nodes(connection: Any, what: str) -> list[dict[str, Any]]:
    """The nodes of one complete GraphQL page; a missing or truncated page fails closed."""
    if not isinstance(connection, dict) or not isinstance(connection.get("nodes"), list):
        raise PhaseLockError(f"GitHub returned no {what} list")
    if (connection.get("pageInfo") or {}).get("hasNextPage") is not False:
        raise PhaseLockError(f"{what} list is truncated")
    return [node for node in connection["nodes"] if isinstance(node, dict)]


def locked_closing_issues(pr: dict[str, Any], open_phase: str) -> list[str]:
    locked = []
    for issue in page_nodes(pr.get("closingIssuesReferences"), "closing issue"):
        labels = label_names(page_nodes(issue.get("labels"), "label"))
        phase = issue_phase(labels)
        if LOCK_LABEL in labels or (phase is not None and PHASE_RANK[phase] > PHASE_RANK[open_phase]):
            locked.append(f"#{issue.get('number')} ({phase or 'no phase'}{', ' + LOCK_LABEL if LOCK_LABEL in labels else ''})")
    return locked


def check_pr(repository: str, pr_number: int, *, open_phase_file: Path = OPEN_PHASE_FILE, api: Api = GH) -> int:
    open_phase = read_open_phase(open_phase_file)
    owner, name = repository.split("/", 1)
    payload = api(["api", "graphql", "-f", f"query={CLOSING_ISSUES_QUERY}", "-f", f"owner={owner}",
                   "-f", f"name={name}", "-F", f"number={pr_number}"])
    repo = ((payload if isinstance(payload, dict) else {}).get("data") or {}).get("repository") or {}
    pr = repo.get("pullRequest")
    if not isinstance(pr, dict):
        raise PhaseLockError(f"pull request #{pr_number} was not found")
    if isinstance(repo.get("object"), dict):
        main_phase = parse_phase(str(repo["object"].get("text")), "default-branch open-phase")
        open_phase = min(open_phase, main_phase, key=PHASE_RANK.__getitem__)
    locked = locked_closing_issues(pr, open_phase)
    if locked:
        print(f"phase-lock: the open phase is {open_phase}; this PR closes locked issue(s): "
              + ", ".join(locked), file=sys.stderr)
        return 1
    print(f"phase-lock: every closed issue is in {open_phase} or earlier and unlocked")
    return 0


def pickup_label(body: str) -> str:
    match = PICKUP_LINE.search(body)
    label = match.group("label") if match else PICKUP_LABELS[0]
    if label not in PICKUP_LABELS:
        raise PhaseLockError(f"unknown pickup label {label!r}")
    return label


def unlock_plan(issues: Sequence[dict[str, Any]], open_phase: str) -> list[tuple[int, list[str]]]:
    """(issue number, its new label set) for each locked issue at or before the open phase."""
    plan = []
    for issue in issues:
        labels = label_names(issue.get("labels", []))
        phase = issue_phase(labels)
        if LOCK_LABEL in labels and phase is not None and PHASE_RANK[phase] <= PHASE_RANK[open_phase]:
            pickup = pickup_label(str(issue.get("body") or ""))
            plan.append((int(issue["number"]), sorted({*labels, pickup} - {LOCK_LABEL})))
    return plan


def unlock(repository: str, *, open_phase_file: Path = OPEN_PHASE_FILE, api: Api = GH) -> int:
    open_phase = read_open_phase(open_phase_file)
    issues = api(["issue", "list", "--repo", repository, "--state", "open", "--label", LOCK_LABEL,
                  "--limit", str(UNLOCK_LIMIT), "--json", "number,body,labels"])
    if not isinstance(issues, list) or len(issues) >= UNLOCK_LIMIT:
        raise PhaseLockError("issue list is missing or truncated")
    for number, labels in unlock_plan(issues, open_phase):
        # One PUT replaces the whole label set, so an issue never holds both labels or neither.
        api(["api", "-X", "PUT", f"repos/{repository}/issues/{number}/labels",
             *(arg for label in labels for arg in ("-f", f"labels[]={label}"))])
        print(f"phase-lock: unlocked #{number} as {', '.join(labels)}")
    return 0


def main(argv: Sequence[str]) -> int:
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if len(argv) != 1 or argv[0] not in {"check-pr", "unlock"} or not REPOSITORY_RE.fullmatch(repository):
        print("usage: GITHUB_REPOSITORY=owner/name [PR_NUMBER=n] phase-lock.py check-pr|unlock", file=sys.stderr)
        return 2
    try:
        if argv[0] == "unlock":
            return unlock(repository)
        return check_pr(repository, int(os.environ.get("PR_NUMBER", "")))
    except (PhaseLockError, ValueError) as exc:
        print(f"phase-lock: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
