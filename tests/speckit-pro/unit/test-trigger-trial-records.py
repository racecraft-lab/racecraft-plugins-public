#!/usr/bin/env python3
"""Deterministic validity and immutability checks for trigger trial records."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))
from test_result import run_counted  # noqa: E402
import trigger_evidence as evidence  # noqa: E402


class TrialRecordTests(unittest.TestCase):
    def test_execution_and_stream_validity_are_separate(self) -> None:
        execution = {
            "provider_exit_code": 0, "timed_out": False, "interrupted_by_signal": None,
            "cleanup_verified": True, "cleanup_error": None, "cleanup_scope": "owned-process-group",
            "unexpected_descendants": False, "child_pid": 1234, "child_pgid": 1234,
            "cleanup_observations": [{"pgid": 1234, "errno": 3, "elapsed_seconds": 0.01}],
            "process_error": None,
            "launch_contract": {
                "config_isolated": True, "retries_disabled": True,
                "requested_model": "claude-test",
            },
        }
        raw = {"stdout_path": "/evidence/stdout", "stdout_sha256": "a" * 64,
               "stderr_path": "/evidence/stderr", "stderr_sha256": "b" * 64}
        parsed = {
            "valid": True, "selected": False, "model_identity_check": "exact",
            "requested_model": "claude-test", "resolved_model": "claude-test",
            "observation_scope": "claude-native-skill-tool", "reason": "no Skill selection",
        }
        entry = {"query": "A legitimate negative", "should_trigger": False}
        for label, changes in (
            ("good", {}), ("exit", {"provider_exit_code": 7}), ("missing-exit", {"provider_exit_code": None}),
            ("boolean-exit", {"provider_exit_code": False}), ("timeout", {"timed_out": True}),
            ("missing-timeout", {"timed_out": None}), ("signal", {"interrupted_by_signal": 15}),
            ("cleanup", {"cleanup_verified": False}), ("unknown-cleanup", {"cleanup_verified": None}),
            ("lingering", {"unexpected_descendants": True}), ("wrong-scope", {"cleanup_scope": "direct-child-only"}),
            ("missing-probe", {"cleanup_observations": None}), ("empty-probe", {"cleanup_observations": []}),
            ("wrong-group", {"child_pgid": 5678}),
        ):
            with self.subTest(scenario=label):
                record = evidence.make_trial_record("claude", "demo", entry, 1, 1, parsed, raw, {**execution, **changes})
                self.assertTrue(record["stream_valid"])
                self.assertIs(record["trial_valid"], label == "good")
                self.assertIs(record["valid"], record["trial_valid"])
                self.assertEqual(record["provider_exit_code"], changes.get("provider_exit_code", 0))
                self.assertEqual(record["selected"], False)

        codex_without_stdin_isolation = evidence.make_trial_record(
            "codex", "demo", entry, 1, 1, parsed, raw, execution,
        )
        codex_launch = {
            **execution["launch_contract"],
            "stdin_prompt_isolated": True,
            "login_state_source": "CODEX_HOME",
            "shell_home_isolated": True,
            "scratch_directory_isolated": True,
        }
        codex_with_environment_isolation = evidence.make_trial_record(
            "codex",
            "demo",
            entry,
            1,
            1,
            parsed,
            raw,
            {
                **execution,
                "launch_contract": codex_launch,
            },
        )
        self.assertFalse(codex_without_stdin_isolation["trial_valid"])
        self.assertTrue(codex_with_environment_isolation["trial_valid"])
        for field in (
            "stdin_prompt_isolated",
            "login_state_source",
            "shell_home_isolated",
            "scratch_directory_isolated",
        ):
            with self.subTest(missing_codex_launch_field=field):
                incomplete_launch = {**codex_launch}
                incomplete_launch.pop(field)
                record = evidence.make_trial_record(
                    "codex", "demo", entry, 1, 1, parsed, raw,
                    {**execution, "launch_contract": incomplete_launch},
                )
                self.assertFalse(record["trial_valid"])

    def test_case_identity_is_independent_of_position_and_runtime_name(self) -> None:
        entry = {"query": "Use this boundary", "should_trigger": True}
        key = evidence.case_id("claude", "demo", entry)
        self.assertEqual(key, evidence.case_id("claude", "demo", dict(reversed(list(entry.items())))))
        self.assertNotEqual(key, evidence.case_id("claude", "demo", {**entry, "should_trigger": False}))
        self.assertNotEqual(key, evidence.case_id("codex", "demo", entry))
        self.assertNotEqual(key, evidence.case_id("claude", "sibling", entry))

    def test_record_cannot_overwrite_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            record = {"schema_version": "trigger-trial/v2", "case_number": 1, "trial_number": 2, "trial_valid": False}
            retained = evidence.retain_trial_record(root, record)
            path = Path(retained["trial_record_path"])
            self.assertEqual(json.loads(path.read_text()), record)
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                evidence.retain_trial_record(root, {**record, "trial_valid": True})
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(TrialRecordTests), label="test-trigger-trial-records"))
