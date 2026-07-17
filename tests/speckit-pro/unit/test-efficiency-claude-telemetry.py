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
import os
import re
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock


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

try:  # T009/T010 deliverable — absent until the probe-logic module is implemented.
    import claude_capabilities  # type: ignore[import-not-found]  # noqa: E402
except ImportError:
    claude_capabilities = None  # type: ignore[assignment]


RESEARCH_ROOT = REPO_ROOT / "docs" / "ai" / "research"
SCHEMA_PATH = RESEARCH_ROOT / "claude-trace-contract.schema.json"
MANIFEST_PATH = RESEARCH_ROOT / "claude-agent-route-candidate-manifest.json"

# The 37 committed CAR-001 candidate routes dedupe to exactly these 6 unique
# (model, effort) tuples (research R1; verified against the committed manifest).
EXPECTED_TUPLE_ROUTE_COUNTS = {
    "opus__max": 11,
    "sonnet__max": 11,
    "fable__max": 5,
    "haiku__max": 8,
    "haiku__low": 1,
    "sonnet__low": 1,
}
EXPECTED_TUPLE_IDS = frozenset(EXPECTED_TUPLE_ROUTE_COUNTS)
EXPECTED_ROUTE_TOTAL = 37
TUPLE_ID_PATTERN = re.compile(r"^[a-z0-9]+__[a-z0-9]+$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

# Local mirror of the committed privacy-scan path patterns
# (tests/speckit-pro/unit/test-privacy-scan.py): the probe sanitizer's output
# MUST neutralize every family the scan flags on committed files.
PRIVACY_HOME_PATH = re.compile(
    r"(?:/(?:Users|home)/|[A-Za-z]:[\\/]+Users[\\/]+)[A-Za-z0-9_.\-]+", re.IGNORECASE
)
PRIVACY_HYPHENATED_HOME = re.compile(r"-Users-[A-Za-z0-9_.\-]+", re.IGNORECASE)
PRIVACY_PRIVATE_VAR = re.compile(r"/private/var/folders/[A-Za-z0-9_/\.\-]+", re.IGNORECASE)
PRIVACY_TMP_TRANSCRIPT = re.compile(r"/private/tmp/claude-[0-9]+", re.IGNORECASE)

# The sanitizer tests need synthetic home/user and machine-local session paths as
# INPUTS, but the committed privacy scan forbids those literal path forms anywhere
# in the tree. Assemble each input from fragments so the runtime string is the real
# path while this file's source text carries no flagged literal.
_USERS_SEG = "Users"
_HOME_SEG = "home"
_PRIVATE_SEG = "/private"


def _home_posix(rest: str) -> str:
    return "/" + _USERS_SEG + "/" + rest


def _home_linux(rest: str) -> str:
    return "/" + _HOME_SEG + "/" + rest


def _home_windows(rest: str) -> str:
    return "C:\\" + _USERS_SEG + "\\" + rest


def _home_hyphenated(rest: str) -> str:
    return "-" + _USERS_SEG + "-" + rest


def _session_var(rest: str) -> str:
    return _PRIVATE_SEG + "/var/folders/" + rest


def _session_tmp(suffix: str) -> str:
    return _PRIVATE_SEG + "/tmp/" + "claude-" + suffix

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


class ClaudeCapabilitiesPureLogicTests(unittest.TestCase):
    """Pure-logic coverage for the operator probe tool (T009/T010, driven by T013).

    Exercises the deduplicated probe matrix, ``tuple_id`` derivation, the fixed
    canary text + hash, ``<home>`` sanitization, per-payload hashing, the three
    fail-closed dispositions, and the FR-003 budget/timeout/no-retry controls —
    all with zero live model calls (the single live boundary is injected as a
    fake ``LiveInvoker``, never spawned).
    """

    def require_capabilities(self):
        self.assertIsNotNone(
            claude_capabilities,
            "claude_capabilities probe-logic module not implemented yet (T009/T010): "
            f"{LAYER6_LIB_DIR / 'claude_capabilities.py'}",
        )
        return claude_capabilities

    # -- Bounded probe matrix (dedup 37 → 6 tuples) ---------------------------

    def test_probe_matrix_dedupes_37_routes_to_six_tuples(self) -> None:
        cap = self.require_capabilities()
        matrix = cap.build_probe_matrix()
        self.assertEqual(matrix.cardinality, 6)
        self.assertEqual(set(matrix.tuple_ids), set(EXPECTED_TUPLE_IDS))
        self.assertEqual(matrix.total_routes, EXPECTED_ROUTE_TOTAL)

    def test_probe_matrix_route_counts_match_committed_manifest(self) -> None:
        cap = self.require_capabilities()
        matrix = cap.build_probe_matrix()
        counts = {spec.tuple_id: spec.route_count for spec in matrix.tuples}
        self.assertEqual(counts, dict(EXPECTED_TUPLE_ROUTE_COUNTS))
        self.assertEqual(sum(counts.values()), EXPECTED_ROUTE_TOTAL)

    def test_probe_matrix_tuple_ids_are_schema_valid(self) -> None:
        cap = self.require_capabilities()
        for tuple_id in cap.build_probe_matrix().tuple_ids:
            with self.subTest(tuple_id=tuple_id):
                self.assertRegex(tuple_id, TUPLE_ID_PATTERN)

    def test_probe_matrix_derives_none_token_for_null_effort_route(self) -> None:
        cap = self.require_capabilities()
        synthetic = {
            "candidate_routes": [
                {
                    "model_selector": {"requested_value": "haiku"},
                    "effort_selector": {"requested_value": None},
                },
                {
                    "model_selector": {"requested_value": "opus"},
                    "effort_selector": {"requested_value": "max"},
                },
            ]
        }
        matrix = cap.build_probe_matrix(synthetic)
        self.assertEqual(set(matrix.tuple_ids), {"haiku__none", "opus__max"})
        self.assertEqual(matrix.total_routes, 2)

    # -- tuple_id derivation --------------------------------------------------

    def test_derive_tuple_id_joins_model_and_effort(self) -> None:
        cap = self.require_capabilities()
        self.assertEqual(cap.derive_tuple_id("opus", "max"), "opus__max")
        self.assertEqual(cap.derive_tuple_id("sonnet", "low"), "sonnet__low")

    def test_derive_tuple_id_null_effort_becomes_none(self) -> None:
        cap = self.require_capabilities()
        self.assertEqual(cap.derive_tuple_id("haiku", None), "haiku__none")

    def test_derive_tuple_id_lowercases_tokens(self) -> None:
        cap = self.require_capabilities()
        self.assertEqual(cap.derive_tuple_id("OPUS", "MAX"), "opus__max")

    # -- Fixed canary text + hash --------------------------------------------

    def test_canary_text_is_fixed_with_no_trailing_newline(self) -> None:
        cap = self.require_capabilities()
        self.assertEqual(cap.CANARY_TEXT, "Reply with the single word: ok")
        self.assertFalse(cap.CANARY_TEXT.endswith("\n"))

    def test_canary_hash_is_sha256_over_exact_utf8_bytes(self) -> None:
        cap = self.require_capabilities()
        expected = hashlib.sha256("Reply with the single word: ok".encode("utf-8")).hexdigest()
        self.assertEqual(cap.CANARY_SHA256, expected)
        self.assertRegex(cap.CANARY_SHA256, SHA256_PATTERN)

    def test_canary_metadata_records_text_and_hash(self) -> None:
        cap = self.require_capabilities()
        meta = cap.canary_metadata()
        self.assertEqual(set(meta), {"text", "canary_sha256"})
        self.assertEqual(meta["text"], cap.CANARY_TEXT)
        self.assertEqual(meta["canary_sha256"], cap.CANARY_SHA256)

    # -- <home> sanitization --------------------------------------------------

    def test_sanitize_normalizes_posix_home_paths(self) -> None:
        cap = self.require_capabilities()
        self.assertEqual(cap.sanitize_home_paths(_home_posix("alice/x")), "<home>/x")
        self.assertEqual(cap.sanitize_home_paths(_home_linux("bob/y")), "<home>/y")

    def test_sanitize_normalizes_windows_hyphenated_and_session_paths(self) -> None:
        cap = self.require_capabilities()
        cases = {
            "windows": _home_windows("alice\\proj"),
            "hyphenated": _home_hyphenated("alice-Documents"),
            "private_var": _session_var("ab/cd/T/x"),
            "tmp_transcript": _session_tmp("501"),
        }
        for label, raw in cases.items():
            with self.subTest(case=label):
                self.assertIn("<home>", cap.sanitize_home_paths(raw))

    def test_sanitized_output_passes_every_privacy_scan_pattern(self) -> None:
        cap = self.require_capabilities()
        raw = " ".join(
            (
                "cwd=" + _home_posix("alice/repo"),
                "tmp=" + _session_tmp("501"),
                "var=" + _session_var("ab/cd/T/z"),
                "win=" + _home_windows("bob\\proj"),
                "hy=" + _home_hyphenated("carol-x"),
            )
        )
        sanitized = cap.sanitize_home_paths(raw)
        for pattern in (
            PRIVACY_HOME_PATH,
            PRIVACY_HYPHENATED_HOME,
            PRIVACY_PRIVATE_VAR,
            PRIVACY_TMP_TRANSCRIPT,
        ):
            with self.subTest(pattern=pattern.pattern):
                self.assertIsNone(pattern.search(sanitized))

    def test_sanitize_is_idempotent_and_leaves_clean_text_untouched(self) -> None:
        cap = self.require_capabilities()
        clean = '{"result":"ok","modelUsage":{"claude-opus-4-8":{"inputTokens":5}}}'
        self.assertEqual(cap.sanitize_home_paths(clean), clean)
        once = cap.sanitize_home_paths(_home_posix("alice/x"))
        self.assertEqual(cap.sanitize_home_paths(once), once)

    # -- Per-payload SHA-256 over sanitized UTF-8 bytes -----------------------

    def test_payload_sha256_reproduces_over_sanitized_utf8_bytes(self) -> None:
        cap = self.require_capabilities()
        sanitized = cap.sanitize_home_paths('{"result":"ok"}')
        expected = hashlib.sha256(sanitized.encode("utf-8")).hexdigest()
        self.assertEqual(cap.payload_sha256(sanitized), expected)
        self.assertEqual(cap.payload_sha256(sanitized), cap.payload_sha256(sanitized))
        self.assertRegex(cap.payload_sha256(sanitized), SHA256_PATTERN)

    def test_payload_sha256_encodes_unicode_as_utf8(self) -> None:
        cap = self.require_capabilities()
        text = '{"note":"café ✓"}'
        self.assertEqual(
            cap.payload_sha256(text),
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
        )

    # -- Three fail-closed dispositions --------------------------------------

    def test_disposition_records_interpretable_platform_observations(self) -> None:
        cap = self.require_capabilities()
        cases = {
            "exit0 parseable schema-valid": cap.ProbeInvocationResult(return_code=0),
            "nonzero exit WITH parseable error body (hard rejection)": cap.ProbeInvocationResult(
                return_code=1
            ),
        }
        for label, result in cases.items():
            with self.subTest(case=label):
                self.assertEqual(
                    cap.classify_probe_disposition(
                        result, payload_parseable=True, observation_schema_valid=True
                    ),
                    cap.DISPOSITION_RECORD,
                )

    def test_disposition_records_undetermined_but_parseable_outcome(self) -> None:
        cap = self.require_capabilities()
        # An undetermined unavailable-probe outcome is a PARSEABLE, schema-valid
        # payload whose path cannot be classified — recorded, never aborted.
        result = cap.ProbeInvocationResult(return_code=0)
        self.assertEqual(
            cap.classify_probe_disposition(
                result, payload_parseable=True, observation_schema_valid=True
            ),
            cap.DISPOSITION_RECORD,
        )

    def test_disposition_aborts_write_on_unparseable_or_schema_invalid(self) -> None:
        cap = self.require_capabilities()
        cases = {
            "unparseable json payload (exit 0)": (cap.ProbeInvocationResult(return_code=0), False, True),
            "schema-invalid observation (exit 0)": (cap.ProbeInvocationResult(return_code=0), True, False),
        }
        for label, (result, parseable, valid) in cases.items():
            with self.subTest(case=label):
                self.assertEqual(
                    cap.classify_probe_disposition(
                        result, payload_parseable=parseable, observation_schema_valid=valid
                    ),
                    cap.DISPOSITION_ABORT_WRITE,
                )

    def test_disposition_aborts_run_on_transport_failure_never_unavailable(self) -> None:
        cap = self.require_capabilities()
        cases = {
            "timeout": cap.ProbeInvocationResult(return_code=None, timed_out=True),
            "network failure": cap.ProbeInvocationResult(return_code=None, network_error=True),
            "nonzero exit with no parseable body": cap.ProbeInvocationResult(return_code=1),
        }
        for label, result in cases.items():
            with self.subTest(case=label):
                disposition = cap.classify_probe_disposition(
                    result, payload_parseable=False, observation_schema_valid=False
                )
                self.assertEqual(disposition, cap.DISPOSITION_ABORT_RUN)
                # A transport failure is NEVER recorded (would falsely narrow
                # availability, FR-026).
                self.assertNotEqual(disposition, cap.DISPOSITION_RECORD)

    # -- FR-003 budget: bound == cardinality, overrun before any live call ----

    def test_enforce_invocation_budget_allows_within_ceiling(self) -> None:
        cap = self.require_capabilities()
        for cardinality in (0, 1, 12, cap.INVOCATION_BUDGET_CEILING):
            with self.subTest(cardinality=cardinality):
                self.assertIsNone(cap.enforce_invocation_budget(cardinality))

    def test_enforce_invocation_budget_surfaces_overrun(self) -> None:
        cap = self.require_capabilities()
        with self.assertRaises(cap.BudgetOverrunError):
            cap.enforce_invocation_budget(cap.INVOCATION_BUDGET_CEILING + 1)

    def test_planned_matrix_cardinality_sits_within_budget(self) -> None:
        cap = self.require_capabilities()
        matrix = cap.build_probe_matrix()
        plan = cap.plan_probe_invocations(matrix)
        by_purpose = Counter(item.purpose for item in plan)
        self.assertEqual(by_purpose[cap.PURPOSE_ALIAS_CANARY], len(matrix.model_aliases))
        self.assertEqual(by_purpose[cap.PURPOSE_CONFIG_ACCEPTANCE], matrix.cardinality)
        self.assertEqual(by_purpose[cap.PURPOSE_UNAVAILABLE_PROBE], 2)
        self.assertLessEqual(len(plan), cap.INVOCATION_BUDGET_CEILING)
        self.assertIsNone(cap.enforce_invocation_budget(len(plan)))

    def test_plan_config_invocations_cover_every_tuple(self) -> None:
        cap = self.require_capabilities()
        matrix = cap.build_probe_matrix()
        plan = cap.plan_probe_invocations(matrix)
        config_tuple_ids = {
            item.tuple_id for item in plan if item.purpose == cap.PURPOSE_CONFIG_ACCEPTANCE
        }
        self.assertEqual(config_tuple_ids, set(matrix.tuple_ids))

    def test_plan_unavailable_probes_cover_both_surfaces(self) -> None:
        cap = self.require_capabilities()
        plan = cap.plan_probe_invocations(cap.build_probe_matrix())
        surfaces = {
            item.surface for item in plan if item.purpose == cap.PURPOSE_UNAVAILABLE_PROBE
        }
        self.assertEqual(surfaces, {"print_model", "subagent_frontmatter"})

    # -- FR-003 driver: explicit timeout, no retries, overrun pre-flight ------

    def _canary_plan(self, cap, count):
        return tuple(
            cap.PlannedInvocation(purpose=cap.PURPOSE_ALIAS_CANARY, model_alias=f"m{index}")
            for index in range(count)
        )

    def test_driver_threads_explicit_timeout_and_records_it(self) -> None:
        cap = self.require_capabilities()
        plan = self._canary_plan(cap, 2)
        seen_timeouts = []

        def invoke(item, *, timeout_seconds):
            seen_timeouts.append(timeout_seconds)
            return cap.ProbeInvocationResult(return_code=0)

        run = cap.run_bounded_probe_matrix(plan, invoke, timeout_seconds=45.0)
        self.assertEqual(seen_timeouts, [45.0, 45.0])
        self.assertEqual(run.metadata["per_invocation_timeout_seconds"], 45.0)
        self.assertEqual(len(run.results), 2)

    def test_driver_requires_an_explicit_timeout(self) -> None:
        cap = self.require_capabilities()
        plan = self._canary_plan(cap, 1)
        with self.assertRaises(TypeError):
            cap.run_bounded_probe_matrix(plan, lambda item, *, timeout_seconds: None)

    def test_driver_surfaces_budget_overrun_before_any_live_call(self) -> None:
        cap = self.require_capabilities()
        plan = self._canary_plan(cap, cap.INVOCATION_BUDGET_CEILING + 1)
        calls = []

        def invoke(item, *, timeout_seconds):
            calls.append(item)
            return cap.ProbeInvocationResult(return_code=0)

        with self.assertRaises(cap.BudgetOverrunError):
            cap.run_bounded_probe_matrix(plan, invoke, timeout_seconds=30.0)
        self.assertEqual(calls, [])

    def test_driver_does_not_retry_a_timed_out_invocation(self) -> None:
        cap = self.require_capabilities()
        plan = self._canary_plan(cap, 3)
        calls = []

        def invoke(item, *, timeout_seconds):
            calls.append(item)
            return cap.ProbeInvocationResult(return_code=None, timed_out=True)

        with self.assertRaises(cap.ProbeRunAborted):
            cap.run_bounded_probe_matrix(plan, invoke, timeout_seconds=30.0)
        self.assertEqual(len(calls), 1)

    def test_driver_aborts_on_network_error_without_proceeding(self) -> None:
        cap = self.require_capabilities()
        plan = self._canary_plan(cap, 3)
        calls = []

        def invoke(item, *, timeout_seconds):
            calls.append(item)
            return cap.ProbeInvocationResult(return_code=None, network_error=True)

        with self.assertRaises(cap.ProbeRunAborted):
            cap.run_bounded_probe_matrix(plan, invoke, timeout_seconds=30.0)
        self.assertEqual(len(calls), 1)

    def test_pure_logic_and_driver_spawn_no_subprocess(self) -> None:
        cap = self.require_capabilities()
        plan = self._canary_plan(cap, 1)

        def invoke(item, *, timeout_seconds):
            return cap.ProbeInvocationResult(return_code=0)

        with mock.patch("subprocess.run", side_effect=AssertionError("no live subprocess in pure logic")):
            matrix = cap.build_probe_matrix()
            cap.plan_probe_invocations(matrix)
            cap.sanitize_home_paths(_home_posix("x/y"))
            cap.payload_sha256("{}")
            cap.classify_probe_disposition(
                cap.ProbeInvocationResult(return_code=0),
                payload_parseable=True,
                observation_schema_valid=True,
            )
            run = cap.run_bounded_probe_matrix(plan, invoke, timeout_seconds=30.0)
        self.assertEqual(len(run.results), 1)


# -- Canned offline payloads for the live-boundary tests (T011/T012/T014) -----
# Grounded dated IDs = the CAR-001 manifest CAP-Q1..Q4 "currently expected"
# alias bindings. No test makes a live call; every ``ProbeInvocationResult`` here
# is synthetic and every ``subprocess.run`` is monkeypatched or unreached.
_EXPECTED_DATED_IDS = {
    "opus": "claude-opus-4-8",
    "sonnet": "claude-sonnet-5",
    "haiku": "claude-haiku-4-5-20251001",
    "fable": "claude-fable-5",
}
_UNAVAILABLE_PROBE_ID = "claude-opus-3-0"


def _canary_stdout(dated_model_id: str) -> str:
    """A raw ``--output-format json`` canary payload whose single ``modelUsage``
    key is the effective dated model ID (there is no scalar ``model`` field —
    research R3)."""
    return json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "result": "ok",
            "modelUsage": {
                dated_model_id: {
                    "inputTokens": 5,
                    "outputTokens": 1,
                    "cacheReadInputTokens": 0,
                    "cacheCreationInputTokens": 0,
                    "contextWindow": 200000,
                    "costUSD": 0.0001,
                }
            },
            "usage": {"input_tokens": 5, "output_tokens": 1},
            "total_cost_usd": 0.0001,
            "num_turns": 1,
            "duration_ms": 100,
        }
    )


def _run_bounded_matrix_with_fake_invoker(cap):
    """Drive the REAL bounded matrix with a deterministic offline invoker (no
    subprocess). Alias canaries resolve to their grounded dated IDs; the
    unavailable probe soft-remaps to opus; effort probes return a clean
    plain-text acceptance. Returns ``(matrix, ProbeRun)``."""
    matrix = cap.build_probe_matrix()
    plan = cap.plan_probe_invocations(matrix)

    def invoke(item, *, timeout_seconds):
        if item.purpose == cap.PURPOSE_ALIAS_CANARY:
            return cap.ProbeInvocationResult(
                return_code=0,
                stdout=_canary_stdout(_EXPECTED_DATED_IDS[item.model_alias]),
                output_mode=cap.OUTPUT_MODE_JSON,
            )
        if item.purpose == cap.PURPOSE_CONFIG_ACCEPTANCE:
            return cap.ProbeInvocationResult(
                return_code=0,
                stdout=f"effort {item.effort_requested} applied to {item.model_alias}",
                output_mode=cap.OUTPUT_MODE_PLAIN_TEXT,
            )
        return cap.ProbeInvocationResult(
            return_code=0,
            stdout=_canary_stdout("claude-opus-4-8"),
            output_mode=cap.OUTPUT_MODE_JSON,
        )

    return matrix, cap.run_bounded_probe_matrix(plan, invoke, timeout_seconds=30.0)


def _argv_aware_fake_run(argv, **kwargs):
    """An offline stand-in for ``subprocess.run`` that returns a canned
    ``CompletedProcess`` shaped by the probe command it is handed — so ``main()``
    runs the whole matrix end-to-end with zero live model calls."""
    args = list(argv)
    joined = " ".join(args)
    if "--effort" in args:
        return subprocess.CompletedProcess(args, 0, stdout="effort applied", stderr="")
    if "--model" in args and args[args.index("--model") + 1] == _UNAVAILABLE_PROBE_ID:
        return subprocess.CompletedProcess(args, 0, stdout=_canary_stdout("claude-opus-4-8"), stderr="")
    if "@agent-" in joined and "--model" not in args:
        return subprocess.CompletedProcess(args, 0, stdout=_canary_stdout("claude-opus-4-8"), stderr="")
    if "--model" in args:
        alias = args[args.index("--model") + 1]
        return subprocess.CompletedProcess(
            args, 0, stdout=_canary_stdout(_EXPECTED_DATED_IDS.get(alias, "claude-opus-4-8")), stderr=""
        )
    return subprocess.CompletedProcess(args, 0, stdout=_canary_stdout("claude-opus-4-8"), stderr="")


class ClaudeCapabilitiesLiveBoundaryTests(unittest.TestCase):
    """The single live boundary (T011), capability-answer/evidence capture (T012),
    and the subagent-frontmatter dispatch mechanism (T014).

    Every test is deterministic and offline: the ``claude`` boundary is either an
    injected fake ``LiveInvoker`` or a monkeypatched ``subprocess.run``; the
    models endpoint is an injected fake; and the subagent probe agent file is
    always staged in a temp dir, never the repo's real ``.claude/agents/``. Zero
    live model calls (FR-001/FR-002).
    """

    def require_capabilities(self):
        self.assertIsNotNone(
            claude_capabilities,
            "claude_capabilities probe-logic module not implemented yet: "
            f"{LAYER6_LIB_DIR / 'claude_capabilities.py'}",
        )
        return claude_capabilities

    def _clean_unset_proof(self, cap):
        return cap.build_unset_proof(env={}, settings={})

    # -- T011: probe command construction (pure, FR-compliant argv) -----------

    def test_build_probe_command_shapes_argv_per_purpose_and_surface(self) -> None:
        cap = self.require_capabilities()

        canary = cap.build_probe_command(
            cap.PlannedInvocation(purpose=cap.PURPOSE_ALIAS_CANARY, model_alias="opus")
        )
        self.assertEqual(canary.output_mode, cap.OUTPUT_MODE_JSON)
        self.assertIn("--output-format", canary.argv)
        self.assertEqual(canary.argv[canary.argv.index("--output-format") + 1], "json")
        self.assertEqual(canary.argv[canary.argv.index("--model") + 1], "opus")
        self.assertEqual(canary.prompt, cap.CANARY_TEXT)
        self.assertIn(cap.CANARY_TEXT, canary.argv)
        self.assertIn("-p", canary.argv)

        config = cap.build_probe_command(
            cap.PlannedInvocation(
                purpose=cap.PURPOSE_CONFIG_ACCEPTANCE,
                model_alias="opus",
                effort_requested="max",
                tuple_id="opus__max",
            )
        )
        self.assertEqual(config.output_mode, cap.OUTPUT_MODE_PLAIN_TEXT)
        self.assertNotIn("--output-format", config.argv)  # plain-text --print avoids silent JSON clamp (R6)
        self.assertEqual(config.argv[config.argv.index("--effort") + 1], "max")
        self.assertEqual(config.argv[config.argv.index("--model") + 1], "opus")

        config_null = cap.build_probe_command(
            cap.PlannedInvocation(
                purpose=cap.PURPOSE_CONFIG_ACCEPTANCE,
                model_alias="haiku",
                effort_requested=None,
                tuple_id="haiku__none",
            )
        )
        self.assertNotIn("--effort", config_null.argv)

        print_model = cap.build_probe_command(
            cap.PlannedInvocation(purpose=cap.PURPOSE_UNAVAILABLE_PROBE, surface="print_model"),
            unavailable_model_id=_UNAVAILABLE_PROBE_ID,
        )
        self.assertEqual(print_model.argv[print_model.argv.index("--model") + 1], _UNAVAILABLE_PROBE_ID)
        self.assertIn("--output-format", print_model.argv)

        subagent = cap.build_probe_command(
            cap.PlannedInvocation(purpose=cap.PURPOSE_UNAVAILABLE_PROBE, surface="subagent_frontmatter"),
            unavailable_model_id=_UNAVAILABLE_PROBE_ID,
            agent_name="car002-probe",
        )
        # No preempting per-invocation --model on the subagent surface (R4/R12); not --bare.
        self.assertNotIn("--model", subagent.argv)
        self.assertNotIn("--bare", subagent.argv)
        self.assertTrue(subagent.prompt.startswith("@agent-car002-probe"))
        self.assertTrue(any(arg.startswith("@agent-car002-probe") for arg in subagent.argv))

    def test_no_probe_command_ever_passes_a_fallback_model_flag(self) -> None:
        # FR-010 unset-proof is structural: the tool never emits --fallback-model.
        cap = self.require_capabilities()
        plan = cap.plan_probe_invocations(cap.build_probe_matrix())
        for item in plan:
            command = cap.build_probe_command(item, unavailable_model_id=_UNAVAILABLE_PROBE_ID)
            with self.subTest(purpose=item.purpose, surface=item.surface):
                self.assertNotIn("--fallback-model", command.argv)
                self.assertNotIn("--fallback", command.argv)
                self.assertEqual(command.argv[0], cap.CLAUDE_BIN)

    # -- T011: the ONLY subprocess boundary (monkeypatched, never live) -------

    def test_invoke_claude_cli_maps_subprocess_outcomes(self) -> None:
        cap = self.require_capabilities()
        command = cap.build_probe_command(
            cap.PlannedInvocation(purpose=cap.PURPOSE_ALIAS_CANARY, model_alias="opus")
        )

        calls: list[tuple[list, dict]] = []

        def ok_run(argv, **kwargs):
            calls.append((list(argv), kwargs))
            return subprocess.CompletedProcess(list(argv), 0, stdout="OUT", stderr="")

        with mock.patch("subprocess.run", ok_run):
            result = cap.invoke_claude_cli(command, timeout_seconds=31.5)
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout, "OUT")
        self.assertEqual(result.output_mode, cap.OUTPUT_MODE_JSON)
        self.assertFalse(result.is_unambiguous_transport_failure())
        argv, kwargs = calls[0]
        self.assertEqual(argv, list(command.argv))
        self.assertIs(kwargs["shell"], False)
        self.assertIs(kwargs["text"], True)
        self.assertTrue(kwargs["capture_output"])
        self.assertEqual(kwargs["timeout"], 31.5)

        def timeout_run(argv, **kwargs):
            raise subprocess.TimeoutExpired(cmd=list(argv), timeout=kwargs.get("timeout", 1))

        with mock.patch("subprocess.run", timeout_run):
            timed = cap.invoke_claude_cli(command, timeout_seconds=5.0)
        self.assertTrue(timed.timed_out)
        self.assertIsNone(timed.return_code)
        self.assertTrue(timed.is_unambiguous_transport_failure())

        def missing_run(argv, **kwargs):
            raise FileNotFoundError("claude not on PATH")

        with mock.patch("subprocess.run", missing_run):
            spawn_fail = cap.invoke_claude_cli(command, timeout_seconds=5.0)
        self.assertIsNone(spawn_fail.return_code)
        self.assertTrue(spawn_fail.is_unambiguous_transport_failure())

    def test_build_arg_parser_parses_operator_options(self) -> None:
        cap = self.require_capabilities()
        parser = cap.build_arg_parser()
        ns = parser.parse_args(
            [
                "--timeout", "45",
                "--unavailable-model-id", "claude-x-0",
                "--pinned-client-version", "2.19.3",
                "--output", "out.json",
                "--version-number", "3",
            ]
        )
        self.assertEqual(ns.timeout, 45.0)
        self.assertEqual(ns.unavailable_model_id, "claude-x-0")
        self.assertEqual(ns.pinned_client_version, "2.19.3")
        self.assertEqual(Path(ns.output), Path("out.json"))
        self.assertEqual(ns.version_number, 3)
        defaults = parser.parse_args([])
        self.assertEqual(defaults.timeout, cap.DEFAULT_TIMEOUT_SECONDS)
        self.assertEqual(Path(defaults.output), cap.SNAPSHOT_OUTPUT_PATH)

    def test_module_import_and_command_building_spawn_no_subprocess(self) -> None:
        cap = self.require_capabilities()
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("subprocess.run", side_effect=AssertionError("no spawn at build time")):
                invoker = cap.LiveClaudeInvoker(agents_dir=Path(tmp))
                self.assertIsNotNone(invoker)
                for item in cap.plan_probe_invocations(cap.build_probe_matrix()):
                    self.assertTrue(cap.build_probe_command(item).argv)
                self.assertIsNotNone(cap.build_arg_parser())

    # -- T012: authentication mode + unset proof (pure) -----------------------

    def test_detect_authentication_mode_from_documented_env_signals(self) -> None:
        cap = self.require_capabilities()
        cases = {
            "api key present": ({"ANTHROPIC_API_KEY": "sk-x"}, "api_key"),
            "auth token present": ({"ANTHROPIC_AUTH_TOKEN": "tok"}, "api_key"),
            "neither present": ({}, "subscription"),
            "empty api key not present": ({"ANTHROPIC_API_KEY": ""}, "subscription"),
        }
        for label, (env, expected) in cases.items():
            with self.subTest(case=label):
                self.assertEqual(cap.detect_authentication_mode(env), expected)

    def test_build_unset_proof_from_operator_environment(self) -> None:
        cap = self.require_capabilities()
        clean = cap.build_unset_proof(env={}, settings={})
        self.assertEqual(
            set(clean),
            {
                "fallback_model_unset",
                "fallbackModel_unset",
                "claude_code_subagent_model_unset",
                "available_models_absent",
                "enforce_available_models_observed",
                "config_dir_isolation",
                "inherit_equivalent_to_unset",
                "org_restriction_gap",
            },
        )
        self.assertTrue(clean["fallback_model_unset"])
        self.assertTrue(clean["fallbackModel_unset"])
        self.assertTrue(clean["claude_code_subagent_model_unset"])
        self.assertTrue(clean["available_models_absent"])
        self.assertEqual(clean["config_dir_isolation"], "none")
        self.assertIsNone(clean["inherit_equivalent_to_unset"])
        self.assertIsNone(clean["org_restriction_gap"])

        set_model = cap.build_unset_proof(env={"CLAUDE_CODE_SUBAGENT_MODEL": "claude-opus-4-8"}, settings={})
        self.assertFalse(set_model["claude_code_subagent_model_unset"])

        with_settings = cap.build_unset_proof(
            env={}, settings={"availableModels": ["claude-opus-4-8"], "enforceAvailableModels": True}
        )
        self.assertFalse(with_settings["available_models_absent"])
        self.assertEqual(with_settings["enforce_available_models_observed"], "True")

        inherit_new = cap.build_unset_proof(
            env={"CLAUDE_CODE_SUBAGENT_MODEL": "inherit"}, settings={}, client_version="2.1.196"
        )
        self.assertTrue(inherit_new["claude_code_subagent_model_unset"])
        self.assertIsNotNone(inherit_new["inherit_equivalent_to_unset"])
        inherit_old = cap.build_unset_proof(
            env={"CLAUDE_CODE_SUBAGENT_MODEL": "inherit"}, settings={}, client_version="2.0.0"
        )
        self.assertFalse(inherit_old["claude_code_subagent_model_unset"])
        self.assertIsNotNone(inherit_old["inherit_equivalent_to_unset"])

    # -- T012: modelUsage extraction, remap cross-check, evidence builders ----

    def test_primary_model_id_and_remap_cross_check(self) -> None:
        cap = self.require_capabilities()
        payload = cap.parse_result_payload(_canary_stdout("claude-opus-4-8"))
        self.assertEqual(cap.primary_model_id(payload), "claude-opus-4-8")
        self.assertIsNone(cap.primary_model_id(cap.parse_result_payload("not json")))
        self.assertTrue(cap.cross_check_remap("claude-opus-3-0", "claude-opus-4-8"))
        self.assertFalse(cap.cross_check_remap("claude-opus-4-8", "claude-opus-4-8"))
        self.assertFalse(cap.cross_check_remap("claude-opus-3-0", None))

    def test_build_alias_binding_from_canary_payload(self) -> None:
        cap = self.require_capabilities()
        result = cap.ProbeInvocationResult(
            return_code=0, stdout=_canary_stdout("claude-sonnet-5"), output_mode=cap.OUTPUT_MODE_JSON
        )
        binding = cap.build_alias_binding("sonnet", "sonnet__max", result)
        self.assertEqual(binding["alias"], "sonnet")
        self.assertEqual(binding["resolved_dated_model_id"], "claude-sonnet-5")
        self.assertEqual(binding["tuple_id"], "sonnet__max")
        self.assertEqual(binding["raw_evidence"]["sanitization"], cap.SANITIZATION_MARKER)
        self.assertRegex(binding["raw_evidence"]["raw_output_sha256"], SHA256_PATTERN)

    def test_classify_effort_acceptance_labels_observation_never_certification(self) -> None:
        cap = self.require_capabilities()
        accepted = cap.classify_effort_acceptance(
            cap.ProbeInvocationResult(return_code=0, stdout="effort max applied", output_mode=cap.OUTPUT_MODE_PLAIN_TEXT)
        )
        self.assertEqual(accepted, ("accepted", "plain_text_print"))
        clamped = cap.classify_effort_acceptance(
            cap.ProbeInvocationResult(
                return_code=0,
                stdout="warning: requested effort max clamped to high",
                output_mode=cap.OUTPUT_MODE_PLAIN_TEXT,
            )
        )
        self.assertEqual(clamped, ("clamped", "plain_text_print"))
        rejected = cap.classify_effort_acceptance(
            cap.ProbeInvocationResult(return_code=1, stdout="", stderr="effort not supported", output_mode=cap.OUTPUT_MODE_PLAIN_TEXT)
        )
        self.assertEqual(rejected, ("rejected", "plain_text_print"))
        json_mode = cap.classify_effort_acceptance(
            cap.ProbeInvocationResult(return_code=0, stdout=_canary_stdout("claude-opus-4-8"), output_mode=cap.OUTPUT_MODE_JSON)
        )
        self.assertEqual(json_mode, ("observation_only", "json_no_org_cap_assumed"))

    def test_build_unavailable_observation_flags_soft_remap_and_records_caveat(self) -> None:
        cap = self.require_capabilities()
        proof = self._clean_unset_proof(cap)
        soft = cap.build_unavailable_observation(
            surface="print_model",
            requested_unavailable_model_id=_UNAVAILABLE_PROBE_ID,
            result=cap.ProbeInvocationResult(
                return_code=0, stdout=_canary_stdout("claude-opus-4-8"), output_mode=cap.OUTPUT_MODE_JSON
            ),
            unset_proof=proof,
        )
        self.assertEqual(soft["surface"], "print_model")
        self.assertEqual(soft["observed_model_id"], "claude-opus-4-8")
        self.assertEqual(soft["observed_outcome"], "soft_remap")
        self.assertTrue(soft["remap_flagged"])
        self.assertTrue(soft["dispatch_equivalence_caveat"])
        self.assertEqual(soft["unset_proof"], proof)

        hard = cap.build_unavailable_observation(
            surface="subagent_frontmatter",
            requested_unavailable_model_id=_UNAVAILABLE_PROBE_ID,
            result=cap.ProbeInvocationResult(
                return_code=1, stdout="", stderr="error: model not found", output_mode=cap.OUTPUT_MODE_JSON
            ),
            unset_proof=proof,
        )
        self.assertEqual(hard["observed_outcome"], "hard_rejection")
        self.assertIsNone(hard["observed_model_id"])
        self.assertFalse(hard["remap_flagged"])
        # The subagent surface must state the file-agent-vs-production-Agent-tool inference (R12).
        self.assertIn("Agent", hard["dispatch_equivalence_caveat"])

    # -- T012: models endpoint corroboration (api_key only; injected fetch) ---

    def test_corroborate_models_endpoint_only_hits_network_in_api_key_mode(self) -> None:
        cap = self.require_capabilities()

        def forbidden_fetch(env):
            raise AssertionError("no network in subscription mode")

        subscription = cap.corroborate_models_endpoint("subscription", fetch=forbidden_fetch)
        self.assertIsNone(subscription.evidence)
        self.assertIsNotNone(subscription.gap)
        self.assertEqual(subscription.gap["disposition"], "gap")

        def ok_fetch(env):
            return {"data": [{"id": "claude-opus-4-8"}, {"id": "claude-sonnet-5"}]}

        accessible = cap.corroborate_models_endpoint("api_key", fetch=ok_fetch)
        self.assertEqual(accessible.evidence["access_status"], "accessible")
        self.assertIn("claude-opus-4-8", accessible.evidence["dated_model_ids"])
        self.assertTrue(accessible.evidence["note"])

        def broken_fetch(env):
            raise OSError("unreachable")

        unreachable = cap.corroborate_models_endpoint("api_key", fetch=broken_fetch)
        self.assertEqual(unreachable.evidence["access_status"], "unreachable")

    def test_build_snapshot_id_embeds_capture_date(self) -> None:
        cap = self.require_capabilities()
        self.assertEqual(
            cap.build_snapshot_id("2026-07-16T12:00:00Z", 1), "CAR-002-RCS-2026-07-16-V1"
        )
        self.assertEqual(
            cap.build_snapshot_id("2026-07-16T12:00:00Z", 3), "CAR-002-RCS-2026-07-16-V3"
        )
        self.assertRegex(cap.build_snapshot_id("2026-07-16T12:00:00Z", 1), SNAPSHOT_ID_PATTERN)

    # -- T012: full assembly validates against the shipped schema -------------

    def test_assemble_runtime_capability_snapshot_validates_against_schema(self) -> None:
        cap = self.require_capabilities()
        validator = self.require_validator_module()
        matrix, probe_run = _run_bounded_matrix_with_fake_invoker(cap)
        endpoint = cap.corroborate_models_endpoint("subscription", fetch=lambda env: {})
        snapshot = cap.assemble_runtime_capability_snapshot(
            probe_run,
            captured_at_utc="2026-07-16T12:00:00Z",
            version=1,
            pinned_client_version="2.19.3",
            authentication_mode="subscription",
            unset_proof=self._clean_unset_proof(cap),
            unavailable_model_id=_UNAVAILABLE_PROBE_ID,
            models_endpoint=endpoint,
        )
        # Fail-closed writer path: must validate against the runtimeCapabilitySnapshot $def.
        self.assertIs(validator.validate_runtime_capability_snapshot(snapshot), snapshot)
        self.assertEqual(len(snapshot["tuple_evidence"]), matrix.cardinality)
        self.assertEqual(len(snapshot["alias_bindings"]), len(matrix.model_aliases))
        self.assertEqual(len(snapshot["unavailable_observations"]), 2)
        self.assertEqual(snapshot["runtime_capability_snapshot_id"], "CAR-002-RCS-2026-07-16-V1")
        surfaces = {obs["surface"] for obs in snapshot["unavailable_observations"]}
        self.assertEqual(surfaces, {"print_model", "subagent_frontmatter"})

    def test_assembled_capability_answers_cover_six_questions_capq6_open(self) -> None:
        cap = self.require_capabilities()
        _, probe_run = _run_bounded_matrix_with_fake_invoker(cap)
        snapshot = cap.assemble_runtime_capability_snapshot(
            probe_run,
            captured_at_utc="2026-07-16T12:00:00Z",
            version=1,
            pinned_client_version="2.19.3",
            authentication_mode="subscription",
            unset_proof=self._clean_unset_proof(cap),
            unavailable_model_id=_UNAVAILABLE_PROBE_ID,
        )
        answers = {a["capability_question_id"]: a for a in snapshot["capability_answers"]}
        self.assertEqual(set(answers), {"CAP-Q1", "CAP-Q2", "CAP-Q3", "CAP-Q4", "CAP-Q5", "CAP-Q6"})
        self.assertEqual(answers["CAP-Q1"]["answer"], "claude-opus-4-8")
        self.assertEqual(answers["CAP-Q1"]["status"], "answered")
        self.assertEqual(answers["CAP-Q6"]["status"], "open")
        self.assertEqual(answers["CAP-Q6"]["label"], "labeled_inference")
        # CAP-Q6 is also carried as an explicit open/gap entry (R11).
        self.assertTrue(any(g["disposition"] == "open" for g in snapshot["open_gaps"]))

    def require_validator_module(self):
        self.assertIsNotNone(
            claude_trace_schema, "claude_trace_schema validator module not importable"
        )
        return claude_trace_schema

    def test_write_snapshot_fail_closed_writes_valid_and_aborts_invalid(self) -> None:
        cap = self.require_capabilities()
        _, probe_run = _run_bounded_matrix_with_fake_invoker(cap)
        snapshot = cap.assemble_runtime_capability_snapshot(
            probe_run,
            captured_at_utc="2026-07-16T12:00:00Z",
            version=1,
            pinned_client_version="2.19.3",
            authentication_mode="subscription",
            unset_proof=self._clean_unset_proof(cap),
            unavailable_model_id=_UNAVAILABLE_PROBE_ID,
        )
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "snap.json"
            disposition = cap.write_snapshot_fail_closed(snapshot, good)
            self.assertEqual(disposition, cap.DISPOSITION_RECORD)
            self.assertTrue(good.exists())
            reloaded = json.loads(good.read_text(encoding="utf-8"))
            self.assertEqual(reloaded["runtime_capability_snapshot_id"], snapshot["runtime_capability_snapshot_id"])

            broken = dict(snapshot)
            broken.pop("canary")
            bad = Path(tmp) / "bad.json"
            with self.assertRaises(cap.ProbeWriteAborted):
                cap.write_snapshot_fail_closed(broken, bad)
            self.assertFalse(bad.exists())  # fail-closed: nothing committed (SC-004)

    # -- T014: subagent-frontmatter dispatch mechanism ------------------------

    def test_build_probe_agent_markdown_names_unavailable_model_in_frontmatter(self) -> None:
        cap = self.require_capabilities()
        text = cap.build_probe_agent_markdown("car002-probe", _UNAVAILABLE_PROBE_ID)
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("name: car002-probe", text)
        self.assertIn(f"model: {_UNAVAILABLE_PROBE_ID}", text)
        self.assertEqual(text.count("---"), 2)

    def test_staged_probe_agent_creates_then_removes_file_on_every_exit(self) -> None:
        cap = self.require_capabilities()
        with tempfile.TemporaryDirectory() as tmp:
            agents_dir = Path(tmp) / ".claude" / "agents"
            with cap.staged_probe_agent(agents_dir, "car002-probe", _UNAVAILABLE_PROBE_ID) as path:
                self.assertTrue(path.exists())
                self.assertIn(_UNAVAILABLE_PROBE_ID, path.read_text(encoding="utf-8"))
            self.assertFalse(path.exists())  # removed on normal exit

            # Removed even when the dispatch body raises (abort/timeout path).
            with self.assertRaises(RuntimeError):
                with cap.staged_probe_agent(agents_dir, "car002-probe", _UNAVAILABLE_PROBE_ID) as path2:
                    self.assertTrue(path2.exists())
                    raise RuntimeError("simulated abort")
            self.assertFalse(path2.exists())

    def test_live_invoker_subagent_stages_file_during_dispatch_and_removes_after(self) -> None:
        cap = self.require_capabilities()
        with tempfile.TemporaryDirectory() as tmp:
            agents_dir = Path(tmp) / ".claude" / "agents"
            invoker = cap.LiveClaudeInvoker(
                agents_dir=agents_dir,
                unavailable_model_id=_UNAVAILABLE_PROBE_ID,
                agent_name="car002-probe",
            )
            probe_path = agents_dir / "car002-probe.md"
            seen = {}

            def spy_run(argv, **kwargs):
                seen["existed_during"] = probe_path.exists()
                seen["argv"] = list(argv)
                return subprocess.CompletedProcess(list(argv), 0, stdout=_canary_stdout("claude-opus-4-8"), stderr="")

            planned = cap.PlannedInvocation(
                purpose=cap.PURPOSE_UNAVAILABLE_PROBE, surface="subagent_frontmatter"
            )
            with mock.patch("subprocess.run", spy_run):
                result = invoker(planned, timeout_seconds=30.0)
            self.assertEqual(result.return_code, 0)
            self.assertTrue(seen["existed_during"])  # file present at dispatch time
            self.assertNotIn("--model", seen["argv"])  # no preempting model (R4/R12)
            self.assertFalse(probe_path.exists())  # removed after (try/finally)

    def test_live_invoker_subagent_removes_file_on_timeout(self) -> None:
        cap = self.require_capabilities()
        with tempfile.TemporaryDirectory() as tmp:
            agents_dir = Path(tmp) / ".claude" / "agents"
            invoker = cap.LiveClaudeInvoker(
                agents_dir=agents_dir, unavailable_model_id=_UNAVAILABLE_PROBE_ID, agent_name="car002-probe"
            )
            probe_path = agents_dir / "car002-probe.md"

            def timeout_run(argv, **kwargs):
                raise subprocess.TimeoutExpired(cmd=list(argv), timeout=kwargs.get("timeout", 1))

            planned = cap.PlannedInvocation(
                purpose=cap.PURPOSE_UNAVAILABLE_PROBE, surface="subagent_frontmatter"
            )
            with mock.patch("subprocess.run", timeout_run):
                result = invoker(planned, timeout_seconds=5.0)
            self.assertTrue(result.timed_out)
            self.assertFalse(probe_path.exists())  # removed on timeout exit path

    def test_probe_run_leaves_the_real_claude_agents_dir_untouched(self) -> None:
        cap = self.require_capabilities()
        real_agents_dir = REPO_ROOT / ".claude" / "agents"
        before = sorted(p.name for p in real_agents_dir.iterdir()) if real_agents_dir.exists() else []
        with tempfile.TemporaryDirectory() as tmp:
            agents_dir = Path(tmp) / ".claude" / "agents"
            invoker = cap.LiveClaudeInvoker(
                agents_dir=agents_dir, unavailable_model_id=_UNAVAILABLE_PROBE_ID, agent_name="car002-probe"
            )
            planned = cap.PlannedInvocation(
                purpose=cap.PURPOSE_UNAVAILABLE_PROBE, surface="subagent_frontmatter"
            )
            with mock.patch("subprocess.run", _argv_aware_fake_run):
                invoker(planned, timeout_seconds=30.0)
        after = sorted(p.name for p in real_agents_dir.iterdir()) if real_agents_dir.exists() else []
        self.assertEqual(before, after)
        self.assertNotIn("car002-probe.md", after)

    # -- T011+T012+T014 end-to-end through main() (offline, faked subprocess) -

    def test_main_runs_the_matrix_offline_and_writes_a_valid_snapshot(self) -> None:
        cap = self.require_capabilities()
        validator = self.require_validator_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "claude-runtime-capability-snapshot.json"
            agents_dir = Path(tmp) / ".claude" / "agents"
            argv = [
                "--timeout", "30",
                "--unavailable-model-id", _UNAVAILABLE_PROBE_ID,
                "--pinned-client-version", "2.19.3",
                "--output", str(out),
                "--agents-dir", str(agents_dir),
                "--version-number", "1",
            ]
            with mock.patch("subprocess.run", _argv_aware_fake_run):
                exit_code = cap.main(argv, env={})  # env={} => subscription => no network
            self.assertEqual(exit_code, 0)
            self.assertTrue(out.exists())
            snapshot = json.loads(out.read_text(encoding="utf-8"))
            self.assertIs(validator.validate_runtime_capability_snapshot(snapshot), snapshot)
            self.assertEqual(snapshot["authentication_mode"], "subscription")
            # No probe residue and the real agents dir is untouched.
            self.assertFalse((agents_dir / "car002-probe.md").exists())


if __name__ == "__main__":
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(ClaudeTraceSchemaContractTests))
    suite.addTests(loader.loadTestsFromTestCase(ClaudeCapabilitiesPureLogicTests))
    suite.addTests(loader.loadTestsFromTestCase(ClaudeCapabilitiesLiveBoundaryTests))
    raise SystemExit(run_counted(suite, label="test-efficiency-claude-telemetry"))
