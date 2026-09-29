#!/usr/bin/env python3
"""Parity guard: autopilot guidance names only stop reasons the runner defines.

The runner owns the closed set of stop reasons (``stop_policy.STOP_REASONS``).
Guidance on both hosts names a reason with the marker ``stop_reason:<id>`` in an
inline code span. A guidance file that names an id outside the runner set fails
here, and so does a set member the shared reference does not state.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
sys.path.insert(0, str(TEST_DIR.parent / "lib"))
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))

from test_result import run_counted  # noqa: E402

CLAUDE_SKILL = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot"
CODEX_SKILL = REPO_ROOT / "speckit-pro" / "codex-skills" / "speckit-autopilot"
REFERENCE = CLAUDE_SKILL / "references" / "stop-policy.md"
MARKER = re.compile(r"`stop_reason:([^`\s]+)`")
CLASSES = {"authority", "exhausted", "harm_halt"}


def _guidance_files() -> list[Path]:
    files = sorted(CLAUDE_SKILL.rglob("*.md")) + sorted(CODEX_SKILL.rglob("*.md"))
    return [path for path in files if path.is_file()]


def _eval_files() -> list[Path]:
    """Eval expectation files and layer 6 and 7 fixtures, as text.

    The marker is a backticked ``stop_reason:<id>`` span, which does not occur in
    JSON or Markdown by accident, so a raw text scan has no false positives.
    """
    tests = REPO_ROOT / "tests" / "speckit-pro"
    roots = [tests / "layer3-functional" / "evals", tests / "layer3-functional" / "codex-evals",
             tests / "evals" / "catalog.json", tests / "layer2-trigger",
             tests / "layer6-integration", tests / "layer7-parity"]
    files: list[Path] = []
    for root in roots:
        found = [root] if root.is_file() else sorted(root.rglob("*")) if root.is_dir() else []
        files += [path for path in found if path.is_file() and path.suffix in {".json", ".md"}]
    return files


def _runner_set() -> dict[str, str]:
    from speckit_pro_runner.stop_policy import STOP_REASONS

    return dict(STOP_REASONS)


class StopReasonParityTests(unittest.TestCase):
    def test_every_named_reason_is_in_the_runner_set(self) -> None:
        known = _runner_set()
        for path in _guidance_files() + _eval_files():
            text = path.read_text(encoding="utf-8")
            for reason in MARKER.findall(text):
                self.assertIn(
                    reason,
                    known,
                    f"{path.relative_to(REPO_ROOT)} names stop reason {reason!r} "
                    "outside the runner set",
                )

    def test_eval_scan_reaches_the_expectation_files(self) -> None:
        files = _eval_files()
        self.assertIn("catalog.json", {path.name for path in files})
        hosts = {p.parent.name for p in files if p.name == "speckit-autopilot-evals.json"}
        self.assertEqual(hosts, {"evals", "codex-evals"}, "scan both hosts' evals")
        tests = REPO_ROOT / "tests" / "speckit-pro"
        self.assertTrue(any(tests / "layer2-trigger" in path.parents for path in files))

    def test_runner_set_is_closed_and_classified(self) -> None:
        known = _runner_set()
        self.assertTrue(known)
        self.assertEqual(set(known.values()), CLASSES)
        for reason in known:
            self.assertRegex(reason, r"^[a-z][a-z0-9_]*$")

    def test_shared_reference_states_every_reason_with_its_class(self) -> None:
        text = REFERENCE.read_text(encoding="utf-8")
        named = set(MARKER.findall(text))
        self.assertEqual(named, set(_runner_set()))
        for reason, stop_class in _runner_set().items():
            self.assertRegex(
                text,
                rf"`stop_reason:{reason}`[^\n]*\b{stop_class}\b",
                f"reference row for {reason} must name class {stop_class}",
            )

    def test_both_autopilot_skills_link_the_shared_reference(self) -> None:
        links = {
            CLAUDE_SKILL: "(./references/stop-policy.md)",
            CODEX_SKILL: "(../../skills/speckit-autopilot/references/stop-policy.md)",
        }
        for skill, link in links.items():
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertGreaterEqual(
                text.count(link), 2, f"{skill.parent.parent.name} skill must link it "
                "where stop behavior is introduced and in its references list"
            )

    def test_unknown_reason_fails_closed(self) -> None:
        from speckit_pro_runner.stop_policy import stop_class

        self.assertEqual(stop_class("secret_exposure"), "harm_halt")
        with self.assertRaises(ValueError):
            stop_class("made_up_reason")

    def test_an_unknown_reason_is_detected(self) -> None:
        sample = "Halt with `stop_reason:made_up_reason` now."
        self.assertNotIn(MARKER.findall(sample)[0], _runner_set())


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(StopReasonParityTests)


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-stop-reason-parity")


if __name__ == "__main__":
    raise SystemExit(main())
