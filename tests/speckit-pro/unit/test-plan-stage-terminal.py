#!/usr/bin/env python3
"""The runner owns the plan stage's terminal sequence (ADR 0026): pages, packet, draft PR, record, stop label."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/speckit-pro/lib"))
sys.path.insert(0, str(ROOT / "speckit-pro"))
from git_fixture import commit_baseline, git, git_stdout  # noqa: E402
from test_result import run_counted  # noqa: E402
from speckit_pro_runner import artifact_review, envelope, stop_policy  # noqa: E402
from speckit_pro_runner.helpers import plan_stage_terminal, registry  # noqa: E402

SOURCE = ROOT / "tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source"
FEATURE = "specs/art-007-draft-pr-emission"
WORKFLOW = "docs/ai/specs/ART-007-workflow.md"
STATE = "docs/ai/specs/autopilot-state.json"
PLANNING = {"plan_file": f"{FEATURE}/plan.md", "spec_file": f"{FEATURE}/spec.md", "tasks_file": f"{FEATURE}/tasks.md"}
CONCEPT = "docs/ai/specs/.process/ART-007-design-concept.md"
URL = "https://github.com/example/repo/pull/7"
LABEL = "stop_reason:plan_stage_boundary"
EVIDENCE_ANCHOR = "Phase 1: Setup (Worktree Preflight)"


class FakeCli:
    """Real git in the fixture repository; scripted gh."""

    def __init__(self, listing: object = (), answers: bool = True) -> None:
        self.listing, self.answers, self.gh = listing, answers, []

    def __call__(self, root: Path, argv: list[str]) -> dict:
        if argv[0] == "git":
            done = git(root, *argv[1:], check=False)
            return {"argv": argv, "exit_status": done.returncode, "stdout_tail": done.stdout.strip(),
                    "stderr_tail": done.stderr.strip()}
        self.gh.append(argv)
        out = ""
        if argv[1:3] == ["pr", "list"]:
            out = json.dumps(self.listing)
        elif argv[1:3] == ["pr", "create"]:
            out = URL
        return {"argv": argv, "exit_status": 0 if self.answers else 1, "stdout_tail": out, "stderr_tail": ""}

    def calls(self, verb: str) -> list[list[str]]:
        return [argv for argv in self.gh if argv[2] == verb]


class TerminalFixture(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name).resolve()
        self.root, remote = base / "work", base / "remote.git"
        (self.root / FEATURE).mkdir(parents=True)
        (self.root / ".specify").mkdir()
        (self.root / "docs/ai/specs").mkdir(parents=True)
        for name in ("spec.md", "plan.md", "tasks.md", "research.md"):
            shutil.copy(SOURCE / name, self.root / FEATURE / name)
        (self.root / CONCEPT).parent.mkdir(parents=True)
        shutil.copy(SOURCE / "design-concept.md", self.root / CONCEPT)
        workflow = (SOURCE / "workflow.md").read_text(encoding="utf-8")
        workflow = re.sub(r"(\| (?:Specify|Clarify|Plan|Checklist|Tasks|Analyze|Confidence Gate) \|[^\n]*?\| )⏳ Pending", r"\1✅ Complete", workflow)
        workflow = workflow.replace("| Mode | <!-- advisory (default) or strict --> |", "| Mode | advisory |")
        (self.root / WORKFLOW).write_text(workflow + "\n📊 Confidence: 0.94\n", encoding="utf-8")
        (self.root / STATE).write_text(json.dumps({"stage": "plan", "status": "in_progress", "plan": []}), encoding="utf-8")
        git(self.root, "init", "-q", "-b", "art-007-draft-pr-emission")
        commit_baseline(self.root, "seed")
        git(self.root, "tag", "seed")
        git(base, "init", "-q", "--bare", str(remote))
        git(self.root, "remote", "add", "origin", str(remote))
        self.remote = remote
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        self.cli = FakeCli()

    def git(self, *args: str) -> str:
        return git_stdout(self.root, *args)

    def subjects(self) -> list[str]:
        return self.git("log", "--format=%s", "seed..HEAD").splitlines()

    def finish(self, mode: str = "apply", **inputs: object) -> dict:
        request = envelope.RunnerRequest("terminal", "finish-plan-stage", "finish-plan-stage", mode,
                                         {"host": "claude", "workflow_file": WORKFLOW, **PLANNING, **inputs}, "compact")
        with unittest.mock.patch.object(plan_stage_terminal, "cli", self.cli):
            return envelope.answer_response(request, registry.dispatch_helper(request))

    def pages(self) -> list[str]:
        return sorted(path.stem for path in (self.root / FEATURE / "artifacts").glob("*.html"))


class OneCallSequenceTests(TerminalFixture):
    def test_one_call_completes_the_sequence_and_returns_the_stop_label(self) -> None:
        result = self.finish(execution_mode="headless")
        self.assertEqual(result["status"], "ok", result)
        data = result["data"]
        self.assertEqual((data["outcome"], data["stop_label"], data["pull_request"]), ("completed", LABEL, {"number": 7, "url": URL}))
        self.assertIn(data["stop_label"].removeprefix("stop_reason:"), stop_policy.STOP_REASONS)
        self.assertEqual(self.subjects(), ["chore(ART-007): record the draft pull request",
                                           "chore(ART-007): add the draft pull request packet",
                                           "chore(ART-007): close the plan stage boundary"])
        self.assertEqual(self.git("rev-parse", "HEAD"), git_stdout(self.remote, "rev-parse", "art-007-draft-pr-emission"))
        self.assertIn(f"| **Draft PR** | [#7]({URL}) |", (self.root / WORKFLOW).read_text(encoding="utf-8"))
        self.assertEqual(json.loads((self.root / STATE).read_text(encoding="utf-8"))["status"], "completed")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertLess(len(json.dumps(result)), envelope.COMPACT_ANSWER_LIMIT_BYTES)

    def test_the_draft_pr_opens_without_a_model_decision(self) -> None:
        self.finish(execution_mode="headless")
        (create,) = self.cli.calls("create")
        flags = dict(zip(create[4::2], create[5::2], strict=False))
        self.assertIn("--draft", create)
        self.assertEqual((flags["--base"], flags["--head"]), ("main", "art-007-draft-pr-emission"))
        self.assertRegex(flags["--title"], r"^feat\(art-007\): plan Draft-PR Emission$")
        body = (self.root / flags["--body-file"]).read_text(encoding="utf-8")
        self.assertRegex(body, r"(?s)^# feat\(art-007\).*\n## Artifacts\n.*\n## Resume\n.*--stage implement")
        self.assertEqual(re.findall(r"^## (.+)$", body, re.MULTILINE), ["Artifacts", "Resume"])

    def test_a_headless_run_records_the_preview_unavailable_and_dispatches_no_observer(self) -> None:
        data = self.finish(execution_mode="headless")["data"]
        self.assertEqual(data["preview"]["status"], "unavailable")
        self.assertEqual(data["preview"]["observer_dispatches"], [])
        self.assertIn("preview unavailable", data["preview"]["note"])

    def test_an_interactive_run_hands_back_the_pages_that_need_an_observer(self) -> None:
        data = self.finish()["data"]
        self.assertEqual((data["outcome"], data["stop_label"]), ("preview_pending", None))
        self.assertEqual(data["preview"]["observer_dispatches"], data["pages"]["generated"])
        self.assertEqual(json.loads((self.root / STATE).read_text(encoding="utf-8"))["status"], "completed")

    def test_a_dry_run_writes_nothing(self) -> None:
        self.assertEqual(self.finish("dry_run")["status"], "ok")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertEqual(self.cli.gh, [])


class NarrativeTests(TerminalFixture):
    def test_plain_text_edits_in_mixed_regions_remain_publishable(self) -> None:
        prose = "The author compares A &amp; B &lt;carefully&gt;."
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.setUp()
                self.finish(host=host, until="pages")
                for page_id, opening in (("implementation-plan", r'<p class="lede"[^>]*>'),
                                         ("module-map", r'<figcaption><p[^>]*>')):
                    page = self.root / FEATURE / "artifacts" / f"{page_id}.html"
                    altered, count = re.subn(f"({opening})[^<]*(</p>)", rf"\g<1>{prose}\g<2>",
                                            page.read_text(), count=1)
                    self.assertEqual(count, 1)
                    page.write_text(altered, encoding="utf-8")
                result = self.finish(host=host, execution_mode="headless")
                self.assertEqual(result["data"]["outcome"], "completed", result)
                for page_id in ("implementation-plan", "module-map"):
                    self.assertIn(prose, (self.root / FEATURE / "artifacts" / f"{page_id}.html").read_text())

    def test_the_finishing_call_keeps_the_prose_the_author_wrote(self) -> None:
        data = self.finish(until="pages")["data"]
        self.assertEqual(data["outcome"], "pages_ready")
        self.assertIn("artifact-author", data["next_action"])
        self.assertEqual(self.subjects(), [])
        page = self.root / FEATURE / "artifacts" / f"{data['pages']['generated'][0]}.html"
        page.write_text(page.read_text(encoding="utf-8").replace("<body", "<body data-author=\"wrote\"", 1), encoding="utf-8")
        written = page.read_bytes()
        self.finish(execution_mode="headless")
        self.assertEqual(page.read_bytes(), written)

    def test_repeated_pages_call_keeps_authored_prose_before_publication(self) -> None:
        data = self.finish(until="pages")["data"]
        identifier = data["pages"]["generated"][0]
        request = envelope.RunnerRequest("author", "fill-artifact-page", "fill-artifact-page", "apply",
                                         {**PLANNING, "entry_id": identifier,
                                          "narrative": {"feature-header": "The author explains the reviewed planning boundary."}})
        self.assertEqual(registry.dispatch_helper(request)["status"], "ok")
        page = self.root / FEATURE / "artifacts" / f"{identifier}.html"
        written = page.read_bytes()
        self.assertIn(b"The author explains", written)
        self.assertEqual(self.finish(until="pages")["status"], "ok")
        self.assertEqual(page.read_bytes(), written)
        self.assertEqual(self.subjects(), [])


class RerunTests(TerminalFixture):
    def test_a_rerun_after_success_refreshes_the_recorded_pull_request_and_adds_no_commit(self) -> None:
        self.finish(execution_mode="headless")
        commits = self.subjects()
        self.cli.listing = [{"number": 7, "url": URL, "state": "OPEN", "title": "feat(art-007): plan Draft-PR Emission"}]
        data = self.finish(execution_mode="headless")["data"]
        self.assertEqual((data["pull_request"]["number"], len(self.cli.calls("create")), self.subjects()), (7, 1, commits))
        self.assertNotIn("--title", self.cli.calls("edit")[0])

    def test_retry_retains_brokered_observations_and_denials(self) -> None:
        self.finish(execution_mode="headless")
        self.cli.listing = [{"number": 7, "url": URL, "state": "OPEN", "title": "feat(art-007): plan Draft-PR Emission"}]
        path = self.root / WORKFLOW
        text = path.read_text(encoding="utf-8")
        record = artifact_review.record_from_workflow(text)
        statuses = ("denied", "verified", "unavailable", "denied")
        for page, status in zip(record["pages"], statuses, strict=True):
            page["preview"] = {"status": status, "blocker": None if status == "verified" else "Brokered disposition",
                               "observation": {"kind": "brokered", "verdict": status, "artifact_sha256": page["sha256"],
                                               "observed_at": "2026-01-01T00:00:00+00:00"}}
        section = "## Artifact Review Handoff\n\n```json\n" + json.dumps(record, indent=2) + "\n```\n"
        path.write_text(plan_stage_terminal.SECTION.sub(lambda _: section, text), encoding="utf-8")
        self.git("commit", "-q", "-am", "record brokered observations")
        before = artifact_review.review_handoff(path.read_text(), self.root, plan_stage_terminal.trusted_bytes, "unavailable")
        self.assertEqual(before["status"], "pending")
        result = self.finish(execution_mode="headless")
        self.assertEqual(result["data"]["preview"]["status"], "pending")
        self.assertNotEqual(result["data"]["outcome"], "completed")
        after = artifact_review.record_from_workflow(path.read_text())
        self.assertEqual([p["preview"] for p in after["pages"]], [p["preview"] for p in record["pages"]])

    def test_a_page_with_active_content_stops_before_any_commit(self) -> None:
        data = self.finish(until="pages")["data"]
        page = self.root / FEATURE / "artifacts" / f"{data['pages']['generated'][0]}.html"
        text = page.read_text(encoding="utf-8")
        page.write_text(re.sub(r"(<!-- FILL:[a-z0-9-]+:START -->)", r"\1<script>alert(1)</script>", text, count=1), encoding="utf-8")
        result = self.finish(execution_mode="headless")
        self.assertEqual(result["data"]["stop_label"], "stop_reason:integrity_failure")
        self.assertEqual((self.subjects(), self.cli.gh), ([], []))


class ContentEvidenceTests(TerminalFixture):
    def test_expected_content_comes_from_planning_not_the_first_page_passage(self) -> None:
        self.finish(until="pages")
        identifier = "implementation-plan"
        request = envelope.RunnerRequest("author", "fill-artifact-page", "fill-artifact-page", "apply",
                                         {**PLANNING, "entry_id": identifier,
                                          "narrative": {"feature-header": "An unrelated explanation about a different feature."}})
        self.assertEqual(registry.dispatch_helper(request)["status"], "ok")
        page = self.root / FEATURE / "artifacts" / f"{identifier}.html"
        written = page.read_text()
        for tag in ("p", "dd", "li", "h2"):
            with self.subTest(tag=tag):
                altered = written if tag == "p" else re.sub(r'<p class="lede"[^>]*>', f"<{tag}>", written).replace("different feature.</p>", f"different feature.</{tag}>")
                page.write_text(altered, encoding="utf-8")
                result = self.finish(until="pages")
                if tag != "p":
                    self.assertNotEqual(result["status"], "ok")
                    continue
                self.assertEqual(result["status"], "ok")
                record = artifact_review.record_from_workflow((self.root / WORKFLOW).read_text())
                entry = next(p for p in record["pages"] if p["id"] == identifier)
                self.assertEqual(entry["expected_title"], "Implementation Plan — art-007-draft-pr-emission Draft-PR Emission")
                self.assertEqual(entry["expected_content"], EVIDENCE_ANCHOR)

    def test_wrong_title_and_wrong_planning_anchor_cannot_certify_generation(self) -> None:
        self.finish(until="pages")
        page = self.root / FEATURE / "artifacts/implementation-plan.html"
        written = page.read_text()
        for variant in ("title", "body"):
            with self.subTest(variant=variant):
                altered = re.sub(r"<title>.*?</title>", "<title>Unrelated feature title</title>", written) if variant == "title" else written.replace(EVIDENCE_ANCHOR, "Unrelated fabricated phase")
                page.write_text(altered, encoding="utf-8")
                self.assertNotEqual(self.finish(execution_mode="headless")["status"], "ok")
                self.assertEqual((self.subjects(), self.cli.gh), ([], []))


class PageRefusalFixture(TerminalFixture):
    def assert_page_edit_refused(self, page_id: str, rewrite: tuple[str, str],
                                *, replace_anchor: bool = False) -> None:
        pattern, replacement = rewrite
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.setUp()
                self.finish(host=host, until="pages")
                page = self.root / FEATURE / "artifacts" / f"{page_id}.html"
                original = page.read_text()
                if replace_anchor:
                    original = original.replace(EVIDENCE_ANCHOR, "Unrelated fabricated phase")
                altered, count = re.subn(pattern, replacement, original, count=1)
                self.assertEqual(count, 1, "the attack must rewrite a generated field")
                page.write_text(altered, encoding="utf-8")
                result = self.finish(host=host, execution_mode="headless")
                self.assertEqual(result["data"]["stop_label"], "stop_reason:integrity_failure", result)
                self.assertIn("planning markup", result["diagnostics"][0]["message"], result)
                self.assertEqual((self.subjects(), self.cli.gh), ([], []))
                self.assertEqual(json.loads((self.root / STATE).read_text())["status"], "in_progress")


class HiddenContentEvidenceTests(PageRefusalFixture):
    def test_hidden_content_variants_cannot_supply_evidence(self) -> None:
        variants = (
            ("hidden", "<p hidden>EVIDENCE</p>"),
            ("display-none", '<p style="display:none">EVIDENCE</p>'),
            ("visibility-hidden", '<p style="visibility:hidden">EVIDENCE</p>'),
            ("opacity-zero", '<p style="opacity:0">EVIDENCE</p>'),
            ("template", "<template><p>EVIDENCE</p></template>"),
            ("closed-details", "<details><summary>Unrelated</summary><p>EVIDENCE</p></details>"),
            ("aria-hidden", '<p aria-hidden="true">EVIDENCE</p>'),
            ("script", "<script>EVIDENCE</script>"),
            ("comment", "<!-- EVIDENCE -->"),
            ("hidden-false", '<p HIDDEN="false">EVIDENCE</p>'),
            ("css-comment-important", '<p style="DISPLAY:/**/none!important">EVIDENCE</p>'),
            ("decimal-opacity", '<p style="opacity:0.0!important">EVIDENCE</p>'),
            ("content-visibility", '<p style="content-visibility:hidden">EVIDENCE</p>'),
            ("zero-font", '<p style="font-size:0">EVIDENCE</p>'),
            ("transparent-text", '<p style="color:transparent">EVIDENCE</p>'),
            ("fallback-class", '<p class="fallback">EVIDENCE</p>'),
            ("svg", '<svg><text>EVIDENCE</text></svg>'),
            ("hidden-input", '<input type="hidden" value="EVIDENCE">'),
            ("title-attribute", '<p title="EVIDENCE">Unrelated</p>'),
            ("nested-aria-hidden", '<p aria-hidden="true"><b>EVIDENCE</b></p>'),
            ("open-details", '<details open><summary>Unrelated</summary>EVIDENCE</details>'),
        )
        for variant, conceal in variants:
            with self.subTest(variant=variant):
                self.assert_page_edit_refused("implementation-plan", (r"(<!-- FILL:feature-header:END -->)",
                                             conceal.replace("EVIDENCE", EVIDENCE_ANCHOR) + r"\1"),
                                             replace_anchor=True)


class ConcealedPassageTests(TerminalFixture):
    def test_concealment_cannot_wrap_the_original_structured_passage(self) -> None:
        self.finish(until="pages")
        page = self.root / FEATURE / "artifacts/implementation-plan.html"
        original = page.read_text()
        for wrapper in ('<span hidden>EVIDENCE</span>', '<span style="opacity:0">EVIDENCE</span>',
                        '<template>EVIDENCE</template>', '<details>EVIDENCE</details>'):
            with self.subTest(wrapper=wrapper):
                page.write_text(original.replace(EVIDENCE_ANCHOR, wrapper.replace("EVIDENCE", EVIDENCE_ANCHOR)),
                                encoding="utf-8")
                result = self.finish(execution_mode="headless")
                self.assertIn("planning markup", result["diagnostics"][0]["message"], result)
                self.assertEqual((self.subjects(), self.cli.gh), ([], []))

    def test_prose_cannot_hide_unchanged_evidence_across_fill_boundaries(self) -> None:
        self.finish(until="pages")
        page = self.root / FEATURE / "artifacts/implementation-plan.html"
        text = page.read_text().replace("<!-- FILL:feature-header:END -->", '<div hidden><!-- FILL:feature-header:END -->')
        text = text.replace("<!-- FILL:task-inventory:START -->", "<!-- FILL:task-inventory:START --></div>")
        page.write_text(text, encoding="utf-8")
        result = self.finish(execution_mode="headless")
        self.assertIn("planning markup", result["diagnostics"][0]["message"], result)
        self.assertEqual((self.subjects(), self.cli.gh), ([], []))


class StructuredContentEvidenceTests(PageRefusalFixture):
    def test_structured_field_variants_cannot_be_rewritten(self) -> None:
        variants = [(page_id, field, pattern, replacement)
                    for page_id in ("implementation-plan", "spec-explainer", "code-approaches", "module-map")
                    for field, pattern, replacement in (
                        ("feature-id", r'(<span id="feature-id">)[^<]+', r"\g<1>fabricated-feature-id"),
                        ("feature-name", r'(<h1 id="feature-name">)[^<]+',
                         r"\g<1>Delete the production billing tables" if page_id == "implementation-plan"
                         else r"\g<1>Fabricated feature name"),
                        ("eyebrow", r'(</span> · )draft pull request', r"\g<1>approved production release"))]
        variants.extend((
            ("module-map", "module-row", r'(?s)(<!-- FILL:module-graph:START -->.*?<li>)[^<]+',
             r"\g<1>payments/ledger: 40 files"),
            ("module-map", "file-count", r'(?s)(<!-- FILL:module-graph:START -->.*?<li>[^<]*: )\d+ file',
             r"\g<1>40 file"),
        ))
        for page_id, field, pattern, replacement in variants:
            with self.subTest(page_id=page_id, field=field):
                self.assert_page_edit_refused(page_id, (pattern, replacement))


class PayloadEvidenceTests(unittest.TestCase):
    def test_both_shipped_runners_reject_every_hidden_content_variant(self) -> None:
        for plugin in ("dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                script = (
                    "import runpy, sys, unittest\n"
                    "sys.path.insert(0, sys.argv[1])\n"
                    "from speckit_pro_runner.helpers import registry\n"
                    "scope = runpy.run_path(sys.argv[2])\n"
                    "suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(scope[name])\n"
                    "    for name in ('HiddenContentEvidenceTests', 'ConcealedPassageTests',\n"
                    "                 'StructuredContentEvidenceTests', 'NarrativeTests'))\n"
                    "result = unittest.TextTestRunner().run(suite)\n"
                    "sys.exit(not result.wasSuccessful())\n"
                )
                done = subprocess.run([sys.executable, "-c", script, str(ROOT / plugin), str(Path(__file__).resolve())],
                                      capture_output=True, text=True, check=False)
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


class FreshnessTests(TerminalFixture):
    def test_research_changes_deletion_and_creation_invalidate_generation(self) -> None:
        research = self.root / FEATURE / "research.md"
        original = research.read_bytes()
        for change in ("edit", "delete", "create"):
            with self.subTest(change=change):
                if change == "create":
                    research.unlink(missing_ok=True)
                else:
                    research.write_bytes(original)
                self.finish(until="pages")
                if change == "delete":
                    research.unlink()
                else:
                    research.write_bytes(original + b"\nNew research evidence.\n")
                text = (self.root / WORKFLOW).read_text()
                handoff = artifact_review.review_handoff(text, self.root, plan_stage_terminal.trusted_bytes, "unavailable")
                self.assertFalse(handoff["reuse_artifacts"])
                self.assertEqual(handoff["status"], "pending")
                before = self.git("status", "--porcelain")
                result = self.finish(execution_mode="headless")
                self.assertNotEqual(result["status"], "ok")
                self.assertEqual(self.git("status", "--porcelain"), before)
                self.assertEqual(self.cli.gh, [])
                # A fresh pages request explicitly rebuilds against the changed inputs.
                self.assertEqual(self.finish(until="pages")["status"], "ok")

    def test_alternate_planning_paths_cannot_escape_the_fingerprinted_inputs(self) -> None:
        for field, original in PLANNING.items():
            with self.subTest(field=field):
                alternate = f"{FEATURE}/alternate-{Path(original).name}"
                shutil.copy(self.root / original, self.root / alternate)
                result = self.finish(until="pages", **{field: alternate})
                self.assertNotEqual(result["status"], "ok")
                self.assertFalse((self.root / FEATURE / "artifacts").exists())
                self.assertEqual((self.subjects(), self.cli.gh), ([], []))

    def test_other_consumed_planning_inputs_are_fingerprinted(self) -> None:
        for path in (CONCEPT, *PLANNING.values()):
            with self.subTest(path=path):
                self.finish(until="pages")
                file = self.root / path
                file.write_bytes(file.read_bytes() + b"\nUpdated planning evidence.\n")
                text = (self.root / WORKFLOW).read_text()
                self.assertFalse(artifact_review.review_handoff(text, self.root, plan_stage_terminal.trusted_bytes)["reuse_artifacts"])
                self.assertNotEqual(self.finish(execution_mode="headless")["status"], "ok")
                self.assertEqual(self.finish(until="pages")["status"], "ok")


class PullRequestTests(TerminalFixture):
    def record(self, number: int = 7) -> None:
        path = self.root / WORKFLOW
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("| **Priority** | P1 |", f"| **Priority** | P1 |\n| **Draft PR** | [#{number}]({URL}) |"),
                        encoding="utf-8")
        self.git("commit", "-q", "-am", "seed row")

    def stops(self, label: str, **inputs: object) -> dict:
        result = self.finish(execution_mode="headless", **inputs)
        self.assertEqual((result["status"], result["data"]["stop_label"]), ("expected_failure", f"stop_reason:{label}"), result)
        self.assertEqual(self.cli.calls("create"), [])
        return result

    def test_an_open_pull_request_on_the_branch_is_refreshed_never_duplicated(self) -> None:
        self.cli.listing = [{"number": 7, "url": URL, "state": "OPEN", "title": "old title"}]
        data = self.finish(execution_mode="headless")["data"]
        self.assertEqual((self.cli.calls("create"), data["pull_request"]["number"]), ([], 7))
        (edit,) = self.cli.calls("edit")
        self.assertEqual(edit[3], "7")
        self.assertIn("--title", edit)
        self.assertIn("[#7]", (self.root / WORKFLOW).read_text(encoding="utf-8"))

    def test_a_closed_recorded_pull_request_stops_and_leaves_the_row(self) -> None:
        self.record()
        self.cli.listing = [{"number": 7, "url": URL, "state": "CLOSED", "title": "t"}]
        self.stops("reopen_closed_pr")
        self.assertIn(f"[#7]({URL})", (self.root / WORKFLOW).read_text(encoding="utf-8"))

    def test_a_missing_recorded_pull_request_is_ambiguous(self) -> None:
        self.record()
        self.stops("ambiguous_pr_record")

    def test_two_open_pull_requests_are_ambiguous(self) -> None:
        self.cli.listing = [{"number": n, "url": URL, "state": "OPEN", "title": "t"} for n in (7, 8)]
        self.stops("ambiguous_pr_record")

    def test_a_query_that_cannot_answer_never_creates(self) -> None:
        self.cli.answers = False
        self.stops("tool_unavailable")

    def test_a_failed_push_stops_before_any_pull_request(self) -> None:
        shutil.rmtree(self.remote)
        self.stops("plan_stage_boundary")
        self.assertEqual(self.cli.gh, [])


class CleanupBoundaryTests(TerminalFixture):
    def test_external_artifacts_are_never_traversed_or_removed(self) -> None:
        external = self.root.parent / "external"
        external.mkdir()
        shutil.copy(self.root / FEATURE / "plan.md", external / "plan.md")
        artifacts = external / "artifacts"
        artifacts.mkdir()
        for name in ("implementation-plan.html", ".artifact-author-retained.tmp"):
            (artifacts / name).write_text("external sentinel", encoding="utf-8")
        feature = self.root / FEATURE
        for variant in ("traversal", "absolute", "feature-link", "artifact-link"):
            with self.subTest(variant=variant):
                inputs = {}
                if variant in {"traversal", "absolute"}:
                    inputs["plan_file"] = "../external/plan.md" if variant == "traversal" else str(external / "plan.md")
                elif variant == "feature-link":
                    feature.rename(feature.with_name("saved-feature"))
                    feature.symlink_to(external, target_is_directory=True)
                else:
                    (feature / "artifacts").symlink_to(artifacts, target_is_directory=True)
                try:
                    result = self.finish(until="pages", **inputs)
                    self.assertNotEqual(result["status"], "ok", result)
                    self.assertEqual({p.name: p.read_text() for p in artifacts.iterdir()},
                                     {"implementation-plan.html": "external sentinel", ".artifact-author-retained.tmp": "external sentinel"})
                    self.assertEqual((self.subjects(), self.cli.gh), ([], []))
                finally:
                    if variant == "feature-link":
                        feature.unlink()
                        feature.with_name("saved-feature").rename(feature)
                    elif variant == "artifact-link":
                        (feature / "artifacts").unlink()

    def test_directory_substitution_before_cleanup_preserves_external_files(self) -> None:
        self.finish(until="pages")
        artifacts = self.root / FEATURE / "artifacts"
        external = self.root.parent / "external"
        external.mkdir()
        sentinel = external / "implementation-plan.html"
        sentinel.write_text("external sentinel", encoding="utf-8")
        (external / ".artifact-author-retained.tmp").write_text("retained", encoding="utf-8")
        original = registry.dispatch_helper
        swapped = False

        def swap(request: envelope.RunnerRequest) -> dict:
            nonlocal swapped
            result = original(request)
            if request.helper_id == "confidence-gate" and not swapped:
                artifacts.rename(artifacts.with_name("saved-artifacts"))
                artifacts.symlink_to(external, target_is_directory=True)
                swapped = True
            return result

        with unittest.mock.patch.object(registry, "dispatch_helper", side_effect=swap):
            self.assertNotEqual(self.finish(until="pages")["status"], "ok")
        self.assertEqual(sentinel.read_text(), "external sentinel")
        self.assertEqual((external / ".artifact-author-retained.tmp").read_text(), "retained")


class CleanupRetentionTests(TerminalFixture):
    def test_cleanup_retains_unowned_temporary_and_linked_entries(self) -> None:
        self.finish(until="pages")
        artifacts = self.root / FEATURE / "artifacts"
        temporary = artifacts / ".artifact-author-retained.tmp"
        temporary.write_text("retained", encoding="utf-8")
        self.finish(until="pages")
        self.assertEqual(temporary.read_text(), "retained")
        external = self.root.parent / "external.html"
        external.write_text("external sentinel", encoding="utf-8")
        page = artifacts / "implementation-plan.html"
        for link in ("symlink", "hardlink"):
            with self.subTest(link=link):
                page.unlink(missing_ok=True)
                if link == "symlink":
                    page.symlink_to(external)
                else:
                    os.link(external, page)
                self.assertNotEqual(self.finish(until="pages")["status"], "ok")
                self.assertEqual(external.read_text(), "external sentinel")
                self.assertTrue(page.exists())


class ConfidenceRecoveryTests(TerminalFixture):
    def test_real_mode_spellings_and_configured_threshold_reach_the_gate(self) -> None:
        path = self.root / WORKFLOW
        original = path.read_text()
        for mode in ("Advisory", "advisory (resolved at Step 0.6b: no flag, no local config)",
                     "`advisory`, resolved at Step 0.6b", "**advisory** — resolved at Step 0.6b"):
            with self.subTest(mode=mode):
                path.write_text(original.replace("| Mode | advisory |", f"| Mode | {mode} |"), encoding="utf-8")
                self.assertEqual(self.finish(until="pages")["status"], "ok")
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                config = self.root / f".{host}/speckit-pro.local.md"
                config.parent.mkdir(exist_ok=True)
                config.write_text("confidence_threshold: 0.80\n", encoding="utf-8")
                path.write_text(original.replace("| Mode | advisory |", "| Mode | **Strict** — resolved at Step 0.6b |")
                               .replace("0.94", "0.85"), encoding="utf-8")
                self.assertEqual(self.finish(host=host, until="pages")["status"], "ok")
                config.write_text("confidence_threshold: 0.95\n", encoding="utf-8")
                self.assertNotEqual(self.finish(host=host, until="pages")["status"], "ok")

    def test_no_data_stops_with_a_documented_confidence_recovery_path(self) -> None:
        path = self.root / WORKFLOW
        path.write_text(path.read_text().replace("📊 Confidence: 0.94", ""), encoding="utf-8")
        result = self.finish(until="pages")
        self.assertIn("rerun Analyze", result["data"]["report"])
        self.assertEqual(json.loads((self.root / STATE).read_text())["status"], "in_progress")
        self.assertFalse((self.root / FEATURE / "artifacts").exists())
        for reference in ("phase-execution.md", "gate-validation.md"):
            with self.subTest(reference=reference):
                guidance = (ROOT / "speckit-pro/skills/speckit-autopilot/references" / reference).read_text()
                no_data = guidance.split("- exit 1 (NO_DATA", 1)[1].split("- exit 2 (FAIL", 1)[0]
                self.assertIn("rerun Analyze", no_data)
                self.assertNotIn("Advance to Phase 7", no_data)
                self.assertNotIn("proceed", no_data)


class GuardTests(TerminalFixture):
    def test_a_blocked_gate_stops_before_generation_and_writes_nothing(self) -> None:
        path = self.root / WORKFLOW
        path.write_text(path.read_text(encoding="utf-8").replace("| Confidence Gate | G6.5 | ✅ Complete", "| Confidence Gate | G6.5 | ⚠️ Blocked"),
                        encoding="utf-8")
        self.git("commit", "-q", "-am", "blocked")
        result = self.finish(execution_mode="headless")
        self.assertEqual(result["data"]["stop_label"], "stop_reason:strict_confidence_opt_in")
        self.assertFalse((self.root / FEATURE / "artifacts").exists())
        self.assertEqual((self.subjects(), self.cli.gh), (["blocked"], []))

    def test_unfinished_or_unresolved_planning_never_mutates(self) -> None:
        path = self.root / WORKFLOW
        original = path.read_text(encoding="utf-8")
        variants = [("Confidence Gate", value) for value in ("⏳ Pending", "", "Failed", "Unknown", None)]
        variants += [(phase, "⏳ Pending") for phase in ("Specify", "Clarify", "Plan", "Checklist", "Tasks", "Analyze")]
        for phase, status in variants:
            with self.subTest(phase=phase, status=status):
                pattern = rf"(?m)^\| {phase} \|[^\n]*$"
                row = re.search(pattern, original)[0]
                changed = row.replace("✅ Complete", status) if status is not None else ""
                path.write_text(re.sub(pattern, lambda _: changed, original), encoding="utf-8")
                before = self.git("status", "--porcelain")
                result = self.finish(execution_mode="headless")
                self.assertNotEqual(result["status"], "ok", result)
                self.assertFalse((self.root / FEATURE / "artifacts").exists())
                self.assertEqual(self.git("status", "--porcelain"), before)
                self.assertEqual((self.subjects(), self.cli.gh), ([], []))

    def test_complete_rows_require_an_explicit_confidence_verdict(self) -> None:
        path = self.root / WORKFLOW
        original = path.read_text(encoding="utf-8")
        for emit in ("", "📊 Confidence: failed", "📊 Confidence: unknown"):
            with self.subTest(emit=emit):
                path.write_text(original.replace("📊 Confidence: 0.94", emit), encoding="utf-8")
                self.assertNotEqual(self.finish(until="pages")["status"], "ok")
                self.assertFalse((self.root / FEATURE / "artifacts").exists())
        path.write_text(original.replace("| Mode | advisory |", "| Mode | strict |").replace("0.94", "0.50"), encoding="utf-8")
        self.assertNotEqual(self.finish(until="pages")["status"], "ok")
        self.assertFalse((self.root / FEATURE / "artifacts").exists())

    def test_a_completed_advisory_warning_allows_pages(self) -> None:
        path = self.root / WORKFLOW
        path.write_text(path.read_text(encoding="utf-8").replace("📊 Confidence: 0.94", "📊 Confidence: 0.50"), encoding="utf-8")
        self.assertEqual(self.finish(until="pages")["status"], "ok")

    def test_a_page_that_is_still_its_template_is_deleted_and_reported_as_a_gap(self) -> None:
        artifacts = self.root / FEATURE / "artifacts"
        artifacts.mkdir()
        shutil.copy(ROOT / "speckit-pro/artifact-gallery/templates/implementation-plan.html", artifacts / "implementation-plan.html")
        data = self.finish(execution_mode="headless")["data"]
        self.assertNotIn("implementation-plan", data["pages"]["generated"])
        self.assertEqual([gap["id"] for gap in data["pages"]["gaps"]], ["implementation-plan"])
        self.assertNotIn("implementation-plan", self.pages())
        self.assertEqual(data["outcome"], "completed")


class FixtureRootTests(unittest.TestCase):
    def test_terminal_fixture_resolves_a_symlinked_temporary_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            actual, alias = base / "actual", base / "alias"
            actual.mkdir()
            alias.symlink_to(actual, target_is_directory=True)
            fixture = TerminalFixture()
            try:
                with unittest.mock.patch.object(tempfile, "gettempdir", return_value=str(alias)):
                    fixture.setUp()
                self.assertEqual(fixture.root, fixture.root.resolve())
                fixture.finish(execution_mode="headless")
                review = artifact_review.review_handoff((fixture.root / WORKFLOW).read_text(), fixture.root,
                                                       plan_stage_terminal.trusted_bytes, "unavailable")
                self.assertTrue(review["reuse_artifacts"])
            finally:
                fixture.doCleanups()


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-plan-stage-terminal"))
