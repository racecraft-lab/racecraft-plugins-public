#!/usr/bin/env python3
"""Every Codex subagent spawn passes `fork_turns="none"`.

Codex defaults an omitted `fork_turns` to `"all"`, which copies the caller's whole
history into the child (openai/codex `multi_agents_v2/spawn.rs`, rust-v0.160.0).
A fresh child already gets a self-contained task message, so the copy is pure
input cost, repeated for every child (#1317).
"""

from __future__ import annotations

import re
import sys
import tomllib
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
sys.path[:0] = [str(TEST_DIR.parent / "lib")]

from host_skill_views import host_skill_root  # noqa: E402
from test_result import run_counted  # noqa: E402

FORK = 'fork_turns="none"'
# A dispatch example names its role (`agent_type=...` or a quoted agent name) inside the call.
DISPATCH = re.compile(r'spawn_agent\((?:agent_type=|")')
PROSE_DISPATCH = re.compile(r"(?:Dispatch|Call|call)[^\n.]{0,40}`spawn_agent`|spawn_agent on the")
WINDOW = 3  # lines: the call may wrap its arguments


def dispatch_sites(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    return [(number + 1, "\n".join(lines[number:number + WINDOW]))
            for number, line in enumerate(lines) if DISPATCH.search(line)]


class CodexSpawnForkTests(unittest.TestCase):
    def test_every_dispatch_example_in_the_codex_skills_passes_fork_turns_none(self) -> None:
        root = host_skill_root("codex")
        sites = 0
        for path in sorted(root.rglob("*.md")):
            for number, window in dispatch_sites(path.read_text(encoding="utf-8")):
                sites += 1
                with self.subTest(file=str(path.relative_to(root)), line=number):
                    self.assertIn(FORK, window)
        self.assertGreater(sites, 0, "no dispatch examples found: the scan matched nothing")

    def test_every_codex_agent_that_dispatches_states_the_rule(self) -> None:
        checked = []
        for path in sorted((REPO_ROOT / "speckit-pro/codex-agents").glob("*.toml")):
            text = tomllib.loads(path.read_text(encoding="utf-8"))["developer_instructions"]
            if "spawn_agent" in text:
                checked.append(path.stem)
                with self.subTest(agent=path.stem):
                    self.assertIn(FORK, text)
        self.assertGreaterEqual(len(checked), 4, checked)

    def test_every_prose_dispatch_in_the_codex_skills_passes_fork_turns_none(self) -> None:
        root = host_skill_root("codex")
        for path in sorted(root.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            for match in PROSE_DISPATCH.finditer(text):
                with self.subTest(file=str(path.relative_to(root)), at=match.start()):
                    self.assertRegex(text[match.start():match.end() + 200], r'fork_turns[:=] ?"none"')

    def test_the_autopilot_names_the_default_that_costs_tokens(self) -> None:
        text = " ".join((host_skill_root("codex") / "speckit-autopilot/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn(f"Every `spawn_agent` call passes `{FORK}`", text)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-codex-spawn-fork-turns"))
