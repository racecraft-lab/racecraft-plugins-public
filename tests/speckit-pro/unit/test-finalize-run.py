#!/usr/bin/env python3
"""How an autopilot run ends once no runnable work remains (issue 804).

A run that finished every runnable task and Post check, and holds only deferred
or fallback items, is done: its pull-request stack goes ready for review (never
merged), the top PR body opens with a "Deferred / not verified" section, the
goal is marked complete, and one plain-text request names what is left. The
`finalize-run` helper derives that decision from the execution-control
ledger's `deferred` list and the final gate results, and fails closed.
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
VETO = {
    "unit": "T042",
    "reason": "The approval reviewer denied the live evaluation twice: it sends skill prompts to a model service.",
    "finish": "Send the paste-ready egress authorization as a chat message, then run the T042 live evaluation.",
}


def finalize(root: Path, inputs: dict[str, object]) -> dict[str, object]:
    from speckit_pro_runner.helpers.run_finalization import finalize_run

    return finalize_run(root, inputs)


class _LedgerFixture:
    """A temporary repository whose ledger holds one runner-recorded deferral."""

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "feature").mkdir()
        (self.root / "feature/workflow.md").write_text("# Workflow\n")
        (self.root / "feature/spec.md").write_text("- FR-001: preserve data\n")
        self.run_id: str | None = None
        self.invoke("start")
        self.invoke("reserve", dispatch_id="fix-a", kind="corrective", failure_invariant="FR-001")
        self.invoke("complete", dispatch_id="fix-a", outcome="completed")
        deferred = self.invoke("reserve", dispatch_id="fix-a-again", kind="corrective", failure_invariant="FR-001")
        assert deferred["disposition"] == "defer", deferred
        self.ledger_path = deferred["ledger_path"]

    def invoke(self, action: str, **inputs: object) -> dict[str, object]:
        binding = {"expected_run_id": self.run_id} if self.run_id else {}
        with patch("speckit_pro_runner.execution_control.time.time", return_value=1000.0):
            result = execution_control(
                self.root, {"workflow_file": "feature/workflow.md", "action": action, **binding, **inputs}, "apply"
            )
        self.run_id = result["ledger"]["run_id"]
        return result

    def inputs(self, **overrides: object) -> dict[str, object]:
        inputs: dict[str, object] = {
            "ledger_path": self.ledger_path,
            "expected_run_id": self.run_id,
            "gates": [
                {"gate": "G7", "status": "passed"},
                {"gate": "Post: Integration Suite", "status": "failed", "attributed_units": ["FR-001"]},
            ],
            "pending_items": [],
            "blocked_action_deferrals": [dict(VETO)],
            "pull_requests": [
                {"number": 101, "url": "https://github.com/example-org/example-repo/pull/101", "draft": True},
                {"number": 102, "url": "https://github.com/example-org/example-repo/pull/102", "draft": False},
                {"number": 103, "url": "https://github.com/example-org/example-repo/pull/103", "draft": True},
            ],
            "resume_command": RESUME,
        }
        inputs.update(overrides)
        return inputs


class FinalizeWithDeferredItemsTests(_LedgerFixture, unittest.TestCase):
    def test_only_deferred_items_left_finalizes_ready_for_review_and_completes_the_goal(self) -> None:
        result = finalize(self.root, self.inputs())
        self.assertEqual(result["outcome"], "complete_with_deferred")
        self.assertEqual(result["goal_status"], "complete")
        self.assertTrue(result["mark_ready"])
        self.assertTrue(result["finalized"])
        self.assertFalse(result["writes_state"])
        self.assertEqual(result["ready_commands"], ["gh pr ready 101", "gh pr ready 103"])
        self.assertFalse(any("merge" in command for command in result["ready_commands"]))
        self.assertEqual(result["top_pull_request"], "https://github.com/example-org/example-repo/pull/103")
        items = result["deferred_items"]
        self.assertEqual([item["item"] for item in items], ["Failure family FR-001", "T042"])
        for item in items:
            self.assertEqual(sorted(item), ["finish", "item", "reason"])
            self.assertTrue(item["reason"] and item["finish"])
        self.assertIn("authorize-corrective-exception", items[0]["finish"])
        self.assertIn(RESUME, items[0]["finish"])
        self.assertEqual(items[1]["reason"], VETO["reason"])
        self.assertEqual(items[1]["finish"], VETO["finish"])
        request = result["end_of_run_request"]
        self.assertIn("ready for review", request)
        for item in items:
            self.assertIn(item["item"], request)
            self.assertIn(item["reason"], request)
            self.assertIn(item["finish"], request)
        self.assertIn(RESUME, request)
        self.assertTrue(result["deferred_digest"].startswith("sha256:"))

    def test_gate_failing_only_on_a_deferred_unit_is_reported_deferred_not_green(self) -> None:
        gates = finalize(self.root, self.inputs())["gates"]
        self.assertEqual([gate["result"] for gate in gates], ["passed", "deferred"])

    def test_unrelated_gate_failure_still_blocks(self) -> None:
        for failing in (
            {"gate": "Post: Integration Suite", "status": "failed"},
            {"gate": "Post: Integration Suite", "status": "failed", "attributed_units": []},
            {"gate": "Post: Integration Suite", "status": "failed", "attributed_units": ["FR-001", "FR-009"]},
        ):
            with self.subTest(gate=failing):
                result = finalize(self.root, self.inputs(gates=[{"gate": "G7", "status": "passed"}, failing]))
                self.assertEqual(result["outcome"], "blocked")
                self.assertEqual(result["goal_status"], "not_complete")
                self.assertFalse(result["mark_ready"])
                self.assertEqual(result["ready_commands"], [])
                self.assertEqual(result["gates"][1]["result"], "failed")

    def test_remaining_runnable_work_continues_the_run(self) -> None:
        result = finalize(self.root, self.inputs(pending_items=["Post: Retrospective"]))
        self.assertEqual(result["outcome"], "continue")
        self.assertEqual(result["goal_status"], "not_complete")
        self.assertFalse(result["mark_ready"])
        self.assertFalse(result["finalized"])

    def test_nothing_deferred_and_all_green_completes_without_a_request(self) -> None:
        (self.root / "fresh").mkdir()
        (self.root / "fresh/workflow.md").write_text("# Workflow\n")
        (self.root / "fresh/spec.md").write_text("- FR-001: preserve data\n")
        with patch("speckit_pro_runner.execution_control.time.time", return_value=1000.0):
            fresh = execution_control(self.root, {"workflow_file": "fresh/workflow.md", "action": "start"}, "apply")
        inputs = self.inputs(
            ledger_path=fresh["ledger_path"],
            expected_run_id=fresh["ledger"]["run_id"],
            gates=[{"gate": "G7", "status": "passed"}],
            blocked_action_deferrals=[],
        )
        result = finalize(self.root, inputs)
        self.assertEqual(result["outcome"], "complete")
        self.assertEqual(result["goal_status"], "complete")
        self.assertTrue(result["mark_ready"])
        self.assertEqual(result["deferred_items"], [])
        self.assertEqual(result["end_of_run_request"], "")

    def test_digest_is_stable_for_an_unchanged_blocker(self) -> None:
        first = finalize(self.root, self.inputs())
        second = finalize(self.root, self.inputs())
        self.assertEqual(first["deferred_digest"], second["deferred_digest"])
        changed = finalize(self.root, self.inputs(blocked_action_deferrals=[dict(VETO, unit="T043")]))
        self.assertNotEqual(first["deferred_digest"], changed["deferred_digest"])

    def test_inputs_fail_closed(self) -> None:
        cases: dict[str, dict[str, object]] = {
            "no gates": {"gates": []},
            "unknown gate status": {"gates": [{"gate": "G7", "status": "green"}]},
            "attribution on a passed gate": {"gates": [{"gate": "G7", "status": "passed", "attributed_units": ["FR-001"]}]},
            "no pull requests": {"pull_requests": []},
            "draft is not a boolean": {"pull_requests": [{"number": 1, "url": "https://x/pull/1", "draft": "yes"}]},
            "run id mismatch": {"expected_run_id": "another-run"},
            "missing ledger": {"ledger_path": "feature/.process/execution-control/missing.json"},
            "ledger outside its directory": {"ledger_path": "feature/workflow.md"},
            "traversal": {"ledger_path": "../execution-control/x.json"},
            "deferral without finish": {"blocked_action_deferrals": [{"unit": "T042", "reason": "veto"}]},
            "unknown input": {"approve": True},
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
        response = _runner(json.loads(FIXTURE_REQUEST.read_text(encoding="utf-8")))
        self.assertEqual(response["status"], "ok", response)
        data = response["data"]
        self.assertEqual(data["helper_id"], HELPER_ID)
        self.assertEqual(data["outcome"], "complete_with_deferred")
        self.assertEqual(data["goal_status"], "complete")
        self.assertFalse(data["writes_state"])

    def test_bad_request_is_an_input_error(self) -> None:
        request = json.loads(FIXTURE_REQUEST.read_text(encoding="utf-8"))
        request["inputs"]["gates"] = []
        self.assertEqual(_runner(request)["status"], "input_error")


def _packet_inputs(**overrides: object) -> dict[str, object]:
    inputs: dict[str, object] = {
        "packet_path": "specs/packet-999-packet/.process/pr-packets/packet-999.json",
        "source_feature_dir": "specs/packet-999-packet",
        "target": {"base_branch": "main", "head_branch": "agent/packet-999-packet"},
        "title_type": "feat",
        "title_scope": "packet-999",
        "title_description": "Generate reviewer packet",
        "changed_files": ["specs/packet-999-packet/spec.md"],
        "verification": ["unit suite passed"],
        "summary": "Adds a reviewer packet.",
        "how_to_uat": "No manual UAT is required for this fixture.",
        "known_gaps": ["T042 is deferred."],
        "non_goals": ["No live pull-request mutation."],
    }
    inputs.update(overrides)
    return inputs


class DeferredSectionInPrBodyTests(unittest.TestCase):
    ITEMS = [
        {"item": "Failure family FR-001", "reason": "Its correction allowance is spent.", "finish": "Approve one exception."},
        {"item": "T042", "reason": VETO["reason"], "finish": VETO["finish"]},
    ]

    def render(self, **overrides: object) -> dict[str, object]:
        from speckit_pro_runner.helpers.pr_emission import normalize_packet_input

        return normalize_packet_input(SimpleNamespace(inputs=_packet_inputs(**overrides)))

    def test_body_opens_with_the_deferred_section_and_still_validates(self) -> None:
        from speckit_pro_runner.helpers.read_only import validate_pr_packet_read_only

        rendered = self.render(deferred_items=self.ITEMS)
        self.assertNotIn("diagnostic", rendered, rendered)
        body = str(rendered["body"])
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
