#!/usr/bin/env python3
"""Focused deterministic tests for the G56R-002 capability contract."""

from __future__ import annotations

import copy
import base64
from collections.abc import Mapping
import importlib.util
import itertools
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py"
FIXTURE_PATH = ROOT / "tests/speckit-pro/unit/fixtures/capability-treatment-replay/capability-matrix.json"
MANIFEST_PATH = ROOT / "docs/ai/research/codex-agent-route-candidate-manifest.json"
PUBLISHED_FREEZE_PATH = ROOT / "docs/ai/research/codex-g56r-002-executable-candidate-freeze.json"
CAPABILITY_EVIDENCE_PATH = ROOT / "docs/ai/research/codex-g56r-002-capability-evidence.md"
TREATMENT_MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py"
TREATMENT_FIXTURE_PATH = ROOT / "tests/speckit-pro/unit/fixtures/capability-treatment-replay/treatment-replay.json"
TREATMENT_PREDECESSOR_PUBLISHED_AT = "2026-07-17T04:44:32.543011Z"
TREATMENT_SUCCESSOR_PUBLISHED_AT = "2026-07-18T19:40:00Z"

EXPECTED_APP_SERVER_TELEMETRY_FIELDS = frozenset({
    "discovery.models", "discovery.efforts", "discovery.capabilities",
    "assignment.named_agent", "assignment.model", "assignment.effort",
    "assignment.candidate_route_id", "assignment.agent_contract_id",
    "assignment.instruction_hash", "assignment.configuration_hash",
    "route.preferred_route_id", "route.attempted_route_ids", "route.assigned_route_id",
    "route.supported_effective_route_id", "route.fallback_index", "route.fallback_reason",
    "route.runtime_capability_snapshot_id", "route.resolved_at", "reroute.events",
    "treatment.sandbox", "treatment.approvals", "treatment.mutation_class",
    "treatment.expected_skills_mcp_tools", "treatment.loaded_skills_mcp_tools",
    "treatment.parent_configuration", "treatment.controlled_overrides",
    "treatment.delivery_canary", "assignment.supported_effective_model",
    "assignment.supported_effective_effort", "treatment.failures", "parent.context", "parent.graph",
    "resources.raw_token_vector", "resources.request_turn_count", "resources.wall_time_ms",
    "lifecycle.retries", "lifecycle.compaction", "lifecycle.validation",
    "lifecycle.cancellation", "lifecycle.failed_abandoned_work", "terminal.state",
    "terminal.outcome", "terminal.acceptance",
})
EXPECTED_TELEMETRY_INVENTORY = frozenset(
    {("app_server", field) for field in EXPECTED_APP_SERVER_TELEMETRY_FIELDS}
    | {("cli", "route.supported_effective_route_id"), ("interactive_picker", "parent.graph")}
)

EXPECTED_CAPABILITY_PUBLIC_API = frozenset({
    "APPROVED_CANARY_EXECUTORS", "APPROVED_LIVE_COLLECTION_METHODS",
    "CANONICAL_MANIFEST_DIGEST", "CANONICAL_MANIFEST_SCHEMA_VERSION",
    "CANONICAL_MANIFEST_SNAPSHOT_ID", "DELETION_INTENTS_DIR", "DELETION_RECORDS_DIR",
    "ERROR_TERMINALS", "EXTRACT_NORMALIZATION", "HAS_DESCRIPTOR_RELATIVE_IO",
    "PENDING_TELEMETRY_PROFILE_ID", "PRIVATE_REFRESH_MAX_BYTES", "PUBLICATION_RECEIPTS_DIR",
    "RAW_EVIDENCE_PENDING_DAYS", "RAW_EVIDENCE_RETENTION_DAYS", "RETENTION_LOCK_FILE",
    "RETENTION_RECORDS_DIR", "SCHEMA_VERSION", "SURFACES", "build_canary_successor",
    "build_client_identity", "build_freeze", "build_repository_binding",
    "build_runtime_snapshot", "candidate_tuples_from_manifest", "candidate_tuples_from_published",
    "canonical_bytes", "digest", "digest_regular_file", "evaluate_surface_matrix",
    "fixture_observation", "main", "materialize_source_capture", "materialize_unknown_capture",
    "normalize_source_refreshes", "publish_with_raw_evidence_retention",
    "read_content_addressed_private_file", "read_private_external_file",
    "reconcile_raw_evidence_retention", "repository_binding_from_checkout", "sanitize",
    "unknown_observation", "validate_canary_evidence", "validate_canary_result",
    "validate_canary_results", "validate_content_addressed_private_file", "validate_freeze",
    "validate_manifest", "validate_observation", "validate_private_external_file",
    "validate_published_source_refreshes", "validate_raw_evidence_root",
    "validate_repository_binding", "validate_source_capture_evidence", "validate_source_refreshes",
    "validate_surface_matrix", "validate_tuple_decisions", "validate_unknown_observation_evidence",
    "validate_work_item",
})

spec = importlib.util.spec_from_file_location("g56r_002_codex_capabilities", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {MODULE_PATH}")
capabilities = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capabilities)

capability_contract = sys.modules["codex_capability_contract"]
capability_freeze = sys.modules["codex_capability_freeze"]
capability_io = sys.modules["codex_capability_io"]
capability_observations = sys.modules["codex_capability_observations"]
capability_private = sys.modules["codex_capability_private"]
capability_publish_io = sys.modules["codex_capability_publish_io"]
capability_retention = sys.modules["codex_capability_retention"]
capability_retention_records = sys.modules["codex_capability_retention_records"]

treatment_spec = importlib.util.spec_from_file_location("g56r_002_treatment_trace_schema", TREATMENT_MODULE_PATH)
if treatment_spec is None or treatment_spec.loader is None:
    raise RuntimeError(f"cannot load {TREATMENT_MODULE_PATH}")
treatment = importlib.util.module_from_spec(treatment_spec)
treatment_spec.loader.exec_module(treatment)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rebind_treatment_owners(bundle: dict) -> dict:
    route_ids: dict[str, str] = {}
    for route in bundle["route_resolutions"]:
        old_id = route["route_resolution_id"]
        route["route_resolution_id"] = treatment.content_id(route, "route_resolution_id")
        route_ids[old_id] = route["route_resolution_id"]
    policy_ids: dict[str, str] = {}
    for policy in bundle["experiment_policy_registry"]:
        old_id = policy["experiment_policy_id"]
        policy["experiment_policy_id"] = treatment.content_id(policy, "experiment_policy_id")
        policy_ids[old_id] = policy["experiment_policy_id"]
    environment_ids: dict[str, str] = {}
    for environment in bundle["controlled_environments"]:
        old_id = environment["controlled_environment_id"]
        environment["controlled_environment_id"] = treatment.content_id(environment, "controlled_environment_id")
        environment_ids[old_id] = environment["controlled_environment_id"]
    for trace in bundle["treatment_traces"]:
        objective = trace["objective_binding"]
        objective["route_resolution_id"] = route_ids.get(objective["route_resolution_id"], objective["route_resolution_id"])
        objective["experiment_policy_id"] = policy_ids.get(objective["experiment_policy_id"], objective["experiment_policy_id"])
        trace["controlled_environment_id"] = environment_ids.get(trace["controlled_environment_id"], trace["controlled_environment_id"])
    trace_ids: dict[str, str] = {}
    for trace in bundle["treatment_traces"]:
        old_id = trace["objective_binding"]["execution_trace_id"]
        trace["objective_binding"]["execution_trace_id"] = treatment.execution_trace_identity(trace)
        trace_ids[old_id] = trace["objective_binding"]["execution_trace_id"]
    for trace in bundle["treatment_traces"]:
        parent = trace["parent_configuration"]["parent_execution_trace_id"]
        trace["parent_configuration"]["parent_execution_trace_id"] = trace_ids.get(parent, parent)
        graph = trace["parent_child_graph"]
        graph["root_execution_trace_id"] = trace_ids.get(graph["root_execution_trace_id"], graph["root_execution_trace_id"])
        graph["parent_execution_trace_id"] = trace_ids.get(graph["parent_execution_trace_id"], graph["parent_execution_trace_id"])
        graph["child_execution_trace_ids"] = [trace_ids.get(item, item) for item in graph["child_execution_trace_ids"]]
        parent_observation = next((item for item in trace["observations"] if item["field_path"] == "parent.graph"), None)
        if parent_observation is not None and parent_observation["observation_state"] == "observed_value":
            parent_observation["value"] = copy.deepcopy(graph)
    for expected in bundle["fixture_provenance"]["expected_dispositions"]:
        expected["execution_trace_id"] = trace_ids.get(expected["execution_trace_id"], expected["execution_trace_id"])
    return bundle


def make_two_trace_graph_bundle(source: dict) -> dict:
    bundle = copy.deepcopy(source); root_trace = bundle["treatment_traces"][0]
    root_id = root_trace["objective_binding"]["execution_trace_id"]
    child_placeholder = "sha256:" + "9" * 64
    child_policy = copy.deepcopy(bundle["experiment_policy_registry"][0])
    child_policy["work_item_id"] = "G56R-002-T021"
    child_policy["experiment_policy_id"] = treatment.content_id(child_policy, "experiment_policy_id")
    bundle["experiment_policy_registry"].append(child_policy)
    child_environment = copy.deepcopy(bundle["controlled_environments"][0])
    child_environment["work_item_id"] = "G56R-002-T021"
    child_environment["controlled_environment_id"] = treatment.content_id(child_environment, "controlled_environment_id")
    bundle["controlled_environments"].append(child_environment)
    child = copy.deepcopy(root_trace)
    child["work_item_id"] = "G56R-002-T021"
    child["controlled_environment_id"] = child_environment["controlled_environment_id"]
    child["objective_binding"]["experiment_policy_id"] = child_policy["experiment_policy_id"]
    child["objective_binding"]["execution_trace_id"] = child_placeholder
    child["context"]["turnId"] = "turn-fixture-002"
    next(item for item in child["observations"] if item["field_path"] == "parent.context")["value"] = copy.deepcopy(child["context"])
    child["parent_configuration"]["parent_execution_trace_id"] = root_id
    child["parent_configuration"]["configuration_hash"] = root_trace["configuration_hash"]
    next(item for item in child["observations"] if item["field_path"] == "treatment.parent_configuration")["value"] = copy.deepcopy(child["parent_configuration"])
    child["parent_child_graph"] = {
        "root_execution_trace_id": root_id,
        "parent_execution_trace_id": root_id,
        "child_execution_trace_ids": [],
    }
    root_trace["parent_child_graph"]["child_execution_trace_ids"] = [child_placeholder]
    for trace in (root_trace, child):
        observation = next(item for item in trace["observations"] if item["field_path"] == "parent.graph")
        observation.update({
            "observation_state": "observed_value", "value": copy.deepcopy(trace["parent_child_graph"]),
            "evidence_ref": "fixture://trace/parent-graph", "captured_at": "2026-07-17T04:01:00Z",
        })
    bundle["treatment_traces"].append(child)
    bundle["fixture_provenance"]["expected_dispositions"].append({
        "execution_trace_id": child_placeholder, "treatment_disposition": "unknown",
    })
    return rebind_treatment_owners(bundle)


def qualification_owner(authority_kind: str) -> dict:
    owner = {
        "authority_kind": authority_kind,
        "owner_spec_id": "G56R-003" if authority_kind == "owned_external" else "G56R-002",
        "destination_candidate_route_id": "G56R-001-CR-PHASE-EXECUTOR-GPT55",
        "destination_agent_contract_id": "G56R-001-AC-PHASE-EXECUTOR",
        "destination_named_agent": "phase-executor",
        "qualification_status": "prequalified",
        "evidence_digest": "sha256:" + ("d" if authority_kind == "owned_external" else "e") * 64,
    }
    owner["qualification_evidence_id"] = treatment.content_id(owner, "qualification_evidence_id")
    return owner


def trusted_external_qualification(bundle: dict) -> dict[str, dict]:
    owner = next(item for item in bundle["qualification_evidence_registry"] if item["authority_kind"] == "owned_external")
    return {owner["qualification_evidence_id"]: copy.deepcopy(owner)}


def bind_trusted_treatment_evidence(bundle: dict) -> tuple[dict, dict[str, bytes]]:
    evidence: dict[str, bytes] = {}
    for trace in bundle["treatment_traces"]:
        proof = trace["configured_route_proof"]
        if proof is None:
            continue
        payload = {
            "schema_version": treatment.CONSUMPTION_EVIDENCE_VERSION,
            "consumed_configuration": {
                key: copy.deepcopy(value)
                for key, value in proof.items()
                if key not in {"proof_id", "consumption_evidence_digest"}
            },
        }
        raw = treatment.canonical_bytes(payload) + b"\n"
        proof["consumption_evidence_digest"] = treatment.digest(raw)
        proof["proof_id"] = treatment.content_id(proof, "proof_id")
        evidence[proof["consumption_evidence_digest"]] = raw
    rebind_treatment_owners(bundle)
    observations_by_ref: dict[str, list[dict]] = {}
    for trace in bundle["treatment_traces"]:
        trace_id = trace["objective_binding"]["execution_trace_id"]
        for observation in trace["observations"]:
            evidence_ref = observation["evidence_ref"]
            if evidence_ref is None:
                continue
            observations_by_ref.setdefault(evidence_ref, []).append({
                "execution_trace_id": trace_id,
                "field_path": observation["field_path"],
                "observation_state": observation["observation_state"],
                "value": copy.deepcopy(observation["value"]),
                "captured_at": observation["captured_at"],
            })
    for evidence_ref, observations in observations_by_ref.items():
        payload = {
            "schema_version": treatment.OBSERVATION_EVIDENCE_VERSION,
            "evidence_ref": evidence_ref,
            "observations": sorted(
                observations,
                key=lambda item: (item["execution_trace_id"], item["field_path"]),
            ),
        }
        evidence[evidence_ref] = treatment.canonical_bytes(payload) + b"\n"
    bundle_binding = copy.deepcopy(bundle)
    del bundle_binding["fixture_provenance"]["raw_evidence_digest"]
    source_payload = {
        "schema_version": treatment.SOURCE_EVIDENCE_VERSION,
        "sanitized_treatment_bundle_digest": treatment.digest(bundle_binding),
    }
    source_bytes = treatment.canonical_bytes(source_payload) + b"\n"
    source_digest = treatment.digest(source_bytes)
    bundle["fixture_provenance"]["raw_evidence_digest"] = source_digest
    evidence[source_digest] = source_bytes
    return bundle, evidence


def declare_treatment_result(
    bundle: dict, failure_codes: list[str], disposition: str, reasons: list[str], *, trace_index: int = 0,
) -> dict:
    trace = bundle["treatment_traces"][trace_index]
    trace["treatment_failures"] = [{
        "failure_code": code, "affected_field": "treatment.evidence",
        "expected_evidence_ref": None, "observed_evidence_ref": None,
        "resulting_disposition": treatment.FAILURE_DISPOSITIONS[code],
    } for code in failure_codes]
    trace["treatment_disposition"] = disposition
    trace["disposition_reasons"] = reasons
    expected_trace_id = trace["objective_binding"]["execution_trace_id"]
    expected = next(
        item for item in bundle["fixture_provenance"]["expected_dispositions"]
        if item["execution_trace_id"] == expected_trace_id
    )
    expected["treatment_disposition"] = disposition
    return bundle


REROUTE_REASON_FAILURES = {
    "reroute_association_mismatch": "reroute_unidentifiable",
    "ambiguous_reroute_association": "reroute_ambiguous",
    "reroute_destination_missing": "reroute_unidentifiable",
    "reroute_destination_ambiguous": "reroute_ambiguous",
    "reroute_destination_unapproved": "reroute_unapproved",
    "reroute_destination_mismatch": "reroute_different_agent",
    "reroute_destination_unidentifiable": "reroute_unidentifiable",
    "reroute_destination_manifest_mismatch": "reroute_unidentifiable",
    "reroute_destination_different_agent": "reroute_different_agent",
    "reroute_destination_model_mismatch": "model_mismatch",
    "reroute_destination_non_authoritative": "reroute_unapproved",
    "reroute_destination_untrusted": "reroute_unapproved",
    "reroute_effective_destination_mismatch": "model_mismatch",
    "reroute_source_model_mismatch": "model_mismatch",
    "orphan_reroute_destination_assessment": "reroute_ambiguous",
}


def declare_reroute_result(bundle: dict, trusted: dict[str, dict] | None = None) -> dict:
    trace = bundle["treatment_traces"][0]
    events = trace["service_reroute_events"]
    qualification = {
        item["qualification_evidence_id"]: item for item in bundle["qualification_evidence_registry"]
    }
    disposition, detailed_reasons = treatment._reroute_disposition(
        trace, events, trace["reroute_destination_assessments"],
        qualification, trusted or {}, treatment._canonical_routes(load_json(MANIFEST_PATH)),
    )
    directly_derived = []
    if trace["supported_effective_effort"] is not None:
        directly_derived.append("effort_mismatch")
    if trace["supported_effective_model"] is not None and (
        len(events) != 1 or events[0]["toModel"] != trace["supported_effective_model"]
    ):
        directly_derived.append("model_mismatch")
    if events and trace["supported_effective_model"] is None:
        directly_derived.append("model_mismatch")
    failure_codes = list(dict.fromkeys(directly_derived + [
        REROUTE_REASON_FAILURES[reason] for reason in detailed_reasons
        if reason in REROUTE_REASON_FAILURES
    ]))
    reasons = (
        sorted(set(failure_codes) | set(detailed_reasons))
        if disposition == "hard_fail" else detailed_reasons
    )
    return declare_treatment_result(bundle, failure_codes, disposition, reasons)


def make_treatment_reroute_case(bundle: dict, authority: str) -> dict:
    trace = bundle["treatment_traces"][0]
    owned = qualification_owner("owned_external")
    synthetic = qualification_owner("synthetic_fixture")
    event = {
        "surface": trace["surface"], "threadId": trace["context"]["threadId"], "turnId": trace["context"]["turnId"],
        "fromModel": trace["requested_model"], "toModel": "gpt-5.5", "reason": "fixture_service_reroute",
        "evidence_digest": treatment.digest(b"fixture-reroute-evidence"),
    }
    event["event_id"] = treatment.digest(event)
    selected = synthetic if authority == "synthetic_fixture" else owned
    bundle["qualification_evidence_registry"] = [] if authority == "missing" else [selected]
    assessment = {
        "event_id": event["event_id"], "destination_candidate_route_id": selected["destination_candidate_route_id"],
        "destination_agent_contract_id": selected["destination_agent_contract_id"],
        "destination_named_agent": selected["destination_named_agent"], "assessment": "prequalified_same_agent",
        "prequalification_evidence_id": selected["qualification_evidence_id"],
    }
    trace["service_reroute_events"] = [event]
    trace["supported_effective_model"] = event["toModel"]
    trace["supported_effective_effort"] = None
    reroute_observation = next(item for item in trace["observations"] if item["field_path"] == "reroute.events")
    reroute_observation.update({
        "observation_state": "observed_value", "value": [event],
        "evidence_ref": "fixture://trace/reroute-events", "captured_at": "2026-07-17T04:01:00Z",
    })
    effective = next(item for item in trace["observations"] if item["field_path"] == "assignment.supported_effective_model")
    effective.update({
        "observation_state": "observed_value", "value": event["toModel"],
        "evidence_ref": "fixture://trace/effective-model", "captured_at": "2026-07-17T04:01:00Z",
    })
    if authority == "missing":
        trace["reroute_destination_assessments"], disposition = [], "hard_fail"
    else:
        if authority == "mismatched":
            assessment["destination_named_agent"] = "different-agent"
        trace["reroute_destination_assessments"] = [assessment]
        disposition = "non_scorable_rerouted" if authority == "owned_external" else "hard_fail"
    bundle["fixture_provenance"]["expected_dispositions"] = [{
        "execution_trace_id": trace["objective_binding"]["execution_trace_id"],
        "treatment_disposition": disposition,
    }]
    return declare_reroute_result(bundle)


def source_capture(manifest: dict, retrieved_at: str = "2026-07-16T00:00:00Z") -> list[dict]:
    captured = []
    for source in manifest["official_source_ledger"]:
        body = "\n".join(item["text"] for item in source["bounded_extracts"])
        prior = f"sha256:{source['body_sha256']}"
        current = capabilities.digest(body.encode())
        redirected = source["requested_url"] != source["canonical_url"]
        captured.append({
            "official_source_ledger_id": source["official_source_ledger_id"],
            "requested_url": source["requested_url"],
            "canonical_url": source["canonical_url"],
            "retrieved_at": retrieved_at,
            "status": "redirected" if redirected else "confirmed_current" if current == prior else "changed",
            "invalidated_claim_ids": [],
            "retrieved_body_b64": base64.b64encode(body.encode()).decode(),
            "bounded_extracts": copy.deepcopy(source["bounded_extracts"]),
        })
    return captured


def source_refreshes(manifest: dict, retrieved_at: str = "2026-07-16T00:00:00Z", *, synthetic: bool = False) -> list[dict]:
    return capabilities.normalize_source_refreshes(manifest, source_capture(manifest, retrieved_at), allow_synthetic_manifest=synthetic)


def canary_envelope() -> tuple[dict, dict]:
    contract_id = capabilities.digest({"executor": "fixture-v1"})
    implementation = capabilities.digest(b"fixture-executor")
    approval = {
        "executor_contract_id": contract_id,
        "contract_version": "1.0.0",
        "implementation_digest": implementation,
        "platform": "macos",
        "approval_evidence_digest": capabilities.digest(b"fixture-approval"),
    }
    result = {
        "snapshot_id": capabilities.digest({"snapshot": "fixture"}), "canonical_model_id": "model-a",
        "canonical_effort": "high", "attempt_index": 1, "timeout_seconds": 30,
        "combined_output_cap_bytes": 65536, "executor_contract_id": contract_id,
        "implementation_digest": implementation, "executor_result_digest": "",
        "contract_version": "1.0.0", "platform": "macos", "timeout_enforced": True, "output_cap_enforced": True,
        "process_tree_termination_state": "not_needed", "retry_count": 0, "exit_code": 0,
        "sentinel_observed": True, "terminal_class": "success",
        "availability_disposition": "available_for_pinned_environment", "evidence_digest": "",
    }
    result["evidence_digest"] = capabilities.digest(canary_evidence_bytes(result))
    result["executor_result_digest"] = capabilities.digest({key: value for key, value in result.items() if key not in {"executor_result_digest", "availability_disposition"}})
    return approval, result


def canary_evidence_bytes(result: dict) -> bytes:
    return capabilities.canonical_bytes({
        "schema_version": "1.0.0",
        "snapshot_id": result["snapshot_id"],
        "canonical_model_id": result["canonical_model_id"],
        "canonical_effort": result["canonical_effort"],
        "terminal_class": result["terminal_class"],
        "exit_code": result["exit_code"],
        "sentinel_observed": result["sentinel_observed"],
    }) + b"\n"


class CapabilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = load_json(FIXTURE_PATH)
        cls.manifest = load_json(MANIFEST_PATH)
        cls.identity = capabilities.build_client_identity(cls.fixture["client_identity"])

    def test_capability_facade_preserves_api_and_reviewable_boundaries(self) -> None:
        self.assertEqual(frozenset(capabilities.__all__), EXPECTED_CAPABILITY_PUBLIC_API)
        self.assertEqual(
            frozenset(name for name in vars(capabilities) if not name.startswith("_")),
            EXPECTED_CAPABILITY_PUBLIC_API,
        )
        self.assertNotIn("_delete_single_link_private_file", vars(capabilities))
        self.assertTrue(callable(capabilities.main))
        implementation_modules = [MODULE_PATH, *sorted(MODULE_PATH.parent.glob("codex_capability_*.py"))]
        self.assertEqual(len(implementation_modules), 12)
        for path in implementation_modules:
            with self.subTest(path=path.name):
                self.assertLessEqual(len(path.read_text(encoding="utf-8").splitlines()), 400)

    def observations(self, case: dict) -> list[dict]:
        return [
            capabilities.fixture_observation(surface, value, self.identity["client_identity_id"])
            for surface, value in case["surfaces"].items()
        ]

    def test_published_evidence_digest_summary_matches_freeze(self) -> None:
        freeze = load_json(PUBLISHED_FREEZE_PATH)
        summary = {}
        for line in CAPABILITY_EVIDENCE_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith("- ") and ": `sha256:" in line and line.endswith("`"):
                label, value = line[2:].split(": `", 1)
                summary[label] = value[:-1]
        expected = {
            "Candidate freeze": freeze["candidate_freeze_id"],
            "Runtime snapshot": freeze["runtime_capability_snapshot_id"],
            "Surface matrix": freeze["surface_matrix_id"],
            "Pinned client identity": freeze["client_identity_id"],
            "Current source-refresh set": freeze["source_refresh_set_digest"],
            "Complete tuple decisions": freeze["tuple_decision_digest"],
            "Treatment evidence set": freeze["treatment_evidence_digest"],
        }
        self.assertEqual({key: summary.get(key) for key in expected}, expected)

    def test_schema_negative_constraints_match_runtime(self) -> None:
        schema = load_json(ROOT / "specs/g56r-002-capability-discovery-telemetry/contracts/capability-freeze.schema.json")
        self.assertEqual(schema["properties"]["tuple_decisions"]["minItems"], 1)
        self.assertEqual(
            schema["dependentRequired"],
            {
                "treatment_contract_digest": ["treatment_evidence_digest"],
                "treatment_evidence_digest": ["treatment_contract_digest"],
            },
        )
        excluded_reasons = schema["$defs"]["excludedCandidate"]["properties"]["reasons"]
        self.assertEqual(excluded_reasons["minItems"], 1)
        effort_rule = schema["$defs"]["tupleDecision"]["properties"]["canonical_effort"]["oneOf"][0]
        self.assertIsNone(re.fullmatch(effort_rule["pattern"], "!!!"))
        canary_effort_rule = schema["$defs"]["canaryResult"]["properties"]["canonical_effort"]
        self.assertIsNone(re.fullmatch(canary_effort_rule["pattern"], "!!!"))
        observations_rule = schema["$defs"]["surfaceMatrix"]["properties"]["observations"]
        required_surfaces = {
            item["contains"]["properties"]["surface"]["const"]
            for item in observations_rule["allOf"]
            if item["minContains"] == item["maxContains"] == 1
        }
        self.assertEqual(required_surfaces, set(capabilities.SURFACES))
        published = load_json(PUBLISHED_FREEZE_PATH)
        invalid_effort = capability_contract._BoundDecisionSet(copy.deepcopy(published["tuple_decisions"]))
        invalid_effort[0]["canonical_effort"] = "!!!"
        with self.assertRaisesRegex(ValueError, "effort is invalid"):
            capabilities.validate_tuple_decisions(invalid_effort, require_snapshot=True)
        missing_reason = capability_contract._BoundDecisionSet(copy.deepcopy(published["tuple_decisions"]))
        missing_reason[0]["reasons"] = []
        with self.assertRaisesRegex(ValueError, "requires a reason"):
            capabilities.validate_tuple_decisions(missing_reason, require_snapshot=True)
        duplicate_surface = copy.deepcopy(published["surface_matrix"])
        duplicate_surface["observations"][1]["surface"] = "app_server"
        with self.assertRaises(ValueError):
            capabilities.validate_surface_matrix(duplicate_surface)

    def authority_tuples(self, case: dict) -> list[dict]:
        tuples = copy.deepcopy(case["source_tuples"])
        for item in tuples:
            instruction = capabilities.digest(b"fixture-instruction")
            item.update({
                "candidate_route_digest": capabilities.digest({"route": item["candidate_route_id"]}),
                "source_ref": "fixtures/fixture-agent.toml",
                "source_sha256": capabilities.digest(b"fixture-agent-source"),
                "instruction_sha256": instruction,
                "role_instruction_sha256": instruction,
                "agent_contract_digest": capabilities.digest(b"fixture-contract"),
                "official_source_bindings": [{
                    "official_source_ledger_id": "OPENAI-DOC-001",
                    "source_refresh_digest": capabilities.digest(b"fixture-source-refresh"),
                }],
                "effort_surface_bindings": [{
                    "effort_surface_record_id": "FIXTURE-ESR-001",
                    "effort_surface_record_digest": capabilities.digest(b"fixture-effort-record"),
                    "official_source_ledger_id": "OPENAI-DOC-001",
                    "source_refresh_digest": capabilities.digest(b"fixture-source-refresh"),
                }],
            })
        return capability_contract._AuthorityTupleSet(tuples)

    def test_current_manifest_and_effort_authority_are_strict(self) -> None:
        result = capabilities.validate_manifest(self.manifest)
        self.assertEqual(result["current_source_count"], 22)
        self.assertEqual(result["historical_active_count"], 0)
        self.assertEqual(result["effort_surface_count"], 5)
        self.assertIn("G56R-001-ESR-003", result["quarantined_effort_record_ids"])
        self.assertNotIn(",", result["authoritative_effort_tokens"])
        api_only = copy.deepcopy(self.manifest)
        api_only["effort_surface_records"][-1].update({"support_status": "documented", "documented_values": ["high"]})
        api_only["candidate_routes"][0]["effort_selector"]["requested_value"] = "high"
        refreshes = source_refreshes(api_only, synthetic=True)
        route = capabilities.candidate_tuples_from_manifest(api_only, refreshes, allow_synthetic_manifest=True)[0]
        self.assertFalse(route["source_admitted"])
        self.assertIn("effort_not_source_admitted", route["authority_reasons"])
        missing_owner = copy.deepcopy(self.manifest)
        first_owner = missing_owner["candidate_routes"][0]["agent_contract_id"]
        missing_owner["agent_contracts"] = [
            item for item in missing_owner["agent_contracts"]
            if item["agent_contract_id"] != first_owner
        ]
        with self.assertRaisesRegex(ValueError, "canonical G56R-001"):
            capabilities.validate_manifest(missing_owner)
        with self.assertRaisesRegex(ValueError, "agent-contract owners"):
            capabilities.validate_manifest(missing_owner, allow_synthetic_manifest=True)
        missing_routes = copy.deepcopy(self.manifest); missing_routes["candidate_routes"] = []
        with self.assertRaisesRegex(ValueError, "canonical G56R-001"):
            capabilities.validate_manifest(missing_routes)
        adverse_effort = copy.deepcopy(self.manifest)
        route_record = adverse_effort["candidate_routes"][0]
        effort_record = next(item for item in adverse_effort["effort_surface_records"] if item["effort_surface_record_id"] == "G56R-001-ESR-004")
        effort_record.update({"support_status": "documented", "documented_values": ["high"]})
        route_record["effort_selector"]["requested_value"] = "high"
        route_record["official_source_ledger_ids"].remove(effort_record["official_source_ledger_id"])
        adverse_capture = source_capture(adverse_effort)
        captured_source = next(item for item in adverse_capture if item["official_source_ledger_id"] == effort_record["official_source_ledger_id"])
        source_authority = next(item for item in adverse_effort["official_source_ledger"] if item["official_source_ledger_id"] == effort_record["official_source_ledger_id"])
        captured_source.update({"status": "inaccessible", "retrieved_body_b64": None, "bounded_extracts": [], "invalidated_claim_ids": source_authority["claim_bindings"]})
        adverse_refreshes = capabilities.normalize_source_refreshes(adverse_effort, adverse_capture, allow_synthetic_manifest=True)
        adverse_tuple = capabilities.candidate_tuples_from_manifest(adverse_effort, adverse_refreshes, allow_synthetic_manifest=True)[0]
        self.assertFalse(adverse_tuple["source_admitted"])
        self.assertIn("effort_source_not_admitted", adverse_tuple["authority_reasons"])
        scoped_manifest = copy.deepcopy(self.manifest)
        scoped_route = scoped_manifest["candidate_routes"][0]
        scoped_source = next(item for item in scoped_manifest["official_source_ledger"] if item["official_source_ledger_id"] == scoped_route["official_source_ledger_ids"][0])
        generic_claim = scoped_source["claim_bindings"][0]
        scoped_source["claim_bindings"].append(scoped_route["candidate_route_id"])
        scoped_source["extract_claim_dependencies"] = {
            item["extract_sha256"]: list(scoped_source["claim_bindings"])
            for item in scoped_source["bounded_extracts"]
        }
        with self.assertRaisesRegex(ValueError, "route-to-claim"):
            capabilities.validate_manifest(scoped_manifest, allow_synthetic_manifest=True)
        for route in scoped_manifest["candidate_routes"]:
            route["official_source_claim_dependencies"] = {
                source_id: (
                    [route["candidate_route_id"]] if route is scoped_route and source_id == scoped_source["official_source_ledger_id"]
                    else [generic_claim] if source_id == scoped_source["official_source_ledger_id"]
                    else list(next(
                        item for item in scoped_manifest["official_source_ledger"]
                        if item["official_source_ledger_id"] == source_id
                    )["claim_bindings"])
                )
                for source_id in route["official_source_ledger_ids"]
            }
        scoped_capture = source_capture(scoped_manifest)
        scoped_row = next(item for item in scoped_capture if item["official_source_ledger_id"] == scoped_source["official_source_ledger_id"])
        scoped_row["invalidated_claim_ids"] = [generic_claim]
        generic_only = capabilities.candidate_tuples_from_manifest(
            scoped_manifest,
            capabilities.normalize_source_refreshes(scoped_manifest, scoped_capture, allow_synthetic_manifest=True),
            allow_synthetic_manifest=True,
        )[0]
        self.assertNotIn("source_not_admitted", generic_only["authority_reasons"])
        scoped_row["invalidated_claim_ids"] = [scoped_route["candidate_route_id"]]
        route_specific = capabilities.candidate_tuples_from_manifest(
            scoped_manifest,
            capabilities.normalize_source_refreshes(scoped_manifest, scoped_capture, allow_synthetic_manifest=True),
            allow_synthetic_manifest=True,
        )[0]
        self.assertIn("source_not_admitted", route_specific["authority_reasons"])
        empty_bindings = copy.deepcopy(self.manifest)
        empty_bindings["official_source_ledger"][1]["claim_bindings"] = []
        with self.assertRaisesRegex(ValueError, "claim bindings"):
            capabilities.validate_manifest(empty_bindings, allow_synthetic_manifest=True)

    def test_canonical_json_refreshes_and_identity(self) -> None:
        self.assertEqual(capabilities.canonical_bytes({"b": 1, "a": 2}), b'{"a":2,"b":1}')
        self.assertFalse(hasattr(capabilities, "refreshes_from_manifest"))
        captured = source_capture(self.manifest)
        refreshes = capabilities.normalize_source_refreshes(self.manifest, captured)
        result = capabilities.validate_source_refreshes(self.manifest, refreshes)
        self.assertEqual(result["count"], 22)
        self.assertEqual(result["invalidated_claim_ids"], [])
        self.assertTrue(all(item["bounded_extracts"] for item in refreshes))
        self.assertTrue(all(item["retrieval_evidence_digest"].startswith("sha256:") for item in refreshes))
        self.assertEqual(len({item["source_capture_digest"] for item in refreshes}), 1)
        self.assertTrue(all("retrieved_body_b64" in item for item in refreshes))
        with tempfile.TemporaryDirectory() as tmp:
            private_root = Path(tmp); private_root.chmod(0o700)
            raw_root = private_root / "raw"; raw_root.mkdir(mode=0o700)
            capture_bytes = capabilities.canonical_bytes(captured) + b"\n"
            capture_digest = capabilities.digest(capture_bytes)
            capture_path = private_root / f"{capture_digest.removeprefix('sha256:')}.json"
            capture_path.write_bytes(capture_bytes); capture_path.chmod(0o600)
            normalized_path = private_root / "normalized.json"
            self.assertEqual(capabilities.main([
                "refresh-sources", "--manifest", str(MANIFEST_PATH),
                "--captured-refresh", str(capture_path),
                "--raw-evidence-root", str(raw_root), "--output", str(normalized_path),
            ]), 0)
            normalized = json.loads(normalized_path.read_text())
            self.assertEqual(normalized, capabilities.normalize_source_refreshes(
                self.manifest, captured, source_capture_digest=capture_digest,
            ))
            self.assertEqual(
                (raw_root / f"{capture_digest.removeprefix('sha256:')}.json").read_bytes(), capture_bytes,
            )
        self.assertEqual(
            self.identity["client_identity_id"],
            capabilities.digest({k: v for k, v in self.identity.items() if k != "client_identity_id"}),
        )
        absolute_client_path = "/" + "Users/private/client"
        for field, value in (("reported_version", absolute_client_path), ("build_identifier", "https://example.invalid/build"), ("build_identifier", "secret\nvalue")):
            with self.assertRaises(ValueError):
                capabilities.build_client_identity({**self.fixture["client_identity"], field: value})
        with self.assertRaisesRegex(ValueError, "closed v1 shape"):
            capabilities.build_client_identity({**self.fixture["client_identity"], "authorization": "sensitive"})
        unrelated_body = copy.deepcopy(captured); unrelated_body[0]["retrieved_body_b64"] = base64.b64encode(b"unrelated").decode()
        with self.assertRaisesRegex(ValueError, "bounded extract"):
            capabilities.normalize_source_refreshes(self.manifest, unrelated_body)
        bad = copy.deepcopy(captured); bad[0]["canonical_url"] = "https://example.invalid/not-authority"
        with self.assertRaisesRegex(ValueError, "identity or URL"):
            capabilities.normalize_source_refreshes(self.manifest, bad)
        insecure = copy.deepcopy(captured); insecure[0]["canonical_url"] = "http://openai.com/unrelated"
        with self.assertRaisesRegex(ValueError, "identity or URL"):
            capabilities.normalize_source_refreshes(self.manifest, insecure)
        approved_redirect = copy.deepcopy(captured); approved_redirect[0].update({"canonical_url": "https://platform.openai.com/docs/moved-source", "status": "redirected"})
        with self.assertRaisesRegex(ValueError, "canonical URL change"):
            capabilities.normalize_source_refreshes(self.manifest, approved_redirect)
        approved_redirect[0]["invalidated_claim_ids"] = self.manifest["official_source_ledger"][0]["claim_bindings"]
        redirected_refreshes = capabilities.normalize_source_refreshes(self.manifest, approved_redirect)
        self.assertEqual(redirected_refreshes[0]["canonical_url"], approved_redirect[0]["canonical_url"])
        self.assertEqual(redirected_refreshes[0]["status"], "redirected")
        redirected_material = copy.deepcopy(approved_redirect)
        redirected_material[0]["bounded_extracts"][0]["text"] += " Updated."
        redirected_material[0]["bounded_extracts"][0]["extract_sha256"] = capabilities.digest(redirected_material[0]["bounded_extracts"][0]["text"].encode()).removeprefix("sha256:")
        redirected_body = "\n".join(item["text"] for item in redirected_material[0]["bounded_extracts"]).encode()
        redirected_material[0].update({
            "retrieved_body_b64": base64.b64encode(redirected_body).decode(),
            "invalidated_claim_ids": self.manifest["official_source_ledger"][0]["claim_bindings"],
        })
        self.assertEqual(capabilities.normalize_source_refreshes(self.manifest, redirected_material)[0]["status"], "redirected")
        redirect_only_manifest = copy.deepcopy(self.manifest)
        redirect_only_source = redirect_only_manifest["official_source_ledger"][0]
        redirect_only_body = "\n".join(item["text"] for item in redirect_only_source["bounded_extracts"]).encode()
        redirect_only_source["body_sha256"] = capabilities.digest(redirect_only_body).removeprefix("sha256:")
        redirect_only_capture = source_capture(redirect_only_manifest)
        redirect_only_capture[0].update({"canonical_url": "https://platform.openai.com/docs/moved-source", "status": "redirected"})
        redirect_only_capture[0]["invalidated_claim_ids"] = redirect_only_source["claim_bindings"]
        redirect_only = capabilities.normalize_source_refreshes(redirect_only_manifest, redirect_only_capture, allow_synthetic_manifest=True)
        self.assertEqual(redirect_only[0]["status"], "redirected")
        canonical_drift = copy.deepcopy(captured)
        canonical_drift[0].update({
            "canonical_url": self.manifest["official_source_ledger"][0]["requested_url"],
            "status": "changed",
        })
        with self.assertRaisesRegex(ValueError, "canonical URL change"):
            capabilities.normalize_source_refreshes(self.manifest, canonical_drift)
        canonical_drift[0]["invalidated_claim_ids"] = self.manifest["official_source_ledger"][0]["claim_bindings"]
        drifted_refreshes = capabilities.normalize_source_refreshes(self.manifest, canonical_drift)
        self.assertEqual(drifted_refreshes[0]["status"], "changed")
        self.assertEqual(
            capabilities.validate_source_refreshes(self.manifest, drifted_refreshes)["invalidated_claim_ids"],
            self.manifest["official_source_ledger"][0]["claim_bindings"],
        )
        prefix_attack = copy.deepcopy(captured); prefix_attack[0]["canonical_url"] = "https://platform.openai.com/docs-evil"
        with self.assertRaisesRegex(ValueError, "identity or URL"):
            capabilities.normalize_source_refreshes(self.manifest, prefix_attack)
        for unapproved_url in (
            "https://unapproved.openai.com/docs/moved-source",
            "https://chatgpt.com/codex/moved-source",
            "https://openai.com/docs/moved-source",
            "https://user" + chr(64) + "platform.openai.com/docs/moved-source",
            "https://platform.openai.com:443/docs/moved-source",
            "https://platform.openai.com:bad/docs/moved-source",
            "https://platform.openai.com/docs/../outside",
            "https://platform.openai.com/docs/%2e%2e/outside",
            "https://platform.openai.com/docs/%2Foutside",
            "https://platform.openai.com/docs//outside",
            "https://platform.openai.com/docs?",
            "https://platform.openai.com/docs#",
            "https://platform.openai.com/docs/moved-source?token=fixture-sensitive",
            "https://platform.openai.com/docs/moved-source#private-fragment",
            "https://platform.openai.com/docs\n",
            "https://platform.openai.com/\tdocs",
            " https://platform.openai.com/docs",
        ):
            unapproved = copy.deepcopy(captured)
            unapproved[0].update({"canonical_url": unapproved_url, "status": "redirected"})
            with self.subTest(unapproved_url=unapproved_url), self.assertRaisesRegex(ValueError, "identity or URL"):
                capabilities.normalize_source_refreshes(self.manifest, unapproved)
        invalid_time = copy.deepcopy(captured); invalid_time[0]["retrieved_at"] = "2026-07-16 00:00:00Z"
        with self.assertRaisesRegex(ValueError, "status or timestamp"):
            capabilities.normalize_source_refreshes(self.manifest, invalid_time)
        adverse = copy.deepcopy(captured); adverse[0].update({"status": "inaccessible", "retrieved_body_b64": None, "bounded_extracts": [], "invalidated_claim_ids": []})
        with self.assertRaisesRegex(ValueError, "invalidate every bound claim"):
            capabilities.normalize_source_refreshes(self.manifest, adverse)
        partial_change = copy.deepcopy(captured)
        changed_source = partial_change[-1]
        changed_source["bounded_extracts"][0]["text"] += " Updated."
        changed_source["bounded_extracts"][0]["extract_sha256"] = capabilities.digest(changed_source["bounded_extracts"][0]["text"].encode()).removeprefix("sha256:")
        changed_body = "\n".join(item["text"] for item in changed_source["bounded_extracts"]).encode()
        changed_source.update({
            "retrieved_body_b64": base64.b64encode(changed_body).decode(),
            "status": "changed",
            "invalidated_claim_ids": ["G56R-V3-PROMPT_ABLATION"],
        })
        wrong_claim = copy.deepcopy(partial_change)
        wrong_claim[-1]["invalidated_claim_ids"] = ["G56R-V3-PROMPT_GUIDANCE"]
        with self.assertRaisesRegex(ValueError, "dependent claims"):
            capabilities.normalize_source_refreshes(self.manifest, wrong_claim)
        partial_refreshes = capabilities.normalize_source_refreshes(self.manifest, partial_change)
        self.assertEqual(partial_refreshes[-1]["invalidated_claim_ids"], changed_source["invalidated_claim_ids"])
        unknown_normalization = copy.deepcopy(captured)
        unknown_normalization[0]["bounded_extracts"][0]["normalization"] = "unreviewed-normalization"
        with self.assertRaisesRegex(ValueError, "retrieved body"):
            capabilities.normalize_source_refreshes(self.manifest, unknown_normalization)
        forged = copy.deepcopy(refreshes); forged_body = b"unrelated body"
        forged[0]["retrieved_body_b64"] = base64.b64encode(forged_body).decode()
        forged[0]["body_digest"] = capabilities.digest(forged_body)
        forged[0]["retrieval_evidence_digest"] = capabilities.digest({
            "canonical_url": forged[0]["canonical_url"], "retrieved_at": forged[0]["retrieved_at"],
            "body_digest": forged[0]["body_digest"], "bounded_extracts": forged[0]["bounded_extracts"],
        })
        with self.assertRaisesRegex(ValueError, "bounded extract"):
            capabilities.validate_source_refreshes(self.manifest, forged)
        unknown_status = copy.deepcopy(refreshes); unknown_status[0]["status"] = "invented"
        with self.assertRaisesRegex(ValueError, "status or invalidation"):
            capabilities.validate_source_refreshes(self.manifest, unknown_status)
        invalidation_drift = copy.deepcopy(refreshes); invalidation_drift[0]["invalidated_claim_ids"] = ["OUT-OF-SCOPE"]
        with self.assertRaisesRegex(ValueError, "status or invalidation"):
            capabilities.validate_source_refreshes(self.manifest, invalidation_drift)
        inconsistent_status = copy.deepcopy(refreshes)
        changed_index = next(index for index, item in enumerate(inconsistent_status) if item["status"] == "changed")
        inconsistent_status[changed_index]["status"] = "confirmed_current"
        with self.assertRaisesRegex(ValueError, "inconsistent with captured evidence"):
            capabilities.validate_source_refreshes(self.manifest, inconsistent_status)
        missing_body = copy.deepcopy(refreshes); missing_body[0]["retrieved_body_b64"] = None; missing_body[0]["body_digest"] = None
        with self.assertRaisesRegex(ValueError, "require a retrieved body"):
            capabilities.validate_source_refreshes(self.manifest, missing_body)
        script_only = copy.deepcopy(captured)
        script_body = f"<html><script>{script_only[0]['bounded_extracts'][0]['text']}</script></html>".encode()
        script_only[0]["retrieved_body_b64"] = base64.b64encode(script_body).decode()
        with self.assertRaisesRegex(ValueError, "bounded extract"):
            capabilities.normalize_source_refreshes(self.manifest, script_only)
        malformed_hidden = copy.deepcopy(captured)
        hidden_body = f"<template></head>{malformed_hidden[0]['bounded_extracts'][0]['text']}</template>".encode()
        malformed_hidden[0]["retrieved_body_b64"] = base64.b64encode(hidden_body).decode()
        with self.assertRaisesRegex(ValueError, "malformed hidden markup"):
            capabilities.normalize_source_refreshes(self.manifest, malformed_hidden)
        for opening in ("<script ", "<template ", "<!-- "):
            incomplete_hidden = copy.deepcopy(captured)
            incomplete_body = f"{opening}{incomplete_hidden[0]['bounded_extracts'][0]['text']}".encode()
            incomplete_hidden[0]["retrieved_body_b64"] = base64.b64encode(incomplete_body).decode()
            with self.subTest(opening=opening), self.assertRaisesRegex(ValueError, "malformed hidden markup"):
                capabilities.normalize_source_refreshes(self.manifest, incomplete_hidden)

    def test_surface_cases_preserve_dispositions(self) -> None:
        for case in self.fixture["surface_cases"]:
            with self.subTest(case=case["case_id"]):
                observations = self.observations(case)
                options = {"aliases": case.get("aliases", {})}
                if "expected_integrity_digest" in case:
                    options["expected_integrity_digest"] = case["expected_integrity_digest"]
                matrix, decisions = capabilities.evaluate_surface_matrix(
                    observations, self.authority_tuples(case), **options,
                )
                self.assertEqual(capabilities.validate_surface_matrix(matrix), matrix)
                self.assertEqual(matrix["validity"], case["expected_validity"])
                if case["expected_decision"] == "none":
                    self.assertEqual(decisions, [])
                else:
                    self.assertTrue(decisions)
                    self.assertEqual(decisions[0]["decision"], case["expected_decision"])
                    self.assertIn("collection_evidence_non_authoritative", decisions[0]["reasons"])
                if case["case_id"] == "hidden_without_source_admission":
                    self.assertEqual(len(decisions), 1)
                    self.assertFalse(decisions[0]["source_admitted"])
                    self.assertIn("source_not_admitted", decisions[0]["reasons"])
                if case["case_id"] == "surface_disagreement":
                    self.assertEqual(len(matrix["disagreements"]), 1)
                    self.assertEqual(set(matrix["disagreements"][0]["surface_values"]), {"app_server", "cli", "interactive_picker"})
                if case["case_id"] == "hidden_picker_omission":
                    self.assertEqual(decisions[0]["surface_disposition"], "agreed")
                    self.assertEqual(decisions[0]["reasons"], ["collection_evidence_non_authoritative"])
                if case["case_id"] == "hidden_state_disagreement":
                    self.assertEqual(decisions[0]["surface_disposition"], "disagreed")
                    self.assertIn("hidden_state_disagreement", decisions[0]["reasons"])
                    self.assertEqual(matrix["disagreements"][0]["disagreement_class"], "hidden_state")
        agreed_case = next(item for item in self.fixture["surface_cases"] if item["case_id"] == "agreed")
        agreed_matrix, _ = capabilities.evaluate_surface_matrix(self.observations(agreed_case), self.authority_tuples(agreed_case))
        for malformed_digest in (None, "", "not-a-digest"):
            with self.subTest(malformed_digest=malformed_digest), self.assertRaisesRegex(ValueError, "sha256 digest"):
                capabilities.evaluate_surface_matrix(
                    self.observations(agreed_case), self.authority_tuples(agreed_case),
                    expected_integrity_digest=malformed_digest,
                )
            malformed_matrix = copy.deepcopy(agreed_matrix)
            malformed_matrix["aggregate_integrity_digest"] = malformed_digest
            malformed_matrix.update({"validity": "invalid", "invalidity_reasons": ["aggregate_hash_mismatch"]})
            malformed_matrix["surface_matrix_id"] = capabilities.digest({
                key: value for key, value in malformed_matrix.items() if key != "surface_matrix_id"
            })
            with self.assertRaisesRegex(ValueError, "sha256 digest"):
                capabilities.validate_surface_matrix(malformed_matrix)
        forged_invalidity = copy.deepcopy(agreed_matrix)
        forged_invalidity.update({"validity": "invalid", "invalidity_reasons": ["aggregate_hash_mismatch"]})
        forged_invalidity["surface_matrix_id"] = capabilities.digest({key: value for key, value in forged_invalidity.items() if key != "surface_matrix_id"})
        with self.assertRaisesRegex(ValueError, "validity is inconsistent"):
            capabilities.validate_surface_matrix(forged_invalidity)
        unequal_clients = self.observations(agreed_case)
        unequal_clients[0]["client_identity_id"] = capabilities.digest(b"different-client")
        unequal_clients[0]["surface_observation_id"] = capabilities.digest({
            key: value for key, value in unequal_clients[0].items() if key != "surface_observation_id"
        })
        unequal_matrix, _ = capabilities.evaluate_surface_matrix(unequal_clients, self.authority_tuples(agreed_case))
        self.assertEqual(unequal_matrix["invalidity_reasons"], ["unprovable_shared_client_identity"])
        self.assertEqual(capabilities.validate_surface_matrix(unequal_matrix), unequal_matrix)
        disagreement_case = next(item for item in self.fixture["surface_cases"] if item["case_id"] == "surface_disagreement")
        disagreement_matrix, _ = capabilities.evaluate_surface_matrix(self.observations(disagreement_case), self.authority_tuples(disagreement_case))
        wrong_class = copy.deepcopy(disagreement_matrix)
        wrong_class["disagreements"][0]["disagreement_class"] = "hidden_state"
        wrong_class["surface_matrix_id"] = capabilities.digest({key: value for key, value in wrong_class.items() if key != "surface_matrix_id"})
        with self.assertRaisesRegex(ValueError, "inconsistent with observed values"):
            capabilities.validate_surface_matrix(wrong_class)
        missing_disagreement = copy.deepcopy(disagreement_matrix)
        missing_disagreement["disagreements"] = []
        missing_disagreement["surface_matrix_id"] = capabilities.digest({key: value for key, value in missing_disagreement.items() if key != "surface_matrix_id"})
        with self.assertRaisesRegex(ValueError, "inventory is incomplete"):
            capabilities.validate_surface_matrix(missing_disagreement)
        partial_observations = self.observations(disagreement_case)
        partial_observations[0]["completeness_state"] = "partial"
        partial_observations[0]["surface_observation_id"] = capabilities.digest({
            key: partial_observations[0][key]
            for key in partial_observations[0]
            if key != "surface_observation_id"
        })
        partial_matrix, partial_decisions = capabilities.evaluate_surface_matrix(
            partial_observations,
            self.authority_tuples(disagreement_case),
        )
        self.assertEqual(capabilities.validate_surface_matrix(partial_matrix), partial_matrix)
        self.assertEqual(len(partial_matrix["disagreements"]), 1)
        self.assertEqual(partial_decisions[0]["surface_disposition"], "disagreed")
        self.assertFalse(capability_freeze._documented_discovery_unavailable(partial_observations))
        binding = partial_observations[0]["repository_binding"]
        work_item = partial_observations[0]["work_item"]
        unavailable_observations = [
            capabilities.unknown_observation(surface, self.identity["client_identity_id"], binding, work_item)
            for surface in capabilities.SURFACES
        ]
        self.assertTrue(capability_freeze._documented_discovery_unavailable(unavailable_observations))
        shared_tuples = self.authority_tuples(disagreement_case)
        shared_route = copy.deepcopy(shared_tuples[0])
        shared_route.update({
            "candidate_route_id": "FIXTURE-ROUTE-SHARED",
            "agent_contract_id": "FIXTURE-AGENT-SHARED",
            "candidate_route_digest": capabilities.digest({"route": "FIXTURE-ROUTE-SHARED"}),
        })
        shared_tuples.append(shared_route)
        shared_matrix, shared_decisions = capabilities.evaluate_surface_matrix(
            self.observations(disagreement_case),
            shared_tuples,
        )
        self.assertEqual(capabilities.validate_surface_matrix(shared_matrix), shared_matrix)
        self.assertEqual(len(shared_matrix["disagreements"]), 1)
        self.assertEqual(len(shared_decisions), 2)
        self.assertEqual(len({item["disagreement_digest"] for item in shared_decisions}), 1)
        wrong_reference = copy.deepcopy(disagreement_matrix)
        wrong_reference["disagreements"][0]["evidence_refs"]["cli"] = wrong_reference["disagreements"][0]["evidence_refs"]["app_server"]
        wrong_reference["surface_matrix_id"] = capabilities.digest({key: value for key, value in wrong_reference.items() if key != "surface_matrix_id"})
        with self.assertRaisesRegex(ValueError, "inconsistent with observed values"):
            capabilities.validate_surface_matrix(wrong_reference)
        agreed = next(item for item in self.fixture["surface_cases"] if item["case_id"] == "agreed")
        with self.assertRaisesRegex(ValueError, "alias authority"):
            capabilities.evaluate_surface_matrix(
                self.observations(agreed), self.authority_tuples(agreed),
                aliases={"unrelated-display": "model-a"},
            )
        alias_case = next(item for item in self.fixture["surface_cases"] if item["case_id"] == "one_to_one_alias")
        with self.assertRaisesRegex(ValueError, "alias authority evidence"):
            capabilities.evaluate_surface_matrix(
                self.observations(alias_case), self.authority_tuples(alias_case),
                aliases={"Model A Display": {"canonical_model_id": "model-b", "authority_kind": "machine_readable_identifier", "authority_surface": "cli"}},
            )
        conflicting_alias_observations = self.observations(alias_case)
        conflicting_entry = conflicting_alias_observations[0]["entries"][0]
        conflicting_entry.update({
            "model": "Model A Display", "raw_label": "Model A Display", "machine_id": "model-b",
        })
        conflicting_alias_observations[0]["surface_observation_id"] = capabilities.digest({
            key: value for key, value in conflicting_alias_observations[0].items() if key != "surface_observation_id"
        })
        conflicting_matrix, conflicting_decisions = capabilities.evaluate_surface_matrix(
            conflicting_alias_observations, self.authority_tuples(alias_case), aliases=alias_case["aliases"],
        )
        self.assertEqual(conflicting_matrix["invalidity_reasons"], ["ambiguous_or_duplicate_normalization_key"])
        self.assertEqual(conflicting_decisions[0]["surface_evidence"]["app_server"]["matching_entry"], None)
        self.assertIn("matrix_invalid", conflicting_decisions[0]["reasons"])
        self.assertEqual(capabilities.validate_surface_matrix(conflicting_matrix), conflicting_matrix)
        observations = self.observations(agreed); baseline = None
        for permutation in itertools.permutations(observations):
            matrix, decisions = capabilities.evaluate_surface_matrix(list(permutation), self.authority_tuples(agreed))
            current = capabilities.canonical_bytes([matrix, decisions])
            baseline = current if baseline is None else baseline
            self.assertEqual(current, baseline)
        arbitrary = self.observations(agreed)
        arbitrary[0]["collection_method_id"] = "unreviewed-live-v999"
        arbitrary[0]["method_inputs_digest"] = capabilities.digest({"arbitrary": True})
        arbitrary[0]["surface_observation_id"] = capabilities.digest({key: arbitrary[0][key] for key in arbitrary[0] if key != "surface_observation_id"})
        with self.assertRaisesRegex(ValueError, "closed registry"):
            capabilities.evaluate_surface_matrix(arbitrary, self.authority_tuples(agreed))
        self.assertEqual(capabilities.APPROVED_LIVE_COLLECTION_METHODS, ())

    def test_freeze_ids_bind_all_decisions_and_allow_zero_eligible(self) -> None:
        case = next(item for item in self.fixture["surface_cases"] if item["case_id"] == "zero_eligible")
        refreshes = source_refreshes(self.manifest)
        source_tuples = capabilities.candidate_tuples_from_manifest(self.manifest, refreshes)
        self.assertEqual(len(source_tuples), 23)
        self.assertTrue(all(not item["source_admitted"] for item in source_tuples))
        self.assertTrue(all(item["effort"] is None for item in source_tuples))
        matrix, decisions = capabilities.evaluate_surface_matrix(self.observations(case), source_tuples)
        freeze = capabilities.build_freeze(
            self.identity, refreshes, matrix, decisions, "2026-07-16T00:00:00Z",
            manifest=self.manifest,
        )
        self.assertEqual(capabilities.validate_freeze(freeze, self.manifest), freeze)
        self.assertEqual(freeze["telemetry_profile_id"], capabilities.PENDING_TELEMETRY_PROFILE_ID)
        leaky_identity = copy.deepcopy(freeze)
        leaky_identity["client_identity"]["authorization"] = "sensitive"
        leaky_identity["candidate_freeze_id"] = capabilities.digest(capability_freeze._freeze_identity_payload(leaky_identity))
        with self.assertRaisesRegex(ValueError, "closed v1 shape"):
            capabilities.validate_freeze(leaky_identity, self.manifest)
        forged_telemetry = copy.deepcopy(freeze)
        forged_telemetry["telemetry_profile_id"] = capabilities.digest(b"forged-telemetry")
        forged_telemetry["candidate_freeze_id"] = capabilities.digest(capability_freeze._freeze_identity_payload(forged_telemetry))
        with self.assertRaisesRegex(ValueError, "treatment-aware freeze validation"):
            capabilities.validate_freeze(forged_telemetry, self.manifest)
        self.assertEqual(len(freeze["tuple_decisions"]), 23)
        self.assertEqual([d for d in freeze["tuple_decisions"] if d["decision"] == "included"], [])
        self.assertEqual(freeze["runtime_capability_snapshot"]["controlled_repository_snapshot"], matrix["observations"][0]["repository_binding"])
        self.assertEqual(freeze["runtime_capability_snapshot"]["work_item"], {"kind": "fixture", "id": "G56R-002-SYNTHETIC"})
        self.assertEqual(freeze["runtime_capability_snapshot_id"], freeze["runtime_capability_snapshot"]["runtime_capability_snapshot_id"])
        self.assertTrue(all(item["runtime_capability_snapshot_id"] == freeze["runtime_capability_snapshot_id"] for item in freeze["tuple_decisions"]))
        self.assertTrue(all(item["official_source_bindings"] for item in freeze["tuple_decisions"]))
        self.assertTrue(all(item["agent_contract_digest"].startswith("sha256:") for item in freeze["tuple_decisions"]))
        successor = capabilities.build_freeze(
            self.identity, refreshes, matrix, decisions, "2026-07-16T00:00:01Z",
            manifest=self.manifest, predecessor=freeze,
        )
        self.assertNotEqual(successor["candidate_freeze_id"], freeze["candidate_freeze_id"])
        self.assertEqual(successor["supersedes_candidate_freeze_id"], freeze["candidate_freeze_id"])
        self.assertEqual(successor["runtime_capability_snapshot_id"], freeze["runtime_capability_snapshot_id"])
        self.assertEqual(capabilities.validate_freeze(successor, self.manifest, predecessor=freeze), successor)
        with self.assertRaisesRegex(ValueError, "requires its validated predecessor"):
            capabilities.validate_freeze(successor, self.manifest)
        with self.assertRaisesRegex(ValueError, "precedes captured evidence"):
            capabilities.build_freeze(self.identity, refreshes, matrix, decisions, "2026-07-15T23:59:59Z", manifest=self.manifest)
        with self.assertRaisesRegex(ValueError, "publication timestamp"):
            capabilities.build_freeze(self.identity, refreshes, matrix, decisions, "not-a-date", manifest=self.manifest)
        changed_contract = copy.deepcopy(self.manifest)
        changed_contract["agent_contracts"][0]["safety_boundary"] += " changed"
        with self.assertRaisesRegex(ValueError, "canonical G56R-001"):
            capabilities.build_freeze(self.identity, refreshes, matrix, decisions, "2026-07-16T00:00:00Z", manifest=changed_contract)
        wrong_identity = capabilities.build_client_identity({**self.fixture["client_identity"], "build_identifier": "fixture-build-002"})
        with self.assertRaisesRegex(ValueError, "client identity"):
            capabilities.build_freeze(wrong_identity, refreshes, matrix, decisions, "2026-07-16T00:00:00Z", manifest=self.manifest)
        tampered = copy.deepcopy(matrix); tampered["surface_matrix_id"] = capabilities.digest(b"tampered")
        with self.assertRaisesRegex(ValueError, "matrix identity"):
            capabilities.build_freeze(self.identity, refreshes, tampered, decisions, "2026-07-16T00:00:00Z", manifest=self.manifest)
        invented = [{"candidate_route_id": "RUNTIME-INVENTED", "agent_contract_id": "AGENT-INVENTED", "named_agent": "fixture-agent", "model": "model-invented", "effort": "high", "source_admitted": True, "authority_reasons": []}]
        with self.assertRaisesRegex(ValueError, "manifest-bound tuple"):
            capabilities.evaluate_surface_matrix(self.observations(next(item for item in self.fixture["surface_cases"] if item["case_id"] == "agreed")), invented)
        forged = [{"candidate_route_id": "RUNTIME-INVENTED", "agent_contract_id": "AGENT-INVENTED", "named_agent": "fixture-agent", "canonical_model_id": "model-invented", "canonical_effort": "high", "source_admitted": True, "availability_disposition": "supported", "surface_disposition": "agreed", "decision": "included", "reasons": []}]
        with self.assertRaisesRegex(ValueError, "manifest-bound authority"):
            capabilities.build_freeze(self.identity, refreshes, matrix, forged, "2026-07-16T00:00:00Z", manifest=self.manifest)
        with self.assertRaisesRegex(ValueError, "closed v1 shape"):
            capabilities.build_freeze(self.identity, refreshes, matrix, capability_contract._BoundDecisionSet(forged), "2026-07-16T00:00:00Z", manifest=self.manifest)
        mutated = capability_contract._BoundDecisionSet(copy.deepcopy(decisions))
        mutated[0].update({
            "source_admitted": True,
            "availability_disposition": "supported",
            "surface_disposition": "agreed",
            "decision": "included",
            "reasons": [],
        })
        with self.assertRaisesRegex(ValueError, "manifest-backed matrix evaluation"):
            capabilities.build_freeze(self.identity, refreshes, matrix, mutated, "2026-07-16T00:00:00Z", manifest=self.manifest)
        for field, replacement in (
            ("included_candidate_route_ids", ["FORGED"]),
            ("current_ledger_digest", capabilities.digest(b"forged")),
            ("client_identity_id", capabilities.digest(b"forged-client")),
            ("source_refresh_set_digest", capabilities.digest(b"forged-refresh")),
            ("surface_matrix_id", capabilities.digest(b"forged-matrix")),
            ("candidate_freeze_id", capabilities.digest(b"forged")),
        ):
            tampered_freeze = copy.deepcopy(freeze); tampered_freeze[field] = replacement
            with self.assertRaises(ValueError): capabilities.validate_freeze(tampered_freeze, self.manifest)
        approval, _ = canary_envelope()
        self_approved_freeze = copy.deepcopy(freeze)
        self_approved_freeze["approved_canary_executors"] = [approval]
        self_approved_freeze["candidate_freeze_id"] = capabilities.digest(capability_freeze._freeze_identity_payload(self_approved_freeze))
        with self.assertRaisesRegex(ValueError, "repository-owned allowlist"):
            capabilities.validate_freeze(self_approved_freeze, self.manifest)

    def test_freeze_cli_round_trips_alias_authority(self) -> None:
        alias_case = next(item for item in self.fixture["surface_cases"] if item["case_id"] == "one_to_one_alias")
        observations = self.observations(alias_case)

        with tempfile.TemporaryDirectory() as tmp:
            private_root = Path(tmp)
            private_root.chmod(0o700)
            raw_root = private_root / "raw"
            raw_root.mkdir(mode=0o700)
            captured = source_capture(self.manifest)
            capture_bytes = capabilities.canonical_bytes(captured) + b"\n"
            capture_digest, _ = capabilities.materialize_source_capture(raw_root, ROOT, capture_bytes)
            refreshes = capabilities.normalize_source_refreshes(
                self.manifest, captured, source_capture_digest=capture_digest,
            )

            def write_input(name: str, value: object) -> Path:
                path = private_root / name
                path.write_bytes(capabilities.canonical_bytes(value) + b"\n")
                path.chmod(0o600)
                return path

            refresh_path = write_input("source-refresh.json", refreshes)
            identity_path = write_input("client-identity.json", self.identity)
            aliases_path = write_input("aliases.json", alias_case["aliases"])
            observation_paths = {
                observation["surface"]: write_input(f"{observation['surface']}.json", observation)
                for observation in observations
            }
            freeze_path = private_root / "candidate-freeze.json"

            self.assertEqual(capabilities.main([
                "freeze",
                "--manifest", str(MANIFEST_PATH),
                "--source-refresh", str(refresh_path),
                "--client-identity", str(identity_path),
                "--app-server", str(observation_paths["app_server"]),
                "--cli", str(observation_paths["cli"]),
                "--interactive-picker", str(observation_paths["interactive_picker"]),
                "--raw-evidence-root", str(raw_root),
                "--aliases", str(aliases_path),
                "--published-at", "2026-07-16T00:00:00Z",
                "--output", str(freeze_path),
            ]), 0)

            freeze = load_json(freeze_path)
            normalization = freeze["surface_matrix"]["normalization_map"]
            self.assertEqual(normalization["Model A Display"]["canonical_model_id"], "model-a")
            self.assertEqual(normalization["Model A Display"]["authority_surface"], "cli")
            self.assertEqual(normalization["Model A Display"]["client_identity_id"], self.identity["client_identity_id"])
            self.assertEqual(
                normalization["Model A Display"]["authority_evidence_ref"],
                next(item for item in observations if item["surface"] == "cli")["raw_evidence_ref"],
            )
            decision_models = {item["canonical_model_id"] for item in freeze["tuple_decisions"]}
            self.assertIn("model-a", decision_models)
            self.assertNotIn("Model A Display", decision_models)
            self.assertEqual(capabilities.validate_freeze(freeze, self.manifest), freeze)
            self.assertEqual(capabilities.main([
                "validate-freeze",
                "--manifest", str(MANIFEST_PATH),
                "--freeze", str(freeze_path),
            ]), 0)

    def test_canary_is_injected_bounded_and_default_denied(self) -> None:
        approval, result = canary_envelope()
        evidence_bytes = canary_evidence_bytes(result)
        denied = capabilities.validate_canary_result(result, evidence_bytes=evidence_bytes)
        self.assertEqual(denied["availability_disposition"], "unknown")
        allowed = capabilities.validate_canary_result(result, [approval], evidence_bytes=evidence_bytes)
        self.assertEqual(allowed["availability_disposition"], "available_for_pinned_environment")
        with self.assertRaisesRegex(ValueError, "requires its content-addressed"):
            capabilities.validate_canary_result(result, [approval], evidence_bytes=None)
        with self.assertRaisesRegex(ValueError, "do not match evidence_digest"):
            capabilities.validate_canary_result(result, [approval], evidence_bytes=b"{}\n")
        with self.assertRaisesRegex(ValueError, "only one canary"):
            capabilities.validate_canary_results([result, result], [approval])
        canary_predecessor = {"canary_results": [result]}
        retained_history = capability_freeze._successor_canary_results(canary_predecessor, True)
        self.assertEqual(retained_history, [result])
        self.assertIsNot(retained_history, canary_predecessor["canary_results"])
        capability_freeze._validate_same_snapshot_canary_history(canary_predecessor, retained_history, True)
        with self.assertRaisesRegex(ValueError, "cannot drop or rewrite"):
            capability_freeze._validate_same_snapshot_canary_history(canary_predecessor, [], True)
        rewritten = copy.deepcopy(result); rewritten["availability_disposition"] = "unknown"
        with self.assertRaisesRegex(ValueError, "cannot drop or rewrite"):
            capability_freeze._validate_same_snapshot_canary_history(canary_predecessor, [rewritten], True)
        self.assertEqual(capability_freeze._successor_canary_results(canary_predecessor, False), [])
        with self.assertRaisesRegex(ValueError, "only one canary"):
            capabilities.validate_canary_results([*retained_history, result], [approval])
        replayed = {**result, "canonical_model_id": "model-b"}
        with self.assertRaisesRegex(ValueError, "cannot be replayed"):
            capabilities.validate_canary_results([result, replayed], [approval])
        mismatched = {**result, "canonical_model_id": "model-b"}
        with self.assertRaisesRegex(ValueError, "does not bind"):
            capabilities.validate_canary_result(mismatched, [approval], evidence_bytes=evidence_bytes)
        boolean_bound = {**result, "attempt_index": True}
        boolean_bound["executor_result_digest"] = capabilities.digest({key: value for key, value in boolean_bound.items() if key not in {"executor_result_digest", "availability_disposition"}})
        with self.assertRaisesRegex(ValueError, "primitive types"):
            capabilities.validate_canary_result(boolean_bound, [approval], evidence_bytes=evidence_bytes)
        wrong_platform = {**result, "platform": "linux"}
        wrong_platform["executor_result_digest"] = capabilities.digest({key: value for key, value in wrong_platform.items() if key not in {"executor_result_digest", "availability_disposition"}})
        with self.assertRaisesRegex(ValueError, "platform does not match"):
            capabilities.validate_canary_result(wrong_platform, [approval], evidence_bytes=evidence_bytes)
        self_approved = {**result, "approved": True}
        with self.assertRaisesRegex(ValueError, "closed v1 envelope"):
            capabilities.validate_canary_result(self_approved, [approval], evidence_bytes=evidence_bytes)
        for terminal in capabilities.ERROR_TERMINALS:
            failed = copy.deepcopy(result)
            failed.update({
                "terminal_class": terminal, "exit_code": None, "sentinel_observed": False,
                "process_tree_termination_state": "completed" if terminal in {"timeout", "output_cap_exceeded"} else "not_needed",
            })
            failed["evidence_digest"] = capabilities.digest(canary_evidence_bytes(failed))
            failed["executor_result_digest"] = capabilities.digest({key: value for key, value in failed.items() if key not in {"executor_result_digest", "availability_disposition"}})
            self.assertEqual(capabilities.validate_canary_result(failed, [approval], evidence_bytes=canary_evidence_bytes(failed))["availability_disposition"], "unknown")
        for terminal in ("timeout", "output_cap_exceeded"):
            missing_cleanup = copy.deepcopy(result)
            missing_cleanup.update({"terminal_class": terminal, "exit_code": None, "sentinel_observed": False})
            missing_cleanup["evidence_digest"] = capabilities.digest(canary_evidence_bytes(missing_cleanup))
            missing_cleanup["executor_result_digest"] = capabilities.digest({key: value for key, value in missing_cleanup.items() if key not in {"executor_result_digest", "availability_disposition"}})
            with self.assertRaisesRegex(ValueError, "process-tree cleanup"):
                capabilities.validate_canary_result(missing_cleanup, [approval], evidence_bytes=canary_evidence_bytes(missing_cleanup))
        shared_decisions = [
            {"canonical_model_id": result["canonical_model_id"], "canonical_effort": result["canonical_effort"], "source_admitted": True,
             "reasons": ["surface_evidence_incomplete", "collection_evidence_non_authoritative"]},
            {"canonical_model_id": result["canonical_model_id"], "canonical_effort": result["canonical_effort"], "source_admitted": True,
             "reasons": ["surface_evidence_incomplete", "collection_evidence_non_authoritative"]},
        ]
        unknown_methods = [{"collection_method_id": "unknown-observation-v1"}]
        self.assertEqual(len(capability_freeze._validate_canary_tuple_binding(shared_decisions, result, result["snapshot_id"], unknown_methods)), 2)
        with self.assertRaisesRegex(ValueError, "documented discovery"):
            capability_freeze._validate_canary_tuple_binding(
                shared_decisions, result, result["snapshot_id"], [{"collection_method_id": "fixture-enumeration-v1"}],
            )
        predecessor = {
            "runtime_capability_snapshot_id": result["snapshot_id"],
            "tuple_decisions": shared_decisions,
            "surface_matrix": {"observations": unknown_methods},
            "canary_results": [],
            "candidate_freeze_id": capabilities.digest(b"fixture-predecessor"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            raw_root = Path(tmp) / "raw"
            raw_root.mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError, "regular non-symlink file"):
                capabilities.validate_canary_evidence(raw_root, ROOT, result)
            with mock.patch.object(capability_freeze, "APPROVED_CANARY_EXECUTORS", (approval,)), mock.patch.object(
                capability_freeze, "_validate_freeze_payload", side_effect=lambda freeze, manifest, **kwargs: freeze,
            ), self.assertRaisesRegex(ValueError, "regular non-symlink file"):
                capabilities.build_canary_successor(
                    predecessor, result, self.manifest, "2026-07-16T00:00:01Z",
                    raw_evidence_root=raw_root, repository_root=ROOT,
                )
            evidence_path = raw_root / f"{result['evidence_digest'].removeprefix('sha256:')}.json"
            evidence_path.write_bytes(evidence_bytes); evidence_path.chmod(0o600)
            self.assertEqual(capabilities.validate_canary_evidence(raw_root, ROOT, result), evidence_bytes)
            unrelated_bytes = b'{"unrelated":true}\n'
            unrelated_result = copy.deepcopy(result)
            unrelated_result["evidence_digest"] = capabilities.digest(unrelated_bytes)
            unrelated_result["executor_result_digest"] = capabilities.digest({
                key: value for key, value in unrelated_result.items()
                if key not in {"executor_result_digest", "availability_disposition"}
            })
            unrelated_path = raw_root / f"{unrelated_result['evidence_digest'].removeprefix('sha256:')}.json"
            unrelated_path.write_bytes(unrelated_bytes); unrelated_path.chmod(0o600)
            with self.assertRaisesRegex(ValueError, "canary evidence"):
                capability_freeze._validate_retained_freeze_evidence({
                    "surface_matrix": {"observations": []},
                    "canary_results": [unrelated_result],
                }, raw_root, ROOT)
            with mock.patch.object(capability_freeze, "APPROVED_CANARY_EXECUTORS", (approval,)), mock.patch.object(
                capability_freeze, "_validate_freeze_payload", side_effect=lambda freeze, manifest, **kwargs: freeze,
            ):
                successor = capabilities.build_canary_successor(
                    predecessor, result, self.manifest, "2026-07-16T00:00:01Z",
                    raw_evidence_root=raw_root, repository_root=ROOT,
                )
            self.assertEqual(successor["canary_results"], [result])
            self.assertEqual(successor["supersedes_candidate_freeze_id"], predecessor["candidate_freeze_id"])
            evidence_path.write_bytes(b"{}\n")
            with self.assertRaisesRegex(ValueError, "content digest as the filename"):
                capabilities.validate_canary_evidence(raw_root, ROOT, result)
            with self.assertRaisesRegex(ValueError, "outside every Git worktree"):
                capabilities.validate_canary_evidence(ROOT, ROOT, result)
        self.assertEqual(capabilities.APPROVED_CANARY_EXECUTORS, ())
        with self.assertRaisesRegex(ValueError, "no repository-approved canary executor"):
            capabilities.main([
                "canary", "--manifest", "unused", "--freeze", "unused", "--model", "model-a",
                "--effort", "high", "--executor-result", "unused",
                "--raw-evidence-root", "unused", "--output", "unused",
            ])

    def test_raw_root_and_sanitizer_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_root = Path(tmp) / "raw"
            raw_root.mkdir(mode=0o700)
            raw_file = raw_root / "capture.bin"
            raw_file.write_bytes(b"fixture")
            raw_file.chmod(0o600)
            self.assertEqual(stat.S_IMODE(raw_root.stat().st_mode), 0o700)
            capabilities.validate_raw_evidence_root(raw_root, ROOT)
            with mock.patch.object(
                capability_private, "PRIVATE_REFRESH_MAX_BYTES", 4,
            ), mock.patch.object(
                capability_private, "_parse_json_bytes",
                wraps=capability_private._parse_json_bytes,
            ) as parse_capture, self.assertRaisesRegex(ValueError, "bounded private-file size"):
                capabilities.materialize_source_capture(raw_root, ROOT, b'["oversized"]')
            parse_capture.assert_not_called()
            with self.assertRaisesRegex(ValueError, "bytes-like"):
                capabilities.materialize_source_capture(raw_root, ROOT, "[]")
            repository = capabilities.build_repository_binding("0" * 40, "1" * 40)
            work_item = {"kind": "fixture", "id": "G56R-002-RAW-REFERENCE"}
            evidence, retained = capabilities.materialize_unknown_capture(
                raw_root, ROOT, "cli", self.identity["client_identity_id"], repository,
                work_item, "2026-07-16T00:00:00Z",
            )
            self.assertEqual(capabilities.digest(retained.read_bytes()), evidence)
            self.assertEqual(retained.name, f"{evidence.removeprefix('sha256:')}.json")
            self.assertEqual(stat.S_IMODE(retained.stat().st_mode), 0o600)
            observation = capabilities.unknown_observation(
                "cli", self.identity["client_identity_id"], repository, work_item,
                raw_evidence_digest=evidence,
            )
            self.assertEqual(observation["raw_evidence_ref"], f"raw://{evidence}")
            self.assertIsNone(capabilities.validate_unknown_observation_evidence(observation, raw_root, ROOT))
            forged = copy.deepcopy(observation)
            forged_evidence = capabilities.digest(b"arbitrary retained bytes")
            forged.update({
                "raw_evidence_digest": forged_evidence,
                "raw_evidence_ref": f"raw://{forged_evidence}",
                "sanitized_evidence_digest": forged_evidence,
            })
            forged["surface_observation_id"] = capabilities.digest({
                key: value for key, value in forged.items() if key != "surface_observation_id"
            })
            with self.assertRaisesRegex(ValueError, "deterministic attempt record"):
                capabilities.validate_observation(forged)
            observations = []
            for surface in capabilities.SURFACES:
                surface_evidence, _ = capabilities.materialize_unknown_capture(
                    raw_root, ROOT, surface, self.identity["client_identity_id"], repository,
                    work_item, "2026-07-16T00:00:00Z",
                )
                observations.append(capabilities.unknown_observation(
                    surface, self.identity["client_identity_id"], repository, work_item,
                    raw_evidence_digest=surface_evidence,
                ))
            captured = source_capture(self.manifest)
            capture_bytes = capabilities.canonical_bytes(captured) + b"\n"
            source_capture_digest, source_capture_path = capabilities.materialize_source_capture(
                raw_root, ROOT, capture_bytes,
            )
            refreshes = capabilities.normalize_source_refreshes(
                self.manifest, captured, source_capture_digest=source_capture_digest,
            )
            source_tuples = capabilities.candidate_tuples_from_manifest(self.manifest, refreshes)
            matrix, decisions = capabilities.evaluate_surface_matrix(observations, source_tuples)
            with self.assertRaisesRegex(ValueError, "raw evidence root"):
                capabilities.build_freeze(
                    self.identity, refreshes, matrix, decisions, "2026-07-16T00:00:00Z",
                    manifest=self.manifest,
                )
            source_capture_path.unlink()
            with self.assertRaisesRegex(ValueError, "regular non-symlink"):
                capabilities.build_freeze(
                    self.identity, refreshes, matrix, decisions, "2026-07-16T00:00:00Z",
                    manifest=self.manifest, raw_evidence_root=raw_root, repository_root=ROOT,
                )
            source_capture_path.write_bytes(capture_bytes); source_capture_path.chmod(0o600)
            freeze = capabilities.build_freeze(
                self.identity, refreshes, matrix, decisions, "2026-07-16T00:00:00Z",
                manifest=self.manifest, raw_evidence_root=raw_root, repository_root=ROOT,
            )
            self.assertEqual(capabilities.validate_freeze(freeze, self.manifest), freeze)
            hard_link_source = Path(tmp) / "hard-linked-source.json"
            hard_link_output = Path(tmp) / "hard-linked-output.json"
            hard_link_source.write_bytes(capabilities.canonical_bytes(freeze) + b"\n")
            os.link(hard_link_source, hard_link_output)
            with mock.patch.object(
                capability_freeze, "_store_publication_receipt_locked",
            ) as store_receipt, self.assertRaisesRegex(ValueError, "single-link"):
                capabilities.publish_with_raw_evidence_retention(
                    freeze, hard_link_output, raw_root, ROOT, manifest=self.manifest,
                )
            store_receipt.assert_not_called()
            hard_link_output.unlink(); hard_link_source.unlink()
            publication_path = Path(tmp) / "candidate-freeze.json"
            with mock.patch.object(
                capability_retention_records, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-07-16T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_freeze, "_store_publication_receipt_locked",
                side_effect=OSError("simulated publication receipt failure"),
            ):
                with self.assertRaisesRegex(OSError, "receipt failure"):
                    capabilities.publish_with_raw_evidence_retention(
                        freeze, publication_path, raw_root, ROOT, manifest=self.manifest,
                    )
            self.assertTrue(publication_path.is_file())
            pending_before_recovery = capabilities.reconcile_raw_evidence_retention(
                raw_root, ROOT, "2026-08-14T23:59:59Z",
            )
            expected_retained = sorted(
                [source_capture_digest, *(item["raw_evidence_digest"] for item in observations)]
            )
            self.assertEqual(pending_before_recovery["retained_evidence_digests"], expected_retained)
            self.assertEqual(len(pending_before_recovery["pending_retention_record_digests"]), 4)
            with mock.patch.object(
                capability_retention_records, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-07-16T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_freeze, "validate_unknown_observation_evidence",
                wraps=capability_freeze.validate_unknown_observation_evidence,
            ) as validate_unknown_evidence:
                publication = capabilities.publish_with_raw_evidence_retention(
                    freeze, publication_path, raw_root, ROOT, manifest=self.manifest,
                )
            self.assertEqual(validate_unknown_evidence.call_count, 3)
            self.assertEqual(len(publication["retention_record_digests"]), 4)
            self.assertEqual(capabilities.publish_with_raw_evidence_retention(
                freeze, publication_path, raw_root, ROOT, manifest=self.manifest,
            ), publication)
            future_freeze = copy.deepcopy(freeze)
            future_freeze["published_at"] = "2026-08-01T00:00:00Z"
            future_freeze["candidate_freeze_id"] = capabilities.digest(capability_freeze._freeze_identity_payload(future_freeze))
            self.assertEqual(capabilities.validate_freeze(future_freeze, self.manifest), future_freeze)
            later_freeze = copy.deepcopy(freeze)
            later_freeze["published_at"] = "2026-09-01T00:00:00Z"
            later_freeze["candidate_freeze_id"] = capabilities.digest(capability_freeze._freeze_identity_payload(later_freeze))
            self.assertEqual(capabilities.validate_freeze(later_freeze, self.manifest), later_freeze)
            with self.assertRaisesRegex(ValueError, "different bytes"):
                capabilities.publish_with_raw_evidence_retention(
                    future_freeze, publication_path, raw_root, ROOT, manifest=self.manifest,
                )
            self.assertEqual(len(list((raw_root / capabilities.RETENTION_RECORDS_DIR).iterdir())), 4)
            failed_publication_path = Path(tmp) / "failed-candidate-freeze.json"
            later_failed_publication_path = Path(tmp) / "later-failed-candidate-freeze.json"
            failed_publication_paths = {failed_publication_path, later_failed_publication_path}
            original_write = capability_private._write
            def fail_publication(path: Path, value: object, **kwargs: object) -> None:
                if Path(path) in failed_publication_paths:
                    raise OSError("simulated publication failure")
                original_write(path, value, **kwargs)
            with mock.patch.object(
                capability_retention_records, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-07-16T00:00:00Z", "test clock"),
            ), mock.patch.object(capability_freeze, "_write", side_effect=fail_publication):
                for failed_freeze, failed_path in (
                    (future_freeze, failed_publication_path),
                    (later_freeze, later_failed_publication_path),
                ):
                    with self.assertRaisesRegex(OSError, "publication failure"):
                        capabilities.publish_with_raw_evidence_retention(
                            failed_freeze, failed_path, raw_root, ROOT, manifest=self.manifest,
                        )
            pending_after_registration = capabilities.reconcile_raw_evidence_retention(
                raw_root, ROOT, "2026-08-14T23:59:59Z",
            )
            self.assertEqual(pending_after_registration["retained_evidence_digests"], expected_retained)
            self.assertEqual(len(pending_after_registration["pending_retention_record_digests"]), 8)
            self.assertEqual(len(pending_after_registration["retention_record_digests"]), 12)
            raw_identity = capability_io._stable_directory_identity(
                os.stat(raw_root, follow_symlinks=False),
            )
            with capability_retention_records._retention_lock(raw_root, raw_identity):
                with self.assertRaisesRegex(ValueError, "already in progress"):
                    capabilities.publish_with_raw_evidence_retention(
                        freeze, publication_path, raw_root, ROOT, manifest=self.manifest,
                    )
                with self.assertRaisesRegex(ValueError, "already in progress"):
                    capabilities.reconcile_raw_evidence_retention(raw_root, ROOT, "2026-08-14T23:59:59Z")
            retention_lock_path = raw_root / capabilities.RETENTION_LOCK_FILE
            self.assertTrue(retention_lock_path.is_file())
            self.assertEqual(stat.S_IMODE(retention_lock_path.stat().st_mode), 0o600)
            retained_report = capabilities.reconcile_raw_evidence_retention(
                raw_root, ROOT, "2026-08-14T23:59:59Z",
            )
            retention_output = raw_root / "retention-report.json"
            self.assertEqual(capabilities.main([
                "retention", "--raw-evidence-root", str(raw_root), "--as-of", "2026-08-14T23:59:59Z",
                "--mode", "verify", "--output", str(retention_output),
            ]), 0)
            self.assertEqual(json.loads(retention_output.read_text()), retained_report)
            self.assertEqual(retained_report["retained_evidence_digests"], expected_retained)
            self.assertTrue(set(publication["retention_record_digests"]) <= set(retained_report["retention_record_digests"]))
            self.assertEqual(len(retained_report["retention_record_digests"]), 12)
            self.assertEqual(len(retained_report["pending_retention_record_digests"]), 8)
            self.assertEqual(retained_report["publication_receipt_digests"], [publication["publication_receipt_digest"]])
            self.assertEqual(source_capture_path.read_bytes(), capture_bytes)
            missing_digest = source_capture_digest
            missing_path = raw_root / f"{missing_digest.removeprefix('sha256:')}.json"
            missing_bytes = missing_path.read_bytes(); missing_path.unlink()
            with self.assertRaisesRegex(ValueError, "regular non-symlink"):
                capabilities.reconcile_raw_evidence_retention(raw_root, ROOT, "2026-08-14T23:59:59Z")
            missing_path.write_bytes(missing_bytes); missing_path.chmod(0o600)
            with self.assertRaisesRegex(ValueError, "requires cleanup"):
                capabilities.reconcile_raw_evidence_retention(raw_root, ROOT, "2026-08-15T00:00:00Z")
            with self.assertRaisesRegex(ValueError, "current UTC"):
                capabilities.reconcile_raw_evidence_retention(raw_root, ROOT, "2099-01-01T00:00:00Z", apply=True)
            stale_hard_link = raw_root / ".g56r-002-power-loss"
            os.link(source_capture_path, stale_hard_link)
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            ):
                with self.assertRaisesRegex(ValueError, "alternate hard links"):
                    capabilities.reconcile_raw_evidence_retention(raw_root, ROOT, apply=True)
            stale_hard_link.unlink(); capability_private._fsync_directory(raw_root.resolve())
            race_root = Path(tmp) / "hard-link-race-root"
            shutil.copytree(raw_root, race_root)
            race_link = Path(tmp) / "retained-race-link.json"; raced_filename = None
            original_unlink_descriptor_relative = capability_retention._unlink_descriptor_relative
            def create_external_link_before_unlink(filename: str, parent_descriptor: int) -> None:
                nonlocal raced_filename
                raced_filename = filename
                os.link(race_root / filename, race_link)
                original_unlink_descriptor_relative(filename, parent_descriptor)
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_retention, "_unlink_descriptor_relative", side_effect=create_external_link_before_unlink,
            ), self.assertRaisesRegex(ValueError, "retains an alternate hard link"):
                capabilities.reconcile_raw_evidence_retention(race_root, ROOT, apply=True)
            self.assertIsNotNone(raced_filename)
            restored_race_target = race_root / str(raced_filename)
            self.assertEqual(restored_race_target.read_bytes(), capture_bytes)
            self.assertEqual(race_link.read_bytes(), capture_bytes)
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            ), self.assertRaisesRegex(ValueError, "target identity changed"):
                capabilities.reconcile_raw_evidence_retention(race_root, ROOT, apply=True)

            deletion_directory = race_root / capabilities.DELETION_RECORDS_DIR
            self.assertFalse(deletion_directory.exists() and any(deletion_directory.iterdir()))
            race_link.unlink()
            mutation_root = Path(tmp) / "post-digest-mutation-root"
            shutil.copytree(raw_root, mutation_root)
            mutated_filename = None
            def mutate_after_digest_before_unlink(filename: str, parent_descriptor: int) -> None:
                nonlocal mutated_filename
                mutated_filename = filename
                mutated = mutation_root / filename; mutated.write_bytes(b"mutated-after-digest\n"); mutated.chmod(0o600)
                original_unlink_descriptor_relative(filename, parent_descriptor)
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_retention, "_unlink_descriptor_relative", side_effect=mutate_after_digest_before_unlink,
            ), self.assertRaisesRegex(ValueError, "changed while it was being unlinked|verified content identity"):
                capabilities.reconcile_raw_evidence_retention(mutation_root, ROOT, apply=True)
            self.assertIsNotNone(mutated_filename)
            restored_mutation_target = mutation_root / str(mutated_filename)
            mutated_intent = next(
                json.loads(path.read_text())
                for path in (mutation_root / capabilities.DELETION_INTENTS_DIR).iterdir()
                if json.loads(path.read_text())["schema_version"] == "raw-evidence-deletion-intent.v3"
            )
            self.assertEqual(
                capabilities.digest(restored_mutation_target.read_bytes()),
                mutated_intent["raw_evidence_digest"],
            )
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            ), self.assertRaisesRegex(ValueError, "target identity changed"):
                capabilities.reconcile_raw_evidence_retention(mutation_root, ROOT, apply=True)
            write_failure_root = Path(tmp) / "deletion-record-write-failure-root"
            shutil.copytree(raw_root, write_failure_root)
            cleanup_clock = mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            )
            original_private_write = capability_private._write_private_bytes_at
            def fail_deletion_record_write(
                parent_descriptor: int, parent_path: Path, filename: str, payload: bytes, **kwargs: object,
            ) -> None:
                if Path(parent_path).name == capabilities.DELETION_RECORDS_DIR:
                    raise OSError("simulated deletion-record write failure")
                original_private_write(parent_descriptor, parent_path, filename, payload, **kwargs)
            with cleanup_clock, mock.patch.object(
                capability_private, "_write_private_bytes_at", side_effect=fail_deletion_record_write,
            ):
                with self.assertRaisesRegex(OSError, "deletion-record write"):
                    capabilities.reconcile_raw_evidence_retention(write_failure_root, ROOT, apply=True)
            self.assertFalse(any(
                path.name.startswith(".g56r-002-") for path in write_failure_root.iterdir()
            ))
            write_failure_intents = [
                (json.loads(path.read_text()), f"sha256:{path.stem}")
                for path in (write_failure_root / capabilities.DELETION_INTENTS_DIR).iterdir()
            ]
            initial_intent, initial_intent_digest = next(
                item for item in write_failure_intents
                if item[0]["schema_version"] == "raw-evidence-deletion-intent.v2"
            )
            staged_intent, staged_intent_digest = next(
                item for item in write_failure_intents
                if item[0]["schema_version"] == "raw-evidence-deletion-intent.v3"
            )
            self.assertFalse((write_failure_root / (
                f"{staged_intent['raw_evidence_digest'].removeprefix('sha256:')}.json"
            )).exists())
            self.assertEqual(staged_intent["predecessor_deletion_intent_digest"], initial_intent_digest)
            self.assertEqual(staged_intent["recovery_proof"], "verified-quarantine-transition-v1")
            forked_recovery = copy.deepcopy(staged_intent)
            forked_recovery["deletion_started_at"] = "2026-08-15T00:00:01Z"
            forked_recovery_digest = capabilities.digest(
                capabilities.canonical_bytes(forked_recovery) + b"\n",
            )
            with self.assertRaisesRegex(ValueError, "missing or forked"):
                capability_retention_records._terminal_deletion_intents([
                    (initial_intent, initial_intent_digest),
                    (staged_intent, staged_intent_digest),
                    (forked_recovery, forked_recovery_digest),
                ])
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            ), self.assertRaisesRegex(ValueError, "missing without durable completion proof"):
                capabilities.reconcile_raw_evidence_retention(write_failure_root, ROOT, apply=True)
            self.assertEqual(list((write_failure_root / capabilities.DELETION_RECORDS_DIR).iterdir()), [])
            interrupted_recovery_root = Path(tmp) / "interrupted-recovery-root"
            shutil.copytree(raw_root, interrupted_recovery_root)
            class SimulatedCompletionTermination(BaseException):
                pass
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_retention, "_store_staged_recovery_completion",
                side_effect=SimulatedCompletionTermination,
            ), self.assertRaises(SimulatedCompletionTermination):
                capabilities.reconcile_raw_evidence_retention(interrupted_recovery_root, ROOT, apply=True)
            interrupted_intents = [
                json.loads(path.read_text())
                for path in (interrupted_recovery_root / capabilities.DELETION_INTENTS_DIR).iterdir()
            ]
            self.assertEqual(
                sorted(item["schema_version"] for item in interrupted_intents),
                ["raw-evidence-deletion-intent.v2", "raw-evidence-deletion-intent.v3"],
            )
            staged_after_crash = next(
                item for item in interrupted_intents
                if item["schema_version"] == "raw-evidence-deletion-intent.v3"
            )
            self.assertFalse((interrupted_recovery_root / (
                f"{staged_after_crash['raw_evidence_digest'].removeprefix('sha256:')}.json"
            )).exists())
            self.assertFalse(any(
                path.name.startswith(".g56r-002-") for path in interrupted_recovery_root.iterdir()
            ))
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-16T00:00:00Z", "test clock"),
            ), self.assertRaisesRegex(ValueError, "missing without durable completion proof"):
                capabilities.reconcile_raw_evidence_retention(interrupted_recovery_root, ROOT, apply=True)
            self.assertFalse((interrupted_recovery_root / capabilities.DELETION_RECORDS_DIR).exists() and any(
                (interrupted_recovery_root / capabilities.DELETION_RECORDS_DIR).iterdir()
            ))
            hard_link_crash_root = Path(tmp) / "post-unlink-hard-link-crash-root"
            shutil.copytree(raw_root, hard_link_crash_root)
            hard_link_after_crash = Path(tmp) / "post-unlink-hard-link.json"
            class SimulatedPostUnlinkTermination(BaseException):
                pass
            def hard_link_then_unlink_then_terminate(filename: str, parent_descriptor: int) -> None:
                os.link(hard_link_crash_root / filename, hard_link_after_crash)
                original_unlink_descriptor_relative(filename, parent_descriptor)
                raise SimulatedPostUnlinkTermination
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_retention, "_unlink_descriptor_relative",
                side_effect=hard_link_then_unlink_then_terminate,
            ), self.assertRaises(SimulatedPostUnlinkTermination):
                capabilities.reconcile_raw_evidence_retention(hard_link_crash_root, ROOT, apply=True)
            self.assertEqual(hard_link_after_crash.read_bytes(), capture_bytes)
            self.assertFalse(any(
                path.name.startswith(".g56r-002-") for path in hard_link_crash_root.iterdir()
            ))
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-16T00:00:00Z", "test clock"),
            ), self.assertRaisesRegex(ValueError, "missing without durable completion proof"):
                capabilities.reconcile_raw_evidence_retention(hard_link_crash_root, ROOT, apply=True)
            self.assertFalse((hard_link_crash_root / capabilities.DELETION_RECORDS_DIR).exists() and any(
                (hard_link_crash_root / capabilities.DELETION_RECORDS_DIR).iterdir()
            ))
            hard_link_after_crash.unlink()
            journal_failure_root = Path(tmp) / "staged-journal-persistence-failure-root"
            shutil.copytree(raw_root, journal_failure_root)
            original_store_staged = capability_retention._store_staged_recovery_intent
            def fail_after_staged_journal(*args: object, **kwargs: object) -> None:
                original_store_staged(*args, **kwargs)
                raise ValueError("simulated post-persistence staged journal failure")
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_retention, "_store_staged_recovery_intent",
                side_effect=fail_after_staged_journal,
            ), mock.patch.object(
                capability_retention, "_write_private_bytes_at",
                side_effect=AssertionError("raw bytes must not be republished after unlink proof"),
            ), self.assertRaisesRegex(ValueError, "staged journal failure"):
                capabilities.reconcile_raw_evidence_retention(journal_failure_root, ROOT, apply=True)
            staged_path = next(
                path for path in (journal_failure_root / capabilities.DELETION_INTENTS_DIR).iterdir()
                if json.loads(path.read_text())["schema_version"] == "raw-evidence-deletion-intent.v3"
            )
            missing_stage = json.loads(staged_path.read_text())
            self.assertFalse((journal_failure_root / (
                f"{missing_stage['raw_evidence_digest'].removeprefix('sha256:')}.json"
            )).exists())
            staged_quarantine = journal_failure_root / missing_stage["quarantine_filename"]
            self.assertTrue(staged_quarantine.is_file())
            self.assertEqual(
                capability_retention._deletion_intent_file_identity(staged_quarantine.stat()),
                missing_stage["target_file_identity"],
            )
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-16T00:00:00Z", "test clock"),
            ):
                missing_staged_cleanup = capabilities.reconcile_raw_evidence_retention(
                    journal_failure_root, ROOT, apply=True,
                )
            self.assertEqual(
                missing_staged_cleanup["deleted_evidence_digests"],
                retained_report["retained_evidence_digests"],
            )
            missing_completion = next(
                json.loads(path.read_text())
                for path in (journal_failure_root / capabilities.DELETION_RECORDS_DIR).iterdir()
                if json.loads(path.read_text())["raw_evidence_digest"] == missing_stage["raw_evidence_digest"]
            )
            self.assertEqual(missing_completion["deletion_intent_digest"], f"sha256:{staged_path.stem}")
            self.assertEqual(missing_completion["deleted_at"], "2026-08-16T00:00:00Z")
            pre_journal_root = Path(tmp) / "pre-journal-persistence-failure-root"
            shutil.copytree(raw_root, pre_journal_root)
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_retention, "_store_staged_recovery_intent",
                side_effect=ValueError("simulated pre-persistence staged journal failure"),
            ), self.assertRaisesRegex(ValueError, "pre-persistence staged journal failure"):
                capabilities.reconcile_raw_evidence_retention(pre_journal_root, ROOT, apply=True)
            pre_journal_intents = [
                (json.loads(path.read_text()), f"sha256:{path.stem}")
                for path in (pre_journal_root / capabilities.DELETION_INTENTS_DIR).iterdir()
            ]
            self.assertEqual(
                sorted(item[0]["schema_version"] for item in pre_journal_intents),
                ["raw-evidence-deletion-intent.v2"],
            )
            pre_journal_intent, pre_journal_digest = pre_journal_intents[0]
            pre_journal_quarantine = pre_journal_root / (
                capability_retention._deletion_quarantine_filename(pre_journal_digest)
            )
            self.assertTrue(pre_journal_quarantine.is_file())
            self.assertEqual(
                capability_retention._deletion_intent_file_identity(pre_journal_quarantine.stat()),
                pre_journal_intent["target_file_identity"],
            )
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-16T00:00:00Z", "test clock"),
            ):
                pre_journal_cleanup = capabilities.reconcile_raw_evidence_retention(
                    pre_journal_root, ROOT, apply=True,
                )
            self.assertEqual(
                pre_journal_cleanup["deleted_evidence_digests"],
                retained_report["retained_evidence_digests"],
            )
            rename_sync_failure_root = Path(tmp) / "rename-sync-failure-root"
            shutil.copytree(raw_root, rename_sync_failure_root)
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_retention, "_sync_verified_quarantine",
                side_effect=OSError("simulated quarantine rename fsync failure"),
            ), self.assertRaisesRegex(ValueError, "could not be deleted safely"):
                capabilities.reconcile_raw_evidence_retention(rename_sync_failure_root, ROOT, apply=True)
            sync_failure_intents = [
                (json.loads(path.read_text()), f"sha256:{path.stem}")
                for path in (rename_sync_failure_root / capabilities.DELETION_INTENTS_DIR).iterdir()
            ]
            self.assertEqual(
                sorted(item[0]["schema_version"] for item in sync_failure_intents),
                ["raw-evidence-deletion-intent.v2"],
            )
            sync_failure_intent, sync_failure_digest = sync_failure_intents[0]
            sync_failure_quarantine = rename_sync_failure_root / (
                capability_retention._deletion_quarantine_filename(sync_failure_digest)
            )
            self.assertTrue(sync_failure_quarantine.is_file())
            class SimulatedPostV3Termination(BaseException):
                pass
            retry_sync_calls = []
            original_sync_quarantine = capability_retention._sync_verified_quarantine
            original_store_staged = capability_retention._store_staged_recovery_intent
            def track_retry_sync(*args: object, **kwargs: object) -> object:
                retry_sync_calls.append(True)
                return original_sync_quarantine(*args, **kwargs)
            def terminate_after_v3(*args: object, **kwargs: object) -> None:
                original_store_staged(*args, **kwargs)
                raise SimulatedPostV3Termination
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-16T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_retention, "_sync_verified_quarantine", side_effect=track_retry_sync,
            ), mock.patch.object(
                capability_retention, "_store_staged_recovery_intent", side_effect=terminate_after_v3,
            ), self.assertRaises(SimulatedPostV3Termination):
                capabilities.reconcile_raw_evidence_retention(rename_sync_failure_root, ROOT, apply=True)
            self.assertEqual(retry_sync_calls, [True])
            post_v3_intents = [
                json.loads(path.read_text())
                for path in (rename_sync_failure_root / capabilities.DELETION_INTENTS_DIR).iterdir()
            ]
            self.assertEqual(
                sorted(item["schema_version"] for item in post_v3_intents),
                ["raw-evidence-deletion-intent.v2", "raw-evidence-deletion-intent.v3"],
            )
            self.assertTrue(sync_failure_quarantine.is_file())
            self.assertFalse((rename_sync_failure_root / (
                f"{sync_failure_intent['raw_evidence_digest'].removeprefix('sha256:')}.json"
            )).exists())
            pre_unlink_error_root = Path(tmp) / "pre-unlink-error-root"
            shutil.copytree(raw_root, pre_unlink_error_root)
            failed_pre_unlink_filename = None
            def fail_before_unlink(filename: str, parent_descriptor: int) -> None:
                nonlocal failed_pre_unlink_filename
                failed_pre_unlink_filename = filename
                raise OSError("simulated pre-unlink failure")
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_retention, "_unlink_descriptor_relative", side_effect=fail_before_unlink,
            ), self.assertRaisesRegex(ValueError, "could not be deleted safely"):
                capabilities.reconcile_raw_evidence_retention(pre_unlink_error_root, ROOT, apply=True)
            self.assertIsNotNone(failed_pre_unlink_filename)
            pre_unlink_error_intents = [
                json.loads(path.read_text())
                for path in (pre_unlink_error_root / capabilities.DELETION_INTENTS_DIR).iterdir()
            ]
            self.assertEqual(
                sorted(item["schema_version"] for item in pre_unlink_error_intents),
                ["raw-evidence-deletion-intent.v2", "raw-evidence-deletion-intent.v3"],
            )
            pre_unlink_error_intent = next(
                item for item in pre_unlink_error_intents
                if item["schema_version"] == "raw-evidence-deletion-intent.v3"
            )
            pre_unlink_error_target = pre_unlink_error_root / str(failed_pre_unlink_filename)
            self.assertEqual(
                capability_retention._deletion_intent_file_identity(pre_unlink_error_target.stat()),
                pre_unlink_error_intent["target_file_identity"],
            )
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-16T00:00:00Z", "test clock"),
            ):
                pre_unlink_error_cleanup = capabilities.reconcile_raw_evidence_retention(
                    pre_unlink_error_root, ROOT, apply=True,
                )
            self.assertEqual(
                pre_unlink_error_cleanup["deleted_evidence_digests"],
                retained_report["retained_evidence_digests"],
            )
            pre_unlink_root = Path(tmp) / "pre-unlink-crash-root"
            shutil.copytree(raw_root, pre_unlink_root)
            class SimulatedPreUnlinkTermination(BaseException):
                pass
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_retention, "_delete_single_link_private_file",
                side_effect=SimulatedPreUnlinkTermination,
            ), self.assertRaises(SimulatedPreUnlinkTermination):
                capabilities.reconcile_raw_evidence_retention(pre_unlink_root, ROOT, apply=True)
            pre_unlink_intents = list((pre_unlink_root / capabilities.DELETION_INTENTS_DIR).iterdir())
            self.assertEqual(len(pre_unlink_intents), 1)
            pre_unlink_intent = json.loads(pre_unlink_intents[0].read_text())
            self.assertEqual(pre_unlink_intent["schema_version"], "raw-evidence-deletion-intent.v2")
            self.assertEqual(pre_unlink_intent["target_file_identity"]["mode"], 0o600)
            malformed_intent = copy.deepcopy(pre_unlink_intent)
            malformed_intent["target_file_identity"]["inode"] = True
            malformed_intent_digest = capabilities.digest(
                capabilities.canonical_bytes(malformed_intent) + b"\n",
            )
            with self.assertRaisesRegex(ValueError, "private target file identity"):
                capability_retention_records._validate_deletion_intent(
                    malformed_intent_digest, malformed_intent,
                )
            pre_unlink_target = pre_unlink_root / (
                f"{pre_unlink_intent['raw_evidence_digest'].removeprefix('sha256:')}.json"
            )
            pre_unlink_link = Path(tmp) / "pre-unlink-retained-link.json"
            os.link(pre_unlink_target, pre_unlink_link)
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-16T00:00:00Z", "test clock"),
            ), self.assertRaisesRegex(ValueError, "alternate hard links"):
                capabilities.reconcile_raw_evidence_retention(pre_unlink_root, ROOT, apply=True)
            self.assertTrue(pre_unlink_target.is_file())
            pre_unlink_link.unlink()
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-16T00:00:00Z", "test clock"),
            ):
                resumed_cleanup = capabilities.reconcile_raw_evidence_retention(
                    pre_unlink_root, ROOT, apply=True,
                )
            self.assertEqual(
                resumed_cleanup["deleted_evidence_digests"],
                retained_report["retained_evidence_digests"],
            )
            self.assertTrue(all(
                json.loads(path.read_text())["deleted_at"] == "2026-08-16T00:00:00Z"
                for path in (pre_unlink_root / capabilities.DELETION_RECORDS_DIR).iterdir()
            ))
            original_delete = capability_retention._delete_single_link_private_file
            class SimulatedProcessTermination(BaseException):
                pass
            def terminate_after_committed_deletion(*args: object, **kwargs: object) -> None:
                original_delete(*args, **kwargs)
                raise SimulatedProcessTermination
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-16T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_retention, "_delete_single_link_private_file",
                side_effect=terminate_after_committed_deletion,
            ), self.assertRaises(SimulatedProcessTermination):
                capabilities.reconcile_raw_evidence_retention(raw_root, ROOT, apply=True)
            deletion_record_paths = list((raw_root / capabilities.DELETION_RECORDS_DIR).iterdir())
            self.assertEqual(len(deletion_record_paths), 1)
            committed_deletion = json.loads(deletion_record_paths[0].read_text())
            self.assertEqual(committed_deletion["deleted_at"], "2026-08-16T00:00:00Z")
            committed_intent_path = (
                raw_root / capabilities.DELETION_INTENTS_DIR
                / f"{committed_deletion['deletion_intent_digest'].removeprefix('sha256:')}.json"
            )
            self.assertEqual(
                json.loads(committed_intent_path.read_text())["deletion_started_at"],
                "2026-08-16T00:00:00Z",
            )
            self.assertEqual(sum(
                (raw_root / f"{item.removeprefix('sha256:')}.json").is_file()
                for item in retained_report["retained_evidence_digests"]
            ), 3)
            original_os_fsync = capability_io.os.fsync
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-16T00:00:00Z", "test clock"),
            ), mock.patch.object(
                capability_private, "_write_private_bytes_at", wraps=original_private_write,
            ) as private_write, mock.patch.object(capability_io.os, "fsync", wraps=original_os_fsync) as fsync:
                cleanup_report = capabilities.reconcile_raw_evidence_retention(raw_root, ROOT, apply=True)
            self.assertTrue(any(
                Path(call.args[1]).name == capabilities.DELETION_RECORDS_DIR
                for call in private_write.call_args_list
            ))
            self.assertTrue(fsync.called)
            self.assertEqual(cleanup_report["deleted_evidence_digests"], retained_report["retained_evidence_digests"])
            self.assertEqual(cleanup_report["retained_evidence_digests"], [])
            self.assertEqual(len(cleanup_report["deletion_record_digests"]), 4)
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-16T00:00:00Z", "test clock"),
            ):
                self.assertEqual(capabilities.reconcile_raw_evidence_retention(raw_root, ROOT, apply=True), cleanup_report)
            cleanup_output = raw_root / "cleanup-report.json"
            with mock.patch.object(
                capability_retention, "_retention_now",
                return_value=capability_contract._parsed_timestamp("2026-08-16T00:00:00Z", "test clock"),
            ):
                self.assertEqual(capabilities.main([
                    "retention", "--raw-evidence-root", str(raw_root),
                    "--mode", "cleanup", "--output", str(cleanup_output),
                ]), 0)
            self.assertEqual(json.loads(cleanup_output.read_text()), cleanup_report)
            verified_deleted = capabilities.reconcile_raw_evidence_retention(raw_root, ROOT, "2026-08-16T00:00:00Z")
            self.assertEqual(verified_deleted["deleted_evidence_digests"], cleanup_report["deleted_evidence_digests"])
            with self.assertRaisesRegex(ValueError, "precedes the deletion"):
                capabilities.reconcile_raw_evidence_retention(raw_root, ROOT, "2026-08-14T23:59:59Z")
            with self.assertRaisesRegex(ValueError, "after deletion"):
                capabilities.publish_with_raw_evidence_retention(
                    freeze, publication_path, raw_root, ROOT, manifest=self.manifest,
                )
            self.assertTrue(all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in (raw_root / capabilities.RETENTION_RECORDS_DIR).iterdir()))
            self.assertTrue(all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in (raw_root / capabilities.DELETION_INTENTS_DIR).iterdir()))
            self.assertTrue(all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in (raw_root / capabilities.DELETION_RECORDS_DIR).iterdir()))
            self.assertTrue(all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in (raw_root / capabilities.PUBLICATION_RECEIPTS_DIR).iterdir()))
            raw_file.chmod(0o644)
            with self.assertRaisesRegex(ValueError, "files require 0600"):
                capabilities.validate_raw_evidence_root(raw_root, ROOT)
            raw_file.chmod(0o600)
            child = raw_root / "nested"; child.mkdir(mode=0o755)
            with self.assertRaisesRegex(ValueError, "directories require 0700"):
                capabilities.validate_raw_evidence_root(raw_root, ROOT)
            child.chmod(0o700)
            if os.name != "nt":
                link = raw_root / "escape"; link.symlink_to(Path(tmp).parent)
                with self.assertRaisesRegex(ValueError, "symlink"):
                    capabilities.validate_raw_evidence_root(raw_root, ROOT)
                link.unlink()
            with self.assertRaisesRegex(ValueError, "outside every Git worktree"):
                capabilities.validate_raw_evidence_root(ROOT, ROOT)
            private = Path(tmp) / "capture.json"; private.write_text("{}"); private.chmod(0o600)
            with mock.patch.object(capability_io.os, "name", "nt"):
                with self.assertRaisesRegex(ValueError, "not supported on Windows"):
                    capabilities.validate_raw_evidence_root(raw_root, ROOT)
                with self.assertRaisesRegex(ValueError, "not supported on Windows"):
                    capabilities.validate_private_external_file(private, ROOT, "private input")
                with self.assertRaisesRegex(ValueError, "not supported on Windows"):
                    capability_private._write_private_bytes(private, b"{}\n")
            self.assertEqual(capabilities.validate_private_external_file(private, ROOT, "capture"), private.resolve())
            content = b"content-addressed evidence\n"; content_digest = capabilities.digest(content)
            content_path = Path(tmp) / f"{content_digest.removeprefix('sha256:')}.json"
            content_path.write_bytes(content); content_path.chmod(0o600)
            self.assertEqual(capabilities.validate_content_addressed_private_file(content_path, ROOT, "capture"), content_path.resolve())
            self.assertEqual(capabilities.read_content_addressed_private_file(content_path, ROOT, "capture"), (content_path.resolve(), content))
            private_tree = Path(tmp) / "private-tree"; private_tree.mkdir(mode=0o700)
            intermediate = private_tree / "intermediate"; intermediate.mkdir(mode=0o700)
            raced_private = intermediate / "private.json"; raced_private.write_bytes(b"original\n"); raced_private.chmod(0o600)
            moved_intermediate = private_tree / "intermediate-original"
            original_open = capability_io.os.open; swapped = False
            def replace_private_directory(path: object, flags: int, *args: object, **kwargs: object) -> int:
                nonlocal swapped
                if path == "private.json" and kwargs.get("dir_fd") is not None and not swapped:
                    swapped = True
                    intermediate.rename(moved_intermediate); intermediate.mkdir(mode=0o700)
                    replacement = intermediate / "private.json"; replacement.write_bytes(b"replacement\n"); replacement.chmod(0o600)
                return original_open(path, flags, *args, **kwargs)
            with mock.patch.object(capability_io.os, "open", side_effect=replace_private_directory), self.assertRaisesRegex(
                ValueError, "directory changed while it was being read|path changed while it was being read"
            ):
                capabilities.read_private_external_file(raced_private, ROOT, "private input")
            with self.assertRaisesRegex(ValueError, "content digest as the filename"):
                capabilities.validate_content_addressed_private_file(private, ROOT, "capture")
            with self.assertRaisesRegex(ValueError, "outside every Git worktree"):
                capabilities.validate_private_external_file(ROOT / "capture.json", ROOT, "capture", output=True)
        sanitized = capabilities.sanitize({"surface": "cli", "status": "unknown", "authorization": "secret", "hostname": "machine"}, "surface_status")
        self.assertEqual(sanitized, {"status": "unknown", "surface": "cli"})
        first = capabilities.sanitize({"account": "fixture-sensitive"}, "fixture_identity")
        self.assertEqual(first, capabilities.sanitize({"account": "different-sensitive"}, "fixture_identity"))
        self.assertNotIn("fixture-sensitive", first["account"])
        with self.assertRaisesRegex(ValueError, "forbidden sensitive field"):
            capabilities.sanitize({"status": {"authorization": "secret"}}, "surface_status")
        secret = {"state": "complete", "entries": [{"model": "model-a", "effort": "high", "available": True, "hidden": False, "credentials": {"token": "secret"}}]}
        with self.assertRaisesRegex(ValueError, "undeclared"):
            capabilities.fixture_observation("cli", secret, self.identity["client_identity_id"])
        observation = self.observations(next(item for item in self.fixture["surface_cases"] if item["case_id"] == "agreed"))[0]
        observation["entries"][0]["model"] = "/" + "Users/fixture/private"
        observation["surface_observation_id"] = capabilities.digest({key: observation[key] for key in observation if key != "surface_observation_id"})
        with self.assertRaisesRegex(ValueError, "path or remote"):
            capabilities.validate_observation(observation)
        for bad_model in ("model-a\nAuthorization", "model-a\x1b[31m", "x" * 129, "モデル"):
            with self.subTest(bad_model=bad_model), self.assertRaisesRegex(ValueError, "model or effort"):
                capabilities.fixture_observation(
                    "cli", {"state": "complete", "entries": [{"model": bad_model, "effort": "high", "available": True, "hidden": False}]},
                    self.identity["client_identity_id"],
                )
        machine = capabilities.fixture_observation("cli", {"state": "complete", "entries": [{"model": "Model A", "machine_id": "model-a", "raw_label": "Model A", "effort": "high", "available": True, "hidden": False}]}, self.identity["client_identity_id"])
        self.assertEqual(machine["entries"][0]["machine_id"], "model-a")
        bad_ref = copy.deepcopy(machine); bad_ref["raw_evidence_ref"] += "/private"
        bad_ref["surface_observation_id"] = capabilities.digest({key: bad_ref[key] for key in bad_ref if key != "surface_observation_id"})
        with self.assertRaisesRegex(ValueError, "content addressed"):
            capabilities.validate_observation(bad_ref)
        mismatched_ref = copy.deepcopy(machine); mismatched_ref["raw_evidence_ref"] = f"raw://{capabilities.digest(b'different')}"
        mismatched_ref["surface_observation_id"] = capabilities.digest({key: mismatched_ref[key] for key in mismatched_ref if key != "surface_observation_id"})
        with self.assertRaisesRegex(ValueError, "match raw_evidence_digest"):
            capabilities.validate_observation(mismatched_ref)
        bad_time = copy.deepcopy(machine); bad_time["started_at"] = "2026-07-16 00:00:00Z"
        bad_time["surface_observation_id"] = capabilities.digest({key: bad_time[key] for key in bad_time if key != "surface_observation_id"})
        with self.assertRaisesRegex(ValueError, "collection timestamp"):
            capabilities.validate_observation(bad_time)
        reversed_window = copy.deepcopy(machine); reversed_window.update({"started_at": "2026-07-16T00:00:01Z", "completed_at": "2026-07-16T00:00:00Z"})
        reversed_window["surface_observation_id"] = capabilities.digest({key: reversed_window[key] for key in reversed_window if key != "surface_observation_id"})
        with self.assertRaisesRegex(ValueError, "collection window"):
            capabilities.validate_observation(reversed_window)

    def test_retention_deadline_includes_every_bounded_pending_claim(self) -> None:
        grouped = [
            ({"registered_at": "2026-07-01T00:00:00Z", "delete_after": "2026-08-15T00:00:00Z"}, "governing"),
            ({"registered_at": "2026-07-17T00:00:00Z", "delete_after": "2026-09-01T00:00:00Z"}, "pending-earlier"),
            ({"registered_at": "2026-07-18T00:00:00Z", "delete_after": "2026-10-01T00:00:00Z"}, "pending-later"),
        ]
        current = capability_contract._parsed_timestamp("2026-08-15T00:00:00Z", "test clock")
        expected = capability_contract._parsed_timestamp("2026-08-17T00:00:00Z", "test deadline")
        self.assertEqual(
            capability_retention._effective_retention_deadline(grouped, {"governing"}, current),
            expected,
        )
        self.assertEqual(
            capability_retention._effective_retention_deadline(grouped[1:], set(), current),
            expected,
        )

    def test_repository_binding_requires_a_clean_committed_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repository = Path(tmp) / "repository"
            repository.mkdir()
            commands = (
                ["git", "init", "-q"],
                ["git", "config", "user.name", "G56R Fixture"],
                ["git", "config", "user.email", "git@github.com"],
                ["git", "config", "commit.gpgsign", "false"],
            )
            for _git, *arguments in commands:
                subprocess.run(["git", *arguments], cwd=repository, check=True, capture_output=True)
            tracked = repository / "tracked.txt"
            tracked.write_text("committed\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repository, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=repository, check=True, capture_output=True)
            binding = capabilities.repository_binding_from_checkout(repository)
            self.assertEqual(binding["revision"], subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repository, check=True,
                capture_output=True, text=True,
            ).stdout.strip())
            (repository / "untracked.txt").write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be clean"):
                capabilities.repository_binding_from_checkout(repository)
            resolved = "a" * 40
            responses = [
                subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                subprocess.CompletedProcess([], 0, stdout=f"{resolved}\n", stderr=""),
                subprocess.CompletedProcess([], 0, stdout=f"{'b' * 40}\n", stderr=""),
                subprocess.CompletedProcess([], 0, stdout=f"{'c' * 40}\n", stderr=""),
            ]
            with mock.patch.object(capability_observations.subprocess, "run", side_effect=responses) as run:
                with self.assertRaisesRegex(ValueError, "changed during collection binding"):
                    capabilities.repository_binding_from_checkout(repository)
            self.assertEqual(run.call_args_list[2].args[0][-1], f"{resolved}^{{tree}}")

    def test_json_inputs_executable_hashing_and_publication_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            duplicate = root / "duplicate.json"
            duplicate.write_bytes(b'{"key":1,"key":2}\n')
            with self.assertRaisesRegex(ValueError, "duplicate JSON object key"):
                capability_publish_io._read(duplicate)
            invalid_utf8 = root / "invalid-utf8.json"
            invalid_utf8.write_bytes(b'{"key":"\xff"}\n')
            with self.assertRaisesRegex(ValueError, "strict UTF-8 JSON"):
                capability_publish_io._read(invalid_utf8)
            for index, constant in enumerate(("NaN", "Infinity", "-Infinity")):
                nonfinite = root / f"nonfinite-{index}.json"
                nonfinite.write_text(f'{{"value":{constant}}}\n', encoding="utf-8")
                with self.subTest(constant=constant), self.assertRaisesRegex(ValueError, "non-JSON numeric constant"):
                    capability_publish_io._read(nonfinite)
                with self.assertRaisesRegex(ValueError, "non-JSON numeric constant"):
                    capability_publish_io._read(nonfinite, require_canonical=True)
            deeply_nested = root / "deeply-nested.json"
            deeply_nested.write_bytes(b"[" * 65 + b"0" + b"]" * 65)
            with self.assertRaisesRegex(ValueError, "maximum nesting depth"):
                capability_publish_io._read(deeply_nested)
            node_heavy = root / "node-heavy.json"
            node_heavy.write_bytes(b'{"values":[1,2]}')
            with mock.patch.object(
                capability_contract, "CAPABILITY_JSON_MAX_TOTAL_NODES", 4,
            ), self.assertRaisesRegex(ValueError, "maximum node count"):
                capability_publish_io._read(node_heavy)
            with mock.patch.object(
                capability_contract.json, "loads", side_effect=RecursionError("too deep"),
            ), self.assertRaisesRegex(ValueError, "strict UTF-8 JSON"):
                capability_publish_io._read(node_heavy)
            with self.assertRaises(ValueError):
                capabilities.canonical_bytes({"value": float("nan")})
            noncanonical = root / "noncanonical.json"
            noncanonical.write_text('{"b": 1, "a": 2}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not canonical"):
                capability_publish_io._read(noncanonical, require_canonical=True)
            canonical = root / "canonical.json"
            original_fsync = capability_private.os.fsync
            with mock.patch.object(capability_private.os, "fsync", wraps=original_fsync) as fsync:
                capability_private._write(canonical, {"b": 1, "a": 2}, append_only=True)
            self.assertGreaterEqual(fsync.call_count, 3)
            self.assertFalse(any(root.glob(".g56r-002-*")))
            self.assertEqual(capability_publish_io._read(canonical, require_canonical=True), {"a": 2, "b": 1})
            crash_payload = capabilities.canonical_bytes({"recovered": True}) + b"\n"
            crash_temporary = root / f".g56r-002-{'a' * 32}"
            crash_target = root / "crash-recovered.json"
            crash_temporary.write_bytes(crash_payload); crash_temporary.chmod(0o600)
            os.link(crash_temporary, crash_target); capability_private._fsync_directory(root)
            with self.assertRaises(FileExistsError):
                capability_private._write(crash_target, {"recovered": True}, append_only=True)
            self.assertFalse(crash_temporary.exists())
            self.assertEqual(crash_target.stat().st_nlink, 1)
            self.assertEqual(crash_target.read_bytes(), crash_payload)
            private_recovery_root = root / "raw-recovery"
            private_recovery_root.mkdir(mode=0o700)
            private_payload = b'[{"capture":"recovered"}]\n'
            private_temporary = private_recovery_root / f".g56r-002-{'b' * 32}"
            private_target = private_recovery_root / f"{capabilities.digest(private_payload).removeprefix('sha256:')}.json"
            private_temporary.write_bytes(private_payload); private_temporary.chmod(0o600)
            os.link(private_temporary, private_target); capability_private._fsync_directory(private_recovery_root)
            capabilities.validate_raw_evidence_root(private_recovery_root, ROOT)
            self.assertFalse(private_temporary.exists())
            self.assertEqual(private_target.stat().st_nlink, 1)
            self.assertEqual(private_target.read_bytes(), private_payload)
            replacement = root / "replacement.json"
            replacement.write_bytes(b'{}\n')
            replacement_metadata = replacement.stat(); original_stat = capability_io.os.stat
            def replaced_path_stat(path: object, *args: object, **kwargs: object) -> os.stat_result:
                if path == "canonical.json" and kwargs.get("dir_fd") is not None:
                    return replacement_metadata
                return original_stat(path, *args, **kwargs)
            with mock.patch.object(capability_io.os, "stat", side_effect=replaced_path_stat):
                with self.assertRaisesRegex(ValueError, "pathname changed"):
                    capability_publish_io._read_bounded_regular_file(canonical)
            initial = canonical.stat()
            changed_ctime = mock.Mock(
                st_mode=initial.st_mode, st_dev=initial.st_dev, st_ino=initial.st_ino,
                st_size=initial.st_size, st_mtime_ns=initial.st_mtime_ns,
                st_ctime_ns=initial.st_ctime_ns + 1, st_nlink=initial.st_nlink,
            )
            original_fstat = capability_io.os.fstat; regular_fstats = 0
            def changed_file_fstat(descriptor: int) -> os.stat_result:
                nonlocal regular_fstats
                metadata = original_fstat(descriptor)
                if stat.S_ISREG(metadata.st_mode) and metadata.st_ino == initial.st_ino:
                    regular_fstats += 1
                    if regular_fstats == 2: return changed_ctime
                return metadata
            with mock.patch.object(capability_io.os, "fstat", side_effect=changed_file_fstat):
                with self.assertRaisesRegex(ValueError, "changed while"):
                    capability_publish_io._read_bounded_regular_file(canonical)
            with mock.patch.object(capability_io, "PRIVATE_REFRESH_MAX_BYTES", 4):
                with self.assertRaisesRegex(ValueError, "exceeds the maximum size"):
                    capability_publish_io._read_bounded_regular_file(canonical)
            with self.assertRaises(FileExistsError):
                capability_private._write(canonical, {"replacement": True}, append_only=True)
            self.assertEqual(capability_publish_io._read(canonical, require_canonical=True), {"a": 2, "b": 1})
            executable = root / "large-client"
            executable.write_bytes(b"fixture-client" * 200000)
            self.assertEqual(capabilities.digest_regular_file(executable), capabilities.digest(executable.read_bytes()))
            executable_replacement = root / "replacement-client"
            executable_replacement.write_bytes(b"different-client")
            with mock.patch.object(capability_io.os, "stat", return_value=executable_replacement.stat()):
                with self.assertRaisesRegex(ValueError, "pathname changed"):
                    capabilities.digest_regular_file(executable)
            executable_before = executable.stat()
            executable_after = mock.Mock(
                st_mode=executable_before.st_mode, st_dev=executable_before.st_dev,
                st_ino=executable_before.st_ino, st_size=executable_before.st_size,
                st_mtime_ns=executable_before.st_mtime_ns,
                st_ctime_ns=executable_before.st_ctime_ns + 1,
            )
            with mock.patch.object(capability_io.os, "fstat", side_effect=[executable_before, executable_after]):
                with self.assertRaisesRegex(ValueError, "changed while hashing"):
                    capabilities.digest_regular_file(executable)
            growing = root / "growing-client"
            growing.write_bytes(b"grow")
            growing_before = growing.stat()
            growing_after = mock.Mock(
                st_mode=growing_before.st_mode, st_dev=growing_before.st_dev,
                st_ino=growing_before.st_ino, st_size=growing_before.st_size + 1,
                st_mtime_ns=growing_before.st_mtime_ns,
                st_ctime_ns=growing_before.st_ctime_ns + 1,
            )
            with mock.patch.object(capability_io.os, "fstat", side_effect=[growing_before, growing_after]), mock.patch.object(
                capability_io.os, "read", side_effect=lambda descriptor, size: b"x" * size,
            ) as growing_read:
                with self.assertRaisesRegex(ValueError, "changed while hashing"):
                    capabilities.digest_regular_file(growing)
            self.assertEqual(growing_read.call_count, 1)
            private_output = root / "private-output.json"
            with mock.patch.object(capability_io.os, "name", "nt"), mock.patch.object(capability_io.os, "fchmod") as fchmod:
                with self.assertRaisesRegex(ValueError, "not supported on Windows"):
                    capability_private._write(private_output, {"private": True}, private=True)
            fchmod.assert_not_called()
            private_output, private_parent_identity = capability_private._private_external_file_binding(
                private_output, ROOT, "test private output", output=True,
            )
            capability_private._write(
                private_output, {"private": True}, private=True,
                expected_parent_identity=private_parent_identity,
            )
            self.assertEqual(capability_publish_io._read(private_output), {"private": True})
            if hasattr(os, "mkfifo"):
                fifo = root / "client-fifo"
                os.mkfifo(fifo)
                with self.assertRaisesRegex(ValueError, "regular file"):
                    capabilities.digest_regular_file(fifo)

    @unittest.skipUnless(capabilities.HAS_DESCRIPTOR_RELATIVE_IO, "descriptor-relative I/O required")
    def test_private_write_refuses_replaced_validated_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_parent = root / "private"
            private_parent.mkdir(mode=0o700)
            target, parent_identity = capability_private._private_external_file_binding(
                private_parent / "secret.json", ROOT, "test private output", output=True,
            )
            moved_parent = root / "validated-parent"
            original_assert = capability_private._assert_private_directory_current
            swapped = False

            def swap_before_commit(path: Path, descriptor: int, expected_identity: object) -> None:
                nonlocal swapped
                if not swapped:
                    Path(path).rename(moved_parent)
                    Path(path).mkdir(mode=0o700)
                    swapped = True
                original_assert(path, descriptor, expected_identity)

            with mock.patch.object(
                capability_private, "_assert_private_directory_current", side_effect=swap_before_commit,
            ), self.assertRaisesRegex(ValueError, "parent changed"):
                capability_private._write_private_bytes(
                    target, b"secret\n", expected_parent_identity=parent_identity,
                )
            self.assertTrue(swapped)
            self.assertFalse(target.exists())
            self.assertEqual(list(private_parent.iterdir()), [])
            self.assertEqual(list(moved_parent.iterdir()), [])
            public_parent = root / "public"
            public_parent.mkdir()
            public_target = public_parent / "published.json"
            moved_public_parent = root / "validated-public"
            public_swapped = False

            def swap_public_parent(path: Path, descriptor: int, expected_identity: object) -> None:
                nonlocal public_swapped
                if Path(path) == public_parent and not public_swapped:
                    public_parent.rename(moved_public_parent)
                    public_parent.mkdir()
                    public_swapped = True
                original_assert(path, descriptor, expected_identity)

            with mock.patch.object(
                capability_private, "_assert_private_directory_current", side_effect=swap_public_parent,
            ), self.assertRaisesRegex(ValueError, "parent changed"):
                capability_private._write(public_target, {"published": True}, append_only=True)
            self.assertTrue(public_swapped)
            self.assertEqual(list(public_parent.iterdir()), [])
            self.assertEqual(list(moved_public_parent.iterdir()), [])
            substituted_parent = root / "substituted-public"
            substituted_parent.mkdir()
            substituted_target = substituted_parent / "published.json"
            original_link = capability_private.os.link

            def substitute_linked_target(source: str, destination: str, **kwargs: object) -> None:
                original_link(source, destination, **kwargs)
                destination_descriptor = kwargs["dst_dir_fd"]
                os.unlink(destination, dir_fd=destination_descriptor)
                replacement_descriptor = os.open(
                    destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600, dir_fd=destination_descriptor,
                )
                try:
                    os.write(replacement_descriptor, b'{"substituted":true}\n')
                finally:
                    os.close(replacement_descriptor)

            with mock.patch.object(
                capability_private.os, "link", side_effect=substitute_linked_target,
            ), self.assertRaisesRegex(ValueError, "does not match its temporary file"):
                capability_private._write(substituted_target, {"published": True}, append_only=True)
            self.assertEqual(substituted_target.read_bytes(), b'{"substituted":true}\n')

    @unittest.skipUnless(capabilities.HAS_DESCRIPTOR_RELATIVE_IO, "descriptor-relative I/O required")
    def test_retention_lock_releases_descriptor_after_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_root = Path(tmp) / "raw"
            raw_root.mkdir(mode=0o700)
            raw_identity = capability_io._stable_directory_identity(
                os.stat(raw_root, follow_symlinks=False),
            )
            original_assert = capability_private._assert_private_directory_current
            assertions = 0

            def fail_release_validation(path: Path, descriptor: int, expected_identity: object) -> None:
                nonlocal assertions
                assertions += 1
                if assertions == 2:
                    raise ValueError("simulated release validation failure")
                original_assert(path, descriptor, expected_identity)

            with mock.patch.object(
                capability_retention_records, "_assert_private_directory_current",
                side_effect=fail_release_validation,
            ), self.assertRaisesRegex(ValueError, "release validation failure"):
                with capability_retention_records._retention_lock(raw_root, raw_identity):
                    pass
            with capability_retention_records._retention_lock(raw_root, raw_identity):
                pass

    @unittest.skipUnless(capabilities.HAS_DESCRIPTOR_RELATIVE_IO, "descriptor-relative I/O required")
    def test_private_record_loader_rejects_directory_races(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_root = Path(tmp) / "raw"
            raw_root.mkdir(mode=0o700)
            raw, raw_identity = capability_private._validated_raw_evidence_root_binding(
                raw_root, ROOT,
            )
            records, records_identity = capability_retention_records._private_record_directory(
                raw, capabilities.RETENTION_RECORDS_DIR, raw_identity,
            )
            capability_retention_records._store_private_record(
                records, {"schema_version": "test-record.v1", "value": "first"},
                ROOT, records_identity,
            )
            moved_records = Path(tmp) / "moved-records"
            original_listdir = capability_io.os.listdir
            replaced = False

            def replace_after_snapshot(descriptor: int) -> list[str]:
                nonlocal replaced
                names = original_listdir(descriptor)
                if not replaced:
                    records.rename(moved_records)
                    records.mkdir(mode=0o700)
                    replaced = True
                return names

            with mock.patch.object(
                capability_io.os, "listdir", side_effect=replace_after_snapshot,
            ), self.assertRaisesRegex(ValueError, "directory changed"):
                capability_retention_records._load_private_records(
                    records, ROOT, "retention record",
                )
            self.assertTrue(replaced)
            records.rmdir()
            moved_records.rename(records)
            extra = {"schema_version": "test-record.v1", "value": "second"}
            extra_bytes = capabilities.canonical_bytes(extra) + b"\n"
            extra_path = records / f"{capabilities.digest(extra_bytes).removeprefix('sha256:')}.json"
            snapshots = 0

            def add_after_snapshot(descriptor: int) -> list[str]:
                nonlocal snapshots
                names = original_listdir(descriptor)
                snapshots += 1
                if snapshots == 1:
                    extra_path.write_bytes(extra_bytes)
                    extra_path.chmod(0o600)
                return names

            with mock.patch.object(
                capability_io.os, "listdir", side_effect=add_after_snapshot,
            ), self.assertRaisesRegex(ValueError, "directory changed"):
                capability_retention_records._load_private_records(
                    records, ROOT, "retention record",
                )

    @unittest.skipUnless(capabilities.HAS_DESCRIPTOR_RELATIVE_IO, "descriptor-relative I/O required")
    def test_deletion_recovery_refuses_replaced_raw_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_parent = Path(tmp)
            raw_root = private_parent / "raw"
            raw_root.mkdir(mode=0o700)
            payload = b"private evidence\n"
            evidence_digest = capabilities.digest(payload)
            target = raw_root / f"{evidence_digest.removeprefix('sha256:')}.json"
            target.write_bytes(payload)
            target.chmod(0o600)
            raw, raw_identity = capability_private._validated_raw_evidence_root_binding(raw_root, ROOT)
            target = raw / target.name
            deletion_directory, deletion_directory_identity = capability_retention_records._private_record_directory(
                raw, capabilities.DELETION_RECORDS_DIR, raw_identity,
            )
            deletion_record = {
                "schema_version": "raw-evidence-deletion.v2",
                "completion_proof": "post-unlink-nlink-zero-rehashed-v1",
                "raw_evidence_digest": evidence_digest,
                "retention_record_digests": [capabilities.digest(b"retention record")],
                "deletion_intent_digest": capabilities.digest(b"deletion intent"),
                "delete_after": "2026-08-15T00:00:00Z",
                "deleted_at": "2026-08-15T00:00:00Z",
            }
            moved_root = private_parent / "validated-raw"
            original_unlink = capability_retention._unlink_descriptor_relative

            def unlink_then_replace(filename: str, parent_descriptor: int) -> None:
                original_unlink(filename, parent_descriptor)
                raw_root.rename(moved_root)
                raw_root.mkdir(mode=0o700)
                raise OSError("simulated failure after unlink")

            with mock.patch.object(
                capability_retention, "_unlink_descriptor_relative", side_effect=unlink_then_replace,
            ), self.assertRaisesRegex(ValueError, "parent changed"):
                capability_retention._delete_single_link_private_file(
                    target, raw, evidence_digest, raw_identity,
                    expected_target_identity=capability_retention._deletion_intent_file_identity(target.stat()),
                    deletion_record=deletion_record,
                    deletion_directory=deletion_directory,
                    deletion_directory_identity=deletion_directory_identity,
                    repository_root=ROOT,
                )
            self.assertFalse(target.exists())
            self.assertEqual(list(raw_root.iterdir()), [])
            self.assertEqual(
                sorted(path.name for path in moved_root.iterdir()),
                sorted([capabilities.DELETION_INTENTS_DIR, capabilities.DELETION_RECORDS_DIR]),
            )
            self.assertEqual(list((moved_root / capabilities.DELETION_RECORDS_DIR).iterdir()), [])
            self.assertEqual(len(list((moved_root / capabilities.DELETION_INTENTS_DIR).iterdir())), 1)

    @unittest.skipUnless(capabilities.HAS_DESCRIPTOR_RELATIVE_IO, "descriptor-relative I/O required")
    def test_deletion_recovery_never_restores_after_journaled_completion_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_root = Path(tmp) / "raw"
            raw_root.mkdir(mode=0o700)
            payload = b"private evidence\n"
            evidence_digest = capabilities.digest(payload)
            target = raw_root / f"{evidence_digest.removeprefix('sha256:')}.json"
            target.write_bytes(payload)
            target.chmod(0o600)
            raw, raw_identity = capability_private._validated_raw_evidence_root_binding(
                raw_root, ROOT,
            )
            target = raw / target.name
            deletion_directory, deletion_directory_identity = (
                capability_retention_records._private_record_directory(
                    raw, capabilities.DELETION_RECORDS_DIR, raw_identity,
                )
            )
            deletion_record = {
                "schema_version": "raw-evidence-deletion.v2",
                "completion_proof": "post-unlink-nlink-zero-rehashed-v1",
                "raw_evidence_digest": evidence_digest,
                "retention_record_digests": [capabilities.digest(b"retention record")],
                "deletion_intent_digest": capabilities.digest(b"deletion intent"),
                "delete_after": "2026-08-15T00:00:00Z",
                "deleted_at": "2026-08-15T00:00:00Z",
            }
            def fail_completion(*_args: object, **_kwargs: object) -> None:
                raise ValueError("simulated completion persistence failure")

            with mock.patch.object(
                capability_retention, "_store_staged_recovery_completion",
                side_effect=fail_completion,
            ), mock.patch.object(
                capability_retention, "_write_private_bytes_at",
                side_effect=AssertionError("raw bytes must not be republished after v3"),
            ), self.assertRaisesRegex(ValueError, "completion persistence failure"):
                capability_retention._delete_single_link_private_file(
                    target, raw, evidence_digest, raw_identity,
                    expected_target_identity=capability_retention._deletion_intent_file_identity(target.stat()),
                    deletion_record=deletion_record,
                    deletion_directory=deletion_directory,
                    deletion_directory_identity=deletion_directory_identity,
                    repository_root=ROOT,
                )
            self.assertFalse(target.exists())
            self.assertFalse(any(
                path.name.startswith(".g56r-002-") for path in raw_root.iterdir()
            ))


class TreatmentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_json(TREATMENT_FIXTURE_PATH)

    def rebound(self, bundle: dict) -> dict:
        bundle["treatment_contract_digest"] = treatment.schema_file_digest()
        bundle["telemetry_profile_id"] = treatment.telemetry_profile_id(
            bundle["schema_version"], bundle["telemetry_profile"], bundle["treatment_contract_digest"]
        )
        return bundle

    def assert_bundle_invalid(self, bundle: dict, message: str = "") -> None:
        with self.assertRaises(ValueError, msg=message):
            treatment.validate_treatment_bundle(self.rebound(bundle))

    def assert_bundle_not_proven(
        self, bundle: dict, expected_disposition: str, failure_codes: list[str], message: str = "",
    ) -> None:
        declare_treatment_result(bundle, failure_codes, expected_disposition, sorted(failure_codes))
        validated = treatment.validate_treatment_bundle(self.rebound(bundle))
        self.assertEqual(validated["treatment_traces"][0]["treatment_disposition"], expected_disposition, message)
        self.assertNotEqual(expected_disposition, "proven", message)

    def assert_reroute_hard_failed(self, bundle: dict, message: str = "", *, trusted: dict[str, dict] | None = None) -> None:
        declare_reroute_result(bundle, trusted)
        validated = treatment.validate_treatment_bundle(
            self.rebound(bundle), trusted_qualification_evidence=trusted or {}
        )
        self.assertEqual(validated["treatment_traces"][0]["treatment_disposition"], "hard_fail", message)

    def test_telemetry_inventory_and_null_semantics(self) -> None:
        validated = treatment.validate_treatment_bundle(copy.deepcopy(self.bundle))
        self.assertEqual(set(treatment.CLASSIFICATIONS), {
            "stable_native", "experimental_native", "derived_from_controlled_configuration",
            "conditional", "unavailable", "not_applicable", "undocumented",
        })
        self.assertEqual({entry["classification"] for entry in validated["telemetry_profile"]}, set(treatment.CLASSIFICATIONS))
        actual_inventory = {(entry["surface"], entry["field_path"]) for entry in validated["telemetry_profile"]}
        self.assertEqual(actual_inventory, EXPECTED_TELEMETRY_INVENTORY)
        self.assertEqual(treatment.TELEMETRY_INVENTORY, EXPECTED_TELEMETRY_INVENTORY)
        client = validated["controlled_environments"][0]["client_identity_id"]
        omitted = treatment.profile_entry(validated["telemetry_profile"], client, "cli", "assignment.model")
        self.assertEqual(omitted["classification"], "undocumented")
        self.assertEqual(omitted["permitted_claims"], [])
        trace = validated["treatment_traces"][0]
        self.assertIsNone(trace["supported_effective_model"])
        self.assertIsNone(trace["supported_effective_effort"])
        forged = copy.deepcopy(self.bundle)
        obs = next(item for item in forged["treatment_traces"][0]["observations"] if item["field_path"] == "terminal.acceptance")
        obs["value"] = False
        with self.assertRaisesRegex(ValueError, "wrong treatment schema type"):
            treatment.validate_treatment_bundle(self.rebound(forged))
        duplicate = copy.deepcopy(self.bundle)
        duplicate["telemetry_profile"].append(copy.deepcopy(duplicate["telemetry_profile"][0]))
        with self.assertRaisesRegex(ValueError, "telemetry_profile must contain unique items"):
            treatment.validate_treatment_bundle(self.rebound(duplicate))

    def test_profile_authority_and_typed_observation_states(self) -> None:
        profile_mutations = [
            ("app_server", "discovery.models", "official_source_ledger_id", None),
            ("app_server", "discovery.models", "official_source_ledger_id", "OPENAI-DOC-999"),
            ("app_server", "discovery.models", "official_source_ledger_id", "OPENAI-DOC-001"),
            ("app_server", "assignment.model", "permitted_claims", ["effective_treatment"]),
            ("app_server", "reroute.events", "condition", "event-only capture"),
            ("app_server", "terminal.acceptance", "permitted_claims", ["observed_value"]),
            ("interactive_picker", "parent.graph", "condition", None),
            ("cli", "route.supported_effective_route_id", "official_source_ledger_id", "OPENAI-DOC-006"),
            ("app_server", "discovery.models", "completeness_rule", "no_authority"),
            ("app_server", "discovery.models", "observation_state_rules", {
                "allowed_states": ["observed_value", "unavailable"],
                "value_rule": "typed_when_observed", "evidence_rule": "required_when_present",
            }),
        ]
        for surface, field_path, field, value in profile_mutations:
            with self.subTest(profile=f"{surface}:{field_path}:{field}"):
                bundle = copy.deepcopy(self.bundle)
                entry = next(item for item in bundle["telemetry_profile"] if item["surface"] == surface and item["field_path"] == field_path)
                entry[field] = value
                self.assert_bundle_invalid(bundle)

        split_owner = copy.deepcopy(self.bundle)
        moved = next(item for item in split_owner["telemetry_profile"] if item["field_path"] == "treatment.sandbox")
        moved["client_identity_id"] = "sha256:" + "0" * 64
        split_owner["treatment_traces"][0]["observations"] = [
            item for item in split_owner["treatment_traces"][0]["observations"]
            if item["field_path"] != "treatment.sandbox"
        ]
        with self.assertRaisesRegex(ValueError, "exactly one client identity owner"):
            treatment.validate_treatment_bundle(self.rebound(split_owner))

        observation_mutations = [
            ("discovery.models", "value", None),
            ("discovery.models", "value", "unknown"),
            ("discovery.models", "evidence_ref", None),
            ("discovery.models", "captured_at", None),
            ("route.supported_effective_route_id", "value", "fixture-route"),
            ("route.supported_effective_route_id", "observation_state", "unavailable"),
            ("treatment.failures", "value", []),
            ("treatment.failures", "evidence_ref", "fixture://forged"),
            ("terminal.acceptance", "value", False),
            ("terminal.acceptance", "observation_state", "observed_value"),
        ]
        for field_path, field, value in observation_mutations:
            with self.subTest(observation=f"{field_path}:{field}"):
                bundle = copy.deepcopy(self.bundle)
                observation = next(item for item in bundle["treatment_traces"][0]["observations"] if item["field_path"] == field_path)
                observation[field] = value
                self.assert_bundle_invalid(bundle)

        missing = copy.deepcopy(self.bundle)
        missing["treatment_traces"][0]["configured_route_proof"] = None
        observation = next(item for item in missing["treatment_traces"][0]["observations"] if item["field_path"] == "route.supported_effective_route_id")
        observation.update({"observation_state": "missing", "value": None, "evidence_ref": None, "captured_at": None})
        missing["treatment_traces"][0]["treatment_disposition"] = "proven"
        with self.assertRaisesRegex(ValueError, "declared treatment disposition"):
            treatment.validate_treatment_bundle(self.rebound(copy.deepcopy(missing)))
        declare_treatment_result(
            missing, ["effective_treatment_unknown"], "unknown", ["effective_treatment_unknown"]
        )
        result = treatment.validate_treatment_bundle(self.rebound(missing))
        self.assertEqual(result["treatment_traces"][0]["treatment_disposition"], "unknown")
        self.assertIsNone(result["treatment_traces"][0]["supported_effective_model"])
        self.assertIsNone(result["treatment_traces"][0]["supported_effective_effort"])

    def test_profile_classification_authority_rejects_semantically_consistent_rebinding(self) -> None:
        classification_mutations = [
            ("assignment.model", "stable_native"),
            ("assignment.named_agent", "stable_native"),
            ("route.supported_effective_route_id", "stable_native"),
            ("treatment.loaded_skills_mcp_tools", "stable_native"),
            ("discovery.models", "derived_from_controlled_configuration"),
            ("lifecycle.compaction", "stable_native"),
        ]
        for field_path, classification in classification_mutations:
            with self.subTest(field_path=field_path, classification=classification):
                bundle = copy.deepcopy(self.bundle)
                entry = next(item for item in bundle["telemetry_profile"] if item["surface"] == "app_server" and item["field_path"] == field_path)
                entry.update({
                    "classification": classification,
                    "condition": None,
                    "completeness_rule": treatment.COMPLETENESS_BY_CLASS[classification],
                    "observation_state_rules": {
                        "allowed_states": ["observed_value", "explicit_null", "missing"],
                        "value_rule": "typed_when_observed", "evidence_rule": "required_when_present",
                    },
                    "permitted_claims": [treatment.CLAIM_BY_CLASS[classification]],
                })
                with self.assertRaisesRegex(ValueError, "exact field-level classification authority"):
                    treatment.validate_treatment_bundle(self.rebound(bundle))

    def test_profile_conditions_and_prohibited_claims_are_exact_authority(self) -> None:
        mutations = [
            ("reroute.events", "condition", "caller-controlled condition"),
            ("assignment.model", "condition", "unexpected condition"),
            ("assignment.model", "prohibited_claims", ["configured_as_effective"]),
            ("terminal.outcome", "prohibited_claims", ["effective_treatment"]),
        ]
        for field_path, field, value in mutations:
            with self.subTest(field_path=field_path, field=field):
                bundle = copy.deepcopy(self.bundle)
                entry = next(item for item in bundle["telemetry_profile"] if item["surface"] == "app_server" and item["field_path"] == field_path)
                entry[field] = value
                self.assert_bundle_invalid(bundle)

    def test_cli_and_picker_traces_cannot_retain_unprofiled_top_level_claims(self) -> None:
        cases = [
            ("cli", "route.supported_effective_route_id", "undocumented"),
            ("interactive_picker", "parent.graph", "not_applicable"),
        ]
        for surface, field_path, state in cases:
            with self.subTest(surface=surface):
                bundle = copy.deepcopy(self.bundle)
                environment = bundle["controlled_environments"][0]
                environment["surface"] = surface
                environment["controlled_environment_id"] = treatment.content_id(environment, "controlled_environment_id")
                trace = bundle["treatment_traces"][0]
                trace["surface"] = surface
                trace["controlled_environment_id"] = environment["controlled_environment_id"]
                trace["configured_route_proof"] = None
                trace["service_reroute_events"] = []
                trace["reroute_destination_assessments"] = []
                trace["observations"] = [{
                    "field_path": field_path, "observation_state": state, "value": None,
                    "evidence_ref": None, "captured_at": None,
                }]
                with self.assertRaisesRegex(ValueError, "cannot retain a top-level claim"):
                    treatment.validate_treatment_bundle(self.rebound(rebind_treatment_owners(bundle)))

    def test_complete_reroute_monitoring_makes_configured_proof_reachable(self) -> None:
        bundle = copy.deepcopy(self.bundle)
        profile = next(item for item in bundle["telemetry_profile"] if item["surface"] == "app_server" and item["field_path"] == "reroute.events")
        trace = bundle["treatment_traces"][0]
        self.assertEqual(profile["classification"], "stable_native")
        self.assertEqual(profile["completeness_rule"], "complete_capture")
        self.assertTrue(trace["configured_route_proof"]["reroute_monitoring_complete"])
        self.assertEqual(trace["service_reroute_events"], [])
        observation = next(item for item in trace["observations"] if item["field_path"] == "reroute.events")
        observation.update({
            "observation_state": "observed_value", "value": [],
            "evidence_ref": "fixture://trace/reroute-monitoring", "captured_at": "2026-07-17T04:01:00Z",
        })
        declare_treatment_result(
            bundle, [], "proven", ["configured_route_proof_and_complete_reroute_monitoring"],
        )
        validated = treatment.validate_treatment_bundle(self.rebound(bundle))
        trace = validated["treatment_traces"][0]
        self.assertEqual(trace["treatment_disposition"], "proven")
        self.assertEqual(trace["disposition_reasons"], ["configured_route_proof_and_complete_reroute_monitoring"])

    def test_effective_model_and_effort_require_profiled_observation_authority(self) -> None:
        for field, value in (
            ("supported_effective_model", "fabricated-model"),
            ("supported_effective_effort", "fabricated-effort"),
        ):
            with self.subTest(field=field):
                bundle = copy.deepcopy(self.bundle)
                bundle["treatment_traces"][0][field] = value
                self.assert_bundle_invalid(bundle)

        fabricated = copy.deepcopy(self.bundle)
        trace = fabricated["treatment_traces"][0]
        trace["supported_effective_model"] = "fabricated-model"
        observation = next(item for item in trace["observations"] if item["field_path"] == "assignment.supported_effective_model")
        observation.update({
            "observation_state": "observed_value", "value": "fabricated-model",
            "evidence_ref": "fixture://forged/effective-model", "captured_at": "2026-07-17T04:01:00Z",
        })
        declare_treatment_result(
            fabricated, ["model_mismatch", "effective_treatment_unknown"], "hard_fail",
            ["effective_treatment_unknown", "model_mismatch"],
        )
        validated = treatment.validate_treatment_bundle(self.rebound(fabricated))
        self.assertEqual(validated["treatment_traces"][0]["treatment_disposition"], "hard_fail")

    def test_manifest_null_effort_remains_unknown_without_complete_monitoring(self) -> None:
        trace = self.bundle["treatment_traces"][0]
        route = treatment._canonical_routes(load_json(MANIFEST_PATH))[trace["assigned_route_id"]]
        self.assertIn("effort", route)
        self.assertIsNone(route["effort"])
        validated = treatment.validate_treatment_bundle(copy.deepcopy(self.bundle))
        self.assertEqual(validated["treatment_traces"][0]["treatment_disposition"], "unknown")
        self.assertIsNone(validated["treatment_traces"][0]["supported_effective_effort"])

        arbitrary = copy.deepcopy(self.bundle)
        arbitrary["treatment_traces"][0]["requested_effort"] = "arbitrary-effort"
        arbitrary["fixture_provenance"]["expected_dispositions"][0]["treatment_disposition"] = "hard_fail"
        self.assert_bundle_not_proven(
            arbitrary, "hard_fail",
            ["effort_mismatch", "client_or_override_mismatch", "effective_treatment_unknown"],
        )

    def test_configured_route_proof_cannot_self_assert_effective_treatment(self) -> None:
        mutations = [
            (("proof_id",), treatment.digest(b"forged-proof")),
            (("profile_entry_key", "field_path"), "discovery.models"),
            (("named_agent",), "different-agent"),
            (("model",), "different-model"),
            (("effort",), "low"),
            (("candidate_route_id",), "different-route"),
            (("agent_contract_id",), "different-contract"),
            (("instruction_hash",), "sha256:" + "0" * 64),
            (("configuration_hash",), "sha256:" + "0" * 64),
            (("client_identity_id",), "sha256:" + "0" * 64),
            (("controlled_overrides", "model"), "different-model"),
            (("launch_id",), ""),
            (("consumption_evidence_digest",), "invalid"),
            (("reroute_monitoring_complete",), False),
        ]
        for path, value in mutations:
            with self.subTest(path=".".join(path)):
                bundle = copy.deepcopy(self.bundle)
                target = bundle["treatment_traces"][0]["configured_route_proof"]
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = value
                if path == ("proof_id",):
                    with self.assertRaisesRegex(ValueError, "proof ID is not content addressed"):
                        treatment.validate_treatment_bundle(self.rebound(bundle))
                elif path in {("launch_id",), ("consumption_evidence_digest",)}:
                    self.assert_bundle_invalid(bundle)
                else:
                    proof = bundle["treatment_traces"][0]["configured_route_proof"]
                    proof["proof_id"] = treatment.content_id(proof, "proof_id")
                    expected = "unknown" if path == ("reroute_monitoring_complete",) else "hard_fail"
                    code_by_path = {
                        ("profile_entry_key", "field_path"): "configuration_mismatch",
                        ("named_agent",): "agent_mismatch",
                        ("model",): "model_mismatch",
                        ("effort",): "effort_mismatch",
                        ("candidate_route_id",): "configuration_mismatch",
                        ("agent_contract_id",): "agent_mismatch",
                        ("instruction_hash",): "configuration_mismatch",
                        ("configuration_hash",): "configuration_mismatch",
                        ("client_identity_id",): "client_or_override_mismatch",
                        ("controlled_overrides", "model"): "client_or_override_mismatch",
                    }
                    failure_codes = (
                        ["effective_treatment_unknown"]
                        if path == ("reroute_monitoring_complete",)
                        else [code_by_path[path], "effective_treatment_unknown"]
                    )
                    self.assert_bundle_not_proven(bundle, expected, failure_codes)
        validated = treatment.validate_treatment_bundle(copy.deepcopy(self.bundle))
        trace = validated["treatment_traces"][0]
        self.assertEqual(trace["treatment_disposition"], "unknown")
        self.assertIsNone(trace["supported_effective_model"])
        self.assertIsNone(trace["supported_effective_effort"])

    def test_observed_supported_route_makes_effective_evidence_reachable(self) -> None:
        bundle = copy.deepcopy(self.bundle)
        trace = bundle["treatment_traces"][0]
        route_id = trace["assigned_route_id"]
        trace["configured_route_proof"] = None
        resolution = bundle["route_resolutions"][0]
        resolution["supported_effective_route_id"] = route_id
        observation = next(
            item for item in trace["observations"]
            if item["field_path"] == "route.supported_effective_route_id"
        )
        observation.update({
            "observation_state": "observed_value", "value": route_id,
            "evidence_ref": "fixture://trace/effective-route", "captured_at": "2026-07-17T04:01:00Z",
        })
        declare_treatment_result(
            bundle, [], "proven", ["profile_supported_effective_treatment"],
        )
        rebind_treatment_owners(bundle)
        canonical_routes = treatment._canonical_routes(load_json(MANIFEST_PATH))
        canonical_routes[route_id]["effort"] = trace["requested_effort"]
        with mock.patch.object(treatment, "_canonical_routes", return_value=canonical_routes):
            validated = treatment.validate_treatment_bundle(
                self.rebound(bundle),
            )
        self.assertEqual(validated["treatment_traces"][0]["treatment_disposition"], "proven")
        self.assertEqual(validated["treatment_traces"][0]["disposition_reasons"], ["profile_supported_effective_treatment"])

    def test_configuration_materialization_and_failure_taxonomy_are_derived(self) -> None:
        mismatch_cases = [
            ("assignment.named_agent", "different-agent", "agent_mismatch", "hard_fail"),
            ("assignment.model", "different-model", "model_mismatch", "hard_fail"),
            ("assignment.effort", "low", "effort_mismatch", "hard_fail"),
            ("assignment.configuration_hash", "sha256:" + "0" * 64, "configuration_mismatch", "hard_fail"),
            ("treatment.sandbox", {"mode": "read_only", "network_access": False, "writable_roots_digest": "sha256:" + "b" * 64}, "sandbox_approvals_mismatch", "hard_fail"),
            ("treatment.approvals", {"policy": "never", "granted_action_ids": []}, "sandbox_approvals_mismatch", "hard_fail"),
            ("treatment.mutation_class", "read_only", "mutation_class_mismatch", "hard_fail"),
            ("treatment.parent_configuration", {"parent_execution_trace_id": None, "configuration_hash": "sha256:" + "0" * 64}, "parent_configuration_mismatch", "hard_fail"),
            ("treatment.controlled_overrides", {"model": "different-model", "effort": "high", "configuration_hash": "sha256:" + "1" * 64}, "client_or_override_mismatch", "hard_fail"),
            ("treatment.delivery_canary", {"status": "failed", "evidence_digest": "sha256:" + "7" * 64}, "delivery_canary_failure", "unknown"),
        ]
        for field_path, observed_value, expected_code, expected_disposition in mismatch_cases:
            with self.subTest(field_path=field_path):
                bundle = copy.deepcopy(self.bundle)
                observation = next(item for item in bundle["treatment_traces"][0]["observations"] if item["field_path"] == field_path)
                observation["value"] = observed_value
                failure_codes = [expected_code, "effective_treatment_unknown"]
                declare_treatment_result(
                    bundle, failure_codes, expected_disposition, sorted(failure_codes)
                )
                result = treatment.validate_treatment_bundle(self.rebound(bundle))
                trace = result["treatment_traces"][0]
                self.assertEqual(trace["treatment_disposition"], expected_disposition)
                self.assertIn(expected_code, {item["failure_code"] for item in trace["treatment_failures"]})

        materialization = copy.deepcopy(self.bundle)
        trace = materialization["treatment_traces"][0]
        changed_hash = "sha256:" + "0" * 64
        trace["controlled_overrides"]["configuration_hash"] = changed_hash
        trace["configured_route_proof"]["controlled_overrides"]["configuration_hash"] = changed_hash
        trace["configured_route_proof"]["proof_id"] = treatment.content_id(trace["configured_route_proof"], "proof_id")
        observation = next(item for item in trace["observations"] if item["field_path"] == "treatment.controlled_overrides")
        observation["value"] = copy.deepcopy(trace["controlled_overrides"])
        declare_treatment_result(
            materialization, ["configuration_mismatch", "effective_treatment_unknown"],
            "hard_fail", ["configuration_mismatch", "effective_treatment_unknown"],
        )
        result = treatment.validate_treatment_bundle(self.rebound(materialization))
        self.assertEqual(result["treatment_traces"][0]["treatment_disposition"], "hard_fail")
        self.assertIn("configuration_mismatch", {item["failure_code"] for item in result["treatment_traces"][0]["treatment_failures"]})

        unsubstantiated = copy.deepcopy(self.bundle)
        unsubstantiated["treatment_traces"][0]["treatment_failures"] = [{
            "failure_code": "agent_mismatch", "affected_field": "assignment.named_agent",
            "expected_evidence_ref": None, "observed_evidence_ref": None,
            "resulting_disposition": "hard_fail",
        }]
        self.assert_bundle_invalid(unsubstantiated)

        forged_declared = copy.deepcopy(self.bundle)
        trace = forged_declared["treatment_traces"][0]
        next(item for item in trace["observations"] if item["field_path"] == "assignment.named_agent")["value"] = "different-agent"
        trace["treatment_failures"] = [{
            "failure_code": "agent_mismatch", "affected_field": "forged.field",
            "expected_evidence_ref": "fixture://forged/expected",
            "observed_evidence_ref": "fixture://forged/observed",
            "resulting_disposition": "hard_fail",
        }]
        forged_declared["fixture_provenance"]["expected_dispositions"][0]["treatment_disposition"] = "hard_fail"
        self.assert_bundle_invalid(forged_declared)

    def test_discovery_observations_must_support_the_requested_treatment(self) -> None:
        cases = [
            ("discovery.models", ["unrelated-model"], "model_mismatch"),
            ("discovery.efforts", ["unrelated-effort"], "effort_mismatch"),
            (
                "discovery.capabilities",
                ["model listing", "supported efforts", "input modalities", "telemetry"],
                "skills_mcp_tools_mismatch",
            ),
        ]
        for field_path, observed_values, expected_code in cases:
            with self.subTest(field_path=field_path):
                bundle = copy.deepcopy(self.bundle)
                observation = next(
                    item for item in bundle["treatment_traces"][0]["observations"]
                    if item["field_path"] == field_path
                )
                observation["value"] = observed_values
                failure_codes = [expected_code, "effective_treatment_unknown"]
                declare_treatment_result(bundle, failure_codes, "hard_fail", sorted(failure_codes))
                validated = treatment.validate_treatment_bundle(self.rebound(bundle))
                self.assertEqual(validated["treatment_traces"][0]["treatment_disposition"], "hard_fail")

        missing = copy.deepcopy(self.bundle)
        observation = next(
            item for item in missing["treatment_traces"][0]["observations"]
            if item["field_path"] == "discovery.models"
        )
        observation.update({
            "observation_state": "missing", "value": None,
            "evidence_ref": None, "captured_at": None,
        })
        declare_treatment_result(
            missing, ["model_mismatch", "effective_treatment_unknown"], "hard_fail",
            ["effective_treatment_unknown", "model_mismatch"],
        )
        validated = treatment.validate_treatment_bundle(self.rebound(missing))
        self.assertEqual(validated["treatment_traces"][0]["treatment_disposition"], "hard_fail")

    def test_observation_comparison_preserves_json_types(self) -> None:
        bundle = copy.deepcopy(self.bundle)
        observation = next(item for item in bundle["treatment_traces"][0]["observations"] if item["field_path"] == "treatment.sandbox")
        observation["value"]["network_access"] = 0
        with self.assertRaisesRegex(ValueError, "schema shape"):
            treatment.validate_treatment_bundle(self.rebound(bundle))

    def test_six_id_environment_and_configured_proof_joins(self) -> None:
        base = treatment.validate_treatment_bundle(copy.deepcopy(self.bundle))
        trace = base["treatment_traces"][0]
        self.assertTrue(all(trace["objective_binding"][field] for field in treatment.OBJECTIVE_ID_FIELDS))
        self.assertEqual(trace["treatment_disposition"], "unknown")
        self.assertIsNone(trace["supported_effective_model"])
        missing_owner = copy.deepcopy(self.bundle); missing_owner["controlled_environments"] = []
        with self.assertRaisesRegex(ValueError, "too few items"):
            treatment.validate_treatment_bundle(self.rebound(missing_owner))
        duplicate_owner = copy.deepcopy(self.bundle); duplicate_owner["controlled_environments"].append(copy.deepcopy(duplicate_owner["controlled_environments"][0]))
        with self.assertRaisesRegex(ValueError, "controlled_environments must contain unique items"):
            treatment.validate_treatment_bundle(self.rebound(duplicate_owner))
        orphan_owner = copy.deepcopy(self.bundle)
        orphan = copy.deepcopy(orphan_owner["controlled_environments"][0])
        orphan["work_item_id"] = "G56R-002-ORPHAN"
        orphan["controlled_environment_id"] = treatment.content_id(orphan, "controlled_environment_id")
        orphan_owner["controlled_environments"].append(orphan)
        with self.assertRaisesRegex(ValueError, "orphan owner"):
            treatment.validate_treatment_bundle(self.rebound(orphan_owner))
        mismatch = copy.deepcopy(self.bundle); mismatch["treatment_traces"][0]["work_item_id"] = "G56R-002-FORGED"
        with self.assertRaisesRegex(ValueError, "controlled environment binding"):
            treatment.validate_treatment_bundle(self.rebound(mismatch))
        validated_graph = treatment.validate_treatment_bundle(self.rebound(make_two_trace_graph_bundle(self.bundle)))
        self.assertEqual(len(validated_graph["treatment_traces"]), 2)

    def test_route_resolution_references_only_canonical_manifest_routes(self) -> None:
        for field in ("preferred_route_id", "attempted_route_ids", "supported_effective_route_id"):
            with self.subTest(route_field=field):
                bundle = copy.deepcopy(self.bundle)
                resolution = bundle["route_resolutions"][0]
                assigned_route = resolution["assigned_route_id"]
                unknown_route = "G56R-001-CR-FORGED"
                if field == "preferred_route_id":
                    resolution["preferred_route_id"] = unknown_route
                    resolution["attempted_route_ids"] = [unknown_route, assigned_route]
                    resolution["fallback_index"] = 1
                    resolution["fallback_reason"] = "preferred_unavailable"
                elif field == "attempted_route_ids":
                    resolution["attempted_route_ids"].append(unknown_route)
                else:
                    resolution["supported_effective_route_id"] = unknown_route
                rebind_treatment_owners(bundle)
                with self.assertRaisesRegex(ValueError, "outside the canonical candidate manifest"):
                    treatment.validate_treatment_bundle(self.rebound(bundle))

        canonical_routes = treatment._canonical_routes(load_json(MANIFEST_PATH))
        baseline_resolution = self.bundle["route_resolutions"][0]
        assigned_route = baseline_resolution["assigned_route_id"]
        assigned_contract = canonical_routes[assigned_route]["agent_contract_id"]
        same_agent_route = next(
            route_id for route_id, route in canonical_routes.items()
            if route_id != assigned_route and route["agent_contract_id"] == assigned_contract
        )
        different_agent_route = next(
            route_id for route_id, route in canonical_routes.items()
            if route["agent_contract_id"] != assigned_contract
        )
        semantic_cases = (
            ("preferred different agent", different_agent_route, "preferred"),
            ("attempted different agent", different_agent_route, "attempted"),
            ("supported alternate same agent", same_agent_route, "supported"),
            ("supported assigned route without route observation", assigned_route, "supported"),
        )
        for label, route_id, mutation in semantic_cases:
            with self.subTest(semantic_case=label):
                bundle = copy.deepcopy(self.bundle)
                resolution = bundle["route_resolutions"][0]
                if mutation == "preferred":
                    resolution["preferred_route_id"] = route_id
                    resolution["attempted_route_ids"] = [route_id, assigned_route]
                    resolution["fallback_index"] = 1
                    resolution["fallback_reason"] = "preferred_unavailable"
                elif mutation == "attempted":
                    resolution["attempted_route_ids"].append(route_id)
                else:
                    resolution["supported_effective_route_id"] = route_id
                rebind_treatment_owners(bundle)
                expected = "different agent contract" if mutation != "supported" or route_id != assigned_route else "declared treatment failures"
                if mutation == "supported" and route_id != assigned_route:
                    expected = "must select the assigned route"
                with self.assertRaisesRegex(ValueError, expected):
                    treatment.validate_treatment_bundle(self.rebound(bundle))

    def test_every_objective_and_environment_binding_is_owned(self) -> None:
        for field in (
            "candidate_route_id", "agent_contract_id", "runtime_capability_snapshot_id",
            "route_resolution_id", "experiment_policy_id", "execution_trace_id",
        ):
            with self.subTest(objective_id=field):
                bundle = copy.deepcopy(self.bundle)
                bundle["treatment_traces"][0]["objective_binding"][field] = None
                self.assert_bundle_invalid(bundle)

        missing_route = copy.deepcopy(self.bundle)
        missing_route["route_resolutions"] = []
        self.assert_bundle_invalid(missing_route)
        duplicate_route = copy.deepcopy(self.bundle)
        duplicate_route["route_resolutions"].append(copy.deepcopy(duplicate_route["route_resolutions"][0]))
        self.assert_bundle_invalid(duplicate_route)
        orphan_route = copy.deepcopy(self.bundle)
        orphan_resolution = copy.deepcopy(orphan_route["route_resolutions"][0])
        orphan_resolution["resolved_at"] = "2026-07-17T04:00:01Z"
        orphan_resolution["route_resolution_id"] = treatment.content_id(orphan_resolution, "route_resolution_id")
        orphan_route["route_resolutions"].append(orphan_resolution)
        with self.assertRaisesRegex(ValueError, "orphan owner"):
            treatment.validate_treatment_bundle(self.rebound(orphan_route))
        missing_policy = copy.deepcopy(self.bundle); missing_policy["experiment_policy_registry"] = []
        self.assert_bundle_invalid(missing_policy)
        duplicate_policy = copy.deepcopy(self.bundle)
        duplicate_policy["experiment_policy_registry"].append(copy.deepcopy(duplicate_policy["experiment_policy_registry"][0]))
        self.assert_bundle_invalid(duplicate_policy)
        orphan_policy = copy.deepcopy(self.bundle)
        policy = copy.deepcopy(orphan_policy["experiment_policy_registry"][0])
        policy["work_item_id"] = "G56R-002-ORPHAN"
        policy["experiment_policy_id"] = treatment.content_id(policy, "experiment_policy_id")
        orphan_policy["experiment_policy_registry"].append(policy)
        with self.assertRaisesRegex(ValueError, "experiment policy owner registry"):
            treatment.validate_treatment_bundle(self.rebound(orphan_policy))
        orphan_qualification = copy.deepcopy(self.bundle)
        orphan_qualification["qualification_evidence_registry"] = [qualification_owner("owned_external")]
        with self.assertRaisesRegex(ValueError, "qualification evidence owner registry"):
            treatment.validate_treatment_bundle(self.rebound(orphan_qualification))
        private_qualification = copy.deepcopy(self.bundle)
        private_owner = qualification_owner("owned_external")
        private_owner["destination_named_agent"] = "native-account-123"
        private_owner["qualification_evidence_id"] = treatment.content_id(
            private_owner, "qualification_evidence_id",
        )
        private_qualification["qualification_evidence_registry"] = [private_owner]
        with self.assertRaisesRegex(ValueError, "canonical manifest"):
            treatment.validate_treatment_bundle(self.rebound(private_qualification))
        duplicate_trace = copy.deepcopy(self.bundle)
        duplicate_trace["treatment_traces"].append(copy.deepcopy(duplicate_trace["treatment_traces"][0]))
        self.assert_bundle_invalid(duplicate_trace)

        equality_mutations = [
            (("client_identity_id",), "sha256:" + "0" * 64),
            (("surface",), "cli"),
            (("objective_binding", "runtime_capability_snapshot_id"), "sha256:" + "0" * 64),
            (("repository_revision",), "0" * 40),
            (("repository_tree_digest",), "sha256:" + "0" * 64),
            (("objective_binding", "candidate_route_id"), "different-route"),
            (("work_item_kind",), "fixture"),
            (("work_item_id",), "different-work-item"),
            (("assigned_route_id",), "different-route"),
        ]
        for path, value in equality_mutations:
            with self.subTest(environment_binding=".".join(path)):
                bundle = copy.deepcopy(self.bundle)
                target = bundle["treatment_traces"][0]
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = value
                self.assert_bundle_invalid(bundle)

    def test_context_lifecycle_and_structured_failures_are_validated(self) -> None:
        invalid_nested_values = [
            (("sandbox", "network_access"), "false"),
            (("approvals", "granted_action_ids"), ["duplicate", "duplicate"]),
            (("mutation_class",), ""),
            (("expected_skills_mcp_tools", "tools"), ["exec_command", "exec_command"]),
            (("parent_configuration", "configuration_hash"), "invalid"),
            (("controlled_overrides", "configuration_hash"), "invalid"),
            (("delivery_canary", "status"), "promoted"),
            (("context", "threadId"), ""),
            (("parent_child_graph", "root_execution_trace_id"), "different-trace"),
            (("raw_token_vector", "input_tokens"), -1),
            (("request_turn_count", "requests"), -1),
            (("wall_time_ms",), "unknown"),
            (("retries",), -1),
            (("compaction", "count"), -1),
            (("validation", "status"), "unknown"),
            (("cancellation", "state"), "unknown"),
            (("failed_abandoned_work", "failed_count"), -1),
            (("terminal_state",), ""),
            (("acceptance",), "unknown"),
        ]
        for path, value in invalid_nested_values:
            with self.subTest(field=".".join(path)):
                bundle = copy.deepcopy(self.bundle)
                target = bundle["treatment_traces"][0]
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = value
                self.assert_bundle_invalid(bundle)

        mismatch = copy.deepcopy(self.bundle)
        mismatch["treatment_traces"][0]["loaded_skills_mcp_tools"]["tools"] = []
        mismatch["treatment_traces"][0]["treatment_failures"] = []
        mismatch["treatment_traces"][0]["treatment_disposition"] = "proven"
        mismatch["fixture_provenance"]["expected_dispositions"][0]["treatment_disposition"] = "hard_fail"
        with self.assertRaisesRegex(ValueError, "declared treatment failures"):
            treatment.validate_treatment_bundle(self.rebound(copy.deepcopy(mismatch)))
        declare_treatment_result(
            mismatch, ["skills_mcp_tools_mismatch", "effective_treatment_unknown"], "hard_fail",
            ["effective_treatment_unknown", "skills_mcp_tools_mismatch"],
        )
        result = treatment.validate_treatment_bundle(self.rebound(mismatch))
        trace = result["treatment_traces"][0]
        self.assertEqual(trace["treatment_disposition"], "hard_fail")
        self.assertIn("skills_mcp_tools_mismatch", {item["failure_code"] for item in trace["treatment_failures"]})

        wrong_expectation = copy.deepcopy(self.bundle)
        wrong_expectation["fixture_provenance"]["expected_dispositions"][0]["treatment_disposition"] = "proven"
        self.assert_bundle_invalid(wrong_expectation)

    def test_declared_treatment_results_must_exactly_match_derived_state(self) -> None:
        missing_failures = copy.deepcopy(self.bundle)
        missing_failures["treatment_traces"][0]["treatment_failures"] = []
        with self.assertRaisesRegex(ValueError, "declared treatment failures"):
            treatment.validate_treatment_bundle(self.rebound(missing_failures))

        false_proven = copy.deepcopy(self.bundle)
        false_proven["treatment_traces"][0]["treatment_disposition"] = "proven"
        with self.assertRaisesRegex(ValueError, "declared treatment disposition"):
            treatment.validate_treatment_bundle(self.rebound(false_proven))

        incorrect_reasons = copy.deepcopy(self.bundle)
        incorrect_reasons["treatment_traces"][0]["disposition_reasons"] = [
            "effective_treatment_or_reroute_evidence_missing"
        ]
        with self.assertRaisesRegex(ValueError, "declared treatment disposition reasons"):
            treatment.validate_treatment_bundle(self.rebound(incorrect_reasons))

    def test_status_conditionals_require_exact_null_evidence(self) -> None:
        cases = [
            ("delivery_canary", "not_run"),
            ("validation", "not_run"),
            ("outcome", "unknown"),
        ]
        for field, status in cases:
            with self.subTest(field=field):
                bundle = copy.deepcopy(self.bundle)
                bundle["treatment_traces"][0][field]["status"] = status
                self.assert_bundle_invalid(bundle)

    def test_evidence_references_and_retained_strings_are_sanitized(self) -> None:
        references = [
            "/" + "Users" + "/example/private/evidence.json",
            "build-host.example.com",
            "https://github.com/private/repository",
            "authorization=Bearer-secret",
        ]
        for evidence_ref in references:
            with self.subTest(evidence_ref=evidence_ref):
                bundle = copy.deepcopy(self.bundle)
                bundle["treatment_traces"][0]["observations"][0]["evidence_ref"] = evidence_ref
                self.assert_bundle_invalid(bundle)
        retained_strings = [
            "note:/" + "Users" + "/example/private/cancellation.txt",
            "/opt/customer/private.json",
            "prefix,/opt/customer/private.json",
            "/mnt/secrets/evidence.json",
            "/Volumes/account-data/evidence.json",
            "C:\\customer\\private.json",
            "\\\\server\\share\\private.json",
            "../private/evidence.json",
            "~/private/evidence.json",
            "sk-exampleSecretToken123456",
        ]
        for retained_text in retained_strings:
            with self.subTest(retained_text=retained_text):
                retained = copy.deepcopy(self.bundle)
                retained["treatment_traces"][0]["work_item_id"] = retained_text
                with self.assertRaisesRegex(ValueError, "forbidden private"):
                    treatment.validate_treatment_bundle(self.rebound(retained))
        raw_reason = copy.deepcopy(self.bundle)
        raw_reason["treatment_traces"][0]["cancellation"].update({
            "state": "requested", "reason": "free form cancellation details",
        })
        with self.assertRaisesRegex(ValueError, "schema constant"):
            treatment.validate_treatment_bundle(self.rebound(raw_reason))

    def test_all_record_layers_reject_undeclared_fields(self) -> None:
        accessors = [
            lambda bundle: bundle,
            lambda bundle: bundle["telemetry_profile"][0],
            lambda bundle: bundle["telemetry_profile"][0]["observation_state_rules"],
            lambda bundle: bundle["controlled_environments"][0],
            lambda bundle: bundle["experiment_policy_registry"][0],
            lambda bundle: (
                bundle["qualification_evidence_registry"].append(qualification_owner("synthetic_fixture"))
                or bundle["qualification_evidence_registry"][0]
            ),
            lambda bundle: bundle["route_resolutions"][0],
            lambda bundle: bundle["treatment_traces"][0],
            lambda bundle: bundle["treatment_traces"][0]["objective_binding"],
            lambda bundle: bundle["treatment_traces"][0]["configured_route_proof"],
            lambda bundle: bundle["treatment_traces"][0]["configured_route_proof"]["profile_entry_key"],
            lambda bundle: bundle["treatment_traces"][0]["configured_route_proof"]["controlled_overrides"],
            lambda bundle: bundle["treatment_traces"][0]["sandbox"],
            lambda bundle: bundle["treatment_traces"][0]["approvals"],
            lambda bundle: bundle["treatment_traces"][0]["expected_skills_mcp_tools"],
            lambda bundle: bundle["treatment_traces"][0]["parent_configuration"],
            lambda bundle: bundle["treatment_traces"][0]["delivery_canary"],
            lambda bundle: bundle["treatment_traces"][0]["context"],
            lambda bundle: bundle["treatment_traces"][0]["parent_child_graph"],
            lambda bundle: bundle["treatment_traces"][0]["raw_token_vector"],
            lambda bundle: bundle["treatment_traces"][0]["request_turn_count"],
            lambda bundle: bundle["treatment_traces"][0]["compaction"],
            lambda bundle: bundle["treatment_traces"][0]["validation"],
            lambda bundle: bundle["treatment_traces"][0]["cancellation"],
            lambda bundle: bundle["treatment_traces"][0]["failed_abandoned_work"],
            lambda bundle: bundle["treatment_traces"][0]["outcome"],
            lambda bundle: bundle["treatment_traces"][0]["observations"][0],
            lambda bundle: bundle["fixture_provenance"],
        ]
        for index, accessor in enumerate(accessors):
            with self.subTest(record_layer=index):
                bundle = copy.deepcopy(self.bundle)
                accessor(bundle)["undeclared"] = True
                self.assert_bundle_invalid(bundle)

    def test_reroutes_are_separate_read_only_and_fail_closed(self) -> None:
        resolver_before_reroute = copy.deepcopy(self.bundle["route_resolutions"][0])
        approved = make_treatment_reroute_case(copy.deepcopy(self.bundle), "owned_external")
        trusted = trusted_external_qualification(approved)
        declare_reroute_result(approved, trusted)
        result = treatment.validate_treatment_bundle(
            self.rebound(approved), trusted_qualification_evidence=trusted
        )
        self.assertEqual(result["treatment_traces"][0]["treatment_disposition"], "non_scorable_rerouted")
        self.assertEqual(result["route_resolutions"][0], resolver_before_reroute)
        for authority in ("synthetic_fixture", "missing", "mismatched"):
            with self.subTest(authority=authority):
                bundle = make_treatment_reroute_case(copy.deepcopy(self.bundle), authority)
                self.assert_reroute_hard_failed(bundle)
        ambiguous = make_treatment_reroute_case(copy.deepcopy(self.bundle), "owned_external")
        second_event = copy.deepcopy(ambiguous["treatment_traces"][0]["service_reroute_events"][0])
        second_event["reason"] = "fixture_second_service_reroute"
        second_event["event_id"] = treatment.content_id(second_event, "event_id")
        ambiguous["treatment_traces"][0]["service_reroute_events"].append(second_event)
        reroute_observation = next(item for item in ambiguous["treatment_traces"][0]["observations"] if item["field_path"] == "reroute.events")
        reroute_observation["value"].append(copy.deepcopy(second_event))
        trusted = trusted_external_qualification(ambiguous)
        declare_reroute_result(ambiguous, trusted)
        failed = treatment.validate_treatment_bundle(
            self.rebound(ambiguous), trusted_qualification_evidence=trusted
        )
        self.assertEqual(failed["treatment_traces"][0]["treatment_disposition"], "hard_fail")
        self.assertEqual(treatment.FAILURE_DISPOSITIONS["effective_treatment_unknown"], "unknown")
        self.assertTrue(all(value in {"unknown", "hard_fail"} for value in treatment.FAILURE_DISPOSITIONS.values()))

    def test_reroute_association_and_external_qualification_are_exact(self) -> None:
        association_mutations = [
            ("event", "surface", "cli"),
            ("event", "threadId", "thread-fixture-different"),
            ("event", "turnId", "turn-fixture-different"),
            ("assessment", "destination_candidate_route_id", "different-route"),
            ("assessment", "destination_agent_contract_id", "different-contract"),
            ("assessment", "destination_named_agent", "different-agent"),
            ("assessment", "assessment", "unknown"),
            ("qualification", "destination_candidate_route_id", "different-route"),
            ("qualification", "destination_agent_contract_id", "different-contract"),
            ("qualification", "destination_named_agent", "different-agent"),
            ("qualification", "qualification_status", "unknown"),
            ("qualification", "owner_spec_id", ""),
            ("qualification", "evidence_digest", "invalid"),
        ]
        for record, field, value in association_mutations:
            with self.subTest(record=record, field=field):
                bundle = make_treatment_reroute_case(copy.deepcopy(self.bundle), "owned_external")
                trusted = trusted_external_qualification(bundle)
                trace = bundle["treatment_traces"][0]
                targets = {
                    "event": trace["service_reroute_events"][0],
                    "assessment": trace["reroute_destination_assessments"][0],
                    "qualification": bundle["qualification_evidence_registry"][0],
                }
                targets[record][field] = value
                if record == "event":
                    event = targets[record]
                    event["event_id"] = treatment.content_id(event, "event_id")
                    trace["reroute_destination_assessments"][0]["event_id"] = event["event_id"]
                    next(item for item in trace["observations"] if item["field_path"] == "reroute.events")["value"] = [copy.deepcopy(event)]
                if record == "qualification" and field in {
                    "destination_candidate_route_id", "destination_agent_contract_id", "destination_named_agent",
                }:
                    owner = targets[record]; old_id = owner["qualification_evidence_id"]
                    owner["qualification_evidence_id"] = treatment.content_id(owner, "qualification_evidence_id")
                    assessment = trace["reroute_destination_assessments"][0]
                    if assessment["prequalification_evidence_id"] == old_id:
                        assessment["prequalification_evidence_id"] = owner["qualification_evidence_id"]
                if record == "qualification":
                    self.assert_bundle_invalid(bundle)
                else:
                    self.assert_reroute_hard_failed(
                        bundle, trusted=trusted
                    )

        missing_assessment = make_treatment_reroute_case(copy.deepcopy(self.bundle), "owned_external")
        missing_assessment["treatment_traces"][0]["reroute_destination_assessments"] = []
        missing_assessment["qualification_evidence_registry"] = []
        self.assert_reroute_hard_failed(missing_assessment)
        duplicate_assessment = make_treatment_reroute_case(copy.deepcopy(self.bundle), "owned_external")
        duplicate_assessment["treatment_traces"][0]["reroute_destination_assessments"].append(
            copy.deepcopy(duplicate_assessment["treatment_traces"][0]["reroute_destination_assessments"][0])
        )
        with self.assertRaisesRegex(ValueError, "reroute_destination_assessments must contain unique items"):
            treatment.validate_treatment_bundle(self.rebound(duplicate_assessment))

        rerouted = make_treatment_reroute_case(copy.deepcopy(self.bundle), "owned_external")
        trace = rerouted["treatment_traces"][0]
        trace["service_reroute_events"][0]["undeclared"] = True
        self.assert_bundle_invalid(rerouted)
        rerouted = make_treatment_reroute_case(copy.deepcopy(self.bundle), "owned_external")
        rerouted["treatment_traces"][0]["reroute_destination_assessments"][0]["undeclared"] = True
        self.assert_bundle_invalid(rerouted)

    def test_reroute_cannot_self_authorize_or_rebind_models(self) -> None:
        no_trust = make_treatment_reroute_case(copy.deepcopy(self.bundle), "owned_external")
        no_trust["fixture_provenance"]["expected_dispositions"][0]["treatment_disposition"] = "hard_fail"
        self.assert_reroute_hard_failed(no_trust)

        forged_owner = make_treatment_reroute_case(copy.deepcopy(self.bundle), "owned_external")
        owner = next(item for item in forged_owner["qualification_evidence_registry"] if item["authority_kind"] == "owned_external")
        old_id = owner["qualification_evidence_id"]
        owner["owner_spec_id"] = "FAKE-OWNER"
        owner["evidence_digest"] = "sha256:" + "0" * 64
        owner["qualification_evidence_id"] = treatment.content_id(owner, "qualification_evidence_id")
        assessment = forged_owner["treatment_traces"][0]["reroute_destination_assessments"][0]
        self.assertEqual(assessment["prequalification_evidence_id"], old_id)
        assessment["prequalification_evidence_id"] = owner["qualification_evidence_id"]
        forged_owner["fixture_provenance"]["expected_dispositions"][0]["treatment_disposition"] = "hard_fail"
        self.assert_bundle_invalid(forged_owner)

        for field, value in (("fromModel", "unrelated-model"), ("toModel", "unrelated-model")):
            with self.subTest(event_field=field):
                bundle = make_treatment_reroute_case(copy.deepcopy(self.bundle), "owned_external")
                trusted = trusted_external_qualification(bundle)
                trace = bundle["treatment_traces"][0]
                event = trace["service_reroute_events"][0]
                event[field] = value
                event["event_id"] = treatment.content_id(event, "event_id")
                trace["reroute_destination_assessments"][0]["event_id"] = event["event_id"]
                next(item for item in trace["observations"] if item["field_path"] == "reroute.events")["value"] = [copy.deepcopy(event)]
                if field == "toModel":
                    trace["supported_effective_model"] = value
                    next(item for item in trace["observations"] if item["field_path"] == "assignment.supported_effective_model")["value"] = value
                bundle["fixture_provenance"]["expected_dispositions"][0]["treatment_disposition"] = "hard_fail"
                self.assert_reroute_hard_failed(
                    bundle, trusted=trusted
                )

    def test_reroute_output_preserves_detailed_and_normalized_reasons(self) -> None:
        cases = {
            "missing": ["reroute_destination_missing", "reroute_unidentifiable"],
            "owned_external": ["reroute_destination_untrusted", "reroute_unapproved"],
            "mismatched": ["reroute_destination_different_agent", "reroute_different_agent"],
        }
        for authority, expected_reasons in cases.items():
            with self.subTest(authority=authority):
                bundle = make_treatment_reroute_case(copy.deepcopy(self.bundle), authority)
                declare_reroute_result(bundle)
                validated = treatment.validate_treatment_bundle(self.rebound(rebind_treatment_owners(bundle)))
                trace = validated["treatment_traces"][0]
                self.assertEqual(trace["treatment_disposition"], "hard_fail")
                self.assertEqual(trace["disposition_reasons"], expected_reasons)

    def test_schema_and_runtime_reject_the_same_structural_mutations(self) -> None:
        baseline = self.rebound(copy.deepcopy(self.bundle))
        schema = treatment._read_json_file(treatment.SCHEMA_PATH)
        treatment._validate_schema_instance(baseline, schema, schema)
        treatment.validate_treatment_bundle(copy.deepcopy(baseline))
        mutations = []
        invalid_ref = copy.deepcopy(baseline)
        invalid_ref["treatment_traces"][0]["observations"][0]["evidence_ref"] = "https://private.example/evidence"
        mutations.append(("sanitized evidence reference", invalid_ref))
        undeclared = copy.deepcopy(baseline); undeclared["treatment_traces"][0]["undeclared"] = True
        mutations.append(("closed trace shape", undeclared))
        opaque_trace = copy.deepcopy(baseline)
        opaque_trace["treatment_traces"][0]["objective_binding"]["execution_trace_id"] = "opaque-trace"
        mutations.append(("digest execution identity", opaque_trace))
        raw_reason = copy.deepcopy(baseline)
        raw_reason["treatment_traces"][0]["service_reroute_events"] = [{
            "event_id": "sha256:" + "0" * 64, "surface": "app_server",
            "threadId": "thread", "turnId": "turn", "fromModel": "a", "toModel": "b",
            "reason": "free form reason", "evidence_digest": "sha256:" + "1" * 64,
        }]
        mutations.append(("enumerated reroute reason", raw_reason))
        explicit_null = copy.deepcopy(baseline)
        explicit = next(item for item in explicit_null["treatment_traces"][0]["observations"] if item["observation_state"] == "explicit_null")
        explicit["evidence_ref"] = None; explicit["captured_at"] = None
        mutations.append(("explicit null evidence and capture time", explicit_null))
        undocumented = copy.deepcopy(baseline)
        undocumented_value = next(item for item in undocumented["treatment_traces"][0]["observations"] if item["observation_state"] == "undocumented")
        undocumented_value["evidence_ref"] = "fixture://forged/undocumented"; undocumented_value["captured_at"] = "2026-07-17T04:01:00Z"
        mutations.append(("undocumented evidence and capture time", undocumented))
        fallback = copy.deepcopy(baseline)
        fallback["route_resolutions"][0]["fallback_reason"] = "preferred_unavailable"
        mutations.append(("primary route fallback reason", fallback))
        failure_disposition = copy.deepcopy(baseline)
        failure_disposition["treatment_traces"][0]["treatment_failures"] = [{
            "failure_code": "agent_mismatch", "affected_field": "treatment.evidence",
            "expected_evidence_ref": None, "observed_evidence_ref": None,
            "resulting_disposition": "non_scorable_rerouted",
        }]
        mutations.append(("unreachable failure disposition", failure_disposition))
        failure_evidence = copy.deepcopy(baseline)
        failure_evidence["treatment_traces"][0]["treatment_failures"] = [{
            "failure_code": "agent_mismatch", "affected_field": "treatment.evidence",
            "expected_evidence_ref": "fixture://forged/expected", "observed_evidence_ref": None,
            "resulting_disposition": "hard_fail",
        }]
        mutations.append(("unrepresentable failure evidence", failure_evidence))
        timestamp = copy.deepcopy(baseline)
        timestamp["route_resolutions"][0]["resolved_at"] = "2026-07-17 04:00:00Z"
        mutations.append(("strict RFC3339 UTC timestamp", timestamp))
        for label, bundle in mutations:
            with self.subTest(label=label):
                with self.assertRaises(ValueError): treatment._validate_schema_instance(bundle, schema, schema)
                with self.assertRaises(ValueError): treatment.validate_treatment_bundle(bundle)

    def test_bounded_file_loading_rejects_links_special_files_and_external_paths(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory); source = root / "source.json"; source.write_text("{}", encoding="utf-8")
            self.assertEqual(treatment._read_bounded_regular_file(source, allowed_root=root), b"{}")
            with mock.patch.object(treatment, "HAS_DESCRIPTOR_RELATIVE_IO", False):
                self.assertEqual(treatment._read_bounded_regular_file(source, allowed_root=root), b"{}")
                self.assertEqual(
                    treatment.validate_treatment_bundle(copy.deepcopy(self.bundle))["telemetry_profile_id"],
                    self.bundle["telemetry_profile_id"],
                )
            with mock.patch.object(
                treatment, "HAS_DESCRIPTOR_RELATIVE_IO", False,
            ), mock.patch.object(
                treatment, "IS_WINDOWS", True,
            ), mock.patch.object(
                treatment, "_windows_final_path_from_descriptor", return_value=source.resolve(),
            ) as final_path:
                self.assertEqual(treatment._read_bounded_regular_file(source, allowed_root=root), b"{}")
                self.assertEqual(final_path.call_count, 1)
            with mock.patch.object(
                treatment, "HAS_DESCRIPTOR_RELATIVE_IO", False,
            ), mock.patch.object(
                treatment, "IS_WINDOWS", True,
            ), mock.patch.object(
                treatment, "_windows_final_path_from_descriptor", return_value=root.parent / "escaped.json",
            ), self.assertRaisesRegex(ValueError, "Windows handle escaped"):
                treatment._read_bounded_regular_file(source, allowed_root=root)
            symlink = root / "symlink.json"; symlink.symlink_to(source)
            with self.assertRaisesRegex(ValueError, "regular non-symlink"):
                treatment._read_bounded_regular_file(symlink, allowed_root=root)
            with mock.patch.object(
                treatment, "HAS_DESCRIPTOR_RELATIVE_IO", False,
            ), self.assertRaisesRegex(ValueError, "non-symlink"):
                treatment._read_bounded_regular_file(symlink, allowed_root=root)
            real_directory = root / "real"; real_directory.mkdir()
            nested_source = real_directory / "nested.json"; nested_source.write_text("{}", encoding="utf-8")
            linked_directory = root / "linked"; linked_directory.symlink_to(real_directory, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "regular non-symlink|real directories"):
                treatment._read_bounded_regular_file(linked_directory / "nested.json", allowed_root=root)
            hardlink = root / "hardlink.json"; os.link(source, hardlink)
            with self.assertRaisesRegex(ValueError, "single-link"):
                treatment._read_bounded_regular_file(source, allowed_root=root)
            hardlink.unlink()
            oversized = root / "oversized.json"; oversized.write_bytes(b"12345")
            with self.assertRaisesRegex(ValueError, "maximum size"):
                treatment._read_bounded_regular_file(oversized, allowed_root=root, max_bytes=4)
            if hasattr(os, "mkfifo"):
                fifo = root / "fixture-fifo"; os.mkfifo(fifo)
                with self.assertRaisesRegex(ValueError, "regular"):
                    treatment._read_bounded_regular_file(fifo, allowed_root=root)

            race_directory = root / "race"; race_directory.mkdir()
            race_source = race_directory / "source.json"; race_source.write_text("{}", encoding="utf-8")
            moved_directory = root / "race-original"
            original_open = treatment.os.open
            swapped = False

            def replace_directory(path: object, flags: int, *args: object, **kwargs: object) -> int:
                nonlocal swapped
                if path == "source.json" and kwargs.get("dir_fd") is not None and not swapped:
                    swapped = True
                    race_directory.rename(moved_directory)
                    race_directory.mkdir()
                    (race_directory / "source.json").write_text('{"outside":"replacement"}', encoding="utf-8")
                return original_open(path, flags, *args, **kwargs)

            with mock.patch.object(treatment.os, "open", side_effect=replace_directory), self.assertRaisesRegex(
                ValueError, "directory changed while it was being read"
            ):
                treatment._read_bounded_regular_file(race_source, allowed_root=root)
            fallback_source = root / "fallback-race.json"
            fallback_source.write_text("{}", encoding="utf-8")
            fallback_original = root / "fallback-original.json"
            fallback_swapped = False

            def replace_fallback_file(path: object, flags: int, *args: object, **kwargs: object) -> int:
                nonlocal fallback_swapped
                if Path(path) == fallback_source and not fallback_swapped:
                    fallback_swapped = True
                    fallback_source.rename(fallback_original)
                    fallback_source.write_text('{"replacement":true}', encoding="utf-8")
                return original_open(path, flags, *args, **kwargs)

            with mock.patch.object(
                treatment, "HAS_DESCRIPTOR_RELATIVE_IO", False,
            ), mock.patch.object(
                treatment.os, "open", side_effect=replace_fallback_file,
            ), self.assertRaisesRegex(ValueError, "pathname changed before it was read"):
                treatment._read_bounded_regular_file(fallback_source, allowed_root=root)
        with tempfile.TemporaryDirectory() as directory:
            external = Path(directory) / "fixture.json"; external.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "approved root"):
                treatment._read_bounded_regular_file(external)
            completed = subprocess.run(
                ["python3", str(TREATMENT_MODULE_PATH), "validate", "--fixture", str(external)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertNotIn(str(external), completed.stderr)

        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            hostile_inputs = {
                "deep.json": "[" * 2_000 + "0" + "]" * 2_000,
                "duplicate.json": '{"api_key=SUPERSECRET":1,"api_key=SUPERSECRET":2}',
            }
            for name, payload in hostile_inputs.items():
                with self.subTest(name=name):
                    source = root / name; source.write_text(payload, encoding="utf-8")
                    completed = subprocess.run(
                        ["python3", str(TREATMENT_MODULE_PATH), "validate", "--fixture", str(source)],
                        cwd=ROOT, text=True, capture_output=True, check=False,
                    )
                    self.assertEqual(completed.returncode, 2)
                    self.assertNotIn("Traceback", completed.stderr)
                    self.assertNotIn("SUPERSECRET", completed.stderr)

    def test_dictionary_keys_are_bounded_private_and_never_echoed(self) -> None:
        oversized_key = "x" * (treatment.MAX_RETAINED_STRING_LENGTH + 1)
        oversized = copy.deepcopy(self.bundle); oversized[oversized_key] = None
        with self.assertRaisesRegex(ValueError, "oversized retained string") as oversized_error:
            treatment.validate_treatment_bundle(self.rebound(oversized))
        self.assertNotIn(oversized_key, str(oversized_error.exception))

        for private_key in (
            "password=SensitiveToken123",
            "/opt/customer/private.json",
            "unsafe\nterminal-key",
        ):
            with self.subTest(private_key=private_key):
                retained = copy.deepcopy(self.bundle); retained[private_key] = None
                with self.assertRaisesRegex(ValueError, "forbidden private") as private_error:
                    treatment.validate_treatment_bundle(self.rebound(retained))
                self.assertNotIn(private_key, str(private_error.exception))

    def test_retained_identifiers_reject_unlabeled_credentials_pii_and_native_ids(self) -> None:
        for value in (
            "person" + "@" + "example.com",
            "AKIA" + "A" * 16,
            "123-45-6789",
            "internal-build.customer.example",
            "builder.internal",
            "192.0.2.42",
            "2001:db8::42",
        ):
            with self.subTest(sensitive_value=value):
                bundle = copy.deepcopy(self.bundle)
                bundle["fixture_provenance"]["sanitizer_version"] = value
                with self.assertRaisesRegex(ValueError, "forbidden private") as error:
                    treatment.validate_treatment_bundle(self.rebound(bundle))
                self.assertNotIn(value, str(error.exception))

        field_cases = []
        native_context = copy.deepcopy(self.bundle)
        native_context["treatment_traces"][0]["context"]["threadId"] = "native-thread-123"
        field_cases.append(("native thread correlation", native_context))
        unsafe_tool = copy.deepcopy(self.bundle)
        unsafe_tool["treatment_traces"][0]["expected_skills_mcp_tools"]["tools"] = ["tool name with spaces"]
        field_cases.append(("unsafe tool identifier", unsafe_tool))
        unsafe_action = copy.deepcopy(self.bundle)
        unsafe_action["treatment_traces"][0]["approvals"]["granted_action_ids"] = ["action with spaces"]
        field_cases.append(("unsafe action identifier", unsafe_action))
        for label, bundle in field_cases:
            with self.subTest(identifier_case=label):
                rebound = self.rebound(bundle)
                with self.assertRaisesRegex(ValueError, "sanitized|correlation"):
                    treatment.validate_treatment_bundle(rebound)

    def test_top_level_claims_follow_profile_classification_and_conditions(self) -> None:
        for field in ("wall_time_ms", "retries"):
            with self.subTest(field=field):
                bundle = copy.deepcopy(self.bundle); bundle["treatment_traces"][0][field] = 1
                with self.assertRaisesRegex(ValueError, "cannot retain a top-level claim"):
                    treatment.validate_treatment_bundle(self.rebound(bundle))
        conditional_fields = {
            "parent.graph": copy.deepcopy(self.bundle["treatment_traces"][0]["parent_child_graph"]),
            "lifecycle.cancellation": copy.deepcopy(self.bundle["treatment_traces"][0]["cancellation"]),
        }
        for field_path, value in conditional_fields.items():
            with self.subTest(field_path=field_path):
                bundle = copy.deepcopy(self.bundle)
                observation = next(item for item in bundle["treatment_traces"][0]["observations"] if item["field_path"] == field_path)
                observation.update({
                    "observation_state": "observed_value", "value": value,
                    "evidence_ref": "fixture://trace/conditional", "captured_at": "2026-07-17T04:01:00Z",
                })
                with self.assertRaisesRegex(ValueError, "condition did not occur"):
                    treatment.validate_treatment_bundle(self.rebound(bundle))

    def test_terminal_lifecycle_invariants_are_schema_and_runtime_authority(self) -> None:
        cases = []
        outcome = copy.deepcopy(self.bundle); outcome["treatment_traces"][0]["outcome"]["status"] = "failed"; cases.append(outcome)
        failed = copy.deepcopy(self.bundle); failed["treatment_traces"][0]["terminal_state"] = "failed"; failed["treatment_traces"][0]["outcome"]["status"] = "failed"; cases.append(failed)
        cancelled = copy.deepcopy(self.bundle); cancelled["treatment_traces"][0]["terminal_state"] = "cancelled"; cancelled["treatment_traces"][0]["outcome"]["status"] = "cancelled"; cases.append(cancelled)
        accepted = copy.deepcopy(self.bundle); accepted["treatment_traces"][0]["acceptance"] = False; cases.append(accepted)
        schema = treatment._read_json_file(treatment.SCHEMA_PATH)
        for index, bundle in enumerate(cases):
            with self.subTest(case=index):
                rebound = self.rebound(bundle)
                with self.assertRaises(ValueError): treatment._validate_schema_instance(rebound, schema, schema)
                with self.assertRaises(ValueError): treatment.validate_treatment_bundle(rebound)

    def test_trace_graph_rejects_orphans_nonreciprocal_edges_wrong_roots_and_cycles(self) -> None:
        missing_root = copy.deepcopy(self.bundle)
        missing_root["treatment_traces"][0]["parent_child_graph"]["root_execution_trace_id"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "graph root has no owner"):
            treatment.validate_treatment_bundle(self.rebound(missing_root))
        graph = make_two_trace_graph_bundle(self.bundle)
        nonreciprocal = copy.deepcopy(graph)
        root_trace, child_trace = nonreciprocal["treatment_traces"]
        root_trace["parent_child_graph"]["child_execution_trace_ids"] = []
        root_observation = next(item for item in root_trace["observations"] if item["field_path"] == "parent.graph")
        root_observation.update({"observation_state": "missing", "value": None, "evidence_ref": None, "captured_at": None})
        with self.assertRaisesRegex(ValueError, "not reciprocal"):
            treatment.validate_treatment_bundle(self.rebound(nonreciprocal))
        wrong_root = copy.deepcopy(graph)
        wrong_root["treatment_traces"][1]["parent_child_graph"]["root_execution_trace_id"] = wrong_root["treatment_traces"][1]["objective_binding"]["execution_trace_id"]
        next(item for item in wrong_root["treatment_traces"][1]["observations"] if item["field_path"] == "parent.graph")["value"] = copy.deepcopy(wrong_root["treatment_traces"][1]["parent_child_graph"])
        with self.assertRaisesRegex(ValueError, "root does not match"):
            treatment.validate_treatment_bundle(self.rebound(wrong_root))
        cyclic = copy.deepcopy(graph); root_trace, child_trace = cyclic["treatment_traces"]
        root_id = root_trace["objective_binding"]["execution_trace_id"]; child_id = child_trace["objective_binding"]["execution_trace_id"]
        root_trace["parent_configuration"]["parent_execution_trace_id"] = child_id
        root_trace["parent_configuration"]["configuration_hash"] = child_trace["configuration_hash"]
        root_trace["parent_child_graph"]["parent_execution_trace_id"] = child_id
        child_trace["parent_child_graph"]["child_execution_trace_ids"] = [root_id]
        for trace in (root_trace, child_trace):
            next(item for item in trace["observations"] if item["field_path"] == "treatment.parent_configuration")["value"] = copy.deepcopy(trace["parent_configuration"])
            next(item for item in trace["observations"] if item["field_path"] == "parent.graph")["value"] = copy.deepcopy(trace["parent_child_graph"])
        with self.assertRaisesRegex(ValueError, "cycle"):
            treatment.validate_treatment_bundle(self.rebound(cyclic))

    def test_child_parent_configuration_hash_binds_parent_trace(self) -> None:
        graph = make_two_trace_graph_bundle(self.bundle)
        child = graph["treatment_traces"][1]
        child["parent_configuration"]["configuration_hash"] = "sha256:" + "2" * 64
        next(
            item for item in child["observations"]
            if item["field_path"] == "treatment.parent_configuration"
        )["value"] = copy.deepcopy(child["parent_configuration"])
        rebind_treatment_owners(graph)
        with self.assertRaisesRegex(ValueError, "does not bind the referenced parent trace"):
            treatment.validate_treatment_bundle(self.rebound(graph))

    def test_locally_owned_identifiers_are_content_addressed(self) -> None:
        mutations = []
        route = copy.deepcopy(self.bundle); route["route_resolutions"][0]["resolved_at"] = "2026-07-17T04:00:01Z"; mutations.append(("route resolution ID", route))
        policy = copy.deepcopy(self.bundle); policy["experiment_policy_registry"][0]["work_item_id"] = "G56R-002-T999"; mutations.append(("experiment policy ID", policy))
        trace = copy.deepcopy(self.bundle); trace["treatment_traces"][0]["objective_binding"]["execution_trace_id"] = "sha256:" + "0" * 64; mutations.append(("execution trace ID", trace))
        for message, bundle in mutations:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                treatment.validate_treatment_bundle(self.rebound(bundle))

    def test_treatment_bound_freeze_apis_require_external_authority(self) -> None:
        manifest = load_json(MANIFEST_PATH)
        published = load_json(PUBLISHED_FREEZE_PATH)
        forged = copy.deepcopy(published)
        forged["telemetry_profile_id"] = capabilities.digest(b"forged-profile")
        forged["treatment_contract_digest"] = capabilities.digest(b"forged-contract")
        forged["candidate_freeze_id"] = capabilities.digest(capability_freeze._freeze_identity_payload(forged))
        expected_profile = self.bundle["telemetry_profile_id"]
        expected_contract = self.bundle["treatment_contract_digest"]
        expected_evidence = published["treatment_evidence_digest"]
        prior = copy.deepcopy(published)
        prior["candidate_freeze_id"] = published["supersedes_candidate_freeze_id"]
        prior["telemetry_profile_id"] = "sha256:f39d0acd9403d193b07861c5cba5dac0e7ba901936ad542c18dd4eb008ec898b"
        prior.pop("treatment_contract_digest")
        prior.pop("treatment_evidence_digest")
        prior["published_at"] = TREATMENT_PREDECESSOR_PUBLISHED_AT
        prior["supersedes_candidate_freeze_id"] = None
        self.assertEqual(capabilities.digest(capability_freeze._freeze_identity_payload(prior)), prior["candidate_freeze_id"])
        with tempfile.TemporaryDirectory() as directory:
            raw_root = Path(directory) / "raw"; raw_root.mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError, "requires its validated predecessor"):
                capabilities.publish_with_raw_evidence_retention(
                    forged, Path(directory) / "forged.json", raw_root, ROOT, manifest=manifest,
                )
            with self.assertRaises(TypeError):
                capabilities.validate_freeze(
                    forged, manifest, _enforce_lineage=False,
                )
            forged_predecessor = copy.deepcopy(prior)
            forged_predecessor["candidate_freeze_id"] = capabilities.digest(b"forged-predecessor")
            with self.assertRaisesRegex(ValueError, "identity"):
                capabilities.publish_with_raw_evidence_retention(
                    forged, Path(directory) / "forged.json", raw_root, ROOT, manifest=manifest,
                    predecessor=forged_predecessor,
                    expected_telemetry_profile_id=forged["telemetry_profile_id"],
                    expected_treatment_contract_digest=forged["treatment_contract_digest"],
                    expected_treatment_evidence_digest=forged["treatment_evidence_digest"],
                )
            with self.assertRaisesRegex(ValueError, "binding disagree"):
                capabilities.publish_with_raw_evidence_retention(
                    forged, Path(directory) / "forged.json", raw_root, ROOT, manifest=manifest,
                    predecessor=prior,
                    expected_telemetry_profile_id=expected_profile,
                    expected_treatment_contract_digest=expected_contract,
                    expected_treatment_evidence_digest=expected_evidence,
                )
            decisions = capability_contract._BoundDecisionSet(copy.deepcopy(published["tuple_decisions"]))
            with mock.patch.object(capability_freeze, "validate_unknown_observation_evidence"), self.assertRaisesRegex(
                ValueError, "binding disagree"
            ):
                capabilities.build_freeze(
                    published["client_identity"], published["official_source_refreshes"],
                    published["surface_matrix"], decisions, "2026-07-18T19:40:01Z",
                    manifest=manifest, predecessor=forged,
                    raw_evidence_root=raw_root, repository_root=ROOT,
                    expected_predecessor_telemetry_profile_id=expected_profile,
                    expected_predecessor_treatment_contract_digest=expected_contract,
                    expected_predecessor_treatment_evidence_digest=expected_evidence,
                )
            with self.assertRaisesRegex(ValueError, "binding disagree"):
                capabilities.build_canary_successor(
                    forged, {}, manifest, "2026-07-18T19:40:01Z",
                    raw_evidence_root=raw_root, repository_root=ROOT,
                    expected_telemetry_profile_id=expected_profile,
                    expected_treatment_contract_digest=expected_contract,
                    expected_treatment_evidence_digest=expected_evidence,
                )

    def test_successor_freeze_preserves_capability_payload(self) -> None:
        published = load_json(ROOT / "docs/ai/research/codex-g56r-002-executable-candidate-freeze.json")
        prior = copy.deepcopy(published)
        prior["candidate_freeze_id"] = "sha256:403051de7d5e0a0a358cd372533ef93da2a25609e8d01ab73cb529e820aaaf03"
        prior["telemetry_profile_id"] = "sha256:f39d0acd9403d193b07861c5cba5dac0e7ba901936ad542c18dd4eb008ec898b"
        prior.pop("treatment_contract_digest", None)
        prior.pop("treatment_evidence_digest", None)
        prior["published_at"] = TREATMENT_PREDECESSOR_PUBLISHED_AT
        prior["supersedes_candidate_freeze_id"] = None
        self.assertEqual(treatment.content_id(prior, "candidate_freeze_id"), prior["candidate_freeze_id"])
        successor_bundle, successor_evidence = bind_trusted_treatment_evidence(
            self.rebound(copy.deepcopy(self.bundle))
        )
        bounded_reads: list[Path] = []
        original_read = treatment._read_bounded_regular_file

        def track_authority_reads(path: Path, **kwargs: object) -> bytes:
            bounded_reads.append(Path(path))
            return original_read(path, **kwargs)

        with mock.patch.object(treatment, "_read_bounded_regular_file", side_effect=track_authority_reads):
            successor = treatment.build_treatment_successor(
                prior, successor_bundle, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
                trusted_treatment_evidence=successor_evidence,
            )
        self.assertEqual(bounded_reads.count(treatment.SCHEMA_PATH), 1)
        self.assertEqual(bounded_reads.count(treatment.MANIFEST_PATH), 1)
        self.assertEqual(successor, published)
        self.assertEqual(successor["supersedes_candidate_freeze_id"], prior["candidate_freeze_id"])
        self.assertEqual(successor["telemetry_profile_id"], successor_bundle["telemetry_profile_id"])
        self.assertEqual(successor["treatment_contract_digest"], successor_bundle["treatment_contract_digest"])
        self.assertEqual(successor["treatment_evidence_digest"], published["treatment_evidence_digest"])
        self.assertEqual(successor["published_at"], TREATMENT_SUCCESSOR_PUBLISHED_AT)
        proven_excluded = copy.deepcopy(self.bundle)
        reroute_observation = next(
            item for item in proven_excluded["treatment_traces"][0]["observations"]
            if item["field_path"] == "reroute.events"
        )
        reroute_observation.update({
            "observation_state": "observed_value", "value": [],
            "evidence_ref": "fixture://trace/reroute-monitoring",
            "captured_at": "2026-07-17T04:01:00Z",
        })
        declare_treatment_result(
            proven_excluded, [], "proven",
            ["configured_route_proof_and_complete_reroute_monitoring"],
        )
        proven_excluded, proven_excluded_evidence = bind_trusted_treatment_evidence(
            self.rebound(proven_excluded)
        )
        self.assertEqual(
            treatment.validate_treatment_bundle(copy.deepcopy(proven_excluded))[
                "treatment_traces"
            ][0]["treatment_disposition"],
            "proven",
        )
        with self.assertRaisesRegex(ValueError, "cannot prove a non-executable prior tuple"):
            treatment.build_treatment_successor(
                prior, proven_excluded, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
                trusted_treatment_evidence=proven_excluded_evidence,
            )
        future_route = copy.deepcopy(self.bundle)
        future_route["route_resolutions"][0]["resolved_at"] = "2026-07-19T04:01:00Z"
        next(
            item for item in future_route["treatment_traces"][0]["observations"]
            if item["field_path"] == "route.resolved_at"
        )["value"] = "2026-07-19T04:01:00Z"
        future_route, future_route_evidence = bind_trusted_treatment_evidence(
            self.rebound(rebind_treatment_owners(future_route))
        )
        with self.assertRaisesRegex(ValueError, "publication timestamp precedes treatment evidence"):
            treatment.build_treatment_successor(
                prior, future_route, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
                trusted_treatment_evidence=future_route_evidence,
            )
        future_observation = copy.deepcopy(self.bundle)
        next(
            item for item in future_observation["treatment_traces"][0]["observations"]
            if item["captured_at"] is not None
        )["captured_at"] = "2026-07-19T04:01:00Z"
        future_observation, future_observation_evidence = bind_trusted_treatment_evidence(
            self.rebound(future_observation)
        )
        with self.assertRaisesRegex(ValueError, "publication timestamp precedes treatment evidence"):
            treatment.build_treatment_successor(
                prior, future_observation, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
                trusted_treatment_evidence=future_observation_evidence,
            )
        class SwitchingEvidence(Mapping[str, bytes]):
            def __init__(self, values: dict[str, bytes], target: str) -> None:
                self.values = values
                self.target = target
                self.reads: dict[str, int] = {}

            def __getitem__(self, key: str) -> bytes:
                self.reads[key] = self.reads.get(key, 0) + 1
                value = self.values[key]
                return value + b" " if key == self.target and self.reads[key] > 1 else value

            def __iter__(self):
                return iter(self.values)

            def __len__(self) -> int:
                return len(self.values)

        switching_evidence = SwitchingEvidence(
            successor_evidence,
            successor_bundle["fixture_provenance"]["raw_evidence_digest"],
        )
        self.assertEqual(treatment.build_treatment_successor(
            prior, successor_bundle, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
            trusted_treatment_evidence=switching_evidence,
        ), successor)
        rerouted = self.rebound(make_treatment_reroute_case(copy.deepcopy(self.bundle), "owned_external"))
        trusted = trusted_external_qualification(rerouted)
        declare_reroute_result(rerouted, trusted)
        rerouted, rerouted_evidence = bind_trusted_treatment_evidence(rerouted)
        rerouted_successor = treatment.build_treatment_successor(
            prior, rerouted, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
            trusted_qualification_evidence=trusted,
            trusted_treatment_evidence=rerouted_evidence,
        )
        self.assertEqual(rerouted_successor["telemetry_profile_id"], published["telemetry_profile_id"])
        self.assertEqual(rerouted_successor["treatment_contract_digest"], published["treatment_contract_digest"])
        self.assertNotEqual(rerouted_successor["treatment_evidence_digest"], published["treatment_evidence_digest"])
        self.assertNotEqual(rerouted_successor["candidate_freeze_id"], published["candidate_freeze_id"])
        with self.assertRaisesRegex(ValueError, "declared treatment"):
            treatment.build_treatment_successor(
                prior, rerouted, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
                trusted_treatment_evidence=rerouted_evidence,
            )
        altered_trust = copy.deepcopy(trusted)
        next(iter(altered_trust.values()))["evidence_digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "not content addressed"):
            treatment.build_treatment_successor(
                prior, rerouted, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
                trusted_qualification_evidence=altered_trust,
                trusted_treatment_evidence=rerouted_evidence,
            )
        custom_manifest = copy.deepcopy(load_json(MANIFEST_PATH))
        route = next(
            item for item in custom_manifest["candidate_routes"]
            if item["candidate_route_id"] == self.bundle["treatment_traces"][0]["assigned_route_id"]
        )
        route["model_selector"]["expected_resolved_model_id"] = "different-model"
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            manifest_path = Path(directory) / "custom-manifest.json"
            manifest_path.write_text(json.dumps(custom_manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "canonical G56R-001"):
                treatment.validate_treatment_bundle(
                    copy.deepcopy(self.bundle), manifest_path=manifest_path,
                )
            with self.assertRaisesRegex(ValueError, "canonical G56R-001"):
                treatment.build_treatment_successor(
                    prior, self.bundle, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
                    manifest_path=manifest_path,
                )
        manifest = load_json(MANIFEST_PATH)
        self.assertEqual(capabilities.validate_freeze(
            published, manifest, predecessor=prior,
            expected_telemetry_profile_id=self.bundle["telemetry_profile_id"],
            expected_treatment_contract_digest=self.bundle["treatment_contract_digest"],
            expected_treatment_evidence_digest=successor["treatment_evidence_digest"],
        ), published)
        for key in prior:
            if key not in {"candidate_freeze_id", "telemetry_profile_id", "published_at", "supersedes_candidate_freeze_id"}:
                self.assertEqual(successor[key], prior[key])
        with self.assertRaisesRegex(ValueError, "must be later"):
            treatment.build_treatment_successor(
                prior, successor_bundle, published_at=TREATMENT_PREDECESSOR_PUBLISHED_AT,
                trusted_treatment_evidence=successor_evidence,
            )
        tampered = copy.deepcopy(prior); tampered["candidate_freeze_id"] = treatment.digest(b"forged")
        with self.assertRaisesRegex(ValueError, "prior freeze identity"):
            treatment.build_treatment_successor(
                tampered, self.bundle, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
            )

        with self.assertRaisesRegex(ValueError, "trusted evidence bytes"):
            treatment.build_treatment_successor(
                prior, successor_bundle, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
            )
        forged_evidence = dict(successor_evidence)
        observation_ref = next(key for key in forged_evidence if key.startswith("fixture://"))
        forged_evidence[observation_ref] += b" "
        with self.assertRaisesRegex(ValueError, "canonical JSON bytes"):
            treatment.build_treatment_successor(
                prior, successor_bundle, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
                trusted_treatment_evidence=forged_evidence,
            )
        proof_digest = successor_bundle["treatment_traces"][0][
            "configured_route_proof"
        ]["consumption_evidence_digest"]
        forged_evidence = dict(successor_evidence)
        forged_evidence[proof_digest] += b" "
        with self.assertRaisesRegex(ValueError, "digest does not match"):
            treatment.build_treatment_successor(
                prior, successor_bundle, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
                trusted_treatment_evidence=forged_evidence,
            )
        source_digest = successor_bundle["fixture_provenance"]["raw_evidence_digest"]
        forged_evidence = dict(successor_evidence)
        forged_evidence[source_digest] += b" "
        with self.assertRaisesRegex(ValueError, "digest does not match"):
            treatment.build_treatment_successor(
                prior, successor_bundle, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
                trusted_treatment_evidence=forged_evidence,
            )

        later_published_at = "2026-07-19T04:01:00Z"
        with self.assertRaisesRegex(ValueError, "requires its validated predecessor"):
            treatment.build_treatment_successor(
                successor, successor_bundle, published_at=later_published_at,
                trusted_treatment_evidence=successor_evidence,
                expected_prior_telemetry_profile_id=successor["telemetry_profile_id"],
                expected_prior_treatment_contract_digest=successor["treatment_contract_digest"],
                expected_prior_treatment_evidence_digest=successor["treatment_evidence_digest"],
            )
        second_successor = treatment.build_treatment_successor(
            successor, successor_bundle, published_at=later_published_at,
            trusted_treatment_evidence=successor_evidence,
            prior_freeze_predecessor=prior,
            expected_prior_telemetry_profile_id=successor["telemetry_profile_id"],
            expected_prior_treatment_contract_digest=successor["treatment_contract_digest"],
            expected_prior_treatment_evidence_digest=successor["treatment_evidence_digest"],
        )
        self.assertEqual(
            second_successor["supersedes_candidate_freeze_id"],
            successor["candidate_freeze_id"],
        )

    def test_successor_normalizes_malformed_predecessor_errors(self) -> None:
        bundle = self.rebound(copy.deepcopy(self.bundle))
        for malformed in (None, [], {}, {"candidate_freeze_id": treatment.digest(b"partial")}):
            with self.subTest(predecessor=type(malformed).__name__), self.assertRaisesRegex(
                ValueError, "prior freeze",
            ):
                treatment.build_treatment_successor(
                    malformed, bundle, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
                )

    def test_successor_rejects_cross_bound_treatment_bundle(self) -> None:
        published = load_json(ROOT / "docs/ai/research/codex-g56r-002-executable-candidate-freeze.json")
        prior = copy.deepcopy(published)
        prior["candidate_freeze_id"] = "sha256:403051de7d5e0a0a358cd372533ef93da2a25609e8d01ab73cb529e820aaaf03"
        prior["telemetry_profile_id"] = "sha256:f39d0acd9403d193b07861c5cba5dac0e7ba901936ad542c18dd4eb008ec898b"
        prior.pop("treatment_contract_digest", None)
        prior.pop("treatment_evidence_digest", None)
        prior["published_at"] = TREATMENT_PREDECESSOR_PUBLISHED_AT
        prior["supersedes_candidate_freeze_id"] = None

        def assert_valid_but_rejected(bundle: dict, message: str) -> None:
            rebound = self.rebound(rebind_treatment_owners(bundle))
            treatment.validate_treatment_bundle(copy.deepcopy(rebound))
            with self.assertRaisesRegex(ValueError, message):
                treatment.build_treatment_successor(
                    prior, rebound, published_at=TREATMENT_SUCCESSOR_PUBLISHED_AT,
                )

        foreign_client = "sha256:" + "0" * 64
        client_rebound = copy.deepcopy(self.bundle)
        for entry in client_rebound["telemetry_profile"]:
            entry["client_identity_id"] = foreign_client
        environment = client_rebound["controlled_environments"][0]
        environment["client_identity_id"] = foreign_client
        environment["controlled_environment_id"] = treatment.content_id(environment, "controlled_environment_id")
        trace = client_rebound["treatment_traces"][0]
        trace["client_identity_id"] = foreign_client
        trace["controlled_environment_id"] = environment["controlled_environment_id"]
        proof = trace["configured_route_proof"]
        proof["client_identity_id"] = foreign_client
        proof["profile_entry_key"]["client_identity_id"] = foreign_client
        proof["proof_id"] = treatment.content_id(proof, "proof_id")
        assert_valid_but_rejected(client_rebound, "client identity")

        foreign_snapshot = "sha256:" + "0" * 64
        snapshot_rebound = copy.deepcopy(self.bundle)
        environment = snapshot_rebound["controlled_environments"][0]
        environment["runtime_capability_snapshot_id"] = foreign_snapshot
        environment["controlled_environment_id"] = treatment.content_id(environment, "controlled_environment_id")
        trace = snapshot_rebound["treatment_traces"][0]
        trace["controlled_environment_id"] = environment["controlled_environment_id"]
        trace["objective_binding"]["runtime_capability_snapshot_id"] = foreign_snapshot
        snapshot_rebound["route_resolutions"][0]["runtime_capability_snapshot_id"] = foreign_snapshot
        next(item for item in trace["observations"] if item["field_path"] == "route.runtime_capability_snapshot_id")["value"] = foreign_snapshot
        assert_valid_but_rejected(snapshot_rebound, "runtime snapshot")

        repository_rebound = copy.deepcopy(self.bundle)
        environment = repository_rebound["controlled_environments"][0]
        environment["repository_revision"] = "0" * 40
        environment["repository_tree_digest"] = "sha256:" + "0" * 64
        environment["controlled_environment_id"] = treatment.content_id(environment, "controlled_environment_id")
        trace = repository_rebound["treatment_traces"][0]
        trace["controlled_environment_id"] = environment["controlled_environment_id"]
        trace["repository_revision"] = environment["repository_revision"]
        trace["repository_tree_digest"] = environment["repository_tree_digest"]
        assert_valid_but_rejected(repository_rebound, "repository binding")

        instruction_rebound = copy.deepcopy(self.bundle)
        trace = instruction_rebound["treatment_traces"][0]
        trace["instruction_hash"] = "sha256:" + "0" * 64
        trace["configured_route_proof"]["instruction_hash"] = trace["instruction_hash"]
        trace["configured_route_proof"]["proof_id"] = treatment.content_id(trace["configured_route_proof"], "proof_id")
        next(item for item in trace["observations"] if item["field_path"] == "assignment.instruction_hash")["value"] = trace["instruction_hash"]
        assert_valid_but_rejected(instruction_rebound, "instruction identity")


if __name__ == "__main__":
    unittest.main()
