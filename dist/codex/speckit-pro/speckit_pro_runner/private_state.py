"""Owner-only session state shared by the capability brokers.

The sweep session store and the author broker both keep capability state in a
directory only the current user may read, and both replace a state file
atomically so a reader never sees a half-written record. Each caller supplies
its own violation type, so a refused root still surfaces through that broker's
error contract.
"""

from __future__ import annotations

import json
import os
import secrets
import stat
from collections.abc import Callable
from pathlib import Path
from typing import Any


def ensure_private_directory(path: Path, *, label: str, violation: Callable[[str], Exception]) -> None:
    """Create ``path`` owner-only, refusing a symlink, a non-directory, or another owner."""
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise violation(f"{label} is unsafe")
    uid = getattr(os, "getuid", lambda: info.st_uid)()
    if info.st_uid != uid:
        raise violation(f"{label} has the wrong owner")
    if stat.S_IMODE(info.st_mode) & 0o077:
        os.chmod(path, 0o700)


def write_private_json(path: Path, payload: dict[str, Any]) -> None:
    """Replace ``path`` with ``payload`` through an owner-only, fsynced temporary file."""
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            fd = -1
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            temporary.unlink()
        except FileNotFoundError:
            # Atomic replacement may have already removed the temporary path.
            pass
