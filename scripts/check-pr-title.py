#!/usr/bin/env python3
"""Check a PR title with the title gate: check-pr-title.py "<title>".

Replaces the raw AGENTS.md section 2 command. It sends the same gate request
and passes the title to the child process through TITLE.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from process_status import shell_compatible_status

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUEST_FILE = (
    REPO_ROOT
    / "tests/speckit-pro/unit/fixtures/runner-gates/requests/validate-pr-title-live.json"
)


def build_environment(base: Mapping[str, str], title: str) -> dict[str, str]:
    environment = dict(base)
    environment["TITLE"] = title
    environment["PYTHONPATH"] = str(REPO_ROOT / "speckit-pro")
    return environment


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a PR title with the title gate.")
    parser.add_argument("title")
    args = parser.parse_args(argv)
    try:
        request = REQUEST_FILE.read_bytes()
    except OSError as exc:
        print(f"check-pr-title: unable to read {REQUEST_FILE.name}: {exc}", file=sys.stderr)
        return 1
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=request,
        cwd=str(REPO_ROOT),
        env=build_environment(os.environ, args.title),
        check=False,
        shell=False,
    )
    return shell_compatible_status(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
