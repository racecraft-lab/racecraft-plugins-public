#!/usr/bin/env python3
"""Focused structural validator failure-path tests."""

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
agent_instructions = load_module("validate_agent_instructions", "validate-agent-instructions.py")


def write_valid_agent_instruction_tree(root: Path) -> None:
    for directory in agent_instructions.EXPECTED_AGENT_DIRS:
        target = root / directory
        target.mkdir(parents=True, exist_ok=True)
        (target / "AGENTS.md").write_text("# Rules\n\nKeep this short.\n", encoding="utf-8")
        (target / "CLAUDE.md").write_text(agent_instructions.CLAUDE_WRAPPER, encoding="utf-8")
        (target / "GEMINI.md").write_text(agent_instructions.GEMINI_WRAPPER, encoding="utf-8")
    copilot = root / ".github" / "copilot-instructions.md"
    copilot.parent.mkdir(parents=True, exist_ok=True)
    copilot.write_text(agent_instructions.COPILOT_POINTER, encoding="utf-8")


class ValidatorFailurePathTests(unittest.TestCase):
    def test_release_workflow_rejects_tab_only_indentation(self) -> None:
        text = "name: Invalid\njobs:\n\tbuild:\n\t  runs-on: ubuntu-latest\n"
        self.assertFalse(release_workflow._yaml_syntax_sane(text))

    def test_plugin_payload_reports_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "broken.json"
            path.write_text('{"plugins":[}\n', encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "malformed JSON.*broken.json"):
                plugin_payload.load_json_file(path)

    def test_plugin_payload_reports_missing_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing.json"
            with self.assertRaisesRegex(AssertionError, "unable to read.*missing.json"):
                plugin_payload.load_json_file(path)

    def test_agent_instruction_validator_accepts_wrapper_only_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_valid_agent_instruction_tree(root)
            self.assertEqual([], agent_instructions.collect_errors(root))

    def test_agent_instruction_validator_rejects_claude_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_valid_agent_instruction_tree(root)
            (root / "CLAUDE.md").write_text("@./AGENTS.md\n\nExtra local rule.\n", encoding="utf-8")
            errors = agent_instructions.collect_errors(root)
            self.assertIn("CLAUDE.md must contain only '@./AGENTS.md'", "\n".join(errors))

    def test_agent_instruction_validator_rejects_unexpected_agent_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_valid_agent_instruction_tree(root)
            extra = root / "docs" / "AGENTS.md"
            extra.parent.mkdir(parents=True)
            extra.write_text("# Extra\n", encoding="utf-8")
            errors = agent_instructions.collect_errors(root)
            self.assertIn("docs/AGENTS.md", "\n".join(errors))


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ValidatorFailurePathTests)
    return run_counted(suite, label="test-validator-failure-paths")


if __name__ == "__main__":
    raise SystemExit(main())
