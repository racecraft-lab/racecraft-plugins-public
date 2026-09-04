#!/usr/bin/env python3
"""Run every Layer-7 fixture class."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TEST_LIB = SCRIPT_DIR.parent / "lib"
if str(TEST_LIB) not in sys.path:
    sys.path.insert(0, str(TEST_LIB))

from test_result import child_check_status  # noqa: E402

RUNNERS = {
    "1": SCRIPT_DIR / "run-dispatch-fixtures.py",
    "2": SCRIPT_DIR / "run-return-format-fixtures.py",
    "3": SCRIPT_DIR / "run-e2e-fixtures.py",
    "4": SCRIPT_DIR / "run-grounding-fixtures.py",
}


def parse_args(argv: list[str]) -> tuple[str, str]:
    mode = "--replay"
    selected = "all"
    index = 0
    while index < len(argv):
        value = argv[index]
        if value in {"--replay", "--live"}:
            mode = value
        elif value == "--class":
            if index + 1 >= len(argv):
                raise ValueError("--class requires a value")
            selected = argv[index + 1]
            index += 1
        index += 1
    if selected != "all" and selected not in RUNNERS:
        raise ValueError(f"unknown Layer-7 class: {selected}")
    return mode, selected


def run_class(class_id: str, mode: str) -> bool:
    print("\n" + "=" * 66)
    print(f"  Layer 7 - Class {class_id}")
    print("=" * 66)
    completed = subprocess.run(
        [sys.executable, str(RUNNERS[class_id]), mode],
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    passed, detail = child_check_status(
        completed.returncode,
        completed.stdout,
        RUNNERS[class_id].stem,
    )
    if not passed:
        print(f"FAIL Layer 7 class {class_id}: {detail}", file=sys.stderr)
    return passed


def main(argv: list[str]) -> int:
    try:
        mode, selected = parse_args(argv)
    except ValueError as exc:
        print(f"run-all-fixtures: {exc}", file=sys.stderr)
        return 2
    classes = list(RUNNERS) if selected == "all" else [selected]
    results = [run_class(class_id, mode) for class_id in classes]
    passed_count = sum(results)
    passed = bool(results) and passed_count == len(results)
    print("\n" + "=" * 66)
    print(f"  Layer 7 {'PASSED' if passed else 'FAILED'}")
    print("=" * 66)
    print(f"run-all-fixtures: {passed_count}/{len(results)} passed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
