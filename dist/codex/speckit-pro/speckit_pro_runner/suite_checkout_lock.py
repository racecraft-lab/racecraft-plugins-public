"""One test suite at a time per checkout.

The quick suite (``tests/speckit-pro/run-all.py``) and the CI suite
(``scripts/run-ci-suite.py``) share staging state under one checkout, so a
second run there corrupts the first. Both entry points hold this lock for
their whole run. The lock is an ``flock`` on a file in the checkout's own git
directory, so it does not depend on ``TMPDIR`` and is private to the checkout.
The kernel drops it when the holding process exits or is killed, so a failed
or interrupted suite never leaves the checkout locked. Child processes do not
inherit it: killing the wrapper alone frees the lock while orphaned children
may still run.

The guard stands down, with a warning, outside supported checkouts: no
``fcntl`` (Windows) or no git directory. Lock errors in a supported checkout
refuse execution because its staging state may still be writable and shared.
"""

from __future__ import annotations

import contextlib
import os
import sys
from collections.abc import Iterator
from pathlib import Path

try:
    import fcntl
except ImportError:  # no flock on this platform: suites run unguarded
    fcntl = None  # type: ignore[assignment]

LOCK_NAME = "speckit-suite.lock"
# EX_TEMPFAIL: distinct from 1 so callers do not read a refusal as a red test.
REFUSED_STATUS = 75


class SuiteLockHeld(RuntimeError):
    """Another suite already holds the lock for this checkout."""


class SuiteLockUnavailable(RuntimeError):
    """A supported checkout cannot establish its suite lock."""


def _git_dir(checkout: Path) -> Path | None:
    """Return the checkout's git directory, following a worktree ``.git`` file."""
    marker = checkout / ".git"
    if marker.is_dir():
        return marker
    try:
        first_line = marker.read_text(encoding="utf-8").splitlines()[0]
    except (OSError, IndexError, UnicodeError):
        return None
    prefix = "gitdir:"
    if not first_line.startswith(prefix):
        return None
    return (checkout / first_line[len(prefix):].strip()).resolve()


def _unguarded(reason: str) -> None:
    print(f"suite lock: {reason}; running without the one-suite guard", file=sys.stderr)


@contextlib.contextmanager
def hold_suite_lock(checkout: Path) -> Iterator[None]:
    """Hold the suite lock, or refuse a held or unavailable checkout lock."""
    git_dir = _git_dir(checkout)
    if fcntl is None or git_dir is None:
        _unguarded("no flock or git directory here")
        yield
        return
    try:
        stream = open(git_dir / LOCK_NAME, "a+", encoding="utf-8")
    except OSError as exc:
        raise SuiteLockUnavailable(f"cannot open the lock file ({exc.strerror}); refusing to run") from exc
    with stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            stream.seek(0)
            holder = stream.read().strip() or "unknown"
            raise SuiteLockHeld(
                f"another suite is already running in this checkout (pid {holder}); "
                "wait for it to finish or run from another worktree"
            ) from None
        except OSError as exc:
            raise SuiteLockUnavailable(f"flock failed ({exc.strerror}); refusing to run") from exc
        stream.seek(0)
        stream.truncate()
        stream.write(str(os.getpid()))
        stream.flush()
        try:
            yield
        finally:
            stream.seek(0)
            stream.truncate()
