#!/usr/bin/env python3
"""Golden-fixture tests for the restored estimate-spec-size runner operation.

XPLAT-010 US7 / FR-025. The historical Bash predecessor was captured from
commit ``c9176902`` and reported 33 named checks. This suite preserves that
ordered inventory with ``subTest(msg=...)`` while exercising the restored
read-only runner operation against the frozen golden fixtures under
``fixtures/estimate-spec-size/``.

The runner is exercised end-to-end through the same request envelope the
grill-me and speckit-prd skills send
(``PYTHONPATH=speckit-pro python3 -m speckit_pro_runner`` with a single JSON
request on stdin).
"""

from __future__ import annotations

import json
import io
import os
import shlex
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "estimate-spec-size"
BASELINE = REPO_ROOT / "tests" / "speckit-pro" / "parity" / "xplat-010" / "test-estimate-spec-size-baseline.txt"

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


def assert_estimator_exit(
    test: unittest.TestCase,
    returncode: int,
    response: dict,
    *,
    context: str,
) -> None:
    test.assertEqual(returncode, 0, f"{context}: runner exit code; response={response!r}")


def golden_pairs() -> list[tuple[str, dict[str, object], dict]]:
    pairs: list[tuple[str, dict[str, object], dict]] = []
    for args_file in sorted(FIXTURE_DIR.glob("*.args")):
        name = args_file.stem
        arg_line = args_file.read_text(encoding="utf-8").splitlines()[:1]
        inputs = parse_args_to_inputs(arg_line[0] if arg_line else "")
        expected = json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))
        pairs.append((name, inputs, expected))
    return pairs


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


CURRENT_INVENTORY = [
    "fixture 'all-absent' → exit 0",
    "fixture 'all-absent' → expected JSON",
    "fixture 'at-ceiling' → exit 0",
    "fixture 'at-ceiling' → expected JSON",
    "fixture 'bad-input' → exit 0",
    "fixture 'bad-input' → expected JSON",
    "fixture 'mixed-valid-bad' → exit 0",
    "fixture 'mixed-valid-bad' → expected JSON",
    "fixture 'modify-discount' → exit 0",
    "fixture 'modify-discount' → expected JSON",
    "fixture 'multi-slice' → exit 0",
    "fixture 'multi-slice' → expected JSON",
    "fixture 'over-ceiling' → exit 0",
    "fixture 'over-ceiling' → expected JSON",
    "fixture 'spike-precedence' → exit 0",
    "fixture 'spike-precedence' → expected JSON",
    "fixture 'spike' → exit 0",
    "fixture 'spike' → expected JSON",
    "fixture 'typical-under' → exit 0",
    "fixture 'typical-under' → expected JSON",
    "repeated identical inputs → byte-identical stdout",
    "second determinism sample (over-ceiling) → byte-identical stdout",
    "estimated_loc == ceiling → status ok",
    "strictly over ceiling → status warn",
    "--spike → {estimated_loc:0, suggested_slices:1, status:ok}",
    "--spike overrides large signals (spike precedence)",
    "no arguments → estimated_loc 0, status ok, exit 0",
    "malformed/negative/decimal signals normalize to 0",
    "mixed valid + bad keeps valid signals",
    "status is always ok or warn across an input sweep",
    "under ceiling → 1 slice",
    "440 LOC → 2 slices",
    "800 LOC → 2 slices",
]


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(EstimateSpecSizeGoldenTests)


class CountingTestResult(unittest.TextTestResult):
    """Self-contained counter used before PR 2 introduces the shared helper."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.units_total = 0
        self.units_passed = 0
        self.subtest_names: list[str] = []

    def addSubTest(self, test, subtest, outcome) -> None:  # type: ignore[no-untyped-def]
        super().addSubTest(test, subtest, outcome)
        self.units_total += 1
        if outcome is None:
            self.units_passed += 1
        self.subtest_names.append(str(getattr(subtest, "_message", "<subtest>")))


def run_counted(suite: unittest.TestSuite, *, label: str) -> int:
    result = unittest.TextTestRunner(
        stream=io.StringIO(),
        resultclass=CountingTestResult,
        verbosity=0,
    ).run(suite)
    print(f"{label}: {result.units_passed}/{result.units_total} passed")
    return 0 if result.wasSuccessful() and result.units_passed == result.units_total else 1


def assert_subtest_inventory_matches_baseline() -> None:
    result = unittest.TextTestRunner(
        stream=io.StringIO(),
        resultclass=CountingTestResult,
        verbosity=0,
    ).run(build_suite())
    expected = baseline_inventory(BASELINE)
    if result.subtest_names != expected:
        raise AssertionError(
            "subTest inventory does not match baseline: "
            f"python={len(result.subtest_names)} baseline={len(expected)}"
        )


class EstimateSpecSizeGoldenTests(unittest.TestCase):
    def test_estimator_contract_matches_historical_predecessor(self) -> None:
        self.assertEqual(baseline_inventory(BASELINE), CURRENT_INVENTORY)
        expected_fixture_names = [
            "all-absent",
            "at-ceiling",
            "bad-input",
            "mixed-valid-bad",
            "modify-discount",
            "multi-slice",
            "over-ceiling",
            "spike-precedence",
            "spike",
            "typical-under",
        ]
        pairs = golden_pairs()
        self.assertTrue(pairs, "no estimate-spec-size golden fixtures discovered")
        self.assertEqual([name for name, _inputs, _expected in pairs], expected_fixture_names)

        names = iter(CURRENT_INVENTORY)

        def next_name(expected: str) -> str:
            name = next(names)
            self.assertEqual(name, expected)
            return name

        for name, inputs, expected in pairs:
            returncode, response = run_estimator(inputs, request_id=f"test-{name}")
            with self.subTest(msg=next_name(f"fixture '{name}' → exit 0")):
                # Advisory-only: the runner never blocks on an estimate, even warn.
                self.assertEqual(returncode, 0, f"{name}: runner exit code")
            with self.subTest(msg=next_name(f"fixture '{name}' → expected JSON")):
                self.assertEqual(response.get("status"), "ok", f"{name}: envelope status")
                result = response["data"]["stdout_json"]
                self.assertEqual(result, expected, f"{name}: estimator result triple")

        inputs = parse_args_to_inputs("--user-stories 2 --files 3 --frs 4")
        with self.subTest(msg=next_name("repeated identical inputs → byte-identical stdout")):
            rc1, first = run_estimator(inputs, request_id="determinism-a")
            rc2, second = run_estimator(inputs, request_id="determinism-b")
            assert_estimator_exit(self, rc1, first, context="determinism-a")
            assert_estimator_exit(self, rc2, second, context="determinism-b")
            self.assertEqual(first["data"]["stdout_json"], second["data"]["stdout_json"])
            self.assertEqual(first["data"]["stdout"]["text"], second["data"]["stdout"]["text"])

        over_ceiling_inputs = parse_args_to_inputs("--files 11")
        with self.subTest(msg=next_name("second determinism sample (over-ceiling) → byte-identical stdout")):
            rc1, first = run_estimator(over_ceiling_inputs, request_id="determinism-over-a")
            rc2, second = run_estimator(over_ceiling_inputs, request_id="determinism-over-b")
            assert_estimator_exit(self, rc1, first, context="determinism-over-a")
            assert_estimator_exit(self, rc2, second, context="determinism-over-b")
            self.assertEqual(first["data"]["stdout_json"], second["data"]["stdout_json"])
            self.assertEqual(first["data"]["stdout"]["text"], second["data"]["stdout"]["text"])

        with self.subTest(msg=next_name("estimated_loc == ceiling → status ok")):
            returncode, response = run_estimator(parse_args_to_inputs("--files 10"))
            assert_estimator_exit(self, returncode, response, context="estimated_loc == ceiling")
            result = response["data"]["stdout_json"]
            self.assertEqual(result["estimated_loc"], 400)
            self.assertEqual(result["status"], "ok")

        with self.subTest(msg=next_name("strictly over ceiling → status warn")):
            returncode, response = run_estimator(parse_args_to_inputs("--files 11"))
            assert_estimator_exit(self, returncode, response, context="strictly over ceiling")
            result = response["data"]["stdout_json"]
            self.assertEqual(result["estimated_loc"], 440)
            self.assertEqual(result["status"], "warn")

        with self.subTest(msg=next_name("--spike → {estimated_loc:0, suggested_slices:1, status:ok}")):
            returncode, response = run_estimator(parse_args_to_inputs("--spike"))
            assert_estimator_exit(self, returncode, response, context="--spike")
            self.assertEqual(
                response["data"]["stdout_json"],
                {"estimated_loc": 0, "suggested_slices": 1, "status": "ok"},
            )

        with self.subTest(msg=next_name("--spike overrides large signals (spike precedence)")):
            returncode, response = run_estimator(
                parse_args_to_inputs("--user-stories 99 --files 99 --frs 99 --spike")
            )
            assert_estimator_exit(self, returncode, response, context="spike precedence")
            self.assertEqual(
                response["data"]["stdout_json"],
                {"estimated_loc": 0, "suggested_slices": 1, "status": "ok"},
            )

        with self.subTest(msg=next_name("no arguments → estimated_loc 0, status ok, exit 0")):
            returncode, response = run_estimator(parse_args_to_inputs(""))
            result = response["data"]["stdout_json"]
            self.assertEqual(returncode, 0)
            self.assertEqual(result["estimated_loc"], 0)
            self.assertEqual(result["status"], "ok")

        with self.subTest(msg=next_name("malformed/negative/decimal signals normalize to 0")):
            returncode, response = run_estimator(parse_args_to_inputs("--user-stories abc --files -5 --frs 3.5"))
            result = response["data"]["stdout_json"]
            self.assertEqual(returncode, 0)
            self.assertEqual(result["estimated_loc"], 0)
            self.assertEqual(result["status"], "ok")

        with self.subTest(msg=next_name("mixed valid + bad keeps valid signals")):
            _returncode, response = run_estimator(parse_args_to_inputs("--user-stories 4 --files abc --frs -2"))
            result = response["data"]["stdout_json"]
            self.assertEqual(result["estimated_loc"], 100)
            self.assertEqual(result["status"], "ok")

        with self.subTest(msg=next_name("status is always ok or warn across an input sweep")):
            status_violation = ""
            for arg_line in (
                "",
                "--files 10",
                "--files 11",
                "--files 20",
                "--user-stories 2 --files 3 --frs 4",
                "--files 10 --new-vs-modify modify",
                "--spike",
                "--user-stories 99 --files 99 --frs 99 --spike",
                "--user-stories abc --files -5 --frs 3.5",
                "--user-stories 4 --files abc --frs -2",
            ):
                returncode, response = run_estimator(parse_args_to_inputs(arg_line))
                assert_estimator_exit(self, returncode, response, context=f"status sweep {arg_line or '<empty>'}")
                status = response["data"]["stdout_json"].get("status", "")
                if status not in {"ok", "warn"}:
                    status_violation = f"args='{arg_line}' status='{status}'"
                    break
            self.assertEqual(status_violation, "")

        with self.subTest(msg=next_name("under ceiling → 1 slice")):
            returncode, response = run_estimator(parse_args_to_inputs("--user-stories 2 --files 3 --frs 4"))
            assert_estimator_exit(self, returncode, response, context="under ceiling")
            self.assertEqual(response["data"]["stdout_json"]["suggested_slices"], 1)

        with self.subTest(msg=next_name("440 LOC → 2 slices")):
            returncode, response = run_estimator(parse_args_to_inputs("--files 11"))
            assert_estimator_exit(self, returncode, response, context="440 LOC")
            self.assertEqual(response["data"]["stdout_json"]["suggested_slices"], 2)

        with self.subTest(msg=next_name("800 LOC → 2 slices")):
            returncode, response = run_estimator(parse_args_to_inputs("--files 20"))
            assert_estimator_exit(self, returncode, response, context="800 LOC")
            self.assertEqual(response["data"]["stdout_json"]["suggested_slices"], 2)

        self.assertEqual(list(names), [])


def main() -> int:
    status = run_counted(build_suite(), label="test-estimate-spec-size")
    try:
        assert_subtest_inventory_matches_baseline()
    except AssertionError as exc:
        print(f"test-estimate-spec-size inventory mismatch: {exc}", file=sys.stderr)
        return 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
