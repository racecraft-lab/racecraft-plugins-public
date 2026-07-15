#!/usr/bin/env python3
"""Contracts for the purpose-based unit-test and fixture layout."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
UNIT_ROOT = TEST_ROOT / "unit"
FIXTURE_ROOT = UNIT_ROOT / "fixtures"
LIB_DIR = TEST_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


SPEC_ID_NAME = re.compile(r"(?:^|[-_])(?:doc|prsg|spec|tacd|xplat)-\d", re.IGNORECASE)
PURPOSE_NAMED_ROOTS = (
    FIXTURE_ROOT,
    TEST_ROOT / "parity",
    TEST_ROOT / "layer7-integration" / "dispatch-fixtures",
    TEST_ROOT / "layer8-parity",
)
LEGACY_LAYOUT_PATHS = (
    "tests/speckit-pro/layer4-scripts",
    "tests/speckit-pro/parity/xplat-010",
    "fixtures/xplat-005-feature",
    "fixtures/xplat-007-gates",
    "fixtures/xplat-008-release",
    "fixtures/xplat-009-zero-bash",
    "fixtures/xplat-010-confinement",
    "fixtures/prsg-012-feature",
    "fixtures/o5-topology",
    "22-prsg-014-stack-manager-replay",
    "02-prsg-011-migration-guidance",
    "03-prsg-010-backstop-o5-routing",
    "04-prsg-014-stack-manager-guidance",
    "test-l6-codex-runner",
    "test-l8-extractors",
    "test-l8-judge",
    "test-layer1-validator-regressions",
    "test-layer2-signal-restoration",
    "test-layer2-trigger-runners",
    "test-layer6-portability",
    "test-layer7-runners",
    "test-layer8-runner",
    "test-check-toolchain-pr10-baseline.txt",
)


class UnitLayoutTests(unittest.TestCase):
    def test_unit_directory_replaces_the_opaque_layer_name(self) -> None:
        self.assertTrue(UNIT_ROOT.is_dir())
        self.assertFalse((UNIT_ROOT.parent / "layer4-scripts").exists())

    def test_support_paths_are_purpose_named(self) -> None:
        violations: list[str] = []
        for root in PURPOSE_NAMED_ROOTS:
            for path in root.rglob("*"):
                relative = path.relative_to(root)
                for part in relative.parts:
                    if part == "specs":
                        break
                    if SPEC_ID_NAME.search(part):
                        violations.append(f"{root.relative_to(TEST_ROOT)}/{relative}")
                        break
        self.assertEqual(violations, [])

    def test_support_fixture_ids_follow_purpose_directories(self) -> None:
        violations: list[str] = []
        for root in PURPOSE_NAMED_ROOTS:
            for path in root.rglob("*.json"):
                relative = path.relative_to(root)
                if "specs" in relative.parts:
                    continue
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    # Negative fixtures intentionally include malformed JSON.
                    continue
                if not isinstance(payload, dict):
                    continue
                fixture_id = payload.get("fixture_id")
                if not isinstance(fixture_id, str):
                    continue
                purpose = path.parent.name
                purpose_aligned = fixture_id == purpose or fixture_id.startswith(f"{purpose}-")
                if SPEC_ID_NAME.search(fixture_id) or not purpose_aligned:
                    violations.append(
                        f"{path.relative_to(TEST_ROOT)}: {fixture_id!r} does not match {purpose!r}"
                    )
        self.assertEqual(violations, [])

    def test_unit_test_method_names_are_behavior_named(self) -> None:
        violations: list[str] = []
        for path in sorted(UNIT_ROOT.glob("test-*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    if SPEC_ID_NAME.search(node.name):
                        violations.append(f"{path.relative_to(TEST_ROOT)}::{node.name}")
        self.assertEqual(violations, [])

    def test_tracked_paths_have_no_legacy_layout_names(self) -> None:
        completed = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            shell=False,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        matches = [
            path
            for path in completed.stdout.splitlines()
            if any(legacy in path for legacy in LEGACY_LAYOUT_PATHS)
        ]
        self.assertEqual(matches, [], completed.stdout + completed.stderr)

    def test_manifest_uses_the_unit_namespace(self) -> None:
        manifest = json.loads(
            (TEST_ROOT / "suite-manifest.json").read_text(encoding="utf-8")
        )
        layer = next(item for item in manifest["layers"] if item["id"] == "4")
        self.assertEqual(layer["label"], "Unit Tests")
        for script in layer["scripts"]:
            path = script["path"]
            self.assertTrue(
                path.startswith("tests/speckit-pro/unit/")
                or path in {"tests/speckit-pro/test-run-all.py", "tests/speckit-pro/lib/test_lib.py"},
                path,
            )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(UnitLayoutTests)
    raise SystemExit(run_counted(suite, label="test-unit-layout"))
