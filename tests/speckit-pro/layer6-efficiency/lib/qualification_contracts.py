#!/usr/bin/env python3
"""G56R-003 qualification assignment validation for score eligibility."""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Mapping

if __package__:
    from .treatment_trace_model import *
    from .treatment_trace_bundle import _validate_treatment_bundle
else:
    from treatment_trace_model import *
    from treatment_trace_bundle import _validate_treatment_bundle


QUALIFICATION_SCHEMA_VERSION = "1.0.0"
COMPARISON_ASSIGNMENT_SCHEMA_VERSION = "comparison-assignment.v1"
QUALIFICATION_OWNER_SPEC_ID = "G56R-003"
TREATMENT_OWNER_SPEC_ID = "G56R-002"
PARTITION_TYPES = frozenset({
    "calibration",
    "screening",
    "selection",
    "cohort_lock",
    "integrated_confirmation",
})
MATERIALIZATION_FIELDS = frozenset({
    "materialization_id",
    "owner_spec_id",
    "candidate_route_id",
    "agent_contract_id",
    "requested_model",
    "requested_effort",
    "destination_bytes_digest",
    "instruction_digest",
    "configuration_digest",
})
QUALIFICATION_OBSERVATION_FIELDS = (
    "assignment.requested_model",
    "assignment.requested_effort",
    "installed.agent_bytes_digest",
    "configured.route_proof",
    "delivery.reroute_monitoring",
    "delivery.status",
    "qualification.notes",
)
MANDATORY_OBSERVATION_FIELDS = frozenset(
    field for field in QUALIFICATION_OBSERVATION_FIELDS if field != "qualification.notes"
)
NULL_ONLY_OBSERVATION_FIELDS = frozenset({"qualification.notes"})
DELIVERY_STATUSES = frozenset({
    "delivered",
    "monitoring_incomplete",
    "service_rerouted",
    "misdelivered",
    "ambiguous",
    "unapproved",
    "unidentifiable",
})
DELIVERY_FAILURE_BY_CODE = {
    "agent_mismatch": "misdelivered",
    "reroute_ambiguous": "ambiguous",
    "reroute_unapproved": "unapproved",
    "reroute_unidentifiable": "unidentifiable",
}
SUCCESSOR_FREEZE_BINDING_FIELDS = frozenset({
    "candidate_freeze_id",
    "runtime_capability_snapshot_id",
    "catalog_capture_digest",
    "included_candidate_route_id",
    "tuple_decision_digest",
})
BINDING_FIELDS = frozenset({"id", "digest"})
BINDING_AUTHORITY_FIELDS = frozenset({
    "partition_binding",
    "candidate_freeze_binding",
    "runtime_snapshot_binding",
    "corpus_binding",
    "workload_manifest_binding",
    "experiment_policy_binding",
    "calibration_protocol_binding",
    "role_binding",
    "fixture_binding",
    "objective_binding",
    "task_binding",
    "fixture_partition_binding",
    "candidate_route_binding",
    "candidate_agent_contract_binding",
    "candidate_materialization_binding",
    "candidate_route_resolution_binding",
    "candidate_instruction_digest",
    "candidate_configuration_digest",
    "comparator_route_binding",
    "comparator_agent_contract_binding",
    "comparator_materialization_binding",
    "comparator_route_resolution_binding",
    "comparator_instruction_digest",
    "comparator_configuration_digest",
})
COMPARISON_ASSIGNMENT_BUNDLE_FIELDS = frozenset({
    "schema_version",
    "owner_spec_id",
    "partition_registry",
    "binding_authorities",
    "experiment_policy",
    "calibration_protocol",
    "executed_pair_snapshots",
    "refresh_invalidations",
})
CALIBRATION_PROTOCOL_FIELDS = frozenset({
    "schema_version",
    "calibration_protocol_id",
    "calibration_protocol_version",
    "calibration_protocol_digest",
    "status",
    "partition_binding",
    "candidate_freeze_binding",
    "runtime_snapshot_binding",
    "pinned_client_binding",
    "corpus_binding",
    "workload_manifest_binding",
    "scorer_bindings",
    "rubric_binding",
    "adjudicator_binding",
    "cache_policy_binding",
    "frozen_at",
    "independent_review_binding",
})
PARTITION_BINDING_FIELDS = frozenset({
    "partition_id",
    "partition_type",
    "partition_digest",
    "qualification_eligible",
})
ROUTE_ASSIGNMENT_FIELDS = frozenset({
    "assignment_id",
    "route_binding",
    "agent_contract_binding",
    "materialization_binding",
    "route_resolution_binding",
})
INSTRUCTION_BINDING_FIELDS = frozenset({
    "candidate_instruction_digest",
    "comparator_instruction_digest",
    "candidate_configuration_digest",
    "comparator_configuration_digest",
})
CAPABILITY_BINDING_FIELDS = frozenset({
    "runtime_snapshot_binding",
    "candidate_freeze_binding",
})
COMPARISON_SET_FIELDS = frozenset({
    "comparison_set_id",
    "comparison_set_digest",
    "partition_binding",
    "assignment_pairs",
})
ASSIGNMENT_PAIR_FIELDS = frozenset({
    "assignment_pair_id",
    "assignment_pair_digest",
    "binding_state",
    "pre_execution_frozen_at",
    "role_binding",
    "fixture_binding",
    "objective_binding",
    "task_binding",
    "candidate_assignment",
    "comparator_assignment",
    "instruction_binding",
    "capability_binding",
    "experiment_policy_binding",
    "calibration_protocol_binding",
    "assigned_order",
    "invalidation_policy",
})
REFRESH_INVALIDATION_FIELDS = frozenset({
    "invalidation_id",
    "target_binding",
    "replacement_binding",
    "reason",
    "detected_at",
})
EXECUTED_PAIR_SNAPSHOT_FIELDS = frozenset({
    "assignment_pair_id",
    "assignment_pair_digest",
    "candidate_assignment_id",
    "comparator_assignment_id",
    "executed_at",
})
QUALIFICATION_BUNDLE_FIELDS = frozenset({
    "schema_version",
    "owner_spec_id",
    "treatment_bundle",
    "materializations",
    "qualification_assignments",
    "qualification_traces",
})
OPTIONAL_QUALIFICATION_BUNDLE_FIELDS = frozenset({"successor_freeze_binding"})


def _validate_binding(value: object, label: str) -> dict:
    row = _closed(value, set(BINDING_FIELDS), label)
    _text(row["id"], f"{label} ID")
    _digest(row["digest"], f"{label} digest")
    return row


def _validate_partition_binding(value: object, label: str, *, require_calibration: bool = True) -> dict:
    row = _closed(value, set(PARTITION_BINDING_FIELDS), label)
    _text(row["partition_id"], f"{label} partition ID")
    partition_type = row["partition_type"]
    if partition_type not in PARTITION_TYPES:
        raise ValueError(f"{label} partition type is outside the closed inventory")
    _digest(row["partition_digest"], f"{label} partition digest")
    if not isinstance(row["qualification_eligible"], bool):
        raise ValueError(f"{label} qualification eligibility must be boolean")
    if require_calibration and (
        partition_type != "calibration" or row["qualification_eligible"] is not False
    ):
        raise ValueError("G56R-003 comparison assignments may only use calibration partitions")
    return row


def _expected_object_binding(value: Mapping[str, object], id_field: str, digest_field: str, label: str) -> dict:
    return {
        "id": _digest(value.get(id_field), f"{label} ID"),
        "digest": _digest(value.get(digest_field), f"{label} digest"),
    }


def _require_equal(left: object, right: object, label: str) -> None:
    if left != right:
        raise ValueError(f"{label} does not match its immutable authority")


def _validated_refresh_invalidations(value: object) -> list[dict]:
    if not isinstance(value, list):
        raise ValueError("refresh invalidations must be an array")
    rows: list[dict] = []
    seen: set[str] = set()
    for raw in value:
        row = _closed(raw, set(REFRESH_INVALIDATION_FIELDS), "refresh invalidation")
        _digest(row["invalidation_id"], "refresh invalidation ID")
        row["target_binding"] = _validate_binding(row["target_binding"], "refresh invalidation target")
        row["replacement_binding"] = _validate_binding(row["replacement_binding"], "refresh invalidation replacement")
        if row["target_binding"] == row["replacement_binding"]:
            raise ValueError("refresh invalidation replacement must differ from target")
        if row["reason"] not in {
            "capability_refresh",
            "runtime_snapshot_refresh",
            "route_refresh",
            "materialization_refresh",
            "route_resolution_refresh",
            "policy_refresh",
            "protocol_refresh",
            "partition_refresh",
        }:
            raise ValueError("refresh invalidation reason is outside the closed inventory")
        _timestamp(row["detected_at"], "refresh invalidation timestamp")
        if row["invalidation_id"] != content_id(row, "invalidation_id"):
            raise ValueError("refresh invalidation ID is not content addressed")
        if row["invalidation_id"] in seen:
            raise ValueError("duplicate refresh invalidation ID")
        seen.add(row["invalidation_id"])
        rows.append(row)
    return rows


def _binding_is_current_or_invalidated(
    frozen: dict,
    current: dict,
    invalidations: list[dict],
    label: str,
) -> None:
    if frozen == current:
        return
    if any(
        item["target_binding"] == frozen and item["replacement_binding"] == current
        for item in invalidations
    ):
        return
    raise ValueError(f"{label} is stale without an additive invalidation")


def _validate_binding_authorities(value: object, registry_partition: dict) -> dict:
    row = _closed(value, set(BINDING_AUTHORITY_FIELDS), "comparison assignment binding authorities")
    row["partition_binding"] = _validate_partition_binding(
        row["partition_binding"], "authority partition binding",
    )
    row["fixture_partition_binding"] = _validate_partition_binding(
        row["fixture_partition_binding"], "fixture authority partition binding",
    )
    _require_equal(row["partition_binding"], registry_partition, "authority partition binding")
    _require_equal(row["fixture_partition_binding"], registry_partition, "fixture partition binding")
    for field in (
        "candidate_freeze_binding",
        "runtime_snapshot_binding",
        "corpus_binding",
        "workload_manifest_binding",
        "experiment_policy_binding",
        "calibration_protocol_binding",
        "role_binding",
        "fixture_binding",
        "objective_binding",
        "task_binding",
        "candidate_route_binding",
        "candidate_agent_contract_binding",
        "candidate_materialization_binding",
        "candidate_route_resolution_binding",
        "comparator_route_binding",
        "comparator_agent_contract_binding",
        "comparator_materialization_binding",
        "comparator_route_resolution_binding",
    ):
        row[field] = _validate_binding(row[field], f"authority {field}")
    for field in (
        "candidate_instruction_digest",
        "candidate_configuration_digest",
        "comparator_instruction_digest",
        "comparator_configuration_digest",
    ):
        _digest(row[field], f"authority {field}")
    return row


def _validate_route_assignment(value: object, authorities: dict, prefix: str) -> dict:
    row = _closed(value, set(ROUTE_ASSIGNMENT_FIELDS), f"{prefix} assignment")
    _digest(row["assignment_id"], f"{prefix} assignment ID")
    for field in (
        "route_binding",
        "agent_contract_binding",
        "materialization_binding",
        "route_resolution_binding",
    ):
        row[field] = _validate_binding(row[field], f"{prefix} {field}")
    expected = {
        "route_binding": authorities[f"{prefix}_route_binding"],
        "agent_contract_binding": authorities[f"{prefix}_agent_contract_binding"],
        "materialization_binding": authorities[f"{prefix}_materialization_binding"],
        "route_resolution_binding": authorities[f"{prefix}_route_resolution_binding"],
    }
    for field, expected_value in expected.items():
        _require_equal(row[field], expected_value, f"{prefix} {field}")
    if row["assignment_id"] != content_id(row, "assignment_id"):
        raise ValueError(f"{prefix} assignment ID is not content addressed")
    return row


def _validate_assignment_pair(
    value: object,
    authorities: dict,
    invalidations: list[dict],
    policy_binding: dict,
    protocol_binding: dict,
) -> dict:
    row = _closed(value, set(ASSIGNMENT_PAIR_FIELDS), "comparison assignment pair")
    _digest(row["assignment_pair_id"], "comparison assignment pair ID")
    _digest(row["assignment_pair_digest"], "comparison assignment pair digest")
    if row["binding_state"] != "pre_execution_frozen":
        raise ValueError("comparison assignment pair must be frozen before execution")
    _timestamp(row["pre_execution_frozen_at"], "comparison assignment freeze timestamp")
    for field in ("role_binding", "fixture_binding", "objective_binding", "task_binding"):
        row[field] = _validate_binding(row[field], f"comparison {field}")
        _require_equal(row[field], authorities[field], f"comparison {field}")
    row["candidate_assignment"] = _validate_route_assignment(
        row["candidate_assignment"], authorities, "candidate",
    )
    row["comparator_assignment"] = _validate_route_assignment(
        row["comparator_assignment"], authorities, "comparator",
    )
    row["instruction_binding"] = _closed(
        row["instruction_binding"], set(INSTRUCTION_BINDING_FIELDS), "comparison instruction binding",
    )
    for field in INSTRUCTION_BINDING_FIELDS:
        _digest(row["instruction_binding"][field], f"comparison {field}")
        _require_equal(
            row["instruction_binding"][field],
            authorities[field],
            f"comparison {field}",
        )
    capability = _closed(
        row["capability_binding"], set(CAPABILITY_BINDING_FIELDS), "comparison capability binding",
    )
    capability["runtime_snapshot_binding"] = _validate_binding(
        capability["runtime_snapshot_binding"], "comparison runtime snapshot binding",
    )
    capability["candidate_freeze_binding"] = _validate_binding(
        capability["candidate_freeze_binding"], "comparison candidate freeze binding",
    )
    _binding_is_current_or_invalidated(
        capability["runtime_snapshot_binding"],
        authorities["runtime_snapshot_binding"],
        invalidations,
        "runtime snapshot binding",
    )
    _binding_is_current_or_invalidated(
        capability["candidate_freeze_binding"],
        authorities["candidate_freeze_binding"],
        invalidations,
        "candidate freeze binding",
    )
    row["capability_binding"] = capability
    row["experiment_policy_binding"] = _validate_binding(
        row["experiment_policy_binding"], "comparison experiment policy binding",
    )
    row["calibration_protocol_binding"] = _validate_binding(
        row["calibration_protocol_binding"],
        "comparison calibration protocol binding",
    )
    _require_equal(row["experiment_policy_binding"], policy_binding, "comparison policy binding")
    _require_equal(
        row["calibration_protocol_binding"],
        protocol_binding,
        "comparison calibration protocol binding",
    )
    if sorted(row["assigned_order"]) != ["candidate", "comparator"]:
        raise ValueError("comparison assigned order must contain each treatment arm exactly once")
    if row["invalidation_policy"] != "additive_only":
        raise ValueError("comparison invalidation policy must be additive only")
    if row["assignment_pair_digest"] != content_id(row, "assignment_pair_digest"):
        raise ValueError("comparison assignment pair digest is not content addressed")
    return row


def _validate_comparison_sets(
    value: object,
    registry_partition: dict,
    authorities: dict,
    invalidations: list[dict],
    policy_binding: dict,
    protocol_binding: dict,
    comparison_policy: dict,
) -> list[dict]:
    if not isinstance(value, list) or not value:
        raise ValueError("comparison sets must be a non-empty array")
    rows: list[dict] = []
    seen: set[str] = set()
    for raw in value:
        row = _closed(raw, set(COMPARISON_SET_FIELDS), "comparison set")
        _digest(row["comparison_set_id"], "comparison set ID")
        _digest(row["comparison_set_digest"], "comparison set digest")
        row["partition_binding"] = _validate_partition_binding(
            row["partition_binding"], "comparison set partition binding",
        )
        _require_equal(row["partition_binding"], registry_partition, "comparison set partition binding")
        row["assignment_pairs"] = [
            _validate_assignment_pair(
                item,
                authorities,
                invalidations,
                policy_binding,
                protocol_binding,
            )
            for item in row["assignment_pairs"]
        ]
        ordered_pairs = sorted(
            row["assignment_pairs"],
            key=lambda item: hashlib.sha256(
                (
                    comparison_policy["randomization_seed_digest"]
                    + "|"
                    + item["assignment_pair_id"]
                ).encode("utf-8")
            ).digest(),
        )
        start_candidate = (
            hashlib.sha256(
                comparison_policy["randomization_seed_digest"].encode("utf-8")
            ).digest()[0]
            % 2
            == 0
        )
        for index, pair in enumerate(ordered_pairs):
            if comparison_policy["order_rule"] == "seeded_balanced":
                candidate_first = start_candidate if index % 2 == 0 else not start_candidate
            else:
                candidate_first = (
                    hashlib.sha256(
                        (
                            comparison_policy["randomization_seed_digest"]
                            + "|"
                            + pair["assignment_pair_id"]
                        ).encode("utf-8")
                    ).digest()[0]
                    % 2
                    == 0
                )
            expected_order = (
                ["candidate", "comparator"]
                if candidate_first
                else ["comparator", "candidate"]
            )
            if pair["assigned_order"] != expected_order:
                raise ValueError("comparison assigned order does not match the frozen seed")
        if row["comparison_set_digest"] != content_id(row, "comparison_set_digest"):
            raise ValueError("comparison set digest is not content addressed")
        if row["comparison_set_id"] in seen:
            raise ValueError("duplicate comparison set ID")
        seen.add(row["comparison_set_id"])
        rows.append(row)
    return rows


def _validate_calibration_protocol_for_assignment(
    value: object,
    authorities: dict,
    registry_partition: dict,
    invalidations: list[dict],
) -> dict:
    row = _closed(
        value,
        set(CALIBRATION_PROTOCOL_FIELDS),
        "calibration protocol",
    )
    if (
        row["schema_version"] != "calibration-protocol.v1"
        or row["status"] != "frozen_before_calibration"
    ):
        raise ValueError("calibration protocol must be frozen before assignment validation")
    expected_digest = digest({
        key: item
        for key, item in row.items()
        if key not in {"calibration_protocol_id", "calibration_protocol_digest"}
    })
    if row["calibration_protocol_digest"] != expected_digest:
        raise ValueError("calibration protocol digest does not match frozen content")
    if row["calibration_protocol_id"] != content_id(
        row,
        "calibration_protocol_id",
    ):
        raise ValueError("calibration protocol ID does not match frozen content")
    protocol_binding = _expected_object_binding(
        row,
        "calibration_protocol_id",
        "calibration_protocol_digest",
        "calibration protocol",
    )
    _require_equal(
        protocol_binding,
        authorities["calibration_protocol_binding"],
        "calibration protocol binding",
    )
    partition = _validate_partition_binding(
        row["partition_binding"],
        "calibration protocol partition",
    )
    _require_equal(
        partition,
        registry_partition,
        "calibration protocol partition binding",
    )
    for field in ("candidate_freeze_binding", "runtime_snapshot_binding"):
        binding = _validate_binding(
            row[field],
            f"calibration protocol {field}",
        )
        _binding_is_current_or_invalidated(
            binding,
            authorities[field],
            invalidations,
            f"calibration protocol {field}",
        )
        row[field] = binding
    for field in ("corpus_binding", "workload_manifest_binding"):
        row[field] = _validate_binding(row[field], f"calibration protocol {field}")
        _require_equal(
            row[field],
            authorities[field],
            f"calibration protocol {field}",
        )
    for field in (
        "pinned_client_binding",
        "rubric_binding",
        "adjudicator_binding",
        "cache_policy_binding",
        "independent_review_binding",
    ):
        row[field] = _validate_binding(row[field], f"calibration protocol {field}")
    if not isinstance(row["scorer_bindings"], list) or len(row["scorer_bindings"]) != 2:
        raise ValueError("calibration protocol must bind exactly two scorers")
    row["scorer_bindings"] = [
        _validate_binding(item, "calibration protocol scorer binding")
        for item in row["scorer_bindings"]
    ]
    if len({item["id"] for item in row["scorer_bindings"]}) != 2:
        raise ValueError("calibration protocol scorer bindings must be distinct")
    _text(row["calibration_protocol_version"], "calibration protocol version")
    _timestamp(row["frozen_at"], "calibration protocol freeze timestamp")
    return row


def _validate_executed_pair_snapshots(value: object, pairs: Mapping[str, dict]) -> list[dict]:
    if not isinstance(value, list):
        raise ValueError("executed pair snapshots must be an array")
    rows: list[dict] = []
    seen: set[str] = set()
    for raw in value:
        row = _closed(raw, set(EXECUTED_PAIR_SNAPSHOT_FIELDS), "executed pair snapshot")
        pair_id = _digest(row["assignment_pair_id"], "executed pair snapshot pair ID")
        _digest(row["assignment_pair_digest"], "executed pair snapshot pair digest")
        _digest(row["candidate_assignment_id"], "executed candidate assignment ID")
        _digest(row["comparator_assignment_id"], "executed comparator assignment ID")
        _timestamp(row["executed_at"], "executed pair snapshot timestamp")
        if pair_id not in pairs:
            raise ValueError("executed pair snapshot references an unknown pair")
        pair = pairs[pair_id]
        if (
            row["assignment_pair_digest"] != pair["assignment_pair_digest"]
            or row["candidate_assignment_id"] != pair["candidate_assignment"]["assignment_id"]
            or row["comparator_assignment_id"] != pair["comparator_assignment"]["assignment_id"]
        ):
            raise ValueError("executed assignment pair cannot be rebound after execution")
        if pair_id in seen:
            raise ValueError("duplicate executed pair snapshot")
        seen.add(pair_id)
        rows.append(row)
    return rows


def _validate_experiment_policy_for_assignment(
    value: object,
    calibration_protocol: dict,
    registry_partition: dict,
    authorities: dict,
    invalidations: list[dict],
) -> dict:
    if not isinstance(value, dict):
        raise ValueError("experiment policy must be an object")
    if value.get("schema_version") != "experiment-policy.v1":
        raise ValueError("experiment policy schema version is unsupported")
    policy_binding = _expected_object_binding(
        value, "experiment_policy_id", "policy_digest", "experiment policy",
    )
    _require_equal(policy_binding, authorities["experiment_policy_binding"], "experiment policy binding")
    protocol_binding = _expected_object_binding(
        calibration_protocol,
        "calibration_protocol_id",
        "calibration_protocol_digest",
        "calibration protocol",
    )
    _require_equal(
        protocol_binding,
        authorities["calibration_protocol_binding"],
        "policy calibration protocol authority",
    )
    partition = _validate_partition_binding(
        value.get("partition_binding"), "experiment policy partition binding",
    )
    _require_equal(partition, registry_partition, "experiment policy partition binding")
    candidate_freeze = _validate_binding(
        value.get("candidate_freeze_binding"), "experiment policy candidate freeze binding",
    )
    _binding_is_current_or_invalidated(
        candidate_freeze, authorities["candidate_freeze_binding"], invalidations,
        "experiment policy candidate freeze binding",
    )
    for field in ("corpus_binding", "workload_manifest_binding"):
        _require_equal(
            _validate_binding(value.get(field), f"experiment policy {field}"),
            authorities[field],
            f"experiment policy {field}",
        )
    _require_equal(
        _validate_binding(
            value.get("calibration_protocol_binding"),
            "experiment policy calibration protocol binding",
        ),
        protocol_binding,
        "experiment policy calibration protocol binding",
    )
    policy = _closed(
        value.get("comparison_policy"),
        {
            "pair_before_execution",
            "comparison_set_generation",
            "order_rule",
            "randomization_seed_digest",
            "rebinding_policy",
        },
        "comparison policy",
    )
    if (
        policy["pair_before_execution"] is not True
        or policy["comparison_set_generation"] != "paired_by_role_fixture_task"
        or policy["rebinding_policy"] != "additive_invalidation_only"
    ):
        raise ValueError("comparison policy does not freeze pairs before execution")
    if policy["order_rule"] not in {"seeded_balanced", "seeded_random"}:
        raise ValueError("comparison order rule is invalid")
    _digest(policy["randomization_seed_digest"], "comparison randomization seed digest")
    value["comparison_sets"] = _validate_comparison_sets(
        value.get("comparison_sets"), registry_partition, authorities, invalidations,
        policy_binding, protocol_binding, policy,
    )
    return value


def validate_comparison_assignment_bundle(bundle: object) -> dict:
    """Validate immutable comparison assignments and calibration partition isolation."""
    _validate_resource_bounds(bundle)
    _validate_retained_strings(bundle, "comparison assignment bundle")
    value = copy.deepcopy(bundle)
    row = _closed(value, set(COMPARISON_ASSIGNMENT_BUNDLE_FIELDS), "comparison assignment bundle")
    if row["schema_version"] != COMPARISON_ASSIGNMENT_SCHEMA_VERSION:
        raise ValueError("comparison assignment schema version is unsupported")
    if row["owner_spec_id"] != QUALIFICATION_OWNER_SPEC_ID:
        raise ValueError("comparison assignment owner is invalid")
    if not isinstance(row["partition_registry"], list) or len(row["partition_registry"]) != 1:
        raise ValueError("comparison assignment must bind exactly one partition registry entry")
    registry_partition = _validate_partition_binding(
        row["partition_registry"][0], "partition registry entry",
    )
    invalidations = _validated_refresh_invalidations(row["refresh_invalidations"])
    authorities = _validate_binding_authorities(row["binding_authorities"], registry_partition)
    row["calibration_protocol"] = _validate_calibration_protocol_for_assignment(
        row["calibration_protocol"],
        authorities,
        registry_partition,
        invalidations,
    )
    row["experiment_policy"] = _validate_experiment_policy_for_assignment(
        row["experiment_policy"],
        row["calibration_protocol"],
        registry_partition,
        authorities,
        invalidations,
    )
    pairs = {
        pair["assignment_pair_id"]: pair
        for comparison_set in row["experiment_policy"]["comparison_sets"]
        for pair in comparison_set["assignment_pairs"]
    }
    if len(pairs) != sum(
        len(comparison_set["assignment_pairs"])
        for comparison_set in row["experiment_policy"]["comparison_sets"]
    ):
        raise ValueError("duplicate comparison assignment pair ID")
    row["executed_pair_snapshots"] = _validate_executed_pair_snapshots(
        row["executed_pair_snapshots"], pairs,
    )
    row["binding_authorities"] = authorities
    row["refresh_invalidations"] = invalidations
    row["partition_registry"] = [registry_partition]
    return row


def _validate_qualification_observations(value: object) -> dict[str, dict]:
    if not isinstance(value, list):
        raise ValueError("qualification observations must be an array")
    observations: dict[str, dict] = {}
    for raw in value:
        observation = _closed(
            raw,
            {"field_path", "observation_state", "value", "evidence_ref", "captured_at"},
            "qualification observation",
        )
        field = _text(observation["field_path"], "qualification observation field")
        if field in observations:
            raise ValueError("duplicate qualification observation field")
        if field not in QUALIFICATION_OBSERVATION_FIELDS:
            raise ValueError("qualification observation field is outside the closed inventory")
        state = observation["observation_state"]
        if state not in OBSERVATION_STATES:
            raise ValueError("qualification observation state is invalid")
        if field in NULL_ONLY_OBSERVATION_FIELDS:
            if state not in {"explicit_null", "missing", "unavailable", "undocumented"}:
                raise ValueError("null-only qualification observation uses an invalid state")
            if observation["value"] is not None:
                raise ValueError("null-only qualification observation cannot carry a value")
        else:
            if state != "observed_value":
                raise ValueError("mandatory qualification observation must be observed")
            if observation["value"] is None:
                raise ValueError("mandatory qualification observation cannot be null")
        if state == "observed_value":
            _evidence_ref(observation["evidence_ref"], "qualification observation evidence reference")
            _timestamp(observation["captured_at"], "qualification observation capture timestamp")
        else:
            _evidence_ref(
                observation["evidence_ref"], "qualification observation evidence reference",
                nullable=True,
            )
            _timestamp(
                observation["captured_at"], "qualification observation capture timestamp",
                nullable=True,
            )
        if state == "undocumented" and (
            observation["evidence_ref"] is not None or observation["captured_at"] is not None
        ):
            raise ValueError("undocumented qualification observation cannot claim evidence")
        observations[field] = observation
    if set(observations) != set(QUALIFICATION_OBSERVATION_FIELDS):
        raise ValueError("qualification observations do not cover the closed inventory")
    return observations


def _failure_codes(trace: dict) -> set[str]:
    return {
        item["failure_code"]
        for item in trace["treatment_failures"]
        if isinstance(item, dict) and isinstance(item.get("failure_code"), str)
    }


def _derived_delivery_status(trace: dict, observations: dict[str, dict]) -> str:
    codes = _failure_codes(trace)
    for failure_code, status in DELIVERY_FAILURE_BY_CODE.items():
        if failure_code in codes:
            return status
    if trace["service_reroute_events"]:
        return "service_rerouted"
    monitoring_observation = observations["delivery.reroute_monitoring"]
    proof = trace["configured_route_proof"]
    if (
        monitoring_observation["value"] is not True
        or proof is None
        or proof["reroute_monitoring_complete"] is not True
    ):
        return "monitoring_incomplete"
    if trace["delivery_canary"]["status"] != "passed":
        return "unidentifiable"
    return "delivered"


def _score_ineligibility_reasons(trace: dict, delivery_status: str) -> list[str]:
    if delivery_status != "delivered":
        return [f"delivery_{delivery_status}"]
    disposition = trace["treatment_disposition"]
    if disposition == "hard_fail":
        return ["treatment_hard_fail"]
    if disposition != "proven":
        return ["treatment_unknown"]
    if trace["disposition_reasons"] != [
        "configured_route_proof_and_complete_reroute_monitoring"
    ]:
        return ["treatment_profile_only"]
    return []


def _expected_route_proof(trace: dict) -> dict:
    proof = trace["configured_route_proof"]
    if proof is None:
        raise ValueError("configured route proof is required for qualification")
    return {
        "proof_id": proof["proof_id"],
        "candidate_route_id": proof["candidate_route_id"],
        "configuration_hash": proof["configuration_hash"],
    }


def _validate_materialization(value: object) -> dict:
    row = _closed(value, set(MATERIALIZATION_FIELDS), "materialization")
    _digest(row["materialization_id"], "materialization ID")
    if row["owner_spec_id"] != QUALIFICATION_OWNER_SPEC_ID:
        raise ValueError("materialization owner is invalid")
    for field in ("candidate_route_id", "agent_contract_id", "requested_model", "requested_effort"):
        _text(row[field], f"materialization {field}")
    for field in ("destination_bytes_digest", "instruction_digest", "configuration_digest"):
        _digest(row[field], f"materialization {field}")
    if row["materialization_id"] != content_id(row, "materialization_id"):
        raise ValueError("materialization ID is not content addressed")
    return row


def _validate_assignment(assignment: object, trace: dict, materialization: dict) -> dict:
    row = _closed(
        assignment,
        {
            "qualification_assignment_id", "owner_spec_id", "execution_trace_id",
            "candidate_route_id", "agent_contract_id", "requested_model", "requested_effort",
            "materialization_id", "installed_agent_bytes_digest", "configured_route_proof_id",
            "delivery_status", "score_eligible", "score_ineligibility_reasons", "observations",
        },
        "qualification assignment",
    )
    _digest(row["qualification_assignment_id"], "qualification assignment ID")
    _digest(row["materialization_id"], "qualification materialization ID")
    if row["owner_spec_id"] != QUALIFICATION_OWNER_SPEC_ID:
        raise ValueError("qualification assignment owner is invalid")
    if row["execution_trace_id"] != trace["objective_binding"]["execution_trace_id"]:
        raise ValueError("qualification assignment does not join its treatment trace")
    proof = _expected_route_proof(trace)
    if row["materialization_id"] != materialization["materialization_id"]:
        raise ValueError("qualification assignment does not join its materialization")
    expected = {
        "candidate_route_id": trace["objective_binding"]["candidate_route_id"],
        "agent_contract_id": trace["objective_binding"]["agent_contract_id"],
        "requested_model": trace["requested_model"],
        "requested_effort": trace["requested_effort"],
        "installed_agent_bytes_digest": materialization["destination_bytes_digest"],
        "configured_route_proof_id": proof["proof_id"],
    }
    for field, expected_value in expected.items():
        if row[field] != expected_value:
            raise ValueError(f"qualification {field} does not match the treatment trace")
    materialization_expected = {
        "candidate_route_id": trace["objective_binding"]["candidate_route_id"],
        "agent_contract_id": trace["objective_binding"]["agent_contract_id"],
        "requested_model": trace["requested_model"],
        "requested_effort": trace["requested_effort"],
        "instruction_digest": trace["instruction_hash"],
        "configuration_digest": proof["configuration_hash"],
    }
    for field, expected_value in materialization_expected.items():
        if materialization[field] != expected_value:
            raise ValueError(f"materialization {field} does not match the treatment trace")
    if row["delivery_status"] not in DELIVERY_STATUSES:
        raise ValueError("qualification delivery status is invalid")
    if not isinstance(row["score_eligible"], bool):
        raise ValueError("qualification score eligibility must be boolean")
    reasons = _strings(row["score_ineligibility_reasons"], "qualification score ineligibility reasons")
    observations = _validate_qualification_observations(row["observations"])
    expected_values = {
        "assignment.requested_model": row["requested_model"],
        "assignment.requested_effort": row["requested_effort"],
        "installed.agent_bytes_digest": row["installed_agent_bytes_digest"],
        "configured.route_proof": proof,
        "delivery.status": row["delivery_status"],
    }
    for field, expected_value in expected_values.items():
        if observations[field]["value"] != expected_value:
            raise ValueError(f"qualification {field} observation does not match its owner")
    if not isinstance(observations["delivery.reroute_monitoring"]["value"], bool):
        raise ValueError("qualification reroute monitoring observation must be boolean")
    delivery_status = _derived_delivery_status(trace, observations)
    if row["delivery_status"] != delivery_status:
        raise ValueError("qualification delivery status does not match the treatment trace")
    expected_reasons = _score_ineligibility_reasons(trace, delivery_status)
    derived_eligible = not expected_reasons
    if row["score_eligible"] != derived_eligible:
        raise ValueError("declared score eligibility does not match derived eligibility")
    if reasons != expected_reasons:
        raise ValueError("qualification score ineligibility reasons do not match derived eligibility")
    if row["qualification_assignment_id"] != content_id(row, "qualification_assignment_id"):
        raise ValueError("qualification assignment ID is not content addressed")
    return row


def _validate_trace_wrapper(wrapper: object, assignment: dict, trace: dict) -> dict:
    row = _closed(
        wrapper,
        {
            "qualification_trace_id", "owner_spec_id", "source_spec_id",
            "qualification_assignment_id", "execution_trace_id", "source_trace_digest",
        },
        "qualification trace wrapper",
    )
    _digest(row["qualification_trace_id"], "qualification trace ID")
    if row["owner_spec_id"] != QUALIFICATION_OWNER_SPEC_ID:
        raise ValueError("qualification trace owner is invalid")
    if row["source_spec_id"] != TREATMENT_OWNER_SPEC_ID:
        raise ValueError("qualification trace source spec is invalid")
    if (
        row["qualification_assignment_id"] != assignment["qualification_assignment_id"]
        or row["execution_trace_id"] != assignment["execution_trace_id"]
    ):
        raise ValueError("qualification trace wrapper has a conflicting assignment join")
    if row["execution_trace_id"] != trace["objective_binding"]["execution_trace_id"]:
        raise ValueError("qualification trace wrapper does not join its treatment trace")
    if row["source_trace_digest"] != digest(trace):
        raise ValueError("qualification trace wrapper does not bind exact source trace bytes")
    if row["qualification_trace_id"] != content_id(row, "qualification_trace_id"):
        raise ValueError("qualification trace ID is not content addressed")
    return row


def _validate_qualification_bundle_shape(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("qualification bundle must use its closed shape")
    keys = set(value)
    if (
        not QUALIFICATION_BUNDLE_FIELDS <= keys
        or keys - QUALIFICATION_BUNDLE_FIELDS - OPTIONAL_QUALIFICATION_BUNDLE_FIELDS
    ):
        raise ValueError("qualification bundle must use its closed shape")
    return value


def _validate_successor_freeze_binding(
    binding: object,
    successor_freeze: Mapping[str, object] | None,
    assignments: list[dict],
) -> dict:
    row = _closed(binding, set(SUCCESSOR_FREEZE_BINDING_FIELDS), "successor freeze binding")
    for field in (
        "candidate_freeze_id",
        "runtime_capability_snapshot_id",
        "catalog_capture_digest",
        "tuple_decision_digest",
    ):
        _digest(row[field], f"successor freeze binding {field}")
    _text(row["included_candidate_route_id"], "successor freeze binding included route")
    if successor_freeze is None:
        raise ValueError("successor freeze authority is required for successor freeze binding")
    if not isinstance(successor_freeze, Mapping):
        raise ValueError("successor freeze authority must be an object")
    if row["candidate_freeze_id"] != successor_freeze.get("candidate_freeze_id"):
        raise ValueError("successor freeze binding candidate freeze ID does not match authority")
    if row["runtime_capability_snapshot_id"] != successor_freeze.get("runtime_capability_snapshot_id"):
        raise ValueError("successor freeze binding runtime snapshot ID does not match authority")
    snapshot = successor_freeze.get("runtime_capability_snapshot")
    if not isinstance(snapshot, Mapping):
        raise ValueError("successor freeze authority is missing its runtime snapshot")
    if row["catalog_capture_digest"] != snapshot.get("catalog_capture_digest"):
        raise ValueError("successor freeze binding catalog digest does not match authority")
    included_routes = successor_freeze.get("included_candidate_route_ids")
    if not isinstance(included_routes, list) or row["included_candidate_route_id"] not in included_routes:
        raise ValueError("successor freeze binding route is not included by the successor freeze")
    assignment_route_ids = {item["candidate_route_id"] for item in assignments}
    if row["included_candidate_route_id"] not in assignment_route_ids:
        raise ValueError("successor freeze binding route does not join any qualification assignment")
    if any(route_id not in included_routes for route_id in assignment_route_ids):
        raise ValueError("qualification assignment route is not included by the successor freeze")
    decisions = successor_freeze.get("tuple_decisions")
    if not isinstance(decisions, list):
        raise ValueError("successor freeze authority is missing tuple decisions")
    matching_decisions = [
        item for item in decisions
        if isinstance(item, dict) and item.get("candidate_route_id") == row["included_candidate_route_id"]
    ]
    if len(matching_decisions) != 1 or matching_decisions[0].get("decision") != "included":
        raise ValueError("successor freeze binding route does not join one included tuple decision")
    if row["tuple_decision_digest"] != digest(matching_decisions[0]):
        raise ValueError("successor freeze binding tuple decision digest does not match authority")
    return row


def validate_qualification_bundle(
    bundle: object, *, schema_path: Path = SCHEMA_PATH, manifest_path: Path = MANIFEST_PATH,
    trusted_qualification_evidence: Mapping[str, dict] | None = None,
    successor_freeze: Mapping[str, object] | None = None,
) -> dict:
    """Validate G56R-003 score qualification against an existing G56R-002 treatment bundle."""
    _validate_resource_bounds(bundle)
    _validate_retained_strings(bundle, "qualification bundle")
    value = _validate_qualification_bundle_shape(copy.deepcopy(bundle))
    if value["schema_version"] != QUALIFICATION_SCHEMA_VERSION:
        raise ValueError("qualification schema version is unsupported")
    if value["owner_spec_id"] != QUALIFICATION_OWNER_SPEC_ID:
        raise ValueError("qualification bundle owner is invalid")
    treatment = _validate_treatment_bundle(
        value["treatment_bundle"], schema_path=schema_path,
        manifest=_read_manifest_snapshot(manifest_path),
        trusted_qualification_evidence=trusted_qualification_evidence,
    )
    traces_by_id = {
        trace["objective_binding"]["execution_trace_id"]: trace
        for trace in treatment["treatment_traces"]
    }
    materializations = value["materializations"]
    if not isinstance(materializations, list) or not materializations:
        raise ValueError("materializations must be a non-empty array")
    validated_materializations = [_validate_materialization(item) for item in materializations]
    materializations_by_id = {item["materialization_id"]: item for item in validated_materializations}
    if len(materializations_by_id) != len(validated_materializations):
        raise ValueError("duplicate materialization ID")
    assignments = value["qualification_assignments"]
    if not isinstance(assignments, list) or not assignments:
        raise ValueError("qualification assignments must be a non-empty array")
    if not isinstance(value["qualification_traces"], list):
        raise ValueError("qualification traces must be an array")
    raw_wrappers_by_assignment: dict[str, list[dict]] = {}
    for raw in value["qualification_traces"]:
        if not isinstance(raw, dict):
            raise ValueError("qualification trace wrapper must be an object")
        assignment_id = raw.get("qualification_assignment_id")
        if isinstance(assignment_id, str):
            raw_wrappers_by_assignment.setdefault(assignment_id, []).append(raw)
    seen_assignment_ids: set[str] = set()
    seen_trace_ids: set[str] = set()
    validated_assignments: list[dict] = []
    validated_wrappers: list[dict] = []
    for raw in assignments:
        if not isinstance(raw, dict):
            raise ValueError("qualification assignment must be an object")
        trace_id = raw.get("execution_trace_id")
        if trace_id not in traces_by_id:
            raise ValueError("qualification assignment references an unknown treatment trace")
        if trace_id in seen_trace_ids:
            raise ValueError("qualification assignments must be one-to-one with treatment traces")
        materialization_id = raw.get("materialization_id")
        if materialization_id not in materializations_by_id:
            raise ValueError("qualification assignment references an unknown materialization")
        trace = traces_by_id[trace_id]
        assignment = _validate_assignment(raw, trace, materializations_by_id[materialization_id])
        assignment_id = assignment["qualification_assignment_id"]
        if assignment_id in seen_assignment_ids:
            raise ValueError("duplicate qualification assignment ID")
        wrappers = raw_wrappers_by_assignment.get(assignment_id, [])
        if len(wrappers) != 1:
            raise ValueError("each qualification assignment must have exactly one trace wrapper")
        wrapper = _validate_trace_wrapper(wrappers[0], assignment, trace)
        seen_assignment_ids.add(assignment_id)
        seen_trace_ids.add(trace_id)
        validated_assignments.append(assignment)
        validated_wrappers.append(wrapper)
    if {item["materialization_id"] for item in validated_assignments} != set(materializations_by_id):
        raise ValueError("materialization registry contains a missing or orphan owner")
    if len(validated_wrappers) != len(value["qualification_traces"]):
        raise ValueError("qualification trace wrappers contain an orphan join")
    if seen_trace_ids != set(traces_by_id):
        raise ValueError("every treatment trace must have exactly one qualification assignment")
    if "successor_freeze_binding" in value:
        value["successor_freeze_binding"] = _validate_successor_freeze_binding(
            value["successor_freeze_binding"], successor_freeze, validated_assignments,
        )
    elif successor_freeze is not None:
        raise ValueError("successor freeze authority requires a successor freeze binding")
    value["treatment_bundle"] = treatment
    value["materializations"] = validated_materializations
    value["qualification_assignments"] = validated_assignments
    value["qualification_traces"] = validated_wrappers
    return value


__all__ = [
    "BINDING_AUTHORITY_FIELDS",
    "COMPARISON_ASSIGNMENT_SCHEMA_VERSION",
    "DELIVERY_STATUSES",
    "MANDATORY_OBSERVATION_FIELDS",
    "MATERIALIZATION_FIELDS",
    "NULL_ONLY_OBSERVATION_FIELDS",
    "PARTITION_TYPES",
    "QUALIFICATION_OBSERVATION_FIELDS",
    "QUALIFICATION_OWNER_SPEC_ID",
    "QUALIFICATION_SCHEMA_VERSION",
    "TREATMENT_OWNER_SPEC_ID",
    "validate_comparison_assignment_bundle",
    "validate_qualification_bundle",
]
