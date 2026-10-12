#!/usr/bin/env python3
"""Compact root answers through the public request/dispatch seam."""
from __future__ import annotations

import json
import subprocess
import tempfile
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "speckit-pro"))
sys.path.insert(0, str(REPO / "tests/speckit-pro/lib"))
from speckit_pro_runner.envelope import parse_request, response  # noqa: E402
from speckit_pro_runner.runtime import handle_request  # noqa: E402
from speckit_pro_runner.helpers.registry import HELPERS, MUTATION_HELPERS  # noqa: E402
from test_result import run_counted  # noqa: E402


class CompactAnswerTests(unittest.TestCase):
    def request(self, helper: str, **fields: object):
        entry = (HELPERS | MUTATION_HELPERS)[helper]
        raw = {"schema_version": "1.0", "helper_id": helper, "operation": entry.operation,
               "mode": "read_only", "inputs": {}, "answer_format": "compact", **fields}
        request, error = parse_request(json.dumps(raw))
        self.assertIsNone(error)
        return request

    def test_every_registered_helper_has_a_bounded_root_answer(self):
        for helper in HELPERS | MUTATION_HELPERS:
            with self.subTest(helper=helper):
                request = self.request(helper)
                result = handle_request(request)
                self.assertLessEqual(len(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()) + 1, 16384)
                self.assertTrue(result["next_action"])
                self.assertIn(result["status"], ("ok", "input_error", "missing_prerequisite", "internal_failure", "expected_failure", "subprocess_failure"))

    def test_small_success_preserves_decision_and_removes_duplicate_transport(self):
        body = response("ok", data={"stdout_json": {"action": "stop", "count": 3},
                                   "stdout": {"text": "duplicate", "truncated": False}, "stdin_request": {"ignored": True}})
        with patch("speckit_pro_runner.helpers.registry.dispatch_helper", return_value=body):
            result = handle_request(self.request("count-markers"))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["next_action"], "stop")
        self.assertEqual(result["data"]["stdout_json"], {"action": "stop", "count": 3})
        self.assertNotIn("stdout", result["data"])
        self.assertNotIn("stdin_request", result["data"])
        self.assertIn("stdout", body["data"], "compact projection must not mutate detailed evidence")

    def test_over_cap_fixture_fails_without_leaking_or_repeating_a_mutation(self):
        body = response("ok", data={"evidence": "private fixture text " * 2000})
        with patch("speckit_pro_runner.helpers.registry.dispatch_helper", return_value=body) as dispatch:
            result = handle_request(self.request("count-markers", mode="apply", request_id="r" * 20000))
        dispatch.assert_called_once()
        self.assertEqual(result["status"], "internal_failure")
        self.assertEqual(result["exit_code"], 5)
        self.assertEqual(result["diagnostics"][0]["code"], "compact_answer_overflow")
        self.assertEqual(result["data"]["helper_status"], "ok")
        self.assertIn("without repeating", result["next_action"])
        self.assertNotIn("private fixture text", json.dumps(result))
        self.assertLessEqual(len(json.dumps(result).encode()), 16384)

    def test_failures_keep_their_status_and_remediation(self):
        for status in ("expected_failure", "input_error", "missing_prerequisite", "subprocess_failure", "internal_failure"):
            body = response(status, diagnostics=[{"code": "fixture", "remediation": {"actions": ["Repair the fixture."]}}])
            with self.subTest(status=status), patch("speckit_pro_runner.helpers.registry.dispatch_helper", return_value=body):
                result = handle_request(self.request("count-markers"))
                self.assertEqual(result["status"], status)
                self.assertEqual(result["exit_code"], body["exit_code"])
                self.assertEqual(result["next_action"], "Repair the fixture.")

    def test_detailed_phase_consumer_keeps_full_evidence(self):
        body = response("ok", data={"text": "x" * 20000})
        with patch("speckit_pro_runner.helpers.registry.dispatch_helper", return_value=body):
            result = handle_request(self.request("count-markers", answer_format="detailed"))
        self.assertEqual(result, body)


class CompactLauncherTests(unittest.TestCase):
    def test_source_and_both_host_launchers_return_compact_decisions(self):
        raw = {"schema_version": "1.0", "helper_id": "count-markers", "operation": "count-markers",
               "mode": "read_only", "answer_format": "compact",
               "inputs": {"type": "all", "feature_dir": "tests/speckit-pro/unit/fixtures/read-only-helpers/read-only-helper-feature"}}
        decisions = []
        for relative in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            command = [sys.executable, str(REPO / relative / "scripts/run-speckit-pro.py")]
            done = subprocess.run(command, input=json.dumps(raw), capture_output=True, text=True,
                                  cwd=REPO, check=False, timeout=30)
            with self.subTest(payload=relative):
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertLessEqual(len(done.stdout.encode()) + len(done.stderr.encode()), 16384)
                answer = json.loads(done.stdout)
                self.assertEqual(answer["status"], "ok")
                self.assertTrue(answer["next_action"])
                decisions.append(answer["data"]["stdout_json"])
        self.assertEqual(len(decisions), 3)
        self.assertEqual(decisions[0], decisions[1])
        self.assertEqual(decisions[0], decisions[2])

    def test_full_sized_tasks_bindings_survive_compact_publish_and_consumption(self):
        text = "# Tasks\n" + "\x00" * (32768 - len("# Tasks\n"))
        for payload in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(binding_payload=payload), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                (root / ".specify").mkdir()
                feature = root / "feature"
                feature.mkdir()
                snapshot = root / "snapshot"
                snapshot.mkdir(mode=0o700)
                (snapshot / "tasks.md").write_text(text, encoding="utf-8")
                identity = feature.stat()
                raw = {"schema_version": "1.0", "helper_id": "publish-tasks-output",
                       "operation": "publish-tasks-output", "mode": "apply", "answer_format": "compact",
                       "inputs": {"feature_dir": "feature", "snapshot_dir": str(snapshot),
                                  "feature_identity": {"device": identity.st_dev, "inode": identity.st_ino}}}
                command = [sys.executable, str(REPO / payload / "scripts/run-speckit-pro.py")]
                published = subprocess.run(command, input=json.dumps(raw), capture_output=True, text=True,
                                           cwd=root, check=False, timeout=30)
                answer = json.loads(published.stdout)
                self.assertEqual(answer["status"], "ok", answer)
                binding = answer["data"]["tasks_binding"]
                self.assertEqual(binding["text"], text)
                self.assertLessEqual(len(published.stdout.encode()) + len(published.stderr.encode()), 212992)
                raw.update(helper_id="read-tasks-output", operation="read-tasks-output", mode="read_only",
                           inputs={"tasks_binding": binding, "live_path": "feature/tasks.md"})
                consumed = subprocess.run(command, input=json.dumps(raw), capture_output=True, text=True,
                                          cwd=root, check=False, timeout=30)
                verified = json.loads(consumed.stdout)
                self.assertEqual(verified["status"], "ok", verified)
                self.assertEqual(verified["data"]["text"], text)
                self.assertTrue(verified["data"]["after_hooks_ready"])
                self.assertLessEqual(len(consumed.stdout.encode()) + len(consumed.stderr.encode()), 212992)


class CompactPlanRepairTests(unittest.TestCase):
    def test_real_sized_plan_repair_preserves_complete_executor_message(self):
        fixtures = REPO / "tests/speckit-pro/unit/fixtures/read-only-helpers"
        raw = json.loads((fixtures / "requests/render-plan-repair-context.json").read_text())
        raw["inputs"]["context_paths"]["source-evidence"] = str(fixtures.relative_to(REPO) / "read-only-helper-feature/plan.md")
        for payload in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            command = [sys.executable, str(REPO / payload / "scripts/run-speckit-pro.py")]
            with self.subTest(repair_payload=payload):
                raw["answer_format"] = "detailed"
                detailed = subprocess.run(command, input=json.dumps(raw), capture_output=True, text=True,
                                          cwd=REPO, check=False, timeout=30)
                evidence = json.loads(detailed.stdout)
                self.assertEqual(evidence["status"], "ok", evidence)
                self.assertGreater(evidence["data"]["stdout_json"]["message_bytes"], 23000)
                raw["answer_format"] = "compact"
                compact = subprocess.run(command, input=json.dumps(raw), capture_output=True, text=True,
                                         cwd=REPO, check=False, timeout=30)
                answer = json.loads(compact.stdout)
                self.assertEqual(answer["status"], "ok", answer)
                self.assertEqual(answer["data"]["stdout_json"], evidence["data"]["stdout_json"])
                self.assertLessEqual(len(compact.stdout.encode()) + len(compact.stderr.encode()), 1196032)
                self.assertTrue(answer["next_action"])


class CompactRequestTests(unittest.TestCase):
    def test_answer_format_rejects_unsupported_values(self):
        for value in (None, [], {}, True, "unbounded"):
            raw = {"schema_version": "1.0", "helper_id": "runner", "operation": "runtime-info",
                   "mode": "read_only", "inputs": {}, "answer_format": value}
            with self.subTest(value=value):
                request, error = parse_request(json.dumps(raw))
                self.assertIsNone(request)
                self.assertEqual(error["status"], "input_error")


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]), label="test-compact-answers"))
