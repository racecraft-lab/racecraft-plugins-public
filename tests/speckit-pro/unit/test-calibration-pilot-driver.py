#!/usr/bin/env python3
"""Deterministic regression tests for the CAR-003 calibration-pilot driver.

The driver at ``tests/speckit-pro/layer6-efficiency/run-calibration-pilot.py``
is operator-only and makes live calls, so its pure seams had no coverage. Three
defects survived that gap and are pinned here:

* the FR-039 ``--fallback-model`` proof was tested against a SHA-256 digest
  string, so it was unconditionally true;
* the budget ceiling was checked from inside ``record_usage``, which raised
  after a live call completed but before its capture was returned, destroying
  the evidence the spend had paid for;
* the within-task correlation aligned the two arms by list position rather than
  by ``comparison_set_id``.

Every test here runs offline against pure functions. Nothing dispatches.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LIB_DIR = TEST_ROOT / "lib"
LAYER6_LIB_DIR = TEST_ROOT / "layer6-efficiency" / "lib"
for _path in (LIB_DIR, LAYER6_LIB_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

DRIVER = TEST_ROOT / "layer6-efficiency" / "run-calibration-pilot.py"

from test_result import run_counted  # noqa: E402


def load_driver():
    spec = importlib.util.spec_from_file_location("calibration_pilot_driver", DRIVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["calibration_pilot_driver"] = module
    spec.loader.exec_module(module)
    return module


driver = load_driver()


def attempt(comparison_set_id: str, arm: str, value: float) -> dict[str, object]:
    return {
        "comparison_set_id": comparison_set_id,
        "arm": arm,
        "quantities": {name: value for name in driver.VARIANCE_QUANTITIES},
    }


class FallbackModelProofTests(unittest.TestCase):
    """FR-039: the override proof must be able to witness the flag."""

    def capture(self, *, flag_absent: bool) -> dict[str, object]:
        return {
            "argv_digest": "sha256:" + "0" * 64,
            "fallback_model_flag_absent": flag_absent,
            "init": {"apiKeySource": "none"},
            "result": {},
        }

    def test_the_proof_is_false_when_the_flag_was_on_the_command_line(self) -> None:
        observed = driver.observed_environment(
            self.capture(flag_absent=False), {"alias": "haiku", "effort": "low"}
        )
        self.assertIs(observed["env_override_proof"]["fallback_model_unset"], False)

    def test_the_proof_is_true_when_the_flag_was_absent(self) -> None:
        observed = driver.observed_environment(
            self.capture(flag_absent=True), {"alias": "haiku", "effort": "low"}
        )
        self.assertIs(observed["env_override_proof"]["fallback_model_unset"], True)

    def test_the_proof_does_not_read_the_argv_digest(self) -> None:
        """A digest cannot witness a flag; both values must come from argv.

        Reading ``argv_digest`` made the proof unconditionally true, because
        ``"--fallback-model" in "sha256:<hex>"`` is false for every possible
        run — including one dispatched with the flag set.
        """
        both = {
            flag_absent: driver.observed_environment(
                self.capture(flag_absent=flag_absent), {"alias": "haiku", "effort": "low"}
            )["env_override_proof"]["fallback_model_unset"]
            for flag_absent in (True, False)
        }
        self.assertNotEqual(both[True], both[False], "the proof ignored its evidence")


class BudgetStopEvidenceTests(unittest.TestCase):
    """A ceiling stop must not destroy the capture the spend already bought."""

    def ledger(self, **envelope: object) -> object:
        base = {
            "max_attempts": 100,
            "max_duration_seconds": 10_000,
            "max_input_tokens": 100,
            "max_cache_write_tokens_by_ttl_class": {"ephemeral_5m": 10_000, "ephemeral_1h": 10_000},
            "max_cache_read_tokens": 10_000,
            "max_output_tokens": 10_000,
            "max_candidates": 8,
            "max_confirmation_entries": 8,
        }
        base.update(envelope)
        return driver.Ledger(base, candidates=2)

    def test_record_usage_accumulates_without_raising(self) -> None:
        ledger = self.ledger()
        ledger.record_usage({"input_tokens": 1_000}, 0.0)
        self.assertEqual(ledger.input_tokens, 1_000)

    def test_the_ceiling_still_stops_the_run_on_a_deferred_check(self) -> None:
        ledger = self.ledger()
        ledger.record_usage({"input_tokens": 1_000}, 0.0)
        with self.assertRaises(driver.BudgetExhausted):
            ledger.check()
        self.assertEqual(ledger.stop_reason, "max_input_tokens_ceiling_reached")

    def test_a_breaching_attempt_is_recordable_before_the_stop(self) -> None:
        """The order that matters: record, then stop.

        Checking inside ``record_usage`` raised before the caller could store
        the attempt, so the run reported one more attempt than it could show
        and a consumed objective with no attempt row.
        """
        ledger = self.ledger()
        recorded: list[str] = []
        ledger.record_usage({"input_tokens": 1_000}, 0.0)
        recorded.append("attempt-1")  # the caller stores its evidence first
        with self.assertRaises(driver.BudgetExhausted):
            ledger.check()
        self.assertEqual(recorded, ["attempt-1"])


class WithinTaskAlignmentTests(unittest.TestCase):
    """The correlation is a within-task quantity and must be task-joined."""

    def test_complete_pairs_correlate_as_before(self) -> None:
        attempts = []
        for index, (candidate, comparator) in enumerate(((1, 2), (2, 4), (3, 6)), start=1):
            attempts.append(attempt(f"CS-{index}", "candidate", candidate))
            attempts.append(attempt(f"CS-{index}", "comparator", comparator))
        estimates = driver.variance_estimates(attempts)
        self.assertEqual(estimates["pairs_used"], 3)
        self.assertEqual(estimates["within_task_pearson_correlation"]["duration_ms"], 1.0)

    def test_a_one_arm_drop_never_correlates_mismatched_tasks(self) -> None:
        """Equal list lengths are not proof of alignment.

        With CS-2 missing its comparator and CS-3 missing its candidate, the
        per-arm lists are both length three and the old equal-length guard
        passed — so CS-2's candidate was correlated against CS-3's comparator.
        Only CS-1 and CS-4 are real pairs.
        """
        attempts = [
            attempt("CS-1", "candidate", 1.0),
            attempt("CS-1", "comparator", 2.0),
            attempt("CS-2", "candidate", 2.0),
            attempt("CS-3", "comparator", 6.0),
            attempt("CS-4", "candidate", 3.0),
            attempt("CS-4", "comparator", 8.0),
        ]
        estimates = driver.variance_estimates(attempts)
        self.assertEqual(estimates["pairs_used"], 2)
        self.assertEqual(estimates["paired_within_task_difference"]["duration_ms"]["n"], 2)

    def test_pairs_used_counts_complete_pairs_only(self) -> None:
        attempts = [
            attempt("CS-1", "candidate", 1.0),
            attempt("CS-1", "comparator", 2.0),
            attempt("CS-2", "candidate", 5.0),
        ]
        self.assertEqual(driver.variance_estimates(attempts)["pairs_used"], 1)


def build_suite() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for case in (FallbackModelProofTests, BudgetStopEvidenceTests, WithinTaskAlignmentTests):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-calibration-pilot-driver"))
