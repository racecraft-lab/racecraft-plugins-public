"""Compare a bounded daemon archive to captured inputs, without filesystem extraction."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import tarfile
import time
from typing import Any, TYPE_CHECKING

from .verification_docker import MAX_SNAPSHOT_ENTRIES, snapshot_members

if TYPE_CHECKING:
    from .verification_docker_runtime import DockerClient

MAX_ARCHIVE_BYTES = 576 * 1024 * 1024
PAX_METADATA = {"path", "mtime", "atime", "ctime", "uid", "gid", "uname", "gname"}


@dataclass(frozen=True)
class SnapshotReadback:
    snapshot: dict[str, tuple[int, bytes | None]]
    archive: Path

    def verify(self, client: DockerClient, cid: str, before: dict[str, Any], deadline: float) -> dict[str, Any]:
        state = before.get("State")
        if (not isinstance(state, dict) or state.get("Status") != "created" or state.get("Running") is not False
                or type(state.get("Pid")) is not int or state["Pid"] != 0):
            raise ValueError("input readback requires a never-started container")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("verification deadline exhausted before input readback")
        copied = client.call(["cp", f"{cid}:/inputs/.", "-"], min(remaining, 120), archive=self.archive)
        readback = verify_snapshot_archive(self.archive, self.snapshot)
        if readback["archive_sha256"] != copied["stdout_sha256"]:
            raise ValueError("input readback archive changed after Docker capture")
        return readback


def compare_member(archive: tarfile.TarFile, member: tarfile.TarInfo,
                   expected: dict[str, tuple[int, bytes | None]], seen: set[str]) -> str:
    name = member.name[2:] if member.name.startswith("./") else member.name
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or ".." in path.parts or path.as_posix() != name
            or "\x00" in name or "\\" in name or name in seen or name not in expected):
        raise ValueError("container archive contains an extra, duplicate, or unsafe input path")
    mode, body = expected[name]
    if (member.mode != mode or member.uid != 65532 or member.gid != 65532
            or set(member.pax_headers) - PAX_METADATA or member.issparse()):
        raise ValueError("container input metadata differs or includes unsupported attributes")
    if body is None:
        if member.type != tarfile.DIRTYPE or member.size != 0:
            raise ValueError("container input directory type differs")
        return name
    if member.type not in {tarfile.REGTYPE, tarfile.AREGTYPE} or member.size != len(body):
        raise ValueError("container input file type or length differs")
    # extractfile reads member bytes; no archive path is ever extracted to disk.
    with archive.extractfile(member) as stream:
        offset = 0
        while offset < len(body):
            chunk = stream.read(min(65536, len(body) - offset))
            if not chunk or chunk != body[offset:offset + len(chunk)]:
                raise ValueError("container input bytes differ from the captured snapshot")
            offset += len(chunk)
    return name


def verify_snapshot_archive(path: Path, expected: dict[str, tuple[int, bytes | None]]) -> dict[str, Any]:
    """Require exact paths/types/bytes/modes and the intentional image UID/GID mapping.

    Only an uncompressed tar from the owned stopped container is accepted. Reject
    links, devices, sparse data, unbound extended attributes and trailing payloads.
    This is input equality evidence, not independent producer/isolation authority.
    """
    snapshot_members(expected)
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("container archive byte limit exceeded")
    seen: set[str] = set()
    try:
        with path.open("rb") as handle:
            archive_sha = hashlib.file_digest(handle, "sha256").hexdigest()
            handle.seek(0)
            with tarfile.open(fileobj=handle, mode="r:") as archive:
                for member in archive:
                    if len(seen) >= MAX_SNAPSHOT_ENTRIES:
                        raise ValueError("container archive entry limit exceeded")
                    seen.add(compare_member(archive, member, expected, seen))
                handle.seek(archive.offset)
                padding = 0
                while chunk := handle.read(65536):
                    if any(chunk):
                        raise ValueError("container archive has trailing non-padding data")
                    padding += len(chunk)
                if padding < 1024:
                    raise ValueError("container archive end markers are missing")
    except tarfile.TarError as exc:
        raise ValueError("invalid or incomplete container input archive") from exc
    if seen != set(expected):
        raise ValueError("container archive is missing captured input entries")
    return {"verified": True, "entries": len(seen), "archive_sha256": archive_sha}
