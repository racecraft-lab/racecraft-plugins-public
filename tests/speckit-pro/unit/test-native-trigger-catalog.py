#!/usr/bin/env python3
"""Executable accounting and sensitivity checks for the native trigger catalog."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
AUDIT_PATH = TEST_ROOT / "evals" / "audit" / "trigger-inventory.json"
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_catalog import load_catalog  # noqa: E402
from native_eval_grading import grade_observation  # noqa: E402
from native_eval_trigger import stage_trigger_catalog  # noqa: E402
from test_result import run_counted  # noqa: E402
from trigger_evidence import case_id as legacy_case_id  # noqa: E402


NATIVE_DIFFERENCES = {
    "Claude uses a completed native Skill call; the adapter normalizes "
    "speckit-pro:<name> to the canonical <name> activation.",
    "Codex uses an exact staged SKILL.md body-read plus a randomized marker "
    "attestation because public exec JSON has no native skill-selection event.",
    "Claude plugin mode and Codex project mode must expose the exact source "
    "descriptions for the target and every sibling before the prompt is submitted.",
}


def trigger_catalog() -> tuple[Path, dict[str, object]]:
    """Prefer the final combined catalog; discover a trigger shard only pre-merge."""
    evals = TEST_ROOT / "evals"
    candidates = [evals / "catalog.json", *sorted(evals.glob("catalog-*.json"))]
    for path in candidates:
        if not path.is_file():
            continue
        catalog = load_catalog(path, REPO_ROOT)
        if any(case["layer"] == "trigger" for case in catalog["cases"]):
            return path, catalog
    raise AssertionError("no native evaluation catalog contains trigger cases")


def observation(activations: list[str]) -> dict[str, object]:
    return {
        "completed": True,
        "error": None,
        "final_text": "Selection evidence is graded independently from prose.",
        "activations": activations,
        "tool_calls": [],
        "artifacts": {},
        "usage": {},
    }


class NativeTriggerCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog_path, cls.catalog = trigger_catalog()
        cls.cases = [case for case in cls.catalog["cases"] if case["layer"] == "trigger"]
        cls.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        cls.shared_skills = {
            path.parent.name for path in (PLUGIN_ROOT / "skills").glob("*/SKILL.md")
        }

    def selection(self, case: dict[str, object]) -> tuple[str, list[str]]:
        self.assertEqual(len(case["checks"]), 1, case["id"])
        check = case["checks"][0]
        self.assertEqual(check["type"], "selection", case["id"])
        self.assertEqual(check["allowed_extra"], [], case["id"])
        expected = check["expected"]
        self.assertLessEqual(len(expected), 1, case["id"])
        claude_skill = case["hosts"]["claude"]["skill"]
        codex_skill = case["hosts"]["codex"]["skill"]
        self.assertEqual(claude_skill, f"speckit-pro:{codex_skill}", case["id"])
        return codex_skill, expected

    def provenance_entry(self, reference: str) -> tuple[str, str, dict[str, object]]:
        source_name, separator, identity = reference.partition("#")
        self.assertEqual(separator, "#", reference)
        source = REPO_ROOT / source_name
        self.assertTrue(source.is_file(), reference)
        host = "codex" if "codex-evals" in source.parts else "claude"
        target = source.stem.removesuffix("-trigger")
        entries = json.loads(source.read_text(encoding="utf-8"))
        matches = [entry for entry in entries if legacy_case_id(host, target, entry) == identity]
        self.assertEqual(len(matches), 1, reference)
        return host, target, matches[0]

    def test_catalog_matches_supported_audit_matrix_and_keeps_gaps_explicit(self) -> None:
        counts = self.audit["counts"]
        matrix = self.audit["coverage_matrix"]
        gaps = self.audit["unresolved_requirements"]
        self.assertEqual(len(self.cases), 109)
        self.assertEqual(counts["proposed_canonical_cases"], 109)
        self.assertEqual(counts["supported_source_cases"], 209)
        self.assertEqual(counts["blocked_source_cases"], 8)
        self.assertEqual(counts["blocked_requirements"], 5)
        self.assertEqual(len(matrix), 109)
        self.assertEqual(len(gaps), 5)

        by_id = {row["canonical_case_id"]: row for row in matrix}
        self.assertEqual(set(by_id), {case["id"] for case in self.cases})
        for case in self.cases:
            target, expected = self.selection(case)
            row = by_id[case["id"]]
            self.assertEqual(row["status"], "supported", case["id"])
            self.assertEqual(row["target_skill"], target, case["id"])
            self.assertEqual(row["expected_activations"], expected, case["id"])
            self.assertEqual(row["prompt"], case["prompt"], case["id"])

        gap_sources = {
            source_id
            for gap in gaps
            for key in ("claude_source_case_ids", "codex_source_case_ids")
            for source_id in gap[key]
        }
        source_rows = {row["case_id"]: row for row in self.audit["source_cases"]}
        self.assertEqual(len(gap_sources), 8)
        self.assertTrue(all(source_rows[item]["counterpart_status"] == "blocked" for item in gap_sources))
        self.assertTrue(all(gap["gap_id"] == "native-agent-availability-bootstrap" for gap in gaps))
        self.assertTrue(all(gap["status"] == "moved-to-functional-integration-gap" for gap in gaps))
        self.assertTrue(all(gap["expected_activations"] == ["install"] for gap in gaps))

        catalog_sources = {ref.partition("#")[2] for case in self.cases for ref in case["provenance"]}
        self.assertEqual(len(catalog_sources), 209)
        self.assertTrue(gap_sources.isdisjoint(catalog_sources))
        self.assertNotIn("install", {
            skill for case in self.cases for skill in case["checks"][0]["expected"]
        })

    def test_provenance_binds_each_measured_target_and_original_polarity(self) -> None:
        referenced: set[str] = set()
        installer_adaptations = 0
        merged_sibling_evidence = 0
        for case in self.cases:
            target, expected = self.selection(case)
            self.assertIn(target, self.shared_skills, case["id"])
            self.assertIn(len(case["provenance"]), {1, 2, 4}, case["id"])
            for reference in case["provenance"]:
                host, source_target, entry = self.provenance_entry(reference)
                source_id = reference.partition("#")[2]
                self.assertNotIn(source_id, referenced, reference)
                referenced.add(source_id)
                rendered_prompt = case["prompt"].replace(
                    "{{skill}}", case["hosts"][host]["skill"],
                )
                self.assertEqual(rendered_prompt, entry["query"], reference)
                if source_target != target:
                    self.assertIs(entry["should_trigger"], False, reference)
                    self.assertEqual(expected, [target], reference)
                    if source_target == "install":
                        installer_adaptations += 1
                        self.assertEqual(host, "codex", reference)
                        self.assertIn("installer target is irrelevant", case["capability"], reference)
                    else:
                        merged_sibling_evidence += 1
                        self.assertEqual(source_target, "grill-me", reference)
                        self.assertEqual(target, "speckit-autopilot", reference)
                        self.assertIn("do not select grill-me", case["capability"], reference)
                elif entry["should_trigger"] is True:
                    self.assertEqual(expected, [target], reference)
                else:
                    self.assertNotIn(target, expected, reference)
        self.assertEqual(len(referenced), 209)
        self.assertEqual(installer_adaptations, 3)
        self.assertEqual(merged_sibling_evidence, 2)

    def test_cases_stage_exact_native_targets_and_complete_sibling_catalogs(self) -> None:
        source_roots = {
            "claude": PLUGIN_ROOT / "skills",
            "codex": PLUGIN_ROOT / "codex-skills",
        }
        rosters = {
            host: {path.parent.name for path in root.glob("*/SKILL.md")}
            for host, root in source_roots.items()
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, case in enumerate(self.cases):
                target, expected = self.selection(case)
                for host in ("claude", "codex"):
                    settings = case["hosts"][host]
                    plugin_name = settings["skill"].partition(":")[0] if host == "claude" else "speckit-pro"
                    staged = stage_trigger_catalog(
                        host,
                        source_roots[host],
                        root / f"{index:03d}-{host}",
                        target,
                        f"catalog-trigger/{case['id']}/{host}/1",
                        plugin_name=plugin_name,
                    )
                    self.assertEqual(staged.target_skill, target, case["id"])
                    self.assertEqual(staged.native_target, settings["skill"], case["id"])
                    self.assertEqual(set(staged.source_identities), rosters[host], case["id"])
                    self.assertEqual(
                        set(staged.staged_identities), rosters[host] | {"no-speckit-skill"},
                        case["id"],
                    )
                    self.assertEqual(
                        set(staged.sibling_skills),
                        (rosters[host] | {"no-speckit-skill"}) - {target},
                        case["id"],
                    )
                    self.assertTrue(set(expected) <= set(staged.staged_identities), case["id"])

    def test_selection_checks_are_sensitive_to_no_wrong_and_conflicting_outcomes(self) -> None:
        for case in self.cases:
            target, expected = self.selection(case)
            alternatives = sorted(self.shared_skills - set(expected))
            wrong = target if target not in expected else alternatives[0]
            conflicting = [*expected, wrong]
            if not expected:
                conflicting.append(next(skill for skill in alternatives if skill != wrong))

            self.assertEqual(grade_observation(case, observation(expected))["status"], "pass", case["id"])
            self.assertEqual(grade_observation(case, observation([wrong]))["status"], "fail", case["id"])
            self.assertEqual(
                grade_observation(case, observation(conflicting))["status"], "fail", case["id"],
            )
            no_selection = grade_observation(case, observation([]))["status"]
            self.assertEqual(no_selection, "pass" if not expected else "fail", case["id"])

    def test_behavior_distinctions_negative_controls_and_fixtures_are_explicit(self) -> None:
        counts = {"positive_self": 0, "sibling_route": 0, "contextual_none": 0}
        templated = 0
        fixture_cases = 0
        identities: set[tuple[str, str]] = set()
        for case in self.cases:
            target, expected = self.selection(case)
            identity = (target, case["prompt"])
            self.assertNotIn(identity, identities, case["id"])
            identities.add(identity)
            self.assertEqual(set(case["native_differences"]), NATIVE_DIFFERENCES, case["id"])
            self.assertEqual(case["hosts"]["claude"]["allowed_tools"], ["Skill"], case["id"])
            self.assertEqual(case["hosts"]["codex"]["allowed_tools"], ["command_execution"], case["id"])
            self.assertEqual(case["hosts"]["claude"]["modes"], ["plugin"], case["id"])
            self.assertEqual(case["hosts"]["codex"]["modes"], ["project"], case["id"])
            if expected == [target]:
                counts["positive_self"] += 1
                self.assertIn(f"Select {target}", case["capability"], case["id"])
            elif expected:
                counts["sibling_route"] += 1
                self.assertIn(f"Select {expected[0]}", case["capability"], case["id"])
                self.assertIn(f"do not select {target}", case["capability"], case["id"])
            else:
                counts["contextual_none"] += 1
                self.assertIn("Select no SpecKit skill", case["capability"], case["id"])
                self.assertIn(target, case["capability"], case["id"])
            if "{{skill}}" in case["prompt"]:
                templated += 1
                self.assertEqual(expected, [target], case["id"])
            if case["fixtures"]:
                fixture_cases += 1
                for fixture in case["fixtures"]:
                    self.assertIn(fixture["destination"], case["prompt"], case["id"])

        self.assertEqual(counts, self.audit["counts"]["canonical_coverage_kinds"])
        self.assertEqual(counts, {"positive_self": 51, "sibling_route": 45, "contextual_none": 13})
        self.assertEqual(templated, 11)
        self.assertEqual(fixture_cases, 10)


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeTriggerCatalogTests),
        label="test-native-trigger-catalog",
    ))
