#!/usr/bin/env python3
"""Capture an ordered count-parity baseline from a Python port.

Unittest ports are loaded without invoking their ``__main__`` block and run
with ``CountingTestResult`` so their explicit ``subTest(msg=...)`` inventory is
preserved. Reporter/CLI ports with no unittest cases run in a child Python
process under ``VERBOSE=true`` and reuse the historical baseline parser.

CLI::

    python3 tests/speckit-pro/lib/capture_python_baseline.py \
        <script.py> [--out path] [script args...]
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import os
import subprocess
import sys
import unittest
from collections.abc import Iterator, Sequence
from pathlib import Path
from types import ModuleType

from capture_baseline import BaselineError, parse_verbose_lines, render_baseline
from test_result import CountingTestResult

BASELINE_DIR = "tests/speckit-pro/parity/bash-to-python"
UNNAMED_SUBTEST = "<subtest>"


def _validate_target(target: Path) -> Path:
    if target.suffix != ".py":
        raise BaselineError(f"target must be a .py file: {target}")
    if not target.is_file():
        raise BaselineError(f"target not found: {target}")
    return target.resolve()


@contextlib.contextmanager
def _loaded_module(target: Path, script_args: Sequence[str]) -> Iterator[ModuleType]:
    """Load ``target`` with script-like argv/path state, then restore the host."""
    digest = hashlib.sha256(str(target).encode("utf-8")).hexdigest()[:16]
    module_name = f"_xplat010_baseline_{target.stem}_{digest}"
    spec = importlib.util.spec_from_file_location(module_name, target)
    if spec is None or spec.loader is None:
        raise BaselineError(f"unable to load Python target: {target}")

    original_argv = sys.argv[:]
    original_path = sys.path[:]
    original_cwd = Path.cwd()
    original_environment = os.environ.copy()
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    sys.argv = [str(target), *script_args]
    sys.path.insert(0, str(target.parent))
    try:
        spec.loader.exec_module(module)
        yield module
    except BaselineError:
        raise
    except (Exception, SystemExit) as exc:
        raise BaselineError(
            f"unable to load or run Python target {target}: {type(exc).__name__}: {exc}"
        ) from exc
    finally:
        sys.modules.pop(module_name, None)
        sys.argv = original_argv
        sys.path[:] = original_path
        os.environ.clear()
        os.environ.update(original_environment)
        try:
            os.chdir(original_cwd)
        except OSError as exc:
            raise BaselineError(f"unable to restore capture cwd {original_cwd}: {exc}") from exc


def _suite_from_module(module: ModuleType, target: Path) -> unittest.TestSuite:
    build_suite = getattr(module, "build_suite", None)
    if build_suite is not None:
        if not callable(build_suite):
            raise BaselineError(f"build_suite is not callable in Python target: {target}")
        suite = build_suite()
    else:
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    if not isinstance(suite, unittest.TestSuite):
        raise BaselineError(f"build_suite did not return unittest.TestSuite for target: {target}")
    return suite


def _normalize_subtest_names(names: Sequence[str], target: Path) -> list[str]:
    normalized: list[str] = []
    for index, name in enumerate(names, start=1):
        clean_name = str(name).strip()
        if not clean_name:
            raise BaselineError(f"empty subtest name at counted unit {index} in target: {target}")
        if clean_name == UNNAMED_SUBTEST:
            raise BaselineError(f"unnamed subtest at counted unit {index} in target: {target}")
        if "\n" in clean_name or "\r" in clean_name:
            raise BaselineError(f"multiline subtest name at counted unit {index} in target: {target}")
        normalized.append(clean_name)
    return normalized


def _capture_unittest(
    suite: unittest.TestSuite,
    target: Path,
) -> tuple[list[tuple[str, str]], int]:
    result = CountingTestResult(stream=None, descriptions=False, verbosity=0)
    suite.run(result)
    names = _normalize_subtest_names(result.subtest_names, target)
    unnamed_units = result.units_total - len(names)
    if unnamed_units:
        raise BaselineError(
            f"{unnamed_units} counted non-subtest method(s) in {target}; "
            "ordered names cannot be preserved 1:1"
        )
    exit_code = 0 if result.wasSuccessful() and result.units_passed == result.units_total else 1
    return [(name, "PASS") for name in names], exit_code


def _capture_reporter(target: Path, script_args: Sequence[str]) -> tuple[list[tuple[str, str]], int]:
    environment = os.environ.copy()
    environment["VERBOSE"] = "true"
    try:
        completed = subprocess.run(
            [sys.executable, str(target), *script_args],
            text=True,
            capture_output=True,
            env=environment,
            shell=False,
            check=False,
        )
    except OSError as exc:
        raise BaselineError(f"unable to execute Python target {target}: {exc}") from exc
    combined_output = completed.stdout + "\n" + completed.stderr
    return parse_verbose_lines(combined_output), completed.returncode


def capture(
    target: Path,
    out_path: Path,
    *,
    script_args: Sequence[str] = (),
) -> dict[str, object]:
    """Capture ``target``, write its inventory, and return target exit metadata."""
    target = _validate_target(target)
    with _loaded_module(target, script_args) as module:
        suite = _suite_from_module(module, target)
        case_count = suite.countTestCases()
        if case_count:
            results, exit_code = _capture_unittest(suite, target)
            mode = "unittest"

    if not case_count:
        results, exit_code = _capture_reporter(target, script_args)
        mode = "reporter"

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8", newline="\n") as baseline_file:
            baseline_file.write(render_baseline(results))
    except OSError as exc:
        raise BaselineError(f"unable to write baseline {out_path}: {exc}") from exc
    return {
        "baseline_path": out_path.as_posix(),
        "total": len(results),
        "exit_code": exit_code,
        "mode": mode,
    }


def _parse_cli(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture an ordered count-parity baseline for a Python port.",
        usage="%(prog)s script.py [--out PATH] [--] [script args ...]",
    )
    parser.add_argument("script", help="Python port to capture")
    parser.add_argument("--out", help="Output baseline path")
    parser.add_argument("script_args", nargs="*", help="Arguments passed verbatim to CLI-style ports")

    if not argv or argv[0] in {"-h", "--help"}:
        return parser.parse_args(list(argv))

    script = argv[0]
    remaining = list(argv[1:])
    out: str | None = None
    if remaining and remaining[0] == "--out":
        if len(remaining) < 2:
            parser.error("argument --out: expected one argument")
        out = remaining[1]
        remaining = remaining[2:]
    elif remaining and remaining[0].startswith("--out="):
        out = remaining[0].split("=", 1)[1]
        if not out:
            parser.error("argument --out: expected one argument")
        remaining = remaining[1:]
    if remaining and remaining[0] == "--":
        remaining = remaining[1:]
    return argparse.Namespace(script=script, out=out, script_args=remaining)


def main(argv: Sequence[str]) -> int:
    args = _parse_cli(argv)
    target = Path(args.script)
    repo_root = Path(__file__).resolve().parents[3]
    out_path = Path(args.out) if args.out else repo_root / BASELINE_DIR / f"{target.stem}-baseline.txt"
    try:
        summary = capture(target, out_path, script_args=tuple(args.script_args))
    except BaselineError as exc:
        print(f"capture-python-baseline: {exc}", file=sys.stderr)
        return 1
    print(
        f"capture-python-baseline: wrote {summary['baseline_path']} "
        f"(TOTAL: {summary['total']}, target_exit_code={summary['exit_code']}, mode={summary['mode']})"
    )
    return int(summary["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
