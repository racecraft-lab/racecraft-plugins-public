#!/usr/bin/env python3
"""Validate generated-artifact merge attributes."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

GITATTRIBUTES = REPO_ROOT / ".gitattributes"


def rules_scoped(text: str) -> bool:
    """Return True iff EVERY ``linguist-generated`` line is scoped to a
    ``.process/`` path segment. Mirrors the bash ``rules_scoped`` predicate: skip
    comment (``#``-leading) and blank lines; a ``linguist-generated`` line is
    scoped when it contains ``/.process/`` or starts with ``.process/`` (the bash
    ``*/.process/*|.process/*`` case), otherwise the file is broadened. A file
    with no ``linguist-generated`` lines is scoped (nothing to broaden)."""
    for line in text.splitlines():
        if line.startswith("#") or line == "":
            continue
        if "linguist-generated" in line:
            if "/.process/" in line or line.startswith(".process/"):
                continue
            return False
    return True


class ValidateProcessGitattributes(unittest.TestCase):
    def test_gitattributes_scope(self) -> None:
        with self.subTest(msg="repo-root .gitattributes exists"):
            self.assertTrue(GITATTRIBUTES.is_file(), f"file not found: {GITATTRIBUTES}")

        # Bash guards the file-reading checks behind `if [ -f ]` so a missing file
        # yields the single clean failure above rather than a crash.
        if GITATTRIBUTES.is_file():
            content = GITATTRIBUTES.read_text(encoding="utf-8")

            with self.subTest(msg="at least one linguist-generated rule is present"):
                self.assertIn(
                    "linguist-generated", content,
                    "no linguist-generated rule found in repo-root .gitattributes",
                )

            with self.subTest(msg="every linguist-generated rule is scoped to .process/"):
                self.assertTrue(
                    rules_scoped(content),
                    "a linguist-generated rule is broadened beyond .process/ (could match a CONTRACT artifact)",
                )

        # SC-005 positive + negative predicate cases (former mktemp fixtures).
        with self.subTest(msg="scoped rule passes (SC-005 positive case)"):
            self.assertTrue(rules_scoped("**/.process/** linguist-generated=true\n"))

        with self.subTest(msg="broadened rule fails (SC-005 negative case)"):
            self.assertFalse(rules_scoped("**/* linguist-generated=true\n"))

        # Regression guard (PR #111 review): a dir merely ENDING in ".process"
        # (foo.process/) is not the dedicated .process/ exhaust dir and must fail.
        with self.subTest(msg="rule for a dir ending in .process (foo.process/) fails — not the .process/ dir"):
            self.assertFalse(rules_scoped("**/foo.process/** linguist-generated=true\n"))


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateProcessGitattributes)


def main() -> int:
    return run_counted(build_suite(), label="validate-process-gitattributes")


if __name__ == "__main__":
    raise SystemExit(main())
