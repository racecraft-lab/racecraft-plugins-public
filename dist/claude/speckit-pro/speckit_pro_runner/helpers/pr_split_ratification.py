"""Decide whether autopilot may ratify a budget-driven PR split itself.

The repository's per-PR path cap can force the planner to split an approved PR
order into smaller increments. Such a split is routine when it only narrows the
approved groups to meet the budget, so autopilot ratifies it and records
`ratified_by=autopilot`. The operator is asked only when the split adds or drops
scope, or drops, merges, or reorders approved groups (`scope_changing_pr_split`).
An increment over the cap is a size finding: the orchestrator re-slices it or
commits a typed reviewability exception. This helper reads only its request
inputs and never writes a file. Malformed input is an `input_error` the
orchestrator repairs from the layer plan and retries; it is never a ratification.
"""

from __future__ import annotations

import re
from typing import Any

from ..envelope import diagnostic, response

ALLOWED_INPUTS = frozenset({"approved_groups", "increments", "active_scope", "path_budget"})
GROUP_FIELDS = frozenset({"group_id", "scope"})
INCREMENT_FIELDS = frozenset({"increment_id", "group_id", "scope", "production_paths", "total_paths"})
BUDGET_FIELDS = frozenset({"production_paths", "total_paths"})
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
# Findings are reported in this order, one per code.
SIZE_ONLY = frozenset({"reviewability_exception_needed"})
REPAIR = {
    "owner": "orchestrator",
    "retry": "ratify-pr-split",
}
FINDING_ORDER = (
    "group_added",
    "group_merged",
    "scope_duplicated",
    "scope_added",
    "group_dropped",
    "scope_dropped",
    "group_reordered",
    "reviewability_exception_needed",
)


class _InvalidInput(ValueError):
    pass


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.match(value):
        raise _InvalidInput(f"{field} must match {IDENTIFIER.pattern}")
    return value


def _count(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise _InvalidInput(f"{field} must be a non-negative integer")
    return value


def _fields(raw: Any, allowed: frozenset[str], field: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise _InvalidInput(f"{field} must be an object")
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise _InvalidInput(f"{field} has unknown fields: {', '.join(unknown)}")
    missing = sorted(allowed - set(raw))
    if missing:
        raise _InvalidInput(f"{field} is missing: {', '.join(missing)}")
    return raw


def _scope(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise _InvalidInput(f"{field} must be a non-empty list")
    items = [_identifier(item, f"{field}[{index}]") for index, item in enumerate(value)]
    if len(set(items)) != len(items):
        raise _InvalidInput(f"{field} repeats an item")
    return items


def _entries(value: Any, field: str, allowed: frozenset[str], key: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise _InvalidInput(f"{field} must be a non-empty list")
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(value):
        entry = dict(_fields(raw, allowed, f"{field}[{index}]"))
        entry[key] = _identifier(entry[key], f"{field}[{index}].{key}")
        if entry[key] in seen:
            raise _InvalidInput(f"{field}[{index}].{key} repeats {entry[key]}")
        seen.add(entry[key])
        entry["scope"] = _scope(entry["scope"], f"{field}[{index}].scope")
        entries.append(entry)
    return entries


def _parse(inputs: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], dict[str, int]]:
    unknown = sorted(set(inputs) - ALLOWED_INPUTS)
    if unknown:
        raise _InvalidInput(f"unknown inputs: {', '.join(unknown)}")
    groups = _entries(inputs.get("approved_groups"), "approved_groups", GROUP_FIELDS, "group_id")
    owner: dict[str, str] = {}
    for group in groups:
        for item in group["scope"]:
            if item in owner:
                raise _InvalidInput(f"{item} belongs to both {owner[item]} and {group['group_id']}")
            owner[item] = group["group_id"]
    increments = _entries(inputs.get("increments"), "increments", INCREMENT_FIELDS, "increment_id")
    for index, increment in enumerate(increments):
        increment["group_id"] = _identifier(increment["group_id"], f"increments[{index}].group_id")
        for field in BUDGET_FIELDS:
            increment[field] = _count(increment[field], f"increments[{index}].{field}")
    active = _scope(inputs.get("active_scope"), "active_scope")
    raw_budget = _fields(inputs.get("path_budget"), BUDGET_FIELDS, "path_budget")
    budget = {field: _count(raw_budget[field], f"path_budget.{field}") for field in sorted(BUDGET_FIELDS)}
    return groups, increments, active, budget


def _findings(
    groups: list[dict[str, Any]],
    increments: list[dict[str, Any]],
    active: list[str],
    budget: dict[str, int],
) -> list[dict[str, str]]:
    order = {group["group_id"]: index for index, group in enumerate(groups)}
    owner = {item: group["group_id"] for group in groups for item in group["scope"]}
    found: dict[str, list[str]] = {}

    def note(code: str, detail: str) -> None:
        found.setdefault(code, []).append(detail)

    # An item moved into another group is reported once, as group_merged.
    carried = {item for increment in increments for item in increment["scope"]}
    # A split is a partition: every approved item lands in exactly one increment.
    holders: dict[str, list[str]] = {}
    for increment in increments:
        for item in increment["scope"]:
            holders.setdefault(item, []).append(increment["increment_id"])
    for item, names in holders.items():
        if len(names) > 1:
            note("scope_duplicated", f"{item} appears in {', '.join(names)}")
    for increment in increments:
        name, group_id = increment["increment_id"], increment["group_id"]
        if group_id not in order:
            note("group_added", f"{name} names group {group_id}, which is not in the approved order")
            continue
        for item in increment["scope"]:
            if item not in owner:
                note("scope_added", f"{name} carries {item}, which no approved group holds")
            elif owner[item] != group_id:
                note("group_merged", f"{name} in group {group_id} carries {item} from group {owner[item]}")
        over = [
            f"{increment[field]} {field.replace('_', ' ')} (cap {budget[field]})"
            for field in sorted(BUDGET_FIELDS)
            if increment[field] > budget[field]
        ]
        if over:
            note("reviewability_exception_needed", f"{name} has {' and '.join(over)}")

    approved_items = set(owner)
    for item in active:
        if item not in approved_items:
            note("scope_added", f"active {item} is in no approved group")
    active_items = set(active)
    for group in groups:
        group_id = group["group_id"]
        if not any(increment["group_id"] == group_id for increment in increments):
            note("group_dropped", f"approved group {group_id} has no increment")
        missing = [item for item in group["scope"] if item not in carried]
        if missing:
            note("scope_dropped", f"group {group_id} loses {', '.join(missing)}")
        inactive = [item for item in group["scope"] if item not in active_items]
        if inactive:
            note("scope_dropped", f"group {group_id} holds {', '.join(inactive)}, which is no longer active")

    sequence = [order[increment["group_id"]] for increment in increments if increment["group_id"] in order]
    for position in range(1, len(sequence)):
        if sequence[position] < sequence[position - 1]:
            later = [increment for increment in increments if increment["group_id"] in order][position]
            note(
                "group_reordered",
                f"{later['increment_id']} (group {later['group_id']}) comes after a later approved group",
            )
            break

    return [{"code": code, "detail": "; ".join(found[code])} for code in FINDING_ORDER if code in found]


def run_pr_split_ratification_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Runner helper entry point: a pure decision over request inputs."""
    try:
        groups, increments, active, budget = _parse(request.inputs)
    except _InvalidInput as error:
        return response(
            "input_error",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "invalid_input",
                    str(error),
                    remediation_summary="The split evidence is incomplete, so regenerate the split evidence from the layer plan.",
                    remediation_actions=[
                        "Pass the approved groups in order with their scope, the increments in order with their "
                        + "group, scope, and path counts, the active requirement, story, and task IDs, and the "
                        + "per-PR path budget.",
                        "Retry the request. Record owner_ratification=pending until the helper ratifies the split.",
                    ],
                )
            ],
            data={
                "helper_id": entry.helper_id,
                "writes_state": False,
                "repair": {**REPAIR, "action": "Regenerate the split evidence from the layer plan and retry"},
            },
        )
    findings = _findings(groups, increments, active, budget)
    extra: dict[str, Any] = {}
    if findings:
        codes = [finding["code"] for finding in findings]
        ratification, ratified_by = "pending", None
        record = ["owner_ratification=pending", "ratification_blockers=" + ",".join(codes)]
        if set(codes) <= SIZE_ONLY:
            decision = "reslice_required"
            reason = "the split leaves an increment over the path cap: " + ", ".join(codes)
            extra["repair"] = {
                **REPAIR,
                "action": "Re-slice the over-cap increment, or commit a typed reviewability exception "
                + "when it cannot split further, then rerun",
            }
        else:
            decision = "operator_required"
            reason = "the split changes approved delivery: " + ", ".join(codes)
            extra["stop_reason"] = "scope_changing_pr_split"
    else:
        decision, ratification, ratified_by = "autopilot_ratified", "ratified", "autopilot"
        reason = (
            f"budget-driven split of {len(groups)} approved groups into {len(increments)} increments keeps the "
            f"approved order, each group's scope, and all {len(active)} active requirements, stories, and tasks; "
            f"every increment is within {budget['production_paths']} production and "
            f"{budget['total_paths']} total paths"
        )
        record = ["owner_ratification=ratified", "ratified_by=autopilot", f"ratification_reason={reason}"]
    return response(
        "ok",
        request_id=request.request_id,
        data={
            "helper_id": entry.helper_id,
            "operation": entry.operation,
            "writes_state": False,
            "decision": decision,
            "owner_ratification": ratification,
            "ratified_by": ratified_by,
            "reason": reason,
            "findings": findings,
            "record": record,
            **extra,
        },
    )
