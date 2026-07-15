#!/usr/bin/env python3
"""Run Claude Layer 3 functional evals without a shell dependency."""

from __future__ import annotations

import sys
from pathlib import Path

from preview_helpers import eval_count, print_eval_prompts


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[3] / "speckit-pro"


def eval_file_for(root: Path, skill: str) -> Path:
    return root / ".." / "tests" / "speckit-pro" / "layer3-functional" / "evals" / f"{skill}-evals.json"


def available_evals(root: Path) -> list[str]:
    eval_dir = root / ".." / "tests" / "speckit-pro" / "layer3-functional" / "evals"
    return [path.name.removesuffix("-evals.json") for path in sorted(eval_dir.glob("*-evals.json"))]


def resolve_skill_path(root: Path, skill: str) -> Path | None:
    claude_path = root / "skills" / skill
    if claude_path.is_dir():
        return claude_path
    codex_path = root / "codex-skills" / skill
    if codex_path.is_dir():
        return codex_path
    return None


def main(argv: list[str]) -> int:
    root = plugin_root()
    skill = argv[0] if argv else "speckit-coach"
    eval_file = eval_file_for(root, skill)

    if not eval_file.is_file():
        print(f"ERROR: Eval file not found: {eval_file}", file=sys.stderr)
        print("Available evals:", file=sys.stderr)
        for name in available_evals(root):
            print(name, file=sys.stderr)
        return 1

    skill_path = resolve_skill_path(root, skill)
    if skill_path is None:
        print(f"ERROR: Skill not found for requested skill '{skill}'.", file=sys.stderr)
        print("Searched locations:", file=sys.stderr)
        print(f"  - {root / 'skills' / skill}", file=sys.stderr)
        print(f"  - {root / 'codex-skills' / skill}", file=sys.stderr)
        return 1

    print(f"Layer 3 Functional Evals: {skill}")
    print("================================")
    print(f"Eval file:  {eval_file}")
    print(f"Skill path: {skill_path}")
    print(f"Eval count: {eval_count(eval_file)}")
    print("")
    print("To run manually:")
    print("  1. Start a session that can load the target skill")
    print(f"  2. Invoke /{skill} or explicitly load ${skill}")
    print("  3. Send each prompt from the evals JSON")
    print("  4. Verify responses match the expectations")
    print("")
    print("Eval prompts:")
    print("")
    print_eval_prompts(eval_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
