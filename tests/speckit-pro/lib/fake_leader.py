"""Fake process-group leaders for cleanup tests.

``trigger_process.cleanup_child`` signals a group only while its leader is
unreaped, because a PGID cannot be reused while the leader's PID is held. It
reaps the leader last. A test models such a leader here instead of a real pid.
"""

from __future__ import annotations

import contextlib
from typing import Iterator
from unittest import mock

import trigger_process


class UnreapedLeader:
    """A Popen stand-in whose leader stays unreaped until cleanup polls it."""

    def __init__(self, pid: int, *, exited: bool = False) -> None:
        self.pid = pid
        self.returncode: int | None = None
        self.exited = exited
        self.reaped = False

    def poll(self) -> int | None:
        if self.exited and not self.reaped:
            self.reaped, self.returncode = True, 0
        return self.returncode


@contextlib.contextmanager
def observed(leader: UnreapedLeader) -> Iterator[None]:
    """Answer cleanup's non-reaping leader observation from the fake.

    While the leader is a zombie, a live member is whatever answers the
    zero-signal group probe, on every platform.
    """

    def exit_status(_pid: int) -> int | None:
        if leader.reaped:
            raise ChildProcessError(10, "leader already reaped")
        return 0 if leader.exited else None

    with (
        mock.patch.object(trigger_process, "leader_exit_status", side_effect=exit_status),
        mock.patch.object(trigger_process, "_live_members_besides_zombies", return_value=None),
    ):
        yield
