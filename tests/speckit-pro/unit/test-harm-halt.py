#!/usr/bin/env python3
"""A harm halt writes a local record, blocks every runner write, and resume refuses until a human clears it (ADR 0010)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "speckit-pro"), str(REPO / "tests/speckit-pro/lib")]
from speckit_pro_runner.helpers.registry import dispatch_helper  # noqa: E402
from speckit_pro_runner.runtime import handle_request  # noqa: E402
from mutation_request_case import MutationRequestCase  # noqa: E402
from test_result import run_counted  # noqa: E402

HARM_HALTS = ("secret_exposure", "tampering_or_forged_evidence", "identity_mismatch", "concurrent_writer")
WORKFLOW = "specs/001-feature/.process/workflow.md"
LIST_FILE = "specs/001-feature/.process/decisions-list/decisions.json"
RECORD = ".specify/harm-halt/halt.json"
SAFE_STATE = "HEAD 0123abc before the plan stage"
SECRET = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
ENTRY = {"kind": "scope_answer", "option_chosen": "a", "rejected_alternative": "b", "evidence": "c", "affected_unit": "d"}


class HarmHaltTests(MutationRequestCase):
    helper_id = "harm-halt"
    files = {WORKFLOW: "# Workflow\n"}

    def halt(self, reason: str = "tampering_or_forged_evidence", evidence: str = "page hash differs") -> dict[str, Any]:
        trigger = {"reason": reason, "evidence": evidence, "last_safe_state": SAFE_STATE}
        return self.call("apply", action="halt", **trigger)

    def write_attempt(self) -> dict[str, Any]:
        """Any other apply-mode helper stands for a commit, push, PR edit or publish."""
        request = SimpleNamespace(schema_version="1.0", request_id="attempt", helper_id="decisions-list",
                                  operation="decisions-list", mode="apply",
                                  inputs={"workflow_file": WORKFLOW, "entries": [ENTRY]})
        return dispatch_helper(request)

    def test_no_record_means_resume_is_allowed_and_writes_proceed(self) -> None:
        self.assertEqual((False, "allowed"), tuple(self.read_only_data()[key] for key in ("halted", "resume")))
        self.assertEqual("ok", self.write_attempt()["status"])

    def test_each_harm_halt_writes_the_record_and_blocks_outward_writes(self) -> None:
        for reason in HARM_HALTS:
            with self.subTest(reason=reason):
                self.setUp()
                self.assertEqual("ok", self.halt(reason)["status"])
                record = json.loads((self.root / RECORD).read_text(encoding="utf-8"))
                self.assertEqual(reason, record["reason"])
                self.assertEqual(SAFE_STATE, record["last_safe_state"])
                blocked = self.write_attempt()
                self.assertEqual("harm_halt_active", blocked["diagnostics"][0]["code"], blocked)
                self.assertFalse((self.root / LIST_FILE).exists())
                self.assertEqual("*\n", (self.root / RECORD).parent.joinpath(".gitignore").read_text(encoding="utf-8"))

    def test_payload_gate_cannot_rebuild_dist_while_a_halt_stands(self) -> None:
        sentinel = self.root / "dist" / "sentinel"
        sentinel.parent.mkdir()
        sentinel.write_text("keep", encoding="utf-8")
        request = SimpleNamespace(schema_version="1.0", request_id="gate-attempt", helper_id="payload-gate",
                                  operation="payload-completeness", mode="apply", inputs={"apply_dist": True})
        self.halt("secret_exposure")
        with patch("speckit_pro_runner.gates.registry.run_payload_gate") as payload_gate:
            blocked = handle_request(request)
        self.assertEqual("harm_halt_active", blocked["diagnostics"][0]["code"], blocked)
        payload_gate.assert_not_called()
        self.assertEqual("keep", sentinel.read_text(encoding="utf-8"))
        self.assertEqual("refused", self.read_only_data()["resume"])

    def test_resume_refuses_until_the_clear_command_runs(self) -> None:
        self.halt()
        shown = self.read_only_data()
        self.assertEqual(("refused", True), (shown["resume"], shown["halted"]))
        self.assertEqual("tampering_or_forged_evidence", shown["record"]["reason"])
        wrong = self.call("apply", action="clear", confirm_reason="secret_exposure")
        self.assertEqual("input_error", wrong["status"])
        self.assertEqual("refused", self.read_only_data()["resume"])
        self.assertEqual("ok", self.call("apply", action="clear", confirm_reason="tampering_or_forged_evidence")["status"])
        self.assertEqual("allowed", self.read_only_data()["resume"])
        self.assertEqual("ok", self.write_attempt()["status"])

    def test_the_record_never_holds_the_secret(self) -> None:
        cases = (("secret_exposure", f"token={SECRET}"), ("tampering_or_forged_evidence", f"the page links {SECRET} here"))
        for reason, evidence in cases:
            with self.subTest(reason=reason):
                self.setUp()
                self.halt(reason, evidence)
                self.assertNotIn(SECRET, (self.root / RECORD).read_text(encoding="utf-8"))
        self.assertIn("[redacted]", (self.root / RECORD).read_text(encoding="utf-8"))

    def test_the_first_trigger_stands(self) -> None:
        self.halt("identity_mismatch", "wrong branch")
        self.halt("concurrent_writer", "second trigger")
        self.assertEqual("identity_mismatch", self.read_only_data()["record"]["reason"])

    def test_only_a_harm_halt_reason_is_recorded(self) -> None:
        for reason in ("merge", "all_tiers_failed", "integrity_failure", "made_up"):
            with self.subTest(reason=reason):
                self.assertEqual("input_error", self.halt(reason)["status"])
                self.assertFalse((self.root / RECORD).exists())

    def test_an_unreadable_record_fails_closed(self) -> None:
        self.halt()
        (self.root / RECORD).write_text("{not json", encoding="utf-8")
        self.assertEqual("harm_halt_active", self.write_attempt()["diagnostics"][0]["code"])
        self.assertEqual("input_error", self.call("read_only")["status"])

    def test_dry_run_and_clear_without_a_record_write_nothing(self) -> None:
        planned = self.call("dry_run", action="halt", reason="secret_exposure", evidence="e", last_safe_state="s")
        self.assertEqual(("ok", False), (planned["status"], planned["data"]["halted"]))
        self.assertEqual("input_error", self.call("apply", action="clear", confirm_reason="secret_exposure")["status"])
        self.assertFalse((self.root / RECORD).exists())


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(HarmHaltTests)


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-harm-halt"))
