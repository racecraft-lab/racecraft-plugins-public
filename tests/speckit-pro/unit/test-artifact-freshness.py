#!/usr/bin/env python3
"""Golden-fixture tests for the artifact-freshness helper's three surfaces.

Two fixture files drive everything here, following the pattern
`tests/speckit-pro/unit/test-feedback-sweep-parse.py` established.

`fixtures/artifact-freshness/freshness-cases.json` holds one case per behaviour,
each carrying the `inputs` object of a `check-artifact-freshness` request
verbatim. A case whose inputs carry no `named_surface` exercises the `verdict`
surface; a case carrying `removal_diff` or `corroborate_refresh` exercises that
one. A case may also carry `workflow_content`, which is written where its
`workflow_file` points for the length of the case, because the helper resolves
that path inside the repository and a system temporary directory is out of
reach.

`fixtures/artifact-freshness/expected-envelopes.json` holds the expected result
for each case under the same name. Two shapes, and they are not
interchangeable:

    {"status": "ok", "envelope": { ... }}
    {"status": "input_error", "error_contains": "..."}

Every expectation here is written by hand, because the contract fixes each
envelope field by field and a reader can check it against
`specs/art-008-feedback-sweep-slice-2/contracts/check-artifact-freshness.md`.
Nothing in this file is captured from the helper's own output: a test that
compares a helper's output to itself executes nothing.

The pair starts empty. The harness therefore asserts the two files name the same
cases and runs whichever cases exist, rather than asserting the corpus is
non-empty — an emptiness assertion would be red before the first case lands and
would say nothing about the helper.

Run it directly:

    python3 tests/speckit-pro/unit/test-artifact-freshness.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = Path(__file__).resolve().parent.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "artifact-freshness"
CASES_PATH = FIXTURE_DIR / "freshness-cases.json"
EXPECTED_PATH = FIXTURE_DIR / "expected-envelopes.json"

# A case that needs a workflow file the repository does not carry writes one here
# for the length of the case, and the directory is removed whatever the case
# does.
WORKFLOW_SCRATCH = FIXTURE_DIR / ".workflow-scratch"

HELPER_ID = "check-artifact-freshness"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


CORPUS = load_json(CASES_PATH)
EXPECTED = load_json(EXPECTED_PATH)


def cases() -> dict[str, Any]:
    return CORPUS["cases"]


def expectations() -> dict[str, Any]:
    return EXPECTED["cases"]


def case_names() -> list[str]:
    return sorted(cases())


def runner_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(PLUGIN_ROOT) if not existing else f"{PLUGIN_ROOT}{os.pathsep}{existing}"
    return env


def helper_request(name: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "request_id": f"corpus-{name}",
        "helper_id": HELPER_ID,
        "operation": HELPER_ID,
        "mode": "read_only",
        "inputs": inputs,
    }


def run_runner(request: dict[str, Any]) -> dict[str, Any]:
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
    if not completed.stdout.strip():
        raise AssertionError(
            f"runner returned no response document; stderr was: {completed.stderr[:2000]}"
        )
    return json.loads(completed.stdout)


class materialized_workflow:
    """Write a case's `workflow_content` where its `workflow_file` points."""

    def __init__(self, case: dict[str, Any]) -> None:
        self.content = case.get("workflow_content")
        target = case.get("inputs", {}).get("workflow_file")
        self.target = (
            None if self.content is None or not isinstance(target, str) else REPO_ROOT / target
        )

    def __enter__(self) -> None:
        if self.target is None or self.content is None:
            return
        self.target.parent.mkdir(parents=True, exist_ok=True)
        self.target.write_text(self.content, encoding="utf-8")

    def __exit__(self, *_exc: object) -> None:
        if self.content is None:
            return
        shutil.rmtree(WORKFLOW_SCRATCH, ignore_errors=True)


_RESPONSE_CACHE: dict[str, dict[str, Any]] = {}


def run_case(name: str) -> dict[str, Any]:
    """Run one case and memoize its response.

    The helper is deterministic by contract, so one invocation per case is the
    whole of what any assertion needs, and every assertion below reads the real
    response rather than the fixture it is compared against.
    """
    cached = _RESPONSE_CACHE.get(name)
    if cached is not None:
        return cached
    case = cases()[name]
    with materialized_workflow(case):
        response = run_runner(helper_request(name, case["inputs"]))
    _RESPONSE_CACHE[name] = response
    return response


def stdout_json(response: dict[str, Any]) -> Any:
    return (response.get("data") or {}).get("stdout_json")


def stderr_text(response: dict[str, Any]) -> str:
    return str((((response.get("data") or {}).get("stderr")) or {}).get("text") or "")


class FreshnessEnvelopeTest(unittest.TestCase):
    """Every case, run through the runner and compared against its expectation."""

    def test_corpus_and_expectations_name_the_same_cases(self) -> None:
        # Both directions. A case with no expectation would run and assert
        # nothing; an expectation with no case would assert nothing and look
        # like coverage.
        self.assertEqual(
            sorted(cases()),
            sorted(expectations()),
            "freshness-cases.json and expected-envelopes.json must name the same cases",
        )

    def test_every_case_declares_its_purpose(self) -> None:
        for name in case_names():
            with self.subTest(case=name):
                case = cases()[name]
                self.assertTrue(
                    str(case.get("purpose") or "").strip(),
                    f"{name} carries no purpose, so a reader cannot check what it pins",
                )
                self.assertIsInstance(
                    case.get("inputs"),
                    dict,
                    f"{name} carries no inputs object",
                )

    def test_every_expectation_declares_a_known_status(self) -> None:
        for name in case_names():
            with self.subTest(case=name):
                want = expectations()[name]
                self.assertIn(
                    want.get("status"),
                    ("ok", "input_error"),
                    f"{name} declares an unknown expected status",
                )
                if want["status"] == "ok":
                    self.assertIsInstance(
                        want.get("envelope"),
                        dict,
                        f"{name} expects ok but carries no envelope to compare",
                    )
                else:
                    self.assertTrue(
                        str(want.get("error_contains") or "").strip(),
                        f"{name} expects an input error but names no diagnostic text",
                    )

    def test_each_case_returns_its_expected_result(self) -> None:
        for name in case_names():
            with self.subTest(case=name):
                want = expectations()[name]
                response = run_case(name)
                if want["status"] == "ok":
                    self.assertEqual(response.get("status"), "ok")
                    self.assertEqual(response.get("exit_code"), 0)
                    self.assertEqual(
                        stdout_json(response),
                        want["envelope"],
                        f"{name} returned an envelope the contract does not fix",
                    )
                else:
                    self.assertEqual(response.get("status"), "input_error")
                    self.assertEqual(response.get("exit_code"), 2)
                    text = stderr_text(response)
                    self.assertTrue(
                        text.startswith("error: "),
                        f"{name} returned a diagnostic that is not the one-line error shape: {text!r}",
                    )
                    self.assertIn(want["error_contains"], text)


def main(argv: list[str]) -> int:
    shutil.rmtree(WORKFLOW_SCRATCH, ignore_errors=True)
    if argv:
        # A named class or method: plain unittest, for iterating on one test.
        result = unittest.main(argv=[sys.argv[0]] + argv, exit=False, verbosity=2).result
        shutil.rmtree(WORKFLOW_SCRATCH, ignore_errors=True)
        return 0 if result.wasSuccessful() else 1
    # The whole file, through the house counter. Without this the runner reports
    # "PASS test-artifact-freshness (no summary)" and counts zero units, so every
    # assertion in this file is invisible to the suite total.
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    code = run_counted(suite, label="test-artifact-freshness")
    shutil.rmtree(WORKFLOW_SCRATCH, ignore_errors=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
