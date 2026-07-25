#!/usr/bin/env python3
"""Focused deterministic tests for the G56R-003 governed role corpus."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/qualification_corpus.py"
SCHEMA_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/contracts/role-corpus.schema.json"
FIXTURE_ROOT = ROOT / "tests/speckit-pro/layer6-efficiency/fixtures-codex"
CORPUS_MANIFEST_PATH = FIXTURE_ROOT / "corpus-manifest.json"

EXPECTED_ROLE_ORDER = (
    "analyze-executor",
    "autopilot-fast-helper",
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
EXPECTED_REQUIRED_CORE = (
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
EXPECTED_EXECUTABLE_CORE = (
    "analyze-executor",
    "checklist-executor",
    "clarify-executor",
    "codebase-analyst",
    "domain-researcher",
    "implement-executor",
    "phase-executor",
    "spec-context-analyst",
    "uat-runbook-author",
)
EXPECTED_NON_EXECUTABLE_CORE = ("consensus-synthesizer", "gate-validator")
EXPECTED_HELPERS = ("autopilot-fast-helper",)
EXPECTED_PUBLIC_API = frozenset(
    {
        "EXECUTABLE_CORE_ROLES",
        "GOVERNED_ROLE_ORDER",
        "NON_EXECUTABLE_CORE_ROLES",
        "OPTIONAL_HELPER_ROLES",
        "PARTITION_TYPES",
        "REQUIRED_CORE_ROLES",
        "ROLE_CORPUS_SCHEMA_VERSION",
        "canonical_bytes",
        "corpus_statistics",
        "digest",
        "schedule_admitted_roles",
        "validate_role_corpus",
    }
)
PARTITION_DIGEST = "sha256:345cf184dd42fb4644f88c141053eb821c484500ac4e15ac94d59bd7673367d6"
FREEZE_ID = "sha256:734672cea5a83e5b8f296ee604f7cb8d93e0a5296a3f864b873fe78bfe518f1e"
CALIBRATION_TIME = "2026-07-24T00:00:00Z"


def load_corpus_module(name: str | None = None):
    if not MODULE_PATH.exists():
        def missing(*_args, **_kwargs):
            raise AssertionError(f"missing implementation: {MODULE_PATH}")

        class MissingModule:
            __all__: tuple[str, ...] = ()
            ROLE_CORPUS_SCHEMA_VERSION = ""
            GOVERNED_ROLE_ORDER: tuple[str, ...] = ()
            REQUIRED_CORE_ROLES: tuple[str, ...] = ()
            EXECUTABLE_CORE_ROLES: tuple[str, ...] = ()
            NON_EXECUTABLE_CORE_ROLES: tuple[str, ...] = ()
            OPTIONAL_HELPER_ROLES: tuple[str, ...] = ()
            PARTITION_TYPES: tuple[str, ...] = ()
            canonical_bytes = staticmethod(missing)
            digest = staticmethod(missing)
            validate_role_corpus = staticmethod(missing)
            corpus_statistics = staticmethod(missing)
            schedule_admitted_roles = staticmethod(missing)

        return MissingModule()

    module_name = name or f"_g56r_003_qualification_corpus_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: object) -> str:
    if isinstance(value, bytes):
        payload = value
    else:
        payload = canonical_bytes(value)
    return "sha256:" + hashlib.sha256(payload).hexdigest()


SHARED_PARTITION_BINDING = {
    "partition_id": "g56r-003-calibration",
    "partition_type": "calibration",
    "partition_digest": digest(
        {
            "partition_id": "g56r-003-calibration",
            "partition_type": "calibration",
        }
    ),
    "qualification_eligible": False,
}


def source_path(role_id: str) -> str:
    if role_id in EXPECTED_NON_EXECUTABLE_CORE:
        return f"speckit-pro/agents/{role_id}.md"
    return f"speckit-pro/codex-agents/{role_id}.toml"


def file_digest(relative_path: str) -> str:
    return digest((ROOT / relative_path).read_bytes())


def fixture_path(role_id: str) -> Path:
    return FIXTURE_ROOT / role_id / "fixture.json"


def read_fixture(role_id: str) -> tuple[dict, bytes]:
    path = fixture_path(role_id)
    if not path.is_file():
        raise AssertionError(f"missing role fixture: {path.relative_to(ROOT)}")
    raw = path.read_bytes()
    fixture = json.loads(raw.decode("utf-8"))
    if raw != canonical_bytes(fixture) + b"\n":
        raise AssertionError(f"fixture is not canonical JSON plus LF: {path.relative_to(ROOT)}")
    return fixture, raw


def read_corpus_manifest() -> tuple[dict, bytes]:
    if not CORPUS_MANIFEST_PATH.is_file():
        raise AssertionError(f"missing corpus manifest: {CORPUS_MANIFEST_PATH.relative_to(ROOT)}")
    raw = CORPUS_MANIFEST_PATH.read_bytes()
    manifest = json.loads(raw.decode("utf-8"))
    if raw != canonical_bytes(manifest) + b"\n":
        raise AssertionError("corpus manifest must use canonical compact UTF-8 JSON plus LF")
    return manifest, raw


def corpus_digest_payload(manifest: dict) -> dict:
    return {
        "corpus_id": manifest["corpus_id"],
        "corpus_version": manifest["corpus_version"],
        "fixture_byte_digests": [
            {
                "fixture_digest": digest(read_fixture(role_id)[1]),
                "fixture_path": str(fixture_path(role_id).relative_to(ROOT)),
                "role_id": role_id,
            }
            for role_id in EXPECTED_ROLE_ORDER
        ],
        "partition_binding": manifest["partition_binding"],
    }


def partition_binding(partition_id: str = "g56r-003-calibration") -> dict:
    return {
        "partition_id": partition_id,
        "partition_type": "calibration",
        "partition_digest": PARTITION_DIGEST,
        "qualification_eligible": False,
    }


def route_binding(role_id: str, *, admitted: bool = True) -> dict:
    payload = {
        "role_id": role_id,
        "route_id": f"g56r-003-route-{role_id}",
        "candidate_freeze_id": FREEZE_ID,
        "agent_contract_id": f"g56r-003-agent-contract-{role_id}",
    }
    return {
        **payload,
        "route_digest": digest(payload),
        "admission_status": "admitted" if admitted else "excluded",
    }


def role_contract(role_id: str) -> dict:
    fixture, _raw = read_fixture(role_id)
    fixture = copy.deepcopy(fixture)
    fixture["partition_binding"] = partition_binding()
    return fixture


def valid_corpus(*, role_order: tuple[str, ...] = tuple(reversed(EXPECTED_ROLE_ORDER))) -> dict:
    roles = [role_contract(role_id) for role_id in role_order]
    corpus = {
        "schema_version": "role-corpus.v1",
        "corpus_id": "g56r-003-role-corpus-v1",
        "corpus_version": "1.0.0",
        "corpus_digest": "",
        "partition_binding": partition_binding(),
        "roles": roles,
    }
    corpus["corpus_digest"] = digest(corpus_digest_payload(corpus))
    return corpus


def admitted_route_ids(corpus: dict) -> set[str]:
    return {
        binding["route_id"]
        for role in corpus["roles"]
        for binding in role["route_bindings"]
    }


def active_route_bindings(corpus: dict) -> list[dict]:
    return [
        copy.deepcopy(binding)
        for role in corpus["roles"]
        for binding in role["route_bindings"]
    ]


def trusted_route_authority_binding(corpus: dict) -> dict:
    routes = sorted(
        active_route_bindings(corpus),
        key=lambda item: (item["role_id"], item["route_id"]),
    )
    return {
        "id": FREEZE_ID,
        "digest": digest(routes),
    }


class CodexQualificationCorpusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = load_corpus_module()

    def assert_rejects(self, mutator, message: str) -> None:
        corpus = valid_corpus()
        mutator(corpus)
        with self.assertRaisesRegex(ValueError, message):
            self.corpus.validate_role_corpus(corpus, repo_root=ROOT)

    def test_public_api_and_schema_are_closed_to_exact_role_contract(self) -> None:
        self.assertEqual(frozenset(self.corpus.__all__), EXPECTED_PUBLIC_API)
        self.assertEqual(tuple(self.corpus.GOVERNED_ROLE_ORDER), EXPECTED_ROLE_ORDER)
        self.assertEqual(tuple(self.corpus.REQUIRED_CORE_ROLES), EXPECTED_REQUIRED_CORE)
        self.assertEqual(tuple(self.corpus.EXECUTABLE_CORE_ROLES), EXPECTED_EXECUTABLE_CORE)
        self.assertEqual(tuple(self.corpus.NON_EXECUTABLE_CORE_ROLES), EXPECTED_NON_EXECUTABLE_CORE)
        self.assertEqual(tuple(self.corpus.OPTIONAL_HELPER_ROLES), EXPECTED_HELPERS)

        self.assertTrue(SCHEMA_PATH.exists(), f"missing schema: {SCHEMA_PATH}")
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["schema_version"]["const"], self.corpus.ROLE_CORPUS_SCHEMA_VERSION)
        self.assertEqual(
            set(schema["required"]),
            {"schema_version", "corpus_id", "corpus_version", "corpus_digest", "partition_binding", "roles"},
        )
        roles_schema = schema["properties"]["roles"]
        self.assertEqual(roles_schema["minItems"], 12)
        self.assertEqual(roles_schema["maxItems"], 12)
        role_schema = schema["$defs"]["roleContract"]
        self.assertFalse(role_schema["additionalProperties"])
        self.assertEqual(role_schema["properties"]["role_id"]["enum"], list(EXPECTED_ROLE_ORDER))
        self.assertEqual(
            set(role_schema["required"]),
            {
                "role_id",
                "required_core",
                "optional_helper",
                "executable",
                "source_binding",
                "fixture_binding",
                "objective_binding",
                "partition_binding",
                "permitted_tools",
                "sandbox",
                "expected_artifacts",
                "acceptance_oracle",
                "independent_review",
                "route_bindings",
            },
        )
        for definition in (
            "sourceBinding",
            "fixtureBinding",
            "objectiveBinding",
            "partitionBinding",
            "sandbox",
            "expectedArtifact",
            "acceptanceOracle",
            "independentReview",
            "routeBinding",
        ):
            with self.subTest(definition=definition):
                self.assertFalse(schema["$defs"][definition]["additionalProperties"])

    def test_valid_corpus_normalizes_exact_membership_and_primary_stats(self) -> None:
        corpus = valid_corpus()
        original = copy.deepcopy(corpus)
        validated = self.corpus.validate_role_corpus(corpus, repo_root=ROOT)

        self.assertEqual(corpus, original, "validator must not mutate caller data")
        self.assertEqual([role["role_id"] for role in validated["roles"]], list(EXPECTED_ROLE_ORDER))
        stats = self.corpus.corpus_statistics(validated)
        self.assertEqual(
            stats,
            {
                "total_roles": 12,
                "required_core_roles": 11,
                "optional_helper_roles": 1,
                "executable_required_core_roles": 9,
                "non_executable_required_core_roles": 2,
                "executable_optional_helper_roles": 1,
                "required_core_primary_role_ids": list(EXPECTED_REQUIRED_CORE),
                "optional_helper_role_ids": ["autopilot-fast-helper"],
            },
        )

    def test_corpus_and_fixture_content_digests_are_recomputed(self) -> None:
        with self.subTest(digest="corpus"):
            corpus = valid_corpus()
            corpus["corpus_digest"] = "sha256:" + "f" * 64
            with self.assertRaisesRegex(ValueError, "corpus digest"):
                self.corpus.validate_role_corpus(corpus, repo_root=ROOT)

        with self.subTest(digest="fixture"):
            corpus = valid_corpus()
            role = next(item for item in corpus["roles"] if item["role_id"] == "phase-executor")
            role["fixture_binding"]["fixture_digest"] = "sha256:" + "f" * 64
            with self.assertRaisesRegex(ValueError, "fixture digest"):
                self.corpus.validate_role_corpus(corpus, repo_root=ROOT)

    def test_committed_corpus_manifest_serializes_all_disjoint_fixture_groups(self) -> None:
        manifest, _raw = read_corpus_manifest()

        self.assertEqual(manifest["schema_version"], self.corpus.ROLE_CORPUS_SCHEMA_VERSION)
        self.assertEqual(manifest["corpus_id"], "g56r-003-role-corpus-v1")
        self.assertEqual(manifest["corpus_version"], "1.0.0")
        self.assertEqual(manifest["corpus_digest"], self.corpus.digest(corpus_digest_payload(manifest)))
        self.assertEqual(manifest["partition_binding"], SHARED_PARTITION_BINDING)

        fixture_bindings_by_role = {}
        source_bindings_by_role = {}
        for role_id in EXPECTED_ROLE_ORDER:
            fixture, raw = read_fixture(role_id)
            self.assertEqual(fixture["role_id"], role_id)
            self.assertEqual(self.corpus.digest(raw), digest(raw))
            fixture_bindings_by_role[role_id] = fixture["fixture_binding"]
            source_bindings_by_role[role_id] = fixture["source_binding"]

        validated = self.corpus.validate_role_corpus(manifest, repo_root=ROOT)
        self.assertEqual([role["role_id"] for role in validated["roles"]], list(EXPECTED_ROLE_ORDER))
        self.assertEqual(
            {role["partition_binding"]["partition_id"] for role in validated["roles"]},
            {SHARED_PARTITION_BINDING["partition_id"]},
        )
        self.assertTrue(
            all(role["partition_binding"] == SHARED_PARTITION_BINDING for role in validated["roles"]),
            "all serialized role contracts must bind the sole calibration partition",
        )
        self.assertEqual(
            {role["partition_binding"]["partition_type"] for role in validated["roles"]},
            {"calibration"},
        )
        self.assertFalse(any(role["partition_binding"]["qualification_eligible"] for role in validated["roles"]))

        self.assertEqual(
            self.corpus.validate_role_corpus(manifest),
            validated,
            "the default corpus root must resolve to the repository",
        )
        for role in validated["roles"]:
            role_id = role["role_id"]
            self.assertEqual(role["fixture_binding"], fixture_bindings_by_role[role_id])
            self.assertEqual(role["source_binding"], source_bindings_by_role[role_id])

        stats = self.corpus.corpus_statistics(validated)
        self.assertEqual(stats["total_roles"], 12)
        self.assertEqual(stats["required_core_roles"], 11)
        self.assertEqual(stats["executable_required_core_roles"], 9)
        self.assertEqual(stats["non_executable_required_core_roles"], 2)
        self.assertEqual(stats["optional_helper_roles"], 1)
        self.assertEqual(stats["executable_optional_helper_roles"], 1)
        self.assertEqual(stats["required_core_primary_role_ids"], list(EXPECTED_REQUIRED_CORE))
        self.assertEqual(stats["optional_helper_role_ids"], ["autopilot-fast-helper"])
        self.assertNotIn("autopilot-fast-helper", stats["required_core_primary_role_ids"])

    def test_runtime_timestamp_validation_accepts_schema_valid_rfc3339_utc_forms(self) -> None:
        for value in (
            "2026-07-24T00:00:00.123Z",
            "2026-07-24T00:00:00+00:00",
        ):
            with self.subTest(value=value):
                self.assertEqual(self.corpus._timestamp(value, "timestamp"), value)
        for value in (
            "2026-07-24 00:00:00+00:00",
            "2026-07-24T00:00:00+01:00",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "RFC3339 UTC"):
                    self.corpus._timestamp(value, "timestamp")

    def test_committed_corpus_manifest_schedules_only_executable_roles_with_skip_reasons(self) -> None:
        manifest, _raw = read_corpus_manifest()
        validated = self.corpus.validate_role_corpus(manifest, repo_root=ROOT)
        admitted = admitted_route_ids(validated)
        schedule = self.corpus.schedule_admitted_roles(
            validated,
            admitted_route_ids=admitted,
            active_route_bindings=active_route_bindings(validated),
            trusted_route_authority_binding=trusted_route_authority_binding(
                validated
            ),
        )

        self.assertEqual([item["role_id"] for item in schedule["required_core"]], list(EXPECTED_EXECUTABLE_CORE))
        self.assertEqual([item["role_id"] for item in schedule["optional_helpers"]], ["autopilot-fast-helper"])
        self.assertEqual([item["role_id"] for item in schedule["unschedulable_governed"]], list(EXPECTED_NON_EXECUTABLE_CORE))
        self.assertEqual(len(schedule["required_core"]) + len(schedule["optional_helpers"]), 10)
        self.assertEqual(len(schedule["required_core"]), 9)
        self.assertEqual(len(schedule["optional_helpers"]), 1)
        self.assertTrue(all(item["route_bindings"] for item in schedule["required_core"]))
        self.assertTrue(all(item["route_bindings"] for item in schedule["optional_helpers"]))
        self.assertTrue(all(not item["route_bindings"] for item in schedule["unschedulable_governed"]))
        self.assertEqual(
            {tuple(item["skip_reasons"]) for item in schedule["unschedulable_governed"]},
            {("non_executable_governed_role",)},
        )

    def test_membership_and_executability_fail_closed(self) -> None:
        self.assert_rejects(
            lambda corpus: corpus["roles"].pop(),
            "exactly twelve",
        )
        self.assert_rejects(
            lambda corpus: corpus["roles"].append(role_contract("phase-executor")),
            "exactly twelve",
        )

        def duplicate_role(corpus: dict) -> None:
            corpus["roles"][0] = copy.deepcopy(corpus["roles"][1])

        self.assert_rejects(duplicate_role, "duplicate role")

        def helper_marked_required(corpus: dict) -> None:
            next(role for role in corpus["roles"] if role["role_id"] == "autopilot-fast-helper")["required_core"] = True

        self.assert_rejects(helper_marked_required, "helper")

        def gate_marked_executable(corpus: dict) -> None:
            role = next(item for item in corpus["roles"] if item["role_id"] == "gate-validator")
            role["executable"] = True
            role["route_bindings"] = [route_binding("gate-validator")]

        self.assert_rejects(gate_marked_executable, "non-executable")

        def executable_without_route(corpus: dict) -> None:
            next(role for role in corpus["roles"] if role["role_id"] == "phase-executor")["route_bindings"] = []

        self.assert_rejects(executable_without_route, "admitted route")

    def test_fixture_bindings_require_source_fixture_oracle_and_review_digests(self) -> None:
        def corrupt_role(corpus: dict, role_id: str = "phase-executor") -> dict:
            return next(role for role in corpus["roles"] if role["role_id"] == role_id)

        self.assert_rejects(
            lambda corpus: corrupt_role(corpus)["source_binding"].update({"source_digest": "sha256:" + "0" * 64}),
            "source digest",
        )
        self.assert_rejects(
            lambda corpus: corrupt_role(corpus)["fixture_binding"].update({"fixture_digest": "not-a-digest"}),
            "fixture digest",
        )
        self.assert_rejects(
            lambda corpus: corrupt_role(corpus)["acceptance_oracle"].update({"oracle_digest": "not-a-digest"}),
            "oracle digest",
        )
        self.assert_rejects(
            lambda corpus: corrupt_role(corpus)["independent_review"].update({"review_digest": "not-a-digest"}),
            "review digest",
        )
        self.assert_rejects(
            lambda corpus: corrupt_role(corpus)["independent_review"].update({"reviewer_digest": "not-a-digest"}),
            "reviewer digest",
        )

    def test_partition_tools_sandbox_and_expected_artifacts_fail_closed(self) -> None:
        def corrupt_role(corpus: dict, role_id: str = "phase-executor") -> dict:
            return next(role for role in corpus["roles"] if role["role_id"] == role_id)

        self.assert_rejects(
            lambda corpus: corrupt_role(corpus)["partition_binding"].update({"partition_type": "selection"}),
            "calibration partition",
        )
        self.assert_rejects(
            lambda corpus: corrupt_role(corpus)["partition_binding"].update({"partition_id": "other-calibration"}),
            "partition",
        )
        self.assert_rejects(
            lambda corpus: corrupt_role(corpus).__setitem__("permitted_tools", []),
            "permitted tools",
        )
        self.assert_rejects(
            lambda corpus: corrupt_role(corpus).__setitem__("permitted_tools", ["filesystem.read", "filesystem.read"]),
            "permitted tools",
        )
        self.assert_rejects(
            lambda corpus: corrupt_role(corpus)["sandbox"].update({"mutation": "network_write"}),
            "sandbox",
        )
        self.assert_rejects(
            lambda corpus: corrupt_role(corpus).__setitem__("expected_artifacts", []),
            "expected artifacts",
        )
        self.assert_rejects(
            lambda corpus: corrupt_role(corpus)["expected_artifacts"][0].update({"artifact_digest": "not-a-digest"}),
            "artifact digest",
        )

    def test_stale_or_unreviewed_fixtures_fail_before_schedule(self) -> None:
        def role(corpus: dict) -> dict:
            return next(item for item in corpus["roles"] if item["role_id"] == "phase-executor")

        self.assert_rejects(
            lambda corpus: role(corpus)["fixture_binding"].update({"current": False}),
            "stale fixture",
        )
        self.assert_rejects(
            lambda corpus: role(corpus)["fixture_binding"].update(
                {"fixture_state": "invalid", "current": False, "invalidation_reason": "oracle_changed"}
            ),
            "stale fixture",
        )
        self.assert_rejects(
            lambda corpus: role(corpus)["independent_review"].update({"review_state": "pending"}),
            "independent review",
        )
        self.assert_rejects(
            lambda corpus: role(corpus)["independent_review"].pop("reviewed_at"),
            "independent review",
        )

        def reseal_objective(corpus: dict) -> None:
            objective = role(corpus)["objective_binding"]
            objective["objective_id"] = "g56r-003-objective-resealed"
            objective["objective_digest"] = digest(
                {"objective": "resealed", "partition": "calibration"}
            )

        self.assert_rejects(
            reseal_objective,
            "canonical fixture authority",
        )

    def test_scheduler_allows_only_executable_roles_with_admitted_routes(self) -> None:
        corpus = valid_corpus()
        validated = self.corpus.validate_role_corpus(corpus, repo_root=ROOT)
        schedule = self.corpus.schedule_admitted_roles(
            validated,
            admitted_route_ids=admitted_route_ids(corpus),
            active_route_bindings=active_route_bindings(validated),
            trusted_route_authority_binding=trusted_route_authority_binding(
                validated
            ),
        )

        self.assertEqual(
            [item["role_id"] for item in schedule["required_core"]],
            list(EXPECTED_EXECUTABLE_CORE),
        )
        self.assertEqual(
            [item["role_id"] for item in schedule["optional_helpers"]],
            ["autopilot-fast-helper"],
        )
        self.assertEqual(
            [item["role_id"] for item in schedule["unschedulable_governed"]],
            list(EXPECTED_NON_EXECUTABLE_CORE),
        )
        self.assertTrue(all(item["required_core"] for item in schedule["required_core"]))
        self.assertTrue(all(item["optional_helper"] for item in schedule["optional_helpers"]))
        self.assertFalse(any(item["executable"] for item in schedule["unschedulable_governed"]))

        admitted = admitted_route_ids(corpus)
        admitted.remove("g56r-003-route-phase-executor")
        with self.assertRaisesRegex(ValueError, "admitted route"):
            self.corpus.schedule_admitted_roles(
                validated,
                admitted_route_ids=admitted,
                active_route_bindings=active_route_bindings(validated),
                trusted_route_authority_binding=trusted_route_authority_binding(
                    validated
                ),
            )

        def route_not_admitted(corpus: dict) -> None:
            role = next(item for item in corpus["roles"] if item["role_id"] == "phase-executor")
            role["route_bindings"][0] = route_binding("phase-executor", admitted=False)

        self.assert_rejects(route_not_admitted, "admitted route")

    def test_scheduler_requires_exact_active_freeze_route_authority(self) -> None:
        corpus = valid_corpus()
        validated = self.corpus.validate_role_corpus(corpus, repo_root=ROOT)
        authority = [
            copy.deepcopy(route)
            for role in validated["roles"]
            for route in role["route_bindings"]
        ]
        phase_authority = next(
            item for item in authority
            if item["route_id"] == "g56r-003-route-phase-executor"
        )
        phase_authority["candidate_freeze_id"] = "sha256:" + "f" * 64
        phase_authority["route_digest"] = digest({
            key: phase_authority[key]
            for key in ("agent_contract_id", "candidate_freeze_id", "role_id", "route_id")
        })
        trusted_authority = trusted_route_authority_binding(validated)

        with self.assertRaisesRegex(ValueError, "active freeze"):
            self.corpus.schedule_admitted_roles(
                validated,
                admitted_route_ids=admitted_route_ids(corpus),
                active_route_bindings=authority,
                trusted_route_authority_binding=trusted_authority,
            )

    def test_closed_validation_rejects_unknown_fields(self) -> None:
        self.assert_rejects(
            lambda corpus: corpus.update({"notes": "free-form"}),
            "closed corpus",
        )
        self.assert_rejects(
            lambda corpus: next(role for role in corpus["roles"] if role["role_id"] == "phase-executor").update(
                {"free_form": "not allowed"}
            ),
            "closed role",
        )


if __name__ == "__main__":
    unittest.main()
