#!/usr/bin/env python3
"""Regression gates for named synthesis, agreement rules, and failure stops."""

from __future__ import annotations

import json
import sys
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from guide_text import guide_text  # noqa: E402
from host_skill_views import host_skill_root  # noqa: E402
from test_result import run_counted  # noqa: E402

PHRASES = json.loads(
    (REPO_ROOT / "tests" / "speckit-pro" / "unit" / "fixtures" / "autopilot-guidance" / "consensus-synthesizer-phrases.json")
    .read_text(encoding="utf-8")
)


SYNTHESIZER = REPO_ROOT / "speckit-pro" / "codex-agents" / "consensus-synthesizer.toml"
CLAUDE_SYNTHESIZER = REPO_ROOT / "speckit-pro" / "agents" / "consensus-synthesizer.md"
PROTOCOL = (
    REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "references"
    / "consensus-protocol.md"
)
# The autopilot skill as each host receives it, rendered from the shared source.
AUTOPILOT_SKILLS = tuple(host_skill_root(host) / "speckit-autopilot" / "SKILL.md" for host in ("claude", "codex"))
CODEX_AUTOPILOT = AUTOPILOT_SKILLS[1]
REFERENCES = AUTOPILOT_SKILLS[0].parent / "references"
CODEX_PHASE_EXECUTION = CODEX_AUTOPILOT.parent / "references" / "phase-execution.md"
ACTIVE_PROTOCOL = "<plugin_root>/skills/speckit-autopilot/references/consensus-protocol.md"
ACTIVE_REFERENCES = "Reference dir: <plugin_root>/skills/speckit-autopilot/references/"
TIEBREAKER_CLAUDE = REPO_ROOT / "speckit-pro" / "agents" / "consensus-tiebreaker.md"
TIEBREAKER_CODEX = REPO_ROOT / "speckit-pro" / "codex-agents" / "consensus-tiebreaker.toml"
SCAFFOLD_SKILL = REPO_ROOT / "speckit-pro" / "skills" / "speckit-scaffold-spec" / "SKILL.md"
EXECUTORS = tuple(
    REPO_ROOT / "speckit-pro" / folder / f"{role}-executor{suffix}"
    for role in ("clarify", "analyze", "checklist")
    for folder, suffix in (("agents", ".md"), ("codex-agents", ".toml"))
)


def dispatch_block(text: str, anchor: str) -> str:
    """Return the fenced dispatch text from ``anchor`` to its closing fence."""
    start = text.index(anchor)
    return text[start:text.index("\n```", start)]


def phase_execution_text() -> str:
    return (REFERENCES / "phase-execution.md").read_text(encoding="utf-8")


def instructions() -> str:
    return tomllib.loads(SYNTHESIZER.read_text(encoding="utf-8"))["developer_instructions"]


def synthesizer_texts() -> tuple[tuple[str, str], ...]:
    """The synthesizer contract as each host receives it, whitespace collapsed."""
    return (
        ("codex", " ".join(instructions().split())),
        ("claude", guide_text("agents/consensus-synthesizer.md", "claude")),
    )


def assert_both_hosts_say(test: unittest.TestCase, phrase_key: str) -> None:
    for host, flat in synthesizer_texts():
        with test.subTest(host=host):
            assert_contains(test, flat, PHRASES[f"ConsensusSynthesizerRegressionTests.{phrase_key}#1"])


def assert_contains(test: unittest.TestCase, text: str, phrases: tuple[str, ...]) -> None:
    for phrase in phrases:
        with test.subTest(phrase=phrase):
            test.assertIn(phrase, text)


class ConsensusSynthesizerRegressionTests(unittest.TestCase):
    def test_codex_dispatch_names_the_custom_agent_in_the_native_argument(self) -> None:
        codex = CODEX_AUTOPILOT.read_text(encoding="utf-8")
        protocol = PROTOCOL.read_text(encoding="utf-8")
        assert_contains(self, codex, PHRASES["ConsensusSynthesizerRegressionTests.test_codex_dispatch_names_the_custom_agent_in_the_native_argument#1"])
        assert_contains(self, protocol, (
            '`spawn_agent(agent_type="consensus-synthesizer"',
            "Omitting `agent_type` and accepting the default role is a failed dispatch",
        ))

    def test_all_agreement_branches_are_explicit_and_fail_closed(self) -> None:
        assert_both_hosts_say(self, "test_all_agreement_branches_are_explicit_and_fail_closed")

    def test_keyword_only_route_uses_the_items_own_rule_when_no_analyst_flags_security(self) -> None:
        # A keyword such as `tokens` meaning LLM usage counts must not force
        # unanimity when every analyst says the item has no security content.
        # A tag, a `true`, or a missing field still fails toward unanimity.
        route_line = "**Security Route:** tag | keyword | none"
        rule = (
            "When the route is `keyword` and every routed response returns "
            "`security_relevant: false`, apply the ordinary three-response rule, "
            "so a 2/3 majority wins"
        )
        fail_closed = "returns `security_relevant: true`, or omits the field"
        for label, text in (
            ("codex", instructions()),
            ("claude", CLAUDE_SYNTHESIZER.read_text(encoding="utf-8")),
        ):
            flat = " ".join(text.split())
            with self.subTest(platform=label):
                assert_contains(self, text, (route_line,))
                self.assertIn("null is written as none", flat)
                assert_contains(self, flat, (rule, fail_closed))
        protocol = " ".join(PROTOCOL.read_text(encoding="utf-8").split())
        assert_contains(self, protocol, PHRASES["ConsensusSynthesizerRegressionTests.test_keyword_only_route_uses_the_items_own_rule_when_no_analyst_flags_security#1"])

    def test_security_relevant_raises_the_bar_only_on_a_security_route(self) -> None:
        # Only a `tag` or `keyword` route sends an item to the synthesizer, and
        # either can raise the bar to unanimity. A route `none` item never
        # reaches the synthesizer, so the agent carries no rule for it.
        for label, text in (
            ("codex", instructions()),
            ("claude", CLAUDE_SYNTHESIZER.read_text(encoding="utf-8")),
        ):
            flat = " ".join(text.split())
            with self.subTest(platform=label):
                self.assertNotIn("at any N", flat)
                self.assertNotIn("(any N)", flat)
                assert_contains(self, flat, (
                    "When the route is `tag`, apply the answer only when all three analysts agree",
                    "When the route is `keyword` and any routed response returns `security_relevant: true`, or omits the field",
                ))
                self.assertNotIn("When the route is `none`", flat)
        protocol = " ".join(PROTOCOL.read_text(encoding="utf-8").split())
        assert_contains(self, protocol, PHRASES["ConsensusSynthesizerRegressionTests.test_security_relevant_raises_the_bar_only_on_a_security_route#1"])

    def test_executors_reserve_the_security_tag_for_security_substance(self) -> None:
        # A `[security]` tag always keeps unanimity, so an executor that tags
        # every keyword-bearing item would defeat the keyword-only relief.
        for path in EXECUTORS:
            flat = " ".join(path.read_text(encoding="utf-8").split())
            with self.subTest(path=f"{path.parent.name}/{path.name}"):
                self.assertNotIn("contains a security keyword (always", flat)
                self.assertIn("substance is about security", flat)
                self.assertIn("A security keyword alone needs no tag", flat)

    def test_executor_eligibility_names_the_security_tag_on_both_hosts(self) -> None:
        # The parent routes only items an executor surfaces, so a high-confidence
        # `[security]` item with no keyword must still be surfaced: the tag is
        # its own trigger, beside low confidence and a security keyword.
        for path in EXECUTORS:
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".toml":
                text = tomllib.loads(text)["developer_instructions"]
            else:
                text = guide_text(f"agents/{path.name}", "claude")
            flat = " ".join(text.split())
            start = flat.index('"Unresolved for consensus" section')
            eligibility = flat[start:flat.index("access-control)", start)]
            with self.subTest(path=f"{path.parent.name}/{path.name}"):
                self.assertIn("you tag `[security]`, at any confidence", eligibility)

    def test_orchestrator_passes_the_active_protocol_path(self) -> None:
        # Every synthesizer prompt carries the protocol path resolved from the loaded plugin root.
        protocol = PROTOCOL.read_text(encoding="utf-8")
        self.assertIn(f"**Protocol:** {ACTIVE_PROTOCOL}", protocol)
        phase = phase_execution_text()
        # The clarify, checklist and analyze executors take reference slices from the phase brief instead.
        self.assertIn('prompt: "Run /speckit-checklist with: <domain prompt>\\nReference slices: <brief.slices, verbatim>")', phase)
        self.assertIn('prompt: "Run /speckit-analyze with: <prompt>\\nReference slices: <brief.slices, verbatim>")', phase)
        flat = " ".join(phase.split())
        self.assertIn("Prepare a Clarify Question Set for: <session prompt> Reference slices: <brief.slices, verbatim>", flat)
        self.assertIn("Workflow root: <WORKFLOW_ROOT>", phase)
        self.assertIn("consensus-synthesizer agent (single fan-out), with the `Protocol:` line,", flat)
        self.assertIn("never the checkout that launched the run", flat)
        prerequisites = " ".join((REFERENCES / "prerequisites.md").read_text(encoding="utf-8").split())
        self.assertIn("Keep the returned `plugin_root`", prerequisites)
        codex = " ".join(CODEX_PHASE_EXECUTION.read_text(encoding="utf-8").split())
        self.assertIn("`Protocol:` line with `<plugin-root>/skills/speckit-autopilot/references/consensus-protocol.md`", codex)

    def test_orchestrator_passes_the_active_reference_directory(self) -> None:
        # Every dispatch of an agent that reads capability-discovery.md and
        # grounding.md carries the directory resolved from the loaded plugin
        # root, so the agent never searches the plugin cache for a copy.
        sites = {
            "phase-execution.md": (
                'subagent_type: "speckit-pro:artifact-author"',
                'subagent_type: "<batch.agent>"',
            ),
            "post-implementation.md": (
                'subagent_type: "speckit-pro:implement-executor"',
                'subagent_type: "speckit-pro:uat-runbook-author"',
            ),
            "consensus-protocol.md": (
                "clarification question that the executor could not resolve",
                "checklist gap that the executor could not resolve",
                "analysis finding that the executor could not resolve",
            ),
        }
        for name, anchors in sites.items():
            text = (REFERENCES / name).read_text(encoding="utf-8")
            for anchor in anchors:
                with self.subTest(file=name, dispatch=anchor):
                    self.assertIn(ACTIVE_REFERENCES, dispatch_block(text, anchor))
        formal = " ".join((REFERENCES / "formal-methods.md").read_text(encoding="utf-8").split())
        self.assertIn(f"`{ACTIVE_REFERENCES}` line", formal)
        prerequisites = " ".join((REFERENCES / "prerequisites.md").read_text(encoding="utf-8").split())
        self.assertIn(f"`{ACTIVE_REFERENCES}`", prerequisites)
        phase = phase_execution_text()
        author = dispatch_block(phase, 'subagent_type: "speckit-pro:artifact-author"')
        self.assertIn("Gallery dir: <plugin_root>/artifact-gallery/", author)
        self.assertNotIn("speckit-pro/artifact-gallery/", phase)
        codex = CODEX_PHASE_EXECUTION.read_text(encoding="utf-8")
        self.assertIn(
            "Gallery dir: <plugin-root>/artifact-gallery/",
            dispatch_block(codex, 'spawn_agent("artifact-author"'),
        )
        self.assertNotIn("speckit-pro/artifact-gallery/", codex)
        self.assertIn("`Gallery dir: <plugin_root>/artifact-gallery/`", prerequisites)
        scaffold = SCAFFOLD_SKILL.read_text(encoding="utf-8")
        self.assertIn(
            "Reference dir: ${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/",
            dispatch_block(scaffold, 'Agent(subagent_type: "speckit-pro:codebase-analyst"'),
        )

    def test_escape_phrases_and_security_override_are_complete(self) -> None:
        assert_both_hosts_say(self, "test_escape_phrases_and_security_override_are_complete")

    def test_result_contract_preserves_evidence_dissent_and_exact_edits(self) -> None:
        # The parent applies an edit only when Flags is None, so any flag,
        # including a routing violation, leaves no edit to apply.
        assert_both_hosts_say(self, "test_result_contract_preserves_evidence_dissent_and_exact_edits")
        for host, flat in synthesizer_texts():
            with self.subTest(host=host):
                self.assertIn("Omit the complete `Artifact Edit` block whenever `Flags` is not `None`", flat)
        protocol = " ".join(PROTOCOL.read_text(encoding="utf-8").split())
        self.assertIn("IF Flags = None AND", protocol)

    def test_confidence_emit_and_routing_violation_return_no_edit(self) -> None:
        # The Phase 6 emit and the G6.5 re-emit carry no consensus item, and
        # only confidence-gate reads their result, so an Artifact Edit there
        # would have no consumer. A routing violation applies nothing either.
        for host, flat in synthesizer_texts():
            with self.subTest(host=host):
                assert_contains(self, flat, (
                    "or re-dispatches you after a G6.5 remediation, the prompt carries no consensus item",
                    "no `Consensus Result` and no `Artifact Edit`",
                    "that result carries no `Answer` and no `Artifact Edit`",
                    "**Analysts Run:** 3",
                ))
                self.assertNotIn("after all per-finding `Consensus Result` blocks", flat)
        claude_phase = " ".join(phase_execution_text().split())
        self.assertIn("Confidence block to the workflow file (confidence block only; no Artifact Edit)", claude_phase)
        codex_phase = " ".join(CODEX_PHASE_EXECUTION.read_text(encoding="utf-8").split())
        self.assertIn("This dispatch carries no consensus item, so its result has no Artifact Edit", codex_phase)
        self.assertNotIn("applies any accepted serial artifact edit, and persists", codex_phase)
        gate = " ".join((REFERENCES / "gate-validation.md").read_text(encoding="utf-8").split())
        self.assertIn("the result is the block alone, with no Artifact Edit", gate)
        protocol = " ".join(PROTOCOL.read_text(encoding="utf-8").split())
        self.assertIn("the parent applies nothing from it", protocol)

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
        assert_contains(self, protocol_flat, PHRASES["ConsensusSynthesizerRegressionTests.test_missing_failed_or_malformed_synthesis_cannot_apply_or_complete#1"])

    def test_analyze_confidence_is_one_five_criterion_block_even_with_zero_findings(self) -> None:
        # confidence-gate reads the last block, so a second one silently wins.
        for host, flat in synthesizer_texts():
            with self.subTest(host=host):
                self.assertIn("including a clean pass with zero findings", flat)
                self.assertIn("return exactly one block and nothing else", flat)
                self.assertIn("never emit it more than once in an Analyze pass", flat)
                for label in (
                    "Task understanding",
                    "Approach clarity",
                    "Requirements alignment",
                    "Risk assessment",
                    "Completeness",
                ):
                    self.assertEqual(flat.count(f"- {label}: 0.XX"), 1, label)

        protocol = PROTOCOL.read_text(encoding="utf-8")
        self.assertIn("even when there were zero findings", protocol)
        self.assertIn("persists that block exactly once for the current Analyze pass", protocol)
        self.assertIn("cannot be reconstructed by the parent", protocol)


class Round3TiebreakGuidanceTests(unittest.TestCase):
    def test_round3_tiebreak_replaces_every_consensus_human_stop_in_the_protocol(self) -> None:
        # Consensus that cannot agree resolves through a Round 3 agent tiebreak
        # in an interactive and an unattended run alike. Nothing asks or stops.
        raw = PROTOCOL.read_text(encoding="utf-8")
        protocol = " ".join(raw.split())
        assert_contains(self, protocol, PHRASES["Round3TiebreakGuidanceTests.test_round3_tiebreak_replaces_every_consensus_human_stop_in_the_protocol#1"])
        for stale in PHRASES["Round3TiebreakGuidanceTests.test_round3_tiebreak_replaces_every_consensus_human_stop_in_the_protocol#2"]:
            with self.subTest(stale=stale):
                self.assertNotIn(stale, protocol)

    def test_synthesizer_keeps_its_default_effort_and_only_flags_round_three(self) -> None:
        claude = CLAUDE_SYNTHESIZER.read_text(encoding="utf-8")
        codex = SYNTHESIZER.read_text(encoding="utf-8")
        self.assertIn("effort: high", claude)
        self.assertIn('model_reasoning_effort = "medium"', codex)
        for label, text in (("claude", claude), ("codex", instructions())):
            flat = " ".join(text.split())
            with self.subTest(host=label):
                assert_contains(self, flat, ("[ROUND_3_TIEBREAK]", "consensus-tiebreaker"))
                self.assertNotIn("**Round:** 1 | 2 | 3", flat)
                self.assertNotIn("[SCOPE_DEFERRED]", flat)
        self.assertNotIn("the orchestrator surfaces that to the user", claude)

    def test_round3_dispatch_names_the_tiebreaker_on_both_hosts(self) -> None:
        protocol = " ".join(PROTOCOL.read_text(encoding="utf-8").split())
        assert_contains(self, protocol, PHRASES["Round3TiebreakGuidanceTests.test_round3_dispatch_names_the_tiebreaker_on_both_hosts#1"])
        for path in (AUTOPILOT_SKILLS[0], AUTOPILOT_SKILLS[1], REFERENCES / "error-recovery.md"):
            with self.subTest(path=path.name):
                self.assertIn("consensus-tiebreaker", path.read_text(encoding="utf-8"))


class Round3TiebreakHostTests(unittest.TestCase):
    """Round 3 reads the same on both hosts and covers the PR feedback sweep."""

    def test_round3_tiebreak_reads_the_same_on_both_hosts(self) -> None:
        anchor = "consensus-protocol.md#round-3-tiebreak"
        claude_files = (
            AUTOPILOT_SKILLS[0],
            REFERENCES / "error-recovery.md",
            REFERENCES / "phase-execution.md",
            REFERENCES / "gate-validation.md",
        )
        codex_refs = CODEX_AUTOPILOT.parent / "references"
        codex_files = (
            CODEX_AUTOPILOT,
            codex_refs / "error-recovery.md",
            CODEX_PHASE_EXECUTION,
        )
        for host, paths in (("claude", claude_files), ("codex", codex_files)):
            for path in paths:
                flat = " ".join(path.read_text(encoding="utf-8").split())
                with self.subTest(host=host, path=path.name):
                    self.assertNotIn("human-review-needed", flat)
                    self.assertNotIn("[ROUND_3_TIEBREAK]` goes to the operator", flat)
                    self.assertNotIn("ask the operator in place", flat)
                    self.assertNotIn("STOP and present all 3 perspectives", flat)
                    self.assertNotIn("STOP. Present remaining ambiguities to human", flat)
                    if path.name != "gate-validation.md":
                        assert_contains(self, flat, ("Round 3",))
                    if path.name not in {"SKILL.md", "gate-validation.md"}:
                        assert_contains(self, flat, (anchor,))
        phase = phase_execution_text()
        self.assertGreaterEqual(phase.count(anchor), 3, "Clarify, Checklist, and Analyze each route to Round 3")
        codex_phase = " ".join(CODEX_PHASE_EXECUTION.read_text(encoding="utf-8").split())
        self.assertGreaterEqual(codex_phase.count(anchor), 1, "Codex consensus step routes to Round 3")
        gate = " ".join((REFERENCES / "gate-validation.md").read_text(encoding="utf-8").split())
        assert_contains(self, gate, ("Round 3 tiebreak", "end-of-run request"))
        # Each host names only its own question tool, and only outside consensus.
        for path in claude_files[1:2] + (REFERENCES / "consensus-protocol.md",):
            self.assertNotIn("request_user_input", path.read_text(encoding="utf-8"))
        for path in codex_files[1:2]:
            self.assertNotIn("AskUserQuestion", path.read_text(encoding="utf-8"))
            self.assertNotIn("request_user_input", path.read_text(encoding="utf-8"))

    def test_round3_tiebreak_covers_the_pr_feedback_sweep_inside_its_isolation(self) -> None:
        sites = (
            ("claude", REFERENCES / "phase-execution.md"),
            ("codex", CODEX_PHASE_EXECUTION),
        )
        for host, path in sites:
            flat = " ".join(path.read_text(encoding="utf-8").split())
            with self.subTest(host=host):
                assert_contains(self, flat, PHRASES["Round3TiebreakGuidanceTests.test_round3_tiebreak_covers_the_pr_feedback_sweep_inside_its_isolation#1"])
                for stale in PHRASES["Round3TiebreakGuidanceTests.test_round3_tiebreak_covers_the_pr_feedback_sweep_inside_its_isolation#2"]:
                    self.assertNotIn(stale, flat)
        codex_prompt = " ".join(
            (CODEX_AUTOPILOT.parent / "references" / "sweep-prompts" / "analyst.md").read_text(encoding="utf-8").split()
        )
        claude_prompt = " ".join(
            (REPO_ROOT / "speckit-pro" / "agents" / "sweep-analyst.md").read_text(encoding="utf-8").split()
        )
        for label, text in (("claude", claude_prompt), ("codex", codex_prompt)):
            with self.subTest(prompt=label):
                assert_contains(self, text, PHRASES["Round3TiebreakGuidanceTests.test_round3_tiebreak_covers_the_pr_feedback_sweep_inside_its_isolation#3"])


class Round3TiebreakAgentTests(unittest.TestCase):
    """The tiebreaker agent and the inventory pin its effort."""

    def test_tiebreaker_agent_is_max_effort_read_only_and_owns_round_three(self) -> None:
        claude = TIEBREAKER_CLAUDE.read_text(encoding="utf-8")
        codex_raw = TIEBREAKER_CODEX.read_text(encoding="utf-8")
        codex = tomllib.loads(codex_raw)
        self.assertIn("name: consensus-tiebreaker", claude)
        self.assertIn("effort: max", claude)
        self.assertIn("model: sonnet", claude)
        self.assertEqual("consensus-tiebreaker", codex["name"])
        self.assertEqual("max", codex["model_reasoning_effort"])
        self.assertEqual("read-only", codex["sandbox_mode"])
        synth_tools = next(l for l in CLAUDE_SYNTHESIZER.read_text(encoding="utf-8").splitlines() if l.startswith("disallowedTools:"))
        self.assertIn(synth_tools, claude)
        for label, text in (("claude", claude), ("codex", codex["developer_instructions"])):
            flat = " ".join(text.split())
            with self.subTest(host=label):
                assert_contains(self, flat, PHRASES["Round3TiebreakGuidanceTests.test_tiebreaker_agent_is_max_effort_read_only_and_owns_round_three#1"])

    def test_inventory_pins_the_synthesizer_at_default_and_the_tiebreaker_at_max(self) -> None:
        inventory = json.loads(
            (REPO_ROOT / "speckit-pro" / "speckit_pro_runner" / "agent_inventory.json").read_text(encoding="utf-8")
        )
        roles = {role["name"]: role for role in inventory["roles"]}
        self.assertEqual(("high", "medium"), (
            roles["consensus-synthesizer"]["claude_code"]["effort"],
            roles["consensus-synthesizer"]["codex"]["effort"],
        ))
        tiebreaker = roles["consensus-tiebreaker"]
        self.assertEqual("shared", tiebreaker["category"])
        self.assertEqual("agents/consensus-tiebreaker.md", tiebreaker["claude_code"]["source"])
        self.assertEqual("codex-agents/consensus-tiebreaker.toml", tiebreaker["codex"]["source"])
        self.assertEqual(("max", "max"), (tiebreaker["claude_code"]["effort"], tiebreaker["codex"]["effort"]))
        self.assertEqual("read-only", tiebreaker["codex"]["sandbox"])
        self.assertEqual("tool-policy-read-only", tiebreaker["claude_code"]["sandbox"])


def main() -> int:
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(case)
        for case in (
            ConsensusSynthesizerRegressionTests,
            Round3TiebreakGuidanceTests,
            Round3TiebreakHostTests,
            Round3TiebreakAgentTests,
        )
    )
    return run_counted(suite, label="test-consensus-synthesizer-regressions")


if __name__ == "__main__":
    raise SystemExit(main())
