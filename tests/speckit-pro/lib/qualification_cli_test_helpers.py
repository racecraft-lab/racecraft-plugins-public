"""Shared subprocess helpers for deterministic qualification CLI tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
QUALIFICATION_RUNNER_PATH = (
    REPO_ROOT / "tests/speckit-pro/layer6-efficiency/run-codex-qualification.py"
)


def run_qualification_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(QUALIFICATION_RUNNER_PATH), *args],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=env,
        shell=False,
        check=False,
    )
