#!/usr/bin/env python3
"""Run ordered Speckit Pro runner request files without shell redirection."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any


def shell_compatible_status(returncode: int) -> int:
    """Convert subprocess signal return codes to conventional shell statuses."""
    return 128 + abs(returncode) if returncode < 0 else returncode or 1


def run_runner_requests(
    repo_root: Path,
    request_files: Sequence[str],
    *,
    run: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
    environment: Mapping[str, str] | None = None,
) -> int:
    repo_root = repo_root.resolve()
    child_environment = dict(os.environ if environment is None else environment)
    child_environment["PYTHONPATH"] = str(repo_root / "speckit-pro")
    child_environment["PYTHONDONTWRITEBYTECODE"] = "1"

    for request_file in request_files:
        try:
            request_path = (repo_root / request_file).resolve()
            request_path.relative_to(repo_root)
            request_bytes = request_path.read_bytes()
        except (OSError, ValueError) as exc:
            print(
                f"run-runner-requests: unable to read {request_file}: {exc}",
                file=sys.stderr,
            )
            return 1

        try:
            completed = run(
                [sys.executable, "-m", "speckit_pro_runner"],
                input=request_bytes,
                cwd=str(repo_root),
                env=child_environment,
                check=False,
                shell=False,
            )
        except OSError as exc:
            print(
                f"run-runner-requests: failed to start {request_file}: {exc}",
                file=sys.stderr,
            )
            return 1
        if completed.returncode != 0:
            status = shell_compatible_status(completed.returncode)
            failure = (
                f"signal {-completed.returncode}; exit {status}"
                if completed.returncode < 0
                else f"exit {status}"
            )
            print(
                f"run-runner-requests: {request_file} failed "
                f"({failure})",
                file=sys.stderr,
            )
            return status
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run Speckit Pro runner request files in the given order."
    )
    parser.add_argument("request_files", nargs="+")
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    return run_runner_requests(repo_root, args.request_files)


if __name__ == "__main__":
    raise SystemExit(main())
