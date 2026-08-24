"""Install inventory doctor and repair helpers."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import platform as platform_module
import re
import stat
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from ..agent_materialization import materialize_agent_policy
from ..envelope import diagnostic, is_diagnostic, response
from ..merge_utils import deep_merge
from ..path_utils import resolves_to_current_python, sha256_text
from .mutation import empty_mutation, operation_record, run_mutation_helper, validate_target_path
from .read_only import find_repo_root, is_relative_to, repo_relative, resolve_input_path

INVENTORY_NAME = "install_inventory.json"
FAKE_HOME_FIXTURE_ROOT = Path("tests") / "speckit-pro" / "unit" / "fixtures"
XPLAT_008_FIXTURE_ROOT = FAKE_HOME_FIXTURE_ROOT / "installed-plugin-release"
DEFAULT_RUNNER_INVOCATION_CASES = XPLAT_008_FIXTURE_ROOT / "runner-invocation-cases.json"
XPLAT_008_PROMOTION_RECORDS = XPLAT_008_FIXTURE_ROOT / "promotion-records.json"
DEFAULT_INSTALL_HEALTH_CASES = XPLAT_008_FIXTURE_ROOT / "install-health-repair-cases.json"
MINIMUM_PYTHON = (3, 11, 0)
CODEX_OPTIONAL_HELPER_NAME = "autopilot-fast-helper"
CODEX_REQUIRED_AGENT_NAMES = (
    "analyze-executor",
    "artifact-author",
    "checklist-executor",
    "clarify-executor",
    "codebase-analyst",
    "domain-researcher",
    "implement-executor",
    "phase-executor",
    "spec-context-analyst",
    "sweep-analyst",
    "sweep-classifier",
    "uat-runbook-author",
)
CODEX_SOURCE_AGENT_TOML_NAMES = tuple(
    sorted((*[f"{name}.toml" for name in CODEX_REQUIRED_AGENT_NAMES], f"{CODEX_OPTIONAL_HELPER_NAME}.toml"))
)
REQUIRED_CODEX_AGENT_NAMES = frozenset(CODEX_SOURCE_AGENT_TOML_NAMES)
SUPPORTED_CODEX_AGENT_MODELS = frozenset({"gpt-5.5", "gpt-5.4"})
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
ROUTE_POLICY_SHA256_IDENTITY = re.compile(r"^sha256:[0-9a-f]{64}$")
ROUTE_POLICY_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
CODEX_AGENT_STATE_UNSET = object()


@dataclass(frozen=True)
class CodexAgentFileState:
    content: bytes
    mode: int
    device: int
    inode: int


def run_runner_invocation_gate(entry: Any, request: Any) -> dict[str, Any]:
    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        return response(
            "missing_prerequisite",
            request_id=request.request_id,
            data=runner_invocation_base_data(entry, request.operation, "missing_prerequisite"),
            diagnostics=[diagnostic("missing_prerequisite", "could not locate repository root for runner invocation request")],
        )

    case_result = runner_invocation_case(repo_root, request.inputs)
    if is_diagnostic(case_result):
        return response(
            "input_error",
            request_id=request.request_id,
            data=runner_invocation_base_data(entry, request.operation, "input_error"),
            diagnostics=[case_result],
        )
    case = case_result

    record, diagnostics = runner_invocation_record(case, request.request_id, repo_root)
    passed = record["status"] == "pass"
    status = "ok" if passed else "expected_failure"
    data = runner_invocation_base_data(entry, request.operation, status)
    data["runner_invocation"] = record
    if passed:
        return response("ok", request_id=request.request_id, data=data)

    data["gate"]["gate_status"] = "fail"
    data["gate"]["blocking"] = True
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=diagnostics)


def run_install_helper(entry: Any, request: Any) -> dict[str, Any]:
    if request.helper_id == "install-codex-agents":
        return run_codex_agent_install(entry, request)

    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        return response(
            "missing_prerequisite",
            request_id=request.request_id,
            diagnostics=[diagnostic("missing_prerequisite", "could not locate repository root for install helper request")],
        )

    if request.helper_id == "install-health-repair":
        return run_install_health_repair(entry, request, repo_root)

    install_root_result = install_root_from_inputs(request.inputs, repo_root)
    if isinstance(install_root_result, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[install_root_result])
    install_root = install_root_result

    inventory_result = inventory_from_inputs(request.inputs, repo_root)
    if is_diagnostic(inventory_result):
        return response("input_error", request_id=request.request_id, diagnostics=[inventory_result])
    inventory = inventory_result

    fake_home = request.inputs.get("fake_home") is True
    if fake_home:
        fake_diag = fake_home_boundary_diagnostic(install_root, repo_root)
        if fake_diag is not None:
            return response("input_error", request_id=request.request_id, diagnostics=[fake_diag])

    doctor = doctor_report(install_root, inventory, repo_root, fake_home=fake_home)

    if request.helper_id == "doctor-preflight":
        return response(
            "ok",
            request_id=request.request_id,
            data={
                "helper_id": entry.helper_id,
                "operation": entry.operation,
                "mode": request.mode,
                "promotion_status": entry.promotion_status,
                "comparison_mode": entry.comparison_mode,
                "writes_state": False,
                "doctor": doctor,
            },
        )

    if request.helper_id == "doctor-repair" and request.inputs.get("fake_home") is not True:
        diag = diagnostic(
            "real_home_refused",
            "doctor-repair refuses to mutate a non-fixture home/install root",
            details={"install_root": repo_relative(install_root, repo_root)},
            remediation_summary="Run repair only against a fake-home fixture until active cutover.",
            remediation_actions=["Set fake_home true for tests.", "Use read-only doctor-preflight for real installs."],
        )
        return response("input_error", request_id=request.request_id, data={"doctor": doctor}, diagnostics=[diag])

    repair_ops: list[dict[str, Any]] = []
    for record in inventory["files"]:
        if record["path"] not in doctor["missing_files"] and record["path"] not in doctor["checksum_mismatches"]:
            continue
        target = install_root / record["path"]
        repair_diag = repair_target_boundary_diagnostic(target, install_root, repo_root)
        if repair_diag is not None:
            return response("input_error", request_id=request.request_id, data={"doctor": doctor}, diagnostics=[repair_diag])
        repair_ops.append(
            {
                "operation_id": f"repair:{record['path']}",
                "kind": "write_file",
                "target": target.relative_to(repo_root).as_posix(),
                "content": record["content"],
            }
        )
    return run_mutation_helper(entry, request, operations=repair_ops, extra_data={"doctor": doctor})


def run_codex_agent_install(entry: Any, request: Any) -> dict[str, Any]:
    source_dir = codex_plugin_root() / "codex-agents"
    source_result = load_codex_agent_bundle(source_dir, request.inputs)
    if is_diagnostic(source_result):
        return response("input_error", request_id=request.request_id, diagnostics=[source_result])
    rendered, model = source_result

    route_manifest: dict[str, Any] | None = None
    route_snapshot: dict[str, Any] | None = None
    strict_model_override = request.inputs.get("strict_model_override")
    if "route_policy_manifest" in request.inputs:
        if strict_model_override is not None and (not isinstance(strict_model_override, str) or not strict_model_override.strip()):
            return response(
                "input_error",
                request_id=request.request_id,
                diagnostics=[
                    diagnostic(
                        "invalid_strict_model_override",
                        "strict_model_override must be a non-empty model string",
                        remediation_summary="Use one explicit model string for strict route-aware override validation.",
                        remediation_actions=["Set inputs.strict_model_override to a supported manifest-admitted model."],
                    )
                ],
            )
        repo_root = find_repo_root(Path.cwd())
        if repo_root is None:
            return response(
                "missing_prerequisite",
                request_id=request.request_id,
                diagnostics=[diagnostic("missing_prerequisite", "could not locate repository root for route-aware Codex agent install")],
            )
        route_manifest = load_codex_route_policy_manifest(
            request.inputs.get("route_policy_manifest"),
            repo_root,
            source_dir,
        )
        if is_diagnostic(route_manifest):
            return response("input_error", request_id=request.request_id, diagnostics=[route_manifest])
        captured_snapshot = capture_codex_runtime_capabilities(request.inputs, route_manifest)
        if is_diagnostic(captured_snapshot):
            return response("input_error", request_id=request.request_id, diagnostics=[captured_snapshot])
        route_snapshot = normalize_codex_runtime_capability_snapshot(captured_snapshot, source="adapter")
        if is_diagnostic(route_snapshot):
            return response("input_error", request_id=request.request_id, diagnostics=[route_snapshot])

    destination_result = codex_agent_destination(request.inputs)
    if is_diagnostic(destination_result):
        return response("input_error", request_id=request.request_id, diagnostics=[destination_result])
    destination = destination_result
    unsafe = codex_agent_destination_diagnostic(destination)
    if unsafe is not None:
        return response("input_error", request_id=request.request_id, diagnostics=[unsafe])

    mutation = empty_mutation(request.mode)
    install_rendered = rendered
    route_routing: dict[str, Any] | None = None
    if route_manifest is not None and route_snapshot is not None:
        source_immutability_diag = codex_route_aware_source_immutability_diagnostic(source_dir, route_manifest)
        if source_immutability_diag is not None:
            return response("input_error", request_id=request.request_id, diagnostics=[source_immutability_diag])
        route_routing = codex_route_aware_adapter_routing(
            route_manifest,
            route_snapshot,
            mutation,
            source_dir,
            destination,
            request.inputs,
            strict_model_override=strict_model_override,
        )
        if codex_route_aware_has_required_miss(route_routing):
            mutation["mutation_status"] = "blocked"
            route_routing["recovery_or_mutation"] = codex_route_aware_recovery_or_mutation(
                mutation,
                no_mutation_reason="required_route_unresolved",
            )
            data = codex_agent_install_data(entry, request, mutation, source_dir, destination, model, install_rendered)
            data["routing"] = route_routing
            data["restart_required"] = False
            miss_diag = codex_route_aware_required_miss_diagnostic(route_routing)
            return response(
                "expected_failure",
                request_id=request.request_id,
                data=data,
                diagnostics=[miss_diag],
            )
        if codex_route_aware_has_unresolved_helper(route_routing):
            data = codex_agent_install_data(entry, request, mutation, source_dir, destination, model, install_rendered)
            data["routing"] = route_routing
            data["restart_required"] = False
            return response(
                "expected_failure",
                request_id=request.request_id,
                data=data,
                diagnostics=[codex_route_aware_helper_unresolved_diagnostic(route_routing)],
            )
        route_rendered = codex_route_aware_rendered_destination_bytes(route_routing, source_dir)
        if is_diagnostic(route_rendered):
            return response("input_error", request_id=request.request_id, diagnostics=[route_rendered])
        install_rendered = route_rendered

    planned: list[tuple[str, Path, bytes | None]] = []
    for name, content in install_rendered.items():
        target = destination / name
        operation = {"operation_id": f"install-codex-agent:{name}", "kind": "write_file", "target": target.as_posix()}
        try:
            previous_state = codex_agent_previous_state(target)
        except OSError as exc:
            return response(
                "input_error",
                request_id=request.request_id,
                diagnostics=[
                    diagnostic(
                        "unsafe_agent_destination",
                        "Codex agent destination contains an unsafe managed entry",
                        details={"path": target.as_posix(), "error": str(exc)},
                    )
                ],
            )
        current = previous_state.content if previous_state is not None else None
        if current == content:
            mutation["no_op_operations"].append(operation_record(operation))
            continue
        planned.append((name, target, content))
        mutation["planned_operations"].append(operation_record(operation))
        mutation["planned_paths"].append(target.as_posix())
    if route_routing is not None:
        helper_removal = codex_route_aware_helper_removal_action(route_routing, destination)
        if helper_removal is not None:
            name, target = helper_removal
            operation = {"operation_id": f"remove-codex-agent:{name}", "kind": "remove_file", "target": target.as_posix()}
            planned.append((name, target, None))
            mutation["planned_operations"].append(dict(operation))

    mutation["live_mutation"] = request.mode == "apply" and bool(planned)
    data = codex_agent_install_data(entry, request, mutation, source_dir, destination, model, install_rendered)
    if route_routing is not None:
        route_routing["recovery_or_mutation"] = codex_route_aware_recovery_or_mutation(mutation)
        data["routing"] = route_routing
    if request.mode == "dry_run":
        mutation["mutation_status"] = "planned" if planned else "no_op"
        return response("ok", request_id=request.request_id, data=data)

    if not planned:
        mutation["mutation_status"] = "no_op"
        data["restart_required"] = False
        data["verification"] = {"status": "verified", "matched_files": sorted(install_rendered)}
        if route_routing is not None:
            data["routing"]["recovery_or_mutation"] = codex_route_aware_recovery_or_mutation(mutation)
        return response("ok", request_id=request.request_id, data=data)

    if route_manifest is not None:
        source_immutability_diag = codex_route_aware_source_immutability_diagnostic(source_dir, route_manifest)
        if source_immutability_diag is not None:
            return response("input_error", request_id=request.request_id, data=data, diagnostics=[source_immutability_diag])

    previous: dict[str, CodexAgentFileState | None] = {}
    applied_previous: dict[str, CodexAgentFileState | None] = {}
    applied_states: dict[str, CodexAgentFileState | None] = {}
    destination_existed = destination.exists()
    destination_parent_existed = destination.parent.exists()
    destination_identity: tuple[int, int] | None = None
    failed_name: str | None = None
    try:
        destination.mkdir(parents=True, exist_ok=True)
        unsafe = codex_agent_destination_diagnostic(destination)
        if unsafe is not None:
            raise OSError("destination changed before apply")
        destination_identity = codex_agent_destination_identity(destination)
        for name, target, _content in planned:
            failed_name = name
            if not codex_agent_target_is_safe(target, destination, destination_identity):
                raise OSError(f"unsafe destination entry: {name}")
            previous[name] = codex_agent_previous_state(target)
        for index, (name, target, content) in enumerate(planned):
            failed_name = name
            if not codex_agent_target_is_safe(target, destination, destination_identity):
                raise OSError(f"unsafe destination entry: {name}")
            if not codex_agent_state_matches(target, previous[name]):
                raise OSError(f"destination entry changed after snapshot: {name}")
            if content is None:
                if previous[name] is not None:
                    remove_codex_agent_if_unchanged(
                        target,
                        previous[name],
                        destination,
                        destination_identity,
                    )
                operation = {"operation_id": f"remove-codex-agent:{name}", "kind": "remove_file", "target": target.as_posix()}
            else:
                write_codex_agent_atomic(
                    target,
                    content,
                    destination,
                    destination_identity,
                    expected_state=previous[name],
                )
                operation = {"operation_id": f"install-codex-agent:{name}", "kind": "write_file", "target": target.as_posix()}
            applied_previous[name] = previous[name]
            applied_states[name] = codex_agent_previous_state(target)
            mutation["applied_operations"].append(dict(operation) if operation["kind"] == "remove_file" else operation_record(operation))
            mutation["touched_paths"].append(target.as_posix())

        mismatches = verify_codex_agent_install(destination, install_rendered)
        if mismatches:
            raise OSError(f"post-copy verification failed: {', '.join(mismatches)}")
    except OSError as exc:
        rollback_failures = rollback_codex_agent_install(
            destination,
            applied_previous,
            destination_identity,
            expected_current=applied_states,
        )
        if failed_name is not None and failed_name not in applied_states:
            failed_target = destination / failed_name
            if not codex_agent_state_matches(failed_target, previous.get(failed_name)):
                rollback_failures = sorted({*rollback_failures, failed_name})
        cleanup_codex_agent_destination(
            destination,
            destination_existed=destination_existed,
            destination_parent_existed=destination_parent_existed,
        )
        mutation["mutation_status"] = "partial_failure" if rollback_failures else "blocked"
        if failed_name is not None:
            failed_target = destination / failed_name
            mutation["failure_operation"] = operation_record(
                {
                    "operation_id": f"install-codex-agent:{failed_name}",
                    "kind": "write_file",
                    "target": failed_target.as_posix(),
                }
            )
        mutation["manual_remediation"] = (
            codex_route_aware_rollback_manual_remediation(destination, rollback_failures) if rollback_failures else []
        )
        data["writes_state"] = bool(rollback_failures)
        data["rollback_succeeded"] = not rollback_failures
        data["restart_required"] = bool(rollback_failures)
        data["verification"] = {"status": "failed", "matched_files": []}
        if route_routing is not None:
            data["routing"]["recovery_or_mutation"] = codex_route_aware_recovery_after_apply_failure(
                mutation,
                destination,
                previous,
                rollback_failures,
            )
        return response(
            "expected_failure",
            request_id=request.request_id,
            data=data,
            diagnostics=[
                diagnostic(
                    "codex_agent_install_failed",
                    "Codex agent installation failed and rollback was attempted",
                    details={"error": str(exc), "rollback_failures": rollback_failures},
                    remediation_summary="Inspect the destination and retry after resolving the reported failure.",
                    remediation_actions=codex_route_aware_remediation_action_summaries(mutation["manual_remediation"])
                    or ["Retry the same request in dry_run mode."],
                )
            ],
        )

    mutation["mutation_status"] = "applied"
    data["writes_state"] = True
    data["verification"] = {"status": "verified", "matched_files": sorted(install_rendered)}
    if route_routing is not None:
        data["routing"]["recovery_or_mutation"] = codex_route_aware_recovery_or_mutation(mutation)
    return response("ok", request_id=request.request_id, data=data)


def codex_plugin_root() -> Path:
    return Path(__file__).resolve().parents[2]


def route_policy_canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def route_policy_digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(route_policy_canonical_bytes(value)).hexdigest()}"


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
        for field in ("status", "available", "evidence_id", "error"):
            if field in raw:
                result[field] = copy.deepcopy(raw[field])
        results.append(result)
    return results


def codex_route_aware_admitted_probe_pairs(route_manifest: dict[str, Any]) -> set[tuple[str, str]]:
    bounded_probes = route_manifest.get("bounded_probes")
    if not isinstance(bounded_probes, dict):
        return set()
    pairs: set[tuple[str, str]] = set()
    for key, raw in bounded_probes.items():
        if not isinstance(raw, dict):
            continue
        probe_id = raw.get("probe_id", key)
        route_id = raw.get("route_id") or raw.get("candidate_route_id")
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
        remediation_actions=["Inject a valid fake snapshot in tests; do not run live discovery for G56R-006."],
    )


def codex_route_aware_adapter_routing(
    route_manifest: dict[str, Any],
    route_snapshot: dict[str, Any],
    mutation: dict[str, Any],
    source_dir: Path,
    destination: Path,
    inputs: dict[str, Any],
    *,
    strict_model_override: Any = None,
) -> dict[str, Any]:
    required_agents = codex_route_aware_required_agents(
        route_manifest,
        route_snapshot,
        source_dir,
        strict_model_override=strict_model_override,
    )
    optional_helper_decision = codex_route_aware_optional_helper(
        route_manifest,
        route_snapshot,
        source_dir,
        destination,
        inputs,
        strict_model_override=strict_model_override,
    )
    return {
        "schema_version": "1.0",
        "mode": "route_aware",
        "manifest": {
            "path": route_manifest["path"],
            "manifest_id": route_manifest["manifest_id"],
            "schema_version": route_manifest["schema_version"],
            "source_roster_id": route_manifest["source_roster_id"],
            "provenance_id": route_manifest["provenance_id"],
        },
        "runtime_capability_snapshot": route_snapshot,
        "required_agents": required_agents,
        "optional_helper_decision": optional_helper_decision,
        "strict_override": codex_route_aware_strict_override_evidence(
            strict_model_override,
            required_agents,
            optional_helper_decision,
        ),
        "recovery_or_mutation": codex_route_aware_recovery_or_mutation(mutation),
    }


def codex_route_aware_required_agents(
    route_manifest: dict[str, Any],
    route_snapshot: dict[str, Any],
    source_dir: Path,
    *,
    strict_model_override: Any = None,
) -> list[dict[str, Any]]:
    policies = route_manifest["required_agent_policies"]
    records: list[dict[str, Any]] = []
    for agent_name in CODEX_REQUIRED_AGENT_NAMES:
        policy = policies[agent_name]
        records.append(
            codex_route_aware_resolve_agent(
                agent_name,
                policy,
                route_snapshot,
                source_dir,
                strict_model_override=strict_model_override if isinstance(strict_model_override, str) else None,
            )
        )
    return records


def codex_route_aware_optional_helper(
    route_manifest: dict[str, Any],
    route_snapshot: dict[str, Any],
    source_dir: Path,
    destination: Path,
    inputs: dict[str, Any],
    *,
    strict_model_override: Any = None,
) -> dict[str, Any]:
    policy = route_manifest["optional_helper_policy"]
    resolution = codex_route_aware_resolve_agent(
        CODEX_OPTIONAL_HELPER_NAME,
        policy,
        route_snapshot,
        source_dir,
        strict_model_override=strict_model_override if isinstance(strict_model_override, str) else None,
    )
    no_helper = policy.get("no_helper") if isinstance(policy.get("no_helper"), dict) else {}
    no_helper_validation = {
        "allowed": bool(no_helper.get("allowed")),
        "selected": False,
        "reason": no_helper.get("reason") if isinstance(no_helper.get("reason"), str) else None,
        "existing_helper_state": None,
    }
    managed_ownership_proof = None
    manual_remediation: list[dict[str, Any]] = []
    if resolution["terminal_outcome"] == "resolved":
        outcome = "installed"
    elif no_helper_validation["allowed"]:
        no_helper_validation["selected"] = True
        managed_ownership_proof = codex_route_aware_managed_helper_ownership_proof(
            route_manifest,
            source_dir,
            destination,
        )
        if managed_ownership_proof is None:
            preservation = codex_route_aware_unmanaged_helper_preservation(destination)
            if preservation is None:
                outcome = "omitted"
                no_helper_validation["existing_helper_state"] = "absent"
                managed_ownership_proof = {"status": "not_required", "reason": "helper_absent"}
            else:
                outcome = "preserved"
                no_helper_validation["existing_helper_state"] = "unmanaged"
                managed_ownership_proof = preservation["managed_ownership_proof"]
                manual_remediation = preservation["manual_remediation"]
        else:
            outcome = "removed"
            no_helper_validation["existing_helper_state"] = "managed"
    else:
        outcome = "unresolved"
        no_helper_validation["existing_helper_state"] = "unknown"
        managed_ownership_proof = None

    return {
        "helper_name": CODEX_OPTIONAL_HELPER_NAME,
        "outcome": outcome,
        "policy_id": resolution["policy_id"],
        "route_resolution_id": resolution["route_resolution_id"],
        "resolved_agent_policy_id": resolution["resolved_agent_policy_id"] if outcome == "installed" else None,
        "materialization_id": resolution["materialization_id"] if outcome == "installed" else None,
        "materialization_proof": resolution["materialization_proof"] if outcome == "installed" else None,
        "snapshot_id": resolution["snapshot_id"],
        "attempted_routes": resolution["attempted_routes"],
        "rejection_reasons": resolution["rejection_reasons"],
        "terminal_outcome": resolution["terminal_outcome"] if outcome == "installed" else outcome,
        "selected_route": resolution["selected_route"] if outcome == "installed" else None,
        "no_helper_validation": no_helper_validation,
        "managed_ownership_proof": managed_ownership_proof,
        "manual_remediation": manual_remediation,
    }


def codex_route_aware_resolve_agent(
    agent_name: str,
    policy: dict[str, Any],
    route_snapshot: dict[str, Any],
    source_dir: Path,
    *,
    strict_model_override: str | None = None,
) -> dict[str, Any]:
    snapshot_id = route_snapshot["snapshot_id"]
    attempted_routes: list[dict[str, Any]] = []
    rejection_reasons: list[str] = []
    selected_route: dict[str, Any] | None = None
    materialization_proof: dict[str, Any] | None = None
    materialization_failure: str | None = None

    routes = (
        [codex_route_aware_strict_override_route(policy, strict_model_override, agent_name=agent_name)]
        if strict_model_override is not None
        else codex_route_aware_policy_routes(policy)
    )
    for route in routes:
        normalized_route = codex_route_aware_normalize_route(route)
        rejection = (
            "strict_override_route_missing"
            if route.get("strict_override_missing") is True
            else codex_route_aware_route_rejection(policy, normalized_route, route_snapshot)
        )
        if rejection is None:
            try:
                materialization_proof = codex_route_aware_materialization_proof(source_dir, agent_name, normalized_route)
            except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, ValueError) as exc:
                materialization_failure = f"materialization_failed:{type(exc).__name__}"
                attempted_routes.append({**normalized_route, "outcome": "rejected", "reason": materialization_failure})
                rejection_reasons.append(f"{normalized_route['route_id']}: {materialization_failure}")
                continue
            attempted_routes.append({**normalized_route, "outcome": "selected"})
            selected_route = normalized_route
            break
        attempted_routes.append({**normalized_route, "outcome": "rejected", "reason": rejection})
        rejection_reasons.append(f"{normalized_route['route_id']}: {rejection}")

    route_resolution_id = route_policy_digest(
        {
            "agent_name": agent_name,
            "policy_id": policy.get("policy_id"),
            "snapshot_id": snapshot_id,
            "attempted_routes": attempted_routes,
            "selected_route": selected_route,
        }
    )
    if selected_route is None or materialization_proof is None:
        return {
            "agent_name": agent_name,
            "route_resolution_id": route_resolution_id,
            "policy_id": policy.get("policy_id"),
            "resolved_agent_policy_id": None,
            "materialization_id": None,
            "materialization_proof": None,
            "snapshot_id": snapshot_id,
            "attempted_routes": attempted_routes,
            "rejection_reasons": rejection_reasons,
            "selected_route": None,
            "terminal_outcome": materialization_failure or "unresolved",
        }

    resolved_agent_policy_id = route_policy_digest(
        {
            "agent_name": agent_name,
            "policy_id": policy.get("policy_id"),
            "selected_route": selected_route,
            "materialization_id": materialization_proof["materialization_id"],
            "non_route_contract_digest": policy.get("non_route_contract_digest"),
        }
    )
    return {
        "agent_name": agent_name,
        "route_resolution_id": route_resolution_id,
        "policy_id": policy.get("policy_id"),
        "resolved_agent_policy_id": resolved_agent_policy_id,
        "materialization_id": materialization_proof["materialization_id"],
        "materialization_proof": materialization_proof,
        "snapshot_id": snapshot_id,
        "attempted_routes": attempted_routes,
        "rejection_reasons": rejection_reasons,
        "selected_route": selected_route,
        "terminal_outcome": "resolved",
    }


def codex_route_aware_managed_helper_ownership_proof(
    route_manifest: dict[str, Any],
    source_dir: Path,
    destination: Path,
) -> dict[str, Any] | None:
    helper_target = destination / f"{CODEX_OPTIONAL_HELPER_NAME}.toml"
    try:
        existing_state = codex_agent_previous_state(helper_target)
    except OSError:
        return None
    if existing_state is None:
        return None

    existing_bytes = existing_state.content
    existing_digest = f"sha256:{hashlib.sha256(existing_bytes).hexdigest()}"
    known_digest = codex_route_aware_known_helper_rendered_digest(source_dir, route_manifest)
    if existing_digest == known_digest:
        return {
            "status": "known_rendered_digest",
            "helper_name": CODEX_OPTIONAL_HELPER_NAME,
            "existing_digest": existing_digest,
            "destination": helper_target.as_posix(),
            "known_rendered_digest": known_digest,
        }
    return None


def codex_route_aware_unmanaged_helper_preservation(destination: Path) -> dict[str, Any] | None:
    helper_target = destination / f"{CODEX_OPTIONAL_HELPER_NAME}.toml"
    try:
        existing_state = codex_agent_previous_state(helper_target)
    except OSError as exc:
        return {
            "managed_ownership_proof": {
                "status": "absent",
                "reason": "ownership_proof_absent",
                "helper_name": CODEX_OPTIONAL_HELPER_NAME,
                "destination": helper_target.as_posix(),
                "existing_digest": None,
                "read_error": type(exc).__name__,
            },
            "manual_remediation": [
                codex_route_aware_unmanaged_helper_manual_remediation(helper_target, read_error=type(exc).__name__)
            ],
        }
    if existing_state is None:
        return None

    existing_bytes = existing_state.content
    existing_digest = f"sha256:{hashlib.sha256(existing_bytes).hexdigest()}"
    return {
        "managed_ownership_proof": {
            "status": "absent",
            "reason": "ownership_proof_absent",
            "helper_name": CODEX_OPTIONAL_HELPER_NAME,
            "destination": helper_target.as_posix(),
            "existing_digest": existing_digest,
        },
        "manual_remediation": [codex_route_aware_unmanaged_helper_manual_remediation(helper_target)],
    }


def codex_route_aware_unmanaged_helper_manual_remediation(
    helper_target: Path,
    *,
    read_error: str | None = None,
) -> dict[str, Any]:
    action = {
        "action_type": "manual_remediation",
        "reason": "unmanaged_helper_preserved",
        "path": helper_target.as_posix(),
        "summary": "Existing same-named optional helper was preserved because managed ownership proof is absent.",
        "recommended_actions": [
            "Review the preserved helper file manually.",
            "Remove or rename it only after confirming it is not user-owned.",
        ],
    }
    if read_error is not None:
        action["read_error"] = read_error
    return action


def codex_route_aware_known_helper_rendered_digest(source_dir: Path, route_manifest: dict[str, Any]) -> str | None:
    policy = route_manifest["optional_helper_policy"]
    route = policy.get("preferred_route")
    if not isinstance(route, dict):
        return None
    try:
        rendered = codex_route_aware_render_destination_bytes(
            (source_dir / f"{CODEX_OPTIONAL_HELPER_NAME}.toml").read_bytes(),
            route,
            agent_name=CODEX_OPTIONAL_HELPER_NAME,
        )
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, ValueError):
        return None
    return f"sha256:{hashlib.sha256(rendered).hexdigest()}"


def codex_route_aware_helper_removal_action(routing: dict[str, Any], destination: Path) -> tuple[str, Path] | None:
    helper = routing.get("optional_helper_decision")
    if not isinstance(helper, dict) or helper.get("outcome") != "removed":
        return None
    name = f"{CODEX_OPTIONAL_HELPER_NAME}.toml"
    return name, destination / name


def codex_route_aware_policy_routes(policy: dict[str, Any]) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    preferred = policy.get("preferred_route")
    if isinstance(preferred, dict):
        routes.append(preferred)
    fallbacks = policy.get("fallback_routes")
    if isinstance(fallbacks, list):
        routes.extend(route for route in fallbacks if isinstance(route, dict))
    return routes


def codex_route_aware_strict_override_route(policy: dict[str, Any], model: str, *, agent_name: str) -> dict[str, Any]:
    routes = codex_route_aware_policy_routes(policy)
    for route in routes:
        if route.get("model") == model:
            strict_route = dict(route)
            strict_route["route_id"] = f"strict-override:{agent_name}:{model}"
            strict_route["source_route_id"] = route["route_id"]
            return strict_route

    fallback = routes[0] if routes else {}
    return {
        "route_id": f"strict-override:{agent_name}:{model}",
        "model": model,
        "model_reasoning_effort": fallback.get("model_reasoning_effort") or "",
        "capabilities": list(fallback.get("capabilities") if isinstance(fallback.get("capabilities"), list) else []),
        "probe_id": fallback.get("probe_id"),
        "strict_override_missing": True,
    }


def codex_route_aware_normalize_route(route: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "route_id": route["route_id"],
        "model": route["model"],
        "model_reasoning_effort": route["model_reasoning_effort"],
        "capabilities": list(route["capabilities"]),
        "probe_id": route.get("probe_id"),
    }
    if isinstance(route.get("source_route_id"), str):
        normalized["source_route_id"] = route["source_route_id"]
    return normalized


def codex_route_aware_route_rejection(
    policy: dict[str, Any],
    route: dict[str, Any],
    route_snapshot: dict[str, Any],
) -> str | None:
    observation = route_snapshot.get("observation_evidence")
    available_routes = observation.get("available_routes") if isinstance(observation, dict) else []
    native_discovery = observation.get("native_discovery") if isinstance(observation, dict) else True
    availability_route_id = route.get("source_route_id") if isinstance(route.get("source_route_id"), str) else route["route_id"]
    observed_routes = set(available_routes if isinstance(available_routes, list) and native_discovery is not False else [])
    if availability_route_id not in observed_routes:
        if native_discovery is False and isinstance(route.get("probe_id"), str):
            probe_rejection = codex_route_aware_probe_route_rejection(route, route_snapshot, availability_route_id)
            if probe_rejection is not None:
                return probe_rejection
        else:
            return "route_unavailable"
    required_capabilities = policy.get("required_capabilities")
    if isinstance(required_capabilities, list) and not set(required_capabilities) <= set(route["capabilities"]):
        return "required_capability_missing"
    return None


def codex_route_aware_probe_route_rejection(
    route: dict[str, Any],
    route_snapshot: dict[str, Any],
    availability_route_id: str,
) -> str | None:
    probe_id = route.get("probe_id")
    child_results = route_snapshot.get("child_probe_results")
    if not isinstance(probe_id, str) or not isinstance(child_results, list):
        return "probe_result_missing"
    matches = [
        result
        for result in child_results
        if isinstance(result, dict)
        and result.get("probe_id") == probe_id
        and result.get("route_id") == availability_route_id
    ]
    if not matches:
        return "probe_result_missing"
    result = matches[0]
    status = result.get("status")
    available = result.get("available")
    if available is True and status in {"success", "available"}:
        return None
    if available is False or status in {"failed", "unavailable"}:
        return "probe_failed"
    return "probe_insufficient_result"


def codex_route_aware_strict_override_evidence(
    strict_model_override: Any,
    required_agents: list[dict[str, Any]],
    optional_helper_decision: dict[str, Any],
) -> dict[str, Any]:
    requested = isinstance(strict_model_override, str) and bool(strict_model_override.strip())
    if not requested:
        return {
            "requested": False,
            "status": "absent",
            "model": None,
            "evaluated_tuples": [],
            "required_agents_evaluated": 0,
            "helper_evaluated": False,
            "helper_tuple": None,
            "fallback_suppressed": False,
        }

    evaluated_tuples: list[dict[str, Any]] = []
    for record in required_agents:
        attempt = record["attempted_routes"][0] if record.get("attempted_routes") else {}
        evaluated_tuples.append(
            {
                "agent_name": record["agent_name"],
                "route_id": attempt.get("route_id"),
                "model": attempt.get("model"),
                "model_reasoning_effort": attempt.get("model_reasoning_effort"),
                "outcome": attempt.get("outcome"),
                "reason": attempt.get("reason"),
            }
        )
    compatible = all(record.get("terminal_outcome") == "resolved" for record in required_agents)
    helper_tuple = codex_route_aware_strict_helper_tuple(strict_model_override, optional_helper_decision)
    return {
        "requested": True,
        "status": "compatible" if compatible else "incompatible",
        "model": strict_model_override,
        "evaluated_tuples": evaluated_tuples,
        "required_agents_evaluated": len(required_agents),
        "helper_evaluated": True,
        "helper_tuple": helper_tuple,
        "fallback_suppressed": True,
    }


def codex_route_aware_strict_helper_tuple(
    strict_model_override: str,
    optional_helper_decision: dict[str, Any],
) -> dict[str, Any]:
    attempts = optional_helper_decision.get("attempted_routes")
    attempt = attempts[0] if isinstance(attempts, list) and attempts and isinstance(attempts[0], dict) else {}
    outcome = optional_helper_decision.get("outcome")
    if outcome == "installed":
        status = "compatible"
    elif outcome == "omitted" and optional_helper_decision.get("no_helper_validation", {}).get("selected") is True:
        status = "incompatible_no_helper"
    else:
        status = "unresolved"
    return {
        "helper_name": optional_helper_decision.get("helper_name"),
        "route_id": attempt.get("route_id"),
        "model": attempt.get("model", strict_model_override),
        "model_reasoning_effort": attempt.get("model_reasoning_effort"),
        "outcome": attempt.get("outcome"),
        "reason": attempt.get("reason"),
        "status": status,
    }


def codex_route_aware_materialization_proof(
    source_dir: Path,
    agent_name: str,
    selected_route: dict[str, Any],
) -> dict[str, Any]:
    source_path = source_dir / f"{agent_name}.toml"
    source_bytes = source_path.read_bytes()
    materialization = materialize_agent_policy(
        source_relative_path=f"speckit-pro/codex-agents/{agent_name}.toml",
        source_bytes=source_bytes,
        candidate_route={
            "agent_name": agent_name,
            "model": selected_route["model"],
            "model_reasoning_effort": selected_route["model_reasoning_effort"],
        },
    )
    return {
        "materialization_id": materialization.materialization_id,
        "source_path": materialization.source_binding["path"],
        "source_bytes_digest": materialization.source_binding["digest"],
        "destination_bytes_digest": materialization.destination_bytes_digest,
        "selected_model": materialization.selected_model,
        "selected_model_reasoning_effort": materialization.selected_model_reasoning_effort,
        "materializer_binding": materialization.materializer_binding,
        "non_route_fields_unchanged": materialization.non_route_fields_unchanged,
    }


def codex_route_aware_rendered_destination_bytes(routing: dict[str, Any], source_dir: Path) -> dict[str, bytes] | dict[str, Any]:
    rendered: dict[str, bytes] = {}
    try:
        for record in routing["required_agents"]:
            if record["terminal_outcome"] != "resolved" or not isinstance(record.get("selected_route"), dict):
                continue
            name = f"{record['agent_name']}.toml"
            rendered[name] = codex_route_aware_rendered_record_bytes(source_dir, record)

        helper = routing["optional_helper_decision"]
        if helper["outcome"] == "installed" and isinstance(helper.get("selected_route"), dict):
            rendered[f"{helper['helper_name']}.toml"] = codex_route_aware_rendered_record_bytes(source_dir, helper)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, ValueError, KeyError) as exc:
        return diagnostic(
            "codex_route_materialization_failed",
            "route-aware Codex agent plan could not render exact destination bytes",
            details={"error": type(exc).__name__, "message": str(exc)},
            remediation_summary="Inspect data.routing materialization records and retry with valid source TOMLs.",
            remediation_actions=["Restore the bundled Codex agent source files and rerun dry_run."],
        )

    missing_required = sorted(f"{agent}.toml" for agent in CODEX_REQUIRED_AGENT_NAMES if f"{agent}.toml" not in rendered)
    if missing_required:
        return diagnostic(
            "codex_route_materialization_failed",
            "route-aware Codex agent plan did not render every required destination file",
            details={"missing_required_files": missing_required},
            remediation_summary="Every required route must materialize before route-aware mutation planning.",
            remediation_actions=["Inspect data.routing.required_agents and fix unresolved route records."],
        )
    return rendered


def codex_route_aware_rendered_record_bytes(source_dir: Path, record: dict[str, Any]) -> bytes:
    agent_name = record["agent_name"] if "agent_name" in record else record["helper_name"]
    source_path = source_dir / f"{agent_name}.toml"
    rendered_bytes = codex_route_aware_render_destination_bytes(
        source_path.read_bytes(),
        record["selected_route"],
        agent_name=agent_name,
    )
    expected_digest = record["materialization_proof"]["destination_bytes_digest"]
    actual_digest = f"sha256:{hashlib.sha256(rendered_bytes).hexdigest()}"
    if actual_digest != expected_digest:
        raise ValueError("rendered bytes do not match materialization proof")
    return rendered_bytes


def codex_route_aware_render_destination_bytes(
    source_bytes: bytes,
    selected_route: dict[str, Any],
    *,
    agent_name: str,
) -> bytes:
    return materialize_agent_policy(
        source_relative_path=f"speckit-pro/codex-agents/{agent_name}.toml",
        source_bytes=source_bytes,
        candidate_route={
            "agent_name": agent_name,
            "model": selected_route["model"],
            "model_reasoning_effort": selected_route["model_reasoning_effort"],
        },
    ).destination_bytes


def codex_route_aware_source_immutability_diagnostic(source_dir: Path, route_manifest: dict[str, Any]) -> dict[str, Any] | None:
    roster = codex_agent_source_roster(source_dir)
    if is_diagnostic(roster):
        return roster
    if roster["source_roster_id"] != route_manifest["source_roster_id"]:
        return diagnostic(
            "codex_agent_source_changed",
            "bundled Codex agent source roster changed during route-aware install planning",
            details={
                "expected_source_roster_id": route_manifest["source_roster_id"],
                "actual_source_roster_id": roster["source_roster_id"],
            },
            remediation_summary="Retry from a stable plugin source bundle.",
            remediation_actions=["Restore the bundled Codex agent source files before applying route-aware installation."],
        )
    return None


def codex_route_aware_has_required_miss(routing: dict[str, Any]) -> bool:
    required_agents = routing.get("required_agents")
    if not isinstance(required_agents, list):
        return True
    return any(record.get("terminal_outcome") != "resolved" for record in required_agents if isinstance(record, dict))


def codex_route_aware_has_unresolved_helper(routing: dict[str, Any]) -> bool:
    helper = routing.get("optional_helper_decision")
    return isinstance(helper, dict) and helper.get("outcome") == "unresolved"


def codex_route_aware_required_miss_diagnostic(routing: dict[str, Any]) -> dict[str, Any]:
    strict = routing.get("strict_override") if isinstance(routing.get("strict_override"), dict) else {}
    if strict.get("status") == "incompatible":
        return diagnostic(
            "codex_strict_override_required_unresolved",
            "strict route-aware override could not resolve every required Codex agent",
            remediation_summary="Inspect data.routing.required_agents and strict_override.evaluated_tuples.",
            remediation_actions=["Retry with an override model that every required policy admits."],
        )
    return diagnostic(
        "codex_route_required_agent_unresolved",
        "route-aware Codex agent install could not resolve every required agent",
        remediation_summary="Inspect data.routing.required_agents and provide manifest-admitted available routes.",
        remediation_actions=["Retry with a compatible route-policy manifest and capability snapshot."],
    )


def codex_route_aware_helper_unresolved_diagnostic(routing: dict[str, Any]) -> dict[str, Any]:
    strict = routing.get("strict_override") if isinstance(routing.get("strict_override"), dict) else {}
    if strict.get("helper_tuple", {}).get("status") == "unresolved":
        return diagnostic(
            "codex_strict_override_helper_unresolved",
            "strict route-aware override could not resolve the optional helper or validate no-helper continuation",
            remediation_summary="Inspect data.routing.optional_helper_decision and strict_override.helper_tuple.",
            remediation_actions=["Permit validated no-helper continuation or use an override model compatible with the helper policy."],
        )
    return diagnostic(
        "codex_route_helper_unresolved",
        "route-aware Codex agent install could not resolve the optional helper or validate no-helper continuation",
        remediation_summary="Inspect data.routing.optional_helper_decision.",
        remediation_actions=["Provide a helper route or a validated no-helper policy."],
    )


def codex_route_aware_recovery_or_mutation(
    mutation: dict[str, Any],
    *,
    no_mutation_reason: str | None = None,
) -> dict[str, Any]:
    planned_operations = mutation.get("planned_operations", [])
    applied_operations = mutation.get("applied_operations", [])
    planned_writes = list(mutation.get("planned_paths", []))
    planned_removals = [
        operation["target"]
        for operation in planned_operations
        if isinstance(operation, dict) and operation.get("kind") == "remove_file" and isinstance(operation.get("target"), str)
    ]
    applied_removals = [
        operation["target"]
        for operation in applied_operations
        if isinstance(operation, dict) and operation.get("kind") == "remove_file" and isinstance(operation.get("target"), str)
    ]
    touched_paths = list(mutation.get("touched_paths", []))
    applied_writes = [path for path in touched_paths if path not in set(applied_removals)]
    writes_state = bool(applied_writes or applied_removals)
    terminal_outcome = "planned" if (planned_writes or planned_removals) and not (applied_writes or applied_removals) else "no_mutation"
    state_identity = route_policy_digest(
        {
            "terminal_outcome": terminal_outcome,
            "planned_writes": planned_writes,
            "planned_removals": planned_removals,
            "applied_writes": applied_writes,
            "applied_removals": applied_removals,
            "writes_state": writes_state,
        }
    )
    final_state_identity = (
        state_identity
        if not writes_state
        else route_policy_digest(
            {
                "terminal_outcome": terminal_outcome,
                "applied_writes": applied_writes,
                "applied_removals": applied_removals,
                "writes_state": writes_state,
            }
        )
    )
    return {
        "planned_writes": planned_writes,
        "planned_removals": planned_removals,
        "applied_writes": applied_writes,
        "applied_removals": applied_removals,
        "recovery_record": {
            "pre_state_id": state_identity,
            "final_state_id": final_state_identity,
            "staged_actions": list(planned_operations if isinstance(planned_operations, list) else []),
            "applied_actions": list(applied_operations if isinstance(applied_operations, list) else []),
            "rolled_back_actions": [],
            "cleanup_actions": [],
            "cleanup_errors": [],
            "failed_actions": [],
            "rollback_outcome": "not_required",
            "manual_remediation": [],
            "terminal_outcome": terminal_outcome,
            "no_mutation_reason": no_mutation_reason if terminal_outcome == "no_mutation" else None,
        },
        "writes_state": writes_state,
        "restart_required": writes_state,
    }


def codex_route_aware_recovery_after_apply_failure(
    mutation: dict[str, Any],
    destination: Path,
    previous: dict[str, CodexAgentFileState | None],
    rollback_failures: list[str],
) -> dict[str, Any]:
    planned_operations = mutation.get("planned_operations", [])
    applied_operations = mutation.get("applied_operations", [])
    applied_removals = [
        operation["target"]
        for operation in applied_operations
        if isinstance(operation, dict) and operation.get("kind") == "remove_file" and isinstance(operation.get("target"), str)
    ]
    touched_paths = list(mutation.get("touched_paths", []))
    applied_writes = [path for path in touched_paths if path not in set(applied_removals)]
    prior_state = codex_route_aware_state_records(destination, previous)
    final_state = codex_route_aware_destination_state_records(destination, list(previous))
    pre_state_id = route_policy_digest(prior_state)
    final_state_id = route_policy_digest(final_state)
    writes_state = bool(rollback_failures) or pre_state_id != final_state_id
    rollback_outcome = "unrestored" if rollback_failures else "restored"
    failure_operation = mutation.get("failure_operation")
    rollback_error_records = codex_route_aware_rollback_error_records(destination, rollback_failures)
    unrestored_actions = codex_route_aware_unrestored_actions(destination, rollback_failures)
    terminal_outcome = "uncertain_state" if writes_state else "restored"
    return {
        "planned_writes": list(mutation.get("planned_paths", [])),
        "planned_removals": [
            operation["target"]
            for operation in planned_operations
            if isinstance(operation, dict) and operation.get("kind") == "remove_file" and isinstance(operation.get("target"), str)
        ],
        "applied_writes": applied_writes,
        "applied_removals": applied_removals,
        "recovery_record": {
            "pre_state_id": pre_state_id,
            "final_state_id": final_state_id,
            "prior_state": prior_state,
            "final_state": final_state,
            "staged_actions": list(planned_operations if isinstance(planned_operations, list) else []),
            "applied_actions": list(applied_operations if isinstance(applied_operations, list) else []),
            "rolled_back_actions": codex_route_aware_rolled_back_actions(destination, previous),
            "cleanup_actions": [],
            "cleanup_errors": [],
            "failed_actions": codex_route_aware_failed_actions(destination, failure_operation),
            "rollback_outcome": rollback_outcome,
            "rollback_failures": list(rollback_failures),
            "rollback_errors": rollback_error_records,
            "unrestored_actions": unrestored_actions,
            "state_status": "uncertain" if writes_state else "restored",
            "manual_remediation": list(mutation.get("manual_remediation", [])),
            "terminal_outcome": terminal_outcome,
            "no_mutation_reason": None,
        },
        "writes_state": writes_state,
        "restart_required": writes_state,
    }


def codex_route_aware_state_records(
    destination: Path,
    states: dict[str, CodexAgentFileState | None],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for name, state in states.items():
        records.append(codex_route_aware_state_record(destination / name, name, state))
    return records


def codex_route_aware_destination_state_records(destination: Path, names: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for name in names:
        target = destination / name
        try:
            state = codex_agent_previous_state(target)
        except OSError as exc:
            records.append(
                {
                    "name": name,
                    "target": target.as_posix(),
                    "existed": "unknown",
                    "digest": None,
                    "mode": None,
                    "error": type(exc).__name__,
                }
            )
            continue
        records.append(codex_route_aware_state_record(target, name, state))
    return records


def codex_route_aware_state_record(
    target: Path,
    name: str,
    state: CodexAgentFileState | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "name": name,
        "target": target.as_posix(),
        "existed": state is not None,
        "digest": None,
        "mode": None,
    }
    if state is not None:
        record["digest"] = f"sha256:{hashlib.sha256(state.content).hexdigest()}"
        record["mode"] = oct(state.mode & 0o7777)
    return record


def codex_route_aware_rolled_back_actions(
    destination: Path,
    previous: dict[str, tuple[bytes, int] | None],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for name, state in previous.items():
        actions.append(
            {
                "operation_id": f"rollback-codex-agent:{name}",
                "kind": "restore_file" if state is not None else "remove_file",
                "name": name,
                "target": (destination / name).as_posix(),
            }
        )
    return actions


def codex_route_aware_failed_actions(destination: Path, failure_operation: Any) -> list[dict[str, Any]]:
    if not isinstance(failure_operation, dict):
        return []
    operation_id = failure_operation.get("operation_id")
    if not isinstance(operation_id, str):
        return [dict(failure_operation)]
    name = operation_id.removeprefix("install-codex-agent:")
    if name == operation_id:
        return [dict(failure_operation)]
    return [
        {
            **failure_operation,
            "name": name,
            "target": (destination / name).as_posix(),
        }
    ]


def codex_route_aware_rollback_error_records(
    destination: Path,
    rollback_failures: list[str],
) -> list[dict[str, Any]]:
    return [{"name": name, "target": (destination / name).as_posix(), "error": "OSError"} for name in rollback_failures]


def codex_route_aware_unrestored_actions(
    destination: Path,
    rollback_failures: list[str],
) -> list[dict[str, Any]]:
    return [{"name": name, "target": (destination / name).as_posix()} for name in rollback_failures]


def codex_route_aware_rollback_manual_remediation(
    destination: Path,
    rollback_failures: list[str],
) -> list[dict[str, Any]]:
    if not rollback_failures:
        return []
    paths = [(destination / name).as_posix() for name in rollback_failures]
    return [
        {
            "action_type": "manual_remediation",
            "reason": "rollback_unrestored",
            "paths": paths,
            "summary": "Restart Codex after manually restoring or reviewing unrestored agent files.",
            "recommended_actions": [
                "Restore each unrestored file from the previous known-good bytes when available.",
                "Review the route-aware recovery record before retrying apply.",
                "Restart Codex after correcting the reported destination state.",
            ],
        }
    ]


def codex_route_aware_remediation_action_summaries(raw_actions: Any) -> list[str]:
    if not isinstance(raw_actions, list):
        return []
    summaries: list[str] = []
    for action in raw_actions:
        if isinstance(action, str):
            summaries.append(action)
        elif isinstance(action, dict) and isinstance(action.get("summary"), str):
            summaries.append(action["summary"])
    return summaries


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
    policies_result = validate_route_policy_required_policies(manifest.get("required_agent_policies"))
    if is_diagnostic(policies_result):
        return policies_result
    helper_result = validate_route_policy_optional_helper(manifest.get("optional_helper"))
    if is_diagnostic(helper_result):
        return helper_result
    if not isinstance(manifest.get("bounded_probes"), dict):
        return invalid_route_policy_manifest("bounded_probes_not_object")
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


def validate_route_policy_required_policies(raw: Any) -> dict[str, Any]:
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
        if not ROUTE_POLICY_REQUIRED_POLICY_KEYS <= policy_keys:
            return invalid_route_policy_manifest(
                "required_agent_policy_missing_keys",
                details={"agent_name": agent_name, "missing": sorted(ROUTE_POLICY_REQUIRED_POLICY_KEYS - policy_keys)},
            )
        if policy.get("agent_name") != agent_name:
            return invalid_route_policy_manifest(
                "required_agent_policy_name_mismatch",
                details={"agent_name": agent_name, "policy_agent_name": policy.get("agent_name")},
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
    if not isinstance(raw.get("no_helper"), dict):
        return invalid_route_policy_manifest("optional_helper_no_helper_not_object")
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
    for field in ("route_id", "model", "model_reasoning_effort"):
        if not isinstance(raw.get(field), str) or not raw[field]:
            return invalid_route_policy_manifest("route_field_invalid", details={"route": context, "field": field})
    if not isinstance(raw.get("capabilities"), list) or any(not isinstance(item, str) or not item for item in raw["capabilities"]):
        return invalid_route_policy_manifest("route_capabilities_invalid", details={"route": context})
    if raw.get("probe_id") is not None and (not isinstance(raw.get("probe_id"), str) or not raw["probe_id"]):
        return invalid_route_policy_manifest("route_probe_id_invalid", details={"route": context})
    return {}


def load_codex_agent_bundle(source_dir: Path, inputs: dict[str, Any]) -> tuple[dict[str, bytes], str] | dict[str, Any]:
    raw_model = inputs["model"] if "model" in inputs else os.environ.get("SPECKIT_CODEX_MODEL") or "gpt-5.5"
    if not isinstance(raw_model, str) or raw_model not in SUPPORTED_CODEX_AGENT_MODELS:
        return diagnostic(
            "unsupported_codex_model",
            "model must be gpt-5.5 or gpt-5.4",
            details={"model": raw_model},
            remediation_summary="Choose a supported explicit Codex agent model.",
            remediation_actions=["Set inputs.model to gpt-5.5 or gpt-5.4."],
        )
    roster_result = codex_agent_source_roster(source_dir)
    if is_diagnostic(roster_result):
        return roster_result
    source_files = sorted(source_dir.glob("*.toml"), key=lambda path: path.name)
    rendered: dict[str, bytes] = {}
    try:
        for path in source_files:
            if path.is_symlink() or not path.is_file():
                raise OSError(path.name)
            source_bytes = path.read_bytes()
            source_text = source_bytes.decode("utf-8")
            source_policy = tomllib.loads(source_text)
            if source_policy.get("name") != path.stem:
                raise ValueError(f"{path.name}: name must match filename")
            expected_source_model = "gpt-5.3-codex-spark" if path.name == "autopilot-fast-helper.toml" else "gpt-5.5"
            if source_policy.get("model") != expected_source_model:
                raise ValueError(f"{path.name}: unexpected source model")

            if raw_model == "gpt-5.4" and expected_source_model == "gpt-5.5":
                rendered_text, replacement_count = re.subn(
                    r'^model = "gpt-5\.5"$',
                    'model = "gpt-5.4"',
                    source_text,
                    flags=re.MULTILINE,
                )
                if replacement_count != 1:
                    raise ValueError(f"{path.name}: expected exactly one model rewrite")
                rendered_policy = tomllib.loads(rendered_text)
                if rendered_policy.get("model") != "gpt-5.4":
                    raise ValueError(f"{path.name}: model rewrite did not validate")
                rendered[path.name] = rendered_text.encode("utf-8")
            else:
                rendered[path.name] = source_bytes
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, ValueError) as exc:
        return diagnostic(
            "unsafe_agent_bundle",
            "bundled Codex agent templates could not be read safely",
            details={"error": type(exc).__name__, "message": str(exc)},
        )
    return rendered, raw_model


def codex_agent_destination(inputs: dict[str, Any]) -> Path | dict[str, Any]:
    default = Path.home() / ".codex" / "agents"
    raw = inputs.get("destination")
    if raw is None:
        candidate = default
    elif not isinstance(raw, str) or not raw.strip():
        return diagnostic("invalid_destination", "destination must be a non-empty path string")
    else:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
    candidate = candidate.absolute()
    allowed = {
        default.absolute(),
        (Path.cwd() / ".codex" / "agents").absolute(),
    }
    if candidate not in allowed:
        return diagnostic(
            "invalid_destination",
            "destination must be the user or current-project Codex agents directory",
            details={"destination": candidate.as_posix()},
            remediation_summary="Use ~/.codex/agents or .codex/agents.",
            remediation_actions=["Retry with a Codex-native agent destination."],
        )
    return candidate


def codex_agent_destination_diagnostic(destination: Path) -> dict[str, Any] | None:
    for path in (destination, *destination.parents):
        if path.exists() and path.is_symlink():
            return diagnostic(
                "unsafe_agent_destination",
                "Codex agent destination must not traverse symlinks",
                details={"path": path.as_posix()},
            )
        if path == path.parent:
            break
    if destination.exists() and not destination.is_dir():
        return diagnostic("unsafe_agent_destination", "Codex agent destination is not a directory")
    return None


def codex_agent_destination_identity(destination: Path) -> tuple[int, int]:
    metadata = destination.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise OSError("destination is not a stable directory")
    return metadata.st_dev, metadata.st_ino


def codex_agent_previous_state(target: Path) -> CodexAgentFileState | None:
    try:
        metadata = target.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(metadata.st_mode):
        raise OSError("managed target is not a regular file")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(target, flags)
        opened_metadata = os.fstat(descriptor)
        if (opened_metadata.st_dev, opened_metadata.st_ino) != (metadata.st_dev, metadata.st_ino):
            raise OSError("managed target changed while being read")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = None
            content = handle.read()
            opened_metadata = os.fstat(handle.fileno())
            if (opened_metadata.st_dev, opened_metadata.st_ino) != (metadata.st_dev, metadata.st_ino):
                raise OSError("managed target changed while being read")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return CodexAgentFileState(
        content=content,
        mode=opened_metadata.st_mode,
        device=opened_metadata.st_dev,
        inode=opened_metadata.st_ino,
    )


def codex_agent_state_matches(target: Path, expected: CodexAgentFileState | None) -> bool:
    try:
        return codex_agent_previous_state(target) == expected
    except OSError:
        return False


def rollback_codex_agent_install(
    destination: Path,
    previous: dict[str, CodexAgentFileState | None],
    destination_identity: tuple[int, int] | None,
    *,
    expected_current: dict[str, CodexAgentFileState | None],
) -> list[str]:
    failures: list[str] = []
    for name, state in reversed(list(previous.items())):
        target = destination / name
        try:
            if not codex_agent_state_matches(target, expected_current[name]):
                raise OSError("rollback target changed after installer mutation")
            if state is None:
                if not codex_agent_target_is_safe(target, destination, destination_identity):
                    raise OSError("rollback target became unsafe")
                if target.exists():
                    remove_codex_agent_if_unchanged(
                        target,
                        expected_current[name],
                        destination,
                        destination_identity,
                    )
            else:
                write_codex_agent_atomic(
                    target,
                    state.content,
                    destination,
                    destination_identity,
                    mode=state.mode,
                    expected_state=expected_current[name],
                )
        except OSError:
            failures.append(name)
    return sorted(failures)


def cleanup_codex_agent_destination(
    destination: Path,
    *,
    destination_existed: bool,
    destination_parent_existed: bool,
) -> None:
    for path, existed in ((destination, destination_existed), (destination.parent, destination_parent_existed)):
        if existed:
            continue
        try:
            path.rmdir()
        except OSError:
            # Cleanup is best-effort and must not replace the install or rollback result.
            pass


def write_codex_agent_atomic(
    target: Path,
    content: bytes,
    destination: Path,
    destination_identity: tuple[int, int] | None,
    *,
    mode: int | None = None,
    expected_state: CodexAgentFileState | None | object = CODEX_AGENT_STATE_UNSET,
) -> None:
    if not codex_agent_target_is_safe(target, destination, destination_identity):
        raise OSError("unsafe target path")
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=destination,
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
            handle.write(content)
            if mode is not None:
                descriptor_chmod = getattr(os, "fchmod", None)
                if not callable(descriptor_chmod):
                    raise OSError("safe descriptor-based mode restoration is unavailable")
                descriptor_chmod(handle.fileno(), mode & 0o7777)
            handle.flush()
            os.fsync(handle.fileno())
        if codex_agent_destination_identity(destination) != destination_identity:
            raise OSError("destination changed after temporary file creation")
        if not codex_agent_target_is_safe(target, destination, destination_identity):
            raise OSError("target path changed before replace")
        if expected_state is not CODEX_AGENT_STATE_UNSET and not codex_agent_state_matches(target, expected_state):
            raise OSError("target changed immediately before replace")
        os.replace(tmp_path, target)
        tmp_path = None
        if codex_agent_destination_identity(destination) != destination_identity:
            raise OSError("destination changed during replace")
        installed_state = codex_agent_previous_state(target)
        if installed_state is None or installed_state.content != content:
            raise OSError("target changed after replace")
        if mode is not None and (installed_state.mode & 0o7777) != (mode & 0o7777):
            raise OSError("target mode changed after replace")
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink()
            except OSError:
                pass


def remove_codex_agent_if_unchanged(
    target: Path,
    expected_state: CodexAgentFileState | None,
    destination: Path,
    destination_identity: tuple[int, int] | None,
) -> None:
    if expected_state is None:
        raise OSError("removal requires a captured file state")
    if not codex_agent_target_is_safe(target, destination, destination_identity):
        raise OSError("unsafe removal target")
    metadata = target.lstat()
    if (metadata.st_dev, metadata.st_ino) != (expected_state.device, expected_state.inode):
        raise OSError("removal target identity changed")
    if not codex_agent_state_matches(target, expected_state):
        raise OSError("removal target changed immediately before unlink")
    target.unlink()


def codex_agent_target_is_safe(
    target: Path,
    destination: Path,
    destination_identity: tuple[int, int] | None,
) -> bool:
    try:
        current_identity = codex_agent_destination_identity(destination)
    except OSError:
        return False
    if destination_identity is None or current_identity != destination_identity or target.parent != destination:
        return False
    try:
        metadata = target.lstat()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return stat.S_ISREG(metadata.st_mode)


def verify_codex_agent_install(destination: Path, rendered: dict[str, bytes]) -> list[str]:
    mismatches: list[str] = []
    for name, content in rendered.items():
        target = destination / name
        try:
            state = codex_agent_previous_state(target)
            if state is None or state.content != content:
                mismatches.append(name)
        except OSError:
            mismatches.append(name)
    return sorted(mismatches)


def codex_agent_install_data(
    entry: Any,
    request: Any,
    mutation: dict[str, Any],
    source_dir: Path,
    destination: Path,
    model: str,
    rendered: dict[str, bytes],
) -> dict[str, Any]:
    return {
        "helper_id": entry.helper_id,
        "operation": entry.operation,
        "mode": request.mode,
        "promotion_status": entry.promotion_status,
        "comparison_mode": entry.comparison_mode,
        "writes_state": False,
        "source": source_dir.as_posix(),
        "destination": destination.as_posix(),
        "model": model,
        "agent_files": sorted(rendered),
        "restart_required": request.mode == "apply",
        "verification": {"status": "planned", "matched_files": []},
        "mutation": mutation,
    }


def run_install_health_repair(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    case_result = install_health_case(repo_root, request.inputs)
    if is_diagnostic(case_result):
        return response("input_error", request_id=request.request_id, diagnostics=[case_result])
    case = case_result

    installed_cache_path = str(case.get("installed_cache_path") or "tests/speckit-pro/unit/fixtures/installed-plugin-release/fake-home/speckit-pro")
    findings = normalize_install_health_findings(case.get("findings"))
    repair_actions = normalize_install_health_actions(case.get("repair_actions"), findings)
    failures = install_health_action_failures(repair_actions)
    has_manual = any(action.get("action_type") == "manual_remediation" for action in repair_actions)
    health_status = "fail" if failures else "manual_remediation_required" if has_manual else "pass"
    install_health = {
        "schema_version": "1.0",
        "feature_id": "XPLAT-008",
        "installed_cache_path": installed_cache_path,
        "findings": findings,
        "repair_actions": repair_actions,
        "status": health_status,
    }

    data = {
        "helper_id": entry.helper_id,
        "operation": entry.operation,
        "mode": request.mode,
        "promotion_status": entry.promotion_status,
        "comparison_mode": entry.comparison_mode,
        "writes_state": False,
        "install_health_repair": install_health,
    }
    if failures:
        diag = diagnostic(
            "install_health_repair_blocked",
            "install-health repair evidence includes unsafe autoheal or broad reinstall behavior",
            details={"case_id": case.get("case_id"), "failures": failures},
            remediation_summary="Limit autoheal to trusted checksum-backed artifacts and emit manual remediation for unsafe drift.",
            remediation_actions=["Inspect data.install_health_repair.repair_actions.", "Replace broad reinstall or unverified autoheal actions with manual remediation."],
        )
        return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])
    return response("ok", request_id=request.request_id, data=data)


def install_health_case(repo_root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    raw = inputs.get("case_file", DEFAULT_INSTALL_HEALTH_CASES.as_posix())
    if not isinstance(raw, str) or not raw:
        return diagnostic("invalid_case_file", "case_file must be a non-empty string")
    path = resolve_case_path(raw, repo_root)
    if not is_relative_to(path.resolve(strict=False), repo_root.resolve(strict=False)):
        return diagnostic("invalid_case_file", "case_file must stay inside the repository")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return diagnostic(
            "invalid_case_file",
            "install-health repair case fixture could not be loaded",
            details={"case_file": raw, "error": type(exc).__name__},
        )
    cases = document.get("cases")
    if not isinstance(cases, list):
        return diagnostic("invalid_case_file", "install-health repair fixture must contain cases")
    case_id = inputs.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        case_id = "ready"
    selected = next((item for item in cases if isinstance(item, dict) and item.get("case_id") == case_id), None)
    if selected is None:
        return diagnostic("unknown_fixture_case", "install-health repair fixture case was not found", details={"case_id": case_id})
    base = copy.deepcopy(document.get("base_case", {}))
    if not isinstance(base, dict):
        base = {}
    overrides = selected.get("overrides")
    if isinstance(overrides, dict):
        deep_merge(base, overrides)
    base["case_id"] = case_id
    base["expected_status"] = selected.get("expected_status")
    return base


def normalize_install_health_findings(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    findings: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        classification = str(item.get("classification") or "unsafe_unknown")
        artifact_path = normalize_artifact_path(item.get("artifact_path"), fallback=f"unknown-{index}.txt")
        trusted = classification in {"trusted_missing", "trusted_stale"}
        findings.append(
            {
                "finding_id": str(item.get("finding_id") or f"finding-{index}"),
                "artifact_path": artifact_path,
                "artifact_kind": str(item.get("artifact_kind") or ("runner_file" if trusted else "unknown")),
                "source_identity": item.get("source_identity") if isinstance(item.get("source_identity"), str) else None,
                "release_channel_or_tag": item.get("release_channel_or_tag") if isinstance(item.get("release_channel_or_tag"), str) else None,
                "expected_digest": normalize_digest(item.get("expected_digest"), fallback=None),
                "actual_digest": normalize_digest(item.get("actual_digest"), fallback=None),
                "classification": classification,
                "repair_allowed": bool(item.get("repair_allowed")) if "repair_allowed" in item else trusted,
            }
        )
    return findings


def normalize_install_health_actions(raw: Any, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    actions: list[dict[str, Any]] = []
    for finding in findings:
        finding_id = str(finding.get("finding_id"))
        target_path = str(finding.get("artifact_path"))
        if (
            finding.get("classification") in {"trusted_missing", "trusted_stale"}
            and finding.get("repair_allowed") is True
            and has_trusted_repair_evidence(finding)
        ):
            actions.append(
                {
                    "action_id": f"autoheal:{finding_id}",
                    "finding_id": finding_id,
                    "action_type": "autoheal_refresh",
                    "target_path": target_path,
                    "source_path": str(finding.get("source_identity") or "speckit-pro"),
                    "digest_verified": True,
                    "status": "completed",
                    "message": "Trusted checksum-backed artifact refreshed from the source payload inventory.",
                    "manual_steps": [],
                }
            )
            continue
        actions.append(
            {
                "action_id": f"manual:{finding_id}",
                "finding_id": finding_id,
                "action_type": "manual_remediation",
                "target_path": target_path,
                "source_path": None,
                "digest_verified": False,
                "status": "blocked",
                "message": "Unsafe installed-cache drift requires exact manual remediation; autoheal is not allowed.",
                "manual_steps": [
                    f"Inspect installed artifact {target_path}.",
                    "Restore the plugin from a trusted marketplace release or remove the unsafe drift manually.",
                ],
            }
        )
    return actions


def has_trusted_repair_evidence(finding: dict[str, Any]) -> bool:
    for key in ("source_identity", "release_channel_or_tag", "expected_digest"):
        value = finding.get(key)
        if not isinstance(value, str) or not value:
            return False
    return True


def install_health_action_failures(actions: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for action in actions:
        action_id = str(action.get("action_id") or "unknown-action")
        action_type = action.get("action_type")
        target_path = str(action.get("target_path") or "")
        target_parts = PurePosixPath(target_path.replace("\\", "/")).parts
        broad = action.get("operation_scope") == "broad_reinstall" or target_path in {"", ".", "/"} or "reinstall" in str(action.get("message", "")).lower()
        unsafe_path = target_path.startswith("/") or any(part in {"", ".", ".."} for part in target_parts)
        if action_type == "autoheal_refresh":
            if action.get("status") != "completed" or action.get("digest_verified") is not True or not action.get("source_path") or broad or unsafe_path:
                failures.append(action_id)
        elif action_type == "manual_remediation":
            steps = action.get("manual_steps")
            if action.get("status") != "blocked" or action.get("digest_verified") is not False or not isinstance(steps, list) or not steps:
                failures.append(action_id)
        else:
            failures.append(action_id)
    return failures


def normalize_artifact_path(value: Any, *, fallback: str) -> str:
    text = value if isinstance(value, str) and value else fallback
    return text.replace("\\", "/").lstrip("/")


def normalize_digest(value: Any, *, fallback: str | None) -> str | None:
    text = value if isinstance(value, str) else fallback
    if text is None:
        return None
    return text if len(text) == 64 and all(char in "0123456789abcdef" for char in text) else fallback


def runner_invocation_case(repo_root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    raw = inputs.get("case_file", DEFAULT_RUNNER_INVOCATION_CASES.as_posix())
    if not isinstance(raw, str) or not raw:
        return diagnostic("invalid_case_file", "case_file must be a non-empty string")
    path = resolve_case_path(raw, repo_root)
    if not is_relative_to(path.resolve(strict=False), repo_root.resolve(strict=False)):
        return diagnostic("invalid_case_file", "case_file must stay inside the repository")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return diagnostic(
            "invalid_case_file",
            "runner invocation case fixture could not be loaded",
            details={"case_file": raw, "error": type(exc).__name__},
        )
    cases = document.get("cases")
    if not isinstance(cases, list):
        return diagnostic("invalid_case_file", "runner invocation fixture must contain cases")
    case_id = inputs.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        case_id = str(cases[0].get("case_id")) if cases and isinstance(cases[0], dict) else ""
    selected = next((item for item in cases if isinstance(item, dict) and item.get("case_id") == case_id), None)
    if selected is None:
        return diagnostic("unknown_fixture_case", "runner invocation fixture case was not found", details={"case_id": case_id})
    return dict(selected)


def runner_invocation_record(case: dict[str, Any], request_id: str | None, repo_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    product = normalize_enum(case.get("product"), {"claude", "codex"}, "claude")
    platform_name = normalize_enum(case.get("platform"), {"windows", "macos", "linux"}, host_platform())
    operation = normalize_enum(
        case.get("operation"),
        {"preflight", "scaffold", "status", "autopilot-dry-run", "doctor", "update", "autoheal"},
        "preflight",
    )
    surface_path = str(case.get("surface_path") or "speckit-pro/skills/speckit-status/SKILL.md")
    cache_root = str(case.get("cache_root") or ".")
    request_id_value = request_id or f"xplat-008-{product}-{platform_name}-{operation}"
    resolution, diagnostics = resolve_python_interpreter(platform_name, case, cache_root)
    fixture_backed = isinstance(case.get("candidate_results"), list)

    runner_request = {
        "schema_version": "1.0",
        "request_id": f"{request_id_value}:runtime-info",
        "helper_id": "runner",
        "operation": "runtime-info",
        "mode": "read_only",
        "inputs": {
            "source": "xplat-008-installed-runtime",
            "product": product,
            "platform": platform_name,
            "surface_path": surface_path,
        },
    }
    accepted = bool(resolution["accepted"])
    invocation = {
        "argv": [*resolution["invocation_argv_prefix"], "-m", "speckit_pro_runner"] if accepted else [],
        "stdin_mode": "single_json_request",
        "stdout_mode": "single_json_response",
        "stderr_mode": "diagnostics_only",
        "shell_used": False,
    }
    runner_response = None
    if accepted and fixture_backed:
        runner_response = {
            "schema_version": "1.0",
            "status": "ok",
            "exit_code": 0,
            "legacy_exit_code": None,
            "diagnostics": [],
            "evidence_source": "fixture",
            "data": {
                "invoked_module": "speckit_pro_runner",
                "cache_root": cache_root,
            },
        }
    elif accepted:
        runner_response, execution_diag = execute_runner_runtime_info(
            invocation["argv"],
            runner_request,
            repo_root,
            cache_root,
            selected_candidate=resolution["attempted_candidates"][-1],
        )
        if execution_diag is not None:
            diagnostics = [execution_diag]
    passed = accepted and not diagnostics
    record = {
        "schema_version": "1.0",
        "request_id": request_id_value,
        "product": product,
        "platform": platform_name,
        "surface_path": surface_path,
        "operation": operation,
        "interpreter_resolution": resolution,
        "invocation": invocation,
        "runner_request": runner_request,
        "runner_response": runner_response,
        "status": "pass" if passed else "blocked",
        "diagnostics": diagnostics,
    }
    return record, diagnostics


def resolve_python_interpreter(platform_name: str, case: dict[str, Any], cache_root: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw_results = case.get("candidate_results")
    if isinstance(raw_results, list):
        candidate_records = [item for item in raw_results if isinstance(item, dict)]
    else:
        candidate_records = probe_host_candidates(platform_name)

    attempted: list[str] = []
    last_version: str | None = None
    failure_messages: list[str] = []
    for record in candidate_records:
        candidate = str(record.get("candidate") or "")
        if not candidate:
            continue
        attempted.append(candidate)
        if not allowed_python_candidate(platform_name, candidate):
            failure_messages.append(f"{candidate}: unsupported Python candidate")
            continue
        returncode = int(record.get("returncode", 0)) if isinstance(record.get("returncode", 0), int) else 1
        version = record.get("version")
        version_text = str(version) if isinstance(version, str) and version else None
        if version_text:
            last_version = version_text
        if returncode != 0:
            stderr = str(record.get("stderr") or "candidate failed")
            failure_messages.append(f"{candidate}: {stderr}")
            continue
        if version_text is None:
            failure_messages.append(f"{candidate}: version unavailable")
            continue
        if parse_version(version_text) < MINIMUM_PYTHON:
            failure_messages.append(f"{candidate}: Python {version_text} is below 3.11")
            continue
        resolved = str(record.get("resolved_executable") or candidate.split()[0])
        if not allowed_python_executable(platform_name, resolved):
            failure_messages.append(f"{candidate}: unsupported resolved executable")
            continue
        invocation_prefix = record_invocation_prefix(record)
        if invocation_prefix is None:
            invocation_prefix = invocation_prefix_for_candidate(platform_name, candidate, resolved)
        if not allowed_python_invocation_prefix(platform_name, invocation_prefix):
            failure_messages.append(f"{candidate}: unsupported invocation prefix")
            continue
        return {
            "attempted_candidates": attempted,
            "resolved_executable": resolved,
            "invocation_argv_prefix": invocation_prefix,
            "version": version_text,
            "accepted": True,
            "minimum_version": "3.11",
            "failure_code": None,
            "diagnostic": f"Accepted Python {version_text} for installed cache {cache_root}.",
        }, []

    diag = diagnostic(
        str(case.get("expected_failure_code") or "python_runtime_unavailable"),
        "no Python 3.11+ interpreter was available for installed runner invocation",
        details={"attempted_candidates": attempted, "platform": platform_name, "cache_root": cache_root},
        remediation_summary="Install or expose Python 3.11+ and retry the installed SpecKit Pro workflow.",
        remediation_actions=["Install Python 3.11 or newer.", "Retry without adding a shell wrapper or jq fallback."],
    )
    resolution = {
        "attempted_candidates": attempted or candidate_order(platform_name),
        "resolved_executable": None,
        "invocation_argv_prefix": [],
        "version": last_version,
        "accepted": False,
        "minimum_version": "3.11",
        "failure_code": diag["code"],
        "diagnostic": "; ".join(failure_messages) or "No Python candidates were attempted.",
    }
    return resolution, [diag]


def probe_host_candidates(platform_name: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for candidate in candidate_order(platform_name):
        argv = probe_argv_for_candidate(candidate)
        try:
            completed = probe_python_candidate(candidate)
        except (OSError, subprocess.TimeoutExpired) as exc:
            records.append({"candidate": candidate, "returncode": 1, "stderr": f"{type(exc).__name__}: {exc}"})
            continue
        stdout = completed.stdout.splitlines()
        records.append(
            {
                "candidate": candidate,
                "returncode": int(completed.returncode),
                "version": stdout[0] if stdout else None,
                "resolved_executable": stdout[1] if len(stdout) > 1 else argv[0],
                "invocation_argv_prefix": invocation_prefix_for_live_probe(candidate, stdout[1] if len(stdout) > 1 else argv[0]),
                "stderr": completed.stderr.strip(),
            }
        )
    return records


def probe_python_candidate(candidate: str) -> subprocess.CompletedProcess[str]:
    probe_source = "import platform, sys; print(platform.python_version()); print(sys.executable)"
    if candidate in {"py -V:3", "py -3"}:
        return subprocess.run(
            ["py", "-3", "-c", probe_source],
            text=True,
            capture_output=True,
            timeout=5,
            shell=False,
            check=False,
        )
    if candidate == "python3":
        return subprocess.run(
            ["python3", "-c", probe_source],
            text=True,
            capture_output=True,
            timeout=5,
            shell=False,
            check=False,
        )
    if candidate == "python":
        return subprocess.run(
            ["python", "-c", probe_source],
            text=True,
            capture_output=True,
            timeout=5,
            shell=False,
            check=False,
        )
    raise OSError(f"unsupported Python probe candidate: {candidate}")


def probe_argv_for_candidate(candidate: str) -> list[str]:
    argv = candidate.split()
    if argv[:2] == ["py", "-V:3"]:
        return ["py", "-3"]
    return argv


def record_invocation_prefix(record: dict[str, Any]) -> list[str] | None:
    raw = record.get("invocation_argv_prefix")
    if isinstance(raw, list) and raw and all(isinstance(item, str) and item for item in raw):
        return list(raw)
    return None


def allowed_python_candidate(platform_name: str, candidate: str) -> bool:
    return allowed_python_program(platform_name, candidate.split()[0] if candidate.split() else "")


def allowed_python_invocation_prefix(platform_name: str, prefix: list[str]) -> bool:
    if not prefix:
        return False
    if not allowed_python_program(platform_name, prefix[0]):
        return False
    if len(prefix) == 1:
        return program_name(prefix[0]) != "py"
    return platform_name == "windows" and len(prefix) == 2 and program_name(prefix[0]) == "py" and prefix[1] == "-3"


def allowed_python_executable(platform_name: str, executable: str) -> bool:
    return allowed_python_program(platform_name, executable)


def allowed_python_program(platform_name: str, value: str) -> bool:
    name = program_name(value)
    return (
        name in {"python", "python3"}
        or bool(re.fullmatch(r"python3(?:\.\d+){1,2}", name))
        or (platform_name == "windows" and name == "py")
    )


def program_name(value: str) -> str:
    name = value.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name.removesuffix(".exe")


def invocation_prefix_for_live_probe(candidate: str, resolved_executable: str) -> list[str]:
    argv = candidate.split()
    if argv and argv[0].lower() == "py":
        return probe_argv_for_candidate(candidate)
    return probe_argv_for_candidate(candidate) if argv else [resolved_executable]


def invocation_prefix_for_candidate(platform_name: str, candidate: str, resolved_executable: str) -> list[str]:
    argv = candidate.split()
    if platform_name == "windows" and argv and argv[0].lower() == "py":
        selector: str | None = None
        if len(argv) > 1:
            selector = "-3" if argv[1] == "-V:3" else argv[1]
        if selector and selector.startswith("-"):
            executable_name = resolved_executable.replace("\\", "/").rsplit("/", 1)[-1].lower()
            if executable_name in {"py", "py.exe"}:
                return [resolved_executable, selector]
    return [resolved_executable]


def execute_runner_runtime_info(
    argv: list[str],
    runner_request: dict[str, Any],
    repo_root: Path,
    cache_root: str,
    *,
    selected_candidate: str | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    cache_path = Path(cache_root.replace("\\", "/"))
    cwd = cache_path if cache_path.is_absolute() else repo_root / cache_path
    if not cwd.is_dir():
        return None, diagnostic(
            "runner_cache_missing",
            "selected installed cache root does not exist",
            details={"cache_root": cache_root},
            remediation_summary="Install or rebuild the plugin payload before claiming installed runner invocation readiness.",
            remediation_actions=["Verify the recorded cache_root exists.", "Repair or reinstall the plugin payload and retry."],
        )
    if not (cwd / "speckit_pro_runner" / "__main__.py").is_file():
        return None, diagnostic(
            "runner_payload_missing",
            "selected installed cache root does not contain speckit_pro_runner",
            details={"cache_root": cache_root},
            remediation_summary="Ship the runner package inside the installed plugin payload.",
            remediation_actions=["Rebuild generated Claude and Codex payloads.", "Verify speckit_pro_runner/__main__.py exists in the installed cache."],
        )
    try:
        completed = run_python_runner_subprocess(
            argv,
            selected_candidate=selected_candidate,
            input_text=json.dumps(runner_request),
            cwd=cwd,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, diagnostic(
            "runner_invocation_failed",
            "selected Python interpreter could not execute speckit_pro_runner",
            details={"error": type(exc).__name__, "cache_root": cache_root},
            remediation_summary="Verify the selected interpreter can run the installed speckit_pro_runner package.",
            remediation_actions=["Run the recorded argv from the installed plugin cache.", "Repair the installed cache or select another Python 3.11+ interpreter."],
        )
    try:
        parsed_value = json.loads(completed.stdout)
    except json.JSONDecodeError:
        parsed = {
            "schema_version": "1.0",
            "status": "subprocess_failure",
            "exit_code": completed.returncode,
            "legacy_exit_code": None,
            "diagnostics": [],
            "data": {
                "stdout_preview": completed.stdout[:200],
                "stderr_preview": completed.stderr[:200],
            },
        }
    else:
        if not isinstance(parsed_value, dict):
            parsed = malformed_runner_response(completed, type(parsed_value).__name__)
            return parsed, diagnostic(
                "runner_response_malformed",
                "selected Python interpreter returned non-object JSON for runner runtime-info",
                details={"exit_code": completed.returncode, "parsed_type": type(parsed_value).__name__},
                remediation_summary="Repair the installed runner payload before claiming invocation readiness.",
                remediation_actions=["Verify the installed runner emits a JSON object envelope.", "Retry after reinstalling or repairing the plugin cache."],
            )
        parsed = parsed_value
    if completed.returncode == 0 and parsed.get("status") == "ok":
        identity_diag = validate_runner_runtime_response(parsed, cwd, cache_root)
        if identity_diag is None:
            return parsed, None
        return parsed, identity_diag
    return parsed, diagnostic(
        "runner_invocation_failed",
        "selected Python interpreter did not return a successful runner runtime-info response",
        details={"exit_code": completed.returncode, "status": parsed.get("status")},
        remediation_summary="Repair the installed runner payload before claiming invocation readiness.",
        remediation_actions=["Inspect runner_response for stdout/stderr diagnostics.", "Retry after reinstalling or repairing the plugin cache."],
    )


def run_python_runner_subprocess(
    argv: list[str],
    *,
    selected_candidate: str | None,
    input_text: str,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    if selected_candidate in {"py -V:3", "py -3"}:
        if len(argv) < 2 or program_name(argv[0]) != "py" or argv[1] != "-3":
            raise OSError("selected py launcher invocation does not match its validated prefix")
        return subprocess.run(
            ["py", "-3", *argv[2:]],
            input=input_text,
            text=True,
            capture_output=True,
            timeout=10,
            shell=False,
            cwd=cwd,
            check=False,
        )
    if selected_candidate == "python3":
        if not argv or program_name(argv[0]) != "python3":
            raise OSError("selected python3 invocation does not match its validated prefix")
        return subprocess.run(
            ["python3", *argv[1:]],
            input=input_text,
            text=True,
            capture_output=True,
            timeout=10,
            shell=False,
            cwd=cwd,
            check=False,
        )
    if selected_candidate == "python":
        if not argv or program_name(argv[0]) != "python":
            raise OSError("selected python invocation does not match its validated prefix")
        return subprocess.run(
            ["python", *argv[1:]],
            input=input_text,
            text=True,
            capture_output=True,
            timeout=10,
            shell=False,
            cwd=cwd,
            check=False,
        )
    if selected_candidate is not None or not argv or not resolves_to_current_python(argv[0]):
        raise OSError("runner invocation executable is not the active Python interpreter")
    return subprocess.run(
        [sys.executable, *argv[1:]],
        input=input_text,
        text=True,
        capture_output=True,
        timeout=10,
        shell=False,
        cwd=cwd,
        check=False,
    )


def malformed_runner_response(completed: subprocess.CompletedProcess[str], parsed_type: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "status": "subprocess_failure",
        "exit_code": completed.returncode,
        "legacy_exit_code": None,
        "diagnostics": [],
        "data": {
            "stdout_preview": completed.stdout[:200],
            "stderr_preview": completed.stderr[:200],
            "parsed_type": parsed_type,
        },
    }


def validate_runner_runtime_response(parsed: dict[str, Any], cwd: Path, cache_root: str) -> dict[str, Any] | None:
    data = parsed.get("data")
    report = data.get("report") if isinstance(data, dict) else None
    if not isinstance(report, dict):
        return runner_identity_mismatch(cache_root, "runner runtime-info response did not include a report")

    expected = {
        "runner_name": "speckit_pro_runner",
        "runner_contract_id": "speckit-pro-runner",
        "selected_runtime_name": "python-stdlib-runner",
        "source_vs_installed_context": "installed_payload",
    }
    for key, value in expected.items():
        if report.get(key) != value:
            return runner_identity_mismatch(
                cache_root,
                "runner runtime-info response did not match installed runner identity",
                details={"field": key, "expected": value, "actual": report.get(key)},
            )

    paths = report.get("paths")
    if not isinstance(paths, dict):
        return runner_identity_mismatch(cache_root, "runner runtime-info response did not include path records")

    required_paths = {
        "plugin_root": ".",
        "runner_package": "speckit_pro_runner",
        "manifest_file": "speckit_pro_runner/speckit-pro-runner.manifest.json",
        "checksum_file": "speckit_pro_runner/speckit-pro-runner.sha256",
    }
    for key, expected_value in required_paths.items():
        record = paths.get(key)
        if not isinstance(record, dict) or record.get("value") != expected_value:
            return runner_identity_mismatch(
                cache_root,
                "runner runtime-info response path records did not match installed payload layout",
                details={
                    "field": key,
                    "expected": expected_value,
                    "actual": record.get("value") if isinstance(record, dict) else None,
                },
            )
        if key != "plugin_root" and not (cwd / expected_value).exists():
            return runner_identity_mismatch(
                cache_root,
                "runner runtime-info response path record does not exist in installed payload",
                details={"field": key, "path": expected_value},
            )
    return None


def runner_identity_mismatch(cache_root: str, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
    merged_details: dict[str, Any] = {"cache_root": cache_root}
    if details:
        merged_details.update(details)
    return diagnostic(
        "runner_identity_mismatch",
        message,
        details=merged_details,
        remediation_summary="Ensure the selected installed cache executes the shipped SpecKit Pro runner package.",
        remediation_actions=[
            "Rebuild generated Claude and Codex payloads.",
            "Verify runtime-info reports the expected runner identity and installed payload paths.",
        ],
    )


def candidate_order(platform_name: str) -> list[str]:
    if platform_name == "windows":
        return ["py -V:3", "py -3", "python", "python3"]
    return ["python3", "python"]


def host_platform() -> str:
    system = platform_module.system().lower()
    if system.startswith("win"):
        return "windows"
    if system == "darwin":
        return "macos"
    return "linux"


def parse_version(version: str) -> tuple[int, int, int]:
    parts: list[int] = []
    for part in version.split(".")[:3]:
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)  # type: ignore[return-value]


def normalize_enum(value: Any, allowed: set[str], fallback: str) -> str:
    text = value if isinstance(value, str) else fallback
    return text if text in allowed else fallback


def runner_invocation_base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    gate_status = "pass"
    if status in {"expected_failure", "subprocess_failure"}:
        gate_status = "fail"
    elif status == "missing_prerequisite":
        gate_status = "skipped"
    elif status == "input_error":
        gate_status = "input_error"
    promotion_record = XPLAT_008_PROMOTION_RECORDS.as_posix()
    case_file = DEFAULT_RUNNER_INVOCATION_CASES.as_posix()
    return {
        "gate": {
            "gate_id": entry.helper_id,
            "operation": operation,
            "gate_status": gate_status,
            "promoted": status != "input_error",
            "blocking": status != "ok",
            "comparison_ids": [f"xplat-008-{operation}"],
            "promotion_record": promotion_record,
        },
        "artifacts": [
            {"path": promotion_record, "kind": "promotion_record"},
            {"path": case_file, "kind": "fixture"},
        ],
    }


def install_root_from_inputs(inputs: dict[str, Any], repo_root: Path) -> Path | dict[str, Any]:
    raw = inputs.get("install_root")
    if not isinstance(raw, str) or not raw:
        return diagnostic(
            "invalid_input",
            "install_root is required",
            details={"field": "install_root"},
            remediation_summary="Send a repo-relative fake install root for fixture-backed repair.",
            remediation_actions=["Set install_root to a directory inside the repo fixture tree."],
        )
    path_diag = validate_target_path(f"{raw}/.speckit-pro-install-probe", repo_root)
    if path_diag is not None:
        return path_diag
    return resolve_input_path(raw, repo_root)


def resolve_case_path(raw: str, repo_root: Path) -> Path:
    path = Path(raw.replace("\\", "/"))
    return path if path.is_absolute() else repo_root / path


def inventory_from_inputs(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    raw = inputs.get("inventory")
    if raw is None:
        inventory_path = repo_root / "speckit-pro" / "speckit_pro_runner" / INVENTORY_NAME
        try:
            raw = json.loads(inventory_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return diagnostic(
                "malformed_inventory",
                "install inventory could not be loaded",
                details={"path": repo_relative(inventory_path, repo_root), "error": type(exc).__name__},
                remediation_summary="Refresh the committed install inventory.",
                remediation_actions=["Regenerate install_inventory.json.", "Retry doctor-preflight."],
            )
    if not isinstance(raw, dict):
        return malformed_inventory("inventory must be an object")
    files = raw.get("files")
    if not isinstance(files, list):
        return malformed_inventory("inventory.files must be an array")
    normalized_files: list[dict[str, str]] = []
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            return malformed_inventory("inventory file records must be objects", index=index)
        path = item.get("path")
        content = item.get("content")
        digest = item.get("sha256", "skip")
        if not isinstance(path, str) or not path:
            return malformed_inventory("inventory file path must be repo-relative without traversal", index=index)
        normalized_path = path.replace("\\", "/")
        parts = PurePosixPath(normalized_path).parts
        if normalized_path.startswith("/") or any(part in {"", ".", ".."} for part in parts):
            return malformed_inventory("inventory file path must be repo-relative without traversal", index=index)
        if not isinstance(content, str):
            return malformed_inventory("inventory file content must be a string", index=index)
        if not isinstance(digest, str) or not digest:
            return malformed_inventory("inventory sha256 must be a string", index=index)
        normalized_files.append({"path": normalized_path, "content": content, "sha256": digest})
    return {"files": normalized_files}


def fake_home_boundary_diagnostic(install_root: Path, repo_root: Path) -> dict[str, Any] | None:
    allowed_root = repo_root / FAKE_HOME_FIXTURE_ROOT
    if is_relative_to(install_root.resolve(strict=False), allowed_root.resolve(strict=False)):
        return None
    return diagnostic(
        "fake_home_boundary_refused",
        "fake_home true is only trusted inside the fixture fake-home boundary",
        details={"install_root": repo_relative(install_root, repo_root), "allowed_root": repo_relative(allowed_root, repo_root)},
        remediation_summary="Use fake_home only with repo fixture roots until active install cutover.",
        remediation_actions=[
            "Move the install_root under tests/speckit-pro/unit/fixtures.",
            "Use doctor-preflight without fake_home for real installs.",
        ],
    )


def repair_target_boundary_diagnostic(target: Path, install_root: Path, repo_root: Path) -> dict[str, Any] | None:
    if is_relative_to(target.resolve(strict=False), install_root.resolve(strict=False)):
        return None
    return diagnostic(
        "install_root_escape",
        "repair target escapes the selected install_root",
        details={"target": repo_relative(target, repo_root), "install_root": repo_relative(install_root, repo_root)},
        remediation_summary="Keep install inventory repair paths inside install_root.",
        remediation_actions=["Remove traversal from the inventory path.", "Retry doctor-repair with a normalized inventory."],
    )


def malformed_inventory(message: str, *, index: int | None = None) -> dict[str, Any]:
    details: dict[str, Any] = {}
    if index is not None:
        details["file_index"] = index
    return diagnostic(
        "malformed_inventory",
        message,
        details=details,
        remediation_summary="Use the committed install inventory schema.",
        remediation_actions=["Inspect install_inventory.json.", "Retry with files containing path, content, and sha256."],
    )


def doctor_report(install_root: Path, inventory: dict[str, Any], repo_root: Path, *, fake_home: bool) -> dict[str, Any]:
    missing: list[str] = []
    mismatches: list[str] = []
    for record in inventory["files"]:
        target = install_root / record["path"]
        if not target.is_file():
            missing.append(record["path"])
            continue
        digest = record["sha256"]
        if digest != "skip" and sha256_text(target.read_text(encoding="utf-8", errors="replace")) != digest:
            mismatches.append(record["path"])

    status = "complete"
    if missing or mismatches:
        status = "safe_repair" if fake_home else "blocked"
    return {
        "status": status,
        "install_root": repo_relative(install_root, repo_root),
        "fake_home": fake_home,
        "missing_files": missing,
        "checksum_mismatches": mismatches,
        "safe_repairs": missing + mismatches if fake_home else [],
        "unsafe_manual_remediations": [] if fake_home else missing + mismatches,
        "blocked": bool((missing or mismatches) and not fake_home),
        "inventory_file_count": len(inventory["files"]),
    }
