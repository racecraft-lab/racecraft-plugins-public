"""Bounded invocation of the two existing native runners, never arbitrary commands."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import threading
import time

import trigger_comparison as comparison
from trigger_campaign import CampaignLedger, QualifiedConcurrency, read_ledger, validate_approval, worker_limit
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


def concurrency_binding(manifest: dict) -> str:
    return comparison.json_digest({"pins": manifest["pins"], "identities": manifest["identities"]})


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
    child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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


def _validate_request(request: CampaignRequest) -> list[tuple[str, int]]:
    manifest = request.manifest
    comparison.validate_experiment(manifest)
    validate_approval(request.approval, comparison.json_digest(manifest), request.launch_budget)
    destination = manifest.get("output_directory")
    comparison._require(isinstance(destination, str) and Path(destination).is_absolute()
        and destination == str(Path(destination).resolve()) and request.output.resolve() == Path(destination),
        "approved manifest must bind this exact canonical output directory; changing it cannot reset the campaign budget")
    comparison._require(type(request.timeout) is int and request.timeout > 0, "invalid per-trial timeout")
    comparison._require(comparison.snapshot_identities(comparison.measurement_snapshot()) == manifest["identities"], "frozen public inputs changed before launch")
    comparison._require(hashlib.sha256(request.inventory.read_bytes()).hexdigest() == manifest["inventory_sha256"], "frozen inventory changed before launch")
    comparison.validate_inventory_binding(manifest, comparison.read_json(request.inventory))
    for arm in manifest["arms"]:
        comparison._require(hashlib.sha256(request.descriptions[arm].read_bytes()).hexdigest() == manifest["controlled_difference"][f"{arm}_sha256"], "controlled description changed before launch")
    if manifest["qualification_scope"] == "pilot":
        inventory = comparison.read_json(request.inventory)
        comparison._require(manifest["arms"] == ["candidate"] and {row["case_id"] for row in manifest["roster"]} == set(inventory["pilot_case_ids"]), "pilot roster differs from protected eight-case selection")
        schedules = [("serial", 1), ("two-worker", 2)]
    else:
        profile = qualify_pilot(request.pilot_evidence) if request.pilot_evidence else None
        schedules = [("serial" if request.workers == 1 else "two-worker", worker_limit(request.workers, profile, concurrency_binding(manifest)))]
    launches = len(manifest["roster"]) * 3 * len(manifest["arms"]) * len(schedules)
    comparison._require(request.launch_budget == launches, "approval budget must equal the exact planned launch count")
    return schedules


def _run_schedule(request: CampaignRequest, schedule: str, workers: int, ledger: CampaignLedger, stop: threading.Event) -> None:
    start_path = request.output / f"{schedule}.start.json"
    resumed = start_path.exists()
    if not start_path.exists():
        write_json_once(start_path, {"started_at": time.time(), "monotonic_started": time.monotonic(), "manifest_sha256": comparison.json_digest(request.manifest)})
    start = comparison.read_json(start_path)
    comparison._require(start["manifest_sha256"] == comparison.json_digest(request.manifest), "schedule start belongs to another manifest")
    started_at = start["started_at"]
    prior = {(row["arm"], row["case_id"]): row["status"] for row in ledger.snapshot()["launches"]}
    def run(job):
        arm, case = job
        identity = f"{schedule}:{arm}"
        if stop.is_set() or prior.get((identity, case["case_id"])) == "complete":
            return
        ledger.reserve_case(identity, case["case_id"])
        directory = request.output / schedule / arm / case["case_id"]
        try:
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
    timing = request.output / f"{schedule}.timing.json"
    if not timing.exists():
        finished_at = time.time()
        monotonic_finished = time.monotonic()
        write_json_once(timing, {"schedule": schedule, "workers": workers, "started_at": started_at,
            "finished_at": finished_at, "calendar_elapsed_seconds": finished_at - started_at,
            "monotonic_started": start["monotonic_started"], "monotonic_finished": monotonic_finished,
            "elapsed_seconds": monotonic_finished - start["monotonic_started"], "resumed": resumed,
            "manifest_sha256": comparison.json_digest(request.manifest)})
    for arm in request.manifest["arms"]:
        reports = [request.output / schedule / arm / case["case_id"] / "report.json" for case in request.manifest["roster"]]
        index = comparison.build_evidence_index(request.manifest, arm, request.output, reports,
            request.output / "inventory.json", request.output / f"{arm}-description.txt")
        index_path = request.output / f"{schedule}-{arm}.index.json"
        if index_path.exists():
            comparison._require(comparison.read_json(index_path) == index, "published index changed on resume")
        else:
            write_json_once(index_path, index)


def _validate_prior(request: CampaignRequest, ledger: CampaignLedger) -> None:
    rows = ledger.snapshot()["launches"]
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


@contextmanager
def _global_lease(request: CampaignRequest, ledger: CampaignLedger, *, reconciling: bool = False):
    comparison._require(os.name == "posix", "native campaigns require the qualified POSIX ownership contract")
    import fcntl
    # Deliberately independent of TMPDIR, campaign roots, and worktree isolation.
    path = Path("/tmp") / f"speckit-trigger-native-{os.getuid()}.lock"
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "r+b") as lock:
        info = os.fstat(lock.fileno())
        comparison._require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) & 0o077 == 0, "unsafe global campaign lock ownership")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("another native campaign owns the global launch ceiling") from None
        previous = lock.read()
        if previous:
            lease = json.loads(previous)
            comparison._require(lease.get("state") == "idle" or reconciling and lease.get("campaign") == str(request.output), "an interrupted global campaign requires owned-process/artifact reconciliation before any new launch")
        def publish(state):
            lock.seek(0)
            lock.write(json.dumps({"schema_version": "trigger-global-lease/v1", "state": state, "campaign": str(request.output)}).encode())
            lock.truncate()
            lock.flush()
            os.fsync(lock.fileno())
        publish("active")
        try:
            yield
        finally:
            publish("unknown" if ledger.snapshot()["unknown_launches"] else "idle")
            fcntl.flock(lock, fcntl.LOCK_UN)


def _require_absent(pid: int, *, group: bool = False) -> None:
    comparison._require(type(pid) is int and pid > 0 and pid != os.getpid(), "invalid owned process identity")
    try:
        if group:
            os.killpg(pid, 0)
        else:
            os.kill(pid, 0)
    except ProcessLookupError:
        return
    raise ValueError("an owned process identity is still live; reconciliation never kills or relaunches it")


def reconcile_campaign(request: CampaignRequest) -> dict:
    """Inspect retained processes/artifacts only; settle accounting without launching."""
    _validate_request(request)
    comparison._require((request.output / "ledger.sqlite3").is_file(), "no existing campaign ledger to reconcile")
    ledger = CampaignLedger(request.output / "ledger.sqlite3", comparison.json_digest(request.manifest), request.approval, request.launch_budget)
    with _global_lease(request, ledger, reconciling=True):
        unresolved = {(row["arm"], row["case_id"]) for row in ledger.snapshot()["launches"] if row["status"] == "unknown"}
        for identity, case_id in sorted(unresolved):
            schedule, arm = identity.split(":", 1)
            directory = request.output / schedule / arm / case_id
            launch = comparison.read_json(directory / "launch.json")
            _require_absent(launch["pid"])
            receipt = comparison.read_json(directory / "evidence/arm-cleanup.json")
            comparison._require(not Path(receipt["workspace"]).exists(), "owned workspace remains after claimed cleanup")
            for path in (directory / "evidence").glob("*.trial.json"):
                _require_absent(comparison.read_json(path)["child_pgid"], group=True)
            status = _settle_case(directory, receipt["runner_exit_code"])
            ledger.finish_case(identity, case_id, status)
    return {"reconciled": True, "native_launches": 0, "ledger": ledger.snapshot()}


def run_campaign(request: CampaignRequest) -> dict:
    schedules = _validate_request(request)
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
    ledger = CampaignLedger(request.output / "ledger.sqlite3", comparison.json_digest(request.manifest), request.approval, request.launch_budget)
    ledger.require_reconciled()
    comparison._require(all(row["status"] == "complete" for row in ledger.snapshot()["launches"]), "prior invalid native results require a newly reviewed campaign; no retries authorized")
    stop = threading.Event()
    previous = {signum: signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)}
    with _global_lease(request, ledger):
        try:
            _validate_prior(request, ledger)
            for signum in previous:
                signal.signal(signum, lambda _signum, _frame: stop.set())
            for schedule, workers in schedules:
                _run_schedule(request, schedule, workers, ledger, stop)
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)
            snapshot = ledger.snapshot()
            completed = snapshot["reserved_launches"] == request.launch_budget and all(row["status"] == "complete" for row in snapshot["launches"])
            output = request.output / ("ledger.json" if completed else f"interrupted-ledger-{time.time_ns()}.json")
            if not output.exists():
                write_json_once(output, snapshot)
            else:
                comparison._require(comparison.read_json(output) == snapshot, "final immutable ledger changed")
    return {"complete": True, "qualification_scope": request.manifest["qualification_scope"],
            "reserved_launches": ledger.snapshot()["reserved_launches"], "qualification": False,
            "next": "Run provider-free comparison or pilot qualification; launch completion alone is not qualification."}
