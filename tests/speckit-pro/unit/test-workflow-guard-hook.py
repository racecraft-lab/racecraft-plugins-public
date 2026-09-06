#!/usr/bin/env python3
"""Behavior tests for the shipped workflow guard hook.

Drives the script with the documented PreToolUse and Stop payloads against
scratch git repositories, so every deny and block path is exercised
without a live Claude Code or Codex session.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_LIB = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from test_result import run_counted  # noqa: E402

HOOK = REPO_ROOT / "speckit-pro" / "scripts" / "workflow-guard-hook.py"
VERSION = "workflow-guard-v1"
ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": "/nonexistent",
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "support@openai.com",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "support@openai.com",
       "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}


def run_hook(mode: str, data: dict, version: str = VERSION) -> tuple[int, dict, str]:
    result = subprocess.run(
        [sys.executable, str(HOOK), mode, version], input=json.dumps(data),
        capture_output=True, text=True, env=ENV, check=False,
    )
    out = json.loads(result.stdout) if result.stdout.strip() else {}
    return result.returncode, out, result.stderr


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, env=ENV, check=True).stdout


def shell(cwd: Path, command: str) -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}


class WorkflowGuardHookTests(unittest.TestCase):
    def test_lockfile_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            git(root, "init", "-q")
            (root / "pnpm-lock.yaml").write_text("", encoding="utf-8")
            with self.subTest(msg="npm under a pnpm lockfile is denied with the documented shape"):
                code, out, _ = run_hook("lockfile", shell(root, "npm install left-pad"))
                self.assertEqual(0, code)
                self.assertEqual("deny", out["hookSpecificOutput"]["permissionDecision"])
                self.assertEqual("PreToolUse", out["hookSpecificOutput"]["hookEventName"])
                self.assertIn("pnpm", out["hookSpecificOutput"]["permissionDecisionReason"])
            with self.subTest(msg="npx is npm"):
                self.assertEqual("deny", run_hook("lockfile", shell(root, "npx vitest run"))[1]["hookSpecificOutput"]["permissionDecision"])
            with self.subTest(msg="the lockfile's own manager passes"):
                self.assertEqual({}, run_hook("lockfile", shell(root, "pnpm install && pnpm test"))[1])
            with self.subTest(msg="a subdirectory inherits the repository lockfile"):
                (root / "packages" / "a").mkdir(parents=True)
                self.assertEqual("deny", run_hook("lockfile", shell(root / "packages" / "a", "yarn add x"))[1]["hookSpecificOutput"]["permissionDecision"])
            with self.subTest(msg="commands without a package manager are not a decision"):
                self.assertEqual({}, run_hook("lockfile", shell(root, "git status && ls node_modules/.bin/npm-run-all"))[1])
            with self.subTest(msg="a path segment containing a manager name is not an invocation"):
                self.assertEqual({}, run_hook("lockfile", shell(root, "cat docs/npm-notes.md"))[1])
            with self.subTest(msg="tools without a command string are ignored"):
                self.assertEqual({}, run_hook("lockfile", {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": "npm.md"}, "cwd": str(root)})[1])
            (root / "yarn.lock").write_text("", encoding="utf-8")
            with self.subTest(msg="two lockfile kinds are ambiguous, so no decision"):
                self.assertEqual({}, run_hook("lockfile", shell(root, "npm install"))[1])
        with tempfile.TemporaryDirectory() as tmp:
            with self.subTest(msg="no lockfile means no decision"):
                self.assertEqual({}, run_hook("lockfile", shell(Path(tmp), "npm install"))[1])
        with self.subTest(msg="malformed input fails open with a stderr note"):
            result = subprocess.run([sys.executable, str(HOOK), "lockfile", VERSION], input="[1,2", capture_output=True, text=True, env=ENV, check=False)
            self.assertEqual((0, ""), (result.returncode, result.stdout))
            self.assertIn("no decision", result.stderr)
        with self.subTest(msg="version mismatch exits 2"):
            self.assertEqual(2, run_hook("lockfile", {}, version="workflow-guard-v0")[0])

    def test_unpushed_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            remote = base / "remote.git"
            git(base, "init", "-q", "--bare", str(remote))
            root = base / "work"
            root.mkdir()
            git(root, "init", "-q", "-b", "main")
            (root / "README.md").write_text("x\n", encoding="utf-8")
            git(root, "add", "README.md")
            git(root, "commit", "-q", "-m", "init")
            stop = {"hook_event_name": "Stop", "stop_hook_active": False, "cwd": str(root)}
            state = root / "docs" / "ai" / "specs" / ".process" / "autopilot-state.json"
            state.parent.mkdir(parents=True)
            with self.subTest(msg="no autopilot state means no decision even with unpushed commits"):
                self.assertEqual({}, run_hook("unpushed", stop)[1])
            state.write_text(json.dumps({"status": "in_progress"}), encoding="utf-8")
            with self.subTest(msg="active state with no upstream blocks and names the commit count"):
                out = run_hook("unpushed", stop)[1]
                self.assertEqual("block", out["decision"])
                self.assertIn("1 commit", out["reason"])
            git(root, "remote", "add", "origin", str(remote))
            git(root, "push", "-q", "-u", "origin", "main")
            with self.subTest(msg="pushed branch passes"):
                self.assertEqual({}, run_hook("unpushed", stop)[1])
            (root / "a.txt").write_text("a\n", encoding="utf-8")
            git(root, "add", "a.txt")
            git(root, "commit", "-q", "-m", "more")
            with self.subTest(msg="a commit ahead of upstream blocks"):
                self.assertEqual("block", run_hook("unpushed", stop)[1]["decision"])
            with self.subTest(msg="stop_hook_active yields so a blocked turn cannot loop"):
                self.assertEqual({}, run_hook("unpushed", {**stop, "stop_hook_active": True})[1])
            state.write_text(json.dumps({"status": "completed_pr_open"}), encoding="utf-8")
            with self.subTest(msg="a finished state is not active"):
                self.assertEqual({}, run_hook("unpushed", stop)[1])
            state.write_text("{not json", encoding="utf-8")
            with self.subTest(msg="an unreadable state fails open"):
                self.assertEqual({}, run_hook("unpushed", stop)[1])


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(WorkflowGuardHookTests)


def main() -> int:
    return run_counted(build_suite(), label="test-workflow-guard-hook")


if __name__ == "__main__":
    raise SystemExit(main())
