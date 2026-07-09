#!/usr/bin/env python3
"""Unit tests for the run-all.py orchestrator (XPLAT-010 US1, FR-006).

Exercises the manifest-driven flag/scope/headline/exit-code contract that
reproduces run-all.sh 1:1 (research §D5): argument parsing (including unknown
flags -> exit 2), per-layer scope selection from suite-manifest.json, the
summary-line parser, the ``speckit-pro test suite: X/Y passed`` headline
formatting, and the child-outcome disposition taxonomy (crash vs no-summary
pass vs Bash-absent transitional skip).

The hyphenated ``run-all.py`` is loaded via importlib. Prints the house
``test-run-all: {passed}/{total} passed`` summary.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import test_result  # noqa: E402


def _load_run_all():
    path = REPO_ROOT / "tests" / "speckit-pro" / "run-all.py"
    spec = importlib.util.spec_from_file_location("run_all", path)
    module = importlib.util.module_from_spec(spec)
    # Register before exec so the @dataclass in run-all.py can resolve its
    # string annotations (from __future__ import annotations) via sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


run_all = _load_run_all()


class ArgParsingTests(unittest.TestCase):
    def test_default_config_runs_deterministic_layers(self) -> None:
        config = run_all.parse_args([])
        self.assertFalse(config.live)
        self.assertFalse(config.run_all)
        self.assertIsNone(config.run_layer)
        self.assertFalse(config.verbose)

    def test_all_flag_enables_live_and_all(self) -> None:
        config = run_all.parse_args(["--all"])
        self.assertTrue(config.run_all)
        self.assertTrue(config.live)

    def test_integration_flag_selects_layer_seven(self) -> None:
        config = run_all.parse_args(["--integration"])
        self.assertEqual(config.run_layer, "7")

    def test_layer_and_live_and_verbose_flags(self) -> None:
        config = run_all.parse_args(["--layer", "4", "--live", "--verbose"])
        self.assertEqual(config.run_layer, "4")
        self.assertTrue(config.live)
        self.assertTrue(config.verbose)

    def test_unknown_flag_raises_usage_error(self) -> None:
        with self.assertRaises(run_all.UsageError):
            run_all.parse_args(["--bogus"])


class ScopeSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = run_all.load_manifest(REPO_ROOT)
        self.by_id = {layer["id"]: layer for layer in self.manifest["layers"]}

    def _runs(self, config):
        return {
            layer["id"]
            for layer in self.manifest["layers"]
            if layer["id"] != "toolchain" and run_all.layer_should_run(layer, config)
        }

    def test_default_runs_only_1_4_5(self) -> None:
        self.assertEqual(self._runs(run_all.parse_args([])), {"1", "4", "5"})

    def test_all_runs_every_runner_block_but_not_layer_8(self) -> None:
        runs = self._runs(run_all.parse_args(["--all"]))
        self.assertEqual(runs, {"1", "2", "3", "4", "5", "6", "7"})
        self.assertNotIn("8", runs)

    def test_layer_selection_is_exact(self) -> None:
        self.assertEqual(self._runs(run_all.parse_args(["--layer", "4"])), {"4"})

    def test_integration_selects_only_layer_7(self) -> None:
        self.assertEqual(self._runs(run_all.parse_args(["--integration"])), {"7"})

    def test_toolchain_runs_when_any_of_1_4_5_7_run(self) -> None:
        self.assertTrue(run_all.toolchain_should_run(self.manifest, run_all.parse_args([])))
        self.assertTrue(run_all.toolchain_should_run(self.manifest, run_all.parse_args(["--integration"])))
        self.assertFalse(run_all.toolchain_should_run(self.manifest, run_all.parse_args(["--layer", "2"])))


class SummaryParsingTests(unittest.TestCase):
    def test_parses_last_passed_summary_line(self) -> None:
        output = "noise\nvalidate-agents: 3/4 passed\ntrailing detail\n"
        self.assertEqual(run_all.parse_summary(output), (3, 4))

    def test_takes_last_when_multiple(self) -> None:
        output = "a: 1/1 passed\nb: 2/5 passed\n"
        self.assertEqual(run_all.parse_summary(output), (2, 5))

    def test_returns_none_without_summary(self) -> None:
        self.assertIsNone(run_all.parse_summary("just some output\n"))

    def test_sum_all_summaries_for_integration_layer(self) -> None:
        output = "run-dispatch-fixtures: 2/2 passed\nrun-e2e-fixtures: 1/3 passed\n"
        self.assertEqual(run_all.sum_all_summaries(output), (3, 5))


class HeadlineTests(unittest.TestCase):
    def test_passing_headline(self) -> None:
        self.assertIn("speckit-pro test suite: 10/10 passed", run_all.format_headline(10, 0))

    def test_failing_headline_includes_failed_count(self) -> None:
        line = run_all.format_headline(7, 3)
        self.assertIn("speckit-pro test suite: 7/10 passed (3 failed)", line)

    def test_exit_code_maps_from_failures(self) -> None:
        self.assertEqual(run_all.exit_code_for(0), 0)
        self.assertEqual(run_all.exit_code_for(1), 1)


class ChildDispositionTests(unittest.TestCase):
    def test_crash_without_summary_counts_as_one_failure(self) -> None:
        # No "X/Y passed" line + nonzero exit == crash -> one failed unit.
        disposition = run_all.classify_child(exit_code=2, summary=None)
        self.assertEqual(disposition, ("crash", 0, 1))

    def test_zero_exit_without_summary_is_no_summary_pass(self) -> None:
        self.assertEqual(run_all.classify_child(exit_code=0, summary=None), ("no-summary-pass", 0, 0))

    def test_summary_present_uses_counts(self) -> None:
        self.assertEqual(run_all.classify_child(exit_code=0, summary=(4, 5)), ("counted", 4, 1))


def main() -> int:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for case in (ArgParsingTests, ScopeSelectionTests, SummaryParsingTests, HeadlineTests, ChildDispositionTests):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return test_result.run_counted(suite, label="test-run-all")


if __name__ == "__main__":
    raise SystemExit(main())
