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

from host_skill_views import host_skill_root  # noqa: E402
from test_result import run_counted  # noqa: E402

# One shared source renders each host's view; guidance is read per host.
HOST_SKILLS = {host: host_skill_root(host) / "speckit-autopilot" for host in ("claude", "codex")}
REFERENCE = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "references" / "stop-policy.md"
MARKER = re.compile(r"`stop_reason:([^`\s]+)`")
CLASSES = {"authority", "exhausted", "harm_halt"}


def _guidance_files() -> list[Path]:
    files = [path for skill in HOST_SKILLS.values() for path in sorted(skill.rglob("*.md"))]
    return [path for path in files if path.is_file()]


def _label(path: Path) -> str:
    """Name a file for a failure message; rendered views live outside the repository."""
    return path.relative_to(REPO_ROOT).as_posix() if path.is_relative_to(REPO_ROOT) else path.as_posix()


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
                    f"{_label(path)} names stop reason {reason!r} "
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
        for host, skill in HOST_SKILLS.items():
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertGreaterEqual(
                text.count("(./references/stop-policy.md)"), 2, f"{host} skill must link it "
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


def _section(text: str, heading: str) -> str:
    """The body of the `####` section whose heading contains `heading`."""
    match = re.search(rf"^#### [^\n]*{re.escape(heading)}[^\n]*\n(.*?)(?=^#### |\Z)", text, re.S | re.M)
    assert match, f"no section titled like {heading!r}"
    return match.group(1)


def _printed(reason: str) -> re.Pattern[str]:
    """An instruction to print the literal marker `stop_reason:<reason>`."""
    return re.compile(rf"\b[Pp]rint\b[^\n]*`stop_reason:{reason}`")


class StopReasonPrintTests(unittest.TestCase):
    """The canary judges a run by the marker its final message prints.

    Naming a reason is not enough: each host's guidance must tell the agent
    to print it.
    """

    def _phase_execution(self, host: str) -> str:
        return (HOST_SKILLS[host] / "references" / "phase-execution.md").read_text(encoding="utf-8")

    def test_plan_stage_terminal_step_prints_the_boundary_reason(self) -> None:
        for host in HOST_SKILLS:
            steps = _section(self._phase_execution(host), "terminal-step sequence")
            self.assertRegex(
                steps,
                re.compile(rf"^\d+\. [^\n]*\b[Pp]rint\b[^\n]*`stop_reason:plan_stage_boundary`", re.M),
                f"{host}: a numbered terminal step must print the plan stage boundary reason",
            )

    def test_plan_stage_stop_report_prints_the_boundary_reason(self) -> None:
        for host in HOST_SKILLS:
            report = _section(self._phase_execution(host), "The plan-stage stop report")
            self.assertRegex(report, _printed("plan_stage_boundary"), f"{host}: stop report")

    def test_draft_description_resume_block_carries_the_boundary_reason(self) -> None:
        for host in HOST_SKILLS:
            body = _section(self._phase_execution(host), "The draft description")
            self.assertIn("`stop_reason:plan_stage_boundary`", body, f"{host}: draft description")

    def test_stop_policy_tells_every_host_to_print_each_registered_reason(self) -> None:
        for host, skill in HOST_SKILLS.items():
            text = (skill / "references" / "stop-policy.md").read_text(encoding="utf-8")
            self.assertRegex(text, r"[Pp]rint the marker\s+\(`stop_reason:` followed by the id[^)]*\) as the last line", f"{host}: print rule")
            for reason in _runner_set():
                self.assertRegex(
                    text,
                    re.compile(rf"^\| `stop_reason:{reason}` \|", re.M),
                    f"{host}: stop-policy must list {reason} so the print rule covers it",
                )


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    return unittest.TestSuite([loader.loadTestsFromTestCase(StopReasonParityTests),
                               loader.loadTestsFromTestCase(StopReasonPrintTests)])


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-stop-reason-parity")


if __name__ == "__main__":
    raise SystemExit(main())
