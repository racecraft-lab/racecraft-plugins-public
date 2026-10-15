#!/usr/bin/env python3
"""Planning approval at the portable runner request seam."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from runner_invocation import run_runner
from test_result import run_counted


class PlanningApprovalTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        (self.root / ".specify").mkdir()
        self.feature = self.root / "specs/demo"
        self.feature.mkdir(parents=True)
        for name, text in {"spec.md": "A feature", "plan.md": "A plan",
                           "tasks.md": "- [ ] T001 Build a thing", "workflow.md": "## Project Commands\nTest: python3 check.py\n"}.items():
            (self.feature / name).write_text(text)

    def call(self, action="manifest", mode="read_only", **extra):
        request = dict(schema_version="1.0", helper_id="planning-approval", operation="planning-approval",
                       mode=mode, inputs=dict(feature_dir="specs/demo", workflow_file="specs/demo/workflow.md",
                                              action=action, **extra))
        _, reply, _ = run_runner(request, cwd=self.root)
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
        for name in ("docs/adr/0013-plan-approval-record.md", "docs/adr/0017-recorded-plan-approval.md",
                     ".github/pull_request_template.md", "GLOSSARY.md", "speckit-pro/skills/speckit-autopilot/SKILL.md",
                     "speckit-pro/skills/speckit-autopilot/references/planning-approval.md"):
            text = (root / name).read_text()
            self.assertNotRegex(text, r"(?i)\b(?:is|provides|ensures|guarantees)\s+(?:a\s+)?tamper[- ]?proof\b")

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
        self.assertEqual(self.call("verify")["status"], "input_error")


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(PlanningApprovalTest), label="test-planning-approval"))
