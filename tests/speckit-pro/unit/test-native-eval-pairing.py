#!/usr/bin/env python3
"""Owner tests for pure native-evaluation pair contracts."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_pairing import (  # noqa: E402
    PairingError,
    compile_pair_plan,
    grade_pair,
    pair_grader_fingerprint,
    pair_input_fingerprint,
)
from test_result import run_counted  # noqa: E402


def workflow(*, note: str = "same", rows: int = 1, safe: str = "true") -> str:
    data = "\n".join(f"| PASS | {note}-{index} |" for index in range(rows))
    return (
        "## Results\n"
        "| Status | Notes |\n"
        "| --- | --- |\n"
        f"{data}\n\n"
        "## Required Invariants\n"
        "| Invariant | Value |\n"
        "| --- | --- |\n"
        f"| safe | {safe} |\n"
        "| teams_only | obsolete |\n"
    )


class NativeEvalPairingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.contract_dir = self.root / "tests" / "speckit-pro" / "pair-fixture"
        self.contract_dir.mkdir(parents=True)
        self.expected_path = self.contract_dir / "expected-equivalence.json"
        self.tolerance_path = self.contract_dir / "tolerance.json"
        self.write_contracts()
        self.case = self.make_case()
        self.plan = compile_pair_plan(self.case, self.root)

    def write_contracts(
        self,
        *,
        compare: list[dict[str, object]] | None = None,
        fields: dict[str, object] | None = None,
        invariants: bool = True,
    ) -> None:
        compare = compare or [
            {
                "field": "results.status", "source": "workflow.md",
                "section_selector": "## Results", "extractor": "table_column:Status",
                "tolerance_key": "results.status",
            },
            {
                "field": "results.notes", "source": "workflow.md",
                "section_selector": "## Results", "extractor": "table_column:Notes",
                "tolerance_key": "results.notes",
            },
        ]
        fields = fields or {
            "results.status": {"tolerance": "exact", "rationale": "Statuses are a closed contract."},
            "results.notes": {
                "tolerance": "semantic-equivalent",
                "rationale": "Allow paraphrase but reject contradictory findings.",
            },
        }
        expected: dict[str, object] = {
            "schema": "speckit.layer7.expected-equivalence.v1",
            "fixture_id": "pair-fixture",
            "description": "Executable normalized outcome fields.",
            "compare": compare,
            "fail_fast": False,
            "report_format": "field-level-diff",
        }
        if invariants:
            expected.update({
                "required_invariants": {"safe": True, "teams_only": "obsolete"},
                "required_invariants_source": {
                    "source": "workflow.md",
                    "section_selector": "## Required Invariants",
                    "key_column": "Invariant",
                    "value_column": "Value",
                },
            })
        tolerance = {
            "schema": "speckit.layer7.tolerance.v1",
            "fixture_id": "pair-fixture",
            "description": "Explicit field tolerances.",
            "fields": fields,
        }
        self.expected_path.write_text(json.dumps(expected), encoding="utf-8")
        self.tolerance_path.write_text(json.dumps(tolerance), encoding="utf-8")

    def make_case(self, *, invariant_keys: list[str] | None = None) -> dict[str, object]:
        return {
            "id": "parity.normalized-outcome",
            "layer": "parity",
            "capability": "Produce the same independently correct normalized outcome.",
            "timeout_seconds": 300,
            "resource_class": "ordinary",
            "requirements": [{"id": "parity", "description": "The normalized outcomes agree."}],
            "prompt": "Use {{skill}} to produce workflow.md.",
            "fixtures": [],
            "hosts": {
                "claude": {"skill": "plugin:skill", "allowed_tools": ["Read"], "modes": ["plugin"]},
                "codex": {"skill": "skill", "allowed_tools": ["read_file"], "modes": ["project"]},
            },
            "checks": [{
                "id": "independent", "requirement": "parity", "type": "semantic",
                "rubric": "The result independently satisfies the requested workflow contract.",
            }],
            "pairing": {
                "schema": "native-eval-pair/v1",
                "arms": {"claude": "plugin", "codex": "project"},
                "checks": [{
                    "id": "outcome", "requirement": "parity", "type": "comparison_plan",
                    "expected_path": "tests/speckit-pro/pair-fixture/expected-equivalence.json",
                    "tolerance_path": "tests/speckit-pro/pair-fixture/tolerance.json",
                    "invariant_keys": ["safe"] if invariant_keys is None else invariant_keys,
                }],
            },
            "native_differences": [],
            "provenance": ["tests/speckit-pro/layer7-parity/legacy-fixture"],
        }

    def arms(
        self,
        left: str | None = None,
        right: str | None = None,
        *,
        left_grade: str = "pass",
        right_grade: str = "pass",
    ) -> list[dict[str, object]]:
        values = (left or workflow(), right or workflow())
        result = []
        for index, (host, mode, value) in enumerate((
            ("claude", "plugin", values[0]),
            ("codex", "project", values[1]),
        )):
            result.append({
                "case_id": self.case["id"],
                "host": host,
                "mode": mode,
                "trial": 1,
                "input_fingerprint": str(index + 1) * 64,
                "capture_sha256": chr(ord("a") + index) * 64,
                "grade_identity": chr(ord("c") + index) * 64,
                "grade_sha256": chr(ord("e") + index) * 64,
                "grade": {"status": left_grade if index == 0 else right_grade},
                "observation": {"artifacts": {"workflow.md": value}},
            })
        return result

    def test_compiles_only_selected_invariants_and_declares_capture_artifacts(self) -> None:
        self.assertEqual(self.plan["declared_artifact_paths"], ["workflow.md"])
        self.assertEqual(self.plan["checks"][0]["invariants"], {"safe": True})
        self.assertNotIn("teams_only", self.plan["checks"][0]["invariants"])
        no_legacy = self.make_case(invariant_keys=[])
        compiled = compile_pair_plan(no_legacy, self.root)
        self.assertEqual(compiled["checks"][0]["invariants"], {})
        self.assertIsNone(compiled["checks"][0]["invariant_source"])

    def test_equal_independently_correct_outputs_pass_without_a_judge(self) -> None:
        result = grade_pair(self.case, self.plan, self.arms())
        self.assertEqual(result["status"], "pass")
        self.assertNotIn("semantic_request", result)
        self.assertTrue(all(row["verdict"] == "pass" for row in result["checks"]))

    def test_correct_empty_tables_remain_valid(self) -> None:
        empty = workflow(rows=0)
        result = grade_pair(self.case, self.plan, self.arms(empty, empty))
        self.assertEqual(result["status"], "pass")
        self.assertNotIn("semantic_request", result)

    def test_equal_malformed_tables_are_invalid_not_equivalent(self) -> None:
        base = workflow()
        malformed = {
            "invalid separator": base.replace("| --- | --- |", "| not-separator | --- |", 1),
            "duplicate columns": base.replace("| Status | Notes |", "| Status | Status |", 1),
            "ragged extra width": base.replace("| PASS | same-0 |", "| PASS | same-0 | extra |", 1),
            "missing trailing pipe": base.replace("| PASS | same-0 |", "| PASS | same-0", 1),
            "duplicate section": base + "\n## Results\n| Status | Notes |\n| --- | --- |\n",
        }
        for label, value in malformed.items():
            with self.subTest(label=label):
                result = grade_pair(self.case, self.plan, self.arms(value, value))
                self.assertEqual(result["status"], "invalid")
                self.assertNotIn("semantic_request", result)

    def test_empty_compiled_comparisons_never_produce_a_pair_pass(self) -> None:
        empty_plan = copy.deepcopy(self.plan)
        empty_plan["checks"] = []
        empty_check = copy.deepcopy(self.plan)
        empty_check["checks"][0]["criteria"] = []
        for plan in (empty_plan, empty_check):
            with self.subTest(plan=plan):
                result = grade_pair(self.case, plan, self.arms())
                self.assertEqual(result["status"], "invalid")
                self.assertIn("nonempty", result["checks"][0]["reason"])

    def test_equal_wrong_outputs_fail_before_equality(self) -> None:
        same = workflow(safe="false")
        independent_fail = grade_pair(
            self.case, self.plan, self.arms(same, same, left_grade="fail", right_grade="fail"),
        )
        self.assertEqual(independent_fail["status"], "fail")
        self.assertNotIn("semantic_request", independent_fail)
        invariant_fail = grade_pair(self.case, self.plan, self.arms(same, same))
        self.assertEqual(invariant_fail["status"], "fail")
        self.assertIn("invariant mismatch", invariant_fail["checks"][-1]["reason"])

    def test_missing_wrong_mode_duplicate_swapped_and_invalid_arms_fail_closed(self) -> None:
        valid = self.arms()
        malformed = [
            valid[:1],
            [valid[0], {**valid[1], "mode": "wrong"}],
            [valid[0], {**valid[1], "host": "claude"}],
            list(reversed(valid)),
            [valid[0], {**valid[1], "grade": {"status": "invalid"}}],
            [valid[0], {**valid[1], "grade": {"status": "needs_judge"}}],
        ]
        for arms in malformed:
            with self.subTest(arms=arms):
                self.assertEqual(grade_pair(self.case, self.plan, arms)["status"], "invalid")

    def test_deterministic_mismatch_fails_without_semantic_judging(self) -> None:
        left = workflow(note="left", rows=1)
        right = workflow(note="right", rows=2)
        result = grade_pair(self.case, self.plan, self.arms(left, right))
        self.assertEqual(result["status"], "fail")
        self.assertNotIn("semantic_request", result)

    def test_missing_artifact_and_malformed_table_are_invalid(self) -> None:
        missing = self.arms()
        missing[1]["observation"]["artifacts"] = {}
        self.assertEqual(grade_pair(self.case, self.plan, missing)["status"], "invalid")
        malformed = self.arms()
        malformed[0]["observation"]["artifacts"]["workflow.md"] = "## Results\nnot a table\n"
        self.assertEqual(grade_pair(self.case, self.plan, malformed)["status"], "invalid")

    def test_byte_identical_compares_the_complete_declared_artifact(self) -> None:
        compare = [{"field": "whole", "source": "workflow.md", "tolerance_key": "whole"}]
        fields = {"whole": {"tolerance": "byte-identical", "rationale": "All bytes are contractual."}}
        self.write_contracts(compare=compare, fields=fields, invariants=False)
        self.case = self.make_case(invariant_keys=[])
        plan = compile_pair_plan(self.case, self.root)
        self.assertEqual(grade_pair(self.case, plan, self.arms())["status"], "pass")
        self.assertEqual(grade_pair(
            self.case, plan, self.arms(workflow(note="left"), workflow(note="right")),
        )["status"], "fail")

    def test_numeric_tolerance_one_is_not_byte_equality(self) -> None:
        compare = [{
            "field": "results.row_count", "source": "workflow.md",
            "section_selector": "## Results", "extractor": "table_row_count",
            "tolerance_key": "results.row_count",
        }]
        fields = {"results.row_count": {
            "tolerance": "tolerance-1", "rationale": "Allow one additional consensus row.",
        }}
        self.write_contracts(compare=compare, fields=fields, invariants=False)
        self.case = self.make_case(invariant_keys=[])
        plan = compile_pair_plan(self.case, self.root)
        self.assertEqual(grade_pair(self.case, plan, self.arms(workflow(rows=1), workflow(rows=2)))["status"], "pass")
        self.assertEqual(grade_pair(self.case, plan, self.arms(workflow(rows=1), workflow(rows=3)))["status"], "fail")

    def test_semantic_difference_builds_one_blinded_request_and_requires_strict_verdicts(self) -> None:
        result = grade_pair(self.case, self.plan, self.arms(workflow(note="alpha"), workflow(note="beta")))
        self.assertEqual(result["status"], "needs_judge")
        request = result["semantic_request"]
        self.assertEqual(set(request["evidence"]), {"arm_a", "arm_b"})
        self.assertNotIn("claude", json.dumps(request).lower())
        self.assertNotIn("codex", json.dumps(request).lower())
        criterion_id = request["semantic_criteria"][0]["id"]
        passed = {criterion_id: {"passed": True, "evidence": [f"arm_a/{criterion_id}", f"arm_b/{criterion_id}"]}}
        self.assertEqual(grade_pair(
            self.case, self.plan, self.arms(workflow(note="alpha"), workflow(note="beta")), passed,
        )["status"], "pass")
        malformed = {criterion_id: {"passed": "true", "evidence": ["arm_a/value"]}}
        self.assertEqual(grade_pair(
            self.case, self.plan, self.arms(workflow(note="alpha"), workflow(note="beta")), malformed,
        )["status"], "invalid")

    def test_all_differing_semantic_criteria_share_one_blinded_request(self) -> None:
        compare = [
            {
                "field": field, "source": "workflow.md", "section_selector": "## Results",
                "extractor": "table_column:Notes", "tolerance_key": field,
            }
            for field in ("results.notes", "results.findings")
        ]
        fields = {
            field: {"tolerance": "semantic-equivalent", "rationale": "Reject contradictory findings."}
            for field in ("results.notes", "results.findings")
        }
        self.write_contracts(compare=compare, fields=fields, invariants=False)
        self.case = self.make_case(invariant_keys=[])
        plan = compile_pair_plan(self.case, self.root)
        result = grade_pair(self.case, plan, self.arms(workflow(note="alpha"), workflow(note="beta")))
        self.assertEqual(result["status"], "needs_judge")
        self.assertEqual(len(result["semantic_request"]["semantic_criteria"]), 2)
        self.assertEqual(set(result["semantic_request"]["evidence"]), {"arm_a", "arm_b"})

    def test_semantic_section_text_accepts_native_table_layouts(self) -> None:
        compare = [{
            "field": "results.summary", "source": "workflow.md",
            "section_selector": "## Results", "extractor": "section_text",
            "tolerance_key": "results.summary",
        }]
        fields = {"results.summary": {
            "tolerance": "semantic-equivalent",
            "rationale": "Require the same closed outcome while allowing native table layouts.",
        }}
        self.write_contracts(compare=compare, fields=fields, invariants=False)
        self.case = self.make_case(invariant_keys=[])
        plan = compile_pair_plan(self.case, self.root)
        left = "## Results\n\n| Status | Notes |\n|---|---|\n| PASS | complete |\n"
        right = "## Results\n\n| Item | Result |\n|---|---|\n| Run | passed and complete |\n"
        result = grade_pair(self.case, plan, self.arms(left, right))
        self.assertEqual(result["status"], "needs_judge", result)
        request = result["semantic_request"]
        criterion = request["semantic_criteria"][0]
        self.assertEqual(set(request["evidence"]), {"arm_a", "arm_b"})
        self.assertIn("| Status | Notes |", request["evidence"]["arm_a"][criterion["id"]])
        self.assertIn("| Item | Result |", request["evidence"]["arm_b"][criterion["id"]])
        verdict = {criterion["id"]: {
            "passed": True,
            "evidence": [f"arm_a/{criterion['id']}", f"arm_b/{criterion['id']}"],
        }}
        self.assertEqual(grade_pair(self.case, plan, self.arms(left, right), verdict)["status"],
                         "pass")

    def test_input_and_grader_fingerprints_have_separate_mutation_boundaries(self) -> None:
        arms = self.arms()
        pair_input = pair_input_fingerprint(self.case["id"], self.plan, arms)
        pair_grader = pair_grader_fingerprint(self.plan, {"source": "pairing-v1", "judge": "model-a"})
        changed_capture = copy.deepcopy(arms)
        changed_capture[1]["capture_sha256"] = "f" * 64
        self.assertNotEqual(pair_input, pair_input_fingerprint(self.case["id"], self.plan, changed_capture))
        changed_grade = copy.deepcopy(arms)
        changed_grade[0]["grade_identity"] = "9" * 64
        self.assertNotEqual(pair_input, pair_input_fingerprint(self.case["id"], self.plan, changed_grade))
        changed_plan = copy.deepcopy(self.plan)
        changed_plan["checks"][0]["criteria"][1]["rubric"] = "A stricter pair-only rubric."
        self.assertEqual(pair_input, pair_input_fingerprint(self.case["id"], changed_plan, arms))
        self.assertNotEqual(pair_grader, pair_grader_fingerprint(
            changed_plan, {"source": "pairing-v1", "judge": "model-a"},
        ))

    def test_rejects_ambiguous_contract_schema_and_unsafe_paths(self) -> None:
        expected = json.loads(self.expected_path.read_text(encoding="utf-8"))
        expected["unexpected"] = True
        self.expected_path.write_text(json.dumps(expected), encoding="utf-8")
        with self.assertRaisesRegex(PairingError, "ambiguous schema"):
            compile_pair_plan(self.case, self.root)
        self.write_contracts()
        traversal = copy.deepcopy(self.case)
        traversal["pairing"]["checks"][0]["expected_path"] = "tests/speckit-pro/../outside.json"
        with self.assertRaisesRegex(PairingError, "canonical relative path"):
            compile_pair_plan(traversal, self.root)
        empty_contract_path = copy.deepcopy(self.case)
        empty_contract_path["pairing"]["checks"][0]["expected_path"] = "."
        with self.assertRaisesRegex(PairingError, "canonical relative path"):
            compile_pair_plan(empty_contract_path, self.root)
        expected = json.loads(self.expected_path.read_text(encoding="utf-8"))
        expected["compare"][0]["source"] = "."
        self.expected_path.write_text(json.dumps(expected), encoding="utf-8")
        with self.assertRaisesRegex(PairingError, "canonical relative path"):
            compile_pair_plan(self.case, self.root)
        self.write_contracts()
        outside = self.root / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        link = self.root / "tests" / "speckit-pro" / "escape.json"
        try:
            os.symlink(outside, link)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        escaped = copy.deepcopy(self.case)
        escaped["pairing"]["checks"][0]["expected_path"] = "tests/speckit-pro/escape.json"
        with self.assertRaisesRegex(PairingError, "escaped tests/speckit-pro"):
            compile_pair_plan(escaped, self.root)

    def test_rejects_ambiguous_extractor_and_host_revealing_semantic_rubric(self) -> None:
        expected = json.loads(self.expected_path.read_text(encoding="utf-8"))
        del expected["compare"][1]["extractor"]
        self.expected_path.write_text(json.dumps(expected), encoding="utf-8")
        with self.assertRaisesRegex(PairingError, "ambiguous schema"):
            compile_pair_plan(self.case, self.root)
        self.write_contracts()
        tolerance = json.loads(self.tolerance_path.read_text(encoding="utf-8"))
        tolerance["fields"]["results.notes"]["rationale"] = "Claude and Codex should agree."
        self.tolerance_path.write_text(json.dumps(tolerance), encoding="utf-8")
        with self.assertRaisesRegex(PairingError, "must not reveal"):
            compile_pair_plan(self.case, self.root)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeEvalPairingTests)
    raise SystemExit(run_counted(suite, label="test-native-eval-pairing"))
