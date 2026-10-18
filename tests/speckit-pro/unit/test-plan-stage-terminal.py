#!/usr/bin/env python3
"""The runner owns the plan stage's terminal sequence (ADR 0026): pages, packet, draft PR, record, stop label."""

from __future__ import annotations

import dataclasses
import functools
import hashlib
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, get_ident

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/speckit-pro/lib"))
sys.path.insert(0, str(ROOT / "speckit-pro"))
from git_fixture import commit_baseline, git, git_stdout  # noqa: E402
from structural_helpers import load_json  # noqa: E402
import host_skill_views  # noqa: E402
from test_result import run_counted  # noqa: E402
from speckit_pro_runner import autopilot_state, artifact_review, envelope, execution_control, stop_policy  # noqa: E402
from speckit_pro_runner.helpers import plan_stage_terminal, registry  # noqa: E402
from speckit_pro_runner.runtime import handle_request  # noqa: E402

SOURCE = ROOT / "tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source"
FEATURE = "specs/art-007-draft-pr-emission"
WORKFLOW = "docs/ai/specs/ART-007-workflow.md"
STATE = "docs/ai/specs/autopilot-state.json"
PLANNING = {"plan_file": f"{FEATURE}/plan.md", "spec_file": f"{FEATURE}/spec.md", "tasks_file": f"{FEATURE}/tasks.md"}
CONCEPT = "docs/ai/specs/.process/ART-007-design-concept.md"
URL = "https://github.com/example/repo/pull/7"
LABEL = "stop_reason:plan_stage_boundary"
FINDINGS = f"{FEATURE}/planning-findings.json"
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


def after_cli_call(original, prefix: tuple[str, ...], occurrence: int, action):
    """Inject one filesystem action after the chosen real Git command has returned."""
    calls = 0

    def invoke(root: Path, argv: list[str]) -> dict:
        nonlocal calls
        result = original(root, argv)
        if tuple(argv[:len(prefix)]) == prefix:
            calls += 1
            if calls == occurrence:
                action(root)
        return result

    return invoke


def stage_unowned_entry(root: Path, *, entry: Path, content: str, commit_subject: str | None = None) -> None:
    entry.write_text(content)
    git(root, "add", "--", str(entry))
    if commit_subject is not None:
        git(root, "commit", "-q", "-m", commit_subject)
    entry.unlink()


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

    def rewrite_workflow(self, *swaps: tuple[str, str], commit: str | None = None) -> None:
        path = self.root / WORKFLOW
        text = path.read_text(encoding="utf-8")
        for old, new in swaps:
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
        if commit is not None:
            self.git("commit", "-q", "-am", commit)


class RunFactsTests(TerminalFixture):
    def test_read_only_and_dry_run_leave_the_state_bytes_unchanged(self) -> None:
        state = (self.root / STATE).read_bytes()
        control = execution_control.execution_control(self.root, {"workflow_file": WORKFLOW, "action": "start"}, "apply")
        for mode in ("read_only", "dry_run"):
            with self.subTest(mode=mode):
                request = envelope.RunnerRequest("clock", "execution-control", "execution-control", mode,
                                                 {"workflow_file": WORKFLOW, "action": "status",
                                                  "expected_run_id": control["ledger"]["run_id"]})
                self.assertEqual(registry.dispatch_helper(request)["status"], "ok")
                self.assertEqual((self.root / STATE).read_bytes(), state)

    def test_terminal_excludes_evidenced_waits_from_elapsed_time(self) -> None:
        started = time.time() - 100
        binding = {"workflow_file": WORKFLOW}
        with unittest.mock.patch.object(execution_control.time, "time", return_value=started):
            control = execution_control.execution_control(self.root, {**binding, "action": "start"}, "apply")
        binding.update(expected_run_id=control["ledger"]["run_id"])
        event = {"kind": "human_uat", "run_id": binding["expected_run_id"]}
        with unittest.mock.patch.object(execution_control.time, "time", return_value=started + 20):
            execution_control.execution_control(self.root, {**binding, "action": "pause", "native_observation": {
                **event, "native_event_id": "wait-start", "action": "wait_started"}}, "apply")
        with unittest.mock.patch.object(execution_control.time, "time", return_value=started + 50):
            execution_control.execution_control(self.root, {**binding, "action": "resume", "native_observation": {
                **event, "native_event_id": "wait-end", "action": "wait_ended", "wait_start_event_id": "wait-start"}}, "apply")
        (self.root / STATE).write_text(json.dumps({"stage": "plan", "status": "in_progress", "execution_control": {
            "ledger_path": control["ledger_path"], "run_id": binding["expected_run_id"], "elapsed_seconds": 0}}))
        self.assertEqual(self.finish(execution_mode="headless")["status"], "ok")
        recorded = json.loads((self.root / STATE).read_text())
        self.assertAlmostEqual(recorded["execution_control"]["elapsed_seconds"], 70, delta=5)

    def test_execution_helper_refreshes_the_state_without_replacing_the_plan(self) -> None:
        state = {"stage": "plan", "status": "in_progress",
                 "plan": [{"step": "Phase 3: Plan", "status": "in_progress"}]}
        (self.root / STATE).write_text(json.dumps(state), encoding="utf-8")
        request = envelope.RunnerRequest("clock", "execution-control", "execution-control", "apply",
                                         {"workflow_file": WORKFLOW, "action": "start"}, "detailed")
        before = datetime.now(timezone.utc)
        result = registry.dispatch_helper(request)
        after = datetime.now(timezone.utc)
        self.assertEqual(result["status"], "ok", result)
        recorded = json.loads((self.root / STATE).read_text(encoding="utf-8"))
        self.assertLessEqual(before, datetime.fromisoformat(recorded["updated_at"]))
        self.assertLessEqual(datetime.fromisoformat(recorded["updated_at"]), after)
        self.assertEqual(recorded["plan"], state["plan"])
        self.assertEqual(recorded["status"], state["status"])
        self.assertEqual(recorded["execution_control"]["run_id"], result["data"]["ledger"]["run_id"])

    def test_a_malformed_state_file_does_not_hide_an_applied_ledger_change(self) -> None:
        for malformed in ("[]", "{not json"):
            with self.subTest(state=malformed):
                self.setUp()
                (self.root / STATE).write_text(malformed, encoding="utf-8")
                request = envelope.RunnerRequest("clock", "execution-control", "execution-control", "apply",
                                                 {"workflow_file": WORKFLOW, "action": "start"}, "detailed")
                result = registry.dispatch_helper(request)
                self.assertEqual(result["status"], "ok", result)
                self.assertTrue(result["data"]["ledger"]["run_id"])
                self.assertEqual(["state_mirror_not_refreshed"], [item["code"] for item in result["diagnostics"]])
                self.assertEqual((self.root / STATE).read_text(encoding="utf-8"), malformed)
                # The compact answer must steer to a state refresh, never a retry of the applied mutation.
                compact = envelope.answer_response(dataclasses.replace(request, answer_format="compact"), result)
                self.assertIn("action=status mode=apply", compact["next_action"])
                self.assertNotIn("retry", compact["next_action"].lower())


class RunFactsConcurrencyTests(TerminalFixture):
    def test_execution_refresh_preserves_plan_observed_by_guarded_state_read(self) -> None:
        observed_plan = [{"step": "Phase 3: Plan", "status": "completed"}]
        snapshot = autopilot_state.snapshot

        def observe_current_plan(root, target):
            state = json.loads(target.read_text())
            state["plan"] = observed_plan
            target.write_text(json.dumps(state))
            return snapshot(root, target)

        request = envelope.RunnerRequest("clock", "execution-control", "execution-control", "apply",
                                         {"workflow_file": WORKFLOW, "action": "start"}, "detailed")
        with unittest.mock.patch.object(autopilot_state, "snapshot", side_effect=observe_current_plan):
            result = registry.dispatch_helper(request)
        self.assertEqual(result["status"], "ok", result)
        recorded = json.loads((self.root / STATE).read_text())
        self.assertEqual(recorded["plan"], observed_plan)
        self.assertEqual(recorded["execution_control"]["run_id"], result["data"]["ledger"]["run_id"])


class TerminalClockTests(TerminalFixture):
    def test_terminal_refreshes_runner_clock_facts_on_both_hosts(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.setUp()
                with unittest.mock.patch.object(execution_control.time, "time", return_value=time.time() - 100):
                    control = execution_control.execution_control(self.root, {
                        "workflow_file": WORKFLOW, "spec_file": PLANNING["spec_file"], "action": "start",
                    }, "apply")
                state = {"stage": "plan", "status": "in_progress", "plan": [],
                         "updated_at": "2026-01-01T00:00:00Z",
                         "execution_control": {"ledger_path": control["ledger_path"],
                                               "run_id": control["ledger"]["run_id"], "elapsed_seconds": 0}}
                (self.root / STATE).write_text(json.dumps(state), encoding="utf-8")
                before = datetime.now(timezone.utc)
                result = self.finish(host=host, execution_mode="headless")
                after = datetime.now(timezone.utc)
                self.assertEqual(result["status"], "ok", result)
                recorded = json.loads((self.root / STATE).read_text(encoding="utf-8"))
                updated = datetime.fromisoformat(recorded["updated_at"])
                self.assertLessEqual(before, updated)
                self.assertLessEqual(updated, after)
                self.assertAlmostEqual(recorded["execution_control"]["elapsed_seconds"], 100, delta=5)
                self.assertEqual(recorded["execution_control"]["run_id"], control["ledger"]["run_id"])


class OneCallSequenceTests(TerminalFixture):
    def test_canonical_absolute_workflow_completes_and_publishes_bookkeeping(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.setUp()
                result = self.finish(host=host, workflow_file=str((self.root / WORKFLOW).resolve()),
                                     execution_mode="headless")
                self.assertEqual(result["status"], "ok", result)
                self.assertEqual(result["data"]["outcome"], "completed")
                self.assertEqual(len(self.cli.calls("create")), 1)
                self.assertEqual(len(self.subjects()), 3)
                self.assertEqual(self.subjects()[0], "chore(ART-007): record the draft pull request")
                self.assertEqual(json.loads((self.root / STATE).read_text())["status"], "completed")
                self.assertIn(f"| **Draft PR** | [#7]({URL}) |", (self.root / WORKFLOW).read_text())
                self.assertEqual(self.git("rev-parse", "HEAD"), git_stdout(self.remote, "rev-parse", "art-007-draft-pr-emission"))
                self.assertEqual(self.git("status", "--porcelain"), "")

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


class StopReportTests(TerminalFixture):
    def test_a_completed_run_returns_the_stop_report_the_parent_prints(self) -> None:
        """The parent prints `report` and then `stop_label`, so it reads no reference to compose the report."""
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.setUp()
                data = self.finish(host=host, execution_mode="headless")["data"]
                report = data["report"]
                self.assertIn(URL, report)
                for page in data["pages"]["generated"]:
                    self.assertIn(f"{FEATURE}/artifacts/{page}.html", report)
                    self.assertIn(f"](<{self.root}/{FEATURE}/artifacts/{page}.html>)", report)
                self.assertIn("preview unavailable", report)
                self.assertIn(f"{plan_stage_terminal.RESUME[host]} {WORKFLOW} --stage implement", report)
                self.assertNotIn("stop_reason:", report)
                self.assertIn("`report`", data["next_action"])

    def test_the_stop_report_names_each_generation_gap(self) -> None:
        artifacts = self.root / FEATURE / "artifacts"
        artifacts.mkdir()
        shutil.copy(ROOT / "speckit-pro/artifact-gallery/templates/implementation-plan.html", artifacts / "implementation-plan.html")
        data = self.finish(execution_mode="headless")["data"]
        (gap,) = data["pages"]["gaps"]
        self.assertIn(f"gap: {gap['reason']}", data["report"])


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
        self.assertEqual(result["data"]["stop_label"], "stop_reason:tampering_or_forged_evidence")
        self.assertEqual((self.subjects(), self.cli.gh), ([], []))

    def test_artifact_binding_drift_is_a_registered_harm_halt_that_blocks_the_next_write(self) -> None:
        page = self.root / FEATURE / "artifacts" / f"{self.finish(until='pages')['data']['pages']['generated'][0]}.html"
        page.write_text(page.read_text(encoding="utf-8") + "<!-- drift -->", encoding="utf-8")
        label = self.finish(execution_mode="headless")["data"]["stop_label"]
        self.assertEqual(stop_policy.stop_class(label.removeprefix("stop_reason:")), "harm_halt")
        record = json.loads((self.root / ".specify/harm-halt/halt.json").read_text(encoding="utf-8"))
        self.assertEqual(record["reason"], label.removeprefix("stop_reason:"))
        blocked = self.finish(execution_mode="headless")
        self.assertEqual(blocked["diagnostics"][0]["code"], "harm_halt_active", blocked)
        self.assertEqual((self.subjects(), self.cli.gh), ([], []))

    def test_stale_planning_inputs_stop_with_a_registered_reason_and_no_halt(self) -> None:
        self.finish(until="pages")
        tasks = self.root / PLANNING["tasks_file"]
        tasks.write_bytes(tasks.read_bytes() + b"\nA late task.\n")
        result = self.finish(execution_mode="headless")
        self.assertEqual(result["data"]["stop_label"], LABEL, result)
        self.assertFalse((self.root / ".specify/harm-halt/halt.json").exists())
        self.assertEqual(self.finish(until="pages")["status"], "ok")


class ConcurrentHaltTests(TerminalFixture):
    def test_a_concurrent_halt_keeps_the_stop_report_and_the_first_record(self) -> None:
        page = self.root / FEATURE / "artifacts" / f"{self.finish(until='pages')['data']['pages']['generated'][0]}.html"
        page.write_text(page.read_text(encoding="utf-8") + "<!-- drift -->", encoding="utf-8")
        record_halt = plan_stage_terminal.harm_halt.record_halt

        def concurrent_trigger_first(root: Path, reason: str, evidence: str, last_safe_state: str) -> dict:
            record_halt(root, "concurrent_writer", "another process", "before the plan stage")
            return record_halt(root, reason, evidence, last_safe_state)

        with unittest.mock.patch.object(plan_stage_terminal.harm_halt, "record_halt", side_effect=concurrent_trigger_first):
            result = self.finish(execution_mode="headless")
        self.assertEqual((result["status"], result["data"]["halt_record_status"]), ("expected_failure", "blocked"), result)
        self.assertEqual(stop_policy.stop_class(result["data"]["stop_label"].removeprefix("stop_reason:")), "harm_halt")
        record = json.loads((self.root / ".specify/harm-halt/halt.json").read_text(encoding="utf-8"))
        self.assertEqual(record["reason"], "concurrent_writer")
        self.assertEqual((self.subjects(), self.cli.gh), ([], []))


class HaltPublicationFixture(TerminalFixture):
    def tamper_stop(self, inject, host: str = "claude") -> dict:
        page = self.root / FEATURE / "artifacts" / f"{self.finish(host=host, until='pages')['data']['pages']['generated'][0]}.html"
        page.write_text(page.read_text(encoding="utf-8") + "<!-- drift -->", encoding="utf-8")
        finish = plan_stage_terminal.finish

        def after_precheck(run, apply):
            try:
                return finish(run, apply)
            except plan_stage_terminal.Stop as stop:
                self.assertEqual("tampering_or_forged_evidence", stop.reason)
                inject()
                raise

        request = envelope.RunnerRequest("tamper", "finish-plan-stage", "finish-plan-stage", "apply",
                                         {"host": host, "workflow_file": WORKFLOW, **PLANNING, "execution_mode": "headless"})
        with unittest.mock.patch.object(plan_stage_terminal, "finish", side_effect=after_precheck), \
                unittest.mock.patch.object(plan_stage_terminal, "cli", self.cli):
            result = handle_request(request)
        self.assertEqual((result["status"], result["data"]["stop_label"]),
                         ("expected_failure", "stop_reason:tampering_or_forged_evidence"), result)
        self.assertEqual((self.subjects(), self.cli.gh), ([], []))
        return result

    def assert_resume_refused(self) -> None:
        result = self.finish(execution_mode="headless")
        self.assertEqual("harm_halt_active", result["diagnostics"][0]["code"], result)



class CompetingHaltFixture(HaltPublicationFixture):
    def competing_trigger(self, last_safe_state, host: str, publication_error=None) -> tuple[dict, dict]:
        entered, release = Event(), Event()
        owner = plan_stage_terminal.harm_halt
        ledger = owner.exclusive_ledger
        publish = owner.durable_json
        plan_thread = get_ident()

        def publishing(path, record):
            if publication_error is not None and record["evidence"] == "first evidence":
                raise publication_error
            publish(path, record)

        @contextmanager
        def paused_ledger(*args, **kwargs):
            with ledger(*args, **kwargs):
                if get_ident() != plan_thread:
                    entered.set()
                    if not release.wait(10):
                        raise RuntimeError("competing writer was not released")
                yield

        def trigger():
            request = envelope.RunnerRequest("competitor", "harm-halt", "harm-halt", "apply",
                                             {"action": "halt", "reason": "concurrent_writer", "evidence": "first evidence",
                                              "last_safe_state": last_safe_state})
            try:
                return handle_request(request)
            finally:
                entered.set()  # Malformed input must finish without ever taking the lock.

        with unittest.mock.patch.object(owner, "exclusive_ledger", side_effect=paused_ledger), \
                unittest.mock.patch.object(owner, "durable_json", side_effect=publishing), ThreadPoolExecutor() as pool:
            pending = []

            def inject():
                pending.append(pool.submit(trigger))
                self.assertTrue(entered.wait(10), "competing writer did not start")

            try:
                stopped = self.tamper_stop(inject, host)
            finally:
                release.set()
            competitor = pending[0].result(timeout=10)
        self.assert_resume_refused()
        return stopped, competitor


class HaltPublisherRaceTests(CompetingHaltFixture):
    def check_competition(self, last_safe_state, competitor_status: str, halt_status: str, expected: dict) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.setUp()
                stopped, competitor = self.competing_trigger(last_safe_state, host)
                self.assertEqual(competitor_status, competitor["status"])
                self.assertEqual(halt_status, stopped["data"]["halt_record_status"])
                record = plan_stage_terminal.harm_halt.stored_halt(self.root)
                self.assertEqual(expected, {key: record[key] for key in expected})

    def test_malformed_competitor_cannot_discard_the_independent_tamper_halt(self) -> None:
        self.check_competition(17, "input_error", "recorded", {"reason": "tampering_or_forged_evidence"})

    def test_valid_competitor_keeps_first_evidence_and_resume_refusal(self) -> None:
        self.check_competition("before plan", "ok", "blocked",
                               {"reason": "concurrent_writer", "evidence": "first evidence"})

    def test_aborting_valid_competitor_leaves_durable_resume_refusal(self) -> None:
        for host, error in itertools.product(("claude", "codex"), (ValueError("rejected"), OSError("disk full"))):
            with self.subTest(host=host, error=type(error).__name__):
                self.setUp()
                stopped, competitor = self.competing_trigger("before plan", host, error)
                self.assertNotEqual("ok", competitor["status"])
                self.assertEqual("blocked", stopped["data"]["halt_record_status"])
                self.assertTrue((self.root / ".specify/harm-halt/halt.lock").is_dir())
                self.assertFalse((self.root / ".specify/harm-halt/halt.json").exists())


class HaltObstructionTests(HaltPublicationFixture):
    def obstruct(self, kind: str, host: str) -> Path:
        record = self.root / ".specify/harm-halt/halt.json"
        obstruction = record.with_suffix(".lock") if "lock" in kind else record

        def inject():
            record.parent.mkdir(parents=True)
            if kind == "lock":
                obstruction.mkdir()
            elif kind == "lock_file":
                obstruction.write_text("foreign lock", encoding="utf-8")
            else:
                target = self.root / "foreign-target"
                if kind in ("lock_symlink", "record_symlink"):
                    target.write_text("foreign content", encoding="utf-8")
                obstruction.symlink_to(target)

        result = self.tamper_stop(inject, host)
        self.assertEqual("blocked", result["data"]["halt_record_status"])
        self.assertNotIn("clear_token", result["data"], "a blocked halt minted no token")
        self.assertTrue(record.is_symlink() or not record.exists())
        if kind in ("lock_symlink", "record_symlink"):
            self.assertEqual("foreign content", (self.root / "foreign-target").read_text(encoding="utf-8"))
        self.assert_resume_refused()
        return obstruction

    def check_obstruction_on_both_hosts(self, kind: str) -> None:
        for host in ("claude", "codex"):
            self.setUp()
            self.obstruct(kind, host)

    def test_lock_appearing_after_precheck_keeps_resume_refused(self) -> None:
        self.check_obstruction_on_both_hosts("lock")

    def test_symlink_appearing_after_precheck_keeps_resume_refused(self) -> None:
        self.check_obstruction_on_both_hosts("symlink")

    def test_linked_or_non_directory_locks_and_live_record_links_refuse_resume(self) -> None:
        for kind in ("lock_file", "lock_symlink", "dangling_lock", "record_symlink"):
            self.check_obstruction_on_both_hosts(kind)

    def test_storage_controller_can_remove_lock_or_symlink_after_the_stop(self) -> None:
        for kind, host, action in itertools.product(("lock", "symlink"), ("claude", "codex"), ("remove", "rename")):
            with self.subTest(kind=kind, host=host, action=action):
                self.setUp()
                obstruction = self.obstruct(kind, host)
                if action == "rename":
                    obstruction.rename(obstruction.with_name("retired-halt-storage"))
                else:
                    obstruction.rmdir() if kind == "lock" else obstruction.unlink()
                self.assertIsNone(plan_stage_terminal.harm_halt.stored_halt(self.root))
                request = envelope.RunnerRequest("resume", "execution-control", "execution-control", "apply",
                                                 {"workflow_file": WORKFLOW, "action": "start"})
                self.assertEqual("ok", handle_request(request)["status"])


class RecordedPlanStopTests(HaltPublicationFixture):
    def test_real_plan_stop_supplies_registered_reason_and_text_state(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.setUp()
                result = self.tamper_stop(lambda: None, host)
                self.assertEqual("recorded", result["data"]["halt_record_status"])
                record = plan_stage_terminal.harm_halt.stored_halt(self.root)
                self.assertEqual("harm_halt", stop_policy.stop_class(record["reason"]))
                self.assertRegex(record["last_safe_state"], r"^HEAD [a-f0-9]+ before the plan stage$")
                self.assert_resume_refused()

    def test_a_recorded_plan_stop_reports_whether_the_clear_token_was_delivered(self) -> None:
        for host, (delivered, expected) in itertools.product(
                ("claude", "codex"), ((True, "shown_on_owner_terminal"), (False, "not_delivered"))):
            with self.subTest(host=host, delivered=delivered):
                self.setUp()
                with unittest.mock.patch.object(plan_stage_terminal.harm_halt, "show_on_owner_terminal",
                                                return_value=delivered):
                    result = self.tamper_stop(lambda: None, host)
                self.assertEqual(("recorded", expected),
                                 (result["data"]["halt_record_status"], result["data"].get("clear_token")), result)


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
                self.assertEqual(result["data"]["stop_label"], "stop_reason:tampering_or_forged_evidence", result)
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
    def test_both_shipped_runners_reject_content_and_publication_violations(self) -> None:
        for plugin in ("dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                script = (
                    "import runpy, sys, unittest\n"
                    "sys.path.insert(0, sys.argv[1])\n"
                    "from speckit_pro_runner.helpers import registry\n"
                    "scope = runpy.run_path(sys.argv[2])\n"
                    "suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(scope[name])\n"
                    "    for name in ('HiddenContentEvidenceTests', 'ConcealedPassageTests',\n"
                    "                 'StructuredContentEvidenceTests', 'NarrativeTests',\n"
                    "                 'PublicationOwnershipTests', 'UnexpectedArtifactEntryTests',\n"
                    "                 'SiblingArtifactPublicationTests', 'StagedArtifactPublicationTests',\n"
                    "                 'ArtifactSubstitutionTests'))\n"
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
        self.rewrite_workflow(("| **Priority** | P1 |", f"| **Priority** | P1 |\n| **Draft PR** | [#{number}]({URL}) |"),
                              commit="seed row")

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


class PublicationOwnershipTests(TerminalFixture):
    def assert_unowned_entry_refused(self, variant: str) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host, variant=variant):
                self.setUp()
                self.assertEqual(self.finish(host=host, until="pages")["status"], "ok")
                artifacts = self.root / FEATURE / "artifacts"
                external = self.root.parent / "external.html"
                external.write_text("private external sentinel", encoding="utf-8")
                name = ".artifact-author-implementation-plan.0123456789abcdef.tmp" if variant == "temporary" else "unowned.html"
                entry = artifacts / name
                if variant == "symlink":
                    entry.symlink_to(external)
                elif variant == "hardlink":
                    os.link(external, entry)
                else:
                    entry.write_text("retained private content", encoding="utf-8")
                result = self.finish(host=host, execution_mode="headless")
                self.assertEqual(result["data"]["stop_label"], "stop_reason:tampering_or_forged_evidence", result)
                self.assertEqual((self.subjects(), self.cli.gh), ([], []))
                self.assertEqual(git(self.remote, "show-ref", check=False).returncode, 1)
                self.assertNotIn(name, self.git("ls-files", "--", f"{FEATURE}/artifacts"))
                self.assertTrue(entry.exists())
                self.assertEqual(external.read_text(), "private external sentinel")

    def test_retained_author_temporary_blocks_publication(self) -> None:
        self.assert_unowned_entry_refused("temporary")

    def test_unowned_final_html_blocks_publication(self) -> None:
        self.assert_unowned_entry_refused("html")

    def test_unowned_hardlink_blocks_publication_without_reading_target(self) -> None:
        self.assert_unowned_entry_refused("hardlink")

    def test_unowned_symlink_blocks_publication_without_publishing_target_string(self) -> None:
        self.assert_unowned_entry_refused("symlink")


class UnexpectedArtifactEntryTests(TerminalFixture):
    def test_every_unexpected_entry_type_blocks_publication(self) -> None:
        for name, kind in (("notes.txt", "file"), ("nested", "directory"), ("pipe", "fifo"),
                           ("broken.html", "broken-link"), ("white space\npage.html", "file")):
            with self.subTest(name=name):
                self.setUp()
                self.finish(until="pages")
                entry = self.root / FEATURE / "artifacts" / name
                if kind == "directory":
                    entry.mkdir()
                    (entry / "private.html").write_text("private content")
                elif kind == "fifo":
                    os.mkfifo(entry)
                elif kind == "broken-link":
                    entry.symlink_to("missing-target")
                else:
                    entry.write_text("private content")
                self.assertEqual(self.finish(execution_mode="headless")["data"]["stop_label"], "stop_reason:tampering_or_forged_evidence")
                self.assertEqual((self.subjects(), self.cli.gh), ([], []))


class PublicationTransactionFixture(TerminalFixture):
    TRANSACTION_CASES = {
        "sibling": ("specs/other-feature/artifacts/unowned.html", ("git", "add", "--"), 1,
                    "private unrelated staged content", None),
        "committed": (f"{FEATURE}/artifacts/unowned.html", ("git", "commit"), 2,
                      "private committed content", "concurrent artifact commit"),
    }

    def assert_unowned_transaction_refused(self, scenario: str) -> None:
        path, prefix, occurrence, content, subject = self.TRANSACTION_CASES[scenario]
        with self.subTest(scenario=scenario):
            self.finish(until="pages")
            entry = self.root / path
            entry.parent.mkdir(parents=True, exist_ok=True)
            action = functools.partial(stage_unowned_entry, entry=entry, content=content, commit_subject=subject)
            self.cli = after_cli_call(self.cli, prefix, occurrence, action)
            result = self.finish(execution_mode="headless")
            expected = "identity_mismatch" if scenario == "sibling" else "tampering_or_forged_evidence"
            self.assertEqual(result["data"]["stop_label"], f"stop_reason:{expected}", result)
            if subject is None:
                self.assertEqual(self.subjects(), [])
            self.assertEqual(git(self.remote, "show-ref", check=False).returncode, 1)


class SiblingArtifactPublicationTests(PublicationTransactionFixture):
    def test_unrelated_feature_artifacts_are_not_swept_into_the_commit(self) -> None:
        self.finish(until="pages")
        sibling = self.root / "specs/other-feature/artifacts"
        sibling.mkdir(parents=True)
        (sibling / "unowned.html").write_text("private unrelated content")
        self.finish(execution_mode="headless")
        self.assertNotIn("other-feature", self.git("ls-tree", "-r", "HEAD"))
        remote = git(self.remote, "ls-tree", "-r", "art-007-draft-pr-emission", check=False)
        self.assertNotIn("other-feature", remote.stdout)

    def test_unowned_staged_artifacts_from_another_feature_block_publication(self) -> None:
        self.assert_unowned_transaction_refused("sibling")


class StagedArtifactPublicationTests(PublicationTransactionFixture):
    def test_staged_then_removed_unowned_entries_block_every_commit_window(self) -> None:
        for host, window in itertools.product(("claude", "codex"), (1, 2, 3)):
            with self.subTest(host=host, window=window):
                self.setUp()
                self.finish(host=host, until="pages")
                entry = self.root / FEATURE / "artifacts" / "unowned.html"
                action = functools.partial(stage_unowned_entry, entry=entry, content="private staged content")
                self.cli = after_cli_call(self.cli, ("git", "add", "--"), window, action)
                result = self.finish(host=host, execution_mode="headless")
                self.assertEqual(result["data"]["stop_label"], "stop_reason:tampering_or_forged_evidence", result)
                local = self.git("ls-tree", "-r", "HEAD", "--", f"{FEATURE}/artifacts")
                self.assertNotIn("unowned.html", local)
                remote = git(self.remote, "ls-tree", "-r", "art-007-draft-pr-emission", check=False)
                self.assertNotIn("unowned.html", remote.stdout)

    def test_committed_unowned_entry_blocks_push(self) -> None:
        self.assert_unowned_transaction_refused("committed")


class ArtifactSubstitutionTests(TerminalFixture):
    def test_staging_substitution_cannot_publish_unvalidated_page_bytes_or_links(self) -> None:
        for host in ("claude", "codex"):
            for variant in ("rename", "hardlink", "symlink"):
                with self.subTest(host=host, variant=variant):
                    self.setUp()
                    self.finish(host=host, until="pages")
                    page = self.root / FEATURE / "artifacts/implementation-plan.html"
                    saved = page.read_bytes()
                    external = self.root.parent / "external.html"
                    external.write_text("private external sentinel")
                    original = self.cli
                    changed = False

                    def swap(root: Path, argv: list[str]) -> dict:
                        nonlocal changed
                        if argv[1:3] != ["add", "--"] or changed:
                            return original(root, argv)
                        changed = True
                        page.unlink()
                        if variant == "symlink":
                            page.symlink_to(external)
                        elif variant == "hardlink":
                            os.link(external, page)
                        else:
                            replacement = page.with_name("replacement")
                            replacement.write_text("unvalidated replacement content")
                            replacement.rename(page)
                        result = original(root, argv)
                        page.unlink()
                        page.write_bytes(saved)
                        return result

                    self.cli = swap
                    result = self.finish(host=host, execution_mode="headless")
                    self.assertEqual(result["data"]["stop_label"], "stop_reason:tampering_or_forged_evidence", result)
                    self.assertEqual(self.subjects(), [])
                    self.assertEqual(external.read_text(), "private external sentinel")


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
                self.assertEqual(self.finish(host=host, until="pages")["status"], "ok")
                self.assertEqual(load_json(self.root / FINDINGS), {"confidence-composite": []})

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


class StrictFindingsTests(TerminalFixture):
    """A strict confidence shortfall goes to plan review as findings; it never stops planning (ADR 0013)."""

    CRITERIA = ("\n- Task understanding: 0.95\n- Approach clarity: 0.70\n- Requirements alignment: 0.92\n"
                "- Risk assessment: 0.91\n- Completeness: 0.80\n")

    def strict(self, emit: str = "📊 Confidence: 0.50") -> None:
        self.rewrite_workflow(("| Mode | advisory |", "| Mode | strict |"), ("📊 Confidence: 0.94", emit),
                              commit="strict shortfall")

    def findings(self) -> dict:
        return load_json(self.root / FINDINGS)

    def test_a_strict_shortfall_publishes_the_draft_pr_and_records_a_finding_on_both_hosts(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.setUp()
                self.strict()
                result = self.finish(host=host, execution_mode="headless")
                self.assertEqual(result["status"], "ok", result)
                self.assertEqual((result["data"]["outcome"], result["data"]["stop_label"]), ("completed", LABEL))
                self.assertEqual(len(self.cli.calls("create")), 1)
                self.assertEqual(self.findings(), {"confidence-composite": []})
                boundary = self.git("log", "--format=%H", "--grep", "close the plan stage boundary", "-1")
                self.assertIn(FINDINGS, self.git("show", "--name-only", "--format=", boundary).splitlines())
                self.assertEqual(self.git("status", "--porcelain"), "")

    def test_each_criterion_below_threshold_is_its_own_finding(self) -> None:
        self.strict("📊 Confidence: 0.86" + self.CRITERIA)
        self.assertEqual(self.finish(until="pages")["status"], "ok")
        self.assertEqual(self.findings(), {"confidence-approach_clarity": [], "confidence-completeness": []})

    def test_a_rerun_keeps_recorded_findings_and_their_requests(self) -> None:
        self.strict("📊 Confidence: 0.86" + self.CRITERIA)
        recorded = {"confidence-completeness": ["List every artifact"], "USER-1": ["Name the owner"]}
        (self.root / FINDINGS).write_text(json.dumps(recorded), encoding="utf-8")
        self.assertEqual(self.finish(until="pages")["status"], "ok")
        self.assertEqual(self.findings(), {**recorded, "confidence-approach_clarity": []})

    def test_a_passing_gate_records_a_clean_inventory_and_never_adds_a_finding(self) -> None:
        self.assertEqual(self.finish(until="pages")["status"], "ok")
        self.assertEqual(self.findings(), {})
        recorded = {"confidence-composite": ["Raise the plan's confidence"]}
        (self.root / FINDINGS).write_text(json.dumps(recorded), encoding="utf-8")
        self.assertEqual(self.finish(until="pages")["status"], "ok")
        self.assertEqual(self.findings(), recorded)

    def test_a_dry_run_records_no_finding(self) -> None:
        self.strict()
        self.assertEqual(self.finish("dry_run")["status"], "ok")
        self.assertFalse((self.root / FINDINGS).exists())

    def test_an_unreadable_inventory_stops_before_any_page(self) -> None:
        self.strict()
        (self.root / FINDINGS).write_text("[]", encoding="utf-8")
        self.assertNotEqual(self.finish(until="pages")["status"], "ok")
        self.assertFalse((self.root / FEATURE / "artifacts").exists())


class GuardTests(TerminalFixture):
    def test_a_legacy_blocked_gate_row_stops_before_generation_and_writes_nothing(self) -> None:
        self.rewrite_workflow(("| Confidence Gate | G6.5 | ✅ Complete", "| Confidence Gate | G6.5 | ⚠️ Blocked"), commit="blocked")
        result = self.finish(execution_mode="headless")
        self.assertEqual(result["data"]["stop_label"], LABEL)
        self.assertIn("must finish", result["data"]["report"])
        self.assertFalse((self.root / FEATURE / "artifacts").exists())
        self.assertFalse((self.root / FINDINGS).exists())
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
                self.assertFalse((self.root / FINDINGS).exists())

    def test_a_completed_advisory_warning_allows_pages(self) -> None:
        self.rewrite_workflow(("📊 Confidence: 0.94", "📊 Confidence: 0.50"))
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


class TerminalGuidanceTests(unittest.TestCase):
    """The parent's terminal step costs one response per poll and per reference read (issue 1317)."""

    def test_each_host_prints_the_helper_report_and_codex_waits_in_one_long_poll(self) -> None:
        # Bind the complete reviewed document bytes, including Markdown context.
        # A section/phrase search can select a hidden copy or miss a negation.
        # Changes require reviewing the rendered instructions before re-pinning.
        reviewed = {
            "claude": "c0b7ea167dc7c68a4a3377f5c7ac67cfd8c2f0858d51b2423f8fda72a6abc7cf",
            "codex": "9d50e87f55c58f7aac2989c189593206d3d28aa24f133106c1cea3998ef5abae",
        }
        for host, digest in reviewed.items():
            path = host_skill_views.host_skill_root(host) / "speckit-autopilot/references/phase-execution.md"
            with self.subTest(host=host):
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest,
                                 "Review the complete rendered terminal instructions before updating this host's digest")


@contextmanager
def mutated_terminal_guidance(host: str, mutate):
    """Stage one mutation in a disposable rendered host tree for the real gate."""
    relative = "speckit-autopilot/references/phase-execution.md"
    roots = {name: host_skill_views.host_skill_root(name) for name in ("claude", "codex")}
    original = (roots[host] / relative).read_text(encoding="utf-8")
    changed = mutate(original)
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / relative
        path.parent.mkdir(parents=True)
        path.write_text(changed, encoding="utf-8")
        roots[host] = Path(temporary)
        with unittest.mock.patch.object(host_skill_views, "host_skill_root", side_effect=roots.__getitem__):
            yield original, changed


class TerminalGuidanceGateMutationTests(unittest.TestCase):
    """Mutate the rendered file, then exercise the real guidance gate."""

    def assert_guidance_rejected(self, host: str, mutate) -> None:
        with mutated_terminal_guidance(host, mutate) as (original, changed):
            self.assertNotEqual(changed, original, "mutation must reach the rendered guidance")
            gate = TerminalGuidanceTests("test_each_host_prints_the_helper_report_and_codex_waits_in_one_long_poll")
            with self.assertRaises(AssertionError):
                gate.test_each_host_prints_the_helper_report_and_codex_waits_in_one_long_poll()

    def assert_inert_report_rejected(self, host: str) -> None:
        clause = "For `outcome: completed`, the answer's `report` is the whole stop report: print it unchanged, then its `stop_label`."
        hidden = f"<!-- {clause} -->"
        self.assert_guidance_rejected(host, lambda text: text.replace(clause, hidden))
        self.assert_guidance_rejected(host, lambda text: text.replace(clause, hidden + " Rewrite the completed report."))

    def test_claude_rejects_inert_completed_report(self) -> None:
        self.assert_inert_report_rejected("claude")

    def test_codex_rejects_inert_completed_report(self) -> None:
        self.assert_inert_report_rejected("codex")

    def test_each_host_rejects_missing_or_changed_final_stop_label(self) -> None:
        for host, replacement in itertools.product(("claude", "codex"), ("", "then print a different marker")):
            with self.subTest(host=host, replacement=replacement):
                self.assert_guidance_rejected(host, lambda text: text.replace("then its `stop_label`", replacement))

    def test_codex_rejects_inert_long_poll_instructions(self) -> None:
        pattern = r"\*\*Wait on the finishing call in one poll\.\*\*.*?while the helper still runs\."
        for replacement in ("Poll every second with `write_stdin` and `yield_time_ms: 1000`.", ""):
            with self.subTest(replacement=replacement):
                self.assert_guidance_rejected("codex", lambda text: re.sub(
                    pattern, lambda match: f"<!-- {match[0]} --> {replacement}", text, flags=re.DOTALL))

    def test_each_host_rejects_shadow_sections_and_other_inert_wrappers(self) -> None:
        start = "#### Draft-PR emission: the terminal-step sequence"
        end = "#### The `artifact-author` dispatch"
        for host, wrapper in itertools.product(("claude", "codex"), ("<!--\n{}\n-->", "```text\n{}\n```", "> {}", "<template>{}</template>")):
            with self.subTest(host=host, wrapper=wrapper):
                def shadow(text: str) -> str:
                    first, last = text.index(start), text.index(end, text.index(start))
                    section = text[first:last]
                    return text[:first] + wrapper.format(section + end) + "\n6. Skip the report and stop.\n" + text[last:]
                self.assert_guidance_rejected(host, shadow)

    def test_each_host_rejects_other_terminal_fields_and_instruction_links(self) -> None:
        replacements = (
            ("print it unchanged", "rewrite it"),
            ("`outcome: completed`", "`outcome: stopped`"),
            ("`report` is the whole stop report", "`summary` is the whole stop report"),
            ("as the last line of your final message", "before another final line"),
            ("6. Print the stop report", "6. [Print the stop report](https://example.invalid/skip)"),
            ("#### Draft-PR emission: the terminal-step sequence", "#### Archived terminal-step sequence"),
        )
        for host, (old, new) in itertools.product(("claude", "codex"), replacements):
            with self.subTest(host=host, old=old):
                self.assert_guidance_rejected(host, lambda text: text.replace(old, new))

    def test_codex_rejects_each_poll_field_change(self) -> None:
        for old, new in (("yield_time_ms: 30000", "yield_time_ms: 1000"),
                         ("yield_time_ms: 300000", "yield_time_ms: 1000"),
                         ("`write_stdin`", "`exec_command`"),
                         ("with empty `chars`", "with nonempty `chars`"),
                         ("that `session_id`", "a different `session_id`"),
                         ("no integer `exit_code`", "an integer `exit_code`")):
            with self.subTest(old=old):
                self.assert_guidance_rejected("codex", lambda text: text.replace(old, new))


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
