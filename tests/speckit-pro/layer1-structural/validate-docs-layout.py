#!/usr/bin/env python3
"""Every tracked file under docs/ sits in a known place.

Per-PR notes once piled up at the docs/ top level. A new top-level file or
folder must be added here on purpose, so the layout a visitor reads stays
deliberate. Planning PRDs keep the speckit-pro convention docs/prd-<slug>.md.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from structural_helpers import tracked_files
from test_result import run_counted

ALLOWED_DIRECTORIES = frozenset({"adr", "agents", "ai", "architecture"})
ALLOWED_FILES = frozenset(
    {
        "agent-runbook.md",
        "compact-runner-answers.md",
        "phase-envelope.md",
        "roadmap-interactive-documentation.md",
        "traceability-interactive-documentation.md",
    }
)
PRD_FILE = re.compile(r"prd-[a-z0-9]+(?:-[a-z0-9]+)*\.md")


def layout_errors(tracked: list[str]) -> list[str]:
    errors: list[str] = []
    for path in sorted(name for name in tracked if name.startswith("docs/")):
        parts = path.split("/")
        if len(parts) > 2:
            if parts[1] not in ALLOWED_DIRECTORIES:
                errors.append(f"{path}: docs/{parts[1]}/ is not an allowed docs/ folder")
        elif parts[1] not in ALLOWED_FILES and not PRD_FILE.fullmatch(parts[1]):
            errors.append(f"{path}: not an allowed top-level docs/ file")
    return errors


class DocsLayout(unittest.TestCase):

    def test_allowed_paths_pass(self) -> None:
        tracked = [
            "docs/agent-runbook.md",
            "docs/prd-html-artifacts.md",
            "docs/adr/0001-x.md",
            "docs/ai/specs/.process/BRAND-001-workflow.md",
            "README.md",
        ]
        self.assertEqual(layout_errors(tracked), [])

    def test_new_top_level_note_is_reported(self) -> None:
        self.assertEqual(
            layout_errors(["docs/pr-1400-planning-drift-review.md"]),
            ["docs/pr-1400-planning-drift-review.md: not an allowed top-level docs/ file"],
        )

    def test_new_top_level_folder_is_reported(self) -> None:
        self.assertEqual(
            layout_errors(["docs/reviews/pr-1304-path-trust.md"]),
            ["docs/reviews/pr-1304-path-trust.md: docs/reviews/ is not an allowed docs/ folder"],
        )

    def test_prd_pattern_is_exact(self) -> None:
        near_misses = ["docs/prd-.md", "docs/prd-Foo.md", "docs/prd-x.md.bak", "docs/xprd-x.md"]
        reported = [error.split(":")[0] for error in layout_errors(near_misses)]
        self.assertEqual(reported, sorted(near_misses))

    def test_repository_docs_follow_the_layout(self) -> None:
        docs = [name for name in tracked_files(REPO_ROOT) if name.startswith("docs/")]
        self.assertNotEqual(docs, [], "no tracked docs found")
        self.assertEqual(layout_errors(docs), [])

def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-docs-layout")


if __name__ == "__main__":
    raise SystemExit(main())
