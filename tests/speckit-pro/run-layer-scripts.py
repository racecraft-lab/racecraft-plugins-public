#!/usr/bin/env python3
"""Repo-side dispatcher for manifest-backed test layers 1, 4, 5, 7, and 8.

This script is intentionally NOT shipped in any plugin payload. Every manifest
entry it dispatches is Python-authoritative; non-Python entries fail closed.

The suite gate (``speckit_pro_runner.gates.suite``) invokes this as an external
argv command (``python tests/speckit-pro/run-layer-scripts.py --layer 1|4|5|7|8``) and
maps the process exit code to a runner status: 0 -> ok, 1 -> expected_failure,
2 -> input_error, 3 -> missing_prerequisite, 4 -> subprocess_failure.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

TEST_LIB = Path(__file__).resolve().parent / "lib"
if str(TEST_LIB) not in sys.path:
    sys.path.insert(0, str(TEST_LIB))

from test_result import child_check_status  # noqa: E402

SUITE_MANIFEST = "tests/speckit-pro/suite-manifest.json"
LAYER_LABELS = {
    "1": "layer-1 structural validation",
    "4": "layer-4 python helper tests",
    "5": "layer-5 agent tool scoping",
    "7": "layer-7 integration fixtures",
    "8": "layer-8 parity fixtures",
}


def resolve_repo_root() -> Path | None:
    repo_root = Path(__file__).resolve().parents[2]
    if (repo_root / "speckit-pro" / "speckit_pro_runner").is_dir() and (repo_root / "tests" / "speckit-pro").is_dir():
        return repo_root
    return None


def canonical_test_scripts(repo_root: Path, layer: str) -> list[Path]:
    """Return the layer's dispatch roster from suite-manifest.json (not run-all.sh).

    The manifest's per-layer ``scripts[]`` is the single source of truth for the
    dispatch set.
    """
    manifest_path = repo_root / SUITE_MANIFEST
    if not manifest_path.is_file():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest.get("layers", []):
        if entry.get("id") == layer:
            return [repo_root / script["path"] for script in entry.get("scripts", [])]
    return []


def python_child_env(repo_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    plugin_root = repo_root / "speckit-pro"
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = plugin_root.as_posix() if not existing else f"{plugin_root.as_posix()}{os.pathsep}{existing}"
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "commit.gpgsign"
    env["GIT_CONFIG_VALUE_0"] = "false"
    return env


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


def run_script_suite(label: str, tests: list[Path], repo_root: Path) -> int:
    checks: list[tuple[str, bool, str]] = []
    for test_path in tests:
        if not test_path.is_file():
            checks.append((rel(test_path, repo_root), False, "test file missing"))
            continue
        if test_path.suffix != ".py":
            checks.append((rel(test_path, repo_root), False, "non-Python manifest entry"))
            continue
        env = python_child_env(repo_root)
        argv = [sys.executable, rel(test_path, repo_root)]
        completed = subprocess.run(
            argv,
            cwd=repo_root,
            text=True,
            capture_output=True,
            env=env,
            shell=False,
            check=False,
        )
        ok, detail = child_check_status(completed.returncode, completed.stdout, test_path.stem)
        checks.append((rel(test_path, repo_root), ok, detail))
    return emit_checks(label, checks)


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--layer" or argv[1] not in LAYER_LABELS:
        print("usage: run-layer-scripts.py --layer {1|4|5|7|8}", file=sys.stderr)
        return 2
    layer = argv[1]

    repo_root = resolve_repo_root()
    if repo_root is None:
        print("could not resolve repository root from run-layer-scripts.py location", file=sys.stderr)
        return 3

    manifest_path = repo_root / SUITE_MANIFEST
    if not manifest_path.is_file():
        print(f"missing prerequisite: {SUITE_MANIFEST} not found", file=sys.stderr)
        return 3

    tests = canonical_test_scripts(repo_root, layer)
    if not tests:
        print(f"missing prerequisite: no layer {layer} test entries in {SUITE_MANIFEST}", file=sys.stderr)
        return 3

    return run_script_suite(LAYER_LABELS[layer], tests, repo_root)


if __name__ == "__main__":
    try:
        exit_code = main(sys.argv[1:])
    except Exception:
        traceback.print_exc()
        exit_code = 4
    raise SystemExit(exit_code)
