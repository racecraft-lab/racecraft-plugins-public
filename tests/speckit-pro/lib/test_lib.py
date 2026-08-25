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

import copy
import sys
import tempfile
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import capture_baseline  # noqa: E402
import test_result  # noqa: E402
import treatment_fixture_helpers  # noqa: E402


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


class SpecsReadGuardTests(unittest.TestCase):
    """The guard that keeps a shipped test from depending on a folder archive deletes."""

    def test_the_guard_distinguishes_reading_a_specs_path_from_naming_one(self) -> None:
        # One process installs one irremovable audit hook, so this exercises the
        # hook already installed by this suite's own run_counted rather than
        # installing a second one.
        import os
        import tempfile
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

        # Opening one is not.
        probe = live / ".specs-read-guard-probe"
        probe.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.assertRaises(AssertionError) as caught:
                open(os.fspath(probe), "w")
            self.assertIn("a test read a live specs/ path", str(caught.exception))
            self.assertIn("fixtures/", str(caught.exception))
        finally:
            if probe.exists():
                probe.unlink()

        # A path outside `specs/` is untouched.
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as handle:
            handle.write("ordinary\n")
            outside = handle.name
        try:
            with open(outside, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "ordinary\n")
        finally:
            os.unlink(outside)


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


class TreatmentFixtureHelpersTests(unittest.TestCase):
    @staticmethod
    def _bundle() -> dict:
        return {
            "treatment_traces": [
                {
                    "context": {"turnId": "turn-fixture-success"},
                    "controlled_environment_id": "environment-success",
                    "objective_binding": {
                        "execution_trace_id": "execution-success",
                        "route_resolution_id": "route-success",
                    },
                    "reroute_destination_assessments": [
                        {"prequalification_evidence_id": "qualification-success"},
                        {"prequalification_evidence_id": None},
                    ],
                    "treatment_disposition": "accepted",
                },
                {
                    "context": {"turnId": "turn-fixture-misdelivery"},
                    "controlled_environment_id": "environment-misdelivery",
                    "objective_binding": {
                        "execution_trace_id": "execution-misdelivery",
                        "route_resolution_id": "route-misdelivery",
                    },
                    "reroute_destination_assessments": [
                        {"prequalification_evidence_id": "qualification-misdelivery"},
                    ],
                    "treatment_disposition": "hard_fail",
                },
            ],
            "controlled_environments": [
                {"controlled_environment_id": "environment-success"},
                {"controlled_environment_id": "environment-misdelivery"},
            ],
            "route_resolutions": [
                {"route_resolution_id": "route-success"},
                {"route_resolution_id": "route-misdelivery"},
            ],
            "qualification_evidence_registry": [
                {"qualification_evidence_id": "qualification-success"},
                {"qualification_evidence_id": "qualification-misdelivery"},
                {"qualification_evidence_id": None},
            ],
            "fixture_provenance": {
                "expected_dispositions": [{"existing": "value"}],
                "source": "fixture",
            },
        }

    def test_replay_trace_selects_case_by_fixture_turn_id(self) -> None:
        bundle = self._bundle()
        trace = treatment_fixture_helpers.replay_trace(bundle, "TRACE-MISDELIVERY")
        self.assertIs(trace, bundle["treatment_traces"][1])

    def test_single_case_deep_copies_without_mutating_input(self) -> None:
        bundle = self._bundle()
        original = copy.deepcopy(bundle)
        isolated = treatment_fixture_helpers.single_treatment_case(bundle, "TRACE-SUCCESS")

        self.assertEqual(bundle, original)
        self.assertIsNot(isolated, bundle)
        self.assertIsNot(isolated["treatment_traces"][0], bundle["treatment_traces"][0])

    def test_single_case_filters_environment_route_and_qualification(self) -> None:
        isolated = treatment_fixture_helpers.single_treatment_case(
            self._bundle(), "TRACE-SUCCESS",
        )

        self.assertEqual(
            [item["controlled_environment_id"] for item in isolated["controlled_environments"]],
            ["environment-success"],
        )
        self.assertEqual(
            [item["route_resolution_id"] for item in isolated["route_resolutions"]],
            ["route-success"],
        )
        self.assertEqual(
            [
                item["qualification_evidence_id"]
                for item in isolated["qualification_evidence_registry"]
            ],
            ["qualification-success"],
        )

    def test_single_case_excludes_none_qualification_reference(self) -> None:
        isolated = treatment_fixture_helpers.single_treatment_case(
            self._bundle(), "TRACE-SUCCESS",
        )
        qualification_ids = {
            item["qualification_evidence_id"]
            for item in isolated["qualification_evidence_registry"]
        }
        self.assertNotIn(None, qualification_ids)

    def test_single_case_sets_exact_expected_disposition(self) -> None:
        isolated = treatment_fixture_helpers.single_treatment_case(
            self._bundle(), "TRACE-SUCCESS",
        )
        self.assertEqual(
            isolated["fixture_provenance"]["expected_dispositions"],
            [{
                "execution_trace_id": "execution-success",
                "treatment_disposition": "accepted",
            }],
        )


def main() -> int:
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    suite.addTests(loader.loadTestsFromTestCase(CountingTestResultTests))
    suite.addTests(loader.loadTestsFromTestCase(SpecsReadGuardTests))
    suite.addTests(loader.loadTestsFromTestCase(CaptureBaselineParseTests))
    suite.addTests(loader.loadTestsFromTestCase(TreatmentFixtureHelpersTests))
    return test_result.run_counted(suite, label="test-lib")


if __name__ == "__main__":
    raise SystemExit(main())
