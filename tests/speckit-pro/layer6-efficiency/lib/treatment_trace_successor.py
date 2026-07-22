#!/usr/bin/env python3
"""Treatment-aware capability freeze successor construction."""

from __future__ import annotations

if __package__:
    from .treatment_trace_replay import *
else:
    from treatment_trace_replay import *


def build_treatment_successor(prior_freeze: dict, treatment_bundle: dict, *, published_at: str,
                              manifest_path: Path = MANIFEST_PATH,
                              trusted_qualification_evidence: Mapping[str, dict] | None = None,
                              prior_freeze_predecessor: dict | None = None,
                              expected_prior_telemetry_profile_id: str | None = None,
                              expected_prior_treatment_contract_digest: str | None = None,
                              expected_prior_predecessor_telemetry_profile_id: str | None = None,
                              expected_prior_predecessor_treatment_contract_digest: str | None = None) -> dict:
    manifest = _read_manifest_snapshot(manifest_path)
    validated = _validate_treatment_bundle(
        treatment_bundle, schema_path=SCHEMA_PATH, manifest=manifest,
        trusted_qualification_evidence=trusted_qualification_evidence,
    )
    capability = _capability_module()
    if not isinstance(prior_freeze, dict):
        raise ValueError("prior freeze must be a JSON object")
    try:
        prior_freeze = capability.validate_freeze(
            copy.deepcopy(prior_freeze), manifest,
            predecessor=copy.deepcopy(prior_freeze_predecessor),
            expected_telemetry_profile_id=expected_prior_telemetry_profile_id,
            expected_treatment_contract_digest=expected_prior_treatment_contract_digest,
            expected_predecessor_telemetry_profile_id=(
                expected_prior_predecessor_telemetry_profile_id
            ),
            expected_predecessor_treatment_contract_digest=(
                expected_prior_predecessor_treatment_contract_digest
            ),
        )
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"prior freeze identity or semantics are invalid: {exc}") from exc
    prior_client_id = prior_freeze["client_identity_id"]
    bundle_client_ids = {item["client_identity_id"] for item in validated["telemetry_profile"]}
    bundle_client_ids.update(item["client_identity_id"] for item in validated["controlled_environments"])
    bundle_client_ids.update(item["client_identity_id"] for item in validated["treatment_traces"])
    for trace in validated["treatment_traces"]:
        proof = trace["configured_route_proof"]
        if proof is not None:
            bundle_client_ids.update({proof["client_identity_id"], proof["profile_entry_key"]["client_identity_id"]})
    if bundle_client_ids != {prior_client_id}:
        raise ValueError("treatment bundle client identity does not match the prior freeze")
    prior_snapshot_id = prior_freeze["runtime_capability_snapshot_id"]
    bundle_snapshot_ids = {item["runtime_capability_snapshot_id"] for item in validated["controlled_environments"]}
    bundle_snapshot_ids.update(item["runtime_capability_snapshot_id"] for item in validated["route_resolutions"])
    bundle_snapshot_ids.update(item["objective_binding"]["runtime_capability_snapshot_id"] for item in validated["treatment_traces"])
    if bundle_snapshot_ids != {prior_snapshot_id}:
        raise ValueError("treatment bundle runtime snapshot does not match the prior freeze")
    repository = prior_freeze["runtime_capability_snapshot"]["controlled_repository_snapshot"]
    expected_repository = {(repository["revision"], repository["tree_digest"])}
    bundle_repositories = {(item["repository_revision"], item["repository_tree_digest"]) for item in validated["controlled_environments"]}
    bundle_repositories.update((item["repository_revision"], item["repository_tree_digest"]) for item in validated["treatment_traces"])
    if bundle_repositories != expected_repository:
        raise ValueError("treatment bundle repository binding does not match the prior freeze")
    prior_tuples = {
        (item["candidate_route_id"], item["agent_contract_id"]): (
            item["instruction_sha256"], item["role_instruction_sha256"], item["canonical_effort"]
        )
        for item in prior_freeze["tuple_decisions"]
    }
    for trace in validated["treatment_traces"]:
        objective = trace["objective_binding"]
        instruction_identity = prior_tuples.get((objective["candidate_route_id"], objective["agent_contract_id"]))
        if instruction_identity is None:
            raise ValueError("treatment bundle candidate tuple is not present in the prior freeze")
        if instruction_identity[:2] != (trace["instruction_hash"], trace["instruction_hash"]):
            raise ValueError("treatment bundle instruction identity does not match the prior freeze")
        prior_effort = instruction_identity[2]
        if prior_effort is not None and trace["requested_effort"] != prior_effort:
            raise ValueError("treatment bundle requested effort does not match the prior freeze")
        if prior_effort is None and trace["treatment_disposition"] == "proven":
            raise ValueError("treatment bundle cannot prove an effort absent from the prior freeze")
    successor = copy.deepcopy(prior_freeze); prior_id = prior_freeze["candidate_freeze_id"]
    successor["telemetry_profile_id"] = validated["telemetry_profile_id"]
    successor["treatment_contract_digest"] = validated["treatment_contract_digest"]
    successor["published_at"] = published_at
    successor["supersedes_candidate_freeze_id"] = prior_id
    successor["candidate_freeze_id"] = digest({key: value for key, value in successor.items() if key != "candidate_freeze_id"})
    for key, value in prior_freeze.items():
        if key not in {"candidate_freeze_id", "telemetry_profile_id", "published_at", "supersedes_candidate_freeze_id"} and canonical_bytes(successor[key]) != canonical_bytes(value):
            raise ValueError("treatment successor changed frozen capability evidence")
    capability.validate_freeze(
        successor, manifest, predecessor=prior_freeze,
        expected_telemetry_profile_id=validated["telemetry_profile_id"],
        expected_treatment_contract_digest=validated["treatment_contract_digest"],
        expected_predecessor_telemetry_profile_id=(
            prior_freeze["telemetry_profile_id"]
            if "treatment_contract_digest" in prior_freeze
            else None
        ),
        expected_predecessor_treatment_contract_digest=prior_freeze.get(
            "treatment_contract_digest"
        ),
    )
    if successor["supersedes_candidate_freeze_id"] != prior_id: raise ValueError("treatment successor does not bind the actual prior freeze")
    return successor

__all__ = [name for name in globals() if not name.startswith("__")]
