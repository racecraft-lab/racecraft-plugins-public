#!/usr/bin/env python3
"""Replay a Phase 6.5 autonomy-boundary receipt the way the Codex autopilot does.

The fixtures under `evals/fixtures/functional/autonomy-boundary-replay/` hold a
private `autonomy-boundary.v1` record template, the workflow and state it
belongs to, and the replays to run. The test builds the record's machine-local
roots under a repository created at run time, fills in its digests, writes it
owner-only under the git common directory, and publishes its
`autonomy-boundary-receipt.v1` projection in `autopilot-state.json`. Each replay
then does what a resume does: run the shipped phase-coverage validator with the
case's `--require-autonomy-boundary` and `--current-*` values. Under the full
guard the validator locates the private record by the state's
`execution_control.run_id` and checks that it still hashes to
`private_record_sha256`; the test recomputes that match independently.
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
FIXTURE_ROOT = TEST_ROOT / "evals" / "fixtures" / "functional" / "autonomy-boundary-replay"
sys.path.insert(0, str(TEST_ROOT / "lib"))

from test_result import run_counted  # noqa: E402
from autonomy_boundary_fixture import (  # noqa: E402
    AUTONOMY_RUN_ID as RUN_ID,
    autonomy_public_receipt,
    digest,
    write_autonomy_private_record,
)

VALIDATOR = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "scripts" / "validate-autopilot-phase-coverage.py"
EXECUTION_FIELDS = ("execution_environment", "sandbox_mode", "approval_reviewer", "writable_roots")
ACTION_FIELDS = ("category", "command_or_tool", "target", "effect", "execution_boundary_sha256")


def _fixture_json(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class AutonomyBoundaryReceiptReplayTests(unittest.TestCase):
    def stage(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        (root / "specs" / "demo").mkdir(parents=True)
        for name in ("plan.md", "tasks.md"):
            shutil.copyfile(FIXTURE_ROOT / name, root / "specs" / "demo" / name)
        shutil.copyfile(FIXTURE_ROOT / "workflow.md", root / "workflow.md")
        return root

    def roots(self, root: Path, value: object) -> object:
        if isinstance(value, dict):
            return {key: self.roots(root, item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.roots(root, item) for item in value]
        if isinstance(value, str) and value.startswith("$root:"):
            return str(root / value.split(":", 1)[1])
        return value

    def private_record(self, root: Path) -> dict:
        record = self.roots(root, _fixture_json("private-record.json"))
        for label, token in record["planning_fingerprints"].items():
            path = token.split(":", 1)[1]
            content = (root / path).read_bytes()
            record["planning_fingerprints"][label] = {
                "path": path, "sha256": digest(content), "size_bytes": len(content)}
        execution = record["execution_boundary"]
        execution["writable_roots"] = sorted(execution["writable_roots"])
        execution["sha256"] = digest({key: execution[key] for key in EXECUTION_FIELDS})
        for action in record["actions"]:
            action["execution_boundary_sha256"] = execution["sha256"]
            action["scope_sha256"] = digest({key: action[key] for key in ACTION_FIELDS})
            action["authorization"]["scope_sha256"] = action["scope_sha256"]
        return record

    def replay(self, case: dict, tamper: dict) -> tuple[bool, int, list[str]]:
        root = self.stage()
        record = self.private_record(root)
        receipt = autonomy_public_receipt(record)
        if case["private_record"] == "tampered":
            changed = copy.deepcopy(record)
            *parents, leaf = tamper["private_record_field"]
            target = changed
            for part in parents:
                target = target[part]
            target[leaf] = self.roots(root, tamper["private_record_value"])
            record = changed
        elif case["private_record"] == "receipt-rewritten":
            receipt["private_record_sha256"] = "sha256:" + "0" * 64
        private_path = write_autonomy_private_record(root, record, RUN_ID)
        if case["private_record"] == "missing":
            private_path.unlink()
        elif case["private_record"] == "unreadable":
            private_path.unlink()
            private_path.mkdir()
        elif case["private_record"] == "symlinked":
            decoy = private_path.with_name("decoy.json")
            private_path.rename(decoy)
            private_path.symlink_to(decoy)
        elif case["private_record"] == "unparseable":
            private_path.write_text("{not json\n", encoding="utf-8")
        state = _fixture_json("state.json")
        if case["private_record"] == "unlocatable":
            del state["execution_control"]
        if case["boundary"] == "receipt":
            state["autonomy_boundary"] = receipt
        (root / "autopilot-state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

        try:
            stored = json.loads(private_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            stored = None
        matches = stored is not None and digest(stored) == receipt["private_record_sha256"]
        if case["private_record"] in ("unlocatable", "symlinked"):
            matches = False
        command = [sys.executable, str(VALIDATOR), "--workflow", str(root / "workflow.md"),
                   "--state", str(root / "autopilot-state.json")]
        if case["require_autonomy_boundary"]:
            command.append("--require-autonomy-boundary")
        for flag, value in case["current"].items():
            command.extend([flag, value])
        for name in case["current_writable_roots"]:
            command.extend(["--current-writable-root", str(root / name)])
        command.extend(["--rule", "status-evidence"])
        completed = subprocess.run(command, text=True, capture_output=True,
                                   timeout=120, check=False, shell=False)
        report = json.loads(completed.stdout)
        errors = report["autonomy_boundary_errors"]
        for error in errors:
            self.assertNotIn(str(root), error)
            self.assertNotIn(RUN_ID, error)
        return matches, completed.returncode, errors

    def test_fixture_replays_against_the_shipped_validator(self) -> None:
        fixture = _fixture_json("replays.json")
        self.assertEqual(fixture["schema"], "autonomy-boundary-replay/v1")
        for case in fixture["cases"]:
            with self.subTest(case=case["id"]):
                matches, code, errors = self.replay(case, fixture["tamper"])
                expect = case["expect"]
                self.assertEqual(matches, expect["private_record_matches"])
                self.assertEqual(errors, expect["autonomy_boundary_errors"])
                self.assertEqual(code == 0, expect["passes"], errors)

    def test_replays_cover_every_omitted_flag_and_digest_mismatch(self) -> None:
        cases = _fixture_json("replays.json")["cases"]
        flags = {"--current-execution-environment", "--current-sandbox-mode",
                 "--current-approval-reviewer"}
        omitted = {flag for case in cases if case["require_autonomy_boundary"]
                   for flag in flags if flag not in case["current"]}
        self.assertEqual(omitted, flags)
        self.assertTrue(any(case["require_autonomy_boundary"] and not case["current_writable_roots"]
                            for case in cases))
        self.assertTrue(any(not case["expect"]["private_record_matches"] for case in cases))
        self.assertTrue(any("does not match the persisted execution boundary" in error
                            for case in cases for error in case["expect"]["autonomy_boundary_errors"]))

    def test_every_private_record_failure_fails_the_full_guard(self) -> None:
        cases = _fixture_json("replays.json")["cases"]
        modes = {case["private_record"] for case in cases
                 if case["require_autonomy_boundary"] and case["boundary"] == "receipt"
                 and not case["expect"]["passes"]}
        self.assertLessEqual(
            {"tampered", "receipt-rewritten", "missing", "unreadable", "symlinked", "unparseable",
             "unlocatable"},
            modes,
        )
        for case in cases:
            if case["boundary"] == "receipt" and not case["expect"]["private_record_matches"]:
                with self.subTest(case=case["id"]):
                    self.assertFalse(case["expect"]["passes"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AutonomyBoundaryReceiptReplayTests)
    raise SystemExit(run_counted(suite, label="test-autonomy-boundary-receipt-replay"))
