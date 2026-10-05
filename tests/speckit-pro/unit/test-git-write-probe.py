#!/usr/bin/env python3
"""Codex scaffold's git write probe: stop early on a read-only .git, record the fact, change nothing else."""

from __future__ import annotations

import errno
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))

from speckit_pro_runner.helpers.git_write_probe import probe_result  # noqa: E402
from speckit_pro_runner.helpers import git_write_probe as probe  # noqa: E402
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

    def probe_current_repository(self) -> dict:
        with patch.object(probe, "git_common_directory", return_value=self.root / ".git"):
            return probe.run_git_write_probe_helper(None, SimpleNamespace(request_id="test-probe"))

    def test_cleanup_failure_names_leftovers_without_local_paths(self) -> None:
        with patch.object(probe.os, "unlink", side_effect=PermissionError(errno.EPERM, "denied")):
            result = self.probe_current_repository()
        self.assertEqual("stop", result["data"]["verdict"])
        message = result["data"]["message"]
        self.assertIn("could not be removed", message)
        leftovers = list((self.root / ".git").rglob(".speckit-git-write-probe-*.lock"))
        self.assertTrue(leftovers)
        for leftover in leftovers:
            self.assertIn(leftover.name, message)
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_transient_unlink_failure_is_retried_and_leaves_no_probe(self) -> None:
        unlink = os.unlink
        calls = 0

        def fail_once(path: str) -> None:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise PermissionError(errno.EPERM, "denied")
            unlink(path)

        with patch.object(probe.os, "unlink", side_effect=fail_once):
            result = self.probe_current_repository()
        self.assertEqual("verified", result["data"]["observation"]["status"])
        self.assertEqual([], list((self.root / ".git").rglob(".speckit-git-write-probe-*.lock")))

    def test_close_failure_still_removes_created_probe_in_finally(self) -> None:
        close = os.close

        def fail_close(fd: int) -> None:
            close(fd)
            raise OSError(errno.EIO, "close failed")

        with patch.object(probe.os, "close", side_effect=fail_close):
            result = self.probe_current_repository()
        self.assertEqual("unknown", result["data"]["observation"]["status"])
        self.assertEqual([], list((self.root / ".git").rglob(".speckit-git-write-probe-*.lock")))

    def test_recycled_pid_leftover_is_preserved_and_does_not_mask_probe(self) -> None:
        stale = self.heads / f".speckit-git-write-probe-{os.getpid()}.lock"
        stale.write_text("existing file", encoding="utf-8")
        result = self.probe_current_repository()
        self.assertEqual("verified", result["data"]["observation"]["status"])
        self.assertEqual("existing file", stale.read_text(encoding="utf-8"))
        self.assertEqual([stale], list((self.root / ".git").rglob(".speckit-git-write-probe-*.lock")))

    def test_collision_retries_fresh_random_name_and_observes_permission_denial(self) -> None:
        with patch.object(probe.os, "open", side_effect=[
            FileExistsError(errno.EEXIST, "collision"),
            PermissionError(errno.EROFS, "read-only"),
            PermissionError(errno.EPERM, "denied"),
        ]) as opened:
            result = self.probe_current_repository()
        self.assertEqual("stop", result["data"]["verdict"])
        names = [Path(call.args[0]).name for call in opened.call_args_list]
        self.assertGreaterEqual(len(names), 2)
        self.assertNotEqual(names[0], names[1])

    def test_unknown_first_directory_does_not_skip_later_permission_denial(self) -> None:
        def fail_open(path: str, flags: int, mode: int) -> int:
            number = errno.ENOSPC if Path(path).parent == self.heads else errno.EACCES
            raise OSError(number, "storage problem")

        with patch.object(probe.os, "open", side_effect=fail_open):
            result = self.probe_current_repository()
        self.assertEqual("stop", result["data"]["verdict"])
        self.assertEqual("unavailable", result["data"]["observation"]["status"])

    @unittest.skipIf(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                     "needs POSIX modes and a non-root user")
    def test_existing_read_only_worktree_metadata_stops_before_gates(self) -> None:
        metadata = self.root / ".git" / "worktrees"
        metadata.mkdir(mode=0o555)
        self.addCleanup(os.chmod, metadata, 0o755)
        _, result, _ = run_runner(REQUEST, cwd=self.root)
        self.assertEqual("stop", result["data"]["verdict"])

    def test_denied_codex_probe_is_recorded_before_the_stop_message(self) -> None:
        codex = (host_skill_root("codex") / SKILL).read_text(encoding="utf-8")
        section = codex.split("## Git Write Probe", 1)[1].split("\n## ", 1)[0]
        self.assertLess(section.index("`write-readiness-record`"), section.index("end scaffold"))
        self.assertIn('`apply`', section)
        with patch.object(probe.os, "open", side_effect=PermissionError(errno.EPERM, "denied")):
            observation = self.probe_current_repository()["data"]["observation"]
        request = {"schema_version": "1.0", "request_id": "denied-readiness", "helper_id": "write-readiness-record",
                   "operation": "write-readiness-record", "mode": "apply", "inputs": {
                       "host": "codex", "execution_mode": "answers-file", "plugin_revision": "2.40.0",
                       "observations": [observation]}}
        _, result, _ = run_runner(request, cwd=self.root)
        assert_runner_response(self, result, "ok", 0)
        record = json.loads((self.root / ".specify" / "readiness" / "codex.json").read_text(encoding="utf-8"))
        self.assertEqual("unavailable", record["items"]["git_write"]["status"])
        self.assertEqual([], list(self.heads.iterdir()))
        self.assertFalse((self.root / ".worktrees").exists())

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

    def test_stub_refs_directory_from_reftable_repositories_still_proceeds(self) -> None:
        self.heads.rmdir()
        self.heads.write_text("stub\n", encoding="utf-8")
        self.addCleanup(self.heads.mkdir)
        self.addCleanup(self.heads.unlink)
        _, response, _ = run_runner(REQUEST, cwd=self.root)
        assert_runner_response(self, response, "ok", 0)
        self.assertEqual("verified", response["data"]["observation"]["status"])

    def test_non_permission_failures_proceed_as_unknown_without_the_sandbox_advice(self) -> None:
        for number in (errno.ENOSPC, errno.EIO):
            with self.subTest(errno=number):
                verdict, message, item = probe_result(OSError(number, "boom"), True)
                self.assertEqual(("proceed", ""), (verdict, message))
                self.assertEqual("unknown", item["status"])
                self.assertTrue(item["action"])
        self.assertEqual("proceed", probe_result(None, False)[0])
        self.assertEqual("stop", probe_result(PermissionError(errno.EACCES, "no"), True)[0])

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
