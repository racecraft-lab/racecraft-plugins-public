#!/usr/bin/env python3
"""The failure-path seam: budgets, epochs, operator events and the invariant registry cross one table.

The golden replay in `test-corrective-authorization-runner-routes.py` pins the
outcomes. This test pins the shape: every failure-path action is reachable only
through `FAILURE_PATH_ACTIONS` and `run_failure_path`, so deleting the machinery
(ADR 0004) removes table rows and handlers, and no caller.
"""

from __future__ import annotations

import ast
import contextlib
import copy
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted
from speckit_pro_runner import execution_control as control

SEAM_ACTIONS = {"bind-invariants", "reserve", "authorize-corrective-retry", "authorize-corrective-continuation",
                "authorize-corrective-exception", "reserve-class-correction", "begin-replan-epoch",
                "begin-stage-epoch"}
SOURCE = Path(control.__file__)


@contextlib.contextmanager
def greenfield():
    """A temporary root and a ledger started before its spec exists, then the two-invariant spec the tests bind."""
    with tempfile.TemporaryDirectory() as name:
        root = Path(name).resolve()
        (root / "workflow.md").write_text("# Workflow\n")
        ledger = control.initial_ledger(root / "spec.md", 1000.0)
        (root / "spec.md").write_text("- FR-001: preserve data\n- FR-002: no secrets\n")
        yield root, ledger


class FailurePathSeamTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root, self.ledger = self.enterContext(greenfield())

    def call(self, held=False, **inputs):
        return control.FailurePathCall(self.root, self.ledger, inputs, self.root / "spec.md",
                                       self.root / "workflow.md", 1000.0, held)

    def test_the_table_names_exactly_the_failure_path_actions(self) -> None:
        self.assertEqual(set(control.FAILURE_PATH_ACTIONS), SEAM_ACTIONS)
        self.assertLessEqual(SEAM_ACTIONS, control.UNKNOWN_GUARDED_ACTIONS)
        self.assertLessEqual(SEAM_ACTIONS, control._ACTIONS)

    def test_a_reservation_is_made_through_the_seam(self) -> None:
        call = self.call(dispatch_id="fix-a", kind="corrective", failure_invariant="FR-001")
        result = control.run_failure_path("reserve", call, {})
        self.assertEqual(self.ledger["dispatches"]["fix-a"]["reservation_id"], result["reservation_id"])
        self.assertEqual(self.ledger["corrective_cycles"], 1)

    def test_a_held_run_skips_every_action_and_returns_the_held_result(self) -> None:
        held = {"blocked_by": ["u1"]}
        inputs = {"dispatch_id": "fix-a", "kind": "corrective", "failure_invariant": "FR-001", "spec_file": "spec.md"}
        for action in sorted(SEAM_ACTIONS):
            before = copy.deepcopy(self.ledger)
            with self.subTest(action=action):
                self.assertIs(control.run_failure_path(action, self.call(True, **inputs), held), held)
                self.assertEqual(self.ledger, before)

    def test_the_invariant_registry_is_frozen_once_and_validated_even_while_held(self) -> None:
        call = self.call(spec_file="spec.md")
        self.assertEqual(control.run_failure_path("bind-invariants", call, {}), {})
        self.assertEqual(self.ledger["approved_invariants"], ["FR-001", "FR-002"])
        with self.assertRaisesRegex(ValueError, "already frozen"):
            control.run_failure_path("bind-invariants", call, {})
        with self.assertRaisesRegex(ValueError, "explicit spec_file"):
            control.run_failure_path("bind-invariants", self.call(True), {})

    def test_failure_path_handlers_are_named_only_in_the_table(self) -> None:
        handlers = {"reserve", "authorize_corrective_retry", "authorize_corrective_continuation",
                    "authorize_corrective_exception", "reserve_class_correction", "begin_replan_epoch",
                    "begin_stage_epoch", "_freeze_invariants"}
        outside = []
        for path in sorted(SOURCE.parent.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            inside = {id(node) for stmt in tree.body if _is_table(stmt) for node in ast.walk(stmt)}
            outside += [f"{path.name}:{node.lineno} {_name(node)}" for node in ast.walk(tree)
                        if _name(node) in handlers and id(node) not in inside]
        self.assertEqual(outside, [])

    def test_escalation_reads_cross_the_seam_not_the_internals(self) -> None:
        internals = {"escalation_key", "escalation_progress", "ESCALATION_TIER3_CAP"}
        outside = []
        for path in sorted(SOURCE.parent.rglob("*.py")):
            if path == SOURCE:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            outside += [f"{path.name}:{node.lineno} {_name(node)}" for node in ast.walk(tree)
                        if _name(node) in internals]
        self.assertEqual(outside, [])

    def test_a_unit_with_no_escalation_record_is_at_tier_two(self) -> None:
        view = control.unit_escalation(self.ledger, "gate_failure", "abc")
        self.assertEqual((view.progress, view.record, view.tier3_cap), ("tier2", None, control.ESCALATION_TIER3_CAP))


def _is_table(statement: ast.stmt) -> bool:
    return isinstance(statement, ast.AnnAssign) and ast.unparse(statement.target) == "FAILURE_PATH_ACTIONS"


def _name(node: ast.AST) -> str | None:
    """The identifier a reference, import or attribute access names; None for any other node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return node.name if isinstance(node, ast.alias) else None


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FailurePathSeamTests)
    raise SystemExit(run_counted(suite, label="test-failure-path-seam"))
