#!/usr/bin/env python3
"""Unit tests for the shared test harness under tests/speckit-pro/lib/.

Covers:
  * ``test_result.CountingTestResult`` — per-assertion counting semantics
    (loop-generated ``subTest`` units AND non-loop grouped methods), the
    house-convention ``{passed}/{total}`` accounting.
Run standalone: ``python3 tests/speckit-pro/lib/test_lib.py`` — prints the
house-convention ``test_lib: {passed}/{total} passed`` summary.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

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

    def test_empty_suite_fails_closed(self) -> None:
        import io

        stream = io.StringIO()
        exit_code = test_result.run_counted(unittest.TestSuite(), label="empty", stream=stream)
        self.assertEqual(exit_code, 1)
        self.assertIn("empty: 0/0 passed", stream.getvalue())

    def test_skipped_suite_unit_is_not_reported_as_passed(self) -> None:
        import io

        class _Skipped(unittest.TestCase):
            @unittest.skip("not executable in this environment")
            def test_required_behavior(self) -> None:
                self.fail("skip must prevent execution")

        stream = io.StringIO()
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(_Skipped)
        exit_code = test_result.run_counted(suite, label="skipped", stream=stream)
        self.assertEqual(exit_code, 1)
        self.assertIn("skipped: 0/1 passed", stream.getvalue())


class SpecsReadGuardTests(unittest.TestCase):
    """The guard that keeps a shipped test from depending on a folder archive deletes."""

    def test_the_guard_distinguishes_reading_a_specs_path_from_naming_one(self) -> None:
        # One process installs one irremovable audit hook, so this exercises the
        # hook already installed by this suite's own run_counted rather than
        # installing a second one.
        import os
        from pathlib import Path

        test_result.install_specs_read_guard()
        repo_root = Path(__file__).resolve().parents[3]
        live = repo_root / "specs"

        # Naming one is data, and stays legal: the fixtures across this suite
        # assert `specs/<feature>/...` strings because that is the shape a real
        # run produces.
        named = f"{live}/some-feature/spec.md"
        self.assertTrue(named.endswith("spec.md"))
        # So is asking whether it exists. Archive makes that answer False; it
        # does not make it raise.
        self.assertFalse(Path(named).exists())
        self.assertTrue(str(Path(named).resolve()).endswith("spec.md"))

        # Opening one is not. The hook raises on the `open` event, before the
        # call reaches the filesystem, so the path need not exist and nothing is
        # created, opened or left to clean up.
        probe = live / "some-feature" / "spec.md"
        with self.assertRaises(AssertionError) as caught:
            with open(os.fspath(probe), encoding="utf-8"):
                self.fail("the guard must raise before the file is opened")
        self.assertIn("a test read a live specs/ path", str(caught.exception))
        self.assertIn("fixtures/", str(caught.exception))
        self.assertFalse(probe.exists(), "the guard must not create the path")

        # A path outside `specs/` is untouched.
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as handle:
            handle.write("ordinary\n")
            outside = handle.name
        try:
            with open(outside, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "ordinary\n")
        finally:
            os.unlink(outside)


class FailureReportTests(unittest.TestCase):
    """``failure_report`` names every failing unit and bounds each traceback."""

    @staticmethod
    def _traceback(test_id: str, length: int) -> list[str]:
        lines = ["Traceback (most recent call last):"]
        lines += [f'  File "child.py", line {index}, in {test_id}' for index in range(1, length - 1)]
        lines.append(f"AssertionError: {test_id} broke")
        return lines

    def test_each_failure_keeps_its_id_and_a_bounded_tail(self) -> None:
        tail = test_result.FAILURE_TAIL_LINES
        long_body = self._traceback("test_long", tail + 20)
        short_body = self._traceback("test_short", 4)
        stderr = "\n".join(
            ["child warning printed while tests ran"]
            + ["child FAILED test_long (child.Case.test_long)"]
            + long_body
            + ["child FAILED test_short (child.Case.test_short)"]
            + short_body
        ) + "\n"
        report = test_result.failure_report("child: 1/3 passed\n" + stderr, "child")
        lines = report.splitlines()
        self.assertIn("child FAILED test_long (child.Case.test_long)", lines)
        self.assertIn("child FAILED test_short (child.Case.test_short)", lines)
        self.assertIn("AssertionError: test_long broke", lines)
        self.assertIn("  ... 20 earlier lines omitted", lines)
        self.assertNotIn(long_body[0], lines[: lines.index("child FAILED test_short (child.Case.test_short)")])
        self.assertEqual(lines[-len(short_body):], short_body)
        self.assertNotIn("child warning printed while tests ran", lines)
        self.assertNotIn("child: 1/3 passed", lines)
        self.assertLessEqual(len(lines), 2 * (tail + 2))

    def test_output_without_failure_headers_falls_back_to_a_bounded_tail(self) -> None:
        tail = test_result.FAILURE_TAIL_LINES
        crash = [f"crash line {index}" for index in range(tail + 5)]
        report = test_result.failure_report("\n".join(crash) + "\n", "child")
        self.assertEqual(report.splitlines(), ["  ... 5 earlier lines omitted", *crash[-tail:]])
        self.assertEqual(test_result.failure_report("", "child"), "")

    def test_run_counted_emits_headers_the_report_reads(self) -> None:
        import contextlib
        import io

        stderr = io.StringIO()
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(_Sample)
        with contextlib.redirect_stderr(stderr):
            test_result.run_counted(suite, label="sample", stream=io.StringIO())
        report = test_result.failure_report(stderr.getvalue(), "sample")
        headers = [line for line in report.splitlines() if line.startswith("sample FAILED ")]
        self.assertTrue(any(line.endswith("._Sample.test_plain_fail") for line in headers), headers)
        self.assertTrue(any("._Sample.test_loop" in line for line in headers), headers)
        self.assertIn("gamma check", report)
        self.assertIn("AssertionError: 2 != 3", report)


def main() -> int:
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    suite.addTests(loader.loadTestsFromTestCase(CountingTestResultTests))
    suite.addTests(loader.loadTestsFromTestCase(SpecsReadGuardTests))
    suite.addTests(loader.loadTestsFromTestCase(FailureReportTests))
    return test_result.run_counted(suite, label="test_lib")


if __name__ == "__main__":
    raise SystemExit(main())
