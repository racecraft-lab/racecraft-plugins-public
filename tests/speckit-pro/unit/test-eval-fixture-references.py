#!/usr/bin/env python3
"""Every functional and contract eval fixture is named by the catalog or a test.

A fixture no case reads looks like coverage and asserts nothing. The
functional root is checked per case directory (or per suite directory when it
has no case-* children); the contract roots are checked per file.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
FIXTURE_ROOT = TEST_ROOT / "evals" / "fixtures"
CATALOG = TEST_ROOT / "evals" / "catalog.json"
CHECKED_ROOTS = ("functional", "scaffold-contracts", "status-contracts")
sys.path.insert(0, str(TEST_ROOT / "lib"))

from test_result import run_counted  # noqa: E402


def reference_text(catalog: Path, tests_root: Path, exclude: Path) -> str:
    """The catalog plus every Python source under the test tree except ``exclude``."""
    sources = [catalog, *(path for path in sorted(tests_root.rglob("*.py")) if path != exclude)]
    return "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in sources)


def reference_unit(fixture_root: Path, relative: Path) -> str:
    """The path a catalog entry or test must name for ``relative`` to count as referenced."""
    parts = relative.parts
    if parts[0] != "functional":
        return relative.as_posix()
    if len(parts) == 2:
        return parts[1]
    suite = fixture_root / parts[0] / parts[1]
    has_cases = any(child.name.startswith("case-") for child in suite.iterdir())
    return "/".join(parts[:3] if has_cases else parts[:2])


def unreferenced_fixture_files(fixture_root: Path, roots: tuple[str, ...], text: str) -> list[str]:
    missing: list[str] = []
    for root in roots:
        for path in sorted((fixture_root / root).rglob("*")):
            if path.is_file() and reference_unit(fixture_root, path.relative_to(fixture_root)) not in text:
                missing.append(path.relative_to(fixture_root).as_posix())
    return missing


class EvalFixtureReferenceTests(unittest.TestCase):
    def test_every_checked_fixture_file_is_referenced(self) -> None:
        text = reference_text(CATALOG, TEST_ROOT, Path(__file__).resolve())
        self.assertEqual([], unreferenced_fixture_files(FIXTURE_ROOT, CHECKED_ROOTS, text))

    def test_an_unreferenced_case_directory_and_contract_file_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in (
                "functional/suite/case-1/a.md",
                "functional/suite/case-2/b.md",
                "functional/flat/c.md",
                "functional/top.json",
                "scaffold-contracts/one/used.txt",
                "scaffold-contracts/one/orphan.txt",
            ):
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
                (root / relative).write_text("x", encoding="utf-8")
            text = "functional/suite/case-1 functional/flat top.json scaffold-contracts/one/used.txt"
            self.assertEqual(
                ["functional/suite/case-2/b.md", "scaffold-contracts/one/orphan.txt"],
                unreferenced_fixture_files(root, ("functional", "scaffold-contracts"), text),
            )


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(EvalFixtureReferenceTests),
        label="test-eval-fixture-references",
    ))
