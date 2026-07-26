#!/usr/bin/env python3
"""Contracts for the exact-treatment runner and the demoted smoke surface.

Two surfaces are pinned here.

The **smoke surface** — the dual-platform prompt-emulation runner and its
lexical quality scorer — is demoted: every record it emits is marked non-release
evidence and carries none of the fields that would let it stand as route
qualification evidence (FR-007).

The **exact-treatment runner** at
``tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py`` is the
thin Layer 6 adapter over the single shipped materializer. It proves the exact
treatment an attempt received before any outcome may be scored: every mandatory
observation present and observed, the named agent and effective model read from
what actually ran rather than from what was requested, the bound environment
contract conformed to, the disposition derived from the shared closed taxonomy,
an immutable trace per assigned attempt, and per-arm cache isolation shown
rather than asserted (FR-009, FR-010, FR-030, FR-031, FR-032, FR-042, FR-049,
FR-051).

Every check is offline. Dispatch is proved from recorded transcript fixtures;
there are zero live model calls.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LAYER6 = TEST_ROOT / "layer6-efficiency"
SMOKE_RUNNER = LAYER6 / "run-efficiency-benchmarks.py"
LIB_DIR = TEST_ROOT / "lib"
LAYER6_LIB_DIR = LAYER6 / "lib"
for _path in (LIB_DIR, LAYER6_LIB_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from test_result import run_counted  # noqa: E402

try:  # T031…T039 deliverable — absent until the treatment runner lands.
    import claude_treatment_runner as runner  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    runner = None  # type: ignore[assignment]


NON_RELEASE_MARKER = "non_release_evidence"

# Fields that let a record stand as route qualification evidence. They belong to
# the treatment-record contract and are never carried by the smoke surface.
ROUTE_QUALIFICATION_FIELDS = frozenset(
    {
        "candidate_route_id",
        "dispatch_namespace",
        "execution_trace_id",
        "observed_model_id",
        "route_resolution",
        "scorable",
        "score_disposition",
        "treatment_disposition",
    }
)

# The shape of every smoke result written before the demotion marker existed.
HISTORICAL_SMOKE_RECORD = {
    "agent": "consensus-synthesizer",
    "model": "",
    "tokens": 1280,
    "wall_time": 12,
    "quality": 0.85,
    "exit_code": 0,
}

EXPECTED_OUTPUT = "## Answer\n\n- alpha beta gamma\n"


def import_smoke_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("l6_smoke_runner", SMOKE_RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_fixture(root: Path, expected: str | None = None) -> Path:
    fixtures = root / "fixtures"
    agent = fixtures / "stub-agent"
    agent.mkdir(parents=True)
    (agent / "input-prompt.md").write_text("stub input\n", encoding="utf-8")
    if expected is not None:
        (agent / "expected-output.md").write_text(expected, encoding="utf-8")
    return fixtures


def read_records(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def codex_stub_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    Path(argv[argv.index("-o") + 1]).write_text(EXPECTED_OUTPUT, encoding="utf-8")
    kwargs["stdout"].write(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 12}}) + "\n")
    return subprocess.CompletedProcess(argv, 0)


# ---------------------------------------------------------------------------
# Exact-treatment fixtures. Every one is a recorded artifact: no live dispatch.
# ---------------------------------------------------------------------------

ASSIGNED_AT = "2026-07-24T12:00:00Z"

# A recorded session transcript. The spawn the platform actually performed is
# deliberately a different agent from the one the dispatch request asked for.
TRANSCRIPT = {
    "events": [
        {"type": "user_turn", "text": "run the calibration objective"},
        {"type": "agent_spawn", "agent": "speckit-pro:autopilot-planner"},
        {"type": "agent_result", "status": "completed"},
    ]
}

# The per-model usage breakdown, the only admissible source of the effective
# model. The requested alias is never a substitute for it.
USAGE_BREAKDOWN = {
    "claude-opus-5-20260514": {
        "input_tokens": 1200,
        "output_tokens": 340,
        "cached_input_tokens": 800,
        "reasoning_output_tokens": 210,
    }
}

UNSET_PROOF = {
    "fallback_model_unset": True,
    "fallbackModel_unset": True,
    "claude_code_subagent_model_unset": True,
    "available_models_absent": True,
    "enforce_available_models_observed": None,
    "config_dir_isolation": "none",
    "inherit_equivalent_to_unset": None,
    "org_restriction_gap": None,
}

TRACE_BINDINGS = {
    "objective_binding": {
        "candidate_route_id": "route-opus-high",
        "agent_contract_id": "agent-autopilot-planner",
        "runtime_capability_snapshot_id": "sha256:" + "1" * 64,
        "route_resolution_id": "sha256:" + "2" * 64,
        "experiment_policy_id": "sha256:" + "3" * 64,
    },
    "controlled_environment_id": "sha256:" + "4" * 64,
    "client_identity_id": "sha256:" + "5" * 64,
    "surface": "cli",
    "repository_revision": "a" * 40,
    "repository_tree_digest": "sha256:" + "6" * 64,
    "work_item_kind": "objective",
    "work_item_id": "calibration-objective-1",
    "launch_id": "launch-fixture-calibration-1",
    "consumption_evidence_digest": "sha256:" + "7" * 64,
    "context": {"threadId": "thread-1", "turnId": "turn-1"},
    "raw_token_vector": {
        "input_tokens": 1200,
        "output_tokens": 340,
        "cached_input_tokens": 800,
        "reasoning_output_tokens": 210,
    },
    "wall_time_ms": 4200,
    "retries": 0,
}


def digest_of_canonical(value: object) -> str:
    """The CAR-002 canonical serialization: sorted keys, minimal separators."""
    import hashlib

    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def observed_environment(**overrides: object) -> dict[str, object]:
    """A run's observed environment, conformant unless overridden."""
    environment: dict[str, object] = {
        "fast_mode_state": "off",
        "client_version": "2.1.240 (Claude Code)",
        "parent_session_configuration": "opus/high",
        "env_override_proof": dict(UNSET_PROOF),
        "authentication_mode": "subscription",
    }
    environment.update(overrides)
    return environment


def complete_observations(manifest: dict[str, object]) -> list[dict[str, object]]:
    """One fully observed entry per mandatory field path."""
    return [
        {
            "field_path": field_path,
            "observation_state": "observed_value",
            "classification": "stable_native",
            "value": f"observed:{field_path}",
        }
        for field_path in runner.mandatory_field_paths(manifest)
    ]


def treatment_record(manifest: dict[str, object], **overrides: object) -> dict[str, object]:
    """A pre-score treatment record, fully proven unless overridden."""
    record: dict[str, object] = {
        "observations": complete_observations(manifest),
        "materialization_proof": {"content_hash": "sha256:" + "8" * 64, "verified": True},
        "installed_policy_proof": False,
        "configured_route_proof_matches": True,
        "route_change_monitoring_complete": True,
        "environment_conformant": True,
        "scorable": True,
        "conditions": (),
    }
    record.update(overrides)
    return record


class SmokeSurfaceDemotionTests(unittest.TestCase):
    """The prompt-emulation runner and the lexical quality scorer are smoke
    surfaces whose results are never route qualification evidence (FR-007)."""

    def setUp(self) -> None:
        self.runner = import_smoke_runner()

    def test_every_emitted_smoke_record_is_labeled_non_release(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixtures = make_fixture(root)
            executable = root / "claude"
            executable.write_text("stub\n", encoding="utf-8")
            results = root / "results.json"
            writer = self.runner.ResultWriter(results)
            writer.write()
            self.assertEqual(read_records(results), [])

            failed = subprocess.CompletedProcess([], 1, stdout="", stderr="refused")
            with contextlib.redirect_stdout(io.StringIO()):
                with mock.patch.object(self.runner.subprocess, "run", return_value=failed):
                    self.runner.run_benchmark("stub-agent", "", fixtures, writer, executable)
                with mock.patch.object(self.runner.subprocess, "run", side_effect=OSError("spawn failed")):
                    self.runner.run_benchmark("stub-agent", "", fixtures, writer, executable)
                with mock.patch.object(self.runner.subprocess, "run", side_effect=codex_stub_run):
                    self.runner.run_benchmark_codex("stub-agent", "high", fixtures, writer, executable)

            records = read_records(results)

        self.assertEqual([record["exit_code"] for record in records], [1, 127, 0])
        for record in records:
            with self.subTest(msg=f"exit_code={record['exit_code']}"):
                self.assertIs(record.get(NON_RELEASE_MARKER), True, record)

    def test_lexical_quality_scores_are_emitted_only_as_non_release_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixtures = make_fixture(root, EXPECTED_OUTPUT)
            executable = root / "claude"
            executable.write_text("stub\n", encoding="utf-8")
            results = root / "results.json"
            writer = self.runner.ResultWriter(results)
            completed = subprocess.CompletedProcess(
                [],
                0,
                stdout=json.dumps(
                    {"result": EXPECTED_OUTPUT, "usage": {"input_tokens": 3, "output_tokens": 4}}
                ),
                stderr="",
            )
            with contextlib.redirect_stdout(io.StringIO()):
                with mock.patch.object(self.runner.subprocess, "run", return_value=completed):
                    self.runner.run_benchmark("stub-agent", "", fixtures, writer, executable)

            record = read_records(results)[0]

        scored = self.runner.QUALITY_SCORER.score_text(EXPECTED_OUTPUT, EXPECTED_OUTPUT)
        self.assertEqual(record["quality"], scored["overall"])
        self.assertIs(record.get(NON_RELEASE_MARKER), True, record)

    def test_smoke_results_cannot_stand_as_route_qualification_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            results = Path(temporary) / "results.json"
            writer = self.runner.ResultWriter(results)
            writer.append("stub-agent", "", 1280, 12, 0.85, 0)
            record = read_records(results)[0]

        self.assertIs(record.get(NON_RELEASE_MARKER), True, record)
        self.assertEqual(ROUTE_QUALIFICATION_FIELDS.intersection(record), set())
        self.assertEqual(ROUTE_QUALIFICATION_FIELDS.intersection(HISTORICAL_SMOKE_RECORD), set())
        self.assertEqual(set(record) - set(HISTORICAL_SMOKE_RECORD), {NON_RELEASE_MARKER})


class TreatmentRunnerTestCase(unittest.TestCase):
    """Shared guard so a missing runner module fails loudly, never silently."""

    def setUp(self) -> None:
        if runner is None:  # pragma: no cover - pre-implementation guard
            self.fail("claude_treatment_runner is not importable from the Layer 6 lib")


class MandatoryObservationTests(TreatmentRunnerTestCase):
    """No outcome is scored until every mandatory observation is present (FR-009)."""

    def test_the_published_manifest_names_every_required_evidence_category(self) -> None:
        manifest = runner.load_mandatory_manifest()

        self.assertEqual(manifest["record_kind"], "mandatory_observation_manifest")
        self.assertEqual(manifest["missing_field_failure_code"], runner.MANDATORY_TELEMETRY_MISSING)
        categories = {entry["category"] for entry in manifest["required_fields"]}
        self.assertEqual(categories, set(runner.REQUIRED_EVIDENCE_CATEGORIES))
        self.assertTrue(manifest["required_fields"], "the manifest must name at least one field")
        # Nullable exemptions are the complement, never an overlap: a field cannot
        # be mandatory and exempt from the non-null rule at the same time.
        self.assertEqual(
            set(manifest["nullable_exemptions"]) & set(runner.mandatory_field_paths(manifest)),
            set(),
        )

    def test_a_complete_observation_set_fires_no_code(self) -> None:
        manifest = runner.load_mandatory_manifest()
        observations = complete_observations(manifest)

        for observation in observations:
            with self.subTest(msg=observation["field_path"]):
                self.assertEqual(observation["observation_state"], "observed_value")
                self.assertIsNotNone(observation["value"])
                self.assertNotEqual(observation["classification"], "unavailable")

        self.assertEqual(runner.check_mandatory_observations(observations, manifest=manifest), ())

    def test_an_unavailable_or_null_mandatory_field_blocks_scoring(self) -> None:
        manifest = runner.load_mandatory_manifest()
        target = runner.mandatory_field_paths(manifest)[0]

        degraded = {
            "unavailable_classification": {"classification": "unavailable"},
            "unavailable_state": {"observation_state": "unavailable", "value": None},
            "explicit_null": {"observation_state": "explicit_null", "value": None},
            "absent": None,
        }
        for label, patch in degraded.items():
            with self.subTest(msg=label):
                observations = complete_observations(manifest)
                if patch is None:
                    observations = [item for item in observations if item["field_path"] != target]
                else:
                    for item in observations:
                        if item["field_path"] == target:
                            item.update(patch)
                codes = runner.check_mandatory_observations(observations, manifest=manifest)
                self.assertEqual(codes, (runner.MANDATORY_TELEMETRY_MISSING,))
                self.assertFalse(
                    runner.evaluate_score_eligibility(treatment_record(manifest, observations=observations)).eligible
                )

    def test_a_nullable_non_manifest_field_stays_permitted(self) -> None:
        manifest = runner.load_mandatory_manifest()
        observations = complete_observations(manifest)
        exempt = manifest["nullable_exemptions"][0]
        observations.append(
            {
                "field_path": exempt,
                "observation_state": "explicit_null",
                "classification": "conditional",
                "value": None,
            }
        )

        self.assertEqual(runner.check_mandatory_observations(observations, manifest=manifest), ())

    def test_the_cached_manifest_is_not_mutable_through_one_of_its_nested_lists(self) -> None:
        # A read-only mapping proxy guards its top level only. If the nested
        # lists are handed out by reference, one caller's edit silently rewrites
        # the manifest every later caller reads.
        manifest = runner.load_mandatory_manifest()
        manifest["required_fields"].clear()
        manifest["nullable_exemptions"].append("injected.field.path")

        refreshed = runner.load_mandatory_manifest()
        self.assertTrue(refreshed["required_fields"], "the cached manifest lost its required fields")
        self.assertNotIn("injected.field.path", refreshed["nullable_exemptions"])


class RealDispatchRecordingTests(TreatmentRunnerTestCase):
    """What ran is read from the run, never from the request (FR-009, SC-021)."""

    def test_the_named_agent_is_the_namespaced_spawn_read_from_the_transcript(self) -> None:
        record = runner.record_exact_treatment(
            transcript=TRANSCRIPT,
            usage_breakdown=USAGE_BREAKDOWN,
            dispatch_request={"agent": "speckit-pro:autopilot-implementer"},
        )

        self.assertEqual(record["dispatch_namespace"], "speckit-pro:autopilot-planner")
        self.assertNotEqual(record["dispatch_namespace"], "speckit-pro:autopilot-implementer")
        self.assertEqual(record["dispatch_namespace_source"], runner.SOURCE_RUN_TRANSCRIPT)

    def test_a_transcript_with_no_namespaced_spawn_yields_no_named_agent(self) -> None:
        bare = {"events": [{"type": "agent_spawn", "agent": "autopilot-planner"}]}

        self.assertIsNone(runner.read_dispatch_namespace(bare))
        record = runner.record_exact_treatment(
            transcript=bare,
            usage_breakdown=USAGE_BREAKDOWN,
            dispatch_request={"agent": "speckit-pro:autopilot-planner"},
        )
        self.assertIsNone(record["dispatch_namespace"])

    def test_the_effective_model_is_read_only_from_the_per_model_usage_breakdown(self) -> None:
        record = runner.record_exact_treatment(
            transcript=TRANSCRIPT,
            usage_breakdown=USAGE_BREAKDOWN,
            dispatch_request={"agent": "speckit-pro:autopilot-planner", "model": "opus"},
        )

        self.assertEqual(record["observed_model_id"], "claude-opus-5-20260514")
        self.assertEqual(record["observed_model_id_source"], runner.SOURCE_PER_MODEL_USAGE)

    def test_a_missing_usage_breakdown_never_falls_back_to_configuration(self) -> None:
        for label, breakdown in {"empty": {}, "absent": None}.items():
            with self.subTest(msg=label):
                record = runner.record_exact_treatment(
                    transcript=TRANSCRIPT,
                    usage_breakdown=breakdown,
                    dispatch_request={"agent": "speckit-pro:autopilot-planner", "model": "opus"},
                )
                self.assertIsNone(record["observed_model_id"])
                self.assertNotIn("opus", json.dumps(record["observed_model_id"]))


class EnvironmentContractTests(TreatmentRunnerTestCase):
    """Recording is not constraining: a bound contract is compared (FR-042, FR-051)."""

    def test_the_bound_contract_pins_every_required_environment_value(self) -> None:
        contract = runner.bind_environment_contract()

        self.assertEqual(contract["schema_version"], runner.ENVIRONMENT_CONTRACT_VERSION)
        self.assertEqual(contract["fast_mode_state"], "off")
        self.assertEqual(contract["authentication_mode"], "subscription")
        self.assertEqual(len(contract["client_version_range"]), 2)
        self.assertIsNotNone(contract["parent_session_configuration"])
        self.assertEqual(set(contract["env_override_proof"]), set(runner.ENV_OVERRIDE_PROOF_MEMBERS))
        self.assertEqual(len(runner.ENV_OVERRIDE_PROOF_MEMBERS), 8)
        self.assertIs(contract["env_override_proof"]["claude_code_subagent_model_unset"], True)

    def test_a_partial_override_preserves_every_other_pinned_proof(self) -> None:
        """Overriding one proof member must not delete the other seven.

        A shallow ``dict.update`` replaced the whole ``env_override_proof``
        block with the caller's partial mapping, so the contract silently
        stopped pinning the members it no longer carried, and
        ``check_environment_conformance`` raised ``KeyError`` on the first
        observed member the truncated contract had lost.
        """
        contract = runner.bind_environment_contract(
            env_override_proof={"fallback_model_unset": False}
        )

        self.assertEqual(
            set(contract["env_override_proof"]), set(runner.ENV_OVERRIDE_PROOF_MEMBERS)
        )
        self.assertIs(contract["env_override_proof"]["fallback_model_unset"], False)
        self.assertIs(contract["env_override_proof"]["fallbackModel_unset"], True)

        # The conformance check returns a verdict rather than raising.
        result = runner.check_environment_conformance(contract, observed_environment())
        self.assertEqual(result.status, runner.ENVIRONMENT_DIVERGENT)
        self.assertIn("env_override_proof.fallback_model_unset", result.diverged_fields)

    def test_a_top_level_override_still_replaces_a_scalar(self) -> None:
        contract = runner.bind_environment_contract(fast_mode_state="on")
        self.assertEqual(contract["fast_mode_state"], "on")
        self.assertEqual(
            set(contract["env_override_proof"]), set(runner.ENV_OVERRIDE_PROOF_MEMBERS)
        )

    def test_a_conformant_environment_is_admitted(self) -> None:
        result = runner.check_environment_conformance(runner.bind_environment_contract(), observed_environment())

        self.assertEqual(result.status, runner.ENVIRONMENT_CONFORMANT)
        self.assertEqual(result.failure_plane, "none")
        self.assertEqual(result.failure_code, "none")
        self.assertIs(result.blocks_scoring, False)

    def test_a_confirmed_divergence_lands_on_the_treatment_plane(self) -> None:
        divergences = {
            "fast_mode": {"fast_mode_state": "on"},
            "client_version": {"client_version": "9.9.9 (Claude Code)"},
            "parent_session": {"parent_session_configuration": "sonnet/low"},
            "subagent_override": {"env_override_proof": dict(UNSET_PROOF, claude_code_subagent_model_unset=False)},
            "authentication_mode": {"authentication_mode": "api_key"},
        }
        for label, patch in divergences.items():
            with self.subTest(msg=label):
                result = runner.check_environment_conformance(
                    runner.bind_environment_contract(), observed_environment(**patch)
                )
                self.assertEqual(result.status, runner.ENVIRONMENT_DIVERGENT)
                self.assertEqual(result.failure_plane, runner.PLANE_TREATMENT)
                self.assertEqual(result.failure_code, runner.TREATMENT_INFRASTRUCTURE_FAILURE)
                self.assertIs(result.blocks_scoring, True)
                self.assertIn(label.replace("subagent_override", "env_override_proof"), " ".join(result.diverged_fields))

    def test_fast_mode_on_is_refused_and_never_repaired(self) -> None:
        """FR-051: "frozen off" is an admission precondition, not an action.

        Fast mode is Opus-only and usage-credit-billed. A harness that switched
        it on would spend an operator's credits for a speed characteristic no
        requirement asks for; one that switched it off would silently revoke a
        setting the operator chose. So an attempt observed with fast mode on is
        refused and recorded, never repaired by changing the environment.
        """
        observed = observed_environment(fast_mode_state="on")
        before = dict(observed)

        result = runner.check_environment_conformance(
            runner.bind_environment_contract(), observed
        )

        self.assertIs(result.blocks_scoring, True)
        self.assertIn("fast_mode_state", " ".join(result.diverged_fields))
        # The observed environment is evidence, not a thing to edit. Conformance
        # checking must leave it byte-identical.
        self.assertEqual(observed, before)
        self.assertEqual(observed["fast_mode_state"], "on")

    def test_the_runner_exposes_no_way_to_set_fast_mode(self) -> None:
        """The plugin never grants or revokes this setting.

        The contract may *declare* the required state and the checker may
        *compare* against it, but nothing in the runner may write it.
        """
        import inspect

        source = inspect.getsource(runner)
        for forbidden in (
            'os.environ["CLAUDE_FAST_MODE"]',
            "os.environ['CLAUDE_FAST_MODE']",
            "--fast",
            "/fast",
        ):
            self.assertNotIn(forbidden, source, f"runner must not emit {forbidden!r}")

    def test_an_unobservable_environment_lands_on_the_evidence_boundary_plane(self) -> None:
        result = runner.check_environment_conformance(
            runner.bind_environment_contract(), observed_environment(fast_mode_state=None)
        )

        self.assertEqual(result.status, runner.ENVIRONMENT_UNOBSERVABLE)
        self.assertEqual(result.failure_plane, runner.PLANE_EVIDENCE_BOUNDARY)
        self.assertEqual(result.failure_code, runner.REQUIRED_EVIDENCE_MISSING)
        self.assertEqual(result.terminal_member, runner.TERMINAL_INCONCLUSIVE)
        self.assertIs(result.blocks_scoring, True)

    def test_the_two_environment_branches_never_share_a_code(self) -> None:
        divergent = runner.check_environment_conformance(
            runner.bind_environment_contract(), observed_environment(fast_mode_state="on")
        )
        unobservable = runner.check_environment_conformance(
            runner.bind_environment_contract(), observed_environment(fast_mode_state=None)
        )

        self.assertNotEqual(divergent.failure_code, unobservable.failure_code)
        self.assertNotEqual(divergent.failure_plane, unobservable.failure_plane)

    def test_the_exclusion_count_is_reported_alongside_every_qualification_claim(self) -> None:
        contract = runner.bind_environment_contract()
        results = [
            runner.check_environment_conformance(contract, observed_environment()),
            runner.check_environment_conformance(contract, observed_environment(fast_mode_state="on")),
            runner.check_environment_conformance(contract, observed_environment(authentication_mode="api_key")),
            runner.check_environment_conformance(contract, observed_environment(fast_mode_state=None)),
        ]
        report = runner.environment_exclusion_report(results)

        self.assertEqual(report["attempts_evaluated"], 4)
        self.assertEqual(report["attempts_excluded"], 3)
        self.assertEqual(report["excluded_by_code"][runner.TREATMENT_INFRASTRUCTURE_FAILURE], 2)
        self.assertEqual(report["excluded_by_code"][runner.REQUIRED_EVIDENCE_MISSING], 1)


class ScoreEligibilityTests(TreatmentRunnerTestCase):
    """Eligibility is conjunctive; disposition is bucket precedence (FR-030, FR-031)."""

    def test_the_predicate_admits_only_a_fully_proven_record(self) -> None:
        manifest = runner.load_mandatory_manifest()
        record = treatment_record(manifest)
        verdict = runner.evaluate_score_eligibility(record)

        self.assertIs(verdict.eligible, True)
        self.assertEqual(verdict.treatment_disposition, "proven")
        self.assertEqual(verdict.blocking_reasons, ())

    def test_every_conjunct_is_independently_necessary(self) -> None:
        manifest = runner.load_mandatory_manifest()
        removals = {
            "materialization_proof": {"materialization_proof": None, "installed_policy_proof": False},
            "configured_route_proof": {"configured_route_proof_matches": False},
            "route_change_monitoring": {"route_change_monitoring_complete": False},
            "environment_conformance": {"environment_conformant": False},
        }
        for label, patch in removals.items():
            with self.subTest(msg=label):
                verdict = runner.evaluate_score_eligibility(treatment_record(manifest, **patch))
                self.assertIs(verdict.eligible, False)
                self.assertIn(label, verdict.blocking_reasons)

    def test_either_proof_branch_satisfies_the_materialization_conjunct(self) -> None:
        manifest = runner.load_mandatory_manifest()

        installed = treatment_record(manifest, materialization_proof=None, installed_policy_proof=True)
        self.assertIs(runner.evaluate_score_eligibility(installed).eligible, True)
        materialized = treatment_record(manifest, installed_policy_proof=False)
        self.assertIs(runner.evaluate_score_eligibility(materialized).eligible, True)

    def test_the_scorable_flag_is_necessary_but_never_sufficient(self) -> None:
        manifest = runner.load_mandatory_manifest()

        blocked = runner.evaluate_score_eligibility(treatment_record(manifest, scorable=False))
        self.assertIs(blocked.eligible, False)
        self.assertIn("scorable", blocked.blocking_reasons)

        # scorable=true alone admits nothing: it speaks only to platform-initiated
        # route change and is derived solely from the record class.
        alone = runner.evaluate_score_eligibility(
            treatment_record(manifest, scorable=True, configured_route_proof_matches=False)
        )
        self.assertIs(alone.eligible, False)

    def test_co_occurring_disqualifiers_are_unioned_and_never_discarded(self) -> None:
        manifest = runner.load_mandatory_manifest()
        fired = ("agent_mismatch", "service_reroute_requested_route_non_scorable", "delivery_canary_failure")
        verdict = runner.evaluate_score_eligibility(treatment_record(manifest, conditions=fired))

        self.assertEqual(set(verdict.disposition_reasons), set(fired))
        self.assertEqual(len(verdict.disposition_reasons), len(fired))
        self.assertIs(verdict.eligible, False)
        for code in fired:
            with self.subTest(msg=code):
                self.assertIn(code, verdict.disposition_reasons)

    def test_the_terminal_disposition_is_the_highest_precedence_bucket(self) -> None:
        manifest = runner.load_mandatory_manifest()
        self.assertEqual(
            runner.DISPOSITION_PRECEDENCE,
            ("hard_fail", "non_scorable_rerouted", "unknown", "proven"),
        )

        cases = {
            "hard_fail": (
                ("agent_mismatch", "service_reroute_requested_route_non_scorable", "delivery_canary_failure"),
                "hard_fail",
            ),
            "non_scorable_rerouted": (
                ("service_reroute_requested_route_non_scorable", "delivery_canary_failure"),
                "non_scorable_rerouted",
            ),
            "unknown": (("delivery_canary_failure",), "unknown"),
            "proven": ((), "proven"),
        }
        for label, (fired, expected) in cases.items():
            with self.subTest(msg=label):
                verdict = runner.evaluate_score_eligibility(treatment_record(manifest, conditions=fired))
                self.assertEqual(verdict.treatment_disposition, expected)
                self.assertEqual(set(verdict.disposition_reasons) & set(fired), set(fired))

    def test_the_disposition_vocabulary_is_read_from_the_shared_contract(self) -> None:
        shared = json.loads(
            (LAYER6 / "contracts" / "treatment-record.schema.json").read_text(encoding="utf-8")
        )
        trace = shared["$defs"]["treatmentTrace"]["properties"]

        self.assertEqual(
            set(runner.TREATMENT_DISPOSITIONS), set(trace["treatment_disposition"]["enum"])
        )
        self.assertEqual(
            set(runner.DISPOSITION_REASON_CODES), set(trace["disposition_reasons"]["items"]["enum"])
        )
        self.assertEqual(set(runner.DISPOSITION_PRECEDENCE), set(runner.TREATMENT_DISPOSITIONS))


class ExecutionTraceBindingTests(TreatmentRunnerTestCase):
    """Traces are immutable and bundles reference them by ID and digest (FR-010, FR-032)."""

    def test_every_assigned_attempt_receives_its_own_immutable_trace(self) -> None:
        first = runner.new_execution_trace(TRACE_BINDINGS, assignment_id="pair-1-arm-a", assigned_at=ASSIGNED_AT)
        second = runner.new_execution_trace(TRACE_BINDINGS, assignment_id="pair-1-arm-b", assigned_at=ASSIGNED_AT)

        self.assertNotEqual(first["execution_trace_id"], second["execution_trace_id"])
        self.assertRegex(first["execution_trace_id"], r"^sha256:[0-9a-f]{64}$")
        with self.assertRaises(TypeError):
            first["execution_trace_id"] = "sha256:" + "0" * 64

    def test_the_frozen_outcome_shape_is_not_extended(self) -> None:
        trace = runner.new_execution_trace(TRACE_BINDINGS, assignment_id="pair-1-arm-a", assigned_at=ASSIGNED_AT)

        self.assertEqual(set(trace["outcome"]), {"status", "telemetry_ref", "notes"})
        self.assertIsNone(trace["acceptance"])

    def test_the_trace_digest_is_canonical_json_recomputed_at_acceptance_and_replay(self) -> None:
        trace = runner.new_execution_trace(TRACE_BINDINGS, assignment_id="pair-1-arm-a", assigned_at=ASSIGNED_AT)
        expected = digest_of_canonical(dict(trace))

        self.assertEqual(runner.trace_digest(trace), expected)
        self.assertEqual(runner.trace_digest(trace), runner.trace_digest(trace))

    def test_a_bundle_references_a_trace_without_embedding_or_mutating_it(self) -> None:
        trace = runner.new_execution_trace(TRACE_BINDINGS, assignment_id="pair-1-arm-a", assigned_at=ASSIGNED_AT)
        bundle = runner.bind_score_bundle(trace)

        self.assertEqual(bundle["execution_trace_binding"]["id"], trace["execution_trace_id"])
        self.assertEqual(bundle["execution_trace_binding"]["digest"], runner.trace_digest(trace))
        self.assertNotIn("observations", bundle)
        self.assertEqual(runner.verify_bundle_references(bundle, [trace]), ())

    def test_a_mismatched_or_dangling_reference_blocks_the_decision_bundle(self) -> None:
        trace = runner.new_execution_trace(TRACE_BINDINGS, assignment_id="pair-1-arm-a", assigned_at=ASSIGNED_AT)

        dangling = runner.bind_score_bundle(trace)
        self.assertEqual(
            runner.verify_bundle_references(dangling, []),
            (runner.TRACE_REFERENCE_INTEGRITY_FAILURE,),
        )

        mismatched = runner.bind_score_bundle(trace)
        mismatched["execution_trace_binding"] = dict(
            mismatched["execution_trace_binding"], digest="sha256:" + "0" * 64
        )
        self.assertEqual(
            runner.verify_bundle_references(mismatched, [trace]),
            (runner.TRACE_REFERENCE_INTEGRITY_FAILURE,),
        )
        # The invalidation blocks; neither artifact is repaired by rewrite.
        self.assertEqual(runner.trace_digest(trace), digest_of_canonical(dict(trace)))

    def test_the_projections_are_re_derived_from_the_digest_verified_trace(self) -> None:
        trace = runner.new_execution_trace(TRACE_BINDINGS, assignment_id="pair-1-arm-a", assigned_at=ASSIGNED_AT)
        bundle = runner.bind_score_bundle(trace)

        self.assertEqual(bundle["resource_vector"], runner.derive_resource_vector(trace))
        self.assertEqual(bundle["reasoning_token_report"], runner.derive_reasoning_token_report(trace))
        self.assertIn("reasoning_output_tokens", bundle["reasoning_token_report"])
        self.assertIs(bundle["reasoning_token_report"]["decision_bearing"], False)
        self.assertEqual(runner.verify_bundle_projections(bundle, trace), ())

    def test_a_disagreeing_projection_fails_closed_on_the_schema_plane(self) -> None:
        trace = runner.new_execution_trace(TRACE_BINDINGS, assignment_id="pair-1-arm-a", assigned_at=ASSIGNED_AT)

        for field in ("resource_vector", "reasoning_token_report"):
            with self.subTest(msg=field):
                bundle = runner.bind_score_bundle(trace)
                bundle[field] = dict(bundle[field], input_tokens=999_999, reasoning_output_tokens=999_999)
                self.assertEqual(
                    runner.verify_bundle_projections(bundle, trace),
                    (runner.BINDING_DIGEST_MISMATCH,),
                )
                self.assertEqual(runner.failure_plane_for(runner.BINDING_DIGEST_MISMATCH), runner.PLANE_SCHEMA)


class CacheIsolationTests(TreatmentRunnerTestCase):
    """Isolation is shown per arm, never asserted in prose (FR-049, SC-024)."""

    def test_paired_arms_record_distinct_roots_and_their_disjointness(self) -> None:
        arm_a, arm_b = runner.observe_paired_cache_isolation("arm-a-ephemeral", "arm-b-ephemeral")

        for label, arm in (("arm_a", arm_a), ("arm_b", arm_b)):
            with self.subTest(msg=label):
                self.assertEqual(arm["status"], runner.CACHE_OBSERVED_DISJOINT)
                self.assertIs(arm["roots_disjoint"], True)
                self.assertRegex(arm["arm_cache_root_digest"], r"^sha256:[0-9a-f]{64}$")
                self.assertNotEqual(arm["arm_cache_root_digest"], arm["paired_arm_cache_root_digest"])

        self.assertEqual(arm_a["arm_cache_root_digest"], arm_b["paired_arm_cache_root_digest"])
        self.assertIs(runner.pair_contributes_resource_comparison(arm_a, arm_b), True)

    def test_roots_are_recorded_as_digests_and_never_as_paths(self) -> None:
        arm_a, arm_b = runner.observe_paired_cache_isolation("arm-a-ephemeral", "arm-b-ephemeral")

        for key, value in {**arm_a, **arm_b}.items():
            with self.subTest(msg=key):
                self.assertNotIn("/", str(value))

    def test_a_shared_root_is_a_confirmed_breach_on_the_infrastructure_plane(self) -> None:
        arm_a, arm_b = runner.observe_paired_cache_isolation("shared-root", "shared-root")

        self.assertEqual(arm_a["status"], runner.CACHE_OBSERVED_SHARED)
        self.assertIs(arm_a["roots_disjoint"], False)
        self.assertIs(runner.pair_contributes_resource_comparison(arm_a, arm_b), False)
        self.assertEqual(runner.failure_plane_for(runner.INFRASTRUCTURE_FAILURE), runner.PLANE_INFRASTRUCTURE)

    def test_an_unobserved_root_is_an_evidence_completeness_failure(self) -> None:
        arm_a, arm_b = runner.observe_paired_cache_isolation("arm-a-ephemeral", None)

        self.assertEqual(arm_b["status"], runner.CACHE_UNOBSERVED)
        self.assertIsNone(arm_b["arm_cache_root_digest"])
        self.assertIsNone(arm_b["roots_disjoint"])
        self.assertIs(runner.pair_contributes_resource_comparison(arm_a, arm_b), False)
        self.assertEqual(runner.failure_plane_for(runner.REQUIRED_EVIDENCE_MISSING), runner.PLANE_EVIDENCE_BOUNDARY)


TEST_CASES = (
    SmokeSurfaceDemotionTests,
    MandatoryObservationTests,
    RealDispatchRecordingTests,
    EnvironmentContractTests,
    ScoreEligibilityTests,
    ExecutionTraceBindingTests,
    CacheIsolationTests,
)


if __name__ == "__main__":
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite(loader.loadTestsFromTestCase(case) for case in TEST_CASES)
    raise SystemExit(run_counted(suite, label="test-exact-treatment-runner"))
