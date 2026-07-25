#!/usr/bin/env python3
"""G56R-003 qualification assignment validation for score eligibility."""

from __future__ import annotations

import copy
from collections.abc import Mapping

if __package__:
    from .treatment_trace_model import *
    from .treatment_trace_bundle import _validate_treatment_bundle
else:
    from treatment_trace_model import *
    from treatment_trace_bundle import _validate_treatment_bundle


QUALIFICATION_SCHEMA_VERSION = "1.0.0"
QUALIFICATION_OWNER_SPEC_ID = "G56R-003"
TREATMENT_OWNER_SPEC_ID = "G56R-002"
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
    derived_eligible = delivery_status == "delivered"
    expected_reasons = [] if derived_eligible else [f"delivery_{delivery_status}"]
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


def validate_qualification_bundle(
    bundle: object, *, schema_path: Path = SCHEMA_PATH, manifest_path: Path = MANIFEST_PATH,
    trusted_qualification_evidence: Mapping[str, dict] | None = None,
) -> dict:
    """Validate G56R-003 score qualification against an existing G56R-002 treatment bundle."""
    _validate_resource_bounds(bundle)
    _validate_retained_strings(bundle, "qualification bundle")
    value = _closed(
        copy.deepcopy(bundle),
        {
            "schema_version", "owner_spec_id", "treatment_bundle", "materializations",
            "qualification_assignments", "qualification_traces",
        },
        "qualification bundle",
    )
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
    value["treatment_bundle"] = treatment
    value["materializations"] = validated_materializations
    value["qualification_assignments"] = validated_assignments
    value["qualification_traces"] = validated_wrappers
    return value


__all__ = [
    "DELIVERY_STATUSES",
    "MANDATORY_OBSERVATION_FIELDS",
    "MATERIALIZATION_FIELDS",
    "NULL_ONLY_OBSERVATION_FIELDS",
    "QUALIFICATION_OBSERVATION_FIELDS",
    "QUALIFICATION_OWNER_SPEC_ID",
    "QUALIFICATION_SCHEMA_VERSION",
    "TREATMENT_OWNER_SPEC_ID",
    "validate_qualification_bundle",
]
