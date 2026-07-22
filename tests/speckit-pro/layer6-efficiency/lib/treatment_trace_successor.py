#!/usr/bin/env python3
"""Treatment-aware capability freeze successor construction."""

from __future__ import annotations

if __package__:
    from .treatment_trace_replay import *
else:
    from treatment_trace_replay import *


OBSERVATION_EVIDENCE_VERSION = "treatment-observation-evidence.v1"
CONSUMPTION_EVIDENCE_VERSION = "configured-route-consumption-evidence.v1"
SOURCE_EVIDENCE_VERSION = "treatment-source-evidence.v1"
TREATMENT_EVIDENCE_SET_VERSION = "treatment-evidence-set.v1"


def _parsed_evidence_timestamp(value: object, label: str) -> datetime:
    validated = _timestamp(value, label)
    return datetime.fromisoformat(validated.removesuffix("Z") + "+00:00")


def _trusted_evidence_object(
    evidence: Mapping[str, bytes], key: str, label: str, *, digest_bound: bool,
) -> dict:
    raw = evidence.get(key)
    if not isinstance(raw, bytes):
        raise ValueError(f"trusted {label} bytes are missing")
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError(f"trusted {label} exceeds the maximum size")
    if digest_bound and digest(raw) != key:
        raise ValueError(f"trusted {label} digest does not match its claimed evidence")
    value = _parse_json_bytes(raw)
    if not isinstance(value, dict) or raw != canonical_bytes(value) + b"\n":
        raise ValueError(f"trusted {label} must use canonical JSON bytes")
    _validate_resource_bounds(value)
    _validate_retained_strings(value, f"trusted {label}")
    return value


def _validate_publishable_treatment_evidence(
    bundle: dict, trusted_evidence: Mapping[str, bytes] | None,
) -> str:
    if not isinstance(trusted_evidence, Mapping):
        raise ValueError("treatment successor requires trusted evidence bytes")
    evidence_snapshot = dict(trusted_evidence)
    if any(
        not isinstance(key, str) or not isinstance(value, bytes)
        for key, value in evidence_snapshot.items()
    ):
        raise ValueError("trusted treatment evidence must map string owners to exact bytes")
    expected_keys: set[str] = set()
    observations_by_ref: dict[str, list[dict]] = {}
    for trace in bundle["treatment_traces"]:
        trace_id = trace["objective_binding"]["execution_trace_id"]
        for observation in trace["observations"]:
            evidence_ref = observation["evidence_ref"]
            if evidence_ref is None:
                continue
            expected_keys.add(evidence_ref)
            observations_by_ref.setdefault(evidence_ref, []).append({
                "execution_trace_id": trace_id,
                "field_path": observation["field_path"],
                "observation_state": observation["observation_state"],
                "value": copy.deepcopy(observation["value"]),
                "captured_at": observation["captured_at"],
            })
        proof = trace["configured_route_proof"]
        if proof is None:
            raise ValueError(
                "treatment successor requires a configured-route proof for every trace"
            )
        evidence_digest = proof["consumption_evidence_digest"]
        expected_keys.add(evidence_digest)
        expected_proof = {
            "schema_version": CONSUMPTION_EVIDENCE_VERSION,
            "consumed_configuration": {
                key: copy.deepcopy(value)
                for key, value in proof.items()
                if key not in {"proof_id", "consumption_evidence_digest"}
            },
        }
        actual_proof = _trusted_evidence_object(
            evidence_snapshot, evidence_digest,
            "configured-route consumption evidence", digest_bound=True,
        )
        if actual_proof != expected_proof:
            raise ValueError(
                "configured-route consumption evidence does not bind the claimed proof"
            )
    for evidence_ref, observations in observations_by_ref.items():
        expected_observations = {
            "schema_version": OBSERVATION_EVIDENCE_VERSION,
            "evidence_ref": evidence_ref,
            "observations": sorted(
                observations,
                key=lambda item: (item["execution_trace_id"], item["field_path"]),
            ),
        }
        actual_observations = _trusted_evidence_object(
            evidence_snapshot, evidence_ref, "observation evidence", digest_bound=False,
        )
        if actual_observations != expected_observations:
            raise ValueError("trusted observation evidence does not bind the treatment observations")
    raw_evidence_digest = bundle["fixture_provenance"]["raw_evidence_digest"]
    expected_keys.add(raw_evidence_digest)
    bundle_binding = copy.deepcopy(bundle)
    del bundle_binding["fixture_provenance"]["raw_evidence_digest"]
    expected_source = {
        "schema_version": SOURCE_EVIDENCE_VERSION,
        "sanitized_treatment_bundle_digest": digest(bundle_binding),
    }
    actual_source = _trusted_evidence_object(
        evidence_snapshot, raw_evidence_digest, "treatment source evidence",
        digest_bound=True,
    )
    if actual_source != expected_source:
        raise ValueError("trusted source evidence does not bind the sanitized treatment bundle")
    if set(evidence_snapshot) != expected_keys:
        raise ValueError("trusted treatment evidence contains missing or orphan owners")
    return digest({
        "schema_version": TREATMENT_EVIDENCE_SET_VERSION,
        "evidence_owners": [
            {"evidence_ref": key, "content_digest": digest(evidence_snapshot[key])}
            for key in sorted(expected_keys)
        ],
    })


def build_treatment_successor(prior_freeze: dict, treatment_bundle: dict, *, published_at: str,
                              manifest_path: Path = MANIFEST_PATH,
                              trusted_qualification_evidence: Mapping[str, dict] | None = None,
                              trusted_treatment_evidence: Mapping[str, bytes] | None = None,
                              prior_freeze_predecessor: dict | None = None,
                              prior_freeze_predecessor_lineage: list[dict] | None = None,
                              expected_prior_predecessor_lineage_bindings: list[dict | None] | None = None,
                              expected_prior_telemetry_profile_id: str | None = None,
                              expected_prior_treatment_contract_digest: str | None = None,
                              expected_prior_treatment_evidence_digest: str | None = None,
                              expected_prior_predecessor_telemetry_profile_id: str | None = None,
                              expected_prior_predecessor_treatment_contract_digest: str | None = None,
                              expected_prior_predecessor_treatment_evidence_digest: str | None = None) -> dict:
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
            predecessor_lineage=copy.deepcopy(prior_freeze_predecessor_lineage),
            expected_predecessor_lineage_bindings=copy.deepcopy(
                expected_prior_predecessor_lineage_bindings
            ),
            expected_telemetry_profile_id=expected_prior_telemetry_profile_id,
            expected_treatment_contract_digest=expected_prior_treatment_contract_digest,
            expected_treatment_evidence_digest=expected_prior_treatment_evidence_digest,
            expected_predecessor_telemetry_profile_id=(
                expected_prior_predecessor_telemetry_profile_id
            ),
            expected_predecessor_treatment_contract_digest=(
                expected_prior_predecessor_treatment_contract_digest
            ),
            expected_predecessor_treatment_evidence_digest=(
                expected_prior_predecessor_treatment_evidence_digest
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
    treatment_evidence_times = [
        *(_parsed_evidence_timestamp(item["resolved_at"], "route resolution timestamp") for item in validated["route_resolutions"]),
        *(
            _parsed_evidence_timestamp(observation["captured_at"], "observation capture timestamp")
            for trace in validated["treatment_traces"]
            for observation in trace["observations"]
            if observation["captured_at"] is not None
        ),
    ]
    if treatment_evidence_times and _parsed_evidence_timestamp(
        published_at, "treatment successor publication timestamp",
    ) < max(treatment_evidence_times):
        raise ValueError("treatment successor publication timestamp precedes treatment evidence")
    prior_tuples = {
        (item["candidate_route_id"], item["agent_contract_id"]): item
        for item in prior_freeze["tuple_decisions"]
    }
    for trace in validated["treatment_traces"]:
        objective = trace["objective_binding"]
        prior_tuple = prior_tuples.get((objective["candidate_route_id"], objective["agent_contract_id"]))
        if prior_tuple is None:
            raise ValueError("treatment bundle candidate tuple is not present in the prior freeze")
        if trace["treatment_disposition"] == "proven" and (
            prior_tuple["decision"] != "included"
            or prior_tuple["source_admitted"] is not True
            or prior_tuple["surface_disposition"] != "agreed"
            or prior_tuple["availability_disposition"] != "supported"
            or prior_tuple["exact_treatment_readiness"] != "pending"
        ):
            raise ValueError("treatment bundle cannot prove a non-executable prior tuple")
        if (prior_tuple["instruction_sha256"], prior_tuple["role_instruction_sha256"]) != (
            trace["instruction_hash"], trace["instruction_hash"],
        ):
            raise ValueError("treatment bundle instruction identity does not match the prior freeze")
        prior_effort = prior_tuple["canonical_effort"]
        if prior_effort is not None and trace["requested_effort"] != prior_effort:
            raise ValueError("treatment bundle requested effort does not match the prior freeze")
        if prior_effort is None and trace["treatment_disposition"] == "proven":
            raise ValueError("treatment bundle cannot prove an effort absent from the prior freeze")
    treatment_evidence_digest = _validate_publishable_treatment_evidence(
        validated, trusted_treatment_evidence,
    )
    successor = copy.deepcopy(prior_freeze); prior_id = prior_freeze["candidate_freeze_id"]
    successor["telemetry_profile_id"] = validated["telemetry_profile_id"]
    successor["treatment_contract_digest"] = validated["treatment_contract_digest"]
    successor["treatment_evidence_digest"] = treatment_evidence_digest
    successor["published_at"] = published_at
    successor["supersedes_candidate_freeze_id"] = prior_id
    successor["candidate_freeze_id"] = digest({key: value for key, value in successor.items() if key != "candidate_freeze_id"})
    for key, value in prior_freeze.items():
        if key not in {"candidate_freeze_id", "telemetry_profile_id", "treatment_contract_digest", "treatment_evidence_digest", "published_at", "supersedes_candidate_freeze_id"} and canonical_bytes(successor[key]) != canonical_bytes(value):
            raise ValueError("treatment successor changed frozen capability evidence")
    successor_lineage = list(copy.deepcopy(prior_freeze_predecessor_lineage) or [])
    successor_lineage_bindings = list(
        copy.deepcopy(expected_prior_predecessor_lineage_bindings) or []
    )
    if prior_freeze_predecessor is not None:
        successor_lineage.append(copy.deepcopy(prior_freeze_predecessor))
        predecessor_binding = (
            None
            if expected_prior_predecessor_telemetry_profile_id is None
            and expected_prior_predecessor_treatment_contract_digest is None
            and expected_prior_predecessor_treatment_evidence_digest is None
            else {
                "telemetry_profile_id": expected_prior_predecessor_telemetry_profile_id,
                "treatment_contract_digest": expected_prior_predecessor_treatment_contract_digest,
                "treatment_evidence_digest": expected_prior_predecessor_treatment_evidence_digest,
            }
        )
        successor_lineage_bindings.append(predecessor_binding)
    capability.validate_freeze(
        successor, manifest, predecessor=prior_freeze,
        predecessor_lineage=successor_lineage,
        expected_predecessor_lineage_bindings=successor_lineage_bindings,
        expected_telemetry_profile_id=validated["telemetry_profile_id"],
        expected_treatment_contract_digest=validated["treatment_contract_digest"],
        expected_treatment_evidence_digest=treatment_evidence_digest,
        expected_predecessor_telemetry_profile_id=(
            prior_freeze["telemetry_profile_id"]
            if "treatment_contract_digest" in prior_freeze
            else None
        ),
        expected_predecessor_treatment_contract_digest=prior_freeze.get(
            "treatment_contract_digest"
        ),
        expected_predecessor_treatment_evidence_digest=prior_freeze.get(
            "treatment_evidence_digest"
        ),
    )
    if successor["supersedes_candidate_freeze_id"] != prior_id: raise ValueError("treatment successor does not bind the actual prior freeze")
    return successor

__all__ = [name for name in globals() if not name.startswith("__")]
