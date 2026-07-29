"""Non-live partition guards for G56R-004 smoke planning and sealing.

This task-level surface only protects reserved and outcome-bearing objectives.
The bounded smoke plan, exact-treatment checks, and repository-safe summaries
are added by the later smoke tasks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import codex_policy_controls as controls


FROZEN_PARTITION_ENTRIES_PATH = (
    Path(__file__).resolve().parent.parent
    / "fixtures-codex-controls"
    / "partition-registry-entries.json"
)


def partition_entries(
    path: Path = FROZEN_PARTITION_ENTRIES_PATH,
) -> list[dict[str, Any]]:
    return controls.load_partition_entries(path)


def _smoke_partition(entries: list[dict[str, Any]]) -> dict[str, Any]:
    smoke = [
        entry
        for entry in entries
        if entry.get("partition_type") == "calibration"
        and entry.get("qualification_eligible") is False
    ]
    if len(smoke) != 1:
        raise controls.ControlContractError(
            "exactly one non-qualification calibration partition is required"
        )
    return smoke[0]


def guard_plan_objectives(
    objective_ids: Any, entries: list[dict[str, Any]] | None = None
) -> None:
    """Refuse any operator plan outside the G56R-004 smoke partition."""

    registered = entries if entries is not None else partition_entries()
    if not isinstance(objective_ids, (list, tuple)) or not objective_ids:
        raise controls.ControlContractError("a smoke plan must name objective ids")
    reserved = controls.reserved_partition_entry(registered)
    rows = [
        {"row_id": f"plan-{index}", "objective_id": objective}
        for index, objective in enumerate(objective_ids)
    ]
    controls.assert_reserved_partition_untouched(rows, reserved)
    admitted = set(_smoke_partition(registered)["objective_ids"])
    extra = set(objective_ids) - admitted
    if extra:
        raise controls.ControlContractError(
            f"smoke plan consumes objectives outside its partition: {sorted(extra)}"
        )


def plan_objectives(
    entries: list[dict[str, Any]] | None = None,
) -> tuple[str, ...]:
    registered = entries if entries is not None else partition_entries()
    objectives = tuple(sorted(_smoke_partition(registered)["objective_ids"]))
    guard_plan_objectives(objectives, registered)
    return objectives


def guard_smoke_record(
    record: Any, entries: list[dict[str, Any]] | None = None
) -> None:
    """Refuse reserved, scored, outcome-bearing, or non-calibration smoke rows."""

    if not isinstance(record, dict):
        raise controls.ControlContractError("a smoke record must be an object")
    registered = entries if entries is not None else partition_entries()
    reserved = controls.reserved_partition_entry(registered)
    controls.assert_reserved_partition_untouched([record], reserved)
    smoke = _smoke_partition(registered)
    if record.get("partition_id") != smoke["partition_id"]:
        raise controls.ControlContractError("smoke record partition_id drift")
    if record.get("partition_type") != "calibration":
        raise controls.ControlContractError(
            "selection and cohort-lock objectives are forbidden"
        )
    if record.get("scored") is not False or record.get("outcome_bearing") is not False:
        raise controls.ControlContractError(
            "smoke records must be non-scored and non-outcome-bearing"
        )
    objective_ids = record.get("objective_ids")
    if not isinstance(objective_ids, list) or not objective_ids:
        raise controls.ControlContractError("smoke record objective_ids are missing")
    admitted = set(smoke["objective_ids"])
    extra = set(objective_ids) - admitted
    if extra:
        raise controls.ControlContractError(
            f"smoke record consumes objectives outside its partition: {sorted(extra)}"
        )


__all__ = (
    "FROZEN_PARTITION_ENTRIES_PATH",
    "guard_plan_objectives",
    "guard_smoke_record",
    "partition_entries",
    "plan_objectives",
)
