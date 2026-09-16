"""Bounded, provider-scoped scheduling for native evaluation jobs.

The execution callback owns evidence persistence.  This module only decides
when a provider job may launch, so a judge returned by a subject runs later as
another Codex job instead of consuming a worker while waiting for capacity.
"""
from __future__ import annotations

from collections import deque
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
import time
from threading import Event
from typing import Any, Callable, Mapping


_HOSTS = ("claude", "codex")
_RESOURCE_CLASSES = ("ordinary", "nested")
_KINDS = ("subject", "judge")
_STATUSES = ("pass", "fail", "invalid", "needs_judge")
_CLAUDE_RUNNER_MAXIMUM = 8
_CODEX_HARNESS_MAXIMUM = 8


@dataclass(frozen=True)
class Job:
    id: str
    host: str
    resource_class: str
    kind: str
    payload: Any


@dataclass(frozen=True)
class Outcome:
    job_id: str
    status: str
    followup: Job | None = None
    stop_provider: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunReport:
    outcomes: dict[str, Outcome]
    remaining_jobs: tuple[Job, ...]
    held_jobs: tuple[Job, ...]
    durations: dict[str, float]
    queue_delays: dict[str, float]
    peak_concurrency: dict[str, int]


def _validate_job(job: Job) -> None:
    if not isinstance(job, Job):
        raise ValueError("jobs must be Job instances")
    if not isinstance(job.id, str) or not job.id:
        raise ValueError("job id must be a non-empty string")
    if job.host not in _HOSTS:
        raise ValueError(f"unknown provider host: {job.host!r}")
    if job.resource_class not in _RESOURCE_CLASSES:
        raise ValueError(f"unknown resource class: {job.resource_class!r}")
    if job.kind not in _KINDS:
        raise ValueError(f"unknown job kind: {job.kind!r}")
    if job.kind == "judge" and job.host != "codex":
        raise ValueError("judge jobs must use the codex provider")


def _validate_limits(name: str, values: Mapping[str, int], maximums: Mapping[str, int]) -> dict[str, int]:
    if not isinstance(values, Mapping) or set(values) != set(_HOSTS):
        raise ValueError(f"{name} must specify exactly claude and codex")
    checked: dict[str, int] = {}
    for host in _HOSTS:
        value = values[host]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > maximums[host]:
            raise ValueError(f"invalid {name} for {host}: {value!r}")
        checked[host] = value
    return checked


def _invalid(job: Job, reason: str, **details: Any) -> Outcome:
    return Outcome(job.id, "invalid", details={"reason": reason, **details})


def _run_one(execute: Callable[[Job], Outcome], job: Job) -> tuple[Outcome, float]:
    started = time.monotonic()
    try:
        outcome = execute(job)
    except BaseException as exc:  # A provider callback must never trigger an implicit retry.
        return _invalid(job, "callback_exception", exception_type=type(exc).__name__, message=str(exc)), time.monotonic() - started
    if not isinstance(outcome, Outcome):
        return _invalid(job, "callback_returned_non_outcome"), time.monotonic() - started
    return outcome, time.monotonic() - started


def _normalize_outcome(job: Job, outcome: Outcome, known_ids: set[str]) -> Outcome:
    if outcome.job_id != job.id:
        return _invalid(job, "outcome_job_id_mismatch")
    if outcome.status not in _STATUSES:
        return _invalid(job, "unknown_outcome_status")
    if outcome.stop_provider is not None and outcome.stop_provider not in _HOSTS:
        return _invalid(job, "unknown_stop_provider")
    if not isinstance(outcome.details, dict):
        return _invalid(job, "outcome_details_not_dict")
    followup = outcome.followup
    if job.kind == "judge" and followup is not None:
        return _invalid(job, "judge_followup_forbidden")
    if job.kind == "subject" and outcome.status == "needs_judge" and followup is None:
        return _invalid(job, "missing_judge_followup")
    if followup is None:
        return outcome
    try:
        _validate_job(followup)
    except ValueError as exc:
        return _invalid(job, "invalid_followup", message=str(exc))
    if outcome.status != "needs_judge" or followup.host != "codex" or followup.kind != "judge":
        return _invalid(job, "invalid_followup")
    if followup.id in known_ids:
        return _invalid(job, "duplicate_followup_id")
    return outcome


def run_jobs(
    jobs: list[Job] | tuple[Job, ...],
    execute: Callable[[Job], Outcome],
    limits: Mapping[str, int] | None = None,
    nested_limits: Mapping[str, int] | None = None,
    stop_event: Event | None = None,
) -> RunReport:
    """Run jobs under one shared pool per provider and return scheduling facts.

    Claude accepts at most eight concurrent jobs because that is the documented
    runner limit.  The equal Codex cap is a local harness policy, not a provider
    capability claim.
    """
    if not isinstance(jobs, (list, tuple)) or not jobs:
        raise ValueError("jobs must be a non-empty list or tuple")
    if not callable(execute):
        raise ValueError("execute must be callable")
    capacities = _validate_limits(
        "limits", {"claude": 4, "codex": 4} if limits is None else limits,
        {"claude": _CLAUDE_RUNNER_MAXIMUM, "codex": _CODEX_HARNESS_MAXIMUM},
    )
    nested = _validate_limits(
        "nested_limits", {"claude": 1, "codex": 1} if nested_limits is None else nested_limits,
        {host: min(2, capacities[host]) for host in _HOSTS},
    )
    queued: dict[str, deque[Job]] = {host: deque() for host in _HOSTS}
    known_ids: set[str] = set()
    enqueued_at: dict[str, float] = {}
    for job in jobs:
        _validate_job(job)
        if job.id in known_ids:
            raise ValueError(f"duplicate job id: {job.id!r}")
        known_ids.add(job.id)
        queued[job.host].append(job)
        enqueued_at[job.id] = time.monotonic()

    outcomes: dict[str, Outcome] = {}
    durations: dict[str, float] = {}
    queue_delays: dict[str, float] = {}
    active = {host: 0 for host in _HOSTS}
    active_nested = {host: 0 for host in _HOSTS}
    peaks = {host: 0 for host in _HOSTS}
    stopped: set[str] = set()
    futures: dict[Future[tuple[Outcome, float]], tuple[Job, str]] = {}

    def pick_eligible(host: str) -> Job | None:
        for index, candidate in enumerate(queued[host]):
            if candidate.resource_class != "nested" or active_nested[host] < nested[host]:
                del queued[host][index]
                return candidate
        return None

    with ThreadPoolExecutor(max_workers=capacities["claude"]) as claude_pool, ThreadPoolExecutor(
        max_workers=capacities["codex"]
    ) as codex_pool:
        pools = {"claude": claude_pool, "codex": codex_pool}
        while futures or any(queued[host] for host in _HOSTS):
            if stop_event is None or not stop_event.is_set():
                for host in _HOSTS:
                    while host not in stopped and active[host] < capacities[host]:
                        candidate = pick_eligible(host)
                        if candidate is None:
                            break
                        queue_delays[candidate.id] = time.monotonic() - enqueued_at[candidate.id]
                        future = pools[host].submit(_run_one, execute, candidate)
                        futures[future] = (candidate, host)
                        active[host] += 1
                        if candidate.resource_class == "nested":
                            active_nested[host] += 1
                        peaks[host] = max(peaks[host], active[host])
            if not futures:
                break
            done, _ = wait(futures, return_when=FIRST_COMPLETED)
            for future in done:
                job, host = futures.pop(future)
                active[host] -= 1
                if job.resource_class == "nested":
                    active_nested[host] -= 1
                outcome, duration = future.result()
                durations[job.id] = duration
                outcome = _normalize_outcome(job, outcome, known_ids)
                outcomes[job.id] = outcome
                if outcome.stop_provider is not None:
                    stopped.add(outcome.stop_provider)
                if outcome.followup is not None:
                    followup = outcome.followup
                    known_ids.add(followup.id)
                    queued[followup.host].append(followup)
                    enqueued_at[followup.id] = time.monotonic()

    remaining: list[Job] = []
    held: list[Job] = []
    for host in _HOSTS:
        target = held if host in stopped else remaining
        target.extend(queued[host])
    return RunReport(outcomes, tuple(remaining), tuple(held), durations, queue_delays, peaks)
