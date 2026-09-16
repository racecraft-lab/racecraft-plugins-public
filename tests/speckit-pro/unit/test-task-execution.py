#!/usr/bin/env python3
"""Deterministic executable-task metadata and native dispatch partition tests."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))
sys.path.insert(0, str(REPO_ROOT / "tests/speckit-pro/lib"))
from test_result import run_counted
from speckit_pro_runner.helpers.read_only import partition_phase7_tasks, validate_task_execution
from speckit_pro_runner.task_execution import fingerprints


class TaskExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.feature = self.root / "feature"
        (self.feature / ".process").mkdir(parents=True)
        (self.feature / "spec.md").write_text("spec\n")
        (self.feature / "plan.md").write_text("plan\n")
        self.body = "## Phase 1\n" + "".join(
            f"- [ ] T{i:03d} [P] Add capability behavior {i}\n" for i in range(1, 13)
        )
        self.meta = {
            "schema_version": "task-execution.v1",
            "fingerprints": fingerprints("spec\n", "plan\n", self.body),
            "tasks": {f"T{i:03d}": {
                "capability_group": "feature", "depends_on": [],
                "owns": [f"src/unit{i}.py"], "tdd_unit": f"behavior-{i}"
            } for i in range(1, 13)},
        }

    def run_partition(self, **inputs):
        (self.feature / "tasks.md").write_text(self.body)
        (self.feature / ".process/task-execution.json").write_text(json.dumps(self.meta))
        result = partition_phase7_tasks({"tasks_file": "feature/tasks.md", **inputs}, self.root)
        return json.loads(result["stdout"]), result["exit_code"]

    def test_twelve_tasks_become_three_dispatches_with_every_task(self):
        value, code = self.run_partition(wave_size=2)
        self.assertEqual(code, 0, value)
        self.assertEqual(value["dispatch_count"], 3)
        self.assertEqual([t for b in value["batches"] for t in b["tasks"]], list(self.meta["tasks"]))
        self.assertEqual(value["waves"], [["B001", "B002"], ["B003"]])

    def test_checkbox_completion_does_not_invalidate_definitions(self):
        before = fingerprints("spec\n", "plan\n", self.body)
        self.body = self.body.replace("[ ] T001", "[x] T001")
        self.assertEqual(before, fingerprints("spec\n", "plan\n", self.body))
        value, code = self.run_partition(completed_tasks=["T001"])
        self.assertEqual(code, 0, value)
        self.assertNotIn("T001", [t for b in value["batches"] for t in b["tasks"]])

    def test_checkbox_without_parent_reconciliation_blocks(self):
        self.body = self.body.replace("[ ] T001", "[x] T001")
        self.assertEqual(self.run_partition()[1], 2)

    def test_definition_and_heading_changes_invalidate(self):
        for old, new in (("behavior 1", "behavior new"), ("Phase 1", "Phase 2"), ("[P]", "[US1]")):
            with self.subTest(new=new):
                original = self.body
                self.body = self.body.replace(old, new)
                self.assertEqual(self.run_partition()[1], 2)
                self.body = original

    def test_missing_and_extra_task_entries_block(self):
        del self.meta["tasks"]["T001"]
        self.assertEqual(self.run_partition()[1], 2)

    def test_cycles_and_forward_dependencies_block(self):
        self.meta["tasks"]["T001"]["depends_on"] = ["T002"]
        self.assertEqual(self.run_partition()[1], 2)
        self.meta["tasks"]["T002"]["depends_on"] = ["T001"]
        self.assertEqual(self.run_partition()[1], 2)

    def test_dependency_between_batches_serializes_waves(self):
        self.meta["tasks"]["T005"]["depends_on"] = ["T004"]
        value, code = self.run_partition()
        self.assertEqual(code, 0, value)
        self.assertEqual(value["waves"][0], ["B001"])

    def test_shared_and_ancestor_ownership_serializes(self):
        self.meta["tasks"]["T001"]["owns"] = ["src"]
        value, code = self.run_partition()
        self.assertEqual(code, 0, value)
        self.assertEqual(value["waves"][0], ["B001"])

    def test_case_alias_ownership_serializes(self):
        self.meta["tasks"]["T005"]["owns"] = ["SRC/UNIT1.PY"]
        value, code = self.run_partition()
        self.assertEqual(code, 0, value)
        self.assertEqual(value["waves"][0], ["B001"])

    def test_escaping_and_noncanonical_paths_block(self):
        for path in ("../outside", "/absolute", "src/../other", "./src", "src//other", "src\\file"):
            with self.subTest(path=path):
                self.meta["tasks"]["T001"]["owns"] = [path]
                self.assertEqual(self.run_partition()[1], 2)

    def test_symlink_escape_blocks(self):
        (self.root / "outside").symlink_to(self.root.parent, target_is_directory=True)
        self.meta["tasks"]["T001"]["owns"] = ["outside/file.py"]
        self.assertEqual(self.run_partition()[1], 2)

    def test_capability_changes_break_batches(self):
        self.meta["tasks"]["T003"]["capability_group"] = "other"
        value, code = self.run_partition()
        self.assertEqual(code, 0, value)
        self.assertEqual(value["batches"][0]["tasks"], ["T001", "T002"])

    def test_paired_tdd_units_are_not_split_at_four_task_boundary(self):
        self.meta["tasks"]["T004"]["tdd_unit"] = "paired"
        self.meta["tasks"]["T005"]["tdd_unit"] = "paired"
        value, code = self.run_partition()
        self.assertEqual(code, 0, value)
        self.assertEqual(value["batches"][0]["tasks"], ["T001", "T002", "T003"])
        self.assertEqual(value["batches"][1]["tasks"][:2], ["T004", "T005"])

    def test_split_tdd_completion_blocks_test_only_green(self):
        self.meta["tasks"]["T001"]["tdd_unit"] = "paired"
        self.meta["tasks"]["T002"]["tdd_unit"] = "paired"
        self.body = self.body.replace("[ ] T001", "[x] T001")
        self.assertEqual(self.run_partition(completed_tasks=["T001"])[1], 2)

    def test_nonparallel_batches_do_not_share_wave(self):
        self.body = self.body.replace(" [P]", "")
        self.meta["fingerprints"] = fingerprints("spec\n", "plan\n", self.body)
        value, code = self.run_partition()
        self.assertEqual(code, 0, value)
        self.assertTrue(all(len(w) == 1 for w in value["waves"]))

    def test_declared_file_reference_must_be_owned(self):
        self.body = self.body.replace("behavior 1\n", "behavior 1 in `tests/shared.py`\n")
        self.meta["fingerprints"] = fingerprints("spec\n", "plan\n", self.body)
        self.assertEqual(self.run_partition()[1], 2)

    def test_required_missing_metadata_blocks_but_legacy_remains(self):
        (self.feature / "tasks.md").write_text(self.body)
        for required, expected in ((True, 2), (False, 0)):
            result = partition_phase7_tasks({"tasks_file": "feature/tasks.md", "task_execution_required": required}, self.root)
            self.assertEqual(result["exit_code"], expected)
            if not required:
                self.assertEqual(json.loads(result["stdout"])["contract_version"], 1)

    def test_fingerprint_authoring_helper_and_validation_share_partition_seam(self):
        (self.feature / "tasks.md").write_text(self.body)
        result = validate_task_execution({"tasks_file": "feature/tasks.md", "action": "fingerprints"}, self.root)
        self.assertEqual(result["exit_code"], 0, result)
        value = json.loads(result["stdout"])
        self.assertEqual(value["fingerprints"], self.meta["fingerprints"])
        self.assertEqual(value["task_ids"], list(self.meta["tasks"]))
        self.run_partition()
        result = validate_task_execution({"tasks_file": "feature/tasks.md"}, self.root)
        self.assertTrue(json.loads(result["stdout"])["valid"])

    def test_spec_or_plan_changes_invalidate_metadata(self):
        for name in ("spec.md", "plan.md"):
            with self.subTest(name=name):
                target = self.feature / name
                original = target.read_text()
                target.write_text("changed")
                self.assertEqual(self.run_partition()[1], 2)
                target.write_text(original)

    def test_appended_task_requires_reconciliation(self):
        self.body += "- [ ] T013 Add appended behavior\n"
        self.assertEqual(self.run_partition()[1], 2)

    def test_completed_task_requires_completed_prerequisites(self):
        self.meta["tasks"]["T002"]["depends_on"] = ["T001"]
        self.body = self.body.replace("[ ] T002", "[x] T002")
        self.assertEqual(self.run_partition(completed_tasks=["T002"])[1], 2)

    def test_duplicate_metadata_keys_are_rejected(self):
        self.run_partition()
        target = self.feature / ".process/task-execution.json"
        target.write_text(target.read_text().replace('"depends_on": []', '"depends_on": [], "depends_on": []', 1))
        result = partition_phase7_tasks({"tasks_file": "feature/tasks.md"}, self.root)
        self.assertEqual(result["exit_code"], 2)

    def test_tdd_unit_cannot_span_routes_or_phases(self):
        self.meta["tasks"]["T001"]["tdd_unit"] = "paired"
        self.meta["tasks"]["T002"]["tdd_unit"] = "paired"
        self.body = self.body.replace("Add capability behavior 2", "Investigate capability behavior 2")
        self.meta["fingerprints"] = fingerprints("spec\n", "plan\n", self.body)
        self.assertEqual(self.run_partition()[1], 2)

    def test_internal_symlink_alias_ownership_serializes(self):
        (self.root / "src").mkdir()
        (self.root / "alias").symlink_to(self.root / "src", target_is_directory=True)
        self.meta["tasks"]["T005"]["owns"] = ["alias/unit1.py"]
        value, code = self.run_partition()
        self.assertEqual(code, 0, value)
        self.assertEqual(value["waves"][0], ["B001"])

    def test_helper_action_rejects_invalid_types(self):
        result = validate_task_execution({"action": []}, self.root)
        self.assertEqual(result["exit_code"], 2)

    def test_foreign_or_duplicate_completion_assertions_are_rejected(self):
        for completed in ([True], ["T999"], ["T001", "T001"]):
            with self.subTest(completed=completed):
                self.assertEqual(self.run_partition(completed_tasks=completed)[1], 2)

    def test_five_task_tdd_unit_requires_smaller_behavioral_units(self):
        for i in range(1, 6):
            self.meta["tasks"][f"T{i:03d}"]["tdd_unit"] = "large"
        self.assertEqual(self.run_partition()[1], 2)

    def test_phase_boundary_never_shares_batch_or_wave(self):
        self.body = self.body.replace("- [ ] T003", "## Phase 2\n- [ ] T003")
        self.meta["fingerprints"] = fingerprints("spec\n", "plan\n", self.body)
        value, code = self.run_partition()
        self.assertEqual(code, 0, value)
        self.assertEqual(value["batches"][0]["tasks"], ["T001", "T002"])
        self.assertEqual(value["waves"][0], ["B001"])

    def test_root_level_references_require_ownership(self):
        for reference in ("package.json", "AGENTS.md", "Makefile", ".gitignore"):
            with self.subTest(reference=reference):
                original = self.body
                self.body = self.body.replace("behavior 1\n", f"behavior 1 in `{reference}`\n")
                self.meta["fingerprints"] = fingerprints("spec\n", "plan\n", self.body)
                self.assertEqual(self.run_partition()[1], 2)
                self.body = original

    def test_root_manifest_reference_cannot_authorize_parallel_writes(self):
        for i in (1, 5):
            self.body = self.body.replace(f"behavior {i}\n", f"behavior {i} in `package.json`\n")
            self.meta["tasks"][f"T{i:03d}"]["owns"] = ["package.json"]
        self.meta["fingerprints"] = fingerprints("spec\n", "plan\n", self.body)
        value, code = self.run_partition()
        self.assertEqual(code, 0, value)
        self.assertEqual(value["waves"][0], ["B001"])

    def test_escaping_title_references_are_not_silently_dropped(self):
        for reference in ("../outside.py", "/private/tmp/outside.py", "src/../../outside.py", "C:\\outside.py", "~/outside.py"):
            with self.subTest(reference=reference):
                original = self.body
                self.body = self.body.replace("behavior 1\n", f"behavior 1 in `{reference}`\n")
                self.meta["fingerprints"] = fingerprints("spec\n", "plan\n", self.body)
                self.assertEqual(self.run_partition()[1], 2)
                self.body = original

    def test_hardlinked_owned_files_fail_closed(self):
        os.link(self.feature / "spec.md", self.feature / "linked-spec.md")
        self.meta["tasks"]["T001"]["owns"] = ["feature/spec.md"]
        self.meta["tasks"]["T005"]["owns"] = ["feature/linked-spec.md"]
        self.assertEqual(self.run_partition()[1], 2)

    def test_hardlinked_directory_descendants_fail_closed(self):
        for name in ("a", "b"):
            (self.root / name).mkdir()
        (self.root / "a/shared.py").write_text("shared")
        os.link(self.root / "a/shared.py", self.root / "b/alias.py")
        self.meta["tasks"]["T001"]["owns"] = ["a"]
        self.meta["tasks"]["T005"]["owns"] = ["b"]
        self.assertEqual(self.run_partition()[1], 2)

    def test_unicode_normalization_aliases_are_not_parallel(self):
        (self.feature / "caf\u00e9.md").write_text("same file on normalization-insensitive hosts")
        self.meta["tasks"]["T001"]["owns"] = ["feature/caf\u00e9.md"]
        self.meta["tasks"]["T005"]["owns"] = ["feature/cafe\u0301.md"]
        value, code = self.run_partition()
        self.assertEqual(code, 0, value)
        self.assertEqual(value["waves"][0], ["B001"])

    def test_repeated_phase_title_preserves_dispatch_boundary(self):
        self.body = self.body.replace("- [ ] T003", "## Phase 1\n- [ ] T003")
        self.meta["fingerprints"] = fingerprints("spec\n", "plan\n", self.body)
        value, code = self.run_partition()
        self.assertEqual(code, 0, value)
        self.assertEqual(value["batches"][0]["tasks"], ["T001", "T002"])
        self.assertEqual(value["waves"][0], ["B001"])

    def test_tdd_unit_cannot_cross_repeated_phase_title(self):
        self.meta["tasks"]["T002"]["tdd_unit"] = "paired"
        self.meta["tasks"]["T003"]["tdd_unit"] = "paired"
        self.body = self.body.replace("- [ ] T003", "## Phase 1\n- [ ] T003")
        self.meta["fingerprints"] = fingerprints("spec\n", "plan\n", self.body)
        self.assertEqual(self.run_partition()[1], 2)

    def test_slash_separated_prose_does_not_invent_file_ownership(self):
        self.body = self.body.replace("Add capability behavior 1\n", "Add unit/integration coverage in `src/unit1.py`\n")
        self.meta["fingerprints"] = fingerprints("spec\n", "plan\n", self.body)
        value, code = self.run_partition()
        self.assertEqual(code, 0, value)

    def test_explicit_extensionless_paths_still_require_ownership(self):
        self.body = self.body.replace("behavior 1\n", "behavior 1 in `src/policy`\n")
        self.meta["fingerprints"] = fingerprints("spec\n", "plan\n", self.body)
        self.assertEqual(self.run_partition()[1], 2)

    def test_symlink_descendants_require_narrower_explicit_ownership(self):
        (self.root / "src").mkdir()
        (self.root / "src/shared.py").symlink_to(self.feature / "spec.md")
        self.meta["tasks"]["T001"]["owns"] = ["src"]
        self.assertEqual(self.run_partition()[1], 2)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(TaskExecutionTests), label="test-task-execution"))
