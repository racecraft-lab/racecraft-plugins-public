#!/usr/bin/env python3
"""Contracts for the governed twelve-role fixture corpus.

The corpus is one governed set of twelve role contracts: the eleven required-core
roles that have shipped agent definitions, plus ``autopilot-fast-helper``, which
has no Claude agent definition and is therefore contract-only. ``required_core``
and ``executable`` are **independent** booleans, so a role can be required by the
cohort design and still be unrunnable today; every contract field binds either
way (FR-011, FR-012).

Two families of checks live here:

* **Contract-structural** cases load
  ``tests/speckit-pro/layer6-efficiency/contracts-claude/role-corpus.schema.json``
  and assert the closed role enumeration it publishes.
* **Module-contract** cases exercise the standard-library implementation at
  ``tests/speckit-pro/layer6-efficiency/lib/claude_role_corpus.py`` against the
  committed corpus fixture: composition, the run-only-admitted-executable-routes
  rule, separate analysis of the contract-only role, and the FR-033 canonical
  digest preimage.

Every check is offline and makes zero live model calls.
"""

from __future__ import annotations

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

try:  # T049…T050 deliverable — absent until the corpus module is implemented.
    import claude_role_corpus  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    claude_role_corpus = None  # type: ignore[assignment]


CONTRACT_ROOT = REPO_ROOT / "tests" / "speckit-pro" / "layer6-efficiency" / "contracts-claude"
CORPUS_SCHEMA_PATH = CONTRACT_ROOT / "role-corpus.schema.json"
AGENT_DIR = REPO_ROOT / "speckit-pro" / "agents"
CURRENT_ROSTER_PATH = (
    REPO_ROOT
    / "tests"
    / "speckit-pro"
    / "layer6-efficiency"
    / "fixtures"
    / "claude-agent-roster-rebaseline-v2.json"
)

# FR-011: the eleven required-core roles the frozen CAR-003 corpus binds. Stated
# as a literal so a unilateral widening of either the corpus or the shipped agent
# set shows up as a diff against this tuple. The corpus is immutable, so a role
# retired from the live roster stays here and is named in RETIRED_ROLES.
REQUIRED_CORE_ROLES = (
    "analyze-executor",
    "checklist-executor",
    "clarify-executor",
    "codebase-analyst",
    "consensus-synthesizer",
    "domain-researcher",
    "gate-validator",
    "implement-executor",
    "phase-executor",
    "spec-context-analyst",
    "uat-runbook-author",
)

# FR-012: contract-only until a later spec authors the agent definition. It binds
# every contract field, runs never, emits no score bundle, and is never attrition.
CONTRACT_ONLY_ROLE = "autopilot-fast-helper"

# Required-core roles the frozen corpus binds that no longer ship an agent
# definition. `gate-validator` retired once the autopilot orchestrator began
# calling the `validate-gate` runner helper directly.
RETIRED_ROLES = ("gate-validator",)
SHIPPED_REQUIRED_CORE_ROLES = tuple(
    role for role in REQUIRED_CORE_ROLES if role not in RETIRED_ROLES
)

GOVERNED_ROLE_IDS = tuple(sorted(REQUIRED_CORE_ROLES + (CONTRACT_ONLY_ROLE,)))

# The published schema tracks the live governed set, so it drops a retired role
# while the frozen corpus keeps binding it.
LIVE_GOVERNED_ROLE_IDS = tuple(sorted(SHIPPED_REQUIRED_CORE_ROLES + (CONTRACT_ONLY_ROLE,)))

CURRENT_SHIPPED_ROLES = (
    "analyze-executor",
    "artifact-author",
    "checklist-executor",
    "clarify-executor",
    "codebase-analyst",
    "consensus-synthesizer",
    "domain-researcher",
    "implement-executor",
    "phase-executor",
    "spec-context-analyst",
    "sweep-analyst",
    "sweep-classifier",
    "uat-runbook-author",
)

# FR-012: bound for every role entry, including the non-executable one.
ALWAYS_BOUND_CONTRACT_FIELDS = (
    "role_id",
    "required_core",
    "executable",
    "source_digest",
    "fixture_digest",
    "objective_binding",
    "permitted_tools",
    "mutation_contract",
    "expected_artifacts",
    "acceptance_oracle_digest",
    "independent_review_binding",
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(record: object) -> str:
    return json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def digest_over(record: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()


class _RoleCorpusFixture:
    def setUp(self) -> None:
        self.assertIsNotNone(claude_role_corpus, "claude_role_corpus is not importable")
        self.module = claude_role_corpus
        self.corpus = self.module.load_corpus()
        self.roles = self.module.role_index(self.corpus)


class CorpusCompositionTests(_RoleCorpusFixture, unittest.TestCase):
    """Exactly twelve role contracts, independent booleans, and a contract-only
    role that binds everything while never running (FR-011, FR-012, SC-005)."""

    def test_the_governed_corpus_binds_exactly_twelve_role_contracts(self) -> None:
        self.assertEqual(len(self.corpus["roles"]), 12)
        self.assertEqual(tuple(sorted(self.roles)), GOVERNED_ROLE_IDS)

    def test_the_module_declares_the_eleven_governed_roles_plus_the_contract_only_one(
        self,
    ) -> None:
        self.assertEqual(tuple(sorted(self.module.REQUIRED_CORE_ROLES)), tuple(sorted(REQUIRED_CORE_ROLES)))
        self.assertEqual(self.module.CONTRACT_ONLY_ROLES, (CONTRACT_ONLY_ROLE,))
        self.assertEqual(self.module.GOVERNED_ROLE_IDS, GOVERNED_ROLE_IDS)
        self.assertEqual(self.module.RETIRED_ROLES, RETIRED_ROLES)
        self.assertEqual(self.module.SHIPPED_REQUIRED_CORE_ROLES, SHIPPED_REQUIRED_CORE_ROLES)

    def test_each_unretired_required_core_role_names_a_shipped_agent_definition(self) -> None:
        for role_id in SHIPPED_REQUIRED_CORE_ROLES:
            with self.subTest(role=role_id):
                self.assertTrue((AGENT_DIR / f"{role_id}.md").is_file())

    def test_a_retired_required_core_role_no_longer_ships_an_agent_definition(self) -> None:
        for role_id in RETIRED_ROLES:
            with self.subTest(role=role_id):
                self.assertIn(role_id, REQUIRED_CORE_ROLES)
                self.assertFalse((AGENT_DIR / f"{role_id}.md").exists())

    def test_the_contract_only_role_has_no_shipped_agent_definition(self) -> None:
        self.assertFalse((AGENT_DIR / f"{CONTRACT_ONLY_ROLE}.md").exists())

    def test_required_core_and_executable_are_independent_booleans(self) -> None:
        for role_id, role in sorted(self.roles.items()):
            with self.subTest(role=role_id):
                self.assertIsInstance(role["required_core"], bool)
                self.assertIsInstance(role["executable"], bool)
        # Independence is only observable if the two are not the same column.
        pairs = {(role["required_core"], role["executable"]) for role in self.roles.values()}
        self.assertIn((True, True), pairs)
        self.assertIn((True, False), pairs)

    def test_the_contract_only_role_is_required_core_but_not_executable(self) -> None:
        helper = self.roles[CONTRACT_ONLY_ROLE]
        self.assertTrue(helper["required_core"])
        self.assertFalse(helper["executable"])

    def test_the_contract_only_role_binds_every_contract_field_anyway(self) -> None:
        helper = self.roles[CONTRACT_ONLY_ROLE]
        for field in ALWAYS_BOUND_CONTRACT_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, helper)
                self.assertIsNotNone(helper[field])

    def test_a_non_executable_role_carries_no_candidate_route_bindings(self) -> None:
        self.assertNotIn("candidate_route_bindings", self.roles[CONTRACT_ONLY_ROLE])

    def test_a_non_executable_role_emits_no_score_bundle(self) -> None:
        self.assertFalse(self.module.emits_score_bundle(self.roles[CONTRACT_ONLY_ROLE]))
        for role_id in REQUIRED_CORE_ROLES:
            with self.subTest(role=role_id):
                self.assertTrue(self.module.emits_score_bundle(self.roles[role_id]))

    def test_a_non_executable_role_is_never_counted_as_attrition(self) -> None:
        self.assertFalse(self.module.counts_as_attrition(self.roles[CONTRACT_ONLY_ROLE]))
        self.assertTrue(self.module.counts_as_attrition(self.roles["implement-executor"]))

    def test_the_contract_only_role_is_analysed_apart_from_primary_statistics(self) -> None:
        partition = self.module.analysis_partition(self.corpus)
        self.assertEqual(partition["required_core_primary"], tuple(sorted(REQUIRED_CORE_ROLES)))
        self.assertEqual(partition["analysed_separately"], (CONTRACT_ONLY_ROLE,))
        self.assertNotIn(CONTRACT_ONLY_ROLE, partition["required_core_primary"])

    def test_only_roles_with_admitted_executable_routes_are_run(self) -> None:
        every_route = self.module.declared_route_ids(self.corpus)
        self.assertEqual(
            self.module.runnable_roles(self.corpus, every_route),
            tuple(sorted(REQUIRED_CORE_ROLES)),
        )
        # Withdraw one admitted route and its role stops being runnable, while the
        # contract-only role never appears under any admission set.
        withdrawn = self.roles["implement-executor"]["candidate_route_bindings"][0]["id"]
        remaining = tuple(route for route in every_route if route != withdrawn)
        runnable = self.module.runnable_roles(self.corpus, remaining)
        self.assertNotIn("implement-executor", runnable)
        self.assertIn("phase-executor", runnable)
        self.assertNotIn(CONTRACT_ONLY_ROLE, runnable)
        self.assertEqual(self.module.runnable_roles(self.corpus, ()), ())

    def test_the_published_role_enumeration_is_closed_to_the_live_governed_set(self) -> None:
        schema = load_json(CORPUS_SCHEMA_PATH)
        role_schema = schema["$defs"]["role"]  # type: ignore[index]
        self.assertEqual(
            tuple(sorted(role_schema["properties"]["role_id"]["enum"])), LIVE_GOVERNED_ROLE_IDS
        )
        roles_property = schema["properties"]["roles"]  # type: ignore[index]
        self.assertEqual(roles_property["minItems"], len(LIVE_GOVERNED_ROLE_IDS))
        self.assertEqual(roles_property["maxItems"], len(LIVE_GOVERNED_ROLE_IDS))
        for role_id in RETIRED_ROLES:
            with self.subTest(role=role_id):
                self.assertNotIn(role_id, role_schema["properties"]["role_id"]["enum"])

    def test_a_thirteenth_role_is_refused(self) -> None:
        oversized = json.loads(json.dumps(self.corpus))
        oversized["roles"].append(json.loads(json.dumps(oversized["roles"][0])))
        findings = self.module.validate_corpus(oversized)
        self.assertTrue(any("twelve" in finding for finding in findings), findings)

    def test_a_route_binding_on_a_non_executable_role_is_refused(self) -> None:
        broken = json.loads(json.dumps(self.corpus))
        for role in broken["roles"]:
            if role["role_id"] == CONTRACT_ONLY_ROLE:
                role["candidate_route_bindings"] = [
                    {"id": "route-never-admitted", "digest": digest_over({"route": "x"})}
                ]
        findings = self.module.validate_corpus(broken)
        self.assertTrue(
            any("candidate_route_bindings" in finding for finding in findings), findings
        )

    def test_the_committed_corpus_validates_clean(self) -> None:
        self.assertEqual(self.module.validate_corpus(self.corpus), ())


class FixtureDigestTests(_RoleCorpusFixture, unittest.TestCase):
    """Every fixture binds its full contract and a canonical-JSON digest that is
    recomputed at acceptance and at replay (FR-033)."""

    def test_every_fixture_binds_the_full_contract_field_set(self) -> None:
        for role_id, role in sorted(self.roles.items()):
            with self.subTest(role=role_id):
                self.assertEqual(
                    self.module.unbound_contract_fields(role),
                    (),
                    f"{role_id} left contract fields unbound",
                )

    def test_a_fixture_digest_is_canonical_json_excluding_its_own_field(self) -> None:
        role = self.roles["implement-executor"]
        preimage = {key: value for key, value in role.items() if key != "fixture_digest"}
        self.assertEqual(role["fixture_digest"], digest_over(preimage))
        self.assertEqual(
            self.module.record_digest(role, digest_field="fixture_digest"), digest_over(preimage)
        )

    def test_a_digest_is_emitted_as_sha256_and_sixty_four_hex_characters(self) -> None:
        for role_id, role in sorted(self.roles.items()):
            with self.subTest(role=role_id):
                for field in ("source_digest", "fixture_digest", "acceptance_oracle_digest"):
                    value = role[field]
                    self.assertTrue(value.startswith("sha256:"), f"{role_id}.{field}")
                    self.assertEqual(len(value), len("sha256:") + 64)
                    self.assertEqual(value, value.lower())

    def test_key_order_never_changes_a_digest(self) -> None:
        role = self.roles["phase-executor"]
        reordered = dict(reversed(list(role.items())))
        self.assertNotEqual(list(reordered), list(role))
        self.assertEqual(
            self.module.record_digest(reordered, digest_field="fixture_digest"),
            self.module.record_digest(role, digest_field="fixture_digest"),
        )

    def test_the_corpus_digest_covers_the_whole_corpus_minus_itself(self) -> None:
        preimage = {key: value for key, value in self.corpus.items() if key != "corpus_digest"}
        self.assertEqual(self.corpus["corpus_digest"], digest_over(preimage))
        self.assertTrue(self.module.verify_corpus_digest(self.corpus))

    def test_a_fixture_digest_mismatch_fails_the_fixture_before_candidate_scoring(self) -> None:
        tampered = json.loads(json.dumps(self.roles["consensus-synthesizer"]))
        tampered["mutation_contract"] = "unrestricted_write"
        verdict = self.module.verify_fixture(tampered)
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.failure_plane, "fixture")
        self.assertEqual(verdict.failure_code, "fixture_invalid")
        self.assertEqual(verdict.stage, self.module.FIXTURE_CHECK_STAGE)
        self.assertEqual(verdict.stage, "before_candidate_scoring")

    def test_an_intact_fixture_passes_its_recomputation(self) -> None:
        for role_id, role in sorted(self.roles.items()):
            with self.subTest(role=role_id):
                verdict = self.module.verify_fixture(role)
                self.assertTrue(verdict.ok, verdict)
                self.assertEqual(verdict.failure_plane, "none")
                self.assertEqual(verdict.failure_code, "none")

    def test_a_corpus_digest_mismatch_is_reported(self) -> None:
        tampered = json.loads(json.dumps(self.corpus))
        tampered["corpus_id"] = tampered["corpus_id"] + "-tampered"
        self.assertFalse(self.module.verify_corpus_digest(tampered))
        self.assertTrue(
            any("corpus_digest" in finding for finding in self.module.validate_corpus(tampered))
        )

    def test_sealing_a_fixture_reproduces_the_committed_digest(self) -> None:
        for role_id, role in sorted(self.roles.items()):
            with self.subTest(role=role_id):
                stripped = {key: value for key, value in role.items() if key != "fixture_digest"}
                self.assertEqual(self.module.seal_fixture(stripped), role)

    def test_the_corpus_fixture_stays_bounded_in_size(self) -> None:
        # FR-057: suite cost must not scale with accumulated cohort evidence.
        self.assertLess(self.module.CORPUS_FIXTURE_PATH.stat().st_size, 32_768)


class CurrentRosterRebaselineTests(unittest.TestCase):
    """The successor roster binds live source without mutating CAR-003 v1."""

    def setUp(self) -> None:
        self.current = load_json(CURRENT_ROSTER_PATH)
        self.roles = {role["role_id"]: role for role in self.current["shipped_roles"]}

    def test_successor_roster_covers_all_thirteen_shipped_agents_plus_helper(self) -> None:
        self.assertEqual(tuple(sorted(self.roles)), CURRENT_SHIPPED_ROLES)
        self.assertEqual(
            self.current["optional_contract_roles"],
            [{"role_id": CONTRACT_ONLY_ROLE, "executable": False}],
        )

    def test_successor_roster_preserves_the_historical_corpus_identity(self) -> None:
        historical = load_json(
            REPO_ROOT
            / "tests"
            / "speckit-pro"
            / "layer6-efficiency"
            / "fixtures"
            / "car-003-role-corpus.json"
        )
        self.assertEqual(self.current["historical_corpus"]["corpus_id"], historical["corpus_id"])
        self.assertEqual(
            self.current["historical_corpus"]["corpus_digest"],
            historical["corpus_digest"],
        )
        self.assertEqual(self.current["historical_corpus"]["disposition"], "immutable")

    def test_each_successor_source_digest_matches_current_agent_bytes(self) -> None:
        for role_id, role in sorted(self.roles.items()):
            with self.subTest(role=role_id):
                digest = "sha256:" + hashlib.sha256(
                    (AGENT_DIR / f"{role_id}.md").read_bytes()
                ).hexdigest()
                self.assertEqual(role["source_digest"], digest)

    def test_new_roles_have_explicit_cohorts_and_trust_boundaries(self) -> None:
        self.assertEqual(self.roles["artifact-author"]["cohort"], "structured-work")
        for role_id in ("sweep-classifier", "sweep-analyst"):
            with self.subTest(role=role_id):
                self.assertEqual(self.roles[role_id]["cohort"], "untrusted-feedback")
                self.assertEqual(
                    self.roles[role_id]["trust_boundary"],
                    "immutable_snapshot_broker_only",
                )

    def test_successor_memory_matrix_stays_narrow(self) -> None:
        scopes = {
            role_id: role["memory_scope"]
            for role_id, role in self.roles.items()
            if role["memory_scope"] is not None
        }
        self.assertEqual(
            scopes,
            {
                "codebase-analyst": "local",
                "implement-executor": "local",
                "spec-context-analyst": "local",
            },
        )

    def test_route_gate_consumes_successor_without_claiming_native_fallback(self) -> None:
        gate = self.current["routing_gate"]
        self.assertEqual(gate["car_006"], "ready")
        self.assertEqual(gate["native_fallback"], "operator_override_only")
        self.assertEqual(gate["unqualified_delivered_model"], "ineligible")

    def test_successor_catalog_digest_covers_the_whole_record_minus_itself(self) -> None:
        preimage = {key: value for key, value in self.current.items() if key != "catalog_digest"}
        self.assertEqual(self.current["catalog_digest"], digest_over(preimage))


TEST_CASES = (
    CorpusCompositionTests,
    FixtureDigestTests,
    CurrentRosterRebaselineTests,
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-role-corpus-governance"))
