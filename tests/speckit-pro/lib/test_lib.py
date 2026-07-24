#!/usr/bin/env python3
"""Unit tests for the shared XPLAT-010 parity harness under tests/speckit-pro/lib/.

Covers:
  * ``test_result.CountingTestResult`` — per-assertion counting semantics
    (loop-generated ``subTest`` units AND non-loop grouped methods), the
    house-convention ``{passed}/{total}`` accounting (FR-010, Clarifications
    Session 1, count-parity contract §3).
  * ``capture_baseline`` — the ``^\\s*(.+?)\\s\\.\\.\\.\\s(PASS|FAIL)$`` parse
    filter, strict frozen-inventory reads, the ``NNN <name>`` + ``TOTAL: <N>``
    render, fail-loud on an empty/stale name, and the pinned non-root capture
    environment (FR-011, count-parity contract §1/§2).

Run standalone: ``python3 tests/speckit-pro/lib/test_lib.py`` — prints the
house-convention ``test-lib: {passed}/{total} passed`` summary.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import capture_baseline  # noqa: E402
import test_result  # noqa: E402


class _Sample(unittest.TestCase):
    """A fixture case exercising both looped subTests and plain methods."""

    def test_loop(self) -> None:
        for name, ok in (("alpha check", True), ("beta check", True), ("gamma check", False)):
            with self.subTest(msg=name):
                self.assertTrue(ok)

    def test_plain_pass(self) -> None:
        self.assertEqual(1 + 1, 2)

    def test_plain_fail(self) -> None:
        self.assertEqual(1 + 1, 3)


class CountingTestResultTests(unittest.TestCase):
    def _run_sample(self) -> test_result.CountingTestResult:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(_Sample)
        result = test_result.CountingTestResult(stream=None, descriptions=False, verbosity=0)
        suite(result)
        return result

    def test_counts_each_assertion_execution_as_one_unit(self) -> None:
        result = self._run_sample()
        # 3 subTest units (test_loop) + 1 plain pass + 1 plain fail = 5 total.
        self.assertEqual(result.units_total, 5)
        # 2 subTest passes + 1 plain pass = 3 passed.
        self.assertEqual(result.units_passed, 3)

    def test_bare_testsrun_undercounts_relative_to_units(self) -> None:
        result = self._run_sample()
        # stdlib testsRun counts 3 methods; the subTest loop hides its units.
        self.assertEqual(result.testsRun, 3)
        self.assertGreater(result.units_total, result.testsRun)

    def test_reconciles_subtest_names_one_to_one(self) -> None:
        result = self._run_sample()
        self.assertEqual(result.subtest_names, ["alpha check", "beta check", "gamma check"])

    def test_run_counted_prints_house_summary_and_returns_exit_code(self) -> None:
        import io

        stream = io.StringIO()
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(_Sample)
        exit_code = test_result.run_counted(suite, label="sample", stream=stream)
        self.assertEqual(exit_code, 1)  # a failing unit -> nonzero
        self.assertIn("sample: 3/5 passed", stream.getvalue())

        class _FailsAfterSubtests(unittest.TestCase):
            def test_failure_after_subtests(self) -> None:
                for token in ("x", "y"):
                    with self.subTest(msg=token):
                        self.assertTrue(token)
                self.fail("method-level failure after successful subtests")

        stream = io.StringIO()
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(_FailsAfterSubtests)
        exit_code = test_result.run_counted(suite, label="late-failure", stream=stream)
        self.assertEqual(exit_code, 1)
        self.assertIn("late-failure: 2/3 passed", stream.getvalue())

    def test_all_pass_suite_reports_zero_exit(self) -> None:
        import io

        class _AllPass(unittest.TestCase):
            def test_a(self) -> None:
                self.assertTrue(True)

            def test_b(self) -> None:
                for token in ("x", "y"):
                    with self.subTest(msg=token):
                        self.assertTrue(token)

        stream = io.StringIO()
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(_AllPass)
        exit_code = test_result.run_counted(suite, label="allpass", stream=stream)
        self.assertEqual(exit_code, 0)
        self.assertIn("allpass: 3/3 passed", stream.getvalue())


class CaptureBaselineParseTests(unittest.TestCase):
    def test_inventory_preserves_order_and_duplicate_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            baseline = Path(temporary) / "baseline.txt"
            baseline.write_text("001 alpha\n002 café\n003 alpha\nTOTAL: 3\n", encoding="utf-8")
            self.assertEqual(capture_baseline.baseline_inventory(baseline), ["alpha", "café", "alpha"])

    def test_inventory_total_mismatch_raises_exact_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            baseline = Path(temporary) / "baseline.txt"
            baseline.write_text("001 alpha\nTOTAL: 2\n", encoding="utf-8")
            with self.assertRaises(AssertionError) as context:
                capture_baseline.baseline_inventory(baseline)
            self.assertEqual(str(context.exception), "baseline TOTAL 2 does not match 1 names")

    def test_inventory_missing_file_raises_file_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(FileNotFoundError):
                capture_baseline.baseline_inventory(Path(temporary) / "missing.txt")

    def test_inventory_malformed_line_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            baseline = Path(temporary) / "baseline.txt"
            baseline.write_text("malformed\nTOTAL: 1\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                capture_baseline.baseline_inventory(baseline)

    def test_inventory_malformed_total_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            baseline = Path(temporary) / "baseline.txt"
            baseline.write_text("001 alpha\nTOTAL: not-an-int\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                capture_baseline.baseline_inventory(baseline)

    def test_parses_only_verbose_pass_fail_lines_in_order(self) -> None:
        text = (
            "Running validate-agents...\n"
            "  frontmatter present ... PASS\n"
            "some interleaved detail: skipped\n"
            "  frontmatter present ... PASS\n"
            "  description non-empty ... FAIL\n"
            "validate-agents: 2/3 passed\n"
        )
        parsed = capture_baseline.parse_verbose_lines(text)
        self.assertEqual(
            parsed,
            [
                ("frontmatter present", "PASS"),
                ("frontmatter present", "PASS"),
                ("description non-empty", "FAIL"),
            ],
        )

    def test_discards_non_matching_and_interleaved_lines(self) -> None:
        text = "PASS without dots\n  name ... PENDING\n  real check ... PASS\n"
        parsed = capture_baseline.parse_verbose_lines(text)
        self.assertEqual(parsed, [("real check", "PASS")])

    def test_fails_loud_on_empty_name(self) -> None:
        with self.assertRaises(capture_baseline.BaselineError):
            capture_baseline.parse_verbose_lines("   ... PASS\n")

    def test_render_baseline_uses_frozen_ordinal_and_total_format(self) -> None:
        rendered = capture_baseline.render_baseline(
            [
                ("validate frontmatter present", "PASS"),
                ("validate frontmatter present", "PASS"),
                ("description field non-empty", "FAIL"),
            ]
        )
        self.assertEqual(
            rendered,
            "001 validate frontmatter present\n"
            "002 validate frontmatter present\n"
            "003 description field non-empty\n"
            "TOTAL: 3\n",
        )

    def test_render_baseline_empty_is_total_zero(self) -> None:
        self.assertEqual(capture_baseline.render_baseline([]), "TOTAL: 0\n")

    def test_capture_environment_records_non_root_pin(self) -> None:
        env = capture_baseline.capture_environment()
        self.assertIn("is_root", env)
        self.assertIn("python_version", env)
        self.assertIn("platform", env)
        self.assertIsInstance(env["is_root"], bool)


def main() -> int:
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    suite.addTests(loader.loadTestsFromTestCase(CountingTestResultTests))
    suite.addTests(loader.loadTestsFromTestCase(CaptureBaselineParseTests))
    return test_result.run_counted(suite, label="test-lib")


if __name__ == "__main__":
    raise SystemExit(main())
