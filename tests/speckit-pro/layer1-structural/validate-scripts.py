#!/usr/bin/env python3
"""Structural validation for plugin script/template safety (port of validate-scripts.sh).

XPLAT-010 count-parity port (T035, US2). Python 3.11+ standard library only.
Asserts the plugin source contains zero live shell/command script files, validates
autopilot JSON contract syntax, and checks reviewability exception guidance in
the roadmap/spec/plan templates. Every former ``assert_*``/``_pass``/``_fail``
execution maps to one counted ``subTest`` unit; names reproduced verbatim via
``subTest(msg=...)`` for a 1:1 baseline match.

Baseline: ``tests/speckit-pro/parity/xplat-010/validate-scripts-baseline.txt``
(TOTAL: 37).
"""

from __future__ import annotations

import json
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

SCRIPT_SUFFIXES = {".sh", ".ps1", ".bat", ".cmd"}
SHELL_SHEBANG_RE = re.compile(r"^#!.*\b(?:bash|sh|zsh|powershell|pwsh)\b", re.IGNORECASE)

CONTRACT_FILES = (
    PLUGIN_ROOT / "skills/speckit-autopilot/contracts/final-reviewability-gate-state.schema.json",
    PLUGIN_ROOT / "skills/speckit-autopilot/contracts/reslicing-packet.schema.json",
    PLUGIN_ROOT / "skills/speckit-autopilot/contracts/routing-decision.schema.json",
    PLUGIN_ROOT / "skills/speckit-autopilot/contracts/o5-parent-manifest.schema.json",
)
ROADMAP_TEMPLATE = PLUGIN_ROOT / "skills/speckit-coach/templates/technical-roadmap-template.md"
SPEC_TEMPLATES = (
    REPO_ROOT / ".specify/presets/speckit-pro-reviewability/templates/spec-template.md",
    REPO_ROOT / ".specify/templates/spec-template.md",
)
PRESET_PLAN_TEMPLATE = REPO_ROOT / ".specify/presets/speckit-pro-reviewability/templates/plan-template.md"


def _rel_plugin(path: Path) -> str:
    return path.relative_to(PLUGIN_ROOT).as_posix()


def _rel_repo(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _live_script_count(root: Path) -> int:
    count = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in SCRIPT_SUFFIXES:
            count += 1
            continue
        if path.suffix:
            continue
        try:
            first_line = path.open("r", encoding="utf-8").readline(4096)
        except (OSError, UnicodeDecodeError):
            continue
        if SHELL_SHEBANG_RE.search(first_line):
            count += 1
    return count


class ValidateScripts(unittest.TestCase):
    def test_001_zero_live_script_files(self) -> None:
        with self.subTest(msg="speckit-pro: contains zero live shell/command script files"):
            script_count = _live_script_count(PLUGIN_ROOT)
            self.assertEqual(0, script_count, f"expected zero live plugin script files, found {script_count}")

    def test_002_autopilot_json_contracts(self) -> None:
        for contract_file in CONTRACT_FILES:
            contract = _rel_plugin(contract_file)
            with self.subTest(msg=f"{contract}: exists"):
                self.assertTrue(contract_file.is_file(), f"file not found: {contract_file}")

            with self.subTest(msg=f"{contract}: parses as JSON"):
                try:
                    json.loads(contract_file.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    self.fail(f"contract JSON parse failed: {exc}")

    def test_003_technical_roadmap_template_reviewability_vocabulary(self) -> None:
        with self.subTest(msg="technical-roadmap-template.md: exists"):
            self.assertTrue(ROADMAP_TEMPLATE.is_file(), f"file not found: {ROADMAP_TEMPLATE}")

        content = ROADMAP_TEMPLATE.read_text(encoding="utf-8") if ROADMAP_TEMPLATE.is_file() else ""
        contains_checks = (
            ("technical-roadmap-template.md: has Reviewability Contract section", "## Reviewability Contract"),
            ("technical-roadmap-template.md: advertises the production-LOC warn threshold", "400 reviewable production LOC"),
            ("technical-roadmap-template.md: advertises the production-LOC block threshold", "800 reviewable production LOC"),
            ("technical-roadmap-template.md: documents surface-count-as-warning rule", "more than one primary surface is also a warning"),
            ("technical-roadmap-template.md: documents the typed exception pragma", "Reviewability-Exception: <class>"),
            ("technical-roadmap-template.md: names the refactor exception class", "refactor"),
            ("technical-roadmap-template.md: names the infra exception class", "infra"),
            ("technical-roadmap-template.md: names the upgrade exception class", "upgrade"),
        )
        for name, needle in contains_checks:
            with self.subTest(msg=name):
                self.assertIn(needle, content)

        for klass in ("refactor", "infra", "upgrade"):
            with self.subTest(msg=f"technical-roadmap-template.md: no concrete '{klass}' exception pragma"):
                self.assertNotIn(f"Reviewability-Exception: {klass}", content)

    def test_004_spec_templates_generated_exception_safety(self) -> None:
        for spec_template in SPEC_TEMPLATES:
            template_name = _rel_repo(spec_template)
            with self.subTest(msg=f"{template_name}: exists"):
                self.assertTrue(spec_template.is_file(), f"file not found: {spec_template}")

            if not spec_template.is_file():
                continue
            template_content = spec_template.read_text(encoding="utf-8")
            with self.subTest(msg=f"{template_name}: names accepted exception classes"):
                self.assertIn("refactor, infra, and upgrade", template_content)
            with self.subTest(msg=f"{template_name}: explains invalid generated/template provenance"):
                self.assertIn("generated templates", template_content)
            for klass in ("refactor", "infra", "upgrade"):
                with self.subTest(msg=f"{template_name}: no concrete {klass} exception pragma"):
                    self.assertNotIn(f"Reviewability-Exception: {klass}", template_content)

    def test_005_reviewability_preset_plan_template_declared_files_format(self) -> None:
        with self.subTest(msg="reviewability-preset plan-template.md: exists"):
            self.assertTrue(PRESET_PLAN_TEMPLATE.is_file(), f"file not found: {PRESET_PLAN_TEMPLATE}")

        if not PRESET_PLAN_TEMPLATE.is_file():
            return
        preset_plan_content = PRESET_PLAN_TEMPLATE.read_text(encoding="utf-8")
        checks = (
            (
                "reviewability-preset plan-template.md: has Declared File Operations section",
                "## Declared File Operations",
            ),
            (
                "reviewability-preset plan-template.md: teaches the '- NEW' list-marker format the parser requires",
                "- NEW ",
            ),
            (
                "reviewability-preset plan-template.md: teaches the '- MODIFIED' list-marker format the parser requires",
                "- MODIFIED ",
            ),
        )
        for name, needle in checks:
            with self.subTest(msg=name):
                self.assertIn(needle, preset_plan_content)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateScripts)


def main() -> int:
    return run_counted(build_suite(), label="validate-scripts")


if __name__ == "__main__":
    raise SystemExit(main())
