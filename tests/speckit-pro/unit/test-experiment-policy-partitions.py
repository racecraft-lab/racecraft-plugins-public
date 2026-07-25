#!/usr/bin/env python3
"""Partition registry, pre-execution pair binding, budgets, and workload strata.

Three governance surfaces meet in this file, all of them pre-execution:

* **Partitions** (FR-013). Disjointness is enforced at the **objective** level, not
  the partition level, so an objective identifier appearing in two registered
  partitions fails closed with ``failure_plane=partition``. Calibration always
  carries ``qualification_eligible=false``, and CAR-003 consumes calibration
  objectives only.
* **Pair binding** (FR-037). Every pair binds its whole context before execution.
  A qualification-eligible pair binds the frozen analysis plan; **every**
  ineligible pair binds the versioned calibration protocol instead, because the
  plan freezes only after calibration and a calibration pair cannot bind an
  artifact that does not yet exist. The substitution is keyed on
  ``qualification_eligible`` rather than ``partition_type`` so the two branches
  are exhaustive, and it holds transitively at the experiment-policy edge.
* **Budgets and strata** (FR-022, FR-038, FR-052). The analysis-plan budget is
  authoritative; the policy budget must equal it for eligible partitions and may
  be tighter only for calibration. Stratum membership is fixed before either arm
  runs, from a closed non-realized basis.

Contract-structural cases read the committed schemas under
``specs/car-003-evaluation-runner-scoring/contracts/``; module-contract cases
exercise ``tests/speckit-pro/layer6-efficiency/lib/claude_experiment_policy.py``.

Every check is offline and makes zero live model calls.
"""

from __future__ import annotations

import copy
import hashlib
import json
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

try:  # T068…T070 deliverable — absent until the policy module is implemented.
    import claude_experiment_policy  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    claude_experiment_policy = None  # type: ignore[assignment]


CONTRACT_ROOT = REPO_ROOT / "specs" / "car-003-evaluation-runner-scoring" / "contracts"
ASSIGNMENT_SCHEMA_PATH = CONTRACT_ROOT / "experiment-assignment.schema.json"
POLICY_SCHEMA_PATH = CONTRACT_ROOT / "experiment-policy.schema.json"
PLAN_SCHEMA_PATH = CONTRACT_ROOT / "analysis-plan.schema.json"
ADDITIVE_SCHEMA_PATH = CONTRACT_ROOT / "car-003-additive-records.schema.json"

# FR-013: the closed partition-type set. Stated as a literal so a unilateral
# widening on either side shows up as a diff against this tuple.
PARTITION_TYPES = (
    "calibration",
    "cohort_lock",
    "integrated_confirmation",
    "screening",
    "selection",
)

# FR-022: closed TTL-class key space, shared by both budgets and the diagnostic.
TTL_CLASSES = ("ephemeral_1h", "ephemeral_5m")

# FR-022: the eight live-campaign ceilings.
BUDGET_CEILINGS = (
    "max_attempts",
    "max_cache_read_tokens",
    "max_cache_write_tokens_by_ttl_class",
    "max_candidates",
    "max_confirmation_entries",
    "max_duration_seconds",
    "max_input_tokens",
    "max_output_tokens",
)

# FR-052: the closed pre-execution basis. Every member is a field the role-corpus
# contract already binds, so no new pre-execution vocabulary is coined.
STRATUM_BASIS = (
    "acceptance_oracle",
    "expected_artifacts",
    "mutation_contract",
    "objective",
    "permitted_tools",
    "role_id",
)

# FR-052: post-treatment quantities that may never derive stratum membership.
REALIZED_OUTCOME_QUANTITIES = ("compactions", "duration", "retries", "tokens", "turns")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(record: object) -> str:
    return json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def digest_over(record: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()


def binding(name: str) -> dict[str, str]:
    return {"id": name, "digest": digest_over({"binding": name})}


def sample_budget(**overrides: object) -> dict[str, object]:
    budget: dict[str, object] = {
        "max_attempts": 48,
        "max_duration_seconds": 5400,
        "max_input_tokens": 4_000_000,
        "max_cache_write_tokens_by_ttl_class": {"ephemeral_5m": 800_000, "ephemeral_1h": 200_000},
        "max_cache_read_tokens": 6_000_000,
        "max_output_tokens": 600_000,
        "max_candidates": 4,
        "max_confirmation_entries": 0,
    }
    budget.update(overrides)
    return budget


class PartitionRegistryTests(unittest.TestCase):
    """A versioned registry entry, objective-level disjointness, and the
    calibration-only consumption rule (FR-013, FR-033)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_experiment_policy, "claude_experiment_policy is not importable")
        self.module = claude_experiment_policy
        self.calibration = self.module.build_partition_registry_entry(
            partition_id="CAR-003-CAL-01",
            partition_type="calibration",
            qualification_eligible=False,
            objective_ids=["obj-cal-b", "obj-cal-a", "obj-cal-b"],
            frozen_at="2026-07-24T00:00:00Z",
            owning_spec="car-003-evaluation-runner-scoring",
        )
        self.screening = self.module.build_partition_registry_entry(
            partition_id="CAR-007-SCREEN-01",
            partition_type="screening",
            qualification_eligible=True,
            objective_ids=["obj-screen-a"],
            frozen_at="2026-07-24T00:00:00Z",
            owning_spec="car-007-cohort",
        )

    def test_the_closed_partition_type_set_is_published_by_the_contract(self) -> None:
        schema = load_json(ASSIGNMENT_SCHEMA_PATH)
        entry = schema["$defs"]["partitionRegistryEntry"]  # type: ignore[index]
        self.assertEqual(
            tuple(sorted(entry["properties"]["partition_type"]["enum"])), PARTITION_TYPES
        )
        self.assertEqual(tuple(sorted(self.module.PARTITION_TYPES)), PARTITION_TYPES)

    def test_a_registry_entry_binds_every_governed_field(self) -> None:
        for field in (
            "partition_id",
            "partition_type",
            "qualification_eligible",
            "objective_set_digest",
            "objective_ids",
            "frozen_at",
            "owning_spec",
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.calibration)
                self.assertIsNotNone(self.calibration[field])
        self.assertEqual(self.calibration["record_kind"], "partition_registry_entry")

    def test_the_objective_set_digest_covers_the_deduplicated_sorted_ids(self) -> None:
        self.assertEqual(
            self.calibration["objective_set_digest"], digest_over(["obj-cal-a", "obj-cal-b"])
        )
        self.assertEqual(self.calibration["objective_ids"], ["obj-cal-a", "obj-cal-b"])

    def test_the_digest_helper_sorts_and_deduplicates_its_own_input(self) -> None:
        # The preimage rule lives in the helper, not only in the builder: a caller
        # handing it an unsorted list must still get the sorted-set digest, or two
        # partitions over one objective set would produce two digests.
        self.assertEqual(
            self.module.objective_set_digest(["obj-cal-b", "obj-cal-a", "obj-cal-b"]),
            digest_over(["obj-cal-a", "obj-cal-b"]),
        )
        self.assertEqual(
            self.module.objective_set_digest(["obj-cal-a", "obj-cal-b"]),
            self.module.objective_set_digest(["obj-cal-b", "obj-cal-a"]),
        )
        with self.assertRaises(self.module.ExperimentPolicyError):
            self.module.objective_set_digest([])

    def test_the_same_objectives_in_a_different_order_collide_detectably(self) -> None:
        reordered = self.module.build_partition_registry_entry(
            partition_id="CAR-003-CAL-01-REORDERED",
            partition_type="calibration",
            qualification_eligible=False,
            objective_ids=["obj-cal-b", "obj-cal-a"],
            frozen_at="2026-07-24T00:00:00Z",
            owning_spec="car-003-evaluation-runner-scoring",
        )
        self.assertEqual(
            reordered["objective_set_digest"], self.calibration["objective_set_digest"]
        )

    def test_a_calibration_partition_may_never_be_qualification_eligible(self) -> None:
        with self.assertRaises(self.module.ExperimentPolicyError):
            self.module.build_partition_registry_entry(
                partition_id="CAR-003-CAL-BAD",
                partition_type="calibration",
                qualification_eligible=True,
                objective_ids=["obj-cal-a"],
                frozen_at="2026-07-24T00:00:00Z",
                owning_spec="car-003-evaluation-runner-scoring",
            )
        schema = load_json(ASSIGNMENT_SCHEMA_PATH)
        entry = schema["$defs"]["partitionRegistryEntry"]  # type: ignore[index]
        guard = entry["allOf"][0]
        self.assertEqual(guard["if"]["properties"]["partition_type"]["const"], "calibration")
        self.assertEqual(
            guard["then"]["properties"]["qualification_eligible"]["const"], False
        )

    def test_an_objective_in_two_partitions_fails_closed_on_the_partition_plane(self) -> None:
        overlapping = self.module.build_partition_registry_entry(
            partition_id="CAR-008-SELECT-01",
            partition_type="selection",
            qualification_eligible=True,
            objective_ids=["obj-cal-a", "obj-select-a"],
            frozen_at="2026-07-24T00:00:00Z",
            owning_spec="car-008-cohort",
        )
        verdict = self.module.register_partitions((self.calibration, self.screening, overlapping))
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_plane, "partition")
        self.assertEqual(verdict.failure_code, "cross_partition_reuse")
        self.assertTrue(any("obj-cal-a" in finding for finding in verdict.findings), verdict)

    def test_disjoint_partitions_register_clean(self) -> None:
        verdict = self.module.register_partitions((self.calibration, self.screening))
        self.assertTrue(verdict.ok, verdict)
        self.assertEqual(verdict.failure_plane, "none")
        self.assertEqual(verdict.failure_code, "none")

    def test_a_duplicate_partition_id_is_refused(self) -> None:
        verdict = self.module.register_partitions((self.calibration, self.calibration))
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_plane, "partition")

    def test_partition_type_and_eligibility_are_immutable_after_freeze(self) -> None:
        retyped = dict(self.calibration, partition_type="screening")
        relaxed = dict(self.screening, qualification_eligible=False)
        for mutated, field in ((retyped, "partition_type"), (relaxed, "qualification_eligible")):
            with self.subTest(field=field):
                verdict = self.module.immutability_verdict(
                    self.calibration if field == "partition_type" else self.screening, mutated
                )
                self.assertFalse(verdict.ok)
                self.assertEqual(verdict.failure_plane, "partition")
                self.assertEqual(verdict.failure_code, "partition_mismatch")
                self.assertTrue(any(field in finding for finding in verdict.findings), verdict)

    def test_an_unchanged_entry_passes_the_immutability_check(self) -> None:
        verdict = self.module.immutability_verdict(self.calibration, dict(self.calibration))
        self.assertTrue(verdict.ok, verdict)

    def test_only_ineligible_calibration_objectives_may_be_consumed(self) -> None:
        registry = (self.calibration, self.screening)
        self.assertEqual(
            self.module.consumable_objectives(registry), ("obj-cal-a", "obj-cal-b")
        )
        allowed = self.module.consumption_verdict(registry, "obj-cal-a")
        self.assertTrue(allowed.ok, allowed)

    def test_consuming_a_qualification_eligible_objective_fails_closed(self) -> None:
        verdict = self.module.consumption_verdict((self.calibration, self.screening), "obj-screen-a")
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_plane, "partition")
        self.assertEqual(verdict.failure_code, "partition_not_eligible")

    def test_consuming_an_unregistered_objective_fails_closed(self) -> None:
        verdict = self.module.consumption_verdict((self.calibration,), "obj-unregistered")
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_plane, "partition")
        self.assertEqual(verdict.failure_code, "partition_mismatch")

    def test_every_bundle_class_must_reference_a_registry_bound_partition(self) -> None:
        registry = (self.calibration, self.screening)
        for bundle_kind in ("fixture", "experiment", "score", "decision"):
            with self.subTest(bundle=bundle_kind):
                bound = {
                    "bundle_kind": bundle_kind,
                    "partition": {
                        "partition_id": "CAR-003-CAL-01",
                        "partition_type": "calibration",
                        "qualification_eligible": False,
                    },
                }
                self.assertTrue(self.module.bundle_partition_verdict(bound, registry).ok)
                unbound = copy.deepcopy(bound)
                unbound["partition"]["partition_id"] = "CAR-999-GHOST"  # type: ignore[index]
                verdict = self.module.bundle_partition_verdict(unbound, registry)
                self.assertFalse(verdict.ok)
                self.assertEqual(verdict.failure_plane, "partition")
                self.assertEqual(verdict.failure_code, "partition_mismatch")

    def test_a_bundle_whose_partition_facts_contradict_the_registry_is_refused(self) -> None:
        registry = (self.calibration,)
        lying = {
            "bundle_kind": "decision",
            "partition": {
                "partition_id": "CAR-003-CAL-01",
                "partition_type": "calibration",
                "qualification_eligible": True,
            },
        }
        verdict = self.module.bundle_partition_verdict(lying, registry)
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_code, "partition_mismatch")

    def test_an_undeclared_partition_type_is_refused(self) -> None:
        with self.assertRaises(self.module.ExperimentPolicyError):
            self.module.build_partition_registry_entry(
                partition_id="CAR-003-CAL-02",
                partition_type="pilot",
                qualification_eligible=False,
                objective_ids=["obj-cal-c"],
                frozen_at="2026-07-24T00:00:00Z",
                owning_spec="car-003-evaluation-runner-scoring",
            )


class PreExecutionBindingTests(unittest.TestCase):
    """Every pair binds its whole context before execution, and the calibration
    protocol substitutes for the analysis plan on ineligible partitions
    (FR-037, FR-041)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_experiment_policy, "claude_experiment_policy is not importable")
        self.module = claude_experiment_policy
        self.calibration_pair = self.module.build_assignment(
            comparison_set_id="CS-CAL-01",
            assignment_id="CS-CAL-01-A0",
            partition={
                "partition_id": "CAR-003-CAL-01",
                "partition_type": "calibration",
                "qualification_eligible": False,
            },
            bindings=self.sample_bindings(),
            role_id="implement-executor",
            instruction_hash=digest_over({"instruction": "implement"}),
            configuration_hash=digest_over({"configuration": "pinned"}),
            environment_contract=self.sample_environment(),
            stratum_assignment=self.sample_stratum(),
            assigned_order=0,
            pre_execution_timestamp="2026-07-24T01:00:00Z",
            plan_binding=binding("CAR-003-CALPROTO-V1"),
        )

    @staticmethod
    def sample_bindings() -> dict[str, dict[str, str]]:
        return {
            "candidate_route_binding": binding("route-candidate"),
            "comparator_route_binding": binding("route-comparator"),
            "fixture_binding": binding("fixture-implement-executor"),
            "task_binding": binding("task-cal-001"),
            "capability_freeze_binding": binding("CAR-003-FREEZE-V1"),
            "runtime_snapshot_binding": binding("CAR-003-SNAPSHOT-V1"),
            "route_resolution_binding": binding("route-resolution-v1"),
            "materialization_binding": binding("materialization-v1"),
            "experiment_policy_binding": binding("CAR-003-POLICY-CAL-V1"),
        }

    @staticmethod
    def sample_environment() -> dict[str, object]:
        return {
            "fast_mode_state": "off",
            "client_version_range": {"min": "2.0.0", "max": "2.9.9"},
            "parent_session_model": "claude-opus-5",
            "parent_session_effort": "high",
            "env_override_proof_complete": True,
            "claude_code_subagent_model_unset": True,
            "authentication_mode": "subscription",
        }

    @staticmethod
    def sample_stratum(**overrides: object) -> dict[str, object]:
        stratum: dict[str, object] = {
            "stratum_id": "short-horizon",
            "long_horizon": False,
            "membership_basis": ["role_id", "objective"],
            "derived_from_realized_outcomes": False,
        }
        stratum.update(overrides)
        return stratum

    def test_every_pre_execution_field_is_bound_before_execution(self) -> None:
        for field in self.module.PRE_EXECUTION_BINDING_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, self.calibration_pair)
                self.assertIsNotNone(self.calibration_pair[field])
        self.assertEqual(
            self.module.unbound_pair_fields(self.calibration_pair), ()
        )

    def test_a_pair_missing_any_pre_execution_binding_is_refused(self) -> None:
        for field in ("experiment_policy_binding", "materialization_binding", "assigned_order"):
            with self.subTest(field=field):
                stripped = {
                    key: value
                    for key, value in self.calibration_pair.items()
                    if key != field
                }
                self.assertIn(field, self.module.unbound_pair_fields(stripped))
                verdict = self.module.assignment_verdict(stripped)
                self.assertFalse(verdict.ok)
                self.assertEqual(verdict.failure_plane, "partition")

    def test_an_ineligible_pair_binds_the_calibration_protocol(self) -> None:
        self.assertIn("calibration_protocol_binding", self.calibration_pair)
        self.assertNotIn("analysis_plan_binding", self.calibration_pair)
        self.assertTrue(self.module.assignment_verdict(self.calibration_pair).ok)
        self.assertEqual(
            self.module.required_plan_binding(qualification_eligible=False),
            "calibration_protocol_binding",
        )

    def test_an_eligible_pair_binds_the_frozen_analysis_plan(self) -> None:
        eligible = self.module.build_assignment(
            comparison_set_id="CS-SCREEN-01",
            assignment_id="CS-SCREEN-01-A0",
            partition={
                "partition_id": "CAR-007-SCREEN-01",
                "partition_type": "screening",
                "qualification_eligible": True,
            },
            bindings=self.sample_bindings(),
            role_id="implement-executor",
            instruction_hash=digest_over({"instruction": "implement"}),
            configuration_hash=digest_over({"configuration": "pinned"}),
            environment_contract=self.sample_environment(),
            stratum_assignment=self.sample_stratum(),
            assigned_order=1,
            pre_execution_timestamp="2026-07-24T01:00:00Z",
            plan_binding=binding("CAR-003-PLAN-V1"),
        )
        self.assertIn("analysis_plan_binding", eligible)
        self.assertNotIn("calibration_protocol_binding", eligible)
        self.assertEqual(
            self.module.required_plan_binding(qualification_eligible=True), "analysis_plan_binding"
        )
        self.assertTrue(self.module.assignment_verdict(eligible).ok)

    def test_the_substitution_is_keyed_on_eligibility_not_partition_type(self) -> None:
        # A NON-calibration ineligible partition must still bind the protocol;
        # keying on partition_type alone would leave it bound to neither.
        ineligible_screening = self.module.build_assignment(
            comparison_set_id="CS-SCREEN-02",
            assignment_id="CS-SCREEN-02-A0",
            partition={
                "partition_id": "CAR-007-SCREEN-02",
                "partition_type": "screening",
                "qualification_eligible": False,
            },
            bindings=self.sample_bindings(),
            role_id="phase-executor",
            instruction_hash=digest_over({"instruction": "plan"}),
            configuration_hash=digest_over({"configuration": "pinned"}),
            environment_contract=self.sample_environment(),
            stratum_assignment=self.sample_stratum(),
            assigned_order=0,
            pre_execution_timestamp="2026-07-24T01:00:00Z",
            plan_binding=binding("CAR-003-CALPROTO-V1"),
        )
        self.assertIn("calibration_protocol_binding", ineligible_screening)
        self.assertNotIn("analysis_plan_binding", ineligible_screening)

    def test_binding_both_artifacts_is_rejected(self) -> None:
        both = copy.deepcopy(self.calibration_pair)
        both["analysis_plan_binding"] = binding("CAR-003-PLAN-V1")
        verdict = self.module.assignment_verdict(both)
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_plane, "partition")
        self.assertTrue(any("both" in finding for finding in verdict.findings), verdict)

    def test_binding_neither_artifact_is_rejected(self) -> None:
        neither = {
            key: value
            for key, value in self.calibration_pair.items()
            if key != "calibration_protocol_binding"
        }
        verdict = self.module.assignment_verdict(neither)
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_plane, "partition")

    def test_binding_the_wrong_artifact_for_the_eligibility_is_rejected(self) -> None:
        swapped = {
            key: value
            for key, value in self.calibration_pair.items()
            if key != "calibration_protocol_binding"
        }
        swapped["analysis_plan_binding"] = binding("CAR-003-PLAN-V1")
        verdict = self.module.assignment_verdict(swapped)
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_code, "partition_not_eligible")

    def test_the_substitution_holds_transitively_at_the_policy_edge(self) -> None:
        calibration_policy = self.module.build_experiment_policy(
            experiment_policy_id="CAR-003-POLICY-CAL-V1",
            partition={
                "partition_id": "CAR-003-CAL-01",
                "partition_type": "calibration",
                "qualification_eligible": False,
            },
            candidate_freeze_binding=binding("CAR-003-FREEZE-V1"),
            corpus_binding=binding("CAR-003-CORPUS-V1"),
            plan_binding=binding("CAR-003-CALPROTO-V1"),
            scorer_family_exclusion=self.sample_exclusion(),
            budget=sample_budget(),
            rerun_cap=1,
        )
        self.assertIn("calibration_protocol_binding", calibration_policy)
        self.assertNotIn("analysis_plan_binding", calibration_policy)
        self.assertTrue(self.module.policy_verdict(calibration_policy).ok)

        reintroduced_cycle = copy.deepcopy(calibration_policy)
        del reintroduced_cycle["calibration_protocol_binding"]
        reintroduced_cycle["analysis_plan_binding"] = binding("CAR-003-PLAN-V1")
        verdict = self.module.policy_verdict(reintroduced_cycle)
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_plane, "partition")

    @staticmethod
    def sample_exclusion() -> dict[str, object]:
        return {
            "static": True,
            "paraphrase_normalization": "prohibited",
            "presentation_order_seed": "car-003-calibration-seed",
            "entries": [
                {"candidate_route_id": "route-candidate", "excluded_families": ["claude"]}
            ],
        }

    def test_the_calibration_protocol_carries_no_margins_or_thresholds(self) -> None:
        # This is what breaks the circular dependency: the artifact a calibration
        # pair binds cannot itself carry the numbers that only freeze afterwards.
        protocol = self.module.build_calibration_protocol(
            calibration_protocol_id="CAR-003-CALPROTO-V1",
            partition_binding=binding("CAR-003-CAL-01"),
            objective_bindings=[binding("obj-cal-a"), binding("obj-cal-b")],
            frozen_at="2026-07-24T00:00:00Z",
        )
        self.assertEqual(protocol["record_kind"], "calibration_protocol")
        for pinned in ("carries_margins", "carries_sample_sizes", "carries_terminal_thresholds"):
            with self.subTest(field=pinned):
                self.assertFalse(protocol[pinned])
                schema = load_json(ASSIGNMENT_SCHEMA_PATH)
                published = schema["$defs"]["calibrationProtocol"]  # type: ignore[index]
                self.assertFalse(published["properties"][pinned]["const"])
        self.assertEqual(
            protocol["protocol_digest"],
            digest_over({k: v for k, v in protocol.items() if k != "protocol_digest"}),
        )

    def test_the_contract_encodes_the_substitution_as_paired_branches(self) -> None:
        for schema_path, node in (
            (POLICY_SCHEMA_PATH, None),
            (ASSIGNMENT_SCHEMA_PATH, "comparisonSetAssignment"),
        ):
            with self.subTest(schema=schema_path.name):
                schema = load_json(schema_path)
                target = schema if node is None else schema["$defs"][node]  # type: ignore[index]
                branches = target["allOf"]
                self.assertEqual(len(branches), 2)
                eligible, ineligible = branches
                self.assertEqual(eligible["then"]["required"], ["analysis_plan_binding"])
                self.assertEqual(
                    eligible["then"]["not"]["required"], ["calibration_protocol_binding"]
                )
                self.assertEqual(ineligible["then"]["required"], ["calibration_protocol_binding"])
                self.assertEqual(ineligible["then"]["not"]["required"], ["analysis_plan_binding"])

    def test_a_refresh_records_an_additive_invalidation_and_never_rebinds(self) -> None:
        refreshed = self.module.refresh_assignment(
            self.calibration_pair,
            reason="capability_changed",
            recorded_at="2026-07-25T00:00:00Z",
        )
        self.assertEqual(
            refreshed["calibration_protocol_binding"],
            self.calibration_pair["calibration_protocol_binding"],
        )
        self.assertEqual(
            refreshed["capability_freeze_binding"],
            self.calibration_pair["capability_freeze_binding"],
        )
        self.assertEqual(refreshed["assignment_id"], self.calibration_pair["assignment_id"])
        self.assertEqual(
            refreshed["invalidations"],
            [{"reason": "capability_changed", "recorded_at": "2026-07-25T00:00:00Z"}],
        )
        # The original record is untouched.
        self.assertNotIn("invalidations", self.calibration_pair)

    def test_repeated_refreshes_accumulate_rather_than_replace(self) -> None:
        once = self.module.refresh_assignment(
            self.calibration_pair, reason="fixture_changed", recorded_at="2026-07-25T00:00:00Z"
        )
        twice = self.module.refresh_assignment(
            once, reason="scorer_changed", recorded_at="2026-07-26T00:00:00Z"
        )
        self.assertEqual([entry["reason"] for entry in twice["invalidations"]],
                         ["fixture_changed", "scorer_changed"])

    def test_rebinding_a_bound_pair_is_refused_outright(self) -> None:
        with self.assertRaises(self.module.ExperimentPolicyError):
            self.module.rebind_assignment(
                self.calibration_pair, plan_binding=binding("CAR-003-CALPROTO-V2")
            )

    def test_an_unknown_invalidation_reason_is_refused(self) -> None:
        with self.assertRaises(self.module.ExperimentPolicyError):
            self.module.refresh_assignment(
                self.calibration_pair, reason="vibes_changed", recorded_at="2026-07-25T00:00:00Z"
            )


class CampaignBudgetAndStratumTests(unittest.TestCase):
    """The analysis-plan budget is authoritative, the TTL key space is closed, and
    stratum membership is fixed before either arm runs (FR-022, FR-038, FR-052)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_experiment_policy, "claude_experiment_policy is not importable")
        self.module = claude_experiment_policy
        self.plan_budget = sample_budget()

    def test_the_eight_ceilings_are_the_closed_budget_surface(self) -> None:
        self.assertEqual(tuple(sorted(self.module.BUDGET_CEILINGS)), BUDGET_CEILINGS)
        for schema_path in (POLICY_SCHEMA_PATH, PLAN_SCHEMA_PATH):
            with self.subTest(schema=schema_path.name):
                schema = load_json(schema_path)
                budget = schema["$defs"]["budget"]  # type: ignore[index]
                self.assertEqual(tuple(sorted(budget["required"])), BUDGET_CEILINGS)
                self.assertFalse(budget["additionalProperties"])

    def test_the_ttl_class_key_space_is_closed_to_exactly_two_members(self) -> None:
        self.assertEqual(tuple(sorted(self.module.TTL_CLASSES)), TTL_CLASSES)
        for schema_path, pointer in (
            (POLICY_SCHEMA_PATH, ("$defs", "budget")),
            (PLAN_SCHEMA_PATH, ("$defs", "budget")),
        ):
            with self.subTest(schema=schema_path.name):
                node: object = load_json(schema_path)
                for key in pointer:
                    node = node[key]  # type: ignore[index]
                ttl = node["properties"]["max_cache_write_tokens_by_ttl_class"]  # type: ignore[index]
                self.assertEqual(tuple(sorted(ttl["propertyNames"]["enum"])), TTL_CLASSES)

    def test_the_cache_diagnostic_uses_the_identical_ttl_key_set(self) -> None:
        schema = load_json(ADDITIVE_SCHEMA_PATH)
        diagnostic = schema["$defs"]["cacheDiagnosticRecord"]  # type: ignore[index]
        keys = diagnostic["properties"]["cache_write_tokens_by_ttl_class"]["propertyNames"]["enum"]
        self.assertEqual(tuple(sorted(keys)), TTL_CLASSES)
        self.assertFalse(diagnostic["properties"]["decision_bearing"]["const"])

    def test_an_eligible_policy_budget_must_equal_the_plan_budget(self) -> None:
        verdict = self.module.budget_verdict(
            policy_budget=sample_budget(),
            plan_budget=self.plan_budget,
            qualification_eligible=True,
        )
        self.assertTrue(verdict.ok, verdict)

    def test_an_eligible_policy_budget_that_is_tighter_still_fails_closed(self) -> None:
        verdict = self.module.budget_verdict(
            policy_budget=sample_budget(max_attempts=24),
            plan_budget=self.plan_budget,
            qualification_eligible=True,
        )
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_plane, "partition")
        self.assertEqual(verdict.failure_code, "partition_mismatch")
        self.assertTrue(any("max_attempts" in finding for finding in verdict.findings), verdict)

    def test_an_eligible_policy_budget_that_is_looser_fails_closed(self) -> None:
        verdict = self.module.budget_verdict(
            policy_budget=sample_budget(max_output_tokens=900_000),
            plan_budget=self.plan_budget,
            qualification_eligible=True,
        )
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_plane, "partition")

    def test_a_calibration_budget_may_be_tighter_on_every_ceiling(self) -> None:
        verdict = self.module.budget_verdict(
            policy_budget=sample_budget(
                max_attempts=8,
                max_duration_seconds=900,
                max_cache_write_tokens_by_ttl_class={
                    "ephemeral_5m": 100_000,
                    "ephemeral_1h": 0,
                },
            ),
            plan_budget=self.plan_budget,
            qualification_eligible=False,
        )
        self.assertTrue(verdict.ok, verdict)

    def test_a_calibration_budget_looser_than_the_plan_fails_closed(self) -> None:
        verdict = self.module.budget_verdict(
            policy_budget=sample_budget(max_input_tokens=9_000_000),
            plan_budget=self.plan_budget,
            qualification_eligible=False,
        )
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_plane, "partition")
        self.assertTrue(any("max_input_tokens" in finding for finding in verdict.findings), verdict)

    def test_a_budget_missing_a_ceiling_fails_closed(self) -> None:
        incomplete = sample_budget()
        del incomplete["max_candidates"]
        verdict = self.module.budget_verdict(
            policy_budget=incomplete, plan_budget=self.plan_budget, qualification_eligible=True
        )
        self.assertFalse(verdict.ok)
        self.assertTrue(any("max_candidates" in finding for finding in verdict.findings), verdict)

    def test_a_ttl_class_outside_the_closed_key_space_fails_closed(self) -> None:
        verdict = self.module.budget_verdict(
            policy_budget=sample_budget(
                max_cache_write_tokens_by_ttl_class={"ephemeral_5m": 1, "persistent_24h": 1}
            ),
            plan_budget=self.plan_budget,
            qualification_eligible=False,
        )
        self.assertFalse(verdict.ok)
        self.assertTrue(
            any("persistent_24h" in finding for finding in verdict.findings), verdict
        )

    def test_the_permitted_stratum_basis_is_closed_to_pre_execution_characteristics(self) -> None:
        self.assertEqual(tuple(sorted(self.module.STRATUM_BASIS)), STRATUM_BASIS)
        schema = load_json(ASSIGNMENT_SCHEMA_PATH)
        assignment = schema["$defs"]["comparisonSetAssignment"]  # type: ignore[index]
        basis = assignment["properties"]["stratum_assignment"]["properties"]["membership_basis"]
        self.assertEqual(tuple(sorted(basis["items"]["enum"])), STRATUM_BASIS)
        self.assertEqual(basis["minItems"], 1)

    def test_a_realized_outcome_may_never_appear_in_the_basis(self) -> None:
        for quantity in REALIZED_OUTCOME_QUANTITIES:
            with self.subTest(quantity=quantity):
                self.assertNotIn(quantity, self.module.STRATUM_BASIS)
                verdict = self.module.stratum_verdict(
                    {
                        "stratum_id": "long-horizon",
                        "long_horizon": True,
                        "membership_basis": [quantity],
                        "derived_from_realized_outcomes": False,
                    }
                )
                self.assertFalse(verdict.ok)
                self.assertEqual(verdict.failure_plane, "partition")

    def test_an_empty_basis_is_refused(self) -> None:
        verdict = self.module.stratum_verdict(
            {
                "stratum_id": "short-horizon",
                "long_horizon": False,
                "membership_basis": [],
                "derived_from_realized_outcomes": False,
            }
        )
        self.assertFalse(verdict.ok)
        self.assertTrue(any("basis" in finding for finding in verdict.findings), verdict)

    def test_membership_derived_from_realized_outcomes_is_refused(self) -> None:
        verdict = self.module.stratum_verdict(
            {
                "stratum_id": "long-horizon",
                "long_horizon": True,
                "membership_basis": ["role_id"],
                "derived_from_realized_outcomes": True,
            }
        )
        self.assertFalse(verdict.ok)
        self.assertTrue(
            any("derived_from_realized_outcomes" in finding for finding in verdict.findings),
            verdict,
        )

    def test_a_valid_pre_execution_stratum_assignment_passes(self) -> None:
        verdict = self.module.stratum_verdict(
            {
                "stratum_id": "long-horizon",
                "long_horizon": True,
                "membership_basis": ["role_id", "objective", "acceptance_oracle"],
                "derived_from_realized_outcomes": False,
            }
        )
        self.assertTrue(verdict.ok, verdict)

    def test_the_long_horizon_stratum_carries_its_own_power_declaration(self) -> None:
        manifest = self.sample_manifest()
        long_horizon = self.module.long_horizon_strata(manifest)
        self.assertEqual(tuple(stratum["stratum_id"] for stratum in long_horizon), ("long-horizon",))
        for stratum in long_horizon:
            self.assertIn("stratum_sample_size", stratum)
            self.assertIn("stratum_minimum_unique_tasks", stratum)
        self.assertEqual(self.module.manifest_findings(manifest), ())

    def test_a_long_horizon_stratum_inheriting_the_pooled_numbers_is_refused(self) -> None:
        manifest = self.sample_manifest()
        for stratum in manifest["strata"]:
            if stratum["long_horizon"]:
                del stratum["stratum_sample_size"]
        findings = self.module.manifest_findings(manifest)
        self.assertTrue(any("stratum_sample_size" in finding for finding in findings), findings)

    def test_a_task_matching_no_registered_stratum_returns_inconclusive(self) -> None:
        manifest = self.sample_manifest()
        self.assertEqual(self.module.UNKNOWN_STRATUM_RESULT, "inconclusive")
        resolved = self.module.resolve_stratum(manifest, "short-horizon")
        self.assertEqual(resolved.stratum_id, "short-horizon")
        self.assertEqual(resolved.result, "resolved")
        unknown = self.module.resolve_stratum(manifest, "epic-horizon")
        self.assertIsNone(unknown.stratum_id)
        self.assertEqual(unknown.result, "inconclusive")

    def test_the_plan_contract_pins_the_unknown_stratum_policy(self) -> None:
        schema = load_json(PLAN_SCHEMA_PATH)
        manifest = schema["properties"]["workload_manifest"]  # type: ignore[index]
        self.assertEqual(manifest["properties"]["unknown_stratum_policy"]["const"], "inconclusive")
        stratum = manifest["properties"]["strata"]["items"]
        self.assertIn("stratum_sample_size", stratum["required"])
        self.assertIn("stratum_minimum_unique_tasks", stratum["required"])
        rule = stratum["properties"]["membership_rule"]
        self.assertFalse(rule["properties"]["derived_from_realized_outcomes"]["const"])

    @staticmethod
    def sample_manifest() -> dict[str, object]:
        return {
            "manifest_id": "CAR-003-WORKLOAD-V1",
            "minimum_unique_tasks": 12,
            "unknown_stratum_policy": "inconclusive",
            "strata": [
                {
                    "stratum_id": "short-horizon",
                    "weight": 0.6,
                    "long_horizon": False,
                    "membership_rule": {
                        "permitted_basis": ["role_id", "objective"],
                        "derived_from_realized_outcomes": False,
                    },
                    "stratum_minimum_unique_tasks": 12,
                    "stratum_sample_size": 48,
                },
                {
                    "stratum_id": "long-horizon",
                    "weight": 0.4,
                    "long_horizon": True,
                    "membership_rule": {
                        "permitted_basis": ["role_id", "expected_artifacts", "acceptance_oracle"],
                        "derived_from_realized_outcomes": False,
                    },
                    "stratum_minimum_unique_tasks": 20,
                    "stratum_sample_size": 64,
                },
            ],
        }


TEST_CASES = (
    PartitionRegistryTests,
    PreExecutionBindingTests,
    CampaignBudgetAndStratumTests,
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-experiment-policy-partitions"))
