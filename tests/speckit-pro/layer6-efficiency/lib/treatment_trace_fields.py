#!/usr/bin/env python3
"""Treatment trace field, proof, assessment, and reroute validation."""

from __future__ import annotations

if __package__:
    from .treatment_trace_model import *
else:
    from treatment_trace_model import *

def _validate_tool_vector(value: object, label: str) -> dict:
    vector = _closed(value, {"skills", "mcp_servers", "tools"}, label)
    for field in ("skills", "mcp_servers", "tools"):
        _identifiers(vector[field], f"{label} {field}")
    return vector


def _validate_trace_structures(trace: dict) -> None:
    sandbox = _closed(trace["sandbox"], {"mode", "network_access", "writable_roots_digest"}, "sandbox")
    if sandbox["mode"] not in {"read_only", "workspace_write", "danger_full_access"} or not isinstance(sandbox["network_access"], bool):
        raise ValueError("sandbox values are invalid")
    _digest(sandbox["writable_roots_digest"], "sandbox writable roots")
    approvals = _closed(trace["approvals"], {"policy", "granted_action_ids"}, "approvals")
    if approvals["policy"] not in {"never", "on_request", "on_failure", "untrusted"}:
        raise ValueError("approval policy is invalid")
    _identifiers(approvals["granted_action_ids"], "approval action IDs")
    _text(trace["mutation_class"], "mutation class")
    _validate_tool_vector(trace["expected_skills_mcp_tools"], "expected skills MCP tools")
    _validate_tool_vector(trace["loaded_skills_mcp_tools"], "loaded skills MCP tools")
    parent = _closed(trace["parent_configuration"], {"parent_execution_trace_id", "configuration_hash"}, "parent configuration")
    _digest(parent["parent_execution_trace_id"], "parent execution trace ID", nullable=True)
    _digest(parent["configuration_hash"], "parent configuration hash")
    overrides = _closed(trace["controlled_overrides"], {"model", "effort", "configuration_hash"}, "controlled overrides")
    _text(overrides["model"], "override model"); _text(overrides["effort"], "override effort")
    _digest(overrides["configuration_hash"], "override configuration hash")
    canary = _closed(trace["delivery_canary"], {"status", "evidence_digest"}, "delivery canary")
    if canary["status"] not in {"passed", "failed", "not_run"}:
        raise ValueError("delivery canary status is invalid")
    if canary["status"] == "not_run":
        if canary["evidence_digest"] is not None: raise ValueError("unrun delivery canary evidence must be null")
    else: _digest(canary["evidence_digest"], "delivery canary evidence")
    context = _closed(trace["context"], {"threadId", "turnId"}, "trace association context")
    _correlation_id(context["threadId"], "trace threadId", "thread")
    _correlation_id(context["turnId"], "trace turnId", "turn")
    graph = _closed(trace["parent_child_graph"], {
        "root_execution_trace_id", "parent_execution_trace_id", "child_execution_trace_ids",
    }, "parent-child graph")
    _digest(graph["root_execution_trace_id"], "root execution trace ID")
    _digest(graph["parent_execution_trace_id"], "graph parent trace ID", nullable=True)
    children = _strings(graph["child_execution_trace_ids"], "child execution trace IDs")
    for child in children: _digest(child, "child execution trace ID")
    tokens = _closed(trace["raw_token_vector"], {
        "input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens",
    }, "raw token vector")
    for field in tokens:
        _integer(tokens[field], f"raw token {field}", nullable=True)
    counts = _closed(trace["request_turn_count"], {"requests", "turns"}, "request-turn count")
    _integer(counts["requests"], "request count", nullable=True); _integer(counts["turns"], "turn count", nullable=True)
    _integer(trace["wall_time_ms"], "wall time", nullable=True); _integer(trace["retries"], "retry count", nullable=True)
    compaction = _closed(trace["compaction"], {"occurred", "count"}, "compaction")
    if not isinstance(compaction["occurred"], bool): raise ValueError("compaction occurred must be boolean")
    _integer(compaction["count"], "compaction count")
    if compaction["occurred"] != (compaction["count"] > 0): raise ValueError("compaction count and occurrence disagree")
    validation = _closed(trace["validation"], {"status", "evidence_digest"}, "validation")
    if validation["status"] not in {"completed", "failed", "not_run"}: raise ValueError("validation status is invalid")
    if validation["status"] == "not_run":
        if validation["evidence_digest"] is not None: raise ValueError("unrun validation evidence must be null")
    else: _digest(validation["evidence_digest"], "validation evidence")
    cancellation = _closed(trace["cancellation"], {"state", "reason"}, "cancellation")
    if cancellation["state"] not in {"not_requested", "requested", "completed"}: raise ValueError("cancellation state is invalid")
    _text(cancellation["reason"], "cancellation reason", nullable=True)
    if cancellation["state"] == "not_requested" and cancellation["reason"] is not None: raise ValueError("uncancelled work cannot carry a cancellation reason")
    if cancellation["state"] != "not_requested" and cancellation["reason"] not in CANCELLATION_REASON_CODES:
        raise ValueError("cancellation reason must use an enumerated code")
    failed = _closed(trace["failed_abandoned_work"], {"failed_count", "abandoned_count"}, "failed-abandoned work")
    _integer(failed["failed_count"], "failed-work count"); _integer(failed["abandoned_count"], "abandoned-work count")
    if trace["terminal_state"] not in {"completed", "failed", "cancelled", "abandoned"}: raise ValueError("terminal state is invalid")
    outcome = _closed(trace["outcome"], {"status", "evidence_digest"}, "outcome")
    if outcome["status"] not in {"completed", "failed", "cancelled", "abandoned"}: raise ValueError("outcome status is invalid")
    _digest(outcome["evidence_digest"], "outcome evidence")
    if outcome["status"] != trace["terminal_state"]: raise ValueError("terminal state and outcome status disagree")
    if trace["acceptance"] is not None: raise ValueError("unavailable terminal acceptance must be null")
    if trace["terminal_state"] == "completed":
        if cancellation["state"] != "not_requested" or failed["failed_count"] or failed["abandoned_count"]:
            raise ValueError("completed work contradicts cancellation or failed-work counters")
    elif trace["terminal_state"] == "failed":
        if cancellation["state"] != "not_requested" or failed["failed_count"] < 1:
            raise ValueError("failed work requires a failed count and no completed cancellation")
    elif trace["terminal_state"] == "abandoned":
        if cancellation["state"] != "not_requested" or failed["abandoned_count"] < 1:
            raise ValueError("abandoned work requires an abandoned count and no completed cancellation")
    elif cancellation["state"] != "completed":
        raise ValueError("cancelled work requires completed cancellation evidence")


def _validate_failure(value: object) -> dict:
    failure = _closed(value, {
        "failure_code", "affected_field", "expected_evidence_ref",
        "observed_evidence_ref", "resulting_disposition",
    }, "treatment failure")
    if failure["failure_code"] not in FAILURE_DISPOSITIONS:
        raise ValueError("treatment failure code is invalid")
    if failure["affected_field"] != "treatment.evidence": raise ValueError("treatment failure affected field is invalid")
    if failure["expected_evidence_ref"] is not None or failure["observed_evidence_ref"] is not None:
        raise ValueError("normalized treatment failure evidence references must be null")
    if failure["resulting_disposition"] != FAILURE_DISPOSITIONS[failure["failure_code"]]:
        raise ValueError("structured treatment failure disposition is invalid")
    return failure


def _validate_observations(trace: dict, profile: list[dict]) -> dict[str, dict]:
    values = trace["observations"]
    if not isinstance(values, list): raise ValueError("trace observations must be an array")
    entries = {item["field_path"]: item for item in profile if item["client_identity_id"] == trace["client_identity_id"] and item["surface"] == trace["surface"]}
    observed: dict[str, dict] = {}
    for value in values:
        row = _closed(value, {"field_path", "observation_state", "value", "evidence_ref", "captured_at"}, "observation value")
        field = _text(row["field_path"], "observation field path")
        if field in observed: raise ValueError("duplicate observation field path")
        if field not in entries: raise ValueError("observation field is not profiled for the trace surface")
        state = row["observation_state"]
        if state not in entries[field]["observation_state_rules"]["allowed_states"]: raise ValueError("observation state is not allowed by its profile")
        if _contains_unknown(row["value"]): raise ValueError("literal unknown cannot replace a typed observation value")
        if state == "observed_value" and row["value"] is None: raise ValueError("observed value cannot be null")
        if state != "observed_value" and row["value"] is not None: raise ValueError("null-only observation state cannot carry a value")
        present = state in {"observed_value", "explicit_null"}
        if present:
            _evidence_ref(row["evidence_ref"], "observation evidence reference"); _timestamp(row["captured_at"], "observation capture timestamp")
        else:
            _evidence_ref(row["evidence_ref"], "observation evidence reference", nullable=True); _timestamp(row["captured_at"], "observation capture timestamp", nullable=True)
        if state == "undocumented" and (row["evidence_ref"] is not None or row["captured_at"] is not None): raise ValueError("undocumented observation cannot claim evidence or capture time")
        if field in {"discovery.models", "discovery.efforts", "discovery.capabilities"} and state == "observed_value": _strings(row["value"], f"{field} observation")
        observed[field] = row
    if set(observed) != set(entries): raise ValueError("trace observations do not cover the surface profile")
    return observed


def _validate_proof(value: object, trace: dict, profile: list[dict]) -> dict | None:
    if value is None: return None
    proof = _closed(value, {
        "proof_id", "profile_entry_key", "named_agent", "model", "effort", "candidate_route_id",
        "agent_contract_id", "instruction_hash", "configuration_hash", "client_identity_id",
        "controlled_overrides", "launch_id", "consumption_evidence_digest", "reroute_monitoring_complete",
    }, "configured-route proof")
    key = _closed(proof["profile_entry_key"], {"client_identity_id", "surface", "field_path"}, "configured-route profile key")
    for field in ("client_identity_id",): _digest(key[field], f"profile key {field}")
    if key["surface"] not in SURFACES: raise ValueError("configured-route profile surface is invalid")
    _text(key["field_path"], "configured-route profile field")
    profile_entry(profile, key["client_identity_id"], key["surface"], key["field_path"])
    for field in ("named_agent", "model", "effort", "candidate_route_id", "agent_contract_id"):
        _text(proof[field], f"configured proof {field}")
    _correlation_id(proof["launch_id"], "configured proof launch ID", "launch")
    for field in ("proof_id", "instruction_hash", "configuration_hash", "client_identity_id", "consumption_evidence_digest"): _digest(proof[field], f"configured proof {field}")
    overrides = _closed(proof["controlled_overrides"], {"model", "effort", "configuration_hash"}, "configured proof overrides")
    _text(overrides["model"], "configured proof override model"); _text(overrides["effort"], "configured proof override effort")
    _digest(overrides["configuration_hash"], "configured proof override configuration hash")
    if not isinstance(proof["reroute_monitoring_complete"], bool): raise ValueError("configured proof reroute completeness must be boolean")
    if proof["proof_id"] != content_id(proof, "proof_id"): raise ValueError("configured-route proof ID is not content addressed")
    return proof


def _proof_failure_codes(proof: dict | None, trace: dict, profile: list[dict]) -> list[str]:
    if proof is None:
        return []
    codes: list[str] = []
    objective = trace["objective_binding"]
    key = proof["profile_entry_key"]
    canonical_key = {"client_identity_id": trace["client_identity_id"], "surface": trace["surface"], "field_path": "assignment.configuration_hash"}
    matched = profile_entry(profile, key["client_identity_id"], key["surface"], key["field_path"])
    if key != canonical_key or matched["classification"] != "derived_from_controlled_configuration" or matched["permitted_claims"] != ["requested_assignment"]:
        codes.append("configuration_mismatch")
    if proof["named_agent"] != trace["named_agent"] or proof["agent_contract_id"] != objective["agent_contract_id"]: codes.append("agent_mismatch")
    if proof["model"] != trace["requested_model"]: codes.append("model_mismatch")
    if proof["effort"] != trace["requested_effort"]: codes.append("effort_mismatch")
    if proof["candidate_route_id"] != objective["candidate_route_id"]: codes.append("configuration_mismatch")
    if proof["instruction_hash"] != trace["instruction_hash"] or proof["configuration_hash"] != trace["configuration_hash"]: codes.append("configuration_mismatch")
    if proof["client_identity_id"] != trace["client_identity_id"]: codes.append("client_or_override_mismatch")
    if (
        proof["launch_id"] != trace["launch_id"]
        or proof["consumption_evidence_digest"] != trace["consumption_evidence_digest"]
    ):
        codes.append("configuration_mismatch")
    expected_overrides = trace["controlled_overrides"]
    if any(proof["controlled_overrides"][field] != expected_overrides[field] for field in ("model", "effort")): codes.append("client_or_override_mismatch")
    hashes = {trace["configuration_hash"], expected_overrides["configuration_hash"], proof["configuration_hash"], proof["controlled_overrides"]["configuration_hash"]}
    if len(hashes) != 1: codes.append("configuration_mismatch")
    if not proof["reroute_monitoring_complete"]: codes.append("effective_treatment_unknown")
    return list(dict.fromkeys(codes))


def _validate_event(value: object) -> dict:
    event = _closed(value, {"event_id", "surface", "threadId", "turnId", "fromModel", "toModel", "reason", "evidence_digest"}, "service reroute event")
    _digest(event["event_id"], "reroute event ID"); _digest(event["evidence_digest"], "reroute event evidence")
    if event["surface"] not in SURFACES: raise ValueError("reroute event surface is invalid")
    _correlation_id(event["threadId"], "reroute threadId", "thread")
    _correlation_id(event["turnId"], "reroute turnId", "turn")
    for field in ("fromModel", "toModel", "reason"): _text(event[field], f"reroute {field}")
    if event["reason"] not in REROUTE_REASON_CODES: raise ValueError("reroute reason must use an enumerated code")
    if event["event_id"] != content_id(event, "event_id"): raise ValueError("reroute event ID is not content addressed")
    return event


def _validate_assessment(value: object) -> dict:
    assessment = _closed(value, {
        "event_id", "destination_candidate_route_id", "destination_agent_contract_id",
        "destination_named_agent", "assessment", "prequalification_evidence_id",
    }, "reroute destination assessment")
    _digest(assessment["event_id"], "assessment event ID")
    for field in ("destination_candidate_route_id", "destination_agent_contract_id", "destination_named_agent"):
        _text(assessment[field], f"assessment {field}", nullable=True)
    if assessment["assessment"] not in {"prequalified_same_agent", "not_prequalified", "unknown", "ambiguous", "different_agent"}:
        raise ValueError("reroute destination assessment is invalid")
    _digest(assessment["prequalification_evidence_id"], "prequalification evidence ID", nullable=True)
    return assessment


def _reroute_disposition(
    trace: dict, events: list[dict], assessments: list[dict], qualification: dict[str, dict],
    trusted: dict[str, dict], canonical_routes: dict[str, dict[str, object]],
    *, synthetic_replay: bool = False,
) -> tuple[str, list[str]]:
    if not events:
        if assessments: return "hard_fail", ["orphan_reroute_destination_assessment"]
        return "", []
    association = (trace["surface"], trace["context"]["threadId"], trace["context"]["turnId"])
    if any((event["surface"], event["threadId"], event["turnId"]) != association for event in events):
        return "hard_fail", ["reroute_association_mismatch"]
    by_event: dict[str, list[dict]] = {}
    for assessment in assessments: by_event.setdefault(assessment["event_id"], []).append(assessment)
    expected_source_model = trace["requested_model"]
    current_route_id = trace["assigned_route_id"]
    visited_route_ids = {current_route_id}
    final_route = None
    for event in events:
        if event["fromModel"] != expected_source_model: return "hard_fail", ["reroute_source_model_mismatch"]
        matches = by_event.get(event["event_id"], [])
        if len(matches) != 1: return "hard_fail", ["reroute_destination_missing" if not matches else "reroute_destination_ambiguous"]
        item = matches[0]; evidence = qualification.get(item["prequalification_evidence_id"])
        if item["assessment"] != "prequalified_same_agent" or evidence is None: return "hard_fail", ["reroute_destination_unapproved"]
        destination_route_id = item["destination_candidate_route_id"]
        if (
            destination_route_id == current_route_id
            or destination_route_id in visited_route_ids
            or event["toModel"] == expected_source_model
        ):
            return "hard_fail", ["reroute_self_target"]
        canonical = canonical_routes.get(destination_route_id)
        if canonical is None: return "hard_fail", ["reroute_destination_unidentifiable"]
        if item["destination_named_agent"] != canonical["named_agent"]: return "hard_fail", ["reroute_destination_different_agent"]
        if item["destination_agent_contract_id"] != canonical["agent_contract_id"]: return "hard_fail", ["reroute_destination_manifest_mismatch"]
        if event["toModel"] != canonical["model"]: return "hard_fail", ["reroute_destination_model_mismatch"]
        expected = (item["destination_candidate_route_id"], item["destination_agent_contract_id"], item["destination_named_agent"])
        actual = (evidence["destination_candidate_route_id"], evidence["destination_agent_contract_id"], evidence["destination_named_agent"])
        if expected != actual or item["destination_named_agent"] != trace["named_agent"]: return "hard_fail", ["reroute_destination_mismatch"]
        synthetic_admitted = (
            synthetic_replay and evidence["authority_kind"] == "synthetic_fixture"
            and evidence["owner_spec_id"] == "G56R-002"
        )
        if not synthetic_admitted:
            if evidence["authority_kind"] != "owned_external" or evidence["owner_spec_id"] == "G56R-002":
                return "hard_fail", ["reroute_destination_non_authoritative"]
            admitted = trusted.get(evidence["qualification_evidence_id"])
            if admitted is None or canonical_bytes(admitted) != canonical_bytes(evidence):
                return "hard_fail", ["reroute_destination_untrusted"]
        expected_source_model = event["toModel"]
        current_route_id = destination_route_id
        visited_route_ids.add(destination_route_id)
        final_route = canonical
    if trace["supported_effective_model"] != events[-1]["toModel"]:
        return "hard_fail", ["reroute_effective_destination_mismatch"]
    if trace["supported_effective_effort"] is not None and (
        final_route is None
        or final_route["effort"] is None
        or trace["supported_effective_effort"] != final_route["effort"]
    ):
        return "hard_fail", ["reroute_effective_destination_mismatch"]
    if set(by_event) != {event["event_id"] for event in events}: return "hard_fail", ["orphan_reroute_destination_assessment"]
    return "non_scorable_rerouted", ["service_reroute_requested_route_non_scorable"]


TRACE_KEYS = {
    "objective_binding", "controlled_environment_id", "client_identity_id", "surface",
    "repository_revision", "repository_tree_digest", "work_item_kind", "work_item_id",
    "named_agent", "assigned_route_id", "requested_model", "requested_effort",
    "supported_effective_model", "supported_effective_effort", "configured_route_proof",
    "launch_id", "consumption_evidence_digest",
    "service_reroute_events", "reroute_destination_assessments", "instruction_hash",
    "configuration_hash", "sandbox", "approvals", "mutation_class",
    "expected_skills_mcp_tools", "loaded_skills_mcp_tools", "parent_configuration",
    "controlled_overrides", "delivery_canary", "treatment_failures", "context",
    "parent_child_graph", "raw_token_vector", "request_turn_count", "wall_time_ms",
    "retries", "compaction", "validation", "cancellation", "failed_abandoned_work",
    "terminal_state", "outcome", "acceptance", "observations", "treatment_disposition",
    "disposition_reasons",
}

__all__ = [name for name in globals() if not name.startswith("__")]
