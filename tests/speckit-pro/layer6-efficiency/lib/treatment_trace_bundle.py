#!/usr/bin/env python3
"""Execution trace and treatment bundle graph validation."""

from __future__ import annotations
if __package__:
    from .treatment_trace_fields import *
else:
    from treatment_trace_fields import *
def _effective_effort_route(
    events: list[dict], assessments: list[dict], supported_route: dict | None,
    canonical_routes: dict[str, dict[str, object]],
) -> dict | None:
    if not events:
        return supported_route
    matches = [item for item in assessments if item["event_id"] == events[-1]["event_id"]]
    if len(matches) != 1:
        return None
    return canonical_routes.get(matches[0]["destination_candidate_route_id"])
def _validate_trace(trace: object, profile: list[dict], environments: dict[str, dict],
                    policies: dict[str, dict], resolutions: dict[str, dict],
                    qualification: dict[str, dict], trusted: dict[str, dict],
                    canonical_routes: dict[str, dict[str, object]],
                    *, synthetic_replay: bool = False) -> dict:
    row = _closed(trace, TRACE_KEYS, "treatment trace")
    objective = _closed(row["objective_binding"], set(OBJECTIVE_ID_FIELDS), "six-ID objective binding")
    for field in ("candidate_route_id", "agent_contract_id"): _text(objective[field], f"objective {field}")
    for field in ("runtime_capability_snapshot_id", "route_resolution_id", "experiment_policy_id", "execution_trace_id"):
        _digest(objective[field], f"objective {field}")
    env_id = _digest(row["controlled_environment_id"], "trace controlled environment ID")
    if env_id not in environments: raise ValueError("trace has no controlled environment owner")
    env = environments[env_id]
    resolution_id = objective["route_resolution_id"]
    if resolution_id not in resolutions: raise ValueError("trace has no route resolution owner")
    resolution = resolutions[resolution_id]
    referenced_route_ids = [
        resolution["preferred_route_id"], *resolution["attempted_route_ids"],
    ]
    if resolution["supported_effective_route_id"] is not None:
        referenced_route_ids.append(resolution["supported_effective_route_id"])
    if any(route_id not in canonical_routes for route_id in referenced_route_ids):
        raise ValueError("route resolution references a route outside the canonical candidate manifest")
    if any(
        canonical_routes[route_id]["agent_contract_id"] != objective["agent_contract_id"]
        for route_id in referenced_route_ids
    ):
        raise ValueError("route resolution references a route owned by a different agent contract")
    policy_id = objective["experiment_policy_id"]
    if policy_id not in policies: raise ValueError("trace has no experiment policy owner")
    policy = policies[policy_id]
    _digest(row["client_identity_id"], "trace client identity"); _digest(row["repository_tree_digest"], "trace repository tree")
    if row["surface"] not in SURFACES or row["work_item_kind"] not in {"task", "fixture", "objective"}: raise ValueError("trace surface or work item kind is invalid")
    if not isinstance(row["repository_revision"], str) or REVISION_RE.fullmatch(row["repository_revision"]) is None: raise ValueError("trace repository revision is invalid")
    _identifier(row["work_item_id"], "trace work_item_id")
    for field in ("named_agent", "assigned_route_id", "requested_model", "requested_effort"):
        _text(row[field], f"trace {field}")
    _correlation_id(row["launch_id"], "trace launch ID", "launch")
    _digest(row["consumption_evidence_digest"], "trace consumption evidence")
    _text(row["supported_effective_model"], "supported effective model", nullable=True); _text(row["supported_effective_effort"], "supported effective effort", nullable=True)
    _digest(row["instruction_hash"], "trace instruction hash"); _digest(row["configuration_hash"], "trace configuration hash")
    env_equalities = {
        "client_identity_id": row["client_identity_id"], "surface": row["surface"],
        "runtime_capability_snapshot_id": objective["runtime_capability_snapshot_id"],
        "repository_revision": row["repository_revision"], "repository_tree_digest": row["repository_tree_digest"],
        "candidate_route_id": objective["candidate_route_id"], "work_item_kind": row["work_item_kind"],
        "work_item_id": row["work_item_id"],
    }
    if any(env[field] != expected for field, expected in env_equalities.items()): raise ValueError("trace controlled environment binding is inconsistent")
    if objective["candidate_route_id"] != row["assigned_route_id"] or resolution["assigned_route_id"] != row["assigned_route_id"]:
        raise ValueError("assigned route does not join objective, environment, and resolution")
    canonical_route = canonical_routes.get(objective["candidate_route_id"])
    if canonical_route is None or {key: canonical_route[key] for key in ("agent_contract_id", "named_agent", "model")} != {
        "agent_contract_id": objective["agent_contract_id"], "named_agent": row["named_agent"], "model": row["requested_model"],
    }:
        raise ValueError("assigned route does not bind the canonical candidate manifest")
    canonical_effort = canonical_route["effort"]
    if canonical_effort is not None and row["requested_effort"] != canonical_effort:
        raise ValueError("requested effort does not bind the canonical candidate manifest")
    if resolution["runtime_capability_snapshot_id"] != objective["runtime_capability_snapshot_id"]: raise ValueError("route resolution snapshot does not join the objective")
    policy_equalities = {
        "candidate_route_id": objective["candidate_route_id"], "work_item_kind": row["work_item_kind"],
        "work_item_id": row["work_item_id"], "mutation_class": row["mutation_class"],
    }
    if any(policy[field] != expected for field, expected in policy_equalities.items()):
        raise ValueError("trace experiment policy binding is inconsistent")
    _validate_trace_structures(row)
    if objective["execution_trace_id"] != execution_trace_identity(row):
        raise ValueError("execution trace ID is not deterministically derived")
    observations = _validate_observations(row, profile)
    proof = _validate_proof(row["configured_route_proof"], row, profile)
    failures = row["treatment_failures"]
    if not isinstance(failures, list): raise ValueError("treatment failures must be an array")
    validated_failures = [_validate_failure(item) for item in failures]
    if len({item["failure_code"] for item in validated_failures}) != len(validated_failures): raise ValueError("duplicate structured treatment failure code")
    derived_codes = _proof_failure_codes(proof, row, profile)
    discovery_requirements = {
        "discovery.models": ([row["requested_model"]], "model_mismatch"),
        "discovery.efforts": ([row["requested_effort"]], "effort_mismatch"),
        "discovery.capabilities": (canonical_route["required_capabilities"], "skills_mcp_tools_mismatch"),
    }
    for field, (required_values, failure_code) in discovery_requirements.items():
        observed = observations.get(field)
        if synthetic_replay and observed is not None and observed["observation_state"] in {
            "explicit_null", "missing", "unavailable", "undocumented",
        }:
            continue
        if (
            observed is None or observed["observation_state"] != "observed_value"
            or any(value not in observed["value"] for value in required_values)
        ):
            derived_codes.append(failure_code)
    events = row["service_reroute_events"]; assessments = row["reroute_destination_assessments"]
    if not isinstance(events, list) or not isinstance(assessments, list): raise ValueError("reroute records must be arrays")
    events = [_validate_event(item) for item in events]; assessments = [_validate_assessment(item) for item in assessments]
    if len({item["event_id"] for item in events}) != len(events): raise ValueError("duplicate reroute event ID")
    supported_route_id = resolution["supported_effective_route_id"]
    supported_route = canonical_routes.get(supported_route_id) if supported_route_id is not None else None
    if events and supported_route_id is not None:
        raise ValueError("service reroute cannot claim a resolver-supported effective route")
    if not events and supported_route is not None:
        if supported_route_id != resolution["assigned_route_id"]:
            raise ValueError("supported effective route must select the assigned route without a service reroute")
        if row["supported_effective_model"] != supported_route["model"]:
            raise ValueError("supported effective route does not bind its canonical effective model")
        if supported_route["effort"] is not None and row["supported_effective_effort"] != supported_route["effort"]:
            raise ValueError("supported effective route does not bind its canonical effective effort")
    effective_effort_route = _effective_effort_route(
        events, assessments, supported_route, canonical_routes,
    )
    if row["supported_effective_effort"] is not None and (
        effective_effort_route is None or effective_effort_route["effort"] is None
        or row["supported_effective_effort"] != effective_effort_route["effort"]
    ):
        derived_codes.append("effort_mismatch")
    if row["supported_effective_model"] is not None and (
        events and events[-1]["toModel"] != row["supported_effective_model"]
        or not events and supported_route is None
    ):
        derived_codes.append("model_mismatch")
    if events and row["supported_effective_model"] is None: derived_codes.append("model_mismatch")
    reroute_observation = observations.get("reroute.events")
    if reroute_observation is not None and reroute_observation["observation_state"] == "observed_value":
        if not _same_json_value(reroute_observation["value"], events, "reroute observation"): derived_codes.append("reroute_ambiguous")
    elif events: derived_codes.append("reroute_unidentifiable")
    bindings = {
        "assignment.named_agent": row["named_agent"], "assignment.model": row["requested_model"],
        "assignment.effort": row["requested_effort"], "assignment.supported_effective_model": row["supported_effective_model"],
        "assignment.supported_effective_effort": row["supported_effective_effort"], "assignment.candidate_route_id": objective["candidate_route_id"],
        "assignment.agent_contract_id": objective["agent_contract_id"], "assignment.instruction_hash": row["instruction_hash"],
        "assignment.configuration_hash": row["configuration_hash"], "route.preferred_route_id": resolution["preferred_route_id"],
        "route.attempted_route_ids": resolution["attempted_route_ids"], "route.assigned_route_id": resolution["assigned_route_id"],
        "route.supported_effective_route_id": resolution["supported_effective_route_id"], "route.fallback_index": resolution["fallback_index"],
        "route.fallback_reason": resolution["fallback_reason"], "route.runtime_capability_snapshot_id": resolution["runtime_capability_snapshot_id"],
        "route.resolved_at": resolution["resolved_at"], "reroute.events": events,
        "treatment.sandbox": row["sandbox"], "treatment.approvals": row["approvals"],
        "treatment.mutation_class": row["mutation_class"], "treatment.expected_skills_mcp_tools": row["expected_skills_mcp_tools"],
        "treatment.loaded_skills_mcp_tools": row["loaded_skills_mcp_tools"], "treatment.parent_configuration": row["parent_configuration"],
        "treatment.controlled_overrides": row["controlled_overrides"], "treatment.delivery_canary": row["delivery_canary"],
        "treatment.failures": row["treatment_failures"],
        "parent.context": row["context"], "parent.graph": row["parent_child_graph"],
        "resources.raw_token_vector": row["raw_token_vector"], "resources.request_turn_count": row["request_turn_count"],
        "resources.wall_time_ms": row["wall_time_ms"], "lifecycle.retries": row["retries"], "lifecycle.compaction": row["compaction"],
        "lifecycle.validation": row["validation"], "lifecycle.cancellation": row["cancellation"],
        "lifecycle.failed_abandoned_work": row["failed_abandoned_work"], "terminal.state": row["terminal_state"],
        "terminal.outcome": row["outcome"], "terminal.acceptance": row["acceptance"],
    }
    observation_failure_codes = {
        "assignment.named_agent": "agent_mismatch",
        "assignment.model": "model_mismatch", "assignment.effort": "effort_mismatch",
        "assignment.supported_effective_model": "model_mismatch", "assignment.supported_effective_effort": "effort_mismatch",
        "assignment.agent_contract_id": "agent_mismatch", "treatment.sandbox": "sandbox_approvals_mismatch",
        "treatment.approvals": "sandbox_approvals_mismatch", "treatment.mutation_class": "mutation_class_mismatch",
        "treatment.expected_skills_mcp_tools": "skills_mcp_tools_mismatch", "treatment.loaded_skills_mcp_tools": "skills_mcp_tools_mismatch",
        "treatment.parent_configuration": "parent_configuration_mismatch", "parent.context": "parent_configuration_mismatch",
        "parent.graph": "parent_configuration_mismatch", "treatment.controlled_overrides": "client_or_override_mismatch",
        "treatment.delivery_canary": "delivery_canary_failure",
    }
    configuration_fields = {
        "assignment.candidate_route_id", "assignment.instruction_hash", "assignment.configuration_hash",
        "route.preferred_route_id", "route.attempted_route_ids", "route.assigned_route_id",
        "route.supported_effective_route_id", "route.fallback_index", "route.fallback_reason",
        "route.runtime_capability_snapshot_id", "route.resolved_at",
    }
    for field, expected in bindings.items():
        entry = profile_entry(profile, row["client_identity_id"], row["surface"], field)
        claim_present = _top_level_claim_present(field, expected)
        if entry["classification"] in {"unavailable", "not_applicable", "undocumented"} and claim_present:
            raise ValueError(f"{field} cannot retain a top-level claim under its telemetry classification")
        observed = observations.get(field)
        if observed is None:
            if claim_present:
                raise ValueError(f"{field} cannot retain a top-level claim without applicable telemetry authority")
            continue
        if entry["classification"] == "conditional":
            if claim_present and observed["observation_state"] != "observed_value":
                raise ValueError(f"{field} condition occurred without an observed value")
            if not claim_present and observed["observation_state"] == "observed_value":
                raise ValueError(f"{field} claims an observation when its condition did not occur")
        mismatch = observed["observation_state"] == "observed_value" and not _same_json_value(observed["value"], expected, f"{field} observation")
        mismatch |= observed["observation_state"] == "explicit_null" and expected is not None
        mismatch |= observed["observation_state"] == "missing" and expected is not None and entry["classification"] not in {"conditional", "undocumented"}
        if mismatch: derived_codes.append("configuration_mismatch" if field in configuration_fields else observation_failure_codes.get(field, "effective_treatment_unknown"))
    if row["expected_skills_mcp_tools"] != row["loaded_skills_mcp_tools"]: derived_codes.append("skills_mcp_tools_mismatch")
    if row["parent_configuration"]["parent_execution_trace_id"] != row["parent_child_graph"]["parent_execution_trace_id"]: derived_codes.append("parent_configuration_mismatch")
    if row["controlled_overrides"]["model"] != row["requested_model"] or row["controlled_overrides"]["effort"] != row["requested_effort"]: derived_codes.append("client_or_override_mismatch")
    proof_configuration_hash = proof["configuration_hash"] if proof is not None else row["configuration_hash"]
    if len({row["configuration_hash"], row["controlled_overrides"]["configuration_hash"], proof_configuration_hash}) != 1: derived_codes.append("configuration_mismatch")
    if row["delivery_canary"]["status"] == "failed": derived_codes.append("delivery_canary_failure")
    reroute_disposition, reasons = _reroute_disposition(
        row, events, assessments, qualification, trusted, canonical_routes,
        synthetic_replay=synthetic_replay,
    )
    if events and resolution["supported_effective_route_id"] not in {None, resolution["assigned_route_id"]}: raise ValueError("service reroute must not rewrite resolver-selected fields")
    reason_codes = {
        "reroute_association_mismatch": "reroute_unidentifiable", "ambiguous_reroute_association": "reroute_ambiguous",
        "reroute_destination_missing": "reroute_unidentifiable", "reroute_destination_ambiguous": "reroute_ambiguous",
        "reroute_destination_unapproved": "reroute_unapproved", "reroute_destination_mismatch": "reroute_different_agent",
        "reroute_destination_unidentifiable": "reroute_unidentifiable", "reroute_destination_manifest_mismatch": "reroute_unidentifiable",
        "reroute_destination_different_agent": "reroute_different_agent", "reroute_destination_model_mismatch": "model_mismatch",
        "reroute_destination_non_authoritative": "reroute_unapproved", "reroute_destination_untrusted": "reroute_unapproved",
        "reroute_effective_destination_mismatch": "model_mismatch", "reroute_source_model_mismatch": "model_mismatch",
        "reroute_self_target": "reroute_unapproved",
        "orphan_reroute_destination_assessment": "reroute_ambiguous",
    }
    if reroute_disposition == "hard_fail": derived_codes.extend(reason_codes[item] for item in reasons)
    effective_observed = all(
        path in observations and row[field] is not None and observations[path]["observation_state"] == "observed_value"
        and _same_json_value(observations[path]["value"], row[field], f"{path} observation")
        for field, path in (("supported_effective_model", "assignment.supported_effective_model"), ("supported_effective_effort", "assignment.supported_effective_effort"))
    )
    reroute_profile = profile_entry(profile, row["client_identity_id"], row["surface"], "reroute.events")
    monitoring_authoritative = (
        proof is not None and proof["reroute_monitoring_complete"]
        and reroute_profile["classification"] == "stable_native"
        and reroute_profile["completeness_rule"] == "complete_capture"
        and reroute_observation is not None and reroute_observation["observation_state"] == "observed_value"
    )
    proof_valid = proof is not None and not _proof_failure_codes(proof, row, profile) and monitoring_authoritative
    hard_failure_derived = any(FAILURE_DISPOSITIONS.get(code) == "hard_fail" for code in derived_codes)
    if not reroute_disposition and (
        not proof_valid and not effective_observed or canonical_effort is None and not hard_failure_derived
    ):
        derived_codes.append("effective_treatment_unknown")
    derived_codes = list(dict.fromkeys(derived_codes))
    declared_by_code = {item["failure_code"]: item for item in validated_failures}
    unsubstantiated = set(declared_by_code) - set(derived_codes)
    if unsubstantiated: raise ValueError(f"unsubstantiated declared treatment failure: {sorted(unsubstantiated)}")
    normalized_failures = [{
        "failure_code": code, "affected_field": "treatment.evidence", "expected_evidence_ref": None,
        "observed_evidence_ref": None, "resulting_disposition": FAILURE_DISPOSITIONS[code],
    } for code in derived_codes]
    if validated_failures != normalized_failures:
        raise ValueError(
            "declared treatment failures do not match derived treatment failures: "
            f"expected {derived_codes!r}"
        )
    failure_dispositions = {item["resulting_disposition"] for item in normalized_failures}
    if reroute_disposition == "non_scorable_rerouted" and "hard_fail" not in failure_dispositions: expected_disposition, expected_reasons = reroute_disposition, reasons
    elif "hard_fail" in failure_dispositions:
        expected_disposition = "hard_fail"
        expected_reasons = sorted(set(derived_codes) | (set(reasons) if reroute_disposition == "hard_fail" else set()))
    elif "unknown" in failure_dispositions: expected_disposition, expected_reasons = "unknown", sorted(derived_codes)
    elif proof_valid: expected_disposition, expected_reasons = "proven", ["configured_route_proof_and_complete_reroute_monitoring"]
    elif effective_observed: expected_disposition, expected_reasons = "proven", ["profile_supported_effective_treatment"]
    else: expected_disposition, expected_reasons = "unknown", ["effective_treatment_or_reroute_evidence_missing"]
    if row["treatment_disposition"] not in {"proven", "unknown", "non_scorable_rerouted", "hard_fail"}: raise ValueError("declared treatment disposition is invalid")
    declared_reasons = _strings(row["disposition_reasons"], "treatment disposition reasons")
    if any(reason not in DISPOSITION_REASON_CODES for reason in declared_reasons):
        raise ValueError("treatment disposition reasons must use enumerated codes")
    if row["treatment_disposition"] != expected_disposition:
        raise ValueError(
            "declared treatment disposition does not match the derived disposition: "
            f"expected {expected_disposition!r}"
        )
    if declared_reasons != expected_reasons:
        raise ValueError(
            "declared treatment disposition reasons do not match the derived reasons: "
            f"expected {expected_reasons!r}"
        )
    return row
def _validate_trace_graph(traces: list[dict]) -> None:
    by_id = {trace["objective_binding"]["execution_trace_id"]: trace for trace in traces}
    if len(by_id) != len(traces): raise ValueError("duplicate execution trace ID")
    for trace_id, trace in by_id.items():
        graph = trace["parent_child_graph"]; parent = graph["parent_execution_trace_id"]
        if graph["root_execution_trace_id"] not in by_id: raise ValueError("trace graph root has no owner")
        if parent == trace_id or trace_id in graph["child_execution_trace_ids"]: raise ValueError("trace graph cannot contain a self edge")
        if parent is not None and parent not in by_id: raise ValueError("trace graph parent has no owner")
        if any(child not in by_id for child in graph["child_execution_trace_ids"]): raise ValueError("trace graph child has no owner")
        if parent is None and graph["root_execution_trace_id"] != trace_id: raise ValueError("root trace does not own its graph root")
        if parent is not None and trace_id not in by_id[parent]["parent_child_graph"]["child_execution_trace_ids"]:
            raise ValueError("trace graph parent and child edges are not reciprocal")
        if parent is not None and trace["parent_configuration"]["configuration_hash"] != by_id[parent]["configuration_hash"]:
            raise ValueError("parent configuration hash does not bind the referenced parent trace")
        for child in graph["child_execution_trace_ids"]:
            if by_id[child]["parent_child_graph"]["parent_execution_trace_id"] != trace_id:
                raise ValueError("trace graph child and parent edges are not reciprocal")
    for trace_id, trace in by_id.items():
        seen: set[str] = set(); current = trace_id
        while by_id[current]["parent_child_graph"]["parent_execution_trace_id"] is not None:
            if current in seen: raise ValueError("trace graph contains a cycle")
            seen.add(current); current = by_id[current]["parent_child_graph"]["parent_execution_trace_id"]
        if trace["parent_child_graph"]["root_execution_trace_id"] != current:
            raise ValueError("trace graph root does not match its ancestor chain")
def _validate_treatment_bundle(
    bundle: object, *, schema_path: Path, manifest: dict,
    trusted_qualification_evidence: Mapping[str, dict] | None,
    synthetic_replay: bool = False,
) -> dict:
    _validate_resource_bounds(bundle)
    _validate_retained_strings(bundle)
    schema_bytes = _read_bounded_regular_file(schema_path)
    schema = _parse_json_bytes(schema_bytes)
    if not isinstance(schema, dict): raise ValueError("treatment contract must be a JSON Schema object")
    _validate_resource_bounds(schema)
    _validate_schema_instance(bundle, schema, schema)
    value = _closed(copy.deepcopy(bundle), {
        "schema_version", "treatment_contract_digest", "telemetry_profile_id", "telemetry_profile",
        "controlled_environments", "experiment_policy_registry", "qualification_evidence_registry", "route_resolutions",
        "treatment_traces", "fixture_provenance",
    }, "treatment bundle")
    if value["schema_version"] != SCHEMA_VERSION: raise ValueError("unsupported treatment schema version")
    contract_digest = digest(schema_bytes)
    if value["treatment_contract_digest"] != contract_digest: raise ValueError("treatment contract digest does not bind the exact schema bytes")
    current_source_ids = _current_source_ids(manifest)
    canonical_routes = _canonical_routes(manifest)
    profile = _validate_profile(value["telemetry_profile"], current_source_ids)
    trusted = _validate_trusted_qualification(trusted_qualification_evidence)
    expected_profile_id = telemetry_profile_id(value["schema_version"], profile, contract_digest)
    if value["telemetry_profile_id"] != expected_profile_id: raise ValueError("telemetry profile ID does not bind the profile and treatment contract")
    registries = (("controlled_environments", _validate_environment, "controlled_environment_id", "controlled environment"),
                  ("experiment_policy_registry", _validate_experiment_policy, "experiment_policy_id", "experiment policy"),
                  ("qualification_evidence_registry", _validate_qualification, "qualification_evidence_id", "qualification evidence"),
                  ("route_resolutions", _validate_resolution, "route_resolution_id", "route resolution"))
    owners: dict[str, dict[str, dict]] = {}
    for field, validator, identity, label in registries:
        if not isinstance(value[field], list): raise ValueError(f"{field} must be an array")
        rows = [validator(item) for item in value[field]]; keys = [item[identity] for item in rows]
        if len(keys) != len(set(keys)): raise ValueError(f"duplicate {label} owner")
        owners[field] = dict(zip(keys, rows))
    for owner in owners["qualification_evidence_registry"].values():
        canonical = canonical_routes.get(owner["destination_candidate_route_id"])
        if canonical is None or (
            owner["destination_agent_contract_id"] != canonical["agent_contract_id"]
            or owner["destination_named_agent"] != canonical["named_agent"]
        ):
            raise ValueError("qualification evidence destination is not bound to the canonical manifest")
    traces = value["treatment_traces"]
    if not isinstance(traces, list) or not traces: raise ValueError("treatment traces must be a non-empty array")
    profile_clients = {item["client_identity_id"] for item in profile}
    environment_clients = {item["client_identity_id"] for item in owners["controlled_environments"].values()}
    trace_clients = {item["client_identity_id"] for item in traces}
    if profile_clients != environment_clients or profile_clients != trace_clients:
        raise ValueError("telemetry profile client must own every environment and trace")
    validated = [_validate_trace(
        item, profile, owners["controlled_environments"], owners["experiment_policy_registry"], owners["route_resolutions"],
        owners["qualification_evidence_registry"], trusted, canonical_routes,
        synthetic_replay=synthetic_replay,
    ) for item in traces]
    referenced_environments = {item["controlled_environment_id"] for item in validated}
    if referenced_environments != set(owners["controlled_environments"]):
        raise ValueError("controlled environment owner registry contains a missing or orphan owner")
    referenced_resolutions = {item["objective_binding"]["route_resolution_id"] for item in validated}
    if referenced_resolutions != set(owners["route_resolutions"]):
        raise ValueError("route resolution owner registry contains a missing or orphan owner")
    referenced_policies = {item["objective_binding"]["experiment_policy_id"] for item in validated}
    if referenced_policies != set(owners["experiment_policy_registry"]):
        raise ValueError("experiment policy owner registry contains a missing or orphan owner")
    referenced_qualifications = {
        assessment["prequalification_evidence_id"]
        for item in validated
        for assessment in item["reroute_destination_assessments"]
        if assessment["prequalification_evidence_id"] is not None
    }
    if referenced_qualifications != set(owners["qualification_evidence_registry"]):
        raise ValueError("qualification evidence owner registry contains a missing or orphan owner")
    _validate_trace_graph(validated)
    provenance = _closed(value["fixture_provenance"], {
        "schema_version", "sanitizer_version", "raw_evidence_digest", "expected_dispositions",
        "network_required", "raw_store_required", "replay_count",
    }, "fixture provenance")
    if provenance["schema_version"] != SCHEMA_VERSION or provenance["network_required"] is not False or provenance["raw_store_required"] is not False or provenance["replay_count"] != 2:
        raise ValueError("fixture provenance violates offline replay bounds")
    _text(provenance["sanitizer_version"], "sanitizer version"); _digest(provenance["raw_evidence_digest"], "raw evidence digest")
    expected_dispositions = [{
        "execution_trace_id": item["objective_binding"]["execution_trace_id"],
        "treatment_disposition": item["treatment_disposition"],
    } for item in validated]
    if provenance["expected_dispositions"] != expected_dispositions:
        raise ValueError(
            f"fixture expected dispositions do not match traces: expected {expected_dispositions!r}"
        )
    return value

__all__ = [name for name in globals() if not name.startswith("__")]
