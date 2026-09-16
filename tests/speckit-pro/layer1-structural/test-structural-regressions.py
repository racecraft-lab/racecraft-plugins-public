#!/usr/bin/env python3
"""Focused failure-path tests for consolidated structural validators."""

from __future__ import annotations

import importlib.util
import shutil
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


ci_release = load_module("validate_ci_release_contracts", "validate-ci-release-contracts.py")
payloads = load_module("validate_payload_contracts", "validate-payload-contracts.py")
agents = load_module("validate_agent_contracts", "validate-agent-contracts.py")


def run_codex_agent_validator(codex_agents_dir: Path) -> unittest.TestResult:
    original = agents.CODEX_AGENTS_DIR
    agents.CODEX_AGENTS_DIR = codex_agents_dir
    try:
        result = unittest.TestResult()
        agents.ValidateCodexAgents("test_codex_agents").run(result)
        return result
    finally:
        agents.CODEX_AGENTS_DIR = original


def write_valid_agent_instruction_tree(root: Path) -> None:
    for directory in agents.AGENT_INSTRUCTION_DIRS:
        target = root / directory
        target.mkdir(parents=True, exist_ok=True)
        (target / "AGENTS.md").write_text("# Rules\n\nKeep this short.\n", encoding="utf-8")
        (target / "CLAUDE.md").write_text(agents.CLAUDE_WRAPPER, encoding="utf-8")
        (target / "GEMINI.md").write_text(agents.GEMINI_WRAPPER, encoding="utf-8")
    copilot = root / ".github" / "copilot-instructions.md"
    copilot.parent.mkdir(parents=True, exist_ok=True)
    copilot.write_text(agents.COPILOT_POINTER, encoding="utf-8")


class StructuralRegressionTests(unittest.TestCase):
    def test_release_workflow_rejects_tab_only_indentation(self) -> None:
        text = "name: Invalid\njobs:\n\tbuild:\n\t  runs-on: ubuntu-latest\n"
        self.assertFalse(ci_release.yaml_syntax_sane(text))

    def test_plugin_payload_reports_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "broken.json"
            path.write_text('{"plugins":[}\n', encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "malformed JSON.*broken.json"):
                payloads.load_json_file(path)

    def test_plugin_payload_reports_missing_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing.json"
            with self.assertRaisesRegex(AssertionError, "unable to read.*missing.json"):
                payloads.load_json_file(path)

    def test_agent_instruction_validator_accepts_wrapper_only_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_valid_agent_instruction_tree(root)
            self.assertEqual([], agents.collect_agent_instruction_errors(root))

    def test_agent_instruction_validator_rejects_claude_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_valid_agent_instruction_tree(root)
            (root / "CLAUDE.md").write_text("@./AGENTS.md\n\nExtra local rule.\n", encoding="utf-8")
            errors = agents.collect_agent_instruction_errors(root)
            self.assertIn("CLAUDE.md must contain only '@./AGENTS.md'", "\n".join(errors))

    def test_agent_instruction_validator_rejects_unexpected_agent_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_valid_agent_instruction_tree(root)
            extra = root / "docs" / "AGENTS.md"
            extra.parent.mkdir(parents=True)
            extra.write_text("# Extra\n", encoding="utf-8")
            errors = agents.collect_agent_instruction_errors(root)
            self.assertIn("docs/AGENTS.md", "\n".join(errors))

    def test_agent_instruction_validator_ignores_only_root_native_eval_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_valid_agent_instruction_tree(root)
            retained = root / ".native-eval-output" / "attempts" / "staging" / "plugin"
            retained.mkdir(parents=True)
            for name in agents.INSTRUCTION_NAMES:
                (retained / name).write_text("retained native evidence\n", encoding="utf-8")
            self.assertEqual([], agents.collect_agent_instruction_errors(root))

            authored = root / "authored" / ".native-eval-output" / "AGENTS.md"
            authored.parent.mkdir(parents=True)
            authored.write_text("# Unexpected authored scope\n", encoding="utf-8")
            errors = agents.collect_agent_instruction_errors(root)
            self.assertIn("authored/.native-eval-output/AGENTS.md", "\n".join(errors))


class CodexAgentRegressionTests(unittest.TestCase):
    def test_codex_agent_validator_rejects_newly_covered_role_corruption(self) -> None:
        mutations = (
            ("artifact-author", 'sandbox_mode = "workspace-write"', 'sandbox_mode = "read-only"'),
            ("uat-runbook-author", 'name = "uat-runbook-author"', 'name = "wrong-role"'),
        )
        for role, original, replacement in mutations:
            with self.subTest(role=role), tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary) / "codex-agents"
                shutil.copytree(agents.CODEX_AGENTS_DIR, target)
                path = target / f"{role}.toml"
                path.write_text(path.read_text(encoding="utf-8").replace(original, replacement), encoding="utf-8")

                result = run_codex_agent_validator(target)
                self.assertFalse(result.wasSuccessful(), f"{role} corruption passed validation")
                self.assertEqual([], result.errors, f"{role} corruption raised instead of producing an assertion failure")
                failures = "\n".join(f"{test}\n{traceback}" for test, traceback in result.failures)
                self.assertIn(role, failures)

    def test_codex_agent_validator_rejects_missing_directory_and_unknown_role(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing-codex-agents"
            result = run_codex_agent_validator(missing)
            self.assertFalse(result.wasSuccessful())
            self.assertEqual([], result.errors, "missing directory must fail closed without an unhandled error")

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "codex-agents"
            shutil.copytree(agents.CODEX_AGENTS_DIR, target)
            (target / "unknown-role.toml").write_text('name = "unknown-role"\n', encoding="utf-8")
            result = run_codex_agent_validator(target)
            self.assertFalse(result.wasSuccessful(), "unknown Codex role passed exact-roster validation")
            self.assertEqual([], result.errors)


def main() -> int:
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(StructuralRegressionTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(CodexAgentRegressionTests))
    return run_counted(suite, label="test-structural-regressions")


if __name__ == "__main__":
    raise SystemExit(main())
