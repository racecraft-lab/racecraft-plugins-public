#!/usr/bin/env python3
"""The runner owns the plan stage's terminal sequence (ADR 0026): pages, packet, draft PR, record, stop label."""

from __future__ import annotations

import json
import os
import re
import shutil
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
from speckit_pro_runner import envelope, stop_policy  # noqa: E402
from speckit_pro_runner.helpers import plan_stage_terminal, registry  # noqa: E402

SOURCE = ROOT / "tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source"
FEATURE = "specs/art-007-draft-pr-emission"
WORKFLOW = "docs/ai/specs/ART-007-workflow.md"
STATE = "docs/ai/specs/autopilot-state.json"
PLANNING = {"plan_file": f"{FEATURE}/plan.md", "spec_file": f"{FEATURE}/spec.md", "tasks_file": f"{FEATURE}/tasks.md"}
CONCEPT = "docs/ai/specs/.process/ART-007-design-concept.md"
URL = "https://github.com/example/repo/pull/7"
LABEL = "stop_reason:plan_stage_boundary"


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
        base = Path(temporary.name)
        self.root, remote = base / "work", base / "remote.git"
        (self.root / FEATURE).mkdir(parents=True)
        (self.root / ".specify").mkdir()
        (self.root / "docs/ai/specs").mkdir(parents=True)
        for name in ("spec.md", "plan.md", "tasks.md", "research.md"):
            shutil.copy(SOURCE / name, self.root / FEATURE / name)
        (self.root / CONCEPT).parent.mkdir(parents=True)
        shutil.copy(SOURCE / "design-concept.md", self.root / CONCEPT)
        shutil.copy(SOURCE / "workflow.md", self.root / WORKFLOW)
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


class RerunTests(TerminalFixture):
    def test_a_rerun_after_success_refreshes_the_recorded_pull_request_and_adds_no_commit(self) -> None:
        self.finish(execution_mode="headless")
        commits = self.subjects()
        self.cli.listing = [{"number": 7, "url": URL, "state": "OPEN", "title": "feat(art-007): plan Draft-PR Emission"}]
        data = self.finish(execution_mode="headless")["data"]
        self.assertEqual((data["pull_request"]["number"], len(self.cli.calls("create")), self.subjects()), (7, 1, commits))
        self.assertNotIn("--title", self.cli.calls("edit")[0])

    def test_a_page_with_active_content_stops_before_any_commit(self) -> None:
        data = self.finish(until="pages")["data"]
        page = self.root / FEATURE / "artifacts" / f"{data['pages']['generated'][0]}.html"
        text = page.read_text(encoding="utf-8")
        page.write_text(re.sub(r"(<!-- FILL:[a-z0-9-]+:START -->)", r"\1<script>alert(1)</script>", text, count=1), encoding="utf-8")
        result = self.finish(execution_mode="headless")
        self.assertEqual(result["data"]["stop_label"], "stop_reason:integrity_failure")
        self.assertEqual((self.subjects(), self.cli.gh), ([], []))


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


class GuardTests(TerminalFixture):
    def test_a_blocked_gate_stops_before_generation_and_writes_nothing(self) -> None:
        path = self.root / WORKFLOW
        path.write_text(path.read_text(encoding="utf-8").replace("| Confidence Gate | G6.5 | ⏳ Pending", "| Confidence Gate | G6.5 | ⚠️ Blocked"),
                        encoding="utf-8")
        self.git("commit", "-q", "-am", "blocked")
        result = self.finish(execution_mode="headless")
        self.assertEqual(result["data"]["stop_label"], "stop_reason:strict_confidence_opt_in")
        self.assertFalse((self.root / FEATURE / "artifacts").exists())
        self.assertEqual((self.subjects(), self.cli.gh), (["blocked"], []))

    def test_a_page_that_is_still_its_template_is_deleted_and_reported_as_a_gap(self) -> None:
        artifacts = self.root / FEATURE / "artifacts"
        artifacts.mkdir()
        shutil.copy(ROOT / "speckit-pro/artifact-gallery/templates/implementation-plan.html", artifacts / "implementation-plan.html")
        data = self.finish(execution_mode="headless")["data"]
        self.assertNotIn("implementation-plan", data["pages"]["generated"])
        self.assertEqual([gap["id"] for gap in data["pages"]["gaps"]], ["implementation-plan"])
        self.assertNotIn("implementation-plan", self.pages())
        self.assertEqual(data["outcome"], "completed")


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-plan-stage-terminal"))
