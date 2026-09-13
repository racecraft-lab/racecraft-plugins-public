#!/usr/bin/env python3
"""Verify frozen benchmark provenance without running providers or archived specs."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests/speckit-pro/layer7-integration/performance-fixtures"
sys.path.insert(0, str(ROOT / "tests/speckit-pro/lib"))
from test_result import run_counted

EXPECTED = {
    "ART-012": (14, "ba22a0938b37743029142b8763b23be693193966", "3a0e49b6c6b49c855e23c4663ae407b7f34fd8a7"),
    "ART-007": (54, "2c4edf01b6f84068bd311de81212fc3d4f2384b9", "d30876bb498a009b24a26df9f2371505722b45ef"),
    "DOC-008": (40, "6d4c194015382182284b76402e33d9164c88b7d6", "5dcb604aed3cd1a850fdfd5881e7515943e191f8"),
}
TASK = re.compile(r"^- \[([ xX])\] (T\d{3,})\b", re.MULTILINE)


class PerformanceFixtureTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((FIXTURES / "manifest.json").read_text())

    def test_scenarios_and_historical_pins_are_exact(self):
        self.assertEqual(self.manifest["schema_version"], "autopilot-performance-fixtures/v1")
        scenarios = self.manifest["scenarios"]
        self.assertEqual([s["id"] for s in scenarios], list(EXPECTED))
        for scenario in scenarios:
            count, workload, planning = EXPECTED[scenario["id"]]
            self.assertEqual((scenario["reference_task_count"], scenario["workload"]["commit"], scenario["planning_commit"]), (count, workload, planning))
            self.assertRegex(scenario["workload"]["tree"], r"^[0-9a-f]{40}$")

    def test_source_bytes_match_sha256_and_original_git_blobs(self):
        for scenario in self.manifest["scenarios"]:
            for source in scenario["sources"]:
                with self.subTest(source=source["file"]):
                    path = (FIXTURES / source["file"]).resolve()
                    self.assertTrue(path.is_relative_to(FIXTURES.resolve()))
                    self.assertFalse((FIXTURES / source["file"]).is_symlink())
                    content = path.read_bytes()
                    self.assertEqual(len(content), source["bytes"])
                    self.assertEqual(hashlib.sha256(content).hexdigest(), source["sha256"])
                    blob = b"blob " + str(len(content)).encode() + b"\0" + content
                    self.assertEqual(hashlib.sha1(blob).hexdigest(), source["git_blob"])
                    self.assertIn(source["commit"], (scenario["workload"]["commit"], scenario["planning_commit"]))
                    self.assertNotIn(".process/implementation-notes.md", source["original_path"])

    def test_reference_tasks_are_complete_and_reset_only_completion(self):
        for scenario in self.manifest["scenarios"]:
            original = (FIXTURES / scenario["reference_tasks"]).read_text()
            prepared = (FIXTURES / scenario["prepared_tasks"]["file"]).read_text()
            expected = re.sub(r"(?m)^(- \[)[xX](\] T\d{3,}\b)", r"\1 \2", original)
            self.assertEqual(prepared, expected)
            ids = [match[1] for match in TASK.findall(original)]
            self.assertEqual(ids, scenario["reference_task_ids"])
            self.assertEqual(len(ids), scenario["reference_task_count"])
            self.assertEqual(len(ids), len(set(ids)))
            reset = [task for marker, task in TASK.findall(original) if marker != " "]
            self.assertEqual(reset, scenario["prepared_tasks"]["reset_task_ids"])
            self.assertEqual([marker for marker, _ in TASK.findall(prepared)], [" "] * len(ids))
            automatic = set(scenario["automated_reference_task_ids"])
            operator = set(scenario["operator_only_reference_task_ids"])
            self.assertFalse(automatic & operator)
            self.assertEqual(automatic | operator, set(ids))

    def test_amended_scope_and_operator_exclusion_are_explicit(self):
        notes, draft, docs = self.manifest["scenarios"]
        self.assertIn("T014", notes["reference_task_ids"])
        kickoff = (FIXTURES / notes["kickoff"]).read_text()
        for token in ("FR-006", "T014", "190", "six", "per-attempt"):
            self.assertIn(token, kickoff)
        self.assertEqual(draft["operator_only_reference_task_ids"], ["T052"])
        tasks = (FIXTURES / draft["reference_tasks"]).read_text()
        self.assertRegex(tasks, r"T052 \*\*Operator-gated\*\*")
        self.assertEqual(notes["operator_only_reference_task_ids"], [])
        self.assertEqual(docs["operator_only_reference_task_ids"], [])

    def test_native_qualification_fails_closed(self):
        qualification = self.manifest["qualification"]
        self.assertEqual(qualification["status"], "pending-native-qualification")
        self.assertIs(qualification["launch_authorized"], False)
        self.assertIs(qualification["prerequisites_verified"], False)
        self.assertEqual(qualification["native_workflow_runs_completed"], 0)
        for field in ("candidate_harness_commit", "model_cli_pins", "provider_launch_budget", "dependency_qualification", "metadata_input_qualification"):
            self.assertIsNone(qualification[field])
        self.assertEqual(qualification["baseline_harness_commit"], "42f4afe5bd2a319f81ea4b28799ec13bfa8e6107")
        self.assertEqual(qualification["native_workflow_runs_planned"], 12)

    def test_workflow_is_unmodified_and_all_main_phases_pending(self):
        for scenario in self.manifest["scenarios"]:
            workflow = (FIXTURES / scenario["workflow"]).read_text()
            for phase in ("Specify", "Clarify", "Plan", "Checklist", "Tasks", "Analyze", "Implement"):
                self.assertRegex(workflow, rf"(?m)^\| {phase} \|[^\n]*Pending[^\n]*\|$")
            source = next(item for item in scenario["sources"] if item["file"] == scenario["workflow"])
            self.assertEqual(source["commit"], scenario["workload"]["commit"])

    def test_protocol_requires_real_generation_and_honest_timing(self):
        protocol = (FIXTURES / "PROTOCOL.md").read_text()
        for token in ("actual Tasks", "never seed", "monotonic", "7200", "0.5", "900", "12", "T052", "launch budget", "not full qualification", "external approval", "token usage", "incomplete baseline"):
            self.assertIn(token, protocol)
        for file in self.manifest["authored_files"]:
            content = (FIXTURES / file["file"]).read_bytes()
            self.assertEqual(hashlib.sha256(content).hexdigest(), file["sha256"])


class PreparationInputTests(unittest.TestCase):
    def test_common_tasks_input_is_identical_and_does_not_seed_outputs(self):
        manifest = json.loads((FIXTURES / "manifest.json").read_text())
        preparation = manifest["preparation"]
        self.assertEqual(preparation["status"], "prepared-inputs-not-native-qualified")
        self.assertEqual(preparation["common_tasks_input"], "COMMON-TASKS-INPUT.md")
        authored = {entry["file"] for entry in manifest["authored_files"]}
        self.assertTrue({preparation["common_tasks_input"], preparation["dependency_inventory"]} <= authored)
        supplement = (FIXTURES / preparation["common_tasks_input"]).read_text()
        for token in ("actual Tasks phase", "never seed", "schema_version", "task-execution.v1", "fingerprints", "spec_sha256", "plan_sha256", "tasks_sha256", "capability_group", "depends_on", "owns", "tdd_unit", "candidate-only helper", "task_execution_required=true"):
            self.assertIn(token, supplement)
        for scenario in manifest["scenarios"]:
            kickoff = (FIXTURES / scenario["kickoff"]).read_text()
            self.assertIn("Apply the identical `../COMMON-TASKS-INPUT.md` supplement to the actual Tasks", kickoff)
        self.assertFalse(list(FIXTURES.rglob("task-execution.json")))

    def test_dependency_inventory_binds_each_historical_workload(self):
        manifest = json.loads((FIXTURES / "manifest.json").read_text())
        inventory = json.loads((FIXTURES / manifest["preparation"]["dependency_inventory"]).read_text())
        self.assertEqual(inventory["status"], "source-pins-only-not-environment-qualified")
        self.assertEqual(set(inventory["scenarios"]), set(EXPECTED))
        for scenario in manifest["scenarios"]:
            entry = inventory["scenarios"][scenario["id"]]
            self.assertEqual(entry["workload_commit"], scenario["workload"]["commit"])
            self.assertEqual(entry["package_manager_declaration"], "pnpm@10.25.0")
            self.assertEqual(entry["astro_node_engine_declaration"], ">=22.12.0")
            self.assertEqual(set(entry["files"]), {"docs-site/package.json", "docs-site/pnpm-lock.yaml"})
            for pin in entry["files"].values():
                self.assertRegex(pin["git_blob"], r"^[0-9a-f]{40}$")
                self.assertRegex(pin["sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(pin["bytes"], 0)
            for pending in ("resolved_runtime_pins", "installation_evidence", "automated_check_evidence"):
                self.assertIsNone(entry[pending])
        self.assertEqual(inventory["scenarios"]["ART-012"]["files"], inventory["scenarios"]["ART-007"]["files"])
        self.assertEqual(inventory["scenarios"]["DOC-008"]["files"]["docs-site/pnpm-lock.yaml"]["git_blob"], "257094f1d5d637695663b8d275393dd777b9752b")

    def test_preflight_separates_source_pins_from_native_evidence(self):
        protocol = " ".join((FIXTURES / "PROTOCOL.md").read_text().split())
        for token in ("DEPENDENCY-PINS.json", "COMMON-TASKS-INPUT.md", "package-manager declaration", "not an environment qualification", "both arms", "prepared-workflow hash", "no candidate-only helper"):
            self.assertIn(token, protocol)


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in (PerformanceFixtureTests, PreparationInputTests))
    raise SystemExit(run_counted(suite, label="test-performance-fixtures"))
