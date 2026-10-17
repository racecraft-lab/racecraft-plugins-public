#!/usr/bin/env python3
"""Planning approval at the portable runner request seam."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from runner_invocation import run_runner
from test_result import run_counted

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "speckit-pro"))
from speckit_pro_runner.formal.evidence import write_checkpoint
from speckit_pro_runner.helpers import planning_approval as approval_owner
from speckit_pro_runner.helpers.read_only import render_spec_index
from speckit_pro_runner.workflow_stage import AUTOPILOT_STATUS_VALUES


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


class PlanningApprovalFixture(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True, capture_output=True)
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

    def assertRefused(self, reply, reason):
        self.assertEqual(reply["status"], "input_error", reply)
        self.assertIn(reason, reply["diagnostics"][0]["message"])



class PlanningApprovalTest(PlanningApprovalFixture):
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
                # Any non-word joint, including a wrapped line or a Unicode dash, spells the term.
                if re.search(r"(?i)tamper[\W_]*proof", sentence):
                    # Accept only complete, explicit denials. A negation elsewhere
                    # in the document cannot exempt a positive assurance claim.
                    # Markdown soft line breaks stay inside their sentence.
                    self.assertRegex(" ".join(sentence.split()),
                                     r"(?i)\A(?:The approval is not|Nothing may describe it as) tamper[\W_]*proof\Z",
                                     f"{name}: {sentence}")



class PlanningMeaningTest(PlanningApprovalFixture):
    def test_workflow_normalization_preserves_acceptance_requirements(self):
        path = self.feature / "workflow.md"
        path.write_text("## Success Criteria\n- [ ] Contract correct\n")
        before = self.call()["data"]["manifest_digest"]
        path.write_text("## Success Criteria\n- [ ] Contract changed\n")
        self.assertNotEqual(self.call()["data"]["manifest_digest"], before)
        path.write_text("## Success Criteria\n- [x] Contract correct\n")
        self.assertEqual(self.call()["data"]["manifest_digest"], before)

    def test_prompt_fences_do_not_hide_planning_inputs(self):
        path = self.feature / "workflow.md"
        path.write_text("```text\n## Implementation Progress\nTest: python3 first.py\n```\n")
        before = self.call()["data"]["manifest_digest"]
        path.write_text("```text\n## Implementation Progress\nTest: python3 other.py\n```\n")
        self.assertNotEqual(self.call()["data"]["manifest_digest"], before)



class RecordedApprovalTest(PlanningApprovalFixture):
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

    def test_wrapped_and_unusual_term_spellings_are_still_claims(self):
        joints = "\n", "-\n", "  ", " - ", "‐", "‑", "–", " "
        self.assertClaimsRejected(map("The approval is tamper{}proof.".format, joints))
        # A genuine denial wrapped across lines stays a denial.
        self.checkAssuranceText("The approval is not\ntamper-proof.")



class WorkflowFixture(PlanningApprovalFixture):
    def assertWorkflowEdit(self, before, after, preserves=False, name="workflow.md"):
        # Each scenario has independent approval history and confirmation evidence.
        for record in (self.feature / "plan-approvals").glob("*.json"):
            record.unlink()
        # An excluded edit must not hide a planning choice after the excluded region.
        choice = "\n## Security plan\n- [x] Allow external requests\n"
        path = self.feature / name
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

    def template(self, name="workflow-template.md"):
        return (self.runner_root / "skills/speckit-coach/templates" / name).read_text()

    def assertTemplateEdit(self, old, new, *, preserves=False):
        before = self.template()
        self.assertEqual(before.count(old), 1)
        self.assertWorkflowEdit(before, before.replace(old, new), preserves=preserves)



class WorkflowPlanningApprovalTest(WorkflowFixture):
    def test_lowercase_planning_checkbox_state_invalidates_approval(self):
        choices = ("## Security plan\n- [x] Require review\n",
                   "## Security checklist\n  - [x] Require review\n",
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
        self.assertWorkflowEdit("## Deployment plan\n- [x] Require review\n",
                                "## Deployment plan\n- [X] Require review\n", preserves=True)

    def test_execution_rows_preserve_approval_but_not_a_choice_flip(self):
        rows = (("## Basic Information\n| **Stage** | plan |\n", "plan", "implement"),
                ("## Basic Information\n| **Draft PR** | [#42](https://github.com/org/repo/pull/42) |\n", "42", "43"))
        sections = (("## Implementation Progress\n- [ ] Work\n", "[ ]", "[x]"),)
        for before, old, new in (*rows, *sections):
            with self.subTest(workflow=before):
                self.assertWorkflowEdit(before, before.replace(old, new), preserves=True)

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



class DeclaredProgressTest(WorkflowFixture):
    def test_overview_status_preserves_approval(self):
        self.assertTemplateEdit("| Implement | `/speckit-implement` | ⏳ Pending |",
                                "| Implement | `/speckit-implement` | 🔄 In Progress |", preserves=True)

    def test_post_checklist_status_preserves_approval(self):
        self.assertTemplateEdit("| Post: Code Review | ⏳ Pending |",
                                "| Post: Code Review | ✅ Complete |", preserves=True)

    def test_formal_checkpoint_result_preserves_approval(self):
        write_checkpoint(self.root, "specs/demo/workflow.md", "final", {"verdict": "passed"})
        self.assertTemplateEdit("| Final model and optional trace checks | disabled |",
                                "| Final model and optional trace checks | passed |", preserves=True)

    def test_lesson_bullet_preserves_approval(self):
        self.assertTemplateEdit("### What Worked Well\n\n-\n",
                                "### What Worked Well\n\n-\n- Progress: lessons; evidence=specs/demo/.process/lessons.json\n", preserves=True)

    def test_spec_map_status_preserves_approval(self):
        before = self.template("spec-moc-template.md")
        self.assertEqual(before.count('status: ""'), 1)
        self.assertWorkflowEdit(before, before.replace('status: ""', 'status: in_progress'),
                                preserves=True, name="SPEC-MOC.md")

    def test_new_sweep_log_separator_preserves_approval(self):
        before = self.template()
        path = self.feature / "workflow.md"
        path.write_text(before)
        recorded = self.call("record", "apply", approval=self.approval())
        self.assertEqual(recorded["status"], "ok", recorded)
        path.write_text(before + "\n## Feedback Sweep Log\n\n| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |\n")
        self.assertEqual(self.call()["data"]["manifest_digest"], recorded["data"]["record"]["manifest_digest"])
        self.assertEqual(self.call("verify")["status"], "ok")

    def test_formal_writer_results_preserve_approval(self):
        path = self.feature / "workflow.md"
        path.write_text(self.template())
        recorded = self.call("record", "apply", approval=self.approval())
        self.assertEqual(recorded["status"], "ok", recorded)
        digest = recorded["data"]["record"]["manifest_digest"]
        for checkpoint in ("final", "post"):
            for verdict in ("running", "pass", "stale", "waived", "inconclusive", "invalid_model", "trace_violation"):
                with self.subTest(checkpoint=checkpoint, verdict=verdict):
                    # Exercise the public row writer, without claiming a model check ran.
                    write_checkpoint(self.root, "specs/demo/workflow.md", checkpoint, {"verdict": verdict})
                    self.assertEqual(self.call()["data"]["manifest_digest"], digest)
                    self.assertEqual(self.call("verify")["status"], "ok")
        path.write_text(path.read_text().replace('"rationale":', '"changed_rationale":'))
        self.assertNotEqual(self.call()["data"]["manifest_digest"], digest)
        self.assertEqual(self.call("verify")["status"], "input_error")



class PlanningNeighborsTest(WorkflowFixture):
    def test_overview_command_remains_bound(self):
        self.assertTemplateEdit("| Implement | `/speckit-implement` |",
                                "| Implement | `/different-command` |")

    def test_post_checklist_requirement_remains_bound(self):
        self.assertTemplateEdit("| Post: Code Review |", "| Post: Skip Code Review |")

    def test_formal_checkpoint_definition_remains_bound(self):
        self.assertTemplateEdit("| Final model and optional trace checks |",
                                "| Optional final model checks |")

    def test_lesson_neighbor_planning_text_remains_bound(self):
        self.assertTemplateEdit("<!-- Populate with your project's directory structure for quick reference during implementation -->",
                                "The implementation must use a different directory layout.")

    def test_spec_map_metadata_remains_bound(self):
        before = self.template("spec-moc-template.md")
        self.assertWorkflowEdit(before, before.replace("related: []", 'related: ["contract.md"]'),
                                name="SPEC-MOC.md")

    def test_sweep_neighbor_planning_text_remains_bound(self):
        before = self.template() + "\n## Feedback Sweep Log\n\n| Comment | Result |\n"
        self.assertWorkflowEdit(before, before.replace("project/", "different-project/"))

    def test_progress_lookalikes_do_not_hide_planning(self):
        cases = (
            ("## Workflow Overview\n| Implement | `/speckit-implement` | ⏳ Pending | Require review |\n",
             "Require review", "Skip review"),
            ("## Post-Implementation Checklist\n| Post: Code Review | ⏳ Pending | Required evidence |\n",
             "Required evidence", "Optional evidence"),
            ("## Formal Checkpoints\n| Final model and optional trace checks | disabled | Required model |\n",
             "Required model", "Optional model"),
            ("## Lessons Learned\nPlanning prose requires review.\n", "requires", "skips"),
            ("## Lessons Learned\n### Security plan\n- [x] Require review\n", "[x]", "[ ]"),
            ("## Lessons Learned\n### What Worked Well\n```text\n- Require review\n```\n", "Require", "Skip"),
            ("## Security plan\n| Implement | `/speckit-implement` | ⏳ Pending | |\n", "⏳ Pending", "✅ Complete"),
            ("## Workflow Overview\n```text\n| Implement | `/speckit-implement` | ⏳ Pending | |\n```\n",
             "⏳ Pending", "✅ Complete"),
        )
        for before, old, new in cases:
            with self.subTest(before=before):
                self.assertWorkflowEdit(before, before.replace(old, new))
        before = '---\nstatus: pending\n---\nstatus: Require review\n'
        self.assertWorkflowEdit(before, before.replace("Require review", "Skip review"), name="SPEC-MOC.md")


class InventoryProgressTest(PlanningApprovalFixture):
    def test_spec_map_writer_progress_preserves_approval_but_edited_navigation_does_not(self):
        path = self.feature / "SPEC-MOC.md"
        path.write_text("---\nstructureVersion: 1\nstatus: pending\n---\n# Map\n")
        rendered, _ = render_spec_index(self.root)
        self.assertEqual(len(rendered), 1)
        path.write_text(rendered[0].rendered)
        before = approval_owner.planning_manifest(self.root, "specs/demo", "specs/demo/workflow.md")
        process = self.feature / ".process"
        process.mkdir()
        (process / "prs.json").write_text(json.dumps({"schemaVersion": 2, "records": [{
            "review_order": 1, "slice_id": "us1", "pr_number": 42, "status": "open",
            "branch": "feature/demo", "base_branch": "main", "head_sha": "a" * 40,
            "declared_files": ["src/demo.py"], "verification_evidence": "specs/demo/.process/result.json"}]}))
        rendered, _ = render_spec_index(self.root)
        path.write_text(rendered[0].rendered)
        self.assertNotEqual(rendered[0].original, rendered[0].rendered)
        self.assertEqual(approval_owner.planning_manifest(self.root, "specs/demo", "specs/demo/workflow.md"), before)
        for text in ("PR#42", "[spec.md]"):
            with self.subTest(text=text):
                self.assertIn(text, rendered[0].rendered)
                path.write_text(rendered[0].rendered.replace(text, "Bypass authentication"))
                self.assertNotEqual(approval_owner.planning_manifest(self.root, "specs/demo", "specs/demo/workflow.md"), before)

    def test_every_declared_write_preserves_the_revision(self):
        cases = json.loads((Path(__file__).parent / "fixtures/planning-progress.json").read_text())
        for case in cases:
            with self.subTest(region=case["region"], before=case["before"]):
                self.assertNotEqual(case["before"], case["after"])
                path = self.feature / case["file"]
                path.write_text(case["before"])
                before = approval_owner.planning_manifest(self.root, "specs/demo", "specs/demo/workflow.md")
                path.write_text(case["after"])
                self.assertEqual(approval_owner.planning_manifest(self.root, "specs/demo", "specs/demo/workflow.md"), before)

    def test_planning_text_inside_every_progress_region_remains_bound(self):
        cases = json.loads((Path(__file__).parent / "fixtures/planning-progress.json").read_text())
        for case in cases:
            with self.subTest(region=case["region"], after=case["after"]):
                self.assertNotEqual(case["after"], case["planning"])
                path = self.feature / case["file"]
                path.write_text(case["after"])
                before = approval_owner.planning_manifest(self.root, "specs/demo", "specs/demo/workflow.md")
                path.write_text(case["planning"])
                self.assertNotEqual(approval_owner.planning_manifest(self.root, "specs/demo", "specs/demo/workflow.md"), before)

    def test_reader_status_vocabulary_preserves_the_revision(self):
        path = self.feature / "workflow.md"
        template = "## Workflow Overview\n| Implement | `/speckit-implement` | %s | |\n"
        path.write_text(template % "Pending")
        before = approval_owner.planning_manifest(self.root, "specs/demo", "specs/demo/workflow.md")
        for status in AUTOPILOT_STATUS_VALUES:
            with self.subTest(status=status):
                path.write_text(template % status)
                self.assertEqual(approval_owner.planning_manifest(self.root, "specs/demo", "specs/demo/workflow.md"), before)

    def test_outbound_disposition_examples_preserve_the_revision(self):
        root = Path(__file__).resolve().parents[3]
        phase = (root / "speckit-pro/skills/speckit-autopilot/references/phase-execution.md").read_text()
        examples = re.search(r"Use these exact Feedback Sweep Log dispositions:\n\n```text\n(.*?)\n```", phase, re.DOTALL)
        self.assertIsNotNone(examples)
        self.assertTrue(examples[1].strip())
        path = self.feature / "workflow.md"
        heading = "## Feedback Sweep Log\n"
        path.write_text(heading)
        before = approval_owner.planning_manifest(self.root, "specs/demo", "specs/demo/workflow.md")
        for example in examples[1].splitlines():
            kind, separator, disposition = example.partition(": ")
            with self.subTest(disposition=kind):
                self.assertTrue(separator)
                disposition = disposition.replace("<artifact>", "spec.md")
                row = f"| 1 | IC_example | conversation | octocat | {kind} | {disposition} | a1b2c3d | |\n"
                path.write_text(heading + row)
                self.assertEqual(approval_owner.planning_manifest(self.root, "specs/demo", "specs/demo/workflow.md"), before)
                path.write_text(heading + row.replace(disposition, disposition + " Bypass review."))
                self.assertNotEqual(approval_owner.planning_manifest(self.root, "specs/demo", "specs/demo/workflow.md"), before)

    def test_protocol_implement_writes_are_owned_in_code_and_exercised(self):
        root = Path(__file__).resolve().parents[3]
        protocol = (root / "speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md").read_text()
        # Every Implement row is checked, including an added row at any position.
        writes = set(re.findall(r"^\| Implement \| `([^`]+)` \|", protocol, re.MULTILINE))
        self.assertTrue(writes, "protocol must enumerate the post-approval write contract")
        self.assertEqual(len(writes), len(re.findall(r"^\| Implement \|", protocol, re.MULTILINE)))
        self.assertEqual(re.findall(r"^\| \*\*Implement\*\* \|.*$", protocol, re.MULTILINE),
                         ["| **Implement** | Every write is listed in the Implement write contract below. |"])
        owned = set(getattr(approval_owner, "PROGRESS_WRITES", {}))
        cases = json.loads((Path(__file__).parent / "fixtures/planning-progress.json").read_text())
        self.assertEqual(writes, owned)
        self.assertEqual(writes, {case["region"] for case in cases})



class ShippedWorkflowTest(WorkflowFixture):
    def test_shipped_hosts_apply_the_progress_contract(self):
        cases = json.loads((Path(__file__).parent / "fixtures/planning-progress.json").read_text())
        for host in ("claude", "codex"):
            self.runner_root = Path(__file__).resolve().parents[3] / "dist" / host / "speckit-pro"
            for case in cases:
                with self.subTest(host=host, region=case["region"]):
                    path = self.feature / case["file"]
                    path.write_text(case["before"])
                    before = self.call()["data"]["manifest_digest"]
                    path.write_text(case["after"])
                    self.assertEqual(self.call()["data"]["manifest_digest"], before)
                    path.write_text(case["planning"])
                    self.assertNotEqual(self.call()["data"]["manifest_digest"], before)

    def test_shipped_hosts_bind_every_workflow_variant(self):
        for host in ("claude", "codex"):
            self.runner_root = Path(__file__).resolve().parents[3] / "dist" / host / "speckit-pro"
            for case in (WorkflowPlanningApprovalTest, DeclaredProgressTest, PlanningNeighborsTest):
                for name in unittest.defaultTestLoader.getTestCaseNames(case):
                    with self.subTest(host=host, variant=name):
                        getattr(case, name)(self)


if __name__ == "__main__":
    cases = (PlanningApprovalTest, PlanningMeaningTest, RecordedApprovalTest, AssuranceGuardTest,
             WorkflowPlanningApprovalTest, DeclaredProgressTest, PlanningNeighborsTest, InventoryProgressTest,
             ShippedWorkflowTest)
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in cases)
    raise SystemExit(run_counted(suite, label="test-planning-approval"))
