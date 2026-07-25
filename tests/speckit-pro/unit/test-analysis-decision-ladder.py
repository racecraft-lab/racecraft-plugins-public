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

try:  # T071…T075 deliverable — absent until the decision module is implemented.
    import claude_analysis_decision  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    claude_analysis_decision = None  # type: ignore[assignment]


CONTRACT_ROOT = REPO_ROOT / "specs" / "car-003-evaluation-runner-scoring" / "contracts"
PLAN_SCHEMA_PATH = CONTRACT_ROOT / "analysis-plan.schema.json"
DECISION_SCHEMA_PATH = CONTRACT_ROOT / "analysis-decision.schema.json"
ADDITIVE_SCHEMA_PATH = CONTRACT_ROOT / "car-003-additive-records.schema.json"
REPLAY_FIXTURE_PATH = (
    TEST_ROOT / "layer6-efficiency" / "fixtures" / "car-003-calibration-replay.json"
)

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


TEST_CASES = (
    OrderedLadderTests,
    ParetoDominanceTests,
    TerminalMappingTests,
    EstimandAndRerunTests,
    GuardrailAndErrorControlTests,
    ReplayAndNonPoolingTests,
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-analysis-decision-ladder"))
