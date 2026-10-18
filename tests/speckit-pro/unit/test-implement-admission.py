#!/usr/bin/env python3
"""Implement admission: every implement entry needs a valid plan approval record."""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
import unittest

from runner_invocation import run_runner
from test_result import run_counted


def load_fixture():
    spec = importlib.util.spec_from_file_location("planning_approval_tests", HERE / "test-planning-approval.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PlanningApprovalFixture


PlanningApprovalFixture = load_fixture()
STAGE_WORKFLOW = (HERE / "fixtures/autopilot-stage/workflow.md").read_text()


class AdmissionFixture(PlanningApprovalFixture):
    def setUp(self):
        super().setUp()
        (self.feature / "workflow.md").write_text(STAGE_WORKFLOW)

    def record(self):
        reply = self.call("record", "apply", approval=self.approval())
        self.assertEqual(reply["status"], "ok", reply)
        return self.root / reply["data"]["record_path"], reply["data"]["record"]

    def refusal(self, reply, field):
        self.assertEqual(reply["status"], "input_error", reply)
        self.assertIn(f"planning approval field {field}:", reply["diagnostics"][0]["message"])


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


class StageAdmissionTest(AdmissionFixture):
    def resolve(self, *args):
        request = dict(schema_version="1.0", helper_id="resolve-autopilot-stage", operation="resolve-autopilot-stage",
                       mode="read_only", inputs=dict(workflow_file="specs/demo/workflow.md", feature_dir="specs/demo",
                                                     autopilot_args=list(args)))
        _, reply, _ = run_runner(request, cwd=self.root, extra_env={"PYTHONPATH": str(self.runner_root)})
        return reply

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

    def test_a_plan_stage_needs_no_record(self):
        reply = self.resolve("--stage", "plan")
        self.assertEqual(reply["status"], "ok", reply)

    def test_implement_without_a_feature_directory_is_refused(self):
        request = dict(schema_version="1.0", helper_id="resolve-autopilot-stage", operation="resolve-autopilot-stage",
                       mode="read_only", inputs=dict(workflow_file="specs/demo/workflow.md",
                                                     autopilot_args=["--stage", "implement"]))
        _, reply, _ = run_runner(request, cwd=self.root, extra_env={"PYTHONPATH": str(self.runner_root)})
        self.assertNotEqual(reply["status"], "ok", reply)
        self.assertIn("feature_dir", json.dumps(reply))


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (PlanApprovalAdmissionTest, StageAdmissionTest))
    raise SystemExit(run_counted(suite, label="test-implement-admission"))
