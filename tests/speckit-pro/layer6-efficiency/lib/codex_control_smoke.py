"""Non-live partition guards for G56R-004 smoke planning and sealing."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import codex_policy_controls as controls


FROZEN_PARTITION_ENTRIES_PATH = (
    Path(__file__).resolve().parent.parent
    / "fixtures-codex-controls"
    / "partition-registry-entries.json"
)
FROZEN_REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent
    / "fixtures-codex-controls"
    / "policy-control-registry.json"
)
FROZEN_REPLAY_CASES_PATH = (
    Path(__file__).resolve().parent.parent
    / "fixtures-codex-controls"
    / "replay-cases.json"
)
_AUTHENTICATION_MODE = "chatgpt_subscription"
_WITHHELD = "withheld"
_UNRUN = "unrun"
_CODEX_CONTROL_IDS_BY_KIND = {
    "unpinned": "g56r-004-unpinned-control",
    "adaptive": "g56r-004-adaptive-control",
    "justified_high_effort": "g56r-004-justified-high-effort-control",
}
_RAW_TOKEN_CEILING_MEMBERS = [
    "input_tokens",
    "output_tokens",
    "cached_input_tokens",
]
_REQUIRED_CACHE_PAIRS = {
    frozenset((
        "g56r-004-unpinned-control",
        "g56r-004-adaptive-control",
    )),
    frozenset((
        "g56r-004-unpinned-control",
        "g56r-004-justified-high-effort-control",
    )),
    frozenset((
        "g56r-004-adaptive-control",
        "g56r-004-justified-high-effort-control",
    )),
}
_RAW_CAPTURE_MEMBERS = {
    "live_model_text",
    "messages",
    "operator_local_path",
    "prompt",
    "response",
    "unsanitized_capture",
}
_GOVERNED_SUMMARY_MEMBERS = {"digest", "status"}
_REFUSAL_RECORD_MEMBERS = {"digest", "reasons"}
_REPLAY_FIXTURE_MEMBERS = {"case_set_id", "digest", "raw_capture"}
_SHA256_PREFIX = "sha256:"
_SHA256_HEX = "0123456789abcdef"


def _committed_replay_case_set_id(path: Path = FROZEN_REPLAY_CASES_PATH) -> str:
    try:
        fixture = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise controls.ControlContractError(
            f"cannot load committed replay fixture: {exc}"
        ) from exc
    if not isinstance(fixture, dict) or not isinstance(fixture.get("case_set_id"), str):
        raise controls.ControlContractError(
            "committed replay fixture case_set_id is malformed"
        )
    return fixture["case_set_id"]


def _assert_registry_authority(registry: dict[str, Any]) -> dict[str, Any]:
    observed = controls.validate_registry_authority(registry)
    committed = controls.load_registry_authority(FROZEN_REGISTRY_PATH)
    if observed != committed:
        raise controls.ControlContractError("injected registry is not the committed authority")
    return copy.deepcopy(committed)


def _assert_partition_authority(
    entries: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    committed = controls.load_partition_entries(FROZEN_PARTITION_ENTRIES_PATH)
    observed = (
        committed
        if entries is None
        else controls.validate_partition_entries(entries)
    )
    if observed != committed:
        raise controls.ControlContractError(
            "injected partition entries are not the committed authority"
        )
    return copy.deepcopy(committed)


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


def _control_of_kind(registry: dict[str, Any], control_kind: str) -> dict[str, Any]:
    if control_kind not in _CODEX_CONTROL_IDS_BY_KIND:
        raise controls.ControlContractError(f"unknown Codex control kind {control_kind!r}")
    matches = [
        control
        for control in registry.get("controls", [])
        if isinstance(control, dict) and control.get("control_kind") == control_kind
    ]
    if len(matches) != 1:
        raise controls.ControlContractError(
            f"registry must contain exactly one {control_kind!r} control"
        )
    control = matches[0]
    if control.get("control_id") != _CODEX_CONTROL_IDS_BY_KIND[control_kind]:
        raise controls.ControlContractError(f"{control_kind!r} control_id drift")
    return control


def _require_authentication(
    *, authentication_mode: Any, authorization: Any
) -> None:
    if authentication_mode != _AUTHENTICATION_MODE:
        raise controls.ControlContractError(
            "Codex control smokes require ChatGPT subscription authentication"
        )
    if authorization != _WITHHELD:
        raise controls.ControlContractError(
            "automated Codex smoke planning may only represent withheld authorization"
        )


def _bound_value(bounds: dict[str, Any], member: str) -> int:
    value = bounds.get(member)
    if not isinstance(value, dict) or isinstance(value.get("value"), bool):
        raise controls.ControlContractError(f"smoke bound {member!r} is malformed")
    quantity = value.get("value")
    if not isinstance(quantity, int):
        raise controls.ControlContractError(f"smoke bound {member!r} is not integer-valued")
    return quantity


def _registered_entries(entries: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return _assert_partition_authority(entries)


def guard_plan_objectives(
    objective_ids: Any, entries: list[dict[str, Any]] | None = None
) -> None:
    """Refuse any operator plan outside the G56R-004 smoke partition."""

    registered = _registered_entries(entries)
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
    registered = _registered_entries(entries)
    objectives = tuple(sorted(_smoke_partition(registered)["objective_ids"]))
    guard_plan_objectives(objectives, registered)
    return objectives


def build_plan(
    control_kind: str,
    *,
    registry: dict[str, Any],
    partition_entries: list[dict[str, Any]] | None = None,
    authentication_mode: str = _AUTHENTICATION_MODE,
    authorization: str = _WITHHELD,
) -> dict[str, Any]:
    """Plan exactly one non-live, operator-withheld Codex smoke."""

    _require_authentication(
        authentication_mode=authentication_mode, authorization=authorization
    )
    registry = _assert_registry_authority(registry)
    registered = _registered_entries(partition_entries)
    control = _control_of_kind(registry, control_kind)
    smoke = _smoke_partition(registered)
    objective_ids = [smoke["objective_ids"][0]]
    guard_plan_objectives(objective_ids, registered)
    return {
        "authentication_mode": _AUTHENTICATION_MODE,
        "authorization": _WITHHELD,
        "control_id": control["control_id"],
        "control_kind": control_kind,
        "objective_ids": objective_ids,
        "partition_id": smoke["partition_id"],
        "run_state": _UNRUN,
        "smoke_id": f"g56r-004-smoke-{control_kind}",
    }


def guard_smoke_record(
    record: Any, entries: list[dict[str, Any]] | None = None
) -> None:
    """Refuse reserved, scored, outcome-bearing, or non-calibration smoke rows."""

    if not isinstance(record, dict):
        raise controls.ControlContractError("a smoke record must be an object")
    registered = _registered_entries(entries)
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


def _unit_rows(record: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], int]:
    attempts = record.get("objective_attempts")
    if not isinstance(attempts, list) or not attempts:
        raise controls.ControlContractError("smoke record objective_attempts are missing")
    rows: list[dict[str, Any]] = []
    objectives: list[str] = []
    child_dispatches = 0
    for attempt_index, attempt in enumerate(attempts):
        if not isinstance(attempt, dict):
            raise controls.ControlContractError(
                f"objective_attempts[{attempt_index}] must be an object"
            )
        objective_id = attempt.get("objective_id")
        if not isinstance(objective_id, str) or not objective_id:
            raise controls.ControlContractError(
                f"objective_attempts[{attempt_index}].objective_id is missing"
            )
        attempt_rows = attempt.get("unit_rows")
        if not isinstance(attempt_rows, list) or not attempt_rows:
            raise controls.ControlContractError(
                f"objective_attempts[{attempt_index}].unit_rows are missing"
            )
        parents = [
            row
            for row in attempt_rows
            if isinstance(row, dict) and row.get("spawned_by") is None
        ]
        if len(parents) != 1:
            raise controls.ControlContractError(
                f"objective_attempts[{attempt_index}] must record exactly one parent row"
            )
        objectives.append(objective_id)
        child_dispatches += len(attempt_rows) - 1
        for row_index, row in enumerate(attempt_rows):
            if not isinstance(row, dict):
                raise controls.ControlContractError(
                    f"unit row {attempt_index}.{row_index} must be an object"
                )
            rows.append(row)
    return rows, objectives, child_dispatches


def _whole_number(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise controls.ControlContractError(f"{label} must be a non-negative integer")
    return value


def _sum_raw(rows: list[dict[str, Any]], member: str) -> int:
    total = 0
    for row in rows:
        raw = row.get("raw_token_vector")
        if not isinstance(raw, dict):
            raise controls.ControlContractError("unit row raw_token_vector is missing")
        total += _whole_number(raw.get(member), f"raw_token_vector.{member}")
    return total


def _sum_cache_read(rows: list[dict[str, Any]]) -> tuple[int, bool]:
    total = 0
    complete = True
    for row in rows:
        diagnostic = row.get("cache_diagnostic")
        if diagnostic is None:
            complete = False
            continue
        if not isinstance(diagnostic, dict):
            raise controls.ControlContractError("unit row cache_diagnostic is malformed")
        value = diagnostic.get("cache_read_tokens")
        if value is None:
            complete = False
            continue
        total += _whole_number(value, "cache_diagnostic.cache_read_tokens")
    return total, complete


def _sum_cache_write(
    rows: list[dict[str, Any]], write_bounds: dict[str, Any]
) -> tuple[dict[str, int], set[str]]:
    totals: dict[str, int] = {ttl_class: 0 for ttl_class in sorted(write_bounds)}
    incomplete: set[str] = set()
    for row in rows:
        diagnostic = row.get("cache_diagnostic")
        if diagnostic is None:
            incomplete.update(totals)
            continue
        if not isinstance(diagnostic, dict):
            raise controls.ControlContractError("unit row cache_diagnostic is malformed")
        write = diagnostic.get("cache_write_tokens_by_ttl_class")
        if write is None:
            incomplete.update(totals)
            continue
        if not isinstance(write, dict):
            raise controls.ControlContractError(
                "cache_diagnostic.cache_write_tokens_by_ttl_class is missing"
            )
        if set(write) != set(totals):
            if not set(write).issubset(set(totals)):
                raise controls.ControlContractError(
                    "cache_diagnostic.cache_write_tokens_by_ttl_class member-set drift"
                )
            for missing in set(totals) - set(write):
                incomplete.add(missing)
        for ttl_class in totals:
            value = write.get(ttl_class)
            if value is None:
                incomplete.add(ttl_class)
                continue
            totals[ttl_class] += _whole_number(
                value,
                f"cache_diagnostic.cache_write_tokens_by_ttl_class.{ttl_class}",
            )
    return totals, incomplete


def _cache_write_unobserved(incomplete_ttl_classes: set[str]) -> list[str]:
    return [
        f"max_cache_write_tokens_by_ttl_class.{ttl_class}"
        for ttl_class in sorted(incomplete_ttl_classes)
    ]


def _assert_cache_write_bounds(
    write_totals: dict[str, int], write_bounds: dict[str, Any]
) -> None:
    if set(write_totals) != set(write_bounds):
        raise controls.ControlContractError(
            "max_cache_write_tokens_by_ttl_class member-set drift"
        )
    for ttl_class, quantity in write_totals.items():
        if quantity is None:
            continue
        if quantity > _bound_value(write_bounds, ttl_class):
            raise controls.ControlContractError(
                f"max_cache_write_tokens_by_ttl_class.{ttl_class} exceeds its smoke ceiling"
            )


def _assert_attempt_objectives(
    *,
    record: dict[str, Any],
    consumed_objectives: list[str],
    registered: list[dict[str, Any]],
) -> None:
    reserved = controls.reserved_partition_entry(registered)
    attempt_rows = [
        {"row_id": f"attempt-{index}", "objective_id": objective}
        for index, objective in enumerate(consumed_objectives)
    ]
    controls.assert_reserved_partition_untouched(attempt_rows, reserved)
    smoke_objectives = set(_smoke_partition(registered)["objective_ids"])
    extra = set(consumed_objectives) - smoke_objectives
    if extra:
        raise controls.ControlContractError(
            f"objective_attempts consume objectives outside the smoke partition: {sorted(extra)}"
        )
    top_level = record.get("objective_ids")
    if not isinstance(top_level, list) or not all(
        isinstance(objective, str) for objective in top_level
    ):
        raise controls.ControlContractError("smoke record objective_ids are malformed")
    if sorted(set(top_level)) != sorted(set(consumed_objectives)):
        raise controls.ControlContractError(
            f"objective_ids records {sorted(top_level)}; objective_attempts consume "
            f"{sorted(set(consumed_objectives))}"
        )


def _consumed(
    record: dict[str, Any],
    rows: list[dict[str, Any]],
    consumed_objectives: list[str],
    bounds: dict[str, Any],
) -> dict[str, Any]:
    attempts = record["objective_attempts"]
    confirmation_entries = _whole_number(
        record.get("confirmation_entries"), "confirmation_entries"
    )
    elapsed = _whole_number(
        record.get("elapsed_wall_clock_seconds"), "elapsed_wall_clock_seconds"
    )
    candidate_repetition = max(
        consumed_objectives.count(objective) for objective in consumed_objectives
    )
    write_bounds = bounds.get("max_cache_write_tokens_by_ttl_class")
    if not isinstance(write_bounds, dict) or not write_bounds:
        raise controls.ControlContractError(
            "smoke bound max_cache_write_tokens_by_ttl_class is malformed"
        )
    cache_read_total, cache_read_complete = _sum_cache_read(rows)
    cache_write_totals, incomplete_cache_writes = _sum_cache_write(rows, write_bounds)
    consumed = {
        "max_attempts": len(attempts),
        "max_candidates": candidate_repetition,
        "max_cache_read_tokens": cache_read_total,
        "max_cache_write_tokens_by_ttl_class": cache_write_totals,
        "max_confirmation_entries": confirmation_entries,
        "max_duration_seconds": elapsed,
        "max_input_tokens": _sum_raw(rows, "input_tokens"),
        "max_output_tokens": _sum_raw(rows, "output_tokens"),
        "max_cached_input_tokens": _sum_raw(rows, "cached_input_tokens"),
    }
    consumed["raw_token_ceiling"] = sum(
        consumed[member]
        for member in ("max_input_tokens", "max_output_tokens", "max_cached_input_tokens")
    )
    for member, value in consumed.items():
        if member == "max_cache_write_tokens_by_ttl_class":
            _assert_cache_write_bounds(value, write_bounds)
            continue
        if value is not None and value > _bound_value(bounds, member):
            raise controls.ControlContractError(f"{member} exceeds its smoke ceiling")
    unobserved: list[str] = []
    if not cache_read_complete:
        unobserved.append("max_cache_read_tokens")
    unobserved.extend(_cache_write_unobserved(incomplete_cache_writes))
    return {"consumed": consumed, "bounds_unobserved": sorted(unobserved)}


def _route_model_effort(route_id: Any) -> tuple[str, str]:
    if not isinstance(route_id, str) or "__" not in route_id:
        raise controls.ControlContractError("route_id must bind model and effort")
    model, effort = route_id.rsplit("__", 1)
    if not model or not effort:
        raise controls.ControlContractError("route_id must bind non-empty model and effort")
    return model, effort


def _adaptive_route_observation(value: Any, label: str) -> str:
    if not isinstance(value, dict):
        raise controls.ControlContractError(f"{label} must be an object")
    route_id = value.get("route_id")
    model, effort = _route_model_effort(route_id)
    if value.get("served_model") != model or value.get("served_effort") != effort:
        raise controls.ControlContractError(f"{label} served model/effort drift")
    return str(route_id)


def _validate_adaptive_exact_treatment(
    control: dict[str, Any],
    produced_evidence: dict[str, Any],
    *,
    consumed_objectives: list[str],
    registered: list[dict[str, Any]],
) -> dict[str, Any]:
    adaptive = control.get("adaptive")
    if not isinstance(adaptive, dict):
        raise controls.ControlContractError("adaptive control is malformed")
    ladder = adaptive.get("escalation_ladder")
    if not isinstance(ladder, list) or len(ladder) < 2:
        raise controls.ControlContractError("adaptive ladder is malformed")

    signal = produced_evidence.get("qualifying_signal")
    if not isinstance(signal, dict):
        raise controls.ControlContractError("adaptive exact treatment requires a qualifying signal")
    signal_objective = signal.get("objective_id")
    if not isinstance(signal_objective, str) or signal_objective not in set(consumed_objectives):
        raise controls.ControlContractError(
            "adaptive qualifying signal objective is not a recorded objective_attempt"
        )
    reserved = controls.reserved_partition_entry(registered)
    controls.assert_reserved_partition_untouched(
        [{"row_id": "adaptive-qualifying-signal", "objective_id": signal_objective}],
        reserved,
    )
    response = controls.resolve_adaptive_response(control, copy.deepcopy(signal))
    if response != "escalate":
        raise controls.ControlContractError("adaptive exact treatment signal did not escalate")

    pre_route = _adaptive_route_observation(
        produced_evidence.get("pre_escalation"), "pre_escalation"
    )
    post_route = _adaptive_route_observation(
        produced_evidence.get("post_escalation"), "post_escalation"
    )
    state = {
        "objective_id": signal.get("objective_id", "g56r-004-smoke-objective"),
        "current_route_id": pre_route,
        "clean_streak": 0,
        "escalations_used": 0,
    }
    movement = controls.advance_adaptive_state(control, state, copy.deepcopy(signal))
    if (
        movement.get("escalated") is not True
        or movement.get("current_route_id") != post_route
        or movement.get("escalation_step")
        != {"from_route_id": pre_route, "to_route_id": post_route}
    ):
        raise controls.ControlContractError(
            "adaptive exact treatment did not move one frozen ladder step"
        )
    observed = copy.deepcopy(produced_evidence)
    observed["resolved_response"] = response
    observed["escalation_step"] = copy.deepcopy(movement["escalation_step"])
    return observed


def _validate_exact_treatment(
    control: dict[str, Any],
    produced_evidence: Any,
    rows: list[dict[str, Any]],
    *,
    consumed_objectives: list[str],
    registered: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(produced_evidence, dict):
        raise controls.ControlContractError("produced_evidence must be an object")
    if produced_evidence.get("read_back_from") != "produced_evidence":
        raise controls.ControlContractError("smoke exact treatment must read produced evidence")
    kind = control.get("control_kind")
    if kind == "unpinned":
        return controls.validate_unpinned_exact_treatment(
            control,
            {
                "read_back_from": "produced_evidence",
                "produced_evidence": copy.deepcopy(produced_evidence),
            },
        )
    if kind == "justified_high_effort":
        observed = controls.validate_justified_high_effort_exact_treatment(
            control,
            {
                "read_back_from": "produced_evidence",
                "produced_evidence": copy.deepcopy(produced_evidence),
            },
        )
        expected = controls.aggregate_parent_plus_children(control, rows)
        if observed.get("parent_plus_child_aggregate") != expected:
            raise controls.ControlContractError(
                "parent_plus_child_aggregate does not match recorded unit rows"
            )
        observed["parent_plus_child_aggregate"] = expected
        return observed
    if kind == "adaptive":
        return _validate_adaptive_exact_treatment(
            control,
            produced_evidence,
            consumed_objectives=consumed_objectives,
            registered=registered,
        )
    raise controls.ControlContractError(f"unknown control kind {kind!r}")


def _digest(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value.startswith(_SHA256_PREFIX)
        or len(value) != len(_SHA256_PREFIX) + 64
        or any(char not in _SHA256_HEX for char in value[len(_SHA256_PREFIX):])
    ):
        raise controls.ControlContractError(f"{label} must be a sha256 digest")
    return value


def _sanitized_digest(value: Any, label: str) -> str:
    return _digest(value, label)


def _reject_raw_members(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, member in value.items():
            member_path = f"{path}.{key}" if path else str(key)
            if key in _RAW_CAPTURE_MEMBERS:
                raise controls.ControlContractError(
                    f"{member_path} is raw live-model or operator-local capture"
                )
            if key.endswith("_path") or key == "path":
                raise controls.ControlContractError(
                    f"{member_path} records an operator-local path"
                )
            if key in {"arm_cache_root_digest", "paired_arm_cache_root_digest"}:
                _digest(member, member_path)
            _reject_raw_members(member, member_path)
    elif isinstance(value, list):
        for index, member in enumerate(value):
            _reject_raw_members(member, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if "/" in value or "\\" in value:
            raise controls.ControlContractError(
                f"{path} records an operator-local path-like string"
            )
        if "raw" in lowered:
            raise controls.ControlContractError(
                f"{path} records raw live-model or operator-local capture text"
            )


def _evaluate_cache_isolation(pairs: Any) -> dict[str, Any]:
    if not isinstance(pairs, list):
        raise controls.ControlContractError("observed_cache_isolation must be an array")
    observed: dict[frozenset[str], dict[str, Any]] = {}
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict):
            raise controls.ControlContractError(f"cache pair {index} must be an object")
        arms = pair.get("arm_pair")
        if not isinstance(arms, list) or len(arms) != 2 or arms != sorted(arms):
            raise controls.ControlContractError("cache pair must be an unordered sorted pair")
        key = frozenset(arms)
        if key not in _REQUIRED_CACHE_PAIRS:
            raise controls.ControlContractError("cache pair is outside the three smoke arms")
        if key in observed:
            raise controls.ControlContractError("cache pair is duplicated")
        status = pair.get("status")
        if status != "observed_disjoint" or pair.get("roots_disjoint") is not True:
            raise controls.ControlContractError("cache pair is not observed disjoint")
        _digest(pair.get("arm_cache_root_digest"), "arm_cache_root_digest")
        _digest(pair.get("paired_arm_cache_root_digest"), "paired_arm_cache_root_digest")
        observed[key] = copy.deepcopy(pair)
    if set(observed) != _REQUIRED_CACHE_PAIRS:
        raise controls.ControlContractError("all three unordered cache-isolation pairs are required")
    return {
        "all_pairs_disjoint": True,
        "pairs": [
            {"pair": sorted(pair), **observed[pair]}
            for pair in sorted(observed, key=lambda item: sorted(item))
        ],
    }


def seal_record(
    record: dict[str, Any],
    *,
    registry: dict[str, Any],
    partition_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Seal a non-live Codex smoke record without invoking any live model."""

    if not isinstance(record, dict):
        raise controls.ControlContractError("smoke record must be an object")
    registry = _assert_registry_authority(registry)
    registered = _registered_entries(partition_entries)
    _require_authentication(
        authentication_mode=record.get("authentication_mode"),
        authorization=record.get("authorization"),
    )
    if record.get("run_state") != _UNRUN:
        raise controls.ControlContractError("automated Codex smoke records must remain unrun")
    guard_smoke_record(record, registered)
    control_kind = record.get("control_kind")
    if not isinstance(control_kind, str):
        raise controls.ControlContractError("smoke record control_kind is missing")
    control = _control_of_kind(registry, control_kind)
    if record.get("control_id") != control.get("control_id"):
        raise controls.ControlContractError("smoke record control_id drift")

    rows, consumed_objectives, child_dispatches = _unit_rows(record)
    _assert_attempt_objectives(
        record=record,
        consumed_objectives=consumed_objectives,
        registered=registered,
    )
    consumption = _consumed(record, rows, consumed_objectives, registry["smoke_bounds"])
    exact_treatment = _validate_exact_treatment(
        control,
        record.get("produced_evidence"),
        rows,
        consumed_objectives=consumed_objectives,
        registered=registered,
    )
    cache_isolation = _evaluate_cache_isolation(record.get("observed_cache_isolation"))

    sealed = copy.deepcopy(record)
    sealed.update(
        {
            "cache_isolation": cache_isolation,
            "child_dispatch_count": child_dispatches,
            "bounds_unobserved": consumption["bounds_unobserved"],
            "consumed": consumption["consumed"],
            "counted_over": "parent_plus_children_unit",
            "evidence_admissibility": _UNRUN,
            "produced_evidence": exact_treatment,
            "raw_token_ceiling_members": list(_RAW_TOKEN_CEILING_MEMBERS),
            "refusal_reasons": [],
        }
    )
    return sealed


def sanitize_repository_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    """Admit only repository-safe governed smoke summaries."""

    if not isinstance(artifact, dict):
        raise controls.ControlContractError("repository artifact must be an object")
    _reject_raw_members(artifact, "")
    required = {
        "artifact_kind",
        "control_id",
        "evidence_admissibility",
        "governed_summary",
        "refusal_record",
        "replay_fixture",
        "run_state",
        "schema_version",
    }
    if set(artifact) != required:
        raise controls.ControlContractError("repository artifact member-set drift")
    if artifact.get("artifact_kind") != "codex_control_smoke_summary":
        raise controls.ControlContractError("unexpected repository artifact kind")
    if artifact.get("schema_version") != "1.0.0":
        raise controls.ControlContractError("repository artifact schema_version drift")
    if artifact.get("run_state") != _UNRUN or artifact.get("evidence_admissibility") != _UNRUN:
        raise controls.ControlContractError("repository artifact must preserve unrun status")
    if artifact.get("control_id") not in set(_CODEX_CONTROL_IDS_BY_KIND.values()):
        raise controls.ControlContractError("repository artifact control_id drift")

    governed = artifact.get("governed_summary")
    if not isinstance(governed, dict) or set(governed) != _GOVERNED_SUMMARY_MEMBERS:
        raise controls.ControlContractError("governed summary member-set drift")
    if governed.get("status") != "authorization_withheld":
        raise controls.ControlContractError("governed summary status drift")
    _sanitized_digest(governed.get("digest"), "governed_summary.digest")

    refusal = artifact.get("refusal_record")
    if not isinstance(refusal, dict) or set(refusal) != _REFUSAL_RECORD_MEMBERS:
        raise controls.ControlContractError("refusal record member-set drift")
    if refusal.get("reasons") != []:
        raise controls.ControlContractError("unrun smoke summaries must carry no refusal reasons")
    if not isinstance(refusal.get("reasons"), list):
        raise controls.ControlContractError("refusal record is malformed")
    _sanitized_digest(refusal.get("digest"), "refusal_record.digest")

    replay = artifact.get("replay_fixture")
    if not isinstance(replay, dict) or set(replay) != _REPLAY_FIXTURE_MEMBERS:
        raise controls.ControlContractError("replay fixture member-set drift")
    case_set_id = replay.get("case_set_id")
    if (
        not isinstance(case_set_id, str)
        or case_set_id != _committed_replay_case_set_id()
        or replay.get("raw_capture") is not False
    ):
        raise controls.ControlContractError("replay fixture summary is not non-raw")
    _sanitized_digest(replay.get("digest"), "replay_fixture.digest")
    return copy.deepcopy(artifact)


__all__ = (
    "FROZEN_PARTITION_ENTRIES_PATH",
    "build_plan",
    "guard_plan_objectives",
    "guard_smoke_record",
    "partition_entries",
    "plan_objectives",
    "sanitize_repository_artifact",
    "seal_record",
)
