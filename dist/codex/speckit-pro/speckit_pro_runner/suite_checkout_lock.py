"""One test suite at a time per checkout.

The quick suite (``tests/speckit-pro/run-all.py``) and the CI suite
(``scripts/run-ci-suite.py``, or the raw runner request it sends) share staging
state under one checkout, so a second run there corrupts the first. Each entry
point and the runner's suite gate hold this lock for their whole run. The lock
is an ``flock`` on a file in the checkout's own git directory, so it does not
depend on ``TMPDIR`` and is private to the checkout. The kernel drops it when
the holding process exits or is killed, so a failed or interrupted suite never
leaves the checkout locked.

A holder names its lock file in ``SPECKIT_SUITE_LOCK`` for its children
(``SuiteLock.environment``). A process that finds its own checkout's lock file
named there runs inside the holding suite and proceeds without locking again,
so a suite's own runner requests and nested test runners are not refused.

The guard stands down outside supported checkouts: no ``fcntl`` (Windows) or
no git directory. It never prints, because the runner's stderr is a JSON
channel; ``SuiteLock.unguarded_warning`` carries the warning for callers that
can print it. Lock errors in a supported checkout refuse execution because its
staging state may still be writable and shared.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

try:
    import fcntl
except ImportError:  # no flock on this platform: suites run unguarded
    fcntl = None  # type: ignore[assignment]

LOCK_NAME = "speckit-suite.lock"
HOLDER_VARIABLE = "SPECKIT_SUITE_LOCK"
# EX_TEMPFAIL: distinct from 1 so callers do not read a refusal as a red test.
REFUSED_STATUS = 75


class SuiteLockHeld(RuntimeError):
    """Another suite already holds the lock for this checkout."""


class SuiteLockUnavailable(RuntimeError):
    """A supported checkout cannot establish its suite lock."""


@dataclass(frozen=True)
class SuiteLock:
    """The lock a running suite holds, as its child processes must see it."""

    lock_path: Path | None = None
    unguarded_warning: str | None = None

    def environment(self, base: Mapping[str, str]) -> dict[str, str]:
        """Return ``base`` plus the marker that admits this suite's children."""
        environment = dict(base)
        if self.lock_path is not None:
            environment[HOLDER_VARIABLE] = str(self.lock_path)
        return environment


def _git_dir(checkout: Path) -> Path | None:
    """Return the checkout's git directory, following a worktree ``.git`` file."""
    marker = checkout / ".git"
    if marker.is_dir():
        return marker.resolve()
    try:
        first_line = marker.read_text(encoding="utf-8").splitlines()[0]
    except (OSError, IndexError, UnicodeError):
        return None
    prefix = "gitdir:"
    if not first_line.startswith(prefix):
        return None
    return (checkout / first_line[len(prefix):].strip()).resolve()


@contextlib.contextmanager
def hold_suite_lock(checkout: Path) -> Iterator[SuiteLock]:
    """Hold the suite lock, or refuse a held or unavailable checkout lock."""
    git_dir = _git_dir(checkout)
    if fcntl is None or git_dir is None:
        yield SuiteLock(
            unguarded_warning="suite lock: no flock or git directory here; running without the one-suite guard"
        )
        return
    lock_path = git_dir / LOCK_NAME
    if os.environ.get(HOLDER_VARIABLE) == str(lock_path):
        # A parent suite holds this checkout's lock and started this process.
        yield SuiteLock(lock_path)
        return
    try:
        stream = open(lock_path, "a+", encoding="utf-8")
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
            yield SuiteLock(lock_path)
        finally:
            stream.seek(0)
            stream.truncate()
