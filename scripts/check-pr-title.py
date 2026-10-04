#!/usr/bin/env python3
"""Check a PR title with the title gate: check-pr-title.py "<title>".

Replaces the raw AGENTS.md section 2 command. It builds the gate request
itself and passes the title to the child process through TITLE.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


REQUEST = {
    "schema_version": "1.0",
    "request_id": "validate-pr-title-live",
    "helper_id": "release-readiness",
    "operation": "validate-pr-title",
    "mode": "read_only",
    "inputs": {"title_env": "TITLE"},
}


def build_environment(base: Mapping[str, str], title: str) -> dict[str, str]:
    environment = dict(base)
    environment["TITLE"] = title
    environment["PYTHONPATH"] = str(REPO_ROOT / "speckit-pro")
    return environment


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a PR title with the title gate.")
    parser.add_argument("title")
    args = parser.parse_args(argv)
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(REQUEST).encode(),
        cwd=str(REPO_ROOT),
        env=build_environment(os.environ, args.title),
        check=False,
        shell=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
