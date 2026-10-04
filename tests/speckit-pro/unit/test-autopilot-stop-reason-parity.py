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


def _h4_body(text: str, title: str) -> str:
    """The lines under the first `####` heading whose title contains `title`.

    A `####` line inside a code fence is content, not a heading.
    """
    kept: list[str] = []
    inside = fenced = False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if line.startswith("#### ") and not fenced:
            if inside:
                break
            inside = title in line
        elif inside:
            kept.append(line)
    if not kept:
        raise ValueError(f"no section titled like {title!r}")
    return "\n".join(kept)


def _printed(reason: str) -> re.Pattern[str]:
    """An instruction to print the literal marker `stop_reason:<reason>`."""
    return re.compile(rf"\b[Pp]rint\b[^\n]*`stop_reason:{reason}`")


# The plan-stage stop report maps each shape that can end a plan-stage run to its marker.
PLAN_STAGE_SHAPES = {
    "Emission ran": "plan_stage_boundary",
    "The stage-boundary commit or a PR-packet step failed": "plan_stage_boundary",
    "The pull request could not be opened": "plan_stage_boundary",
    "The branch push failed": "plan_stage_boundary",
    "The bookkeeping commit or its push failed": "plan_stage_boundary",
    "The gate blocked in strict mode": "strict_confidence_opt_in",
    "The recorded pull request is closed or merged": "reopen_closed_pr",
    "The recorded pull request is missing, or several open pull requests match": "ambiguous_pr_record",
    "The PR tool is absent or unauthenticated": "tool_unavailable",
    "An artifact-integrity failure": "integrity_failure",
    "A push requires protected-branch authority": "protected_push",
}


PRINT_RULE = re.compile(r"[Pp]rint exactly one marker for that reason,\s+copied verbatim from the Reason column, as the last line")


class StopReasonPrintTests(unittest.TestCase):
    """The canary judges a run by the marker its final message prints.

    Naming a reason is not enough: each host's guidance must tell the agent
    to print it.
    """

    def _phase_execution(self, host: str) -> str:
        return (HOST_SKILLS[host] / "references" / "phase-execution.md").read_text(encoding="utf-8")

    def test_plan_stage_terminal_step_prints_the_boundary_reason(self) -> None:
        for host in HOST_SKILLS:
            steps = _h4_body(self._phase_execution(host), "terminal-step sequence")
            self.assertRegex(
                steps,
                re.compile(r"^\d+\. Print the stop report, then print exactly one `stop_reason:plan_stage_boundary` as the last line of your final message, and stop\.", re.M),
                f"{host}: a numbered terminal step must print the plan stage boundary reason",
            )

    def _assert_stop_report(self, report: str, host: str) -> None:
        self.assertIn("**Print exactly one stop reason as the last line of the final message**", report)
        self.assertIn("Specific stop-policy reasons take precedence over the general report shapes", report)
        rows = [line.split("|")[1:3] for line in report.splitlines() if line.startswith("| ")]
        for shape, reason in PLAN_STAGE_SHAPES.items():
            self.assertIn(reason, _runner_set())
            matches = [cell for label, cell in rows if label.strip() == shape]
            self.assertEqual(len(matches), 1, f"{host}: one mapping for {shape}")
            self.assertEqual(MARKER.findall(matches[0]), [reason], f"{host}: one registered marker for {shape}")
            self.assertRegex(matches[0], _printed(reason))

    def test_plan_stage_stop_report_prints_each_shape_marker(self) -> None:
        for host in HOST_SKILLS:
            self._assert_stop_report(_h4_body(self._phase_execution(host), "The plan-stage stop report"), host)

    def test_stop_report_guard_rejects_duplicates_trailing_output_and_wrong_mappings(self) -> None:
        for host in HOST_SKILLS:
            report = _h4_body(self._phase_execution(host), "The plan-stage stop report")
            self._assert_stop_report(report, host)
            mutations = (
                report.replace("Print exactly one stop reason", "Print two stop reasons"),
                report.replace("as the last line of the final message", "before the resume command"),
                report.replace("Print `stop_reason:tool_unavailable`", "Print `stop_reason:plan_stage_boundary`"),
                report.replace("Print `stop_reason:tool_unavailable`", "Print `stop_reason:tool_unavailable` and `stop_reason:plan_stage_boundary`"),
            )
            for index, mutated in enumerate(mutations):
                with self.subTest(host=host, mutation=index), self.assertRaises(AssertionError):
                    self._assert_stop_report(mutated, host)

    def test_early_terminal_failure_report_preserves_actual_commit_state(self) -> None:
        for host in HOST_SKILLS:
            report = _h4_body(self._phase_execution(host), "The plan-stage stop report")
            self.assertIn("**The stage-boundary commit or a PR-packet step failed.**", report)
            self.assertIn("Do not claim the boundary or packet was committed when that step failed", report)

    def test_stop_policy_tells_every_host_to_print_the_marker_of_a_run_ending_stop(self) -> None:
        policies = {host: skill / "references" / "stop-policy.md" for host, skill in HOST_SKILLS.items()}
        missing = [host for host, path in policies.items() if not PRINT_RULE.search(path.read_text(encoding="utf-8"))]
        self.assertEqual(missing, [], "hosts whose stop-policy lacks the print rule")


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    return unittest.TestSuite([loader.loadTestsFromTestCase(StopReasonParityTests),
                               loader.loadTestsFromTestCase(StopReasonPrintTests)])


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-stop-reason-parity")


if __name__ == "__main__":
    raise SystemExit(main())
