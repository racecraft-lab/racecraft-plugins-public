#!/usr/bin/env python3
"""Run the Claude Layer 2 trigger eval+improve loop via skill-creator."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = (SCRIPT_DIR / "../../../speckit-pro").resolve()


def eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def available_evals(eval_dir: Path) -> list[str]:
    return [path.name.removesuffix("-trigger.json") for path in sorted(eval_dir.glob("*.json"))]


def main(argv: list[str]) -> int:
    home = Path(os.environ.get("HOME", str(Path.home())))
    skill_creator = Path(
        os.environ.get(
            "SKILL_CREATOR_ROOT",
            str(home / ".claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator"),
        )
    )
    skill = argv[0] if argv else "speckit-coach"
    eval_dir = PLUGIN_ROOT / "../tests/speckit-pro/layer2-trigger/evals"
    eval_file = eval_dir / f"{skill}-trigger.json"
    skill_path = PLUGIN_ROOT / f"skills/{skill}"

    if not eval_file.is_file():
        eprint(f"ERROR: Eval file not found: {eval_file}")
        eprint("Available evals:")
        for name in available_evals(eval_dir):
            eprint(name)
        return 1

    if not skill_path.is_dir():
        eprint(f"ERROR: Skill not found: {skill_path}")
        return 1

    if not skill_creator.is_dir():
        eprint(f"ERROR: skill-creator not found at: {skill_creator}")
        eprint("Set SKILL_CREATOR_ROOT to the skill-creator skill directory.")
        return 1

    eprint(f"Running trigger eval+improve loop for: {skill}")
    eprint(f"Eval file: {eval_file}")
    eprint(f"Skill path: {skill_path}")
    eprint("Max iterations: 5, Holdout: 0.4")
    eprint()

    cmd = [
        sys.executable,
        "-m",
        "scripts.run_loop",
        "--eval-set",
        str(eval_file),
        "--skill-path",
        str(skill_path),
        "--max-iterations",
        "5",
        "--holdout",
        "0.4",
        "--runs-per-query",
        "3",
        "--trigger-threshold",
        "0.5",
        "--verbose",
    ]
    return subprocess.run(cmd, cwd=skill_creator, shell=False).returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
