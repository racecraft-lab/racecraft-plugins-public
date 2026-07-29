#!/usr/bin/env python3
"""Control-comparison contract: eligibility floors, the Pareto dominance rule, and claim classes.

This module is the deterministic coverage for the frozen comparison rule the
successor spec will apply: the resource-vector projection over the eight Pareto
dimensions, the mandatory deterministic gates that floor a comparison to
``no_verdict``, the three-stage dominance evaluation with its materiality margin
map, and the total verdict-to-claim-class messaging map.

Contract-structural cases read the committed schema documents under
``tests/speckit-pro/layer6-efficiency/contracts-claude/``; module-contract cases
exercise ``tests/speckit-pro/layer6-efficiency/lib/claude_control_comparison.py``.

Nothing here concludes dominance. Every check is offline and makes zero live
model calls.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import sys
import tempfile
import unittest
from collections.abc import Iterator
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LIB_DIR = TEST_ROOT / "lib"
LAYER6_LIB_DIR = TEST_ROOT / "layer6-efficiency" / "lib"
for _path in (LIB_DIR, LAYER6_LIB_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from test_result import run_counted  # noqa: E402

# Frozen CAR-003 code, imported read-only: it publishes the one preimage rule the
# whole program digests under, so these cases seal a synthetic comparison against
# an oracle the module under test does not own (research D3).
from claude_successor_freeze import record_digest  # noqa: E402

try:  # CAR-004 deliverable — absent until the comparison module is implemented.
    import claude_control_comparison  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    claude_control_comparison = None  # type: ignore[assignment]

try:  # G56R-004 T021 deliverable — absent until the Codex comparison module lands.
    import codex_control_comparison  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only during the T020 RED state
    codex_control_comparison = None  # type: ignore[assignment]


CONTRACT_ROOT = TEST_ROOT / "layer6-efficiency" / "contracts-claude"
FIXTURE_ROOT = TEST_ROOT / "layer6-efficiency" / "fixtures-controls"
CODEX_CONTRACT_ROOT = TEST_ROOT / "layer6-efficiency" / "contracts-codex-specification"
CODEX_FIXTURE_ROOT = TEST_ROOT / "layer6-efficiency" / "fixtures-codex-controls"

COMPARISON_SCHEMA_PATH = CONTRACT_ROOT / "control-comparison.schema.json"
COMPARISON_SCHEMA_ID = "https://racecraft.dev/schemas/car-004/control-comparison.schema.json"
CODEX_COMPARISON_SCHEMA_PATH = CODEX_CONTRACT_ROOT / "control-comparison.schema.json"
CODEX_COMPARISON_INSTANCE_PATH = CODEX_FIXTURE_ROOT / "control-comparison.json"
CODEX_COMPARISON_SCHEMA_ID = (
    "https://racecraft.dev/schemas/g56r-004/control-comparison.schema.json"
)
CODEX_COMPARISON_ID = "g56r-004-control-comparison"
G56R_003_ANALYSIS_PLAN_ID = "https://racecraft.dev/schemas/g56r-003/analysis-plan.schema.json"
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

# FR-004 and SC-017: a reference that leaves the owning document is refused, so
# the only admissible prefix is the document's own local definition pointer.
LOCAL_REF_PREFIX = "#/$defs/"

# Keywords whose value is itself a schema, a list of schemas, or a mapping of
# names to schemas. Walking only these avoids mistaking a ``const`` payload or a
# property named after a keyword for a schema node.
_SCHEMA_MAP_KEYWORDS = ("properties", "$defs", "patternProperties")
_SCHEMA_KEYWORDS = ("items", "not", "if", "then", "else", "additionalProperties", "propertyNames", "contains")
_SCHEMA_LIST_KEYWORDS = ("allOf", "anyOf", "oneOf", "prefixItems")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_subschemas(schema: object) -> Iterator[dict[str, object]]:
    """Yield every schema node in a JSON Schema document, the root included."""
    stack: list[object] = [schema]
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        yield node
        for keyword in _SCHEMA_MAP_KEYWORDS:
            container = node.get(keyword)
            if isinstance(container, dict):
                stack.extend(container.values())
        for keyword in _SCHEMA_KEYWORDS:
            stack.append(node.get(keyword))
        for keyword in _SCHEMA_LIST_KEYWORDS:
            branch = node.get(keyword)
            if isinstance(branch, list):
                stack.extend(branch)


def open_object_nodes(schema: object) -> list[list[str]]:
    """Member lists of every object node that fails to close its member set."""
    return [
        sorted(node.get("properties", {}))
        for node in iter_subschemas(schema)
        if node.get("type") == "object" and node.get("additionalProperties") is not False
    ]


def declared_refs(schema: object) -> list[str]:
    return sorted({
        node["$ref"] for node in iter_subschemas(schema) if isinstance(node.get("$ref"), str)
    })


class ControlComparisonDominanceTests(unittest.TestCase):
    def test_validator_module_directory_is_on_the_import_path(self) -> None:
        self.assertTrue(LAYER6_LIB_DIR.is_dir())
        self.assertIn(str(LAYER6_LIB_DIR), sys.path)

    def test_schemas_and_frozen_instances_occupy_separate_roots(self) -> None:
        self.assertTrue(CONTRACT_ROOT.is_dir())
        self.assertNotEqual(CONTRACT_ROOT, FIXTURE_ROOT)
        self.assertEqual(CONTRACT_ROOT.parent, FIXTURE_ROOT.parent)


class ComparisonDocumentShapeTests(unittest.TestCase):
    """FR-004 and SC-017: the comparison document's own shape, before any instance."""

    def setUp(self) -> None:
        # Per-test rather than per-class so a missing or malformed document
        # surfaces as a counted failure on every case it breaks.
        self.schema = load_json(COMPARISON_SCHEMA_PATH)

    def test_the_comparison_document_loads_and_declares_its_own_identifier(self) -> None:
        self.assertEqual(self.schema["$schema"], JSON_SCHEMA_DIALECT)
        self.assertEqual(self.schema["$id"], COMPARISON_SCHEMA_ID)

    def test_the_comparison_document_freezes_its_schema_version_and_status(self) -> None:
        properties = self.schema["properties"]
        self.assertEqual(properties["schema_version"]["const"], "1.0.0")
        self.assertEqual(properties["status"]["const"], "frozen")

    def test_every_object_in_the_comparison_document_closes_its_member_set(self) -> None:
        self.assertEqual(open_object_nodes(self.schema), [])

    def test_the_comparison_document_resolves_every_reference_inside_its_own_defs(self) -> None:
        local_definitions = self.schema["$defs"]
        refs = declared_refs(self.schema)
        self.assertTrue(refs, "the document declares no $ref at all")
        for ref in refs:
            with self.subTest(ref=ref):
                self.assertTrue(ref.startswith(LOCAL_REF_PREFIX))
                self.assertIn(ref[len(LOCAL_REF_PREFIX):], local_definitions)

    def test_the_comparison_document_declares_every_successor_facing_block(self) -> None:
        self.assertEqual(
            sorted(self.schema["required"]),
            [
                "car_003_bindings",
                "comparison_digest",
                "comparison_id",
                "confidence_method",
                "dominance_rule",
                "eligibility_floors",
                "frozen_at",
                "messaging_map",
                "multiplicity_position",
                "reserved_partition_binding",
                "schema_version",
                "status",
            ],
        )
        properties = self.schema["properties"]
        for member, ref in (
            ("eligibility_floors", "#/$defs/eligibilityFloors"),
            ("dominance_rule", "#/$defs/dominanceRule"),
            ("confidence_method", "#/$defs/confidenceMethod"),
            ("multiplicity_position", "#/$defs/multiplicityPosition"),
            ("reserved_partition_binding", "#/$defs/binding"),
        ):
            with self.subTest(member=member):
                self.assertEqual(properties[member]["$ref"], ref)
        messaging_map = properties["messaging_map"]
        self.assertEqual(
            sorted(messaging_map["required"]),
            ["dominant", "inconclusive", "not_dominant"],
        )
        bindings = properties["car_003_bindings"]
        self.assertEqual(bindings["type"], "array")
        self.assertEqual(bindings["minItems"], 1)
        self.assertEqual(bindings["items"]["$ref"], "#/$defs/binding")


# --------------------------------------------------------------------------- #
# Frozen enumerations, read live from the committed CAR-003 contracts           #
#                                                                               #
# Never transcribed: a set-equality check only fails closed on an upstream       #
# membership change while both the subject and the validator read the same       #
# committed bytes.                                                              #
# --------------------------------------------------------------------------- #

SCORE_BUNDLE_SCHEMA_PATH = CONTRACT_ROOT / "score-bundle.schema.json"
ANALYSIS_PLAN_SCHEMA_PATH = CONTRACT_ROOT / "analysis-plan.schema.json"
ANALYSIS_PLAN_ID = "https://racecraft.dev/schemas/car-003/analysis-plan.schema.json"


def frozen_gates() -> list[str]:
    """The seven-member `deterministic_gates.gate` enum (FR-019)."""
    schema = load_json(SCORE_BUNDLE_SCHEMA_PATH)
    gates = schema["properties"]["deterministic_gates"]["items"]["properties"]["gate"]
    return list(gates["enum"])


def frozen_dimensions() -> list[str]:
    """The eight-member `pareto_policy.dimensions` enum (FR-020)."""
    schema = load_json(ANALYSIS_PLAN_SCHEMA_PATH)
    return list(schema["properties"]["pareto_policy"]["properties"]["dimensions"]["items"]["enum"])


def frozen_resource_vector_members() -> list[str]:
    """The frozen score-bundle `resource_vector` member names (FR-021e)."""
    schema = load_json(SCORE_BUNDLE_SCHEMA_PATH)
    return list(schema["properties"]["resource_vector"]["required"])


def frozen_multiplicity_families() -> list[str]:
    """The analysis plan's three frozen families, closed under FR-050."""
    schema = load_json(ANALYSIS_PLAN_SCHEMA_PATH)
    declaration = schema["properties"]["non_inferiority"]["properties"]["multiplicity_declaration"]
    return [member for member in declaration["required"] if member.endswith("_family")]


# --------------------------------------------------------------------------- #
# Synthetic comparison subject                                                  #
#                                                                               #
# Built in-test rather than read from the committed instance so these cases     #
# prove the rules independently of the fixture, which lands later. The committed #
# instance gets its own conformance case.                                       #
# --------------------------------------------------------------------------- #

FROZEN_AT = "2026-07-27T00:00:00Z"

# FR-021: the four ratio-scale cost quantities, the only dimensions that can
# supply material dominance.
MARGIN_ELIGIBLE_DIMENSIONS = ("input_tokens", "cached_input_tokens", "output_tokens", "duration")
RELATIVE_MARGIN = 0.10

MARGIN_UNITS = {
    "input_tokens": "tokens",
    "cached_input_tokens": "tokens",
    "output_tokens": "tokens",
    "duration": "milliseconds",
    "retries": "count",
    "compactions": "count",
    "acceptance": "ratio",
    "terminal_state": "categorical",
}
NO_WORSE_ONLY_DIRECTIONS = {
    "retries": "lower_is_better",
    "compactions": "lower_is_better",
    "acceptance": "higher_is_better",
    "terminal_state": "equal_only",
}


def synthetic_margin_map() -> dict[str, object]:
    """Total over all eight dimensions: four eligible at 0.10, four no-worse-only."""
    entries: dict[str, object] = {}
    for dimension in frozen_dimensions():
        if dimension in MARGIN_ELIGIBLE_DIMENSIONS:
            entries[dimension] = {
                "class": "margin_eligible",
                "relative_margin": RELATIVE_MARGIN,
                "unit": MARGIN_UNITS[dimension],
                "direction": "lower_is_better",
            }
        else:
            entries[dimension] = {
                "class": "no_worse_only",
                "unit": MARGIN_UNITS[dimension],
                "direction": NO_WORSE_ONLY_DIRECTIONS[dimension],
                "reason": (
                    f"{dimension} can defeat material dominance by being worse but can "
                    "never supply it"
                ),
            }
    return entries


def synthetic_messaging_map() -> dict[str, object]:
    return {
        "dominant": {
            "permitted_claim_class": "measured_improvement_over_previous_static_baseline",
            "forbidden_claim_classes": ["efficient", "optimal", "best_measured"],
            "messaging_restriction": True,
            "restriction_scope": "release_wording_only",
            "static_defaults_may_still_ship": True,
        },
        "not_dominant": {
            "permitted_claim_class": "no_comparative_claim",
            "forbidden_claim_classes": [],
            "messaging_restriction": False,
        },
        "inconclusive": {
            "permitted_claim_class": "no_comparative_claim",
            "forbidden_claim_classes": [],
            "messaging_restriction": False,
        },
    }


def synthetic_comparison() -> dict[str, object]:
    document: dict[str, object] = {
        "schema_version": "1.0.0",
        "comparison_id": "car-004-control-comparison",
        "status": "frozen",
        "frozen_at": FROZEN_AT,
        "eligibility_floors": {
            "required_gates": frozen_gates(),
            "all_gates_must_pass": True,
            "quality_floors_binding": {
                "id": ANALYSIS_PLAN_ID,
                "digest": "sha256:" + "1" * 64,
            },
            "reliability_guardrail_breach_result": "no_qualification",
            "availability_gate_required": True,
            "verdict_when_floor_unmet": "no_verdict",
            "claim_class_when_floor_unmet": "no_comparative_claim",
            "messaging_restriction_when_floor_unmet": False,
        },
        "dominance_rule": {
            "rule": "environment_independent_pareto",
            "weights_prohibited": True,
            "dimensions": frozen_dimensions(),
            "dimension_projection": {"duration_ms": "duration"},
            "evaluation_order": ["eligibility_floors", "pareto", "materiality_margin"],
            "margin_denominator": "comparator_value",
            "zero_denominator_result": "margin_not_computable",
            "margin_map": synthetic_margin_map(),
        },
        "confidence_method": {
            "method": "one_sided_lower_confidence_bound",
            "confidence_level": 0.95,
            "alpha": 0.05,
            "cluster_unit": "role",
            "cluster_adjustment": "cluster_robust_sandwich_variance_by_role",
            "replay_point_estimate_stand_in": True,
        },
        "multiplicity_position": {
            "family": "secondary_control_arm_family",
            "adjustment": "holm_bonferroni_within_the_secondary_control_arm_family",
            "family_wise_alpha": 0.05,
            "draws_alpha_from_primary": False,
            "disjoint_from_frozen_families": True,
            "rationale": (
                "CAR-011's three predeclared secondary control arms form one family, "
                "declared here rather than added to the frozen plan's closed three"
            ),
        },
        "reserved_partition_binding": {
            "id": "car-011-reserved-comparison-partition",
            "digest": "sha256:" + "2" * 64,
        },
        "messaging_map": synthetic_messaging_map(),
        # A real committed digest, not a placeholder: validate_comparison now
        # recomputes these against the bound document's bytes, so a stand-in
        # would only prove the guard fires on the fixture.
        "car_003_bindings": [
            {
                "id": ANALYSIS_PLAN_ID,
                "digest": file_bytes_digest(CONTRACT_ROOT / "analysis-plan.schema.json"),
            }
        ],
    }
    return reseal(document)


def reseal(document: dict[str, object]) -> dict[str, object]:
    """Re-stamp the address after a seeded edit, so a raise is attributable.

    Without this a seeded violation would also stale the recorded digest, and
    ``assertRaises`` could not tell the seeded rule from the stale address.
    """
    document.pop("comparison_digest", None)
    document["comparison_digest"] = record_digest(document, digest_field="comparison_digest")
    return document


def resource_vector(**overrides: object) -> dict[str, object]:
    """An unprojected frozen score-bundle resource vector, carrying `duration_ms`."""
    vector: dict[str, object] = {
        "input_tokens": 1000,
        "cached_input_tokens": 500,
        "output_tokens": 200,
        "duration_ms": 60000,
        "retries": 1,
        "compactions": 0,
        "acceptance": 0.9,
        "terminal_state": "completed",
    }
    vector.update(overrides)
    return vector


def eligible_arm(vector: dict[str, object] | None = None, **overrides: object) -> dict[str, object]:
    """An arm carrying its floor evidence and its unprojected resource vector."""
    arm: dict[str, object] = {
        "deterministic_gates": [{"gate": gate, "pass": True} for gate in frozen_gates()],
        "quality_floors_met": True,
        "reliability_guardrails_respected": True,
        "availability_gate_passed": True,
        "resource_vector": vector if vector is not None else resource_vector(),
    }
    arm.update(overrides)
    return arm


class ComparisonModuleTestCase(unittest.TestCase):
    """Shared setup: the module under test plus a sealed synthetic contract."""

    def setUp(self) -> None:
        self.assertIsNotNone(
            claude_control_comparison, "claude_control_comparison is not importable"
        )
        self.module = claude_control_comparison
        self.error = self.module.ControlComparisonError
        self.contract = synthetic_comparison()


class DimensionProjectionTests(ComparisonModuleTestCase):
    """FR-021e: one frozen rename, and no key outside the eight dimensions."""

    def test_the_synthetic_contract_is_accepted_before_any_seeded_violation(self) -> None:
        self.assertEqual(self.module.validate_comparison(self.contract), self.contract)

    def test_the_projection_carries_duration_ms_onto_the_frozen_dimension_name(self) -> None:
        projected = self.module.project_resource_vector(resource_vector())
        self.assertNotIn("duration_ms", projected)
        self.assertEqual(projected["duration"], 60000)
        self.assertEqual(sorted(projected), sorted(frozen_dimensions()))

    def test_the_other_seven_member_names_are_carried_across_unchanged(self) -> None:
        vector = resource_vector()
        projected = self.module.project_resource_vector(vector)
        for member in frozen_resource_vector_members():
            if member == "duration_ms":
                continue
            with self.subTest(member=member):
                self.assertEqual(projected[member], vector[member])

    def test_a_key_outside_the_eight_frozen_dimensions_is_refused(self) -> None:
        # FR-016e.2: the reasoning member is summed and reported, and adding it
        # here would make a frozen eight-dimension policy a nine-dimension one.
        with self.assertRaises(self.error):
            self.module.project_resource_vector(
                resource_vector(reasoning_output_tokens=42)
            )

    def test_a_vector_carrying_both_names_for_one_quantity_is_refused(self) -> None:
        with self.assertRaises(self.error):
            self.module.project_resource_vector(resource_vector(duration=59000))


class EligibilityFloorTests(ComparisonModuleTestCase):
    """FR-019 and FR-024a: stage one, and the no-verdict outcome it declares."""

    def floors(self) -> dict[str, object]:
        return self.contract["eligibility_floors"]  # type: ignore[return-value]

    def test_the_required_gates_are_set_equal_to_the_frozen_gate_enum(self) -> None:
        self.assertEqual(sorted(self.floors()["required_gates"]), sorted(frozen_gates()))
        self.module.validate_comparison(self.contract)

    def test_a_required_gate_set_that_drops_a_frozen_gate_is_refused(self) -> None:
        self.floors()["required_gates"] = [g for g in frozen_gates() if g != "acceptance"]
        with self.assertRaises(self.error):
            self.module.validate_comparison(reseal(self.contract))

    def test_a_required_gate_set_that_coins_a_gate_is_refused(self) -> None:
        self.floors()["required_gates"] = [*frozen_gates(), "operational_simplicity"]
        with self.assertRaises(self.error):
            self.module.validate_comparison(reseal(self.contract))

    def test_an_arm_that_cleared_every_floor_is_eligible(self) -> None:
        self.assertIs(
            self.module.check_eligibility_floors(eligible_arm(), self.contract), True
        )

    def test_a_failed_mandatory_gate_leaves_the_control_ineligible(self) -> None:
        for gate in frozen_gates():
            with self.subTest(gate=gate):
                arm = eligible_arm()
                for entry in arm["deterministic_gates"]:
                    if entry["gate"] == gate:
                        entry["pass"] = False
                self.assertIs(
                    self.module.check_eligibility_floors(arm, self.contract), False
                )

    def test_a_mandatory_gate_the_arm_never_recorded_leaves_it_ineligible(self) -> None:
        arm = eligible_arm()
        arm["deterministic_gates"] = [
            entry for entry in arm["deterministic_gates"] if entry["gate"] != "safety"
        ]
        self.assertIs(self.module.check_eligibility_floors(arm, self.contract), False)

    def test_an_unmet_quality_reliability_or_availability_floor_leaves_it_ineligible(self) -> None:
        for member in (
            "quality_floors_met",
            "reliability_guardrails_respected",
            "availability_gate_passed",
        ):
            with self.subTest(floor=member):
                self.assertIs(
                    self.module.check_eligibility_floors(
                        eligible_arm(**{member: False}), self.contract
                    ),
                    False,
                )
            with self.subTest(floor=member, evidence="absent"):
                arm = eligible_arm()
                del arm[member]
                self.assertIs(
                    self.module.check_eligibility_floors(arm, self.contract), False
                )

    def test_eligibility_is_decided_without_reading_the_resource_numbers(self) -> None:
        # FR-019: no floor cleared, no verdict, whatever the numbers say. The
        # strictly better vector below would win every dimension at stage two.
        unbeatable = resource_vector(
            input_tokens=1, cached_input_tokens=1, output_tokens=1,
            duration_ms=1, retries=0, compactions=0, acceptance=1.0,
        )
        arm = eligible_arm(unbeatable, quality_floors_met=False)
        self.assertIs(self.module.check_eligibility_floors(arm, self.contract), False)
        self.assertEqual(self.floors()["verdict_when_floor_unmet"], "no_verdict")

    def test_the_no_verdict_outcome_is_declared_inside_the_eligibility_block(self) -> None:
        # FR-024a and SC-019: beside the member that already records the
        # no-verdict result, never as a fourth verdict or a fourth map row.
        floors = self.floors()
        self.assertEqual(floors["claim_class_when_floor_unmet"], "no_comparative_claim")
        self.assertIs(floors["messaging_restriction_when_floor_unmet"], False)
        self.assertNotIn(floors["verdict_when_floor_unmet"], self.contract["messaging_map"])
        self.assertEqual(len(self.contract["messaging_map"]), 3)

    def test_a_fourth_messaging_map_row_for_the_no_verdict_outcome_is_refused(self) -> None:
        self.contract["messaging_map"]["no_verdict"] = {
            "permitted_claim_class": "no_comparative_claim",
            "forbidden_claim_classes": [],
            "messaging_restriction": False,
        }
        with self.assertRaises(self.error):
            self.module.validate_comparison(reseal(self.contract))


def projected_vector(**overrides: object) -> dict[str, object]:
    """A resource vector already carrying the frozen decision-vector names."""
    vector = resource_vector()
    vector["duration"] = vector.pop("duration_ms")
    vector.update(overrides)
    return vector


class MarginMapTests(ComparisonModuleTestCase):
    """FR-021 and SC-016: total over eight, four eligible, four no-worse-only."""

    def margin_map(self) -> dict[str, object]:
        return self.contract["dominance_rule"]["margin_map"]  # type: ignore[index]

    def test_the_margin_map_is_total_over_all_eight_frozen_dimensions(self) -> None:
        self.assertEqual(sorted(self.margin_map()), sorted(frozen_dimensions()))
        self.module.validate_comparison(self.contract)

    def test_exactly_four_dimensions_are_margin_eligible_at_the_frozen_margin(self) -> None:
        eligible = {
            name: entry
            for name, entry in self.margin_map().items()
            if entry["class"] == "margin_eligible"
        }
        self.assertEqual(sorted(eligible), sorted(MARGIN_ELIGIBLE_DIMENSIONS))
        for name, entry in eligible.items():
            with self.subTest(dimension=name):
                self.assertEqual(entry["relative_margin"], RELATIVE_MARGIN)

    def test_the_other_four_are_no_worse_only_and_each_records_its_reason(self) -> None:
        remaining = {
            name: entry
            for name, entry in self.margin_map().items()
            if entry["class"] == "no_worse_only"
        }
        self.assertEqual(
            sorted(remaining),
            sorted(d for d in frozen_dimensions() if d not in MARGIN_ELIGIBLE_DIMENSIONS),
        )
        for name, entry in remaining.items():
            with self.subTest(dimension=name):
                self.assertTrue(entry["reason"])
                self.assertNotIn("relative_margin", entry)

    def test_a_margin_map_that_omits_a_dimension_is_refused(self) -> None:
        del self.margin_map()["compactions"]
        with self.assertRaises(self.error):
            self.module.validate_comparison(reseal(self.contract))

    def test_promoting_a_no_worse_only_dimension_to_margin_eligible_is_refused(self) -> None:
        # FR-021b: a control that is cheaper because it gave up can never read as
        # materially dominant, which only holds while acceptance stays no-worse-only.
        self.margin_map()["acceptance"] = {
            "class": "margin_eligible",
            "relative_margin": RELATIVE_MARGIN,
            "unit": "ratio",
            "direction": "higher_is_better",
        }
        with self.assertRaises(self.error):
            self.module.validate_comparison(reseal(self.contract))


class ParetoStageTests(ComparisonModuleTestCase):
    """FR-020 and FR-021b: the frozen rule, with no weighted scalar ranking."""

    def verdict(self, candidate: dict[str, object], comparator: dict[str, object]) -> str:
        return self.module.pareto_verdict(candidate, comparator, self.contract)

    def test_an_unprojected_vector_raises_rather_than_comparing(self) -> None:
        # FR-021e: the stage reads projected names only, so an unprojected vector
        # never silently compares seven of eight dimensions.
        with self.assertRaises(self.error):
            self.verdict(resource_vector(), resource_vector())

    def test_a_candidate_better_on_one_dimension_and_equal_elsewhere_dominates(self) -> None:
        self.assertEqual(
            self.verdict(projected_vector(input_tokens=500), projected_vector()),
            "candidate_dominant",
        )

    def test_a_comparator_better_on_one_dimension_dominates_the_candidate(self) -> None:
        self.assertEqual(
            self.verdict(projected_vector(), projected_vector(input_tokens=500)),
            "comparator_dominant",
        )

    def test_two_identical_vectors_tie(self) -> None:
        self.assertEqual(self.verdict(projected_vector(), projected_vector()), "tied")

    def test_one_dimension_better_and_another_worse_is_mixed(self) -> None:
        self.assertEqual(
            self.verdict(projected_vector(input_tokens=500, retries=4), projected_vector()),
            "mixed",
        )

    def test_acceptance_is_higher_is_better_so_a_lower_value_is_worse(self) -> None:
        self.assertEqual(
            self.verdict(projected_vector(acceptance=0.5), projected_vector()),
            "comparator_dominant",
        )
        self.assertEqual(
            self.verdict(projected_vector(acceptance=1.0), projected_vector()),
            "candidate_dominant",
        )

    def test_a_differing_terminal_state_is_mixed_rather_than_ranked(self) -> None:
        # FR-021b: terminal state is categorical and unordered here. The FR-016a
        # severity rank is aggregation-only and must not be read at this stage,
        # so neither direction resolves in anybody's favour.
        for candidate_state, comparator_state in (("completed", "failed"), ("failed", "completed")):
            with self.subTest(candidate=candidate_state, comparator=comparator_state):
                self.assertEqual(
                    self.verdict(
                        projected_vector(input_tokens=500, terminal_state=candidate_state),
                        projected_vector(terminal_state=comparator_state),
                    ),
                    "mixed",
                )

    def test_a_null_acceptance_or_terminal_state_makes_the_comparison_uncertain(self) -> None:
        for dimension in ("acceptance", "terminal_state"):
            with self.subTest(dimension=dimension):
                self.assertEqual(
                    self.verdict(
                        projected_vector(input_tokens=500, **{dimension: None}),
                        projected_vector(),
                    ),
                    "mixed",
                )

    def test_an_incomplete_vector_is_never_resolved_in_anybody_s_favour(self) -> None:
        incomplete = projected_vector(input_tokens=500)
        del incomplete["compactions"]
        self.assertEqual(self.verdict(incomplete, projected_vector()), "mixed")

    def test_the_stage_accepts_no_weights(self) -> None:
        # FR-020: no weighted scalar ranking is imported or accepted, which is a
        # signature property rather than a promise in prose.
        for name in ("pareto_verdict", "materiality_filter", "compare"):
            with self.subTest(function=name):
                parameters = list(inspect.signature(getattr(self.module, name)).parameters)
                self.assertEqual(parameters, ["candidate", "comparator", "contract"])


class MaterialityMarginTests(ComparisonModuleTestCase):
    """FR-021c and FR-021d: the comparator denominator and the 0.10 lower bound."""

    def filter(self, candidate: dict[str, object], comparator: dict[str, object]) -> dict[str, str]:
        return self.module.materiality_filter(candidate, comparator, self.contract)

    def test_only_the_margin_eligible_dimensions_are_tested_for_materiality(self) -> None:
        result = self.filter(projected_vector(input_tokens=500), projected_vector())
        self.assertEqual(sorted(result), sorted(MARGIN_ELIGIBLE_DIMENSIONS))

    def test_a_component_reaching_the_frozen_margin_clears(self) -> None:
        result = self.filter(projected_vector(input_tokens=850), projected_vector())
        self.assertEqual(result["input_tokens"], "cleared")

    def test_a_component_short_of_the_frozen_margin_does_not_clear(self) -> None:
        result = self.filter(projected_vector(input_tokens=950), projected_vector())
        self.assertEqual(result["input_tokens"], "not_cleared")

    def test_the_denominator_is_the_comparator_value_and_not_the_candidate_s(self) -> None:
        # 1000 -> 905 is 9.5% of the comparator and 10.5% of the candidate; only
        # the comparator denominator keeps it short of the frozen margin.
        result = self.filter(projected_vector(input_tokens=905), projected_vector())
        self.assertEqual(result["input_tokens"], "not_cleared")

    def test_a_zero_comparator_component_is_not_computable_rather_than_infinite(self) -> None:
        result = self.filter(
            projected_vector(output_tokens=0), projected_vector(output_tokens=0)
        )
        self.assertEqual(result["output_tokens"], "margin_not_computable")

    def test_the_replay_point_estimate_stands_in_for_the_bound_on_a_single_row(self) -> None:
        # FR-021d: with no sampling distribution behind one synthetic row, the
        # stand-in is recorded rather than left implicit.
        self.assertIs(self.contract["confidence_method"]["replay_point_estimate_stand_in"], True)
        self.assertEqual(
            self.filter(projected_vector(duration=54000), projected_vector())["duration"],
            "cleared",
        )

    def test_a_contract_declaring_no_stand_in_refuses_to_invent_a_bound(self) -> None:
        self.contract["confidence_method"]["replay_point_estimate_stand_in"] = False
        with self.assertRaises(self.error):
            self.filter(projected_vector(input_tokens=500), projected_vector())


class ThreeStageOrderTests(ComparisonModuleTestCase):
    """FR-021a: floors, then Pareto, then materiality — and never out of order."""

    def compare(self, candidate: dict[str, object], comparator: dict[str, object]) -> dict:
        return self.module.compare(candidate, comparator, self.contract)

    def test_the_frozen_evaluation_order_is_the_one_the_stages_report(self) -> None:
        self.assertEqual(
            self.contract["dominance_rule"]["evaluation_order"],
            ["eligibility_floors", "pareto", "materiality_margin"],
        )

    def test_a_comparison_returns_a_verdict_its_components_and_the_stage_reached(self) -> None:
        outcome = self.compare(eligible_arm(), eligible_arm())
        self.assertEqual(sorted(outcome), ["per_component", "stage_reached", "verdict"])

    def test_an_ineligible_arm_stops_at_the_floors_whatever_its_numbers_say(self) -> None:
        unbeatable = resource_vector(
            input_tokens=1, cached_input_tokens=1, output_tokens=1,
            duration_ms=1, retries=0, compactions=0, acceptance=1.0,
        )
        outcome = self.compare(
            eligible_arm(unbeatable, availability_gate_passed=False), eligible_arm()
        )
        self.assertEqual(outcome["verdict"], "no_verdict")
        self.assertEqual(outcome["stage_reached"], "eligibility_floors")
        self.assertEqual(outcome["per_component"], {})

    def test_an_ineligible_comparator_stops_at_the_floors_as_well(self) -> None:
        outcome = self.compare(eligible_arm(), eligible_arm(quality_floors_met=False))
        self.assertEqual(outcome["verdict"], "no_verdict")
        self.assertEqual(outcome["stage_reached"], "eligibility_floors")

    def test_comparator_dominance_stops_at_the_pareto_stage(self) -> None:
        outcome = self.compare(
            eligible_arm(), eligible_arm(resource_vector(input_tokens=100))
        )
        self.assertEqual(outcome["verdict"], "not_dominant")
        self.assertEqual(outcome["stage_reached"], "pareto")
        self.assertEqual(outcome["per_component"], {})

    def test_a_mixed_comparison_is_inconclusive_and_never_reaches_the_margin(self) -> None:
        # FR-021a: the margin is a second-stage materiality filter, never a
        # replacement for the Pareto rule, so a 50% cheaper candidate that is
        # worse on one dimension still never reaches it.
        outcome = self.compare(
            eligible_arm(resource_vector(input_tokens=500, retries=4)), eligible_arm()
        )
        self.assertEqual(outcome["verdict"], "inconclusive")
        self.assertEqual(outcome["stage_reached"], "pareto")
        self.assertEqual(outcome["per_component"], {})

    def test_a_tied_comparison_is_inconclusive(self) -> None:
        outcome = self.compare(eligible_arm(), eligible_arm())
        self.assertEqual(outcome["verdict"], "inconclusive")
        self.assertEqual(outcome["stage_reached"], "pareto")

    def test_an_incomplete_or_uncertain_comparison_is_inconclusive(self) -> None:
        for label, vector in (
            ("uncertain", resource_vector(input_tokens=500, acceptance=None)),
            ("differing terminal state", resource_vector(input_tokens=500, terminal_state="failed")),
        ):
            with self.subTest(case=label):
                outcome = self.compare(eligible_arm(vector), eligible_arm())
                self.assertEqual(outcome["verdict"], "inconclusive")

    def test_candidate_dominance_with_a_material_component_is_dominant(self) -> None:
        outcome = self.compare(eligible_arm(resource_vector(input_tokens=800)), eligible_arm())
        self.assertEqual(outcome["verdict"], "dominant")
        self.assertEqual(outcome["stage_reached"], "materiality_margin")
        self.assertEqual(outcome["per_component"]["input_tokens"], "cleared")

    def test_candidate_dominance_with_no_material_component_is_not_dominant(self) -> None:
        # The evidence was sufficient; the materiality bar simply was not cleared.
        outcome = self.compare(eligible_arm(resource_vector(input_tokens=980)), eligible_arm())
        self.assertEqual(outcome["verdict"], "not_dominant")
        self.assertEqual(outcome["stage_reached"], "materiality_margin")
        self.assertEqual(outcome["per_component"]["input_tokens"], "not_cleared")

    def test_a_cheaper_control_that_gave_up_never_reads_as_materially_dominant(self) -> None:
        # FR-021b: a strictly higher acceptance is recorded and reported but can
        # never satisfy the margin trigger, so it alone yields not_dominant.
        outcome = self.compare(eligible_arm(resource_vector(acceptance=1.0)), eligible_arm())
        self.assertEqual(outcome["verdict"], "not_dominant")
        self.assertEqual(outcome["stage_reached"], "materiality_margin")
        self.assertNotIn("acceptance", outcome["per_component"])

    def test_a_comparison_whose_every_component_is_not_computable_is_not_dominant(self) -> None:
        # Every margin-eligible comparator value is zero, so the candidate wins
        # the Pareto stage on retries alone and no component can be computed.
        zeroed = {
            "input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "duration_ms": 0,
        }
        outcome = self.compare(
            eligible_arm(resource_vector(retries=0, **zeroed)),
            eligible_arm(resource_vector(**zeroed)),
        )
        self.assertEqual(outcome["verdict"], "not_dominant")
        self.assertEqual(
            sorted(set(outcome["per_component"].values())), ["margin_not_computable"]
        )


class MessagingMapTests(ComparisonModuleTestCase):
    """FR-022, FR-024, SC-008: one permitted class per verdict, and only one restricts."""

    def messaging_map(self) -> dict[str, object]:
        return self.contract["messaging_map"]  # type: ignore[return-value]

    def test_the_map_is_total_and_single_valued_over_the_three_verdict_states(self) -> None:
        self.assertEqual(sorted(self.messaging_map()), ["dominant", "inconclusive", "not_dominant"])
        for verdict in self.messaging_map():
            with self.subTest(verdict=verdict):
                looked_up = self.module.claim_class(verdict, self.contract)
                self.assertIsInstance(looked_up["permitted_claim_class"], str)

    def test_dominance_permits_measured_improvement_over_the_static_baseline(self) -> None:
        looked_up = self.module.claim_class("dominant", self.contract)
        self.assertEqual(
            looked_up["permitted_claim_class"],
            "measured_improvement_over_previous_static_baseline",
        )
        self.assertIs(looked_up["messaging_restriction"], True)

    def test_dominance_forbids_the_efficient_optimal_and_best_measured_classes(self) -> None:
        looked_up = self.module.claim_class("dominant", self.contract)
        self.assertEqual(
            sorted(looked_up["forbidden_claim_classes"]),
            ["best_measured", "efficient", "optimal"],
        )

    def test_the_dominant_restriction_reaches_release_wording_and_not_shipping(self) -> None:
        # FR-024: the static defaults may still ship for declared operational
        # simplicity, in the same sentence that removes the wording.
        looked_up = self.module.claim_class("dominant", self.contract)
        self.assertEqual(looked_up["restriction_scope"], "release_wording_only")
        self.assertIs(looked_up["static_defaults_may_still_ship"], True)

    def test_neither_non_dominant_verdict_imposes_a_messaging_restriction(self) -> None:
        for verdict in ("not_dominant", "inconclusive"):
            with self.subTest(verdict=verdict):
                looked_up = self.module.claim_class(verdict, self.contract)
                self.assertEqual(looked_up["permitted_claim_class"], "no_comparative_claim")
                self.assertIs(looked_up["messaging_restriction"], False)
                self.assertEqual(looked_up["forbidden_claim_classes"], [])
                self.assertNotIn("restriction_scope", looked_up)

    def test_a_non_dominant_entry_carrying_a_forbidden_set_is_refused(self) -> None:
        # A forbidden set IS a restriction, and FR-022 refuses to impose one.
        self.messaging_map()["inconclusive"]["forbidden_claim_classes"] = ["optimal"]
        with self.assertRaises(self.error):
            self.module.validate_comparison(reseal(self.contract))

    def test_a_dominant_entry_that_hides_the_shipping_permission_is_refused(self) -> None:
        del self.messaging_map()["dominant"]["static_defaults_may_still_ship"]
        with self.assertRaises(self.error):
            self.module.validate_comparison(reseal(self.contract))

    def test_moving_the_restriction_off_the_dominant_verdict_is_refused(self) -> None:
        self.messaging_map()["dominant"]["messaging_restriction"] = False
        with self.assertRaises(self.error):
            self.module.validate_comparison(reseal(self.contract))


class ClaimClassTotalityTests(ComparisonModuleTestCase):
    """FR-024a and SC-019: total over every reachable outcome, three verdicts still."""

    def test_the_eligibility_floor_outcome_resolves_to_exactly_one_wording_class(self) -> None:
        looked_up = self.module.claim_class("no_verdict", self.contract)
        self.assertEqual(looked_up["permitted_claim_class"], "no_comparative_claim")
        self.assertIs(looked_up["messaging_restriction"], False)
        self.assertEqual(looked_up["forbidden_claim_classes"], [])

    def test_the_no_verdict_class_is_read_from_the_eligibility_block(self) -> None:
        # Not from a fourth messaging-map row: moving the declared class inside
        # the block moves the lookup with it.
        self.contract["eligibility_floors"]["claim_class_when_floor_unmet"] = "no_comparative_claim"
        self.assertEqual(
            self.module.claim_class("no_verdict", self.contract)["permitted_claim_class"],
            self.contract["eligibility_floors"]["claim_class_when_floor_unmet"],
        )
        self.assertNotIn("no_verdict", self.contract["messaging_map"])

    def test_the_verdict_enum_still_carries_exactly_three_members(self) -> None:
        self.assertEqual(len(self.contract["messaging_map"]), 3)
        self.assertNotIn("no_verdict", self.contract["messaging_map"])

    def test_every_outcome_a_comparison_can_reach_resolves_to_one_class(self) -> None:
        reachable = {
            "ineligible": self.module.compare(
                eligible_arm(quality_floors_met=False), eligible_arm(), self.contract
            ),
            "comparator dominance": self.module.compare(
                eligible_arm(), eligible_arm(resource_vector(input_tokens=100)), self.contract
            ),
            "tied": self.module.compare(eligible_arm(), eligible_arm(), self.contract),
            "material dominance": self.module.compare(
                eligible_arm(resource_vector(input_tokens=800)), eligible_arm(), self.contract
            ),
            "immaterial dominance": self.module.compare(
                eligible_arm(resource_vector(input_tokens=980)), eligible_arm(), self.contract
            ),
        }
        for case, outcome in reachable.items():
            with self.subTest(case=case):
                looked_up = self.module.claim_class(outcome["verdict"], self.contract)
                self.assertIn(
                    looked_up["permitted_claim_class"],
                    ("measured_improvement_over_previous_static_baseline", "no_comparative_claim"),
                )
        self.assertEqual(
            sorted({outcome["verdict"] for outcome in reachable.values()}),
            ["dominant", "inconclusive", "no_verdict", "not_dominant"],
        )

    def test_an_outcome_the_procedure_cannot_reach_is_refused(self) -> None:
        for unreachable in ("efficient", "partial_dominance", ""):
            with self.subTest(outcome=unreachable):
                with self.assertRaises(self.error):
                    self.module.claim_class(unreachable, self.contract)


# --------------------------------------------------------------------------- #
# The committed comparison instance (SC-012, SC-017)                            #
# --------------------------------------------------------------------------- #

COMPARISON_INSTANCE_PATH = FIXTURE_ROOT / "control-comparison.json"
PARTITION_ENTRIES_PATH = FIXTURE_ROOT / "partition-registry-entries.json"


def file_bytes_digest(path: Path) -> str:
    """The SHA-256 of a document's committed bytes, not its record preimage."""
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class CommittedComparisonInstanceTests(unittest.TestCase):
    """Every rule above, run against the bytes the repository actually ships."""

    def setUp(self) -> None:
        self.assertIsNotNone(
            claude_control_comparison, "claude_control_comparison is not importable"
        )
        self.module = claude_control_comparison
        self.error = self.module.ControlComparisonError
        self.contract = self.module.load_comparison(COMPARISON_INSTANCE_PATH)

    def test_the_committed_instance_loads_through_the_schema_and_the_semantics(self) -> None:
        self.assertEqual(self.contract["schema_version"], "1.0.0")
        self.assertEqual(self.contract["status"], "frozen")
        self.assertEqual(
            sorted(self.contract["messaging_map"]),
            ["dominant", "inconclusive", "not_dominant"],
        )

    def test_the_recorded_address_recomputes_over_the_committed_bytes(self) -> None:
        self.assertEqual(
            self.contract["comparison_digest"],
            record_digest(self.contract, digest_field="comparison_digest"),
        )

    def test_every_recorded_binding_matches_the_bound_document_s_committed_bytes(self) -> None:
        for binding in self.contract["car_003_bindings"]:
            with self.subTest(binding=binding["id"]):
                name = binding["id"].rsplit("/", 1)[-1]
                self.assertEqual(binding["digest"], file_bytes_digest(CONTRACT_ROOT / name))
        floors = self.contract["eligibility_floors"]["quality_floors_binding"]
        self.assertEqual(floors["id"], ANALYSIS_PLAN_ID)
        self.assertEqual(floors["digest"], file_bytes_digest(ANALYSIS_PLAN_SCHEMA_PATH))

    def test_the_reserved_binding_pins_the_committed_membership_digest(self) -> None:
        # FR-025c: only the digest over the deduplicated, sorted objective ids
        # pins membership, so that is the digest the binding carries.
        entries = load_json(PARTITION_ENTRIES_PATH)["entries"]
        reserved = next(entry for entry in entries if entry["qualification_eligible"])
        self.assertEqual(
            self.contract["reserved_partition_binding"],
            {"id": reserved["partition_id"], "digest": reserved["objective_set_digest"]},
        )
        self.assertEqual(reserved["partition_type"], "integrated_confirmation")
        self.assertEqual(reserved["owning_spec"], "CAR-004")

    def test_the_committed_margin_map_declares_the_frozen_relative_margin(self) -> None:
        margin_map = self.contract["dominance_rule"]["margin_map"]
        eligible = {
            dimension: entry["relative_margin"]
            for dimension, entry in margin_map.items()
            if entry["class"] == "margin_eligible"
        }
        self.assertEqual(sorted(eligible), sorted(MARGIN_ELIGIBLE_DIMENSIONS))
        self.assertEqual(set(eligible.values()), {RELATIVE_MARGIN})

    def test_a_seeded_byte_change_in_the_committed_instance_fails_closed(self) -> None:
        tampered = load_json(COMPARISON_INSTANCE_PATH)
        tampered["comparison_id"] = "car-004-control-comparison-tampered"
        with tempfile.TemporaryDirectory() as directory:
            seeded = Path(directory) / "control-comparison.json"
            seeded.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaises(self.error):
                self.module.load_comparison(seeded)


class MarginBoundaryExactnessTests(ComparisonModuleTestCase):
    """FR-021: the declared margin is a decimal, and the boundary is exact.

    ``json.load`` turns the literal ``0.1`` into the nearest binary float, and a
    candidate sitting exactly on the declared margin then clears or misses it
    depending on the scale its inputs happen to be recorded in. A rule whose
    premise is byte-deterministic reproducibility cannot behave that way.
    """

    def filter_at(self, comparator: float, candidate: float) -> str:
        base = projected_vector()
        comparator_vector = dict(base)
        candidate_vector = dict(base)
        for dimension in MARGIN_ELIGIBLE_DIMENSIONS:
            comparator_vector[dimension] = comparator
            candidate_vector[dimension] = comparator
        candidate_vector["duration"] = candidate
        return self.module.materiality_filter(
            candidate_vector, comparator_vector, self.contract
        )["duration"]

    def test_a_candidate_exactly_on_the_margin_clears_it(self) -> None:
        # (0.3 - 0.27) / 0.3 is a tenth. In binary it is 0.09999999999999991.
        self.assertEqual(self.filter_at(0.3, 0.27), "cleared")

    def test_the_boundary_does_not_move_with_the_scale_of_its_inputs(self) -> None:
        for comparator, candidate in ((0.3, 0.27), (3.0, 2.7), (30.0, 27.0), (1.0, 0.9)):
            with self.subTest(comparator=comparator):
                self.assertEqual(self.filter_at(comparator, candidate), "cleared")

    def test_a_candidate_just_inside_the_margin_does_not_clear_it(self) -> None:
        self.assertEqual(self.filter_at(0.3, 0.2701), "not_cleared")

    def test_a_non_finite_resource_value_is_not_a_number(self) -> None:
        # An infinity would otherwise divide into a improvement of one.
        self.assertEqual(self.filter_at(float("inf"), 1.0), "margin_not_computable")


class FloorReadStrictnessTests(ComparisonModuleTestCase):
    """FR-019: a mandatory gate cannot be retired by deleting the member that names it."""

    def test_the_availability_gate_switch_is_frozen_at_true(self) -> None:
        del self.contract["eligibility_floors"]["availability_gate_required"]
        with self.assertRaises(self.error):
            self.module.validate_comparison(reseal(self.contract))

    def test_an_arm_failing_availability_is_ineligible_however_the_contract_reads(self) -> None:
        arm = eligible_arm(availability_gate_passed=False)
        self.assertFalse(self.module.check_eligibility_floors(arm, self.contract))
        # And deleting the switch refuses the contract rather than clearing the arm.
        del self.contract["eligibility_floors"]["availability_gate_required"]
        with self.assertRaises(self.error):
            self.module.check_eligibility_floors(arm, self.contract)

    def test_both_arms_are_read_even_when_the_candidate_already_fails(self) -> None:
        # Short-circuiting would return a well-formed no-verdict from a
        # comparison in which the comparator was never inspected at all.
        candidate = eligible_arm(quality_floors_met=False)
        with self.assertRaises(self.error):
            self.module.compare(candidate, "not-an-arm-at-all", self.contract)


class CodexComparisonArtifactPresenceTests(unittest.TestCase):
    """T020 RED: the G56R-004 comparison contract, fixture, and helper must exist."""

    def test_the_codex_comparison_schema_is_published_under_the_g56r_004_id(self) -> None:
        self.assertTrue(
            CODEX_COMPARISON_SCHEMA_PATH.is_file(),
            f"{CODEX_COMPARISON_SCHEMA_PATH} is missing; T021 must publish it",
        )
        schema = load_json(CODEX_COMPARISON_SCHEMA_PATH)
        self.assertEqual(schema["$schema"], JSON_SCHEMA_DIALECT)
        self.assertEqual(schema["$id"], CODEX_COMPARISON_SCHEMA_ID)

    def test_the_codex_comparison_fixture_is_published_under_the_g56r_004_id(self) -> None:
        self.assertTrue(
            CODEX_COMPARISON_INSTANCE_PATH.is_file(),
            f"{CODEX_COMPARISON_INSTANCE_PATH} is missing; T021 must publish it",
        )
        fixture = load_json(CODEX_COMPARISON_INSTANCE_PATH)
        self.assertEqual(fixture["comparison_id"], CODEX_COMPARISON_ID)
        self.assertEqual(fixture["schema_version"], "1.0.0")
        self.assertEqual(fixture["status"], "frozen")

    def test_the_codex_comparison_helper_module_is_importable(self) -> None:
        self.assertIsNotNone(
            codex_control_comparison,
            "codex_control_comparison is not importable; T021 must implement it",
        )


class CodexComparisonModuleTestCase(unittest.TestCase):
    """Shared G56R-004 setup for the Codex-local comparison rule."""

    def setUp(self) -> None:
        self.assertIsNotNone(
            codex_control_comparison,
            "codex_control_comparison is not importable; T021 must implement it",
        )
        self.module = codex_control_comparison
        self.error = self.module.ControlComparisonError
        self.contract = self.module.load_comparison(CODEX_COMPARISON_INSTANCE_PATH)

    def compare(self, candidate: dict[str, object], comparator: dict[str, object]) -> dict:
        return self.module.compare(candidate, comparator, self.contract)


class CodexComparisonContractTests(CodexComparisonModuleTestCase):
    """T020 RED: G56R-004 freezes the CAR-004 comparison behavior locally."""

    def test_the_codex_fixture_loads_and_recomputes_its_content_address(self) -> None:
        self.assertEqual(self.contract["comparison_id"], CODEX_COMPARISON_ID)
        self.assertEqual(self.contract["schema_version"], "1.0.0")
        self.assertEqual(self.contract["status"], "frozen")
        self.assertEqual(
            self.contract["comparison_digest"],
            record_digest(self.contract, digest_field="comparison_digest"),
        )

    def test_eligibility_floors_gate_every_verdict_before_resources_are_read(self) -> None:
        floors = self.contract["eligibility_floors"]
        self.assertEqual(sorted(floors["required_gates"]), sorted(frozen_gates()))
        self.assertIs(floors["all_gates_must_pass"], True)
        self.assertIs(floors["availability_gate_required"], True)
        self.assertEqual(floors["verdict_when_floor_unmet"], "no_verdict")
        self.assertEqual(floors["claim_class_when_floor_unmet"], "no_comparative_claim")

        for arm_name, candidate, comparator in (
            (
                "candidate",
                eligible_arm(resource_vector(input_tokens=1), quality_floors_met=False),
                eligible_arm(),
            ),
            (
                "comparator",
                eligible_arm(resource_vector(input_tokens=1)),
                eligible_arm(reliability_guardrails_respected=False),
            ),
        ):
            with self.subTest(ineligible=arm_name):
                outcome = self.compare(candidate, comparator)
                self.assertEqual(outcome["verdict"], "no_verdict")
                self.assertEqual(outcome["stage_reached"], "eligibility_floors")
                self.assertEqual(
                    self.module.claim_class(outcome["verdict"], self.contract)[
                        "permitted_claim_class"
                    ],
                    "no_comparative_claim",
                )

    def test_dominance_rule_declares_all_eight_direction_aware_dimensions(self) -> None:
        rule = self.contract["dominance_rule"]
        self.assertEqual(rule["rule"], "environment_independent_pareto")
        self.assertEqual(rule["evaluation_order"], ["eligibility_floors", "pareto", "materiality_margin"])
        self.assertEqual(rule["dimension_projection"], {"duration_ms": "duration"})
        self.assertEqual(sorted(rule["dimensions"]), sorted(frozen_dimensions()))
        self.assertEqual(sorted(rule["margin_map"]), sorted(frozen_dimensions()))
        self.assertTrue(rule["weights_prohibited"])
        self.assertEqual(rule["margin_denominator"], "comparator_value")
        self.assertEqual(rule["zero_denominator_result"], "margin_not_computable")

    def test_margin_map_preserves_exact_margins_units_directions_and_null_no_worse_values(self) -> None:
        expected = {
            "input_tokens": (0.10, "tokens", "lower_is_better", "margin_eligible"),
            "cached_input_tokens": (0.10, "tokens", "lower_is_better", "margin_eligible"),
            "output_tokens": (0.10, "tokens", "lower_is_better", "margin_eligible"),
            "duration": (0.10, "milliseconds", "lower_is_better", "margin_eligible"),
            "acceptance": (None, "ratio", "higher_is_better", "no_worse_only"),
            "compactions": (None, "count", "lower_is_better", "no_worse_only"),
            "retries": (None, "count", "lower_is_better", "no_worse_only"),
            "terminal_state": (None, "categorical", "equal_only", "no_worse_only"),
        }
        margin_map = self.contract["dominance_rule"]["margin_map"]
        for dimension, (value, unit, direction, klass) in expected.items():
            with self.subTest(dimension=dimension):
                entry = margin_map[dimension]
                self.assertEqual(entry["unit"], unit)
                self.assertEqual(entry["direction"], direction)
                self.assertEqual(entry["class"], klass)
                self.assertEqual(entry.get("relative_margin"), value)

    def test_confidence_and_multiplicity_are_single_valued_and_disjoint(self) -> None:
        confidence = self.contract["confidence_method"]
        self.assertEqual(confidence["method"], "one_sided_lower_confidence_bound")
        self.assertEqual(confidence["confidence_level"], 0.95)
        self.assertEqual(confidence["alpha"], 0.05)
        self.assertEqual(confidence["cluster_unit"], "role")
        self.assertEqual(
            confidence["cluster_adjustment"], "cluster_robust_sandwich_variance_by_role"
        )
        self.assertTrue(confidence["replay_point_estimate_stand_in"])

        multiplicity = self.contract["multiplicity_position"]
        self.assertEqual(multiplicity["family"], "secondary_control_arm_family")
        self.assertEqual(
            multiplicity["adjustment"],
            "holm_bonferroni_within_the_secondary_control_arm_family",
        )
        self.assertEqual(multiplicity["family_wise_alpha"], 0.05)
        self.assertFalse(multiplicity["draws_alpha_from_primary"])
        self.assertTrue(multiplicity["disjoint_from_frozen_families"])

    def test_materiality_uses_the_ten_percent_comparator_denominator_and_zero_guard(self) -> None:
        clears = self.compare(eligible_arm(resource_vector(input_tokens=900)), eligible_arm())
        self.assertEqual(clears["verdict"], "dominant")
        self.assertEqual(clears["per_component"]["input_tokens"], "cleared")

        short = self.compare(eligible_arm(resource_vector(input_tokens=905)), eligible_arm())
        self.assertEqual(short["verdict"], "not_dominant")
        self.assertEqual(short["per_component"]["input_tokens"], "not_cleared")

        zeroed = {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "duration_ms": 0,
        }
        outcome = self.compare(
            eligible_arm(resource_vector(retries=0, **zeroed)),
            eligible_arm(resource_vector(**zeroed)),
        )
        self.assertEqual(outcome["verdict"], "not_dominant")
        self.assertEqual(
            sorted(set(outcome["per_component"].values())),
            ["margin_not_computable"],
        )

    def test_mixed_null_and_terminal_uncertain_outcomes_are_inconclusive(self) -> None:
        cases = {
            "mixed": resource_vector(input_tokens=500, retries=4),
            "null_acceptance": resource_vector(input_tokens=500, acceptance=None),
            "terminal_state": resource_vector(input_tokens=500, terminal_state="failed"),
        }
        for label, vector in cases.items():
            with self.subTest(case=label):
                self.assertEqual(
                    self.compare(eligible_arm(vector), eligible_arm())["verdict"],
                    "inconclusive",
                )

    def test_the_helper_accepts_no_weighted_score_or_price_coefficient(self) -> None:
        for name in ("pareto_verdict", "materiality_filter", "compare"):
            with self.subTest(function=name):
                parameters = list(inspect.signature(getattr(self.module, name)).parameters)
                self.assertEqual(parameters, ["candidate", "comparator", "contract"])
        self.assertNotIn("weighted_score", json.dumps(self.contract, sort_keys=True))
        self.assertNotIn("price_coefficient", json.dumps(self.contract, sort_keys=True))

    def test_the_comparison_owned_category_one_to_six_mirror_members_are_reported(self) -> None:
        report = self.module.comparison_owned_mirror_members(
            handoff_path=REPO_ROOT / "docs" / "ai" / "specs" / ".process" / "CAR-004-twin-handoff.md",
            codex_schema_path=CODEX_COMPARISON_SCHEMA_PATH,
            codex_instance_path=CODEX_COMPARISON_INSTANCE_PATH,
        )
        self.assertEqual(report["comparison_id"], CODEX_COMPARISON_ID)
        self.assertEqual(report["schema_id"], CODEX_COMPARISON_SCHEMA_ID)
        self.assertEqual(set(report["categories_present"]), {1, 2, 3, 5, 6})
        self.assertEqual(report["missing"], [])
        self.assertEqual(report["extra"], [])
        self.assertEqual(report["drifted"], [])
        self.assertEqual(
            report["no_worse_null_margin_dimensions"],
            ["acceptance", "compactions", "retries", "terminal_state"],
        )
        self.assertIn(G56R_003_ANALYSIS_PLAN_ID, report["bound_ids"])


class CodexReleaseClaimPolicyTests(CodexComparisonModuleTestCase):
    """T022 RED: release messaging is explicit and cannot conclude G56R-011."""

    def test_every_reachable_outcome_maps_to_exactly_one_release_claim_policy(self) -> None:
        policies = self.module.release_claim_policies(self.contract)
        self.assertEqual(
            sorted(policies),
            ["dominant", "inconclusive", "no_verdict", "not_dominant"],
        )
        for outcome, policy in policies.items():
            with self.subTest(outcome=outcome):
                self.assertEqual(
                    sorted(policy),
                    [
                        "forbidden_claim_classes",
                        "g56r_011_final_conclusion_allowed",
                        "messaging_restriction",
                        "permitted_claim_class",
                        "static_defaults_may_ship_for_operational_simplicity",
                    ],
                )
                self.assertIs(policy["g56r_011_final_conclusion_allowed"], False)
                self.assertIs(
                    policy["static_defaults_may_ship_for_operational_simplicity"],
                    True,
                )

    def test_dominant_release_policy_restricts_only_wording_not_static_shipment(self) -> None:
        dominant = self.module.release_claim_policy("dominant", self.contract)
        self.assertEqual(
            dominant["permitted_claim_class"],
            "measured_improvement_over_previous_static_baseline",
        )
        self.assertEqual(
            sorted(dominant["forbidden_claim_classes"]),
            ["best_measured", "efficient", "optimal"],
        )
        self.assertIs(dominant["messaging_restriction"], True)
        self.assertIs(
            dominant["static_defaults_may_ship_for_operational_simplicity"], True
        )
        self.assertIs(dominant["g56r_011_final_conclusion_allowed"], False)

    def test_non_dominant_and_no_verdict_release_policies_make_no_comparative_claim(self) -> None:
        for outcome in ("not_dominant", "inconclusive", "no_verdict"):
            with self.subTest(outcome=outcome):
                policy = self.module.release_claim_policy(outcome, self.contract)
                self.assertEqual(policy["permitted_claim_class"], "no_comparative_claim")
                self.assertEqual(policy["forbidden_claim_classes"], [])
                self.assertIs(policy["messaging_restriction"], False)
                self.assertIs(policy["g56r_011_final_conclusion_allowed"], False)

    def test_g56r_004_rejects_any_final_static_core_dominance_conclusion(self) -> None:
        for conclusion in (
            "static_core_dominant",
            "control_arm_dominant",
            "final_g56r_011_verdict",
        ):
            with self.subTest(conclusion=conclusion):
                with self.assertRaises(self.error):
                    self.module.record_g56r_011_dominance_conclusion(
                        conclusion,
                        self.contract,
                    )


TEST_CASES = (
    ControlComparisonDominanceTests,
    ComparisonDocumentShapeTests,
    DimensionProjectionTests,
    EligibilityFloorTests,
    MarginMapTests,
    ParetoStageTests,
    MaterialityMarginTests,
    ThreeStageOrderTests,
    MessagingMapTests,
    ClaimClassTotalityTests,
    CommittedComparisonInstanceTests,
    MarginBoundaryExactnessTests,
    FloorReadStrictnessTests,
    CodexComparisonArtifactPresenceTests,
    CodexComparisonContractTests,
    CodexReleaseClaimPolicyTests,
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-control-comparison-dominance"))
