"""Child processes that inherit nothing from the parent's Python environment.

A test child that inherits PYTHONPATH, PYTHONHOME or PYTHONSTARTUP can import a
checkout module ahead of the code it means to exercise and forge a passing
result. Every child gets an explicit environment built here instead.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from contextlib import ExitStack
from pathlib import Path
from typing import Any

# What a process needs to start and find tools on any supported host; nothing Python-specific.
BASE_KEYS = ("PATH", "HOME", "USER", "LOGNAME", "TMPDIR", "TEMP", "TMP", "LANG", "LC_ALL", "LC_CTYPE",
             "SYSTEMROOT", "COMSPEC", "PATHEXT", "USERPROFILE", "APPDATA", "LOCALAPPDATA")


def minimal_env(extra: Mapping[str, str] | None = None, *, keys: Iterable[str] = ()) -> dict[str, str]:
    """BASE_KEYS and `keys` copied from the parent, then `extra`. No PYTHON* variable ever passes."""
    env = {key: os.environ[key] for key in (*BASE_KEYS, *keys) if key in os.environ}
    env.update(extra or {})
    leaked = sorted(key for key in env if key.upper().startswith("PYTHON"))
    if leaked:
        raise ValueError("a child environment may not set " + ", ".join(leaked))
    return env


def run_python(args: Sequence[str], *, cwd: Path | str | None = None, env_extra: Mapping[str, str] | None = None,
               **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """Run `sys.executable -I *args` with a minimal environment.

    `-I` keeps the working directory, the script's directory, every PYTHON* variable and
    user site-packages off the child's sys.path; the minimal environment keeps PYTHON*
    variables from reaching the child's own children. The child starts in a fresh empty
    directory unless the caller names one it must read.
    """
    with ExitStack() as stack:
        if cwd is None:
            cwd = stack.enter_context(tempfile.TemporaryDirectory())
        return subprocess.run([sys.executable, "-I", *args], cwd=cwd, env=minimal_env(env_extra),
                              text=True, capture_output=True, shell=False, check=False, **kwargs)
