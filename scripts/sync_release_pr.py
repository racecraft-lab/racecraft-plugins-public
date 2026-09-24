#!/usr/bin/env python3
"""Merge current main into release PR branches and refresh generated artifacts."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from resolve_release_prs import ResolutionError, normalize_release_pr, parse_json_array


class SyncError(RuntimeError):
    """Raised when a release branch cannot be reconciled safely."""


RELEASE_MANIFEST = ".release-please-manifest.json"


def _manifest_versions(text: str, side: str) -> dict[str, str]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SyncError(f"{RELEASE_MANIFEST} on the {side} side is not valid JSON: {exc}") from exc
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(version, str) for key, version in value.items()
    ):
        raise SyncError(
            f"{RELEASE_MANIFEST} on the {side} side is not an object of version strings"
        )
    return value


def merge_release_manifest(base_text: str, branch_text: str, main_text: str) -> str:
    """Three-way merge the release-please manifest one component key at a time.

    Each release branch bumps only its own component, while main may already
    carry another component's released version on the adjacent line. For each
    key, keep the release branch's value when the branch changed it relative to
    the merge base, and main's value otherwise. Both sides changing one key to
    different values is a real conflict and fails the sync.
    """
    base = _manifest_versions(base_text, "merge base")
    branch = _manifest_versions(branch_text, "release branch")
    main = _manifest_versions(main_text, "main")

    merged: dict[str, str] = {}
    for key in [*main, *(key for key in branch if key not in main)]:
        base_value = base.get(key)
        branch_value = branch.get(key)
        main_value = main.get(key)
        if branch_value != base_value:
            if main_value not in (base_value, branch_value):
                raise SyncError(
                    f"{RELEASE_MANIFEST} conflict on {key!r}: release branch has "
                    f"{branch_value!r}, main has {main_value!r}"
                )
            value = branch_value
        else:
            value = main_value
        if value is not None:
            merged[key] = value
    return json.dumps(merged, indent=2) + "\n"


def regenerated_artifact_paths(repo_root: Path) -> tuple[str, ...]:
    """Return the paths ``refresh-release-artifacts.py`` rewrites from source.

    Read from that script's own ``CHECK_WORKTREE_PATHS`` rather than restated
    here, so the two stay in step when the generated surface moves.
    """
    script = repo_root / "scripts" / "refresh-release-artifacts.py"
    spec = importlib.util.spec_from_file_location("refresh_release_artifacts", script)
    if spec is None or spec.loader is None:
        raise SyncError(f"cannot load generated-artifact paths from {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return tuple(module.CHECK_WORKTREE_PATHS)


def is_regenerated_artifact(path: str, regenerated: Sequence[str]) -> bool:
    """True when ``path`` is a regenerated artifact or lives under one."""
    return any(path == entry or path.startswith(f"{entry}/") for entry in regenerated)


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


def merge_release_base(
    repo_root: Path,
    base_sha: str,
    runner: CommandRunner,
) -> None:
    """Merge the release base, tolerating conflicts in regenerated artifacts.

    ``refresh-release-artifacts.py`` runs immediately after this and rewrites
    its managed paths from source, so a conflict confined to those paths has no
    bearing on the result: whichever side is kept, the refresh emits identical
    bytes. Resolve them to the base side and let the refresh settle them. The
    release-please manifest is merged per component key (see
    ``merge_release_manifest``). A conflict anywhere else is a real one and
    still fails the sync.
    """
    try:
        runner.run(["git", "merge", "--no-edit", base_sha], repo_root)
        return
    except SyncError as exc:
        merge_error = exc

    conflicted = [
        line
        for line in runner.output(
            ["git", "diff", "--name-only", "--diff-filter=U"], repo_root
        ).splitlines()
        if line
    ]
    if not conflicted:
        # The merge failed for some reason other than a conflict, so keep git's
        # own diagnostic rather than replacing it with a conflict story.
        raise SyncError(f"{merge_error}; no conflicted path was reported") from merge_error

    generated = [path for path in conflicted if path != RELEASE_MANIFEST]
    regenerated = regenerated_artifact_paths(repo_root) if generated else ()
    unmanaged = sorted(
        path for path in generated if not is_regenerated_artifact(path, regenerated)
    )
    if unmanaged:
        raise SyncError(
            "release base merge conflicts outside regenerated artifacts: "
            + ", ".join(unmanaged)
        )

    if RELEASE_MANIFEST in conflicted:
        # Index stages of a conflicted path: 1 is the merge base, 2 the checked
        # out release branch, 3 the release base (main) being merged in.
        base_text, branch_text, main_text = (
            runner.output(["git", "show", f":{stage}:{RELEASE_MANIFEST}"], repo_root)
            for stage in (1, 2, 3)
        )
        merged = merge_release_manifest(base_text, branch_text, main_text)
        (repo_root / RELEASE_MANIFEST).write_text(merged, encoding="utf-8")
        runner.run(["git", "add", "--", RELEASE_MANIFEST], repo_root)

    for path in generated:
        runner.run(["git", "checkout", "--theirs", "--", path], repo_root)
        runner.run(["git", "add", "--", path], repo_root)
    runner.run(["git", "commit", "--no-edit"], repo_root)
    print(f"resolved {len(conflicted)} manifest or regenerated-artifact conflict(s) before refresh")


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
    merge_release_base(repo_root, base_sha, runner)

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
