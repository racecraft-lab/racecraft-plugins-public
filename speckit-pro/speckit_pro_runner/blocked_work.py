"""The blocked-work record (ADR 0012): what a spent retry ladder leaves behind in the run ledger.

When a failing check exhausts its ladder, the tasks that own it become blocked-for-UAT,
and so does every task that depends on them. A check with no owning task blocks its gate
and nothing else. A block is terminal inside the run: it records incomplete or unverified
work, never completion, and no later resume or human disposition changes that.

The record lives at `ledger["blocked_work"]`:

- `causes[check_sha256]` keeps the evidence once per cause: the check, its final failure
  every ladder attempt, retained work and the unblock note.
- `entries["task:T003"]` or `entries["gate:G4"]` keeps one blocked unit. An exhausted unit
  is a root. A dependent skip links to its roots and records no attempt of its own.

The functions take plain dicts and know nothing of the ledger file.
"""

from __future__ import annotations

from typing import Any, NamedTuple

BLOCK_EXHAUSTED_CHECK = "block-exhausted-check"
ACCEPT_BLOCKED_GAP = "accept-blocked-gap"
GAP_ACCEPTED = "gap_accepted"

ENTRY_KEYS = {"kind", "unit", "reason", "causes", "roots", "attempted", "retained_work", "verification", "unblock",
              "plan_sha256", "blocked_at", "disposition"}
DISPOSITION_KEYS = {"decision", "event_id", "recorded_at"}


def entry_id(kind: str, unit: str) -> str:
    return f"{kind}:{unit}"


class Block(NamedTuple):
    """One exhausted check: its evidence, its owners (none for an ownerless gate) and the plan's task graph."""

    check: str
    cause: dict[str, Any]
    owners: list[str]
    gate: str | None
    depends_on: dict[str, list[str]]
    tdd_units: dict[str, str]
    plan_sha256: str | None
    retained_work: list[str]
    unblock: str
    now: float


def _entry(block: Block, kind: str, unit: str, **fields: Any) -> dict[str, Any]:
    record = {"kind": kind, "unit": unit, "reason": "check_exhausted", "causes": [block.check], "roots": [],
              "attempted": True, "retained_work": block.retained_work, "verification": "failed",
              "unblock": block.unblock, "plan_sha256": block.plan_sha256, "blocked_at": block.now,
              "disposition": None, **fields}
    if kind == "task":
        record["tdd_unit"] = block.tdd_units[unit]
    return record


def dependents(depends_on: dict[str, list[str]], roots: list[str]) -> list[str]:
    """Every task that depends on a root, regardless of the sidecar object ordering."""
    blocked = set(roots)
    while True:
        discovered = {task_id for task_id, deps in depends_on.items() if blocked.intersection(deps)} - blocked
        if not discovered:
            break
        blocked.update(discovered)
    return [task_id for task_id in depends_on if task_id in blocked and task_id not in roots]


def block_exhausted_check(record: dict[str, Any], block: Block) -> list[str]:
    """Record the block and return the entry IDs it created. A blocked unit stays blocked; a repeat adds cause and root links."""
    record["causes"].setdefault(block.check, {**block.cause, "retained_work": block.retained_work,
                                            "unblock": block.unblock})
    entries = record["entries"]
    if block.gate is not None:
        roots = {entry_id("gate", block.gate): _entry(block, "gate", block.gate)}
    else:
        roots = {entry_id("task", task): _entry(block, "task", task) for task in block.owners}
    skipped = {entry_id("task", task): _entry(block, "task", task, reason="dependency_blocked", attempted=False,
                                              roots=sorted(roots), verification="not_run")
               for task in dependents(block.depends_on, block.owners)}
    created = []
    for key, entry in {**roots, **skipped}.items():
        if key not in entries:
            entries[key] = entry
            created.append(key)
        else:
            entries[key]["causes"] = sorted({*entries[key]["causes"], block.check})
            if entry["reason"] == "dependency_blocked" and entries[key]["reason"] == "dependency_blocked":
                entries[key]["roots"] = sorted({*entries[key]["roots"], *entry["roots"]})
    return created


def _entries(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    return list(ledger.get("blocked_work", {}).get("entries", {}).values())


def blocked_scope(ledger: dict[str, Any]) -> set[str]:
    """The task units and gates that no request in the original run may dispatch again."""
    return {f"unit:{entry['tdd_unit']}" if entry["kind"] == "task" else entry_id("gate", entry["unit"])
            for entry in _entries(ledger)}


def blocked_check(ledger: dict[str, Any], check: str) -> bool:
    return check in ledger.get("blocked_work", {}).get("causes", {})


def disposition_event_ids(ledger: dict[str, Any]) -> set[str]:
    return {entry["disposition"]["event_id"] for entry in _entries(ledger) if entry["disposition"] is not None}


def accept_gap(ledger: dict[str, Any], key: str, event_id: str, now: float) -> None:
    """Record a human's acceptance of one gap. Only the disposition changes; the block stays a block."""
    entry = ledger.get("blocked_work", {}).get("entries", {}).get(key)
    if entry is None:
        raise ValueError("no blocked entry to accept")
    if entry["disposition"] is not None:
        raise ValueError("this blocked entry already has a human disposition")
    entry["disposition"] = {"decision": GAP_ACCEPTED, "event_id": event_id, "recorded_at": now}


def validate_blocked_work(ledger: dict[str, Any]) -> None:
    """The record is closed, every entry links to its cause and roots, and no entry reads as complete."""
    if "blocked_work" not in ledger:
        return
    record = ledger["blocked_work"]
    if not isinstance(record, dict) or set(record) != {"causes", "entries"} or not all(
            isinstance(record[name], dict) for name in record):
        raise ValueError("invalid blocked-work record")
    for key, entry in record["entries"].items():
        if (not isinstance(entry, dict) or not ENTRY_KEYS <= set(entry) <= ENTRY_KEYS | {"tdd_unit"}
                or key != entry_id(str(entry["kind"]), str(entry["unit"])) or entry["kind"] not in {"task", "gate"}
                or not isinstance(entry["causes"], list) or not entry["causes"]
                or any(cause not in record["causes"] for cause in entry["causes"])
                or entry["reason"] not in {"check_exhausted", "dependency_blocked"}
                or (entry["reason"] == "dependency_blocked") != (not entry["attempted"])
                or (entry["reason"] == "dependency_blocked") != bool(entry["roots"])
                or ("tdd_unit" in entry) != (entry["kind"] == "task")
                or any(root not in record["entries"] or not record["entries"][root].get("attempted") or root == key
                       for root in entry["roots"])
                or (entry["disposition"] is not None and (
                    set(entry["disposition"]) != DISPOSITION_KEYS or entry["disposition"]["decision"] != GAP_ACCEPTED))):
            raise ValueError("invalid blocked-work entry")
