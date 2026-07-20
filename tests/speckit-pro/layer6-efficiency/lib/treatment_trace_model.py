#!/usr/bin/env python3
"""Treatment profile, environment, qualification, and resolution validation."""

from __future__ import annotations

from treatment_trace_json_schema import *

def canonical_fixture_bytes(value: object) -> bytes:
    return canonical_bytes(value) + b"\n"


def digest(value: object) -> str:
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def content_id(value: dict, identity_field: str) -> str:
    return digest({key: item for key, item in value.items() if key != identity_field})


def schema_file_digest(path: Path = SCHEMA_PATH) -> str:
    return digest(_read_bounded_regular_file(path))


def execution_trace_identity(trace: dict) -> str:
    objective = trace["objective_binding"]
    return digest({
        "candidate_route_id": objective["candidate_route_id"],
        "agent_contract_id": objective["agent_contract_id"],
        "runtime_capability_snapshot_id": objective["runtime_capability_snapshot_id"],
        "route_resolution_id": objective["route_resolution_id"],
        "experiment_policy_id": objective["experiment_policy_id"],
        "controlled_environment_id": trace["controlled_environment_id"],
        "client_identity_id": trace["client_identity_id"],
        "surface": trace["surface"],
        "repository_revision": trace["repository_revision"],
        "repository_tree_digest": trace["repository_tree_digest"],
        "work_item_kind": trace["work_item_kind"],
        "work_item_id": trace["work_item_id"],
        "context": trace["context"],
    })


def telemetry_profile_id(schema_version: str, profile: list[dict], contract_digest: str) -> str:
    return digest({
        "schema_version": schema_version,
        "telemetry_profile": profile,
        "treatment_contract_digest": contract_digest,
    })


def _closed(value: object, keys: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} must use its closed shape")
    return value


def _text(value: object, label: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _identifier(value: object, label: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or SANITIZED_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must use a bounded sanitized identifier")
    return value


def _correlation_id(value: object, label: str, fixture_prefix: str) -> str:
    fixture = re.fullmatch(rf"{re.escape(fixture_prefix)}-fixture-[A-Za-z0-9._-]{{1,96}}", value) if isinstance(value, str) else None
    if not isinstance(value, str) or DIGEST_RE.fullmatch(value) is None and fixture is None:
        raise ValueError(f"{label} must be a digest or sanitized fixture correlation ID")
    return value


def _evidence_ref(value: object, label: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or EVIDENCE_REF_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must use the sanitized fixture evidence namespace")
    return value


def _digest(value: object, label: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a sha256 digest")
    return value


def _integer(value: object, label: str, *, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _timestamp(value: object, label: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    _text(value, label)
    if RFC3339_UTC_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be an RFC3339 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{label} must be an RFC3339 timestamp") from exc
    if parsed.utcoffset() is None:
        raise ValueError(f"{label} must be an RFC3339 UTC timestamp")
    return value


def _strings(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{label} must be an array of non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} must contain unique values")
    return value


def _identifiers(value: object, label: str) -> list[str]:
    values = _strings(value, label)
    for item in values:
        _identifier(item, label)
    return values


def _profile_key(entry: dict) -> tuple[str, str, str]:
    return entry["client_identity_id"], entry["surface"], entry["field_path"]


def _contains_unknown(value: object) -> bool:
    if value == "unknown": return True
    if isinstance(value, list): return any(_contains_unknown(item) for item in value)
    if isinstance(value, dict): return any(_contains_unknown(item) for item in value.values())
    return False


def _top_level_claim_present(field_path: str, value: object) -> bool:
    if field_path == "reroute.events": return bool(value)
    if field_path == "parent.graph":
        return bool(value["parent_execution_trace_id"] or value["child_execution_trace_ids"])
    if field_path == "lifecycle.validation": return value["status"] != "not_run"
    if field_path == "lifecycle.cancellation": return value["state"] != "not_requested"
    if field_path in INTERNAL_DERIVED_FIELDS: return False
    return value is not None


def profile_entry(profile: list[dict], client_identity_id: str, surface: str, field_path: str) -> dict:
    matches = [item for item in profile if _profile_key(item) == (client_identity_id, surface, field_path)]
    if len(matches) > 1:
        raise ValueError("duplicate telemetry profile key")
    if matches:
        return matches[0]
    return {
        "client_identity_id": client_identity_id, "surface": surface, "field_path": field_path,
        "classification": "undocumented", "official_source_ledger_id": None, "condition": None,
        "completeness_rule": "no_authority",
        "observation_state_rules": {
            "allowed_states": ["undocumented"], "value_rule": "null_only", "evidence_rule": "optional",
        },
        "permitted_claims": [], "prohibited_claims": ["configured_as_effective", "unsupported_platform_value"],
    }


def _validate_profile(profile: object, current_source_ids: frozenset[str]) -> list[dict]:
    if not isinstance(profile, list) or not profile:
        raise ValueError("telemetry profile must be a non-empty array")
    seen: set[tuple[str, str, str]] = set()
    for entry in profile:
        _closed(entry, {
            "client_identity_id", "surface", "field_path", "classification",
            "official_source_ledger_id", "condition", "completeness_rule",
            "observation_state_rules", "permitted_claims", "prohibited_claims",
        }, "telemetry profile entry")
        _digest(entry["client_identity_id"], "telemetry client identity")
        if entry["surface"] not in SURFACES or not isinstance(entry["field_path"], str):
            raise ValueError("telemetry profile surface and field path are invalid")
        key = _profile_key(entry)
        if key in seen:
            raise ValueError("duplicate telemetry profile key")
        seen.add(key)
        if (entry["surface"], entry["field_path"]) not in TELEMETRY_INVENTORY:
            raise ValueError("telemetry profile field is outside the closed inventory")
        classification = entry["classification"]
        if classification not in CLASSIFICATIONS:
            raise ValueError("telemetry profile classification is invalid")
        expected_classification = AUTHORIZED_PROFILE_CLASSIFICATIONS[(entry["surface"], entry["field_path"])]
        if classification != expected_classification:
            raise ValueError("telemetry field does not use its exact field-level classification authority")
        source = entry["official_source_ledger_id"]
        expected_source = AUTHORIZED_PROFILE_SOURCES[(entry["surface"], entry["field_path"])]
        if source != expected_source or (source is not None and source not in current_source_ids):
            raise ValueError("telemetry field does not use its exact field-level source authority")
        if (expected_source is None) != (classification == "undocumented"):
            raise ValueError("telemetry authority and undocumented classification disagree")
        if entry["condition"] != AUTHORIZED_PROFILE_CONDITIONS[(entry["surface"], entry["field_path"])]:
            raise ValueError("telemetry field does not use its exact condition authority")
        if entry["completeness_rule"] != COMPLETENESS_BY_CLASS[classification]:
            raise ValueError("telemetry completeness rule does not match its classification")
        rules = _closed(entry["observation_state_rules"], {"allowed_states", "value_rule", "evidence_rule"}, "observation-state rules")
        allowed = rules["allowed_states"]
        if not isinstance(allowed, list) or not allowed or len(allowed) != len(set(allowed)) or any(item not in OBSERVATION_STATES for item in allowed):
            raise ValueError("observation-state rules must use the closed state inventory")
        null_only = classification in {"unavailable", "not_applicable", "undocumented"}
        expected_rules = {
            "allowed_states": [classification] if null_only else ["observed_value", "explicit_null", "missing"],
            "value_rule": "null_only" if null_only else "typed_when_observed",
            "evidence_rule": "optional" if null_only else "required_when_present",
        }
        if rules != expected_rules:
            raise ValueError("observation-state rules do not match classification semantics")
        permitted = _strings(entry["permitted_claims"], "permitted claims")
        prohibited = _strings(entry["prohibited_claims"], "prohibited claims")
        expected_claim = CLAIM_BY_CLASS.get(classification)
        if permitted != ([expected_claim] if expected_claim else []):
            raise ValueError("telemetry permitted claims do not match classification semantics")
        if prohibited != AUTHORIZED_PROHIBITED_CLAIMS[(entry["surface"], entry["field_path"])]:
            raise ValueError("telemetry prohibited claims do not match field-level authority")
    clients = {item["client_identity_id"] for item in profile}
    if len(clients) != 1:
        raise ValueError("schema v1 telemetry profile must have exactly one client identity owner")
    client = next(iter(clients))
    actual_inventory = {_profile_key(item) for item in profile}
    expected_inventory = {(client, surface, field) for surface, field in TELEMETRY_INVENTORY}
    if actual_inventory != expected_inventory:
        raise ValueError("telemetry profile client does not cover the closed inventory")
    return profile


def _validate_environment(value: object) -> dict:
    env = _closed(value, {
        "controlled_environment_id", "client_identity_id", "surface",
        "runtime_capability_snapshot_id", "repository_revision", "repository_tree_digest",
        "candidate_route_id", "work_item_kind", "work_item_id",
    }, "controlled environment")
    _digest(env["controlled_environment_id"], "controlled environment ID")
    _digest(env["client_identity_id"], "controlled environment client identity")
    _digest(env["runtime_capability_snapshot_id"], "controlled environment snapshot")
    if env["surface"] not in SURFACES:
        raise ValueError("controlled environment surface is invalid")
    if not isinstance(env["repository_revision"], str) or REVISION_RE.fullmatch(env["repository_revision"]) is None:
        raise ValueError("controlled environment repository revision is invalid")
    _digest(env["repository_tree_digest"], "controlled environment repository tree")
    _text(env["candidate_route_id"], "controlled environment candidate route")
    if env["work_item_kind"] not in {"task", "fixture", "objective"}:
        raise ValueError("controlled environment work item kind is invalid")
    _identifier(env["work_item_id"], "controlled environment work item ID")
    if env["controlled_environment_id"] != content_id(env, "controlled_environment_id"):
        raise ValueError("controlled environment ID is not content addressed")
    return env


def _validate_experiment_policy(value: object) -> dict:
    policy = _closed(value, {
        "experiment_policy_id", "owner_spec_id", "candidate_route_id",
        "work_item_kind", "work_item_id", "mutation_class",
    }, "experiment policy")
    _digest(policy["experiment_policy_id"], "experiment policy ID")
    if policy["owner_spec_id"] != "G56R-002": raise ValueError("experiment policy is not owned by G56R-002")
    _text(policy["candidate_route_id"], "experiment policy candidate route")
    if policy["work_item_kind"] not in {"task", "fixture", "objective"}: raise ValueError("experiment policy work item kind is invalid")
    _identifier(policy["work_item_id"], "experiment policy work item ID")
    _text(policy["mutation_class"], "experiment policy mutation class")
    if policy["experiment_policy_id"] != content_id(policy, "experiment_policy_id"):
        raise ValueError("experiment policy ID is not content addressed")
    return policy


def _validate_qualification(value: object) -> dict:
    owner = _closed(value, {
        "qualification_evidence_id", "authority_kind", "owner_spec_id",
        "destination_candidate_route_id", "destination_agent_contract_id",
        "destination_named_agent", "qualification_status", "evidence_digest",
    }, "qualification evidence")
    _digest(owner["qualification_evidence_id"], "qualification evidence ID")
    if owner["authority_kind"] not in {"synthetic_fixture", "owned_external"}:
        raise ValueError("qualification authority kind is invalid")
    if not isinstance(owner["owner_spec_id"], str) or SPEC_ID_RE.fullmatch(owner["owner_spec_id"]) is None:
        raise ValueError("qualification owner spec ID is invalid")
    for field in ("destination_candidate_route_id", "destination_agent_contract_id", "destination_named_agent"):
        _identifier(owner[field], f"qualification {field}")
    if owner["qualification_status"] != "prequalified":
        raise ValueError("qualification status is invalid")
    _digest(owner["evidence_digest"], "qualification evidence digest")
    if owner["qualification_evidence_id"] != content_id(owner, "qualification_evidence_id"):
        raise ValueError("qualification evidence ID is not content addressed")
    return owner


def _validate_trusted_qualification(value: Mapping[str, dict] | None) -> dict[str, dict]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("trusted qualification evidence must be a read-only ID mapping")
    trusted: dict[str, dict] = {}
    for identity, raw in value.items():
        _digest(identity, "trusted qualification mapping key")
        owner = _validate_qualification(copy.deepcopy(raw))
        if owner["qualification_evidence_id"] != identity:
            raise ValueError("trusted qualification mapping key does not match its owner")
        if owner["authority_kind"] != "owned_external" or owner["owner_spec_id"] == "G56R-002":
            raise ValueError("trusted qualification authority must be owned externally")
        trusted[identity] = owner
    return trusted


def _validate_resolution(value: object) -> dict:
    route = _closed(value, {
        "route_resolution_id", "preferred_route_id", "attempted_route_ids",
        "assigned_route_id", "supported_effective_route_id", "fallback_index",
        "fallback_reason", "runtime_capability_snapshot_id", "resolved_at",
    }, "route resolution")
    _digest(route["route_resolution_id"], "route resolution ID")
    for field in ("preferred_route_id", "assigned_route_id"):
        _text(route[field], f"route resolution {field}")
    attempts = _strings(route["attempted_route_ids"], "attempted routes")
    if not attempts:
        raise ValueError("route resolution requires an attempted route")
    index = _integer(route["fallback_index"], "fallback index")
    if index >= len(attempts) or attempts[index] != route["assigned_route_id"]:
        raise ValueError("route resolution fallback index does not select the assigned route")
    if route["preferred_route_id"] != attempts[0]:
        raise ValueError("route resolution preferred route must be the first attempt")
    _text(route["supported_effective_route_id"], "supported effective route", nullable=True)
    _text(route["fallback_reason"], "fallback reason", nullable=True)
    if index == 0 and route["fallback_reason"] is not None:
        raise ValueError("primary route selection cannot carry a fallback reason")
    if index > 0 and route["fallback_reason"] is None:
        raise ValueError("fallback selection requires a reason")
    if route["fallback_reason"] is not None and route["fallback_reason"] not in FALLBACK_REASON_CODES:
        raise ValueError("route fallback reason must use an enumerated code")
    _digest(route["runtime_capability_snapshot_id"], "route resolution snapshot")
    _timestamp(route["resolved_at"], "route resolution timestamp")
    if route["route_resolution_id"] != content_id(route, "route_resolution_id"):
        raise ValueError("route resolution ID is not content addressed")
    return route

__all__ = [name for name in globals() if not name.startswith("__")]
