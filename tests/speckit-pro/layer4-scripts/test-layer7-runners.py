#!/usr/bin/env python3
"""Layer-4 contracts for the Python Layer-7 replay/live runners."""

from __future__ import annotations

import ast
import os
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


RUNNERS = [
    LAYER7 / "run-dispatch-fixtures.py",
    LAYER7 / "run-return-format-fixtures.py",
    LAYER7 / "run-e2e-fixtures.py",
    LAYER7 / "run-grounding-fixtures.py",
    LAYER7 / "run-all-fixtures.py",
]


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


class Layer7RunnerTests(unittest.TestCase):
    def test_layer7_runner_contract(self) -> None:
        checks: list[tuple[str, Callable[[], None]]] = []
        for runner in RUNNERS:
            checks.append((f"{runner.name} exists", lambda runner=runner: self.assertTrue(runner.is_file())))
        checks.append(("shared fixture runner exists", lambda: self.assertTrue((LAYER7 / "lib" / "fixture_runner.py").is_file())))
        checks.append(("all Layer-7 Python runners are executable", lambda: self.assertTrue(all(os.access(path, os.X_OK) for path in RUNNERS))))

        for runner, summary in [
            (RUNNERS[0], "run-dispatch-fixtures: 184/184 passed"),
            (RUNNERS[1], "run-return-format-fixtures: 17/17 passed"),
            (RUNNERS[2], "run-e2e-fixtures: 23/23 passed"),
            (RUNNERS[3], "run-grounding-fixtures: 33/33 passed"),
        ]:
            result = run_runner(runner, "--replay")
            checks.append((f"{runner.name} replay exits 0", lambda result=result: self.assertEqual(result.returncode, 0, result.stderr)))
            checks.append((f"{runner.name} replay preserves summary", lambda result=result, summary=summary: self.assertIn(summary, result.stdout)))

        aggregate = run_runner(RUNNERS[4], "--replay")
        checks.append(("run-all-fixtures.py replay exits 0", lambda: self.assertEqual(aggregate.returncode, 0, aggregate.stderr)))
        checks.append(("run-all-fixtures.py executes all four classes", lambda: self.assertEqual(aggregate.stdout.count("Layer 7 Class"), 4)))
        checks.append(("run-all-fixtures.py preserves PASSED headline", lambda: self.assertIn("Layer 7 PASSED", aggregate.stdout)))

        source_paths = [*RUNNERS, LAYER7 / "lib" / "fixture_runner.py"]
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

        tree = ast.parse((LAYER7 / "lib" / "fixture_runner.py").read_text(encoding="utf-8"))
        subprocess_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run"]
        checks.append(("live capture subprocess calls use argv lists", lambda: self.assertTrue(all(isinstance(call.args[0], (ast.List, ast.Name)) for call in subprocess_calls))))

        for name, check in checks:
            with self.subTest(msg=name):
                check()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer7RunnerTests)
    raise SystemExit(run_counted(suite, label="test-layer7-runners"))
