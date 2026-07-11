#!/usr/bin/env python3
"""Unit tests for the Layer 8 section/table extractors.

Port of ``test-parity-extractors.sh`` (XPLAT-010 T073). The count-parity
baseline is pinned at
``tests/speckit-pro/parity/bash-to-python/test-parity-extractors-baseline.txt``.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
EXTRACTORS_LIB = TESTS_ROOT / "layer8-parity" / "lib"
EXTRACTORS = EXTRACTORS_LIB / "extractors.py"
SHARED_LIB = TESTS_ROOT / "lib"
for value in (EXTRACTORS_LIB, SHARED_LIB):
    if str(value) not in sys.path:
        sys.path.insert(0, str(value))

import extractors  # noqa: E402
from test_result import run_counted  # noqa: E402


def run_extractor(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(EXTRACTORS), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )


class Layer8ExtractorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.fixture_dir = Path(self._tmp.name)
        self.fixture = self.fixture_dir / "workflow.md"
        self.fixture.write_text(
            textwrap.dedent(
                """\
                # Workflow Overview

                | Phase | Status | Notes |
                |-------|--------|-------|
                | Specify | PASS | ok |
                | Plan | FAIL | bad |

                ## Post-Implementation Checklist

                | Task | Status | Findings |
                |------|--------|----------|
                | 10 | PASS | doctor clean |
                | 11 | PASS | review approved |
                | 12 | FAIL | regression in foo |

                ### Notes Subsection

                This H3 must remain inside the H2 body.

                ## Consensus Resolution Log

                | Item | Round | Result |
                |------|-------|--------|
                | Q1 | 1 | resolved |
                | Q2 | 2 | resolved |
                """
            ),
            encoding="utf-8",
        )
        self.empty_table_fixture = self.fixture_dir / "empty-table.md"
        self.empty_table_fixture.write_text(
            textwrap.dedent(
                """\
                ## Empty Table

                | A | B |
                |---|---|

                ## Next Section
                """
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_extractors_contract(self) -> None:
        output = extractors.extract_section(self.fixture, "Post-Implementation Checklist")
        with self.subTest(msg="stops at next H2, includes H3 subsection inside body"):
            self.assertIn("regression in foo", output)
        with self.subTest(msg="stops at next H2, includes H3 subsection inside body"):
            self.assertIn("### Notes Subsection", output)
        with self.subTest(msg="stops at next H2, includes H3 subsection inside body"):
            self.assertIn("This H3 must remain inside", output)
        with self.subTest(msg="stops at next H2, includes H3 subsection inside body"):
            self.assertNotIn("Consensus Resolution Log", output)

        with self.subTest(msg="missing section emits nothing (rc=0)"):
            output = extractors.extract_section(self.fixture, "Nonexistent Section")
            self.assertEqual("", output)

        with self.subTest(msg="first H2 section (Post-Implementation Checklist) → 3 data rows"):
            result = extractors.extract_table_row_count(self.fixture, "Post-Implementation Checklist")
            self.assertEqual("3", result)

        with self.subTest(msg="second H2 section (Consensus Resolution Log) → 2 data rows"):
            result = extractors.extract_table_row_count(self.fixture, "Consensus Resolution Log")
            self.assertEqual("2", result)

        with self.subTest(msg="missing section returns non-zero exit code"):
            with self.assertRaises(extractors.ExtractorError):
                extractors.extract_table_row_count(self.fixture, "Nonexistent")

        with self.subTest(msg="Status column → PASS\\nPASS\\nFAIL (newline-separated)"):
            result = extractors.extract_table_column(self.fixture, "Post-Implementation Checklist", "Status")
            self.assertEqual("PASS\nPASS\nFAIL", result)

        result = extractors.extract_table_column(self.fixture, "Post-Implementation Checklist", "Findings")
        with self.subTest(msg="Findings column preserves text"):
            self.assertIn("doctor clean", result)
        with self.subTest(msg="Findings column preserves text"):
            self.assertIn("regression in foo", result)

        with self.subTest(msg="case-sensitive — wrong casing returns non-zero"):
            with self.assertRaises(extractors.ExtractorError):
                extractors.extract_table_column(self.fixture, "Post-Implementation Checklist", "status")

        with self.subTest(msg="Consensus Resolution Log: Result column → 2 values"):
            result = extractors.extract_table_column(self.fixture, "Consensus Resolution Log", "Result")
            line_count = len(result.splitlines())
            self.assertEqual(2, line_count)

        with self.subTest(msg="table with header + separator only → row_count=0"):
            result = extractors.extract_table_row_count(self.empty_table_fixture, "Empty Table")
            self.assertEqual("0", result)

        with self.subTest(msg="table with no data rows → column extract emits nothing"):
            result = extractors.extract_table_column(self.empty_table_fixture, "Empty Table", "A")
            self.assertEqual("", result)

        with self.subTest(msg="CLI subcommand row-count returns expected value"):
            result = run_extractor("row-count", str(self.fixture), "Post-Implementation Checklist")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("3", result.stdout.strip())

        result = run_extractor("column", str(self.fixture), "Post-Implementation Checklist", "Status")
        with self.subTest(msg="CLI subcommand column returns expected value"):
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("PASS", result.stdout)
        with self.subTest(msg="CLI subcommand column returns expected value"):
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("FAIL", result.stdout)

        with self.subTest(msg="CLI invalid subcommand → exit 2"):
            result = run_extractor("bogus")
            self.assertEqual(2, result.returncode)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer8ExtractorTests)
    raise SystemExit(run_counted(suite, label="test-parity-extractors"))
