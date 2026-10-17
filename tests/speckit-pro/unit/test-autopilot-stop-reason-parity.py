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
    files += [host_skill_root(host) / "speckit-scaffold-spec" / "SKILL.md" for host in HOST_SKILLS]
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

        for harm in ("secret_exposure", "tampering_or_forged_evidence", "identity_mismatch", "concurrent_writer"):
            self.assertEqual(stop_class(harm), "harm_halt")
        self.assertEqual({r for r, c in _runner_set().items() if c == "harm_halt"},
                         {"secret_exposure", "tampering_or_forged_evidence", "identity_mismatch", "concurrent_writer"})
        with self.assertRaises(ValueError):
            stop_class("made_up_reason")

    def test_an_unknown_reason_is_detected(self) -> None:
        sample = "Halt with `stop_reason:made_up_reason` now."
        self.assertNotIn(MARKER.findall(sample)[0], _runner_set())


class RunEndRegistryTests(unittest.TestCase):
    """The reference tables state the registry entry for entry, and the registry alone decides what may end a run."""

    def test_reference_tables_match_the_registry_entry_for_entry(self) -> None:
        from speckit_pro_runner.stop_policy import END_STATES

        text = REFERENCE.read_text(encoding="utf-8")
        reasons = dict(re.findall(r"(?m)^\| `stop_reason:([^`]+)` \| (\w+) \|", text))
        self.assertEqual(reasons, _runner_set())
        ends = dict(re.findall(r"(?m)^\| `([a-z_]+)` \| (terminal|interrupt) \|", text))
        self.assertEqual(ends, dict(END_STATES))

    def test_only_an_end_state_or_a_harm_halt_may_end_a_run(self) -> None:
        from speckit_pro_runner.stop_policy import END_STATES, may_end

        for state in END_STATES:
            self.assertTrue(may_end(state), state)
        for reason, stop_class in _runner_set().items():
            self.assertEqual(may_end(reason), stop_class == "harm_halt", reason)
        self.assertEqual(set(END_STATES.values()), {"terminal", "interrupt"})
        self.assertFalse(may_end("integrity_failure"), "a removed reason is unregistered, so it fails closed")
        self.assertFalse(may_end("made_up_reason"))


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
    "An artifact-integrity failure": "tampering_or_forged_evidence",
    "A push requires protected-branch authority": "protected_push",
}


PRINT_RULE = re.compile(r"[Pp]rint exactly one marker for that reason,\s+copied verbatim from the Reason column, as the last line")


class ScaffoldStopReasonPrintTests(unittest.TestCase):
    def test_scaffold_completion_prints_one_registered_authority_reason_on_both_hosts(self) -> None:
        from speckit_pro_runner.stop_policy import stop_class

        self.assertEqual(stop_class("scaffold_complete"), "authority")
        scaffold_files = [path for path in _guidance_files() if path.parent.name == "speckit-scaffold-spec"]
        self.assertEqual(len(scaffold_files), 2, "scan both rendered scaffold hosts")
        for path in scaffold_files:
            section = re.search(r"(?ms)^### 10\. Closing Report\n(.*?)(?=^## Failure Handling)",
                                path.read_text(encoding="utf-8"))
            self.assertIsNotNone(section, path)
            closing = section.group(1)
            self.assertRegex(closing, _printed("scaffold_complete"))
            self.assertIn("as the last line of the final message", closing)
            self.assertIn("Do not print this marker on an incomplete or failed scaffold", closing)


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


SCAFFOLD_SKILLS = {host: host_skill_root(host) / "speckit-scaffold-spec" for host in ("claude", "codex")}


class ScaffoldOlderCliStopTests(unittest.TestCase):
    """Answers-file scaffold stops on an older SpecKit CLI instead of asking to repair it."""

    def _step_zero(self, host: str) -> str:
        text = (SCAFFOLD_SKILLS[host] / "SKILL.md").read_text(encoding="utf-8")
        match = re.search(r"### 0\. Ensure SpecKit CLI(.*?)### 1\. ", text, re.S)
        self.assertIsNotNone(match, f"{host}: scaffold Step 0 section")
        return " ".join(match.group(1).split()) if match else ""

    def test_older_cli_is_a_registered_authority_stop(self) -> None:
        self.assertEqual(_runner_set().get("speckit_cli_older"), "authority")

    def test_both_hosts_stop_without_a_question_and_print_the_marker(self) -> None:
        for host in SCAFFOLD_SKILLS:
            step = self._step_zero(host)
            self.assertRegex(step, r"`older` and the invocation has `--answers-file`", host)
            self.assertRegex(step, _printed("speckit_cli_older"), host)
            for field in ("spec_kit.installed_version", "spec_kit.pinned_version"):
                self.assertIn(field, step, f"{host}: the stop message names {field}")
            self.assertRegex(step, r"without (?:asking|a question)", host)

    def test_interactive_older_cli_still_offers_the_repair(self) -> None:
        for host in SCAFFOLD_SKILLS:
            self.assertIn("offer the operator `install_argv`", self._step_zero(host), host)


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    return unittest.TestSuite([loader.loadTestsFromTestCase(StopReasonParityTests),
                               loader.loadTestsFromTestCase(RunEndRegistryTests),
                               loader.loadTestsFromTestCase(ScaffoldStopReasonPrintTests),
                               loader.loadTestsFromTestCase(StopReasonPrintTests),
                               loader.loadTestsFromTestCase(ScaffoldOlderCliStopTests)])


def main() -> int:
    return run_counted(build_suite(), label="test-autopilot-stop-reason-parity")


if __name__ == "__main__":
    raise SystemExit(main())
