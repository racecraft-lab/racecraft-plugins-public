"""Bounded invocation of the two existing native runners, never arbitrary commands."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
import errno
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import sqlite3
import stat
import subprocess
import sys
import threading
import time

import trigger_comparison as comparison
import trigger_carry_forward as carry
from trigger_campaign import CampaignLedger, QualifiedConcurrency, read_ledger, read_ledger_bytes, validate_approval, worker_limit
from trigger_evidence import write_json_once

RUNNERS = {"claude": comparison.ROOT / "layer2-trigger/run-trigger-evals.py",
           "codex": comparison.ROOT / "layer2-trigger/run_codex_evals.py"}


@dataclass(frozen=True)
class CampaignRequest:
    manifest: dict
    approval: dict
    launch_budget: int
    inventory: Path
    descriptions: dict[str, Path]
    output: Path
    workers: int = 1
    pilot_evidence: Path | None = None
    timeout: int = 180
    carry_forward: dict | None = None


def concurrency_binding(manifest: dict) -> str:
    return comparison.json_digest({"pins": manifest["pins"], "identities": manifest["identities"],
                                   "trial_timeout_seconds": manifest["trial_timeout_seconds"]})


def qualify_pilot(root: Path) -> QualifiedConcurrency:
    """Recompute qualification from both full 24-trial schedules and ledger times."""
    manifest = comparison.read_json(root / "manifest.json")
    cases = comparison.validate_experiment(manifest)
    comparison._require(manifest["qualification_scope"] == "pilot" and manifest["arms"] == ["candidate"] and len(cases) == 8, "profile is not the eight-case, fixed-arm pilot")
    approval = comparison.read_json(root / "approval.json")
    validate_approval(approval, comparison.json_digest(manifest), 48)
    binding, ledger = read_ledger(root / "ledger.sqlite3")
    comparison._require(binding == {"manifest_sha256": comparison.json_digest(manifest), "approval_sha256": comparison.json_digest(approval), "launch_budget": 48}, "pilot ledger authorization mismatch")
    comparison._require(comparison.read_json(root / "ledger.json") == ledger and ledger["reserved_launches"] == 48, "published pilot ledger differs from authoritative reservations")
    outcomes, elapsed = [], []
    for schedule in ("serial", "two-worker"):
        index = comparison.read_json(root / f"{schedule}-candidate.index.json")
        _hits, qualified = comparison._read_arm(manifest, root, index, "candidate", cases)
        comparison._require(qualified, "pilot includes ineligible native observations")
        inventory = comparison._artifact_json(root, index["inventory"])
        comparison._require(set(cases) == set(inventory["pilot_case_ids"]), "pilot omitted protected coverage")
        timing = comparison.read_json(root / f"{schedule}.timing.json")
        comparison._require(timing["manifest_sha256"] == comparison.json_digest(manifest) and timing["schedule"] == schedule,
                            "pilot timing is not bound to this execution")
        comparison._require(type(timing["elapsed_seconds"]) in (int, float) and timing["elapsed_seconds"] > 0 and abs(timing["elapsed_seconds"] - (timing["monotonic_finished"] - timing["monotonic_started"])) < 0.001, "missing or inconsistent monotonic pilot elapsed time")
        comparison._require(timing.get("resumed") is False and abs(timing["elapsed_seconds"] - (timing["finished_at"] - timing["started_at"])) < 0.25, "resumed or clock-discontinuous pilot timing cannot qualify concurrency")
        comparison._require(timing.get("non_contiguous") is not True and timing.get("timing_eligible") is not False,
                            "carry-forward or non-contiguous timing cannot qualify a pilot")
        comparison._require(type(timing.get("workers")) is int and timing["workers"] == (1 if schedule == "serial" else 2), "pilot worker configuration mismatch")
        launches = [row for row in ledger["launches"] if row["arm"] == f"{schedule}:candidate"]
        comparison._require(len(launches) == 24 and all(row["status"] == "complete" for row in launches), "pilot has incomplete launch reservations")
        comparison._require({(row["case_id"], row["trial_number"]) for row in launches} == {(key, trial) for key in cases for trial in (1, 2, 3)}, "pilot ledger case roster mismatch")
        comparison._require(all(timing["started_at"] <= row["reserved_at"] <= row["completed_at"] <= timing["finished_at"] for row in launches), "pilot timing does not contain its launches")
        comparison._require(_peak_cases(launches) == (1 if schedule == "serial" else 2), "pilot did not observe the declared concurrency ceiling")
        outcomes.append({(row["case_id"], row["trial_number"]): row["selected"] for row in index["trials"]})
        elapsed.append(timing["elapsed_seconds"])
    comparison._require(outcomes[0] == outcomes[1], "concurrent scheduling changed a matched native outcome")
    profile = QualifiedConcurrency(concurrency_binding(manifest), elapsed[0], elapsed[1], 48)
    worker_limit(2, profile, profile.binding_sha256)
    return profile


def _peak_cases(launches: list[dict]) -> int:
    events = []
    for key in {row["case_id"] for row in launches}:
        rows = [row for row in launches if row["case_id"] == key]
        events.extend([(min(row["reserved_at"] for row in rows), 1), (max(row["completed_at"] for row in rows), -1)])
    active = peak = 0
    for _at, change in sorted(events):
        active += change
        peak = max(peak, active)
    return peak


def native_command(case: dict, request: CampaignRequest, arm: str, directory: Path) -> list[str]:
    """Only a fixed in-repository runner can be dispatched by a campaign."""
    return [sys.executable, str(RUNNERS[case["host"]]), case["skill"],
            "--case-id", case["case_id"], "--model", request.manifest["pins"][case["host"]]["model"],
            "--timeout", str(request.timeout), "--no-op-description-file", str(request.output / f"{arm}-description.txt"),
            "--evidence-dir", str(directory / "evidence"), "--out", str(directory / "report.json")]


def execute_case(case: dict, request: CampaignRequest, arm: str, directory: Path, stop: threading.Event) -> int:
    """Forward cancellation to the native runner so its owned cleanup executes."""
    directory.mkdir(parents=True, exist_ok=False)
    command = native_command(case, request, arm, directory)
    started = time.monotonic()
    child = subprocess.Popen([sys.executable, *command[1:]], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             shell=False, start_new_session=True)
    try:
        write_json_once(directory / "launch.json", {"pid": child.pid, "command": command, "started_at": time.time()})
        stdout, stderr = _collect_runner(child, request.timeout * 3 + 180, stop)
        for name, payload in (("runner.stdout", stdout), ("runner.stderr", stderr)):
            with (directory / name).open("xb") as stream:
                stream.write(payload)
        write_json_once(directory / "execution.json", {"runner_exit_code": child.returncode, "finished_at": time.time(),
                                                       "elapsed_seconds": time.monotonic() - started})
        return child.returncode
    finally:
        if child.poll() is None:
            _terminate_runner(child)


def _terminate_runner(child) -> None:
    child.send_signal(signal.SIGTERM)
    try:
        child.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        child.kill()
        try:
            child.communicate(timeout=5)
        finally:
            raise ValueError("forced native runner termination; owned-provider cleanup is unknown") from None


def _collect_runner(child, timeout: int, stop: threading.Event) -> tuple[bytes, bytes]:
    started = time.monotonic()
    while True:
        if stop.is_set() or time.monotonic() - started > timeout:
            _terminate_runner(child)
            return child.communicate(timeout=5)
        try:
            return child.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            continue


def _settle_case(directory: Path, exit_code: int) -> str:
    receipt = comparison.read_json(directory / "evidence/arm-cleanup.json")
    comparison._require(receipt.get("workspace_removed") is True and receipt.get("cleanup_error") is None,
                        "native workspace cleanup is unknown")
    comparison._require(receipt.get("runner_exit_code") == exit_code, "native exit and cleanup disagree")
    trials = list((directory / "evidence").glob("*.trial.json"))
    comparison._require(all(comparison.read_json(path).get("cleanup_verified") is True for path in trials), "provider group cleanup is unknown")
    report_path = directory / "report.json"
    if exit_code not in (0, 1) or not report_path.exists():
        return "invalid"
    report = comparison.read_json(report_path)
    return "complete" if report["summary"]["complete"] is True else "invalid"


def _copy_input(source: Path, target: Path) -> None:
    payload = source.read_bytes()
    if target.exists():
        comparison._require(target.read_bytes() == payload, "frozen campaign input changed on resume")
    else:
        with target.open("xb") as stream:
            stream.write(payload)


def _request_inputs(request: CampaignRequest, reconciliation_identities: dict | None) -> tuple[Path, dict[str, Path]]:
    manifest = request.manifest
    current_identities = reconciliation_identities or comparison.snapshot_identities(comparison.measurement_snapshot())
    if reconciliation_identities is None:
        comparison._require(current_identities == manifest["identities"], "frozen public inputs changed before launch")
        return request.inventory, request.descriptions
    observer = current_identities.get("observer")
    comparison._require(set(current_identities) == set(manifest["identities"])
                        and isinstance(observer, str) and len(observer) == 64
                        and all(character in "0123456789abcdef" for character in observer)
                        and {key: value for key, value in current_identities.items() if key != "observer"}
                        == {key: value for key, value in manifest["identities"].items() if key != "observer"},
                        "frozen public inputs other than the observer changed before reconciliation")
    return (request.output / "inventory.json",
            {arm: request.output / f"{arm}-description.txt" for arm in manifest["arms"]})


def _validate_carry_forward_request(
    request: CampaignRequest, manifest: dict, *, under_global_lease: bool = False,
) -> carry.CarryForwardPlan | carry.MultiGenerationPlan | None:
    if request.approval.get("schema_version") == "trigger-campaign-approval/v5":
        comparison._require(request.carry_forward is not None,
                            "multi-generation approval requires its request component")
        plan = carry.validate_multi_generation_carry_forward(
            request.carry_forward, manifest, comparison.json_digest(manifest),
            approval=request.approval, check_historical_lease=not under_global_lease)
        comparison._require(all(segment.lease_path == _global_lease_path().resolve()
                                for segment in plan.histories),
                            "all historical campaigns must share the exact global lease")
        comparison._require(manifest["qualification_scope"] == "full" and request.workers == 1
                            and request.pilot_evidence is None,
                            "multi-generation carry-forward requires serial full qualification without a pilot")
        return plan
    if request.approval.get("schema_version") == "trigger-campaign-approval/v4":
        comparison._require(request.carry_forward is not None, "carry-forward approval requires its request component")
        plan = carry.validate_carry_forward(request.carry_forward, manifest, comparison.json_digest(manifest),
                                            approval=request.approval)
        comparison._require(manifest["qualification_scope"] == "full" and request.workers == 1
                            and request.pilot_evidence is None,
                            "carry-forward requires serial full qualification without a pilot")
        return plan
    comparison._require(request.carry_forward is None, "carry-forward requires its versioned approval")
    return None


def _validate_request(request: CampaignRequest, *, reconciliation_identities: dict | None = None,
                      under_global_lease: bool = False) -> list[tuple[str, int]]:
    manifest = request.manifest
    comparison.validate_experiment(manifest)
    validate_approval(request.approval, comparison.json_digest(manifest), request.launch_budget,
                      carry_forward=request.carry_forward)
    carry_plan = _validate_carry_forward_request(
        request, manifest, under_global_lease=under_global_lease)
    if request.approval.get("schema_version") == "trigger-campaign-approval/v3":
        comparison._require(type(request.workers) is int
                            and request.workers == request.approval["campaign_exercise"]["schedule"]["workers"] == 1,
                            "standing campaign authorization requires serial execution")
    destination = manifest.get("output_directory")
    comparison._require(isinstance(destination, str) and Path(destination).is_absolute()
        and destination == str(Path(destination).resolve()) and request.output.resolve() == Path(destination),
        "approved manifest must bind this exact canonical output directory; changing it cannot reset the campaign budget")
    comparison._require(type(request.timeout) is int and request.timeout == manifest["trial_timeout_seconds"],
                        "per-trial timeout differs from approved manifest")
    inventory_path, descriptions = _request_inputs(request, reconciliation_identities)
    comparison._require(hashlib.sha256(inventory_path.read_bytes()).hexdigest() == manifest["inventory_sha256"], "frozen inventory changed before launch")
    inventory_manifest = (carry_plan.logical_manifest
                          if isinstance(carry_plan, carry.MultiGenerationPlan) else manifest)
    comparison.validate_inventory_binding(inventory_manifest, comparison.read_json(inventory_path))
    for arm in manifest["arms"]:
        comparison._require(hashlib.sha256(descriptions[arm].read_bytes()).hexdigest() == manifest["controlled_difference"][f"{arm}_sha256"], "controlled description changed before launch")
    if manifest["qualification_scope"] == "pilot":
        inventory = comparison.read_json(inventory_path)
        comparison._require(manifest["arms"] == ["candidate"] and {row["case_id"] for row in manifest["roster"]} == set(inventory["pilot_case_ids"]), "pilot roster differs from protected eight-case selection")
        schedules = [("serial", 1), ("two-worker", 2)]
    else:
        profile = qualify_pilot(request.pilot_evidence) if request.pilot_evidence else None
        schedules = [("serial" if request.workers == 1 else "two-worker", worker_limit(request.workers, profile, concurrency_binding(manifest)))]
    launches = len(manifest["roster"]) * 3 * len(manifest["arms"]) * len(schedules)
    if request.approval.get("schema_version") == "trigger-campaign-approval/v4":
        launches -= len(carry_plan.carried_trials)
    comparison._require(request.launch_budget == launches, "approval budget must equal the exact planned launch count")
    return schedules


def _build_schedule_index(request: CampaignRequest, arm: str, reports: list[Path],
                          plan: carry.CarryForwardPlan | carry.MultiGenerationPlan | None) -> dict:
    if isinstance(plan, carry.MultiGenerationPlan):
        fresh_ids = tuple(row["case_id"] for row in plan.logical_manifest["roster"]
                          if (arm, row["case_id"]) in plan.fresh)
        if not fresh_ids:
            return carry.multi_source_index(plan, arm, None)
        fresh_manifest = carry.fresh_partial_manifest(plan.logical_manifest, fresh_ids)
        fresh_index = comparison.build_evidence_index(
            fresh_manifest, arm, request.output, reports,
            request.output / "inventory.json", request.output / f"{arm}-description.txt",
        )
        return carry.multi_source_index(plan, arm, fresh_index)
    if plan is not None and arm == "baseline":
        fresh_manifest = carry.fresh_partial_manifest(request.manifest, plan.fresh_case_ids)
        fresh_index = comparison.build_evidence_index(
            fresh_manifest, arm, request.output, reports,
            request.output / "inventory.json", request.output / f"{arm}-description.txt",
        )
        return carry.source_aware_index(request.manifest, plan, fresh_index)
    return comparison.build_evidence_index(request.manifest, arm, request.output, reports,
        request.output / "inventory.json", request.output / f"{arm}-description.txt")


def _schedule_reservation(request: CampaignRequest, schedule: str, ledger: CampaignLedger,
                          activate_lease=None):
    start_path = request.output / f"{schedule}.start.json"
    resumed = start_path.exists()
    start = comparison.read_json(start_path) if resumed else {
        "started_at": time.time(), "monotonic_started": time.monotonic(),
        "manifest_sha256": comparison.json_digest(request.manifest)}
    if activate_lease is None:
        if not resumed:
            write_json_once(start_path, start)
        return start, resumed, ledger.reserve_case, lambda publication: publication()
    pending = True
    def activate_schedule(publication=None):
        nonlocal pending
        if not pending:
            if publication is not None:
                publication()
            return
        activate_lease()
        if not resumed:
            write_json_once(start_path, start)
        if publication is not None:
            publication()
        pending = False
    def reserve_case(arm, case_id):
        ledger.reserve_case(arm, case_id, activate_schedule)
    def publish(publication):
        if pending:
            ledger.prepare_publication(lambda: activate_schedule(publication))
        else:
            publication()
    return start, resumed, reserve_case, publish


def _run_schedule(request: CampaignRequest, schedule: str, workers: int, ledger: CampaignLedger,
                  stop: threading.Event, plan: carry.CarryForwardPlan | carry.MultiGenerationPlan | None = None,
                  lineage_guard=None, activate_lease=None) -> None:
    if lineage_guard is not None:
        lineage_guard()
    start, resumed, reserve_case, publish = _schedule_reservation(
        request, schedule, ledger, activate_lease)
    comparison._require(start["manifest_sha256"] == comparison.json_digest(request.manifest), "schedule start belongs to another manifest")
    started_at = start["started_at"]
    prior = {(row["arm"], row["case_id"]): row["status"] for row in ledger.snapshot()["launches"]}
    carried_pairs = (set(plan.carried) if plan is not None and hasattr(plan, "carried") else
                     {("baseline", case_id) for case_id in getattr(plan, "carried_case_ids", ())})
    def run(job):
        arm, case = job
        identity = f"{schedule}:{arm}"
        if stop.is_set() or prior.get((identity, case["case_id"])) == "complete" or (arm, case["case_id"]) in carried_pairs:
            return
        try:
            if lineage_guard is not None:
                comparison._require(plan is not None, "carry-forward dispatch lacks its validated lineage plan")
                lineage_guard()
            reserve_case(identity, case["case_id"])
            directory = request.output / schedule / arm / case["case_id"]
            status = _settle_case(directory, execute_case(case, request, arm, directory, stop))
            ledger.finish_case(identity, case["case_id"], status)
            if status != "complete":
                stop.set()
        except (OSError, ValueError, KeyError, TypeError):
            stop.set()
            raise
    jobs = [(arm, case) for arm in request.manifest["arms"] for case in request.manifest["roster"]]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(run, jobs))
    comparison._require(not stop.is_set(), "campaign interrupted or invalid; remaining launches were not started")
    if lineage_guard is not None:
        lineage_guard()
        carry.validate_fresh_ledger(plan, ledger.snapshot()["launches"], complete=True)
    timing = request.output / f"{schedule}.timing.json"
    if not timing.exists():
        finished_at = time.time()
        monotonic_finished = time.monotonic()
        record = {"schedule": schedule, "workers": workers, "started_at": started_at,
            "finished_at": finished_at, "calendar_elapsed_seconds": finished_at - started_at,
            "monotonic_started": start["monotonic_started"], "monotonic_finished": monotonic_finished,
            "elapsed_seconds": monotonic_finished - start["monotonic_started"], "resumed": resumed,
            "manifest_sha256": comparison.json_digest(request.manifest),
            **({"non_contiguous": True, "timing_eligible": False} if plan is not None else {})}
        publish(lambda: write_json_once(timing, record))
    index_arms = plan.logical_manifest["arms"] if isinstance(plan, carry.MultiGenerationPlan) else request.manifest["arms"]
    for arm in index_arms:
        reports = [request.output / schedule / arm / case["case_id"] / "report.json"
                   for case in request.manifest["roster"]
                   if arm in request.manifest["arms"]
                   and (plan is None or (arm, case["case_id"]) not in carried_pairs)]
        index = _build_schedule_index(request, arm, reports, plan)
        index_path = request.output / f"{schedule}-{arm}.index.json"
        if index_path.exists():
            comparison._require(comparison.read_json(index_path) == index, "published index changed on resume")
        else:
            publish(lambda: write_json_once(index_path, index))


def _validate_prior(request: CampaignRequest, ledger: CampaignLedger | None = None,
                    *, snapshot: dict | None = None) -> None:
    comparison._require((ledger is None) != (snapshot is None),
                        "prior validation requires exactly one immutable ledger view")
    rows = (snapshot if snapshot is not None else ledger.snapshot())["launches"]
    identities = {row["arm"] for row in rows}
    for identity in sorted(identities):
        schedule, arm = identity.split(":", 1)
        if request.manifest["qualification_scope"] == "pilot":
            comparison._require((request.output / f"{schedule}.timing.json").is_file(), "partial pilot schedule cannot qualify timing; review a new campaign before additional launches")
        keys = {row["case_id"] for row in rows if row["arm"] == identity}
        roster = [row for row in request.manifest["roster"] if row["case_id"] in keys]
        partial = {**request.manifest, "qualification_scope": "pr-core", "roster": roster, "corpus_sha256": comparison.json_digest(roster)}
        reports = [request.output / schedule / arm / row["case_id"] / "report.json" for row in roster]
        comparison.build_evidence_index(partial, arm, request.output, reports, request.output / "inventory.json", request.output / f"{arm}-description.txt")


def _global_lease_path() -> Path:
    return Path("/tmp") / f"speckit-trigger-native-{os.getuid()}.lock"


def _validate_lease_file(lock, request: CampaignRequest, *, reconciling: bool = False) -> None:
    info = os.fstat(lock.fileno())
    comparison._require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                        and stat.S_IMODE(info.st_mode) & 0o077 == 0,
                        "unsafe global campaign lock ownership")
    lock.seek(0)
    previous = lock.read()
    if not previous:
        return
    try:
        lease = json.loads(previous)
    except (json.JSONDecodeError, UnicodeError):
        raise ValueError("global campaign lease state is unreadable") from None
    comparison._require(isinstance(lease, dict)
                        and set(lease) == {"schema_version", "state", "campaign"}
                        and lease["schema_version"] == "trigger-global-lease/v1"
                        and (lease["state"] == "idle"
                             or reconciling and lease["state"] == "unknown"
                             and lease["campaign"] == str(request.output)),
                        "an interrupted global campaign requires owned-process/artifact reconciliation before any new launch")


def _inspect_global_lease(request: CampaignRequest, *, path: Path | None = None) -> None:
    """Prove current lease admission without creating or modifying the lease."""
    import fcntl
    lease_path = path or _global_lease_path()
    try:
        descriptor = os.open(lease_path, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0))
    except FileNotFoundError:
        return
    except OSError as exc:
        raise ValueError(f"global campaign lease could not be inspected: {exc}") from None
    with os.fdopen(descriptor, "rb") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("another native campaign owns the global launch ceiling") from None
        try:
            _validate_lease_file(lock, request)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


@dataclass
class _LeaseState:
    ledger: CampaignLedger | None
    _publish_active: object = None
    active: bool = False

    def activate(self, ledger: CampaignLedger) -> None:
        comparison._require(self.ledger is None and not self.active,
                            "global campaign lease was already activated")
        self.ledger = ledger
        if self._publish_active is not None:
            self._publish_active()
        self.active = True


@contextmanager
def _global_lease(request: CampaignRequest, ledger: CampaignLedger | None = None,
                  *, reconciling: bool = False):
    comparison._require(os.name == "posix", "native campaigns require the qualified POSIX ownership contract")
    import fcntl
    # Deliberately independent of TMPDIR, campaign roots, and worktree isolation.
    path = _global_lease_path()
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "r+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("another native campaign owns the global launch ceiling") from None
        _validate_lease_file(lock, request, reconciling=reconciling)
        def publish(state):
            lock.seek(0)
            lock.write(json.dumps({"schema_version": "trigger-global-lease/v1", "state": state, "campaign": str(request.output)}).encode())
            lock.truncate()
            lock.flush()
            os.fsync(lock.fileno())
        state = _LeaseState(ledger, lambda: publish("active"))
        if ledger is not None:
            publish("active")
            state.active = True
        try:
            yield state
        finally:
            if state.active:
                unknown = state.ledger is not None and state.ledger.snapshot()["unknown_launches"]
                publish("unknown" if unknown else "idle")
            fcntl.flock(lock, fcntl.LOCK_UN)


def _require_absent(pid: int, *, group: bool = False) -> dict:
    comparison._require(type(pid) is int and pid > 0 and pid != os.getpid(), "invalid owned process identity")
    try:
        if group:
            os.killpg(pid, 0)
        else:
            os.kill(pid, 0)
    except ProcessLookupError as error:
        return {"kind": "pgid" if group else "pid", "identity": pid, "signal": 0,
                "outcome": "absent", "errno": error.errno or errno.ESRCH}
    raise ValueError("an owned process identity is still live; reconciliation never kills or relaunches it")


def _validate_frozen_campaign(request: CampaignRequest) -> None:
    for name, expected in (("manifest.json", request.manifest), ("approval.json", request.approval)):
        path = request.output / name
        comparison._require(path.is_file() and not path.is_symlink(), f"missing frozen campaign {name}")
        comparison._require(comparison.read_json(path) == expected, f"frozen campaign {name} changed")


def _case_artifacts(request: CampaignRequest, identity: str, case_id: str, directory: Path) -> tuple[dict, list[dict]]:
    _schedule, arm = identity.split(":", 1)
    matches = [case for case in request.manifest["roster"] if case["case_id"] == case_id]
    comparison._require(len(matches) == 1 and arm in request.manifest["arms"], "ledger case is not in the frozen campaign roster")
    case = matches[0]
    launch_path = directory / "launch.json"
    execution_path = directory / "execution.json"
    report_path = directory / "report.json"
    cleanup_path = directory / "evidence/arm-cleanup.json"
    runner_stdout = directory / "runner.stdout"
    runner_stderr = directory / "runner.stderr"
    launch = comparison.read_json(launch_path)
    execution_record = comparison.read_json(execution_path)
    report = comparison.read_json(report_path)
    cleanup = comparison.read_json(cleanup_path)
    comparison._require(launch.get("command") == native_command(case, request, arm, directory), "retained launch identity changed")
    comparison._require(type(execution_record.get("runner_exit_code")) is int
                        and cleanup.get("runner_exit_code") == execution_record["runner_exit_code"],
                        "retained execution and cleanup identities disagree")
    comparison._require(cleanup.get("schema_version") == "trigger-arm-cleanup/v1"
                        and cleanup.get("workspace_removed") is True and cleanup.get("cleanup_error") is None,
                        "retained arm cleanup identity is malformed")
    workspace = cleanup.get("workspace")
    comparison._require(isinstance(workspace, str) and Path(workspace).is_absolute()
                        and workspace == str(Path(workspace).resolve()), "retained workspace identity is malformed")
    results = report.get("results")
    comparison._require(isinstance(report.get("summary"), dict) and report["summary"].get("complete") is False
                        and isinstance(results, list) and len(results) == 1
                        and results[0].get("case_id") == case_id and results[0].get("status") == "invalid",
                        "retained invalid report identity is malformed")
    trial_paths = sorted((directory / "evidence").glob("*.trial.json"))
    comparison._require(bool(trial_paths), "retained provider trial roster is empty")
    trial_artifacts = []
    failed_cleanup = False
    report_trials = results[0].get("selection_evidence")
    comparison._require(isinstance(report_trials, list) and len(report_trials) == len(trial_paths),
                        "retained report trial roster disagrees with evidence")
    by_path = {item.get("trial_record_path"): item for item in report_trials if isinstance(item, dict)}
    pgids = set()
    for trial_path in trial_paths:
        trial = comparison.read_json(trial_path)
        comparison._require(trial.get("schema_version") == "trigger-trial/v2" and trial.get("case_id") == case_id,
                            "retained trial identity changed")
        embedded = by_path.get(str(trial_path.resolve()))
        comparison._require(isinstance(embedded, dict)
                            and embedded.get("trial_record_sha256") == hashlib.sha256(trial_path.read_bytes()).hexdigest()
                            and {key: value for key, value in embedded.items()
                                 if key not in {"trial_record_path", "trial_record_sha256"}} == trial,
                            "retained report embeds a different trial")
        raw = {}
        for channel in ("stdout", "stderr"):
            raw_path = Path(trial.get(f"{channel}_path", ""))
            comparison._require(raw_path.is_absolute() and not raw_path.is_symlink()
                                and raw_path.resolve().is_relative_to((directory / "evidence").resolve()),
                                "retained raw stream escaped its case evidence")
            reference = comparison.artifact_reference(request.output, raw_path)
            comparison._require(reference["sha256"] == trial.get(f"{channel}_sha256"),
                                "retained raw stream digest changed")
            raw[channel] = reference
        pgid = trial.get("child_pgid")
        comparison._require(type(pgid) is int and pgid > 0, "retained provider process-group identity is malformed")
        pgids.add(pgid)
        failed_cleanup = failed_cleanup or trial.get("trial_valid") is False and (
            trial.get("cleanup_verified") is False or trial.get("cleanup_error") is not None)
        trial_artifacts.append({"record": comparison.artifact_reference(request.output, trial_path), **raw})
    comparison._require(failed_cleanup, "terminal reconciliation requires an immutable cleanup-failed invalid trial")
    observations = [_require_absent(launch.get("pid"))]
    observations.extend(_require_absent(pgid, group=True) for pgid in sorted(pgids))
    comparison._require(not Path(workspace).exists(), "owned workspace remains after claimed cleanup")
    observations.append({"kind": "workspace", "identity": workspace, "outcome": "absent"})
    artifacts = {
        "campaign": {
            "manifest": comparison.artifact_reference(request.output, request.output / "manifest.json"),
            "approval": comparison.artifact_reference(request.output, request.output / "approval.json"),
            "inventory": comparison.artifact_reference(request.output, request.output / "inventory.json"),
            "descriptions": {name: comparison.artifact_reference(request.output, request.output / f"{name}-description.txt")
                             for name in request.manifest["arms"]},
        },
        "case": {
            "launch": comparison.artifact_reference(request.output, launch_path),
            "execution": comparison.artifact_reference(request.output, execution_path),
            "report": comparison.artifact_reference(request.output, report_path),
            "cleanup": comparison.artifact_reference(request.output, cleanup_path),
            "runner_stdout": comparison.artifact_reference(request.output, runner_stdout),
            "runner_stderr": comparison.artifact_reference(request.output, runner_stderr),
            "trials": trial_artifacts,
        },
    }
    return artifacts, observations


def _retain_terminal_reconciliation(request: CampaignRequest, identity: str, case_id: str,
                                    directory: Path, current_identities: dict) -> None:
    artifacts, observations = _case_artifacts(request, identity, case_id, directory)
    stable = {
        "schema_version": "trigger-terminal-reconciliation/v1",
        "manifest_sha256": comparison.json_digest(request.manifest),
        "approval_sha256": comparison.json_digest(request.approval),
        "launch_budget": request.launch_budget,
        "arm": identity,
        "case_id": case_id,
        "historical_observer": request.manifest["identities"]["observer"],
        "current_observer": current_identities["observer"],
        "terminal_status": "invalid",
        "native_launches": 0,
        "artifacts": artifacts,
        "absence_observations": observations,
    }
    path = directory / "evidence/terminal-reconciliation.json"
    if path.exists():
        comparison._require(path.is_file() and not path.is_symlink(), "terminal reconciliation receipt is not a regular file")
        receipt = comparison.read_json(path)
        observed_at = receipt.pop("observed_at", None)
        comparison._require(type(observed_at) in (int, float) and not isinstance(observed_at, bool) and observed_at > 0
                            and receipt == stable, "terminal reconciliation receipt changed or is malformed")
    else:
        write_json_once(path, {**stable, "observed_at": time.time()})


def reconcile_campaign(request: CampaignRequest) -> dict:
    """Inspect retained processes/artifacts only; settle accounting without launching."""
    _validate_frozen_campaign(request)
    current_identities = comparison.snapshot_identities(comparison.measurement_snapshot())
    _validate_request(request, reconciliation_identities=current_identities)
    comparison._require((request.output / "ledger.sqlite3").is_file(), "no existing campaign ledger to reconcile")
    ledger = CampaignLedger(request.output / "ledger.sqlite3", comparison.json_digest(request.manifest),
                            request.approval, request.launch_budget, carry_forward=request.carry_forward)
    with _global_lease(request, ledger, reconciling=True):
        snapshot = ledger.snapshot()
        candidates = {(row["arm"], row["case_id"]) for row in snapshot["launches"]
                      if row["status"] == "unknown" or
                      (request.output / row["arm"].replace(":", "/") / row["case_id"]
                       / "evidence/terminal-reconciliation.json").exists()}
        for identity, case_id in sorted(candidates):
            schedule, arm = identity.split(":", 1)
            directory = request.output / schedule / arm / case_id
            rows = [row for row in snapshot["launches"] if row["arm"] == identity and row["case_id"] == case_id]
            statuses = {row["status"] for row in rows}
            comparison._require(len(rows) == 3 and {row["trial_number"] for row in rows} == {1, 2, 3}
                                and statuses in ({"unknown"}, {"invalid"}),
                                "terminal reconciliation ledger reservations are malformed")
            trial_paths = sorted((directory / "evidence").glob("*.trial.json"))
            comparison._require(bool(trial_paths), "retained provider trial roster is empty")
            cleanup_failed = any(
                (trial := comparison.read_json(path)).get("cleanup_verified") is False
                or trial.get("cleanup_error") is not None
                for path in trial_paths
            )
            if cleanup_failed:
                _retain_terminal_reconciliation(request, identity, case_id, directory, current_identities)
                if statuses == {"unknown"}:
                    ledger.finish_case(identity, case_id, "invalid")
                continue
            comparison._require(statuses == {"unknown"}, "settled clean reconciliation lacks a terminal receipt")
            launch = comparison.read_json(directory / "launch.json")
            _require_absent(launch["pid"])
            cleanup = comparison.read_json(directory / "evidence/arm-cleanup.json")
            comparison._require(not Path(cleanup["workspace"]).exists(), "owned workspace remains after claimed cleanup")
            for path in trial_paths:
                _require_absent(comparison.read_json(path)["child_pgid"], group=True)
            ledger.finish_case(identity, case_id, _settle_case(directory, cleanup["runner_exit_code"]))
    return {"reconciled": True, "native_launches": 0, "ledger": ledger.snapshot()}


def _carry_lineage_receipt(
    request: CampaignRequest, plan: carry.CarryForwardPlan | carry.MultiGenerationPlan,
) -> dict:
    if isinstance(plan, carry.MultiGenerationPlan):
        return {
            "schema_version": "trigger-carry-forward-lineage/v2",
            "manifest_sha256": comparison.json_digest(request.manifest),
            "logical_manifest_sha256": comparison.json_digest(plan.logical_manifest),
            "approval_sha256": comparison.json_digest(request.approval),
            "carry_forward_sha256": plan.component_sha256,
            "historical_generations": [segment.generation_id for segment in plan.histories],
            "carried_trials": len(plan.carried_trials),
            "fresh_trials": len(plan.fresh_trials),
            "accounting": plan.component["accounting"],
            "non_contiguous": True, "timing_eligible": False,
        }
    return {
        "schema_version": "trigger-carry-forward-lineage/v1",
        "manifest_sha256": comparison.json_digest(request.manifest),
        "approval_sha256": comparison.json_digest(request.approval),
        "carry_forward_sha256": plan.component_sha256,
        "source_root": str(plan.source_root),
        "review_root": str(plan.review_root),
        "carried_case_ids": list(plan.carried_case_ids),
        "fresh_case_ids": list(plan.fresh_case_ids),
        "accounting": carry.EXPECTED_ACCOUNTING,
        "non_contiguous": True,
        "timing_eligible": False,
    }


def _publish_carry_request(
    request: CampaignRequest, plan: carry.CarryForwardPlan | carry.MultiGenerationPlan,
) -> None:
    """Publish one immutable request set; a partial prior publication is terminal."""
    if isinstance(plan, carry.MultiGenerationPlan):
        comparison._require(not request.output.exists(),
                            "V5 carry-forward requires a fresh absent output root")
        request.output.mkdir(parents=True)
        write_json_once(request.output / "carry-forward-lineage.json",
                        _carry_lineage_receipt(request, plan))
        write_json_once(request.output / "logical-manifest.json", plan.logical_manifest)
        return
    required = {"carry-forward-lineage.json", "manifest.json", "approval.json", "inventory.json",
                "baseline-description.txt", "candidate-description.txt", "ledger.sqlite3"}
    if request.output.exists():
        present = {path.name for path in request.output.iterdir()}
        comparison._require(required <= present,
                            "partial carry-forward publication requires a newly reviewed output root")
        comparison._require(comparison.read_json(request.output / "carry-forward-lineage.json")
                            == _carry_lineage_receipt(request, plan),
                            "published carry-forward lineage changed on resume")
        return
    request.output.mkdir(parents=True)
    write_json_once(request.output / "carry-forward-lineage.json", _carry_lineage_receipt(request, plan))


def _serialized_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def _safe_saved_entry(path: Path, label: str, *, directory: bool) -> None:
    try:
        value = path.lstat()
    except OSError as exc:
        raise ValueError(f"{label} could not be inspected safely: {exc}") from None
    expected_type = stat.S_ISDIR(value.st_mode) if directory else stat.S_ISREG(value.st_mode)
    comparison._require(expected_type and not stat.S_ISLNK(value.st_mode)
                        and value.st_uid == os.getuid()
                        and not value.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
                        and (directory or value.st_nlink == 1),
                        f"{label} ownership, type, mode, or identity is unsafe")


def _saved_json(root: Path, name: str, label: str) -> dict:
    path = root / name
    _safe_saved_entry(path, label, directory=False)
    payload = carry._read_external_path(root, Path(name), label, max_bytes=carry._MAX_JSON)
    value = carry._json(payload, label)
    comparison._require(isinstance(value, dict) and payload == _serialized_json(value),
                        f"{label} is not the canonical immutable JSON publication")
    return value


def _validate_saved_ledger_snapshot(value: object, plan: carry.CarryForwardPlan,
                                    budget: int, *, complete: bool = False) -> None:
    comparison._require(isinstance(value, dict) and set(value) == {
        "schema_version", "launch_budget", "reserved_launches", "unknown_launches", "launches"}
        and value["schema_version"] == "trigger-campaign-ledger/v1"
        and type(value["launch_budget"]) is int and value["launch_budget"] == budget
        and type(value["reserved_launches"]) is int
        and isinstance(value["launches"], list)
        and value["reserved_launches"] == len(value["launches"])
        and type(value["unknown_launches"]) is int
        and value["unknown_launches"]
        == sum(row.get("status") == "unknown" for row in value["launches"]
               if isinstance(row, dict)),
        "saved carry-forward ledger snapshot is malformed")
    for row in value["launches"]:
        comparison._require(isinstance(row, dict) and set(row) == {
            "arm", "case_id", "trial_number", "status", "reserved_at", "completed_at"}
            and type(row["reserved_at"]) in {int, float}
            and not isinstance(row["reserved_at"], bool) and math.isfinite(row["reserved_at"])
            and row["reserved_at"] > 0
            and ((row["status"] == "unknown" and row["completed_at"] is None)
                 or (row["status"] in {"complete", "invalid"}
                     and type(row["completed_at"]) in {int, float}
                     and not isinstance(row["completed_at"], bool)
                     and math.isfinite(row["completed_at"])
                     and row["completed_at"] >= row["reserved_at"])),
                            "saved carry-forward ledger row has invalid timestamps")
    carry.validate_fresh_ledger(plan, value["launches"], complete=complete)


def _validate_saved_start(request: CampaignRequest, present: set[str], snapshot: dict) -> dict | None:
    if "serial.start.json" not in present:
        comparison._require(not snapshot["launches"],
                            "saved carry-forward reservations lack their schedule start")
        return None
    value = _saved_json(request.output, "serial.start.json", "saved serial schedule start")
    comparison._require(set(value) == {"started_at", "monotonic_started", "manifest_sha256"}
                        and value["manifest_sha256"] == comparison.json_digest(request.manifest)
                        and type(value["started_at"]) is float and math.isfinite(value["started_at"])
                        and value["started_at"] > 0
                        and type(value["monotonic_started"]) is float
                        and math.isfinite(value["monotonic_started"])
                        and value["monotonic_started"] >= 0,
                        "saved serial schedule start is malformed or belongs to another manifest")
    return value


def _validate_saved_serial_tree(request: CampaignRequest, present: set[str], snapshot: dict) -> None:
    grouped: dict[str, set[str]] = {}
    for row in snapshot["launches"]:
        schedule, separator, arm = row["arm"].partition(":")
        comparison._require(separator and schedule == "serial" and arm in request.manifest["arms"],
                            "saved carry-forward ledger uses an unsupported schedule")
        grouped.setdefault(arm, set()).add(row["case_id"])
    if "serial" not in present:
        comparison._require(not grouped, "saved carry-forward case results lack their serial directory")
        return
    serial = request.output / "serial"
    _safe_saved_entry(serial, "saved serial destination", directory=True)
    comparison._require(grouped, "an empty saved serial destination cannot precede reservations")
    try:
        arm_paths = list(serial.iterdir())
    except OSError as exc:
        raise ValueError(f"saved serial destination could not be enumerated: {exc}") from None
    comparison._require({path.name for path in arm_paths} == set(grouped),
                        "saved serial destination arms differ from the fresh ledger")
    for arm_path in arm_paths:
        _safe_saved_entry(arm_path, "saved serial arm destination", directory=True)
        try:
            case_paths = list(arm_path.iterdir())
        except OSError as exc:
            raise ValueError(f"saved serial arm destination could not be enumerated: {exc}") from None
        comparison._require({path.name for path in case_paths} == grouped[arm_path.name],
                            "saved serial case destinations differ from the fresh ledger")
        for case_path in case_paths:
            _safe_saved_entry(case_path, "saved serial case destination", directory=True)
            try:
                descendants = list(case_path.rglob("*"))
            except OSError as exc:
                raise ValueError(f"saved serial case tree could not be enumerated: {exc}") from None
            for path in descendants:
                try:
                    kind = path.lstat().st_mode
                except OSError as exc:
                    raise ValueError(f"saved serial case entry could not be inspected: {exc}") from None
                comparison._require(stat.S_ISDIR(kind) or stat.S_ISREG(kind),
                                    "saved serial case tree contains an unsupported entry")
                _safe_saved_entry(path, "saved serial case entry", directory=stat.S_ISDIR(kind))


def _validate_saved_timing(request: CampaignRequest, present: set[str], snapshot: dict,
                           start: dict | None) -> dict | None:
    if "serial.timing.json" not in present:
        return None
    comparison._require(start is not None and snapshot["reserved_launches"] == request.launch_budget
                        and all(row["status"] == "complete" for row in snapshot["launches"]),
                        "saved serial timing cannot precede complete fresh evidence")
    value = _saved_json(request.output, "serial.timing.json", "saved serial timing")
    fields = {"schedule", "workers", "started_at", "finished_at", "calendar_elapsed_seconds",
              "monotonic_started", "monotonic_finished", "elapsed_seconds", "resumed",
              "manifest_sha256", "non_contiguous", "timing_eligible"}
    numeric = ("started_at", "finished_at", "calendar_elapsed_seconds", "monotonic_started",
               "monotonic_finished", "elapsed_seconds")
    comparison._require(set(value) == fields and value["schedule"] == "serial"
                        and value["workers"] == 1 and type(value["workers"]) is int
                        and value["manifest_sha256"] == comparison.json_digest(request.manifest)
                        and value["non_contiguous"] is True and value["timing_eligible"] is False
                        and type(value["resumed"]) is bool
                        and all(type(value[name]) is float and math.isfinite(value[name]) for name in numeric)
                        and value["started_at"] == start["started_at"]
                        and value["monotonic_started"] == start["monotonic_started"]
                        and value["finished_at"] >= value["started_at"]
                        and value["monotonic_finished"] >= value["monotonic_started"]
                        and abs(value["calendar_elapsed_seconds"]
                                - (value["finished_at"] - value["started_at"])) < 0.001
                        and abs(value["elapsed_seconds"]
                                - (value["monotonic_finished"] - value["monotonic_started"])) < 0.001,
                        "saved serial timing is malformed, mismatched, or timing-eligible")
    return value


def _validate_saved_indexes(request: CampaignRequest, plan: carry.CarryForwardPlan,
                            present: set[str], snapshot: dict, timing: dict | None) -> None:
    names = [f"serial-{arm}.index.json" for arm in request.manifest["arms"]]
    found = [name for name in names if name in present]
    if not found:
        return
    comparison._require(timing is not None and snapshot["reserved_launches"] == request.launch_budget
                        and all(row["status"] == "complete" for row in snapshot["launches"]),
                        "saved evidence indexes cannot precede complete serial evidence")
    comparison._require(names[1] not in present or names[0] in present,
                        "saved candidate index cannot precede its baseline index")
    carried = set(plan.carried_case_ids)
    for arm, name in zip(request.manifest["arms"], names, strict=True):
        if name not in present:
            continue
        value = _saved_json(request.output, name, f"saved serial {arm} index")
        reports = [request.output / "serial" / arm / case["case_id"] / "report.json"
                   for case in request.manifest["roster"]
                   if arm != "baseline" or case["case_id"] not in carried]
        expected = _build_schedule_index(request, arm, reports, plan)
        comparison._require(value == expected, f"saved serial {arm} index changed")
        if arm == "baseline":
            carry.source_aware_union(value, request.manifest, "baseline")


def _validate_saved_publications(request: CampaignRequest, plan: carry.CarryForwardPlan,
                                 present: set[str], snapshot: dict) -> None:
    current = {(row["arm"], row["case_id"], row["trial_number"]): row
               for row in snapshot["launches"]}
    prior_rows: dict[tuple[str, str, int], dict] = {}
    interrupted = sorted(name for name in present
                         if re.fullmatch(r"interrupted-ledger-\d+\.json", name))
    for name in interrupted:
        value = _saved_json(request.output, name, "saved interrupted ledger")
        _validate_saved_ledger_snapshot(value, plan, request.launch_budget)
        comparison._require(0 < value["reserved_launches"] <= snapshot["reserved_launches"],
                            "saved interrupted ledger cannot exist for the current ledger state")
        rows = {}
        for row in value["launches"]:
            identity = (row["arm"], row["case_id"], row["trial_number"])
            latest = current.get(identity)
            comparison._require(latest is not None
                                and row["reserved_at"] == latest["reserved_at"]
                                and (row["status"] == "unknown"
                                     or row["status"] == latest["status"]
                                     and row["completed_at"] == latest["completed_at"]),
                                "saved interrupted ledger conflicts with the authoritative ledger")
            previous = prior_rows.get(identity)
            comparison._require(previous is None
                                or (previous["reserved_at"] == row["reserved_at"]
                                    and (previous["status"] == "unknown"
                                         or previous["status"] == row["status"]
                                         and previous["completed_at"] == row["completed_at"])),
                                "saved interrupted ledger regresses a prior terminal result")
            rows[identity] = row
        comparison._require(set(prior_rows) <= set(rows),
                            "saved interrupted ledgers regress reserved identities")
        prior_rows = rows
    if "ledger.json" in present:
        value = _saved_json(request.output, "ledger.json", "saved final ledger")
        _validate_saved_ledger_snapshot(value, plan, request.launch_budget, complete=True)
        required = {"serial.timing.json", "serial-baseline.index.json",
                    "serial-candidate.index.json"}
        comparison._require(value == snapshot and required <= present,
                            "saved final ledger lacks its exact completed serial publications")


def _inspect_carry_output(
    request: CampaignRequest, plan: carry.CarryForwardPlan | carry.MultiGenerationPlan,
) -> tuple[dict, dict, bytes] | None:
    """Validate an existing V4 resume root without changing it or its lease."""
    if isinstance(plan, carry.MultiGenerationPlan):
        comparison._require(not request.output.exists(),
                            "V5 carry-forward requires a fresh absent output root")
        return None
    try:
        status = os.lstat(request.output)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise ValueError(f"carry-forward output admission could not inspect its root: {exc}") from None
    comparison._require(stat.S_ISDIR(status.st_mode) and not stat.S_ISLNK(status.st_mode)
                        and status.st_uid == os.getuid()
                        and not status.st_mode & (stat.S_IWGRP | stat.S_IWOTH),
                        "carry-forward output root ownership or mode is unsafe")
    required = {"carry-forward-lineage.json", "manifest.json", "approval.json", "inventory.json",
                "baseline-description.txt", "candidate-description.txt", "ledger.sqlite3"}
    try:
        present = {path.name for path in request.output.iterdir()}
    except OSError as exc:
        raise ValueError(f"carry-forward output admission could not enumerate its root: {exc}") from None
    comparison._require(required <= present,
                        "partial carry-forward publication requires a newly reviewed output root")
    allowed = required | {"serial", "serial.start.json", "serial.timing.json",
                          "serial-baseline.index.json", "serial-candidate.index.json", "ledger.json"}
    comparison._require(all(name in allowed or re.fullmatch(r"interrupted-ledger-\d+\.json", name)
                            for name in present),
                        "carry-forward resume output contains an unrecognized artifact")
    try:
        inventory_bytes = request.inventory.read_bytes()
        description_bytes = {arm: request.descriptions[arm].read_bytes()
                             for arm in ("baseline", "candidate")}
    except OSError as exc:
        raise ValueError(f"carry-forward resume source input could not be read: {exc}") from None
    expected = {
        "carry-forward-lineage.json": _serialized_json(_carry_lineage_receipt(request, plan)),
        "manifest.json": _serialized_json(request.manifest),
        "approval.json": _serialized_json(request.approval),
        "inventory.json": inventory_bytes,
        "baseline-description.txt": description_bytes["baseline"],
        "candidate-description.txt": description_bytes["candidate"],
    }
    for name, payload in expected.items():
        observed = carry.read_external_file(
            request.output, {"path": name, "sha256": hashlib.sha256(payload).hexdigest()},
            f"carry-forward resume {name}", max_bytes=max(len(payload), 1))
        comparison._require(observed == payload, f"carry-forward resume {name} changed")
    ledger_reference = {"path": "ledger.sqlite3", "sha256": "0" * 64}
    carry._assert_sidecars_absent(request.output, ledger_reference)
    before = carry._read_external_path(request.output, Path("ledger.sqlite3"),
                                       "carry-forward resume ledger", max_bytes=2 * 1024 * 1024)
    try:
        authorization, snapshot = read_ledger_bytes(before)
    except (sqlite3.Error, TypeError, IndexError, KeyError, json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError(f"carry-forward resume ledger is unreadable: {exc}") from None
    comparison._require(authorization == {
        "manifest_sha256": comparison.json_digest(request.manifest),
        "approval_sha256": comparison.json_digest(request.approval),
        "launch_budget": request.launch_budget,
        "carry_forward_sha256": plan.component_sha256,
    }, "carry-forward resume ledger authorization changed")
    _validate_saved_ledger_snapshot(snapshot, plan, request.launch_budget)
    grouped: dict[tuple[str, str], set[int]] = {}
    for row in snapshot["launches"]:
        comparison._require(row["status"] == "complete",
                            "carry-forward resume contains a non-complete prior result")
        grouped.setdefault((row["arm"], row["case_id"]), set()).add(row["trial_number"])
    comparison._require(all(trials == {1, 2, 3} for trials in grouped.values()),
                        "carry-forward resume contains a partial case reservation")
    start = _validate_saved_start(request, present, snapshot)
    _validate_saved_serial_tree(request, present, snapshot)
    _validate_prior(request, snapshot=snapshot)
    timing = _validate_saved_timing(request, present, snapshot, start)
    _validate_saved_indexes(request, plan, present, snapshot, timing)
    _validate_saved_publications(request, plan, present, snapshot)
    after = carry._read_external_path(request.output, Path("ledger.sqlite3"),
                                      "carry-forward resume ledger", max_bytes=2 * 1024 * 1024)
    carry._assert_sidecars_absent(request.output, ledger_reference)
    comparison._require(before == after, "carry-forward resume ledger changed during admission")
    return authorization, snapshot, before


def _prepare_campaign(request: CampaignRequest,
                      plan: carry.CarryForwardPlan | carry.MultiGenerationPlan | None,
                      admission: tuple[dict, dict, bytes] | None = None) -> CampaignLedger:
    if plan is not None:
        _publish_carry_request(request, plan)
    else:
        request.output.mkdir(parents=True, exist_ok=True)
    manifest_path = request.output / "manifest.json"
    if manifest_path.exists():
        comparison._require(comparison.read_json(manifest_path) == request.manifest, "frozen manifest changed on resume")
    else:
        write_json_once(manifest_path, request.manifest)
    approval_path = request.output / "approval.json"
    if approval_path.exists():
        comparison._require(comparison.read_json(approval_path) == request.approval, "frozen approval changed on resume")
    else:
        write_json_once(approval_path, request.approval)
    _copy_input(request.inventory, request.output / "inventory.json")
    for arm in request.manifest["arms"]:
        _copy_input(request.descriptions[arm], request.output / f"{arm}-description.txt")
    ledger = CampaignLedger(request.output / "ledger.sqlite3", comparison.json_digest(request.manifest),
                            request.approval, request.launch_budget,
                            carry_forward=request.carry_forward, admitted=admission)
    ledger.require_reconciled()
    comparison._require(all(row["status"] == "complete" for row in ledger.snapshot()["launches"]), "prior invalid native results require a newly reviewed campaign; no retries authorized")
    return ledger


def _same_carry_plan(expected: carry.CarryForwardPlan | carry.MultiGenerationPlan | None,
                     observed: carry.CarryForwardPlan | carry.MultiGenerationPlan | None) -> None:
    comparison._require((expected is None) == (observed is None)
                        and (expected is None or observed.component_sha256 == expected.component_sha256
                             and observed.carried_trials == expected.carried_trials
                             and observed.fresh_trials == expected.fresh_trials),
                        "carry-forward lineage changed before dispatch")


def _prepared_lease_activation(lease: _LeaseState, ledger: CampaignLedger,
                               admission: tuple[dict, dict, bytes] | None):
    if admission is None:
        lease.activate(ledger)
        return None
    return lambda: None if lease.active else lease.activate(ledger)


def _publish_ledger_snapshot(output: Path, snapshot: dict, ledger: CampaignLedger,
                             activate_lease=None) -> None:
    if output.exists():
        comparison._require(comparison.read_json(output) == snapshot,
                            "final immutable ledger changed")
        return
    def publish():
        if activate_lease is not None:
            activate_lease()
        write_json_once(output, snapshot)
    if activate_lease is None:
        publish()
    else:
        ledger.prepare_publication(publish)


def _run_under_lease(request: CampaignRequest, schedules: list[tuple[str, int]],
                     plan: carry.CarryForwardPlan | carry.MultiGenerationPlan | None, lease: _LeaseState,
                     ledger: CampaignLedger | None = None) -> CampaignLedger:
    leased_schedules = _validate_request(request, under_global_lease=True)
    comparison._require(leased_schedules == schedules,
                        "campaign request changed while the global lease was acquired")
    leased_plan = _validate_carry_forward_request(
        request, request.manifest, under_global_lease=True)
    _same_carry_plan(plan, leased_plan)
    admission = None
    if leased_plan is not None:
        admission = _inspect_carry_output(request, leased_plan)
    activate_lease = None
    if ledger is None:
        ledger = _prepare_campaign(request, plan, admission)
        activate_lease = _prepared_lease_activation(lease, ledger, admission)
    if leased_plan is not None:
        carry.validate_fresh_ledger(leased_plan, ledger.snapshot()["launches"])
    stop = threading.Event()
    previous = {signum: signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)}
    lease_entry_snapshot = ledger.snapshot()
    def lineage_guard():
        current = _validate_carry_forward_request(
            request, request.manifest, under_global_lease=True)
        comparison._require(current is not None and plan is not None
                            and current.component_sha256 == plan.component_sha256
                            and current.carried_trials == plan.carried_trials
                            and current.fresh_trials == plan.fresh_trials,
                            "carry-forward lineage changed immediately before reservation")
        carry.validate_fresh_ledger(current, ledger.snapshot()["launches"])
    try:
        _validate_prior(request, ledger)
        for signum in previous:
            signal.signal(signum, lambda _signum, _frame: stop.set())
        for schedule, workers in schedules:
            _run_schedule(request, schedule, workers, ledger, stop, leased_plan,
                          lineage_guard if leased_plan is not None else None,
                          activate_lease)
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)
        snapshot = ledger.snapshot()
        completed = snapshot["reserved_launches"] == request.launch_budget and all(
            row["status"] == "complete" for row in snapshot["launches"])
        if plan is None or completed or snapshot["reserved_launches"] > lease_entry_snapshot["reserved_launches"]:
            output = request.output / ("ledger.json" if completed else f"interrupted-ledger-{time.time_ns()}.json")
            _publish_ledger_snapshot(output, snapshot, ledger, activate_lease)
    return ledger


def run_campaign(request: CampaignRequest) -> dict:
    schedules = _validate_request(request)
    plan = _validate_carry_forward_request(request, request.manifest)
    if plan is not None:
        _inspect_carry_output(request, plan)
        _inspect_global_lease(request)
        with _global_lease(request) as lease:
            ledger = _run_under_lease(request, schedules, plan, lease)
    else:
        ledger = _prepare_campaign(request, None)
        with _global_lease(request, ledger) as lease:
            ledger = _run_under_lease(request, schedules, None, lease, ledger)
    result = {"complete": True, "qualification_scope": request.manifest["qualification_scope"],
            "reserved_launches": ledger.snapshot()["reserved_launches"], "qualification": False,
            "next": "Run provider-free comparison or pilot qualification; launch completion alone is not qualification."}
    if plan is not None:
        result.update({"historical_charged_launches": plan.historical_charged_launches,
                       "carried_trials": len(plan.carried_trials),
                       "fresh_launch_ceiling": request.launch_budget,
                       "maximum_total_charged_attempts": (
                           plan.maximum_total_charged_attempts
                           if isinstance(plan, carry.MultiGenerationPlan) else 1305),
                       "carry_forward": True, "non_contiguous": True, "timing_eligible": False})
    return result
