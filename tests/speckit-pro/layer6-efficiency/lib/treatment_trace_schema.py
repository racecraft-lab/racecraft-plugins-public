#!/usr/bin/env python3
"""Vendor-neutral G56R-002 telemetry and exact-treatment validation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
from collections.abc import Mapping
from datetime import datetime
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = ROOT / "specs/g56r-002-capability-discovery-telemetry/contracts/treatment-record.schema.json"
MANIFEST_PATH = ROOT / "docs/ai/research/codex-agent-route-candidate-manifest.json"
CAPABILITY_MODULE_PATH = Path(__file__).with_name("codex_capabilities.py")

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

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SOURCE_RE = re.compile(r"^OPENAI-DOC-[0-9]{3}$")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")


@lru_cache(maxsize=1)
def _current_source_ids() -> frozenset[str]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    ids = frozenset(item["official_source_ledger_id"] for item in manifest["official_source_ledger"])
    if len(ids) != 22 or any(SOURCE_RE.fullmatch(item) is None for item in ids):
        raise ValueError("canonical manifest does not expose exactly 22 current source owners")
    return ids


@lru_cache(maxsize=1)
def _canonical_routes() -> dict[str, dict[str, str]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    agents = {item["agent_contract_id"]: item["agent_name"] for item in manifest["agent_contracts"]}
    routes = {}
    for item in manifest["candidate_routes"]:
        contract = item["agent_contract_id"]
        routes[item["candidate_route_id"]] = {
            "agent_contract_id": contract,
            "named_agent": agents[contract],
            "model": item["model_selector"]["expected_resolved_model_id"],
        }
    if len(routes) != len(manifest["candidate_routes"]):
        raise ValueError("canonical manifest candidate routes are not uniquely owned")
    return routes


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: object) -> str:
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def content_id(value: dict, identity_field: str) -> str:
    return digest({key: item for key, item in value.items() if key != identity_field})


def schema_file_digest(path: Path = SCHEMA_PATH) -> str:
    return digest(path.read_bytes())


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
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an RFC3339 timestamp") from exc
    if not value.endswith("Z") or parsed.utcoffset() is None:
        raise ValueError(f"{label} must be an RFC3339 UTC timestamp")
    return value


def _strings(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{label} must be an array of non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} must contain unique values")
    return value


def _profile_key(entry: dict) -> tuple[str, str, str]:
    return entry["client_identity_id"], entry["surface"], entry["field_path"]


def _contains_unknown(value: object) -> bool:
    if value == "unknown": return True
    if isinstance(value, list): return any(_contains_unknown(item) for item in value)
    if isinstance(value, dict): return any(_contains_unknown(item) for item in value.values())
    return False


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


def _validate_profile(profile: object) -> list[dict]:
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
        if source != expected_source or (source is not None and source not in _current_source_ids()):
            raise ValueError("telemetry field does not use its exact field-level source authority")
        if (expected_source is None) != (classification == "undocumented"):
            raise ValueError("telemetry authority and undocumented classification disagree")
        condition_required = classification in {"conditional", "not_applicable"}
        if condition_required != (isinstance(entry["condition"], str) and bool(entry["condition"])):
            raise ValueError("conditional applicability semantics are invalid")
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
        _strings(entry["prohibited_claims"], "prohibited claims")
        expected_claim = CLAIM_BY_CLASS.get(classification)
        if permitted != ([expected_claim] if expected_claim else []):
            raise ValueError("telemetry permitted claims do not match classification semantics")
    actual_inventory = {(item["surface"], item["field_path"]) for item in profile}
    if actual_inventory != TELEMETRY_INVENTORY:
        raise ValueError("telemetry profile does not cover the closed inventory")
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
    _text(env["work_item_id"], "controlled environment work item ID")
    if env["controlled_environment_id"] != content_id(env, "controlled_environment_id"):
        raise ValueError("controlled environment ID is not content addressed")
    return env


def _validate_qualification(value: object) -> dict:
    owner = _closed(value, {
        "qualification_evidence_id", "authority_kind", "owner_spec_id",
        "destination_candidate_route_id", "destination_agent_contract_id",
        "destination_named_agent", "qualification_status", "evidence_digest",
    }, "qualification evidence")
    _digest(owner["qualification_evidence_id"], "qualification evidence ID")
    if owner["authority_kind"] not in {"synthetic_fixture", "owned_external"}:
        raise ValueError("qualification authority kind is invalid")
    for field in ("owner_spec_id", "destination_candidate_route_id", "destination_agent_contract_id", "destination_named_agent"):
        _text(owner[field], f"qualification {field}")
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
    for field in ("route_resolution_id", "preferred_route_id", "assigned_route_id"):
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
    _digest(route["runtime_capability_snapshot_id"], "route resolution snapshot")
    _timestamp(route["resolved_at"], "route resolution timestamp")
    return route


def _validate_tool_vector(value: object, label: str) -> dict:
    vector = _closed(value, {"skills", "mcp_servers", "tools"}, label)
    for field in ("skills", "mcp_servers", "tools"):
        _strings(vector[field], f"{label} {field}")
    return vector


def _validate_trace_structures(trace: dict) -> None:
    sandbox = _closed(trace["sandbox"], {"mode", "network_access", "writable_roots_digest"}, "sandbox")
    if sandbox["mode"] not in {"read_only", "workspace_write", "danger_full_access"} or not isinstance(sandbox["network_access"], bool):
        raise ValueError("sandbox values are invalid")
    _digest(sandbox["writable_roots_digest"], "sandbox writable roots")
    approvals = _closed(trace["approvals"], {"policy", "granted_action_ids"}, "approvals")
    if approvals["policy"] not in {"never", "on_request", "on_failure", "untrusted"}:
        raise ValueError("approval policy is invalid")
    _strings(approvals["granted_action_ids"], "approval action IDs")
    _text(trace["mutation_class"], "mutation class")
    _validate_tool_vector(trace["expected_skills_mcp_tools"], "expected skills MCP tools")
    _validate_tool_vector(trace["loaded_skills_mcp_tools"], "loaded skills MCP tools")
    parent = _closed(trace["parent_configuration"], {"parent_execution_trace_id", "configuration_hash"}, "parent configuration")
    _text(parent["parent_execution_trace_id"], "parent execution trace ID", nullable=True)
    _digest(parent["configuration_hash"], "parent configuration hash")
    overrides = _closed(trace["controlled_overrides"], {"model", "effort", "configuration_hash"}, "controlled overrides")
    _text(overrides["model"], "override model"); _text(overrides["effort"], "override effort")
    _digest(overrides["configuration_hash"], "override configuration hash")
    canary = _closed(trace["delivery_canary"], {"status", "evidence_digest"}, "delivery canary")
    if canary["status"] not in {"passed", "failed", "not_run"}:
        raise ValueError("delivery canary status is invalid")
    _digest(canary["evidence_digest"], "delivery canary evidence", nullable=canary["status"] == "not_run")
    context = _closed(trace["context"], {"threadId", "turnId"}, "trace association context")
    _text(context["threadId"], "trace threadId"); _text(context["turnId"], "trace turnId")
    graph = _closed(trace["parent_child_graph"], {
        "root_execution_trace_id", "parent_execution_trace_id", "child_execution_trace_ids",
    }, "parent-child graph")
    _text(graph["root_execution_trace_id"], "root execution trace ID")
    _text(graph["parent_execution_trace_id"], "graph parent trace ID", nullable=True)
    _strings(graph["child_execution_trace_ids"], "child execution trace IDs")
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
    _digest(validation["evidence_digest"], "validation evidence", nullable=validation["status"] == "not_run")
    cancellation = _closed(trace["cancellation"], {"state", "reason"}, "cancellation")
    if cancellation["state"] not in {"not_requested", "requested", "completed"}: raise ValueError("cancellation state is invalid")
    _text(cancellation["reason"], "cancellation reason", nullable=True)
    if cancellation["state"] == "not_requested" and cancellation["reason"] is not None: raise ValueError("uncancelled work cannot carry a cancellation reason")
    failed = _closed(trace["failed_abandoned_work"], {"failed_count", "abandoned_count"}, "failed-abandoned work")
    _integer(failed["failed_count"], "failed-work count"); _integer(failed["abandoned_count"], "abandoned-work count")
    if trace["terminal_state"] not in {"completed", "failed", "cancelled", "abandoned"}: raise ValueError("terminal state is invalid")
    outcome = _closed(trace["outcome"], {"status", "evidence_digest"}, "outcome")
    if outcome["status"] not in {"completed", "failed", "cancelled", "abandoned", "unknown"}: raise ValueError("outcome status is invalid")
    _digest(outcome["evidence_digest"], "outcome evidence", nullable=outcome["status"] == "unknown")
    if trace["acceptance"] is not None and not isinstance(trace["acceptance"], bool): raise ValueError("acceptance must be boolean or null")


def _validate_failure(value: object) -> dict:
    failure = _closed(value, {
        "failure_code", "affected_field", "expected_evidence_ref",
        "observed_evidence_ref", "resulting_disposition",
    }, "treatment failure")
    if failure["failure_code"] not in FAILURE_DISPOSITIONS:
        raise ValueError("treatment failure code is invalid")
    _text(failure["affected_field"], "treatment failure affected field")
    _text(failure["expected_evidence_ref"], "expected evidence reference", nullable=True)
    _text(failure["observed_evidence_ref"], "observed evidence reference", nullable=True)
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
            _text(row["evidence_ref"], "observation evidence reference"); _timestamp(row["captured_at"], "observation capture timestamp")
        else:
            _text(row["evidence_ref"], "observation evidence reference", nullable=True); _timestamp(row["captured_at"], "observation capture timestamp", nullable=True)
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
    for field in ("named_agent", "model", "effort", "candidate_route_id", "agent_contract_id", "launch_id"): _text(proof[field], f"configured proof {field}")
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
    for field in ("threadId", "turnId", "fromModel", "toModel", "reason"): _text(event[field], f"reroute {field}")
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


def _reroute_disposition(trace: dict, events: list[dict], assessments: list[dict], qualification: dict[str, dict], trusted: dict[str, dict]) -> tuple[str, list[str]]:
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
        canonical = _canonical_routes().get(item["destination_candidate_route_id"])
        if canonical is None: return "hard_fail", ["reroute_destination_unidentifiable"]
        if item["destination_named_agent"] != canonical["named_agent"]: return "hard_fail", ["reroute_destination_different_agent"]
        if item["destination_agent_contract_id"] != canonical["agent_contract_id"]: return "hard_fail", ["reroute_destination_manifest_mismatch"]
        if event["toModel"] != canonical["model"]: return "hard_fail", ["reroute_destination_model_mismatch"]
        expected = (item["destination_candidate_route_id"], item["destination_agent_contract_id"], item["destination_named_agent"])
        actual = (evidence["destination_candidate_route_id"], evidence["destination_agent_contract_id"], evidence["destination_named_agent"])
        if expected != actual or item["destination_named_agent"] != trace["named_agent"]: return "hard_fail", ["reroute_destination_mismatch"]
        if evidence["authority_kind"] != "owned_external" or evidence["owner_spec_id"] == "G56R-002": return "hard_fail", ["reroute_destination_non_authoritative"]
        admitted = trusted.get(evidence["qualification_evidence_id"])
        if admitted is None or canonical_bytes(admitted) != canonical_bytes(evidence): return "hard_fail", ["reroute_destination_untrusted"]
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
                    resolutions: dict[str, dict], qualification: dict[str, dict], trusted: dict[str, dict]) -> dict:
    row = _closed(trace, TRACE_KEYS, "treatment trace")
    objective = _closed(row["objective_binding"], set(OBJECTIVE_ID_FIELDS), "six-ID objective binding")
    for field in OBJECTIVE_ID_FIELDS: _text(objective[field], f"objective {field}")
    _digest(objective["runtime_capability_snapshot_id"], "objective runtime snapshot")
    env_id = _digest(row["controlled_environment_id"], "trace controlled environment ID")
    if env_id not in environments: raise ValueError("trace has no controlled environment owner")
    env = environments[env_id]
    resolution_id = objective["route_resolution_id"]
    if resolution_id not in resolutions: raise ValueError("trace has no route resolution owner")
    resolution = resolutions[resolution_id]
    _digest(row["client_identity_id"], "trace client identity"); _digest(row["repository_tree_digest"], "trace repository tree")
    if row["surface"] not in SURFACES or row["work_item_kind"] not in {"task", "fixture", "objective"}: raise ValueError("trace surface or work item kind is invalid")
    if not isinstance(row["repository_revision"], str) or REVISION_RE.fullmatch(row["repository_revision"]) is None: raise ValueError("trace repository revision is invalid")
    for field in ("work_item_id", "named_agent", "assigned_route_id", "requested_model", "requested_effort"): _text(row[field], f"trace {field}")
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
    canonical_route = _canonical_routes().get(objective["candidate_route_id"])
    if canonical_route is None or canonical_route != {
        "agent_contract_id": objective["agent_contract_id"], "named_agent": row["named_agent"], "model": row["requested_model"],
    }:
        raise ValueError("assigned route does not bind the canonical candidate manifest")
    if resolution["runtime_capability_snapshot_id"] != objective["runtime_capability_snapshot_id"]: raise ValueError("route resolution snapshot does not join the objective")
    if row["parent_child_graph"]["root_execution_trace_id"] != objective["execution_trace_id"]: raise ValueError("parent-child graph does not bind the execution trace")
    _validate_trace_structures(row)
    observations = _validate_observations(row, profile)
    proof = _validate_proof(row["configured_route_proof"], row, profile)
    failures = row["treatment_failures"]
    if not isinstance(failures, list): raise ValueError("treatment failures must be an array")
    validated_failures = [_validate_failure(item) for item in failures]
    if len({item["failure_code"] for item in validated_failures}) != len(validated_failures): raise ValueError("duplicate structured treatment failure code")
    derived_codes = _proof_failure_codes(proof, row, profile)
    events = row["service_reroute_events"]; assessments = row["reroute_destination_assessments"]
    if not isinstance(events, list) or not isinstance(assessments, list): raise ValueError("reroute records must be arrays")
    events = [_validate_event(item) for item in events]; assessments = [_validate_assessment(item) for item in assessments]
    if len({item["event_id"] for item in events}) != len(events): raise ValueError("duplicate reroute event ID")
    if row["supported_effective_effort"] is not None: derived_codes.append("effort_mismatch")
    if row["supported_effective_model"] is not None and (len(events) != 1 or events[0]["toModel"] != row["supported_effective_model"]): derived_codes.append("model_mismatch")
    if events and row["supported_effective_model"] is None: derived_codes.append("model_mismatch")
    if observations["reroute.events"]["observation_state"] == "observed_value":
        if observations["reroute.events"]["value"] != events: derived_codes.append("reroute_ambiguous")
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
        "route.resolved_at": resolution["resolved_at"], "treatment.sandbox": row["sandbox"], "treatment.approvals": row["approvals"],
        "treatment.mutation_class": row["mutation_class"], "treatment.expected_skills_mcp_tools": row["expected_skills_mcp_tools"],
        "treatment.loaded_skills_mcp_tools": row["loaded_skills_mcp_tools"], "treatment.parent_configuration": row["parent_configuration"],
        "treatment.controlled_overrides": row["controlled_overrides"], "treatment.delivery_canary": row["delivery_canary"],
        "parent.context": row["context"], "parent.graph": row["parent_child_graph"],
        "resources.raw_token_vector": row["raw_token_vector"], "resources.request_turn_count": row["request_turn_count"],
        "resources.wall_time_ms": row["wall_time_ms"], "lifecycle.retries": row["retries"], "lifecycle.compaction": row["compaction"],
        "lifecycle.validation": row["validation"], "lifecycle.cancellation": row["cancellation"],
        "lifecycle.failed_abandoned_work": row["failed_abandoned_work"], "terminal.state": row["terminal_state"],
        "terminal.outcome": row["outcome"], "terminal.acceptance": row["acceptance"],
    }
    observation_failure_codes = {
        "discovery.models": "model_mismatch", "discovery.efforts": "effort_mismatch",
        "discovery.capabilities": "skills_mcp_tools_mismatch", "assignment.named_agent": "agent_mismatch",
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
        observed = observations[field]
        mismatch = observed["observation_state"] == "observed_value" and observed["value"] != expected
        mismatch |= observed["observation_state"] == "explicit_null" and expected is not None
        mismatch |= observed["observation_state"] in {"unavailable", "not_applicable", "undocumented", "missing"} and expected is not None
        if mismatch: derived_codes.append("configuration_mismatch" if field in configuration_fields else observation_failure_codes.get(field, "effective_treatment_unknown"))
    if row["expected_skills_mcp_tools"] != row["loaded_skills_mcp_tools"]: derived_codes.append("skills_mcp_tools_mismatch")
    if row["parent_configuration"]["parent_execution_trace_id"] != row["parent_child_graph"]["parent_execution_trace_id"]: derived_codes.append("parent_configuration_mismatch")
    if row["controlled_overrides"]["model"] != row["requested_model"] or row["controlled_overrides"]["effort"] != row["requested_effort"]: derived_codes.append("client_or_override_mismatch")
    proof_configuration_hash = proof["configuration_hash"] if proof is not None else row["configuration_hash"]
    if len({row["configuration_hash"], row["controlled_overrides"]["configuration_hash"], proof_configuration_hash}) != 1: derived_codes.append("configuration_mismatch")
    if row["delivery_canary"]["status"] == "failed": derived_codes.append("delivery_canary_failure")
    reroute_disposition, reasons = _reroute_disposition(row, events, assessments, qualification, trusted)
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
        row[field] is not None and observations[path]["observation_state"] == "observed_value" and observations[path]["value"] == row[field]
        for field, path in (("supported_effective_model", "assignment.supported_effective_model"), ("supported_effective_effort", "assignment.supported_effective_effort"))
    )
    reroute_profile = profile_entry(profile, row["client_identity_id"], row["surface"], "reroute.events")
    monitoring_authoritative = (
        proof is not None and proof["reroute_monitoring_complete"]
        and reroute_profile["classification"] == "stable_native"
        and reroute_profile["completeness_rule"] == "complete_capture"
        and observations["reroute.events"]["observation_state"] == "observed_value"
    )
    proof_valid = proof is not None and not _proof_failure_codes(proof, row, profile) and monitoring_authoritative
    if not reroute_disposition and not proof_valid and not effective_observed:
        derived_codes.append("effective_treatment_unknown")
    derived_codes = list(dict.fromkeys(derived_codes))
    declared_by_code = {item["failure_code"]: item for item in validated_failures}
    unsubstantiated = set(declared_by_code) - set(derived_codes)
    if unsubstantiated: raise ValueError(f"unsubstantiated declared treatment failure: {sorted(unsubstantiated)}")
    normalized_failures = [{
        "failure_code": code, "affected_field": "treatment.evidence", "expected_evidence_ref": None,
        "observed_evidence_ref": None, "resulting_disposition": FAILURE_DISPOSITIONS[code],
    } for code in derived_codes]
    if validated_failures and validated_failures != normalized_failures:
        raise ValueError("declared treatment failures do not match derived treatment failures")
    row["treatment_failures"] = normalized_failures
    failure_dispositions = {item["resulting_disposition"] for item in normalized_failures}
    if reroute_disposition == "non_scorable_rerouted" and "hard_fail" not in failure_dispositions: expected_disposition, expected_reasons = reroute_disposition, reasons
    elif "hard_fail" in failure_dispositions: expected_disposition, expected_reasons = "hard_fail", sorted(derived_codes)
    elif "unknown" in failure_dispositions: expected_disposition, expected_reasons = "unknown", sorted(derived_codes)
    elif proof_valid: expected_disposition, expected_reasons = "proven", ["configured_route_proof_and_complete_reroute_monitoring"]
    elif effective_observed: expected_disposition, expected_reasons = "proven", ["profile_supported_effective_treatment"]
    else: expected_disposition, expected_reasons = "unknown", ["effective_treatment_or_reroute_evidence_missing"]
    if row["treatment_disposition"] not in {"proven", "unknown", "non_scorable_rerouted", "hard_fail"}: raise ValueError("declared treatment disposition is invalid")
    _strings(row["disposition_reasons"], "treatment disposition reasons")
    row["treatment_disposition"] = expected_disposition; row["disposition_reasons"] = expected_reasons
    return row


def validate_treatment_bundle(bundle: object, *, schema_path: Path = SCHEMA_PATH,
                              trusted_qualification_evidence: Mapping[str, dict] | None = None) -> dict:
    value = _closed(copy.deepcopy(bundle), {
        "schema_version", "treatment_contract_digest", "telemetry_profile_id", "telemetry_profile",
        "controlled_environments", "qualification_evidence_registry", "route_resolutions",
        "treatment_traces", "fixture_provenance",
    }, "treatment bundle")
    if value["schema_version"] != SCHEMA_VERSION: raise ValueError("unsupported treatment schema version")
    contract_digest = schema_file_digest(schema_path)
    if value["treatment_contract_digest"] != contract_digest: raise ValueError("treatment contract digest does not bind the exact schema bytes")
    profile = _validate_profile(value["telemetry_profile"])
    trusted = _validate_trusted_qualification(trusted_qualification_evidence)
    expected_profile_id = telemetry_profile_id(value["schema_version"], profile, contract_digest)
    if value["telemetry_profile_id"] != expected_profile_id: raise ValueError("telemetry profile ID does not bind the profile and treatment contract")
    registries = (("controlled_environments", _validate_environment, "controlled_environment_id", "controlled environment"),
                  ("qualification_evidence_registry", _validate_qualification, "qualification_evidence_id", "qualification evidence"),
                  ("route_resolutions", _validate_resolution, "route_resolution_id", "route resolution"))
    owners: dict[str, dict[str, dict]] = {}
    for field, validator, identity, label in registries:
        if not isinstance(value[field], list): raise ValueError(f"{field} must be an array")
        rows = [validator(item) for item in value[field]]; keys = [item[identity] for item in rows]
        if len(keys) != len(set(keys)): raise ValueError(f"duplicate {label} owner")
        owners[field] = dict(zip(keys, rows))
    traces = value["treatment_traces"]
    if not isinstance(traces, list) or not traces: raise ValueError("treatment traces must be a non-empty array")
    validated = [_validate_trace(
        item, profile, owners["controlled_environments"], owners["route_resolutions"],
        owners["qualification_evidence_registry"], trusted,
    ) for item in traces]
    referenced_environments = {item["controlled_environment_id"] for item in validated}
    if referenced_environments != set(owners["controlled_environments"]):
        raise ValueError("controlled environment owner registry contains a missing or orphan owner")
    referenced_resolutions = {item["objective_binding"]["route_resolution_id"] for item in validated}
    if referenced_resolutions != set(owners["route_resolutions"]):
        raise ValueError("route resolution owner registry contains a missing or orphan owner")
    execution_ids = [item["objective_binding"]["execution_trace_id"] for item in validated]
    if len(execution_ids) != len(set(execution_ids)): raise ValueError("duplicate execution trace ID")
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
        raise ValueError("fixture expected dispositions do not match traces")
    return value


def _capability_module():
    spec = importlib.util.spec_from_file_location("g56r_002_capability_for_treatment", CAPABILITY_MODULE_PATH)
    if spec is None or spec.loader is None: raise RuntimeError("cannot load capability freeze validator")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def build_treatment_successor(prior_freeze: dict, treatment_bundle: dict, *, manifest_path: Path = MANIFEST_PATH) -> dict:
    validated = validate_treatment_bundle(treatment_bundle)
    capability = _capability_module(); manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if prior_freeze["candidate_freeze_id"] != digest({key: value for key, value in prior_freeze.items() if key != "candidate_freeze_id"}):
        raise ValueError("prior freeze identity is invalid")
    try: capability.validate_freeze(prior_freeze, manifest)
    except ValueError as exc: raise ValueError(f"prior freeze identity or semantics are invalid: {exc}") from exc
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
        (item["candidate_route_id"], item["agent_contract_id"]): (item["instruction_sha256"], item["role_instruction_sha256"])
        for item in prior_freeze["tuple_decisions"]
    }
    for trace in validated["treatment_traces"]:
        objective = trace["objective_binding"]
        instruction_identity = prior_tuples.get((objective["candidate_route_id"], objective["agent_contract_id"]))
        if instruction_identity is None:
            raise ValueError("treatment bundle candidate tuple is not present in the prior freeze")
        if instruction_identity != (trace["instruction_hash"], trace["instruction_hash"]):
            raise ValueError("treatment bundle instruction identity does not match the prior freeze")
    successor = copy.deepcopy(prior_freeze); prior_id = prior_freeze["candidate_freeze_id"]
    successor["telemetry_profile_id"] = validated["telemetry_profile_id"]
    successor["supersedes_candidate_freeze_id"] = prior_id
    successor["candidate_freeze_id"] = digest({key: value for key, value in successor.items() if key != "candidate_freeze_id"})
    for key, value in prior_freeze.items():
        if key not in {"candidate_freeze_id", "telemetry_profile_id", "supersedes_candidate_freeze_id"} and canonical_bytes(successor[key]) != canonical_bytes(value):
            raise ValueError("treatment successor changed frozen capability evidence")
    capability.validate_freeze(successor, manifest)
    if successor["supersedes_candidate_freeze_id"] != prior_id: raise ValueError("treatment successor does not bind the actual prior freeze")
    return successor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate"); validate.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args(argv)
    bundle = json.loads(args.fixture.read_text(encoding="utf-8")); validate_treatment_bundle(bundle)
    print(json.dumps({"status": "valid", "telemetry_profile_id": bundle["telemetry_profile_id"]}, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
