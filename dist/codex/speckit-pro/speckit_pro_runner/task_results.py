"""Persist native-parent task reports without treating worker claims as proof."""
from __future__ import annotations

import json
import re
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from .agent_materialization import canonical_bytes
from .formal.selection import require_text as text_field, unique_object
from .task_execution import fingerprints

SCHEMA = "task-results.v1"


def non_tdd_reason(batch: dict[str, Any]) -> str | None:
    from .helpers.read_only import PHASE7_RESEARCH_AGENT, PHASE7_VERIFY_AGENT

    if batch["agent"] in {PHASE7_RESEARCH_AGENT, PHASE7_VERIFY_AGENT}:
        return f"native route {batch['agent']} does not run implementation TDD"
    return None


def result_path(root: Path, value: Any) -> Path:
    from .execution_control import confined_path

    raw = text_field(value, "path")
    if "\\" in raw or raw != Path(raw).as_posix() or any(p in {"", ".", ".."} for p in raw.split("/")):
        raise ValueError("path must be canonical and repository relative")
    return confined_path(root, raw)


def source_snapshot(root: Path, path: Path) -> dict[str, Any]:
    from .helpers.mutation import snapshot_write_target

    value = snapshot_write_target(path, root)
    if not value["exists"]:
        raise ValueError(f"required evidence or source missing: {path.relative_to(root)}")
    return value


def decode_object(raw: bytes) -> dict[str, Any]:
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(value, dict):
        raise ValueError("journal and metadata must be JSON objects")
    canonical_bytes(value)
    return value


def current_binding(root: Path, tasks: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    sources = [source_snapshot(root, p) for p in (tasks.parent / "spec.md", tasks.parent / "plan.md", tasks)]
    sidecar = source_snapshot(root, tasks.parent / ".process/task-execution.json")
    binding = {"fingerprints": fingerprints(*(s["content"].decode("utf-8") for s in sources)),
               "metadata_sha256": sidecar["digest"]}
    return binding, decode_object(sidecar["content"])


def start_journal(root: Path, inputs: dict[str, Any], tasks: Path, path: Path,
                  binding: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    from .helpers.read_only import partition_phase7_tasks

    partition = partition_phase7_tasks({**inputs, "task_execution_required": True}, root)
    if partition["exit_code"]:
        raise ValueError(partition["stderr"] or "task metadata partition failed")
    plan = decode_object(partition["stdout"].encode("utf-8"))
    journal = {"schema_version": SCHEMA, "tasks_file": tasks.relative_to(root).as_posix(), **binding,
               "batches": plan["batches"], "task_units": {t: metadata["tasks"][t]["tdd_unit"]
                   for b in plan["batches"] for t in b["tasks"]}, "reports": []}
    for batch in journal["batches"]:
        if reason := non_tdd_reason(batch):
            batch["tdd_not_applicable_reason"] = reason
    others = list(path.parent.glob("*.json"))
    prior = inputs.get("prior_journal_file")
    if others or prior is not None:
        prior_path = result_path(root, prior)
        if prior_path.parent != path.parent or prior_path == path or prior_path not in others:
            raise ValueError("new journal requires an existing sibling prior_journal_file")
        previous = source_snapshot(root, prior_path)
        prior_value = decode_object(previous["content"])
        if prior_value.get("schema_version") != SCHEMA or prior_value.get("tasks_file") != journal["tasks_file"]:
            raise ValueError("prior journal belongs to a different contract or tasks file")
        journal.update({"prior_journal_file": prior, "prior_journal_sha256": previous["digest"],
                        "reconciliation_event_id": text_field(inputs.get("reconciliation_event_id"), "reconciliation_event_id"),
                        "reconciliation_reason": text_field(inputs.get("reconciliation_reason"), "reconciliation_reason")})
    return journal


def validate_observation(root: Path, event: Any) -> None:
    if not isinstance(event, dict):
        raise ValueError("native observation must be an object")
    task_result = event.get("stage") == "task_result"
    fields = {"event_id", "tdd_unit", "stage", "output_path", "output_sha256"} | (
        {"task_id", "outcome"} if task_result else {"argv", "exit_code", "classification", "snapshot_sha256"})
    if not isinstance(event, dict) or set(event) != fields:
        raise ValueError("native observation fields are incomplete or unknown")
    for name in ("event_id", "tdd_unit"):
        text_field(event[name], name)
    if task_result:
        text_field(event["task_id"], "task_id")
        if event["outcome"] != "completed":
            raise ValueError("native task_result outcome must be completed")
    else:
        if event["stage"] not in {"red", "green", "refactor"} or type(event["exit_code"]) is not int:
            raise ValueError("native observation needs a TDD stage and integer exit code")
        if event["classification"] not in {"assertion_failure", "test_pass", "infrastructure"}:
            raise ValueError("native parent must classify the command outcome")
        if not isinstance(event["argv"], list) or not event["argv"] or any(not isinstance(a, str) or not a for a in event["argv"]):
            raise ValueError("native observation needs the actual command argv")
    for name in (("output_sha256",) if task_result else ("output_sha256", "snapshot_sha256")):
        if not isinstance(event[name], str) or not re.fullmatch("[0-9a-f]{64}", event[name]):
            raise ValueError(f"{name} must be a sha256 digest")
    output = source_snapshot(root, result_path(root, event["output_path"]))
    if output["digest"] != event["output_sha256"]:
        raise ValueError("native command output digest mismatch")


def validate_report(root: Path, journal: dict[str, Any], report: dict[str, Any]) -> None:
    if not isinstance(report, dict) or set(report) != {"batch_id", "results", "native_observations"}:
        raise ValueError("invalid report fields")
    batch = next((b for b in journal["batches"] if b["id"] == report.get("batch_id")), None)
    results, observations = report.get("results"), report.get("native_observations")
    if batch is None or not isinstance(results, list) or not all(isinstance(r, dict) for r in results):
        raise ValueError("unknown batch or invalid results")
    if [r.get("task_id") for r in results] != batch["tasks"]:
        raise ValueError("results must contain exactly the frozen ordered task IDs")
    if not isinstance(observations, list):
        raise ValueError("native_observations must be an independent event array")
    events = {}
    for event in observations:
        validate_observation(root, event)
        if event["event_id"] in events:
            raise ValueError("duplicate native event ID")
        events[event["event_id"]] = event
    referenced, units = set(), {}
    for result in results:
        if set(result) != {"task_id", "tdd_unit", "status", "block", "evidence_event_ids"}:
            raise ValueError("TaskResult fields are incomplete or unknown")
        text_field(result["block"], "TaskResult block")
        unit, refs = result["tdd_unit"], result["evidence_event_ids"]
        if unit != journal["task_units"][result["task_id"]] or result["status"] not in {"complete", "unfinished"}:
            raise ValueError("TaskResult unit or status mismatch")
        if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs) or len(set(refs)) != len(refs):
            raise ValueError("evidence references must be unique event IDs")
        if any(ref not in events or events[ref]["tdd_unit"] != unit for ref in refs):
            raise ValueError("missing or mismatched native event reference")
        referenced.update(refs)
        state = (result["status"], refs)
        if not non_tdd_reason(batch) and unit in units and units[unit] != state:
            raise ValueError("a TDD unit cannot be partly complete or use different evidence")
        units[unit] = state
        if result["status"] == "complete":
            proof = [events[ref] for ref in refs]
            if non_tdd_reason(batch):
                if len(proof) != 1 or proof[0]["stage"] != "task_result" or proof[0]["task_id"] != result["task_id"]:
                    raise ValueError("nonimplementation completion requires its native task_result event")
                continue
            if [e["stage"] for e in proof] != ["red", "green", "refactor"]:
                raise ValueError("complete unit requires distinct RED, GREEN, and refactor command observations")
            red, green, refactor = proof
            if red["exit_code"] == 0 or red["classification"] != "assertion_failure":
                raise ValueError("RED must be an assertion failure, not infrastructure failure")
            if any(e["exit_code"] != 0 or e["classification"] != "test_pass" or e["argv"] != red["argv"]
                   for e in (green, refactor)):
                raise ValueError("GREEN and refactor must pass the same focused command as RED")
    if referenced != set(events):
        raise ValueError("unreferenced native observations are not accepted")


def append_report(root: Path, journal: dict[str, Any], inputs: dict[str, Any]) -> bool:
    report = {key: inputs.get(key) for key in ("batch_id", "results", "native_observations")}
    validate_report(root, journal, report)
    if report in journal["reports"]:
        return False
    prior = [r for r in journal["reports"] if r["batch_id"] == report["batch_id"]]
    if any(all(t["status"] == "complete" for t in r["results"]) for r in prior):
        raise ValueError("completed batch report is immutable")
    completed = {t["task_id"]: t for r in prior for t in r["results"] if t["status"] == "complete"}
    if any(t != completed[t["task_id"]] for t in report["results"] if t["task_id"] in completed):
        raise ValueError("previously complete task results must be carried forward unchanged")
    carried_ids = {ref for t in completed.values() for ref in t["evidence_event_ids"]}
    previous_events = {e["event_id"]: e for r in journal["reports"] for e in r["native_observations"]}
    for event in report["native_observations"]:
        if event["event_id"] in previous_events and (event["event_id"] not in carried_ids or previous_events[event["event_id"]] != event):
            raise ValueError("only unchanged completed task observations may be carried forward")
    journal["reports"].append(report)
    return True


def validate_journal(root: Path, journal: dict[str, Any], metadata: dict[str, Any]) -> None:
    required = {"schema_version", "tasks_file", "fingerprints", "metadata_sha256", "batches", "task_units", "reports"}
    lineage = {"prior_journal_file", "prior_journal_sha256", "reconciliation_event_id", "reconciliation_reason"}
    if not required <= journal.keys() or journal.keys() - required not in (set(), lineage):
        raise ValueError("journal fields are incomplete or unknown")
    if not isinstance(journal["batches"], list) or not isinstance(journal["reports"], list) or not isinstance(journal["task_units"], dict):
        raise ValueError("journal batches, reports, or task_units malformed")
    seen = []
    for ordinal, batch in enumerate(journal["batches"], 1):
        tasks = batch.get("tasks")
        if batch.get("id") != f"B{ordinal:03d}" or not isinstance(tasks, list) or not tasks or any(not isinstance(t, str) for t in tasks):
            raise ValueError("frozen batch IDs or tasks malformed")
        seen.extend(tasks)
        if any(t not in metadata["tasks"] or journal["task_units"].get(t) != metadata["tasks"][t]["tdd_unit"] for t in tasks):
            raise ValueError("frozen task identity does not match approved metadata")
        if batch.get("tdd_units") != list(dict.fromkeys(journal["task_units"][t] for t in tasks)):
            raise ValueError("frozen batch TDD units do not match task identity")
        text_field(batch["agent"], "frozen agent route")
        if batch.get("tdd_not_applicable_reason") != non_tdd_reason(batch):
            raise ValueError("TDD exception must match the frozen native route")
    if len(seen) != len(set(seen)) or set(seen) != set(journal["task_units"]):
        raise ValueError("frozen tasks must appear exactly once with complete unit mapping")
    replay = {**journal, "reports": []}
    for report in journal["reports"]:
        if not isinstance(report, dict) or set(report) != {"batch_id", "results", "native_observations"}:
            raise ValueError("invalid persisted report fields")
        if not append_report(root, replay, report):
            raise ValueError("duplicate persisted report")


def task_results(root: Path, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    """Validate supplied evidence; never execute workers or authenticate the caller.

    Only the native parent may supply native_observations, independently of worker
    blocks. This JSON boundary cannot establish that a caller is that parent.
    Deterministic fixture success is therefore always native-unqualified.
    """
    from .execution_control import exclusive_ledger
    from .helpers.mutation import snapshot_write_target, write_file_atomic

    action = inputs.get("action")
    if action not in {"start", "record", "inspect"} or mode not in {"apply", "dry_run", "read_only"}:
        raise ValueError("invalid task-results action or mode")
    if mode == "read_only" and action != "inspect":
        raise ValueError("read_only supports inspect only")
    root = root.resolve()
    tasks, path = result_path(root, inputs.get("tasks_file")), result_path(root, inputs.get("journal_file"))
    if path.parent != tasks.parent / ".process/task-results" or not re.fullmatch(r"[A-Za-z0-9_-]+\.json", path.name):
        raise ValueError("journal_file must be a named JSON file in the feature .process/task-results directory")
    # One feature-wide lock prevents concurrent starts from creating unrelated journals.
    lock = exclusive_ledger(path.parent / "journal-writer.json") if mode == "apply" and action != "inspect" else nullcontext()
    try:
        with lock:
            binding, metadata = current_binding(root, tasks)
            snapshot = snapshot_write_target(path, root)
            changed = False
            if snapshot["exists"]:
                journal = decode_object(snapshot["content"])
                if (journal.get("schema_version") != SCHEMA or journal.get("tasks_file") != inputs["tasks_file"]
                        or any(journal.get(k) != v for k, v in binding.items())):
                    raise ValueError("stale task result binding; explicit parent reconciliation and successor journal required")
                validate_journal(root, journal, metadata)
            elif action == "start":
                journal = start_journal(root, inputs, tasks, path, binding, metadata)
                changed = True
            else:
                raise ValueError("task result journal missing; start it before recording or inspecting")
            if action == "record":
                changed = append_report(root, journal, inputs)
            if changed and mode == "apply":
                if current_binding(root, tasks)[0] != binding:
                    raise ValueError("source changed before journal commit")
                write_file_atomic(path, canonical_bytes(journal).decode("utf-8") + "\n", trust_root=root, expected_snapshot=snapshot)
            latest = {report["batch_id"]: report for report in journal["reports"]}
            unfinished = any(r["status"] == "unfinished" for report in latest.values() for r in report["results"])
            return {"journal": journal, "journal_path": inputs["journal_file"],
                    "disposition": "checkpoint_required" if unfinished else "continue",
                    "reasons": ["unfinished_task_results"] if unfinished else [],
                    "helper_exit_code": int(unfinished and action == "record"),
                    "authorization_granted": False, "native_qualification": "pending",
                    "writes_state": changed and mode == "apply"}
    except (OSError, TypeError, KeyError, AttributeError, UnicodeError) as exc:
        raise ValueError(f"task result journal invalid or inaccessible: {exc}") from exc
