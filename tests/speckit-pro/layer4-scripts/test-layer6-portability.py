#!/usr/bin/env python3
"""Cross-platform contracts for the XPLAT-010 Layer-6 Python runner."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
RUNNER_PATH = TESTS_ROOT / "layer6-efficiency" / "run-efficiency-benchmarks.py"
QUALITY_SCORER = TESTS_ROOT / "layer6-efficiency" / "lib" / "quality-scorer.py"
BASELINE = TESTS_ROOT / "parity" / "xplat-010" / "test-layer6-portability-baseline.txt"
SHARED_LIB = TESTS_ROOT / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from test_result import run_counted  # noqa: E402


CURRENT_INVENTORY = [
    "baseline inventory is truthful and ordered",
    "result timestamp is Windows-safe",
    "generic path resolution works while configured runtime names are constrained",
    "Claude benchmark pins command resolution to the selected directory",
    "Codex benchmark pins command resolution to the selected directory",
    "Claude subprocess pins UTF-8 replacement decoding",
    "Codex subprocess pins UTF-8 replacement decoding",
    "Claude prompt strips command-substitution trailing newlines",
    "Codex prompt bytes match command-substitution composition",
    "result writer initializes a valid empty JSON array",
    "result writer persists a valid record after append",
    "Codex spawn failure records exit 127",
    "Codex spawn failure removes all temporary files",
    "partial result JSON remains valid after spawn failure",
    "quality scorer ignores extra positional arguments like predecessor",
    "quality scorer missing arguments exits one like predecessor",
    "Layer-6 help remains an unknown flag with exit two",
    "Layer-6 missing agent value exits one",
]


def import_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("l6_portability_runner", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def baseline_inventory(path: Path) -> list[str]:
    names: list[str] = []
    total: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("TOTAL: "):
            total = int(line.removeprefix("TOTAL: "))
            continue
        _ordinal, name = line.split(" ", 1)
        names.append(name)
    if total != len(names):
        raise AssertionError(f"baseline TOTAL {total} does not match {len(names)} names")
    return names


def make_fixture(root: Path) -> Path:
    fixtures = root / "fixtures"
    fixture = fixtures / "stub-agent"
    fixture.mkdir(parents=True)
    (fixture / "input-prompt.md").write_text("user input\n\n", encoding="utf-8")
    return fixtures


class Layer6PortabilityTests(unittest.TestCase):
    def test_layer6_portability_contract(self) -> None:
        runner = import_runner()
        help_stderr = io.StringIO()
        missing_stderr = io.StringIO()
        with contextlib.redirect_stderr(help_stderr):
            help_exit = runner.main(["--help"])
        with contextlib.redirect_stderr(missing_stderr):
            missing_agent_exit = runner.main(["--agent"])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixtures = make_fixture(root)
            arbitrary_executable = root / "custom-runtime.cmd"
            arbitrary_executable.write_text("test double\n", encoding="utf-8")
            if os.name != "nt":
                arbitrary_executable.chmod(
                    stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
                )
            resolved = runner.resolve_executable(str(arbitrary_executable))
            with contextlib.redirect_stdout(io.StringIO()):
                rejected_runtime = runner.resolve_runtime_executable(
                    runner.Config(runtime=runner.RUNTIME_CLAUDE, claude_bin=str(arbitrary_executable))
                )

            claude_results = root / "claude-results.json"
            claude_writer = runner.ResultWriter(claude_results)
            claude_writer.write()
            claude_calls: list[tuple[list[str], dict[str, object]]] = []

            def claude_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                claude_calls.append((list(argv), dict(kwargs)))
                return subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout=json.dumps({"usage": {"input_tokens": 1, "output_tokens": 2}}),
                    stderr="",
                )

            with mock.patch.object(runner.subprocess, "run", side_effect=claude_run):
                runner.run_benchmark(
                    "stub-agent",
                    "",
                    fixtures,
                    claude_writer,
                    arbitrary_executable,
                )

            codex_results = root / "codex-results.json"
            codex_writer = runner.ResultWriter(codex_results)
            codex_writer.write()
            codex_calls: list[tuple[list[str], dict[str, object]]] = []

            def codex_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                codex_calls.append((list(argv), dict(kwargs)))
                output_path = Path(argv[argv.index("-o") + 1])
                output_path.write_text("final answer\n", encoding="utf-8")
                stdout = kwargs["stdout"]
                stdout.write(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1}}) + "\n")
                return subprocess.CompletedProcess(argv, 0)

            with mock.patch.object(runner.subprocess, "run", side_effect=codex_run):
                runner.run_benchmark_codex(
                    "stub-agent",
                    "xhigh",
                    fixtures,
                    codex_writer,
                    arbitrary_executable,
                )

            failure_results = root / "failure-results.json"
            failure_writer = runner.ResultWriter(failure_results)
            failure_writer.write()
            temp_root = root / "temporary-files"
            temp_root.mkdir()
            previous_tempdir = runner.tempfile.tempdir
            runner.tempfile.tempdir = str(temp_root)
            try:
                with mock.patch.object(runner.subprocess, "run", side_effect=OSError("spawn failed")):
                    runner.run_benchmark_codex(
                        "stub-agent",
                        "high",
                        fixtures,
                        failure_writer,
                        arbitrary_executable,
                    )
            finally:
                runner.tempfile.tempdir = previous_tempdir

            standalone_writer = runner.ResultWriter(root / "empty.json")
            standalone_writer.write()
            empty_payload = json.loads(standalone_writer.path.read_text(encoding="utf-8"))
            standalone_writer.append("agent", "model", 1, 2, 0.5, 0)
            appended_payload = json.loads(standalone_writer.path.read_text(encoding="utf-8"))
            failure_payload = json.loads(failure_results.read_text(encoding="utf-8"))

            actual = root / "actual.md"
            expected = root / "expected.md"
            actual.write_text("## Result\n", encoding="utf-8")
            expected.write_text("## Result\n", encoding="utf-8")
            quality_extra = subprocess.run(
                [sys.executable, str(QUALITY_SCORER), str(actual), str(expected), "ignored"],
                cwd=REPO_ROOT,
                text=True,
                encoding="utf-8",
                capture_output=True,
                shell=False,
                check=False,
            )
            quality_missing = subprocess.run(
                [sys.executable, str(QUALITY_SCORER)],
                cwd=REPO_ROOT,
                text=True,
                encoding="utf-8",
                capture_output=True,
                shell=False,
                check=False,
            )

            checks = [
                (CURRENT_INVENTORY[0], lambda: self.assertEqual(baseline_inventory(BASELINE), CURRENT_INVENTORY)),
                (CURRENT_INVENTORY[1], lambda: self.assertRegex(runner.timestamp(), r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z$")),
                (
                    CURRENT_INVENTORY[2],
                    lambda: (
                        self.assertEqual(resolved, Path(os.path.abspath(arbitrary_executable))),
                        self.assertIsNone(rejected_runtime),
                    ),
                ),
                (
                    CURRENT_INVENTORY[3],
                    lambda: (
                        self.assertEqual(claude_calls[0][0][0], "claude"),
                        self.assertEqual(
                            str(claude_calls[0][1]["env"]["PATH"]).split(os.pathsep, 1)[0],
                            str(arbitrary_executable.parent),
                        ),
                    ),
                ),
                (
                    CURRENT_INVENTORY[4],
                    lambda: (
                        self.assertEqual(codex_calls[0][0][0], "codex"),
                        self.assertEqual(
                            str(codex_calls[0][1]["env"]["PATH"]).split(os.pathsep, 1)[0],
                            str(arbitrary_executable.parent),
                        ),
                    ),
                ),
                (
                    CURRENT_INVENTORY[5],
                    lambda: self.assertEqual(
                        (claude_calls[0][1].get("encoding"), claude_calls[0][1].get("errors")),
                        ("utf-8", "replace"),
                    ),
                ),
                (
                    CURRENT_INVENTORY[6],
                    lambda: self.assertEqual(
                        (codex_calls[0][1].get("encoding"), codex_calls[0][1].get("errors")),
                        ("utf-8", "replace"),
                    ),
                ),
                (CURRENT_INVENTORY[7], lambda: self.assertEqual(runner.compose_prompt("body\n", "input\n\n"), "body\n\n---\n\ninput")),
                (CURRENT_INVENTORY[8], lambda: self.assertEqual(runner.compose_prompt("dev\n\n", "task\n"), "dev\n\n---\n\ntask")),
                (CURRENT_INVENTORY[9], lambda: self.assertEqual(empty_payload, [])),
                (CURRENT_INVENTORY[10], lambda: self.assertEqual(appended_payload[0]["agent"], "agent")),
                (CURRENT_INVENTORY[11], lambda: self.assertEqual(failure_payload[0]["exit_code"], 127)),
                (CURRENT_INVENTORY[12], lambda: self.assertEqual(list(temp_root.iterdir()), [])),
                (CURRENT_INVENTORY[13], lambda: self.assertEqual(len(failure_payload), 1)),
                (CURRENT_INVENTORY[14], lambda: self.assertEqual(quality_extra.returncode, 0)),
                (CURRENT_INVENTORY[15], lambda: self.assertEqual(quality_missing.returncode, 1)),
                (CURRENT_INVENTORY[16], lambda: self.assertEqual(help_exit, 2)),
                (CURRENT_INVENTORY[17], lambda: self.assertEqual(missing_agent_exit, 1)),
            ]

            self.assertEqual([name for name, _check in checks], CURRENT_INVENTORY)
            for name, check in checks:
                with self.subTest(msg=name):
                    check()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer6PortabilityTests)
    raise SystemExit(run_counted(suite, label="test-layer6-portability"))
