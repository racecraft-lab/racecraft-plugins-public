"""Run the speckit-pro runner as a subprocess for unit tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"


def runner_env(
    overrides: Mapping[str, str] | None = None,
    *,
    defaults: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """The process environment with the plugin on PYTHONPATH.

    ``defaults`` fill keys the caller's environment leaves unset; ``overrides`` win.
    """
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(PLUGIN_ROOT) if not existing else f"{PLUGIN_ROOT}{os.pathsep}{existing}"
    for key, value in (defaults or {}).items():
        env.setdefault(key, value)
    env.update(overrides or {})
    return env


def run_runner(
    request: object,
    *,
    cwd: Path = REPO_ROOT,
    extra_env: Mapping[str, str] | None = None,
    env_defaults: Mapping[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any], list[dict[str, Any]]]:
    """Send ``request`` (a document or raw text) to the runner on stdin.

    Returns the finished process, its parsed response document (empty when it
    wrote none), and the JSON records it wrote to stderr.
    """
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=request if isinstance(request, str) else json.dumps(request),
        text=True,
        capture_output=True,
        cwd=cwd,
        env=runner_env(extra_env, defaults=env_defaults),
        shell=False,
        check=False,
    )
    response = json.loads(completed.stdout) if completed.stdout.strip() else {}
    stderr_records = [json.loads(line) for line in completed.stderr.splitlines() if line.strip()]
    return completed, response, stderr_records


def command_stdin_fixture(command: str) -> Path:
    """The repository path of the single stdin fixture an authoritative command reads."""
    if "<" not in command:
        raise AssertionError(f"authoritative_command must include a stdin fixture: {command}")
    stdin_path = command.split("<", 1)[1].strip()
    if not stdin_path or any(char.isspace() for char in stdin_path):
        raise AssertionError(f"authoritative_command must use one stdin fixture path: {command}")
    return REPO_ROOT / stdin_path


def assert_runner_response(case: Any, response: dict[str, Any], status: str, exit_code: int) -> None:
    """The response envelope every runner reply carries."""
    case.assertEqual(response["schema_version"], "1.0")
    case.assertEqual(response["status"], status)
    case.assertEqual(response["exit_code"], exit_code)
    case.assertIsNone(response["legacy_exit_code"])
    case.assertIsInstance(response["diagnostics"], list)
    case.assertIsInstance(response["data"], dict)
