#!/usr/bin/env python3
"""Focused fixture checks for G56R-003 Codex corpus group C roles."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/qualification_corpus.py"
FIXTURE_ROOT = ROOT / "tests/speckit-pro/layer6-efficiency/fixtures-codex"
CORPUS_MANIFEST_PATH = FIXTURE_ROOT / "corpus-manifest.json"

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
GROUP_C_ROLE_IDS = ("autopilot-fast-helper", "consensus-synthesizer", "gate-validator")
REQUIRED_CORE = (
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
EXECUTABLE_CORE = (
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
NON_EXECUTABLE_CORE = ("consensus-synthesizer", "gate-validator")
OPTIONAL_HELPERS = ("autopilot-fast-helper",)
READ_ONLY_ROLES = frozenset(
    {
        "autopilot-fast-helper",
        "codebase-analyst",
        "consensus-synthesizer",
        "domain-researcher",
        "gate-validator",
        "spec-context-analyst",
    }
)
PARTITION_DIGEST = "sha256:" + "1" * 64
FREEZE_ID = "sha256:" + "2" * 64
CALIBRATION_TIME = "2026-07-24T00:00:00Z"


def load_corpus_module():
    module_name = f"_g56r_003_corpus_fixtures_c_{uuid4().hex}"
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


def file_digest(relative_path: str) -> str:
    return digest((ROOT / relative_path).read_bytes())


def source_path(role_id: str) -> str:
    if role_id in NON_EXECUTABLE_CORE:
        return f"speckit-pro/agents/{role_id}.md"
    return f"speckit-pro/codex-agents/{role_id}.toml"


def source_kind(role_id: str) -> str:
    if role_id in NON_EXECUTABLE_CORE:
        return "governed_markdown_contract"
    return "codex_toml"


def partition_binding() -> dict:
    return {
        "partition_id": "g56r-003-calibration",
        "partition_type": "calibration",
        "partition_digest": PARTITION_DIGEST,
        "qualification_eligible": False,
    }


def route_binding(role_id: str) -> dict:
    payload = {
        "agent_contract_id": f"g56r-003-agent-contract-{role_id}",
        "candidate_freeze_id": FREEZE_ID,
        "role_id": role_id,
        "route_id": f"g56r-003-route-{role_id}",
    }
    return {
        **payload,
        "route_digest": digest(payload),
        "admission_status": "admitted",
    }


def role_fixture(role_id: str) -> dict:
    required_core = role_id in REQUIRED_CORE
    optional_helper = role_id in OPTIONAL_HELPERS
    executable = role_id in EXECUTABLE_CORE or optional_helper
    mutation = "read_only" if role_id in READ_ONLY_ROLES else "workspace_write"
    permitted_tools = ["filesystem.read"] if mutation == "read_only" else ["filesystem.read", "shell.exec"]
    sandbox_mode = "read-only" if mutation == "read_only" else "workspace-write"
    return {
        "role_id": role_id,
        "required_core": required_core,
        "optional_helper": optional_helper,
        "executable": executable,
        "source_binding": {
            "source_path": source_path(role_id),
            "source_kind": source_kind(role_id),
            "source_digest": file_digest(source_path(role_id)),
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
        "permitted_tools": permitted_tools,
        "sandbox": {
            "mode": sandbox_mode,
            "network": "restricted",
            "mutation": mutation,
        },
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
        "route_bindings": [route_binding(role_id)] if executable else [],
    }


def role_corpus(roles: list[dict]) -> dict:
    return {
        "schema_version": "role-corpus.v1",
        "corpus_id": "g56r-003-role-corpus-v1",
        "corpus_version": "1.0.0",
        "corpus_digest": digest({"corpus_id": "g56r-003-role-corpus-v1", "corpus_version": "1.0.0"}),
        "partition_binding": partition_binding(),
        "roles": roles,
    }


class CodexCorpusFixturesCTests(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = load_corpus_module()

    def read_fixture(self, role_id: str) -> dict:
        fixture_path = FIXTURE_ROOT / role_id / "fixture.json"
        self.assertTrue(
            fixture_path.is_file(),
            f"missing fixture: {fixture_path.relative_to(ROOT)}",
        )
        raw = fixture_path.read_bytes()
        fixture = json.loads(raw.decode("utf-8"))
        self.assertEqual(raw, self.corpus.canonical_bytes(fixture) + b"\n")
        return fixture

    def test_group_c_fixtures_preserve_governed_helper_and_scheduler_separation(self) -> None:
        fixtures = {}
        for role_id in GROUP_C_ROLE_IDS:
            with self.subTest(role_id=role_id):
                fixture = self.read_fixture(role_id)
                self.assertEqual(fixture, role_fixture(role_id))
                fixtures[role_id] = fixture

        corpus = json.loads(CORPUS_MANIFEST_PATH.read_text(encoding="utf-8"))
        validated = self.corpus.validate_role_corpus(corpus, repo_root=ROOT)

        stats = self.corpus.corpus_statistics(validated)
        self.assertEqual(stats["required_core_roles"], 11)
        self.assertEqual(stats["optional_helper_roles"], 1)
        self.assertEqual(stats["non_executable_required_core_roles"], 2)
        self.assertEqual(stats["executable_optional_helper_roles"], 1)
        self.assertEqual(stats["optional_helper_role_ids"], ["autopilot-fast-helper"])
        self.assertNotIn("autopilot-fast-helper", stats["required_core_primary_role_ids"])

        admitted_route_ids = {
            route["route_id"]
            for role in validated["roles"]
            for route in role["route_bindings"]
        }
        active_route_bindings = [
            route
            for role in validated["roles"]
            for route in role["route_bindings"]
        ]
        schedule = self.corpus.schedule_admitted_roles(
            validated,
            admitted_route_ids=admitted_route_ids,
            active_route_bindings=active_route_bindings,
            trusted_route_authority_binding={
                "id": "g56r-003-active-route-authority",
                "digest": self.corpus.digest(
                    sorted(
                        active_route_bindings,
                        key=lambda item: (item["role_id"], item["route_id"]),
                    )
                ),
            },
        )
        self.assertEqual(
            [entry["role_id"] for entry in schedule["unschedulable_governed"]],
            ["consensus-synthesizer", "gate-validator"],
        )
        self.assertEqual(
            [entry["role_id"] for entry in schedule["optional_helpers"]],
            ["autopilot-fast-helper"],
        )
        self.assertFalse(any(entry["route_bindings"] for entry in schedule["unschedulable_governed"]))
        self.assertTrue(schedule["optional_helpers"][0]["route_bindings"])


if __name__ == "__main__":
    unittest.main()
