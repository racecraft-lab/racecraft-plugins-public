#!/usr/bin/env python3
"""Focused deterministic tests for the G56R-003 qualification contract."""

from __future__ import annotations

import copy
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import tomllib
import types
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
QUALIFICATION_MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/qualification_contracts.py"
QUALIFICATION_RUNNER_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/run-codex-qualification.py"
SUCCESSOR_TEST_PATH = ROOT / "tests/speckit-pro/unit/test-codex-successor-capability.py"
TREATMENT_MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py"
TREATMENT_FIXTURE_PATH = ROOT / "tests/speckit-pro/unit/fixtures/capability-treatment-replay/treatment-replay.json"
MANIFEST_PATH = ROOT / "docs/ai/research/codex-agent-route-candidate-manifest.json"
PLUGIN_ROOT = ROOT / "speckit-pro"
MATERIALIZER_MODULE_PATH = PLUGIN_ROOT / "speckit_pro_runner/agent_materialization.py"
PHASE_AGENT_SOURCE = PLUGIN_ROOT / "codex-agents/phase-executor.toml"
PHASE_AGENT_RELATIVE_PATH = "speckit-pro/codex-agents/phase-executor.toml"


def load_treatment_runtime() -> dict[str, types.ModuleType]:
    dependency_names = (
        "treatment_trace_capability", "treatment_trace_authority", "treatment_trace_io",
        "treatment_trace_json_schema", "treatment_trace_model", "treatment_trace_fields",
        "treatment_trace_bundle", "treatment_trace_fixture", "treatment_trace_replay",
        "treatment_trace_successor", "treatment_trace_cli",
    )
    package_name = f"_g56r_qualification_treatment_runtime_{uuid4().hex}"
    package = types.ModuleType(package_name)
    package.__package__ = package_name
    package.__path__ = [str(TREATMENT_MODULE_PATH.parent)]
    package.__spec__ = importlib.machinery.ModuleSpec(package_name, loader=None, is_package=True)
    sys.modules[package_name] = package
    try:
        cli_name = f"{package_name}.treatment_trace_cli"
        cli_spec = importlib.util.spec_from_file_location(
            cli_name, TREATMENT_MODULE_PATH.with_name("treatment_trace_cli.py"),
        )
        if cli_spec is None or cli_spec.loader is None:
            raise RuntimeError("cannot load treatment test dependencies")
        cli = importlib.util.module_from_spec(cli_spec)
        sys.modules[cli_name] = cli
        cli_spec.loader.exec_module(cli)
        return {
            name: sys.modules[f"{package_name}.{name}"]
            for name in dependency_names
        }
    finally:
        for module_name in tuple(sys.modules):
            if module_name == package_name or module_name.startswith(f"{package_name}."):
                sys.modules.pop(module_name, None)


def load_treatment_facade(name: str):
    facade_spec = importlib.util.spec_from_file_location(name, TREATMENT_MODULE_PATH)
    if facade_spec is None or facade_spec.loader is None:
        raise RuntimeError(f"cannot load {TREATMENT_MODULE_PATH}")
    facade = importlib.util.module_from_spec(facade_spec)
    facade_spec.loader.exec_module(facade)
    return facade


def load_qualification_module():
    if not QUALIFICATION_MODULE_PATH.exists():
        return types.SimpleNamespace(
            content_id=lambda value, identity_field: treatment.content_id(value, identity_field),
            validate_qualification_bundle=lambda bundle, **_: copy.deepcopy(bundle),
        )
    package_name = f"_g56r_qualification_contract_runtime_{uuid4().hex}"
    package = types.ModuleType(package_name)
    package.__package__ = package_name
    package.__path__ = [str(QUALIFICATION_MODULE_PATH.parent)]
    package.__spec__ = importlib.machinery.ModuleSpec(package_name, loader=None, is_package=True)
    sys.modules[package_name] = package
    try:
        module_name = f"{package_name}.qualification_contracts"
        spec = importlib.util.spec_from_file_location(module_name, QUALIFICATION_MODULE_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load {QUALIFICATION_MODULE_PATH}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        for module_name in tuple(sys.modules):
            if module_name == package_name or module_name.startswith(f"{package_name}."):
                sys.modules.pop(module_name, None)


def load_materializer_module():
    if str(PLUGIN_ROOT) not in sys.path:
        sys.path.insert(0, str(PLUGIN_ROOT))
    module_name = f"_g56r_003_agent_materialization_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MATERIALIZER_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MATERIALIZER_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_qualification_cli():
    module_name = f"_g56r_003_codex_qualification_cli_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, QUALIFICATION_RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {QUALIFICATION_RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_successor_test_helpers():
    module_name = f"_g56r_003_successor_test_helpers_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, SUCCESSOR_TEST_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SUCCESSOR_TEST_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


TREATMENT_INTERNALS = load_treatment_runtime()
treatment = load_treatment_facade("g56r_003_treatment_facade")
treatment_authority = TREATMENT_INTERNALS["treatment_trace_authority"]
treatment_fields = TREATMENT_INTERNALS["treatment_trace_fields"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def replay_trace(bundle: dict, case_id: str) -> dict:
    slug = case_id.removeprefix("TRACE-").lower()
    return next(
        item for item in bundle["treatment_traces"]
        if item["context"]["turnId"] == f"turn-fixture-{slug}"
    )


def single_treatment_case(bundle: dict, case_id: str) -> dict:
    isolated = copy.deepcopy(bundle)
    trace = replay_trace(isolated, case_id)
    execution_trace_id = trace["objective_binding"]["execution_trace_id"]
    isolated["treatment_traces"] = [trace]
    isolated["controlled_environments"] = [
        item for item in isolated["controlled_environments"]
        if item["controlled_environment_id"] == trace["controlled_environment_id"]
    ]
    isolated["route_resolutions"] = [
        item for item in isolated["route_resolutions"]
        if item["route_resolution_id"] == trace["objective_binding"]["route_resolution_id"]
    ]
    referenced_qualifications = {
        item["prequalification_evidence_id"]
        for item in trace["reroute_destination_assessments"]
        if item["prequalification_evidence_id"] is not None
    }
    isolated["qualification_evidence_registry"] = [
        item for item in isolated["qualification_evidence_registry"]
        if item["qualification_evidence_id"] in referenced_qualifications
    ]
    isolated["fixture_provenance"]["expected_dispositions"] = [{
        "execution_trace_id": execution_trace_id,
        "treatment_disposition": trace["treatment_disposition"],
    }]
    return isolated


def rebound(bundle: dict) -> dict:
    bundle["treatment_contract_digest"] = treatment.schema_file_digest()
    bundle["telemetry_profile_id"] = treatment.telemetry_profile_id(
        bundle["schema_version"], bundle["telemetry_profile"], bundle["treatment_contract_digest"],
    )
    return bundle


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
    return {
        owner["qualification_evidence_id"]: copy.deepcopy(owner)
        for owner in bundle["qualification_evidence_registry"]
        if owner["authority_kind"] == "owned_external"
    }


REROUTE_REASON_FAILURES = {
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
    "reroute_self_target": "reroute_unapproved",
    "orphan_reroute_destination_assessment": "reroute_ambiguous",
}


def declare_treatment_result(bundle: dict, failure_codes: list[str], disposition: str, reasons: list[str]) -> dict:
    trace = bundle["treatment_traces"][0]
    trace["treatment_failures"] = [{
        "failure_code": code, "affected_field": "treatment.evidence",
        "expected_evidence_ref": None, "observed_evidence_ref": None,
        "resulting_disposition": treatment.FAILURE_DISPOSITIONS[code],
    } for code in failure_codes]
    trace["treatment_disposition"] = disposition
    trace["disposition_reasons"] = reasons
    bundle["fixture_provenance"]["expected_dispositions"] = [{
        "execution_trace_id": trace["objective_binding"]["execution_trace_id"],
        "treatment_disposition": disposition,
    }]
    return bundle


def declare_reroute_result(bundle: dict, trusted: dict[str, dict] | None = None) -> dict:
    trace = bundle["treatment_traces"][0]
    qualification = {
        item["qualification_evidence_id"]: item for item in bundle["qualification_evidence_registry"]
    }
    disposition, detailed_reasons = treatment_fields._reroute_disposition(
        trace, trace["service_reroute_events"], trace["reroute_destination_assessments"],
        qualification, trusted or {}, treatment_authority._canonical_routes(load_json(MANIFEST_PATH)),
    )
    failure_codes = list(dict.fromkeys(
        REROUTE_REASON_FAILURES[reason] for reason in detailed_reasons
        if reason in REROUTE_REASON_FAILURES
    ))
    reasons = sorted(set(failure_codes) | set(detailed_reasons)) if disposition == "hard_fail" else detailed_reasons
    return declare_treatment_result(bundle, failure_codes, disposition, reasons)


def make_owned_reroute_case(bundle: dict, authority: str = "owned_external") -> dict:
    trace = bundle["treatment_traces"][0]
    selected = qualification_owner("owned_external")
    bundle["qualification_evidence_registry"] = [] if authority == "missing" else [selected]
    event = {
        "surface": trace["surface"], "threadId": trace["context"]["threadId"], "turnId": trace["context"]["turnId"],
        "fromModel": trace["requested_model"], "toModel": "gpt-5.5", "reason": "fixture_service_reroute",
        "evidence_digest": treatment.digest(b"fixture-reroute-evidence"),
    }
    event["event_id"] = treatment.content_id(event, "event_id")
    assessment = {
        "event_id": event["event_id"],
        "destination_candidate_route_id": selected["destination_candidate_route_id"],
        "destination_agent_contract_id": selected["destination_agent_contract_id"],
        "destination_named_agent": selected["destination_named_agent"],
        "assessment": "prequalified_same_agent",
        "prequalification_evidence_id": selected["qualification_evidence_id"],
    }
    trace["service_reroute_events"] = [event]
    trace["supported_effective_model"] = event["toModel"]
    trace["supported_effective_effort"] = None
    next(item for item in trace["observations"] if item["field_path"] == "reroute.events").update({
        "observation_state": "observed_value", "value": [copy.deepcopy(event)],
        "evidence_ref": "fixture://trace/reroute-events", "captured_at": "2026-07-17T04:01:00Z",
    })
    next(item for item in trace["observations"] if item["field_path"] == "assignment.supported_effective_model").update({
        "observation_state": "observed_value", "value": event["toModel"],
        "evidence_ref": "fixture://trace/effective-model", "captured_at": "2026-07-17T04:01:00Z",
    })
    trace["reroute_destination_assessments"] = [] if authority == "missing" else [assessment]
    trusted = trusted_external_qualification(bundle) if authority == "owned_external" else {}
    return declare_reroute_result(bundle, trusted)


def content_id(value: dict, identity_field: str) -> str:
    return treatment.content_id(value, identity_field)


def observed(field_path: str, value: object) -> dict:
    return {
        "field_path": field_path,
        "observation_state": "observed_value",
        "value": copy.deepcopy(value),
        "evidence_ref": f"fixture://qualification/{field_path.replace('.', '-')}",
        "captured_at": "2026-07-18T04:01:00Z",
    }


def null_observed(field_path: str, state: str = "explicit_null") -> dict:
    return {
        "field_path": field_path,
        "observation_state": state,
        "value": None,
        "evidence_ref": "fixture://qualification/null" if state == "explicit_null" else None,
        "captured_at": "2026-07-18T04:01:00Z" if state == "explicit_null" else None,
    }


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"


def write_canonical_json(path: Path, value: object) -> None:
    path.write_text(canonical_json(value), encoding="utf-8")


def run_qualification_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(QUALIFICATION_RUNNER_PATH), *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=env,
        shell=False,
        check=False,
    )


def phase_policy_for_trace(trace: dict) -> str:
    instructions = tomllib.loads(PHASE_AGENT_SOURCE.read_text(encoding="utf-8"))["developer_instructions"]
    sandbox_mode = str(trace["sandbox"]["mode"]).replace("_", "-")
    fields = {
        "name": trace["named_agent"],
        "description": "Fixture policy for qualification CLI validation.",
        "model": trace["requested_model"],
        "model_reasoning_effort": trace["requested_effort"],
        "sandbox_mode": sandbox_mode,
        "developer_instructions": instructions,
    }
    return "".join(
        f"{key} = {json.dumps(value, ensure_ascii=False)}\n"
        for key, value in fields.items()
    )


def build_successor_freeze_from_sanitized_catalog() -> dict:
    helpers = load_successor_test_helpers()
    successor = helpers.load_successor_module(f"_g56r_003_successor_e2e_{uuid4().hex}")
    fixture = helpers.load_json(helpers.FIXTURE_PATH)
    manifest = helpers.load_json(helpers.MANIFEST_PATH)
    helper = helpers.CodexSuccessorCapabilityTests(
        "test_successor_build_is_additive_and_diagnostics_do_not_grant_availability",
    )
    helper.fixture = fixture
    helper.manifest = manifest
    helper.identity = helpers.capabilities.build_client_identity(fixture["client_identity"])
    predecessor = helper.predecessor_freeze()
    request = helper.successor_request(predecessor, successor)
    freeze = successor.build_successor_freeze(predecessor, request, manifest=manifest)
    return successor.validate_successor_freeze(freeze, predecessor, request, manifest=manifest)


def materialize_trace_policy(trace: dict):
    module = load_materializer_module()
    source_bytes = phase_policy_for_trace(trace).encode("utf-8")
    return module.materialize_agent_policy(
        source_relative_path=PHASE_AGENT_RELATIVE_PATH,
        source_bytes=source_bytes,
        candidate_route={
            "agent_name": trace["named_agent"],
            "model": trace["requested_model"],
            "model_reasoning_effort": trace["requested_effort"],
        },
        parent_controls={
            "sandbox_mode": str(trace["sandbox"]["mode"]).replace("_", "-"),
        },
    )


def apply_materialized_source(wrapper: dict, source_path: Path) -> dict:
    module = load_materializer_module()
    trace = wrapper["treatment_bundle"]["treatment_traces"][0]
    materialized = module.materialize_agent_policy(
        source_relative_path=PHASE_AGENT_RELATIVE_PATH,
        source_bytes=source_path.read_bytes(),
    )
    materialization = wrapper["materializations"][0]
    materialization["requested_model"] = trace["requested_model"]
    materialization["requested_effort"] = trace["requested_effort"]
    materialization["destination_bytes_digest"] = materialized.destination_bytes_digest
    materialization["instruction_digest"] = materialized.instruction_digest
    materialization["materialization_id"] = content_id(materialization, "materialization_id")
    assignment = wrapper["qualification_assignments"][0]
    assignment["materialization_id"] = materialization["materialization_id"]
    assignment["installed_agent_bytes_digest"] = materialized.destination_bytes_digest
    next(
        item for item in assignment["observations"]
        if item["field_path"] == "installed.agent_bytes_digest"
    )["value"] = materialized.destination_bytes_digest
    return set_assignment_ids(wrapper)


def set_assignment_ids(wrapper: dict) -> dict:
    for materialization in wrapper.get("materializations", []):
        materialization["materialization_id"] = content_id(materialization, "materialization_id")
    for assignment in wrapper["qualification_assignments"]:
        assignment["qualification_assignment_id"] = content_id(assignment, "qualification_assignment_id")
    assignment_ids = {
        item["execution_trace_id"]: item["qualification_assignment_id"]
        for item in wrapper["qualification_assignments"]
    }
    traces = {
        item["objective_binding"]["execution_trace_id"]: item
        for item in wrapper["treatment_bundle"]["treatment_traces"]
    }
    for trace_wrapper in wrapper["qualification_traces"]:
        trace_wrapper["qualification_assignment_id"] = assignment_ids[trace_wrapper["execution_trace_id"]]
        trace_wrapper["source_trace_digest"] = treatment.digest(traces[trace_wrapper["execution_trace_id"]])
        trace_wrapper["qualification_trace_id"] = content_id(trace_wrapper, "qualification_trace_id")
    return wrapper


def successor_freeze_binding(successor_freeze: dict, candidate_route_id: str) -> dict:
    decision = next(
        item for item in successor_freeze["tuple_decisions"]
        if item["candidate_route_id"] == candidate_route_id
    )
    return {
        "candidate_freeze_id": successor_freeze["candidate_freeze_id"],
        "runtime_capability_snapshot_id": successor_freeze["runtime_capability_snapshot_id"],
        "catalog_capture_digest": successor_freeze["runtime_capability_snapshot"]["catalog_capture_digest"],
        "included_candidate_route_id": candidate_route_id,
        "tuple_decision_digest": treatment.digest(decision),
    }


def qualification_bundle(treatment_bundle: dict, *, score_eligible: bool = True, delivery_status: str = "delivered") -> dict:
    source = rebound(copy.deepcopy(treatment_bundle))
    trace = source["treatment_traces"][0]
    proof = trace["configured_route_proof"]
    materialization = {
        "materialization_id": "sha256:" + "0" * 64,
        "owner_spec_id": "G56R-003",
        "candidate_route_id": trace["objective_binding"]["candidate_route_id"],
        "agent_contract_id": trace["objective_binding"]["agent_contract_id"],
        "requested_model": trace["requested_model"],
        "requested_effort": trace["requested_effort"],
        "destination_bytes_digest": treatment.digest(b"fixture-materialized-agent-destination-bytes"),
        "instruction_digest": trace["instruction_hash"],
        "configuration_digest": proof["configuration_hash"],
    }
    materialization["materialization_id"] = content_id(materialization, "materialization_id")
    assignment = {
        "qualification_assignment_id": "sha256:" + "0" * 64,
        "owner_spec_id": "G56R-003",
        "execution_trace_id": trace["objective_binding"]["execution_trace_id"],
        "candidate_route_id": trace["objective_binding"]["candidate_route_id"],
        "agent_contract_id": trace["objective_binding"]["agent_contract_id"],
        "requested_model": trace["requested_model"],
        "requested_effort": trace["requested_effort"],
        "materialization_id": materialization["materialization_id"],
        "installed_agent_bytes_digest": materialization["destination_bytes_digest"],
        "configured_route_proof_id": proof["proof_id"],
        "delivery_status": delivery_status,
        "score_eligible": score_eligible,
        "score_ineligibility_reasons": [] if score_eligible else [f"delivery_{delivery_status}"],
        "observations": [
            observed("assignment.requested_model", trace["requested_model"]),
            observed("assignment.requested_effort", trace["requested_effort"]),
            observed("installed.agent_bytes_digest", materialization["destination_bytes_digest"]),
            observed("configured.route_proof", {
                "proof_id": proof["proof_id"],
                "candidate_route_id": proof["candidate_route_id"],
                "configuration_hash": proof["configuration_hash"],
            }),
            observed("delivery.reroute_monitoring", proof["reroute_monitoring_complete"]),
            observed("delivery.status", delivery_status),
            null_observed("qualification.notes"),
        ],
    }
    wrapper = {
        "schema_version": "1.0.0",
        "owner_spec_id": "G56R-003",
        "treatment_bundle": source,
        "materializations": [materialization],
        "qualification_assignments": [assignment],
        "qualification_traces": [{
            "qualification_trace_id": "sha256:" + "0" * 64,
            "owner_spec_id": "G56R-003",
            "source_spec_id": "G56R-002",
            "qualification_assignment_id": "sha256:" + "0" * 64,
            "execution_trace_id": assignment["execution_trace_id"],
            "source_trace_digest": "sha256:" + "0" * 64,
        }],
    }
    return set_assignment_ids(wrapper)


class QualificationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.replay_bundle = load_json(TREATMENT_FIXTURE_PATH)
        cls.base_treatment = single_treatment_case(cls.replay_bundle, "TRACE-SUCCESS")

    def setUp(self) -> None:
        self.qualification = load_qualification_module()

    def validate(self, wrapper: dict, trusted: dict[str, dict] | None = None) -> dict:
        return self.qualification.validate_qualification_bundle(
            wrapper, trusted_qualification_evidence=trusted,
        )

    def assert_invalid(self, wrapper: dict, message: str = "") -> None:
        with self.assertRaises(ValueError, msg=message):
            self.validate(wrapper)

    def test_public_api_loads_from_assigned_module(self) -> None:
        expected_api = {
            "DELIVERY_STATUSES", "MANDATORY_OBSERVATION_FIELDS",
            "MATERIALIZATION_FIELDS", "NULL_ONLY_OBSERVATION_FIELDS",
            "QUALIFICATION_OBSERVATION_FIELDS", "QUALIFICATION_OWNER_SPEC_ID",
            "QUALIFICATION_SCHEMA_VERSION", "TREATMENT_OWNER_SPEC_ID",
            "validate_qualification_bundle",
        }
        self.assertTrue(QUALIFICATION_MODULE_PATH.exists())
        self.assertTrue(callable(self.qualification.validate_qualification_bundle))
        self.assertEqual(set(self.qualification.__all__), expected_api)

    def test_scoreable_assignment_wraps_g56r002_trace_and_is_idempotent(self) -> None:
        wrapper = qualification_bundle(self.base_treatment)
        first = self.validate(copy.deepcopy(wrapper))
        second = self.validate(copy.deepcopy(first))
        self.assertEqual(treatment.canonical_bytes(first), treatment.canonical_bytes(second))
        assignment = first["qualification_assignments"][0]
        self.assertTrue(assignment["score_eligible"])
        self.assertEqual(assignment["score_ineligibility_reasons"], [])
        self.assertEqual(first["qualification_traces"][0]["owner_spec_id"], "G56R-003")
        self.assertEqual(
            first["qualification_traces"][0]["execution_trace_id"],
            first["qualification_assignments"][0]["execution_trace_id"],
        )

    def test_mandatory_observation_coverage_and_null_only_states_are_closed(self) -> None:
        for state in ("explicit_null", "missing", "unavailable", "undocumented"):
            with self.subTest(state=state):
                wrapper = qualification_bundle(self.base_treatment)
                note = next(
                    item for item in wrapper["qualification_assignments"][0]["observations"]
                    if item["field_path"] == "qualification.notes"
                )
                note.update(null_observed("qualification.notes", state))
                self.validate(set_assignment_ids(wrapper))

        missing = qualification_bundle(self.base_treatment)
        missing["qualification_assignments"][0]["observations"] = [
            item for item in missing["qualification_assignments"][0]["observations"]
            if item["field_path"] != "configured.route_proof"
        ]
        self.assert_invalid(set_assignment_ids(missing), "mandatory proof observation should be required")

        valued_null = qualification_bundle(self.base_treatment)
        note = next(
            item for item in valued_null["qualification_assignments"][0]["observations"]
            if item["field_path"] == "qualification.notes"
        )
        note["observation_state"] = "unavailable"
        note["value"] = "free-form"
        self.assert_invalid(set_assignment_ids(valued_null), "null-only states cannot carry values")

    def test_exact_model_effort_installed_bytes_and_configured_route_proof_are_required(self) -> None:
        mutations = [
            ("requested_model", "different-model"),
            ("requested_effort", "medium"),
            ("installed_agent_bytes_digest", "sha256:" + "f" * 64),
            ("configured_route_proof_id", "sha256:" + "a" * 64),
        ]
        for field, value in mutations:
            with self.subTest(field=field):
                wrapper = qualification_bundle(self.base_treatment)
                wrapper["qualification_assignments"][0][field] = value
                self.assert_invalid(set_assignment_ids(wrapper))

    def test_materialization_separates_installed_bytes_from_instruction_digest(self) -> None:
        wrapper = qualification_bundle(self.base_treatment)
        materialization = wrapper["materializations"][0]
        assignment = wrapper["qualification_assignments"][0]
        self.assertNotEqual(
            materialization["destination_bytes_digest"],
            materialization["instruction_digest"],
        )
        self.assertEqual(assignment["installed_agent_bytes_digest"], materialization["destination_bytes_digest"])
        self.assertEqual(
            materialization["instruction_digest"],
            wrapper["treatment_bundle"]["treatment_traces"][0]["instruction_hash"],
        )
        self.validate(copy.deepcopy(wrapper))

        parsed_equivalent_wrong_bytes = copy.deepcopy(wrapper)
        assignment = parsed_equivalent_wrong_bytes["qualification_assignments"][0]
        assignment["installed_agent_bytes_digest"] = materialization["instruction_digest"]
        next(
            item for item in assignment["observations"]
            if item["field_path"] == "installed.agent_bytes_digest"
        )["value"] = materialization["instruction_digest"]
        self.assert_invalid(
            set_assignment_ids(parsed_equivalent_wrong_bytes),
            "installed bytes must bind destination bytes, not parsed instruction digest",
        )

    def test_score_eligibility_requires_delivery_canary_and_reroute_monitoring(self) -> None:
        monitoring = qualification_bundle(self.base_treatment, score_eligible=False, delivery_status="monitoring_incomplete")
        next(
            item for item in monitoring["qualification_assignments"][0]["observations"]
            if item["field_path"] == "delivery.reroute_monitoring"
        )["value"] = False
        monitoring["qualification_assignments"][0]["score_ineligibility_reasons"] = ["delivery_monitoring_incomplete"]
        validated = self.validate(set_assignment_ids(monitoring))
        self.assertFalse(validated["qualification_assignments"][0]["score_eligible"])

        forged = copy.deepcopy(monitoring)
        forged["qualification_assignments"][0]["score_eligible"] = True
        forged["qualification_assignments"][0]["score_ineligibility_reasons"] = []
        self.assert_invalid(set_assignment_ids(forged), "monitoring gaps cannot be score eligible")

        failed_canary = qualification_bundle(self.base_treatment, score_eligible=True)
        trace = failed_canary["treatment_bundle"]["treatment_traces"][0]
        trace["delivery_canary"]["status"] = "failed"
        next(item for item in trace["observations"] if item["field_path"] == "treatment.delivery_canary")["value"] = copy.deepcopy(trace["delivery_canary"])
        self.assert_invalid(set_assignment_ids(failed_canary), "failed delivery canary must block scoring")

    def test_service_reroutes_stay_immutable_and_non_scorable(self) -> None:
        rerouted = make_owned_reroute_case(copy.deepcopy(self.base_treatment))
        route_before = copy.deepcopy(rerouted["route_resolutions"][0])
        wrapper = qualification_bundle(rerouted, score_eligible=False, delivery_status="service_rerouted")
        wrapper["qualification_assignments"][0]["score_ineligibility_reasons"] = ["delivery_service_rerouted"]
        validated = self.validate(set_assignment_ids(wrapper), trusted_external_qualification(rerouted))
        self.assertFalse(validated["qualification_assignments"][0]["score_eligible"])
        self.assertEqual(validated["treatment_bundle"]["route_resolutions"][0], route_before)

        forged = copy.deepcopy(wrapper)
        forged["qualification_assignments"][0]["score_eligible"] = True
        forged["qualification_assignments"][0]["score_ineligibility_reasons"] = []
        with self.assertRaises(ValueError):
            self.validate(set_assignment_ids(forged), trusted_external_qualification(rerouted))

    def test_delivery_failures_cover_misdelivery_ambiguous_unapproved_and_unidentifiable(self) -> None:
        cases: list[tuple[str, dict, dict[str, dict]]] = [
            (
                "misdelivered",
                single_treatment_case(self.replay_bundle, "TRACE-MISDELIVERY"),
                {},
            ),
            (
                "unidentifiable",
                make_owned_reroute_case(copy.deepcopy(self.base_treatment), authority="missing"),
                {},
            ),
        ]
        unapproved = make_owned_reroute_case(copy.deepcopy(self.base_treatment), authority="untrusted")
        cases.append(("unapproved", unapproved, {}))
        ambiguous = make_owned_reroute_case(copy.deepcopy(self.base_treatment))
        second = copy.deepcopy(ambiguous["treatment_traces"][0]["reroute_destination_assessments"][0])
        second["assessment"] = "unknown"
        ambiguous["treatment_traces"][0]["reroute_destination_assessments"].append(second)
        declare_reroute_result(ambiguous, trusted_external_qualification(ambiguous))
        cases.append(("ambiguous", ambiguous, trusted_external_qualification(ambiguous)))

        for delivery_status, treatment_bundle, trusted in cases:
            with self.subTest(delivery_status=delivery_status):
                wrapper = qualification_bundle(
                    treatment_bundle, score_eligible=False, delivery_status=delivery_status,
                )
                wrapper["qualification_assignments"][0]["score_ineligibility_reasons"] = [f"delivery_{delivery_status}"]
                validated = self.qualification.validate_qualification_bundle(
                    set_assignment_ids(wrapper), trusted_qualification_evidence=trusted,
                )
                self.assertFalse(validated["qualification_assignments"][0]["score_eligible"])
                self.assertEqual(validated["qualification_assignments"][0]["delivery_status"], delivery_status)

    def test_sanitized_successor_freeze_materialization_assignment_and_trace_replay_join(self) -> None:
        successor_freeze = build_successor_freeze_from_sanitized_catalog()
        self.assertGreater(len(successor_freeze["included_candidate_route_ids"]), 0)

        trace = copy.deepcopy(self.base_treatment)["treatment_traces"][0]
        candidate_route_id = trace["objective_binding"]["candidate_route_id"]
        self.assertIn(candidate_route_id, successor_freeze["included_candidate_route_ids"])
        materialized = materialize_trace_policy(trace)

        wrapper = qualification_bundle(self.base_treatment)
        wrapper["successor_freeze_binding"] = successor_freeze_binding(
            successor_freeze, candidate_route_id,
        )
        materialization = wrapper["materializations"][0]
        materialization["requested_model"] = trace["requested_model"]
        materialization["requested_effort"] = trace["requested_effort"]
        materialization["destination_bytes_digest"] = materialized.destination_bytes_digest
        materialization["instruction_digest"] = materialized.instruction_digest
        materialization["materialization_id"] = content_id(materialization, "materialization_id")
        assignment = wrapper["qualification_assignments"][0]
        assignment["materialization_id"] = materialization["materialization_id"]
        assignment["installed_agent_bytes_digest"] = materialized.destination_bytes_digest
        next(
            item for item in assignment["observations"]
            if item["field_path"] == "installed.agent_bytes_digest"
        )["value"] = materialized.destination_bytes_digest
        wrapper = set_assignment_ids(wrapper)

        expected_assignment_id = wrapper["qualification_assignments"][0]["qualification_assignment_id"]
        expected_materialization_id = wrapper["materializations"][0]["materialization_id"]
        expected_trace_wrapper = copy.deepcopy(wrapper["qualification_traces"][0])
        expected_source_trace_digest = expected_trace_wrapper["source_trace_digest"]
        expected_binding = copy.deepcopy(wrapper["successor_freeze_binding"])

        try:
            validated = self.qualification.validate_qualification_bundle(
                copy.deepcopy(wrapper),
                successor_freeze=copy.deepcopy(successor_freeze),
            )
        except TypeError as exc:
            self.fail(f"qualification replay must accept successor freeze authority: {exc}")

        validated_assignment = validated["qualification_assignments"][0]
        validated_materialization = validated["materializations"][0]
        validated_trace = validated["treatment_bundle"]["treatment_traces"][0]
        self.assertEqual(validated["successor_freeze_binding"], expected_binding)
        self.assertEqual(validated_assignment["qualification_assignment_id"], expected_assignment_id)
        self.assertEqual(validated_materialization["materialization_id"], expected_materialization_id)
        self.assertEqual(validated_assignment["materialization_id"], expected_materialization_id)
        self.assertEqual(validated_materialization["destination_bytes_digest"], materialized.destination_bytes_digest)
        self.assertEqual(validated_materialization["instruction_digest"], materialized.instruction_digest)
        self.assertEqual(validated_assignment["installed_agent_bytes_digest"], materialized.destination_bytes_digest)
        self.assertTrue(validated_assignment["score_eligible"])
        self.assertEqual(validated_assignment["score_ineligibility_reasons"], [])
        self.assertEqual(
            validated_trace["objective_binding"]["execution_trace_id"],
            trace["objective_binding"]["execution_trace_id"],
        )
        self.assertEqual(validated["qualification_traces"][0], expected_trace_wrapper)
        self.assertEqual(validated["qualification_traces"][0]["source_trace_digest"], expected_source_trace_digest)

    def test_assignments_and_trace_wrappers_are_one_to_one_and_conflict_closed(self) -> None:
        duplicate = qualification_bundle(self.base_treatment)
        duplicate["qualification_assignments"].append(copy.deepcopy(duplicate["qualification_assignments"][0]))
        self.assert_invalid(set_assignment_ids(duplicate), "one assignment per treatment trace")

        conflict = qualification_bundle(self.base_treatment)
        conflict["qualification_traces"][0]["execution_trace_id"] = "sha256:" + "b" * 64
        conflict["qualification_traces"][0]["qualification_trace_id"] = content_id(
            conflict["qualification_traces"][0], "qualification_trace_id",
        )
        self.assert_invalid(conflict, "trace wrapper join must be exact")

    def test_cli_reports_legacy_smoke_as_non_release_and_stale_runner_absent(self) -> None:
        self.assertTrue(
            QUALIFICATION_RUNNER_PATH.exists(),
            "G56R-003 qualification must use its own durable entry point",
        )
        stale_paths = sorted(path.relative_to(ROOT).as_posix() for path in ROOT.rglob("run_codex_role_eval.py"))
        self.assertEqual(stale_paths, [])

        completed = run_qualification_cli("legacy-smoke-status")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.stdout, canonical_json(payload))
        self.assertEqual(payload["status"], "non_release_smoke")
        self.assertFalse(payload["release_qualification"])
        self.assertEqual(payload["legacy_runner"], "tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py")
        self.assertEqual(payload["qualification_entry_point"], "tests/speckit-pro/layer6-efficiency/run-codex-qualification.py")

    def test_cli_publish_materialization_uses_shared_materializer_and_canonical_json(self) -> None:
        self.assertTrue(QUALIFICATION_RUNNER_PATH.exists())
        trace = copy.deepcopy(self.base_treatment)["treatment_traces"][0]
        expected_materializer = load_materializer_module()

        with tempfile.TemporaryDirectory() as temporary:
            source_path = Path(temporary) / "phase-executor.toml"
            source_path.write_text(phase_policy_for_trace(trace), encoding="utf-8")
            expected = expected_materializer.materialize_agent_policy(
                source_relative_path=PHASE_AGENT_RELATIVE_PATH,
                source_bytes=source_path.read_bytes(),
            )

            completed = run_qualification_cli(
                "publish-materialization",
                "--agent-policy-source", str(source_path),
                "--source-relative-path", PHASE_AGENT_RELATIVE_PATH,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.stdout, canonical_json(payload))
        self.assertEqual(payload["status"], "materialized")
        self.assertEqual(payload["schema_version"], expected_materializer.MATERIALIZATION_SCHEMA_VERSION)
        self.assertEqual(payload["materializer_version"], expected_materializer.MATERIALIZER_VERSION)
        self.assertEqual(payload["materializer_binding"], expected.materializer_binding)
        self.assertEqual(payload["source_binding"], expected.source_binding)
        self.assertEqual(payload["destination_bytes_digest"], expected.destination_bytes_digest)
        self.assertEqual(payload["instruction_digest"], trace["instruction_hash"])
        self.assertNotIn("destination_bytes", payload)

    def test_cli_validate_treatment_uses_materializer_and_accepts_score_eligible_bundle(self) -> None:
        self.assertTrue(QUALIFICATION_RUNNER_PATH.exists())

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_path = root / "phase-executor.toml"
            source_path.write_text(
                phase_policy_for_trace(copy.deepcopy(self.base_treatment)["treatment_traces"][0]),
                encoding="utf-8",
            )
            bundle_path = root / "qualification.json"
            wrapper = apply_materialized_source(qualification_bundle(self.base_treatment), source_path)
            write_canonical_json(bundle_path, wrapper)

            completed = run_qualification_cli(
                "validate-treatment",
                "--qualification-bundle", str(bundle_path),
                "--agent-policy-source", str(source_path),
                "--source-relative-path", PHASE_AGENT_RELATIVE_PATH,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.stdout, canonical_json(payload))
        self.assertEqual(payload["status"], "valid")
        self.assertEqual(payload["validated_treatment"], "exact")
        self.assertEqual(payload["score_eligible_count"], 1)
        self.assertEqual(payload["score_ineligible_count"], 0)
        self.assertEqual(payload["materializer_source_path"], "speckit-pro/speckit_pro_runner/agent_materialization.py")

    def test_cli_validate_treatment_rejects_source_bytes_that_do_not_match_materialization(self) -> None:
        self.assertTrue(QUALIFICATION_RUNNER_PATH.exists())

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original_source = root / "phase-executor.toml"
            trace = copy.deepcopy(self.base_treatment)["treatment_traces"][0]
            original_source.write_text(phase_policy_for_trace(trace), encoding="utf-8")
            wrapper = apply_materialized_source(qualification_bundle(self.base_treatment), original_source)
            bundle_path = root / "qualification.json"
            write_canonical_json(bundle_path, wrapper)
            changed_source = root / "changed-phase-executor.toml"
            changed_source.write_text(
                phase_policy_for_trace(trace).replace(
                    "Fixture policy for qualification CLI validation.",
                    "Changed fixture policy for qualification CLI validation.",
                ),
                encoding="utf-8",
            )

            completed = run_qualification_cli(
                "validate-treatment",
                "--qualification-bundle", str(bundle_path),
                "--agent-policy-source", str(changed_source),
                "--source-relative-path", PHASE_AGENT_RELATIVE_PATH,
            )

        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.stdout, canonical_json(payload))
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["command"], "validate-treatment")
        self.assertIn("source materialization", payload["error"])

    def test_cli_score_refuses_score_before_validated_exact_treatment(self) -> None:
        self.assertTrue(QUALIFICATION_RUNNER_PATH.exists())

        with tempfile.TemporaryDirectory() as temporary:
            score_request = Path(temporary) / "score-request.json"
            write_canonical_json(score_request, {"schema_version": "score-request.v1"})
            completed = run_qualification_cli("score", "--score-request", str(score_request))

        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.stdout, canonical_json(payload))
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["reason"], "score_before_treatment_refused")
        self.assertIn("validated exact treatment", payload["message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
