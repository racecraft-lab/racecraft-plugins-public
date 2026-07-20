#!/usr/bin/env python3
"""Deterministic synthetic treatment replay semantics."""

from __future__ import annotations

from treatment_trace_fixture import *

def _validate_replay_capability_semantics(case_id: str, case: dict, trace: dict) -> None:
    expected_source = {
        "candidate_route_id": trace["objective_binding"]["candidate_route_id"],
        "agent_contract_id": trace["objective_binding"]["agent_contract_id"],
        "named_agent": trace["named_agent"],
        "model": trace["requested_model"],
        "effort": trace["requested_effort"],
    }
    if len(case["source_tuples"]) != 1 or any(
        case["source_tuples"][0][field] != value
        for field, value in expected_source.items()
    ):
        raise ValueError("linked replay capability source tuple does not match treatment trace")
    sources = {(item["model"], item["effort"]) for item in case["source_tuples"]}
    if not sources or any(not item["source_admitted"] for item in case["source_tuples"]):
        raise ValueError("replay capability source case must contain admitted source tuples")
    entries: dict[str, dict[tuple[str, str], tuple[bool, bool]]] = {}
    for surface, payload in case["surfaces"].items():
        indexed: dict[tuple[str, str], tuple[bool, bool]] = {}
        for item in payload["entries"]:
            key = (item["model"], item["effort"])
            if key in indexed:
                raise ValueError("replay capability source case contains a duplicate surface tuple")
            indexed[key] = (item["available"], item["hidden"])
        entries[surface] = indexed
    if case_id == "partial_surface":
        states = {surface: payload["state"] for surface, payload in case["surfaces"].items()}
        incomplete = any(state in {"partial", "unavailable", "unknown"} for state in states.values())
        unavailable_source = any(
            entries[surface].get(source) != (True, False)
            for source in sources for surface in SURFACES
        )
        if not incomplete or not unavailable_source:
            raise ValueError("partial-surface replay case must prove unavailable discovery on a required surface")
    elif case_id == "surface_disagreement":
        if any(case["surfaces"][surface]["state"] != "complete" for surface in SURFACES):
            raise ValueError("surface-disagreement replay case requires complete compared surfaces")
        if any(source not in entries[surface] for source in sources for surface in SURFACES):
            raise ValueError("surface-disagreement replay case must compare every admitted source tuple")
        disagreement = any(
            len({entries[surface][source] for surface in SURFACES}) > 1
            for source in sources
        )
        if not disagreement:
            raise ValueError("surface-disagreement replay case must prove conflicting surface observations")
    else:
        raise ValueError("unsupported linked replay capability case")


def _validate_replay_effort_authority(trace: dict) -> None:
    if digest(REPLAY_RUNTIME_EFFORT_AUTHORITY) != REPLAY_RUNTIME_EFFORT_AUTHORITY_ID:
        raise ValueError("synthetic replay effort authority identity is invalid")
    actual = {
        "schema_version": SCHEMA_VERSION,
        "authority_kind": "synthetic_replay_configuration",
        "runtime_capability_snapshot_id": trace["objective_binding"]["runtime_capability_snapshot_id"],
        "candidate_route_id": trace["objective_binding"]["candidate_route_id"],
        "agent_contract_id": trace["objective_binding"]["agent_contract_id"],
        "named_agent": trace["named_agent"],
        "model": trace["requested_model"],
        "effort": trace["requested_effort"],
    }
    if actual != REPLAY_RUNTIME_EFFORT_AUTHORITY:
        raise ValueError("replay trace does not bind the pinned synthetic runtime effort authority")


def _validate_replay_trace_semantics(case_class: str, trace: dict,
                                     required_capabilities: list[str]) -> None:
    observations = {item["field_path"]: item for item in trace["observations"]}
    events = trace["service_reroute_events"]
    assessments = trace["reroute_destination_assessments"]
    failure_codes = [item["failure_code"] for item in trace["treatment_failures"]]

    def observed(field: str, state: str, value: object) -> bool:
        item = observations[field]
        return item["observation_state"] == state and item["value"] == value

    if trace["terminal_state"] != "completed" or trace["outcome"]["status"] != "completed" or trace["delivery_canary"]["status"] != "passed":
        raise ValueError("replay trace must preserve the predeclared completed canary lifecycle")
    if case_class not in {"approved_same_agent_reroute", "unapproved_unidentifiable_reroute"} and (events or assessments):
        raise ValueError("non-reroute replay class must not contain reroute records")
    model_state, model_value = REPLAY_DISCOVERY_MODEL_DELTAS.get(
        case_class, ("observed_value", [trace["requested_model"]]),
    )
    discovery_baseline = (
        ("discovery.models", model_state, model_value),
        ("discovery.efforts", "observed_value", [trace["requested_effort"]]),
        ("discovery.capabilities", "observed_value", required_capabilities),
    )
    if any(not observed(field, state, value) for field, state, value in discovery_baseline):
        raise ValueError("replay trace changes undeclared baseline discovery observations")

    if case_class == "success":
        valid = observed("discovery.models", "observed_value", [trace["requested_model"]])
        valid &= observed("assignment.named_agent", "observed_value", trace["named_agent"])
    elif case_class == "explicit_null":
        valid = observed("discovery.models", "explicit_null", None)
    elif case_class == "unavailable":
        valid = trace["acceptance"] is None and observed("terminal.acceptance", "unavailable", None)
    elif case_class == "misdelivery":
        item = observations["assignment.named_agent"]
        valid = item["observation_state"] == "observed_value" and item["value"] != trace["named_agent"]
        valid &= "agent_mismatch" in failure_codes
    elif case_class == "approved_same_agent_reroute":
        valid = len(events) == 1 and len(assessments) == 1
        if valid:
            assessment = assessments[0]
            valid = assessment["event_id"] == events[0]["event_id"]
            valid &= assessment["assessment"] == "prequalified_same_agent"
            valid &= assessment["destination_named_agent"] == trace["named_agent"]
        valid &= failure_codes == []
    elif case_class == "unapproved_unidentifiable_reroute":
        valid = len(events) == 1 and assessments == [] and failure_codes == ["reroute_unidentifiable"]
    elif case_class == "discovery_loss":
        valid = observed("discovery.models", "missing", None)
    elif case_class == "surface_disagreement":
        valid = observed("discovery.models", "observed_value", [trace["requested_model"]])
    else:
        raise ValueError("unsupported replay case class")
    if not valid:
        raise ValueError(f"replay trace does not prove its predeclared {case_class} semantics")


def _normalized_replay_pass(capability_fixture: object, treatment_fixture: object) -> list[dict]:
    capability_cases, capability_client_identity_id = _validate_capability_fixture(capability_fixture)
    bundle = _validate_treatment_bundle(
        treatment_fixture, schema_path=SCHEMA_PATH,
        manifest=_read_manifest_snapshot(MANIFEST_PATH),
        trusted_qualification_evidence=None, synthetic_replay=True,
    )
    traces = bundle["treatment_traces"]
    treatment_client_identity_ids = {
        *(item["client_identity_id"] for item in bundle["telemetry_profile"]),
        *(item["client_identity_id"] for item in bundle["controlled_environments"]),
        *(item["client_identity_id"] for item in traces),
    }
    if treatment_client_identity_ids != {capability_client_identity_id}:
        raise ValueError("capability replay client identity does not match treatment evidence")
    canonical_routes = _canonical_routes(_read_manifest_snapshot(MANIFEST_PATH))
    if len(traces) != len(REPLAY_CASES):
        raise ValueError("treatment replay fixture does not use the exact eight-case registry")
    normalized = []
    for trace, replay_case in zip(traces, REPLAY_CASES):
        case_id, case_class, expected_disposition, expected_reasons, capability_case_id, expected_trace_id = replay_case
        execution_trace_id = trace["objective_binding"]["execution_trace_id"]
        slug = case_class.replace("_", "-")
        if trace["context"] != {
            "threadId": f"thread-fixture-{slug}",
            "turnId": f"turn-fixture-{slug}",
        }:
            raise ValueError("treatment replay association does not use fixture-local pseudonyms")
        if trace["parent_child_graph"]["root_execution_trace_id"] != execution_trace_id:
            raise ValueError("treatment replay graph does not bind its deterministic execution identity")
        _validate_replay_effort_authority(trace)
        if trace["treatment_disposition"] != expected_disposition or tuple(trace["disposition_reasons"]) != expected_reasons:
            raise ValueError("treatment replay case does not preserve its predeclared disposition")
        required_capabilities = canonical_routes[trace["objective_binding"]["candidate_route_id"]]["required_capabilities"]
        _validate_replay_trace_semantics(case_class, trace, required_capabilities)
        if (
            execution_trace_id != expected_trace_id
            or digest(trace) != REPLAY_TRACE_BASELINE_DIGESTS[case_id]
        ):
            raise ValueError("treatment replay case changed outside its immutable baseline")
        if capability_case_id is not None:
            source = capability_cases[capability_case_id]
            if source["expected_validity"] != "valid" or source["expected_decision"] != "excluded":
                raise ValueError("replay capability source case does not preserve its predeclared exclusion")
            _validate_replay_capability_semantics(capability_case_id, source, trace)
        normalized.append({
            "case_id": case_id,
            "execution_trace_id": execution_trace_id,
            "case_class": case_class,
            "source_capability_case_id": capability_case_id,
            "treatment_disposition": trace["treatment_disposition"],
            "disposition_reasons": trace["disposition_reasons"],
            "treatment_failure_codes": [item["failure_code"] for item in trace["treatment_failures"]],
            "terminal_state": trace["terminal_state"],
            "delivery_canary_status": trace["delivery_canary"]["status"],
        })
    return normalized


def replay_fixture(fixture_path: Path, digest_manifest_path: Path, *, repeat: int = 2,
                   repository_root: Path = ROOT) -> dict:
    if isinstance(repeat, bool) or not isinstance(repeat, int) or repeat != 2:
        raise ValueError("replay repeat must be exactly 2")
    manifest_target = _fixture_target(repository_root, REPLAY_DIGEST_MANIFEST_PATH)
    treatment_target = _fixture_target(repository_root, TREATMENT_FIXTURE_PATH)
    if _normalized_path(digest_manifest_path) != _normalized_path(manifest_target):
        raise ValueError("replay digest manifest argument must select the declared repository manifest")
    if _normalized_path(fixture_path) != _normalized_path(treatment_target):
        raise ValueError("replay fixture argument must select the declared treatment fixture")
    manifest_raw = _read_bounded_regular_file(manifest_target, allowed_root=repository_root)
    manifest = _unique_json(manifest_raw, "fixture digest manifest")
    if manifest_raw != canonical_fixture_bytes(manifest):
        raise ValueError("fixture digest manifest must use canonical compact UTF-8 JSON plus LF")
    entries = _manifest_entries(manifest)
    targets = {entry["fixture_path"]: _fixture_target(repository_root, entry["fixture_path"]) for entry in entries}
    raw_fixtures = {
        path: _read_bounded_regular_file(targets[path], allowed_root=repository_root)
        for path in REPLAY_FIXTURE_PATHS
    }
    for entry in entries:
        if digest(raw_fixtures[entry["fixture_path"]]) != entry["fixture_digest"]:
            raise ValueError(f"fixture digest mismatch before parsing: {entry['fixture_path']}")
    parsed = {
        path: _unique_json(raw_fixtures[path], f"fixture {path}")
        for path in REPLAY_FIXTURE_PATHS
    }
    for path in REPLAY_FIXTURE_PATHS:
        if raw_fixtures[path] != canonical_fixture_bytes(parsed[path]):
            raise ValueError(f"fixture must use canonical compact UTF-8 JSON plus LF: {path}")
    guardrails = {
        "qualification_scope": "synthetic_replay_only",
        "runtime_continuation_authorized": False,
        "canary_promotes_treatment": False,
        "network_accessed": False,
        "raw_store_accessed": False,
        "synthetic_runtime_effort_authority_id": REPLAY_RUNTIME_EFFORT_AUTHORITY_ID,
    }
    pass_outputs = []
    for _ in range(repeat):
        pass_outputs.append({
            "status": "replayed", "repeat": repeat,
            "fixture_digests": copy.deepcopy(entries),
            "cases": _normalized_replay_pass(parsed[CAPABILITY_FIXTURE_PATH], parsed[TREATMENT_FIXTURE_PATH]),
            "guardrails": copy.deepcopy(guardrails),
        })
    serialized = [canonical_fixture_bytes(item) for item in pass_outputs]
    if serialized[0] != serialized[1]:
        raise ValueError("two-pass replay output is not byte-identical")
    result = pass_outputs[0]
    result["replay_digest"] = digest(serialized[0])
    return result

__all__ = [name for name in globals() if not name.startswith("__")]
