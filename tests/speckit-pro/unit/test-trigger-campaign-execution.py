#!/usr/bin/env python3
"""Mocked dispatch, cancellation, global ceiling and resume contracts; no providers."""
from __future__ import annotations

import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
import trigger_campaign_execution as execution
import trigger_campaign as accounting
from trigger_campaign import CampaignLedger
import trigger_comparison as comparison
from test_result import run_counted


def fixture_module():
    spec = importlib.util.spec_from_file_location("campaign_comparison_fixture", ROOT / "unit/test-trigger-comparison.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request_fixture(root):
    manifest, _indexes = fixture_module().evidence_fixture(root)
    manifest["output_directory"] = str(root.resolve())
    digest = comparison.json_digest(manifest)
    approval = {"schema_version": "trigger-campaign-approval/v1", "manifest_sha256": digest,
        "launch_budget": 6, "source": {"role": "user", "message_id": "mock-user-message",
            "content": f"Approve trigger campaign {digest} with launch budget 6."}}
    return execution.CampaignRequest(manifest, approval, 6, root / "inventory.json",
        {arm: root / f"{arm}-description.txt" for arm in manifest["arms"]}, root)


class FakeChild:
    pid = 12345
    returncode = None

    def poll(self):
        return self.returncode

    def send_signal(self, signum):
        self.returncode = -signum

    def communicate(self, timeout):
        self.returncode = -signal.SIGTERM
        return b"", b""


class ExecutionTests(unittest.TestCase):
    def test_retention_failure_after_spawn_terminates_and_drains_owned_runner(self):
        with tempfile.TemporaryDirectory() as temp:
            request = request_fixture(Path(temp))
            child = FakeChild()
            with mock.patch.object(execution.subprocess, "Popen", return_value=child), mock.patch.object(execution, "write_json_once", side_effect=OSError("disk full")), mock.patch.object(child, "communicate", wraps=child.communicate) as drained:
                with self.assertRaises(OSError):
                    execution.execute_case(request.manifest["roster"][0], request, "candidate", Path(temp) / "native-case", threading.Event())
                drained.assert_called_once_with(timeout=30)
                self.assertEqual(child.returncode, -signal.SIGTERM)

    def test_forced_kill_is_reaped_and_stays_unknown(self):
        child = mock.Mock()
        child.communicate.side_effect = [subprocess.TimeoutExpired("native", 30), (b"", b"")]
        with self.assertRaisesRegex(ValueError, "cleanup is unknown"):
            execution._terminate_runner(child)
        child.kill.assert_called_once_with()
        self.assertEqual(child.communicate.call_args_list[-1], mock.call(timeout=5))

    @unittest.skipUnless(os.name == "posix", "native campaigns fail closed outside POSIX")
    def test_different_tmpdirs_contend_for_one_user_global_lease(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = request_fixture(root)
            ledger = CampaignLedger(root / "ledger.sqlite3", comparison.json_digest(request.manifest), request.approval, 6)
            canonical = []
            original_open = os.open
            def open_lock(path, flags, mode):
                canonical.append(str(path))
                return original_open(root / "isolated-test.lock", flags, mode)
            with mock.patch.object(execution.os, "open", side_effect=open_lock):
                with mock.patch.dict(os.environ, {"TMPDIR": "/tmp/one"}), execution._global_lease(request, ledger):
                    with mock.patch.dict(os.environ, {"TMPDIR": "/tmp/two"}), self.assertRaisesRegex(ValueError, "global launch ceiling"):
                        with execution._global_lease(request, ledger):
                            self.fail("second controller acquired the global lease")
            self.assertEqual(canonical, [f"/tmp/speckit-trigger-native-{os.getuid()}.lock"] * 2)

    def test_non_posix_native_execution_is_explicitly_unsupported(self):
        with mock.patch.object(execution.os, "name", "nt"), self.assertRaisesRegex(ValueError, "POSIX"):
            with execution._global_lease(None, None):
                self.fail("unsupported platform was accepted")

    def test_fixed_runner_campaign_and_completed_resume_do_not_relaunch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = request_fixture(root)
            calls = []
            def native(case, current, arm, directory, _stop):
                calls.append(execution.native_command(case, current, arm, directory))
                directory.mkdir(parents=True)
                shutil.copytree(root / arm, directory / "evidence")
                shutil.copyfile(root / arm / "report.json", directory / "report.json")
                return 0
            with mock.patch.object(execution, "execute_case", side_effect=native), mock.patch.object(execution, "_global_lease") as lease:
                result = execution.run_campaign(request)
                self.assertTrue(result["complete"])
                self.assertEqual(len(calls), 2)
                self.assertEqual(result["reserved_launches"], 6)
                self.assertTrue(all(command[1] == str(execution.RUNNERS["claude"]) and "--case-id" in command for command in calls))
                resumed = execution.run_campaign(request)
                self.assertTrue(resumed["complete"])
                self.assertEqual(len(calls), 2)
                self.assertEqual(lease.call_count, 2)

    def test_invalid_scope_is_rejected_before_provider_or_output_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            request = request_fixture(Path(temp))
            request.manifest["qualification_scope"] = "full"
            digest = comparison.json_digest(request.manifest)
            request.approval["manifest_sha256"] = digest
            request.approval["source"]["content"] = f"Approve trigger campaign {digest} with launch budget 6."
            with mock.patch.object(execution, "execute_case") as native, self.assertRaisesRegex(ValueError, "entire dual-host"):
                execution.run_campaign(request)
            native.assert_not_called()

    def test_same_approval_cannot_reset_budget_at_another_output_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            request = request_fixture(Path(temp))
            moved = replace(request, output=Path(temp) / "budget-reset-attempt")
            with mock.patch.object(execution, "execute_case") as native, self.assertRaisesRegex(ValueError, "cannot reset"):
                execution.run_campaign(moved)
            native.assert_not_called()
            self.assertFalse(moved.output.exists())

    def test_partial_resume_replays_prior_evidence_before_any_new_launch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = request_fixture(root)
            def native(_case, _request, arm, directory, stop):
                directory.mkdir(parents=True)
                shutil.copytree(root / arm, directory / "evidence")
                shutil.copyfile(root / arm / "report.json", directory / "report.json")
                stop.set()
                return 0
            with mock.patch.object(execution, "execute_case", side_effect=native), mock.patch.object(execution, "_global_lease"), self.assertRaisesRegex(ValueError, "interrupted"):
                execution.run_campaign(request)
            (root / "baseline/1.jsonl").write_bytes(b"corrupt retained stream")
            with mock.patch.object(execution, "execute_case") as dispatch, mock.patch.object(execution, "_global_lease"), self.assertRaises(ValueError):
                execution.run_campaign(request)
            dispatch.assert_not_called()

    def test_48_trial_pilot_replays_both_hosts_and_rejects_timing_or_ledger_forgery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pilot_fixture(root)
            profile = execution.qualify_pilot(root)
            self.assertEqual(profile.trial_count, 48)
            self.assertEqual(profile.parallel_seconds, 40)
            self.assertEqual(profile.serial_seconds, 80)
            timing_path = root / "serial.timing.json"
            timing = comparison.read_json(timing_path)
            for key, value in (("elapsed_seconds", 800), ("resumed", True), ("workers", True)):
                with self.subTest(key=key):
                    timing_path.write_text(json.dumps({**timing, key: value}))
                    with self.assertRaises(ValueError):
                        execution.qualify_pilot(root)
            timing_path.write_text(json.dumps(timing))
            ledger = comparison.read_json(root / "ledger.json")
            ledger["launches"][0]["completed_at"] += 1
            (root / "ledger.json").write_text(json.dumps(ledger))
            with self.assertRaisesRegex(ValueError, "authoritative"):
                execution.qualify_pilot(root)

    def test_pilot_resumes_after_completed_serial_without_relaunching_it(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, approval = pilot_fixture(root)
            with sqlite3.connect(root / "ledger.sqlite3") as connection:
                connection.execute("DELETE FROM launches WHERE arm='two-worker:candidate'")
            for name in ("two-worker.timing.json", "two-worker-candidate.index.json", "ledger.json"):
                (root / name).unlink()
            shutil.rmtree(root / "two-worker")
            request = execution.CampaignRequest(manifest, approval, 48, root / "inventory.json", {"candidate": root / "candidate-description.txt"}, root)
            calls = []
            fixture_lock = threading.Lock()
            def native(case, _request, arm, directory, _stop):
                with fixture_lock:
                    calls.append((arm, case["case_id"]))
                    directory.mkdir(parents=True)
                    fixture_module().evidence_fixture(directory, host=case["host"], entry_override=case, selected_pattern=(case["should_trigger"],) * 3)
                    shutil.copytree(directory / "candidate", directory / "evidence")
                    shutil.copyfile(directory / "candidate/report.json", directory / "report.json")
                return 0
            with mock.patch.object(execution, "execute_case", side_effect=native), mock.patch.object(execution, "_global_lease"):
                result = execution.run_campaign(request)
            self.assertTrue(result["complete"])
            self.assertEqual(len(calls), 8)
            self.assertEqual(comparison.read_json(root / "serial.timing.json")["started_at"], 1000)
            self.assertEqual(comparison.read_json(root / "ledger.json")["reserved_launches"], 48)


def pilot_fixture(root):
    module = fixture_module()
    inventory = comparison.read_json(ROOT / "layer2-trigger/case-inventory.json")
    active = {row["case_id"]: row for row in inventory["active"]}
    roster = [{key: active[identity][key] for key in ("case_id", "host", "skill", "query", "should_trigger")} for identity in inventory["pilot_case_ids"]]
    inventory_path = root / "inventory.json"
    inventory_path.write_bytes((ROOT / "layer2-trigger/case-inventory.json").read_bytes())
    description = root / "candidate-description.txt"
    description.write_text("candidate no-op description")
    manifest = {**module.minimal_manifest(), "qualification_scope": "pilot", "arms": ["candidate"], "roster": roster, "output_directory": str(root.resolve()),
        "corpus_sha256": comparison.json_digest(roster), "inventory_sha256": hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        "identities": comparison.snapshot_identities(comparison.measurement_snapshot()),
        "pins": {"claude": {"model": "claude-sonnet-test", "cli_version": "test"}, "codex": {"model": "gpt-5.6-sol", "cli_version": "test"}}}
    manifest["controlled_difference"]["candidate_sha256"] = hashlib.sha256(description.read_bytes()).hexdigest()
    digest = comparison.json_digest(manifest)
    approval = {"schema_version": "trigger-campaign-approval/v1", "manifest_sha256": digest, "launch_budget": 48,
        "source": {"role": "user", "message_id": "synthetic-pilot-approval", "content": f"Approve trigger campaign {digest} with launch budget 48."}}
    (root / "manifest.json").write_text(json.dumps(manifest))
    (root / "approval.json").write_text(json.dumps(approval))
    ledger = CampaignLedger(root / "ledger.sqlite3", digest, approval, 48)
    for schedule, workers, start in (("serial", 1, 1000), ("two-worker", 2, 2000)):
        reports = []
        for offset, case in enumerate(roster):
            directory = root / schedule / "candidate" / case["case_id"]
            directory.mkdir(parents=True)
            module.evidence_fixture(directory, host=case["host"], entry_override=case, selected_pattern=(case["should_trigger"],) * 3)
            shutil.copytree(directory / "candidate", directory / "evidence")
            shutil.copyfile(directory / "candidate/report.json", directory / "report.json")
            reports.append(directory / "report.json")
            at = start + (offset // workers) * 10
            with mock.patch.object(accounting.time, "time", return_value=at + 0.1):
                ledger.reserve_case(f"{schedule}:candidate", case["case_id"])
            with mock.patch.object(accounting.time, "time", return_value=at + 9):
                ledger.finish_case(f"{schedule}:candidate", case["case_id"], "complete")
        index = comparison.build_evidence_index(manifest, "candidate", root, reports, inventory_path, description)
        (root / f"{schedule}-candidate.index.json").write_text(json.dumps(index))
        duration = 80 / workers
        (root / f"{schedule}.timing.json").write_text(json.dumps({"manifest_sha256": digest, "schedule": schedule, "workers": workers,
            "started_at": start, "finished_at": start + duration, "monotonic_started": start, "monotonic_finished": start + duration,
            "elapsed_seconds": duration, "calendar_elapsed_seconds": duration, "resumed": False}))
    (root / "ledger.json").write_text(json.dumps(ledger.snapshot()))
    return manifest, approval


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(ExecutionTests), label="test-trigger-campaign-execution"))
