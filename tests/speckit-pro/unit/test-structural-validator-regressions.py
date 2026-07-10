#!/usr/bin/env python3
"""Focused regressions for XPLAT-010 Layer 1 validator failure paths."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
LAYER1_DIR = REPO_ROOT / "tests" / "speckit-pro" / "layer1-structural"
for path in (LIB_DIR, LAYER1_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
from test_result import run_counted  # noqa: E402


def load_module(name: str, filename: str):
    path = LAYER1_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


release_workflow = load_module("validate_release_workflow", "validate-release-workflow.py")
plugin_payload = load_module("validate_plugin_payload", "validate-plugin-payload.py")
pr_checks_sentinel = load_module("validate_pr_checks_sentinel", "validate-pr-checks-sentinel.py")
skill_pointers = load_module("validate_skill_capability_pointers", "validate-skill-capability-pointers.py")


class Layer1ValidatorRegressionTests(unittest.TestCase):
    def test_release_workflow_rejects_tab_only_indentation(self) -> None:
        text = "name: Invalid\njobs:\n\tbuild:\n\t  runs-on: ubuntu-latest\n"
        self.assertFalse(release_workflow._yaml_syntax_sane(text))

    def test_plugin_payload_reports_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "broken.json"
            path.write_text('{"plugins":[}\n', encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "malformed JSON.*broken.json"):
                plugin_payload.load_json_file(path)

    def test_plugin_payload_reports_unreadable_json(self) -> None:
        missing = Path("/tmp/xplat010-definitely-missing-marketplace.json")
        with self.assertRaisesRegex(AssertionError, "unable to read.*xplat010-definitely-missing"):
            plugin_payload.load_json_file(missing)

    def test_pr_checks_docstring_distinguishes_external_yaml_probe(self) -> None:
        doc = pr_checks_sentinel.__doc__ or ""
        self.assertIn("module imports only the Python", doc)
        self.assertIn("optional PyYAML/Ruby subprocess delegation", doc)

    def test_skill_pointer_paths_are_repo_relative(self) -> None:
        self.assertEqual(
            skill_pointers._display_path(skill_pointers.REPO_ROOT / "dist" / "claude"),
            "dist/claude",
        )


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer1ValidatorRegressionTests)
    return run_counted(suite, label="test-structural-validator-regressions")


if __name__ == "__main__":
    raise SystemExit(main())
