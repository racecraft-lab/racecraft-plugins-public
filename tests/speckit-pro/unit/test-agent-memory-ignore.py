#!/usr/bin/env python3
"""Consumer repository ignore checks for Claude's persistent agent memory."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted


SCRIPT = Path(__file__).resolve().parents[3] / "speckit-pro/scripts/agent-memory-ignore.py"
REPO_ROOT = SCRIPT.parents[2]


class AgentMemoryIgnoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "consumer"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def run_tool(self, mode):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--mode", mode, "--repo-root", str(self.root)],
            text=True, capture_output=True, check=False,
        )
        return result.returncode, json.loads(result.stdout)

    def test_apply_preserves_content_and_is_idempotent_for_root_and_nested_memory(self):
        (self.root / ".gitignore").write_text("# existing\n*.cache\n")
        nested = self.root / "feature/.claude/agent-memory-local"
        nested.mkdir(parents=True)
        (nested / "note.md").write_text("private memory\n")
        root_memory = self.root / ".claude/agent-memory-local"
        root_memory.mkdir(parents=True)
        (root_memory / "note.md").write_text("private memory\n")
        self.assertNotEqual(self.run_tool("check")[0], 0)
        self.assertEqual(self.run_tool("apply")[0], 0)
        first = (self.root / ".gitignore").read_text()
        self.assertEqual(first, "# existing\n*.cache\n**/.claude/agent-memory-local/\n")
        self.assertEqual(self.run_tool("apply")[0], 0)
        self.assertEqual((self.root / ".gitignore").read_text(), first)
        self.assertEqual(self.run_tool("check")[0], 0)
        (self.root / "unrelated.txt").write_text("still visible\n")
        status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=self.root, text=True, capture_output=True, check=True).stdout
        self.assertNotIn("note.md", status)
        self.assertIn("unrelated.txt", status)
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        tracked = subprocess.run(["git", "ls-files"], cwd=self.root, text=True, capture_output=True, check=True).stdout
        self.assertNotIn("note.md", tracked)

    def test_existing_effective_rule_needs_no_edit(self):
        rule = "**/.claude/agent-memory-local/**\n"
        (self.root / ".gitignore").write_text(rule)
        self.assertEqual(self.run_tool("apply")[0], 0)
        self.assertEqual((self.root / ".gitignore").read_text(), rule)

    def test_nested_override_is_reported(self):
        (self.root / "feature").mkdir()
        (self.root / "feature/.gitignore").write_text("!**/.claude/agent-memory-local/\n!**/.claude/agent-memory-local/**\n")
        code, report = self.run_tool("apply")
        self.assertNotEqual(code, 0)
        self.assertIn("feature", str(report))

    def test_tracked_memory_is_reported_without_deletion(self):
        self.assertEqual(self.run_tool("apply")[0], 0)
        memory = self.root / ".claude/agent-memory-local/keep.md"
        memory.parent.mkdir(parents=True)
        memory.write_text("keep me\n")
        subprocess.run(["git", "add", "-f", str(memory.relative_to(self.root))], cwd=self.root, check=True)
        code, report = self.run_tool("check")
        self.assertNotEqual(code, 0)
        self.assertIn(".claude/agent-memory-local/keep.md", report["tracked_memory"])
        self.assertEqual(memory.read_text(), "keep me\n")

    def test_symlink_ignore_file_is_rejected(self):
        outside = Path(self.temp.name) / "outside"
        outside.write_text("untouched\n")
        (self.root / ".gitignore").symlink_to(outside)
        code, report = self.run_tool("apply")
        self.assertNotEqual(code, 0)
        self.assertIn("symlink", str(report))
        self.assertEqual(outside.read_text(), "untouched\n")

    def test_symlink_memory_directory_is_rejected(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.root / ".claude").symlink_to(outside, target_is_directory=True)
        code, report = self.run_tool("apply")
        self.assertNotEqual(code, 0)
        self.assertIn("symlink", str(report))
        self.assertFalse((self.root / ".gitignore").exists())

    def test_both_clients_include_repair_in_setup_and_check_before_dispatch(self):
        for client in ("skills", "codex-skills"):
            for operation in ("speckit-install", "speckit-upgrade"):
                path = REPO_ROOT / "speckit-pro" / client / operation / "SKILL.md"
                with self.subTest(path=path):
                    body = path.read_text()
                    self.assertIn("agent-memory-ignore.py", body)
                    self.assertIn("--mode apply", body)
        prerequisites = (REPO_ROOT / "speckit-pro/skills/speckit-autopilot/references/prerequisites.md").read_text()
        self.assertIn("agent-memory-ignore.py", prerequisites)
        self.assertIn("--mode check", prerequisites)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(AgentMemoryIgnoreTests), label="test-agent-memory-ignore"))
