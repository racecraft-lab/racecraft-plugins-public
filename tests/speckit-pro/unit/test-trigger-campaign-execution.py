#!/usr/bin/env python3
"""Mocked dispatch, cancellation, global ceiling and resume contracts; no providers."""
from __future__ import annotations

import importlib.util
from contextlib import ExitStack, nullcontext
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock
from dataclasses import dataclass, replace

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


def standing_request_fixture(root):
    request = request_fixture(root)
    inventory = comparison.read_json(request.inventory)
    request.manifest["qualification_scope"] = "full"
    request.manifest["roster"] = [
        {key: row[key] for key in ("case_id", "host", "skill", "query", "should_trigger")}
        for row in inventory["active"]
    ]
    request.manifest["corpus_sha256"] = comparison.json_digest(request.manifest["roster"])
    request.manifest["pins"]["codex"] = {"model": "gpt-5.6-sol", "cli_version": "test"}
    approval = runpy.run_path(str(ROOT / "unit/test-trigger-campaign.py"))["standing_approval"](request.manifest)
    return replace(request, approval=approval, launch_budget=1302, workers=1)


def contextual_approval(digest, budget=6, response="approved"):
    session = "execution-session-123"
    request_id = "assistant-request-123"
    response_id = "user-response-456"
    request = f"Approve trigger campaign {digest} with launch budget {budget}."

    def observation(role, message_id, timestamp, ordinal, content):
        return {"role": role, "message_id": message_id, "session_id": session,
                "timestamp": timestamp, "source_ordinal": ordinal, "content": content,
                "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
                "source_line_sha256": hashlib.sha256(f"source:{message_id}:{content}".encode()).hexdigest()}

    return {"schema_version": "trigger-campaign-approval/v2", "manifest_sha256": digest,
            "launch_budget": budget, "recorder_observation": {
                "observer": "trusted-orchestrator", "session_id": session,
                "adjacent_user_visible_message_ids": [request_id, response_id],
                "request": observation("assistant", request_id, "2026-09-14T16:00:00.000Z", 200, request),
                "response": observation("user", response_id, "2026-09-14T16:00:01.000Z", 201, response)}}


def saved_carry_fixture(root):
    output = root / "resume"
    output.mkdir()
    inventory = root / "source-inventory.json"
    inventory.write_bytes(b'{"inventory":true}\n')
    descriptions = {arm: root / f"source-{arm}.txt" for arm in ("baseline", "candidate")}
    for arm, path in descriptions.items():
        path.write_bytes(f"{arm}\n".encode())
    manifest = {"arms": ["baseline", "candidate"], "experiment_id": "resume",
                "qualification_scope": "full", "roster": [{"case_id": "fresh"}]}
    approval = {"schema_version": "trigger-campaign-approval/v4"}
    plan = SimpleNamespace(component_sha256=comparison.json_digest({"bound": True}),
        source_root=root / "old",
        review_root=root / "review", carried_case_ids=("carried",),
        fresh_case_ids=("fresh",), carried_trials=frozenset(),
        fresh_trials=frozenset((arm, "fresh", trial)
                               for arm in manifest["arms"] for trial in (1, 2, 3)))
    request = execution.CampaignRequest(manifest, approval, 6, inventory, descriptions,
                                        output, carry_forward={"bound": True})
    for name, value in {
        "carry-forward-lineage.json": execution._carry_lineage_receipt(request, plan),
        "manifest.json": manifest, "approval.json": approval,
    }.items():
        (output / name).write_bytes(execution._serialized_json(value))
    (output / "inventory.json").write_bytes(inventory.read_bytes())
    for arm, path in descriptions.items():
        (output / f"{arm}-description.txt").write_bytes(path.read_bytes())
    authorization = {"manifest_sha256": comparison.json_digest(manifest),
        "approval_sha256": comparison.json_digest(approval), "launch_budget": 6,
        "carry_forward_sha256": plan.component_sha256}
    connection = sqlite3.connect(output / "ledger.sqlite3")
    connection.execute("CREATE TABLE authorization (id INTEGER PRIMARY KEY, binding TEXT NOT NULL)")
    connection.execute("CREATE TABLE launches (arm TEXT, case_id TEXT, trial INTEGER, status TEXT, reserved_at REAL, completed_at REAL)")
    connection.execute("INSERT INTO authorization VALUES (1, ?)",
                       (json.dumps(authorization, sort_keys=True),))
    connection.commit()
    connection.close()
    return request, plan


def completed_saved_carry_fixture(root):
    request, plan = saved_carry_fixture(root)
    ledger = request.output / "ledger.sqlite3"
    with sqlite3.connect(ledger) as connection:
        connection.executemany(
            "INSERT INTO launches VALUES (?, ?, ?, 'complete', ?, ?)",
            [(f"serial:{arm}", "fresh", trial, 1.0, 2.0)
             for arm in request.manifest["arms"] for trial in (1, 2, 3)])
    (request.output / "serial.start.json").write_bytes(execution._serialized_json({
        "started_at": 1.0, "monotonic_started": 1.0,
        "manifest_sha256": comparison.json_digest(request.manifest)}))
    for arm in request.manifest["arms"]:
        (request.output / "serial" / arm / "fresh").mkdir(parents=True)
    return request, plan


def assert_v4_run_rejected_unchanged(test, request, plan, lease, *patchers):
    before_lease = lease.read_bytes()
    before_output = {path.relative_to(request.output): path.read_bytes()
                     for path in request.output.rglob("*") if path.is_file()}
    with ExitStack() as stack:
        stack.enter_context(mock.patch.object(execution, "_validate_request",
                                              return_value=[("serial", 1)]))
        stack.enter_context(mock.patch.object(execution, "_validate_carry_forward_request",
                                              return_value=plan))
        stack.enter_context(mock.patch.object(execution, "_global_lease_path",
                                              return_value=lease))
        stack.enter_context(mock.patch.object(accounting, "validate_approval"))
        provider = stack.enter_context(mock.patch.object(
            execution, "execute_case", side_effect=ValueError("provider reached")))
        for patcher in patchers:
            stack.enter_context(patcher)
        with test.assertRaises(ValueError) as failure:
            execution.run_campaign(request)
    provider.assert_not_called()
    test.assertEqual(lease.read_bytes(), before_lease)
    test.assertEqual({path.relative_to(request.output): path.read_bytes()
                      for path in request.output.rglob("*") if path.is_file()}, before_output)
    return failure.exception


@dataclass
class OneShotSqliteSwap:
    ledger: Path
    replacement: Path
    retained: Path
    predicate: object
    connect: object = sqlite3.connect
    calls: int = 0

    def __call__(self, database, *args, **kwargs):
        if self.calls or not self.predicate(database):
            return self.connect(database, *args, **kwargs)
        self.ledger.rename(self.retained)
        self.replacement.rename(self.ledger)
        try:
            connection = self.connect(database, *args, **kwargs)
        finally:
            self.ledger.rename(self.replacement)
            self.retained.rename(self.ledger)
        self.calls += 1
        return connection


def v4_sqlite_swap_fixture(root, *, unknown_original, copy_replacement):
    request, plan = saved_carry_fixture(root)
    ledger = request.output / "ledger.sqlite3"
    replacement = root / "replacement.sqlite3"
    if copy_replacement:
        shutil.copyfile(ledger, replacement)
    else:
        sqlite3.connect(replacement).close()
    if unknown_original:
        with sqlite3.connect(ledger) as connection:
            connection.execute("INSERT INTO launches VALUES (?, ?, ?, ?, ?, ?)",
                               ("serial:baseline", "unknown-case", 1,
                                "unknown", 1.0, None))
    lease = root / "global-lease"
    lease.write_bytes(b'{"schema_version":"trigger-global-lease/v1",'
                      b'"state":"idle","campaign":"prior"}')
    lease.chmod(0o600)
    return request, plan, ledger, replacement, root / "retained.sqlite3", lease


def assert_v4_ledger_path_swap_rejected(test, root):
    request, plan, ledger, replacement, retained, lease = v4_sqlite_swap_fixture(
        root, unknown_original=True, copy_replacement=True)
    swap = OneShotSqliteSwap(ledger, replacement, retained,
        lambda database: isinstance(database, str) and "ledger.sqlite3?mode=ro" in database)
    campaign_ledger = mock.Mock()
    assert_v4_run_rejected_unchanged(test, request, plan, lease,
        mock.patch.object(sqlite3, "connect", side_effect=swap),
        mock.patch.object(execution, "_inspect_global_lease",
                          side_effect=AssertionError("lease inspection reached")),
        mock.patch.object(execution, "CampaignLedger", campaign_ledger))
    test.assertEqual(swap.calls, 0)
    campaign_ledger.assert_not_called()


def assert_v4_late_ledger_replacement_rejected(test, root):
    request, plan = saved_carry_fixture(root)
    ledger, real_validate = request.output / "ledger.sqlite3", execution._validate_saved_publications
    original = ledger.read_bytes()

    def replace_after_validation(*args, **kwargs):
        result = real_validate(*args, **kwargs)
        ledger.write_bytes(original[:512])
        return result

    try:
        with mock.patch.object(execution, "_validate_saved_publications",
                               side_effect=replace_after_validation), \
             test.assertRaisesRegex(ValueError, "changed during admission"):
            execution._inspect_carry_output(request, plan)
    finally:
        ledger.write_bytes(original)


def assert_v4_ledger_file_attacks_rejected(test, root):
    for attack in ("symlink", "special", "truncated"):
        with test.subTest(attack=attack):
            case_root = root / attack
            case_root.mkdir()
            request, plan = saved_carry_fixture(case_root)
            ledger = request.output / "ledger.sqlite3"
            if attack == "symlink":
                retained = case_root / "retained.sqlite3"
                ledger.rename(retained)
                ledger.symlink_to(retained)
            elif attack == "special":
                ledger.unlink()
                os.mkfifo(ledger)
            else:
                ledger.write_bytes(ledger.read_bytes()[:512])
            with test.assertRaises(ValueError):
                execution._inspect_carry_output(request, plan)


def assert_v4_ledger_handoff_swap_rejected(test, root):
    request, plan, ledger, replacement, retained, lease = v4_sqlite_swap_fixture(
        root, unknown_original=False, copy_replacement=False)
    swap = OneShotSqliteSwap(ledger, replacement, retained,
                             lambda database: Path(database) == ledger)
    failure = assert_v4_run_rejected_unchanged(test, request, plan, lease,
        mock.patch.object(sqlite3, "connect", side_effect=swap))
    test.assertEqual(swap.calls, 1, str(failure))


def assert_v4_handoff_input_drift_rejected(test, root):
    for attack in ("manifest", "approval", "inventory"):
        with test.subTest(attack=attack):
            case_root = root / attack
            case_root.mkdir()
            request, plan = saved_carry_fixture(case_root)
            lease = case_root / "global-lease"
            lease.write_bytes(b'{"schema_version":"trigger-global-lease/v1",'
                              b'"state":"idle","campaign":"prior"}')
            lease.chmod(0o600)
            inspect, calls = execution._inspect_carry_output, 0

            def drift_after_under_lease_admission(*args, **kwargs):
                nonlocal calls
                admission = inspect(*args, **kwargs)
                calls += 1
                if calls == 2:
                    if attack == "manifest":
                        request.manifest["experiment_id"] = "changed"
                    elif attack == "approval":
                        request.approval["changed"] = True
                    else:
                        request.inventory.write_bytes(b'{"changed":true}\n')
                return admission

            assert_v4_run_rejected_unchanged(test, request, plan, lease,
                mock.patch.object(execution, "_inspect_carry_output",
                                  side_effect=drift_after_under_lease_admission))
            test.assertEqual(calls, 2)


def assert_v4_admitted_ledger_transactions(test, root):
    request, plan = saved_carry_fixture(root)
    admission = execution._inspect_carry_output(request, plan)
    with mock.patch.object(accounting, "validate_approval"):
        ledger = CampaignLedger(request.output / "ledger.sqlite3",
            comparison.json_digest(request.manifest), request.approval,
            request.launch_budget, carry_forward=request.carry_forward,
            admitted=admission)
    ledger.reserve_case("serial:baseline", "fresh")
    test.assertEqual(ledger.snapshot()["unknown_launches"], 3)
    ledger.finish_case("serial:baseline", "fresh", "complete")
    test.assertEqual(ledger.snapshot()["unknown_launches"], 0)

    changed = root / "byte-drift"
    changed.mkdir()
    request, plan = saved_carry_fixture(changed)
    admission = execution._inspect_carry_output(request, plan)
    with mock.patch.object(accounting, "validate_approval"):
        ledger = CampaignLedger(request.output / "ledger.sqlite3",
            comparison.json_digest(request.manifest), request.approval,
            request.launch_budget, carry_forward=request.carry_forward,
            admitted=admission)
    with sqlite3.connect(ledger.path) as connection:
        connection.execute("CREATE TABLE harmless_byte_drift (value INTEGER)")
    with test.assertRaisesRegex(ValueError, "changed before its writable transaction"):
        ledger.reserve_case("serial:baseline", "fresh")
    test.assertEqual(execution.read_ledger_bytes(ledger.path.read_bytes())[1]["reserved_launches"], 0)


def assert_v4_raw_drift_rejects_before_publication(test, root):
    for complete in (False, True):
        with test.subTest(no_reservation=complete):
            case_root = root / ("complete" if complete else "reservation")
            case_root.mkdir()
            request, plan = (completed_saved_carry_fixture(case_root) if complete
                             else saved_carry_fixture(case_root))
            ledger = request.output / "ledger.sqlite3"
            lease = case_root / "global-lease"
            lease.write_bytes(b'{"schema_version":"trigger-global-lease/v1",'
                              b'"state":"idle","campaign":"prior"}')
            lease.chmod(0o600)
            before_lease = lease.read_bytes()
            drifted_output = None
            campaign_ledger = execution.CampaignLedger

            def construct_then_drift(*args, **kwargs):
                nonlocal drifted_output
                admitted = kwargs["admitted"]
                current = campaign_ledger(*args, **kwargs)
                with sqlite3.connect(ledger) as connection:
                    connection.execute("CREATE TABLE harmless_byte_drift (value INTEGER)")
                drifted_bytes = ledger.read_bytes()
                test.assertNotEqual(drifted_bytes, admitted[2])
                test.assertEqual(execution.read_ledger_bytes(drifted_bytes)[1],
                                 admitted[1])
                drifted_output = {path.relative_to(request.output): path.read_bytes()
                                  for path in request.output.rglob("*") if path.is_file()}
                return current

            failure = None
            with ExitStack() as stack:
                stack.enter_context(mock.patch.object(
                    execution, "_validate_request", return_value=[("serial", 1)]))
                stack.enter_context(mock.patch.object(
                    execution, "_validate_carry_forward_request", return_value=plan))
                stack.enter_context(mock.patch.object(
                    execution, "_global_lease_path", return_value=lease))
                stack.enter_context(mock.patch.object(
                    execution, "CampaignLedger", side_effect=construct_then_drift))
                stack.enter_context(mock.patch.object(accounting, "validate_approval"))
                if complete:
                    stack.enter_context(mock.patch.object(execution, "_validate_prior"))
                    stack.enter_context(mock.patch.object(
                        execution, "_build_schedule_index", return_value={}))
                provider = stack.enter_context(mock.patch.object(execution, "execute_case"))
                try:
                    execution.run_campaign(request)
                except ValueError as exc:
                    failure = exc
            provider.assert_not_called()
            test.assertIsNotNone(drifted_output)
            test.assertEqual(lease.read_bytes(), before_lease)
            test.assertEqual({path.relative_to(request.output): path.read_bytes()
                              for path in request.output.rglob("*") if path.is_file()},
                             drifted_output)
            test.assertIsNotNone(failure)
            test.assertRegex(str(failure), "changed before its writable transaction")


def assert_v4_successful_resume_publication_order(test, root):
    request, plan = saved_carry_fixture(root)
    admission = execution._inspect_carry_output(request, plan)
    with mock.patch.object(accounting, "validate_approval"):
        ledger = CampaignLedger(
            request.output / "ledger.sqlite3", comparison.json_digest(request.manifest),
            request.approval, request.launch_budget, carry_forward=request.carry_forward,
            admitted=admission)
    events = []
    lease = execution._LeaseState(None, lambda: events.append("lease"))
    require_admitted = accounting._require_admitted_connection
    write_json_once = execution.write_json_once

    def observe_admission(connection, budget, authorization, expected, expected_bytes=None):
        result = require_admitted(connection, budget, authorization, expected, expected_bytes)
        if expected_bytes is not None:
            events.append("writable-admission")
        return result

    def observe_write(path, value):
        if path.name == "serial.start.json":
            events.append("serial.start")
        return write_json_once(path, value)

    def provider(*_args):
        events.append("provider")
        test.assertTrue(lease.active)
        test.assertTrue((request.output / "serial.start.json").exists())
        if events.count("provider") == 1:
            test.assertEqual(ledger.snapshot()["reserved_launches"], 3)
        return 0

    with mock.patch.object(accounting, "_require_admitted_connection",
                           side_effect=observe_admission), \
         mock.patch.object(execution, "write_json_once", side_effect=observe_write), \
         mock.patch.object(execution, "execute_case", side_effect=provider), \
         mock.patch.object(execution, "_settle_case", return_value="complete"), \
         mock.patch.object(execution, "_build_schedule_index", return_value={}):
        execution._run_schedule(request, "serial", 1, ledger, threading.Event(), plan,
                                activate_lease=lambda: lease.activate(ledger))
    test.assertEqual(events[:4],
                     ["writable-admission", "lease", "serial.start", "provider"])
    test.assertEqual(ledger.snapshot()["reserved_launches"], 6)


def terminal_reconciliation_fixture(root, *, cleanup_failed=True):
    request = request_fixture(root)
    (root / "manifest.json").write_text(json.dumps(request.manifest))
    (root / "approval.json").write_text(json.dumps(request.approval))
    ledger = CampaignLedger(root / "ledger.sqlite3", comparison.json_digest(request.manifest), request.approval, 6)
    case = request.manifest["roster"][0]
    identity = "serial:baseline"
    ledger.reserve_case(identity, case["case_id"])
    directory = root / "serial" / "baseline" / case["case_id"]
    directory.mkdir(parents=True)
    shutil.copytree(root / "baseline", directory / "evidence")
    shutil.copyfile(root / "baseline/report.json", directory / "report.json")
    (directory / "runner.stdout").write_bytes(b"retained runner output\n")
    (directory / "runner.stderr").write_bytes(b"")
    (directory / "launch.json").write_text(json.dumps({
        "pid": 12345,
        "command": execution.native_command(case, request, "baseline", directory),
        "started_at": 1000.0,
    }))
    (directory / "execution.json").write_text(json.dumps({
        "runner_exit_code": 1 if cleanup_failed else 0, "finished_at": 1001.0, "elapsed_seconds": 1.0,
    }))
    cleanup_path = directory / "evidence/arm-cleanup.json"
    cleanup = comparison.read_json(cleanup_path)
    cleanup["runner_exit_code"] = 1 if cleanup_failed else 0
    cleanup_path.write_text(json.dumps(cleanup))
    trial_paths = sorted((directory / "evidence").glob("*.trial.json"))
    if cleanup_failed:
        for trial_path in trial_paths[1:]:
            number = trial_path.name.removesuffix(".trial.json")
            trial_path.unlink()
            (directory / "evidence" / f"{number}.jsonl").unlink()
            (directory / "evidence" / f"{number}.stderr").unlink()
        trial_paths = trial_paths[:1]
    for trial_path in trial_paths:
        trial = comparison.read_json(trial_path)
        number = trial_path.name.removesuffix(".trial.json")
        trial["stdout_path"] = str((directory / "evidence" / f"{number}.jsonl").resolve())
        trial["stderr_path"] = str((directory / "evidence" / f"{number}.stderr").resolve())
        trial_path.write_text(json.dumps(trial))
    if cleanup_failed:
        trial_path = trial_paths[0]
        trial = comparison.read_json(trial_path)
        trial.update({"cleanup_verified": False, "cleanup_error": "PermissionError: EPERM",
                      "process_error": "PermissionError: EPERM", "trial_valid": False,
                      "qualification_eligible": False, "valid": False})
        trial["checks"]["process"] = False
        trial["checks"]["cleanup"] = False
        trial["checks"]["absence_probe"] = False
        trial_path.write_text(json.dumps(trial))
        report_path = directory / "report.json"
        report = comparison.read_json(report_path)
        report["summary"].update({"complete": False, "passed": 0, "failed": 1,
                                  "qualification_eligible": False})
        report["results"][0]["status"] = "invalid"
        report["results"][0]["selection_evidence"] = [
            {**comparison.read_json(path), "trial_record_path": str(path.resolve()),
             "trial_record_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in trial_paths
        ]
        report_path.write_text(json.dumps(report))
    return request, ledger, identity, case["case_id"], directory


def changed_observer(manifest):
    return {**manifest["identities"], "observer": "f" * 64}


def assert_preflight_rejected(test, root, request, message=None):
    before = sorted(path.relative_to(root) for path in root.rglob("*"))
    expected = test.assertRaisesRegex(ValueError, message) if message else test.assertRaises(ValueError)
    with mock.patch.object(Path, "mkdir", side_effect=AssertionError("output mkdir reached")) as output_mkdir, \
         mock.patch.object(execution, "CampaignLedger", side_effect=AssertionError("ledger reached")) as ledger, \
         mock.patch.object(execution, "_global_lease", side_effect=AssertionError("lease reached")) as lease, \
         mock.patch.object(execution, "execute_case", side_effect=AssertionError("provider reached")) as provider, \
         expected:
        execution.run_campaign(request)
    output_mkdir.assert_not_called()
    ledger.assert_not_called()
    lease.assert_not_called()
    provider.assert_not_called()
    test.assertEqual(sorted(path.relative_to(root) for path in root.rglob("*")), before)


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

    def test_invalid_contextual_approval_fails_before_output_ledger_lease_or_provider(self):
        def malformed_provenance(record):
            record["recorder_observation"]["response"]["content_sha256"] = "0" * 64

        def stale_sequence(record):
            record["recorder_observation"]["response"]["source_ordinal"] = 199

        def competing_sequence(record):
            record["recorder_observation"]["adjacent_user_visible_message_ids"] = [
                "competing-request", "user-response-456"]

        def denied_response(record):
            response = record["recorder_observation"]["response"]
            response["content"] = "approved, but not yet"
            response["content_sha256"] = hashlib.sha256(response["content"].encode()).hexdigest()

        for label, mutate in (("malformed", malformed_provenance), ("stale", stale_sequence),
                              ("competing", competing_sequence), ("denied", denied_response)):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                request = request_fixture(root)
                request = replace(request, approval=contextual_approval(comparison.json_digest(request.manifest)))
                mutate(request.approval)
                assert_preflight_rejected(self, root, request)

    def test_valid_contextual_approval_passes_normal_request_preflight(self):
        with tempfile.TemporaryDirectory() as temp:
            request = request_fixture(Path(temp))
            request = replace(request, approval=contextual_approval(comparison.json_digest(request.manifest)))
            self.assertEqual(execution._validate_request(request), [("serial", 1)])

    def test_standing_v3_fails_closed_before_output_ledger_lease_or_provider(self):
        for label in ("invalid-approval", "parallel-worker", "different-output"):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                request = standing_request_fixture(root)
                message = None
                if label == "invalid-approval":
                    request.approval["campaign_exercise"]["constraints"]["quota_reset"] = True
                elif label == "parallel-worker":
                    request = replace(request, workers=2)
                    message = "standing campaign authorization requires serial execution"
                else:
                    request = replace(request, output=root / "different-output")
                    message = "bind this exact canonical output directory"
                assert_preflight_rejected(self, root, request, message)

    def test_valid_standing_v3_passes_full_inventory_and_launch_preflight(self):
        with tempfile.TemporaryDirectory() as temp:
            request = standing_request_fixture(Path(temp))
            self.assertEqual(execution._validate_request(request), [("serial", 1)])

    def test_carry_forward_preflight_subtracts_only_the_validated_trial_cohort(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = standing_request_fixture(root)
            component = {"schema_version": "trigger-case-carry-forward/v1",
                         "source": {"source_stability_review": {"sha256": "d" * 64},
                                    "dual_replay": {"path": "dual.json", "sha256": "e" * 64}},
                         "cohort": {}, "compatibility": {"old_observer_sha256": "1" * 64,
                                                           "new_observer_sha256": "2" * 64},
                         "accounting": {}}
            approval = runpy.run_path(str(ROOT / "unit/test-trigger-campaign.py"))["v4_approval"](
                request.manifest, component,
            )
            request = replace(request, approval=approval, launch_budget=891, carry_forward=component)
            carried_cases = [case["case_id"] for case in request.manifest["roster"][:137]]
            plan = mock.Mock(carried_trials=frozenset(("baseline", case, trial)
                                                      for case in carried_cases for trial in (1, 2, 3)))
            with mock.patch.object(execution.carry, "validate_carry_forward", return_value=plan):
                self.assertEqual(execution._validate_request(
                    request, reconciliation_identities=request.manifest["identities"]), [("serial", 1)])

    def test_carry_active_or_unknown_global_lease_rejects_before_any_mutation(self):
        for state in ("active", "unknown"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                lease = root / "lease"
                lease.write_text(json.dumps({"schema_version": "trigger-global-lease/v1",
                                             "state": state, "campaign": "/old"}))
                lease.chmod(0o600)
                request = SimpleNamespace(output=root / "new", manifest={})
                with mock.patch.object(execution, "_validate_request", return_value=[("serial", 1)]), \
                     mock.patch.object(execution, "_validate_carry_forward_request", return_value=mock.Mock()), \
                     mock.patch.object(execution, "_global_lease_path", return_value=lease), \
                     mock.patch.object(execution, "CampaignLedger", side_effect=AssertionError("ledger")) as ledger, \
                     mock.patch.object(execution, "execute_case", side_effect=AssertionError("provider")) as provider, \
                     self.assertRaisesRegex(ValueError, "reconciliation"):
                    execution.run_campaign(request)
                ledger.assert_not_called()
                provider.assert_not_called()
                self.assertFalse(request.output.exists())

    def test_legacy_predispatch_failure_retains_base_interrupted_snapshot_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            request = request_fixture(Path(temp))
            with mock.patch.object(execution, "_global_lease",
                                   return_value=nullcontext(execution._LeaseState(None))), \
                 mock.patch.object(execution, "_run_schedule", side_effect=ValueError("pre-dispatch stop")), \
                 self.assertRaisesRegex(ValueError, "pre-dispatch stop"):
                execution.run_campaign(request)
            snapshots = list(request.output.glob("interrupted-ledger-*.json"))
            self.assertEqual(len(snapshots), 1)
            self.assertEqual(comparison.read_json(snapshots[0])["reserved_launches"], 0)

    def test_same_approval_cannot_reset_budget_at_another_output_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            request = request_fixture(Path(temp))
            moved = replace(request, output=Path(temp) / "budget-reset-attempt")
            with mock.patch.object(execution, "execute_case") as native, self.assertRaisesRegex(ValueError, "cannot reset"):
                execution.run_campaign(moved)
            native.assert_not_called()
            self.assertFalse(moved.output.exists())

    def test_timeout_override_refused_before_ledger_or_native_launch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = replace(request_fixture(root), timeout=181)
            self.assertNotEqual(execution.concurrency_binding(request.manifest),
                                execution.concurrency_binding({**request.manifest, "trial_timeout_seconds": 181}))
            before = sorted(path.relative_to(root) for path in root.rglob("*"))
            with mock.patch.object(execution, "execute_case") as native, \
                 mock.patch.object(execution, "_global_lease", side_effect=AssertionError("lease reached")) as lease, \
                 self.assertRaisesRegex(ValueError, "timeout"):
                execution.run_campaign(request)
            native.assert_not_called()
            lease.assert_not_called()
            self.assertEqual(sorted(path.relative_to(root) for path in root.rglob("*")), before)

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

class MultiGenerationAdmissionTests(unittest.TestCase):
    def test_v5_candidate_only_budget_is_not_reduced_by_historical_baseline(self):
        with tempfile.TemporaryDirectory() as temp:
            request = standing_request_fixture(Path(temp))
            manifest = {**request.manifest, "arms": ["candidate"]}
            request = replace(request, manifest=manifest,
                              approval={"schema_version": "trigger-campaign-approval/v5"},
                              launch_budget=651, carry_forward={"schema_version":
                                                               execution.carry.MULTI_GENERATION_SCHEMA_VERSION})
            plan = SimpleNamespace(
                histories=(SimpleNamespace(
                    lease_path=execution._global_lease_path().resolve()),),
                carried_trials=frozenset(("baseline", row["case_id"], trial)
                                          for row in manifest["roster"] for trial in (1, 2, 3)),
                fresh_trials=frozenset(("candidate", row["case_id"], trial)
                                        for row in manifest["roster"] for trial in (1, 2, 3)))
            with mock.patch.object(execution, "validate_approval"), \
                 mock.patch.object(execution.carry, "validate_multi_generation_carry_forward",
                                   return_value=plan):
                self.assertEqual(execution._validate_request(
                    request, reconciliation_identities=manifest["identities"]), [("serial", 1)])

    def test_v5_rejects_a_history_bound_to_a_different_global_lease(self):
        with tempfile.TemporaryDirectory() as temp:
            request = standing_request_fixture(Path(temp))
            request = replace(
                request,
                approval={"schema_version": "trigger-campaign-approval/v5"},
                carry_forward={"schema_version": execution.carry.MULTI_GENERATION_SCHEMA_VERSION},
            )
            plan = SimpleNamespace(histories=(SimpleNamespace(
                lease_path=(Path(temp) / "other.lock").resolve()),))
            with mock.patch.object(execution.carry, "validate_multi_generation_carry_forward",
                                   return_value=plan), \
                 self.assertRaisesRegex(ValueError, "exact global lease"):
                execution._validate_carry_forward_request(request, request.manifest)

    def test_v5_rejects_any_preexisting_destination_without_relaxing_v4_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            output = root / "v5-output"
            output.mkdir()
            request = SimpleNamespace(output=output)
            plan = execution.carry.MultiGenerationPlan(
                {}, "a" * 64, {}, tuple(), tuple(), frozenset(), frozenset(),
                frozenset(), frozenset(), {}, 651, 660, 1311)
            before = list(output.iterdir())
            with self.assertRaisesRegex(ValueError, "fresh absent"):
                execution._inspect_carry_output(request, plan)
            self.assertEqual(list(output.iterdir()), before)

            v4_request, v4_plan = saved_carry_fixture(root)
            execution._inspect_carry_output(v4_request, v4_plan)

    def test_v5_publication_uses_lineage_v2_and_full_logical_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            output = root / "fresh"
            logical = {"experiment_id": "logical", "arms": ["baseline", "candidate"]}
            component = {"schema_version": execution.carry.MULTI_GENERATION_SCHEMA_VERSION,
                         "accounting": {"historical_charged_launches": 660}}
            segment = SimpleNamespace(generation_id="original")
            plan = execution.carry.MultiGenerationPlan(
                component, comparison.json_digest(component), logical, (segment,), tuple(),
                frozenset(), frozenset(), frozenset(), frozenset(), {}, 651, 660, 1311)
            request = SimpleNamespace(output=output, manifest={"arms": ["candidate"]},
                                      approval={"schema_version": "trigger-campaign-approval/v5"})
            execution._publish_carry_request(request, plan)
            self.assertEqual({path.name for path in output.iterdir()},
                             {"carry-forward-lineage.json", "logical-manifest.json"})
            self.assertEqual(comparison.read_json(output / "logical-manifest.json"), logical)
            self.assertEqual(comparison.read_json(
                output / "carry-forward-lineage.json")["schema_version"],
                "trigger-carry-forward-lineage/v2")


class CarryForwardAdmissionTests(unittest.TestCase):
    def test_legacy_prior_validation_failure_retains_one_interrupted_snapshot_for_v1_v2_v3(self):
        for version in ("v1", "v2", "v3"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                request = standing_request_fixture(root) if version == "v3" else request_fixture(root)
                if version == "v2":
                    request = replace(request, approval=contextual_approval(
                        comparison.json_digest(request.manifest)))
                with mock.patch.object(execution, "_global_lease",
                                       return_value=nullcontext(execution._LeaseState(None))), \
                     mock.patch.object(execution, "_validate_prior",
                                       side_effect=ValueError("prior evidence rejected")), \
                     mock.patch.object(execution, "execute_case",
                                       side_effect=AssertionError("provider")), \
                     self.assertRaisesRegex(ValueError, "prior evidence rejected"):
                    execution.run_campaign(request)
                snapshots = list(request.output.glob("interrupted-ledger-*.json"))
                self.assertEqual(len(snapshots), 1)
                self.assertEqual(comparison.read_json(snapshots[0])["reserved_launches"], 0)

    def test_v4_partial_output_rejects_before_touching_stand_in_lease(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = replace(request_fixture(root), output=root / "partial")
            request.output.mkdir()
            lease = root / "global-lease"
            lease.write_bytes(b'{"state":"idle","campaign":"prior"}')
            before = lease.read_bytes()
            plan = SimpleNamespace(component_sha256="a" * 64,
                                   carried_trials=frozenset(), fresh_trials=frozenset())
            with mock.patch.object(execution, "_validate_request", return_value=[("serial", 1)]), \
                 mock.patch.object(execution, "_validate_carry_forward_request", return_value=plan), \
                 mock.patch.object(execution, "_global_lease_path", return_value=lease), \
                 mock.patch.object(execution, "_inspect_global_lease",
                                   side_effect=AssertionError("lease inspection reached")), \
                 mock.patch.object(execution, "_global_lease",
                                   side_effect=AssertionError("lease mutation reached")), \
                 mock.patch.object(execution, "CampaignLedger",
                                   side_effect=AssertionError("ledger mutation reached")), \
                 self.assertRaisesRegex(ValueError, "partial carry-forward publication"):
                execution.run_campaign(request)
            self.assertEqual(lease.read_bytes(), before)
            self.assertEqual(list(request.output.iterdir()), [])

    def test_v4_complete_saved_resume_state_passes_read_only_admission(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            request, plan = saved_carry_fixture(root)
            before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in request.output.iterdir()}
            execution._inspect_carry_output(request, plan)
            after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in request.output.iterdir()}
            self.assertEqual(after, before)

    def test_v4_ledger_path_swap_at_sqlite_open_rejects_exact_secure_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            assert_v4_ledger_path_swap_rejected(self, Path(temp).resolve())

    def test_v4_ledger_replacement_after_byte_inspection_rejects_before_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            assert_v4_late_ledger_replacement_rejected(self, Path(temp).resolve())

    def test_v4_ledger_symlink_special_and_truncated_files_reject(self):
        with tempfile.TemporaryDirectory() as temp:
            assert_v4_ledger_file_attacks_rejected(self, Path(temp).resolve())

    def test_v4_admission_to_first_writable_transaction_handoff(self):
        checks = (assert_v4_ledger_handoff_swap_rejected,
                  assert_v4_handoff_input_drift_rejected,
                  assert_v4_admitted_ledger_transactions,
                  assert_v4_raw_drift_rejects_before_publication,
                  assert_v4_successful_resume_publication_order)
        for check in checks:
            with self.subTest(check=check.__name__), tempfile.TemporaryDirectory() as temp:
                check(self, Path(temp).resolve())

    def test_v4_auxiliary_artifact_matrix_rejects_read_only_before_lease(self):
        attacks = ("malformed_start", "wrong_start_manifest", "symlink_start", "unsafe_serial",
                   "malformed_timing", "malformed_baseline_index", "malformed_final_ledger")
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as temp:
                root = Path(temp).resolve()
                request, plan = saved_carry_fixture(root)
                if attack == "malformed_start":
                    (request.output / "serial.start.json").write_bytes(b"{")
                elif attack == "wrong_start_manifest":
                    (request.output / "serial.start.json").write_bytes(execution._serialized_json({
                        "started_at": 1.0, "monotonic_started": 1.0,
                        "manifest_sha256": "0" * 64}))
                elif attack == "symlink_start":
                    outside = root / "outside.json"
                    outside.write_bytes(b"{}")
                    (request.output / "serial.start.json").symlink_to(outside)
                elif attack == "unsafe_serial":
                    outside = root / "outside"
                    outside.mkdir()
                    (request.output / "serial").symlink_to(outside, target_is_directory=True)
                elif attack == "malformed_timing":
                    (request.output / "serial.timing.json").write_bytes(b"{")
                elif attack == "malformed_baseline_index":
                    (request.output / "serial-baseline.index.json").write_bytes(b"{")
                else:
                    (request.output / "ledger.json").write_bytes(b"{")
                lease = root / "global-lease"
                lease.write_bytes(b'{"schema_version":"trigger-global-lease/v1",'
                                  b'"state":"idle","campaign":"prior"}')
                before_lease = lease.read_bytes()
                before_output = sorted((path.relative_to(request.output).as_posix(),
                    "symlink" if path.is_symlink() else hashlib.sha256(path.read_bytes()).hexdigest())
                    for path in request.output.rglob("*") if not path.is_dir())
                with mock.patch.object(execution, "_validate_request", return_value=[("serial", 1)]), \
                     mock.patch.object(execution, "_validate_carry_forward_request", return_value=plan), \
                     mock.patch.object(execution, "_global_lease_path", return_value=lease), \
                     mock.patch.object(execution, "_inspect_global_lease",
                                       side_effect=AssertionError("lease inspection reached")), \
                     mock.patch.object(execution, "CampaignLedger") as ledger, \
                     mock.patch.object(execution, "execute_case") as provider, \
                     self.assertRaises(ValueError):
                    execution.run_campaign(request)
                ledger.assert_not_called()
                provider.assert_not_called()
                self.assertEqual(lease.read_bytes(), before_lease)
                after_output = sorted((path.relative_to(request.output).as_posix(),
                    "symlink" if path.is_symlink() else hashlib.sha256(path.read_bytes()).hexdigest())
                    for path in request.output.rglob("*") if not path.is_dir())
                self.assertEqual(after_output, before_output)


class TerminalReconciliationTests(unittest.TestCase):
    def test_clean_unknown_reconciliation_preserves_original_completion_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request, _ledger, _identity, _case_id, directory = terminal_reconciliation_fixture(
                root, cleanup_failed=False)
            with mock.patch.object(execution.os, "kill", side_effect=ProcessLookupError), \
                 mock.patch.object(execution.os, "killpg", side_effect=ProcessLookupError), \
                 mock.patch.object(execution, "_global_lease"), \
                 mock.patch.object(execution, "execute_case") as provider:
                result = execution.reconcile_campaign(request)
            provider.assert_not_called()
            self.assertEqual(result["ledger"]["unknown_launches"], 0)
            self.assertEqual({row["status"] for row in result["ledger"]["launches"]}, {"complete"})
            self.assertFalse((directory / "evidence/terminal-reconciliation.json").exists())

    def test_terminal_reconciliation_allows_only_observer_change_and_charges_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request, _ledger, identity, case_id, directory = terminal_reconciliation_fixture(root)
            protected = {
                path.relative_to(directory): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in directory.rglob("*") if path.is_file()
            }
            current = changed_observer(request.manifest)
            with mock.patch.object(comparison, "snapshot_identities", return_value=current), \
                 mock.patch.object(execution.os, "kill", side_effect=ProcessLookupError) as pid_probe, \
                 mock.patch.object(execution.os, "killpg", side_effect=ProcessLookupError) as group_probe, \
                 mock.patch.object(execution, "_global_lease"), \
                 mock.patch.object(execution, "execute_case") as provider:
                result = execution.reconcile_campaign(request)
            provider.assert_not_called()
            self.assertTrue(result["reconciled"])
            self.assertEqual(result["native_launches"], 0)
            self.assertEqual(result["ledger"]["reserved_launches"], 3)
            self.assertEqual(result["ledger"]["unknown_launches"], 0)
            self.assertEqual({row["status"] for row in result["ledger"]["launches"]}, {"invalid"})
            self.assertTrue(all(call.args[1] == 0 for call in pid_probe.call_args_list + group_probe.call_args_list))
            receipt_path = directory / "evidence/terminal-reconciliation.json"
            receipt = comparison.read_json(receipt_path)
            self.assertEqual(receipt["schema_version"], "trigger-terminal-reconciliation/v1")
            self.assertEqual((receipt["arm"], receipt["case_id"]), (identity, case_id))
            self.assertEqual(receipt["terminal_status"], "invalid")
            self.assertEqual(receipt["native_launches"], 0)
            self.assertEqual(receipt["historical_observer"], request.manifest["identities"]["observer"])
            self.assertEqual(receipt["current_observer"], current["observer"])
            self.assertEqual({item["signal"] for item in receipt["absence_observations"]
                              if item["kind"] in {"pid", "pgid"}}, {0})
            self.assertEqual({item["outcome"] for item in receipt["absence_observations"]}, {"absent"})
            self.assertEqual(
                protected,
                {path.relative_to(directory): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in directory.rglob("*")
                 if path.is_file() and path != receipt_path},
            )
            self.assertFalse(comparison.read_json(sorted((directory / "evidence").glob("*.trial.json"))[0])["trial_valid"])
            with mock.patch.object(comparison, "snapshot_identities", return_value=current), \
                 mock.patch.object(execution, "execute_case") as provider, \
                 self.assertRaisesRegex(ValueError, "frozen public inputs"):
                execution.run_campaign(request)
            provider.assert_not_called()
            with mock.patch.object(execution, "execute_case") as provider, \
                 self.assertRaisesRegex(ValueError, "prior invalid native results"):
                execution.run_campaign(request)
            provider.assert_not_called()

    def test_terminal_reconciliation_replay_is_idempotent_and_receipt_is_immutable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request, _ledger, _identity, _case_id, directory = terminal_reconciliation_fixture(root)
            probes = (mock.patch.object(execution.os, "kill", side_effect=ProcessLookupError),
                      mock.patch.object(execution.os, "killpg", side_effect=ProcessLookupError))
            with probes[0], probes[1], mock.patch.object(execution, "_global_lease"):
                first = execution.reconcile_campaign(request)
                receipt_path = directory / "evidence/terminal-reconciliation.json"
                digest = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
                second = execution.reconcile_campaign(request)
            self.assertEqual(first["ledger"], second["ledger"])
            self.assertEqual(hashlib.sha256(receipt_path.read_bytes()).hexdigest(), digest)
            receipt = comparison.read_json(receipt_path)
            receipt["native_launches"] = 1
            receipt_path.write_text(json.dumps(receipt))
            with mock.patch.object(execution.os, "kill", side_effect=ProcessLookupError), \
                 mock.patch.object(execution.os, "killpg", side_effect=ProcessLookupError), \
                 mock.patch.object(execution, "_global_lease"), \
                 self.assertRaises(ValueError):
                execution.reconcile_campaign(request)

    def test_terminal_reconciliation_rejects_missing_mutated_or_empty_evidence(self):
        def missing_execution(_request, _directory):
            (_directory / "execution.json").unlink()

        def contradictory_cleanup(_request, directory):
            path = directory / "evidence/arm-cleanup.json"
            record = comparison.read_json(path)
            record["runner_exit_code"] = 0
            path.write_text(json.dumps(record))

        def mutated_report(_request, directory):
            path = directory / "report.json"
            record = comparison.read_json(path)
            record["results"][0]["case_id"] = "l2-wrong-case"
            path.write_text(json.dumps(record))

        def mutated_raw(_request, directory):
            sorted((directory / "evidence").glob("*.jsonl"))[0].write_bytes(b"mutated")

        def empty_trials(_request, directory):
            for path in (directory / "evidence").glob("*.trial.json"):
                path.unlink()

        def mutated_manifest(request, _directory):
            path = request.output / "manifest.json"
            record = comparison.read_json(path)
            record["experiment_id"] = "another-experiment"
            path.write_text(json.dumps(record))

        def mutated_approval(request, _directory):
            path = request.output / "approval.json"
            record = comparison.read_json(path)
            record["source"]["message_id"] = "different-approval"
            path.write_text(json.dumps(record))

        def mutated_inventory(request, _directory):
            (request.output / "inventory.json").write_bytes(b"{}")

        def mutated_description(request, _directory):
            (request.output / "baseline-description.txt").write_text("changed")

        def malformed_execution(_request, directory):
            path = directory / "execution.json"
            record = comparison.read_json(path)
            record["runner_exit_code"] = "1"
            path.write_text(json.dumps(record))

        for label, mutate in (("missing execution", missing_execution),
                              ("contradictory cleanup", contradictory_cleanup),
                              ("mutated report", mutated_report), ("mutated raw", mutated_raw),
                              ("empty trials", empty_trials), ("mutated manifest", mutated_manifest),
                              ("mutated approval", mutated_approval), ("mutated inventory", mutated_inventory),
                              ("mutated description", mutated_description),
                              ("malformed execution", malformed_execution)):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                request, ledger, _identity, _case_id, directory = terminal_reconciliation_fixture(root)
                mutate(request, directory)
                with mock.patch.object(execution.os, "kill", side_effect=ProcessLookupError), \
                     mock.patch.object(execution.os, "killpg", side_effect=ProcessLookupError), \
                     mock.patch.object(execution, "_global_lease"), \
                     mock.patch.object(execution, "execute_case") as provider, \
                     self.assertRaises((ValueError, FileNotFoundError, KeyError, json.JSONDecodeError)):
                    execution.reconcile_campaign(request)
                provider.assert_not_called()
                self.assertEqual(ledger.snapshot()["unknown_launches"], 3)

    def test_terminal_reconciliation_rejects_non_observer_snapshot_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request, ledger, _identity, _case_id, directory = terminal_reconciliation_fixture(root)
            current = {**changed_observer(request.manifest), "catalog": "e" * 64}
            with mock.patch.object(comparison, "snapshot_identities", return_value=current), \
                 mock.patch.object(execution.os, "kill", side_effect=AssertionError("process probe reached")), \
                 mock.patch.object(execution.os, "killpg", side_effect=AssertionError("group probe reached")), \
                 mock.patch.object(execution, "_global_lease", side_effect=AssertionError("lease reached")), \
                 self.assertRaisesRegex(ValueError, "other than the observer"):
                execution.reconcile_campaign(request)
            self.assertEqual(ledger.snapshot()["unknown_launches"], 3)
            self.assertFalse((directory / "evidence/terminal-reconciliation.json").exists())

    def test_terminal_reconciliation_rejects_live_denied_or_remaining_ownership(self):
        scenarios = (
            ("live pid", None, ProcessLookupError(), False),
            ("denied pid", PermissionError(1, "denied"), ProcessLookupError(), False),
            ("live pgid", ProcessLookupError(), None, False),
            ("denied pgid", ProcessLookupError(), PermissionError(1, "denied"), False),
            ("remaining workspace", ProcessLookupError(), ProcessLookupError(), True),
        )
        for label, pid_result, group_result, workspace_remains in scenarios:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                request, ledger, _identity, _case_id, directory = terminal_reconciliation_fixture(root)
                if workspace_remains:
                    Path(comparison.read_json(directory / "evidence/arm-cleanup.json")["workspace"]).mkdir()
                pid_effect = pid_result if isinstance(pid_result, BaseException) else None
                group_effect = group_result if isinstance(group_result, BaseException) else None
                with mock.patch.object(execution.os, "kill", side_effect=pid_effect, return_value=pid_result), \
                     mock.patch.object(execution.os, "killpg", side_effect=group_effect, return_value=group_result), \
                     mock.patch.object(execution, "_global_lease"), \
                     self.assertRaises((ValueError, PermissionError)):
                    execution.reconcile_campaign(request)
                self.assertEqual(ledger.snapshot()["unknown_launches"], 3)
                self.assertFalse((directory / "evidence/terminal-reconciliation.json").exists())

class PilotExecutionTests(unittest.TestCase):
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
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]), label="test-trigger-campaign-execution"))
