"""Bounded process supervision shared by the live trigger-evaluation hosts.

The POSIX proof is absence of the original owned process group. On Windows the
scope is the direct child only; callers must not claim descendant containment.
"""
from __future__ import annotations

import errno
import os
import signal
import subprocess
import time
from typing import Callable

CLEANUP_TIMEOUT = 5
DESCENDANT_EXIT_GRACE = 0.2

class QueryError(OSError):
    """Stop the evaluation without discarding a failed child's raw evidence."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.stdout = b""
        self.stderr = b""
        self.exit_code: int | None = None
        self.timed_out = False
        self.cleanup_error: str | None = None
        self.unexpected_descendants = False
        self.child_pid: int | None = None
        self.child_pgid: int | None = None
        self.cleanup_observations: list[dict[str, object]] = []
        self.process_evidence: dict[str, object] = {}



class TerminationRequested(Exception):
    """Raised after terminating the owned child so local cleanup can run."""

    def __init__(self, signum: int) -> None:
        super().__init__(f"termination requested by signal {signum}")
        self.signum = signum
        self.stdout = b""
        self.stderr = b""
        self.exit_code: int | None = None
        self.timed_out = False
        self.cleanup_error: str | None = None
        self.unexpected_descendants = False
        self.child_pid: int | None = None
        self.child_pgid: int | None = None
        self.cleanup_observations: list[dict[str, object]] = []
        self.process_evidence: dict[str, object] = {}



def terminate_child(child: subprocess.Popen[bytes] | None, signum: int = signal.SIGTERM) -> bool:
    if child is None:
        return False
    try:
        if os.name != "nt":
            if child.pid <= 0 or child.pid == os.getpgrp():
                raise OSError("refusing to signal an unowned process group")
            os.killpg(child.pid, signum)
        elif child.poll() is None:
            child.terminate()
        else:
            return False
    except ProcessLookupError:
        return False
    return True



def cleanup_child(
    child: subprocess.Popen[bytes], *, observations: list[dict[str, object]] | None = None,
    timeout: float | None = None, grace: float | None = None,
    terminate: Callable[..., bool] = terminate_child,
) -> bool:
    """Drain the original owned group; report whether signaling was required."""
    timeout = CLEANUP_TIMEOUT if timeout is None else timeout
    grace = DESCENDANT_EXIT_GRACE if grace is None else grace
    started = time.monotonic()
    kill_sent = False
    last_probe_error: PermissionError | None = None

    def running() -> bool:
        nonlocal last_probe_error
        child.poll()
        if os.name == "nt":
            return child.returncode is None
        if child.pid <= 0 or child.pid == os.getpgrp():
            raise OSError("refusing to inspect an unowned process group")
        try:
            os.killpg(child.pid, 0)
        except ProcessLookupError:
            if observations is not None:
                observations.append({"pgid": child.pid, "errno": errno.ESRCH, "elapsed_seconds": time.monotonic() - started})
            return False
        except PermissionError as exc:
            if observations is not None:
                observations.append({"pgid": child.pid, "errno": exc.errno, "elapsed_seconds": time.monotonic() - started})
            if not kill_sent or exc.errno != errno.EPERM:
                raise
            # A post-KILL permission error is unresolved, never proof of absence.
            last_probe_error = exc
        return True

    if child.poll() is not None:
        deadline = time.monotonic() + grace
        while running() and time.monotonic() < deadline:
            time.sleep(0.01)
    signaled = False
    for signum in (signal.SIGTERM, signal.SIGKILL):
        if not running():
            return signaled
        signaled = True
        sent = terminate(child, signum)
        if signum == signal.SIGKILL and sent:
            kill_sent = True
        deadline = time.monotonic() + timeout
        while running() and time.monotonic() < deadline:
            time.sleep(0.05)
    if running():
        detail = f"; last unresolved probe: {last_probe_error}" if last_probe_error else ""
        raise OSError(f"owned process group {child.pid} remained after bounded cleanup{detail}")
    return signaled



def handle_termination(signum: int, _frame: object) -> None:
    # The query's finally block owns bounded signaling, draining, and evidence.
    raise TerminationRequested(signum)



def install_termination_handlers() -> dict[int, object]:
    previous: dict[int, object] = {}
    for name in ("SIGHUP", "SIGTERM"):
        signum = getattr(signal, name, None)
        if not isinstance(signum, int):
            continue
        try:
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, handle_termination)
        except (OSError, ValueError):
            previous.pop(signum, None)
    return previous



def restore_termination_handlers(previous: dict[int, object]) -> None:
    for signum, handler in previous.items():
        try:
            signal.signal(signum, handler)
        except (OSError, ValueError):
            pass


def supervise_child(
    child: subprocess.Popen[bytes], timeout: float, *,
    cleanup: Callable[..., bool] = cleanup_child, cleanup_timeout: float = CLEANUP_TIMEOUT,
    evidence: dict[str, object] | None = None,
) -> tuple[int, bytes, bytes, bool]:
    """Collect exact streams and verify the owned scope before returning or raising."""
    stdout = stderr = b""
    timed_out = completed = False
    failure: Exception | None = None
    cleanup_error: str | None = None
    unexpected_descendants = False
    observations: list[dict[str, object]] = []
    try:
        try:
            stdout, stderr = child.communicate(timeout=timeout)
            completed = True
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.output if isinstance(exc.output, bytes) else stdout
            stderr = exc.stderr if isinstance(exc.stderr, bytes) else stderr
        except KeyboardInterrupt:
            failure = TerminationRequested(signal.SIGINT)
        except Exception as exc:
            failure = exc
    finally:
        try:
            unexpected_descendants = cleanup(child, observations=observations) is True and completed
        except (TerminationRequested, KeyboardInterrupt) as exc:
            if not isinstance(failure, TerminationRequested):
                failure = exc if isinstance(exc, TerminationRequested) else TerminationRequested(signal.SIGINT)
            cleanup_error = "owned process cleanup interrupted before absence was verified"
        except (OSError, ValueError) as exc:
            cleanup_error = f"{type(exc).__name__}: {exc}"
        if not completed:
            try:
                drained_stdout, drained_stderr = child.communicate(timeout=cleanup_timeout)
                stdout, stderr = drained_stdout or stdout, drained_stderr or stderr
            except (TerminationRequested, KeyboardInterrupt) as exc:
                if not isinstance(failure, TerminationRequested):
                    failure = exc if isinstance(exc, TerminationRequested) else TerminationRequested(signal.SIGINT)
                cleanup_error = f"{cleanup_error + '; ' if cleanup_error else ''}owned stream drain interrupted"
            except subprocess.TimeoutExpired as exc:
                stdout = exc.output if isinstance(exc.output, bytes) else stdout
                stderr = exc.stderr if isinstance(exc.stderr, bytes) else stderr
                cleanup_error = f"{cleanup_error + '; ' if cleanup_error else ''}owned stream drain exceeded cleanup bound"
            except (OSError, ValueError) as exc:
                cleanup_error = f"{cleanup_error + '; ' if cleanup_error else ''}stream drain failed: {exc}"

    record = {
        "provider_exit_code": child.returncode,
        "timed_out": timed_out,
        "interrupted_by_signal": failure.signum if isinstance(failure, TerminationRequested) else None,
        "cleanup_verified": cleanup_error is None,
        "cleanup_error": cleanup_error,
        "cleanup_scope": "owned-process-group" if os.name != "nt" else "direct-child-only",
        "unexpected_descendants": unexpected_descendants,
        "child_pid": child.pid,
        "child_pgid": child.pid if os.name != "nt" else None,
        "cleanup_observations": observations,
        "process_error": str(failure) if failure is not None else None,
    }
    if evidence is not None:
        evidence.update(record)
    if failure is not None or cleanup_error is not None or unexpected_descendants or child.returncode is None:
        error = failure if isinstance(failure, TerminationRequested) else QueryError(
            str(failure) if failure is not None else (
                f"provider child cleanup failed: {cleanup_error}" if cleanup_error else
                "provider child exited with lingering owned descendants" if unexpected_descendants else
                "provider child exit status is unavailable"
            )
        )
        error.stdout, error.stderr = stdout, stderr
        error.exit_code, error.timed_out = child.returncode, timed_out
        error.cleanup_error, error.unexpected_descendants = cleanup_error, unexpected_descendants
        error.child_pid, error.child_pgid = child.pid, record["child_pgid"]
        error.cleanup_observations, error.process_evidence = observations, record
        raise error
    # Kept for the existing helper API; the receipt always holds the observed exit.
    return -1 if timed_out else int(child.returncode), stdout, stderr, timed_out
