"""Bounded process supervision shared by the live trigger-evaluation hosts.

The POSIX proof is absence of the original owned process group. On Windows the
scope is the direct child only; callers must not claim descendant containment.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import errno
import functools
import os
import signal
import subprocess
import time
from typing import Callable

CLEANUP_TIMEOUT = 5
DESCENDANT_EXIT_GRACE = 0.2

@dataclass
class CleanupEvidence:
    """Presence metadata alongside the legacy permission/absence probe stream."""

    initially_present: bool | None = None
    observations: list[dict[str, object]] = field(default_factory=list)

    def observe_presence(self, present: bool) -> None:
        if self.initially_present is None:
            self.initially_present = present

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



_REAL_POPEN = subprocess.Popen  # captured before any test patches the module attribute


def _wait_status(code: int, status: int) -> int:
    """Encode a waitid result as the waitpid status Popen decodes."""
    if code == os.CLD_EXITED:
        return (status & 0xFF) << 8
    return status | (0x80 if code == os.CLD_DUMPED else 0)


def leader_exit_status(pid: int) -> int | None:
    """Return the leader's wait status once it exits, without reaping it.

    An unreaped leader keeps its PID, and a PGID cannot be reused while its
    leader's PID is held, so the group stays owned. Raises ChildProcessError
    once the leader has been reaped.
    """
    flags = os.WEXITED | os.WNOWAIT | os.WNOHANG
    if hasattr(os, "waitid"):
        info = os.waitid(os.P_PID, pid, flags)
        return None if info is None else _wait_status(info.si_code, info.si_status)
    return _libc_waitid_nowait(pid, flags)


@functools.lru_cache(maxsize=None)
def _libc_waitid() -> tuple[object, type]:
    import ctypes

    class SigInfo(ctypes.Structure):
        # Leading siginfo_t fields shared by macOS and Linux, then room for the rest.
        _fields_ = [("si_signo", ctypes.c_int), ("si_errno", ctypes.c_int), ("si_code", ctypes.c_int),
                    ("si_pid", ctypes.c_int), ("si_uid", ctypes.c_uint), ("si_status", ctypes.c_int),
                    ("reserved", ctypes.c_byte * 128)]

    return ctypes.CDLL(None, use_errno=True).waitid, SigInfo


def _libc_waitid_nowait(pid: int, flags: int) -> int | None:
    """CPython omits os.waitid on macOS, but libc waitid honors WNOWAIT there."""
    import ctypes

    waitid, sig_info = _libc_waitid()
    while True:
        info = sig_info()
        if waitid(os.P_PID, pid, ctypes.byref(info), flags) == 0:
            return None if info.si_pid == 0 else _wait_status(info.si_code, info.si_status)
        err = ctypes.get_errno()
        if err == errno.ECHILD:
            raise ChildProcessError(err, os.strerror(err))
        if err != errno.EINTR:
            raise OSError(err, os.strerror(err))


def hold_leader(child: subprocess.Popen[bytes]) -> None:
    """Stop Popen from reaping the leader until cleanup_child reaps it last.

    Popen reaps through _try_wait (wait, communicate) and _internal_poll (poll,
    send_signal, __del__, subprocess._cleanup). While held, both record the
    exit status and leave the zombie in place, so the PGID stays owned.
    """
    if os.name == "nt" or not isinstance(child, _REAL_POPEN):
        return

    def try_wait(wait_flags: int) -> tuple[int, int]:
        while True:
            try:
                status = leader_exit_status(child.pid)
            except ChildProcessError:
                return child.pid, 0  # As Popen does when the child was reaped elsewhere.
            if status is not None:
                return child.pid, status
            if wait_flags & os.WNOHANG:
                return 0, 0
            time.sleep(0.005)

    def internal_poll(_deadstate: int | None = None, **_unused: object) -> int | None:
        if child.returncode is None:
            try:
                status = leader_exit_status(child.pid)
            except ChildProcessError:
                child.returncode = _deadstate or 0  # As Popen does when the child was reaped elsewhere.
            else:
                if status is not None:
                    child._handle_exitstatus(status)
        return child.returncode

    child._try_wait = try_wait  # type: ignore[method-assign]
    child._internal_poll = internal_poll  # type: ignore[method-assign]


def _held(child: object) -> bool:
    return "_try_wait" in vars(child) if hasattr(child, "__dict__") else False


def reap_leader(child: subprocess.Popen[bytes]) -> None:
    """Release a held leader and reap it once no further group signal is due."""
    held = _held(child)
    if held:
        del child._try_wait, child._internal_poll
    if held and child.returncode is not None:
        try:
            os.waitpid(child.pid, 0)  # The exit was recorded while held; the zombie is still ours.
        except ChildProcessError:
            pass  # Reaped elsewhere already; there is nothing left to release.
    elif child.returncode is None:
        child.poll()


def _leader_exited(child: subprocess.Popen[bytes]) -> bool | None:
    """True once the leader exited, False while it runs, None once it is reaped.

    None means the PGID is no longer owned and must never be signaled again.
    """
    if child.returncode is not None and not _held(child):
        return None
    try:
        return leader_exit_status(child.pid) is not None
    except ChildProcessError:
        return None


def _live_members_besides_zombies(pgid: int) -> bool | None:
    """Linux keeps a zombie leader signalable, so read member states from /proc."""
    if not os.path.isdir("/proc/self/task"):
        return None
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            with open(f"/proc/{name}/stat", "rb") as handle:
                fields = handle.read().rpartition(b")")[2].split()
        except OSError:
            continue
        if len(fields) > 2 and int(fields[2]) == pgid and fields[0] not in (b"Z", b"X"):
            return True
    return False


def _cleanup_direct_child(
    child: subprocess.Popen[bytes], timeout: float, terminate: Callable[..., bool],
) -> bool:
    """Windows scope: the direct child only."""
    signaled = False
    for signum in (signal.SIGTERM, signal.SIGKILL):
        if child.poll() is not None:
            return signaled
        signaled = True
        terminate(child, signum)
        deadline = time.monotonic() + timeout
        while child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
    if child.poll() is None:
        raise OSError(f"owned process group {child.pid} remained after bounded cleanup")
    return signaled


def cleanup_child(
    child: subprocess.Popen[bytes], *, observations: list[dict[str, object]] | CleanupEvidence | None = None,
    timeout: float | None = None, grace: float | None = None,
    terminate: Callable[..., bool] = terminate_child,
) -> bool:
    """Drain the original owned group; report whether signaling was required.

    On POSIX every group signal is sent while the leader is still unreaped, so
    its PGID cannot have been reused; the leader is reaped last. A leader that
    was already reaped leaves an unowned PGID that is probed but never signaled.
    """
    timeout = CLEANUP_TIMEOUT if timeout is None else timeout
    grace = DESCENDANT_EXIT_GRACE if grace is None else grace
    if os.name == "nt":
        return _cleanup_direct_child(child, timeout, terminate)
    if child.pid <= 0 or child.pid == os.getpgrp():
        raise OSError("refusing to inspect an unowned process group")
    pgid = child.pid
    started = time.monotonic()
    evidence = observations if isinstance(observations, CleanupEvidence) else None
    observations = observations.observations if isinstance(observations, CleanupEvidence) else observations

    absent = False  # Set by the first ESRCH: the original group is gone, and any later answer is another group.

    def probe(*, record_eperm: bool = True) -> int | None:
        """Return ESRCH or EPERM from a zero-signal group probe, or None if a member answered."""
        nonlocal absent
        result: int | None = None
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            result = errno.ESRCH
            absent = True
        except PermissionError as exc:
            if exc.errno != errno.EPERM:
                raise
            result = errno.EPERM  # macOS: members exist but none can take a signal (zombies, exiting).
        if result is not None and observations is not None and (record_eperm or result != errno.EPERM):
            observations.append({"pgid": pgid, "errno": result, "elapsed_seconds": time.monotonic() - started})
        if evidence is not None:
            evidence.observe_presence(result != errno.ESRCH)
        return result

    def live() -> bool:
        """Whether the owned group may still hold a live member we are allowed to signal."""
        exited = _leader_exited(child)
        # macOS answers EPERM for our own held zombie leader: expected, not unresolved evidence.
        answer = probe(record_eperm=exited is not True)
        if exited is None or answer == errno.ESRCH:
            return False  # Absent, or the leader was reaped and the PGID is no longer ours.
        if not exited:
            return True
        # The leader is a held zombie: only another live member keeps the group alive.
        scanned = _live_members_besides_zombies(pgid)
        return answer is None if scanned is None else scanned

    signaled = False
    try:
        phases = ((None, grace if _leader_exited(child) else 0), (signal.SIGTERM, timeout), (signal.SIGKILL, timeout))
        for signum, bound in phases:
            if signum is not None:
                signaled = True
                try:
                    group_gone = not terminate(child, signum)
                except PermissionError as exc:
                    if exc.errno != errno.EPERM:
                        raise
                    group_gone = False  # No member could take it; the held leader keeps the PGID ours.
                if group_gone:
                    # ESRCH: the original group is gone, so its PGID is never signaled again.
                    absent = True
                    if observations is not None:
                        observations.append({"pgid": pgid, "errno": errno.ESRCH, "elapsed_seconds": time.monotonic() - started})
                    break
            deadline = time.monotonic() + bound
            while (state := live()) and time.monotonic() < deadline:
                time.sleep(0.01 if signum is None else 0.05)
            if not state:
                break
    finally:
        reap_leader(child)
    # Absence proof after the reap. No signal follows, so a reused PGID is never touched.
    deadline = time.monotonic() + timeout
    while not absent and (answer := probe()) != errno.ESRCH:
        if time.monotonic() >= deadline:
            detail = "a member answers" if answer is None else "probe denied (EPERM)"
            raise OSError(f"owned process group {pgid} remained after bounded cleanup; {detail}")
        time.sleep(0.01)
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
            # Handler restoration is best effort; preserve the primary result on failure.
            pass


def supervise_child(
    child: subprocess.Popen[bytes], timeout: float, *,
    cleanup: Callable[..., bool] = cleanup_child, cleanup_timeout: float = CLEANUP_TIMEOUT,
    evidence: dict[str, object] | None = None, input_bytes: bytes | None = None,
) -> tuple[int, bytes, bytes, bool]:
    """Collect exact streams and verify the owned scope before returning or raising."""
    stdout = stderr = b""
    timed_out = completed = False
    failure: Exception | None = None
    cleanup_error: str | None = None
    unexpected_descendants = False
    observations: list[dict[str, object]] = []
    hold_leader(child)  # communicate() must not reap the leader before cleanup signals its group.
    try:
        try:
            if input_bytes is None:
                stdout, stderr = child.communicate(timeout=timeout)
            else:
                stdout, stderr = child.communicate(input=input_bytes, timeout=timeout)
            completed = True
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.output if isinstance(exc.output, bytes) else stdout
            stderr = exc.stderr if isinstance(exc.stderr, bytes) else stderr
        except KeyboardInterrupt:
            failure = TerminationRequested(signal.SIGINT)
        except Exception as exc:  # noqa: BLE001 - boundary: any failure becomes an explicit error
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
        if _held(child):
            reap_leader(child)  # A substitute cleanup left the hold in place.
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
