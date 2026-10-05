#!/usr/bin/env python3
"""Codex scaffold's git write probe: stop early on a read-only .git, record the fact, change nothing else."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))

from host_skill_views import host_skill_root  # noqa: E402
from runner_invocation import assert_runner_response, run_runner  # noqa: E402
from test_result import run_counted  # noqa: E402

REQUEST = {"schema_version": "1.0", "request_id": "test-git-write", "helper_id": "probe-git-write",
           "operation": "probe-git-write", "mode": "read_only", "inputs": {}}
SKILL = Path("speckit-scaffold-spec") / "SKILL.md"
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, env={**os.environ, **GIT_ENV})


class GitWriteProbeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        git(self.root, "init", "-q")
        self.root.joinpath(".specify").mkdir()
        self.heads = self.root / ".git" / "refs" / "heads"
        self.addCleanup(os.chmod, self.heads, 0o755)

    def test_writable_git_directory_proceeds_and_leaves_no_lock_file(self) -> None:
        _, response, _ = run_runner(REQUEST, cwd=self.root)
        assert_runner_response(self, response, "ok", 0)
        self.assertEqual("proceed", response["data"]["verdict"])
        self.assertEqual("verified", response["data"]["observation"]["status"])
        self.assertEqual("git_write", response["data"]["observation"]["item"])
        self.assertEqual([], sorted(self.heads.iterdir()))

    @unittest.skipIf(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                     "needs POSIX modes and a non-root user")
    def test_read_only_git_directory_stops_with_cause_and_both_fixes(self) -> None:
        os.chmod(self.heads, 0o555)
        _, response, _ = run_runner(REQUEST, cwd=self.root)
        assert_runner_response(self, response, "expected_failure", 1)
        data = response["data"]
        self.assertEqual("stop", data["verdict"])
        self.assertIn(".git", data["message"])
        self.assertIn("approve git writes", data["message"])
        self.assertIn("sandbox_workspace_write.writable_roots", data["message"])
        self.assertNotIn(str(self.root), data["message"])
        observation = data["observation"]
        self.assertEqual(("git_write", "unavailable"), (observation["item"], observation["status"]))
        self.assertTrue(observation["action"])

    def test_codex_scaffold_probes_before_any_gate_and_claude_does_not(self) -> None:
        codex = (host_skill_root("codex") / SKILL).read_text(encoding="utf-8")
        probe_at = codex.index("## Git Write Probe")
        for later in ("## Answers-file mode", "### -0.5 ", "### 2. Find the Spec"):
            self.assertLess(probe_at, codex.index(later))
        section = codex.split("## Git Write Probe", 1)[1].split("\n## ", 1)[0]
        self.assertIn("`probe-git-write`", section)
        self.assertIn("before any gate or branch step", section)
        self.assertNotIn("Git Write Probe", (host_skill_root("claude") / SKILL).read_text(encoding="utf-8"))

    def test_readiness_record_accepts_git_write_and_scaffold_sends_it_on_each_host(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                step = (host_skill_root(host) / SKILL).read_text(encoding="utf-8").split("### 6.5 Write the Readiness Record", 1)[1].split("\n### ", 1)[0]
                self.assertIn("`git_write`", step)
        item = {"item": "git_write", "status": "not_applicable", "evidence_source": "Claude Code has no git sandbox probe"}
        body = {"host": "claude", "execution_mode": "interactive", "plugin_revision": "2.40.0", "observations": [item]}
        request = {"schema_version": "1.0", "request_id": "test-readiness", "helper_id": "write-readiness-record",
                   "operation": "write-readiness-record", "mode": "dry_run", "inputs": body}
        completed, response, _ = run_runner(request, cwd=self.root)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("not_applicable", response["data"]["record"]["items"]["git_write"]["status"])


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(GitWriteProbeTest)


def main() -> int:
    return run_counted(build_suite(), label="test-git-write-probe")


if __name__ == "__main__":
    raise SystemExit(main())
