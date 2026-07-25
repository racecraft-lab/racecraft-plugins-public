#!/usr/bin/env python3
"""Contracts for the exact-treatment runner and the demoted smoke surface."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LAYER6 = TEST_ROOT / "layer6-efficiency"
SMOKE_RUNNER = LAYER6 / "run-efficiency-benchmarks.py"
LIB_DIR = TEST_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


NON_RELEASE_MARKER = "non_release_evidence"

# Fields that let a record stand as route qualification evidence. They belong to
# the treatment-record contract and are never carried by the smoke surface.
ROUTE_QUALIFICATION_FIELDS = frozenset(
    {
        "candidate_route_id",
        "dispatch_namespace",
        "execution_trace_id",
        "observed_model_id",
        "route_resolution",
        "scorable",
        "score_disposition",
        "treatment_disposition",
    }
)

# The shape of every smoke result written before the demotion marker existed.
HISTORICAL_SMOKE_RECORD = {
    "agent": "consensus-synthesizer",
    "model": "",
    "tokens": 1280,
    "wall_time": 12,
    "quality": 0.85,
    "exit_code": 0,
}

EXPECTED_OUTPUT = "## Answer\n\n- alpha beta gamma\n"


def import_smoke_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("l6_smoke_runner", SMOKE_RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_fixture(root: Path, expected: str | None = None) -> Path:
    fixtures = root / "fixtures"
    agent = fixtures / "stub-agent"
    agent.mkdir(parents=True)
    (agent / "input-prompt.md").write_text("stub input\n", encoding="utf-8")
    if expected is not None:
        (agent / "expected-output.md").write_text(expected, encoding="utf-8")
    return fixtures


def read_records(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def codex_stub_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    Path(argv[argv.index("-o") + 1]).write_text(EXPECTED_OUTPUT, encoding="utf-8")
    kwargs["stdout"].write(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 12}}) + "\n")
    return subprocess.CompletedProcess(argv, 0)


class SmokeSurfaceDemotionTests(unittest.TestCase):
    """The prompt-emulation runner and the lexical quality scorer are smoke
    surfaces whose results are never route qualification evidence (FR-007)."""

    def setUp(self) -> None:
        self.runner = import_smoke_runner()

    def test_every_emitted_smoke_record_is_labeled_non_release(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixtures = make_fixture(root)
            executable = root / "claude"
            executable.write_text("stub\n", encoding="utf-8")
            results = root / "results.json"
            writer = self.runner.ResultWriter(results)
            writer.write()
            self.assertEqual(read_records(results), [])

            failed = subprocess.CompletedProcess([], 1, stdout="", stderr="refused")
            with contextlib.redirect_stdout(io.StringIO()):
                with mock.patch.object(self.runner.subprocess, "run", return_value=failed):
                    self.runner.run_benchmark("stub-agent", "", fixtures, writer, executable)
                with mock.patch.object(self.runner.subprocess, "run", side_effect=OSError("spawn failed")):
                    self.runner.run_benchmark("stub-agent", "", fixtures, writer, executable)
                with mock.patch.object(self.runner.subprocess, "run", side_effect=codex_stub_run):
                    self.runner.run_benchmark_codex("stub-agent", "high", fixtures, writer, executable)

            records = read_records(results)

        self.assertEqual([record["exit_code"] for record in records], [1, 127, 0])
        for record in records:
            with self.subTest(msg=f"exit_code={record['exit_code']}"):
                self.assertIs(record.get(NON_RELEASE_MARKER), True, record)

    def test_lexical_quality_scores_are_emitted_only_as_non_release_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixtures = make_fixture(root, EXPECTED_OUTPUT)
            executable = root / "claude"
            executable.write_text("stub\n", encoding="utf-8")
            results = root / "results.json"
            writer = self.runner.ResultWriter(results)
            completed = subprocess.CompletedProcess(
                [],
                0,
                stdout=json.dumps(
                    {"result": EXPECTED_OUTPUT, "usage": {"input_tokens": 3, "output_tokens": 4}}
                ),
                stderr="",
            )
            with contextlib.redirect_stdout(io.StringIO()):
                with mock.patch.object(self.runner.subprocess, "run", return_value=completed):
                    self.runner.run_benchmark("stub-agent", "", fixtures, writer, executable)

            record = read_records(results)[0]

        scored = self.runner.QUALITY_SCORER.score_text(EXPECTED_OUTPUT, EXPECTED_OUTPUT)
        self.assertEqual(record["quality"], scored["overall"])
        self.assertIs(record.get(NON_RELEASE_MARKER), True, record)

    def test_smoke_results_cannot_stand_as_route_qualification_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            results = Path(temporary) / "results.json"
            writer = self.runner.ResultWriter(results)
            writer.append("stub-agent", "", 1280, 12, 0.85, 0)
            record = read_records(results)[0]

        self.assertIs(record.get(NON_RELEASE_MARKER), True, record)
        self.assertEqual(ROUTE_QUALIFICATION_FIELDS.intersection(record), set())
        self.assertEqual(ROUTE_QUALIFICATION_FIELDS.intersection(HISTORICAL_SMOKE_RECORD), set())
        self.assertEqual(set(record) - set(HISTORICAL_SMOKE_RECORD), {NON_RELEASE_MARKER})


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SmokeSurfaceDemotionTests)
    raise SystemExit(run_counted(suite, label="test-exact-treatment-runner"))
