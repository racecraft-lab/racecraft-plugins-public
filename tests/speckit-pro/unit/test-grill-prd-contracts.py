#!/usr/bin/env python3
"""Behavior contracts for the user-facing Grill Me and PRD skills."""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
CLAUDE_GRILL = PLUGIN_ROOT / "skills/grill-me/SKILL.md"
CODEX_GRILL = PLUGIN_ROOT / "codex-skills/grill-me/SKILL.md"
CLAUDE_PRD = PLUGIN_ROOT / "skills/speckit-prd/SKILL.md"
CODEX_PRD = PLUGIN_ROOT / "codex-skills/speckit-prd/SKILL.md"
OWNED_ROOTS = (
    PLUGIN_ROOT / "skills/grill-me",
    PLUGIN_ROOT / "codex-skills/grill-me",
    PLUGIN_ROOT / "skills/speckit-prd",
    PLUGIN_ROOT / "codex-skills/speckit-prd",
)
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)#]+\.md)(?:#[^)]+)?\)")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def combined(root: Path) -> str:
    return "\n".join(read(path) for path in sorted(root.rglob("*.md")))


def skill_contract(skill: Path) -> str:
    text = read(skill)
    resources = []
    for link in MARKDOWN_LINK.findall(text):
        target = (skill.parent / link).resolve()
        if target.is_file() and target != skill:
            resources.append(read(target))
    return "\n".join([text, *resources])


def assert_terms(test: unittest.TestCase, text: str, *groups: tuple[str, ...]) -> None:
    lowered = text.lower()
    for alternatives in groups:
        test.assertTrue(
            any(term.lower() in lowered for term in alternatives),
            f"missing semantic contract: one of {alternatives}",
        )


def assert_local_links_resolve(test: unittest.TestCase, skill: Path) -> None:
    links = [link for link in MARKDOWN_LINK.findall(read(skill)) if not link.startswith(("http://", "https://"))]
    test.assertTrue(links, f"{skill} must directly link its required references")
    for link in links:
        test.assertTrue((skill.parent / link).resolve().is_file(), f"unresolved reference from {skill}: {link}")


def linked_reference(skill: Path, filename: str) -> str:
    matches = []
    for link in MARKDOWN_LINK.findall(read(skill)):
        target = (skill.parent / link).resolve()
        if target.name == filename and target.is_file():
            matches.append(target)
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one linked {filename} from {skill}, found {matches}")
    return read(matches[0])


def markdown_section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        return ""
    return match.group("body")


def paragraph_matches(text: str, *patterns: str) -> bool:
    paragraphs = (" ".join(paragraph.split()) for paragraph in re.split(r"\n\s*\n", text))
    return any(all(re.search(pattern, paragraph, re.IGNORECASE) for pattern in patterns) for paragraph in paragraphs)


def prd_update_contract_violations(protocol: str) -> set[str]:
    update_modes = markdown_section(protocol, "Input and update modes")
    prd_authoring = markdown_section(protocol, "Author or update the PRD")
    violations = set()
    if not paragraph_matches(update_modes, r"\*\*Update", r"existing PRD", r"revise.+in place"):
        violations.add("update in place")
    if not paragraph_matches(
        update_modes,
        r"preserve.+feature.+acceptance.+SPEC identifiers",
        r"unchanged work",
    ):
        violations.add("stable identifiers")
    if not paragraph_matches(
        update_modes,
        r"permanently reserved",
        r"never.+(?:renumber|reuse).+retired identifier",
        r"new identifier.+above.+historical use",
    ):
        violations.add("retired identifiers")
    if not paragraph_matches(update_modes, r"roadmap.+roadmap-MOC.+exists", r"update it"):
        violations.add("existing roadmap updates")
    if not paragraph_matches(
        update_modes,
        r"never backfill",
        r"missing roadmap-MOC",
        r"legacy roadmap",
        r"unless the user asks",
    ):
        violations.add("legacy MOC no-backfill")
    if not paragraph_matches(prd_authoring, r"preserve.+confirmed path", r"update mode"):
        violations.add("existing PRD path")
    return violations


def codex_fallback_contract_violations(skill_text: str) -> set[str]:
    boundary = markdown_section(skill_text, "Interactive boundary")
    adapter = markdown_section(skill_text, "Codex interaction adapter")
    violations = set()
    if not paragraph_matches(
        boundary,
        r"allowed entry points",
        r"active user",
        r"before any question or write",
        r"direct reply",
    ):
        violations.add("foreground eligibility")
    if not paragraph_matches(
        boundary,
        r"abort",
        r"background or non-interactive",
        r"codex exec",
        r"\bCI\b",
        r"\bautopilot\b",
        r"\bsubagent\b",
        r"do not ask",
        r"do not write",
    ):
        violations.add("autonomous hard stop")
    if not paragraph_matches(
        adapter,
        r"free-text fallback",
        r"allowed only",
        r"already active user chat",
        r"exactly one question",
        r"wait.+direct reply",
    ):
        violations.add("foreground-only fallback")
    if not paragraph_matches(
        adapter,
        r"never use this fallback",
        r"\bbackground\b",
        r"\bCI\b",
        r"\bautopilot\b",
        r"\bsubagent\b",
    ):
        violations.add("fallback prohibition")
    return violations


def remove_once(text: str, pattern: str) -> str:
    mutated, count = re.subn(pattern, "", text, count=1, flags=re.IGNORECASE | re.DOTALL)
    if count != 1:
        raise AssertionError(f"mutation did not match exactly once: {pattern}")
    return mutated


def remove_from_section_once(text: str, heading: str, pattern: str) -> str:
    section = markdown_section(text, heading)
    if not section:
        raise AssertionError(f"missing section for mutation: {heading}")
    return text.replace(section, remove_once(section, pattern), 1)


class GrillPrdContracts(unittest.TestCase):
    def test_grill_interaction_and_no_write_boundary(self) -> None:
        claude = skill_contract(CLAUDE_GRILL)
        codex = skill_contract(CODEX_GRILL)
        for text in (claude, codex):
            assert_terms(
                self,
                text,
                ("one question at a time", "one decision at a time", "exactly one question"),
                ("mutually exclusive", "multiselect: false"),
                ("(recommended)",),
                ("active user", "live user", "real user"),
                ("background",),
                ("autopilot",),
                ("subagent", "agent context"),
                ("ci",),
                ("do not write", "write no file", "nothing written"),
            )
        self.assertIn("AskUserQuestion", claude)
        self.assertIn("request_user_input", codex)

    def test_codex_grill_picker_preference_and_live_chat_fallback(self) -> None:
        self.assertEqual(set(), codex_fallback_contract_violations(read(CODEX_GRILL)))

    def test_codex_grill_fallback_boundary_rejects_semantic_mutations(self) -> None:
        original = read(CODEX_GRILL)
        mutations = (
            (
                "foreground-only fallback",
                remove_from_section_once(
                    original,
                    "Codex interaction adapter",
                    r"allowed only in the already active user chat",
                ),
            ),
            (
                "fallback prohibition",
                remove_from_section_once(original, "Codex interaction adapter", r"\bbackground\b"),
            ),
            (
                "fallback prohibition",
                remove_from_section_once(original, "Codex interaction adapter", r"\bCI\b"),
            ),
            (
                "fallback prohibition",
                remove_from_section_once(original, "Codex interaction adapter", r"\bautopilot\b"),
            ),
            (
                "fallback prohibition",
                remove_from_section_once(original, "Codex interaction adapter", r"\bsubagent\b"),
            ),
        )
        for expected_violation, mutated in mutations:
            with self.subTest(mutation=expected_violation):
                self.assertIn(expected_violation, codex_fallback_contract_violations(mutated))

    def test_codex_mutating_skills_require_explicit_invocation(self) -> None:
        for skill in (CODEX_GRILL, CODEX_PRD):
            sidecar = read(skill.parent / "agents/openai.yaml")
            values = re.findall(r"^\s*allow_implicit_invocation:\s*(\w+)\s*$", sidecar, re.MULTILINE)
            self.assertEqual(["false"], values)

    def test_grill_output_records_decisions_and_handoffs(self) -> None:
        for skill in (CLAUDE_GRILL, CODEX_GRILL):
            text = skill_contract(skill)
            assert_terms(
                self,
                text,
                ("design concept",),
                ("goals",),
                ("non-goals",),
                ("design tree", "q&a log"),
                ("recommended answer",),
                ("user's answer", "user answer"),
                ("open questions",),
                ("recommended next step",),
                ("standalone",),
                ("setup",),
                ("estimate-spec-size",),
                ("advisory",),
            )

    def test_prd_creation_and_three_artifact_handoff(self) -> None:
        for skill in (CLAUDE_PRD, CODEX_PRD):
            text = skill_contract(skill)
            assert_terms(
                self,
                text,
                ("create", "author"),
                ("one question at a time",),
                ("feature",),
                ("acceptance criteria",),
                ("1:1", "one spec per feature"),
                ("technical roadmap",),
                ("roadmap-moc",),
                ("generate-spec-index-write",),
                ("consumer", "project root"),
                ("reciprocal",),
                ("scaffold-spec",),
            )
        self.assertIn("AskUserQuestion", read(CLAUDE_PRD))
        self.assertIn("request_user_input", read(CODEX_PRD))

    def test_prd_update_protocol_is_linked_and_complete(self) -> None:
        for skill in (CLAUDE_PRD, CODEX_PRD):
            protocol = linked_reference(skill, "prd-authoring-protocol.md")
            self.assertEqual(set(), prd_update_contract_violations(protocol))

    def test_prd_update_contract_rejects_semantic_mutations(self) -> None:
        protocol = linked_reference(CLAUDE_PRD, "prd-authoring-protocol.md")
        if prd_update_contract_violations(protocol):
            self.skipTest("base PRD update contract must be complete before mutation checks")
        mutations = {
            "stable identifiers": remove_once(
                protocol,
                r"Preserve stable feature, acceptance-criteria, and\s+SPEC identifiers for unchanged work\.\s*",
            ),
            "retired identifiers": remove_once(
                protocol,
                r"Issued Feature, acceptance-criteria, and\s+SPEC identifiers are permanently reserved\..+?historical use\.\s*",
            ),
            "existing roadmap updates": remove_once(
                protocol,
                r"If its\s+roadmap or roadmap-MOC exists,\s+update it to keep the crosswalk and navigation\s+consistent\.\s*",
            ),
            "legacy MOC no-backfill": remove_once(
                protocol,
                r"Never backfill a\s+missing roadmap-MOC onto a legacy roadmap unless\s+the user asks\.\s*",
            ),
            "existing PRD path": remove_once(
                protocol,
                r"preserve the confirmed path in update\s+mode\.\s*",
            ),
        }
        for expected_violation, mutated in mutations.items():
            with self.subTest(mutation=expected_violation):
                self.assertIn(expected_violation, prd_update_contract_violations(mutated))

    def test_prd_decomposition_is_vertical_not_layer_first(self) -> None:
        text = combined(CLAUDE_PRD.parent)
        assert_terms(self, text, ("vertical",), ("end-to-end",), ("spidr",), ("invest",))
        self.assertNotRegex(text.lower(), r"different system layers[^\n]*one (?:feature|spec)[^\n]*per layer")

    def test_owned_guidance_has_no_fixed_project_spec_ids(self) -> None:
        text = "\n".join(combined(root) for root in OWNED_ROOTS)
        self.assertNotRegex(text, r"\b(?:ART|CAR|G56R|RDL|SPEC|XPLAT)-\d{3,}\b")

    def test_shared_references_resolve_in_source(self) -> None:
        for skill in (CLAUDE_GRILL, CODEX_GRILL, CLAUDE_PRD, CODEX_PRD):
            assert_local_links_resolve(self, skill)

    def test_shared_references_resolve_in_installed_payloads(self) -> None:
        sys.path.insert(0, str(PLUGIN_ROOT))
        from speckit_pro_runner.gates.payloads import build_installed_plugin_payloads

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            build_installed_plugin_payloads(REPO_ROOT, output)
            for platform in ("claude", "codex"):
                installed = output / platform / "speckit-pro/skills"
                for name in ("grill-me", "speckit-prd"):
                    assert_local_links_resolve(self, installed / name / "SKILL.md")
            claude_grill = read(output / "claude/speckit-pro/skills/grill-me/SKILL.md")
            self.assertNotIn("Codex Skill-Selection Guard", claude_grill)


if __name__ == "__main__":
    unittest.main()
