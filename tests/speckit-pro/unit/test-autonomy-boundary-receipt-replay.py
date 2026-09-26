#!/usr/bin/env python3
"""Replay a Phase 6.5 autonomy-boundary receipt the way the Codex autopilot does.

The receipt in `autopilot-state.json` is the public projection of a private
record kept under the git common directory. A resume replays it in two steps:
confirm the private record still hashes to `private_record_sha256`, then run the
real phase-coverage validator with `--require-autonomy-boundary` and every
`--current-*` value. Every machine-local path here is built at run time.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
UNIT_ROOT = REPO_ROOT / "tests" / "speckit-pro" / "unit"
sys.path.insert(0, str(REPO_ROOT / "tests" / "speckit-pro" / "lib"))

from test_result import run_counted  # noqa: E402


def _load_coverage_tests() -> object:
    """Reuse the record, receipt, workflow, and state builders instead of copying them."""
    path = UNIT_ROOT / "test-autopilot-phase-coverage.py"
    spec = importlib.util.spec_from_file_location("autopilot_phase_coverage_builders", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load the phase-coverage test builders")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILDERS = _load_coverage_tests()
VALIDATOR = BUILDERS.VALIDATOR
canonical_sha256 = BUILDERS.VALIDATOR_MODULE._canonical_json_sha256
RUN_ID = "0" * 32
CURRENT = {
    "--current-execution-environment": "local",
    "--current-sandbox-mode": "workspace-write",
    "--current-approval-reviewer": "auto_review",
}


class AutonomyBoundaryReceiptReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / ".git").mkdir()
        self.roots = [str(self.root / "checkout"), str(Path(tempfile.gettempdir()).resolve())]
        self.record = BUILDERS.autonomy_private_record(self.root, self.roots)
        self.receipt = BUILDERS.autonomy_public_receipt(self.record)
        self.private_path = self.write_private_record(self.record)
        (self.root / "workflow.md").write_text(BUILDERS.workflow_text(), encoding="utf-8")
        self.write_state(self.receipt)

    def write_private_record(self, record: dict[str, object]) -> Path:
        directory = self.root / ".git" / "speckit-pro" / "autonomy-boundary"
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = directory / f"{RUN_ID}.json"
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        os.chmod(path, 0o600)
        return path

    def write_state(self, boundary: object) -> None:
        state = BUILDERS.state_json()
        state["workflow_file"] = "workflow.md"
        state["stage"] = "implement"
        if boundary is not None:
            state["autonomy_boundary"] = boundary
        (self.root / "autopilot-state.json").write_text(
            json.dumps(state, indent=2) + "\n", encoding="utf-8")

    def private_record_matches(self) -> bool:
        record = json.loads(self.private_path.read_text(encoding="utf-8"))
        return canonical_sha256(record) == self.receipt["private_record_sha256"]

    def guard(self, *, require: bool = True, current: dict[str, str] | None = None,
              roots: list[str] | None = None) -> tuple[int, list[str]]:
        command = [sys.executable, str(VALIDATOR),
                   "--workflow", str(self.root / "workflow.md"),
                   "--state", str(self.root / "autopilot-state.json")]
        if require:
            command.append("--require-autonomy-boundary")
        for flag, value in (CURRENT if current is None else current).items():
            command.extend([flag, value])
        for root in (list(reversed(self.roots)) if roots is None else roots):
            command.extend(["--current-writable-root", root])
        command.extend(["--rule", "status-evidence"])
        completed = subprocess.run(command, text=True, capture_output=True,
                                   timeout=120, check=False, shell=False)
        report = json.loads(completed.stdout)
        return completed.returncode, report["autonomy_boundary_errors"]

    def test_receipt_replays_under_the_full_guard(self) -> None:
        self.assertTrue(self.private_record_matches())
        code, errors = self.guard()
        self.assertEqual(errors, [])
        self.assertEqual(code, 0)

    def test_each_omitted_current_value_fails_the_full_guard(self) -> None:
        for flag in CURRENT:
            with self.subTest(flag=flag):
                partial = {key: value for key, value in CURRENT.items() if key != flag}
                code, errors = self.guard(current=partial)
                self.assertNotEqual(code, 0)
                self.assertIn("current execution boundary is incomplete or malformed", errors)
        code, errors = self.guard(roots=[])
        self.assertNotEqual(code, 0)
        self.assertIn("current execution boundary writable_roots are incomplete or malformed", errors)
        code, errors = self.guard(current={}, roots=[])
        self.assertNotEqual(code, 0)
        self.assertIn("current execution boundary is unavailable", errors)

    def test_dropping_the_require_flag_hides_a_missing_boundary(self) -> None:
        self.write_state(None)
        code, errors = self.guard(current={}, roots=[])
        self.assertNotEqual(code, 0)
        self.assertIn(
            "autopilot_state.autonomy_boundary is required before this active run can reach Phase 7",
            errors,
        )
        # The weakened call passes on nothing; only the full guard proves a boundary.
        code, errors = self.guard(require=False, current={}, roots=[])
        self.assertEqual((code, errors), (0, []))

    def test_execution_boundary_digest_mismatch_fails_the_full_guard(self) -> None:
        for label, roots in (
            ("dropped root", self.roots[:1]),
            ("added root", [*self.roots, str(self.root / "elsewhere")]),
        ):
            with self.subTest(label):
                code, errors = self.guard(roots=roots)
                self.assertNotEqual(code, 0)
                self.assertIn(
                    "current execution boundary does not match the persisted execution boundary",
                    errors,
                )
        code, errors = self.guard(current={**CURRENT, "--current-sandbox-mode": "danger-full-access"})
        self.assertNotEqual(code, 0)
        self.assertIn(
            "current execution boundary does not match the persisted execution boundary", errors)

    def test_private_record_digest_mismatch_is_caught_before_the_guard(self) -> None:
        # The validator never sees the private record, so this check is the
        # documented agent-side step; the guard alone still passes the receipt.
        changed = json.loads(json.dumps(self.record))
        changed["actions"][0]["target"] = str(self.root / "checkout" / "other-settings.json")
        self.private_path = self.write_private_record(changed)
        self.assertFalse(self.private_record_matches())
        self.assertEqual(self.guard(), (0, []))

        self.private_path = self.write_private_record(self.record)
        self.receipt = {**self.receipt, "private_record_sha256": "sha256:" + "0" * 64}
        self.write_state(self.receipt)
        self.assertFalse(self.private_record_matches())


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AutonomyBoundaryReceiptReplayTests)
    raise SystemExit(run_counted(suite, label="test-autonomy-boundary-receipt-replay"))
