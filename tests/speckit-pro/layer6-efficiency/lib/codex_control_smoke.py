"""Non-live partition guards for G56R-004 smoke planning and sealing."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import codex_policy_controls as controls


FROZEN_PARTITION_ENTRIES_PATH = (
    Path(__file__).resolve().parent.parent
    / "fixtures-codex-controls"
    / "partition-registry-entries.json"
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
    return entries if entries is not None else partition_entries()


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


def _unit_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    attempts = record.get("objective_attempts")
    if not isinstance(attempts, list) or not attempts:
        raise controls.ControlContractError("smoke record objective_attempts are missing")
    rows: list[dict[str, Any]] = []
    for attempt_index, attempt in enumerate(attempts):
        if not isinstance(attempt, dict):
            raise controls.ControlContractError(
                f"objective_attempts[{attempt_index}] must be an object"
            )
        attempt_rows = attempt.get("unit_rows")
        if not isinstance(attempt_rows, list) or not attempt_rows:
            raise controls.ControlContractError(
                f"objective_attempts[{attempt_index}].unit_rows are missing"
            )
        for row_index, row in enumerate(attempt_rows):
            if not isinstance(row, dict):
                raise controls.ControlContractError(
                    f"unit row {attempt_index}.{row_index} must be an object"
                )
            rows.append(row)
    return rows


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


def _child_dispatch_count(rows: list[dict[str, Any]]) -> int:
    return len(rows)


def _consumed(record: dict[str, Any], rows: list[dict[str, Any]], bounds: dict[str, Any]) -> dict[str, int]:
    attempts = record["objective_attempts"]
    confirmation_entries = _whole_number(
        record.get("confirmation_entries"), "confirmation_entries"
    )
    elapsed = _whole_number(
        record.get("elapsed_wall_clock_seconds"), "elapsed_wall_clock_seconds"
    )
    consumed = {
        "max_attempts": len(attempts),
        "max_candidates": 1,
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
        if value > _bound_value(bounds, member):
            raise controls.ControlContractError(f"{member} exceeds its smoke ceiling")
    return consumed


def _validate_exact_treatment(
    control: dict[str, Any], produced_evidence: Any
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
        return controls.validate_justified_high_effort_exact_treatment(
            control,
            {
                "read_back_from": "produced_evidence",
                "produced_evidence": copy.deepcopy(produced_evidence),
            },
        )
    if kind == "adaptive":
        adaptive = control.get("adaptive")
        if not isinstance(adaptive, dict):
            raise controls.ControlContractError("adaptive control is malformed")
        ladder = adaptive.get("escalation_ladder")
        if not isinstance(ladder, list) or len(ladder) < 2:
            raise controls.ControlContractError("adaptive ladder is malformed")
        pre = produced_evidence.get("pre_escalation")
        post = produced_evidence.get("post_escalation")
        if not isinstance(pre, dict) or not isinstance(post, dict):
            raise controls.ControlContractError("adaptive produced route evidence is missing")
        if pre.get("route_id") != ladder[0] or post.get("route_id") != ladder[1]:
            raise controls.ControlContractError("adaptive exact treatment route drift")
        return copy.deepcopy(produced_evidence)
    raise controls.ControlContractError(f"unknown control kind {kind!r}")


def _digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
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

    rows = _unit_rows(record)
    consumed = _consumed(record, rows, registry["smoke_bounds"])
    exact_treatment = _validate_exact_treatment(control, record.get("produced_evidence"))
    cache_isolation = _evaluate_cache_isolation(record.get("observed_cache_isolation"))

    sealed = copy.deepcopy(record)
    sealed.update(
        {
            "cache_isolation": cache_isolation,
            "child_dispatch_count": _child_dispatch_count(rows),
            "consumed": consumed,
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
    if not isinstance(governed, dict) or governed.get("status") != "authorization_withheld":
        raise controls.ControlContractError("governed summary status drift")
    _sanitized_digest(governed.get("digest"), "governed_summary.digest")

    refusal = artifact.get("refusal_record")
    if not isinstance(refusal, dict) or not isinstance(refusal.get("reasons"), list):
        raise controls.ControlContractError("refusal record is malformed")
    _sanitized_digest(refusal.get("digest"), "refusal_record.digest")

    replay = artifact.get("replay_fixture")
    if (
        not isinstance(replay, dict)
        or not isinstance(replay.get("case_set_id"), str)
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
