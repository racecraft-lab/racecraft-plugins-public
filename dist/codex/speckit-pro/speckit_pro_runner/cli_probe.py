"""One bounded, read-only `gh` or `git` query with a fixed argv, a per-caller allowlist and a timeout."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Collection
from pathlib import Path
from typing import Any

# A branch name that could be read as an option, or that git would reject, is never passed to a CLI.
BRANCH = re.compile(r"(?!-)(?!.*\.\.)(?!.*//)[A-Za-z0-9._/-]{1,255}\Z")
STDERR_TAIL_CHARS = 2048


def probe(root: Path, argv: list[str], *, allowed: Collection[str], timeout: float) -> dict[str, Any]:
    """Run `argv` when its CLI is in `allowed`; any failure to run is reported, never raised.

    The record always has the same four keys. `exit_status` is None when the CLI is not
    allowed, cannot start, or exceeds `timeout` seconds.
    """
    try:
        if not argv or argv[0] not in allowed:
            raise ValueError(f"only {', '.join(sorted(allowed))} may run here")
        result = subprocess.run(
            [argv[0], *argv[1:]],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            shell=False,
        )
        return {
            "argv": argv,
            "exit_status": result.returncode,
            "stdout_tail": result.stdout.strip(),
            "stderr_tail": result.stderr[-STDERR_TAIL_CHARS:].strip(),
        }
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return {"argv": argv, "exit_status": None, "stdout_tail": "", "stderr_tail": str(exc)}
