#!/usr/bin/env python3
"""Fixture loading, capability semantics, and digest authority."""

from __future__ import annotations

from treatment_trace_bundle import *

def validate_treatment_bundle(
    bundle: object, *, schema_path: Path = SCHEMA_PATH, manifest_path: Path = MANIFEST_PATH,
    trusted_qualification_evidence: Mapping[str, dict] | None = None,
) -> dict:
    """Validate a runtime treatment bundle without trusting fixture-local qualification."""
    manifest = _read_manifest_snapshot(manifest_path)
    return _validate_treatment_bundle(
        bundle, schema_path=schema_path, manifest=manifest,
        trusted_qualification_evidence=trusted_qualification_evidence,
    )


def _unique_json(raw: bytes, label: str) -> object:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} must be UTF-8 JSON") from exc

    def unique_object(pairs: list[tuple[str, object]]) -> dict:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"{label} contains a duplicate JSON key")
            value[key] = item
        return value

    try:
        return json.loads(text, object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON") from exc


def _manifest_entries(value: object) -> list[dict[str, str]]:
    manifest = _closed(value, {"schema_version", "fixtures"}, "fixture digest manifest")
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ValueError("fixture digest manifest schema version is unsupported")
    if not isinstance(manifest["fixtures"], list) or len(manifest["fixtures"]) != 2:
        raise ValueError("fixture digest manifest must contain exactly two entries")
    entries: list[dict[str, str]] = []
    paths: list[str] = []
    for raw in manifest["fixtures"]:
        entry = _closed(raw, {"fixture_path", "fixture_digest"}, "fixture digest entry")
        path = _text(entry["fixture_path"], "fixture path")
        parsed = PurePosixPath(path)
        if parsed.is_absolute() or path != parsed.as_posix() or any(part in {".", ".."} for part in parsed.parts):
            raise ValueError("fixture path must be a normalized traversal-free repository-relative path")
        _digest(entry["fixture_digest"], "fixture digest")
        paths.append(path); entries.append({"fixture_path": path, "fixture_digest": entry["fixture_digest"]})
    if len(set(paths)) != len(paths):
        raise ValueError("fixture digest manifest contains a duplicate fixture path")
    if tuple(paths) != REPLAY_FIXTURE_PATHS:
        raise ValueError("fixture digest manifest must use the exact closed fixture path registry")
    return entries


def _fixture_target(repository_root: Path, fixture_path: str) -> Path:
    root = Path(os.path.abspath(repository_root))
    target = Path(os.path.abspath(root / fixture_path))
    if not target.is_relative_to(root):
        raise ValueError("fixture path escapes the repository root")
    return target


def _replay_capability_authority_tuples(capability: object, source_tuples: list[dict]) -> list[dict]:
    tuples = copy.deepcopy(source_tuples)
    for item in tuples:
        instruction = capability.digest(b"fixture-instruction")
        item.update({
            "candidate_route_digest": capability.digest({"route": item["candidate_route_id"]}),
            "source_ref": "fixtures/fixture-agent.toml",
            "source_sha256": capability.digest(b"fixture-agent-source"),
            "instruction_sha256": instruction,
            "role_instruction_sha256": instruction,
            "agent_contract_digest": capability.digest(b"fixture-contract"),
            "official_source_bindings": [{
                "official_source_ledger_id": "OPENAI-DOC-001",
                "source_refresh_digest": capability.digest(b"fixture-source-refresh"),
            }],
            "effort_surface_bindings": [{
                "effort_surface_record_id": "FIXTURE-ESR-001",
                "effort_surface_record_digest": capability.digest(b"fixture-effort-record"),
                "official_source_ledger_id": "OPENAI-DOC-001",
                "source_refresh_digest": capability.digest(b"fixture-source-refresh"),
            }],
        })
    return _capability_authority_tuple_set(tuples)


def _evaluate_replay_capability_case(capability: object, case: dict, client_identity_id: str) -> None:
    observations = [
        capability.fixture_observation(surface, payload, client_identity_id)
        for surface, payload in case["surfaces"].items()
    ]
    options = {"aliases": case.get("aliases", {})}
    if "expected_integrity_digest" in case:
        options["expected_integrity_digest"] = case["expected_integrity_digest"]
    matrix, decisions = capability.evaluate_surface_matrix(
        observations,
        _replay_capability_authority_tuples(capability, case["source_tuples"]),
        **options,
    )
    capability.validate_surface_matrix(matrix)
    if matrix["validity"] != case["expected_validity"]:
        raise ValueError("capability replay case derived validity does not match its expectation")
    derived_decision = decisions[0]["decision"] if decisions else "none"
    if derived_decision != case["expected_decision"]:
        raise ValueError("capability replay case derived decision does not match its expectation")


def _validate_capability_fixture(value: object) -> tuple[dict[str, dict], str]:
    _validate_resource_bounds(value)
    _validate_retained_strings(
        value, "capability replay fixture", reject_two_label_hostnames=True,
    )
    fixture = _closed(value, {
        "schema_version", "sanitizer_version", "raw_evidence_digest",
        "source_refresh_cases", "client_identity", "surface_cases",
    }, "capability replay fixture")
    if fixture["schema_version"] != SCHEMA_VERSION or fixture["sanitizer_version"] != SCHEMA_VERSION:
        raise ValueError("capability replay fixture version is unsupported")
    _digest(fixture["raw_evidence_digest"], "capability fixture raw evidence digest")
    if not isinstance(fixture["source_refresh_cases"], list):
        raise ValueError("capability source-refresh cases must be an array")
    refresh_ids = []
    for item in fixture["source_refresh_cases"]:
        row = _closed(item, {
            "case_id", "status", "body_digest", "claim_bindings", "invalidated_claim_ids",
        }, "capability source-refresh case")
        refresh_ids.append(_text(row["case_id"], "source-refresh case ID"))
        if row["status"] not in {"confirmed_current", "changed", "inaccessible"}:
            raise ValueError("capability source-refresh status is invalid")
        _digest(row["body_digest"], "source-refresh body digest", nullable=row["status"] == "inaccessible")
        _strings(row["claim_bindings"], "source-refresh claim bindings")
        _strings(row["invalidated_claim_ids"], "source-refresh invalidated claims")
    if refresh_ids != ["current", "changed", "inaccessible"]:
        raise ValueError("capability source-refresh fixture does not use the exact case registry")
    identity = _closed(fixture["client_identity"], {
        "reported_version", "build_identifier_kind", "build_identifier", "distribution",
    }, "capability fixture client identity")
    for field in identity:
        _text(identity[field], f"capability client identity {field}")
    if identity["build_identifier_kind"] not in {"vendor_build_id", "executable_sha256", "package_sha256"}:
        raise ValueError("capability client build identity kind is invalid")
    if not isinstance(fixture["surface_cases"], list):
        raise ValueError("capability surface cases must be an array")
    required = {"case_id", "source_tuples", "surfaces", "expected_validity", "expected_decision"}
    allowed = required | {"aliases", "expected_integrity_digest"}
    case_ids = (
        "agreed", "hidden_without_source_admission", "hidden_picker_omission",
        "hidden_state_disagreement", "one_to_one_alias", "surface_disagreement",
        "partial_surface", "duplicate_normalization_key", "aggregate_hash_failure", "zero_eligible",
    )
    cases: dict[str, dict] = {}
    for raw in fixture["surface_cases"]:
        if not isinstance(raw, dict) or not required <= set(raw) or set(raw) - allowed:
            raise ValueError("capability surface case must use its closed shape")
        case_id = _text(raw["case_id"], "capability surface case ID")
        if case_id in cases:
            raise ValueError("duplicate capability surface case ID")
        if raw["expected_validity"] not in {"valid", "invalid"} or raw["expected_decision"] not in {"excluded", "none"}:
            raise ValueError("capability surface case expectation is invalid")
        if not isinstance(raw["source_tuples"], list):
            raise ValueError("capability source tuples must be an array")
        for item in raw["source_tuples"]:
            source = _closed(item, {
                "candidate_route_id", "agent_contract_id", "named_agent", "model", "effort",
                "source_admitted", "authority_reasons",
            }, "capability source tuple")
            for field in ("candidate_route_id", "agent_contract_id", "named_agent", "model", "effort"):
                _text(source[field], f"capability source tuple {field}")
            if not isinstance(source["source_admitted"], bool):
                raise ValueError("capability source admission must be boolean")
            _strings(source["authority_reasons"], "capability authority reasons")
        surfaces = _closed(raw["surfaces"], set(SURFACES), "capability fixture surfaces")
        for surface, item in surfaces.items():
            payload = _closed(item, {"state", "entries"}, f"{surface} fixture payload")
            if payload["state"] not in {"complete", "partial", "unavailable", "unknown"} or not isinstance(payload["entries"], list):
                raise ValueError("capability fixture surface payload is invalid")
            for entry in payload["entries"]:
                keys = {"model", "effort", "available", "hidden"}
                optional = {"machine_id", "raw_label"}
                if not isinstance(entry, dict) or not keys <= set(entry) or set(entry) - keys - optional:
                    raise ValueError("capability fixture surface entry must use its closed shape")
                _text(entry["model"], "capability fixture model"); _text(entry["effort"], "capability fixture effort")
                if not isinstance(entry["available"], bool) or not isinstance(entry["hidden"], bool):
                    raise ValueError("capability fixture availability values must be boolean")
                for field in optional & set(entry):
                    _text(entry[field], f"capability fixture {field}")
        aliases = raw.get("aliases", {})
        if not isinstance(aliases, dict):
            raise ValueError("capability aliases must be an object")
        for label, item in aliases.items():
            _text(label, "capability alias label")
            alias = _closed(item, {"canonical_model_id", "authority_kind", "authority_surface"}, "capability alias")
            _text(alias["canonical_model_id"], "capability alias model")
            _text(alias["authority_kind"], "capability alias authority kind")
            if alias["authority_surface"] not in SURFACES:
                raise ValueError("capability alias authority surface is invalid")
        if "expected_integrity_digest" in raw:
            _digest(raw["expected_integrity_digest"], "capability expected integrity digest")
        cases[case_id] = raw
    if tuple(cases) != case_ids:
        raise ValueError("capability surface fixture does not use the exact case registry")
    capability = _capability_module()
    identity = capability.build_client_identity(fixture["client_identity"])
    for case in cases.values():
        _evaluate_replay_capability_case(capability, case, identity["client_identity_id"])
    return cases, identity["client_identity_id"]

__all__ = [name for name in globals() if not name.startswith("__")]
