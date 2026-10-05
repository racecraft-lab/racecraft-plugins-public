#!/usr/bin/env python3
"""Draft page selection through the runner helper seam (ADR 0019)."""

from __future__ import annotations

import copy
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


class SelectionFixture(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.gallery: Path | None = None
        self.swap_on_read = False
        self.timeout = 30
        (self.root / ".specify").mkdir()
        (self.root / "plan.md").write_text("## Declared File Operations\n\n- NEW src/new.py\n", encoding="utf-8")

    def select(self, *, status: str = "ok", plugin: str = "speckit-pro", **inputs: object) -> dict:
        request = {"schema_version": "1.0", "request_id": "artifact-selection-test",
                   "helper_id": "select-artifact-pages", "operation": "select-artifact-pages",
                   "mode": "read_only", "inputs": {"plan_file": "plan.md", **inputs}}
        done = subprocess.run([
            sys.executable, "-c", "import os, runpy, sys\nfrom pathlib import Path\n"
            "from speckit_pro_runner.helpers import artifact_selection\n"
            "artifact_selection.GALLERY = Path(sys.argv[1]) if sys.argv[1] != 'None' else artifact_selection.GALLERY\n"
            "swap_requested = sys.argv[2] == 'True'\nreal_open = os.open\n"
            "def swap_open(path, *args, **kwargs):\n"
            "    global swap_requested\n"
            "    if swap_requested and str(path) == 'artifacts' and kwargs.get('dir_fd') is not None:\n"
            "        Path('artifacts').rename('held-artifacts')\n"
            "        Path('artifacts').symlink_to('outside', target_is_directory=True)\n"
            "        swap_requested = False\n"
            "    return real_open(path, *args, **kwargs)\n"
            "os.open = swap_open\nsys.argv = sys.argv[:1]\n"
            "runpy.run_module('speckit_pro_runner', run_name='__main__')", str(self.gallery), str(self.swap_on_read),
        ],
                              input=json.dumps(request), text=True, capture_output=True, check=False,
                              cwd=self.root, env={**os.environ, "PYTHONPATH": str(ROOT / plugin)}, timeout=self.timeout)
        result = json.loads(done.stdout.splitlines()[-1])
        self.assertEqual(done.returncode, 0 if status == "ok" else 2, result)
        self.assertEqual(result["status"], status, result)
        if self.gallery is not None and status != "ok":
            self.assertIn("gallery manifest", result["diagnostics"][0]["message"])
        return result["data"]


class ManifestSecurityTests(SelectionFixture):
    def test_structurally_malformed_manifests_are_explicit_errors(self) -> None:
        gallery = self.root / "gallery"
        gallery.mkdir()
        self.gallery = gallery
        shipped = json.loads((ROOT / "speckit-pro/artifact-gallery/manifest.json").read_text(encoding="utf-8"))
        cases = [("missing contract", {"templates": []}), ("null", None), ("array", [])]
        for label, field, value in (("empty templates", "templates", []), ("invalid entries", "templates", [None]),
                                    ("invalid version", "schema_version", "2.0"), ("invalid signals", "signals", {})):
            manifest = copy.deepcopy(shipped)
            manifest[field] = value
            cases.append((label, manifest))
        for trigger in ({}, {"always": False}, {"always": 1}, {"any_of": []}, {"any_of": "brownfield_change"},
                        {"any_of": ["unknown"]}, {"always": True, "any_of": ["brownfield_change"]}):
            manifest = copy.deepcopy(shipped)
            manifest["templates"][0]["trigger"] = trigger
            cases.append((str(trigger), manifest))
        duplicate = copy.deepcopy(shipped)
        duplicate["templates"].append(duplicate["templates"][0])
        cases.append(("duplicate ids", duplicate))
        no_mandatory = copy.deepcopy(shipped)
        for entry in no_mandatory["templates"]:
            if entry["stage"] == "draft-pr":
                entry["trigger"] = {"any_of": ["brownfield_change"]}
        cases.append(("missing mandatory draft pages", no_mandatory))
        for label, manifest in cases:
            with self.subTest(case=label):
                (gallery / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                self.assertEqual(self.select(status="input_error"), {})

    def test_manifest_ids_cannot_escape_the_artifact_directory(self) -> None:
        gallery = self.root / "gallery"
        gallery.mkdir()
        self.gallery = gallery
        manifest = json.loads((ROOT / "speckit-pro/artifact-gallery/manifest.json").read_text(encoding="utf-8"))
        for identifier in ("../../escape", "/absolute-target", "sub/page", "..", "C:\\escape", "\\escape"):
            with self.subTest(identifier=identifier):
                manifest["templates"][0]["id"] = identifier
                (gallery / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                self.assertEqual(self.select(status="input_error"), {})


class WrittenOutputSecurityTests(SelectionFixture):
    def test_written_file_verification_fails_closed_at_the_descriptor_read(self) -> None:
        artifacts = self.root / "artifacts"
        outside = self.root / "outside"
        artifacts.mkdir()
        outside.mkdir()
        final = "artifacts/implementation-plan.html"
        (self.root / final).write_text("owned page", encoding="utf-8")
        (outside / "implementation-plan.html").write_text("outside page", encoding="utf-8")
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                self.swap_on_read = True
                self.assertEqual(self.select(status="input_error", plugin=plugin, candidate_paths=[final],
                                             verify_written_paths=True), {})
                self.swap_on_read = False
                self.assertTrue(artifacts.is_symlink(), "the race probe must actually swap the directory")
                artifacts.unlink()
                (self.root / "held-artifacts").rename(artifacts)
        (self.root / final).unlink()
        self.assertEqual(self.select(status="input_error", candidate_paths=[final], verify_written_paths=True), {})
        (self.root / final).mkdir()
        self.assertEqual(self.select(status="input_error", candidate_paths=[final], verify_written_paths=True), {})
        self.assertEqual(self.select(status="input_error", verify_written_paths=1), {})
        (self.root / final).rmdir()
        os.mkfifo(self.root / final)
        self.timeout = 10
        self.assertEqual(self.select(status="input_error", candidate_paths=[final],
                                     verify_written_paths=True), {})

    def test_post_write_verification_rejects_a_swapped_artifact_directory(self) -> None:
        artifacts = self.root / "artifacts"
        outside = self.root / "outside"
        artifacts.mkdir()
        outside.mkdir()
        final = "artifacts/implementation-plan.html"
        temporary = "artifacts/.artifact-author-implementation-plan.race.tmp"
        (self.root / final).write_text("owned page", encoding="utf-8")
        verified = self.select(candidate_paths=[final], verify_written_paths=True)
        self.assertEqual(verified["verified_paths"], [final])
        self.assertEqual(self.select(candidate_paths=[temporary, final])["checked_paths"], [temporary, final])
        artifacts.rename(self.root / "held-artifacts")
        artifacts.symlink_to(outside, target_is_directory=True)
        # Exercise the documented native-tool check/use window, including exclusive create.
        with (self.root / temporary).open("x", encoding="utf-8") as stream:
            stream.write("redirected page")
        os.replace(self.root / temporary, self.root / final)
        self.assertEqual(self.select(status="input_error", candidate_paths=[final], verify_written_paths=True), {})
        self.assertEqual((outside / "implementation-plan.html").read_text(encoding="utf-8"), "redirected page")
        self.assertEqual((self.root / "held-artifacts/implementation-plan.html").read_text(encoding="utf-8"), "owned page")


class OutputSecurityTests(SelectionFixture):
    def test_temporary_and_final_outputs_require_a_fresh_confinement_check(self) -> None:
        artifacts = self.root / "artifacts"
        artifacts.mkdir()
        paths = ["artifacts/.artifact-author-implementation-plan.probe.tmp", "artifacts/implementation-plan.html"]
        self.assertEqual(self.select(candidate_paths=paths)["checked_paths"], paths)
        for raw in ("../../escape", "/absolute-target", str(artifacts / "absolute.html"),
                    "elsewhere.html", "artifacts/../escape.html", "artifacts/sub/page.html", "C:\\escape"):
            with self.subTest(raw=raw):
                self.assertEqual(self.select(status="input_error", candidate_paths=[raw]), {})
        temporary = self.root / paths[0]
        temporary.symlink_to(self.root / "escape.html")
        self.assertEqual(self.select(status="input_error", candidate_paths=paths), {})
        temporary.unlink()
        for invalid in ([], "artifacts/page.html", [1]):
            with self.subTest(invalid=invalid):
                self.assertEqual(self.select(status="input_error", candidate_paths=invalid), {})

    def test_symlinked_artifact_components_reject_selection(self) -> None:
        artifacts = self.root / "artifacts"
        outside = self.root / "outside"
        outside.mkdir()
        for target in (outside, outside / "missing"):
            with self.subTest(target=target.name):
                artifacts.symlink_to(target)
                self.assertEqual(self.select(status="input_error"), {})
                artifacts.unlink()
        artifacts.mkdir()
        final = artifacts / "implementation-plan.html"
        for target in (outside / "escape.html", artifacts / "another.html"):
            with self.subTest(target=target.name):
                final.symlink_to(target)
                self.assertEqual(self.select(status="input_error"), {})
                final.unlink()


class ArtifactSelectionTests(SelectionFixture):
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

    def test_each_signal_follows_its_planning_record(self) -> None:
        cases = (
            ("plan_file", "plan.md", "- MODIFIED outside.py\n## Declared File Operations\n"
             "- NEW src/new.py\n## Notes\n- MODIFIED also-outside.py\n", [],
             ["implementation-plan", "spec-explainer"]),
            ("plan_file", "plan.md", "## Declared File Operations\n- NEW src/new.py\n"
             "```markdown\n- MODIFIED src/example.py\n```\n", [], ["implementation-plan", "spec-explainer"]),
            ("plan_file", "plan.md", "## Declared File Operations\n- NEW src/new.py\n<!--\n  - MODIFIED <path>\n-->\n"
             "<!-- - MODIFIED src/inline.py -->\n", [], ["implementation-plan", "spec-explainer"]),
            ("research_file", "research.md", "**Alternatives considered**: a separate schema.\n",
             ["competing_approaches"], ["implementation-plan", "spec-explainer", "code-approaches"]),
            ("design_concept_file", "design.md", "**Alternatives offered:**\n- Keep the old schema.\n",
             ["competing_approaches"], ["implementation-plan", "spec-explainer", "code-approaches"]),
        )
        for field, filename, text, signals, pages in cases:
            with self.subTest(field=field, text=text):
                (self.root / filename).write_text(text, encoding="utf-8")
                result = self.select(**{field: filename})
                self.assertEqual((result["signals"], result["selected_pages"]), (signals, pages))

    def test_links_and_subheadings_record_real_alternatives(self) -> None:
        for text in ("**Alternatives considered**:\n- [Separate schema](https://example.com/schema)\n",
                     "## Alternatives considered\n### Separate schema\nKeep a dedicated schema.\n",
                     "- Decision: reuse\n- Alternatives considered: a separate schema.\n",
                     "- **Alternatives considered**: a separate schema.\n", "Alternatives considered: a separate schema.\n"):
            with self.subTest(text=text):
                (self.root / "research.md").write_text(text, encoding="utf-8")
                self.assertEqual(self.select(research_file="research.md")["signals"], ["competing_approaches"])

    def test_empty_negative_placeholder_and_incidental_alternatives_do_not_select(self) -> None:
        for text in ("", "We may research alternatives later.\n", "## Alternatives were not considered\n",
                     "## Alternatives considered\n\n## Decision\nKeep it.\n",
                     "**Alternatives considered**: None.\n", "**Alternatives offered:**\n- N/A\n",
                     "**Alternatives considered**: None.\nCompatibility requires the existing approach.\n",
                     "## Alternatives considered\nNone.\nCompatibility requires the existing approach.\n",
                     "## Alternatives\n[TODO]\n", "- Alternatives considered: None\n",
                     "Alternatives were weighed in review.\n", "```markdown\n**Alternatives considered**: Example.\n```\n"):
            with self.subTest(text=text):
                (self.root / "research.md").write_text(text, encoding="utf-8")
                (self.root / "design.md").write_text(text, encoding="utf-8")
                self.assertEqual(self.select(research_file="research.md", design_concept_file="design.md")["signals"], [])

    def test_both_rules_select_all_shipped_draft_pages_but_no_planned_or_final_pages(self) -> None:
        (self.root / "plan.md").write_text("## Declared File Operations\n- MODIFIED src/old.py\n", encoding="utf-8")
        (self.root / "research.md").write_text("## Alternatives considered\n- Add a new adapter.\n", encoding="utf-8")
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                self.assertEqual(self.select(plugin=plugin, research_file="research.md")["selected_pages"],
                                 ["implementation-plan", "spec-explainer", "code-approaches", "module-map"])

    def test_unreadable_invalid_and_escaping_inputs_are_explicit_selection_errors(self) -> None:
        for inputs in ({"plan_file": "missing.md"}, {"research_file": "missing.md"},
                       {"design_concept_file": "../outside.md"}, {"plan_file": 1}, {"unknown": True}):
            with self.subTest(inputs=inputs):
                self.assertEqual(self.select(status="input_error", **inputs), {})
        (self.root / "outside-link.md").symlink_to(ROOT / "README.md")
        self.assertEqual(self.select(status="input_error", research_file="outside-link.md"), {})


class ArtifactHostSelectionTests(SelectionFixture):
    def test_packaged_hosts_enforce_manifest_and_output_confinement(self) -> None:
        gallery = self.root / "gallery"
        gallery.mkdir()
        shipped = json.loads((ROOT / "speckit-pro/artifact-gallery/manifest.json").read_text(encoding="utf-8"))
        for host in ("claude", "codex"):
            plugin = f"dist/{host}/speckit-pro"
            with self.subTest(host=host):
                self.assertEqual(self.select(plugin=plugin)["output_paths"], {
                    "implementation-plan": "artifacts/implementation-plan.html",
                    "spec-explainer": "artifacts/spec-explainer.html",
                })
                self.gallery = gallery
                for identifier in ("../../escape", "/absolute-target"):
                    manifest = copy.deepcopy(shipped)
                    manifest["templates"][0]["id"] = identifier
                    (gallery / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                    self.assertEqual(self.select(status="input_error", plugin=plugin), {})
                malformed = copy.deepcopy(shipped)
                malformed["templates"][0]["trigger"] = {}
                (gallery / "manifest.json").write_text(json.dumps(malformed), encoding="utf-8")
                self.assertEqual(self.select(status="input_error", plugin=plugin), {})
                self.gallery = None
                (self.root / "artifacts").symlink_to(self.root / "redirected")
                self.assertEqual(self.select(status="input_error", plugin=plugin), {})
                (self.root / "artifacts").unlink()

    def test_both_host_dispatches_and_author_roles_consume_runner_selection(self) -> None:
        for host, agent in (("claude", "agents/artifact-author.md"), ("codex", "codex-agents/artifact-author.toml")):
            with self.subTest(host=host):
                plugin = ROOT / f"dist/{host}/speckit-pro"
                for relative in ("skills/speckit-autopilot/SKILL.md", agent):
                    text = (plugin / relative).read_text(encoding="utf-8")
                    self.assertIn("select-artifact-pages", text)
                    self.assertIn("selected_pages", text)
                self.assertNotIn("Apply each surviving entry's `trigger`", (plugin / agent).read_text(encoding="utf-8"))
                author = (plugin / agent).read_text(encoding="utf-8")
                self.assertIn("output_paths[entry-id]", author)
                self.assertIn("publish-artifact-page", author)
                self.assertIn("data.verified_html", author)
                self.assertIn("data.file_identity", author)
                self.assertNotIn("verify_written_paths", author)
                self.assertNotIn("Native tool writes retain a check/use race", author)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-artifact-selection"))
