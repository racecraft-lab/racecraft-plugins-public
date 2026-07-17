#!/usr/bin/env python3
"""Vendor-neutral G56R-002 telemetry and exact-treatment validation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import ipaddress
import importlib.util
import json
import os
import re
import stat
import sys
from collections.abc import Mapping
from datetime import datetime
from functools import lru_cache
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = ROOT / "specs/g56r-002-capability-discovery-telemetry/contracts/treatment-record.schema.json"
MANIFEST_PATH = ROOT / "docs/ai/research/codex-agent-route-candidate-manifest.json"
CAPABILITY_MODULE_PATH = Path(__file__).with_name("codex_capabilities.py")
MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_NESTING_DEPTH = 64
MAX_COLLECTION_ITEMS = 10_000
MAX_TOTAL_NODES = 100_000
MAX_RETAINED_STRING_LENGTH = 8_192
HAS_DESCRIPTOR_RELATIVE_IO = os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd
IS_WINDOWS = os.name == "nt"

CAPABILITY_FIXTURE_PATH = "tests/speckit-pro/unit/fixtures/capability-treatment-replay/capability-matrix.json"
TREATMENT_FIXTURE_PATH = "tests/speckit-pro/unit/fixtures/capability-treatment-replay/treatment-replay.json"
REPLAY_FIXTURE_PATHS = (CAPABILITY_FIXTURE_PATH, TREATMENT_FIXTURE_PATH)
REPLAY_CASES = (
    ("TRACE-SUCCESS", "success", "unknown", ("effective_treatment_unknown",), None),
    ("TRACE-EXPLICIT-NULL", "explicit_null", "unknown", ("effective_treatment_unknown",), None),
    ("TRACE-UNAVAILABLE", "unavailable", "unknown", ("effective_treatment_unknown",), None),
    ("TRACE-MISDELIVERY", "misdelivery", "hard_fail", ("agent_mismatch", "effective_treatment_unknown"), None),
    ("TRACE-APPROVED-SAME-AGENT-REROUTE", "approved_same_agent_reroute", "non_scorable_rerouted", ("service_reroute_requested_route_non_scorable",), None),
    ("TRACE-UNAPPROVED-UNIDENTIFIABLE-REROUTE", "unapproved_unidentifiable_reroute", "hard_fail", ("reroute_unidentifiable",), None),
    ("TRACE-DISCOVERY-LOSS", "discovery_loss", "unknown", ("effective_treatment_unknown",), "partial_surface"),
    ("TRACE-SURFACE-DISAGREEMENT", "surface_disagreement", "unknown", ("effective_treatment_unknown",), "surface_disagreement"),
)

SCHEMA_VERSION = "1.0.0"
SURFACES = ("app_server", "cli", "interactive_picker")
CLASSIFICATIONS = (
    "stable_native", "experimental_native", "derived_from_controlled_configuration",
    "conditional", "unavailable", "not_applicable", "undocumented",
)
OBSERVATION_STATES = (
    "observed_value", "explicit_null", "missing", "unavailable",
    "not_applicable", "undocumented",
)
OBJECTIVE_ID_FIELDS = (
    "candidate_route_id", "agent_contract_id", "runtime_capability_snapshot_id",
    "route_resolution_id", "experiment_policy_id", "execution_trace_id",
)

APP_SERVER_FIELDS = frozenset({
    "discovery.models", "discovery.efforts", "discovery.capabilities",
    "assignment.named_agent", "assignment.model", "assignment.effort",
    "assignment.supported_effective_model", "assignment.supported_effective_effort",
    "assignment.candidate_route_id", "assignment.agent_contract_id",
    "assignment.instruction_hash", "assignment.configuration_hash",
    "route.preferred_route_id", "route.attempted_route_ids", "route.assigned_route_id",
    "route.supported_effective_route_id", "route.fallback_index", "route.fallback_reason",
    "route.runtime_capability_snapshot_id", "route.resolved_at", "reroute.events",
    "treatment.sandbox", "treatment.approvals", "treatment.mutation_class",
    "treatment.expected_skills_mcp_tools", "treatment.loaded_skills_mcp_tools",
    "treatment.parent_configuration", "treatment.controlled_overrides",
    "treatment.delivery_canary", "treatment.failures", "parent.context", "parent.graph",
    "resources.raw_token_vector", "resources.request_turn_count", "resources.wall_time_ms",
    "lifecycle.retries", "lifecycle.compaction", "lifecycle.validation",
    "lifecycle.cancellation", "lifecycle.failed_abandoned_work", "terminal.state",
    "terminal.outcome", "terminal.acceptance",
})
TELEMETRY_INVENTORY = frozenset(
    {("app_server", field) for field in APP_SERVER_FIELDS}
    | {("cli", "route.supported_effective_route_id"), ("interactive_picker", "parent.graph")}
)

AUTHORIZED_PROFILE_SOURCES = {
    **{("app_server", field): "OPENAI-DOC-006" for field in {
        "discovery.models", "discovery.efforts", "discovery.capabilities",
        "assignment.supported_effective_model",
        "route.supported_effective_route_id", "reroute.events", "treatment.loaded_skills_mcp_tools",
        "treatment.delivery_canary", "parent.context", "parent.graph", "resources.raw_token_vector",
        "resources.request_turn_count", "lifecycle.compaction", "lifecycle.cancellation",
    }},
    **{("app_server", field): "OPENAI-DOC-003" for field in {
        "assignment.named_agent", "assignment.model", "assignment.effort", "assignment.candidate_route_id",
        "assignment.agent_contract_id", "assignment.instruction_hash", "assignment.configuration_hash",
        "treatment.mutation_class", "treatment.expected_skills_mcp_tools", "treatment.parent_configuration",
    }},
    **{("app_server", field): "OPENAI-DOC-004" for field in {
        "route.preferred_route_id", "route.attempted_route_ids", "route.assigned_route_id",
        "route.fallback_index", "route.fallback_reason", "route.runtime_capability_snapshot_id",
        "route.resolved_at", "treatment.controlled_overrides",
    }},
    **{("app_server", field): "OPENAI-DOC-010" for field in {"treatment.sandbox", "treatment.approvals"}},
    **{("app_server", field): "OPENAI-DOC-007" for field in {
        "lifecycle.validation", "lifecycle.failed_abandoned_work", "terminal.state",
        "terminal.outcome", "terminal.acceptance",
    }},
    ("app_server", "treatment.failures"): None,
    ("app_server", "assignment.supported_effective_effort"): None,
    ("app_server", "resources.wall_time_ms"): None,
    ("app_server", "lifecycle.retries"): None,
    ("cli", "route.supported_effective_route_id"): None,
    ("interactive_picker", "parent.graph"): "OPENAI-DOC-006",
}
if set(AUTHORIZED_PROFILE_SOURCES) != TELEMETRY_INVENTORY:
    raise RuntimeError("field-level telemetry source map does not cover the closed inventory")

AUTHORIZED_PROFILE_CLASSIFICATIONS = {
    **{("app_server", field): "stable_native" for field in {
        "discovery.models", "discovery.efforts", "discovery.capabilities", "parent.context",
        "resources.raw_token_vector", "resources.request_turn_count", "lifecycle.failed_abandoned_work",
        "terminal.state", "terminal.outcome",
    }},
    **{("app_server", field): "experimental_native" for field in {
        "route.supported_effective_route_id", "treatment.loaded_skills_mcp_tools",
        "treatment.delivery_canary", "lifecycle.compaction",
    }},
    **{("app_server", field): "derived_from_controlled_configuration" for field in {
        "assignment.named_agent", "assignment.model", "assignment.effort", "assignment.candidate_route_id",
        "assignment.agent_contract_id", "assignment.instruction_hash", "assignment.configuration_hash",
        "route.preferred_route_id", "route.attempted_route_ids", "route.assigned_route_id",
        "route.fallback_index", "route.fallback_reason", "route.runtime_capability_snapshot_id",
        "route.resolved_at", "treatment.sandbox", "treatment.approvals", "treatment.mutation_class",
        "treatment.expected_skills_mcp_tools", "treatment.parent_configuration",
        "treatment.controlled_overrides",
    }},
    **{("app_server", field): "conditional" for field in {
        "assignment.supported_effective_model", "reroute.events", "parent.graph",
        "lifecycle.validation", "lifecycle.cancellation",
    }},
    **{("app_server", field): "undocumented" for field in {
        "assignment.supported_effective_effort", "treatment.failures", "resources.wall_time_ms",
        "lifecycle.retries",
    }},
    ("app_server", "terminal.acceptance"): "unavailable",
    ("cli", "route.supported_effective_route_id"): "undocumented",
    ("interactive_picker", "parent.graph"): "not_applicable",
}
if set(AUTHORIZED_PROFILE_CLASSIFICATIONS) != TELEMETRY_INVENTORY:
    raise RuntimeError("field-level telemetry classification map does not cover the closed inventory")
if any(
    (AUTHORIZED_PROFILE_SOURCES[key] is None) != (classification == "undocumented")
    for key, classification in AUTHORIZED_PROFILE_CLASSIFICATIONS.items()
):
    raise RuntimeError("field-level telemetry source and classification authority maps disagree")

AUTHORIZED_PROFILE_CONDITIONS = {key: None for key in TELEMETRY_INVENTORY}
AUTHORIZED_PROFILE_CONDITIONS.update({
    ("app_server", "assignment.supported_effective_model"): "model/rerouted observes a destination model",
    ("app_server", "reroute.events"): "model/rerouted is emitted for a service reroute",
    ("app_server", "parent.graph"): "parent and child identifiers are emitted for nested work",
    ("app_server", "lifecycle.validation"): "validation evidence is emitted when validation runs",
    ("app_server", "lifecycle.cancellation"): "cancellation evidence is emitted when cancellation is requested",
    ("interactive_picker", "parent.graph"): "interactive picker collection has no execution parent graph",
})
AUTHORIZED_PROHIBITED_CLAIMS = {
    key: (["effective_treatment"] if classification == "derived_from_controlled_configuration"
          else ["configured_as_effective", "unsupported_platform_value"])
    for key, classification in AUTHORIZED_PROFILE_CLASSIFICATIONS.items()
}

COMPLETENESS_BY_CLASS = {
    "stable_native": "complete_capture",
    "experimental_native": "pinned_build_observation_only",
    "derived_from_controlled_configuration": "consumed_configuration_only",
    "conditional": "condition_bound",
    "unavailable": "known_unavailable",
    "not_applicable": "false_applicability",
    "undocumented": "no_authority",
}
CLAIM_BY_CLASS = {
    "stable_native": "observed_value",
    "experimental_native": "pinned_build_value",
    "derived_from_controlled_configuration": "requested_assignment",
    "conditional": "condition_bound_presence",
}
FAILURE_DISPOSITIONS = {
    "agent_mismatch": "hard_fail", "model_mismatch": "hard_fail",
    "effort_mismatch": "hard_fail", "configuration_mismatch": "hard_fail",
    "sandbox_approvals_mismatch": "hard_fail", "mutation_class_mismatch": "hard_fail",
    "skills_mcp_tools_mismatch": "hard_fail", "parent_configuration_mismatch": "hard_fail",
    "client_or_override_mismatch": "hard_fail", "delivery_canary_failure": "unknown",
    "effective_treatment_unknown": "unknown", "reroute_unapproved": "hard_fail",
    "reroute_unidentifiable": "hard_fail", "reroute_ambiguous": "hard_fail",
    "reroute_different_agent": "hard_fail",
}
INTERNAL_DERIVED_FIELDS = frozenset({"treatment.failures"})
DISPOSITION_REASON_CODES = frozenset(set(FAILURE_DISPOSITIONS) | {
    "configured_route_proof_and_complete_reroute_monitoring",
    "profile_supported_effective_treatment",
    "effective_treatment_or_reroute_evidence_missing",
    "service_reroute_requested_route_non_scorable",
    "reroute_association_mismatch", "ambiguous_reroute_association",
    "reroute_destination_missing", "reroute_destination_ambiguous",
    "reroute_destination_unapproved", "reroute_destination_mismatch",
    "reroute_destination_unidentifiable", "reroute_destination_manifest_mismatch",
    "reroute_destination_different_agent", "reroute_destination_model_mismatch",
    "reroute_destination_non_authoritative", "reroute_destination_untrusted",
    "reroute_effective_destination_mismatch", "reroute_source_model_mismatch",
    "orphan_reroute_destination_assessment",
})

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SOURCE_RE = re.compile(r"^OPENAI-DOC-[0-9]{3}$")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
EVIDENCE_REF_RE = re.compile(r"^fixture://[a-z0-9][a-z0-9._-]*(?:/[a-z0-9][a-z0-9._-]*)*$")
ABSOLUTE_PATH_RE = re.compile(
    r"(?ix)(?:^//(?=[^/])|(?<![a-z0-9._~+/\-])/(?!/)"
    r"|(?<![a-z0-9._-])[a-z]:[\\/]|(?<![\\a-z0-9._-])\\\\[a-z0-9._-]+[\\/])"
)
TRAVERSAL_RE = re.compile(r"(?:^|[\\/])\.\.(?:[\\/]|$)|(?<![A-Za-z0-9._~+\-])~[\\/]")
RFC3339_UTC_RE = re.compile(
    r"^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.[0-9]+)?Z$"
)
REMOTE_RE = re.compile(r"(?i)(?:\b(?:https?|ssh|git|file)://|\bgit@[a-z0-9.-]+:)")
CREDENTIAL_RE = re.compile(
    r"(?i)(?:\b(?:authorization|credential|secret|api[_-]?key|cookie|password)\b\s*[:=]"
    r"|\bbearer\s+[A-Za-z0-9._~+/=-]+|\b(?:sk|ghp|github_pat|xox[baprs])[-_][A-Za-z0-9_-]{8,})"
)
UNLABELED_CREDENTIAL_RE = re.compile(
    r"(?:\b(?:AKIA|ASIA|AIDA|AROA|AIPA|ANPA|ANVA|ASCA)[A-Z0-9]{16}\b"
    r"|\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b)"
)
PII_RE = re.compile(
    r"(?i)(?:\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b)"
)
HOSTNAME_RE = re.compile(
    r"(?i)(?<![A-Z0-9_-])(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.){2,}[A-Z]{2,63}(?![A-Z0-9_-])"
)
INTERNAL_HOSTNAME_RE = re.compile(
    r"(?i)(?<![A-Z0-9_-])[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.(?:internal|local|lan|corp|home)(?![A-Z0-9_-])"
)
IP_CANDIDATE_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:[0-9]{1,3}(?:\.[0-9]{1,3}){3}|[0-9A-Fa-f]*:[0-9A-Fa-f:]+)(?![A-Za-z0-9])"
)
SANITIZED_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+-]{0,127}$")
SPEC_ID_RE = re.compile(r"^[A-Z][A-Z0-9]*-[0-9]{3}$")
FALLBACK_REASON_CODES = frozenset({"preferred_unavailable", "capability_mismatch", "policy_fallback"})
REROUTE_REASON_CODES = frozenset({
    "service_capacity", "service_policy", "service_availability",
    "fixture_service_reroute", "fixture_second_service_reroute",
})
CANCELLATION_REASON_CODES = frozenset({"user_requested", "timeout", "superseded", "policy_denied"})


def _current_source_ids(manifest: dict) -> frozenset[str]:
    ids = frozenset(item["official_source_ledger_id"] for item in manifest["official_source_ledger"])
    if len(ids) != 22 or any(SOURCE_RE.fullmatch(item) is None for item in ids):
        raise ValueError("canonical manifest does not expose exactly 22 current source owners")
    return ids


def _canonical_routes(manifest: dict) -> dict[str, dict[str, object]]:
    agents = {item["agent_contract_id"]: item["agent_name"] for item in manifest["agent_contracts"]}
    routes = {}
    for item in manifest["candidate_routes"]:
        contract = item["agent_contract_id"]
        required_capabilities = item["required_capabilities"]
        if (
            not isinstance(required_capabilities, list) or not required_capabilities
            or any(not isinstance(value, str) or not value for value in required_capabilities)
            or len(required_capabilities) != len(set(required_capabilities))
        ):
            raise ValueError("canonical manifest route capabilities are invalid")
        routes[item["candidate_route_id"]] = {
            "agent_contract_id": contract,
            "named_agent": agents[contract],
            "model": item["model_selector"]["expected_resolved_model_id"],
            "effort": item["effort_selector"]["requested_value"],
            "required_capabilities": list(required_capabilities),
        }
    if len(routes) != len(manifest["candidate_routes"]):
        raise ValueError("canonical manifest candidate routes are not uniquely owned")
    return routes


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _stable_file_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns,
        metadata.st_ctime_ns, stat.S_IMODE(metadata.st_mode), metadata.st_nlink,
    )


def _stable_directory_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode), stat.S_IMODE(metadata.st_mode)


def _normalized_path(path: Path) -> str:
    return os.path.normcase(os.path.abspath(path))


def _windows_final_path_from_descriptor(descriptor: int) -> Path:
    try:
        import ctypes
        import msvcrt
        from ctypes import wintypes
    except ImportError as exc:  # pragma: no cover - available on supported Windows Python
        raise ValueError("bounded input cannot inspect its Windows file handle") from exc
    get_final_path = ctypes.WinDLL("kernel32", use_last_error=True).GetFinalPathNameByHandleW
    get_final_path.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    get_final_path.restype = wintypes.DWORD
    handle = wintypes.HANDLE(msvcrt.get_osfhandle(descriptor))
    required = get_final_path(handle, None, 0, 0)
    if required == 0:
        raise ValueError("bounded input cannot resolve its Windows file handle")
    buffer = ctypes.create_unicode_buffer(required + 1)
    written = get_final_path(handle, buffer, len(buffer), 0)
    if written == 0 or written >= len(buffer):
        raise ValueError("bounded input cannot resolve its Windows file handle")
    value = buffer.value
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return Path(value)


def _handle_bound_path_snapshot(source: Path, root: Path, relative: Path) -> tuple[
    tuple[int, ...], list[tuple[int, ...]], os.stat_result, Path,
]:
    try:
        canonical_root = root.resolve(strict=True)
        canonical_source = source.resolve(strict=True)
        if _normalized_path(canonical_root) != _normalized_path(root):
            raise ValueError("bounded input approved root must be a real directory")
        if _normalized_path(canonical_source) != _normalized_path(source):
            raise ValueError("bounded input path components must be real directories and the file non-symlink")
        canonical_source.relative_to(canonical_root)
        root_metadata = os.stat(root, follow_symlinks=False)
        if not stat.S_ISDIR(root_metadata.st_mode):
            raise ValueError("bounded input approved root must be a real directory")
        directory_identities: list[tuple[int, ...]] = []
        current = root
        for component in relative.parts[:-1]:
            current /= component
            metadata = os.stat(current, follow_symlinks=False)
            if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
                raise ValueError("bounded input path components must be real directories")
            directory_identities.append(_stable_directory_identity(metadata))
        pathname = os.stat(source, follow_symlinks=False)
    except OSError as exc:
        raise ValueError("bounded input must be a readable regular non-symlink file") from exc
    except ValueError:
        raise
    if not stat.S_ISREG(pathname.st_mode) or stat.S_ISLNK(pathname.st_mode) or pathname.st_nlink != 1:
        raise ValueError("bounded input must be a single-link regular non-symlink file")
    return _stable_directory_identity(root_metadata), directory_identities, pathname, canonical_source


def _read_bounded_regular_file_by_handle(source: Path, root: Path, relative: Path, max_bytes: int) -> bytes:
    root_identity, directory_identities, pathname_before, canonical_source = _handle_bound_path_snapshot(
        source, root, relative,
    )
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOINHERIT", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(source, flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("bounded input must be a single-link regular file")
        if _stable_file_identity(pathname_before) != _stable_file_identity(before):
            raise ValueError("bounded input pathname changed before it was read")
        if IS_WINDOWS and _normalized_path(_windows_final_path_from_descriptor(descriptor)) != _normalized_path(canonical_source):
            raise ValueError("bounded input Windows handle escaped its approved path")
        if before.st_size > max_bytes:
            raise ValueError("bounded input exceeds the maximum size")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("bounded input exceeds the maximum size")
        after = os.fstat(descriptor)
        if _stable_file_identity(after) != _stable_file_identity(before) or total != after.st_size:
            raise ValueError("bounded input changed while it was being read")
        current_root, current_directories, current_pathname, current_canonical = _handle_bound_path_snapshot(
            source, root, relative,
        )
        if (
            current_root != root_identity
            or current_directories != directory_identities
            or _stable_file_identity(current_pathname) != _stable_file_identity(after)
            or _normalized_path(current_canonical) != _normalized_path(canonical_source)
        ):
            raise ValueError("bounded input path changed while it was being read")
        return b"".join(chunks)
    except OSError as exc:
        raise ValueError("bounded input must be a readable regular non-symlink file") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_bounded_regular_file(path: Path, *, allowed_root: Path = ROOT,
                               max_bytes: int = MAX_INPUT_BYTES) -> bytes:
    source = Path(os.path.abspath(path)); root = Path(os.path.abspath(allowed_root))
    try:
        relative = source.relative_to(root)
    except ValueError as exc:
        raise ValueError("bounded input must remain inside its approved root") from exc
    if not relative.parts:
        raise ValueError("bounded input must name a file below its approved root")
    if not HAS_DESCRIPTOR_RELATIVE_IO:
        return _read_bounded_regular_file_by_handle(source, root, relative, max_bytes)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow | getattr(os, "O_DIRECTORY", 0)
    file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow
    directory_descriptors: list[int] = []
    directory_identities: list[tuple[int, ...]] = []
    descriptor: int | None = None
    try:
        root_before = os.stat(root, follow_symlinks=False)
        if not stat.S_ISDIR(root_before.st_mode):
            raise ValueError("bounded input approved root must be a real directory")
        root_descriptor = os.open(root, directory_flags)
        directory_descriptors.append(root_descriptor)
        root_open = os.fstat(root_descriptor)
        if _stable_directory_identity(root_before) != _stable_directory_identity(root_open):
            raise ValueError("bounded input approved root changed before it was opened")
        directory_identities.append(_stable_directory_identity(root_open))
        parent_descriptor = root_descriptor
        for component in relative.parts[:-1]:
            component_before = os.stat(component, dir_fd=parent_descriptor, follow_symlinks=False)
            if not stat.S_ISDIR(component_before.st_mode):
                raise ValueError("bounded input path components must be real directories")
            child_descriptor = os.open(component, directory_flags, dir_fd=parent_descriptor)
            child_open = os.fstat(child_descriptor)
            if _stable_directory_identity(component_before) != _stable_directory_identity(child_open):
                os.close(child_descriptor)
                raise ValueError("bounded input directory changed before it was opened")
            directory_descriptors.append(child_descriptor)
            directory_identities.append(_stable_directory_identity(child_open))
            parent_descriptor = child_descriptor
        filename = relative.parts[-1]
        pathname_before = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
        if not stat.S_ISREG(pathname_before.st_mode) or pathname_before.st_nlink != 1:
            raise ValueError("bounded input must be a single-link regular non-symlink file")
        descriptor = os.open(filename, file_flags, dir_fd=parent_descriptor)
    except OSError as exc:
        if descriptor is not None:
            os.close(descriptor)
        for directory_descriptor in reversed(directory_descriptors):
            os.close(directory_descriptor)
        raise ValueError("bounded input must be a readable regular non-symlink file") from exc
    except ValueError:
        if descriptor is not None:
            os.close(descriptor)
        for directory_descriptor in reversed(directory_descriptors):
            os.close(directory_descriptor)
        raise
    try:
        if descriptor is None:
            raise ValueError("bounded input could not be opened safely")
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("bounded input must be a single-link regular file")
        if _stable_file_identity(pathname_before) != _stable_file_identity(before):
            raise ValueError("bounded input pathname changed before it was read")
        if before.st_size > max_bytes:
            raise ValueError("bounded input exceeds the maximum size")
        chunks: list[bytes] = []; total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk: break
            chunks.append(chunk); total += len(chunk)
            if total > max_bytes: raise ValueError("bounded input exceeds the maximum size")
        after = os.fstat(descriptor)
        if _stable_file_identity(after) != _stable_file_identity(before) or total != after.st_size:
            raise ValueError("bounded input changed while it was being read")
        current = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
        if _stable_file_identity(current) != _stable_file_identity(after):
            raise ValueError("bounded input pathname changed while it was being read")
        verifier_descriptors: list[int] = []
        try:
            root_current = os.stat(root, follow_symlinks=False)
            verifier = os.open(root, directory_flags)
            verifier_descriptors.append(verifier)
            if _stable_directory_identity(root_current) != directory_identities[0] or _stable_directory_identity(os.fstat(verifier)) != directory_identities[0]:
                raise ValueError("bounded input approved root changed while it was being read")
            for component, expected_identity in zip(relative.parts[:-1], directory_identities[1:]):
                next_descriptor = os.open(component, directory_flags, dir_fd=verifier)
                verifier_descriptors.append(next_descriptor)
                if _stable_directory_identity(os.fstat(next_descriptor)) != expected_identity:
                    raise ValueError("bounded input directory changed while it was being read")
                verifier = next_descriptor
            current_path = os.stat(filename, dir_fd=verifier, follow_symlinks=False)
            if _stable_file_identity(current_path) != _stable_file_identity(after):
                raise ValueError("bounded input path changed while it was being read")
        except OSError as exc:
            raise ValueError("bounded input path changed while it was being read") from exc
        finally:
            for verifier_descriptor in reversed(verifier_descriptors):
                os.close(verifier_descriptor)
        return b"".join(chunks)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        for directory_descriptor in reversed(directory_descriptors):
            os.close(directory_descriptor)


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result: raise ValueError("input contains a duplicate JSON object key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-JSON numeric constant: {value}")


def _parse_json_bytes(raw: bytes) -> object:
    try:
        return json.loads(
            raw.decode("utf-8", errors="strict"), object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("input must be strict UTF-8 JSON") from exc


def _read_json_file(path: Path, *, allowed_root: Path = ROOT) -> object:
    return _parse_json_bytes(_read_bounded_regular_file(path, allowed_root=allowed_root))


def _read_manifest_snapshot(path: Path) -> dict:
    manifest = _read_json_file(path)
    if not isinstance(manifest, dict):
        raise ValueError("candidate manifest must be a JSON object")
    _validate_resource_bounds(manifest)
    _capability_module().validate_manifest(manifest)
    return manifest


def _validate_resource_bounds(value: object, *, depth: int = 0, counter: list[int] | None = None) -> None:
    if counter is None: counter = [0]
    counter[0] += 1
    if counter[0] > MAX_TOTAL_NODES: raise ValueError("treatment input exceeds the maximum node count")
    if depth > MAX_NESTING_DEPTH: raise ValueError("treatment input exceeds the maximum nesting depth")
    if isinstance(value, str) and len(value) > MAX_RETAINED_STRING_LENGTH:
        raise ValueError("treatment input contains an oversized retained string")
    if isinstance(value, (list, dict)):
        if len(value) > MAX_COLLECTION_ITEMS: raise ValueError("treatment input contains an oversized collection")
        if isinstance(value, dict):
            for key, item in value.items():
                _validate_resource_bounds(key, depth=depth + 1, counter=counter)
                _validate_resource_bounds(item, depth=depth + 1, counter=counter)
        else:
            for item in value:
                _validate_resource_bounds(item, depth=depth + 1, counter=counter)


def _json_type_matches(value: object, expected: str) -> bool:
    return {
        "null": value is None,
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "string": isinstance(value, str),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
    }.get(expected, False)


def _schema_matches(value: object, schema: object, root: dict, path: str) -> bool:
    try:
        _validate_schema_instance(value, schema, root, path)
    except ValueError:
        return False
    return True


def _resolve_schema_ref(root: dict, reference: str) -> object:
    if not reference.startswith("#/"):
        raise ValueError("treatment schema may only use local references")
    current: object = root
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            raise ValueError("treatment schema contains an unresolved local reference")
        current = current[token]
    return current


def _validate_schema_instance(value: object, schema: object, root: dict, path: str = "$") -> None:
    if schema is True: return
    if schema is False or not isinstance(schema, dict):
        raise ValueError(f"{path} is rejected by the treatment JSON Schema")
    if "$ref" in schema:
        _validate_schema_instance(value, _resolve_schema_ref(root, schema["$ref"]), root, path)
    for branch in schema.get("allOf", []):
        _validate_schema_instance(value, branch, root, path)
    if "anyOf" in schema and not any(_schema_matches(value, branch, root, path) for branch in schema["anyOf"]):
        raise ValueError(f"{path} does not match any allowed treatment schema shape")
    if "oneOf" in schema and sum(_schema_matches(value, branch, root, path) for branch in schema["oneOf"]) != 1:
        raise ValueError(f"{path} does not match exactly one treatment schema shape")
    if "not" in schema and _schema_matches(value, schema["not"], root, path):
        raise ValueError(f"{path} matches a prohibited treatment schema shape")
    if "if" in schema:
        branch = schema.get("then") if _schema_matches(value, schema["if"], root, path) else schema.get("else")
        if branch is not None: _validate_schema_instance(value, branch, root, path)
    if "const" in schema and not _same_json_value(value, schema["const"], path):
        raise ValueError(f"{path} does not match its treatment schema constant")
    if "enum" in schema and not any(_same_json_value(value, item, path) for item in schema["enum"]):
        raise ValueError(f"{path} is outside its treatment schema enum")
    if "type" in schema:
        expected = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_json_type_matches(value, item) for item in expected):
            raise ValueError(f"{path} has the wrong treatment schema type")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0): raise ValueError(f"{path} is shorter than allowed")
        if "pattern" in schema and re.search(schema["pattern"], value) is None: raise ValueError(f"{path} does not match its pattern")
        if schema.get("format") == "date-time": _timestamp(value, path)
    if isinstance(value, int) and not isinstance(value, bool) and "minimum" in schema and value < schema["minimum"]:
        raise ValueError(f"{path} is below its minimum")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0): raise ValueError(f"{path} has too few items")
        if schema.get("uniqueItems") and len({canonical_bytes(item) for item in value}) != len(value):
            raise ValueError(f"{path} must contain unique items")
        if isinstance(schema.get("items"), dict):
            for index, item in enumerate(value): _validate_schema_instance(item, schema["items"], root, f"{path}[{index}]")
    if isinstance(value, dict):
        missing = set(schema.get("required", [])) - set(value)
        if missing: raise ValueError(f"{path} is missing required treatment schema fields")
        properties = schema.get("properties", {})
        for index, (key, item) in enumerate(value.items()):
            if key in properties:
                _validate_schema_instance(item, properties[key], root, f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                raise ValueError(f"{path} contains an undeclared treatment schema field")
            elif isinstance(schema.get("additionalProperties"), dict):
                _validate_schema_instance(item, schema["additionalProperties"], root, f"{path}.<field:{index}>")


def _same_json_value(actual: object, expected: object, label: str) -> bool:
    try:
        return canonical_bytes(actual) == canonical_bytes(expected)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be canonical JSON") from exc


def _contains_ip_address(value: str) -> bool:
    for candidate in IP_CANDIDATE_RE.findall(value):
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            continue
        return True
    return False


def _validate_retained_strings(value: object, label: str = "treatment bundle") -> None:
    if isinstance(value, str):
        forbidden = (
            any(ord(char) < 32 for char in value)
            or (EVIDENCE_REF_RE.fullmatch(value) is None and ABSOLUTE_PATH_RE.search(value))
            or TRAVERSAL_RE.search(value)
            or REMOTE_RE.search(value)
            or CREDENTIAL_RE.search(value)
            or UNLABELED_CREDENTIAL_RE.search(value)
            or PII_RE.search(value)
            or HOSTNAME_RE.search(value)
            or INTERNAL_HOSTNAME_RE.search(value)
            or _contains_ip_address(value)
        )
        if forbidden:
            raise ValueError(f"{label} retains forbidden private or credential-bearing text")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_retained_strings(item, f"{label}[{index}]")
    elif isinstance(value, dict):
        for index, (key, item) in enumerate(value.items()):
            _validate_retained_strings(key, f"{label} object key {index}")
            _validate_retained_strings(item, f"{label} object value {index}")


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


def _validate_tool_vector(value: object, label: str) -> dict:
    vector = _closed(value, {"skills", "mcp_servers", "tools"}, label)
    for field in ("skills", "mcp_servers", "tools"):
        _identifiers(vector[field], f"{label} {field}")
    return vector


def _validate_trace_structures(trace: dict) -> None:
    sandbox = _closed(trace["sandbox"], {"mode", "network_access", "writable_roots_digest"}, "sandbox")
    if sandbox["mode"] not in {"read_only", "workspace_write", "danger_full_access"} or not isinstance(sandbox["network_access"], bool):
        raise ValueError("sandbox values are invalid")
    _digest(sandbox["writable_roots_digest"], "sandbox writable roots")
    approvals = _closed(trace["approvals"], {"policy", "granted_action_ids"}, "approvals")
    if approvals["policy"] not in {"never", "on_request", "on_failure", "untrusted"}:
        raise ValueError("approval policy is invalid")
    _identifiers(approvals["granted_action_ids"], "approval action IDs")
    _text(trace["mutation_class"], "mutation class")
    _validate_tool_vector(trace["expected_skills_mcp_tools"], "expected skills MCP tools")
    _validate_tool_vector(trace["loaded_skills_mcp_tools"], "loaded skills MCP tools")
    parent = _closed(trace["parent_configuration"], {"parent_execution_trace_id", "configuration_hash"}, "parent configuration")
    _digest(parent["parent_execution_trace_id"], "parent execution trace ID", nullable=True)
    _digest(parent["configuration_hash"], "parent configuration hash")
    overrides = _closed(trace["controlled_overrides"], {"model", "effort", "configuration_hash"}, "controlled overrides")
    _text(overrides["model"], "override model"); _text(overrides["effort"], "override effort")
    _digest(overrides["configuration_hash"], "override configuration hash")
    canary = _closed(trace["delivery_canary"], {"status", "evidence_digest"}, "delivery canary")
    if canary["status"] not in {"passed", "failed", "not_run"}:
        raise ValueError("delivery canary status is invalid")
    if canary["status"] == "not_run":
        if canary["evidence_digest"] is not None: raise ValueError("unrun delivery canary evidence must be null")
    else: _digest(canary["evidence_digest"], "delivery canary evidence")
    context = _closed(trace["context"], {"threadId", "turnId"}, "trace association context")
    _correlation_id(context["threadId"], "trace threadId", "thread")
    _correlation_id(context["turnId"], "trace turnId", "turn")
    graph = _closed(trace["parent_child_graph"], {
        "root_execution_trace_id", "parent_execution_trace_id", "child_execution_trace_ids",
    }, "parent-child graph")
    _digest(graph["root_execution_trace_id"], "root execution trace ID")
    _digest(graph["parent_execution_trace_id"], "graph parent trace ID", nullable=True)
    children = _strings(graph["child_execution_trace_ids"], "child execution trace IDs")
    for child in children: _digest(child, "child execution trace ID")
    tokens = _closed(trace["raw_token_vector"], {
        "input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens",
    }, "raw token vector")
    for field in tokens:
        _integer(tokens[field], f"raw token {field}", nullable=True)
    counts = _closed(trace["request_turn_count"], {"requests", "turns"}, "request-turn count")
    _integer(counts["requests"], "request count", nullable=True); _integer(counts["turns"], "turn count", nullable=True)
    _integer(trace["wall_time_ms"], "wall time", nullable=True); _integer(trace["retries"], "retry count", nullable=True)
    compaction = _closed(trace["compaction"], {"occurred", "count"}, "compaction")
    if not isinstance(compaction["occurred"], bool): raise ValueError("compaction occurred must be boolean")
    _integer(compaction["count"], "compaction count")
    if compaction["occurred"] != (compaction["count"] > 0): raise ValueError("compaction count and occurrence disagree")
    validation = _closed(trace["validation"], {"status", "evidence_digest"}, "validation")
    if validation["status"] not in {"completed", "failed", "not_run"}: raise ValueError("validation status is invalid")
    if validation["status"] == "not_run":
        if validation["evidence_digest"] is not None: raise ValueError("unrun validation evidence must be null")
    else: _digest(validation["evidence_digest"], "validation evidence")
    cancellation = _closed(trace["cancellation"], {"state", "reason"}, "cancellation")
    if cancellation["state"] not in {"not_requested", "requested", "completed"}: raise ValueError("cancellation state is invalid")
    _text(cancellation["reason"], "cancellation reason", nullable=True)
    if cancellation["state"] == "not_requested" and cancellation["reason"] is not None: raise ValueError("uncancelled work cannot carry a cancellation reason")
    if cancellation["state"] != "not_requested" and cancellation["reason"] not in CANCELLATION_REASON_CODES:
        raise ValueError("cancellation reason must use an enumerated code")
    failed = _closed(trace["failed_abandoned_work"], {"failed_count", "abandoned_count"}, "failed-abandoned work")
    _integer(failed["failed_count"], "failed-work count"); _integer(failed["abandoned_count"], "abandoned-work count")
    if trace["terminal_state"] not in {"completed", "failed", "cancelled", "abandoned"}: raise ValueError("terminal state is invalid")
    outcome = _closed(trace["outcome"], {"status", "evidence_digest"}, "outcome")
    if outcome["status"] not in {"completed", "failed", "cancelled", "abandoned"}: raise ValueError("outcome status is invalid")
    _digest(outcome["evidence_digest"], "outcome evidence")
    if outcome["status"] != trace["terminal_state"]: raise ValueError("terminal state and outcome status disagree")
    if trace["acceptance"] is not None: raise ValueError("unavailable terminal acceptance must be null")
    if trace["terminal_state"] == "completed":
        if cancellation["state"] != "not_requested" or failed["failed_count"] or failed["abandoned_count"]:
            raise ValueError("completed work contradicts cancellation or failed-work counters")
    elif trace["terminal_state"] == "failed":
        if cancellation["state"] != "not_requested" or failed["failed_count"] < 1:
            raise ValueError("failed work requires a failed count and no completed cancellation")
    elif trace["terminal_state"] == "abandoned":
        if cancellation["state"] != "not_requested" or failed["abandoned_count"] < 1:
            raise ValueError("abandoned work requires an abandoned count and no completed cancellation")
    elif cancellation["state"] != "completed":
        raise ValueError("cancelled work requires completed cancellation evidence")


def _validate_failure(value: object) -> dict:
    failure = _closed(value, {
        "failure_code", "affected_field", "expected_evidence_ref",
        "observed_evidence_ref", "resulting_disposition",
    }, "treatment failure")
    if failure["failure_code"] not in FAILURE_DISPOSITIONS:
        raise ValueError("treatment failure code is invalid")
    if failure["affected_field"] != "treatment.evidence": raise ValueError("treatment failure affected field is invalid")
    if failure["expected_evidence_ref"] is not None or failure["observed_evidence_ref"] is not None:
        raise ValueError("normalized treatment failure evidence references must be null")
    if failure["resulting_disposition"] != FAILURE_DISPOSITIONS[failure["failure_code"]]:
        raise ValueError("structured treatment failure disposition is invalid")
    return failure


def _validate_observations(trace: dict, profile: list[dict]) -> dict[str, dict]:
    values = trace["observations"]
    if not isinstance(values, list): raise ValueError("trace observations must be an array")
    entries = {item["field_path"]: item for item in profile if item["client_identity_id"] == trace["client_identity_id"] and item["surface"] == trace["surface"]}
    observed: dict[str, dict] = {}
    for value in values:
        row = _closed(value, {"field_path", "observation_state", "value", "evidence_ref", "captured_at"}, "observation value")
        field = _text(row["field_path"], "observation field path")
        if field in observed: raise ValueError("duplicate observation field path")
        if field not in entries: raise ValueError("observation field is not profiled for the trace surface")
        state = row["observation_state"]
        if state not in entries[field]["observation_state_rules"]["allowed_states"]: raise ValueError("observation state is not allowed by its profile")
        if _contains_unknown(row["value"]): raise ValueError("literal unknown cannot replace a typed observation value")
        if state == "observed_value" and row["value"] is None: raise ValueError("observed value cannot be null")
        if state != "observed_value" and row["value"] is not None: raise ValueError("null-only observation state cannot carry a value")
        present = state in {"observed_value", "explicit_null"}
        if present:
            _evidence_ref(row["evidence_ref"], "observation evidence reference"); _timestamp(row["captured_at"], "observation capture timestamp")
        else:
            _evidence_ref(row["evidence_ref"], "observation evidence reference", nullable=True); _timestamp(row["captured_at"], "observation capture timestamp", nullable=True)
        if state == "undocumented" and (row["evidence_ref"] is not None or row["captured_at"] is not None): raise ValueError("undocumented observation cannot claim evidence or capture time")
        if field in {"discovery.models", "discovery.efforts", "discovery.capabilities"} and state == "observed_value": _strings(row["value"], f"{field} observation")
        observed[field] = row
    if set(observed) != set(entries): raise ValueError("trace observations do not cover the surface profile")
    return observed


def _validate_proof(value: object, trace: dict, profile: list[dict]) -> dict | None:
    if value is None: return None
    proof = _closed(value, {
        "proof_id", "profile_entry_key", "named_agent", "model", "effort", "candidate_route_id",
        "agent_contract_id", "instruction_hash", "configuration_hash", "client_identity_id",
        "controlled_overrides", "launch_id", "consumption_evidence_digest", "reroute_monitoring_complete",
    }, "configured-route proof")
    key = _closed(proof["profile_entry_key"], {"client_identity_id", "surface", "field_path"}, "configured-route profile key")
    for field in ("client_identity_id",): _digest(key[field], f"profile key {field}")
    if key["surface"] not in SURFACES: raise ValueError("configured-route profile surface is invalid")
    _text(key["field_path"], "configured-route profile field")
    profile_entry(profile, key["client_identity_id"], key["surface"], key["field_path"])
    for field in ("named_agent", "model", "effort", "candidate_route_id", "agent_contract_id"):
        _text(proof[field], f"configured proof {field}")
    _correlation_id(proof["launch_id"], "configured proof launch ID", "launch")
    for field in ("proof_id", "instruction_hash", "configuration_hash", "client_identity_id", "consumption_evidence_digest"): _digest(proof[field], f"configured proof {field}")
    overrides = _closed(proof["controlled_overrides"], {"model", "effort", "configuration_hash"}, "configured proof overrides")
    _text(overrides["model"], "configured proof override model"); _text(overrides["effort"], "configured proof override effort")
    _digest(overrides["configuration_hash"], "configured proof override configuration hash")
    if not isinstance(proof["reroute_monitoring_complete"], bool): raise ValueError("configured proof reroute completeness must be boolean")
    if proof["proof_id"] != content_id(proof, "proof_id"): raise ValueError("configured-route proof ID is not content addressed")
    return proof


def _proof_failure_codes(proof: dict | None, trace: dict, profile: list[dict]) -> list[str]:
    if proof is None:
        return []
    codes: list[str] = []
    objective = trace["objective_binding"]
    key = proof["profile_entry_key"]
    canonical_key = {"client_identity_id": trace["client_identity_id"], "surface": trace["surface"], "field_path": "assignment.configuration_hash"}
    matched = profile_entry(profile, key["client_identity_id"], key["surface"], key["field_path"])
    if key != canonical_key or matched["classification"] != "derived_from_controlled_configuration" or matched["permitted_claims"] != ["requested_assignment"]:
        codes.append("configuration_mismatch")
    if proof["named_agent"] != trace["named_agent"] or proof["agent_contract_id"] != objective["agent_contract_id"]: codes.append("agent_mismatch")
    if proof["model"] != trace["requested_model"]: codes.append("model_mismatch")
    if proof["effort"] != trace["requested_effort"]: codes.append("effort_mismatch")
    if proof["candidate_route_id"] != objective["candidate_route_id"]: codes.append("configuration_mismatch")
    if proof["instruction_hash"] != trace["instruction_hash"] or proof["configuration_hash"] != trace["configuration_hash"]: codes.append("configuration_mismatch")
    if proof["client_identity_id"] != trace["client_identity_id"]: codes.append("client_or_override_mismatch")
    expected_overrides = trace["controlled_overrides"]
    if any(proof["controlled_overrides"][field] != expected_overrides[field] for field in ("model", "effort")): codes.append("client_or_override_mismatch")
    hashes = {trace["configuration_hash"], expected_overrides["configuration_hash"], proof["configuration_hash"], proof["controlled_overrides"]["configuration_hash"]}
    if len(hashes) != 1: codes.append("configuration_mismatch")
    if not proof["reroute_monitoring_complete"]: codes.append("effective_treatment_unknown")
    return list(dict.fromkeys(codes))


def _validate_event(value: object) -> dict:
    event = _closed(value, {"event_id", "surface", "threadId", "turnId", "fromModel", "toModel", "reason", "evidence_digest"}, "service reroute event")
    _digest(event["event_id"], "reroute event ID"); _digest(event["evidence_digest"], "reroute event evidence")
    if event["surface"] not in SURFACES: raise ValueError("reroute event surface is invalid")
    _correlation_id(event["threadId"], "reroute threadId", "thread")
    _correlation_id(event["turnId"], "reroute turnId", "turn")
    for field in ("fromModel", "toModel", "reason"): _text(event[field], f"reroute {field}")
    if event["reason"] not in REROUTE_REASON_CODES: raise ValueError("reroute reason must use an enumerated code")
    if event["event_id"] != content_id(event, "event_id"): raise ValueError("reroute event ID is not content addressed")
    return event


def _validate_assessment(value: object) -> dict:
    assessment = _closed(value, {
        "event_id", "destination_candidate_route_id", "destination_agent_contract_id",
        "destination_named_agent", "assessment", "prequalification_evidence_id",
    }, "reroute destination assessment")
    _digest(assessment["event_id"], "assessment event ID")
    for field in ("destination_candidate_route_id", "destination_agent_contract_id", "destination_named_agent"):
        _text(assessment[field], f"assessment {field}", nullable=True)
    if assessment["assessment"] not in {"prequalified_same_agent", "not_prequalified", "unknown", "ambiguous", "different_agent"}:
        raise ValueError("reroute destination assessment is invalid")
    _digest(assessment["prequalification_evidence_id"], "prequalification evidence ID", nullable=True)
    return assessment


def _reroute_disposition(
    trace: dict, events: list[dict], assessments: list[dict], qualification: dict[str, dict],
    trusted: dict[str, dict], canonical_routes: dict[str, dict[str, object]],
    *, synthetic_replay: bool = False,
) -> tuple[str, list[str]]:
    if not events:
        if assessments: return "hard_fail", ["orphan_reroute_destination_assessment"]
        return "", []
    association = (trace["surface"], trace["context"]["threadId"], trace["context"]["turnId"])
    if any((event["surface"], event["threadId"], event["turnId"]) != association for event in events):
        return "hard_fail", ["reroute_association_mismatch"]
    if len({(event["surface"], event["threadId"], event["turnId"]) for event in events}) != len(events):
        return "hard_fail", ["ambiguous_reroute_association"]
    by_event: dict[str, list[dict]] = {}
    for assessment in assessments: by_event.setdefault(assessment["event_id"], []).append(assessment)
    for event in events:
        if event["fromModel"] != trace["requested_model"]: return "hard_fail", ["reroute_source_model_mismatch"]
        matches = by_event.get(event["event_id"], [])
        if len(matches) != 1: return "hard_fail", ["reroute_destination_missing" if not matches else "reroute_destination_ambiguous"]
        item = matches[0]; evidence = qualification.get(item["prequalification_evidence_id"])
        if item["assessment"] != "prequalified_same_agent" or evidence is None: return "hard_fail", ["reroute_destination_unapproved"]
        canonical = canonical_routes.get(item["destination_candidate_route_id"])
        if canonical is None: return "hard_fail", ["reroute_destination_unidentifiable"]
        if item["destination_named_agent"] != canonical["named_agent"]: return "hard_fail", ["reroute_destination_different_agent"]
        if item["destination_agent_contract_id"] != canonical["agent_contract_id"]: return "hard_fail", ["reroute_destination_manifest_mismatch"]
        if event["toModel"] != canonical["model"]: return "hard_fail", ["reroute_destination_model_mismatch"]
        expected = (item["destination_candidate_route_id"], item["destination_agent_contract_id"], item["destination_named_agent"])
        actual = (evidence["destination_candidate_route_id"], evidence["destination_agent_contract_id"], evidence["destination_named_agent"])
        if expected != actual or item["destination_named_agent"] != trace["named_agent"]: return "hard_fail", ["reroute_destination_mismatch"]
        synthetic_admitted = (
            synthetic_replay and evidence["authority_kind"] == "synthetic_fixture"
            and evidence["owner_spec_id"] == "G56R-002"
        )
        if not synthetic_admitted:
            if evidence["authority_kind"] != "owned_external" or evidence["owner_spec_id"] == "G56R-002":
                return "hard_fail", ["reroute_destination_non_authoritative"]
            admitted = trusted.get(evidence["qualification_evidence_id"])
            if admitted is None or canonical_bytes(admitted) != canonical_bytes(evidence):
                return "hard_fail", ["reroute_destination_untrusted"]
        if trace["supported_effective_model"] != event["toModel"] or trace["supported_effective_effort"] is not None:
            return "hard_fail", ["reroute_effective_destination_mismatch"]
    if set(by_event) != {event["event_id"] for event in events}: return "hard_fail", ["orphan_reroute_destination_assessment"]
    return "non_scorable_rerouted", ["service_reroute_requested_route_non_scorable"]


TRACE_KEYS = {
    "objective_binding", "controlled_environment_id", "client_identity_id", "surface",
    "repository_revision", "repository_tree_digest", "work_item_kind", "work_item_id",
    "named_agent", "assigned_route_id", "requested_model", "requested_effort",
    "supported_effective_model", "supported_effective_effort", "configured_route_proof",
    "service_reroute_events", "reroute_destination_assessments", "instruction_hash",
    "configuration_hash", "sandbox", "approvals", "mutation_class",
    "expected_skills_mcp_tools", "loaded_skills_mcp_tools", "parent_configuration",
    "controlled_overrides", "delivery_canary", "treatment_failures", "context",
    "parent_child_graph", "raw_token_vector", "request_turn_count", "wall_time_ms",
    "retries", "compaction", "validation", "cancellation", "failed_abandoned_work",
    "terminal_state", "outcome", "acceptance", "observations", "treatment_disposition",
    "disposition_reasons",
}


def _validate_trace(trace: object, profile: list[dict], environments: dict[str, dict],
                    policies: dict[str, dict], resolutions: dict[str, dict],
                    qualification: dict[str, dict], trusted: dict[str, dict],
                    canonical_routes: dict[str, dict[str, object]],
                    *, synthetic_replay: bool = False) -> dict:
    row = _closed(trace, TRACE_KEYS, "treatment trace")
    objective = _closed(row["objective_binding"], set(OBJECTIVE_ID_FIELDS), "six-ID objective binding")
    for field in ("candidate_route_id", "agent_contract_id"): _text(objective[field], f"objective {field}")
    for field in ("runtime_capability_snapshot_id", "route_resolution_id", "experiment_policy_id", "execution_trace_id"):
        _digest(objective[field], f"objective {field}")
    env_id = _digest(row["controlled_environment_id"], "trace controlled environment ID")
    if env_id not in environments: raise ValueError("trace has no controlled environment owner")
    env = environments[env_id]
    resolution_id = objective["route_resolution_id"]
    if resolution_id not in resolutions: raise ValueError("trace has no route resolution owner")
    resolution = resolutions[resolution_id]
    referenced_route_ids = [
        resolution["preferred_route_id"], *resolution["attempted_route_ids"],
    ]
    if resolution["supported_effective_route_id"] is not None:
        referenced_route_ids.append(resolution["supported_effective_route_id"])
    if any(route_id not in canonical_routes for route_id in referenced_route_ids):
        raise ValueError("route resolution references a route outside the canonical candidate manifest")
    if any(
        canonical_routes[route_id]["agent_contract_id"] != objective["agent_contract_id"]
        for route_id in referenced_route_ids
    ):
        raise ValueError("route resolution references a route owned by a different agent contract")
    policy_id = objective["experiment_policy_id"]
    if policy_id not in policies: raise ValueError("trace has no experiment policy owner")
    policy = policies[policy_id]
    _digest(row["client_identity_id"], "trace client identity"); _digest(row["repository_tree_digest"], "trace repository tree")
    if row["surface"] not in SURFACES or row["work_item_kind"] not in {"task", "fixture", "objective"}: raise ValueError("trace surface or work item kind is invalid")
    if not isinstance(row["repository_revision"], str) or REVISION_RE.fullmatch(row["repository_revision"]) is None: raise ValueError("trace repository revision is invalid")
    _identifier(row["work_item_id"], "trace work_item_id")
    for field in ("named_agent", "assigned_route_id", "requested_model", "requested_effort"):
        _text(row[field], f"trace {field}")
    _text(row["supported_effective_model"], "supported effective model", nullable=True); _text(row["supported_effective_effort"], "supported effective effort", nullable=True)
    _digest(row["instruction_hash"], "trace instruction hash"); _digest(row["configuration_hash"], "trace configuration hash")
    env_equalities = {
        "client_identity_id": row["client_identity_id"], "surface": row["surface"],
        "runtime_capability_snapshot_id": objective["runtime_capability_snapshot_id"],
        "repository_revision": row["repository_revision"], "repository_tree_digest": row["repository_tree_digest"],
        "candidate_route_id": objective["candidate_route_id"], "work_item_kind": row["work_item_kind"],
        "work_item_id": row["work_item_id"],
    }
    if any(env[field] != expected for field, expected in env_equalities.items()): raise ValueError("trace controlled environment binding is inconsistent")
    if objective["candidate_route_id"] != row["assigned_route_id"] or resolution["assigned_route_id"] != row["assigned_route_id"]:
        raise ValueError("assigned route does not join objective, environment, and resolution")
    canonical_route = canonical_routes.get(objective["candidate_route_id"])
    if canonical_route is None or {key: canonical_route[key] for key in ("agent_contract_id", "named_agent", "model")} != {
        "agent_contract_id": objective["agent_contract_id"], "named_agent": row["named_agent"], "model": row["requested_model"],
    }:
        raise ValueError("assigned route does not bind the canonical candidate manifest")
    canonical_effort = canonical_route["effort"]
    if canonical_effort is not None and row["requested_effort"] != canonical_effort:
        raise ValueError("requested effort does not bind the canonical candidate manifest")
    if resolution["runtime_capability_snapshot_id"] != objective["runtime_capability_snapshot_id"]: raise ValueError("route resolution snapshot does not join the objective")
    policy_equalities = {
        "candidate_route_id": objective["candidate_route_id"], "work_item_kind": row["work_item_kind"],
        "work_item_id": row["work_item_id"], "mutation_class": row["mutation_class"],
    }
    if any(policy[field] != expected for field, expected in policy_equalities.items()):
        raise ValueError("trace experiment policy binding is inconsistent")
    _validate_trace_structures(row)
    if objective["execution_trace_id"] != execution_trace_identity(row):
        raise ValueError("execution trace ID is not deterministically derived")
    observations = _validate_observations(row, profile)
    proof = _validate_proof(row["configured_route_proof"], row, profile)
    failures = row["treatment_failures"]
    if not isinstance(failures, list): raise ValueError("treatment failures must be an array")
    validated_failures = [_validate_failure(item) for item in failures]
    if len({item["failure_code"] for item in validated_failures}) != len(validated_failures): raise ValueError("duplicate structured treatment failure code")
    derived_codes = _proof_failure_codes(proof, row, profile)
    discovery_requirements = {
        "discovery.models": ([row["requested_model"]], "model_mismatch"),
        "discovery.efforts": ([row["requested_effort"]], "effort_mismatch"),
        "discovery.capabilities": (canonical_route["required_capabilities"], "skills_mcp_tools_mismatch"),
    }
    for field, (required_values, failure_code) in discovery_requirements.items():
        observed = observations.get(field)
        if (
            observed is None or observed["observation_state"] != "observed_value"
            or any(value not in observed["value"] for value in required_values)
        ):
            derived_codes.append(failure_code)
    events = row["service_reroute_events"]; assessments = row["reroute_destination_assessments"]
    if not isinstance(events, list) or not isinstance(assessments, list): raise ValueError("reroute records must be arrays")
    events = [_validate_event(item) for item in events]; assessments = [_validate_assessment(item) for item in assessments]
    if len({item["event_id"] for item in events}) != len(events): raise ValueError("duplicate reroute event ID")
    supported_route_id = resolution["supported_effective_route_id"]
    supported_route = canonical_routes.get(supported_route_id) if supported_route_id is not None else None
    if events and supported_route_id is not None:
        raise ValueError("service reroute cannot claim a resolver-supported effective route")
    if not events and supported_route is not None:
        if supported_route_id != resolution["assigned_route_id"]:
            raise ValueError("supported effective route must select the assigned route without a service reroute")
        if row["supported_effective_model"] != supported_route["model"]:
            raise ValueError("supported effective route does not bind its canonical effective model")
        if supported_route["effort"] is not None and row["supported_effective_effort"] != supported_route["effort"]:
            raise ValueError("supported effective route does not bind its canonical effective effort")
    if row["supported_effective_effort"] is not None and (
        supported_route is None or supported_route["effort"] is None
        or row["supported_effective_effort"] != supported_route["effort"]
    ):
        derived_codes.append("effort_mismatch")
    if row["supported_effective_model"] is not None and (
        events and (len(events) != 1 or events[0]["toModel"] != row["supported_effective_model"])
        or not events and supported_route is None
    ):
        derived_codes.append("model_mismatch")
    if events and row["supported_effective_model"] is None: derived_codes.append("model_mismatch")
    reroute_observation = observations.get("reroute.events")
    if reroute_observation is not None and reroute_observation["observation_state"] == "observed_value":
        if not _same_json_value(reroute_observation["value"], events, "reroute observation"): derived_codes.append("reroute_ambiguous")
    elif events: derived_codes.append("reroute_unidentifiable")
    bindings = {
        "assignment.named_agent": row["named_agent"], "assignment.model": row["requested_model"],
        "assignment.effort": row["requested_effort"], "assignment.supported_effective_model": row["supported_effective_model"],
        "assignment.supported_effective_effort": row["supported_effective_effort"], "assignment.candidate_route_id": objective["candidate_route_id"],
        "assignment.agent_contract_id": objective["agent_contract_id"], "assignment.instruction_hash": row["instruction_hash"],
        "assignment.configuration_hash": row["configuration_hash"], "route.preferred_route_id": resolution["preferred_route_id"],
        "route.attempted_route_ids": resolution["attempted_route_ids"], "route.assigned_route_id": resolution["assigned_route_id"],
        "route.supported_effective_route_id": resolution["supported_effective_route_id"], "route.fallback_index": resolution["fallback_index"],
        "route.fallback_reason": resolution["fallback_reason"], "route.runtime_capability_snapshot_id": resolution["runtime_capability_snapshot_id"],
        "route.resolved_at": resolution["resolved_at"], "reroute.events": events,
        "treatment.sandbox": row["sandbox"], "treatment.approvals": row["approvals"],
        "treatment.mutation_class": row["mutation_class"], "treatment.expected_skills_mcp_tools": row["expected_skills_mcp_tools"],
        "treatment.loaded_skills_mcp_tools": row["loaded_skills_mcp_tools"], "treatment.parent_configuration": row["parent_configuration"],
        "treatment.controlled_overrides": row["controlled_overrides"], "treatment.delivery_canary": row["delivery_canary"],
        "treatment.failures": row["treatment_failures"],
        "parent.context": row["context"], "parent.graph": row["parent_child_graph"],
        "resources.raw_token_vector": row["raw_token_vector"], "resources.request_turn_count": row["request_turn_count"],
        "resources.wall_time_ms": row["wall_time_ms"], "lifecycle.retries": row["retries"], "lifecycle.compaction": row["compaction"],
        "lifecycle.validation": row["validation"], "lifecycle.cancellation": row["cancellation"],
        "lifecycle.failed_abandoned_work": row["failed_abandoned_work"], "terminal.state": row["terminal_state"],
        "terminal.outcome": row["outcome"], "terminal.acceptance": row["acceptance"],
    }
    observation_failure_codes = {
        "assignment.named_agent": "agent_mismatch",
        "assignment.model": "model_mismatch", "assignment.effort": "effort_mismatch",
        "assignment.supported_effective_model": "model_mismatch", "assignment.supported_effective_effort": "effort_mismatch",
        "assignment.agent_contract_id": "agent_mismatch", "treatment.sandbox": "sandbox_approvals_mismatch",
        "treatment.approvals": "sandbox_approvals_mismatch", "treatment.mutation_class": "mutation_class_mismatch",
        "treatment.expected_skills_mcp_tools": "skills_mcp_tools_mismatch", "treatment.loaded_skills_mcp_tools": "skills_mcp_tools_mismatch",
        "treatment.parent_configuration": "parent_configuration_mismatch", "parent.context": "parent_configuration_mismatch",
        "parent.graph": "parent_configuration_mismatch", "treatment.controlled_overrides": "client_or_override_mismatch",
        "treatment.delivery_canary": "delivery_canary_failure",
    }
    configuration_fields = {
        "assignment.candidate_route_id", "assignment.instruction_hash", "assignment.configuration_hash",
        "route.preferred_route_id", "route.attempted_route_ids", "route.assigned_route_id",
        "route.supported_effective_route_id", "route.fallback_index", "route.fallback_reason",
        "route.runtime_capability_snapshot_id", "route.resolved_at",
    }
    for field, expected in bindings.items():
        entry = profile_entry(profile, row["client_identity_id"], row["surface"], field)
        claim_present = _top_level_claim_present(field, expected)
        if entry["classification"] in {"unavailable", "not_applicable", "undocumented"} and claim_present:
            raise ValueError(f"{field} cannot retain a top-level claim under its telemetry classification")
        observed = observations.get(field)
        if observed is None:
            if claim_present:
                raise ValueError(f"{field} cannot retain a top-level claim without applicable telemetry authority")
            continue
        if entry["classification"] == "conditional":
            if claim_present and observed["observation_state"] != "observed_value":
                raise ValueError(f"{field} condition occurred without an observed value")
            if not claim_present and observed["observation_state"] == "observed_value":
                raise ValueError(f"{field} claims an observation when its condition did not occur")
        mismatch = observed["observation_state"] == "observed_value" and not _same_json_value(observed["value"], expected, f"{field} observation")
        mismatch |= observed["observation_state"] == "explicit_null" and expected is not None
        mismatch |= observed["observation_state"] == "missing" and expected is not None and entry["classification"] not in {"conditional", "undocumented"}
        if mismatch: derived_codes.append("configuration_mismatch" if field in configuration_fields else observation_failure_codes.get(field, "effective_treatment_unknown"))
    if row["expected_skills_mcp_tools"] != row["loaded_skills_mcp_tools"]: derived_codes.append("skills_mcp_tools_mismatch")
    if row["parent_configuration"]["parent_execution_trace_id"] != row["parent_child_graph"]["parent_execution_trace_id"]: derived_codes.append("parent_configuration_mismatch")
    if row["controlled_overrides"]["model"] != row["requested_model"] or row["controlled_overrides"]["effort"] != row["requested_effort"]: derived_codes.append("client_or_override_mismatch")
    proof_configuration_hash = proof["configuration_hash"] if proof is not None else row["configuration_hash"]
    if len({row["configuration_hash"], row["controlled_overrides"]["configuration_hash"], proof_configuration_hash}) != 1: derived_codes.append("configuration_mismatch")
    if row["delivery_canary"]["status"] == "failed": derived_codes.append("delivery_canary_failure")
    reroute_disposition, reasons = _reroute_disposition(
        row, events, assessments, qualification, trusted, canonical_routes,
        synthetic_replay=synthetic_replay,
    )
    if events and resolution["supported_effective_route_id"] not in {None, resolution["assigned_route_id"]}: raise ValueError("service reroute must not rewrite resolver-selected fields")
    reason_codes = {
        "reroute_association_mismatch": "reroute_unidentifiable", "ambiguous_reroute_association": "reroute_ambiguous",
        "reroute_destination_missing": "reroute_unidentifiable", "reroute_destination_ambiguous": "reroute_ambiguous",
        "reroute_destination_unapproved": "reroute_unapproved", "reroute_destination_mismatch": "reroute_different_agent",
        "reroute_destination_unidentifiable": "reroute_unidentifiable", "reroute_destination_manifest_mismatch": "reroute_unidentifiable",
        "reroute_destination_different_agent": "reroute_different_agent", "reroute_destination_model_mismatch": "model_mismatch",
        "reroute_destination_non_authoritative": "reroute_unapproved", "reroute_destination_untrusted": "reroute_unapproved",
        "reroute_effective_destination_mismatch": "model_mismatch", "reroute_source_model_mismatch": "model_mismatch",
        "orphan_reroute_destination_assessment": "reroute_ambiguous",
    }
    if reroute_disposition == "hard_fail": derived_codes.extend(reason_codes[item] for item in reasons)
    effective_observed = all(
        path in observations and row[field] is not None and observations[path]["observation_state"] == "observed_value"
        and _same_json_value(observations[path]["value"], row[field], f"{path} observation")
        for field, path in (("supported_effective_model", "assignment.supported_effective_model"), ("supported_effective_effort", "assignment.supported_effective_effort"))
    )
    reroute_profile = profile_entry(profile, row["client_identity_id"], row["surface"], "reroute.events")
    monitoring_authoritative = (
        proof is not None and proof["reroute_monitoring_complete"]
        and reroute_profile["classification"] == "stable_native"
        and reroute_profile["completeness_rule"] == "complete_capture"
        and reroute_observation is not None and reroute_observation["observation_state"] == "observed_value"
    )
    proof_valid = proof is not None and not _proof_failure_codes(proof, row, profile) and monitoring_authoritative
    hard_failure_derived = any(FAILURE_DISPOSITIONS.get(code) == "hard_fail" for code in derived_codes)
    if not reroute_disposition and (
        not proof_valid and not effective_observed or canonical_effort is None and not hard_failure_derived
    ):
        derived_codes.append("effective_treatment_unknown")
    derived_codes = list(dict.fromkeys(derived_codes))
    declared_by_code = {item["failure_code"]: item for item in validated_failures}
    unsubstantiated = set(declared_by_code) - set(derived_codes)
    if unsubstantiated: raise ValueError(f"unsubstantiated declared treatment failure: {sorted(unsubstantiated)}")
    normalized_failures = [{
        "failure_code": code, "affected_field": "treatment.evidence", "expected_evidence_ref": None,
        "observed_evidence_ref": None, "resulting_disposition": FAILURE_DISPOSITIONS[code],
    } for code in derived_codes]
    if validated_failures != normalized_failures:
        raise ValueError(
            "declared treatment failures do not match derived treatment failures: "
            f"expected {derived_codes!r}"
        )
    failure_dispositions = {item["resulting_disposition"] for item in normalized_failures}
    if reroute_disposition == "non_scorable_rerouted" and "hard_fail" not in failure_dispositions: expected_disposition, expected_reasons = reroute_disposition, reasons
    elif "hard_fail" in failure_dispositions:
        expected_disposition = "hard_fail"
        expected_reasons = sorted(set(derived_codes) | (set(reasons) if reroute_disposition == "hard_fail" else set()))
    elif "unknown" in failure_dispositions: expected_disposition, expected_reasons = "unknown", sorted(derived_codes)
    elif proof_valid: expected_disposition, expected_reasons = "proven", ["configured_route_proof_and_complete_reroute_monitoring"]
    elif effective_observed: expected_disposition, expected_reasons = "proven", ["profile_supported_effective_treatment"]
    else: expected_disposition, expected_reasons = "unknown", ["effective_treatment_or_reroute_evidence_missing"]
    if row["treatment_disposition"] not in {"proven", "unknown", "non_scorable_rerouted", "hard_fail"}: raise ValueError("declared treatment disposition is invalid")
    declared_reasons = _strings(row["disposition_reasons"], "treatment disposition reasons")
    if any(reason not in DISPOSITION_REASON_CODES for reason in declared_reasons):
        raise ValueError("treatment disposition reasons must use enumerated codes")
    if row["treatment_disposition"] != expected_disposition:
        raise ValueError(
            "declared treatment disposition does not match the derived disposition: "
            f"expected {expected_disposition!r}"
        )
    if declared_reasons != expected_reasons:
        raise ValueError(
            "declared treatment disposition reasons do not match the derived reasons: "
            f"expected {expected_reasons!r}"
        )
    return row


def _validate_trace_graph(traces: list[dict]) -> None:
    by_id = {trace["objective_binding"]["execution_trace_id"]: trace for trace in traces}
    if len(by_id) != len(traces): raise ValueError("duplicate execution trace ID")
    for trace_id, trace in by_id.items():
        graph = trace["parent_child_graph"]; parent = graph["parent_execution_trace_id"]
        if graph["root_execution_trace_id"] not in by_id: raise ValueError("trace graph root has no owner")
        if parent == trace_id or trace_id in graph["child_execution_trace_ids"]: raise ValueError("trace graph cannot contain a self edge")
        if parent is not None and parent not in by_id: raise ValueError("trace graph parent has no owner")
        if any(child not in by_id for child in graph["child_execution_trace_ids"]): raise ValueError("trace graph child has no owner")
        if parent is None and graph["root_execution_trace_id"] != trace_id: raise ValueError("root trace does not own its graph root")
        if parent is not None and trace_id not in by_id[parent]["parent_child_graph"]["child_execution_trace_ids"]:
            raise ValueError("trace graph parent and child edges are not reciprocal")
        if parent is not None and trace["parent_configuration"]["configuration_hash"] != by_id[parent]["configuration_hash"]:
            raise ValueError("parent configuration hash does not bind the referenced parent trace")
        for child in graph["child_execution_trace_ids"]:
            if by_id[child]["parent_child_graph"]["parent_execution_trace_id"] != trace_id:
                raise ValueError("trace graph child and parent edges are not reciprocal")
    for trace_id, trace in by_id.items():
        seen: set[str] = set(); current = trace_id
        while by_id[current]["parent_child_graph"]["parent_execution_trace_id"] is not None:
            if current in seen: raise ValueError("trace graph contains a cycle")
            seen.add(current); current = by_id[current]["parent_child_graph"]["parent_execution_trace_id"]
        if trace["parent_child_graph"]["root_execution_trace_id"] != current:
            raise ValueError("trace graph root does not match its ancestor chain")


def _validate_treatment_bundle(
    bundle: object, *, schema_path: Path, manifest: dict,
    trusted_qualification_evidence: Mapping[str, dict] | None,
    synthetic_replay: bool = False,
) -> dict:
    _validate_resource_bounds(bundle)
    _validate_retained_strings(bundle)
    schema_bytes = _read_bounded_regular_file(schema_path)
    schema = _parse_json_bytes(schema_bytes)
    if not isinstance(schema, dict): raise ValueError("treatment contract must be a JSON Schema object")
    _validate_resource_bounds(schema)
    _validate_schema_instance(bundle, schema, schema)
    value = _closed(copy.deepcopy(bundle), {
        "schema_version", "treatment_contract_digest", "telemetry_profile_id", "telemetry_profile",
        "controlled_environments", "experiment_policy_registry", "qualification_evidence_registry", "route_resolutions",
        "treatment_traces", "fixture_provenance",
    }, "treatment bundle")
    if value["schema_version"] != SCHEMA_VERSION: raise ValueError("unsupported treatment schema version")
    contract_digest = digest(schema_bytes)
    if value["treatment_contract_digest"] != contract_digest: raise ValueError("treatment contract digest does not bind the exact schema bytes")
    current_source_ids = _current_source_ids(manifest)
    canonical_routes = _canonical_routes(manifest)
    profile = _validate_profile(value["telemetry_profile"], current_source_ids)
    trusted = _validate_trusted_qualification(trusted_qualification_evidence)
    expected_profile_id = telemetry_profile_id(value["schema_version"], profile, contract_digest)
    if value["telemetry_profile_id"] != expected_profile_id: raise ValueError("telemetry profile ID does not bind the profile and treatment contract")
    registries = (("controlled_environments", _validate_environment, "controlled_environment_id", "controlled environment"),
                  ("experiment_policy_registry", _validate_experiment_policy, "experiment_policy_id", "experiment policy"),
                  ("qualification_evidence_registry", _validate_qualification, "qualification_evidence_id", "qualification evidence"),
                  ("route_resolutions", _validate_resolution, "route_resolution_id", "route resolution"))
    owners: dict[str, dict[str, dict]] = {}
    for field, validator, identity, label in registries:
        if not isinstance(value[field], list): raise ValueError(f"{field} must be an array")
        rows = [validator(item) for item in value[field]]; keys = [item[identity] for item in rows]
        if len(keys) != len(set(keys)): raise ValueError(f"duplicate {label} owner")
        owners[field] = dict(zip(keys, rows))
    for owner in owners["qualification_evidence_registry"].values():
        canonical = canonical_routes.get(owner["destination_candidate_route_id"])
        if canonical is None or (
            owner["destination_agent_contract_id"] != canonical["agent_contract_id"]
            or owner["destination_named_agent"] != canonical["named_agent"]
        ):
            raise ValueError("qualification evidence destination is not bound to the canonical manifest")
    traces = value["treatment_traces"]
    if not isinstance(traces, list) or not traces: raise ValueError("treatment traces must be a non-empty array")
    profile_clients = {item["client_identity_id"] for item in profile}
    environment_clients = {item["client_identity_id"] for item in owners["controlled_environments"].values()}
    trace_clients = {item["client_identity_id"] for item in traces}
    if profile_clients != environment_clients or profile_clients != trace_clients:
        raise ValueError("schema v1 telemetry profile client must own every environment and trace")
    validated = [_validate_trace(
        item, profile, owners["controlled_environments"], owners["experiment_policy_registry"], owners["route_resolutions"],
        owners["qualification_evidence_registry"], trusted, canonical_routes,
        synthetic_replay=synthetic_replay,
    ) for item in traces]
    referenced_environments = {item["controlled_environment_id"] for item in validated}
    if referenced_environments != set(owners["controlled_environments"]):
        raise ValueError("controlled environment owner registry contains a missing or orphan owner")
    referenced_resolutions = {item["objective_binding"]["route_resolution_id"] for item in validated}
    if referenced_resolutions != set(owners["route_resolutions"]):
        raise ValueError("route resolution owner registry contains a missing or orphan owner")
    referenced_policies = {item["objective_binding"]["experiment_policy_id"] for item in validated}
    if referenced_policies != set(owners["experiment_policy_registry"]):
        raise ValueError("experiment policy owner registry contains a missing or orphan owner")
    referenced_qualifications = {
        assessment["prequalification_evidence_id"]
        for item in validated
        for assessment in item["reroute_destination_assessments"]
        if assessment["prequalification_evidence_id"] is not None
    }
    if referenced_qualifications != set(owners["qualification_evidence_registry"]):
        raise ValueError("qualification evidence owner registry contains a missing or orphan owner")
    _validate_trace_graph(validated)
    provenance = _closed(value["fixture_provenance"], {
        "schema_version", "sanitizer_version", "raw_evidence_digest", "expected_dispositions",
        "network_required", "raw_store_required", "replay_count",
    }, "fixture provenance")
    if provenance["schema_version"] != SCHEMA_VERSION or provenance["network_required"] is not False or provenance["raw_store_required"] is not False or provenance["replay_count"] != 2:
        raise ValueError("fixture provenance violates offline replay bounds")
    _text(provenance["sanitizer_version"], "sanitizer version"); _digest(provenance["raw_evidence_digest"], "raw evidence digest")
    expected_dispositions = [{
        "execution_trace_id": item["objective_binding"]["execution_trace_id"],
        "treatment_disposition": item["treatment_disposition"],
    } for item in validated]
    if provenance["expected_dispositions"] != expected_dispositions:
        raise ValueError(
            f"fixture expected dispositions do not match traces: expected {expected_dispositions!r}"
        )
    return value


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
                raise ValueError(f"{label} contains a duplicate JSON key: {key}")
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
    root = repository_root.resolve()
    target = (root / fixture_path).resolve()
    if not target.is_relative_to(root):
        raise ValueError("fixture path escapes the repository root")
    return target


def _validate_capability_fixture(value: object) -> dict[str, dict]:
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
    return cases


def _validate_replay_capability_semantics(case_id: str, case: dict) -> None:
    sources = {(item["model"], item["effort"]) for item in case["source_tuples"]}
    if not sources or any(not item["source_admitted"] for item in case["source_tuples"]):
        raise ValueError("replay capability source case must contain admitted source tuples")
    entries: dict[str, dict[tuple[str, str], tuple[bool, bool]]] = {}
    for surface, payload in case["surfaces"].items():
        indexed: dict[tuple[str, str], tuple[bool, bool]] = {}
        for item in payload["entries"]:
            key = (item["model"], item["effort"])
            if key in indexed:
                raise ValueError("replay capability source case contains a duplicate surface tuple")
            indexed[key] = (item["available"], item["hidden"])
        entries[surface] = indexed
    if case_id == "partial_surface":
        states = {surface: payload["state"] for surface, payload in case["surfaces"].items()}
        incomplete = any(state in {"partial", "unavailable", "unknown"} for state in states.values())
        unavailable_source = any(
            entries[surface].get(source) != (True, False)
            for source in sources for surface in SURFACES
        )
        if not incomplete or not unavailable_source:
            raise ValueError("partial-surface replay case must prove unavailable discovery on a required surface")
    elif case_id == "surface_disagreement":
        if any(case["surfaces"][surface]["state"] != "complete" for surface in SURFACES):
            raise ValueError("surface-disagreement replay case requires complete compared surfaces")
        if any(source not in entries[surface] for source in sources for surface in SURFACES):
            raise ValueError("surface-disagreement replay case must compare every admitted source tuple")
        disagreement = any(
            len({entries[surface][source] for surface in SURFACES}) > 1
            for source in sources
        )
        if not disagreement:
            raise ValueError("surface-disagreement replay case must prove conflicting surface observations")
    else:
        raise ValueError("unsupported linked replay capability case")


def _validate_replay_trace_semantics(case_class: str, trace: dict) -> None:
    observations = {item["field_path"]: item for item in trace["observations"]}
    events = trace["service_reroute_events"]
    assessments = trace["reroute_destination_assessments"]
    failure_codes = [item["failure_code"] for item in trace["treatment_failures"]]

    def observed(field: str, state: str, value: object) -> bool:
        item = observations[field]
        return item["observation_state"] == state and item["value"] == value

    if trace["terminal_state"] != "completed" or trace["outcome"]["status"] != "completed" or trace["delivery_canary"]["status"] != "passed":
        raise ValueError("replay trace must preserve the predeclared completed canary lifecycle")
    if case_class not in {"approved_same_agent_reroute", "unapproved_unidentifiable_reroute"} and (events or assessments):
        raise ValueError("non-reroute replay class must not contain reroute records")

    if case_class == "success":
        valid = observed("discovery.models", "observed_value", [trace["requested_model"]])
        valid &= observed("assignment.named_agent", "observed_value", trace["named_agent"])
    elif case_class == "explicit_null":
        valid = observed("discovery.models", "explicit_null", None)
    elif case_class == "unavailable":
        valid = trace["acceptance"] is None and observed("terminal.acceptance", "unavailable", None)
    elif case_class == "misdelivery":
        item = observations["assignment.named_agent"]
        valid = item["observation_state"] == "observed_value" and item["value"] != trace["named_agent"]
        valid &= "agent_mismatch" in failure_codes
    elif case_class == "approved_same_agent_reroute":
        valid = len(events) == 1 and len(assessments) == 1
        if valid:
            assessment = assessments[0]
            valid = assessment["event_id"] == events[0]["event_id"]
            valid &= assessment["assessment"] == "prequalified_same_agent"
            valid &= assessment["destination_named_agent"] == trace["named_agent"]
        valid &= failure_codes == []
    elif case_class == "unapproved_unidentifiable_reroute":
        valid = len(events) == 1 and assessments == [] and failure_codes == ["reroute_unidentifiable"]
    elif case_class == "discovery_loss":
        valid = observed("discovery.models", "missing", None)
    elif case_class == "surface_disagreement":
        valid = observed("discovery.models", "observed_value", [trace["requested_model"]])
    else:
        raise ValueError("unsupported replay case class")
    if not valid:
        raise ValueError(f"replay trace does not prove its predeclared {case_class} semantics")


def _normalized_replay_pass(capability_fixture: object, treatment_fixture: object) -> list[dict]:
    capability_cases = _validate_capability_fixture(capability_fixture)
    bundle = _validate_treatment_bundle(
        treatment_fixture, schema_path=SCHEMA_PATH,
        manifest=_read_manifest_snapshot(MANIFEST_PATH),
        trusted_qualification_evidence=None, synthetic_replay=True,
    )
    traces = bundle["treatment_traces"]
    execution_ids = [item["objective_binding"]["execution_trace_id"] for item in traces]
    expected_ids = [item[0] for item in REPLAY_CASES]
    if execution_ids != expected_ids:
        raise ValueError("treatment replay fixture does not use the exact eight-case execution registry")
    by_id = dict(zip(execution_ids, traces))
    normalized = []
    for execution_id, case_class, expected_disposition, expected_reasons, capability_case_id in REPLAY_CASES:
        trace = by_id[execution_id]
        slug = case_class.replace("_", "-")
        if trace["context"] != {"threadId": f"thread-{slug}", "turnId": f"turn-{slug}"}:
            raise ValueError("treatment replay association does not use fixture-local pseudonyms")
        if trace["parent_child_graph"]["root_execution_trace_id"] != execution_id:
            raise ValueError("treatment replay graph does not use its fixture execution pseudonym")
        if trace["treatment_disposition"] != expected_disposition or tuple(trace["disposition_reasons"]) != expected_reasons:
            raise ValueError("treatment replay case does not preserve its predeclared disposition")
        _validate_replay_trace_semantics(case_class, trace)
        if capability_case_id is not None:
            source = capability_cases[capability_case_id]
            if source["expected_validity"] != "valid" or source["expected_decision"] != "excluded":
                raise ValueError("replay capability source case does not preserve its predeclared exclusion")
            _validate_replay_capability_semantics(capability_case_id, source)
        normalized.append({
            "execution_trace_id": execution_id,
            "case_class": case_class,
            "source_capability_case_id": capability_case_id,
            "treatment_disposition": trace["treatment_disposition"],
            "disposition_reasons": trace["disposition_reasons"],
            "treatment_failure_codes": [item["failure_code"] for item in trace["treatment_failures"]],
            "terminal_state": trace["terminal_state"],
            "delivery_canary_status": trace["delivery_canary"]["status"],
        })
    return normalized


def replay_fixture(fixture_path: Path, digest_manifest_path: Path, *, repeat: int = 2,
                   repository_root: Path = ROOT) -> dict:
    if isinstance(repeat, bool) or not isinstance(repeat, int) or repeat != 2:
        raise ValueError("replay repeat must be exactly 2")
    manifest_raw = digest_manifest_path.read_bytes()
    manifest = _unique_json(manifest_raw, "fixture digest manifest")
    if manifest_raw != canonical_fixture_bytes(manifest):
        raise ValueError("fixture digest manifest must use canonical compact UTF-8 JSON plus LF")
    entries = _manifest_entries(manifest)
    targets = {entry["fixture_path"]: _fixture_target(repository_root, entry["fixture_path"]) for entry in entries}
    if fixture_path.resolve() != targets[TREATMENT_FIXTURE_PATH]:
        raise ValueError("replay fixture argument must select the declared treatment fixture")
    raw_fixtures = {path: targets[path].read_bytes() for path in REPLAY_FIXTURE_PATHS}
    for entry in entries:
        if digest(raw_fixtures[entry["fixture_path"]]) != entry["fixture_digest"]:
            raise ValueError(f"fixture digest mismatch before parsing: {entry['fixture_path']}")
    parsed = {
        path: _unique_json(raw_fixtures[path], f"fixture {path}")
        for path in REPLAY_FIXTURE_PATHS
    }
    for path in REPLAY_FIXTURE_PATHS:
        if raw_fixtures[path] != canonical_fixture_bytes(parsed[path]):
            raise ValueError(f"fixture must use canonical compact UTF-8 JSON plus LF: {path}")
    guardrails = {
        "qualification_scope": "synthetic_replay_only",
        "runtime_continuation_authorized": False,
        "canary_promotes_treatment": False,
        "network_accessed": False,
        "raw_store_accessed": False,
    }
    pass_outputs = []
    for _ in range(repeat):
        pass_outputs.append({
            "status": "replayed", "repeat": repeat,
            "fixture_digests": copy.deepcopy(entries),
            "cases": _normalized_replay_pass(parsed[CAPABILITY_FIXTURE_PATH], parsed[TREATMENT_FIXTURE_PATH]),
            "guardrails": copy.deepcopy(guardrails),
        })
    serialized = [canonical_fixture_bytes(item) for item in pass_outputs]
    if serialized[0] != serialized[1]:
        raise ValueError("two-pass replay output is not byte-identical")
    result = pass_outputs[0]
    result["replay_digest"] = digest(serialized[0])
    return result


def _capability_module():
    spec = importlib.util.spec_from_file_location("g56r_002_capability_for_treatment", CAPABILITY_MODULE_PATH)
    if spec is None or spec.loader is None: raise RuntimeError("cannot load capability freeze validator")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def build_treatment_successor(prior_freeze: dict, treatment_bundle: dict, *, published_at: str,
                              manifest_path: Path = MANIFEST_PATH,
                              trusted_qualification_evidence: Mapping[str, dict] | None = None) -> dict:
    manifest = _read_manifest_snapshot(manifest_path)
    validated = _validate_treatment_bundle(
        treatment_bundle, schema_path=SCHEMA_PATH, manifest=manifest,
        trusted_qualification_evidence=trusted_qualification_evidence,
    )
    capability = _capability_module()
    if not isinstance(prior_freeze, dict):
        raise ValueError("prior freeze must be a JSON object")
    try:
        prior_freeze = capability.validate_freeze(copy.deepcopy(prior_freeze), manifest)
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
    )
    if successor["supersedes_candidate_freeze_id"] != prior_id: raise ValueError("treatment successor does not bind the actual prior freeze")
    return successor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate"); validate.add_argument("--fixture", type=Path, required=True)
    replay = sub.add_parser("replay"); replay.add_argument("--fixture", type=Path, required=True)
    replay.add_argument("--digest-manifest", type=Path, required=True)
    replay.add_argument("--repeat", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            bundle = _read_json_file(args.fixture)
            if not isinstance(bundle, dict):
                raise ValueError("treatment fixture must be a JSON object")
            validate_treatment_bundle(bundle)
            print(json.dumps({
                "status": "valid",
                "telemetry_profile_id": bundle["telemetry_profile_id"],
            }, sort_keys=True))
        else:
            result = replay_fixture(args.fixture, args.digest_manifest, repeat=args.repeat)
            sys.stdout.buffer.write(canonical_fixture_bytes(result))
    except (OSError, ValueError, RecursionError) as exc:
        print(f"treatment {args.command} failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
