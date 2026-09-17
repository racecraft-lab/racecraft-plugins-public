"""Versioned task-definition validation and bounded native dispatch planning.

This module neither runs agents nor declares worker effects verified. Completed
IDs are an assertion by the native orchestrator *after* result/effect
reconciliation; a checkbox alone never authorizes skipping work.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any

from .formal.selection import SelectionError, unique_object


class TaskExecutionError(ValueError):
    """Task metadata cannot safely authorize a dispatch."""


def fingerprints(spec: str, plan: str, tasks: str) -> dict[str, str]:
    """Bind all source text, excluding only task-checkbox completion state."""
    definitions = re.sub(r"(?m)^(\s*-\s+\[)[ xX](\]\s+T[0-9]{3,})", r"\1 \2", tasks)
    return {name: hashlib.sha256(text.encode("utf-8")).hexdigest() for name, text in (
        ("spec_sha256", spec), ("plan_sha256", plan), ("tasks_sha256", definitions)
    )}


def owned_path(value: Any, root: Path) -> str:
    """Canonicalize contained ownership; compare aliases conservatively later."""
    if not isinstance(value, str) or not value or any(c in value for c in "\\\x00:$*?[]") or value.startswith("~"):
        raise TaskExecutionError("owns must contain canonical repository-relative paths")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or any(p in {".", ".."} for p in path.parts) or not path.parts:
        raise TaskExecutionError(f"noncanonical owned path: {value}")
    try:
        resolved = (root / value).resolve().relative_to(root.resolve()).as_posix()
    except (OSError, RuntimeError, ValueError) as exc:
        raise TaskExecutionError(f"owned path escapes repository: {value}") from exc
    if resolved == ".":
        raise TaskExecutionError("repository root ownership is not a bounded task")
    return resolved


def overlaps(left: str, right: str) -> bool:
    a, b = path_key(left).split("/"), path_key(right).split("/")
    return a[:len(b)] == b or b[:len(a)] == a


def path_key(path: str) -> str:
    """Use a conservative comparison on case/normalization-insensitive hosts."""
    return unicodedata.normalize("NFC", path).casefold()


def task_references(title: str, root: Path) -> list[str]:
    """Keep explicit path-like references, including root files and escapes.

    The legacy parser is a navigation aid and intentionally discards unresolved
    or escaping references. It cannot authorize disjoint write ownership.
    Ambiguous filename-like tokens conservatively require declared ownership.
    """
    references: set[str] = set()
    root_names = {"Makefile", "Dockerfile", "Justfile", "Gemfile", "Rakefile", "Procfile", "LICENSE", "NOTICE", "README"}
    for code_span, prose in re.findall(r"`([^`]+)`|(\S+)", title):
        for word in (code_span or prose).split():
            token = word.strip("`'\"()[]{}").rstrip(",;.!?")
            if not token or "://" in token:
                continue
            token = re.sub(r":\d+(?:-\d+)?$", "", token).split("#", 1)[0]
            explicit_path = (bool(code_span) and "/" in token) or token.startswith(("./", "../", "/", "~/")) or "\\" in token
            if explicit_path or re.search(r"\.[A-Za-z][A-Za-z0-9_-]*$", token) or token in root_names or (root / token).is_file():
                references.add(token)
    return sorted(references)


def filesystem_identities(path: Path) -> set[tuple[int, int]]:
    """Inventory a bounded owned tree without following hidden alias edges.

    Hard links can alias outside the repository; reject them rather than guess
    containment. Symlink descendants require narrower explicit ownership.
    Identities remain internal to planning, never native prompt payloads.
    """
    pending = [path]
    identities: set[tuple[int, int]] = set()
    visited = 0
    while pending:
        current = pending.pop()
        try:
            info = current.lstat()
        except FileNotFoundError:
            if current == path:
                continue  # Future paths are still compared by normalized name.
            raise TaskExecutionError(f"owned tree changed during inspection: {path}")
        except OSError as exc:
            raise TaskExecutionError(f"cannot inspect owned path: {current}") from exc
        visited += 1
        if visited > 10000:
            raise TaskExecutionError("owned tree exceeds 10000 entries; declare narrower owned paths")
        if stat.S_ISLNK(info.st_mode) or (stat.S_ISREG(info.st_mode) and info.st_nlink != 1):
            raise TaskExecutionError(f"owned tree contains a symlink or hard-link alias: {current}")
        if not stat.S_ISREG(info.st_mode) and not stat.S_ISDIR(info.st_mode):
            raise TaskExecutionError(f"owned path is not an ordinary file or directory: {current}")
        identities.add((info.st_dev, info.st_ino))
        if stat.S_ISDIR(info.st_mode):
            try:
                with os.scandir(current) as children:
                    for child in children:
                        if visited + len(pending) >= 10000:
                            raise TaskExecutionError("owned tree exceeds 10000 entries; declare narrower owned paths")
                        pending.append(Path(child.path))
            except OSError as exc:
                raise TaskExecutionError(f"cannot inspect owned directory: {current}") from exc
    return identities


def string_list(value: Any, field: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        raise TaskExecutionError(f"{field} must be an array of nonempty strings")
    if len(value) != len(set(value)) or (nonempty and not value):
        raise TaskExecutionError(f"{field} must be unique and satisfy its minimum length")
    return value


def validate_metadata(text: str, records: list[dict[str, Any]], root: Path,
                      expected: dict[str, str], completed: Any) -> dict[str, dict[str, Any]]:
    try:
        data = json.loads(text, object_pairs_hook=unique_object)
    except (json.JSONDecodeError, UnicodeError, SelectionError) as exc:
        raise TaskExecutionError(f"invalid metadata JSON: {exc}") from exc
    if not isinstance(data, dict) or set(data) != {"schema_version", "fingerprints", "tasks"}:
        raise TaskExecutionError("metadata requires exactly schema_version, fingerprints, tasks")
    if data["schema_version"] != "task-execution.v1" or data["fingerprints"] != expected:
        raise TaskExecutionError("metadata schema or source fingerprints are stale; reconcile definitions")
    entries = data["tasks"]
    ids = [r["id"] for r in records]
    if not isinstance(entries, dict) or set(entries) != set(ids) or len(ids) != len(set(ids)):
        raise TaskExecutionError("metadata must cover exactly every unique task ID")
    completed_ids = string_list(completed, "completed_tasks")
    if set(completed_ids) != {r["id"] for r in records if r["status"] == "done"}:
        raise TaskExecutionError("checked tasks require exact parent-reconciled completed_tasks")
    seen: set[str] = set()
    normalized: dict[str, dict[str, Any]] = {}
    units: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        task_id = record["id"]
        entry = entries[task_id]
        normalized[task_id] = validate_entry(entry, task_id, record, root, seen)
        if task_id in completed_ids and not set(entry["depends_on"]) <= set(completed_ids):
            raise TaskExecutionError(f"completed {task_id} has unfinished prerequisites; reconcile effects")
        units.setdefault(entry["tdd_unit"], []).append(record)
        seen.add(task_id)
    validate_units(units, normalized, ids, set(completed_ids))
    # Inspect each distinct ownership root once in this validation, not once
    # per task. This is a local proof input, never a cross-run verification cache.
    roots = {path for entry in normalized.values() for path in entry["owns"]}
    identities = {path: filesystem_identities(root / path) for path in roots}
    for entry in normalized.values():
        entry["_filesystem_ids"] = set().union(*(identities[path] for path in entry["owns"]))
    return normalized


def validate_entry(entry: Any, task_id: str, record: dict[str, Any], root: Path,
                   predecessors: set[str]) -> dict[str, Any]:
    if not isinstance(entry, dict) or set(entry) != {"capability_group", "depends_on", "owns", "tdd_unit"}:
        raise TaskExecutionError(f"invalid metadata fields for {task_id}")
    for key in ("capability_group", "tdd_unit"):
        if not isinstance(entry[key], str) or not re.fullmatch(r"[a-z][a-z0-9-]*", entry[key]):
            raise TaskExecutionError(f"{task_id}.{key} must be a lowercase stable identifier")
    dependencies = string_list(entry["depends_on"], f"{task_id}.depends_on")
    if not set(dependencies) <= predecessors:
        raise TaskExecutionError(f"{task_id} has unknown, cyclic, or forward dependencies; order prerequisites first")
    owns = [owned_path(path, root) for path in string_list(entry["owns"], f"{task_id}.owns", nonempty=True)]
    if len({path_key(path) for path in owns}) != len(owns):
        raise TaskExecutionError(f"{task_id} contains aliased owned paths")
    for reference in task_references(record["title"], root):
        canonical = owned_path(reference.removeprefix("./"), root)
        # Ownership may cover a directory, never merely a sibling or child.
        if not any(path_key(canonical) == path_key(p) or path_key(canonical).startswith(path_key(p) + "/") for p in owns):
            raise TaskExecutionError(f"{task_id} reference is not owned: {reference}")
    return {**entry, "owns": owns}


def validate_units(units: dict[str, list[dict[str, Any]]], entries: dict[str, dict[str, Any]],
                   ids: list[str], completed: set[str]) -> None:
    positions = {task_id: i for i, task_id in enumerate(ids)}
    for unit, members in units.items():
        indices = [positions[r["id"]] for r in members]
        routes = {(r["phase_instance"], r["agent"], entries[r["id"]]["capability_group"]) for r in members}
        if len(members) > 4 or indices != list(range(indices[0], indices[-1] + 1)) or len(routes) != 1:
            raise TaskExecutionError(f"TDD unit {unit} must be adjacent, at most four tasks, and share phase/agent/capability")
        done = [r["id"] in completed for r in members]
        if any(done) and not all(done):
            raise TaskExecutionError(f"TDD unit {unit} is partially marked complete; reconcile the entire behavioral unit")


def make_batches(records: list[dict[str, Any]], entries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    batches: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    index = 0
    while index < len(records):
        record = records[index]
        entry = entries[record["id"]]
        unit: list[dict[str, Any]] = []
        while index < len(records) and entries[records[index]["id"]]["tdd_unit"] == entry["tdd_unit"]:
            unit.append(records[index])
            index += 1
        if record["status"] == "done":
            flush_batch(pending, entries, batches)
            continue
        if pending:
            first = pending[0]
            compatible = (first["phase_instance"], first["agent"], entries[first["id"]]["capability_group"]) == (
                record["phase_instance"], record["agent"], entry["capability_group"])
            if not compatible or len(pending) + len(unit) > 4:
                flush_batch(pending, entries, batches)
        pending.extend(unit)
    flush_batch(pending, entries, batches)
    return batches


def flush_batch(pending: list[dict[str, Any]], entries: dict[str, dict[str, Any]],
                batches: list[dict[str, Any]]) -> None:
    if not pending:
        return
    first = pending[0]
    batches.append({
        "id": f"B{len(batches) + 1:03d}", "agent": first["agent"], "group": first["group"],
        "phase_instance": first["phase_instance"],
        "capability_group": entries[first["id"]]["capability_group"],
        "tasks": [r["id"] for r in pending],
        "tdd_units": list(dict.fromkeys(entries[r["id"]]["tdd_unit"] for r in pending)),
        "owns": sorted({p for r in pending for p in entries[r["id"]]["owns"]}),
        "_filesystem_ids": set().union(*(entries[r["id"]]["_filesystem_ids"] for r in pending)),
        "parallel": all(r["parallel"] for r in pending),
        "depends_on": sorted({d for r in pending for d in entries[r["id"]]["depends_on"]} - {r["id"] for r in pending}),
    })
    pending.clear()


def batch_waves(batches: list[dict[str, Any]], wave_size: int) -> list[list[str]]:
    """Only co-schedule proven-independent adjacent batches within the host cap."""
    waves: list[list[str]] = []
    pending: list[dict[str, Any]] = []
    for batch in batches:
        if pending and not can_share_wave(batch, pending, wave_size):
            waves.append([b["id"] for b in pending])
            pending = []
        pending.append(batch)
    if pending:
        waves.append([b["id"] for b in pending])
    return waves


def can_share_wave(batch: dict[str, Any], pending: list[dict[str, Any]], wave_size: int) -> bool:
    if len(pending) >= wave_size or not batch["parallel"]:
        return False
    for other in pending:
        if not other["parallel"] or (batch["phase_instance"], batch["agent"]) != (other["phase_instance"], other["agent"]):
            return False
        if set(batch["depends_on"]) & set(other["tasks"]):
            return False
        if batch["_filesystem_ids"] & other["_filesystem_ids"]:
            return False
        if any(overlaps(left, right) for left in batch["owns"] for right in other["owns"]):
            return False
    return True
