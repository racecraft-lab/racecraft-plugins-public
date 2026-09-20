#!/usr/bin/env python3
"""Owner tests for the authored functional rows in the native catalog."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
SHARD_PATH = TEST_ROOT / "evals" / "catalog-functional.json"
CATALOG_PATH = SHARD_PATH if SHARD_PATH.is_file() else TEST_ROOT / "evals" / "catalog.json"
SELECTION_PATH = TEST_ROOT / "evals" / "fixtures" / "functional" / "legacy-selection.json"
EXAMPLES_PATH = TEST_ROOT / "evals" / "fixtures" / "functional" / "criterion-examples.json"
AUDIT_PATH = TEST_ROOT / "evals" / "audit" / "functional-inventory.json"
sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_catalog import load_catalog, validate_catalog  # noqa: E402
from native_eval_adapters import _stage_fixture_plan  # noqa: E402
from native_eval_fixture_setup import materialize_workspace  # noqa: E402
from native_eval_grading import grade_observation  # noqa: E402
from test_result import run_counted  # noqa: E402


ALIASES = {
    "/speckit-pro:speckit-install": "the host-native speckit-install capability",
    "$speckit-install": "the host-native speckit-install capability",
    "/speckit-pro:coach": "the host-native speckit-coach capability",
    "$speckit-coach": "the host-native speckit-coach capability",
    "/speckit-pro:speckit-scaffold-spec": "the host-native speckit-scaffold-spec capability",
    "$speckit-scaffold-spec": "the host-native speckit-scaffold-spec capability",
    "/speckit-pro:speckit-autopilot": "the host-native speckit-autopilot capability",
    "$speckit-autopilot": "the host-native speckit-autopilot capability",
    "/speckit-pro:grill-me": "the host-native grill-me capability",
    "$grill-me": "the host-native grill-me capability",
    "/speckit-clarify": "the host-native speckit-clarify capability",
    "$speckit-clarify": "the host-native speckit-clarify capability",
    "Skill('grill-me')": "the native grill-me capability",
    " via spawn_agent": " through native subagent dispatch",
    "Codex autopilot": "autopilot",
    "the Codex autopilot": "the autopilot",
    "same Plan executor": "same native Plan executor",
    "spawns the author": "invokes the author",
    "same phase-executor": "same native Plan executor",
    "canonical Codex Post": "canonical native-client Post",
    "Runs ${CLAUDE_PLUGIN_ROOT}/scripts/ubiquitous-language-lint.py":
        "Runs the host-runtime ubiquitous-language-lint.py",
    "Runs resolved_python <plugin-root>/scripts/ubiquitous-language-lint.py":
        "Runs the host-runtime ubiquitous-language-lint.py",
}

EXPECTED_GAPS = {
    "functional.speckit-autopilot.case-7": "host-divergent-canonical-sequence",
    "functional.speckit-autopilot.case-25": "host-divergent-canonical-position",
    "functional.speckit-status.case-1": "missing-worktree-materialization",
}
EXPECTED_SCENARIO_GAPS = set()

GROUNDED_IDS = {
    "functional.speckit-coach.case-2",
    "functional.speckit-status.case-2",
    "functional.speckit-status.case-5",
    "functional.speckit-status.case-6",
}
SCAFFOLD_FIXTURE_IDS = {"functional.speckit-scaffold-spec.case-3"}
SCAFFOLD_DIAGNOSTIC_IDS = {"functional.speckit-scaffold-spec.case-7"}
STATUS_SEARCH_IDS = {"functional.speckit-status.case-3", "functional.speckit-status.case-7"}
CHILD_ABORT_IDS = {"functional.grill-me.case-7"}
WORKTREE_BINDING_IDS = {
    "functional.speckit-autopilot.case-34",
    "functional.speckit-autopilot.case-106",
    "functional.speckit-autopilot.case-108",
}
ARCHIVE_EXTENSION_IDS = {"functional.speckit-autopilot.case-35"}
COACH_INSTALLED_IDS = {"functional.speckit-coach.case-8"}
AUTOPILOT_PREREQ_IDS = {"functional.speckit-autopilot.case-1"}
STATUS_WORKTREE_IDS = {"functional.speckit-status.case-4"}
SCAFFOLD_HANDOFF_IDS = {"functional.speckit-scaffold-spec.case-2-handoff"}
COACH_ARCHIVE_IDS = {"functional.speckit-coach.case-14"}
SCENARIO_IDS = {
    "functional.speckit-autopilot.case-29",
    "functional.speckit-autopilot.case-30",
    "functional.speckit-autopilot.case-36",
    "functional.speckit-autopilot.case-111",
    "functional.speckit-autopilot.case-112",
}
PLAN_REPAIR_IDS = {
    "functional.speckit-autopilot.case-111",
    "functional.speckit-autopilot.case-112",
}
LOCAL_COMMAND_IDS = {
    "functional.speckit-autopilot.case-2",
    "functional.ubiquitous-language.case-3",
}
REDIRECT_IDS = {"functional.speckit-coach.case-7"}
DASHBOARD_IDS = {"functional.speckit-status.case-1"}
WORKTREE_MIGRATION_IDS = {"functional.speckit-autopilot.case-107"}
NATIVE_RESPONSE_IDS = {
    "functional.speckit-autopilot.case-7", "functional.speckit-autopilot.case-25",
}
LOCAL_COMMAND_LEGACY_SOURCES = {
    "functional.speckit-autopilot.case-2": (
        ("layer3-functional/evals/speckit-autopilot-evals.json", 2),
        ("layer3-functional/codex-evals/speckit-autopilot-evals.json", 2),
    ),
    "functional.ubiquitous-language.case-3": (
        ("layer3-functional/evals/ubiquitous-language-evals.json", 3),
        ("layer3-functional/codex-evals/ubiquitous-language-evals.json", 3),
    ),
}
SCENARIO_LEGACY_SOURCES = {
    "functional.speckit-autopilot.case-29": (
        ("layer3-functional/evals/speckit-autopilot-evals.json", 23),
        ("layer3-functional/codex-evals/speckit-autopilot-evals.json", 29),
    ),
    "functional.speckit-autopilot.case-30": (
        ("layer3-functional/codex-evals/speckit-autopilot-evals.json", 30),
    ),
    "functional.speckit-autopilot.case-36": (
        ("layer3-functional/codex-evals/speckit-autopilot-evals.json", 36),
    ),
    "functional.speckit-autopilot.case-111": (
        ("layer3-functional/evals/speckit-autopilot-evals.json", 111),
        ("layer3-functional/codex-evals/speckit-autopilot-evals.json", 111),
    ),
    "functional.speckit-autopilot.case-112": (
        ("layer3-functional/evals/speckit-autopilot-evals.json", 112),
        ("layer3-functional/codex-evals/speckit-autopilot-evals.json", 112),
    ),
}
GROUNDED_LEGACY_SOURCES = {
    "functional.speckit-coach.case-2": (
        ("layer3-functional/evals/speckit-coach-evals.json", 2),
        ("layer3-functional/codex-evals/speckit-coach-evals.json", 2),
    ),
    "functional.speckit-status.case-2": (
        ("layer3-functional/codex-evals/speckit-status-evals.json", 2),
    ),
    "functional.speckit-status.case-5": (
        ("layer3-functional/codex-evals/speckit-status-evals.json", 5),
    ),
    "functional.speckit-status.case-6": (
        ("layer3-functional/codex-evals/speckit-status-evals.json", 6),
    ),
}
GROUNDING_SENTINELS = {
    "functional.speckit-coach.case-2": (
        "at least one accurate, non-prompt fact", "acceptable disjunctive anchors",
        "POST /deliveries", "response field", "retry classification", "attempt limit",
        "exponential backoff", "Idempotency-Key", "exact signed bytes", "HMAC-SHA256",
        "freshness or 401", "secret handling and non-exposure",
    ),
    "functional.speckit-status.case-2": (
        "SPEC-013 Search & Database", "Phase 3 Plan", "no current blocker",
    ),
    "functional.speckit-status.case-5": (
        "docs/ai/current-quarter-technical-roadmap.md", "SPEC-030 Current Search",
        "docs/ai/last-quarter-technical-roadmap.md", "SPEC-029 Historical Search",
    ),
    "functional.speckit-status.case-6": (
        "SPEC-040 Reporting", "SPEC-041", "SPEC-042 Export", "SPEC-043",
    ),
}
FROZEN_GROUNDING_COPIES = {
    "evals/fixtures/grounding/coach-checklist/spec.md":
        "layer3-functional/fixtures/headless/coach-webhook-project/spec.md",
    "evals/fixtures/grounding/status-specific/docs/ai/current-technical-roadmap.md":
        "layer3-functional/fixtures/status/scenario-roots/spec-specific/docs/ai/current-technical-roadmap.md",
    "evals/fixtures/grounding/status-specific/docs/ai/specs/SPEC-013-workflow.md":
        "layer3-functional/fixtures/status/scenario-roots/spec-specific/docs/ai/specs/SPEC-013-workflow.md",
    "evals/fixtures/grounding/status-multiple/docs/ai/current-quarter-technical-roadmap.md":
        "layer3-functional/fixtures/status/scenario-roots/multiple-roadmaps/docs/ai/current-quarter-technical-roadmap.md",
    "evals/fixtures/grounding/status-multiple/docs/ai/last-quarter-technical-roadmap.md":
        "layer3-functional/fixtures/status/scenario-roots/multiple-roadmaps/docs/ai/last-quarter-technical-roadmap.md",
    "evals/fixtures/grounding/status-blocked/docs/ai/current-technical-roadmap.md":
        "layer3-functional/fixtures/status/scenario-roots/all-blocked/docs/ai/current-technical-roadmap.md",
}

EXPECTED_SEMANTIC_OVERLAYS = {
    ("functional.speckit-autopilot.case-15", "legacy-09-semantic"):
        "PASS only if the evidence identifies the Clarify Question Set as the clarify-executor handoff returned to the parent. "
        "FAIL if the named set has another role, the handoff direction is contradicted, or the phrase is merely named.",
    ("functional.speckit-autopilot.case-24", "legacy-01-semantic"):
        "PASS only if the evidence identifies confidence-gate as a read-only runner helper and workflow_file, mode_name, and threshold as its inputs. "
        "FAIL if the helper role or input relationship is omitted, contradicted, or merely implied by adjacent names.",
    ("functional.speckit-autopilot.case-24", "legacy-10-semantic"):
        "PASS only if the evidence says resolve-confidence-mode checks each listed local configuration path as a default. "
        "FAIL if either path is not a checked default, if the relationship is contradicted, or if the paths are merely named.",
    ("functional.speckit-coach.case-1", "legacy-04-semantic"):
        "PASS only if the evidence identifies specify, clarify, plan, checklist, tasks, analyze, and implement as the seven SDD phases in that order. "
        "FAIL if the sequence relationship is negated, contradicted, or the phase names are merely listed.",
    ("functional.speckit-scaffold-spec.case-5", "legacy-02-semantic"):
        "PASS only if the answer says the failure report must identify the locally created branch, worktree, workflow file, and commit. "
        "Concrete identities are not required because the prompt does not supply them. FAIL if any category is omitted or the answer invents a value.",
    ("functional.speckit-scaffold-spec.case-5", "legacy-04-semantic"):
        "PASS only if the answer directs the user to resolve the remote rejection and retry the push from the existing worktree without recreating the branch, worktree, workflow, or commit. "
        "FAIL if retry context is omitted or local work is discarded.",
}


def normalize_legacy_requirement(text: str) -> str:
    for old, new in ALIASES.items():
        text = text.replace(old, new)
    return " ".join(text.replace("the the ", "the ").split())


def observation(
    *,
    activation: str,
    final_text: str = "",
    tool_calls: list[dict] | None = None,
    artifacts: dict[str, str] | None = None,
) -> dict:
    return {
        "completed": True,
        "error": None,
        "final_text": final_text,
        "activations": [activation],
        "tool_calls": tool_calls or [],
        "artifacts": artifacts or {},
        "usage": {},
    }


def one_check_case(case: dict, check: dict) -> dict:
    requirement = next(item for item in case["requirements"] if item["id"] == check["requirement"])
    return {"requirements": [requirement], "checks": [check]}


def semantic_verdicts(case: dict, passed: bool) -> dict:
    return {
        check["id"]: {"passed": passed, "evidence": ["mock-semantic-verdict"]}
        for check in case["checks"] if check["type"] == "semantic"
    }


def grounded_observation(case: dict, host: str, *, final_text: str = "grounded response") -> dict:
    paths = [check["path"] for check in case["checks"] if check["type"] == "file_access"]
    if host == "claude":
        calls = [
            {"name": "Read", "input": {"file_path": path}, "output": "captured", "success": True}
            for path in paths
        ]
    else:
        calls = [
            {
                "name": "command_execution", "input": {"command": f"cat -- {path}"},
                "output": "captured", "success": True,
            }
            for path in paths
        ]
    return observation(
        activation=case["hosts"][host]["skill"].split(":")[-1],
        final_text=final_text,
        tool_calls=calls,
    )


def _assert_scenario_legacy_boundaries(
    test: unittest.TestCase,
    cases: dict[str, dict],
    selection: dict,
) -> None:
    for case_id, sources in SCENARIO_LEGACY_SOURCES.items():
        case = cases[case_id]
        test.assertEqual(
            case["provenance"],
            [f"tests/speckit-pro/{source}#eval-id={eval_id}" for source, eval_id in sources],
            case_id,
        )
        test.assertTrue(any(check["type"] == "semantic" for check in case["checks"]), case_id)
        test.assertTrue(any(check["type"] == "file_access" for check in case["checks"]), case_id)
        for source, eval_id in sources:
            legacy = json.loads((TEST_ROOT / source).read_text(encoding="utf-8"))
            entry = next(row for row in legacy["evals"] if row["id"] == eval_id)
            mapped = next(row for row in selection["selected"] if row["case_id"] == case_id)
            boundary = next(row for row in mapped["sources"] if row["eval_id"] == eval_id)
            test.assertEqual(len(boundary["expectations"]), len(entry["expectations"]))


def _assert_relocation_checks(test: unittest.TestCase, cases: dict[str, dict]) -> None:
    relocation = cases["functional.speckit-autopilot.case-29"]
    test.assertEqual(
        {check["id"] for check in relocation["checks"] if check["type"] == "file_exists"},
        {"no-relocated-analysis", "no-relocated-uat"},
    )
    test.assertEqual(
        {check["id"] for check in relocation["checks"] if check["type"] == "text"},
        {"candidate-analysis-unchanged", "candidate-uat-unchanged"},
    )


def _assert_layer_plan_checks(test: unittest.TestCase, cases: dict[str, dict]) -> None:
    layer_plan = cases["functional.speckit-autopilot.case-30"]
    prompt = layer_plan["prompt"]
    test.assertIn("four independent scenarios after G5", prompt)
    test.assertIn("top-level receipt keys valid, invalid, input_error, and non_split", prompt)
    test.assertIn("derive every recorded value and action", prompt)
    test.assertEqual(layer_plan["required_tools"], ["specify"])
    test.assertIn("git_fixture", layer_plan)
    for request in ("valid-request.json", "invalid-request.json", "input-error-request.json"):
        test.assertEqual(
            prompt.count(
                f"{{{{resolved_python}}}} -m speckit_pro_runner < scenario-inputs/{request}"
            ),
            1,
        )
    for leaked_answer in (
        "status skipped",
        "helper_invoked false",
        "persist the valid response's complete data.stdout_json",
        "exact exit-1 stop line",
    ):
        test.assertNotIn(leaked_answer, prompt)
    layer_checks = {check["id"] for check in layer_plan["checks"]}
    test.assertTrue(
        {
            "valid-exit", "invalid-exit", "input-error-exit", "non-split-skipped",
            "exact-three-invocations", "gate-order", "request-contract",
            "no-pr-side-effects", "valid-native-result", "invalid-native-result",
            "input-error-native-result",
        } <= layer_checks
    )


def _assert_broken_archive_checks(test: unittest.TestCase, cases: dict[str, dict]) -> None:
    broken_archive = cases["functional.speckit-autopilot.case-36"]
    archive_checks = {check["id"] for check in broken_archive["checks"]}
    test.assertTrue(
        {
            "missing-command", "blocked-status", "cleanup-disabled",
            "invocation-unavailable", "exact-missing-path", "archive-item-pending",
            "phase-zero-pending", "manual-inventory-rejected",
            "no-no-candidates-substitution",
        } <= archive_checks
    )


class NativeFunctionalCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        loaded = load_catalog(CATALOG_PATH, REPO_ROOT)
        cls.loaded = loaded
        cls.all_cases = {case["id"]: case for case in loaded["cases"]}
        cls.catalog = {**loaded, "cases": [case for case in loaded["cases"] if case["layer"] == "functional"]}
        cls.selection = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))
        cls.examples = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))
        cls.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        cls.cases = {case["id"]: case for case in cls.catalog["cases"]}

    def test_shard_is_functional_paired_and_schema_valid(self) -> None:
        selected_ids = {row["case_id"] for row in self.selection["selected"]}
        response_only_ids = (
            (selected_ids | NATIVE_RESPONSE_IDS)
            - SCAFFOLD_FIXTURE_IDS - SCAFFOLD_DIAGNOSTIC_IDS - STATUS_SEARCH_IDS - CHILD_ABORT_IDS
            - WORKTREE_BINDING_IDS - ARCHIVE_EXTENSION_IDS - COACH_INSTALLED_IDS - COACH_ARCHIVE_IDS - AUTOPILOT_PREREQ_IDS - STATUS_WORKTREE_IDS - SCAFFOLD_HANDOFF_IDS - SCENARIO_IDS - LOCAL_COMMAND_IDS
            - REDIRECT_IDS - WORKTREE_MIGRATION_IDS
        )
        self.assertEqual(len(response_only_ids), 65)
        self.assertEqual(len(self.all_cases), 207)
        self.assertEqual(len(self.catalog["cases"]), 93)
        self.assertEqual(set(self.cases), selected_ids | GROUNDED_IDS | NATIVE_RESPONSE_IDS | DASHBOARD_IDS)
        selected = {row["case_id"]: row for row in self.selection["selected"]}
        for case in self.catalog["cases"]:
            self.assertEqual(case["layer"], "functional")
            self.assertEqual(set(case["hosts"]), {"claude", "codex"})
            if case["id"] in CHILD_ABORT_IDS:
                self.assertEqual(case["timeout_seconds"], 300)
                self.assertEqual(case["resource_class"], "nested")
            elif case["id"] in PLAN_REPAIR_IDS:
                self.assertEqual(case["timeout_seconds"], 600)
                self.assertEqual(case["resource_class"], "nested")
                self.assertEqual(case["required_tools"], ["specify"])
            else:
                self.assertEqual(case["timeout_seconds"], 300)
                self.assertEqual(case["resource_class"], "ordinary")
            self.assertNotIn("Schema-valid", case["capability"])
            self.assertFalse(any("observable response satisfies" in row["description"] for row in case["requirements"]))
            if case["id"] in GROUNDED_IDS | SCAFFOLD_FIXTURE_IDS | SCAFFOLD_DIAGNOSTIC_IDS | STATUS_SEARCH_IDS | CHILD_ABORT_IDS | WORKTREE_BINDING_IDS | ARCHIVE_EXTENSION_IDS | COACH_INSTALLED_IDS | COACH_ARCHIVE_IDS | AUTOPILOT_PREREQ_IDS | STATUS_WORKTREE_IDS | SCAFFOLD_HANDOFF_IDS | SCENARIO_IDS | LOCAL_COMMAND_IDS | REDIRECT_IDS | NATIVE_RESPONSE_IDS | DASHBOARD_IDS | WORKTREE_MIGRATION_IDS:
                continue
            self.assertEqual(case["fixtures"], [], case["id"])
            self.assertFalse(any(check["type"] == "tool_used" for check in case["checks"]), case["id"])
            self.assertEqual(
                selected[case["id"]]["deterministic_text_checks"],
                sum(check["type"] == "text" for check in case["checks"]),
                case["id"],
            )
            self.assertEqual(
                selected[case["id"]]["semantic_checks"],
                sum(check["type"] == "semantic" for check in case["checks"]),
                case["id"],
            )
        self.assertEqual(
            sum(check["type"] == "text" for case in self.catalog["cases"] for check in case["checks"]),
            22,
        )
        self.assertEqual(
            sum(
                check["type"] == "text"
                for case_id in SCENARIO_IDS
                for check in self.cases[case_id]["checks"]
            ),
            10,
        )

    def test_cross_layer_reuse_preserves_every_legacy_expectation_without_duplicate_launches(self) -> None:
        reused = self.selection["cross_layer_reuse"]
        direct_sources = {
            (source["host"], source["source"], source["eval_id"])
            for row in self.selection["selected"] + self.selection["resolved_exclusions"]
            for source in row.get("sources", row.get("legacy_boundaries", []))
        }
        self.assertEqual([row["canonical_case_id"] for row in reused],
                         ["functional.speckit-scaffold-spec.case-8"])
        self.assertEqual(len(self.cases) + len(reused), 94)
        for row in reused:
            self.assertEqual(row["disposition"], "merge")
            self.assertNotIn(row["canonical_case_id"], self.all_cases)
            case = self.all_cases[row["case_id"]]
            self.assertEqual(case["layer"], "parity")
            self.assertEqual(set(case["hosts"]), {"claude", "codex"})
            self.assertEqual({source["host"] for source in row["sources"]}, {"claude", "codex"})
            requirements = {item["id"] for item in case["requirements"]}
            executable = {check["requirement"] for check in case["checks"]}
            for source in row["sources"]:
                self.assertNotIn((source["host"], source["source"], source["eval_id"]), direct_sources)
                legacy = json.loads((REPO_ROOT / source["source"]).read_text())
                original = next(item for item in legacy["evals"] if item["id"] == source["eval_id"])
                self.assertEqual(source["legacy_expectations"], original["expectations"])
                self.assertEqual([item["expectation_index"] for item in source["expectations"]],
                                 list(range(len(original["expectations"]))))
                for expectation in source["expectations"]:
                    self.assertTrue(expectation["requirement_ids"])
                    self.assertLessEqual(set(expectation["requirement_ids"]), requirements & executable)
            continuation = next(check for check in case["checks"] if check["id"] == "capability-correctness")
            self.assertIn("remaining scaffold workflow", continuation["rubric"])
            self.assertIn("normal prerequisites", continuation["rubric"])

    def test_every_selected_legacy_expectation_maps_to_shared_requirement(self) -> None:
        for selected in self.selection["selected"]:
            requirements = {row["id"]: row["description"] for row in self.cases[selected["case_id"]]["requirements"]}
            mapped_ids = set()
            for source in selected["sources"]:
                legacy = json.loads((REPO_ROOT / source["source"]).read_text(encoding="utf-8"))
                entry = next(row for row in legacy["evals"] if row["id"] == source["eval_id"])
                if "legacy_expectations" in source:
                    self.assertEqual(source["legacy_expectations"], entry["expectations"])
                for mapping in source["expectations"]:
                    if "requirement_ids" in mapping:
                        self.assertTrue(mapping["requirement_ids"])
                        self.assertLessEqual(set(mapping["requirement_ids"]), set(requirements))
                        mapped_ids.update(mapping["requirement_ids"])
                        continue
                    expected = normalize_legacy_requirement(entry["expectations"][mapping["expectation_index"]])
                    if selected["case_id"] in REDIRECT_IDS:
                        expected = expected.replace("as the correct command", "as the correct entrypoint")
                    if selected["case_id"] not in {
                        "functional.speckit-autopilot.case-17",
                        "functional.speckit-autopilot.case-18",
                        "functional.speckit-autopilot.case-21",
                    }:
                        self.assertEqual(requirements[mapping["requirement_id"]], expected)
                    mapped_ids.add(mapping["requirement_id"])
            catalog_ids = {key for key in requirements if key.startswith("legacy-")}
            if selected["case_id"] in WORKTREE_MIGRATION_IDS:
                self.assertEqual(mapped_ids, {"binding", "preservation"})
            elif selected["case_id"] in SCAFFOLD_DIAGNOSTIC_IDS:
                self.assertEqual(mapped_ids, {"diagnosis"})
            elif selected["case_id"] in STATUS_SEARCH_IDS:
                self.assertEqual(mapped_ids, {"behavior"})
            elif selected["case_id"] in CHILD_ABORT_IDS:
                self.assertEqual(mapped_ids, {"refusal", "mechanism", "no-artifacts"})
            elif selected["case_id"] in WORKTREE_BINDING_IDS:
                expected = {
                    "functional.speckit-autopilot.case-34": {"binding", "planning"},
                    "functional.speckit-autopilot.case-106": {"binding", "safety"},
                    "functional.speckit-autopilot.case-108": {"revalidation", "safety"},
                }[selected["case_id"]]
                self.assertEqual(mapped_ids, expected)
            elif selected["case_id"] in ARCHIVE_EXTENSION_IDS:
                self.assertEqual(mapped_ids, {"contract", "recording", "continuation"})
            elif selected["case_id"] in COACH_INSTALLED_IDS:
                self.assertEqual(mapped_ids, {"observation", "behavior"})
            elif selected["case_id"] in AUTOPILOT_PREREQ_IDS:
                self.assertEqual(mapped_ids, {"helper", "reporting"})
            elif selected["case_id"] in STATUS_WORKTREE_IDS:
                self.assertEqual(mapped_ids, {"discovery", "reporting"})
            elif selected["case_id"] in SCAFFOLD_HANDOFF_IDS:
                self.assertEqual(mapped_ids, {f"legacy-{i:02d}" for i in range(1, 7)})
            elif selected["case_id"] in COACH_ARCHIVE_IDS:
                self.assertEqual(mapped_ids, {"inspection", "proposal", "hook-claims"})
            else:
                self.assertEqual(catalog_ids, mapped_ids, selected["case_id"])

    def test_exclusions_are_explicit_non_vacuous_gaps(self) -> None:
        prior_exclusions = {row["case_id"]: row for row in self.selection["excluded"]}
        scenario_gaps = {
            key: row for key, row in prior_exclusions.items() if key in EXPECTED_SCENARIO_GAPS
        }
        gaps = {
            key: row for key, row in prior_exclusions.items()
            if key not in GROUNDED_IDS | set(EXPECTED_SCENARIO_GAPS)
        }
        represented = {row["case_id"]: row for row in self.selection.get("resolved_exclusions", [])}
        current_gaps = self.audit["native_catalog"]["held_early_candidates"]
        self.assertEqual({key: row["gap_code"] for key, row in current_gaps.items()}, EXPECTED_GAPS)
        self.assertEqual(set(gaps), (set(EXPECTED_GAPS) - set(self.cases)) - set(EXPECTED_SCENARIO_GAPS))
        self.assertEqual(set(scenario_gaps), set(EXPECTED_SCENARIO_GAPS))
        self.assertEqual(set(represented), GROUNDED_IDS | NATIVE_RESPONSE_IDS | DASHBOARD_IDS)
        self.assertEqual(
            len(self.selection["selected"]) + len(represented) + len(gaps) + len(scenario_gaps),
            94,
        )
        self.assertFalse(set(self.cases) & (set(gaps) | set(scenario_gaps)))
        self.assertTrue(GROUNDED_IDS <= set(self.cases))
        for row in (*gaps.values(), *scenario_gaps.values()):
            self.assertTrue(row["legacy_ids"])
            self.assertGreaterEqual(len(row["reason"]), 40)
            self.assertGreaterEqual(len(row["required_replacement"]), 40)
            self.assertNotIn(row["case_id"], self.cases)
            self.assertEqual(len(row["legacy_ids"]), len(row["legacy_boundaries"]))
            for boundary in row["legacy_boundaries"]:
                legacy = json.loads((REPO_ROOT / boundary["source"]).read_text(encoding="utf-8"))
                entry = next(item for item in legacy["evals"] if item["id"] == boundary["eval_id"])
                self.assertEqual(boundary["expectations"], entry["expectations"])
        frozen_inventory = self.audit["native_catalog"]
        self.assertEqual(frozen_inventory["represented"], 94)
        self.assertEqual(frozen_inventory["held"], 33)
        self.assertEqual(frozen_inventory["response_only"], 65)
        self.assertEqual(frozen_inventory["file_grounded"], 28)
        self.assertEqual(frozen_inventory["held_early_candidates"], current_gaps)
        self.assertEqual(
            frozen_inventory["represented"],
            len(self.cases) + len(self.selection["cross_layer_reuse"]),
        )
        self.assertEqual(
            frozen_inventory["held"],
            127 - len(self.catalog["cases"]) - len(self.selection["cross_layer_reuse"]),
        )
        self.assertEqual(127 - len(self.catalog["cases"]) - len(self.selection["cross_layer_reuse"]), 33)

    def test_native_response_contracts_keep_exact_source_steps_and_legacy_coverage(self) -> None:
        case = self.cases["functional.speckit-autopilot.case-7"]
        sequence = next(check for check in case["checks"] if check["id"] == "native-sequence")
        sources = {
            "claude": "speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md",
            "codex": "speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md",
        }
        for host, source in sources.items():
            names = re.findall(r'^  "(Post: [^"<]+)"', (REPO_ROOT / source).read_text(), re.MULTILINE)
            self.assertEqual(sequence["expected_by_host"][host], names)
        for case_id in NATIVE_RESPONSE_IDS:
            native_case = self.cases[case_id]
            deterministic = [c for c in native_case["checks"] if c["type"] == "response_json_field"]
            for host in ("claude", "codex"):
                body = {c["field_path"][0]: c["expected_by_host"][host] for c in deterministic}
                body["explanation"] = "mock semantic response, not native evidence"
                correct = observation(activation="speckit-autopilot", final_text=json.dumps(body))
                verdicts = semantic_verdicts(native_case, True)
                self.assertEqual(grade_observation(native_case, correct, verdicts, host=host)["status"], "pass")
                other = "codex" if host == "claude" else "claude"
                for check in deterministic:
                    if check["expected_by_host"][host] == check["expected_by_host"][other]:
                        continue
                    wrong = copy.deepcopy(body)
                    wrong[check["field_path"][0]] = check["expected_by_host"][other]
                    bad = observation(activation="speckit-autopilot", final_text=json.dumps(wrong))
                    self.assertEqual(grade_observation(native_case, bad, verdicts, host=host)["status"], "fail")
                self.assertEqual(grade_observation(native_case, correct, host=host)["status"], "needs_judge")
            record = next(row for row in self.selection["resolved_exclusions"] if row["case_id"] == case_id)
            requirements = {row["id"] for row in native_case["requirements"]}
            for boundary, coverage in zip(record["legacy_boundaries"], record["requirement_coverage"], strict=True):
                original = json.loads((REPO_ROOT / boundary["source"]).read_text())
                legacy = next(row for row in original["evals"] if row["id"] == boundary["eval_id"])
                self.assertEqual(boundary["expectations"], legacy["expectations"])
                self.assertEqual([m["expectation_index"] for m in coverage["expectations"]], list(range(len(legacy["expectations"]))))
                self.assertTrue(all(m["requirement_id"] in requirements for m in coverage["expectations"]))

    def test_active_cases_are_not_held_in_selection_ledger(self) -> None:
        selected = {row["case_id"] for row in self.selection["selected"]}
        resolved = {row["case_id"] for row in self.selection.get("resolved_exclusions", [])}
        held = {row["case_id"] for row in self.selection["excluded"]}
        self.assertFalse(set(self.cases) & held)
        self.assertFalse(selected & resolved)
        self.assertEqual(set(self.cases), selected | resolved)
        self.assertEqual(len(resolved), len(self.selection.get("resolved_exclusions", [])))

    def test_dashboard_facts_fail_independently_of_semantic_judgment(self) -> None:
        case = self.cases["functional.speckit-status.case-1"]
        expected_path = TEST_ROOT / "evals/fixtures/functional/status-dashboard/case-1/expected.json"
        expected = json.loads(expected_path.read_text())
        for host in ("claude", "codex"):
            correct = grounded_observation(case, host, final_text=json.dumps(expected["response_json"]))
            self.assertEqual(grade_observation(case, correct, host=host)["status"], "needs_judge")
            for control in expected["negative_controls"]:
                with self.subTest(host=host, control=control["id"]):
                    body = copy.deepcopy(expected["response_json"])
                    container = body
                    for key in control["field_path"][:-1]:
                        container = container[key]
                    container[control["field_path"][-1]] = control["corrupt_value"]
                    bad = grounded_observation(case, host, final_text=json.dumps(body))
                    result = grade_observation(case, bad, semantic_verdicts(case, True), host=host)
                    self.assertEqual(result["status"], "fail")

        record = next(row for row in self.selection["resolved_exclusions"] if row["case_id"] == case["id"])
        self.assertEqual(len(record["requirement_coverage"][0]["expectations"]), 4)
        self.assertFalse(any(row["source"] == str(expected_path.relative_to(REPO_ROOT)) for row in case["fixtures"]))
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            case_dir = root / "case"
            case_dir.mkdir()
            plan, _ = _stage_fixture_plan(case, REPO_ROOT, case_dir)
            plan["source_root"] = str(case_dir / plan["source_root"])
            workspace = root / "workspace"
            workspace.mkdir()
            result = materialize_workspace(plan, workspace)
            self.assertTrue(result["git_repository"]["clean"])
            self.assertFalse(list(workspace.rglob("expected.json")))
            registrations = subprocess.run(
                ["git", "worktree", "list", "--porcelain"], cwd=workspace,
                text=True, capture_output=True, check=True,
            ).stdout
            self.assertEqual(registrations.count("worktree "), 2)
            self.assertIn("branch refs/heads/scenario/spec-021", registrations)
            for fixture in case["fixtures"]:
                self.assertEqual((workspace / fixture["destination"]).read_bytes(),
                                 (REPO_ROOT / fixture["source"]).read_bytes())

    def test_coach_redirect_preserves_workflow_and_rejects_execution_attempts(self) -> None:
        case = self.cases["functional.speckit-coach.case-7"]
        fixture = case["fixtures"][0]
        self.assertEqual(fixture["destination"], "docs/ai/specs/.process/SPEC-025-workflow.md")
        contents = (REPO_ROOT / fixture["source"]).read_text(encoding="utf-8")
        correct = observation(activation="speckit-coach", artifacts={fixture["destination"]: contents})
        verdicts = semantic_verdicts(case, True)
        self.assertEqual(grade_observation(case, correct, verdicts)["status"], "pass")
        for success in (False, True):
            attempted = copy.deepcopy(correct)
            attempted["tool_calls"] = [{"name": "subagent", "input": {}, "success": success}]
            self.assertEqual(grade_observation(case, attempted, verdicts)["status"], "fail")
        for artifacts in ({}, {fixture["destination"]: contents.replace("Pending", "Completed")}):
            changed = copy.deepcopy(correct)
            changed["artifacts"] = artifacts
            self.assertEqual(grade_observation(case, changed, verdicts)["status"], "fail")
        activated = copy.deepcopy(correct)
        activated["activations"].append("speckit-autopilot")
        self.assertEqual(grade_observation(case, activated, verdicts)["status"], "fail")
        self.assertEqual(grade_observation(case, correct)["status"], "needs_judge")

    def test_audit_accounts_for_every_prior_text_and_read_search_check(self) -> None:
        audit = self.selection["text_check_audit"]
        self.assertEqual(audit["prior_text_checks"], 197)
        self.assertEqual(
            audit["literal_or_format_checks_after_audit"] + audit["reclassified_as_semantic"],
            audit["prior_text_checks"],
        )
        self.assertEqual(
            audit["literal_checks_in_adapter_gap_cases"] + audit["literal_checks_in_selected_cases"],
            audit["literal_or_format_checks_after_audit"],
        )
        adapter = self.selection["read_search_adapter_gap_audit"]
        self.assertEqual(adapter["affected_cases"], 8)
        self.assertEqual(adapter["affected_checks"], 17)
        self.assertEqual(adapter["claude"], {"Read": "read_file", "Glob": "list_files"})
        self.assertIn("unmapped", adapter["codex"]["command_execution"])

    def test_fixtures_are_dedicated_existing_and_never_runtime_specs_paths(self) -> None:
        for case in self.catalog["cases"]:
            if case["id"] not in GROUNDED_IDS | SCAFFOLD_FIXTURE_IDS | SCAFFOLD_DIAGNOSTIC_IDS | STATUS_SEARCH_IDS | CHILD_ABORT_IDS | WORKTREE_BINDING_IDS | ARCHIVE_EXTENSION_IDS | COACH_INSTALLED_IDS | COACH_ARCHIVE_IDS | AUTOPILOT_PREREQ_IDS | STATUS_WORKTREE_IDS | SCAFFOLD_HANDOFF_IDS | SCENARIO_IDS | LOCAL_COMMAND_IDS | REDIRECT_IDS | DASHBOARD_IDS | WORKTREE_MIGRATION_IDS:
                self.assertEqual(case["fixtures"], [], case["id"])
                continue
            if case["id"] in SCAFFOLD_FIXTURE_IDS:
                self.assertEqual(
                    case["fixtures"],
                    [{
                        "source": "tests/speckit-pro/evals/fixtures/scaffold-contracts/missing/roadmap.txt",
                        "destination": "docs/ai/current-technical-roadmap.md",
                    }],
                )
                self.assertTrue((REPO_ROOT / case["fixtures"][0]["source"]).is_file())
                continue
            if case["id"] in SCENARIO_IDS:
                for fixture in case["fixtures"]:
                    expected_prefix = (
                        "tests/speckit-pro/evals/fixtures/functional/autopilot-scenarios/"
                        if case["id"] in PLAN_REPAIR_IDS
                        else "tests/speckit-pro/evals/fixtures/scenario-contracts/"
                    )
                    self.assertTrue(
                        fixture["source"].startswith(expected_prefix),
                        fixture,
                    )
                    self.assertFalse(fixture["source"].startswith("specs/"), fixture)
                    self.assertTrue((REPO_ROOT / fixture["source"]).is_file(), fixture)
                continue
            if case["id"] in LOCAL_COMMAND_IDS | REDIRECT_IDS | DASHBOARD_IDS | WORKTREE_MIGRATION_IDS | SCAFFOLD_DIAGNOSTIC_IDS:
                for fixture in case["fixtures"]:
                    self.assertTrue(
                        fixture["source"].startswith(
                            "tests/speckit-pro/evals/fixtures/functional/"
                        ),
                        fixture,
                    )
                    self.assertTrue((REPO_ROOT / fixture["source"]).is_file(), fixture)
                continue
            if case["id"] in CHILD_ABORT_IDS | SCAFFOLD_HANDOFF_IDS:
                self.assertEqual(case["fixtures"], [], case["id"])
                continue
            if case["id"] in STATUS_SEARCH_IDS:
                for fixture in case["fixtures"]:
                    self.assertTrue(
                        fixture["source"].startswith(
                            "tests/speckit-pro/layer3-functional/fixtures/status/"
                        ),
                        fixture,
                    )
                    self.assertTrue((REPO_ROOT / fixture["source"]).is_file(), fixture)
                continue
            if case["id"] in WORKTREE_BINDING_IDS:
                for fixture in case["fixtures"]:
                    self.assertTrue(
                        fixture["source"].startswith(
                            "tests/speckit-pro/evals/fixtures/functional/registered-worktree-migration/"
                        ),
                        fixture,
                    )
                    self.assertTrue((REPO_ROOT / fixture["source"]).is_file(), fixture)
                continue
            if case["id"] in ARCHIVE_EXTENSION_IDS:
                for fixture in case["fixtures"]:
                    self.assertTrue(
                        fixture["source"].startswith(
                            "tests/speckit-pro/evals/fixtures/scenario-contracts/archive/no-candidates/"
                        ),
                        fixture,
                    )
                    self.assertTrue((REPO_ROOT / fixture["source"]).is_file(), fixture)
                continue
            if case["id"] in COACH_INSTALLED_IDS:
                for fixture in case["fixtures"]:
                    self.assertTrue(
                        fixture["source"].startswith(
                            "tests/speckit-pro/evals/fixtures/functional/speckit-coach/case-8/"
                        ),
                        fixture,
                    )
                    self.assertTrue((REPO_ROOT / fixture["source"]).is_file(), fixture)
                continue
            if case["id"] in COACH_ARCHIVE_IDS:
                for fixture in case["fixtures"]:
                    self.assertTrue(
                        fixture["source"].startswith(
                            "tests/speckit-pro/evals/fixtures/functional/speckit-coach/case-8/"
                        ) or fixture["source"].startswith(
                            "tests/speckit-pro/evals/fixtures/scenario-contracts/archive/no-candidates/"
                        ),
                        fixture,
                    )
                    self.assertTrue((REPO_ROOT / fixture["source"]).is_file(), fixture)
                continue
            if case["id"] in AUTOPILOT_PREREQ_IDS:
                for fixture in case["fixtures"]:
                    self.assertTrue(
                        fixture["source"].startswith(
                            "tests/speckit-pro/evals/fixtures/functional/autopilot-prerequisites/"
                        ) or fixture["source"].startswith(
                            "tests/speckit-pro/layer3-functional/fixtures/autopilot/SPEC-805/"
                        ),
                        fixture,
                    )
                    self.assertTrue((REPO_ROOT / fixture["source"]).is_file(), fixture)
                continue
            if case["id"] in STATUS_WORKTREE_IDS:
                for fixture in case["fixtures"]:
                    self.assertTrue(
                        fixture["source"].startswith(
                            "tests/speckit-pro/layer3-functional/fixtures/status/"
                        ),
                        fixture,
                    )
                    self.assertTrue((REPO_ROOT / fixture["source"]).is_file(), fixture)
                continue
            destinations = {fixture["destination"] for fixture in case["fixtures"]}
            for fixture in case["fixtures"]:
                self.assertTrue(fixture["source"].startswith("tests/speckit-pro/evals/fixtures/grounding/"))
                self.assertFalse(fixture["source"].startswith("specs/"))
                self.assertTrue((REPO_ROOT / fixture["source"]).is_file())
            reads = {
                check["path"] for check in case["checks"]
                if check["type"] == "file_access" and check["operation"] == "read_file"
            }
            self.assertEqual(reads, destinations, case["id"])
            grounding = [
                check for check in case["checks"]
                if check["type"] == "semantic" and check["requirement"] == "grounding"
            ]
            self.assertEqual(len(grounding), 1, case["id"])
            for sentinel in GROUNDING_SENTINELS[case["id"]]:
                self.assertIn(sentinel, grounding[0]["rubric"], (case["id"], sentinel))

        for frozen, legacy in FROZEN_GROUNDING_COPIES.items():
            self.assertEqual(
                (TEST_ROOT / frozen).read_bytes(),
                (TEST_ROOT / legacy).read_bytes(),
                frozen,
            )

    def test_grounded_additions_preserve_legacy_boundaries_and_read_profiles(self) -> None:
        for case_id, sources in GROUNDED_LEGACY_SOURCES.items():
            case = self.cases[case_id]
            legacy_rows = []
            expected_provenance = []
            for relative, eval_id in sources:
                source = TEST_ROOT / relative
                document = json.loads(source.read_text(encoding="utf-8"))
                legacy_rows.append(next(row for row in document["evals"] if row["id"] == eval_id))
                expected_provenance.append(f"tests/speckit-pro/{relative}#eval-{eval_id}")
            self.assertTrue(all(row == legacy_rows[0] for row in legacy_rows), case_id)
            legacy = legacy_rows[0]
            self.assertEqual(case["provenance"], expected_provenance, case_id)
            self.assertIn(
                "Use {{skill}} to address this bounded request. " + legacy["prompt"],
                case["prompt"],
                case_id,
            )
            behavior = next(row for row in case["requirements"] if row["id"] == "behavior")
            self.assertEqual(behavior["description"], legacy["expected_output"], case_id)
            rubric = next(check for check in case["checks"] if check["id"] == "legacy-behavior")["rubric"]
            for expectation in legacy["expectations"]:
                self.assertIn(expectation, rubric, (case_id, expectation))
            self.assertEqual(
                case["hosts"]["claude"]["allowed_tools"],
                ["Skill", "Read", "Glob", "Grep"],
            )
            self.assertEqual(
                case["hosts"]["codex"]["allowed_tools"],
                ["read_file", "list_files", "search_files"],
            )

    def test_scenario_additions_preserve_legacy_boundaries_and_observable_checks(self) -> None:
        _assert_scenario_legacy_boundaries(self, self.cases, self.selection)
        _assert_relocation_checks(self, self.cases)
        _assert_layer_plan_checks(self, self.cases)
        _assert_broken_archive_checks(self, self.cases)

    def test_repaired_contracts_are_explicit_and_obsolete_duplicates_are_merged(self) -> None:
        merged = {
            "functional.speckit-autopilot.case-17": {"legacy-07", "legacy-08"},
            "functional.speckit-autopilot.case-18": {"legacy-06"},
            "functional.speckit-autopilot.case-21": {"legacy-07"},
            "functional.speckit-autopilot.case-31": {"legacy-19"},
        }
        for case_id, retired in merged.items():
            case = self.cases[case_id]
            requirement_ids = {row["id"] for row in case["requirements"]}
            check_requirements = {row["requirement"] for row in case["checks"]}
            self.assertTrue(retired.isdisjoint(requirement_ids), case_id)
            self.assertTrue(retired.isdisjoint(check_requirements), case_id)

        security = self.cases["functional.speckit-autopilot.case-18"]
        security_text = " ".join(
            [security["capability"], security["prompt"]]
            + [row["description"] for row in security["requirements"]]
        ).casefold()
        self.assertIn("all three analysts", security_text)
        self.assertIn("security-keyword override", security_text)
        self.assertIn("human review", security_text)
        self.assertIn("does not single-route", security_text)

        for case_id in ("functional.speckit-autopilot.case-1", "functional.speckit-autopilot.case-107"):
            case = self.cases[case_id]
            self.assertEqual(case["required_tools"], ["specify"])
            self.assertIn("default-shell command", case["prompt"])
            self.assertIn("{{resolved_python}} -m speckit_pro_runner <", case["prompt"])

        for case_id in PLAN_REPAIR_IDS:
            prompt = self.cases[case_id]["prompt"]
            self.assertIn("exactly one top-level JSON object whose only key is attempts", prompt)

        grill = self.cases["functional.grill-me.case-7"]
        self.assertIn("spawn_agent", grill["hosts"]["codex"]["allowed_tools"])
        self.assertNotIn("subagent", grill["hosts"]["codex"]["allowed_tools"])

    def test_status_cases_scope_absence_and_stage_external_workflow_only(self) -> None:
        status3 = self.cases["functional.speckit-status.case-3"]
        status7 = self.cases["functional.speckit-status.case-7"]
        self.assertEqual(
            next(check for check in status3["checks"] if check["type"] == "file_search")["pattern"],
            "**/current-technical-roadmap.md",
        )
        self.assertEqual(
            {check["pattern"] for check in status7["checks"] if check["type"] == "file_search"},
            {"**/current-technical-roadmap.md", "**/SPEC-*-workflow.md"},
        )

        external = self.cases["functional.speckit-status.case-4"]
        self.assertEqual(
            external["git_fixture"]["feature_deletions"],
            ["docs/ai/specs/SPEC-021-workflow.md"],
        )
        self.assertEqual(external["git_fixture"]["worktrees"][0]["revision"], "baseline")
        checks = {check["id"]: check for check in external["checks"]}
        self.assertFalse(checks["root-workflow-absent"]["exists"])
        self.assertTrue(checks["attached-workflow-present"]["exists"])
        for field in ("active_spec", "source_path", "next_action"):
            self.assertIn(field, external["prompt"])
        for leaked_answer in ("SPEC-021", ".worktrees/spec-021", "continue_workflow"):
            self.assertNotIn(leaked_answer, external["prompt"])

    def test_catalog_rejects_unknown_host_tools_and_hidden_machine_contracts(self) -> None:
        unknown_tool = copy.deepcopy(self.loaded)
        target = next(
            case for case in unknown_tool["cases"]
            if case["id"] == "functional.grill-me.case-7"
        )
        target["hosts"]["codex"]["allowed_tools"][-1] = "subagent"
        with self.assertRaisesRegex(ValueError, "unknown names"):
            validate_catalog(unknown_tool, REPO_ROOT)

        hidden_field = copy.deepcopy(self.loaded)
        target = next(
            case for case in hidden_field["cases"]
            if case["id"] == "functional.speckit-status.case-4"
        )
        target["prompt"] = target["prompt"].replace("next_action", "next result")
        with self.assertRaisesRegex(ValueError, "omits response fields"):
            validate_catalog(hidden_field, REPO_ROOT)

        hidden_search = copy.deepcopy(self.loaded)
        target = next(
            case for case in hidden_search["cases"]
            if case["id"] == "functional.speckit-status.case-7"
        )
        target["prompt"] = target["prompt"].replace("**/SPEC-*-workflow.md", "workflow search")
        with self.assertRaisesRegex(ValueError, "omits file search patterns"):
            validate_catalog(hidden_search, REPO_ROOT)

    def test_registered_worktree_ambiguity_case_matches_accepted_factory_and_legacy(self) -> None:
        case_id = "functional.speckit-autopilot.case-107"
        source = TEST_ROOT / "unit" / "test-native-worktree-migration.py"
        spec = importlib.util.spec_from_file_location("native_worktree_migration_contract", source)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(self.cases[case_id], module.ambiguity_case())

        record = next(row for row in self.selection["selected"] if row["case_id"] == case_id)
        self.assertEqual(record["legacy_ids"], ["codex:speckit-autopilot:107"])
        self.assertEqual(len(record["sources"]), 1)
        boundary = record["sources"][0]
        original = json.loads((REPO_ROOT / boundary["source"]).read_text(encoding="utf-8"))
        legacy = next(row for row in original["evals"] if row["id"] == 107)
        self.assertEqual(boundary["legacy_expectations"], legacy["expectations"])
        self.assertEqual(
            [row["expectation_index"] for row in boundary["expectations"]],
            list(range(len(legacy["expectations"]))),
        )
        executable = {check["requirement"] for check in self.cases[case_id]["checks"]}
        for mapping in boundary["expectations"]:
            self.assertTrue(mapping["requirement_ids"])
            self.assertLessEqual(set(mapping["requirement_ids"]), executable)
        self.assertEqual({row["host"] for row in record["sources"]}, {"codex"})
        self.assertIn("parity addition", " ".join(self.cases[case_id]["native_differences"]))

    def test_subject_fixtures_do_not_explain_the_expected_missing_or_branch_outcomes(self) -> None:
        roadmap = (
            TEST_ROOT / "evals/fixtures/scaffold-contracts/missing/roadmap.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("SPEC-030", roadmap)
        self.assertNotIn("SPEC-031", roadmap)
        self.assertNotIn("intentionally has no", roadmap)

        case = self.cases["functional.speckit-autopilot.case-30"]
        fixture_text = "\n".join(
            (REPO_ROOT / fixture["source"]).read_text(encoding="utf-8")
            for fixture in case["fixtures"]
        )
        self.assertNotIn("helper_invoked", fixture_text)
        self.assertNotIn("invalid_plan_stop", fixture_text)
        self.assertNotIn("layer_plan.status=skipped", fixture_text)

    def test_plan_repair_cases_bind_native_context_and_real_g3_fixtures(self) -> None:
        expected_contexts = {
            "functional.speckit-autopilot.case-111": {
                "clarify-results": "scenario-inputs/clarify-results.md",
                "original-plan-prompt": "scenario-inputs/original-plan-prompt.md",
            },
            "functional.speckit-autopilot.case-112": {
                "architecture": "scenario-inputs/architecture.md",
                "clarify-results": "scenario-inputs/clarify-results.md",
                "original-plan-prompt": "scenario-inputs/original-plan-prompt.md",
            },
        }
        project = TEST_ROOT / "evals/fixtures/functional/autopilot-scenarios/common/project.json"
        for case_id, contexts in expected_contexts.items():
            case = self.cases[case_id]
            native_checks = [
                check for check in case["checks"]
                if check["type"] == "native_plan_repair_context"
            ]
            self.assertEqual(len(native_checks), 1, case_id)
            check = native_checks[0]
            self.assertEqual(check["contexts"], contexts, case_id)
            self.assertEqual(check["executor_role"], "phase-executor", case_id)
            self.assertEqual(check["max_repairs"], 2, case_id)
            self.assertEqual(
                check["terminal_outcome"],
                "pass" if case_id.endswith("111") else "unresolved",
                case_id,
            )
            fixtures = {row["destination"]: REPO_ROOT / row["source"] for row in case["fixtures"]}
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / ".specify").mkdir()
                shutil.copyfile(project, root / ".specify/project.json")
                feature = root / "scenario-inputs/feature"
                feature.mkdir(parents=True)
                shutil.copyfile(fixtures["scenario-inputs/feature/plan.md"], feature / "plan.md")
                env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "speckit-pro")}
                result = subprocess.run(
                    [sys.executable, "-m", "speckit_pro_runner"],
                    input=fixtures[check["g3_request_path"]].read_text(encoding="utf-8"),
                    text=True,
                    capture_output=True,
                    cwd=root,
                    env=env,
                    check=False,
                )
                self.assertEqual(result.returncode, 1, (case_id, result.stderr))
                envelope = json.loads(result.stdout)
                self.assertEqual(envelope["status"], "expected_failure", case_id)
                self.assertFalse(envelope["data"]["writes_state"], case_id)
                self.assertEqual(
                    envelope["data"]["stdout_json"],
                    {
                        "gate": "G3", "pass": False,
                        "reason": "1 unresolved markers (NC:1, TODO:0)",
                        "markers": 1, "details": [],
                    },
                    case_id,
                )

    def test_local_command_cases_preserve_provenance_and_exact_observations(self) -> None:
        for case_id, sources in LOCAL_COMMAND_LEGACY_SOURCES.items():
            case = self.cases[case_id]
            self.assertEqual(
                case["provenance"],
                [f"tests/speckit-pro/{source}#eval-id={eval_id}" for source, eval_id in sources],
                case_id,
            )

        g7 = self.cases["functional.speckit-autopilot.case-2"]
        self.assertEqual(
            g7["fixtures"],
            [
                {
                    "source": "tests/speckit-pro/evals/fixtures/functional/local-command/validate-g7-request.json",
                    "destination": "scenario-inputs/validate-g7-request.json",
                },
                {
                    "source": "tests/speckit-pro/evals/fixtures/functional/local-command/baseline.md",
                    "destination": "scenario-inputs/read-only-helper-feature/tasks.md",
                },
            ],
        )
        self.assertIn("Bash prerequisite", " ".join(g7["native_differences"]))
        self.assertEqual(g7["hosts"]["claude"]["allowed_tools"], ["Skill", "Read", "Bash", "Write"])

        request = json.loads(
            (TEST_ROOT / "evals/fixtures/functional/local-command/validate-g7-request.json").read_text()
        )
        task_text = (
            TEST_ROOT / "evals/fixtures/functional/local-command/baseline.md"
        ).read_text(encoding="utf-8")
        envelope = {
            "data": {
                "stdin_request": request,
                "writes_state": False,
                "exit_code": 1,
                "stdout_json": {
                    "gate": "G7", "pass": False, "reason": "1 of 85 tasks incomplete",
                    "markers": 1, "total": 85, "done": 84,
                },
            }
        }
        correct = observation(
            activation="speckit-autopilot",
            artifacts={
                "scenario-inputs/read-only-helper-feature/tasks.md": task_text,
                "scenario-output/validate-g7-envelope.json": json.dumps(envelope),
            },
        )
        self.assertEqual(grade_observation(g7, correct, semantic_verdicts(g7, True))["status"], "pass")

        changed_task = copy.deepcopy(correct)
        changed_task["artifacts"]["scenario-inputs/read-only-helper-feature/tasks.md"] = (
            task_text.replace("T001 Complete", "T001 Changed", 1)
        )
        self.assertEqual(
            grade_observation(g7, changed_task, semantic_verdicts(g7, True))["status"],
            "fail",
        )
        wrong_done = copy.deepcopy(correct)
        wrong_envelope = copy.deepcopy(envelope)
        wrong_envelope["data"]["stdout_json"]["done"] = 85
        wrong_done["artifacts"]["scenario-output/validate-g7-envelope.json"] = json.dumps(wrong_envelope)
        self.assertEqual(
            grade_observation(g7, wrong_done, semantic_verdicts(g7, True))["status"],
            "fail",
        )

        lint = self.cases["functional.ubiquitous-language.case-3"]
        unmapped_checks = [check for check in lint["checks"] if check["id"].startswith("unmapped-")]
        self.assertEqual(
            [(check["id"], check["field_path"]) for check in unmapped_checks if check["type"] == "json_field"],
            [("unmapped-complete-set", ["unmapped"]), ("unmapped-summary", ["note"])],
        )
        report = {
            "advisory": True,
            "declared": 2,
            "terms": 2,
            "unmapped": [{"file": "src/billing.py", "identifier": "reindex_all", "line": 6}],
            "note": "1 of 2 declared identifiers map to no term",
        }
        lint_observation = observation(
            activation="ubiquitous-language",
            artifacts={"scenario-output/ubiquitous-language-lint.json": json.dumps(report)},
        )
        self.assertEqual(
            grade_observation(lint, lint_observation, semantic_verdicts(lint, True))["status"],
            "pass",
        )
        for bad_unmapped in (
            report["unmapped"] + [{"file": "src/extra.py", "identifier": "extra", "line": 1}],
            [{"file": "src/billing.py", "identifier": "rebuild_all", "line": 6}],
            [{"file": "src/billing.py", "identifier": "reindex_all", "line": "6"}],
        ):
            bad_report = copy.deepcopy(report)
            bad_report["unmapped"] = bad_unmapped
            bad = copy.deepcopy(lint_observation)
            bad["artifacts"]["scenario-output/ubiquitous-language-lint.json"] = json.dumps(bad_report)
            self.assertEqual(
                grade_observation(lint, bad, semantic_verdicts(lint, True))["status"],
                "fail",
            )

        two_item = copy.deepcopy(lint)
        complete_set = next(check for check in two_item["checks"] if check["id"] == "unmapped-complete-set")
        second = {"file": "src/extra.py", "identifier": "extra", "line": 1}
        complete_set["expected"] = [*report["unmapped"], second]
        reordered_report = copy.deepcopy(report)
        reordered_report["unmapped"] = [second, *report["unmapped"]]
        reordered = copy.deepcopy(lint_observation)
        reordered["artifacts"]["scenario-output/ubiquitous-language-lint.json"] = json.dumps(reordered_report)
        self.assertEqual(
            grade_observation(two_item, reordered, semantic_verdicts(two_item, True))["status"],
            "fail",
        )

    def test_local_command_neutral_fixtures_execute_against_shipped_helpers(self) -> None:
        task_fixture = TEST_ROOT / "evals/fixtures/functional/local-command/baseline.md"
        request_fixture = TEST_ROOT / "evals/fixtures/functional/local-command/validate-g7-request.json"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".specify").mkdir()
            shutil.copyfile(
                TEST_ROOT / "evals/fixtures/functional/local-command/project.json",
                root / ".specify/project.json",
            )
            feature = root / "scenario-inputs/read-only-helper-feature"
            feature.mkdir(parents=True)
            shutil.copyfile(task_fixture, feature / "tasks.md")
            before = (feature / "tasks.md").read_bytes()
            env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "speckit-pro")}
            result = subprocess.run(
                [sys.executable, "-m", "speckit_pro_runner"],
                input=request_fixture.read_text(encoding="utf-8"),
                text=True,
                capture_output=True,
                cwd=root,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            envelope = json.loads(result.stdout)
            self.assertEqual(envelope["data"]["exit_code"], 1)
            self.assertFalse(envelope["data"]["writes_state"])
            self.assertEqual(
                envelope["data"]["stdout_json"],
                {
                    "gate": "G7", "pass": False, "reason": "1 of 85 tasks incomplete",
                    "markers": 1, "total": 85, "done": 84,
                },
            )
            self.assertEqual((feature / "tasks.md").read_bytes(), before)

        lint_script = REPO_ROOT / "speckit-pro/scripts/ubiquitous-language-lint.py"
        lint_fixture = TEST_ROOT / "evals/fixtures/functional/ubiquitous-language-lint"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "docs/ai/specs").mkdir(parents=True)
            shutil.copyfile(lint_fixture / "baseline.py", root / "src/billing.py")
            shutil.copyfile(lint_fixture / "terms.md", root / "docs/ai/specs/ubiquitous-language.md")

            def git(*args: str) -> None:
                subprocess.run(
                    ["git", "-C", str(root), *args],
                    capture_output=True,
                    text=True,
                    check=True,
                )

            git("init", "-b", "main")
            git("add", ".")
            git("-c", "commit.gpgsign=false", "-c", "user.name=Fixture", "-c", "user.email=native-eval@example.invalid", "commit", "-m", "baseline")
            git("update-ref", "refs/remotes/origin/main", "HEAD")
            shutil.copyfile(lint_fixture / "feature.py", root / "src/billing.py")
            git("add", "src/billing.py")
            git("-c", "commit.gpgsign=false", "-c", "user.name=Fixture", "-c", "user.email=native-eval@example.invalid", "commit", "-m", "feature")
            report_path = root / "scenario-output/ubiquitous-language-lint.json"
            report_path.parent.mkdir()
            result = subprocess.run(
                [
                    sys.executable, str(lint_script), "--base", "origin/main",
                    "--report", str(report_path),
                ],
                capture_output=True,
                text=True,
                cwd=root,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["declared"], 2)
            self.assertEqual(report["terms"], 2)
            self.assertEqual(
                report["unmapped"],
                [{"file": "src/billing.py", "identifier": "reindex_all", "line": 6}],
            )
            self.assertTrue(report["advisory"])

    def test_grounded_reads_are_status_sensitive_for_both_native_shapes(self) -> None:
        for case_id in GROUNDED_IDS:
            case = self.cases[case_id]
            verdicts = semantic_verdicts(case, True)
            for host in ("claude", "codex"):
                complete = grounded_observation(case, host)
                self.assertEqual(grade_observation(case, complete, verdicts)["status"], "pass")

                missing = copy.deepcopy(complete)
                missing["tool_calls"].pop()
                self.assertEqual(grade_observation(case, missing, verdicts)["status"], "fail")

                failed = copy.deepcopy(complete)
                failed["tool_calls"][0]["success"] = False
                self.assertEqual(grade_observation(case, failed, verdicts)["status"], "fail")

                wrong = copy.deepcopy(complete)
                if host == "claude":
                    wrong["tool_calls"][0]["input"]["file_path"] = "unrelated.md"
                else:
                    wrong["tool_calls"][0]["input"]["command"] = "cat -- unrelated.md"
                self.assertEqual(grade_observation(case, wrong, verdicts)["status"], "fail")

    def test_grounded_semantic_mocks_prove_plumbing_not_judge_sensitivity(self) -> None:
        for case_id in GROUNDED_IDS:
            case = self.cases[case_id]
            generic = grounded_observation(
                case, "claude", final_text="I read the files and everything looks good."
            )
            self.assertEqual(grade_observation(case, generic)["status"], "needs_judge")
            self.assertEqual(
                grade_observation(case, generic, semantic_verdicts(case, True))["status"],
                "pass",
            )
            self.assertEqual(
                grade_observation(case, generic, semantic_verdicts(case, False))["status"],
                "fail",
            )

        examples = self.examples["grounded_semantic_examples"]
        self.assertEqual(len(examples), 1)
        example = examples[0]
        self.assertEqual(example["case_id"], "functional.speckit-coach.case-2")
        self.assertEqual(example["check_id"], "fixture-grounding")
        self.assertIn("POST /deliveries", example["accepted_concise"])
        self.assertIn("five-attempt", example["accepted_concise"])
        self.assertIn("HMAC-SHA256", example["accepted_concise"])
        self.assertNotIn("202", example["generic_wrong"])
        self.assertIn("always returns 200", example["contradictory_wrong"])
        self.assertIn("plumbing only", example["evidence_note"])

        case = self.cases[example["case_id"]]
        for text in (
            example["accepted_concise"],
            example["generic_wrong"],
            example["contradictory_wrong"],
        ):
            candidate = grounded_observation(case, "claude", final_text=text)
            self.assertEqual(grade_observation(case, candidate)["status"], "needs_judge")
        accepted = grounded_observation(case, "claude", final_text=example["accepted_concise"])
        contradictory = grounded_observation(
            case, "claude", final_text=example["contradictory_wrong"]
        )
        self.assertEqual(
            grade_observation(case, accepted, semantic_verdicts(case, False))["status"],
            "fail",
        )
        self.assertEqual(
            grade_observation(case, contradictory, semantic_verdicts(case, True))["status"],
            "pass",
        )

    def test_each_deterministic_check_rejects_a_negative_observation(self) -> None:
        for case in self.catalog["cases"]:
            activation = case["checks"][0]["expected"][0]
            for check in case["checks"]:
                expected_status = "fail"
                if check["type"] == "semantic":
                    verdicts = {check["id"]: {"passed": False, "evidence": ["negative-fixture"]}}
                    result = grade_observation(
                        one_check_case(case, check), observation(activation=activation), verdicts
                    )
                elif check["type"] == "selection":
                    result = grade_observation(
                        one_check_case(case, check), observation(activation="wrong-capability")
                    )
                elif check["type"] == "text":
                    result = grade_observation(
                        one_check_case(case, check), observation(activation=activation, final_text="")
                    )
                elif check["type"] == "tool_used":
                    calls = []
                    if check.get("max") == 0:
                        calls = [{
                            "name": check["name"],
                            "input": {"command": "relocate-process-artifacts.sh dry_run apply"},
                            "output": "unexpected invocation",
                            "success": True,
                        }]
                    result = grade_observation(
                        one_check_case(case, check),
                        observation(activation=activation, tool_calls=calls),
                    )
                elif check["type"] == "file_access":
                    result = grade_observation(
                        one_check_case(case, check), observation(activation=activation, tool_calls=[])
                    )
                elif check["type"] == "file_exists":
                    artifacts = {} if check["exists"] else {check["path"]: "unexpected"}
                    result = grade_observation(
                        one_check_case(case, check),
                        observation(activation=activation, artifacts=artifacts),
                    )
                elif check["type"] == "response_json_field":
                    for host in ("claude", "codex"):
                        result = grade_observation(
                            one_check_case(case, check),
                            observation(activation=activation, final_text="{}"), host=host,
                        )
                        self.assertEqual(result["status"], "fail", (case["id"], check["id"], host))
                elif check["type"] == "json_field":
                    result = grade_observation(
                        one_check_case(case, check),
                        observation(activation=activation, artifacts={check["path"]: "{}"}),
                    )
                elif check["type"] == "file_search":
                    result = grade_observation(
                        one_check_case(case, check), observation(activation=activation),
                        host="codex",
                    )
                elif check["type"] == "native_subagent_dispatch":
                    result = grade_observation(
                        one_check_case(case, check), observation(activation=activation),
                        host="codex",
                    )
                    expected_status = "invalid"
                elif check["type"] == "native_plan_repair_context":
                    negative = observation(activation=activation)
                    negative["native_metadata"] = {
                        "native_plan_repair_context": {
                            "schema": "native-plan-repair-context/v1",
                            "authority": "controller-bound-retained-native-evidence",
                            "checks": [{
                                "check_id": check["id"], "commands": [], "dispatches": [],
                            }],
                        },
                        "subagent_return_order": {
                            "schema": "native-subagent-return-order/v1",
                            "scope": "direct-root-only",
                            "returns": [],
                            "parent_file_changes": [],
                        },
                        "nested_rollout": {"dispatches": []},
                    }
                    result = grade_observation(
                        one_check_case(case, check), negative, host="codex",
                    )
                elif check["type"] == "file_search":
                    result = grade_observation(
                        one_check_case(case, check), observation(activation=activation),
                        host="codex",
                    )
                elif check["type"] == "native_subagent_dispatch":
                    result = grade_observation(
                        one_check_case(case, check), observation(activation=activation),
                        host="codex",
                    )
                    expected_status = "invalid"
                elif check["type"] == "file_search":
                    result = grade_observation(
                        one_check_case(case, check), observation(activation=activation),
                        host="codex",
                    )
                elif check["type"] == "native_subagent_dispatch":
                    result = grade_observation(
                        one_check_case(case, check), observation(activation=activation),
                        host="codex",
                    )
                    expected_status = "invalid"
                elif check["type"] in {"native_git_final_state", "native_runner_result"}:
                    result = grade_observation(
                        one_check_case(case, check), observation(activation=activation),
                    )
                    expected_status = "invalid"
                else:
                    self.fail(f"unreviewed check type {check['type']} in {case['id']}")
                self.assertEqual(
                    result["status"], expected_status, (case["id"], check["id"], result)
                )

    def test_missing_roadmap_scaffold_case_requires_absence_and_shared_semantics(self) -> None:
        case = self.cases["functional.speckit-scaffold-spec.case-3"]
        self.assertEqual(case["required_tools"], ["specify"])
        self.assertEqual(
            case["prompt"],
            "Use {{skill}} to set up SPEC-031 from docs/ai/current-technical-roadmap.md.",
        )
        self.assertNotIn("PASS only if", case["prompt"])
        self.assertNotIn("workflow", (REPO_ROOT / case["fixtures"][0]["source"]).read_text())
        verdicts = semantic_verdicts(case, True)
        correct = observation(activation="speckit-scaffold-spec")
        self.assertEqual(grade_observation(case, correct, verdicts)["status"], "pass")
        invented = observation(
            activation="speckit-scaffold-spec",
            artifacts={"docs/ai/specs/.process/SPEC-031-workflow.md": "invented workflow"},
        )
        self.assertEqual(grade_observation(case, invented, verdicts)["status"], "fail")
        wrong_skill = observation(activation="speckit-coach")
        self.assertEqual(grade_observation(case, wrong_skill, verdicts)["status"], "fail")

    def test_semantic_checks_are_narrow_and_not_action_claim_substitutes(self) -> None:
        for case in self.catalog["cases"]:
            if case["id"] in GROUNDED_IDS | SCENARIO_IDS | LOCAL_COMMAND_IDS | REDIRECT_IDS | DASHBOARD_IDS | WORKTREE_MIGRATION_IDS | SCAFFOLD_DIAGNOSTIC_IDS | STATUS_SEARCH_IDS | CHILD_ABORT_IDS | WORKTREE_BINDING_IDS | ARCHIVE_EXTENSION_IDS | COACH_INSTALLED_IDS | COACH_ARCHIVE_IDS | AUTOPILOT_PREREQ_IDS | STATUS_WORKTREE_IDS | SCAFFOLD_HANDOFF_IDS:
                continue
            requirement_ids = {row["id"] for row in case["requirements"]}
            for check in case["checks"]:
                if check["type"] != "semantic":
                    continue
                self.assertIn(check["requirement"], requirement_ids)
                expected = EXPECTED_SEMANTIC_OVERLAYS.get(
                    (case["id"], check["id"]),
                    f"PASS only if the evidence satisfies: {next(row['description'] for row in case['requirements'] if row['id'] == check['requirement'])} FAIL if omitted, contradicted, or merely claimed without required evidence.",
                )
                self.assertEqual(check["rubric"], expected)
                self.assertNotIn("all applicable requirements", check["rubric"])

    def test_only_audited_literal_or_format_requirements_use_text_checks(self) -> None:
        declared = {(row["case_id"], row["check_id"]): row for row in self.examples["literal_checks"]}
        actual = {
            (case["id"], check["id"]): (case, check)
            for case in self.catalog["cases"]
            for check in case["checks"]
            if check["type"] == "text"
            and case["id"] not in SCENARIO_IDS | LOCAL_COMMAND_IDS | REDIRECT_IDS
        }
        self.assertEqual(set(actual), set(declared))
        for key, (case, check) in actual.items():
            result = grade_observation(
                one_check_case(case, check),
                observation(
                    activation=case["checks"][0]["expected"][0],
                    final_text=declared[key]["passing"],
                ),
            )
            self.assertEqual(result["status"], "pass", (key, result))

    def test_confidence_format_accepts_any_nonempty_value_without_a_hidden_enum(self) -> None:
        for case_id in (
            "functional.speckit-autopilot.case-103",
            "functional.speckit-coach.case-103",
        ):
            case = self.cases[case_id]
            check = next(item for item in case["checks"] if item["id"] == "legacy-01-text")
            self.assertNotIn("high|medium|low", check["pattern"])
            result = grade_observation(
                one_check_case(case, check),
                observation(
                    activation=case["checks"][0]["expected"][0],
                    final_text="Capability path: need -> selected source; Evidence: local ref; Confidence: 0.8",
                ),
            )
            self.assertEqual(result["status"], "pass", (case_id, result))

    def test_same_keywords_do_not_bypass_ordered_format_checks(self) -> None:
        for row in self.examples["same_keyword_format_negatives"]:
            case = self.cases[row["case_id"]]
            check = next(item for item in case["checks"] if item["id"] == row["check_id"])
            result = grade_observation(
                one_check_case(case, check),
                observation(
                    activation=case["checks"][0]["expected"][0],
                    final_text=row["wrong"],
                ),
            )
            self.assertEqual(result["status"], "fail", (row["case_id"], result))

    def test_keyword_stuffed_contradictions_fail_and_correct_paraphrases_pass(self) -> None:
        """Injected semantic verdicts prove grader wiring, not live-judge sensitivity."""
        for row in self.examples["case_examples"]:
            case = self.cases[row["case_id"]]
            activation = case["checks"][0]["expected"][0]
            semantic_ids = [check["id"] for check in case["checks"] if check["type"] == "semantic"]
            passing_verdicts = {
                check_id: {"passed": True, "evidence": ["correct-paraphrase"]}
                for check_id in semantic_ids
            }
            failing_verdicts = {
                check_id: {"passed": False, "evidence": ["keyword-stuffed-contradiction"]}
                for check_id in semantic_ids
            }
            passed = grade_observation(
                case,
                observation(activation=activation, final_text=row["correct_paraphrase"]),
                passing_verdicts,
            )
            failed = grade_observation(
                case,
                observation(activation=activation, final_text=row["keyword_stuffed_wrong"]),
                failing_verdicts,
            )
            self.assertEqual(passed["status"], "pass", (row["case_id"], passed))
            self.assertEqual(failed["status"], "fail", (row["case_id"], failed))

    def test_literal_tokens_cannot_bypass_their_semantic_relationship(self) -> None:
        """Mock verdicts prove the overlay is enforced; they do not qualify a judge."""
        for row in self.examples["literal_plus_semantic_examples"]:
            source_case = self.cases[row["case_id"]]
            checks = [
                check for check in source_case["checks"]
                if check["requirement"] == row["requirement_id"]
            ]
            requirement = next(
                item for item in source_case["requirements"]
                if item["id"] == row["requirement_id"]
            )
            case = {"requirements": [requirement], "checks": checks}
            semantic_id = next(check["id"] for check in checks if check["type"] == "semantic")
            text_check = next(check for check in checks if check["type"] == "text")
            activation = source_case["checks"][0]["expected"][0]
            literal_only = grade_observation(
                one_check_case(source_case, text_check),
                observation(activation=activation, final_text=row["keyword_stuffed_wrong"]),
            )
            passed = grade_observation(
                case,
                observation(activation=activation, final_text=row["correct_paraphrase"]),
                {semantic_id: {"passed": True, "evidence": ["correct-relationship"]}},
            )
            failed = grade_observation(
                case,
                observation(activation=activation, final_text=row["keyword_stuffed_wrong"]),
                {semantic_id: {"passed": False, "evidence": ["negated-relationship"]}},
            )
            self.assertEqual(literal_only["status"], "pass", (row["case_id"], literal_only))
            self.assertEqual(passed["status"], "pass", (row["case_id"], passed))
            self.assertEqual(failed["status"], "fail", (row["case_id"], failed))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeFunctionalCatalogTests)
    raise SystemExit(run_counted(suite, label="test-native-functional-catalog"))
