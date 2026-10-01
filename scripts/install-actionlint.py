#!/usr/bin/env python3
"""Install and run the checksum-pinned actionlint release used by PR Checks."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import BinaryIO

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pinned_archive as _pinned  # noqa: E402
from pinned_archive import DOWNLOAD_TIMEOUT_SECONDS  # noqa: E402,F401


ACTIONLINT_MEMBER = "actionlint"

# Raised when actionlint cannot be installed or executed safely.
ActionlintError = _pinned.PinnedArchiveError


def _validated_version(version: str) -> str:
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is None:
        raise ActionlintError(f"invalid actionlint version: {version!r}")
    return version


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise ActionlintError(f"required environment variable is not set: {name}")
    return value


def extract_actionlint(archive_path: Path, destination: Path) -> None:
    _pinned.extract_member(archive_path, ACTIONLINT_MEMBER, destination, label="actionlint")


def install_actionlint(
    version: str,
    expected_sha256: str,
    install_directory: Path,
    *,
    opener: Callable[..., BinaryIO] | None = None,
) -> Path:
    pinned_version = _validated_version(version)
    archive_name = f"actionlint_{pinned_version}_linux_amd64.tar.gz"
    download_url = (
        "https://github.com/rhysd/actionlint/releases/download/"
        f"v{pinned_version}/{archive_name}"
    )
    release = _pinned.PinnedArchive("actionlint", download_url, expected_sha256, ACTIONLINT_MEMBER)
    return _pinned.install_binary(release, install_directory / ACTIONLINT_MEMBER, opener=opener)


def sorted_workflow_files(workflows_directory: Path) -> list[Path]:
    if not workflows_directory.is_dir():
        raise ActionlintError(f"workflow directory does not exist: {workflows_directory}")
    workflows = sorted(
        (path for path in workflows_directory.glob("*.yml") if path.is_file()),
        key=lambda path: path.as_posix(),
    )
    if not workflows:
        raise ActionlintError(f"no .yml workflows found under {workflows_directory}")
    return workflows


def run_actionlint(
    actionlint_path: Path,
    workflows_directory: Path,
) -> subprocess.CompletedProcess[object]:
    if actionlint_path.name != ACTIONLINT_MEMBER or not actionlint_path.is_file():
        raise ActionlintError(f"installed actionlint executable not found: {actionlint_path}")
    if not os.access(actionlint_path, os.X_OK):
        raise ActionlintError(f"installed actionlint is not executable: {actionlint_path}")

    workflows = sorted_workflow_files(workflows_directory)
    child_environment = os.environ.copy()
    existing_path = child_environment.get("PATH", "")
    child_environment["PATH"] = str(actionlint_path.parent) + (
        os.pathsep + existing_path if existing_path else ""
    )
    argv = ["actionlint"]
    argv.extend(str(path) for path in workflows)
    try:
        return subprocess.run(
            argv,
            check=True,
            env=child_environment,
            shell=False,
        )
    except subprocess.CalledProcessError as error:
        raise ActionlintError(
            f"actionlint failed with exit code {error.returncode}"
        ) from error
    except OSError as error:
        raise ActionlintError(f"unable to execute actionlint: {error}") from error


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "install",
        help="download, verify, and install the pinned actionlint binary",
    )
    run_parser = subparsers.add_parser(
        "run",
        help="run the installed actionlint binary over sorted workflow paths",
    )
    run_parser.add_argument(
        "--workflows-directory",
        type=Path,
        default=Path(".github/workflows"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        runner_temp = Path(_required_environment("RUNNER_TEMP"))
        if args.command == "install":
            installed = install_actionlint(
                _required_environment("ACTIONLINT_VERSION"),
                _required_environment("ACTIONLINT_SHA256"),
                runner_temp,
            )
            print(f"Installed actionlint at {installed}")
        else:
            workflows_directory = args.workflows_directory
            result = run_actionlint(runner_temp / ACTIONLINT_MEMBER, workflows_directory)
            print(
                f"actionlint validated {len(sorted_workflow_files(workflows_directory))} workflows"
            )
            return int(result.returncode)
    except ActionlintError as error:
        print(f"::error::Actionlint validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
