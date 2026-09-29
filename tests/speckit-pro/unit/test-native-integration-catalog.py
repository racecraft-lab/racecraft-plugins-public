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
        self.keyword_majority = self.cases["integration.return-04-keyword-only-majority"]
        self.keyword_security = self.cases["integration.return-05-keyword-security-relevant"]

    def test_return_cases_preserve_two_and_three_input_boundaries(self) -> None:
        for case, names in (
            (self.disagreement, ["codebase-analyst", "domain-researcher"]),
            (self.majority, ["codebase-analyst", "domain-researcher", "spec-context-analyst"]),
            (self.keyword_majority, ["codebase-analyst", "domain-researcher", "spec-context-analyst"]),
            (self.keyword_security, ["codebase-analyst", "domain-researcher", "spec-context-analyst"]),
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
        cases = (self.disagreement, self.majority, self.analyze,
                 self.keyword_majority, self.keyword_security)
        for case in cases:
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
            len(plan_trials(list(cases))),
            10,
        )

    def test_analyze_case_requires_the_synthesizer_protocol_line(self) -> None:
        self.assertIn("`Protocol:` line naming the absolute path of the active", self.analyze["prompt"])
        requirement = next(row for row in self.analyze["requirements"] if row["id"] == "protocol")
        self.assertIn("`Protocol:`", requirement["description"])
        check = next(check for check in self.analyze["checks"] if check["requirement"] == "protocol")
        self.assertEqual(check["type"], "semantic")
        for needle in ("dispatch prompt", "`Protocol:` line", "consensus-protocol.md", "plugin-relative"):
            self.assertIn(needle, check["rubric"])

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
            (self.keyword_majority, {"decision": "per-request", "next_action": "apply",
                                     "agreement": "2/3-majority",
                                     "retained_options": ["per-request", "per-billing-period"]}),
            (self.keyword_security, {"decision": None, "next_action": "round_3_tiebreak",
                                     "agreement": "2/3-majority",
                                     "retained_options": ["per-request", "per-billing-period"]}),
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
                    value[field] = "round_3_tiebreak"
                bad["artifacts"]["scenario-output/consensus-result.json"] = json.dumps(value)
                with self.subTest(case=case["id"], field=field):
                    self.assertEqual(grade_observation(focused, bad)["status"], "fail")

    def test_round3_tiebreak_case_applies_the_conservative_option_without_a_stop(self) -> None:
        case = self.cases["integration.consensus-round3-tiebreak"]
        self.assertEqual(case["layer"], "integration")
        self.assertEqual(case["resource_class"], "nested")
        self.assertIn("`**Round:** 3`", case["prompt"])
        self.assertIn("must not ask the user, and must not stop", case["prompt"])
        paths = [f"scenario-inputs/analysts/{name}.md" for name in (
            "codebase-analyst", "domain-researcher", "spec-context-analyst", "tiebreak-analyst")]
        self.assertEqual(sorted(fixture["destination"] for fixture in case["fixtures"]), sorted(paths))
        self.assertEqual(sorted(check["path"] for check in case["checks"]
                                if check["type"] == "file_access"), sorted(paths))
        dispatch = [check for check in case["checks"] if check["type"] == "native_subagent_dispatch"]
        self.assertEqual(len(dispatch), 1)
        self.assertEqual([pair["role"] for pair in dispatch[0]["expected"]], ["consensus-tiebreaker"])
        self.assertEqual(dispatch[0]["forbidden_roles"], ["consensus-synthesizer"])
        expected = {"decision": "per-request", "next_action": "apply", "retained_options":
                    ["per-request", "per-billing-period"], "dissent": ["per-billing-period"],
                    "agreement": "tiebreak", "scope_deferred": False}
        checks = [check for check in case["checks"] if check["type"] == "json_field"]
        self.assertEqual({check["field_path"][0]: check["expected"] for check in checks}, expected)
        focused = focused_case(case, checks)
        observation = {"completed": True, "error": None, "final_text": "",
                       "activations": [], "tool_calls": [], "usage": {},
                       "artifacts": {"scenario-output/consensus-result.json": json.dumps(expected)}}
        self.assertEqual(grade_observation(focused, observation)["status"], "pass")
        for field, wrong in (("next_action", "round_3_tiebreak"), ("agreement", "0/3-all-disagree"),
                             ("decision", None), ("scope_deferred", True), ("dissent", [])):
            bad = copy.deepcopy(observation)
            bad["artifacts"]["scenario-output/consensus-result.json"] = json.dumps({**expected, field: wrong})
            with self.subTest(field=field):
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


    def test_keyword_route_cases_differ_only_in_one_security_relevant_answer(self) -> None:
        item = "`[domain] I1: Should the usage report count tokens per LLM request or per billing period?`"
        for case in (self.keyword_majority, self.keyword_security):
            with self.subTest(case=case["id"]):
                self.assertIn(item, case["prompt"])
                self.assertIn("`**Security Route:** keyword`", case["prompt"])
        inputs = {}
        for case in (self.keyword_majority, self.keyword_security):
            inputs[case["id"]] = {fixture["destination"]: (ROOT / fixture["source"]).read_text(encoding="utf-8")
                                  for fixture in case["fixtures"]}
        majority, security = inputs.values()
        changed = [path for path in majority if majority[path] != security[path]]
        self.assertEqual(changed, ["scenario-inputs/analysts/domain-researcher.md"])
        self.assertTrue(all("security_relevant: false" in text for text in majority.values()))
        self.assertIn("security_relevant: true", security["scenario-inputs/analysts/domain-researcher.md"])

    def test_namespaced_analyst_labels_preserve_identity_and_attribution(self) -> None:
        for case in (self.disagreement, self.majority, self.keyword_majority, self.keyword_security):
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
