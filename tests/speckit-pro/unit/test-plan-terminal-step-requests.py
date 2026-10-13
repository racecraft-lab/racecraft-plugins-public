#!/usr/bin/env python3
"""Guard: the plan-stage terminal step names only runner requests a user repository can run.

The terminal step runs in the user's repository, late in the plan stage, when the
orchestrator's context is largest. Each request the guidance names but does not
spell out, and each request that cannot run there, costs the orchestrator extra
turns hunting through references and runner source. The release-readiness gate
needs a SpecKit Pro source checkout, so its operations never belong here; the
finish-plan-stage helper owns the draft title and packet (test-plan-stage-terminal).
"""

from __future__ import annotations

import json
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
from speckit_pro_runner.helpers.plan_stage_terminal import INPUTS  # noqa: E402
from speckit_pro_runner.helpers.read_only import workflow_draft_pr_row  # noqa: E402
from speckit_pro_runner.helpers.registry import HELPERS, MUTATION_HELPERS  # noqa: E402
from speckit_pro_runner.workflow_stage import AUTOPILOT_BASIC_INFO_HEADING  # noqa: E402
from test_result import run_counted  # noqa: E402

HOSTS = ("claude", "codex")
START = re.compile(r"^#{3,4} Plan [Ss]tage: .*[Tt]erminal [Ss]tep\s*$", re.M)
END = re.compile(r"^#{2,3} Phase 7: Implement", re.M)
HELPER_ID = re.compile(r"helper_id=([a-z0-9-]+)|\"helper_id\": \"([a-z0-9-]+)\"")
SEQUENCE_HEADING = "Draft-PR emission: the terminal-step sequence"
FINISH_REQUEST = re.compile(r'```json\n(\{\n  "schema_version": "1\.0",\n  "request_id": "plan-stage-terminal".*?)\n```', re.S)
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
    section = text[start.start():end.start()]
    if SEQUENCE_HEADING not in section:
        raise AssertionError(f"{host}: the terminal-step slice no longer holds the draft-PR sequence")
    return section


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
            text = terminal_step(host)
            for operation in sorted(repo_only):
                self.assertNotIn(operation, text,
                                 f"{host}: the terminal step names release-gate operation {operation!r}, which needs a "
                                 "SpecKit Pro source checkout and refuses in a user repository")

    def test_the_terminal_step_names_the_helper_and_one_author_dispatch(self) -> None:
        for host in HOSTS:
            text = terminal_step(host)
            self.assertEqual(named_helpers(text) - {"preview-isolation-session"}, {"finish-plan-stage"}, host)
            self.assertEqual(len(re.findall(r"subagent_type: \"speckit-pro:artifact-author\"|spawn_agent\(\"artifact-author\"", text)), 1, host)

    def test_documented_request_sends_only_inputs_the_helper_accepts(self) -> None:
        for host in HOSTS:
            match = FINISH_REQUEST.search(terminal_step(host))
            self.assertIsNotNone(match, f"{host}: the terminal step shows no finish-plan-stage request")
            request = json.loads(match.group(1))
            self.assertLessEqual(set(request["inputs"]), INPUTS, host)
            self.assertEqual(request["answer_format"], "compact", host)

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
