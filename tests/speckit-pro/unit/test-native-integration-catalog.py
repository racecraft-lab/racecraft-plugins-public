#!/usr/bin/env python3
"""Deterministic corpus controls; these do not qualify live integration behavior."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_catalog import load_catalog, plan_trials  # noqa: E402
from native_eval_grading import grade_observation  # noqa: E402
from test_result import run_counted  # noqa: E402


def focused_case(case: dict, checks: list[dict]) -> dict:
    """Exercise only these checks, without claiming the full case passed."""
    covered = {check["requirement"] for check in checks}
    return {**case, "checks": checks,
            "requirements": [item for item in case["requirements"] if item["id"] in covered]}


class NativeReturnCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        catalog = load_catalog(TEST_ROOT / "evals" / "catalog.json", ROOT)
        self.cases = {case["id"]: case for case in catalog["cases"]}
        self.disagreement = self.cases["integration.return-01-synthesizer-disagreement"]
        self.majority = self.cases["integration.return-02-synthesizer-majority"]
        self.analyze = self.cases[
            "integration.return-03-analyze-zero-findings-confidence"
        ]

    def test_return_cases_preserve_two_and_three_input_boundaries(self) -> None:
        for case, names in (
            (self.disagreement, ["codebase-analyst", "domain-researcher"]),
            (self.majority, ["codebase-analyst", "domain-researcher", "spec-context-analyst"]),
        ):
            with self.subTest(case=case["id"]):
                paths = [f"scenario-inputs/analysts/{name}.md" for name in names]
                self.assertEqual([fixture["destination"] for fixture in case["fixtures"]], paths)

                self.assertEqual([check["path"] for check in case["checks"]
                                  if check["type"] == "file_access"], paths)
                for fixture in case["fixtures"]:
                    unchanged = next(check for check in case["checks"]
                                     if check.get("source") == fixture["destination"])
                    original = (ROOT / fixture["source"]).read_text(encoding="utf-8")
                    self.assertIsNotNone(re.search(unchanged["pattern"], original))
                    self.assertIsNone(re.search(unchanged["pattern"], original + "changed"))

    def test_analyze_case_requires_a_standalone_complete_input_read(self) -> None:
        self.assertIn(
            "using its own standalone read operation; do not combine that read",
            self.analyze["prompt"],
        )

    def test_native_mechanisms_align_responsibilities_with_platform_role_names(self) -> None:
        for case in (self.disagreement, self.majority, self.analyze):
            mechanism = [check for check in case["checks"]
                         if check["type"] == "native_synthesis_mechanism"]
            self.assertEqual(len(mechanism), 1)
            self.assertEqual(mechanism[0]["per_host"], {
                "claude": {"mode": "dedicated_subagent", "role": "speckit-pro:consensus-synthesizer"},
                "codex": {"mode": "dedicated_subagent", "role": "consensus-synthesizer"},
            })
            self.assertEqual(case["resource_class"], "nested")
            self.assertEqual(case["layer"], "integration")
        self.assertEqual(
            len(plan_trials([self.disagreement, self.majority, self.analyze])),
            6,
        )

    def test_representative_phase_cases_cover_clarify_checklist_and_clean_analyze(self) -> None:
        self.assertIn("Clarify", self.disagreement["capability"])
        self.assertIn("Checklist", self.majority["capability"])
        self.assertIn("zero-findings", self.analyze["capability"])
        self.assertIn("exactly once", self.analyze["prompt"])
        confidence = next(check for check in self.analyze["checks"]
                          if check["id"] == "confidence-block")
        self.assertIn("Task\\ understanding", confidence["pattern"])
        self.assertIn("Completeness", confidence["pattern"])

    def test_decision_checks_reject_old_terminal_and_wrong_majority_results(self) -> None:
        for case, expected in (
            (self.disagreement, {"decision": None, "next_action": "escape_to_round_2",
                                 "agreement": "two-analyst-disagreement", "confidence": "low",
                                 "retained_options": ["bcrypt", "argon2id"]}),
            (self.majority, {"decision": "JSON", "next_action": "apply",
                             "agreement": "3/3-unanimous", "confidence": "high",
                             "retained_options": ["JSON"]}),
        ):
            checks = [check for check in case["checks"] if check["type"] == "json_field"
                      and check["field_path"] != ["evidence"]]
            self.assertEqual({check["field_path"][0]: check["expected"] for check in checks}, expected)
            # This deliberately exercises only deterministic artifact checks.
            # It does not synthesize a passing native mechanism or judge result.
            focused = focused_case(case, checks)
            observation = {"completed": True, "error": None, "final_text": "",
                           "activations": [], "tool_calls": [], "usage": {},
                           "artifacts": {"scenario-output/consensus-result.json": json.dumps(expected)}}
            self.assertEqual(grade_observation(focused, observation)["status"], "pass")
            for field in expected:
                bad = copy.deepcopy(observation)
                value = {**expected, field: "incorrect"}
                if field == "next_action" and case is self.disagreement:
                    value[field] = "human_review"
                bad["artifacts"]["scenario-output/consensus-result.json"] = json.dumps(value)
                with self.subTest(case=case["id"], field=field):
                    self.assertEqual(grade_observation(focused, bad)["status"], "fail")

    def test_explicit_json_spelling_alternatives_preserve_choice_and_evidence(self) -> None:
        checks = copy.deepcopy([check for check in self.majority["checks"]
                                if check["id"] in {"decision", "retained-options", "evidence"}])
        for check in checks:
            alternative = json.loads(json.dumps(check["expected"]).replace('"JSON"', '"json"'))
            self.assertIn(alternative, check.get("alternatives", []))
        focused = focused_case(self.majority, checks)
        answer = {check["field_path"][0]: check["alternatives"][0] for check in checks}
        observation = {"completed": True, "error": None, "final_text": "",
                       "activations": [], "tool_calls": [], "usage": {},
                       "artifacts": {"scenario-output/consensus-result.json": json.dumps(answer)}}
        self.assertEqual(grade_observation(focused, observation)["status"], "pass")
        for field, wrong in (("decision", "YAML"), ("decision", True),
                             ("retained_options", ["json", "xml"]),
                             ("evidence", list(reversed(answer["evidence"]))),
                             ("evidence", [{**answer["evidence"][0], "source": "wrong.md"},
                                           *answer["evidence"][1:]])):
            bad = copy.deepcopy(observation)
            bad["artifacts"]["scenario-output/consensus-result.json"] = json.dumps({**answer, field: wrong})
            with self.subTest(field=field, wrong=wrong):
                self.assertEqual(grade_observation(focused, bad)["status"], "fail")


    def test_namespaced_analyst_labels_preserve_identity_and_attribution(self) -> None:
        for case in (self.disagreement, self.majority):
            check = next(check for check in case["checks"] if check["id"] == "evidence")
            focused = focused_case(case, [check])
            evidence = [{**row, "analyst": "speckit-pro:" + row["analyst"]}
                        for row in check["expected"]]
            observation = {"completed": True, "error": None, "final_text": "",
                           "activations": [], "tool_calls": [], "usage": {},
                           "artifacts": {"scenario-output/consensus-result.json":
                                         json.dumps({"evidence": evidence})}}
            with self.subTest(case=case["id"]):
                self.assertEqual(grade_observation(focused, observation)["status"], "pass")
            for field, wrong in (("analyst", "other-plugin:codebase-analyst"),
                                 ("analyst", "speckit-pro:consensus-synthesizer"),
                                 ("source", evidence[-1]["source"]),
                                 ("recommendation", "invented")):
                changed = copy.deepcopy(evidence)
                changed[0][field] = wrong
                bad = {**observation, "artifacts": {
                    "scenario-output/consensus-result.json": json.dumps({"evidence": changed})}}
                with self.subTest(case=case["id"], field=field, wrong=wrong):
                    self.assertEqual(grade_observation(focused, bad)["status"], "fail")


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(NativeReturnCatalogTests),
                                 label="test-native-integration-catalog"))
