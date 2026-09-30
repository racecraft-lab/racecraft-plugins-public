#!/usr/bin/env python3
"""Host and Docker verification records: independently observed, ledger-bound evidence."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "speckit-pro"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from execution_verification_fixture import VerificationFixture, unittest_output
from test_result import run_counted
from speckit_pro_runner.execution_control import execution_control, ignore_owned_directory, is_runner_byproduct
from speckit_pro_runner.verification_records import (digest, execute_verification, project_command,
                                                     run_snapshot_command, tree_bytes, validate_execution_record)


class VerificationTests(VerificationFixture, unittest.TestCase):
    def test_directory_named_gitignore_fails_with_a_clear_error(self):
        owned = self.root / "feature/.process/execution-control"
        (owned / ".gitignore").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, r"\.gitignore is not a regular file"):
            ignore_owned_directory(owned)
        self.assertTrue((owned / ".gitignore").is_dir())

    def test_directory_wide_add_never_stages_ledger_or_verification_evidence(self):
        self.assert_directory_wide_add_never_stages_evidence()

    def test_true_reuse_requires_independent_native_observation(self):
        result, observed = self.produce()
        self.assertFalse(self.validate(result, observed)["reusable"])
        self.assertFalse(self.validate(result)["reusable"])

    def test_a_failing_run_records_its_failing_checks_on_the_ledger(self):
        (self.root / "check.py").write_text("import sys\nsys.stderr.write(" + repr(unittest_output("test_a"))
                                            + ")\nsys.exit(1)\n")
        result, _ = self.produce()
        ledger_file = next((self.root / "feature/.process/execution-control").glob("*.json"))
        item = json.loads(ledger_file.read_text())["dispatches"][result["record"]["dispatch_id"]]
        self.assertEqual(item["failing_checks"]["command_id"], "UNIT_TEST")
        self.assertEqual(item["failing_checks"]["failing"], ["test_a (tests.test_sample.SampleTests.test_a)"])

    def test_produced_record_fields_match_published_schema(self):
        result, _ = self.produce()
        schema_path = Path(__file__).resolve().parents[3] / "speckit-pro/speckit_pro_runner/contracts/verification-record.schema.json"
        schema = json.loads(schema_path.read_text())
        self.assertLessEqual(set(result["record"]), set(schema["properties"]))
        self.assertLessEqual(set(schema["required"]), set(result["record"]))
        self.assertIn("output_directory", schema["required"])

    def test_synthetic_qualified_host_event_not_portable_runtime_qualification(self):
        result, observed = self.produce()
        path = self.root / result["record_path"]
        record = json.loads(path.read_text())
        # Synthetic host adapter fixture: no claim the portable copy-only
        # producer actually implements this independently qualified host mode.
        record["isolation_mode"] = "qualified_readonly_snapshot"
        path.write_text(json.dumps(record))
        observed["isolation_mode"] = "qualified_readonly_snapshot"
        observed["qualified_isolation"] = {
            "schema_version": "native-isolation/v1",
            **{key: record[key] for key in ("execution_id", "snapshot_sha256", "environment_sha256", "toolchain", "output_directory")},
            "readonly_snapshot_identity": "fixture-readonly-mount", "isolated_output_identity": "fixture-output-mount",
            "qualification_id": "synthetic-test-only", "external_input_sha256": "a" * 64,
            "current_external_input_sha256": "a" * 64}
        self.assertTrue(self.validate(result, observed)["reusable"])
        observed["qualified_isolation"]["output_directory"] = str(self.root / "wrong-output")
        self.assertIn("isolation_event_binding_mismatch", self.validate(result, observed)["reasons"])
        observed["qualified_isolation"]["output_directory"] = record["output_directory"]
        observed["qualified_isolation"]["current_external_input_sha256"] = "b" * 64
        self.assertFalse(self.validate(result, observed)["reusable"])
        observed["qualified_isolation"]["current_external_input_sha256"] = "a" * 64
        record["isolation_mode"] = "copy_only"
        observed["isolation_mode"] = "copy_only"
        path.write_text(json.dumps(record))
        self.assertFalse(self.validate(result, observed)["reusable"])

    def test_forged_receipt_and_failed_command_cannot_pass(self):
        (self.root / "check.py").write_text("raise SystemExit(1)\n")
        result, observed = self.produce()
        path = self.root / result["record_path"]
        forged = json.loads(path.read_text())
        forged["exit_code"] = 0
        path.write_text(json.dumps(forged))
        self.assertFalse(self.validate(result, observed)["reusable"])

    def test_source_fixture_configuration_and_environment_invalidate(self):
        for name in ("check.py", "fixture.txt", "feature/workflow.md"):
            with self.subTest(name=name):
                result, observed = self.produce()
                path = self.root / name
                old = path.read_bytes()
                path.write_bytes(old + b"\n")
                invalid = self.validate(result, observed)
                self.assertFalse(invalid["reusable"])
                self.assertIn("input_snapshot_changed", invalid["reasons"])
                path.write_bytes(old)
        result, observed = self.produce()
        # The binding covers the variables the child actually receives. Changing
        # one of those still invalidates reuse; an unrelated host variable no
        # longer reaches the child, so it must not.
        with patch.dict(os.environ, {"TZ": "UTC-14"}):
            self.assertIn("toolchain_or_environment_changed", self.validate(result, observed)["reasons"])
        with patch.dict(os.environ, {"VERIFICATION_CHANGED": "yes"}):
            self.assertNotIn("toolchain_or_environment_changed", self.validate(result, observed)["reasons"])

    def test_missing_receipt_and_native_result_mismatch_fail_closed(self):
        result, observed = self.produce()
        observed["exit_code"] = 99
        self.assertFalse(self.validate(result, observed)["reusable"])
        (self.root / result["record_path"]).unlink()
        self.assertFalse(self.validate(result, observed)["reusable"])

    def test_file_and_directory_modes_invalidate_snapshot_identity(self):
        for name in ("fixture.txt", "feature"):
            with self.subTest(name=name):
                result, observed = self.produce()
                path = self.root / name
                original_mode = path.stat().st_mode & 0o777
                try:
                    path.chmod(original_mode ^ 0o010)
                    self.assertIn("input_snapshot_changed", self.validate(result, observed)["reasons"])
                finally:
                    path.chmod(original_mode)

    def test_empty_directory_changes_invalidate_snapshot_identity(self):
        result, observed = self.produce()
        (self.root / "new-empty-directory").mkdir()
        self.assertIn("input_snapshot_changed", self.validate(result, observed)["reasons"])

    def test_materialized_snapshot_preserves_empty_directories_and_executable_bits(self):
        (self.root / "empty-directory").mkdir(mode=0o750)
        (self.root / "fixture.txt").chmod(0o754)
        (self.root / "check.py").write_text(
            "from pathlib import Path\n"
            "assert Path('empty-directory').is_dir()\n"
            "assert Path('empty-directory').stat().st_mode & 0o777 == 0o750\n"
            "assert Path('fixture.txt').stat().st_mode & 0o777 == 0o754\n"
        )
        result, _ = self.produce()
        self.assertEqual(result["record"]["exit_code"], 0)
        self.assertTrue(result["record"]["snapshot_unchanged"])

    def test_snapshot_directory_mode_mutation_is_detected(self):
        (self.root / "check.py").write_text("from pathlib import Path\nPath('feature').chmod(0o700)\n")
        result, _ = self.produce()
        self.assertFalse(result["record"]["snapshot_unchanged"])

    def test_child_environment_excludes_host_credentials(self):
        canaries = {
            "SPECKIT_TEST_CANARY": "top-secret-value",
            "AWS_SECRET_ACCESS_KEY": "aws-canary",
            "GITHUB_TOKEN": "gh-canary",
            "NPM_TOKEN": "npm-canary",
        }
        with patch.dict(os.environ, canaries):
            with patch("speckit_pro_runner.verification_records.run_snapshot_command", wraps=run_snapshot_command) as launched:
                self.produce()
        environment = launched.call_args.args[2]
        for name, value in canaries.items():
            self.assertNotIn(name, environment, f"{name} leaked into the verification child environment")
            self.assertNotIn(value, environment.values())

    def test_child_home_is_relocated_away_from_the_operator_account(self):
        with patch("speckit_pro_runner.verification_records.run_snapshot_command", wraps=run_snapshot_command) as launched:
            result, _ = self.produce()
        environment = launched.call_args.args[2]
        outputs = result["record"]["output_directory"]
        self.assertEqual(outputs, environment["HOME"])
        self.assertNotEqual(str(Path.home()), environment["HOME"])
        for name in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME"):
            self.assertEqual(outputs, environment[name])

    def test_record_binds_effective_child_environment_after_output_relocation(self):
        with patch("speckit_pro_runner.verification_records.run_snapshot_command", wraps=run_snapshot_command) as launched:
            result, _ = self.produce()
        environment = launched.call_args.args[2]
        self.assertEqual(result["record"]["environment_sha256"], digest(environment))
        self.assertEqual(result["record"]["output_directory"], environment["SPECKIT_VERIFICATION_OUTPUT_DIR"])

    def test_output_relocation_is_bound_to_independent_observation(self):
        result, observed = self.produce()
        path = self.root / result["record_path"]
        record = json.loads(path.read_text())
        record["output_directory"] = str(self.root / "forged-output")
        path.write_text(json.dumps(record))
        self.assertIn("native_event_disagrees_with_receipt", self.validate(result, observed)["reasons"])

    def test_reserved_verification_cannot_launch_twice(self):
        result, _ = self.produce()
        with self.assertRaisesRegex(ValueError, "dispatch_already_started_no_relaunch"):
            execute_verification(self.root, {**self.inputs, "dispatch_id": result["record"]["dispatch_id"],
                                            "expected_run_id": self.run_id}, "apply")

    def test_snapshot_mutation_and_unknown_command_do_not_reuse(self):
        (self.root / "check.py").write_text("from pathlib import Path\np=Path('fixture.txt')\np.chmod(0o600)\np.write_text('mutated')\n")
        result, observed = self.produce()
        self.assertFalse(self.validate(result, observed)["reusable"])
        self.assertEqual((self.root / "fixture.txt").read_text(), "dirty untracked fixture")
        with self.assertRaises(ValueError):
            execute_verification(self.root, {**self.inputs, "command_id": "LINT_FIX"}, "apply")

    def test_verification_source_has_no_dynamic_or_shell_executable_findings(self):
        from speckit_pro_runner.gates.active_path_guard import repo_bash_python_findings

        source = Path(__file__).resolve().parents[3] / "speckit-pro/speckit_pro_runner/verification_records.py"
        self.assertEqual(repo_bash_python_findings("speckit-pro/speckit_pro_runner/verification_records.py", source.read_text()), [])

    def test_workflow_shell_jq_and_unsupported_executables_are_rejected(self):
        for command in ("bash -c true", "sh -c true", "jq . fixture.json", "env python3 check.py", "unqualified-tool check.py"):
            with self.subTest(command=command):
                (self.root / "feature/workflow.md").write_text("## PROJECT_COMMANDS\n```json\n" + json.dumps({"UNIT_TEST": command}) + "\n```\n")
                with self.assertRaisesRegex(ValueError, "ordinary native verification"):
                    project_command(self.root / "feature/workflow.md", "UNIT_TEST")

    def test_supported_tools_keep_literal_executable_arguments_and_environment(self):
        programs = ("python", "python3", "node", "npm", "npx", "pnpm", "yarn", "bun", "cargo", "go", "make", "pytest", "lint-imports", "uv", "ruff", "mypy")
        for program in programs:
            with self.subTest(program=program), patch("speckit_pro_runner.verification_records.shutil.which", side_effect=lambda name, **kwargs: f"/qualified-tools/{name}"), patch("speckit_pro_runner.verification_records.subprocess.Popen") as popen:
                process = popen.return_value.__enter__.return_value
                process.communicate.return_value = (b"ok", b"")
                process.returncode = 0
                environment = {"PATH": "/qualified-tools"}
                result = run_snapshot_command([program, "check", "one argument"], self.root, environment, 1)
                self.assertEqual(result, (0, b"ok", b"", True))
                self.assertEqual(popen.call_args.args[0], [f"/qualified-tools/{program}", "check", "one argument"])
                self.assertEqual(popen.call_args.kwargs["env"], environment)
                self.assertIs(popen.call_args.kwargs["shell"], False)
                self.assertNotIn("executable", popen.call_args.kwargs)

    def test_path_python_is_not_replaced_with_the_runner_interpreter(self):
        requested = "/qualified-tools/python3.11"
        with patch("speckit_pro_runner.verification_records.shutil.which", return_value=requested), patch("speckit_pro_runner.verification_records.subprocess.Popen") as popen:
            process = popen.return_value.__enter__.return_value
            process.communicate.return_value = (b"ok", b"")
            process.returncode = 0
            run_snapshot_command(["python3", "check.py"], self.root, {"PATH": "/qualified-tools"}, 1, expected_executable=requested)
            self.assertEqual(popen.call_args.args[0], [requested, "check.py"])
            self.assertNotIn("executable", popen.call_args.kwargs)

    def test_changed_or_relative_executable_resolution_cannot_launch(self):
        for resolved, expected in (("/different-tools/python3", "/qualified-tools/python3"), ("relative/python3", None)):
            with self.subTest(resolved=resolved), patch("speckit_pro_runner.verification_records.shutil.which", return_value=resolved), patch("speckit_pro_runner.verification_records.subprocess.Popen") as popen:
                with self.assertRaisesRegex(ValueError, "ordinary native verification"):
                    run_snapshot_command(["python3", "check.py"], self.root, {"PATH": "relative"}, 1, expected_executable=expected)
                popen.assert_not_called()

    def test_virtualenv_invocation_is_preserved_even_when_binary_target_is_shared(self):
        interpreter = self.root / "venv/bin/python3"
        interpreter.parent.mkdir(parents=True)
        interpreter.symlink_to(sys.executable)
        with patch("speckit_pro_runner.verification_records.shutil.which", return_value=str(interpreter)), patch("speckit_pro_runner.verification_records.subprocess.Popen") as popen:
            process = popen.return_value.__enter__.return_value
            process.communicate.return_value = (b"ok", b"")
            process.returncode = 0
            run_snapshot_command(["python3", "check.py"], self.root, {"PATH": str(interpreter.parent)}, 1, expected_executable=str(interpreter))
            self.assertEqual(popen.call_args.args[0], [str(interpreter), "check.py"])

    def test_process_directory_workflow_evidence_is_not_doubled_and_legacy_record_is_read(self):
        workflow = "docs/ai/specs/.process/workflow.md"
        # An in-flight run already holds the doubled evidence directory.
        (self.root / "docs/ai/specs/.process/.process/verification").mkdir(parents=True)
        (self.root / workflow).write_text((self.root / "feature/workflow.md").read_text())
        inputs = {"workflow_file": workflow, "command_id": "UNIT_TEST"}
        run_id = execution_control(self.root, {"workflow_file": workflow, "action": "start"}, "apply")["ledger"]["run_id"]
        execution_control(self.root, {"workflow_file": workflow, "action": "reserve", "dispatch_id": "verify-1",
                                      "kind": "verification", "expected_run_id": run_id}, "apply")
        result = execute_verification(self.root, {**inputs, "dispatch_id": "verify-1", "expected_run_id": run_id}, "apply")
        name = Path(result["record_path"]).name
        self.assertEqual(result["record_path"], f"docs/ai/specs/.process/verification/{name}")
        self.assertTrue((self.root / result["record_path"]).is_file())
        self.assertFalse([path for path in tree_bytes(self.root, workflow) if "verification" in path])
        current = validate_execution_record(self.root, {**inputs, "record_path": result["record_path"]})
        self.assertFalse([reason for reason in current["reasons"] if reason.startswith("unverifiable_record")])

        legacy = f"docs/ai/specs/.process/.process/verification/{name}"
        (self.root / result["record_path"]).rename(self.root / legacy)
        self.assertFalse([path for path in tree_bytes(self.root, workflow) if "verification" in path])
        self.assertTrue(is_runner_byproduct(legacy) and is_runner_byproduct(result["record_path"]))
        self.assertEqual(validate_execution_record(self.root, {**inputs, "record_path": legacy}), current)
        stray = f"docs/ai/specs/verification/{name}"
        (self.root / stray).parent.mkdir(parents=True)
        (self.root / legacy).rename(self.root / stray)
        self.assertIn("unverifiable_record: record_path is not this workflow's verification evidence",
                      validate_execution_record(self.root, {**inputs, "record_path": stray})["reasons"])


class DockerVerificationTests(VerificationFixture, unittest.TestCase):
    """Docker-backed verification; host methods have their own class."""

    def setUp(self):
        super().setUp()
        (self.root / "feature/workflow.md").write_text('## PROJECT_COMMANDS\n```json\n{"UNIT_TEST":"python3 check.py"}\n```\n')
        self.inputs["docker"] = {"executable": "/usr/local/bin/docker", "endpoint": "unix:///tmp/docker.sock",
                                 "base_image": "python@sha256:" + "a" * 64, "output_contract": "streams_only"}

    def test_docker_directory_wide_add_never_stages_evidence(self):
        self.assert_directory_wide_add_never_stages_evidence()

    def test_docker_dry_run_does_not_resolve_host_tools_or_contact_daemon(self):
        with patch("speckit_pro_runner.verification_records.project_program", side_effect=AssertionError("host tool used")):
            result = execute_verification(self.root, self.inputs, "dry_run")
        self.assertEqual(result["argv"], ["python3", "check.py"])
        self.assertFalse(result["authorization_granted"] or result["writes_state"] or result["reusable"])

    def test_docker_requires_explicit_supported_configuration(self):
        for change in ({"output_contract": "files"}, {"extra": True}, {"base_image": "python:latest"},
                       {"endpoint": "tcp://remote:2375"}, {"executable": "docker"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                execute_verification(self.root, {**self.inputs, "docker": {**self.inputs["docker"], **change}}, "dry_run")

    def test_docker_requires_ledger_reservation_before_daemon_access(self):
        from speckit_pro_runner import verification_docker_workflow as workflow_backend
        with patch.object(workflow_backend, "DockerClient") as client, self.assertRaises(ValueError):
            execute_verification(self.root, {**self.inputs, "dispatch_id": "not-reserved"}, "apply")
        client.assert_not_called()

    def test_docker_receipt_is_image_bound_and_cannot_authorize_reuse_or_relaunch(self):
        from speckit_pro_runner import verification_docker_workflow as workflow_backend
        image_id = "sha256:" + "b" * 64
        backend = {"completed": True, "exit_code": 0, "stdout": b"verified\n", "stderr": b"",
                   "input_readback": {"verified": True},
                   "image_id": image_id, "base_image": {"Id": "sha256:" + "c" * 64},
                   "cleanup_confirmed": True, "image_tag_cleanup_confirmed": True, "reusable": False}
        with patch.object(workflow_backend, "DockerClient") as client, \
             patch.object(workflow_backend, "execute_image", return_value=backend) as launch:
            client.return_value.events = []
            result, observation = self.produce()
            record = result["record"]
            self.assertEqual(record["schema_version"], "docker-verification-record/v1")
            self.assertEqual(record["toolchain"]["image_id"], image_id)
            self.assertNotIn("executable_sha256", record["toolchain"])
            self.assertTrue(record["completed"] and record["inputs_unchanged"])
            self.assertTrue(record["input_snapshot_verified"])
            self.assertFalse(self.validate(result, observation)["reusable"])
            evidence = self.root / result["evidence_path"]
            self.assertTrue(evidence.is_file())
            self.assertEqual((evidence.parent / "stdout").read_bytes(), b"verified\n")
            self.assertEqual(record["evidence_sha256"], workflow_backend.sha(evidence.read_bytes()))
            schema = json.loads((Path(workflow_backend.__file__).parent / "contracts/docker-verification-record.schema.json").read_text())
            self.assertEqual(set(record), set(schema["required"]))
            self.assertEqual(set(record), set(schema["properties"]))
            with self.assertRaisesRegex(ValueError, "dispatch_already_started_no_relaunch"):
                execute_verification(self.root, {**self.inputs, "dispatch_id": record["dispatch_id"],
                                                "expected_run_id": self.run_id}, "apply")
            client.assert_called_once()
            launch.assert_called_once()

    def test_docker_failed_preparation_retains_evidence_and_consumes_reservation(self):
        from speckit_pro_runner import verification_docker_workflow as workflow_backend
        with patch.object(workflow_backend, "DockerClient", side_effect=ValueError("daemon unavailable")):
            result, _ = self.produce()
        self.assertFalse(result["record"]["completed"] or result["reusable"])
        self.assertIsNone(result["record"]["toolchain"]["image_id"])
        self.assertTrue((self.root / result["evidence_path"]).is_file())
        ledger_file = next((self.root / "feature/.process/execution-control").glob("*.json"))
        evidence = json.loads(ledger_file.read_text())["dispatches"][result["record"]["dispatch_id"]]["failing_checks"]
        self.assertEqual((evidence["command_id"], evidence["format"], evidence["failing"]), ("UNIT_TEST", "unparsed", None))
        with patch.object(workflow_backend, "DockerClient") as client, \
             self.assertRaisesRegex(ValueError, "dispatch_already_started_no_relaunch"):
            execute_verification(self.root, {**self.inputs, "dispatch_id": result["record"]["dispatch_id"],
                                            "expected_run_id": self.run_id}, "apply")
        client.assert_not_called()

    def test_docker_command_cannot_silently_rewrite_a_host_executable(self):
        for command in (f"{sys.executable} check.py", "sh -c true", "python3 ../outside.py", "python3 check.py\u0000bad"):
            with self.subTest(command=command), self.assertRaises(ValueError):
                (self.root / "feature/workflow.md").write_text("## PROJECT_COMMANDS\n```json\n" + json.dumps({"UNIT_TEST": command}) + "\n```\n")
                execute_verification(self.root, self.inputs, "dry_run")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-execution-verification"))
