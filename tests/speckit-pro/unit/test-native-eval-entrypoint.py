#!/usr/bin/env python3
"""Public preview CLI tests for native-evaluation planning."""
from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from test_result import run_counted  # noqa: E402
import uuid


ENTRYPOINT = Path(__file__).resolve().parents[1] / "run-native-evals.py"


def catalog_case(case_id: str = "native.preview") -> dict[str, object]:
    return {
        "id": case_id,
        "layer": "trigger",
        "capability": "Plan a native trial.",
        "requirements": [{"id": "one", "description": "One."}, {"id": "two", "description": "Two."}],
        "prompt": "Perform the trial.",
        "fixtures": [],
        "hosts": {
            "claude": {"skill": "plugin:skill", "allowed_tools": [], "modes": ["plugin"]},
            "codex": {"skill": "skill", "allowed_tools": [], "modes": ["project"]},
        },
        "checks": [
            {"id": "semantic.one", "requirement": "one", "type": "semantic", "rubric": "First rubric."},
            {"id": "semantic.two", "requirement": "two", "type": "semantic", "rubric": "Second rubric."},
        ],
        "native_differences": [],
        "provenance": ["tests/speckit-pro/unit/test-native-eval-entrypoint.py"],
        "timeout_seconds": 60,
        "resource_class": "ordinary",
    }


class NativeEvalEntrypointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.catalog = self.temp / "catalog.json"
        self.catalog.write_text(json.dumps({"schema_version": "native-eval-catalog/v1", "cases": [catalog_case()]}))
        name = "native_entrypoint_test_" + uuid.uuid4().hex
        spec = importlib.util.spec_from_file_location(name, ENTRYPOINT)
        self.module = importlib.util.module_from_spec(spec)
        sys.modules[name] = self.module
        self.addCleanup(sys.modules.pop, name)
        spec.loader.exec_module(self.module)

    def run_entrypoint(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ENTRYPOINT), "--catalog", str(self.catalog), *args],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )

    def test_preview_resolves_numeric_layer_and_counts_shared_judges_once_per_output(self) -> None:
        result = self.run_entrypoint("--layers", "2", "--hosts", "both", "--runs", "2", "--preview")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["unique_cases"], 1)
        self.assertEqual(payload["native_modes"], 2)
        self.assertEqual(payload["subject_trials"], 4)
        self.assertEqual(payload["potential_judge_calls"], 4)
        self.assertEqual(payload["layers"], ["trigger"])

    def test_preview_rejects_non_native_layer_empty_selection_and_invalid_limits(self) -> None:
        for arguments in (
            ("--layers", "1", "--preview"),
            ("--layers", "trigger", "--case-id", "unknown", "--preview"),
            ("--layers", "trigger", "--claude-concurrency", "9", "--preview"),
            ("--layers", "trigger", "--claude-concurrency", "1", "--nested-concurrency", "2", "--preview"),
        ):
            with self.subTest(arguments=arguments):
                result = self.run_entrypoint(*arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")

    def test_execute_returns_runtime_status_and_persists_report(self) -> None:
        output = self.temp / "run-output"
        module = self.module
        report = {"exit_status": 1, "counts": {"behavior_fails": 0},
                  "pair_counts": {"planned": 1, "behavior_fails": 1}, "providers": {}, "limitations": []}
        def execute(*args, **kwargs):
            output.mkdir()
            return report
        with mock.patch.object(module, "run_evaluations", side_effect=execute) as runner, \
                mock.patch.object(module, "NativeJudge") as judge, \
                mock.patch("builtins.print") as printed:
            result = module.main(["--catalog", str(self.catalog), "--layers", "trigger", "--execute", "--output", str(output)])
        self.assertEqual(result, 1)
        runner.assert_called_once()
        self.assertIs(runner.call_args.kwargs["judge_execute"], judge.return_value)
        saved = list((output / "reports").glob("*.json"))
        self.assertEqual(len(saved), 1)
        self.assertEqual(json.loads(saved[0].read_text()), report)
        self.assertEqual(json.loads(printed.call_args.args[0])["pair_counts"], report["pair_counts"])

    def test_existing_output_requires_resume_and_resume_requires_existing_output(self) -> None:
        output = self.temp / "run-output"
        output.mkdir()
        (output / "existing.json").write_text("{}")
        result = self.run_entrypoint("--layers", "trigger", "--execute", "--output", str(output))
        self.assertEqual(result.returncode, 2)
        self.assertIn("--resume", result.stderr)
        result = self.run_entrypoint("--layers", "trigger", "--execute", "--output", str(self.temp / "absent"), "--resume")
        self.assertEqual(result.returncode, 2)
        self.assertIn("existing", result.stderr)

    def test_retry_requires_explicit_resume(self) -> None:
        output = self.temp / "run-output"
        result = self.run_entrypoint(
            "--layers", "trigger", "--execute", "--output", str(output),
            "--retry-case", "native.preview", "--retry-status", "fail",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--resume", result.stderr)
        self.assertFalse(output.exists())

    def judge_fixture(self, *, text='{"result":true}', result=None, tools=(), exit_code=0, cleanup=True):
        def prepare(request, *, attempt_dir, model):
            attempt_dir.mkdir()
            result_path = attempt_dir / "judge-result.json"
            result_path.write_text(text if result is None else result)
            return SimpleNamespace(result_path=result_path)
        events = [{"type": "thread.started", "thread_id": "judge-thread"}, {"type": "turn.started"}]
        events.extend({"type": "item.completed", "item": item} for item in tools)
        events.extend([
            {"type": "item.completed", "item": {"id": "final", "type": "agent_message", "text": text}},
            {"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}},
        ])
        raw = SimpleNamespace(exit_code=exit_code, timed_out=False,
                              process_evidence={"cleanup_verified": cleanup, "cleanup_error": None},
                              raw_trace="\n".join(json.dumps(event) for event in events))
        return prepare, raw

    def test_native_judge_pins_runtime_and_returns_only_verified_native_result(self) -> None:
        prepare, raw = self.judge_fixture()
        with mock.patch.object(self.module, "prepare_judge", side_effect=prepare) as stage, \
                mock.patch.object(self.module, "judge_runtime_compatibility_identity", return_value={"pin": "one"}), \
                mock.patch.object(self.module, "execute_prepared", return_value=raw) as execute:
            judge = self.module.NativeJudge("pinned-model")
            self.assertEqual(judge({}, self.temp, "pinned-model"), '{"result":true}')
            self.assertEqual(judge.runtime_identity["native"], {"pin": "one"})
        self.assertEqual(stage.call_count, 2)
        execute.assert_called_once()

    def test_native_judge_rejects_changed_runtime_before_launch(self) -> None:
        prepare, raw = self.judge_fixture()
        with mock.patch.object(self.module, "prepare_judge", side_effect=prepare), \
                mock.patch.object(self.module, "judge_runtime_compatibility_identity", side_effect=[{"pin": "one"}, {"pin": "two"}]), \
                mock.patch.object(self.module, "execute_prepared", return_value=raw) as execute:
            judge = self.module.NativeJudge("pinned-model")
            with self.assertRaisesRegex(ValueError, "runtime changed"):
                judge({}, self.temp, "pinned-model")
        execute.assert_not_called()

    def test_native_judge_rejects_tools_mismatched_result_and_failed_cleanup(self) -> None:
        controls = [
            {"tools": [{"id": "cmd", "type": "command_execution", "command": "echo unsafe", "status": "completed", "exit_code": 0, "aggregated_output": "unsafe"}]},
            {"result": '{"result":false}'},
            {"cleanup": False},
            {"exit_code": 1},
        ]
        for index, control in enumerate(controls):
            with self.subTest(control=control):
                destination = self.temp / str(index)
                destination.mkdir()
                prepare, raw = self.judge_fixture(**control)
                with mock.patch.object(self.module, "prepare_judge", side_effect=prepare), \
                        mock.patch.object(self.module, "judge_runtime_compatibility_identity", return_value={"pin": "one"}), \
                        mock.patch.object(self.module, "execute_prepared", return_value=raw):
                    judge = self.module.NativeJudge("pinned-model")
                    with self.assertRaises(ValueError):
                        judge({}, destination, "pinned-model")


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-native-eval-entrypoint"))
