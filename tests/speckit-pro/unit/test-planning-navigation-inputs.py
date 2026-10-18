#!/usr/bin/env python3
"""Generated navigation inputs at the planning approval seam."""
import json
import unittest
from importlib import import_module
from pathlib import Path

fixtures = import_module("test-planning-approval")
from test_result import run_counted
from speckit_pro_runner.helpers.read_only import SpecIndexRenderError, render_spec_index


class NavigationInjectionTest(fixtures.NavigationFixture):
    def injectedPrFields(self, payload):
        manifest = self.feature / ".process/prs.json"
        original = json.loads(manifest.read_text())
        for version, field in ((2, "slice_id"), (2, "status"), (2, "branch"),
                               (2, "base_branch"), (2, "head_sha"), (2, "merged_sha"),
                               (2, "declared_files"), (2, "verification_evidence"),
                               (1, "slice"), (1, "merged_sha")):
            data = json.loads(json.dumps(original)) if version == 2 else {
                "schemaVersion": 1, "records": [{"slice": "us1", "pr": 41, "merged_sha": "a" * 40}]}
            data["records"][0][field] = ["src/demo.py", payload] if field == "declared_files" else payload
            if field == "merged_sha" and version == 2:
                data["records"][0]["status"] = "merged"
            manifest.write_text(json.dumps(data))
            yield version, field

    def test_pr_fields_render_as_literal_text_after_approval(self):
        self.approval()
        self.map_path.write_text(render_spec_index(self.root)[0][0].rendered)
        self.assertEqual(self.call("record", "apply", approval=self.approval())["status"], "ok")
        payload = "[injected](untrusted.invalid)\n|<b>&\\`"
        literal = "&#91;injected&#93;&#40;untrusted.invalid&#41;&#10;&#124;&#60;b&#62;&#38;&#92;&#96;"
        for version, field in self.injectedPrFields(payload):
            with self.subTest(version=version, field=field):
                text = render_spec_index(self.root)[0][0].rendered
                self.assertNotIn(payload, text)
                self.assertIn(literal, text)
                self.map_path.write_text(text)
                for host in ("claude", "codex"):
                    self.runner_root = Path(__file__).resolve().parents[3] / "dist" / host / "speckit-pro"
                    self.assertEqual(self.call("verify")["status"], "ok")

    def test_external_links_are_refused_in_every_pr_field(self):
        for version, field in self.injectedPrFields("[injected](https://untrusted.invalid)"):
            with self.subTest(version=version, field=field):
                with self.assertRaises(SpecIndexRenderError):
                    render_spec_index(self.root)
                for host in ("claude", "codex"):
                    self.runner_root = Path(__file__).resolve().parents[3] / "dist" / host / "speckit-pro"
                    self.assertRefused(self.call(), "literal text")

    def test_runtime_filenames_cannot_add_markdown_or_external_destinations(self):
        self.approval()
        self.map_path.write_text(render_spec_index(self.root)[0][0].rendered)
        self.assertEqual(self.call("record", "apply", approval=self.approval())["status"], "ok")
        targets = (("evil", "evil", "evil"),
                   ("https:untrusted.invalid", "https&#58;untrusted.invalid", "https%3Auntrusted.invalid"))
        for target, label, destination in targets:
            for directory in ("artifacts", ".process"):
                with self.subTest(directory=directory, target=target):
                    path = self.feature / directory / f"x]({target})[y\n.md"
                    path.parent.mkdir(exist_ok=True)
                    path.write_text("runtime")
                    text = render_spec_index(self.root)[0][0].rendered
                    self.assertIn(f"- [{directory}/x&#93;&#40;{label}&#41;&#91;y&#10;.md]({directory}/x%5D%28{destination}%29%5By%0A.md)", text)
                    self.assertNotIn(f"x]({target})[y", text)
                    self.map_path.write_text(text)
                    for host in ("claude", "codex"):
                        self.runner_root = Path(__file__).resolve().parents[3] / "dist" / host / "speckit-pro"
                        self.assertEqual(self.call("verify")["status"], "ok")

    def test_scoped_package_paths_remain_literal_metadata(self):
        manifest = self.feature / ".process/prs.json"
        data = json.loads(manifest.read_text())
        data["records"][0]["declared_files"] = ["packages/" + chr(64) + "scope/x"]
        manifest.write_text(json.dumps(data))
        self.assertIn("packages/&#64;scope/x", render_spec_index(self.root)[0][0].rendered)

    def test_backlink_labels_can_contain_at_signs_and_www_without_external_links(self):
        for name, label, destination in (("logo" + chr(64) + "2x.png", "logo&#64;2x.png", "logo%402x.png"),
                                          ("www.example.invalid", "www.example.invalid", "www.example.invalid")):
            with self.subTest(name=name):
                path = self.feature / "artifacts" / name
                path.parent.mkdir(exist_ok=True)
                path.write_text("runtime")
                try:
                    text = render_spec_index(self.root)[0][0].rendered
                    self.assertIn(f"- [artifacts/{label}](artifacts/{destination})", text)
                finally:
                    path.unlink()

    def test_schema_one_slice_prefix_stays_literal_at_the_start_of_a_line(self):
        manifest = self.feature / ".process/prs.json"
        for value, literal in (("- injected", "&#45; injected"), ("-", "&#45;"),
                               ("1. injected", "&#49;. injected"), ("1.", "&#49;."),
                               ("    injected", "&#32;   injected")):
            with self.subTest(value=value):
                manifest.write_text(json.dumps({"schemaVersion": 1, "records": [
                    {"slice": value, "pr": 41, "merged_sha": "a" * 40}]}))
                text = render_spec_index(self.root)[0][0].rendered
                self.assertIn("\n" + literal + " · PR#41 · " + "a" * 40 + "\n", text)


class TableStructureApprovalTest(fixtures.PlanningApprovalFixture):
    def test_complete_implement_table_creation_preserves_revision_on_both_hosts(self):
        cases = json.loads((Path(__file__).parent / "fixtures/planning-progress.json").read_text())
        creation = [case for case in cases if case["region"] in (
            "implement-checklist-gate", "feedback-sweep", "consensus-sweep") and case["before"] in (
                "", "## Phase 7: Implement\n", "## Review records\n### Existing context\n")]
        self.assertEqual(len(creation), 4)
        for host in ("claude", "codex"):
            self.runner_root = Path(__file__).resolve().parents[3] / "dist" / host / "speckit-pro"
            for case in creation:
                with self.subTest(host=host, region=case["region"]):
                    self.writeProgressCase(case, "before")
                    before = self.call()["data"]["manifest_digest"]
                    self.writeProgressCase(case, "after")
                    self.assertEqual(self.call()["data"]["manifest_digest"], before)

    def test_separator_removal_width_and_alignment_change_revision(self):
        path = self.feature / "workflow.md"
        original = "## Basic Information\n| Field | Value |\n|---|---|\n| **Stage** | plan |\n"
        path.write_text(original)
        self.assertEqual(self.call("record", "apply", approval=self.approval())["status"], "ok")
        digest = self.call()["data"]["manifest_digest"]
        for host in ("claude", "codex"):
            self.runner_root = Path(__file__).resolve().parents[3] / "dist" / host / "speckit-pro"
            for separator in ("", "|---|---|---|\n", "|:---|---:|\n"):
                with self.subTest(host=host, separator=separator):
                    path.write_text(original.replace("|---|---|\n", separator))
                    self.assertNotEqual(self.call()["data"]["manifest_digest"], digest)
                    self.assertEqual(self.call("verify")["status"], "input_error")

    def test_owned_table_separator_edits_remain_bound(self):
        tables = (("## Phase 7: Implement\n### Implement Checklist Gate\n", "| Field | Value |", "|---|---|"),
                  ("## Feedback Sweep Log\n", "| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |", "|---|---|---|---|---|---|---|---|"),
                  ("## Consensus Resolution Log\n", "| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |", "|---|---|---|---|---|---|---|---|"))
        path = self.feature / "workflow.md"
        for host in ("claude", "codex"):
            self.runner_root = Path(__file__).resolve().parents[3] / "dist" / host / "speckit-pro"
            for heading, header, separator in tables:
                original = heading + header + "\n" + separator + "\n"
                path.write_text(original)
                digest = self.call()["data"]["manifest_digest"]
                for replacement in ("", separator + "---|\n", separator.replace("---", ":---", 1) + "\n"):
                    with self.subTest(host=host, heading=heading, replacement=replacement):
                        path.write_text(original.replace(separator + "\n", replacement))
                        self.assertNotEqual(self.call()["data"]["manifest_digest"], digest)


if __name__ == "__main__":
    cases = (NavigationInjectionTest, TableStructureApprovalTest)
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in cases)
    raise SystemExit(run_counted(suite, label="test-planning-navigation-inputs"))
