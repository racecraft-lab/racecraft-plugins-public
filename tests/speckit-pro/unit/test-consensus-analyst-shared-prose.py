#!/usr/bin/env python3
"""Byte-equality guard for the prose the three consensus analysts share.

``codebase-analyst``, ``spec-context-analyst``, and ``domain-researcher`` are
three definitions on purpose: ``effort`` and ``memory`` are per-definition
frontmatter, the Codex mirrors carry per-role reasoning effort, and the
consensus protocol, the synthesizer input contract, and the Layer 7 dispatch
fixtures are all keyed by agent name. This file fails when a shared block is
edited in one body and not the other two.

Three blocks are shared word for word across the three Claude bodies:

* the ``## Input`` bullets and the sentence that closes them,
* the grounding-evidence note under ``## Output Format``,
* the ``### Terminal Deliverable`` paragraph, which differs only in the
  ``(Answer / X / Confidence)`` section-name triple and is compared with that
  triple normalized out.

Everything else is lane-specific and shapes artifact quality, so it is not
guarded here. The ``Stay in your lane`` rule is deliberately excluded: each
copy names the other two lanes, so the three can never be byte-equal.

**Comparison is byte-exact.** Nothing is whitespace-normalized. A rewrap of a
shared block in one body is a real divergence and this file reports it.

**Two accepted cross-platform asymmetries**, both recorded rather than fixed:

1. The Codex TOMLs write ``$speckit-analyze`` where the Claude bodies write
   ``/speckit-analyze``. The Codex checks map the one to the other.
2. The Codex parity checks cover the Input bullets only; the ``### Terminal
   Deliverable`` paragraph is outside those checks.

The fourth ``Research Task`` input is domain-researcher's alone. Phase 7 routes
implementation tasks whose descriptions match ``research``, ``investigate``, or
``explore API`` to that agent, outside the consensus protocol. That second
dispatch path gets its own assertion group here.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


ANALYSTS = ("codebase-analyst", "spec-context-analyst", "domain-researcher")
CONSENSUS_ONLY = ("codebase-analyst", "spec-context-analyst")
RESEARCH_ROLE = "domain-researcher"

CLAUDE_AGENTS_DIR = REPO_ROOT / "speckit-pro" / "agents"
CODEX_AGENTS_DIR = REPO_ROOT / "speckit-pro" / "codex-agents"

SHARED_GROUP = "SHARED PROSE"
CODEX_GROUP = "CODEX MIRROR"
DISPATCH_GROUP = "RESEARCH DISPATCH"

SHARED_INPUT_BULLETS = (
    "1. **Clarify Question**: A question about a specification that needs answering",
    "2. **Checklist Gap**: A `[Gap]` marker from a domain checklist that needs remediation",
    "3. **Analyze Finding**: A CRITICAL or HIGH finding from `/speckit-analyze` "
    "that needs fixing",
)
SHARED_INPUT_CLOSER = (
    "Each input includes the relevant context (spec.md excerpt, question text, "
    "gap description, or finding details)."
)
RESEARCH_TASK_BULLET = (
    "4. **Research Task**: A `tasks.md` task that Phase 7 routes here for research "
    "or API investigation, outside the consensus protocol, carrying the exact "
    "task description and the prior task results accumulated in the run"
)

BULLET_RE = re.compile(r"^\d+\. \*\*", re.MULTILINE)
LEAD_RE = re.compile(r"^You will receive one of (\w+) types of input:$", re.MULTILINE)
GROUNDING_PREFIX = "For every externally-sourced fact in your output,"
SECTION_TRIPLE_RE = re.compile(r"\(Answer / \w+ / Confidence\)")


def _claude_body(name: str) -> str:
    return (CLAUDE_AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _codex_body(name: str) -> str:
    return (CODEX_AGENTS_DIR / f"{name}.toml").read_text(encoding="utf-8")


def _input_section(text: str) -> str:
    """Text between the ``## Input`` heading and ``## Your Process``.

    Both platforms place the Input block immediately before Your Process, and
    neither fences anything inside it, so a plain heading scan is exact.
    """
    match = re.search(r"^## Input\n(.*?)(?=^## Your Process$)", text, re.S | re.M)
    if match is None:
        raise AssertionError("no '## Input' section ending at '## Your Process'")
    return match.group(1)


def _input_bullets(text: str) -> list[str]:
    return [
        line
        for line in _input_section(text).splitlines()
        if BULLET_RE.match(line)
    ]


def _input_lead_count_word(text: str) -> str:
    match = LEAD_RE.search(_input_section(text))
    if match is None:
        raise AssertionError("no 'You will receive one of N types of input:' lead line")
    return match.group(1)


def _input_closer(text: str) -> str:
    for line in _input_section(text).splitlines():
        if line.startswith("Each input includes"):
            return line
    raise AssertionError("no 'Each input includes' sentence in the Input section")


def _grounding_note(text: str) -> str:
    for line in text.splitlines():
        if line.startswith(GROUNDING_PREFIX):
            return line
    raise AssertionError(f"no line starting {GROUNDING_PREFIX!r}")


def _terminal_deliverable(text: str) -> str:
    match = re.search(
        r"^### Terminal Deliverable\n(.*?)(?=^#{2,3} )", text, re.S | re.M
    )
    if match is None:
        raise AssertionError("no '### Terminal Deliverable' section")
    return match.group(1)


def _codex_flavored(bullet: str) -> str:
    """The Claude bullet as the Codex TOMLs spell it (accepted asymmetry 1)."""
    return bullet.replace("`/speckit-analyze`", "`$speckit-analyze`")


class ConsensusAnalystSharedProseTests(unittest.TestCase):
    def test_shared_input_bullets_are_byte_identical(self) -> None:
        for name in ANALYSTS:
            with self.subTest(agent=name):
                bullets = _input_bullets(_claude_body(name))
                self.assertEqual(
                    tuple(bullets[: len(SHARED_INPUT_BULLETS)]),
                    SHARED_INPUT_BULLETS,
                    f"[{SHARED_GROUP}] {name}: the first three Input bullets are shared "
                    "word for word by all three consensus analysts. Edit all three "
                    "bodies together, or update SHARED_INPUT_BULLETS here",
                )

    def test_shared_input_closing_sentence_is_byte_identical(self) -> None:
        for name in ANALYSTS:
            with self.subTest(agent=name):
                self.assertEqual(
                    _input_closer(_claude_body(name)),
                    SHARED_INPUT_CLOSER,
                    f"[{SHARED_GROUP}] {name}: the sentence closing the Input section "
                    "is shared by all three consensus analysts",
                )

    def test_grounding_note_is_byte_identical(self) -> None:
        notes = {name: _grounding_note(_claude_body(name)) for name in ANALYSTS}
        self.assertEqual(
            len(set(notes.values())),
            1,
            f"[{SHARED_GROUP}] the grounding-evidence note diverged across the three "
            f"consensus analysts: {notes}",
        )

    def test_terminal_deliverable_is_identical_modulo_the_section_triple(self) -> None:
        normalized = {
            name: SECTION_TRIPLE_RE.sub("(<TRIPLE>)", _terminal_deliverable(_claude_body(name)))
            for name in ANALYSTS
        }
        self.assertEqual(
            len(set(normalized.values())),
            1,
            f"[{SHARED_GROUP}] the Terminal Deliverable paragraph diverged across the "
            "three consensus analysts. Only the (Answer / X / Confidence) triple may "
            f"differ: {normalized}",
        )

    def test_terminal_deliverable_names_each_agents_own_output_sections(self) -> None:
        expected = {
            "codebase-analyst": "(Answer / Evidence / Confidence)",
            "spec-context-analyst": "(Answer / References / Confidence)",
            "domain-researcher": "(Answer / Citations / Confidence)",
        }
        for name, triple in expected.items():
            with self.subTest(agent=name):
                self.assertIn(
                    triple,
                    _terminal_deliverable(_claude_body(name)),
                    f"[{SHARED_GROUP}] {name}: the Terminal Deliverable must name this "
                    "agent's own Output Format sections",
                )

    def test_codex_mirrors_carry_the_shared_input_bullets(self) -> None:
        for name in ANALYSTS:
            with self.subTest(agent=name):
                section = _input_section(_codex_body(name))
                for bullet in SHARED_INPUT_BULLETS:
                    self.assertIn(
                        _codex_flavored(bullet),
                        section,
                        f"[{CODEX_GROUP}] {name}: the Codex Input block must mirror the "
                        "Claude Input bullets, with `$speckit-analyze` for "
                        "`/speckit-analyze`",
                    )

    def test_consensus_only_analysts_declare_three_input_types(self) -> None:
        for name in CONSENSUS_ONLY:
            with self.subTest(agent=name):
                self.assertEqual(
                    _input_lead_count_word(_claude_body(name)),
                    "three",
                    f"[{DISPATCH_GROUP}] {name}: this agent is reachable only through "
                    "the consensus protocol, so its Input block declares three types",
                )
                self.assertEqual(len(_input_bullets(_claude_body(name))), 3)

    def test_domain_researcher_declares_the_phase_7_research_dispatch(self) -> None:
        body = _claude_body(RESEARCH_ROLE)
        self.assertEqual(
            _input_lead_count_word(body),
            "four",
            f"[{DISPATCH_GROUP}] {RESEARCH_ROLE} has a second dispatch path: Phase 7 "
            "routes research and API-investigation tasks to it outside consensus "
            "(references/phase-execution.md routing rule 7c). Its Input block must "
            "declare four types, not three",
        )
        self.assertEqual(
            _input_bullets(body)[3],
            RESEARCH_TASK_BULLET,
            f"[{DISPATCH_GROUP}] {RESEARCH_ROLE}: the fourth Input bullet declares the "
            "Phase 7 research dispatch",
        )

    def test_codex_domain_researcher_mirrors_the_research_dispatch(self) -> None:
        section = _input_section(_codex_body(RESEARCH_ROLE))
        self.assertIn(
            "You will receive one of four types of input:",
            section,
            f"[{DISPATCH_GROUP}] {RESEARCH_ROLE}.toml must mirror the Claude Input lead "
            "line, because the Codex autopilot routes Phase 7 research the same way",
        )
        self.assertIn(
            _codex_flavored(RESEARCH_TASK_BULLET),
            section,
            f"[{DISPATCH_GROUP}] {RESEARCH_ROLE}.toml must mirror the fourth Input "
            "bullet",
        )


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(
        ConsensusAnalystSharedProseTests
    )


def main() -> int:
    return run_counted(build_suite(), label="test-consensus-analyst-shared-prose")


if __name__ == "__main__":
    raise SystemExit(main())
