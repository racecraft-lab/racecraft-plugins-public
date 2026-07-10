#!/usr/bin/env python3
"""Manual Layer 3 functional eval helper for Codex without Bash."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[3] / "speckit-pro"


def eval_roots(root: Path) -> tuple[Path, Path]:
    base = root / ".." / "tests" / "speckit-pro" / "layer3-functional"
    return (base / "codex-evals", base / "evals")


def eval_file_for(root: Path, skill: str) -> Path | None:
    codex_dir, shared_dir = eval_roots(root)
    codex_file = codex_dir / f"{skill}-evals.json"
    if codex_file.is_file():
        return codex_file
    shared_file = shared_dir / f"{skill}-evals.json"
    if shared_file.is_file():
        return shared_file
    return None


def available_evals(root: Path) -> list[str]:
    paths: set[str] = set()
    for directory in eval_roots(root):
        paths.update(path.as_posix() for path in directory.glob("*-evals.json"))
    return [Path(path).name.removesuffix("-evals.json") for path in sorted(paths)]


def eval_count(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(len(data.get("evals", [])))
    except Exception:
        return "?"


def print_eval_prompts(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for item in data.get("evals", []):
        print(f"  [{item['id']}] {item['prompt'][:100]}...")
        for expectation in item.get("expectations", []):
            print(f"      - {expectation[:80]}")
        print()


def main(argv: list[str]) -> int:
    root = plugin_root()
    skill = argv[0] if argv else "speckit-coach"
    eval_file = eval_file_for(root, skill)
    skill_path = root / "codex-skills" / skill

    if eval_file is None:
        print(f"ERROR: Eval file not found for: {skill}", file=sys.stderr)
        print("Available Codex functional evals:", file=sys.stderr)
        for name in available_evals(root):
            print(name, file=sys.stderr)
        return 1

    if not skill_path.is_dir():
        print(f"ERROR: Codex skill not found: {skill_path}", file=sys.stderr)
        return 1

    print(f"Layer 3 Codex Functional Evals: {skill}")
    print("======================================")
    print(f"Eval file:  {eval_file}")
    print(f"Skill path: {skill_path}")
    print(f"Eval count: {eval_count(eval_file)}")
    print("")
    print("To run manually in Codex:")
    print("  1. Start a Codex session with SpecKit Pro installed")
    print(f"  2. Invoke /{skill}, load ${skill}, or route through @SpecKit Pro")
    print("  3. Send each prompt from the evals JSON")
    print("  4. Verify the response matches the expectations")
    print("")
    print("Eval prompts:")
    print("")
    print_eval_prompts(eval_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
