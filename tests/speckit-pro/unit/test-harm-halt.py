#!/usr/bin/env python3
"""A harm halt writes a local record, blocks every runner write, and resume refuses until a human clears it (ADR 0010)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import select
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "speckit-pro"), str(REPO / "tests/speckit-pro/lib")]
from speckit_pro_runner.helpers.registry import dispatch_helper  # noqa: E402
from speckit_pro_runner.helpers import harm_halt  # noqa: E402
from speckit_pro_runner.runtime import handle_request  # noqa: E402
from speckit_pro_runner.__main__ import main as runner_main  # noqa: E402
from speckit_pro_runner.sweep_isolation import RECEIPT_PREFIX  # noqa: E402
from mutation_request_case import FIXTURES, MutationRequestCase  # noqa: E402
from test_result import run_counted  # noqa: E402

HARM_HALTS = ("secret_exposure", "tampering_or_forged_evidence", "identity_mismatch", "concurrent_writer")
WORKFLOW = "specs/001-feature/.process/workflow.md"
LIST_FILE = "specs/001-feature/.process/decisions-list/decisions.json"
RECORD = ".specify/harm-halt/halt.json"
SAFE_STATE = "HEAD 0123abc before the plan stage"
SECRET = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
ENTRY = {"kind": "scope_answer", "option_chosen": "a", "rejected_alternative": "b", "evidence": "c", "affected_unit": "d"}


class QuietTerminal(MutationRequestCase):
    """Tests never write a clear token to the terminal of whoever runs the suite."""

    def setUp(self) -> None:
        super().setUp()
        self.shown: list[str] = []
        quiet = patch.object(harm_halt, "show_on_owner_terminal", side_effect=self.shown.append)
        quiet.start()
        self.addCleanup(quiet.stop)


class HarmHaltTests(QuietTerminal):
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

    def test_runner_entry_refuses_each_dispatch_path_with_valid_or_unreadable_halt(self) -> None:
        sentinel = self.root / "dist" / "sentinel"
        sentinel.parent.mkdir()
        sentinel.write_text("keep", encoding="utf-8")
        routes = (
            ("payload-gate", "payload-completeness", {"apply_dist": True},
             "speckit_pro_runner.gates.registry.run_payload_gate"),
            ("decisions-list", "decisions-list", {"workflow_file": WORKFLOW, "entries": [ENTRY]},
             "speckit_pro_runner.helpers.registry.dispatch_helper"),
        )
        self.halt("secret_exposure")
        for unreadable in (False, True):
            if unreadable:
                (self.root / RECORD).write_text("{not json", encoding="utf-8")
            for helper_id, operation, inputs, target in routes:
                with self.subTest(unreadable=unreadable, helper_id=helper_id):
                    request = SimpleNamespace(schema_version="1.0", request_id="attempt", helper_id=helper_id,
                                              operation=operation, mode="apply", inputs=inputs)
                    with patch(target) as dispatch:
                        blocked = handle_request(request)
                    self.assertEqual("harm_halt_active", blocked["diagnostics"][0]["code"], blocked)
                    dispatch.assert_not_called()
                    self.assertEqual("keep", sentinel.read_text(encoding="utf-8"))
                    self.assertFalse((self.root / LIST_FILE).exists())

    def test_disclosed_reason_cannot_authorize_an_agent_clear(self) -> None:
        self.halt()
        shown = self.read_only_data()
        self.assertEqual(("refused", True), (shown["resume"], shown["halted"]))
        self.assertEqual("tampering_or_forged_evidence", shown["record"]["reason"])
        wrong = self.call("apply", action="clear", confirm_reason="secret_exposure")
        self.assertEqual("input_error", wrong["status"])
        self.assertEqual("refused", self.read_only_data()["resume"])
        self.assertEqual("input_error", self.call("apply", action="clear", confirm_reason=shown["record"]["reason"])["status"])
        self.assertEqual("refused", self.read_only_data()["resume"])
        self.assertEqual("harm_halt_active", self.write_attempt()["diagnostics"][0]["code"])


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
        self.assertEqual("input_error", self.halt("concurrent_writer", "second trigger")["status"])
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
        self.assertEqual("input_error", self.call("apply", action="clear", token="guess")["status"])
        self.assertFalse((self.root / RECORD).exists())


class HaltDispatchTests(QuietTerminal):
    helper_id = harm_halt.HELPER_ID
    files = {WORKFLOW: "# Workflow\n"}

    def test_direct_helper_dispatch_refuses_a_stateful_read(self) -> None:
        harm_halt.record_halt(self.root, "secret_exposure", "withheld", SAFE_STATE)
        request = SimpleNamespace(schema_version="1.0", request_id="direct", helper_id="sweep-isolation-session",
                                  operation="sweep-isolation-session", mode="read_only",
                                  inputs={"named_surface": "capture", "surface": "codex", "repository": "owner/repo",
                                          "pr_number": 498, "workflow_file": WORKFLOW})
        with patch("speckit_pro_runner.helpers.registry.run_registered_helper") as dispatch:
            result = dispatch_helper(request)
        self.assertEqual("harm_halt_active", result["diagnostics"][0]["code"], result)
        dispatch.assert_not_called()

    def test_standing_halt_refuses_stateful_read_only_sweep_operations(self) -> None:
        harm_halt.record_halt(self.root, "secret_exposure", "withheld", SAFE_STATE)
        for surface in ("capture", "launch_codex", "launch_claude", "accept", "close"):
            with self.subTest(surface=surface):
                inputs: dict[str, Any] = {"named_surface": surface, "session_id": "a" * 32}
                if surface == "capture":
                    inputs = {"named_surface": surface, "surface": "codex", "repository": "owner/repo",
                              "pr_number": 498, "workflow_file": WORKFLOW}
                elif surface.startswith("launch_"):
                    inputs.update(comment_id="RC_kwDO123", stage="classifier")
                elif surface == "accept":
                    inputs.update(receipt=RECEIPT_PREFIX + "b" * 64, stage="classifier")
                request = SimpleNamespace(schema_version="1.0", request_id="attempt",
                                          helper_id="sweep-isolation-session", operation="sweep-isolation-session",
                                          mode="read_only", inputs=inputs)
                with patch("speckit_pro_runner.helpers.registry.run_registered_helper") as dispatch:
                    blocked = handle_request(request)
                self.assertEqual("harm_halt_active", blocked["diagnostics"][0]["code"], blocked)
                dispatch.assert_not_called()
        self.assertEqual("refused", self.read_only_data()["resume"])

    def test_payload_gate_checks_its_actual_root_from_a_nested_specify_directory(self) -> None:
        (self.root / "speckit-pro/speckit_pro_runner").mkdir(parents=True)
        (self.root / "tests/speckit-pro").mkdir(parents=True)
        nested = self.root / "fixture"
        (nested / ".specify").mkdir(parents=True)
        harm_halt.record_halt(self.root, "secret_exposure", "withheld", SAFE_STATE)
        request = SimpleNamespace(schema_version="1.0", request_id="nested", helper_id="payload-gate",
                                  operation="payload-completeness", mode="apply", inputs={"apply_dist": True})
        with patch.object(Path, "cwd", return_value=nested), patch("speckit_pro_runner.gates.registry.run_payload_gate") as gate:
            blocked = handle_request(request)
        self.assertEqual("harm_halt_active", blocked["diagnostics"][0]["code"], blocked)
        gate.assert_not_called()


class HaltConcurrencyTests(QuietTerminal):
    helper_id = harm_halt.HELPER_ID
    files = {WORKFLOW: "# Workflow\n"}

    def test_unsafe_halt_storage_refuses_writes_and_resume(self) -> None:
        for obstruction in ("ignore_marker", "directory"):
            with self.subTest(obstruction=obstruction):
                self.setUp()
                if obstruction == "ignore_marker":
                    (self.root / ".specify/harm-halt/.gitignore").mkdir(parents=True)
                else:
                    (self.root / ".specify/harm-halt").write_text("obstruction", encoding="utf-8")
                request = SimpleNamespace(schema_version="1.0", request_id="storage", helper_id="decisions-list",
                                          operation="decisions-list", mode="apply",
                                          inputs={"workflow_file": WORKFLOW, "entries": [ENTRY]})
                with patch("speckit_pro_runner.helpers.registry.dispatch_helper") as dispatch:
                    result = handle_request(request)
                self.assertEqual("harm_halt_active", result["diagnostics"][0]["code"], result)
                dispatch.assert_not_called()
                self.assertEqual("input_error", self.call("read_only")["status"])

    def test_an_interrupted_publication_refuses_writes_and_resume(self) -> None:
        lock = self.root / ".specify/harm-halt/halt.lock"
        lock.mkdir(parents=True)
        request = SimpleNamespace(schema_version="1.0", request_id="pending", helper_id="decisions-list",
                                  operation="decisions-list", mode="apply", inputs={"workflow_file": WORKFLOW, "entries": [ENTRY]})
        with patch("speckit_pro_runner.helpers.registry.dispatch_helper") as dispatch:
            result = handle_request(request)
        self.assertEqual("harm_halt_active", result["diagnostics"][0]["code"], result)
        dispatch.assert_not_called()
        self.assertEqual("input_error", self.call("read_only")["status"])

    def test_a_concurrent_trigger_is_refused_before_it_can_replace_evidence(self) -> None:
        for second_reason in ("concurrent_writer", "identity_mismatch"):
            with self.subTest(second_reason=second_reason):
                self.setUp()
                entered, release = Event(), Event()
                publish = harm_halt.durable_json

                def delayed_publish(path: Path, record: dict[str, Any]) -> None:
                    if record["evidence"] == "first evidence":
                        entered.set()
                        if not release.wait(10):
                            raise RuntimeError("first publisher was not released")
                    publish(path, record)

                with patch.object(harm_halt, "durable_json", side_effect=delayed_publish), ThreadPoolExecutor() as pool:
                    first = pool.submit(harm_halt.record_halt, self.root, "identity_mismatch", "first evidence", SAFE_STATE)
                    try:
                        self.assertTrue(entered.wait(10), "first publisher did not start")
                        with self.assertRaisesRegex(ValueError, second_reason + ".*(locked|already stands)"):
                            harm_halt.record_halt(self.root, second_reason, "second evidence", SAFE_STATE)
                    finally:
                        release.set()
                        first.result(timeout=10)
                self.assertEqual("first evidence", self.read_only_data()["record"]["evidence"])


class HaltClearTokenTests(QuietTerminal):
    """Only the one-time token shown on the owner's terminal clears a standing halt (#1378)."""

    helper_id = harm_halt.HELPER_ID
    files = {WORKFLOW: "# Workflow\n"}

    def halt(self, evidence: str = "page hash differs") -> str:
        result = self.call("apply", action="halt", reason="tampering_or_forged_evidence", evidence=evidence,
                           last_safe_state=SAFE_STATE)
        self.assertEqual("ok", result["status"], result)
        return self.shown[-1]

    def clear(self, mode: str = "apply", **token: str) -> dict[str, Any]:
        return self.call(mode, action="clear", **token)

    def test_clear_with_the_right_token_resumes(self) -> None:
        token = self.halt()
        self.assertGreaterEqual(len(token), 40)
        cleared = self.clear(token=token)
        self.assertEqual("ok", cleared["status"], cleared)
        self.assertEqual((False, "allowed"), (cleared["data"]["halted"], cleared["data"]["resume"]))
        self.assertFalse((self.root / RECORD).exists())
        self.assertEqual("ok", HarmHaltTests.write_attempt(self)["status"])

    def test_wrong_missing_and_reused_tokens_refuse_and_the_halt_stands(self) -> None:
        first = self.halt()
        for attempt in ({"token": first[:-1] + ("A" if first[-1] != "A" else "B")}, {"token": ""}, {},
                        {"confirm_reason": "tampering_or_forged_evidence"}, {"token": 7}):
            with self.subTest(attempt=sorted(attempt)):
                self.assertEqual("input_error", self.clear(**attempt)["status"])
                self.assertEqual("refused", self.read_only_data()["resume"])
        self.assertEqual("ok", self.clear(token=first)["status"])
        self.assertEqual("input_error", self.clear(token=first)["status"], "a used token clears nothing")
        second = self.halt("second trigger")
        self.assertNotEqual(first, second)
        self.assertEqual("input_error", self.clear(token=first)["status"])
        self.assertEqual("second trigger", self.read_only_data()["record"]["evidence"])
        self.assertEqual("harm_halt_active", HarmHaltTests.write_attempt(self)["diagnostics"][0]["code"])

    def test_dry_run_clear_reports_without_changing_state(self) -> None:
        token = self.halt()
        before = (self.root / RECORD).read_bytes()
        for candidate, expected in ((token, True), ("wrong", False)):
            with self.subTest(expected=expected):
                planned = self.clear("dry_run", token=candidate)
                self.assertEqual("ok", planned["status"], planned)
                self.assertEqual((expected, True, "refused"), (planned["data"]["would_clear"],
                                 planned["data"]["halted"], planned["data"]["resume"]))
                self.assertEqual(before, (self.root / RECORD).read_bytes())
        self.assertEqual("ok", self.clear(token=token)["status"], "a dry run does not spend the token")

    def test_a_record_without_a_valid_token_digest_refuses_every_clear(self) -> None:
        for stored in (None, "", "\u00e9" * 64, "A" * 64, 7):
            with self.subTest(stored=stored):
                self.setUp()
                self.halt()
                record = json.loads((self.root / RECORD).read_text(encoding="utf-8"))
                record.pop("clear_token_sha256")
                if stored is not None:
                    record["clear_token_sha256"] = stored
                (self.root / RECORD).write_text(json.dumps(record), encoding="utf-8")
                for mode in ("dry_run", "apply"):
                    self.assertEqual("input_error", self.clear(mode, token="anything")["status"])
                self.assertTrue((self.root / RECORD).exists())

    def run_runner(self, request: dict[str, Any]) -> str:
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "stdin", io.StringIO(json.dumps(request))), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            runner_main([])
        return stdout.getvalue() + stderr.getvalue()

    def test_the_documented_clear_request_clears(self) -> None:
        adr = (REPO / "docs/adr/0010-stop-policy-enforcement.md").read_text(encoding="utf-8")
        documented = json.loads(adr.split("```json\n", 1)[1].split("\n```", 1)[0])
        token = self.halt()
        documented["inputs"]["token"] = token
        self.assertIn('"resume":"allowed"', self.run_runner(documented))
        self.assertFalse((self.root / RECORD).exists())

    def test_no_agent_readable_path_exposes_the_token(self) -> None:
        fixture = json.loads((FIXTURES / "harm-halt.json").read_text(encoding="utf-8"))

        def request(mode: str, **inputs: Any) -> dict[str, Any]:
            return {**fixture, "mode": mode, "inputs": inputs}

        seen = self.run_runner(request("apply", action="halt", reason="secret_exposure", evidence="leak",
                                       last_safe_state=SAFE_STATE))
        token = self.shown[-1]
        seen += self.run_runner(request("read_only"))
        seen += self.run_runner(request("apply", action="clear", token=token + "x"))
        seen += self.run_runner(request("dry_run", action="clear", token=token))
        seen += self.run_runner(request("dry_run", action="clear", token=token + "x"))
        seen += self.run_runner({**request("apply", action="clear", token=token), "helper_id": "decisions-list"})
        stored = [path.read_bytes() for path in self.root.rglob("*") if path.is_file()]
        self.assertNotIn(token, seen)
        self.assertNotIn("clear_token_sha256", seen)
        self.assertFalse([blob for blob in stored if token.encode() in blob])
        self.assertIn("refused", seen)
        seen = self.run_runner(request("apply", action="clear", token=token))
        self.assertNotIn(token, seen)
        self.assertIn('"resume":"allowed"', seen)
        self.assertFalse([path for path in self.root.rglob("*") if path.is_file() and token.encode() in path.read_bytes()])


class OwnerTerminalTests(unittest.TestCase):
    """The token goes only to the outermost ancestor terminal, never to one the runner's own streams use."""

    def setUp(self) -> None:
        switch = patch.dict(os.environ)
        switch.start()
        self.addCleanup(switch.stop)
        os.environ.pop(harm_halt.TERMINAL_SWITCH, None)

    def terminal(self) -> tuple[int, str]:
        master, slave = os.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        return master, os.ttyname(slave)

    def drained(self, master: int) -> bytes:
        received = b""
        while select.select([master], [], [], 0.2)[0]:
            received += os.read(master, 4096)
        return received

    def table(self, rows: dict[int, tuple[int, str]]) -> Any:
        def row(pid: int) -> tuple[int, str]:
            if pid not in rows:
                raise OSError("ps could not read the process")
            return rows[pid]

        return patch.object(harm_halt, "process_row", side_effect=row)

    def test_the_outermost_ancestor_terminal_receives_the_token(self) -> None:
        outer, outer_path = self.terminal()
        inner, inner_path = self.terminal()
        rows = {os.getpid(): (10, "??"), 10: (11, inner_path.removeprefix("/dev/")),
                11: (12, outer_path.removeprefix("/dev/")), 12: (1, "??")}
        with self.table(rows), patch.object(harm_halt, "runner_terminals", return_value=set()):
            self.assertTrue(harm_halt.show_on_owner_terminal("tok-123"))
        self.assertIn(b"tok-123", self.drained(outer))
        self.assertNotIn(b"tok-123", self.drained(inner))

    def test_a_terminal_the_runner_uses_or_the_suite_switch_withholds_the_token(self) -> None:
        for case in ("runner_stream", "suite_switch"):
            with self.subTest(case=case):
                outer, outer_path = self.terminal()
                own = {os.stat(outer_path).st_rdev} if case == "runner_stream" else set()
                if case == "suite_switch":
                    os.environ[harm_halt.TERMINAL_SWITCH] = "off"
                rows = {os.getpid(): (10, outer_path.removeprefix("/dev/")), 10: (1, "??")}
                with self.table(rows), patch.object(harm_halt, "runner_terminals", return_value=own):
                    self.assertFalse(harm_halt.show_on_owner_terminal("tok-123"))
                self.assertNotIn(b"tok-123", self.drained(outer))

    def test_no_terminal_or_an_unreadable_process_table_delivers_nothing(self) -> None:
        for rows in ({os.getpid(): (1, "??")}, {}, {os.getpid(): (10, "../etc/passwd"), 10: (1, "??")}):
            with self.subTest(rows=rows), self.table(rows), patch.object(harm_halt, "runner_terminals", return_value=set()):
                self.assertFalse(harm_halt.show_on_owner_terminal("tok-123"))


def build_suite() -> unittest.TestSuite:
    return unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                              for case in (HarmHaltTests, HaltDispatchTests, HaltConcurrencyTests,
                                           HaltClearTokenTests, OwnerTerminalTests))


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-harm-halt"))
