#!/usr/bin/env python3
"""Safely prepare and verify the generated docs artifact directory."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
from collections.abc import Sequence
from pathlib import Path


class ArtifactError(Exception):
    """An actionable docs artifact validation failure."""


CANONICAL_ARTIFACT_PATH = Path("docs-site/dist")


def checked_artifact_path(repo_root: Path, supplied_path: str | Path) -> Path:
    """Return a real in-repository artifact path that is safe to inspect or remove."""
    try:
        root = repo_root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ArtifactError(
            f"Cannot resolve repository root '{repo_root}': {exc}. Check the checkout path and permissions."
        ) from exc
    if not root.is_dir():
        raise ArtifactError(f"Repository root '{root}' is not a directory. Check the checkout path.")

    raw = Path(supplied_path)
    if ".." in raw.parts:
        raise ArtifactError(
            f"Refusing artifact path '{supplied_path}': '..' path segments are not allowed. "
            "Pass a dedicated output directory inside the repository."
        )

    candidate = raw if raw.is_absolute() else root / raw
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ArtifactError(
            f"Refusing artifact path '{supplied_path}': it is outside repository '{root}'. "
            "Pass a dedicated output directory inside the repository."
        ) from exc

    if not relative.parts:
        raise ArtifactError(
            f"Refusing artifact path '{supplied_path}': it resolves to the repository root. "
            "Pass a dedicated output directory such as docs-site/dist."
        )
    if relative != CANONICAL_ARTIFACT_PATH:
        raise ArtifactError(
            f"Refusing artifact path '{supplied_path}': only '{CANONICAL_ARTIFACT_PATH}' is allowed. "
            "The prepare operation recursively deletes its target, so the workflow path is fixed."
        )

    current = root
    try:
        for part in relative.parts:
            current /= part
            if current.is_symlink():
                raise ArtifactError(
                    f"Refusing artifact path '{supplied_path}': symlink traversal at '{current}' is not allowed. "
                    "Replace the symlink with a real directory inside the repository."
                )
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ArtifactError(
            f"Cannot safely resolve artifact path '{supplied_path}': {exc}. Check the path and permissions."
        ) from exc

    if resolved == root or not resolved.is_relative_to(root):
        raise ArtifactError(
            f"Refusing artifact path '{supplied_path}': it resolves outside the repository. "
            "Replace any escaping symlink and pass a dedicated in-repository output directory."
        )
    return resolved


def prepare_artifact(repo_root: Path, supplied_path: str | Path) -> Path:
    """Remove an existing artifact directory without touching adjacent paths."""
    artifact = checked_artifact_path(repo_root, supplied_path)
    if artifact.exists():
        if not artifact.is_dir():
            raise ArtifactError(
                f"Refusing to prepare artifact path '{supplied_path}': it is not a directory. "
                "Remove or rename the file, then rerun the workflow."
            )
        try:
            shutil.rmtree(artifact)
        except OSError as exc:
            raise ArtifactError(
                f"Could not remove artifact directory '{supplied_path}': {exc}. Check its permissions and retry."
            ) from exc
    print(f"Prepared docs artifact path: {supplied_path}")
    return artifact


def verify_artifact(repo_root: Path, supplied_path: str | Path) -> Path:
    """Require the generated artifact to be an existing non-empty directory."""
    artifact = checked_artifact_path(repo_root, supplied_path)
    if not artifact.exists():
        raise ArtifactError(
            f"Docs artifact '{supplied_path}' is missing after validation. "
            "Run the docs validation step and confirm it writes this directory."
        )
    if not artifact.is_dir():
        raise ArtifactError(
            f"Docs artifact '{supplied_path}' is not a directory after validation. "
            "Fix the docs output configuration and rerun validation."
        )
    has_content = validate_artifact_tree(artifact, supplied_path)
    if not has_content:
        raise ArtifactError(
            f"Docs artifact '{supplied_path}' is empty after validation. "
            "Check the docs build output before uploading the Pages artifact."
        )
    print(f"Verified non-empty docs artifact path: {supplied_path}")
    return artifact


def validate_artifact_tree(artifact: Path, supplied_path: str | Path) -> bool:
    """Reject links and special files before the Pages action dereferences the tree."""
    has_content = False

    def walk_error(error: OSError) -> None:
        raise ArtifactError(
            f"Could not inspect docs artifact '{supplied_path}': {error}. Check its permissions and retry."
        ) from error

    try:
        for directory, child_directories, files in os.walk(
            artifact,
            topdown=True,
            onerror=walk_error,
            followlinks=False,
        ):
            directory_path = Path(directory)
            for name, expected_directory in (
                *((name, True) for name in child_directories),
                *((name, False) for name in files),
            ):
                has_content = True
                entry = directory_path / name
                metadata = entry.lstat()
                if stat.S_ISLNK(metadata.st_mode):
                    raise ArtifactError(
                        f"Docs artifact '{supplied_path}' contains a symbolic link: "
                        f"{entry.relative_to(artifact)}. Replace it with generated file content."
                    )
                if expected_directory:
                    if not stat.S_ISDIR(metadata.st_mode):
                        raise ArtifactError(
                            f"Docs artifact '{supplied_path}' contains an invalid directory entry: "
                            f"{entry.relative_to(artifact)}."
                        )
                    continue
                if not stat.S_ISREG(metadata.st_mode):
                    raise ArtifactError(
                        f"Docs artifact '{supplied_path}' contains a special file: "
                        f"{entry.relative_to(artifact)}. Only regular files and directories are allowed."
                    )
                if metadata.st_nlink != 1:
                    raise ArtifactError(
                        f"Docs artifact '{supplied_path}' contains a hard-linked file: "
                        f"{entry.relative_to(artifact)}. Materialize a standalone generated file."
                    )
    except ArtifactError:
        raise
    except OSError as exc:
        raise ArtifactError(
            f"Could not inspect docs artifact '{supplied_path}': {exc}. Check its permissions and retry."
        ) from exc
    return has_content


def emit_github_error(message: str) -> None:
    """Emit one escaped GitHub Actions error annotation."""
    escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::error title=Docs artifact::{escaped}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "verify"))
    parser.add_argument("artifact_path", metavar="ARTIFACT_PATH")
    return parser


def main(argv: Sequence[str] | None = None, *, repo_root: Path | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root if repo_root is not None else Path(__file__).resolve().parents[1]
    try:
        if args.operation == "prepare":
            prepare_artifact(root, args.artifact_path)
        else:
            verify_artifact(root, args.artifact_path)
    except ArtifactError as exc:
        emit_github_error(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
