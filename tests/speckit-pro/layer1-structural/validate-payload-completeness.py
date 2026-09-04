#!/usr/bin/env python3
"""Validate generated plugin payload completeness."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

SRC_SKILLS_DIR = REPO_ROOT / "speckit-pro" / "skills"
DIST_CLAUDE_SKILLS_DIR = REPO_ROOT / "dist" / "claude" / "speckit-pro" / "skills"

GUARD_HEADING = "## Codex Skill-Selection Guard"
LINE_SLACK = 5


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def guard_section_lines(text: str) -> int:
    """Mirror the awk guard-section counter: from the guard heading (inclusive)
    up to (not including) the next level-2 ``## `` heading or EOF. A ``### ``
    sub-heading is part of the guard section. 0 when no guard heading is present."""
    in_guard = False
    count = 0
    for line in text.splitlines():
        if not in_guard:
            if line == GUARD_HEADING:
                in_guard = True
                count = 1
        else:
            if line.startswith("## "):
                in_guard = False
            else:
                count += 1
    return count


def last_non_guard_heading(text: str) -> str:
    """Mirror the awk last-non-guard-heading finder: the text of the LAST level-2
    ``## `` heading (not ``### ``, not the guard heading). Empty if none."""
    last = ""
    for line in text.splitlines():
        if line.startswith("## ") and not line.startswith("### ") and line != GUARD_HEADING:
            last = line
    return last


class ValidatePayloadCompleteness(unittest.TestCase):
    def test_body_completeness(self) -> None:
        with self.subTest(msg=f"built Claude skills directory exists ({_rel(DIST_CLAUDE_SKILLS_DIR)})"):
            self.assertTrue(
                DIST_CLAUDE_SKILLS_DIR.is_dir(),
                f"built Claude skills directory missing: {_rel(DIST_CLAUDE_SKILLS_DIR)} "
                "(run python3 scripts/build-plugin-payloads.py)",
            )
        if not DIST_CLAUDE_SKILLS_DIR.is_dir():
            return

        dist_skills = sorted(
            (p for p in DIST_CLAUDE_SKILLS_DIR.glob("*/SKILL.md") if p.is_file()),
            key=lambda p: p.as_posix(),
        )
        with self.subTest(msg="built Claude skills glob matched at least one SKILL.md"):
            self.assertTrue(
                dist_skills,
                f"no built Claude SKILL.md found under {_rel(DIST_CLAUDE_SKILLS_DIR)}/*/SKILL.md "
                "(empty glob — refusing to pass vacuously)",
            )
        if not dist_skills:
            return

        for dist_file in dist_skills:
            skill_name = dist_file.parent.name
            src_file = SRC_SKILLS_DIR / skill_name / "SKILL.md"

            src_ok = src_file.is_file() and os.access(src_file, os.R_OK)
            with self.subTest(msg=f"[{skill_name}] source SKILL.md exists and is readable ({_rel(src_file)})"):
                self.assertTrue(src_ok, f"built skill '{skill_name}' has no readable source SKILL.md at {_rel(src_file)}")
            if not src_ok:
                continue

            dist_ok = os.access(dist_file, os.R_OK)
            with self.subTest(msg=f"[{skill_name}] built SKILL.md is readable ({_rel(dist_file)})"):
                self.assertTrue(dist_ok, f"built skill '{skill_name}' SKILL.md is not readable at {_rel(dist_file)}")
            if not dist_ok:
                continue

            src_text = src_file.read_text(encoding="utf-8", errors="replace")
            anchor = last_non_guard_heading(src_text)
            with self.subTest(msg=f"[{skill_name}] source has a non-guard level-2 heading to anchor on"):
                self.assertNotEqual(
                    "", anchor,
                    f"source SKILL.md for '{skill_name}' has no non-guard '## ' heading — cannot anchor completeness",
                )
            if anchor == "":
                continue

            dist_text = dist_file.read_text(encoding="utf-8", errors="replace")
            with self.subTest(msg=f"[{skill_name}] last non-guard source heading survives in built body: '{anchor}'"):
                self.assertIn(
                    anchor, dist_text,
                    f"built '{skill_name}' SKILL.md is missing the last non-guard source heading "
                    f"('{anchor}') — body truncated",
                )

            # wc -l semantics == newline-byte count; guard measured on text lines.
            src_lines = src_file.read_bytes().count(b"\n")
            dist_lines = dist_file.read_bytes().count(b"\n")
            guard_lines = guard_section_lines(src_text)
            expected = src_lines - guard_lines
            diff = abs(dist_lines - expected)
            with self.subTest(
                msg=f"[{skill_name}] built body length within tolerance of source-minus-guard "
                f"(dist={dist_lines}, expected≈{expected}, guard={guard_lines})"
            ):
                self.assertLessEqual(
                    diff, LINE_SLACK,
                    f"built '{skill_name}' SKILL.md has {dist_lines} lines; expected ≈{expected} "
                    f"(source {src_lines} − guard {guard_lines}), off by {diff} (> {LINE_SLACK}) — likely truncated",
                )


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidatePayloadCompleteness)


def main() -> int:
    return run_counted(build_suite(), label="validate-payload-completeness")


if __name__ == "__main__":
    raise SystemExit(main())
