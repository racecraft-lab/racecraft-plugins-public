#!/usr/bin/env python3
"""Autopilot ratifies a budget-driven PR split without a human (issue 763).

The per-PR path cap can force the planner to split an approved PR order into
smaller increments. The `ratify-pr-split` helper decides whether autopilot may
ratify that split itself: only when it splits approved groups without merging
or dropping them, keeps the approved order and each group's scope, keeps every
active requirement, story, and task, and keeps each increment within the cap.
Anything else routes to the operator. These tests pin both outcomes, the
fail-closed input rules, and the skill prose for both hosts.
"""

from __future__ import annotations

import copy
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

HELPER_ID = "ratify-pr-split"
FIXTURES = REPO_ROOT / "tests/speckit-pro/unit/fixtures/pr-split-ratification"
FIXTURE_REQUEST = (
    REPO_ROOT / "tests/speckit-pro/unit/fixtures/read-only-helpers/requests" / f"{HELPER_ID}.json"
)
CLAUDE_PHASE = PLUGIN_ROOT / "skills/speckit-autopilot/references/phase-execution.md"
CODEX_PHASE = PLUGIN_ROOT / "codex-skills/speckit-autopilot/references/phase-execution-codex.md"
CLAUDE_SKILL = PLUGIN_ROOT / "skills/speckit-autopilot/SKILL.md"
CLAUDE_GATES = PLUGIN_ROOT / "skills/speckit-autopilot/references/gate-validation.md"


def _fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))["inputs"]


def _run(inputs: object) -> dict[str, object]:
    request = {
        "schema_version": "1.0",
        "request_id": f"test-{HELPER_ID}",
        "helper_id": HELPER_ID,
        "operation": HELPER_ID,
        "mode": "read_only",
        "inputs": inputs,
    }
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


def _codes(data: dict[str, object]) -> list[str]:
    return [str(item["code"]) for item in data["findings"]]  # type: ignore[index, union-attr]


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class RatifyPrSplitTests(unittest.TestCase):
    def test_preserving_split_is_ratified_by_autopilot(self) -> None:
        response = _run(_fixture("preserving-split"))
        self.assertEqual(response["status"], "ok", response)
        data = response["data"]
        self.assertFalse(data["writes_state"])
        self.assertEqual(data["operation"], HELPER_ID)
        self.assertEqual(data["decision"], "autopilot_ratified")
        self.assertEqual(data["owner_ratification"], "ratified")
        self.assertEqual(data["ratified_by"], "autopilot")
        self.assertEqual(data["findings"], [])
        self.assertIn("5 approved groups into 8 increments", data["reason"])
        self.assertEqual(data["record"][:2], ["owner_ratification=ratified", "ratified_by=autopilot"])
        self.assertTrue(data["record"][2].startswith("ratification_reason="))

    def test_dropped_requirement_routes_to_operator(self) -> None:
        data = _run(_fixture("dropped-requirement"))["data"]
        self.assertEqual(data["decision"], "operator_required")
        self.assertEqual(data["owner_ratification"], "pending")
        self.assertIsNone(data["ratified_by"])
        self.assertEqual(_codes(data), ["scope_dropped"])
        self.assertIn("FR-002", data["findings"][0]["detail"])
        self.assertEqual(data["record"][0], "owner_ratification=pending")
        self.assertEqual(data["record"][1], "ratification_blockers=scope_dropped")

    def test_reordered_groups_route_to_operator(self) -> None:
        data = _run(_fixture("reordered-groups"))["data"]
        self.assertEqual(data["decision"], "operator_required")
        self.assertEqual(data["owner_ratification"], "pending")
        self.assertIsNone(data["ratified_by"])
        self.assertEqual(_codes(data), ["group_reordered"])

    def test_merge_across_groups_routes_to_operator(self) -> None:
        inputs = _fixture("preserving-split")
        increments = inputs["increments"]  # type: ignore[index]
        increments[1]["scope"] = ["T002", "FR-002"]  # type: ignore[index]
        increments[2]["scope"] = ["T003"]  # type: ignore[index]
        data = _run(inputs)["data"]
        self.assertEqual(_codes(data), ["group_merged"])

    def test_added_scope_routes_to_operator(self) -> None:
        inputs = _fixture("preserving-split")
        increments = inputs["increments"]  # type: ignore[index]
        increments[0]["scope"] = ["FR-001", "US1", "T001", "T999"]  # type: ignore[index]
        data = _run(inputs)["data"]
        self.assertEqual(_codes(data), ["scope_added"])

    def test_new_active_scope_since_approval_routes_to_operator(self) -> None:
        inputs = _fixture("preserving-split")
        inputs["active_scope"] = [*inputs["active_scope"], "FR-006"]  # type: ignore[misc]
        data = _run(inputs)["data"]
        self.assertEqual(data["decision"], "operator_required")
        self.assertIn("scope_added", _codes(data))

    def test_dropped_group_routes_to_operator(self) -> None:
        inputs = _fixture("preserving-split")
        inputs["increments"] = inputs["increments"][:-1]  # type: ignore[index]
        data = _run(inputs)["data"]
        self.assertEqual(_codes(data), ["group_dropped", "scope_dropped"])

    def test_unknown_group_routes_to_operator(self) -> None:
        inputs = _fixture("preserving-split")
        inputs["increments"][-1]["group_id"] = "D"  # type: ignore[index]
        data = _run(inputs)["data"]
        self.assertIn("group_added", _codes(data))

    def test_over_budget_increment_needs_a_reviewability_exception(self) -> None:
        for field, value in (("production_paths", 5), ("total_paths", 25)):
            with self.subTest(field=field):
                inputs = _fixture("preserving-split")
                inputs["increments"][0][field] = value  # type: ignore[index]
                data = _run(inputs)["data"]
                self.assertEqual(data["decision"], "operator_required")
                self.assertEqual(_codes(data), ["reviewability_exception_needed"])

    def test_invalid_input_fails_closed(self) -> None:
        base = _fixture("preserving-split")

        def variant(mutate: object) -> dict[str, object]:
            copied = copy.deepcopy(base)
            mutate(copied)  # type: ignore[operator]
            return copied

        cases = {
            "missing budget": variant(lambda d: d.pop("path_budget")),
            "missing active scope": variant(lambda d: d.pop("active_scope")),
            "budget without total": variant(lambda d: d["path_budget"].pop("total_paths")),
            "negative budget": variant(lambda d: d["path_budget"].update(production_paths=-1)),
            "boolean path count": variant(lambda d: d["increments"][0].update(total_paths=True)),
            "missing path count": variant(lambda d: d["increments"][0].pop("production_paths")),
            "no groups": variant(lambda d: d.update(approved_groups=[])),
            "no increments": variant(lambda d: d.update(increments=[])),
            "empty increment scope": variant(lambda d: d["increments"][0].update(scope=[])),
            "duplicate group id": variant(lambda d: d["approved_groups"].append(dict(d["approved_groups"][0]))),
            "duplicate increment id": variant(lambda d: d["increments"].append(dict(d["increments"][0]))),
            "item in two groups": variant(lambda d: d["approved_groups"][1]["scope"].append("FR-001")),
            "unknown input": variant(lambda d: d.update(extra=True)),
            "unknown increment field": variant(lambda d: d["increments"][0].update(note="x")),
        }
        for label, inputs in cases.items():
            with self.subTest(case=label):
                response = _run(inputs)
                self.assertEqual(response["status"], "input_error", response)
                self.assertEqual([item["code"] for item in response["diagnostics"]], ["invalid_input"])

    def test_fixture_request_is_ratified(self) -> None:
        request = json.loads(FIXTURE_REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["helper_id"], HELPER_ID)
        self.assertEqual(_run(request["inputs"])["data"]["decision"], "autopilot_ratified")


class SplitRatificationSourceContractTests(unittest.TestCase):
    """Both hosts' guidance states the rule and the one-live-value rule."""

    def test_both_hosts_route_budget_splits_through_the_helper(self) -> None:
        for path in (CLAUDE_PHASE, CODEX_PHASE):
            with self.subTest(path=path.name):
                text = _flat(path)
                self.assertIn("helper_id=ratify-pr-split", text)
                self.assertIn("`ratified_by=autopilot`", text)
                self.assertIn(
                    "Ask the operator only when the helper returns `decision=operator_required`",
                    text,
                )
                self.assertIn("never ratify it yourself", text)
                for code in (
                    "scope_added",
                    "scope_dropped",
                    "group_reordered",
                    "group_merged",
                    "reviewability_exception_needed",
                ):
                    self.assertIn(f"`{code}`", text)

    def test_both_hosts_keep_one_live_ratification_value(self) -> None:
        for path in (CLAUDE_PHASE, CODEX_PHASE):
            with self.subTest(path=path.name):
                text = _flat(path)
                self.assertIn("`owner_ratification=superseded`", text)
                self.assertIn("only one live `owner_ratification` value", text)

    def test_split_evidence_is_no_longer_operator_only(self) -> None:
        for path in (CLAUDE_SKILL, CLAUDE_GATES, CODEX_PHASE):
            with self.subTest(path=path.name):
                text = _flat(path)
                self.assertNotIn("operator-ratified split decision", text)
                self.assertIn("ratified split decision (autopilot or operator)", text)


if __name__ == "__main__":
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite(
        [
            loader.loadTestsFromTestCase(RatifyPrSplitTests),
            loader.loadTestsFromTestCase(SplitRatificationSourceContractTests),
        ]
    )
    raise SystemExit(run_counted(suite, label="test-ratify-pr-split"))
