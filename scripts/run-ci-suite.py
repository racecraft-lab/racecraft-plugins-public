#!/usr/bin/env python3
"""Run the CI suite (layers 1, 4, 5, 6, 7) with no env prefix or redirect.

Replaces the raw AGENTS.md section 2 command. It sets the same variables for
the child process only and sends the same runner request.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from process_status import shell_compatible_status  # noqa: E402
from speckit_pro_runner.suite_checkout_lock import (  # noqa: E402
    REFUSED_STATUS,
    SuiteLockHeld,
    SuiteLockUnavailable,
    hold_suite_lock,
)

REQUEST_FILE = (
    REPO_ROOT
    / "tests/speckit-pro/unit/fixtures/runner-gates/requests/run-ci-suite.json"
)


def build_environment(base: Mapping[str, str]) -> dict[str, str]:
    environment = dict(base)
    environment.update(
        {
            "SPECKIT_SKIP_TOOLCHAIN_CHECK": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "PYTHONPATH": str(PLUGIN_ROOT),
        }
    )
    return environment


def main(argv: Sequence[str] | None = None) -> int:
    argparse.ArgumentParser(description="Run the CI suite.").parse_args(argv)
    try:
        request = REQUEST_FILE.read_bytes()
    except OSError as exc:
        print(f"run-ci-suite: unable to read {REQUEST_FILE.name}: {exc}", file=sys.stderr)
        return 1
    try:
        with hold_suite_lock(REPO_ROOT) as suite_lock:
            if suite_lock.unguarded_warning:
                print(suite_lock.unguarded_warning, file=sys.stderr)
            completed = subprocess.run(
                [sys.executable, "-m", "speckit_pro_runner"],
                input=request,
                cwd=str(REPO_ROOT),
                env=suite_lock.environment(build_environment(os.environ)),
                check=False,
                shell=False,
            )
    except (SuiteLockHeld, SuiteLockUnavailable) as exc:
        print(f"run-ci-suite: {exc}", file=sys.stderr)
        return REFUSED_STATUS
    return shell_compatible_status(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
