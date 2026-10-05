#!/usr/bin/env python3
"""Artifact preview evidence and preview-only resume regression tests."""

from __future__ import annotations

import copy
import hashlib
import json
import re
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
from speckit_pro_runner.agent_materialization import digest
from speckit_pro_runner.helpers.read_only import resolve_autopilot_stage, trusted_bytes
from guide_text import guide_text, host_source
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
        def render_template(identifier, title, body):
            template = (self.gallery / f"templates/{identifier}.html").read_text(encoding="utf-8")
            pattern = re.compile(r"(<!--\s*FILL:document-title:START\s*-->)(.*?)(<!--\s*FILL:document-title:END\s*-->)", re.DOTALL)
            replacement = rf"\1<title>{title}</title><h1>{body}</h1>\3"
            return pattern.sub(replacement, template, count=1)
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
            (self.root / path).write_text(render_template(identifier, title, body))
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

    def review(self, record: dict | None = None, **surface: str) -> dict:
        return artifact_review.review_handoff(
            self.workflow(self.record if record is None else record), self.root, trusted_bytes, **surface,
        )

    def verify(self, index: int = 0) -> None:
        page = self.record["pages"][index]
        page["preview"] = {
            "status": "verified", "blocker": None,
            "observation": {
                "kind": "brokered", "verdict": "verified",
                "artifact_sha256": page["sha256"],
                "observed_at": "2026-09-10T18:00:00Z",
            },
        }

    def resolve(self, *, args: list[str] | None = None, text: str | None = None) -> dict:
        (self.root / "workflow.md").write_text(text or self.workflow(self.record))
        return resolve_autopilot_stage({"workflow_file": "workflow.md", "autopilot_args": args or []}, self.root)

    def test_valid_pending_record_is_not_a_validation_failure(self) -> None:
        result = self.review()
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["resume_action"], "preview")
        self.assertEqual(result["observer"], artifact_review.OBSERVER)
        self.assertTrue(result["reuse_artifacts"])
        self.assertEqual(result["verified"], 0)

    def test_one_observer_dispatch_per_page_with_a_preview_surface(self) -> None:
        for surface in ("available", "unknown"):
            with self.subTest(surface=surface):
                result = self.review(preview_surface=surface)
                self.assertEqual(result["observer"], artifact_review.OBSERVER)
                self.assertEqual(result["observer_dispatches"], ["implementation-plan", "spec-explainer"])
                self.assertEqual(result["resume_action"], "preview")
                self.assertNotIn("preview_note", result)
        self.verify(0)
        self.assertEqual(self.review(preview_surface="available")["observer_dispatches"], ["spec-explainer"])

    def test_no_observer_dispatch_without_a_preview_surface(self) -> None:
        result = self.review(preview_surface="unavailable")
        self.assertIsNone(result["observer"])
        self.assertEqual(result["observer_dispatches"], [])
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["resume_action"], "none")
        self.assertEqual(result["preview_note"], artifact_review.NO_SURFACE_NOTE)
        self.assertEqual([page["status"] for page in result["pages"]], ["unavailable", "unavailable"])
        self.assertTrue(all(page["blocker"] == artifact_review.NO_SURFACE_NOTE for page in result["pages"]))
        self.assertTrue(result["reuse_artifacts"])

    def test_no_surface_keeps_verified_pages_and_policy_denials(self) -> None:
        self.verify(0)
        self.record["pages"][1]["preview"].update(status="denied", blocker="Origin access denied")
        result = self.review(preview_surface="unavailable")
        self.assertEqual([page["status"] for page in result["pages"]], ["verified", "denied"])
        self.assertEqual(result["observer_dispatches"], [])
        self.assertEqual(result["status"], "pending")

    def test_stale_pages_regenerate_before_any_observer_dispatch(self) -> None:
        (self.root / self.feature / "plan.md").write_text("Changed plan")
        for surface in ("available", "unavailable"):
            with self.subTest(surface=surface):
                result = self.review(preview_surface=surface)
                self.assertEqual(result["resume_action"], "generate")
                self.assertEqual(result["observer_dispatches"], [])

    def test_a_surface_outside_the_closed_set_is_rejected(self) -> None:
        for surface in ("headless", "", "Available"):
            with self.subTest(surface=surface):
                with self.assertRaisesRegex(ValueError, "preview_surface must be one of"):
                    self.review(preview_surface=surface)

    def test_the_stage_helper_reads_the_surface_from_the_readiness_record(self) -> None:
        def stage(host: str | None) -> dict:
            (self.root / "workflow.md").write_text(self.workflow(self.record))
            inputs = {"workflow_file": "workflow.md", "autopilot_args": [], **({"host": host} if host else {})}
            return json.loads(resolve_autopilot_stage(inputs, self.root)["stdout"])["artifact_review"]
        self.assertEqual(stage("claude")["observer_dispatches"], ["implementation-plan", "spec-explainer"])
        self.write_readiness("claude", "unavailable")
        self.assertEqual(stage(None)["observer_dispatches"], ["implementation-plan", "spec-explainer"])
        self.assertEqual(stage("codex")["observer_dispatches"], ["implementation-plan", "spec-explainer"])
        review = stage("claude")
        self.assertEqual((review["observer"], review["observer_dispatches"], review["status"]), (None, [], "unavailable"))
        self.write_readiness("claude", "verified")
        self.assertEqual(stage("claude")["observer_dispatches"], ["implementation-plan", "spec-explainer"])
        result = resolve_autopilot_stage({"workflow_file": "workflow.md", "autopilot_args": [], "host": "gemini"}, self.root)
        self.assertEqual(result["exit_code"], 2)

    def write_readiness(self, host: str, status: str) -> None:
        directory = self.root / ".specify/readiness"
        directory.mkdir(parents=True, exist_ok=True)
        item = {"status": status, "evidence_source": "session tools", "observed_at": "2026-10-05T00:00:00Z", "fingerprints": {}}
        record = {"schema_version": "readiness-record/v1", "binding": {"worktree": digest(str(self.root))}, "host": host,
                  "items": {"preview_surface": item}}
        (directory / f"{host}.json").write_text(json.dumps(record))

    def test_untrusted_html_outside_template_regions_is_rejected(self) -> None:
        path = self.root / self.record["pages"][0]["path"]
        path.write_text(path.read_text().replace("<!DOCTYPE html>", "<!DOCTYPE html><!-- injected -->", 1))
        self.record["pages"][0]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "trusted fill"):
            self.review()

    def test_all_rendered_pages_are_verified(self) -> None:
        self.verify(0)
        self.verify(1)
        self.assertEqual(self.review()["status"], "verified")
        self.assertEqual(self.review()["verified"], 2)

    def test_closed_unavailability_finishes_handoff_without_claiming_verification(self) -> None:
        for unavailable_indexes in ((0, 1), (1,)):
            with self.subTest(unavailable_indexes=unavailable_indexes):
                self.verify(0)
                self.verify(1)
                for index in unavailable_indexes:
                    preview = self.record["pages"][index]["preview"]
                    preview.update(status="unavailable", blocker="No preview capability")
                    preview["observation"]["verdict"] = "unavailable"
                result = self.review()
                self.assertEqual(result["status"], "unavailable")
                self.assertEqual(result["resume_action"], "none")
                self.assertEqual(result["verified"], 2 - len(unavailable_indexes))
                self.assertTrue(result["reuse_artifacts"])
                for index in unavailable_indexes:
                    self.assertEqual(result["pages"][index]["status"], "unavailable")
                    self.assertEqual(result["pages"][index]["blocker"], "No preview capability")
                    self.assertEqual(result["pages"][index]["path"], self.record["pages"][index]["path"])
                data = json.loads(self.resolve()["stdout"])
                self.assertEqual(data["stage"], "implement")
                self.assertTrue(data["planning_complete"])
                self.assertEqual(data["artifact_review"]["resume_action"], "none")

    def test_unavailability_without_matching_broker_observation_stays_pending(self) -> None:
        self.verify(0)
        preview = self.record["pages"][1]["preview"]
        preview.update(status="unavailable", blocker="No preview capability")
        for observation in (None, {
            "kind": "brokered", "verdict": "unavailable",
            "artifact_sha256": "0" * 64, "observed_at": "2026-09-10T18:00:00Z",
        }):
            with self.subTest(observation=observation):
                preview["observation"] = observation
                result = self.review()
                self.assertEqual(result["status"], "pending")
                self.assertEqual(result["resume_action"], "preview")
                self.assertEqual(result["pages"][1]["status"], "pending")
                self.assertTrue(result["pages"][1]["blocker"])
                self.assertEqual(result["verified"], 1)
                self.assertTrue(result["reuse_artifacts"])

    def test_partial_success_preserves_per_page_dispositions(self) -> None:
        self.verify()
        self.record["pages"][1]["preview"]["blocker"] = "queued"
        result = self.review()
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["verified"], 1)
        self.assertEqual([page["status"] for page in result["pages"]], ["verified", "pending"])

    def test_unfinished_or_stale_delivery_cannot_become_terminal_unavailability(self) -> None:
        self.verify(0)
        self.verify(1)
        preview = self.record["pages"][1]["preview"]
        preview.update(status="unavailable", blocker="No preview capability")
        preview["observation"]["verdict"] = "unavailable"
        original = copy.deepcopy(self.record)
        for state in ("pending", "denied", "changed-artifact", "changed-inputs"):
            with self.subTest(state=state):
                self.record = copy.deepcopy(original)
                if state in ("pending", "denied"):
                    self.record["pages"][0]["preview"] = {
                        "status": state, "blocker": "Preview unresolved", "observation": None,
                    }
                elif state == "changed-artifact":
                    self.record["pages"][1]["sha256"] = "0" * 64
                else:
                    self.record["input_hashes"][f"{self.feature}/plan.md"] = "0" * 64
                result = self.review()
                self.assertEqual(result["status"], "pending")
                self.assertEqual(result["resume_action"], "preview" if state in ("pending", "denied") else "generate")
                data = json.loads(self.resolve()["stdout"])
                self.assertEqual(data["stage"], "plan")

    def test_non_brokered_receipts_never_verify_a_page(self) -> None:
        for kind in ("rendered", "queued", "open", "http", "file", "tab"):
            with self.subTest(kind=kind):
                self.verify()
                self.record["pages"][0]["preview"]["observation"]["kind"] = kind
                with self.assertRaises(ValueError):
                    self.review()

    def test_wrong_digest_verdict_and_timestamp_cannot_verify(self) -> None:
        for key, value in (
            ("artifact_sha256", "0" * 64),
            ("verdict", "denied"),
            ("observed_at", "2026-09-10T18:00:00"),
            ("observed_at", "2999-01-01T00:00:00Z"),
        ):
            with self.subTest(key=key, value=value):
                self.verify()
                self.record["pages"][0]["preview"]["observation"][key] = value
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
        for host in ("claude", "codex"):
            text = host_source("skills/speckit-autopilot/references/phase-execution.md", host)
            self.assertIn("artifact-review.md", text)
            self.assertLess(text.index("Take a separate bookkeeping commit"), text.index("The parent dispatches `artifact-preview-observer`"))
            self.assertIn("preview-only resume", text)
            self.assertIn("direct local file links", text)

    def test_preview_guidance_requires_broker_readback_before_verification(self) -> None:
        text = guide_text("skills/speckit-autopilot/references/artifact-review.md", "claude")
        self.assertIn("`close_session`", text)
        self.assertIn("Compare the observer's closed verdict and", text)
        self.assertIn("Never create `observed_at` in the parent", text)

    def test_each_host_describes_its_own_observer_tools(self) -> None:
        relative = "skills/speckit-autopilot/references/artifact-review.md"
        claude = guide_text(relative, "claude")
        codex = guide_text(relative, "codex")
        self.assertIn("The observer has only the `Artifact` tool and the broker's verdict tool", claude)
        self.assertNotIn("preview-isolation-session", claude)
        self.assertIn("only the broker's verdict tool (no `Artifact` tool and no network)", codex)
        self.assertIn("`named_surface=observe_codex`", codex)
        self.assertIn("`unavailable` is its normal verdict", codex)
        self.assertNotIn("The observer has only the `Artifact` tool", codex)
        self.assertIn("Never create `observed_at` in the parent", codex)
        for text in (claude, codex):
            normalized = " ".join(text.split())
            self.assertIn("terminal `unavailable` with `resume_action: none`", normalized)
            self.assertIn("`denied` remains pending and retained on resume", normalized)
            self.assertIn("each unverified page's disposition and exact blocker", normalized)

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
