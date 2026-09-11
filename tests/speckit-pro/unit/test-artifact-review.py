#!/usr/bin/env python3
"""Artifact preview evidence and preview-only resume regression tests."""

from __future__ import annotations

import copy
import hashlib
import json
import runpy
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "speckit-pro"))
sys.path.insert(0, str(ROOT / "tests/speckit-pro/lib"))

from speckit_pro_runner import artifact_review
from speckit_pro_runner.helpers.read_only import resolve_autopilot_stage, trusted_bytes
from test_result import run_counted


class ArtifactReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = ROOT / "speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py"
        cls.coverage = runpy.run_path(str(path))

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.feature = "specs/001-review-demo"
        directory = self.root / self.feature
        (directory / "artifacts").mkdir(parents=True)
        inputs = {}
        for name in ("spec.md", "plan.md", "tasks.md"):
            path = f"{self.feature}/{name}"
            (self.root / path).write_text("Review Demo preserves the existing draft PR.\n")
            inputs[path] = hashlib.sha256((self.root / path).read_bytes()).hexdigest()
        self.gallery = ROOT / "speckit-pro/artifact-gallery"
        self.record = {
            "schema_version": "1.0",
            "feature_dir": self.feature,
            "input_hashes": inputs,
            "manifest_sha256": hashlib.sha256((self.gallery / "manifest.json").read_bytes()).hexdigest(),
            "template_hashes": {},
            "generation_error": None,
            "pages": [],
        }
        for identifier in ("implementation-plan", "spec-explainer"):
            path = f"{self.feature}/artifacts/{identifier}.html"
            title = f"Review Demo: {identifier}"
            body = f"Review Demo {identifier} preserves the existing draft PR."
            (self.root / path).write_text(f"<html><head><title>{title}</title></head><body><p>{body}</p></body></html>")
            self.record["template_hashes"][identifier] = hashlib.sha256(
                (self.gallery / f"templates/{identifier}.html").read_bytes()
            ).hexdigest()
            self.record["pages"].append({
                "id": identifier, "generation": "generated", "path": path,
                "sha256": hashlib.sha256((self.root / path).read_bytes()).hexdigest(),
                "expected_title": title, "expected_content": body,
                "preview": {"status": "pending", "blocker": "Not observed yet", "observation": None},
            })

    def workflow(self, record: dict | None = None, *, implement: str = "⏳ Pending") -> str:
        rows = "\n".join(f"| {phase} | /test | ✅ Complete | |" for phase in (
            "Specify", "Clarify", "Plan", "Checklist", "Tasks", "Analyze", "Confidence Gate",
        ))
        text = (
            "# Review Demo\n\n## Workflow Overview\n\n| Phase | Command | Status | Notes |\n"
            "|---|---|---|---|\n" + rows + f"\n| Implement | /test | {implement} | |\n\n"
            "### Basic Information\n\n| Field | Value |\n|---|---|\n| Stage | plan |\n"
            "| Draft PR | [#12](https://github.com/example/demo/pull/12) |\n"
        )
        if record is not None:
            text += "\n## Artifact Review Handoff\n\n```json\n" + json.dumps(record) + "\n```\n"
        return text

    def review(self, record: dict | None = None) -> dict:
        return artifact_review.review_handoff(
            self.workflow(self.record if record is None else record), self.root, trusted_bytes,
        )

    def verify(self, index: int = 0) -> None:
        page = self.record["pages"][index]
        page["preview"] = {
            "status": "verified", "blocker": None,
            "observation": {
                "kind": "rendered", "title": page["expected_title"],
                "body_text": page["expected_content"], "route": "native-html",
                "reference": f"observation-{index}", "observed_at": "2026-09-10T18:00:00Z",
            },
        }

    def resolve(self, *, args: list[str] | None = None, text: str | None = None) -> dict:
        (self.root / "workflow.md").write_text(text or self.workflow(self.record))
        return resolve_autopilot_stage({"workflow_file": "workflow.md", "autopilot_args": args or []}, self.root)

    def test_valid_pending_record_is_not_a_validation_failure(self) -> None:
        result = self.review()
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["resume_action"], "preview")
        self.assertTrue(result["reuse_artifacts"])
        self.assertEqual(result["verified"], 0)

    def test_all_rendered_pages_are_verified(self) -> None:
        self.verify(0)
        self.verify(1)
        self.assertEqual(self.review()["status"], "verified")
        self.assertEqual(self.review()["verified"], 2)

    def test_partial_success_preserves_per_page_dispositions(self) -> None:
        self.verify()
        self.record["pages"][1]["preview"]["blocker"] = "queued"
        result = self.review()
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["verified"], 1)
        self.assertEqual([page["status"] for page in result["pages"]], ["verified", "pending"])

    def test_open_receipts_never_verify_a_page(self) -> None:
        for kind in ("queued", "open", "http", "file", "tab"):
            with self.subTest(kind=kind):
                self.verify()
                self.record["pages"][0]["preview"]["observation"]["kind"] = kind
                with self.assertRaises(ValueError):
                    self.review()

    def test_wrong_blank_error_and_title_only_observations_cannot_verify(self) -> None:
        for body in ("", "404 Not Found", "Unrelated feature", "Review Demo: implementation-plan"):
            with self.subTest(body=body):
                self.verify()
                self.record["pages"][0]["preview"]["observation"]["body_text"] = body
                with self.assertRaises(ValueError):
                    self.review()
        self.verify()
        self.record["pages"][0]["preview"]["observation"]["title"] = "Wrong title"
        with self.assertRaises(ValueError):
            self.review()

    def test_denied_and_headless_dispositions_are_valid_but_unverified(self) -> None:
        for status, blocker in (("denied", "Browser access denied"), ("unavailable", "No rendered observer in CLI")):
            with self.subTest(status=status):
                self.record["pages"][0]["preview"].update(status=status, blocker=blocker)
                result = self.review()
                self.assertEqual(result["pages"][0]["blocker"], blocker)
                self.assertEqual(result["verified"], 0)
                self.assertTrue((self.root / self.record["pages"][0]["path"]).is_file())

    def test_modified_inputs_require_generation_but_bookkeeping_does_not(self) -> None:
        self.assertTrue(self.review()["reuse_artifacts"])
        (self.root / self.feature / "plan.md").write_text("Changed plan")
        result = self.review()
        self.assertFalse(result["reuse_artifacts"])
        self.assertEqual(result["resume_action"], "generate")

    def test_changed_or_missing_page_invalidates_preview_without_deleting_files(self) -> None:
        self.verify()
        path = self.root / self.record["pages"][0]["path"]
        path.write_text("Changed content")
        result = self.review()
        self.assertEqual(result["verified"], 0)
        self.assertEqual(path.read_text(), "Changed content")
        path.unlink()
        self.assertFalse(self.review()["reuse_artifacts"])

    def test_one_changed_page_preserves_other_preview_evidence(self) -> None:
        self.verify(0)
        self.verify(1)
        (self.root / self.record["pages"][0]["path"]).write_text("Modified first page")
        result = self.review()
        self.assertEqual(result["verified"], 1)
        self.assertEqual(result["pages"][1]["status"], "verified")

    def test_input_changes_do_not_erase_a_policy_denial(self) -> None:
        self.record["pages"][0]["preview"].update(status="denied", blocker="Origin access denied")
        (self.root / self.feature / "plan.md").write_text("New plan")
        self.assertEqual(self.review()["pages"][0]["status"], "denied")

    def test_symlink_cannot_redirect_an_artifact_to_another_feature(self) -> None:
        path = self.root / self.record["pages"][0]["path"]
        other = self.root / "other.html"
        other.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(other)
        with self.assertRaises(ValueError):
            self.review()

    def test_missing_template_hash_and_omitted_mandatory_page_are_rejected(self) -> None:
        self.record["template_hashes"]["implementation-plan"] = None
        with self.assertRaises(ValueError):
            self.review()
        self.record["pages"].pop(0)
        del self.record["template_hashes"]["implementation-plan"]
        with self.assertRaises(ValueError):
            self.review()

    def test_template_gap_is_separate_from_verified_previews(self) -> None:
        self.verify(0)
        self.verify(1)
        self.record["pages"].append({"id": "architecture-viewer", "generation": "gap", "reason": "Template is planned, not shipped"})
        self.record["template_hashes"]["architecture-viewer"] = None
        result = self.review()
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["generation_gaps"], ["architecture-viewer"])

    def test_whole_set_generation_failure_requires_no_previews(self) -> None:
        self.record.update(pages=[], template_hashes={}, generation_error="Author returned no complete result")
        original = copy.deepcopy(self.record)
        for stale in (None, "planning", "gallery"):
            with self.subTest(stale=stale):
                self.record = copy.deepcopy(original)
                if stale == "planning":
                    self.record["input_hashes"][f"{self.feature}/spec.md"] = "0" * 64
                elif stale == "gallery":
                    self.record["manifest_sha256"] = "0" * 64
                result = self.review()
                self.assertEqual(result["status"], "not_applicable")
                self.assertEqual(result["generated"], 0)
                self.assertEqual(result["verified"], 0)
                self.assertEqual(result["resume_action"], "generate" if stale else "none")
                self.assertEqual(result["reuse_artifacts"], stale is None)
                self.assertEqual(result["generation_error"], "Author returned no complete result")

    def test_duplicate_pages_bad_hashes_and_path_escape_are_rejected(self) -> None:
        invalid = copy.deepcopy(self.record)
        invalid["pages"].append(copy.deepcopy(invalid["pages"][0]))
        with self.assertRaises(ValueError):
            self.review(invalid)
        for key, value in (("path", "../outside.html"), ("sha256", "not-a-hash")):
            invalid = copy.deepcopy(self.record)
            invalid["pages"][0][key] = value
            with self.assertRaises(ValueError):
                self.review(invalid)

    def test_comments_and_examples_do_not_become_records(self) -> None:
        section = self.workflow(self.record).split("## Artifact Review Handoff", 1)[1]
        for text in (f"<!--\n## Artifact Review Handoff{section}\n-->", f"````markdown\n## Artifact Review Handoff{section}\n````"):
            with self.subTest(text=text[:20]):
                self.assertEqual(artifact_review.review_handoff(text, self.root, trusted_bytes)["status"], "absent")

    def test_malformed_or_duplicate_sections_cannot_be_treated_as_absent(self) -> None:
        for text in ("## Artifact Review Handoff\n", self.workflow(self.record) * 2,
                     '## Artifact Review Handoff\n```json\n{"schema_version":"1.0","schema_version":"1.0"}\n```'):
            with self.subTest(text=text[:40]), self.assertRaises(ValueError):
                artifact_review.review_handoff(text, self.root, trusted_bytes)

    def test_explicit_null_is_not_legacy_absence(self) -> None:
        with self.assertRaises(ValueError):
            artifact_review.review_handoff("## Artifact Review Handoff\n```json\nnull\n```", self.root, trusted_bytes)

    def test_literal_comment_text_inside_json_is_preserved(self) -> None:
        self.record["pages"][0]["preview"]["blocker"] = "Rendered example contains <!-- but observer is unavailable"
        self.assertEqual(self.review()["pages"][0]["blocker"], self.record["pages"][0]["preview"]["blocker"])

    def test_nested_json_example_cannot_supply_live_evidence(self) -> None:
        example = "## Artifact Review Handoff\n````markdown\n```json\n" + json.dumps(self.record) + "\n```\n````\n"
        with self.assertRaises(ValueError):
            artifact_review.review_handoff(example, self.root, trusted_bytes)

    def test_coverage_gate_accepts_pending_and_rejects_false_verification(self) -> None:
        with unittest.mock.patch.dict(self.coverage["artifact_review_errors"].__globals__, _repository_root=unittest.mock.Mock(return_value=self.root)):
            errors = self.coverage["artifact_review_errors"](self.root / "workflow.md", self.workflow(self.record))
            self.assertEqual(errors, {"artifact_review_errors": []})
            self.record["pages"][0]["preview"]["status"] = "verified"
            errors = self.coverage["artifact_review_errors"](self.root / "workflow.md", self.workflow(self.record))
            self.assertTrue(errors["artifact_review_errors"])
        self.assertIn("artifact_review_errors", self.coverage["RULE_PROBLEM_KEYS"]["status-evidence"])

    def test_coverage_gate_does_not_require_record_in_legacy_workflows(self) -> None:
        with unittest.mock.patch.dict(self.coverage["artifact_review_errors"].__globals__, _repository_root=unittest.mock.Mock(side_effect=AssertionError("No new legacy prerequisite"))):
            self.assertEqual(self.coverage["artifact_review_errors"](self.root / "workflow.md", self.workflow()), {"artifact_review_errors": []})

    def test_both_parents_reference_the_shared_delivery_and_resume_contract(self) -> None:
        for directory, suffix in (("skills", ""), ("codex-skills", "-codex")):
            path = ROOT / f"speckit-pro/{directory}/speckit-autopilot/references/phase-execution{suffix}.md"
            text = path.read_text()
            self.assertIn("artifact-review.md", text)
            self.assertLess(text.index("6. Take a separate bookkeeping commit"), text.index("7. The parent opens and observes"))
            self.assertIn("preview-only resume", text)
            self.assertIn("direct local file links", text)

    def test_default_resume_returns_to_preview_without_redefining_planning_complete(self) -> None:
        result = self.resolve()
        self.assertEqual(result["exit_code"], 0)
        data = json.loads(result["stdout"])
        self.assertEqual(data["stage"], "plan")
        self.assertTrue(data["planning_complete"])
        self.assertEqual(data["artifact_review"]["resume_action"], "preview")

    def test_explicit_implementation_preserves_the_preview_warning(self) -> None:
        data = json.loads(self.resolve(args=["--stage", "implement"])["stdout"])
        self.assertEqual(data["stage"], "implement")
        self.assertEqual(data["artifact_review"]["status"], "pending")

    def test_finished_previews_resume_implementation(self) -> None:
        self.verify(0)
        self.verify(1)
        data = json.loads(self.resolve()["stdout"])
        self.assertEqual(data["stage"], "implement")

    def test_legacy_plan_draft_is_unverified_but_started_implementation_keeps_routing(self) -> None:
        data = json.loads(self.resolve(text=self.workflow())["stdout"])
        self.assertEqual(data["stage"], "plan")
        self.assertEqual(data["artifact_review"]["status"], "unrecorded")
        data = json.loads(self.resolve(text=self.workflow(implement="🔄 In Progress"))["stdout"])
        self.assertEqual(data["stage"], "implement")

    def test_invalid_record_is_a_stage_input_error(self) -> None:
        self.record["schema_version"] = "unknown"
        result = self.resolve()
        self.assertEqual(result["exit_code"], 2)
        self.assertIn("artifact review", result["stderr"].lower())


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(ArtifactReviewTests), label="test-artifact-review"))
