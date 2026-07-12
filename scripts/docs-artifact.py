#!/usr/bin/env python3
"""Safely prepare and verify the generated docs artifact directory."""

from __future__ import annotations

import argparse
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path


class ArtifactError(Exception):
    """An actionable docs artifact validation failure."""


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
    try:
        has_content = next(artifact.iterdir(), None) is not None
    except OSError as exc:
        raise ArtifactError(
            f"Could not inspect docs artifact '{supplied_path}': {exc}. Check its permissions and retry."
        ) from exc
    if not has_content:
        raise ArtifactError(
            f"Docs artifact '{supplied_path}' is empty after validation. "
            "Check the docs build output before uploading the Pages artifact."
        )
    print(f"Verified non-empty docs artifact path: {supplied_path}")
    return artifact


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
