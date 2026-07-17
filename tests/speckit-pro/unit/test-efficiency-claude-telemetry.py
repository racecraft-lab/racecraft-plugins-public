#!/usr/bin/env python3
"""Deterministic contract tests for the CAR-002 Claude trace/telemetry schema.

The shipped JSON Schema at ``docs/ai/research/claude-trace-contract.schema.json``
publishes four record contracts as ``$defs`` — ``runtimeCapabilitySnapshot``,
``telemetryProfile``, ``routeResolution``, and ``exactTreatmentReplay`` — plus
shared primitive/ID ``$defs`` (the WP1 foundation these tests gate). Every check
is offline and makes zero live model calls (FR-002).

Two families of tests live here:

* **Schema-structural** cases load the shipped schema file and assert its
  strictness, the four record ``$defs``, the shared primitives, the roadmap
  route-resolution bindings, and identical cross-reference ID patterns. They go
  green once the schema is authored (T003/T004).
* **Validator-contract** cases exercise the standard-library validator
  ``claude_trace_schema`` (T005 deliverable at
  ``tests/speckit-pro/layer6-efficiency/lib/claude_trace_schema.py``): each of the
  four record ``$defs`` is checked with an inline conformant sample (accepted) and
  a family of malformed variants (rejected fail-closed).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LIB_DIR = TEST_ROOT / "lib"
LAYER6_LIB_DIR = TEST_ROOT / "layer6-efficiency" / "lib"
for _path in (LIB_DIR, LAYER6_LIB_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from test_result import run_counted  # noqa: E402

try:  # T005 deliverable — absent until the validator module is implemented.
    import claude_trace_schema  # type: ignore[import-not-found]  # noqa: E402
except ImportError:
    claude_trace_schema = None  # type: ignore[assignment]


RESEARCH_ROOT = REPO_ROOT / "docs" / "ai" / "research"
SCHEMA_PATH = RESEARCH_ROOT / "claude-trace-contract.schema.json"

RECORD_DEFS = (
    "runtimeCapabilitySnapshot",
    "telemetryProfile",
    "routeResolution",
    "exactTreatmentReplay",
)
VALIDATOR_ENTRYPOINTS = (
    "validate_runtime_capability_snapshot",
    "validate_telemetry_profile",
    "validate_route_resolution",
    "validate_exact_treatment_replay",
)
SNAPSHOT_ID_PATTERN = r"^CAR-002-RCS-[0-9]{4}-[0-9]{2}-[0-9]{2}-V[0-9]+$"
CANDIDATE_ROUTE_ID_PATTERN = r"^CAR-001-CR-[0-9]{2}-[0-9]{2}$"
AGENT_CONTRACT_ID_PATTERN = r"^car\.[a-z0-9-]+\.v[0-9]+$"
CAMEL_CASE = re.compile(r"^[a-z][a-zA-Z0-9]*$")
SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")


def load_schema() -> dict[str, object] | None:
    try:
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


# -- Inline conformant record samples (T006) ---------------------------------
# Each builder returns a freshly-constructed, schema-conformant instance of one
# record $def so a test can mutate a copy without disturbing the others. Hashes
# are real SHA-256 digests so they satisfy the shared ``sha256`` pattern.


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _raw_evidence() -> dict[str, object]:
    raw_output = '{"result":"ok","modelUsage":{"claude-opus-4-8":{"inputTokens":5}}}'
    return {
        "raw_output": raw_output,
        "raw_output_sha256": _sha256_hex(raw_output),
        "sanitization": "home_paths_normalized_utf8",
    }


def _unset_proof() -> dict[str, object]:
    return {
        "fallback_model_unset": True,
        "fallbackModel_unset": True,
        "claude_code_subagent_model_unset": True,
        "available_models_absent": True,
        "enforce_available_models_observed": None,
        "config_dir_isolation": "none",
        "inherit_equivalent_to_unset": None,
        "org_restriction_gap": None,
    }


def valid_models_endpoint_evidence() -> dict[str, object]:
    return {
        "access_status": "accessible",
        "dated_model_ids": ["claude-opus-4-8"],
        "per_model_effort_flags": {},
        "note": "GET /v1/models corroboration in api_key mode",
    }


def valid_runtime_capability_snapshot() -> dict[str, object]:
    canary_text = "Reply with the single word: ok"
    return {
        "schema_version": "1.0.0",
        "runtime_capability_snapshot_id": "CAR-002-RCS-2026-07-16-V1",
        "captured_at_utc": "2026-07-16T12:00:00Z",
        "pinned_client_version": "2.19.3",
        "authentication_mode": "api_key",
        "canary": {"text": canary_text, "canary_sha256": _sha256_hex(canary_text)},
        "tuple_evidence": [
            {
                "tuple_id": "opus__max",
                "model_requested": "opus",
                "effort_requested": "max",
                "resolved_dated_model_id": "claude-opus-4-8",
                "effort_acceptance": "accepted",
                "effort_probe_output_mode": "plain_text_print",
                "raw_evidence": _raw_evidence(),
            }
        ],
        "alias_bindings": [
            {
                "alias": "opus",
                "resolved_dated_model_id": "claude-opus-4-8",
                "tuple_id": "opus__max",
                "raw_evidence": _raw_evidence(),
            }
        ],
        "unavailable_observations": [
            {
                "surface": "print_model",
                "requested_unavailable_model_id": "claude-opus-3-0",
                "observed_outcome": "soft_remap",
                "observed_model_id": "claude-opus-4-8",
                "unset_proof": _unset_proof(),
                "remap_flagged": True,
                "dispatch_equivalence_caveat": "file-agent @mention approximates the production Agent tool",
                "raw_evidence": _raw_evidence(),
            }
        ],
        "models_endpoint_evidence": None,
        "capability_answers": [
            {
                "capability_question_id": question_id,
                "status": "answered",
                "answer": "recorded",
                "evidence_refs": ["opus__max"],
                "label": "observation",
            }
            for question_id in ("CAP-Q1", "CAP-Q2", "CAP-Q3", "CAP-Q4", "CAP-Q5", "CAP-Q6")
        ],
        "open_gaps": [],
    }


def valid_telemetry_profile() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "telemetry_profile_id": "CAR-002-TP-2026-07-16-V1",
        "pinned_client_version": "2.19.3",
        "runtime_capability_snapshot_id": "CAR-002-RCS-2026-07-16-V1",
        "field_classifications": [
            {
                "field": "usage.input_tokens",
                "classification": "stable_native",
                "observed_value": "1234",
                "label": "observation",
                "source_ref": None,
            }
        ],
    }


def valid_route_resolution() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "route_resolution_id": "CAR-002-RR-FIXTURE-001",
        "agent_contract_id": "car.implement-executor.v1",
        "candidate_route_id": "CAR-001-CR-01-01",
        "runtime_capability_snapshot_id": "CAR-002-RCS-2026-07-16-V1",
        "requested_model_alias": "opus",
        "resolved_dated_model_id": "claude-opus-4-8",
        "effort_level": "max",
        "instruction_sha256": _sha256_hex("role instruction body"),
        "mutation_contract": "additive_only",
        "dispatch_namespace": "speckit-pro:implement-executor",
        "parent_session_configuration": None,
        "client_version": "2.19.3",
        "fast_mode_state": "off",
        "env_override_proof": _unset_proof(),
        "fallback_index": None,
        "fallback_reason": None,
        "tuple_id": "opus__max",
    }


def valid_exact_treatment_replay() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "route_resolution": valid_route_resolution(),
        "execution_trace_id": None,
        "record_class": "success",
        "observed_model_id": "claude-opus-4-8",
        "outcome": {"status": "completed", "telemetry_ref": None, "notes": None},
        "scorable": True,
    }


class ClaudeTraceSchemaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_schema()

    def require_schema(self) -> dict[str, object]:
        self.assertIsNotNone(
            self.schema,
            f"shipped schema not authored yet (T003/T004): {SCHEMA_PATH}",
        )
        return self.schema  # type: ignore[return-value]

    def object_defs(self, schema: dict[str, object]) -> dict[str, dict]:
        return {
            name: node
            for name, node in schema["$defs"].items()
            if isinstance(node, dict) and node.get("type") == "object" and "properties" in node
        }

    # -- Schema-structural cases (green once T003/T004 author the schema) -----

    def test_shipped_schema_loads_and_declares_draft_2020_12(self) -> None:
        schema = self.require_schema()
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertIsInstance(schema.get("$id"), str)
        self.assertTrue(schema["$id"], "top-level $id must be a non-empty string")
        self.assertIn("$defs", schema)

    def test_schema_publishes_the_four_record_defs(self) -> None:
        schema = self.require_schema()
        for name in RECORD_DEFS:
            self.assertIn(name, schema["$defs"], name)
        # The oneOf publishes exactly the four record contracts as a review-visible union.
        one_of_refs = {branch.get("$ref") for branch in schema.get("oneOf", [])}
        self.assertEqual(
            one_of_refs,
            {f"#/$defs/{name}" for name in RECORD_DEFS},
        )

    def test_shared_primitive_defs_are_present_and_typed(self) -> None:
        schema = self.require_schema()
        defs = schema["$defs"]
        self.assertEqual(defs["sha256"], {"type": "string", "pattern": r"^[0-9a-f]{64}$"})
        self.assertEqual(defs["nullableString"], {"type": ["string", "null"]})
        raw = defs["rawEvidence"]
        self.assertIs(raw["additionalProperties"], False)
        self.assertEqual(set(raw["required"]), {"raw_output", "raw_output_sha256", "sanitization"})
        self.assertEqual(raw["properties"]["sanitization"], {"const": "home_paths_normalized_utf8"})
        self.assertEqual(raw["properties"]["raw_output_sha256"], {"$ref": "#/$defs/sha256"})

    def test_every_object_def_is_strict_and_symmetric(self) -> None:
        schema = self.require_schema()
        object_defs = self.object_defs(schema)
        self.assertTrue(object_defs, "schema must publish object $defs")
        for name, node in object_defs.items():
            with self.subTest(definition=name):
                self.assertIs(node["additionalProperties"], False, name)
                self.assertEqual(set(node["required"]), set(node["properties"]), name)

    def test_every_record_def_pins_schema_version_const(self) -> None:
        schema = self.require_schema()
        for name in RECORD_DEFS:
            with self.subTest(definition=name):
                schema_version = schema["$defs"][name]["properties"]["schema_version"]
                self.assertEqual(schema_version, {"const": "1.0.0"}, name)

    def test_def_names_are_camelcase_and_instance_fields_are_snake_case(self) -> None:
        schema = self.require_schema()
        for name in schema["$defs"]:
            with self.subTest(definition=name):
                self.assertRegex(name, CAMEL_CASE, name)
                self.assertNotIn("_", name, name)
        for name in RECORD_DEFS:
            for field in schema["$defs"][name]["properties"]:
                with self.subTest(field=f"{name}.{field}"):
                    self.assertRegex(field, SNAKE_CASE, field)

    def test_route_resolution_binds_dispatch_namespace_and_fallback_fields(self) -> None:
        schema = self.require_schema()
        route = schema["$defs"]["routeResolution"]
        required = set(route["required"])
        props = route["properties"]
        for field in (
            "dispatch_namespace",
            "parent_session_configuration",
            "fallback_index",
            "fallback_reason",
        ):
            with self.subTest(field=field):
                self.assertIn(field, required, field)
                self.assertIn(field, props, field)
        self.assertEqual(props["dispatch_namespace"], {"type": "string", "minLength": 1})
        self.assertEqual(props["parent_session_configuration"], {"$ref": "#/$defs/nullableString"})
        self.assertEqual(props["fallback_index"], {"type": ["integer", "null"]})
        self.assertEqual(props["fallback_reason"], {"$ref": "#/$defs/nullableString"})

    def test_cross_reference_ids_are_pattern_constrained_identically(self) -> None:
        schema = self.require_schema()
        defs = schema["$defs"]
        # runtime_capability_snapshot_id is validated by ONE shared pattern def
        # wherever it appears (FR-015: no $def accepts as free text an ID another
        # $def pattern-enforces).
        snapshot_id_carriers = ("runtimeCapabilitySnapshot", "telemetryProfile", "routeResolution")
        for carrier in snapshot_id_carriers:
            with self.subTest(carrier=carrier):
                self.assertEqual(
                    defs[carrier]["properties"]["runtime_capability_snapshot_id"],
                    {"$ref": "#/$defs/runtimeCapabilitySnapshotId"},
                    carrier,
                )
        self.assertEqual(defs["runtimeCapabilitySnapshotId"]["pattern"], SNAPSHOT_ID_PATTERN)
        # CAR-001 cross-reference IDs carry the manifest patterns, never free text.
        route_props = defs["routeResolution"]["properties"]
        self.assertEqual(route_props["candidate_route_id"], {"$ref": "#/$defs/candidateRouteId"})
        self.assertEqual(route_props["agent_contract_id"], {"$ref": "#/$defs/agentContractId"})
        self.assertEqual(defs["candidateRouteId"]["pattern"], CANDIDATE_ROUTE_ID_PATTERN)
        self.assertEqual(defs["agentContractId"]["pattern"], AGENT_CONTRACT_ID_PATTERN)
        for shared in ("runtimeCapabilitySnapshotId", "candidateRouteId", "agentContractId"):
            with self.subTest(shared=shared):
                self.assertIn("pattern", defs[shared], shared)
                self.assertNotIn("minLength", defs[shared], shared)

    # -- Validator-contract cases (RED until T005 ships claude_trace_schema) ---

    def test_stdlib_validator_exposes_a_fail_closed_entrypoint_per_record(self) -> None:
        self.assertIsNotNone(
            claude_trace_schema,
            "claude_trace_schema validator module not implemented yet (T005)",
        )
        for entrypoint in VALIDATOR_ENTRYPOINTS:
            with self.subTest(entrypoint=entrypoint):
                self.assertTrue(
                    callable(getattr(claude_trace_schema, entrypoint, None)),
                    entrypoint,
                )

    def test_stdlib_validator_rejects_a_malformed_record_fail_closed(self) -> None:
        self.assertIsNotNone(
            claude_trace_schema,
            "claude_trace_schema validator module not implemented yet (T005)",
        )
        validate = getattr(claude_trace_schema, "validate_runtime_capability_snapshot", None)
        self.assertTrue(callable(validate), "validate_runtime_capability_snapshot")
        with self.assertRaises(Exception):
            validate({})

    # -- Validator conformance + fail-closed rejection (T006) -----------------
    # Drive the T005 stdlib validator with inline valid + invalid samples for
    # each of the four record $defs: conformant records are accepted and returned
    # unchanged; every malformed variant is rejected fail-closed.

    def require_validator(self):
        self.assertIsNotNone(
            claude_trace_schema,
            "claude_trace_schema validator module not implemented yet (T005)",
        )
        return claude_trace_schema

    def test_validator_accepts_conformant_samples_for_each_record(self) -> None:
        validator = self.require_validator()
        cases = {
            "validate_runtime_capability_snapshot": valid_runtime_capability_snapshot(),
            "validate_telemetry_profile": valid_telemetry_profile(),
            "validate_route_resolution": valid_route_resolution(),
            "validate_exact_treatment_replay": valid_exact_treatment_replay(),
        }
        for entrypoint, record in cases.items():
            with self.subTest(entrypoint=entrypoint):
                validate = getattr(validator, entrypoint)
                self.assertIs(validate(record), record)

    def test_validator_accepts_snapshot_with_models_endpoint_object(self) -> None:
        validator = self.require_validator()
        record = valid_runtime_capability_snapshot()
        record["models_endpoint_evidence"] = valid_models_endpoint_evidence()
        self.assertIs(validator.validate_runtime_capability_snapshot(record), record)

    def test_validator_rejects_malformed_runtime_capability_snapshots(self) -> None:
        validator = self.require_validator()
        error = validator.ClaudeTraceContractError
        mutations = {
            "missing required key": lambda r: r.pop("canary"),
            "wrong schema_version const": lambda r: r.__setitem__("schema_version", "2.0.0"),
            "bad snapshot id pattern": lambda r: r.__setitem__("runtime_capability_snapshot_id", "RCS-1"),
            "captured_at not UTC-Z": lambda r: r.__setitem__("captured_at_utc", "2026-07-16 12:00:00"),
            "bad authentication_mode enum": lambda r: r.__setitem__("authentication_mode", "oauth"),
            "additional property": lambda r: r.__setitem__("extra_field", True),
            "too few capability_answers": lambda r: r.__setitem__("capability_answers", r["capability_answers"][:5]),
            "empty tuple_evidence": lambda r: r.__setitem__("tuple_evidence", []),
            "bad tuple_id pattern": lambda r: r["tuple_evidence"][0].__setitem__("tuple_id", "opus-max"),
            "bad raw_evidence sha256": lambda r: r["tuple_evidence"][0]["raw_evidence"].__setitem__("raw_output_sha256", "deadbeef"),
            "bad canary sha256": lambda r: r["canary"].__setitem__("canary_sha256", "nothex"),
        }
        for label, mutate in mutations.items():
            with self.subTest(mutation=label):
                record = valid_runtime_capability_snapshot()
                mutate(record)
                with self.assertRaises(error):
                    validator.validate_runtime_capability_snapshot(record)

    def test_validator_rejects_malformed_telemetry_profiles(self) -> None:
        validator = self.require_validator()
        error = validator.ClaudeTraceContractError
        mutations = {
            "missing field_classifications": lambda r: r.pop("field_classifications"),
            "bad telemetry_profile_id pattern": lambda r: r.__setitem__("telemetry_profile_id", "CAR-002-TP-bad"),
            "bad snapshot cross-ref pattern": lambda r: r.__setitem__("runtime_capability_snapshot_id", "CAR-002-TP-2026-07-16-V1"),
            "empty field_classifications": lambda r: r.__setitem__("field_classifications", []),
            "bad classification enum": lambda r: r["field_classifications"][0].__setitem__("classification", "made_up"),
            "additional property": lambda r: r.__setitem__("extra", 1),
        }
        for label, mutate in mutations.items():
            with self.subTest(mutation=label):
                record = valid_telemetry_profile()
                mutate(record)
                with self.assertRaises(error):
                    validator.validate_telemetry_profile(record)

    def test_validator_rejects_malformed_route_resolutions(self) -> None:
        validator = self.require_validator()
        error = validator.ClaudeTraceContractError
        mutations = {
            "missing dispatch_namespace": lambda r: r.pop("dispatch_namespace"),
            "bad candidate_route_id pattern": lambda r: r.__setitem__("candidate_route_id", "CR-1"),
            "bad agent_contract_id pattern": lambda r: r.__setitem__("agent_contract_id", "implement-executor"),
            "bad instruction_sha256": lambda r: r.__setitem__("instruction_sha256", "xyz"),
            "fallback_index wrong type": lambda r: r.__setitem__("fallback_index", "0"),
            "fallback_index boolean not integer": lambda r: r.__setitem__("fallback_index", True),
            "bad fast_mode_state enum": lambda r: r.__setitem__("fast_mode_state", "maybe"),
            "parent_session_configuration wrong type": lambda r: r.__setitem__("parent_session_configuration", 3),
            "env_override_proof missing key": lambda r: r["env_override_proof"].pop("config_dir_isolation"),
            "additional property": lambda r: r.__setitem__("extra", None),
        }
        for label, mutate in mutations.items():
            with self.subTest(mutation=label):
                record = valid_route_resolution()
                mutate(record)
                with self.assertRaises(error):
                    validator.validate_route_resolution(record)

    def test_validator_rejects_malformed_exact_treatment_replays(self) -> None:
        validator = self.require_validator()
        error = validator.ClaudeTraceContractError
        mutations = {
            "bad record_class enum": lambda r: r.__setitem__("record_class", "partial"),
            "scorable wrong type": lambda r: r.__setitem__("scorable", "true"),
            "missing outcome": lambda r: r.pop("outcome"),
            "bad outcome.status enum": lambda r: r["outcome"].__setitem__("status", "done"),
            "execution_trace_id wrong type": lambda r: r.__setitem__("execution_trace_id", 7),
            "nested route_resolution invalid": lambda r: r["route_resolution"].pop("tuple_id"),
            "additional property": lambda r: r.__setitem__("extra", 1),
        }
        for label, mutate in mutations.items():
            with self.subTest(mutation=label):
                record = valid_exact_treatment_replay()
                mutate(record)
                with self.assertRaises(error):
                    validator.validate_exact_treatment_replay(record)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ClaudeTraceSchemaContractTests)
    raise SystemExit(run_counted(suite, label="test-efficiency-claude-telemetry"))
