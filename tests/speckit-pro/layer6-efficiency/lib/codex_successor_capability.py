#!/usr/bin/env python3
"""Additive G56R-003 capability publication over immutable G56R-002 evidence."""

from __future__ import annotations

import copy as _copy
import importlib.util as _importlib_util
from pathlib import Path as _Path
from uuid import uuid4 as _uuid4


SUCCESSOR_FREEZE_SCHEMA_VERSION = "successor-capability-freeze.v1"
SUCCESSOR_MUTABLE_FIELDS = (
    "candidate_freeze_id",
    "published_at",
    "supersedes_candidate_freeze_id",
)
TOPOLOGY_CONTROL_FIELDS = (
    "candidate_routes",
    "tuple_decisions",
    "included_candidate_route_ids",
    "excluded_candidates",
    "surface_matrix",
    "surface_matrix_id",
    "runtime_capability_snapshot",
    "runtime_capability_snapshot_id",
    "official_source_refreshes",
    "source_manifest_binding",
    "source_refresh_set_digest",
    "current_ledger_digest",
    "surface_matrix_digest",
)

_REQUEST_KEYS = frozenset({
    "schema_version",
    "predecessor_candidate_freeze_id",
    "client_identity_id",
    "account_identity_id",
    "source_manifest_digest",
    "source_refresh_set_digest",
    "runtime_capability_snapshot_id",
    "catalog_capture",
    "diagnostic_capture_digest",
    "published_at",
    "successor_mutable_fields",
    "diagnostics",
})
_CATALOG_KEYS = frozenset({
    "schema_version",
    "command_contract",
    "client_identity",
    "account_boundary_id",
    "environment_boundary_id",
    "raw_catalog_digest",
    "raw_evidence_ref",
    "parsed_catalog_digest",
    "visible_models",
    "defaults",
    "supported_efforts",
    "effort_normalization_map",
    "collected_at",
    "valid_until",
    "invalidation_triggers",
    "authority",
    "sanitization",
})
_DIAGNOSTIC_KEYS = frozenset({
    "surface",
    "captured_at",
    "reported_effort",
    "diagnostic_fields",
})
_CATALOG_MODEL_KEYS = frozenset({
    "model",
    "default_effort",
    "supported_efforts",
    "catalog_entry_digest",
})
_NORMALIZATION_KEYS = frozenset({
    "raw_effort",
    "canonical_effort",
    "evidence_digest",
    "evidence_ref",
})
_ORDINARY_LABELS = frozenset({"ordinary", "default", "normal", "none"})
_TOPOLOGY_LABELS = frozenset({"ultra"})


def _load_capability_facade():
    module_path = _Path(__file__).resolve().with_name("codex_capabilities.py")
    module_name = f"_g56r_successor_capability_runtime_{_uuid4().hex}"
    spec = _importlib_util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load capability facade from {module_path}")
    module = _importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if _Path(getattr(module, "__file__", "")).resolve(strict=True) != module_path:
        raise RuntimeError("capability facade resolved outside the local checkout")
    return module


_capability = _load_capability_facade()
_internals = _capability.__capability_internal_modules__
_contract = _internals["codex_capability_contract"]
_freeze = _internals["codex_capability_freeze"]
_io = _internals["codex_capability_io"]
_observations = _internals["codex_capability_observations"]
_private = _internals["codex_capability_private"]


def canonical_bytes(value):
    return _capability.canonical_bytes(value)


def digest(value):
    return _capability.digest(value)


def _closed(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"closed {label} shape is required")
    return value


def _need_digest(value, label):
    _contract._need_digest(value, label)
    return value


def _parsed_timestamp(value, label):
    return _contract._parsed_timestamp(value, label)


def _token(value, label):
    if not isinstance(value, str) or not value or not _contract._token(value):
        raise ValueError(f"{label} is invalid")
    return value


def _normalized_label(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is invalid")
    normalized = "-".join(value.strip().lower().split())
    return _token(normalized, label)


def _normalize_diagnostic_effort(value):
    if value is None:
        return None
    normalized = _normalized_label(value, "diagnostic effort")
    return None if normalized in _ORDINARY_LABELS else normalized


def _validate_predecessor(predecessor, manifest):
    if not isinstance(predecessor, dict):
        raise ValueError("prior freeze must be a JSON object")
    try:
        candidate = _capability.validate_freeze(_copy.deepcopy(predecessor), manifest)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"prior freeze identity or semantics are invalid: {exc}") from exc
    if candidate.get("candidate_freeze_id") != digest(
        _freeze._freeze_identity_payload(candidate)
    ):
        raise ValueError("prior freeze identity is invalid")
    return candidate


def _validate_catalog_model(raw):
    entry = _closed(raw, _CATALOG_MODEL_KEYS, "catalog model")
    model = _token(entry["model"], "catalog model")
    default = entry["default_effort"]
    if default is not None:
        _normalized_label(default, "catalog default effort")
    efforts = entry["supported_efforts"]
    if not isinstance(efforts, list) or not efforts:
        raise ValueError("catalog supported efforts must be a non-empty array")
    for effort in efforts:
        _normalized_label(effort, "catalog supported effort")
    expected_digest = digest({
        "model": model,
        "default_effort": default,
        "supported_efforts": efforts,
    })
    if entry["catalog_entry_digest"] != expected_digest:
        raise ValueError("catalog entry digest does not match its parsed fields")
    return _copy.deepcopy(entry)


def _validate_normalization_map(entries, raw_digest, raw_ref):
    if not isinstance(entries, list) or not entries:
        raise ValueError("effort normalization map must be a non-empty array")
    normalized = {}
    validated = []
    for raw in entries:
        entry = _closed(raw, _NORMALIZATION_KEYS, "effort normalization entry")
        label = _normalized_label(entry["raw_effort"], "raw effort")
        canonical = _normalized_label(entry["canonical_effort"], "canonical effort")
        if label in _TOPOLOGY_LABELS:
            raise ValueError("topology-changing effort cannot normalize to an ordinary effort")
        if canonical != "ordinary":
            raise ValueError("only evidence-backed ordinary effort normalization is supported")
        if entry["evidence_digest"] != raw_digest or entry["evidence_ref"] != raw_ref:
            raise ValueError("effort normalization evidence does not bind the raw catalog")
        if label in normalized:
            raise ValueError("effort normalization map contains duplicate raw efforts")
        normalized[label] = canonical
        validated.append(_copy.deepcopy(entry))
    return normalized, validated


def _validate_catalog_capture(raw, predecessor, published_at):
    capture = _closed(raw, _CATALOG_KEYS, "catalog capture")
    if capture["schema_version"] != "codex-debug-models-catalog.v1":
        raise ValueError("catalog capture schema version is unsupported")
    command = _closed(
        capture["command_contract"],
        {"argv", "requires_refresh", "output_format"},
        "catalog command contract",
    )
    if command != {
        "argv": ["codex", "debug", "models"],
        "requires_refresh": True,
        "output_format": "json",
    }:
        raise ValueError("catalog collection command is not the pinned refreshed authority")
    try:
        identity = _capability.build_client_identity(capture["client_identity"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"catalog client identity is invalid: {exc}") from exc
    if identity != predecessor["client_identity"]:
        raise ValueError("catalog client identity does not match the pinned predecessor client")
    _need_digest(capture["account_boundary_id"], "catalog account boundary")
    _need_digest(capture["environment_boundary_id"], "catalog environment boundary")
    raw_digest = _need_digest(capture["raw_catalog_digest"], "raw catalog digest")
    raw_ref = capture["raw_evidence_ref"]
    if raw_ref != f"raw://{raw_digest}":
        raise ValueError("raw catalog evidence reference does not bind its digest")
    _need_digest(capture["parsed_catalog_digest"], "parsed catalog digest")

    collected_at = _parsed_timestamp(capture["collected_at"], "catalog collection timestamp")
    valid_until = _parsed_timestamp(capture["valid_until"], "catalog expiry timestamp")
    if collected_at > published_at or valid_until <= published_at:
        raise ValueError("catalog collection is stale for successor publication")
    authority = _closed(
        capture["authority"], {"collector", "trust", "currentness"}, "catalog authority"
    )
    if authority != {
        "collector": "codex-debug-models",
        "trust": "pinned_client",
        "currentness": "current",
    }:
        raise ValueError("catalog collection authority is untrusted or stale")
    sanitization = _closed(
        capture["sanitization"], {"allowlist_version", "result"}, "catalog sanitization"
    )
    if sanitization != {
        "allowlist_version": "g56r-003-catalog-capture.v1",
        "result": "pass",
    }:
        raise ValueError("catalog capture is not sanitized")

    models = capture["visible_models"]
    if not isinstance(models, list) or not models:
        raise ValueError("catalog visible models must be a non-empty array")
    validated_models = [_validate_catalog_model(item) for item in models]
    model_ids = [item["model"] for item in validated_models]
    if len(model_ids) != len(set(model_ids)):
        raise ValueError("catalog visible models contain duplicates")
    defaults = _closed(capture["defaults"], {"effort"}, "catalog defaults")
    _normalized_label(defaults["effort"], "catalog default effort")
    supported = capture["supported_efforts"]
    if not isinstance(supported, list) or not supported:
        raise ValueError("catalog supported efforts must be a non-empty array")
    for effort in supported:
        _normalized_label(effort, "catalog supported effort")
    aggregate = sorted({
        effort for item in validated_models for effort in item["supported_efforts"]
    })
    if supported != aggregate:
        raise ValueError("catalog supported-effort aggregate does not match model entries")

    normalization, validated_normalization = _validate_normalization_map(
        capture["effort_normalization_map"], raw_digest, raw_ref
    )
    parsed_payload = {
        "visible_models": validated_models,
        "defaults": _copy.deepcopy(defaults),
        "supported_efforts": _copy.deepcopy(supported),
        "effort_normalization_map": validated_normalization,
    }
    if capture["parsed_catalog_digest"] != digest(parsed_payload):
        raise ValueError("parsed catalog digest does not match the sanitized projection")
    triggers = capture["invalidation_triggers"]
    if not isinstance(triggers, list) or not triggers or len(triggers) != len(set(triggers)):
        raise ValueError("catalog invalidation triggers must be a unique non-empty array")
    for trigger in triggers:
        _token(trigger, "catalog invalidation trigger")

    normalized_models = []
    for item in validated_models:
        default_label = (
            "implicit_default"
            if item["default_effort"] is None
            else _normalized_label(item["default_effort"], "catalog default effort")
        )
        canonical_default = normalization.get(default_label)
        normalized_efforts = []
        for effort in item["supported_efforts"]:
            label = _normalized_label(effort, "catalog supported effort")
            normalized_efforts.append(
                "topology-control" if label in _TOPOLOGY_LABELS else normalization.get(label)
            )
        normalized_models.append({
            **item,
            "default_effort": canonical_default,
            "normalized_supported_efforts": normalized_efforts,
        })
    validated = _copy.deepcopy(capture)
    validated["visible_models"] = normalized_models
    validated["effort_normalization_map"] = validated_normalization
    validated["_normalization"] = normalization
    return validated


def _validate_diagnostic_entry(entry, published_at):
    if not isinstance(entry, dict):
        raise ValueError("successor diagnostics must be objects")
    unexpected = set(entry) - _DIAGNOSTIC_KEYS
    if unexpected & set(TOPOLOGY_CONTROL_FIELDS):
        raise ValueError("topology-changing controls are excluded from successor diagnostics")
    if set(entry) != _DIAGNOSTIC_KEYS:
        raise ValueError("successor diagnostic must use the closed shape")
    if entry["surface"] not in _capability.SURFACES:
        raise ValueError("successor diagnostic surface is unsupported")
    if _parsed_timestamp(entry["captured_at"], "diagnostic capture timestamp") > published_at:
        raise ValueError("diagnostic capture timestamp cannot follow publication")
    fields = entry["diagnostic_fields"]
    if not isinstance(fields, dict) or not fields:
        raise ValueError("successor diagnostic fields must be a non-empty object")
    if set(fields) & set(TOPOLOGY_CONTROL_FIELDS):
        raise ValueError("topology-changing controls are excluded from successor diagnostics")
    try:
        _observations._safe_sanitized_value(fields)
    except ValueError as exc:
        raise ValueError(f"successor diagnostic is not sanitized: {exc}") from exc
    return {
        "surface": entry["surface"],
        "captured_at": entry["captured_at"],
        "reported_effort": _normalize_diagnostic_effort(entry["reported_effort"]),
        "diagnostic_fields": _copy.deepcopy(fields),
    }


def validate_successor_request(request, predecessor):
    request = _closed(request, _REQUEST_KEYS, "successor request")
    if request["schema_version"] != SUCCESSOR_FREEZE_SCHEMA_VERSION:
        raise ValueError("closed successor request schema version is required")
    for field in (
        "predecessor_candidate_freeze_id",
        "client_identity_id",
        "account_identity_id",
        "source_manifest_digest",
        "source_refresh_set_digest",
        "runtime_capability_snapshot_id",
        "diagnostic_capture_digest",
    ):
        _need_digest(request[field], field.replace("_", " "))
    if request["predecessor_candidate_freeze_id"] != predecessor.get("candidate_freeze_id"):
        raise ValueError("successor request does not bind the prior freeze")
    if request["client_identity_id"] != predecessor.get("client_identity_id"):
        raise ValueError("successor request client identity does not match predecessor")
    if request["source_manifest_digest"] != predecessor.get(
        "source_manifest_binding", {}
    ).get("manifest_digest"):
        raise ValueError("successor request pinned manifest provenance does not match predecessor")
    if request["source_refresh_set_digest"] != predecessor.get("source_refresh_set_digest"):
        raise ValueError("successor request pinned source provenance does not match predecessor")
    if request["runtime_capability_snapshot_id"] != predecessor.get(
        "runtime_capability_snapshot_id"
    ):
        raise ValueError("successor request predecessor snapshot binding does not match predecessor")
    if list(request["successor_mutable_fields"]) != list(SUCCESSOR_MUTABLE_FIELDS):
        raise ValueError("successor mutable fields are not the closed additive set")
    predecessor_time = _parsed_timestamp(
        predecessor["published_at"], "predecessor publication timestamp"
    )
    published_at = _parsed_timestamp(request["published_at"], "successor publication timestamp")
    if published_at <= predecessor_time:
        raise ValueError("successor publication timestamp must be later than predecessor")
    catalog = _validate_catalog_capture(request["catalog_capture"], predecessor, published_at)
    if request["account_identity_id"] != catalog["account_boundary_id"]:
        raise ValueError("successor request account identity does not match catalog boundary")
    diagnostics = request["diagnostics"]
    if not isinstance(diagnostics, list) or not diagnostics:
        raise ValueError("successor diagnostics must be a non-empty array")
    if request["diagnostic_capture_digest"] != digest(canonical_bytes(diagnostics) + b"\n"):
        raise ValueError("successor diagnostic capture digest does not match diagnostics")
    validated = _copy.deepcopy(request)
    validated["catalog_capture"] = catalog
    validated["diagnostics"] = [
        _validate_diagnostic_entry(item, published_at) for item in diagnostics
    ]
    return validated


def _source_route_rows(manifest, predecessor):
    refreshes = {
        item["official_source_ledger_id"]: item
        for item in predecessor["official_source_refreshes"]
    }
    contracts = {
        item["agent_contract_id"]: item for item in manifest["agent_contracts"]
    }
    effort_records = {
        item["effort_surface_record_id"]: item
        for item in manifest["effort_surface_records"]
    }
    rows = []
    for route in manifest["candidate_routes"]:
        contract = contracts[route["agent_contract_id"]]
        source_bindings = [
            {
                "official_source_ledger_id": source_id,
                "source_refresh_digest": digest(refreshes[source_id]),
            }
            for source_id in route["official_source_ledger_ids"]
            if source_id in refreshes
        ]
        candidate = {
            "candidate_route_id": route["candidate_route_id"],
            "agent_contract_id": route["agent_contract_id"],
            "named_agent": contract["agent_name"],
            "model": route["model_selector"]["requested_value"],
            "effort": route["effort_selector"]["requested_value"],
            "official_source_bindings": source_bindings,
            "effort_surface_bindings": [
                {
                    "effort_surface_record_id": record_id,
                    "effort_surface_record_digest": digest(effort_records[record_id]),
                    "official_source_ledger_id": effort_records[record_id][
                        "official_source_ledger_id"
                    ],
                }
                for record_id in route["effort_surface_record_ids"]
                if record_id in effort_records
            ],
        }
        source_admitted = (
            route.get("candidate_status") == "source_bound_provisional"
            and len(source_bindings) == len(route["official_source_ledger_ids"])
            and len(candidate["effort_surface_bindings"])
            == len(route["effort_surface_record_ids"])
        )
        rows.append((candidate, route, source_admitted))
    return rows


def _catalog_authority(catalog):
    result = {}
    for item in catalog["visible_models"]:
        result[item["model"]] = {
            "ordinary_supported": "ordinary" in item["normalized_supported_efforts"],
            "topology_supported": "topology-control" in item["normalized_supported_efforts"],
            "catalog_entry_digest": item["catalog_entry_digest"],
        }
    return result


def _build_tuple_decisions(predecessor, request, manifest):
    catalog = request["catalog_capture"]
    catalog_by_model = _catalog_authority(catalog)
    normalization = catalog["_normalization"]
    decisions = []
    for candidate, route, source_authoritative in _source_route_rows(manifest, predecessor):
        raw_effort = route["effort_selector"].get("requested_value")
        effort_label = (
            "implicit_default"
            if raw_effort is None
            else _normalized_label(raw_effort, "candidate effort")
        )
        canonical_effort = normalization.get(effort_label)
        reasons = []
        if canonical_effort is None:
            reasons.append("canonical_effort_unknown")
        if not source_authoritative:
            reasons.append("source_not_admitted")
        catalog_entry = catalog_by_model.get(candidate["model"])
        catalog_supported = bool(
            catalog_entry
            and canonical_effort == "ordinary"
            and catalog_entry["ordinary_supported"]
        )
        if not catalog_supported:
            reasons.append("availability_not_proven")
        included = source_authoritative and catalog_supported and not reasons
        decisions.append({
            "candidate_route_id": candidate["candidate_route_id"],
            "canonical_model_id": candidate["model"],
            "canonical_effort": canonical_effort,
            "decision": "included" if included else "excluded",
            "reasons": [] if included else sorted(set(reasons)),
            "source_admitted": source_authoritative,
            "catalog_supported": catalog_supported,
            "official_source_bindings": _copy.deepcopy(
                candidate["official_source_bindings"]
            ),
            "effort_surface_bindings": _copy.deepcopy(
                candidate["effort_surface_bindings"]
            ),
            "catalog_evidence": {
                "raw_catalog_digest": catalog["raw_catalog_digest"],
                "raw_evidence_ref": catalog["raw_evidence_ref"],
                "parsed_catalog_digest": catalog["parsed_catalog_digest"],
                "catalog_entry_digest": (
                    catalog_entry["catalog_entry_digest"] if catalog_entry else None
                ),
            },
        })
    for model, authority in sorted(catalog_by_model.items()):
        if authority["topology_supported"]:
            decisions.append({
                "candidate_route_id": f"catalog-control:{model}:ultra",
                "canonical_model_id": model,
                "canonical_effort": "ultra",
                "decision": "excluded",
                "reasons": ["topology_control_not_candidate_effort"],
                "source_admitted": False,
                "catalog_supported": True,
                "official_source_bindings": [],
                "effort_surface_bindings": [],
                "catalog_evidence": {
                    "raw_catalog_digest": catalog["raw_catalog_digest"],
                    "raw_evidence_ref": catalog["raw_evidence_ref"],
                    "parsed_catalog_digest": catalog["parsed_catalog_digest"],
                    "catalog_entry_digest": authority["catalog_entry_digest"],
                },
            })
    return decisions


def _construct_successor(predecessor, request, manifest):
    decisions = _build_tuple_decisions(predecessor, request, manifest)
    included = [
        item["candidate_route_id"] for item in decisions if item["decision"] == "included"
    ]
    if not included:
        if any(
            "canonical_effort_unknown" in item["reasons"]
            and item["canonical_model_id"] in {
                model["model"] for model in request["catalog_capture"]["visible_models"]
            }
            for item in decisions
        ):
            raise ValueError("canonical effort unknown for the source/runtime intersection")
        raise ValueError("source/runtime intersection is empty")
    catalog = request["catalog_capture"]
    sanitized_catalog = {
        key: _copy.deepcopy(value)
        for key, value in catalog.items()
        if key not in {"_normalization"}
    }
    for item in sanitized_catalog["visible_models"]:
        item.pop("normalized_supported_efforts", None)
    snapshot = {
        "schema_version": "runtime-capability-snapshot.v1",
        "client_identity_id": request["client_identity_id"],
        "source_manifest_digest": request["source_manifest_digest"],
        "source_refresh_set_digest": request["source_refresh_set_digest"],
        "catalog_capture_digest": digest(sanitized_catalog),
        "raw_catalog_digest": catalog["raw_catalog_digest"],
        "parsed_catalog_digest": catalog["parsed_catalog_digest"],
        "supported_tuples": sorted({
            (item["canonical_model_id"], item["canonical_effort"])
            for item in decisions if item["decision"] == "included"
        }),
        "diagnostic_capture_digest": request["diagnostic_capture_digest"],
        "authority_status": "authoritative",
    }
    snapshot["runtime_capability_snapshot_id"] = digest(snapshot)
    result = {
        "schema_version": SUCCESSOR_FREEZE_SCHEMA_VERSION,
        "predecessor_freeze": {
            "candidate_freeze_id": predecessor["candidate_freeze_id"],
            "frozen_payload_digest": digest(predecessor),
            "frozen_payload": _copy.deepcopy(predecessor),
        },
        "source_manifest_binding": _copy.deepcopy(predecessor["source_manifest_binding"]),
        "source_refresh_set_digest": predecessor["source_refresh_set_digest"],
        "catalog_capture": sanitized_catalog,
        "runtime_capability_snapshot": snapshot,
        "runtime_capability_snapshot_id": snapshot["runtime_capability_snapshot_id"],
        "tuple_decisions": decisions,
        "included_candidate_route_ids": included,
        "excluded_candidates": [
            {
                "candidate_route_id": item["candidate_route_id"],
                "reasons": item["reasons"],
            }
            for item in decisions if item["decision"] == "excluded"
        ],
        "snapshot_authority_failures": [],
        "published_at": request["published_at"],
        "supersedes_candidate_freeze_id": predecessor["candidate_freeze_id"],
        "invalidation_triggers": _copy.deepcopy(catalog["invalidation_triggers"]),
    }
    result["candidate_freeze_id"] = digest(result)
    return result


def build_successor_freeze(predecessor, request, *, manifest):
    predecessor = _validate_predecessor(predecessor, manifest)
    if request.get("source_manifest_digest") != digest(manifest):
        raise ValueError("successor request pinned manifest digest does not match the manifest")
    validated_request = validate_successor_request(request, predecessor)
    return _construct_successor(predecessor, validated_request, manifest)


def validate_successor_freeze(successor, predecessor, request, *, manifest):
    predecessor = _validate_predecessor(predecessor, manifest)
    validated_request = validate_successor_request(request, predecessor)
    expected = _construct_successor(predecessor, validated_request, manifest)
    if not isinstance(successor, dict) or canonical_bytes(successor) != canonical_bytes(expected):
        raise ValueError("successor freeze changed authoritative or historical evidence")
    return successor


def publish_successor_freeze(
    predecessor_path,
    request,
    output,
    raw_evidence_root,
    repository_root,
    *,
    manifest,
):
    predecessor_path = _Path(predecessor_path)
    output = _Path(output)
    if predecessor_path.resolve(strict=False) == output.resolve(strict=False):
        raise ValueError("additive successor publication requires a distinct output path")
    predecessor_bytes = _io._read_bounded_regular_file(predecessor_path)
    predecessor = _contract._parse_json_bytes(predecessor_bytes)
    if predecessor_bytes != canonical_bytes(predecessor) + b"\n":
        raise ValueError("prior freeze must be stored as canonical committed JSON bytes")
    raw_digest = request.get("catalog_capture", {}).get("raw_catalog_digest")
    if not isinstance(raw_digest, str):
        raise ValueError("retained raw catalog evidence digest is missing")
    raw_path = _Path(raw_evidence_root) / f"{raw_digest.removeprefix('sha256:')}.json"
    try:
        _, raw_catalog_bytes = _capability.read_content_addressed_private_file(
            raw_path, repository_root, "retained raw catalog evidence"
        )
    except (OSError, ValueError) as exc:
        raise ValueError(f"retained raw catalog evidence is unavailable: {exc}") from exc
    if digest(raw_catalog_bytes) != raw_digest:
        raise ValueError("retained raw catalog evidence digest does not match the request")
    successor = build_successor_freeze(predecessor, request, manifest=manifest)
    successor_bytes = canonical_bytes(successor) + b"\n"
    _private._write_public_append_only_bytes(output, successor_bytes)
    if _io._read_bounded_regular_file(predecessor_path) != predecessor_bytes:
        raise ValueError("predecessor freeze bytes changed during successor publication")
    return {
        "predecessor_candidate_freeze_id": predecessor["candidate_freeze_id"],
        "successor_candidate_freeze_id": successor["candidate_freeze_id"],
        "predecessor_bytes_sha256": digest(predecessor_bytes),
        "successor_bytes_sha256": digest(successor_bytes),
        "raw_catalog_evidence_digest": raw_digest,
        "raw_catalog_evidence_ref": request["catalog_capture"]["raw_evidence_ref"],
    }


globals().pop("annotations", None)

__all__ = (
    "SUCCESSOR_FREEZE_SCHEMA_VERSION",
    "SUCCESSOR_MUTABLE_FIELDS",
    "TOPOLOGY_CONTROL_FIELDS",
    "build_successor_freeze",
    "canonical_bytes",
    "digest",
    "publish_successor_freeze",
    "validate_successor_freeze",
    "validate_successor_request",
)
