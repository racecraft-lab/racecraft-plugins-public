#!/usr/bin/env python3
"""Install and run the checksum-pinned actionlint release used by PR Checks."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from pathlib import Path, PurePosixPath
from typing import BinaryIO


ACTIONLINT_MEMBER = "actionlint"
DOWNLOAD_TIMEOUT_SECONDS = 30
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_BINARY_BYTES = 64 * 1024 * 1024


class ActionlintError(RuntimeError):
    """Raised when actionlint cannot be installed or executed safely."""


def _validated_version(version: str) -> str:
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is None:
        raise ActionlintError(f"invalid actionlint version: {version!r}")
    return version


def _validated_sha256(expected_sha256: str) -> str:
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        raise ActionlintError("ACTIONLINT_SHA256 must be exactly 64 lowercase hexadecimal characters")
    return expected_sha256


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise ActionlintError(f"required environment variable is not set: {name}")
    return value


def _download_archive(
    url: str,
    destination: Path,
    *,
    opener: Callable[..., BinaryIO] | None = None,
) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "racecraft-pr-checks-actionlint-installer"},
    )
    open_url = opener or urllib.request.urlopen
    total = 0
    try:
        with open_url(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            with destination.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_ARCHIVE_BYTES:
                        raise ActionlintError(
                            f"actionlint archive exceeds {MAX_ARCHIVE_BYTES} bytes"
                        )
                    output.write(chunk)
    except ActionlintError:
        raise
    except (OSError, urllib.error.URLError) as error:
        raise ActionlintError(f"unable to download actionlint archive: {error}") from error

    if total == 0:
        raise ActionlintError("downloaded actionlint archive is empty")


def verify_sha256(archive_path: Path, expected_sha256: str) -> None:
    expected = _validated_sha256(expected_sha256)
    digest = hashlib.sha256()
    try:
        with archive_path.open("rb") as archive:
            while chunk := archive.read(1024 * 1024):
                digest.update(chunk)
    except OSError as error:
        raise ActionlintError(f"unable to read actionlint archive: {error}") from error

    actual = digest.hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise ActionlintError(
            f"actionlint checksum mismatch: expected {expected}, got {actual}"
        )


def _member_name_is_safe(name: str) -> bool:
    if not name or "\x00" in name or "\\" in name:
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def extract_actionlint(archive_path: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_destination = destination.with_name(f".{destination.name}.tmp")
    temporary_destination.unlink(missing_ok=True)

    try:
        with tarfile.open(archive_path, mode="r:gz") as archive:
            members = archive.getmembers()
            unsafe_members = [
                member.name
                for member in members
                if not _member_name_is_safe(member.name)
                or member.issym()
                or member.islnk()
                or member.isdev()
            ]
            if unsafe_members:
                raise ActionlintError(
                    f"actionlint archive contains unsafe members: {unsafe_members}"
                )

            matches = [member for member in members if member.name == ACTIONLINT_MEMBER]
            if len(matches) != 1:
                raise ActionlintError(
                    "actionlint archive must contain exactly one top-level actionlint member"
                )

            member = matches[0]
            if not member.isreg() or member.size <= 0 or member.size > MAX_BINARY_BYTES:
                raise ActionlintError("actionlint archive member is not a safe regular file")

            extracted = archive.extractfile(member)
            if extracted is None:
                raise ActionlintError("unable to read actionlint archive member")

            written = 0
            with extracted, temporary_destination.open("xb") as output:
                while chunk := extracted.read(1024 * 1024):
                    written += len(chunk)
                    if written > member.size or written > MAX_BINARY_BYTES:
                        raise ActionlintError("actionlint archive member exceeds its declared size")
                    output.write(chunk)
            if written != member.size:
                raise ActionlintError("actionlint archive member is truncated")

        temporary_destination.chmod(
            stat.S_IRUSR
            | stat.S_IWUSR
            | stat.S_IXUSR
            | stat.S_IRGRP
            | stat.S_IXGRP
            | stat.S_IROTH
            | stat.S_IXOTH
        )
        temporary_destination.replace(destination)
    except ActionlintError:
        temporary_destination.unlink(missing_ok=True)
        raise
    except (OSError, tarfile.TarError) as error:
        temporary_destination.unlink(missing_ok=True)
        raise ActionlintError(f"unable to extract actionlint archive: {error}") from error


def install_actionlint(
    version: str,
    expected_sha256: str,
    install_directory: Path,
    *,
    opener: Callable[..., BinaryIO] | None = None,
) -> Path:
    pinned_version = _validated_version(version)
    pinned_sha256 = _validated_sha256(expected_sha256)
    archive_name = f"actionlint_{pinned_version}_linux_amd64.tar.gz"
    download_url = (
        "https://github.com/rhysd/actionlint/releases/download/"
        f"v{pinned_version}/{archive_name}"
    )

    install_directory.mkdir(parents=True, exist_ok=True)
    destination = install_directory / ACTIONLINT_MEMBER
    with tempfile.TemporaryDirectory(
        prefix="actionlint-install-",
        dir=install_directory,
    ) as temporary_directory:
        archive_path = Path(temporary_directory) / archive_name
        _download_archive(download_url, archive_path, opener=opener)
        verify_sha256(archive_path, pinned_sha256)
        extract_actionlint(archive_path, destination)
    return destination


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
