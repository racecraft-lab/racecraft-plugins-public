#!/usr/bin/env python3
"""The plan-review repair prompt at the portable runner request seam, on source and both host payloads."""
import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from runner_invocation import run_runner
from test_result import run_counted

REPO = Path(__file__).resolve().parents[3]
PAYLOADS = {"source": REPO / "speckit-pro", "claude": REPO / "dist/claude/speckit-pro",
            "codex": REPO / "dist/codex/speckit-pro"}

FINDINGS = [
    {"id": "F1", "summary": "Resume clears blocked tasks."},
    {"id": "F2", "summary": "Two documents list unfinished tasks separately."},
]
REQUESTS = [
    {"id": "R1", "finding": "F1", "kind": "recommended", "instruction": "Keep history and prepare a linked repair draft."},
    {"id": "R2", "finding": "F2", "kind": "custom", "instruction": "Feed both documents one shared task list."},
]


class PlanReviewPromptTest(unittest.TestCase):
    runner_root = PAYLOADS["source"]

    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True, capture_output=True)
        (self.root / ".specify").mkdir()
        feature = self.root / "specs/demo"
        feature.mkdir(parents=True)
        for name, text in {"spec.md": "A feature", "plan.md": "A plan",
                           "tasks.md": "- [ ] T001 Build a thing", "workflow.md": "## Project Commands\n"}.items():
            (feature / name).write_text(text)

    def call(self, **extra):
        manifest_request = dict(schema_version="1.0", helper_id="planning-approval", operation="planning-approval",
                                mode="read_only", inputs=dict(action="manifest", feature_dir="specs/demo",
                                                              workflow_file="specs/demo/workflow.md"))
        _, manifest, _ = run_runner(manifest_request, cwd=self.root, extra_env={"PYTHONPATH": str(self.runner_root)})
        inputs = dict(feature_dir="specs/demo", workflow_file="specs/demo/workflow.md", findings=copy.deepcopy(FINDINGS),
                      reviewed_revision=manifest["data"]["manifest_digest"], requests=copy.deepcopy(REQUESTS), withdrawals=[])
        inputs.update(extra)
        request = dict(schema_version="1.0", helper_id="plan-review-prompt", operation="plan-review-prompt",
                       mode="read_only", inputs=inputs)
        _, reply, _ = run_runner(request, cwd=self.root, extra_env={"PYTHONPATH": str(self.runner_root)})
        return reply

    def assertRefused(self, reply, reason):
        self.assertEqual(reply["status"], "input_error", reply)
        self.assertIn(reason, reply["diagnostics"][0]["message"])

    def test_prompt_carries_every_finding_and_its_remedy(self):
        reply = self.call()
        self.assertEqual(reply["status"], "ok", reply)
        prompt = reply["data"]["prompt"]
        for finding in FINDINGS:
            self.assertIn(finding["id"], prompt)
            self.assertIn(finding["summary"], prompt)
        for request in REQUESTS:
            self.assertIn(request["instruction"], prompt)
        self.assertIn(self.call()["data"]["revision"], prompt)
        self.assertEqual([entry["request"] for entry in reply["data"]["active"]], ["R1", "R2"])

    def test_prompt_sends_nothing_and_starts_no_work(self):
        data = self.call()["data"]
        self.assertEqual({flag: data[flag] for flag in ("writes_state", "sends", "starts_work")},
                         dict.fromkeys(("writes_state", "sends", "starts_work"), False))
        for promise in ("Do not start implementation", "blocked entries"):
            self.assertIn(promise, data["prompt"])

    def test_every_finding_needs_a_request_and_no_unknown_finding_is_accepted(self):
        self.assertRefused(self.call(requests=REQUESTS[:1]), "F2")
        stray = [*REQUESTS, {"id": "R3", "finding": "F9", "kind": "custom", "instruction": "Extra."}]
        self.assertRefused(self.call(requests=stray), "F9")

    def test_requests_are_strict(self):
        for change in ({"kind": "approve"}, {"instruction": "  "}, {"id": "R1"}, {"extra": 1}):
            with self.subTest(change=change):
                requests = copy.deepcopy(REQUESTS)
                requests[1].update(change)
                self.assertEqual(self.call(requests=requests)["status"], "input_error")
        duplicated = [*REQUESTS, {**REQUESTS[0]}]
        self.assertRefused(self.call(requests=duplicated), "duplicate")

    def test_withdrawal_keeps_history_and_leaves_the_instruction_out_of_the_active_queue(self):
        replacement = {"id": "R3", "finding": "F2", "kind": "alternative", "instruction": "Generate one immutable report."}
        withdrawal = {"request": "R2", "finding": "F2", "instruction": REQUESTS[1]["instruction"]}
        reply = self.call(requests=[*REQUESTS, replacement], withdrawals=[withdrawal])
        self.assertEqual(reply["status"], "ok", reply)
        data = reply["data"]
        self.assertEqual({entry["request"]: entry["disposition"] for entry in data["history"]},
                         {"R1": "active", "R2": "withdrawn", "R3": "active"})
        self.assertEqual([entry["request"] for entry in data["active"]], ["R1", "R3"])
        self.assertIn(REQUESTS[1]["instruction"], data["prompt"])
        self.assertIn("Withdrawn", data["prompt"])
        self.assertIn("F2", [entry["finding"] for entry in data["required_findings"]])

    def test_withdrawal_needs_the_exact_request_finding_and_text(self):
        wrong = {"request": "R2", "finding": "F2", "instruction": "feed both documents one shared task list."}
        self.assertRefused(self.call(withdrawals=[wrong]), "exact text")
        self.assertRefused(self.call(withdrawals=[{**wrong, "instruction": REQUESTS[1]["instruction"], "finding": "F1"}]), "R2")
        self.assertRefused(self.call(withdrawals=[{"request": "R9", "finding": "F2", "instruction": "x"}]), "R9")
        builtin = {"request": "R1", "finding": "F1", "instruction": REQUESTS[0]["instruction"]}
        self.assertRefused(self.call(withdrawals=[builtin]), "custom")

    def test_withdrawing_the_only_request_requires_a_replacement(self):
        withdrawal = {"request": "R2", "finding": "F2", "instruction": REQUESTS[1]["instruction"]}
        self.assertRefused(self.call(withdrawals=[withdrawal]), "replacement")

    def test_withdrawing_twice_is_refused(self):
        replacement = {"id": "R3", "finding": "F2", "kind": "recommended", "instruction": "Use the shared list."}
        withdrawal = {"request": "R2", "finding": "F2", "instruction": REQUESTS[1]["instruction"]}
        self.assertRefused(self.call(requests=[*REQUESTS, replacement], withdrawals=[withdrawal, withdrawal]), "twice")

    def test_a_clean_plan_has_nothing_to_repair(self):
        self.assertRefused(self.call(findings=[], requests=[]), "no findings")

    def test_prompt_refuses_a_revision_changed_during_the_interview(self):
        before = self.call()["data"]["revision"]
        (self.root / "specs/demo/plan.md").write_text("A changed plan")
        self.assertRefused(self.call(reviewed_revision=before), "reviewed revision changed")


class HostPayloadTest(unittest.TestCase):
    def test_both_host_payloads_answer_the_same_request(self):
        for host in ("claude", "codex"):
            for name in ("test_prompt_carries_every_finding_and_its_remedy",
                         "test_withdrawal_keeps_history_and_leaves_the_instruction_out_of_the_active_queue",
                         "test_prompt_refuses_a_revision_changed_during_the_interview"):
                with self.subTest(host=host, check=name):
                    case = PlanReviewPromptTest(name)
                    case.runner_root = PAYLOADS[host]
                    result = unittest.TestResult()
                    case.run(result)
                    self.assertTrue(result.wasSuccessful(), result.errors + result.failures)


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (PlanReviewPromptTest, HostPayloadTest))
    raise SystemExit(run_counted(suite, label="test-plan-review-prompt"))
