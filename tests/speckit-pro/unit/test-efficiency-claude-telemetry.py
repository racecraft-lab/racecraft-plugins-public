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
from datetime import datetime, timezone
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


def _require_validator(test_case: unittest.TestCase):
    test_case.assertIsNotNone(
        claude_trace_schema,
        "claude_trace_schema validator module not importable (T005)",
    )
    return claude_trace_schema


RESEARCH_ROOT = REPO_ROOT / "docs" / "ai" / "research"
SCHEMA_PATH = RESEARCH_ROOT / "claude-trace-contract.schema.json"
MANIFEST_PATH = RESEARCH_ROOT / "claude-agent-route-candidate-manifest.json"
# The canonical committed runtime-capability snapshot (T015 operator deliverable),
# continuously validated on every run by CommittedRuntimeCapabilitySnapshotTests (T017).
SNAPSHOT_PATH = RESEARCH_ROOT / "claude-runtime-capability-snapshot.json"
# The committed WP2 telemetry capability profile (T019-T021) and the standalone
# route-resolution fixture (T022), continuously validated on every run (T023/T026).
PROFILE_PATH = RESEARCH_ROOT / "claude-telemetry-capability-profile.json"
TELEMETRY_RECORDS_DIR = TEST_ROOT / "unit" / "fixtures" / "claude-telemetry-records"
ROUTE_RESOLUTION_FIXTURE_PATH = TELEMETRY_RECORDS_DIR / "route-resolution.json"

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
PRIVACY_UUID = re.compile(
    r"[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}",
    re.IGNORECASE,
)

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
        "sanitization": "home_paths_and_session_ids_normalized_utf8",
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
        self.assertEqual(raw["properties"]["sanitization"], {"const": "home_paths_and_session_ids_normalized_utf8"})
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

    def test_sanitize_redacts_run_local_session_uuids(self) -> None:
        # Run-local session/request UUIDs in the raw payload carry no evidentiary
        # value and are redacted so the tree-wide privacy-scan UUID rule holds.
        # The UUID inputs are assembled from fragments so this file's source text
        # carries no literal UUID (which the privacy scan would itself flag).
        cap = self.require_capabilities()
        uuid_a = "-".join(("78b65992", "1a2b", "3c4d", "5e6f", "0011" + "22334455"))
        uuid_b = "-".join(("E034F23D", "AAAA", "4BBB", "8CCC", "DDDDEEEE" + "FFFF"))
        raw = f'{{"session_id":"{uuid_a}","uuid":"{uuid_b}"}}'
        self.assertIsNotNone(PRIVACY_UUID.search(raw))  # inputs really are UUIDs
        sanitized = cap.sanitize_home_paths(raw)
        self.assertIsNone(PRIVACY_UUID.search(sanitized))
        self.assertEqual(sanitized.count("<session-id>"), 2)
        self.assertEqual(cap.SANITIZATION_MARKER, "home_paths_and_session_ids_normalized_utf8")

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


def _run_bounded_matrix_with_one_unparseable_canary(cap, *, broken_alias="opus"):
    """Drive the REAL bounded matrix but return an UNPARSEABLE ``--output-format
    json`` payload (a truncated JSON body) for one alias canary. Every other
    invocation is a clean parseable observation, so the ONLY fail-closed trigger
    is the malformed JSON payload (spec "Malformed probe payload"). Returns
    ``(matrix, ProbeRun)`` — the driver records it because a syntactically-broken
    payload is not a transport failure."""
    matrix = cap.build_probe_matrix()
    plan = cap.plan_probe_invocations(matrix)

    def invoke(item, *, timeout_seconds):
        if item.purpose == cap.PURPOSE_ALIAS_CANARY:
            if item.model_alias == broken_alias:
                return cap.ProbeInvocationResult(
                    return_code=0,
                    stdout='{"type":"result","modelUsage":{',  # truncated => json.loads raises
                    output_mode=cap.OUTPUT_MODE_JSON,
                )
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


def _subagent_parent_narrated_reject_stdout(
    requested_id=_UNAVAILABLE_PROBE_ID, parent_model="claude-fable-5"
):
    """A ``subagent_frontmatter`` ``--output-format json`` payload in which the
    PARENT ``-p`` session (running on ``parent_model``) SUCCEEDED and merely
    NARRATES the dispatched subagent's terminal model-access failure for
    ``requested_id``. Mirrors the committed CAR-002 subagent evidence: the
    top-level ``modelUsage`` is the PARENT's model and must NOT be read as the
    subagent's observed model (FR-026 / root-cause LOW-2)."""
    return json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "api_error_status": None,
            "result": (
                "The probe agent could not run: it terminated immediately with an API "
                f"error - its configured model `{requested_id}` doesn't exist or isn't "
                "accessible, so no reply was produced. Dispatching a subagent pinned to an "
                "unavailable model fails at spawn time with a terminal model-access error "
                "rather than falling back to another model."
            ),
            "modelUsage": {
                parent_model: {"inputTokens": 4, "outputTokens": 83, "contextWindow": 1000000}
            },
            "num_turns": 2,
            "terminal_reason": "completed",
        }
    )


def _subagent_parent_narrated_success_stdout(parent_model="claude-fable-5"):
    """A ``subagent_frontmatter`` payload where the PARENT session succeeded and
    narrates a non-error outcome that does NOT name the subagent's model — the
    subagent outcome is NOT derivable from the parent narration (undetermined).
    The top-level ``modelUsage`` is again the PARENT's model."""
    return json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "api_error_status": None,
            "result": "The dispatched agent replied: ok.",
            "modelUsage": {
                parent_model: {"inputTokens": 4, "outputTokens": 5, "contextWindow": 1000000}
            },
            "num_turns": 2,
            "terminal_reason": "completed",
        }
    )


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

        # --fallback-model (CLI flag) and fallbackModel (settings key) are distinct
        # surfaces proven from distinct sources — a fallbackModel setting must NOT
        # drive the CLI-flag proof, and a --fallback-model argv must NOT be masked
        # by clean settings.
        settings_only = cap.build_unset_proof(env={}, settings={"fallbackModel": "claude-opus-4-8"})
        self.assertTrue(settings_only["fallback_model_unset"])   # no --fallback-model argv
        self.assertFalse(settings_only["fallbackModel_unset"])   # fallbackModel setting present
        argv_flag = cap.build_unset_proof(
            env={}, settings={},
            probe_argvs=[["claude", "-p", "hi", "--model", "opus"],
                         ["claude", "-p", "hi", "--fallback-model", "sonnet"]],
        )
        self.assertFalse(argv_flag["fallback_model_unset"])      # --fallback-model in a real argv
        self.assertTrue(argv_flag["fallbackModel_unset"])        # settings key still absent
        argv_clean = cap.build_unset_proof(
            env={}, settings={}, probe_argvs=[["claude", "-p", "hi", "--model", "opus"]]
        )
        self.assertTrue(argv_clean["fallback_model_unset"])

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

    # -- MEDIUM-2 (root cause LOW-2): the subagent surface must NEVER read the
    # PARENT session's top-level modelUsage as the subagent's observed model. On
    # the committed evidence the parent ran on claude-fable-5 and merely NARRATED
    # the subagent's terminal model-access rejection of claude-opus-3-0; the old
    # code recorded soft_remap / claude-fable-5 / remap_flagged=true — a false
    # remap/availability signal (FR-026; "Interfering configuration fires despite
    # unset-proof"), on an answer CAR-003..CAR-011 consume.

    def test_subagent_surface_hard_rejects_parent_narrated_model_access_error(self) -> None:
        cap = self.require_capabilities()
        proof = self._clean_unset_proof(cap)
        obs = cap.build_unavailable_observation(
            surface="subagent_frontmatter",
            requested_unavailable_model_id=_UNAVAILABLE_PROBE_ID,
            result=cap.ProbeInvocationResult(
                return_code=0,
                stdout=_subagent_parent_narrated_reject_stdout(parent_model="claude-fable-5"),
                output_mode=cap.OUTPUT_MODE_JSON,
            ),
            unset_proof=proof,
        )
        # The subagent never ran => a HARD rejection at the subagent boundary.
        self.assertEqual(obs["observed_outcome"], "hard_rejection")
        self.assertIsNone(obs["observed_model_id"])
        self.assertFalse(obs["remap_flagged"])
        # Prove the OLD bug is caught: never the parent's model, never soft_remap.
        self.assertNotEqual(obs["observed_outcome"], "soft_remap")
        self.assertNotEqual(obs["observed_model_id"], "claude-fable-5")

    def test_subagent_surface_undetermined_when_outcome_not_derivable(self) -> None:
        cap = self.require_capabilities()
        proof = self._clean_unset_proof(cap)
        obs = cap.build_unavailable_observation(
            surface="subagent_frontmatter",
            requested_unavailable_model_id=_UNAVAILABLE_PROBE_ID,
            result=cap.ProbeInvocationResult(
                return_code=0,
                stdout=_subagent_parent_narrated_success_stdout(parent_model="claude-fable-5"),
                output_mode=cap.OUTPUT_MODE_JSON,
            ),
            unset_proof=proof,
        )
        # Parent success with no terminal error and no subagent-scoped model signal
        # => undetermined; the parent's fable model is NEVER borrowed.
        self.assertEqual(obs["observed_outcome"], "undetermined")
        self.assertIsNone(obs["observed_model_id"])
        self.assertFalse(obs["remap_flagged"])
        self.assertNotEqual(obs["observed_model_id"], "claude-fable-5")

    def test_classify_subagent_unavailable_outcome_three_documented_paths(self) -> None:
        cap = self.require_capabilities()
        # (a) hard rejection: parent narrates a terminal model-access error and the
        # subagent never ran => hard_rejection / null, never the parent model.
        hard = cap.classify_subagent_unavailable_outcome(
            cap.ProbeInvocationResult(
                return_code=0,
                stdout=_subagent_parent_narrated_reject_stdout(parent_model="claude-fable-5"),
                output_mode=cap.OUTPUT_MODE_JSON,
            ),
            requested_id=_UNAVAILABLE_PROBE_ID,
        )
        self.assertEqual(hard, ("hard_rejection", None))

        # (b) genuine substitution: ONLY the subagent's OWN observed model (never
        # the parent's top-level modelUsage) may establish a soft remap.
        soft = cap.classify_subagent_unavailable_outcome(
            cap.ProbeInvocationResult(
                return_code=0,
                stdout=_subagent_parent_narrated_success_stdout(parent_model="claude-fable-5"),
                output_mode=cap.OUTPUT_MODE_JSON,
            ),
            requested_id=_UNAVAILABLE_PROBE_ID,
            subagent_observed_model_id="claude-sonnet-5",
        )
        self.assertEqual(soft, ("soft_remap", "claude-sonnet-5"))
        self.assertNotEqual(soft[1], "claude-fable-5")  # never the parent's model

        # (c) undetermined: parent success, no terminal error, no subagent-scoped
        # model => the parent narration does not determine the subagent outcome.
        undet = cap.classify_subagent_unavailable_outcome(
            cap.ProbeInvocationResult(
                return_code=0,
                stdout=_subagent_parent_narrated_success_stdout(parent_model="claude-fable-5"),
                output_mode=cap.OUTPUT_MODE_JSON,
            ),
            requested_id=_UNAVAILABLE_PROBE_ID,
        )
        self.assertEqual(undet, ("undetermined", None))

        # A non-zero parent exit carrying an error body is also a hard rejection
        # (keeps the print_model-style direct-rejection reading; R4/R12).
        hard_nonzero = cap.classify_subagent_unavailable_outcome(
            cap.ProbeInvocationResult(
                return_code=1,
                stdout="",
                stderr="error: model not found",
                output_mode=cap.OUTPUT_MODE_JSON,
            ),
            requested_id=_UNAVAILABLE_PROBE_ID,
        )
        self.assertEqual(hard_nonzero, ("hard_rejection", None))

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

    # -- MEDIUM-1: the fail-closed dispositions gate the assemble/write path. An
    # UNPARSEABLE `--output-format json` payload is disposition (1) abort_write:
    # the snapshot write aborts BEFORE any file is written or overwritten (spec
    # "Malformed probe payload" / "Partial probe matrix" (1); FR-023). The old
    # code routed it through parse->None->null binding (schema-valid) and wrote it.

    def test_assemble_aborts_write_on_unparseable_json_payload_writes_no_file(self) -> None:
        cap = self.require_capabilities()
        _, bad_run = _run_bounded_matrix_with_one_unparseable_canary(cap)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "snap.json"
            with self.assertRaises(cap.ProbeWriteAborted):
                snapshot = cap.assemble_runtime_capability_snapshot(
                    bad_run,
                    captured_at_utc="2026-07-16T12:00:00Z",
                    version=1,
                    pinned_client_version="2.19.3",
                    authentication_mode="subscription",
                    unset_proof=self._clean_unset_proof(cap),
                    unavailable_model_id=_UNAVAILABLE_PROBE_ID,
                )
                cap.write_snapshot_fail_closed(snapshot, out)
            self.assertFalse(out.exists())  # fail-closed: nothing written/overwritten

    def test_assemble_writes_a_valid_run_positive_control(self) -> None:
        cap = self.require_capabilities()
        validator = self.require_validator_module()
        _, good_run = _run_bounded_matrix_with_fake_invoker(cap)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "snap.json"
            snapshot = cap.assemble_runtime_capability_snapshot(
                good_run,
                captured_at_utc="2026-07-16T12:00:00Z",
                version=1,
                pinned_client_version="2.19.3",
                authentication_mode="subscription",
                unset_proof=self._clean_unset_proof(cap),
                unavailable_model_id=_UNAVAILABLE_PROBE_ID,
            )
            self.assertIs(validator.validate_runtime_capability_snapshot(snapshot), snapshot)
            self.assertEqual(cap.write_snapshot_fail_closed(snapshot, out), cap.DISPOSITION_RECORD)
            self.assertTrue(out.exists())

    def test_gate_probe_run_dispositions_maps_each_disposition(self) -> None:
        cap = self.require_capabilities()
        planned = cap.PlannedInvocation(purpose=cap.PURPOSE_ALIAS_CANARY, model_alias="opus")
        bad_run = cap.ProbeRun(
            metadata={},
            results=(
                (
                    planned,
                    cap.ProbeInvocationResult(
                        return_code=0, stdout="not valid json {", output_mode=cap.OUTPUT_MODE_JSON
                    ),
                ),
            ),
        )
        with self.assertRaises(cap.ProbeWriteAborted):
            cap.gate_probe_run_dispositions(bad_run)

        # Parseable JSON canaries + plain-text config observations => all record.
        _, good_run = _run_bounded_matrix_with_fake_invoker(cap)
        self.assertIsNone(cap.gate_probe_run_dispositions(good_run))

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


# -- T017: committed runtime-capability snapshot — continuous validation ------
# FR-011 / SC-002: the one committed operator snapshot is re-validated on every
# run. Each rule below is a pure check that raises AssertionError on violation, so
# the same logic backs both the positive assertion (committed snapshot passes) and
# the teeth test (a deliberately-corrupted in-memory copy fails) — making an
# otherwise-characterization "it already validates" green meaningful.

EXPECTED_ALIAS_SET = frozenset({"opus", "sonnet", "haiku", "fable"})
_SNAPSHOT_ID_IDENTITY_RE = re.compile(r"^CAR-002-RCS-(\d{4}-\d{2}-\d{2})-V(\d+)$")


def utc_calendar_date(timestamp: str) -> str:
    """Calendar date ``YYYY-MM-DD`` of a UTC instant (the validator guarantees a
    ``Z``-suffixed, zero-offset ``captured_at_utc``)."""
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc).date().isoformat()


def check_snapshot_id_identity(snapshot: dict) -> None:
    """FR-011: the date embedded in ``runtime_capability_snapshot_id`` equals the
    UTC date of ``captured_at_utc`` and the ``V<n>`` suffix is a positive integer."""
    snapshot_id = snapshot["runtime_capability_snapshot_id"]
    match = _SNAPSHOT_ID_IDENTITY_RE.fullmatch(snapshot_id)
    if match is None:
        raise AssertionError(f"snapshot id is not well-formed: {snapshot_id!r}")
    embedded_date, version_token = match.group(1), match.group(2)
    capture_date = utc_calendar_date(snapshot["captured_at_utc"])
    if embedded_date != capture_date:
        raise AssertionError(
            f"id date {embedded_date!r} != captured_at_utc UTC date {capture_date!r}"
        )
    if int(version_token) < 1:
        raise AssertionError(f"V<n> suffix is not a positive integer: V{version_token}")


def check_alias_bindings_cover_four(snapshot: dict) -> None:
    """FR-011 coverage: ``alias_bindings`` cover exactly opus/sonnet/haiku/fable,
    with no duplicate alias."""
    aliases = [binding["alias"] for binding in snapshot["alias_bindings"]]
    if len(aliases) != len(set(aliases)):
        raise AssertionError(f"duplicate alias bindings: {aliases}")
    if set(aliases) != set(EXPECTED_ALIAS_SET):
        raise AssertionError(
            f"alias set {sorted(set(aliases))} != {sorted(EXPECTED_ALIAS_SET)}"
        )


def check_tuple_evidence_has_six(snapshot: dict) -> None:
    """FR-011 coverage: ``tuple_evidence`` holds exactly the six deduped
    ``(model, effort)`` tuple_ids, with no duplicate."""
    tuple_ids = [evidence["tuple_id"] for evidence in snapshot["tuple_evidence"]]
    if len(tuple_ids) != len(set(tuple_ids)):
        raise AssertionError(f"duplicate tuple_evidence ids: {tuple_ids}")
    if set(tuple_ids) != set(EXPECTED_TUPLE_IDS):
        raise AssertionError(
            f"tuple_id set {sorted(set(tuple_ids))} != {sorted(EXPECTED_TUPLE_IDS)}"
        )


class CommittedRuntimeCapabilitySnapshotTests(unittest.TestCase):
    """The committed operator snapshot at
    ``docs/ai/research/claude-runtime-capability-snapshot.json`` is continuously
    re-validated on every run (FR-011, SC-002): it conforms to the
    ``runtimeCapabilitySnapshot`` ``$def``, its ID identity holds, and its
    alias/tuple coverage is exact. Each check is teeth-verified against a
    deliberately-corrupted in-memory copy so the green is meaningful and not a
    vacuous characterization pass.
    """

    require_validator = _require_validator

    def load_committed_snapshot(self) -> dict:
        # Loaded fresh per call so a test may mutate its copy without leaking.
        self.assertTrue(
            SNAPSHOT_PATH.is_file(),
            f"committed runtime-capability snapshot missing (T015): {SNAPSHOT_PATH}",
        )
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

    # (a) fail-closed schema validation of the committed snapshot -------------

    def test_committed_snapshot_validates_against_the_schema(self) -> None:
        validator = self.require_validator()
        snapshot = self.load_committed_snapshot()
        self.assertIs(
            validator.validate_runtime_capability_snapshot(snapshot), snapshot
        )

    def test_committed_snapshot_validation_rejects_corrupted_copies(self) -> None:
        validator = self.require_validator()
        error = validator.ClaudeTraceContractError
        mutations = {
            "drop required canary": lambda r: r.pop("canary"),
            "wrong schema_version const": lambda r: r.__setitem__("schema_version", "2.0.0"),
            "malformed snapshot id": lambda r: r.__setitem__(
                "runtime_capability_snapshot_id", "RCS-not-valid"
            ),
            "captured_at not UTC-Z": lambda r: r.__setitem__(
                "captured_at_utc", "2026-07-17 08:20:26"
            ),
            "empty tuple_evidence": lambda r: r.__setitem__("tuple_evidence", []),
        }
        for label, mutate in mutations.items():
            with self.subTest(mutation=label):
                snapshot = self.load_committed_snapshot()
                mutate(snapshot)
                with self.assertRaises(error):
                    validator.validate_runtime_capability_snapshot(snapshot)

    # (b) FR-011 identity: id-embedded date == captured UTC date; V<n> positive

    def test_committed_snapshot_id_identity_holds(self) -> None:
        snapshot = self.load_committed_snapshot()
        check_snapshot_id_identity(snapshot)  # raises on any FR-011 violation
        match = _SNAPSHOT_ID_IDENTITY_RE.fullmatch(
            snapshot["runtime_capability_snapshot_id"]
        )
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), utc_calendar_date(snapshot["captured_at_utc"]))
        self.assertGreaterEqual(int(match.group(2)), 1)

    def test_id_identity_check_has_teeth(self) -> None:
        # Each corruption keeps the id schema-well-formed (so the validator alone
        # would NOT catch most of these) yet violates FR-011 identity — proving the
        # dedicated check adds real coverage.
        cases = {
            "id date one day ahead of capture": lambda r: r.__setitem__(
                "runtime_capability_snapshot_id", "CAR-002-RCS-2026-07-18-V1"
            ),
            "id date one day behind capture": lambda r: r.__setitem__(
                "runtime_capability_snapshot_id", "CAR-002-RCS-2026-07-16-V1"
            ),
            "captured_at shifted off the id date": lambda r: r.__setitem__(
                "captured_at_utc", "2026-08-01T08:20:26Z"
            ),
            "non-positive V0 (schema-valid, identity-invalid)": lambda r: r.__setitem__(
                "runtime_capability_snapshot_id", "CAR-002-RCS-2026-07-17-V0"
            ),
            "non-numeric V suffix": lambda r: r.__setitem__(
                "runtime_capability_snapshot_id", "CAR-002-RCS-2026-07-17-VX"
            ),
        }
        for label, mutate in cases.items():
            with self.subTest(corruption=label):
                snapshot = self.load_committed_snapshot()
                mutate(snapshot)
                with self.assertRaises(AssertionError):
                    check_snapshot_id_identity(snapshot)

    # (c) alias bindings cover exactly the four aliases -----------------------

    def test_committed_snapshot_alias_bindings_cover_exactly_four(self) -> None:
        snapshot = self.load_committed_snapshot()
        check_alias_bindings_cover_four(snapshot)
        self.assertEqual(
            {binding["alias"] for binding in snapshot["alias_bindings"]},
            set(EXPECTED_ALIAS_SET),
        )

    def test_alias_coverage_check_has_teeth(self) -> None:
        cases = {
            "missing an alias": lambda r: r.__setitem__(
                "alias_bindings", r["alias_bindings"][:3]
            ),
            "unexpected extra alias": lambda r: r["alias_bindings"].append(
                {"alias": "ultra"}
            ),
            "duplicate alias": lambda r: r["alias_bindings"].append(
                {"alias": r["alias_bindings"][0]["alias"]}
            ),
        }
        for label, mutate in cases.items():
            with self.subTest(corruption=label):
                snapshot = self.load_committed_snapshot()
                mutate(snapshot)
                with self.assertRaises(AssertionError):
                    check_alias_bindings_cover_four(snapshot)

    # (d) tuple_evidence holds exactly the six expected tuple_ids --------------

    def test_committed_snapshot_tuple_evidence_has_the_six_tuples(self) -> None:
        snapshot = self.load_committed_snapshot()
        check_tuple_evidence_has_six(snapshot)
        self.assertEqual(
            {evidence["tuple_id"] for evidence in snapshot["tuple_evidence"]},
            set(EXPECTED_TUPLE_IDS),
        )
        self.assertEqual(len(snapshot["tuple_evidence"]), len(EXPECTED_TUPLE_IDS))

    def test_tuple_evidence_check_has_teeth(self) -> None:
        cases = {
            "missing a tuple": lambda r: r.__setitem__(
                "tuple_evidence", r["tuple_evidence"][:5]
            ),
            "unexpected extra tuple": lambda r: r["tuple_evidence"].append(
                {"tuple_id": "opus__low"}
            ),
            "duplicate tuple": lambda r: r["tuple_evidence"].append(
                {"tuple_id": r["tuple_evidence"][0]["tuple_id"]}
            ),
        }
        for label, mutate in cases.items():
            with self.subTest(corruption=label):
                snapshot = self.load_committed_snapshot()
                mutate(snapshot)
                with self.assertRaises(AssertionError):
                    check_tuple_evidence_has_six(snapshot)


# -- T019-T024 (WP2): committed telemetry profile, route-resolution fixture, and
# the exact-treatment telemetry-linkage rule — continuously validated every run.
# Each rule is a pure check raising AssertionError on violation, so the same logic
# backs both the positive assertion (committed artifact passes) and the teeth test
# (a deliberately-corrupted in-memory copy fails), making the green meaningful.

CLASSIFICATION_LABELS = frozenset(
    {"stable_native", "derived", "derived_from_controlled_configuration", "unavailable"}
)

# FR-019 mandated minimums. The effective model is read from the ``modelUsage`` key
# set (there is no scalar ``model`` field) and is ``stable_native`` per AC-2.4 / the
# roadmap verbatim — NOT ``derived`` (spec.md FR-019 traceability revision note).
EFFECTIVE_MODEL_FIELD = "modelUsage.<model>"
FR019_STABLE_NATIVE_FIELDS = frozenset(
    {
        "usage.input_tokens",
        "usage.output_tokens",
        "usage.cache_read_input_tokens",
        "usage.cache_creation.ephemeral_5m_input_tokens",
        "usage.cache_creation.ephemeral_1h_input_tokens",
        "usage.cache_creation_input_tokens",
        "num_turns",
        "duration_ms",
        EFFECTIVE_MODEL_FIELD,
        "modelUsage.<model>.inputTokens",
        "modelUsage.<model>.outputTokens",
        "modelUsage.<model>.cacheReadInputTokens",
        "modelUsage.<model>.cacheCreationInputTokens",
        "modelUsage.<model>.contextWindow",
    }
)
FR019_DERIVED_FIELDS = frozenset({"total_cost_usd", "modelUsage.<model>.costUSD"})
FR019_EFFORT_FIELD = "effective_reasoning_effort"

FR021_ROUTE_RESOLUTION_BINDINGS = (
    "agent_contract_id",
    "candidate_route_id",
    "runtime_capability_snapshot_id",
    "requested_model_alias",
    "resolved_dated_model_id",
    "effort_level",
    "instruction_sha256",
    "mutation_contract",
    "dispatch_namespace",
    "parent_session_configuration",
    "client_version",
    "fast_mode_state",
    "env_override_proof",
    "fallback_index",
    "fallback_reason",
    "tuple_id",
)


def _read_committed_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _relabel_field(profile: dict, field: str, classification: str) -> None:
    for entry in profile["field_classifications"]:
        if entry["field"] == field:
            entry["classification"] = classification
            return
    raise LookupError(f"test setup error: field {field!r} not in committed profile")


def _manifest_candidate_routes() -> dict:
    manifest = _read_committed_json(MANIFEST_PATH)
    return {route["candidate_route_id"]: route for route in manifest["candidate_routes"]}


def check_profile_exactly_one_classification(profile: dict) -> None:
    """SC-006: every telemetry field carries exactly one of the four classification
    labels, and no field is classified twice."""
    classifications = profile["field_classifications"]
    if not classifications:
        raise AssertionError("field_classifications is empty (SC-006 100% coverage)")
    fields = [entry["field"] for entry in classifications]
    if len(fields) != len(set(fields)):
        dupes = sorted({field for field in fields if fields.count(field) > 1})
        raise AssertionError(f"field(s) classified more than once: {dupes}")
    for entry in classifications:
        if entry["classification"] not in CLASSIFICATION_LABELS:
            raise AssertionError(
                f"{entry['field']!r}: {entry['classification']!r} is not one of the four labels"
            )


def check_profile_preserves_nulls(profile: dict) -> None:
    """FR-020/SC-006: unobserved fields are present with ``observed_value`` null and
    still classified — 'unavailable' is distinguishable from 'absent'. At least one
    preserved null must exist and every null field must still be classified."""
    null_entries = [
        entry for entry in profile["field_classifications"] if entry["observed_value"] is None
    ]
    if not null_entries:
        raise AssertionError(
            "no observed_value:null field present — nulls-preserved guarantee undemonstrated"
        )
    for entry in null_entries:
        if entry["classification"] not in CLASSIFICATION_LABELS:
            raise AssertionError(f"null field {entry['field']!r} dropped its classification")


def check_profile_meets_fr019_minimums(profile: dict) -> None:
    """FR-019: the mandated classifications, including the effective model as
    ``stable_native`` (NOT ``derived`` — traceability revision note)."""
    by_field = {
        entry["field"]: entry["classification"] for entry in profile["field_classifications"]
    }
    for field in FR019_STABLE_NATIVE_FIELDS:
        if by_field.get(field) != "stable_native":
            raise AssertionError(
                f"{field!r}: expected stable_native, got {by_field.get(field)!r}"
            )
    for field in FR019_DERIVED_FIELDS:
        if by_field.get(field) != "derived":
            raise AssertionError(f"{field!r}: expected derived, got {by_field.get(field)!r}")
    if by_field.get(FR019_EFFORT_FIELD) != "derived_from_controlled_configuration":
        raise AssertionError(
            f"{FR019_EFFORT_FIELD!r}: expected derived_from_controlled_configuration, "
            f"got {by_field.get(FR019_EFFORT_FIELD)!r}"
        )


def check_profile_grounds_in_committed_snapshot(profile: dict) -> None:
    """FR-018: the profile records the pinned client version in a field (not the id)
    and cross-references the committed snapshot's real id."""
    snapshot = _read_committed_json(SNAPSHOT_PATH)
    if profile["runtime_capability_snapshot_id"] != snapshot["runtime_capability_snapshot_id"]:
        raise AssertionError(
            f"profile cross-ref {profile['runtime_capability_snapshot_id']!r} != committed "
            f"snapshot id {snapshot['runtime_capability_snapshot_id']!r}"
        )
    if not profile["pinned_client_version"]:
        raise AssertionError("pinned_client_version must be a recorded non-empty field (FR-018)")


def check_route_resolution_binds_all_fr021_fields(record: dict) -> None:
    """FR-021: every binding present; ``dispatch_namespace`` a non-empty string;
    ``fallback_index``/``fallback_reason`` null under CAR-002's unset-proof."""
    for field in FR021_ROUTE_RESOLUTION_BINDINGS:
        if field not in record:
            raise AssertionError(f"route_resolution missing FR-021 binding {field!r}")
    if not isinstance(record["dispatch_namespace"], str) or not record["dispatch_namespace"]:
        raise AssertionError("dispatch_namespace must be a non-empty string (roadmap binding)")
    if record["fallback_index"] is not None or record["fallback_reason"] is not None:
        raise AssertionError(
            "fallback_index/fallback_reason must be null under CAR-002's unset-proof"
        )


def check_route_resolution_crossrefs_resolve(record: dict) -> None:
    """SC-008 / CAR-003 handoff (quickstart Part C): the fixture's cross-reference
    IDs resolve against committed bytes with no re-probing — ``candidate_route_id``
    + ``agent_contract_id`` are a real CAR-001 manifest pair and
    ``runtime_capability_snapshot_id`` matches the committed snapshot."""
    routes = _manifest_candidate_routes()
    candidate = record["candidate_route_id"]
    if candidate not in routes:
        raise AssertionError(
            f"candidate_route_id {candidate!r} absent from committed CAR-001 manifest"
        )
    manifest_contract = routes[candidate]["agent_contract_id"]
    if manifest_contract != record["agent_contract_id"]:
        raise AssertionError(
            f"agent_contract_id {record['agent_contract_id']!r} != manifest pair "
            f"{manifest_contract!r} for {candidate!r}"
        )
    snapshot = _read_committed_json(SNAPSHOT_PATH)
    if record["runtime_capability_snapshot_id"] != snapshot["runtime_capability_snapshot_id"]:
        raise AssertionError(
            f"snapshot cross-ref {record['runtime_capability_snapshot_id']!r} != committed "
            f"snapshot id {snapshot['runtime_capability_snapshot_id']!r}"
        )


def check_telemetry_ref_resolves(replay: dict, profile: dict) -> None:
    """FR-022: a non-null ``outcome.telemetry_ref`` MUST resolve against the
    telemetry-profile field set; a dangling reference fails validation."""
    telemetry_ref = replay["outcome"]["telemetry_ref"]
    if telemetry_ref is None:
        return
    field_set = {entry["field"] for entry in profile["field_classifications"]}
    if telemetry_ref not in field_set:
        raise AssertionError(
            f"dangling telemetry_ref {telemetry_ref!r}: not in the telemetry-profile field set"
        )


class _CommittedTelemetryProfileFixture:
    def load_committed_profile(self) -> dict:
        self.assertTrue(
            PROFILE_PATH.is_file(),
            f"committed telemetry capability profile missing (T019): {PROFILE_PATH}",
        )
        return _read_committed_json(PROFILE_PATH)


class CommittedTelemetryProfileTests(_CommittedTelemetryProfileFixture, unittest.TestCase):
    """The committed WP2 telemetry capability profile at
    ``docs/ai/research/claude-telemetry-capability-profile.json`` is continuously
    re-validated (T019-T021/T023): it conforms to the ``telemetryProfile`` ``$def``,
    every field carries exactly one classification (SC-006), nulls are preserved
    (FR-020), and the FR-019 minimums hold (the effective model is ``stable_native``,
    not ``derived``). Every check is teeth-verified against a corrupted copy.
    """

    require_validator = _require_validator

    def test_committed_profile_validates_against_the_schema(self) -> None:
        validator = self.require_validator()
        profile = self.load_committed_profile()
        self.assertIs(validator.validate_telemetry_profile(profile), profile)

    def test_committed_profile_validation_rejects_corrupted_copies(self) -> None:
        validator = self.require_validator()
        error = validator.ClaudeTraceContractError
        mutations = {
            "drop field_classifications": lambda r: r.pop("field_classifications"),
            "wrong schema_version const": lambda r: r.__setitem__("schema_version", "2.0.0"),
            "malformed telemetry_profile_id": lambda r: r.__setitem__(
                "telemetry_profile_id", "CAR-002-TP-bad"
            ),
            "snapshot cross-ref not a snapshot id": lambda r: r.__setitem__(
                "runtime_capability_snapshot_id", r["telemetry_profile_id"]
            ),
            "bad classification enum": lambda r: r["field_classifications"][0].__setitem__(
                "classification", "made_up"
            ),
            "additional property": lambda r: r.__setitem__("extra", 1),
        }
        for label, mutate in mutations.items():
            with self.subTest(mutation=label):
                profile = self.load_committed_profile()
                mutate(profile)
                with self.assertRaises(error):
                    validator.validate_telemetry_profile(profile)

    def test_committed_profile_carries_exactly_one_classification(self) -> None:
        check_profile_exactly_one_classification(self.load_committed_profile())

    def test_exactly_one_classification_check_has_teeth(self) -> None:
        cases = {
            "duplicate field entry": lambda r: r["field_classifications"].append(
                dict(r["field_classifications"][0])
            ),
            "classification outside the four labels": lambda r: r["field_classifications"][
                0
            ].__setitem__("classification", "sometimes_native"),
            "empty field_classifications": lambda r: r.__setitem__("field_classifications", []),
        }
        for label, mutate in cases.items():
            with self.subTest(corruption=label):
                profile = self.load_committed_profile()
                mutate(profile)
                with self.assertRaises(AssertionError):
                    check_profile_exactly_one_classification(profile)

    def test_committed_profile_preserves_null_valued_fields(self) -> None:
        check_profile_preserves_nulls(self.load_committed_profile())

    def test_nulls_preserved_check_has_teeth(self) -> None:
        # Dropping every null-valued field (so 'unavailable' becomes indistinguishable
        # from 'absent') must fail the guarantee.
        profile = self.load_committed_profile()
        profile["field_classifications"] = [
            entry
            for entry in profile["field_classifications"]
            if entry["observed_value"] is not None
        ]
        with self.assertRaises(AssertionError):
            check_profile_preserves_nulls(profile)

    def test_committed_profile_meets_fr019_minimums(self) -> None:
        check_profile_meets_fr019_minimums(self.load_committed_profile())

    def test_fr019_minimums_check_has_teeth(self) -> None:
        cases = {
            # The exact revision-note trap: effective model mislabeled derived.
            "effective model mislabeled derived": lambda r: _relabel_field(
                r, EFFECTIVE_MODEL_FIELD, "derived"
            ),
            "raw token field mislabeled derived": lambda r: _relabel_field(
                r, "usage.input_tokens", "derived"
            ),
            "cost field mislabeled stable_native": lambda r: _relabel_field(
                r, "total_cost_usd", "stable_native"
            ),
            "effort field mislabeled stable_native": lambda r: _relabel_field(
                r, FR019_EFFORT_FIELD, "stable_native"
            ),
        }
        for label, mutate in cases.items():
            with self.subTest(corruption=label):
                profile = self.load_committed_profile()
                mutate(profile)
                with self.assertRaises(AssertionError):
                    check_profile_meets_fr019_minimums(profile)

    def test_committed_profile_grounds_in_committed_snapshot(self) -> None:
        check_profile_grounds_in_committed_snapshot(self.load_committed_profile())

    def test_snapshot_grounding_check_has_teeth(self) -> None:
        profile = self.load_committed_profile()
        profile["runtime_capability_snapshot_id"] = "CAR-002-RCS-2020-01-01-V9"
        with self.assertRaises(AssertionError):
            check_profile_grounds_in_committed_snapshot(profile)


class RouteResolutionFixtureTests(unittest.TestCase):
    """The standalone route-resolution fixture at
    ``tests/speckit-pro/unit/fixtures/claude-telemetry-records/route-resolution.json``
    exercises the ``routeResolution`` ``$def`` in isolation (T022/T023, US3
    acceptance scenario 1) and stands in for the CAR-003 handoff (quickstart Part C
    / SC-008, T026): a downstream consumer binds a route from committed bytes
    without re-probing. Every check is teeth-verified against a corrupted copy.
    """

    require_validator = _require_validator

    def load_fixture(self) -> dict:
        self.assertTrue(
            ROUTE_RESOLUTION_FIXTURE_PATH.is_file(),
            f"route-resolution fixture missing (T022): {ROUTE_RESOLUTION_FIXTURE_PATH}",
        )
        return _read_committed_json(ROUTE_RESOLUTION_FIXTURE_PATH)

    def test_fixture_validates_against_route_resolution_def(self) -> None:
        validator = self.require_validator()
        fixture = self.load_fixture()
        self.assertIs(validator.validate_route_resolution(fixture), fixture)

    def test_fixture_uses_the_deterministic_literal_id(self) -> None:
        self.assertEqual(
            self.load_fixture()["route_resolution_id"], "CAR-002-RR-FIXTURE-001"
        )

    def test_fixture_binds_every_fr021_field(self) -> None:
        check_route_resolution_binds_all_fr021_fields(self.load_fixture())

    def test_fr021_binding_check_has_teeth(self) -> None:
        cases = {
            "missing dispatch_namespace": lambda r: r.pop("dispatch_namespace"),
            "missing parent_session_configuration": lambda r: r.pop(
                "parent_session_configuration"
            ),
            "empty dispatch_namespace": lambda r: r.__setitem__("dispatch_namespace", ""),
            "non-null fallback_index": lambda r: r.__setitem__("fallback_index", 0),
            "non-null fallback_reason": lambda r: r.__setitem__(
                "fallback_reason", "documented chain fired"
            ),
        }
        for label, mutate in cases.items():
            with self.subTest(corruption=label):
                fixture = self.load_fixture()
                mutate(fixture)
                with self.assertRaises(AssertionError):
                    check_route_resolution_binds_all_fr021_fields(fixture)

    def test_fixture_crossrefs_resolve_against_committed_bytes(self) -> None:
        # SC-008 / CAR-003 handoff: the handoff path is exercised by the committed
        # fixture resolving against the committed snapshot + manifest, no re-probing.
        check_route_resolution_crossrefs_resolve(self.load_fixture())

    def test_crossref_resolution_check_has_teeth(self) -> None:
        cases = {
            "unknown candidate_route_id": lambda r: r.__setitem__(
                "candidate_route_id", "CAR-001-CR-99-99"
            ),
            "mismatched agent_contract_id": lambda r: r.__setitem__(
                "agent_contract_id", "car.gate-validator.v1"
            ),
            "stale snapshot cross-ref": lambda r: r.__setitem__(
                "runtime_capability_snapshot_id", "CAR-002-RCS-2020-01-01-V9"
            ),
        }
        for label, mutate in cases.items():
            with self.subTest(corruption=label):
                fixture = self.load_fixture()
                mutate(fixture)
                with self.assertRaises(AssertionError):
                    check_route_resolution_crossrefs_resolve(fixture)


class ExactTreatmentTelemetryLinkageTests(_CommittedTelemetryProfileFixture, unittest.TestCase):
    """FR-022 telemetry-linkage rule: a non-null ``outcome.telemetry_ref`` MUST
    resolve against the committed telemetry-profile field set during deterministic
    validation; a dangling reference fails validation (T024)."""

    def test_null_telemetry_ref_needs_no_resolution(self) -> None:
        replay = valid_exact_treatment_replay()
        replay["outcome"]["telemetry_ref"] = None
        check_telemetry_ref_resolves(replay, self.load_committed_profile())

    def test_resolvable_telemetry_ref_against_committed_profile(self) -> None:
        profile = self.load_committed_profile()
        resolvable_field = profile["field_classifications"][0]["field"]
        replay = valid_exact_treatment_replay()
        replay["outcome"]["telemetry_ref"] = resolvable_field
        check_telemetry_ref_resolves(replay, profile)  # resolves; does not raise

    def test_stable_native_raw_token_ref_resolves(self) -> None:
        # AC-2.3: raw token categories stay reachable from the record via the profile.
        profile = self.load_committed_profile()
        replay = valid_exact_treatment_replay()
        replay["outcome"]["telemetry_ref"] = "usage.input_tokens"
        check_telemetry_ref_resolves(replay, profile)

    def test_dangling_telemetry_ref_fails_validation(self) -> None:
        profile = self.load_committed_profile()
        replay = valid_exact_treatment_replay()
        replay["outcome"]["telemetry_ref"] = "usage.no_such_field_anywhere"
        with self.assertRaises(AssertionError):
            check_telemetry_ref_resolves(replay, profile)


# -- T029-T036 (WP3): the four record-class fixtures, class invariants, the
# 37-route -> tuple join, and the committed-payload integrity re-checks. Same
# pure-check-plus-teeth idiom as WP1/WP2 above: each rule is a module-level
# ``check_*`` that raises AssertionError on violation, so one function backs both
# the positive assertion (committed artifact passes) and the teeth test (a
# deliberately-corrupted copy fails), making every green meaningful.

SUCCESS_FIXTURE_PATH = TELEMETRY_RECORDS_DIR / "success.json"
NULL_FIXTURE_PATH = TELEMETRY_RECORDS_DIR / "null.json"
UNAVAILABLE_FIXTURE_PATH = TELEMETRY_RECORDS_DIR / "unavailable.json"
MISDELIVERY_FIXTURE_PATH = TELEMETRY_RECORDS_DIR / "misdelivery.json"
RECORD_CLASS_FIXTURE_PATHS = {
    "success": SUCCESS_FIXTURE_PATH,
    "null": NULL_FIXTURE_PATH,
    "unavailable": UNAVAILABLE_FIXTURE_PATH,
    "misdelivery": MISDELIVERY_FIXTURE_PATH,
}

# FR-024 class-invariant pairings and FR-025 class -> status mapping.
SCORABLE_BY_CLASS = {"success": True, "null": True, "unavailable": False, "misdelivery": False}
STATUS_BY_CLASS = {
    "success": "completed",
    "null": "completed",
    "misdelivery": "completed",
    "unavailable": "unavailable",
}

# The committed CAR-002 payloads whose sanitized bytes the validator re-scans every
# run (the write-time FR-012/FR-013 guarantee, re-checked continuously).
COMMITTED_CAR002_PAYLOAD_PATHS = (
    SNAPSHOT_PATH,
    PROFILE_PATH,
    ROUTE_RESOLUTION_FIXTURE_PATH,
    SUCCESS_FIXTURE_PATH,
    NULL_FIXTURE_PATH,
    UNAVAILABLE_FIXTURE_PATH,
    MISDELIVERY_FIXTURE_PATH,
)

# Every home/user/session privacy family plus the raw session/request UUID rule the
# committed privacy scan flags — the sanitizer now redacts UUIDs to ``<session-id>``.
_PRIVACY_SCAN_PATTERNS = {
    "posix/windows home path": PRIVACY_HOME_PATH,
    "hyphenated home path": PRIVACY_HYPHENATED_HOME,
    "private/var session path": PRIVACY_PRIVATE_VAR,
    "tmp transcript path": PRIVACY_TMP_TRANSCRIPT,
    "raw session/request UUID": PRIVACY_UUID,
}


def _nullable_leaf_values(record: dict) -> dict[str, object]:
    """The nullable leaf fields of an ``exactTreatmentReplay`` record (every schema
    ``nullableString`` / nullable-integer leaf). ``null.json`` sets every one to null
    (present-but-null); ``success.json`` sets every one non-null — exact mirrors
    (FR-020/FR-025)."""
    route = record["route_resolution"]
    proof = route["env_override_proof"]
    return {
        "execution_trace_id": record["execution_trace_id"],
        "observed_model_id": record["observed_model_id"],
        "outcome.telemetry_ref": record["outcome"]["telemetry_ref"],
        "outcome.notes": record["outcome"]["notes"],
        "route_resolution.effort_level": route["effort_level"],
        "route_resolution.parent_session_configuration": route["parent_session_configuration"],
        "route_resolution.fallback_index": route["fallback_index"],
        "route_resolution.fallback_reason": route["fallback_reason"],
        "env_override_proof.enforce_available_models_observed": proof["enforce_available_models_observed"],
        "env_override_proof.inherit_equivalent_to_unset": proof["inherit_equivalent_to_unset"],
        "env_override_proof.org_restriction_gap": proof["org_restriction_gap"],
    }


def check_class_scorable_pairing(record: dict) -> None:
    """FR-024: ``success``/``null`` are scorable; ``unavailable``/``misdelivery`` are not."""
    record_class = record["record_class"]
    expected = SCORABLE_BY_CLASS[record_class]
    if record["scorable"] is not expected:
        raise AssertionError(
            f"record_class {record_class!r}: scorable must be {expected}, got {record['scorable']!r}"
        )


def check_class_status_mapping(record: dict) -> None:
    """FR-025 class -> status: ``unavailable`` => ``unavailable``; ``success``/``null``/
    ``misdelivery`` => ``completed`` (misdelivery is a completed-but-misrouted treatment)."""
    record_class = record["record_class"]
    expected = STATUS_BY_CLASS[record_class]
    if record["outcome"]["status"] != expected:
        raise AssertionError(
            f"record_class {record_class!r}: outcome.status must be {expected!r}, "
            f"got {record['outcome']['status']!r}"
        )


def check_misdelivery_semantics(record: dict) -> None:
    """FR-025 precedence: a misdelivery is ``observed_model_id`` != the resolved qualified
    ID WITH ``fallback_index``/``fallback_reason`` null — a fallback-null difference is a
    misdelivery, not a recorded resolver fallback (AC-2.3 separation)."""
    route = record["route_resolution"]
    resolved = route["resolved_dated_model_id"]
    observed = record["observed_model_id"]
    if observed == resolved:
        raise AssertionError(
            f"misdelivery requires observed != resolved, but both are {resolved!r}"
        )
    if route["fallback_index"] is not None or route["fallback_reason"] is not None:
        raise AssertionError(
            "misdelivery requires fallback_index/fallback_reason null (a non-null fallback "
            "reclassifies the difference as recorded resolver fallback, not misdelivery)"
        )


def check_null_class_nulls_preserved(record: dict) -> None:
    """FR-020/FR-025: every nullable leaf is present-but-null (not dropped), so
    'unavailable' stays distinguishable from 'absent'."""
    non_null = {p: v for p, v in _nullable_leaf_values(record).items() if v is not None}
    if non_null:
        raise AssertionError(
            f"null-class record has non-null nullable field(s): {sorted(non_null)}"
        )


def check_success_fully_populated(record: dict) -> None:
    """FR-025: the ``success`` fixture is fully-populated — every nullable leaf non-null."""
    nulls = [p for p, v in _nullable_leaf_values(record).items() if v is None]
    if nulls:
        raise AssertionError(
            f"success-class record must be fully-populated but has null field(s): {sorted(nulls)}"
        )


def check_unavailable_crossref_resolves(record: dict) -> None:
    """FR-021/FR-025: the ``unavailable`` record cross-references a real unavailable
    observation in the committed snapshot — its ``runtime_capability_snapshot_id`` resolves
    AND the resolved dated model id is one the snapshot actually recorded as unavailable."""
    snapshot = _read_committed_json(SNAPSHOT_PATH)
    snapshot_id = record["route_resolution"]["runtime_capability_snapshot_id"]
    if snapshot_id != snapshot["runtime_capability_snapshot_id"]:
        raise AssertionError(
            f"unavailable cross-ref {snapshot_id!r} != committed snapshot id "
            f"{snapshot['runtime_capability_snapshot_id']!r}"
        )
    unavailable_ids = {
        obs["requested_unavailable_model_id"] for obs in snapshot["unavailable_observations"]
    }
    resolved = record["route_resolution"]["resolved_dated_model_id"]
    if resolved not in unavailable_ids:
        raise AssertionError(
            f"unavailable record resolved model {resolved!r} is not among the snapshot's "
            f"recorded unavailable observations {sorted(unavailable_ids)}"
        )


def check_exact_treatment_class_invariants(record: dict) -> None:
    """FR-024/FR-025 dispatcher: the class<->scorable pairing and class->status mapping for
    every class, then the per-class semantic rule (misdelivery / null / unavailable /
    success)."""
    check_class_scorable_pairing(record)
    check_class_status_mapping(record)
    record_class = record["record_class"]
    if record_class == "misdelivery":
        check_misdelivery_semantics(record)
    elif record_class == "null":
        check_null_class_nulls_preserved(record)
    elif record_class == "unavailable":
        check_unavailable_crossref_resolves(record)
    elif record_class == "success":
        check_success_fully_populated(record)
    else:  # pragma: no cover - schema enum already constrains record_class
        raise AssertionError(f"unknown record_class {record_class!r}")


def check_exact_treatment_referential_integrity(record: dict, profile: dict) -> None:
    """FR-024/FR-022: the embedded ``candidate_route_id``/``agent_contract_id`` resolve to
    the committed CAR-001 manifest, the snapshot cross-ref resolves, and any non-null
    ``telemetry_ref`` resolves to the committed telemetry-profile field set — referential,
    not merely well-formed."""
    check_route_resolution_crossrefs_resolve(record["route_resolution"])
    check_telemetry_ref_resolves(record, profile)


def derive_route_tuple_id(route: dict) -> str:
    """Pure derivation of a CAR-001 route's ``(model, effort)`` tuple_id from its manifest
    selectors — null effort -> the ``none`` token (research R1). NEVER persisted (SC-005)."""
    model = route["model_selector"]["requested_value"]
    effort = route["effort_selector"]["requested_value"]
    return f"{model}__{effort if effort is not None else 'none'}".lower()


def join_routes_to_tuples(candidate_routes: list, tuple_evidence: list) -> dict[str, str]:
    """SC-005: recompute the 37-route -> tuple join from the committed manifest selectors
    against the snapshot's per-tuple evidence, failing closed if any route resolves to zero
    or to more than one tuple. Returns the derived ``candidate_route_id`` -> ``tuple_id``
    map (computed every run, never persisted)."""
    evidence_ids = [evidence["tuple_id"] for evidence in tuple_evidence]
    resolved: dict[str, str] = {}
    for route in candidate_routes:
        tuple_id = derive_route_tuple_id(route)
        matches = [tid for tid in evidence_ids if tid == tuple_id]
        if len(matches) != 1:
            raise AssertionError(
                f"route {route['candidate_route_id']!r} resolves to {len(matches)} tuple(s) "
                f"(expected exactly 1) for derived tuple_id {tuple_id!r}"
            )
        resolved[route["candidate_route_id"]] = tuple_id
    return resolved


def check_snapshot_has_no_persisted_route_tuple_map(snapshot: dict) -> None:
    """FR-004/SC-005/constitution VI: the route -> tuple join is derived, never stored — no
    ``tuple_evidence`` entry carries a ``candidate_route_id``."""
    for evidence in snapshot["tuple_evidence"]:
        if "candidate_route_id" in evidence:
            raise AssertionError(
                f"tuple_evidence {evidence.get('tuple_id')!r} persists a candidate_route_id — "
                "the route->tuple join must be derived, not stored (SC-005)"
            )


def _iter_snapshot_raw_evidence(snapshot: dict):
    for location in ("tuple_evidence", "alias_bindings", "unavailable_observations"):
        for entry in snapshot[location]:
            yield location, entry["raw_evidence"]


def check_snapshot_hashes_reproduce(snapshot: dict) -> None:
    """FR-024/FR-013: the canary hash reproduces over the recorded canary text and every
    stored ``raw_output_sha256`` reproduces over the committed sanitized UTF-8 payload
    bytes."""
    canary = snapshot["canary"]
    if _sha256_hex(canary["text"]) != canary["canary_sha256"]:
        raise AssertionError("canary_sha256 does not reproduce over the recorded canary text")
    for location, evidence in _iter_snapshot_raw_evidence(snapshot):
        recomputed = _sha256_hex(evidence["raw_output"])
        if recomputed != evidence["raw_output_sha256"]:
            raise AssertionError(
                f"{location}: raw_output_sha256 {evidence['raw_output_sha256']!r} does not "
                f"reproduce over committed bytes (recomputed {recomputed!r})"
            )


def scan_text_for_unsanitized_paths(text: str) -> dict[str, str]:
    """Return ``{pattern_label: first_match}`` for every privacy family the text still leaks
    (FR-012/FR-013 home/user/session paths plus the raw session/request UUID rule). An empty
    dict means the text is clean."""
    hits: dict[str, str] = {}
    for label, pattern in _PRIVACY_SCAN_PATTERNS.items():
        match = pattern.search(text)
        if match is not None:
            hits[label] = match.group(0)
    return hits


def check_committed_payload_is_sanitized(path: Path) -> None:
    """FR-024: continuously re-check the write-time FR-012/FR-013 guarantee — no committed
    payload contains an unsanitized home/user/session path or a raw session/request UUID."""
    hits = scan_text_for_unsanitized_paths(path.read_text(encoding="utf-8"))
    if hits:
        raise AssertionError(f"{path.name}: unsanitized content {hits}")


class RecordClassFixtureTests(unittest.TestCase):
    """The four committed record-class fixtures (T029-T032) are validated against the
    ``exactTreatmentReplay`` ``$def`` on every run (T033, SC-003 100% record-class coverage)
    and additionally enforced for their FR-024/FR-025 class invariants (T034): the
    class<->scorable pairing, the class->status mapping, and each class's semantic rule.
    Every check is teeth-verified against a deliberately-corrupted copy."""

    require_validator = _require_validator

    def load_fixture(self, record_class: str) -> dict:
        path = RECORD_CLASS_FIXTURE_PATHS[record_class]
        self.assertTrue(path.is_file(), f"record-class fixture missing (T029-T032): {path}")
        record = _read_committed_json(path)
        self.assertEqual(record["record_class"], record_class, f"{path.name} record_class")
        return record

    # -- T033: all four validate against the exactTreatmentReplay $def every run ----

    def test_all_four_fixtures_validate_against_exact_treatment_replay(self) -> None:
        validator = self.require_validator()
        for record_class in RECORD_CLASS_FIXTURE_PATHS:
            with self.subTest(record_class=record_class):
                record = self.load_fixture(record_class)
                self.assertIs(validator.validate_exact_treatment_replay(record), record)

    def test_all_four_record_classes_have_a_committed_fixture(self) -> None:
        # SC-003: 100% record-class coverage — exactly one fixture per class.
        self.assertEqual(
            set(RECORD_CLASS_FIXTURE_PATHS), {"success", "null", "unavailable", "misdelivery"}
        )
        for record_class in RECORD_CLASS_FIXTURE_PATHS:
            with self.subTest(record_class=record_class):
                self.assertEqual(self.load_fixture(record_class)["record_class"], record_class)

    def test_fixture_validation_rejects_corrupted_copies(self) -> None:
        validator = self.require_validator()
        error = validator.ClaudeTraceContractError
        mutations = {
            "bad record_class enum": lambda r: r.__setitem__("record_class", "partial"),
            "scorable wrong type": lambda r: r.__setitem__("scorable", "yes"),
            "drop outcome": lambda r: r.pop("outcome"),
            "nested route_resolution loses tuple_id": lambda r: r["route_resolution"].pop("tuple_id"),
            "additional property": lambda r: r.__setitem__("extra_field", 1),
        }
        for record_class in RECORD_CLASS_FIXTURE_PATHS:
            for label, mutate in mutations.items():
                with self.subTest(record_class=record_class, mutation=label):
                    record = self.load_fixture(record_class)
                    mutate(record)
                    with self.assertRaises(error):
                        validator.validate_exact_treatment_replay(record)

    # -- T034: class invariants (scorable pairing + status mapping + semantic) ------

    def test_all_fixtures_satisfy_their_class_invariants(self) -> None:
        for record_class in RECORD_CLASS_FIXTURE_PATHS:
            with self.subTest(record_class=record_class):
                check_exact_treatment_class_invariants(self.load_fixture(record_class))

    def test_scorable_pairing_matches_the_declared_class(self) -> None:
        for record_class, expected in SCORABLE_BY_CLASS.items():
            with self.subTest(record_class=record_class):
                self.assertIs(self.load_fixture(record_class)["scorable"], expected)

    def test_outcome_status_matches_the_declared_class(self) -> None:
        for record_class, expected in STATUS_BY_CLASS.items():
            with self.subTest(record_class=record_class):
                self.assertEqual(
                    self.load_fixture(record_class)["outcome"]["status"], expected
                )

    def test_scorable_pairing_check_has_teeth(self) -> None:
        for record_class in RECORD_CLASS_FIXTURE_PATHS:
            with self.subTest(record_class=record_class):
                record = self.load_fixture(record_class)
                record["scorable"] = not SCORABLE_BY_CLASS[record_class]
                with self.assertRaises(AssertionError):
                    check_class_scorable_pairing(record)

    def test_status_mapping_check_has_teeth(self) -> None:
        flip = {"completed": "unavailable", "unavailable": "completed"}
        for record_class in RECORD_CLASS_FIXTURE_PATHS:
            with self.subTest(record_class=record_class):
                record = self.load_fixture(record_class)
                record["outcome"]["status"] = flip[STATUS_BY_CLASS[record_class]]
                with self.assertRaises(AssertionError):
                    check_class_status_mapping(record)

    def test_misdelivery_semantics_check_has_teeth(self) -> None:
        # observed == resolved erases the misdelivery signal.
        equal = self.load_fixture("misdelivery")
        equal["observed_model_id"] = equal["route_resolution"]["resolved_dated_model_id"]
        with self.assertRaises(AssertionError):
            check_misdelivery_semantics(equal)
        # a non-null fallback reclassifies the difference as recorded resolver fallback.
        for field, value in (("fallback_index", 0), ("fallback_reason", "documented chain fired")):
            with self.subTest(fallback=field):
                record = self.load_fixture("misdelivery")
                record["route_resolution"][field] = value
                with self.assertRaises(AssertionError):
                    check_misdelivery_semantics(record)

    def test_null_class_nulls_preserved_check_has_teeth(self) -> None:
        setters = {
            "execution_trace_id": lambda r: r.__setitem__("execution_trace_id", "x"),
            "observed_model_id": lambda r: r.__setitem__("observed_model_id", "claude-opus-4-8"),
            "outcome.telemetry_ref": lambda r: r["outcome"].__setitem__("telemetry_ref", "usage.input_tokens"),
            "effort_level": lambda r: r["route_resolution"].__setitem__("effort_level", "max"),
            "fallback_index": lambda r: r["route_resolution"].__setitem__("fallback_index", 0),
            "org_restriction_gap": lambda r: r["route_resolution"]["env_override_proof"].__setitem__(
                "org_restriction_gap", "gap"
            ),
        }
        for leaf, mutate in setters.items():
            with self.subTest(leaf=leaf):
                record = self.load_fixture("null")
                mutate(record)
                with self.assertRaises(AssertionError):
                    check_null_class_nulls_preserved(record)

    def test_success_fully_populated_check_has_teeth(self) -> None:
        nullers = {
            "execution_trace_id": lambda r: r.__setitem__("execution_trace_id", None),
            "observed_model_id": lambda r: r.__setitem__("observed_model_id", None),
            "outcome.notes": lambda r: r["outcome"].__setitem__("notes", None),
            "fallback_index": lambda r: r["route_resolution"].__setitem__("fallback_index", None),
            "org_restriction_gap": lambda r: r["route_resolution"]["env_override_proof"].__setitem__(
                "org_restriction_gap", None
            ),
        }
        for leaf, mutate in nullers.items():
            with self.subTest(leaf=leaf):
                record = self.load_fixture("success")
                mutate(record)
                with self.assertRaises(AssertionError):
                    check_success_fully_populated(record)

    def test_unavailable_crossref_check_has_teeth(self) -> None:
        stale = self.load_fixture("unavailable")
        stale["route_resolution"]["runtime_capability_snapshot_id"] = "CAR-002-RCS-2020-01-01-V9"
        with self.assertRaises(AssertionError):
            check_unavailable_crossref_resolves(stale)
        # a model the snapshot never recorded as unavailable does not resolve.
        available = self.load_fixture("unavailable")
        available["route_resolution"]["resolved_dated_model_id"] = "claude-opus-4-8"
        with self.assertRaises(AssertionError):
            check_unavailable_crossref_resolves(available)


class RouteToTupleJoinTests(unittest.TestCase):
    """T035/SC-005: the 37-route -> tuple join is recomputed every run from the committed
    CAR-001 manifest selectors against the snapshot's per-tuple evidence, failing closed if
    any route resolves to zero or to more than one tuple; the join is derived, never
    persisted. Teeth-verified for the zero-resolve, multi-resolve, and persisted-map
    failure modes."""

    def committed_routes(self) -> list:
        return _read_committed_json(MANIFEST_PATH)["candidate_routes"]

    def committed_tuple_evidence(self) -> list:
        return _read_committed_json(SNAPSHOT_PATH)["tuple_evidence"]

    def test_all_37_routes_resolve_to_exactly_one_of_the_six_tuples(self) -> None:
        routes = self.committed_routes()
        self.assertEqual(len(routes), EXPECTED_ROUTE_TOTAL)
        resolved = join_routes_to_tuples(routes, self.committed_tuple_evidence())
        self.assertEqual(len(resolved), EXPECTED_ROUTE_TOTAL)
        self.assertEqual(set(resolved.values()), set(EXPECTED_TUPLE_IDS))
        self.assertEqual(dict(Counter(resolved.values())), dict(EXPECTED_TUPLE_ROUTE_COUNTS))

    def test_derive_route_tuple_id_lowercases_and_handles_null_effort(self) -> None:
        self.assertEqual(
            derive_route_tuple_id(
                {"model_selector": {"requested_value": "haiku"}, "effort_selector": {"requested_value": None}}
            ),
            "haiku__none",
        )
        self.assertEqual(
            derive_route_tuple_id(
                {"model_selector": {"requested_value": "OPUS"}, "effort_selector": {"requested_value": "MAX"}}
            ),
            "opus__max",
        )

    def test_join_is_derived_not_persisted(self) -> None:
        check_snapshot_has_no_persisted_route_tuple_map(_read_committed_json(SNAPSHOT_PATH))

    def test_join_fails_closed_when_a_route_resolves_to_zero_tuples(self) -> None:
        routes = self.committed_routes()
        evidence = [te for te in self.committed_tuple_evidence() if te["tuple_id"] != "opus__max"]
        with self.assertRaises(AssertionError):
            join_routes_to_tuples(routes, evidence)

    def test_join_fails_closed_when_a_route_resolves_to_more_than_one_tuple(self) -> None:
        routes = self.committed_routes()
        evidence = self.committed_tuple_evidence()
        evidence.append(dict(evidence[0]))  # duplicate the first tuple_id -> >1 match
        with self.assertRaises(AssertionError):
            join_routes_to_tuples(routes, evidence)

    def test_persisted_map_check_has_teeth(self) -> None:
        snapshot = _read_committed_json(SNAPSHOT_PATH)
        snapshot["tuple_evidence"][0]["candidate_route_id"] = "CAR-001-CR-01-01"
        with self.assertRaises(AssertionError):
            check_snapshot_has_no_persisted_route_tuple_map(snapshot)


class CommittedPayloadIntegrityTests(unittest.TestCase):
    """T036/FR-024 integrity re-checks over committed bytes: every stored hash reproduces,
    no committed payload leaks an unsanitized home/user/session path or a raw UUID, and every
    cross-reference in the record fixtures resolves referentially (not merely as a
    well-formed string). Each check is teeth-verified."""

    # -- (a) hash reproduction over committed sanitized bytes ----------------------

    def test_committed_snapshot_hashes_reproduce_over_committed_bytes(self) -> None:
        check_snapshot_hashes_reproduce(_read_committed_json(SNAPSHOT_PATH))

    def test_hash_reproduction_check_has_teeth(self) -> None:
        tampered = _read_committed_json(SNAPSHOT_PATH)
        tampered["tuple_evidence"][0]["raw_evidence"]["raw_output"] += " tampered"
        with self.assertRaises(AssertionError):
            check_snapshot_hashes_reproduce(tampered)
        canary_tampered = _read_committed_json(SNAPSHOT_PATH)
        canary_tampered["canary"]["text"] += "!"
        with self.assertRaises(AssertionError):
            check_snapshot_hashes_reproduce(canary_tampered)

    # -- (b) privacy re-scan: home/user/session paths + raw UUIDs ------------------

    def test_every_committed_payload_is_sanitized(self) -> None:
        for path in COMMITTED_CAR002_PAYLOAD_PATHS:
            with self.subTest(payload=path.name):
                self.assertTrue(path.is_file(), f"committed CAR-002 payload missing: {path}")
                check_committed_payload_is_sanitized(path)

    def test_privacy_scan_flags_a_home_path(self) -> None:
        leaked = "cwd=" + _home_posix("alice/repo")
        self.assertIn("posix/windows home path", scan_text_for_unsanitized_paths(leaked))

    def test_privacy_scan_flags_a_raw_uuid(self) -> None:
        # Assembled from fragments so this file's source carries no literal UUID.
        uuid = "-".join(("78b65992", "1a2b", "3c4d", "5e6f", "0011" + "22334455"))
        self.assertIn(
            "raw session/request UUID",
            scan_text_for_unsanitized_paths(f'"session_id":"{uuid}"'),
        )

    def test_privacy_scan_passes_clean_sanitized_text(self) -> None:
        clean = '{"session_id":"<session-id>","cwd":"<home>/repo","modelUsage":{}}'
        self.assertEqual(scan_text_for_unsanitized_paths(clean), {})

    # -- (c) referential integrity of every committed record fixture ---------------

    def test_record_fixtures_resolve_all_crossrefs(self) -> None:
        profile = _read_committed_json(PROFILE_PATH)
        for record_class, path in RECORD_CLASS_FIXTURE_PATHS.items():
            with self.subTest(record_class=record_class):
                self.assertTrue(path.is_file(), f"record-class fixture missing: {path}")
                check_exact_treatment_referential_integrity(_read_committed_json(path), profile)

    def test_referential_integrity_check_has_teeth(self) -> None:
        profile = _read_committed_json(PROFILE_PATH)
        self.assertTrue(SUCCESS_FIXTURE_PATH.is_file(), "success fixture missing (T029)")
        cases = {
            "unknown candidate_route_id": lambda r: r["route_resolution"].__setitem__(
                "candidate_route_id", "CAR-001-CR-99-99"
            ),
            "mismatched agent_contract_id": lambda r: r["route_resolution"].__setitem__(
                "agent_contract_id", "car.gate-validator.v1"
            ),
            "stale snapshot cross-ref": lambda r: r["route_resolution"].__setitem__(
                "runtime_capability_snapshot_id", "CAR-002-RCS-2020-01-01-V9"
            ),
            "dangling telemetry_ref": lambda r: r["outcome"].__setitem__(
                "telemetry_ref", "usage.no_such_field_anywhere"
            ),
        }
        for label, mutate in cases.items():
            with self.subTest(corruption=label):
                record = _read_committed_json(SUCCESS_FIXTURE_PATH)
                mutate(record)
                with self.assertRaises(AssertionError):
                    check_exact_treatment_referential_integrity(record, profile)


if __name__ == "__main__":
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(ClaudeTraceSchemaContractTests))
    suite.addTests(loader.loadTestsFromTestCase(ClaudeCapabilitiesPureLogicTests))
    suite.addTests(loader.loadTestsFromTestCase(ClaudeCapabilitiesLiveBoundaryTests))
    suite.addTests(loader.loadTestsFromTestCase(CommittedRuntimeCapabilitySnapshotTests))
    suite.addTests(loader.loadTestsFromTestCase(CommittedTelemetryProfileTests))
    suite.addTests(loader.loadTestsFromTestCase(RouteResolutionFixtureTests))
    suite.addTests(loader.loadTestsFromTestCase(ExactTreatmentTelemetryLinkageTests))
    suite.addTests(loader.loadTestsFromTestCase(RecordClassFixtureTests))
    suite.addTests(loader.loadTestsFromTestCase(RouteToTupleJoinTests))
    suite.addTests(loader.loadTestsFromTestCase(CommittedPayloadIntegrityTests))
    raise SystemExit(run_counted(suite, label="test-efficiency-claude-telemetry"))
