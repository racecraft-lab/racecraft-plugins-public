#!/usr/bin/env python3
"""Guard: the plan-stage terminal step names only runner requests a user repository can run.

The terminal step runs in the user's repository, late in the plan stage, when the
orchestrator's context is largest. Each request the guidance names but does not
spell out, and each request that cannot run there, costs the orchestrator extra
turns hunting through references and runner source. The release-readiness gate
needs a SpecKit Pro source checkout, so its operations never belong here; the
packet producer owns the draft title's shape instead (GeneratedTitleScopeTests).
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
from speckit_pro_runner.gates.release import RELEASE_INPUT_FIELDS  # noqa: E402
from speckit_pro_runner.helpers.read_only import workflow_draft_pr_row  # noqa: E402
from speckit_pro_runner.helpers.registry import HELPERS, MUTATION_HELPERS  # noqa: E402
from speckit_pro_runner.workflow_stage import AUTOPILOT_BASIC_INFO_HEADING  # noqa: E402
from test_result import run_counted  # noqa: E402

HOSTS = ("claude", "codex")
START = re.compile(r"^#{3,4} Plan [Ss]tage: .*[Tt]erminal [Ss]tep\s*$", re.M)
END = re.compile(r"^#{2,3} Phase 7: Implement", re.M)
HELPER_ID = re.compile(r"helper_id=([a-z0-9-]+)|\"helper_id\": \"([a-z0-9-]+)\"")
CODE_SPAN = re.compile(r"`([a-z0-9-]+)`")
DRAFT_PR_ROW = re.compile(r"^\| \*\*Draft PR\*\* \|.*\|$", re.M)


def terminal_step(host: str) -> str:
    """The plan-stage terminal-step text `host` loads, from its heading to Phase 7."""
    text = (host_skill_root(host) / "speckit-autopilot" / "references" / "phase-execution.md").read_text(encoding="utf-8")
    start = START.search(text)
    if start is None:
        raise AssertionError(f"{host}: phase-execution.md has no plan-stage terminal-step heading")
    end = END.search(text, start.end())
    if end is None:
        raise AssertionError(f"{host}: phase-execution.md has no Phase 7 heading after the terminal step")
    return text[start.start():end.start()]


def named_helpers(text: str) -> set[str]:
    return {first or second for first, second in HELPER_ID.findall(text)}


class TerminalStepRequestTests(unittest.TestCase):
    def test_every_named_helper_is_registered(self) -> None:
        for host in HOSTS:
            names = named_helpers(terminal_step(host))
            self.assertTrue(names, f"{host}: the terminal step names no runner helper")
            for name in sorted(names):
                self.assertTrue(name in HELPERS or name in MUTATION_HELPERS,
                                f"{host}: the terminal step names unregistered helper {name!r}")

    def test_no_release_gate_operation_is_named(self) -> None:
        repo_only = set(RELEASE_INPUT_FIELDS)
        self.assertIn("validate-pr-title", repo_only)
        for host in HOSTS:
            spans = set(CODE_SPAN.findall(terminal_step(host))) | named_helpers(terminal_step(host))
            self.assertEqual(spans & repo_only, set(),
                             f"{host}: the terminal step names a release-gate operation, which needs a "
                             "SpecKit Pro source checkout and refuses in a user repository")

    def test_packet_validation_request_is_spelled_out(self) -> None:
        for host in HOSTS:
            text = terminal_step(host)
            self.assertIn("validate-pr-packet-read-only", named_helpers(text),
                          f"{host}: name the packet validator as a runner request")
            for condition in ("`data.stdout_json.status` is `passed`", "`data.stdout_json.pr_blocked` is false",
                              "`data.writes_state` is false"):
                self.assertIn(condition, text, f"{host}: state the packet validator's pass condition {condition!r}")

    def test_draft_pr_row_example_parses_as_the_runner_reads_it(self) -> None:
        for host in HOSTS:
            rows = DRAFT_PR_ROW.findall(terminal_step(host))
            self.assertTrue(rows, f"{host}: show the Draft PR row inline at the step that writes it")
            for row in rows:
                lines = [AUTOPILOT_BASIC_INFO_HEADING, "", "| Field | Value |", "|-------|-------|", row]
                parsed = workflow_draft_pr_row(lines)
                self.assertIsNotNone(parsed, f"{host}: the runner reads {row!r} as no Draft PR row")


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    return unittest.TestSuite([loader.loadTestsFromTestCase(TerminalStepRequestTests)])


def main() -> int:
    return run_counted(build_suite(), label="test-plan-terminal-step-requests")


if __name__ == "__main__":
    raise SystemExit(main())
