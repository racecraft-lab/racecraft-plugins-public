#!/usr/bin/env python3
"""Merge current main into release PR branches and refresh generated artifacts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from resolve_release_prs import ResolutionError, normalize_release_pr, parse_json_array


class SyncError(RuntimeError):
    """Raised when a release branch cannot be reconciled safely."""


class CommandRunner:
    @staticmethod
    def _execute(
        argv: Sequence[str],
        cwd: Path,
        *,
        capture_output: bool,
    ) -> subprocess.CompletedProcess[str]:
        if not argv:
            raise SyncError("command argv must not be empty")

        executable, *tail = argv
        if executable == "git":
            return subprocess.run(
                ["git", *tail],
                cwd=cwd,
                text=True,
                capture_output=capture_output,
                shell=False,
                check=False,
            )
        if executable == "corepack":
            return subprocess.run(
                ["corepack", *tail],
                cwd=cwd,
                text=True,
                capture_output=capture_output,
                shell=False,
                check=False,
            )
        if executable == "pnpm":
            return subprocess.run(
                ["pnpm", *tail],
                cwd=cwd,
                text=True,
                capture_output=capture_output,
                shell=False,
                check=False,
            )
        if executable == sys.executable:
            return subprocess.run(
                [sys.executable, *tail],
                cwd=cwd,
                text=True,
                capture_output=capture_output,
                shell=False,
                check=False,
            )
        raise SyncError(f"unsupported command executable: {executable}")

    def run(self, argv: Sequence[str], cwd: Path) -> None:
        completed = self._execute(argv, cwd, capture_output=False)
        if completed.returncode != 0:
            raise SyncError(f"command failed ({completed.returncode}): {' '.join(argv)}")

    def output(self, argv: Sequence[str], cwd: Path) -> str:
        completed = self._execute(argv, cwd, capture_output=True)
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise SyncError(detail or f"command failed ({completed.returncode}): {' '.join(argv)}")
        return completed.stdout.strip()


def sync_release_branch(
    repo_root: Path,
    release_pr: dict,
    base_ref: str,
    runner: CommandRunner,
) -> bool:
    normalized = normalize_release_pr(release_pr, base_ref, strict=True)
    assert normalized is not None
    branch = normalized["headBranchName"]

    runner.run(["git", "fetch", "origin", branch], repo_root)
    remote_branch_sha = runner.output(["git", "rev-parse", "FETCH_HEAD"], repo_root)
    runner.run(["git", "checkout", "-B", branch, remote_branch_sha], repo_root)

    runner.run(["git", "fetch", "origin", base_ref], repo_root)
    base_sha = runner.output(["git", "rev-parse", "FETCH_HEAD"], repo_root)
    runner.run(["git", "config", "user.name", "github-actions[bot]"], repo_root)
    runner.run(
        [
            "git",
            "config",
            "user.email",
            "41898282+github-actions[bot]@users.noreply.github.com",
        ],
        repo_root,
    )
    runner.run(["git", "merge", "--no-edit", base_sha], repo_root)

    runner.run(["corepack", "enable"], repo_root)
    runner.run(["corepack", "prepare", "pnpm@10.25.0", "--activate"], repo_root)
    runner.run([sys.executable, "scripts/refresh-release-artifacts.py"], repo_root)
    runner.run(["pnpm", "--dir", "docs-site", "reference:generate"], repo_root)

    if runner.output(["git", "status", "--porcelain"], repo_root):
        runner.run(["git", "add", "-A"], repo_root)
        runner.run(
            ["git", "commit", "-m", "chore(release): sync generated artifacts for release"],
            repo_root,
        )

    head_sha = runner.output(["git", "rev-parse", "HEAD"], repo_root)
    if head_sha == remote_branch_sha:
        print(f"{branch}: branch and generated artifacts are already current")
        return False
    runner.run(["git", "push", "origin", f"HEAD:{branch}"], repo_root)
    print(f"{branch}: reconciled and pushed")
    return True


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    base_ref = os.environ.get("BASE_REF", "main")
    try:
        release_prs = parse_json_array(os.environ.get("RELEASE_PRS", "[]"), "resolved release PRs")
        if not release_prs:
            raise SyncError("release PR resolver returned no metadata")
        runner = CommandRunner()
        for release_pr in release_prs:
            sync_release_branch(repo_root, release_pr, base_ref, runner)
    except (ResolutionError, SyncError, json.JSONDecodeError) as exc:
        print(f"sync-release-pr: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
