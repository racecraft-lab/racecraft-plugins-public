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
  ``tests/speckit-pro/layer6-efficiency/lib/claude_trace_schema.py``). Until that
  module lands they fail closed on ``assertIsNotNone`` — an expected RED that
  T005/T006 turn green.
"""

from __future__ import annotations

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


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ClaudeTraceSchemaContractTests)
    raise SystemExit(run_counted(suite, label="test-efficiency-claude-telemetry"))
