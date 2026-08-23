#!/usr/bin/env python3
"""Deterministic tests for the G56R-005 Codex fallback simulation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CONTRACT_ROOT = ROOT / "tests/speckit-pro/layer6-efficiency/contracts-codex-fallback"
CORPUS_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/fixtures-codex-fallback/fallback-recovery-corpus.json"
MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py"
SOURCE_ROOT = ROOT / "speckit-pro/codex-agents"

CONTRACT_NAMES = (
    "route-policy.schema.json",
    "route-resolution-report.schema.json",
    "recovery-record.schema.json",
)
SCHEMA_ID_PREFIX = "https://racecraft.dev/schemas/g56r-005/"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_runtime():
    spec = importlib.util.spec_from_file_location("codex_route_fallback", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def route(
    route_id: str,
    *,
    model_present: bool = True,
    effort_supported: bool = True,
    discovery_available: bool = True,
    availability_succeeded: bool = True,
    treatment_succeeded: bool = True,
    treatment_digest: str = "sha256:" + "a" * 64,
) -> dict:
    return {
        "route_id": route_id,
        "model": f"model-{route_id}",
        "effort": "high",
        "model_present": model_present,
        "effort_supported": effort_supported,
        "capability_discovery_available": discovery_available,
        "availability_probe": {"attempted": discovery_available, "succeeded": availability_succeeded},
        "treatment_probe": {"attempted": availability_succeeded, "succeeded": treatment_succeeded},
        "non_route_treatment_digest": treatment_digest,
        "declaration_source": "local",
    }


def policy(preferred: dict, *fallbacks: dict, strict_status: str = "absent") -> dict:
    return {
        "schema_version": "1.0.0",
        "policy_id": "fixture-policy",
        "source_roster_id": "sha256:" + "b" * 64,
        "agent": {
            "name": "fixture-agent",
            "role_classification": "required_core",
            "non_route_treatment_digest": "sha256:" + "a" * 64,
        },
        "preferred_route": preferred,
        "fallback_routes": list(fallbacks),
        "strict_override": {"status": strict_status},
        "helper_state": {
            "available": True,
            "no_helper_continuation_qualified": False,
            "helper_route_attempts": 0,
        },
        "fake_home": {
            "seed_state_id": "sha256:" + "c" * 64,
            "temporary_root_required": True,
        },
        "budgets": {
            "max_retries": 0,
            "max_elapsed_units": 1,
            "max_fanout": 1,
            "max_context_units": 0,
            "cancellation_point": "none",
            "max_escalations": 0,
        },
    }


class ContractAndCorpusTests(unittest.TestCase):
    def test_contract_identity_is_closed_and_feature_named(self) -> None:
        self.assertEqual(
            sorted(path.name for path in CONTRACT_ROOT.glob("*.schema.json")),
            sorted(CONTRACT_NAMES),
        )
        for name in CONTRACT_NAMES:
            with self.subTest(name=name):
                document = load_json(CONTRACT_ROOT / name)
                self.assertEqual(document["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(document["$id"], SCHEMA_ID_PREFIX + name)
                self.assertEqual(document["properties"]["schema_version"]["const"], "1.0.0")
                self.assertFalse(document["additionalProperties"])

    def test_route_policy_declares_every_supported_declaration_source(self) -> None:
        document = load_json(CONTRACT_ROOT / "route-policy.schema.json")
        declaration_source = document["$defs"]["routeCandidate"]["properties"]["declaration_source"]
        self.assertEqual(
            declaration_source["enum"],
            [
                "local",
                "inherited_model",
                "inherited_effort",
                "generic_substitution",
                "unqualified_adjacent",
            ],
        )

    def test_resolution_report_binds_recovery_record_to_its_closed_schema(self) -> None:
        document = load_json(CONTRACT_ROOT / "route-resolution-report.schema.json")
        self.assertEqual(
            document["properties"]["recovery_record"],
            {"oneOf": [{"type": "null"}, {"$ref": "recovery-record.schema.json"}]},
        )

    def test_policy_fixture_helper_supplies_closed_neutral_defaults(self) -> None:
        fixture = policy(route("preferred"))
        self.assertEqual(
            fixture["helper_state"],
            {
                "available": True,
                "no_helper_continuation_qualified": False,
                "helper_route_attempts": 0,
            },
        )
        self.assertEqual(
            fixture["fake_home"],
            {
                "seed_state_id": "sha256:" + "c" * 64,
                "temporary_root_required": True,
            },
        )
        self.assertEqual(
            fixture["budgets"],
            {
                "max_retries": 0,
                "max_elapsed_units": 1,
                "max_fanout": 1,
                "max_context_units": 0,
                "cancellation_point": "none",
                "max_escalations": 0,
            },
        )

    def test_fixture_covers_every_declared_required_scenario(self) -> None:
        corpus = load_json(CORPUS_PATH)
        covered = {scenario for case in corpus["cases"] for scenario in case["covers"]}
        self.assertEqual(covered, set(corpus["required_scenarios"]))
        self.assertEqual(len({case["case_id"] for case in corpus["cases"]}), len(corpus["cases"]))

    def test_reviewed_source_roster_matches_runtime_derivation(self) -> None:
        corpus = load_json(CORPUS_PATH)
        runtime = load_runtime()
        derived = runtime.derive_source_roster(SOURCE_ROOT, ROOT)
        self.assertEqual(derived, corpus["source_roster"])

    def test_source_roster_drift_fails_closed(self) -> None:
        corpus = load_json(CORPUS_PATH)
        runtime = load_runtime()
        changed = json.loads(json.dumps(corpus["source_roster"]))
        changed["members"][0]["sha256"] = "sha256:" + hashlib.sha256(b"drift").hexdigest()
        with self.assertRaisesRegex(runtime.RosterDriftError, "fixture re-review required"):
            runtime.validate_source_roster(changed, corpus["source_roster"])

    def test_traceability_covers_all_fr_and_sc(self) -> None:
        traceability = load_json(CORPUS_PATH)["traceability"]
        expected = {f"FR-{number:03d}" for number in range(1, 23)}
        expected.update(f"SC-{number:03d}" for number in range(1, 10))
        self.assertEqual(set(traceability), expected)
        self.assertTrue(all(isinstance(evidence, str) and evidence for evidence in traceability.values()))

    def test_codex_resolver_has_no_claude_import(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("claude_route_fallback", source)
        self.assertNotIn("shared resolver", source.lower())

    def test_scope_excludes_production_and_live_claims(self) -> None:
        changed_runtime = MODULE_PATH.relative_to(ROOT).as_posix()
        self.assertTrue(changed_runtime.startswith("tests/speckit-pro/"))
        corpus = load_json(CORPUS_PATH)
        self.assertIn(
            "no row makes a live model or service availability claim",
            corpus["description"],
        )


class DeterministicRouteResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = load_runtime()

    def reasons(self, report: dict) -> list[str]:
        return [item["reason"] for item in report["plugin_diagnostics"]]

    def test_preferred_absence_falls_through_to_qualified_route(self) -> None:
        report = self.runtime.resolve_route(
            policy(route("preferred", model_present=False), route("fallback")),
            case_id="preferred-absent",
        )
        self.assertEqual(report["attempted_routes"], ["preferred", "fallback"])
        self.assertEqual(self.reasons(report), ["model_absent"])
        self.assertEqual(report["qualified_route"], "fallback")
        self.assertEqual(report["terminal_outcome"], "qualified_route")

    def test_effort_discovery_availability_and_treatment_reasons_use_fixed_order(self) -> None:
        preferred = route(
            "preferred",
            effort_supported=False,
            discovery_available=False,
            availability_succeeded=False,
            treatment_succeeded=False,
            treatment_digest="sha256:" + "c" * 64,
        )
        preferred["model_present"] = False
        report = self.runtime.resolve_route(policy(preferred), case_id="fixed-order")
        self.assertEqual(
            self.reasons(report),
            [
                "model_absent",
                "unsupported_effort",
                "capability_discovery_unavailable",
                "availability_probe_failed",
                "treatment_probe_failed",
                "non_route_treatment_mutation",
            ],
        )
        self.assertEqual(report["terminal_outcome"], "no_safe_route")

    def test_availability_and_treatment_failures_each_allow_later_fallback(self) -> None:
        availability = self.runtime.resolve_route(
            policy(route("preferred", availability_succeeded=False), route("fallback")),
            case_id="availability-failed",
        )
        treatment = self.runtime.resolve_route(
            policy(route("preferred", treatment_succeeded=False), route("fallback")),
            case_id="treatment-failed",
        )
        self.assertEqual(self.reasons(availability), ["availability_probe_failed"])
        self.assertEqual(self.reasons(treatment), ["treatment_probe_failed"])
        self.assertEqual(availability["qualified_route"], "fallback")
        self.assertEqual(treatment["qualified_route"], "fallback")

    def test_exhaustion_is_details_under_the_only_terminal_outcome(self) -> None:
        report = self.runtime.resolve_route(
            policy(route("preferred", model_present=False), route("fallback", effort_supported=False)),
            case_id="exhausted",
        )
        self.assertEqual(report["terminal_outcome"], "no_safe_route")
        self.assertIn("fallback_exhausted", report["terminal_details"])
        self.assertNotIn("fallback_exhausted", self.runtime.TERMINAL_OUTCOMES)
        self.assertEqual(sum(key == "terminal_outcome" for key in report), 1)

    def test_loop_is_detected_only_when_reached(self) -> None:
        reached = self.runtime.resolve_route(
            policy(route("same", model_present=False), route("same")),
            case_id="reached-loop",
        )
        unreachable = self.runtime.resolve_route(
            policy(route("winner"), route("later"), route("later")),
            case_id="unreachable-duplicate",
        )
        self.assertEqual(reached["attempted_routes"], ["same"])
        self.assertEqual(self.reasons(reached), ["model_absent", "loop_rejected"])
        self.assertEqual(reached["terminal_outcome"], "no_safe_route")
        self.assertEqual(unreachable["attempted_routes"], ["winner"])
        self.assertEqual(unreachable["terminal_outcome"], "qualified_route")

    def test_incompatible_strict_override_stops_before_route_walk(self) -> None:
        report = self.runtime.resolve_route(
            policy(route("preferred"), route("fallback"), strict_status="incompatible"),
            case_id="strict-override",
        )
        self.assertEqual(report["attempted_routes"], [])
        self.assertEqual(report["plugin_diagnostics"], [])
        self.assertEqual(report["terminal_outcome"], "strict_override_rejected")

    def test_route_report_is_byte_stable_across_three_replays(self) -> None:
        fixture = policy(
            route("preferred", model_present=False, effort_supported=False),
            route("fallback"),
        )
        outputs = [
            self.runtime.canonical_bytes(
                self.runtime.resolve_route(fixture, case_id="three-run-stability")
            )
            for _ in range(3)
        ]
        self.assertEqual(outputs, [outputs[0]] * 3)
        decoded = json.loads(outputs[0])
        self.assertEqual(
            [item["reason"] for item in decoded["plugin_diagnostics"]],
            ["model_absent", "unsupported_effort"],
        )
        self.assertEqual(decoded["terminal_outcome"], "qualified_route")
        self.assertNotIn(str(ROOT), outputs[0].decode("utf-8"))


class ServiceRerouteAttributionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = load_runtime()

    def service_policy(self, approval: str, target: str) -> dict:
        fixture = policy(route("preferred", model_present=False), route("fallback"))
        fixture["service_reroute"] = {
            "origin": "service",
            "observed_target_route": target,
            "approval": approval,
            "approval_evidence": f"fixture-{approval}",
            "scoring_effect": "eligible" if approval == "approved" else "ineligible",
            "non_route_treatment_digest": "sha256:" + "a" * 64,
        }
        return fixture

    def test_approved_service_reroute_is_separate_and_preserves_scoring(self) -> None:
        report = self.runtime.resolve_route(
            self.service_policy("approved", "fallback"), case_id="approved-service"
        )
        self.assertEqual(
            report["service_reroute_attribution"],
            {
                "origin": "service",
                "observed_target_route": "fallback",
                "approval": "approved",
                "scoring_effect": "eligible",
            },
        )
        self.assertEqual([item["reason"] for item in report["plugin_diagnostics"]], ["model_absent"])
        self.assertTrue(report["scoring_eligible"])

    def test_unapproved_service_reroute_is_ineligible_without_relabeling_plugin_reasons(self) -> None:
        report = self.runtime.resolve_route(
            self.service_policy("unapproved", "adjacent"), case_id="unapproved-service"
        )
        self.assertEqual(report["qualified_route"], "fallback")
        self.assertEqual(report["service_reroute_attribution"]["approval"], "unapproved")
        self.assertEqual(report["service_reroute_attribution"]["origin"], "service")
        self.assertFalse(report["scoring_eligible"])
        self.assertEqual([item["reason"] for item in report["plugin_diagnostics"]], ["model_absent"])

    def test_treatment_digest_ignores_only_model_and_effort(self) -> None:
        treatment = {
            "agent_identity": "fixture-agent",
            "instructions": "preserve exact behavior",
            "tools": ["filesystem.read"],
            "skills": ["speckit-implement"],
            "mcp_bindings": [],
            "sandbox": {"mode": "workspace-write", "network": "restricted"},
            "mutation_policy": "fake-home-only",
            "output_contract": "g56r-005-route-report",
            "model": "preferred-model",
            "effort": "high",
        }
        changed_route = json.loads(json.dumps(treatment))
        changed_route.update(model="fallback-model", effort="xhigh")
        changed_instructions = json.loads(json.dumps(changed_route))
        changed_instructions["instructions"] = "different treatment"
        self.assertEqual(
            self.runtime.treatment_digest(treatment),
            self.runtime.treatment_digest(changed_route),
        )
        self.assertNotEqual(
            self.runtime.treatment_digest(treatment),
            self.runtime.treatment_digest(changed_instructions),
        )

    def test_non_route_treatment_mutation_disqualifies_fallback(self) -> None:
        unchanged = route("fallback")
        unchanged["effort"] = "xhigh"
        qualified = self.runtime.resolve_route(
            policy(route("preferred", model_present=False), unchanged),
            case_id="model-effort-only",
        )
        mutated = self.runtime.resolve_route(
            policy(
                route("preferred", model_present=False),
                route("fallback", treatment_digest="sha256:" + "c" * 64),
            ),
            case_id="non-route-mutation",
        )
        self.assertEqual(qualified["qualified_route"], "fallback")
        self.assertEqual(mutated["qualified_route"], None)
        self.assertIn(
            "non_route_treatment_mutation",
            [item["reason"] for item in mutated["plugin_diagnostics"]],
        )


class OptionalHelperAndRosterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = load_runtime()

    def test_current_roster_has_twelve_core_roles_and_one_optional_helper(self) -> None:
        # Twelve since ART-008 added sweep-classifier and sweep-analyst, the two
        # agents that read reviewer-written text. Neither participates in route
        # fallback; they raise the count because the roster is derived by globbing
        # every Codex agent definition, not by listing fallback participants.
        roster = self.runtime.derive_source_roster(SOURCE_ROOT, ROOT)
        core = [item for item in roster["members"] if item["classification"] == "required_core"]
        helpers = [item for item in roster["members"] if item["classification"] == "optional_helper"]
        self.assertEqual(len(core), 12)
        self.assertEqual([Path(item["path"]).name for item in helpers], ["autopilot-fast-helper.toml"])

    def test_qualified_no_helper_continuation_has_separate_zero_helper_counter(self) -> None:
        fixture = policy(route("required-route"))
        fixture["helper_state"] = {
            "available": False,
            "no_helper_continuation_qualified": True,
            "helper_route_attempts": 0,
        }
        report = self.runtime.resolve_route(fixture, case_id="no-helper-qualified")
        self.assertEqual(report["terminal_outcome"], "qualified_route")
        self.assertEqual(report["helper_counters"], {"attempts": 0, "successes": 0, "failures": 1})
        self.assertEqual(report["required_route_counters"], {"attempts": 1, "successes": 1, "failures": 0})
        self.assertEqual(report["plugin_diagnostics"][-1]["reason"], "optional_helper_unavailable")

    def test_unqualified_no_helper_path_fails_closed_before_required_success(self) -> None:
        fixture = policy(route("required-route"))
        fixture["helper_state"] = {
            "available": False,
            "no_helper_continuation_qualified": False,
            "helper_route_attempts": 0,
        }
        report = self.runtime.resolve_route(fixture, case_id="no-helper-unqualified")
        self.assertIsNone(report["qualified_route"])
        self.assertFalse(report["scoring_eligible"])
        self.assertEqual(report["required_route_counters"]["successes"], 0)
        self.assertEqual(report["terminal_outcome"], "no_safe_route")

    def test_optional_helper_classification_is_bound_to_its_toml_contract(self) -> None:
        helper = self.runtime.validate_helper_definition(SOURCE_ROOT / "autopilot-fast-helper.toml")
        self.assertEqual(
            helper,
            {
                "classification": "optional_helper",
                "model": "gpt-5.3-codex-spark",
                "name": "autopilot-fast-helper",
                "sandbox_mode": "read-only",
            },
        )


class FakeHomeRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = load_runtime()

    def prepared_home(self, base: Path) -> Path:
        root = base / "fake-home"
        self.runtime.prepare_fake_home(root)
        return root

    def test_prewrite_failure_is_atomic_and_does_not_run_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.prepared_home(Path(temporary))
            agents = root / ".codex/agents"
            (agents / "existing.toml").write_text("old", encoding="utf-8")
            before = self.runtime.state_manifest(
                agents, {"existing.toml": "required_core"}
            )
            record = self.runtime.apply_fake_home(
                root,
                {"existing.toml": b"new", "second.toml": b"second"},
                {"existing.toml": "required_core", "second.toml": "required_core"},
                failure_mode="before_write",
            )
            after = self.runtime.state_manifest(
                agents, {"existing.toml": "required_core"}
            )
        self.assertEqual(before, after)
        self.assertEqual(record["pre_state_id"], record["final_state_id"])
        self.assertEqual(record["rollback_outcome"], "not_required")
        self.assertFalse(record["writes_state"])
        self.assertEqual(record["applied_actions"], [])

    def test_postwrite_failure_restores_previous_known_good_and_seed_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            seed = base / "seed"
            seed.mkdir()
            (seed / "existing.toml").write_text("old", encoding="utf-8")
            seed_bytes = (seed / "existing.toml").read_bytes()
            root = self.prepared_home(base)
            agents = root / ".codex/agents"
            shutil.copytree(seed, agents, dirs_exist_ok=True)
            before = self.runtime.state_manifest(agents, {"existing.toml": "required_core"})
            record = self.runtime.apply_fake_home(
                root,
                {"existing.toml": b"new", "second.toml": b"second"},
                {"existing.toml": "required_core", "second.toml": "required_core"},
                failure_mode="after_first_write",
            )
            after = self.runtime.state_manifest(agents, {"existing.toml": "required_core"})
            self.assertEqual((seed / "existing.toml").read_bytes(), seed_bytes)
        self.assertEqual(before, after)
        self.assertEqual(record["rollback_outcome"], "restored")
        self.assertFalse(record["writes_state"])
        self.assertTrue(record["rolled_back_actions"])
        self.assertTrue(record["cleanup_actions"])

    def test_rollback_failure_reports_writes_and_deterministic_remediation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.prepared_home(Path(temporary))
            agents = root / ".codex/agents"
            (agents / "existing.toml").write_text("old", encoding="utf-8")
            record = self.runtime.apply_fake_home(
                root,
                {"existing.toml": b"new"},
                {"existing.toml": "required_core"},
                failure_mode="rollback_failure",
            )
        self.assertEqual(record["rollback_outcome"], "failed")
        self.assertTrue(record["writes_state"])
        self.assertEqual(
            record["manual_remediation"],
            ["restore .codex/agents/existing.toml from the previous-known-good manifest"],
        )

    def test_cleanup_error_is_sorted_and_never_masks_successful_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.prepared_home(Path(temporary))
            agents = root / ".codex/agents"
            (agents / "existing.toml").write_text("old", encoding="utf-8")
            record = self.runtime.apply_fake_home(
                root,
                {"existing.toml": b"new"},
                {"existing.toml": "required_core"},
                failure_mode="cleanup_failure",
            )
        self.assertEqual(record["rollback_outcome"], "restored")
        self.assertFalse(record["writes_state"])
        self.assertEqual(record["cleanup_errors"], sorted(record["cleanup_errors"]))
        self.assertEqual(record["terminal_outcome"], "no_safe_route")

    def test_boundary_traversal_real_home_and_symlink_are_rejected_before_write(self) -> None:
        with self.assertRaisesRegex(ValueError, "real home"):
            self.runtime.prepare_fake_home(Path.home())
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = self.prepared_home(base)
            with self.assertRaisesRegex(ValueError, "boundary"):
                self.runtime.apply_fake_home(
                    root,
                    {"agent.toml": b"new"},
                    {"agent.toml": "required_core"},
                    destination_override=root / "../escape",
                )
            external = base / "external"
            external.mkdir()
            agents = root / ".codex/agents"
            agents.rmdir()
            os.symlink(external, agents, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                self.runtime.apply_fake_home(
                    root,
                    {"agent.toml": b"new"},
                    {"agent.toml": "required_core"},
                )
            self.assertEqual(list(external.iterdir()), [])


class BoundedSequentialHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = load_runtime()

    def harness_policy(self) -> dict:
        fixture = policy(route("preferred"))
        fixture["budgets"] = {
            "max_retries": 1,
            "max_elapsed_units": 5,
            "max_fanout": 1,
            "max_context_units": 10,
            "cancellation_point": "none",
            "max_escalations": 0,
        }
        return fixture

    def test_each_declared_bound_has_a_deterministic_terminal(self) -> None:
        cases = (
            ({"retries": 2}, "bounded_retry_exhausted"),
            ({"elapsed_units": 6}, "time_budget_exhausted"),
            ({"fanout": 2}, "fanout_budget_rejected"),
            ({"context_units": 11}, "context_budget_rejected"),
            ({"cancellation": True}, "cancellation_observed"),
            ({"escalations": 1}, "escalation_rejected"),
            ({"human_in_loop": True}, "escalation_rejected"),
        )
        for evidence, expected in cases:
            with self.subTest(expected=expected):
                report = self.runtime.run_harness(
                    self.harness_policy(), case_id=expected, consumption=evidence
                )
                self.assertEqual(report["terminal_outcome"], expected)
                self.assertIsNone(report["qualified_route"])

    def test_recursive_execution_is_rejected_without_dispatch(self) -> None:
        report = self.runtime.run_harness(
            self.harness_policy(),
            case_id="recursive-rejected",
            consumption={"recursive": True},
        )
        self.assertEqual(report["terminal_outcome"], "no_safe_route")
        self.assertEqual(report["attempted_routes"], [])
        self.assertIn("recursive_execution_rejected", report["terminal_details"])

    def test_inherited_and_substituted_routes_fail_closed(self) -> None:
        candidates = (
            ("inherited_model", "inherited_model_rejected"),
            ("inherited_effort", "inherited_effort_rejected"),
            ("generic_substitution", "generic_substitution_rejected"),
            ("unqualified_adjacent", "unqualified_adjacent_route"),
        )
        for declaration_source, reason in candidates:
            with self.subTest(reason=reason):
                candidate = route("preferred")
                candidate["declaration_source"] = declaration_source
                report = self.runtime.run_harness(
                    policy(candidate), case_id=reason, consumption={}
                )
                self.assertEqual(report["terminal_outcome"], "no_safe_route")
                self.assertIn(reason, [item["reason"] for item in report["plugin_diagnostics"]])

    def test_cancellation_after_mutation_runs_only_bounded_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "fake-home"
            agents = self.runtime.prepare_fake_home(root)
            (agents / "existing.toml").write_text("old", encoding="utf-8")
            report = self.runtime.run_harness(
                self.harness_policy(),
                case_id="cancel-after-mutation",
                consumption={"cancellation": True},
                fake_home={
                    "root": root,
                    "desired_files": {"existing.toml": b"new"},
                    "classifications": {"existing.toml": "required_core"},
                },
            )
            self.assertEqual((agents / "existing.toml").read_text(encoding="utf-8"), "old")
        self.assertEqual(report["terminal_outcome"], "cancellation_observed")
        self.assertEqual(report["recovery_record"]["rollback_outcome"], "restored")
        self.assertFalse(report["recovery_record"]["writes_state"])

    def test_canonical_replay_excludes_host_paths_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "fake-home"
            agents = self.runtime.prepare_fake_home(root)
            (agents / "existing.toml").write_text("old", encoding="utf-8")
            report = self.runtime.run_harness(
                self.harness_policy(),
                case_id="host-data-exclusion",
                consumption={"cancellation": True},
                fake_home={
                    "root": root,
                    "desired_files": {"existing.toml": b"new"},
                    "classifications": {"existing.toml": "required_core"},
                },
            )
            encoded = self.runtime.canonical_bytes(report).decode("utf-8")
        self.assertNotIn(temporary, encoded)
        self.assertNotIn(str(Path.home()), encoded)
        for forbidden in ("mtime", "inode", "timestamp", "temporary_root"):
            self.assertNotIn(forbidden, encoded)


if __name__ == "__main__":
    unittest.main()
