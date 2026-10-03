#!/usr/bin/env python3
"""Setup leaves the scaffold worktree directory ignored in a consumer repository."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted
from host_skill_views import host_skill_root
from script_loader import load_script

SCRIPT = Path(__file__).resolve().parents[3] / "speckit-pro/scripts/agent-memory-ignore.py"
PROBE = ".worktrees/__speckit_worktree_probe__"


class WorktreesIgnoreTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        self.tool = load_script("agent_memory_ignore", SCRIPT)

    def ignored(self):
        probe = subprocess.run(["git", "check-ignore", "-q", ".worktrees/x"], cwd=self.root, check=False)
        return probe.returncode == 0

    def test_apply_ignores_worktrees_and_a_second_run_changes_nothing(self):
        (self.root / ".gitignore").write_text("*.cache\n")
        self.assertFalse(self.ignored())
        code, report = self.tool.run(self.root, "check", "worktrees")
        self.assertNotEqual(code, 0)
        self.assertEqual(report["unignored_paths"], [PROBE])
        self.assertEqual(self.tool.run(self.root, "apply", "worktrees")[0], 0)
        self.assertTrue(self.ignored())
        first = (self.root / ".gitignore").read_text()
        self.assertEqual(first, "*.cache\n/.worktrees/\n")
        code, report = self.tool.run(self.root, "apply", "worktrees")
        self.assertEqual((code, report["changed"]), (0, False))
        self.assertEqual((self.root / ".gitignore").read_text(), first)

    def test_an_unfixed_check_reports_worktree_remediation_not_memory_text(self):
        _, report = self.tool.run(self.root, "check", "worktrees")
        self.assertIn(".worktrees/", report["remediation"])
        self.assertNotIn("memory", report["remediation"])

    def test_apply_leaves_the_memory_rule_out(self):
        self.tool.run(self.root, "apply", "worktrees")
        self.assertNotIn("agent-memory-local", (self.root / ".gitignore").read_text())

    def test_a_later_rule_beats_an_earlier_negation(self):
        (self.root / ".gitignore").write_text("!/.worktrees/\n")
        self.assertEqual(self.tool.run(self.root, "apply", "worktrees")[0], 0)
        self.assertTrue(self.ignored())

    def test_command_line_target_flag_runs_the_same_repair(self):
        argv = [sys.executable, str(SCRIPT), "--mode", "apply", "--target", "worktrees", "--repo-root", str(self.root)]
        self.assertEqual(subprocess.run(argv, capture_output=True, check=False).returncode, 0)
        self.assertTrue(self.ignored())

    def test_install_and_upgrade_run_it_on_both_hosts(self):
        for host in ("claude", "codex"):
            for operation in ("speckit-install", "speckit-upgrade"):
                path = host_skill_root(host) / operation / "SKILL.md"
                with self.subTest(path=path):
                    self.assertIn("--mode apply --target worktrees", path.read_text())


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(WorktreesIgnoreTests), label="test-worktrees-ignore"))
