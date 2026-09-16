#!/usr/bin/env python3
"""Real repository checks for explicitly scoped, non-reusable Git snapshots."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "speckit-pro"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted
from speckit_pro_runner import verification_git as git_snapshot
from speckit_pro_runner import verification_docker_workflow as docker_workflow
from speckit_pro_runner.execution_control import execution_control
from speckit_pro_runner import verification_records
from speckit_pro_runner.verification_records import validate_execution_record


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

    def test_bounded_record_reader_never_requests_more_than_limit_plus_one(self):
        requested = []

        class Stream:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def fileno(self):
                return 17
            def read(self, size):
                requested.append(size)
                return b"x" * size

        info = SimpleNamespace(st_dev=1, st_ino=2, st_mode=stat.S_IFREG | 0o600, st_size=4,
                               st_mtime_ns=3, st_ctime_ns=4)
        with patch.object(verification_records.os, "open", return_value=17), \
             patch.object(verification_records.os, "fdopen", return_value=Stream()), \
             patch.object(verification_records.os, "fstat", return_value=info), \
             self.assertRaisesRegex(ValueError, "changed while being read"):
            verification_records._read_bounded_regular(self.root / "record", 4, "verification record")
        self.assertEqual(requested, [5])

    def test_plain_repository_preserves_real_index_objects_and_configuration(self):
        files, binding = git_snapshot.capture_git_metadata(self.root, self.settings)
        self.assertEqual(files[".git/index"][1], (self.common / "index").read_bytes())
        self.assertEqual(files[".git/config"][1], (self.common / "config").read_bytes())
        self.assertTrue(any(name.startswith(".git/objects/") and body for name, (_, body) in files.items()))
        self.assertEqual(binding["profile"], "git-readonly-metadata/v1")
        self.assertFalse(binding["qualified"])
        self.assertTrue(binding["limitations"])

    def test_v2_profile_is_qualified_only_after_hermetic_dependency_checks(self):
        files, binding = git_snapshot.capture_git_metadata(self.root, self.settings, qualified=True)
        self.assertIn(".git/index", files)
        self.assertEqual(binding["profile"], "git-hermetic-relocated/v2")
        self.assertTrue(binding["qualified"])
        self.assertEqual(binding["limitations"], [])

    def test_v2_rejects_hooks_hookspath_and_nested_repositories(self):
        hook = self.common / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\n")
        with self.assertRaisesRegex(ValueError, "hook"):
            git_snapshot.capture_git_metadata(self.root, self.settings, qualified=True)
        hook.unlink()
        self.git("config", "core.hooksPath", "hooks")
        _, legacy = git_snapshot.capture_git_metadata(self.root, self.settings)
        self.assertEqual(legacy["profile"], "git-readonly-metadata/v1")
        with self.assertRaisesRegex(ValueError, "configuration"):
            git_snapshot.capture_git_metadata(self.root, self.settings, qualified=True)
        self.git("config", "--unset", "core.hooksPath")
        nested = self.root / "nested" / ".git"
        nested.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "nested"):
            git_snapshot.capture_git_metadata(self.root, self.settings, qualified=True)

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

    def test_v2_producer_and_consumer_require_retained_native_and_current_closures(self):
        started = execution_control(self.root, {"workflow_file": "workflow.md", "action": "start"}, "apply")
        run_id = started["ledger"]["run_id"]
        execution_control(self.root, {"workflow_file": "workflow.md", "action": "reserve", "dispatch_id": "qualified",
                                     "kind": "verification", "expected_run_id": run_id}, "apply")
        engine = {"schema_version": "docker-engine-binding/v2", "cli": {"path": "/usr/local/bin/docker", "sha256": "1" * 64},
                  "endpoint": "unix:///tmp/docker.sock", "version": {"bound": True}, "info": {"bound": True}}
        base = {"Id": "sha256:" + "2" * 64, "RepoDigests": ["python@sha256:" + "a" * 64],
                "Os": "linux", "Architecture": "arm64", "Variant": None,
                "RootFS": {"Type": "layers", "Layers": ["sha256:" + "3" * 64]},
                "Config": {"OnBuild": None, "Volumes": None}}
        middle = [("image", "inspect"), ("image", "ls"), ("build",), ("image", "inspect"), ("ps",),
                  ("create",), ("inspect",), ("cp",), ("start",), ("inspect",), ("wait",), ("cp",),
                  ("ps",), ("inspect",), ("rm",), ("ps",), ("image", "ls"), ("image", "inspect"),
                  ("image", "rm"), ("image", "ls"), ("image", "inspect")]

        class FakeClient:
            def __init__(self, *args):
                self.events = []
            def engine_binding(self):
                position = "version" if not self.events else "version"
                self.events.extend({"argv": [name], "exit_code": 0, "timed_out": False, "output_limited": False}
                                   for name in (position, "info"))
                return engine

        def image_run(client, *args, **kwargs):
            self.assertTrue(client.qualified)
            client.events.extend({"argv": list(prefix), "exit_code": 0, "timed_out": False, "output_limited": False}
                                 for prefix in middle)
            return {"completed": True, "exit_code": 0, "stdout": b"ok\n", "stderr": b"", "base_image": base,
                    "base_image_after": base,
                    "image_id": "sha256:" + "4" * 64, "input_readback": {"verified": True},
                    "post_input_readback": {"verified": True}, "runtime_attestation": {"bound": True},
                    "cleanup_confirmed": True, "image_tag_cleanup_confirmed": True}

        qualified = {**self.inputs, "docker": {**self.inputs["docker"], "qualification_profile": "docker-qualified/v2"},
                     "dispatch_id": "qualified", "expected_run_id": run_id}
        with patch.object(docker_workflow, "DockerClient", FakeClient), patch.object(docker_workflow, "execute_image", side_effect=image_run), \
             patch.object(docker_workflow, "inspect_image", return_value=base):
            produced = docker_workflow.execute_docker_verification(self.root, qualified, "apply")
        self.assertEqual(produced["record"]["schema_version"], "docker-verification-record/v2")
        self.assertFalse(produced["reusable"])
        observation = {"native_event_id": "retained-real-tool-event", **produced["observation_material"]}
        record_path = self.root / produced["record_path"]
        record_body = record_path.read_bytes()
        deeply_nested_record = "0"
        for _ in range(10_000):
            deeply_nested_record = "[" + deeply_nested_record + "]"
        record_path.write_text(deeply_nested_record)
        with patch("speckit_pro_runner.verification_docker_runtime.DockerClient",
                   side_effect=AssertionError("deep record reached Docker")) as docker:
            rejected = validate_execution_record(self.root, {"workflow_file": "workflow.md", "command_id": "UNIT_TEST",
                                                              "record_path": produced["record_path"],
                                                              "native_observation": observation})
        self.assertFalse(rejected["reusable"])
        self.assertTrue(any(reason.startswith("unverifiable_record") for reason in rejected["reasons"]))
        docker.assert_not_called()
        record_path.write_bytes(record_body)
        swapped_record = {**produced["record"], "dispatch_id": "swapped-after-outer-read"}
        swapped_body = json.dumps(swapped_record, sort_keys=True).encode()
        swapped_observation = json.loads(json.dumps(observation))
        swapped_observation["docker_qualification"]["record_sha256"] = docker_workflow.sha(swapped_body)
        read_descriptions = []
        original_reader = verification_records._read_bounded_regular
        def read_then_swap(path, limit, description):
            body = original_reader(path, limit, description)
            read_descriptions.append(description)
            if description == "verification record":
                record_path.write_bytes(swapped_body)
            return body
        with patch.object(verification_records, "_read_bounded_regular", side_effect=read_then_swap), \
             patch("speckit_pro_runner.verification_docker_runtime.DockerClient",
                   side_effect=AssertionError("swapped record reached Docker")) as docker:
            rejected = validate_execution_record(self.root, {"workflow_file": "workflow.md", "command_id": "UNIT_TEST",
                                                              "record_path": produced["record_path"],
                                                              "native_observation": swapped_observation})
        self.assertIn("native_event_disagrees_with_docker_closure", rejected["reasons"])
        self.assertEqual(read_descriptions, ["verification record"])
        docker.assert_not_called()
        record_path.write_bytes(record_body)

        class ValidationClient:
            def __init__(self, *args):
                pass
            def engine_binding(self):
                return engine

        validation = {"workflow_file": "workflow.md", "command_id": "UNIT_TEST",
                      "record_path": produced["record_path"], "native_observation": observation}
        with patch("speckit_pro_runner.verification_docker_runtime.DockerClient", ValidationClient), \
             patch("speckit_pro_runner.verification_docker_image.inspect_image", return_value=base):
            first = validate_execution_record(self.root, validation)
            second = validate_execution_record(self.root, validation)
        self.assertTrue(first["reusable"], first["reasons"])
        self.assertTrue(second["reusable"], second["reasons"])
        with patch("speckit_pro_runner.verification_docker_runtime.DockerClient", side_effect=AssertionError("untrusted observation reached Docker")) as docker:
            self.assertFalse(validate_execution_record(self.root, {**validation, "native_observation": None})["reusable"])
            wrong = json.loads(json.dumps(observation))
            wrong["docker_qualification"]["execution_closure_sha256"] = "0" * 64
            self.assertIn("native_event_disagrees_with_docker_closure",
                          validate_execution_record(self.root, {**validation, "native_observation": wrong})["reasons"])
        docker.assert_not_called()

        stdout = self.root / produced["record"]["output_directory"] / "stdout"
        stdout.write_bytes(b"changed")
        with patch("speckit_pro_runner.verification_docker_runtime.DockerClient", side_effect=AssertionError("tampered evidence reached Docker")) as docker:
            changed = validate_execution_record(self.root, validation)
        self.assertIn("retained_docker_output_changed", changed["reasons"])
        docker.assert_not_called()
        stdout.write_bytes(b"ok\n")
        evidence_path = self.root / produced["evidence_path"]
        evidence_body = evidence_path.read_bytes()
        deeply_nested = "0"
        for _ in range(1000):
            deeply_nested = "[" + deeply_nested + "]"
        evidence_path.write_text(deeply_nested)
        with patch("speckit_pro_runner.verification_docker_runtime.DockerClient",
                   side_effect=AssertionError("deep evidence reached Docker")) as docker:
            changed = validate_execution_record(self.root, validation)
        self.assertTrue(any(reason.startswith("unverifiable_docker_record") for reason in changed["reasons"]))
        docker.assert_not_called()
        malformed = json.loads(evidence_body)
        malformed["result"]["input_readback"] = []
        evidence_path.write_text(json.dumps(malformed))
        with patch("speckit_pro_runner.verification_docker_runtime.DockerClient",
                   side_effect=AssertionError("malformed evidence reached Docker")) as docker:
            changed = validate_execution_record(self.root, validation)
        self.assertIn("docker_readback_receipt_disagrees_with_evidence", changed["reasons"])
        docker.assert_not_called()
        evidence_path.write_bytes(evidence_body)
        (self.root / "tracked.txt").write_text("changed after qualification\n")
        with patch("speckit_pro_runner.verification_docker_runtime.DockerClient", side_effect=AssertionError("stale input reached Docker")) as docker:
            changed = validate_execution_record(self.root, validation)
        self.assertIn("docker_current_input_closure_changed", changed["reasons"])
        docker.assert_not_called()


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(GitSnapshotTests),
                                label="test-verification-git"))
