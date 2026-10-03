#!/usr/bin/env python3
"""Contract tests for the phase lock: the PR check, the open-phase file and the label swap."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from script_loader import load_script  # noqa: E402
from test_result import run_counted  # noqa: E402

phase_lock = load_script("phase_lock", REPO_ROOT / "scripts" / "phase-lock.py")
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
DONE = {"hasNextPage": False}


def labels(*names: str) -> dict[str, Any]:
    return {"pageInfo": DONE, "nodes": [{"name": name} for name in names]}


def pr_payload(*issues: tuple[int, list[str]], main_phase: str | None = None) -> dict[str, Any]:
    """A GraphQL response for a PR that closes ``issues`` (number, labels)."""
    closing = {"pageInfo": DONE, "nodes": [{"number": n, "labels": labels(*names)} for n, names in issues]}
    blob = None if main_phase is None else {"text": main_phase + "\n"}
    return {"data": {"repository": {"object": blob, "pullRequest": {"closingIssuesReferences": closing}}}}


class PhaseLockCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.open_phase_file = Path(self.enterContext(tempfile.TemporaryDirectory())) / "open-phase"

    def check(self, payload: Any, open_phase: str | None = "phase-1") -> int:
        if open_phase is not None:
            self.open_phase_file.write_text(open_phase + "\n", encoding="utf-8")
        return phase_lock.check_pr("owner/repo", 7, open_phase_file=self.open_phase_file, api=lambda _: payload)

    def test_closing_a_later_phase_issue_fails(self) -> None:
        self.assertEqual(self.check(pr_payload((12, ["phase-2"]))), 1)

    def test_closing_an_open_or_earlier_unlocked_issue_passes(self) -> None:
        payload = pr_payload((11, ["phase-1", "ready-for-agent"]), (3, ["phase-0"]), (4, ["bug"]))
        self.assertEqual(self.check(payload), 0)

    def test_closing_a_still_locked_issue_fails_whatever_its_phase(self) -> None:
        for names in (["phase-locked"], ["phase-1", "phase-locked"]):
            self.assertEqual(self.check(pr_payload((12, names))), 1, names)

    def test_part_d_is_after_phase_5(self) -> None:
        self.assertEqual(self.check(pr_payload((9, ["part-d"])), open_phase="phase-5"), 1)

    def test_pr_cannot_open_a_phase_the_default_branch_keeps_locked(self) -> None:
        self.assertEqual(self.check(pr_payload((12, ["phase-2"]), main_phase="phase-1"), open_phase="phase-2"), 1)

    def test_missing_unreadable_or_unknown_open_phase_fails_closed(self) -> None:
        payload = pr_payload((11, ["phase-1"]))
        with self.assertRaises(phase_lock.PhaseLockError):
            self.check(payload, open_phase=None)
        self.open_phase_file.mkdir()
        with self.assertRaises(phase_lock.PhaseLockError):
            self.check(payload, open_phase=None)
        self.open_phase_file.rmdir()
        for text in ("", "phase-9", "phase-1\nphase-2"):
            with self.assertRaises(phase_lock.PhaseLockError, msg=text):
                self.check(payload, open_phase=text)

    def test_missing_or_truncated_github_evidence_fails_closed(self) -> None:
        truncated = pr_payload((11, ["phase-1"]))
        truncated["data"]["repository"]["pullRequest"]["closingIssuesReferences"]["pageInfo"] = {"hasNextPage": True}
        for payload in (truncated, {"data": None}, {"data": {"repository": None}}, None):
            with self.assertRaises(phase_lock.PhaseLockError, msg=payload):
                self.check(payload)

    def test_main_exits_one_on_any_error(self) -> None:
        env = {"GITHUB_REPOSITORY": "owner/repo", "PR_NUMBER": "7"}
        failure = phase_lock.PhaseLockError("gh api failed")
        with mock.patch.dict(os.environ, env), mock.patch.object(phase_lock, "check_pr", side_effect=failure):
            self.assertEqual(phase_lock.main(["check-pr"]), 1)
        with mock.patch.dict(os.environ, {**env, "PR_NUMBER": "seven"}):
            self.assertEqual(phase_lock.main(["check-pr"]), 1)


class UnlockTests(unittest.TestCase):
    HUMAN = "## Notes\n\n- Pickup label when unlocked: ready-for-human\n"
    ISSUES = [
        {"number": 1, "body": "", "labels": [{"name": "phase-1"}, {"name": "phase-locked"}]},
        {"number": 2, "body": HUMAN, "labels": [{"name": "phase-1"}, {"name": "phase-locked"}, {"name": "bug"}]},
        {"number": 3, "body": "", "labels": [{"name": "phase-2"}, {"name": "phase-locked"}]},
        {"number": 4, "body": "", "labels": [{"name": "phase-1"}, {"name": "ready-for-agent"}]},
        {"number": 5, "body": "", "labels": [{"name": "phase-locked"}]},
        {"number": 6, "body": "", "labels": [{"name": "phase-0"}, {"name": "phase-locked"}]},
    ]

    def test_unlocks_every_locked_issue_up_to_the_open_phase_with_its_pickup_label(self) -> None:
        self.assertEqual(
            phase_lock.unlock_plan(self.ISSUES, "phase-1"),
            [(1, ["phase-1", "ready-for-agent"]), (2, ["bug", "phase-1", "ready-for-human"]),
             (6, ["phase-0", "ready-for-agent"])],
        )

    def test_unknown_pickup_label_fails_closed(self) -> None:
        issue = {**self.ISSUES[0], "body": "Pickup label when unlocked: ready-for-humans"}
        with self.assertRaises(phase_lock.PhaseLockError):
            phase_lock.unlock_plan([issue], "phase-1")

    def test_unlock_replaces_each_label_set_in_one_call(self) -> None:
        calls: list[list[str]] = []

        def api(argv: Any) -> Any:
            calls.append(list(argv))
            return self.ISSUES[:2] if argv[0] == "issue" else []

        with tempfile.TemporaryDirectory() as tmp:
            open_phase_file = Path(tmp) / "open-phase"
            open_phase_file.write_text("phase-1\n", encoding="utf-8")
            self.assertEqual(phase_lock.unlock("owner/repo", open_phase_file=open_phase_file, api=api), 0)
            self.assertEqual(calls[1], ["api", "-X", "PUT", "repos/owner/repo/issues/1/labels",
                                        "-f", "labels[]=phase-1", "-f", "labels[]=ready-for-agent"])
            self.assertEqual(len(calls), 3)
            with self.assertRaises(phase_lock.PhaseLockError):
                phase_lock.unlock("owner/repo", open_phase_file=open_phase_file, api=lambda _: [{}] * 500)


class WiringTests(unittest.TestCase):
    WIRING = {
        "phase-lock.yml": ("issues: read", "pull-requests: read", "run: python3 scripts/phase-lock.py check-pr"),
        "phase-unlock.yml": ("branches: [main]", "paths: [.github/open-phase]", "run: python3 scripts/phase-lock.py unlock"),
    }

    def test_workflows_run_the_check_on_prs_and_the_unlock_on_main(self) -> None:
        for workflow, needles in self.WIRING.items():
            text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
            for needle in needles:
                self.assertIn(needle, text, workflow)

    def test_tracked_open_phase_file_is_valid(self) -> None:
        self.assertIn(phase_lock.read_open_phase(phase_lock.OPEN_PHASE_FILE), phase_lock.PHASES)


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    return unittest.TestSuite(loader.loadTestsFromTestCase(case) for case in (PhaseLockCheckTests, UnlockTests, WiringTests))


def main() -> int:
    return run_counted(build_suite(), label="test-phase-lock")


if __name__ == "__main__":
    raise SystemExit(main())
