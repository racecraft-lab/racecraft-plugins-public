#!/usr/bin/env python3
"""Regression gates for named synthesis, agreement rules, and failure stops."""

from __future__ import annotations

import sys
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


SYNTHESIZER = REPO_ROOT / "speckit-pro" / "codex-agents" / "consensus-synthesizer.toml"
PROTOCOL = (
    REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "references"
    / "consensus-protocol.md"
)
AUTOPILOT_SKILLS = (
    REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "SKILL.md",
    REPO_ROOT / "speckit-pro" / "codex-skills" / "speckit-autopilot" / "SKILL.md",
)
CODEX_AUTOPILOT = AUTOPILOT_SKILLS[1]


def instructions() -> str:
    return tomllib.loads(SYNTHESIZER.read_text(encoding="utf-8"))["developer_instructions"]


def assert_contains(test: unittest.TestCase, text: str, phrases: tuple[str, ...]) -> None:
    for phrase in phrases:
        with test.subTest(phrase=phrase):
            test.assertIn(phrase, text)


class ConsensusSynthesizerRegressionTests(unittest.TestCase):
    def test_codex_dispatch_names_the_custom_agent_in_the_native_argument(self) -> None:
        codex = CODEX_AUTOPILOT.read_text(encoding="utf-8")
        protocol = PROTOCOL.read_text(encoding="utf-8")
        assert_contains(self, codex, (
            '`agent_type="<installed-agent-name>"`',
            '`agent_type="consensus-synthesizer"`',
            "A default or general-purpose worker is not the named synthesizer",
        ))
        assert_contains(self, protocol, (
            '`spawn_agent(agent_type="consensus-synthesizer"',
            "Omitting `agent_type` and accepting the default role is a failed dispatch",
        ))

    def test_all_agreement_branches_are_explicit_and_fail_closed(self) -> None:
        text = instructions()
        flat = " ".join(text.split())
        assert_contains(self, flat, (
            "N = 1:",
            "A high-confidence answer with no escape phrase",
            "Low confidence or any escape phrase",
            "N = 2:",
            "Agreement produces `confidence: high`",
            "Disagreement produces",
            "N = 3:",
            "Unanimity produces high confidence",
            "A 2/3 majority wins while the dissent is preserved",
            "If all three disagree",
            "[HUMAN REVIEW NEEDED]",
            "Security override at any N",
            "apply the answer only when all three analysts agree",
            "A 2/3 majority or no agreement returns `[HUMAN REVIEW NEEDED]`",
            "a keyword alone never stops the run",
        ))

    def test_escape_phrases_and_security_override_are_complete(self) -> None:
        text = instructions()
        assert_contains(self, text, (
            "insufficient context",
            "not in this codebase",
            "no precedent in this repo",
            "outside my scope",
            "cannot answer from this perspective",
            "this is a [different category] question",
            "security item arrives with fewer than three responses",
        ))

    def test_result_contract_preserves_evidence_dissent_and_exact_edits(self) -> None:
        text = instructions()
        assert_contains(self, text, (
            "**Supporting Analysts:**",
            "**Dissent:**",
            "**Artifact Edit:**",
            "- **File:**",
            "- **Section:**",
            "- **Action:**",
            "- **Content:**",
            "**Flags:**",
        ))
        self.assertIn("Omit the complete `Artifact Edit` block whenever `Flags` is not `None`.", text)

    def test_missing_failed_or_malformed_synthesis_cannot_apply_or_complete(self) -> None:
        required = (
            "MUST NOT synthesize directly or silently",
            "missing, failed, or malformed synthesizer result",
            "authorizes no edit and cannot mark consensus complete",
        )
        for path in AUTOPILOT_SKILLS:
            text = path.read_text(encoding="utf-8")
            flat = " ".join(text.split())
            with self.subTest(path=path.name):
                assert_contains(self, flat, required)
        protocol = PROTOCOL.read_text(encoding="utf-8")
        protocol_flat = " ".join(protocol.split())
        assert_contains(self, protocol_flat, (
            "applies no edit",
            "writes no completed Consensus Resolution Log row",
            "does not mark the item complete",
            "retry the same named synthesizer once with the same analyst responses",
            "A second invalid result is",
            "must never replace it with parent-authored synthesis",
        ))

    def test_analyze_confidence_is_one_five_criterion_block_even_with_zero_findings(self) -> None:
        text = instructions()
        self.assertIn("including a\nclean pass with zero findings", text)
        self.assertIn("append exactly one block", text)
        self.assertIn("never emit it more than once in an Analyze pass", text)
        for label in (
            "Task understanding",
            "Approach clarity",
            "Requirements alignment",
            "Risk assessment",
            "Completeness",
        ):
            with self.subTest(label=label):
                self.assertEqual(text.count(f"- {label}: 0.XX"), 1)

        protocol = PROTOCOL.read_text(encoding="utf-8")
        self.assertIn("even when there were zero findings", protocol)
        self.assertIn("persists that block exactly once for the current Analyze pass", protocol)
        self.assertIn("cannot be reconstructed by the parent", protocol)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        ConsensusSynthesizerRegressionTests,
    )
    return run_counted(suite, label="test-consensus-synthesizer-regressions")


if __name__ == "__main__":
    raise SystemExit(main())
