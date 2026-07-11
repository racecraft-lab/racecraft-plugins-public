#!/usr/bin/env python3
"""PostToolUse hook that runs Layer 1 structural validation for plugin edits."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


TRIGGER_SUFFIXES = (
    "/SKILL.md",
    "/.claude-plugin/plugin.json",
    "/.codex-plugin/plugin.json",
    "/.claude-plugin/marketplace.json",
    "/release-please-config.json",
    "/.release-please-manifest.json",
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def file_path_from_payload(text: str) -> str:
    try:
        payload: Any = json.loads(text)
    except json.JSONDecodeError:
        return ""
    if not isinstance(payload, dict):
        return ""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    file_path = tool_input.get("file_path")
    return file_path if isinstance(file_path, str) else ""


def should_validate(file_path: str) -> bool:
    normalized = file_path.replace("\\", "/")
    if any(normalized.endswith(suffix) for suffix in TRIGGER_SUFFIXES):
        return True
    return "/commands/" in normalized and normalized.endswith(".md")


def repo_relative(file_path: str, repo_root: Path) -> str:
    path = Path(file_path)
    try:
        return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix()
    except ValueError:
        return file_path.replace("\\", "/")


def plugin_dir_for(rel_path: str) -> str:
    return "speckit-pro" if rel_path.startswith("speckit-pro/") else "speckit-pro"


def structural_runner(repo_root: Path) -> Path:
    return repo_root / "tests" / "speckit-pro" / "run-layer-scripts.py"


def run_layer1(repo_root: Path) -> subprocess.CompletedProcess[str]:
    runner = structural_runner(repo_root)
    if not runner.is_file():
        return subprocess.CompletedProcess([sys.executable, str(runner), "--layer", "1"], 0, "", "")
    env = os.environ.copy()
    plugin_root = repo_root / "speckit-pro"
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = plugin_root.as_posix() if not existing else f"{plugin_root.as_posix()}{os.pathsep}{existing}"
    return subprocess.run(
        [sys.executable, str(runner), "--layer", "1"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        env=env,
        shell=False,
        check=False,
    )


def handle_payload(payload_text: str, *, repo_root: Path | None = None) -> tuple[int, str]:
    repo_root = repo_root or repo_root_from_script()
    file_path = file_path_from_payload(payload_text)
    if not file_path or not should_validate(file_path):
        return 0, ""

    rel_path = repo_relative(file_path, repo_root)
    plugin_dir = plugin_dir_for(rel_path)
    target = repo_root / plugin_dir
    if not target.is_dir():
        return 0, ""

    completed = run_layer1(repo_root)
    if completed.returncode == 0:
        return 0, ""
    output = completed.stdout + completed.stderr
    message = f"Warning: Layer 1 structural test failed for {plugin_dir} after edit to {rel_path}:\n\n{output}\n"
    return 2, message


def main() -> int:
    exit_code, message = handle_payload(sys.stdin.read())
    if message:
        print(message, file=sys.stderr, end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
