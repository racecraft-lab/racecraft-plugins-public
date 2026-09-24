#!/usr/bin/env python3
"""Repo-side dispatcher for manifest-backed deterministic test layers.

This script is intentionally NOT shipped in any plugin payload. Every manifest
entry it dispatches is Python-authoritative; non-Python entries fail closed.

The suite gate (``speckit_pro_runner.gates.suite``) invokes this as an external
argv command (``python tests/speckit-pro/run-layer-scripts.py --layer <id|key>``) and
maps the process exit code to a runner status: 0 -> ok, 1 -> expected_failure,
2 -> input_error, 3 -> missing_prerequisite, 4 -> subprocess_failure.

A layer's scripts run as separate child processes, several at a time. The default
is 4 or the CPU count, whichever is lower; ``SPECKIT_LAYER_WORKERS`` overrides it
exactly (``1`` runs them one by one). Results are reported in manifest order
whatever order the children finish in.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

TEST_LIB = Path(__file__).resolve().parent / "lib"
if str(TEST_LIB) not in sys.path:
    sys.path.insert(0, str(TEST_LIB))

from test_result import child_check_status  # noqa: E402

SUITE_MANIFEST = "tests/speckit-pro/suite-manifest.json"
LAYER_WORKERS_VARIABLE = "SPECKIT_LAYER_WORKERS"
DEFAULT_LAYER_WORKERS = 4
# Scripts that run alone, after the parallel batch, because their scheduling and
# timing assertions fail under a loaded host. Each costs a few seconds.
SERIAL_SCRIPTS = frozenset({
    "tests/speckit-pro/unit/test-native-eval-execution.py",
})


def resolve_repo_root() -> Path | None:
    repo_root = Path(__file__).resolve().parents[2]
    if (repo_root / "speckit-pro" / "speckit_pro_runner").is_dir() and (repo_root / "tests" / "speckit-pro").is_dir():
        return repo_root
    return None


def load_manifest(repo_root: Path) -> dict:
    return json.loads((repo_root / SUITE_MANIFEST).read_text(encoding="utf-8"))


def canonical_layer_entry(repo_root: Path, selector: str) -> dict | None:
    """Resolve one exact numeric ID or semantic key through the manifest."""
    matches = [
        entry
        for entry in load_manifest(repo_root).get("layers", [])
        if not entry.get("live_only")
        and entry.get("id") != "toolchain"
        and entry.get("dispatch") == "python-module"
        and selector in {entry.get("id"), entry.get("key")}
    ]
    return matches[0] if len(matches) == 1 else None


def canonical_test_scripts(repo_root: Path, layer: str) -> list[Path]:
    """Return the layer's dispatch roster from suite-manifest.json (not run-all.sh).

    The manifest's per-layer ``scripts[]`` is the single source of truth for the
    dispatch set.
    """
    entry = canonical_layer_entry(repo_root, layer)
    if entry is None:
        return []
    return [repo_root / script["path"] for script in entry.get("scripts", [])]


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


def layer_workers() -> int:
    """Return how many layer scripts may run at once; an unset or invalid value uses the default."""
    raw = os.environ.get(LAYER_WORKERS_VARIABLE, "")
    if raw.isdigit() and int(raw) >= 1:
        return int(raw)
    return min(DEFAULT_LAYER_WORKERS, os.cpu_count() or 1)


def run_script(test_path: Path, repo_root: Path) -> tuple[str, bool, str]:
    if not test_path.is_file():
        return (rel(test_path, repo_root), False, "test file missing")
    if test_path.suffix != ".py":
        return (rel(test_path, repo_root), False, "non-Python manifest entry")
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
    if not ok and completed.stderr.strip():
        # Surface the child's own failure report; the summary line alone hides which unit failed.
        tail = "\n".join(completed.stderr.rstrip().splitlines()[-40:])
        detail = f"{detail}\n{tail}"
    return (rel(test_path, repo_root), ok, detail)


def run_script_suite(label: str, tests: list[Path], repo_root: Path) -> int:
    workers = min(layer_workers(), len(tests))
    if workers <= 1:
        checks = [run_script(test_path, repo_root) for test_path in tests]
    else:
        # Each script is its own child process, and children stay in this
        # dispatcher's process group, as in the serial loop. Executor.map yields
        # results in input order, so the PASS/FAIL lines and the summary keep
        # manifest order.
        pooled = [test_path for test_path in tests if rel(test_path, repo_root) not in SERIAL_SCRIPTS]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = dict(zip(pooled, pool.map(run_script, pooled, [repo_root] * len(pooled))))
        for test_path in tests:
            if test_path not in results:
                results[test_path] = run_script(test_path, repo_root)
        checks = [results[test_path] for test_path in tests]
    return emit_checks(label, checks)


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--layer":
        print("usage: run-layer-scripts.py --layer <id|key>", file=sys.stderr)
        return 2
    selector = argv[1]

    repo_root = resolve_repo_root()
    if repo_root is None:
        print("could not resolve repository root from run-layer-scripts.py location", file=sys.stderr)
        return 3

    manifest_path = repo_root / SUITE_MANIFEST
    if not manifest_path.is_file():
        print(f"missing prerequisite: {SUITE_MANIFEST} not found", file=sys.stderr)
        return 3

    layer = canonical_layer_entry(repo_root, selector)
    if layer is None:
        print(f"unsupported layer selector: {selector}", file=sys.stderr)
        return 2

    tests = [repo_root / script["path"] for script in layer.get("scripts", [])]
    if not tests:
        print(f"missing prerequisite: no layer {layer['id']} test entries in {SUITE_MANIFEST}", file=sys.stderr)
        return 3

    return run_script_suite(f"layer-{layer['id']} {layer['label'].lower()}", tests, repo_root)


if __name__ == "__main__":
    try:
        exit_code = main(sys.argv[1:])
    except Exception:
        traceback.print_exc()
        exit_code = 4
    raise SystemExit(exit_code)
