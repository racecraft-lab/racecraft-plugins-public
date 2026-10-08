#!/usr/bin/env python3
"""Codex scaffold's git write probe: stop early on a read-only .git, record the fact, change nothing else."""

from __future__ import annotations

import errno
import json
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
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
from readiness_case import current_plugin_revision  # noqa: E402
from test_result import run_counted  # noqa: E402

REQUEST = {"schema_version": "1.0", "request_id": "test-git-write", "helper_id": "probe-git-write",
           "operation": "probe-git-write", "mode": "read_only", "inputs": {}}
SKILL = Path("speckit-scaffold-spec") / "SKILL.md"
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, env={**os.environ, **GIT_ENV})


class GitWriteProbeFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        git(self.root, "init", "-q")
        self.root.joinpath(".specify").mkdir()
        self.heads = self.root / ".git" / "refs" / "heads"
        self.addCleanup(os.chmod, self.heads, 0o755)

    def probe_current_repository(self) -> dict:
        with patch.object(probe, "git_common_directory", return_value=self.root / ".git"):
            return probe.run_git_write_probe_helper(None, SimpleNamespace(request_id="test-probe"))

    def assert_no_probe_files(self) -> None:
        self.assertEqual([], list((self.root / ".git").rglob(".speckit-git-write-probe-*.lock")))

    def directory_denial_result(self, directory: Path) -> dict:
        if os.name != "nt" and hasattr(os, "geteuid") and os.geteuid() != 0:
            mode = directory.stat().st_mode
            os.chmod(directory, 0o555)
            self.addCleanup(os.chmod, directory, mode)
            _, result, _ = run_runner(REQUEST, cwd=self.root)
            return result
        # Root bypasses POSIX modes; Windows directory modes cannot prove denial.
        open_file = os.open

        def deny_directory(path, flags: int, mode: int = 0o777, *, dir_fd=None) -> int:
            target = os.fstat(dir_fd) if dir_fd is not None else None
            denied = directory.stat()
            if flags & os.O_CREAT and target is not None and (target.st_dev, target.st_ino) == (denied.st_dev, denied.st_ino):
                raise PermissionError(errno.EACCES, "directory write denied")
            return open_file(path, flags, mode, dir_fd=dir_fd)

        with patch.object(probe.os, "open", side_effect=deny_directory):
            return self.probe_current_repository()



class GitWriteProbeDescriptorTest(unittest.TestCase):
    def assert_helper_descriptor_cleanup(self, common: Path, scenario: str) -> None:
        open_file, close, rename = os.open, os.close, os.rename
        live: set[int] = set()
        opened: list[str] = []
        injected: list[str] = []

        def track_open(path, flags, mode=0o777, *, dir_fd=None):
            name = str(path)
            capture = name.endswith(".lock.cleanup")
            target = {"component_open": name == "heads",
                      "cleanup_open": name == probe.PROBE_CLEANUP_DIRECTORY,
                      "capture_open": capture}.get(scenario, False)
            if target:
                injected.append(scenario)
                raise PermissionError(errno.EACCES, "injected open denial")
            fd = open_file(path, flags, mode, dir_fd=dir_fd)
            live.add(fd)
            opened.append(name)
            shared_parent = scenario == "created_cleanup_validation" and name == probe.PROBE_CLEANUP_DIRECTORY
            shared_capture = scenario == "capture_validation" and capture
            if shared_parent or shared_capture:
                injected.append(scenario)
                os.fchmod(fd, 0o755)
            return fd

        def track_close(fd):
            close(fd)
            live.remove(fd)

        def fail_rename(*args, **kwargs):
            if scenario == "capture_rename":
                injected.append(scenario)
                raise PermissionError(errno.EACCES, "injected capture denial")
            return rename(*args, **kwargs)

        try:
            with patch.object(probe, "git_common_directory", return_value=common):
                with patch.object(probe.os, "open", side_effect=track_open), \
                     patch.object(probe.os, "close", side_effect=track_close), \
                     patch.object(probe.os, "rename", side_effect=fail_rename):
                    result = probe.run_git_write_probe_helper(None, SimpleNamespace(request_id="test-probe"))
            self.assertTrue(opened, "descriptor tracking did not reach the probe")
            self.assertEqual(set(), live, "helper leaked descriptors")
            expected = "verified" if scenario == "success" else "unavailable"
            self.assertEqual(expected, result["data"]["observation"]["status"])
            if scenario not in {"success", "existing_cleanup_validation"}:
                self.assertTrue(injected, "fault did not reach the intended storage boundary")
        finally:
            for fd in live:
                close(fd)

    def test_helper_closes_descriptors_on_success_and_storage_failures(self) -> None:
        scenarios = ("success", "component_open", "cleanup_open", "created_cleanup_validation",
                     "existing_cleanup_validation", "capture_open", "capture_validation", "capture_rename")
        for scenario in scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                common = Path(temporary)
                common.joinpath("refs", "heads").mkdir(parents=True)
                if scenario == "existing_cleanup_validation":
                    existing = common / probe.PROBE_CLEANUP_DIRECTORY
                    existing.mkdir(mode=0o755)
                    existing.chmod(0o755)
                self.assert_helper_descriptor_cleanup(common, scenario)


class GitWriteProbeTest(GitWriteProbeFixture):
    def test_root_runs_execute_both_directory_denial_cases_without_skips(self) -> None:
        with patch.object(os, "geteuid", return_value=0, create=True):
            module = runpy.run_path(str(Path(__file__)), run_name="root_probe_tests")
            result = unittest.TestResult()
            for name in ("test_read_only_git_directory_stops_with_cause_and_both_fixes",
                         "test_existing_read_only_worktree_metadata_stops_before_gates"):
                module["GitWriteProbeTest"](name).run(result)
        self.assertEqual([], result.skipped)
        self.assertTrue(result.wasSuccessful(), result.errors or result.failures)
        self.assertEqual(2, result.testsRun)

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

        def fail_once(path: str, *, dir_fd=None) -> None:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise PermissionError(errno.EPERM, "denied")
            unlink(path, dir_fd=dir_fd)

        with patch.object(probe.os, "unlink", side_effect=fail_once):
            result = self.probe_current_repository()
        self.assertEqual("verified", result["data"]["observation"]["status"])
        self.assert_no_probe_files()

    def test_close_failure_still_removes_created_probe_in_finally(self) -> None:
        close = os.close

        def fail_close(fd: int) -> None:
            close(fd)
            raise OSError(errno.EIO, "close failed")

        with patch.object(probe.os, "close", side_effect=fail_close):
            result = self.probe_current_repository()
        self.assertEqual("unknown", result["data"]["observation"]["status"])
        self.assert_no_probe_files()

    def test_recycled_pid_leftover_is_preserved_and_does_not_mask_probe(self) -> None:
        stale = self.heads / f".speckit-git-write-probe-{os.getpid()}.lock"
        stale.write_text("existing file", encoding="utf-8")
        result = self.probe_current_repository()
        self.assertEqual("verified", result["data"]["observation"]["status"])
        self.assertEqual("existing file", stale.read_text(encoding="utf-8"))
        self.assertEqual([stale], list((self.root / ".git").rglob(".speckit-git-write-probe-*.lock")))

    def test_collision_retries_fresh_random_name_and_observes_permission_denial(self) -> None:
        open_file = os.open
        names = []

        def fail_creation(path, flags, mode=0o777, *, dir_fd=None):
            if not flags & os.O_CREAT:
                return open_file(path, flags, mode, dir_fd=dir_fd)
            names.append(Path(path).name)
            if len(names) == 1:
                raise FileExistsError(errno.EEXIST, "collision")
            raise PermissionError(errno.EROFS, "read-only")

        with patch.object(probe.os, "open", side_effect=fail_creation):
            result = self.probe_current_repository()
        self.assertEqual("stop", result["data"]["verdict"])
        self.assertGreaterEqual(len(names), 2)
        self.assertNotEqual(names[0], names[1])

    def test_unknown_first_directory_does_not_skip_later_permission_denial(self) -> None:
        open_file = os.open

        def fail_open(path, flags: int, mode: int = 0o777, *, dir_fd=None) -> int:
            if not flags & os.O_CREAT:
                return open_file(path, flags, mode, dir_fd=dir_fd)
            target = os.fstat(dir_fd)
            heads = self.heads.stat()
            number = errno.ENOSPC if (target.st_dev, target.st_ino) == (heads.st_dev, heads.st_ino) else errno.EACCES
            raise OSError(number, "storage problem")

        with patch.object(probe.os, "open", side_effect=fail_open):
            result = self.probe_current_repository()
        self.assertEqual("stop", result["data"]["verdict"])
        self.assertEqual("unavailable", result["data"]["observation"]["status"])

    def test_existing_read_only_worktree_metadata_stops_before_gates(self) -> None:
        metadata = self.root / ".git" / "worktrees"
        metadata.mkdir()
        result = self.directory_denial_result(metadata)
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
                       "host": "codex", "execution_mode": "answers-file", "plugin_revision": current_plugin_revision(),
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

    def test_read_only_git_directory_stops_with_cause_and_both_fixes(self) -> None:
        response = self.directory_denial_result(self.heads)
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
        body = {"host": "claude", "execution_mode": "interactive", "plugin_revision": current_plugin_revision(), "observations": [item]}
        request = {"schema_version": "1.0", "request_id": "test-readiness", "helper_id": "write-readiness-record",
                   "operation": "write-readiness-record", "mode": "dry_run", "inputs": body}
        completed, response, _ = run_runner(request, cwd=self.root)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("not_applicable", response["data"]["record"]["items"]["git_write"]["status"])



class GitWriteProbeContainmentTest(GitWriteProbeFixture):
    def test_cleanup_rejects_a_private_directory_owned_by_another_user(self) -> None:
        fstat = os.fstat

        def foreign_owner(fd):
            metadata = fstat(fd)
            if metadata.st_mode & 0o777 == 0o700:
                fields = list(metadata)
                fields[4] = os.geteuid() + 1
                return os.stat_result(fields)
            return metadata

        with patch.object(probe.os, "fstat", side_effect=foreign_owner):
            result = self.probe_current_repository()
        self.assertEqual("stop", result["data"]["verdict"])
        self.assertTrue(list(self.heads.glob("*.lock")), "probe moved into a foreign directory")
        self.assertTrue(list((self.root / ".git").glob("*.cleanup")), "foreign directory was removed")

    def test_cleanup_rejects_a_substituted_shared_directory_before_capture(self) -> None:
        open_file = os.open
        replacement = None

        def substitute_cleanup(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal replacement
            if str(path).endswith(".cleanup") and replacement is None:
                private = self.root / ".git" / path
                private.rename(self.root / ".git" / "held-cleanup")
                private.mkdir(mode=0o755)
                private.chmod(0o755)
                replacement = private / str(path).removesuffix(".cleanup")
                replacement.write_text("foreign file", encoding="utf-8")
            return open_file(path, flags, mode, dir_fd=dir_fd)

        with patch.object(probe.os, "open", side_effect=substitute_cleanup):
            result = self.probe_current_repository()
        self.assertIsNotNone(replacement)
        self.assertTrue(replacement.exists(), "capture overwrote a foreign file")
        self.assertEqual("foreign file", replacement.read_text(encoding="utf-8"))
        self.assertEqual("stop", result["data"]["verdict"])

    def test_symlinked_git_subdirectory_never_receives_probe_files(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        self.heads.rmdir()
        self.heads.symlink_to(outside, target_is_directory=True)
        self.addCleanup(self.heads.mkdir)
        self.addCleanup(self.heads.unlink)
        opened_outside = []
        open_file = os.open

        def observe_open(path, flags, mode=0o777, *, dir_fd=None):
            fd = open_file(path, flags, mode, dir_fd=dir_fd)
            if flags & os.O_CREAT and (outside / Path(path).name).exists():
                opened_outside.append(Path(path).name)
            return fd

        with patch.object(probe.os, "open", side_effect=observe_open):
            result = self.probe_current_repository()
        self.assertEqual([], opened_outside, "probe created a file outside .git")
        self.assertEqual("stop", result["data"]["verdict"])
        self.assertEqual([], list(outside.iterdir()))

    @contextmanager
    def replacement_on_creation(self):
        open_file = os.open
        replacement = None

        def replace_created_lock(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal replacement
            fd = open_file(path, flags, mode, dir_fd=dir_fd)
            if flags & os.O_CREAT and replacement is None:
                original = self.heads / Path(path).name
                original.rename(self.heads / "held-original")
                original.write_text("replacement belongs to someone else", encoding="utf-8")
                replacement = original
            return fd

        with patch.object(probe.os, "open", side_effect=replace_created_lock):
            yield lambda: replacement

    def test_cleanup_preserves_a_replacement_file(self) -> None:
        with self.replacement_on_creation() as replaced:
            result = self.probe_current_repository()
        replacement = replaced()
        self.assertIsNotNone(replacement)
        self.assertTrue(replacement.exists(), "cleanup deleted a replacement file")
        self.assertEqual("replacement belongs to someone else", replacement.read_text(encoding="utf-8"))
        self.assertEqual("unknown", result["data"]["observation"]["status"])

    def test_probe_removed_before_capture_leaves_no_leftover_report(self) -> None:
        rename = os.rename

        def remove_then_rename(src, dst, **kwargs):
            if str(src).endswith(".lock") and kwargs.get("src_dir_fd") is not None:
                os.unlink(src, dir_fd=kwargs["src_dir_fd"])
            return rename(src, dst, **kwargs)

        with patch.object(probe.os, "rename", side_effect=remove_then_rename):
            result = self.probe_current_repository()
        self.assertEqual("proceed", result["data"]["verdict"])
        self.assertNotIn("could not be removed", result["data"]["message"])
        self.assert_no_probe_files()

    def test_unrestored_replacement_is_preserved_for_inspection(self) -> None:
        with self.replacement_on_creation():
            with patch.object(probe.os, "link", side_effect=PermissionError(errno.EPERM, "restore denied")):
                result = self.probe_current_repository()
        self.assertEqual("stop", result["data"]["verdict"])
        captured = list((self.root / ".git").rglob("*.cleanup/*.lock"))
        self.assertEqual(1, len(captured))
        self.assertEqual("replacement belongs to someone else", captured[0].read_text(encoding="utf-8"))
        action = result["data"]["observation"]["action"]
        self.assertIn("restore any replacement files", action)
        self.assertNotIn("Remove the named leftover probe files", action)

    def test_cleanup_preserves_replacement_inserted_after_identity_check(self) -> None:
        stat_file = os.stat
        replacement = None

        def replace_after_stat(path, *args, **kwargs):
            nonlocal replacement
            metadata = stat_file(path, *args, **kwargs)
            name = Path(path).name
            if kwargs.get("dir_fd") is not None and name.endswith(".lock") and replacement is None:
                public = self.heads / name
                replacement = public
                if public.exists():
                    public.rename(self.heads / "held-original")
                public.write_text("replacement after stat", encoding="utf-8")
            return metadata

        with patch.object(probe.os, "stat", side_effect=replace_after_stat):
            self.probe_current_repository()
        self.assertIsNotNone(replacement)
        self.assertTrue(replacement.exists(), "cleanup raced and deleted the replacement")
        self.assertEqual("replacement after stat", replacement.read_text(encoding="utf-8"))

    def test_close_failure_does_not_mask_cleanup_permission_denial(self) -> None:
        close = os.close

        def fail_close(fd: int) -> None:
            close(fd)
            raise OSError(errno.EIO, "close failed")

        with patch.object(probe.os, "unlink", side_effect=PermissionError(errno.EACCES, "denied")):
            with patch.object(probe.os, "close", side_effect=fail_close):
                result = self.probe_current_repository()
        self.assertEqual("stop", result["data"]["verdict"])
        self.assertEqual("unavailable", result["data"]["observation"]["status"])


class GitWriteProbeDirectoryReplacementTest(GitWriteProbeFixture):
    def directory_replacement_result(self, deny_open: bool) -> dict:
        open_file, close = os.open, os.close
        common = self.root / ".git"
        parent_metadata = common.stat()
        private_fd = None
        replacement = None

        def replace_directory(path):
            nonlocal replacement
            replacement = common / path
            replacement.rename(common / "held-cleanup")
            replacement.mkdir(mode=0o700)

        def observe_open(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal private_fd
            parent = os.fstat(dir_fd) if dir_fd is not None else None
            if (str(path).endswith(".cleanup") and parent is not None
                    and (parent.st_dev, parent.st_ino) == (parent_metadata.st_dev, parent_metadata.st_ino)):
                if deny_open and (common / path).exists():
                    if replacement is None:
                        replace_directory(path)
                    raise PermissionError(errno.EACCES, "cleanup open denied")
                private_fd = open_file(path, flags, mode, dir_fd=dir_fd)
                return private_fd
            return open_file(path, flags, mode, dir_fd=dir_fd)

        def replace_before_close(fd):
            if fd == private_fd and replacement is None:
                replace_directory(next(common.glob("*.cleanup")).name)
            close(fd)

        with patch.object(probe.os, "open", side_effect=observe_open):
            with patch.object(probe.os, "close", side_effect=replace_before_close):
                result = self.probe_current_repository()
        self.assertIsNotNone(replacement, "public directory substitution was not exercised")
        self.assertTrue((common / "held-cleanup").exists(), "original directory was not moved")
        self.assertTrue(replacement.exists(), "cleanup removed a foreign replacement directory")
        return result

    def test_cleanup_preserves_public_directory_replacement_when_open_is_denied(self) -> None:
        self.assertEqual("stop", self.directory_replacement_result(True)["data"]["verdict"])

    def test_cleanup_preserves_public_directory_replacement_after_close(self) -> None:
        self.assertEqual("proceed", self.directory_replacement_result(False)["data"]["verdict"])


def build_suite() -> unittest.TestSuite:
    return unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                              for case in (GitWriteProbeTest, GitWriteProbeContainmentTest, GitWriteProbeDirectoryReplacementTest,
                                           GitWriteProbeDescriptorTest))


def main() -> int:
    return run_counted(build_suite(), label="test-git-write-probe")


if __name__ == "__main__":
    raise SystemExit(main())
