#!/usr/bin/env python3
"""Surface matrix and canary validation."""

from __future__ import annotations

if __package__:
    from .codex_capability_observations import *
else:
    from codex_capability_observations import *

def evaluate_surface_matrix(observations, source_tuples, *, aliases=None, expected_integrity_digest=_UNSET):
    if any(row.get("source_admitted") for row in source_tuples) and not isinstance(source_tuples, _AuthorityTupleSet):
        raise ValueError("source admission requires a manifest-bound tuple set")
    if aliases is None:
        aliases = {}
    if not isinstance(aliases, dict):
        raise ValueError("aliases must be a mapping")
    if not isinstance(observations, list):
        raise ValueError("matrix observations must be a list")
    if any(not isinstance(item, dict) for item in observations):
        raise ValueError("every matrix observation must be an object")
    observations = [validate_observation(dict(item)) for item in observations]
    surfaces = [item["surface"] for item in observations]
    if len(observations) != 3 or set(surfaces) != set(SURFACES) or len(set(surfaces)) != 3:
        raise ValueError("matrix requires exactly one observation per surface")
    observations_by_surface = {item["surface"]: item for item in observations}
    observations = [observations_by_surface[surface] for surface in SURFACES]
    clients = {item["client_identity_id"] for item in observations}
    repository_ids = {item["repository_binding"]["repository_binding_id"] for item in observations}; work_items = {canonical_bytes(item["work_item"]) for item in observations}
    if len(repository_ids) != 1 or len(work_items) != 1: raise ValueError("surface observations must share repository and work-item bindings")
    collection_authorities = [_collection_authority(item) for item in observations]
    normalized_aliases = {}; observations_by_surface = {item["surface"]: item for item in observations}
    for raw_label, alias in aliases.items():
        required = {"canonical_model_id", "authority_kind", "authority_surface"}; enriched = required | {"client_identity_id", "authority_evidence_ref"}
        if not isinstance(raw_label, str) or not _LABEL.fullmatch(raw_label) or not isinstance(alias, dict) or set(alias) != required and set(alias) != enriched:
            raise ValueError("alias authority must use the closed pinned-build shape")
        canonical, surface = alias["canonical_model_id"], alias["authority_surface"]
        if not _token(canonical) or alias["authority_kind"] != "machine_readable_identifier" or surface not in SURFACES:
            raise ValueError("alias authority is unsupported")
        observation = observations_by_surface[surface]
        evidence = [entry for entry in observation["entries"] if entry["model"] == raw_label and entry.get("raw_label") == raw_label and entry.get("machine_id") == canonical]
        if len(evidence) != 1: raise ValueError("alias authority evidence is absent")
        expected_alias = {"canonical_model_id": canonical, "authority_kind": "machine_readable_identifier", "authority_surface": surface,
                          "client_identity_id": observation["client_identity_id"], "authority_evidence_ref": observation["raw_evidence_ref"]}
        if set(alias) == enriched and alias != expected_alias: raise ValueError("alias authority does not match the pinned-build evidence")
        normalized_aliases[raw_label] = expected_alias
    authority_keys = {"candidate_route_digest", "source_ref", "source_sha256", "instruction_sha256", "role_instruction_sha256", "agent_contract_digest", "official_source_bindings", "effort_surface_bindings"}
    if any(row.get("source_admitted") and (not authority_keys <= set(row) or not row["official_source_bindings"] or not row["effort_surface_bindings"]) for row in source_tuples):
        raise ValueError("source admission requires complete tuple authority")
    normalization = digest(normalized_aliases)
    actual_integrity = digest({"observations": observations, "normalization_map_id": normalization})
    if expected_integrity_digest is _UNSET:
        integrity = actual_integrity
    else:
        _need_digest(expected_integrity_digest, "expected_integrity_digest")
        integrity = expected_integrity_digest
    indexed, reasons, _ = _surface_index_and_invalidity(observations, normalized_aliases, normalization, integrity)
    decisions = []
    disagreements_by_key = _surface_disagreements(indexed, observations_by_surface)
    disagreements = [disagreements_by_key[key] for key in sorted(disagreements_by_key)]
    sources = list(source_tuples); source_keys = {(row.get("model"), row.get("effort")) for row in sources}
    observed_keys = {key for entries in indexed.values() for key in entries}
    for key in sorted(observed_keys - source_keys):
        suffix = digest({"model": key[0], "effort": key[1]})[7:23]
        sources.append({"candidate_route_id": f"runtime-only:{suffix}", "agent_contract_id": "unbound-runtime-observation",
                        "named_agent": "unbound-runtime-observation", "model": key[0], "effort": key[1],
                        "candidate_route_digest": digest({"runtime_only": key}), "source_ref": "runtime-only-observation",
                        "source_sha256": digest({"runtime_only": "source"}), "instruction_sha256": digest({"runtime_only": "instruction"}),
                        "role_instruction_sha256": digest({"runtime_only": "instruction"}), "agent_contract_digest": digest({"runtime_only": "contract"}),
                        "official_source_bindings": [], "effort_surface_bindings": [],
                        "source_admitted": False, "authority_reasons": ["source_not_admitted"]})
    complete = all(item["completeness_state"] == "complete" for item in observations); collection_authoritative = all(item == "approved_live" for item in collection_authorities)
    for source in sources:
        key = (source.get("model"), source.get("effort")); values = {surface: indexed[surface].get(key) for surface in SURFACES}
        observed = [value for value in values.values() if value is not None]; availability = {value["available"] for value in observed}
        picker_omission = values["interactive_picker"] is None and values["app_server"] is not None and values["cli"] is not None and values["app_server"]["hidden"] and values["cli"]["hidden"] and next(item for item in observations if item["surface"] == "interactive_picker")["visibility_policy"] == {"complete_enumeration": True}
        why = list(source.get("authority_reasons", [])) if not source.get("source_admitted") else []
        if reasons: disposition, surface_why = "unknown", ["matrix_invalid"]
        elif key[1] is None: disposition, surface_why = "unknown", ["canonical_effort_unknown"]
        elif key in disagreements_by_key:
            disposition = "disagreed"
            surface_why = ["hidden_state_disagreement" if disagreements_by_key[key]["disagreement_class"] == "hidden_state" else "surface_disagreement"]
        elif not complete or len(observed) != 3 and not picker_omission: disposition, surface_why = "unknown", ["surface_evidence_incomplete"]
        elif availability == {True}: disposition, surface_why = "agreed", []
        else: disposition, surface_why = "agreed", ["availability_not_proven"]
        why.extend(item for item in surface_why if item not in why)
        if not collection_authoritative and "collection_evidence_non_authoritative" not in why: why.append("collection_evidence_non_authoritative")
        included = source.get("source_admitted") and disposition == "agreed" and availability == {True} and collection_authoritative
        disagreement = disagreements_by_key.get(key)
        decisions.append({"candidate_route_id": source["candidate_route_id"], "agent_contract_id": source["agent_contract_id"], "named_agent": source["named_agent"],
                          "canonical_model_id": key[0], "canonical_effort": key[1], "source_admitted": bool(source.get("source_admitted")),
                          "candidate_route_digest": source["candidate_route_digest"], "source_ref": source["source_ref"],
                          "source_sha256": source["source_sha256"], "instruction_sha256": source["instruction_sha256"], "role_instruction_sha256": source["role_instruction_sha256"],
                          "agent_contract_digest": source["agent_contract_digest"], "official_source_bindings": list(source["official_source_bindings"]), "effort_surface_bindings": list(source["effort_surface_bindings"]),
                          "runtime_capability_snapshot_id": None,
                          "surface_evidence": {item["surface"]: {"surface_observation_id": item["surface_observation_id"], "completeness_state": item["completeness_state"], "visibility_policy": item["visibility_policy"], "raw_evidence_digest": item["raw_evidence_digest"], "raw_evidence_ref": item["raw_evidence_ref"], "matching_entry": values[item["surface"]]} for item in observations},
                          "hidden_state": {surface: values[surface]["hidden"] if values[surface] is not None else None for surface in SURFACES},
                          "normalization_map_id": normalization, "disagreement_digest": digest(disagreement) if disagreement else None,
                          "exact_treatment_readiness": "pending" if included else "not_ready_excluded",
                          "source_admission_reasons": list(source.get("authority_reasons", [])),
                          "availability_disposition": "supported" if included else "unknown", "surface_disposition": disposition,
                          "decision": "included" if included else "excluded", "reasons": why})
    payload = {"schema_version": SCHEMA_VERSION, "client_identity_id": next(iter(clients)) if len(clients) == 1 else digest({"invalid": "client_identity"}),
               "repository_binding_id": next(iter(repository_ids)), "work_item": observations[0]["work_item"],
               "observations": observations, "normalization_map": normalized_aliases, "normalization_map_id": normalization, "disagreements": disagreements,
               "aggregate_integrity_digest": integrity, "validity": "invalid" if reasons else "valid", "invalidity_reasons": reasons}
    matrix_id = digest(payload)
    for decision in decisions: decision["surface_matrix_id"] = matrix_id
    return {"surface_matrix_id": matrix_id, **payload}, _BoundDecisionSet(decisions)


def validate_surface_matrix(matrix):
    required = {"surface_matrix_id", "schema_version", "client_identity_id", "repository_binding_id", "work_item", "observations", "normalization_map", "normalization_map_id", "disagreements", "aggregate_integrity_digest", "validity", "invalidity_reasons"}
    if not isinstance(matrix, dict) or set(matrix) != required or matrix.get("schema_version") != SCHEMA_VERSION: raise ValueError("surface matrix must use the closed v1 shape")
    if not isinstance(matrix["observations"], list):
        raise ValueError("matrix observations must be a list")
    if any(not isinstance(item, dict) for item in matrix["observations"]):
        raise ValueError("every matrix observation must be an object")
    observations = [validate_observation(dict(item)) for item in matrix["observations"]]
    surfaces = [item["surface"] for item in observations]
    if surfaces != list(SURFACES): raise ValueError("matrix observations must use canonical surface order")
    clients = {item["client_identity_id"] for item in observations}
    expected_client_identity = next(iter(clients)) if len(clients) == 1 else digest({"invalid": "client_identity"})
    if matrix["client_identity_id"] != expected_client_identity: raise ValueError("matrix client identity mismatch")
    validate_work_item(matrix["work_item"])
    if any(item["repository_binding"]["repository_binding_id"] != matrix["repository_binding_id"] or item["work_item"] != matrix["work_item"] for item in observations): raise ValueError("matrix repository or work-item binding mismatch")
    observations_by_surface = {item["surface"]: item for item in observations}
    alias_keys = {"canonical_model_id", "authority_kind", "authority_surface", "client_identity_id", "authority_evidence_ref"}
    for raw_label, alias in matrix["normalization_map"].items():
        if not _LABEL.fullmatch(str(raw_label)) or not isinstance(alias, dict) or set(alias) != alias_keys or not _token(alias["canonical_model_id"]) or alias["authority_kind"] != "machine_readable_identifier" or alias["authority_surface"] not in SURFACES:
            raise ValueError("normalization map alias authority is invalid")
        observation = observations_by_surface[alias["authority_surface"]]
        evidence = [item for item in observation["entries"] if item["model"] == raw_label and item.get("raw_label") == raw_label and item.get("machine_id") == alias["canonical_model_id"]]
        if alias["client_identity_id"] != observation["client_identity_id"] or alias["authority_evidence_ref"] != observation["raw_evidence_ref"] or len(evidence) != 1:
            raise ValueError("normalization map alias authority is not bound to the pinned build")
    if matrix["normalization_map_id"] != digest(matrix["normalization_map"]): raise ValueError("normalization map identity mismatch")
    _need_digest(matrix["aggregate_integrity_digest"], "aggregate_integrity_digest")
    indexed, expected_invalidity_reasons, _ = _surface_index_and_invalidity(
        observations, matrix["normalization_map"], matrix["normalization_map_id"], matrix["aggregate_integrity_digest"],
    )
    if matrix["validity"] not in {"valid", "invalid"} or matrix["invalidity_reasons"] != expected_invalidity_reasons or (matrix["validity"] == "invalid") != bool(expected_invalidity_reasons):
        raise ValueError("surface matrix validity is inconsistent")
    expected_disagreements = _surface_disagreements(indexed, observations_by_surface)
    actual_disagreements = {}
    for item in matrix["disagreements"]:
        keys = {"canonical_tuple", "surface_values", "evidence_refs", "proposed_normalized_key", "disagreement_class", "tuple_disposition"}
        tuple_value = item.get("canonical_tuple", {}) if isinstance(item, dict) else {}
        tuple_key = (tuple_value.get("model"), tuple_value.get("effort"))
        if set(item) != keys or set(tuple_value) != {"model", "effort"} or not all(_token(value) for value in tuple_key) or tuple_key in actual_disagreements:
            raise ValueError("surface disagreement must use unique canonical tuple keys")
        if item != expected_disagreements.get(tuple_key):
            raise ValueError("surface disagreement is inconsistent with observed values")
        actual_disagreements[tuple_key] = item
    if set(actual_disagreements) != set(expected_disagreements):
        raise ValueError("surface disagreement inventory is incomplete")
    if matrix["surface_matrix_id"] != digest({key: matrix[key] for key in matrix if key != "surface_matrix_id"}):
        raise ValueError("surface matrix identity does not match its canonical payload")
    return matrix


def validate_tuple_decisions(decisions, *, require_snapshot=False):
    if any(item.get("decision") == "included" for item in decisions) and not isinstance(decisions, _BoundDecisionSet):
        raise ValueError("included decisions require manifest-bound authority")
    keys = {"candidate_route_id", "candidate_route_digest", "agent_contract_id", "named_agent", "agent_contract_digest", "source_ref", "source_sha256", "instruction_sha256", "role_instruction_sha256", "canonical_model_id", "canonical_effort", "official_source_bindings", "effort_surface_bindings", "runtime_capability_snapshot_id", "surface_matrix_id", "surface_evidence", "hidden_state", "normalization_map_id", "disagreement_digest", "source_admitted", "source_admission_reasons", "availability_disposition", "surface_disposition", "exact_treatment_readiness", "decision", "reasons"}
    for item in decisions:
        strings = (item.get("candidate_route_id"), item.get("agent_contract_id"), item.get("named_agent"), item.get("canonical_model_id"))
        if set(item) != keys or not all(isinstance(value, str) and value and not any(mark in value for mark in ("/", "\\", "://", "@")) for value in strings):
            raise ValueError("tuple decision must use the sanitized closed v1 shape")
        if not isinstance(item["source_ref"], str) or not item["source_ref"] or item["source_ref"].startswith(("/", "\\")) or ".." in Path(item["source_ref"]).parts: raise ValueError("tuple source_ref must be repository relative")
        for field in ("candidate_route_digest", "agent_contract_digest", "source_sha256", "instruction_sha256", "role_instruction_sha256", "surface_matrix_id", "normalization_map_id"):
            _need_digest(item[field], field)
        if item["instruction_sha256"] != item["role_instruction_sha256"]: raise ValueError("tuple instruction hashes disagree")
        snapshot = item["runtime_capability_snapshot_id"]
        if snapshot is not None: _need_digest(snapshot, "runtime_capability_snapshot_id")
        if require_snapshot and snapshot is None: raise ValueError("tuple runtime snapshot binding is required")
        if item["disagreement_digest"] is not None: _need_digest(item["disagreement_digest"], "disagreement_digest")
        source_binding_keys = {"official_source_ledger_id", "source_refresh_digest"}
        if any(set(row) != source_binding_keys or not _SOURCE_ID.fullmatch(str(row["official_source_ledger_id"])) or not _DIGEST.fullmatch(str(row["source_refresh_digest"])) for row in item["official_source_bindings"]): raise ValueError("tuple official-source binding is invalid")
        effort_binding_keys = {"effort_surface_record_id", "effort_surface_record_digest", "official_source_ledger_id", "source_refresh_digest"}
        if any(set(row) != effort_binding_keys or not isinstance(row["effort_surface_record_id"], str) or not row["effort_surface_record_id"] or not _SOURCE_ID.fullmatch(str(row["official_source_ledger_id"])) or not _DIGEST.fullmatch(str(row["effort_surface_record_digest"])) or not _DIGEST.fullmatch(str(row["source_refresh_digest"])) for row in item["effort_surface_bindings"]): raise ValueError("tuple effort-surface binding is invalid")
        if set(item["surface_evidence"]) != set(SURFACES) or set(item["hidden_state"]) != set(SURFACES): raise ValueError("tuple surface evidence is incomplete")
        evidence_keys = {"surface_observation_id", "completeness_state", "visibility_policy", "raw_evidence_digest", "raw_evidence_ref", "matching_entry"}
        for surface, evidence in item["surface_evidence"].items():
            if set(evidence) != evidence_keys or evidence["completeness_state"] not in {"complete", "partial", "unavailable", "unknown"}: raise ValueError("tuple surface evidence is invalid")
            _need_digest(evidence["surface_observation_id"], "surface_observation_id"); _need_digest(evidence["raw_evidence_digest"], "raw_evidence_digest")
            if evidence["raw_evidence_ref"] != f"raw://{evidence['raw_evidence_digest']}": raise ValueError("tuple surface evidence reference is invalid")
            if evidence["matching_entry"] is not None: _clean_entry(evidence["matching_entry"])
            expected_hidden = evidence["matching_entry"]["hidden"] if evidence["matching_entry"] is not None else None
            if item["hidden_state"][surface] != expected_hidden: raise ValueError("tuple hidden state does not match surface evidence")
        if item["canonical_effort"] is not None and not _token(item["canonical_effort"]): raise ValueError("tuple effort is invalid")
        if not isinstance(item["source_admitted"], bool) or item["availability_disposition"] not in {"supported", "available_for_pinned_environment", "unknown"} or item["surface_disposition"] not in {"agreed", "disagreed", "unknown"} or item["exact_treatment_readiness"] not in {"pending", "not_ready_excluded"} or item["decision"] not in {"included", "excluded"} or not all(_token(value) for value in item["source_admission_reasons"] + item["reasons"]):
            raise ValueError("tuple decision disposition is invalid")
        if item["decision"] == "excluded" and not item["reasons"]:
            raise ValueError("excluded tuple decision requires a reason")
        if item["decision"] == "included" and (not item["source_admitted"] or item["surface_disposition"] != "agreed"): raise ValueError("included tuple lacks source and surface admission")
    if len({item["candidate_route_id"] for item in decisions}) != len(decisions): raise ValueError("tuple decision candidate identities must be unique")
    return decisions


def build_runtime_snapshot(identity, refreshes, matrix, *, supersedes=None):
    if supersedes is not None: _need_digest(supersedes, "supersedes_snapshot_id")
    matrix = validate_surface_matrix(matrix)
    if matrix["client_identity_id"] != identity["client_identity_id"]: raise ValueError("freeze client identity does not match the matrix")
    repository = validate_repository_binding(matrix["observations"][0]["repository_binding"]); work_item = validate_work_item(matrix["work_item"])
    entries = [entry for observation in matrix["observations"] for entry in observation["entries"]]
    raw_digest = digest([item["raw_evidence_digest"] for item in matrix["observations"]])
    started_at = min(
        matrix["observations"],
        key=lambda item: _parsed_timestamp(item["started_at"], "surface collection start"),
    )["started_at"]
    completed_at = max(
        matrix["observations"],
        key=lambda item: _parsed_timestamp(item["completed_at"], "surface collection completion"),
    )["completed_at"]
    payload = {"schema_version": SCHEMA_VERSION, "surface_matrix_id": matrix["surface_matrix_id"], "client_identity_id": identity["client_identity_id"],
               "controlled_repository_snapshot": repository, "work_item": work_item,
               "models": sorted({item["model"] for item in entries}), "efforts": sorted({item["effort"] for item in entries}),
               "capabilities": sorted({value for item in entries for value in item.get("capabilities", [])}),
               "collection_window": {"started_at": started_at, "completed_at": completed_at},
               "raw_evidence_digest": raw_digest, "raw_evidence_ref": f"aggregate://{raw_digest}",
               "source_refresh_set_digest": digest(refreshes), "supersedes_snapshot_id": supersedes}
    return {"runtime_capability_snapshot_id": digest(payload), **payload}


def _validated_canary_approvals(approvals):
    keys = {"executor_contract_id", "contract_version", "implementation_digest", "platform", "approval_evidence_digest"}; identities = []
    for item in approvals:
        if not isinstance(item, dict) or set(item) != keys or item["contract_version"] != SCHEMA_VERSION or item["platform"] not in {"macos", "linux", "windows"}:
            raise ValueError("canary approval must use the closed repository-owned shape")
        for field in ("executor_contract_id", "implementation_digest", "approval_evidence_digest"): _need_digest(item[field], field)
        identities.append((item["executor_contract_id"], item["implementation_digest"]))
    if len(identities) != len(set(identities)): raise ValueError("canary approvals must be unique")
    return approvals


def _canary_evidence_payload(result):
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": result["snapshot_id"],
        "canonical_model_id": result["canonical_model_id"],
        "canonical_effort": result["canonical_effort"],
        "terminal_class": result["terminal_class"],
        "exit_code": result["exit_code"],
        "sentinel_observed": result["sentinel_observed"],
    }


def _validate_canary_result_envelope(result, approvals=APPROVED_CANARY_EXECUTORS, *, evidence_bytes=None):
    required = {"snapshot_id", "canonical_model_id", "canonical_effort", "attempt_index", "timeout_seconds", "combined_output_cap_bytes", "executor_contract_id", "implementation_digest", "executor_result_digest", "contract_version", "platform", "timeout_enforced", "output_cap_enforced", "process_tree_termination_state", "retry_count", "exit_code", "sentinel_observed", "terminal_class", "availability_disposition", "evidence_digest"}
    if set(result) != required:
        raise ValueError("canary result must use the closed v1 envelope")
    for field in ("snapshot_id", "executor_contract_id", "implementation_digest", "executor_result_digest", "evidence_digest"):
        _need_digest(result[field], field)
    if not _token(result["canonical_model_id"]) or not _token(result["canonical_effort"]) or result["platform"] not in {"macos", "linux", "windows"}:
        raise ValueError("canary tuple or platform identity is invalid")
    bound_result = {key: result[key] for key in result if key not in {"executor_result_digest", "availability_disposition"}}
    if result["executor_result_digest"] != digest(bound_result): raise ValueError("canary result digest does not bind the closed result envelope")
    integer_fields = ("attempt_index", "timeout_seconds", "combined_output_cap_bytes", "retry_count")
    if any(type(result[field]) is not int for field in integer_fields) or type(result["timeout_enforced"]) is not bool or type(result["output_cap_enforced"]) is not bool or type(result["sentinel_observed"]) is not bool or result["exit_code"] is not None and type(result["exit_code"]) is not int:
        raise ValueError("canary result uses invalid primitive types")
    fixed = result["attempt_index"], result["timeout_seconds"], result["combined_output_cap_bytes"], result["contract_version"], result["retry_count"]
    if fixed != (1, 30, 65536, SCHEMA_VERSION, 0) or not result["timeout_enforced"] or not result["output_cap_enforced"]:
        raise ValueError("canary bounds or retry contract violated")
    if result["terminal_class"] not in ("success", *ERROR_TERMINALS) or result["process_tree_termination_state"] not in {"not_needed", "completed", "failed"}:
        raise ValueError("unknown canary state")
    if result["terminal_class"] in {"timeout", "output_cap_exceeded"} and result["process_tree_termination_state"] == "not_needed":
        raise ValueError("bounded canary termination requires process-tree cleanup")
    if evidence_bytes is not None:
        if not isinstance(evidence_bytes, bytes) or digest(evidence_bytes) != result["evidence_digest"]:
            raise ValueError("canary evidence bytes do not match evidence_digest")
        evidence = _parse_json_bytes(evidence_bytes)
        if evidence_bytes != canonical_bytes(evidence) + b"\n" or evidence != _canary_evidence_payload(result):
            raise ValueError("canary evidence must use the canonical closed redacted schema")
    approvals = _validated_canary_approvals(approvals); approval = next((item for item in approvals if item["executor_contract_id"] == result["executor_contract_id"] and item["implementation_digest"] == result["implementation_digest"]), None)
    if approval is not None and approval["platform"] != result["platform"]:
        raise ValueError("canary executor platform does not match its repository approval")
    # A caller-supplied envelope can prove internal consistency, not executor
    # provenance. This slice has no trusted invocation or verifiable attestation
    # mechanism, so even a structurally matching repository approval remains
    # non-authoritative and cannot promote availability.
    return {**result, "availability_disposition": "unknown"}


def validate_canary_result(result, approvals=APPROVED_CANARY_EXECUTORS, *, evidence_bytes):
    if evidence_bytes is None:
        raise ValueError("canary result requires its content-addressed redacted evidence")
    return _validate_canary_result_envelope(result, approvals, evidence_bytes=evidence_bytes)


def validate_canary_results(results, approvals=APPROVED_CANARY_EXECUTORS):
    keys = [(item.get("snapshot_id"), item.get("canonical_model_id"), item.get("canonical_effort")) for item in results]
    if len(keys) != len(set(keys)):
        raise ValueError("only one canary is permitted per snapshot/model/effort")
    result_digests = [item.get("executor_result_digest") for item in results]
    if len(result_digests) != len(set(result_digests)): raise ValueError("canary result digests cannot be replayed across tuple keys")
    return [_validate_canary_result_envelope(item, approvals) for item in results]

__all__ = [name for name in globals() if not name.startswith("__")]
