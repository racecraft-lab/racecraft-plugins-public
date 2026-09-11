"""Versioned, replayable trial records for the two trigger-evaluation hosts."""
from __future__ import annotations

import hashlib
import errno
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import trigger_process as processes

SCHEMA_VERSION = "trigger-trial/v1"
EXECUTION_FIELDS = (
    "provider_exit_code", "timed_out", "interrupted_by_signal", "cleanup_verified",
    "cleanup_error", "cleanup_scope", "unexpected_descendants", "child_pid",
    "child_pgid", "cleanup_observations", "process_error",
)


def case_id(host: str, skill: str, entry: dict[str, object]) -> str:
    value = [host, skill, entry["query"], entry["should_trigger"]]
    digest = hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return f"l2-{digest[:24]}"


def trial_checks(record: dict[str, object]) -> dict[str, bool]:
    """Derive validity from typed observations, never from the aggregate pass flag."""
    observations = record.get("cleanup_observations")
    last_probe = observations[-1] if isinstance(observations, list) and observations else None
    group = record.get("child_pgid")
    model_check = record.get("model_identity_check")
    return {
        "execution_record": record.get("execution_record_complete") is True,
        "process": record.get("process_error") is None,
        "stream": record.get("stream_valid") is True,
        "provider_exit": type(record.get("provider_exit_code")) is int and record["provider_exit_code"] == 0,
        "timeout": record.get("timed_out") is False,
        "interruption": "interrupted_by_signal" in record and record["interrupted_by_signal"] is None,
        "cleanup": record.get("cleanup_verified") is True and record.get("cleanup_error") is None,
        "owned_scope": record.get("cleanup_scope") == "owned-process-group",
        "absence_probe": isinstance(last_probe, dict) and last_probe.get("errno") == errno.ESRCH
        and type(group) is int and group > 0 and group == record.get("child_pid") and last_probe.get("pgid") == group,
        "descendants": record.get("unexpected_descendants") is False,
        "model": isinstance(model_check, str) and model_check in {"exact", "alias", "unavailable-in-exec-json"},
        "selection": type(record.get("selected")) is bool,
    }


def make_trial_record(
    host: str, skill: str, entry: dict[str, object], case_number: int, trial_number: int,
    parsed: dict[str, object], raw: dict[str, object], execution: dict[str, object],
) -> dict[str, object]:
    record = {
        **parsed, **raw,
        **{name: execution.get(name) for name in EXECUTION_FIELDS},
        "schema_version": SCHEMA_VERSION,
        "execution_record_complete": all(name in execution for name in EXECUTION_FIELDS),
        "host": host, "skill": skill, "case_id": case_id(host, skill, entry),
        "case_number": case_number, "trial_number": trial_number,
        "query": entry["query"], "should_trigger": entry["should_trigger"],
        "query_sha256": hashlib.sha256(str(entry["query"]).encode()).hexdigest(),
        "stream_valid": parsed.get("valid") is True,
        "selected": parsed.get("selected") if type(parsed.get("selected")) is bool else None,
        "observation_scope": "claude-skill-tool" if host == "claude" else "codex-marker-proxy",
        # The capability prerequisite is still open; diagnostic validity cannot qualify a matrix.
        "qualification_eligible": False,
    }
    if host == "codex":
        record["model_identity_check"] = "exact" if parsed.get("resolved_model") else "unavailable-in-exec-json"
    checks = trial_checks(record)
    valid = all(checks.values())
    record.update(valid=valid, trial_valid=valid, checks=checks)
    if not valid:
        record["reason"] = f"invalid checks: {', '.join(name for name, passed in checks.items() if not passed)}; {parsed.get('reason', '')}"
    # This alias contains an observed status only, never the helper's timeout sentinel.
    record["exit_code"] = record["provider_exit_code"]
    return record


def write_json_once(path: Path, value: object) -> str:
    payload = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(payload)
    return hashlib.sha256(payload).hexdigest()


def retain_trial_record(directory: Path, record: dict[str, object]) -> dict[str, object]:
    path = directory / f"case-{record['case_number']:03d}-trial-{record['trial_number']:02d}.trial.json"
    digest = write_json_once(path, record)
    return {**record, "trial_record_path": str(path.resolve()), "trial_record_sha256": digest}


def retain_cleanup_receipt(directory: Path, workspace: Path, runner_exit: int, error: str | None) -> None:
    write_json_once(directory / "arm-cleanup.json", {
        "schema_version": "trigger-arm-cleanup/v1", "workspace": str(workspace.resolve()),
        "workspace_removed": error is None and not workspace.exists(),
        "runner_exit_code": runner_exit, "cleanup_error": error,
    })


def case_result(
    host: str, skill: str, entry: dict[str, object], trials: list[dict[str, object]],
    runs: int, threshold: float,
) -> dict[str, object]:
    """Keep unexecuted cases distinct from observed zero-hit outcomes."""
    invalid = sum(trial["trial_valid"] is not True for trial in trials)
    hits = sum(trial["trial_valid"] is True and trial["selected"] is True for trial in trials)
    complete = len(trials) == runs and invalid == 0
    rate = hits / runs if complete else None
    return {
        **entry, "case_id": case_id(host, skill, entry),
        "status": "not_run" if not trials else "complete" if complete else "invalid",
        "selected" if host == "claude" else "triggers": hits if trials else None,
        "runs": runs, "executed_runs": len(trials), "not_run_trials": runs - len(trials),
        "trigger_rate": round(rate, 3) if rate is not None else None,
        "invalid_runs": invalid if trials else None,
        "selection_evidence": trials,
        "pass": (rate >= threshold if entry["should_trigger"] else rate < threshold) if complete else False if trials else None,
    }


@dataclass(frozen=True)
class TrialBatch:
    host: str
    skill: str
    directory: Path
    runs: int
    threshold: float


def execute_trial(
    batch: TrialBatch, entry: dict[str, object], position: tuple[int, int],
    launch: Callable, inspect: Callable, retain: Callable,
) -> dict[str, object]:
    execution: dict[str, object] = {}
    failure = None
    try:
        _rc, stdout, stderr, _timed_out = launch(entry["query"], execution)
    except (processes.QueryError, processes.TerminationRequested) as exc:
        failure = exc
        stdout, stderr = exc.stdout, exc.stderr
        execution.update(exc.process_evidence)
        execution["process_error"] = str(exc)
        if isinstance(exc, processes.TerminationRequested):
            execution["interrupted_by_signal"] = int(exc.signum)
    raw = retain(*position, stdout, stderr)
    parsed = inspect(stdout)
    if failure is not None:
        parsed["reason"] = f"{failure}; {parsed.get('reason', '')}"
    trial = retain_trial_record(batch.directory, make_trial_record(
        batch.host, batch.skill, entry, *position, parsed, raw, execution,
    ))
    if failure is not None:
        write_json_once(batch.directory / f"case-{position[0]:03d}-trial-{position[1]:02d}.failure.json", trial)
    return trial


def run_trials(
    batch: TrialBatch, corpus: list[dict[str, object]], launch: Callable, inspect: Callable, retain: Callable,
    *, progress: Callable | None = None,
) -> tuple[list[dict[str, object]], int | None]:
    """One launch at a time; persist each trial and stop on its first invalidity."""
    results = []
    stop_exit = None
    for case_number, entry in enumerate(corpus, start=1):
        trials = []
        for trial_number in range(1, batch.runs + 1):
            if stop_exit is not None:
                break
            trial = execute_trial(batch, entry, (case_number, trial_number), launch, inspect, retain)
            trials.append(trial)
            if trial["trial_valid"] is not True:
                signum = trial["interrupted_by_signal"]
                stop_exit = 128 + signum if type(signum) is int else 1
                write_json_once(batch.directory / "trial-stop.json", trial)
                if trial.get("isolation_stop"):
                    write_json_once(batch.directory / "isolation-stop.json", {"case": case_number, "trial": trial_number, "evidence": trial})
                break
        result = case_result(batch.host, batch.skill, entry, trials, batch.runs, batch.threshold)
        results.append(result)
        if progress is not None:
            progress(case_number, result)
    return results, stop_exit
