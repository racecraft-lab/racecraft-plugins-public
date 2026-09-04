#!/usr/bin/env python3
"""Validate the structural shape of Claude skill directories."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from structural_helpers import body as _body  # noqa: E402
from structural_helpers import frontmatter as _frontmatter  # noqa: E402
from test_result import run_counted  # noqa: E402

SKILLS_DIR = PLUGIN_ROOT / "skills"
SKILLS = (
    "grill-me",
    "speckit-archive-cleanup",
    "speckit-autopilot",
    "speckit-coach",
    "speckit-install",
    "speckit-upgrade",
    "speckit-scaffold-spec",
    "speckit-status",
    "speckit-resolve-pr",
    "speckit-prd",
)
SKILLS_REQUIRING_REFERENCES = frozenset({"speckit-autopilot", "speckit-coach"})
ALLOWED_KEYS = frozenset(
    {
        "name",
        "description",
        "license",
        "allowed-tools",
        "metadata",
        "compatibility",
        "user-invocable",
        "disable-model-invocation",
        "argument-hint",
    }
)
NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
TOP_LEVEL_KEY_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*):", re.MULTILINE)


def _field(frontmatter: str, key: str) -> str:
    for line in frontmatter.splitlines():
        if line.startswith(f"{key}:"):
            value = re.sub(rf"^{key}:[ \t]*", "", line)
            return value.replace('"', "").replace("'", "")
    return ""


def _description_value(frontmatter: str) -> str:
    block = re.search(r"description:\s*([>|])\s*\n((?:\s+.*\n?)*)", frontmatter)
    if block:
        return " ".join(line.strip() for line in block.group(2).split("\n") if line.strip())
    inline = re.search(r'description:\s*"([^"]*)"|description:\s*(.+)', frontmatter)
    if inline:
        return (inline.group(1) or inline.group(2) or "").strip()
    return ""


class ValidateSkills(unittest.TestCase):
    def test_skills(self) -> None:
        for skill in SKILLS:
            skill_dir = SKILLS_DIR / skill
            skill_file = skill_dir / "SKILL.md"

            with self.subTest(msg=f"{skill}: SKILL.md exists"):
                self.assertTrue(skill_file.is_file(), f"file not found: {skill_file}")
            if not skill_file.is_file():
                continue

            content = skill_file.read_text(encoding="utf-8")
            lines = content.splitlines()
            first_line = lines[0] if lines else ""

            with self.subTest(msg=f"{skill}: YAML frontmatter present (starts with ---)"):
                self.assertEqual("---", first_line, "first line must be ---")

            with self.subTest(msg=f"{skill}: has closing ---"):
                fence_count = sum(1 for line in lines if line == "---")
                self.assertGreaterEqual(fence_count, 2, f"expected at least 2 '---' lines, found {fence_count}")

            frontmatter = _frontmatter(lines)
            name_val = _field(frontmatter, "name")

            with self.subTest(msg=f"{skill}: name: field exists and is kebab-case"):
                if not name_val:
                    self.fail("name field is missing")
                self.assertRegex(name_val, NAME_RE, "name must be kebab-case")

            with self.subTest(msg=f"{skill}: name max 64 chars"):
                self.assertLessEqual(len(name_val), 64, f"name is {len(name_val)} chars (max 64)")

            with self.subTest(msg=f"{skill}: description: field exists"):
                self.assertIn("description:", frontmatter)

            desc_val = _description_value(frontmatter)
            with self.subTest(msg=f"{skill}: description max 1024 chars"):
                self.assertLessEqual(len(desc_val), 1024, f"description is {len(desc_val)} chars (max 1024)")

            with self.subTest(msg=f"{skill}: description has no angle brackets"):
                self.assertNotRegex(desc_val, r"[<>]", "description contains angle brackets")

            with self.subTest(msg=f"{skill}: only allowed frontmatter keys"):
                found_keys = TOP_LEVEL_KEY_RE.findall(frontmatter)
                bad_keys = [key for key in found_keys if key not in ALLOWED_KEYS]
                self.assertEqual([], bad_keys, "disallowed frontmatter keys:" + "".join(f" {key}" for key in bad_keys))

            body = _body(lines)
            with self.subTest(msg=f"{skill}: body content exists"):
                self.assertTrue(body.strip(), "body must contain non-whitespace content")

            if skill == "grill-me":
                with self.subTest(msg="grill-me: Claude variant requires AskUserQuestion"):
                    self.assertTrue(
                        "Confirm `AskUserQuestion` is available in your tool list" in body
                        and "the only sanctioned interview mechanism in the Claude Code variant" in body
                        and "Call `AskUserQuestion` with the question" in body,
                        "expected Claude grill-me to require AskUserQuestion as the interview mechanism",
                    )

                with self.subTest(msg="grill-me: compatibility text does not document stale Codex free-text loop"):
                    self.assertTrue(
                        "AskUserQuestion tool support" in frontmatter
                        and "request_user_input when available" in frontmatter
                        and "uses a free-text Q&A loop instead" not in content,
                        "expected grill-me compatibility text to avoid the obsolete Codex free-text-loop contract",
                    )

            if skill == "speckit-scaffold-spec":
                with self.subTest(msg="speckit-scaffold-spec: skill heading uses scaffold naming"):
                    self.assertTrue(
                        re.search(r"^# SpecKit Scaffold Spec$", content, re.MULTILINE) is not None
                        and re.search(r"^# SpecKit Setup$", content, re.MULTILINE) is None,
                        "expected '# SpecKit Scaffold Spec' heading in skills/speckit-scaffold-spec/SKILL.md",
                    )

                with self.subTest(msg="speckit-scaffold-spec: completion report uses scaffold naming"):
                    self.assertTrue(
                        re.search(r"^## Scaffold Complete$", content, re.MULTILINE) is not None
                        and re.search(r"^## Setup Complete$", content, re.MULTILINE) is None,
                        "expected '## Scaffold Complete' report heading in skills/speckit-scaffold-spec/SKILL.md",
                    )

            with self.subTest(msg=f"{skill}: references directory exists if required"):
                if skill in SKILLS_REQUIRING_REFERENCES:
                    self.assertTrue(
                        (skill_dir / "references").is_dir(),
                        f"references directory not found at {skill_dir / 'references'}",
                    )
                else:
                    self.assertTrue(True)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateSkills)


def main() -> int:
    return run_counted(build_suite(), label="validate-skills")


if __name__ == "__main__":
    raise SystemExit(main())
