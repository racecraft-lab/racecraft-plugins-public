#!/usr/bin/env python3
"""Pins on the content of Layer 3 functional evals and their catalog cases.

Each eval is located by a phrase from its prompt, and each catalog case by its
stable id, so renumbering an eval file never silently retargets a pin.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LAYER3 = TEST_ROOT / "layer3-functional"
sys.path.insert(0, str(TEST_ROOT / "lib"))

from test_result import run_counted  # noqa: E402

AUTOPILOT_EVAL_FILES = (
    LAYER3 / "codex-evals" / "speckit-autopilot-evals.json",
    LAYER3 / "evals" / "speckit-autopilot-evals.json",
)
COACH_EVAL_FILES = (
    LAYER3 / "codex-evals" / "speckit-coach-evals.json",
    LAYER3 / "evals" / "speckit-coach-evals.json",
)
CATALOG_PATH = TEST_ROOT / "evals" / "catalog.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _only(items: list[dict], matches, description: str) -> dict:
    found = [item for item in items if matches(item)]
    if len(found) != 1:
        raise AssertionError(f"expected one {description}, found {len(found)}")
    return found[0]


def eval_with_prompt(path: Path, phrase: str) -> dict:
    return _only(_load(path)["evals"], lambda item: phrase in item["prompt"], f"{path.name} eval whose prompt has {phrase!r}")


def catalog_case(case_id: str) -> dict:
    return _only(_load(CATALOG_PATH)["cases"], lambda case: case["id"] == case_id, f"catalog case {case_id}")


class FunctionalEvalExpectationTests(unittest.TestCase):
    def test_external_workflow_eval_binds_and_continues(self) -> None:
        item = json.dumps(eval_with_prompt(AUTOPILOT_EVAL_FILES[0], "explicitly supplies the absolute workflow"))
        self.assertNotIn("open a new Codex task rooted", item)
        self.assertIn("WORKFLOW_ROOT", item)

    def test_keyword_eval_widens_to_all_three_analysts_with_a_conditional_bar(self) -> None:
        for path in AUTOPILOT_EVAL_FILES:
            with self.subTest(path=path.parent.name):
                item = json.dumps(eval_with_prompt(path, "cookie SameSite"))
                self.assertNotIn("ONLY domain-researcher", item)
                self.assertIn("security_relevant", item)

    def test_security_tag_eval_applies_a_unanimous_answer(self) -> None:
        stale = "fires automatically for security items"
        corrected = "a unanimous 3/3 answer applies and the run continues"
        for path in AUTOPILOT_EVAL_FILES:
            with self.subTest(path=path.parent.name):
                item = eval_with_prompt(path, "[security] Q5: How should we hash")
                self.assertNotIn(stale, item["expected_output"])
                self.assertIn(corrected, item["expected_output"])
        case = catalog_case("functional.speckit-autopilot.case-19")
        self.assertNotIn(stale, case["capability"])
        self.assertIn(corrected, case["capability"])

    def test_coach_consensus_eval_resolves_disagreement_by_round_three_tiebreak(self) -> None:
        stale = "asked in place in an interactive run"
        corrected = "resolved by a Round 3 agent tiebreak"
        phrase = "How does the consensus protocol work in the autopilot workflow"
        for path in COACH_EVAL_FILES:
            with self.subTest(path=path.parent.name):
                item = json.dumps(eval_with_prompt(path, phrase))
                self.assertNotIn(stale, item)
                self.assertIn(corrected, item)
        case = json.dumps(catalog_case("functional.speckit-coach.case-4"))
        self.assertNotIn(stale, case)
        self.assertIn(corrected, case)

    def test_pins_fail_when_the_anchor_is_missing_or_ambiguous(self) -> None:
        with self.assertRaisesRegex(AssertionError, "found 0"):
            eval_with_prompt(AUTOPILOT_EVAL_FILES[0], "no eval has this phrase")
        with self.assertRaisesRegex(AssertionError, "found 0"):
            catalog_case("functional.speckit-autopilot.case-0")


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(FunctionalEvalExpectationTests),
        label="test-functional-eval-expectations",
    ))
