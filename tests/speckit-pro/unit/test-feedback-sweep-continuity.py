#!/usr/bin/env python3
"""The feedback sweep keeps running through amendments and GitHub errors.

Runner contracts (row repair, GitHub retry, capture reasons) and the guidance
each host loads. The stop policy is the spec: a stop names a reason from
``stop_policy.STOP_REASONS``, and agents resolve every other condition.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for import_root in (PLUGIN_ROOT, LIB_DIR):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from host_skill_views import host_skill_root  # noqa: E402
from speckit_pro_runner import sweep_isolation, sweep_launcher  # noqa: E402
from speckit_pro_runner.helpers import read_only  # noqa: E402
from speckit_pro_runner.stop_policy import STOP_REASONS  # noqa: E402
from test_result import run_counted  # noqa: E402

HOSTS = ("claude", "codex")
ROW = {"number": 7, "url": "https://github.example/pr/7"}
SAME = {"number": 7, "url": ROW["url"], "state": "OPEN"}
OTHER = {"number": 8, "url": "https://github.example/pr/8", "state": "open"}
ATTEMPTS = len(sweep_isolation.GH_RETRY_DELAYS) + 1
TIMED_OUT = "Command '['gh', 'api', 'user']' timed out after 60 seconds"


def observe(*entries: dict) -> dict:
    return {"ok": True, "pull_requests": list(entries)}


def probed(exit_status: int | None, stdout: str = "", stderr: str = "") -> dict:
    """One `cli_probe.probe` record, as the real probe shapes it."""
    return {"argv": [], "exit_status": exit_status, "stdout_tail": stdout, "stderr_tail": stderr}


def guidance() -> list[tuple[str, str, str]]:
    """(host, phase reference, SKILL.md) as each host loads them, whitespace collapsed."""
    views = []
    for host in HOSTS:
        root = host_skill_root(host) / "speckit-autopilot"
        phase = (root / "references/phase-execution.md").read_text(encoding="utf-8")
        skill = (root / "SKILL.md").read_text(encoding="utf-8")
        views.append((host, " ".join(phase.split()), " ".join(skill.split())))
    return views


class DraftPrRowRepairTests(unittest.TestCase):
    """Exactly one open pull request on the branch names the row's repair."""

    def corroborate(self, *entries: dict) -> dict:
        return read_only.corroborate_draft_pr(ROW, observe(*entries))

    def test_a_sole_open_pull_request_is_the_repair(self) -> None:
        moved = {**SAME, "url": "https://moved.example/pr/7"}
        cases = (
            ("another number", (OTHER,), {"number": 8, "url": OTHER["url"]}),
            ("closed row, open replacement", ({**SAME, "state": "closed"}, OTHER),
             {"number": 8, "url": OTHER["url"]}),
            ("moved url", (moved,), {"number": 7, "url": moved["url"]}),
        )
        for label, entries, expected in cases:
            with self.subTest(case=label):
                record = self.corroborate(*entries)
                self.assertEqual(record["status"], "identity_mismatch")
                self.assertEqual(record["repair"], expected)

    def test_two_open_pull_requests_are_ambiguous_and_never_repaired(self) -> None:
        for order in ((SAME, OTHER), (OTHER, SAME)):
            with self.subTest(order=[entry["number"] for entry in order]):
                record = self.corroborate(*order)
                self.assertEqual(record["status"], "identity_mismatch")
                self.assertIsNone(record["repair"])

    def test_no_other_status_carries_a_repair(self) -> None:
        cases = (
            ("no_record", None, None),
            ("skipped", ROW, None),
            ("pr_missing", ROW, observe()),
            ("pr_closed", ROW, observe({**SAME, "state": "closed"})),
            ("pr_closed", ROW, observe({**SAME, "state": "merged"})),
            ("match", ROW, observe(SAME)),
        )
        for status, recorded, observation in cases:
            with self.subTest(status=status, observation=str(observation)[:40]):
                record = read_only.corroborate_draft_pr(recorded, observation)
                self.assertEqual(record["status"], status)
                self.assertIsNone(record["repair"])

    def test_the_record_carries_one_more_key_and_never_drops_one(self) -> None:
        self.assertEqual(
            list(self.corroborate(SAME)),
            ["status", "recorded", "observed", "merged", "reason", "repair"],
        )


class ScriptedGh(unittest.TestCase):
    """Runs `_run_gh_json` against scripted `gh` probe results."""

    def run_gh(self, script: list[dict], *, installed: bool = True):
        """Returns (result, violation, gh argvs run, backoff sleeps)."""
        calls: list[list[str]] = []
        sleeps: list[float] = []
        steps = list(script)

        def fake_run(root, argv, **kwargs):
            calls.append(list(argv))
            return steps.pop(0)

        which = "/usr/bin/gh" if installed else None
        with patch.object(sweep_isolation.shutil, "which", return_value=which), patch.object(
            sweep_isolation, "probe", side_effect=fake_run
        ), patch.object(sweep_isolation, "_sleep", side_effect=sleeps.append):
            try:
                return sweep_isolation._run_gh_json(["user"], REPO_ROOT), None, calls, sleeps
            except sweep_isolation.CaptureViolation as violation:
                return None, violation, calls, sleeps

    def assert_violation(self, violation, reason: str, message: str) -> None:
        self.assertIsNotNone(violation)
        self.assertEqual((violation.reason, str(violation)), (reason, message))


class GitHubRetryTests(ScriptedGh):
    """A rate limit, a timeout, a server error, or a parse failure retries with backoff."""

    def test_a_rate_limit_backs_off_then_succeeds(self) -> None:
        limited = probed(1, stderr="gh: API rate limit exceeded for user (HTTP 403)")
        result, violation, calls, sleeps = self.run_gh([limited, limited, probed(0, '{"login":"me"}')])
        self.assertIsNone(violation)
        self.assertEqual(result, {"login": "me"})
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleeps, list(sweep_isolation.GH_RETRY_DELAYS[:2]))
        self.assertLess(sleeps[0], sleeps[1])

    def test_other_transient_failures_also_retry(self) -> None:
        transient = {
            "secondary rate limit": probed(1, stderr="secondary rate limit (HTTP 403)"),
            "429": probed(1, stderr="HTTP 429: Too Many Requests"),
            "server error": probed(1, stderr="HTTP 502: Bad Gateway"),
            "timeout": probed(None, stderr=TIMED_OUT),
            "unparseable output": probed(0, "<html>"),
        }
        for label, first in transient.items():
            with self.subTest(failure=label):
                _, violation, calls, sleeps = self.run_gh([first, probed(0, "{}")])
                self.assertIsNone(violation)
                self.assertEqual((len(calls), sleeps), (2, [sweep_isolation.GH_RETRY_DELAYS[0]]))

    def test_a_spent_schedule_reports_the_closed_reason_of_the_last_failure(self) -> None:
        cases = (
            ("rate_limited", "GitHub rate limit persisted after retries",
             probed(1, stderr="API rate limit exceeded")),
            ("malformed_output", "GitHub observation returned malformed JSON", probed(0, "nope")),
            ("observation_failed", "GitHub observation failed", probed(1, stderr="HTTP 500")),
        )
        for reason, message, failure in cases:
            with self.subTest(reason=reason):
                _, violation, calls, sleeps = self.run_gh([failure] * ATTEMPTS)
                self.assert_violation(violation, reason, message)
                self.assertEqual((len(calls), sleeps), (ATTEMPTS, list(sweep_isolation.GH_RETRY_DELAYS)))
                self.assertNotIn(["gh", "auth", "status"], calls)


class GitHubStopTests(ScriptedGh):
    """Only an absent tool or absent authentication stops at once."""

    def test_an_absent_tool_stops_at_once_without_retry(self) -> None:
        _, violation, calls, sleeps = self.run_gh([], installed=False)
        self.assert_violation(violation, "gh_unavailable", "GitHub CLI is unavailable")
        self.assertEqual((calls, sleeps), ([], []))

    def test_an_unclassified_failure_asks_auth_status_and_never_retries(self) -> None:
        marker = "reviewer-controlled-marker"
        cases = (
            ("gh_not_authenticated", "GitHub CLI is not authenticated",
             probed(1, stderr="You are not logged into any GitHub hosts")),
            ("observation_failed", "GitHub observation failed", probed(0, stdout="Logged in")),
        )
        for reason, message, auth_status in cases:
            with self.subTest(reason=reason):
                _, violation, calls, sleeps = self.run_gh([probed(1, stderr=f"HTTP 404 {marker}"), auth_status])
                self.assert_violation(violation, reason, message)
                self.assertEqual((calls[1], sleeps), (["gh", "auth", "status"], []))
                self.assertNotIn(marker, str(violation))


class CaptureReasonTests(unittest.TestCase):
    """The capture surface tells the orchestrator which failure it hit."""

    def capture(self, violation: BaseException) -> tuple[dict, int]:
        inputs = {
            "named_surface": "capture",
            "surface": "claude",
            "repository": "owner/repo",
            "pr_number": 7,
            "workflow_file": "workflow.md",
        }
        with patch.object(sweep_launcher, "verify_claude_boundary"), patch.object(
            sweep_isolation, "capture_github_session", side_effect=violation
        ):
            result = read_only.sweep_isolation_session(inputs, REPO_ROOT)
        return json.loads(result["stdout"]), result["exit_code"]

    def test_each_capture_failure_reports_its_own_closed_reason(self) -> None:
        for violation in (
            sweep_isolation.GitHubUnavailable("x"),
            sweep_isolation.GitHubUnauthenticated("x"),
            sweep_isolation.GitHubRateLimited("x"),
            sweep_isolation.GitHubMalformedOutput("x"),
            sweep_isolation.CaptureViolation("x"),
        ):
            with self.subTest(reason=violation.reason):
                self.assertEqual(self.capture(violation), ({"status": "blocked", "reason": violation.reason}, 3))

    def test_a_boundary_failure_keeps_the_isolation_reason(self) -> None:
        payload, code = self.capture(sweep_isolation.IsolationViolation("boundary"))
        self.assertEqual((payload["reason"], code), ("isolation_boundary_unavailable", 3))

    def test_the_closed_reason_set_is_what_the_guidance_branches_on(self) -> None:
        self.assertEqual(
            set(sweep_isolation.CAPTURE_REASONS),
            {"gh_unavailable", "gh_not_authenticated", "rate_limited", "malformed_output", "observation_failed"},
        )
        for host, phase, _ in guidance():
            for reason in sweep_isolation.CAPTURE_REASONS:
                with self.subTest(host=host, reason=reason):
                    self.assertTrue(f"`{reason}`" in phase, f"{host} lacks `{reason}`")


_DELAYS = sweep_isolation.GH_RETRY_DELAYS
_SCHEDULE = ", ".join(f"{delay:g}" for delay in _DELAYS[:-1]) + f", and {_DELAYS[-1]:g} seconds"

# What each host must say (phase reference, SKILL.md) and must no longer say.
GUIDANCE_PINS = {
    "an amendment regenerates in a fresh worker and never stops for review": {
        "phase": (
            "Regenerate after an amendment in a fresh isolated worker; do not stop for re-review.",
            "receives only committed bytes",
            "their committed diff is the only amendment text it can see",
            "List every amended comment in the final report",
            "Keep the isolation-unavailable stop",
            "`stop_reason:integrity_failure`",
            "Invalidate the private sweep session",
        ),
        "absent": (
            "Stop for human re-review",
            "stops for human re-review",
            "stop for re-review before any task work",
            "Confirm this run made no amendment",
            "This sequence is unreachable in a run that made an amendment",
        ),
    },
    "rate limits and parse failures retry and only absence stops": {
        "phase": (
            "Retry before a `skipped` stands, and let the cause decide.",
            _SCHEDULE,
            "`gh auth status`",
            "`stop_reason:tool_unavailable`",
            "do not stop",
        ),
        "skill": (_SCHEDULE, "`gh auth status`"),
        "absent": ("Behaviour does not branch on", "| `skipped` | stop |"),
    },
    "a sole open pull request repairs the row and a closed one stays human": {
        "phase": (
            "Repair the row when exactly one open pull request answers for the branch.",
            "`corroboration.repair`",
            "`stop_reason:reopen_closed_pr`",
            "`stop_reason:ambiguous_pr_record`",
            "Reopening a closed pull request stays a human call",
        ),
        "skill": ("`corroboration.repair`", "the run at this step", "the Phase 7 corroboration gate"),
        "absent": (
            "| `identity_mismatch` | stop |",
            "| `pr_missing` | stop |",
            "never stops the run. It is computed",
        ),
    },
}


class HostGuidanceTests(unittest.TestCase):
    """Both hosts load the same behaviours."""

    def test_every_pin_holds_on_both_hosts(self) -> None:
        for name, pin in GUIDANCE_PINS.items():
            for host, phase_text, skill_text in guidance():
                with self.subTest(pin=name, host=host):
                    for snippet in pin.get("phase", ()):
                        self.assertTrue(snippet in phase_text, f"{host} phase lacks: {snippet}")
                    for snippet in pin.get("skill", ()):
                        self.assertTrue(snippet in skill_text, f"{host} SKILL.md lacks: {snippet}")
                    for snippet in pin.get("absent", ()):
                        self.assertFalse(snippet in phase_text + " " + skill_text, f"{host} still says: {snippet}")

    def test_every_marker_the_change_names_is_in_the_closed_stop_set(self) -> None:
        marker = re.compile(r"`stop_reason:([a-z0-9_]+)`")
        for host, phase, skill in guidance():
            with self.subTest(host=host):
                named = set(marker.findall(phase)) | set(marker.findall(skill))
                self.assertLessEqual(
                    {"integrity_failure", "tool_unavailable", "ambiguous_pr_record", "reopen_closed_pr"}, named
                )
                self.assertLessEqual(named, set(STOP_REASONS))
        for reason in ("tool_unavailable", "ambiguous_pr_record"):
            self.assertEqual(STOP_REASONS[reason], "authority")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-feedback-sweep-continuity"))
