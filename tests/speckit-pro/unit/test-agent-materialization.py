#!/usr/bin/env python3
"""Focused deterministic tests for canonical Codex agent materialization."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import sys
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = ROOT / "speckit-pro"
LIB_DIR = ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

MODULE_PATH = PLUGIN_ROOT / "speckit_pro_runner/agent_materialization.py"
MODULE_IMPORT = "speckit_pro_runner.agent_materialization"
SOURCE_PATH = "speckit-pro/codex-agents/fixture-agent.toml"
MATERIALIZER_SOURCE_PATH = "speckit-pro/speckit_pro_runner/agent_materialization.py"
MATERIALIZER_PLUGIN_PATH = "speckit_pro_runner/agent_materialization.py"
RUNNER_MANIFEST_PATH = PLUGIN_ROOT / "speckit_pro_runner/speckit-pro-runner.manifest.json"
RUNNER_CHECKSUM_PATH = PLUGIN_ROOT / "speckit_pro_runner/speckit-pro-runner.sha256"

EXPECTED_DESTINATION_BYTES = (
    b'name = "fixture-agent"\n'
    b'description = "Fixture agent for byte materialization."\n'
    b'model = "gpt-5.5"\n'
    b'model_reasoning_effort = "xhigh"\n'
    b'sandbox_mode = "workspace-write"\n'
    b'developer_instructions = """\n'
    b'# Fixture Agent\n'
    b'\n'
    b'Return exact evidence.\n'
    b'"""\n'
)
PARSED_EQUIVALENT_BYTES = (
    b'name="fixture-agent"\n'
    b'description = "Fixture agent for byte materialization."\n'
    b'model = "gpt-5.5"\n'
    b'model_reasoning_effort = "xhigh"\n'
    b'sandbox_mode = "workspace-write"\n'
    b'developer_instructions = """\n'
    b'# Fixture Agent\n'
    b'\n'
    b'Return exact evidence.\n'
    b'"""\n'
)
EXPECTED_ROUTE = {
    "agent_name": "fixture-agent",
    "model": "gpt-5.5",
    "model_reasoning_effort": "xhigh",
}
EXPECTED_PARENT_CONTROLS = {"sandbox_mode": "workspace-write"}
ROUTE_SOURCE_BYTES = (
    b'name = "fixture-agent"\n'
    b'description = "Fixture agent for route materialization."\n'
    b'model = "gpt-5.5"\n'
    b'model_reasoning_effort = "xhigh"\n'
    b'sandbox_mode = "workspace-write"\n'
    b'tools = ["shell", "apply_patch"]\n'
    b'skills = ["speckit-autopilot"]\n'
    b'mcp_servers = ["context7"]\n'
    b'mutation_policy = "fake-home-only"\n'
    b'output_contract = "structured-json"\n'
    b'developer_instructions = """\n'
    b'# Fixture Agent\n'
    b'\n'
    b'Return exact evidence.\n'
    b'"""\n'
)
ROUTE_DESTINATION_BYTES = ROUTE_SOURCE_BYTES.replace(
    b'model = "gpt-5.5"\nmodel_reasoning_effort = "xhigh"\n',
    b'model = "gpt-5.4"\nmodel_reasoning_effort = "high"\n',
)
SELECTED_ROUTE = {
    "agent_name": "fixture-agent",
    "model": "gpt-5.4",
    "model_reasoning_effort": "high",
}
NON_ROUTE_FIELDS = {
    "name",
    "description",
    "sandbox_mode",
    "tools",
    "skills",
    "mcp_servers",
    "mutation_policy",
    "output_contract",
    "developer_instructions",
}


def sha256_digest(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def canonical_bytes(value) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def load_materialization_module():
    if str(PLUGIN_ROOT) not in sys.path:
        sys.path.insert(0, str(PLUGIN_ROOT))
    return importlib.import_module(MODULE_IMPORT)


class AgentMaterializationTests(unittest.TestCase):
    def materializer(self):
        self.assertTrue(
            MODULE_PATH.exists(),
            "canonical materializer module must be shipped from speckit-pro/speckit_pro_runner",
        )
        return load_materialization_module()

    def materialize(self, *, source_bytes: bytes = EXPECTED_DESTINATION_BYTES):
        module = self.materializer()
        return module.materialize_agent_policy(
            source_relative_path=SOURCE_PATH,
            source_bytes=source_bytes,
            candidate_route=copy.deepcopy(EXPECTED_ROUTE),
            parent_controls=copy.deepcopy(EXPECTED_PARENT_CONTROLS),
        )

    def materialize_selected_route(self):
        module = self.materializer()
        return module.materialize_agent_policy(
            source_relative_path=SOURCE_PATH,
            source_bytes=ROUTE_SOURCE_BYTES,
            candidate_route=copy.deepcopy(SELECTED_ROUTE),
            parent_controls=copy.deepcopy(EXPECTED_PARENT_CONTROLS),
        )

    def test_materializes_exact_destination_bytes_with_golden_digests(self) -> None:
        result = self.materialize()
        parsed = tomllib.loads(EXPECTED_DESTINATION_BYTES.decode("utf-8"))
        configuration = {
            key: parsed[key]
            for key in sorted(parsed)
            if key != "developer_instructions"
        }

        self.assertEqual(result.destination_bytes, EXPECTED_DESTINATION_BYTES)
        self.assertEqual(
            result.destination_bytes_digest,
            sha256_digest(EXPECTED_DESTINATION_BYTES),
        )
        self.assertEqual(
            result.instruction_digest,
            sha256_digest(parsed["developer_instructions"].encode("utf-8")),
        )
        self.assertEqual(
            result.configuration_digest,
            sha256_digest(canonical_bytes(configuration)),
        )
        self.assertEqual(result.byte_count, len(EXPECTED_DESTINATION_BYTES))

    def test_binds_agent_source_and_materializer_source(self) -> None:
        result = self.materialize()
        module = self.materializer()

        self.assertEqual(
            result.source_binding,
            {
                "path": SOURCE_PATH,
                "digest": sha256_digest(EXPECTED_DESTINATION_BYTES),
                "byte_count": len(EXPECTED_DESTINATION_BYTES),
            },
        )
        self.assertEqual(result.materializer_binding["path"], MATERIALIZER_SOURCE_PATH)
        self.assertEqual(
            result.materializer_binding["digest"],
            sha256_digest(MODULE_PATH.read_bytes()),
        )
        self.assertEqual(result.materializer_version, module.MATERIALIZER_VERSION)

    def test_renders_selected_explicit_route_from_original_source_bytes(self) -> None:
        result = self.materialize_selected_route()

        self.assertEqual(result.destination_bytes, ROUTE_DESTINATION_BYTES)
        self.assertEqual(
            result.destination_bytes_digest,
            sha256_digest(ROUTE_DESTINATION_BYTES),
        )
        self.assertEqual(
            result.source_binding,
            {
                "path": SOURCE_PATH,
                "digest": sha256_digest(ROUTE_SOURCE_BYTES),
                "byte_count": len(ROUTE_SOURCE_BYTES),
            },
        )
        self.assertNotEqual(result.source_binding["digest"], result.destination_bytes_digest)
        self.assertEqual(result.candidate_route, SELECTED_ROUTE)

    def test_inserts_explicit_route_when_source_inherits_both_route_fields(self) -> None:
        module = self.materializer()
        source_bytes = ROUTE_SOURCE_BYTES.replace(
            b'model = "gpt-5.5"\nmodel_reasoning_effort = "xhigh"\n',
            b'',
        )

        result = module.materialize_agent_policy(
            source_relative_path=SOURCE_PATH,
            source_bytes=source_bytes,
            candidate_route=copy.deepcopy(SELECTED_ROUTE),
            parent_controls=copy.deepcopy(EXPECTED_PARENT_CONTROLS),
        )

        self.assertIn(
            b'model = "gpt-5.4"\nmodel_reasoning_effort = "high"\n',
            result.destination_bytes,
        )
        source_policy = tomllib.loads(source_bytes.decode("utf-8"))
        destination_policy = tomllib.loads(result.destination_bytes.decode("utf-8"))
        self.assertEqual(destination_policy["model"], SELECTED_ROUTE["model"])
        self.assertEqual(
            destination_policy["model_reasoning_effort"],
            SELECTED_ROUTE["model_reasoning_effort"],
        )
        self.assertEqual(
            {field: destination_policy[field] for field in NON_ROUTE_FIELDS},
            {field: source_policy[field] for field in NON_ROUTE_FIELDS},
        )
        self.assertTrue(result.non_route_fields_unchanged)

    def test_default_route_preserves_source_that_inherits_both_route_fields(self) -> None:
        module = self.materializer()
        source_bytes = ROUTE_SOURCE_BYTES.replace(
            b'model = "gpt-5.5"\nmodel_reasoning_effort = "xhigh"\n',
            b'',
        )

        result = module.materialize_agent_policy(
            source_relative_path=SOURCE_PATH,
            source_bytes=source_bytes,
            candidate_route=None,
            parent_controls=copy.deepcopy(EXPECTED_PARENT_CONTROLS),
        )

        self.assertEqual(result.destination_bytes, source_bytes)
        self.assertTrue(module.verify_destination_bytes(result, source_bytes))
        self.assertEqual(
            result.candidate_route,
            {
                "agent_name": EXPECTED_ROUTE["agent_name"],
                "model": "",
                "model_reasoning_effort": "",
            },
        )
        self.assertEqual(result.selected_model, "")
        self.assertEqual(result.selected_model_reasoning_effort, "")

        for field in ("model", "model_reasoning_effort"):
            with self.subTest(field=field):
                incomplete_route = copy.deepcopy(SELECTED_ROUTE)
                incomplete_route[field] = ""
                with self.assertRaisesRegex(
                    ValueError,
                    rf"candidate route requires non-empty {field}",
                ):
                    module.materialize_agent_policy(
                        source_relative_path=SOURCE_PATH,
                        source_bytes=source_bytes,
                        candidate_route=incomplete_route,
                        parent_controls=copy.deepcopy(EXPECTED_PARENT_CONTROLS),
                    )

    def test_read_only_analyst_sources_materialize_their_live_route_settings(self) -> None:
        module = self.materializer()
        for agent_name in ("codebase-analyst", "spec-context-analyst"):
            with self.subTest(agent=agent_name):
                source_path = PLUGIN_ROOT / "codex-agents" / f"{agent_name}.toml"
                source_bytes = source_path.read_bytes()
                source_policy = tomllib.loads(source_bytes.decode("utf-8"))
                result = module.materialize_agent_policy(
                    source_relative_path=f"speckit-pro/codex-agents/{agent_name}.toml",
                    source_bytes=source_bytes,
                    candidate_route=None,
                    parent_controls={"sandbox_mode": "read-only"},
                )
                installed_policy = tomllib.loads(result.destination_bytes.decode("utf-8"))
                self.assertEqual(
                    (
                        source_policy.get("model"),
                        source_policy.get("model_reasoning_effort"),
                        installed_policy.get("model"),
                        installed_policy.get("model_reasoning_effort"),
                    ),
                    ("gpt-5.6-sol", "low", "gpt-5.6-sol", "low"),
                )
                self.assertEqual(result.destination_bytes, source_bytes)

    def test_legacy_default_route_preserves_original_model_formatting(self) -> None:
        module = self.materializer()
        source_bytes = ROUTE_SOURCE_BYTES.replace(
            b'model = "gpt-5.5"\nmodel_reasoning_effort = "xhigh"\n',
            b'model="gpt-5.5"\n',
        )

        result = module.materialize_agent_policy(
            source_relative_path=SOURCE_PATH,
            source_bytes=source_bytes,
            candidate_route=None,
            parent_controls=copy.deepcopy(EXPECTED_PARENT_CONTROLS),
        )

        self.assertEqual(result.destination_bytes, source_bytes)
        self.assertTrue(module.verify_destination_bytes(result, source_bytes))

    def test_route_materialization_preserves_non_route_fields(self) -> None:
        result = self.materialize_selected_route()
        source_policy = tomllib.loads(ROUTE_SOURCE_BYTES.decode("utf-8"))
        destination_policy = tomllib.loads(result.destination_bytes.decode("utf-8"))

        self.assertEqual(destination_policy["model"], SELECTED_ROUTE["model"])
        self.assertEqual(
            destination_policy["model_reasoning_effort"],
            SELECTED_ROUTE["model_reasoning_effort"],
        )
        self.assertEqual(
            {field: destination_policy[field] for field in NON_ROUTE_FIELDS},
            {field: source_policy[field] for field in NON_ROUTE_FIELDS},
        )
        self.assertIs(result.non_route_fields_unchanged, True)
        self.assertEqual(
            result.non_route_fields_digest,
            sha256_digest(
                canonical_bytes(
                    {field: source_policy[field] for field in sorted(NON_ROUTE_FIELDS)}
                )
            ),
        )

    def test_runner_trust_metadata_registers_materializer_source(self) -> None:
        expected_digest = hashlib.sha256(MODULE_PATH.read_bytes()).hexdigest()
        manifest = json.loads(RUNNER_MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest_records = {
            record["path"]["value"]: record["sha256"]
            for record in manifest["runner_files"]
        }
        checksum_records = {}
        for line in RUNNER_CHECKSUM_PATH.read_text(encoding="utf-8").splitlines():
            digest, rel_path = line.split(maxsplit=1)
            checksum_records[rel_path] = digest

        self.assertEqual(
            manifest_records.get(MATERIALIZER_PLUGIN_PATH),
            expected_digest,
        )
        self.assertEqual(
            manifest_records.get(MATERIALIZER_PLUGIN_PATH),
            checksum_records.get(MATERIALIZER_PLUGIN_PATH),
            expected_digest,
        )

    def test_idempotent_for_same_source_route_and_controls(self) -> None:
        first = self.materialize()
        second = self.materialize()

        self.assertEqual(first, second)
        self.assertEqual(first.materialization_id, second.materialization_id)

    def test_rejects_parsed_equivalent_toml_as_byte_proof(self) -> None:
        module = self.materializer()
        original = self.materialize()
        equivalent = self.materialize(source_bytes=PARSED_EQUIVALENT_BYTES)

        self.assertEqual(
            tomllib.loads(EXPECTED_DESTINATION_BYTES.decode("utf-8")),
            tomllib.loads(PARSED_EQUIVALENT_BYTES.decode("utf-8")),
        )
        self.assertEqual(original.instruction_digest, equivalent.instruction_digest)
        self.assertEqual(original.configuration_digest, equivalent.configuration_digest)
        self.assertNotEqual(
            original.destination_bytes_digest,
            equivalent.destination_bytes_digest,
        )
        self.assertTrue(module.verify_destination_bytes(original, EXPECTED_DESTINATION_BYTES))
        self.assertFalse(module.verify_destination_bytes(original, PARSED_EQUIVALENT_BYTES))

    def test_rejects_route_or_parent_control_mismatch(self) -> None:
        module = self.materializer()
        wrong_route = copy.deepcopy(EXPECTED_ROUTE)
        wrong_route["agent_name"] = "other-agent"
        with self.assertRaisesRegex(ValueError, "candidate route"):
            module.materialize_agent_policy(
                source_relative_path=SOURCE_PATH,
                source_bytes=EXPECTED_DESTINATION_BYTES,
                candidate_route=wrong_route,
                parent_controls=copy.deepcopy(EXPECTED_PARENT_CONTROLS),
            )

        wrong_controls = {"sandbox_mode": "read-only"}
        with self.assertRaisesRegex(ValueError, "parent controls"):
            module.materialize_agent_policy(
                source_relative_path=SOURCE_PATH,
                source_bytes=EXPECTED_DESTINATION_BYTES,
                candidate_route=copy.deepcopy(EXPECTED_ROUTE),
                parent_controls=wrong_controls,
            )

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AgentMaterializationTests)
    raise SystemExit(run_counted(suite, label="test-agent-materialization"))
