"""Download, checksum-verify, and extract one binary from a pinned release archive.

Shared by the CI tool installers (install-actionlint.py, install-ripwire.py).
Every step fails closed: the archive is verified before it is opened, and an
unsafe or unexpected archive layout installs nothing.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import stat
import tarfile
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO


DOWNLOAD_TIMEOUT_SECONDS = 30
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_BINARY_BYTES = 128 * 1024 * 1024
_CHUNK_BYTES = 1024 * 1024
_EXECUTABLE_MODE = (
    stat.S_IRUSR
    | stat.S_IWUSR
    | stat.S_IXUSR
    | stat.S_IRGRP
    | stat.S_IXGRP
    | stat.S_IROTH
    | stat.S_IXOTH
)


class PinnedArchiveError(RuntimeError):
    """Raised when a pinned tool cannot be installed or executed safely."""


def validated_sha256(expected_sha256: str, *, label: str) -> str:
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        raise PinnedArchiveError(
            f"{label} SHA-256 must be exactly 64 lowercase hexadecimal characters"
        )
    return expected_sha256


def download_archive(
    url: str,
    destination: Path,
    *,
    label: str,
    opener: Callable[..., BinaryIO] | None = None,
) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"racecraft-ci-{label}-installer"},
    )
    open_url = opener or urllib.request.urlopen
    total = 0
    try:
        with open_url(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            with destination.open("wb") as output:
                while chunk := response.read(_CHUNK_BYTES):
                    total += len(chunk)
                    if total > MAX_ARCHIVE_BYTES:
                        raise PinnedArchiveError(
                            f"{label} archive exceeds {MAX_ARCHIVE_BYTES} bytes"
                        )
                    output.write(chunk)
    except PinnedArchiveError:
        raise
    except (OSError, urllib.error.URLError) as error:
        raise PinnedArchiveError(f"unable to download {label} archive: {error}") from error

    if total == 0:
        raise PinnedArchiveError(f"downloaded {label} archive is empty")


def verify_sha256(archive_path: Path, expected_sha256: str, *, label: str = "archive") -> None:
    expected = validated_sha256(expected_sha256, label=label)
    digest = hashlib.sha256()
    try:
        with archive_path.open("rb") as archive:
            while chunk := archive.read(_CHUNK_BYTES):
                digest.update(chunk)
    except OSError as error:
        raise PinnedArchiveError(f"unable to read {label} archive: {error}") from error

    actual = digest.hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise PinnedArchiveError(
            f"{label} checksum mismatch: expected {expected}, got {actual}"
        )


def member_name_is_safe(name: str) -> bool:
    if not name or "\x00" in name or "\\" in name:
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def _checked_member(archive: tarfile.TarFile, member_name: str, *, label: str) -> tarfile.TarInfo:
    members = archive.getmembers()
    unsafe_members = [
        member.name
        for member in members
        if not member_name_is_safe(member.name)
        or member.issym()
        or member.islnk()
        or member.isdev()
    ]
    if unsafe_members:
        raise PinnedArchiveError(f"{label} archive contains unsafe members: {unsafe_members}")

    matches = [member for member in members if member.name == member_name]
    if len(matches) != 1:
        raise PinnedArchiveError(
            f"{label} archive must contain exactly one {member_name} member"
        )
    member = matches[0]
    if not member.isreg() or member.size <= 0 or member.size > MAX_BINARY_BYTES:
        raise PinnedArchiveError(f"{label} archive member is not a safe regular file")
    return member


def extract_member(
    archive_path: Path,
    member_name: str,
    destination: Path,
    *,
    label: str,
) -> None:
    """Write one regular-file member to ``destination`` with executable mode."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_destination = destination.with_name(f".{destination.name}.tmp")
    temporary_destination.unlink(missing_ok=True)

    try:
        with tarfile.open(archive_path, mode="r:gz") as archive:
            member = _checked_member(archive, member_name, label=label)
            extracted = archive.extractfile(member)
            if extracted is None:
                raise PinnedArchiveError(f"unable to read {label} archive member")

            written = 0
            with extracted, temporary_destination.open("xb") as output:
                while chunk := extracted.read(_CHUNK_BYTES):
                    written += len(chunk)
                    if written > member.size:
                        raise PinnedArchiveError(
                            f"{label} archive member exceeds its declared size"
                        )
                    output.write(chunk)
            if written != member.size:
                raise PinnedArchiveError(f"{label} archive member is truncated")

        temporary_destination.chmod(_EXECUTABLE_MODE)
        temporary_destination.replace(destination)
    except PinnedArchiveError:
        temporary_destination.unlink(missing_ok=True)
        raise
    except (OSError, tarfile.TarError) as error:
        temporary_destination.unlink(missing_ok=True)
        raise PinnedArchiveError(f"unable to extract {label} archive: {error}") from error


@dataclass(frozen=True)
class PinnedArchive:
    """One release archive: where it lives, its SHA-256, and the binary inside."""

    label: str
    url: str
    sha256: str
    member: str


def install_binary(
    archive: PinnedArchive,
    destination: Path,
    *,
    opener: Callable[..., BinaryIO] | None = None,
) -> Path:
    """Download ``archive``, verify its SHA-256, then extract its binary to ``destination``."""
    pinned_sha256 = validated_sha256(archive.sha256, label=archive.label)
    destination.parent.mkdir(parents=True, exist_ok=True)
    archive_name = archive.url.rsplit("/", 1)[-1]
    with tempfile.TemporaryDirectory(
        prefix=f"{archive.label}-install-",
        dir=destination.parent,
    ) as temporary_directory:
        archive_path = Path(temporary_directory) / archive_name
        download_archive(archive.url, archive_path, label=archive.label, opener=opener)
        verify_sha256(archive_path, pinned_sha256, label=archive.label)
        extract_member(archive_path, archive.member, destination, label=archive.label)
    return destination
