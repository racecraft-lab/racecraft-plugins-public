"""One test suite at a time per checkout.

The quick suite (``tests/speckit-pro/run-all.py``) and the CI suite
(``scripts/run-ci-suite.py``) share staging state under one checkout, so a
second run there corrupts the first. Both entry points hold this lock for
their whole run. The kernel drops an ``flock`` when its holder exits or is
killed, so a failed or interrupted suite never leaves the checkout locked.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

try:
    import fcntl
except ImportError:  # no flock on this platform: suites run unguarded
    fcntl = None  # type: ignore[assignment]


class SuiteLockHeld(RuntimeError):
    """Another suite already holds the lock for this checkout."""


def _lock_path(checkout: Path) -> Path:
    digest = hashlib.sha256(str(checkout.resolve()).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"speckit-suite-{digest}.lock"


@contextlib.contextmanager
def hold_suite_lock(checkout: Path) -> Iterator[None]:
    """Hold the checkout's suite lock, or raise ``SuiteLockHeld``."""
    if fcntl is None:
        yield
        return
    with open(_lock_path(checkout), "a+", encoding="utf-8") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            stream.seek(0)
            holder = stream.read().strip() or "unknown"
            raise SuiteLockHeld(
                f"another suite is already running in this checkout (pid {holder}); "
                "wait for it to finish or run from another worktree"
            ) from None
        stream.seek(0)
        stream.truncate()
        stream.write(str(os.getpid()))
        stream.flush()
        yield
