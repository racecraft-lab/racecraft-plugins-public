"""Durable run accounting. This is a budget gate, never an authorization grant.

Native orchestration still owns approvals, dispatch, and recovered tool events.
No user-supplied boolean can exclude wall time or reset a consumed reservation.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any

from .formal.selection import require_text as require_nonempty_text

SCHEMA = "execution-control/v1"
KINDS = {"implementation", "corrective", "verification", "infrastructure"}
OUTCOMES = {"completed", "failed", "unknown", "expected_tdd_red"}
CORRECTIVE_REFUSALS = {"failure_family_budget_exhausted", "corrective_run_budget_exhausted"}
CLASS_CHANGE_KINDS = {"test_timeout"}
CLASS_FOLLOW_UP_LIMIT = 2
# Review fixes inside one increment's own owned paths get this many rounds per
# increment, outside the run-wide corrective budget.
INCREMENT_REVIEW_ROUNDS = 2
# A planning gate's own remediation gets this many rounds per gate, outside the
# run-wide corrective budget, when every path is a planning document of the
# bound feature. Anything else (code, tests, formal models, contracts) is run-wide.
GATE_REMEDIATION_ROUNDS = 2
REMEDIATION_GATES = ("G2", "G3", "G4", "G5", "G6", "G7")
# A test-only fix confined to test files its own increment edited earlier in the run
# gets this many rounds per increment, outside the run-wide corrective budget.
TEST_FIX_ROUNDS = 1
# A snapshot of the worktree the runner takes itself: HEAD and every path git reports as changed.
WORKTREE_SNAPSHOT_KEYS = {"head", "dirty"}
PLANNING_DOCUMENTS = frozenset({"spec.md", "plan.md", "research.md", "tasks.md", "data-model.md", "quickstart.md",
                                ".process/task-execution.json"})
# A refusal because an allowance is spent defers the blocked unit to the end-of-run
# request instead of stopping the run. Each reason names the kind of unit it blocks.
DEFER_REASONS = {"failure_family_budget_exhausted": "failure_family",
                 "corrective_run_budget_exhausted": "failure_family",
                 "corrective_cycle_failed_no_nested_retry": "failure_family",
                 "corrective_cycle_already_closed": "failure_family",
                 "increment_review_allowance_exhausted": "increment",
                 "gate_remediation_allowance_exhausted": "gate",
                 "failure_class_allowance_exhausted": "failure_class"}
DEFERRAL_KEYS = {"dispatch_id", "reason", "unit_kind", "unit", "deferred_at"}
# A later completed dispatch for the same unit resolves a deferral. The runner stamps
# the resolution itself when it records that completion; no request can name one.
DEFERRAL_RESOLUTION_KEYS = {"resolved_by", "resolved_at"}
# Verification evidence the runner itself records; never a helper-request action.
RECORD_FAILING_CHECKS = "record-failing-checks"
FAILING_CHECK_KEYS = {"command_id", "command_sha256", "format", "failing", "passing", "checks_run", "output_sha256",
                      "recorded_at"}
# The runner reads the head it verified and whether the worktree matched it. Earlier records lack both.
FAILING_CHECK_OPTIONAL_KEYS = {"head_sha", "worktree_clean"}
# A failed unit climbs a fixed ladder before it is exhausted. Tier 1 is the current agent's
# repair loop inside its existing allowance (corrective_cycles and the unit allowances). Tier 2
# is a fresh agent with a different approach, guided by a consensus diagnosis. Tier 3 is the
# strongest model at max effort with the full failure history. Each retry is one corrective
# ledger dispatch that draws on the unit's escalation record, never on `corrective_cycles`, and
# the record shows the tier reached. Tier 3 has a per-run cap. A unit is a deferral's unit, or
# `gate_failure` (the command digest of a verification the runner fingerprinted as failing).
ESCALATION_UNIT_KINDS = {*DEFER_REASONS.values(), "gate_failure"}
ESCALATION_TIERS = (2, 3)
ESCALATION_TIER3_CAP = 3
ESCALATION_KEYS = {"unit_kind", "unit", "tier", "dispatches"}
ESCALATION_DISPATCH_KEYS = {"tier", "dispatch_id", "reserved_at"}
# `finalize-run` counts how often it saw the same head and gate unfinished, so a stop is
# proved by the runner's own record of earlier cycles and never by a caller's claim.
FINALIZE_OBSERVATION_KINDS = ("missing_gate", "harness_error")
FINALIZE_OBSERVATION_CAP = 3
# A metadata-only correction rewords task definitions without changing scope. The
# runner proves it against the committed baseline itself and admits it once per
# task per run without spending a corrective cycle.
METADATA_CORRECTION_KEYS = {"dispatch_id", "task_ids", "tasks_file", "baseline_sha256", "corrected_sha256",
                            "admitted_at"}
METADATA_TASK_LINE = re.compile(r"^(\s*-\s+\[[ xX]\]\s+(T[0-9]{3,})\s+(?:\[P\]\s*|\[US[1-9][0-9]*\]\s*)*)(.*)$")
RUNNER_BYPRODUCT_DIRECTORIES = frozenset({(".process", "execution-control"), (".process", "verification"),
                                          (".process", "task-results")})


def is_runner_byproduct(relative: str) -> bool:
    """True for a repo-relative path inside a runner-owned ledger or evidence directory."""
    parts = PurePosixPath(relative).parts
    return any(pair in RUNNER_BYPRODUCT_DIRECTORIES for pair in zip(parts, parts[1:], strict=False))


def is_implementation_notes(relative: str) -> bool:
    """True only for `specs/<feature>/.process/implementation-notes.md` (#801).

    The autopilot appends to it after every task, so it lags the checkpoint
    commit that publishes it. Unlike a byproduct it is committed; it is only
    exempt from the clean-worktree check and the per-PR path budget.
    """
    parts = PurePosixPath(relative).parts
    return (len(parts) == 4 and parts[0] == "specs"
            and parts[2:] == (".process", "implementation-notes.md"))


def workflow_process_directory(workflow_name: str) -> PurePosixPath:
    """The workflow's `.process` directory, without doubling a `.process` parent."""
    parent = PurePosixPath(workflow_name).parent
    return parent if parent.name == ".process" else parent / ".process"


def default_ledger_directory(workflow_name: str) -> str:
    """The workflow's ledger directory, without doubling a `.process` parent."""
    return workflow_process_directory(workflow_name).joinpath("execution-control").as_posix()


def evidence_directory(workflow_name: str) -> str:
    """The workflow's verification evidence directory, beside its ledger directory."""
    return workflow_process_directory(workflow_name).joinpath("verification").as_posix()


def confined_path(root: Path, value: str) -> Path:
    """Reject traversal and every symlink component, including dangling links."""
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError("path must be a nonempty repository-relative path")
    parts = Path(value).parts
    if any(part in {"..", ".git"} for part in parts):
        raise ValueError("path traversal or git metadata is not permitted")
    path = root.resolve()
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("symlink paths are not permitted")
    return path


def ignore_owned_directory(directory: Path) -> None:
    """Keep a runner-owned directory out of every commit, `git add -A` included."""
    directory.mkdir(parents=True, exist_ok=True)
    marker = directory / ".gitignore"
    if marker.is_dir() and not marker.is_symlink():
        raise ValueError(f"{marker} is not a regular file; remove it so the runner can write its ignore rule")
    if marker.is_symlink() or not marker.is_file() or marker.read_bytes() != b"*\n":
        marker.unlink(missing_ok=True)
        marker.write_bytes(b"*\n")


def durable_json(path: Path, value: dict[str, Any]) -> None:
    """Publish a complete record, with data and containing directory flushed."""
    ignore_owned_directory(path.parent)
    descriptor, temporary = tempfile.mkstemp(prefix=".execution-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        if os.name == "posix":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


@contextmanager
def exclusive_ledger(path: Path):
    """Concurrent or interrupted writers fail closed; never steal a stale lock."""
    ignore_owned_directory(path.parent)
    lock = path.with_suffix(".lock")
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise ValueError("ledger locked; reconcile the prior owner before retrying") from exc
    try:
        yield
    finally:
        lock.rmdir()


def require_text(value: Any, name: str) -> str:
    text = require_nonempty_text(value, name)
    if len(text) > 240:
        raise ValueError(f"{name} exceeds 240 characters")
    return text


def initial_ledger(spec: Path, now: float) -> dict[str, Any]:
    text = spec.read_text(encoding="utf-8") if spec.is_file() else ""
    invariants = sorted(set(re.findall(r"\b(?:FR|NFR|INV)-[A-Za-z0-9]+\b", text)))
    return {"schema_version": SCHEMA, "run_id": uuid.uuid4().hex,
            "started_at": now, "slice_started_at": now, "last_observed_at": now,
            "checkpoint_at": now, "approved_invariants": invariants,
            "corrective_cycles": 0, "reservations": {}, "dispatches": {},
            "excluded_intervals": [], "active_wait": None, "authorization_granted": False}


def _validate_workflow_identity(value: Any) -> dict[str, Any]:
    keys = {"original_workflow_file", "current_workflow_file", "relocation_event_ids"}
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("execution ledger has no valid workflow identity")
    workflow_files = [require_text(value.get(key), key) for key in keys if key.endswith("_workflow_file")]
    if any(Path(item).is_absolute() or Path(item).as_posix() != item or
           any(part in {"..", ".git"} for part in Path(item).parts) for item in workflow_files):
        raise ValueError("execution ledger workflow identity is not canonical")
    event_ids = value.get("relocation_event_ids")
    if not isinstance(event_ids, list) or not all(isinstance(event_id, str) and event_id.strip() for event_id in event_ids):
        raise ValueError("invalid workflow relocation event registry")
    if len(event_ids) != len(set(event_ids)):
        raise ValueError("duplicate workflow relocation event")
    return value


def _validate_invariant_binding(ledger: dict[str, Any]) -> None:
    if "invariant_binding" not in ledger:
        return
    binding = ledger["invariant_binding"]
    if (not isinstance(binding, dict) or set(binding) != {"spec_file", "spec_sha256", "bound_at"}
            or not ledger["approved_invariants"]):
        raise ValueError("invalid invariant binding")
    bound_spec = require_text(binding["spec_file"], "bound spec_file")
    if (Path(bound_spec).is_absolute() or Path(bound_spec).as_posix() != bound_spec
            or any(part in {"..", ".git"} for part in Path(bound_spec).parts)
            or not isinstance(binding["spec_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", binding["spec_sha256"])):
        raise ValueError("invalid invariant binding provenance")
    if (type(binding["bound_at"]) not in (int, float)
            or not ledger["started_at"] <= binding["bound_at"] < float("inf")):
        raise ValueError("invalid invariant binding clock")


def validate_ledger(value: Any) -> None:
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA:
        raise ValueError("invalid execution ledger schema")
    require_text(value.get("run_id"), "run_id")
    _validate_workflow_identity(value.get("workflow_identity"))
    for key in ("started_at", "slice_started_at", "last_observed_at", "checkpoint_at"):
        if type(value.get(key)) not in (int, float) or not 0 <= value[key] < float("inf"):
            raise ValueError(f"invalid ledger clock: {key}")
    if value.get("authorization_granted") is not False:
        raise ValueError("budget gates cannot grant authorization")
    validate_intervals(value)
    _validate_corrective_state(value)
    _validate_corrective_epochs(value)
    _validate_escalation_cap(value)
    _validate_finalize_observations(value)


def _validate_corrective_state(value: dict[str, Any]) -> None:
    """One allowance's counters, reservations, dispatches, and operator records."""
    if type(value.get("corrective_cycles")) is not int or not 0 <= value["corrective_cycles"] <= 2:
        raise ValueError("invalid corrective counter")
    if not isinstance(value.get("approved_invariants"), list) or not all(isinstance(v, str) for v in value["approved_invariants"]):
        raise ValueError("invalid invariant registry")
    _validate_invariant_binding(value)
    if not isinstance(value.get("reservations"), dict) or not isinstance(value.get("dispatches"), dict):
        raise ValueError("invalid execution reservations")
    if len(value["reservations"]) != value["corrective_cycles"]:
        raise ValueError("reservation counter disagrees with ledger")
    exception_reservation = _validate_corrective_exception(value)
    allowances = _validate_unit_allowances(value, "increment_allowances", "increment", INCREMENT_REVIEW_ROUNDS)
    test_fixes = _validate_unit_allowances(value, "test_fix_allowances", "test_fix", TEST_FIX_ROUNDS)
    metadata_corrections = _validate_metadata_corrections(value)
    _validate_deferrals(value)
    gate_allowances = _validate_gate_allowances(value)
    escalations = _validate_escalations(value)
    families = [item.get("family") for item in value["reservations"].values() if isinstance(item, dict)]
    if len(families) != len(value["reservations"]) or len(set(families)) != len(families):
        raise ValueError("duplicate or malformed corrective family")
    for dispatch_id, item in value["dispatches"].items():
        if not isinstance(item, dict) or item.get("kind") not in KINDS or item.get("outcome") not in OUTCOMES | {"reserved", "running"}:
            raise ValueError("invalid dispatch record")
        if "failing_checks" in item:
            _validate_failing_checks(item["failing_checks"], item)
        if type(item.get("reconciliations")) is not int or not 0 <= item["reconciliations"] <= 1:
            raise ValueError("invalid reconciliation counter")
        reservation = item.get("reservation_id")
        if sum(key in item for key in ("increment", "gate", "metadata_correction", "test_fix", "escalation")) > 1:
            raise ValueError("a corrective dispatch draws on one allowance, not an increment and a gate")
        _validate_edit_records(item)
        if "escalation" in item or "escalation_tier" in item:
            listed = {(entry["tier"], entry["dispatch_id"])
                      for entry in escalations.get(str(item.get("escalation")), {}).get("dispatches", [])}
            if (item["kind"] != "corrective" or reservation is not None
                    or (item.get("escalation_tier"), dispatch_id) not in listed):
                raise ValueError("escalation dispatch is not recorded in its escalation allowance")
        elif "test_fix" in item:
            if (item["kind"] != "corrective" or reservation is not None
                    or dispatch_id not in test_fixes.get(item["test_fix"], {}).get("dispatch_ids", [])):
                raise ValueError("test-fix dispatch is not recorded in its increment's test-fix allowance")
        elif "metadata_correction" in item:
            if (item["kind"] != "corrective" or reservation is not None
                    or metadata_corrections.get(dispatch_id) != item["metadata_correction"]):
                raise ValueError("metadata correction dispatch is not recorded in the metadata corrections")
        elif "increment" in item:
            if (item["kind"] != "corrective" or reservation is not None
                    or dispatch_id not in allowances.get(item["increment"], {}).get("dispatch_ids", [])):
                raise ValueError("increment review dispatch is not recorded in its increment allowance")
        elif "gate" in item:
            if (item["kind"] != "corrective" or reservation is not None
                    or dispatch_id not in gate_allowances.get(item["gate"], {}).get("dispatch_ids", [])):
                raise ValueError("gate remediation dispatch is not recorded in its gate allowance")
        elif (item["kind"] == "corrective" and reservation not in value["reservations"]
                and (exception_reservation is None or reservation != exception_reservation)):
            raise ValueError("corrective dispatch has no reservation")
    _validate_progress(value)
    validate_recovery_records(value)
    validate_continuation_records(value)


EPOCH_STATE_KEYS = ("corrective_cycles", "reservations", "dispatches", "approved_invariants")
EPOCH_OPTIONAL_KEYS = ("invariant_binding", "corrective_exception", "increment_allowances", "gate_allowances",
                       "deferred", "metadata_corrections", "test_fix_allowances", "escalation_allowances")
# An operator's explicit stage start closes the prior stage's allowance under a
# runner-derived event ID, so each stage opens at most one allowance per run.
STAGE_EPOCH_STAGES = ("implement",)
STAGE_EPOCH_PREFIX = "stage-transition:"


def _epoch_view(ledger: dict[str, Any], epoch: dict[str, Any]) -> dict[str, Any]:
    """The ledger as it stood when an archived allowance was current."""
    view = {key: value for key, value in ledger.items()
            if key not in {"corrective_epochs", *EPOCH_STATE_KEYS, *EPOCH_OPTIONAL_KEYS}}
    view.update({key: epoch[key] for key in (*EPOCH_STATE_KEYS, *EPOCH_OPTIONAL_KEYS) if key in epoch})
    return view


def _validate_corrective_epochs(ledger: dict[str, Any]) -> None:
    """Archived allowances stay valid, settled, and disjoint from the current one."""
    if "corrective_epochs" not in ledger:
        return
    epochs = ledger["corrective_epochs"]
    if not isinstance(epochs, list) or not epochs:
        raise ValueError("invalid corrective epoch history")
    required = {*EPOCH_STATE_KEYS, "epoch_event_id", "closed_at"}
    allowed = required | set(EPOCH_OPTIONAL_KEYS) | {"stage_transition"}
    dispatch_ids = set(ledger["dispatches"])
    corrected_tasks = {task for entry in ledger.get("metadata_corrections", []) for task in entry["task_ids"]}
    event_ids = _consumed_native_event_ids({key: value for key, value in ledger.items() if key != "corrective_epochs"})
    previous_close = ledger["started_at"]
    for epoch in epochs:
        if not isinstance(epoch, dict) or not required <= set(epoch) <= allowed:
            raise ValueError("invalid corrective epoch record")
        stage = epoch.get("stage_transition")
        if (("stage_transition" in epoch or str(epoch["epoch_event_id"]).startswith(STAGE_EPOCH_PREFIX))
                and (stage not in STAGE_EPOCH_STAGES or epoch["epoch_event_id"] != STAGE_EPOCH_PREFIX + stage)):
            raise ValueError("invalid stage transition epoch")
        closed_at = epoch["closed_at"]
        if type(closed_at) not in (int, float) or not previous_close <= closed_at < float("inf"):
            raise ValueError("invalid corrective epoch clock")
        previous_close = closed_at
        view = _epoch_view(ledger, epoch)
        _validate_corrective_state(view)
        if any(item["outcome"] not in OUTCOMES - {"unknown"} for item in view["dispatches"].values()):
            raise ValueError("corrective epoch closed with unsettled dispatches")
        if dispatch_ids & set(view["dispatches"]):
            raise ValueError("dispatch id reused across corrective epochs")
        dispatch_ids.update(view["dispatches"])
        epoch_tasks = {task for entry in view.get("metadata_corrections", []) for task in entry["task_ids"]}
        if corrected_tasks & epoch_tasks:
            raise ValueError("a task was corrected twice as metadata-only in one run")
        corrected_tasks.update(epoch_tasks)
        epoch_event = require_text(epoch["epoch_event_id"], "epoch_event_id")
        owned = _consumed_native_event_ids(view) - set(ledger["workflow_identity"]["relocation_event_ids"])
        owned -= {event for interval in ledger["excluded_intervals"] for event in (interval["start_event"], interval["end_event"])}
        if ledger.get("active_wait"):
            owned.discard(ledger["active_wait"]["start_event"])
        if epoch_event in owned or (owned | {epoch_event}) & event_ids:
            raise ValueError("native event reused across corrective epochs")
        event_ids.update(owned | {epoch_event})


def _used_dispatch_ids(ledger: dict[str, Any]) -> set[str]:
    used = set(ledger["dispatches"])
    for epoch in ledger.get("corrective_epochs", []):
        used.update(epoch["dispatches"])
    return used


def _validate_corrective_exception(ledger: dict[str, Any]) -> str | None:
    """Validate the run's optional single operator-approved corrective exception."""
    if "corrective_exception" not in ledger:
        return None
    record = ledger["corrective_exception"]
    keys = {"reservation_id", "dispatch_id", "failure_invariant", "refusal_reason", "scope_sha256",
            "spec_sha256", "operator_exception_event_id", "authorized_at"}
    if not isinstance(record, dict) or set(record) - {"failure_class"} != keys:
        raise ValueError("invalid corrective exception")
    reservation = require_text(record["reservation_id"], "corrective exception reservation_id")
    dispatch_id = require_text(record["dispatch_id"], "corrective exception dispatch_id")
    event_id = require_text(record["operator_exception_event_id"], "operator_exception_event_id")
    if event_id in _consumed_native_event_ids({key: value for key, value in ledger.items()
                                               if key != "corrective_exception"}):
        raise ValueError("corrective exception event id was already consumed")
    if (record["failure_invariant"] not in ledger["approved_invariants"]
            or record["refusal_reason"] not in CORRECTIVE_REFUSALS
            or not all(isinstance(record[key], str) and re.fullmatch(r"[0-9a-f]{64}", record[key])
                       for key in ("scope_sha256", "spec_sha256"))
            or record["spec_sha256"] != ledger.get("invariant_binding", {}).get("spec_sha256")
            or type(record["authorized_at"]) not in (int, float)
            or not ledger["started_at"] <= record["authorized_at"] < float("inf")
            or reservation in ledger["reservations"]):
        raise ValueError("invalid corrective exception binding")
    follow_ups = _validate_failure_class(record["failure_class"]) if "failure_class" in record else []
    # The ledger is saved with sorted keys, so the recorded list, not dict order, is the sequence.
    members = [dispatch_id, *follow_ups]
    owned = {key for key, item in ledger["dispatches"].items()
             if isinstance(item, dict) and item.get("reservation_id") == reservation}
    if (len(set(members)) != len(members) or owned != set(members)
            or any(ledger["dispatches"][member].get("kind") != "corrective" for member in members)):
        raise ValueError("corrective exception must own its approved corrective dispatches")
    if any(ledger["dispatches"][member].get("outcome") != "completed" for member in members[:-1]):
        raise ValueError("a class follow-up requires every earlier class correction to have completed")
    return reservation


def _class_scope(value: Any) -> dict[str, str]:
    """One test file, one normalized failure signature, and one change kind."""
    keys = {"test_file", "failure_signature", "change_kind"}
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("failure_class requires exactly test_file, failure_signature, and change_kind")
    from .helpers.read_only import is_test_path

    test_file = require_text(value["test_file"], "failure_class test_file")
    path = PurePosixPath(test_file)
    if (path.is_absolute() or path.as_posix() != test_file or any(part in {"..", ".git"} for part in path.parts)
            or is_runner_byproduct(test_file) or not is_test_path(test_file)):
        raise ValueError("failure_class test_file must be a canonical repository-relative test file")
    if value["change_kind"] not in CLASS_CHANGE_KINDS:
        raise ValueError("unsupported failure_class change_kind")
    return {"test_file": test_file,
            "failure_signature": require_text(value["failure_signature"], "failure_class failure_signature"),
            "change_kind": value["change_kind"]}


def _validate_failure_class(value: Any) -> list[str]:
    if not isinstance(value, dict):
        raise ValueError("invalid failure_class")
    _class_scope({key: item for key, item in value.items() if key != "follow_up_dispatch_ids"})
    follow_ups = value.get("follow_up_dispatch_ids")
    if (not isinstance(follow_ups, list) or len(follow_ups) > CLASS_FOLLOW_UP_LIMIT
            or not all(isinstance(item, str) and item.strip() for item in follow_ups)
            or len(set(follow_ups)) != len(follow_ups)):
        raise ValueError("invalid failure_class follow-up registry")
    return follow_ups


def _validate_unit_allowances(ledger: dict[str, Any], key: str, marker: str, limit: int) -> dict[str, Any]:
    """Each increment's rounds under one allowance match its own recorded, unreserved corrective dispatches."""
    if key not in ledger:
        return {}
    allowances = ledger[key]
    if not isinstance(allowances, dict) or not allowances:
        raise ValueError(f"invalid {key}")
    for unit, record in allowances.items():
        require_text(unit, "increment tdd_unit")
        if (not isinstance(record, dict) or set(record) != {"rounds", "dispatch_ids"}
                or type(record["rounds"]) is not int or not 1 <= record["rounds"] <= limit
                or not isinstance(record["dispatch_ids"], list) or len(record["dispatch_ids"]) != record["rounds"]
                or len(set(record["dispatch_ids"])) != record["rounds"]):
            raise ValueError(f"{key} rounds disagree with the ledger")
        for dispatch_id in record["dispatch_ids"]:
            item = ledger["dispatches"].get(dispatch_id)
            if not isinstance(item, dict) or item.get(marker) != unit:
                raise ValueError(f"{key} lists a dispatch it does not own")
    return allowances


def _canonical_repo_path(value: Any) -> bool:
    """True for a canonical repository-relative path with no traversal or git metadata."""
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return (not path.is_absolute() and path.as_posix() == value
            and not any(part in {"..", ".", ".git"} for part in path.parts))


def _sorted_paths(value: Any) -> bool:
    return (isinstance(value, list) and all(_canonical_repo_path(path) for path in value)
            and value == sorted(set(value)))


def _validate_snapshot(value: Any) -> bool:
    return (isinstance(value, dict) and set(value) == WORKTREE_SNAPSHOT_KEYS
            and isinstance(value["head"], str) and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value["head"]) is not None
            and isinstance(value["dirty"], dict)
            and all(_canonical_repo_path(path) and (digest is None or (isinstance(digest, str)
                                                                         and re.fullmatch(r"[0-9a-f]{64}", digest)))
                    for path, digest in value["dirty"].items()))


def _validate_edit_records(item: dict[str, Any]) -> None:
    """The runner's own edit records: the units an implementation dispatch works on and the paths it changed."""
    from .helpers.read_only import is_test_path

    if "tdd_units" in item:
        units = item["tdd_units"]
        if (item["kind"] != "implementation" or not isinstance(units, list) or not units
                or not all(isinstance(unit, str) and unit.strip() and len(unit) <= 240 for unit in units)
                or len(set(units)) != len(units)):
            raise ValueError("invalid implementation tdd_units")
    if "test_fix_paths" in item or "test_fix" in item:
        paths = item.get("test_fix_paths")
        if ("test_fix" not in item or not isinstance(item["test_fix"], str) or not item["test_fix"].strip()
                or not _sorted_paths(paths) or not paths
                or not all(is_test_path(path) and not is_runner_byproduct(path) for path in paths)):
            raise ValueError("a test fix names its increment and only test files")
    tracked = "tdd_units" in item or "test_fix" in item
    if "worktree_before" in item and (not tracked or item["outcome"] not in {"reserved", "running", "unknown"}
                                      or not _validate_snapshot(item["worktree_before"])):
        raise ValueError("invalid worktree snapshot record")
    if "changed_paths" in item and (not tracked or item["outcome"] not in {"completed", "failed", "expected_tdd_red"}
                                    or not _sorted_paths(item["changed_paths"])):
        raise ValueError("invalid changed-path record")


def _validate_gate_allowances(ledger: dict[str, Any]) -> dict[str, Any]:
    """Each gate's remediation rounds match its own recorded, unreserved corrective dispatches."""
    if "gate_allowances" not in ledger:
        return {}
    allowances = ledger["gate_allowances"]
    if not isinstance(allowances, dict) or not allowances:
        raise ValueError("invalid gate remediation allowances")
    for gate, record in allowances.items():
        if (gate not in REMEDIATION_GATES or not isinstance(record, dict) or set(record) != {"rounds", "dispatch_ids"}
                or type(record["rounds"]) is not int or not 1 <= record["rounds"] <= GATE_REMEDIATION_ROUNDS
                or not isinstance(record["dispatch_ids"], list) or len(record["dispatch_ids"]) != record["rounds"]
                or len(set(record["dispatch_ids"])) != record["rounds"]):
            raise ValueError("gate remediation rounds disagree with the ledger")
        for dispatch_id in record["dispatch_ids"]:
            item = ledger["dispatches"].get(dispatch_id)
            if not isinstance(item, dict) or item.get("gate") != gate:
                raise ValueError("gate remediation allowance lists a dispatch it does not own")
    return allowances


def _validate_metadata_corrections(ledger: dict[str, Any]) -> dict[str, list[str]]:
    """Each metadata-only admission names its own unreserved dispatch and tasks corrected once."""
    if "metadata_corrections" not in ledger:
        return {}
    entries = ledger["metadata_corrections"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("invalid metadata corrections")
    owned: dict[str, list[str]] = {}
    tasks: set[str] = set()
    for entry in entries:
        if (not isinstance(entry, dict) or set(entry) != METADATA_CORRECTION_KEYS
                or not isinstance(entry["task_ids"], list) or not entry["task_ids"]
                or not all(isinstance(task, str) and re.fullmatch(r"T[0-9]{3,}", task) for task in entry["task_ids"])
                or len(set(entry["task_ids"])) != len(entry["task_ids"])
                or not all(isinstance(entry[key], str) and re.fullmatch(r"[0-9a-f]{64}", entry[key])
                           for key in ("baseline_sha256", "corrected_sha256"))
                or type(entry["admitted_at"]) not in (int, float)
                or not ledger["started_at"] <= entry["admitted_at"] < float("inf")):
            raise ValueError("invalid metadata correction record")
        dispatch_id = require_text(entry["dispatch_id"], "metadata correction dispatch_id")
        tasks_file = PurePosixPath(require_text(entry["tasks_file"], "metadata correction tasks_file"))
        bound = ledger.get("invariant_binding", {}).get("spec_file")
        if (tasks_file.is_absolute() or tasks_file.as_posix() != entry["tasks_file"] or tasks_file.name != "tasks.md"
                or any(part in {"..", ".", ".git"} for part in tasks_file.parts) or is_runner_byproduct(entry["tasks_file"])
                or (isinstance(bound, str) and tasks_file.parent != PurePosixPath(bound).parent)):
            raise ValueError("metadata correction tasks_file must be the bound feature's canonical tasks.md")
        if dispatch_id in owned:
            raise ValueError("duplicate metadata correction dispatch")
        if tasks & set(entry["task_ids"]):
            raise ValueError("a task was corrected twice as metadata-only in one run")
        tasks.update(entry["task_ids"])
        item = ledger["dispatches"].get(dispatch_id)
        if not isinstance(item, dict) or item.get("metadata_correction") != entry["task_ids"]:
            raise ValueError("metadata correction lists a dispatch it does not own")
        owned[dispatch_id] = entry["task_ids"]
    return owned


def escalation_key(unit_kind: str, unit: str) -> str:
    return f"{unit_kind}:{unit}"


def failed_verification(item: Any) -> bool:
    """True when the runner's own fingerprint on a verification dispatch shows failing or unparsed checks."""
    fingerprint = item.get("failing_checks") if isinstance(item, dict) else None
    return (isinstance(item, dict) and item.get("kind") == "verification"
            and isinstance(fingerprint, dict) and fingerprint.get("failing") != [])


def _failing_verification_since(ledger: dict[str, Any], command_sha256: str, since: float, until: float) -> bool:
    """True when the ledger shows a verification of this command failing between two clock readings."""
    return any(failed_verification(item) and item["failing_checks"]["command_sha256"] == command_sha256
               and since <= item["failing_checks"]["recorded_at"] <= until for item in ledger["dispatches"].values())


def _escalation_unit_failed(ledger: dict[str, Any], unit_kind: str, unit: str, since: float, until: float) -> bool:
    """True when the ledger itself shows this unit failed, by the moment a tier was reserved."""
    if unit_kind == "gate_failure":
        return _failing_verification_since(ledger, unit, since, until)
    return any(entry.get("unit_kind") == unit_kind and entry.get("unit") == unit and entry["deferred_at"] <= until
               for entry in ledger.get("deferred", []))


def _failing_since(ledger: dict[str, Any], unit_kind: str, earlier: list[dict[str, Any]]) -> float:
    """A failing gate must fail again after the prior tier settled; a deferral has one failure to answer."""
    if unit_kind == "gate_failure" and earlier:
        completed = ledger["dispatches"].get(earlier[-1]["dispatch_id"], {}).get("completed_at")
        if type(completed) in (int, float):
            return completed  # type: ignore[no-any-return]
    return ledger["started_at"]  # type: ignore[no-any-return]


def _tier_ready(ledger: dict[str, Any], record: dict[str, Any] | None, tier: int, reserved_at: float) -> bool:
    """True when the ledger shows the prior tier settled without resolving the unit, as `tier` requires."""
    if tier == 2:
        return record is None
    if record is None or len(record["dispatches"]) != tier - 2:
        return False
    dispatches = record["dispatches"]
    previous = ledger["dispatches"].get(dispatches[-1]["dispatch_id"])
    return (isinstance(previous, dict) and previous.get("outcome") in {"failed", "unknown", "completed"}
            and type(previous.get("completed_at")) in (int, float) and previous["completed_at"] <= reserved_at
            and (record["unit_kind"] == "gate_failure" or previous["outcome"] != "completed"))


def escalation_tier3_used(ledger: dict[str, Any]) -> int:
    """Tier-3 retries the run has reserved, in the current allowance and every archived one."""
    records = [ledger, *ledger.get("corrective_epochs", [])]
    return sum(1 for owner in records for record in owner.get("escalation_allowances", {}).values()
               if record["tier"] == 3)


def escalation_progress(ledger: dict[str, Any], unit_kind: str, unit: str) -> str:
    """The next step for a failed unit: `tier2`, `tier3`, `open` while a retry runs, or `exhausted`."""
    record = ledger.get("escalation_allowances", {}).get(escalation_key(unit_kind, unit))
    if record is None:
        return "tier2"
    if ledger["dispatches"][record["dispatches"][-1]["dispatch_id"]]["outcome"] in {"reserved", "running"}:
        return "open"
    if record["tier"] == 2 and escalation_tier3_used(ledger) < ESCALATION_TIER3_CAP:
        return "tier3"
    return "exhausted"


def _validate_escalations(ledger: dict[str, Any]) -> dict[str, Any]:
    """Each escalation record lists the tiers one unit reached, each owned by one recorded corrective dispatch."""
    if "escalation_allowances" not in ledger:
        return {}
    allowances = ledger["escalation_allowances"]
    if not isinstance(allowances, dict) or not allowances or ledger.get("escalation_tier3_cap") != ESCALATION_TIER3_CAP:
        raise ValueError("invalid escalation allowances")
    for key, record in allowances.items():
        if (not isinstance(record, dict) or set(record) != ESCALATION_KEYS
                or record["unit_kind"] not in ESCALATION_UNIT_KINDS
                or not isinstance(record["unit"], str) or not record["unit"]
                or key != escalation_key(record["unit_kind"], record["unit"])
                or record["tier"] not in ESCALATION_TIERS or not isinstance(record["dispatches"], list)
                or len(record["dispatches"]) != record["tier"] - 1):
            raise ValueError("invalid escalation allowance")
        for tier, entry in zip(ESCALATION_TIERS, record["dispatches"], strict=False):
            if (not isinstance(entry, dict) or set(entry) != ESCALATION_DISPATCH_KEYS or entry["tier"] != tier
                    or type(entry["reserved_at"]) not in (int, float)):
                raise ValueError("invalid escalation allowance")
            item = ledger["dispatches"].get(entry["dispatch_id"])
            if (not isinstance(item, dict) or item.get("escalation") != key or item.get("escalation_tier") != tier
                    or item.get("reserved_at") != entry["reserved_at"]):
                raise ValueError("escalation allowance lists a dispatch it does not own")
            earlier = record["dispatches"][:tier - 2]
            partial = {**record, "dispatches": earlier} if earlier else None
            if (not _escalation_unit_failed(ledger, record["unit_kind"], record["unit"],
                                            _failing_since(ledger, record["unit_kind"], earlier), entry["reserved_at"])
                    or not _tier_ready(ledger, partial, tier, entry["reserved_at"])):
                raise ValueError("escalation allowance names a unit or tier the ledger does not show as reached")
    return allowances


def _validate_escalation_cap(ledger: dict[str, Any]) -> None:
    """The run-wide tier-3 count never passes the cap the ledger records."""
    if "escalation_tier3_cap" in ledger and ledger["escalation_tier3_cap"] != ESCALATION_TIER3_CAP:
        raise ValueError("invalid escalation tier-3 cap")
    if escalation_tier3_used(ledger) > ESCALATION_TIER3_CAP:
        raise ValueError("escalation tier-3 retries pass the per-run cap")


def _validate_finalize_observations(ledger: dict[str, Any]) -> None:
    """Counts of the head-and-gate pairs `finalize-run` saw unfinished, one per pair and kind."""
    if "finalize_observations" not in ledger:
        return
    observations = ledger["finalize_observations"]
    if not isinstance(observations, dict) or not observations:
        raise ValueError("invalid finalize observations")
    for key, count in observations.items():
        kind, _, rest = key.partition(":")
        head, _, gate = rest.partition(":")
        if (kind not in FINALIZE_OBSERVATION_KINDS or re.fullmatch(r"[0-9a-f]{40}", head) is None or not gate
                or type(count) is not int or not 1 <= count <= FINALIZE_OBSERVATION_CAP):
            raise ValueError("invalid finalize observations")


def finalize_observation_key(kind: str, head_sha: str, gate: str) -> str:
    return f"{kind}:{head_sha}:{gate}"


def record_finalize_observations(root: Path, ledger_path: str, expected_run_id: str, keys: list[str]) -> None:
    """Count each key once for the finalize cycle that just observed it; the count stops at the cap."""
    path = confined_path(root, ledger_path)
    with exclusive_ledger(path):
        ledger = json.loads(path.read_text(encoding="utf-8"))
        validate_ledger(ledger)
        if ledger["run_id"] != expected_run_id:
            raise ValueError("expected_run_id does not match the ledger")
        counts = dict(ledger.get("finalize_observations", {}))
        for key in sorted(set(keys)):
            counts[key] = min(counts.get(key, 0) + 1, FINALIZE_OBSERVATION_CAP)
        ledger["finalize_observations"] = counts
        validate_ledger(ledger)
        durable_json(path, ledger)


def _reserve_escalation(ledger: dict[str, Any], dispatch_id: str, kind: Any, reservation: Any, request: Any,
                        now: float) -> dict[str, Any]:
    """Admit one escalation retry for a failed unit, outside the run-wide corrective budget."""
    if (not isinstance(request, dict) or set(request) != {"unit_kind", "unit", "tier"}
            or request["unit_kind"] not in ESCALATION_UNIT_KINDS or request["tier"] not in ESCALATION_TIERS
            or type(request["tier"]) is not int or not isinstance(request["unit"], str) or not request["unit"].strip()):
        raise ValueError("escalation must name a unit_kind, a unit, and a tier of 2 or 3")
    if kind != "corrective" or reservation is not None:
        raise ValueError("an escalation retry is a corrective dispatch with no corrective reservation")
    unit_kind, unit, tier = request["unit_kind"], request["unit"], request["tier"]
    key = escalation_key(unit_kind, unit)
    record = ledger.get("escalation_allowances", {}).get(key)
    note = {"escalation_allowance": "unit", "escalation_tier": tier}
    open_unit = unit_kind == "gate_failure" or any(
        entry["unit_kind"] == unit_kind and entry["unit"] == unit and "resolved_by" not in entry
        for entry in ledger.get("deferred", []))
    if record is not None and record["tier"] >= tier:
        return {"reasons": ["escalation_allowance_spent"], **note}
    earlier = record["dispatches"] if record is not None else []
    if not open_unit or not _escalation_unit_failed(ledger, unit_kind, unit,
                                                    _failing_since(ledger, unit_kind, earlier), now):
        return {"reasons": ["escalation_requires_a_failed_unit"], **note}
    if not _tier_ready(ledger, record, tier, now):
        return {"reasons": ["escalation_tier_out_of_order"], **note}
    if tier == 3 and escalation_tier3_used(ledger) >= ESCALATION_TIER3_CAP:
        return {"reasons": ["escalation_tier3_cap_reached"], **note}
    entry = {"tier": tier, "dispatch_id": dispatch_id, "reserved_at": now}
    ledger["escalation_tier3_cap"] = ESCALATION_TIER3_CAP
    ledger["escalation_allowances"] = {
        **ledger.get("escalation_allowances", {}),
        key: {"unit_kind": unit_kind, "unit": unit, "tier": tier,
              "dispatches": [*(record["dispatches"] if record is not None else []), entry]}}
    ledger["dispatches"][dispatch_id] = {"kind": kind, "outcome": "reserved", "reserved_at": now,
                                         "reservation_id": None, "reconciliations": 0, "escalation": key,
                                         "escalation_tier": tier}
    return {"reservation_id": None, "dispatch_id": dispatch_id, **note}


def _allowance_spent(ledger: dict[str, Any], reason: str, unit: str) -> bool:
    """True when the ledger itself shows the allowance a deferral names as spent."""
    if reason in {"failure_family_budget_exhausted", "corrective_run_budget_exhausted"}:
        return _corrective_refusal(ledger, unit) == reason
    if reason == "increment_review_allowance_exhausted":
        return ledger.get("increment_allowances", {}).get(unit, {}).get("rounds") == INCREMENT_REVIEW_ROUNDS
    if reason == "gate_remediation_allowance_exhausted":
        return ledger.get("gate_allowances", {}).get(unit, {}).get("rounds") == GATE_REMEDIATION_ROUNDS
    if reason == "failure_class_allowance_exhausted":
        approved = ledger.get("corrective_exception", {}).get("failure_class")
        return (isinstance(approved, dict) and approved.get("test_file") == unit
                and len(approved.get("follow_up_dispatch_ids", [])) >= CLASS_FOLLOW_UP_LIMIT)
    return any(item["family"] == unit for item in ledger["reservations"].values())


def _validate_deferrals(ledger: dict[str, Any]) -> None:
    """Each deferral is well formed, recorded once, in clock order, and names a spent allowance."""
    if "deferred" not in ledger:
        return
    entries = ledger["deferred"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("invalid deferral record")
    seen: set[str] = set()
    previous = ledger["started_at"]
    for entry in entries:
        if (not isinstance(entry, dict) or set(entry) not in (DEFERRAL_KEYS, DEFERRAL_KEYS | DEFERRAL_RESOLUTION_KEYS)
                or DEFER_REASONS.get(entry["reason"]) != entry["unit_kind"]):
            raise ValueError("invalid deferral record")
        dispatch_id = require_text(entry["dispatch_id"], "deferred dispatch_id")
        unit = require_text(entry["unit"], "deferred unit")
        if dispatch_id in seen:
            raise ValueError("duplicate deferral")
        seen.add(dispatch_id)
        deferred_at = entry["deferred_at"]
        if type(deferred_at) not in (int, float) or not previous <= deferred_at < float("inf"):
            raise ValueError("invalid deferral clock")
        previous = deferred_at
        if not _allowance_spent(ledger, entry["reason"], unit):
            raise ValueError("deferral names an allowance the ledger does not show as spent")
        if "resolved_by" in entry:
            resolver = entry["resolved_by"]
            if (not isinstance(resolver, str) or not _resolves(ledger, entry, resolver)
                    or entry["resolved_at"] != ledger["dispatches"][resolver]["completed_at"]
                    or any(_resolves(ledger, entry, other) and item["completed_at"] < entry["resolved_at"]
                           for other, item in ledger["dispatches"].items())):
                raise ValueError("deferral resolution is not the first later completed dispatch for its unit")


def _dispatch_units(ledger: dict[str, Any], item: dict[str, Any]) -> set[tuple[str, str]]:
    """The deferrable units a corrective dispatch works on, derived only from the ledger's own records."""
    if item.get("kind") != "corrective":
        return set()
    units: set[tuple[str, str]] = set()
    # A test fix runs under its own allowance and is not the deferred review fix, so it names no unit.
    if isinstance(item.get("increment"), str):
        units.add(("increment", item["increment"]))
    if isinstance(item.get("gate"), str):
        units.add(("gate", item["gate"]))
    reservation = item.get("reservation_id")
    if reservation in ledger["reservations"]:
        units.add(("failure_family", ledger["reservations"][reservation]["family"]))
    if isinstance(item.get("escalation"), str):
        unit_kind, _, unit = item["escalation"].partition(":")
        units.add((unit_kind, unit))
    exception = ledger.get("corrective_exception")
    if isinstance(exception, dict) and reservation is not None and reservation == exception.get("reservation_id"):
        units.add(("failure_family", exception["failure_invariant"]))
        if isinstance(exception.get("failure_class"), dict):
            units.add(("failure_class", exception["failure_class"]["test_file"]))
    return units


def _resolves(ledger: dict[str, Any], entry: dict[str, Any], dispatch_id: str) -> bool:
    """True when the ledger's own records show this dispatch resolved the deferral.

    The dispatch completed, was reserved at or after the deferral, and its allowance
    or reservation ties it to the deferral's unit. Nothing the caller claims counts.
    """
    item = ledger["dispatches"].get(dispatch_id)
    return (isinstance(item, dict) and item.get("outcome") == "completed"
            and type(item.get("completed_at")) in (int, float) and type(item.get("reserved_at")) in (int, float)
            and item["reserved_at"] >= entry["deferred_at"]
            and (entry["unit_kind"], entry["unit"]) in _dispatch_units(ledger, item))


def _resolve_deferrals(ledger: dict[str, Any], dispatch_id: str, now: float) -> None:
    """Stamp each open deferral that this just-completed dispatch resolves; the history stays."""
    for entry in ledger.get("deferred", []):
        if "resolved_by" not in entry and _resolves(ledger, entry, dispatch_id):
            entry.update(resolved_by=dispatch_id, resolved_at=now)


def _defer(ledger: dict[str, Any], dispatch_id: str, reason: str, unit: str, now: float) -> dict[str, Any]:
    """Refuse the dispatch and record its blocked unit once for the end-of-run request."""
    entries = ledger.setdefault("deferred", [])
    entry = next((item for item in entries if item["dispatch_id"] == dispatch_id), None)
    if entry is None:
        entry = {"dispatch_id": dispatch_id, "reason": reason, "unit_kind": DEFER_REASONS[reason],
                 "unit": unit, "deferred_at": now}
        entries.append(entry)
    return {"reasons": [entry["reason"]], "deferred": dict(entry)}


def _validate_failing_checks(record: Any, item: dict[str, Any]) -> None:
    """One runner-recorded fingerprint: closed shape, sorted unique identifiers, recorded while running."""
    from .failing_checks import FORMATS, MAX_IDENTIFIER_LENGTH, MAX_IDENTIFIERS

    if (not isinstance(record, dict) or not FAILING_CHECK_KEYS <= set(record) <= FAILING_CHECK_KEYS | FAILING_CHECK_OPTIONAL_KEYS
            or item.get("kind") != "verification" or record["format"] not in {*FORMATS, "passed", "unparsed"}):
        raise ValueError("invalid failing-check evidence")
    if ("head_sha" in record) != ("worktree_clean" in record) or (
            "head_sha" in record and (not isinstance(record["head_sha"], str)
                                      or re.fullmatch(r"[0-9a-f]{40}", record["head_sha"]) is None
                                      or type(record["worktree_clean"]) is not bool)):
        raise ValueError("invalid failing-check head evidence")
    require_text(record["command_id"], "failing-check command_id")
    for key in ("failing", "passing"):
        values = record[key]
        if values is not None and (not isinstance(values, list) or len(values) > MAX_IDENTIFIERS
                                   or values != sorted(set(values))
                                   or not all(isinstance(value, str) and 0 < len(value) <= MAX_IDENTIFIER_LENGTH
                                              for value in values)):
            raise ValueError("failing-check identifiers must be a sorted unique bounded list")
    if (record["failing"] is None) != (record["format"] == "unparsed") or (
            record["failing"] is None and record["passing"] is not None):
        raise ValueError("invalid failing-check evidence")
    if not all(isinstance(record[key], str) and re.fullmatch(r"[0-9a-f]{64}", record[key])
               for key in ("command_sha256", "output_sha256")):
        raise ValueError("invalid failing-check digest")
    checks_run = record["checks_run"]
    if (checks_run is not None and (type(checks_run) is not int or checks_run < 0)) or (
            record["failing"] is None and checks_run is not None):
        raise ValueError("invalid failing-check count")
    recorded_at, reserved_at = record["recorded_at"], item.get("reserved_at")
    if (type(recorded_at) not in (int, float) or type(reserved_at) not in (int, float)
            or not reserved_at <= recorded_at < float("inf")):
        raise ValueError("invalid failing-check clock")


def _record_failing_checks(ledger: dict[str, Any], inputs: dict[str, Any], evidence: dict[str, Any],
                           now: float) -> dict[str, Any]:
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    item = ledger["dispatches"].get(dispatch_id)
    if (not isinstance(item, dict) or item.get("kind") != "verification" or item["outcome"] != "running"
            or "failing_checks" in item):
        raise ValueError("failing checks are recorded once, on a running verification dispatch")
    record = {**evidence, "recorded_at": now}
    _validate_failing_checks(record, item)
    item["failing_checks"] = record
    return {"dispatch_id": dispatch_id}


def validate_recovery_records(ledger: dict[str, Any]) -> None:
    sources: set[str] = set()
    events: set[str] = set()
    keys = {"recovery_of", "failure_event_id", "operator_recovery_event_id"}
    for dispatch_id, item in ledger["dispatches"].items():
        present = keys & item.keys()
        if not present:
            continue
        if present != keys:
            raise ValueError("incomplete corrective recovery record")
        failed_id = require_text(item["recovery_of"], "recovery_of")
        failed_event_id = require_text(item["failure_event_id"], "failure_event_id")
        approval_event_id = require_text(item["operator_recovery_event_id"], "operator_recovery_event_id")
        failed = ledger["dispatches"].get(failed_id)
        if not isinstance(failed, dict):
            raise ValueError("invalid corrective recovery source")
        if (dispatch_id == failed_id or failed_id in sources or approval_event_id in events or
                approval_event_id == failed_event_id):
            raise ValueError("duplicate corrective recovery event")
        reservation = item.get("reservation_id")
        binding = (item["kind"], failed.get("kind"), failed.get("outcome"), failed.get("reservation_id"),
                   ledger["reservations"].get(reservation, {}).get("dispatch_id"),
                   failed.get("resolution_event_id"), ledger["corrective_cycles"])
        expected = ("corrective", "corrective", "failed", reservation, failed_id, failed_event_id, 2)
        if binding != expected:
            raise ValueError("invalid corrective recovery binding")
        sources.add(failed_id)
        events.add(approval_event_id)


def validate_continuation_records(ledger: dict[str, Any]) -> None:
    keys = {"continuation_of", "operator_continuation_event_id", "continuation_purpose"}
    events: set[str] = set()
    reservations: set[str] = set()
    other_events = set(ledger["workflow_identity"]["relocation_event_ids"])
    other_events.update(event for interval in ledger["excluded_intervals"]
                        for event in (interval["start_event"], interval["end_event"]))
    if ledger.get("active_wait"):
        other_events.add(ledger["active_wait"]["start_event"])
    other_events.update(record["resolution_event_id"] for record in ledger["dispatches"].values()
                        if "resolution_event_id" in record)
    other_events.update(record["operator_recovery_event_id"] for record in ledger["dispatches"].values()
                        if "operator_recovery_event_id" in record)
    if "corrective_exception" in ledger:
        other_events.add(ledger["corrective_exception"]["operator_exception_event_id"])
    for dispatch_id, item in ledger["dispatches"].items():
        present = keys & item.keys()
        if not present:
            continue
        if present != keys:
            raise ValueError("incomplete corrective continuation record")
        source_id = require_text(item["continuation_of"], "continuation_of")
        event_id = require_text(item["operator_continuation_event_id"], "operator_continuation_event_id")
        reservation = item.get("reservation_id")
        source = ledger["dispatches"].get(source_id)
        owner_id = ledger["reservations"].get(reservation, {}).get("dispatch_id")
        owner = ledger["dispatches"].get(owner_id)
        if (item.get("continuation_purpose") != "task_metadata_reconciliation" or
                item.get("kind") != "corrective" or not isinstance(source, dict) or
                source.get("kind") != "corrective" or source.get("outcome") != "completed" or
                source.get("reservation_id") != reservation or ledger["corrective_cycles"] != 2 or
                reservation in reservations or event_id in events or event_id in other_events):
            raise ValueError("invalid corrective continuation binding")
        recovered = source_id != owner_id and source.get("recovery_of") == owner_id and isinstance(owner, dict) and owner.get("outcome") == "failed"
        if source_id != owner_id and not recovered:
            raise ValueError("continuation source is not the completed reservation owner or its recovery")
        members = {key for key, record in ledger["dispatches"].items()
                   if record.get("reservation_id") == reservation}
        if members != {owner_id, source_id, dispatch_id}:
            raise ValueError("corrective continuation has unrelated reservation work")
        events.add(event_id)
        reservations.add(reservation)


def validate_intervals(ledger: dict[str, Any]) -> None:
    intervals = ledger.get("excluded_intervals")
    if not isinstance(intervals, list):
        raise ValueError("invalid excluded clock intervals")
    previous_end = ledger["started_at"]
    for interval in intervals:
        if not isinstance(interval, dict) or interval.get("kind") not in {"human_uat", "external_approval"}:
            raise ValueError("invalid excluded interval kind")
        for key in ("start", "end"):
            if type(interval.get(key)) not in (int, float) or not 0 <= interval[key] < float("inf"):
                raise ValueError("invalid excluded clock interval")
        if interval["start"] < previous_end or interval["end"] < interval["start"]:
            raise ValueError("overlapping or inverted excluded intervals")
        require_text(interval.get("start_event"), "start_event")
        require_text(interval.get("end_event"), "end_event")
        previous_end = interval["end"]
    active = ledger.get("active_wait")
    if active is not None:
        if not isinstance(active, dict) or active.get("kind") not in {"human_uat", "external_approval"}:
            raise ValueError("invalid active wait")
        if type(active.get("start")) not in (int, float) or not previous_end <= active["start"] < float("inf"):
            raise ValueError("invalid active wait clock")
        require_text(active.get("start_event"), "start_event")


def elapsed(ledger: dict[str, Any], now: float, since: float) -> float:
    intervals = list(ledger["excluded_intervals"])
    if ledger.get("active_wait"):
        intervals.append({**ledger["active_wait"], "end": now})
    excluded = sum(max(0, min(now, item["end"]) - max(since, item["start"])) for item in intervals)
    return max(0, now - since - excluded)


def clock_reasons(ledger: dict[str, Any], now: float) -> list[str]:
    reasons = []
    if now < ledger["last_observed_at"]:
        reasons.append("clock_moved_backwards")
    if ledger.get("active_wait"):
        reasons.append("awaiting_external_event")
    if any(item["outcome"] == "unknown" for item in ledger["dispatches"].values()):
        reasons.append("unknown_side_effects_require_operator_reconciliation")
    return reasons


def _consumed_native_event_ids(ledger: dict[str, Any]) -> set[str]:
    consumed = set(ledger["workflow_identity"]["relocation_event_ids"])
    consumed.update(event for interval in ledger["excluded_intervals"]
                    for event in (interval["start_event"], interval["end_event"]))
    if ledger.get("active_wait"):
        consumed.add(ledger["active_wait"]["start_event"])
    consumed.update(item["resolution_event_id"] for item in ledger["dispatches"].values()
                    if "resolution_event_id" in item)
    consumed.update(item["operator_recovery_event_id"] for item in ledger["dispatches"].values()
                    if "operator_recovery_event_id" in item)
    consumed.update(item["operator_continuation_event_id"] for item in ledger["dispatches"].values()
                    if "operator_continuation_event_id" in item)
    if "corrective_exception" in ledger:
        consumed.add(ledger["corrective_exception"]["operator_exception_event_id"])
    for epoch in ledger.get("corrective_epochs", []):
        consumed.add(epoch["epoch_event_id"])
        consumed.update(_consumed_native_event_ids(_epoch_view(ledger, epoch)))
    return consumed


def _operator_event(ledger: dict[str, Any], inputs: dict[str, Any], keys: set[str],
                    name: str) -> tuple[dict[str, Any], str]:
    """One bounded, unconsumed parent-observed operator event; binding is the caller's check."""
    event = inputs.get("native_observation")
    if not isinstance(event, dict) or set(event) != keys:
        raise ValueError(f"{name} requires one bounded operator native event")
    event_id = require_text(event.get("native_event_id"), "native_event_id")
    if event_id in _consumed_native_event_ids(ledger):
        raise ValueError(f"operator {name} event was already consumed")
    return event, event_id


def _corrective_refusal(ledger: dict[str, Any], family: str) -> str | None:
    """The reason an ordinary new corrective reservation for this family would be refused."""
    if any(item["family"] == family for item in ledger["reservations"].values()):
        return "failure_family_budget_exhausted"
    if ledger["corrective_cycles"] >= 2:
        return "corrective_run_budget_exhausted"
    return None


def _spec_digest(root: Path, spec_file: str) -> str | None:
    try:
        spec = confined_path(root, spec_file)
        return hashlib.sha256(spec.read_bytes()).hexdigest() if spec.is_file() else None
    except (OSError, ValueError):
        return None


def _chain_spec_file(ledger: dict[str, Any], root: Path, spec: Path) -> str:
    """The spec a family's first correction pins: the bound spec when the run has one, else the resolved spec."""
    bound = ledger.get("invariant_binding", {}).get("spec_file")
    return bound if isinstance(bound, str) else spec.relative_to(root.resolve()).as_posix()


def _latest_evidence(ledger: dict[str, Any], since: float, until: float, command_id: str | None) -> str | None:
    """The verification dispatch whose runner-recorded fingerprint is newest inside the window."""
    found = [(item["failing_checks"]["recorded_at"], dispatch_id) for dispatch_id, item in ledger["dispatches"].items()
             if "failing_checks" in item and since <= item["failing_checks"]["recorded_at"] <= until
             and command_id in {None, item["failing_checks"]["command_id"]}]
    return max(found)[1] if found else None


def _was_latest(ledger: dict[str, Any], candidate: Any, since: float, until: float, command_id: str | None) -> bool:
    """True when `_latest_evidence` could have chosen the candidate when the window closed.

    Evidence stamped at the same instant as the window's end may have been recorded
    after the choice, so only strictly earlier evidence can outrank the candidate.
    """
    item = ledger["dispatches"].get(candidate) if isinstance(candidate, str) else None
    if not isinstance(item, dict) or "failing_checks" not in item:
        return False
    stamp = item["failing_checks"]["recorded_at"]
    if not since <= stamp <= until or command_id not in {None, item["failing_checks"]["command_id"]}:
        return False
    return not any(stamp < other["failing_checks"]["recorded_at"] < until
                   for other in ledger["dispatches"].values()
                   if "failing_checks" in other and command_id in {None, other["failing_checks"]["command_id"]})


def _correction_baseline(ledger: dict[str, Any], now: float) -> str | None:
    """The newest recorded failure a family's first correction starts from, when it names its failing checks."""
    latest = _latest_evidence(ledger, ledger["started_at"], now, None)
    return latest if latest is not None and ledger["dispatches"][latest]["failing_checks"]["failing"] else None


def _progress_chain(ledger: dict[str, Any], reservation: str, until: str | None = None) -> list[str]:
    """The family's corrections in order: the reservation owner, then each progress admission."""
    chain = [ledger["reservations"][reservation]["dispatch_id"]]
    while chain[-1] != until:
        following = [key for key, item in ledger["dispatches"].items() if item.get("progress_of") == chain[-1]]
        if len(following) > 1:
            raise ValueError("progress history forks")
        if not following:
            break
        chain.append(following[0])
    return chain


def _progress(ledger: dict[str, Any], reservation: str, previous_id: str, spec_sha256: str | None,
              reserved_at: float, recorded_after: str | None = None) -> tuple[str | None, str, str | None]:
    """Whether the family's latest correction measurably converged: (change, reason, after-state dispatch).

    Every input is runner-recorded: the fingerprints on verification dispatches,
    the correction outcomes and clocks, and the spec digest the chain started from.
    Validation passes the after-state the ledger recorded to check it instead of choosing one.
    """
    dispatches = ledger["dispatches"]
    chain = _progress_chain(ledger, reservation, previous_id)
    previous = dispatches[previous_id]
    members = [dispatches[key] for key in chain] + [item for item in dispatches.values()
                                                    if item.get("reservation_id") == reservation
                                                    and "progress_of" not in item]
    if chain[-1] != previous_id or any(item["outcome"] != "completed" for item in members):
        return None, "previous_correction_unsettled", None
    if "baseline" not in previous:
        return None, "no_baseline", None
    if spec_sha256 is None or spec_sha256 != previous["spec_sha256"]:
        return None, "spec_changed", None
    before = dispatches[previous["baseline"]]["failing_checks"]
    after_id = _latest_evidence(ledger, previous["completed_at"], reserved_at, before["command_id"])
    if recorded_after is not None:
        valid = _was_latest(ledger, recorded_after, previous["completed_at"], reserved_at, before["command_id"])
        after_id = recorded_after if valid else None
    if after_id is None:
        return None, "no_new_evidence", None
    after = dispatches[after_id]["failing_checks"]
    if after["failing"] is None:
        return None, "evidence_unparsed", after_id
    if after["command_sha256"] != before["command_sha256"]:
        return None, "command_changed", after_id
    if before["checks_run"] is None or after["checks_run"] is None or after["checks_run"] < before["checks_run"]:
        return None, "fewer_checks_ran", after_id
    prior, current = set(before["failing"]), set(after["failing"])
    if not current:
        return None, "no_failing_checks", after_id
    if current < prior:
        change = "shrank"
    elif not current & prior and after["passing"] is not None and prior <= set(after["passing"]):
        change = "moved"
    else:
        return None, "no_progress", after_id
    if any(set(dispatches[dispatches[key]["baseline"]]["failing_checks"]["failing"]) == current
           for key in chain if "baseline" in dispatches[key]):
        return None, "returned_to_earlier_state", after_id
    return change, "", after_id


def _admit_progress(ledger: dict[str, Any], dispatch_id: str, family: str, root: Path,
                    now: float) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Admit a correction past the family cap when the previous one converged, with no operator event."""
    if family not in ledger["approved_invariants"]:
        return None, {"admitted": False, "reason": "unresolved_family"}
    reservation = next(key for key, item in ledger["reservations"].items() if item["family"] == family)
    tail = _progress_chain(ledger, reservation)[-1]
    spec_file = ledger["dispatches"][tail].get("spec_file")
    spec_sha256 = _spec_digest(root, spec_file) if isinstance(spec_file, str) else None
    change, reason, after_id = _progress(ledger, reservation, tail, spec_sha256, now)
    if change is None or after_id is None:
        return None, {"admitted": False, "reason": reason}
    if any(item.get("reservation_id") == reservation and item.get("baseline") == after_id
           for item in ledger["dispatches"].values()):
        return None, {"admitted": False, "reason": "no_new_evidence"}
    ledger["dispatches"][dispatch_id] = {"kind": "corrective", "outcome": "reserved", "reserved_at": now,
                                         "reservation_id": reservation, "reconciliations": 0, "progress_of": tail,
                                         "baseline": after_id, "spec_file": spec_file, "spec_sha256": spec_sha256}
    return ({"reservation_id": reservation, "dispatch_id": dispatch_id},
            {"admitted": True, "change": change, "previous_dispatch_id": tail, "baseline": after_id})


def _validate_progress(ledger: dict[str, Any]) -> None:
    """Recompute every recorded baseline and progress admission from the ledger's own evidence."""
    dispatches = ledger["dispatches"]
    owners = {item["dispatch_id"]: key for key, item in ledger["reservations"].items()}
    successors = [item["progress_of"] for item in dispatches.values() if "progress_of" in item]
    if len(successors) != len(set(successors)):
        raise ValueError("progress history forks")
    recorded = {key: item for key, item in dispatches.items()
                if {"baseline", "spec_file", "spec_sha256", "progress_of"} & item.keys()}
    bound = ledger.get("invariant_binding", {}).get("spec_file")
    baselines: set[tuple[Any, Any]] = set()
    for item in recorded.values():
        reservation, baseline = item.get("reservation_id"), item.get("baseline")
        evidence = dispatches.get(baseline, {}).get("failing_checks") if isinstance(baseline, str) else None
        if ({"baseline", "spec_file", "spec_sha256"} - item.keys() or item["kind"] != "corrective"
                or not isinstance(item["spec_file"], str) or (bound is not None and item["spec_file"] != bound)
                or reservation not in ledger["reservations"] or (reservation, baseline) in baselines
                or not isinstance(evidence, dict) or not evidence["failing"]
                or not isinstance(item["spec_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", item["spec_sha256"])):
            raise ValueError("invalid correction progress record")
        baselines.add((reservation, baseline))
    for dispatch_id, item in recorded.items():
        reservation = item["reservation_id"]
        if "progress_of" not in item:
            if (owners.get(dispatch_id) != reservation
                    or not _was_latest(ledger, item["baseline"], ledger["started_at"], item["reserved_at"], None)):
                raise ValueError("correction baseline disagrees with the recorded verification evidence")
            continue
        previous = dispatches.get(item["progress_of"])
        if (not isinstance(previous, dict) or previous.get("reservation_id") != reservation
                or previous.get("spec_file") != item["spec_file"]
                or type(previous.get("completed_at")) not in (int, float)
                or previous["completed_at"] > item["reserved_at"]):
            raise ValueError("invalid correction progress record")
        change, _, after_id = _progress(ledger, reservation, item["progress_of"], item["spec_sha256"], item["reserved_at"],
                                        item["baseline"])
        if change is None or after_id != item["baseline"]:
            raise ValueError("correction progress disagrees with the recorded verification evidence")


def _review_remediation(inputs: dict[str, Any]) -> dict[str, Any] | None:
    """The optional `review_remediation` request: one increment and the paths the fix touches."""
    request = inputs.get("review_remediation")
    if request is None:
        return None
    if (not isinstance(request, dict) or set(request) != {"tdd_unit", "paths"}
            or not isinstance(request["paths"], list) or not all(isinstance(path, str) for path in request["paths"])):
        raise ValueError("review_remediation requires exactly tdd_unit and a paths array of strings")
    require_text(request["tdd_unit"], "review_remediation tdd_unit")
    if inputs.get("kind") != "corrective" or inputs.get("reservation_id") is not None:
        raise ValueError("review_remediation applies only to a new corrective dispatch")
    if inputs.get("spec_file") is None:
        raise ValueError("review_remediation requires an explicit spec_file naming the feature spec")
    return request


def _increment_ineligibility(root: Path, spec: Path, request: dict[str, Any]) -> str | None:
    """Why a review fix does not qualify for its increment's allowance, or None when it does.

    Ownership comes only from the task-execution sidecar beside the explicit
    feature spec's tasks, bound to the current spec, plan, and tasks by their fingerprints.
    Missing, stale, or malformed evidence never qualifies.
    """
    from .task_execution import TaskExecutionError, fingerprints, owned_path, overlaps, path_key

    try:
        feature = spec.parent.relative_to(root.resolve()).as_posix()
        sources = [confined_path(root, f"{feature}/{name}").read_text(encoding="utf-8")
                   for name in ("spec.md", "plan.md", "tasks.md")]
        metadata = json.loads(confined_path(root, f"{feature}/.process/task-execution.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return "ownership_evidence_unavailable"
    if (not isinstance(metadata, dict) or metadata.get("schema_version") != "task-execution.v1"
            or metadata.get("fingerprints") != fingerprints(*sources)):
        return "ownership_evidence_stale"
    tasks = metadata.get("tasks")
    units: dict[str, list[str]] = {}
    try:
        if not isinstance(tasks, dict) or not tasks:
            raise TaskExecutionError("no task ownership")
        for entry in tasks.values():
            if (not isinstance(entry, dict) or not isinstance(entry.get("tdd_unit"), str)
                    or not isinstance(entry.get("owns"), list) or not entry["owns"]):
                raise TaskExecutionError("malformed task ownership")
            units.setdefault(entry["tdd_unit"], []).extend(owned_path(path, root) for path in entry["owns"])
    except TaskExecutionError:
        return "ownership_evidence_unavailable"
    owns = units.get(request["tdd_unit"])
    if owns is None:
        return "increment_not_in_ownership_evidence"
    if not request["paths"]:
        return "no_remediation_paths"
    try:
        paths = [owned_path(path, root) for path in request["paths"]]
    except TaskExecutionError:
        return "path_outside_increment_ownership"
    if not all(any(path_key(path) == path_key(own) or path_key(path).startswith(path_key(own) + "/") for own in owns)
               for path in paths):
        return "path_outside_increment_ownership"
    closed = _closed_units(root, feature, tasks, metadata["fingerprints"], sources[2])
    if any(overlaps(path, own) for unit, other in units.items() if unit != request["tdd_unit"] and unit not in closed
           for own in other for path in paths):
        return "path_reopens_another_increment"
    return None


def _checked_tasks(text: str) -> set[str]:
    """Task IDs whose checkbox is checked in a tasks.md text."""
    return {match.group(2) for line in text.splitlines()
            if (match := METADATA_TASK_LINE.match(line)) and re.match(r"\s*-\s+\[[xX]\]", line)}


def _closed_units(root: Path, feature: str, tasks: dict[str, Any], bound: dict[str, str], worktree: str) -> set[str]:
    """TDD units whose every task is checked in both the committed HEAD tasks.md and the worktree.

    The committed file must carry the same task definitions the sidecar binds.
    Without git, a HEAD copy, or matching definitions, no unit is closed.
    """
    from .task_execution import fingerprints

    committed = _head_bytes(root, f"{feature}/tasks.md")
    try:
        head = committed.decode("utf-8") if committed is not None else None
    except UnicodeError:
        head = None
    if head is None or fingerprints("", "", head)["tasks_sha256"] != bound.get("tasks_sha256"):
        return set()
    checked = _checked_tasks(head) & _checked_tasks(worktree)
    members: dict[str, set[str]] = {}
    for task_id, entry in tasks.items():
        members.setdefault(entry["tdd_unit"], set()).add(task_id)
    return {unit for unit, task_ids in members.items() if task_ids <= checked}


def _gate_remediation(inputs: dict[str, Any]) -> dict[str, Any] | None:
    """The optional `gate_remediation` request: one planning gate and the paths the fix touches."""
    request = inputs.get("gate_remediation")
    if request is None:
        return None
    if (not isinstance(request, dict) or set(request) != {"gate", "paths"} or request["gate"] not in REMEDIATION_GATES
            or not isinstance(request["paths"], list) or not all(isinstance(path, str) for path in request["paths"])):
        raise ValueError("gate_remediation requires exactly a gate from G2 to G7 and a paths array of strings")
    if inputs.get("review_remediation") is not None:
        raise ValueError("a corrective dispatch names review_remediation or gate_remediation, never both")
    if inputs.get("kind") != "corrective" or inputs.get("reservation_id") is not None:
        raise ValueError("gate_remediation applies only to a new corrective dispatch")
    if inputs.get("spec_file") is None:
        raise ValueError("gate_remediation requires an explicit spec_file naming the feature spec")
    return request


def _gate_ineligibility(root: Path, spec: Path, ledger: dict[str, Any], paths: list[str]) -> str | None:
    """Why a gate remediation does not qualify for its gate's allowance, or None when it does.

    The feature directory is the explicit spec's; when the ledger has bound a spec,
    it must be the same one. Every path must name a planning document on the closed
    list inside that directory, or a checklist directly under its `checklists/`.
    """
    feature = PurePosixPath(spec.parent.relative_to(root.resolve()).as_posix())
    binding = ledger.get("invariant_binding")
    if binding is not None and PurePosixPath(binding["spec_file"]).parent != feature:
        return "feature_binding_mismatch"
    if not paths:
        return "no_remediation_paths"
    for value in paths:
        path = PurePosixPath(value)
        if (not value or path.is_absolute() or path.as_posix() != value
                or any(part in {"..", ".", ".git"} for part in path.parts) or path.parent == path):
            return "path_outside_planning_documents"
        try:
            relative = path.relative_to(feature).as_posix()
        except ValueError:
            return "path_outside_planning_documents"
        checklist = PurePosixPath(relative)
        if relative not in PLANNING_DOCUMENTS and not (
                len(checklist.parts) == 2 and checklist.parts[0] == "checklists" and checklist.suffix == ".md"):
            return "path_outside_planning_documents"
        try:
            confined_path(root, value)
        except ValueError:
            return "path_outside_planning_documents"
    return None


def _metadata_correction(inputs: dict[str, Any]) -> bool:
    """The optional `metadata_only` request: the parent claims a task-verb correction for the runner to prove."""
    if "metadata_only" not in inputs:
        return False
    if inputs["metadata_only"] is not True:
        raise ValueError("metadata_only must be true when present")
    if inputs.get("review_remediation") is not None or inputs.get("gate_remediation") is not None:
        raise ValueError("a metadata_only correction names no review_remediation or gate_remediation")
    if inputs.get("kind") != "corrective" or inputs.get("reservation_id") is not None:
        raise ValueError("metadata_only applies only to a new corrective dispatch")
    if inputs.get("spec_file") is None:
        raise ValueError("metadata_only requires an explicit spec_file naming the feature spec")
    return True


def _git(root: Path, args: list[str]) -> bytes | None:
    """Standard output of one read-only git command in the repository, or None when git cannot answer."""
    git = shutil.which("git")
    if git is None:
        return None
    environment = {"PATH": os.environ.get("PATH", ""), "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                   "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}
    try:
        completed = subprocess.run([git, *args], cwd=root.resolve(), env=environment,
                                   capture_output=True, check=False, timeout=30, shell=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return completed.stdout if completed.returncode == 0 else None


def _head_bytes(root: Path, relative: str) -> bytes | None:
    """The committed HEAD bytes of a repository-relative path, or None when git cannot show them."""
    return _git(root, ["show", f"HEAD:./{relative}"])


def _tracked_path(relative: str) -> bool:
    """A path whose edits the runner attributes: not a runner byproduct or the implementation notes."""
    return _canonical_repo_path(relative) and not is_runner_byproduct(relative) and not is_implementation_notes(relative)


def _file_digest(root: Path, relative: str) -> str | None:
    """The digest of the worktree bytes at a path (a symlink's target text), or None when nothing is there."""
    path = root.resolve() / relative
    try:
        if path.is_symlink():
            return hashlib.sha256(os.readlink(path).encode("utf-8")).hexdigest()
        return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    except OSError:
        return None


def _git_paths(output: bytes) -> list[str]:
    return [item.decode("utf-8") for item in output.split(b"\0") if item]


def _worktree_snapshot(root: Path) -> dict[str, Any] | None:
    """HEAD and the digest of every changed path, read by the runner itself; None when git cannot answer."""
    top, head = _git(root, ["rev-parse", "--show-toplevel"]), _git(root, ["rev-parse", "--verify", "HEAD"])
    status = _git(root, ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames"])
    try:
        if (top is None or head is None or status is None
                or Path(top.decode("utf-8").strip()).resolve() != root.resolve()):
            return None
        paths = [entry[3:] for entry in _git_paths(status)]
        commit = head.decode("utf-8").strip()
    except (OSError, UnicodeError):
        return None
    return {"head": commit, "dirty": {path: _file_digest(root, path) for path in sorted(paths) if _tracked_path(path)}}


def worktree_evidence(root: Path) -> dict[str, Any]:
    """The head the runner sees and whether no tracked path differs from it; empty when git cannot answer."""
    snapshot = _worktree_snapshot(root)
    if snapshot is None:
        return {}
    return {"head_sha": snapshot["head"], "worktree_clean": not snapshot["dirty"]}


def _changed_since(root: Path, before: dict[str, Any]) -> list[str] | None:
    """Every path whose content differs from the snapshot, in sorted order; None when git cannot answer.

    A path clean at the snapshot held its content at the snapshot's HEAD, so the
    runner compares that committed content, or the snapshot's own digest for a
    path already dirty then, with the worktree now.
    """
    after = _worktree_snapshot(root)
    moved = b"" if after is None or after["head"] == before["head"] else _git(
        root, ["diff", "--name-only", "--no-renames", "-z", before["head"], after["head"]])
    if after is None or moved is None:
        return None
    try:
        candidates = set(before["dirty"]) | set(after["dirty"]) | set(_git_paths(moved))
    except UnicodeError:
        return None
    changed = []
    for path in sorted(candidate for candidate in candidates if _tracked_path(candidate)):
        if path in before["dirty"]:
            previous = before["dirty"][path]
        else:
            committed = _git(root, ["show", f"{before['head']}:./{path}"])
            previous = hashlib.sha256(committed).hexdigest() if committed is not None else None
        if previous != _file_digest(root, path):
            changed.append(path)
    return changed


def _verb_swap(before: str, after: str) -> str | None:
    """The task ID when two task lines differ only by a verification verb at the head, else None.

    Checkbox state is not a task definition, matching `fingerprints`. Everything
    else (ID, markers, emphasis, and every byte after the verb) must be identical,
    and both verbs must be verification verbs, so the task keeps its routing.
    """
    from .helpers.read_only import PHASE7_LEADING_VERB, PHASE7_VERIFY_KEYWORDS

    old, new = (METADATA_TASK_LINE.match(re.sub(r"^(\s*-\s+\[)[ xX]\]", r"\1 ]", line)) for line in (before, after))
    if old is None or new is None or old.group(1) != new.group(1):
        return None
    old_verb, new_verb = PHASE7_LEADING_VERB.match(old.group(3)), PHASE7_LEADING_VERB.match(new.group(3))
    if (old_verb is None or new_verb is None or old.group(3)[:old_verb.start(1)] != new.group(3)[:new_verb.start(1)]
            or old.group(3)[old_verb.end(1):] != new.group(3)[new_verb.end(1):]
            or old_verb.group(1) == new_verb.group(1)
            or not {old_verb.group(1).lower(), new_verb.group(1).lower()} <= set(PHASE7_VERIFY_KEYWORDS)):
        return None
    return old.group(2)


def _sidecar_unchanged(root: Path, feature: PurePosixPath, current: dict[str, bytes]) -> bool:
    """True when the task-execution sidecar keeps every task entry of its committed baseline.

    Dependencies and ownership live in the sidecar, so its `tasks` must be
    unchanged. Its fingerprints may be the committed ones or the refresh for the
    corrected sources. A legacy feature has no sidecar at either end.
    """
    from .task_execution import fingerprints

    relative = (feature / ".process/task-execution.json").as_posix()
    committed = _head_bytes(root, relative)
    try:
        path = confined_path(root, relative)
        present = path.exists() or path.is_symlink()
        if committed is None or not present:
            return committed is None and not present
        if not path.is_file():
            return False
        baseline, worktree = json.loads(committed), json.loads(path.read_bytes())
    except (OSError, UnicodeError, ValueError):
        return False
    if (not isinstance(baseline, dict) or not isinstance(worktree, dict) or set(baseline) != set(worktree)
            or any(baseline[key] != worktree[key] for key in baseline if key != "fingerprints")):
        return False
    texts = [current[name].decode("utf-8") for name in ("spec.md", "plan.md", "tasks.md")]
    return worktree.get("fingerprints") in (baseline.get("fingerprints"), fingerprints(*texts))


def _metadata_ineligibility(root: Path, spec: Path, ledger: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    """Why a claimed metadata-only correction does not qualify, or None with its admission record.

    The baseline is the committed HEAD of the explicit spec's feature directory,
    read by the runner itself. spec.md and plan.md must match it byte for byte,
    and tasks.md may differ only by verification-verb swaps on task lines.
    Missing, unreadable, or symlinked evidence never qualifies.
    """
    from .task_execution import fingerprints

    feature = PurePosixPath(spec.parent.relative_to(root.resolve()).as_posix())
    binding = ledger.get("invariant_binding")
    if binding is not None and PurePosixPath(binding["spec_file"]).parent != feature:
        return "feature_binding_mismatch", {}
    current: dict[str, bytes] = {}
    baseline: dict[str, bytes] = {}
    for name in ("spec.md", "plan.md", "tasks.md"):
        relative = (feature / name).as_posix()
        committed = _head_bytes(root, relative)
        try:
            path = confined_path(root, relative)
            if committed is None or not path.is_file():
                return "baseline_unavailable", {}
            current[name], baseline[name] = path.read_bytes(), committed
            current[name].decode("utf-8"), committed.decode("utf-8")
        except (OSError, UnicodeError, ValueError):
            return "baseline_unavailable", {}
    if any(current[name] != baseline[name] for name in ("spec.md", "plan.md")):
        return "planning_source_changed", {}
    before, after = baseline["tasks.md"].decode("utf-8"), current["tasks.md"].decode("utf-8")
    if (fingerprints("", "", before)["tasks_sha256"] == fingerprints("", "", after)["tasks_sha256"]):
        return "no_task_correction", {}
    old_lines, new_lines = before.splitlines(keepends=True), after.splitlines(keepends=True)
    if len(old_lines) != len(new_lines):
        return "not_metadata_only", {}
    task_ids: list[str] = []
    for old, new in zip(old_lines, new_lines, strict=True):
        if fingerprints("", "", old)["tasks_sha256"] == fingerprints("", "", new)["tasks_sha256"]:
            continue
        task_id = _verb_swap(old, new)
        if task_id is None:
            return "not_metadata_only", {}
        task_ids.append(task_id)
    if not _sidecar_unchanged(root, feature, current):
        return "not_metadata_only", {}
    corrected = {task for entry in ledger.get("metadata_corrections", []) for task in entry["task_ids"]}
    for epoch in ledger.get("corrective_epochs", []):
        corrected.update(task for entry in epoch.get("metadata_corrections", []) for task in entry["task_ids"])
    if corrected & set(task_ids) or len(set(task_ids)) != len(task_ids):
        return "task_already_corrected", {}
    return None, {"task_ids": task_ids, "tasks_file": (feature / "tasks.md").as_posix(),
                  "baseline_sha256": hashlib.sha256(baseline["tasks.md"]).hexdigest(),
                  "corrected_sha256": hashlib.sha256(current["tasks.md"]).hexdigest()}


def _admit_metadata_correction(ledger: dict[str, Any], dispatch_id: str, record: dict[str, Any],
                               now: float) -> dict[str, Any]:
    """Record a proven metadata-only correction; never touches the run-wide counter."""
    ledger.setdefault("metadata_corrections", []).append({"dispatch_id": dispatch_id, **record, "admitted_at": now})
    ledger["dispatches"][dispatch_id] = {"kind": "corrective", "outcome": "reserved", "reserved_at": now,
                                         "reservation_id": None, "reconciliations": 0,
                                         "metadata_correction": list(record["task_ids"])}
    return {"reservation_id": None, "dispatch_id": dispatch_id, "correction_allowance": "metadata_only",
            "task_ids": list(record["task_ids"])}


def _test_fix_request(inputs: dict[str, Any]) -> dict[str, Any] | None:
    """The optional `test_fix` request: one increment and the test files the fix touches."""
    request = inputs.get("test_fix")
    if request is None:
        return None
    if (not isinstance(request, dict) or set(request) != {"tdd_unit", "paths"}
            or not isinstance(request["paths"], list) or not all(isinstance(path, str) for path in request["paths"])):
        raise ValueError("test_fix requires exactly tdd_unit and a paths array of strings")
    require_text(request["tdd_unit"], "test_fix tdd_unit")
    if any(inputs.get(key) is not None for key in ("review_remediation", "gate_remediation", "metadata_only")):
        raise ValueError("a test_fix names no review_remediation, gate_remediation, or metadata_only")
    if inputs.get("kind") != "corrective" or inputs.get("reservation_id") is not None:
        raise ValueError("test_fix applies only to a new corrective dispatch")
    if inputs.get("spec_file") is None:
        raise ValueError("test_fix requires an explicit spec_file naming the feature spec")
    return request


def _implementation_units(inputs: dict[str, Any]) -> list[str] | None:
    """The optional `tdd_units` of an implementation dispatch, whose edits the runner then records."""
    if "tdd_units" not in inputs:
        return None
    units = inputs["tdd_units"]
    if inputs.get("kind") != "implementation":
        raise ValueError("tdd_units applies only to an implementation dispatch")
    if (not isinstance(units, list) or not units or len(set(map(str, units))) != len(units)
            or not all(isinstance(unit, str) for unit in units)):
        raise ValueError("tdd_units requires a nonempty array of distinct TDD unit names")
    return [require_text(unit, "tdd_units item") for unit in units]


def _edited_paths(ledger: dict[str, Any], unit: str) -> set[str]:
    """Paths the runner recorded as changed by the increment's own implementation dispatches in this run."""
    views = [ledger, *(_epoch_view(ledger, epoch) for epoch in ledger.get("corrective_epochs", []))]
    return {path for view in views for item in view["dispatches"].values()
            if item.get("kind") == "implementation" and unit in item.get("tdd_units", [])
            for path in item.get("changed_paths", [])}


def _test_fix_ineligibility(root: Path, spec: Path, ledger: dict[str, Any],
                            request: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    """Why a test fix does not qualify for its increment's test-fix allowance, or None with a worktree snapshot.

    Every path must be a test file inside the increment's own ownership that the
    runner recorded as changed by one of that increment's implementation dispatches
    in this run. Missing ownership, edit, or git evidence never qualifies.
    """
    from .helpers.read_only import is_test_path

    unit, paths = request["tdd_unit"], request["paths"]
    if unit in ledger.get("test_fix_allowances", {}):
        return "test_fix_allowance_spent", None
    ownership = _increment_ineligibility(root, spec, request)
    if ownership is not None:
        return ownership, None
    if not all(_canonical_repo_path(path) and is_test_path(path) and not is_runner_byproduct(path) for path in paths):
        return "path_not_test_code", None
    if not set(paths) <= _edited_paths(ledger, unit):
        return "path_not_edited_by_increment", None
    snapshot = _worktree_snapshot(root)
    if snapshot is None:
        return "worktree_state_unavailable", None
    return None, snapshot


def _reserve_test_fix(ledger: dict[str, Any], dispatch_id: str, request: dict[str, Any], snapshot: dict[str, Any],
                      now: float) -> dict[str, Any]:
    """Spend the increment's one test-fix round; never touches the run-wide counter."""
    unit = request["tdd_unit"]
    ledger["test_fix_allowances"] = {**ledger.get("test_fix_allowances", {}),
                                     unit: {"rounds": 1, "dispatch_ids": [dispatch_id]}}
    ledger["dispatches"][dispatch_id] = {"kind": "corrective", "outcome": "reserved", "reserved_at": now,
                                         "reservation_id": None, "reconciliations": 0, "test_fix": unit,
                                         "test_fix_paths": sorted(set(request["paths"])), "worktree_before": snapshot}
    return {"reservation_id": None, "dispatch_id": dispatch_id, "test_fix_allowance": "increment"}


def _reserve_gate_remediation(ledger: dict[str, Any], dispatch_id: str, gate: str, now: float) -> dict[str, Any]:
    """Spend one of the gate's own remediation rounds; never touches the run-wide counter."""
    allowances = ledger.get("gate_allowances", {})
    record = allowances.get(gate, {"rounds": 0, "dispatch_ids": []})
    if record["rounds"] >= GATE_REMEDIATION_ROUNDS:
        return {**_defer(ledger, dispatch_id, "gate_remediation_allowance_exhausted", gate, now),
                "remediation_allowance": "gate"}
    ledger["gate_allowances"] = {**allowances, gate: {"rounds": record["rounds"] + 1,
                                                      "dispatch_ids": [*record["dispatch_ids"], dispatch_id]}}
    ledger["dispatches"][dispatch_id] = {"kind": "corrective", "outcome": "reserved", "reserved_at": now,
                                         "reservation_id": None, "reconciliations": 0, "gate": gate}
    return {"reservation_id": None, "dispatch_id": dispatch_id, "remediation_allowance": "gate"}


def _reserve_increment_review(ledger: dict[str, Any], dispatch_id: str, unit: str, now: float) -> dict[str, Any]:
    """Spend one of the increment's own review rounds; never touches the run-wide counter."""
    allowances = ledger.get("increment_allowances", {})
    record = allowances.get(unit, {"rounds": 0, "dispatch_ids": []})
    if record["rounds"] >= INCREMENT_REVIEW_ROUNDS:
        return {**_defer(ledger, dispatch_id, "increment_review_allowance_exhausted", unit, now),
                "review_allowance": "increment"}
    ledger["increment_allowances"] = {**allowances, unit: {"rounds": record["rounds"] + 1,
                                                           "dispatch_ids": [*record["dispatch_ids"], dispatch_id]}}
    ledger["dispatches"][dispatch_id] = {"kind": "corrective", "outcome": "reserved", "reserved_at": now,
                                         "reservation_id": None, "reconciliations": 0, "increment": unit}
    return {"reservation_id": None, "dispatch_id": dispatch_id, "review_allowance": "increment"}


def reserve(ledger: dict[str, Any], inputs: dict[str, Any], now: float, root: Path, spec: Path) -> dict[str, Any]:
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    kind = inputs.get("kind")
    if kind not in KINDS:
        raise ValueError("unknown execution kind")
    metadata_only = _metadata_correction(inputs)
    review = _review_remediation(inputs)
    gate_request = _gate_remediation(inputs)
    test_fix = _test_fix_request(inputs)
    units = _implementation_units(inputs)
    if dispatch_id in _used_dispatch_ids(ledger):
        return {"reasons": ["dispatch_already_reserved_no_relaunch"]}
    reservation = inputs.get("reservation_id")
    if "escalation" in inputs:
        return _reserve_escalation(ledger, dispatch_id, kind, reservation, inputs["escalation"], now)
    note: dict[str, Any] = {}
    if metadata_only:
        ineligible, record = _metadata_ineligibility(root, spec, ledger)
        if ineligible is None:
            return _admit_metadata_correction(ledger, dispatch_id, record, now)
        note = {"correction_allowance": "run_wide", "metadata_ineligible": ineligible}
    if review is not None:
        ineligible = _increment_ineligibility(root, spec, review)
        if ineligible is None:
            return _reserve_increment_review(ledger, dispatch_id, review["tdd_unit"], now)
        note = {"review_allowance": "run_wide", "increment_ineligible": ineligible}
    if gate_request is not None:
        ineligible = _gate_ineligibility(root, spec, ledger, gate_request["paths"])
        if ineligible is None:
            return _reserve_gate_remediation(ledger, dispatch_id, gate_request["gate"], now)
        note = {"remediation_allowance": "run_wide", "gate_ineligible": ineligible}
    if test_fix is not None:
        ineligible, snapshot = _test_fix_ineligibility(root, spec, ledger, test_fix)
        if ineligible is None and snapshot is not None:
            return _reserve_test_fix(ledger, dispatch_id, test_fix, snapshot, now)
        note = {"test_fix_allowance": "run_wide", "test_fix_ineligible": ineligible}
    if kind == "corrective":
        if reservation is not None:
            if reservation not in ledger["reservations"]:
                raise ValueError("nested correction requires an existing run reservation")
            owner = ledger["reservations"][reservation]["dispatch_id"]
            family = ledger["reservations"][reservation]["family"]
            if ledger["dispatches"][owner]["outcome"] != "reserved":
                return _defer(ledger, dispatch_id, "corrective_cycle_already_closed", family, now)
            if any(item.get("reservation_id") == reservation and item["outcome"] in {"failed", "unknown"}
                   for item in ledger["dispatches"].values()):
                return _defer(ledger, dispatch_id, "corrective_cycle_failed_no_nested_retry", family, now)
        else:
            invariant = inputs.get("failure_invariant")
            family = str(invariant) if invariant in ledger["approved_invariants"] else "unresolved"
            refusal = _corrective_refusal(ledger, family)
            if refusal == "failure_family_budget_exhausted":
                admitted, progress = _admit_progress(ledger, dispatch_id, family, root, now)
                if admitted is not None:
                    return {**admitted, "progress": progress, **note}
                return {**_defer(ledger, dispatch_id, refusal, family, now), "progress": progress, **note}
            if refusal is not None:
                return {**_defer(ledger, dispatch_id, refusal, family, now), **note}
            reservation = uuid.uuid4().hex
            ledger["reservations"][reservation] = {"family": family, "dispatch_id": dispatch_id, "reserved_at": now}
            ledger["corrective_cycles"] += 1
            spec_file = _chain_spec_file(ledger, root, spec)
            baseline, spec_sha256 = _correction_baseline(ledger, now), _spec_digest(root, spec_file)
            if family in ledger["approved_invariants"] and baseline is not None and spec_sha256 is not None:
                ledger["dispatches"][dispatch_id] = {"kind": kind, "outcome": "reserved", "reserved_at": now,
                                                     "reservation_id": reservation, "reconciliations": 0,
                                                     "baseline": baseline, "spec_file": spec_file,
                                                     "spec_sha256": spec_sha256}
                return {"reservation_id": reservation, "dispatch_id": dispatch_id, **note}
    elif reservation is not None:
        raise ValueError("only corrective dispatches use corrective reservations")
    ledger["dispatches"][dispatch_id] = {"kind": kind, "outcome": "reserved", "reserved_at": now,
                                        "reservation_id": reservation, "reconciliations": 0}
    if units is not None:
        ledger["dispatches"][dispatch_id]["tdd_units"] = units
        snapshot = _worktree_snapshot(root)
        if snapshot is not None:
            ledger["dispatches"][dispatch_id]["worktree_before"] = snapshot
    return {"reservation_id": reservation, "dispatch_id": dispatch_id, **note}


def authorize_corrective_retry(ledger: dict[str, Any], inputs: dict[str, Any], now: float) -> dict[str, Any]:
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    failed_id = require_text(inputs.get("failed_dispatch_id"), "failed_dispatch_id")
    reservation = require_text(inputs.get("reservation_id"), "reservation_id")
    keys = {"native_event_id", "run_id", "action", "failed_dispatch_id", "failed_native_event_id",
            "retry_dispatch_id", "reservation_id", "failure_kind"}
    event, event_id = _operator_event(ledger, inputs, keys, "corrective retry")
    failed = ledger["dispatches"].get(failed_id)
    binding = (event.get("run_id"), event.get("action"), event.get("failed_dispatch_id"),
               event.get("retry_dispatch_id"), event.get("reservation_id"), event.get("failure_kind"))
    expected = (ledger["run_id"], "corrective_retry_approved", failed_id, dispatch_id,
                reservation, "infrastructure")
    if binding != expected:
        raise ValueError("operator recovery event does not match this run")
    if (dispatch_id in _used_dispatch_ids(ledger) or ledger["corrective_cycles"] != 2 or
            not isinstance(failed, dict) or failed.get("kind") != "corrective" or
            failed.get("outcome") != "failed" or failed.get("reservation_id") != reservation or
            failed.get("resolution_event_id") != event.get("failed_native_event_id") or
            ledger["reservations"].get(reservation, {}).get("dispatch_id") != failed_id or
            any(item.get("reservation_id") == reservation for item_id, item in ledger["dispatches"].items()
                if item_id != failed_id)):
        raise ValueError("failed corrective dispatch is not eligible for a one-time infrastructure retry")
    ledger["dispatches"][dispatch_id] = {"kind": "corrective", "outcome": "reserved", "reserved_at": now,
                                         "reservation_id": reservation, "reconciliations": 0,
                                         "recovery_of": failed_id, "failure_event_id": event["failed_native_event_id"],
                                         "operator_recovery_event_id": event_id}
    return {"reservation_id": reservation, "dispatch_id": dispatch_id, "recovery_of": failed_id}


def authorize_corrective_continuation(ledger: dict[str, Any], inputs: dict[str, Any], now: float) -> dict[str, Any]:
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    source_id = require_text(inputs.get("completed_dispatch_id"), "completed_dispatch_id")
    reservation = require_text(inputs.get("reservation_id"), "reservation_id")
    keys = {"native_event_id", "run_id", "action", "completed_dispatch_id",
            "continuation_dispatch_id", "reservation_id", "purpose"}
    event, event_id = _operator_event(ledger, inputs, keys, "corrective continuation")
    expected = (ledger["run_id"], "corrective_continuation_approved", source_id, dispatch_id,
                reservation, "task_metadata_reconciliation")
    binding = (event.get("run_id"), event.get("action"), event.get("completed_dispatch_id"),
               event.get("continuation_dispatch_id"), event.get("reservation_id"), event.get("purpose"))
    if binding != expected:
        raise ValueError("operator continuation event does not match this run")
    source = ledger["dispatches"].get(source_id)
    owner_id = ledger["reservations"].get(reservation, {}).get("dispatch_id")
    owner = ledger["dispatches"].get(owner_id)
    recovered = isinstance(source, dict) and source.get("recovery_of") == owner_id and isinstance(owner, dict) and owner.get("outcome") == "failed"
    members = {key for key, item in ledger["dispatches"].items() if item.get("reservation_id") == reservation}
    if (dispatch_id in _used_dispatch_ids(ledger) or ledger["corrective_cycles"] != 2 or
            not isinstance(source, dict) or source.get("kind") != "corrective" or
            source.get("outcome") != "completed" or source.get("reservation_id") != reservation or
            (source_id != owner_id and not recovered) or
            members != {owner_id, source_id}):
        raise ValueError("completed corrective dispatch is not eligible for one metadata continuation")
    ledger["dispatches"][dispatch_id] = {"kind": "corrective", "outcome": "reserved", "reserved_at": now,
                                         "reservation_id": reservation, "reconciliations": 0,
                                         "continuation_of": source_id,
                                         "operator_continuation_event_id": event_id,
                                         "continuation_purpose": "task_metadata_reconciliation"}
    return {"reservation_id": reservation, "dispatch_id": dispatch_id, "continuation_of": source_id}


def authorize_corrective_exception(ledger: dict[str, Any], inputs: dict[str, Any], now: float) -> dict[str, Any]:
    """Reserve the run's one operator-approved correction that an ordinary reserve would refuse."""
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    invariant = require_text(inputs.get("failure_invariant"), "failure_invariant")
    scope = inputs.get("scope_sha256")
    failure_class = _class_scope(inputs["failure_class"]) if inputs.get("failure_class") is not None else None
    keys = {"native_event_id", "run_id", "action", "failure_invariant", "dispatch_id", "failure_kind",
            "refusal_reason", "scope_sha256", "spec_sha256"} | ({"failure_class"} if failure_class else set())
    event, event_id = _operator_event(ledger, inputs, keys, "corrective exception")
    if failure_class is not None and event.get("failure_class") != failure_class:
        raise ValueError("operator exception event does not approve this failure class")
    spec_digest = ledger.get("invariant_binding", {}).get("spec_sha256")
    refusal = _corrective_refusal(ledger, invariant)
    binding = (event.get("run_id"), event.get("action"), event.get("failure_invariant"), event.get("dispatch_id"),
               event.get("failure_kind"), event.get("refusal_reason"), event.get("scope_sha256"),
               event.get("spec_sha256"))
    expected = (ledger["run_id"], "corrective_exception_approved", invariant, dispatch_id, "application",
                refusal, scope, spec_digest)
    if binding != expected:
        raise ValueError("operator exception event does not match this run, scope, spec, and refusal")
    family = next((key for key, item in ledger["reservations"].items() if item["family"] == invariant), None)
    if ("corrective_exception" in ledger or dispatch_id in _used_dispatch_ids(ledger) or spec_digest is None or
            refusal is None or invariant not in ledger["approved_invariants"] or
            not isinstance(scope, str) or not re.fullmatch(r"[0-9a-f]{64}", scope) or
            any(item.get("reservation_id") == family and item["outcome"] not in {"completed", "failed"}
                for item in ledger["dispatches"].values() if family is not None)):
        raise ValueError("correction is not eligible for the run's one operator-approved exception")
    reservation = uuid.uuid4().hex
    ledger["corrective_exception"] = {"reservation_id": reservation, "dispatch_id": dispatch_id,
                                      "failure_invariant": invariant, "refusal_reason": refusal,
                                      "scope_sha256": scope, "spec_sha256": spec_digest,
                                      "operator_exception_event_id": event_id, "authorized_at": now}
    if failure_class is not None:
        ledger["corrective_exception"]["failure_class"] = {**failure_class, "follow_up_dispatch_ids": []}
    ledger["dispatches"][dispatch_id] = {"kind": "corrective", "outcome": "reserved", "reserved_at": now,
                                         "reservation_id": reservation, "reconciliations": 0}
    return {"reservation_id": reservation, "dispatch_id": dispatch_id}


def reserve_class_correction(ledger: dict[str, Any], inputs: dict[str, Any], now: float) -> dict[str, Any]:
    """Reserve a follow-up inside the operator-approved failure class, with no new approval.

    The scope must match exactly, every earlier correction in the class must have
    completed, and at most CLASS_FOLLOW_UP_LIMIT follow-ups share one approval. A
    follow-up past that limit is deferred to the end-of-run request.
    """
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    scope = _class_scope(inputs.get("failure_class"))
    exception: dict[str, Any] = ledger.get("corrective_exception") or {}
    approved = exception.get("failure_class")
    if not isinstance(approved, dict) or {key: approved[key] for key in scope} != scope:
        raise ValueError("no operator approval covers this failure class in the current corrective epoch")
    reservation = exception["reservation_id"]
    members = [item for item in ledger["dispatches"].values() if item.get("reservation_id") == reservation]
    if dispatch_id in _used_dispatch_ids(ledger) or any(item["outcome"] != "completed" for item in members):
        raise ValueError("class correction needs a new dispatch id and completed earlier fixes")
    if len(approved["follow_up_dispatch_ids"]) >= CLASS_FOLLOW_UP_LIMIT:
        return _defer(ledger, dispatch_id, "failure_class_allowance_exhausted", scope["test_file"], now)
    approved["follow_up_dispatch_ids"].append(dispatch_id)
    ledger["dispatches"][dispatch_id] = {"kind": "corrective", "outcome": "reserved", "reserved_at": now,
                                         "reservation_id": reservation, "reconciliations": 0}
    return {"reservation_id": reservation, "dispatch_id": dispatch_id}


def _observed_changes(item: dict[str, Any], outcome: str, root: Path) -> list[str] | None:
    """The paths the runner saw a tracked dispatch change since its own snapshot, or None when it cannot say."""
    if "worktree_before" not in item or outcome == "unknown":
        return None
    return _changed_since(root, item["worktree_before"])


def record_result(ledger: dict[str, Any], inputs: dict[str, Any], now: float, root: Path) -> dict[str, Any]:
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    if dispatch_id not in ledger["dispatches"]:
        raise ValueError("dispatch was not reserved")
    item = ledger["dispatches"][dispatch_id]
    if inputs["action"] == "reconcile":
        allowed = item["reconciliations"] == 0 and item["outcome"] in {"reserved", "running", "unknown"}
        if allowed:
            item["reconciliations"] = 1
            item["outcome"] = "unknown"
        return {"reconciliation_allowed": allowed, "relaunch_allowed": False,
                "reasons": [] if allowed else ["reconciliation_budget_exhausted"]}
    outcome = inputs.get("outcome")
    if outcome not in OUTCOMES or (outcome == "expected_tdd_red" and item["kind"] != "implementation"):
        raise ValueError("invalid outcome for dispatch kind")
    changed = _observed_changes(item, outcome, root)
    if "test_fix" in item and outcome == "completed" and item["outcome"] in {"reserved", "running"}:
        # A test fix completes only when the runner saw a change and every change stayed in its declared test files.
        if not changed or not set(changed) <= set(item["test_fix_paths"]):
            return {"reasons": ["test_fix_scope_unproven"]}
    if item["outcome"] == "unknown":
        event = inputs.get("native_observation")
        if not isinstance(event, dict) or not isinstance(event.get("native_event_id"), str) or not event["native_event_id"].strip():
            return {"reasons": ["missing_independent_native_result"]}
        if event["native_event_id"] in _consumed_native_event_ids(ledger):
            raise ValueError("native event was already consumed")
        if event.get("run_id") != ledger["run_id"] or event.get("dispatch_id") != dispatch_id or event.get("action") != "dispatch_result" or event.get("outcome") != outcome or outcome == "unknown":
            return {"reasons": ["native_result_binding_mismatch"]}
        item["resolution_event_id"] = event["native_event_id"]
    elif item["outcome"] not in {"reserved", "running"}:
        return {"reasons": ["recorded_outcome_cannot_be_overwritten"]}
    if outcome != "unknown" and "worktree_before" in item:
        del item["worktree_before"]
        if changed is not None:
            item["changed_paths"] = changed
    item.update(outcome=outcome, completed_at=now)
    if outcome == "completed":
        _resolve_deferrals(ledger, dispatch_id, now)
    return {"reasons": ["unknown_side_effects_require_operator_reconciliation"] if outcome == "unknown" else []}


def begin_verification(ledger: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    item = ledger["dispatches"].get(dispatch_id)
    if not isinstance(item, dict) or item.get("kind") != "verification":
        raise ValueError("verification requires a reserved verification dispatch")
    if item["outcome"] != "reserved":
        return {"reasons": ["dispatch_already_started_no_relaunch"]}
    item["outcome"] = "running"
    return {"dispatch_id": dispatch_id}


def checkpoint_or_wait(ledger: dict[str, Any], inputs: dict[str, Any], now: float) -> dict[str, Any]:
    action = inputs["action"]
    if action == "checkpoint":
        completed = [name for name, item in ledger["dispatches"].items() if item["outcome"] == "completed"]
        if not completed:
            return {"reasons": ["no_completed_work_to_checkpoint"]}
        ledger["checkpoint_at"] = now
        return {"completed_dispatch_ids": completed}
    event = inputs.get("native_observation")
    if not isinstance(event, dict) or event.get("run_id") != ledger["run_id"]:
        raise ValueError("wait accounting requires an independent parent native event bound to this run")
    event_id = require_text(event.get("native_event_id"), "native_event_id")
    if event_id in _consumed_native_event_ids(ledger):
        raise ValueError("native event was already consumed")
    kind = event.get("kind")
    if kind not in {"human_uat", "external_approval"}:
        raise ValueError("only human UAT or external approval waits can exclude wall time")
    active = ledger.get("active_wait")
    if action == "pause":
        if active is not None or event.get("action") != "wait_started":
            raise ValueError("pause requires a new native wait-start event")
        ledger["active_wait"] = {"start": now, "kind": kind, "start_event": event_id}
    else:
        if active is None or active["kind"] != kind or event.get("action") != "wait_ended" or event_id == active["start_event"] or event.get("wait_start_event_id") != active["start_event"]:
            raise ValueError("resume requires the matching independent native wait-end event")
        ledger["excluded_intervals"].append({**active, "end": now, "end_event": event_id})
        ledger["active_wait"] = None
    return {}


def _relocate_workflow(ledger: dict[str, Any], inputs: dict[str, Any], workflow_file: str) -> None:
    event = inputs.get("native_observation")
    keys = {"native_event_id", "run_id", "action", "previous_workflow_file", "workflow_file"}
    if not isinstance(event, dict) or set(event) != keys:
        raise ValueError("workflow relocation requires one bounded parent native event")
    event_id = require_text(event.get("native_event_id"), "native_event_id")
    identity = ledger["workflow_identity"]
    # The parent-native trust boundary supplies this observation; matching
    # fixture-shaped data here is validation, not authentication.
    binding = (event.get("run_id"), event.get("action"), event.get("previous_workflow_file"),
               event.get("workflow_file"))
    expected = (ledger["run_id"], "workflow_relocated", identity["current_workflow_file"], workflow_file)
    if binding != expected or workflow_file == identity["current_workflow_file"]:
        raise ValueError("workflow relocation event does not match this run and workflow transition")
    if event_id in _consumed_native_event_ids(ledger):
        raise ValueError("native event was already consumed")
    identity["current_workflow_file"] = workflow_file
    identity["relocation_event_ids"].append(event_id)


def _spec_invariants(spec_bytes: bytes) -> list[str]:
    invariants = sorted(set(re.findall(r"\b(?:FR|NFR|INV)-[A-Za-z0-9]+\b", spec_bytes.decode("utf-8"))))
    if not invariants:
        raise ValueError("spec_file contains no requirement or invariant IDs")
    return invariants


def begin_replan_epoch(root: Path, ledger: dict[str, Any], inputs: dict[str, Any], spec: Path,
                       now: float) -> dict[str, Any]:
    """Archive the spent allowance and open a fresh one for an operator-approved re-plan."""
    if inputs.get("spec_file") is None:
        raise ValueError("begin-replan-epoch requires an explicit spec_file")
    keys = {"native_event_id", "run_id", "action", "spec_sha256"}
    event, event_id = _operator_event(ledger, inputs, keys, "re-plan epoch")
    spec_bytes = spec.read_bytes()
    spec_digest = hashlib.sha256(spec_bytes).hexdigest()
    if (event.get("run_id"), event.get("action"), event.get("spec_sha256")) != (
            ledger["run_id"], "replan_epoch_approved", spec_digest):
        raise ValueError("operator re-plan event does not match this run and the current spec")
    if ledger.get("active_wait") or any(item["outcome"] not in OUTCOMES - {"unknown"}
                                        for item in ledger["dispatches"].values()):
        raise ValueError("settle every dispatch and wait before opening a new corrective epoch")
    epoch = {key: ledger.pop(key) for key in (*EPOCH_STATE_KEYS, *EPOCH_OPTIONAL_KEYS) if key in ledger}
    epoch.update(epoch_event_id=event_id, closed_at=now)
    ledger.setdefault("corrective_epochs", []).append(epoch)
    ledger.update(corrective_cycles=0, reservations={}, dispatches={}, approved_invariants=_spec_invariants(spec_bytes),
                  invariant_binding={"spec_file": spec.relative_to(root.resolve()).as_posix(),
                                     "spec_sha256": spec_digest, "bound_at": now})
    return {"corrective_epoch": len(ledger["corrective_epochs"])}


def begin_stage_epoch(root: Path, ledger: dict[str, Any], inputs: dict[str, Any], workflow: Path,
                      now: float) -> dict[str, Any]:
    """Archive the prior stage's allowance when the operator explicitly starts the implement stage.

    The runner derives every piece of evidence itself: the invocation argv names
    the stage explicitly, and the workflow file records planning complete with
    its `Stage` row already written for this invocation. No operator event is
    needed, and the derived event ID makes a second opening for the stage a no-op.
    """
    from .helpers.read_only import parse_stage_args, trusted_text, workflow_stage_signals

    args = inputs.get("autopilot_args")
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        raise ValueError("begin-stage-epoch requires autopilot_args, the invocation argv as an array of strings")
    parsed = parse_stage_args(args)
    stage = parsed["stage"]
    if parsed["error"] or stage not in STAGE_EPOCH_STAGES:
        raise ValueError("begin-stage-epoch requires an explicit --stage implement in the invocation argv")
    text = trusted_text(workflow, root)
    signals = workflow_stage_signals(text) if text is not None else {"parsed": False}
    if not signals["parsed"] or not signals["planning_complete"]:
        raise ValueError("begin-stage-epoch requires a workflow file whose planning stage is complete")
    if signals["recorded_stage"] != stage:
        raise ValueError(f"begin-stage-epoch requires the workflow Stage row to record {stage}; "
                         "write the resolved Stage row before opening the stage allowance")
    event_id = STAGE_EPOCH_PREFIX + stage
    if any(epoch.get("stage_transition") == stage for epoch in ledger.get("corrective_epochs", [])):
        return {"stage_epoch_opened": False, "corrective_epoch": len(ledger["corrective_epochs"])}
    if event_id in _consumed_native_event_ids(ledger):
        raise ValueError("the stage transition event ID was already consumed by another event")
    if ledger.get("active_wait") or any(item["outcome"] not in OUTCOMES - {"unknown"}
                                        for item in ledger["dispatches"].values()):
        raise ValueError("settle every dispatch and wait before opening a new corrective epoch")
    epoch = {key: ledger.pop(key) for key in (*EPOCH_STATE_KEYS, *EPOCH_OPTIONAL_KEYS) if key in ledger}
    ledger.update(corrective_cycles=0, reservations={}, dispatches={},
                  approved_invariants=list(epoch["approved_invariants"]))
    if "invariant_binding" in epoch:
        ledger["invariant_binding"] = dict(epoch["invariant_binding"])
    epoch.update(epoch_event_id=event_id, closed_at=now, stage_transition=stage)
    ledger.setdefault("corrective_epochs", []).append(epoch)
    return {"stage_epoch_opened": True, "corrective_epoch": len(ledger["corrective_epochs"])}


def _bind_invariants_if_requested(root: Path, inputs: dict[str, Any], spec: Path,
                                  ledger: dict[str, Any], now: float, reasons: list[str]) -> None:
    if inputs.get("action") != "bind-invariants":
        return
    if inputs.get("spec_file") is None:
        raise ValueError("bind-invariants requires an explicit spec_file")
    if reasons:
        return
    if ledger["approved_invariants"] or "invariant_binding" in ledger:
        raise ValueError("invariant registry is already frozen for this run")
    spec_bytes = spec.read_bytes()
    ledger["approved_invariants"] = _spec_invariants(spec_bytes)
    ledger["invariant_binding"] = {
        "spec_file": spec.relative_to(root.resolve()).as_posix(),
        "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(), "bound_at": now,
    }


def execution_control(root: Path, inputs: dict[str, Any], mode: str,
                      evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    """Runner adapter returns a disposition without changing autopilot top-state.

    `evidence` is set only by `record_failing_checks`, the verification executors'
    internal path; a helper request cannot reach the evidence action.
    """
    workflow_name = require_text(inputs.get("workflow_file"), "workflow_file")
    workflow = confined_path(root, workflow_name)
    if not workflow.is_file():
        raise ValueError("workflow_file must exist")
    workflow_name = workflow.relative_to(root.resolve()).as_posix()
    spec_name = inputs.get("spec_file")
    spec = confined_path(root, spec_name) if spec_name is not None else workflow.with_name("spec.md")
    if spec_name is not None and not spec.is_file():
        raise ValueError("spec_file must be an existing contained file")
    action = inputs.get("action", "status")
    if action not in {"start", "status", "bind-invariants", "reserve", "authorize-corrective-retry", "authorize-corrective-continuation", "authorize-corrective-exception", "reserve-class-correction", "begin-replan-epoch", "begin-stage-epoch", "begin-verification", "complete", "reconcile", "checkpoint", "pause", "resume", "relocate-workflow"}:
        if evidence is None or action != RECORD_FAILING_CHECKS:
            raise ValueError("unsupported action; pauses/resets require verified native authorization")
    elif evidence is not None:
        raise ValueError("failing-check evidence is recorded only by the verification executors")
    if mode not in {"read_only", "dry_run", "apply"} or (mode == "read_only" and action != "status"):
        raise ValueError("ledger mutations require dry_run or apply")
    expected_run_id = inputs.get("expected_run_id")
    if expected_run_id is not None:
        require_text(expected_run_id, "expected_run_id")
    elif action != "start":
        raise ValueError("expected_run_id is required after the explicit first kickoff")
    workflow_key = hashlib.sha256(workflow_name.encode("utf-8")).hexdigest()[:24]
    relative = inputs.get("ledger_path") or f"{default_ledger_directory(workflow_name)}/{workflow_key}.json"
    if Path(relative).parent.name != "execution-control" or Path(relative).suffix != ".json":
        raise ValueError("ledger_path must reference an owned execution-control JSON record")
    path = confined_path(root, relative)

    def update() -> dict[str, Any]:
        now = time.time()
        ledger = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        existing_ledger = ledger is not None
        if ledger is None:
            if action != "start" or expected_run_id is not None:
                raise ValueError("known run ledger missing; recover its owned ledger without resetting the budget")
            ledger = initial_ledger(spec, now)
            ledger["workflow_identity"] = {"original_workflow_file": workflow_name,
                                           "current_workflow_file": workflow_name,
                                           "relocation_event_ids": []}
        validate_ledger(ledger)
        if existing_ledger and expected_run_id is None:
            raise ValueError("expected_run_id is required for every existing execution ledger action")
        if expected_run_id is not None and ledger["run_id"] != expected_run_id:
            raise ValueError("execution ledger does not match the parent expected_run_id")
        ledger = copy.deepcopy(ledger)
        identity = ledger["workflow_identity"]
        if action == "relocate-workflow":
            _relocate_workflow(ledger, inputs, workflow_name)
        elif identity["current_workflow_file"] != workflow_name:
            raise ValueError("execution ledger belongs to a different workflow")
        reasons = clock_reasons(ledger, now)
        extra: dict[str, Any] = {}
        if "clock_moved_backwards" in reasons and action not in {"status", "start"}:
            raise ValueError("clock moved backwards; preserve the ledger and reconcile time before continuing")
        _bind_invariants_if_requested(root, inputs, spec, ledger, now, reasons)
        if action == RECORD_FAILING_CHECKS and evidence is not None:
            extra = _record_failing_checks(ledger, inputs, evidence, now)
        elif action == "reserve" and not reasons:
            extra = reserve(ledger, inputs, now, root, spec)
        elif action == "authorize-corrective-retry" and not reasons:
            extra = authorize_corrective_retry(ledger, inputs, now)
        elif action == "authorize-corrective-continuation" and not reasons:
            extra = authorize_corrective_continuation(ledger, inputs, now)
        elif action == "authorize-corrective-exception" and not reasons:
            extra = authorize_corrective_exception(ledger, inputs, now)
        elif action == "reserve-class-correction" and not reasons:
            extra = reserve_class_correction(ledger, inputs, now)
        elif action == "begin-replan-epoch" and not reasons:
            extra = begin_replan_epoch(root, ledger, inputs, spec, now)
        elif action == "begin-stage-epoch" and not reasons:
            extra = begin_stage_epoch(root, ledger, inputs, workflow, now)
        elif action == "begin-verification" and not reasons:
            extra = begin_verification(ledger, inputs)
        elif action in {"complete", "reconcile"}:
            extra = record_result(ledger, inputs, now, root)
            reasons = clock_reasons(ledger, now)
        elif action in {"checkpoint", "pause", "resume"}:
            extra = checkpoint_or_wait(ledger, inputs, now)
            reasons = clock_reasons(ledger, now)
        reasons.extend(extra.pop("reasons", []))
        if mode == "apply":
            ledger["last_observed_at"] = max(now, ledger["last_observed_at"])
            durable_json(path, ledger)
        disposition = ("continue" if not reasons else "defer" if all(reason in DEFER_REASONS for reason in reasons)
                       else "checkpoint_required")
        return {"ledger": ledger, "ledger_path": relative, "disposition": disposition,
                "reasons": reasons, "elapsed_seconds": elapsed(ledger, now, ledger["started_at"]),
                "checkpoint_due": elapsed(ledger, now, ledger["checkpoint_at"]) >= 2700,
                "authorization_granted": False, "writes_state": mode == "apply", **extra}

    if mode == "apply":
        # Mark the evidence directory before the orchestrator can write its own logs there (#813).
        ignore_owned_directory(confined_path(root, evidence_directory(workflow_name)))
        with exclusive_ledger(path):
            return update()
    return update()


def record_failing_checks(root: Path, inputs: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    """Write the runner's own failing-check fingerprint onto its running verification dispatch.

    Only the verification executors call this, with a fingerprint they derived from
    output they executed. The action is not reachable through a helper request.
    """
    request = {key: inputs.get(key) for key in ("workflow_file", "expected_run_id", "ledger_path", "dispatch_id")}
    return execution_control(root, {**request, "action": RECORD_FAILING_CHECKS}, "apply", evidence=evidence)


def run_execution_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Existing runner envelope adapter; apply remains a host-authorized action."""
    from .envelope import diagnostic, response
    from .helpers.read_only import canonicalize_inputs, resolve_repo_root, validate_bounded_inputs
    from .verification_records import execute_verification
    from .task_results import task_results

    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    error = validate_bounded_inputs(entry.helper_id, request.inputs, root)
    if error:
        return response("input_error", request_id=request.request_id, diagnostics=[error])
    inputs = canonicalize_inputs(entry.helper_id, request.inputs, root)
    try:
        handler = {"execution-control": execution_control, "execute-verification": execute_verification,
                   "task-results": task_results}[entry.helper_id]
        result = handler(root, inputs, request.mode)
    except (ValueError, OSError, TypeError) as exc:
        return response("input_error", request_id=request.request_id,
                        diagnostics=[diagnostic("invalid_execution_request", str(exc))])
    # A deferral refuses the dispatch, so it is an expected failure just like a checkpoint.
    failed = (result.get("helper_exit_code") == 1 if entry.helper_id == "task-results"
              else result.get("disposition") in {"checkpoint_required", "defer"})
    status = "expected_failure" if failed else "ok"
    result.update(helper_id=entry.helper_id, operation=entry.operation, mode=request.mode,
                  promotion_status=entry.promotion_status)
    return response(status, request_id=request.request_id, data=result)
