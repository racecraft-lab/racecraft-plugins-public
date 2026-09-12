#!/usr/bin/env python3
"""Synthetic native events qualify the journal contract, not native TDD itself."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))
sys.path.insert(0, str(REPO_ROOT / "tests/speckit-pro/lib"))
from test_result import run_counted
from speckit_pro_runner.task_execution import fingerprints
from speckit_pro_runner.task_results import task_results


class BatchedTaskResultsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.feature = self.root / "feature"
        (self.feature / ".process").mkdir(parents=True)
        (self.feature / "spec.md").write_text("spec\n")
        (self.feature / "plan.md").write_text("plan\n")
        self.body = "## Phase 1\n" + "".join(
            f"- [ ] T{i:03d} [P] Add capability behavior {i}\n" for i in range(1, 13))
        (self.feature / "tasks.md").write_text(self.body)
        self.meta = {"schema_version": "task-execution.v1",
                     "fingerprints": fingerprints("spec\n", "plan\n", self.body),
                     "tasks": {f"T{i:03d}": {"capability_group": "feature", "depends_on": [],
                               "owns": [f"src/unit{i}.py"], "tdd_unit": f"behavior-{i}"}
                               for i in range(1, 13)}}
        self.metadata_path = self.feature / ".process/task-execution.json"
        self.metadata_path.write_text(json.dumps(self.meta))
        self.inputs = {"tasks_file": "feature/tasks.md",
                       "journal_file": "feature/.process/task-results/run.json"}
        self.path = self.root / self.inputs["journal_file"]

    def call(self, action="start", mode="apply", **inputs):
        return task_results(self.root, {**self.inputs, "action": action, **inputs}, mode)

    def report(self, batch):
        results, observations = [], []
        for task in batch["tasks"]:
            unit = self.meta["tasks"][task]["tdd_unit"]
            ids = []
            for stage in ("red", "green", "refactor"):
                event = f"{task}-{stage}"
                output = f"feature/.process/{event}.txt"
                raw = f"synthetic contract fixture {event}\n".encode()
                (self.root / output).write_bytes(raw)
                ids.append(event)
                observations.append({"event_id": event, "tdd_unit": unit, "stage": stage,
                    "argv": ["python3", "-m", "unittest", unit], "exit_code": 1 if stage == "red" else 0,
                    "classification": "assertion_failure" if stage == "red" else "test_pass",
                    "output_path": output, "output_sha256": hashlib.sha256(raw).hexdigest(),
                    "snapshot_sha256": hashlib.sha256(stage.encode()).hexdigest()})
            results.append({"task_id": task, "tdd_unit": unit, "status": "complete",
                            "block": f"## TaskResult {task}\nFull result for {task}\n", "evidence_event_ids": ids})
        return {"batch_id": batch["id"], "results": results, "native_observations": observations}

    def first_report(self):
        return self.report(self.call()["journal"]["batches"][0])

    def rejected_unchanged(self, report):
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.call("record", **report)
        self.assertEqual(before, self.path.read_bytes())

    def test_twelve_full_results_and_tdd_references_survive_three_real_partitions(self):
        journal = self.call()["journal"]
        self.assertEqual(len(journal["batches"]), 3)
        submitted = []
        for batch in journal["batches"]:
            report = self.report(batch)
            submitted.extend(report["results"])
            self.assertEqual(self.call("record", **report)["helper_exit_code"], 0)
        result = self.call("inspect", mode="read_only")
        stored = [r for report in result["journal"]["reports"] for r in report["results"]]
        self.assertEqual(stored, submitted)
        self.assertEqual(len(stored), 12)
        self.assertEqual(len({e for r in stored for e in r["evidence_event_ids"]}), 36)
        self.assertEqual(result["native_qualification"], "pending")
        self.assertFalse(result["authorization_granted"])

    def test_missing_duplicate_reordered_or_extra_task_rejected(self):
        original = self.first_report()
        variants = [original["results"][:-1], original["results"] + [original["results"][0]],
                    list(reversed(original["results"]))]
        for results in variants:
            with self.subTest(results=results):
                self.rejected_unchanged({**original, "results": results})

    def test_mismatched_task_unit_batch_and_empty_block_rejected(self):
        original = self.first_report()
        for key, value in (("task_id", "T999"), ("tdd_unit", "other"), ("block", ""), ("status", "passed")):
            report = copy.deepcopy(original)
            report["results"][0][key] = value
            self.rejected_unchanged(report)
        self.rejected_unchanged({**original, "batch_id": "B999"})

    def test_missing_tdd_and_worker_pass_without_native_events_rejected(self):
        original = self.first_report()
        self.rejected_unchanged({**original, "native_observations": []})
        report = copy.deepcopy(original)
        report["results"][0]["evidence_event_ids"] = []
        report["results"][0]["passed"] = True
        self.rejected_unchanged(report)

    def test_bad_native_command_or_assertion_classification_rejected(self):
        original = self.first_report()
        for index, key, value in ((0, "classification", "infrastructure"), (0, "exit_code", 0),
                                  (1, "exit_code", 1), (1, "argv", ["unrelated"]),
                                  (2, "stage", "green"), (0, "snapshot_sha256", "bad"),
                                  (0, "exit_code", True), (0, "event_id", "")):
            report = copy.deepcopy(original)
            report["native_observations"][index][key] = value
            self.rejected_unchanged(report)

    def test_duplicate_native_event_or_extra_event_rejected(self):
        report = self.first_report()
        report["native_observations"].append(copy.deepcopy(report["native_observations"][0]))
        self.rejected_unchanged(report)

    def test_output_missing_changed_escaping_or_symlink_rejected(self):
        original = self.first_report()
        for path in ("../escape", "/absolute", "feature/../escape", "feature\\file"):
            report = copy.deepcopy(original)
            report["native_observations"][0]["output_path"] = path
            self.rejected_unchanged(report)
        target = self.root / original["native_observations"][0]["output_path"]
        target.write_text("changed")
        self.rejected_unchanged(original)
        target.unlink()
        self.rejected_unchanged(original)
        target.symlink_to(self.feature / "spec.md")
        self.rejected_unchanged(original)

    def test_changed_metadata_spec_plan_and_task_definitions_rejected(self):
        report = self.first_report()
        for path in (self.metadata_path, self.feature / "spec.md", self.feature / "plan.md", self.feature / "tasks.md"):
            before = path.read_bytes()
            path.write_bytes(before + b"\n")
            self.rejected_unchanged(report)
            path.write_bytes(before)

    def test_checkbox_update_keeps_frozen_batch_identifiers(self):
        report = self.first_report()
        self.call("record", **report)
        before = self.path.read_bytes()
        (self.feature / "tasks.md").write_text(self.body.replace("[ ] T001", "[x] T001"))
        restarted = self.call()
        self.assertEqual(restarted["journal"]["batches"][0]["tasks"][0], "T001")
        self.assertEqual(self.path.read_bytes(), before)

    def test_unfinished_results_preserved_and_require_checkpoint(self):
        report = self.first_report()
        report["results"][0]["status"] = "unfinished"
        report["results"][0]["evidence_event_ids"] = []
        report["native_observations"] = report["native_observations"][3:]
        result = self.call("record", **report)
        self.assertEqual(result["helper_exit_code"], 1)
        self.assertEqual(result["disposition"], "checkpoint_required")
        self.assertEqual(result["journal"]["reports"][0]["results"], report["results"])
        inspected = self.call("inspect", mode="read_only")
        self.assertEqual(inspected["disposition"], "checkpoint_required")
        self.assertEqual(inspected["helper_exit_code"], 0)
        self.assertEqual(self.call()["disposition"], "checkpoint_required")

    def test_same_unit_cannot_report_test_only_green(self):
        self.meta["tasks"]["T002"]["tdd_unit"] = "behavior-1"
        self.metadata_path.write_text(json.dumps(self.meta))
        report = self.first_report()
        report["results"][1]["status"] = "unfinished"
        self.rejected_unchanged(report)

    def test_identical_replay_idempotent_conflicting_completed_replay_rejected(self):
        report = self.first_report()
        self.call("record", **report)
        before = self.path.read_bytes()
        self.call("record", **report)
        self.assertEqual(self.path.read_bytes(), before)
        report["results"][0]["block"] += "conflict"
        self.rejected_unchanged(report)

    def test_dry_run_and_read_only_do_not_create_or_modify_journal(self):
        self.call(mode="dry_run")
        self.assertFalse(self.path.parent.exists())
        with self.assertRaises(ValueError):
            self.call(mode="read_only")
        report = self.first_report()
        before = self.path.read_bytes()
        self.call("record", mode="dry_run", **report)
        self.call("inspect", mode="read_only")
        self.assertEqual(before, self.path.read_bytes())

    def test_new_journal_requires_explicit_prior_link_and_retains_old_results(self):
        report = self.first_report()
        self.call("record", **report)
        before = self.path.read_bytes()
        new = "feature/.process/task-results/reconciled.json"
        with self.assertRaises(ValueError):
            self.call(journal_file=new)
        result = self.call(journal_file=new, prior_journal_file=self.inputs["journal_file"],
                           reconciliation_event_id="native-parent-reconcile-1", reconciliation_reason="replanned")
        self.assertEqual(result["journal"]["reports"], [])
        self.assertEqual(result["journal"]["prior_journal_file"], self.inputs["journal_file"])
        self.assertEqual(before, self.path.read_bytes())

    def test_journal_target_cannot_overwrite_source(self):
        before = (self.feature / "tasks.md").read_bytes()
        with self.assertRaises(ValueError):
            self.call(journal_file="feature/tasks.md")
        self.assertEqual(before, (self.feature / "tasks.md").read_bytes())

    def test_malformed_or_duplicate_key_journal_fails_closed(self):
        self.call()
        original = self.path.read_bytes()
        for raw in (b'{"schema_version":"x","schema_version":"y"}', b'null', b'{"reports":NaN}'):
            self.path.write_bytes(raw)
            with self.assertRaises(ValueError):
                self.call("inspect", mode="read_only")
            self.assertEqual(raw, self.path.read_bytes())
        self.path.write_bytes(original)

    def test_stored_journal_shape_and_metadata_identity_are_validated_on_inspect(self):
        journal = self.call()["journal"]
        variants = []
        for key in ("task_units", "batches", "reports"):
            variant = copy.deepcopy(journal)
            del variant[key]
            variants.append(variant)
        variant = copy.deepcopy(journal)
        del variant["batches"][0]["tasks"]
        variants.append(variant)
        variant = copy.deepcopy(journal)
        variant["batches"][1]["id"] = "B001"
        variants.append(variant)
        variant = copy.deepcopy(journal)
        variant["batches"][0]["tasks"].append("T999")
        variants.append(variant)
        variant = copy.deepcopy(journal)
        variant["task_units"]["T001"] = "other"
        variants.append(variant)
        variant = copy.deepcopy(journal)
        variant["batches"][1]["tasks"].append("T001")
        variants.append(variant)
        for variant in variants:
            self.path.write_text(json.dumps(variant))
            before = self.path.read_bytes()
            with self.assertRaises(ValueError):
                self.call("inspect", mode="read_only")
            self.assertEqual(before, self.path.read_bytes())

    def test_feature_lock_rejects_concurrent_writer(self):
        self.call()
        lock = self.path.parent / "journal-writer.lock"
        lock.mkdir()
        with self.assertRaises(ValueError):
            self.call()
        self.assertTrue(lock.is_dir())

    def test_partial_retry_preserves_previously_completed_tasks(self):
        complete = self.first_report()
        partial = copy.deepcopy(complete)
        partial["results"][0]["status"] = "unfinished"
        partial["results"][0]["evidence_event_ids"] = []
        partial["native_observations"] = partial["native_observations"][3:]
        self.call("record", **partial)
        result = self.call("record", **complete)
        self.assertEqual(len(result["journal"]["reports"]), 2)
        self.assertEqual(result["helper_exit_code"], 0)

    def native_task_report(self, batch):
        results, observations = [], []
        for task in batch["tasks"]:
            output = f"feature/.process/{task}-result.txt"
            raw = f"Synthetic native task result {task}".encode()
            (self.root / output).write_bytes(raw)
            event, unit = f"{task}-result", self.meta["tasks"][task]["tdd_unit"]
            results.append({"task_id": task, "tdd_unit": unit, "status": "complete", "block": raw.decode(),
                            "evidence_event_ids": [event]})
            observations.append({"event_id": event, "tdd_unit": unit, "stage": "task_result", "task_id": task,
                                 "outcome": "completed", "output_path": output, "output_sha256": hashlib.sha256(raw).hexdigest()})
        return {"batch_id": batch["id"], "results": results, "native_observations": observations}

    def test_research_and_direct_routes_retain_results_without_fabricated_tdd(self):
        self.body = self.body.replace("Add capability behavior 1\n", "Research the interface\n").replace(
            "Add capability behavior 2\n", "Verify acceptance criteria\n")
        (self.feature / "tasks.md").write_text(self.body)
        self.meta["fingerprints"] = fingerprints("spec\n", "plan\n", self.body)
        self.metadata_path.write_text(json.dumps(self.meta))
        journal = self.call()["journal"]
        for batch in journal["batches"][:2]:
            self.assertIn("tdd_not_applicable_reason", batch)
            report = self.native_task_report(batch)
            result = self.call("record", **report)
            self.assertEqual(result["helper_exit_code"], 0)
            self.assertEqual(result["journal"]["reports"][-1]["results"], report["results"])

    def test_implementation_cannot_bypass_tdd_with_native_task_result(self):
        batch = self.call()["journal"]["batches"][0]
        self.assertNotIn("tdd_not_applicable_reason", batch)
        self.rejected_unchanged(self.native_task_report(batch))

    def test_worker_cannot_supply_tdd_not_applicable_reason(self):
        report = self.first_report()
        report["results"][0]["tdd_not_applicable_reason"] = "research"
        self.rejected_unchanged(report)

    def runner(self, action="start", mode="apply", **inputs):
        (self.root / ".specify").mkdir(exist_ok=True)
        environment = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "speckit-pro")}
        request = {"schema_version": "1.0", "helper_id": "task-results", "operation": "task-results",
                   "mode": mode, "inputs": {**self.inputs, "action": action, **inputs}}
        process = subprocess.run([sys.executable, "-m", "speckit_pro_runner"], cwd=self.root,
                                 env=environment, input=json.dumps(request), text=True, capture_output=True)
        return process.returncode, json.loads(process.stdout)

    def test_runner_start_dry_run_apply_inspect_and_three_complete_batches(self):
        code, result = self.runner(mode="dry_run")
        self.assertEqual(code, 0, result)
        self.assertFalse(self.path.parent.exists())
        code, result = self.runner()
        self.assertEqual(code, 0, result)
        for batch in result["data"]["journal"]["batches"]:
            code, recorded = self.runner("record", **self.report(batch))
            self.assertEqual(code, 0, recorded)
        code, result = self.runner("inspect", mode="read_only")
        self.assertEqual(code, 0, result)
        self.assertEqual(sum(len(r["results"]) for r in result["data"]["journal"]["reports"]), 12)

    def test_runner_unfinished_is_expected_failure_and_invalid_input_is_two(self):
        report = self.first_report()
        report["results"][0]["status"] = "unfinished"
        report["results"][0]["evidence_event_ids"] = []
        report["native_observations"] = report["native_observations"][3:]
        code, result = self.runner("record", **report)
        self.assertEqual(code, 1, result)
        self.assertEqual(result["status"], "expected_failure")
        code, inspected = self.runner("inspect", mode="read_only")
        self.assertEqual(code, 0, inspected)
        self.assertEqual(inspected["data"]["disposition"], "checkpoint_required")
        report["results"].append(copy.deepcopy(report["results"][0]))
        code, result = self.runner("record", **report)
        self.assertEqual(code, 2, result)
        self.metadata_path.write_text(self.metadata_path.read_text() + "\n")
        code, result = self.runner("inspect", mode="read_only")
        self.assertEqual(code, 2, result)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(BatchedTaskResultsTests),
                                label="batched-task-results"))
