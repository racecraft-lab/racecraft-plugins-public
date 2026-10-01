"""Codex agent source roster and route-policy manifest: loading, digests and validation."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import stat
import tomllib
from pathlib import Path
from typing import Any

from ..agent_inventory import AGENT_INVENTORY, CODEX_OPTIONAL_AGENT_NAMES, CODEX_REQUIRED_AGENT_NAMES
from ..agent_materialization import materialize_agent_policy
from ..canonical_json import canonical_bytes
from ..envelope import diagnostic, is_diagnostic
from ..trusted_io import is_relative_to, repo_relative, resolve_input_path


if len(CODEX_OPTIONAL_AGENT_NAMES) != 1:
    raise RuntimeError("agent inventory must declare exactly one optional Codex helper")
CODEX_OPTIONAL_HELPER_NAME = CODEX_OPTIONAL_AGENT_NAMES[0]
CODEX_SOURCE_AGENT_TOML_NAMES = tuple(
    sorted((*[f"{name}.toml" for name in CODEX_REQUIRED_AGENT_NAMES], f"{CODEX_OPTIONAL_HELPER_NAME}.toml"))
)
REQUIRED_CODEX_AGENT_NAMES = frozenset(CODEX_SOURCE_AGENT_TOML_NAMES)
SUPPORTED_CODEX_AGENT_MODELS = frozenset({"gpt-6-sol", "gpt-6-luna", "gpt-6-astra"})
CODEX_SOL_SOURCE_MODEL = "gpt-6-sol"
CODEX_LUNA_SOURCE_MODEL = "gpt-6-luna"
CODEX_LUNA_FALLBACK_MODEL = "gpt-6-sol"
CODEX_SOURCE_AGENT_POLICIES = {
    role["name"]: (role["codex"]["model"], role["codex"]["effort"])
    for role in AGENT_INVENTORY["roles"]
    if role["codex"]["implementation"] == "custom_agent"
}
ROUTE_POLICY_MANIFEST_SCHEMA_VERSION = "1.0.0"
ROUTE_POLICY_MANIFEST_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "manifest_id",
        "provenance_id",
        "source_roster",
        "required_agent_policies",
        "optional_helper",
        "bounded_probes",
    }
)
ROUTE_POLICY_SOURCE_ROSTER_KEYS = frozenset({"schema_version", "source_roster_id", "files"})
ROUTE_POLICY_SOURCE_FILE_KEYS = frozenset({"name", "sha256"})
ROUTE_POLICY_REQUIRED_POLICY_KEYS = frozenset(
    {
        "policy_id",
        "agent_name",
        "preferred_route",
        "fallback_routes",
        "required_capabilities",
        "non_route_contract_digest",
    }
)
ROUTE_POLICY_ROUTE_KEYS = frozenset({"route_id", "model", "model_reasoning_effort", "capabilities", "probe_id"})
ROUTE_POLICY_OPTIONAL_HELPER_KEYS = frozenset(
    {"helper_name", "policy_id", "preferred_route", "fallback_routes", "no_helper"}
)
ROUTE_POLICY_NO_HELPER_KEYS = frozenset({"allowed", "reason"})
ROUTE_POLICY_BOUNDED_PROBE_KEYS = frozenset(
    {"probe_id", "candidate_route_id", "purpose", "bounds", "expected_result_shape"}
)
ROUTE_POLICY_SHA256_IDENTITY = re.compile(r"^sha256:[0-9a-f]{64}$")
ROUTE_POLICY_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def codex_plugin_root() -> Path:
    return Path(__file__).resolve().parents[2]


def route_policy_digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_bytes(value)).hexdigest()}"


def invalid_route_policy_manifest(reason: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {"reason": reason}
    if details:
        payload.update(details)
    return diagnostic(
        "invalid_route_policy_manifest",
        "route policy manifest is invalid",
        details=payload,
        remediation_summary="Provide a supported closed route-policy manifest bound to the bundled Codex agent roster.",
        remediation_actions=["Regenerate the route-policy manifest from the current bundled Codex agent source roster."],
    )


def invalid_route_policy_manifest_path(
    raw: Any,
    *,
    reason: str,
    path: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"reason": reason, "path": path or str(raw)}
    if details:
        payload.update(details)
    return diagnostic(
        "invalid_route_policy_manifest_path",
        "route_policy_manifest must point to a trusted regular file inside the current repository",
        details=payload,
        remediation_summary="Use a repository-local manifest file, not inline policy data or an external path.",
        remediation_actions=["Set inputs.route_policy_manifest to a non-symlink JSON file inside the repository."],
    )


def codex_agent_source_roster(source_dir: Path) -> dict[str, Any]:
    if not source_dir.is_dir() or source_dir.is_symlink():
        return diagnostic("missing_agent_bundle", "bundled codex-agents directory is missing or unsafe")
    if any(source_dir.glob("*.md")):
        return diagnostic("legacy_agent_bundle", "bundled codex-agents directory contains legacy Markdown agents")

    source_files = sorted(source_dir.glob("*.toml"), key=lambda path: path.name)
    source_names = [path.name for path in source_files]
    missing = sorted(REQUIRED_CODEX_AGENT_NAMES - set(source_names))
    unexpected = sorted(set(source_names) - REQUIRED_CODEX_AGENT_NAMES)
    if missing or unexpected:
        return diagnostic(
            "incomplete_agent_bundle",
            "bundled Codex agent set does not match the required inventory",
            details={"missing_files": missing, "unexpected_files": unexpected},
            remediation_summary="Restore the complete bundled agent set before installing.",
            remediation_actions=["Repair or reinstall the SpecKit Pro plugin."],
        )

    records: list[dict[str, str]] = []
    try:
        for path in source_files:
            if path.is_symlink() or not path.is_file():
                raise OSError(path.name)
            records.append({"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    except OSError as exc:
        return diagnostic(
            "unsafe_agent_bundle",
            "bundled Codex agent templates could not be read safely",
            details={"error": type(exc).__name__, "message": str(exc)},
        )

    return {
        "schema_version": ROUTE_POLICY_MANIFEST_SCHEMA_VERSION,
        "source_roster_id": route_policy_digest(records),
        "files": records,
    }


def trusted_route_policy_manifest_path(raw: Any, repo_root: Path) -> Path | dict[str, Any]:
    if not isinstance(raw, str) or not raw.strip():
        return invalid_route_policy_manifest_path(raw, reason="manifest_path_required")
    candidate = resolve_input_path(raw, repo_root)
    try:
        metadata = candidate.lstat()
    except OSError as exc:
        return invalid_route_policy_manifest_path(
            raw,
            reason="manifest_unreadable",
            path=candidate.as_posix(),
            details={"error": type(exc).__name__},
        )
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        return invalid_route_policy_manifest_path(raw, reason="manifest_not_regular_file", path=candidate.as_posix())
    resolved = candidate.resolve(strict=False)
    if not is_relative_to(resolved, repo_root):
        return invalid_route_policy_manifest_path(raw, reason="manifest_outside_repository", path=candidate.as_posix())
    return candidate


def load_codex_route_policy_manifest(raw: Any, repo_root: Path, source_dir: Path) -> dict[str, Any]:
    path_result = trusted_route_policy_manifest_path(raw, repo_root)
    if is_diagnostic(path_result):
        return path_result
    manifest_path = path_result

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return invalid_route_policy_manifest("manifest_unreadable_or_malformed", details={"error": type(exc).__name__})
    if not isinstance(manifest, dict):
        return invalid_route_policy_manifest("manifest_not_object")

    validation_result = validate_codex_route_policy_manifest(manifest, source_dir)
    if is_diagnostic(validation_result):
        return validation_result

    source_roster = manifest["source_roster"]
    return {
        "path": repo_relative(manifest_path, repo_root),
        "schema_version": manifest["schema_version"],
        "manifest_id": manifest["manifest_id"],
        "source_roster_id": source_roster["source_roster_id"],
        "provenance_id": manifest["provenance_id"],
        "required_agents": list(CODEX_REQUIRED_AGENT_NAMES),
        "optional_helper": CODEX_OPTIONAL_HELPER_NAME,
        "source_files": [record["name"] for record in source_roster["files"]],
        "required_agent_policies": copy.deepcopy(manifest["required_agent_policies"]),
        "optional_helper_policy": copy.deepcopy(manifest["optional_helper"]),
        "bounded_probes": copy.deepcopy(manifest["bounded_probes"]),
    }


def validate_codex_route_policy_manifest(manifest: dict[str, Any], source_dir: Path) -> dict[str, Any]:
    keys = set(manifest)
    missing = sorted(ROUTE_POLICY_MANIFEST_TOP_LEVEL_KEYS - keys)
    if missing:
        return invalid_route_policy_manifest("missing_top_level_keys", details={"missing": missing})
    unknown = sorted(keys - ROUTE_POLICY_MANIFEST_TOP_LEVEL_KEYS)
    if unknown:
        return invalid_route_policy_manifest("unknown_top_level_keys", details={"unknown": unknown})

    if manifest.get("schema_version") != ROUTE_POLICY_MANIFEST_SCHEMA_VERSION:
        return invalid_route_policy_manifest(
            "unsupported_schema_version",
            details={"schema_version": manifest.get("schema_version")},
        )
    manifest_id = manifest.get("manifest_id")
    if not isinstance(manifest_id, str) or ROUTE_POLICY_SHA256_IDENTITY.fullmatch(manifest_id) is None:
        return invalid_route_policy_manifest("manifest_id_invalid")
    recomputed_manifest_id = route_policy_digest(
        {key: value for key, value in manifest.items() if key != "manifest_id"}
    )
    if manifest_id != recomputed_manifest_id:
        return invalid_route_policy_manifest(
            "manifest_id_mismatch",
            details={"expected_manifest_id": recomputed_manifest_id, "actual_manifest_id": manifest_id},
        )
    if not isinstance(manifest.get("provenance_id"), str) or not manifest["provenance_id"]:
        return invalid_route_policy_manifest("provenance_id_invalid")

    source_result = validate_route_policy_source_roster(manifest.get("source_roster"), source_dir)
    if is_diagnostic(source_result):
        return source_result
    policies_result = validate_route_policy_required_policies(
        manifest.get("required_agent_policies"),
        source_dir,
    )
    if is_diagnostic(policies_result):
        return policies_result
    helper_result = validate_route_policy_optional_helper(manifest.get("optional_helper"))
    if is_diagnostic(helper_result):
        return helper_result
    probes_result = validate_route_policy_bounded_probes(
        manifest.get("bounded_probes"),
        manifest["required_agent_policies"],
        manifest["optional_helper"],
    )
    if is_diagnostic(probes_result):
        return probes_result
    return {}


def validate_route_policy_bounded_probes(
    raw: Any,
    required_policies: dict[str, Any],
    optional_helper: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return invalid_route_policy_manifest("bounded_probes_not_object")

    route_probe_pairs: set[tuple[str, str]] = set()
    admitted_route_ids: set[str] = set()
    route_definitions: dict[str, tuple[str, str, tuple[str, ...], str | None]] = {}
    route_groups = [
        *required_policies.values(),
        optional_helper,
    ]
    for policy in route_groups:
        routes = [policy.get("preferred_route"), *policy.get("fallback_routes", [])]
        for route in routes:
            if not isinstance(route, dict):
                continue
            route_id = route.get("route_id")
            probe_id = route.get("probe_id")
            if isinstance(route_id, str):
                definition = (
                    route["model"],
                    route["model_reasoning_effort"],
                    tuple(sorted(route["capabilities"])),
                    probe_id,
                )
                existing_definition = route_definitions.get(route_id)
                if existing_definition is not None and existing_definition != definition:
                    return invalid_route_policy_manifest(
                        "route_id_definition_mismatch",
                        details={"route_id": route_id},
                    )
                route_definitions[route_id] = definition
                admitted_route_ids.add(route_id)
                if isinstance(probe_id, str):
                    route_probe_pairs.add((probe_id, route_id))

    manifest_probe_pairs: set[tuple[str, str]] = set()
    for key, probe in raw.items():
        if not isinstance(key, str) or not key:
            return invalid_route_policy_manifest("bounded_probe_key_invalid")
        if not isinstance(probe, dict):
            return invalid_route_policy_manifest("bounded_probe_not_object", details={"probe_id": key})
        keys = set(probe)
        if keys != ROUTE_POLICY_BOUNDED_PROBE_KEYS:
            return invalid_route_policy_manifest(
                "bounded_probe_schema_mismatch",
                details={
                    "probe_id": key,
                    "missing": sorted(ROUTE_POLICY_BOUNDED_PROBE_KEYS - keys),
                    "unknown": sorted(keys - ROUTE_POLICY_BOUNDED_PROBE_KEYS),
                },
            )
        if probe.get("probe_id") != key:
            return invalid_route_policy_manifest(
                "bounded_probe_id_mismatch",
                details={"probe_key": key, "probe_id": probe.get("probe_id")},
            )
        candidate_route_id = probe.get("candidate_route_id")
        if not isinstance(candidate_route_id, str) or not candidate_route_id:
            return invalid_route_policy_manifest("bounded_probe_candidate_route_id_invalid", details={"probe_id": key})
        if candidate_route_id not in admitted_route_ids:
            return invalid_route_policy_manifest(
                "bounded_probe_candidate_not_admitted",
                details={"probe_id": key, "candidate_route_id": candidate_route_id},
            )
        if not isinstance(probe.get("purpose"), str) or not probe["purpose"]:
            return invalid_route_policy_manifest("bounded_probe_purpose_invalid", details={"probe_id": key})
        if not isinstance(probe.get("bounds"), dict) or not probe["bounds"]:
            return invalid_route_policy_manifest("bounded_probe_bounds_invalid", details={"probe_id": key})
        if not isinstance(probe.get("expected_result_shape"), dict) or not probe["expected_result_shape"]:
            return invalid_route_policy_manifest("bounded_probe_expected_result_shape_invalid", details={"probe_id": key})
        manifest_probe_pairs.add((key, candidate_route_id))

    if manifest_probe_pairs != route_probe_pairs:
        return invalid_route_policy_manifest(
            "bounded_probe_route_binding_mismatch",
            details={
                "missing": sorted(route_probe_pairs - manifest_probe_pairs),
                "unreferenced": sorted(manifest_probe_pairs - route_probe_pairs),
            },
        )
    return {}


def validate_route_policy_source_roster(raw: Any, source_dir: Path) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return invalid_route_policy_manifest("source_roster_not_object")
    keys = set(raw)
    if keys != ROUTE_POLICY_SOURCE_ROSTER_KEYS:
        return invalid_route_policy_manifest(
            "source_roster_schema_mismatch",
            details={
                "missing": sorted(ROUTE_POLICY_SOURCE_ROSTER_KEYS - keys),
                "unknown": sorted(keys - ROUTE_POLICY_SOURCE_ROSTER_KEYS),
            },
        )
    if raw.get("schema_version") != ROUTE_POLICY_MANIFEST_SCHEMA_VERSION:
        return invalid_route_policy_manifest(
            "source_roster_schema_version_mismatch",
            details={"schema_version": raw.get("schema_version")},
        )
    files = raw.get("files")
    if not isinstance(files, list):
        return invalid_route_policy_manifest("source_roster_files_not_array")
    normalized: list[dict[str, str]] = []
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            return invalid_route_policy_manifest("source_roster_file_not_object", details={"index": index})
        item_keys = set(item)
        if item_keys != ROUTE_POLICY_SOURCE_FILE_KEYS:
            return invalid_route_policy_manifest(
                "source_roster_file_schema_mismatch",
                details={
                    "index": index,
                    "missing": sorted(ROUTE_POLICY_SOURCE_FILE_KEYS - item_keys),
                    "unknown": sorted(item_keys - ROUTE_POLICY_SOURCE_FILE_KEYS),
                },
            )
        name = item.get("name")
        digest = item.get("sha256")
        if not isinstance(name, str) or not name:
            return invalid_route_policy_manifest("source_roster_file_name_invalid", details={"index": index})
        if not isinstance(digest, str) or ROUTE_POLICY_SHA256_HEX.fullmatch(digest) is None:
            return invalid_route_policy_manifest("source_roster_file_digest_invalid", details={"index": index})
        normalized.append({"name": name, "sha256": digest})
    source_roster_id = raw.get("source_roster_id")
    recomputed_source_roster_id = route_policy_digest(normalized)
    if source_roster_id != recomputed_source_roster_id:
        return invalid_route_policy_manifest(
            "source_roster_id_mismatch",
            details={"expected_source_roster_id": recomputed_source_roster_id, "actual_source_roster_id": source_roster_id},
        )

    current_roster = codex_agent_source_roster(source_dir)
    if is_diagnostic(current_roster):
        return current_roster
    current_files = current_roster["files"]
    if normalized != current_files:
        return invalid_route_policy_manifest(
            "source_roster_files_mismatch",
            details={
                "expected_files": [record["name"] for record in current_files],
                "actual_files": [record["name"] for record in normalized],
            },
        )
    return {}


def validate_route_policy_required_policies(raw: Any, source_dir: Path) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return invalid_route_policy_manifest("required_agent_policies_not_object")
    keys = set(raw)
    expected = set(CODEX_REQUIRED_AGENT_NAMES)
    if keys != expected:
        return invalid_route_policy_manifest(
            "required_agent_policy_roster_mismatch",
            details={"missing": sorted(expected - keys), "unexpected": sorted(keys - expected)},
        )
    for agent_name in CODEX_REQUIRED_AGENT_NAMES:
        policy = raw.get(agent_name)
        if not isinstance(policy, dict):
            return invalid_route_policy_manifest("required_agent_policy_not_object", details={"agent_name": agent_name})
        policy_keys = set(policy)
        if policy_keys != ROUTE_POLICY_REQUIRED_POLICY_KEYS:
            return invalid_route_policy_manifest(
                "required_agent_policy_schema_mismatch",
                details={
                    "agent_name": agent_name,
                    "missing": sorted(ROUTE_POLICY_REQUIRED_POLICY_KEYS - policy_keys),
                    "unknown": sorted(policy_keys - ROUTE_POLICY_REQUIRED_POLICY_KEYS),
                },
            )
        if not isinstance(policy.get("policy_id"), str) or not policy["policy_id"]:
            return invalid_route_policy_manifest(
                "required_agent_policy_id_invalid",
                details={"agent_name": agent_name},
            )
        if policy.get("agent_name") != agent_name:
            return invalid_route_policy_manifest(
                "required_agent_policy_name_mismatch",
                details={"agent_name": agent_name, "policy_agent_name": policy.get("agent_name")},
            )
        required_capabilities = policy.get("required_capabilities")
        if (
            not isinstance(required_capabilities, list)
            or any(not isinstance(item, str) or not item for item in required_capabilities)
            or len(set(required_capabilities)) != len(required_capabilities)
        ):
            return invalid_route_policy_manifest(
                "required_agent_capabilities_invalid",
                details={"agent_name": agent_name},
            )
        declared_non_route_digest = policy.get("non_route_contract_digest")
        if (
            not isinstance(declared_non_route_digest, str)
            or ROUTE_POLICY_SHA256_IDENTITY.fullmatch(declared_non_route_digest) is None
        ):
            return invalid_route_policy_manifest(
                "required_agent_non_route_contract_digest_invalid",
                details={"agent_name": agent_name},
            )
        try:
            canonical_non_route_digest = materialize_agent_policy(
                source_relative_path=f"speckit-pro/codex-agents/{agent_name}.toml",
                source_bytes=(source_dir / f"{agent_name}.toml").read_bytes(),
            ).non_route_fields_digest
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, ValueError) as exc:
            return invalid_route_policy_manifest(
                "required_agent_non_route_contract_unavailable",
                details={"agent_name": agent_name, "error": type(exc).__name__},
            )
        if declared_non_route_digest != canonical_non_route_digest:
            return invalid_route_policy_manifest(
                "required_agent_non_route_contract_digest_mismatch",
                details={
                    "agent_name": agent_name,
                    "expected_digest": canonical_non_route_digest,
                    "actual_digest": declared_non_route_digest,
                },
            )
        route_result = validate_route_policy_route(policy.get("preferred_route"), context=f"{agent_name}.preferred_route")
        if is_diagnostic(route_result):
            return route_result
        fallback_routes = policy.get("fallback_routes")
        if not isinstance(fallback_routes, list):
            return invalid_route_policy_manifest("required_agent_policy_fallback_routes_not_array", details={"agent_name": agent_name})
        for index, route in enumerate(fallback_routes):
            route_result = validate_route_policy_route(route, context=f"{agent_name}.fallback_routes[{index}]")
            if is_diagnostic(route_result):
                return route_result
    return {}


def validate_route_policy_optional_helper(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return invalid_route_policy_manifest("optional_helper_not_object")
    keys = set(raw)
    if keys != ROUTE_POLICY_OPTIONAL_HELPER_KEYS:
        return invalid_route_policy_manifest(
            "optional_helper_schema_mismatch",
            details={
                "missing": sorted(ROUTE_POLICY_OPTIONAL_HELPER_KEYS - keys),
                "unknown": sorted(keys - ROUTE_POLICY_OPTIONAL_HELPER_KEYS),
            },
        )
    if raw.get("helper_name") != CODEX_OPTIONAL_HELPER_NAME:
        return invalid_route_policy_manifest(
            "optional_helper_mismatch",
            details={"expected": CODEX_OPTIONAL_HELPER_NAME, "actual": raw.get("helper_name")},
        )
    policy_id = raw.get("policy_id")
    if policy_id is not None and (not isinstance(policy_id, str) or not policy_id):
        return invalid_route_policy_manifest("optional_helper_policy_id_invalid")
    preferred = raw.get("preferred_route")
    if preferred is not None:
        route_result = validate_route_policy_route(preferred, context="optional_helper.preferred_route")
        if is_diagnostic(route_result):
            return route_result
    fallback_routes = raw.get("fallback_routes")
    if not isinstance(fallback_routes, list):
        return invalid_route_policy_manifest("optional_helper_fallback_routes_not_array")
    for index, route in enumerate(fallback_routes):
        route_result = validate_route_policy_route(route, context=f"optional_helper.fallback_routes[{index}]")
        if is_diagnostic(route_result):
            return route_result
    if policy_id is None and (preferred is not None or fallback_routes):
        return invalid_route_policy_manifest("optional_helper_policy_id_required_for_routes")
    no_helper = raw.get("no_helper")
    if not isinstance(no_helper, dict):
        return invalid_route_policy_manifest("optional_helper_no_helper_not_object")
    no_helper_keys = set(no_helper)
    if no_helper_keys != ROUTE_POLICY_NO_HELPER_KEYS:
        return invalid_route_policy_manifest(
            "optional_helper_no_helper_schema_mismatch",
            details={
                "missing": sorted(ROUTE_POLICY_NO_HELPER_KEYS - no_helper_keys),
                "unknown": sorted(no_helper_keys - ROUTE_POLICY_NO_HELPER_KEYS),
            },
        )
    if not isinstance(no_helper.get("allowed"), bool):
        return invalid_route_policy_manifest("optional_helper_no_helper_allowed_not_boolean")
    if not isinstance(no_helper.get("reason"), str) or not no_helper["reason"]:
        return invalid_route_policy_manifest("optional_helper_no_helper_reason_invalid")
    return {}


def validate_route_policy_route(raw: Any, *, context: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return invalid_route_policy_manifest("route_not_object", details={"route": context})
    keys = set(raw)
    if keys != ROUTE_POLICY_ROUTE_KEYS:
        return invalid_route_policy_manifest(
            "route_schema_mismatch",
            details={
                "route": context,
                "missing": sorted(ROUTE_POLICY_ROUTE_KEYS - keys),
                "unknown": sorted(keys - ROUTE_POLICY_ROUTE_KEYS),
            },
        )
    for field_name in ("route_id", "model", "model_reasoning_effort"):
        if not isinstance(raw.get(field_name), str) or not raw[field_name]:
            return invalid_route_policy_manifest("route_field_invalid", details={"route": context, "field": field_name})
    if raw["model"] not in SUPPORTED_CODEX_AGENT_MODELS:
        return invalid_route_policy_manifest("route_model_unsupported", details={"route": context, "model": raw["model"]})
    if not isinstance(raw.get("capabilities"), list) or any(not isinstance(item, str) or not item for item in raw["capabilities"]):
        return invalid_route_policy_manifest("route_capabilities_invalid", details={"route": context})
    if raw.get("probe_id") is not None and (not isinstance(raw.get("probe_id"), str) or not raw["probe_id"]):
        return invalid_route_policy_manifest("route_probe_id_invalid", details={"route": context})
    return {}
