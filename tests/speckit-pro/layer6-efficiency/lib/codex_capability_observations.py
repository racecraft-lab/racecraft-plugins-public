#!/usr/bin/env python3
"""Client identity, observations, and surface normalization."""

from __future__ import annotations

from codex_capability_sources import *

def build_client_identity(payload):
    keys = ("reported_version", "build_identifier_kind", "build_identifier", "distribution")
    if not isinstance(payload, dict) or set(payload) not in (set(keys), {*keys, "client_identity_id"}):
        raise ValueError("client identity must use the closed v1 shape")
    clean = {key: payload.get(key) for key in keys}
    if any(not value for value in clean.values()) or clean["build_identifier_kind"] not in {"vendor_build_id", "executable_sha256", "package_sha256"}:
        raise ValueError("client identity is incomplete or unsupported")
    _safe_sanitized_value(clean)
    identity = {"client_identity_id": digest(clean), **clean}
    if not _token(clean["distribution"]) or not _LABEL.fullmatch(str(clean["reported_version"])):
        raise ValueError("client version or distribution is invalid")
    if clean["build_identifier_kind"] == "vendor_build_id" and not _IDENTIFIER.fullmatch(str(clean["build_identifier"])):
        raise ValueError("vendor build identifier is invalid")
    if clean["build_identifier_kind"] != "vendor_build_id" and not _DIGEST.fullmatch(str(clean["build_identifier"])):
        raise ValueError("client distribution or immutable build identifier is invalid")
    if payload.get("client_identity_id", identity["client_identity_id"]) != identity["client_identity_id"]:
        raise ValueError("client_identity_id does not match its canonical payload")
    return identity


def build_repository_binding(revision, tree_object):
    if not _GIT_OBJECT.fullmatch(str(revision)) or not _GIT_OBJECT.fullmatch(str(tree_object)):
        raise ValueError("repository revision and tree object must be immutable Git object IDs")
    payload = {
        "revision": revision,
        "tree_object": tree_object,
        "tree_digest": digest({"git_tree_object": tree_object}),
        "evidence_ref": f"git-object://{revision}/{tree_object}",
    }
    return {"repository_binding_id": digest(payload), **payload}


def validate_repository_binding(binding):
    keys = {"repository_binding_id", "revision", "tree_object", "tree_digest", "evidence_ref"}
    if not isinstance(binding, dict) or set(binding) != keys:
        raise ValueError("repository binding must use the closed v1 shape")
    expected = build_repository_binding(binding["revision"], binding["tree_object"])
    if binding != expected:
        raise ValueError("repository binding does not match its revision and tree evidence")
    return binding


def repository_binding_from_checkout(repository_root):
    def status():
        completed = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=repository_root, capture_output=True, text=True, timeout=5,
            check=False,
        )
        if completed.returncode:
            raise ValueError("active checkout cleanliness is unavailable")
        return completed.stdout

    if status():
        raise ValueError("active checkout must be clean before collection")
    values = []
    for revision in ("HEAD",):
        completed = subprocess.run(
            ["git", "rev-parse", revision], cwd=repository_root, capture_output=True,
            text=True, timeout=5, check=False,
        )
        value = completed.stdout.strip()
        if completed.returncode or not _GIT_OBJECT.fullmatch(value):
            raise ValueError("active checkout revision/tree binding is unavailable")
        values.append(value)
    resolved_revision = values[0]
    completed = subprocess.run(
        ["git", "rev-parse", f"{resolved_revision}^{{tree}}"], cwd=repository_root,
        capture_output=True, text=True, timeout=5, check=False,
    )
    tree_object = completed.stdout.strip()
    if completed.returncode or not _GIT_OBJECT.fullmatch(tree_object):
        raise ValueError("active checkout revision/tree binding is unavailable")
    values.append(tree_object)
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository_root, capture_output=True,
        text=True, timeout=5, check=False,
    )
    if completed.returncode or completed.stdout.strip() != resolved_revision:
        raise ValueError("active checkout changed during collection binding")
    if status():
        raise ValueError("active checkout changed during collection binding")
    return build_repository_binding(*values)


def validate_work_item(work_item):
    if not isinstance(work_item, dict) or set(work_item) != {"kind", "id"} or work_item.get("kind") not in {"task", "fixture", "objective"} or not _WORK_ITEM_ID.fullmatch(str(work_item.get("id"))):
        raise ValueError("work item must use the closed task/fixture/objective shape")
    return work_item


def _safe_sanitized_value(value, pseudonym_fields=frozenset(), *, require_generated=False):
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ValueError("sanitized output contains a non-string JSON object key")
            lowered = str(key).lower()
            sensitive = any(part in lowered for part in _FORBIDDEN_KEY_PARTS)
            if key in pseudonym_fields:
                if require_generated and nested != f"fixture-{key}":
                    raise ValueError("sanitized pseudonym does not match its declared field")
                continue
            if sensitive:
                raise ValueError("sanitized output contains a forbidden sensitive field")
            _safe_sanitized_value(nested)
    elif isinstance(value, list):
        for nested in value: _safe_sanitized_value(nested)
    elif isinstance(value, str) and (value.startswith(("/", "\\")) or "://" in value or re.match(r"^[A-Za-z]:[\\/]", value)):
        raise ValueError("sanitized output contains a path or remote locator")
    elif value is not None and type(value) not in {str, int, float, bool}:
        raise ValueError("sanitized output contains a non-JSON container type")


def sanitize(record, profile):
    if profile not in _SANITIZER_PROFILES or not isinstance(record, dict):
        raise ValueError("sanitizer profile is unknown")
    allowlist, pseudonym_fields, strict = _SANITIZER_PROFILES[profile]
    if strict and set(record) - set(allowlist): raise ValueError("surface entry contains undeclared fields")
    selected = {key: record[key] for key in sorted(set(record) & set(allowlist))}
    _safe_sanitized_value(selected, pseudonym_fields)
    result = {
        key: f"fixture-{key}" if key in pseudonym_fields else value
        for key, value in selected.items()
    }
    _safe_sanitized_value(result, pseudonym_fields, require_generated=True)
    return result


def _clean_entry(raw):
    raw = sanitize(raw, "surface_entry")
    if not {"model", "effort", "available", "hidden"} <= set(raw):
        raise ValueError("surface entry contains undeclared or missing fields")
    if not isinstance(raw["model"], str) or not _LABEL.fullmatch(raw["model"]) or not _token(raw["effort"]):
        raise ValueError("surface entry model or effort is invalid")
    if not isinstance(raw["available"], bool) or not isinstance(raw["hidden"], bool):
        raise ValueError("surface entry availability fields must be boolean")
    if "machine_id" in raw and not _token(raw["machine_id"]): raise ValueError("surface entry machine identifier is invalid")
    if "raw_label" in raw and (not isinstance(raw["raw_label"], str) or not _LABEL.fullmatch(raw["raw_label"])): raise ValueError("surface entry raw label is invalid")
    if "capabilities" in raw and (not isinstance(raw["capabilities"], list) or not all(_token(value) for value in raw["capabilities"])):
        raise ValueError("surface entry capabilities are invalid")
    return {key: raw[key] for key in sorted(raw)}


def _observation_payload(observation):
    return {key: observation[key] for key in sorted(_OBSERVATION_KEYS - {"surface_observation_id"})}


def _unknown_capture_record(surface, client_identity_id, repository_binding, work_item, captured_at):
    repository = validate_repository_binding(repository_binding); work_item = validate_work_item(work_item)
    if surface not in SURFACES or not _DIGEST.fullmatch(str(client_identity_id)) or not _utc_timestamp(captured_at):
        raise ValueError("unknown capture binding is invalid")
    return {
        "schema_version": SCHEMA_VERSION, "surface": surface, "client_identity_id": client_identity_id,
        "repository_binding_id": repository["repository_binding_id"], "work_item": work_item,
        "collection_method_id": "unknown-observation-v1", "outcome": "no_approved_live_collector",
        "captured_at": captured_at,
    }


def _collection_authority(observation):
    repository = validate_repository_binding(observation["repository_binding"])
    work_item = validate_work_item(observation["work_item"])
    shared = {"repository_binding_id": repository["repository_binding_id"], "work_item": work_item}
    method = observation["collection_method_id"]
    if method == "fixture-enumeration-v1":
        expected = digest({"include_hidden": observation["surface"] == "app_server", **shared})
        authority = "synthetic"
    elif method == "unknown-observation-v1":
        expected = digest({"reason": "no_approved_live_collector", "surface": observation["surface"], **shared})
        authority = "non_authoritative"
        if observation["completeness_state"] != "unknown" or observation["entries"]:
            raise ValueError("unknown observation method cannot carry discovered entries")
    else:
        raise ValueError("collection method is not in the closed registry")
    if observation["method_inputs_digest"] != expected:
        raise ValueError("collection method inputs do not match the closed registry")
    return authority


def validate_observation(observation):
    if not isinstance(observation, dict) or set(observation) != _OBSERVATION_KEYS:
        raise ValueError("surface observation must use the closed v1 shape")
    if observation["surface"] not in SURFACES or observation["completeness_state"] not in {"complete", "partial", "unavailable", "unknown"}:
        raise ValueError("unsupported surface observation")
    expected_visibility = {"complete_enumeration": observation["completeness_state"] == "complete"} if observation["surface"] == "interactive_picker" else None
    if observation["visibility_policy"] != expected_visibility:
        raise ValueError("surface collection or visibility policy is invalid")
    if not _utc_timestamp(observation["started_at"]) or not _utc_timestamp(observation["completed_at"]):
        raise ValueError("collection timestamp must be RFC3339 UTC")
    if datetime.fromisoformat(observation["started_at"].replace("Z", "+00:00")) > datetime.fromisoformat(observation["completed_at"].replace("Z", "+00:00")):
        raise ValueError("collection window is reversed")
    for field in ("client_identity_id", "method_inputs_digest", "raw_evidence_digest"):
        _need_digest(observation[field], field)
    if observation["sanitized_evidence_digest"] is not None:
        _need_digest(observation["sanitized_evidence_digest"], "sanitized_evidence_digest")
    if not _RAW_REF.fullmatch(str(observation["raw_evidence_ref"])):
        raise ValueError("raw evidence reference must be content addressed")
    if observation["raw_evidence_ref"] != f"raw://{observation['raw_evidence_digest']}":
        raise ValueError("raw_evidence_ref must match raw_evidence_digest")
    observation["entries"] = [_clean_entry(item) for item in observation["entries"]]
    _collection_authority(observation)
    if observation["collection_method_id"] == "unknown-observation-v1":
        if observation["started_at"] != observation["completed_at"]:
            raise ValueError("unknown observation must use one capture timestamp")
        record = _unknown_capture_record(
            observation["surface"], observation["client_identity_id"], observation["repository_binding"],
            observation["work_item"], observation["started_at"],
        )
        expected_evidence = digest(canonical_bytes(record) + b"\n")
        if observation["raw_evidence_digest"] != expected_evidence or observation["sanitized_evidence_digest"] != expected_evidence:
            raise ValueError("unknown observation evidence does not match its deterministic attempt record")
    if observation["surface_observation_id"] != digest(_observation_payload(observation)):
        raise ValueError("surface observation identity does not match its canonical payload")
    return observation


def fixture_observation(surface, payload, client_identity_id):
    state, entries = payload.get("state", "unknown"), [_clean_entry(item) for item in payload.get("entries", [])]
    if surface not in SURFACES or state not in {"complete", "partial", "unavailable", "unknown"}:
        raise ValueError("unsupported surface observation")
    repository = validate_repository_binding(payload.get("repository_binding", build_repository_binding("0" * 40, "0" * 40)))
    work_item = validate_work_item(payload.get("work_item", {"kind": "fixture", "id": "G56R-002-SYNTHETIC"}))
    evidence = digest({"surface": surface, "state": state, "entries": entries})
    result = {
        "client_identity_id": client_identity_id, "surface": surface,
        "collection_method_id": "fixture-enumeration-v1", "method_inputs_digest": digest({"include_hidden": surface == "app_server", "repository_binding_id": repository["repository_binding_id"], "work_item": work_item}),
        "started_at": "2026-07-16T00:00:00Z", "completed_at": "2026-07-16T00:00:00Z", "completeness_state": state,
        "visibility_policy": {"complete_enumeration": state == "complete"} if surface == "interactive_picker" else None,
        "entries": entries, "raw_evidence_digest": evidence, "raw_evidence_ref": f"raw://{evidence}", "sanitized_evidence_digest": evidence,
        "repository_binding": repository, "work_item": work_item,
    }
    result["surface_observation_id"] = digest(result)
    return validate_observation(result)


def unknown_observation(surface, client_identity_id, repository_binding, work_item, *, raw_evidence_digest=None, captured_at="2026-07-16T00:00:00Z"):
    repository = validate_repository_binding(repository_binding); work_item = validate_work_item(work_item)
    if not _utc_timestamp(captured_at): raise ValueError("unknown observation timestamp must be RFC3339 UTC")
    evidence = digest(canonical_bytes(_unknown_capture_record(surface, client_identity_id, repository, work_item, captured_at)) + b"\n")
    if raw_evidence_digest is not None and raw_evidence_digest != evidence:
        raise ValueError("unknown observation raw evidence does not match its attempt record")
    _need_digest(evidence, "raw_evidence_digest")
    result = {
        "client_identity_id": client_identity_id, "surface": surface,
        "collection_method_id": "unknown-observation-v1",
        "method_inputs_digest": digest({"reason": "no_approved_live_collector", "surface": surface, "repository_binding_id": repository["repository_binding_id"], "work_item": work_item}),
        "started_at": captured_at, "completed_at": captured_at,
        "completeness_state": "unknown", "visibility_policy": {"complete_enumeration": False} if surface == "interactive_picker" else None,
        "entries": [], "raw_evidence_digest": evidence, "raw_evidence_ref": f"raw://{evidence}", "sanitized_evidence_digest": evidence,
        "repository_binding": repository, "work_item": work_item,
    }
    result["surface_observation_id"] = digest(result)
    return validate_observation(result)


def _candidate_tuples(manifest, validation, *, allow_synthetic_manifest=False):
    authority = validate_manifest(manifest, allow_synthetic_manifest=allow_synthetic_manifest)
    sources = {row["official_source_ledger_id"]: row for row in manifest["official_source_ledger"]}; current_ids = set(sources)
    contracts = {row["agent_contract_id"]: row for row in manifest.get("agent_contracts", [])}; effort_records = {row["effort_surface_record_id"]: row for row in manifest["effort_surface_records"]}
    refresh_by_source = {row["official_source_ledger_id"]: row for row in validation["sanitized_refreshes"]}
    efforts_by_record = authority["authoritative_effort_tokens_by_record"]
    route_dependencies = {route["candidate_route_id"]: _route_claim_dependencies(route, sources) for route in manifest.get("candidate_routes", [])}
    def source_adverse_for_route(row, route):
        invalid = set(row["invalidated_claim_ids"])
        dependencies = route_dependencies[route["candidate_route_id"]][row["official_source_ledger_id"]]
        return row["status"] in {"inaccessible", "withdrawn", "conflicting"} or bool(invalid & dependencies)

    tuples = []
    for route in manifest.get("candidate_routes", []):
        model = route.get("model_selector", {}).get("requested_value"); effort = route.get("effort_selector", {}).get("requested_value")
        source_ids = route.get("official_source_ledger_ids", []); reasons = []
        adverse_source_ids = {
            source_id for source_id in source_ids
            if source_adverse_for_route(refresh_by_source[source_id], route)
        }
        if not _token(model) or not source_ids or not set(source_ids) <= current_ids or adverse_source_ids:
            reasons.append("source_not_admitted")
        bound_records = [effort_records[record_id] for record_id in route.get("effort_surface_record_ids", [])]
        supporting = [row for row in bound_records if effort in efforts_by_record.get(row["effort_surface_record_id"], [])]
        valid_supporting = [row for row in supporting if row["official_source_ledger_id"] in set(source_ids) and not source_adverse_for_route(refresh_by_source[row["official_source_ledger_id"]], route)]
        if not _token(effort) or not supporting:
            reasons.append("effort_not_source_admitted")
        elif not valid_supporting: reasons.append("effort_source_not_admitted")
        contract = contracts[route["agent_contract_id"]]
        tuples.append({"candidate_route_id": route["candidate_route_id"], "agent_contract_id": route["agent_contract_id"],
                       "named_agent": contract["agent_name"], "model": model, "effort": effort,
                       "candidate_route_digest": digest(route), "source_ref": contract["source_ref"],
                       "source_sha256": f"sha256:{contract['source_sha256']}", "instruction_sha256": f"sha256:{contract['instruction_sha256']}",
                       "role_instruction_sha256": f"sha256:{route['role_instruction_sha256']}", "agent_contract_digest": digest(contract),
                       "official_source_bindings": [{"official_source_ledger_id": source_id, "source_refresh_digest": digest(refresh_by_source[source_id])} for source_id in sorted(source_ids)],
                       "effort_surface_bindings": sorted(({"effort_surface_record_id": row["effort_surface_record_id"], "effort_surface_record_digest": digest(row), "official_source_ledger_id": row["official_source_ledger_id"], "source_refresh_digest": digest(refresh_by_source[row["official_source_ledger_id"]])} for row in bound_records), key=lambda row: row["effort_surface_record_id"]),
                       "source_admitted": not reasons, "authority_reasons": reasons})
    return _AuthorityTupleSet(tuples)


def candidate_tuples_from_manifest(manifest, refreshes, *, allow_synthetic_manifest=False):
    validation = validate_source_refreshes(manifest, refreshes, allow_synthetic_manifest=allow_synthetic_manifest)
    return _candidate_tuples(manifest, validation, allow_synthetic_manifest=allow_synthetic_manifest)


def candidate_tuples_from_published(manifest, refreshes):
    return _candidate_tuples(manifest, validate_published_source_refreshes(manifest, refreshes))


def _surface_disagreements(indexed, observations_by_surface):
    disagreements = {}
    for key in sorted({key for entries in indexed.values() for key in entries}):
        values = {surface: indexed[surface].get(key) for surface in SURFACES}
        observed = [value for value in values.values() if value is not None]
        availability = {value["available"] for value in observed}
        hidden = {value["hidden"] for value in observed}
        disagreement_class = "hidden_state" if len(hidden) > 1 else "availability" if len(availability) > 1 else None
        if disagreement_class is None:
            continue
        tuple_value = {"model": key[0], "effort": key[1]}
        disagreements[key] = {
            "canonical_tuple": tuple_value,
            "surface_values": values,
            "evidence_refs": {surface: observations_by_surface[surface]["raw_evidence_ref"] for surface in SURFACES},
            "proposed_normalized_key": tuple_value,
            "disagreement_class": disagreement_class,
            "tuple_disposition": "excluded",
        }
    return disagreements


def _surface_index_and_invalidity(observations, normalization_map, normalization_map_id, aggregate_integrity_digest):
    reasons = []
    if len({item["client_identity_id"] for item in observations}) != 1:
        reasons.append("unprovable_shared_client_identity")
    canonical_aliases = [item["canonical_model_id"] for item in normalization_map.values()]
    if len(canonical_aliases) != len(set(canonical_aliases)):
        reasons.append("ambiguous_or_duplicate_normalization_key")
    indexed = {}
    for observation in observations:
        entries = {}
        for raw in observation["entries"]:
            alias = normalization_map.get(raw["model"])
            if alias is not None and "machine_id" in raw and raw["machine_id"] != alias["canonical_model_id"]:
                reasons.append("ambiguous_or_duplicate_normalization_key")
                continue
            key = (alias["canonical_model_id"] if alias is not None else raw["model"], raw["effort"])
            if not all(_token(value) for value in key):
                reasons.append("ambiguous_or_duplicate_normalization_key")
                continue
            if key in entries:
                reasons.append("ambiguous_or_duplicate_normalization_key")
            entries[key] = raw
        indexed[observation["surface"]] = entries
    actual_integrity = digest({"observations": observations, "normalization_map_id": normalization_map_id})
    if aggregate_integrity_digest != actual_integrity:
        reasons.append("aggregate_hash_mismatch")
    return indexed, list(dict.fromkeys(reasons)), actual_integrity

__all__ = [name for name in globals() if not name.startswith("__")]
