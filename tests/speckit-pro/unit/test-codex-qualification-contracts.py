#!/usr/bin/env python3
"""Focused deterministic tests for the G56R-003 qualification contract."""

from __future__ import annotations

import copy
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import re
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
SCORING_TEST_PATH = ROOT / "tests/speckit-pro/unit/test-codex-qualification-scoring.py"
TREATMENT_MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py"
TREATMENT_FIXTURE_PATH = ROOT / "tests/speckit-pro/unit/fixtures/capability-treatment-replay/treatment-replay.json"
CONTRACT_DIR = ROOT / "tests/speckit-pro/layer6-efficiency/contracts"
CALIBRATION_PROTOCOL_SCHEMA_PATH = CONTRACT_DIR / "calibration-protocol.schema.json"
CALIBRATION_COMPLETION_SCHEMA_PATH = CONTRACT_DIR / "calibration-completion.schema.json"
EXPERIMENT_POLICY_SCHEMA_PATH = CONTRACT_DIR / "experiment-policy.schema.json"
ENVIRONMENT_CONTRACT_SCHEMA_PATH = CONTRACT_DIR / "environment-contract.schema.json"
ANALYSIS_PLAN_SCHEMA_PATH = CONTRACT_DIR / "analysis-plan.schema.json"
ANALYSIS_DECISION_SCHEMA_PATH = CONTRACT_DIR / "analysis-decision.schema.json"
CONTRACT_SCHEMA_PATHS = (
    CALIBRATION_PROTOCOL_SCHEMA_PATH,
    CALIBRATION_COMPLETION_SCHEMA_PATH,
    EXPERIMENT_POLICY_SCHEMA_PATH,
    ENVIRONMENT_CONTRACT_SCHEMA_PATH,
    ANALYSIS_PLAN_SCHEMA_PATH,
    ANALYSIS_DECISION_SCHEMA_PATH,
)
SPEC_CONTRACT_DIR = ROOT / "specs/g56r-003-evaluation-runner-scoring/contracts"
G56R_003_RUNTIME_CONTRACT_NAMES = (
    "analysis-decision.schema.json",
    "analysis-plan.schema.json",
    "calibration-completion.schema.json",
    "calibration-protocol.schema.json",
    "experiment-policy.schema.json",
    "environment-contract.schema.json",
    "role-corpus.schema.json",
    "score-bundle.schema.json",
    "successor-capability-freeze.schema.json",
)
MANIFEST_PATH = ROOT / "docs/ai/research/codex-agent-route-candidate-manifest.json"
PLUGIN_ROOT = ROOT / "speckit-pro"
MATERIALIZER_MODULE_PATH = PLUGIN_ROOT / "speckit_pro_runner/agent_materialization.py"
PHASE_AGENT_SOURCE = (
    ROOT
    / "tests/speckit-pro/unit/fixtures/qualification-agent-policies/phase-executor-sol.toml"
)
PHASE_AGENT_RELATIVE_PATH = (
    "tests/speckit-pro/unit/fixtures/qualification-agent-policies/phase-executor-sol.toml"
)
DECISION_GATE_ORDER = [
    "bindings",
    "partition",
    "treatment",
    "deterministic",
    "provenance",
    "completeness",
    "floors",
    "non_inferiority",
    "pareto",
]
PARETO_DIMENSIONS = [
    "raw_input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "duration_ms",
    "retries",
    "compactions",
    "acceptance",
    "terminal_state",
]


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


def load_scoring_test_helpers():
    module_name = f"_g56r_003_scoring_test_helpers_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, SCORING_TEST_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCORING_TEST_PATH}")
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


def schema_digest(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def schema_binding(label: str) -> dict:
    return {"id": label, "digest": schema_digest(label)}


def object_binding(object_id: str, object_digest: str) -> dict:
    return {"id": object_id, "digest": object_digest}


def partition_binding(partition_type: str = "calibration", *, eligible: bool = False) -> dict:
    return {
        "partition_id": f"{partition_type}-partition",
        "partition_type": partition_type,
        "partition_digest": schema_digest(f"{partition_type}-partition"),
        "qualification_eligible": eligible,
    }


def _schema_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _schema_type_matches(value: object, expected: str) -> bool:
    return {
        "null": value is None,
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "string": isinstance(value, str),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
    }.get(expected, False)


def _resolve_contract_ref(root: dict, reference: str) -> object:
    if not reference.startswith("#/"):
        raise AssertionError(f"contract schema must use only local refs: {reference}")
    current: object = root
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            raise AssertionError(f"contract schema contains unresolved ref: {reference}")
        current = current[token]
    return current


def _contract_schema_matches(value: object, schema: object, root: dict, path: str) -> bool:
    try:
        validate_contract_schema_instance(value, schema, root, path)
    except AssertionError:
        return False
    return True


def validate_contract_schema_instance(value: object, schema: object, root: dict, path: str = "$") -> None:
    if schema is True:
        return
    if schema is False or not isinstance(schema, dict):
        raise AssertionError(f"{path} is rejected by the contract schema")
    if "$ref" in schema:
        validate_contract_schema_instance(value, _resolve_contract_ref(root, schema["$ref"]), root, path)
    for branch in schema.get("allOf", []):
        validate_contract_schema_instance(value, branch, root, path)
    if "anyOf" in schema and not any(_contract_schema_matches(value, branch, root, path) for branch in schema["anyOf"]):
        raise AssertionError(f"{path} does not match any allowed contract shape")
    if "oneOf" in schema and sum(_contract_schema_matches(value, branch, root, path) for branch in schema["oneOf"]) != 1:
        raise AssertionError(f"{path} does not match exactly one contract shape")
    if "not" in schema and _contract_schema_matches(value, schema["not"], root, path):
        raise AssertionError(f"{path} matches a prohibited contract shape")
    if "if" in schema:
        branch = schema.get("then") if _contract_schema_matches(value, schema["if"], root, path) else schema.get("else")
        if branch is not None:
            validate_contract_schema_instance(value, branch, root, path)
    if "const" in schema and _schema_bytes(value) != _schema_bytes(schema["const"]):
        raise AssertionError(f"{path} does not match its contract constant")
    if "enum" in schema and not any(_schema_bytes(value) == _schema_bytes(item) for item in schema["enum"]):
        raise AssertionError(f"{path} is outside its contract enum")
    if "type" in schema:
        expected = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_schema_type_matches(value, item) for item in expected):
            raise AssertionError(f"{path} has the wrong contract type")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise AssertionError(f"{path} is shorter than allowed")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise AssertionError(f"{path} does not match its contract pattern")
        if schema.get("format") == "date-time" and re.fullmatch(
            r"[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
            r"[Tt](?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
            r"(?:\.[0-9]+)?(?:[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])",
            value,
        ) is None:
            raise AssertionError(f"{path} must be an RFC3339 timestamp")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise AssertionError(f"{path} is below its minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise AssertionError(f"{path} is above its maximum")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            raise AssertionError(f"{path} is not above its exclusive minimum")
        if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
            raise AssertionError(f"{path} is not below its exclusive maximum")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise AssertionError(f"{path} has too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise AssertionError(f"{path} has too many items")
        if schema.get("uniqueItems") and len({_schema_bytes(item) for item in value}) != len(value):
            raise AssertionError(f"{path} must contain unique items")
        prefix_items = schema.get("prefixItems", [])
        if prefix_items:
            for index, item_schema in enumerate(prefix_items[:len(value)]):
                validate_contract_schema_instance(value[index], item_schema, root, f"{path}[{index}]")
            if schema.get("items") is False and len(value) > len(prefix_items):
                raise AssertionError(f"{path} has unexpected trailing items")
            if isinstance(schema.get("items"), dict):
                for index, item in enumerate(value[len(prefix_items):], start=len(prefix_items)):
                    validate_contract_schema_instance(item, schema["items"], root, f"{path}[{index}]")
        elif isinstance(schema.get("items"), dict):
            for index, item in enumerate(value):
                validate_contract_schema_instance(item, schema["items"], root, f"{path}[{index}]")
    if isinstance(value, dict):
        if len(value) < schema.get("minProperties", 0):
            raise AssertionError(f"{path} has too few properties")
        if "maxProperties" in schema and len(value) > schema["maxProperties"]:
            raise AssertionError(f"{path} has too many properties")
        missing = set(schema.get("required", [])) - set(value)
        if missing:
            raise AssertionError(f"{path} is missing required contract fields: {sorted(missing)}")
        properties = schema.get("properties", {})
        for index, (key, item) in enumerate(value.items()):
            if key in properties:
                validate_contract_schema_instance(item, properties[key], root, f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                raise AssertionError(f"{path} contains an undeclared contract field: {key}")
            elif isinstance(schema.get("additionalProperties"), dict):
                validate_contract_schema_instance(item, schema["additionalProperties"], root, f"{path}.<field:{index}>")


def walk_schema_nodes(value: object):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk_schema_nodes(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_schema_nodes(item)


def iter_schema_refs(value: object):
    if isinstance(value, dict):
        if "$ref" in value:
            yield value["$ref"]
        for item in value.values():
            yield from iter_schema_refs(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_schema_refs(item)


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


def bind_qualification_to_successor(wrapper: dict) -> tuple[dict, dict]:
    successor_freeze = build_successor_freeze_from_sanitized_catalog()
    candidate_route_id = wrapper["treatment_bundle"]["treatment_traces"][0][
        "objective_binding"
    ]["candidate_route_id"]
    wrapper["successor_freeze_binding"] = successor_freeze_binding(
        successor_freeze,
        candidate_route_id,
    )
    return set_assignment_ids(wrapper), successor_freeze


def qualification_bundle(
    treatment_bundle: dict,
    *,
    score_eligible: bool | None = None,
    delivery_status: str = "delivered",
) -> dict:
    source = rebound(copy.deepcopy(treatment_bundle))
    trace = source["treatment_traces"][0]
    proof = trace["configured_route_proof"]
    if score_eligible is None:
        score_eligible = (
            delivery_status == "delivered"
            and trace["treatment_disposition"] == "proven"
            and trace["disposition_reasons"]
            == ["configured_route_proof_and_complete_reroute_monitoring"]
        )
    if score_eligible:
        score_ineligibility_reasons = []
    elif delivery_status != "delivered":
        score_ineligibility_reasons = [f"delivery_{delivery_status}"]
    elif trace["treatment_disposition"] == "hard_fail":
        score_ineligibility_reasons = ["treatment_hard_fail"]
    elif trace["treatment_disposition"] != "proven":
        score_ineligibility_reasons = ["treatment_unknown"]
    else:
        score_ineligibility_reasons = ["treatment_profile_only"]
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
        "score_ineligibility_reasons": score_ineligibility_reasons,
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


def route_assignment(label: str) -> dict:
    assignment = {
        "assignment_id": schema_digest(f"{label}-assignment"),
        "route_binding": schema_binding(f"{label}-route"),
        "agent_contract_binding": schema_binding(f"{label}-agent-contract"),
        "materialization_binding": schema_binding(f"{label}-materialization"),
        "route_resolution_binding": schema_binding(f"{label}-route-resolution"),
    }
    assignment["assignment_id"] = content_id(assignment, "assignment_id")
    return assignment


def refresh_comparison_pair_digests(
    policy: dict,
    *,
    refresh_policy_binding: bool = True,
) -> dict:
    if refresh_policy_binding:
        policy["policy_digest"] = treatment.digest({
            key: value
            for key, value in policy.items()
            if key not in {
                "experiment_policy_id",
                "policy_digest",
                "comparison_sets",
            }
        })
        policy["experiment_policy_id"] = treatment.digest({
            "schema_version": policy["schema_version"],
            "experiment_policy_version": policy["experiment_policy_version"],
            "policy_digest": policy["policy_digest"],
        })
        policy_binding = experiment_policy_binding(policy)
    for comparison_set in policy["comparison_sets"]:
        for pair in comparison_set["assignment_pairs"]:
            if refresh_policy_binding:
                pair["experiment_policy_binding"] = copy.deepcopy(policy_binding)
            pair["candidate_assignment"]["assignment_id"] = content_id(
                pair["candidate_assignment"], "assignment_id",
            )
            pair["comparator_assignment"]["assignment_id"] = content_id(
                pair["comparator_assignment"], "assignment_id",
            )
            pair["assignment_pair_digest"] = content_id(pair, "assignment_pair_digest")
        comparison_set["comparison_set_digest"] = content_id(comparison_set, "comparison_set_digest")
    return policy


def experiment_policy_binding(policy: dict) -> dict:
    return object_binding(policy["experiment_policy_id"], policy["policy_digest"])


def calibration_protocol_binding(protocol: dict) -> dict:
    return object_binding(
        protocol["calibration_protocol_id"],
        protocol["calibration_protocol_digest"],
    )


def full_budget() -> dict:
    return {
        "max_attempts": 24,
        "max_wall_clock_seconds": 3600,
        "max_raw_input_tokens": 200000,
        "max_cached_input_tokens": 50000,
        "max_output_tokens": 60000,
        "max_candidates": 4,
        "max_confirmation_entries": 0,
    }


def calibration_candidate_freeze_fixture() -> dict:
    return {
        "schema_version": "successor-capability-freeze.v1",
        "candidate_freeze_id": "candidate-freeze",
        "freeze_digest": schema_digest("candidate-freeze"),
        "pinned_client_binding": schema_binding("codex-0.145.0"),
        "runtime_snapshot_binding": schema_binding("runtime-snapshot"),
    }


def calibration_corpus_fixture() -> dict:
    return {
        "schema_version": "role-corpus.v1",
        "corpus_id": "corpus",
        "corpus_digest": schema_digest("corpus"),
    }


def seal_calibration_protocol(protocol: dict) -> dict:
    sealed = copy.deepcopy(protocol)
    sealed["calibration_protocol_digest"] = treatment.digest({
        key: value
        for key, value in sealed.items()
        if key not in {
            "calibration_protocol_id",
            "calibration_protocol_digest",
        }
    })
    sealed["calibration_protocol_id"] = content_id(
        sealed,
        "calibration_protocol_id",
    )
    return sealed


def calibration_protocol_fixture() -> dict:
    return seal_calibration_protocol({
        "schema_version": "calibration-protocol.v1",
        "calibration_protocol_id": schema_digest("calibration-protocol"),
        "calibration_protocol_version": "2026-07-24.calibration",
        "calibration_protocol_digest": schema_digest("calibration-protocol-digest"),
        "status": "frozen_before_calibration",
        "partition_binding": partition_binding(),
        "candidate_freeze_binding": schema_binding("candidate-freeze"),
        "runtime_snapshot_binding": schema_binding("runtime-snapshot"),
        "pinned_client_binding": schema_binding("codex-0.145.0"),
        "corpus_binding": schema_binding("corpus"),
        "workload_manifest_binding": schema_binding("workload-manifest"),
        "scorer_bindings": [
            schema_binding("opaque-scorer-a"),
            schema_binding("opaque-scorer-b"),
        ],
        "rubric_binding": schema_binding("g56r-003-semantic-rubric"),
        "adjudicator_binding": schema_binding("opaque-adjudicator-c"),
        "cache_policy_binding": {
            "id": "cache-isolation-v1",
            "digest": schema_digest("cache-policy"),
        },
        "frozen_at": "2026-07-24T11:00:00Z",
        "independent_review_binding": schema_binding("calibration-protocol-review"),
    })


def specification_calibration_protocol_fixture() -> dict:
    return {
        "schema_version": "1.0.0",
        "calibration_protocol_id": "calibration-protocol",
        "calibration_protocol_version": "2026-07-24.calibration",
        "calibration_protocol_digest": schema_digest("calibration-protocol"),
        "status": "frozen_before_calibration",
        "partition": {
            "partition_id": "calibration-partition",
            "partition_type": "calibration",
            "qualification_eligible": False,
        },
        "candidate_freeze_binding": schema_binding("candidate-freeze"),
        "runtime_snapshot_binding": schema_binding("runtime-snapshot"),
        "pinned_client_binding": schema_binding("codex-0.145.0"),
        "corpus_binding": schema_binding("corpus"),
        "workload_manifest_binding": schema_binding("workload-manifest"),
        "scorer_bindings": [
            schema_binding("opaque-scorer-a"),
            schema_binding("opaque-scorer-b"),
        ],
        "rubric_binding": schema_binding("g56r-003-semantic-rubric"),
        "adjudicator_binding": schema_binding("opaque-adjudicator-c"),
        "cache_policy_binding": {
            "id": "cache-isolation-v1",
            "digest": schema_digest("cache-policy"),
        },
        "frozen_at": "2026-07-24T11:00:00Z",
        "independent_review_binding": schema_binding("calibration-protocol-review"),
    }


def seal_calibration_completion(completion: dict) -> dict:
    sealed = copy.deepcopy(completion)
    sealed["calibration_completion_digest"] = treatment.digest({
        key: value
        for key, value in sealed.items()
        if key not in {
            "calibration_completion_id",
            "calibration_completion_digest",
        }
    })
    sealed["calibration_completion_id"] = content_id(
        sealed,
        "calibration_completion_id",
    )
    return sealed


def calibration_completion_fixture() -> dict:
    return seal_calibration_completion({
        "schema_version": "calibration-completion.v1",
        "calibration_completion_id": schema_digest("calibration-completion"),
        "calibration_completion_version": "2026-07-24.calibration",
        "calibration_completion_digest": schema_digest(
            "calibration-completion-digest"
        ),
        "status": "complete",
        "calibration_protocol_binding": calibration_protocol_binding(
            calibration_protocol_fixture()
        ),
        "calibration_partition_binding": partition_binding(),
        "comparison_set_bindings": [schema_binding("comparison-set")],
        "assignment_bindings": [
            schema_binding("candidate-assignment"),
            schema_binding("comparator-assignment"),
        ],
        "score_bundle_bindings": [
            schema_binding("candidate-score"),
            schema_binding("comparator-score"),
        ],
        "calibration_evidence_bindings": [
            schema_binding("calibration-evidence")
        ],
        "completion_provenance": {
            "completed_at": "2026-07-24T15:00:00Z",
            "calibration_execution_complete": True,
            "analysis_plan_observed": False,
            "cohort_outcome_observed": False,
            "independent_review_binding": schema_binding("analysis-review"),
        },
    })


def calibration_completion_binding(completion: dict) -> dict:
    return object_binding(
        completion["calibration_completion_id"],
        completion["calibration_completion_digest"],
    )


def specification_calibration_completion_fixture() -> dict:
    return {
        "schema_version": "1.0.0",
        "calibration_completion_id": "calibration-completion",
        "calibration_completion_version": "2026-07-24.calibration",
        "calibration_completion_digest": schema_digest(
            "calibration-completion"
        ),
        "status": "complete",
        "calibration_protocol_binding": schema_binding(
            "calibration-protocol"
        ),
        "partition": {
            "partition_id": "calibration-partition",
            "partition_type": "calibration",
            "qualification_eligible": False,
        },
        "comparison_set_bindings": [schema_binding("comparison-set")],
        "assignment_bindings": [
            schema_binding("candidate-assignment"),
            schema_binding("comparator-assignment"),
        ],
        "score_bundle_bindings": [
            schema_binding("candidate-score"),
            schema_binding("comparator-score"),
        ],
        "calibration_evidence_bindings": [
            schema_binding("calibration-evidence")
        ],
        "completion_provenance": {
            "completed_at": "2026-07-24T15:00:00Z",
            "calibration_execution_complete": True,
            "analysis_plan_observed": False,
            "cohort_outcome_observed": False,
            "independent_review_binding": schema_binding("analysis-review"),
        },
    }


def specification_experiment_policy_fixture(*, eligible: bool) -> dict:
    policy = {
        "schema_version": "1.0.0",
        "experiment_policy_id": "experiment-policy",
        "policy_digest": schema_digest("experiment-policy"),
        "partition": {
            "partition_id": "selection-partition" if eligible else "calibration-partition",
            "partition_type": "selection" if eligible else "calibration",
            "qualification_eligible": eligible,
        },
        "candidate_freeze_binding": schema_binding("candidate-freeze"),
        "corpus_binding": schema_binding("corpus"),
        "environment_contract_binding": schema_binding(
            "environment-contract"
        ),
        "assignment_policy": {
            "pair_before_execution": True,
            "order_rule": "seeded_random",
        },
        "terminal_policy": {
            "candidate_failures_remain_in_estimand": True,
            "candidate_failure_acceptance": 0,
        },
        "rerun_policy": {
            "eligible_failure": "independently_preclassified_transient_harness_failure",
            "scope": "complete_pair",
            "cap": 1,
        },
        "budget": {
            "max_attempts": 24,
            "max_duration_seconds": 3600,
            "max_input_tokens": 200000,
            "max_cached_input_tokens": 50000,
            "max_output_tokens": 60000,
            "max_candidates": 4,
            "max_confirmation_entries": 0,
        },
        "execution_mode": "deterministic_replay",
    }
    required_binding = (
        "analysis_plan_binding"
        if eligible
        else "calibration_protocol_binding"
    )
    policy[required_binding] = schema_binding(required_binding)
    return policy


def calibration_cli_policy_fixture(
    protocol: dict | None = None,
) -> dict:
    policy = experiment_policy_fixture()
    protocol = copy.deepcopy(protocol or calibration_protocol_fixture())
    policy["candidate_freeze_binding"] = copy.deepcopy(
        protocol["candidate_freeze_binding"]
    )
    policy["corpus_binding"] = copy.deepcopy(protocol["corpus_binding"])
    policy["workload_manifest_binding"] = copy.deepcopy(
        protocol["workload_manifest_binding"]
    )
    policy["calibration_protocol_binding"] = calibration_protocol_binding(protocol)
    for comparison_set in policy["comparison_sets"]:
        for pair in comparison_set["assignment_pairs"]:
            pair["capability_binding"] = {
                "runtime_snapshot_binding": copy.deepcopy(
                    protocol["runtime_snapshot_binding"]
                ),
                "candidate_freeze_binding": copy.deepcopy(
                    protocol["candidate_freeze_binding"]
                ),
            }
            pair["calibration_protocol_binding"] = calibration_protocol_binding(
                protocol
            )
    policy["budget"] = full_budget()
    return refresh_comparison_pair_digests(policy)


def experiment_policy_fixture() -> dict:
    partition = partition_binding()
    protocol = calibration_protocol_fixture()
    policy = {
        "schema_version": "experiment-policy.v1",
        "experiment_policy_id": schema_digest("experiment-policy"),
        "experiment_policy_version": "2026-07-24.calibration",
        "policy_digest": schema_digest("experiment-policy-digest"),
        "partition_binding": partition,
        "candidate_freeze_binding": schema_binding("candidate-freeze"),
        "corpus_binding": schema_binding("corpus"),
        "calibration_protocol_binding": calibration_protocol_binding(protocol),
        "workload_manifest_binding": schema_binding("workload-manifest"),
        "environment_contract_binding": schema_binding(
            "environment-contract"
        ),
        "comparison_policy": {
            "pair_before_execution": True,
            "comparison_set_generation": "paired_by_role_fixture_task",
            "order_rule": "seeded_balanced",
            "randomization_seed_digest": schema_digest("experiment-seed"),
            "rebinding_policy": "additive_invalidation_only",
        },
        "comparison_sets": [{
            "comparison_set_id": schema_digest("comparison-set"),
            "comparison_set_digest": schema_digest("comparison-set-digest"),
            "partition_binding": partition,
            "assignment_pairs": [{
                "assignment_pair_id": schema_digest("assignment-pair"),
                "assignment_pair_digest": schema_digest("assignment-pair-digest"),
                "binding_state": "pre_execution_frozen",
                "pre_execution_frozen_at": "2026-07-24T12:00:00Z",
                "role_binding": schema_binding("phase-executor-role"),
                "fixture_binding": schema_binding("phase-executor-fixture"),
                "objective_binding": schema_binding("calibration-objective"),
                "task_binding": schema_binding("calibration-task"),
                "candidate_assignment": route_assignment("candidate"),
                "comparator_assignment": route_assignment("comparator"),
                "instruction_binding": {
                    "candidate_instruction_digest": schema_digest("candidate-instructions"),
                    "comparator_instruction_digest": schema_digest("comparator-instructions"),
                    "candidate_configuration_digest": schema_digest("candidate-config"),
                    "comparator_configuration_digest": schema_digest("comparator-config"),
                },
                "capability_binding": {
                    "runtime_snapshot_binding": schema_binding("runtime-snapshot"),
                    "candidate_freeze_binding": schema_binding("candidate-freeze"),
                },
                "experiment_policy_binding": object_binding(
                    schema_digest("experiment-policy"),
                    schema_digest("experiment-policy-digest"),
                ),
                "calibration_protocol_binding": calibration_protocol_binding(protocol),
                "environment_contract_binding": schema_binding(
                    "environment-contract"
                ),
                "workload_stratum_assignment": {
                    "workload_stratum_binding": schema_binding(
                        "implementation-small"
                    ),
                    "membership_basis": [
                        "role_id",
                        "objective",
                        "permitted_tools",
                        "mutation_contract",
                        "expected_artifacts",
                        "acceptance_oracle",
                    ],
                    "derived_from_realized_outcomes": False,
                },
                "assigned_order": ["candidate", "comparator"],
                "invalidation_policy": "additive_only",
            }],
        }],
        "terminal_policy": {
            "candidate_failures_remain_in_estimand": True,
            "candidate_failure_acceptance": 0,
            "unknown_attrition_result": "evidence_boundary_failure",
        },
        "rerun_policy": {
            "eligible_failure": "independently_preclassified_transient_harness_failure",
            "scope": "complete_pair",
            "cap": 1,
            "one_arm_rerun_prohibited": True,
            "complete_case_filtering": False,
        },
        "budget": full_budget(),
        "execution_mode": {
            "default_ci": "deterministic_replay",
            "live_mode": "explicit_local_live",
            "local_only": True,
            "pinned_client_required": True,
        },
    }
    return refresh_comparison_pair_digests(policy)


def analysis_plan_fixture() -> dict:
    return {
        "schema_version": "analysis-plan.v1",
        "analysis_plan_id": schema_digest("analysis-plan"),
        "analysis_plan_version": "2026-07-24.calibration",
        "analysis_plan_digest": schema_digest("analysis-plan-digest"),
        "status": "frozen",
        "calibration_protocol_binding": calibration_protocol_binding(
            calibration_protocol_fixture()
        ),
        "calibration_completion_binding": calibration_completion_binding(
            calibration_completion_fixture()
        ),
        "calibration_partition_binding": partition_binding(),
        "calibration_evidence_bindings": [schema_binding("calibration-evidence")],
        "freeze_provenance": {
            "frozen_at": "2026-07-24T13:00:00Z",
            "frozen_after_calibration": True,
            "cohort_outcome_observed": False,
            "pre_cohort_outcome_absence_digest": schema_digest("pre-cohort-absence"),
            "independent_review_binding": schema_binding("analysis-review"),
        },
        "workload_manifest": {
            "manifest_id": "workload-manifest-v1",
            "manifest_digest": schema_digest("workload-manifest"),
            "minimum_unique_tasks": 12,
            "unknown_stratum_policy": "inconclusive",
            "guardrail_method": {
                "units": {
                    "raw_input_tokens": "tokens_per_attempt",
                    "cached_input_tokens": "tokens_per_attempt",
                    "output_tokens": "tokens_per_attempt",
                    "duration_ms": "milliseconds_per_attempt",
                },
                "denominator": "per_attempt_within_stratum_arm",
                "comparator": "absolute_ceiling",
                "margin": 0,
                "confidence_method": {
                    "method": "empirical_order_statistic",
                    "confidence_level": 0.95,
                },
                "missing_data_rule": "report_jointly_with_attrition",
                "direction": "higher_is_worse",
                "multiplicity_position": {
                    "family": "guardrail",
                    "adjustment": "holm_within_guardrail_family",
                    "rationale": "Controls the four prespecified upper-tail guardrails.",
                },
                "breach_result": "no_qualification",
                "decision_bearing": False,
            },
            "strata": [{
                "stratum_id": "implementation-small",
                "target_weight": 1.0,
                "long_horizon": False,
                "sample_size": 24,
                "minimum_unique_tasks": 12,
                "p95_guardrails": {
                    "raw_input_tokens_max": 8000,
                    "cached_input_tokens_max": 2000,
                    "output_tokens_max": 4000,
                    "duration_ms_max": 600000,
                },
            }],
        },
        "cache_policy": {
            "policy_id": "cache-isolation-v1",
            "policy_digest": schema_digest("cache-policy"),
            "pair_isolation": True,
            "order_leakage_prohibited": True,
            "cache_state": "isolated_by_pair",
        },
        "quality_floors": {
            "evaluation_order": 1,
            "semantic": {"metric": "semantic_acceptance_rate", "minimum": 0.85},
            "reliability": {"metric": "non_candidate_failure_free_rate", "minimum": 0.95},
        },
        "non_inferiority": {
            "evaluation_order": 2,
            "endpoints": ["semantic_score", "reliability_score"],
            "margins": {"semantic_score": -0.02, "reliability_score": -0.01},
            "confidence_level": 0.95,
            "alpha": 0.05,
            "power": 0.8,
            "sample_sizes": {"per_role_minimum": 12},
            "sample_size_assumptions": {
                "variance_source_binding": schema_binding("calibration-variance"),
                "expected_missingness_rate": 0.05,
            },
            "cluster_unit": "role",
            "cluster_adjustment": "cluster_robust",
            "multiplicity_adjustment": "holm",
            "multiplicity_declaration": {
                "conjunctive_family": {
                    "adjustment": "none_required",
                    "rationale": "Every ordered floor and non-inferiority gate must pass.",
                },
                "pareto_disjunctive_family": {
                    "adjustment": "holm",
                    "rationale": "Controls the better-on-at-least-one-dimension claim.",
                },
                "across_ladder_family": {
                    "adjustment": "holm",
                    "rationale": "Controls comparisons across candidates, roles, and strata.",
                },
                "cluster_adjustment_is_precondition": True,
            },
        },
        "pareto_policy": {
            "evaluation_order": 3,
            "dimensions": PARETO_DIMENSIONS,
            "directions": {
                "raw_input_tokens": "lower",
                "cached_input_tokens": "lower",
                "output_tokens": "lower",
                "duration_ms": "lower",
                "retries": "lower",
                "compactions": "lower",
                "acceptance": "higher",
                "terminal_state": "not_worse",
            },
            "weights_prohibited": True,
            "mixed_or_tied_result": "inconclusive",
        },
        "estimand_policy": {
            "assigned_attempt": True,
            "candidate_terminal_acceptance_zero": True,
            "candidate_terminal_states": [
                "failed",
                "timed_out",
                "cancelled",
                "budget_exhausted",
                "abandoned",
            ],
            "complete_case_filtering": False,
        },
        "attrition_policy": {
            "cap": 0.1,
            "unclassifiable_attrition": "evidence_boundary_failure",
            "unclassifiable_result": "inconclusive",
            "complete_case_filtering": False,
        },
        "rerun_policy": {
            "eligible_failure": "independently_preclassified_transient_harness_failure",
            "scope": "complete_pair",
            "cap": 1,
            "one_arm_rerun_prohibited": True,
        },
        "campaign_budget": full_budget(),
        "racing_policy": {
            "enabled": False,
            "terminal_rule": "disabled",
            "interim_looks": {"count": 0, "information_fractions": []},
            "boundary": {
                "type": "disabled",
                "rationale": "Calibration replay has no interim racing looks.",
            },
            "error_control": {
                "method": "none_no_interim_looks",
                "rationale": "Zero looks create no repeated-testing error.",
            },
            "look_schedule_frozen": True,
            "early_stop_biases_estimate": True,
            "stop_scope": "complete_pair",
        },
        "futility_policy": {
            "enabled": False,
            "terminal_rule": "disabled",
            "interim_looks": {"count": 0, "information_fractions": []},
            "boundary": {
                "type": "disabled",
                "rationale": "Calibration replay has no interim futility looks.",
            },
            "error_control": {
                "method": "none_no_interim_looks",
                "rationale": "Zero looks create no repeated-testing error.",
            },
            "look_schedule_frozen": True,
            "early_stop_biases_estimate": True,
            "stop_scope": "complete_pair",
            "boundary_binding": "non_binding",
        },
        "terminal_policy": {
            "incomplete_result": "inconclusive",
            "uncertain_result": "inconclusive",
            "no_forced_ranking": True,
        },
    }


def comparison_assignment_authorities(policy: dict, protocol: dict) -> dict:
    pair = policy["comparison_sets"][0]["assignment_pairs"][0]
    return {
        "partition_binding": copy.deepcopy(policy["partition_binding"]),
        "candidate_freeze_binding": copy.deepcopy(policy["candidate_freeze_binding"]),
        "runtime_snapshot_binding": copy.deepcopy(pair["capability_binding"]["runtime_snapshot_binding"]),
        "corpus_binding": copy.deepcopy(policy["corpus_binding"]),
        "workload_manifest_binding": copy.deepcopy(policy["workload_manifest_binding"]),
        "environment_contract_binding": copy.deepcopy(
            policy["environment_contract_binding"]
        ),
        "experiment_policy_binding": experiment_policy_binding(policy),
        "calibration_protocol_binding": calibration_protocol_binding(protocol),
        "role_binding": copy.deepcopy(pair["role_binding"]),
        "fixture_binding": copy.deepcopy(pair["fixture_binding"]),
        "objective_binding": copy.deepcopy(pair["objective_binding"]),
        "task_binding": copy.deepcopy(pair["task_binding"]),
        "fixture_partition_binding": copy.deepcopy(policy["partition_binding"]),
        "candidate_route_binding": copy.deepcopy(pair["candidate_assignment"]["route_binding"]),
        "candidate_agent_contract_binding": copy.deepcopy(pair["candidate_assignment"]["agent_contract_binding"]),
        "candidate_materialization_binding": copy.deepcopy(pair["candidate_assignment"]["materialization_binding"]),
        "candidate_route_resolution_binding": copy.deepcopy(pair["candidate_assignment"]["route_resolution_binding"]),
        "candidate_instruction_digest": pair["instruction_binding"]["candidate_instruction_digest"],
        "candidate_configuration_digest": pair["instruction_binding"]["candidate_configuration_digest"],
        "comparator_route_binding": copy.deepcopy(pair["comparator_assignment"]["route_binding"]),
        "comparator_agent_contract_binding": copy.deepcopy(pair["comparator_assignment"]["agent_contract_binding"]),
        "comparator_materialization_binding": copy.deepcopy(pair["comparator_assignment"]["materialization_binding"]),
        "comparator_route_resolution_binding": copy.deepcopy(pair["comparator_assignment"]["route_resolution_binding"]),
        "comparator_instruction_digest": pair["instruction_binding"]["comparator_instruction_digest"],
        "comparator_configuration_digest": pair["instruction_binding"]["comparator_configuration_digest"],
    }


def executed_pair_snapshot(policy: dict) -> dict:
    pair = policy["comparison_sets"][0]["assignment_pairs"][0]
    return {
        "assignment_pair_id": pair["assignment_pair_id"],
        "assignment_pair_digest": pair["assignment_pair_digest"],
        "candidate_assignment_id": pair["candidate_assignment"]["assignment_id"],
        "comparator_assignment_id": pair["comparator_assignment"]["assignment_id"],
        "executed_at": "2026-07-24T14:00:00Z",
    }


def comparison_assignment_bundle_fixture() -> dict:
    policy = experiment_policy_fixture()
    protocol = calibration_protocol_fixture()
    return {
        "schema_version": "comparison-assignment.v1",
        "owner_spec_id": "G56R-003",
        "partition_registry": [copy.deepcopy(policy["partition_binding"])],
        "binding_authorities": comparison_assignment_authorities(policy, protocol),
        "experiment_policy": policy,
        "calibration_protocol": protocol,
        "executed_pair_snapshots": [executed_pair_snapshot(policy)],
        "refresh_invalidations": [],
    }


def comparison_refresh_invalidation(old_binding: dict, new_binding: dict) -> dict:
    row = {
        "invalidation_id": "sha256:" + "0" * 64,
        "target_binding": copy.deepcopy(old_binding),
        "replacement_binding": copy.deepcopy(new_binding),
        "reason": "capability_refresh",
        "detected_at": "2026-07-24T15:00:00Z",
    }
    row["invalidation_id"] = content_id(row, "invalidation_id")
    return row


def ordered_gate_results(failed_gate: str | None = None) -> list[dict]:
    rows: list[dict] = []
    failed = False
    for index, gate in enumerate(DECISION_GATE_ORDER, start=1):
        if failed:
            result = "not_evaluated"
        elif gate == failed_gate:
            result = "fail"
            failed = True
        else:
            result = "pass"
        rows.append({"sequence": index, "gate": gate, "result": result})
    return rows


def decision_bundle_fixture(
    *,
    decision: str = "calibration_complete",
    complete: bool = True,
    floor_result: str = "pass",
    non_inferiority_result: str = "pass",
    pareto_result: str = "candidate_dominates",
    failed_gate: str | None = None,
) -> dict:
    return {
        "schema_version": "analysis-decision.v1",
        "decision_bundle_id": schema_digest(f"decision-{decision}"),
        "decision_bundle_version": "2026-07-24.calibration",
        "decision_bundle_digest": schema_digest(f"decision-{decision}-digest"),
        "partition_binding": partition_binding(),
        "comparison_set_binding": schema_binding("comparison-set"),
        "assignment_bindings": [schema_binding("candidate-assignment"), schema_binding("comparator-assignment")],
        "score_bundle_bindings": [schema_binding("candidate-score"), schema_binding("comparator-score")],
        "analysis_plan_binding": schema_binding("analysis-plan"),
        "analysis_output": {
            "analysis_output_id": schema_digest(f"analysis-output-{decision}"),
            "analysis_output_digest": schema_digest(f"analysis-output-{decision}-digest"),
            "complete": complete,
            "floor_result": floor_result,
            "non_inferiority_result": non_inferiority_result,
            "pareto_result": pareto_result,
            "terminal_analysis_disposition": decision,
        },
        "ordered_gate_results": ordered_gate_results(failed_gate),
        "decision": decision,
        "qualification_policy_output": {
            "preferred_route_policy_created": False,
            "fallback_route_policy_created": False,
            "installed_default_changed": False,
        },
        "evidence_refs": [schema_digest(f"decision-evidence-{decision}")],
    }


def seal_decision_bundle(bundle: dict) -> dict:
    sealed = copy.deepcopy(bundle)
    output = sealed["analysis_output"]
    output["details"] = {}
    output["analysis_output_digest"] = treatment.digest({
        key: value
        for key, value in output.items()
        if key not in {"analysis_output_id", "analysis_output_digest"}
    })
    output["analysis_output_id"] = content_id(output, "analysis_output_id")
    sealed["decision_bundle_digest"] = treatment.digest({
        key: value
        for key, value in sealed.items()
        if key not in {"decision_bundle_id", "decision_bundle_digest"}
    })
    sealed["decision_bundle_id"] = content_id(sealed, "decision_bundle_id")
    return sealed


def seal_calibration_report(report: dict) -> dict:
    sealed = copy.deepcopy(report)
    sealed["calibration_report_digest"] = treatment.digest({
        key: value
        for key, value in sealed.items()
        if key not in {"calibration_report_id", "calibration_report_digest"}
    })
    sealed["calibration_report_id"] = content_id(
        sealed,
        "calibration_report_id",
    )
    return sealed


class ExperimentAnalysisContractSchemaTests(unittest.TestCase):
    maxDiff = None

    def schema_for(self, path: Path) -> dict:
        self.assertTrue(path.exists(), f"{path.relative_to(ROOT)} must exist")
        schema = load_json(path)
        self.assertIsInstance(schema, dict)
        return schema

    def assert_accepts(self, schema: dict, value: dict) -> None:
        validate_contract_schema_instance(value, schema, schema)

    def assert_rejects(self, schema: dict, value: dict, message: str) -> None:
        with self.assertRaises(AssertionError, msg=message):
            validate_contract_schema_instance(value, schema, schema)

    def assert_shared_id_digest_defs(self, schema: dict) -> None:
        self.assertEqual(
            schema["$defs"]["digest"],
            {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
        )
        self.assertEqual(schema["$defs"]["binding"]["required"], ["id", "digest"])
        self.assertFalse(schema["$defs"]["binding"]["additionalProperties"])
        self.assertEqual(schema["$defs"]["binding"]["properties"]["digest"], {"$ref": "#/$defs/digest"})

    def test_contract_schemas_are_self_contained_closed_and_share_id_digest_defs(self) -> None:
        for path in CONTRACT_SCHEMA_PATHS:
            with self.subTest(schema=path.name):
                schema = self.schema_for(path)
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(schema["type"], "object")
                self.assertFalse(schema["additionalProperties"])
                self.assert_shared_id_digest_defs(schema)
                for reference in iter_schema_refs(schema):
                    self.assertTrue(reference.startswith("#/"), reference)
                for node in walk_schema_nodes(schema):
                    if node.get("type") == "object":
                        self.assertIn("additionalProperties", node)
                        self.assertFalse(node["additionalProperties"], node.get("title", node))
                    elif "properties" in node:
                        self.assertTrue(
                            set(node) <= {"properties", "required"},
                            "property-only schema nodes must remain bounded conditional predicates",
                        )

    def test_runtime_and_specification_contracts_have_distinct_schema_ids(self) -> None:
        for name in G56R_003_RUNTIME_CONTRACT_NAMES:
            with self.subTest(name=name):
                runtime_schema = self.schema_for(CONTRACT_DIR / name)
                specification_schema = self.schema_for(SPEC_CONTRACT_DIR / name)
                self.assertNotEqual(runtime_schema["$id"], specification_schema["$id"])
                self.assertIn("/runtime/", runtime_schema["$id"])

    def test_spec_experiment_policy_selects_exactly_one_pre_execution_authority(self) -> None:
        schema = self.schema_for(SPEC_CONTRACT_DIR / "experiment-policy.schema.json")
        calibration = specification_experiment_policy_fixture(eligible=False)
        eligible = specification_experiment_policy_fixture(eligible=True)

        self.assertNotIn("analysis_plan_binding", schema["required"])
        conditional = schema["allOf"][0]
        self.assertEqual(
            conditional["if"]["properties"]["partition"]["properties"][
                "qualification_eligible"
            ],
            {"const": True},
        )
        self.assertEqual(conditional["then"]["required"], ["analysis_plan_binding"])
        self.assertEqual(
            conditional["else"]["required"],
            ["calibration_protocol_binding"],
        )
        self.assert_accepts(schema, calibration)
        self.assert_accepts(schema, eligible)
        ineligible_selection = copy.deepcopy(calibration)
        ineligible_selection["partition"].update({
            "partition_id": "ineligible-selection-partition",
            "partition_type": "selection",
        })
        self.assert_accepts(
            schema,
            ineligible_selection,
        )

        both = copy.deepcopy(calibration)
        both["analysis_plan_binding"] = schema_binding("analysis-plan")
        self.assert_rejects(
            schema,
            both,
            "calibration policy cannot bind both protocol and analysis plan",
        )

        neither = copy.deepcopy(calibration)
        del neither["calibration_protocol_binding"]
        self.assert_rejects(
            schema,
            neither,
            "calibration policy must bind its protocol",
        )

        eligible_without_plan = copy.deepcopy(eligible)
        del eligible_without_plan["analysis_plan_binding"]
        self.assert_rejects(
            schema,
            eligible_without_plan,
            "qualification-eligible policy must bind the frozen analysis plan",
        )

    def test_calibration_protocol_schema_is_pre_calibration_only(self) -> None:
        runtime_schema = self.schema_for(CALIBRATION_PROTOCOL_SCHEMA_PATH)
        specification_schema = self.schema_for(
            SPEC_CONTRACT_DIR / "calibration-protocol.schema.json"
        )
        self.assert_accepts(runtime_schema, calibration_protocol_fixture())
        self.assert_accepts(
            specification_schema,
            specification_calibration_protocol_fixture(),
        )

        for prohibited in ("margins", "sample_sizes", "terminal_policy"):
            with self.subTest(prohibited=prohibited):
                invalid = calibration_protocol_fixture()
                invalid[prohibited] = {}
                self.assert_rejects(
                    runtime_schema,
                    invalid,
                    f"calibration protocol cannot freeze {prohibited}",
                )

    def test_calibration_completion_schema_proves_evidence_collection_without_a_plan(self) -> None:
        runtime_schema = self.schema_for(CALIBRATION_COMPLETION_SCHEMA_PATH)
        specification_schema = self.schema_for(
            SPEC_CONTRACT_DIR / "calibration-completion.schema.json"
        )
        runtime = calibration_completion_fixture()
        specification = specification_calibration_completion_fixture()

        self.assert_accepts(runtime_schema, runtime)
        self.assert_accepts(specification_schema, specification)
        self.assertNotIn("analysis_plan_binding", runtime_schema["properties"])
        self.assertNotIn("analysis_plan_binding", specification_schema["properties"])

        for prohibited in (
            "margins",
            "sample_sizes",
            "quality_floors",
            "terminal_thresholds",
        ):
            with self.subTest(prohibited=prohibited):
                invalid = calibration_completion_fixture()
                invalid[prohibited] = {}
                self.assert_rejects(
                    runtime_schema,
                    invalid,
                    f"calibration completion cannot freeze {prohibited}",
                )

    def test_experiment_policy_schema_closes_partition_pair_budget_and_rerun_contracts(self) -> None:
        schema = self.schema_for(EXPERIMENT_POLICY_SCHEMA_PATH)
        valid = experiment_policy_fixture()
        self.assert_accepts(schema, valid)
        self.assertIn("calibration_protocol_binding", schema["required"])
        self.assertNotIn("analysis_plan_binding", schema["required"])
        self.assertNotIn("allOf", schema)
        self.assertIn(
            "calibration_protocol_binding",
            schema["$defs"]["assignmentPair"]["required"],
        )
        self.assertNotIn(
            "analysis_plan_binding",
            schema["$defs"]["assignmentPair"]["required"],
        )
        self.assertEqual(
            schema["$defs"]["calibrationPartitionBinding"]["properties"][
                "qualification_eligible"
            ],
            {"const": False},
        )

        unknown_partition = copy.deepcopy(valid)
        unknown_partition["partition_binding"]["partition_type"] = "exploration"
        self.assert_rejects(schema, unknown_partition, "partition types must be closed")

        calibration_eligible = copy.deepcopy(valid)
        calibration_eligible["partition_binding"]["qualification_eligible"] = True
        self.assert_rejects(schema, calibration_eligible, "calibration cannot qualify")

        missing_budget = copy.deepcopy(valid)
        del missing_budget["budget"]["max_confirmation_entries"]
        self.assert_rejects(schema, missing_budget, "live policy budget must be complete")

        one_arm_rerun = copy.deepcopy(valid)
        one_arm_rerun["rerun_policy"]["scope"] = "single_arm"
        self.assert_rejects(schema, one_arm_rerun, "reruns must be complete-pair only")

        mutable_pair = copy.deepcopy(valid)
        del mutable_pair["comparison_sets"][0]["assignment_pairs"][0]["candidate_assignment"]["route_resolution_binding"]
        self.assert_rejects(schema, mutable_pair, "candidate assignment must bind route resolution before execution")

    def test_analysis_plan_schema_freezes_workload_cache_statistics_attrition_and_budget(self) -> None:
        schema = self.schema_for(ANALYSIS_PLAN_SCHEMA_PATH)
        valid = analysis_plan_fixture()
        self.assert_accepts(schema, valid)

        missing_protocol = copy.deepcopy(valid)
        del missing_protocol["calibration_protocol_binding"]
        self.assert_rejects(
            schema,
            missing_protocol,
            "frozen analysis plan must bind its calibration protocol",
        )

        missing_completion = copy.deepcopy(valid)
        del missing_completion["calibration_completion_binding"]
        self.assert_rejects(
            schema,
            missing_completion,
            "frozen analysis plan must bind calibration completion",
        )

        missing_p95_cache = copy.deepcopy(valid)
        del missing_p95_cache["workload_manifest"]["strata"][0]["p95_guardrails"]["cached_input_tokens_max"]
        self.assert_rejects(schema, missing_p95_cache, "workload strata must bind p95 cache guardrails")

        missing_guardrail_method = copy.deepcopy(valid)
        del missing_guardrail_method["workload_manifest"]["guardrail_method"]
        self.assert_rejects(
            schema,
            missing_guardrail_method,
            "p95 ceilings require their complete comparison method",
        )

        missing_stratum_floor = copy.deepcopy(valid)
        del missing_stratum_floor["workload_manifest"]["strata"][0][
            "minimum_unique_tasks"
        ]
        self.assert_rejects(
            schema,
            missing_stratum_floor,
            "each workload stratum requires its own estimability floor",
        )

        missing_multiplicity_family = copy.deepcopy(valid)
        del missing_multiplicity_family["non_inferiority"][
            "multiplicity_declaration"
        ]["across_ladder_family"]
        self.assert_rejects(
            schema,
            missing_multiplicity_family,
            "all three multiplicity families must be declared",
        )

        unstated_looks = copy.deepcopy(valid)
        del unstated_looks["racing_policy"]["interim_looks"]
        self.assert_rejects(
            schema,
            unstated_looks,
            "disabled racing still declares zero interim looks",
        )

        cache_leak = copy.deepcopy(valid)
        cache_leak["cache_policy"]["pair_isolation"] = False
        self.assert_rejects(schema, cache_leak, "cache state must be isolated by pair")

        pareto_before_non_inferiority = copy.deepcopy(valid)
        pareto_before_non_inferiority["pareto_policy"]["evaluation_order"] = 2
        self.assert_rejects(schema, pareto_before_non_inferiority, "Pareto cannot run before non-inferiority")

        complete_case = copy.deepcopy(valid)
        complete_case["attrition_policy"]["complete_case_filtering"] = True
        self.assert_rejects(schema, complete_case, "attrition cannot use complete-case filtering")

        post_cohort_freeze = copy.deepcopy(valid)
        post_cohort_freeze["freeze_provenance"]["cohort_outcome_observed"] = True
        self.assert_rejects(schema, post_cohort_freeze, "analysis plan must freeze before later cohort outcomes")

    def test_decision_schema_enforces_ordered_terminal_cases_and_no_calibration_qualification(self) -> None:
        schema = self.schema_for(ANALYSIS_DECISION_SCHEMA_PATH)
        cases = [
            decision_bundle_fixture(),
            decision_bundle_fixture(
                decision="no_qualification",
                floor_result="fail",
                non_inferiority_result="not_evaluated",
                pareto_result="not_evaluated",
                failed_gate="floors",
            ),
            decision_bundle_fixture(
                decision="no_qualification",
                non_inferiority_result="fail",
                pareto_result="not_evaluated",
                failed_gate="non_inferiority",
            ),
            decision_bundle_fixture(
                decision="inconclusive",
                pareto_result="mixed",
                failed_gate=None,
            ),
            decision_bundle_fixture(
                decision="inconclusive",
                complete=False,
                floor_result="not_evaluated",
                non_inferiority_result="not_evaluated",
                pareto_result="not_evaluated",
                failed_gate="completeness",
            ),
        ]
        for case in cases:
            with self.subTest(decision=case["decision"], output=case["analysis_output"]):
                self.assert_accepts(schema, case)

        qualified_calibration = decision_bundle_fixture(decision="qualified")
        qualified_calibration["analysis_output"]["terminal_analysis_disposition"] = "qualified"
        self.assert_rejects(schema, qualified_calibration, "calibration partition cannot emit qualified")

        wrong_order = decision_bundle_fixture()
        wrong_order["ordered_gate_results"][6]["gate"] = "pareto"
        self.assert_rejects(schema, wrong_order, "decision gates must be in frozen order")

        pareto_without_ni = decision_bundle_fixture(
            non_inferiority_result="not_evaluated",
            pareto_result="candidate_dominates",
        )
        self.assert_rejects(schema, pareto_without_ni, "Pareto cannot be evaluated before NI passes")

    def test_decision_v1_1_selects_authority_from_partition_eligibility(self) -> None:
        schema = self.schema_for(ANALYSIS_DECISION_SCHEMA_PATH)
        calibration = decision_bundle_fixture()
        calibration["schema_version"] = "analysis-decision.v1.1"
        del calibration["analysis_plan_binding"]
        calibration["calibration_protocol_binding"] = schema_binding(
            "calibration-protocol"
        )
        self.assert_accepts(schema, calibration)

        eligible = decision_bundle_fixture(
            decision="no_qualification",
            floor_result="fail",
            non_inferiority_result="not_evaluated",
            pareto_result="not_evaluated",
            failed_gate="floors",
        )
        eligible["schema_version"] = "analysis-decision.v1.1"
        eligible["partition_binding"].update({
            "partition_id": "selection-partition",
            "partition_type": "selection",
            "qualification_eligible": True,
        })
        self.assert_accepts(schema, eligible)

        both = copy.deepcopy(calibration)
        both["analysis_plan_binding"] = schema_binding("analysis-plan")
        self.assert_rejects(
            schema,
            both,
            "version 1.1 decision must not bind both protocol and plan",
        )

        eligible_without_plan = copy.deepcopy(eligible)
        del eligible_without_plan["analysis_plan_binding"]
        self.assert_rejects(
            schema,
            eligible_without_plan,
            "qualification-eligible decision must bind the frozen plan",
        )


class ComparisonAssignmentValidatorTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.qualification = load_qualification_module()

    def validate_assignment_bundle(self, bundle: dict) -> dict:
        return self.qualification.validate_comparison_assignment_bundle(bundle)

    def assert_invalid_assignment(self, bundle: dict, message: str = "") -> None:
        with self.assertRaises(ValueError, msg=message):
            self.validate_assignment_bundle(bundle)

    def recompute_policy_digests(
        self,
        bundle: dict,
        *,
        refresh_policy_binding: bool = True,
    ) -> dict:
        bundle["experiment_policy"] = refresh_comparison_pair_digests(
            bundle["experiment_policy"],
            refresh_policy_binding=refresh_policy_binding,
        )
        return bundle

    def test_comparison_assignment_validator_accepts_complete_pre_execution_join_graph(self) -> None:
        bundle = comparison_assignment_bundle_fixture()

        first = self.validate_assignment_bundle(copy.deepcopy(bundle))
        second = self.validate_assignment_bundle(copy.deepcopy(first))

        self.assertEqual(treatment.canonical_bytes(first), treatment.canonical_bytes(second))
        pair = first["experiment_policy"]["comparison_sets"][0]["assignment_pairs"][0]
        self.assertEqual(pair["binding_state"], "pre_execution_frozen")
        self.assertEqual(pair["capability_binding"]["candidate_freeze_binding"], first["binding_authorities"]["candidate_freeze_binding"])
        self.assertEqual(pair["capability_binding"]["runtime_snapshot_binding"], first["binding_authorities"]["runtime_snapshot_binding"])
        self.assertEqual(pair["experiment_policy_binding"], experiment_policy_binding(first["experiment_policy"]))
        self.assertEqual(
            pair["calibration_protocol_binding"],
            calibration_protocol_binding(first["calibration_protocol"]),
        )
        self.assertEqual(first["executed_pair_snapshots"][0]["assignment_pair_digest"], pair["assignment_pair_digest"])

    def test_calibration_policy_validator_enforces_closed_schema_identity_and_protocol_joins(self) -> None:
        policy = experiment_policy_fixture()
        protocol = calibration_protocol_fixture()

        validated_protocol = self.qualification.validate_calibration_protocol(
            copy.deepcopy(protocol)
        )
        validated_policy = self.qualification.validate_calibration_experiment_policy(
            copy.deepcopy(policy),
            copy.deepcopy(validated_protocol),
        )

        self.assertEqual(validated_protocol, protocol)
        self.assertEqual(validated_policy, policy)

        offset_protocol = copy.deepcopy(protocol)
        offset_protocol["frozen_at"] = "2026-07-24T12:30:00+01:30"
        offset_protocol = seal_calibration_protocol(offset_protocol)
        self.assertEqual(
            self.qualification.validate_calibration_protocol(offset_protocol),
            offset_protocol,
        )

        cases = (
            (
                "open_shape",
                lambda value: value.__setitem__("operator_note", "untrusted"),
            ),
            (
                "policy_digest",
                lambda value: value.__setitem__(
                    "policy_digest",
                    schema_digest("wrong-policy"),
                ),
            ),
            (
                "comparison_set_digest",
                lambda value: value["comparison_sets"][0].__setitem__(
                    "comparison_set_digest",
                    schema_digest("wrong-comparison-set"),
                ),
            ),
            (
                "protocol_binding",
                lambda value: value.__setitem__(
                    "calibration_protocol_binding",
                    schema_binding("wrong-protocol"),
                ),
            ),
        )
        for label, mutate in cases:
            with self.subTest(case=label):
                invalid = copy.deepcopy(policy)
                mutate(invalid)
                with self.assertRaises(ValueError):
                    self.qualification.validate_calibration_experiment_policy(
                        invalid,
                        protocol,
                    )

    def test_comparison_assignment_validator_rejects_each_required_pre_execution_join_mismatch(self) -> None:
        cases = [
            ("route", ("candidate_assignment", "route_binding", "digest"), schema_digest("wrong-candidate-route")),
            ("agent_contract", ("candidate_assignment", "agent_contract_binding", "digest"), schema_digest("wrong-agent-contract")),
            ("materialization", ("candidate_assignment", "materialization_binding", "digest"), schema_digest("wrong-materialization")),
            ("route_resolution", ("candidate_assignment", "route_resolution_binding", "digest"), schema_digest("wrong-route-resolution")),
            ("comparator_route", ("comparator_assignment", "route_binding", "digest"), schema_digest("wrong-comparator-route")),
            ("role", ("role_binding", "digest"), schema_digest("wrong-role")),
            ("fixture", ("fixture_binding", "digest"), schema_digest("wrong-fixture")),
            ("task", ("task_binding", "digest"), schema_digest("wrong-task")),
            ("instruction_hash", ("instruction_binding", "candidate_instruction_digest"), schema_digest("wrong-instruction")),
            ("configuration_hash", ("instruction_binding", "comparator_configuration_digest"), schema_digest("wrong-configuration")),
            ("snapshot", ("capability_binding", "runtime_snapshot_binding", "digest"), schema_digest("wrong-snapshot")),
            ("freeze", ("capability_binding", "candidate_freeze_binding", "digest"), schema_digest("wrong-freeze")),
            ("policy", ("experiment_policy_binding", "digest"), schema_digest("wrong-policy")),
            (
                "protocol",
                ("calibration_protocol_binding", "digest"),
                schema_digest("wrong-protocol"),
            ),
        ]
        for label, path, value in cases:
            with self.subTest(join=label):
                bundle = comparison_assignment_bundle_fixture()
                target = bundle["experiment_policy"]["comparison_sets"][0]["assignment_pairs"][0]
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                self.recompute_policy_digests(
                    bundle,
                    refresh_policy_binding=label != "policy",
                )
                self.assert_invalid_assignment(bundle, f"{label} join must fail closed")

    def test_partition_joins_and_cross_partition_reuse_fail_closed(self) -> None:
        cases = [
            ("comparison_set_partition", ("experiment_policy", "comparison_sets", 0, "partition_binding"), partition_binding("screening", eligible=True)),
            ("policy_partition", ("experiment_policy", "partition_binding"), partition_binding("selection", eligible=True)),
            (
                "calibration_protocol_partition",
                ("calibration_protocol", "partition_binding"),
                partition_binding("cohort_lock", eligible=True),
            ),
            ("fixture_partition_reuse", ("binding_authorities", "fixture_partition_binding"), partition_binding("screening", eligible=True)),
        ]
        for label, path, value in cases:
            with self.subTest(partition=label):
                bundle = comparison_assignment_bundle_fixture()
                target = bundle
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                if path[0] == "experiment_policy":
                    self.recompute_policy_digests(bundle)
                self.assert_invalid_assignment(bundle, f"{label} must not cross partition boundaries")

    def test_refreshes_create_additive_invalidations_without_rebinding_frozen_pair(self) -> None:
        bundle = comparison_assignment_bundle_fixture()
        original_freeze = copy.deepcopy(bundle["binding_authorities"]["candidate_freeze_binding"])
        refreshed_freeze = schema_binding("candidate-freeze-refresh")

        missing_invalidation = copy.deepcopy(bundle)
        missing_invalidation["binding_authorities"]["candidate_freeze_binding"] = refreshed_freeze
        self.assert_invalid_assignment(
            missing_invalidation,
            "refreshed authority must create an additive invalidation record",
        )

        recorded = copy.deepcopy(bundle)
        recorded["binding_authorities"]["candidate_freeze_binding"] = refreshed_freeze
        recorded["refresh_invalidations"] = [
            comparison_refresh_invalidation(original_freeze, refreshed_freeze),
        ]
        validated = self.validate_assignment_bundle(recorded)
        pair = validated["experiment_policy"]["comparison_sets"][0]["assignment_pairs"][0]
        self.assertEqual(pair["capability_binding"]["candidate_freeze_binding"], original_freeze)
        self.assertEqual(validated["binding_authorities"]["candidate_freeze_binding"], refreshed_freeze)

    def test_post_execution_rebinding_is_rejected_even_when_authority_is_current(self) -> None:
        bundle = comparison_assignment_bundle_fixture()
        original_route = copy.deepcopy(bundle["binding_authorities"]["candidate_route_binding"])
        new_route = schema_binding("candidate-route-refresh")
        pair = bundle["experiment_policy"]["comparison_sets"][0]["assignment_pairs"][0]
        pair["candidate_assignment"]["route_binding"] = copy.deepcopy(new_route)
        bundle["binding_authorities"]["candidate_route_binding"] = copy.deepcopy(new_route)
        bundle["refresh_invalidations"] = [
            comparison_refresh_invalidation(original_route, new_route),
        ]
        self.recompute_policy_digests(bundle)

        self.assert_invalid_assignment(bundle, "executed assignment pairs cannot be rebound")


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
            "BINDING_AUTHORITY_FIELDS", "COMPARISON_ASSIGNMENT_SCHEMA_VERSION",
            "DELIVERY_STATUSES", "MANDATORY_OBSERVATION_FIELDS",
            "MATERIALIZATION_FIELDS", "NULL_ONLY_OBSERVATION_FIELDS",
            "PARTITION_TYPES", "QUALIFICATION_OBSERVATION_FIELDS", "QUALIFICATION_OWNER_SPEC_ID",
            "QUALIFICATION_SCHEMA_VERSION", "TREATMENT_OWNER_SPEC_ID",
            "validate_calibration_experiment_policy", "validate_calibration_protocol",
            "validate_comparison_assignment_bundle", "validate_qualification_bundle",
        }
        self.assertTrue(QUALIFICATION_MODULE_PATH.exists())
        self.assertTrue(callable(self.qualification.validate_qualification_bundle))
        self.assertEqual(set(self.qualification.__all__), expected_api)

    def test_unknown_treatment_assignment_is_non_scorable_and_idempotent(self) -> None:
        wrapper = qualification_bundle(self.base_treatment)
        first = self.validate(copy.deepcopy(wrapper))
        second = self.validate(copy.deepcopy(first))
        self.assertEqual(treatment.canonical_bytes(first), treatment.canonical_bytes(second))
        assignment = first["qualification_assignments"][0]
        self.assertFalse(assignment["score_eligible"])
        self.assertEqual(assignment["score_ineligibility_reasons"], ["treatment_unknown"])
        self.assertEqual(first["qualification_traces"][0]["owner_spec_id"], "G56R-003")
        self.assertEqual(
            first["qualification_traces"][0]["execution_trace_id"],
            first["qualification_assignments"][0]["execution_trace_id"],
        )

    def test_treatment_disposition_and_proof_authority_gate_score_eligibility(self) -> None:
        cases = (
            ("unknown", ["effective_treatment_unknown"], ["treatment_unknown"], False),
            (
                "proven",
                ["profile_supported_effective_treatment"],
                ["treatment_profile_only"],
                True,
            ),
            ("hard_fail", ["configuration_mismatch"], ["treatment_hard_fail"], True),
        )
        for disposition, disposition_reasons, expected_reasons, bypass_treatment_validation in cases:
            with self.subTest(disposition=disposition, disposition_reasons=disposition_reasons):
                treatment_bundle = copy.deepcopy(self.base_treatment)
                trace = treatment_bundle["treatment_traces"][0]
                trace["treatment_disposition"] = disposition
                trace["disposition_reasons"] = disposition_reasons
                trace["treatment_failures"] = [] if disposition == "proven" else [{
                    "failure_code": disposition_reasons[0],
                    "affected_field": "treatment.evidence",
                    "expected_evidence_ref": None,
                    "observed_evidence_ref": None,
                    "resulting_disposition": disposition,
                }]
                treatment_bundle["fixture_provenance"]["expected_dispositions"] = [{
                    "execution_trace_id": trace["objective_binding"]["execution_trace_id"],
                    "treatment_disposition": disposition,
                }]
                wrapper = qualification_bundle(
                    treatment_bundle,
                    score_eligible=False,
                    delivery_status="delivered",
                )
                assignment = wrapper["qualification_assignments"][0]
                assignment["score_ineligibility_reasons"] = expected_reasons
                wrapper = set_assignment_ids(wrapper)
                if bypass_treatment_validation:
                    self.qualification._validate_treatment_bundle = (
                        lambda value, **_kwargs: copy.deepcopy(value)
                    )

                validated = self.validate(wrapper)

                self.assertFalse(validated["qualification_assignments"][0]["score_eligible"])
                self.assertEqual(
                    validated["qualification_assignments"][0]["score_ineligibility_reasons"],
                    expected_reasons,
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
        self.assertFalse(validated_assignment["score_eligible"])
        self.assertEqual(validated_assignment["score_ineligibility_reasons"], ["treatment_unknown"])
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
            source_path.write_bytes(PHASE_AGENT_SOURCE.read_bytes())
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

    def test_cli_validate_treatment_reports_unknown_treatment_as_score_ineligible(self) -> None:
        self.assertTrue(QUALIFICATION_RUNNER_PATH.exists())

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_path = root / "phase-executor.toml"
            source_path.write_bytes(PHASE_AGENT_SOURCE.read_bytes())
            bundle_path = root / "qualification.json"
            wrapper = apply_materialized_source(qualification_bundle(self.base_treatment), source_path)
            wrapper, successor_freeze = bind_qualification_to_successor(wrapper)
            successor_path = root / "successor.json"
            write_canonical_json(bundle_path, wrapper)
            write_canonical_json(successor_path, successor_freeze)

            completed = run_qualification_cli(
                "validate-treatment",
                "--qualification-bundle", str(bundle_path),
                "--agent-policy-source", str(source_path),
                "--source-relative-path", PHASE_AGENT_RELATIVE_PATH,
                "--successor-freeze", str(successor_path),
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.stdout, canonical_json(payload))
        self.assertEqual(payload["status"], "valid")
        self.assertEqual(payload["validated_treatment"], "exact")
        self.assertEqual(payload["score_eligible_count"], 0)
        self.assertEqual(payload["score_ineligible_count"], 1)
        self.assertEqual(payload["materializer_source_path"], "speckit-pro/speckit_pro_runner/agent_materialization.py")

    def test_cli_score_rejects_a_receipt_resealed_against_original_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            trace = copy.deepcopy(self.base_treatment)["treatment_traces"][0]
            source_path = root / "phase-executor.toml"
            source_path.write_bytes(PHASE_AGENT_SOURCE.read_bytes())
            qualification_path = root / "qualification.json"
            wrapper = apply_materialized_source(
                qualification_bundle(self.base_treatment),
                source_path,
            )
            wrapper, successor_freeze = bind_qualification_to_successor(wrapper)
            successor_path = root / "successor.json"
            write_canonical_json(qualification_path, wrapper)
            write_canonical_json(successor_path, successor_freeze)
            receipt_path = root / "validated-treatment.json"
            validation = run_qualification_cli(
                "validate-treatment",
                "--qualification-bundle", str(qualification_path),
                "--agent-policy-source", str(source_path),
                "--source-relative-path", PHASE_AGENT_RELATIVE_PATH,
                "--successor-freeze", str(successor_path),
                "--output", str(receipt_path),
            )
            self.assertEqual(validation.returncode, 0, validation.stdout)

            forged = load_json(receipt_path)
            trace_id = trace["objective_binding"]["execution_trace_id"]
            forged["score_eligible_execution_trace_ids"] = [trace_id]
            forged["score_eligible_count"] = 1
            forged["score_ineligible_count"] = 0
            write_canonical_json(receipt_path, forged)
            score_request_path = root / "score-request.json"
            write_canonical_json(
                score_request_path,
                {"execution_trace_binding": {"id": trace_id}},
            )

            completed = run_qualification_cli(
                "score",
                "--score-request", str(score_request_path),
                "--validated-treatment", str(receipt_path),
                "--qualification-bundle", str(qualification_path),
                "--agent-policy-source", str(source_path),
                "--source-relative-path", PHASE_AGENT_RELATIVE_PATH,
                "--successor-freeze", str(successor_path),
            )

        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["reason"], "score_before_treatment_refused")
        self.assertIn("joined to original evidence", payload["message"])

    def test_cli_validate_treatment_rejects_source_bytes_that_do_not_match_materialization(self) -> None:
        self.assertTrue(QUALIFICATION_RUNNER_PATH.exists())

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original_source = root / "phase-executor.toml"
            trace = copy.deepcopy(self.base_treatment)["treatment_traces"][0]
            original_source.write_bytes(PHASE_AGENT_SOURCE.read_bytes())
            wrapper = apply_materialized_source(qualification_bundle(self.base_treatment), original_source)
            wrapper, successor_freeze = bind_qualification_to_successor(wrapper)
            bundle_path = root / "qualification.json"
            successor_path = root / "successor.json"
            write_canonical_json(bundle_path, wrapper)
            write_canonical_json(successor_path, successor_freeze)
            changed_source = root / "changed-phase-executor.toml"
            changed_source.write_bytes(PHASE_AGENT_SOURCE.read_bytes() + b"\n# changed\n")

            completed = run_qualification_cli(
                "validate-treatment",
                "--qualification-bundle", str(bundle_path),
                "--agent-policy-source", str(changed_source),
                "--source-relative-path", PHASE_AGENT_RELATIVE_PATH,
                "--successor-freeze", str(successor_path),
            )

        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.stdout, canonical_json(payload))
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["command"], "validate-treatment")
        self.assertIn("do not match the declared repository path", payload["error"])

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

    def test_cli_score_accepts_only_a_replayed_exact_treatment_receipt(self) -> None:
        cli = load_qualification_cli()
        helpers = load_scoring_test_helpers()
        scoring = helpers.load_scoring_module()
        gate_result = scoring.evaluate_hard_gates(helpers.gate_request())
        semantic_result = scoring.evaluate_blinded_ballots(
            gate_result,
            helpers.semantic_request(),
        )
        score_request = helpers.score_bundle_request(
            gate_result,
            semantic_result=semantic_result,
        )
        receipt = {
            "command": "validate-treatment",
            "execution_trace_ids": [gate_result["execution_trace_id"]],
            "score_eligible_execution_trace_ids": [
                gate_result["execution_trace_id"]
            ],
            "score_eligible_execution_trace_bindings": [{
                "id": gate_result["execution_trace_id"],
                "digest": gate_result["trace_digest"],
            }],
            "materialization_ids": [schema_digest("materialization")],
            "materializer_source_path": (
                "speckit-pro/speckit_pro_runner/agent_materialization.py"
            ),
            "matched_materialization_id": schema_digest("materialization"),
            "score_eligible_count": 1,
            "score_ineligible_count": 0,
            "status": "valid",
            "validated_treatment": "exact",
        }
        authority_fields = (
            "assignment_binding",
            "candidate_route_binding",
            "agent_contract_binding",
            "runtime_snapshot_binding",
            "candidate_freeze_binding",
            "route_resolution_binding",
            "experiment_policy_binding",
            "treatment_contract_binding",
            "telemetry_profile_binding",
        )
        receipt["score_authority_bindings_by_execution_trace_id"] = {
            gate_result["execution_trace_id"]: {
                field: copy.deepcopy(score_request[field])
                for field in authority_fields
            }
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            score_request_path = root / "score-request.json"
            write_canonical_json(score_request_path, score_request)
            receipt_path = root / "validated-treatment.json"
            write_canonical_json(receipt_path, receipt)
            cli.validate_treatment_command = lambda _args: (
                0,
                copy.deepcopy(receipt),
            )
            exit_code, payload = cli.score_command(
                types.SimpleNamespace(
                    score_request=score_request_path,
                    validated_treatment=receipt_path,
                    qualification_bundle=root / "qualification.json",
                    agent_policy_source=root / "phase-executor.toml",
                    source_relative_path=PHASE_AGENT_RELATIVE_PATH,
                    trusted_qualification_evidence=None,
                    successor_freeze=root / "successor.json",
                )
            )
            drift_gate_request = helpers.gate_request()
            drift_gate_request["execution_trace_id"] = gate_result[
                "execution_trace_id"
            ]
            drift_gate_request["trace_digest"] = schema_digest(
                "different-source-trace"
            )
            drift_gate_result = scoring.evaluate_hard_gates(drift_gate_request)
            drift_semantic_result = scoring.evaluate_blinded_ballots(
                drift_gate_result,
                helpers.semantic_request(),
            )
            write_canonical_json(
                score_request_path,
                helpers.score_bundle_request(
                    drift_gate_result,
                    semantic_result=drift_semantic_result,
                ),
            )
            with self.assertRaisesRegex(
                cli.ScoreBlocked,
                "execution trace binding",
            ):
                cli.score_command(
                    types.SimpleNamespace(
                        score_request=score_request_path,
                        validated_treatment=receipt_path,
                        qualification_bundle=root / "qualification.json",
                        agent_policy_source=root / "phase-executor.toml",
                        source_relative_path=PHASE_AGENT_RELATIVE_PATH,
                        trusted_qualification_evidence=None,
                        successor_freeze=root / "successor.json",
                    )
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "scored")
        self.assertEqual(
            payload["score_bundle"],
            scoring.build_score_bundle(score_request),
        )

    def test_cli_calibrate_refuses_implicit_live_and_accepts_confirmed_pinned_local_setup(self) -> None:
        self.assertTrue(QUALIFICATION_RUNNER_PATH.exists())

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            partition_path = root / "partition.json"
            freeze_path = root / "freeze.json"
            policy_path = root / "policy.json"
            protocol_path = root / "protocol.json"
            corpus_path = root / "corpus.json"
            budget_path = root / "budget.json"
            raw_root = root / "operator-raw"
            raw_root.mkdir()
            partition = partition_binding()
            freeze = calibration_candidate_freeze_fixture()
            corpus = calibration_corpus_fixture()
            protocol = calibration_protocol_fixture()
            policy = calibration_cli_policy_fixture(protocol)
            budget = full_budget()
            for path, value in (
                (partition_path, partition),
                (freeze_path, freeze),
                (policy_path, policy),
                (protocol_path, protocol),
                (corpus_path, corpus),
                (budget_path, budget),
            ):
                write_canonical_json(path, value)

            no_confirmation = run_qualification_cli(
                "calibrate",
                "--partition", str(partition_path),
                "--candidate-freeze", str(freeze_path),
                "--experiment-policy", str(policy_path),
                "--calibration-protocol", str(protocol_path),
                "--corpus", str(corpus_path),
                "--budget", str(budget_path),
                "--raw-evidence-root", str(raw_root),
            )

            self.assertEqual(no_confirmation.returncode, 2)
            refused = json.loads(no_confirmation.stdout)
            self.assertEqual(no_confirmation.stdout, canonical_json(refused))
            self.assertEqual(refused["status"], "blocked")
            self.assertEqual(refused["reason"], "explicit_live_confirmation_required")

            confirmed = run_qualification_cli(
                "calibrate",
                "--partition", str(partition_path),
                "--candidate-freeze", str(freeze_path),
                "--experiment-policy", str(policy_path),
                "--calibration-protocol", str(protocol_path),
                "--corpus", str(corpus_path),
                "--budget", str(budget_path),
                "--raw-evidence-root", str(raw_root),
                "--confirm-explicit-local-live",
            )

        self.assertEqual(confirmed.returncode, 0, confirmed.stderr)
        payload = json.loads(confirmed.stdout)
        self.assertEqual(confirmed.stdout, canonical_json(payload))
        self.assertEqual(payload["status"], "calibration_ready")
        self.assertEqual(payload["command"], "calibrate")
        self.assertEqual(payload["execution_mode"], "explicit_local_live")
        self.assertFalse(payload["network_access"])
        self.assertEqual(payload["live_writes"], [])
        self.assertEqual(payload["partition_binding"], partition)
        self.assertEqual(payload["pinned_client_binding"], freeze["pinned_client_binding"])
        self.assertEqual(payload["runtime_snapshot_binding"], freeze["runtime_snapshot_binding"])
        self.assertEqual(payload["budget"], budget)
        self.assertEqual(payload["calibration_protocol_binding"], calibration_protocol_binding(protocol))
        self.assertEqual(
            payload["environment_contract_binding"],
            policy["environment_contract_binding"],
        )
        self.assertEqual(payload["scorer_bindings"], protocol["scorer_bindings"])
        self.assertEqual(payload["rubric_binding"], protocol["rubric_binding"])
        self.assertEqual(payload["adjudicator_binding"], protocol["adjudicator_binding"])
        self.assertEqual(payload["workload_manifest_binding"], protocol["workload_manifest_binding"])
        self.assertEqual(payload["cache_policy_binding"], protocol["cache_policy_binding"])

    def test_cli_calibrate_consumes_the_published_successor_freeze_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            partition = partition_binding()
            freeze = build_successor_freeze_from_sanitized_catalog()
            corpus = calibration_corpus_fixture()
            budget = full_budget()
            snapshot = freeze["runtime_capability_snapshot"]
            pinned_client = {
                "id": snapshot["client_identity_id"],
                "digest": snapshot["client_identity_id"],
            }
            runtime_snapshot = {
                "id": snapshot["runtime_capability_snapshot_id"],
                "digest": treatment.digest(snapshot),
            }
            successor_binding = {
                "id": freeze["candidate_freeze_id"],
                "digest": treatment.digest(freeze),
            }
            protocol = calibration_protocol_fixture()
            protocol.update({
                "candidate_freeze_binding": successor_binding,
                "pinned_client_binding": pinned_client,
                "runtime_snapshot_binding": runtime_snapshot,
            })
            protocol = seal_calibration_protocol(protocol)
            policy = calibration_cli_policy_fixture(protocol)
            policy.update({
                "candidate_freeze_binding": successor_binding,
            })
            policy = refresh_comparison_pair_digests(policy)
            paths = {
                "partition": root / "partition.json",
                "freeze": root / "freeze.json",
                "policy": root / "policy.json",
                "protocol": root / "protocol.json",
                "corpus": root / "corpus.json",
                "budget": root / "budget.json",
            }
            for name, value in (
                ("partition", partition),
                ("freeze", freeze),
                ("policy", policy),
                ("protocol", protocol),
                ("corpus", corpus),
                ("budget", budget),
            ):
                write_canonical_json(paths[name], value)
            raw_root = root / "operator-raw"
            raw_root.mkdir()

            completed = run_qualification_cli(
                "calibrate",
                "--partition", str(paths["partition"]),
                "--candidate-freeze", str(paths["freeze"]),
                "--experiment-policy", str(paths["policy"]),
                "--calibration-protocol", str(paths["protocol"]),
                "--corpus", str(paths["corpus"]),
                "--budget", str(paths["budget"]),
                "--raw-evidence-root", str(raw_root),
                "--confirm-explicit-local-live",
            )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["pinned_client_binding"], pinned_client)
        self.assertEqual(payload["runtime_snapshot_binding"], runtime_snapshot)

    def test_cli_calibrate_rejects_later_partitions_missing_budgets_and_repo_raw_root(self) -> None:
        cases = [
            ("later_partition", {"partition": partition_binding("selection", eligible=True)}, "calibration_partition_required"),
            ("missing_budget", {"drop_budget_field": "max_output_tokens"}, "campaign_budget_incomplete"),
            ("repo_raw_root", {"raw_root": ROOT}, "operator_only_raw_root_required"),
            ("open_policy", {"open_policy": True}, "experiment_policy_schema_invalid"),
        ]
        for label, override, reason in cases:
            with self.subTest(case=label):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    partition_path = root / "partition.json"
                    freeze_path = root / "freeze.json"
                    policy_path = root / "policy.json"
                    protocol_path = root / "protocol.json"
                    corpus_path = root / "corpus.json"
                    budget_path = root / "budget.json"
                    raw_root = Path(override.get("raw_root", root / "operator-raw"))
                    if raw_root != ROOT:
                        raw_root.mkdir()
                    partition = copy.deepcopy(override.get("partition", partition_binding()))
                    freeze = calibration_candidate_freeze_fixture()
                    corpus = calibration_corpus_fixture()
                    protocol = calibration_protocol_fixture()
                    policy = calibration_cli_policy_fixture(protocol)
                    budget = full_budget()
                    if "drop_budget_field" in override:
                        del budget[override["drop_budget_field"]]
                    if override.get("open_policy"):
                        policy["operator_note"] = "untrusted"
                    for path, value in (
                        (partition_path, partition),
                        (freeze_path, freeze),
                        (policy_path, policy),
                        (protocol_path, protocol),
                        (corpus_path, corpus),
                        (budget_path, budget),
                    ):
                        write_canonical_json(path, value)

                    completed = run_qualification_cli(
                        "calibrate",
                        "--partition", str(partition_path),
                        "--candidate-freeze", str(freeze_path),
                        "--experiment-policy", str(policy_path),
                        "--calibration-protocol", str(protocol_path),
                        "--corpus", str(corpus_path),
                        "--budget", str(budget_path),
                        "--raw-evidence-root", str(raw_root),
                        "--confirm-explicit-local-live",
                    )

                self.assertEqual(completed.returncode, 2)
                payload = json.loads(completed.stdout)
                self.assertEqual(payload["status"], "error")
                self.assertEqual(payload["reason"], reason)

    def test_cli_freeze_analysis_plan_writes_canonical_frozen_plan_before_cohort_outcomes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report_path = root / "calibration-report.json"
            draft_path = root / "analysis-plan-draft.json"
            output_path = root / "analysis-plan.json"
            report = seal_calibration_report({
                "schema_version": "calibration-report.v1",
                "calibration_protocol_binding": calibration_protocol_binding(
                    calibration_protocol_fixture()
                ),
                "calibration_partition_binding": partition_binding(),
                "calibration_evidence_bindings": [schema_binding("calibration-evidence")],
                "freeze_provenance": {
                    "frozen_at": "2026-07-24T16:00:00Z",
                    "frozen_after_calibration": True,
                    "cohort_outcome_observed": False,
                    "pre_cohort_outcome_absence_digest": schema_digest("pre-cohort-absence"),
                    "independent_review_binding": schema_binding("analysis-review"),
                },
                "calibration_completion": calibration_completion_fixture(),
            })
            draft = analysis_plan_fixture()
            draft["status"] = "draft_from_calibration"
            write_canonical_json(report_path, report)
            write_canonical_json(draft_path, draft)

            completed = run_qualification_cli(
                "freeze-analysis-plan",
                "--calibration-report", str(report_path),
                "--draft-plan", str(draft_path),
                "--output", str(output_path),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            frozen = load_json(output_path)
            self.assertEqual(output_path.read_text(encoding="utf-8"), canonical_json(frozen))
            self.assertEqual(payload, frozen)
            self.assertEqual(frozen["status"], "frozen")
            self.assertEqual(
                frozen["calibration_protocol_binding"],
                report["calibration_protocol_binding"],
            )
            self.assertEqual(
                frozen["calibration_completion_binding"],
                calibration_completion_binding(
                    report["calibration_completion"]
                ),
            )
            self.assertEqual(frozen["calibration_partition_binding"], report["calibration_partition_binding"])
            self.assertEqual(frozen["calibration_evidence_bindings"], report["calibration_evidence_bindings"])
            self.assertEqual(frozen["freeze_provenance"], report["freeze_provenance"])
            expected_digest = treatment.digest({
                key: value for key, value in frozen.items()
                if key not in {"analysis_plan_id", "analysis_plan_digest"}
            })
            self.assertEqual(frozen["analysis_plan_digest"], expected_digest)
            self.assertEqual(frozen["analysis_plan_id"], content_id(frozen, "analysis_plan_id"))
            self.assertNotEqual(frozen["analysis_plan_digest"], draft["analysis_plan_digest"])
            self.assertNotEqual(frozen["analysis_plan_id"], draft["analysis_plan_id"])

            report["freeze_provenance"]["cohort_outcome_observed"] = True
            report = seal_calibration_report(report)
            write_canonical_json(report_path, report)
            refused = run_qualification_cli(
                "freeze-analysis-plan",
                "--calibration-report", str(report_path),
                "--draft-plan", str(draft_path),
                "--output", str(output_path),
            )

        self.assertEqual(refused.returncode, 2)
        refusal = json.loads(refused.stdout)
        self.assertEqual(refusal["status"], "error")
        self.assertEqual(refusal["reason"], "cohort_outcome_observed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
