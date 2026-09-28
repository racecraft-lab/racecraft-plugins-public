#!/usr/bin/env python3
"""How an autopilot run ends once no runnable work remains (issue 804).

Human UAT is the only gate a run may defer. A run whose non-UAT gates all
passed and that holds no unresolved deferral is done: its pull-request stack
goes ready for review (never merged), the top PR body opens with a
"Deferred / not verified" section listing the human UAT, the goal is marked
complete, and one plain-text request names what is left. A failed gate, a
ledger deferral, or an unresolved deferred task at the end is one human stop
that names the gate and its exact command, never ready for review. The
`finalize-run` helper derives that decision and fails closed.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
for entry in (PLUGIN_ROOT, REPO_ROOT / "tests" / "speckit-pro" / "lib"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from test_result import run_counted  # noqa: E402

from speckit_pro_runner.execution_control import execution_control  # noqa: E402

HELPER_ID = "finalize-run"
FIXTURE_REQUEST = (
    REPO_ROOT / "tests/speckit-pro/unit/fixtures/read-only-helpers/requests" / f"{HELPER_ID}.json"
)
RESUME = "/speckit-pro:speckit-autopilot docs/ai/specs/.process/FEATURE-001-workflow.md --from-phase implement"
UAT = {
    "item": "UAT story 2: the export opens in a spreadsheet app",
    "reason": "It needs a person to open the exported file.",
    "finish": "Follow steps 4 to 6 of the UAT runbook and record the result on the pull request.",
}
VETO = {
    "unit": "T042",
    "reason": "The approval reviewer denied the live evaluation twice despite the recorded chat authorization.",
    "finish": "python3 tests/live/run-eval.py --task T042",
}
LIVE_EVAL = {"gate": "Post: Live Evaluation", "status": "failed",
             "command": "python3 tests/live/run-eval.py --task T042"}


def finalize(root: Path, inputs: dict[str, object]) -> dict[str, object]:
    from speckit_pro_runner.helpers.run_finalization import finalize_run

    return finalize_run(root, inputs)


class _LedgerFixture:
    """A temporary repository with a clean ledger and one holding a deferral."""

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.clean = self.start("clean")
        self.deferring = self.start("feature")
        self.invoke(self.deferring, "reserve", dispatch_id="fix-a", kind="corrective", failure_invariant="FR-001")
        self.invoke(self.deferring, "complete", dispatch_id="fix-a", outcome="completed")
        deferred = self.invoke(self.deferring, "reserve", dispatch_id="fix-a-again", kind="corrective",
                               failure_invariant="FR-001")
        assert deferred["disposition"] == "defer", deferred

    def start(self, name: str) -> dict[str, object]:
        (self.root / name).mkdir()
        (self.root / name / "workflow.md").write_text("# Workflow\n")
        (self.root / name / "spec.md").write_text("- FR-001: preserve data\n")
        run: dict[str, object] = {"workflow": f"{name}/workflow.md"}
        self.invoke(run, "start")
        return run

    def invoke(self, run: dict[str, object], action: str, **inputs: object) -> dict[str, object]:
        binding = {"expected_run_id": run["run_id"]} if "run_id" in run else {}
        with patch("speckit_pro_runner.execution_control.time.time", return_value=1000.0):
            result = execution_control(
                self.root, {"workflow_file": run["workflow"], "action": action, **binding, **inputs}, "apply"
            )
        run.update(run_id=result["ledger"]["run_id"], ledger_path=result["ledger_path"])
        return result

    def inputs(self, run: dict[str, object] | None = None, **overrides: object) -> dict[str, object]:
        run = run or self.clean
        inputs: dict[str, object] = {
            "ledger_path": run["ledger_path"],
            "expected_run_id": run["run_id"],
            "gates": [
                {"gate": "G7", "status": "passed", "command": "python3 tests/run-all.py"},
                {"gate": "Post: Integration Suite", "status": "passed", "command": "python3 tests/integration.py"},
            ],
            "pending_items": [],
            "unresolved_deferrals": [],
            "human_uat": [dict(UAT)],
            "pull_requests": [
                {"number": 101, "url": "https://github.com/example-org/example-repo/pull/101", "draft": True},
                {"number": 102, "url": "https://github.com/example-org/example-repo/pull/102", "draft": False},
                {"number": 103, "url": "https://github.com/example-org/example-repo/pull/103", "draft": True},
            ],
            "resume_command": RESUME,
        }
        inputs.update(overrides)
        return inputs


class FinalizeRunTests(_LedgerFixture, unittest.TestCase):
    def test_green_gates_with_only_human_uat_left_finalize_ready_for_review(self) -> None:
        result = finalize(self.root, self.inputs())
        self.assertEqual(result["outcome"], "complete_with_deferred")
        self.assertEqual(result["goal_status"], "complete")
        self.assertTrue(result["mark_ready"])
        self.assertTrue(result["finalized"])
        self.assertFalse(result["writes_state"])
        self.assertEqual(result["ready_commands"], ["gh pr ready 101", "gh pr ready 103"])
        self.assertFalse(any("merge" in command for command in result["ready_commands"]))
        self.assertEqual(result["top_pull_request"], "https://github.com/example-org/example-repo/pull/103")
        self.assertEqual(result["deferred_items"], [UAT])
        request = result["end_of_run_request"]
        self.assertIn("ready for review", request)
        for value in UAT.values():
            self.assertIn(value, request)
        self.assertIn(RESUME, request)
        self.assertTrue(result["deferred_digest"].startswith("sha256:"))
        self.assertIsNone(result["human_stop"])

    def test_a_failed_gate_is_one_human_stop_naming_the_gate_and_command(self) -> None:
        gates = [{"gate": "G7", "status": "passed", "command": "python3 tests/run-all.py"}, dict(LIVE_EVAL)]
        result = finalize(self.root, self.inputs(gates=gates))
        self.assertEqual(result["outcome"], "human_stop")
        self.assertEqual(result["goal_status"], "blocked")
        self.assertFalse(result["mark_ready"])
        self.assertFalse(result["finalized"])
        self.assertEqual(result["ready_commands"], [])
        stop = result["human_stop"]
        self.assertEqual(stop["gates"], [{"gate": LIVE_EVAL["gate"], "command": LIVE_EVAL["command"]}])
        request = result["end_of_run_request"]
        self.assertIn(LIVE_EVAL["gate"], request)
        self.assertIn(LIVE_EVAL["command"], request)
        self.assertNotIn("ready for review.", request)

    def test_an_unresolved_ledger_deferral_is_a_human_stop_not_finalize_ready(self) -> None:
        result = finalize(self.root, self.inputs(self.deferring))
        self.assertEqual(result["outcome"], "human_stop")
        self.assertFalse(result["mark_ready"])
        units = result["human_stop"]["units"]
        self.assertEqual([unit["unit"] for unit in units], ["Failure family FR-001"])
        self.assertIn("authorize-corrective-exception", units[0]["finish"])
        self.assertIn("Failure family FR-001", result["end_of_run_request"])

    def test_an_unresolved_deferred_task_is_a_human_stop(self) -> None:
        result = finalize(self.root, self.inputs(unresolved_deferrals=[dict(VETO)]))
        self.assertEqual(result["outcome"], "human_stop")
        self.assertEqual(result["human_stop"]["units"], [VETO])
        self.assertIn(VETO["finish"], result["end_of_run_request"])

    def test_only_human_uat_reaches_the_deferred_section(self) -> None:
        result = finalize(self.root, self.inputs(self.deferring, gates=[dict(LIVE_EVAL)],
                                                 unresolved_deferrals=[dict(VETO)]))
        self.assertEqual(result["deferred_items"], [UAT])

    def test_remaining_runnable_work_continues_the_run(self) -> None:
        result = finalize(self.root, self.inputs(self.deferring, pending_items=["Post: Retrospective"],
                                                 gates=[dict(LIVE_EVAL)]))
        self.assertEqual(result["outcome"], "continue")
        self.assertEqual(result["goal_status"], "not_complete")
        self.assertFalse(result["mark_ready"])
        self.assertIsNone(result["human_stop"])

    def test_nothing_left_completes_without_a_request(self) -> None:
        result = finalize(self.root, self.inputs(human_uat=[]))
        self.assertEqual(result["outcome"], "complete")
        self.assertEqual(result["goal_status"], "complete")
        self.assertTrue(result["mark_ready"])
        self.assertEqual(result["deferred_items"], [])
        self.assertEqual(result["end_of_run_request"], "")

    def test_digest_is_stable_for_an_unchanged_blocker(self) -> None:
        first = finalize(self.root, self.inputs(self.deferring))
        second = finalize(self.root, self.inputs(self.deferring))
        self.assertEqual(first["deferred_digest"], second["deferred_digest"])
        changed = finalize(self.root, self.inputs(self.deferring, unresolved_deferrals=[dict(VETO)]))
        self.assertNotEqual(first["deferred_digest"], changed["deferred_digest"])

    def test_digest_and_request_ignore_input_order(self) -> None:
        """#807 review: the same blocker listed in another order is not a changed blocker."""
        gates = [{"gate": "G7", "status": "failed", "command": "python3 tests/run-all.py"},
                 {"gate": "Post: Integration Suite", "status": "failed", "command": "python3 tests/integration.py"}]
        uat = [dict(UAT), {**UAT, "item": "Second walkthrough"}]
        forward = finalize(self.root, self.inputs(gates=gates, human_uat=uat))
        backward = finalize(self.root, self.inputs(gates=gates[::-1], human_uat=uat[::-1]))
        self.assertEqual(forward["deferred_digest"], backward["deferred_digest"])
        self.assertEqual(forward["end_of_run_request"], backward["end_of_run_request"])
        ready = finalize(self.root, self.inputs(human_uat=uat))
        again = finalize(self.root, self.inputs(human_uat=uat[::-1]))
        self.assertEqual(ready["deferred_digest"], again["deferred_digest"])
        self.assertEqual(ready["end_of_run_request"], again["end_of_run_request"])

    def test_inputs_fail_closed(self) -> None:
        cases: dict[str, dict[str, object]] = {
            "no gates": {"gates": []},
            "unknown gate status": {"gates": [{"gate": "G7", "status": "green", "command": "x"}]},
            "deferred gate status": {"gates": [{"gate": "G7", "status": "deferred", "command": "x"}]},
            "gate without command": {"gates": [{"gate": "G7", "status": "failed"}]},
            "no pull requests": {"pull_requests": []},
            "draft is not a boolean": {"pull_requests": [{"number": 1, "url": "https://x/pull/1", "draft": "yes"}]},
            "run id mismatch": {"expected_run_id": "another-run"},
            "missing ledger": {"ledger_path": "clean/.process/execution-control/missing.json"},
            "ledger outside its directory": {"ledger_path": "clean/workflow.md"},
            "traversal": {"ledger_path": "../execution-control/x.json"},
            "deferral without finish": {"unresolved_deferrals": [{"unit": "T042", "reason": "veto"}]},
            "uat without finish": {"human_uat": [{"item": "UAT", "reason": "person"}]},
            "unknown input": {"approve": True},
            "old input name": {"blocked_action_deferrals": []},
            "no resume command": {"resume_command": ""},
        }
        for name, override in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(ValueError):
                    finalize(self.root, self.inputs(**override))


def _runner(request: dict[str, object]) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        env={"PYTHONPATH": str(PLUGIN_ROOT), "PATH": os.defpath},
        check=False,
        timeout=60,
    )
    return json.loads(completed.stdout.splitlines()[-1])


class FinalizeRunRegistryTests(unittest.TestCase):
    def test_fixture_request_runs_through_the_runner(self) -> None:
        # The fixture ledger holds a deferral, so the authoritative request ends in the human stop.
        response = _runner(json.loads(FIXTURE_REQUEST.read_text(encoding="utf-8")))
        self.assertEqual(response["status"], "ok", response)
        data = response["data"]
        self.assertEqual(data["helper_id"], HELPER_ID)
        self.assertEqual(data["outcome"], "human_stop")
        self.assertEqual(data["goal_status"], "blocked")
        self.assertFalse(data["writes_state"])

    def test_bad_request_is_an_input_error(self) -> None:
        request = json.loads(FIXTURE_REQUEST.read_text(encoding="utf-8"))
        request["inputs"]["gates"] = []
        self.assertEqual(_runner(request)["status"], "input_error")


def _packet_inputs(**overrides: object) -> dict[str, object]:
    inputs: dict[str, object] = {
        "packet_path": "specs/packet-999-packet/.process/pr-packets/packet-999.json",
        "source_feature_dir": "specs/packet-999-packet",
        "workflow_file": "workflow.md",
        "target": {"base_branch": "main", "head_branch": "agent/packet-999-packet"},
        "title_type": "feat",
        "title_scope": "packet-999",
        "title_description": "Generate reviewer packet",
        "changed_files": ["specs/packet-999-packet/spec.md"],
        "verification": ["unit suite passed"],
        "summary": "Adds a reviewer packet.",
        "how_to_uat": "No manual UAT is required for this fixture.",
        "known_gaps": ["Human UAT story 2 is not verified."],
        "non_goals": ["No live pull-request mutation."],
    }
    inputs.update(overrides)
    return inputs


class DeferredSectionInPrBodyTests(unittest.TestCase):
    ITEMS = [
        {"item": "UAT story 1: the report page loads", "reason": "It needs a person at a browser.",
         "finish": "Follow steps 1 to 3 of the UAT runbook."},
        {"item": UAT["item"], "reason": UAT["reason"], "finish": UAT["finish"]},
    ]

    def render(self, **overrides: object) -> dict[str, object]:
        from speckit_pro_runner.helpers.pr_emission import normalize_packet_input

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / "workflow.md").write_text(
                "## Phase 6.5: Confidence Gate\n\n| Field | Value |\n"
                "| --- | --- |\n| Verdict | proceed |\n",
                encoding="utf-8",
            )
            with patch("speckit_pro_runner.helpers.pr_emission.find_repo_root", return_value=root):
                return normalize_packet_input(SimpleNamespace(inputs=_packet_inputs(**overrides)))

    def test_body_opens_with_the_deferred_section_and_still_validates(self) -> None:
        from speckit_pro_runner.helpers.read_only import validate_pr_packet_read_only

        rendered = self.render(deferred_items=self.ITEMS)
        self.assertNotIn("diagnostic", rendered, rendered)
        body = str(rendered["body"])
        self.assertIn("## Verification\n\nPhase 6.5 Verdict: proceed\n", body)
        headings = [line for line in body.splitlines() if line.startswith("#")]
        self.assertEqual(headings[:3], ["# feat(packet-999): Generate reviewer packet",
                                        "## Deferred / not verified", "## Summary"])
        section = body.split("## Deferred / not verified", 1)[1].split("## Summary", 1)[0]
        for item in self.ITEMS:
            for value in item.values():
                self.assertIn(value, section)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            packet = rendered["packet"]
            assert isinstance(packet, dict)
            for relative, content in ((packet["body_file"], body),
                                      (rendered["packet_path"], json.dumps(packet, indent=2) + "\n")):
                path = root / str(relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            (root / "speckit-pro/speckit_pro_runner").mkdir(parents=True)
            result = validate_pr_packet_read_only({"packet_path": rendered["packet_path"]}, root)
            verdict = json.loads(str(result["stdout"]))
            self.assertEqual((result["exit_code"], verdict["status"]), (0, "passed"), verdict)

    def test_the_section_is_protected_by_the_body_fingerprint(self) -> None:
        with_items = self.render(deferred_items=self.ITEMS)["packet"]
        other = self.render(deferred_items=[dict(self.ITEMS[0], reason="Different reason.")])["packet"]
        assert isinstance(with_items, dict) and isinstance(other, dict)
        self.assertNotEqual(with_items["protected_body_fingerprint"]["value"],
                            other["protected_body_fingerprint"]["value"])

    def test_no_deferred_items_leaves_the_body_unchanged(self) -> None:
        self.assertEqual(self.render()["body"], self.render(deferred_items=[])["body"])
        self.assertNotIn("Deferred / not verified", str(self.render()["body"]))

    def test_malformed_items_and_draft_mode_are_refused(self) -> None:
        for override in (
            {"deferred_items": [{"item": "T042", "reason": "veto"}]},
            {"deferred_items": "T042"},
            {"deferred_items": self.ITEMS, "mode": "draft"},
        ):
            with self.subTest(override=override):
                self.assertIn("diagnostic", self.render(**override))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-finalize-run"))
