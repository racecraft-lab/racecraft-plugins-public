#!/usr/bin/env python3
"""Draft page selection through the runner helper seam (ADR 0019)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/speckit-pro/lib"))
from test_result import run_counted  # noqa: E402


class ArtifactSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = ROOT / ".git/scratch"
        scratch.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / ".specify").mkdir()
        (self.root / "plan.md").write_text("## Declared File Operations\n\n- NEW src/new.py\n", encoding="utf-8")

    def select(self, *, status: str = "ok", plugin: str = "speckit-pro", **inputs: object) -> dict:
        request = {"schema_version": "1.0", "request_id": "artifact-selection-test",
                   "helper_id": "select-artifact-pages", "operation": "select-artifact-pages",
                   "mode": "read_only", "inputs": {"plan_file": "plan.md", **inputs}}
        done = subprocess.run([sys.executable, "-m", "speckit_pro_runner"],
                              input=json.dumps(request), text=True, capture_output=True, check=False,
                              cwd=self.root, env={**os.environ, "PYTHONPATH": str(ROOT / plugin)}, timeout=30)
        result = json.loads(done.stdout.splitlines()[-1])
        self.assertEqual(done.returncode, 0 if status == "ok" else 2, result)
        self.assertEqual(result["status"], status, result)
        return result["data"]

    def test_new_files_select_only_the_always_selected_draft_pages(self) -> None:
        result = self.select()
        self.assertEqual(result["selected_pages"], ["implementation-plan", "spec-explainer"])
        self.assertEqual(result["signals"], [])
        self.assertFalse(result["writes_state"])

    def test_modified_operation_selects_module_map_in_manifest_order(self) -> None:
        (self.root / "plan.md").write_text("## Declared File Operations\n\n- NEW src/new.py\n"
                                           "- MODIFIED src/existing.py\n", encoding="utf-8")
        result = self.select()
        self.assertEqual(result["selected_pages"], ["implementation-plan", "spec-explainer", "module-map"])
        self.assertEqual(result["signals"], ["brownfield_change"])

    def test_modified_mentions_outside_declared_operations_do_not_select_module_map(self) -> None:
        (self.root / "plan.md").write_text("- MODIFIED outside.py\n## Declared File Operations\n"
                                           "- NEW src/new.py\n## Notes\n- MODIFIED also-outside.py\n", encoding="utf-8")
        self.assertEqual(self.select()["selected_pages"], ["implementation-plan", "spec-explainer"])

    def test_research_alternatives_select_code_approaches(self) -> None:
        (self.root / "research.md").write_text("**Alternatives considered**: a separate schema.\n", encoding="utf-8")
        self.assertEqual(self.select(research_file="research.md")["selected_pages"],
                         ["implementation-plan", "spec-explainer", "code-approaches"])

    def test_design_alternatives_select_code_approaches(self) -> None:
        (self.root / "design.md").write_text("**Alternatives offered:**\n- Keep the old schema.\n", encoding="utf-8")
        self.assertEqual(self.select(design_concept_file="design.md")["signals"], ["competing_approaches"])

    def test_empty_negative_placeholder_and_incidental_alternatives_do_not_select(self) -> None:
        for text in ("", "We may research alternatives later.\n", "## Alternatives considered\n\n## Decision\nKeep it.\n",
                     "**Alternatives considered**: None.\n", "**Alternatives offered:**\n- N/A\n",
                     "## Alternatives\n[TODO]\n", "```markdown\n**Alternatives considered**: Example.\n```\n"):
            with self.subTest(text=text):
                (self.root / "research.md").write_text(text, encoding="utf-8")
                (self.root / "design.md").write_text(text, encoding="utf-8")
                self.assertEqual(self.select(research_file="research.md", design_concept_file="design.md")["signals"], [])

    def test_both_rules_select_all_shipped_draft_pages_but_no_planned_or_final_pages(self) -> None:
        (self.root / "plan.md").write_text("## Declared File Operations\n- MODIFIED src/old.py\n", encoding="utf-8")
        (self.root / "research.md").write_text("## Alternatives considered\n- Add a new adapter.\n", encoding="utf-8")
        self.assertEqual(self.select(research_file="research.md")["selected_pages"],
                         ["implementation-plan", "spec-explainer", "code-approaches", "module-map"])

    def test_unreadable_invalid_and_escaping_inputs_are_explicit_selection_errors(self) -> None:
        for inputs in ({"plan_file": "missing.md"}, {"research_file": "missing.md"},
                       {"design_concept_file": "../outside.md"}, {"plan_file": 1}, {"unknown": True}):
            with self.subTest(inputs=inputs):
                self.assertEqual(self.select(status="input_error", **inputs), {})
        (self.root / "outside-link.md").symlink_to(ROOT / "README.md")
        self.assertEqual(self.select(status="input_error", research_file="outside-link.md"), {})

    def test_shipped_claude_and_codex_helpers_choose_the_same_pages(self) -> None:
        (self.root / "plan.md").write_text("## Declared File Operations\n- MODIFIED src/old.py\n", encoding="utf-8")
        (self.root / "design.md").write_text("**Alternatives offered:**\n- A separate adapter.\n", encoding="utf-8")
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.assertEqual(self.select(plugin=f"dist/{host}/speckit-pro", design_concept_file="design.md")["selected_pages"],
                                 ["implementation-plan", "spec-explainer", "code-approaches", "module-map"])

    def test_both_host_dispatches_and_author_roles_consume_runner_selection(self) -> None:
        for host, agent in (("claude", "agents/artifact-author.md"), ("codex", "codex-agents/artifact-author.toml")):
            with self.subTest(host=host):
                plugin = ROOT / f"dist/{host}/speckit-pro"
                for relative in ("skills/speckit-autopilot/SKILL.md", agent):
                    text = (plugin / relative).read_text(encoding="utf-8")
                    self.assertIn("select-artifact-pages", text)
                    self.assertIn("selected_pages", text)
                self.assertNotIn("Apply each surviving entry's `trigger`", (plugin / agent).read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-artifact-selection"))
