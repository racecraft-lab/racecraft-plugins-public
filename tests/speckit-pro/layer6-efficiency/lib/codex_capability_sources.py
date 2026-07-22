#!/usr/bin/env python3
"""Capability source-manifest and refresh normalization."""

from __future__ import annotations

from codex_capability_io import *

# Exact identity of the published predecessor set; any byte change loses this compatibility boundary.
_LEGACY_SOURCE_REFRESH_SET_DIGEST = "sha256:6f382a11b06df40e03719d713fae09c8d88a9ddb9586b735a48f039ac8505ea9"
_SOURCE_CAPTURE_KEYS = frozenset({
    "official_source_ledger_id", "requested_url", "canonical_url", "retrieved_at",
    "status", "invalidated_claim_ids", "retrieved_body_b64", "retrieved_body_format",
    "bounded_extracts",
})

def _extract_claim_dependencies(source):
    bindings = set(source["claim_bindings"])
    if len(bindings) == 1:
        return {item["extract_sha256"]: set(bindings) for item in source["bounded_extracts"]}
    raw = source.get("extract_claim_dependencies", _MULTI_CLAIM_EXTRACT_DEPENDENCIES.get(source["official_source_ledger_id"], {}))
    return {key: set(value) for key, value in raw.items()}


def _route_claim_dependencies(route, sources_by_id):
    source_ids = route.get("official_source_ledger_ids", [])
    raw = route.get("official_source_claim_dependencies")
    if raw is None:
        dependencies = {}
        for source_id in source_ids:
            bindings = set(sources_by_id[source_id]["claim_bindings"])
            if len(bindings) != 1:
                raise ValueError("multi-claim route source requires explicit route-to-claim dependencies")
            dependencies[source_id] = bindings
        return dependencies
    if not isinstance(raw, dict) or set(raw) != set(source_ids):
        raise ValueError("route-to-claim dependencies must cover every bound source exactly")
    dependencies = {}
    for source_id, claims in raw.items():
        bindings = set(sources_by_id[source_id]["claim_bindings"])
        if not isinstance(claims, list) or not claims or len(claims) != len(set(claims)) or not set(claims) <= bindings:
            raise ValueError("route-to-claim dependency is not bound to its source")
        dependencies[source_id] = set(claims)
    return dependencies


def validate_manifest(manifest, *, allow_synthetic_manifest=False):
    snapshot = manifest.get("snapshot", {})
    if manifest.get("schema_version") != CANONICAL_MANIFEST_SCHEMA_VERSION or snapshot.get("snapshot_id") != CANONICAL_MANIFEST_SNAPSHOT_ID:
        raise ValueError("manifest schema or snapshot identity is not the canonical G56R-001 v3 authority")
    if not allow_synthetic_manifest and digest(manifest) != CANONICAL_MANIFEST_DIGEST:
        raise ValueError("manifest content does not match the canonical G56R-001 v3 authority")
    sources = manifest.get("official_source_ledger", [])
    ids = [row.get("official_source_ledger_id") for row in sources]
    if len(sources) != 22 or len(set(ids)) != 22 or any(not _SOURCE_ID.fullmatch(str(item)) for item in ids):
        raise ValueError("manifest must contain exactly 22 unique current OPENAI-DOC records")
    if any(not isinstance(row.get("claim_bindings"), list) or not row["claim_bindings"] or len(row["claim_bindings"]) != len(set(row["claim_bindings"])) or not all(isinstance(item, str) and _CLAIM_ID.fullmatch(item) for item in row["claim_bindings"]) or not _openai_url(row.get("requested_url")) or not _openai_url(row.get("canonical_url")) for row in sources):
        raise ValueError("every current source requires claim bindings and approved URLs")
    for row in sources:
        extracts = row.get("bounded_extracts", [])
        if not extracts or any(set(item) != {"text", "extract_sha256", "normalization"} or not item["text"] or item["normalization"] != EXTRACT_NORMALIZATION or not _HEX_SHA256.fullmatch(str(item["extract_sha256"])) or hashlib.sha256(item["text"].encode()).hexdigest() != item["extract_sha256"] for item in extracts):
            raise ValueError("every current source requires valid bounded extracts")
        bindings = set(row["claim_bindings"])
        if len(bindings) > 1:
            dependencies = _extract_claim_dependencies(row)
            if set(dependencies) != {item["extract_sha256"] for item in extracts} or set().union(*dependencies.values()) != bindings or any(not claims or not claims <= bindings for claims in dependencies.values()):
                raise ValueError("multi-claim source requires complete extract-to-claim dependencies")
    contracts = manifest.get("agent_contracts", []); contract_ids = [row.get("agent_contract_id") for row in contracts]
    routes = manifest.get("candidate_routes", []); route_ids = [row.get("candidate_route_id") for row in routes]
    invalid_contract_hash = any(not _HEX_SHA256.fullmatch(str(row.get("source_sha256"))) or not _HEX_SHA256.fullmatch(str(row.get("instruction_sha256"))) for row in contracts)
    if len(contracts) != 12 or len(routes) != 23 or len(contract_ids) != len(set(contract_ids)) or len(route_ids) != len(set(route_ids)) or invalid_contract_hash or any(row.get("agent_contract_id") not in set(contract_ids) for row in routes):
        raise ValueError("candidate routes require unique agent-contract owners")
    efforts = manifest.get("effort_surface_records", [])
    effort_ids = [row.get("effort_surface_record_id") for row in efforts]
    if len(efforts) != 5 or len(effort_ids) != len(set(effort_ids)) or any(row.get("official_source_ledger_id") not in set(ids) for row in efforts):
        raise ValueError("manifest must contain exactly five effort-surface records")
    contracts_by_id = {row["agent_contract_id"]: row for row in contracts}; effort_id_set = set(effort_ids); source_id_set = set(ids)
    invalid_route_binding = any(
        not _HEX_SHA256.fullmatch(str(row.get("role_instruction_sha256")))
        or row.get("role_instruction_sha256") != contracts_by_id[row["agent_contract_id"]]["instruction_sha256"]
        or not set(row.get("official_source_ledger_ids", [])) <= source_id_set
        or not set(row.get("effort_surface_record_ids", [])) <= effort_id_set
        or len(row.get("official_source_ledger_ids", [])) != len(set(row.get("official_source_ledger_ids", [])))
        or len(row.get("effort_surface_record_ids", [])) != len(set(row.get("effort_surface_record_ids", [])))
        for row in routes
    )
    if invalid_route_binding: raise ValueError("candidate route authority binding is invalid")
    sources_by_id = {row["official_source_ledger_id"]: row for row in sources}
    for route in routes:
        _route_claim_dependencies(route, sources_by_id)
    quarantined, authoritative, by_record = [], set(), {}
    for row in efforts:
        values = row.get("documented_values", [])
        field = str(row.get("field", "")); codex_selector = str(row.get("surface", "")).startswith("Codex ") and any(name in field for name in ("model_reasoning_effort", "supportedReasoningEfforts", "defaultReasoningEffort"))
        if row.get("support_status") != "documented" or not codex_selector or any(not _token(value) for value in values):
            quarantined.append(str(row.get("effort_surface_record_id")))
        else:
            by_record[row["effort_surface_record_id"]] = set(values); authoritative.update(values)
    return {"current_source_count": 22, "historical_active_count": 0, "effort_surface_count": 5, "quarantined_effort_record_ids": sorted(quarantined), "authoritative_effort_tokens": sorted(authoritative), "authoritative_effort_tokens_by_record": {key: sorted(value) for key, value in by_record.items()}}


def _changed_extract_claims(source, extracts):
    original = source["bounded_extracts"]
    if extracts == original:
        return set()
    bindings = set(source["claim_bindings"])
    if len(bindings) == 1:
        return bindings
    dependencies = _extract_claim_dependencies(source)
    changed = [item for item in original if item not in extracts]
    claims = set().union(*(dependencies[item["extract_sha256"]] for item in changed)) if changed else set()
    return claims or bindings


def _source_capture_digest(rows):
    captured = [
        {key: row[key] for key in _SOURCE_CAPTURE_KEYS}
        for row in rows
    ]
    captured.sort(key=lambda row: row["official_source_ledger_id"])
    return digest(canonical_bytes(captured) + b"\n")


def normalize_source_refreshes(manifest, captured, *, source_capture_digest=None, allow_synthetic_manifest=False):
    validate_manifest(manifest, allow_synthetic_manifest=allow_synthetic_manifest)
    sources = {row["official_source_ledger_id"]: row for row in manifest["official_source_ledger"]}
    actual = [row.get("official_source_ledger_id") for row in captured]
    if len(captured) != 22 or set(actual) != set(sources) or len(set(actual)) != 22 or any(set(row) != _SOURCE_CAPTURE_KEYS for row in captured):
        raise ValueError("source refresh must cover the 22 unique current records")
    actual_capture_digest = _source_capture_digest(captured)
    if source_capture_digest is not None and source_capture_digest != actual_capture_digest:
        raise ValueError("source_capture_digest does not match captured bytes in canonical source-ID order")
    source_capture_digest = actual_capture_digest
    statuses = {"confirmed_current", "changed", "redirected", "inaccessible", "withdrawn", "conflicting"}
    normalized = []
    for item in captured:
        source, status = sources[item["official_source_ledger_id"]], item.get("status")
        if item.get("requested_url") != source.get("requested_url") or not _openai_url(item.get("canonical_url")):
            raise ValueError("captured refresh identity or URL does not match current authority")
        if status not in statuses or not _utc_timestamp(item.get("retrieved_at")):
            raise ValueError("source refresh status or timestamp is invalid")
        bindings = list(source.get("claim_bindings", [])); invalid = list(item.get("invalidated_claim_ids", []))
        if len(invalid) != len(set(invalid)) or not set(invalid) <= set(bindings):
            raise ValueError("claim-scoped invalidation is invalid")
        canonical_changed = item["canonical_url"] != source["canonical_url"]
        if canonical_changed and set(invalid) != set(bindings):
            raise ValueError("canonical URL change must invalidate every bound claim")
        if status in {"inaccessible", "withdrawn", "conflicting"} and set(invalid) != set(bindings):
            raise ValueError("adverse source outcome must invalidate every bound claim")
        body_bytes = _validated_body(item["retrieved_body_b64"], item["retrieved_body_format"], item["bounded_extracts"], item["official_source_ledger_id"])
        body, extracts = (digest(body_bytes), list(item["bounded_extracts"])) if body_bytes is not None else (None, [])
        if body is not None:
            prior_body = f"sha256:{source['body_sha256']}"
            if body != prior_body and set(invalid) != set(bindings):
                raise ValueError("source body change must invalidate every bound claim")
            redirect_with_change = status == "redirected" and source["requested_url"] != item["canonical_url"]
            changed_claims = _changed_extract_claims(source, extracts)
            if changed_claims and (status != "changed" and not redirect_with_change or not changed_claims <= set(invalid)):
                raise ValueError("changed bounded extracts must invalidate dependent claims")
        if body is None and status not in {"inaccessible", "withdrawn", "conflicting"}:
            raise ValueError("a retrieved body is required for this source outcome")
        if body is not None and status in {"confirmed_current", "changed", "redirected"}:
            prior_body = f"sha256:{source['body_sha256']}"
            expected_status = "redirected" if source["requested_url"] != item["canonical_url"] else "changed" if canonical_changed else "confirmed_current" if body == prior_body else "changed"
            if status != expected_status: raise ValueError("source refresh status or timestamp is invalid")
        evidence = {"canonical_url": item["canonical_url"], "retrieved_at": item["retrieved_at"], "body_digest": body, "bounded_extracts": extracts}
        normalized.append({
            "official_source_ledger_id": item["official_source_ledger_id"],
            "requested_url": source["requested_url"], "canonical_url": item["canonical_url"],
            "retrieved_at": item["retrieved_at"], "body_digest": body, "status": status,
            "retrieved_body_b64": item["retrieved_body_b64"],
            "retrieved_body_format": item["retrieved_body_format"],
            "source_capture_digest": source_capture_digest,
            "bounded_extracts": extracts, "retrieval_evidence_digest": digest(evidence),
            "documented_facts": list(source.get("exact_documented_facts", [])),
            "claim_bindings": bindings, "invalidated_claim_ids": invalid,
            "prior_record_digest": digest(source),
        })
    return sorted(normalized, key=lambda row: row["official_source_ledger_id"])


def validate_published_source_refreshes(manifest, refreshes, *, allow_synthetic_manifest=False):
    validate_manifest(manifest, allow_synthetic_manifest=allow_synthetic_manifest); sources = {row["official_source_ledger_id"]: row for row in manifest["official_source_ledger"]}
    if len(refreshes) != 22 or [row.get("official_source_ledger_id") for row in refreshes] != sorted(sources):
        raise ValueError("source refresh must cover the 22 unique current records")
    keys = {"official_source_ledger_id", "requested_url", "canonical_url", "retrieved_at", "body_digest", "status", "source_capture_digest", "bounded_extracts", "retrieval_evidence_digest", "documented_facts", "claim_bindings", "invalidated_claim_ids", "prior_record_digest"}
    statuses = {"confirmed_current", "changed", "redirected", "inaccessible", "withdrawn", "conflicting"}
    exact_legacy_set = digest(refreshes) == _LEGACY_SOURCE_REFRESH_SET_DIGEST
    for item in refreshes:
        source = sources[item["official_source_ledger_id"]]; bindings = source["claim_bindings"]
        if set(item) != keys or item["requested_url"] != source["requested_url"] or not _openai_url(item["canonical_url"]) or not _utc_timestamp(item["retrieved_at"]):
            raise ValueError("source refresh authority fields must be canonical manifest values")
        if item["documented_facts"] != source["exact_documented_facts"] or item["claim_bindings"] != bindings or item["prior_record_digest"] != digest(source):
            raise ValueError("source refresh authority fields must be canonical manifest values")
        _need_digest(item["source_capture_digest"], "source_capture_digest")
        invalid = item["invalidated_claim_ids"]
        if item["status"] not in statuses or len(invalid) != len(set(invalid)) or not set(invalid) <= set(bindings): raise ValueError("source refresh status or invalidation is invalid")
        canonical_changed = item["canonical_url"] != source["canonical_url"]
        if canonical_changed and set(invalid) != set(bindings):
            raise ValueError("canonical URL change must invalidate every bound claim")
        if item["body_digest"] is not None: _need_digest(item["body_digest"], "body_digest")
        elif item["bounded_extracts"]: raise ValueError("bounded extracts require a published body digest")
        for extract in item["bounded_extracts"]:
            if set(extract) != {"text", "extract_sha256", "normalization"} or not isinstance(extract["text"], str) or not extract["text"] or extract["normalization"] != EXTRACT_NORMALIZATION or not _HEX_SHA256.fullmatch(str(extract["extract_sha256"])) or hashlib.sha256(extract["text"].encode()).hexdigest() != extract["extract_sha256"]:
                raise ValueError("published bounded extract identity is invalid")
        if item["status"] in {"confirmed_current", "changed", "redirected"} and (item["body_digest"] is None or not item["bounded_extracts"]):
            raise ValueError("source refresh lacks bounded extract evidence")
        prior_body = f"sha256:{source['body_sha256']}"
        if item["body_digest"] is not None and item["body_digest"] != prior_body and set(invalid) != set(bindings) and not exact_legacy_set:
            raise ValueError("source body change must invalidate every bound claim")
        redirect_with_change = item["status"] == "redirected" and source["requested_url"] != item["canonical_url"]
        changed_claims = _changed_extract_claims(source, item["bounded_extracts"])
        if item["status"] in {"confirmed_current", "changed", "redirected"} and changed_claims and (item["status"] != "changed" and not redirect_with_change or not changed_claims <= set(item["invalidated_claim_ids"])):
            raise ValueError("changed bounded extracts must invalidate dependent claims")
        if item["status"] in {"inaccessible", "withdrawn", "conflicting"} and set(item["invalidated_claim_ids"]) != set(bindings):
            raise ValueError("adverse source outcome must invalidate every bound claim")
        if item["status"] in {"confirmed_current", "changed", "redirected"}:
            prior_body = f"sha256:{source['body_sha256']}"; expected_status = "redirected" if source["requested_url"] != item["canonical_url"] else "changed" if canonical_changed else "confirmed_current" if item["body_digest"] == prior_body else "changed"
            if item["status"] != expected_status: raise ValueError("source refresh status is inconsistent with captured evidence")
        evidence = {"canonical_url": item["canonical_url"], "retrieved_at": item["retrieved_at"], "body_digest": item["body_digest"], "bounded_extracts": item["bounded_extracts"]}
        if item["retrieval_evidence_digest"] != digest(evidence): raise ValueError("source retrieval evidence digest is invalid")
    capture_digests = {row["source_capture_digest"] for row in refreshes}
    if len(capture_digests) != 1:
        raise ValueError("source refreshes must bind one complete raw source capture")
    invalidated = sorted({claim for row in refreshes for claim in row["invalidated_claim_ids"]})
    return {"count": 22, "invalidated_claim_ids": invalidated, "digest": digest(refreshes), "sanitized_refreshes": refreshes}


def validate_source_refreshes(manifest, refreshes, *, allow_synthetic_manifest=False):
    raw_keys = {"official_source_ledger_id", "requested_url", "canonical_url", "retrieved_at", "body_digest", "status", "retrieved_body_b64", "retrieved_body_format", "source_capture_digest", "bounded_extracts", "retrieval_evidence_digest", "documented_facts", "claim_bindings", "invalidated_claim_ids", "prior_record_digest"}
    for item in refreshes:
        if set(item) != raw_keys: raise ValueError("source refresh must retain the closed raw evidence binding")
        body_bytes = _validated_body(item["retrieved_body_b64"], item["retrieved_body_format"], item["bounded_extracts"], item.get("official_source_ledger_id"))
        if item["body_digest"] is None and body_bytes is not None or item["body_digest"] is not None and (body_bytes is None or item["body_digest"] != digest(body_bytes)):
            raise ValueError("source body digest does not match captured evidence")
    sanitized = [{key: item[key] for key in item if key not in {"retrieved_body_b64", "retrieved_body_format"}} for item in refreshes]
    validation = validate_published_source_refreshes(
        manifest, sanitized, allow_synthetic_manifest=allow_synthetic_manifest,
    )
    capture_digests = {item["source_capture_digest"] for item in refreshes}
    if len(capture_digests) != 1 or capture_digests.pop() != _source_capture_digest(refreshes):
        raise ValueError("source refreshes do not bind their canonical raw capture")
    return validation

__all__ = [name for name in globals() if not name.startswith("__")]
