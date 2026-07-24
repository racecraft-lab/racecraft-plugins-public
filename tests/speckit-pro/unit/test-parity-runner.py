#!/usr/bin/env python3
"""Focused Layer-4 contracts for the Python Layer-8 parity runner."""

from __future__ import annotations

import ast
import copy
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LAYER8 = TESTS_ROOT / "layer8-parity"
RUNNER = LAYER8 / "run-parity-fixtures.py"
BASELINE = TESTS_ROOT / "parity" / "bash-to-python" / "test-parity-runner-baseline.txt"
SHARED_LIB = TESTS_ROOT / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from capture_baseline import baseline_inventory  # noqa: E402
from test_result import run_counted  # noqa: E402


CURRENT_INVENTORY = [
    "baseline inventory is truthful and ordered",
    "Layer-8 runner module imports",
    "Layer-8 runner source has no shell=True",
    "Layer-8 runner source has no os.system",
    "tracked Layer-8 tree contains no shell scripts",
    "run_path subprocess call uses argv variable",
    "run_path subprocess call disables shell",
    "help exits zero and prints usage",
    "unknown flag exits two with diagnostic",
    "missing CLAUDE_BIN skips live fixture",
    "configured missing claude path reports configured-path reason",
    "live stub invoked Path A and Path B only",
    "live stub receives claude -p argv",
    "live stub pins command resolution to the selected CLAUDE_BIN directory",
    "live stub receives configured budget",
    "JSON env set applies teams mode",
    "JSON env set applies fallback mode",
    "JSON env unset removes inherited values",
    "extractor exact passes despite whole-file drift",
    "extractor tolerance-1 passes numeric difference one",
    "byte-identical bypasses extractor configuration",
    "extractor equal-value fast path is semantic-only",
    "semantic-equivalent is skipped without failure",
    "semantic skip writes warning report",
    "invalid env contract is labeled to the env file",
    "diff reports consume bounded input and truncate deterministically",
    "no-extractor exact fallback passes identical bytes",
    "no-extractor tolerance-1 fallback passes identical bytes",
    "no-extractor tolerance-1 fallback rejects numeric drift as byte diff",
    "no-extractor exact fallback rejects byte drift",
    "fail_fast stops after first failing comparison",
    "fail_fast omits later comparison label",
    "live mode writes claude exit code files",
]


LIVE_COMPARE = [
    {
        "field": "extractor.statuses",
        "source": "artifact.md",
        "section_selector": "## Exact Section",
        "extractor": "table_column:Status",
        "tolerance_key": "extractor.statuses",
    },
    {
        "field": "extractor.row_count",
        "source": "artifact.md",
        "section_selector": "## Count Section",
        "extractor": "table_row_count",
        "tolerance_key": "extractor.row_count",
    },
    {
        "field": "semantic.findings",
        "source": "artifact.md",
        "section_selector": "## Semantic Section",
        "extractor": "table_column:Finding",
        "tolerance_key": "semantic.findings",
    },
    {
        "field": "whole_file.exact",
        "source": "same-exact.txt",
        "tolerance_key": "whole_file.exact",
    },
    {
        "field": "whole_file.tolerance_one",
        "source": "same-number.txt",
        "tolerance_key": "whole_file.tolerance_one",
    },
]

LIVE_TOLERANCES = {
    "extractor.statuses": {"tolerance": "exact"},
    "extractor.row_count": {"tolerance": "tolerance-1"},
    "semantic.findings": {"tolerance": "semantic-equivalent"},
    "whole_file.exact": {"tolerance": "exact"},
    "whole_file.tolerance_one": {"tolerance": "tolerance-1"},
}


def import_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("layer8_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1"},
        shell=False,
        check=False,
    )


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_fixture(
    root: Path,
    name: str,
    compare: list[dict[str, str]],
    tolerances: dict[str, dict[str, str]],
    *,
    fail_fast: bool = False,
) -> Path:
    fixture = root / name
    fixture.mkdir()
    (fixture / "README.md").write_text(f"# {name}\n", encoding="utf-8")
    (fixture / "workflow.md").write_text("# Temporary parity workflow\n", encoding="utf-8")
    for mode in ("teams", "fallback"):
        write_json(
            fixture / f"env-{mode}.json",
            {
                "schema": "speckit.layer8.env.v1",
                "mode": mode,
                "environment": {
                    "set": {"L8_MODE": mode},
                    "unset": ["L8_SHOULD_BE_UNSET"],
                },
            },
        )
    write_json(
        fixture / "tolerance.json",
        {
            "schema": "speckit.layer8.tolerance.v1",
            "fixture_id": name,
            "fields": {
                key: value | {"rationale": value.get("rationale", "focused unit-test contract")}
                for key, value in tolerances.items()
            },
        },
    )
    write_json(
        fixture / "expected-equivalence.json",
        {
            "schema": "speckit.layer8.expected-equivalence.v1",
            "fixture_id": name,
            "compare": compare,
            "fail_fast": fail_fast,
        },
    )
    return fixture


def fake_claude_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    """Emulate Claude without relying on POSIX executable files."""
    child_env = kwargs["env"]
    if not isinstance(child_env, dict):
        raise AssertionError("child environment must be a dictionary")
    cwd = Path(str(kwargs["cwd"]))
    mode = str(child_env.get("L8_MODE", ""))
    log_path = Path(str(child_env["L8_STUB_LOG"]))
    with log_path.open("a", encoding="utf-8") as log:
        log.write(
            json.dumps(
                {
                    "executable": argv[0],
                    "selected_dir": str(child_env.get("PATH", "")).split(os.pathsep, 1)[0],
                    "argv": argv[1:],
                    "budget": argv[argv.index("--max-budget-usd") + 1],
                    "cwd": cwd.name,
                    "mode": mode,
                    "unset_present": "L8_SHOULD_BE_UNSET" in child_env,
                },
                sort_keys=True,
            )
            + "\n"
        )

    if mode == "teams":
        exact_noise = "teams-only unrelated text"
        count_rows = "| A | PASS |\n| B | PASS |"
        semantic_finding = "doctor clean"
        drift_exact = "alpha\n"
        drift_number = "1\n"
    else:
        exact_noise = "fallback-only unrelated text"
        count_rows = "| A | PASS |\n| B | PASS |\n| C | PASS |"
        semantic_finding = "doctor passes"
        drift_exact = "alpha \n"
        drift_number = "2\n"

    (cwd / "artifact.md").write_text(
        f"""# Artifact

{exact_noise}

## Exact Section

| Task | Status |
|------|--------|
| one | PASS |
| two | FAIL |

## Count Section

| Task | Status |
|------|--------|
{count_rows}

## Semantic Section

| Item | Finding |
|------|---------|
| one | {semantic_finding} |
""",
        encoding="utf-8",
    )
    (cwd / "same-exact.txt").write_text("alpha\n", encoding="utf-8")
    (cwd / "same-number.txt").write_text("7\n", encoding="utf-8")
    (cwd / "drift-exact.txt").write_text(drift_exact, encoding="utf-8")
    (cwd / "drift-number.txt").write_text(drift_number, encoding="utf-8")
    return subprocess.CompletedProcess(argv, 0)


def subprocess_run_calls(tree: ast.AST) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "run"
            and isinstance(func.value, ast.Name)
            and func.value.id == "subprocess"
        ):
            calls.append(node)
    return calls


def call_shell_keyword_is_false(call: ast.Call) -> bool:
    for keyword in call.keywords:
        if keyword.arg == "shell":
            return isinstance(keyword.value, ast.Constant) and keyword.value.value is False
    return False


class Layer8RunnerTests(unittest.TestCase):
    def test_required_invariant_negative_canaries(self) -> None:
        runner = import_runner()
        with tempfile.TemporaryDirectory() as temporary:
            fixture = make_fixture(
                Path(temporary),
                "invariant-canary",
                [{"field": "workflow", "source": "workflow.md", "tolerance_key": "workflow"}],
                {"workflow": {"tolerance": "exact"}},
            )
            (fixture / "workflow.md").write_text(
                """# Invariant canary

## Required Invariants

| Invariant | Value |
|-----------|-------|
| missing_packet_blocks_pr_create | true |
""",
                encoding="utf-8",
            )
            expected = runner.load_json(fixture / "expected-equivalence.json")
            tolerance = runner.load_json(fixture / "tolerance.json")
            expected["required_invariants"] = {"missing_packet_blocks_pr_create": True}
            expected["required_invariants_source"] = {
                "source": "workflow.md",
                "section_selector": "## Required Invariants",
                "key_column": "Invariant",
                "value_column": "Value",
            }

            with self.subTest(msg="invalid expected schema is rejected"):
                invalid_schema = copy.deepcopy(expected)
                invalid_schema["schema"] = "broken"
                with self.assertRaisesRegex(ValueError, "schema must be"):
                    runner.validate_fixture_contracts(fixture, invalid_schema, tolerance)

            with self.subTest(msg="dangling tolerance reference is rejected"):
                dangling = copy.deepcopy(expected)
                dangling["compare"][0]["tolerance_key"] = "missing"
                with self.assertRaisesRegex(ValueError, "must reference tolerance.json fields"):
                    runner.validate_fixture_contracts(fixture, dangling, tolerance)

            with self.subTest(msg="false required invariant output is rejected"):
                runner.validate_fixture_contracts(fixture, expected, tolerance)
                (fixture / "workflow.md").write_text(
                    (fixture / "workflow.md").read_text(encoding="utf-8").replace("| true |", "| false |"),
                    encoding="utf-8",
                )
                counts = runner.Counts()
                with contextlib.redirect_stdout(io.StringIO()):
                    valid = runner.enforce_required_invariants(fixture, expected, counts, fixture.name)
                self.assertFalse(valid)
                self.assertEqual(counts.failed, 1)

    def test_layer8_runner_contract(self) -> None:
        runner = import_runner()
        source = RUNNER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        run_calls = subprocess_run_calls(tree)
        tracked_shells = subprocess.run(
            ["git", "ls-files", "--", ":(glob)tests/speckit-pro/layer8-parity/**/*.sh"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            shell=False,
            check=False,
        )
        live_tracked_shells = [
            path for path in tracked_shells.stdout.splitlines() if (REPO_ROOT / path).is_file()
        ]

        help_result = run_cli("--help")
        parse_error = run_cli("--unknown")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = make_fixture(root, "canonical-live", LIVE_COMPARE, LIVE_TOLERANCES)
            stub = root / "claude.cmd"
            stub.write_text("test double\n", encoding="utf-8")
            out_root = root / "out"
            log_path = root / "stub-calls.jsonl"
            env = {
                "L8_OUT": str(out_root),
                "L8_STUB_LOG": str(log_path),
                "L8_SHOULD_BE_UNSET": "inherited-value",
            }
            counts = runner.Counts()
            stdout = io.StringIO()
            with (
                patch.dict(os.environ, env, clear=False),
                patch.object(runner, "resolve_executable", return_value=str(stub)),
                patch.object(runner.subprocess, "run", side_effect=fake_claude_run),
                contextlib.redirect_stdout(stdout),
            ):
                runner.run_fixture_live(
                    fixture,
                    runner.Config(mode="live", budget_usd="3.50", claude_bin=str(stub)),
                    counts,
                )

            output = stdout.getvalue()
            logs = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            path_a = out_root / fixture.name / "pathA"
            path_b = out_root / fixture.name / "pathB"
            report = out_root / fixture.name / "diff-report.txt"

            missing_counts = runner.Counts()
            missing_stdout = io.StringIO()
            with contextlib.redirect_stdout(missing_stdout):
                runner.run_fixture_live(
                    fixture,
                    runner.Config(mode="live", budget_usd="3.50", claude_bin=str(root / "missing-claude")),
                    missing_counts,
                )

            fail_fast_fixture = make_fixture(
                root,
                "fail-fast-live",
                [
                    {
                        "field": "first_failure",
                        "source": "drift-exact.txt",
                        "tolerance_key": "first_failure",
                    },
                    {
                        "field": "after_failure",
                        "source": "same-exact.txt",
                        "tolerance_key": "after_failure",
                    },
                ],
                {
                    "first_failure": {"tolerance": "exact"},
                    "after_failure": {"tolerance": "exact"},
                },
                fail_fast=True,
            )
            fail_fast_log = root / "fail-fast-calls.jsonl"
            fail_fast_counts = runner.Counts()
            fail_fast_stdout = io.StringIO()
            with (
                patch.dict(
                    os.environ,
                    {
                        "L8_OUT": str(root / "fail-fast-out"),
                        "L8_STUB_LOG": str(fail_fast_log),
                        "L8_SHOULD_BE_UNSET": "inherited-value",
                    },
                    clear=False,
                ),
                patch.object(runner, "resolve_executable", return_value=str(stub)),
                patch.object(runner.subprocess, "run", side_effect=fake_claude_run),
                contextlib.redirect_stdout(fail_fast_stdout),
            ):
                runner.run_fixture_live(
                    fail_fast_fixture,
                    runner.Config(mode="live", budget_usd="3.50", claude_bin=str(stub)),
                    fail_fast_counts,
                )

            invalid_env_fixture = make_fixture(root, "invalid-env-live", LIVE_COMPARE, LIVE_TOLERANCES)
            write_json(
                invalid_env_fixture / "env-fallback.json",
                {
                    "schema": "broken.schema",
                    "mode": "fallback",
                    "environment": {
                        "set": {"L8_MODE": "fallback"},
                        "unset": ["L8_SHOULD_BE_UNSET"],
                    },
                },
            )
            invalid_env_counts = runner.Counts()
            invalid_env_stdout = io.StringIO()
            with contextlib.redirect_stdout(invalid_env_stdout):
                runner.validate_fixture_structure(invalid_env_fixture, invalid_env_counts)

            diff_report = root / "bounded-diff.txt"
            runner.append_value_diff(
                diff_report,
                "bounded.field",
                "table_column:Status",
                "\n".join(f"alpha {index}" for index in range(200)),
                "\n".join(f"beta {index}" for index in range(200)),
            )
            diff_report_text = diff_report.read_text(encoding="utf-8")
            bounded_diff_consumed = 0

            def bounded_diff_lines() -> object:
                nonlocal bounded_diff_consumed
                for index in range(200):
                    bounded_diff_consumed += 1
                    yield f"line {index}\n"

            bounded_diff_output = io.StringIO()
            runner._write_bounded_diff(bounded_diff_output, bounded_diff_lines())

            drift_number_status = self._compare_direct(
                runner,
                path_a,
                path_b,
                {
                    "field": "whole_file.tolerance_drift",
                    "source": "drift-number.txt",
                    "tolerance_key": "whole_file.tolerance_drift",
                },
                {"fields": {"whole_file.tolerance_drift": {"tolerance": "tolerance-1"}}},
            )
            drift_exact_status = self._compare_direct(
                runner,
                path_a,
                path_b,
                {
                    "field": "whole_file.exact_drift",
                    "source": "drift-exact.txt",
                    "tolerance_key": "whole_file.exact_drift",
                },
                {"fields": {"whole_file.exact_drift": {"tolerance": "exact"}}},
            )
            byte_first_status = self._compare_direct(
                runner,
                path_a,
                path_b,
                {
                    "field": "whole_file.byte_first",
                    "source": "same-exact.txt",
                    "section_selector": "## Missing Section",
                    "extractor": "table_column:Missing",
                    "tolerance_key": "whole_file.byte_first",
                },
                {"fields": {"whole_file.byte_first": {"tolerance": "byte-identical"}}},
            )
            with patch.object(runner.judge, "judge_values", side_effect=AssertionError("judge should not run")):
                semantic_fast_path_status = self._compare_direct(
                    runner,
                    path_a,
                    path_b,
                    {
                        "field": "extractor.semantic_fast_path",
                        "source": "artifact.md",
                        "section_selector": "## Exact Section",
                        "extractor": "table_column:Status",
                        "tolerance_key": "extractor.semantic_fast_path",
                    },
                    {"fields": {"extractor.semantic_fast_path": {"tolerance": "semantic-equivalent"}}},
                )
            nonnumeric_tolerance_status = self._compare_direct(
                runner,
                path_a,
                path_b,
                {
                    "field": "extractor.equal_nonnumeric",
                    "source": "artifact.md",
                    "section_selector": "## Exact Section",
                    "extractor": "table_column:Status",
                    "tolerance_key": "extractor.equal_nonnumeric",
                },
                {"fields": {"extractor.equal_nonnumeric": {"tolerance": "tolerance-1"}}},
            )
            unsupported_tolerance_status = self._compare_direct(
                runner,
                path_a,
                path_b,
                {
                    "field": "extractor.unsupported",
                    "source": "artifact.md",
                    "section_selector": "## Exact Section",
                    "extractor": "table_column:Status",
                    "tolerance_key": "extractor.unsupported",
                },
                {"fields": {"extractor.unsupported": {"tolerance": "unsupported"}}},
            )

            checks = [
                (
                    CURRENT_INVENTORY[0],
                    lambda: self.assertEqual(baseline_inventory(BASELINE), CURRENT_INVENTORY),
                ),
                (CURRENT_INVENTORY[1], lambda: self.assertIsNotNone(runner)),
                (CURRENT_INVENTORY[2], lambda: self.assertNotIn("shell=True", source)),
                (CURRENT_INVENTORY[3], lambda: self.assertNotIn("os.system", source)),
                (
                    CURRENT_INVENTORY[4],
                    lambda: self.assertTrue(tracked_shells.returncode == 0 and not live_tracked_shells),
                ),
                (
                    CURRENT_INVENTORY[5],
                    lambda: self.assertTrue(
                        any(call.args and isinstance(call.args[0], ast.Name) and call.args[0].id == "argv" for call in run_calls)
                    ),
                ),
                (
                    CURRENT_INVENTORY[6],
                    lambda: self.assertTrue(run_calls and all(call_shell_keyword_is_false(call) for call in run_calls)),
                ),
                (
                    CURRENT_INVENTORY[7],
                    lambda: self.assertTrue(
                        help_result.returncode == 0 and "Layer 8 - Parity Fixtures Runner" in help_result.stdout
                    ),
                ),
                (
                    CURRENT_INVENTORY[8],
                    lambda: self.assertTrue(
                        parse_error.returncode == 2 and "Unknown flag: --unknown" in parse_error.stderr
                    ),
                ),
                (
                    CURRENT_INVENTORY[9],
                    lambda: self.assertEqual((missing_counts.skipped, missing_counts.failed), (1, 0)),
                ),
                (
                    CURRENT_INVENTORY[10],
                    lambda: self.assertIn(
                        f"configured CLAUDE_BIN path does not exist: {root / 'missing-claude'}",
                        missing_stdout.getvalue(),
                    ),
                ),
                (CURRENT_INVENTORY[11], lambda: self.assertEqual([entry["cwd"] for entry in logs], ["pathA", "pathB"])),
                (
                    CURRENT_INVENTORY[12],
                    lambda: self.assertTrue(all(entry["argv"][0] == "-p" for entry in logs)),
                ),
                (
                    CURRENT_INVENTORY[13],
                    lambda: (
                        self.assertEqual([entry["executable"] for entry in logs], ["claude", "claude"]),
                        self.assertEqual([entry["selected_dir"] for entry in logs], [str(stub.parent), str(stub.parent)]),
                    ),
                ),
                (
                    CURRENT_INVENTORY[14],
                    lambda: self.assertEqual([entry["budget"] for entry in logs], ["3.50", "3.50"]),
                ),
                (CURRENT_INVENTORY[15], lambda: self.assertEqual(logs[0]["mode"], "teams")),
                (CURRENT_INVENTORY[16], lambda: self.assertEqual(logs[1]["mode"], "fallback")),
                (
                    CURRENT_INVENTORY[17],
                    lambda: self.assertEqual([entry["unset_present"] for entry in logs], [False, False]),
                ),
                (
                    CURRENT_INVENTORY[18],
                    lambda: self.assertIn(
                        "PASS canonical-live:extractor.statuses (exact, extractor=table_column:Status)",
                        output,
                    ),
                ),
                (
                    CURRENT_INVENTORY[19],
                    lambda: self.assertIn("PASS canonical-live:extractor.row_count (tolerance-1, |2 - 3|=1)", output),
                ),
                (
                    CURRENT_INVENTORY[20],
                    lambda: self.assertEqual(byte_first_status, "pass"),
                ),
                (
                    CURRENT_INVENTORY[21],
                    lambda: self.assertEqual(
                        (semantic_fast_path_status, nonnumeric_tolerance_status, unsupported_tolerance_status),
                        ("pass", "fail", "fail"),
                    ),
                ),
                (
                    CURRENT_INVENTORY[22],
                    lambda: self.assertEqual((counts.failed, counts.skipped), (0, 1)),
                ),
                (
                    CURRENT_INVENTORY[23],
                    lambda: self.assertIn("semantic-equivalent comparison skipped", report.read_text(encoding="utf-8")),
                ),
                (
                    CURRENT_INVENTORY[24],
                    lambda: self.assertIn(
                        "FAIL invalid-env-live: env-fallback.json invalid env contract",
                        invalid_env_stdout.getvalue(),
                    ),
                ),
                (
                    CURRENT_INVENTORY[25],
                    lambda: self.assertTrue(
                        "... diff truncated after 50 lines" in diff_report_text
                        and diff_report_text.count("\n") <= 60
                        and bounded_diff_consumed == runner.MAX_DIFF_LINES + 1
                        and bounded_diff_output.getvalue().endswith(
                            f"... diff truncated after {runner.MAX_DIFF_LINES} lines\n"
                        )
                    ),
                ),
                (
                    CURRENT_INVENTORY[26],
                    lambda: self.assertIn("PASS canonical-live:whole_file.exact (exact, whole-file)", output),
                ),
                (
                    CURRENT_INVENTORY[27],
                    lambda: self.assertIn(
                        "PASS canonical-live:whole_file.tolerance_one (tolerance-1, whole-file)",
                        output,
                    ),
                ),
                (
                    CURRENT_INVENTORY[28],
                    lambda: self.assertEqual(drift_number_status, "fail"),
                ),
                (
                    CURRENT_INVENTORY[29],
                    lambda: self.assertEqual(drift_exact_status, "fail"),
                ),
                (
                    CURRENT_INVENTORY[30],
                    lambda: self.assertEqual((fail_fast_counts.failed, fail_fast_counts.passed), (1, 0)),
                ),
                (
                    CURRENT_INVENTORY[31],
                    lambda: self.assertNotIn("after_failure", fail_fast_stdout.getvalue()),
                ),
                (
                    CURRENT_INVENTORY[32],
                    lambda: self.assertEqual(
                        [
                            (path_a / ".claude-exit-code").read_text(encoding="utf-8").strip(),
                            (path_b / ".claude-exit-code").read_text(encoding="utf-8").strip(),
                        ],
                        ["0", "0"],
                    ),
                ),
            ]

            self.assertEqual([name for name, _check in checks], CURRENT_INVENTORY)
            for name, check in checks:
                with self.subTest(msg=name):
                    check()

    def _compare_direct(
        self,
        runner: ModuleType,
        path_a: Path,
        path_b: Path,
        field_json: dict[str, str],
        tolerance_json: dict[str, dict[str, dict[str, str]]],
    ) -> str:
        with contextlib.redirect_stdout(io.StringIO()):
            return runner.compare_field(
                "canonical-live",
                path_a,
                path_b,
                field_json,
                tolerance_json,
                runner.Counts(),
            )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer8RunnerTests)
    raise SystemExit(run_counted(suite, label="test-parity-runner"))
