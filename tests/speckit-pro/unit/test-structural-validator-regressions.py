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
agent_instructions = load_module("validate_agent_instructions", "validate-agent-instructions.py")


def write_valid_agent_instruction_tree(root: Path) -> None:
    agent_dirs = (
        Path("."),
        Path("speckit-pro"),
        Path("tests/speckit-pro"),
        Path("docs-site"),
    )
    for directory in agent_dirs:
        target = root / directory
        target.mkdir(parents=True, exist_ok=True)
        (target / "AGENTS.md").write_text("# Rules\n\nKeep this short.\n", encoding="utf-8")
        (target / "CLAUDE.md").write_text(agent_instructions.CLAUDE_WRAPPER, encoding="utf-8")
        (target / "GEMINI.md").write_text(agent_instructions.GEMINI_WRAPPER, encoding="utf-8")
    copilot = root / ".github" / "copilot-instructions.md"
    copilot.parent.mkdir(parents=True, exist_ok=True)
    copilot.write_text(agent_instructions.COPILOT_POINTER, encoding="utf-8")


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

    def test_pr_checks_docstring_describes_stdlib_yaml_sanity(self) -> None:
        doc = pr_checks_sentinel.__doc__ or ""
        self.assertIn("does not invoke those probes", doc)
        self.assertIn("stdlib-only", doc)

    def test_skill_pointer_paths_are_repo_relative(self) -> None:
        self.assertEqual(
            skill_pointers._display_path(skill_pointers.REPO_ROOT / "dist" / "claude"),
            "dist/claude",
        )

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

    def test_archive_cleanup_title_guidance_uses_lowercase_spec_scope(self) -> None:
        paths = (
            REPO_ROOT / "speckit-pro/skills/speckit-archive-cleanup/SKILL.md",
            REPO_ROOT / "speckit-pro/codex-skills/speckit-archive-cleanup/SKILL.md",
            REPO_ROOT / "dist/claude/speckit-pro/skills/speckit-archive-cleanup/SKILL.md",
            REPO_ROOT / "dist/codex/speckit-pro/skills/speckit-archive-cleanup/SKILL.md",
            REPO_ROOT
            / "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/skills/speckit-archive-cleanup/SKILL.md",
            REPO_ROOT
            / "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-archive-cleanup/SKILL.md",
        )
        for path in paths:
            with self.subTest(msg=f"{path.relative_to(REPO_ROOT)} uses lower-case archive PR title guidance"):
                text = path.read_text(encoding="utf-8")
                self.assertIn("docs(car-001): archive post-merge state", text)
                self.assertNotIn("docs(SPEC-ID): archive post-merge state", text)
                self.assertNotIn("docs(CAR-001): archive post-merge state` for archive-only", text)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer1ValidatorRegressionTests)
    return run_counted(suite, label="test-structural-validator-regressions")


if __name__ == "__main__":
    raise SystemExit(main())
