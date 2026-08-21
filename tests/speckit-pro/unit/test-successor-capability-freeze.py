#!/usr/bin/env python3
"""Contracts for the CAR-003 successor capability freeze.

The freeze admits only model/effort tuples present in BOTH the official-source
candidate ledger and the pinned runtime catalog collected through the sole
admitting surface — the operator-run print-mode canary probe. Every other
runtime surface is diagnostic: it may corroborate or invalidate an admitted
tuple, never admit one (FR-004).

Two families of checks live here:

* **Contract-structural** cases load the CAR-003 schemas under
  ``tests/speckit-pro/layer6-efficiency/contracts-claude/`` and assert the closed
  taxonomies they publish.
* **Module-contract** cases exercise the standard-library implementation at
  ``tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py``:
  admission, the fail-closed publication gate, alias re-point detection, and
  the four versioned refresh triggers.

Every check is offline and makes zero live model calls. The live collection
that feeds a real freeze is operator-only and never runs in this suite.
"""

from __future__ import annotations

import hashlib
import json
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

from test_result import run_counted  # noqa: E402

try:  # T013…T019 deliverable — absent until the freeze module is implemented.
    import claude_successor_freeze  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    claude_successor_freeze = None  # type: ignore[assignment]


CONTRACT_ROOT = REPO_ROOT / "tests" / "speckit-pro" / "layer6-efficiency" / "contracts-claude"
FREEZE_SCHEMA_PATH = CONTRACT_ROOT / "successor-capability-freeze.schema.json"
ADDITIVE_SCHEMA_PATH = CONTRACT_ROOT / "car-003-additive-records.schema.json"

# FR-029: the closed exclusion taxonomy, stated here so a unilateral widening of
# either the schema or the emitter shows up as a diff against a literal.
EXCLUSION_TAXONOMY = frozenset(
    {
        "source_not_admitted",
        "effort_not_source_admitted",
        "effort_source_not_admitted",
        "canonical_effort_unknown",
        "surface_evidence_incomplete",
        "surface_disagreement",
        "alias_repoint_unresolved",
        "availability_not_proven",
        "topology_control_not_candidate_effort",
    }
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def digest_of(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


PINNED_CLIENT = "2.1.240 (Claude Code)"
ROLE_ELIGIBLE_MODELS = ("opus", "sonnet")


def probe_ladder(model: str, *, efforts: tuple[str, ...] | None = None, surface: str | None = None,
                 acceptance: str = "accepted") -> list[dict[str, object]]:
    """One admitting-surface observation per effort on the ordered ladder."""
    ladder = efforts if efforts is not None else ("low", "medium", "high", "xhigh", "max")
    return [
        {
            "effort": effort,
            "acceptance": acceptance,
            "surface": surface or "print_mode_canary_probe",
            "evidence_digest": digest_of(f"{model}__{effort}"),
        }
        for effort in ladder
    ]


def source_ledger(**overrides: object) -> dict[str, object]:
    """The official-source candidate ledger half of the intersection (FR-003)."""
    ledger: dict[str, object] = {
        "ledger_id": "CAR-001-LEDGER-2026-07-24-V1",
        "ledger_digest": digest_of("official-source-ledger"),
        "candidates": [
            {"model": model, "efforts": ["low", "medium", "high", "xhigh", "max"]}
            for model in ROLE_ELIGIBLE_MODELS
        ],
    }
    ledger.update(overrides)
    return ledger


def collection_fields(**overrides: object) -> dict[str, object]:
    """A complete, provenance-clean runtime catalog collection input (FR-002)."""
    fields: dict[str, object] = {
        "collection_id": "CAR-003-RCC-2026-07-24-V1",
        "command_contract": {
            "executable": "claude",
            "flags": ["-p", "--model"],
            "canary": "Reply with the single word: ok",
        },
        "collection_method": "operator_run_print_mode_canary_probe",
        "collection_authority": "operator_pinned_client",
        "client_version": PINNED_CLIENT,
        "client_distribution": "native",
        "account_boundary": "subscription_account_redacted",
        "environment_boundary": "<home>",
        "authentication_mode": "subscription",
        "raw_catalog_digest": digest_of("raw-catalog"),
        "parsed_catalog_digest": digest_of("parsed-catalog"),
        "observed_models": list(ROLE_ELIGIBLE_MODELS),
        "alias_bindings": [
            {"alias": "opus", "resolved_dated_model_id": "claude-opus-5"},
            {"alias": "sonnet", "resolved_dated_model_id": "claude-sonnet-5"},
        ],
        "visible_defaults": {"model": "opus", "effort": "high"},
        "supported_efforts": {model: probe_ladder(model) for model in ROLE_ELIGIBLE_MODELS},
        "effort_search_origin": "high",
        "collected_at_utc": "2026-07-24T18:00:00Z",
        "invalidation_criteria": [
            "client_change",
            "catalog_change",
            "alias_repoint",
            "source_ledger_change",
        ],
        "sanitization_status": "passed",
        "retention_status": "passed",
    }
    fields.update(overrides)
    return fields


class ExclusionTaxonomyTests(unittest.TestCase):
    """The CAR-003 contracts parse and publish a closed exclusion taxonomy that
    the emitter reproduces exactly (FR-029, SC-003)."""

    def test_the_freeze_and_additive_contracts_parse(self) -> None:
        for path in (FREEZE_SCHEMA_PATH, ADDITIVE_SCHEMA_PATH):
            with self.subTest(contract=path.name):
                document = load_json(path)
                self.assertEqual(
                    document["$schema"],
                    "https://json-schema.org/draft/2020-12/schema",
                    path.name,
                )

    def test_schema_exclusion_reasons_are_exactly_the_nine_closed_members(self) -> None:
        schema = load_json(FREEZE_SCHEMA_PATH)
        reasons = schema["properties"]["excluded_tuples"]["items"]["properties"]["reason"]
        self.assertEqual(set(reasons["enum"]), EXCLUSION_TAXONOMY)
        self.assertEqual(len(reasons["enum"]), 9)

    def test_emitter_exposes_the_same_closed_taxonomy(self) -> None:
        self.assertIsNotNone(claude_successor_freeze, "claude_successor_freeze is not importable")
        self.assertEqual(set(claude_successor_freeze.EXCLUSION_REASONS), EXCLUSION_TAXONOMY)

    def test_every_excluded_tuple_carries_a_machine_checkable_reason(self) -> None:
        self.assertIsNotNone(claude_successor_freeze, "claude_successor_freeze is not importable")
        excluded = claude_successor_freeze.ExcludedTuple(
            model="opus", effort="fast", reason="topology_control_not_candidate_effort"
        )
        self.assertEqual(
            excluded.as_record(),
            {
                "model": "opus",
                "effort": "fast",
                "reason": "topology_control_not_candidate_effort",
            },
        )
        with self.assertRaises(claude_successor_freeze.SuccessorFreezeError):
            claude_successor_freeze.ExcludedTuple(model="opus", effort="fast", reason="just_because")


class _SuccessorFreezeModuleFixture:
    def setUp(self) -> None:
        self.assertIsNotNone(claude_successor_freeze, "claude_successor_freeze is not importable")
        self.module = claude_successor_freeze


class CollectionRecordProvenanceTests(_SuccessorFreezeModuleFixture, unittest.TestCase):
    """The runtime catalog collection record carries its own mandatory
    provenance, and effort admission is a bounded configuration-acceptance
    claim rather than verified support (FR-002)."""

    def test_a_complete_collection_record_is_provenance_clean(self) -> None:
        record = self.module.build_collection_record(**collection_fields())
        self.assertEqual(self.module.missing_provenance(record), ())

    def test_every_mandatory_provenance_field_is_named_when_absent(self) -> None:
        for field in self.module.REQUIRED_COLLECTION_FIELDS:
            with self.subTest(field=field):
                record = self.module.build_collection_record(**collection_fields())
                del record[field]
                self.assertIn(field, self.module.missing_provenance(record))

    def test_the_record_names_the_command_contract_and_sole_admitting_surface(self) -> None:
        record = self.module.build_collection_record(**collection_fields())
        self.assertEqual(record["admitting_surface"], "print_mode_canary_probe")
        self.assertEqual(record["command_contract"]["executable"], "claude")
        self.assertIn("--model", record["command_contract"]["flags"])

    def test_the_record_carries_client_boundary_catalog_and_timestamp_provenance(self) -> None:
        record = self.module.build_collection_record(**collection_fields())
        self.assertEqual(record["client_version"], PINNED_CLIENT)
        self.assertEqual(record["client_distribution"], "native")
        self.assertEqual(record["account_boundary"], "subscription_account_redacted")
        self.assertEqual(record["environment_boundary"], "<home>")
        self.assertTrue(record["raw_catalog_digest"].startswith("sha256:"))
        self.assertTrue(record["parsed_catalog_digest"].startswith("sha256:"))
        self.assertEqual(record["observed_models"], list(ROLE_ELIGIBLE_MODELS))
        self.assertEqual(record["alias_bindings"][0]["alias"], "opus")
        self.assertEqual(record["visible_defaults"]["effort"], "high")
        self.assertEqual(sorted(record["supported_efforts"]), sorted(ROLE_ELIGIBLE_MODELS))
        self.assertEqual(record["collected_at_utc"], "2026-07-24T18:00:00Z")
        self.assertEqual(
            record["invalidation_criteria"], list(self.module.REFRESH_TRIGGERS)
        )

    def test_effort_admission_is_a_bounded_configuration_acceptance_claim(self) -> None:
        record = self.module.build_collection_record(**collection_fields())
        self.assertEqual(
            record["effort_admission"],
            {
                "basis": "configuration_acceptance",
                "verified_support": False,
                "bounded": True,
            },
        )

    def test_a_verified_support_claim_is_refused_rather_than_recorded(self) -> None:
        with self.assertRaises(self.module.SuccessorFreezeError):
            self.module.build_collection_record(
                **collection_fields(
                    effort_admission={
                        "basis": "verified_effect",
                        "verified_support": True,
                        "bounded": False,
                    }
                )
            )

    def test_the_collection_digest_excludes_itself_and_recomputes(self) -> None:
        record = self.module.build_collection_record(**collection_fields())
        self.assertEqual(
            record["collection_digest"],
            self.module.record_digest(record, digest_field="collection_digest"),
        )
        mutated = dict(record)
        mutated["client_version"] = "9.9.9 (Claude Code)"
        self.assertNotEqual(
            record["collection_digest"],
            self.module.record_digest(mutated, digest_field="collection_digest"),
        )


class AdmissionAndLadderTests(_SuccessorFreezeModuleFixture, unittest.TestCase):
    """Admission is the intersection of the official-source ledger and the
    pinned runtime. Diagnostic surfaces corroborate or invalidate, never admit
    (FR-003, FR-004, FR-005, FR-040, SC-002, SC-018)."""

    def admit(self, *, collection: dict[str, object] | None = None,
              ledger: dict[str, object] | None = None,
              diagnostics: tuple[dict[str, object], ...] = ()) -> object:
        return self.module.admit_tuples(
            source_ledger=ledger if ledger is not None else source_ledger(),
            collection=collection if collection is not None
            else self.module.build_collection_record(**collection_fields()),
            diagnostics=diagnostics,
        )

    def reasons_for(self, result: object, model: str, effort: str) -> list[str]:
        return [
            excluded.reason
            for excluded in result.excluded
            if excluded.model == model and excluded.effort == effort
        ]

    def admitted_pairs(self, result: object) -> set[tuple[str, str]]:
        return {(tuple_["model"], tuple_["effort"]) for tuple_ in result.admitted}

    def test_the_full_source_runtime_intersection_is_admitted(self) -> None:
        result = self.admit()
        self.assertEqual(
            self.admitted_pairs(result),
            {(model, effort) for model in ROLE_ELIGIBLE_MODELS for effort in self.module.EFFORT_LADDER},
        )

    def test_a_runtime_only_tuple_is_excluded_source_not_admitted(self) -> None:
        fields = collection_fields()
        fields["observed_models"] = [*ROLE_ELIGIBLE_MODELS, "haiku"]
        fields["supported_efforts"] = dict(fields["supported_efforts"])
        fields["supported_efforts"]["haiku"] = probe_ladder("haiku")
        result = self.admit(collection=self.module.build_collection_record(**fields))
        self.assertNotIn(("haiku", "max"), self.admitted_pairs(result))
        self.assertEqual(self.reasons_for(result, "haiku", "max"), ["source_not_admitted"])

    def test_a_source_effort_the_runtime_rejected_is_excluded(self) -> None:
        fields = collection_fields()
        fields["supported_efforts"] = dict(fields["supported_efforts"])
        fields["supported_efforts"]["sonnet"] = [
            *probe_ladder("sonnet", efforts=("low", "medium", "high", "xhigh")),
            *probe_ladder("sonnet", efforts=("max",), acceptance="rejected"),
        ]
        result = self.admit(collection=self.module.build_collection_record(**fields))
        self.assertNotIn(("sonnet", "max"), self.admitted_pairs(result))
        self.assertEqual(self.reasons_for(result, "sonnet", "max"), ["effort_source_not_admitted"])

    def test_a_source_model_the_runtime_never_observed_is_excluded(self) -> None:
        ledger = source_ledger()
        ledger["candidates"] = [*ledger["candidates"], {"model": "haiku", "efforts": ["max"]}]
        result = self.admit(ledger=ledger)
        self.assertNotIn(("haiku", "max"), self.admitted_pairs(result))
        self.assertEqual(self.reasons_for(result, "haiku", "max"), ["effort_source_not_admitted"])

    def test_a_runtime_effort_the_source_never_admitted_is_excluded(self) -> None:
        ledger = source_ledger()
        ledger["candidates"] = [
            {"model": "opus", "efforts": ["low", "medium", "high", "xhigh"]},
            {"model": "sonnet", "efforts": list(self.module.EFFORT_LADDER)},
        ]
        result = self.admit(ledger=ledger)
        self.assertNotIn(("opus", "max"), self.admitted_pairs(result))
        self.assertEqual(self.reasons_for(result, "opus", "max"), ["effort_not_source_admitted"])

    def test_a_diagnostic_surface_can_never_admit_a_tuple(self) -> None:
        self.assertEqual(self.module.classify_surface("print_mode_canary_probe"), "admitting")
        for surface in self.module.DIAGNOSTIC_SURFACES:
            with self.subTest(surface=surface):
                self.assertEqual(self.module.classify_surface(surface), "diagnostic")
        fields = collection_fields()
        fields["supported_efforts"] = dict(fields["supported_efforts"])
        fields["supported_efforts"]["opus"] = [
            *probe_ladder("opus", efforts=("low", "medium", "high", "xhigh")),
            *probe_ladder("opus", efforts=("max",), surface="models_endpoint"),
        ]
        result = self.admit(collection=self.module.build_collection_record(**fields))
        self.assertNotIn(("opus", "max"), self.admitted_pairs(result))
        self.assertEqual(self.reasons_for(result, "opus", "max"), ["surface_evidence_incomplete"])

    def test_a_corroborating_diagnostic_observation_leaves_admission_intact(self) -> None:
        result = self.admit(
            diagnostics=(
                {
                    "model": "opus",
                    "effort": "max",
                    "surface": "subagent_frontmatter",
                    "acceptance": "accepted",
                },
            )
        )
        self.assertIn(("opus", "max"), self.admitted_pairs(result))
        self.assertEqual(result.investigations, ())
        self.assertIn(("opus", "max"), result.corroborated)

    def test_a_probe_diagnostic_disagreement_is_investigated_and_excluded(self) -> None:
        result = self.admit(
            diagnostics=(
                {
                    "model": "opus",
                    "effort": "max",
                    "surface": "models_endpoint",
                    "acceptance": "unavailable",
                },
            )
        )
        self.assertNotIn(("opus", "max"), self.admitted_pairs(result))
        self.assertEqual(self.reasons_for(result, "opus", "max"), ["surface_disagreement"])
        self.assertEqual(len(result.investigations), 1)
        investigation = result.investigations[0]
        self.assertEqual(investigation["model"], "opus")
        self.assertEqual(investigation["effort"], "max")
        self.assertEqual(investigation["admitting_acceptance"], "accepted")
        self.assertEqual(investigation["diagnostic_acceptance"], "unavailable")
        self.assertEqual(investigation["diagnostic_surface"], "models_endpoint")
        self.assertEqual(investigation["disposition"], "excluded_pending_investigation")

    def test_fast_mode_is_a_topology_control_and_never_a_candidate_effort(self) -> None:
        self.assertEqual(
            self.module.canonical_effort("fast"),
            (None, "topology_control_not_candidate_effort"),
        )
        ledger = source_ledger()
        ledger["candidates"] = [
            {"model": "opus", "efforts": [*self.module.EFFORT_LADDER, "fast"]},
            {"model": "sonnet", "efforts": list(self.module.EFFORT_LADDER)},
        ]
        result = self.admit(ledger=ledger)
        self.assertNotIn(("opus", "fast"), self.admitted_pairs(result))
        self.assertEqual(
            self.reasons_for(result, "opus", "fast"),
            ["topology_control_not_candidate_effort"],
        )

    def test_an_unmapped_source_effort_records_canonical_effort_unknown(self) -> None:
        for value in ("inherit", "", "ultra", "aggregate"):
            with self.subTest(effort=value):
                self.assertEqual(
                    self.module.canonical_effort(value), (None, "canonical_effort_unknown")
                )
        ledger = source_ledger()
        ledger["candidates"] = [
            {"model": "opus", "efforts": [*self.module.EFFORT_LADDER, "inherit"]},
            {"model": "sonnet", "efforts": list(self.module.EFFORT_LADDER)},
        ]
        result = self.admit(ledger=ledger)
        self.assertEqual(
            self.reasons_for(result, "opus", "inherit"), ["canonical_effort_unknown"]
        )

    def test_the_ordered_ladder_is_probed_per_role_eligible_model(self) -> None:
        self.assertEqual(
            self.module.EFFORT_LADDER, ("low", "medium", "high", "xhigh", "max")
        )
        self.assertEqual(self.module.EFFORT_SEARCH_ORIGIN, "high")
        collection = self.module.build_collection_record(**collection_fields())
        self.assertEqual(collection["effort_search_origin"], "high")
        coverage = self.module.ladder_coverage(collection, ROLE_ELIGIBLE_MODELS)
        for model in ROLE_ELIGIBLE_MODELS:
            with self.subTest(model=model):
                self.assertEqual(coverage[model]["probed"], list(self.module.EFFORT_LADDER))
                self.assertEqual(coverage[model]["unprobed"], [])
                self.assertEqual(coverage[model]["search_origin"], "high")

    def test_an_unprobed_ladder_rung_is_recorded_as_incomplete_surface_evidence(self) -> None:
        fields = collection_fields()
        fields["supported_efforts"] = dict(fields["supported_efforts"])
        fields["supported_efforts"]["opus"] = probe_ladder(
            "opus", efforts=("low", "high", "max")
        )
        collection = self.module.build_collection_record(**fields)
        coverage = self.module.ladder_coverage(collection, ROLE_ELIGIBLE_MODELS)
        self.assertEqual(coverage["opus"]["unprobed"], ["medium", "xhigh"])
        result = self.admit(collection=collection)
        for effort in ("medium", "xhigh"):
            with self.subTest(effort=effort):
                self.assertEqual(
                    self.reasons_for(result, "opus", effort), ["surface_evidence_incomplete"]
                )


class PublicationAuthorityTests(_SuccessorFreezeModuleFixture, unittest.TestCase):
    """The publication gate fails closed: every blocking condition maps to a
    closed authority-failure member, and a blocked publication emits no freeze
    record at all (FR-028, FR-044, SC-016)."""

    def publish(self, **overrides: object) -> object:
        arguments: dict[str, object] = {
            "source_ledger": source_ledger(),
            "collection": self.module.build_collection_record(**collection_fields()),
            "freeze_id": "CAR-003-FREEZE-2026-07-24-V1",
            "published_at": "2026-07-24T18:30:00Z",
            "pinned_client_version": PINNED_CLIENT,
        }
        arguments.update(overrides)
        return self.module.publish_freeze(**arguments)

    def test_authority_failure_members_are_exactly_the_ten_closed_conditions(self) -> None:
        schema = load_json(FREEZE_SCHEMA_PATH)
        members = set(schema["properties"]["authority_failures"]["items"]["enum"])
        self.assertEqual(set(self.module.AUTHORITY_FAILURES), members)
        self.assertEqual(len(members), 10)

    def test_a_clean_collection_publishes_an_authoritative_freeze(self) -> None:
        publication = self.publish()
        self.assertEqual(publication.authority_failures, ())
        self.assertIsNotNone(publication.freeze)
        self.assertEqual(publication.freeze["authority_failures"], [])
        self.assertGreaterEqual(len(publication.freeze["admitted_tuples"]), 1)
        self.assertEqual(publication.freeze["admitting_surface"], "print_mode_canary_probe")
        self.assertEqual(
            publication.freeze["runtime_snapshot_binding"]["id"],
            publication.collection_record["collection_id"],
        )
        schema = load_json(FREEZE_SCHEMA_PATH)
        self.assertEqual(
            sorted(publication.freeze), sorted(schema["properties"])
        )
        for field in schema["required"]:
            with self.subTest(field=field):
                self.assertIn(field, publication.freeze)

    def test_every_closed_authority_failure_blocks_publication(self) -> None:
        provocations = {
            "empty_intersection": {
                "source_ledger": source_ledger(candidates=[{"model": "haiku", "efforts": ["max"]}])
            },
            "malformed_source": {"source_ledger": {"ledger_id": "no-candidates"}},
            "malformed_catalog": {
                "collection": self.module.build_collection_record(
                    **collection_fields(client_distribution=None)
                )
            },
            "stale_collection": {"pinned_client_version": "2.9.9 (Claude Code)"},
            "untrusted_collection": {
                "collection": self.module.build_collection_record(
                    **collection_fields(collection_authority="unattested_third_party")
                )
            },
            "sanitization_failed": {
                "collection": self.module.build_collection_record(
                    **collection_fields(sanitization_status="failed")
                )
            },
            "retention_failed": {
                "collection": self.module.build_collection_record(
                    **collection_fields(retention_status="failed")
                )
            },
            "identity_mismatch": {
                "runtime_snapshot_binding": {
                    "id": "CAR-003-RCC-SOMEONE-ELSE",
                    "digest": digest_of("someone-else"),
                }
            },
            "digest_mismatch": {"collection": self.tampered_collection()},
            "historical_mutation": {
                "car002_baseline": {
                    "docs/ai/research/claude-runtime-capability-snapshot.json": digest_of("wrong")
                }
            },
        }
        self.assertEqual(sorted(provocations), sorted(self.module.AUTHORITY_FAILURES))
        for member, overrides in provocations.items():
            with self.subTest(authority_failure=member):
                publication = self.publish(**overrides)
                self.assertIn(member, publication.authority_failures)
                self.assertIsNone(publication.freeze)

    def tampered_collection(self) -> dict[str, object]:
        collection = self.module.build_collection_record(**collection_fields())
        collection["client_distribution"] = "repackaged"
        return collection

    def test_missing_provenance_is_malformed_catalog_and_not_untrusted(self) -> None:
        collection = self.module.build_collection_record(**collection_fields())
        for field in ("client_version", "raw_catalog_digest", "collected_at_utc",
                      "visible_defaults", "supported_efforts", "invalidation_criteria",
                      "collection_method", "environment_boundary"):
            with self.subTest(missing=field):
                incomplete = dict(collection)
                del incomplete[field]
                publication = self.publish(collection=incomplete)
                self.assertIn("malformed_catalog", publication.authority_failures)
                self.assertNotIn("untrusted_collection", publication.authority_failures)

    def test_a_blocked_publication_emits_no_freeze_record_at_all(self) -> None:
        publication = self.publish(
            source_ledger=source_ledger(candidates=[{"model": "haiku", "efforts": ["max"]}])
        )
        self.assertIsNone(publication.freeze)
        self.assertFalse(publication.published)
        self.assertEqual(
            publication.collection_record["authority_failures"], ["empty_intersection"]
        )
        self.assertEqual(publication.collection_record["publication_state"], "diagnostic_only")
        self.assertEqual(publication.admission.admitted, ())

    def test_an_empty_intersection_never_promotes_the_archived_predecessor_tuples(self) -> None:
        publication = self.publish(
            source_ledger=source_ledger(candidates=[{"model": "haiku", "efforts": ["max"]}])
        )
        self.assertIsNone(publication.freeze)
        archived = load_json(self.module.ARCHIVED_SNAPSHOT_PATH)
        self.assertEqual(len(archived["tuple_evidence"]), 6)
        self.assertEqual(publication.admission.admitted, ())
        self.assertEqual(publication.collection_record.get("promoted_tuples", []), [])

    def test_runtime_evidence_resolving_to_the_archived_snapshot_is_rejected(self) -> None:
        archived_digests = sorted(self.module.archived_snapshot_evidence_digests())
        self.assertTrue(archived_digests)
        fields = collection_fields()
        fields["supported_efforts"] = dict(fields["supported_efforts"])
        reused = probe_ladder("opus")
        reused[-1] = dict(reused[-1], evidence_digest=archived_digests[0])
        fields["supported_efforts"]["opus"] = reused
        publication = self.publish(collection=self.module.build_collection_record(**fields))
        excluded = [
            item.reason
            for item in publication.admission.excluded
            if item.model == "opus" and item.effort == "max"
        ]
        self.assertEqual(excluded, ["availability_not_proven"])
        self.assertTrue(self.module.resolves_to_archived_snapshot(archived_digests[0]))

    def test_a_dangling_runtime_evidence_digest_is_rejected(self) -> None:
        publication = self.publish()
        self.assertIsNotNone(publication.freeze)
        for tuple_ in publication.freeze["admitted_tuples"]:
            with self.subTest(tuple_id=tuple_["candidate_route_id"]):
                self.assertIn(
                    tuple_["runtime_evidence_digest"],
                    self.module.collection_evidence_digests(publication.collection_record),
                )
        self.assertFalse(self.module.resolves_to_archived_snapshot(digest_of("not-archived")))


# The absolute-path and session-identifier provocations are assembled at run
# time from fragments. Spelling either one as a literal would leak a shape the
# tree-wide privacy scan is required to reject, and a negative control must not
# become the very leak it guards against.
ABSOLUTE_PATH_PROVOCATION = "/".join(("", "Users", "operator", ".claude"))
HOME_PATH_PROVOCATION = "/".join(("", "home", "operator", ".config", "claude"))
SESSION_ID_PROVOCATION = "-".join(
    ("6f1c2b90", "2f0a", "4a11", "9b6d", "6d1c2b90aa11")
)

SENSITIVE_PROVOCATIONS = {
    "account": {"account_id": "acct-1a2b3c"},
    "authentication": {"authorization": "Bearer sk-live-secret"},
    "credential": {"credential": "hunter2"},
    "raw_response": {"raw_output": '{"result":"ok"}'},
    "private_host": {"private_host": "runner.internal.example"},
    "absolute_path": {"config_dir": ABSOLUTE_PATH_PROVOCATION},
    "remote": {"repository_remote": "git@github.com:owner/private.git"},
    "billing": {"billing_id": "bill-99"},
    "plan": {"plan_id": "max-20x"},
}


class HistoricalImmutabilityTests(_SuccessorFreezeModuleFixture, unittest.TestCase):
    """CAR-002 stays byte-unchanged and a non-allowlisted field blocks
    publication rather than being silently stripped (FR-001, FR-027, SC-001,
    SC-015)."""

    def artifact_state(self) -> dict[str, str]:
        # Raw bytes, not decoded text: a text read collapses CRLF to LF before
        # hashing, so a baseline built that way is blind to the line-ending
        # mutation this suite exists to catch.
        return {
            path: "sha256:" + hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
            for path in self.module.CAR002_ARTIFACTS
        }

    def artifact_ids(self) -> dict[str, object]:
        snapshot = load_json(REPO_ROOT / "docs/ai/research/claude-runtime-capability-snapshot.json")
        profile = load_json(REPO_ROOT / "docs/ai/research/claude-telemetry-capability-profile.json")
        contract = load_json(REPO_ROOT / "docs/ai/research/claude-trace-contract.schema.json")
        return {
            "runtime_capability_snapshot_id": snapshot["runtime_capability_snapshot_id"],
            "telemetry_profile_id": profile["telemetry_profile_id"],
            "trace_contract_id": contract["$id"],
        }

    def test_the_archived_artifact_set_is_named_and_present(self) -> None:
        self.assertEqual(len(self.module.CAR002_ARTIFACTS), 3)
        for path in self.module.CAR002_ARTIFACTS:
            with self.subTest(artifact=path):
                self.assertTrue((REPO_ROOT / path).is_file(), path)

    def test_every_archived_path_and_id_is_byte_unchanged_after_freeze_generation(self) -> None:
        before_bytes = self.artifact_state()
        before_ids = self.artifact_ids()
        publication = self.module.publish_freeze(
            source_ledger=source_ledger(),
            collection=self.module.build_collection_record(**collection_fields()),
            freeze_id="CAR-003-FREEZE-2026-07-24-V1",
            published_at="2026-07-24T18:30:00Z",
            pinned_client_version=PINNED_CLIENT,
        )
        self.assertIsNotNone(publication.freeze)
        self.assertEqual(self.artifact_state(), before_bytes)
        self.assertEqual(self.artifact_ids(), before_ids)
        report = self.module.car002_immutability_report(before_bytes)
        self.assertEqual(report["mutated"], [])
        self.assertEqual(sorted(report["unchanged"]), sorted(self.module.CAR002_ARTIFACTS))

    def test_a_mutated_archived_artifact_is_reported_rather_than_repaired(self) -> None:
        baseline = self.artifact_state()
        baseline["docs/ai/research/claude-trace-contract.schema.json"] = digest_of("tampered")
        report = self.module.car002_immutability_report(baseline)
        self.assertEqual(
            report["mutated"], ["docs/ai/research/claude-trace-contract.schema.json"]
        )
        self.assertEqual(self.artifact_state(), self.artifact_state())

    def test_a_line_ending_only_mutation_is_still_a_mutation(self) -> None:
        """The digest must be taken over bytes, not decoded text.

        ``read_text`` opens in universal-newline mode, so a CRLF rewrite of an
        archived artifact decodes to the identical string and would hash the
        same. The immutability check would report ``unchanged`` on a file whose
        bytes moved.
        """
        original_root = self.module.REPO_ROOT
        original_artifacts = self.module.CAR002_ARTIFACTS
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "archived.json").write_bytes(b'{"a": 1}\n{"b": 2}\n')
            self.module.REPO_ROOT = root
            self.module.CAR002_ARTIFACTS = ("archived.json",)
            try:
                baseline = self.module.car002_artifact_digests()
                self.assertEqual(
                    self.module.car002_immutability_report(baseline)["mutated"], []
                )
                # Same characters, different bytes.
                (root / "archived.json").write_bytes(b'{"a": 1}\r\n{"b": 2}\r\n')
                report = self.module.car002_immutability_report(baseline)
                self.assertEqual(report["mutated"], ["archived.json"])
                self.assertEqual(report["unchanged"], [])
            finally:
                self.module.REPO_ROOT = original_root
                self.module.CAR002_ARTIFACTS = original_artifacts

    def test_every_non_allowlisted_sensitive_category_is_detected(self) -> None:
        for category, leak in SENSITIVE_PROVOCATIONS.items():
            with self.subTest(category=category):
                record = self.module.build_collection_record(**collection_fields())
                record.update(leak)
                findings = self.module.inspect_sensitive_fields(record)
                self.assertTrue(findings, f"{category} leak went undetected")
                self.assertTrue(
                    any(next(iter(leak)) in finding for finding in findings), findings
                )

    def test_a_session_identifier_or_home_path_in_nested_evidence_is_detected(self) -> None:
        record = self.module.build_collection_record(
            **collection_fields(environment_boundary=HOME_PATH_PROVOCATION)
        )
        self.assertEqual(
            self.module.inspect_sensitive_fields(record), ("environment_boundary",)
        )
        nested = self.module.build_collection_record(**collection_fields())
        nested["command_contract"] = dict(
            nested["command_contract"], canary=f"session {SESSION_ID_PROVOCATION}"
        )
        self.assertEqual(
            self.module.inspect_sensitive_fields(nested), ("command_contract.canary",)
        )

    def test_a_clean_record_reports_no_sensitive_findings(self) -> None:
        record = self.module.build_collection_record(**collection_fields())
        self.assertEqual(self.module.inspect_sensitive_fields(record), ())

    def test_a_non_allowlisted_field_blocks_publication_and_is_not_stripped(self) -> None:
        record = self.module.build_collection_record(**collection_fields())
        record["account_id"] = "acct-1a2b3c"
        publication = self.module.publish_freeze(
            source_ledger=source_ledger(),
            collection=record,
            freeze_id="CAR-003-FREEZE-2026-07-24-V1",
            published_at="2026-07-24T18:30:00Z",
            pinned_client_version=PINNED_CLIENT,
        )
        self.assertIn("sanitization_failed", publication.authority_failures)
        self.assertIsNone(publication.freeze)
        self.assertEqual(publication.collection_record["account_id"], "acct-1a2b3c")
        self.assertIn(
            "account_id", publication.collection_record["sensitive_field_findings"]
        )


TRACE_CONTRACT_PATH = REPO_ROOT / "docs" / "ai" / "research" / "claude-trace-contract.schema.json"
REPLAY_FIXTURE_PATH = (
    TEST_ROOT / "layer6-efficiency" / "fixtures" / "car-003-alias-repoint-replay.json"
)

FREEZE_BINDING = {
    "id": "CAR-003-FREEZE-2026-07-24-V1",
    "digest": digest_of("car-003-freeze-2026-07-24-v1"),
}


def complete_override_proof(**overrides: object) -> dict[str, object]:
    proof: dict[str, object] = {
        "fallback_model_unset": True,
        "fallbackModel_unset": True,
        "claude_code_subagent_model_unset": True,
        "available_models_absent": True,
        "enforce_available_models_observed": None,
        "config_dir_isolation": "partial_defense_in_depth",
        "inherit_equivalent_to_unset": None,
        "org_restriction_gap": None,
    }
    proof.update(overrides)
    return proof


def repoint_observation(**overrides: object) -> dict[str, object]:
    """The five observables plus the classification inputs (FR-039)."""
    observation: dict[str, object] = {
        "requested_alias": "opus",
        "freeze_bound_identity": "claude-opus-5",
        "freeze_bound_identity_source": "car_003_successor_freeze",
        "candidate_freeze_binding": dict(FREEZE_BINDING),
        "run_observed_identity": "claude-opus-4-8",
        "env_override_proof": complete_override_proof(),
        "client_version_at_freeze": PINNED_CLIENT,
        "client_version_at_run": PINNED_CLIENT,
        "requested_route_unchanged": True,
        "plugin_initiated_substitution": False,
        "behavioral_divergence_observed": False,
        "execution_trace_binding": {
            "id": "CAR-003-TRACE-0001",
            "digest": digest_of("car-003-trace-0001"),
        },
        "attribution_id": "CAR-003-ATTR-0001",
        "recorded_at": "2026-07-24T18:45:00Z",
        "validated_by": "synthetic_replay_fixture",
    }
    observation.update(overrides)
    return observation


class AliasRepointDetectionTests(_SuccessorFreezeModuleFixture, unittest.TestCase):
    """Alias re-point detection reads five observables and attributes a
    divergence only when the elimination argument holds (FR-039, FR-045,
    SC-017)."""

    def detect(self, **overrides: object) -> object:
        return self.module.detect_alias_repoint(
            repoint_observation(**overrides), published_freeze_binding=dict(FREEZE_BINDING)
        )

    def test_the_detector_declares_exactly_the_five_observables(self) -> None:
        self.assertEqual(
            self.module.ALIAS_REPOINT_OBSERVABLES,
            (
                "requested_alias",
                "freeze_bound_identity",
                "run_observed_identity",
                "env_override_proof",
                "client_version",
            ),
        )

    def test_the_override_proof_members_are_reused_from_the_frozen_contract(self) -> None:
        frozen = load_json(TRACE_CONTRACT_PATH)["$defs"]["unsetProof"]["required"]
        self.assertEqual(list(self.module.ENV_OVERRIDE_PROOF_MEMBERS), list(frozen))
        self.assertEqual(len(frozen), 8)

    def test_an_unchanged_route_with_proven_unset_overrides_is_platform_attributed(self) -> None:
        finding = self.detect()
        self.assertEqual(finding.attribution, "platform_route_change")
        self.assertTrue(finding.admits)
        self.assertIsNone(finding.exclusion_reason)
        self.assertNotEqual(finding.attribution, "resolver_fallback")
        self.assertEqual(finding.record["attribution"], "platform_route_change")
        self.assertIs(finding.record["attribution_bounded"], True)
        self.assertEqual(finding.record["record_kind"], "alias_repoint_attribution")
        self.assertEqual(
            finding.record["freeze_bound_identity_source"], "car_003_successor_freeze"
        )
        self.assertEqual(finding.record["candidate_freeze_binding"], dict(FREEZE_BINDING))
        self.assertEqual(finding.record["validated_by"], "synthetic_replay_fixture")

    def test_the_emitted_record_matches_the_additive_contract(self) -> None:
        finding = self.detect()
        schema = load_json(ADDITIVE_SCHEMA_PATH)["$defs"]["aliasRepointAttribution"]
        for field in schema["required"]:
            with self.subTest(field=field):
                self.assertIn(field, finding.record)
        self.assertEqual(set(finding.record) - set(schema["properties"]), set())

    def test_a_plugin_initiated_substitution_is_resolver_fallback(self) -> None:
        finding = self.detect(plugin_initiated_substitution=True)
        self.assertEqual(finding.attribution, "resolver_fallback")
        self.assertTrue(finding.admits)

    def test_an_incomplete_override_proof_blocks_admission(self) -> None:
        partial = complete_override_proof()
        del partial["org_restriction_gap"]
        finding = self.detect(env_override_proof=partial)
        self.assertEqual(finding.attribution, "alias_repoint_unresolved")
        self.assertFalse(finding.admits)
        self.assertEqual(finding.exclusion_reason, "alias_repoint_unresolved")
        self.assertIs(finding.record["override_proof_complete"], False)

    def test_a_false_subagent_model_unset_blocks_admission(self) -> None:
        finding = self.detect(
            env_override_proof=complete_override_proof(claude_code_subagent_model_unset=False)
        )
        self.assertEqual(finding.attribution, "alias_repoint_unresolved")
        self.assertFalse(finding.admits)

    def test_a_changed_client_version_blocks_admission(self) -> None:
        finding = self.detect(client_version_at_run="2.2.001 (Claude Code)")
        self.assertEqual(finding.attribution, "alias_repoint_unresolved")
        self.assertFalse(finding.admits)

    def test_a_binding_resolving_to_the_archived_snapshot_blocks_admission(self) -> None:
        archived = load_json(self.module.ARCHIVED_SNAPSHOT_PATH)
        finding = self.module.detect_alias_repoint(
            repoint_observation(
                candidate_freeze_binding={
                    "id": archived["runtime_capability_snapshot_id"],
                    "digest": digest_of("archived-snapshot"),
                }
            ),
            published_freeze_binding=dict(FREEZE_BINDING),
        )
        self.assertEqual(finding.attribution, "alias_repoint_unresolved")
        self.assertFalse(finding.admits)

    def test_a_binding_that_is_not_the_published_freeze_blocks_admission(self) -> None:
        finding = self.detect(
            candidate_freeze_binding={
                "id": FREEZE_BINDING["id"],
                "digest": digest_of("some-other-freeze"),
            }
        )
        self.assertEqual(finding.attribution, "alias_repoint_unresolved")
        self.assertFalse(finding.admits)

    def test_a_run_time_route_resolution_source_is_not_accepted_as_the_freeze(self) -> None:
        finding = self.detect(freeze_bound_identity_source="route_resolution")
        self.assertEqual(finding.attribution, "alias_repoint_unresolved")
        self.assertFalse(finding.admits)

    def test_a_behavioral_difference_without_identity_change_is_a_separate_condition(self) -> None:
        finding = self.detect(
            run_observed_identity="claude-opus-5", behavioral_divergence_observed=True
        )
        self.assertEqual(finding.attribution, "no_divergence")
        self.assertTrue(finding.behavioral_only)
        self.assertIs(finding.record["behavioral_only_divergence"], True)
        self.assertTrue(finding.admits)

    def test_no_divergence_is_recorded_when_the_identities_agree(self) -> None:
        finding = self.detect(run_observed_identity="claude-opus-5")
        self.assertEqual(finding.attribution, "no_divergence")
        self.assertFalse(finding.behavioral_only)
        self.assertTrue(finding.admits)

    def test_the_synthetic_replay_fixture_validates_the_detector_in_band(self) -> None:
        fixture = load_json(REPLAY_FIXTURE_PATH)
        self.assertEqual(fixture["fixture_kind"], "alias_repoint_replay")
        binding = fixture["published_freeze_binding"]
        cases = fixture["cases"]
        # FR-057: bounded in size, so suite cost never scales with campaigns.
        self.assertLessEqual(len(cases), 8)
        self.assertGreaterEqual(len(cases), 4)
        for case in cases:
            with self.subTest(case=case["case_id"]):
                finding = self.module.detect_alias_repoint(
                    case["observation"], published_freeze_binding=binding
                )
                self.assertEqual(finding.attribution, case["expected_attribution"])
                self.assertIs(finding.admits, case["expected_admits"])

    def test_the_replay_fixture_never_sets_the_override_the_proof_requires_unset(self) -> None:
        fixture = load_json(REPLAY_FIXTURE_PATH)
        divergent = [
            case
            for case in fixture["cases"]
            if case["observation"]["run_observed_identity"]
            != case["observation"]["freeze_bound_identity"]
        ]
        self.assertTrue(divergent, "the fixture supplies no divergent observed identity")
        for case in divergent:
            if case["expected_attribution"] != "platform_route_change":
                continue
            with self.subTest(case=case["case_id"]):
                proof = case["observation"]["env_override_proof"]
                for member in self.module.OVERRIDE_UNSET_BOOLEANS:
                    self.assertIs(proof[member], True, member)


def evidence_graph() -> dict[str, object]:
    return {
        "freeze_admission": "published",
        "unexecuted_bindings": ["BIND-0003", "BIND-0004"],
        "experiment_bundles": ["EXP-0001"],
        "score_bundles": ["SCORE-0001"],
        "decision_bundles": ["DEC-0001"],
        "execution_traces": ["CAR-003-TRACE-0001"],
        "treatment_records": ["TREAT-0001"],
        "bound_pairs": ["PAIR-0001"],
        "in_flight_attempts": [
            {"attempt_id": "ATT-0001", "requested_alias": "opus"},
            {"attempt_id": "ATT-0002", "requested_alias": "sonnet"},
        ],
    }


class RefreshTriggerTests(_SuccessorFreezeModuleFixture, unittest.TestCase):
    """Four versioned refresh triggers invalidate additively and never rebind
    an already-bound pair (FR-041)."""

    def test_the_trigger_set_matches_the_freeze_contract(self) -> None:
        schema = load_json(FREEZE_SCHEMA_PATH)
        members = schema["properties"]["invalidation_triggers"]["items"]["properties"]
        self.assertEqual(set(self.module.REFRESH_TRIGGERS), set(members["trigger"]["enum"]))
        self.assertEqual(len(self.module.REFRESH_TRIGGERS), 4)
        declared = self.module.INVALIDATION_TRIGGERS
        self.assertEqual(len(declared), 4)
        for entry in declared:
            with self.subTest(trigger=entry["trigger"]):
                self.assertEqual(sorted(entry), ["invalidates", "survives", "trigger"])
                self.assertLessEqual(set(entry["invalidates"]), set(members["invalidates"]["items"]["enum"]))
                self.assertLessEqual(set(entry["survives"]), set(members["survives"]["items"]["enum"]))

    def test_every_trigger_invalidates_admission_and_unexecuted_bindings(self) -> None:
        for trigger in self.module.REFRESH_TRIGGERS:
            with self.subTest(trigger=trigger):
                outcome = self.module.apply_refresh_trigger(trigger, evidence_graph())
                self.assertIs(outcome["invalidated"]["freeze_admission"], True)
                self.assertEqual(
                    outcome["invalidated"]["unexecuted_bindings"], ["BIND-0003", "BIND-0004"]
                )

    def test_every_trigger_additively_invalidates_the_downstream_bundles(self) -> None:
        for trigger in self.module.REFRESH_TRIGGERS:
            with self.subTest(trigger=trigger):
                outcome = self.module.apply_refresh_trigger(trigger, evidence_graph())
                self.assertEqual(outcome["invalidated"]["experiment_bundles"], ["EXP-0001"])
                self.assertEqual(outcome["invalidated"]["score_bundles"], ["SCORE-0001"])
                self.assertEqual(outcome["invalidated"]["decision_bundles"], ["DEC-0001"])
                self.assertIs(outcome["additive"], True)

    def test_traces_records_and_bound_pairs_survive_marked_not_rebound(self) -> None:
        for trigger in self.module.REFRESH_TRIGGERS:
            with self.subTest(trigger=trigger):
                outcome = self.module.apply_refresh_trigger(trigger, evidence_graph())
                self.assertEqual(outcome["survived"]["execution_traces"], ["CAR-003-TRACE-0001"])
                self.assertEqual(outcome["survived"]["treatment_records"], ["TREAT-0001"])
                self.assertEqual(outcome["survived"]["bound_pairs"], ["PAIR-0001"])
                self.assertEqual(
                    sorted(outcome["marked_invalidated"]),
                    ["CAR-003-TRACE-0001", "PAIR-0001", "TREAT-0001"],
                )
                self.assertEqual(outcome["rebound"], [])

    def test_an_alias_repoint_marks_only_that_alias_in_flight_attempts_non_scorable(self) -> None:
        outcome = self.module.apply_refresh_trigger(
            "alias_repoint", evidence_graph(), repointed_alias="opus"
        )
        self.assertEqual(outcome["non_scorable_attempts"], ["ATT-0001"])
        self.assertIn("in_flight_attempts_for_alias", self.module.refresh_trigger_effects("alias_repoint")["invalidates"])

    def test_other_triggers_do_not_touch_in_flight_attempts(self) -> None:
        for trigger in ("client_change", "catalog_change", "source_ledger_change"):
            with self.subTest(trigger=trigger):
                outcome = self.module.apply_refresh_trigger(trigger, evidence_graph())
                self.assertEqual(outcome["non_scorable_attempts"], [])
                self.assertNotIn(
                    "in_flight_attempts_for_alias",
                    self.module.refresh_trigger_effects(trigger)["invalidates"],
                )

    def test_a_source_ledger_change_alone_admits_no_runtime_unsupported_tuple(self) -> None:
        outcome = self.module.apply_refresh_trigger("source_ledger_change", evidence_graph())
        self.assertIs(outcome["admits_runtime_unsupported"], False)
        collection = self.module.build_collection_record(**collection_fields())
        widened = source_ledger()
        widened["candidates"] = [
            *widened["candidates"],
            {"model": "haiku", "efforts": ["max"]},
        ]
        readmitted = self.module.admit_tuples(
            source_ledger=widened, collection=collection, diagnostics=()
        )
        pairs = {(item["model"], item["effort"]) for item in readmitted.admitted}
        self.assertNotIn(("haiku", "max"), pairs)
        self.assertEqual(
            [item.reason for item in readmitted.excluded
             if item.model == "haiku" and item.effort == "max"],
            ["effort_source_not_admitted"],
        )

    def test_an_unknown_trigger_is_refused(self) -> None:
        with self.assertRaises(self.module.SuccessorFreezeError):
            self.module.apply_refresh_trigger("vibes_changed", evidence_graph())


class FailClosedEvidenceTests(_SuccessorFreezeModuleFixture, unittest.TestCase):
    """Missing provenance is refused rather than promoted. An observation that
    names no surface admits nothing, an attribution with no published freeze to
    compare against stays unresolved, published diagnostic evidence verifies
    against its own digest, and no emitted record aliases module state
    (FR-002, FR-004, FR-033, FR-039)."""

    def unlabeled_collection(self) -> dict[str, object]:
        """A collection whose opus ladder carries no ``surface`` on any rung."""
        fields = collection_fields()
        fields["supported_efforts"] = dict(fields["supported_efforts"])
        fields["supported_efforts"]["opus"] = [
            {key: value for key, value in observation.items() if key != "surface"}
            for observation in probe_ladder("opus")
        ]
        return self.module.build_collection_record(**fields)

    def publish(self, **overrides: object) -> object:
        arguments: dict[str, object] = {
            "source_ledger": source_ledger(),
            "collection": self.module.build_collection_record(**collection_fields()),
            "freeze_id": "CAR-003-FREEZE-2026-07-24-V1",
            "published_at": "2026-07-24T18:30:00Z",
            "pinned_client_version": PINNED_CLIENT,
        }
        arguments.update(overrides)
        return self.module.publish_freeze(**arguments)

    def test_the_unlabeled_surface_sentinel_is_refused_by_the_classifier(self) -> None:
        self.assertNotEqual(self.module.UNLABELED_SURFACE, self.module.ADMITTING_SURFACE)
        self.assertNotIn(self.module.UNLABELED_SURFACE, self.module.DIAGNOSTIC_SURFACES)
        with self.assertRaises(self.module.SuccessorFreezeError):
            self.module.classify_surface(self.module.UNLABELED_SURFACE)

    def test_an_unlabeled_observation_never_admits_a_tuple(self) -> None:
        result = self.module.admit_tuples(
            source_ledger=source_ledger(), collection=self.unlabeled_collection()
        )
        admitted = {(item["model"], item["effort"]) for item in result.admitted}
        for effort in self.module.EFFORT_LADDER:
            with self.subTest(effort=effort):
                self.assertNotIn(("opus", effort), admitted)
                self.assertEqual(
                    [
                        item.reason
                        for item in result.excluded
                        if item.model == "opus" and item.effort == effort
                    ],
                    ["surface_evidence_incomplete"],
                )
        # The labelled half of the same collection is untouched.
        self.assertIn(("sonnet", "max"), admitted)

    def test_an_unlabeled_observation_leaves_every_ladder_rung_unprobed(self) -> None:
        coverage = self.module.ladder_coverage(self.unlabeled_collection(), ROLE_ELIGIBLE_MODELS)
        self.assertEqual(coverage["opus"]["probed"], [])
        self.assertEqual(coverage["opus"]["unprobed"], list(self.module.EFFORT_LADDER))
        self.assertEqual(coverage["sonnet"]["unprobed"], [])

    def test_an_unlabeled_collection_publishes_no_freeze_for_that_model(self) -> None:
        publication = self.publish(collection=self.unlabeled_collection())
        self.assertIsNotNone(publication.freeze)
        admitted = {item["model"] for item in publication.freeze["admitted_tuples"]}
        self.assertEqual(admitted, {"sonnet"})

    def test_an_attribution_with_no_published_freeze_binding_is_unresolved(self) -> None:
        finding = self.module.detect_alias_repoint(repoint_observation())
        self.assertEqual(finding.attribution, "alias_repoint_unresolved")
        self.assertFalse(finding.admits)
        self.assertEqual(finding.exclusion_reason, "alias_repoint_unresolved")

    def test_an_empty_candidate_freeze_binding_is_unresolved(self) -> None:
        for published in (None, dict(FREEZE_BINDING)):
            with self.subTest(published_freeze_binding=published):
                finding = self.module.detect_alias_repoint(
                    repoint_observation(candidate_freeze_binding={}),
                    published_freeze_binding=published,
                )
                self.assertEqual(finding.attribution, "alias_repoint_unresolved")
                self.assertFalse(finding.admits)

    def test_the_emitted_diagnostic_record_verifies_against_its_own_digest(self) -> None:
        publications = {
            "published": self.publish(),
            "diagnostic_only": self.publish(
                source_ledger=source_ledger(candidates=[{"model": "haiku", "efforts": ["max"]}])
            ),
        }
        for state, publication in sorted(publications.items()):
            with self.subTest(publication_state=state):
                record = publication.collection_record
                self.assertEqual(record["publication_state"], state)
                self.assertEqual(
                    record["publication_record_digest"],
                    self.module.record_digest(record, digest_field="publication_record_digest"),
                )
                self.assertEqual(self.module.inspect_sensitive_fields(record), ())

    def test_a_published_freeze_never_aliases_the_module_trigger_lists(self) -> None:
        publication = self.publish()
        self.assertIsNotNone(publication.freeze)
        for entry in publication.freeze["invalidation_triggers"]:
            entry["invalidates"].append("everything_everywhere")
            entry["survives"].clear()
        for entry in self.module.INVALIDATION_TRIGGERS:
            with self.subTest(trigger=entry["trigger"]):
                self.assertNotIn("everything_everywhere", entry["invalidates"])
                self.assertEqual(
                    list(entry["survives"]),
                    ["execution_traces", "treatment_records", "bound_pairs"],
                )
        for entry in self.publish().freeze["invalidation_triggers"]:
            with self.subTest(republished=entry["trigger"]):
                self.assertNotIn("everything_everywhere", entry["invalidates"])
                self.assertTrue(entry["survives"])


TEST_CASES = (
    ExclusionTaxonomyTests,
    CollectionRecordProvenanceTests,
    AdmissionAndLadderTests,
    PublicationAuthorityTests,
    HistoricalImmutabilityTests,
    AliasRepointDetectionTests,
    RefreshTriggerTests,
    FailClosedEvidenceTests,
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-successor-capability-freeze"))
