#!/usr/bin/env python3
"""Treatment authority constants, route ownership, and closed telemetry inventory."""

from __future__ import annotations

import argparse
import copy
import hashlib
import ipaddress
import json
import os
import re
import stat
from collections.abc import Mapping
from datetime import datetime
from functools import lru_cache
from pathlib import Path, PurePosixPath

if __package__:
    from .treatment_trace_capability import *
else:
    from treatment_trace_capability import *


ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = ROOT / "specs/g56r-002-capability-discovery-telemetry/contracts/treatment-record.schema.json"
MANIFEST_PATH = ROOT / "docs/ai/research/codex-agent-route-candidate-manifest.json"
MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_NESTING_DEPTH = 64
MAX_COLLECTION_ITEMS = 10_000
MAX_TOTAL_NODES = 100_000
MAX_RETAINED_STRING_LENGTH = 8_192
HAS_DESCRIPTOR_RELATIVE_IO = os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd
IS_WINDOWS = os.name == "nt"

CAPABILITY_FIXTURE_PATH = "tests/speckit-pro/unit/fixtures/capability-treatment-replay/capability-matrix.json"
CAPABILITY_FIXTURE_BASELINE_DIGEST = "sha256:4c4b2bc56d6ad3251beaab64126ece7012502b0230ce7c474a8cb231d7166b1a"
TREATMENT_FIXTURE_PATH = "tests/speckit-pro/unit/fixtures/capability-treatment-replay/treatment-replay.json"
REPLAY_DIGEST_MANIFEST_PATH = "tests/speckit-pro/unit/fixtures/capability-treatment-replay/fixture-digests.json"
REPLAY_FIXTURE_PATHS = (CAPABILITY_FIXTURE_PATH, TREATMENT_FIXTURE_PATH)
REPLAY_CASES = (
    ("TRACE-SUCCESS", "success", "unknown", ("effective_treatment_unknown",), None, "sha256:0c5f2e407d0caea2a0139a0fdac97882eb45ee8dab6db2aad5736d216e2732d9"),
    ("TRACE-EXPLICIT-NULL", "explicit_null", "unknown", ("effective_treatment_unknown",), None, "sha256:1dd3f74c9de86b5e1cae10614f1919d307aa75c0dcd6426ca04229e98b691df2"),
    ("TRACE-UNAVAILABLE", "unavailable", "unknown", ("effective_treatment_unknown",), None, "sha256:e54959b7d357c5e41c441b867b3332b35262dc29959448251057567b134f420e"),
    ("TRACE-MISDELIVERY", "misdelivery", "hard_fail", ("agent_mismatch", "effective_treatment_unknown"), None, "sha256:c34374c78a1fb95889144587effbd8de961189d12c1ec8dd4ea4a77fa0a0b9bd"),
    ("TRACE-APPROVED-SAME-AGENT-REROUTE", "approved_same_agent_reroute", "non_scorable_rerouted", ("service_reroute_requested_route_non_scorable",), None, "sha256:20439fba89b8f3d23425adae6e46d23819ecc1fe53c3ef4da7a95353111805e8"),
    (
        "TRACE-UNAPPROVED-UNIDENTIFIABLE-REROUTE",
        "unapproved_unidentifiable_reroute",
        "hard_fail",
        ("reroute_destination_missing", "reroute_unidentifiable"),
        None,
        "sha256:4edf8ddf03120ec835e295c3852aef551f2042bd20eca0092a505aaead164c3e",
    ),
    ("TRACE-DISCOVERY-LOSS", "discovery_loss", "unknown", ("effective_treatment_unknown",), "partial_surface", "sha256:739e64329c52c019929ecc67bc9153371d914ddbfca857ffdeba01f648e4ff9f"),
    ("TRACE-SURFACE-DISAGREEMENT", "surface_disagreement", "unknown", ("effective_treatment_unknown",), "surface_disagreement", "sha256:81170575d042c30863349fd364a321ce66f8bb04c3f01f2055cecbeb78152864"),
)
REPLAY_DISCOVERY_MODEL_DELTAS = {
    "explicit_null": ("explicit_null", None),
    "discovery_loss": ("missing", None),
}
REPLAY_TRACE_BASELINE_DIGESTS = {
    "TRACE-SUCCESS": "sha256:88a8d0808a32f62a33942cafcae532f7705c6885b814ebf03408c7e0111e0616",
    "TRACE-EXPLICIT-NULL": "sha256:2a16e4e0583b2c9665e79ad0ff9d0d8f54aecc7aa99bf276637c83aae3fc34b3",
    "TRACE-UNAVAILABLE": "sha256:11f88c9e2d69dc82ccd1ee2f330bf7bda8bc30ce69b166632feb33e6c0a000c3",
    "TRACE-MISDELIVERY": "sha256:56f229647dabef2d4af0835373f497e7d74f9479f0242af264cbce4b47c71cc9",
    "TRACE-APPROVED-SAME-AGENT-REROUTE": "sha256:b5511625683001152b130d9eb00bc04655f10d8c888111cc57b2f7579a850e14",
    "TRACE-UNAPPROVED-UNIDENTIFIABLE-REROUTE": "sha256:324867af769df11809f5748b7fed52c99492ddef85cdd48b67cb7fcd2a019a79",
    "TRACE-DISCOVERY-LOSS": "sha256:85965184a8e5b984f48f418eeb5dba42f96dc3b21e5a7fd667d39c8e5cfecc2e",
    "TRACE-SURFACE-DISAGREEMENT": "sha256:0660f3fe2f08904c9578cd8c73cf26471f23bbf749ba6e138c2e091f3172240e",
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
    "reroute_self_target", "orphan_reroute_destination_assessment",
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


__all__ = [name for name in globals() if not name.startswith("__")]
