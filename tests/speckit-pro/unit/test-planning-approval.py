#!/usr/bin/env python3
"""Planning approval at the portable runner request seam."""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from runner_invocation import run_runner
from test_result import run_counted


ASSURANCE_DOCUMENTS = (
    "docs/adr/0013-plan-approval-record.md", "docs/adr/0017-recorded-plan-approval.md",
    ".github/pull_request_template.md", "GLOSSARY.md", "speckit-pro/skills/speckit-autopilot/SKILL.md",
    "speckit-pro/skills/speckit-autopilot/references/planning-approval.md",
    "speckit-pro/agents/phase-executor.md", "speckit-pro/codex-agents/phase-executor.toml",
    "speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml",
    "dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md",
    "dist/claude/speckit-pro/skills/speckit-autopilot/references/planning-approval.md",
    "dist/claude/speckit-pro/agents/phase-executor.md",
    "dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md",
    "dist/codex/speckit-pro/skills/speckit-autopilot/references/planning-approval.md",
    "dist/codex/speckit-pro/codex-agents/phase-executor.toml",
    "dist/codex/speckit-pro/skills/speckit-autopilot/agents/openai.yaml",
)
UNRELATED_NEGATIONS = tuple((word, separator) for word in ("No", "not", "never", "nothing")
                            for separator in (". ", "; ", ", ", " and ", "\n"))


class PlanningApprovalTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        (self.root / ".specify").mkdir()
        self.runner_root = Path(__file__).resolve().parents[3] / "speckit-pro"
        self.feature = self.root / "specs/demo"
        self.feature.mkdir(parents=True)
        for name, text in {"spec.md": "A feature", "plan.md": "A plan",
                           "tasks.md": "- [ ] T001 Build a thing", "workflow.md": "## Project Commands\nTest: python3 check.py\n"}.items():
            (self.feature / name).write_text(text)

    def call(self, action="manifest", mode="read_only", **extra):
        request = dict(schema_version="1.0", helper_id="planning-approval", operation="planning-approval",
                       mode=mode, inputs=dict(feature_dir="specs/demo", workflow_file="specs/demo/workflow.md",
                                              action=action, **extra))
        _, reply, _ = run_runner(request, cwd=self.root, extra_env={"PYTHONPATH": str(self.runner_root)})
        return reply

    def test_progress_preserves_revision_but_planning_changes_do_not(self):
        reply = self.call()
        self.assertEqual(reply["status"], "ok", reply)
        before = reply["data"]["manifest_digest"]
        (self.feature / "tasks.md").write_text("- [x] T001 Build a thing")
        (self.feature / "task-results.json").write_text('{"attempts": 2}')
        self.assertEqual(self.call()["data"]["manifest_digest"], before)
        for name in ("contracts/api.json", "tasks.meta.json", "design.md", "checklists/requirements.md",
                     "research.md", "workflow.md", ".settings"):
            with self.subTest(name=name):
                path = self.feature / name
                path.parent.mkdir(exist_ok=True)
                previous = path.read_bytes() if path.exists() else None
                path.write_text("changed")
                self.assertNotEqual(self.call()["data"]["manifest_digest"], before)
                if previous is None:
                    path.unlink()
                else:
                    path.write_bytes(previous)

    def test_inventory_binds_formal_settings_dispatch_and_task_meaning(self):
        original = self.call()["data"]["manifest_digest"]
        for name, text in ((".specify/quality-gates.json", '{"threshold": 2}'),
                           ("formal/model.tla", "VARIABLE x"),
                           ("specs/demo/.process/task-execution.json", '{"tasks": {"T001": {"depends_on": []}}}'),
                           ("specs/demo/tasks.md", "- [ ] T001 Build another thing")):
            with self.subTest(name=name):
                path = self.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                previous = path.read_bytes() if path.exists() else None
                path.write_text(text)
                if name.startswith("formal/"):
                    (self.root / ".specify/formal-methods.json").write_text(json.dumps(
                        {"models": {"model": {"inputs": [name]}}}))
                    baseline = self.call()["data"]["manifest_digest"]
                    path.write_text("VARIABLE changed")
                else:
                    baseline = original
                self.assertNotEqual(self.call()["data"]["manifest_digest"], baseline)
                if previous is None:
                    path.unlink()
                else:
                    path.write_bytes(previous)
                (self.root / ".specify/formal-methods.json").unlink(missing_ok=True)

    def test_public_spec_and_pr_template_do_not_claim_protected_assurance(self):
        root = Path(__file__).resolve().parents[3]
        for name in ASSURANCE_DOCUMENTS:
            for sentence in re.split(r"[.!?]", (root / name).read_text()):
                if re.search(r"(?i)tamper[- ]?proof", sentence):
                    # Accept only complete, explicit denials. A negation elsewhere
                    # in the document cannot exempt a positive assurance claim.
                    # Markdown soft line breaks stay inside their sentence.
                    self.assertRegex(sentence.strip(),
                                     r"(?i)\A(?:The approval is not|Nothing may describe it as) tamper[- ]?proof\Z",
                                     f"{name}: {sentence}")

    def test_workflow_normalization_preserves_acceptance_requirements(self):
        path = self.feature / "workflow.md"
        path.write_text("## Success Criteria\n- [ ] Contract correct\n")
        before = self.call()["data"]["manifest_digest"]
        path.write_text("## Success Criteria\n- [ ] Contract changed\n")
        self.assertNotEqual(self.call()["data"]["manifest_digest"], before)
        path.write_text("## Success Criteria\n- [x] Contract correct\n")
        self.assertNotEqual(self.call()["data"]["manifest_digest"], before)

    def test_prompt_fences_do_not_hide_planning_inputs(self):
        path = self.feature / "workflow.md"
        path.write_text("```text\n## Implementation Progress\nTest: python3 first.py\n```\n")
        before = self.call()["data"]["manifest_digest"]
        path.write_text("```text\n## Implementation Progress\nTest: python3 other.py\n```\n")
        self.assertNotEqual(self.call()["data"]["manifest_digest"], before)

    def approval(self):
        (self.feature / "planning-findings.json").write_text(json.dumps({"F1": ["Use bounded retries"]}))
        (self.feature / "artifacts").mkdir(exist_ok=True)
        (self.feature / "artifacts/review.txt").write_text("Reviewed corrections and passing check")
        digest = self.call()["data"]["manifest_digest"]
        approval = dict(repository="example/project", planning_run="plan-1", repair_runs=["repair-1"],
                    source_commit="a" * 40, canary_issued=False, supersedes=None,
                    superseded_by=None, withdrawn_by=None,
                    reviewed_evidence=["specs/demo/artifacts/review.txt"],
                    confirmation=dict(reference="specs/demo/artifacts/confirmation.json", manifest_digest=digest,
                                      decision="approve", approver="reviewer", time="2026-10-15T12:00:00Z"),
                    findings={"F1": dict(requests=["Use bounded retries"], correction="Bounded to three",
                                         check=dict(status="passed", manifest_digest=digest,
                                                    reference="specs/demo/artifacts/review.txt"))})
        (self.feature / "artifacts/confirmation.json").write_text(json.dumps(
            {k: v for k, v in approval["confirmation"].items() if k != "reference"}))
        return approval

    def test_record_round_trip_and_refusal_of_incomplete_or_canary_evidence(self):
        approval = self.approval()
        reply = self.call("record", "apply", approval=approval)
        self.assertEqual(reply["status"], "ok", reply)
        record = reply["data"]["record"]
        self.assertEqual(record["assurance"], "recorded")
        self.assertEqual(self.call("verify")["data"]["record"], record)
        path = self.root / reply["data"]["record_path"]
        for field, value, reason in (("findings", {}, "findings must cover exactly"),
                                     ("canary_issued", True, "refuses canary-issued"),
                                     ("withdrawn_by", "withdrawal-1", "refuses canary-issued, superseded or withdrawn")):
            with self.subTest(field=field):
                bad = {**record, field: value}
                path.write_text(json.dumps(bad))
                self.assertRefused(self.call("verify"), reason)
        record["findings"]["F1"]["check"]["status"] = "failed"
        path.write_text(json.dumps(record))
        self.assertRefused(self.call("verify"), "missing correction or passing check")

    def test_dry_run_writes_nothing_and_apply_preserves_the_original_decision(self):
        approval = self.approval()
        dry = self.call("record", "dry_run", approval=approval)
        self.assertEqual(dry["status"], "ok", dry)
        self.assertFalse(dry["data"]["writes_state"])
        path = self.root / dry["data"]["record_path"]
        self.assertFalse(path.exists())
        self.assertEqual(self.call("record", "apply", approval=approval)["status"], "ok")
        original = path.read_bytes()
        self.assertEqual(self.call("record", "apply", approval=approval)["status"], "ok")
        changed = {**approval, "planning_run": "plan-2"}
        self.assertRefused(self.call("record", "apply", approval=changed), "approval already exists")
        self.assertEqual(path.read_bytes(), original)

    def assertRefused(self, reply, reason):
        self.assertEqual(reply["status"], "input_error", reply)
        self.assertIn(reason, reply["diagnostics"][0]["message"])

    def test_new_approval_supersedes_the_previous_revision(self):
        first = self.call("record", "apply", approval=self.approval())["data"]
        confirmation = self.feature / "artifacts/confirmation.json"
        original = confirmation.read_bytes()
        (self.feature / "plan.md").write_text("Revised plan")
        revised = self.approval()
        (self.feature / "artifacts/new-confirmation.json").write_bytes(confirmation.read_bytes())
        confirmation.write_bytes(original)
        revised["confirmation"]["reference"] = "specs/demo/artifacts/new-confirmation.json"
        revised["supersedes"] = first["record_path"]
        self.assertEqual(self.call("record", "apply", approval=revised)["status"], "ok")
        (self.feature / "plan.md").write_text("A plan")
        self.assertRefused(self.call("verify"), "subsequent supersession")


class AssuranceGuardTest(unittest.TestCase):
    def checkAssuranceText(self, text, document=None):
        guard = PlanningApprovalTest("test_public_spec_and_pr_template_do_not_claim_protected_assurance")
        root = Path(__file__).resolve().parents[3]
        with patch.object(Path, "read_text", autospec=True) as read:
            read.side_effect = lambda path: text if document is None or path == root / document else ""
            guard.test_public_spec_and_pr_template_do_not_claim_protected_assurance()

    def assertClaimsRejected(self, texts, documents=(None,)):
        texts = tuple(texts)
        for document in documents:
            for text in texts:
                with self.subTest(document=document, text=text), self.assertRaises(AssertionError):
                    self.checkAssuranceText(text, document)

    def test_positive_claim_rejects_unrelated_following_negation(self):
        self.assertClaimsRejected(
            f"The approval is tamper-proof{separator}{word} further review is needed."
            for word, separator in UNRELATED_NEGATIONS)

    def test_positive_claim_rejects_unrelated_preceding_negation(self):
        self.assertClaimsRejected(
            f"{word} further review is needed{separator}the approval is tamper-proof."
            for word, separator in UNRELATED_NEGATIONS)

    def test_claim_spellings_reject_unrelated_negation(self):
        self.assertClaimsRejected(
            text for term in ("tamperproof", "tamper proof", "TAMPER-PROOF")
            for text in (f"No review needed; the approval is {term}.",
                         f"The approval is {term}. Nothing else is needed."))

    def test_genuine_denials_pass_without_exempting_other_claims(self):
        for term in ("tamper-proof", "tamper proof", "tamperproof"):
            for denial in (f"The approval is not {term}.", f"Nothing may describe it as {term}."):
                with self.subTest(denial=denial):
                    self.checkAssuranceText(denial)
                    self.assertClaimsRejected((denial + f" The approval is {term}.",
                                               f"The approval is {term}. " + denial))

    def test_negated_qualifiers_and_double_negation_do_not_hide_claims(self):
        self.assertClaimsRejected(("The approval is not only tamper-proof but also portable.",
                                   "The approval is not not tamper-proof.",
                                   "Nothing else matters: the approval is tamper-proof.",
                                   "The approval is not tamper-proof and the record is tamperproof."))

    def test_each_public_surface_rejects_a_claim_beside_a_denial(self):
        self.assertClaimsRejected(("The approval is not tamper-proof. The record is tamperproof.",),
                                  documents=ASSURANCE_DOCUMENTS)

    def test_soft_line_breaks_do_not_separate_a_denial_from_its_qualifiers(self):
        self.assertClaimsRejected(("The approval is not tamper-proof\nunless the record is signed.",
                                   "The following statement is false:\nThe approval is not tamper-proof."))


class WorkflowPlanningApprovalTest(PlanningApprovalTest):
    def assertWorkflowEdit(self, before, after, *, preserves=False):
        # Each scenario has independent approval history and confirmation evidence.
        for record in (self.feature / "plan-approvals").glob("*.json"):
            record.unlink()
        # An excluded edit must not hide a planning choice after the excluded region.
        choice = "\n## Security plan\n- [x] Allow external requests\n"
        path = self.feature / "workflow.md"
        path.write_text(before + choice)
        recorded = self.call("record", "apply", approval=self.approval())
        self.assertEqual(recorded["status"], "ok", recorded)
        digest = recorded["data"]["record"]["manifest_digest"]
        self.assertEqual(self.call("verify")["status"], "ok")
        path.write_text(after + choice)
        changed = self.call()["data"]["manifest_digest"]
        verified = self.call("verify")
        if preserves:
            self.assertEqual(changed, digest)
            self.assertEqual(verified["status"], "ok", verified)
            path.write_text(after + choice.replace("[x]", "[ ]"))
            changed = self.call()["data"]["manifest_digest"]
            self.assertNotEqual(changed, digest)
            verified = self.call("verify")
        else:
            self.assertNotEqual(changed, digest)
        self.assertRefused(verified, changed + ".json")

    def test_lowercase_planning_checkbox_state_invalidates_approval(self):
        choices = ("## Security plan\n- [x] Require review\n",
                   "## Success Criteria\n  - [x] Require review\n",
                   "## Project Commands\n- [x] Require review\n")
        for before in choices:
            with self.subTest(workflow=before):
                self.assertWorkflowEdit(before, before.replace("[x]", "[ ]"))
                self.assertWorkflowEdit(before.replace("[x]", "[ ]"), before)

    def test_uppercase_planning_checkbox_state_invalidates_approval(self):
        self.assertWorkflowEdit("## Deployment plan\n- [X] Require review\n",
                                "## Deployment plan\n- [ ] Require review\n")
        self.assertWorkflowEdit("## Deployment plan\n  - [X] Require review\n",
                                "## Deployment plan\n  - [ ] Require review\n")

    def test_checked_marker_case_preserves_approval_but_not_a_choice_flip(self):
        before = "## Deployment plan\n- [x] Require review\n"
        self.assertWorkflowEdit(before, before.replace("[x]", "[X]"), preserves=True)

    def test_execution_rows_preserve_approval_but_not_a_choice_flip(self):
        for field in ("Stage", "Draft PR"):
            with self.subTest(field=field):
                before = f"| **{field}** | pending |\n"
                self.assertWorkflowEdit(before, before.replace("pending", "updated"), preserves=True)

    def test_execution_sections_preserve_approval_but_not_a_choice_flip(self):
        for heading in ("Implementation Progress", "Feedback Sweep Log"):
            with self.subTest(heading=heading):
                before = f"## {heading}\n- [ ] Work\n### Details\nPending\n"
                self.assertWorkflowEdit(before, before.replace("[ ]", "[x]"), preserves=True)

    def test_fenced_checkbox_state_invalidates_approval(self):
        for before in ("```text\n- [x] Require review\n```\n", "~~~text\n- [x] Require review\n~~~\n"):
            self.assertWorkflowEdit(before, before.replace("[x]", "[ ]"))
            self.assertWorkflowEdit(before, before.replace("[x]", "[X]"))
            # Also check that unchanged fenced input does not disable later binding.
            self.assertWorkflowEdit(before, before, preserves=True)

    def test_planning_choice_text_invalidates_approval(self):
        before = "## Security plan\n- [x] Require review\n"
        self.assertWorkflowEdit(before, before.replace("Require review", "Bypass review"))
        self.assertWorkflowEdit(before, before, preserves=True)

    def test_fenced_execution_rows_are_planning_inputs(self):
        self.assertWorkflowEdit("```text\n| **Stage** | Require review |\n```\n",
                                "```text\n| **Stage** | Bypass review |\n```\n")
        self.assertWorkflowEdit("```text\n| **Draft PR** | Require review |\n```\n",
                                "```text\n| **Draft PR** | Bypass review |\n```\n")

    def test_shipped_hosts_bind_every_workflow_variant(self):
        variants = (self.test_lowercase_planning_checkbox_state_invalidates_approval,
                    self.test_uppercase_planning_checkbox_state_invalidates_approval,
                    self.test_checked_marker_case_preserves_approval_but_not_a_choice_flip,
                    self.test_execution_rows_preserve_approval_but_not_a_choice_flip,
                    self.test_execution_sections_preserve_approval_but_not_a_choice_flip,
                    self.test_fenced_checkbox_state_invalidates_approval,
                    self.test_planning_choice_text_invalidates_approval,
                    self.test_fenced_execution_rows_are_planning_inputs)
        for host in ("claude", "codex"):
            self.runner_root = Path(__file__).resolve().parents[3] / "dist" / host / "speckit-pro"
            for check in variants:
                with self.subTest(host=host, variant=check.__name__):
                    check()

if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (WorkflowPlanningApprovalTest, AssuranceGuardTest))
    raise SystemExit(run_counted(suite, label="test-planning-approval"))
