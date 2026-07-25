#!/usr/bin/env python3
"""Contract tests for the first Codex role-corpus fixture group."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tomllib
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/qualification_corpus.py"
FIXTURE_ROOT = ROOT / "tests/speckit-pro/layer6-efficiency/fixtures-codex"
CORPUS_MANIFEST_PATH = FIXTURE_ROOT / "corpus-manifest.json"

GROUP_ROLE_IDS = (
    "analyze-executor",
    "checklist-executor",
    "clarify-executor",
    "codebase-analyst",
)
CALIBRATION_TIME = "2026-07-24T00:00:00Z"

TOP_LEVEL_FIELDS = (
    "acceptance_oracle",
    "executable",
    "expected_artifacts",
    "fixture_binding",
    "independent_review",
    "objective_binding",
    "optional_helper",
    "partition_binding",
    "permitted_tools",
    "required_core",
    "role_id",
    "route_bindings",
    "sandbox",
    "source_binding",
)
ROUTE_FIELDS = (
    "admission_status",
    "agent_contract_id",
    "candidate_freeze_id",
    "role_id",
    "route_digest",
    "route_id",
)


def load_corpus_module():
    module_name = f"_g56r_003_fixture_group_a_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


CORPUS = load_corpus_module()
PARTITION_BINDING = {
    "partition_digest": CORPUS.digest({"partition_id": "g56r-003-calibration", "partition_type": "calibration"}),
    "partition_id": "g56r-003-calibration",
    "partition_type": "calibration",
    "qualification_eligible": False,
}
CANDIDATE_FREEZE_ID = CORPUS.digest(
    {"candidate": "g56r-003", "partition_id": "g56r-003-calibration", "version": "1.0.0"}
)
REVIEWER_DIGEST = CORPUS.digest(
    {"partition_id": "g56r-003-calibration", "reviewer": "independent-corpus-reviewer"}
)


def fixture_path(role_id: str) -> Path:
    return FIXTURE_ROOT / role_id / "fixture.json"


def read_fixture(role_id: str) -> dict:
    path = fixture_path(role_id)
    if not path.is_file():
        raise AssertionError(f"missing Codex corpus fixture: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def role_source_path(role_id: str) -> str:
    if role_id in CORPUS.NON_EXECUTABLE_CORE_ROLES:
        return f"speckit-pro/agents/{role_id}.md"
    return f"speckit-pro/codex-agents/{role_id}.toml"


def role_source_kind(role_id: str) -> str:
    if role_id in CORPUS.NON_EXECUTABLE_CORE_ROLES:
        return "governed_markdown_contract"
    return "codex_toml"


def role_sandbox_mode(role_id: str) -> str:
    if role_source_kind(role_id) != "codex_toml":
        return "read-only"
    source = tomllib.loads((ROOT / role_source_path(role_id)).read_text(encoding="utf-8"))
    return source["sandbox_mode"]


def permitted_tools(role_id: str) -> list[str]:
    if role_sandbox_mode(role_id) == "workspace-write":
        return ["filesystem.read", "filesystem.write", "shell.exec"]
    return ["filesystem.read"]


def route_binding(role_id: str) -> dict:
    payload = {
        "agent_contract_id": f"g56r-003-agent-contract-{role_id}",
        "candidate_freeze_id": CANDIDATE_FREEZE_ID,
        "role_id": role_id,
        "route_id": f"g56r-003-route-{role_id}",
    }
    return {
        "admission_status": "admitted",
        "agent_contract_id": payload["agent_contract_id"],
        "candidate_freeze_id": payload["candidate_freeze_id"],
        "role_id": payload["role_id"],
        "route_digest": CORPUS.digest(payload),
        "route_id": payload["route_id"],
    }


def expected_contract(role_id: str) -> dict:
    executable = role_id in CORPUS.EXECUTABLE_CORE_ROLES or role_id in CORPUS.OPTIONAL_HELPER_ROLES
    sandbox_mode = role_sandbox_mode(role_id)
    mutation = "workspace_write" if sandbox_mode == "workspace-write" else "read_only"
    source_path = role_source_path(role_id)
    fixture_id = f"g56r-003-fixture-{role_id}"
    fixture_version = "1.0.0"
    objective_id = f"g56r-003-objective-{role_id}"
    artifact_id = f"g56r-003-artifact-{role_id}-summary"
    oracle_id = f"g56r-003-oracle-{role_id}"
    review_id = f"g56r-003-review-{role_id}"
    return {
        "acceptance_oracle": {
            "oracle_digest": CORPUS.digest({"oracle_id": oracle_id, "role_id": role_id, "version": "1.0.0"}),
            "oracle_id": oracle_id,
            "oracle_version": "1.0.0",
        },
        "executable": executable,
        "expected_artifacts": [
            {
                "artifact_contract_id": artifact_id,
                "artifact_digest": CORPUS.digest(
                    {"artifact_contract_id": artifact_id, "artifact_type": "markdown_summary", "role_id": role_id}
                ),
                "artifact_type": "markdown_summary",
            }
        ],
        "fixture_binding": {
            "current": True,
            "fixture_digest": CORPUS.digest(
                {"fixture_id": fixture_id, "role_id": role_id, "version": fixture_version}
            ),
            "fixture_id": fixture_id,
            "fixture_state": "valid",
            "fixture_version": fixture_version,
            "invalidated_at": None,
            "invalidation_reason": None,
        },
        "independent_review": {
            "review_digest": CORPUS.digest(
                {
                    "review_id": review_id,
                    "review_state": "passed",
                    "reviewed_at": CALIBRATION_TIME,
                    "role_id": role_id,
                }
            ),
            "review_id": review_id,
            "review_state": "passed",
            "reviewed_at": CALIBRATION_TIME,
            "reviewer_digest": REVIEWER_DIGEST,
        },
        "objective_binding": {
            "objective_digest": CORPUS.digest(
                {"objective_id": objective_id, "partition_id": PARTITION_BINDING["partition_id"], "role_id": role_id}
            ),
            "objective_id": objective_id,
        },
        "optional_helper": role_id in CORPUS.OPTIONAL_HELPER_ROLES,
        "partition_binding": copy.deepcopy(PARTITION_BINDING),
        "permitted_tools": permitted_tools(role_id),
        "required_core": role_id in CORPUS.REQUIRED_CORE_ROLES,
        "role_id": role_id,
        "route_bindings": [route_binding(role_id)] if executable else [],
        "sandbox": {
            "mode": sandbox_mode,
            "mutation": mutation,
            "network": "restricted",
        },
        "source_binding": {
            "source_digest": CORPUS.digest((ROOT / source_path).read_bytes()),
            "source_kind": role_source_kind(role_id),
            "source_path": source_path,
        },
    }


def full_corpus_with_group_fixtures() -> dict:
    corpus = json.loads(CORPUS_MANIFEST_PATH.read_text(encoding="utf-8"))
    roles = corpus["roles"]
    by_role = {role["role_id"]: role for role in roles}
    for role_id in GROUP_ROLE_IDS:
        by_role[role_id] = read_fixture(role_id)
    corpus["roles"] = [
        by_role[role_id]
        for role_id in reversed(CORPUS.GOVERNED_ROLE_ORDER)
    ]
    return corpus


class CodexCorpusFixtureGroupATests(unittest.TestCase):
    def test_fixture_files_exist_and_use_deterministic_canonical_bytes(self) -> None:
        for role_id in GROUP_ROLE_IDS:
            with self.subTest(role_id=role_id):
                path = fixture_path(role_id)
                self.assertTrue(path.is_file(), f"missing fixture: {path.relative_to(ROOT)}")
                fixture = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(path.read_bytes(), CORPUS.canonical_bytes(fixture) + b"\n")

    def test_fixture_files_match_strict_per_role_contract(self) -> None:
        common_shape = None
        for role_id in GROUP_ROLE_IDS:
            with self.subTest(role_id=role_id):
                fixture = read_fixture(role_id)
                self.assertEqual(tuple(fixture), TOP_LEVEL_FIELDS)
                self.assertEqual(tuple(fixture["route_bindings"][0]), ROUTE_FIELDS)
                self.assertEqual(fixture, expected_contract(role_id))
                common_shape = common_shape or tuple(fixture)
                self.assertEqual(tuple(fixture), common_shape)

    def test_group_fixtures_validate_and_schedule_through_t007_contract(self) -> None:
        corpus = full_corpus_with_group_fixtures()
        validated = CORPUS.validate_role_corpus(corpus, repo_root=ROOT)
        admitted_route_ids = {
            binding["route_id"]
            for role in validated["roles"]
            for binding in role["route_bindings"]
            if binding["admission_status"] == "admitted"
        }
        active_route_bindings = [
            binding
            for role in validated["roles"]
            for binding in role["route_bindings"]
        ]
        schedule = CORPUS.schedule_admitted_roles(
            validated,
            admitted_route_ids=admitted_route_ids,
            active_route_bindings=active_route_bindings,
            trusted_route_authority_binding={
                "id": "g56r-003-active-route-authority",
                "digest": CORPUS.digest(
                    sorted(
                        active_route_bindings,
                        key=lambda item: (item["role_id"], item["route_id"]),
                    )
                ),
            },
        )
        scheduled_roles = {
            item["role_id"]
            for bucket in ("required_core", "optional_helpers")
            for item in schedule[bucket]
        }
        self.assertTrue(set(GROUP_ROLE_IDS) <= scheduled_roles)


if __name__ == "__main__":
    unittest.main()
