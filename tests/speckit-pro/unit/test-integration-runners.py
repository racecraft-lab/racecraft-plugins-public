#!/usr/bin/env python3
"""Layer-4 contracts for the Python Layer-7 replay/live runners."""

from __future__ import annotations

import ast
import contextlib
import importlib.util
import io
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Callable
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LAYER7 = TESTS_ROOT / "layer7-integration"
LIB_DIR = TESTS_ROOT / "lib"
for value in (LAYER7, LIB_DIR):
    if str(value) not in sys.path:
        sys.path.insert(0, str(value))

from lib import fixture_runner  # noqa: E402
from test_result import run_counted  # noqa: E402


AGGREGATE_RUNNER = LAYER7 / "run-all-fixtures.py"


def run_runner(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(path), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1"},
        shell=False,
        check=False,
    )


def load_script_module(path: Path, module_name: str) -> object:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Layer7RunnerTests(unittest.TestCase):
    def test_layer7_runner_contract(self) -> None:
        aggregate_module = load_script_module(AGGREGATE_RUNNER, "run_all_fixtures_test")
        dispatcher_module = load_script_module(TESTS_ROOT / "run-layer-scripts.py", "run_layer_scripts_layer7_test")
        runners = list(aggregate_module.RUNNERS.values())
        self.assertTrue(runners)
        checks: list[tuple[str, Callable[[], None]]] = []
        for runner in (*runners, AGGREGATE_RUNNER):
            checks.append((f"{runner.name} exists", lambda runner=runner: self.assertTrue(runner.is_file())))
        checks.append(("shared fixture runner exists", lambda: self.assertTrue((LAYER7 / "lib" / "fixture_runner.py").is_file())))
        checks.append(("all Layer-7 Python runners are executable", lambda: self.assertTrue(all(os.access(path, os.X_OK) for path in (*runners, AGGREGATE_RUNNER)))))

        for runner in runners:
            result = run_runner(runner, "--replay")
            checks.append((f"{runner.name} replay exits 0", lambda result=result: self.assertEqual(result.returncode, 0, result.stderr)))
            summary = re.search(rf"^{re.escape(runner.stem)}: ([0-9]+)/([0-9]+) passed$", result.stdout, re.MULTILINE)
            checks.append((f"{runner.name} replay emits a summary", lambda summary=summary: self.assertIsNotNone(summary)))
            if summary is not None:
                passed, total = map(int, summary.groups())
                checks.append((f"{runner.name} replay summary is self-consistent", lambda passed=passed, total=total: self.assertTrue(total > 0 and passed == total)))

        aggregate = run_runner(AGGREGATE_RUNNER, "--replay")
        checks.append(("run-all-fixtures.py replay exits 0", lambda: self.assertEqual(aggregate.returncode, 0, aggregate.stderr)))
        for class_id in aggregate_module.RUNNERS:
            heading = f"Layer 7 - Class {class_id}"
            checks.append((f"run-all-fixtures.py executes class {class_id}", lambda heading=heading: self.assertEqual(aggregate.stdout.count(heading), 1)))
        checks.append(("run-all-fixtures.py preserves PASSED headline", lambda: self.assertIn("Layer 7 PASSED", aggregate.stdout)))

        empty_reporter = fixture_runner.Reporter()
        with contextlib.redirect_stdout(io.StringIO()):
            empty_reporter_exit = empty_reporter.finish("empty-layer7-fixture")
        checks.append(("fixture reporter rejects zero discovered checks", lambda: self.assertEqual(empty_reporter_exit, 1)))

        invalid_nested_results = (
            ("missing summary", subprocess.CompletedProcess(["early"], 0, stdout="", stderr="")),
            ("wrong label only", subprocess.CompletedProcess(["early"], 0, stdout="nested-child: 1/1 passed\n", stderr="")),
            (
                "duplicate owned summary",
                subprocess.CompletedProcess(["early"], 0, stdout="early: 1/1 passed\nearly: 1/1 passed\n", stderr=""),
            ),
            ("zero discovery", subprocess.CompletedProcess(["early"], 0, stdout="early: 0/0 passed\n", stderr="")),
            ("partial pass", subprocess.CompletedProcess(["early"], 0, stdout="early: 1/2 passed\n", stderr="")),
            ("passed exceeds total", subprocess.CompletedProcess(["early"], 0, stdout="early: 2/1 passed\n", stderr="")),
            ("nonzero all-pass", subprocess.CompletedProcess(["early"], 1, stdout="early: 1/1 passed\n", stderr="")),
        )
        valid_later = subprocess.CompletedProcess(["later"], 0, stdout="later: 1/1 passed\n", stderr="")
        for case_name, invalid_early in invalid_nested_results:
            aggregate_stdout = io.StringIO()
            aggregate_stderr = io.StringIO()
            with (
                patch.object(aggregate_module, "RUNNERS", {"early": Path("early.py"), "later": Path("later.py")}),
                patch.object(aggregate_module.subprocess, "run", side_effect=[invalid_early, valid_later]),
                contextlib.redirect_stdout(aggregate_stdout),
                contextlib.redirect_stderr(aggregate_stderr),
            ):
                aggregate_exit = aggregate_module.main(["--replay"])
            checks.append(
                (
                    f"run-all-fixtures rejects an early {case_name} before a valid child",
                    lambda aggregate_exit=aggregate_exit: self.assertEqual(aggregate_exit, 1),
                )
            )

            aggregate_completed = subprocess.CompletedProcess(
                [sys.executable, str(AGGREGATE_RUNNER)],
                aggregate_exit,
                stdout=aggregate_stdout.getvalue(),
                stderr=aggregate_stderr.getvalue(),
            )
            with patch.object(dispatcher_module.subprocess, "run", return_value=aggregate_completed):
                dispatch_stdout = io.StringIO()
                dispatch_stderr = io.StringIO()
                with contextlib.redirect_stdout(dispatch_stdout), contextlib.redirect_stderr(dispatch_stderr):
                    dispatch_exit = dispatcher_module.run_script_suite(
                        "layer-7 integration fixtures",
                        [AGGREGATE_RUNNER],
                        REPO_ROOT,
                    )
            checks.append(
                (
                    f"layer dispatcher rejects composed output with an early {case_name}",
                    lambda dispatch_exit=dispatch_exit: self.assertEqual(dispatch_exit, 1),
                )
            )

        source_paths = [*runners, AGGREGATE_RUNNER, LAYER7 / "lib" / "fixture_runner.py"]
        checks.append(("Layer-7 runner sources contain no shell=True", lambda: self.assertTrue(all("shell=True" not in path.read_text(encoding="utf-8") for path in source_paths))))
        checks.append(("Layer-7 runner sources contain no os.system", lambda: self.assertTrue(all("os.system" not in path.read_text(encoding="utf-8") for path in source_paths))))

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "fixture"
            fixture.mkdir()
            (fixture / "prompt.txt").write_text("test prompt\n", encoding="utf-8")
            (fixture / "expected.json").write_text("{}\n", encoding="utf-8")
            transcript_source = LAYER7 / "test-fixtures" / "single-dispatch.jsonl"
            discovered_claude = str(root / "claude.cmd")
            claude_argv: list[str] = []
            real_run = subprocess.run

            def run_with_fake_claude(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                if argv[0] == discovered_claude:
                    claude_argv.extend(argv[1:])
                    destination = kwargs["stdout"]
                    destination.write(transcript_source.read_text(encoding="utf-8"))
                    return subprocess.CompletedProcess(argv, 0)
                return real_run(argv, **kwargs)

            with (
                patch.object(fixture_runner.shutil, "which", return_value=discovered_claude),
                patch.object(fixture_runner.subprocess, "run", side_effect=run_with_fake_claude),
                patch.dict(os.environ, {"L7_UPDATE_PARSER_FIXTURE": "true"}),
            ):
                captured = fixture_runner.capture_live(fixture, "1.25")
            transcript_written = (fixture / "transcript.jsonl").is_file()
            parser_fixture_written = (fixture / "parser-fixture.jsonl").is_file()
            checks.append(("live capture uses discovered claude executable", lambda: self.assertTrue(captured)))
            checks.append(("live capture writes scrubbed transcript", lambda: self.assertTrue(transcript_written)))
            checks.append(("live capture can refresh parser fixture", lambda: self.assertTrue(parser_fixture_written)))
            checks.append(("live capture preserves stream-json flags", lambda: self.assertLessEqual({"-p", "--output-format", "stream-json", "--include-partial-messages", "--verbose", "--no-session-persistence"}, set(claude_argv))))
            checks.append(("live capture preserves budget argument", lambda: self.assertEqual(claude_argv[claude_argv.index("--max-budget-usd") + 1], "1.25")))

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "fixture"
            fixture.mkdir()
            (fixture / "prompt.txt").write_text("test prompt\n", encoding="utf-8")
            transcript_source = LAYER7 / "test-fixtures" / "single-dispatch.jsonl"
            discovered_claude = str(root / "claude.cmd")
            real_run = subprocess.run

            def run_with_failed_scrub(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                if argv[0] == discovered_claude:
                    destination = kwargs["stdout"]
                    destination.write(transcript_source.read_text(encoding="utf-8"))
                    return subprocess.CompletedProcess(argv, 0)
                if argv[:2] == [sys.executable, str(fixture_runner.SCRUBBER)]:
                    return subprocess.CompletedProcess(argv, 1, "", "scrub failed")
                return real_run(argv, **kwargs)

            scrub_failure: Exception | None = None
            with (
                patch.object(fixture_runner.shutil, "which", return_value=discovered_claude),
                patch.object(fixture_runner.subprocess, "run", side_effect=run_with_failed_scrub),
            ):
                try:
                    fixture_runner.capture_live(fixture, "1.25")
                except Exception as exc:  # pragma: no cover - exercised by assertions below
                    scrub_failure = exc
            checks.append(("scrub failure raises runtime error", lambda: self.assertIsInstance(scrub_failure, RuntimeError)))
            checks.append(("scrub failure reports scrub stderr", lambda: self.assertEqual(str(scrub_failure), "scrub failed")))
            checks.append(("scrub failure removes captured transcript", lambda: self.assertFalse((fixture / "transcript.jsonl").exists())))

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "bad-response-assertions"
            fixture.mkdir()
            (fixture / "expected.json").write_text('{"response_assertions":false}\n', encoding="utf-8")
            (fixture / "parser-fixture.jsonl").write_text(
                (LAYER7 / "test-fixtures" / "single-dispatch.jsonl").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            module = load_script_module(LAYER7 / "run-return-format-fixtures.py", "run_return_format_fixtures_test")
            module.FIXTURES = root
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                malformed_exit = module.main([fixture.name])
            checks.append(("return-format runner rejects top-level false response_assertions", lambda: self.assertEqual(malformed_exit, 2)))
            checks.append(("return-format runner reports response_assertions array requirement", lambda: self.assertIn("response_assertions must be an array", stderr.getvalue())))

        tree = ast.parse((LAYER7 / "lib" / "fixture_runner.py").read_text(encoding="utf-8"))
        subprocess_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run"]
        checks.append(("live capture subprocess calls use argv lists", lambda: self.assertTrue(all(isinstance(call.args[0], (ast.List, ast.Name)) for call in subprocess_calls))))

        for name, check in checks:
            with self.subTest(msg=name):
                check()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer7RunnerTests)
    raise SystemExit(run_counted(suite, label="test-integration-runners"))
