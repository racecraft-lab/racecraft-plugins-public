"""Git queries the phase coverage validator uses to authorize checkpoint evidence."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from phase_coverage_repo_files import _is_normalized_repo_path


def _git_env() -> dict[str, str]:
    return {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"}


def _git_file_at_commit(repo_root: Path, commit_sha: object, relative_path: str) -> bytes | None:
    if not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        return None
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit_sha}:{relative_path}"],
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else None


def _git_commit_exists(repo_root: Path, commit_sha: object) -> bool:
    if not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        return False
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e", f"{commit_sha}^{{commit}}"],
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    return completed.returncode == 0


def _git_commit_is_ancestor(repo_root: Path, ancestor_sha: str, descendant_sha: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", ancestor_sha, descendant_sha],
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    return completed.returncode == 0


def _git_commit_is_strict_ancestor(
    repo_root: Path, ancestor_sha: str, descendant_sha: str,
) -> bool:
    return (
        ancestor_sha != descendant_sha
        and _git_commit_is_ancestor(repo_root, ancestor_sha, descendant_sha)
    )


def _git_commit_is_ancestor_of_head(repo_root: Path, commit_sha: str) -> bool:
    return _git_commit_is_ancestor(repo_root, commit_sha, "HEAD")


def _git_changed_paths(
    repo_root: Path, base_sha: object, head_sha: object,
) -> set[str] | None:
    if (
        not _git_commit_exists(repo_root, base_sha)
        or not _git_commit_exists(repo_root, head_sha)
    ):
        return None
    completed = subprocess.run(
        [
            "git", "-C", str(repo_root),
            "-c", "diff.renames=true",
            "-c", "diff.renameLimit=0",
            "diff", "--no-ext-diff", "--find-renames=50%",
            "--ignore-submodules=none", "--name-status", "-z",
            f"{base_sha}..{head_sha}",
        ],
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return _name_status_paths(completed.stdout)


def _name_status_paths(output: bytes) -> set[str] | None:
    """Every path in `git diff --name-status -z` output, or None when it is malformed."""
    records = output.split(b"\0")
    paths: set[str] = set()
    index = 0
    try:
        while index < len(records) and records[index]:
            status = records[index].decode("ascii")
            index += 1
            if not status or index >= len(records):
                return None
            paths.add(records[index].decode("utf-8"))
            index += 1
            if status[0] in {"R", "C"}:
                if index >= len(records) or not records[index]:
                    return None
                paths.add(records[index].decode("utf-8"))
                index += 1
            elif status[0] not in {"A", "D", "M", "T", "U", "X", "B"}:
                return None
    except (UnicodeDecodeError, IndexError):
        return None
    return paths


def _git_path_introduction_commit(
    repo_root: Path, path: object, head_sha: object,
) -> str | None:
    if (
        not _is_normalized_repo_path(path)
        or not isinstance(head_sha, str)
        or not re.fullmatch(r"[0-9a-f]{40}", head_sha)
    ):
        return None
    completed = subprocess.run(
        [
            "git", "-C", str(repo_root), "log", "--diff-filter=A", "--format=%H",
            "--reverse", head_sha, "--", path,
        ],
        text=True,
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        return None
    commits = [line for line in completed.stdout.splitlines() if line]
    return commits[0] if commits else None


def _git_tree_entries(repo_root: Path, commit_sha: object) -> dict[str, str] | None:
    if not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        return None
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "ls-tree", "-r", "-z", "--full-tree", commit_sha],
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        return None
    entries: dict[str, str] = {}
    for raw_record in completed.stdout.split(b"\0"):
        if not raw_record:
            continue
        try:
            raw_identity, raw_path = raw_record.split(b"\t", 1)
            identity = raw_identity.decode("ascii")
            path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError):
            return None
        if path in entries:
            return None
        entries[path] = identity
    return entries


def _git_common_dir(repo_root: Path) -> Path | None:
    """`git rev-parse --git-common-dir` resolved against the worktree, or None."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            env=_git_env(),
            shell=False,
            check=False,
        )
    except (OSError, ValueError):
        return None
    common = completed.stdout.strip()
    if completed.returncode != 0 or not common:
        return None
    return repo_root / common
