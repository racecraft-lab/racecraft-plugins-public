"""One bounded, read-only `gh`, `git` or `docker` query with a fixed argv, a per-caller allowlist and a timeout."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Collection
from pathlib import Path
from typing import Any

# A branch name that could be read as an option, or that git would reject, is never passed to a CLI.
BRANCH = re.compile(r"(?!-)(?!.*\.\.)(?!.*//)[A-Za-z0-9._/-]{1,255}\Z")
STDERR_TAIL_CHARS = 2048
STDOUT_TAIL_CHARS = 1024 * 1024
DOCKER_STDOUT_TAIL_CHARS = STDERR_TAIL_CHARS
CLIS = ("gh", "git", "docker")


def probe(root: Path, argv: list[str], *, allowed: Collection[str], timeout: float) -> dict[str, Any]:
    """Run `argv` when its CLI is in `allowed`; any failure to run is reported, never raised.

    The record always has the same four keys. `exit_status` is None when the CLI is not
    allowed, cannot start, exceeds `timeout` seconds, or overflows the stdout limit.
    Docker output is limited to 2048 characters; Git/GitHub retain up to 1 MiB
    so ordinary structured responses stay complete. Overflow is never a successful probe.
    """
    try:
        if not argv or argv[0] not in allowed or argv[0] not in CLIS:
            raise ValueError(f"only {', '.join(sorted(allowed))} may run here")
        # Each executable is a literal, so the repository Bash-confinement guard can prove it Bash-free.
        options: dict[str, Any] = {"cwd": root, "capture_output": True, "text": True, "timeout": timeout,
                                   "stdin": subprocess.DEVNULL, "shell": False}
        if argv[0] == "gh":
            result = subprocess.run(["gh", *argv[1:]], **options)
        elif argv[0] == "docker":
            result = subprocess.run(["docker", *argv[1:]], **options)
        else:
            result = subprocess.run(["git", *argv[1:]], **options)
        stdout_limit = DOCKER_STDOUT_TAIL_CHARS if argv[0] == "docker" else STDOUT_TAIL_CHARS
        overflow = len(result.stdout) > stdout_limit
        stderr = result.stderr[-STDERR_TAIL_CHARS:].strip()
        if overflow:
            stderr = f"CLI stdout exceeded {stdout_limit} characters; probe output is incomplete. {stderr}"[:STDERR_TAIL_CHARS]
        return {
            "argv": argv,
            "exit_status": None if overflow else result.returncode,
            "stdout_tail": result.stdout[-stdout_limit:].strip(),
            "stderr_tail": stderr,
        }
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return {"argv": argv, "exit_status": None, "stdout_tail": "", "stderr_tail": str(exc)}
