"""Codex runtime capability probe: capture, normalize and validate the capability snapshot."""

from __future__ import annotations

import copy
from typing import Any

from ..envelope import diagnostic, is_diagnostic


def capture_codex_runtime_capabilities(
    inputs: dict[str, Any],
    route_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    overrides = inputs.get("test_overrides")
    if overrides is None:
        raw_snapshot: dict[str, Any] = {
            "snapshot_id": "snapshot:codex-runtime:unavailable",
            "adapter_id": "codex-runtime-observation.v1",
            "native_discovery": False,
            "available_routes": [],
            "child_probe_results": [],
        }
        return normalize_codex_runtime_capability_snapshot(raw_snapshot, source="default_adapter")
    if not isinstance(overrides, dict):
        return diagnostic(
            "invalid_route_capability_snapshot",
            "test_overrides must be an object when supplied",
            details={"reason": "test_overrides_not_object"},
        )
    raw_snapshot = overrides.get("codex_capability_snapshot")
    if raw_snapshot is None:
        return diagnostic(
            "invalid_route_capability_snapshot",
            "route-aware tests must inject a deterministic Codex capability snapshot",
            details={"reason": "missing_test_snapshot"},
            remediation_summary="Use test_overrides.codex_capability_snapshot for deterministic route-aware tests.",
            remediation_actions=["Inject a fixture snapshot instead of running live discovery."],
        )
    snapshot = normalize_codex_runtime_capability_snapshot(raw_snapshot, source="test_override")
    if is_diagnostic(snapshot):
        return snapshot
    observation = snapshot.get("observation_evidence")
    native_discovery = observation.get("native_discovery") if isinstance(observation, dict) else True
    if native_discovery is False and route_manifest is not None:
        raw_probe_results = overrides.get("codex_probe_results", snapshot.get("child_probe_results", []))
        probe_results = codex_route_aware_bounded_child_probe_results(raw_probe_results, route_manifest)
        if is_diagnostic(probe_results):
            return probe_results
        snapshot["child_probe_results"] = probe_results
    return snapshot


def codex_route_aware_bounded_child_probe_results(
    raw_probe_results: Any,
    route_manifest: dict[str, Any],
) -> list[dict[str, Any]] | dict[str, Any]:
    if raw_probe_results is None:
        return []
    if not isinstance(raw_probe_results, list):
        return invalid_capability_snapshot("probe_results_not_array")
    admitted = codex_route_aware_admitted_probe_pairs(route_manifest)
    results: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for raw in raw_probe_results:
        if not isinstance(raw, dict):
            continue
        probe_id = raw.get("probe_id")
        route_id = raw.get("route_id")
        if not isinstance(probe_id, str) or not isinstance(route_id, str):
            continue
        if (probe_id, route_id) not in admitted or (probe_id, route_id) in seen:
            continue
        seen.add((probe_id, route_id))
        result = {"probe_id": probe_id, "route_id": route_id}
        for field_name in ("status", "available", "evidence_id", "error"):
            if field_name in raw:
                result[field_name] = copy.deepcopy(raw[field_name])
        results.append(result)
    return results


def codex_route_aware_admitted_probe_pairs(route_manifest: dict[str, Any]) -> set[tuple[str, str]]:
    bounded_probes = route_manifest.get("bounded_probes")
    if not isinstance(bounded_probes, dict):
        return set()
    pairs: set[tuple[str, str]] = set()
    for _key, raw in bounded_probes.items():
        if not isinstance(raw, dict):
            continue
        probe_id = raw.get("probe_id")
        route_id = raw.get("candidate_route_id")
        if isinstance(probe_id, str) and isinstance(route_id, str):
            pairs.add((probe_id, route_id))
    return pairs


def normalize_codex_runtime_capability_snapshot(raw: Any, *, source: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return diagnostic(
            "invalid_route_capability_snapshot",
            "Codex capability snapshot must be an object",
            details={"reason": "snapshot_not_object"},
        )
    if isinstance(raw.get("observation_evidence"), dict):
        return validate_normalized_codex_runtime_capability_snapshot(raw)

    snapshot_id = raw.get("snapshot_id")
    adapter_id = raw.get("adapter_id")
    child_probe_results = raw.get("child_probe_results", [])
    available_routes = raw.get("available_routes", [])
    if not isinstance(snapshot_id, str) or not snapshot_id:
        return invalid_capability_snapshot("snapshot_id_invalid")
    if not isinstance(adapter_id, str) or not adapter_id:
        return invalid_capability_snapshot("adapter_id_invalid")
    if not isinstance(child_probe_results, list):
        return invalid_capability_snapshot("child_probe_results_not_array")
    if not isinstance(available_routes, list) or any(not isinstance(route, str) or not route for route in available_routes):
        return invalid_capability_snapshot("available_routes_invalid")
    return {
        "snapshot_id": snapshot_id,
        "adapter_id": adapter_id,
        "observation_evidence": {
            "source": source,
            "native_discovery": bool(raw.get("native_discovery")),
            "available_routes": list(available_routes),
        },
        "child_probe_results": copy.deepcopy(child_probe_results),
    }


def validate_normalized_codex_runtime_capability_snapshot(raw: dict[str, Any]) -> dict[str, Any]:
    snapshot_id = raw.get("snapshot_id")
    adapter_id = raw.get("adapter_id")
    observation_evidence = raw.get("observation_evidence")
    child_probe_results = raw.get("child_probe_results")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        return invalid_capability_snapshot("snapshot_id_invalid")
    if not isinstance(adapter_id, str) or not adapter_id:
        return invalid_capability_snapshot("adapter_id_invalid")
    if not isinstance(observation_evidence, dict):
        return invalid_capability_snapshot("observation_evidence_not_object")
    if not isinstance(child_probe_results, list):
        return invalid_capability_snapshot("child_probe_results_not_array")
    return {
        "snapshot_id": snapshot_id,
        "adapter_id": adapter_id,
        "observation_evidence": copy.deepcopy(observation_evidence),
        "child_probe_results": copy.deepcopy(child_probe_results),
    }


def invalid_capability_snapshot(reason: str) -> dict[str, Any]:
    return diagnostic(
        "invalid_route_capability_snapshot",
        "Codex capability snapshot is invalid",
        details={"reason": reason},
        remediation_summary="Use one deterministic runner-owned capability snapshot for the route-aware invocation.",
        remediation_actions=["Inject a valid fake snapshot in tests; do not run live discovery for static-agent-install."],
    )
