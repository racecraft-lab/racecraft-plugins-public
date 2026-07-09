#!/usr/bin/env python3
"""Golden-fixture tests for the restored estimate-spec-size runner operation.

XPLAT-010 US7 / FR-025. The Bash predecessor
(speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh) was deleted by
XPLAT-009 without a Python port; this suite pins the restored read-only runner
operation against the frozen golden fixtures under
``fixtures/estimate-spec-size/`` — ``<name>.args`` (one line of the deleted
script's CLI flags) paired with ``<name>.json`` (its exact compact stdout).

This is a born-Python test: there is no live Bash baseline to capture (the
subject was deleted), so the count-parity dual-run protocol does not apply. The
golden ``(.args -> .json)`` pairs are the authoritative oracle. The runner is
exercised end-to-end through the same request envelope the grill-me and
speckit-prd skills send (``PYTHONPATH=speckit-pro python3 -m speckit_pro_runner``
with a single JSON request on stdin).
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "estimate-spec-size"

# Maps the deleted script's value-taking flags onto the runner's structured
# input keys; --spike is a bare boolean flag handled separately.
FLAG_TO_INPUT = {
    "--user-stories": "user_stories",
    "--files": "files",
    "--frs": "frs",
    "--new-vs-modify": "new_vs_modify",
}


def runner_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(PLUGIN_ROOT) if not existing else f"{PLUGIN_ROOT}{os.pathsep}{existing}"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def parse_args_to_inputs(arg_line: str) -> dict[str, object]:
    """Convert a golden ``.args`` CLI line into the runner ``inputs`` dict.

    Values are kept verbatim as strings (exactly as the deleted Bash saw its
    positional tokens) so the estimator's lenient coercion path — negative,
    decimal, and non-numeric signals normalizing to 0 — is exercised for real.
    """
    tokens = shlex.split(arg_line)
    inputs: dict[str, object] = {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "--spike":
            inputs["spike"] = True
            index += 1
        elif token in FLAG_TO_INPUT:
            value = tokens[index + 1] if index + 1 < len(tokens) else ""
            inputs[FLAG_TO_INPUT[token]] = value
            index += 2
        else:
            index += 1
    return inputs


def run_estimator(inputs: dict[str, object], request_id: str = "test-estimate-spec-size") -> tuple[int, dict]:
    request = {
        "schema_version": "1.0",
        "request_id": request_id,
        "helper_id": "estimate-spec-size",
        "operation": "estimate-spec-size",
        "mode": "read_only",
        "inputs": inputs,
    }
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        env=runner_env(),
        shell=False,
        check=False,
    )
    response = json.loads(completed.stdout) if completed.stdout.strip() else {}
    return completed.returncode, response


def golden_pairs() -> list[tuple[str, dict[str, object], dict]]:
    pairs: list[tuple[str, dict[str, object], dict]] = []
    for args_file in sorted(FIXTURE_DIR.glob("*.args")):
        name = args_file.stem
        arg_line = args_file.read_text(encoding="utf-8").splitlines()[:1]
        inputs = parse_args_to_inputs(arg_line[0] if arg_line else "")
        expected = json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))
        pairs.append((name, inputs, expected))
    return pairs


class EstimateSpecSizeGoldenTests(unittest.TestCase):
    def test_golden_fixtures_match_exactly(self) -> None:
        pairs = golden_pairs()
        self.assertTrue(pairs, "no estimate-spec-size golden fixtures discovered")
        for name, inputs, expected in pairs:
            with self.subTest(fixture=name):
                returncode, response = run_estimator(inputs, request_id=f"test-{name}")
                # Advisory-only: the runner never blocks on an estimate, even warn.
                self.assertEqual(returncode, 0, f"{name}: runner exit code")
                self.assertEqual(response.get("status"), "ok", f"{name}: envelope status")
                result = response["data"]["stdout_json"]
                self.assertEqual(result, expected, f"{name}: estimator result triple")

    def test_status_is_only_ok_or_warn(self) -> None:
        for name, inputs, _expected in golden_pairs():
            with self.subTest(fixture=name):
                _returncode, response = run_estimator(inputs, request_id=f"test-status-{name}")
                status = response["data"]["stdout_json"]["status"]
                self.assertIn(status, {"ok", "warn"}, f"{name}: status enum")

    def test_boundary_at_ceiling_ok_over_ceiling_warn(self) -> None:
        cases = [
            ("--files 10", {"estimated_loc": 400, "status": "ok"}),
            ("--files 11", {"estimated_loc": 440, "status": "warn"}),
        ]
        for arg_line, expected in cases:
            with self.subTest(args=arg_line):
                _returncode, response = run_estimator(parse_args_to_inputs(arg_line))
                result = response["data"]["stdout_json"]
                self.assertEqual(result["estimated_loc"], expected["estimated_loc"])
                self.assertEqual(result["status"], expected["status"])

    def test_repeated_inputs_are_deterministic(self) -> None:
        inputs = parse_args_to_inputs("--user-stories 2 --files 3 --frs 4")
        with self.subTest(sample="typical-under"):
            _rc1, first = run_estimator(inputs, request_id="determinism-a")
            _rc2, second = run_estimator(inputs, request_id="determinism-b")
            self.assertEqual(first["data"]["stdout_json"], second["data"]["stdout_json"])
            self.assertEqual(first["data"]["stdout"]["text"], second["data"]["stdout"]["text"])


class CountingResult(unittest.TextTestResult):
    """Counts each executed subTest (and each non-subTest method) as one unit.

    New XPLAT-010 ports must count assertion units rather than printing bare
    ``result.testsRun``; this suite groups its checks into subTests, so the
    denominator is the number of subTests executed, not the four method names.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.units_passed = 0
        self.units_failed = 0
        self._subtests_in_current = 0

    def startTest(self, test: unittest.TestCase) -> None:
        super().startTest(test)
        self._subtests_in_current = 0

    def addSubTest(self, test, subtest, outcome) -> None:  # type: ignore[no-untyped-def]
        super().addSubTest(test, subtest, outcome)
        self._subtests_in_current += 1
        if outcome is None:
            self.units_passed += 1
        else:
            self.units_failed += 1

    def addSuccess(self, test: unittest.TestCase) -> None:
        super().addSuccess(test)
        if self._subtests_in_current == 0:
            self.units_passed += 1

    def addFailure(self, test, err) -> None:  # type: ignore[no-untyped-def]
        super().addFailure(test, err)
        if self._subtests_in_current == 0:
            self.units_failed += 1

    def addError(self, test, err) -> None:  # type: ignore[no-untyped-def]
        super().addError(test, err)
        if self._subtests_in_current == 0:
            self.units_failed += 1


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EstimateSpecSizeGoldenTests)
    result = unittest.TextTestRunner(resultclass=CountingResult, verbosity=1).run(suite)
    total = result.units_passed + result.units_failed
    print(f"test-estimate-spec-size: {result.units_passed}/{total} passed")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
