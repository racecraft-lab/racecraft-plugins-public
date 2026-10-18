#!/usr/bin/env python3
"""Implement admission: every implement entry needs a valid plan approval record."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
import unittest

from test_result import run_counted


from script_loader import load_script

PlanningApprovalFixture = load_script("planning_approval_tests", HERE / "test-planning-approval.py").PlanningApprovalFixture
STAGE_WORKFLOW = (HERE / "fixtures/autopilot-stage/workflow.md").read_text()


class AdmissionFixture(PlanningApprovalFixture):
    def setUp(self):
        super().setUp()
        subprocess.run(["git", "-C", str(self.root), "remote", "add", "origin", "https://github.com/example/project.git"], check=True)
        (self.feature / "workflow.md").write_text(STAGE_WORKFLOW)

    def record(self, **changes):
        reply = self.call("record", "apply", approval={**self.approval(), **changes})
        self.assertEqual(reply["status"], "ok", reply)
        return self.root / reply["data"]["record_path"], reply["data"]["record"]

    def refusal(self, reply, field):
        self.assertRefused(reply, f"planning approval field {field}:")


class PlanApprovalAdmissionTest(AdmissionFixture):
    def test_a_valid_record_admits_implement(self):
        _, record = self.record()
        reply = self.call("admit")
        self.assertEqual(reply["status"], "ok", reply)
        self.assertEqual(reply["data"]["admitted"], True)
        self.assertEqual(reply["data"]["manifest_digest"], record["manifest_digest"])

    def test_a_missing_record_names_the_record(self):
        self.refusal(self.call("admit"), "record")

    def test_a_stale_record_names_the_manifest_digest(self):
        self.record()
        (self.feature / "plan.md").write_text("A different plan")
        self.refusal(self.call("admit"), "manifest_digest")

    def test_invalid_record_kinds_name_the_failing_field(self):
        path, record = self.record()
        cases = (("canary_issued", True), ("withdrawn_by", "withdrawal-1"), ("superseded_by", "later.json"))
        for field, value in cases:
            with self.subTest(field=field):
                path.write_text(json.dumps({**record, field: value}))
                self.refusal(self.call("admit"), field)
        path.write_text("{not json")
        self.refusal(self.call("admit"), "record")

    def test_non_object_findings_names_the_record(self):
        path, record = self.record()
        for findings in (None, 5):
            with self.subTest(findings=findings):
                path.write_text(json.dumps({**record, "findings": findings}))
                self.refusal(self.call("admit"), "record")

    def test_a_failed_finding_check_names_the_finding(self):
        path, record = self.record()
        record["findings"]["F1"]["check"]["status"] = "failed"
        path.write_text(json.dumps(record))
        self.refusal(self.call("admit"), "findings.F1")

    def test_a_later_approval_that_supersedes_the_record_names_superseded_by(self):
        first, _ = self.record()
        (self.feature / "plan.md").write_text("Revised plan")
        revised = self.approval()
        revised["supersedes"] = str(first.relative_to(self.root))
        self.assertEqual(self.call("record", "apply", approval=revised)["status"], "ok")
        (self.feature / "plan.md").write_text("A plan")
        self.refusal(self.call("admit"), "superseded_by")


class RepositoryAdmissionTest(AdmissionFixture):
    def test_a_foreign_repository_approval_is_refused_by_name(self):
        self.record(repository="someone-else/unrelated")
        self.refusal(self.call("admit"), "repository")

    def test_changed_repository_identity_is_refused_by_name(self):
        path, record = self.record()
        for repository in ("someone-else/unrelated", None, ""):
            with self.subTest(repository=repository):
                path.write_text(json.dumps({**record, "repository": repository}))
                self.refusal(self.call("admit"), "repository")

    def test_origin_identity_is_required_across_remote_spellings(self):
        self.record()
        for remote in ("https://github.com/example/project", "git@github.com:example/project.git",
                       "ssh://git@github.com/example/project.git"):
            with self.subTest(remote=remote):
                subprocess.run(["git", "-C", str(self.root), "remote", "set-url", "origin", remote], check=True)
                self.assertEqual(self.call("admit")["status"], "ok")
        for remote in ("https://github.com/another/project.git", "https://elsewhere.example/example/project.git"):
            with self.subTest(remote=remote):
                subprocess.run(["git", "-C", str(self.root), "remote", "set-url", "origin", remote], check=True)
                self.refusal(self.call("admit"), "repository")
        subprocess.run(["git", "-C", str(self.root), "remote", "remove", "origin"], check=True)
        self.refusal(self.call("admit"), "repository")


class StageAdmissionTest(AdmissionFixture):
    def resolve(self, *args, feature_dir="specs/demo"):
        return self.helper("resolve-autopilot-stage", autopilot_args=list(args), feature_dir=feature_dir)

    def test_planning_complete_never_selects_implement_on_its_own(self):
        self.record()
        reply = self.resolve()
        self.assertEqual(reply["status"], "ok", reply)
        self.assertEqual(reply["data"]["stdout_json"]["stage"], "plan")

    def test_every_implement_entry_is_admitted_or_refused_by_name(self):
        for args in (("--stage", "implement"), ("--stage", "full"), ("--from-phase", "implement")):
            with self.subTest(args=args):
                reply = self.resolve(*args)
                self.assertNotEqual(reply["status"], "ok", reply)
                self.assertIn("planning approval field record:", json.dumps(reply))
        self.record()
        for args in (("--stage", "implement"), ("--stage", "full"), ("--from-phase", "implement")):
            with self.subTest(args=args, record=True):
                reply = self.resolve(*args)
                self.assertEqual(reply["status"], "ok", reply)
                envelope = reply["data"]["stdout_json"]
                self.assertIn(envelope["stage"], ("implement", "full"))
                self.assertTrue(envelope["planning_approval"]["admitted"])

    def test_resuming_started_implementation_is_admitted_or_refused_too(self):
        (self.feature / "workflow.md").write_text(STAGE_WORKFLOW.replace("| Implement | `/speckit-implement` | ⏳ Pending |", "| Implement | `/speckit-implement` | 🔄 In Progress |"))
        reply = self.resolve()
        self.assertNotEqual(reply["status"], "ok", reply)
        self.assertIn("planning approval field record:", json.dumps(reply))

    def test_a_plan_stage_needs_no_record(self):
        reply = self.resolve("--stage", "plan")
        self.assertEqual(reply["status"], "ok", reply)

    def test_implement_without_a_feature_directory_is_refused(self):
        reply = self.resolve("--stage", "implement", feature_dir=None)
        self.assertNotEqual(reply["status"], "ok", reply)
        self.assertIn("planning approval field feature_dir:", json.dumps(reply))


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (PlanApprovalAdmissionTest, RepositoryAdmissionTest, StageAdmissionTest))
    raise SystemExit(run_counted(suite, label="test-implement-admission"))
