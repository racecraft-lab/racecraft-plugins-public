#!/usr/bin/env python3
"""Repo-side shell dispatcher for the legacy bash-backed test layers 1 and 4.

This script is intentionally NOT shipped in any plugin payload. It lives under
``tests/`` — a sibling of ``speckit-pro/`` that plugin install never copies and
the zero-bash payload guard never scans — so the literal ``bash`` dependency for
the remaining ``.sh`` structural (layer 1) and unit (layer 4) tests can live here
rather than inside ``speckit_pro_runner``. Keeping it out of the runner package
is what lets the shipped payload stay bash-free. The dependency is scheduled for
removal when XPLAT-010 ports the remaining ``.sh`` tests to Python.

The suite gate (``speckit_pro_runner.gates.suite``) invokes this as an external
argv command (``python tests/speckit-pro/run-layer-scripts.py --layer 1|4``) and
maps the process exit code to a runner status: 0 -> ok, 1 -> expected_failure,
2 -> input_error, 3 -> missing_prerequisite, 4 -> subprocess_failure.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

RUN_ALL_SCRIPT = "run-all.sh"
LAYER_LABELS = {
    "1": "layer-1 structural validation",
    "4": "layer-4 python helper tests",
}
LAYER_BOUNDS = {
    "1": ("# Layer 1:", "# Layer 2:"),
    "4": ("# Layer 4:", "# Layer 5:"),
}


def resolve_repo_root() -> Path | None:
    repo_root = Path(__file__).resolve().parents[2]
    if (repo_root / "speckit-pro" / "speckit_pro_runner").is_dir() and (repo_root / "tests" / "speckit-pro").is_dir():
        return repo_root
    return None


def bounded_section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start == -1:
        return ""
    end = text.find(end_marker, start + len(start_marker))
    if end == -1:
        return text[start:]
    return text[start:end]


def canonical_test_scripts(repo_root: Path, layer: str) -> list[Path]:
    script = repo_root / "tests" / "speckit-pro" / RUN_ALL_SCRIPT
    if not script.is_file():
        return []
    text = script.read_text(encoding="utf-8")
    start_marker, end_marker = LAYER_BOUNDS[layer]
    section = bounded_section(text, start_marker, end_marker)
    matches = re.findall(r'"\$TESTS_DIR/([^"]+)"', section)
    return [repo_root / "tests" / "speckit-pro" / match for match in matches]


def python_child_env(repo_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    plugin_root = repo_root / "speckit-pro"
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = plugin_root.as_posix() if not existing else f"{plugin_root.as_posix()}{os.pathsep}{existing}"
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "commit.gpgsign"
    env["GIT_CONFIG_VALUE_0"] = "false"
    return env


def last_summary_line(stdout: str) -> str:
    for line in reversed(stdout.splitlines()):
        if " passed" in line and "/" in line:
            return line
    return ""


def rel(path: Path, repo_root: Path) -> str:
    return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix()


def emit_checks(label: str, checks: list[tuple[str, bool, str]]) -> int:
    passed = 0
    for name, ok, detail in checks:
        if ok:
            passed += 1
            print(f"PASS {name}: {detail}")
        else:
            print(f"FAIL {name}: {detail}", file=sys.stderr)
    print(f"{label}: {passed}/{len(checks)} passed")
    return 0 if passed == len(checks) else 1


def run_script_suite(label: str, tests: list[Path], repo_root: Path, bash_executable: str) -> int:
    checks: list[tuple[str, bool, str]] = []
    for test_path in tests:
        if not test_path.is_file():
            checks.append((rel(test_path, repo_root), False, "test file missing"))
            continue
        env = python_child_env(repo_root)
        # Sanctioned repo-side shell dispatch of legacy .sh tests (XPLAT-010 scope).
        argv = [sys.executable, rel(test_path, repo_root)] if test_path.suffix == ".py" else [bash_executable, rel(test_path, repo_root)]
        completed = subprocess.run(
            argv,
            cwd=repo_root,
            text=True,
            capture_output=True,
            env=env,
            shell=False,
            check=False,
        )
        detail = last_summary_line(completed.stdout) or completed.stderr.strip().splitlines()[-1:] or ["no summary"]
        detail_text = detail[0] if isinstance(detail, list) else detail
        checks.append((rel(test_path, repo_root), completed.returncode == 0, detail_text))
    return emit_checks(label, checks)


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--layer" or argv[1] not in LAYER_LABELS:
        print("usage: run-layer-scripts.py --layer {1|4}", file=sys.stderr)
        return 2
    layer = argv[1]

    repo_root = resolve_repo_root()
    if repo_root is None:
        print("could not resolve repository root from run-layer-scripts.py location", file=sys.stderr)
        return 3

    script = repo_root / "tests" / "speckit-pro" / RUN_ALL_SCRIPT
    if not script.is_file():
        print(f"missing prerequisite: {rel(script, repo_root)} not found", file=sys.stderr)
        return 3

    tests = canonical_test_scripts(repo_root, layer)
    if not tests:
        print(f"missing prerequisite: no layer {layer} test entries parsed from run-all.sh", file=sys.stderr)
        return 3

    # Sanctioned repo-side shell dispatch: bash runs the legacy .sh layers until
    # XPLAT-010 ports them to Python. Report a missing prerequisite instead of
    # failing opaquely when .sh entries exist but no bash is available.
    found_bash = shutil.which("bash")
    bash_executable = found_bash or "/bin/bash"
    if any(test_path.suffix != ".py" for test_path in tests) and found_bash is None and not Path("/bin/bash").is_file():
        print("missing prerequisite: bash not found for legacy .sh test layers", file=sys.stderr)
        return 3

    return run_script_suite(LAYER_LABELS[layer], tests, repo_root, bash_executable)


if __name__ == "__main__":
    try:
        exit_code = main(sys.argv[1:])
    except Exception:
        traceback.print_exc()
        exit_code = 4
    raise SystemExit(exit_code)
