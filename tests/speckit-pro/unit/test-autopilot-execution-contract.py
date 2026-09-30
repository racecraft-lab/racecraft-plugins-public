#!/usr/bin/env python3
"""Deterministic checks for the paired native execution policy boundaries."""
from pathlib import Path
import json
import re
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "speckit-pro"
LIB_DIR = ROOT / "tests/speckit-pro/lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from host_skill_views import host_skill_root  # noqa: E402
# Each host's autopilot skill as it ships, rendered from the one shared source.
SHARED = host_skill_root("claude") / "speckit-autopilot"
CODEX = host_skill_root("codex") / "speckit-autopilot"
from script_loader import load_script  # noqa: E402
from test_result import run_counted  # noqa: E402
if str(PLUGIN) not in sys.path:
    sys.path.insert(0, str(PLUGIN))
from speckit_pro_runner.execution_control import execution_control  # noqa: E402
from speckit_pro_runner.helpers.read_only import json_schema_failures  # noqa: E402


class LiveCanaryRegressionTests(unittest.TestCase):
    def test_claude_explicit_loader_does_not_reinvoke_the_active_skill(self):
        shared = (SHARED / "SKILL.md").read_text()
        boundary = " ".join(shared.split("## Explicit Invocation Boundary", 1)[1].split(
            "## Installed Runtime Contract", 1
        )[0].split())
        self.assertIn("skill is already active", boundary)
        self.assertIn("Do not invoke the `Skill` tool", boundary)
        self.assertIn("does not authorize stopping", boundary)

    def test_codex_requires_direct_update_plan_invocation(self):
        codex = (CODEX / "SKILL.md").read_text()
        runtime = codex.split("## Codex Runtime Contract", 1)[1].split(
            "## Scope", 1
        )[0]
        self.assertIn("Invoke it directly", runtime)
        self.assertIn("do not infer that it is unavailable", runtime)
        self.assertIn("actual call is rejected", runtime)

    def test_codex_pre_final_audit_drains_separately_attributable_gate_runs(self):
        post = (CODEX / "references/post-implementation.md").read_text()
        audit = " ".join(post.split("- **Pre-final completion audit:**", 1)[1].split(
            "## PR Packet Validation Workflow", 1
        )[0].split())
        for boundary in (
            "run each gate exactly once as a separately attributable foreground command",
            "do not launch an overlapping copy while an equivalent gate is pending",
            "forbidden while any started tool item remains in progress",
            "wait on that exact native handle for its terminal result",
        ):
            self.assertIn(boundary, audit)

        skill_audit = " ".join((CODEX / "SKILL.md").read_text().split(
            "### 3.4 Pre-final completion audit", 1
        )[1].split("## Workflow File Update Protocol", 1)[0].split())
        for boundary in (
            "reconcile every started native command, tool, and agent",
            "separately attributable foreground command",
            "wait on that exact native handle",
            "report an incomplete checkpoint instead of a completion response",
        ):
            self.assertIn(boundary, skill_audit)


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
        # A run has no wall-clock limit, so task sizing must not cite a two-hour budget.
        self.assertNotIn("two-hour", " ".join(tasks.split()))
        self.assertIn("Small, complete behavioral units", tasks)
        for key in ("task-execution.v1", "task-execution.json", "capability_group",
                    "depends_on", "owns", "tdd_unit", "fingerprints"):
            self.assertIn(key, tasks)

    def test_checklist_domain_list_lives_only_in_the_guide(self):
        import re

        guide = (PLUGIN / "skills/speckit-coach/references/checklist-domains-guide.md").read_text()
        template = (PLUGIN / "skills/speckit-coach/templates/workflow-template.md").read_text()
        row = r"^\|[^|\n]+\| \*\*([a-z-]+)\*\* \|"
        in_guide = set(re.findall(row, guide, re.M))
        # The guide is the one domain list: all 15 domains, and the template keeps no copy.
        self.assertTrue({"privacy", "supply-chain", "integration", "mobile-ux", "reliability"} <= in_guide, in_guide)
        self.assertEqual(15, len(in_guide))
        self.assertEqual(set(), set(re.findall(row, template, re.M)))
        self.assertIn("references/checklist-domains-guide.md", template)

    def test_quality_gates_table_has_a_row_per_discovered_slot(self):
        from speckit_pro_runner.gate_discovery import SLOTS

        template = (PLUGIN / "skills/speckit-coach/templates/workflow-template.md").read_text()
        table = template.split("### Quality Gates", 1)[1].split("\n---\n", 1)[0]
        rows = {line.split("|")[1].strip() for line in table.splitlines()
                if line.startswith("| ") and not line.startswith("| Slot ")}
        self.assertEqual(set(SLOTS), rows)

    def test_paired_executors_preserve_per_task_results_in_batches(self):
        claude = (PLUGIN / "agents/implement-executor.md").read_text()
        codex = tomllib.loads((PLUGIN / "codex-agents/implement-executor.toml").read_text())
        self.assertEqual(codex["model"], "gpt-6-sol")
        self.assertEqual(codex["model_reasoning_effort"], "xhigh")
        for text in (claude, codex["developer_instructions"]):
            for contract in ("up to four", "sequentially", "tdd_unit", "## Task Result: <TASK_ID>",
                             "unfinished", "reservation"):
                self.assertIn(contract, text)
            self.assertNotIn("Executes a SINGLE", text)

    def test_unknown_results_do_not_authorize_relaunch(self):
        for path in (SHARED / "references/error-recovery.md",
                     CODEX / "references/error-recovery.md"):
            text = " ".join(path.read_text().split())
            self.assertNotIn("make one fresh retry", text)
            self.assertNotIn("Re-spawn with the", text)
            self.assertIn("read-only reconciliation", text)

    def test_plan_rescope_reconciles_every_plan_artifact_before_g3_on_both_hosts(self):
        # A rescope once left research.md, quickstart.md, and the requirements
        # checklist on the old slice count while plan.md moved on, and no gate caught it.
        rule = (
            "After a rescope changes plan.md's scope, slices, or delivery order, the parent "
            "reconciles every Plan artifact before G3: `research.md`, `quickstart.md`, "
            "`data-model.md`, `contracts/`, and every file under `checklists/`. Record what "
            "changed in each artifact in the workflow file's Plan Results."
        )
        claude = " ".join((SHARED / "references/phase-execution.md").read_text().split())
        plan = claude.split("### Phase 3: Plan", 1)[1].split("**Gate:** G3", 1)[0]
        self.assertIn(rule, plan)
        codex = " ".join((CODEX / "references/phase-execution.md").read_text().split())
        loop = codex.split("7. Validate gate directly in the main session:", 1)[1].split(
            "8. If gate fails:", 1)[0]
        self.assertIn(rule, loop)
        for executor in (PLUGIN / "agents/phase-executor.md",
                         PLUGIN / "codex-agents/phase-executor.toml"):
            with self.subTest(executor=executor.name):
                text = " ".join(executor.read_text().split())
                self.assertIn("Plan reports artifact status and any rescope of plan.md", text)

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
        cls.validator = load_script(
            "execution_contract_status_validator",
            SHARED / "scripts/validate-autopilot-phase-coverage.py",
        )

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
        schema = json.loads((PLUGIN / "speckit_pro_runner/contracts/execution-control.schema.json").read_text())
        self.assertEqual([], json_schema_failures(result["ledger"], schema, schema, "ledger"))
        unbound = {key: value for key, value in result["ledger"].items() if key != "workflow_identity"}
        self.assertTrue(json_schema_failures(unbound, schema, schema, "ledger"))
        mirror = {key: result[key] for key in (
            "ledger_path", "disposition", "reasons", "elapsed_seconds", "checkpoint_due",
        )}
        mirror["run_id"] = result["ledger"]["run_id"]
        self.assertEqual([], self.validator.validate_state_status({
            "status": "in_progress", "execution_control": mirror,
        })["state_status_errors"])
        deferred = dict(mirror, disposition="defer", reasons=["failure_family_budget_exhausted"])
        self.assertEqual([], self.validator.validate_state_status({
            "status": "in_progress", "execution_control": deferred,
        })["state_status_errors"])
        self.assertTrue(self.validator.validate_state_status({
            "status": "in_progress", "execution_control": dict(mirror, disposition="stop_for_approval"),
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
        schema = json.loads((PLUGIN / "speckit_pro_runner/contracts/task-results.schema.json").read_text())
        self.assertIn("partition_sha256", schema["required"])
        self.assertEqual({"$ref": "#/$defs/digest"}, schema["properties"]["partition_sha256"])
        policy = " ".join((SHARED / "references/execution-efficiency.md").read_text().split())
        for boundary in ("`stage=task_result`", "`outcome=completed`",
                         "`tdd_not_applicable_reason`", "frozen route",
                         "previously complete task's block and evidence references unchanged",
                         "never fabricate RED/GREEN/refactor"):
            with self.subTest(boundary=boundary):
                self.assertIn(boundary, policy)

    def test_both_native_dispatches_use_persisted_task_results(self):
        for path in (SHARED / "references/phase-execution.md",
                     CODEX / "references/phase-execution.md"):
            phase = " ".join(path.read_text().split())
            with self.subTest(path=path):
                for call in ("task-results", "action=start", "action=record", "action=inspect"):
                    self.assertIn(call, phase)
                self.assertIn("before dispatch", phase)
                self.assertIn("native_observations", phase)
                self.assertIn("unfinished", phase)
                for term in ("partition_sha256", "expected_partition_sha256", "original parent start result"):
                    self.assertTrue(term in phase, f"{path.name}: missing required {term}")

    def test_parent_mirror_contract_names_actual_envelope_and_spec_path(self):
        policy = (SHARED / "references/execution-efficiency.md").read_text()
        for term in ("inputs.spec_file", "result.data.ledger.run_id", "ledger_path",
                     "not independent proof", "native orchestrator"):
            self.assertIn(term, policy)

    def test_docker_reuse_requires_versioned_closure_and_fresh_gate_validation(self):
        policy = " ".join((SHARED / "references/execution-efficiency.md").read_text().split())
        for boundary in (
            "`docker-verification-record/v1` remains non-reusable",
            "`docker-verification-record/v2`",
            "`execution_closure_sha256`",
            "`revalidation_input_sha256`",
            'qualification_profile="docker-qualified/v2"',
            "before and after execution",
            "never reconstruct it from a receipt or worker text",
            "Missing runtime qualification requires rerunning",
        ):
            with self.subTest(boundary=boundary):
                self.assertTrue(boundary in policy, f"missing Docker boundary: {boundary}")
        for path in (SHARED / "references/gate-validation.md",
                     SHARED / "references/post-implementation.md",
                     CODEX / "references/post-implementation.md"):
            gate = " ".join(path.read_text().split())
            with self.subTest(gate=path.name):
                self.assertTrue("revalidate current inputs" in gate, f"{path.name}: missing current-input validation")
                self.assertTrue("same independently retained observation" in gate, f"{path.name}: missing retained observation")

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
            "`relocate-workflow`",
            "`action=workflow_relocated`",
            "`previous_workflow_file`",
            "Each `native_event_id` is single-use across workflow moves, wait boundaries, and recovered dispatch results",
        ):
            with self.subTest(boundary=boundary):
                self.assertTrue(boundary in policy, f"missing required boundary: {boundary}")
        verification = policy.split("Use `execute-verification`", 1)[1].split(
            "Persist discovered commands", 1)[0]
        for required in ("`expected_run_id`", "`dispatch_id`", "`ledger_path`"):
            self.assertIn(required, verification)


def _flat(path: Path) -> str:
    return " ".join(path.read_text().split())


class ImplementChecklistGateTests(unittest.TestCase):
    """Autopilot records the implement checklist gate instead of silently skipping it.

    Spec Kit's checklist items are reviewer-owned, and stock `/speckit-implement`
    stops on unticked items. Autopilot defers those items to PR review, keeps
    `[Gap]` markers blocking through G4, and writes the decision down.
    """

    PHASE_EXECUTION = (
        SHARED / "references/phase-execution.md",
        CODEX / "references/phase-execution.md",
    )

    def test_both_hosts_record_the_gate_before_the_first_dispatch(self):
        for path in self.PHASE_EXECUTION:
            with self.subTest(host=path.name):
                text = _flat(path)
                self.assertIn("Record the Implement Checklist Gate", text)
                gate = re.split("Open the implementation-notes record",
                                text.split("Record the Implement Checklist Gate", 1)[1],
                                maxsplit=1, flags=re.I)[0]
                for phrase in (
                    "before the first Phase 7 dispatch",
                    "`deferred-to-review`",
                    "reviewer-owned",
                    "Autopilot never ticks a reviewer-owned item",
                    "`[Gap]` markers are not deferred: they stay blocking through G4",
                    "`### Implement Checklist Gate`",
                    "`## Phase 7: Implement`",
                    "`unknown`",
                    "never asks the operator",
                ):
                    self.assertIn(phrase, gate)

    def test_g4_names_the_deferral(self):
        g4 = _flat(SHARED / "references/gate-validation.md").split(
            "### G4 — After Checklist", 1)[1].split("**Auto-Fix:**", 1)[0]
        self.assertIn("counts only `[Gap]` markers", g4)
        self.assertIn("deferred to PR review", g4)
        self.assertIn("Implement Checklist Gate", g4)

    def test_workflow_protocol_lists_the_record_on_both_hosts(self):
        for path in (SHARED / "references/workflow-file-protocol.md",
                     CODEX / "references/workflow-file-protocol.md"):
            with self.subTest(host=path.name):
                row = next(line for line in path.read_text().splitlines()
                           if line.startswith("| **Implement** |"))
                self.assertIn("Implement Checklist Gate", row)

    def test_pr_body_tells_the_reviewer_the_boxes_are_theirs(self):
        for path in (SHARED / "references/post-implementation.md",
                     CODEX / "references/post-implementation.md"):
            with self.subTest(host=path.name):
                text = _flat(path)
                self.assertIn("`how_to_review`", text)
                self.assertIn("left unticked for the reviewer", text)

    def test_executors_neither_stop_on_nor_tick_checklist_items(self):
        claude = (PLUGIN / "agents/implement-executor.md").read_text()
        codex = tomllib.loads((PLUGIN / "codex-agents/implement-executor.toml").read_text())
        for text in (claude, codex["developer_instructions"]):
            rules = " ".join(text.split("</hard_constraints>", 1)[0].split())
            self.assertIn("Do not stop on unticked domain checklist items", rules)
            self.assertIn("Never edit a checklist marker", rules)

    def test_dispatch_prompts_carry_the_rule_to_project_agents(self):
        for path in self.PHASE_EXECUTION:
            with self.subTest(host=path.name):
                self.assertIn("do not stop on unticked ones, and never edit a checklist marker",
                              _flat(path))


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                           for case in (LiveCanaryRegressionTests, ExecutionContractTests,
                                        ExecutionMirrorTests,
                                        NativeRequestContractTests,
                                        ImplementChecklistGateTests)),
        label="test-autopilot-execution-contract",
    ))
