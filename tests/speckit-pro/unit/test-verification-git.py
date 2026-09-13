#!/usr/bin/env python3
"""Real repository checks for explicitly scoped, non-reusable Git snapshots."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "speckit-pro"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted
from speckit_pro_runner import verification_git as git_snapshot
from speckit_pro_runner import verification_docker_workflow as docker_workflow
from speckit_pro_runner.execution_control import execution_control


@unittest.skipUnless(hasattr(os, "O_NOFOLLOW") and os.open in os.supports_dir_fd, "POSIX no-follow Git capture")
class GitSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / "repository"
        self.root.mkdir()
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                         "HOME": str(self.base), "XDG_CONFIG_HOME": str(self.base)})
        self.git("init", "--quiet")
        self.git("config", "user.name", "Snapshot Fixture")
        self.git("config", "user.email", "git@github.com")
        (self.root / "tracked.txt").write_text("committed\n")
        self.git("add", "tracked.txt")
        self.git("commit", "--quiet", "-m", "fixture")
        self.common = self.root / ".git"
        self.settings = {"common_directory": str(self.common), "worktree_directory": str(self.common)}
        (self.root / "workflow.md").write_text('## PROJECT_COMMANDS\n```json\n{"UNIT_TEST":"python3 check.py"}\n```\n')
        self.inputs = {"workflow_file": "workflow.md", "command_id": "UNIT_TEST", "git_snapshot": self.settings,
                       "docker": {"executable": "/usr/local/bin/docker", "endpoint": "unix:///tmp/docker.sock",
                                  "base_image": "python@sha256:" + "a" * 64, "output_contract": "streams_only"}}

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, env=self.env, stderr=subprocess.PIPE)

    def test_plain_repository_preserves_real_index_objects_and_configuration(self):
        files, binding = git_snapshot.capture_git_metadata(self.root, self.settings)
        self.assertEqual(files[".git/index"][1], (self.common / "index").read_bytes())
        self.assertEqual(files[".git/config"][1], (self.common / "config").read_bytes())
        self.assertTrue(any(name.startswith(".git/objects/") and body for name, (_, body) in files.items()))
        self.assertEqual(binding["profile"], "git-readonly-metadata/v1")
        self.assertFalse(binding["qualified"])
        self.assertTrue(binding["limitations"])

    def test_linked_worktree_uses_private_index_and_common_refs(self):
        linked = self.base / "linked"
        self.git("worktree", "add", "--quiet", "--detach", str(linked), "HEAD")
        private = Path((linked / ".git").read_text().strip().removeprefix("gitdir: "))
        settings = {"common_directory": str(self.common), "worktree_directory": str(private)}
        files, binding = git_snapshot.capture_git_metadata(linked, settings)
        self.assertEqual(files[".git/index"][1], (private / "index").read_bytes())
        self.assertEqual(files[".git/HEAD"][1], (private / "HEAD").read_bytes())
        self.assertNotIn(".git/commondir", files)
        self.assertEqual(binding["layout"], "linked")
        self.assertEqual(binding["control_files"]["gitfile"], git_snapshot.sha((linked / ".git").read_bytes()))

    def test_new_refs_and_index_changes_change_the_binding(self):
        _, before = git_snapshot.capture_git_metadata(self.root, self.settings)
        self.git("branch", "new-branch")
        _, with_ref = git_snapshot.capture_git_metadata(self.root, self.settings)
        self.assertNotEqual(before, with_ref)
        (self.root / "tracked.txt").write_text("staged change\n")
        self.git("add", "tracked.txt")
        _, staged = git_snapshot.capture_git_metadata(self.root, self.settings)
        self.assertNotEqual(with_ref, staged)

    def test_explicit_scope_must_match_actual_repository_layout(self):
        with self.assertRaises(ValueError):
            git_snapshot.capture_git_metadata(self.root, {**self.settings, "worktree_directory": str(self.base)})
        for settings in ({}, {**self.settings, "extra": "value"},
                         {**self.settings, "common_directory": ".git"}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                git_snapshot.capture_git_metadata(self.root, settings)

    def test_unsupported_object_dependencies_are_rejected(self):
        for name in ("objects/info/alternates", "objects/info/http-alternates", "shallow"):
            with self.subTest(name=name):
                path = self.common / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("external dependency\n")
                try:
                    with self.assertRaisesRegex(ValueError, "unsupported Git"):
                        git_snapshot.capture_git_metadata(self.root, self.settings)
                finally:
                    path.unlink()

    def test_credential_and_include_configuration_is_rejected(self):
        for key, value in (("credential.helper", "secret-helper"), ("include.path", "external"),
                           ("http.extraHeader", "Authorization: synthetic"),
                           ("core.excludesFile", "external"),
                           ("remote.origin.url", "https://user:git@github.com/repo")):
            with self.subTest(key=key):
                self.git("config", key, value)
                try:
                    with self.assertRaisesRegex(ValueError, "unsupported Git configuration"):
                        git_snapshot.capture_git_metadata(self.root, self.settings)
                finally:
                    self.git("config", "--unset", key)

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires no-follow file access")
    def test_metadata_symlinks_cannot_read_an_external_file(self):
        secret = self.base / "outside"
        secret.write_text("must not be captured")
        (self.common / "info" / "escape").symlink_to(secret)
        with self.assertRaises((OSError, ValueError)):
            git_snapshot.capture_git_metadata(self.root, self.settings)

    def test_ambiguous_configuration_cannot_bypass_admission(self):
        for body in (b'[DEFAULT]\npassword = synthetic\n',
                     b'[remote.origin]\nurl = https://user:git@github.com/repo\n',
                     b'[remote "origin"]\nurl = user:git@github.com:repo\n'):
            with self.subTest(body=body), self.assertRaisesRegex(ValueError, "unsupported Git configuration"):
                git_snapshot.check_git_configuration(body)

    def test_linked_worktree_private_refs_and_split_indexes_are_refused(self):
        linked = self.base / "linked"
        self.git("worktree", "add", "--quiet", "--detach", str(linked), "HEAD")
        private = Path((linked / ".git").read_text().strip().removeprefix("gitdir: "))
        settings = {"common_directory": str(self.common), "worktree_directory": str(private)}
        (private / "sharedindex.synthetic").write_bytes(b"synthetic")
        with self.assertRaisesRegex(ValueError, "split index"):
            git_snapshot.capture_git_metadata(linked, settings)
        (private / "sharedindex.synthetic").unlink()
        (private / "refs" / "worktree").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "per-worktree references"):
            git_snapshot.capture_git_metadata(linked, settings)

    def test_git_root_mode_is_preserved_and_bound(self):
        self.common.chmod(0o700)
        files, binding = git_snapshot.capture_git_metadata(self.root, self.settings)
        self.assertEqual(files[".git"], (0o700, None))
        self.assertEqual(binding["directory_modes"]["common"], 0o700)

    def test_replaced_parent_cannot_be_followed_by_file_reader(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "data").write_bytes(b"must not be read")
        (self.base / "linked-parent").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(OSError):
            git_snapshot.read_git_file(self.base / "linked-parent" / "data", 100)

    def test_input_limits_fail_before_unbounded_reads(self):
        with patch.object(git_snapshot, "MAX_BYTES", 4), self.assertRaises(ValueError):
            git_snapshot.capture_git_metadata(self.root, self.settings)
        with patch.object(git_snapshot, "MAX_FILES", 2), self.assertRaises(ValueError):
            git_snapshot.capture_git_metadata(self.root, self.settings)

    def test_workflow_capture_merges_git_inputs_and_detects_changed_state(self):
        from speckit_pro_runner.verification_docker_workflow import docker_input_snapshot
        files, binding = docker_input_snapshot(self.root, "workflow.md", self.settings)
        self.assertIn("tracked.txt", files)
        self.assertIn(".git/index", files)
        self.git("branch", "after-capture")
        changed_files, changed_binding = docker_input_snapshot(self.root, "workflow.md", self.settings)
        self.assertNotEqual(files, changed_files)
        self.assertNotEqual(binding, changed_binding)

    def test_combined_snapshot_bounds_include_project_and_git(self):
        files, _ = docker_workflow.docker_input_snapshot(self.root, "workflow.md", self.settings)
        total = sum(len(body) for _, body in files.values() if body is not None)
        with patch.object(docker_workflow, "MAX_BYTES", total - 1), self.assertRaisesRegex(ValueError, "combined"):
            docker_workflow.docker_input_snapshot(self.root, "workflow.md", self.settings)
        with patch.object(docker_workflow, "MAX_FILES", len(files) - 1), self.assertRaisesRegex(ValueError, "combined"):
            docker_workflow.docker_input_snapshot(self.root, "workflow.md", self.settings)

    def test_dry_run_discloses_unqualified_git_profile_without_daemon(self):
        with patch.object(docker_workflow, "DockerClient") as client:
            result = docker_workflow.execute_docker_verification(self.root, self.inputs, "dry_run")
        client.assert_not_called()
        self.assertEqual(result["git_snapshot"]["directories"], self.settings)
        self.assertFalse(result["git_snapshot"]["qualified"] or result["reusable"] or result["writes_state"])
        without_git = {key: value for key, value in self.inputs.items() if key != "git_snapshot"}
        ordinary = docker_workflow.execute_docker_verification(self.root, without_git, "dry_run")
        self.assertIsNone(ordinary["git_snapshot"])
        self.assertNotEqual(result["snapshot_sha256"], ordinary["snapshot_sha256"])

    def test_invalid_git_scope_refuses_before_reservation_and_daemon(self):
        with patch.object(docker_workflow, "DockerClient") as client, \
             patch.object(docker_workflow, "execution_control") as reserve, self.assertRaises(ValueError):
            docker_workflow.execute_docker_verification(self.root, {**self.inputs, "git_snapshot": {}}, "apply")
        client.assert_not_called()
        reserve.assert_not_called()

    def test_execution_binds_git_evidence_and_rejects_a_midrun_ref_change(self):
        ledger_inputs = {"workflow_file": "workflow.md", "action": "start"}
        started = execution_control(self.root, ledger_inputs, "apply")
        run_id = started["ledger"]["run_id"]
        execution_control(self.root, {**ledger_inputs, "action": "reserve", "dispatch_id": "git-check",
                                     "kind": "verification", "expected_run_id": run_id}, "apply")

        def image_run(*args):
            self.assertIn(".git/index", args[1])
            self.git("branch", "changed-during-execution")
            return {"completed": True, "exit_code": 0, "stdout": b"ok", "stderr": b""}

        with patch.object(docker_workflow, "DockerClient") as client, \
             patch.object(docker_workflow, "execute_image", side_effect=image_run) as launch:
            client.return_value.events = []
            result = docker_workflow.execute_docker_verification(
                self.root, {**self.inputs, "dispatch_id": "git-check", "expected_run_id": run_id}, "apply")
        launch.assert_called_once()
        self.assertTrue(result["record"]["completed"])
        self.assertFalse(result["record"]["inputs_unchanged"] or result["reusable"])
        body = (self.root / result["evidence_path"]).read_bytes()
        evidence = json.loads(body)
        self.assertEqual(result["record"]["evidence_sha256"], git_snapshot.sha(body))
        self.assertEqual(evidence["git_snapshot"]["profile"], "git-readonly-metadata/v1")
        self.assertIn("git_metadata_profile_not_independently_qualified", result["limitations"])


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(GitSnapshotTests),
                                label="test-verification-git"))
