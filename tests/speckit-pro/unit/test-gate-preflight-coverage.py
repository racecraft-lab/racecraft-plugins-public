#!/usr/bin/env python3
"""Every gate's required escalation is in the Phase 6.5 inventory at run start.

A gate that fails at the end of a run for want of an authorization is a
preflight defect: the inventory should have collected that authorization at
run start, as a chat reply. The `check-gate-preflight-coverage` helper names
each gate need that no inventoried action covers, and fails closed.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
for entry in (PLUGIN_ROOT, REPO_ROOT / "tests" / "speckit-pro" / "lib"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from test_result import run_counted  # noqa: E402

HELPER_ID = "check-gate-preflight-coverage"
FIXTURE_REQUEST = (
    REPO_ROOT / "tests/speckit-pro/unit/fixtures/read-only-helpers/requests" / f"{HELPER_ID}.json"
)
SCHEMA = REPO_ROOT / "speckit-pro/skills/speckit-autopilot/contracts/autonomy-boundary.schema.json"
EVAL_NEED = {"category": "external_side_effect", "target": "api.example.com model service"}
GATES = [
    {"gate": "G7", "command": "python3 tests/run-all.py", "needs": []},
    {"gate": "Post: Live Evaluation", "command": "python3 tests/live/run-eval.py --task T042",
     "needs": [dict(EVAL_NEED)]},
]
INVENTORY = [{"action_id": "live-skill-eval", **EVAL_NEED}]


def check(inputs: dict[str, object]) -> dict[str, object]:
    from speckit_pro_runner.helpers.gate_preflight_coverage import gate_preflight_coverage

    return gate_preflight_coverage(inputs)


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


class GatePreflightCoverageTests(unittest.TestCase):
    def test_every_gate_need_in_the_inventory_is_covered(self) -> None:
        result = check({"gates": GATES, "inventory_actions": INVENTORY})
        self.assertTrue(result["covered"])
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["covering_actions"], {"Post: Live Evaluation": ["live-skill-eval"]})
        self.assertFalse(result["writes_state"])

    def test_a_gate_need_missing_from_the_inventory_is_a_preflight_defect(self) -> None:
        result = check({"gates": GATES, "inventory_actions": []})
        self.assertFalse(result["covered"])
        self.assertEqual(result["missing"], [{"gate": "Post: Live Evaluation",
                                              "command": "python3 tests/live/run-eval.py --task T042",
                                              **EVAL_NEED}])

    def test_a_different_target_or_category_does_not_cover(self) -> None:
        for action in (
            {"action_id": "a", "category": "external_side_effect", "target": "api.other.example model service"},
            {"action_id": "a", "category": "privileged_command", "target": EVAL_NEED["target"]},
        ):
            with self.subTest(action=action):
                self.assertFalse(check({"gates": GATES, "inventory_actions": [action]})["covered"])

    def test_categories_match_the_autonomy_boundary_schema(self) -> None:
        from speckit_pro_runner.helpers.gate_preflight_coverage import CATEGORIES

        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(set(CATEGORIES), set(schema["$defs"]["action"]["properties"]["category"]["enum"]))

    def test_inputs_fail_closed(self) -> None:
        cases: dict[str, dict[str, object]] = {
            "no gates": {"gates": [], "inventory_actions": INVENTORY},
            "gate without needs": {"gates": [{"gate": "G7", "command": "x"}], "inventory_actions": []},
            "unknown category": {"gates": [{"gate": "G7", "command": "x",
                                            "needs": [{"category": "egress", "target": "t"}]}],
                                 "inventory_actions": []},
            "inventory not a list": {"gates": GATES, "inventory_actions": {}},
            "action without target": {"gates": GATES,
                                      "inventory_actions": [{"action_id": "a", "category": "external_side_effect"}]},
            "unknown input": {"gates": GATES, "inventory_actions": INVENTORY, "skip": True},
        }
        for name, inputs in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(ValueError):
                    check(inputs)

    def test_a_declared_pre_pr_audit_command_lands_in_the_required_needs(self) -> None:
        import tempfile

        from speckit_pro_runner.helpers.gate_preflight_coverage import gate_preflight_coverage

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "AGENTS.md").write_text(
                "# Rules\n\nBefore a PR, run `pnpm audit --prod` and the checks below.\n\n"
                "```bash\nnpm audit --audit-level=high\npnpm test\n```\n\n"
                "Dependency audits matter, but prose alone declares no command.\n", encoding="utf-8")
            (root / "CLAUDE.md").write_text("@./AGENTS.md\n\nAlso run `pnpm audit --prod`.\n", encoding="utf-8")
            audits = ["npm audit --audit-level=high", "pnpm audit --prod"]
            result = gate_preflight_coverage({"gates": GATES, "inventory_actions": INVENTORY}, root)
            self.assertFalse(result["covered"])
            self.assertEqual(result["declared_commands"],
                             [{"command": "npm audit --audit-level=high", "source": "AGENTS.md"},
                              {"command": "pnpm audit --prod", "source": "AGENTS.md"}])
            self.assertEqual(result["missing"], [
                {"gate": f"pre-PR: {command}", "command": command, "category": "external_side_effect",
                 "target": command} for command in audits])
            covered = [*INVENTORY, *({"action_id": f"audit-{index}", "category": "external_side_effect",
                                      "target": command} for index, command in enumerate(audits))]
            result = gate_preflight_coverage({"gates": GATES, "inventory_actions": covered}, root)
            self.assertTrue(result["covered"])
            self.assertEqual(result["covering_actions"]["pre-PR: pnpm audit --prod"], ["audit-1"])
            (root / "AGENTS.md").write_text("Run a dependency audit before a PR.\n", encoding="utf-8")
            (root / "CLAUDE.md").unlink()
            quiet = gate_preflight_coverage({"gates": GATES, "inventory_actions": INVENTORY}, root)
            self.assertEqual((quiet["covered"], quiet["declared_commands"]), (True, []))
            (root / "AGENTS.md").write_bytes(b"`npm audit`\xff\n")
            with self.assertRaises(ValueError):
                gate_preflight_coverage({"gates": GATES, "inventory_actions": INVENTORY}, root)

    def test_both_hosts_collect_declared_pre_pr_commands_at_run_start(self) -> None:
        codex = " ".join((PLUGIN_ROOT / "codex-skills/speckit-autopilot/references/phase-execution-codex.md")
                         .read_text(encoding="utf-8").split())
        for phrase in ("`declared_commands`", "declared pre-PR command", "copy its `target` verbatim"):
            self.assertIn(phrase, codex)
        claude = " ".join((PLUGIN_ROOT / "skills/speckit-autopilot/references/phase-execution.md")
                          .read_text(encoding="utf-8").split())
        for phrase in ("declared pre-PR command", "`check-gate-preflight-coverage`"):
            self.assertIn(phrase, claude)

    def test_runner_reports_a_gap_as_an_expected_failure(self) -> None:
        request = json.loads(FIXTURE_REQUEST.read_text(encoding="utf-8"))
        response = _runner(request)
        self.assertEqual(response["status"], "ok", response)
        self.assertTrue(response["data"]["covered"])
        request["inputs"]["inventory_actions"] = []
        response = _runner(request)
        self.assertEqual(response["status"], "expected_failure", response)
        self.assertFalse(response["data"]["covered"])
        request["inputs"]["gates"] = []
        self.assertEqual(_runner(request)["status"], "input_error")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-gate-preflight-coverage"))
