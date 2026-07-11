#!/usr/bin/env python3
"""Layer-4 parity tests for the Layer-7 transcript parser."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
FIXTURES = TESTS_ROOT / "layer7-integration" / "test-fixtures"
TRANSCRIPT_LIB = TESTS_ROOT / "layer7-integration" / "lib"
SHARED_LIB = TESTS_ROOT / "lib"
for value in (TRANSCRIPT_LIB, SHARED_LIB):
    if str(value) not in sys.path:
        sys.path.insert(0, str(value))

import transcript_helpers as helpers  # noqa: E402
from test_result import run_counted  # noqa: E402


class TranscriptHelperTests(unittest.TestCase):
    def fixture(self, name: str) -> Path:
        return FIXTURES / name

    def test_transcript_helper_contract(self) -> None:
        single = self.fixture("single-dispatch.jsonl")
        multi = self.fixture("multi-dispatch.jsonl")
        sidechain = self.fixture("sidechain-noise.jsonl")
        none = self.fixture("no-dispatch.jsonl")
        chain = self.fixture("redelegation-chain.jsonl")
        forbidden = self.fixture("forbidden-spawn.jsonl")
        skills = self.fixture("skill-invocations.jsonl")

        checks = [
            ("single-dispatch returns 1 dispatch", lambda: self.assertEqual(len(helpers.extract_orchestrator_dispatches(single)), 1)),
            ("multi-dispatch returns 3 dispatches", lambda: self.assertEqual(len(helpers.extract_orchestrator_dispatches(multi)), 3)),
            (
                "sidechain-noise returns only 1 (top-level) dispatch",
                lambda: self.assertEqual(len(helpers.extract_orchestrator_dispatches(sidechain)), 1),
            ),
            ("no-dispatch returns 0 dispatches", lambda: self.assertEqual(len(helpers.extract_orchestrator_dispatches(none)), 0)),
            ("redelegation-chain returns 4 dispatches", lambda: self.assertEqual(len(helpers.extract_orchestrator_dispatches(chain)), 4)),
            (
                "single-dispatch subagent_type is codebase-analyst",
                lambda: self.assertEqual(
                    helpers.extract_orchestrator_dispatches(single)[0]["subagent_type"], "speckit-pro:codebase-analyst"
                ),
            ),
            (
                "multi-dispatch subagent_type set",
                lambda: self.assertEqual(
                    sorted(item["subagent_type"] for item in helpers.extract_orchestrator_dispatches(multi)),
                    [
                        "speckit-pro:codebase-analyst",
                        "speckit-pro:consensus-synthesizer",
                        "speckit-pro:domain-researcher",
                    ],
                ),
            ),
            (
                "redelegation-chain dispatch order",
                lambda: self.assertEqual(
                    helpers.extract_dispatch_order(chain),
                    [
                        "speckit-pro:clarify-executor",
                        "speckit-pro:codebase-analyst",
                        "speckit-pro:domain-researcher",
                        "speckit-pro:consensus-synthesizer",
                    ],
                ),
            ),
            (
                "assert_dispatched_to passes when type present",
                lambda: self.assertTrue(helpers.assert_dispatched_to(single, "speckit-pro:codebase-analyst")),
            ),
            (
                "assert_dispatched_to fails when type absent",
                lambda: self.assertFalse(helpers.assert_dispatched_to(single, "speckit-pro:domain-researcher")),
            ),
            (
                "assert_not_dispatched_to passes when type absent",
                lambda: self.assertTrue(helpers.assert_not_dispatched_to(single, "speckit-pro:domain-researcher")),
            ),
            (
                "assert_not_dispatched_to fails when type present",
                lambda: self.assertFalse(helpers.assert_not_dispatched_to(single, "speckit-pro:codebase-analyst")),
            ),
            (
                "grill-me is never dispatched in autopilot transcripts",
                lambda: self.assertTrue(helpers.assert_not_dispatched_to(chain, "speckit-pro:grill-me")),
            ),
            (
                "forbidden-spawn fixture detects 1 violation",
                lambda: self.assertEqual(len(helpers.find_forbidden_agent_spawns(forbidden)), 1),
            ),
            ("single-dispatch has 0 violations", lambda: self.assertEqual(len(helpers.find_forbidden_agent_spawns(single)), 0)),
            ("redelegation-chain has 0 violations", lambda: self.assertEqual(len(helpers.find_forbidden_agent_spawns(chain)), 0)),
            (
                "sidechain-noise has 0 violations (sidechain Bash is allowed)",
                lambda: self.assertEqual(len(helpers.find_forbidden_agent_spawns(sidechain)), 0),
            ),
            (
                "assert_no_forbidden_spawns passes for legal transcript",
                lambda: self.assertTrue(helpers.assert_no_forbidden_spawns(chain)),
            ),
            (
                "assert_no_forbidden_spawns fails for forbidden-spawn",
                lambda: self.assertFalse(helpers.assert_no_forbidden_spawns(forbidden)),
            ),
            (
                "redelegation-chain has 1 codebase-analyst dispatch",
                lambda: self.assertEqual(helpers.count_dispatches_to(chain, "speckit-pro:codebase-analyst"), 1),
            ),
            (
                "no-dispatch has 0 of any type",
                lambda: self.assertEqual(helpers.count_dispatches_to(none, "speckit-pro:codebase-analyst"), 0),
            ),
            (
                "single-dispatch description preserved",
                lambda: self.assertEqual(helpers.extract_orchestrator_dispatches(single)[0]["description"], "Codebase analysis"),
            ),
            (
                "single-dispatch prompt preserved",
                lambda: self.assertEqual(helpers.extract_orchestrator_dispatches(single)[0]["prompt"], "Analyze the auth module"),
            ),
            ("single-dispatch returns 1 response", lambda: self.assertEqual(len(helpers.extract_subagent_responses(single)), 1)),
            (
                "single-dispatch response content matches",
                lambda: self.assertIn("Found auth in src/auth.ts", helpers.extract_subagent_responses(single)[0]["content"]),
            ),
            ("multi-dispatch returns 3 paired responses", lambda: self.assertEqual(len(helpers.extract_subagent_responses(multi)), 3)),
            (
                "redelegation-chain returns 4 paired responses",
                lambda: self.assertEqual(len(helpers.extract_subagent_responses(chain)), 4),
            ),
            ("no-dispatch returns 0 responses", lambda: self.assertEqual(len(helpers.extract_subagent_responses(none)), 0)),
            (
                "synthesizer response contains 'argon2' (redelegation-chain)",
                lambda: self.assertTrue(
                    helpers.assert_response_contains(chain, "speckit-pro:consensus-synthesizer", "argon2")
                ),
            ),
            (
                "synthesizer response does NOT contain 'bcrypt' (redelegation-chain)",
                lambda: self.assertFalse(
                    helpers.assert_response_contains(chain, "speckit-pro:consensus-synthesizer", "bcrypt")
                ),
            ),
            (
                "no response from never-dispatched subagent",
                lambda: self.assertFalse(helpers.assert_response_contains(single, "speckit-pro:domain-researcher", "anything")),
            ),
            (
                "skill-invocations fixture: 2 total Skill invocations (default scope=all)",
                lambda: self.assertEqual(len(helpers.extract_skill_invocations(skills)), 2),
            ),
            (
                "skill-invocations fixture: 1 orchestrator-level Skill invocation",
                lambda: self.assertEqual(len(helpers.extract_skill_invocations(skills, "orchestrator")), 1),
            ),
            (
                "skill-invocations fixture: orchestrator skill is speckit.specify",
                lambda: self.assertEqual(helpers.extract_skill_invocations(skills, "orchestrator")[0]["skill"], "speckit.specify"),
            ),
            (
                "count_skill_invocations grill-me at all scope: 1 match (sidechain only)",
                lambda: self.assertEqual(helpers.count_skill_invocations(skills, "grill-me"), 1),
            ),
            (
                "count_skill_invocations grill-me at orchestrator scope: 0 (sidechain doesn't count)",
                lambda: self.assertEqual(helpers.count_skill_invocations(skills, "grill-me", "orchestrator"), 0),
            ),
            (
                "count_skill_invocations matches namespaced form via regex",
                lambda: self.assertEqual(helpers.count_skill_invocations(skills, "speckit-pro:grill-me"), 1),
            ),
            (
                "assert_skill_not_invoked grill-me at all scope FAILS (sidechain has it)",
                lambda: self.assertFalse(helpers.assert_skill_not_invoked(skills, "grill-me")),
            ),
            (
                "assert_skill_not_invoked grill-me at orchestrator scope PASSES",
                lambda: self.assertTrue(helpers.assert_skill_not_invoked(skills, "grill-me", "orchestrator")),
            ),
            (
                "assert_skill_invoked speckit.specify at orchestrator scope PASSES",
                lambda: self.assertTrue(helpers.assert_skill_invoked(skills, r"speckit\.specify", "orchestrator")),
            ),
            (
                "single-dispatch fixture has 0 Skill invocations",
                lambda: self.assertEqual(len(helpers.extract_skill_invocations(single)), 0),
            ),
            (
                "assert_skill_not_invoked grill-me on single-dispatch PASSES (no Skill calls)",
                lambda: self.assertTrue(helpers.assert_skill_not_invoked(single, "grill-me")),
            ),
        ]
        for name, check in checks:
            with self.subTest(msg=name):
                check()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TranscriptHelperTests)
    raise SystemExit(run_counted(suite, label="test-transcript-helpers"))
