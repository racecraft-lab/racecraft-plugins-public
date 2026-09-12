#!/usr/bin/env python3
"""Deterministic durable budget and independently observed verification contracts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "speckit-pro"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted
from speckit_pro_runner.execution_control import durable_json, execution_control
from speckit_pro_runner.verification_records import digest, execute_verification, project_command, run_snapshot_command, validate_execution_record


class ExecutionControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "feature").mkdir()
        (self.root / "feature/workflow.md").write_text("# Workflow\n")
        (self.root / "feature/spec.md").write_text("- FR-001: preserve data\n- FR-002: no secrets\n")
        self.now = 1000.0
        self.run_id = None

    def invoke(self, action, mode="apply", **inputs):
        binding = {"expected_run_id": self.run_id} if self.run_id else {}
        with patch("speckit_pro_runner.execution_control.time.time", return_value=self.now):
            result = execution_control(self.root, {"workflow_file": "feature/workflow.md", "action": action, **binding, **inputs}, mode)
        if mode == "apply":
            self.run_id = result["ledger"]["run_id"]
        return result

    def test_start_is_idempotent_and_phase_changes_do_not_reset_clock(self):
        first = self.invoke("start")
        self.now += 2800
        second = self.invoke("start")
        self.assertEqual(first["ledger"]["run_id"], second["ledger"]["run_id"])
        self.assertTrue(second["checkpoint_due"])
        self.assertEqual(second["elapsed_seconds"], 2800)

    def test_one_family_and_two_global_reservations_across_restart(self):
        self.invoke("start")
        first = self.invoke("reserve", dispatch_id="fix-a", kind="corrective", failure_invariant="FR-001")
        self.invoke("complete", dispatch_id="fix-a", outcome="failed")
        denied = self.invoke("reserve", dispatch_id="renamed-error", kind="corrective", failure_invariant="FR-001")
        self.assertEqual(denied["disposition"], "checkpoint_required")
        second = self.invoke("reserve", dispatch_id="fix-b", kind="corrective", failure_invariant="FR-002")
        self.assertEqual(second["disposition"], "continue")
        third = self.invoke("reserve", dispatch_id="fix-c", kind="corrective", failure_invariant="new-error")
        self.assertEqual(third["disposition"], "checkpoint_required")
        self.assertEqual(first["ledger"]["corrective_cycles"], 1)

    def test_unknown_families_share_budget_and_nested_hardener_reuses_reservation(self):
        self.invoke("start")
        first = self.invoke("reserve", dispatch_id="repair", kind="corrective", failure_invariant="whatever")
        reservation = first["reservation_id"]
        nested = self.invoke("reserve", dispatch_id="nested", kind="corrective", reservation_id=reservation)
        self.assertEqual(nested["ledger"]["corrective_cycles"], 1)
        denied = self.invoke("reserve", dispatch_id="other", kind="corrective", failure_invariant="different words")
        self.assertEqual(denied["disposition"], "checkpoint_required")

    def test_failed_nested_correction_cannot_launder_another_cycle(self):
        self.invoke("start")
        first = self.invoke("reserve", dispatch_id="owner", kind="corrective", failure_invariant="FR-001")
        reservation = first["reservation_id"]
        self.invoke("reserve", dispatch_id="nested-one", kind="corrective", reservation_id=reservation)
        self.invoke("complete", dispatch_id="nested-one", outcome="failed")
        self.assertEqual(self.invoke("reserve", dispatch_id="nested-two", kind="corrective", reservation_id=reservation)["disposition"], "checkpoint_required")

    def test_missing_result_has_one_inspection_and_no_relaunch(self):
        self.invoke("start")
        self.invoke("reserve", dispatch_id="task", kind="implementation")
        first = self.invoke("reconcile", dispatch_id="task")
        self.assertTrue(first["reconciliation_allowed"])
        second = self.invoke("reconcile", dispatch_id="task")
        self.assertFalse(second["reconciliation_allowed"])
        self.assertEqual(self.invoke("reserve", dispatch_id="task", kind="implementation")["disposition"], "checkpoint_required")
        self.assertEqual(self.invoke("status", mode="read_only")["disposition"], "checkpoint_required")
        self.assertEqual(self.invoke("reserve", dispatch_id="renamed-task", kind="implementation")["disposition"], "checkpoint_required")

    def test_unknown_effects_block_already_reserved_verification_until_native_resolution(self):
        start = self.invoke("start")
        self.invoke("reserve", dispatch_id="worker", kind="implementation")
        self.invoke("reserve", dispatch_id="verify", kind="verification")
        self.invoke("complete", dispatch_id="worker", outcome="unknown")
        self.assertEqual(self.invoke("begin-verification", dispatch_id="verify")["disposition"], "checkpoint_required")
        self.assertEqual(self.invoke("complete", dispatch_id="worker", outcome="completed")["disposition"], "checkpoint_required")
        resolved = self.invoke("complete", dispatch_id="worker", outcome="completed", native_observation={
            "native_event_id": "recovered-real-result", "run_id": start["ledger"]["run_id"],
            "dispatch_id": "worker", "action": "dispatch_result", "outcome": "completed"})
        self.assertEqual(resolved["disposition"], "continue")
        self.assertEqual(self.invoke("begin-verification", dispatch_id="verify")["disposition"], "continue")

    def test_expected_tdd_red_is_not_repair_but_verification_red_is_failure(self):
        self.invoke("start")
        self.invoke("reserve", dispatch_id="tdd", kind="implementation")
        result = self.invoke("complete", dispatch_id="tdd", outcome="expected_tdd_red")
        self.assertEqual(result["ledger"]["corrective_cycles"], 0)
        self.invoke("reserve", dispatch_id="verify", kind="verification")
        with self.assertRaises(ValueError):
            self.invoke("complete", dispatch_id="verify", outcome="expected_tdd_red")

    def test_wall_limits_unknown_clock_and_self_asserted_pause_fail_closed(self):
        self.invoke("start")
        self.now += 5400
        self.assertEqual(self.invoke("reserve", dispatch_id="late", kind="implementation")["disposition"], "checkpoint_required")
        self.now = 900
        self.assertIn("clock_moved_backwards", self.invoke("status", mode="read_only")["reasons"])
        with self.assertRaises(ValueError):
            self.invoke("pause", authorized=True, pause_kind="human_uat")

    def test_only_independent_native_wait_events_exclude_wall_time(self):
        initial = self.invoke("start")
        self.now += 100
        self.invoke("pause", native_observation={"native_event_id": "wait-start", "kind": "human_uat",
                    "action": "wait_started", "run_id": initial["ledger"]["run_id"]})
        self.now += 8000
        paused = self.invoke("status", mode="read_only")
        self.assertEqual(paused["elapsed_seconds"], 100)
        self.invoke("resume", native_observation={"native_event_id": "wait-end", "kind": "human_uat",
                    "action": "wait_ended", "wait_start_event_id": "wait-start", "run_id": initial["ledger"]["run_id"]})
        self.now += 100
        self.assertEqual(self.invoke("status", mode="read_only")["elapsed_seconds"], 200)

    def test_wait_end_replay_and_wrong_pair_cannot_exclude_more_time(self):
        initial = self.invoke("start")
        common = {"kind": "human_uat", "run_id": initial["ledger"]["run_id"]}
        self.invoke("pause", native_observation={**common, "native_event_id": "start-one", "action": "wait_started"})
        self.now += 100
        self.invoke("resume", native_observation={**common, "native_event_id": "end-one", "action": "wait_ended", "wait_start_event_id": "start-one"})
        self.invoke("pause", native_observation={**common, "native_event_id": "start-two", "action": "wait_started"})
        self.now += 100
        for event_id, start_id in (("end-one", "start-two"), ("end-two", "start-one")):
            with self.subTest(event_id=event_id, start_id=start_id):
                with self.assertRaises(ValueError):
                    self.invoke("resume", native_observation={**common, "native_event_id": event_id,
                                "action": "wait_ended", "wait_start_event_id": start_id})

    def test_completed_work_does_not_silently_reset_checkpoint_deadline(self):
        self.invoke("start")
        self.now += 2500
        self.invoke("reserve", dispatch_id="work", kind="implementation")
        self.invoke("complete", dispatch_id="work", outcome="completed")
        self.now += 300
        self.assertTrue(self.invoke("status", mode="read_only")["checkpoint_due"])
        self.assertFalse(self.invoke("checkpoint")["checkpoint_due"])

    def test_corrupted_boolean_counter_and_unapproved_invariant_rejected(self):
        result = self.invoke("start")
        path = self.root / result["ledger_path"]
        value = json.loads(path.read_text())
        value["corrective_cycles"] = True
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            self.invoke("status", mode="read_only")

    def test_dry_run_does_not_write(self):
        self.invoke("start", mode="dry_run")
        self.assertFalse((self.root / "feature/.process").exists())

    def test_different_workflows_cannot_share_the_same_ledger(self):
        first = self.invoke("start")
        (self.root / "feature/other-workflow.md").write_text("# Other workflow\n")
        other = execution_control(self.root, {"workflow_file": "feature/other-workflow.md", "action": "start"}, "apply")
        self.assertNotEqual(first["ledger_path"], other["ledger_path"])
        self.assertNotEqual(first["ledger"]["run_id"], other["ledger"]["run_id"])

    def test_known_run_missing_ledger_cannot_be_reset_and_relocation_preserves_budget(self):
        first = self.invoke("start")
        self.invoke("reserve", dispatch_id="fix", kind="corrective", failure_invariant="FR-001")
        old_path = self.root / first["ledger_path"]
        (self.root / "feature/copied-workflow.md").write_text("# Copied workflow\n")
        copied = {"workflow_file": "feature/copied-workflow.md", "expected_run_id": self.run_id}
        with self.assertRaises(ValueError):
            execution_control(self.root, {**copied, "action": "start"}, "apply")
        with self.assertRaises(ValueError):
            execution_control(self.root, {**copied, "action": "status"}, "read_only")
        moved_path = old_path.with_name("relocated-owned-ledger.json")
        old_path.rename(moved_path)
        moved = execution_control(self.root, {**copied, "action": "status", "ledger_path": moved_path.relative_to(self.root).as_posix()}, "read_only")
        self.assertEqual(moved["ledger"]["corrective_cycles"], 1)
        with self.assertRaises(ValueError):
            self.invoke("start")

    def test_interrupted_atomic_publication_preserves_previous_record(self):
        first = self.invoke("start")
        path = self.root / first["ledger_path"]
        before = path.read_bytes()
        with patch("speckit_pro_runner.execution_control.os.replace", side_effect=OSError("injected publication interruption")):
            with self.assertRaises(OSError):
                durable_json(path, {"partial": True})
        self.assertEqual(before, path.read_bytes())
        self.assertEqual(list(path.parent.glob(".execution-*")), [])

    def test_existing_lock_fails_closed_without_resetting_reservations(self):
        first = self.invoke("start")
        path = self.root / first["ledger_path"]
        path.with_suffix(".lock").mkdir()
        with self.assertRaises(ValueError):
            self.invoke("reserve", dispatch_id="blocked", kind="corrective", failure_invariant="FR-001")
        self.assertEqual(json.loads(path.read_text())["corrective_cycles"], 0)


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "feature").mkdir()
        commands = {"UNIT_TEST": f"{sys.executable} check.py"}
        (self.root / "feature/workflow.md").write_text("## PROJECT_COMMANDS\n```json\n" + json.dumps(commands) + "\n```\n")
        (self.root / "check.py").write_text("print('verified')\n")
        (self.root / "fixture.txt").write_text("dirty untracked fixture")
        self.inputs = {"workflow_file": "feature/workflow.md", "command_id": "UNIT_TEST"}

    def produce(self):
        started = execution_control(self.root, {"workflow_file": "feature/workflow.md", "action": "start"}, "apply")
        run_id = started["ledger"]["run_id"]
        dispatch = uuid.uuid4().hex
        execution_control(self.root, {"workflow_file": "feature/workflow.md", "action": "reserve",
                                      "dispatch_id": dispatch, "kind": "verification", "expected_run_id": run_id}, "apply")
        result = execute_verification(self.root, {**self.inputs, "dispatch_id": dispatch, "expected_run_id": run_id}, "apply")
        observation = {**result["observation_material"], "native_event_id": "actual-host-event-1"}
        return result, observation

    def validate(self, result, observation=None):
        return validate_execution_record(self.root, {**self.inputs, "record_path": result["record_path"], "native_observation": observation})

    def test_true_reuse_requires_independent_native_observation(self):
        result, observed = self.produce()
        self.assertFalse(self.validate(result, observed)["reusable"])
        self.assertFalse(self.validate(result)["reusable"])

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
        with patch.dict(os.environ, {"VERIFICATION_CHANGED": "yes"}):
            self.assertIn("toolchain_or_environment_changed", self.validate(result, observed)["reasons"])

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
        started = execution_control(self.root, {"workflow_file": "feature/workflow.md", "action": "start"}, "apply")
        with self.assertRaisesRegex(ValueError, "dispatch_already_started_no_relaunch"):
            execute_verification(self.root, {**self.inputs, "dispatch_id": result["record"]["dispatch_id"],
                                            "expected_run_id": started["ledger"]["run_id"]}, "apply")

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


class RunnerDispatchTests(unittest.TestCase):
    """Exercise actual request-envelope entrypoints in a temporary consumer repo."""

    def setUp(self):
        VerificationTests.setUp(self)
        (self.root / ".specify").mkdir()

    def call_runner(self, helper, mode, **inputs):
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[3] / "speckit-pro")
        binding = {"expected_run_id": self.run_id} if getattr(self, "run_id", None) else {}
        request = {"schema_version": "1.0", "helper_id": helper, "operation": helper,
                   "mode": mode, "inputs": {"workflow_file": "feature/workflow.md", **binding, **inputs}}
        process = subprocess.run([sys.executable, "-m", "speckit_pro_runner"], cwd=self.root,
                                 env=environment, input=json.dumps(request), text=True, capture_output=True)
        result = json.loads(process.stdout)
        if helper == "execution-control" and "ledger" in result["data"]:
            self.run_id = result["data"]["ledger"]["run_id"]
        return process.returncode, result

    def test_ledger_and_verification_helpers_are_real_runner_routes(self):
        code, started = self.call_runner("execution-control", "apply", action="start")
        self.assertEqual(code, 0, started)
        code, denied = self.call_runner("execution-control", "read_only", action="reserve", dispatch_id="x", kind="implementation")
        self.assertEqual(code, 2, denied)
        code, reserved = self.call_runner("execution-control", "apply", action="reserve", dispatch_id="verify-1", kind="verification")
        self.assertEqual(code, 0, reserved)
        code, executed = self.call_runner("execute-verification", "apply", command_id="UNIT_TEST", dispatch_id="verify-1")
        self.assertEqual(code, 0, executed)
        data = executed["data"]
        code, validated = self.call_runner("validate-execution-record", "read_only", command_id="UNIT_TEST",
                                          record_path=data["record_path"], native_observation={**data["observation_material"], "native_event_id": "fixture-native-event"})
        self.assertEqual(code, 1, validated)
        self.assertFalse(validated["data"]["stdout_json"]["reusable"])

    def test_task_metadata_helper_is_registered_and_read_only(self):
        (self.root / "feature/tasks.md").write_text("# Tasks\n## Phase 1: Setup\n- [ ] T001 Create fixture in `fixture.txt`\n")
        (self.root / "feature/spec.md").write_text("# Spec\n")
        (self.root / "feature/plan.md").write_text("# Plan\n")
        code, result = self.call_runner("validate-task-execution", "read_only", tasks_file="feature/tasks.md", action="fingerprints")
        self.assertEqual(code, 0, result)
        self.assertIn("fingerprints", result["data"]["stdout_json"])
        code, result = self.call_runner("validate-task-execution", "apply", tasks_file="feature/tasks.md")
        self.assertEqual(code, 2, result)


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (ExecutionControlTests, VerificationTests, RunnerDispatchTests))
    raise SystemExit(run_counted(suite, label="test-execution-control"))
