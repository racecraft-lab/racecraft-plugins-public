#!/usr/bin/env python3
"""Resolve and optionally run Codex Layer 2 trigger evals."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = (SCRIPT_DIR / "../../../speckit-pro").resolve()


def eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def trigger_names_for_available_message(paths: list[Path]) -> list[str]:
    existing: list[str] = []
    for root in paths:
        if root.is_dir():
            existing.extend(str(path) for path in root.glob("*-trigger.json"))
    return [Path(path).name.removesuffix("-trigger.json") for path in sorted(existing)]


def main(argv: list[str]) -> int:
    skill = argv[0] if argv else "speckit-coach"
    codex_eval_dir = PLUGIN_ROOT / "../tests/speckit-pro/layer2-trigger/codex-evals"
    shared_eval_dir = PLUGIN_ROOT / "../tests/speckit-pro/layer2-trigger/evals"
    codex_eval_file = codex_eval_dir / f"{skill}-trigger.json"
    shared_eval_file = shared_eval_dir / f"{skill}-trigger.json"

    if codex_eval_file.is_file():
        eval_file = codex_eval_file
    elif shared_eval_file.is_file():
        eval_file = shared_eval_file
    else:
        eprint(f"ERROR: Eval file not found for: {skill}")
        eprint("Available Codex trigger evals:")
        for name in trigger_names_for_available_message([codex_eval_dir, shared_eval_dir]):
            eprint(name)
        return 1

    skill_path = PLUGIN_ROOT / f"codex-skills/{skill}"
    if not skill_path.is_dir():
        eprint(f"ERROR: Codex skill not found: {skill_path}")
        return 1

    print(f"Eval file: {eval_file}")
    print(f"Skill path: {skill_path}")

    run_eval = any(arg == "--run" for arg in argv)
    if not run_eval:
        print("")
        eprint("Pass --run to invoke the codex CLI and execute the eval.")
        eprint("Without --run, this script only resolves paths and exits.")
        return 0

    if shutil.which("codex") is None:
        eprint("ERROR: --run was passed but codex CLI is not on PATH.")
        eprint("Install codex first: https://developers.openai.com/codex/")
        return 1

    py_args = [arg for arg in argv if arg != "--run"]
    os.execv(sys.executable, [sys.executable, str(SCRIPT_DIR / "run_codex_evals.py"), *py_args])
    return 127


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
