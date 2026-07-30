"""Codex-local policy-control validation for G56R-004.

The module starts with the registry-owned CAR-004 mirror subset. Later tasks
extend the same fail-closed surface with comparison, partition, replay, and
reconciliation behavior as those artifacts become available.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from claude_score_bundle import (
    SERVICE_REROUTE_DISPOSITION_REASON,
    SERVICE_REROUTE_FAILURE_CODE,
    failure_plane_for,
)
import codex_control_comparison as _codex_control_comparison


class ControlContractError(ValueError):
    """Raised when a Codex policy-control artifact drifts from its authority."""


_CAR_SCHEMA_ID = "https://racecraft.dev/schemas/car-004/policy-control-registry.schema.json"
_CAR_COMPARISON_SCHEMA_ID = (
    "https://racecraft.dev/schemas/car-004/control-comparison.schema.json"
)
_CODEX_SCHEMA_ID = "https://racecraft.dev/schemas/g56r-004/policy-control-registry.schema.json"
_CODEX_COMPARISON_SCHEMA_ID = (
    "https://racecraft.dev/schemas/g56r-004/control-comparison.schema.json"
)
_CAR_REGISTRY_ID = "car-004-policy-control-registry"
_CODEX_REGISTRY_ID = "g56r-004-policy-control-registry"
_CAR_COMPARISON_ID = "car-004-control-comparison"
_CODEX_COMPARISON_ID = "g56r-004-control-comparison"
_CONTROL_ID_MAP = {
    "g56r-004-unpinned-control": "car-004-unpinned-control",
    "g56r-004-adaptive-control": "car-004-adaptive-control",
    "g56r-004-justified-high-effort-control": "car-004-orchestration-changing-control",
}
_PARTITION_ID_MAP = {
    "G56R-004-SMOKE": "CAR-004-SMOKE",
    "G56R-011-RESERVED-COMPARISON": "CAR-011-RESERVED-COMPARISON",
}
_CODEX_ONLY_UNPINNED_FIELDS = {
    "authentication_mode",
    "environment_boundary",
    "required_absent_overrides",
}
_REQUIRED_ABSENT_OVERRIDES = (
    "api_key",
    "effort",
    "model",
    "provider",
    "service_tier",
)
_ABSENT_OVERRIDE_SET = set(_REQUIRED_ABSENT_OVERRIDES)
_ADMITTED_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
_EFFORT_RANK = {
    effort: index for index, effort in enumerate(("low", "medium", "high", "xhigh", "max"))
}
_AUTHENTICATION_MODE = "chatgpt_subscription"
# Deliberate code-owned freeze authority: changing these values is an explicit,
# reviewable re-freeze rather than a fixture editing its own validation source.
_CODEX_SUCCESSOR_FREEZE_ID = (
    "sha256:734672cea5a83e5b8f296ee604f7cb8d93e0a5296a3f864b873fe78bfe518f1e"
)
_CODEX_ROUTE_EVIDENCE_DIGEST = (
    "sha256:f01ff64ca3d17b40db8ca802dd6501e62d91c4c161d01a94879c156f90eb09e4"
)
_CODEX_JUSTIFIED_HIGH_EFFORT_ROUTE_ID = "g56r-003-route-phase-executor"
_CODEX_JUSTIFIED_HIGH_EFFORT_MODEL = "gpt-5.5"
_CODEX_JUSTIFIED_HIGH_EFFORT_EFFORT = "xhigh"
_CODEX_JUSTIFIED_ELIGIBILITY_PREDICATE_ID = (
    "required_core_workspace_write_phase_executor"
)
_CODEX_ONLY_JUSTIFIED_HIGH_EFFORT_FIELDS = {
    "dynamic_route_discovery",
    "effort",
    "eligibility_predicate",
    "eligibility_rationale",
    "fallback_route_id",
    "model",
    "route_evidence_digest",
    "route_id",
    "successor_freeze_digest",
}
_CAR_SYNTHETIC_SUCCESSOR_FREEZE_ID = (
    "sha256:efccacf2bb277b2d87bf04f14bb542d941049d9456c94d55999ce8a311b4f392"
)
_CODEX_TO_CAR_ROUTE_ID = {
    "gpt-5.5__medium": "model-alpha__medium",
    "gpt-5.5__high": "model-alpha__high",
    "gpt-5.6-terra__high": "model-beta__high",
}
_SANCTIONED_DIVERGENCE = {
    "category": 3,
    "car_value": "orchestration_changing",
    "codex_value": "justified_high_effort",
    "unchanged_values": ["adaptive", "unpinned"],
}
_CODEX_CONTROL_IDS_BY_KIND = {
    "unpinned": "g56r-004-unpinned-control",
    "adaptive": "g56r-004-adaptive-control",
    "justified_high_effort": "g56r-004-justified-high-effort-control",
}
_CODEX_CONTROL_KINDS = tuple(_CODEX_CONTROL_IDS_BY_KIND)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ControlContractError(f"cannot load {path}: {exc}") from exc


_LAYER6_ROOT = Path(__file__).resolve().parent.parent
_CAR_REGISTRY_SCHEMA_PATH = (
    _LAYER6_ROOT / "contracts-claude" / "policy-control-registry.schema.json"
)
_CAR_REGISTRY_PATH = (
    _LAYER6_ROOT / "fixtures-controls" / "policy-control-registry.json"
)
_FROZEN_CODEX_REGISTRY_SCHEMA_PATH = (
    _LAYER6_ROOT
    / "contracts-codex-specification"
    / "policy-control-registry.schema.json"
)
_FROZEN_CODEX_REGISTRY_PATH = (
    _LAYER6_ROOT / "fixtures-codex-controls" / "policy-control-registry.json"
)
_FROZEN_CODEX_PARTITION_ENTRIES_PATH = (
    _LAYER6_ROOT / "fixtures-codex-controls" / "partition-registry-entries.json"
)
_FROZEN_CODEX_REPLAY_CASES_PATH = (
    _LAYER6_ROOT / "fixtures-codex-controls" / "replay-cases.json"
)
_FROZEN_CAR_HANDOFF_PATH = (
    _LAYER6_ROOT.parents[2]
    / "docs"
    / "ai"
    / "specs"
    / ".process"
    / "CAR-004-twin-handoff.md"
)
_SCORE_BUNDLE_SCHEMA = _load_json(
    _LAYER6_ROOT / "contracts-codex-specification" / "score-bundle.schema.json"
)
_FROZEN_TERMINAL_STATES = tuple(
    _SCORE_BUNDLE_SCHEMA["properties"]["resource_vector"]["properties"]["terminal_state"]["enum"]
)
_FROZEN_PARETO_DIMENSIONS = tuple(
    _SCORE_BUNDLE_SCHEMA["properties"]["resource_vector"]["required"]
)
_FROZEN_FAILURE_PLANES = tuple(_SCORE_BUNDLE_SCHEMA["properties"]["failure_plane"]["enum"])
_FROZEN_FAILURE_CODES = tuple(_SCORE_BUNDLE_SCHEMA["properties"]["failure_code"]["enum"])
_TREATMENT_RECORD_SCHEMA = _load_json(
    _LAYER6_ROOT / "contracts" / "treatment-record.schema.json"
)
_FROZEN_RAW_TOKEN_MEMBERS = tuple(
    _TREATMENT_RECORD_SCHEMA["$defs"]["rawTokenVector"]["required"]
)
_UNBOUNDED_RAW_TOKEN_MEMBER = "reasoning_output_tokens"
_RAW_TOKEN_CEILING_QUANTITY_MEMBERS = tuple(
    member for member in _FROZEN_RAW_TOKEN_MEMBERS if member != _UNBOUNDED_RAW_TOKEN_MEMBER
)
_ADDITIVE_RECORDS_SCHEMA = _load_json(
    _LAYER6_ROOT / "contracts-claude" / "car-003-additive-records.schema.json"
)
_CACHE_DIAGNOSTIC_SCHEMA = _ADDITIVE_RECORDS_SCHEMA["$defs"]["cacheDiagnosticRecord"]
_FROZEN_CACHE_TTL_CLASSES = tuple(
    _CACHE_DIAGNOSTIC_SCHEMA["properties"]["cache_write_tokens_by_ttl_class"][
        "propertyNames"
    ]["enum"]
)
_CACHE_QUANTITY_CEILINGS = {
    "cache_write_tokens_by_ttl_class": "max_cache_write_tokens_by_ttl_class",
    "cache_read_tokens": "max_cache_read_tokens",
}
_RAW_TOKEN_MEMBER_CEILINGS = {
    "input_tokens": "max_input_tokens",
    "output_tokens": "max_output_tokens",
    "cached_input_tokens": "max_cached_input_tokens",
    _UNBOUNDED_RAW_TOKEN_MEMBER: None,
}
_POLICY_RESPONSES = ("escalate", "hold", "non_scorable")
_SIGNAL_SOURCES = (
    "failure_code",
    "failure_plane",
    "retry_count",
    "budget_threshold",
    "terminal_state",
)
_EXECUTION_OBSERVED_SIGNALS = ("failure_code", "failure_plane", "retries", "terminal_state")
_BUDGET_SIGNAL_MEMBERS = {"max_duration_seconds", "raw_token_ceiling"}
_NONE_SENTINEL = "none"
_CLEAN_TERMINAL_STATE = "completed"
_ALWAYS_VALUED_SOURCE = "terminal_state"
_SIGNAL_MAP_ENUMS = (
    ("terminal_state_response", _FROZEN_TERMINAL_STATES),
    ("failure_plane_response", _FROZEN_FAILURE_PLANES),
    ("failure_code_response", _FROZEN_FAILURE_CODES),
)
_ADDITIVE_RULE = "sum"
_SEVERITY_FOLD_RULE = "worst_wins_by_severity"
_PARENT_ORACLE_RULE = "parent_objective_oracle"


def _record_digest(record: dict[str, Any], digest_field: str) -> str:
    preimage = copy.deepcopy(record)
    preimage.pop(digest_field, None)
    encoded = json.dumps(
        preimage,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _normalize_platform_value(value: Any, *, drop_jhe_fields: bool = False) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, member in value.items():
            if key in _CODEX_ONLY_UNPINNED_FIELDS:
                continue
            if drop_jhe_fields and key in _CODEX_ONLY_JUSTIFIED_HIGH_EFFORT_FIELDS:
                continue
            normalized_key = (
                "orchestration_changing" if key == "justified_high_effort" else key
            )
            if (
                key in {"registry_digest", "control_digest"}
                and isinstance(member, str)
                and member.startswith("sha256:")
            ):
                normalized[normalized_key] = "<content-address>"
            else:
                normalized[normalized_key] = _normalize_platform_value(
                    member,
                    drop_jhe_fields=drop_jhe_fields or key == "justified_high_effort",
                )
        return normalized
    if isinstance(value, list):
        return [
            _normalize_platform_value(member, drop_jhe_fields=drop_jhe_fields)
            for member in value
        ]
    if value == _CODEX_SCHEMA_ID:
        return _CAR_SCHEMA_ID
    if value == _CODEX_COMPARISON_SCHEMA_ID:
        return _CAR_COMPARISON_SCHEMA_ID
    if value == "G56R-004 Policy Control Registry":
        return "CAR-004 Policy Control Registry"
    if value == _CODEX_REGISTRY_ID:
        return _CAR_REGISTRY_ID
    if value == _CODEX_COMPARISON_ID:
        return _CAR_COMPARISON_ID
    if value in _CONTROL_ID_MAP:
        return _CONTROL_ID_MAP[value]
    if value in _PARTITION_ID_MAP:
        return _PARTITION_ID_MAP[value]
    if value == _CODEX_SUCCESSOR_FREEZE_ID:
        return _CAR_SYNTHETIC_SUCCESSOR_FREEZE_ID
    if value in _CODEX_TO_CAR_ROUTE_ID:
        return _CODEX_TO_CAR_ROUTE_ID[value]
    if value == "justified_high_effort":
        return "orchestration_changing"
    return value


def _assert_content_addresses(registry: dict[str, Any]) -> None:
    controls = registry.get("controls")
    if not isinstance(controls, list) or len(controls) != 3:
        raise ControlContractError("the Codex registry must carry exactly three controls")
    kinds = [control.get("control_kind") for control in controls]
    if len(set(kinds)) != len(kinds):
        raise ControlContractError("the Codex registry repeats a control_kind")
    expected_kinds = {"unpinned", "adaptive", "justified_high_effort"}
    if set(kinds) != expected_kinds:
        raise ControlContractError(
            f"unexpected Codex control_kind set: {sorted(str(kind) for kind in kinds)}"
        )
    for control in controls:
        expected = _record_digest(control, "control_digest")
        if control.get("control_digest") != expected:
            raise ControlContractError(
                f"control digest drift for {control.get('control_id')}"
            )
    expected_registry = _record_digest(registry, "registry_digest")
    if registry.get("registry_digest") != expected_registry:
        raise ControlContractError("registry digest drift")


def validate_registry_authority(registry: Any) -> dict[str, Any]:
    """Validate registry content addresses and return an isolated copy."""

    if not isinstance(registry, dict):
        raise ControlContractError("the Codex registry must be an object")
    _assert_content_addresses(registry)
    return copy.deepcopy(registry)


def load_registry_authority(path: Path) -> dict[str, Any]:
    """Load a Codex registry and validate its content-addressed authority."""

    return validate_registry_authority(_load_json(path))


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ControlContractError(f"{label} must be an object")
    return value


def _require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ControlContractError(f"{label} must be a non-empty string")
    return value


def _require_sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ControlContractError(f"{label} must be an array")
    return value


def _require_digest(value: Any, label: str) -> str:
    digest = _require_nonempty_string(value, label)
    if not digest.startswith("sha256:") or len(digest) != len("sha256:") + 64:
        raise ControlContractError(f"{label} must be a sha256 digest")
    return digest


def _adaptive(control: dict[str, Any]) -> dict[str, Any]:
    if control.get("control_kind") != "adaptive":
        raise ControlContractError("expected an adaptive control")
    return _require_mapping(control.get("adaptive"), "adaptive")


def _require_set_equal(mapping: Any, enum: tuple[str, ...], member: str) -> dict[str, str]:
    if not isinstance(mapping, dict):
        raise ControlContractError(f"{member} must be an object")
    unmapped = sorted(set(enum) - set(mapping))
    orphaned = sorted(set(mapping) - set(enum))
    if unmapped or orphaned:
        raise ControlContractError(
            f"{member} must match its frozen domain: unmapped {unmapped}, orphaned {orphaned}"
        )
    for signal, response in mapping.items():
        if not isinstance(response, str) or response not in _POLICY_RESPONSES:
            raise ControlContractError(
                f"{member}[{signal!r}] resolves outside the closed response set"
            )
    return mapping


def _candidate_code_for(terminal_state: str) -> str:
    candidate_code = f"candidate_{terminal_state}"
    if candidate_code not in _FROZEN_FAILURE_CODES:
        raise ControlContractError(
            f"{terminal_state!r} has no paired candidate failure code"
        )
    return candidate_code


def _threshold_met(entry: dict[str, Any], observed: Any) -> bool:
    if observed is None:
        return False
    if isinstance(observed, bool) or not isinstance(observed, (int, float)):
        raise ControlContractError("budget or retry observations must be numeric")
    direction = entry.get("direction")
    if direction == "at_or_above":
        return observed >= entry["threshold"]
    if direction == "at_or_below":
        return observed <= entry["threshold"]
    raise ControlContractError(f"{direction!r} is not a declared comparison direction")


def validate_adaptive_signal_maps(control: dict[str, Any]) -> None:
    """Validate total Codex adaptive signal maps and consistency guards."""

    adaptive = _adaptive(control)
    maps = {
        member: _require_set_equal(adaptive.get(member), enum, member)
        for member, enum in _SIGNAL_MAP_ENUMS
    }

    execution_contract = _require_mapping(
        control.get("execution_contract"), "execution_contract"
    )
    observed = execution_contract.get("observed_signals")
    if not isinstance(observed, list) or sorted(observed) != sorted(_EXECUTION_OBSERVED_SIGNALS):
        raise ControlContractError("adaptive observed_signals is not the closed frozen set")

    precedence = adaptive.get("signal_precedence")
    if not isinstance(precedence, list) or tuple(precedence) != _SIGNAL_SOURCES:
        raise ControlContractError("adaptive signal_precedence does not match the frozen order")
    if precedence[-1] != _ALWAYS_VALUED_SOURCE:
        raise ControlContractError("terminal_state is always valued and must rank last")

    retry_response = _require_mapping(
        adaptive.get("retry_count_response"), "retry_count_response"
    )
    if retry_response.get("response") not in _POLICY_RESPONSES:
        raise ControlContractError("retry_count_response resolves outside the closed set")
    threshold = retry_response.get("threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise ControlContractError("retry_count_response.threshold must be numeric")
    _threshold_met(retry_response, threshold)

    triggers = adaptive.get("budget_triggers")
    if not isinstance(triggers, list) or not triggers:
        raise ControlContractError("budget_threshold has no declared triggers")
    trigger_members: set[str] = set()
    for index, trigger in enumerate(triggers):
        trigger_map = _require_mapping(trigger, f"budget_triggers[{index}]")
        member = _require_nonempty_string(
            trigger_map.get("member"), f"budget_triggers[{index}].member"
        )
        if member not in _BUDGET_SIGNAL_MEMBERS:
            raise ControlContractError(f"{member!r} is not a frozen budget signal")
        if member in trigger_members:
            raise ControlContractError(f"budget trigger {member!r} is duplicated")
        trigger_members.add(member)
        if trigger_map.get("response") not in _POLICY_RESPONSES:
            raise ControlContractError("budget trigger resolves outside the closed set")
        trigger_threshold = trigger_map.get("threshold")
        if isinstance(trigger_threshold, bool) or not isinstance(
            trigger_threshold, (int, float)
        ):
            raise ControlContractError("budget trigger threshold must be numeric")
        _threshold_met(trigger_map, trigger_threshold)

    code_map = maps["failure_code_response"]
    plane_map = maps["failure_plane_response"]
    terminal_map = maps["terminal_state_response"]
    for code, response in code_map.items():
        plane = failure_plane_for(code)
        if plane not in plane_map:
            raise ControlContractError(f"failure code {code!r} derives unknown plane {plane!r}")
        if plane_map[plane] != response:
            raise ControlContractError("failure-plane and failure-code responses disagree")
    for state, response in terminal_map.items():
        if state == _CLEAN_TERMINAL_STATE:
            continue
        paired = _candidate_code_for(state)
        if code_map[paired] != response:
            raise ControlContractError("terminal-state and candidate-code responses disagree")
    return None


def resolve_adaptive_response(control: dict[str, Any], row: dict[str, Any]) -> str:
    """Resolve one Codex adaptive row by the frozen signal precedence."""

    validate_adaptive_signal_maps(control)
    adaptive = _adaptive(control)
    enum_sources = {
        "failure_code": ("failure_code_response", row.get("failure_code", _NONE_SENTINEL)),
        "failure_plane": ("failure_plane_response", row.get("failure_plane", _NONE_SENTINEL)),
        "terminal_state": ("terminal_state_response", row.get("terminal_state")),
    }
    for source in adaptive["signal_precedence"]:
        if source in enum_sources:
            member, value = enum_sources[source]
            mapping = adaptive[member]
            if value not in mapping:
                raise ControlContractError(f"row {source} is outside the frozen domain")
            if source == _ALWAYS_VALUED_SOURCE or value != _NONE_SENTINEL:
                return mapping[value]
            continue
        if source == "retry_count":
            if _threshold_met(adaptive["retry_count_response"], row.get("retries", 0)):
                return adaptive["retry_count_response"]["response"]
            continue
        if source == "budget_threshold":
            observations = row.get("budget_observations", {})
            if not isinstance(observations, dict):
                raise ControlContractError("budget_observations must be an object")
            declared = {trigger["member"] for trigger in adaptive["budget_triggers"]}
            unknown = sorted(set(observations) - declared)
            if unknown:
                raise ControlContractError(f"unknown budget observation members: {unknown}")
            for trigger in adaptive["budget_triggers"]:
                if _threshold_met(trigger, observations.get(trigger["member"])):
                    return trigger["response"]
            continue
        raise ControlContractError(f"{source!r} is not a member of the closed source set")
    raise ControlContractError("no adaptive signal resolved the row")


def _adaptive_ladder(control: dict[str, Any]) -> list[Any]:
    ladder = _adaptive(control).get("escalation_ladder")
    if not isinstance(ladder, list) or not ladder:
        raise ControlContractError("adaptive escalation_ladder must not be empty")
    return ladder


def _adaptive_ladder_position(control: dict[str, Any], route_id: Any) -> int:
    if not isinstance(route_id, str) or not route_id:
        raise ControlContractError("current_route_id must be a non-empty string")
    ladder = _adaptive_ladder(control)
    if route_id not in ladder:
        raise ControlContractError(f"{route_id!r} is not on the frozen adaptive ladder")
    return ladder.index(route_id)


def _next_adaptive_route(control: dict[str, Any], current_route_id: str) -> str | None:
    ladder = _adaptive_ladder(control)
    position = _adaptive_ladder_position(control, current_route_id)
    if position + 1 >= len(ladder):
        return None
    return ladder[position + 1]


def _previous_adaptive_route(control: dict[str, Any], current_route_id: str) -> str | None:
    ladder = _adaptive_ladder(control)
    position = _adaptive_ladder_position(control, current_route_id)
    if position == 0:
        return None
    return ladder[position - 1]


def _budget_trigger_reading(
    control: dict[str, Any], observations: Any
) -> tuple[bool, str | None]:
    adaptive = _adaptive(control)
    if not isinstance(observations, dict):
        raise ControlContractError("budget_observations must be an object")
    declared = {trigger["member"] for trigger in adaptive["budget_triggers"]}
    unknown = sorted(set(observations) - declared)
    if unknown:
        raise ControlContractError(f"unknown budget observation members: {unknown}")
    for trigger in adaptive["budget_triggers"]:
        if _threshold_met(trigger, observations.get(trigger["member"])):
            return True, trigger["response"]
    return False, None


def _is_adaptive_clean_pass(control: dict[str, Any], row: dict[str, Any]) -> bool:
    adaptive = _adaptive(control)
    declared = _require_mapping(
        adaptive.get("clean_pass_definition"), "clean_pass_definition"
    )
    if row.get("escalated"):
        return False
    if row.get("terminal_state") != declared.get("terminal_state"):
        return False
    if row.get("failure_code", _NONE_SENTINEL) != declared.get("failure_code"):
        return False
    retries = row.get("retries", 0)
    if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
        raise ControlContractError("retries must be a non-negative integer")
    if retries > declared.get("max_retries"):
        return False
    budget_trigger_met, _ = _budget_trigger_reading(control, row.get("budget_observations", {}))
    return not budget_trigger_met


def _whole_number(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ControlContractError(f"{label} must be a non-negative integer")
    return value


def advance_adaptive_state(
    control: dict[str, Any], state: dict[str, Any], row: dict[str, Any]
) -> dict[str, Any]:
    """Advance Codex adaptive ladder and clean-pass state across one objective row."""

    adaptive = _adaptive(control)
    route = state.get("current_route_id")
    _adaptive_ladder_position(control, route)
    objective_id = row.get("objective_id", state.get("objective_id"))
    escalations_used = _whole_number(state.get("escalations_used", 0), "escalations_used")
    if state.get("objective_id") != objective_id:
        escalations_used = 0
    clean_streak = _whole_number(state.get("clean_streak", 0), "clean_streak")
    response = resolve_adaptive_response(control, row)

    outcome: dict[str, Any] = {
        "objective_id": objective_id,
        "current_route_id": route,
        "clean_streak": clean_streak,
        "escalations_used": escalations_used,
        "response": response,
        "clean_pass": False,
        "excluded": False,
        "escalated": False,
        "escalation_step": None,
        "de_escalation_evaluated": False,
        "de_escalated": False,
    }

    if response == "non_scorable":
        outcome["excluded"] = True
        return outcome

    if response == "escalate":
        outcome["clean_streak"] = 0
        max_escalations = adaptive.get("max_escalations_per_objective")
        if isinstance(max_escalations, bool) or not isinstance(max_escalations, int):
            raise ControlContractError("max_escalations_per_objective must be an integer")
        target = _next_adaptive_route(control, str(route))
        if escalations_used < max_escalations and target is not None:
            outcome["current_route_id"] = target
            outcome["escalated"] = True
            outcome["escalations_used"] = escalations_used + 1
            outcome["escalation_step"] = {
                "from_route_id": route,
                "to_route_id": target,
            }
        return outcome

    clean = _is_adaptive_clean_pass(control, row)
    outcome["clean_pass"] = clean
    clean_streak = clean_streak + 1 if clean else 0
    threshold = adaptive.get("de_escalation_clean_pass_threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold < 1:
        raise ControlContractError("de_escalation_clean_pass_threshold must be a positive integer")
    if clean_streak >= threshold:
        outcome["de_escalation_evaluated"] = True
        target = _previous_adaptive_route(control, str(route))
        if target is not None:
            outcome["current_route_id"] = target
            outcome["de_escalated"] = True
        clean_streak = 0
    outcome["clean_streak"] = clean_streak
    return outcome


def _bound_declaration(control: dict[str, Any], member: str) -> dict[str, Any]:
    contract = _require_mapping(control.get("execution_contract"), "execution_contract")
    return _require_mapping(contract.get(member), member)


def evaluate_adaptive_bounds(
    control: dict[str, Any], objective: dict[str, Any]
) -> dict[str, Any]:
    """Read Codex adaptive retry/cancellation breaches and budget triggers."""

    _adaptive(control)
    retry_bounds = _bound_declaration(control, "retry_bounds")
    cancellation_bounds = _bound_declaration(control, "cancellation_bounds")
    declared_scope = _require_nonempty_string(
        retry_bounds.get("counted_over"), "retry_bounds.counted_over"
    )
    if cancellation_bounds.get("counted_over") != declared_scope:
        raise ControlContractError("retry and cancellation bounds must share one scope")
    if objective.get("counted_over") != declared_scope:
        raise ControlContractError("objective counted_over disagrees with the control bounds")

    attempts = objective.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        raise ControlContractError("objective attempts must be a non-empty array")
    retries = 0
    duration_ms = 0
    for index, attempt in enumerate(attempts):
        entry = _require_mapping(attempt, f"attempts[{index}]")
        if entry.get("counter_reset_on_escalation"):
            raise ControlContractError("escalation must not reset retry or cancellation bounds")
        retries += _whole_number(entry.get("retries"), f"attempts[{index}].retries")
        duration_ms += _whole_number(entry.get("duration_ms"), f"attempts[{index}].duration_ms")

    budget_trigger_met, budget_response = _budget_trigger_reading(
        control, objective.get("budget_observations", {})
    )
    reading: dict[str, Any] = {
        "counted_over": declared_scope,
        "retries": retries,
        "duration_ms": duration_ms,
        "retry_bound_breached": retries > retry_bounds["max_retries"],
        "cancellation_bound_breached": duration_ms > cancellation_bounds["max_duration_ms"],
        "budget_trigger_met": budget_trigger_met,
        "budget_response": budget_response,
        "terminal_state": None,
        "failure_code": None,
    }

    breach = None
    if reading["cancellation_bound_breached"]:
        breach = cancellation_bounds["on_breach"]
    elif reading["retry_bound_breached"]:
        breach = retry_bounds["on_breach"]
    if breach is not None:
        terminal_state = breach["terminal_state"]
        failure_code = breach["failure_code"]
        if _candidate_code_for(terminal_state) != failure_code:
            raise ControlContractError("bound breach outcome is not the frozen candidate pairing")
        reading["terminal_state"] = terminal_state
        reading["failure_code"] = failure_code

    recorded = objective.get("recorded_outcome")
    if recorded is not None:
        expected = {
            "terminal_state": reading["terminal_state"],
            "failure_code": reading["failure_code"],
        }
        if recorded != expected:
            raise ControlContractError("recorded breach outcome disagrees with declared pairing")
    return reading


def classify_adaptive_service_reroute(
    control: dict[str, Any], state: dict[str, Any], row: dict[str, Any]
) -> dict[str, Any]:
    """Classify a Codex platform reroute without spending movement or streak state."""

    route = state.get("current_route_id")
    _adaptive_ladder_position(control, route)
    is_reroute = row.get("failure_code") == SERVICE_REROUTE_FAILURE_CODE
    classified: dict[str, Any] = {
        "service_reroute": is_reroute,
        "response": None,
        "current_route_id": route,
        "clean_streak": state.get("clean_streak", 0),
        "escalation_allowance_spent": False,
        "ladder_position_changed": False,
        "unit_non_scorable": is_reroute,
        "failure_plane": None,
        "disposition_reason": None,
    }
    if not is_reroute:
        return classified

    plane = failure_plane_for(SERVICE_REROUTE_FAILURE_CODE)
    if row.get("failure_plane") not in (None, plane):
        raise ControlContractError("service_reroute row records the wrong failure plane")
    response = resolve_adaptive_response(control, row)
    if response != "non_scorable":
        raise ControlContractError("service_reroute must resolve to non_scorable")
    classified.update(
        response=response,
        failure_plane=plane,
        disposition_reason=SERVICE_REROUTE_DISPOSITION_REASON,
    )
    return classified


def validate_adaptive_ladder(
    control: dict[str, Any], successor_freeze: dict[str, Any]
) -> None:
    """Validate the Codex adaptive ladder against its frozen G56R-003 tuples."""

    if control.get("control_kind") != "adaptive":
        raise ControlContractError("validate_adaptive_ladder received a non-adaptive control")
    if control.get("control_digest") != _record_digest(control, "control_digest"):
        raise ControlContractError("adaptive control digest drift")

    adaptive = _require_mapping(control.get("adaptive"), "adaptive")
    freeze = _require_mapping(successor_freeze, "successor_freeze")
    if adaptive.get("candidate_freeze_id") != _CODEX_SUCCESSOR_FREEZE_ID:
        raise ControlContractError("adaptive control is not bound to the frozen G56R-003 successor")
    if freeze.get("candidate_freeze_id") != adaptive.get("candidate_freeze_id"):
        raise ControlContractError("successor freeze ID drift")
    if freeze.get("freeze_digest") != adaptive.get("freeze_digest"):
        raise ControlContractError("successor freeze digest drift")

    ladder = _require_sequence(adaptive.get("escalation_ladder"), "adaptive.escalation_ladder")
    if not ladder:
        raise ControlContractError("adaptive escalation_ladder must not be empty")
    if len(ladder) != len(set(ladder)):
        raise ControlContractError("adaptive escalation_ladder repeats a route")
    for index, route_id in enumerate(ladder):
        _require_nonempty_string(route_id, f"adaptive.escalation_ladder[{index}]")

    admitted = _require_sequence(freeze.get("admitted_tuples"), "successor_freeze.admitted_tuples")
    if not admitted:
        raise ControlContractError("successor freeze must declare admitted tuples")

    ordered_routes: list[str] = []
    route_metadata: dict[str, tuple[str, str]] = {}
    for index, raw_tuple in enumerate(admitted):
        tuple_record = _require_mapping(
            raw_tuple, f"successor_freeze.admitted_tuples[{index}]"
        )
        if tuple_record.get("source_spec_id") != "G56R-003":
            raise ControlContractError("adaptive ladder admits a non-G56R-003 tuple")
        route_id = _require_nonempty_string(
            tuple_record.get("candidate_route_id"),
            f"successor_freeze.admitted_tuples[{index}].candidate_route_id",
        )
        if route_id in route_metadata:
            raise ControlContractError("successor freeze repeats an admitted route")
        model = _require_nonempty_string(
            tuple_record.get("model"), f"successor_freeze.admitted_tuples[{index}].model"
        )
        effort = _require_nonempty_string(
            tuple_record.get("effort"), f"successor_freeze.admitted_tuples[{index}].effort"
        )
        if effort not in _EFFORT_RANK:
            raise ControlContractError("successor freeze tuple effort is outside the Codex ladder")
        source_digest = _require_digest(
            tuple_record.get("source_evidence_digest"),
            f"successor_freeze.admitted_tuples[{index}].source_evidence_digest",
        )
        runtime_digest = _require_digest(
            tuple_record.get("runtime_evidence_digest"),
            f"successor_freeze.admitted_tuples[{index}].runtime_evidence_digest",
        )
        if runtime_digest != source_digest:
            raise ControlContractError("successor freeze route evidence digest drift")
        ordered_routes.append(route_id)
        route_metadata[route_id] = (model, effort)

    if ladder != ordered_routes:
        raise ControlContractError("adaptive escalation_ladder does not match admitted route order")

    raw_rationales = _require_sequence(
        adaptive.get("escalation_ladder_rationales"),
        "adaptive.escalation_ladder_rationales",
    )
    rationale_pairs: dict[tuple[str, str], str] = {}
    for index, raw_rationale in enumerate(raw_rationales):
        rationale = _require_mapping(
            raw_rationale, f"adaptive.escalation_ladder_rationales[{index}]"
        )
        from_route = _require_nonempty_string(
            rationale.get("from_route"),
            f"adaptive.escalation_ladder_rationales[{index}].from_route",
        )
        to_route = _require_nonempty_string(
            rationale.get("to_route"),
            f"adaptive.escalation_ladder_rationales[{index}].to_route",
        )
        text = _require_nonempty_string(
            rationale.get("rationale"),
            f"adaptive.escalation_ladder_rationales[{index}].rationale",
        )
        pair = (from_route, to_route)
        if pair in rationale_pairs:
            raise ControlContractError("adaptive escalation_ladder_rationales repeats a step")
        rationale_pairs[pair] = text

    cross_model_pairs: set[tuple[str, str]] = set()
    for current_route, next_route in zip(ladder, ladder[1:]):
        current_model, current_effort = route_metadata[current_route]
        next_model, next_effort = route_metadata[next_route]
        if current_model == next_model:
            if _EFFORT_RANK[current_effort] >= _EFFORT_RANK[next_effort]:
                raise ControlContractError("adaptive ladder contradicts Codex effort order")
            continue
        cross_model_pairs.add((current_route, next_route))

    if set(rationale_pairs) != cross_model_pairs:
        raise ControlContractError("adaptive cross-model rationales do not match ladder steps")
    return None


def validate_unpinned_control(control: dict[str, Any]) -> None:
    """Validate the Codex unpinned control's inherited parent identity."""

    if control.get("control_kind") != "unpinned":
        raise ControlContractError("validate_unpinned_control received a non-unpinned control")
    if control.get("control_digest") != _record_digest(control, "control_digest"):
        raise ControlContractError("unpinned control digest drift")

    unpinned = _require_mapping(control.get("unpinned"), "unpinned")
    if unpinned.get("arm_count") != 1:
        raise ControlContractError("the unpinned control must carry exactly one arm")
    if unpinned.get("model_resolution") != "inherit":
        raise ControlContractError("the unpinned control must inherit the parent model")

    dispatch = _require_mapping(
        _require_mapping(control.get("execution_contract"), "execution_contract").get(
            "dispatch_parameters"
        ),
        "dispatch_parameters",
    )
    if dispatch != {"model_resolution": "inherit"}:
        raise ControlContractError("the unpinned dispatch contract must not set local overrides")

    _require_mapping(unpinned.get("pinned_parent_binding"), "pinned_parent_binding")
    _require_nonempty_string(unpinned.get("pinned_parent_model"), "pinned_parent_model")
    effort = _require_nonempty_string(unpinned.get("pinned_parent_effort"), "pinned_parent_effort")
    if effort not in _ADMITTED_EFFORTS:
        raise ControlContractError("pinned_parent_effort is outside the closed effort set")
    if unpinned.get("authentication_mode") != _AUTHENTICATION_MODE:
        raise ControlContractError("the unpinned parent must be ChatGPT-subscription authenticated")

    boundary = _require_mapping(unpinned.get("environment_boundary"), "environment_boundary")
    _require_nonempty_string(boundary.get("client_version"), "environment_boundary.client_version")

    observed = unpinned.get("required_absent_overrides")
    if not isinstance(observed, list) or set(observed) != _ABSENT_OVERRIDE_SET:
        raise ControlContractError("required_absent_overrides must be the closed Codex set")
    if len(observed) != len(_REQUIRED_ABSENT_OVERRIDES):
        raise ControlContractError("required_absent_overrides must not repeat a member")
    return None


def validate_unpinned_exact_treatment(
    control: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, Any]:
    """Read unpinned exact treatment from produced evidence, never request intent."""

    validate_unpinned_control(control)
    if evidence.get("read_back_from") != "produced_evidence":
        raise ControlContractError("unpinned exact treatment must read produced evidence")
    produced = _require_mapping(evidence.get("produced_evidence"), "produced_evidence")
    unpinned = _require_mapping(control.get("unpinned"), "unpinned")

    served_model = produced.get("served_model")
    served_effort = produced.get("served_effort")
    if served_model != unpinned.get("pinned_parent_model"):
        raise ControlContractError("served model does not match the pinned parent")
    if served_effort != unpinned.get("pinned_parent_effort"):
        raise ControlContractError("served effort does not match the pinned parent")

    absent = _require_mapping(
        produced.get("observed_absent_overrides"), "observed_absent_overrides"
    )
    if set(absent) != _ABSENT_OVERRIDE_SET:
        raise ControlContractError("produced evidence omits a required absent override")
    if any(absent[member] is not True for member in _REQUIRED_ABSENT_OVERRIDES):
        raise ControlContractError("a required local override was not observed absent")

    return {
        "read_back_from": "produced_evidence",
        "served_model": served_model,
        "served_effort": served_effort,
        "observed_absent_overrides": {
            member: absent[member] for member in _REQUIRED_ABSENT_OVERRIDES
        },
    }


def _justified_high_effort(control: dict[str, Any]) -> dict[str, Any]:
    if control.get("control_kind") != "justified_high_effort":
        raise ControlContractError("expected a justified-high-effort control")
    return _require_mapping(control.get("justified_high_effort"), "justified_high_effort")


def validate_justified_high_effort_control(control: dict[str, Any]) -> dict[str, Any]:
    """Validate the frozen Codex justified-high-effort route binding."""

    if control.get("control_digest") != _record_digest(control, "control_digest"):
        raise ControlContractError("justified-high-effort control digest drift")
    binding = _justified_high_effort(control)
    expected = {
        "route_id": _CODEX_JUSTIFIED_HIGH_EFFORT_ROUTE_ID,
        "model": _CODEX_JUSTIFIED_HIGH_EFFORT_MODEL,
        "effort": _CODEX_JUSTIFIED_HIGH_EFFORT_EFFORT,
        "successor_freeze_digest": _CODEX_SUCCESSOR_FREEZE_ID,
        "route_evidence_digest": _CODEX_ROUTE_EVIDENCE_DIGEST,
    }
    for member, value in expected.items():
        if binding.get(member) != value:
            raise ControlContractError(f"justified-high-effort {member} drift")

    predicate = _require_mapping(
        binding.get("eligibility_predicate"), "eligibility_predicate"
    )
    if predicate.get("predicate_id") != _CODEX_JUSTIFIED_ELIGIBILITY_PREDICATE_ID:
        raise ControlContractError("justified-high-effort predicate identity drift")
    if predicate.get("result") is not True:
        raise ControlContractError("justified-high-effort route is not eligible")
    _require_nonempty_string(predicate.get("source"), "eligibility_predicate.source")
    _require_nonempty_string(binding.get("eligibility_rationale"), "eligibility_rationale")
    if binding.get("fallback_route_id") is not None:
        raise ControlContractError("justified-high-effort must not declare a fallback route")
    if binding.get("dynamic_route_discovery") is not False:
        raise ControlContractError("justified-high-effort must not use dynamic discovery")
    return copy.deepcopy(binding)


def validate_justified_high_effort_exact_treatment(
    control: dict[str, Any], evidence: dict[str, Any]
) -> dict[str, Any]:
    """Read justified-high-effort exact treatment from produced evidence."""

    binding = validate_justified_high_effort_control(control)
    if evidence.get("read_back_from") != "produced_evidence":
        raise ControlContractError("justified-high-effort exact treatment must read produced evidence")
    produced = _require_mapping(evidence.get("produced_evidence"), "produced_evidence")
    comparisons = {
        "served_route_id": binding["route_id"],
        "served_model": binding["model"],
        "served_effort": binding["effort"],
        "successor_freeze_digest": binding["successor_freeze_digest"],
        "route_evidence_digest": binding["route_evidence_digest"],
        "fallback_route_id": None,
        "dynamic_route_discovery": False,
    }
    for member, expected in comparisons.items():
        if produced.get(member) != expected:
            raise ControlContractError(
                f"produced evidence {member} does not match the frozen high-effort binding"
            )
    if produced.get("eligibility_predicate_result") is not True:
        raise ControlContractError("produced evidence does not reproduce eligibility")
    if (
        produced.get("eligibility_rationale_binding")
        != binding["eligibility_predicate"]["predicate_id"]
    ):
        raise ControlContractError("produced evidence does not bind the eligibility rationale")
    aggregate = _require_mapping(
        produced.get("parent_plus_child_aggregate"), "parent_plus_child_aggregate"
    )
    return {
        "read_back_from": "produced_evidence",
        "served_route_id": produced["served_route_id"],
        "served_model": produced["served_model"],
        "served_effort": produced["served_effort"],
        "successor_freeze_digest": produced["successor_freeze_digest"],
        "route_evidence_digest": produced["route_evidence_digest"],
        "eligibility_predicate_result": produced["eligibility_predicate_result"],
        "eligibility_rationale_binding": produced["eligibility_rationale_binding"],
        "parent_plus_child_aggregate": copy.deepcopy(aggregate),
    }


def _validate_aggregation_declarations(control: dict[str, Any]) -> dict[str, Any]:
    validate_justified_high_effort_control(control)
    specialization = _justified_high_effort(control)
    if control.get("attribution_level") != "policy":
        raise ControlContractError("parent-plus-children aggregation is policy-level only")

    rule = _require_mapping(specialization.get("aggregation_rule"), "aggregation_rule")
    if sorted(rule) != sorted(_FROZEN_PARETO_DIMENSIONS):
        raise ControlContractError(
            "aggregation_rule must cover the frozen eight decision dimensions"
        )
    if rule.get("terminal_state") != _SEVERITY_FOLD_RULE:
        raise ControlContractError("terminal_state must fold by worst-wins severity")
    if rule.get("acceptance") != _PARENT_ORACLE_RULE:
        raise ControlContractError("acceptance must be read from the parent oracle")
    for dimension, combining in rule.items():
        if combining not in (_ADDITIVE_RULE, _SEVERITY_FOLD_RULE, _PARENT_ORACLE_RULE):
            raise ControlContractError(
                f"aggregation_rule[{dimension!r}] declares unknown combining rule"
            )

    severity = _require_sequence(
        specialization.get("terminal_state_severity"), "terminal_state_severity"
    )
    if sorted(severity) != sorted(_FROZEN_TERMINAL_STATES):
        raise ControlContractError("terminal_state_severity must match the frozen enum")
    if specialization.get("acceptance_rule") != _PARENT_ORACLE_RULE:
        raise ControlContractError("acceptance_rule must match the parent oracle rule")
    if specialization.get("acceptance_floor_on_non_completed") != 0:
        raise ControlContractError("non-completed acceptance must floor to zero")

    raw_rule = _require_mapping(
        specialization.get("raw_token_aggregation"), "raw_token_aggregation"
    )
    if sorted(raw_rule) != sorted(_FROZEN_RAW_TOKEN_MEMBERS):
        raise ControlContractError("raw_token_aggregation must cover the frozen raw-token vector")
    if any(combining != _ADDITIVE_RULE for combining in raw_rule.values()):
        raise ControlContractError("raw token members must aggregate additively")

    cache_rule = _require_mapping(
        specialization.get("cache_aggregation"), "cache_aggregation"
    )
    if sorted(cache_rule) != sorted(_CACHE_QUANTITY_CEILINGS):
        raise ControlContractError("cache_aggregation must declare the two cache diagnostics")
    write_rule = _require_mapping(
        cache_rule.get("cache_write_tokens_by_ttl_class"),
        "cache_write_tokens_by_ttl_class",
    )
    if sorted(write_rule) != sorted(_FROZEN_CACHE_TTL_CLASSES):
        raise ControlContractError("cache write aggregation must use the frozen TTL classes")
    if any(combining != _ADDITIVE_RULE for combining in write_rule.values()):
        raise ControlContractError("cache write TTL classes must aggregate additively")
    if cache_rule.get("cache_read_tokens") != _ADDITIVE_RULE:
        raise ControlContractError("cache_read_tokens must aggregate additively")
    if specialization.get("unrecorded_quantity_disposition") != "unobserved":
        raise ControlContractError("missing diagnostics must stay unobserved")
    return specialization


def _resource_vector(member: dict[str, Any]) -> dict[str, Any]:
    return _require_mapping(member.get("resource_vector"), "resource_vector")


def _raw_token_vector(member: dict[str, Any]) -> dict[str, Any]:
    return _require_mapping(member.get("raw_token_vector"), "raw_token_vector")


def _sum_or_unobserved(values: list[Any], label: str) -> int | None:
    if any(value is None for value in values):
        return None
    return sum(_whole_number(value, label) for value in values)


def _unit_members(
    members: Any, specialization: dict[str, Any]
) -> list[dict[str, Any]]:
    if not isinstance(members, list) or not members:
        raise ControlContractError("parent-plus-children aggregation requires a non-empty unit")

    observed: list[dict[str, Any]] = []
    member_ids: list[str] = []
    for index, raw_member in enumerate(members):
        member = _require_mapping(raw_member, f"members[{index}]")
        row_id = _require_nonempty_string(member.get("row_id"), f"members[{index}].row_id")
        if row_id in member_ids:
            raise ControlContractError(f"unit member repeats row_id {row_id!r}")
        if "spawned_by" not in member:
            raise ControlContractError(f"{row_id!r} records no spawned_by boundary")
        if index == 0 and member["spawned_by"] is not None:
            raise ControlContractError("the first unit member must be the parent row")
        if index > 0 and member["spawned_by"] is None:
            raise ControlContractError(f"{row_id!r} is a second parent row")

        vector = _resource_vector(member)
        if "terminal_state" not in vector or vector.get("terminal_state") is None:
            raise ControlContractError(f"{row_id!r} records no terminal_state")
        member_ids.append(row_id)
        observed.append(member)

    reachable = {member_ids[0]}
    pending = observed[1:]
    while pending:
        linked = [member for member in pending if member["spawned_by"] in reachable]
        if not linked:
            raise ControlContractError(
                f"{pending[0]['row_id']!r} records a spawned_by value outside the parent chain"
            )
        reachable.update(member["row_id"] for member in linked)
        pending = [member for member in pending if member["row_id"] not in reachable]

    fan_out = _require_mapping(
        specialization.get("topology_descriptor"), "topology_descriptor"
    ).get("fan_out")
    if not isinstance(fan_out, int) or isinstance(fan_out, bool) or fan_out < 0:
        raise ControlContractError("topology_descriptor.fan_out must be a non-negative integer")
    if len(observed) - 1 > fan_out:
        raise ControlContractError("parent-plus-children unit exceeds the declared fan-out")
    return observed


def _worst_terminal_state(states: list[Any], severity_order: list[Any]) -> str:
    worst = None
    rank = -1
    for state in states:
        if state not in severity_order:
            raise ControlContractError(f"{state!r} is outside terminal_state_severity")
        position = severity_order.index(state)
        if position > rank:
            worst = state
            rank = position
    if worst is None:
        raise ControlContractError("the unit has no terminal_state to fold")
    return str(worst)


def aggregate_parent_plus_children(
    control: dict[str, Any], members: Any
) -> dict[str, Any]:
    """Aggregate a Codex justified-high-effort parent plus every spawned child."""

    specialization = _validate_aggregation_declarations(control)
    unit = _unit_members(members, specialization)
    decision_dimensions: dict[str, Any] = {}
    for dimension, combining in specialization["aggregation_rule"].items():
        if combining == _ADDITIVE_RULE:
            decision_dimensions[dimension] = sum(
                _whole_number(
                    _resource_vector(member).get(dimension),
                    f"{member.get('row_id')}.{dimension}",
                )
                for member in unit
            )

    states = [_resource_vector(member).get("terminal_state") for member in unit]
    decision_dimensions["terminal_state"] = _worst_terminal_state(
        states, list(specialization["terminal_state_severity"])
    )
    parent_acceptance = _resource_vector(unit[0]).get("acceptance")
    if parent_acceptance is not None and (
        isinstance(parent_acceptance, bool)
        or not isinstance(parent_acceptance, (int, float))
    ):
        raise ControlContractError("parent acceptance must be numeric or null")
    if decision_dimensions["terminal_state"] != _CLEAN_TERMINAL_STATE:
        parent_acceptance = specialization["acceptance_floor_on_non_completed"]
    decision_dimensions["acceptance"] = parent_acceptance

    raw_tokens = {
        member: _sum_or_unobserved(
            [_raw_token_vector(row).get(member) for row in unit], member
        )
        for member in specialization["raw_token_aggregation"]
    }
    raw_token_ceiling_quantity = _sum_or_unobserved(
        [raw_tokens[member] for member in _RAW_TOKEN_CEILING_QUANTITY_MEMBERS],
        "raw_token_ceiling",
    )

    unobserved: list[str] = []
    diagnostics = [row.get("cache_diagnostic") for row in unit]
    if any(diagnostic is None for diagnostic in diagnostics):
        cache_write = None
        cache_read = None
        unobserved.extend(_CACHE_QUANTITY_CEILINGS.values())
    else:
        for diagnostic in diagnostics:
            if not isinstance(diagnostic, dict):
                raise ControlContractError("cache_diagnostic must be an object or absent")
            if not isinstance(diagnostic.get("cache_write_tokens_by_ttl_class", {}), dict):
                raise ControlContractError(
                    "cache_write_tokens_by_ttl_class must be an object or absent"
                )
        cache_read = _sum_or_unobserved(
            [diagnostic.get("cache_read_tokens") for diagnostic in diagnostics],
            "cache_read_tokens",
        )
        if cache_read is None:
            unobserved.append(_CACHE_QUANTITY_CEILINGS["cache_read_tokens"])
        per_class = {
            ttl_class: _sum_or_unobserved(
                [
                    diagnostic.get("cache_write_tokens_by_ttl_class", {}).get(ttl_class)
                    for diagnostic in diagnostics
                ],
                f"cache_write_tokens_by_ttl_class.{ttl_class}",
            )
            for ttl_class in _FROZEN_CACHE_TTL_CLASSES
        }
        if any(value is None for value in per_class.values()):
            cache_write = None
            unobserved.append(_CACHE_QUANTITY_CEILINGS["cache_write_tokens_by_ttl_class"])
        else:
            cache_write = per_class

    return {
        "unit_member_ids": [member["row_id"] for member in unit],
        "decision_dimensions": decision_dimensions,
        "raw_tokens": raw_tokens,
        "raw_token_ceiling_members": list(_RAW_TOKEN_CEILING_QUANTITY_MEMBERS),
        "raw_token_ceiling_quantity": raw_token_ceiling_quantity,
        "cache_write_tokens_by_ttl_class": cache_write,
        "cache_read_tokens": cache_read,
        "bounded_by": {**_RAW_TOKEN_MEMBER_CEILINGS, **_CACHE_QUANTITY_CEILINGS},
        "unobserved": sorted(set(unobserved)),
        "member_count": len(unit),
    }


def validate_car_004_twin_mirror(
    *,
    car_handoff_path: Path,
    codex_registry_schema_path: Path,
    codex_registry_instance_path: Path,
) -> dict[str, Any]:
    """Validate frozen registry authorities and the handoff category envelope."""

    handoff_entries, handoff_divergences = _load_handoff_membership(car_handoff_path)
    _, frozen_divergences = _load_handoff_membership(_FROZEN_CAR_HANDOFF_PATH)
    _validate_handoff_obligations(handoff_entries)
    compared_categories = sorted(
        {
            entry["category"]
            for entry in handoff_entries
            if entry.get("category") in range(1, 7)
        }
    )
    if compared_categories != list(range(1, 7)):
        raise ControlContractError("CAR-004 handoff category envelope drift")
    _assert_single_sanctioned_divergence(
        expected_divergences=frozen_divergences,
        actual_divergences=handoff_divergences,
    )

    car_schema = _load_json(_CAR_REGISTRY_SCHEMA_PATH)
    codex_schema = _load_json(codex_registry_schema_path)
    if codex_schema != _load_json(_FROZEN_CODEX_REGISTRY_SCHEMA_PATH):
        raise ControlContractError("Codex registry schema authority drift")
    car_registry = _load_json(_CAR_REGISTRY_PATH)
    codex_registry = _load_json(codex_registry_instance_path)

    _assert_content_addresses(codex_registry)
    if codex_registry != load_registry_authority(_FROZEN_CODEX_REGISTRY_PATH):
        raise ControlContractError("Codex registry fixture authority drift")
    if _normalize_platform_value(codex_schema) != car_schema:
        raise ControlContractError(
            "Codex registry schema has drift beyond the sanctioned platform values"
        )
    if _normalize_platform_value(codex_registry) != _normalize_platform_value(
        car_registry
    ):
        raise ControlContractError(
            "Codex registry fixture has drift beyond the sanctioned platform values"
        )

    smoke_bounds = codex_registry["smoke_bounds"]
    car_control_kind_enum = car_schema["$defs"]["control"]["properties"][
        "control_kind"
    ]["enum"]
    control_kind_enum = codex_schema["$defs"]["control"]["properties"]["control_kind"][
        "enum"
    ]
    car_only = sorted(set(car_control_kind_enum) - set(control_kind_enum))
    codex_only = sorted(set(control_kind_enum) - set(car_control_kind_enum))
    unchanged = sorted(set(car_control_kind_enum) & set(control_kind_enum))
    if len(car_only) != 1 or len(codex_only) != 1:
        raise ControlContractError("sanctioned control-kind divergence drift")
    divergence = {
        "category": handoff_divergences[0]["category"],
        "car_value": car_only[0],
        "codex_value": codex_only[0],
        "unchanged_values": unchanged,
    }
    return {
        "compared_categories": compared_categories,
        "sanctioned_divergences": [divergence],
        "preserved_literals": {
            "zeros": {
                "max_confirmation_entries": smoke_bounds["max_confirmation_entries"][
                    "value"
                ]
            },
            "units": {
                "raw_token_ceiling": smoke_bounds["raw_token_ceiling"]["unit"]
            },
            "enums": {"control_kind": list(control_kind_enum)},
            "numerics": {
                "raw_token_ceiling": smoke_bounds["raw_token_ceiling"]["value"]
            },
        },
    }


def _objective_set_digest(objective_ids: Any) -> str:
    if not isinstance(objective_ids, list) or not objective_ids:
        raise ControlContractError("a partition must register at least one objective")
    if any(not isinstance(objective, str) or not objective for objective in objective_ids):
        raise ControlContractError("partition objective ids must be non-empty strings")
    payload = sorted(set(objective_ids))
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def validate_partition_entries(entries: Any) -> list[dict[str, Any]]:
    """Validate the closed two-entry Codex partition authority."""

    if not isinstance(entries, list) or len(entries) != 2:
        raise ControlContractError("partition fixture must contain exactly two entries")

    observed_ids: set[str] = set()
    observed_objectives: set[str] = set()
    validated: list[dict[str, Any]] = []
    for index, raw_entry in enumerate(entries):
        entry = _require_mapping(raw_entry, f"entries[{index}]")
        required = {
            "frozen_at",
            "objective_ids",
            "objective_set_digest",
            "owning_spec",
            "partition_id",
            "partition_type",
            "qualification_eligible",
            "record_kind",
            "schema_version",
        }
        if set(entry) != required:
            raise ControlContractError(f"entries[{index}] member-set drift")
        partition_id = _require_nonempty_string(
            entry.get("partition_id"), f"entries[{index}].partition_id"
        )
        if partition_id in observed_ids:
            raise ControlContractError(f"duplicate partition_id {partition_id!r}")
        observed_ids.add(partition_id)
        objectives = entry.get("objective_ids")
        if not isinstance(objectives, list) or objectives != sorted(set(objectives)):
            raise ControlContractError(f"{partition_id!r} objective ids are not sorted unique")
        if entry.get("objective_set_digest") != _objective_set_digest(objectives):
            raise ControlContractError(f"{partition_id!r} objective_set_digest drift")
        overlap = observed_objectives & set(objectives)
        if overlap:
            raise ControlContractError(
                f"partition objective overlap: {sorted(overlap)}"
            )
        observed_objectives.update(objectives)
        if entry.get("owning_spec") != "G56R-004":
            raise ControlContractError(f"{partition_id!r} owner drift")
        if entry.get("schema_version") != "1.0.0":
            raise ControlContractError(f"{partition_id!r} schema_version drift")
        if entry.get("record_kind") != "partition_registry_entry":
            raise ControlContractError(f"{partition_id!r} record_kind drift")
        validated.append(copy.deepcopy(entry))

    expected = {
        "G56R-011-RESERVED-COMPARISON": ("integrated_confirmation", True),
        "G56R-004-SMOKE": ("calibration", False),
    }
    if observed_ids != set(expected):
        raise ControlContractError("partition identifier set drift")
    for entry in validated:
        expected_type, expected_eligibility = expected[entry["partition_id"]]
        if (
            entry.get("partition_type") != expected_type
            or entry.get("qualification_eligible") is not expected_eligibility
        ):
            raise ControlContractError(
                f"{entry['partition_id']!r} type or eligibility drift"
            )
    return validated


def load_partition_entries(path: Path) -> list[dict[str, Any]]:
    """Load and validate the two Codex partition registry entries."""

    fixture = _load_json(path)
    if (
        not isinstance(fixture, dict)
        or fixture.get("schema_version") != "1.0.0"
        or fixture.get("fixture_kind") != "policy_control_partition_registry"
    ):
        raise ControlContractError("partition fixture identity drift")
    return validate_partition_entries(fixture.get("entries"))


def _partition_entries_by_id(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {entry["partition_id"]: entry for entry in entries}


def reserved_partition_entry(entries: Any) -> dict[str, Any]:
    if not isinstance(entries, list):
        raise ControlContractError("partition entries must be an array")
    reserved = [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("qualification_eligible") is True
    ]
    if len(reserved) != 1:
        raise ControlContractError("exactly one qualification-eligible partition is required")
    return copy.deepcopy(reserved[0])


def _row_objective_ids(row: dict[str, Any], label: str) -> list[str]:
    objective_ids: list[str] = []
    if row.get("objective_id") is not None:
        objective_ids.append(str(row["objective_id"]))
    many = row.get("objective_ids")
    if many is not None:
        if not isinstance(many, list):
            raise ControlContractError(f"row {label}: objective_ids must be an array")
        objective_ids.extend(str(objective) for objective in many)
    return objective_ids


def assert_reserved_partition_untouched(
    rows: Any, reserved_entry: dict[str, Any]
) -> None:
    """Reject replay or smoke evidence that consumes the G56R-011 reservation."""

    if not isinstance(rows, list):
        raise ControlContractError("evidence rows must be an array")
    reserved_id = _require_nonempty_string(
        reserved_entry.get("partition_id"), "reserved partition_id"
    )
    objectives = reserved_entry.get("objective_ids")
    if not isinstance(objectives, list) or not objectives:
        raise ControlContractError("the reserved partition declares no objective")
    reserved_objectives = set(objectives)
    for index, raw_row in enumerate(rows):
        row = _require_mapping(raw_row, f"rows[{index}]")
        label = str(row.get("row_id") or index)
        if row.get("partition_id") == reserved_id:
            raise ControlContractError(
                f"row {label!r} names reserved partition {reserved_id!r}"
            )
        overlap = reserved_objectives & set(_row_objective_ids(row, label))
        if overlap:
            raise ControlContractError(
                f"row {label!r} consumes reserved objectives {sorted(overlap)}"
            )


def partition_owned_mirror_members(
    *, handoff_path: Path, fixture_path: Path
) -> dict[str, Any]:
    """Report the partition-owned category 1-6 subset after validating its source."""

    entries = load_partition_entries(fixture_path)
    if _partition_entries_by_id(entries) != _partition_entries_by_id(
        load_partition_entries(_FROZEN_CODEX_PARTITION_ENTRIES_PATH)
    ):
        raise ControlContractError("partition fixture authority drift")
    handoff_entries, _ = _load_handoff_membership(handoff_path)
    required_car_ids = {"CAR-004-SMOKE", "CAR-011-RESERVED-COMPARISON"}
    observed_car_ids = {
        str(record.get("member_id"))
        for record in handoff_entries
        if record.get("category") == 4
        and record.get("kind") == "partition_id"
        and record.get("mirror_obligation") == "car_owned"
    }
    if observed_car_ids != required_car_ids:
        raise ControlContractError("CAR-004 partition identity evidence drift")
    return {
        "categories_present": [4],
        "partition_ids": sorted(entry["partition_id"] for entry in entries),
        "missing": [],
        "extra": [],
        "drifted": [],
    }


def _sha256_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _smoke_partition_entry(entries: list[dict[str, Any]]) -> dict[str, Any]:
    smoke = [
        entry
        for entry in entries
        if entry.get("partition_type") == "calibration"
        and entry.get("qualification_eligible") is False
    ]
    if len(smoke) != 1:
        raise ControlContractError(
            "exactly one G56R-004 smoke calibration partition is required"
        )
    return smoke[0]


def replay_codex_controls(path: Path) -> list[dict[str, Any]]:
    """Replay committed non-live Codex control rows with governed evidence."""

    fixture = _load_json(path)
    if not isinstance(fixture, dict):
        raise ControlContractError("Codex replay fixture must be an object")
    if fixture != _load_json(_FROZEN_CODEX_REPLAY_CASES_PATH):
        raise ControlContractError("replay fixture authority drift")
    cases = fixture.get("control_replay_cases")
    if not isinstance(cases, list):
        raise ControlContractError("control_replay_cases must be an array")
    entries = load_partition_entries(_FROZEN_CODEX_PARTITION_ENTRIES_PATH)
    reserved = reserved_partition_entry(entries)
    smoke = _smoke_partition_entry(entries)
    admitted_objectives = set(smoke["objective_ids"])

    observed_kinds: set[str] = set()
    observed_ids: set[str] = set()
    replayed: list[dict[str, Any]] = []
    for index, raw_case in enumerate(cases):
        case = _require_mapping(raw_case, f"control_replay_cases[{index}]")
        expected_members = {
            "case_id",
            "control_id",
            "control_kind",
            "objective_id",
            "outcome_bearing",
            "partition_id",
            "partition_type",
            "scored",
        }
        if set(case) != expected_members:
            raise ControlContractError(f"control_replay_cases[{index}] member-set drift")
        case_id = _require_nonempty_string(case.get("case_id"), f"case {index} id")
        control_kind = _require_nonempty_string(
            case.get("control_kind"), f"{case_id}.control_kind"
        )
        if control_kind not in _CODEX_CONTROL_IDS_BY_KIND:
            raise ControlContractError(f"{control_kind!r} is not a Codex control kind")
        control_id = _require_nonempty_string(
            case.get("control_id"), f"{case_id}.control_id"
        )
        if control_id != _CODEX_CONTROL_IDS_BY_KIND[control_kind]:
            raise ControlContractError(f"{case_id} control_id drift")
        if case.get("partition_id") != smoke["partition_id"]:
            raise ControlContractError(f"{case_id} partition_id drift")
        if case.get("partition_type") != "calibration":
            raise ControlContractError(f"{case_id} is not a calibration replay row")
        if case.get("scored") is not False:
            raise ControlContractError(f"{case_id} replay row must be non-scored")
        if case.get("outcome_bearing") is not False:
            raise ControlContractError(
                f"{case_id} replay row must be non-outcome-bearing"
            )
        objective_id = _require_nonempty_string(
            case.get("objective_id"), f"{case_id}.objective_id"
        )
        if objective_id not in admitted_objectives:
            raise ControlContractError(
                f"{case_id} objective is outside the smoke partition"
            )
        assert_reserved_partition_untouched([case], reserved)
        if control_kind in observed_kinds or control_id in observed_ids:
            raise ControlContractError("duplicate Codex control replay case")
        observed_kinds.add(control_kind)
        observed_ids.add(control_id)

        governed_evidence = {
            "digest": _sha256_digest(case),
            "source": "committed_fixture",
        }
        replayed.append(
            {
                "case_id": case_id,
                "control_id": control_id,
                "control_kind": control_kind,
                "governed_evidence": governed_evidence,
                "objective_id": objective_id,
                "outcome_bearing": False,
                "partition_id": smoke["partition_id"],
                "partition_type": "calibration",
                "scored": False,
            }
        )

    if observed_kinds != set(_CODEX_CONTROL_KINDS):
        raise ControlContractError("Codex replay cases do not cover every control kind")
    if observed_ids != set(_CODEX_CONTROL_IDS_BY_KIND.values()):
        raise ControlContractError("Codex replay cases do not cover every control id")
    return replayed


_FINAL_RECONCILIATION_BUCKETS = (
    "missing",
    "extra",
    "invented",
    "drifted",
    "duplicated",
    "silently_omitted",
)
_DIFFERENCE_BUCKET_BY_RECONCILIATION_MUTATION = {
    "missing": "missing_from_record",
    "extra": "absent_from_artifacts",
    "invented": "absent_from_artifacts",
    "drifted": "mismatched",
    "duplicated": "duplicated",
    "silently_omitted": "missing_from_record",
}
_HANDOFF_JSON_BLOCK = re.compile(r"^```json\n(.*?)^```", re.MULTILINE | re.DOTALL)
_FINAL_DIFFERENCE_BUCKETS = (
    "missing_from_record",
    "absent_from_artifacts",
    "mismatched",
    "duplicated",
)
_FINAL_COMPARE_FIELDS = {
    1: ("category", "member_id", "contract_id", "hash_relevant", "schema_version"),
    2: ("category", "member_id", "contract_id", "hash_relevant", "properties", "required"),
    3: ("category", "member_id", "contract_id", "hash_relevant", "kind", "members", "sites"),
    4: ("category", "member_id", "contract_id", "hash_relevant", "kind", "sites"),
    5: ("category", "member_id", "contract_id", "hash_relevant", "sites"),
    6: ("category", "member_id", "contract_id", "hash_relevant", "value", "unit", "direction", "class"),
}
_FIELDS_NOT_CROSS_PLATFORM_COMPARED = (
    "bound_id",
    "digest",
    "mirror_obligation",
    "path",
    "rationale",
    "requirement",
    "sha256",
)


def _repo_relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(_LAYER6_ROOT.parents[2]))
    except ValueError:
        return str(resolved)


def _json_pointer_token(value: Any) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _walk_json_pointer(
    node: Any, pointer: str, visit: Any
) -> None:
    visit(node, pointer)
    if isinstance(node, dict):
        for key, value in node.items():
            _walk_json_pointer(value, f"{pointer}/{_json_pointer_token(key)}", visit)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _walk_json_pointer(value, f"{pointer}/{index}", visit)


def _resolve_json_pointer(document: Any, pointer: str) -> Any:
    node = document
    for token in pointer.lstrip("#").split("/"):
        if not token:
            continue
        token = token.replace("~1", "/").replace("~0", "~")
        node = node[int(token)] if isinstance(node, list) else node[token]
    return node


def _document_identity(document: dict[str, Any]) -> str:
    for key in ("registry_id", "comparison_id", "fixture_kind"):
        if key in document:
            identity = _normalize_platform_value(document[key])
            if isinstance(identity, str) and identity:
                return identity
    raise ControlContractError("document declares no reconciliation identity")


def _control_pointer_by_kind(registry: dict[str, Any], control_kind: str) -> str:
    for index, control in enumerate(_require_sequence(registry.get("controls"), "controls")):
        control_map = _require_mapping(control, f"controls[{index}]")
        if control_map.get("control_kind") == control_kind:
            return f"#/controls/{index}"
    raise ControlContractError(f"the registry declares no {control_kind} control")


def _load_handoff_membership(
    path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ControlContractError(f"cannot load {path}: {exc}") from exc
    blocks = _HANDOFF_JSON_BLOCK.findall(text)
    if len(blocks) != 2:
        raise ControlContractError("CAR-004 handoff machine-readable block drift")
    try:
        entries = json.loads(blocks[0])
        divergences = json.loads(blocks[1])
    except json.JSONDecodeError as exc:
        raise ControlContractError(f"CAR-004 handoff JSON drift: {exc}") from exc
    if not isinstance(entries, list) or not isinstance(divergences, list):
        raise ControlContractError("CAR-004 handoff blocks must be arrays")
    return (
        [_require_mapping(entry, "CAR-004 handoff entry") for entry in entries],
        [
            _require_mapping(divergence, "CAR-004 sanctioned divergence")
            for divergence in divergences
        ],
    )


def _validate_handoff_obligations(entries: list[dict[str, Any]]) -> None:
    for entry in entries:
        if entry.get("category") not in range(1, 7):
            continue
        if entry.get("mirror_obligation") not in {
            "mirror_required",
            "car_owned",
            "sanctioned_divergence",
        }:
            raise ControlContractError("CAR-004 handoff mirror obligation drift")


def _final_artifact_group(entry: dict[str, Any]) -> str:
    if entry.get("contract_id") == _CAR_COMPARISON_SCHEMA_ID:
        return "comparison"
    if entry.get("kind") == "partition_id":
        return "partition"
    sites = entry.get("sites")
    if isinstance(sites, list) and any(
        isinstance(site, str) and site.startswith("policy_control_partition_registry#")
        for site in sites
    ):
        return "partition"
    return "registry"


def _final_marker(entry: dict[str, Any], field: str | None = None) -> dict[str, Any]:
    marker = {
        "artifact_group": _final_artifact_group(entry),
        "category": entry.get("category"),
        "member_id": entry.get("member_id"),
    }
    if field is not None:
        marker["field"] = field
    return marker


def _final_members_by_key(
    entries: list[dict[str, Any]],
) -> tuple[dict[tuple[int, str], dict[str, Any]], list[dict[str, Any]]]:
    keyed: dict[tuple[int, str], dict[str, Any]] = {}
    duplicated: list[dict[str, Any]] = []
    for entry in entries:
        category = entry.get("category")
        member_id = entry.get("member_id")
        if category not in range(1, 7):
            continue
        if (
            not isinstance(category, int)
            or not isinstance(member_id, str)
            or not member_id
        ):
            raise ControlContractError("CAR-004 handoff entry identity drift")
        key = (category, member_id)
        if key in keyed:
            duplicated.append(_final_marker(entry))
            continue
        keyed[key] = copy.deepcopy(entry)
    return keyed, duplicated


def _diff_final_handoff_members(
    *,
    expected_entries: list[dict[str, Any]],
    actual_entries: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    expected, expected_duplicated = _final_members_by_key(expected_entries)
    actual, actual_duplicated = _final_members_by_key(actual_entries)
    if expected_duplicated:
        raise ControlContractError(
            "committed CAR-004 handoff authority contains duplicated members"
        )

    missing = [
        _final_marker(expected[key])
        for key in sorted(set(expected) - set(actual))
    ]
    absent = [
        _final_marker(actual[key])
        for key in sorted(set(actual) - set(expected))
    ]
    mismatched: list[dict[str, Any]] = []
    for key in sorted(set(expected) & set(actual)):
        expected_entry = expected[key]
        actual_entry = actual[key]
        for field in _FINAL_COMPARE_FIELDS[key[0]]:
            if (
                (field in expected_entry) != (field in actual_entry)
                or expected_entry.get(field) != actual_entry.get(field)
            ):
                mismatched.append(_final_marker(expected_entry, field))
    return {
        "missing_from_record": missing,
        "absent_from_artifacts": absent,
        "mismatched": mismatched,
        "duplicated": actual_duplicated,
    }


def _assert_single_sanctioned_divergence(
    *,
    expected_divergences: list[dict[str, Any]],
    actual_divergences: list[dict[str, Any]],
) -> None:
    if len(expected_divergences) != 1 or len(actual_divergences) != 1:
        raise ControlContractError("sanctioned divergence cardinality drift")
    if actual_divergences != expected_divergences:
        raise ControlContractError("sanctioned divergence authority drift")


def _final_reconciliation_buckets(
    differences: dict[str, list[dict[str, Any]]],
    *,
    expected_entries: list[dict[str, Any]],
    actual_entries: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    expected, _ = _final_members_by_key(expected_entries)
    actual, _ = _final_members_by_key(actual_entries)
    missing_keys = sorted(set(expected) - set(actual))
    absent_keys = sorted(set(actual) - set(expected))
    expected_member_ids = {member_id for _, member_id in expected}
    return {
        "missing": [
            _final_marker(expected[key])
            for key in missing_keys
            if expected[key].get("mirror_obligation") != "mirror_required"
        ],
        "extra": [
            _final_marker(actual[key])
            for key in absent_keys
            if key[1] in expected_member_ids
        ],
        "invented": [
            _final_marker(actual[key])
            for key in absent_keys
            if key[1] not in expected_member_ids
        ],
        "drifted": copy.deepcopy(differences["mismatched"]),
        "duplicated": copy.deepcopy(differences["duplicated"]),
        "silently_omitted": [
            _final_marker(expected[key])
            for key in missing_keys
            if expected[key].get("mirror_obligation") == "mirror_required"
        ],
    }


def _raise_on_final_reconciliation_differences(report: dict[str, Any]) -> None:
    payload = {
        "differences": {
            bucket: report["differences"][bucket]
            for bucket in _FINAL_DIFFERENCE_BUCKETS
            if report["differences"][bucket]
        },
        "buckets": {
            bucket: report[bucket]
            for bucket in _FINAL_RECONCILIATION_BUCKETS
            if report[bucket]
        },
    }
    if payload["differences"] or payload["buckets"]:
        raise ControlContractError(
            "final twin reconciliation differences: "
            + json.dumps(payload)
        )


def _validate_codex_registry_reconciliation_sources(
    *, schema_path: Path, instance_path: Path
) -> dict[str, Any]:
    schema = _load_json(schema_path)
    if not isinstance(schema, dict):
        raise ControlContractError("Codex registry schema must be an object")
    if schema != _load_json(_FROZEN_CODEX_REGISTRY_SCHEMA_PATH):
        raise ControlContractError("Codex registry schema authority drift")
    return validate_registry_authority(_load_json(instance_path))


def _validate_comparison_for_reconciliation_derivation(
    *, schema_path: Path, instance_path: Path
) -> dict[str, Any]:
    schema = _load_json(schema_path)
    if not isinstance(schema, dict):
        raise ControlContractError("comparison reconciliation sources must be objects")
    if schema.get("$id") != _codex_control_comparison.CODEX_COMPARISON_SCHEMA_ID:
        raise ControlContractError("comparison schema identity drift")
    if schema.get("properties", {}).get("schema_version", {}).get("const") != "1.0.0":
        raise ControlContractError("comparison schema version drift")
    if schema != _codex_control_comparison.COMPARISON_SCHEMA:
        raise ControlContractError("comparison schema authority drift")
    instance = _load_json(instance_path)
    if not isinstance(instance, dict):
        raise ControlContractError("comparison fixture must be an object")
    try:
        _codex_control_comparison.validate_instance(
            instance, schema, path="codex_comparison"
        )
        return dict(_codex_control_comparison.validate_comparison(instance))
    except (
        _codex_control_comparison.ControlComparisonError,
        _codex_control_comparison.ControlContractError,
    ) as exc:
        raise ControlContractError(
            f"comparison reconciliation validation failed: {exc}"
        ) from exc


def _final_entry(
    *,
    category: int,
    member_id: str,
    contract_id: str,
    facts: dict[str, Any],
) -> dict[str, Any]:
    return {
        "category": category,
        "member_id": member_id,
        "contract_id": contract_id,
        "hash_relevant": True,
        **facts,
    }


def _derive_schema_final_entries(
    *,
    schemas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for raw_schema in schemas:
        schema = _require_mapping(
            _normalize_platform_value(raw_schema), "normalized schema"
        )
        schema_id = _require_nonempty_string(schema.get("$id"), "schema $id")
        schema_version = (
            _require_mapping(schema.get("properties"), "schema.properties")
            .get("schema_version", {})
            .get("const")
        )
        entries.append(
            _final_entry(
                category=1,
                member_id=schema_id,
                contract_id=schema_id,
                facts={"hash_relevant": False, "schema_version": schema_version},
            )
        )

        def declared_member(node: Any, pointer: str) -> None:
            if not isinstance(node, dict):
                return
            if node.get("type") != "object" or "properties" not in node:
                return
            member_id = f"{schema_id}{pointer}"
            entries.append(
                _final_entry(
                    category=2,
                    member_id=member_id,
                    contract_id=schema_id,
                    facts={
                        "properties": sorted(node["properties"]),
                        "required": sorted(node.get("required", [])),
                    },
                )
            )

        _walk_json_pointer(schema, "#", declared_member)

        groups: dict[tuple[str, str], list[str]] = {}
        values: dict[tuple[str, str], Any] = {}

        def closed_member(node: Any, pointer: str) -> None:
            if not isinstance(node, dict):
                return
            for kind in ("enum", "const"):
                if kind not in node:
                    continue
                value = node[kind]
                key = (kind, json.dumps(value, sort_keys=True))
                groups.setdefault(key, []).append(pointer)
                values[key] = value

        _walk_json_pointer(schema, "#", closed_member)
        for key, sites in groups.items():
            kind = key[0]
            members = values[key] if kind == "enum" else [values[key]]
            ordered = sorted(f"{schema_id}{site}" for site in sites)
            entries.append(
                _final_entry(
                    category=3,
                    member_id=ordered[0],
                    contract_id=schema_id,
                    facts={
                        "kind": kind,
                        "members": members,
                        "sites": ordered,
                    },
                )
            )
    return entries


def _derive_identifier_final_entries(
    *,
    registry: dict[str, Any],
    comparison: dict[str, Any],
    partition_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    registry_identity = _document_identity(registry)
    comparison_identity = _document_identity(comparison)
    partition_identity = "policy_control_partition_registry"
    orchestration = _control_pointer_by_kind(registry, "orchestration_changing")
    additive_records_schema_id = _require_nonempty_string(
        _ADDITIVE_RECORDS_SCHEMA.get("$id"), "additive records schema id"
    )

    sightings: list[tuple[str, str, str, bool, str]] = [
        (
            "registry_id",
            _require_nonempty_string(registry.get("registry_id"), "registry_id"),
            f"{registry_identity}#/registry_id",
            True,
            _CAR_SCHEMA_ID,
        ),
        (
            "comparison_id",
            _require_nonempty_string(comparison.get("comparison_id"), "comparison_id"),
            f"{comparison_identity}#/comparison_id",
            True,
            _CAR_COMPARISON_SCHEMA_ID,
        ),
        (
            "topology_id",
            _require_nonempty_string(
                _resolve_json_pointer(
                    registry,
                    (
                        f"{orchestration}/orchestration_changing"
                        "/topology_descriptor/topology_id"
                    ),
                ),
                "topology_id",
            ),
            (
                f"{registry_identity}{orchestration}/orchestration_changing"
                "/topology_descriptor/topology_id"
            ),
            True,
            _CAR_SCHEMA_ID,
        ),
        (
            "partition_id",
            _require_nonempty_string(
                _require_mapping(
                    comparison.get("reserved_partition_binding"),
                    "reserved_partition_binding",
                ).get("id"),
                "reserved_partition_binding.id",
            ),
            f"{comparison_identity}#/reserved_partition_binding/id",
            False,
            additive_records_schema_id,
        ),
    ]
    for index, control in enumerate(_require_sequence(registry.get("controls"), "controls")):
        control_map = _require_mapping(control, f"controls[{index}]")
        sightings.append(
            (
                "control_id",
                _require_nonempty_string(control_map.get("control_id"), "control_id"),
                f"{registry_identity}#/controls/{index}/control_id",
                True,
                _CAR_SCHEMA_ID,
            )
        )
    for index, entry in enumerate(partition_entries):
        sightings.append(
            (
                "partition_id",
                _require_nonempty_string(entry.get("partition_id"), "partition_id"),
                f"{partition_identity}#/entries/{index}/partition_id",
                False,
                additive_records_schema_id,
            )
        )
    for schema_id, contract_id in (
        (_CAR_SCHEMA_ID, _CAR_SCHEMA_ID),
        (_CAR_COMPARISON_SCHEMA_ID, _CAR_COMPARISON_SCHEMA_ID),
    ):
        sightings.append(("schema_id", schema_id, f"{schema_id}#/$id", False, contract_id))

    grouped: dict[str, dict[str, Any]] = {}
    for kind, value, site, hash_relevant, contract_id in sightings:
        member_id = _require_nonempty_string(
            _normalize_platform_value(value), f"{kind} member"
        )
        entry = grouped.setdefault(
            member_id,
            _final_entry(
                category=4,
                member_id=member_id,
                contract_id=contract_id,
                facts={
                    "hash_relevant": hash_relevant,
                    "kind": kind,
                    "sites": [],
                },
            ),
        )
        entry["sites"].append(site)
    for entry in grouped.values():
        entry["sites"] = sorted(entry["sites"])
    return list(grouped.values())


def _derive_binding_final_entries(
    *,
    registry: dict[str, Any],
    comparison: dict[str, Any],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for document, schema_id in (
        (registry, _CAR_SCHEMA_ID),
        (comparison, _CAR_COMPARISON_SCHEMA_ID),
    ):
        identity = _document_identity(document)
        found: dict[tuple[str, str], list[str]] = {}

        def visit(node: Any, pointer: str) -> None:
            if not isinstance(node, dict) or set(node) != {"id", "digest"}:
                return
            binding_id = _normalize_platform_value(node["id"])
            if not isinstance(binding_id, str):
                return
            binding_id = binding_id.replace(
                "https://racecraft.dev/schemas/g56r-003/",
                "https://racecraft.dev/schemas/car-003/",
            )
            if not binding_id.startswith("https://racecraft.dev/schemas/car-003/"):
                return
            found.setdefault((binding_id, str(node["digest"])), []).append(pointer)

        _walk_json_pointer(document, "#", visit)
        for (bound_id, digest), sites in found.items():
            ordered = sorted(f"{identity}{site}" for site in sites)
            entries.append(
                _final_entry(
                    category=5,
                    member_id=ordered[0],
                    contract_id=schema_id,
                    facts={
                        "bound_id": bound_id,
                        "digest": digest,
                        "sites": ordered,
                    },
                )
            )
    return entries


def _adaptive_control_position(registry: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    for index, control in enumerate(_require_sequence(registry.get("controls"), "controls")):
        control_map = _require_mapping(control, f"controls[{index}]")
        if control_map.get("control_kind") == "adaptive":
            return index, control_map
    raise ControlContractError("the Codex registry declares no adaptive control")


def _derive_registry_final_numeric_entries(
    *,
    registry: dict[str, Any],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    registry_id = _normalize_platform_value(registry.get("registry_id"))
    if not isinstance(registry_id, str):
        raise ControlContractError("registry_id cannot be mapped into the CAR namespace")

    adaptive_index, adaptive_control = _adaptive_control_position(registry)
    adaptive = _require_mapping(adaptive_control.get("adaptive"), "adaptive")
    threshold_id = (
        f"{registry_id}#/controls/{adaptive_index}"
        "/adaptive/de_escalation_clean_pass_threshold"
    )
    entries.append(
        _final_entry(
            category=6,
            member_id=threshold_id,
            contract_id=_CAR_SCHEMA_ID,
            facts={
                "value": adaptive.get("de_escalation_clean_pass_threshold"),
                "unit": "clean objectives",
                "direction": "at_or_above",
            },
        )
    )

    smoke_bounds = _require_mapping(registry.get("smoke_bounds"), "smoke_bounds")

    def visit(node: Any, pointer: str) -> None:
        if isinstance(node, dict) and set(node) == {"value", "unit", "direction"}:
            member_id = f"{registry_id}#/smoke_bounds{pointer}"
            entries.append(
                _final_entry(
                    category=6,
                    member_id=member_id,
                    contract_id=_CAR_SCHEMA_ID,
                    facts={
                        "value": node["value"],
                        "unit": node["unit"],
                        "direction": node["direction"],
                    },
                )
            )
            return
        if isinstance(node, dict):
            for key in sorted(node):
                visit(node[key], f"{pointer}/{_json_pointer_token(key)}")

    visit(smoke_bounds, "")
    return entries


def _derive_comparison_final_numeric_entries(
    *,
    comparison: dict[str, Any],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    comparison_id = _normalize_platform_value(comparison.get("comparison_id"))
    if not isinstance(comparison_id, str):
        raise ControlContractError("comparison_id cannot be mapped into the CAR namespace")

    scalars = (
        (
            "#/confidence_method/alpha",
            comparison["confidence_method"]["alpha"],
            "probability",
            "at_or_below",
        ),
        (
            "#/confidence_method/confidence_level",
            comparison["confidence_method"]["confidence_level"],
            "probability",
            "at_or_above",
        ),
        (
            "#/multiplicity_position/family_wise_alpha",
            comparison["multiplicity_position"]["family_wise_alpha"],
            "probability",
            "at_or_below",
        ),
    )
    for pointer, value, unit, direction in scalars:
        entries.append(
            _final_entry(
                category=6,
                member_id=f"{comparison_id}{pointer}",
                contract_id=_CAR_COMPARISON_SCHEMA_ID,
                facts={"value": value, "unit": unit, "direction": direction},
            )
        )

    margin_map = _require_mapping(
        _require_mapping(comparison.get("dominance_rule"), "dominance_rule").get(
            "margin_map"
        ),
        "margin_map",
    )
    for dimension in sorted(margin_map):
        margin = _require_mapping(margin_map[dimension], f"margin_map[{dimension!r}]")
        entries.append(
            _final_entry(
                category=6,
                member_id=(
                    f"{comparison_id}#/dominance_rule/margin_map/"
                    f"{_json_pointer_token(dimension)}"
                ),
                contract_id=_CAR_COMPARISON_SCHEMA_ID,
                facts={
                    "value": margin.get("relative_margin"),
                    "unit": margin.get("unit"),
                    "direction": margin.get("direction"),
                    "class": margin.get("class"),
                },
            )
        )
    return entries


def _derive_mapped_final_handoff_members(
    *,
    codex_registry_schema_path: Path,
    codex_registry_instance_path: Path,
    codex_comparison_schema_path: Path,
    codex_comparison_instance_path: Path,
    codex_partition_instance_path: Path,
) -> list[dict[str, Any]]:
    registry_schema = _load_json(codex_registry_schema_path)
    comparison_schema = _load_json(codex_comparison_schema_path)
    registry = _validate_codex_registry_reconciliation_sources(
        schema_path=codex_registry_schema_path,
        instance_path=codex_registry_instance_path,
    )
    comparison = _validate_comparison_for_reconciliation_derivation(
        schema_path=codex_comparison_schema_path,
        instance_path=codex_comparison_instance_path,
    )
    partition_entries = load_partition_entries(codex_partition_instance_path)
    normalized_registry = _require_mapping(
        _normalize_platform_value(registry), "normalized registry"
    )
    normalized_comparison = _require_mapping(
        _normalize_platform_value(comparison), "normalized comparison"
    )
    normalized_partition_entries = [
        _require_mapping(
            _normalize_platform_value(entry), "normalized partition entry"
        )
        for entry in partition_entries
    ]

    actual = _derive_schema_final_entries(
        schemas=[registry_schema, comparison_schema],
    )
    actual.extend(
        _derive_identifier_final_entries(
            registry=normalized_registry,
            comparison=normalized_comparison,
            partition_entries=normalized_partition_entries,
        )
    )
    actual.extend(
        _derive_binding_final_entries(
            registry=normalized_registry,
            comparison=normalized_comparison,
        )
    )
    actual.extend(_derive_registry_final_numeric_entries(registry=registry))
    actual.extend(
        _derive_comparison_final_numeric_entries(
            comparison=comparison,
        )
    )
    return actual


def _validate_comparison_reconciliation_sources(
    *, schema_path: Path, instance_path: Path
) -> dict[str, Any]:
    instance = _validate_comparison_for_reconciliation_derivation(
        schema_path=schema_path,
        instance_path=instance_path,
    )
    if instance != _codex_control_comparison.load_comparison():
        raise ControlContractError("comparison fixture authority drift")
    return {
        "comparison_id": instance["comparison_id"],
        "schema_version": instance["schema_version"],
    }


def _verified_source_artifacts(paths: list[Path]) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for path in paths:
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise ControlContractError(f"cannot hash reconciliation source {path}: {exc}") from exc
        evidence.append(
            {
                "path": _repo_relative_path(path),
                "sha256": f"sha256:{digest}",
            }
        )
    return evidence


def reconcile_final_twin_handoff(
    *,
    car_handoff_path: Path,
    codex_registry_schema_path: Path,
    codex_registry_instance_path: Path,
    codex_comparison_schema_path: Path,
    codex_comparison_instance_path: Path,
    codex_partition_instance_path: Path,
) -> dict[str, Any]:
    """Compose registry, comparison, and partition mirrors into the final report."""

    expected_entries, expected_divergences = _load_handoff_membership(
        _FROZEN_CAR_HANDOFF_PATH
    )
    _validate_handoff_obligations(expected_entries)
    _, actual_divergences = _load_handoff_membership(car_handoff_path)
    _assert_single_sanctioned_divergence(
        expected_divergences=expected_divergences,
        actual_divergences=actual_divergences,
    )
    actual_entries = _derive_mapped_final_handoff_members(
        codex_registry_schema_path=codex_registry_schema_path,
        codex_registry_instance_path=codex_registry_instance_path,
        codex_comparison_schema_path=codex_comparison_schema_path,
        codex_comparison_instance_path=codex_comparison_instance_path,
        codex_partition_instance_path=codex_partition_instance_path,
    )
    differences = _diff_final_handoff_members(
        expected_entries=expected_entries,
        actual_entries=actual_entries,
    )
    final_buckets = _final_reconciliation_buckets(
        differences,
        expected_entries=expected_entries,
        actual_entries=actual_entries,
    )
    _raise_on_final_reconciliation_differences(
        {
            "differences": differences,
            **final_buckets,
        }
    )
    registry_report = validate_car_004_twin_mirror(
        car_handoff_path=car_handoff_path,
        codex_registry_schema_path=codex_registry_schema_path,
        codex_registry_instance_path=codex_registry_instance_path,
    )
    comparison_report = _validate_comparison_reconciliation_sources(
        schema_path=codex_comparison_schema_path,
        instance_path=codex_comparison_instance_path,
    )
    partition_report = partition_owned_mirror_members(
        handoff_path=car_handoff_path,
        fixture_path=codex_partition_instance_path,
    )
    source_evidence = _verified_source_artifacts(
        [
            codex_registry_schema_path,
            codex_registry_instance_path,
            codex_comparison_schema_path,
            codex_comparison_instance_path,
            codex_partition_instance_path,
        ]
    )

    report = {
        "artifact_groups": ["registry", "comparison", "partition"],
        "compared_categories": sorted({entry["category"] for entry in actual_entries}),
        "comparison_contract": {
            "fields_by_category": {
                str(category): list(fields)
                for category, fields in _FINAL_COMPARE_FIELDS.items()
            },
            "fields_not_cross_platform_compared": list(
                _FIELDS_NOT_CROSS_PLATFORM_COMPARED
            ),
        },
        "differences": differences,
        "sanctioned_divergences": copy.deepcopy(
            registry_report["sanctioned_divergences"]
        ),
        "source_paths": [item["path"] for item in source_evidence],
        "verified_source_artifacts": source_evidence,
        "verified_platform_bindings": [
            {
                field: copy.deepcopy(entry[field])
                for field in ("member_id", "bound_id", "digest", "sites")
            }
            for entry in actual_entries
            if entry["category"] == 5
        ],
        "registry": {
            "preserved_literals": copy.deepcopy(registry_report["preserved_literals"])
        },
        "comparison": comparison_report,
        "partition": partition_report,
    }
    for bucket in _FINAL_RECONCILIATION_BUCKETS:
        report[bucket] = final_buckets[bucket]
    _raise_on_final_reconciliation_differences(report)
    return report


def seed_final_twin_reconciliation(
    report: dict[str, Any], mutation: str
) -> dict[str, Any]:
    """Return a copied report with one deterministic reconciliation fault."""

    if mutation not in _FINAL_RECONCILIATION_BUCKETS:
        raise ControlContractError(f"unknown reconciliation mutation {mutation!r}")
    seeded = copy.deepcopy(report)
    marker = {
        "member_id": f"seeded-{mutation}-member",
        "mutation": mutation,
    }
    for bucket in _FINAL_RECONCILIATION_BUCKETS:
        seeded.setdefault(bucket, [])
    seeded[mutation].append(copy.deepcopy(marker))

    differences = seeded.setdefault(
        "differences",
        {
            "missing_from_record": [],
            "absent_from_artifacts": [],
            "mismatched": [],
            "duplicated": [],
        },
    )
    differences.setdefault(
        _DIFFERENCE_BUCKET_BY_RECONCILIATION_MUTATION[mutation], []
    ).append(marker)
    return seeded
