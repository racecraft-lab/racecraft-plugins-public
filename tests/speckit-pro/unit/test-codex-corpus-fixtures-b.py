#!/usr/bin/env python3
"""Group B fixture tests for the G56R-003 Codex role corpus."""

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
FIXTURES_ROOT = ROOT / "tests/speckit-pro/layer6-efficiency/fixtures-codex"

ROLE_ORDER = (
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
GROUP_B_ROLES = (
    "domain-researcher",
    "implement-executor",
    "phase-executor",
    "spec-context-analyst",
    "uat-runbook-author",
)
REQUIRED_CORE_ROLES = tuple(role for role in ROLE_ORDER if role != "autopilot-fast-helper")
OPTIONAL_HELPER_ROLES = ("autopilot-fast-helper",)
NON_EXECUTABLE_ROLES = ("consensus-synthesizer", "gate-validator")
READ_ONLY_ROLES = (
    "autopilot-fast-helper",
    "codebase-analyst",
    "consensus-synthesizer",
    "domain-researcher",
    "gate-validator",
    "spec-context-analyst",
)
PARTITION_DIGEST = "sha256:" + "1" * 64
FREEZE_ID = "sha256:" + "2" * 64
CALIBRATION_TIME = "2026-07-24T00:00:00Z"


def load_corpus_module():
    module_name = f"_g56r_003_fixture_b_corpus_{uuid4().hex}"
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
    payload = value if isinstance(value, bytes) else canonical_bytes(value)
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def source_path(role_id: str) -> str:
    if role_id in NON_EXECUTABLE_ROLES:
        return f"speckit-pro/agents/{role_id}.md"
    return f"speckit-pro/codex-agents/{role_id}.toml"


def source_kind(role_id: str) -> str:
    return "governed_markdown_contract" if role_id in NON_EXECUTABLE_ROLES else "codex_toml"


def file_digest(relative_path: str) -> str:
    return digest((ROOT / relative_path).read_bytes())


def partition_binding() -> dict:
    return {
        "partition_id": "g56r-003-calibration",
        "partition_type": "calibration",
        "partition_digest": PARTITION_DIGEST,
        "qualification_eligible": False,
    }


def route_binding(role_id: str) -> dict:
    route_payload = {
        "role_id": role_id,
        "route_id": f"g56r-003-route-{role_id}",
        "candidate_freeze_id": FREEZE_ID,
        "agent_contract_id": f"g56r-003-agent-contract-{role_id}",
    }
    return {
        **route_payload,
        "route_digest": digest(route_payload),
        "admission_status": "admitted",
    }


def role_boundary(role_id: str) -> dict:
    return {
        "read_only": role_id in READ_ONLY_ROLES,
        "executable": role_id not in NON_EXECUTABLE_ROLES,
    }


def common_binding_fields(role_id: str) -> dict:
    source = source_path(role_id)
    return {
        "source_binding": {
            "source_path": source,
            "source_kind": source_kind(role_id),
            "source_digest": file_digest(source),
        },
        "fixture_binding": {
            "fixture_id": f"g56r-003-fixture-{role_id}",
            "fixture_version": "1.0.0",
            "fixture_digest": digest({"fixture": role_id, "version": "1.0.0"}),
            "fixture_state": "valid",
            "current": True,
            "invalidated_at": None,
            "invalidation_reason": None,
        },
        "objective_binding": {
            "objective_id": f"g56r-003-objective-{role_id}",
            "objective_digest": digest({"objective": role_id, "partition": "calibration"}),
        },
        "partition_binding": partition_binding(),
        "expected_artifacts": [
            {
                "artifact_contract_id": f"g56r-003-artifact-{role_id}-summary",
                "artifact_type": "markdown_summary",
                "artifact_digest": digest({"artifact": role_id, "type": "markdown_summary"}),
            }
        ],
        "acceptance_oracle": {
            "oracle_id": f"g56r-003-oracle-{role_id}",
            "oracle_version": "1.0.0",
            "oracle_digest": digest({"oracle": role_id, "version": "1.0.0"}),
        },
        "independent_review": {
            "review_id": f"g56r-003-review-{role_id}",
            "reviewer_digest": digest({"reviewer": "independent-corpus-reviewer"}),
            "review_digest": digest({"review": role_id, "result": "passed"}),
            "review_state": "passed",
            "reviewed_at": CALIBRATION_TIME,
        },
    }


def role_contract(role_id: str) -> dict:
    boundary = role_boundary(role_id)
    read_only = boundary["read_only"]
    executable = boundary["executable"]
    return {
        "role_id": role_id,
        "required_core": role_id in REQUIRED_CORE_ROLES,
        "optional_helper": role_id in OPTIONAL_HELPER_ROLES,
        "executable": executable,
        **common_binding_fields(role_id),
        "permitted_tools": ["filesystem.read"] if read_only else ["filesystem.read", "shell.exec"],
        "sandbox": {
            "mode": "read-only" if read_only else "workspace-write",
            "network": "restricted",
            "mutation": "read_only" if read_only else "workspace_write",
        },
        "route_bindings": [route_binding(role_id)] if executable else [],
    }


def corpus_with_fixture(role_id: str, fixture: dict) -> dict:
    roles = [role_contract(item) for item in ROLE_ORDER]
    for index, role in enumerate(roles):
        if role["role_id"] == role_id:
            roles[index] = copy.deepcopy(fixture)
            break
    return {
        "schema_version": "role-corpus.v1",
        "corpus_id": "g56r-003-role-corpus-v1",
        "corpus_version": "1.0.0",
        "corpus_digest": digest({"corpus_id": "g56r-003-role-corpus-v1", "corpus_version": "1.0.0"}),
        "partition_binding": partition_binding(),
        "roles": roles,
    }


class CodexCorpusFixtureGroupBTests(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = load_corpus_module()

    def test_group_b_fixtures_match_role_corpus_contracts(self) -> None:
        for role_id in GROUP_B_ROLES:
            with self.subTest(role_id=role_id):
                fixture_path = FIXTURES_ROOT / role_id / "fixture.json"
                self.assertTrue(fixture_path.is_file(), f"missing fixture: {fixture_path}")

                raw = fixture_path.read_bytes()
                fixture = json.loads(raw.decode("utf-8"))
                expected = role_contract(role_id)

                self.assertEqual(fixture, expected)
                self.assertEqual(raw, canonical_bytes(expected) + b"\n")

                validated = self.corpus.validate_role_corpus(
                    corpus_with_fixture(role_id, fixture),
                    repo_root=ROOT,
                )
                validated_fixture = next(item for item in validated["roles"] if item["role_id"] == role_id)
                self.assertEqual(validated_fixture, expected)


if __name__ == "__main__":
    unittest.main()
