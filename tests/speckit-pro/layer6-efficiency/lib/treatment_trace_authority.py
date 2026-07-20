#!/usr/bin/env python3
"""Treatment authority constants, route ownership, and closed telemetry inventory."""

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
REPLAY_DIGEST_MANIFEST_PATH = "tests/speckit-pro/unit/fixtures/capability-treatment-replay/fixture-digests.json"
REPLAY_FIXTURE_PATHS = (CAPABILITY_FIXTURE_PATH, TREATMENT_FIXTURE_PATH)
REPLAY_CASES = (
    ("TRACE-SUCCESS", "success", "unknown", ("effective_treatment_unknown",), None, "sha256:e8b73e9a64580eb85b0fc482c702f629b7f368de8dbb1e89d5e4e37cfc5766f2"),
    ("TRACE-EXPLICIT-NULL", "explicit_null", "unknown", ("effective_treatment_unknown",), None, "sha256:21067534aafd4cd11c7641f78b21b87d0a60f16a601b1b523baebc88e3d76e69"),
    ("TRACE-UNAVAILABLE", "unavailable", "unknown", ("effective_treatment_unknown",), None, "sha256:a1547f4a1eeaf32e173e8275305997c69b8336ce4cd4153e5c981351bff0172d"),
    ("TRACE-MISDELIVERY", "misdelivery", "hard_fail", ("agent_mismatch", "effective_treatment_unknown"), None, "sha256:f6ec4e7b3f705d65c2bd46532abfda661c51398499ae0d73720271eeabab4cae"),
    ("TRACE-APPROVED-SAME-AGENT-REROUTE", "approved_same_agent_reroute", "non_scorable_rerouted", ("service_reroute_requested_route_non_scorable",), None, "sha256:8b6d51927aeeb4cbd97e9a53bd367b7938abfa8e555bc3bac4ca23b97b9de312"),
    (
        "TRACE-UNAPPROVED-UNIDENTIFIABLE-REROUTE",
        "unapproved_unidentifiable_reroute",
        "hard_fail",
        ("reroute_destination_missing", "reroute_unidentifiable"),
        None,
        "sha256:ac347882d6b84ddcbaa91209495e985de3c72e5b3cfbefb83776469403fe9c25",
    ),
    ("TRACE-DISCOVERY-LOSS", "discovery_loss", "unknown", ("effective_treatment_unknown",), "partial_surface", "sha256:1df39f99442e0bc7e3d2a78c616d04e8009ac174cb483d4f312b80415f74ebd1"),
    ("TRACE-SURFACE-DISAGREEMENT", "surface_disagreement", "unknown", ("effective_treatment_unknown",), "surface_disagreement", "sha256:5ca1a8b4c004e69522671b9acc4ccedc6ca4adddb8918fe976aee33d7315e810"),
)
REPLAY_DISCOVERY_MODEL_DELTAS = {
    "explicit_null": ("explicit_null", None),
    "discovery_loss": ("missing", None),
}
REPLAY_TRACE_BASELINE_DIGESTS = {
    "TRACE-SUCCESS": "sha256:e79b7b33aacf6c41e5dfec9ed7cb7668d658eefcc0fc7f84b412a727dbebae91",
    "TRACE-EXPLICIT-NULL": "sha256:e16a8035cdfcbf3c3742a91ee5a5dc377ec38094169af080e67db2575830e794",
    "TRACE-UNAVAILABLE": "sha256:9ff04fc8c42d9fde007d79dbbda06ac2ac2fac1ab0247b838eebd7eda2adae0f",
    "TRACE-MISDELIVERY": "sha256:248eb26e9f430d2ce5293e35f0068ee9622063bb9d92198ee809f306b532625b",
    "TRACE-APPROVED-SAME-AGENT-REROUTE": "sha256:d40bdea7d2b551f58875a521a141ccc2b3f9d7c5c72bcd5265487d5586ddbf87",
    "TRACE-UNAPPROVED-UNIDENTIFIABLE-REROUTE": "sha256:e466217dfaa2df09d4bce607a2613754fae509cf31bc83da7ae3ee20f67771e2",
    "TRACE-DISCOVERY-LOSS": "sha256:f4d0887f015307b75e0df2a307026aa617c592943d369a7b6693080d403f4087",
    "TRACE-SURFACE-DISAGREEMENT": "sha256:bff29cfbc3dcb78761e3af65d65040ab446acc7257039f3ce9404fe1d92bf485",
}
REPLAY_RUNTIME_EFFORT_AUTHORITY = {
    "schema_version": "1.0.0",
    "authority_kind": "synthetic_replay_configuration",
    "runtime_capability_snapshot_id": "sha256:450a655fabafb765b19bfc9ff3cbefe4b075d6c40fdbc5fd9dbc8ce8c4cfc3fe",
    "candidate_route_id": "G56R-001-CR-PHASE-EXECUTOR-SOL",
    "agent_contract_id": "G56R-001-AC-PHASE-EXECUTOR",
    "named_agent": "phase-executor",
    "model": "gpt-5.6-sol",
    "effort": "high",
}
REPLAY_RUNTIME_EFFORT_AUTHORITY_ID = "sha256:2f629183baad7dd544e7200eb9bab1490ac253f85a3bb91e73670298180fe20c"

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
REPLAY_HOSTNAME_RE = re.compile(
    r"(?i)(?<![A-Z0-9_-])(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.){1,}[A-Z]{2,63}(?![A-Z0-9_-])"
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


def _capability_module():
    spec = importlib.util.spec_from_file_location("g56r_002_capability_for_treatment", CAPABILITY_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load capability freeze validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

__all__ = [name for name in globals() if not name.startswith("__")]
