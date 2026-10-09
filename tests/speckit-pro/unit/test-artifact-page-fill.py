#!/usr/bin/env python3
"""The runner fills draft artifact pages from the planning files (ADR 0019)."""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/speckit-pro/lib"))
sys.path.insert(0, str(ROOT / "speckit-pro"))
from runner_invocation import run_runner  # noqa: E402
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

    def fill(self, entry_id: str, expect: str = "ok", **inputs: object) -> dict:
        """Run fill-artifact-page; `mode` and `plugin` default to a dry run of the source plugin."""
        mode, plugin = inputs.pop("mode", "dry_run"), inputs.pop("plugin", "speckit-pro")
        planning = {field: f"{FEATURE}/{name}" for field, name in (
            ("plan_file", "plan.md"), ("spec_file", "spec.md"), ("tasks_file", "tasks.md"),
            ("research_file", "research.md"), ("design_concept_file", "design-concept.md"))}
        request = {"schema_version": "1.0", "helper_id": "fill-artifact-page", "operation": "fill-artifact-page",
                   "mode": mode, "inputs": {**planning, "entry_id": entry_id, **inputs}}
        _, result, _ = run_runner(request, cwd=self.root, extra_env={"PYTHONPATH": str(ROOT / str(plugin))})
        self.assertEqual(result["status"], expect, result)
        if expect != "ok":
            self.assertEqual(result["diagnostics"][0]["code"], "artifact_fill_invalid", result)
        return result

    def regions(self, entry_id: str, **inputs: object) -> dict[str, str]:
        self.fill(entry_id, mode="apply", **inputs)
        page = (self.root / FEATURE / "artifacts" / f"{entry_id}.html").read_text(encoding="utf-8")
        return dict(REGION.findall(page))

    def assert_regions(self, entry_id: str, expected: dict[str, tuple[str, ...]], **inputs: object) -> None:
        regions = self.regions(entry_id, **inputs)
        for name, fragments in expected.items():
            for fragment in fragments:
                with self.subTest(entry_id=entry_id, region=name, fragment=fragment):
                    self.assertIn(fragment, regions[name])


class StructuredRegionTests(FillFixture):
    def test_implementation_plan_counts_come_from_the_tasks_and_plan_files(self) -> None:
        self.assert_regions("implementation-plan", {
            "feature-header": ('<span id="feature-id">art-007-draft-pr-emission</span>',
                               '<h1 id="feature-name">Draft-PR Emission</h1>'),
            "document-title": ("<title>Implementation Plan — art-007-draft-pr-emission Draft-PR Emission</title>",),
            "plan-stats": ("<dt>Phases</dt><dd>6</dd>", "<dt>Files touched</dt><dd>16</dd>"),
            "phases": ('id="phases-phase-1-setup-worktree-preflight"',),
            "task-inventory": ('<p class="task-count">3 tasks</p>', '<span class="task-id">T001</span>'),
        })

    def test_spec_explainer_lists_criteria_and_non_goals_from_the_spec(self) -> None:
        self.assert_regions("spec-explainer", {
            "acceptance-criteria": ("<summary>SC-001</summary>",),
            "non-goals": ("Reading or acting on pull-request review feedback.",),
            "goals": ("Plan stage ends at an open draft pull request",),
        })

    def test_module_map_and_approaches_come_from_declared_files_and_research(self) -> None:
        self.assert_regions("module-map", {
            "key-files": ('<span class="path">speckit-pro/speckit_pro_runner/helpers/pr_emission.py</span>',),
            "modules": ('id="modules-speckit-pro-speckit-pro-runner-helpers"',),
        })
        self.assert_regions("code-approaches", {"approaches": (
            "D1 — Draft mode is a third value on the existing packet mode", "A separate draft-packet schema.")})

    def test_approaches_keep_the_plan_workflows_bulleted_research_fields(self) -> None:
        research = ROOT / "tests/speckit-pro/evals/fixtures/functional/native-orchestration/plan-research/research.md"
        shutil.copy(research, self.root / FEATURE / "research.md")
        for plugin in PLUGINS:
            with self.subTest(plugin=plugin):
                self.assert_regions("code-approaches", {"approaches": (
                    "Retain refresh tokens for 30 days.", "7 days; 90 days.",
                    "Exponential backoff with full jitter, capped at 60 seconds.", "Fixed delay; linear backoff."),
                    "recommendation": ("Retain refresh tokens for 30 days.",)}, plugin=plugin)


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
                    self.assertFalse([banner for banner in ('class="sample-notice"', 'class="notice"', 'class="note"')
                                      if banner in page])
                    self.assertTrue(data["narrative_slots"])
                    for slot in data["narrative_slots"]:
                        self.assertIn(slot["slot"], dict(REGION.findall(page)))
                        self.assertTrue(slot["fallback"])

    def test_planning_markup_lands_as_escaped_text(self) -> None:
        tasks = self.root / FEATURE / "tasks.md"
        tasks.write_text('## Phase 1: <img src=x onerror="alert(1)">\n\n- [ ] T001 Ship <b>it</b>\n', encoding="utf-8")
        regions = self.regions("implementation-plan")
        self.assertIn("&lt;img src=x onerror=&quot;alert(1)&quot;&gt;", regions["phases"])
        self.assertIn('<p class="what">1 task</p>', regions["phases"])
        self.assertEqual([], [name for name, body in regions.items() if _active_content(body.encode())])

    def test_narrative_lands_as_escaped_text_in_its_slot(self) -> None:
        regions = self.regions("spec-explainer", narrative={"tldr": "<script>alert(1)</script> Plain & short."})
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; Plain &amp; short.", regions["tldr"])
        self.assertEqual(_active_content(regions["tldr"].encode()), [])

    def test_unknown_or_malformed_narrative_is_refused(self) -> None:
        for narrative in ({"no-such-slot": "text"}, {"tldr": ""}, {"tldr": 3}, ["tldr"], {"tldr": "x" * 1201}):
            with self.subTest(narrative=narrative):
                self.fill("spec-explainer", "input_error", narrative=narrative)
        self.assertFalse((self.root / FEATURE / "artifacts").exists())

    def test_a_page_selection_did_not_return_is_refused(self) -> None:
        (self.root / FEATURE / "research.md").write_text("# Research\n", encoding="utf-8")
        (self.root / FEATURE / "design-concept.md").write_text("# Concept\n", encoding="utf-8")
        self.fill("code-approaches", "input_error")


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-artifact-page-fill"))
