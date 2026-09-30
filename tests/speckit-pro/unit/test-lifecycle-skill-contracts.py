#!/usr/bin/env python3
"""Lifecycle skill references, evals and templates agree with the shipped skills."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
SKILLS = REPO_ROOT / "speckit-pro" / "skills"
EVAL_DIRS = ("evals", "codex-evals")
sys.path.insert(0, str(TEST_ROOT / "lib"))

from test_result import run_counted  # noqa: E402


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def eval_text(directory: str, skill: str) -> str:
    return read(TEST_ROOT / "layer3-functional" / directory / f"{skill}-evals.json")


def frontmatter_value(text: str, key: str) -> str:
    match = re.search(rf"^{key}: (.+)$", text, re.MULTILINE)
    assert match, key
    return match.group(1).strip()


class LifecycleSkillContractTests(unittest.TestCase):
    def test_setup_design_concept_path_is_the_process_location(self) -> None:
        formats = read(SKILLS / "grill-me" / "references" / "output-formats.md")
        self.assertIn("docs/ai/specs/.process/<SPEC-ID>-design-concept.md", formats)
        self.assertNotIn("docs/ai/specs/<SPEC-ID>-design-concept.md", formats)
        for directory in EVAL_DIRS:
            with self.subTest(directory=directory):
                self.assertNotRegex(eval_text(directory, "grill-me"), r"docs/ai/specs/SPEC-\d+-design-concept\.md")

    def test_status_globs_reach_the_process_directory(self) -> None:
        status = read(SKILLS / "speckit-status" / "SKILL.md")
        for name in ("workflow", "design-concept"):
            self.assertIn(f"docs/ai/specs/.process/*-{name}.md", status)

    def test_status_frontmatter_and_body_agree_on_helper_calls(self) -> None:
        status = read(SKILLS / "speckit-status" / "SKILL.md")
        tools = frontmatter_value(status, "allowed-tools").split()
        if "Bash" in tools:
            return
        self.assertIn("are\nnot pre-approved", status)
        for helper in ("generate-spec-index-check", "o5-topology"):
            self.assertIn(helper, status)

    def test_prd_evals_number_the_crosswalk_like_the_template(self) -> None:
        template = read(SKILLS / "speckit-coach" / "templates" / "prd-template.md")
        heading = re.search(r"^## (\d+)\. SPEC Catalog Crosswalk$", template, re.MULTILINE)
        assert heading is not None
        section = heading.group(1)
        for directory in EVAL_DIRS:
            with self.subTest(directory=directory):
                text = eval_text(directory, "speckit-prd")
                self.assertIn(f"§{section} SPEC Catalog Crosswalk", text)
                self.assertNotRegex(text, r"§(?!" + section + r")\d+ SPEC Catalog Crosswalk")
                self.assertIn("Module and Interface Deltas", text)
                first = json.loads(text)["evals"][0]
                self.assertIn("roadmap-MOC", json.dumps(first))

    def test_workflow_template_defers_to_the_checklist_domain_guide(self) -> None:
        template = read(SKILLS / "speckit-coach" / "templates" / "workflow-template.md")
        self.assertNotIn("| Recommended Domain |", template)
        self.assertIn("references/checklist-domains-guide.md", template)


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(LifecycleSkillContractTests),
        label="test-lifecycle-skill-contracts",
    ))
