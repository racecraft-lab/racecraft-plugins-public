#!/usr/bin/env python3
"""Runtime snapshot and capability freeze construction."""

from __future__ import annotations

from codex_capability_retention import *

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


def _freeze_identity_payload(freeze):
    return {key: freeze[key] for key in freeze if key != "candidate_freeze_id"}


def _validate_publication_time(published_at, refreshes, matrix, predecessor=None):
    published = _parsed_timestamp(published_at, "publication timestamp")
    evidence_times = [
        *(_parsed_timestamp(item["retrieved_at"], "source retrieval timestamp") for item in refreshes),
        *(_parsed_timestamp(item["completed_at"], "surface collection timestamp") for item in matrix["observations"]),
    ]
    if evidence_times and published < max(evidence_times):
        raise ValueError("publication timestamp precedes captured evidence")
    if predecessor is not None and published <= _parsed_timestamp(predecessor["published_at"], "predecessor publication timestamp"):
        raise ValueError("successor publication timestamp must be later than its predecessor")


def _successor_canary_results(predecessor, same_runtime_inputs):
    return copy.deepcopy(predecessor["canary_results"]) if predecessor is not None and same_runtime_inputs else []


def _validate_same_snapshot_canary_history(predecessor, results, unchanged_snapshot):
    if not unchanged_snapshot:
        return
    prior_results = predecessor["canary_results"]
    if len(results) < len(prior_results) or canonical_bytes(results[:len(prior_results)]) != canonical_bytes(prior_results):
        raise ValueError("same-snapshot successor cannot drop or rewrite canary history")


def build_freeze(
    identity, refreshes, matrix, decisions, published_at, *, manifest, predecessor=None,
    raw_evidence_root=None, repository_root=None,
    expected_predecessor_telemetry_profile_id=None,
    expected_predecessor_treatment_contract_digest=None,
    expected_predecessor_treatment_evidence_digest=None,
):
    identity = build_client_identity(identity); matrix = validate_surface_matrix(matrix); decisions = validate_tuple_decisions(decisions)
    if (raw_evidence_root is None) != (repository_root is None):
        raise ValueError("freeze raw evidence root and repository root must be provided together")
    if any(item["collection_method_id"] == "unknown-observation-v1" for item in matrix["observations"]):
        if raw_evidence_root is None or repository_root is None:
            raise ValueError("initial unknown-observation publication requires its raw evidence root")
        for observation in matrix["observations"]:
            validate_unknown_observation_evidence(observation, raw_evidence_root, repository_root)
    if predecessor is not None:
        predecessor = _validate_freeze_payload(
            predecessor, manifest,
            expected_telemetry_profile_id=expected_predecessor_telemetry_profile_id,
            expected_treatment_contract_digest=expected_predecessor_treatment_contract_digest,
            expected_treatment_evidence_digest=expected_predecessor_treatment_evidence_digest,
            require_predecessor=False,
        )
    if len(refreshes) != 22 or len({item.get("official_source_ledger_id") for item in refreshes}) != 22:
        raise ValueError("freeze requires all 22 source refreshes")
    refresh_validation = validate_source_refreshes(manifest, refreshes); sanitized_refreshes = refresh_validation["sanitized_refreshes"]
    if raw_evidence_root is not None:
        validate_source_capture_evidence(manifest, refreshes, raw_evidence_root, repository_root)
    _validate_publication_time(published_at, sanitized_refreshes, matrix, predecessor)
    rebuilt, expected = evaluate_surface_matrix(matrix["observations"], candidate_tuples_from_manifest(manifest, refreshes), aliases=matrix["normalization_map"], expected_integrity_digest=matrix["aggregate_integrity_digest"])
    if rebuilt["surface_matrix_id"] != matrix["surface_matrix_id"] or canonical_bytes(expected) != canonical_bytes(decisions):
        raise ValueError("tuple decisions do not match manifest-backed matrix evaluation")
    source_digest, telemetry = refresh_validation["digest"], PENDING_TELEMETRY_PROFILE_ID
    same_runtime_inputs = predecessor is not None and (
        predecessor["client_identity"] == identity
        and predecessor["official_source_refreshes"] == sanitized_refreshes
        and predecessor["surface_matrix"] == matrix
    )
    supersedes_snapshot = None
    if predecessor is not None:
        supersedes_snapshot = predecessor["runtime_capability_snapshot"].get("supersedes_snapshot_id") if same_runtime_inputs else predecessor["runtime_capability_snapshot_id"]
    snapshot = build_runtime_snapshot(identity, sanitized_refreshes, matrix, supersedes=supersedes_snapshot)
    decisions = _BoundDecisionSet([{**item, "runtime_capability_snapshot_id": snapshot["runtime_capability_snapshot_id"]} for item in expected]); validate_tuple_decisions(decisions, require_snapshot=True)
    tuple_digest = digest(decisions); manifest_binding = {"schema_version": manifest["schema_version"], "snapshot_id": manifest["snapshot"]["snapshot_id"], "manifest_digest": digest(manifest)}
    included = [item["candidate_route_id"] for item in decisions if item["decision"] == "included"]
    excluded = [{"candidate_route_id": item["candidate_route_id"], "reasons": item["reasons"]} for item in decisions if item["decision"] == "excluded"]
    result = {"schema_version": SCHEMA_VERSION, "source_manifest_binding": manifest_binding, "client_identity": identity, "client_identity_id": identity["client_identity_id"],
            "official_source_refreshes": sanitized_refreshes, "surface_matrix": matrix, "runtime_capability_snapshot": snapshot,
            "runtime_capability_snapshot_id": snapshot["runtime_capability_snapshot_id"], "telemetry_profile_id": telemetry,
            "source_refresh_set_digest": source_digest, "current_ledger_digest": source_digest, "surface_matrix_id": matrix["surface_matrix_id"],
            "surface_matrix_digest": matrix["surface_matrix_id"], "tuple_decision_digest": tuple_digest,
            "included_candidate_route_ids": included, "excluded_candidates": excluded,
            "tuple_decisions": decisions, "approved_canary_executors": list(APPROVED_CANARY_EXECUTORS),
            "canary_results": _successor_canary_results(predecessor, same_runtime_inputs), "published_at": published_at,
            "supersedes_candidate_freeze_id": predecessor["candidate_freeze_id"] if predecessor is not None else None}
    result["candidate_freeze_id"] = digest(_freeze_identity_payload(result))
    return validate_freeze(
        result, manifest, predecessor=predecessor,
        expected_predecessor_telemetry_profile_id=expected_predecessor_telemetry_profile_id,
        expected_predecessor_treatment_contract_digest=expected_predecessor_treatment_contract_digest,
        expected_predecessor_treatment_evidence_digest=expected_predecessor_treatment_evidence_digest,
    )


def _documented_discovery_unavailable(observations):
    return any(item.get("collection_method_id") == "unknown-observation-v1" for item in observations)


def _validate_canary_tuple_binding(decisions, result, snapshot_id, observations):
    matches = [
        item for item in decisions
        if item["canonical_model_id"] == result["canonical_model_id"]
        and item["canonical_effort"] == result["canonical_effort"]
    ]
    admitted = [item for item in matches if item["source_admitted"]]
    if result["snapshot_id"] != snapshot_id or not admitted:
        raise ValueError("canary requires a source-admitted snapshot model/effort key")
    if not _documented_discovery_unavailable(observations):
        raise ValueError("canary requires documented discovery to be unavailable")
    return admitted


def _validate_freeze_payload(
    freeze, manifest, *, predecessor=None, expected_telemetry_profile_id=None,
    expected_treatment_contract_digest=None, expected_treatment_evidence_digest=None,
    expected_predecessor_telemetry_profile_id=None,
    expected_predecessor_treatment_contract_digest=None,
    expected_predecessor_treatment_evidence_digest=None, require_predecessor=True,
):
    keys = {"schema_version", "candidate_freeze_id", "source_manifest_binding", "client_identity", "client_identity_id", "official_source_refreshes", "source_refresh_set_digest", "surface_matrix", "surface_matrix_id", "runtime_capability_snapshot", "runtime_capability_snapshot_id", "telemetry_profile_id", "current_ledger_digest", "surface_matrix_digest", "tuple_decision_digest", "included_candidate_route_ids", "excluded_candidates", "tuple_decisions", "approved_canary_executors", "canary_results", "published_at", "supersedes_candidate_freeze_id"}
    actual_keys = set(freeze) if isinstance(freeze, dict) else set()
    treatment_fields = {"treatment_contract_digest", "treatment_evidence_digest"}
    present_treatment_fields = actual_keys & treatment_fields
    if present_treatment_fields and present_treatment_fields != treatment_fields:
        raise ValueError("freeze treatment contract and evidence bindings must be present together")
    treatment_bound = present_treatment_fields == treatment_fields
    expected_keys = keys | (treatment_fields if treatment_bound else set())
    if not isinstance(freeze, dict) or actual_keys != expected_keys or freeze.get("schema_version") != SCHEMA_VERSION: raise ValueError("freeze must use the closed v1 shape")
    validate_manifest(manifest); identity = build_client_identity(freeze["client_identity"])
    if predecessor is not None:
        predecessor = _validate_freeze_payload(
            predecessor, manifest,
            expected_telemetry_profile_id=expected_predecessor_telemetry_profile_id,
            expected_treatment_contract_digest=expected_predecessor_treatment_contract_digest,
            expected_treatment_evidence_digest=expected_predecessor_treatment_evidence_digest,
            require_predecessor=False,
        )
    supersedes = freeze["supersedes_candidate_freeze_id"]
    if supersedes is None and predecessor is not None:
        raise ValueError("initial freeze cannot declare a predecessor")
    if supersedes is not None:
        _need_digest(supersedes, "supersedes_candidate_freeze_id")
        if require_predecessor and predecessor is None:
            raise ValueError("successor freeze requires its validated predecessor")
        if predecessor is not None and supersedes != predecessor["candidate_freeze_id"]:
            raise ValueError("successor freeze predecessor identity is invalid")
    if freeze["client_identity_id"] != identity["client_identity_id"]: raise ValueError("freeze client identity fields disagree")
    if freeze["client_identity"] != identity: raise ValueError("freeze client identity must use the canonical closed shape")
    expected_manifest = {"schema_version": manifest["schema_version"], "snapshot_id": manifest["snapshot"]["snapshot_id"], "manifest_digest": digest(manifest)}
    if freeze["source_manifest_binding"] != expected_manifest: raise ValueError("freeze manifest binding is not canonical")
    refresh_validation = validate_published_source_refreshes(manifest, freeze["official_source_refreshes"]); matrix = validate_surface_matrix(freeze["surface_matrix"])
    _validate_publication_time(freeze["published_at"], freeze["official_source_refreshes"], matrix, predecessor)
    if freeze["source_refresh_set_digest"] != refresh_validation["digest"] or freeze["current_ledger_digest"] != refresh_validation["digest"]: raise ValueError("freeze source ledger digests disagree")
    if freeze["surface_matrix_id"] != matrix["surface_matrix_id"] or freeze["surface_matrix_digest"] != matrix["surface_matrix_id"]: raise ValueError("freeze surface matrix fields disagree")
    snapshot = freeze["runtime_capability_snapshot"]; expected_snapshot = build_runtime_snapshot(identity, freeze["official_source_refreshes"], matrix, supersedes=snapshot.get("supersedes_snapshot_id"))
    if snapshot != expected_snapshot or freeze["runtime_capability_snapshot_id"] != expected_snapshot["runtime_capability_snapshot_id"]: raise ValueError("freeze runtime snapshot fields disagree")
    unchanged_snapshot = predecessor is not None and expected_snapshot["runtime_capability_snapshot_id"] == predecessor["runtime_capability_snapshot_id"]
    if predecessor is not None:
        required_snapshot_predecessor = predecessor["runtime_capability_snapshot"].get("supersedes_snapshot_id") if unchanged_snapshot else predecessor["runtime_capability_snapshot_id"]
        if expected_snapshot["supersedes_snapshot_id"] != required_snapshot_predecessor:
            raise ValueError("successor runtime snapshot lineage is invalid")
    rebuilt_matrix, expected_decisions = evaluate_surface_matrix(matrix["observations"], candidate_tuples_from_published(manifest, freeze["official_source_refreshes"]), aliases=matrix["normalization_map"], expected_integrity_digest=matrix["aggregate_integrity_digest"])
    if rebuilt_matrix["surface_matrix_id"] != matrix["surface_matrix_id"]: raise ValueError("published surface matrix cannot be rebuilt")
    expected_decisions = _BoundDecisionSet([{**item, "runtime_capability_snapshot_id": expected_snapshot["runtime_capability_snapshot_id"]} for item in expected_decisions])
    validate_tuple_decisions(expected_decisions, require_snapshot=True)
    if canonical_bytes(freeze["tuple_decisions"]) != canonical_bytes(expected_decisions): raise ValueError("published tuple decisions cannot be rebuilt")
    route_ids = {item["candidate_route_id"] for item in expected_decisions}; manifest_route_ids = {item["candidate_route_id"] for item in manifest["candidate_routes"]}
    if not manifest_route_ids <= route_ids or freeze["tuple_decision_digest"] != digest(expected_decisions): raise ValueError("freeze tuple authority is incomplete")
    included = [item["candidate_route_id"] for item in expected_decisions if item["decision"] == "included"]
    excluded = [{"candidate_route_id": item["candidate_route_id"], "reasons": item["reasons"]} for item in expected_decisions if item["decision"] == "excluded"]
    if freeze["included_candidate_route_ids"] != included or freeze["excluded_candidates"] != excluded: raise ValueError("freeze derived candidate lists disagree")
    _need_digest(freeze["candidate_freeze_id"], "candidate_freeze_id")
    if freeze["telemetry_profile_id"] == PENDING_TELEMETRY_PROFILE_ID:
        if (
            treatment_bound
            or expected_telemetry_profile_id is not None
            or expected_treatment_contract_digest is not None
            or expected_treatment_evidence_digest is not None
        ):
            raise ValueError("pending-treatment freeze cannot claim a treatment contract binding")
    else:
        if (
            expected_telemetry_profile_id is None
            or expected_treatment_contract_digest is None
            or expected_treatment_evidence_digest is None
        ):
            raise ValueError(
                "treatment-aware freeze validation requires the expected profile, contract, and evidence binding"
            )
        _need_digest(expected_telemetry_profile_id, "expected telemetry profile ID")
        _need_digest(expected_treatment_contract_digest, "expected treatment contract digest")
        _need_digest(expected_treatment_evidence_digest, "expected treatment evidence digest")
        if not treatment_bound:
            raise ValueError("treatment-aware freeze must retain its treatment contract and evidence digests")
        _need_digest(freeze["treatment_contract_digest"], "treatment contract digest")
        _need_digest(freeze["treatment_evidence_digest"], "treatment evidence digest")
        if (
            freeze["telemetry_profile_id"] != expected_telemetry_profile_id
            or freeze["treatment_contract_digest"] != expected_treatment_contract_digest
            or freeze["treatment_evidence_digest"] != expected_treatment_evidence_digest
        ):
            raise ValueError("freeze treatment profile, contract, and evidence binding disagree")
    canonical_approvals = list(_validated_canary_approvals(APPROVED_CANARY_EXECUTORS))
    if freeze["approved_canary_executors"] != canonical_approvals:
        raise ValueError("published canary approvals do not match the repository-owned allowlist")
    if canonical_approvals or freeze["canary_results"]:
        raise ValueError("published canary provenance is unavailable in this slice")
    validated_canaries = validate_canary_results(freeze["canary_results"], APPROVED_CANARY_EXECUTORS)
    if validated_canaries != freeze["canary_results"]: raise ValueError("published canary dispositions are not validated")
    _validate_same_snapshot_canary_history(predecessor, validated_canaries, unchanged_snapshot)
    for result in validated_canaries:
        _validate_canary_tuple_binding(expected_decisions, result, expected_snapshot["runtime_capability_snapshot_id"], matrix["observations"])
    if freeze["candidate_freeze_id"] != digest(_freeze_identity_payload(freeze)): raise ValueError("candidate freeze identity does not bind its authoritative payload")
    return freeze


def validate_freeze(
    freeze, manifest, *, predecessor=None, expected_telemetry_profile_id=None,
    expected_treatment_contract_digest=None, expected_treatment_evidence_digest=None,
    expected_predecessor_telemetry_profile_id=None,
    expected_predecessor_treatment_contract_digest=None,
    expected_predecessor_treatment_evidence_digest=None,
):
    return _validate_freeze_payload(
        freeze, manifest, predecessor=predecessor,
        expected_telemetry_profile_id=expected_telemetry_profile_id,
        expected_treatment_contract_digest=expected_treatment_contract_digest,
        expected_treatment_evidence_digest=expected_treatment_evidence_digest,
        expected_predecessor_telemetry_profile_id=expected_predecessor_telemetry_profile_id,
        expected_predecessor_treatment_contract_digest=expected_predecessor_treatment_contract_digest,
        expected_predecessor_treatment_evidence_digest=expected_predecessor_treatment_evidence_digest,
        require_predecessor=True,
    )


def build_canary_successor(
    predecessor, result, manifest, published_at, *, raw_evidence_root, repository_root,
    expected_telemetry_profile_id=None, expected_treatment_contract_digest=None,
    expected_treatment_evidence_digest=None,
):
    _validate_freeze_payload(
        predecessor, manifest,
        expected_telemetry_profile_id=expected_telemetry_profile_id,
        expected_treatment_contract_digest=expected_treatment_contract_digest,
        expected_treatment_evidence_digest=expected_treatment_evidence_digest,
        require_predecessor=False,
    )
    raise ValueError(
        "trusted canary invocation and attestation are unavailable in this slice; "
        "caller-supplied executor results cannot establish provenance"
    )


def _validate_retained_freeze_evidence(freeze, raw, repository_root, raw_descriptor=None, raw_identity=None):
    for observation in freeze["surface_matrix"]["observations"]:
        if observation["collection_method_id"] != "fixture-enumeration-v1":
            validate_unknown_observation_evidence(
                observation, raw, repository_root, raw_descriptor=raw_descriptor, raw_identity=raw_identity)
    for result in freeze["canary_results"]:
        validate_canary_evidence(
            raw, repository_root, result, raw_descriptor=raw_descriptor, raw_identity=raw_identity)
def publish_with_raw_evidence_retention(
    freeze, output, raw_evidence_root, repository_root, *, manifest,
    predecessor=None, expected_telemetry_profile_id=None, expected_treatment_contract_digest=None,
    expected_treatment_evidence_digest=None, expected_predecessor_telemetry_profile_id=None,
    expected_predecessor_treatment_contract_digest=None,
    expected_predecessor_treatment_evidence_digest=None,
):
    raw, raw_identity = _validated_raw_evidence_root_binding(raw_evidence_root, repository_root)
    freeze = validate_freeze(
        freeze, manifest, predecessor=predecessor,
        expected_telemetry_profile_id=expected_telemetry_profile_id,
        expected_treatment_contract_digest=expected_treatment_contract_digest,
        expected_treatment_evidence_digest=expected_treatment_evidence_digest,
        expected_predecessor_telemetry_profile_id=expected_predecessor_telemetry_profile_id,
        expected_predecessor_treatment_contract_digest=expected_predecessor_treatment_contract_digest,
        expected_predecessor_treatment_evidence_digest=expected_predecessor_treatment_evidence_digest,
    )
    payload = canonical_bytes(freeze) + b"\n"
    if len(payload) > PRIVATE_REFRESH_MAX_BYTES: raise ValueError("freeze publication exceeds the bounded size")
    with _bound_publication_output(output, raw, raw_identity) as (
        output, output_parent_descriptor, output_parent_identity,
    ):
        _recover_append_only_directory(
            output.parent, output_parent_identity, require_content_addressed=False,
            descriptor=output_parent_descriptor, directory_lock_held=True,
        )
        with _retention_lock(raw, raw_identity) as raw_descriptor:
            validate_raw_evidence_root(raw, repository_root, **_raw_lock_kwargs(raw_descriptor, raw_identity))
            deleted_digests = {
                _validate_deletion_record(record_digest, record)["raw_evidence_digest"]
                for record_digest, record in _load_private_records(raw / DELETION_RECORDS_DIR, repository_root, "deletion record")
            }
            if set(_freeze_raw_evidence_digests(freeze)) & deleted_digests:
                raise ValueError("raw evidence cannot be registered after deletion has begun")
            validate_source_capture_evidence(
                manifest, freeze["official_source_refreshes"], raw, repository_root,
                raw_descriptor=raw_descriptor, raw_identity=raw_identity)
            _validate_retained_freeze_evidence(freeze, raw, repository_root, raw_descriptor, raw_identity)
            already_published = _publication_target_matches(
                output, payload, parent_descriptor=output_parent_descriptor,
                parent_identity=output_parent_identity, directory_lock_held=True,
            )
            retention_record_digests = _register_raw_evidence_retention_locked(
                freeze, raw, raw_identity, repository_root, raw_descriptor=raw_descriptor,
            )
            intent_digest = _store_publication_intent_locked(
                freeze, retention_record_digests, raw, raw_identity, repository_root,
            )
            if not already_published:
                _write_private_bytes_at(
                    output_parent_descriptor, output.parent, output.name, payload,
                    append_only=True, expected_parent_identity=output_parent_identity,
                    directory_lock_held=True,
                )
            with _bound_publication_target(
                output, payload, receipt_commit=True,
                parent_descriptor=output_parent_descriptor,
                parent_identity=output_parent_identity, directory_lock_held=True,
            ):
                receipt_digest = _store_publication_receipt_locked(
                    freeze, retention_record_digests, raw, raw_identity, repository_root,
                )
            validate_raw_evidence_root(raw, repository_root, **_raw_lock_kwargs(raw_descriptor, raw_identity))
            return {
                "retention_record_digests": retention_record_digests,
                "publication_intent_digest": intent_digest,
                "publication_receipt_digest": receipt_digest,
            }
__all__ = [name for name in globals() if not name.startswith("__")]
