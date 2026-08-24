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

The pair started empty, so the harness asserts the two files name the same cases
and runs whichever cases exist rather than asserting the corpus is non-empty: an
emptiness assertion would have been red before the first case landed and would
say nothing about the helper.

That is no longer sufficient on its own. Once the corpus is established, a
name-agreement check alone stays green after every case is deleted from both
files, so a suite that pins nothing looks exactly like a suite that pins
everything. `REQUIRED_CASES` closes that: it names one case per behavioural
obligation the contract fixes, and removing any of them is a failure rather
than a smaller run.

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

# One case per behavioural obligation, not the whole corpus: a list of all 57
# would have to be edited for every case added, which turns the guard into
# bookkeeping and invites deleting a line to make a run green. These are the
# obligations whose loss would not be visible any other way.
REQUIRED_CASES = (
    # The four verdicts and their precedence.
    "verdict-current-ancestor-row",
    "verdict-stale-newer-amended-row",
    "verdict-undeterminable-unmatched-row",
    "verdict-no-pages-directory-absent",
    "precedence-no-pages-over-amended-rows",
    "precedence-stale-over-undeterminable-row",
    # Every closed undeterminable reason.
    "reason-empty-commit-cell",
    "reason-malformed-row",
    "reason-missing-commit-cell",
    "reason-no-matching-observation-record",
    "reason-unresolvable-commit",
    # The dual anchoring, which is the one place a naive read is silently wrong.
    "dual-anchoring-escaped-pipe-in-disposition",
    "structural-short-row-does-not-stop-the-other-rows",
    "structural-no-feedback-sweep-log-heading",
    # Ancestry rather than comparison, and the FR-007a interrupted-run case.
    "fr007a-null-artifacts-commit-with-joinable-row-is-stale",
    "fr007b-null-artifacts-commit-with-unresolved-row-is-undeterminable",
    "fr007b-pinned-false-ancestor-reaches-stale-through-the-ordinary-test",
    "fr008-abbreviated-cell-against-full-sha-is-current",
    # `ok` read as the JSON literal `true`, which a truthiness test would lose.
    "observation-ok-integer-one-is-undeterminable",
    "observation-ok-string-true-is-undeterminable",
    "observation-ok-absent-is-undeterminable",
    # A successful gather whose shape is the caller's own defect.
    "input-error-observation-pages-not-an-array",
    "input-error-observation-pages-non-string-member",
    "input-error-observation-amended-commits-not-an-array",
    "input-error-observation-record-resolved-without-boolean-ancestry",
    "input-error-observation-record-unresolved-with-non-null-ancestry",
    # Evidence that survives a verdict that had nothing to judge.
    "verdict-no-pages-still-reports-undeterminable-rows",
    # The removal diff, one-way and over stems.
    "removal-deselected-page-yields-one-removal",
    "removal-gap-page-in-reselected-is-not-removed",
    "removal-stem-only-in-reselected-is-ignored",
    "removal-empty-reselected-removes-every-observed-page",
    # The six corroboration statuses, reused verbatim rather than re-decided.
    "corroborate-match",
    "corroborate-no-record-absent-draft-pr-row",
    "corroborate-skipped-observation-absent",
    "corroborate-pr-closed",
    "corroborate-pr-missing",
    "corroborate-identity-mismatch",
)


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

    def test_every_required_obligation_still_has_a_case(self) -> None:
        # Without this, deleting every case from both fixture files leaves the
        # name-agreement check above green and every assertion below iterating
        # nothing, so a corpus that pins nothing is indistinguishable from one
        # that pins everything.
        present = set(cases())
        missing = [name for name in REQUIRED_CASES if name not in present]
        self.assertEqual(
            missing,
            [],
            "the corpus no longer covers these obligations; rename the guard "
            "entry deliberately or restore the case, never delete the line to "
            "make a run green",
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

    def test_an_oversize_envelope_fails_closed(self) -> None:
        """A verdict too large for the runner's capture is refused, not truncated.

        Built here rather than stored as a case, because the input that trips it
        is 16 KiB of filler that would say nothing to a reader of the corpus.
        The runner truncates stdout at the capture limit and derives status from
        the exit code alone, so without the guard this returns `status: ok`,
        `exit_code: 0`, no diagnostics, and no `stdout_json` at all — which an
        orchestrator told to branch on the verdict cannot tell apart from a
        surface it never called.
        """
        pages = [f"page-{index:05d}-{'a' * 30}" for index in range(600)]
        inputs = {
            "named_surface": "verdict",
            "workflow_file": "tests/speckit-pro/unit/fixtures/artifact-freshness"
            "/.workflow-scratch/oversize-envelope.md",
            "artifacts_observation": {
                "ok": True,
                "artifacts_dir_state": "present",
                "last_artifacts_commit": "9f2c1ab",
                "pages": pages,
                "amended_commits": [],
            },
        }
        case = {"inputs": inputs, "workflow_content": "# oversize\n"}
        with materialized_workflow(case):
            response = run_runner(helper_request("oversize-envelope", inputs))
        self.assertEqual(response.get("status"), "input_error")
        self.assertEqual(response.get("exit_code"), 2)
        self.assertIn("exceeds the runner's stdout capture", stderr_text(response))



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
