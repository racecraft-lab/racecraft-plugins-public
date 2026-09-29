"""Shared git helpers for tests that build a throwaway repository.

Every call runs with no user or system git configuration and a fixed committer
identity, so a fixture commit never depends on the operator's machine.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

GIT_ENVIRONMENT = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "fixture",
    "GIT_AUTHOR_EMAIL": "git@github.com",
    "GIT_COMMITTER_NAME": "fixture",
    "GIT_COMMITTER_EMAIL": "git@github.com",
}


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run one git command in `root`, capturing text output."""
    return subprocess.run(["git", "-C", str(root), *args], check=check, capture_output=True, text=True,
                          env=GIT_ENVIRONMENT, timeout=60)


def git_stdout(root: Path, *args: str) -> str:
    """The trimmed standard output of a git command that must succeed."""
    completed = git(root, *args, check=False)
    if completed.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {completed.stderr}")
    return completed.stdout.strip()


def commit_baseline(root: Path, message: str = "baseline") -> None:
    """Commit every file under `root`, creating the repository first, so HEAD holds the baseline."""
    if not (root / ".git").exists():
        git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "--allow-empty", "-m", message)
