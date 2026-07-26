#!/usr/bin/env python3
"""The ordered decision ladder, Pareto dominance, terminal mapping, and replay.

The ladder is **ordered and short-circuiting**: absolute semantic and reliability
floors, then task-paired cluster-adjusted non-inferiority, then Pareto dominance
over the eight raw dimensions. A stage that was not reached records
``not_evaluated`` rather than being omitted, because an omitted stage and a
passed stage are indistinguishable to a reader and SC-007 is a claim about order,
not about outcomes (FR-017, FR-018).

Dominance is decidable only because each dimension declares a **direction of
preference** (FR-058). Six resource dimensions are lower-is-better, acceptance is
higher-is-better, and terminal state is categorical and unordered — "no worse" on
terminal state means *equal*, and any difference makes the comparison mixed
rather than silently better or worse.

``reasoning_output_tokens`` is recorded and reported for every attempt and is
**never** a Pareto dimension while the twin's frozen policy omits it. That is a
stated limitation, not a claim the cost is absent: the field is disjoint from
``output_tokens`` and is billed, so a route whose cost concentrates in reasoning
can look cheaper than it is (FR-049).

Nothing here forces a weighted ranking. A failed gate, tie, mixed dominance,
incomplete evidence, or statistical uncertainty each routes to its own closed
terminal member, and no scalar score, per-category weight, or price coefficient
appears anywhere in a decision bundle (FR-019).

Every check is offline and makes zero live model calls.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import sys
import unittest
from pathlib import Path
from statistics import NormalDist


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LIB_DIR = TEST_ROOT / "lib"
LAYER6_LIB_DIR = TEST_ROOT / "layer6-efficiency" / "lib"
for _path in (LIB_DIR, LAYER6_LIB_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from test_result import run_counted  # noqa: E402

try:  # T071…T075 deliverable — absent until the decision module is implemented.
    import claude_analysis_decision  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    claude_analysis_decision = None  # type: ignore[assignment]

try:  # Budget authority lives with the experiment policy, not with the ladder.
    import claude_experiment_policy  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    claude_experiment_policy = None  # type: ignore[assignment]


CONTRACT_ROOT = REPO_ROOT / "specs" / "car-003-evaluation-runner-scoring" / "contracts"
PLAN_SCHEMA_PATH = CONTRACT_ROOT / "analysis-plan.schema.json"
DECISION_SCHEMA_PATH = CONTRACT_ROOT / "analysis-decision.schema.json"
ADDITIVE_SCHEMA_PATH = CONTRACT_ROOT / "car-003-additive-records.schema.json"
REPLAY_FIXTURE_PATH = (
    TEST_ROOT / "layer6-efficiency" / "fixtures" / "car-003-calibration-replay.json"
)
RESEARCH_ROOT = REPO_ROOT / "docs" / "ai" / "research"
CALIBRATION_PILOT_PATH = RESEARCH_ROOT / "claude-car-003-calibration-pilot.json"
FROZEN_PLAN_PATH = RESEARCH_ROOT / "claude-car-003-analysis-plan.json"

# SC-012: the cohort specs whose outcomes the plan must pre-date.
COHORT_SPECS = ("CAR-007", "CAR-008", "CAR-009", "CAR-010")
COHORT_ARTIFACT_PATTERN = re.compile(r"car-0(0[789]|10)(?![0-9])", re.IGNORECASE)

# FR-017, FR-018: the ladder, in the only order it may run.
LADDER_GATES = (
    "bindings",
    "partition",
    "treatment",
    "deterministic",
    "provenance",
    "completeness",
    "floors",
    "non_inferiority",
    "pareto",
)

# FR-018: exactly eight decision-bearing dimensions, identical to the twin's
# frozen policy. Stated as a literal so a unilateral addition on either platform
# shows up as a diff against this tuple.
PARETO_DIMENSIONS = (
    "acceptance",
    "cached_input_tokens",
    "compactions",
    "duration",
    "input_tokens",
    "output_tokens",
    "retries",
    "terminal_state",
)

# FR-058: direction of preference, declared rather than inferred.
LOWER_IS_BETTER = (
    "cached_input_tokens",
    "compactions",
    "duration",
    "input_tokens",
    "output_tokens",
    "retries",
)
HIGHER_IS_BETTER = ("acceptance",)
CATEGORICAL_UNORDERED = ("terminal_state",)

TERMINAL_STATES = (
    "calibration_complete",
    "inconclusive",
    "invalid",
    "no_qualification",
    "qualified",
)

# FR-020: candidate-plane outcomes retained in the estimand at acceptance zero.
ESTIMAND_RETAINED_CODES = (
    "candidate_abandoned",
    "candidate_budget_exhausted",
    "candidate_cancelled",
    "candidate_failed",
    "candidate_timed_out",
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(record: object) -> str:
    return json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def digest_over(record: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()


def vector(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "input_tokens": 120_000,
        "cached_input_tokens": 40_000,
        "output_tokens": 9_000,
        "duration": 240_000,
        "retries": 1,
        "compactions": 0,
        "acceptance": 1.0,
        "terminal_state": "completed",
    }
    base.update(overrides)
    return base


class OrderedLadderTests(unittest.TestCase):
    """Floors, then non-inferiority, then the resource comparison — and a stage
    that was not reached is recorded, never omitted (FR-017, FR-018, SC-007)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_analysis_decision, "claude_analysis_decision is not importable")
        self.module = claude_analysis_decision

    def test_the_ladder_declares_its_stages_in_the_only_permitted_order(self) -> None:
        self.assertEqual(self.module.LADDER_GATES, LADDER_GATES)
        floors = LADDER_GATES.index("floors")
        non_inferiority = LADDER_GATES.index("non_inferiority")
        pareto = LADDER_GATES.index("pareto")
        self.assertLess(floors, non_inferiority)
        self.assertLess(non_inferiority, pareto)

    def test_the_contract_publishes_the_same_ordered_gate_set(self) -> None:
        schema = load_json(DECISION_SCHEMA_PATH)
        gates = schema["properties"]["ordered_gate_results"]["items"]["properties"]["gate"]  # type: ignore[index]
        self.assertEqual(tuple(gates["enum"]), LADDER_GATES)

    def test_every_stage_is_recorded_even_when_all_pass(self) -> None:
        results = self.module.evaluate_ladder({gate: "pass" for gate in LADDER_GATES})
        self.assertEqual(tuple(entry["gate"] for entry in results), LADDER_GATES)
        self.assertEqual({entry["result"] for entry in results}, {"pass"})

    def test_a_stage_after_a_failure_records_not_evaluated_rather_than_omission(self) -> None:
        results = self.module.evaluate_ladder(
            {
                **{gate: "pass" for gate in LADDER_GATES},
                "floors": "fail",
            }
        )
        by_gate = {entry["gate"]: entry["result"] for entry in results}
        self.assertEqual(tuple(by_gate), LADDER_GATES)
        self.assertEqual(by_gate["floors"], "fail")
        self.assertEqual(by_gate["non_inferiority"], "not_evaluated")
        self.assertEqual(by_gate["pareto"], "not_evaluated")

    def test_pareto_is_not_evaluated_until_non_inferiority_passes(self) -> None:
        results = self.module.evaluate_ladder(
            {**{gate: "pass" for gate in LADDER_GATES}, "non_inferiority": "fail"}
        )
        by_gate = {entry["gate"]: entry["result"] for entry in results}
        self.assertEqual(by_gate["floors"], "pass")
        self.assertEqual(by_gate["non_inferiority"], "fail")
        self.assertEqual(by_gate["pareto"], "not_evaluated")

    def test_an_early_gate_failure_short_circuits_the_whole_ladder(self) -> None:
        results = self.module.evaluate_ladder(
            {**{gate: "pass" for gate in LADDER_GATES}, "bindings": "fail"}
        )
        by_gate = {entry["gate"]: entry["result"] for entry in results}
        self.assertEqual(by_gate["bindings"], "fail")
        for gate in LADDER_GATES[1:]:
            with self.subTest(gate=gate):
                self.assertEqual(by_gate[gate], "not_evaluated")

    def test_an_uncertain_stage_also_stops_the_ladder(self) -> None:
        results = self.module.evaluate_ladder(
            {**{gate: "pass" for gate in LADDER_GATES}, "non_inferiority": "uncertain"}
        )
        by_gate = {entry["gate"]: entry["result"] for entry in results}
        self.assertEqual(by_gate["non_inferiority"], "uncertain")
        self.assertEqual(by_gate["pareto"], "not_evaluated")

    def test_an_unsupplied_stage_defaults_to_not_evaluated(self) -> None:
        results = self.module.evaluate_ladder({"bindings": "pass"})
        by_gate = {entry["gate"]: entry["result"] for entry in results}
        self.assertEqual(by_gate["bindings"], "pass")
        self.assertEqual(by_gate["partition"], "not_evaluated")

    def test_an_undeclared_stage_or_result_is_refused(self) -> None:
        with self.assertRaises(self.module.AnalysisDecisionError):
            self.module.evaluate_ladder({"vibes": "pass"})
        with self.assertRaises(self.module.AnalysisDecisionError):
            self.module.evaluate_ladder({"bindings": "probably"})


class ParetoDominanceTests(unittest.TestCase):
    """Eight dimensions, a declared direction for each, categorical terminal state,
    and a reasoning-token report beside every result (FR-018, FR-049, FR-058)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_analysis_decision, "claude_analysis_decision is not importable")
        self.module = claude_analysis_decision

    def test_the_dimension_set_is_exactly_eight_and_matches_the_frozen_policy(self) -> None:
        self.assertEqual(tuple(sorted(self.module.PARETO_DIMENSIONS)), PARETO_DIMENSIONS)
        self.assertEqual(len(self.module.PARETO_DIMENSIONS), 8)
        schema = load_json(PLAN_SCHEMA_PATH)
        policy = schema["properties"]["pareto_policy"]  # type: ignore[index]
        published = policy["properties"]["dimensions"]
        self.assertEqual(tuple(sorted(published["items"]["enum"])), PARETO_DIMENSIONS)
        self.assertEqual(published["minItems"], 8)
        self.assertEqual(published["maxItems"], 8)
        self.assertTrue(policy["properties"]["weights_prohibited"]["const"])
        self.assertEqual(policy["properties"]["mixed_or_tied_result"]["const"], "inconclusive")

    def test_every_dimension_declares_a_direction_of_preference(self) -> None:
        for dimension in PARETO_DIMENSIONS:
            with self.subTest(dimension=dimension):
                self.assertIn(dimension, self.module.DIRECTION_OF_PREFERENCE)
        self.assertEqual(
            tuple(sorted(self.module.DIRECTION_OF_PREFERENCE)), PARETO_DIMENSIONS
        )
        for dimension in LOWER_IS_BETTER:
            with self.subTest(dimension=dimension):
                self.assertEqual(
                    self.module.DIRECTION_OF_PREFERENCE[dimension], "lower_is_better"
                )
        for dimension in HIGHER_IS_BETTER:
            with self.subTest(dimension=dimension):
                self.assertEqual(
                    self.module.DIRECTION_OF_PREFERENCE[dimension], "higher_is_better"
                )
        for dimension in CATEGORICAL_UNORDERED:
            with self.subTest(dimension=dimension):
                self.assertEqual(
                    self.module.DIRECTION_OF_PREFERENCE[dimension], "categorical_unordered"
                )

    def test_a_lower_resource_reading_is_better_and_a_higher_one_is_worse(self) -> None:
        for dimension in LOWER_IS_BETTER:
            with self.subTest(dimension=dimension):
                self.assertEqual(self.module.compare_dimension(dimension, 1, 2), "better")
                self.assertEqual(self.module.compare_dimension(dimension, 2, 1), "worse")
                self.assertEqual(self.module.compare_dimension(dimension, 2, 2), "equal")

    def test_higher_acceptance_is_better(self) -> None:
        self.assertEqual(self.module.compare_dimension("acceptance", 1.0, 0.0), "better")
        self.assertEqual(self.module.compare_dimension("acceptance", 0.0, 1.0), "worse")
        self.assertEqual(self.module.compare_dimension("acceptance", 1.0, 1.0), "equal")

    def test_terminal_state_is_categorical_so_any_difference_is_mixed(self) -> None:
        self.assertEqual(
            self.module.compare_dimension("terminal_state", "completed", "completed"), "equal"
        )
        for other in ("timed_out", "cancelled", "failed"):
            with self.subTest(terminal_state=other):
                self.assertEqual(
                    self.module.compare_dimension("terminal_state", "completed", other), "mixed"
                )
                self.assertEqual(
                    self.module.compare_dimension("terminal_state", other, "completed"), "mixed"
                )

    def test_a_candidate_no_worse_everywhere_and_better_somewhere_dominates(self) -> None:
        result = self.module.pareto_compare(vector(input_tokens=100_000), vector())
        self.assertEqual(result.result, "candidate_dominates")
        self.assertEqual(result.better_on, ("input_tokens",))
        self.assertEqual(result.worse_on, ())

    def test_a_comparator_that_is_better_everywhere_dominates(self) -> None:
        result = self.module.pareto_compare(vector(), vector(input_tokens=100_000))
        self.assertEqual(result.result, "comparator_dominates")

    def test_a_strictly_beaten_candidate_fails_the_stage_and_cannot_qualify(self) -> None:
        """A candidate the comparator dominates MUST NOT pass the resource stage.

        Regression guard. The mapping previously treated `comparator_dominates`
        as a stage pass, which is the clearest possible losing case. With no
        condition raised the terminal resolver saw an empty condition set and
        returned `qualified`, so the worst possible candidate qualified. Only
        calibration partitions being ineligible kept that off a real decision.
        """
        for outcome, expected in (
            ("candidate_dominates", "pass"),
            ("comparator_dominates", "fail"),
            ("mixed", "fail"),
            ("tie", "fail"),
            ("uncertain", "uncertain"),
        ):
            with self.subTest(outcome=outcome):
                self.assertEqual(self.module._pareto_stage_result(outcome), expected)

        # End to end: the strictly-beaten candidate must not reach `qualified`.
        beaten = self.module.pareto_compare(vector(), vector(input_tokens=100_000))
        self.assertEqual(beaten.result, "comparator_dominates")
        self.assertEqual(self.module._pareto_stage_result(beaten.result), "fail")

    def test_identical_vectors_tie(self) -> None:
        self.assertEqual(self.module.pareto_compare(vector(), vector()).result, "tie")

    def test_better_on_one_and_worse_on_another_is_mixed(self) -> None:
        result = self.module.pareto_compare(
            vector(input_tokens=100_000), vector(output_tokens=8_000)
        )
        self.assertEqual(result.result, "mixed")
        self.assertEqual(result.better_on, ("input_tokens",))
        self.assertEqual(result.worse_on, ("output_tokens",))

    def test_a_terminal_state_difference_makes_the_whole_comparison_mixed(self) -> None:
        # Better on every resource dimension, but a different terminal state:
        # never silently promoted to dominance.
        result = self.module.pareto_compare(
            vector(input_tokens=1, output_tokens=1, duration=1, terminal_state="timed_out"),
            vector(),
        )
        self.assertEqual(result.result, "mixed")
        self.assertIn("terminal_state", result.mixed_on)

    def test_a_missing_or_null_dimension_returns_uncertain(self) -> None:
        incomplete = vector()
        del incomplete["retries"]
        self.assertEqual(self.module.pareto_compare(incomplete, vector()).result, "uncertain")
        self.assertEqual(
            self.module.pareto_compare(vector(compactions=None), vector()).result, "uncertain"
        )

    def test_a_ninth_dimension_is_refused_rather_than_silently_compared(self) -> None:
        with self.assertRaises(self.module.AnalysisDecisionError):
            self.module.pareto_compare(
                dict(vector(), reasoning_output_tokens=1_000), dict(vector(), reasoning_output_tokens=2_000)
            )

    def test_reasoning_output_tokens_is_reported_but_never_decision_bearing(self) -> None:
        self.assertNotIn("reasoning_output_tokens", self.module.PARETO_DIMENSIONS)
        schema = load_json(PLAN_SCHEMA_PATH)
        policy = schema["properties"]["pareto_policy"]  # type: ignore[index]
        self.assertNotIn("reasoning_output_tokens", policy["properties"]["dimensions"]["items"]["enum"])
        self.assertFalse(policy["properties"]["reasoning_tokens_decision_bearing"]["const"])
        report = self.module.reasoning_token_report(41_200)
        self.assertEqual(report["reasoning_output_tokens_total"], 41_200)
        self.assertFalse(report["decision_bearing"])
        self.assertTrue(report["stated_limitation"])

    def test_a_dominance_result_always_carries_its_reasoning_token_report(self) -> None:
        reported = self.module.dominance_with_reasoning_report(
            vector(input_tokens=100_000), vector(), reasoning_output_tokens_total=41_200
        )
        self.assertEqual(reported["pareto_result"], "candidate_dominates")
        self.assertEqual(reported["reasoning_token_report"]["reasoning_output_tokens_total"], 41_200)
        self.assertFalse(reported["reasoning_token_report"]["decision_bearing"])

    def test_an_unobserved_reasoning_total_is_recorded_as_null_not_dropped(self) -> None:
        report = self.module.reasoning_token_report(None)
        self.assertIn("reasoning_output_tokens_total", report)
        self.assertIsNone(report["reasoning_output_tokens_total"])

    def test_cache_breakdowns_are_diagnostic_only_and_never_pareto_dimensions(self) -> None:
        for diagnostic_field in self.module.DIAGNOSTIC_ONLY_FIELDS:
            with self.subTest(field=diagnostic_field):
                self.assertNotIn(diagnostic_field, self.module.PARETO_DIMENSIONS)
        schema = load_json(ADDITIVE_SCHEMA_PATH)
        diagnostic = schema["$defs"]["cacheDiagnosticRecord"]  # type: ignore[index]
        for diagnostic_field in ("cache_write_tokens_by_ttl_class", "cache_read_tokens"):
            with self.subTest(field=diagnostic_field):
                self.assertIn(diagnostic_field, diagnostic["required"])
        self.assertFalse(diagnostic["properties"]["decision_bearing"]["const"])


class TerminalMappingTests(unittest.TestCase):
    """Each non-qualifying condition maps to its own closed member, and nothing
    anywhere forces a weighted ranking (FR-019, FR-024, SC-008)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_analysis_decision, "claude_analysis_decision is not importable")
        self.module = claude_analysis_decision

    def test_the_terminal_set_is_closed_and_carries_an_explicit_inconclusive(self) -> None:
        self.assertEqual(tuple(sorted(self.module.TERMINAL_STATES)), TERMINAL_STATES)
        schema = load_json(DECISION_SCHEMA_PATH)
        self.assertEqual(
            tuple(sorted(schema["properties"]["decision"]["enum"])), TERMINAL_STATES  # type: ignore[index]
        )
        self.assertIn("inconclusive", self.module.TERMINAL_STATES)

    def test_evidence_sufficient_but_bar_not_cleared_returns_no_qualification(self) -> None:
        for condition in ("failed_gate", "failed_floor", "failed_non_inferiority"):
            with self.subTest(condition=condition):
                state, reason = self.module.terminal_for(condition)
                self.assertEqual(state, "no_qualification")
                self.assertIn(reason, self.module.DECISION_REASONS)

    def test_evidence_that_could_not_decide_returns_inconclusive(self) -> None:
        for condition in (
            "pareto_tie",
            "mixed_dominance",
            "statistical_uncertainty",
            "incomplete_evidence",
            "rerun_cap_exhausted",
            "attrition_cap_exceeded",
            "unclassifiable_attrition",
            "unobservable_environment",
            "campaign_budget_exhausted",
        ):
            with self.subTest(condition=condition):
                state, reason = self.module.terminal_for(condition)
                self.assertEqual(state, "inconclusive")
                self.assertIn(reason, self.module.DECISION_REASONS)

    def test_binding_eligibility_and_reference_integrity_failures_return_invalid(self) -> None:
        for condition in (
            "binding_failure",
            "partition_not_eligible",
            "reference_integrity_failure",
        ):
            with self.subTest(condition=condition):
                state, reason = self.module.terminal_for(condition)
                self.assertEqual(state, "invalid")
                self.assertIn(reason, self.module.DECISION_REASONS)

    def test_a_completed_calibration_partition_returns_calibration_complete(self) -> None:
        state, reason = self.module.terminal_for("calibration_partition_complete")
        self.assertEqual(state, "calibration_complete")
        self.assertEqual(reason, "calibration_only")

    def test_a_campaign_stop_is_never_recorded_as_a_candidate_budget_outcome(self) -> None:
        # FR-019, FR-056: the campaign stopped early; the candidate did not fail
        # to clear the bar. The two must not collapse into one terminal member.
        campaign_state, _ = self.module.terminal_for("campaign_budget_exhausted")
        self.assertEqual(campaign_state, "inconclusive")
        self.assertTrue(self.module.retained_in_estimand("candidate_budget_exhausted"))
        self.assertEqual(self.module.estimand_acceptance("candidate_budget_exhausted"), 0)

    def test_every_mapped_reason_is_a_member_of_the_published_enum(self) -> None:
        schema = load_json(DECISION_SCHEMA_PATH)
        published = tuple(schema["properties"]["decision_reasons"]["items"]["enum"])  # type: ignore[index]
        self.assertEqual(tuple(sorted(self.module.DECISION_REASONS)), tuple(sorted(published)))
        for condition in self.module.TERMINAL_BY_CONDITION:
            with self.subTest(condition=condition):
                _, reason = self.module.terminal_for(condition)
                self.assertIn(reason, published)

    def test_an_unmapped_condition_is_refused_rather_than_defaulted(self) -> None:
        with self.assertRaises(self.module.AnalysisDecisionError):
            self.module.terminal_for("looked_fine_to_me")

    def test_the_worst_terminal_wins_when_several_conditions_fire(self) -> None:
        decision = self.module.resolve_terminal(
            ("failed_floor", "reference_integrity_failure"), qualification_eligible=True
        )
        self.assertEqual(decision.decision, "invalid")
        self.assertIn("floors_failed", decision.decision_reasons)
        self.assertIn("trace_reference_integrity_failure", decision.decision_reasons)

    def test_no_condition_at_all_on_an_eligible_partition_may_qualify(self) -> None:
        decision = self.module.resolve_terminal((), qualification_eligible=True)
        self.assertEqual(decision.decision, "qualified")
        self.assertEqual(decision.decision_reasons, ("none",))

    def test_qualified_is_unreachable_from_a_calibration_partition(self) -> None:
        decision = self.module.resolve_terminal((), qualification_eligible=False)
        self.assertEqual(decision.decision, "calibration_complete")
        self.assertNotEqual(decision.decision, "qualified")

    def test_the_contract_gates_qualified_behind_an_eligible_partition(self) -> None:
        schema = load_json(DECISION_SCHEMA_PATH)
        guard = schema["allOf"][0]  # type: ignore[index]
        self.assertEqual(guard["if"]["properties"]["decision"]["const"], "qualified")
        self.assertTrue(
            guard["then"]["properties"]["partition"]["properties"]["qualification_eligible"]["const"]
        )

    def test_no_weighted_ranking_or_scalar_score_may_appear_in_a_bundle(self) -> None:
        for offending in (
            {"scalar_score": 0.87},
            {"per_category_weights": {"semantic": 0.5, "resource": 0.5}},
            {"price_coefficient": 3.0},
            {"analysis_output": {"weighted_rank": 2}},
            {"composite_score": 12},
        ):
            with self.subTest(field=tuple(offending)[0]):
                findings = self.module.weighting_findings(offending)
                self.assertTrue(findings, offending)

    def test_diagnostic_price_context_is_not_mistaken_for_a_coefficient(self) -> None:
        self.assertEqual(
            self.module.weighting_findings(
                {"reported_limitations": {"published_price_context": "diagnostic only"}}
            ),
            (),
        )

    def test_no_final_route_policy_or_release_claim_may_be_created(self) -> None:
        for offending in (
            {"preferred_route_policy": {"route": "x"}},
            {"fallback_route_policy": {"route": "y"}},
            {"installed_default": "opus"},
            {"aggregate_identity": "claude"},
            {"release_claim": "ready"},
            {"cohort_decision": {"cohort": "car-007"}},
        ):
            with self.subTest(field=tuple(offending)[0]):
                findings = self.module.final_output_findings(offending)
                self.assertTrue(findings, offending)

    def test_a_clean_decision_bundle_trips_neither_guard(self) -> None:
        fixture = load_json(REPLAY_FIXTURE_PATH)
        for case in fixture["cases"]:  # type: ignore[index]
            with self.subTest(case=case["case_id"]):
                bundle = case["decision_bundle"]
                self.assertEqual(self.module.weighting_findings(bundle), ())
                self.assertEqual(self.module.final_output_findings(bundle), ())


class EstimandAndRerunTests(unittest.TestCase):
    """Assigned attempts stay in the estimand, and reruns are capped, complete-pair,
    and classified before either outcome is read (FR-020, FR-021, FR-056)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_analysis_decision, "claude_analysis_decision is not importable")
        self.module = claude_analysis_decision
        self.record = self.module.build_transient_classification_record(
            record_id="TCR-001",
            arm_blind_evidence_digest=digest_over({"evidence": "harness-timeout"}),
            recorded_at="2026-07-24T02:00:00Z",
        )

    def test_candidate_caused_outcomes_stay_in_the_estimand_at_acceptance_zero(self) -> None:
        self.assertEqual(
            tuple(sorted(self.module.ESTIMAND_RETAINED_CODES)), ESTIMAND_RETAINED_CODES
        )
        for code in ESTIMAND_RETAINED_CODES:
            with self.subTest(code=code):
                self.assertTrue(self.module.retained_in_estimand(code))
                self.assertEqual(self.module.estimand_acceptance(code), 0)

    def test_complete_case_filtering_is_pinned_off(self) -> None:
        self.assertFalse(self.module.COMPLETE_CASE_FILTERING)
        schema = load_json(PLAN_SCHEMA_PATH)
        attrition = schema["properties"]["attrition_policy"]  # type: ignore[index]
        self.assertFalse(attrition["properties"]["complete_case_filtering"]["const"])
        self.assertEqual(attrition["properties"]["unclassifiable_result"]["const"], "inconclusive")

    def test_a_campaign_ceiling_between_arms_is_an_infrastructure_truncation(self) -> None:
        stop = self.module.classify_campaign_ceiling_stop(
            assignment_id="CS-CAL-01-A0", arms_completed=1
        )
        self.assertEqual(stop.failure_plane, "infrastructure")
        self.assertEqual(stop.failure_code, "infrastructure_failure")
        self.assertNotEqual(stop.failure_code, "candidate_budget_exhausted")
        self.assertEqual(stop.pair_status, "incomplete")
        self.assertNotEqual(stop.pair_status, "one_armed")
        self.assertFalse(stop.one_arm_rerun_permitted)
        self.assertEqual(stop.terminal_condition, "campaign_budget_exhausted")

    def test_a_truncated_pair_is_never_completed_by_a_one_arm_rerun(self) -> None:
        verdict = self.module.grant_rerun(
            classification_record=self.record,
            arm_outcome_digest_timestamps=("2026-07-24T03:00:00Z", "2026-07-24T03:05:00Z"),
            cap=2,
            reruns_used=0,
            scope="single_arm",
        )
        self.assertFalse(verdict.granted)
        self.assertEqual(verdict.pair_result, "inconclusive")
        self.assertTrue(any("complete_pair" in finding for finding in verdict.findings), verdict)

    def test_a_rerun_within_the_cap_with_a_pre_outcome_record_is_granted(self) -> None:
        verdict = self.module.grant_rerun(
            classification_record=self.record,
            arm_outcome_digest_timestamps=("2026-07-24T03:00:00Z", "2026-07-24T03:05:00Z"),
            cap=2,
            reruns_used=1,
            scope="complete_pair",
        )
        self.assertTrue(verdict.granted, verdict)
        self.assertEqual(verdict.pair_result, "granted")

    def test_the_cap_counts_reruns_rather_than_attempts(self) -> None:
        # Two reruns of a paired comparison are four attempts. The cap is on the
        # reruns, so a cap of 2 is exhausted at the third rerun, not the third attempt.
        exhausted = self.module.grant_rerun(
            classification_record=self.record,
            arm_outcome_digest_timestamps=("2026-07-24T03:00:00Z",),
            cap=2,
            reruns_used=2,
            scope="complete_pair",
        )
        self.assertFalse(exhausted.granted)
        self.assertEqual(exhausted.pair_result, "inconclusive")
        self.assertEqual(exhausted.failure_condition, "rerun_cap_exhausted")
        self.assertEqual(self.module.attempts_for_reruns(2), 4)

    def test_a_rerun_with_no_classification_record_is_not_granted(self) -> None:
        verdict = self.module.grant_rerun(
            classification_record=None,
            arm_outcome_digest_timestamps=("2026-07-24T03:00:00Z",),
            cap=2,
            reruns_used=0,
            scope="complete_pair",
        )
        self.assertFalse(verdict.granted)
        self.assertEqual(verdict.pair_result, "inconclusive")

    def test_a_classification_record_post_dating_an_outcome_is_not_granted(self) -> None:
        late = self.module.build_transient_classification_record(
            record_id="TCR-002",
            arm_blind_evidence_digest=digest_over({"evidence": "harness-timeout"}),
            recorded_at="2026-07-24T04:00:00Z",
        )
        verdict = self.module.grant_rerun(
            classification_record=late,
            arm_outcome_digest_timestamps=("2026-07-24T03:00:00Z", "2026-07-24T03:05:00Z"),
            cap=2,
            reruns_used=0,
            scope="complete_pair",
        )
        self.assertFalse(verdict.granted)
        self.assertEqual(verdict.pair_result, "inconclusive")
        self.assertTrue(
            any("outcome" in finding for finding in verdict.findings), verdict
        )

    def test_an_offset_timestamp_is_compared_as_an_instant_rather_than_as_a_string(self) -> None:
        # 09:00 at UTC-06:00 is 15:00Z, three hours AFTER the 12:00Z outcome. As
        # strings "2026-07-01T09..." sorts below "2026-07-01T12...", so a textual
        # comparison reads a post-dated classification as arm-blind.
        offset = self.module.build_transient_classification_record(
            record_id="TCR-003",
            arm_blind_evidence_digest=digest_over({"evidence": "harness-timeout"}),
            recorded_at="2026-07-01T09:00:00-06:00",
        )
        verdict = self.module.grant_rerun(
            classification_record=offset,
            arm_outcome_digest_timestamps=("2026-07-01T12:00:00Z",),
            cap=2,
            reruns_used=0,
            scope="complete_pair",
        )
        self.assertFalse(verdict.granted, verdict)
        self.assertEqual(verdict.pair_result, "inconclusive")
        self.assertEqual(verdict.failure_condition, "incomplete_evidence")
        self.assertTrue(any("outcome" in finding for finding in verdict.findings), verdict)

    def test_an_offset_timestamp_that_truly_pre_dates_the_outcome_is_still_granted(self) -> None:
        early = self.module.build_transient_classification_record(
            record_id="TCR-004",
            arm_blind_evidence_digest=digest_over({"evidence": "harness-timeout"}),
            recorded_at="2026-07-01T09:00:00+06:00",
        )
        verdict = self.module.grant_rerun(
            classification_record=early,
            arm_outcome_digest_timestamps=("2026-07-01T12:00:00Z",),
            cap=2,
            reruns_used=0,
            scope="complete_pair",
        )
        self.assertTrue(verdict.granted, verdict)

    def test_an_unparseable_timestamp_on_either_side_refuses_the_rerun(self) -> None:
        corrupt = self.module.build_transient_classification_record(
            record_id="TCR-005",
            arm_blind_evidence_digest=digest_over({"evidence": "harness-timeout"}),
            recorded_at="0000-00-00T00:00:00Z",
        )
        unparseable_record = self.module.grant_rerun(
            classification_record=corrupt,
            arm_outcome_digest_timestamps=("2026-07-24T03:00:00Z",),
            cap=2,
            reruns_used=0,
            scope="complete_pair",
        )
        self.assertFalse(unparseable_record.granted, unparseable_record)
        unparseable_outcome = self.module.grant_rerun(
            classification_record=self.record,
            arm_outcome_digest_timestamps=("2026-07-24T99:00:00Z",),
            cap=2,
            reruns_used=0,
            scope="complete_pair",
        )
        self.assertFalse(unparseable_outcome.granted, unparseable_outcome)

    def test_zero_arm_outcome_timestamps_refuse_the_rerun(self) -> None:
        # With no arm outcome bound, the arm-blind precommitment has nothing to
        # be checked against, so the loop must not read as "no violation found".
        verdict = self.module.grant_rerun(
            classification_record=self.record,
            arm_outcome_digest_timestamps=(),
            cap=2,
            reruns_used=0,
            scope="complete_pair",
        )
        self.assertFalse(verdict.granted, verdict)
        self.assertEqual(verdict.pair_result, "inconclusive")
        self.assertEqual(verdict.failure_condition, "incomplete_evidence")

    def test_a_classification_record_carries_its_arm_blind_evidence_and_own_digest(self) -> None:
        self.assertEqual(self.module.CLASSIFICATION_TIMING, "arm_blind_before_outcome_read")
        for required_field in (
            "arm_blind_evidence_digest",
            "classification_digest",
            "recorded_at",
        ):
            with self.subTest(field=required_field):
                self.assertIn(required_field, self.record)
                self.assertIsNotNone(self.record[required_field])
        self.assertTrue(self.record["classification_digest"].startswith("sha256:"))

    def test_a_tampered_classification_record_is_refused(self) -> None:
        tampered = dict(self.record, arm_blind_evidence_digest=digest_over({"evidence": "other"}))
        verdict = self.module.grant_rerun(
            classification_record=tampered,
            arm_outcome_digest_timestamps=("2026-07-24T03:00:00Z",),
            cap=2,
            reruns_used=0,
            scope="complete_pair",
        )
        self.assertFalse(verdict.granted)

    def test_a_superseded_pair_is_retained_immutably_and_marked(self) -> None:
        pair = {"assignment_id": "CS-CAL-01-A0", "superseded": False, "complete": True}
        retained = self.module.supersede_pair(pair)
        self.assertTrue(retained["superseded"])
        self.assertFalse(pair["superseded"])  # the original record never moves
        self.assertEqual(retained["assignment_id"], pair["assignment_id"])

    def test_primary_statistics_use_exactly_one_terminal_complete_pair_per_assignment(
        self,
    ) -> None:
        pairs = (
            {"assignment_id": "A0", "superseded": True, "complete": True},
            {"assignment_id": "A0", "superseded": False, "complete": True},
            {"assignment_id": "A1", "superseded": False, "complete": True},
            {"assignment_id": "A2", "superseded": False, "complete": False},
        )
        terminal = self.module.terminal_complete_pairs(pairs)
        self.assertEqual(tuple(pair["assignment_id"] for pair in terminal), ("A0", "A1"))
        self.assertEqual(self.module.primary_statistics_findings(pairs), ())

    def test_two_live_complete_pairs_for_one_assignment_are_refused(self) -> None:
        pairs = (
            {"assignment_id": "A0", "superseded": False, "complete": True},
            {"assignment_id": "A0", "superseded": False, "complete": True},
        )
        findings = self.module.primary_statistics_findings(pairs)
        self.assertTrue(any("A0" in finding for finding in findings), findings)

    def test_exclusion_is_complete_pair_and_arm_symmetric(self) -> None:
        self.assertEqual(self.module.RERUN_SCOPE, "complete_pair")
        schema = load_json(PLAN_SCHEMA_PATH)
        rerun = schema["properties"]["rerun_policy"]  # type: ignore[index]
        self.assertEqual(rerun["properties"]["scope"]["const"], "complete_pair")
        self.assertEqual(
            rerun["properties"]["classification_timing"]["const"], "arm_blind_before_outcome_read"
        )


class GuardrailAndErrorControlTests(unittest.TestCase):
    """A guardrail is a complete comparison, multiplicity is three families plus a
    precondition, and looks are frozen (FR-050, FR-053, FR-054, FR-055)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_analysis_decision, "claude_analysis_decision is not importable")
        self.module = claude_analysis_decision
        self.plan = load_json(REPLAY_FIXTURE_PATH)["analysis_plan"]  # type: ignore[index]

    def test_every_guardrail_declares_the_full_comparison(self) -> None:
        method = self.plan["workload_manifest"]["guardrail_method"]
        for declared in self.module.GUARDRAIL_DECLARATION_FIELDS:
            with self.subTest(field=declared):
                self.assertIn(declared, method)
                self.assertIsNotNone(method[declared])
        self.assertEqual(
            self.module.guardrail_findings(
                method, non_inferiority_margins=self.plan["non_inferiority"]["margins"]
            ),
            (),
        )

    def test_a_guardrail_margin_reused_from_the_non_inferiority_margins_is_refused(self) -> None:
        method = copy.deepcopy(self.plan["workload_manifest"]["guardrail_method"])
        method["margin"] = list(self.plan["non_inferiority"]["margins"].values())[0]
        findings = self.module.guardrail_findings(
            method, non_inferiority_margins=self.plan["non_inferiority"]["margins"]
        )
        self.assertTrue(any("margin" in finding for finding in findings), findings)

    def test_a_silent_exclusion_missing_data_rule_is_refused(self) -> None:
        method = copy.deepcopy(self.plan["workload_manifest"]["guardrail_method"])
        method["missing_data_rule"] = "exclude_failed_attempts"
        findings = self.module.guardrail_findings(
            method, non_inferiority_margins=self.plan["non_inferiority"]["margins"]
        )
        self.assertTrue(any("missing_data_rule" in finding for finding in findings), findings)

    def test_a_guardrail_declared_in_one_of_the_three_multiplicity_families_is_refused(
        self,
    ) -> None:
        method = copy.deepcopy(self.plan["workload_manifest"]["guardrail_method"])
        method["multiplicity_family"]["family"] = "across_ladder_family"
        findings = self.module.guardrail_findings(
            method, non_inferiority_margins=self.plan["non_inferiority"]["margins"]
        )
        self.assertTrue(any("family" in finding for finding in findings), findings)
        self.assertEqual(self.module.GUARDRAIL_FAMILY, "guardrail")
        self.assertNotIn(self.module.GUARDRAIL_FAMILY, self.module.MULTIPLICITY_FAMILIES)

    def test_a_guardrail_breach_returns_no_qualification_and_is_never_traded_off(self) -> None:
        method = self.plan["workload_manifest"]["guardrail_method"]
        self.assertEqual(method["breach_result"], "no_qualification")
        self.assertFalse(method["decision_bearing"])
        breach = self.module.guardrail_breach("p95_duration_ms_max", observed=999_999, ceiling=1_000)
        self.assertEqual(breach.result, "no_qualification")
        self.assertFalse(breach.tradeable)

    def test_a_stratum_below_its_own_floor_returns_inconclusive(self) -> None:
        stratum = self.plan["workload_manifest"]["strata"][0]
        floor = stratum["stratum_minimum_unique_tasks"]
        below = self.module.guardrail_admissibility(stratum, observed_unique_tasks=floor - 1)
        self.assertEqual(below.result, "inconclusive")
        self.assertFalse(below.admissible)
        self.assertTrue(below.shortfall_reported)
        at_floor = self.module.guardrail_admissibility(stratum, observed_unique_tasks=floor)
        self.assertTrue(at_floor.admissible)
        self.assertEqual(at_floor.result, "admissible")

    def test_a_manifest_wide_floor_never_substitutes_for_the_per_stratum_floor(self) -> None:
        manifest = self.plan["workload_manifest"]
        for stratum in manifest["strata"]:
            with self.subTest(stratum=stratum["stratum_id"]):
                self.assertIn("stratum_minimum_unique_tasks", stratum)
                self.assertIn("stratum_sample_size", stratum)
        thin = copy.deepcopy(manifest["strata"][0])
        thin["stratum_minimum_unique_tasks"] = manifest["minimum_unique_tasks"] + 8
        below = self.module.guardrail_admissibility(
            thin, observed_unique_tasks=manifest["minimum_unique_tasks"]
        )
        self.assertFalse(below.admissible)

    def test_the_multiplicity_declaration_addresses_three_families_separately(self) -> None:
        declaration = self.plan["non_inferiority"]["multiplicity_declaration"]
        self.assertEqual(tuple(self.module.MULTIPLICITY_FAMILIES), (
            "conjunctive_family",
            "pareto_disjunctive_family",
            "across_ladder_family",
        ))
        for family in self.module.MULTIPLICITY_FAMILIES:
            with self.subTest(family=family):
                self.assertIn(family, declaration)
                self.assertTrue(declaration[family]["adjustment"])
                self.assertTrue(declaration[family]["rationale"])
        self.assertEqual(self.module.multiplicity_findings(declaration), ())

    def test_the_conjunctive_stage_needs_no_adjustment_and_says_why(self) -> None:
        declaration = self.plan["non_inferiority"]["multiplicity_declaration"]
        self.assertEqual(declaration["conjunctive_family"]["adjustment"], "none_required")

    def test_the_pareto_disjunctive_half_must_state_how_it_is_controlled(self) -> None:
        declaration = copy.deepcopy(self.plan["non_inferiority"]["multiplicity_declaration"])
        declaration["pareto_disjunctive_family"]["adjustment"] = "none_required"
        findings = self.module.multiplicity_findings(declaration)
        self.assertTrue(
            any("pareto_disjunctive_family" in finding for finding in findings), findings
        )

    def test_cluster_adjustment_is_a_precondition_not_a_multiplicity_control(self) -> None:
        declaration = self.plan["non_inferiority"]["multiplicity_declaration"]
        self.assertTrue(declaration["cluster_adjustment_is_precondition"])
        relaxed = copy.deepcopy(declaration)
        relaxed["cluster_adjustment_is_precondition"] = False
        self.assertTrue(self.module.multiplicity_findings(relaxed))
        control = copy.deepcopy(declaration)
        control["across_ladder_family"]["adjustment"] = "cluster_adjusted_variance"
        findings = self.module.multiplicity_findings(control)
        self.assertTrue(any("precondition" in finding for finding in findings), findings)

    def test_the_plan_declares_alpha_power_sample_sizes_and_assumptions(self) -> None:
        non_inferiority = self.plan["non_inferiority"]
        for declared in ("alpha", "power", "sample_sizes", "sample_size_assumptions",
                         "confidence_level", "cluster_unit", "cluster_adjustment", "margins"):
            with self.subTest(field=declared):
                self.assertIn(declared, non_inferiority)
                self.assertTrue(non_inferiority[declared])

    def test_racing_and_futility_record_every_planned_look(self) -> None:
        for policy_name in ("racing_policy", "futility_policy"):
            with self.subTest(policy=policy_name):
                policy = self.plan[policy_name]
                looks = policy["interim_looks"]
                self.assertEqual(looks["count"], len(looks["information_fractions"]))
                self.assertEqual(
                    looks["information_fractions"], sorted(set(looks["information_fractions"]))
                )
                self.assertTrue(policy["boundary"]["type"])
                self.assertTrue(policy["boundary"]["rationale"])
                self.assertTrue(policy["look_schedule_frozen"])
                self.assertTrue(policy["early_stop_biases_estimate"])
                self.assertEqual(policy["stop_scope"], "complete_pair")
                self.assertEqual(self.module.interim_look_findings(policy), ())

    def test_futility_declares_whether_its_boundary_binds(self) -> None:
        self.assertIn(self.plan["futility_policy"]["boundary_binding"], ("binding", "non_binding"))
        unstated = copy.deepcopy(self.plan["futility_policy"])
        del unstated["boundary_binding"]
        findings = self.module.interim_look_findings(unstated, futility=True)
        self.assertTrue(any("boundary_binding" in finding for finding in findings), findings)

    def test_a_look_count_disagreeing_with_its_schedule_is_refused(self) -> None:
        broken = copy.deepcopy(self.plan["racing_policy"])
        broken["interim_looks"]["count"] = broken["interim_looks"]["count"] + 1
        findings = self.module.interim_look_findings(broken)
        self.assertTrue(any("count" in finding for finding in findings), findings)

    def test_a_look_added_after_an_outcome_is_visible_invalidates_the_declaration(self) -> None:
        frozen = self.plan["racing_policy"]
        revised = copy.deepcopy(frozen)
        revised["interim_looks"]["information_fractions"].append(0.9)
        revised["interim_looks"]["count"] += 1
        findings = self.module.look_schedule_findings(frozen, revised, outcome_visible=True)
        self.assertTrue(findings)
        self.assertTrue(any("invalidat" in finding for finding in findings), findings)
        self.assertEqual(
            self.module.look_schedule_findings(frozen, revised, outcome_visible=False), ()
        )

    def test_a_look_moved_or_repeated_after_an_outcome_is_visible_invalidates_it(self) -> None:
        frozen = self.plan["racing_policy"]
        for mutation in ("moved", "repeated"):
            with self.subTest(mutation=mutation):
                revised = copy.deepcopy(frozen)
                fractions = revised["interim_looks"]["information_fractions"]
                if mutation == "moved":
                    fractions[0] = round(fractions[0] + 0.05, 4)
                else:
                    fractions.append(fractions[0])
                    revised["interim_looks"]["count"] += 1
                self.assertTrue(
                    self.module.look_schedule_findings(frozen, revised, outcome_visible=True)
                )

    def test_a_stopped_comparison_is_reported_as_stopped_not_completed(self) -> None:
        report = self.module.stop_report(reason="futility_boundary_crossed", stop_scope="complete_pair")
        self.assertEqual(report["reported_as"], "stopped")
        self.assertNotEqual(report["reported_as"], "completed")
        self.assertTrue(report["early_stop_biases_estimate"])
        self.assertEqual(report["stopping_reason"], "futility_boundary_crossed")
        self.assertEqual(report["stop_scope"], "complete_pair")

    def test_a_single_arm_stop_is_refused(self) -> None:
        with self.assertRaises(self.module.AnalysisDecisionError):
            self.module.stop_report(reason="futility_boundary_crossed", stop_scope="single_arm")


class ReplayAndNonPoolingTests(unittest.TestCase):
    """Replay reconstructs the same terminal decision byte for byte, and a changed
    ceiling produces a new plan whose outcomes are never pooled (SC-011, FR-056)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_analysis_decision, "claude_analysis_decision is not importable")
        self.module = claude_analysis_decision
        self.fixture = self.module.load_replay_fixture()

    def test_the_fixture_is_bounded_in_count_and_size(self) -> None:
        # FR-057: suite cost must not scale with accumulated campaign evidence.
        self.assertLessEqual(len(self.fixture["cases"]), 8)
        self.assertLess(self.module.REPLAY_FIXTURE_PATH.stat().st_size, 65_536)

    def test_replay_reconstructs_byte_identical_decision_bundles(self) -> None:
        for case in self.fixture["cases"]:
            with self.subTest(case=case["case_id"]):
                replayed = self.module.replay_decision(case)
                self.assertEqual(
                    canonical_json(replayed), canonical_json(case["decision_bundle"])
                )

    def test_replay_is_stable_across_repeated_runs(self) -> None:
        for case in self.fixture["cases"]:
            with self.subTest(case=case["case_id"]):
                first = canonical_json(self.module.replay_decision(case))
                second = canonical_json(self.module.replay_decision(copy.deepcopy(case)))
                self.assertEqual(first, second)

    def test_every_case_reconstructs_its_expected_terminal_member(self) -> None:
        for case in self.fixture["cases"]:
            with self.subTest(case=case["case_id"]):
                replayed = self.module.replay_decision(case)
                self.assertEqual(replayed["decision"], case["expected_decision"])
                self.assertIn(replayed["decision"], TERMINAL_STATES)

    def test_the_fixture_exercises_every_terminal_member_reachable_here(self) -> None:
        observed = {case["expected_decision"] for case in self.fixture["cases"]}
        self.assertEqual(
            observed,
            {"calibration_complete", "no_qualification", "inconclusive", "invalid"},
        )
        self.assertNotIn("qualified", observed)

    def test_no_case_reaches_qualified_from_a_calibration_partition(self) -> None:
        for case in self.fixture["cases"]:
            with self.subTest(case=case["case_id"]):
                self.assertFalse(case["decision_bundle"]["partition"]["qualification_eligible"])
                self.assertNotEqual(case["decision_bundle"]["decision"], "qualified")

    def test_every_replayed_bundle_records_the_full_ordered_ladder(self) -> None:
        for case in self.fixture["cases"]:
            with self.subTest(case=case["case_id"]):
                replayed = self.module.replay_decision(case)
                gates = tuple(entry["gate"] for entry in replayed["ordered_gate_results"])
                self.assertEqual(gates, LADDER_GATES)

    def test_every_replayed_bundle_reports_its_bounded_limitations(self) -> None:
        for case in self.fixture["cases"]:
            with self.subTest(case=case["case_id"]):
                limitations = self.module.replay_decision(case)["reported_limitations"]
                self.assertTrue(limitations["reasoning_tokens_excluded_from_dominance"])
                self.assertTrue(limitations["blinding_bounded"])
                self.assertIn("reasoning_output_tokens_total", limitations)

    def test_completeness_tracks_evidence_shortfall_and_untrustworthy_records(self) -> None:
        # `complete` is an evidence claim, so it is false whenever an evidence
        # shortfall fired AND whenever the record itself is invalid — a bundle whose
        # bindings failed has no analysis for completeness to describe.
        by_case = {case["case_id"]: case for case in self.fixture["cases"]}
        for case_id, expected in (
            ("calibration_pair_completes_cleanly", True),
            ("absolute_floor_not_cleared", True),
            ("terminal_state_difference_is_mixed_not_better", True),
            ("campaign_ceiling_truncated_the_pair", False),
            ("rerun_cap_exhausted_before_complete_evidence", False),
            ("dangling_trace_reference_blocks_the_bundle", False),
        ):
            with self.subTest(case=case_id):
                replayed = self.module.replay_decision(by_case[case_id])
                self.assertEqual(replayed["analysis_output"]["complete"], expected)
        for condition in self.module.EVIDENCE_SHORTFALL_CONDITIONS:
            with self.subTest(condition=condition):
                self.assertEqual(self.module.terminal_for(condition)[0], "inconclusive")

    def test_a_tampered_bundle_digest_no_longer_replays(self) -> None:
        case = copy.deepcopy(self.fixture["cases"][0])
        case["decision_bundle"]["decision_bundle_digest"] = digest_over({"tampered": True})
        replayed = self.module.replay_decision(case)
        self.assertNotEqual(canonical_json(replayed), canonical_json(case["decision_bundle"]))

    def test_a_changed_ceiling_after_freeze_creates_a_new_versioned_plan(self) -> None:
        plan = self.fixture["analysis_plan"]
        superseded = self.module.supersede_analysis_plan(
            plan, campaign_budget=dict(plan["campaign_budget"], max_attempts=96)
        )
        self.assertNotEqual(superseded.plan["analysis_plan_id"], plan["analysis_plan_id"])
        self.assertNotEqual(superseded.plan["analysis_plan_digest"], plan["analysis_plan_digest"])
        self.assertEqual(superseded.supersedes["id"], plan["analysis_plan_id"])
        # FR-056: non-pooling is carried by the {id, digest} binding every decision
        # bundle already holds, not by a new field. The plan contract is closed
        # under additionalProperties:false, so the new plan gains no member.
        self.assertNotIn("supersedes", superseded.plan)
        self.assertEqual(tuple(sorted(superseded.plan)), tuple(sorted(plan)))

    def test_outcomes_under_a_superseded_plan_are_never_pooled_with_the_new_one(self) -> None:
        plan = self.fixture["analysis_plan"]
        superseded = self.module.supersede_analysis_plan(
            plan, quality_floors=dict(plan["quality_floors"], semantic_minimum=0.99)
        )
        original = {"id": plan["analysis_plan_id"], "digest": plan["analysis_plan_digest"]}
        replacement = {
            "id": superseded.plan["analysis_plan_id"],
            "digest": superseded.plan["analysis_plan_digest"],
        }
        self.assertFalse(self.module.pooling_permitted(original, replacement))
        self.assertTrue(self.module.pooling_permitted(original, dict(original)))

    def test_the_frozen_plan_records_its_pre_cohort_outcome_absence(self) -> None:
        plan = self.fixture["analysis_plan"]
        self.assertEqual(plan["status"], "frozen")
        self.assertTrue(plan["pre_cohort_outcome_absence_digest"].startswith("sha256:"))
        self.assertIn("calibration_binding", plan)

    def test_the_replay_fixture_carries_no_operator_only_evidence(self) -> None:
        text = self.module.REPLAY_FIXTURE_PATH.read_text(encoding="utf-8")
        for forbidden in ("/Users/", "/home/", "api_key", "authorization", "transcript"):
            with self.subTest(pattern=forbidden):
                self.assertNotIn(forbidden, text)


def decision_bundle(module: object, **overrides: object) -> dict[str, object]:
    """One clean calibration decision bundle, assembled through the builder."""
    fields: dict[str, object] = {
        "decision_bundle_id": "CAR-003-DECISION-WRITE-GUARD-001",
        "partition": {
            "partition_id": "CAR-003-CAL-01",
            "partition_type": "calibration",
            "qualification_eligible": False,
        },
        "comparison_set_binding": {"id": "CS-CAL-01", "digest": digest_over({"comparison_set": 1})},
        "assignment_bindings": [{"id": "CS-CAL-01-A0", "digest": digest_over({"assignment": 0})}],
        "score_bundle_bindings": [{"id": "SB-CAL-01-A0", "digest": digest_over({"score_bundle": 0})}],
        # FR-037: this is a calibration partition, so it binds the protocol. It
        # cannot bind a plan that does not freeze until calibration finishes.
        "calibration_protocol_binding": {
            "id": "CAL-PROTOCOL-01",
            "digest": digest_over({"protocol": 1}),
        },
        "analysis_output_id": "AO-CAL-01",
        "ordered_gate_results": list(
            module.evaluate_ladder({gate: "pass" for gate in module.LADDER_GATES})  # type: ignore[attr-defined]
        ),
        "floor_result": "pass",
        "non_inferiority_result": "pass",
        "pareto_result": "candidate_dominates",
        "complete": True,
        "decision": "calibration_complete",
        "decision_reasons": ["calibration_only"],
        "reasoning_output_tokens_total": 800,
        "provenance_inference_count": 0,
        "evidence_refs": [digest_over({"evidence": "gate-log"})],
    }
    fields.update(overrides)
    return module.build_decision_bundle(**fields)  # type: ignore[attr-defined]


def calibration_partition(**extra: object) -> dict[str, object]:
    partition: dict[str, object] = {
        "partition_id": "CAR-003-CAL-01",
        "partition_type": "calibration",
        "qualification_eligible": False,
    }
    partition.update(extra)
    return partition


class DecisionBundleWriteGuardTests(unittest.TestCase):
    """The no-weighting and no-final-output guards run on the write path, before
    the bundle is sealed and digested. A guard that only exists as a reader
    cannot stop a caller-supplied weight from reaching sealed evidence
    (FR-019, FR-024)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_analysis_decision, "claude_analysis_decision is not importable")
        self.module = claude_analysis_decision

    def test_a_clean_bundle_still_seals_against_its_own_digest(self) -> None:
        bundle = decision_bundle(self.module)
        self.assertEqual(self.module.weighting_findings(bundle), ())
        self.assertEqual(self.module.final_output_findings(bundle), ())
        self.assertEqual(
            bundle["decision_bundle_digest"],
            digest_over(
                {key: value for key, value in bundle.items() if key != "decision_bundle_digest"}
            ),
        )

    def test_a_weighting_key_in_a_caller_supplied_mapping_is_refused_before_sealing(self) -> None:
        provocations = {
            "partition": {"partition": calibration_partition(criterion_weight=0.4)},
            "binding": {
                "analysis_plan_binding": {
                    "id": "PLAN-01",
                    "digest": digest_over({"plan": 1}),
                    "price_coefficient": 3.0,
                }
            },
            "nested_binding": {
                "assignment_bindings": [
                    {
                        "id": "CS-CAL-01-A0",
                        "digest": digest_over({"assignment": 0}),
                        "composite_score": 0.91,
                    }
                ]
            },
            "ranking": {"partition": calibration_partition(ranking=["opus", "sonnet"])},
            "scalar_score": {"partition": calibration_partition(scalar_score=7.25)},
        }
        for label, overrides in sorted(provocations.items()):
            with self.subTest(surface=label):
                with self.assertRaises(self.module.AnalysisDecisionError):
                    decision_bundle(self.module, **overrides)

    def test_a_forbidden_final_output_key_is_refused_before_sealing(self) -> None:
        for key in self.module.FORBIDDEN_OUTPUT_KEYS:
            with self.subTest(forbidden=key):
                with self.assertRaises(self.module.AnalysisDecisionError):
                    decision_bundle(self.module, partition=calibration_partition(**{key: "opus"}))


def schema_findings(instance: object, node: object, defs: dict, path: str = "") -> list[str]:
    """Standard-library validation against the closed analysis-plan contract.

    The keyword set is exactly the one the contract uses. Same fail-closed idiom
    as the CAR-002 trace validator, kept local because that module is bound to a
    different shipped contract.
    """
    found: list[str] = []
    if not isinstance(node, dict):
        return found
    if "$ref" in node:
        ref = str(node["$ref"])
        name = ref.rsplit("/", 1)[-1]
        if name not in defs:
            return [f"{path or '<root>'}: unknown $def {name!r}"]
        return schema_findings(instance, defs[name], defs, path)
    where = path or "<root>"
    if "const" in node:
        return [] if instance == node["const"] else [f"{where}: expected {node['const']!r}"]
    if "enum" in node:
        return [] if instance in node["enum"] else [f"{where}: {instance!r} not in enum"]
    declared = node.get("type")
    if declared is not None:
        by_name = {
            "object": isinstance(instance, dict),
            "array": isinstance(instance, list),
            "string": isinstance(instance, str),
            "boolean": isinstance(instance, bool),
            "integer": isinstance(instance, int) and not isinstance(instance, bool),
            "number": isinstance(instance, (int, float)) and not isinstance(instance, bool),
            "null": instance is None,
        }
        # JSON Schema allows a union, e.g. {"type": ["integer", "null"]}, and it
        # is satisfied when ANY member matches. Looking the declaration up by
        # str() collapsed a list to "['integer', 'null']", which is no key at
        # all, so every union-typed field was reported as a type violation no
        # matter what it held.
        candidates = declared if isinstance(declared, list) else [declared]
        if not any(by_name.get(str(name)) is True for name in candidates):
            return [f"{where}: expected type {declared!r}, got {type(instance).__name__}"]
    if isinstance(instance, str):
        minimum_length = node.get("minLength")
        if minimum_length is not None and len(instance) < int(minimum_length):
            found.append(f"{where}: shorter than minLength {minimum_length}")
        pattern = node.get("pattern")
        if pattern is not None and not re.fullmatch(str(pattern), instance):
            found.append(f"{where}: {instance!r} does not match {pattern}")
        if node.get("format") == "date-time" and not instance.endswith("Z"):
            found.append(f"{where}: {instance!r} is not a Z-suffixed UTC instant")
    elif isinstance(instance, bool):
        pass
    elif isinstance(instance, (int, float)):
        for keyword, ok in (
            ("minimum", lambda bound: instance >= bound),
            ("maximum", lambda bound: instance <= bound),
            ("exclusiveMinimum", lambda bound: instance > bound),
            ("exclusiveMaximum", lambda bound: instance < bound),
        ):
            bound = node.get(keyword)
            if bound is not None and not ok(bound):
                found.append(f"{where}: {instance!r} violates {keyword} {bound}")
    elif isinstance(instance, list):
        for keyword, ok in (
            ("minItems", lambda bound: len(instance) >= bound),
            ("maxItems", lambda bound: len(instance) <= bound),
        ):
            bound = node.get(keyword)
            if bound is not None and not ok(bound):
                found.append(f"{where}: {len(instance)} items violates {keyword} {bound}")
        if node.get("uniqueItems") and len(instance) != len({canonical_json(x) for x in instance}):
            found.append(f"{where}: items are not unique")
        items = node.get("items")
        if items is not None:
            for index, element in enumerate(instance):
                found.extend(schema_findings(element, items, defs, f"{where}[{index}]"))
    elif isinstance(instance, dict):
        properties = node.get("properties", {})
        minimum_properties = node.get("minProperties")
        if minimum_properties is not None and len(instance) < int(minimum_properties):
            found.append(f"{where}: fewer than minProperties {minimum_properties}")
        missing = sorted(set(node.get("required", ())) - set(instance))
        if missing:
            found.append(f"{where}: missing required keys {missing}")
        extra_schema = node.get("additionalProperties")
        if extra_schema is False:
            unexpected = sorted(set(instance) - set(properties))
            if unexpected:
                found.append(f"{where}: unexpected keys {unexpected}")
        names = node.get("propertyNames")
        if isinstance(names, dict) and "enum" in names:
            outside = sorted(set(instance) - set(names["enum"]))
            if outside:
                found.append(f"{where}: keys outside the closed key space {outside}")
        for key, value in instance.items():
            child = f"{where}.{key}" if path else str(key)
            if key in properties:
                found.extend(schema_findings(value, properties[key], defs, child))
            elif isinstance(extra_schema, dict):
                found.extend(schema_findings(value, extra_schema, defs, child))
    return found


def pre_cohort_absence_record(pilot: dict) -> dict[str, object]:
    """The SC-012 attestation the frozen plan digests.

    Reproducible from committed evidence alone: the cohort specs checked, the
    empty observation, and the calibration run's own identity and repository
    state. Nothing here is authored by hand, so the digest cannot be back-fitted.
    """
    return {
        "record_kind": "pre_cohort_outcome_absence",
        "schema_version": "1.0.0",
        "checked_cohort_specs": list(COHORT_SPECS),
        "outcome_bearing_cohort_artifacts": [],
        "qualification_eligible_partitions_consumed": [],
        "calibration_pilot_id": pilot["pilot_id"],
        "calibration_pilot_digest": pilot["pilot_digest"],
        "repository_revision": pilot["repository_revision"],
        "repository_tree_digest": pilot["repository_tree_digest"],
    }


def required_pairs(
    *, sd: float, margin: float, alpha: float, power: float, clusters: int, icc: float
) -> tuple[int, int]:
    """Paired non-inferiority pairs, before and after cluster inflation.

    The clustered size is the fixed point of ``n = n0 * (1 + (n/R - 1) * icc)``,
    which is why the attainable effective sample size is capped at ``R / icc``
    however many pairs are run.
    """
    z = NormalDist().inv_cdf(1 - alpha) + NormalDist().inv_cdf(power)
    unclustered = z * z * sd * sd / (margin * margin)
    denominator = 1 - unclustered * icc / clusters
    if denominator <= 0:
        raise AssertionError("no achievable sample size reaches the declared power")
    return math.ceil(unclustered), math.ceil(unclustered * (1 - icc) / denominator)


class FrozenAnalysisPlanTests(unittest.TestCase):
    """The authored, frozen numeric plan (FR-023, FR-038, FR-050, FR-053…FR-055).

    Unlike the synthetic replay plan, this one is authoritative: its margins,
    sample sizes, guardrails, and budget govern every qualification-eligible
    campaign. Each number is checked against the calibration evidence it claims
    to come from, and every input the pilot could not measure has to say so.
    """

    def setUp(self) -> None:
        self.assertTrue(FROZEN_PLAN_PATH.is_file(), f"{FROZEN_PLAN_PATH.name} is not authored")
        self.plan = load_json(FROZEN_PLAN_PATH)
        self.pilot = load_json(CALIBRATION_PILOT_PATH)
        self.assumptions = self.plan["non_inferiority"]["sample_size_assumptions"]

    def test_the_frozen_plan_validates_against_its_published_contract(self) -> None:
        schema = load_json(PLAN_SCHEMA_PATH)
        findings = schema_findings(self.plan, schema, schema.get("$defs", {}))
        self.assertEqual(findings, [], findings)
        self.assertEqual(self.plan["status"], "frozen")

    def test_the_frozen_plan_is_sealed_against_its_own_digest(self) -> None:
        for record, field in (
            (self.plan, "analysis_plan_digest"),
            (self.plan["workload_manifest"], "manifest_digest"),
            (self.plan["cache_policy"], "policy_digest"),
        ):
            with self.subTest(field=field):
                sealed = {key: value for key, value in record.items() if key != field}
                self.assertEqual(record[field], digest_over(sealed))

    def test_the_plan_binds_the_calibration_protocol_it_was_derived_from(self) -> None:
        protocol = self.pilot["calibration_protocol"]
        self.assertEqual(
            self.plan["calibration_protocol_binding"],
            {"id": protocol["calibration_protocol_id"], "digest": protocol["protocol_digest"]},
        )
        # FR-037: the protocol carries none of the numbers the plan freezes, which
        # is the whole reason a calibration pair binds it instead of the plan.
        for carried in ("carries_margins", "carries_sample_sizes", "carries_terminal_thresholds"):
            self.assertFalse(protocol[carried], carried)

    def test_the_plan_binds_the_calibration_run_its_numbers_came_from(self) -> None:
        """FR-038: the protocol proves the design; completion proves the execution.

        Binding only the protocol let the plan claim derivation from a design
        without naming the run that produced its variance estimates. The pilot
        identity was committed only incidentally, inside the SC-012 pre-cohort
        absence attestation, whose purpose is proving no cohort outcome existed.
        """
        completion = load_json(RESEARCH_ROOT / "claude-car-003-calibration-completion.json")
        binding = self.plan["calibration_completion_binding"]

        self.assertEqual(binding["id"], completion["calibration_completion_id"])
        self.assertEqual(binding["digest"], completion["calibration_completion_digest"])
        self.assertEqual(
            binding["digest"],
            digest_over(
                {k: v for k, v in completion.items() if k != "calibration_completion_digest"}
            ),
            "the completion record does not seal against the digest the plan binds",
        )
        # It must attest to the pilot the plan was actually derived from, and to
        # the same protocol the plan binds separately.
        self.assertIn(
            {"id": self.pilot["pilot_id"], "digest": self.pilot["pilot_digest"]},
            completion["calibration_evidence_bindings"],
        )
        self.assertEqual(
            completion["calibration_protocol_binding"], self.plan["calibration_protocol_binding"]
        )

    def test_the_completion_record_proves_calibration_preceded_the_plan(self) -> None:
        completion = load_json(RESEARCH_ROOT / "claude-car-003-calibration-completion.json")
        provenance = completion["completion_provenance"]

        self.assertIs(provenance["calibration_execution_complete"], True)
        # Both pinned false by contract: no plan exists while calibration runs,
        # and no cohort outcome may precede it.
        self.assertIs(provenance["analysis_plan_observed"], False)
        self.assertIs(provenance["cohort_outcome_observed"], False)
        self.assertEqual(completion["partition"]["partition_type"], "calibration")
        self.assertIs(completion["partition"]["qualification_eligible"], False)
        # Every bundle the completion attests to is a real pilot comparison set.
        pilot_sets = {
            entry["decision_bundle"]["comparison_set_binding"]["id"]
            for entry in self.pilot["decision_bundles"]
        }
        self.assertEqual(
            {b["id"] for b in completion["comparison_set_bindings"]}, pilot_sets
        )

    def test_the_completion_record_validates_against_its_contract(self) -> None:
        completion = load_json(RESEARCH_ROOT / "claude-car-003-calibration-completion.json")
        schema = load_json(CONTRACT_ROOT / "calibration-completion.schema.json")
        self.assertEqual(
            schema_findings(completion, schema, schema.get("$defs", {})), []
        )

    def test_the_independent_review_absence_is_recorded_not_fabricated(self) -> None:
        """CAR-003 scored calibration with deterministic rubric scorers.

        No independent review artifact exists to bind, so the field is null
        rather than back-filled. G56R-003's protocol carries scorer, rubric,
        adjudicator, cache-policy, and independent-review bindings that CAR-003's
        leaner anti-cycle protocol does not; closing that shape gap is CAR-012.
        """
        completion = load_json(RESEARCH_ROOT / "claude-car-003-calibration-completion.json")
        self.assertIsNone(completion["completion_provenance"]["independent_review_binding"])
        self.assertNotIn("independent_review_binding", self.pilot["calibration_protocol"])

    def test_every_sample_size_derives_from_a_measured_paired_difference(self) -> None:
        measured = self.pilot["variance_estimates"]["paired_within_task_difference"]
        non_inferiority = self.plan["non_inferiority"]
        for endpoint, declared in self.assumptions["endpoints"].items():
            with self.subTest(endpoint=endpoint):
                estimate = measured[declared["pilot_estimate_field"]]
                self.assertEqual(declared["paired_difference_sd"], estimate["sd"])
                self.assertEqual(declared["paired_difference_pairs"], estimate["n"])
                unclustered, clustered = required_pairs(
                    sd=estimate["sd"],
                    margin=non_inferiority["margins"][endpoint],
                    alpha=non_inferiority["alpha"],
                    power=non_inferiority["power"],
                    clusters=self.assumptions["cluster_count"],
                    icc=self.assumptions["assumed_intracluster_correlation"],
                )
                self.assertEqual(declared["n_unclustered_pairs"], unclustered)
                self.assertEqual(declared["n_pairs"], clustered)
                self.assertEqual(non_inferiority["sample_sizes"][endpoint], clustered)

    def test_the_cluster_count_is_the_corpus_role_count_not_an_estimate(self) -> None:
        corpus = load_json(
            TEST_ROOT / "layer6-efficiency" / "fixtures" / "car-003-role-corpus.json"
        )
        self.assertEqual(self.plan["non_inferiority"]["cluster_unit"], "role")
        self.assertEqual(self.assumptions["cluster_count"], len(corpus["roles"]))

    def test_the_per_stratum_task_floor_supports_the_percentile_it_claims(self) -> None:
        manifest = self.plan["workload_manifest"]
        confidence = manifest["guardrail_method"]["confidence_method"]["confidence_level"]
        # A distribution-free upper bound on the p95 from the largest order
        # statistic reaches its nominal level only once 1 - 0.95**n >= confidence.
        floor = math.ceil(math.log(1 - confidence) / math.log(0.95))
        self.assertGreater(1 - 0.95**floor, confidence)
        self.assertLessEqual(1 - 0.95 ** (floor - 1), confidence)
        for stratum in manifest["strata"]:
            with self.subTest(stratum=stratum["stratum_id"]):
                self.assertGreaterEqual(stratum["stratum_minimum_unique_tasks"], floor)
                self.assertGreaterEqual(stratum["stratum_sample_size"], floor)
                self.assertFalse(stratum["membership_rule"]["derived_from_realized_outcomes"])

    def test_the_declared_error_control_returns_no_findings(self) -> None:
        module = claude_analysis_decision
        self.assertIsNotNone(module, "claude_analysis_decision is not importable")
        manifest = self.plan["workload_manifest"]
        non_inferiority = self.plan["non_inferiority"]
        self.assertEqual(
            module.guardrail_findings(
                manifest["guardrail_method"],
                non_inferiority_margins=non_inferiority["margins"],
            ),
            (),
        )
        self.assertEqual(
            module.multiplicity_findings(non_inferiority["multiplicity_declaration"]), ()
        )
        self.assertEqual(module.interim_look_findings(self.plan["racing_policy"]), ())
        self.assertEqual(
            module.interim_look_findings(self.plan["futility_policy"], futility=True), ()
        )

    def test_the_campaign_budget_is_authoritative_over_the_calibration_budget(self) -> None:
        policy = claude_experiment_policy
        self.assertIsNotNone(policy, "claude_experiment_policy is not importable")
        plan_budget = self.plan["campaign_budget"]
        pilot_budget = self.pilot["experiment_policy"]["budget"]
        self.assertFalse(self.pilot["experiment_policy"]["partition"]["qualification_eligible"])
        tighter = policy.budget_verdict(
            policy_budget=pilot_budget, plan_budget=plan_budget, qualification_eligible=False
        )
        self.assertTrue(tighter.ok, tighter.findings)
        # The same budget on a qualification-eligible partition must be equal, not
        # merely tighter: a campaign that may spend less is a different estimand.
        unequal = policy.budget_verdict(
            policy_budget=pilot_budget, plan_budget=plan_budget, qualification_eligible=True
        )
        self.assertFalse(unequal.ok)
        self.assertEqual(unequal.failure_plane, "partition")
        equal = policy.budget_verdict(
            policy_budget=plan_budget, plan_budget=plan_budget, qualification_eligible=True
        )
        self.assertTrue(equal.ok, equal.findings)

    def test_the_decision_vector_carries_no_weighting_and_no_scalar_score(self) -> None:
        module = claude_analysis_decision
        self.assertIsNotNone(module, "claude_analysis_decision is not importable")
        pareto = self.plan["pareto_policy"]
        self.assertEqual(tuple(sorted(pareto["dimensions"])), PARETO_DIMENSIONS)
        self.assertTrue(pareto["weights_prohibited"])
        self.assertEqual(pareto["mixed_or_tied_result"], "inconclusive")
        self.assertFalse(pareto["reasoning_tokens_decision_bearing"])
        self.assertEqual(module.final_output_findings(self.plan), ())
        # Two weighting-shaped keys are permitted and no others: a stratum's share
        # of the pooled summary, which sets no dimension against another, and the
        # flag that prohibits weighting outright. No scalar score, composite score,
        # ranking, or price coefficient appears anywhere in the frozen plan.
        permitted = {
            f"workload_manifest.strata[{index}].weight"
            for index, _ in enumerate(self.plan["workload_manifest"]["strata"])
        } | {"pareto_policy.weights_prohibited"}
        flagged = {
            finding.split(" ", 1)[0] for finding in module.weighting_findings(self.plan)
        }
        self.assertEqual(flagged, permitted)

    def test_the_reasoning_token_exclusion_states_its_measured_cost(self) -> None:
        candidate = self.pilot["variance_estimates"]["per_arm"]["candidate"]
        limitation = self.plan["pareto_policy"]["reasoning_tokens_limitation"]
        self.assertIn(str(round(candidate["reasoning_output_tokens"]["mean"], 1)), limitation)
        self.assertIn(str(round(candidate["reasoning_output_tokens"]["sd"], 1)), limitation)

    def test_the_plan_froze_after_calibration_and_before_any_cohort_outcome(self) -> None:
        self.assertGreater(self.plan["frozen_at"], self.pilot["completed_at_utc"])
        observed = sorted(
            str(path.relative_to(REPO_ROOT))
            for root in (REPO_ROOT / "specs", RESEARCH_ROOT)
            for path in root.rglob("*")
            if path.is_file() and COHORT_ARTIFACT_PATTERN.search(path.name)
        )
        self.assertEqual(observed, [], observed)
        self.assertTrue(self.pilot["partition_consumption_proof"]["non_calibration_none_consumed"])
        self.assertEqual(
            self.plan["pre_cohort_outcome_absence_digest"],
            digest_over(pre_cohort_absence_record(self.pilot)),
        )

    def test_every_input_the_pilot_could_not_measure_is_labelled_an_assumption(self) -> None:
        stated = self.assumptions["assumptions_not_measured"]
        self.assertTrue(stated, "the plan claims every input was measured")
        for name, entry in stated.items():
            with self.subTest(assumption=name):
                self.assertIn("value", entry)
                self.assertTrue(entry["basis"].strip())
                self.assertFalse(entry["measured_by_the_calibration_pilot"])
        # The two limitations the pilot itself stated must survive into the plan.
        for marker in ("rubric", "attrition"):
            self.assertTrue(
                any(marker in key for key in stated),
                f"no assumption carries the pilot's {marker} limitation",
            )

    def test_the_frozen_size_is_reported_against_its_own_variance_uncertainty(self) -> None:
        sensitivity = self.assumptions["sensitivity"]
        estimate = self.pilot["variance_estimates"]["paired_within_task_difference"]
        pairs = estimate["semantic_score"]["n"]
        self.assertEqual(sensitivity["variance_estimate_degrees_of_freedom"], pairs - 1)
        # With twelve role clusters the effective sample size is capped at R/icc
        # however many pairs run, so a larger correlation is not merely costlier.
        clusters = self.assumptions["cluster_count"]
        for reported in sensitivity["intracluster_correlation_sensitivity"]:
            with self.subTest(icc=reported["intracluster_correlation"]):
                icc = reported["intracluster_correlation"]
                self.assertEqual(
                    reported["max_attainable_effective_pairs"], clusters / icc
                )
                self.assertEqual(
                    reported["feasible"],
                    clusters / icc
                    > self.assumptions["endpoints"]["semantic_score"]["n_unclustered_pairs"],
                )


class CalibrationDecisionBindingTests(unittest.TestCase):
    """FR-037 at the decision layer: which artifact a bundle binds follows from
    eligibility, not from what the caller passed.

    FR-037 removed the calibration cycle at the comparison pair and again at the
    experiment policy. The decision bundle is the next edge that carries the same
    binding, and contract 1.0.0 required ``analysis_plan_binding`` on every
    bundle unconditionally -- including a ``calibration_complete`` bundle
    produced before any plan exists. The only way to satisfy that was to record
    the calibration protocol's ``{id, digest}`` under the plan's name, so the
    bundle stated a provenance that was not true. 1.1.0 substitutes on
    ``qualification_eligible``.
    """

    def setUp(self) -> None:
        self.assertIsNotNone(claude_analysis_decision, "claude_analysis_decision is not importable")
        self.module = claude_analysis_decision
        self.schema = load_json(DECISION_SCHEMA_PATH)

    # The contract requires a pair on both binding arrays (minItems 2); the
    # shared helper carries one because the tests that use it exercise the
    # decision ladder rather than the contract.
    PAIRED = {
        "assignment_bindings": [
            {"id": "CS-CAL-01-A0", "digest": digest_over({"assignment": 0})},
            {"id": "CS-CAL-01-A1", "digest": digest_over({"assignment": 1})},
        ],
        "score_bundle_bindings": [
            {"id": "SB-CAL-01-A0", "digest": digest_over({"score_bundle": 0})},
            {"id": "SB-CAL-01-A1", "digest": digest_over({"score_bundle": 1})},
        ],
    }

    def validate(self, bundle: dict[str, object]) -> list[str]:
        return schema_findings(bundle, self.schema, self.schema.get("$defs", {}))

    def test_an_ineligible_decision_binds_the_protocol_and_validates(self) -> None:
        bundle = decision_bundle(self.module, **self.PAIRED)
        self.assertIn("calibration_protocol_binding", bundle)
        self.assertNotIn("analysis_plan_binding", bundle)
        self.assertEqual(bundle["schema_version"], "1.1.0")
        self.assertEqual(self.validate(bundle), [])

    def test_an_ineligible_decision_may_not_bind_the_analysis_plan(self) -> None:
        """The defect this version closes, stated as a test."""
        with self.assertRaises(self.module.AnalysisDecisionError):
            decision_bundle(
                self.module,
                calibration_protocol_binding=None,
                analysis_plan_binding={"id": "PLAN-01", "digest": digest_over({"plan": 1})},
            )

    def test_an_ineligible_decision_may_not_bind_both(self) -> None:
        with self.assertRaises(self.module.AnalysisDecisionError):
            decision_bundle(
                self.module,
                analysis_plan_binding={"id": "PLAN-01", "digest": digest_over({"plan": 1})},
            )

    def test_an_ineligible_decision_must_bind_something(self) -> None:
        with self.assertRaises(self.module.AnalysisDecisionError):
            decision_bundle(self.module, calibration_protocol_binding=None)

    def test_an_eligible_decision_binds_the_plan_and_not_the_protocol(self) -> None:
        eligible = {
            "partition_id": "CAR-003-SELECT-01",
            "partition_type": "selection",
            "qualification_eligible": True,
        }
        bundle = decision_bundle(
            self.module,
            partition=eligible,
            calibration_protocol_binding=None,
            analysis_plan_binding={"id": "PLAN-01", "digest": digest_over({"plan": 1})},
            decision="no_qualification",
            decision_reasons=["floors_failed"],
            **self.PAIRED,
        )
        self.assertIn("analysis_plan_binding", bundle)
        self.assertNotIn("calibration_protocol_binding", bundle)
        self.assertEqual(self.validate(bundle), [])

        with self.assertRaises(self.module.AnalysisDecisionError):
            decision_bundle(
                self.module,
                partition=eligible,
                decision="no_qualification",
                decision_reasons=["floors_failed"],
            )

    def test_the_contract_still_accepts_evidence_sealed_under_1_0_0(self) -> None:
        """A frozen record is not retroactively invalid because the contract improved.

        The committed calibration pilot declared 1.0.0 and bound the protocol
        under the plan's name, which is what 1.0.0 required. Regenerating it
        would mean a new live run whose measurements would differ from the ones
        the frozen analysis plan was derived from, so the contract keeps 1.0.0
        valid rather than invalidating sealed evidence retroactively.
        """
        pilot = load_json(CALIBRATION_PILOT_PATH)
        bundles = [entry["decision_bundle"] for entry in pilot["decision_bundles"]]
        self.assertTrue(bundles, "the committed pilot records no decision bundles")
        for bundle in bundles:
            with self.subTest(bundle=bundle["decision_bundle_id"]):
                self.assertEqual(bundle["schema_version"], "1.0.0")
                self.assertIn("analysis_plan_binding", bundle)
                self.assertEqual(self.validate(bundle), [])

    def test_a_1_1_0_bundle_carrying_the_legacy_shape_is_refused_by_the_contract(self) -> None:
        """Version alone must not be a loophole."""
        bundle = dict(decision_bundle(self.module))
        bundle["analysis_plan_binding"] = bundle.pop("calibration_protocol_binding")
        self.assertNotEqual(self.validate(bundle), [])


TEST_CASES = (
    OrderedLadderTests,
    ParetoDominanceTests,
    TerminalMappingTests,
    EstimandAndRerunTests,
    GuardrailAndErrorControlTests,
    DecisionBundleWriteGuardTests,
    ReplayAndNonPoolingTests,
    CalibrationDecisionBindingTests,
    FrozenAnalysisPlanTests,
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-analysis-decision-ladder"))
