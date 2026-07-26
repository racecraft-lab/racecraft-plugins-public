#!/usr/bin/env python3
"""Contracts for deterministic hard gates, blinded ballots, and adjudication.

An outcome reaches a semantic scorer only after seven deterministic hard gates
all pass; the ballot then binds exactly one blinded artifact as its sole scored
input. Blinding is enforced **and bounded**: a mechanical leak check strips
explicit identifiers and fails closed, but identifier stripping cannot remove
stylistic tells, so every ballot also records whether provenance was inferred
and from what signal (FR-014, FR-035, FR-048).

Three families of checks live here:

* **Contract-structural** cases load the parity-mirror
  ``specs/car-003-evaluation-runner-scoring/contracts/score-bundle.schema.json``
  and assert the four closed taxonomies it publishes.
* **Module-contract** cases exercise
  ``tests/speckit-pro/layer6-efficiency/lib/claude_score_bundle.py``: the gate
  barrier, the leak check, two-ballot collection, adjudication routing, observed
  scorer-identity attestation, and the total code-to-plane mapping.
* **Repository-boundary** cases assert the evidence ignore rule keeps a named
  consolidated baseline trackable while per-run raw output stays ignored, and
  that the three repo-level shared contracts are untouched.

Every check is offline and makes zero live model calls.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LIB_DIR = TEST_ROOT / "lib"
LAYER6_DIR = TEST_ROOT / "layer6-efficiency"
LAYER6_LIB_DIR = LAYER6_DIR / "lib"
for _path in (LIB_DIR, LAYER6_LIB_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from test_result import run_counted  # noqa: E402

try:  # T052…T056 deliverable — absent until the score-bundle module is implemented.
    import claude_score_bundle  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    claude_score_bundle = None  # type: ignore[assignment]


CONTRACT_ROOT = REPO_ROOT / "specs" / "car-003-evaluation-runner-scoring" / "contracts"
BUNDLE_SCHEMA_PATH = CONTRACT_ROOT / "score-bundle.schema.json"
ADDITIVE_SCHEMA_PATH = CONTRACT_ROOT / "car-003-additive-records.schema.json"
SHARED_CONTRACT_DIR = LAYER6_DIR / "contracts"
SHARED_CONTRACT_NAMES = (
    "capability-freeze.schema.json",
    "marker-checkpoint.schema.json",
    "treatment-record.schema.json",
)

# FR-014: the closed hard-gate set, stated as a literal so widening either the
# module or the mirror schema shows up as a diff here.
REQUIRED_GATES = ("role", "safety", "grounding", "mutation", "tool", "output", "acceptance")

# FR-034: the closed score taxonomies, adopted verbatim from the parity mirror.
SCORE_DISPOSITIONS = ("accepted", "gate_failed", "invalidated", "non_scorable")
FAILURE_PLANES = (
    "adjudication",
    "ballot",
    "candidate",
    "evidence_boundary",
    "fixture",
    "gate",
    "infrastructure",
    "none",
    "partition",
    "schema",
    "scorer",
    "treatment",
)
INVALIDATION_REASONS = (
    "adjudicator_changed",
    "capability_changed",
    "fixture_changed",
    "none",
    "partition_changed",
    "rubric_changed",
    "schema_changed",
    "scorer_changed",
    "treatment_changed",
)

# FR-034: platform alias re-pointing reuses the shared treatment-record code in
# disposition_reasons; the score bundle's own code stays service_reroute.
SHARED_REROUTE_DISPOSITION_REASON = "service_reroute_requested_route_non_scorable"
CAPABILITY_PLANE_CODE = "alias_repoint_unresolved"

# Frozen scoring furniture for the module-contract cases. None of it is a live
# call: the identities are opaque labels and the scores are recorded fixtures.
CANDIDATE_MODEL_IDS = ("claude-opus-4-6-20260115", "claude-sonnet-4-6-20260115")
CANDIDATE_ALIASES = ("opus", "sonnet")
CANDIDATE_FAMILIES = ("opus", "sonnet")
CANDIDATE_ROUTE_IDS = ("candidate-route-alpha", "comparator-route-beta")
EFFORT_VALUES = ("low", "medium", "high", "xhigh", "max")
FAMILY_DECLARATION = {
    "claude-opus-4-6-20260115": "opus",
    "claude-sonnet-4-6-20260115": "sonnet",
    "scorer-model-outside-candidate-families": "independent-scorer",
    "adjudicator-model-outside-candidate-families": "independent-adjudicator",
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(record: object) -> str:
    return json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def digest_over(record: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()


def binding(identifier: str) -> dict[str, str]:
    return {"id": identifier, "digest": digest_over({"binding": identifier})}


RUBRIC_BINDING = binding("car-003-semantic-rubric-v1")
STALE_RUBRIC_BINDING = binding("car-003-semantic-rubric-v0")
FROZEN_RUBRIC = {
    "rubric_binding": RUBRIC_BINDING,
    "criteria": ("grounding", "completeness", "instruction_adherence"),
    "criterion_threshold": 3.0,
}
CURRENT_CALIBRATIONS = ("calibration-scorer-a-v3", "calibration-scorer-b-v3", "calibration-adjudicator-v3")
BLINDED_ARTIFACT = (
    "# Task outcome\n"
    "The runner materialised the destination file, verified the digest, and "
    "recorded the acceptance oracle result. Two follow-up checks were listed.\n"
)
BLINDED_ARTIFACT_DIGEST = digest_over({"artifact": BLINDED_ARTIFACT})


def gate_results(*, missing: tuple[str, ...] = (), failing: tuple[str, ...] = ()) -> list[dict[str, object]]:
    return [
        {"gate": gate, "pass": gate not in failing, "evidence_digest": digest_over({"gate": gate})}
        for gate in REQUIRED_GATES
        if gate not in missing
    ]


def git_output(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class DeterministicGateTests(unittest.TestCase):
    """All seven hard gates are required for every executed role, a missing gate
    result fails closed, and no ballot is collected until every gate passes
    (FR-014)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_score_bundle, "claude_score_bundle is not importable")
        self.module = claude_score_bundle

    def test_the_hard_gate_set_is_closed_to_seven_named_gates(self) -> None:
        self.assertEqual(self.module.REQUIRED_GATES, REQUIRED_GATES)
        schema = load_json(BUNDLE_SCHEMA_PATH)
        published = schema["properties"]["deterministic_gates"]["items"]["properties"]["gate"]["enum"]  # type: ignore[index]
        self.assertEqual(tuple(sorted(published)), tuple(sorted(REQUIRED_GATES)))

    def test_a_complete_passing_gate_set_is_accepted(self) -> None:
        verdict = self.module.evaluate_gates(gate_results())
        self.assertTrue(verdict.complete)
        self.assertTrue(verdict.all_passed)
        self.assertEqual(verdict.missing, ())
        self.assertEqual(verdict.failed, ())
        self.assertEqual(verdict.failure_plane, "none")
        self.assertEqual(verdict.failure_code, "none")

    def test_every_single_missing_gate_fails_closed_rather_than_reading_as_a_pass(self) -> None:
        for gate in REQUIRED_GATES:
            with self.subTest(gate=gate):
                verdict = self.module.evaluate_gates(gate_results(missing=(gate,)))
                self.assertFalse(verdict.complete)
                self.assertFalse(verdict.all_passed)
                self.assertEqual(verdict.missing, (gate,))
                self.assertEqual(verdict.failure_plane, "evidence_boundary")
                self.assertEqual(verdict.failure_code, "required_evidence_missing")

    def test_there_is_no_per_role_gate_subset(self) -> None:
        self.assertEqual(self.module.required_gates_for_role("implement-executor"), REQUIRED_GATES)
        self.assertEqual(self.module.required_gates_for_role("codebase-analyst"), REQUIRED_GATES)

    def test_a_duplicated_gate_name_is_refused(self) -> None:
        duplicated = gate_results()
        duplicated.append(dict(duplicated[0]))
        verdict = self.module.evaluate_gates(duplicated)
        self.assertFalse(verdict.complete)
        self.assertEqual(verdict.missing, ())
        self.assertEqual(verdict.failure_plane, "schema")
        self.assertEqual(verdict.failure_code, "schema_invalid")

    def test_an_unknown_gate_name_is_refused(self) -> None:
        with self.assertRaises(self.module.ScoreBundleError):
            self.module.evaluate_gates(
                gate_results() + [{"gate": "vibes", "pass": True, "evidence_digest": digest_over({})}]
            )

    def test_each_gate_result_records_name_pass_and_evidence_digest(self) -> None:
        for result in gate_results():
            with self.subTest(gate=result["gate"]):
                self.assertEqual(tuple(sorted(result)), ("evidence_digest", "gate", "pass"))
                self.assertTrue(str(result["evidence_digest"]).startswith("sha256:"))

    def test_a_failing_gate_blocks_the_bundle_on_its_own_plane(self) -> None:
        verdict = self.module.evaluate_gates(gate_results(failing=("safety",)))
        self.assertTrue(verdict.complete)
        self.assertFalse(verdict.all_passed)
        self.assertEqual(verdict.failed, ("safety",))
        self.assertEqual(self.module.bind_disposition(verdict.failure_plane, verdict.failure_code, "none"), "gate_failed")

    def test_no_ballot_is_collected_until_every_gate_has_passed(self) -> None:
        self.assertTrue(self.module.ballots_permitted(gate_results()))
        self.assertFalse(self.module.ballots_permitted(gate_results(failing=("output",))))
        self.assertFalse(self.module.ballots_permitted(gate_results(missing=("acceptance",))))

    def test_ballot_collection_refuses_to_run_behind_an_open_gate(self) -> None:
        collection = self.module.collect_ballots(
            gate_results(failing=("grounding",)),
            ballots=(scorer_a_ballot(self.module), scorer_b_ballot(self.module)),
            rubric=FROZEN_RUBRIC,
            current_calibrations=CURRENT_CALIBRATIONS,
        )
        self.assertFalse(collection.accepted)
        self.assertEqual(collection.ballots, ())
        self.assertIn("gate_barrier", collection.reasons)


def scorer_a_ballot(module: object, **overrides: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "ballot_id": "ballot-scorer-a-001",
        "scorer_binding": binding("scorer-identity-a"),
        "scorer_execution_id": "scorer-execution-a-001",
        "calibration_binding": binding("calibration-scorer-a-v3"),
        "rubric_binding": RUBRIC_BINDING,
        "blinded_artifact_digest": BLINDED_ARTIFACT_DIGEST,
        "criterion_scores": {"grounding": 4.0, "completeness": 4.0, "instruction_adherence": 4.0},
        "provenance_inferred": False,
        "inference_signal": None,
        "presentation_order_seed": "presentation-seed-001",
    }
    fields.update(overrides)
    return module.build_ballot(**fields)  # type: ignore[attr-defined]


def leak_lexicon(module: object) -> dict[str, object]:
    return module.build_leak_lexicon(  # type: ignore[attr-defined]
        model_identities=CANDIDATE_MODEL_IDS,
        aliases=CANDIDATE_ALIASES,
        efforts=EFFORT_VALUES,
        route_identifiers=CANDIDATE_ROUTE_IDS,
    )


def passing_leak_finding(module: object) -> object:
    """A real leak-check verdict over a clean artifact.

    Supplied wherever a caller must present blinding evidence: the collector and
    the bundle builder consume a recorded finding and never assume one passed.
    """
    return module.leak_check(BLINDED_ARTIFACT, leak_lexicon(module))  # type: ignore[attr-defined]


def failing_leak_finding(module: object) -> object:
    return module.leak_check(  # type: ignore[attr-defined]
        BLINDED_ARTIFACT + "\nclaude-opus-4-6-20260115\n", leak_lexicon(module)
    )


def scorer_b_ballot(module: object, **overrides: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "ballot_id": "ballot-scorer-b-001",
        "scorer_binding": binding("scorer-identity-b"),
        "scorer_execution_id": "scorer-execution-b-001",
        "calibration_binding": binding("calibration-scorer-b-v3"),
        "rubric_binding": RUBRIC_BINDING,
        "blinded_artifact_digest": BLINDED_ARTIFACT_DIGEST,
        "criterion_scores": {"grounding": 4.0, "completeness": 3.5, "instruction_adherence": 4.0},
        "provenance_inferred": False,
        "inference_signal": None,
        "presentation_order_seed": "presentation-seed-001",
    }
    fields.update(overrides)
    return module.build_ballot(**fields)  # type: ignore[attr-defined]


class BlindedBallotTests(unittest.TestCase):
    """One blinded artifact per ballot, a mechanical leak check that fails closed,
    observed-identity family exclusion, and seeded presentation order with no
    normalization step (FR-035, FR-047)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_score_bundle, "claude_score_bundle is not importable")
        self.module = claude_score_bundle
        self.lexicon = self.module.build_leak_lexicon(
            model_identities=CANDIDATE_MODEL_IDS,
            aliases=CANDIDATE_ALIASES,
            efforts=EFFORT_VALUES,
            route_identifiers=CANDIDATE_ROUTE_IDS,
        )

    def test_a_ballot_binds_exactly_one_blinded_artifact_as_its_sole_scored_input(self) -> None:
        ballot = scorer_a_ballot(self.module)
        self.assertEqual(ballot["blinded_artifact_digest"], BLINDED_ARTIFACT_DIGEST)
        self.assertEqual(self.module.scored_inputs(ballot), (BLINDED_ARTIFACT_DIGEST,))

    def test_a_ballot_carrying_a_second_scored_input_is_refused(self) -> None:
        with self.assertRaises(self.module.ScoreBundleError):
            scorer_a_ballot(self.module, blinded_artifact_digest=[BLINDED_ARTIFACT_DIGEST, digest_over({"b": 1})])

    def test_a_clean_artifact_passes_the_mechanical_leak_check(self) -> None:
        finding = self.module.leak_check(BLINDED_ARTIFACT, self.lexicon)
        self.assertTrue(finding.passed, finding.hits)
        self.assertEqual(finding.hits, ())
        self.assertEqual(finding.failure_code, "none")

    def test_a_freeze_bound_model_identity_fails_the_leak_check(self) -> None:
        leaked = BLINDED_ARTIFACT + "\nProduced by claude-opus-4-6-20260115.\n"
        finding = self.module.leak_check(leaked, self.lexicon)
        self.assertFalse(finding.passed)
        self.assertEqual(finding.failure_plane, "ballot")
        self.assertEqual(finding.failure_code, "ballot_non_blind")

    def test_an_alias_an_effort_value_and_a_route_identifier_each_fail_the_leak_check(self) -> None:
        cases = {
            "alias": "\nRun on the opus alias.\n",
            "effort": "\nreasoning_effort: xhigh\n",
            "route": "\nRoute candidate-route-alpha served this attempt.\n",
        }
        for label, suffix in sorted(cases.items()):
            with self.subTest(identifier=label):
                finding = self.module.leak_check(BLINDED_ARTIFACT + suffix, self.lexicon)
                self.assertFalse(finding.passed)
                self.assertEqual(finding.failure_code, "ballot_non_blind")

    def test_agent_frontmatter_fails_the_leak_check(self) -> None:
        leaked = "---\nname: implement-executor\nmodel: opus\n---\n" + BLINDED_ARTIFACT
        finding = self.module.leak_check(leaked, self.lexicon)
        self.assertFalse(finding.passed)
        self.assertEqual(finding.failure_code, "ballot_non_blind")

    def test_an_effort_word_in_ordinary_prose_is_not_a_leak(self) -> None:
        # The lexicon separates unambiguous identity tokens from effort values,
        # which are ordinary English and only leak in a declaration context.
        finding = self.module.leak_check(
            BLINDED_ARTIFACT + "\nThe max retry count was low and confidence stayed high.\n",
            self.lexicon,
        )
        self.assertTrue(finding.passed, finding.hits)

    def test_a_failed_leak_check_blocks_scoring(self) -> None:
        collection = self.module.collect_ballots(
            gate_results(),
            ballots=(scorer_a_ballot(self.module), scorer_b_ballot(self.module)),
            rubric=FROZEN_RUBRIC,
            current_calibrations=CURRENT_CALIBRATIONS,
            leak_finding=self.module.leak_check(
                BLINDED_ARTIFACT + "\nclaude-opus-4-6-20260115\n", self.lexicon
            ),
        )
        self.assertFalse(collection.accepted)
        self.assertEqual(collection.failure_code, "ballot_non_blind")
        self.assertEqual(collection.failure_plane, "ballot")

    def test_a_scorer_observed_inside_a_candidate_family_is_rejected(self) -> None:
        attestation = self.module.build_scorer_identity_attestation(
            attestation_id="attestation-001",
            score_bundle_binding=binding("score-bundle-001"),
            recorded_at="2026-07-25T00:00:00Z",
            ballot_attestations=(
                {
                    "ballot_role": "scorer_a",
                    "declared_family": "independent-scorer",
                    "observed_model_id": "claude-opus-4-6-20260115",
                },
                {
                    "ballot_role": "scorer_b",
                    "declared_family": "independent-scorer",
                    "observed_model_id": "scorer-model-outside-candidate-families",
                },
            ),
            family_declaration=FAMILY_DECLARATION,
            candidate_families=CANDIDATE_FAMILIES,
        )
        by_role = {entry["ballot_role"]: entry for entry in attestation["ballot_attestations"]}
        self.assertFalse(by_role["scorer_a"]["family_exclusion_holds"])
        self.assertEqual(by_role["scorer_a"]["observed_family"], "opus")
        self.assertTrue(by_role["scorer_b"]["family_exclusion_holds"])
        self.assertTrue(self.module.attestation_blocks_acceptance(attestation))

    def test_an_adjudicator_observed_inside_a_candidate_family_is_rejected(self) -> None:
        attestation = self.module.build_scorer_identity_attestation(
            attestation_id="attestation-002",
            score_bundle_binding=binding("score-bundle-002"),
            recorded_at="2026-07-25T00:00:00Z",
            ballot_attestations=(
                {
                    "ballot_role": "adjudicator",
                    "declared_family": "independent-adjudicator",
                    "observed_model_id": "claude-sonnet-4-6-20260115",
                },
            ),
            family_declaration=FAMILY_DECLARATION,
            candidate_families=CANDIDATE_FAMILIES,
        )
        self.assertTrue(self.module.attestation_blocks_acceptance(attestation))
        self.assertEqual(
            self.module.attestation_findings(attestation),
            ("adjudicator:adjudicator_invalid",),
        )

    def test_an_unobservable_scorer_identity_fails_closed(self) -> None:
        attestation = self.module.build_scorer_identity_attestation(
            attestation_id="attestation-003",
            score_bundle_binding=binding("score-bundle-003"),
            recorded_at="2026-07-25T00:00:00Z",
            ballot_attestations=(
                {
                    "ballot_role": "scorer_a",
                    "declared_family": "independent-scorer",
                    "observed_model_id": None,
                },
            ),
            family_declaration=FAMILY_DECLARATION,
            candidate_families=CANDIDATE_FAMILIES,
        )
        entry = attestation["ballot_attestations"][0]
        self.assertIsNone(entry["observed_family"])
        self.assertFalse(entry["family_exclusion_holds"])
        self.assertTrue(self.module.attestation_blocks_acceptance(attestation))

    def test_the_attestation_matches_its_published_additive_record(self) -> None:
        attestation = self.module.build_scorer_identity_attestation(
            attestation_id="attestation-004",
            score_bundle_binding=binding("score-bundle-004"),
            recorded_at="2026-07-25T00:00:00Z",
            ballot_attestations=(
                {
                    "ballot_role": "scorer_a",
                    "declared_family": "independent-scorer",
                    "observed_model_id": "scorer-model-outside-candidate-families",
                },
            ),
            family_declaration=FAMILY_DECLARATION,
            candidate_families=CANDIDATE_FAMILIES,
        )
        schema = load_json(ADDITIVE_SCHEMA_PATH)
        published = schema["$defs"]["scorerIdentityAttestation"]  # type: ignore[index]
        self.assertEqual(tuple(sorted(attestation)), tuple(sorted(published["required"])))
        self.assertEqual(attestation["record_kind"], "scorer_identity_attestation")
        entry_keys = tuple(sorted(attestation["ballot_attestations"][0]))
        self.assertEqual(
            entry_keys,
            tuple(sorted(published["properties"]["ballot_attestations"]["items"]["required"])),
        )
        self.assertEqual(
            attestation["attestation_digest"],
            self.module.record_digest(attestation, digest_field="attestation_digest"),
        )

    def test_a_scorer_whose_observed_identity_diverges_from_its_route_blocks_that_ballot(self) -> None:
        divergence = self.module.check_scorer_route_divergence(
            declared_route_identity="scorer-model-outside-candidate-families",
            observed_model_id="claude-opus-4-6-20260115",
        )
        self.assertTrue(divergence.diverged)
        self.assertTrue(divergence.blocks_ballot)
        self.assertEqual(divergence.failure_plane, "scorer")
        self.assertEqual(divergence.failure_code, "scorer_invalid")
        agreeing = self.module.check_scorer_route_divergence(
            declared_route_identity="scorer-model-outside-candidate-families",
            observed_model_id="scorer-model-outside-candidate-families",
        )
        self.assertFalse(agreeing.diverged)
        self.assertFalse(agreeing.blocks_ballot)

    def test_presentation_order_is_randomised_under_a_recorded_seed(self) -> None:
        items = ("arm-a", "arm-b", "arm-c", "arm-d", "arm-e", "arm-f")
        first = self.module.presentation_order(items, "presentation-seed-001")
        self.assertEqual(first, self.module.presentation_order(items, "presentation-seed-001"))
        self.assertEqual(tuple(sorted(first)), tuple(sorted(items)))
        seeds = {self.module.presentation_order(items, f"seed-{index}") for index in range(12)}
        self.assertGreater(len(seeds), 1)

    def test_no_paraphrase_or_style_normalisation_step_exists(self) -> None:
        for banned in ("paraphrase", "normalize_style", "normalise_style", "style_normalize"):
            with self.subTest(step=banned):
                self.assertFalse(hasattr(self.module, banned))


class ScorerProvenanceTests(unittest.TestCase):
    """Two distinct scorers on one frozen rubric, adjudication on decision-affecting
    disagreement, complete provenance, and a bounded blinding residual
    (FR-015, FR-016, FR-048, SC-006)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_score_bundle, "claude_score_bundle is not importable")
        self.module = claude_score_bundle

    def collect(self, **overrides: object) -> object:
        fields: dict[str, object] = {
            "ballots": (scorer_a_ballot(self.module), scorer_b_ballot(self.module)),
            "rubric": FROZEN_RUBRIC,
            "current_calibrations": CURRENT_CALIBRATIONS,
            # Real blinding evidence, because an absent finding is a refusal:
            # the collector consumes the leak check's verdict and never assumes
            # a check it was not shown.
            "leak_finding": passing_leak_finding(self.module),
        }
        fields.update(overrides)
        return self.module.collect_ballots(gate_results(), **fields)

    def test_two_distinct_scorer_identities_and_execution_records_are_required(self) -> None:
        collection = self.collect()
        self.assertTrue(collection.accepted, collection.reasons)
        self.assertEqual(len(collection.ballots), 2)
        same_identity = self.collect(
            ballots=(
                scorer_a_ballot(self.module),
                scorer_b_ballot(self.module, scorer_binding=binding("scorer-identity-a")),
            )
        )
        self.assertFalse(same_identity.accepted)
        self.assertEqual(same_identity.failure_code, "scorer_invalid")
        same_execution = self.collect(
            ballots=(
                scorer_a_ballot(self.module),
                scorer_b_ballot(self.module, scorer_execution_id="scorer-execution-a-001"),
            )
        )
        self.assertFalse(same_execution.accepted)
        self.assertEqual(same_execution.failure_code, "scorer_invalid")

    def test_a_single_ballot_is_not_enough(self) -> None:
        collection = self.collect(ballots=(scorer_a_ballot(self.module),))
        self.assertFalse(collection.accepted)
        self.assertEqual(collection.failure_code, "ballot_missing")
        self.assertEqual(collection.failure_plane, "ballot")

    def test_both_ballots_bind_the_frozen_rubric_version_and_digest(self) -> None:
        collection = self.collect()
        for ballot in collection.ballots:
            with self.subTest(ballot=ballot["ballot_id"]):
                self.assertEqual(ballot["rubric_binding"], RUBRIC_BINDING)
        stale = self.collect(
            ballots=(
                scorer_a_ballot(self.module),
                scorer_b_ballot(self.module, rubric_binding=STALE_RUBRIC_BINDING),
            )
        )
        self.assertFalse(stale.accepted)
        self.assertEqual(stale.failure_code, "ballot_rubric_stale")

    def test_scorer_calibration_must_be_current(self) -> None:
        stale = self.collect(
            ballots=(
                scorer_a_ballot(self.module),
                scorer_b_ballot(self.module, calibration_binding=binding("calibration-scorer-b-v1")),
            )
        )
        self.assertFalse(stale.accepted)
        self.assertEqual(stale.failure_code, "scorer_calibration_missing")
        self.assertEqual(stale.failure_plane, "scorer")

    def test_agreeing_ballots_need_no_adjudicator(self) -> None:
        a = scorer_a_ballot(self.module)
        b = scorer_b_ballot(self.module)
        self.assertFalse(self.module.decision_affecting_disagreement(a, b, FROZEN_RUBRIC))

    def test_a_decision_affecting_disagreement_routes_to_a_frozen_third_adjudicator(self) -> None:
        a = scorer_a_ballot(self.module)
        b = scorer_b_ballot(
            self.module,
            criterion_scores={"grounding": 2.0, "completeness": 3.5, "instruction_adherence": 4.0},
        )
        self.assertTrue(self.module.decision_affecting_disagreement(a, b, FROZEN_RUBRIC))
        adjudication = self.module.adjudicate(
            a,
            b,
            adjudication_id="adjudication-001",
            adjudicator_binding=binding("adjudicator-identity-frozen"),
            resolved_outcome="scorer_a_upheld",
        )
        self.assertEqual(
            tuple(sorted(adjudication)),
            ("adjudication_digest", "adjudication_id", "adjudicator_binding", "ballot_bindings", "resolved_outcome"),
        )
        self.assertEqual(len(adjudication["ballot_bindings"]), 2)
        self.assertEqual(
            adjudication["adjudication_digest"],
            self.module.record_digest(adjudication, digest_field="adjudication_digest"),
        )

    def test_an_adjudicator_reusing_a_primary_scorer_is_refused(self) -> None:
        a = scorer_a_ballot(self.module)
        b = scorer_b_ballot(
            self.module,
            criterion_scores={"grounding": 2.0, "completeness": 3.5, "instruction_adherence": 4.0},
        )
        with self.assertRaises(self.module.ScoreBundleError) as caught:
            self.module.adjudicate(
                a,
                b,
                adjudication_id="adjudication-002",
                adjudicator_binding=binding("scorer-identity-a"),
                resolved_outcome="scorer_a_upheld",
            )
        self.assertIn("adjudicator_reused_primary_scorer", str(caught.exception))

    def test_an_unresolved_disagreement_blocks_the_bundle(self) -> None:
        a = scorer_a_ballot(self.module)
        b = scorer_b_ballot(
            self.module,
            criterion_scores={"grounding": 2.0, "completeness": 3.5, "instruction_adherence": 4.0},
        )
        collection = self.collect(ballots=(a, b))
        self.assertFalse(collection.accepted)
        self.assertEqual(collection.failure_code, "adjudication_disagreement_unresolved")
        self.assertEqual(collection.failure_plane, "adjudication")
        resolved = self.collect(
            ballots=(a, b),
            adjudication=self.module.adjudicate(
                a,
                b,
                adjudication_id="adjudication-003",
                adjudicator_binding=binding("adjudicator-identity-frozen"),
                resolved_outcome="scorer_a_upheld",
            ),
        )
        self.assertTrue(resolved.accepted, resolved.reasons)

    def test_the_adjudicator_provenance_attaches_to_the_bundle(self) -> None:
        bundle = complete_bundle(self.module)
        self.assertIsNotNone(bundle["adjudication"])
        self.assertEqual(
            bundle["adjudication"]["adjudicator_binding"]["id"], "adjudicator-identity-frozen"
        )
        self.assertEqual(self.module.missing_provenance(bundle), ())

    def test_every_provenance_class_is_preserved(self) -> None:
        bundle = complete_bundle(self.module)
        self.assertEqual(
            tuple(sorted(self.module.PROVENANCE_CLASSES)),
            ("adjudicator", "candidate", "fixture", "infrastructure", "scorer", "treatment"),
        )
        for provenance_class, fields in sorted(self.module.PROVENANCE_CLASSES.items()):
            for field in fields:
                with self.subTest(provenance=provenance_class, field=field):
                    stripped = {key: value for key, value in bundle.items() if key != field}
                    self.assertIn(
                        f"{provenance_class}:{field}", self.module.missing_provenance(stripped)
                    )

    def test_every_ballot_records_whether_provenance_was_inferred(self) -> None:
        for ballot in complete_bundle(self.module)["ballots"]:
            with self.subTest(ballot=ballot["ballot_id"]):
                self.assertIn("provenance_inferred", ballot)
                self.assertIsInstance(ballot["provenance_inferred"], bool)
                self.assertIn("inference_signal", ballot)

    def test_a_recorded_inference_is_a_residual_rather_than_a_silent_invalidation(self) -> None:
        inferring = scorer_b_ballot(
            self.module, provenance_inferred=True, inference_signal="section_heading_style"
        )
        collection = self.collect(ballots=(scorer_a_ballot(self.module), inferring))
        self.assertTrue(collection.accepted, collection.reasons)
        residual = self.module.blinding_residual(
            leak_check_passed=True, ballots=(scorer_a_ballot(self.module), inferring)
        )
        self.assertTrue(residual["leak_check_passed"])
        self.assertTrue(residual["provenance_inferred"])
        self.assertEqual(residual["inference_signal"], "section_heading_style")

    def test_an_inference_flag_without_a_signal_is_refused(self) -> None:
        with self.assertRaises(self.module.ScoreBundleError):
            scorer_a_ballot(self.module, provenance_inferred=True, inference_signal=None)

    def test_blinding_is_reported_as_bounded_and_never_as_complete(self) -> None:
        residual = self.module.blinding_residual(
            leak_check_passed=True, ballots=(scorer_a_ballot(self.module), scorer_b_ballot(self.module))
        )
        self.assertEqual(
            tuple(sorted(residual)),
            ("inference_signal", "inference_signals", "leak_check_passed", "provenance_inferred"),
        )
        self.assertIn("bounded", self.module.BLINDING_CLAIM.lower())
        self.assertNotIn("complete", self.module.BLINDING_CLAIM.lower())

    def test_every_inferring_ballot_contributes_its_signal(self) -> None:
        """FR-048: the residual must not shrink as more scorers infer.

        Taking ``next(...)`` over the inferring ballots reported one signal no
        matter how many scorers independently saw through the blinding, so the
        residual understated itself exactly when the blinding was weakest.
        """
        first = scorer_a_ballot(
            self.module, provenance_inferred=True, inference_signal="section_heading_style"
        )
        second = scorer_b_ballot(
            self.module, provenance_inferred=True, inference_signal="list_marker_choice"
        )
        residual = self.module.blinding_residual(
            leak_check_passed=False, ballots=(first, second)
        )
        self.assertEqual(
            tuple(residual["inference_signals"]),
            ("section_heading_style", "list_marker_choice"),
        )
        self.assertTrue(residual["provenance_inferred"])
        # The scalar stays the first signal for the cross-platform contract.
        self.assertEqual(residual["inference_signal"], "section_heading_style")

    def test_a_residual_with_no_inference_carries_an_empty_signal_list(self) -> None:
        residual = self.module.blinding_residual(
            leak_check_passed=True,
            ballots=(scorer_a_ballot(self.module), scorer_b_ballot(self.module)),
        )
        self.assertEqual(tuple(residual["inference_signals"]), ())
        self.assertIsNone(residual["inference_signal"])
        self.assertFalse(residual["provenance_inferred"])


def complete_bundle(module: object, **overrides: object) -> dict[str, object]:
    a = scorer_a_ballot(module)
    b = scorer_b_ballot(
        module, criterion_scores={"grounding": 2.0, "completeness": 3.5, "instruction_adherence": 4.0}
    )
    fields: dict[str, object] = {
        "score_bundle_id": "score-bundle-complete-001",
        "bindings": {name: binding(name.replace("_binding", "")) for name in module.PROVENANCE_BINDINGS},  # type: ignore[attr-defined]
        "deterministic_gates": gate_results(),
        "ballots": (a, b),
        "adjudication": module.adjudicate(  # type: ignore[attr-defined]
            a,
            b,
            adjudication_id="adjudication-bundle-001",
            adjudicator_binding=binding("adjudicator-identity-frozen"),
            resolved_outcome="scorer_a_upheld",
        ),
        "resource_vector": {
            "input_tokens": 1200,
            "cached_input_tokens": 400,
            "output_tokens": 300,
            "duration_ms": 45_000,
            "retries": 0,
            "compactions": 0,
            "acceptance": 1.0,
            "terminal_state": "completed",
        },
        "reasoning_output_tokens": 800,
        "evidence_refs": (digest_over({"evidence": "gate-log"}),),
    }
    fields.update(overrides)
    return module.build_score_bundle(**fields)  # type: ignore[attr-defined]


class ClosedTaxonomyTests(unittest.TestCase):
    """The four closed taxonomies, the total code-to-plane mapping, the disposition
    biconditional, and the shared contracts left untouched (FR-034)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_score_bundle, "claude_score_bundle is not importable")
        self.module = claude_score_bundle
        self.schema = load_json(BUNDLE_SCHEMA_PATH)

    def published(self, field: str) -> tuple[str, ...]:
        return tuple(sorted(self.schema["properties"][field]["enum"]))  # type: ignore[index]

    def test_the_four_closed_taxonomies_are_set_equal_to_the_mirrored_contract(self) -> None:
        self.assertEqual(tuple(sorted(self.module.SCORE_DISPOSITIONS)), SCORE_DISPOSITIONS)
        self.assertEqual(self.published("score_disposition"), SCORE_DISPOSITIONS)
        self.assertEqual(tuple(sorted(self.module.FAILURE_PLANES)), FAILURE_PLANES)
        self.assertEqual(self.published("failure_plane"), FAILURE_PLANES)
        self.assertEqual(tuple(sorted(self.module.INVALIDATION_REASONS)), INVALIDATION_REASONS)
        self.assertEqual(self.published("invalidation_reason"), INVALIDATION_REASONS)
        self.assertEqual(tuple(sorted(self.module.FAILURE_CODES)), self.published("failure_code"))

    def test_the_code_to_plane_mapping_is_total_and_single_valued(self) -> None:
        self.assertEqual(
            tuple(sorted(self.module.FAILURE_PLANE_BY_CODE)), tuple(sorted(self.module.FAILURE_CODES))
        )
        for code in sorted(self.module.FAILURE_CODES):
            with self.subTest(code=code):
                plane = self.module.failure_plane_for(code)
                self.assertIn(plane, self.module.FAILURE_PLANES)
                self.assertEqual(plane, self.module.FAILURE_PLANE_BY_CODE[code])
        self.assertEqual(
            set(self.module.FAILURE_PLANE_BY_CODE.values()), set(self.module.FAILURE_PLANES)
        )

    def test_a_failed_gate_is_not_a_candidate_terminal_outcome(self) -> None:
        """FR-014, AC-2.7: a gate rejection and a terminal failure are different facts.

        A hard gate that ran and rejected the output was previously filed as
        ``(candidate, candidate_failed)`` -- the same code AC-2.7 uses for an
        estimand-retained terminal outcome. A score bundle carries no
        ``terminal_state``, so a run that completed cleanly and failed a safety
        gate was indistinguishable from one that crashed. Those imply completely
        different remediation, and AC-2.7 lists its retained categories
        specifically: failures, timeouts, cancellations, budget exhaustion,
        abandoned branches. A gate rejection is not among them.
        """
        gate_plane, gate_code = self.module.FAILED_GATE_FAILURE
        self.assertEqual((gate_plane, gate_code), ("gate", "gate_failed"))
        self.assertEqual(self.module.failure_plane_for("gate_failed"), "gate")

        # The candidate plane keeps its AC-2.7 terminal codes, and none of them
        # is reachable from a gate rejection.
        for terminal_code in (
            "candidate_failed",
            "candidate_timed_out",
            "candidate_cancelled",
            "candidate_budget_exhausted",
            "candidate_abandoned",
        ):
            with self.subTest(code=terminal_code):
                self.assertEqual(self.module.failure_plane_for(terminal_code), "candidate")
                self.assertNotEqual(terminal_code, gate_code)

        # Both still bind the gate_failed disposition -- the distinction is the
        # plane and code, not the disposition.
        self.assertEqual(
            self.module.bind_disposition(gate_plane, gate_code, "none"), "gate_failed"
        )

    def test_the_missing_and_failed_and_duplicated_gate_cases_stay_distinct(self) -> None:
        """Three gate conditions, three pairings. None may collapse onto another."""
        pairings = {
            "missing": self.module.MISSING_GATE_FAILURE,
            "duplicated": self.module.DUPLICATE_GATE_FAILURE,
            "failed": self.module.FAILED_GATE_FAILURE,
        }
        self.assertEqual(len(set(pairings.values())), 3, pairings)
        self.assertEqual(pairings["missing"], ("evidence_boundary", "required_evidence_missing"))
        self.assertEqual(pairings["duplicated"], ("schema", "schema_invalid"))
        self.assertEqual(pairings["failed"], ("gate", "gate_failed"))
        # A missing gate is not scorable; a failed gate is a scored rejection.
        self.assertEqual(
            self.module.bind_disposition(*pairings["missing"], "none"), "non_scorable"
        )
        self.assertEqual(
            self.module.bind_disposition(*pairings["failed"], "none"), "gate_failed"
        )

    def test_the_none_code_is_the_only_member_on_the_none_plane(self) -> None:
        on_none = [
            code for code, plane in self.module.FAILURE_PLANE_BY_CODE.items() if plane == "none"
        ]
        self.assertEqual(on_none, ["none"])

    def test_a_pair_outside_the_table_fails_closed_as_schema_invalid(self) -> None:
        self.assertEqual(
            self.module.normalize_failure("candidate", "ballot_non_blind"), ("schema", "schema_invalid")
        )
        # The missing-gate pair FR-014 authors is a listed row, so it survives
        # normalization unchanged; the mis-planed variant is what fails closed.
        self.assertEqual(
            self.module.normalize_failure("evidence_boundary", "required_evidence_missing"),
            ("evidence_boundary", "required_evidence_missing"),
        )
        self.assertEqual(
            self.module.normalize_failure("schema", "required_evidence_missing"),
            ("schema", "schema_invalid"),
        )

    def test_an_unknown_code_is_refused(self) -> None:
        with self.assertRaises(self.module.ScoreBundleError):
            self.module.failure_plane_for("candidate_vibed_out")

    def test_accepted_holds_if_and_only_if_plane_code_and_reason_are_all_none(self) -> None:
        self.assertEqual(self.module.bind_disposition("none", "none", "none"), "accepted")
        for plane, code, reason in (
            ("ballot", "ballot_non_blind", "none"),
            ("none", "none", "fixture_changed"),
            ("fixture", "fixture_stale", "fixture_changed"),
        ):
            with self.subTest(plane=plane, code=code, reason=reason):
                self.assertNotEqual(self.module.bind_disposition(plane, code, reason), "accepted")

    def test_gate_failed_and_non_scorable_each_carry_a_live_plane_and_code(self) -> None:
        for disposition in ("gate_failed", "non_scorable"):
            with self.subTest(disposition=disposition):
                findings = self.module.disposition_findings(
                    {
                        "score_disposition": disposition,
                        "failure_plane": "none",
                        "failure_code": "none",
                        "invalidation_reason": "none",
                    }
                )
                self.assertTrue(findings)
        self.assertEqual(
            self.module.disposition_findings(
                {
                    "score_disposition": "gate_failed",
                    "failure_plane": "schema",
                    "failure_code": "schema_invalid",
                    "invalidation_reason": "none",
                }
            ),
            (),
        )

    def test_invalidated_carries_a_live_invalidation_reason(self) -> None:
        self.assertTrue(
            self.module.disposition_findings(
                {
                    "score_disposition": "invalidated",
                    "failure_plane": "none",
                    "failure_code": "none",
                    "invalidation_reason": "none",
                }
            )
        )

    def test_an_accepted_bundle_declaring_a_live_failure_is_refused(self) -> None:
        self.assertTrue(
            self.module.disposition_findings(
                {
                    "score_disposition": "accepted",
                    "failure_plane": "ballot",
                    "failure_code": "ballot_non_blind",
                    "invalidation_reason": "none",
                }
            )
        )

    def test_platform_alias_repointing_reuses_the_shared_disposition_reason(self) -> None:
        self.assertEqual(
            self.module.SERVICE_REROUTE_DISPOSITION_REASON, SHARED_REROUTE_DISPOSITION_REASON
        )
        record = self.module.record_service_reroute({"disposition_reasons": []})
        self.assertEqual(record["disposition_reasons"], [SHARED_REROUTE_DISPOSITION_REASON])
        self.assertEqual(record["failure_code"], "service_reroute")
        self.assertEqual(record["failure_plane"], "treatment")
        shared = load_json(SHARED_CONTRACT_DIR / "treatment-record.schema.json")
        self.assertIn(SHARED_REROUTE_DISPOSITION_REASON, canonical_json(shared))

    def test_the_capability_plane_code_is_not_repurposed_here(self) -> None:
        self.assertNotIn(CAPABILITY_PLANE_CODE, self.module.FAILURE_CODES)
        self.assertNotIn(CAPABILITY_PLANE_CODE, self.published("failure_code"))
        with self.assertRaises(self.module.ScoreBundleError):
            self.module.failure_plane_for(CAPABILITY_PLANE_CODE)

    def test_an_invalidation_is_additive_and_never_rewrites_the_prior_bundle(self) -> None:
        original = complete_bundle(self.module)
        frozen = canonical_json(original)
        for reason in self.module.INVALIDATION_REASONS:
            if reason == "none":
                continue
            with self.subTest(reason=reason):
                superseding = self.module.invalidate_bundle(original, reason)
                self.assertEqual(canonical_json(original), frozen)
                self.assertEqual(superseding["invalidation_reason"], reason)
                self.assertEqual(superseding["score_disposition"], "invalidated")
                self.assertNotEqual(
                    superseding["score_bundle_id"], original["score_bundle_id"]
                )
                self.assertEqual(
                    superseding["supersedes"],
                    {"id": original["score_bundle_id"], "digest": original["score_bundle_digest"]},
                )

    def test_an_unknown_invalidation_reason_is_refused(self) -> None:
        with self.assertRaises(self.module.ScoreBundleError):
            self.module.invalidate_bundle(complete_bundle(self.module), "budget_changed")

    def test_operator_only_evidence_blocks_publication_rather_than_being_stripped(self) -> None:
        for field in sorted(self.module.OPERATOR_ONLY_EVIDENCE_FIELDS):
            with self.subTest(field=field):
                findings = self.module.inspect_committed_evidence({field: "recorded"})
                self.assertTrue(findings)
                self.assertEqual(
                    self.module.evidence_boundary_failure(findings),
                    ("evidence_boundary", "sensitive_evidence_violation"),
                )
        self.assertEqual(self.module.inspect_committed_evidence(complete_bundle(self.module)), ())

    def test_the_repo_level_shared_contracts_are_unmodified(self) -> None:
        paths = tuple(
            str((SHARED_CONTRACT_DIR / name).relative_to(REPO_ROOT)) for name in SHARED_CONTRACT_NAMES
        )
        self.assertEqual(
            tuple(str(path.relative_to(REPO_ROOT)) for path in self.module.SHARED_CONTRACT_PATHS),
            paths,
        )
        status = git_output("status", "--porcelain", "--", *paths)
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(status.stdout.strip(), "", "a repo-level shared contract was modified")


class BlindingEvidenceTests(unittest.TestCase):
    """Blinding and ballot evidence is consumed, never asserted. A bundle with no
    leak-check finding, a failed finding, or no ballot at all fails closed instead
    of sealing as accepted (FR-014, FR-035, FR-048)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_score_bundle, "claude_score_bundle is not importable")
        self.module = claude_score_bundle
        self.passing = passing_leak_finding(self.module)
        self.failing = failing_leak_finding(self.module)

    def test_a_bundle_with_no_leak_check_evidence_never_seals_as_accepted(self) -> None:
        bundle = complete_bundle(self.module)
        self.assertNotEqual(bundle["score_disposition"], "accepted")
        self.assertFalse(bundle["blinding_residual"]["leak_check_passed"])
        self.assertEqual(self.module.disposition_findings(bundle), ())

    def test_a_bundle_with_no_ballots_never_seals_as_accepted(self) -> None:
        self.assertNotEqual(
            complete_bundle(self.module, ballots=(), adjudication=None)["score_disposition"],
            "accepted",
        )
        evidenced = complete_bundle(
            self.module, ballots=(), adjudication=None, leak_finding=self.passing
        )
        self.assertEqual(evidenced["failure_plane"], "ballot")
        self.assertEqual(evidenced["failure_code"], "ballot_missing")
        self.assertEqual(self.module.disposition_findings(evidenced), ())

    def test_a_failed_leak_check_blocks_bundle_acceptance(self) -> None:
        self.assertFalse(self.failing.passed, self.failing.hits)
        bundle = complete_bundle(self.module, leak_finding=self.failing)
        self.assertNotEqual(bundle["score_disposition"], "accepted")
        self.assertEqual(bundle["failure_plane"], "ballot")
        self.assertEqual(bundle["failure_code"], "ballot_non_blind")
        self.assertFalse(bundle["blinding_residual"]["leak_check_passed"])

    def test_a_passing_leak_check_with_two_ballots_seals_as_accepted(self) -> None:
        bundle = complete_bundle(self.module, leak_finding=self.passing)
        self.assertEqual(bundle["score_disposition"], "accepted")
        self.assertTrue(bundle["blinding_residual"]["leak_check_passed"])
        self.assertEqual(self.module.disposition_findings(bundle), ())

    def test_ballot_collection_with_no_leak_finding_is_refused(self) -> None:
        collection = self.module.collect_ballots(
            gate_results(),
            ballots=(scorer_a_ballot(self.module), scorer_b_ballot(self.module)),
            rubric=FROZEN_RUBRIC,
            current_calibrations=CURRENT_CALIBRATIONS,
        )
        self.assertFalse(collection.accepted)
        self.assertEqual(collection.ballots, ())
        self.assertEqual(collection.failure_plane, "evidence_boundary")
        self.assertEqual(collection.failure_code, "required_evidence_missing")


class EvidenceBoundaryIgnoreTests(unittest.TestCase):
    """Both halves of the evidence ignore rule: the named consolidated baseline is
    trackable, a representative per-run raw output beside it is still ignored, and
    the allow entry names the file rather than un-ignoring a directory (FR-027)."""

    def setUp(self) -> None:
        self.assertIsNotNone(claude_score_bundle, "claude_score_bundle is not importable")
        self.module = claude_score_bundle
        self.gitignore = self.module.RESULTS_GITIGNORE_PATH
        self.assertTrue(self.gitignore.is_file(), self.gitignore)
        self.lines = tuple(
            line.strip()
            for line in self.gitignore.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )

    def relative(self, path: Path) -> str:
        return str(path.relative_to(REPO_ROOT))

    def ignored(self, path: Path) -> bool:
        result = git_output("check-ignore", "-q", "--no-index", self.relative(path))
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return result.returncode == 0

    def test_the_consolidated_baseline_is_trackable(self) -> None:
        baseline = self.module.CONSOLIDATED_BASELINE_PATH
        self.assertFalse(self.ignored(baseline), f"{self.relative(baseline)} is ignored")
        if baseline.is_file():
            tracked = git_output("ls-files", "--error-unmatch", "--", self.relative(baseline))
            self.assertEqual(tracked.returncode, 0, tracked.stderr)

    def test_a_representative_per_run_raw_output_is_still_ignored(self) -> None:
        for probe in self.module.RAW_RESULT_PROBE_PATHS:
            with self.subTest(path=self.relative(probe)):
                self.assertTrue(self.ignored(probe), f"{self.relative(probe)} is not ignored")

    def test_the_allow_entry_names_the_baseline_file_explicitly(self) -> None:
        allow_entries = tuple(line for line in self.lines if line.startswith("!"))
        expected = "!" + self.module.CONSOLIDATED_BASELINE_RELATIVE_ENTRY
        self.assertIn(expected, allow_entries)
        self.assertTrue(expected.endswith(".json"))

    def test_no_allow_entry_un_ignores_a_directory(self) -> None:
        for line in self.lines:
            if not line.startswith("!"):
                continue
            with self.subTest(entry=line):
                self.assertFalse(line.endswith("/"), "a directory-wide allow was added")
                self.assertNotIn("*", line, "a wildcard allow was added")

    def test_the_results_directory_itself_stays_ignored_by_content(self) -> None:
        results_dir = self.module.RESULTS_DIR
        self.assertTrue(self.ignored(results_dir / "any-future-per-run-output.json"))
        self.assertTrue(self.ignored(results_dir / "nested" / "per-run.jsonl"))


TEST_CASES = (
    DeterministicGateTests,
    BlindedBallotTests,
    ScorerProvenanceTests,
    ClosedTaxonomyTests,
    BlindingEvidenceTests,
    EvidenceBoundaryIgnoreTests,
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-score-bundle-adjudication"))
