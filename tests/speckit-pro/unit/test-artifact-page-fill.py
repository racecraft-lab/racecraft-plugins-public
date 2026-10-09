#!/usr/bin/env python3
"""The runner fills draft artifact pages from the planning files (ADR 0019)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/speckit-pro/lib"))
sys.path.insert(0, str(ROOT / "speckit-pro"))
from test_result import run_counted  # noqa: E402
from speckit_pro_runner.artifact_review import _active_content  # noqa: E402

PLANNING = ROOT / "tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission" / "source"
FEATURE = "specs/art-007-draft-pr-emission"
PLUGINS = ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro")
REGION = re.compile(r"<!-- FILL:([a-z0-9-]+):START -->(.*?)<!-- FILL:\1:END -->", re.DOTALL)
PAGES = ("implementation-plan", "spec-explainer", "code-approaches", "module-map")


class FillFixture(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / ".specify").mkdir()
        (self.root / FEATURE).mkdir(parents=True)
        for name in ("spec.md", "plan.md", "tasks.md", "research.md", "design-concept.md"):
            shutil.copy(PLANNING / name, self.root / FEATURE / name)

    def fill(self, entry_id: str, *, status: str = "ok", mode: str = "dry_run", plugin: str = "speckit-pro",
             **inputs: object) -> dict:
        planning = {"plan_file": f"{FEATURE}/plan.md", "spec_file": f"{FEATURE}/spec.md",
                    "tasks_file": f"{FEATURE}/tasks.md", "research_file": f"{FEATURE}/research.md",
                    "design_concept_file": f"{FEATURE}/design-concept.md"}
        request = {"schema_version": "1.0", "request_id": "artifact-fill-test", "helper_id": "fill-artifact-page",
                   "operation": "fill-artifact-page", "mode": mode,
                   "inputs": {**planning, "entry_id": entry_id, **inputs}}
        done = subprocess.run([sys.executable, "-m", "speckit_pro_runner"], input=json.dumps(request), text=True,
                              capture_output=True, check=False, cwd=self.root,
                              env={**os.environ, "PYTHONPATH": str(ROOT / plugin)}, timeout=30)
        self.assertTrue(done.stdout, done.stderr)
        result = json.loads(done.stdout.splitlines()[-1])
        self.assertEqual(result["status"], status, result)
        if status != "ok":
            self.assertEqual(result["diagnostics"][0]["code"], "artifact_fill_invalid", result)
        return result

    def regions(self, entry_id: str, **inputs: object) -> dict[str, str]:
        self.fill(entry_id, mode="apply", **inputs)
        page = (self.root / FEATURE / "artifacts" / f"{entry_id}.html").read_text(encoding="utf-8")
        return dict(REGION.findall(page))


class StructuredRegionTests(FillFixture):
    def test_implementation_plan_counts_come_from_the_tasks_and_plan_files(self) -> None:
        regions = self.regions("implementation-plan")
        self.assertIn('<span id="feature-id">art-007-draft-pr-emission</span>', regions["feature-header"])
        self.assertIn('<h1 id="feature-name">Draft-PR Emission</h1>', regions["feature-header"])
        self.assertIn("<title>Implementation Plan — art-007-draft-pr-emission Draft-PR Emission</title>",
                      regions["document-title"])
        self.assertIn("<dt>Phases</dt><dd>6</dd>", regions["plan-stats"])
        self.assertIn("<dt>Files touched</dt><dd>16</dd>", regions["plan-stats"])
        self.assertIn('id="phases-phase-1-setup-worktree-preflight"', regions["phases"])
        self.assertIn('<p class="task-count">3 tasks</p>', regions["task-inventory"])
        self.assertIn('<span class="task-id">T001</span>', regions["task-inventory"])

    def test_spec_explainer_lists_criteria_and_non_goals_from_the_spec(self) -> None:
        regions = self.regions("spec-explainer")
        self.assertIn("<summary>SC-001</summary>", regions["acceptance-criteria"])
        self.assertIn("Reading or acting on pull-request review feedback.", regions["non-goals"])
        self.assertIn("Plan stage ends at an open draft pull request", regions["goals"])

    def test_module_map_and_approaches_come_from_declared_files_and_research(self) -> None:
        modules = self.regions("module-map")
        self.assertIn('<span class="path">speckit-pro/speckit_pro_runner/helpers/pr_emission.py</span>',
                      modules["key-files"])
        self.assertIn('id="modules-speckit-pro-speckit-pro-runner-helpers"', modules["modules"])
        approaches = self.regions("code-approaches")
        self.assertIn("D1 — Draft mode is a third value on the existing packet mode", approaches["approaches"])
        self.assertIn("A separate draft-packet schema.", approaches["approaches"])


class FallbackAndNarrativeTests(FillFixture):
    def test_a_page_with_fallbacks_validates_publishes_and_lists_its_prose_slots(self) -> None:
        for plugin in PLUGINS:
            for entry_id in PAGES:
                with self.subTest(plugin=plugin, entry_id=entry_id):
                    data = self.fill(entry_id, mode="apply", plugin=plugin)["data"]
                    self.assertTrue(data["writes_state"])
                    self.assertEqual(data["output_path"], f"{FEATURE}/artifacts/{entry_id}.html")
                    page = (self.root / data["output_path"]).read_text(encoding="utf-8")
                    template = (ROOT / plugin / f"artifact-gallery/templates/{entry_id}.html").read_text(
                        encoding="utf-8")
                    self.assertEqual(REGION.sub("", page), REGION.sub("", template))
                    for name, body in REGION.findall(page):
                        self.assertEqual(_active_content(body.encode()), [], name)
                    self.assertTrue(data["narrative_slots"])
                    for slot in data["narrative_slots"]:
                        self.assertIn(slot["slot"], dict(REGION.findall(page)))
                        self.assertTrue(slot["fallback"])

    def test_narrative_lands_as_escaped_text_in_its_slot(self) -> None:
        regions = self.regions("spec-explainer", narrative={"tldr": "<script>alert(1)</script> Plain & short."})
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; Plain &amp; short.", regions["tldr"])
        self.assertEqual(_active_content(regions["tldr"].encode()), [])

    def test_unknown_or_malformed_narrative_is_refused(self) -> None:
        for narrative in ({"no-such-slot": "text"}, {"tldr": ""}, {"tldr": 3}, ["tldr"], {"tldr": "x" * 1201}):
            with self.subTest(narrative=narrative):
                self.fill("spec-explainer", status="input_error", narrative=narrative)
        self.assertFalse((self.root / FEATURE / "artifacts").exists())

    def test_a_page_selection_did_not_return_is_refused(self) -> None:
        (self.root / FEATURE / "research.md").write_text("# Research\n", encoding="utf-8")
        (self.root / FEATURE / "design-concept.md").write_text("# Concept\n", encoding="utf-8")
        self.fill("code-approaches", status="input_error")


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-artifact-page-fill"))
