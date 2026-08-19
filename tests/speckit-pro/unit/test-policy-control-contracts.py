#!/usr/bin/env python3
"""Policy-control registry contract, per-control rules, replay, guard, and smoke records.

This module is the deterministic coverage for the three frozen policy controls —
unpinned, adaptive, and orchestration-changing — and for everything the registry
freezes about them: content addressing, additive-only bindings into the frozen
CAR-003 contracts, the adaptive signal maps and escalation ladder, bound scope
and breach outcomes, unit membership and aggregation, the reserved-partition
guard, and the bounded operator smoke record.

Contract-structural cases read the committed schema documents under
``tests/speckit-pro/layer6-efficiency/contracts-claude/``; module-contract cases
exercise ``tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py``.

Every check is offline and makes zero live model calls. The three live smokes are
operator-driven and deliberately live outside this module.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import inspect
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LIB_DIR = TEST_ROOT / "lib"
LAYER6_LIB_DIR = TEST_ROOT / "layer6-efficiency" / "lib"
for _path in (LIB_DIR, LAYER6_LIB_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from structural_helpers import declared_refs, load_json, open_object_nodes  # noqa: E402
from test_result import run_counted  # noqa: E402

# Frozen CAR-003 code, imported read-only: it publishes the one preimage rule the
# whole program digests under, so these cases check CAR-004 addresses against an
# oracle the module under test does not own (research D3).
from claude_successor_freeze import canonical_json, record_digest  # noqa: E402

# The frozen plane derivation, likewise read-only: a case that restated the
# code-to-plane partition would author the very agreement FR-010c.1 checks.
from claude_score_bundle import failure_plane_for  # noqa: E402

# The frozen partition machinery, read-only: FR-025a and FR-025b oblige CAR-004
# to register through the path CAR-003 already owns, so these cases exercise that
# path rather than a CAR-004 restatement of it.
from claude_experiment_policy import (  # noqa: E402
    CROSS_PARTITION_REUSE,
    PARTITION_MISMATCH,
    PARTITION_PLANE,
    ExperimentPolicyError,
    build_partition_registry_entry,
    register_partitions,
)

try:  # CAR-004 deliverable — absent until the policy-control module is implemented.
    import claude_policy_controls  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    claude_policy_controls = None  # type: ignore[assignment]

try:  # G56R-004 deliverable — extended as Codex control validation lands.
    import codex_policy_controls  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    codex_policy_controls = None  # type: ignore[assignment]

try:  # G56R-004 T025 deliverable — absent until the partition guards land.
    import codex_control_smoke  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only during the T024 RED state
    codex_control_smoke = None  # type: ignore[assignment]


CONTRACT_ROOT = TEST_ROOT / "layer6-efficiency" / "contracts-claude"
FIXTURE_ROOT = TEST_ROOT / "layer6-efficiency" / "fixtures-controls"
CODEX_CONTRACT_ROOT = TEST_ROOT / "layer6-efficiency" / "contracts-codex-specification"
CODEX_FIXTURE_ROOT = TEST_ROOT / "layer6-efficiency" / "fixtures-codex-controls"

REGISTRY_SCHEMA_PATH = CONTRACT_ROOT / "policy-control-registry.schema.json"
REGISTRY_SCHEMA_ID = "https://racecraft.dev/schemas/car-004/policy-control-registry.schema.json"
CODEX_REGISTRY_SCHEMA_PATH = CODEX_CONTRACT_ROOT / "policy-control-registry.schema.json"
CODEX_REGISTRY_FIXTURE_PATH = CODEX_FIXTURE_ROOT / "policy-control-registry.json"
CODEX_REPLAY_CASES_PATH = CODEX_FIXTURE_ROOT / "replay-cases.json"
CODEX_PARTITION_FIXTURE_PATH = CODEX_FIXTURE_ROOT / "partition-registry-entries.json"
CODEX_REGISTRY_SCHEMA_ID = "https://racecraft.dev/schemas/g56r-004/policy-control-registry.schema.json"
CODEX_REGISTRY_ID = "g56r-004-policy-control-registry"
CODEX_CONTROL_IDS_BY_KIND = {
    "unpinned": "g56r-004-unpinned-control",
    "adaptive": "g56r-004-adaptive-control",
    "justified_high_effort": "g56r-004-justified-high-effort-control",
}
CODEX_CONTROL_KINDS = tuple(CODEX_CONTROL_IDS_BY_KIND)
CODEX_REQUIRED_ABSENT_OVERRIDES = (
    "api_key",
    "effort",
    "model",
    "provider",
    "service_tier",
)
CODEX_G56R003_SUCCESSOR_FREEZE_ID = (
    "sha256:734672cea5a83e5b8f296ee604f7cb8d93e0a5296a3f864b873fe78bfe518f1e"
)
CODEX_G56R003_ROUTE_EVIDENCE_DIGEST = (
    "sha256:f01ff64ca3d17b40db8ca802dd6501e62d91c4c161d01a94879c156f90eb09e4"
)
CODEX_JUSTIFIED_HIGH_EFFORT_ROUTE_ID = "g56r-003-route-phase-executor"
CODEX_JUSTIFIED_HIGH_EFFORT_MODEL = "gpt-5.5"
CODEX_JUSTIFIED_HIGH_EFFORT_EFFORT = "xhigh"
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

# FR-004 and SC-017: a reference that leaves the owning document is refused, so
# the only admissible prefix is the document's own local definition pointer.
LOCAL_REF_PREFIX = "#/$defs/"

class PolicyControlContractTests(unittest.TestCase):
    def test_validator_module_directory_is_on_the_import_path(self) -> None:
        self.assertTrue(LAYER6_LIB_DIR.is_dir())
        self.assertIn(str(LAYER6_LIB_DIR), sys.path)

    def test_schemas_and_frozen_instances_occupy_separate_roots(self) -> None:
        self.assertTrue(CONTRACT_ROOT.is_dir())
        self.assertNotEqual(CONTRACT_ROOT, FIXTURE_ROOT)
        self.assertEqual(CONTRACT_ROOT.parent, FIXTURE_ROOT.parent)


class RegistryDocumentShapeTests(unittest.TestCase):
    """FR-004 and SC-017: the registry document's own shape, before any instance."""

    def setUp(self) -> None:
        # Per-test rather than per-class so a missing or malformed document
        # surfaces as a counted failure on every case it breaks.
        self.schema = load_json(REGISTRY_SCHEMA_PATH)

    def test_the_registry_document_loads_and_declares_its_own_identifier(self) -> None:
        self.assertEqual(self.schema["$schema"], JSON_SCHEMA_DIALECT)
        self.assertEqual(self.schema["$id"], REGISTRY_SCHEMA_ID)

    def test_the_registry_document_freezes_its_schema_version_and_status(self) -> None:
        properties = self.schema["properties"]
        self.assertEqual(properties["schema_version"]["const"], "1.0.0")
        self.assertEqual(properties["status"]["const"], "frozen")
        self.assertEqual(
            sorted(self.schema["required"]),
            [
                "car_003_bindings",
                "controls",
                "frozen_at",
                "registry_digest",
                "registry_id",
                "schema_version",
                "smoke_bounds",
                "status",
            ],
        )

    def test_every_object_in_the_registry_document_closes_its_member_set(self) -> None:
        self.assertEqual(open_object_nodes(self.schema), [])

    def test_the_registry_document_resolves_every_reference_inside_its_own_defs(self) -> None:
        local_definitions = self.schema["$defs"]
        refs = declared_refs(self.schema)
        self.assertTrue(refs, "the document declares no $ref at all")
        for ref in refs:
            with self.subTest(ref=ref):
                self.assertTrue(ref.startswith(LOCAL_REF_PREFIX))
                self.assertIn(ref[len(LOCAL_REF_PREFIX):], local_definitions)

    def test_the_control_array_is_closed_at_exactly_three_members(self) -> None:
        controls = self.schema["properties"]["controls"]
        self.assertEqual(controls["type"], "array")
        self.assertEqual(controls["minItems"], 3)
        self.assertEqual(controls["maxItems"], 3)
        self.assertIs(controls["uniqueItems"], True)
        self.assertEqual(controls["items"]["$ref"], "#/$defs/control")

    def test_the_registry_declares_shared_smoke_bounds_and_frozen_contract_bindings(self) -> None:
        properties = self.schema["properties"]
        self.assertEqual(properties["smoke_bounds"]["$ref"], "#/$defs/smokeBounds")
        bindings = properties["car_003_bindings"]
        self.assertEqual(bindings["type"], "array")
        self.assertEqual(bindings["minItems"], 1)
        self.assertEqual(bindings["items"]["$ref"], "#/$defs/binding")
        binding = self.schema["$defs"]["binding"]
        self.assertEqual(sorted(binding["required"]), ["digest", "id"])


# A self-contained probe document, deliberately not the committed registry: the
# engine is generic and its refusals must be provable without depending on any
# frozen instance. It carries one member per keyword FR-004 and SC-017 name.
ENGINE_PROBE_SCHEMA: dict[str, object] = {
    "$schema": JSON_SCHEMA_DIALECT,
    "$id": "https://racecraft.dev/schemas/car-004/engine-probe.schema.json",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "record_id", "frozen_at", "digest", "control_kinds"],
    "properties": {
        "schema_version": {"const": "1.0.0"},
        "record_id": {"type": "string", "minLength": 1},
        "frozen_at": {"type": "string", "format": "date-time"},
        "digest": {"$ref": "#/$defs/digest"},
        "control_kinds": {
            "type": "array",
            "minItems": 1,
            "items": {"enum": ["unpinned", "adaptive", "orchestration_changing"]},
        },
    },
    "$defs": {"digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}},
}

ENGINE_PROBE_INSTANCE: dict[str, object] = {
    "schema_version": "1.0.0",
    "record_id": "car-004-engine-probe",
    "frozen_at": "2026-07-27T00:00:00Z",
    "digest": "sha256:" + "0" * 64,
    "control_kinds": ["unpinned", "adaptive", "orchestration_changing"],
}


class SchemaEngineFailClosedTests(unittest.TestCase):
    """FR-004 and SC-017: the shared engine refuses, it never degrades."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.schema = copy.deepcopy(ENGINE_PROBE_SCHEMA)
        self.instance = copy.deepcopy(ENGINE_PROBE_INSTANCE)

    def test_the_engine_error_is_an_assertion_error(self) -> None:
        self.assertTrue(issubclass(self.error, AssertionError))

    def test_load_contract_reads_a_committed_document_from_disk(self) -> None:
        loaded = self.module.load_contract(REGISTRY_SCHEMA_PATH)
        self.assertEqual(loaded["$id"], REGISTRY_SCHEMA_ID)
        self.assertEqual(loaded, load_json(REGISTRY_SCHEMA_PATH))

    def test_load_contract_refuses_a_document_that_is_not_on_disk(self) -> None:
        with self.assertRaises(self.error):
            self.module.load_contract(CONTRACT_ROOT / "no-such-contract.schema.json")

    def test_a_conforming_instance_validates_and_is_returned_unchanged(self) -> None:
        self.assertEqual(
            self.module.validate_instance(self.instance, self.schema), self.instance
        )

    def test_a_reference_leaving_the_document_is_refused(self) -> None:
        # SC-017: the refusal is what makes "resolves nothing outside its own
        # #/$defs/" machine-checked rather than asserted.
        self.schema["properties"]["digest"] = {
            "$ref": "https://racecraft.dev/schemas/car-003/score-bundle.schema.json#/$defs/digest"
        }
        with self.assertRaises(self.error):
            self.module.validate_instance(self.instance, self.schema)

    def test_a_reference_to_an_undeclared_local_definition_is_refused(self) -> None:
        self.schema["properties"]["digest"] = {"$ref": "#/$defs/absentDigest"}
        with self.assertRaises(self.error):
            self.module.validate_instance(self.instance, self.schema)

    def test_a_missing_required_key_is_refused(self) -> None:
        del self.instance["frozen_at"]
        with self.assertRaises(self.error):
            self.module.validate_instance(self.instance, self.schema)

    def test_an_unexpected_key_under_a_closed_member_set_is_refused(self) -> None:
        self.instance["authentication_mode"] = "subscription"
        with self.assertRaises(self.error):
            self.module.validate_instance(self.instance, self.schema)

    def test_a_const_violation_is_refused(self) -> None:
        self.instance["schema_version"] = "1.0.1"
        with self.assertRaises(self.error):
            self.module.validate_instance(self.instance, self.schema)

    def test_an_enum_violation_is_refused(self) -> None:
        self.instance["control_kinds"] = ["unpinned", "justified_high_effort"]
        with self.assertRaises(self.error):
            self.module.validate_instance(self.instance, self.schema)

    def test_a_pattern_violation_is_refused(self) -> None:
        self.instance["digest"] = "sha256:" + "F" * 64
        with self.assertRaises(self.error):
            self.module.validate_instance(self.instance, self.schema)

    def test_a_min_length_violation_is_refused(self) -> None:
        self.instance["record_id"] = ""
        with self.assertRaises(self.error):
            self.module.validate_instance(self.instance, self.schema)

    def test_a_min_items_violation_is_refused(self) -> None:
        self.instance["control_kinds"] = []
        with self.assertRaises(self.error):
            self.module.validate_instance(self.instance, self.schema)

    def test_a_declared_type_violation_is_refused(self) -> None:
        self.instance["record_id"] = 4
        with self.assertRaises(self.error):
            self.module.validate_instance(self.instance, self.schema)

    def test_a_timestamp_that_is_not_a_z_suffixed_utc_instant_is_refused(self) -> None:
        for stamp in ("2026-07-27T00:00:00+02:00", "2026-07-27T00:00:00", "not-a-timestamp"):
            with self.subTest(frozen_at=stamp):
                instance = dict(self.instance, frozen_at=stamp)
                with self.assertRaises(self.error):
                    self.module.validate_instance(instance, self.schema)


# --------------------------------------------------------------------------- #
# Synthetic registry subject                                                    #
#                                                                               #
# Built in-test rather than read from the committed instance so these cases      #
# prove the rules independently of the fixture, which lands later. The committed #
# instance gets its own conformance case.                                        #
# --------------------------------------------------------------------------- #

CONTROL_KINDS = ("unpinned", "adaptive", "orchestration_changing")
FROZEN_AT = "2026-07-27T00:00:00Z"


def bound(value: int, unit: str) -> dict[str, object]:
    """A `smoke_bounds` member: every numeric carries its unit and direction."""
    return {"value": value, "unit": unit, "direction": "higher_is_worse"}


def synthetic_smoke_bounds() -> dict[str, object]:
    """The frozen bound set. 800000 + 150000 + 50000 == 1000000 (FR-030a)."""
    return {
        "max_attempts": bound(5, "attempts"),
        "max_candidates": bound(1, "candidates"),
        "max_confirmation_entries": bound(0, "entries"),
        "max_duration_seconds": bound(1800, "seconds"),
        "max_input_tokens": bound(800000, "tokens"),
        "max_cached_input_tokens": bound(150000, "tokens"),
        "max_output_tokens": bound(50000, "tokens"),
        "raw_token_ceiling": bound(1000000, "tokens"),
        "max_cache_read_tokens": bound(1200000, "tokens"),
        "max_cache_write_tokens_by_ttl_class": {
            "ephemeral_5m": bound(160000, "tokens"),
            "ephemeral_1h": bound(40000, "tokens"),
        },
    }


# --------------------------------------------------------------------------- #
# Frozen enumerations, read live from the committed contracts                   #
#                                                                               #
# Never transcribed: FR-010a fails closed on an upstream membership change only  #
# if both the control under test and the validator read the same committed       #
# bytes, so a case that restated an enum would absorb the very drift it exists   #
# to catch.                                                                      #
# --------------------------------------------------------------------------- #

SCORE_BUNDLE_SCHEMA_PATH = CONTRACT_ROOT / "score-bundle.schema.json"
FREEZE_SCHEMA_PATH = CONTRACT_ROOT / "successor-capability-freeze.schema.json"
ASSIGNMENT_SCHEMA_PATH = CONTRACT_ROOT / "experiment-assignment.schema.json"
SHARED_CONTRACT_ROOT = TEST_ROOT / "layer6-efficiency" / "contracts"
SHARED_ENVIRONMENT_CONTRACT_PATH = SHARED_CONTRACT_ROOT / "environment-contract.schema.json"

POLICY_RESPONSES = ("escalate", "hold", "non_scorable")
SIGNAL_SOURCES = (
    "failure_code",
    "failure_plane",
    "retry_count",
    "budget_threshold",
    "terminal_state",
)


def frozen_terminal_states() -> list[str]:
    resource_vector = load_json(SCORE_BUNDLE_SCHEMA_PATH)["properties"]["resource_vector"]
    return list(resource_vector["properties"]["terminal_state"]["enum"])


def frozen_failure_planes() -> list[str]:
    return list(load_json(SCORE_BUNDLE_SCHEMA_PATH)["properties"]["failure_plane"]["enum"])


def frozen_failure_codes() -> list[str]:
    return list(load_json(SCORE_BUNDLE_SCHEMA_PATH)["properties"]["failure_code"]["enum"])


def frozen_pareto_dimensions() -> list[str]:
    return list(load_json(SCORE_BUNDLE_SCHEMA_PATH)["properties"]["resource_vector"]["required"])


def frozen_effort_ladder() -> list[str]:
    return list(load_json(FREEZE_SCHEMA_PATH)["$defs"]["tuple"]["properties"]["effort"]["enum"])


# The policy's response per failure plane. Authored per plane rather than per
# code because FR-010c.1 requires the plane map and the code map to agree under
# the frozen plane derivation, so a per-code authoring would have to re-derive
# the same partition by hand. treatment carries service_reroute, which FR-015a
# fixes at non_scorable; candidate carries the five bound-breach outcomes.
PLANE_RESPONSE: dict[str, str] = {
    "none": "hold",
    "gate": "hold",
    "treatment": "non_scorable",
    "fixture": "non_scorable",
    "scorer": "non_scorable",
    "ballot": "non_scorable",
    "adjudication": "non_scorable",
    "candidate": "escalate",
    "infrastructure": "non_scorable",
    "evidence_boundary": "non_scorable",
    "partition": "non_scorable",
    "schema": "non_scorable",
}


def synthetic_failure_code_response() -> dict[str, str]:
    return {code: PLANE_RESPONSE[failure_plane_for(code)] for code in frozen_failure_codes()}


def synthetic_terminal_state_response() -> dict[str, str]:
    """Non-completed states take the response of their paired candidate code."""
    codes = synthetic_failure_code_response()
    return {
        state: "hold" if state == "completed" else codes[f"candidate_{state}"]
        for state in frozen_terminal_states()
    }


# A synthetic successor-capability freeze: two efforts on one model plus a
# second model, so the ladder exercises the derived within-model rule and the
# authored cross-model rule at once. Names are deliberately generic — a route
# identifier is opaque to every rule under test.
LADDER_ROUTES = ("route-alpha-low", "route-alpha-high", "route-beta-medium")


def synthetic_freeze() -> dict[str, object]:
    tuples = [
        ("route-alpha-low", "model-alpha", "low"),
        ("route-alpha-high", "model-alpha", "high"),
        ("route-beta-medium", "model-beta", "medium"),
    ]
    return {
        "candidate_freeze_id": "sha256:" + "a" * 64,
        "freeze_digest": "sha256:" + "b" * 64,
        "admitted_tuples": [
            {
                "candidate_route_id": route,
                "model": model,
                "effort": effort,
                "source_evidence_digest": "sha256:" + "c" * 64,
                "runtime_evidence_digest": "sha256:" + "d" * 64,
            }
            for route, model, effort in tuples
        ],
        "excluded_tuples": [],
    }


def synthetic_unpinned() -> dict[str, object]:
    """FR-006: the pin rides the Claude-side experiment-assignment document."""
    return {
        "pinned_parent_binding": committed_binding("experiment-assignment.schema.json"),
        "pinned_parent_model": "model-alpha",
        "pinned_parent_effort": "high",
        "arm_count": 1,
        "model_resolution": "inherit",
    }


def synthetic_adaptive() -> dict[str, object]:
    freeze = synthetic_freeze()
    return {
        "candidate_freeze_id": freeze["candidate_freeze_id"],
        "freeze_digest": freeze["freeze_digest"],
        "escalation_ladder": list(LADDER_ROUTES),
        "escalation_ladder_rationales": [
            {
                "from_route": "route-alpha-high",
                "to_route": "route-beta-medium",
                "rationale": "cross-model rank is a declared capability judgment, not a derived one",
            }
        ],
        "max_escalations_per_objective": 1,
        "de_escalation_clean_pass_threshold": 3,
        "de_escalation_timing": "between_objectives",
        "terminal_state_response": synthetic_terminal_state_response(),
        "failure_plane_response": dict(PLANE_RESPONSE),
        "failure_code_response": synthetic_failure_code_response(),
        "signal_precedence": list(SIGNAL_SOURCES),
        "retry_count_response": {
            "threshold": 1,
            "direction": "at_or_above",
            "response": "escalate",
        },
        "budget_triggers": [
            {
                "member": "max_duration_seconds",
                "direction": "at_or_above",
                "threshold": 1200,
                "response": "escalate",
            }
        ],
        "clean_pass_definition": {
            "terminal_state": "completed",
            "failure_code": "none",
            "max_retries": 0,
            "budget_trigger_met": False,
        },
        "clean_pass_accounting": {
            "escalating_objective_counts": False,
            "non_scorable_objective_disposition": "neither_advances_nor_resets",
            "non_scorable_precedence": "outranks_reset_on_non_clean",
            "reset_on_de_escalation_evaluation": True,
            "first_entry_de_escalation": "no_step_and_no_wrap_around",
        },
    }


TOPOLOGY_DESCRIPTOR: dict[str, object] = {
    "topology_id": "car-004-parallel-fan-out",
    "fan_out": 3,
    "child_shape": {
        "dispatch_mechanism": "car_004_harness_child_dispatch",
        "wall_time_window": "full_elapsed_including_child_wait",
    },
}


def synthetic_orchestration_changing() -> dict[str, object]:
    return {
        "topology_descriptor": copy.deepcopy(TOPOLOGY_DESCRIPTOR),
        "topology_digest": record_digest(TOPOLOGY_DESCRIPTOR),
        "aggregation_rule": {
            "input_tokens": "sum",
            "cached_input_tokens": "sum",
            "output_tokens": "sum",
            "duration_ms": "sum",
            "retries": "sum",
            "compactions": "sum",
            "terminal_state": "worst_wins_by_severity",
            "acceptance": "parent_objective_oracle",
        },
        "raw_token_aggregation": {
            "input_tokens": "sum",
            "output_tokens": "sum",
            "cached_input_tokens": "sum",
            "reasoning_output_tokens": "sum",
        },
        "cache_aggregation": {
            "cache_write_tokens_by_ttl_class": {
                "ephemeral_5m": "sum",
                "ephemeral_1h": "sum",
            },
            "cache_read_tokens": "sum",
        },
        "unrecorded_quantity_disposition": "unobserved",
        "terminal_state_severity": [
            "completed",
            "failed",
            "timed_out",
            "cancelled",
            "budget_exhausted",
            "abandoned",
        ],
        "acceptance_rule": "parent_objective_oracle",
        "acceptance_floor_on_non_completed": 0,
    }


SPECIALIZATION_BUILDERS = {
    "unpinned": synthetic_unpinned,
    "adaptive": synthetic_adaptive,
    "orchestration_changing": synthetic_orchestration_changing,
}


def synthetic_control(kind: str, frozen_at: str = FROZEN_AT) -> dict[str, object]:
    scope = "per_unit" if kind == "orchestration_changing" else "per_objective"
    return {
        "control_id": f"car-004-{kind}",
        "control_kind": kind,
        "frozen_at": frozen_at,
        "execution_contract": {
            "dispatch_parameters": {"model_resolution": "inherit"},
            "observed_signals": ["terminal_state"],
            "retry_bounds": {
                "max_retries": 2,
                "counted_over": scope,
                "on_breach": {"terminal_state": "failed", "failure_code": "candidate_failed"},
            },
            "cancellation_bounds": {
                "max_duration_ms": 900000,
                "counted_over": scope,
                "on_breach": {
                    "terminal_state": "cancelled",
                    "failure_code": "candidate_cancelled",
                },
            },
        },
        "evidence_requirements": ["execution_trace"],
        "attribution_level": "policy",
        kind: SPECIALIZATION_BUILDERS[kind](),
    }


def control_of_kind(registry: dict[str, object], kind: str) -> dict[str, object]:
    return next(control for control in registry["controls"] if control["control_kind"] == kind)


def seal(registry: dict[str, object]) -> dict[str, object]:
    """Stamp every address under the frozen preimage rule, controls first."""
    for control in registry["controls"]:
        control.pop("control_digest", None)
        control["control_digest"] = record_digest(control, digest_field="control_digest")
    registry.pop("registry_digest", None)
    registry["registry_digest"] = record_digest(registry, digest_field="registry_digest")
    return registry


def synthetic_registry(frozen_at: str = FROZEN_AT) -> dict[str, object]:
    return seal({
        "schema_version": "1.0.0",
        "registry_id": "car-004-policy-control-registry",
        "status": "frozen",
        "frozen_at": frozen_at,
        "controls": [synthetic_control(kind, frozen_at) for kind in CONTROL_KINDS],
        "smoke_bounds": synthetic_smoke_bounds(),
        # A real committed binding, not a placeholder digest: validate_registry
        # recomputes these against the bound documents' bytes, so a stand-in
        # digest here would only prove the guard fires on the fixture.
        "car_003_bindings": [committed_binding("score-bundle.schema.json")],
    })


class RegistryIdentityAndClosureTests(unittest.TestCase):
    """FR-001, FR-002, FR-030a: one preimage rule, three controls, one identity."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.registry = synthetic_registry()

    def controls_by_kind(self, kind: str) -> dict[str, object]:
        return next(c for c in self.registry["controls"] if c["control_kind"] == kind)

    def test_a_control_address_is_the_frozen_preimage_over_its_own_record(self) -> None:
        for control in self.registry["controls"]:
            with self.subTest(control_kind=control["control_kind"]):
                self.assertEqual(
                    self.module.control_digest(control),
                    record_digest(control, digest_field="control_digest"),
                )
                self.assertEqual(self.module.control_digest(control), control["control_digest"])

    def test_a_control_preimage_drops_only_the_record_s_own_digest_member(self) -> None:
        control = self.controls_by_kind("adaptive")
        preimage = {key: value for key, value in control.items() if key != "control_digest"}
        self.assertEqual(
            self.module.control_digest(control),
            "sha256:" + hashlib.sha256(canonical_json(preimage).encode("utf-8")).hexdigest(),
        )

    def test_the_registry_and_every_control_carry_their_own_address(self) -> None:
        self.assertEqual(
            self.registry["registry_digest"],
            record_digest(self.registry, digest_field="registry_digest"),
        )
        self.assertEqual(len(self.registry["controls"]), 3)
        for control in self.registry["controls"]:
            with self.subTest(control_kind=control["control_kind"]):
                self.assertIn("control_digest", control)
        self.assertEqual(self.module.validate_registry(self.registry), self.registry)

    def test_a_timestamp_only_change_moves_every_address(self) -> None:
        # FR-002b: frozen_at is inside the preimage, so a re-issue that changes
        # nothing but the instant is a new identity rather than a silent re-use.
        reissued = synthetic_registry(frozen_at="2026-07-28T00:00:00Z")
        self.assertNotEqual(reissued["registry_digest"], self.registry["registry_digest"])
        for old, new in zip(self.registry["controls"], reissued["controls"]):
            with self.subTest(control_kind=old["control_kind"]):
                self.assertNotEqual(new["control_digest"], old["control_digest"])
        self.assertEqual(self.module.validate_registry(reissued), reissued)

    def test_a_recorded_address_that_does_not_recompute_is_refused(self) -> None:
        control = self.controls_by_kind("unpinned")
        control["evidence_requirements"] = ["execution_trace", "score_bundle"]
        with self.assertRaises(self.error):
            self.module.validate_registry(self.registry)

    def test_a_registry_address_that_does_not_recompute_is_refused(self) -> None:
        self.registry["registry_id"] = "car-004-policy-control-registry-v2"
        with self.assertRaises(self.error):
            self.module.validate_registry(self.registry)

    def test_a_frozen_at_that_is_not_a_z_suffixed_utc_instant_is_refused(self) -> None:
        for stamp in ("2026-07-27T00:00:00+02:00", "2026-07-27T00:00:00"):
            with self.subTest(frozen_at=stamp):
                registry = synthetic_registry(frozen_at=stamp)
                with self.assertRaises(self.error):
                    self.module.validate_registry(registry)

    def test_the_raw_token_identity_is_read_against_the_declared_ceiling(self) -> None:
        bounds = self.registry["smoke_bounds"]
        self.assertEqual(
            bounds["max_input_tokens"]["value"]
            + bounds["max_cached_input_tokens"]["value"]
            + bounds["max_output_tokens"]["value"],
            bounds["raw_token_ceiling"]["value"],
        )
        bounds["max_output_tokens"] = bound(50001, "tokens")
        with self.assertRaises(self.error):
            self.module.validate_registry(seal(self.registry))

    def test_an_identity_admitting_a_cache_ceiling_is_refused(self) -> None:
        # FR-016e.4: both cache quantities are diagnostics and stay outside the
        # identity, so a ceiling that only balances once one is added is refused.
        cases = {
            "cache_read": 1000000 + 1200000,
            "cache_write_class": 1000000 + 160000,
        }
        for label, ceiling in cases.items():
            with self.subTest(admits=label):
                registry = synthetic_registry()
                registry["smoke_bounds"]["raw_token_ceiling"] = bound(ceiling, "tokens")
                with self.assertRaises(self.error):
                    self.module.validate_registry(seal(registry))

    def test_a_smoke_bound_missing_its_value_unit_or_direction_is_refused(self) -> None:
        for dropped in ("value", "unit", "direction"):
            with self.subTest(dropped=dropped):
                registry = synthetic_registry()
                del registry["smoke_bounds"]["max_attempts"][dropped]
                with self.assertRaises(self.error):
                    self.module.validate_registry(seal(registry))

    def test_the_frozen_three_kinds_satisfy_closure(self) -> None:
        self.assertIsNone(self.module.assert_closed_at_three(self.registry))

    def test_a_seeded_fourth_control_is_refused(self) -> None:
        # SC-001: including a justified high-effort arm.
        fourth = synthetic_control("adaptive")
        fourth["control_id"] = "car-004-justified-high-effort"
        self.registry["controls"].append(fourth)
        with self.assertRaises(self.error):
            self.module.assert_closed_at_three(self.registry)
        with self.assertRaises(self.error):
            self.module.validate_registry(seal(self.registry))

    def test_a_duplicate_control_kind_is_refused(self) -> None:
        duplicate = synthetic_control("adaptive")
        duplicate["control_id"] = "car-004-adaptive-second"
        self.registry["controls"][0] = duplicate
        with self.assertRaises(self.error):
            self.module.assert_closed_at_three(self.registry)
        with self.assertRaises(self.error):
            self.module.validate_registry(seal(self.registry))

    def test_fewer_than_three_controls_is_refused(self) -> None:
        self.registry["controls"].pop()
        with self.assertRaises(self.error):
            self.module.assert_closed_at_three(self.registry)


# The frozen CAR-003 documents research D2 binds. Nothing in them is edited,
# re-versioned, or removed; each is referenced by stable identifier and digest.
BOUND_CAR_003_DOCUMENTS = (
    "score-bundle.schema.json",
    "successor-capability-freeze.schema.json",
    "analysis-plan.schema.json",
    "experiment-policy.schema.json",
    "role-corpus.schema.json",
    "experiment-assignment.schema.json",
)


def file_bytes_digest(path: Path) -> str:
    """FR-005a: the SHA-256 of a document's committed bytes."""
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def committed_binding(filename: str) -> dict[str, str]:
    path = CONTRACT_ROOT / filename
    return {"id": load_json(path)["$id"], "digest": file_bytes_digest(path)}


class Car003BindingTests(unittest.TestCase):
    """FR-005a and SC-018: additive-only references, checked against the bytes."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.document = {
            "car_003_bindings": [committed_binding(name) for name in BOUND_CAR_003_DOCUMENTS]
        }

    def test_every_recorded_binding_recomputes_the_bound_document_s_committed_bytes(self) -> None:
        self.assertIsNone(self.module.verify_car_003_bindings(self.document))

    def test_a_seeded_byte_change_in_a_bound_document_fails_the_check_closed(self) -> None:
        # The verifier compares a recorded digest against the committed bytes, so
        # a document whose bytes drifted by one character and a record whose
        # digest drifted by the same character are the same disagreement. Seeding
        # it on the record leaves the frozen CAR-003 documents untouched, which
        # FR-005 requires of every CAR-004 case.
        for index, filename in enumerate(BOUND_CAR_003_DOCUMENTS):
            with self.subTest(bound_document=filename):
                document = copy.deepcopy(self.document)
                seeded = (CONTRACT_ROOT / filename).read_bytes() + b"\n"
                document["car_003_bindings"][index]["digest"] = (
                    "sha256:" + hashlib.sha256(seeded).hexdigest()
                )
                with self.assertRaises(self.error):
                    self.module.verify_car_003_bindings(document)

    def test_a_binding_naming_no_committed_document_is_refused(self) -> None:
        self.document["car_003_bindings"].append(
            {
                "id": "https://racecraft.dev/schemas/car-003/absent-contract.schema.json",
                "digest": "sha256:" + "2" * 64,
            }
        )
        with self.assertRaises(self.error):
            self.module.verify_car_003_bindings(self.document)

    def test_a_document_declaring_no_bindings_is_refused(self) -> None:
        with self.assertRaises(self.error):
            self.module.verify_car_003_bindings({"registry_id": "car-004-no-bindings"})

    def test_the_file_bytes_digest_is_distinct_from_the_record_preimage(self) -> None:
        # FR-002a addresses a record's canonical JSON; FR-005a addresses a
        # document's committed bytes. Conflating them would let a reformat pass.
        path = CONTRACT_ROOT / "score-bundle.schema.json"
        self.assertNotEqual(
            file_bytes_digest(path), record_digest(load_json(path), digest_field=None)
        )

    def test_a_binding_is_data_and_never_a_schema_reference(self) -> None:
        # FR-004: the CAR-003 reference form is {id, digest}, never a $ref.
        for binding in self.document["car_003_bindings"]:
            with self.subTest(binding=binding["id"]):
                self.assertEqual(sorted(binding), ["digest", "id"])


class CodexRegistryFixtureTests(unittest.TestCase):
    """G56R-004 FR-001..FR-004: the Codex registry freezes IDs and digests."""

    def test_committed_codex_registry_schema_uses_the_g56r_namespace(self) -> None:
        self.assertTrue(
            CODEX_REGISTRY_SCHEMA_PATH.exists(),
            f"missing {CODEX_REGISTRY_SCHEMA_PATH.relative_to(REPO_ROOT)}",
        )
        schema = load_json(CODEX_REGISTRY_SCHEMA_PATH)
        self.assertEqual(schema["$schema"], JSON_SCHEMA_DIALECT)
        self.assertEqual(schema["$id"], CODEX_REGISTRY_SCHEMA_ID)

    def test_committed_codex_registry_fixture_freezes_ids_preimages_and_binding_drift(self) -> None:
        self.assertTrue(
            CODEX_REGISTRY_FIXTURE_PATH.exists(),
            f"missing {CODEX_REGISTRY_FIXTURE_PATH.relative_to(REPO_ROOT)}",
        )
        registry = load_json(CODEX_REGISTRY_FIXTURE_PATH)
        self.assertEqual(registry["registry_id"], CODEX_REGISTRY_ID)

        controls = registry["controls"]
        self.assertEqual(len(controls), 3)
        kinds = [control["control_kind"] for control in controls]
        self.assertEqual(sorted(kinds), sorted(CODEX_CONTROL_KINDS))
        self.assertEqual(len(set(kinds)), len(kinds))
        self.assertNotIn("orchestration_changing", kinds)

        for control in controls:
            with self.subTest(control_kind=control["control_kind"]):
                self.assertEqual(
                    control["control_id"],
                    CODEX_CONTROL_IDS_BY_KIND[control["control_kind"]],
                )
                self.assertEqual(
                    control["control_digest"],
                    record_digest(control, digest_field="control_digest"),
                )
                reissued = copy.deepcopy(control)
                reissued["frozen_at"] = "2026-07-29T00:00:00Z"
                self.assertNotEqual(
                    record_digest(reissued, digest_field="control_digest"),
                    control["control_digest"],
                )

        self.assertEqual(
            registry["registry_digest"],
            record_digest(registry, digest_field="registry_digest"),
        )
        self.assertGreater(len(registry["car_003_bindings"]), 0)

        drifted = copy.deepcopy(registry)
        first_binding = drifted["car_003_bindings"][0]
        original_digest = first_binding["digest"]
        drifted_digest = "sha256:" + "0" * 64
        if original_digest == drifted_digest:
            drifted_digest = "sha256:" + "1" * 64
        first_binding["digest"] = drifted_digest
        self.assertNotEqual(
            record_digest(drifted, digest_field="registry_digest"),
            registry["registry_digest"],
        )


class CodexUnpinnedControlTests(unittest.TestCase):
    """G56R-004 FR-008, FR-009, FR-037, and SC-015: inherited exact treatment."""

    def setUp(self) -> None:
        self.assertIsNotNone(codex_policy_controls, "codex_policy_controls is not importable")
        self.module = codex_policy_controls
        self.error = self.module.ControlContractError
        self.registry = load_json(CODEX_REGISTRY_FIXTURE_PATH)
        self.control = control_of_kind(self.registry, "unpinned")
        self.unpinned = self.control["unpinned"]

    def validate_control(self, control: dict[str, object]) -> object:
        self.assertTrue(
            hasattr(self.module, "validate_unpinned_control"),
            "T009 must expose validate_unpinned_control for Codex unpinned controls",
        )
        return self.module.validate_unpinned_control(control)

    def validate_exact_treatment(self, evidence: dict[str, object]) -> dict[str, object]:
        self.assertTrue(
            hasattr(self.module, "validate_unpinned_exact_treatment"),
            "T009 must read Codex unpinned exact treatment from produced evidence",
        )
        return self.module.validate_unpinned_exact_treatment(self.control, evidence)

    def exact_treatment_evidence(self, **overrides: object) -> dict[str, object]:
        evidence: dict[str, object] = {
            "read_back_from": "produced_evidence",
            "dispatch_intent": {"model_resolution": "inherit"},
            "produced_evidence": {
                "served_model": self.unpinned["pinned_parent_model"],
                "served_effort": self.unpinned["pinned_parent_effort"],
                "observed_absent_overrides": {
                    member: True for member in CODEX_REQUIRED_ABSENT_OVERRIDES
                },
            },
        }
        evidence.update(overrides)
        return evidence

    def test_the_unpinned_control_freezes_one_inherited_parent_arm(self) -> None:
        self.assertEqual(self.unpinned["arm_count"], 1)
        self.assertEqual(self.unpinned["model_resolution"], "inherit")
        self.assertEqual(
            self.control["execution_contract"]["dispatch_parameters"],
            {"model_resolution": "inherit"},
        )
        self.assertIsNone(self.validate_control(self.control))

        for arm_count in (0, 2):
            with self.subTest(arm_count=arm_count):
                control = copy.deepcopy(self.control)
                control["unpinned"]["arm_count"] = arm_count
                with self.assertRaises(self.error):
                    self.validate_control(control)

    def test_parent_context_identity_includes_every_frozen_parent_member(self) -> None:
        self.assertIsNone(self.validate_control(self.control))
        for member in (
            "pinned_parent_model",
            "pinned_parent_effort",
            "authentication_mode",
            "environment_boundary",
        ):
            with self.subTest(member=member):
                self.assertIn(member, self.unpinned)
        self.assertEqual(self.unpinned["authentication_mode"], "chatgpt_subscription")
        self.assertIn("client_version", self.unpinned["environment_boundary"])

        changed = copy.deepcopy(self.control)
        changed["unpinned"]["environment_boundary"]["client_version"] = "codex-client-repin"
        changed["control_digest"] = record_digest(changed, digest_field="control_digest")
        self.assertNotEqual(changed["control_digest"], self.control["control_digest"])
        self.assertIsNone(self.validate_control(changed))

    def test_required_local_overrides_are_closed_and_observed_absent(self) -> None:
        self.assertIsNone(self.validate_control(self.control))
        self.assertEqual(
            tuple(sorted(self.unpinned["required_absent_overrides"])),
            CODEX_REQUIRED_ABSENT_OVERRIDES,
        )
        evidence = self.exact_treatment_evidence()
        for override in CODEX_REQUIRED_ABSENT_OVERRIDES:
            with self.subTest(override=override):
                seeded = copy.deepcopy(evidence)
                seeded["produced_evidence"]["observed_absent_overrides"][override] = False
                with self.assertRaises(self.error):
                    self.validate_exact_treatment(seeded)

    def test_exact_treatment_is_read_back_from_produced_evidence(self) -> None:
        observed = self.validate_exact_treatment(self.exact_treatment_evidence())
        self.assertEqual(observed["read_back_from"], "produced_evidence")
        self.assertEqual(observed["served_model"], self.unpinned["pinned_parent_model"])
        self.assertEqual(observed["served_effort"], self.unpinned["pinned_parent_effort"])

        request_only = self.exact_treatment_evidence(read_back_from="dispatch_intent")
        with self.assertRaises(self.error):
            self.validate_exact_treatment(request_only)


class CodexAdaptiveLadderTests(unittest.TestCase):
    """G56R-004 FR-010, FR-011, FR-017, and SC-005: frozen Codex ladder."""

    def setUp(self) -> None:
        self.assertIsNotNone(codex_policy_controls, "codex_policy_controls is not importable")
        self.module = codex_policy_controls
        self.error = self.module.ControlContractError
        self.registry = load_json(CODEX_REGISTRY_FIXTURE_PATH)
        self.control = control_of_kind(self.registry, "adaptive")
        self.adaptive = self.control["adaptive"]
        self.freeze = self.successor_freeze()

    def validate_ladder(
        self, control: dict[str, object], freeze: dict[str, object]
    ) -> object:
        self.assertTrue(
            hasattr(self.module, "validate_adaptive_ladder"),
            "T011 must expose validate_adaptive_ladder for Codex adaptive controls",
        )
        return self.module.validate_adaptive_ladder(control, freeze)

    def successor_freeze(self, **overrides: object) -> dict[str, object]:
        ladder = list(self.adaptive["escalation_ladder"])
        tuples = [
            (ladder[0], "gpt-5.5", "medium"),
            (ladder[1], "gpt-5.5", "high"),
            (ladder[2], "gpt-5.6-terra", "high"),
        ]
        freeze: dict[str, object] = {
            "candidate_freeze_id": CODEX_G56R003_SUCCESSOR_FREEZE_ID,
            "freeze_digest": self.adaptive["freeze_digest"],
            "admitted_tuples": [
                {
                    "source_spec_id": "G56R-003",
                    "candidate_route_id": route_id,
                    "model": model,
                    "effort": effort,
                    "source_evidence_digest": CODEX_G56R003_ROUTE_EVIDENCE_DIGEST,
                    "runtime_evidence_digest": CODEX_G56R003_ROUTE_EVIDENCE_DIGEST,
                }
                for route_id, model, effort in tuples
            ],
            "excluded_tuples": [],
        }
        freeze.update(overrides)
        return freeze

    def test_the_adaptive_ladder_is_the_ordered_g56r003_successor_tuple_set(self) -> None:
        self.assertEqual(self.adaptive["candidate_freeze_id"], CODEX_G56R003_SUCCESSOR_FREEZE_ID)
        self.assertEqual(
            self.adaptive["escalation_ladder"],
            [tuple_["candidate_route_id"] for tuple_ in self.freeze["admitted_tuples"]],
        )
        self.assertTrue(
            all(tuple_["source_spec_id"] == "G56R-003" for tuple_ in self.freeze["admitted_tuples"])
        )
        self.assertIsNone(self.validate_ladder(self.control, self.freeze))

    def test_ladder_order_is_hash_relevant_and_declared(self) -> None:
        self.assertIsNone(self.validate_ladder(self.control, self.freeze))
        reordered = copy.deepcopy(self.control)
        first, second, third = reordered["adaptive"]["escalation_ladder"]
        reordered["adaptive"]["escalation_ladder"] = [second, first, third]
        reordered["control_digest"] = record_digest(reordered, digest_field="control_digest")
        self.assertNotEqual(reordered["control_digest"], self.control["control_digest"])
        with self.assertRaises(self.error):
            self.validate_ladder(reordered, self.freeze)

    def test_cross_model_steps_have_rationales_and_duplicate_or_omitted_routes_fail(self) -> None:
        self.assertIsNone(self.validate_ladder(self.control, self.freeze))
        rationale = self.adaptive["escalation_ladder_rationales"][0]
        self.assertEqual(
            (rationale["from_route"], rationale["to_route"]),
            (self.adaptive["escalation_ladder"][1], self.adaptive["escalation_ladder"][2]),
        )
        self.assertTrue(rationale["rationale"])

        for label, ladder in {
            "duplicate": [
                self.adaptive["escalation_ladder"][0],
                self.adaptive["escalation_ladder"][0],
                self.adaptive["escalation_ladder"][2],
            ],
            "omission": self.adaptive["escalation_ladder"][:-1],
        }.items():
            with self.subTest(case=label):
                control = copy.deepcopy(self.control)
                control["adaptive"]["escalation_ladder"] = list(ladder)
                with self.assertRaises(self.error):
                    self.validate_ladder(control, self.freeze)

    def test_successor_freeze_and_route_evidence_drift_invalidate_the_control(self) -> None:
        self.assertIsNone(self.validate_ladder(self.control, self.freeze))
        drifted_freeze = copy.deepcopy(self.freeze)
        drifted_freeze["freeze_digest"] = "sha256:" + "0" * 64
        with self.assertRaises(self.error):
            self.validate_ladder(self.control, drifted_freeze)

        drifted_route = copy.deepcopy(self.freeze)
        drifted_route["admitted_tuples"][0]["runtime_evidence_digest"] = "sha256:" + "1" * 64
        with self.assertRaises(self.error):
            self.validate_ladder(self.control, drifted_route)


class CodexAdaptiveSignalResolutionTests(unittest.TestCase):
    """G56R-004 FR-012, FR-013, and SC-006: Codex adaptive signal resolution."""

    def setUp(self) -> None:
        self.assertIsNotNone(codex_policy_controls, "codex_policy_controls is not importable")
        self.module = codex_policy_controls
        self.error = self.module.ControlContractError
        self.registry = load_json(CODEX_REGISTRY_FIXTURE_PATH)
        self.control = control_of_kind(self.registry, "adaptive")
        self.adaptive = self.control["adaptive"]

    def signal_validator(self) -> object:
        self.assertTrue(
            hasattr(self.module, "validate_adaptive_signal_maps"),
            "T013 must expose validate_adaptive_signal_maps for Codex adaptive controls",
        )
        return self.module.validate_adaptive_signal_maps

    def response_resolver(self) -> object:
        self.assertTrue(
            hasattr(self.module, "resolve_adaptive_response"),
            "T013 must expose resolve_adaptive_response for Codex adaptive rows",
        )
        return self.module.resolve_adaptive_response

    def clean_row(self, **overrides: object) -> dict[str, object]:
        row: dict[str, object] = {
            "terminal_state": "completed",
            "failure_plane": "none",
            "failure_code": "none",
            "retries": 0,
            "budget_observations": {"max_duration_seconds": 100},
        }
        row.update(overrides)
        return row

    def test_signal_sources_are_the_closed_frozen_observed_set(self) -> None:
        self.assertEqual(self.adaptive["signal_precedence"], list(SIGNAL_SOURCES))
        self.assertEqual(
            sorted(self.control["execution_contract"]["observed_signals"]),
            ["failure_code", "failure_plane", "retries", "terminal_state"],
        )
        self.assertEqual(
            [trigger["member"] for trigger in self.adaptive["budget_triggers"]],
            ["max_duration_seconds"],
        )
        self.assertIsNone(self.signal_validator()(self.control))

    def test_response_maps_are_total_single_valued_and_closed(self) -> None:
        cases = {
            "terminal_state_response": frozen_terminal_states(),
            "failure_plane_response": frozen_failure_planes(),
            "failure_code_response": frozen_failure_codes(),
        }
        for member, enum in cases.items():
            with self.subTest(map=member):
                self.assertEqual(sorted(self.adaptive[member]), sorted(enum))
                self.assertTrue(
                    all(response in POLICY_RESPONSES for response in self.adaptive[member].values())
                )
        self.assertIsNone(self.signal_validator()(self.control))

    def test_resolution_uses_the_declared_precedence_order(self) -> None:
        resolver = self.response_resolver()
        row = self.clean_row(
            failure_code="candidate_failed",
            failure_plane="candidate",
            retries=3,
            budget_observations={"max_duration_seconds": 1800},
        )
        self.assertEqual(resolver(self.control, row), "escalate")

        lower_source = self.clean_row(failure_plane="candidate")
        self.assertEqual(resolver(self.control, lower_source), "escalate")

    def test_failure_plane_and_code_responses_stay_consistent(self) -> None:
        for code in frozen_failure_codes():
            with self.subTest(failure_code=code):
                self.assertEqual(
                    self.adaptive["failure_plane_response"][failure_plane_for(code)],
                    self.adaptive["failure_code_response"][code],
                )
        self.assertIsNone(self.signal_validator()(self.control))

    def test_terminal_states_match_their_candidate_failure_codes(self) -> None:
        codes = frozen_failure_codes()
        for state in frozen_terminal_states():
            if state == "completed":
                continue
            with self.subTest(terminal_state=state):
                paired = f"candidate_{state}"
                self.assertIn(paired, codes)
                self.assertEqual(
                    self.adaptive["terminal_state_response"][state],
                    self.adaptive["failure_code_response"][paired],
                )
        self.assertIsNone(self.signal_validator()(self.control))

    def test_unknown_closed_domain_values_fail_before_resolution(self) -> None:
        resolver = self.response_resolver()
        cases = (
            {"failure_code": "route_repointed"},
            {"failure_plane": "routing"},
            {"terminal_state": "quiesced"},
        )
        for seeded in cases:
            with self.subTest(**seeded):
                with self.assertRaises(self.error):
                    resolver(self.control, self.clean_row(**seeded))


class CodexAdaptiveMovementAndBreachTests(unittest.TestCase):
    """G56R-004 FR-014 through FR-016 and SC-007: Codex adaptive replay semantics."""

    def setUp(self) -> None:
        self.assertIsNotNone(codex_policy_controls, "codex_policy_controls is not importable")
        self.module = codex_policy_controls
        self.error = self.module.ControlContractError
        self.registry = load_json(CODEX_REGISTRY_FIXTURE_PATH)
        self.control = control_of_kind(self.registry, "adaptive")
        self.adaptive = self.control["adaptive"]
        self.ladder = list(self.adaptive["escalation_ladder"])

    def state(
        self, route_index: int = 0, clean_streak: int = 0, escalations_used: int = 0
    ) -> dict[str, object]:
        return {
            "objective_id": "g56r-004-objective-1",
            "current_route_id": self.ladder[route_index],
            "clean_streak": clean_streak,
            "escalations_used": escalations_used,
        }

    def row(self, **overrides: object) -> dict[str, object]:
        row: dict[str, object] = {
            "objective_id": "g56r-004-objective-1",
            "terminal_state": "completed",
            "failure_plane": "none",
            "failure_code": "none",
            "retries": 0,
            "budget_observations": {"max_duration_seconds": 100},
        }
        row.update(overrides)
        return row

    def attempt(self, route_id: str, retries: int, duration_ms: int) -> dict[str, object]:
        return {
            "attempt_id": f"{route_id}-{retries}-{duration_ms}",
            "route_id": route_id,
            "retries": retries,
            "duration_ms": duration_ms,
        }

    def bounded_objective(
        self,
        attempts: list[dict[str, object]],
        **overrides: object,
    ) -> dict[str, object]:
        row: dict[str, object] = {
            "objective_id": "g56r-004-objective-1",
            "counted_over": self.control["execution_contract"]["retry_bounds"]["counted_over"],
            "attempts": attempts,
            "budget_observations": {"max_duration_seconds": 100},
        }
        row.update(overrides)
        return row

    def state_advancer(self) -> object:
        self.assertTrue(
            hasattr(self.module, "advance_adaptive_state"),
            "T015 must expose advance_adaptive_state for Codex adaptive movement replay",
        )
        return self.module.advance_adaptive_state

    def bounds_evaluator(self) -> object:
        self.assertTrue(
            hasattr(self.module, "evaluate_adaptive_bounds"),
            "T015 must expose evaluate_adaptive_bounds for Codex retry and cancellation replay",
        )
        return self.module.evaluate_adaptive_bounds

    def reroute_classifier(self) -> object:
        self.assertTrue(
            hasattr(self.module, "classify_adaptive_service_reroute"),
            "T015 must expose classify_adaptive_service_reroute for Codex platform reroutes",
        )
        return self.module.classify_adaptive_service_reroute

    def test_at_most_one_escalation_is_spent_per_objective(self) -> None:
        advance = self.state_advancer()
        failure = self.row(failure_code="candidate_failed", failure_plane="candidate")
        first = advance(self.control, self.state(route_index=0), failure)
        self.assertTrue(first["escalated"])
        self.assertEqual(first["current_route_id"], self.ladder[1])
        self.assertEqual(first["escalations_used"], 1)
        self.assertEqual(
            first["escalation_step"],
            {"from_route_id": self.ladder[0], "to_route_id": self.ladder[1]},
        )

        second = advance(self.control, first, failure)
        self.assertFalse(second["escalated"])
        self.assertEqual(second["current_route_id"], self.ladder[1])
        self.assertEqual(second["escalations_used"], 1)

    def test_floor_and_ceiling_do_not_wrap_when_movement_is_due(self) -> None:
        advance = self.state_advancer()
        ceiling = advance(
            self.control,
            self.state(route_index=len(self.ladder) - 1),
            self.row(failure_code="candidate_failed", failure_plane="candidate"),
        )
        self.assertFalse(ceiling["escalated"])
        self.assertEqual(ceiling["current_route_id"], self.ladder[-1])
        self.assertNotEqual(ceiling["current_route_id"], self.ladder[0])

        floor = advance(self.control, self.state(route_index=0, clean_streak=2), self.row())
        self.assertTrue(floor["de_escalation_evaluated"])
        self.assertFalse(floor["de_escalated"])
        self.assertEqual(floor["current_route_id"], self.ladder[0])
        self.assertEqual(floor["clean_streak"], 0)
        self.assertNotEqual(floor["current_route_id"], self.ladder[-1])

    def test_three_clean_passes_de_escalate_between_objectives(self) -> None:
        advance = self.state_advancer()
        carried = self.state(route_index=1)
        for _ in range(2):
            carried = advance(self.control, carried, self.row())
            self.assertFalse(carried["de_escalated"])
        carried = advance(self.control, carried, self.row())
        self.assertTrue(carried["de_escalation_evaluated"])
        self.assertTrue(carried["de_escalated"])
        self.assertEqual(carried["current_route_id"], self.ladder[0])
        self.assertEqual(carried["clean_streak"], 0)

    def test_non_scorable_rows_do_not_advance_or_reset_the_clean_streak(self) -> None:
        advance = self.state_advancer()
        reroute = self.row(
            terminal_state="failed",
            failure_code="service_reroute",
            failure_plane="treatment",
            retries=3,
        )
        carried = advance(self.control, self.state(route_index=1, clean_streak=2), reroute)
        self.assertTrue(carried["excluded"])
        self.assertFalse(carried["clean_pass"])
        self.assertEqual(carried["clean_streak"], 2)
        self.assertEqual(carried["current_route_id"], self.ladder[1])

        final = advance(self.control, carried, self.row())
        self.assertTrue(final["de_escalated"])
        self.assertEqual(final["current_route_id"], self.ladder[0])

    def test_retry_and_cancellation_breaches_record_only_their_declared_pairings(self) -> None:
        evaluate = self.bounds_evaluator()
        retry_bounds = self.control["execution_contract"]["retry_bounds"]
        cancellation_bounds = self.control["execution_contract"]["cancellation_bounds"]

        respected = evaluate(
            self.control,
            self.bounded_objective([
                self.attempt(self.ladder[0], retry_bounds["max_retries"], 1000)
            ]),
        )
        self.assertFalse(respected["retry_bound_breached"])
        self.assertFalse(respected["cancellation_bound_breached"])
        self.assertIsNone(respected["terminal_state"])
        self.assertIsNone(respected["failure_code"])

        retry_breach = evaluate(
            self.control,
            self.bounded_objective([
                self.attempt(self.ladder[0], retry_bounds["max_retries"] + 1, 1000)
            ]),
        )
        self.assertTrue(retry_breach["retry_bound_breached"])
        self.assertEqual(retry_breach["terminal_state"], "failed")
        self.assertEqual(retry_breach["failure_code"], "candidate_failed")

        cancellation_breach = evaluate(
            self.control,
            self.bounded_objective([
                self.attempt(self.ladder[0], 0, cancellation_bounds["max_duration_ms"] + 1)
            ]),
        )
        self.assertTrue(cancellation_breach["cancellation_bound_breached"])
        self.assertEqual(cancellation_breach["terminal_state"], "cancelled")
        self.assertEqual(cancellation_breach["failure_code"], "candidate_cancelled")

    def test_budget_triggers_resolve_by_response_not_on_breach_pairing(self) -> None:
        evaluate = self.bounds_evaluator()
        trigger = self.adaptive["budget_triggers"][0]
        reading = evaluate(
            self.control,
            self.bounded_objective(
                [self.attempt(self.ladder[0], 0, 1000)],
                budget_observations={trigger["member"]: trigger["threshold"]},
            ),
        )
        self.assertTrue(reading["budget_trigger_met"])
        self.assertEqual(reading["budget_response"], trigger["response"])
        self.assertFalse(reading["retry_bound_breached"])
        self.assertFalse(reading["cancellation_bound_breached"])
        self.assertIsNone(reading["terminal_state"])
        self.assertIsNone(reading["failure_code"])

    def test_service_reroute_is_non_scorable_without_spending_movement(self) -> None:
        from claude_score_bundle import SERVICE_REROUTE_DISPOSITION_REASON

        classify = self.reroute_classifier()
        classified = classify(
            self.control,
            self.state(route_index=1, clean_streak=2),
            self.row(failure_code="service_reroute", failure_plane="treatment"),
        )
        self.assertTrue(classified["service_reroute"])
        self.assertEqual(classified["response"], "non_scorable")
        self.assertFalse(classified["escalation_allowance_spent"])
        self.assertFalse(classified["ladder_position_changed"])
        self.assertEqual(classified["current_route_id"], self.ladder[1])
        self.assertEqual(classified["clean_streak"], 2)
        self.assertTrue(classified["unit_non_scorable"])
        self.assertEqual(classified["failure_plane"], failure_plane_for("service_reroute"))
        self.assertEqual(classified["disposition_reason"], SERVICE_REROUTE_DISPOSITION_REASON)


class CodexJustifiedHighEffortControlTests(unittest.TestCase):
    """G56R-004 FR-018, FR-019, FR-023, SC-008, and SC-015: fixed high-effort route."""

    def setUp(self) -> None:
        self.assertIsNotNone(codex_policy_controls, "codex_policy_controls is not importable")
        self.module = codex_policy_controls
        self.error = self.module.ControlContractError
        self.registry = load_json(CODEX_REGISTRY_FIXTURE_PATH)
        self.control = control_of_kind(self.registry, "justified_high_effort")

    def validate_control(self, control: dict[str, object]) -> dict[str, object]:
        self.assertTrue(
            hasattr(self.module, "validate_justified_high_effort_control"),
            "T017 must expose validate_justified_high_effort_control for Codex high effort",
        )
        return self.module.validate_justified_high_effort_control(control)

    def validate_exact_treatment(self, evidence: dict[str, object]) -> dict[str, object]:
        self.assertTrue(
            hasattr(self.module, "validate_justified_high_effort_exact_treatment"),
            "T017 must read justified-high-effort exact treatment from produced evidence",
        )
        return self.module.validate_justified_high_effort_exact_treatment(
            self.control, evidence
        )

    def exact_treatment_evidence(self, **overrides: object) -> dict[str, object]:
        evidence: dict[str, object] = {
            "read_back_from": "produced_evidence",
            "dispatch_request": {
                "route_id": CODEX_JUSTIFIED_HIGH_EFFORT_ROUTE_ID,
                "model": CODEX_JUSTIFIED_HIGH_EFFORT_MODEL,
                "effort": CODEX_JUSTIFIED_HIGH_EFFORT_EFFORT,
            },
            "produced_evidence": {
                "served_route_id": CODEX_JUSTIFIED_HIGH_EFFORT_ROUTE_ID,
                "served_model": CODEX_JUSTIFIED_HIGH_EFFORT_MODEL,
                "served_effort": CODEX_JUSTIFIED_HIGH_EFFORT_EFFORT,
                "successor_freeze_digest": CODEX_G56R003_SUCCESSOR_FREEZE_ID,
                "route_evidence_digest": CODEX_G56R003_ROUTE_EVIDENCE_DIGEST,
                "eligibility_predicate_result": True,
                "eligibility_rationale_binding": "required_core_workspace_write_phase_executor",
                "fallback_route_id": None,
                "dynamic_route_discovery": False,
                "parent_plus_child_aggregate": {
                    "input_tokens": 1,
                    "cached_input_tokens": 0,
                    "output_tokens": 1,
                    "duration_ms": 1,
                    "retries": 0,
                    "compactions": 0,
                    "terminal_state": "completed",
                    "acceptance": 1,
                },
            },
        }
        evidence.update(overrides)
        return evidence

    def test_the_control_binds_one_frozen_g56r003_phase_executor_route(self) -> None:
        binding = self.validate_control(self.control)
        self.assertEqual(binding["route_id"], CODEX_JUSTIFIED_HIGH_EFFORT_ROUTE_ID)
        self.assertEqual(binding["model"], CODEX_JUSTIFIED_HIGH_EFFORT_MODEL)
        self.assertEqual(binding["effort"], CODEX_JUSTIFIED_HIGH_EFFORT_EFFORT)
        self.assertEqual(binding["successor_freeze_digest"], CODEX_G56R003_SUCCESSOR_FREEZE_ID)
        self.assertEqual(binding["route_evidence_digest"], CODEX_G56R003_ROUTE_EVIDENCE_DIGEST)

    def test_eligibility_predicate_rationale_and_no_fallback_are_declared(self) -> None:
        binding = self.validate_control(self.control)
        self.assertIs(binding["eligibility_predicate"]["result"], True)
        self.assertIn("required_core", binding["eligibility_predicate"]["predicate_id"])
        self.assertIn("workspace_write", binding["eligibility_predicate"]["predicate_id"])
        self.assertTrue(binding["eligibility_rationale"].strip())
        self.assertIsNone(binding["fallback_route_id"])
        self.assertIs(binding["dynamic_route_discovery"], False)

    def test_ineligible_or_fallback_seeded_controls_are_refused(self) -> None:
        self.assertIsNotNone(self.validate_control(self.control))
        seeded_cases = (
            ("predicate_false", {"eligibility_predicate": {"result": False}}),
            ("empty_rationale", {"eligibility_rationale": ""}),
            ("fallback_route", {"fallback_route_id": "g56r-003-route-fallback"}),
            ("dynamic_discovery", {"dynamic_route_discovery": True}),
        )
        for label, seeded in seeded_cases:
            with self.subTest(case=label):
                control = copy.deepcopy(self.control)
                control["justified_high_effort"].update(seeded)
                with self.assertRaises(self.error):
                    self.validate_control(control)

    def test_exact_treatment_is_read_back_from_produced_evidence(self) -> None:
        observed = self.validate_exact_treatment(self.exact_treatment_evidence())
        self.assertEqual(observed["read_back_from"], "produced_evidence")
        self.assertEqual(observed["served_route_id"], CODEX_JUSTIFIED_HIGH_EFFORT_ROUTE_ID)
        self.assertEqual(observed["served_model"], CODEX_JUSTIFIED_HIGH_EFFORT_MODEL)
        self.assertEqual(observed["served_effort"], CODEX_JUSTIFIED_HIGH_EFFORT_EFFORT)
        self.assertIs(observed["eligibility_predicate_result"], True)
        self.assertEqual(
            observed["route_evidence_digest"], CODEX_G56R003_ROUTE_EVIDENCE_DIGEST
        )
        self.assertIn("parent_plus_child_aggregate", observed)

        request_only = self.exact_treatment_evidence(read_back_from="dispatch_request")
        with self.assertRaises(self.error):
            self.validate_exact_treatment(request_only)


def codex_unit_member(
    row_id: str,
    spawned_by: str | None = None,
    *,
    cost: int = 10,
    terminal_state: str = "completed",
    acceptance: float | None = 1.0,
    raw: tuple[int, int, int, int | None] = (100, 20, 30, 5),
    cache: tuple[int, int, int] | None = (7, 3, 40),
) -> dict[str, object]:
    member: dict[str, object] = {
        "row_id": row_id,
        "spawned_by": spawned_by,
        "resource_vector": {
            "input_tokens": cost,
            "cached_input_tokens": cost,
            "output_tokens": cost,
            "duration_ms": cost,
            "retries": cost,
            "compactions": cost,
            "terminal_state": terminal_state,
            "acceptance": acceptance,
        },
        "raw_token_vector": {
            "input_tokens": raw[0],
            "output_tokens": raw[1],
            "cached_input_tokens": raw[2],
            "reasoning_output_tokens": raw[3],
        },
    }
    if cache is not None:
        member["cache_diagnostic"] = {
            "cache_write_tokens_by_ttl_class": {
                "ephemeral_5m": cache[0],
                "ephemeral_1h": cache[1],
            },
            "cache_read_tokens": cache[2],
        }
    return member


class CodexParentPlusChildrenAggregationTests(unittest.TestCase):
    """G56R-004 FR-020 through FR-022 and SC-009: governed unit aggregation."""

    def setUp(self) -> None:
        self.assertIsNotNone(codex_policy_controls, "codex_policy_controls is not importable")
        self.module = codex_policy_controls
        self.error = self.module.ControlContractError
        self.registry = load_json(CODEX_REGISTRY_FIXTURE_PATH)
        self.control = control_of_kind(self.registry, "justified_high_effort")

    def aggregate(self, members: list[dict[str, object]]) -> dict[str, object]:
        self.assertTrue(
            hasattr(self.module, "aggregate_parent_plus_children"),
            "T019 must expose aggregate_parent_plus_children for Codex governed evidence",
        )
        return self.module.aggregate_parent_plus_children(self.control, members)

    def test_children_are_included_across_all_eight_decision_dimensions(self) -> None:
        aggregate = self.aggregate([
            codex_unit_member("parent", cost=10, acceptance=0.92),
            codex_unit_member("child-1", "parent", cost=3),
            codex_unit_member("child-2", "parent", cost=5),
        ])
        self.assertEqual(aggregate["unit_member_ids"], ["parent", "child-1", "child-2"])
        for dimension in (
            "input_tokens",
            "cached_input_tokens",
            "output_tokens",
            "duration_ms",
            "retries",
            "compactions",
        ):
            with self.subTest(dimension=dimension):
                self.assertEqual(aggregate["decision_dimensions"][dimension], 18)
        self.assertEqual(aggregate["decision_dimensions"]["terminal_state"], "completed")
        self.assertEqual(aggregate["decision_dimensions"]["acceptance"], 0.92)

    def test_null_acceptance_floor_and_missing_terminal_state_are_handled_explicitly(self) -> None:
        completed_gap = self.aggregate([
            codex_unit_member("parent", acceptance=None),
            codex_unit_member("child-1", "parent"),
        ])
        self.assertIsNone(completed_gap["decision_dimensions"]["acceptance"])

        failed = self.aggregate([
            codex_unit_member("parent", acceptance=None),
            codex_unit_member("child-1", "parent", terminal_state="failed"),
        ])
        self.assertEqual(failed["decision_dimensions"]["terminal_state"], "failed")
        self.assertEqual(failed["decision_dimensions"]["acceptance"], 0)

        malformed = codex_unit_member("child-2", "parent")
        del malformed["resource_vector"]["terminal_state"]
        with self.assertRaises(self.error):
            self.aggregate([codex_unit_member("parent"), malformed])

    def test_raw_tokens_and_cache_diagnostics_preserve_their_member_sets(self) -> None:
        aggregate = self.aggregate([
            codex_unit_member("parent"),
            codex_unit_member("child-1", "parent", raw=(200, 40, 60, 11), cache=(13, 5, 80)),
        ])
        self.assertEqual(
            aggregate["raw_tokens"],
            {
                "input_tokens": 300,
                "output_tokens": 60,
                "cached_input_tokens": 90,
                "reasoning_output_tokens": 16,
            },
        )
        self.assertEqual(
            aggregate["cache_write_tokens_by_ttl_class"],
            {"ephemeral_5m": 20, "ephemeral_1h": 8},
        )
        self.assertEqual(aggregate["cache_read_tokens"], 120)
        replay_case = load_json(CODEX_REPLAY_CASES_PATH)["aggregation_cases"][0]
        self.assertEqual(self.aggregate(replay_case["members"]), replay_case["expected"])

    def test_missing_or_null_cache_diagnostics_remain_unobserved_not_zero(self) -> None:
        no_cache = self.aggregate([
            codex_unit_member("parent"),
            codex_unit_member("child-1", "parent", cache=None),
        ])
        self.assertIsNone(no_cache["cache_read_tokens"])
        self.assertIsNone(no_cache["cache_write_tokens_by_ttl_class"])
        self.assertEqual(
            sorted(no_cache["unobserved"]),
            ["max_cache_read_tokens", "max_cache_write_tokens_by_ttl_class"],
        )

        null_cache = codex_unit_member("child-2", "parent")
        null_cache["cache_diagnostic"]["cache_read_tokens"] = None
        aggregate = self.aggregate([codex_unit_member("parent"), null_cache])
        self.assertIsNone(aggregate["cache_read_tokens"])
        self.assertIn("max_cache_read_tokens", aggregate["unobserved"])
        self.assertNotEqual(aggregate["cache_read_tokens"], 0)


class CodexReservedPartitionArtifactTests(unittest.TestCase):
    """T024 RED: the partition fixture and its smoke guard must be published."""

    def test_the_codex_partition_fixture_and_smoke_guard_are_present(self) -> None:
        self.assertTrue(
            CODEX_PARTITION_FIXTURE_PATH.is_file(),
            f"{CODEX_PARTITION_FIXTURE_PATH} is missing; T025 must publish it",
        )
        self.assertIsNotNone(
            codex_control_smoke,
            "codex_control_smoke is not importable; T025 must implement it",
        )


class CodexReservedPartitionTests(unittest.TestCase):
    """G56R-004 FR-031 through FR-033 and SC-012: reserved-objective refusal."""

    def setUp(self) -> None:
        self.assertIsNotNone(codex_policy_controls, "codex_policy_controls is not importable")
        self.assertIsNotNone(
            codex_control_smoke,
            "codex_control_smoke is not importable; T025 must implement it",
        )
        self.module = codex_policy_controls
        self.smoke_module = codex_control_smoke
        self.error = self.module.ControlContractError
        fixture = load_json(CODEX_PARTITION_FIXTURE_PATH)
        self.entries = fixture["entries"]
        self.reserved = next(
            entry for entry in self.entries if entry["qualification_eligible"]
        )
        self.smoke = next(
            entry for entry in self.entries if not entry["qualification_eligible"]
        )

    def test_both_entries_are_content_addressed_by_the_frozen_partition_builder(self) -> None:
        self.assertEqual(
            [entry["partition_id"] for entry in self.entries],
            ["G56R-011-RESERVED-COMPARISON", "G56R-004-SMOKE"],
        )
        for entry in self.entries:
            with self.subTest(partition=entry["partition_id"]):
                rebuilt = build_partition_registry_entry(
                    partition_id=entry["partition_id"],
                    partition_type=entry["partition_type"],
                    qualification_eligible=entry["qualification_eligible"],
                    objective_ids=entry["objective_ids"],
                    frozen_at=entry["frozen_at"],
                    owning_spec=entry["owning_spec"],
                )
                self.assertEqual(entry, rebuilt)
                self.assertEqual(entry["owning_spec"], "G56R-004")

    def test_the_entries_register_clean_and_are_mutually_disjoint(self) -> None:
        verdict = register_partitions(self.entries)
        self.assertTrue(verdict.ok, verdict.findings)
        self.assertFalse(
            set(self.reserved["objective_ids"]) & set(self.smoke["objective_ids"])
        )
        intruder = build_partition_registry_entry(
            partition_id="G56R-004-SEEDED-OVERLAP",
            partition_type="calibration",
            qualification_eligible=False,
            objective_ids=[self.reserved["objective_ids"][0]],
            frozen_at=self.smoke["frozen_at"],
            owning_spec="G56R-004",
        )
        self.assertFalse(register_partitions([*self.entries, intruder]).ok)

    def test_partition_owned_category_one_to_six_members_are_reported(self) -> None:
        report = self.module.partition_owned_mirror_members(
            handoff_path=REPO_ROOT
            / "docs"
            / "ai"
            / "specs"
            / ".process"
            / "CAR-004-twin-handoff.md",
            fixture_path=CODEX_PARTITION_FIXTURE_PATH,
        )
        self.assertEqual(report["categories_present"], [4])
        self.assertEqual(
            report["partition_ids"],
            ["G56R-004-SMOKE", "G56R-011-RESERVED-COMPARISON"],
        )
        self.assertEqual(report["missing"], [])
        self.assertEqual(report["extra"], [])
        self.assertEqual(report["drifted"], [])

    def test_replay_guard_refuses_a_reserved_objective(self) -> None:
        clean = {
            "row_id": "replay-clean",
            "objective_id": self.smoke["objective_ids"][0],
            "outcome_bearing": False,
            "partition_type": "calibration",
            "scored": False,
        }
        self.assertIsNone(
            self.module.assert_reserved_partition_untouched([clean], self.reserved)
        )
        seeded = dict(clean, objective_id=self.reserved["objective_ids"][0])
        with self.assertRaises(self.error):
            self.module.assert_reserved_partition_untouched([seeded], self.reserved)

    def test_smoke_plan_uses_only_non_scored_calibration_objectives(self) -> None:
        planned = self.smoke_module.plan_objectives(self.entries)
        self.assertEqual(planned, tuple(sorted(self.smoke["objective_ids"])))
        self.assertFalse(set(planned) & set(self.reserved["objective_ids"]))
        with self.assertRaises(self.error):
            self.smoke_module.guard_plan_objectives(
                [*planned, self.reserved["objective_ids"][0]],
                self.entries,
            )

    def test_smoke_seal_refuses_reserved_scored_selection_and_cohort_consumption(self) -> None:
        clean = {
            "objective_ids": [self.smoke["objective_ids"][0]],
            "outcome_bearing": False,
            "partition_id": self.smoke["partition_id"],
            "partition_type": "calibration",
            "scored": False,
        }
        self.assertIsNone(self.smoke_module.guard_smoke_record(clean, self.entries))
        seeded_cases = (
            dict(clean, objective_ids=[self.reserved["objective_ids"][0]]),
            dict(clean, scored=True),
            dict(clean, outcome_bearing=True),
            dict(clean, partition_type="selection"),
            dict(clean, partition_type="cohort_lock"),
        )
        for seeded in seeded_cases:
            with self.subTest(seeded=seeded):
                with self.assertRaises(self.error):
                    self.smoke_module.guard_smoke_record(seeded, self.entries)


class CodexDeterministicReplayTests(unittest.TestCase):
    """T026 RED: all three Codex controls must replay from governed fixture rows."""

    def setUp(self) -> None:
        self.assertIsNotNone(codex_policy_controls, "codex_policy_controls is not importable")
        self.module = codex_policy_controls
        self.error = self.module.ControlContractError
        self.replay_fixture = load_json(CODEX_REPLAY_CASES_PATH)

    def replay(self) -> list[dict[str, object]]:
        self.assertTrue(
            hasattr(self.module, "replay_codex_controls"),
            "T027 must expose replay_codex_controls for deterministic G56R-004 replay",
        )
        return self.module.replay_codex_controls(CODEX_REPLAY_CASES_PATH)

    def replay_api(self) -> object:
        self.assertTrue(
            hasattr(self.module, "replay_codex_controls"),
            "T027 must expose replay_codex_controls for deterministic G56R-004 replay",
        )
        return self.module.replay_codex_controls

    def test_replay_fixture_declares_a_case_for_every_codex_control_kind(self) -> None:
        cases = self.replay_fixture.get("control_replay_cases", [])
        self.assertEqual(
            sorted(case["control_kind"] for case in cases),
            sorted(CODEX_CONTROL_KINDS),
        )
        self.assertEqual(
            sorted(case["control_id"] for case in cases),
            sorted(CODEX_CONTROL_IDS_BY_KIND.values()),
        )

    def test_two_replays_of_the_committed_fixture_are_byte_identical(self) -> None:
        first = self.replay()
        second = self.replay()
        self.assertEqual(canonical_json(first), canonical_json(second))
        self.assertEqual(record_digest({"replay": first}), record_digest({"replay": second}))

    def test_every_replayed_row_is_governed_non_scored_and_not_outcome_bearing(self) -> None:
        for outcome in self.replay():
            with self.subTest(case_id=outcome["case_id"]):
                self.assertIn(outcome["control_kind"], CODEX_CONTROL_KINDS)
                self.assertEqual(outcome["control_id"], CODEX_CONTROL_IDS_BY_KIND[outcome["control_kind"]])
                self.assertEqual(outcome["partition_type"], "calibration")
                self.assertFalse(outcome["scored"])
                self.assertFalse(outcome["outcome_bearing"])
                self.assertTrue(outcome["governed_evidence"])
                self.assertEqual(outcome["governed_evidence"]["source"], "committed_fixture")
                self.assertTrue(str(outcome["governed_evidence"]["digest"]).startswith("sha256:"))

    def test_seeded_outcome_bearing_or_scored_rows_fail_replay_closed(self) -> None:
        replay = self.replay_api()
        cases = copy.deepcopy(self.replay_fixture)
        cases.setdefault("control_replay_cases", [{}])
        for field in ("outcome_bearing", "scored"):
            with self.subTest(field=field):
                mutated = copy.deepcopy(cases)
                mutated["control_replay_cases"][0][field] = True
                with tempfile.TemporaryDirectory() as directory:
                    seeded_path = Path(directory) / "replay-cases.json"
                    seeded_path.write_text(
                        json.dumps(mutated, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    with self.assertRaises(self.error):
                        replay(seeded_path)

    def test_replay_refuses_self_consistent_copy_with_changed_case_id_and_objective(self) -> None:
        replay = self.replay_api()
        mutated = copy.deepcopy(self.replay_fixture)
        mutated["control_replay_cases"][0]["case_id"] = (
            "unpinned-non-live-control-replay-copy"
        )
        mutated["control_replay_cases"][0]["objective_id"] = "G56R-004-SMOKE-OBJ-04"

        with tempfile.TemporaryDirectory() as directory:
            seeded_path = Path(directory) / "replay-cases.json"
            seeded_path.write_text(
                json.dumps(mutated, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(self.error, "replay fixture"):
                replay(seeded_path)


class CodexControlSmokePlanAndSealTests(unittest.TestCase):
    """T028 RED: non-live Codex smoke plan and seal semantics."""

    def setUp(self) -> None:
        self.assertIsNotNone(codex_policy_controls, "codex_policy_controls is not importable")
        self.assertIsNotNone(codex_control_smoke, "codex_control_smoke is not importable")
        self.controls = codex_policy_controls
        self.smoke_module = codex_control_smoke
        self.error = self.controls.ControlContractError
        self.registry = load_json(CODEX_REGISTRY_FIXTURE_PATH)
        self.partition_entries = load_json(CODEX_PARTITION_FIXTURE_PATH)["entries"]
        self.smoke_partition = next(
            entry for entry in self.partition_entries if not entry["qualification_eligible"]
        )

    def build_plan(self, control_kind: str) -> dict[str, object]:
        return self.build_plan_with(control_kind, authorization="withheld")

    def build_plan_with(self, control_kind: str, **kwargs: object) -> dict[str, object]:
        self.assertTrue(
            hasattr(self.smoke_module, "build_plan"),
            "T029 must expose build_plan for Codex ChatGPT-sign-in control smokes",
        )
        options: dict[str, object] = {"authorization": "withheld"}
        options.update(kwargs)
        return self.smoke_module.build_plan(
            control_kind,
            registry=self.registry,
            partition_entries=self.partition_entries,
            **options,
        )

    def seal(self, record: dict[str, object]) -> dict[str, object]:
        self.assertTrue(
            hasattr(self.smoke_module, "seal_record"),
            "T029 must expose seal_record for non-live Codex smoke records",
        )
        return self.smoke_module.seal_record(
            record,
            registry=self.registry,
            partition_entries=self.partition_entries,
        )

    def unit_member(
        self,
        row_id: str,
        spawned_by: str | None = None,
        *,
        duration_ms: int = 60000,
        raw: tuple[int, int, int, int | None] = (1000, 200, 300, 50),
        cache: tuple[int, int, int] | None = (70, 30, 400),
    ) -> dict[str, object]:
        row: dict[str, object] = {
            "row_id": row_id,
            "spawned_by": spawned_by,
            "duration_ms": duration_ms,
            "resource_vector": {
                "input_tokens": raw[0],
                "cached_input_tokens": raw[2],
                "output_tokens": raw[1],
                "duration_ms": duration_ms,
                "retries": 0,
                "compactions": 0,
                "terminal_state": "completed",
                "acceptance": 1.0,
            },
            "raw_token_vector": {
                "input_tokens": raw[0],
                "output_tokens": raw[1],
                "cached_input_tokens": raw[2],
                "reasoning_output_tokens": raw[3],
            },
        }
        if cache is not None:
            row["cache_diagnostic"] = {
                "cache_read_tokens": cache[2],
                "cache_write_tokens_by_ttl_class": {
                    "ephemeral_5m": cache[0],
                    "ephemeral_1h": cache[1],
                },
            }
        return row

    def smoke_record(self, control_kind: str, **overrides: object) -> dict[str, object]:
        control = control_of_kind(self.registry, control_kind)
        objective = self.smoke_partition["objective_ids"][0]
        default_attempts = [
            {
                "objective_id": objective,
                "unit_rows": [
                    self.unit_member("parent"),
                    self.unit_member("child-1", "parent"),
                ],
            }
        ]
        record: dict[str, object] = {
            "record_kind": "codex_control_smoke",
            "schema_version": "1.0.0",
            "smoke_id": f"g56r-004-smoke-{control_kind}",
            "control_id": control["control_id"],
            "control_kind": control_kind,
            "authentication_mode": "chatgpt_subscription",
            "authorization": "withheld",
            "run_state": "unrun",
            "scored": False,
            "outcome_bearing": False,
            "partition_id": self.smoke_partition["partition_id"],
            "partition_type": "calibration",
            "objective_ids": [objective],
            "confirmation_entries": 0,
            "elapsed_wall_clock_seconds": 600,
            "objective_attempts": default_attempts,
            "observed_cache_isolation": [
                self.isolation_pair("unpinned", "adaptive"),
                self.isolation_pair("unpinned", "justified_high_effort"),
                self.isolation_pair("adaptive", "justified_high_effort"),
            ],
        }
        record.update(overrides)
        if "produced_evidence" not in overrides:
            record["produced_evidence"] = self.produced_evidence(
                control_kind, self.record_unit_rows(record)
            )
        return record

    def record_unit_rows(self, record: dict[str, object]) -> list[dict[str, object]]:
        return [
            row
            for attempt in record["objective_attempts"]
            for row in attempt["unit_rows"]
        ]

    def produced_evidence(
        self,
        control_kind: str,
        unit_rows: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        control = control_of_kind(self.registry, control_kind)
        if control_kind == "unpinned":
            return {
                "read_back_from": "produced_evidence",
                "served_model": control["unpinned"]["pinned_parent_model"],
                "served_effort": control["unpinned"]["pinned_parent_effort"],
                "observed_absent_overrides": {
                    member: True for member in CODEX_REQUIRED_ABSENT_OVERRIDES
                },
            }
        if control_kind == "adaptive":
            ladder = control["adaptive"]["escalation_ladder"]
            pre_model, pre_effort = ladder[0].rsplit("__", 1)
            post_model, post_effort = ladder[1].rsplit("__", 1)
            return {
                "read_back_from": "produced_evidence",
                "qualifying_signal": {
                    "objective_id": self.smoke_partition["objective_ids"][0],
                    "failure_code": "candidate_failed",
                    "failure_plane": "candidate",
                    "terminal_state": "failed",
                    "retries": 0,
                    "budget_observations": {},
                },
                "pre_escalation": {
                    "route_id": ladder[0],
                    "served_model": pre_model,
                    "served_effort": pre_effort,
                },
                "post_escalation": {
                    "route_id": ladder[1],
                    "served_model": post_model,
                    "served_effort": post_effort,
                },
            }
        if unit_rows is None:
            unit_rows = [self.unit_member("parent"), self.unit_member("child-1", "parent")]
        return {
            "read_back_from": "produced_evidence",
            "served_route_id": CODEX_JUSTIFIED_HIGH_EFFORT_ROUTE_ID,
            "served_model": CODEX_JUSTIFIED_HIGH_EFFORT_MODEL,
            "served_effort": CODEX_JUSTIFIED_HIGH_EFFORT_EFFORT,
            "successor_freeze_digest": CODEX_G56R003_SUCCESSOR_FREEZE_ID,
            "route_evidence_digest": CODEX_G56R003_ROUTE_EVIDENCE_DIGEST,
            "eligibility_predicate_result": True,
            "eligibility_rationale_binding": "required_core_workspace_write_phase_executor",
            "fallback_route_id": None,
            "dynamic_route_discovery": False,
            "parent_plus_child_aggregate": self.controls.aggregate_parent_plus_children(
                control, unit_rows
            ),
        }

    def isolation_pair(self, left: str, right: str, status: str = "observed_disjoint") -> dict[str, object]:
        return {
            "arm_pair": sorted([
                CODEX_CONTROL_IDS_BY_KIND[left],
                CODEX_CONTROL_IDS_BY_KIND[right],
            ]),
            "status": status,
            "arm_cache_root_digest": "sha256:" + "1" * 64,
            "paired_arm_cache_root_digest": "sha256:" + "2" * 64,
            "roots_disjoint": status == "observed_disjoint",
        }

    def test_plan_names_exactly_one_chatgpt_sign_in_smoke_per_control(self) -> None:
        for kind in CODEX_CONTROL_KINDS:
            with self.subTest(control_kind=kind):
                plan = self.build_plan(kind)
                self.assertEqual(plan["control_kind"], kind)
                self.assertEqual(plan["control_id"], CODEX_CONTROL_IDS_BY_KIND[kind])
                self.assertEqual(plan["authentication_mode"], "chatgpt_subscription")
                self.assertEqual(plan["run_state"], "unrun")
                self.assertEqual(plan["authorization"], "withheld")
                self.assertEqual(plan["objective_ids"], [self.smoke_partition["objective_ids"][0]])

    def test_plan_refuses_api_key_and_ambiguous_authorization(self) -> None:
        for kwargs in (
            {"authentication_mode": "api_key"},
            {"authorization": "unknown"},
            {"authorization": "granted"},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(self.error):
                    self.build_plan_with("unpinned", **kwargs)

    def test_seal_keeps_authorization_withheld_as_unrun_not_refused(self) -> None:
        sealed = self.seal(self.smoke_record("unpinned"))
        self.assertEqual(sealed["run_state"], "unrun")
        self.assertEqual(sealed["evidence_admissibility"], "unrun")
        self.assertEqual(sealed["authorization"], "withheld")
        self.assertEqual(sealed["refusal_reasons"], [])

    def test_seal_refuses_api_key_ambiguous_auth_scored_and_outcome_rows(self) -> None:
        cases = (
            {"authentication_mode": "api_key"},
            {"authorization": "unknown"},
            {"scored": True},
            {"outcome_bearing": True},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(self.error):
                    self.seal(self.smoke_record("adaptive", **overrides))

    def test_all_mirrored_ceilings_raw_identity_and_elapsed_scope_are_reported(self) -> None:
        sealed = self.seal(self.smoke_record("justified_high_effort"))
        self.assertEqual(sealed["counted_over"], "parent_plus_children_unit")
        self.assertEqual(sealed["consumed"]["max_duration_seconds"], 600)
        self.assertEqual(sealed["raw_token_ceiling_members"], [
            "input_tokens",
            "output_tokens",
            "cached_input_tokens",
        ])
        for member in (
            "max_attempts",
            "max_candidates",
            "max_confirmation_entries",
            "max_duration_seconds",
            "max_input_tokens",
            "max_output_tokens",
            "max_cached_input_tokens",
            "raw_token_ceiling",
        ):
            with self.subTest(member=member):
                self.assertIn(member, sealed["consumed"])

    def test_nested_attempt_objectives_must_match_top_level_smoke_partition(self) -> None:
        admitted = self.smoke_partition["objective_ids"]
        reserved = next(
            entry for entry in self.partition_entries if entry["qualification_eligible"]
        )["objective_ids"][0]
        seeded_cases = (
            ("reserved_objective", reserved),
            ("outside_smoke_partition", "G56R-004-OUTSIDE-SMOKE-OBJ"),
            ("top_level_mismatch", admitted[1]),
        )
        for label, nested_objective in seeded_cases:
            with self.subTest(case=label):
                record = self.smoke_record("unpinned")
                record["objective_attempts"][0]["objective_id"] = nested_objective
                with self.assertRaises(self.error):
                    self.seal(record)

    def test_candidate_repetition_cache_diagnostics_and_child_count_follow_frozen_accounting(self) -> None:
        objectives = self.smoke_partition["objective_ids"]
        rows_one = [
            self.unit_member("objective-1-parent", raw=(10, 10, 10, 0), cache=(70, 30, 400)),
            self.unit_member("objective-1-child-1", "objective-1-parent", raw=(20, 20, 20, 0), cache=(7, 3, 40)),
            self.unit_member("objective-1-child-2", "objective-1-parent", raw=(30, 30, 30, 0), cache=(13, 5, 80)),
        ]
        rows_two = [
            self.unit_member("objective-2-parent", raw=(40, 40, 40, 0), cache=(17, 11, 120)),
            self.unit_member("objective-2-child-1", "objective-2-parent", raw=(50, 50, 50, 0), cache=(19, 13, 160)),
        ]
        sealed = self.seal(
            self.smoke_record(
                "adaptive",
                objective_ids=objectives[:2],
                objective_attempts=[
                    {"objective_id": objectives[0], "unit_rows": rows_one},
                    {"objective_id": objectives[1], "unit_rows": rows_two},
                ],
            )
        )
        self.assertEqual(sealed["consumed"]["max_attempts"], 2)
        self.assertEqual(sealed["consumed"]["max_candidates"], 1)
        self.assertEqual(sealed["child_dispatch_count"], 3)
        self.assertEqual(sealed["consumed"]["max_cache_read_tokens"], 800)
        self.assertEqual(
            sealed["consumed"]["max_cache_write_tokens_by_ttl_class"],
            {"ephemeral_5m": 126, "ephemeral_1h": 62},
        )

    def test_partial_cache_diagnostics_preserve_the_observed_ceiling(self) -> None:
        missing_read = self.smoke_record("adaptive")
        del missing_read["objective_attempts"][0]["unit_rows"][0]["cache_diagnostic"][
            "cache_read_tokens"
        ]
        read_sealed = self.seal(missing_read)
        self.assertEqual(read_sealed["consumed"]["max_cache_read_tokens"], 400)
        self.assertEqual(
            read_sealed["consumed"]["max_cache_write_tokens_by_ttl_class"],
            {"ephemeral_5m": 140, "ephemeral_1h": 60},
        )
        self.assertEqual(read_sealed["bounds_unobserved"], ["max_cache_read_tokens"])

        missing_ttl = self.smoke_record("adaptive")
        del missing_ttl["objective_attempts"][0]["unit_rows"][0]["cache_diagnostic"][
            "cache_write_tokens_by_ttl_class"
        ]["ephemeral_1h"]
        ttl_sealed = self.seal(missing_ttl)
        self.assertEqual(ttl_sealed["consumed"]["max_cache_read_tokens"], 800)
        self.assertEqual(
            ttl_sealed["consumed"]["max_cache_write_tokens_by_ttl_class"],
            {"ephemeral_5m": 140, "ephemeral_1h": 30},
        )
        self.assertEqual(
            ttl_sealed["bounds_unobserved"],
            ["max_cache_write_tokens_by_ttl_class.ephemeral_1h"],
        )

    def test_missing_child_cache_diagnostic_does_not_erase_observed_parent_breaches(self) -> None:
        record = self.smoke_record(
            "adaptive",
            objective_attempts=[
                {
                    "objective_id": self.smoke_partition["objective_ids"][0],
                    "unit_rows": [
                        self.unit_member(
                            "parent",
                            cache=(160_001, 40_001, 1_200_001),
                        ),
                        self.unit_member("child", "parent", cache=None),
                    ],
                }
            ],
        )
        with self.assertRaises(self.error):
            self.seal(record)

    def test_missing_child_cache_diagnostic_preserves_observed_subtotals_and_incompleteness(self) -> None:
        record = self.smoke_record(
            "adaptive",
            objective_attempts=[
                {
                    "objective_id": self.smoke_partition["objective_ids"][0],
                    "unit_rows": [
                        self.unit_member("parent", cache=(70, 30, 400)),
                        self.unit_member("child", "parent", cache=None),
                    ],
                }
            ],
        )
        sealed = self.seal(record)
        self.assertEqual(sealed["consumed"]["max_cache_read_tokens"], 400)
        self.assertEqual(
            sealed["consumed"]["max_cache_write_tokens_by_ttl_class"],
            {"ephemeral_5m": 70, "ephemeral_1h": 30},
        )
        self.assertEqual(
            sealed["bounds_unobserved"],
            [
                "max_cache_read_tokens",
                "max_cache_write_tokens_by_ttl_class.ephemeral_1h",
                "max_cache_write_tokens_by_ttl_class.ephemeral_5m",
            ],
        )

    def test_partial_cache_write_still_enforces_observed_ttl_breaches(self) -> None:
        record = self.smoke_record("adaptive")
        record["objective_attempts"][0]["unit_rows"][0]["cache_diagnostic"][
            "cache_write_tokens_by_ttl_class"
        ]["ephemeral_5m"] = 160_001
        del record["objective_attempts"][0]["unit_rows"][0]["cache_diagnostic"][
            "cache_write_tokens_by_ttl_class"
        ]["ephemeral_1h"]
        with self.assertRaises(self.error):
            self.seal(record)

    def test_adaptive_qualifying_signal_objective_is_bound_to_the_demonstrated_attempt(self) -> None:
        reserved = next(
            entry for entry in self.partition_entries if entry["qualification_eligible"]
        )["objective_ids"][0]
        for label, objective in (
            ("outside_attempts", self.smoke_partition["objective_ids"][1]),
            ("reserved", reserved),
        ):
            with self.subTest(case=label):
                evidence = copy.deepcopy(self.produced_evidence("adaptive"))
                evidence["qualifying_signal"]["objective_id"] = objective
                with self.assertRaises(self.error):
                    self.seal(
                        self.smoke_record("adaptive", produced_evidence=evidence)
                    )

    def test_public_smoke_apis_bind_injected_inputs_to_the_committed_authority(self) -> None:
        stale_registry = copy.deepcopy(self.registry)
        stale_registry["controls"][0]["control_digest"] = "sha256:" + "9" * 64

        altered_bounds = copy.deepcopy(self.registry)
        altered_bounds["smoke_bounds"]["max_attempts"]["value"] = 500

        stale_partition_digest = copy.deepcopy(self.partition_entries)
        stale_partition_digest[1]["objective_set_digest"] = "sha256:" + "8" * 64

        changed_reserved_membership = copy.deepcopy(self.partition_entries)
        changed_reserved_membership[0]["objective_ids"] = [
            "G56R-011-RESERVED-OBJ-COMPARISON-DRIFTED"
        ]

        cases = (
            ("stale_control_digest", stale_registry, self.partition_entries),
            ("altered_bounds", altered_bounds, self.partition_entries),
            ("stale_objective_set_digest", self.registry, stale_partition_digest),
            ("changed_reserved_membership", self.registry, changed_reserved_membership),
        )
        for label, registry, entries in cases:
            with self.subTest(api="build_plan", case=label):
                with self.assertRaises(self.error):
                    self.smoke_module.build_plan(
                        "adaptive",
                        registry=registry,
                        partition_entries=entries,
                        authorization="withheld",
                    )
            with self.subTest(api="seal_record", case=label):
                with self.assertRaises(self.error):
                    self.smoke_module.seal_record(
                        self.smoke_record("adaptive"),
                        registry=registry,
                        partition_entries=entries,
                    )

    def test_exported_partition_helpers_bind_injected_entries_to_committed_authority(self) -> None:
        stale_partition_digest = copy.deepcopy(self.partition_entries)
        stale_partition_digest[1]["objective_set_digest"] = "sha256:" + "8" * 64

        changed_reserved_membership = copy.deepcopy(self.partition_entries)
        changed_reserved_membership[0]["objective_ids"] = [
            "G56R-011-RESERVED-OBJ-COMPARISON-DRIFTED"
        ]

        clean_record = {
            "objective_ids": [self.smoke_partition["objective_ids"][0]],
            "outcome_bearing": False,
            "partition_id": self.smoke_partition["partition_id"],
            "partition_type": "calibration",
            "scored": False,
        }

        cases = (
            ("stale_objective_set_digest", stale_partition_digest),
            ("changed_reserved_membership", changed_reserved_membership),
        )
        for label, entries in cases:
            with self.subTest(helper="guard_plan_objectives", case=label):
                with self.assertRaises(self.error):
                    self.smoke_module.guard_plan_objectives(
                        [self.smoke_partition["objective_ids"][0]], entries
                    )
            with self.subTest(helper="plan_objectives", case=label):
                with self.assertRaises(self.error):
                    self.smoke_module.plan_objectives(entries)
            with self.subTest(helper="guard_smoke_record", case=label):
                with self.assertRaises(self.error):
                    self.smoke_module.guard_smoke_record(clean_record, entries)

    def test_repeating_one_candidate_objective_breaches_candidate_ceiling(self) -> None:
        objective = self.smoke_partition["objective_ids"][0]
        record = self.smoke_record(
            "adaptive",
            objective_ids=[objective],
            objective_attempts=[
                {"objective_id": objective, "unit_rows": [self.unit_member("parent-1")]},
                {"objective_id": objective, "unit_rows": [self.unit_member("parent-2")]},
            ],
        )
        with self.assertRaises(self.error):
            self.seal(record)

    def test_cache_read_and_write_ceilings_are_refused_independently(self) -> None:
        objective = self.smoke_partition["objective_ids"][0]
        seeded_cases = (
            ("cache_read", (1, 1, 1_200_001)),
            ("cache_write_5m", (160_001, 1, 1)),
            ("cache_write_1h", (1, 40_001, 1)),
        )
        for label, cache in seeded_cases:
            with self.subTest(case=label):
                record = self.smoke_record(
                    "justified_high_effort",
                    objective_attempts=[
                        {
                            "objective_id": objective,
                            "unit_rows": [
                                self.unit_member(
                                    "parent",
                                    raw=(1, 1, 1, 0),
                                    cache=cache,
                                )
                            ],
                        }
                    ],
                )
                with self.assertRaises(self.error):
                    self.seal(record)

    def test_adaptive_exact_treatment_requires_signal_and_served_route_movement(self) -> None:
        control = control_of_kind(self.registry, "adaptive")
        ladder = control["adaptive"]["escalation_ladder"]
        sealed = self.seal(self.smoke_record("adaptive"))
        self.assertEqual(
            sealed["produced_evidence"]["pre_escalation"]["route_id"],
            ladder[0],
        )
        self.assertEqual(
            sealed["produced_evidence"]["post_escalation"]["route_id"],
            ladder[1],
        )

        route_only = {
            "read_back_from": "produced_evidence",
            "pre_escalation": {"route_id": ladder[0]},
            "post_escalation": {"route_id": ladder[1]},
        }
        missing_signal = copy.deepcopy(self.produced_evidence("adaptive"))
        del missing_signal["qualifying_signal"]
        mismatched_metadata = copy.deepcopy(self.produced_evidence("adaptive"))
        mismatched_metadata["pre_escalation"]["served_effort"] = "xhigh"
        non_qualifying_signal = copy.deepcopy(self.produced_evidence("adaptive"))
        non_qualifying_signal["qualifying_signal"].update({
            "failure_code": "none",
            "failure_plane": "none",
            "terminal_state": "completed",
        })
        for label, evidence in (
            ("route_only", route_only),
            ("missing_signal", missing_signal),
            ("mismatched_metadata", mismatched_metadata),
            ("non_qualifying_signal", non_qualifying_signal),
        ):
            with self.subTest(case=label):
                with self.assertRaises(self.error):
                    self.seal(self.smoke_record("adaptive", produced_evidence=evidence))

    def test_high_effort_exact_treatment_recomputes_the_recorded_unit_aggregate(self) -> None:
        control = control_of_kind(self.registry, "justified_high_effort")
        record = self.smoke_record("justified_high_effort")
        expected = self.controls.aggregate_parent_plus_children(
            control, self.record_unit_rows(record)
        )
        sealed = self.seal(record)
        self.assertEqual(
            sealed["produced_evidence"]["parent_plus_child_aggregate"],
            expected,
        )

        invented = self.smoke_record("justified_high_effort")
        invented["produced_evidence"]["parent_plus_child_aggregate"] = {
            "terminal_state": "completed"
        }
        with self.assertRaises(self.error):
            self.seal(invented)

        mismatched = self.smoke_record("justified_high_effort")
        mismatched["objective_attempts"][0]["unit_rows"].append(
            self.unit_member("child-2", "parent", raw=(2, 2, 2, 0), cache=(2, 2, 2))
        )
        with self.assertRaises(self.error):
            self.seal(mismatched)

    def test_child_dispatches_do_not_consume_objective_attempts(self) -> None:
        record = self.smoke_record("adaptive")
        record["objective_attempts"][0]["unit_rows"].extend([
            self.unit_member("child-2", "parent"),
            self.unit_member("child-3", "parent"),
        ])
        sealed = self.seal(record)
        self.assertEqual(sealed["consumed"]["max_attempts"], 1)
        self.assertEqual(sealed["child_dispatch_count"], 3)

    def test_exact_treatment_is_read_back_from_produced_evidence(self) -> None:
        for kind in CODEX_CONTROL_KINDS:
            with self.subTest(control_kind=kind):
                sealed = self.seal(self.smoke_record(kind))
                self.assertEqual(
                    sealed["produced_evidence"]["read_back_from"], "produced_evidence"
                )
                request_only = self.smoke_record(
                    kind,
                    produced_evidence=dict(
                        self.produced_evidence(kind),
                        read_back_from="dispatch_request",
                    ),
                )
                with self.assertRaises(self.error):
                    self.seal(request_only)

    def test_all_three_unordered_cache_isolation_pairs_are_required(self) -> None:
        sealed = self.seal(self.smoke_record("unpinned"))
        self.assertEqual(len(sealed["cache_isolation"]["pairs"]), 3)
        self.assertTrue(sealed["cache_isolation"]["all_pairs_disjoint"])

        missing = self.smoke_record("unpinned")
        missing["observed_cache_isolation"] = missing["observed_cache_isolation"][:2]
        with self.assertRaises(self.error):
            self.seal(missing)


class CodexRawCaptureExclusionTests(unittest.TestCase):
    """T030 RED: committed smoke artifacts must contain summaries, never raw runs."""

    def setUp(self) -> None:
        self.assertIsNotNone(codex_policy_controls, "codex_policy_controls is not importable")
        self.assertIsNotNone(codex_control_smoke, "codex_control_smoke is not importable")
        self.controls = codex_policy_controls
        self.smoke_module = codex_control_smoke
        self.error = self.controls.ControlContractError

    def sanitize(self, artifact: dict[str, object]) -> dict[str, object]:
        self.assertTrue(
            hasattr(self.smoke_module, "sanitize_repository_artifact"),
            "T031 must expose sanitize_repository_artifact for repository-safe smoke output",
        )
        return self.smoke_module.sanitize_repository_artifact(artifact)

    def governed_summary(self, **overrides: object) -> dict[str, object]:
        artifact: dict[str, object] = {
            "artifact_kind": "codex_control_smoke_summary",
            "schema_version": "1.0.0",
            "control_id": CODEX_CONTROL_IDS_BY_KIND["adaptive"],
            "run_state": "unrun",
            "evidence_admissibility": "unrun",
            "governed_summary": {
                "status": "authorization_withheld",
                "digest": "sha256:" + "3" * 64,
            },
            "refusal_record": {
                "reasons": [],
                "digest": "sha256:" + "4" * 64,
            },
            "replay_fixture": {
                "case_set_id": "g56r-004-adaptive-signal-resolution",
                "digest": "sha256:" + "5" * 64,
                "raw_capture": False,
            },
        }
        artifact.update(overrides)
        return artifact

    def test_governed_summaries_digests_refusals_and_non_raw_replay_are_admitted(self) -> None:
        sanitized = self.sanitize(self.governed_summary())
        self.assertEqual(sanitized["artifact_kind"], "codex_control_smoke_summary")
        self.assertEqual(sanitized["run_state"], "unrun")
        self.assertEqual(sanitized["governed_summary"]["status"], "authorization_withheld")
        self.assertEqual(sanitized["refusal_record"]["reasons"], [])
        self.assertFalse(sanitized["replay_fixture"]["raw_capture"])

    def test_raw_live_model_text_prompts_and_responses_are_refused(self) -> None:
        raw_cases = (
            {"live_model_text": "assistant raw response"},
            {"prompt": "score this candidate with private context"},
            {"response": "raw model output"},
            {"messages": [{"role": "user", "content": "raw prompt"}]},
        )
        for seeded in raw_cases:
            with self.subTest(seeded=seeded):
                with self.assertRaises(self.error):
                    self.sanitize(self.governed_summary(**seeded))

    def test_operator_local_paths_unsanitized_captures_and_path_cache_roots_are_refused(self) -> None:
        raw_cases = (
            {"operator_local_path": "/local/operator/raw-smoke.json"},
            {"unsanitized_capture": {"path": "/private/tmp/raw.json"}},
            {
                "observed_cache_isolation": [
                    {
                        "arm_pair": sorted([
                            CODEX_CONTROL_IDS_BY_KIND["unpinned"],
                            CODEX_CONTROL_IDS_BY_KIND["adaptive"],
                        ]),
                        "arm_cache_root_digest": "/tmp/codex-cache-a",
                        "paired_arm_cache_root_digest": "sha256:" + "6" * 64,
                    }
                ]
            },
        )
        for seeded in raw_cases:
            with self.subTest(seeded=seeded):
                with self.assertRaises(self.error):
                    self.sanitize(self.governed_summary(**seeded))

    def test_repository_summary_nested_member_sets_are_exact(self) -> None:
        raw_cases = (
            {
                "governed_summary": {
                    "status": "authorization_withheld",
                    "digest": "sha256:" + "3" * 64,
                    "raw_output_digest": "sha256:" + "6" * 64,
                }
            },
            {
                "refusal_record": {
                    "reasons": [],
                    "digest": "sha256:" + "4" * 64,
                    "raw_reason_digest": "sha256:" + "7" * 64,
                }
            },
            {
                "replay_fixture": {
                    "case_set_id": "g56r-004-adaptive-signal-resolution",
                    "digest": "sha256:" + "5" * 64,
                    "raw_capture": False,
                    "response_digest": "sha256:" + "8" * 64,
                }
            },
        )
        for seeded in raw_cases:
            with self.subTest(seeded=seeded):
                with self.assertRaises(self.error):
                    self.sanitize(self.governed_summary(**seeded))

    def test_repository_summary_replay_case_set_id_is_bound_to_the_committed_fixture(self) -> None:
        artifact = self.governed_summary(
            replay_fixture={
                "case_set_id": "Summarize the smoke plan in prose for the next reviewer",
                "digest": "sha256:" + "5" * 64,
                "raw_capture": False,
            }
        )
        with self.assertRaises(self.error):
            self.sanitize(artifact)

    def test_repository_summary_digest_rejects_prose_payload_with_sha256_prefix(self) -> None:
        valid_digest = "sha256:" + "abcdef0123456789" * 4
        valid = self.sanitize(
            self.governed_summary(
                governed_summary={
                    "status": "authorization_withheld",
                    "digest": valid_digest,
                }
            )
        )
        self.assertEqual(valid["governed_summary"]["digest"], valid_digest)

        prose_payload = "nothexprompttext" * 4
        self.assertEqual(len(prose_payload), 64)
        artifact = self.governed_summary(
            governed_summary={
                "status": "authorization_withheld",
                "digest": "sha256:" + prose_payload,
            }
        )
        with self.assertRaises(self.error):
            self.sanitize(artifact)

    def test_repository_summary_rejects_path_strings_and_unrun_refusal_reasons(self) -> None:
        raw_cases = (
            {"replay_fixture": {
                "case_set_id": "/private/tmp/raw-smoke.json",
                "digest": "sha256:" + "5" * 64,
                "raw_capture": False,
            }},
            {"refusal_record": {
                "reasons": ["operator refused from /private/tmp/raw-smoke.json"],
                "digest": "sha256:" + "4" * 64,
            }},
        )
        for seeded in raw_cases:
            with self.subTest(seeded=seeded):
                with self.assertRaises(self.error):
                    self.sanitize(self.governed_summary(**seeded))


class UnpinnedControlTests(unittest.TestCase):
    """FR-006 and FR-007: one arm, riding the pinned parent, re-frozen on a re-pin."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.registry = synthetic_registry()
        self.control = control_of_kind(self.registry, "unpinned")

    def test_the_unpinned_control_freezes_exactly_one_arm(self) -> None:
        self.assertEqual(self.control["unpinned"]["arm_count"], 1)
        self.assertIsNone(self.module.validate_unpinned_control(self.control))

    def test_more_than_one_concurrent_arm_is_refused(self) -> None:
        # FR-007: a matrix over parent sessions is not freezable as one control.
        for seeded in (0, 2, True):
            with self.subTest(arm_count=seeded):
                control = copy.deepcopy(self.control)
                control["unpinned"]["arm_count"] = seeded
                with self.assertRaises(self.error):
                    self.module.validate_unpinned_control(control)

    def test_agents_inherit_the_session_model_rather_than_setting_one(self) -> None:
        self.assertEqual(self.control["unpinned"]["model_resolution"], "inherit")
        self.control["unpinned"]["model_resolution"] = "explicit"
        with self.assertRaises(self.error):
            self.module.validate_unpinned_control(self.control)

    def test_the_pin_is_read_from_the_claude_side_experiment_assignment_document(self) -> None:
        # FR-006: the repository carries two documents a reader can reach for
        # "the environment contract"; this is the one carrying the four
        # identifying members and the subscription | api_key mode.
        identifier, node = self.module.pinned_parent_document()
        self.assertEqual(identifier, load_json(ASSIGNMENT_SCHEMA_PATH)["$id"])
        self.assertEqual(
            sorted(node["properties"]["authentication_mode"]["enum"]),
            ["api_key", "subscription"],
        )
        for member in ("parent_session_model", "parent_session_effort",
                       "claude_code_subagent_model_unset"):
            with self.subTest(member=member):
                self.assertIn(member, node["properties"])
        self.assertEqual(self.control["unpinned"]["pinned_parent_binding"]["id"], identifier)

    def test_a_binding_to_the_shared_runtime_environment_contract_is_refused(self) -> None:
        # The shared document's parent session is a differently shaped member and
        # its authentication_mode enumerates chatgpt_subscription | api_key.
        shared = load_json(SHARED_ENVIRONMENT_CONTRACT_PATH)
        self.assertEqual(
            sorted(shared["properties"]["authentication_mode"]["enum"]),
            ["api_key", "chatgpt_subscription"],
        )
        self.control["unpinned"]["pinned_parent_binding"] = {
            "id": shared["$id"],
            "digest": file_bytes_digest(SHARED_ENVIRONMENT_CONTRACT_PATH),
        }
        with self.assertRaises(self.error):
            self.module.validate_unpinned_control(self.control)

    def test_a_pin_binding_whose_digest_drifted_is_refused(self) -> None:
        self.control["unpinned"]["pinned_parent_binding"]["digest"] = "sha256:" + "e" * 64
        with self.assertRaises(self.error):
            self.module.validate_unpinned_control(self.control)

    def test_the_pinned_effort_is_read_against_the_bound_document_s_own_enum(self) -> None:
        admitted = load_json(ASSIGNMENT_SCHEMA_PATH)["$defs"]["comparisonSetAssignment"][
            "properties"
        ]["environment_contract"]["properties"]["parent_session_effort"]["enum"]
        self.assertIn(self.control["unpinned"]["pinned_parent_effort"], admitted)
        self.control["unpinned"]["pinned_parent_effort"] = "ultra"
        with self.assertRaises(self.error):
            self.module.validate_unpinned_control(self.control)

    def test_a_pinned_model_that_is_not_a_recorded_string_is_refused(self) -> None:
        for seeded in ("", None):
            with self.subTest(pinned_parent_model=seeded):
                control = copy.deepcopy(self.control)
                control["unpinned"]["pinned_parent_model"] = seeded
                with self.assertRaises(self.error):
                    self.module.validate_unpinned_control(control)

    def test_a_different_pin_yields_a_different_control_address(self) -> None:
        # FR-007: a re-pin is a new control version, never a second concurrent arm.
        repinned = copy.deepcopy(self.control)
        repinned["unpinned"]["pinned_parent_model"] = "model-beta"
        repinned.pop("control_digest")
        repinned["control_digest"] = record_digest(repinned, digest_field="control_digest")
        self.assertNotEqual(repinned["control_digest"], self.control["control_digest"])
        self.assertEqual(repinned["unpinned"]["arm_count"], 1)
        self.assertIsNone(self.module.validate_unpinned_control(repinned))

    def test_the_registry_load_path_reaches_the_unpinned_rules(self) -> None:
        self.control["unpinned"]["model_resolution"] = "explicit"
        with self.assertRaises(self.error):
            self.module.validate_registry(seal(self.registry))


def clean_row() -> dict[str, object]:
    """A row on which every source above terminal state carries the none sentinel."""
    return {
        "terminal_state": "completed",
        "failure_plane": "none",
        "failure_code": "none",
        "retries": 0,
        "budget_observations": {"max_duration_seconds": 100},
    }


class AdaptiveSignalMapTests(unittest.TestCase):
    """FR-008 through FR-010c: total maps, one response per row, nothing unreachable."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.registry = synthetic_registry()
        self.control = control_of_kind(self.registry, "adaptive")
        self.adaptive = self.control["adaptive"]

    def test_each_response_map_is_set_equal_to_the_enum_read_live_from_the_contract(self) -> None:
        cases = {
            "terminal_state_response": frozen_terminal_states(),
            "failure_plane_response": frozen_failure_planes(),
            "failure_code_response": frozen_failure_codes(),
        }
        for member, enum in cases.items():
            with self.subTest(map=member):
                self.assertEqual(sorted(self.adaptive[member]), sorted(enum))
        self.assertIsNone(self.module.validate_signal_maps(self.control))

    def test_every_mapping_is_total_and_single_valued(self) -> None:
        for member in ("terminal_state_response", "failure_plane_response",
                       "failure_code_response"):
            for signal, response in self.adaptive[member].items():
                with self.subTest(map=member, signal=signal):
                    self.assertIn(response, POLICY_RESPONSES)

    def test_a_seeded_membership_change_on_a_frozen_enum_fails_closed(self) -> None:
        # FR-010a: an added or removed member must refuse rather than leave a
        # signal unmapped inside a content address that never moved.
        cases = (
            ("terminal_state_response", "completed", "quiesced"),
            ("failure_plane_response", "candidate", "routing"),
            ("failure_code_response", "service_reroute", "route_repointed"),
        )
        for member, dropped, added in cases:
            with self.subTest(map=member, dropped=dropped):
                control = copy.deepcopy(self.control)
                del control["adaptive"][member][dropped]
                with self.assertRaises(self.error):
                    self.module.validate_signal_maps(control)
            with self.subTest(map=member, added=added):
                control = copy.deepcopy(self.control)
                control["adaptive"][member][added] = "hold"
                with self.assertRaises(self.error):
                    self.module.validate_signal_maps(control)

    def test_a_response_outside_the_closed_policy_enum_is_refused(self) -> None:
        self.adaptive["failure_code_response"]["candidate_failed"] = "de_escalate"
        with self.assertRaises(self.error):
            self.module.validate_signal_maps(self.control)

    def test_signal_precedence_covers_the_closed_five_member_source_set(self) -> None:
        # FR-010b: the retry-count and budget-threshold sources hold ranks of
        # their own rather than carrying a response no order ever consults.
        self.assertEqual(self.adaptive["signal_precedence"], list(SIGNAL_SOURCES))
        self.assertIn("retry_count", self.adaptive["signal_precedence"])
        self.assertIn("budget_threshold", self.adaptive["signal_precedence"])

    def test_a_precedence_array_omitting_an_admitted_source_is_refused(self) -> None:
        for omitted in SIGNAL_SOURCES:
            with self.subTest(omitted=omitted):
                control = copy.deepcopy(self.control)
                control["adaptive"]["signal_precedence"] = [
                    source for source in SIGNAL_SOURCES if source != omitted
                ]
                with self.assertRaises(self.error):
                    self.module.validate_signal_maps(control)

    def test_terminal_state_ranked_ahead_of_a_lower_source_is_refused(self) -> None:
        # The always-valued source placed above retry count or budget threshold
        # would make both unreachable, which is what FR-010b fails closed on.
        seeded = (
            ["failure_code", "failure_plane", "terminal_state", "retry_count",
             "budget_threshold"],
            ["terminal_state", "failure_code", "failure_plane", "retry_count",
             "budget_threshold"],
            ["failure_code", "failure_plane", "retry_count", "terminal_state",
             "budget_threshold"],
        )
        for order in seeded:
            with self.subTest(signal_precedence=order):
                control = copy.deepcopy(self.control)
                control["adaptive"]["signal_precedence"] = list(order)
                with self.assertRaises(self.error):
                    self.module.validate_signal_maps(control)

    def test_the_plane_map_agrees_with_the_code_map_under_the_frozen_derivation(self) -> None:
        for code in frozen_failure_codes():
            with self.subTest(failure_code=code):
                self.assertEqual(
                    self.adaptive["failure_plane_response"][failure_plane_for(code)],
                    self.adaptive["failure_code_response"][code],
                )
        self.adaptive["failure_plane_response"]["candidate"] = "hold"
        with self.assertRaises(self.error):
            self.module.validate_signal_maps(self.control)

    def test_the_terminal_state_map_agrees_under_the_candidate_plane_pairing(self) -> None:
        codes = frozen_failure_codes()
        for state in frozen_terminal_states():
            if state == "completed":
                continue
            with self.subTest(terminal_state=state):
                paired = f"candidate_{state}"
                self.assertIn(paired, codes)
                self.assertEqual(
                    self.adaptive["terminal_state_response"][state],
                    self.adaptive["failure_code_response"][paired],
                )
        self.adaptive["terminal_state_response"]["failed"] = "hold"
        with self.assertRaises(self.error):
            self.module.validate_signal_maps(self.control)

    def test_a_derived_candidate_code_absent_from_the_frozen_enum_fails_closed(self) -> None:
        # The pairing is derived live from the committed failure_code enum, so a
        # terminal state with no candidate_<state> member refuses rather than
        # being skipped. Exercised through the derivation itself: the committed
        # enums agree today, and a case that mutated one would be testing its own
        # edit rather than the guard.
        codes = frozen_failure_codes()
        for state in frozen_terminal_states():
            if state == "completed":
                continue
            with self.subTest(terminal_state=state):
                self.assertEqual(self.module.candidate_code_for(state), f"candidate_{state}")
                self.assertIn(self.module.candidate_code_for(state), codes)
        with self.assertRaises(self.error):
            self.module.candidate_code_for("quiesced")

    def test_the_registry_load_path_reaches_the_signal_map_rules(self) -> None:
        self.adaptive["failure_plane_response"]["candidate"] = "hold"
        with self.assertRaises(self.error):
            self.module.validate_registry(seal(self.registry))


class AdaptiveRowResolutionTests(unittest.TestCase):
    """FR-010b and FR-015a: one response per row, decided by the declared order."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.control = control_of_kind(synthetic_registry(), "adaptive")

    def test_a_row_carrying_only_a_terminal_state_resolves_through_the_last_rank(self) -> None:
        self.assertEqual(self.module.resolve_response(self.control, clean_row()), "hold")

    def test_a_failure_code_outranks_every_lower_source(self) -> None:
        row = clean_row()
        row.update(failure_code="candidate_failed", failure_plane="candidate", retries=3)
        self.assertEqual(self.module.resolve_response(self.control, row), "escalate")

    def test_a_platform_initiated_reroute_resolves_non_scorable(self) -> None:
        # FR-015a: the observable is the already-frozen service_reroute code.
        row = clean_row()
        row.update(failure_code="service_reroute", failure_plane="treatment")
        self.assertEqual(self.module.resolve_response(self.control, row), "non_scorable")

    def test_a_failure_plane_decides_when_the_code_is_the_none_sentinel(self) -> None:
        row = clean_row()
        row["failure_plane"] = "candidate"
        self.assertEqual(self.module.resolve_response(self.control, row), "escalate")

    def test_the_retry_count_source_is_reachable_below_both_enum_sources(self) -> None:
        row = clean_row()
        row["retries"] = 1
        self.assertEqual(self.module.resolve_response(self.control, row), "escalate")

    def test_the_budget_threshold_source_is_reachable_below_the_retry_count(self) -> None:
        row = clean_row()
        row["budget_observations"] = {"max_duration_seconds": 1200}
        self.assertEqual(self.module.resolve_response(self.control, row), "escalate")

    def test_a_row_resolves_to_exactly_one_response_over_every_frozen_signal(self) -> None:
        for code in frozen_failure_codes():
            with self.subTest(failure_code=code):
                row = clean_row()
                row.update(failure_code=code, failure_plane=failure_plane_for(code))
                self.assertIn(self.module.resolve_response(self.control, row), POLICY_RESPONSES)

    def test_a_row_carrying_an_unmapped_signal_fails_closed(self) -> None:
        cases = (
            {"failure_code": "route_repointed"},
            {"failure_plane": "routing"},
            {"terminal_state": "quiesced"},
        )
        for seeded in cases:
            with self.subTest(**seeded):
                row = clean_row()
                row.update(seeded)
                with self.assertRaises(self.error):
                    self.module.resolve_response(self.control, row)

    def test_a_row_recording_no_terminal_state_fails_closed(self) -> None:
        row = clean_row()
        del row["terminal_state"]
        with self.assertRaises(self.error):
            self.module.resolve_response(self.control, row)


class EscalationLadderTests(unittest.TestCase):
    """FR-011, FR-011a, FR-011b: rank is array position, and the ladder is total."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.registry = synthetic_registry()
        self.control = control_of_kind(self.registry, "adaptive")
        self.freeze = synthetic_freeze()

    def test_a_well_formed_ladder_over_the_bound_freeze_is_accepted(self) -> None:
        self.assertIsNone(
            self.module.validate_escalation_ladder(self.control, self.freeze)
        )

    def test_exactly_one_freeze_is_bound_by_identifier_and_digest(self) -> None:
        for member in ("candidate_freeze_id", "freeze_digest"):
            with self.subTest(drifted=member):
                control = copy.deepcopy(self.control)
                control["adaptive"][member] = "sha256:" + "f" * 64
                with self.assertRaises(self.error):
                    self.module.validate_escalation_ladder(control, self.freeze)

    def test_the_ladder_carries_every_admitted_tuple_exactly_once(self) -> None:
        admitted = [t["candidate_route_id"] for t in self.freeze["admitted_tuples"]]
        self.assertEqual(sorted(self.control["adaptive"]["escalation_ladder"]), sorted(admitted))

    def test_a_seeded_duplicate_entry_is_refused(self) -> None:
        self.control["adaptive"]["escalation_ladder"] = [
            "route-alpha-low",
            "route-alpha-low",
            "route-alpha-high",
            "route-beta-medium",
        ]
        with self.assertRaises(self.error):
            self.module.validate_escalation_ladder(self.control, self.freeze)

    def test_a_seeded_omission_is_refused(self) -> None:
        # FR-011a.2: exclusion happens at the freeze through excluded_tuples,
        # never by omission from the ladder.
        self.control["adaptive"]["escalation_ladder"] = ["route-alpha-low", "route-alpha-high"]
        with self.assertRaises(self.error):
            self.module.validate_escalation_ladder(self.control, self.freeze)

    def test_an_entry_outside_the_bound_freeze_is_refused(self) -> None:
        self.control["adaptive"]["escalation_ladder"] = [
            "route-alpha-low",
            "route-alpha-high",
            "route-gamma-max",
        ]
        with self.assertRaises(self.error):
            self.module.validate_escalation_ladder(self.control, self.freeze)

    def test_a_within_model_position_contradicting_the_frozen_effort_ladder_is_refused(
        self,
    ) -> None:
        # The two model-alpha entries are swapped, and the cross-model step that
        # the swap creates carries its rationale, so the only violation left is
        # the derived within-model order.
        ladder = ["route-alpha-high", "route-alpha-low", "route-beta-medium"]
        self.assertLess(
            frozen_effort_ladder().index("low"), frozen_effort_ladder().index("high")
        )
        self.control["adaptive"]["escalation_ladder"] = ladder
        self.control["adaptive"]["escalation_ladder_rationales"] = [
            {
                "from_route": "route-alpha-low",
                "to_route": "route-beta-medium",
                "rationale": "declared cross-model judgment",
            }
        ]
        with self.assertRaises(self.error):
            self.module.validate_escalation_ladder(self.control, self.freeze)

    def test_a_cross_model_step_with_no_recorded_rationale_is_refused(self) -> None:
        self.control["adaptive"]["escalation_ladder_rationales"] = []
        with self.assertRaises(self.error):
            self.module.validate_escalation_ladder(self.control, self.freeze)

    def test_a_rationale_recorded_for_a_step_the_ladder_does_not_take_is_refused(self) -> None:
        self.control["adaptive"]["escalation_ladder_rationales"] = [
            {
                "from_route": "route-alpha-low",
                "to_route": "route-beta-medium",
                "rationale": "a step the ladder never takes",
            }
        ]
        with self.assertRaises(self.error):
            self.module.validate_escalation_ladder(self.control, self.freeze)

    def test_reordering_the_ladder_yields_a_new_adaptive_control_address(self) -> None:
        # FR-011b: array order is inside the preimage, so a reorder is a new
        # version rather than an in-place edit.
        reordered = copy.deepcopy(self.control)
        reordered["adaptive"]["escalation_ladder"] = [
            "route-alpha-high",
            "route-alpha-low",
            "route-beta-medium",
        ]
        reordered.pop("control_digest")
        reordered["control_digest"] = record_digest(reordered, digest_field="control_digest")
        self.assertNotEqual(reordered["control_digest"], self.control["control_digest"])

    def test_the_next_higher_route_is_the_entry_at_the_following_index(self) -> None:
        self.assertEqual(
            self.module.next_route(self.control, "route-alpha-low"), "route-alpha-high"
        )
        self.assertEqual(
            self.module.next_route(self.control, "route-alpha-high"), "route-beta-medium"
        )

    def test_an_escalation_at_the_ceiling_records_no_route_and_refuses_wrap_around(self) -> None:
        self.assertIsNone(self.module.next_route(self.control, "route-beta-medium"))

    def test_the_de_escalation_target_is_the_entry_at_the_preceding_index(self) -> None:
        self.assertEqual(
            self.module.previous_route(self.control, "route-beta-medium"), "route-alpha-high"
        )

    def test_a_de_escalation_at_the_floor_records_no_route_and_refuses_wrap_around(self) -> None:
        self.assertIsNone(self.module.previous_route(self.control, "route-alpha-low"))

    def test_a_route_outside_the_ladder_fails_closed_at_both_ends(self) -> None:
        for entrypoint in (self.module.next_route, self.module.previous_route):
            with self.subTest(entrypoint=entrypoint.__name__):
                with self.assertRaises(self.error):
                    entrypoint(self.control, "route-gamma-max")


def objective(**overrides: object) -> dict[str, object]:
    """A completed objective row; overrides make it non-clean or non-scorable."""
    row = clean_row()
    row.update({"objective_id": "car-004-smoke-objective-1", "escalated": False})
    row.update(overrides)
    return row


class CleanPassStreakTests(unittest.TestCase):
    """FR-012 and FR-012a: what counts, what resets, and what the floor does."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.control = control_of_kind(synthetic_registry(), "adaptive")
        self.state = {"current_route_id": "route-alpha-high", "clean_streak": 0}

    def walk(self, objectives: list[dict[str, object]],
             state: dict[str, object] | None = None) -> dict[str, object]:
        carried = dict(self.state if state is None else state)
        for entry in objectives:
            carried = self.module.advance_clean_streak(self.control, carried, entry)
        return carried

    def test_a_clean_pass_requires_every_declared_member_at_its_frozen_value(self) -> None:
        declared = self.control["adaptive"]["clean_pass_definition"]
        self.assertEqual(declared["terminal_state"], "completed")
        self.assertEqual(declared["failure_code"], "none")
        self.assertEqual(declared["max_retries"], 0)
        self.assertIs(declared["budget_trigger_met"], False)
        advanced = self.module.advance_clean_streak(self.control, self.state, objective())
        self.assertTrue(advanced["clean_pass"])
        self.assertEqual(advanced["clean_streak"], 1)

    def test_an_objective_failing_any_declared_member_is_not_a_clean_pass(self) -> None:
        cases = {
            "terminal_state": {"terminal_state": "failed", "failure_code": "candidate_failed",
                               "failure_plane": "candidate"},
            "failure_code": {"failure_code": "gate_failed", "failure_plane": "gate"},
            "retries": {"retries": 1},
            "budget_trigger": {"budget_observations": {"max_duration_seconds": 1200}},
        }
        for label, overrides in cases.items():
            with self.subTest(non_clean=label):
                advanced = self.module.advance_clean_streak(
                    self.control, {"current_route_id": "route-alpha-high", "clean_streak": 2},
                    objective(**overrides),
                )
                self.assertFalse(advanced["clean_pass"])
                self.assertEqual(advanced["clean_streak"], 0)

    def test_the_bar_is_the_declared_trigger_rather_than_a_breach(self) -> None:
        # FR-012a.1: a trigger that fired is evidence the route was strained, and
        # it is the same threshold the policy escalates on.
        trigger = self.control["adaptive"]["budget_triggers"][0]
        at_threshold = objective(budget_observations={trigger["member"]: trigger["threshold"]})
        self.assertFalse(
            self.module.advance_clean_streak(self.control, self.state, at_threshold)["clean_pass"]
        )
        below = objective(budget_observations={trigger["member"]: trigger["threshold"] - 1})
        self.assertTrue(
            self.module.advance_clean_streak(self.control, self.state, below)["clean_pass"]
        )

    def test_an_objective_in_which_the_policy_escalated_never_counts(self) -> None:
        # FR-012a.2: the clean run that licenses a step down is always measured
        # at the route the policy moved to, never at the route it left.
        advanced = self.module.advance_clean_streak(
            self.control, {"current_route_id": "route-alpha-high", "clean_streak": 2},
            objective(escalated=True),
        )
        self.assertFalse(advanced["clean_pass"])
        self.assertEqual(advanced["clean_streak"], 0)
        self.assertFalse(advanced["de_escalated"])

    def test_three_consecutive_clean_passes_step_down_at_the_boundary(self) -> None:
        final = self.walk([objective(), objective(), objective()])
        self.assertTrue(final["de_escalation_evaluated"])
        self.assertTrue(final["de_escalated"])
        self.assertEqual(final["current_route_id"], "route-alpha-low")
        self.assertEqual(final["clean_streak"], 0)

    def test_an_interrupted_streak_does_not_step_down(self) -> None:
        final = self.walk([objective(), objective(retries=1), objective()])
        self.assertFalse(final["de_escalated"])
        self.assertEqual(final["current_route_id"], "route-alpha-high")
        self.assertEqual(final["clean_streak"], 1)

    def test_a_non_scorable_objective_neither_advances_nor_resets_the_streak(self) -> None:
        reroute = objective(failure_code="service_reroute", failure_plane="treatment")
        self.assertEqual(self.module.resolve_response(self.control, reroute), "non_scorable")
        carried = self.walk([objective(), objective(), reroute])
        self.assertTrue(carried["excluded"])
        self.assertEqual(carried["clean_streak"], 2)
        self.assertEqual(carried["current_route_id"], "route-alpha-high")

    def test_the_streak_resumes_across_an_excluded_objective_and_completes(self) -> None:
        # FR-012a.3 and SC-024: proven by walking the sequence, not asserted.
        reroute = objective(failure_code="service_reroute", failure_plane="treatment")
        final = self.walk([objective(), objective(), reroute, objective()])
        self.assertTrue(final["de_escalated"])
        self.assertEqual(final["current_route_id"], "route-alpha-low")

    def test_the_non_scorable_exclusion_outranks_the_reset_on_non_clean_rule(self) -> None:
        # The row is non-clean on every other member and still leaves the streak
        # untouched, which is what "takes precedence" means.
        reroute = objective(
            terminal_state="failed", failure_code="service_reroute",
            failure_plane="treatment", retries=4,
        )
        carried = self.module.advance_clean_streak(
            self.control, {"current_route_id": "route-alpha-high", "clean_streak": 2}, reroute
        )
        self.assertEqual(carried["clean_streak"], 2)
        self.assertFalse(carried["clean_pass"])

    def test_the_streak_resets_whenever_de_escalation_is_evaluated(self) -> None:
        # FR-012a.4: reaching three licenses at most one downward step, not a
        # further step at every subsequent boundary.
        final = self.walk([objective(), objective(), objective(), objective()])
        self.assertEqual(final["current_route_id"], "route-alpha-low")
        self.assertEqual(final["clean_streak"], 1)

    def test_a_de_escalation_due_at_the_first_entry_records_no_step(self) -> None:
        floor = {"current_route_id": "route-alpha-low", "clean_streak": 0}
        final = self.walk([objective(), objective(), objective()], state=floor)
        self.assertTrue(final["de_escalation_evaluated"])
        self.assertFalse(final["de_escalated"])
        self.assertEqual(final["current_route_id"], "route-alpha-low")
        self.assertNotEqual(final["current_route_id"], "route-beta-medium")
        self.assertEqual(final["clean_streak"], 0)

    def test_a_state_naming_a_route_outside_the_ladder_fails_closed(self) -> None:
        with self.assertRaises(self.error):
            self.module.advance_clean_streak(
                self.control, {"current_route_id": "route-gamma-max", "clean_streak": 2},
                objective(),
            )


def bounded_objective(attempts: list[dict[str, object]],
                      counted_over: str = "per_objective",
                      **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "objective_id": "car-004-smoke-objective-1",
        "counted_over": counted_over,
        "attempts": attempts,
    }
    row.update(overrides)
    return row


def attempt(route_id: str, retries: int, duration_ms: int,
            **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "attempt_id": f"{route_id}-{retries}-{duration_ms}",
        "route_id": route_id,
        "retries": retries,
        "duration_ms": duration_ms,
    }
    row.update(overrides)
    return row


class BoundScopeAndBreachTests(unittest.TestCase):
    """FR-014 and FR-014a: scope, non-reset across escalation, and breach outcomes."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.registry = synthetic_registry()
        self.control = control_of_kind(self.registry, "adaptive")
        self.orchestration = control_of_kind(self.registry, "orchestration_changing")

    def test_both_counters_span_every_attempt_and_every_route_in_the_objective(self) -> None:
        # FR-014a.1: an escalation resets neither counter, so the two attempts on
        # two different routes are one count rather than two.
        reading = self.module.evaluate_bounds(
            self.control,
            bounded_objective([
                attempt("route-alpha-low", 1, 300000),
                attempt("route-alpha-high", 1, 400000),
            ]),
        )
        self.assertEqual(reading["retries"], 2)
        self.assertEqual(reading["duration_ms"], 700000)
        self.assertFalse(reading["retry_bound_breached"])
        self.assertFalse(reading["cancellation_bound_breached"])

    def test_an_attempt_recording_a_counter_reset_on_escalation_is_refused(self) -> None:
        with self.assertRaises(self.error):
            self.module.evaluate_bounds(
                self.control,
                bounded_objective([
                    attempt("route-alpha-low", 2, 300000),
                    attempt("route-alpha-high", 1, 300000, counter_reset_on_escalation=True),
                ]),
            )

    def test_a_scope_disagreeing_with_the_declared_counted_over_is_refused(self) -> None:
        cases = ((self.control, "per_unit"), (self.orchestration, "per_objective"))
        for control, seeded in cases:
            with self.subTest(control_kind=control["control_kind"], seeded=seeded):
                with self.assertRaises(self.error):
                    self.module.evaluate_bounds(
                        control,
                        bounded_objective([attempt("route-alpha-low", 0, 1000)], seeded),
                    )

    def test_the_orchestration_control_counts_both_bounds_over_the_whole_unit(self) -> None:
        # FR-014a.2: a run cannot stay inside its bounds by distributing retries
        # or elapsed time across children.
        declared = self.orchestration["execution_contract"]
        self.assertEqual(declared["retry_bounds"]["counted_over"], "per_unit")
        self.assertEqual(declared["cancellation_bounds"]["counted_over"], "per_unit")
        reading = self.module.evaluate_bounds(
            self.orchestration,
            bounded_objective([
                attempt("parent", 1, 400000),
                attempt("child-1", 1, 400000),
                attempt("child-2", 1, 400000),
            ], "per_unit"),
        )
        self.assertEqual(reading["retries"], 3)
        self.assertTrue(reading["retry_bound_breached"])
        self.assertTrue(reading["cancellation_bound_breached"])

    def test_a_retry_bound_breach_records_failed_with_the_paired_candidate_code(self) -> None:
        reading = self.module.evaluate_bounds(
            self.control, bounded_objective([attempt("route-alpha-low", 3, 10000)])
        )
        self.assertTrue(reading["retry_bound_breached"])
        self.assertEqual(reading["terminal_state"], "failed")
        self.assertEqual(reading["failure_code"], "candidate_failed")
        self.assertEqual(
            reading["failure_code"], self.module.candidate_code_for(reading["terminal_state"])
        )

    def test_a_cancellation_bound_breach_records_cancelled_with_its_paired_code(self) -> None:
        reading = self.module.evaluate_bounds(
            self.control, bounded_objective([attempt("route-alpha-low", 0, 900001)])
        )
        self.assertTrue(reading["cancellation_bound_breached"])
        self.assertEqual(reading["terminal_state"], "cancelled")
        self.assertEqual(reading["failure_code"], "candidate_cancelled")

    def test_a_recorded_outcome_other_than_the_declared_breach_pairing_is_refused(self) -> None:
        # timed_out and budget_exhausted stay reserved and are not representable
        # on the bound execution trace.
        cases = (
            ({"terminal_state": "timed_out", "failure_code": "candidate_timed_out"},
             [attempt("route-alpha-low", 0, 900001)]),
            ({"terminal_state": "budget_exhausted",
              "failure_code": "candidate_budget_exhausted"},
             [attempt("route-alpha-low", 3, 10000)]),
            ({"terminal_state": "abandoned", "failure_code": "candidate_abandoned"},
             [attempt("route-alpha-low", 3, 10000)]),
            ({"terminal_state": "failed", "failure_code": "candidate_cancelled"},
             [attempt("route-alpha-low", 3, 10000)]),
        )
        for outcome, attempts in cases:
            with self.subTest(recorded_outcome=outcome):
                with self.assertRaises(self.error):
                    self.module.evaluate_bounds(
                        self.control, bounded_objective(attempts, recorded_outcome=outcome)
                    )

    def test_a_respected_run_records_no_breach_outcome(self) -> None:
        reading = self.module.evaluate_bounds(
            self.control, bounded_objective([attempt("route-alpha-low", 2, 900000)])
        )
        self.assertFalse(reading["retry_bound_breached"])
        self.assertFalse(reading["cancellation_bound_breached"])
        self.assertIsNone(reading["terminal_state"])
        self.assertIsNone(reading["failure_code"])


class ServiceRerouteTests(unittest.TestCase):
    """FR-015 and FR-015a: the already-frozen observable, never a coined signal."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.control = control_of_kind(synthetic_registry(), "adaptive")
        self.row = objective(failure_code="service_reroute", failure_plane="treatment")

    def test_the_observable_is_the_code_the_frozen_module_already_publishes(self) -> None:
        import claude_score_bundle

        self.assertEqual(
            self.module.SERVICE_REROUTE_FAILURE_CODE,
            claude_score_bundle.SERVICE_REROUTE_FAILURE_CODE,
        )
        self.assertEqual(
            self.module.SERVICE_REROUTE_DISPOSITION_REASON,
            claude_score_bundle.SERVICE_REROUTE_DISPOSITION_REASON,
        )
        self.assertIn(self.module.SERVICE_REROUTE_FAILURE_CODE, frozen_failure_codes())

    def test_a_reroute_row_resolves_non_scorable_and_spends_no_allowance(self) -> None:
        classified = self.module.classify_service_reroute(self.control, self.row)
        self.assertTrue(classified["service_reroute"])
        self.assertEqual(classified["response"], "non_scorable")
        self.assertFalse(classified["escalation_allowance_spent"])
        self.assertFalse(classified["ladder_position_changed"])
        self.assertEqual(classified["failure_plane"], failure_plane_for("service_reroute"))
        self.assertEqual(
            classified["disposition_reason"], self.module.SERVICE_REROUTE_DISPOSITION_REASON
        )

    def test_a_reroute_makes_a_whole_orchestration_unit_non_scorable(self) -> None:
        # terminal_state_severity carries no non-scorable member, so a rerouted
        # member cannot be folded away.
        classified = self.module.classify_service_reroute(self.control, self.row)
        self.assertTrue(classified["unit_non_scorable"])
        severity = control_of_kind(synthetic_registry(), "orchestration_changing")[
            "orchestration_changing"
        ]["terminal_state_severity"]
        self.assertNotIn("non_scorable", severity)

    def test_a_row_carrying_any_other_code_is_not_classified_as_a_reroute(self) -> None:
        for code in ("none", "candidate_failed", "treatment_misdelivery"):
            with self.subTest(failure_code=code):
                row = objective(failure_code=code, failure_plane=failure_plane_for(code))
                classified = self.module.classify_service_reroute(self.control, row)
                self.assertFalse(classified["service_reroute"])
                self.assertFalse(classified["unit_non_scorable"])

    def test_a_reroute_row_leaves_the_ladder_position_untouched(self) -> None:
        state = {"current_route_id": "route-alpha-high", "clean_streak": 1}
        carried = self.module.advance_clean_streak(self.control, state, self.row)
        self.assertEqual(carried["current_route_id"], "route-alpha-high")
        self.assertFalse(carried["de_escalated"])


ADDITIVE_DIMENSIONS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "duration_ms",
    "retries",
    "compactions",
)


def unit_member(row_id: str, spawned_by: str | None = None, *,
                terminal_state: str = "completed", acceptance: float | None = None,
                cost: int = 10, **overrides: object) -> dict[str, object]:
    member: dict[str, object] = {
        "row_id": row_id,
        "spawned_by": spawned_by,
        "resource_vector": {
            **{dimension: cost for dimension in ADDITIVE_DIMENSIONS},
            "acceptance": acceptance,
            "terminal_state": terminal_state,
        },
    }
    member.update(overrides)
    return member


class AggregateFoldTests(unittest.TestCase):
    """FR-016, FR-016a, FR-016b, FR-016c: what sums, what folds, what floors."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.control = control_of_kind(synthetic_registry(), "orchestration_changing")
        self.severity = self.control["orchestration_changing"]["terminal_state_severity"]

    def test_the_additive_dimensions_sum_across_the_parent_and_every_member(self) -> None:
        parent = unit_member("parent", acceptance=0.9, cost=10)
        children = [
            unit_member("child-1", "parent", terminal_state="failed", cost=3),
            unit_member("child-2", "parent", terminal_state="timed_out", cost=5),
            unit_member("child-3", "parent", terminal_state="cancelled", cost=7),
        ]
        folded = self.module.aggregate_objective(parent, children, self.control)
        for dimension in ADDITIVE_DIMENSIONS:
            with self.subTest(dimension=dimension):
                self.assertEqual(folded[dimension], 25)

    def test_a_zero_child_run_folds_to_the_parent_s_own_values(self) -> None:
        parent = unit_member("parent", acceptance=0.75, cost=11)
        folded = self.module.aggregate_objective(parent, [], self.control)
        for dimension in ADDITIVE_DIMENSIONS:
            with self.subTest(dimension=dimension):
                self.assertEqual(folded[dimension], 11)
        self.assertEqual(folded["terminal_state"], "completed")
        self.assertEqual(folded["acceptance"], 0.75)

    def test_the_aggregate_state_is_completed_only_when_every_member_completed(self) -> None:
        parent = unit_member("parent", acceptance=1.0)
        self.assertEqual(
            self.module.aggregate_objective(
                parent, [unit_member("child-1", "parent")], self.control
            )["terminal_state"],
            "completed",
        )
        folded = self.module.aggregate_objective(
            parent, [unit_member("child-1", "parent", terminal_state="failed")], self.control
        )
        self.assertEqual(folded["terminal_state"], "failed")

    def test_the_fold_returns_the_most_severe_member_state(self) -> None:
        cases = (
            (["completed", "failed", "timed_out"], "timed_out"),
            (["completed", "abandoned", "failed"], "abandoned"),
            (["cancelled", "budget_exhausted"], "budget_exhausted"),
            (["completed", "completed"], "completed"),
        )
        for states, expected in cases:
            with self.subTest(states=states):
                self.assertEqual(
                    self.module.worst_terminal_state(states, self.severity), expected
                )

    def test_a_state_outside_the_declared_severity_order_fails_closed(self) -> None:
        for states in ([], ["completed", "quiesced"], ["completed", None]):
            with self.subTest(states=states):
                with self.assertRaises(self.error):
                    self.module.worst_terminal_state(states, self.severity)

    def test_the_severity_array_is_validated_set_equal_rather_than_order_equal(self) -> None:
        # FR-016a: a future reordering of the mirrored enum must not silently
        # change a verdict, so membership is the check and order is a declaration.
        self.assertEqual(sorted(self.severity), sorted(frozen_terminal_states()))
        permuted = copy.deepcopy(self.control)
        permuted["orchestration_changing"]["terminal_state_severity"] = list(
            reversed(self.severity)
        )
        self.assertIsNone(self.module.validate_orchestration_control(permuted))

    def test_a_severity_array_that_is_not_set_equal_to_the_frozen_enum_is_refused(self) -> None:
        cases = {
            "dropped": [state for state in self.severity if state != "abandoned"],
            "added": list(self.severity) + ["quiesced"],
            "substituted": [
                "quiesced" if state == "abandoned" else state for state in self.severity
            ],
        }
        for label, seeded in cases.items():
            with self.subTest(severity=label):
                control = copy.deepcopy(self.control)
                control["orchestration_changing"]["terminal_state_severity"] = seeded
                with self.assertRaises(self.error):
                    self.module.validate_orchestration_control(control)

    def test_the_aggregation_rule_is_total_over_all_eight_pareto_dimensions(self) -> None:
        rule = self.control["orchestration_changing"]["aggregation_rule"]
        self.assertEqual(sorted(rule), sorted(frozen_pareto_dimensions()))
        for dimension in frozen_pareto_dimensions():
            with self.subTest(omitted=dimension):
                control = copy.deepcopy(self.control)
                del control["orchestration_changing"]["aggregation_rule"][dimension]
                with self.assertRaises(self.error):
                    self.module.validate_orchestration_control(control)

    def test_acceptance_is_the_parent_objective_oracle_result(self) -> None:
        parent = unit_member("parent", acceptance=0.8)
        folded = self.module.aggregate_objective(
            parent, [unit_member("child-1", "parent", acceptance=0.1)], self.control
        )
        self.assertEqual(folded["acceptance"], 0.8)

    def test_acceptance_floors_to_zero_whenever_the_unit_did_not_complete(self) -> None:
        for state in [s for s in self.severity if s != "completed"]:
            with self.subTest(child_terminal_state=state):
                folded = self.module.aggregate_objective(
                    unit_member("parent", acceptance=0.95),
                    [unit_member("child-1", "parent", terminal_state=state)],
                    self.control,
                )
                self.assertEqual(folded["terminal_state"], state)
                self.assertEqual(folded["acceptance"], 0)

    def test_a_failed_child_floors_acceptance_while_its_cost_still_sums(self) -> None:
        folded = self.module.aggregate_objective(
            unit_member("parent", acceptance=1.0, cost=10),
            [unit_member("child-1", "parent", terminal_state="failed", cost=6)],
            self.control,
        )
        self.assertEqual(folded["acceptance"], 0)
        self.assertEqual(folded["input_tokens"], 16)

    def test_acceptance_is_null_only_on_a_completed_unit_whose_oracle_did_not_run(self) -> None:
        # FR-016c: the FR-016b floor outranks the null allowance wherever they meet.
        completed = self.module.aggregate_objective(
            unit_member("parent", acceptance=None), [unit_member("child-1", "parent")],
            self.control,
        )
        self.assertIsNone(completed["acceptance"])
        failed = self.module.aggregate_objective(
            unit_member("parent", acceptance=None),
            [unit_member("child-1", "parent", terminal_state="failed")], self.control,
        )
        self.assertEqual(failed["acceptance"], 0)

    def test_a_child_missing_its_own_value_never_induces_a_null_aggregate(self) -> None:
        folded = self.module.aggregate_objective(
            unit_member("parent", acceptance=0.6),
            [unit_member("child-1", "parent", acceptance=None)], self.control,
        )
        self.assertEqual(folded["acceptance"], 0.6)

    def test_a_recorded_aggregate_disagreeing_with_the_fold_is_refused(self) -> None:
        parent = unit_member("parent", acceptance=1.0)
        parent["recorded_aggregate"] = {"terminal_state": "completed", "acceptance": 1.0}
        with self.assertRaises(self.error):
            self.module.aggregate_objective(
                parent, [unit_member("child-1", "parent", terminal_state="failed")], self.control
            )

    def test_a_reroute_anywhere_in_the_unit_makes_the_whole_unit_non_scorable(self) -> None:
        folded = self.module.aggregate_objective(
            unit_member("parent", acceptance=1.0),
            [unit_member("child-1", "parent", failure_code="service_reroute")],
            self.control,
        )
        self.assertTrue(folded["non_scorable"])
        self.assertNotIn("non_scorable", self.severity)

    def test_no_committed_fixture_row_carries_a_null_aggregate_acceptance(self) -> None:
        # FR-016c and SC-015. The scan is over whatever the fixture root carries,
        # so it stays load-bearing as the replay fixtures land.
        self.assertTrue(FIXTURE_ROOT.is_dir())
        for path in sorted(FIXTURE_ROOT.glob("*.json")):
            document = load_json(path)
            for case in document.get("cases", []):
                aggregate = case.get("expected_aggregate")
                if aggregate is None:
                    continue
                with self.subTest(fixture=path.name, case=case.get("case_id")):
                    self.assertIsNotNone(aggregate.get("acceptance"))


def graph(root: str, parent: str | None, children: list[str]) -> dict[str, object]:
    """The shared treatment-record contract's parent_child_graph shape."""
    return {
        "root_execution_trace_id": root,
        "parent_execution_trace_id": parent,
        "child_execution_trace_ids": children,
    }


class UnitMembershipTests(unittest.TestCase):
    """FR-016d, FR-017, FR-017a, FR-018: who is in the unit, and how many may be."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.control = control_of_kind(synthetic_registry(), "orchestration_changing")
        self.rows = [
            unit_member("parent", None, cost=10),
            unit_member("child-1", "parent", cost=4),
            unit_member("grandchild-1", "child-1", cost=6),
        ]

    def test_a_nested_grandchild_is_inside_the_unit(self) -> None:
        # FR-016d.1: a topology cannot shed cost by nesting a child one level
        # deeper, so the closure is transitive rather than one generation.
        members = self.module.unit_members(self.rows, self.control)
        self.assertEqual(
            [member["row_id"] for member in members], ["parent", "child-1", "grandchild-1"]
        )

    def test_a_nested_grandchild_contributes_to_the_additive_sum(self) -> None:
        members = self.module.unit_members(self.rows, self.control)
        folded = self.module.aggregate_objective(members[0], members[1:], self.control)
        self.assertEqual(folded["input_tokens"], 20)

    def test_the_fan_out_ceiling_is_read_against_every_non_parent_member(self) -> None:
        # FR-016d.2: nesting does not buy fan-out headroom either.
        self.assertEqual(self.control["orchestration_changing"]["topology_descriptor"]["fan_out"], 3)
        self.assertEqual(len(self.module.unit_members(self.rows, self.control)), 3)
        over = self.rows + [
            unit_member("child-2", "parent"),
            unit_member("grandchild-2", "child-1"),
        ]
        with self.assertRaises(self.error):
            self.module.unit_members(over, self.control)

    def test_a_zero_child_run_conforms_to_the_declared_ceiling(self) -> None:
        # FR-017a: fan_out is a ceiling, never an exact count.
        members = self.module.unit_members([unit_member("parent", None)], self.control)
        self.assertEqual([member["row_id"] for member in members], ["parent"])

    def test_a_member_recording_no_terminal_state_is_refused(self) -> None:
        for seeded in (None, "absent"):
            with self.subTest(terminal_state=seeded):
                rows = copy.deepcopy(self.rows)
                if seeded == "absent":
                    del rows[1]["resource_vector"]["terminal_state"]
                else:
                    rows[1]["resource_vector"]["terminal_state"] = None
                with self.assertRaises(self.error):
                    self.module.unit_members(rows, self.control)

    def test_a_row_carrying_no_authored_spawn_link_is_refused(self) -> None:
        rows = copy.deepcopy(self.rows)
        del rows[1]["spawned_by"]
        with self.assertRaises(self.error):
            self.module.unit_members(rows, self.control)

    def test_more_than_one_parentless_row_leaves_the_boundary_undecidable(self) -> None:
        rows = copy.deepcopy(self.rows) + [unit_member("orphan-parent", None)]
        with self.assertRaises(self.error):
            self.module.unit_members(rows, self.control)

    def test_a_spawn_link_naming_no_row_in_the_set_is_refused(self) -> None:
        rows = copy.deepcopy(self.rows)
        rows[2]["spawned_by"] = "child-absent"
        with self.assertRaises(self.error):
            self.module.unit_members(rows, self.control)

    def test_the_boundary_must_agree_with_a_bound_parent_child_graph(self) -> None:
        rows = copy.deepcopy(self.rows)
        rows[0]["parent_child_graph"] = graph("parent", None, ["child-1"])
        rows[1]["parent_child_graph"] = graph("parent", "parent", ["grandchild-1"])
        rows[2]["parent_child_graph"] = graph("parent", "child-1", [])
        self.assertEqual(len(self.module.unit_members(rows, self.control)), 3)

    def test_a_graph_disagreeing_with_the_authored_links_fails_the_row_closed(self) -> None:
        cases = {
            "child_set": graph("parent", None, ["child-1", "child-2"]),
            "parent_link": graph("parent", "child-1", ["child-1"]),
            "root": graph("child-1", None, ["child-1"]),
        }
        for label, seeded in cases.items():
            with self.subTest(disagreement=label):
                rows = copy.deepcopy(self.rows)
                rows[0]["parent_child_graph"] = seeded
                with self.assertRaises(self.error):
                    self.module.unit_members(rows, self.control)

    def test_a_member_binding_no_graph_leaves_the_authored_links_standing_alone(self) -> None:
        # The obligation is conditional on the binding existing: a replay case
        # need not bind a full execution trace.
        rows = copy.deepcopy(self.rows)
        rows[0]["parent_child_graph"] = graph("parent", None, ["child-1"])
        self.assertEqual(len(self.module.unit_members(rows, self.control)), 3)

    def test_evidence_is_attributed_at_policy_level_only(self) -> None:
        # FR-018: never as evidence about any single agent's route.
        self.assertEqual(self.control["attribution_level"], "policy")
        control = copy.deepcopy(self.control)
        control["attribution_level"] = "route"
        with self.assertRaises(self.error):
            self.module.unit_members(self.rows, control)

    def test_the_topology_descriptor_declares_exactly_its_three_frozen_members(self) -> None:
        descriptor = self.control["orchestration_changing"]["topology_descriptor"]
        self.assertEqual(sorted(descriptor), ["child_shape", "fan_out", "topology_id"])
        self.assertEqual(
            sorted(descriptor["child_shape"]), ["dispatch_mechanism", "wall_time_window"]
        )
        self.assertEqual(
            descriptor["child_shape"]["wall_time_window"], "full_elapsed_including_child_wait"
        )
        self.assertEqual(
            self.control["orchestration_changing"]["topology_digest"],
            record_digest(descriptor),
        )

    def test_a_topology_digest_that_does_not_recompute_is_refused(self) -> None:
        control = copy.deepcopy(self.control)
        control["orchestration_changing"]["topology_descriptor"]["fan_out"] = 4
        with self.assertRaises(self.error):
            self.module.validate_orchestration_control(control)


TREATMENT_RECORD_SCHEMA_PATH = SHARED_CONTRACT_ROOT / "treatment-record.schema.json"
ADDITIVE_RECORDS_SCHEMA_PATH = CONTRACT_ROOT / "car-003-additive-records.schema.json"


def frozen_raw_token_members() -> list[str]:
    return list(load_json(TREATMENT_RECORD_SCHEMA_PATH)["$defs"]["rawTokenVector"]["required"])


def frozen_cache_ttl_classes() -> list[str]:
    diagnostic = load_json(ADDITIVE_RECORDS_SCHEMA_PATH)["$defs"]["cacheDiagnosticRecord"]
    return list(
        diagnostic["properties"]["cache_write_tokens_by_ttl_class"]["propertyNames"]["enum"]
    )


def tokened_member(row_id: str, spawned_by: str | None = None, *,
                   raw: tuple[int, int, int, int | None] = (100, 20, 30, 5),
                   cache: tuple[int, int, int] | None = (7, 3, 40),
                   **overrides: object) -> dict[str, object]:
    member = unit_member(row_id, spawned_by, **overrides)
    member["raw_token_vector"] = {
        "input_tokens": raw[0],
        "output_tokens": raw[1],
        "cached_input_tokens": raw[2],
        "reasoning_output_tokens": raw[3],
    }
    if cache is not None:
        member["cache_diagnostic"] = {
            "cache_write_tokens_by_ttl_class": {
                "ephemeral_5m": cache[0],
                "ephemeral_1h": cache[1],
            },
            "cache_read_tokens": cache[2],
        }
    return member


class RawTokenAndCacheAggregationTests(unittest.TestCase):
    """FR-016e: four raw members sum, two cache quantities sum, and none is promoted."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.control = control_of_kind(synthetic_registry(), "orchestration_changing")
        self.members = [
            tokened_member("parent", None),
            tokened_member("child-1", "parent", raw=(200, 40, 60, 11), cache=(13, 5, 80)),
        ]

    def test_all_four_frozen_raw_token_members_sum_across_the_unit(self) -> None:
        declared = self.control["orchestration_changing"]["raw_token_aggregation"]
        self.assertEqual(sorted(declared), sorted(frozen_raw_token_members()))
        folded = self.module.aggregate_raw_tokens_and_cache(self.members, self.control)
        self.assertEqual(
            folded["raw_tokens"],
            {
                "input_tokens": 300,
                "output_tokens": 60,
                "cached_input_tokens": 90,
                "reasoning_output_tokens": 16,
            },
        )

    def test_a_raw_token_aggregation_omitting_a_frozen_member_is_refused(self) -> None:
        for member in frozen_raw_token_members():
            with self.subTest(omitted=member):
                control = copy.deepcopy(self.control)
                del control["orchestration_changing"]["raw_token_aggregation"][member]
                with self.assertRaises(self.error):
                    self.module.validate_orchestration_control(control)

    def test_reasoning_tokens_sum_but_are_not_a_pareto_dimension(self) -> None:
        # FR-016e.2: admitting it would add a ninth dimension to a frozen
        # eight-dimension policy.
        folded = self.module.aggregate_raw_tokens_and_cache(self.members, self.control)
        self.assertEqual(folded["raw_tokens"]["reasoning_output_tokens"], 16)
        self.assertNotIn("reasoning_output_tokens", frozen_pareto_dimensions())
        self.assertNotIn(
            "reasoning_output_tokens",
            self.control["orchestration_changing"]["aggregation_rule"],
        )

    def test_the_raw_token_ceiling_is_read_against_the_three_bounded_members_alone(self) -> None:
        # FR-030a and SC-028: reasoning tokens are summed and reported under no
        # ceiling, so they never move the quantity the ceiling is read against.
        folded = self.module.aggregate_raw_tokens_and_cache(self.members, self.control)
        self.assertEqual(
            sorted(folded["raw_token_ceiling_members"]),
            ["cached_input_tokens", "input_tokens", "output_tokens"],
        )
        self.assertEqual(folded["raw_token_ceiling_quantity"], 450)
        louder = copy.deepcopy(self.members)
        louder[0]["raw_token_vector"]["reasoning_output_tokens"] = 900000
        self.assertEqual(
            self.module.aggregate_raw_tokens_and_cache(louder, self.control)[
                "raw_token_ceiling_quantity"
            ],
            450,
        )
        self.assertNotIn(
            "reasoning_output_tokens", folded["raw_token_ceiling_members"]
        )

    def test_cache_write_sums_per_frozen_ttl_class_keyed_like_its_ceiling(self) -> None:
        folded = self.module.aggregate_raw_tokens_and_cache(self.members, self.control)
        self.assertEqual(
            folded["cache_write_tokens_by_ttl_class"], {"ephemeral_5m": 20, "ephemeral_1h": 8}
        )
        bounds = synthetic_registry()["smoke_bounds"]["max_cache_write_tokens_by_ttl_class"]
        self.assertEqual(
            sorted(folded["cache_write_tokens_by_ttl_class"]), sorted(bounds)
        )
        self.assertEqual(sorted(bounds), sorted(frozen_cache_ttl_classes()))

    def test_cache_read_sums_under_the_ceiling_that_bounds_it(self) -> None:
        folded = self.module.aggregate_raw_tokens_and_cache(self.members, self.control)
        self.assertEqual(folded["cache_read_tokens"], 120)
        self.assertEqual(folded["bounded_by"]["cache_read_tokens"], "max_cache_read_tokens")
        self.assertEqual(
            folded["bounded_by"]["cache_write_tokens_by_ttl_class"],
            "max_cache_write_tokens_by_ttl_class",
        )

    def test_neither_cache_quantity_is_promoted_by_being_aggregated(self) -> None:
        # FR-016e.4: not a Pareto dimension, not in the identity, and never read
        # against max_input_tokens.
        folded = self.module.aggregate_raw_tokens_and_cache(self.members, self.control)
        for quantity in ("cache_read_tokens", "cache_write_tokens_by_ttl_class"):
            with self.subTest(quantity=quantity):
                self.assertNotIn(quantity, frozen_pareto_dimensions())
                self.assertNotIn(quantity, folded["raw_token_ceiling_members"])
                self.assertNotEqual(folded["bounded_by"][quantity], "max_input_tokens")

    def test_a_member_with_no_cache_diagnostic_records_the_bound_unobserved(self) -> None:
        # FR-016e.5: never passed, never zero.
        members = copy.deepcopy(self.members)
        del members[1]["cache_diagnostic"]
        folded = self.module.aggregate_raw_tokens_and_cache(members, self.control)
        self.assertIsNone(folded["cache_read_tokens"])
        self.assertIsNone(folded["cache_write_tokens_by_ttl_class"])
        self.assertEqual(
            sorted(folded["unobserved"]),
            ["max_cache_read_tokens", "max_cache_write_tokens_by_ttl_class"],
        )
        self.assertEqual(
            self.control["orchestration_changing"]["unrecorded_quantity_disposition"],
            "unobserved",
        )

    def test_a_null_cache_quantity_is_unobserved_rather_than_zero(self) -> None:
        members = copy.deepcopy(self.members)
        members[1]["cache_diagnostic"]["cache_read_tokens"] = None
        folded = self.module.aggregate_raw_tokens_and_cache(members, self.control)
        self.assertIsNone(folded["cache_read_tokens"])
        self.assertIn("max_cache_read_tokens", folded["unobserved"])
        self.assertEqual(
            folded["cache_write_tokens_by_ttl_class"], {"ephemeral_5m": 20, "ephemeral_1h": 8}
        )

    def test_a_null_reasoning_report_leaves_the_reasoning_sum_unobserved(self) -> None:
        members = copy.deepcopy(self.members)
        members[1]["raw_token_vector"]["reasoning_output_tokens"] = None
        folded = self.module.aggregate_raw_tokens_and_cache(members, self.control)
        self.assertIsNone(folded["raw_tokens"]["reasoning_output_tokens"])
        self.assertEqual(folded["raw_token_ceiling_quantity"], 450)

    def test_a_cache_aggregation_keyed_unlike_its_ceiling_is_refused(self) -> None:
        control = copy.deepcopy(self.control)
        aggregation = control["orchestration_changing"]["cache_aggregation"]
        aggregation["cache_write_tokens_by_ttl_class"] = {"ephemeral_5m": "sum"}
        with self.assertRaises(self.error):
            self.module.validate_orchestration_control(control)

    def test_a_disposition_other_than_unobserved_is_refused(self) -> None:
        control = copy.deepcopy(self.control)
        control["orchestration_changing"]["unrecorded_quantity_disposition"] = "zero"
        with self.assertRaises(self.error):
            self.module.validate_orchestration_control(control)


# --------------------------------------------------------------------------- #
# Deterministic replay of the committed fixture                                 #
# (FR-026, FR-027, FR-028, SC-005, SC-010)                                      #
# --------------------------------------------------------------------------- #

REPLAY_FIXTURE_PATH = FIXTURE_ROOT / "control-replay.json"
PARTITION_ENTRIES_PATH = FIXTURE_ROOT / "partition-registry-entries.json"

# The partition types CAR-004 registers but may never draw evidence from: the
# reserved comparison slice is `integrated_confirmation`, and `selection` is the
# other qualification-bearing type the frozen consumption path refuses.
WITHHELD_PARTITION_TYPES = ("selection", "integrated_confirmation")


def replay_rows() -> list[dict[str, object]]:
    """Every row of every committed replay case, flattened."""
    fixture = load_json(REPLAY_FIXTURE_PATH)
    return [row for case in fixture["cases"] for row in case["rows"]]


def withheld_objective_ids() -> set[str]:
    """Objective ids the committed entries reserve, read rather than transcribed."""
    entries = load_json(PARTITION_ENTRIES_PATH)["entries"]
    return {
        objective
        for entry in entries
        if entry["partition_type"] in WITHHELD_PARTITION_TYPES
        for objective in entry["objective_ids"]
    }


class ReplayDeterminismTests(unittest.TestCase):
    """FR-028 and SC-005: the same committed bytes replay to the same result."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError

    def test_two_replays_of_the_same_fixture_digest_identically(self) -> None:
        # SC-005's byte-identical claim is tested rather than asserted: the
        # replay output is digested twice under the frozen preimage rule.
        first = self.module.replay(REPLAY_FIXTURE_PATH)
        second = self.module.replay(REPLAY_FIXTURE_PATH)
        self.assertTrue(first)
        self.assertEqual(record_digest({"replay": first}), record_digest({"replay": second}))

    def test_the_replay_covers_every_committed_case(self) -> None:
        fixture = load_json(REPLAY_FIXTURE_PATH)
        replayed = self.module.replay(REPLAY_FIXTURE_PATH)
        self.assertEqual(
            [outcome["case_id"] for outcome in replayed],
            [case["case_id"] for case in fixture["cases"]],
        )

    def test_the_fixture_carries_no_run_time_value(self) -> None:
        # FR-028: no timestamp generated at run time, no randomness, no absolute
        # path, and no session identifier reaches the committed bytes.
        text = REPLAY_FIXTURE_PATH.read_text(encoding="utf-8")
        for forbidden in ("/Users/", "/home/", "session_"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)
        self.assertIsNone(re.search(r"\d{4}-\d{2}-\d{2}T", text))

    def test_every_replayed_row_is_recorded_non_scored(self) -> None:
        rows = replay_rows()
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(row=row["row_id"]):
                self.assertIs(row["scored"], False)

    def test_no_replayed_row_is_outcome_bearing(self) -> None:
        # FR-027 and SC-010: zero rows carry an outcome, so no replay evidence
        # can be read as qualification-bearing.
        self.assertEqual(
            [row["row_id"] for row in replay_rows() if row["outcome_bearing"]], []
        )

    def test_no_replayed_row_references_a_withheld_objective(self) -> None:
        withheld = withheld_objective_ids()
        self.assertTrue(withheld, "the committed entries reserve no objective at all")
        referenced = {row["objective_id"] for row in replay_rows()}
        self.assertEqual(sorted(referenced & withheld), [])

    def test_a_seeded_reserved_objective_reference_fails_the_replay_closed(self) -> None:
        fixture = load_json(REPLAY_FIXTURE_PATH)
        fixture["cases"][0]["rows"][0]["objective_id"] = sorted(withheld_objective_ids())[0]
        with tempfile.TemporaryDirectory() as directory:
            seeded = Path(directory) / "control-replay.json"
            seeded.write_text(json.dumps(fixture), encoding="utf-8")
            with self.assertRaises(self.error):
                self.module.replay(seeded)

    def test_a_seeded_scored_row_fails_the_replay_closed(self) -> None:
        fixture = load_json(REPLAY_FIXTURE_PATH)
        fixture["cases"][0]["rows"][0]["scored"] = True
        with tempfile.TemporaryDirectory() as directory:
            seeded = Path(directory) / "control-replay.json"
            seeded.write_text(json.dumps(fixture), encoding="utf-8")
            with self.assertRaises(self.error):
                self.module.replay(seeded)


# --------------------------------------------------------------------------- #
# The committed registry instance (SC-012, SC-017, SC-018)                      #
# --------------------------------------------------------------------------- #

REGISTRY_INSTANCE_PATH = FIXTURE_ROOT / "policy-control-registry.json"


class CommittedRegistryInstanceTests(unittest.TestCase):
    """Every rule above, run against the bytes the repository actually ships."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.registry = self.module.load_registry(REGISTRY_INSTANCE_PATH)

    def test_the_committed_instance_loads_through_the_schema_and_the_semantics(self) -> None:
        self.assertEqual(self.registry["schema_version"], "1.0.0")
        self.assertEqual(self.registry["status"], "frozen")
        self.assertEqual(len(self.registry["controls"]), len(CONTROL_KINDS))
        self.assertEqual(
            sorted(control["control_kind"] for control in self.registry["controls"]),
            sorted(CONTROL_KINDS),
        )

    def test_every_recorded_address_recomputes_over_the_committed_bytes(self) -> None:
        self.assertEqual(
            self.registry["registry_digest"],
            record_digest(self.registry, digest_field="registry_digest"),
        )
        for control in self.registry["controls"]:
            with self.subTest(control=control["control_id"]):
                self.assertEqual(
                    control["control_digest"],
                    record_digest(control, digest_field="control_digest"),
                )
        orchestration = control_of_kind(self.registry, "orchestration_changing")[
            "orchestration_changing"
        ]
        self.assertEqual(
            orchestration["topology_digest"],
            record_digest(orchestration["topology_descriptor"]),
        )

    def test_every_recorded_binding_matches_the_bound_document_s_committed_bytes(self) -> None:
        self.module.verify_car_003_bindings(self.registry)
        pin = control_of_kind(self.registry, "unpinned")["unpinned"]["pinned_parent_binding"]
        self.assertEqual(
            pin["digest"], file_bytes_digest(CONTRACT_ROOT / "experiment-assignment.schema.json")
        )

    def test_the_committed_smoke_bounds_carry_the_frozen_values_and_their_units(self) -> None:
        self.assertEqual(self.registry["smoke_bounds"], synthetic_smoke_bounds())

    def test_the_committed_adaptive_control_binds_the_committed_replay_freeze(self) -> None:
        freeze = load_json(REPLAY_FIXTURE_PATH)["bound_freeze"]
        self.assertEqual(
            freeze["freeze_digest"], record_digest(freeze, digest_field="freeze_digest")
        )
        control = control_of_kind(self.registry, "adaptive")
        self.assertEqual(control["adaptive"]["candidate_freeze_id"], freeze["candidate_freeze_id"])
        self.module.validate_escalation_ladder(control, freeze)

    def test_the_comparison_binding_pins_the_committed_reserved_membership_digest(self) -> None:
        entries = load_json(PARTITION_ENTRIES_PATH)["entries"]
        reserved = next(entry for entry in entries if entry["qualification_eligible"])
        comparison = load_json(FIXTURE_ROOT / "control-comparison.json")
        self.assertEqual(
            comparison["reserved_partition_binding"],
            {"id": reserved["partition_id"], "digest": reserved["objective_set_digest"]},
        )

    def test_a_seeded_byte_change_in_the_committed_instance_fails_closed(self) -> None:
        tampered = load_json(REGISTRY_INSTANCE_PATH)
        tampered["registry_id"] = "car-004-policy-control-registry-tampered"
        with tempfile.TemporaryDirectory() as directory:
            seeded = Path(directory) / "policy-control-registry.json"
            seeded.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaises(self.error):
                self.module.load_registry(seeded)


# --------------------------------------------------------------------------- #
# Reserved-partition registration and guard                                     #
# (FR-025a, FR-025b, FR-025c, FR-025d, FR-026, SC-007, SC-020)                  #
# --------------------------------------------------------------------------- #

OWNING_SPEC = "CAR-004"


def partition_entries() -> list[dict[str, object]]:
    return load_json(PARTITION_ENTRIES_PATH)["entries"]


def entry_of_eligibility(eligible: bool) -> dict[str, object]:
    """The committed entry on one side of the qualification-eligibility split.

    Selected by the flag the frozen admission path reads rather than by a
    transcribed partition id, so re-freezing the reservation moves these cases
    with it (FR-025a).
    """
    matches = [entry for entry in partition_entries() if entry["qualification_eligible"] is eligible]
    if len(matches) != 1:
        raise AssertionError(
            f"the committed entries record {len(matches)} partitions with "
            f"qualification_eligible={eligible}; exactly one is expected"
        )
    return matches[0]


def smoke_row(**overrides: object) -> dict[str, object]:
    """One row shaped like the bounded smoke record's, never committed (FR-033)."""
    row = {
        "row_id": "smoke-row-01",
        "objective_id": entry_of_eligibility(False)["objective_ids"][0],
        "partition_id": entry_of_eligibility(False)["partition_id"],
        "scored": False,
    }
    row.update(overrides)
    return row


class ReservedPartitionRegistrationTests(unittest.TestCase):
    """SC-020: disjointness is proven through the frozen path, not asserted."""

    def setUp(self) -> None:
        self.entries = partition_entries()
        self.reserved = entry_of_eligibility(True)
        self.smoke = entry_of_eligibility(False)

    def test_both_entries_record_the_freezing_spec_as_their_owner(self) -> None:
        # FR-025d: provenance is the spec that freezes them, never the successor
        # that later benefits from the reservation.
        for entry in self.entries:
            with self.subTest(partition=entry["partition_id"]):
                self.assertEqual(entry["owning_spec"], OWNING_SPEC)

    def test_both_entries_take_a_member_of_the_frozen_partition_type_set(self) -> None:
        # FR-025a: no new type is coined, and the smoke partition is the
        # calibration one the frozen consumption path admits.
        self.assertEqual(self.reserved["partition_type"], "integrated_confirmation")
        self.assertEqual(self.smoke["partition_type"], "calibration")
        self.assertIs(self.smoke["qualification_eligible"], False)

    def test_the_committed_entries_register_clean_through_the_frozen_path(self) -> None:
        # FR-025b: registered together, so disjointness is enforced mechanically
        # against each other rather than declared in prose.
        verdict = register_partitions(self.entries)
        self.assertTrue(verdict.ok, verdict.findings)
        self.assertEqual(verdict.failure_plane, "none")
        self.assertEqual(verdict.failure_code, "none")

    def test_a_seeded_duplicate_partition_identifier_fails_registration_closed(self) -> None:
        duplicate = copy.deepcopy(self.smoke)
        verdict = register_partitions([*self.entries, duplicate])
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_plane, PARTITION_PLANE)
        self.assertEqual(verdict.failure_code, PARTITION_MISMATCH)

    def test_a_seeded_shared_objective_fails_registration_closed(self) -> None:
        # Built through the frozen builder so its membership digest still matches
        # its preimage: the refusal proves the objective collision, not a stale
        # digest on a hand-edited record.
        intruder = build_partition_registry_entry(
            partition_id="CAR-004-SEEDED-OVERLAP",
            partition_type="calibration",
            qualification_eligible=False,
            objective_ids=[self.reserved["objective_ids"][0]],
            frozen_at=FROZEN_AT,
            owning_spec=OWNING_SPEC,
        )
        verdict = register_partitions([*self.entries, intruder])
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_plane, PARTITION_PLANE)
        self.assertEqual(verdict.failure_code, CROSS_PARTITION_REUSE)

    def test_the_frozen_builder_refuses_calibration_paired_with_eligibility(self) -> None:
        # FR-027: the smoke partition is structurally incapable of carrying
        # qualification-bearing rows, not merely instructed not to.
        with self.assertRaises(ExperimentPolicyError):
            build_partition_registry_entry(
                partition_id=self.smoke["partition_id"],
                partition_type="calibration",
                qualification_eligible=True,
                objective_ids=self.smoke["objective_ids"],
                frozen_at=FROZEN_AT,
                owning_spec=OWNING_SPEC,
            )


class ReservedPartitionGuardTests(unittest.TestCase):
    """FR-026 and SC-007: one entry point covers replay rows and smoke rows."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.guard = self.module.assert_reserved_partition_untouched
        self.reserved = entry_of_eligibility(True)
        self.reserved_objective = self.reserved["objective_ids"][0]

    def test_the_guard_passes_on_the_delivered_replay_evidence(self) -> None:
        rows = replay_rows()
        self.assertTrue(rows)
        self.assertIsNone(self.guard(rows, self.reserved))

    def test_the_guard_passes_on_a_clean_smoke_row_set(self) -> None:
        self.assertIsNone(self.guard([smoke_row()], self.reserved))

    def test_a_seeded_replay_row_fails_the_guard(self) -> None:
        rows = copy.deepcopy(replay_rows())
        rows[0]["objective_id"] = self.reserved_objective
        with self.assertRaises(self.error):
            self.guard(rows, self.reserved)

    def test_a_seeded_smoke_row_fails_the_guard(self) -> None:
        with self.assertRaises(self.error):
            self.guard([smoke_row(objective_id=self.reserved_objective)], self.reserved)

    def test_a_seeded_smoke_row_fails_the_guard_on_its_objective_array(self) -> None:
        # The smoke record carries its consumed objectives as an array, so the one
        # entry point reads both members rather than only the single-id shape.
        row = smoke_row(objective_ids=[self.reserved_objective])
        del row["objective_id"]
        with self.assertRaises(self.error):
            self.guard([row], self.reserved)

    def test_a_smoke_row_naming_the_reserved_partition_fails_the_guard(self) -> None:
        with self.assertRaises(self.error):
            self.guard([smoke_row(partition_id=self.reserved["partition_id"])], self.reserved)

    def test_a_reservation_declaring_no_objective_fails_the_guard_closed(self) -> None:
        # An empty reservation would let the guard pass on every row, certifying
        # non-consumption against nothing.
        with self.assertRaises(self.error):
            self.guard([smoke_row()], dict(self.reserved, objective_ids=[]))

    def test_a_row_the_guard_cannot_read_fails_closed(self) -> None:
        with self.assertRaises(self.error):
            self.guard([self.reserved_objective], self.reserved)

    def test_the_reserved_entry_is_read_from_the_committed_registration(self) -> None:
        # The replay half runs in the committed suite, so it resolves the
        # reservation itself rather than taking it from a caller (FR-026a.1).
        self.assertEqual(self.module.reserved_partition_entry(), self.reserved)


# --------------------------------------------------------------------------- #
# Bounded smoke record: bounds, counting scope, and the constraining mode        #
# (FR-027, FR-030, FR-030b, FR-030c, SC-009, SC-029, SC-030)                     #
# --------------------------------------------------------------------------- #

# The smoke partition's five objectives are committed; a sixth id is synthetic and
# exists only to push the attempt count past its frozen ceiling.
SIXTH_OBJECTIVE = "CAR-004-SMOKE-OBJ-06"


def smoke_unit_row(
    row_id: str,
    spawned_by: str | None = None,
    *,
    wall_time_ms: int | None = 60000,
    duration_ms: int = 60000,
    raw: tuple[int, int, int, int | None] = (1000, 200, 300, 50),
    cache: tuple[int, int, int] | None = (70, 30, 400),
) -> dict[str, object]:
    """One member of a smoke run's parent-plus-children unit.

    ``wall_time_ms`` is the frozen trace's own nullable member, read for the
    FR-031a.5 parallel inequality; ``duration_ms`` is the additive Pareto
    dimension, deliberately a different quantity from the elapsed wall clock the
    30-minute cap is read against (FR-030b.3).
    """
    row: dict[str, object] = {
        "row_id": row_id,
        "spawned_by": spawned_by,
        "wall_time_ms": wall_time_ms,
        "duration_ms": duration_ms,
        "raw_token_vector": {
            "input_tokens": raw[0],
            "output_tokens": raw[1],
            "cached_input_tokens": raw[2],
            "reasoning_output_tokens": raw[3],
        },
    }
    if cache is not None:
        row["cache_diagnostic"] = {
            "cache_write_tokens_by_ttl_class": {
                "ephemeral_5m": cache[0],
                "ephemeral_1h": cache[1],
            },
            "cache_read_tokens": cache[2],
        }
    return row


def smoke_attempt(
    objective_id: str, rows: list[dict[str, object]] | None = None
) -> dict[str, object]:
    """One objective attempt and the unit it dispatched."""
    return {
        "objective_id": objective_id,
        "unit_rows": rows if rows is not None else [smoke_unit_row(f"{objective_id}-parent")],
    }


def route_observation(model: str, effort: str, route_id: str) -> dict[str, object]:
    """The three frozen configured-route-proof members FR-031a.3 and .4 read back."""
    return {"model": model, "effort": effort, "candidate_route_id": route_id}


def demonstration_evidence(
    kind: str, control: dict[str, object] | None = None, **overrides: object
) -> dict[str, object]:
    """Evidence shaped as the run produced it, never as the dispatch asked for it.

    ``control`` anchors the evidence to the control it will be read against. The
    committed registry and the synthetic one declare different ladders and pins,
    so evidence quoting the wrong one demonstrates nothing — which now refuses
    the record rather than passing unnoticed.
    """
    ladder = LADDER_ROUTES
    pin_model, pin_effort = "model-alpha", "high"
    if isinstance(control, dict):
        adaptive = control.get("adaptive")
        if isinstance(adaptive, dict) and adaptive.get("escalation_ladder"):
            ladder = tuple(adaptive["escalation_ladder"])
        pin = control.get("unpinned")
        if isinstance(pin, dict):
            pin_model = str(pin.get("pinned_parent_model", pin_model))
            pin_effort = str(pin.get("pinned_parent_effort", pin_effort))
    if kind == "adaptive":
        evidence: dict[str, object] = {
            "read_back_from": "configured_route_proof",
            "pre_escalation": route_observation("model-alpha", "low", ladder[0]),
            "post_escalation": route_observation("model-alpha", "high", ladder[1]),
        }
    elif kind == "unpinned":
        evidence = {
            "read_back_from": "configured_route_proof",
            "served_route": route_observation(pin_model, pin_effort, ladder[1]),
        }
    else:
        evidence = {"read_back_from": "execution_trace"}
    evidence.update(overrides)
    return evidence


def smoke_record(control: dict[str, object], **overrides: object) -> dict[str, object]:
    """A produced smoke record, never committed (FR-033)."""
    partition = entry_of_eligibility(False)
    objective = partition["objective_ids"][0]
    kind = str(control["control_kind"])
    record: dict[str, object] = {
        "record_kind": "policy_control_smoke",
        "schema_version": "1.0.0",
        "smoke_id": f"car-004-smoke-{kind}",
        "arm_id": control["control_id"],
        "control_id": control["control_id"],
        "control_digest": control["control_digest"],
        "authentication_mode": "subscription",
        "scored": False,
        "partition_id": partition["partition_id"],
        "objective_ids": [objective],
        "confirmation_entries": 0,
        "elapsed_wall_clock_seconds": 600,
        "claude_code_subagent_model_unset": True,
        "objective_attempts": [smoke_attempt(objective)],
        # FR-032: a record claiming admissible evidence carries the pairwise
        # observation that backs the claim. An empty list discharges nothing, so
        # it is not what a conforming record looks like.
        "observed_cache_isolation": [isolation_pair(f"{control['control_id']}-paired")],
        "demonstration_state": "demonstrated",
        "demonstration_evidence": demonstration_evidence(kind, control),
    }
    record.update(overrides)
    return record


def smoke_attempts(count: int) -> list[dict[str, object]]:
    objectives = list(entry_of_eligibility(False)["objective_ids"]) + [SIXTH_OBJECTIVE]
    return [smoke_attempt(objective) for objective in objectives[:count]]


class SmokeRecordBoundTests(unittest.TestCase):
    """FR-030 and FR-030b: four bounds, one unit, one elapsed reading."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.registry = synthetic_registry()
        self.control = control_of_kind(self.registry, "unpinned")

    def validate(self, **overrides: object) -> dict[str, object]:
        return self.module.validate_smoke_record(
            smoke_record(self.control, **overrides), self.registry
        )

    def test_a_conforming_record_is_admitted_as_evidence(self) -> None:
        reading = self.validate()
        self.assertEqual(reading["evidence_admissibility"], "admitted")
        self.assertEqual(reading["refusal_reasons"], [])

    def test_all_four_frozen_bounds_are_read_over_the_parent_plus_children_unit(self) -> None:
        # FR-030b.1: an unscoped bound is not a bound, so the reading names the
        # scope it counted over and reports every frozen bound it read.
        reading = self.validate()
        self.assertEqual(reading["counted_over"], "parent_plus_children_unit")
        for member in ("max_attempts", "max_candidates", "raw_token_ceiling",
                       "max_duration_seconds"):
            with self.subTest(bound=member):
                self.assertIn(member, reading["consumed"])

    def test_a_consumed_budget_exceeding_a_frozen_bound_is_refused(self) -> None:
        objectives = [attempt["objective_id"] for attempt in smoke_attempts(6)]
        with self.assertRaises(self.error):
            self.validate(objective_attempts=smoke_attempts(6), objective_ids=objectives)

    def test_a_second_repetition_of_one_objective_breaches_the_candidate_bound(self) -> None:
        objective = entry_of_eligibility(False)["objective_ids"][0]
        with self.assertRaises(self.error):
            self.validate(objective_attempts=[smoke_attempt(objective), smoke_attempt(objective)])

    def test_a_child_dispatch_consumes_no_objective_attempt(self) -> None:
        # FR-030b.4: five objectives with three children each stays inside the
        # five-attempt ceiling; counting children would silently reduce it.
        attempts = smoke_attempts(5)
        for attempt in attempts:
            parent = str(attempt["objective_id"]) + "-parent"
            attempt["unit_rows"] = [smoke_unit_row(parent)] + [
                smoke_unit_row(f"{parent}-child-{index}", parent) for index in range(3)
            ]
        reading = self.validate(
            objective_attempts=attempts,
            objective_ids=[attempt["objective_id"] for attempt in attempts],
        )
        self.assertEqual(reading["consumed"]["max_attempts"], 5)
        self.assertEqual(reading["child_dispatch_count"], 15)

    def test_a_child_s_tokens_are_charged_to_the_unit(self) -> None:
        # FR-030b.1 and FR-030b.2: a run cannot stay inside a ceiling by
        # distributing spend across children.
        parent = smoke_unit_row("parent", raw=(400000, 100, 100, None))
        child = smoke_unit_row("child", "parent", raw=(500000, 100, 100, None))
        objective = entry_of_eligibility(False)["objective_ids"][0]
        with self.assertRaises(self.error):
            self.validate(objective_attempts=[smoke_attempt(objective, [parent, child])])

    def test_the_thirty_minute_cap_is_read_as_elapsed_rather_than_additive(self) -> None:
        # FR-030b.3: a parallel unit legitimately records an additive duration
        # larger than its elapsed time, and both are recorded.
        objective = entry_of_eligibility(False)["objective_ids"][0]
        parent = smoke_unit_row("parent", duration_ms=1_200_000)
        child = smoke_unit_row("child", "parent", duration_ms=1_200_000)
        reading = self.validate(
            objective_attempts=[smoke_attempt(objective, [parent, child])],
            elapsed_wall_clock_seconds=1200,
        )
        self.assertEqual(reading["evidence_admissibility"], "admitted")
        self.assertGreater(reading["additive_duration_ms"], 1800 * 1000)
        self.assertEqual(reading["consumed"]["max_duration_seconds"], 1200)

    def test_an_elapsed_wall_clock_past_the_cap_is_refused(self) -> None:
        with self.assertRaises(self.error):
            self.validate(elapsed_wall_clock_seconds=1801)

    def test_a_member_with_no_cache_diagnostic_records_its_bound_unobserved(self) -> None:
        # FR-016e.5 and FR-030b.2: never passed, never read as zero.
        objective = entry_of_eligibility(False)["objective_ids"][0]
        rows = [smoke_unit_row("parent"), smoke_unit_row("child", "parent", cache=None)]
        reading = self.validate(objective_attempts=[smoke_attempt(objective, rows)])
        self.assertEqual(
            sorted(reading["bounds_unobserved"]),
            ["max_cache_read_tokens", "max_cache_write_tokens_by_ttl_class"],
        )


class SmokeRecordEvidenceTests(unittest.TestCase):
    """FR-027 and FR-030c: what makes a produced record inadmissible."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.registry = synthetic_registry()
        self.control = control_of_kind(self.registry, "adaptive")
        self.reserved = entry_of_eligibility(True)

    def validate(self, **overrides: object) -> dict[str, object]:
        return self.module.validate_smoke_record(
            smoke_record(self.control, **overrides), self.registry
        )

    def test_an_observed_api_key_refuses_the_record_as_evidence(self) -> None:
        # FR-030c.3: refused as evidence rather than raised on, because the
        # observation itself is required to survive.
        reading = self.validate(authentication_mode="api_key")
        self.assertEqual(reading["evidence_admissibility"], "refused")
        self.assertIn(self.module.API_KEY_REFUSAL_REASON, reading["refusal_reasons"])

    def test_the_refused_record_keeps_its_observed_mode_beside_the_refusal(self) -> None:
        # An absent row and a refused row must never be indistinguishable.
        reading = self.validate(authentication_mode="api_key")
        self.assertEqual(reading["authentication_mode"], "api_key")
        self.assertIn("max_attempts", reading["consumed"])

    def test_the_mode_is_read_from_the_claude_side_frozen_member(self) -> None:
        # FR-030c.1: the shared runtime member of the same name enumerates
        # chatgpt_subscription, and recording against it would make the mode
        # incomparable with every CAR-003 record on this platform.
        shared = load_json(SHARED_ENVIRONMENT_CONTRACT_PATH)
        shared_modes = set(self.module.shared_environment_authentication_modes(shared))
        claude_modes = set(self.module.admissible_authentication_modes())
        self.assertNotEqual(shared_modes, claude_modes)
        self.assertEqual(claude_modes, {"subscription", "api_key"})
        with self.assertRaises(self.error):
            self.validate(authentication_mode="chatgpt_subscription")

    def test_a_scored_row_is_refused(self) -> None:
        for scored in (True, "false", None):
            with self.subTest(scored=scored):
                with self.assertRaises(self.error):
                    self.validate(scored=scored)

    def test_a_reserved_objective_reference_is_refused(self) -> None:
        objective = self.reserved["objective_ids"][0]
        with self.assertRaises(self.error):
            self.validate(objective_ids=[objective], objective_attempts=[smoke_attempt(objective)])

    def test_a_reserved_partition_reference_is_refused(self) -> None:
        with self.assertRaises(self.error):
            self.validate(partition_id=self.reserved["partition_id"])

    def test_a_record_naming_no_registry_control_is_refused(self) -> None:
        with self.assertRaises(self.error):
            self.validate(control_digest="sha256:" + "e" * 64)

    def test_the_recorded_objectives_must_agree_with_the_attempts(self) -> None:
        with self.assertRaises(self.error):
            self.validate(objective_ids=[SIXTH_OBJECTIVE])


# --------------------------------------------------------------------------- #
# Demonstration state and pairwise cache isolation                              #
# (FR-031, FR-031a, FR-032, FR-032a, SC-026, SC-027, SC-031)                    #
# --------------------------------------------------------------------------- #

CACHE_DIAGNOSTIC_SCHEMA_PATH = CONTRACT_ROOT / "car-003-additive-records.schema.json"


def frozen_isolation_statuses() -> list[str]:
    """The closed status set, read from the frozen cache diagnostic (FR-032a.1)."""
    diagnostic = load_json(CACHE_DIAGNOSTIC_SCHEMA_PATH)["$defs"]["cacheDiagnosticRecord"]
    return list(
        diagnostic["properties"]["observed_cache_isolation"]["properties"]["status"]["enum"]
    )


def isolation_pair(
    paired_arm_id: str, status: str = "observed_disjoint", **overrides: object
) -> dict[str, object]:
    """One unordered arm pair, in the frozen single-pair shape (FR-032a.4)."""
    disjoint = {"observed_disjoint": True, "observed_shared": False}.get(status)
    pair: dict[str, object] = {
        "paired_arm_id": paired_arm_id,
        "status": status,
        "arm_cache_root_digest": "sha256:" + "1" * 64,
        "paired_arm_cache_root_digest": "sha256:" + "2" * 64,
        "roots_disjoint": disjoint,
    }
    pair.update(overrides)
    return pair


def isolation_series(registry: dict[str, object], **statuses: str) -> list[dict[str, object]]:
    """The three smokes as one ordered series of three arms."""
    arms = [str(control["control_id"]) for control in registry["controls"]]
    series = []
    for arm in arms:
        pairs = [
            isolation_pair(other, statuses.get(f"{arm}|{other}", "observed_disjoint"))
            for other in arms
            if other != arm
        ]
        series.append({"arm_id": arm, "observed_cache_isolation": pairs})
    return series


def parallel_unit(*, parent_wall_time_ms: int | None = 50000,
                  child_wall_times: tuple[int | None, ...] = (40000, 40000)) -> list[dict]:
    rows = [smoke_unit_row("parent", wall_time_ms=parent_wall_time_ms)]
    rows.extend(
        smoke_unit_row(f"child-{index}", "parent", wall_time_ms=wall_time)
        for index, wall_time in enumerate(child_wall_times)
    )
    return rows


class DemonstrationStateTests(unittest.TestCase):
    """FR-031a: 'real' is decidable from evidence, or it is not demonstrated."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.registry = synthetic_registry()

    def record_for(self, kind: str, **overrides: object) -> dict[str, object]:
        control = control_of_kind(self.registry, kind)
        if kind == "orchestration_changing":
            objective = entry_of_eligibility(False)["objective_ids"][0]
            overrides.setdefault(
                "objective_attempts", [smoke_attempt(objective, parallel_unit())]
            )
        return smoke_record(control, **overrides)

    def evaluate(self, kind: str, **overrides: object) -> dict[str, object]:
        return self.module.evaluate_demonstration(self.record_for(kind, **overrides), self.registry)

    def test_every_smoke_records_the_frozen_subagent_model_observation(self) -> None:
        # FR-031a.6: all three carry one record shape, so the observation is a
        # required member of every smoke record rather than an adaptive extra.
        for kind in ("unpinned", "adaptive", "orchestration_changing"):
            with self.subTest(control_kind=kind):
                record = self.record_for(kind)
                del record["claude_code_subagent_model_unset"]
                with self.assertRaises(self.error):
                    self.module.validate_smoke_record(record, self.registry)

    def test_the_three_demonstrations_read_back_from_run_evidence(self) -> None:
        for kind in ("unpinned", "adaptive", "orchestration_changing"):
            with self.subTest(control_kind=kind):
                self.assertEqual(self.evaluate(kind)["demonstration_state"], "demonstrated")

    def test_an_observable_read_from_the_dispatch_request_is_not_a_demonstration(self) -> None:
        # FR-031a.1: a demonstration evidenced only by the request is refused.
        for kind in ("unpinned", "adaptive", "orchestration_changing"):
            with self.subTest(control_kind=kind):
                evidence = demonstration_evidence(
                    kind if kind != "orchestration_changing" else "orchestration",
                    read_back_from="dispatch_request",
                )
                observed = self.evaluate(kind, demonstration_evidence=evidence)
                self.assertEqual(observed["demonstration_state"], "not_demonstrated")

    def test_the_adaptive_smoke_moves_from_ladder_index_i_to_i_plus_one(self) -> None:
        # FR-031a.3: the route identifiers must be consecutive ladder entries.
        evidence = demonstration_evidence(
            "adaptive",
            post_escalation=route_observation("model-beta", "medium", LADDER_ROUTES[2]),
        )
        observed = self.module.evaluate_demonstration(
            self.record_for("adaptive", demonstration_evidence=evidence), self.registry
        )
        self.assertEqual(observed["demonstration_state"], "not_demonstrated")

    def test_matching_route_identifiers_alone_do_not_demonstrate_an_escalation(self) -> None:
        # FR-031a.3: the served model and effort must move with the route id.
        evidence = demonstration_evidence(
            "adaptive",
            post_escalation=route_observation("model-alpha", "low", LADDER_ROUTES[1]),
        )
        observed = self.module.evaluate_demonstration(
            self.record_for("adaptive", demonstration_evidence=evidence), self.registry
        )
        self.assertEqual(observed["demonstration_state"], "not_demonstrated")

    def test_the_unpinned_smoke_serves_the_pinned_parent_model_and_effort(self) -> None:
        # FR-031a.4: what the platform resolved, not what the arm requested.
        pin = control_of_kind(self.registry, "unpinned")["unpinned"]
        observed = self.evaluate("unpinned")
        self.assertEqual(observed["served"]["model"], pin["pinned_parent_model"])
        self.assertEqual(observed["served"]["effort"], pin["pinned_parent_effort"])

    def test_an_unpinned_smoke_serving_another_pin_is_not_demonstrated(self) -> None:
        evidence = demonstration_evidence(
            "unpinned", served_route=route_observation("model-beta", "low", LADDER_ROUTES[2])
        )
        observed = self.evaluate("unpinned", demonstration_evidence=evidence)
        self.assertEqual(observed["demonstration_state"], "not_demonstrated")

    def test_the_parallel_inequality_needs_two_non_parent_members(self) -> None:
        # FR-031a.5: at least two members besides the parent.
        objective = entry_of_eligibility(False)["objective_ids"][0]
        rows = parallel_unit(child_wall_times=(40000,))
        observed = self.evaluate(
            "orchestration_changing", objective_attempts=[smoke_attempt(objective, rows)]
        )
        self.assertEqual(observed["demonstration_state"], "not_demonstrated")

    def test_a_parent_wall_time_at_or_above_the_sum_is_not_demonstrated(self) -> None:
        objective = entry_of_eligibility(False)["objective_ids"][0]
        rows = parallel_unit(parent_wall_time_ms=80000)
        observed = self.evaluate(
            "orchestration_changing", objective_attempts=[smoke_attempt(objective, rows)]
        )
        self.assertEqual(observed["demonstration_state"], "not_demonstrated")

    def test_a_null_wall_time_anywhere_records_the_demonstration_as_not_made(self) -> None:
        # FR-031a.5: never satisfied by the members that did report, and never
        # with a missing value read as zero, which would invert the check.
        objective = entry_of_eligibility(False)["objective_ids"][0]
        for rows in (
            parallel_unit(parent_wall_time_ms=None),
            parallel_unit(child_wall_times=(40000, None)),
        ):
            with self.subTest(rows=[row["wall_time_ms"] for row in rows]):
                observed = self.evaluate(
                    "orchestration_changing",
                    objective_attempts=[smoke_attempt(objective, rows)],
                )
                self.assertEqual(observed["demonstration_state"], "not_demonstrated")

    def test_an_unset_subagent_override_gates_the_adaptive_and_unpinned_smokes(self) -> None:
        # FR-031a.6: the served model would otherwise be decided by the override
        # rather than by the declared parameter or the parent session.
        for kind in ("unpinned", "adaptive"):
            with self.subTest(control_kind=kind):
                observed = self.evaluate(kind, claude_code_subagent_model_unset=False)
                self.assertEqual(observed["demonstration_state"], "not_demonstrated")

    def test_the_override_observation_does_not_gate_the_orchestration_smoke(self) -> None:
        # It gates rules 3 and 4 specifically; the parallel observable does not
        # turn on which model was served.
        observed = self.evaluate(
            "orchestration_changing", claude_code_subagent_model_unset=False
        )
        self.assertEqual(observed["demonstration_state"], "demonstrated")

    def test_an_unevidenced_demonstration_is_never_relabeled(self) -> None:
        # FR-031a.7: the remedy is re-running the smoke, never relabeling.
        evidence = demonstration_evidence("adaptive", read_back_from="dispatch_request")
        observed = self.module.evaluate_demonstration(
            self.record_for(
                "adaptive", demonstration_evidence=evidence, demonstration_state="demonstrated"
            ),
            self.registry,
        )
        self.assertEqual(observed["demonstration_state"], "not_demonstrated")
        self.assertIs(observed["relabel_refused"], True)

    def test_the_demonstration_state_is_a_closed_member_this_spec_owns(self) -> None:
        # FR-031a.7: never a score-plane failure code, because a non-scored smoke
        # row produces no score bundle for such a code to sit on.
        self.assertEqual(
            sorted(self.module.DEMONSTRATION_STATES), ["demonstrated", "not_demonstrated"]
        )
        self.assertFalse(set(self.module.DEMONSTRATION_STATES) & set(frozen_failure_codes()))


class CacheIsolationTests(unittest.TestCase):
    """FR-032 and FR-032a: pairwise across the whole series, or not evidence."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.registry = synthetic_registry()
        self.arms = [str(control["control_id"]) for control in self.registry["controls"]]

    def test_the_status_set_is_read_from_the_frozen_cache_diagnostic(self) -> None:
        # FR-032a.1: no new field, status, or code is coined.
        self.assertEqual(
            sorted(self.module.ISOLATION_STATUSES), sorted(frozen_isolation_statuses())
        )

    def test_all_three_unordered_arm_pairs_are_recorded_disjoint(self) -> None:
        observed = self.module.evaluate_cache_isolation(isolation_series(self.registry))
        self.assertEqual(len(observed["pairs"]), 3)
        self.assertIs(observed["all_pairs_disjoint"], True)
        self.assertEqual(observed["invalidated_arms"], [])

    def test_a_disjoint_pair_carries_both_root_digests(self) -> None:
        for pair in self.module.evaluate_cache_isolation(isolation_series(self.registry))["pairs"]:
            with self.subTest(pair=pair["pair"]):
                self.assertRegex(pair["arm_cache_root_digest"], r"^sha256:[0-9a-f]{64}$")
                self.assertRegex(pair["paired_arm_cache_root_digest"], r"^sha256:[0-9a-f]{64}$")

    def test_a_disjoint_claim_missing_a_root_digest_fails_closed(self) -> None:
        series = isolation_series(self.registry)
        series[0]["observed_cache_isolation"][0]["arm_cache_root_digest"] = None
        with self.assertRaises(self.error):
            self.module.evaluate_cache_isolation(series)

    def test_a_root_recorded_as_a_filesystem_path_fails_closed(self) -> None:
        # FR-032a.6: a cache root is a digest, never a path, which also keeps the
        # untracked-output discipline from being undone by a leaked path.
        series = isolation_series(self.registry)
        series[0]["observed_cache_isolation"][0]["arm_cache_root_digest"] = "/tmp/arm-cache"
        with self.assertRaises(self.error):
            self.module.evaluate_cache_isolation(series)

    def test_the_precommitment_is_not_offered_as_the_observation(self) -> None:
        # FR-032a.2: per_arm_ephemeral_root is a precommitment, not evidence.
        series = isolation_series(self.registry)
        series[0]["observed_cache_isolation"][0]["per_arm_ephemeral_root"] = True
        with self.assertRaises(self.error):
            self.module.evaluate_cache_isolation(series)

    def test_a_series_missing_a_pair_fails_closed(self) -> None:
        # FR-032a.4: consecutive pairs alone leave the first-to-last unchecked.
        series = isolation_series(self.registry)
        series[0]["observed_cache_isolation"] = series[0]["observed_cache_isolation"][:1]
        series[2]["observed_cache_isolation"] = [
            pair for pair in series[2]["observed_cache_isolation"]
            if pair["paired_arm_id"] != self.arms[0]
        ]
        with self.assertRaises(self.error):
            self.module.evaluate_cache_isolation(series)

    def test_a_shared_pair_carries_the_frozen_infrastructure_code(self) -> None:
        series = isolation_series(self.registry, **{
            f"{self.arms[0]}|{self.arms[1]}": "observed_shared",
            f"{self.arms[1]}|{self.arms[0]}": "observed_shared",
        })
        observed = self.module.evaluate_cache_isolation(series)
        breached = [pair for pair in observed["pairs"] if pair["status"] == "observed_shared"]
        self.assertEqual(len(breached), 1)
        self.assertEqual(breached[0]["failure_code"], "infrastructure_failure")
        self.assertEqual(breached[0]["failure_plane"], "infrastructure")
        self.assertIs(observed["all_pairs_disjoint"], False)
        self.assertEqual(observed["invalidated_arms"], sorted(self.arms[:2]))

    def test_an_unobserved_pair_carries_the_frozen_evidence_boundary_code(self) -> None:
        series = isolation_series(self.registry, **{
            f"{self.arms[1]}|{self.arms[2]}": "unobserved",
            f"{self.arms[2]}|{self.arms[1]}": "unobserved",
        })
        observed = self.module.evaluate_cache_isolation(series)
        missing = [pair for pair in observed["pairs"] if pair["status"] == "unobserved"]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["failure_code"], "required_evidence_missing")
        self.assertEqual(missing[0]["failure_plane"], "evidence_boundary")
        self.assertEqual(observed["invalidated_arms"], sorted(self.arms[1:]))

    def test_both_frozen_codes_are_members_of_the_frozen_code_enum(self) -> None:
        codes = frozen_failure_codes()
        for code in ("infrastructure_failure", "required_evidence_missing"):
            with self.subTest(failure_code=code):
                self.assertIn(code, codes)


# --------------------------------------------------------------------------- #
# Operator smoke driver: plan-time and seal-time enforcement                     #
# (FR-026a, FR-030, FR-030c, FR-033, SC-007)                                     #
# --------------------------------------------------------------------------- #

SMOKE_DRIVER_PATH = TEST_ROOT / "layer6-efficiency" / "run-control-smoke.py"
LAYER6_GITIGNORE_PATH = TEST_ROOT / "layer6-efficiency" / ".gitignore"


def load_smoke_driver():
    """Import the operator driver by path: its filename is not a module name.

    The driver is live and operator-only, so it is deliberately absent from
    ``suite-manifest.json``. Its deterministic seams are covered from here, the
    same arrangement ``run-calibration-pilot.py`` already uses.
    """
    spec = importlib.util.spec_from_file_location("control_smoke_driver", SMOKE_DRIVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["control_smoke_driver"] = module
    spec.loader.exec_module(module)
    return module


try:  # CAR-004 deliverable — absent until the smoke driver lands.
    smoke_driver = load_smoke_driver()
except (FileNotFoundError, AttributeError):  # pragma: no cover - pre-implementation only
    smoke_driver = None


class SmokeDriverPlanTests(unittest.TestCase):
    """FR-026a.1: a reserved objective never reaches an operator."""

    def setUp(self) -> None:
        self.assertIsNotNone(smoke_driver, "run-control-smoke.py is not importable")
        self.driver = smoke_driver
        self.entries = partition_entries()
        self.smoke = entry_of_eligibility(False)
        self.reserved = entry_of_eligibility(True)

    def test_the_plan_derives_its_objectives_from_the_registered_smoke_partition(self) -> None:
        self.assertEqual(
            list(self.driver.plan_objectives(self.entries)), sorted(self.smoke["objective_ids"])
        )

    def test_the_plan_emits_only_what_the_frozen_consumption_path_admits(self) -> None:
        # The objective list is the frozen path's own answer, not a CAR-004
        # restatement of it.
        from claude_experiment_policy import consumable_objectives

        self.assertEqual(
            tuple(self.driver.plan_objectives(self.entries)),
            consumable_objectives(self.entries),
        )

    def test_no_planned_objective_touches_the_reservation(self) -> None:
        planned = set(self.driver.plan_objectives(self.entries))
        self.assertTrue(planned)
        self.assertFalse(planned & set(self.reserved["objective_ids"]))

    def test_a_qualification_eligible_smoke_partition_leaves_nothing_to_plan(self) -> None:
        seeded = copy.deepcopy(self.entries)
        for entry in seeded:
            if entry["partition_id"] == self.smoke["partition_id"]:
                entry["qualification_eligible"] = True
        with self.assertRaises(claude_policy_controls.ControlContractError):
            self.driver.plan_objectives(seeded)

    def test_a_reserved_objective_leaking_into_the_smoke_set_is_refused(self) -> None:
        seeded = copy.deepcopy(self.entries)
        for entry in seeded:
            if entry["partition_id"] == self.smoke["partition_id"]:
                entry["objective_ids"] = sorted(
                    entry["objective_ids"] + [self.reserved["objective_ids"][0]]
                )
        with self.assertRaises(claude_policy_controls.ControlContractError):
            self.driver.plan_objectives(seeded)

    def test_the_printed_plan_names_one_control_and_its_objectives(self) -> None:
        for flag, kind in self.driver.CONTROL_CHOICES.items():
            with self.subTest(control=flag):
                text = self.driver.render_plan(self.driver.build_plan(kind))
                self.assertIn(kind, text)
                for objective in self.driver.plan_objectives(self.entries):
                    self.assertIn(objective, text)
                for objective in self.reserved["objective_ids"]:
                    self.assertNotIn(objective, text)


class SmokeDriverSealTests(unittest.TestCase):
    """FR-026a.2, FR-030c.3, FR-033: refuse, record the refusal, commit nothing."""

    def setUp(self) -> None:
        self.assertIsNotNone(smoke_driver, "run-control-smoke.py is not importable")
        self.driver = smoke_driver
        self.registry = claude_policy_controls.load_registry()
        self.control = control_of_kind(self.registry, "adaptive")
        self.reserved = entry_of_eligibility(True)

    def seal(self, **overrides: object) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            outcome = self.driver.seal_record(
                smoke_record(self.control, **overrides), results_dir=Path(directory)
            )
            outcome["written"] = json.loads(Path(outcome["path"]).read_text(encoding="utf-8"))
            return outcome

    def test_a_conforming_record_is_sealed(self) -> None:
        outcome = self.seal()
        self.assertIs(outcome["admitted"], True)
        self.assertEqual(outcome["refusal_reasons"], [])

    def test_an_observed_api_key_is_refused_and_still_written(self) -> None:
        outcome = self.seal(authentication_mode="api_key")
        self.assertIs(outcome["admitted"], False)
        self.assertEqual(outcome["written"]["authentication_mode"], "api_key")
        self.assertIn(
            claude_policy_controls.API_KEY_REFUSAL_REASON, outcome["written"]["refusal_reasons"]
        )

    def test_a_scored_record_is_refused(self) -> None:
        outcome = self.seal(scored=True)
        self.assertIs(outcome["admitted"], False)
        self.assertTrue(outcome["written"]["refusal_reasons"])

    def test_a_record_touching_the_reservation_is_refused(self) -> None:
        objective = self.reserved["objective_ids"][0]
        outcome = self.seal(objective_ids=[objective], objective_attempts=[smoke_attempt(objective)])
        self.assertIs(outcome["admitted"], False)

    def test_a_record_breaching_a_frozen_bound_is_refused(self) -> None:
        outcome = self.seal(elapsed_wall_clock_seconds=1801)
        self.assertIs(outcome["admitted"], False)

    def test_a_refused_record_stays_distinguishable_from_one_that_never_ran(self) -> None:
        outcome = self.seal(authentication_mode="api_key")
        self.assertEqual(outcome["written"]["evidence_admissibility"], "refused")
        self.assertEqual(outcome["written"]["control_id"], self.control["control_id"])

    def test_sealed_records_are_written_under_the_git_ignored_results_directory(self) -> None:
        # FR-033: per-run smoke output stays out of version control. The default
        # destination is the directory the committed layer6 .gitignore excludes.
        self.assertEqual(
            self.driver.RESULTS_DIR, TEST_ROOT / "layer6-efficiency" / "results"
        )
        ignored = LAYER6_GITIGNORE_PATH.read_text(encoding="utf-8").splitlines()
        self.assertIn("results/*", ignored)
        default = inspect.signature(self.driver.seal_record).parameters["results_dir"].default
        self.assertEqual(default, self.driver.RESULTS_DIR)

    def test_a_sealed_record_lands_in_the_results_directory_it_was_given(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outcome = self.driver.seal_record(
                smoke_record(self.control), results_dir=Path(directory)
            )
            self.assertEqual(outcome["path"].parent, Path(directory))

    def test_the_driver_is_not_registered_in_the_suite_manifest(self) -> None:
        # Live and operator-only, so it never runs in the default suite; its
        # deterministic seams are covered from this module instead.
        manifest = load_json(TEST_ROOT / "suite-manifest.json")
        registered = json.dumps(manifest)
        self.assertNotIn(SMOKE_DRIVER_PATH.name, registered)


class SchemaEngineKeywordCoverageTests(unittest.TestCase):
    """An unenforceable keyword is refused, and the enforceable ones are enforced.

    The engine is shared by every contract in ``contracts-claude/``, several of
    which use keywords CAR-004's own two documents do not. A keyword the engine
    quietly skips is indistinguishable from one the instance satisfied, so both
    halves are pinned here: the corpus stays inside the supported set, and each
    keyword the corpus uses actually rejects something.
    """

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError

    def accepts(self, instance: object, schema: dict[str, object]) -> bool:
        try:
            self.module.validate_instance(instance, schema)
        except self.error:
            return False
        return True

    def test_every_keyword_the_committed_corpus_uses_is_supported(self) -> None:
        supported = self.module.SUPPORTED_KEYWORDS
        unknown: list[tuple[str, list[str]]] = []

        def walk(node: object, document: str) -> None:
            if not isinstance(node, dict):
                return
            extra = sorted(set(node) - supported)
            if extra:
                unknown.append((document, extra))
            for keyword, value in node.items():
                if keyword in ("properties", "$defs") and isinstance(value, dict):
                    for child in value.values():
                        walk(child, document)
                elif keyword in ("items", "not", "if", "then", "else", "propertyNames"):
                    walk(value, document)
                elif keyword == "additionalProperties" and isinstance(value, dict):
                    walk(value, document)
                elif keyword in ("allOf", "anyOf", "oneOf") and isinstance(value, list):
                    for child in value:
                        walk(child, document)

        for path in sorted(CONTRACT_ROOT.glob("*.schema.json")):
            walk(load_json(path), path.name)
        self.assertEqual(unknown, [], "a committed contract uses a keyword the engine skips")

    def test_a_keyword_the_engine_cannot_enforce_is_refused(self) -> None:
        # Refusing beats ignoring: teaching the engine is the prerequisite for
        # using a keyword, not a follow-up to discovering it did nothing.
        with self.assertRaises(self.error):
            self.module.validate_instance(5, {"type": "integer", "multipleOf": 2})

    def test_additional_properties_as_a_schema_constrains_the_unnamed_members(self) -> None:
        schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": {"type": "integer", "minimum": 0},
        }
        self.assertTrue(self.accepts({"a": 1}, schema))
        self.assertFalse(self.accepts({"a": -1}, schema))
        self.assertFalse(self.accepts({"a": "one"}, schema))

    def test_exclusive_maximum_bounds_the_open_upper_end(self) -> None:
        schema = {"type": "number", "exclusiveMaximum": 2}
        self.assertTrue(self.accepts(1.999, schema))
        self.assertFalse(self.accepts(2, schema))

    def test_one_of_admits_exactly_one_branch(self) -> None:
        schema = {"oneOf": [{"type": "integer"}, {"type": "string"}]}
        self.assertTrue(self.accepts(1, schema))
        self.assertTrue(self.accepts("x", schema))
        self.assertFalse(self.accepts(1.5, schema))
        self.assertFalse(self.accepts(True, schema))

    def test_property_names_constrains_the_keys(self) -> None:
        schema = {"type": "object", "propertyNames": {"pattern": "^[a-z]+$"}}
        self.assertTrue(self.accepts({"ab": 1}, schema))
        self.assertFalse(self.accepts({"A1": 1}, schema))

    def test_the_string_and_object_maxima_bound_their_own_types(self) -> None:
        self.assertFalse(self.accepts("abcd", {"type": "string", "maxLength": 3}))
        self.assertFalse(
            self.accepts({"a": 1, "b": 2}, {"type": "object", "maxProperties": 1})
        )


class BindingDriftOnProductionPathsTests(unittest.TestCase):
    """FR-005a and SC-018: the byte-drift guard runs where consumers actually go.

    A guard reachable only from a unit test guards the unit test. Every loader a
    consumer touches is exercised here against a seeded byte change in a bound
    CAR-003 document, and each one must fail closed.
    """

    BOUND = "score-bundle.schema.json"

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.path = CONTRACT_ROOT / self.BOUND
        self.original = self.path.read_bytes()
        self.addCleanup(self.path.write_bytes, self.original)

    def seed_byte_drift(self) -> None:
        # A trailing newline: the parsed value is identical, only the bytes move.
        self.path.write_bytes(self.original + b"\n")

    def test_load_registry_recomputes_the_bound_digests(self) -> None:
        self.assertTrue(self.module.load_registry())
        self.seed_byte_drift()
        with self.assertRaises(self.module.ControlContractError):
            self.module.load_registry()

    def test_replay_recomputes_the_bound_digests(self) -> None:
        self.seed_byte_drift()
        with self.assertRaises(self.module.ControlContractError):
            self.module.replay()

    def test_the_operator_plan_recomputes_the_bound_digests(self) -> None:
        self.assertIsNotNone(smoke_driver, "run-control-smoke.py is not importable")
        self.seed_byte_drift()
        with self.assertRaises(self.module.ControlContractError):
            smoke_driver.build_plan("adaptive")


class SmokeRecordCacheIsolationReadingTests(unittest.TestCase):
    """FR-032: the required member is read, so the requirement is a requirement."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.registry = synthetic_registry()
        self.control = control_of_kind(self.registry, "unpinned")

    def read(self, pairs: object) -> dict[str, object]:
        return self.module.validate_smoke_record(
            smoke_record(self.control, observed_cache_isolation=pairs), self.registry
        )

    def test_a_disjoint_pair_is_admitted(self) -> None:
        reading = self.read([isolation_pair("other-arm")])
        self.assertEqual(reading["evidence_admissibility"], "admitted")
        self.assertTrue(reading["cache_isolation"]["all_pairs_disjoint"])

    def test_a_shared_pair_refuses_the_record_and_survives_on_it(self) -> None:
        reading = self.read([isolation_pair("other-arm", "observed_shared")])
        self.assertEqual(reading["evidence_admissibility"], "refused")
        self.assertIn(
            self.module.CACHE_ISOLATION_REFUSAL_REASON, reading["refusal_reasons"]
        )
        self.assertEqual(reading["cache_isolation"]["pairs_not_disjoint"], ["other-arm"])

    def test_an_unobserved_pair_refuses_the_record(self) -> None:
        reading = self.read([isolation_pair("other-arm", "unobserved")])
        self.assertEqual(reading["evidence_admissibility"], "refused")

    def test_an_empty_observation_list_discharges_nothing(self) -> None:
        with self.assertRaises(self.error):
            self.read([])

    def test_a_precommitment_is_not_an_observation_on_this_path_either(self) -> None:
        pair = isolation_pair("other-arm")
        pair[self.module.PRECOMMITMENT_MEMBER] = True
        with self.assertRaises(self.error):
            self.read([pair])

    def test_the_same_pair_may_not_be_recorded_twice(self) -> None:
        with self.assertRaises(self.error):
            self.read([isolation_pair("other-arm"), isolation_pair("other-arm")])


class ReaderTotalityTests(unittest.TestCase):
    """Fail-closed means this module's own error, never a bare builtin one.

    Callers route every entrypoint through ``except ControlContractError``. A
    reader raising ``KeyError`` or ``TypeError`` escapes that handler, so a
    malformed record surfaces as a traceback instead of a contract refusal.
    """

    def setUp(self) -> None:
        self.assertIsNotNone(claude_policy_controls, "claude_policy_controls is not importable")
        self.module = claude_policy_controls
        self.error = self.module.ControlContractError
        self.registry = synthetic_registry()

    def test_an_attempt_missing_a_counter_is_a_contract_error(self) -> None:
        control = control_of_kind(self.registry, "adaptive")
        scope = control["execution_contract"]["retry_bounds"]["counted_over"]
        with self.assertRaises(self.error):
            self.module.evaluate_bounds(
                control, {"counted_over": scope, "attempts": [{"duration_ms": 1}]}
            )

    def test_a_control_without_a_de_escalation_threshold_is_a_contract_error(self) -> None:
        control = copy.deepcopy(control_of_kind(self.registry, "adaptive"))
        del control["adaptive"]["de_escalation_clean_pass_threshold"]
        with self.assertRaises(self.error):
            self.module.validate_signal_maps(control)
        with self.assertRaises(self.error):
            self.module.advance_clean_streak(
                control,
                {"current_route_id": control["adaptive"]["escalation_ladder"][0]},
                objective(),
            )

    def test_a_non_count_confirmation_entry_is_a_contract_error(self) -> None:
        control = control_of_kind(self.registry, "unpinned")
        with self.assertRaises(self.error):
            self.module.validate_smoke_record(
                smoke_record(control, confirmation_entries=["one", "two"]), self.registry
            )

    def test_a_malformed_wall_time_yields_a_verdict_rather_than_raising(self) -> None:
        # FR-031a documents this reader as never raising. A value it cannot read
        # leaves the wall time unobserved, which is a verdict, not an exception.
        control = control_of_kind(self.registry, "orchestration_changing")
        objective = entry_of_eligibility(False)["objective_ids"][0]
        rows = [
            dict(smoke_unit_row("parent"), wall_time_ms="not-a-number"),
            smoke_unit_row("child-0", "parent"),
            smoke_unit_row("child-1", "parent"),
        ]
        observed = self.module.evaluate_demonstration(
            smoke_record(control, objective_attempts=[smoke_attempt(objective, rows)]),
            self.registry,
        )
        self.assertEqual(observed["demonstration_state"], "not_demonstrated")
        self.assertIn("wall_time_unobserved", observed["reasons"])

    def test_an_unrecorded_duration_leaves_the_additive_sum_unobserved(self) -> None:
        # FR-016e.5: never zero. A zero would read as a unit that finished fast.
        rows = [smoke_unit_row("parent"), smoke_unit_row("child-0", "parent")]
        self.assertEqual(
            self.module._smoke_aggregate(rows)["additive_duration_ms"],
            sum(int(row["duration_ms"]) for row in rows),
        )
        rows[1] = dict(rows[1])
        del rows[1]["duration_ms"]
        self.assertIsNone(self.module._smoke_aggregate(rows)["additive_duration_ms"])


class SmokeDriverRefusalDurabilityTests(unittest.TestCase):
    """FR-031a and FR-030c.3: the record survives, and a relabel does not stand."""

    def setUp(self) -> None:
        self.assertIsNotNone(smoke_driver, "run-control-smoke.py is not importable")
        self.driver = smoke_driver
        self.registry = claude_policy_controls.load_registry()
        self.control = control_of_kind(self.registry, "adaptive")

    def seal(self, record: dict[str, object]) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            outcome = self.driver.seal_record(
                record, results_dir=Path(directory), registry=self.registry
            )
            outcome["written"] = json.loads(Path(outcome["path"]).read_text(encoding="utf-8"))
            return outcome

    def test_a_relabelled_demonstration_is_refused(self) -> None:
        outcome = self.seal(
            smoke_record(
                self.control, demonstration_evidence={}, demonstration_state="demonstrated"
            )
        )
        self.assertIs(outcome["admitted"], False)
        self.assertIn(self.driver.RELABEL_REFUSAL_REASON, outcome["written"]["refusal_reasons"])
        self.assertEqual(
            outcome["written"]["demonstration"]["demonstration_state"], "not_demonstrated"
        )

    def test_the_command_line_exits_non_zero_on_a_relabelled_demonstration(self) -> None:
        # An operator script keys on the exit status; a relabel that exits 0
        # would read there as a clean pass.
        record = smoke_record(
            self.control, demonstration_evidence={}, demonstration_state="demonstrated"
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "record.json"
            source.write_text(json.dumps(record), encoding="utf-8")
            original = self.driver.RESULTS_DIR
            self.driver.RESULTS_DIR = Path(directory) / "results"
            self.addCleanup(setattr, self.driver, "RESULTS_DIR", original)
            with contextlib.redirect_stderr(io.StringIO()):
                status = self.driver.main(
                    ["--control", "adaptive", "--seal", str(source)]
                )
        self.assertNotEqual(status, 0)

    def test_an_unforeseen_reader_fault_still_writes_the_record(self) -> None:
        # The one outcome seal_record exists to prevent is losing the operator's
        # single copy of a live run, whatever the reader did.
        def explode(*_args: object, **_kwargs: object) -> None:
            raise RuntimeError("reader defect")

        original = claude_policy_controls.validate_smoke_record
        claude_policy_controls.validate_smoke_record = explode
        self.addCleanup(
            setattr, claude_policy_controls, "validate_smoke_record", original
        )
        outcome = self.seal(smoke_record(self.control))
        self.assertIs(outcome["admitted"], False)
        self.assertTrue(
            any(
                reason.startswith(self.driver.READER_FAULT_PREFIX)
                for reason in outcome["written"]["refusal_reasons"]
            )
        )
        self.assertEqual(outcome["written"]["control_id"], self.control["control_id"])

    def test_two_distinct_smoke_ids_never_write_the_same_file(self) -> None:
        # Sanitizing alone flattens both of these to the same stem.
        first = self.driver.record_filename({"smoke_id": "arm/one"})
        second = self.driver.record_filename({"smoke_id": "arm-one"})
        self.assertNotEqual(first, second)

    def test_no_smoke_can_produce_the_committed_baseline_filename(self) -> None:
        # results/consolidated-baseline.json is the one path the layer6
        # .gitignore re-includes, so a smoke overwriting it would replace
        # committed evidence.
        produced = self.driver.record_filename({"smoke_id": "consolidated-baseline"})
        self.assertNotEqual(produced, "consolidated-baseline.json")

    def test_a_record_without_a_smoke_id_is_not_sealable(self) -> None:
        with self.assertRaises(claude_policy_controls.ControlContractError):
            self.driver.record_filename({"control_id": "car-004-adaptive"})


TEST_CASES = (
    PolicyControlContractTests,
    RegistryDocumentShapeTests,
    SchemaEngineFailClosedTests,
    SchemaEngineKeywordCoverageTests,
    BindingDriftOnProductionPathsTests,
    SmokeRecordCacheIsolationReadingTests,
    ReaderTotalityTests,
    SmokeDriverRefusalDurabilityTests,
    RegistryIdentityAndClosureTests,
    Car003BindingTests,
    CodexRegistryFixtureTests,
    CodexUnpinnedControlTests,
    CodexAdaptiveLadderTests,
    CodexAdaptiveSignalResolutionTests,
    CodexAdaptiveMovementAndBreachTests,
    CodexJustifiedHighEffortControlTests,
    CodexParentPlusChildrenAggregationTests,
    CodexReservedPartitionArtifactTests,
    CodexReservedPartitionTests,
    CodexDeterministicReplayTests,
    CodexControlSmokePlanAndSealTests,
    CodexRawCaptureExclusionTests,
    UnpinnedControlTests,
    AdaptiveSignalMapTests,
    AdaptiveRowResolutionTests,
    EscalationLadderTests,
    CleanPassStreakTests,
    BoundScopeAndBreachTests,
    ServiceRerouteTests,
    AggregateFoldTests,
    UnitMembershipTests,
    RawTokenAndCacheAggregationTests,
    ReplayDeterminismTests,
    CommittedRegistryInstanceTests,
    ReservedPartitionRegistrationTests,
    ReservedPartitionGuardTests,
    SmokeRecordBoundTests,
    SmokeRecordEvidenceTests,
    DemonstrationStateTests,
    CacheIsolationTests,
    SmokeDriverPlanTests,
    SmokeDriverSealTests,
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-policy-control-contracts"))
