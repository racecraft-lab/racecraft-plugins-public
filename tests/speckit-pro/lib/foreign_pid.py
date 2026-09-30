"""Fake process ids that can never be the test process's own identity.

Process-cleanup code refuses to signal its own pid or process group. A test
that hard-codes a fake child pid fails whenever the operating system happens
to give the test process that same pid or group id, which fresh CI runners
do often enough to matter. Pick fake ids through ``foreign_pid`` instead.
"""

from __future__ import annotations

import os


def foreign_pid(preferred: int) -> int:
    """Return ``preferred``, or the next larger id if it is this process's own."""
    if type(preferred) is not int or preferred <= 1:
        raise ValueError("preferred fake pid must be an integer above 1")
    own = {os.getpid()}
    if hasattr(os, "getpgrp"):
        own.add(os.getpgrp())
    candidate = preferred
    while candidate in own:
        candidate += 1
    return candidate
