#!/usr/bin/env python3
"""Deterministic checks for the paired native execution policy boundaries."""
from pathlib import Path
import importlib.util
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "speckit-pro"
SHARED = PLUGIN / "skills/speckit-autopilot"
CODEX = PLUGIN / "codex-skills/speckit-autopilot"
LIB_DIR = ROOT / "tests/speckit-pro/lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402
if str(PLUGIN) not in sys.path:
    sys.path.insert(0, str(PLUGIN))
from speckit_pro_runner.execution_control import execution_control  # noqa: E402


class ExecutionContractTests(unittest.TestCase):
    def test_both_hosts_load_one_durable_contract(self):
        for root in (SHARED, CODEX):
            with self.subTest(host=root):
                self.assertIn("execution-efficiency.md", (root / "SKILL.md").read_text())
        policy = (SHARED / "references/execution-efficiency.md").read_text()
        for helper in ("validate-task-execution", "partition-phase7-tasks",
                       "execution-control", "execute-verification",
                       "validate-execution-record", "task-results"):
            self.assertIn(helper, policy)
        for field in ("checkpoint_required", "failure_invariant", "reservation_id",
                      "task_execution_required", "completed_tasks", "reusable=false"):
            self.assertIn(field, policy)

    def test_tasks_producer_declares_closed_behavior_and_sidecar(self):
        template = (PLUGIN / "skills/speckit-coach/templates/workflow-template.md").read_text()
        tasks = template.split("## Phase 5: Tasks", 1)[1].split("### Tasks Results", 1)[0]
        self.assertNotIn("1-2 hours each", tasks)
        for key in ("task-execution.v1", "task-execution.json", "capability_group",
                    "depends_on", "owns", "tdd_unit", "fingerprints"):
            self.assertIn(key, tasks)

    def test_paired_executors_preserve_per_task_results_in_batches(self):
        claude = (PLUGIN / "agents/implement-executor.md").read_text()
        codex = tomllib.loads((PLUGIN / "codex-agents/implement-executor.toml").read_text())
        self.assertEqual(codex["model"], "gpt-5.6-sol")
        self.assertEqual(codex["model_reasoning_effort"], "xhigh")
        for text in (claude, codex["developer_instructions"]):
            for contract in ("up to four", "sequentially", "tdd_unit", "## Task Result: <TASK_ID>",
                             "unfinished", "reservation"):
                self.assertIn(contract, text)
            self.assertNotIn("Executes a SINGLE", text)

    def test_unknown_results_do_not_authorize_relaunch(self):
        for path in (SHARED / "references/error-recovery.md",
                     CODEX / "references/error-recovery-codex.md"):
            text = " ".join(path.read_text().split())
            self.assertNotIn("make one fresh retry", text)
            self.assertNotIn("Re-spawn with the", text)
            self.assertIn("read-only reconciliation", text)

    def test_native_dispatch_keeps_direct_route_and_owned_cleanup(self):
        phase = (SHARED / "references/phase-execution.md").read_text()
        dispatch = phase.split("##### Step 3b: Execute Each Batch", 1)[1].split(
            "##### Step 3c: Agent Prompt Template", 1)[0]
        self.assertIn("For orchestrator-direct batches", dispatch)
        self.assertIn("without an Agent", dispatch)
        self.assertIn("domain-researcher", dispatch)
        self.assertIn("without TDD", dispatch)
        self.assertIn("confirm owned cleanup", dispatch)

    def test_count_growth_is_not_acceptance_and_checkpoint_is_not_completion(self):
        gate = (SHARED / "references/gate-validation.md").read_text()
        self.assertNotIn("Verify test count increased", gate)
        audit = (CODEX / "SKILL.md").read_text().split("### 3.4 Pre-final completion audit", 1)[1]
        self.assertIn("checkpoint_required", audit)
        self.assertIn("not complete", audit)

class ExecutionMirrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "execution_contract_status_validator",
            SHARED / "scripts/validate-autopilot-phase-coverage.py",
        )
        cls.validator = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.validator
        spec.loader.exec_module(cls.validator)

    def test_state_mirror_accepts_actual_ledger_result_without_new_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            (root / "feature").mkdir()
            (root / "docs/workflow.md").write_text("# Workflow\n", encoding="utf-8")
            (root / "feature/spec.md").write_text("FR-101 Preserve behavior\n", encoding="utf-8")
            result = execution_control(root, {
                "workflow_file": "docs/workflow.md", "spec_file": "feature/spec.md",
                "action": "start",
            }, "apply")
        mirror = {key: result[key] for key in (
            "ledger_path", "disposition", "reasons", "elapsed_seconds", "checkpoint_due",
        )}
        mirror["run_id"] = result["ledger"]["run_id"]
        self.assertEqual([], self.validator.validate_state_status({
            "status": "in_progress", "execution_control": mirror,
        })["state_status_errors"])
        checkpoint = dict(mirror, disposition="checkpoint_required", reasons=["slice_deadline"])
        self.assertEqual([], self.validator.validate_state_status({
            "status": "awaiting_review", "execution_control": checkpoint,
        })["state_status_errors"])
        self.assertTrue(self.validator.validate_state_status({
            "status": "checkpoint_required", "execution_control": checkpoint,
        })["state_status_errors"])

    def test_state_mirror_rejects_invalid_fields_and_preserves_legacy_absence(self):
        baseline = {
            "ledger_path": "docs/.process/execution-control.json", "run_id": "run-123",
            "disposition": "continue", "reasons": [], "elapsed_seconds": 0.1,
            "checkpoint_due": False,
        }
        self.assertEqual([], self.validator.validate_state_status({})["state_status_errors"])
        invalid = (
            {"ledger_path": "../escape.json"}, {"ledger_path": "/tmp/ledger.json"},
            {"run_id": ""}, {"disposition": "completed"}, {"reasons": [1]},
            {"elapsed_seconds": True}, {"elapsed_seconds": -1}, {"checkpoint_due": "false"},
            {"reservation_id": "worker-added"},
        )
        for replacement in invalid:
            with self.subTest(replacement=replacement):
                self.assertTrue(self.validator.validate_state_status({
                    "execution_control": dict(baseline, **replacement),
                })["state_status_errors"])
        for field in baseline:
            with self.subTest(missing=field):
                mirror = {key: value for key, value in baseline.items() if key != field}
                self.assertTrue(self.validator.validate_state_status({
                    "execution_control": mirror,
                })["state_status_errors"])

class NativeRequestContractTests(unittest.TestCase):
    def test_journal_evidence_follows_frozen_route_and_preserves_partial_results(self):
        policy = " ".join((SHARED / "references/execution-efficiency.md").read_text().split())
        for boundary in ("`stage=task_result`", "`outcome=completed`",
                         "`tdd_not_applicable_reason`", "frozen route",
                         "previously complete task's block and evidence references unchanged",
                         "never fabricate RED/GREEN/refactor"):
            with self.subTest(boundary=boundary):
                self.assertIn(boundary, policy)

    def test_both_native_dispatches_use_persisted_task_results(self):
        for path in (SHARED / "references/phase-execution.md",
                     CODEX / "references/phase-execution-codex.md"):
            phase = " ".join(path.read_text().split())
            with self.subTest(path=path):
                for call in ("task-results", "action=start", "action=record", "action=inspect"):
                    self.assertIn(call, phase)
                self.assertIn("before dispatch", phase)
                self.assertIn("native_observations", phase)
                self.assertIn("unfinished", phase)

    def test_parent_mirror_contract_names_actual_envelope_and_spec_path(self):
        policy = (SHARED / "references/execution-efficiency.md").read_text()
        for term in ("inputs.spec_file", "result.data.ledger.run_id", "ledger_path",
                     "not independent proof", "native orchestrator"):
            self.assertIn(term, policy)

    def test_resume_requests_bind_run_and_independent_events(self):
        policy = " ".join((SHARED / "references/execution-efficiency.md").read_text().split())
        for boundary in (
            "Every non-start action requires `inputs.expected_run_id`",
            "known resume also passes `expected_run_id`",
            "missing ledger is a recovery failure, never a new kickoff",
            "`ledger_path` returned by the helper",
            "`reconciliation_allowed=true`",
            "`action=dispatch_result`",
            "`wait_start_event_id`",
            "do not pre-call `begin-verification`",
        ):
            with self.subTest(boundary=boundary):
                self.assertIn(boundary, policy)
        verification = policy.split("Use `execute-verification`", 1)[1].split(
            "Persist discovered commands", 1)[0]
        for required in ("`expected_run_id`", "`dispatch_id`", "`ledger_path`"):
            self.assertIn(required, verification)


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                           for case in (ExecutionContractTests, ExecutionMirrorTests,
                                        NativeRequestContractTests)),
        label="test-autopilot-execution-contract",
    ))
