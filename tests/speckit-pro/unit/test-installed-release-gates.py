#!/usr/bin/env python3
"""Installed-release readiness and public result-schema gate tests.

These three tests build and check the installed-plugin release tree, which makes
them the slowest part of the runner gate suite. They live in their own Layer 4
script so the layer dispatcher can run them in parallel with the rest of
``test-speckit-pro-gates.py``. The request builders and assertion helpers stay
in that module and are borrowed here, not copied.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path
from types import ModuleType


def load_gate_tests() -> ModuleType:
    path = Path(__file__).resolve().parent / "test-speckit-pro-gates.py"
    spec = importlib.util.spec_from_file_location("speckit_pro_gate_tests", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATES = load_gate_tests()
REPO_ROOT = GATES.REPO_ROOT
INSTALLED_RELEASE_CONTRACT_DIR = GATES.INSTALLED_RELEASE_CONTRACT_DIR
PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR = GATES.PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR
REPOSITORY_BASH_CONFINEMENT_FIXTURE_DIR = GATES.REPOSITORY_BASH_CONFINEMENT_FIXTURE_DIR
gate_request = GATES.gate_request
installed_release_fixture_request = GATES.installed_release_fixture_request
run_runner = GATES.run_runner


class InstalledReleaseGateTests(unittest.TestCase):
    maxDiff = None

    assert_response = GATES.GateFoundationTests.assert_response
    schema_failures = GATES.GateFoundationTests.schema_failures
    assert_schema_instance = GATES.GateFoundationTests.assert_schema_instance
    assert_schema_rejected = GATES.GateFoundationTests.assert_schema_rejected
    assert_runner_ok = GATES.GateFoundationTests.assert_runner_ok
    assert_no_release_promotion_metadata = GATES.GateFoundationTests.assert_no_release_promotion_metadata
    assert_release_readiness_contract_subset = GATES.GateFoundationTests.assert_release_readiness_contract_subset
    assert_manifest_mutation_blocked = GATES.GateFoundationTests.assert_manifest_mutation_blocked

    def test_public_result_schema_validation_rejects_constraint_mutations(self) -> None:
        zero_completed, zero_response, _ = run_runner(
            gate_request("active-path-guard", "zero-bash-guard", inputs={"max_findings": 3})
        )
        self.assertEqual(zero_completed.returncode, 2)
        zero_schema = json.loads(
            (PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR / "zero-bash-guard-result.schema.json").read_text(encoding="utf-8")
        )
        negative_count = copy.deepcopy(zero_response)
        negative_count["data"]["blocking_count"] = -1
        self.assert_schema_rejected(negative_count, zero_schema, "minimum")
        empty_artifact = copy.deepcopy(zero_response)
        empty_artifact["data"]["artifacts"][0]["path"] = ""
        self.assert_schema_rejected(empty_artifact, zero_schema, "min_length")
        escaping_artifact = copy.deepcopy(zero_response)
        escaping_artifact["data"]["artifacts"][0]["path"] = "../artifact.json"
        self.assert_schema_rejected(escaping_artifact, zero_schema, "not")
        undeclared = copy.deepcopy(zero_response)
        undeclared["data"]["unpublished"] = True
        self.assert_schema_rejected(undeclared, zero_schema, "additional_properties")

        _, repo_response, _ = run_runner(
            gate_request("active-path-guard", "repo-bash-confinement", inputs={"unexpected": True})
        )
        repo_schema = json.loads(
            (REPOSITORY_BASH_CONFINEMENT_FIXTURE_DIR / "contracts/repo-bash-confinement-result.schema.json").read_text(encoding="utf-8")
        )
        excessive_allowlist = copy.deepcopy(repo_response["data"])
        excessive_allowlist["allowlist"]["entry_count"] = 12
        self.assert_schema_rejected(excessive_allowlist, repo_schema, "maximum")

        readiness_response = self.assert_runner_ok(installed_release_fixture_request("release-readiness"))
        readiness = readiness_response["data"]["release_readiness"]
        readiness_schema = json.loads(
            (INSTALLED_RELEASE_CONTRACT_DIR / "release-readiness.schema.json").read_text(encoding="utf-8")
        )
        self.assert_schema_instance(readiness, readiness_schema)
        inconsistent_status = copy.deepcopy(readiness)
        inconsistent_status["blocking_count"] = 1
        self.assert_schema_rejected(inconsistent_status, readiness_schema, "const")
        inconsistent_failure = copy.deepcopy(readiness)
        inconsistent_failure["status"] = "fail"
        self.assert_schema_rejected(inconsistent_failure, readiness_schema, "minimum")
        excessive_payloads = copy.deepcopy(readiness)
        excessive_payloads["payload_results"].append(copy.deepcopy(readiness["payload_results"][0]))
        self.assert_schema_rejected(excessive_payloads, readiness_schema, "max_items")
        invalid_argv = copy.deepcopy(readiness)
        invalid_argv["runner_invocations"][0]["invocation"]["argv"] = ["python3", "-m"]
        self.assert_schema_rejected(invalid_argv, readiness_schema, "one_of")

    def test_installed_release_readiness_default_request_passes(self) -> None:
        response = self.assert_runner_ok(installed_release_fixture_request("release-readiness"))
        self.assert_no_release_promotion_metadata(response)
        readiness = response["data"]["release_readiness"]
        self.assertEqual(
            set(readiness),
            {
                "schema_version",
                "contract_id",
                "status",
                "blocking_count",
                "checks",
                "payload_results",
                "runner_invocations",
            },
        )
        self.assertEqual(readiness["contract_id"], "installed-plugin-release")
        self.assertEqual(readiness["status"], "pass")
        self.assertEqual(readiness["blocking_count"], 0)
        self.assertFalse(any(check["blocking"] for check in readiness["checks"]))
        self.assertEqual(
            {check["check_id"] for check in readiness["checks"]},
            {
                "active-runtime-guard",
                "zero-bash-guard",
                "repo_bash_confinement",
                "payload-completeness",
                "runner-invocations",
                "version-sync",
            },
        )
        version_check = next(check for check in readiness["checks"] if check["check_id"] == "version-sync")
        expected_version = json.loads(
            (REPO_ROOT / "speckit-pro/.codex-plugin/plugin.json").read_text(encoding="utf-8")
        )["version"]
        versioned_sources = {
            "speckit-pro/.codex-plugin/plugin.json",
            ".agents/plugins/marketplace.json",
            ".release-please-manifest.json",
            "speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json",
        }
        unversioned_sources = {
            "speckit-pro/.claude-plugin/plugin.json",
            ".claude-plugin/marketplace.json",
        }
        self.assertEqual(
            set(version_check["evidence"]),
            {f"{path}={expected_version}" for path in versioned_sources}
            | {f"{path}=omitted" for path in unversioned_sources},
        )
        self.assertTrue(all("script_file_count" in item for item in readiness["payload_results"]))
        self.assert_release_readiness_contract_subset(readiness)

    def test_installed_release_readiness_reports_version_sync_failures_truthfully(self) -> None:
        cases = (
            (
                ".release-please-manifest.json",
                "speckit-pro",
                "9.9.9",
                ".release-please-manifest.json=9.9.9",
                None,
            ),
            (
                "speckit-pro/.claude-plugin/plugin.json",
                "version",
                "2.32.0",
                "speckit-pro/.claude-plugin/plugin.json=2.32.0",
                "speckit-pro/.claude-plugin/plugin.json=omitted",
            ),
            (
                "speckit-pro/.claude-plugin/plugin.json",
                "version",
                "",
                'speckit-pro/.claude-plugin/plugin.json=invalid:""',
                None,
            ),
        )
        for relative_path, key, value, expected, unexpected in cases:
            with self.subTest(relative_path=relative_path, value=value):
                readiness = self.assert_manifest_mutation_blocked(
                    relative_path,
                    key,
                    value,
                    "version-sync",
                )
                version_check = next(
                    check for check in readiness["checks"] if check["check_id"] == "version-sync"
                )
                self.assertIn(expected, version_check["evidence"])
                if unexpected is not None:
                    self.assertNotIn(unexpected, version_check["evidence"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(InstalledReleaseGateTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"test-installed-release-gates: {passed}/{total} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
