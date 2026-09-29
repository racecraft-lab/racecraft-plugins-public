"""Versioned, replayable trial records for the two trigger-evaluation hosts."""
from __future__ import annotations

import hashlib
import errno
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import trigger_process as processes

SCHEMA_VERSION = "trigger-trial/v2"
EXECUTION_FIELDS = (
    "provider_exit_code", "timed_out", "interrupted_by_signal", "cleanup_verified",
    "cleanup_error", "cleanup_scope", "unexpected_descendants", "child_pid",
    "child_pgid", "cleanup_observations", "process_error", "launch_contract",
)


def case_id(host: str, skill: str, entry: dict[str, object]) -> str:
    value = [host, skill, entry["query"], entry["should_trigger"]]
    digest = hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return f"l2-{digest[:24]}"


def select_case(host: str, skill: str, corpus: list[dict], requested: str | None) -> list[dict]:
    """Select an exact stable identity without altering corpus format or trial count."""
    if requested is None:
        return corpus
    selected = [entry for entry in corpus if case_id(host, skill, entry) == requested]
    if len(selected) != 1:
        raise ValueError("--case-id must resolve exactly one case in the selected corpus")
    return selected


NO_SPECKIT_SKILL_NAME = "no-speckit-skill"
NO_SPECKIT_SKILL_DESCRIPTION = (
    "Use when no available SpecKit skill covers the request, including ordinary coding, testing, tooling, or "
    "repository work and host-specific SpecKit operations whose matching skill is absent from the current catalog, "
    "such as installing Codex subagents when no agent-install skill is available or running the plan stage for an "
    "already-existing spec or populated workflow when no planning skill is available. Reply that no available "
    "SpecKit skill applies and stop."
)
SKILL_ROOT_NAMES = frozenset({"skills", "codex-skills"})


def load_eval_corpus(path: Path) -> tuple[list[dict[str, object]] | None, str]:
    """Validate a trigger corpus before any provider subprocess can run."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"could not read eval file: {exc}"
    if not isinstance(value, list):
        return None, "eval file must contain a JSON list"
    if not value:
        return None, "eval file must contain at least one case"
    seen_queries: set[str] = set()
    for index, entry in enumerate(value, start=1):
        if not isinstance(entry, dict):
            return None, f"eval case {index} must be an object"
        query = entry.get("query")
        should_trigger = entry.get("should_trigger")
        if not isinstance(query, str) or not query.strip() or not isinstance(should_trigger, bool):
            return None, f"eval case {index} requires a non-empty query and boolean should_trigger"
        if query in seen_queries:
            return None, f"eval case {index} duplicates query {query!r}"
        seen_queries.add(query)
    return value, "valid eval corpus"


def available_evals(eval_dir: Path) -> list[str]:
    return [path.name.removesuffix("-trigger.json") for path in sorted(eval_dir.glob("*-trigger.json"))]


def sibling_skill_dirs(source: Path) -> list[Path]:
    """List sibling skill directories beside ``source``'s skill directory.

    Only a plugin skills root (``skills`` or ``codex-skills``) is walked; a
    source staged elsewhere has no siblings. Entries that cannot be inspected
    are skipped, because shared temp roots hold directories owned by others.
    """
    root = source.parent.parent
    if root.name not in SKILL_ROOT_NAMES:
        return []
    siblings: list[Path] = []
    for sibling in sorted(root.iterdir(), key=lambda path: path.name):
        if sibling == source.parent:
            continue
        try:
            if sibling.is_dir() and (sibling / "SKILL.md").is_file():
                siblings.append(sibling)
        except OSError:
            continue
    return siblings


def retain_trial_evidence(
    evidence_dir: Path, case_number: int, trial_number: int, stdout: bytes, stderr: bytes,
) -> dict[str, str]:
    """Persist the exact provider streams, exclusively, and return their path and digest."""
    stem = f"case-{case_number:03d}-trial-{trial_number:02d}"
    stdout_path = evidence_dir / f"{stem}.jsonl"
    stderr_path = evidence_dir / f"{stem}.stderr.log"
    with stdout_path.open("xb") as stream:
        stream.write(stdout)
    with stderr_path.open("xb") as stream:
        stream.write(stderr)
    return {
        "stdout_path": str(stdout_path.resolve()),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_path": str(stderr_path.resolve()),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
    }


def description_override(path: str | None, default: str) -> str:
    """Only the controlled single-line no-op description may vary between arms."""
    if path is None:
        return default
    description = Path(path).read_bytes().decode("utf-8").removesuffix("\n")
    if not description.strip() or "\n" in description or "\r" in description:
        raise ValueError("no-op description must be one nonempty line with at most one terminal LF")
    return description


def trial_checks(record: dict[str, object]) -> dict[str, bool]:
    """Derive validity from typed observations, never from the aggregate pass flag."""
    observations = record.get("cleanup_observations")
    last_probe = observations[-1] if isinstance(observations, list) and observations else None
    group = record.get("child_pgid")
    model_check = record.get("model_identity_check")
    launch = record.get("launch_contract")
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
        "launch": isinstance(launch, dict)
        and launch.get("config_isolated") is True
        and launch.get("retries_disabled") is True
        and launch.get("requested_model") == record.get("requested_model")
        and (
            record.get("host") != "codex"
            or launch.get("stdin_prompt_isolated") is True
            and launch.get("login_state_source") == "CODEX_HOME"
            and launch.get("shell_home_isolated") is True
            and launch.get("scratch_directory_isolated") is True
        ),
        "model": isinstance(model_check, str) and model_check in {"exact", "alias", "requested-only"},
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
        "observation_scope": parsed.get("observation_scope"),
        "qualification_eligible": parsed.get("qualification_eligible") is True,
    }
    checks = trial_checks(record)
    valid = all(checks.values())
    record.update(
        valid=valid,
        trial_valid=valid,
        qualification_eligible=record["qualification_eligible"] is True and valid,
        checks=checks,
    )
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
    qualification_eligible: bool = False


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
    parsed["qualification_eligible"] = (
        batch.qualification_eligible and parsed.get("qualification_observed") is True
    )
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
