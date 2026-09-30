#!/usr/bin/env python3
"""Golden-fixture tests for the estimate-spec-size runner operation.

Each fixture under ``fixtures/estimate-spec-size/`` holds the runner ``inputs``
a skill sends and the estimator result they must produce. The runner is
exercised end-to-end through the same request envelope the grill-me and
speckit-prd skills send (``PYTHONPATH=speckit-pro python3 -m speckit_pro_runner``
with a single JSON request on stdin).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "estimate-spec-size"
SHARED_LIB = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from runner_invocation import run_runner  # noqa: E402
from test_result import run_counted  # noqa: E402

SPIKE_RESULT = {"estimated_loc": 0, "suggested_slices": 1, "status": "ok"}


def run_estimator(inputs: dict[str, object], request_id: str = "test-estimate-spec-size") -> tuple[int, dict]:
    request = {
        "schema_version": "1.0",
        "request_id": request_id,
        "helper_id": "estimate-spec-size",
        "operation": "estimate-spec-size",
        "mode": "read_only",
        "inputs": inputs,
    }
    completed, response, _ = run_runner(request, extra_env={"PYTHONDONTWRITEBYTECODE": "1"})
    return completed.returncode, response


def estimate(test: unittest.TestCase, inputs: dict[str, object], *, context: str) -> dict:
    """The estimator result for ``inputs``; the runner never blocks on an estimate, even a warning."""
    returncode, response = run_estimator(inputs, request_id=f"test-{context}")
    test.assertEqual(returncode, 0, f"{context}: runner exit code; response={response!r}")
    return response["data"]["stdout_json"]


def golden_cases() -> list[tuple[str, dict[str, object], dict]]:
    cases = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        cases.append((path.stem, fixture["inputs"], fixture["expected"]))
    return cases


class EstimateSpecSizeGoldenTests(unittest.TestCase):
    def test_every_golden_fixture_produces_its_expected_result(self) -> None:
        cases = golden_cases()
        self.assertTrue(cases, "no estimate-spec-size golden fixtures discovered")
        for name, inputs, expected in cases:
            with self.subTest(msg=f"fixture '{name}' → expected result"):
                self.assertEqual(estimate(self, inputs, context=name), expected)

    def test_repeated_inputs_give_byte_identical_output(self) -> None:
        for label, inputs in (("typical", {"user_stories": "2", "files": "3", "frs": "4"}), ("over-ceiling", {"files": "11"})):
            with self.subTest(msg=f"repeated {label} inputs → byte-identical stdout"):
                _, first = run_estimator(inputs, request_id=f"determinism-{label}-a")
                _, second = run_estimator(inputs, request_id=f"determinism-{label}-b")
                self.assertEqual(first["data"]["stdout_json"], second["data"]["stdout_json"])
                self.assertEqual(first["data"]["stdout"]["text"], second["data"]["stdout"]["text"])

    def test_ceiling_and_slice_boundaries(self) -> None:
        for label, inputs, loc, status, slices in (
            ("estimated_loc == ceiling", {"files": "10"}, 400, "ok", None),
            ("strictly over ceiling", {"files": "11"}, 440, "warn", 2),
            ("800 LOC", {"files": "20"}, 800, None, 2),
            ("under ceiling", {"user_stories": "2", "files": "3", "frs": "4"}, None, None, 1),
        ):
            with self.subTest(msg=label):
                result = estimate(self, inputs, context=label)
                for key, expected in (("estimated_loc", loc), ("status", status), ("suggested_slices", slices)):
                    if expected is not None:
                        self.assertEqual(result[key], expected)

    def test_spike_overrides_every_other_signal(self) -> None:
        for label, inputs in (
            ("--spike alone", {"spike": True}),
            ("--spike overrides large signals", {"user_stories": "99", "files": "99", "frs": "99", "spike": True}),
        ):
            with self.subTest(msg=label):
                self.assertEqual(estimate(self, inputs, context=label), SPIKE_RESULT)

    def test_absent_and_malformed_signals_normalize_to_zero(self) -> None:
        for label, inputs, loc in (
            ("no signals", {}, 0),
            ("malformed, negative and decimal signals", {"user_stories": "abc", "files": "-5", "frs": "3.5"}, 0),
            ("mixed valid and bad keeps the valid signal", {"user_stories": "4", "files": "abc", "frs": "-2"}, 100),
        ):
            with self.subTest(msg=label):
                result = estimate(self, inputs, context=label)
                self.assertEqual((result["estimated_loc"], result["status"]), (loc, "ok"))

    def test_status_is_always_ok_or_warn_across_an_input_sweep(self) -> None:
        sweep = (
            {}, {"files": "10"}, {"files": "11"}, {"files": "20"},
            {"user_stories": "2", "files": "3", "frs": "4"},
            {"files": "10", "new_vs_modify": "modify"},
            {"spike": True},
            {"user_stories": "99", "files": "99", "frs": "99", "spike": True},
            {"user_stories": "abc", "files": "-5", "frs": "3.5"},
            {"user_stories": "4", "files": "abc", "frs": "-2"},
        )
        for inputs in sweep:
            with self.subTest(inputs=inputs):
                self.assertIn(estimate(self, inputs, context="status sweep")["status"], {"ok", "warn"})


def main() -> int:
    return run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(EstimateSpecSizeGoldenTests),
        label="test-estimate-spec-size",
    )


if __name__ == "__main__":
    raise SystemExit(main())
