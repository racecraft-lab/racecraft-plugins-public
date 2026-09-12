#!/usr/bin/env python3
"""Deterministic checks for the paired native execution policy boundaries."""
from pathlib import Path
import sys
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


class ExecutionContractTests(unittest.TestCase):
    def test_both_hosts_load_one_durable_contract(self):
        for root in (SHARED, CODEX):
            with self.subTest(host=root):
                self.assertIn("execution-efficiency.md", (root / "SKILL.md").read_text())
        policy = (SHARED / "references/execution-efficiency.md").read_text()
        for helper in ("validate-task-execution", "partition-phase7-tasks",
                       "execution-control", "execute-verification",
                       "validate-execution-record"):
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


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(ExecutionContractTests),
        label="test-autopilot-execution-contract",
    ))
