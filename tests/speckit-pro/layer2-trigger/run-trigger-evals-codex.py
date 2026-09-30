#!/usr/bin/env python3
"""Resolve and optionally run Codex Layer 2 trigger evals."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = (SCRIPT_DIR / "../../../speckit-pro").resolve()
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))
import trigger_evidence as evidence_records  # noqa: E402


def eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def main(argv: list[str]) -> int:
    skill = argv[0] if argv else "speckit-coach"
    codex_eval_dir = PLUGIN_ROOT / "../tests/speckit-pro/layer2-trigger/codex-evals"
    eval_file = codex_eval_dir / f"{skill}-trigger.json"

    if not eval_file.is_file():
        eprint(f"ERROR: Eval file not found for: {skill}")
        eprint("Available Codex trigger evals:")
        for name in evidence_records.available_evals(codex_eval_dir):
            eprint(name)
        return 1

    # A Codex overlay wins; a merged skill's Codex text lives in skills/ as host blocks.
    skill_path = PLUGIN_ROOT / f"codex-skills/{skill}"
    if not (skill_path / "SKILL.md").is_file():
        skill_path = PLUGIN_ROOT / f"skills/{skill}"
    if not (skill_path / "SKILL.md").is_file():
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
