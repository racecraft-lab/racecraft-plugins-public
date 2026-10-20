#!/usr/bin/env python3
"""Canary-issued plan approval: refused by production verifiers, accepted only in a canary-marked home."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from script_loader import load_script
from test_result import run_counted

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LAYER6 = REPO / "tests/speckit-pro/layer6-integration"
sys.path.insert(0, str(LAYER6))
sys.path.insert(0, str(REPO / "speckit-pro"))
from speckit_pro_runner.canary_trust import MARKER_NAME
PlanningApprovalFixture = load_script("planning_approval_tests", HERE / "test-planning-approval.py").PlanningApprovalFixture
issuer = load_script("issue_canary_plan_approval", LAYER6 / "issue-canary-plan-approval.py")
STAGE_WORKFLOW = (HERE / "fixtures/autopilot-stage/workflow.md").read_text()


class CanaryApprovalFixture(PlanningApprovalFixture):
    def setUp(self):
        super().setUp()
        (self.feature / "workflow.md").write_text(STAGE_WORKFLOW)
        (self.feature / "planning-findings.json").write_text(json.dumps({"F1": ["Use bounded retries"]}))
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.enterContext(patch.dict(os.environ, {"HOME": str(self.home)}))

    def issue(self):
        inputs = {"feature_dir": self.feature_dir, "workflow_file": self.workflow_file}
        # The issuer launches its own runner child; use the same private Git PATH as helper calls.
        with patch.dict(os.environ, self.runner_environment()):
            return issuer.issue(self.root, self.home, inputs, "example/project", "a" * 40)

    def mark(self):
        (self.home / MARKER_NAME).write_text("canary-home/v1\n")

    def issue_marked(self):
        self.mark()
        return self.issue()


class CanaryTrustTest(CanaryApprovalFixture):
    def test_the_issuer_uses_the_fixture_git_path(self):
        ambient_bin = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        (ambient_bin / "git").symlink_to(self.git_directory / "git")
        (ambient_bin / "checkout-entry").symlink_to(self.feature / "spec.md")
        with patch.dict(os.environ, {"PATH": str(ambient_bin)}):
            self.issue_marked()
        self.assertEqual(self.call("admit")["status"], "ok")

    def test_the_canary_verifier_in_a_marked_home_accepts_the_issued_record(self):
        path = self.issue_marked()
        record = json.loads((self.root / path).read_text())
        self.assertIs(record["canary_issued"], True)
        self.assertEqual(record["assurance"], "recorded")
        self.assertEqual(self.call("verify")["status"], "ok")
        reply = self.call("admit")
        self.assertEqual(reply["status"], "ok", reply)

    def test_a_production_verifier_refuses_the_canary_issued_record(self):
        path = self.issue_marked()
        (self.home / MARKER_NAME).unlink()
        for action, reason in (("verify", "refuses canary-issued"), ("admit", "canary_issued")):
            with self.subTest(action=action):
                self.assertRefused(self.call(action), reason)
        self.assertTrue((self.root / path).is_file())

    def test_only_the_exact_marker_is_trust(self):
        self.issue_marked()
        for text in ("anything else\n", "", "canary-home/v1"):
            with self.subTest(marker=text):
                (self.home / MARKER_NAME).write_text(text)
                self.assertRefused(self.call("admit"), "canary_issued")

    def test_an_unmarked_home_cannot_record_a_canary_issued_approval(self):
        with self.assertRaises(SystemExit) as refusal:
            self.issue()
        self.assertIn("refuses canary-issued", str(refusal.exception))
        self.assertEqual(list(self.feature.glob("plan-approvals/*.json")), [])

    def test_a_marked_home_still_refuses_withdrawn_and_superseded_records(self):
        path = self.issue_marked()
        record = json.loads((self.root / path).read_text())
        for field, value in (("withdrawn_by", "withdrawal-1"), ("superseded_by", "later.json")):
            with self.subTest(field=field):
                (self.root / path).write_text(json.dumps({**record, field: value}))
                self.assertNotEqual(self.call("admit")["status"], "ok")

    def test_the_scripted_review_path_reaches_implement(self):
        self.issue_marked()
        for args in (("--stage", "implement"), ("--stage", "full"), ("--from-phase", "implement")):
            with self.subTest(args=args):
                reply = self.helper("resolve-autopilot-stage", autopilot_args=list(args), feature_dir=self.feature_dir)
                self.assertEqual(reply["status"], "ok", reply)


class IssuerReachTest(unittest.TestCase):
    ISSUER_NAMES = ("issue-canary-plan-approval", "scripted_plan_reviewer", "scripted-plan-reviewer")

    def shipped(self):
        for root in (REPO / "speckit-pro", REPO / "dist"):
            yield from (path for path in root.rglob("*") if path.is_file() and path.suffix in {".py", ".md", ".json", ".toml", ".yaml", ".yml"})

    def test_no_default_install_carries_or_names_the_issuer(self):
        offenders = [str(path.relative_to(REPO)) for path in self.shipped()
                     if any(name in path.name or name in path.read_text(encoding="utf-8", errors="replace")
                            for name in self.ISSUER_NAMES)]
        self.assertEqual(offenders, [])

    def test_the_issuer_is_not_a_runner_helper(self):
        from speckit_pro_runner.helpers.registry import HELPERS
        self.assertFalse([helper for helper in HELPERS if "canary" in str(helper)])


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (CanaryTrustTest, IssuerReachTest))
    raise SystemExit(run_counted(suite, label="test-canary-plan-approval"))
