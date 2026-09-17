#!/usr/bin/env python3
"""Bounded scheduling tests for provider-native evaluation work."""
from __future__ import annotations

from pathlib import Path
import sys
import threading
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from test_result import run_counted  # noqa: E402
from native_eval_pool import Job, Outcome, run_jobs  # noqa: E402


def job(job_id: str, host: str = "claude", resource_class: str = "ordinary", kind: str = "subject") -> Job:
    return Job(job_id, host, resource_class, kind, {"layer": job_id})


class NativeEvalPoolTests(unittest.TestCase):
    def test_global_host_bound_applies_to_jobs_from_multiple_layers(self) -> None:
        started = threading.Event()
        release = threading.Event()
        lock = threading.Lock()
        active = 0
        peak = 0

        def execute(item: Job) -> Outcome:
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
                if active == 2:
                    started.set()
            release.wait(2)
            with lock:
                active -= 1
            return Outcome(item.id, "pass")

        result_box: list[object] = []
        thread = threading.Thread(target=lambda: result_box.append(run_jobs(
            [job("layer1.a"), job("layer2.a"), job("layer3.a")], execute,
            limits={"claude": 2, "codex": 1},
        )))
        thread.start()
        self.assertTrue(started.wait(1))
        release.set()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        report = result_box[0]
        self.assertEqual(peak, 2)
        self.assertEqual(report.peak_concurrency["claude"], 2)
        self.assertEqual(set(report.outcomes), {"layer1.a", "layer2.a", "layer3.a"})
        self.assertEqual(set(report.durations), set(report.outcomes))
        self.assertEqual(set(report.queue_delays), set(report.outcomes))

    def test_judge_uses_the_same_codex_capacity_and_is_not_run_inside_subject(self) -> None:
        judge_started = threading.Event()
        release_judge = threading.Event()
        codex_active = 0
        peak = 0
        lock = threading.Lock()

        def execute(item: Job) -> Outcome:
            nonlocal codex_active, peak
            if item.host == "claude":
                return Outcome(item.id, "needs_judge", followup=job("judge.one", "codex", kind="judge"))
            with lock:
                codex_active += 1
                peak = max(peak, codex_active)
            judge_started.set()
            release_judge.wait(2)
            with lock:
                codex_active -= 1
            return Outcome(item.id, "pass")

        result_box: list[object] = []
        runner = threading.Thread(target=lambda: result_box.append(run_jobs(
            [job("subject", "claude"), job("codex.subject", "codex")], execute,
            limits={"claude": 1, "codex": 1},
        )))
        runner.start()
        self.assertTrue(judge_started.wait(1))
        release_judge.set()
        runner.join(2)
        self.assertFalse(runner.is_alive())
        report = result_box[0]
        self.assertEqual(peak, 1)
        self.assertEqual(report.peak_concurrency["codex"], 1)
        self.assertEqual(set(report.outcomes), {"subject", "codex.subject", "judge.one"})

    def test_failure_is_not_retried_and_callback_exception_is_invalid(self) -> None:
        calls: list[str] = []

        def execute(item: Job) -> Outcome:
            calls.append(item.id)
            if item.id == "error":
                raise RuntimeError("transport down")
            return Outcome(item.id, "fail")

        report = run_jobs([job("failed"), job("error")], execute)
        self.assertEqual(calls.count("failed"), 1)
        self.assertEqual(calls.count("error"), 1)
        self.assertEqual(report.outcomes["failed"].status, "fail")
        self.assertEqual(report.outcomes["error"].status, "invalid")
        self.assertEqual(report.outcomes["error"].details["exception_type"], "RuntimeError")

    def test_provider_stop_holds_its_queue_while_other_provider_completes(self) -> None:
        called: list[str] = []

        def execute(item: Job) -> Outcome:
            called.append(item.id)
            if item.id == "claude.first":
                return Outcome(item.id, "invalid", stop_provider="claude")
            return Outcome(item.id, "pass")

        report = run_jobs(
            [job("claude.first"), job("claude.later"), job("codex.one", "codex")],
            execute, limits={"claude": 1, "codex": 1},
        )
        self.assertEqual(set(called), {"claude.first", "codex.one"})
        self.assertEqual([item.id for item in report.held_jobs], ["claude.later"])
        self.assertEqual(report.remaining_jobs, ())
        self.assertIn("codex.one", report.outcomes)

    def test_stop_event_prevents_new_launches_but_drains_running_work(self) -> None:
        started = threading.Event()
        release = threading.Event()
        stop = threading.Event()
        calls: list[str] = []

        def execute(item: Job) -> Outcome:
            calls.append(item.id)
            started.set()
            release.wait(2)
            return Outcome(item.id, "pass")

        result_box: list[object] = []
        runner = threading.Thread(target=lambda: result_box.append(run_jobs(
            [job("running"), job("waiting")], execute,
            limits={"claude": 1, "codex": 1}, stop_event=stop,
        )))
        runner.start()
        self.assertTrue(started.wait(1))
        stop.set()
        release.set()
        runner.join(2)
        report = result_box[0]
        self.assertEqual(calls, ["running"])
        self.assertEqual([item.id for item in report.remaining_jobs], ["waiting"])

    def test_duplicate_followup_is_invalid_and_never_executes(self) -> None:
        calls: list[str] = []

        def execute(item: Job) -> Outcome:
            calls.append(item.id)
            return Outcome(item.id, "needs_judge", followup=job("taken", "codex", kind="judge"))

        report = run_jobs([job("taken", "codex"), job("source")], execute)
        self.assertEqual(calls.count("taken"), 1)
        self.assertEqual(calls.count("source"), 1)
        self.assertEqual(report.outcomes["source"].status, "invalid")
        self.assertNotIn("taken", [item.id for item in report.remaining_jobs])

    def test_judges_are_codex_only_and_cannot_spawn_more_judges(self) -> None:
        called = False

        def execute(item: Job) -> Outcome:
            nonlocal called
            called = True
            return Outcome(item.id, "pass")

        with self.assertRaises(ValueError):
            run_jobs([job("claude.judge", "claude", kind="judge")], execute)
        self.assertFalse(called)

        report = run_jobs(
            [job("judge.one", "codex", kind="judge")],
            lambda item: Outcome(item.id, "needs_judge", followup=job("judge.two", "codex", kind="judge")),
        )
        self.assertEqual(report.outcomes["judge.one"].status, "invalid")
        self.assertEqual(report.outcomes["judge.one"].details["reason"], "judge_followup_forbidden")
        self.assertNotIn("judge.two", report.outcomes)

    def test_subject_needing_judge_without_followup_is_invalid(self) -> None:
        report = run_jobs([job("subject")], lambda item: Outcome(item.id, "needs_judge"))
        self.assertEqual(report.outcomes["subject"].status, "invalid")
        self.assertEqual(report.outcomes["subject"].details["reason"], "missing_judge_followup")

    def test_nested_limit_selects_ordinary_work_without_blocking_an_ordinary_slot(self) -> None:
        nested_started = threading.Event()
        ordinary_started = threading.Event()
        release = threading.Event()
        lock = threading.Lock()
        nested_active = 0
        nested_peak = 0

        def execute(item: Job) -> Outcome:
            nonlocal nested_active, nested_peak
            if item.resource_class == "nested":
                with lock:
                    nested_active += 1
                    nested_peak = max(nested_peak, nested_active)
            (nested_started if item.resource_class == "nested" else ordinary_started).set()
            release.wait(2)
            if item.resource_class == "nested":
                with lock:
                    nested_active -= 1
            return Outcome(item.id, "pass")

        result_box: list[object] = []
        runner = threading.Thread(target=lambda: result_box.append(run_jobs(
            [job("nested.one", resource_class="nested"), job("nested.two", resource_class="nested"), job("ordinary")],
            execute, limits={"claude": 2, "codex": 1}, nested_limits={"claude": 1, "codex": 1},
        )))
        runner.start()
        self.assertTrue(nested_started.wait(1))
        self.assertTrue(ordinary_started.wait(1))
        release.set()
        runner.join(2)
        self.assertFalse(runner.is_alive())
        self.assertEqual(result_box[0].peak_concurrency["claude"], 2)
        self.assertEqual(nested_peak, 1)

    def test_judge_queued_after_codex_stop_is_held_not_discarded(self) -> None:
        stopped = threading.Event()
        release_subject = threading.Event()

        def execute(item: Job) -> Outcome:
            if item.id == "codex.stop":
                stopped.set()
                return Outcome(item.id, "invalid", stop_provider="codex")
            self.assertTrue(stopped.wait(1))
            release_subject.wait(2)
            return Outcome(item.id, "needs_judge", followup=job("judge.held", "codex", kind="judge"))

        result_box: list[object] = []
        runner = threading.Thread(target=lambda: result_box.append(run_jobs(
            [job("codex.stop", "codex"), job("claude.subject")], execute,
            limits={"claude": 1, "codex": 1},
        )))
        runner.start()
        self.assertTrue(stopped.wait(1))
        release_subject.set()
        runner.join(2)
        report = result_box[0]
        self.assertNotIn("judge.held", report.outcomes)
        self.assertEqual([item.id for item in report.held_jobs], ["judge.held"])

    def test_rejects_empty_duplicate_and_malformed_inputs_before_execution(self) -> None:
        called = False

        def execute(item: Job) -> Outcome:
            nonlocal called
            called = True
            return Outcome(item.id, "pass")

        invalid_calls = (
            lambda: run_jobs([], execute),
            lambda: run_jobs([job("same"), job("same")], execute),
            lambda: run_jobs([job("bad", "other")], execute),
            lambda: run_jobs([job("bad", resource_class="other")], execute),
            lambda: run_jobs([job("bad", kind="other")], execute),
            lambda: run_jobs([job("one")], execute, limits={"claude": 9, "codex": 1}),
            lambda: run_jobs([job("one")], execute, limits={"claude": 1, "codex": 0}),
            lambda: run_jobs([job("one")], execute, limits={}),
            lambda: run_jobs([job("one")], execute, nested_limits={}),
            lambda: run_jobs([job("one")], execute, limits={"claude": 1, "codex": 1}, nested_limits={"claude": 2, "codex": 1}),
            lambda: run_jobs([job("one")], execute, nested_limits={"claude": 3, "codex": 1}),
        )
        for invocation in invalid_calls:
            with self.subTest(invocation=invocation), self.assertRaises(ValueError):
                invocation()
        self.assertFalse(called)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-native-eval-pool"))
