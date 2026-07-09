#!/usr/bin/env python3
"""Layer-1 skill pointer-coverage check (port of validate-skill-capability-pointers.sh).

XPLAT-010 count-parity port (T036, US2). Python 3.11+ standard library only.
Enforces universal-scope capability-discovery / grounding pointers across both
user-invocable skill surfaces:

* ``speckit-pro/skills/<name>/SKILL.md`` (Claude)
* ``speckit-pro/codex-skills/<name>/SKILL.md`` (Codex)

Every former ``_pass``/``_fail`` execution maps to one counted ``subTest`` unit;
names are reproduced via ``subTest(msg=...)`` for a 1:1 baseline match.

Environment-path normalization: the bash predecessor interpolated absolute
checkout paths into the skills-directory and built-payload-tree checks. As with
the PR 3a pointer/resolution ports, the absolute repo-root prefix is environment
noise and is normalized to repo-relative paths in both the port and baseline.

Baseline: ``tests/speckit-pro/parity/xplat-010/validate-skill-capability-pointers-baseline.txt``
(TOTAL: 55).
"""

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
from test_result import run_counted  # noqa: E402

CLAUDE_SKILLS_DIR = PLUGIN_ROOT / "skills"
CODEX_SKILLS_DIR = PLUGIN_ROOT / "codex-skills"
DIST_CLAUDE = REPO_ROOT / "dist" / "claude"
DIST_CODEX = REPO_ROOT / "dist" / "codex"

DIRECTIVE_MARKER = "capability-discovery.md"
GROUNDING_MARKER = "grounding.md"
PATH_TOKEN_RE = re.compile(r"speckit-pro/[A-Za-z0-9._/-]*capability-discovery\.md")
GROUNDING_TOKEN_RE = re.compile(r"speckit-pro/[A-Za-z0-9._/-]*grounding\.md")

EXCLUSIONS = frozenset(
    {
        "speckit-install",
        "install",
        "speckit-upgrade",
        "speckit-status",
        "speckit-archive-cleanup",
    }
)
HOST_SKILL = "speckit-autopilot"


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _skill_dirs(directory: Path) -> list[Path]:
    return sorted((p for p in directory.iterdir() if (p / "SKILL.md").is_file()), key=lambda p: p.name)


def _unique_matches(pattern: re.Pattern[str], text: str) -> list[str]:
    return sorted(set(pattern.findall(text)))


class ValidateSkillCapabilityPointers(unittest.TestCase):
    def setUp(self) -> None:
        self.found_tokens: list[str] = []

    def _token_seen(self, token: str) -> bool:
        return token in self.found_tokens

    def _collect_marker(
        self,
        runtime: str,
        skill: str,
        skill_file: Path,
        marker: str,
        pattern: re.Pattern[str],
    ) -> None:
        text = skill_file.read_text(encoding="utf-8", errors="replace")
        with self.subTest(msg=f"{runtime} skill '{skill}' references {marker}"):
            if marker not in text:
                self.fail(
                    f"in-scope skill '{skill}' ({runtime}) does not reference {marker} "
                    "(add the pointer, or record it in EXCLUSIONS with a reason - do NOT widen EXCLUSIONS to silence it)"
                )

        matches = _unique_matches(pattern, text)
        for token in matches:
            if not self._token_seen(token):
                self.found_tokens.append(token)
        with self.subTest(msg=f"{runtime} skill '{skill}' {marker} reference yields a repo-root-relative path token"):
            self.assertTrue(matches, f"skill references {marker} but no token matched {pattern.pattern} in {skill_file}")

    def _check_runtime(self, runtime: str, directory: Path) -> None:
        with self.subTest(msg=f"{runtime}: skills directory exists ({_rel(directory)})"):
            self.assertTrue(directory.is_dir(), f"skills directory missing: {_rel(directory)}")
        if not directory.is_dir():
            return

        skill_dirs = _skill_dirs(directory)
        with self.subTest(msg=f"{runtime}: at least one skill with a SKILL.md was found"):
            self.assertTrue(
                skill_dirs,
                f"no skills found under {_rel(directory)}/*/SKILL.md (empty glob - refusing to pass vacuously)",
            )
        if not skill_dirs:
            return

        for skill_dir in skill_dirs:
            skill = skill_dir.name
            skill_file = skill_dir / "SKILL.md"
            if skill in EXCLUSIONS:
                continue
            if skill == HOST_SKILL:
                text = skill_file.read_text(encoding="utf-8", errors="replace")
                with self.subTest(msg=f"{runtime} host skill '{skill}' references {DIRECTIVE_MARKER}"):
                    self.assertIn(
                        DIRECTIVE_MARKER,
                        text,
                        f"host skill '{skill}' ({runtime}) dropped its {DIRECTIVE_MARKER} reference",
                    )
                with self.subTest(msg=f"{runtime} host skill '{skill}' references {GROUNDING_MARKER}"):
                    self.assertIn(
                        GROUNDING_MARKER,
                        text,
                        f"host skill '{skill}' ({runtime}) dropped its {GROUNDING_MARKER} reference",
                    )
                continue
            self._collect_marker(runtime, skill, skill_file, DIRECTIVE_MARKER, PATH_TOKEN_RE)
            self._collect_marker(runtime, skill, skill_file, GROUNDING_MARKER, GROUNDING_TOKEN_RE)

    def test_skill_pointer_coverage_and_resolution(self) -> None:
        self._check_runtime("claude", CLAUDE_SKILLS_DIR)
        self._check_runtime("codex", CODEX_SKILLS_DIR)

        with self.subTest(msg="at least one skill directive/grounding token was collected"):
            self.assertTrue(
                self.found_tokens,
                "no skill path tokens collected - refusing to report resolution success on zero work",
            )
        if not self.found_tokens:
            return

        with self.subTest(msg=f"built Claude payload tree exists ({_rel(DIST_CLAUDE)})"):
            self.assertTrue(DIST_CLAUDE.is_dir(), f"missing built tree: {DIST_CLAUDE}")
        with self.subTest(msg=f"built Codex payload tree exists ({_rel(DIST_CODEX)})"):
            self.assertTrue(DIST_CODEX.is_dir(), f"missing built tree: {DIST_CODEX}")

        for token in self.found_tokens:
            with self.subTest(msg=f"resolves under dist/claude: {token}"):
                self.assertTrue(
                    (DIST_CLAUDE / token).is_file(),
                    f"skill reference correct in source but absent in built Claude tree (dist/claude/{token})",
                )
            with self.subTest(msg=f"resolves under dist/codex: {token}"):
                self.assertTrue(
                    (DIST_CODEX / token).is_file(),
                    f"skill reference correct in source but absent in built Codex tree (dist/codex/{token})",
                )


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateSkillCapabilityPointers)


def main() -> int:
    return run_counted(build_suite(), label="validate-skill-capability-pointers")


if __name__ == "__main__":
    raise SystemExit(main())
