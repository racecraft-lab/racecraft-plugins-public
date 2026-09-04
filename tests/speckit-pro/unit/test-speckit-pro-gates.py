#!/usr/bin/env python3
"""Foundation tests for runner gate dispatch."""

from __future__ import annotations

import ast
import copy
from contextlib import ExitStack, contextmanager
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
TEST_LIB_ROOT = REPO_ROOT / "tests" / "speckit-pro" / "lib"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "runner-gates"
REQUESTS_DIR = FIXTURE_DIR / "requests"
INSTALLED_RELEASE_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "installed-plugin-release"
INSTALLED_RELEASE_CONTRACT_DIR = INSTALLED_RELEASE_FIXTURE_DIR / "contracts"
INSTALLED_RELEASE_REQUESTS_DIR = INSTALLED_RELEASE_FIXTURE_DIR / "requests"
PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "plugin-bash-confinement"
PLUGIN_BASH_CONFINEMENT_REQUESTS_DIR = PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "requests"
PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR = PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "contracts"
INSTALLED_CACHE_ORACLE_PATH = PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "installed-cache/oracle.json"
REPOSITORY_BASH_CONFINEMENT_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "repository-bash-confinement"

if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))
if str(TEST_LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_LIB_ROOT))

from structural_helpers import iter_subschemas  # noqa: E402


STATUS_EXIT_CODES = {
    "ok": 0,
    "expected_failure": 1,
    "input_error": 2,
    "missing_prerequisite": 3,
    "subprocess_failure": 4,
    "internal_failure": 5,
}


def runner_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(PLUGIN_ROOT) if not existing else f"{PLUGIN_ROOT}{os.pathsep}{existing}"
    return env


def gate_request(
    helper_id: str,
    operation: str,
    *,
    mode: str = "read_only",
    inputs: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "request_id": f"test-{operation}",
        "helper_id": helper_id,
        "operation": operation,
        "mode": mode,
        "inputs": inputs or {},
    }


def run_runner(
    request: object,
    *,
    extra_env: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any], list[dict[str, Any]]]:
    env = runner_env()
    if extra_env:
        env.update(extra_env)
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(request) if not isinstance(request, str) else request,
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        env=env,
        shell=False,
        check=False,
    )
    response = json.loads(completed.stdout) if completed.stdout.strip() else {}
    stderr_records = [json.loads(line) for line in completed.stderr.splitlines() if line.strip()]
    return completed, response, stderr_records


def fixture_request(name: str) -> dict[str, Any]:
    return json.loads((REQUESTS_DIR / f"{name}.json").read_text(encoding="utf-8"))


def fixture_cases(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / f"{name}-cases.json").read_text(encoding="utf-8"))


def installed_release_fixture_request(name: str) -> dict[str, Any]:
    return json.loads((INSTALLED_RELEASE_REQUESTS_DIR / f"{name}.json").read_text(encoding="utf-8"))


def installed_release_fixture_cases(name: str) -> dict[str, Any]:
    return json.loads((INSTALLED_RELEASE_FIXTURE_DIR / f"{name}-cases.json").read_text(encoding="utf-8"))


def plugin_bash_confinement_fixture_request(name: str) -> dict[str, Any]:
    return json.loads((PLUGIN_BASH_CONFINEMENT_REQUESTS_DIR / f"{name}.json").read_text(encoding="utf-8"))


def plugin_bash_confinement_fixture_cases(name: str) -> dict[str, Any]:
    return json.loads((PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / f"{name}-cases.json").read_text(encoding="utf-8"))


def installed_cache_oracle() -> dict[str, Any]:
    return json.loads(INSTALLED_CACHE_ORACLE_PATH.read_text(encoding="utf-8"))


@contextmanager
def materialized_installed_cache_oracle():
    oracle = installed_cache_oracle()
    with tempfile.TemporaryDirectory(
        prefix=".oracle-roots-",
        dir=INSTALLED_CACHE_ORACLE_PATH.parent,
    ) as temporary:
        temporary_root = Path(temporary)
        roots: dict[str, dict[str, str]] = {}
        for product, surface in oracle["surfaces"].items():
            source_root = temporary_root / "source" / product / "speckit-pro"
            installed_root = temporary_root / "installed" / product / "speckit-pro"
            for root in (source_root, installed_root):
                for record in surface["files"]:
                    path = root / record["path"]
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(record["content"], encoding="utf-8")
            roots[product] = {
                "source_root": source_root.relative_to(REPO_ROOT).as_posix(),
                "installed_root": installed_root.relative_to(REPO_ROOT).as_posix(),
            }
        yield oracle, roots


def installed_cache_oracle_proof(roots: dict[str, dict[str, str]]) -> dict[str, Any]:
    from speckit_pro_runner.gates import active_path_guard

    proofs = []
    for product in sorted(roots):
        root = roots[product]
        inventory = active_path_guard.payload_tree_inventory(
            REPO_ROOT,
            root["source_root"],
            {"product": product},
        )
        proofs.append(
            {
                "product": product,
                "surface": f"{product}_payload_fixture",
                "installed_root": root["installed_root"],
                "source_payload_root": root["source_root"],
                "source_payload_tree_hash": inventory["tree_hash"],
                "source_derived": True,
                "mutable_user_cache": False,
                "script_file_count": 0,
                "active_guidance_findings": [],
                "allowlist_release_readiness_excluded": True,
            }
        )
    return {
        "schema_version": "2.0",
        "contract_id": "plugin-bash-confinement",
        "proofs": proofs,
    }


@contextmanager
def installed_cache_oracle_root_policy(roots: dict[str, dict[str, str]]):
    from speckit_pro_runner.gates import active_path_guard

    source_products = {
        root["source_root"]: product for product, root in roots.items()
    }
    with (
        patch.object(
            active_path_guard,
            "canonical_installed_cache_root",
            side_effect=lambda root, product: root == roots.get(product, {}).get("installed_root"),
        ),
        patch.object(
            active_path_guard,
            "canonical_payload_root",
            side_effect=lambda root, product: root == roots.get(product, {}).get("source_root"),
        ),
        patch.object(
            active_path_guard,
            "payload_surface_from_root",
            side_effect=lambda root, _repo_root=None: source_products.get(root),
        ),
    ):
        yield


def run_installed_release_readiness(
    *,
    repo_root: Path = REPO_ROOT,
    live_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from speckit_pro_runner.gates import registry, release as release_gate

    entry = next(
        operation
        for operation in registry.all_gate_operations()
        if operation.operation == "installed-release-readiness"
    )
    request = SimpleNamespace(
        request_id="test-installed-release-readiness",
        operation="installed-release-readiness",
        inputs={},
    )
    if live_evidence is None:
        return release_gate.installed_release_readiness(entry, request, repo_root)
    with patch.object(release_gate, "live_installed_release_gate_evidence", return_value=live_evidence):
        return release_gate.installed_release_readiness(entry, request, repo_root)


def copy_installed_release_tree(destination: Path) -> None:
    for relative in (
        ".agents/plugins",
        ".claude-plugin",
        "dist",
        "speckit-pro",
        "tests/speckit-pro/unit/fixtures",
    ):
        shutil.copytree(REPO_ROOT / relative, destination / relative)
    shutil.copy2(REPO_ROOT / ".release-please-manifest.json", destination)


def run_plugin_bash_confinement_case(
    case_id: str,
    *,
    skip_source_scan: bool = False,
    skip_repo_source_scan: bool = False,
) -> dict[str, Any]:
    from speckit_pro_runner.gates import active_path_guard, registry

    entry = next(
        operation
        for operation in registry.all_gate_operations()
        if operation.operation == "zero-bash-guard"
    )
    inputs: dict[str, Any] = {
        "case_file": "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/zero-bash-guard-cases.json",
        "case_id": case_id,
    }
    request = SimpleNamespace(
        request_id=f"test-zero-bash-guard-{case_id}",
        operation="zero-bash-guard",
        inputs=inputs,
    )
    if not skip_source_scan and not skip_repo_source_scan:
        return active_path_guard.run_zero_bash_guard(entry, request, REPO_ROOT)
    with ExitStack() as stack:
        if skip_source_scan:
            stack.enter_context(patch.object(active_path_guard, "source_files", return_value=[]))
        if skip_repo_source_scan:
            stack.enter_context(patch.object(active_path_guard, "scan_repo_sources", return_value=[]))
        return active_path_guard.run_zero_bash_guard(entry, request, REPO_ROOT)


def python_argv(source: str) -> list[str]:
    return [sys.executable, "-c", source]


def load_layer_script_dispatcher() -> Any:
    dispatcher_path = REPO_ROOT / "tests" / "speckit-pro" / "run-layer-scripts.py"
    spec = importlib.util.spec_from_file_location("run_layer_scripts", dispatcher_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def successful_command(label: str) -> dict[str, Any]:
    return {
        "argv": python_argv(f"import sys; print('{label} stdout'); print('{label} stderr', file=sys.stderr)"),
        "timeout_seconds": 5,
    }


def failing_command(label: str, exit_code: int = 1) -> dict[str, Any]:
    return {
        "argv": python_argv(
            f"import sys; print('{label} stdout'); print('{label} stderr', file=sys.stderr); raise SystemExit({exit_code})"
        ),
        "timeout_seconds": 5,
    }


class GateFoundationTests(unittest.TestCase):
    maxDiff = None

    def assert_stdout_json(self, completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, completed.stdout)
        parsed = json.loads(lines[0])
        self.assertIsInstance(parsed, dict)
        return parsed

    def assert_response(self, response: dict[str, Any], status: str) -> None:
        self.assertEqual(response["schema_version"], "1.0")
        self.assertEqual(response["status"], status)
        self.assertEqual(response["exit_code"], STATUS_EXIT_CODES[status])
        self.assertIsNone(response["legacy_exit_code"])
        self.assertIsInstance(response["diagnostics"], list)
        self.assertIsInstance(response["data"], dict)

    def schema_failures(self, value: object, schema: dict) -> list[dict[str, Any]]:
        from speckit_pro_runner.helpers import read_only

        return read_only.json_schema_failures(value, schema, schema, "$")

    def assert_schema_instance(self, value: object, schema: dict) -> None:
        self.assertEqual(self.schema_failures(value, schema), [])

    def assert_schema_rejected(self, value: object, schema: dict, rule: str) -> None:
        self.assertTrue(
            any(failure["rule"].endswith(rule) for failure in self.schema_failures(value, schema)),
            self.schema_failures(value, schema),
        )

    def assert_runner_ok(
        self,
        request: object,
        *,
        extra_env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        completed, response, stderr_records = run_runner(request, extra_env=extra_env)
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        return response

    def assert_status_exit_mapping(self, completed: subprocess.CompletedProcess[str], response: dict[str, Any]) -> None:
        self.assertEqual(completed.returncode, response["exit_code"])
        self.assertEqual(completed.returncode, STATUS_EXIT_CODES[response["status"]])

    def assert_stderr_diagnostics(self, response: dict[str, Any], stderr_records: list[dict[str, Any]]) -> None:
        self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])
        for diag in response["diagnostics"]:
            for field in ("severity", "source", "code", "message", "remediation"):
                self.assertIn(field, diag)
            self.assertEqual(diag["source"], "runner")
            self.assertIsInstance(diag["remediation"], dict)
            self.assertTrue(diag["remediation"]["summary"])
            self.assertTrue(diag["remediation"]["actions"])

    def assert_artifact_paths(self, response: dict[str, Any]) -> None:
        artifacts = response["data"].get("artifacts", [])
        self.assertIsInstance(artifacts, list)
        for artifact in artifacts:
            self.assertIsInstance(artifact, dict)
            path = Path(artifact["path"])
            self.assertFalse(path.is_absolute(), artifact["path"])
            self.assertNotIn("..", path.parts)

    def assert_no_release_promotion_metadata(
        self,
        response: dict[str, Any],
        case_file: str | None = None,
    ) -> None:
        self.assertNotIn("promotion_record", response["data"]["gate"])
        artifacts = response["data"].get("artifacts", [])
        self.assertFalse(any(artifact.get("kind") == "promotion_record" for artifact in artifacts))
        if case_file is not None:
            self.assertIn({"path": case_file, "kind": "fixture"}, artifacts)
        self.assertEqual(len({artifact["path"] for artifact in artifacts}), len(artifacts))

    def assert_no_shell_argv(self, argv: list[str]) -> None:
        joined = " ".join(argv).lower()
        self.assertNotIn("bash", joined)
        self.assertNotIn("jq", joined)
        self.assertNotIn("powershell", joined)
        self.assertNotIn("pwsh", joined)
        self.assertFalse(any(arg.lower().endswith(".sh") for arg in argv))

    def assert_payload_completeness_contract_subset(self, results: list[dict[str, Any]]) -> None:
        schema = json.loads((INSTALLED_RELEASE_CONTRACT_DIR / "payload-completeness.schema.json").read_text(encoding="utf-8"))
        required = set(schema["required"])
        allowed = set(schema["properties"])
        file_required = set(schema["$defs"]["payload_file"]["required"])
        file_allowed = set(schema["$defs"]["payload_file"]["properties"])
        for result in results:
            self.assertLessEqual(required, set(result), result.get("payload_surface"))
            self.assertFalse(set(result) - allowed, result.get("payload_surface"))
            for files_key in ("expected_files", "actual_files"):
                for file_record in result[files_key]:
                    with self.subTest(surface=result["payload_surface"], path=file_record["path"]):
                        self.assertLessEqual(file_required, set(file_record), file_record)
                        self.assertFalse(set(file_record) - file_allowed, file_record)
                        path = file_record["path"]
                        self.assertFalse(path.startswith("/") or ".." in path.split("/") or ":" in path.split("/")[0], path)

    def assert_release_readiness_contract_subset(self, readiness: dict[str, Any]) -> None:
        schema = json.loads((INSTALLED_RELEASE_CONTRACT_DIR / "release-readiness.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(self.schema_failures(readiness, schema), [])

    def repo_rel(self, path: Path) -> str:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve(strict=False)).as_posix()

    def assert_input_error_code(self, request: dict[str, object], expected_code: str) -> dict[str, Any]:
        completed, response, stderr_records = run_runner(request)
        self.assert_stdout_json(completed)
        self.assert_response(response, "input_error")
        self.assert_status_exit_mapping(completed, response)
        self.assert_stderr_diagnostics(response, stderr_records)
        self.assert_artifact_paths(response)
        self.assertEqual([diag["code"] for diag in response["diagnostics"]], [expected_code])
        return response

    def test_zero_bash_unknown_input_matches_the_public_result_schema(self) -> None:
        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "zero-bash-guard",
                inputs={"max_findings": 3},
            )
        )
        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error")
        self.assertEqual([item["code"] for item in stderr_records], ["unsupported_gate_inputs"])
        self.assertEqual(response["diagnostics"][0]["details"], {"fields": ["max_findings"]})
        self.assertEqual(response["data"]["status"], "fail")
        self.assertEqual(response["data"]["blocking_count"], 1)
        self.assertEqual(response["data"]["classified_counts"], {})
        self.assertEqual(response["data"]["findings"], [])
        schema = json.loads(
            (PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR / "zero-bash-guard-result.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(response["data"]), set(schema["properties"]["data"]["properties"]))
        self.assertEqual(set(response["data"]["gate"]), set(schema["properties"]["data"]["properties"]["gate"]["properties"]))
        self.assert_schema_instance(response, schema)

    def test_repo_bash_unknown_input_matches_the_public_result_schema(self) -> None:
        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "repo-bash-confinement",
                inputs={"unexpected": True},
            )
        )
        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error")
        self.assertEqual([item["code"] for item in stderr_records], ["unsupported_gate_inputs"])
        self.assertEqual(response["diagnostics"][0]["details"], {"fields": ["unexpected"]})
        self.assertEqual(response["data"]["status"], "fail")
        self.assertEqual(response["data"]["blocking_count"], 1)
        self.assertEqual(response["data"]["classified_counts"], {})
        self.assertEqual(response["data"]["findings"], [])
        schema = json.loads(
            (REPOSITORY_BASH_CONFINEMENT_FIXTURE_DIR / "contracts/repo-bash-confinement-result.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(response["data"]), set(schema["properties"]))
        self.assertEqual(set(response["data"]["gate"]), set(schema["properties"]["gate"]["properties"]))
        self.assert_schema_instance(response["data"], schema)

    def test_public_result_schema_validation_enforces_owned_assertion_keywords(self) -> None:
        schema_paths = (
            PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR / "zero-bash-guard-result.schema.json",
            REPOSITORY_BASH_CONFINEMENT_FIXTURE_DIR / "contracts/repo-bash-confinement-result.schema.json",
            INSTALLED_RELEASE_CONTRACT_DIR / "release-readiness.schema.json",
        )
        annotations = {"$schema", "$id", "$defs", "title", "description", "default"}
        supported = {
            "$ref",
            "type",
            "const",
            "enum",
            "properties",
            "required",
            "additionalProperties",
            "items",
            "prefixItems",
            "oneOf",
            "allOf",
            "if",
            "then",
            "else",
            "not",
            "minItems",
            "maxItems",
            "minLength",
            "pattern",
            "minimum",
            "maximum",
        }

        for path in schema_paths:
            schema = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(schema=path.name):
                assertion_keywords = {
                    keyword
                    for node in iter_subschemas(schema)
                    for keyword in node
                    if keyword not in annotations
                }
                self.assertEqual(assertion_keywords - supported, set())

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

    def test_request_fixtures_cover_registered_suite_operations(self) -> None:
        expected = {
            "run-default-suite.json",
            "run-layer.json",
            "run-toolchain-preflight.json",
            "run-toolchain-preflight-docs.json",
            "run-integration-suite.json",
            "run-parity-suite.json",
            "test-payload-evidence.json",
            "install-verification.json",
            "validate-pr-title-live.json",
            "active-path-guard.json",
            "classify-shell-finding.json",
        }
        self.assertEqual({path.name for path in REQUESTS_DIR.iterdir()}, expected)

        default_request = fixture_request("run-default-suite")
        self.assertEqual(default_request["helper_id"], "suite-gate")
        self.assertEqual(default_request["operation"], "run-default-suite")
        self.assertEqual(default_request["mode"], "read_only")
        self.assertEqual(default_request["inputs"]["suite"], ["toolchain", "1", "4", "5", "7", "8"])

        for name in [
            "run-default-suite",
            "run-layer",
            "run-toolchain-preflight",
            "run-integration-suite",
            "run-parity-suite",
        ]:
            with self.subTest(fixture=name):
                request = fixture_request(name)
                self.assertEqual(request["schema_version"], "1.0")
                self.assertEqual(request["helper_id"], "suite-gate")
                self.assertEqual(request["mode"], "read_only")
                self.assertIn(request["operation"], {
                    "run-default-suite",
                    "run-layer",
                    "run-toolchain-preflight",
                    "run-integration-suite",
                    "run-parity-suite",
                })

        payload_request = fixture_request("test-payload-evidence")
        self.assertEqual(payload_request["helper_id"], "payload-gate")
        self.assertEqual(payload_request["operation"], "build-test-payload-evidence")
        self.assertEqual(payload_request["mode"], "read_only")

        install_request = fixture_request("install-verification")
        self.assertEqual(install_request["helper_id"], "install-verification")
        self.assertEqual(install_request["operation"], "verify-install")
        self.assertTrue(install_request["inputs"]["fake_home"])

        title_request = fixture_request("validate-pr-title-live")
        self.assertEqual(title_request["helper_id"], "release-readiness")
        self.assertEqual(title_request["operation"], "validate-pr-title")
        self.assertEqual(title_request["inputs"], {"title_env": "TITLE"})

        active_guard_request = fixture_request("active-path-guard")
        self.assertEqual(active_guard_request["helper_id"], "active-path-guard")
        self.assertEqual(active_guard_request["operation"], "active-path-guard")
        self.assertEqual(active_guard_request["mode"], "read_only")
        self.assertEqual(active_guard_request["inputs"]["case_id"], "final-current-implementation")

        classify_request = fixture_request("classify-shell-finding")
        self.assertEqual(classify_request["helper_id"], "active-path-guard")
        self.assertEqual(classify_request["operation"], "classify-shell-finding")
        self.assertEqual(classify_request["mode"], "read_only")
        self.assertIn("text", classify_request["inputs"])

    def test_case_fixtures_cover_payload_install_and_guard_failures(self) -> None:
        payload_cases = fixture_cases("payload-evidence")
        self.assertEqual(payload_cases["schema_version"], "2.0")
        self.assertEqual(payload_cases["contract_id"], "runner-gates")
        self.assertIn("fixture-or-temp-output-roots", payload_cases["coverage"])
        self.assertEqual({case["case_id"] for case in payload_cases["cases"]}, {"claude-codex-test-payloads", "stale-generated-files"})

        install_cases = fixture_cases("install-verification")
        self.assertEqual(install_cases["schema_version"], "2.0")
        self.assertEqual(install_cases["contract_id"], "runner-gates")
        self.assertEqual(
            {case["case_id"] for case in install_cases["cases"]},
            {
                "complete-fake-home",
                "safe-repair-plan",
                "windows-style-paths",
                "traversal-rejection",
                "line-ending-normalization",
            },
        )

        active_cases = fixture_cases("active-path-guard")
        self.assertEqual(active_cases["schema_version"], "2.0")
        self.assertEqual(active_cases["contract_id"], "runner-gates")
        self.assertEqual(
            {case["case_id"] for case in active_cases["cases"]},
            {
                "blocking-active-patterns",
                "nonblocking-classifications",
                "workflow-dispatch-good",
                "workflow-dispatch-with-plugin-logic",
                "final-current-implementation",
            },
        )
        for label in [
            "active Bash",
            ".sh",
            "jq",
            "Git Bash",
            "WSL",
            "PowerShell helper",
            "shell parsing",
            "shell interpolation",
            "shell=True",
            "os.system",
            "command-string subprocess",
            "CI dispatch glue",
            "installed-plugin cutover surface",
        ]:
            self.assertIn(label, active_cases["coverage"])

    def test_installed_release_runner_invocation_fixtures_cover_interpreter_resolution(self) -> None:
        cases = installed_release_fixture_cases("runner-invocation")
        self.assertEqual(cases["schema_version"], "2.0")
        self.assertEqual(cases["contract_id"], "installed-plugin-release")
        self.assertEqual(
            {case["case_id"] for case in cases["cases"]},
            {
                "windows-py-v3",
                "windows-py-3-fallback",
                "macos-python3",
                "linux-python-fallback",
                "live-host-runtime-info",
                "too-old-or-missing",
            },
        )
        expected_candidates = {
            "windows": ["py -V:3", "py -3", "python", "python3"],
            "macos": ["python3", "python"],
            "linux": ["python3", "python"],
        }
        for case in cases["cases"]:
            with self.subTest(case_id=case["case_id"]):
                self.assertIn(case["product"], {"claude", "codex"})
                self.assertIn(case["operation"], {"preflight", "scaffold", "status", "autopilot-dry-run"})
                self.assertTrue(case["cache_root"])
                if "candidate_results" not in case:
                    continue
                platform = case["platform"]
                attempted = [item["candidate"] for item in case["candidate_results"]]
                self.assertEqual(attempted, expected_candidates[platform][: len(attempted)])

        request = installed_release_fixture_request("runner-invocation")
        self.assertEqual(request["helper_id"], "runner-invocation")
        self.assertEqual(request["operation"], "runner-invocation")
        self.assertEqual(request["mode"], "read_only")
        self.assertEqual(request["inputs"]["case_id"], "live-host-runtime-info")

    def test_installed_release_runner_invocation_records_have_no_shell_fallback(self) -> None:
        contract = json.loads((INSTALLED_RELEASE_CONTRACT_DIR / "runner-invocation.schema.json").read_text(encoding="utf-8"))
        release_contract = json.loads((INSTALLED_RELEASE_CONTRACT_DIR / "release-readiness.schema.json").read_text(encoding="utf-8"))
        argv_contract = contract["properties"]["invocation"]["properties"]["argv"]
        self.assertEqual(len(argv_contract["oneOf"]), 3)
        self.assertEqual(contract["$defs"]["diagnostic"]["properties"]["remediation"]["type"], "object")
        release_runner = release_contract["$defs"]["runner_invocation"]
        self.assertEqual(release_runner["properties"]["invocation"]["properties"]["argv"], argv_contract)
        self.assertIn(
            "runner-invocations",
            release_contract["$defs"]["check"]["properties"]["check_id"]["enum"],
        )
        self.assertIn(
            "missing_runner_invocation",
            release_contract["$defs"]["check"]["properties"]["blocker_class"]["enum"],
        )
        self.assertEqual(release_contract["properties"]["runner_invocations"]["minItems"], 1)
        self.assertEqual(
            release_contract["$defs"]["interpreter_resolution"],
            contract["$defs"]["interpreter_resolution"],
        )
        self.assertEqual(
            release_contract["$defs"]["diagnostic"]["properties"]["remediation"]["type"],
            "object",
        )

        from speckit_pro_runner.helpers import install as install_helper

        self.assertEqual(
            install_helper.invocation_prefix_for_candidate("windows", "py -V:3", "C:/Python312/python.exe"),
            ["C:/Python312/python.exe"],
        )
        self.assertEqual(
            install_helper.invocation_prefix_for_candidate("windows", "py -V:3", "C:/Windows/py.exe"),
            ["C:/Windows/py.exe", "-3"],
        )
        self.assertEqual(
            install_helper.invocation_prefix_for_live_probe("py -V:3", "C:/Python312/python.exe"),
            ["py", "-3"],
        )
        self.assertTrue(install_helper.allowed_python_executable("linux", "/usr/bin/python3.11"))
        resolution, diagnostics = install_helper.resolve_python_interpreter(
            "linux",
            {"candidate_results": [{"candidate": "bash", "returncode": 0, "version": "3.11.8", "resolved_executable": "bash"}]},
            "dist/codex/speckit-pro",
        )
        self.assertFalse(resolution["accepted"])
        self.assertEqual(resolution["failure_code"], "python_runtime_unavailable")
        self.assertEqual([diag["code"] for diag in diagnostics], ["python_runtime_unavailable"])
        self.assertIn("unsupported Python candidate", resolution["diagnostic"])
        resolution, diagnostics = install_helper.resolve_python_interpreter(
            "linux",
            {
                "candidate_results": [
                    {
                        "candidate": "python3",
                        "returncode": 0,
                        "version": "3.11.8",
                        "resolved_executable": "bash",
                    }
                ]
            },
            "dist/codex/speckit-pro",
        )
        self.assertFalse(resolution["accepted"])
        self.assertEqual(resolution["failure_code"], "python_runtime_unavailable")
        self.assertEqual([diag["code"] for diag in diagnostics], ["python_runtime_unavailable"])
        self.assertIn("unsupported resolved executable", resolution["diagnostic"])
        resolution, diagnostics = install_helper.resolve_python_interpreter(
            "linux",
            {
                "candidate_results": [
                    {
                        "candidate": "python3",
                        "returncode": 0,
                        "version": "3.11.8",
                        "resolved_executable": "python3",
                        "invocation_argv_prefix": ["bash"],
                    }
                ]
            },
            "dist/codex/speckit-pro",
        )
        self.assertFalse(resolution["accepted"])
        self.assertEqual(resolution["failure_code"], "python_runtime_unavailable")
        self.assertEqual([diag["code"] for diag in diagnostics], ["python_runtime_unavailable"])
        self.assertIn("unsupported invocation prefix", resolution["diagnostic"])
        for prefix in [["python3", "-c"], ["python3", "bash"], ["python3", "-m"], ["py"], ["py", "-c"]]:
            with self.subTest(prefix=prefix):
                self.assertFalse(install_helper.allowed_python_invocation_prefix("linux", prefix))
        self.assertFalse(install_helper.allowed_python_invocation_prefix("windows", ["py", "-c"]))
        self.assertTrue(install_helper.allowed_python_invocation_prefix("windows", ["py", "-3"]))
        self.assertTrue(install_helper.allowed_python_invocation_prefix("linux", ["python3"]))
        for payload_root in [
            REPO_ROOT / "dist" / "claude" / "speckit-pro",
            REPO_ROOT / "dist" / "codex" / "speckit-pro",
        ]:
            self.assertTrue((payload_root / "speckit_pro_runner" / "__main__.py").is_file())
            self.assertTrue((payload_root / "speckit_pro_runner" / "speckit-pro-runner.manifest.json").is_file())

        pass_cases = [
            "windows-py-v3",
            "windows-py-3-fallback",
            "macos-python3",
            "linux-python-fallback",
        ]
        for case_id in pass_cases:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "runner-invocation",
                        "runner-invocation",
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/runner-invocation-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 0)
                self.assert_stdout_json(completed)
                self.assert_response(response, "ok")
                self.assert_status_exit_mapping(completed, response)
                self.assertEqual(stderr_records, [])
                self.assert_no_release_promotion_metadata(
                    response,
                    "tests/speckit-pro/unit/fixtures/installed-plugin-release/runner-invocation-cases.json",
                )
                record = response["data"]["runner_invocation"]
                self.assertEqual(record["schema_version"], "2.0")
                self.assertEqual(record["request_id"], response["request_id"])
                self.assertTrue(record["interpreter_resolution"]["accepted"])
                self.assertEqual(record["interpreter_resolution"]["minimum_version"], "3.11")
                self.assertIsNone(record["interpreter_resolution"]["failure_code"])
                self.assertTrue(record["interpreter_resolution"]["attempted_candidates"])
                self.assertTrue(record["interpreter_resolution"]["resolved_executable"])
                self.assertTrue(record["interpreter_resolution"]["invocation_argv_prefix"])
                self.assertRegex(record["interpreter_resolution"]["version"], r"^3\.(1[1-9]|[2-9][0-9])\.")
                expected_argv = [
                    *record["interpreter_resolution"]["invocation_argv_prefix"],
                    "-m",
                    "speckit_pro_runner",
                ]
                self.assertEqual(
                    record["invocation"],
                    {
                        "argv": expected_argv,
                        "stdin_mode": "single_json_request",
                        "stdout_mode": "single_json_response",
                        "stderr_mode": "diagnostics_only",
                        "shell_used": False,
                    },
                )
                self.assertEqual(record["runner_request"]["helper_id"], "runner")
                self.assertEqual(record["runner_response"]["schema_version"], "1.0")
                self.assertEqual(record["runner_response"]["evidence_source"], "fixture")
                self.assertEqual(record["status"], "pass")
                self.assertEqual(record["diagnostics"], [])
                self.assert_no_shell_argv(record["invocation"]["argv"])
                if record["platform"] == "windows":
                    self.assertEqual(record["invocation"]["argv"][-3:], ["-3", "-m", "speckit_pro_runner"])

        completed, response, stderr_records = run_runner(
            gate_request(
                "runner-invocation",
                "runner-invocation",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/runner-invocation-cases.json",
                    "case_id": "live-host-runtime-info",
                },
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_stdout_json(completed)
        self.assert_response(response, "ok")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual(stderr_records, [])
        self.assert_no_release_promotion_metadata(
            response,
            "tests/speckit-pro/unit/fixtures/installed-plugin-release/runner-invocation-cases.json",
        )
        record = response["data"]["runner_invocation"]
        self.assertEqual(record["status"], "pass")
        self.assertTrue(record["interpreter_resolution"]["accepted"])
        self.assertNotEqual(record["runner_response"].get("evidence_source"), "fixture")
        self.assertEqual(record["runner_response"]["status"], "ok")
        self.assertEqual(record["runner_response"]["data"]["report"]["runner_name"], "speckit_pro_runner")
        self.assert_no_shell_argv(record["invocation"]["argv"])

        from speckit_pro_runner import runtime as runner_runtime

        with tempfile.TemporaryDirectory() as tmp:
            installed_root = Path(tmp) / "installed-cache" / "speckit-pro"
            (installed_root / ".codex-plugin").mkdir(parents=True)
            (installed_root / ".codex-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
            (installed_root / "speckit_pro_runner").mkdir()
            self.assertEqual(runner_runtime.runtime_context(installed_root), "installed_payload")
        self.assertEqual(runner_runtime.runtime_context(PLUGIN_ROOT), "source_checkout")

        runner_response, execution_diag = install_helper.execute_runner_runtime_info(
            [sys.executable, "-m", "speckit_pro_runner"],
            record["runner_request"],
            REPO_ROOT,
            "dist/missing-installed-cache",
        )
        self.assertIsNone(runner_response)
        self.assertEqual(execution_diag["code"], "runner_cache_missing")

        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp) / "fake-payload"
            package = fake_root / "speckit_pro_runner"
            package.mkdir(parents=True)
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "__main__.py").write_text(
                "import json\n"
                "print(json.dumps({"
                "'schema_version':'1.0',"
                "'status':'ok',"
                "'exit_code':0,"
                "'legacy_exit_code':None,"
                "'diagnostics':[],"
                "'data':{'report':{"
                "'runner_name':'fake_runner',"
                "'runner_contract_id':'speckit-pro-runner',"
                "'selected_runtime_name':'python-stdlib-runner',"
                "'source_vs_installed_context':'installed_payload',"
                "'paths':{}"
                "}}}))\n",
                encoding="utf-8",
            )
            runner_response, execution_diag = install_helper.execute_runner_runtime_info(
                [sys.executable, "-m", "speckit_pro_runner"],
                record["runner_request"],
                REPO_ROOT,
                fake_root.as_posix(),
            )
        self.assertIsNotNone(runner_response)
        self.assertEqual(execution_diag["code"], "runner_identity_mismatch")

        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp) / "list-payload"
            package = fake_root / "speckit_pro_runner"
            package.mkdir(parents=True)
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "__main__.py").write_text("print('[]')\n", encoding="utf-8")
            runner_response, execution_diag = install_helper.execute_runner_runtime_info(
                [sys.executable, "-m", "speckit_pro_runner"],
                record["runner_request"],
                REPO_ROOT,
                fake_root.as_posix(),
            )
        self.assertIsNotNone(runner_response)
        self.assertEqual(runner_response["data"]["parsed_type"], "list")
        self.assertEqual(execution_diag["code"], "runner_response_malformed")

        completed, response, stderr_records = run_runner(
            gate_request(
                "runner-invocation",
                "runner-invocation",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/runner-invocation-cases.json",
                    "case_id": "too-old-or-missing",
                },
            )
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_stdout_json(completed)
        self.assert_response(response, "expected_failure")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual([diag["code"] for diag in stderr_records], ["python_runtime_unavailable"])
        record = response["data"]["runner_invocation"]
        self.assertFalse(record["interpreter_resolution"]["accepted"])
        self.assertIsNone(record["interpreter_resolution"]["resolved_executable"])
        self.assertEqual(record["interpreter_resolution"]["failure_code"], "python_runtime_unavailable")
        self.assertEqual(record["interpreter_resolution"]["invocation_argv_prefix"], [])
        self.assertIsNone(record["runner_response"])
        self.assertEqual(record["status"], "blocked")
        self.assertEqual(record["invocation"]["argv"], [])
        self.assertFalse(record["invocation"]["shell_used"])

    def test_installed_release_active_runtime_guard_fixtures_block_only_active_runtime_findings(self) -> None:
        from speckit_pro_runner.gates import active_path_guard

        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "bash",
                "Run bash before status.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/codex-agents/implement-executor.toml",
                "bash",
                "Bash",
                "Require Bash before running this agent.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "shell_interpolation",
                "`speckit-pro/skills/speckit-status/SKILL.md`",
                "`speckit-pro/skills/speckit-status/SKILL.md`",
                "repo_baseline",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "Do not add a shell fallback, jq parsing path, Git Bash, WSL, or PowerShell requirement.",
                "repo",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "Bash",
                "Do not run without Bash.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "bash",
                "Run bash without Python before status.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "shell_interpolation",
                "`bash`",
                "Run `bash` before status.",
                "repo",
            ),
            "blocking_active_runtime",
        )

        cases = installed_release_fixture_cases("active-runtime-guard")
        self.assertEqual(cases["schema_version"], "2.0")
        self.assertEqual(cases["contract_id"], "installed-plugin-release")
        self.assertEqual(
            {case["case_id"] for case in cases["cases"]},
            {
                "blocking-active-runtime-patterns",
                "allowed-runtime-exceptions",
                "final-current-implementation",
                "empty-scan-roots",
                "non-list-scan-roots",
            },
        )
        final_case = next(case for case in cases["cases"] if case["case_id"] == "final-current-implementation")
        self.assertFalse(final_case["scan_changed_sources"])
        self.assertIn(
            "final current implementation scans the full release surface without requiring PR review-base diff metadata",
            cases["coverage"],
        )
        self.assertIn(
            "empty and non-list configured scan roots fail closed instead of falling back to default roots",
            cases["coverage"],
        )
        blocking_case = next(case for case in cases["cases"] if case["case_id"] == "blocking-active-runtime-patterns")
        blocking_yaml = next(file for file in blocking_case["files"] if file["path"] == "speckit-pro/codex-agents/openai.yaml")
        blocking_yaml_findings = active_path_guard.scan_installed_runtime_sources(
            [active_path_guard.SourceFile(blocking_yaml["path"], blocking_yaml["content"], "fixture")],
            REPO_ROOT,
        )
        blocking_yaml_records = {(finding.category, finding.line): finding.pattern for finding in blocking_yaml_findings}
        self.assertIn(("shell_command_wrapper", 2), blocking_yaml_records)
        self.assertIn("/bin/sh", blocking_yaml_records[("shell_command_wrapper", 2)])
        self.assertIn("-c", blocking_yaml_records[("shell_command_wrapper", 2)])
        self.assertIn(("shell_runtime", 6), blocking_yaml_records)
        self.assertIn("/bin/sh", blocking_yaml_records[("shell_runtime", 6)])
        self.assertIn(("shell_runtime", 8), blocking_yaml_records)
        self.assertIn("/usr/bin/zsh", blocking_yaml_records[("shell_runtime", 8)])
        self.assertLessEqual(
            {
                "dist/claude/speckit-pro/hooks",
                "dist/claude/speckit-pro/agents",
                "dist/claude/speckit-pro/skills",
                "dist/claude/speckit-pro/scripts",
                "dist/claude/speckit-pro/speckit_pro_runner",
                "dist/claude/speckit-pro/.claude-plugin",
                "dist/codex/speckit-pro/codex-hooks.json",
                "dist/codex/speckit-pro/codex-agents",
                "dist/codex/speckit-pro/skills",
                "dist/codex/speckit-pro/scripts",
                "dist/codex/speckit-pro/speckit_pro_runner",
                "dist/codex/speckit-pro/.codex-plugin",
                ".github/workflows",
                "README.md",
                "speckit-pro/README.md",
                "docs-site/src/content/docs",
            },
            set(final_case["scan_roots"]),
        )

        with patch.object(active_path_guard, "review_base_ref", return_value=None):
            response = active_path_guard.run_active_runtime_guard(
                SimpleNamespace(helper_id="active-path-guard"),
                SimpleNamespace(
                    operation="active-runtime-guard",
                    request_id="test-final-current-no-review-base",
                    inputs={
                        "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json",
                        "case_id": "final-current-implementation",
                    },
                ),
                REPO_ROOT,
            )
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["data"]["blocking_count"], 0)
        for payload_root in (REPO_ROOT / "dist/claude/speckit-pro", REPO_ROOT / "dist/codex/speckit-pro"):
            for suffix in (".sh", ".ps1", ".bat", ".cmd"):
                self.assertFalse([path for path in payload_root.rglob(f"*{suffix}")], payload_root)

        with patch.object(active_path_guard, "review_base_ref", return_value=None):
            changed_sources = active_path_guard.changed_repo_sources(REPO_ROOT, {"scan_roots": ["speckit-pro/skills"]})
        self.assertIsInstance(changed_sources, active_path_guard.RawFinding)
        self.assertEqual(changed_sources.classification, "blocking_active_runtime")
        self.assertEqual(changed_sources.category, "diff_scan")
        with patch.object(active_path_guard.subprocess, "run", side_effect=OSError("git missing")):
            changed_sources = active_path_guard.changed_repo_sources(REPO_ROOT, {"scan_roots": ["speckit-pro/skills"]})
        self.assertIsInstance(changed_sources, active_path_guard.RawFinding)
        self.assertEqual(changed_sources.classification, "blocking_active_runtime")
        self.assertEqual(changed_sources.category, "diff_scan")
        self.assertNotIn("HEAD^", active_path_guard.review_base_ref.__code__.co_consts)
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "README.md",
                "bash",
                "bash",
                "Install requires Bash before running SpecKit Pro.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "README.md",
                "bash",
                "bash",
                "Install requires Bash before running SpecKit Pro.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "docs-site/src/content/docs/install/codex.md",
                "jq",
                "jq",
                "Installed runtime requires jq before first use.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "README.md",
                "bash",
                "bash",
                "SpecKit Pro does not require Bash.",
                "repo",
            ),
            "docs_non_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "docs-site/src/content/docs/contribute-and-release.md",
                "script_file",
                "scripts/sync-marketplace-versions.sh",
                "`scripts/sync-marketplace-versions.sh`",
                "repo",
            ),
            "docs_non_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "docs-site/src/content/docs/troubleshooting.md",
                "bash",
                "Bash",
                "Bash source-checkout prerequisite",
                "repo",
            ),
            "docs_non_runtime",
        )
        wrapped_negative_findings = active_path_guard.scan_installed_runtime_sources(
            [
                active_path_guard.SourceFile(
                    "docs-site/src/content/docs/install/codex.md",
                    "payload; Bash, Git Bash, WSL, PowerShell-specific command language, and `jq` are\n"
                    "not installed-runtime requirements.",
                    "repo",
                )
            ],
            REPO_ROOT,
        )
        self.assertFalse(
            [finding for finding in wrapped_negative_findings if finding.classification == "blocking_active_runtime"]
        )
        markdown_heading_findings = active_path_guard.scan_installed_runtime_sources(
            [
                active_path_guard.SourceFile(
                    "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                    "# Requires Bash before first use\n",
                    "repo_baseline",
                )
            ],
            REPO_ROOT,
        )
        self.assertTrue(
            [finding for finding in markdown_heading_findings if finding.classification == "blocking_active_runtime"]
        )
        script_suffix_findings = active_path_guard.scan_installed_runtime_sources(
            [
                active_path_guard.SourceFile(
                    "dist/codex/speckit-pro/scripts/install.ps1",
                    "Write-Host 'install'\n",
                    "repo_baseline",
                )
            ],
            REPO_ROOT,
        )
        self.assertTrue(
            [finding for finding in script_suffix_findings if finding.classification == "blocking_active_runtime"]
        )
        payload_detector_findings = active_path_guard.scan_installed_runtime_sources(
            [
                active_path_guard.SourceFile(
                    "dist/codex/speckit-pro/speckit_pro_runner/gates/payloads.py",
                    '    first_line = handle.readline(4096)\n'
                    '    return bool(re.search(r"^#!.*\\b(?:bash|sh|zsh|powershell|pwsh)\\b", first_line))\n',
                    "repo",
                )
            ],
            REPO_ROOT,
        )
        self.assertFalse(
            [finding for finding in payload_detector_findings if finding.classification == "blocking_active_runtime"]
        )
        mixed_tool_guidance_findings = active_path_guard.scan_installed_runtime_sources(
            [
                active_path_guard.SourceFile(
                    "speckit-pro/agents/phase-executor.md",
                    "allowed-tools: Bash, Read\nRun scripts/install.sh before release.\n",
                    "repo",
                )
            ],
            REPO_ROOT,
        )
        self.assertTrue(
            [
                finding
                for finding in mixed_tool_guidance_findings
                if finding.line == 2 and finding.classification == "blocking_active_runtime"
            ]
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "bash",
                "Run bash before status.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "script_file",
                "scripts/setup.sh",
                "Run scripts/setup.sh before use.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "dist/codex/speckit-pro/scripts/install.sh",
                "script_file",
                "*.sh",
                "#!/usr/bin/env bash\njq -n '{}'\n",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "Run jq before use.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "If Python is missing, use command -v jq and run Bash.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "powershell",
                "PowerShell",
                "Requires PowerShell before status.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "script_file",
                "scripts/setup.sh",
                "Run scripts/setup.sh before first use.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "Run jq before status.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/agents/phase-executor.md",
                "shell_interpolation",
                "`$SHELL`",
                "Use `$SHELL` to run the installed agent.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "Bash",
                "Do not add Bash as an installed-runtime requirement.",
                "repo_baseline",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/skills/speckit-upgrade/SKILL.md",
                "bash",
                "Bash",
                "allowed-tools: Bash Read Edit Write",
                "repo",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/skills/speckit-upgrade/SKILL.md",
                "bash",
                "Bash",
                "allowed-tools: Bash Read Edit Write\nRun Bash before use.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "Bash",
                "Maintainer-only source-checkout helper text may mention Bash.",
                "repo",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md",
                "script_file",
                "`estimate-reviewable-loc.sh",
                "The parent runs `estimate-reviewable-loc.sh <plan.md>` via `exec_command`, capturing the exit code.",
                "repo",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "If Python is missing, use command -v jq and run Bash.",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "If Python is missing, use command -v jq and run Bash.",
                "repo_baseline",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "dist/codex/speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "Bash",
                "Do not add Bash as an installed-runtime requirement.",
                "repo_baseline",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/agents/phase-executor.md",
                "bash",
                "Bash",
                "allowed-tools: Bash, Read",
                "repo",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/agents/clarify-executor.md",
                "bash",
                "Bash",
                "disallowedTools: Write, Edit, Bash, Agent",
                "repo",
            ),
            "source_checkout_helper",
        )
        self.assertEqual(
            active_path_guard.classify_installed_runtime_path(
                "speckit-pro/agents/phase-executor.md",
                "bash",
                "Bash",
                "allowed-tools: Bash, Read; run scripts/install.sh",
                "repo",
            ),
            "blocking_active_runtime",
        )
        self.assertEqual(
            active_path_guard.zero_bash_classification(
                "dist/claude/speckit-pro/agents/clarify-executor.md",
                "bash",
                "Bash",
                "disallowedTools: Write, Edit, Bash, Agent",
                [],
                declaration_line="disallowedTools: Write, Edit, Bash, Agent",
            ),
            "blocking_zero_bash",
        )
        self.assertEqual(
            active_path_guard.zero_bash_classification(
                "dist/claude/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md",
                "shell_interpolation",
                "$SHELL",
                "Do not use $SHELL to run installed helpers.",
                [],
                declaration_line="Do not use $SHELL to run installed helpers.",
            ),
            "negative_policy",
        )
        self.assertEqual(
            active_path_guard.zero_bash_classification(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "bash",
                "Bash",
                "Run Bash instead of Python.",
                [],
                declaration_line="Run Bash instead of Python.",
            ),
            "blocking_zero_bash",
        )
        self.assertEqual(
            active_path_guard.zero_bash_classification(
                "speckit-pro/skills/speckit-status/SKILL.md",
                "jq",
                "jq",
                "Use jq rather than Python JSON parsing.",
                [],
                declaration_line="Use jq rather than Python JSON parsing.",
            ),
            "blocking_zero_bash",
        )
        missing_roots = active_path_guard.missing_installed_runtime_scan_root_findings(
            REPO_ROOT,
            {"scan_roots": ["dist/missing-runtime-root"]},
        )
        self.assertEqual(len(missing_roots), 1)
        self.assertEqual(missing_roots[0].classification, "blocking_active_runtime")
        self.assertEqual(missing_roots[0].category, "scan_root")
        for malformed_case in ({"scan_roots": []}, {"scan_roots": "speckit-pro/skills"}):
            with self.subTest(malformed_case=malformed_case):
                malformed_roots = active_path_guard.missing_installed_runtime_scan_root_findings(REPO_ROOT, malformed_case)
                self.assertEqual(len(malformed_roots), 1)
                self.assertEqual(malformed_roots[0].classification, "blocking_active_runtime")
                self.assertEqual(malformed_roots[0].category, "scan_root")
                changed_sources = active_path_guard.changed_repo_sources(REPO_ROOT, malformed_case)
                self.assertIsInstance(changed_sources, active_path_guard.RawFinding)
                self.assertEqual(changed_sources.classification, "blocking_active_runtime")
                self.assertEqual(changed_sources.category, "scan_root")

        with tempfile.TemporaryDirectory() as tmp:
            completed, response, stderr_records = run_runner(
                gate_request(
                    "active-path-guard",
                    "active-runtime-guard",
                    inputs={"repo_root": tmp},
                )
            )
        self.assertEqual(completed.returncode, 3)
        self.assert_response(response, "missing_prerequisite")
        self.assertEqual([diag["code"] for diag in stderr_records], ["missing_prerequisite"])
        self.assertEqual(response["data"]["gate"]["comparison_ids"], ["installed-plugin-release-active-runtime-guard"])
        self.assert_no_release_promotion_metadata(
            response,
            "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json",
        )

        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "active-runtime-guard",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json",
                    "case_id": "blocking-active-runtime-patterns",
                },
            )
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assertEqual([diag["code"] for diag in stderr_records], ["active_runtime_guard_blocked"])
        self.assertGreaterEqual(response["data"]["blocking_count"], 4)
        self.assertTrue(
            all(finding["classification"] == "blocking_active_runtime" for finding in response["data"]["findings"])
        )
        self.assertLessEqual(
            {"bash", "script_file", "jq", "git_bash", "wsl"},
            {finding["category"] for finding in response["data"]["findings"]},
        )

        for case_id in ["empty-scan-roots", "non-list-scan-roots"]:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "active-path-guard",
                        "active-runtime-guard",
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 1)
                self.assert_response(response, "expected_failure")
                self.assertEqual([diag["code"] for diag in stderr_records], ["active_runtime_guard_blocked"])
                self.assertEqual(response["data"]["blocking_count"], 1)
                self.assertEqual({finding["category"] for finding in response["data"]["findings"]}, {"scan_root"})

        response = self.assert_runner_ok(
            gate_request(
                "active-path-guard",
                "active-runtime-guard",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json",
                    "case_id": "allowed-runtime-exceptions",
                },
            )
        )
        self.assertEqual(response["data"]["blocking_count"], 0)
        self.assertLessEqual(
            {
                "archive_provenance",
                "upstream_spec_kit_helper",
                "test_fixture",
                "ci_dispatch_glue",
            },
            set(response["data"]["classified_counts"]),
        )

        response = self.assert_runner_ok(
            gate_request(
                "active-path-guard",
                "active-runtime-guard",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/active-runtime-guard-cases.json",
                    "case_id": "final-current-implementation",
                },
            )
        )
        self.assertEqual(response["data"]["blocking_count"], 0)

    def test_installed_release_payload_completeness_fixtures_cover_release_payload_blockers(self) -> None:
        cases = installed_release_fixture_cases("payload-completeness")
        self.assertEqual(cases["schema_version"], "2.0")
        self.assertEqual(cases["contract_id"], "installed-plugin-release")
        self.assertEqual(
            {case["case_id"] for case in cases["cases"]},
            {
                "current-committed-dist",
                "empty-surfaces",
                "invalid-surfaces",
                "missing-runner-file",
                "stale-metadata",
                "extra-file",
                "path-leak",
                "transform-mismatch",
            },
        )
        for label in [
            "source-derived expected inventory",
            "apply-mode rebuild comparison",
            "missing runner file blocker",
            "stale metadata blocker",
            "extra file blocker",
            "path leak blocker",
            "empty surface selection blocker",
            "invalid surface selection blocker",
            "transform mismatch blocker",
        ]:
            self.assertIn(label, cases["coverage"])

        request = installed_release_fixture_request("payload-completeness")
        self.assertEqual(request["helper_id"], "payload-gate")
        self.assertEqual(request["operation"], "payload-completeness")
        self.assertEqual(request["mode"], "read_only")

        apply_request = installed_release_fixture_request("payload-completeness-apply")
        self.assertEqual(apply_request["helper_id"], "payload-gate")
        self.assertEqual(apply_request["operation"], "payload-completeness")
        self.assertEqual(apply_request["mode"], "apply")
        self.assertTrue(apply_request["inputs"]["apply_dist"])

    def test_plugin_bash_confinement_zero_bash_guard_fixtures_cover_source_payload_and_cache_proof(self) -> None:
        from speckit_pro_runner.gates import active_path_guard

        cases = plugin_bash_confinement_fixture_cases("zero-bash-guard")
        self.assertEqual(cases["schema_version"], "2.0")
        self.assertEqual(cases["contract_id"], "plugin-bash-confinement")
        self.assertEqual(
            {case["case_id"] for case in cases["cases"]},
            {
                "clean-fixture",
                "blocking-active-source",
                "blocking-active-allowlist-entry",
                "blocking-missing-allowlist-fields",
                "blocking-unsupported-allowlist-field",
                "blocking-traversal-allowlist-path",
                "blocking-invalid-allowlist-line-bounds",
                "blocking-python-shell-exec",
                "blocking-uppercase-script-file",
                "blocking-suffixful-shell-script",
                "blocking-extensionless-script",
                "blocking-active-reference",
                "blocking-active-source-tree-language",
                "blocking-active-guidance-categories",
                "blocking-active-tool-declaration",
                "missing-scan-root",
                "missing-required-scan-root",
                "traversal-scan-root",
                "malformed-scan-root",
                "empty-scan-roots",
                "non-list-scan-roots",
                "missing-installed-cache-proof",
                "final-current-implementation",
            },
        )
        final_case = next(case for case in cases["cases"] if case["case_id"] == "final-current-implementation")
        self.assertLessEqual(
            {"speckit-pro", "scripts/build-plugin-payloads.py", "dist/claude/speckit-pro", "dist/codex/speckit-pro", "README.md"},
            set(final_case["scan_roots"]),
        )
        self.assertFalse(final_case["require_installed_cache_proof"])
        self.assertNotIn("installed_cache_proof", final_case)
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/usr/bin/env", "-S bash -lc jq -r . package.json"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["sh", "-c", "python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/bin/sh", "runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/usr/bin/env", "zsh", "runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/usr/bin/env", "-i", "sh", "-c", "python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["env", "FOO=bar", "zsh", "-c", "python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/usr/bin/env", "--ignore-environment", "sh", "-c", "python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/bin/sh", "--noprofile", "--norc", "-c", "python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/bin/zsh", "-o", "pipefail", "-c", "python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/usr/bin/env", "-S", "sh -c python -m speckit_pro_runner"]))
        self.assertTrue(active_path_guard.command_argv_contains_forbidden(["/usr/bin/env", "-S sh -c python -m speckit_pro_runner"]))
        with tempfile.TemporaryDirectory() as tmp:
            extensionless = Path(tmp) / "install"
            extensionless.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            self.assertEqual(active_path_guard.count_prohibited_script_files(extensionless), 1)
            zsh_script = Path(tmp) / "install.zsh"
            zsh_script.write_text("#!/usr/bin/env zsh\n", encoding="utf-8")
            self.assertEqual(active_path_guard.count_prohibited_script_files(zsh_script), 1)
            bash_script = Path(tmp) / "install.bash"
            bash_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            self.assertEqual(active_path_guard.count_prohibited_script_files(bash_script), 1)
            oversized = Path(tmp) / "large-install"
            oversized.write_text("#!/usr/bin/env bash\n" + ("#" * (active_path_guard.MAX_SCAN_BYTES + 1)), encoding="utf-8")
            self.assertEqual(active_path_guard.count_prohibited_script_files(oversized), 1)
        with tempfile.TemporaryDirectory(prefix=".plugin-bash-confinement-large-script-", dir=PLUGIN_ROOT) as tmp:
            temp_root = Path(tmp)
            large_suffix_script = temp_root / "install.sh"
            large_suffix_script.write_text("#!/usr/bin/env bash\n" + ("#" * (active_path_guard.MAX_SCAN_BYTES + 1)), encoding="utf-8")
            large_extensionless_script = temp_root / "install"
            large_extensionless_script.write_text(
                "#!/usr/bin/env bash\n" + ("#" * (active_path_guard.MAX_SCAN_BYTES + 1)),
                encoding="utf-8",
            )
            sources = active_path_guard.scan_repo_sources(
                REPO_ROOT,
                roots=(temp_root.relative_to(REPO_ROOT).as_posix(),),
            )
            findings = active_path_guard.zero_bash_source_findings(sources, [])
            script_paths = {finding.path for finding in findings if finding.category == "script_file"}
            self.assertLessEqual(
                {
                    large_suffix_script.relative_to(REPO_ROOT).as_posix(),
                    large_extensionless_script.relative_to(REPO_ROOT).as_posix(),
                },
                script_paths,
            )
        with tempfile.TemporaryDirectory(prefix=".plugin-bash-confinement-symlink-", dir=PLUGIN_ROOT) as tmp:
            temp_root = Path(tmp)
            with tempfile.TemporaryDirectory() as outside:
                outside_script = Path(outside) / "install"
                outside_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
                symlink = temp_root / "install"
                symlink.symlink_to(outside_script)
                sources = active_path_guard.scan_repo_sources(
                    REPO_ROOT,
                    roots=(temp_root.relative_to(REPO_ROOT).as_posix(),),
                )
            self.assertFalse([source for source in sources if source.path == symlink.relative_to(REPO_ROOT).as_posix()])
        with tempfile.TemporaryDirectory() as tmp:
            completed, response, stderr_records = run_runner(
                gate_request(
                    "active-path-guard",
                    "zero-bash-guard",
                    inputs={"repo_root": tmp},
                )
            )
            self.assertEqual(completed.returncode, 3)
            self.assert_response(response, "missing_prerequisite")
            self.assertEqual([diag["code"] for diag in stderr_records], ["missing_prerequisite"])
            self.assertEqual(response["data"]["gate"]["comparison_ids"], ["plugin-bash-confinement-zero-bash-guard"])
            self.assertEqual(response["data"]["gate"]["gate_status"], "fail")
            self.assertEqual(response["data"]["contract_id"], "plugin-bash-confinement")
            self.assertEqual(response["data"]["status"], "fail")
            self.assertEqual(response["data"]["blocking_count"], 1)

        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "zero-bash-guard",
                inputs={"case_file": "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/missing-case-file.json"},
            )
        )
        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error")
        self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_case_file"])
        self.assertEqual(response["data"]["gate"]["gate_status"], "fail")
        self.assertEqual(response["data"]["contract_id"], "plugin-bash-confinement")
        self.assertEqual(response["data"]["status"], "fail")

        response = self.assert_runner_ok(plugin_bash_confinement_fixture_request("zero-bash-guard"))
        clean_response = response
        result = response["data"]
        self.assertEqual(result["contract_id"], "plugin-bash-confinement")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["blocking_count"], 0)
        self.assertEqual(result["script_file_count"], 0)
        self.assertTrue(result["allowlist"]["release_readiness_excluded"])
        self.assertFalse(result["installed_cache_proof"]["required"])
        self.assertEqual(result["installed_cache_proof"]["proof_count"], 0)
        self.assertFalse(result["installed_cache_proof"]["source_derived"])
        self.assertIsNone(result["installed_cache_proof"]["mutable_user_cache"])

        scan_root_only_cases = {
            "missing-scan-root",
            "missing-required-scan-root",
            "traversal-scan-root",
            "malformed-scan-root",
            "empty-scan-roots",
            "non-list-scan-roots",
        }
        for case_id in [
            "blocking-active-source",
            "blocking-active-allowlist-entry",
            "blocking-missing-allowlist-fields",
            "blocking-unsupported-allowlist-field",
            "blocking-traversal-allowlist-path",
            "blocking-invalid-allowlist-line-bounds",
            "blocking-python-shell-exec",
            "blocking-uppercase-script-file",
            "blocking-suffixful-shell-script",
            "blocking-extensionless-script",
            "blocking-active-reference",
            "blocking-active-source-tree-language",
            "blocking-active-guidance-categories",
            "blocking-active-tool-declaration",
            "missing-scan-root",
            "missing-required-scan-root",
            "traversal-scan-root",
            "malformed-scan-root",
            "empty-scan-roots",
            "non-list-scan-roots",
            "missing-installed-cache-proof",
        ]:
            with self.subTest(case_id=case_id):
                response = run_plugin_bash_confinement_case(
                    case_id,
                    skip_source_scan=case_id in scan_root_only_cases,
                    skip_repo_source_scan=True,
                )
                self.assert_response(response, "expected_failure")
                self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["zero_bash_guard_blocked"])
                self.assertGreater(response["data"]["blocking_count"], 0)
                self.assertTrue(
                    all(finding["classification"] == "blocking_zero_bash" for finding in response["data"]["findings"])
                )

        expected_categories = {
            "blocking-active-source": {"bash", "git_bash", "jq", "script_file", "shell_command_wrapper", "shell_runtime", "shell_true", "wsl"},
            "blocking-missing-allowlist-fields": {"allowlist"},
            "blocking-unsupported-allowlist-field": {"allowlist"},
            "blocking-traversal-allowlist-path": {"allowlist"},
            "blocking-invalid-allowlist-line-bounds": {"allowlist"},
            "blocking-python-shell-exec": {"os_system", "shell_true", "command_string_subprocess", "command_argv_subprocess"},
            "blocking-uppercase-script-file": {"script_file"},
            "blocking-suffixful-shell-script": {"script_file"},
            "blocking-extensionless-script": {"script_file"},
            "blocking-active-reference": {"bash", "script_file", "wsl"},
            "blocking-active-source-tree-language": {"bash", "jq"},
            "blocking-active-guidance-categories": {
                "bash",
                "wsl",
                "script_file",
                "powershell_helper",
                "jq",
                "shell_interpolation",
                "shell_command_wrapper",
                "shell_runtime",
            },
            "blocking-active-tool-declaration": {"bash", "shell_runtime"},
            "missing-required-scan-root": {"scan_root"},
            "traversal-scan-root": {"scan_root"},
            "malformed-scan-root": {"scan_root"},
            "empty-scan-roots": {"scan_root"},
            "non-list-scan-roots": {"scan_root"},
        }
        for case_id, categories in expected_categories.items():
            with self.subTest(case_id=f"{case_id}-categories"):
                response = run_plugin_bash_confinement_case(
                    case_id,
                    skip_source_scan=case_id in scan_root_only_cases,
                    skip_repo_source_scan=True,
                )
                self.assert_response(response, "expected_failure")
                actual_categories = {finding["category"] for finding in response["data"]["findings"]}
                self.assertLessEqual(categories, actual_categories)

        capped = active_path_guard.bounded_findings(
            [
                active_path_guard.RawFinding(
                    path=f"speckit-pro/file-{index}.py",
                    line=None,
                    category="bash",
                    pattern="bash",
                    reason="test",
                    active_role="test",
                    classification="blocking_zero_bash",
                    remediation="test",
                )
                for index in range(600)
            ],
        )
        self.assertEqual(len(capped), 25)

        yaml_case = next(case for case in cases["cases"] if case["case_id"] == "blocking-active-guidance-categories")
        yaml_source = next(file for file in yaml_case["files"] if file["path"] == "speckit-pro/codex-agents/openai.yaml")
        yaml_findings = active_path_guard.zero_bash_source_findings(
            [active_path_guard.SourceFile(yaml_source["path"], yaml_source["content"], "fixture")],
            [],
        )
        yaml_records = {(finding.category, finding.line): finding.pattern for finding in yaml_findings}
        self.assertIn(("shell_command_wrapper", 2), yaml_records)
        self.assertIn("/bin/sh", yaml_records[("shell_command_wrapper", 2)])
        self.assertIn("-c", yaml_records[("shell_command_wrapper", 2)])
        self.assertIn(("shell_command_wrapper", 7), yaml_records)
        self.assertIn("/usr/bin/zsh", yaml_records[("shell_command_wrapper", 7)])
        self.assertIn("pipefail", yaml_records[("shell_command_wrapper", 7)])
        self.assertIn("-c", yaml_records[("shell_command_wrapper", 7)])
        self.assertIn(("shell_runtime", 14), yaml_records)
        self.assertIn("/bin/sh", yaml_records[("shell_runtime", 14)])
        self.assertIn("runner", yaml_records[("shell_runtime", 14)])
        self.assertIn(("shell_runtime", 16), yaml_records)
        self.assertIn("/bin/sh", yaml_records[("shell_runtime", 16)])
        self.assertIn(("shell_runtime", 18), yaml_records)
        self.assertIn("/usr/bin/zsh", yaml_records[("shell_runtime", 18)])

        python_case = next(case for case in cases["cases"] if case["case_id"] == "blocking-python-shell-exec")
        dynamic_python = next(file for file in python_case["files"] if file["path"].endswith("dynamic_shell.py"))
        dynamic_python_findings = active_path_guard.zero_bash_source_findings(
            [active_path_guard.SourceFile(dynamic_python["path"], dynamic_python["content"], "fixture")],
            [],
        )
        dynamic_python_records = {(finding.category, finding.line): finding.pattern for finding in dynamic_python_findings}
        self.assertIn(("shell_true", 8), dynamic_python_records)
        self.assertIn("shell=use_shell", dynamic_python_records[("shell_true", 8)])
        self.assertIn(("shell_true", 9), dynamic_python_records)
        self.assertIn("shell=1", dynamic_python_records[("shell_true", 9)])
        self.assertNotIn(("shell_true", 10), dynamic_python_records)
        self.assertIn(("command_string_subprocess", 11), dynamic_python_records)
        self.assertIn("subprocess.getoutput", dynamic_python_records[("command_string_subprocess", 11)])
        self.assertIn(("command_string_subprocess", 12), dynamic_python_records)
        self.assertIn("subprocess.getstatusoutput", dynamic_python_records[("command_string_subprocess", 12)])
        self.assertIn(("os_system", 13), dynamic_python_records)
        self.assertIn("os.popen", dynamic_python_records[("os_system", 13)])
        self.assertIn(("os_system", 14), dynamic_python_records)
        self.assertIn("os_popen", dynamic_python_records[("os_system", 14)])
        self.assertIn(("command_string_subprocess", 15), dynamic_python_records)
        self.assertIn("getoutput", dynamic_python_records[("command_string_subprocess", 15)])
        self.assertIn(("command_string_subprocess", 16), dynamic_python_records)
        self.assertIn("getstatusoutput", dynamic_python_records[("command_string_subprocess", 16)])

        self.assert_plugin_bash_confinement_contracts_match_fixtures(clean_response)

    def test_compact_installed_cache_oracle_covers_payload_shape_and_platform_transforms(self) -> None:
        from speckit_pro_runner.gates import payloads as payload_gate

        tracked_files = sorted(
            path.relative_to(INSTALLED_CACHE_ORACLE_PATH.parent).as_posix()
            for path in INSTALLED_CACHE_ORACLE_PATH.parent.rglob("*")
            if path.is_file()
        )
        self.assertEqual(tracked_files, ["oracle.json"])

        with materialized_installed_cache_oracle() as (oracle, roots):
            for product, surface in oracle["surfaces"].items():
                records = payload_gate.scan_payload_files(
                    REPO_ROOT / roots[product]["installed_root"],
                    source_root=REPO_ROOT / "speckit-pro",
                    surface=product,
                )
                actual = [
                    {
                        key: record[key]
                        for key in ("path", "source_path", "kind", "transform")
                    }
                    for record in records
                ]
                expected = [
                    {
                        key: record[key]
                        for key in ("path", "source_path", "kind", "transform")
                    }
                    for record in surface["files"]
                ]
                self.assertEqual(actual, expected, product)

    def test_installed_cache_oracle_detects_missing_extra_content_and_hash_mutations(self) -> None:
        from speckit_pro_runner.gates import active_path_guard

        allowlist = json.loads(
            (PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "allowlist.json").read_text(encoding="utf-8")
        )["entries"]
        mutations = ("missing", "extra", "content", "hash")
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with materialized_installed_cache_oracle() as (oracle, roots):
                    proof = installed_cache_oracle_proof(roots)
                    claude_root = REPO_ROOT / roots["claude"]["installed_root"]
                    first_path = oracle["surfaces"]["claude"]["files"][0]["path"]
                    if mutation == "missing":
                        (claude_root / first_path).unlink()
                    elif mutation == "extra":
                        (claude_root / "unexpected.txt").write_text("extra\n", encoding="utf-8")
                    elif mutation == "content":
                        target = claude_root / first_path
                        target.write_text(target.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
                    else:
                        proof["proofs"][0]["source_payload_tree_hash"] = "0" * 64

                    with installed_cache_oracle_root_policy(roots):
                        findings = active_path_guard.installed_cache_proof_findings(
                            REPO_ROOT,
                            proof,
                            allowlist,
                        )

                hash_findings = [
                    finding
                    for finding in findings
                    if finding.category == "source_payload_tree_hash"
                ]
                self.assertTrue(hash_findings, mutation)
                if mutation == "hash":
                    self.assertTrue(any("stale" in finding.reason for finding in hash_findings))
                else:
                    self.assertTrue(any("inventory does not match" in finding.reason for finding in hash_findings))

    def test_installed_cache_oracle_detects_bash_and_root_failures(self) -> None:
        from speckit_pro_runner.gates import active_path_guard

        allowlist = json.loads(
            (PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "allowlist.json").read_text(encoding="utf-8")
        )["entries"]
        with materialized_installed_cache_oracle() as (_, roots):
            source_readme = REPO_ROOT / roots["claude"]["source_root"] / "README.md"
            installed_readme = REPO_ROOT / roots["claude"]["installed_root"] / "README.md"
            for readme in (source_readme, installed_readme):
                readme.write_text("Run Bash before continuing.\n", encoding="utf-8")
            proof = installed_cache_oracle_proof(roots)
            with installed_cache_oracle_root_policy(roots):
                findings = active_path_guard.installed_cache_proof_findings(
                    REPO_ROOT,
                    proof,
                    allowlist,
                )
            self.assertIn("bash", {finding.category for finding in findings})

            proof["proofs"][0]["installed_root"] = "../outside-repository"
            with installed_cache_oracle_root_policy(roots):
                findings = active_path_guard.installed_cache_proof_findings(
                    REPO_ROOT,
                    proof,
                    allowlist,
                )
            self.assertIn("installed_root", {finding.category for finding in findings})

    def test_installed_cache_oracle_detects_proof_failure_modes(self) -> None:
        from speckit_pro_runner.gates import active_path_guard

        allowlist = json.loads(
            (PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "allowlist.json").read_text(encoding="utf-8")
        )["entries"]
        with materialized_installed_cache_oracle() as (_, roots):
            clean = installed_cache_oracle_proof(roots)
            with installed_cache_oracle_root_policy(roots):
                self.assertEqual(
                    active_path_guard.installed_cache_proof_findings(REPO_ROOT, clean, allowlist),
                    [],
                )

            mutations = {
                "mutable": ({**clean, "proofs": [{**clean["proofs"][0], "mutable_user_cache": True}, clean["proofs"][1]]}, "mutable_user_cache"),
                "missing-product": ({**clean, "proofs": clean["proofs"][:1]}, "product_coverage"),
                "missing-source": ({**clean, "proofs": [{key: value for key, value in clean["proofs"][0].items() if key != "source_payload_root"}, clean["proofs"][1]]}, "source_payload_root"),
            }
            for name, (proof, category) in mutations.items():
                with self.subTest(name=name):
                    with installed_cache_oracle_root_policy(roots):
                        findings = active_path_guard.installed_cache_proof_findings(
                            REPO_ROOT,
                            proof,
                            allowlist,
                        )
                    self.assertIn(category, {finding.category for finding in findings})

    def test_installed_cache_proof_is_gate_owned_and_excluded_from_payloads(self) -> None:
        from speckit_pro_runner.gates import active_path_guard

        proof_path = active_path_guard.INSTALLED_CACHE_PROOF
        self.assertEqual(proof_path, "speckit-pro/gate-evidence/installed-cache-proof.json")
        self.assertFalse((REPO_ROOT / proof_path).exists())
        self.assertEqual(
            active_path_guard.load_installed_cache_proof(
                REPO_ROOT,
                {"require_installed_cache_proof": False},
            )["proofs"],
            [],
        )
        rejected = active_path_guard.load_installed_cache_proof(
            REPO_ROOT,
            {"installed_cache_proof": "unknown-installed-cache-proof.json"},
        )
        self.assertEqual(rejected["code"], "unsupported_installed_cache_proof")
        scanned_paths = {
            source.path
            for source in active_path_guard.scan_repo_sources(REPO_ROOT, roots=("speckit-pro",))
        }
        self.assertNotIn(proof_path, scanned_paths)
        for payload_root in ("dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(payload_root=payload_root):
                self.assertFalse((REPO_ROOT / payload_root / "gate-evidence").exists())

    def test_plugin_bash_confinement_runner_rejects_malformed_proof_documents(self) -> None:
        from speckit_pro_runner.gates import active_path_guard, registry

        cases = plugin_bash_confinement_fixture_cases("zero-bash-guard")
        clean_case = next(case for case in cases["cases"] if case["case_id"] == "clean-fixture")
        canonical_proof = {
            "schema_version": "2.0",
            "contract_id": "plugin-bash-confinement",
            "proofs": [],
        }
        entry = next(
            operation
            for operation in registry.all_gate_operations()
            if operation.operation == "zero-bash-guard"
        )
        malformed_documents = (
            ("schema-version", {**canonical_proof, "schema_version": "future"}, "invalid_installed_cache_proof"),
            ("contract-id", {**canonical_proof, "contract_id": "unknown-contract"}, "invalid_installed_cache_proof"),
            ("proofs-shape", {**canonical_proof, "proofs": {}}, "invalid_installed_cache_proof"),
            ("unknown-field", {**canonical_proof, "unexpected": True}, "invalid_installed_cache_proof"),
        )

        with tempfile.TemporaryDirectory(
            prefix=".malformed-proof-",
            dir=PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR,
        ) as fixture_root:
            fixture_dir = Path(fixture_root)
            proof_file = fixture_dir / "proof.json"
            case_file = fixture_dir / "cases.json"
            proof_path = proof_file.relative_to(REPO_ROOT).as_posix()
            case_path = case_file.relative_to(REPO_ROOT).as_posix()

            for case_id, document, expected_category in malformed_documents:
                with self.subTest(case_id=case_id):
                    proof_file.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
                    case = {**clean_case, "case_id": case_id, "installed_cache_proof": proof_path}
                    case_file.write_text(
                        json.dumps(
                            {
                                "schema_version": "2.0",
                                "contract_id": "plugin-bash-confinement",
                                "cases": [case],
                            },
                            indent=2,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    request = SimpleNamespace(
                        request_id=f"test-malformed-proof-{case_id}",
                        operation="zero-bash-guard",
                        inputs={"case_file": case_path, "case_id": case_id},
                    )
                    with (
                        patch.object(active_path_guard, "INSTALLED_CACHE_PROOF", proof_path),
                        patch.object(active_path_guard, "source_files", return_value=[]),
                        patch.object(active_path_guard, "scan_repo_sources", return_value=[]),
                    ):
                        response = active_path_guard.run_active_path_guard(entry, request)
                    self.assert_response(response, "expected_failure")
                    self.assertEqual(
                        {finding["category"] for finding in response["data"]["findings"]},
                        {expected_category},
                    )

            canonical_path_case = {**clean_case, "case_id": "canonical-path", "installed_cache_proof": proof_path}
            case_file.write_text(
                json.dumps(
                    {
                        "schema_version": "2.0",
                        "contract_id": "plugin-bash-confinement",
                        "cases": [canonical_path_case],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            request = SimpleNamespace(
                request_id="test-malformed-proof-canonical-path",
                operation="zero-bash-guard",
                inputs={"case_file": case_path, "case_id": "canonical-path"},
            )
            with (
                patch.object(active_path_guard, "source_files", return_value=[]),
                patch.object(active_path_guard, "scan_repo_sources", return_value=[]),
            ):
                response = active_path_guard.run_active_path_guard(entry, request)
            self.assert_response(response, "expected_failure")
            self.assertEqual(
                {finding["category"] for finding in response["data"]["findings"]},
                {"unsupported_installed_cache_proof"},
            )

    def test_plugin_bash_confinement_installed_cache_proof_blocks_empty_payload_roots(self) -> None:
        from speckit_pro_runner.gates import active_path_guard

        with tempfile.TemporaryDirectory(prefix="plugin-bash-confinement-empty-", dir=REPO_ROOT / "dist" / "claude") as claude_root:
            with tempfile.TemporaryDirectory(prefix="plugin-bash-confinement-empty-", dir=REPO_ROOT / "dist" / "codex") as codex_root:
                with tempfile.TemporaryDirectory(prefix=".plugin-bash-confinement-proof-", dir=REPO_ROOT) as proof_root:
                    proof_dir = Path(proof_root)
                    proof_file = proof_dir / "installed-cache-proof-empty.json"
                    proof_file.write_text(
                        json.dumps(
                            {
                                "schema_version": "2.0",
                                "contract_id": "plugin-bash-confinement",
                                "proofs": [
                                    {
                                        "product": "claude",
                                        "surface": "claude_payload_fixture",
                                        "installed_root": Path(claude_root).relative_to(REPO_ROOT).as_posix(),
                                        "source_payload_root": Path(claude_root).relative_to(REPO_ROOT).as_posix(),
                                        "source_payload_tree_hash": "0" * 64,
                                        "source_derived": True,
                                        "mutable_user_cache": False,
                                        "script_file_count": 0,
                                        "active_guidance_findings": [],
                                        "allowlist_release_readiness_excluded": True,
                                    },
                                    {
                                        "product": "codex",
                                        "surface": "codex_payload_fixture",
                                        "installed_root": Path(codex_root).relative_to(REPO_ROOT).as_posix(),
                                        "source_payload_root": Path(codex_root).relative_to(REPO_ROOT).as_posix(),
                                        "source_payload_tree_hash": "0" * 64,
                                        "source_derived": True,
                                        "mutable_user_cache": False,
                                        "script_file_count": 0,
                                        "active_guidance_findings": [],
                                        "allowlist_release_readiness_excluded": True,
                                    },
                                ],
                            },
                            indent=2,
                        )
                        + "\n",
                        encoding="utf-8",
                    )

                    proof = json.loads(proof_file.read_text(encoding="utf-8"))
                    allowlist = json.loads(
                        (PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "allowlist.json").read_text(encoding="utf-8")
                    )["entries"]
                    findings = active_path_guard.installed_cache_proof_findings(
                        REPO_ROOT,
                        proof,
                        allowlist,
                    )

        categories = {finding.category for finding in findings}
        self.assertLessEqual({"source_payload_root", "installed_root"}, categories)

    def test_plugin_bash_confinement_installed_cache_proof_blocks_schema_drift(self) -> None:
        from speckit_pro_runner.gates import active_path_guard

        allowlist = json.loads(
            (PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "allowlist.json").read_text(encoding="utf-8")
        )["entries"]
        with materialized_installed_cache_oracle() as (_, roots):
            proof = installed_cache_oracle_proof(roots)
            proof["proofs"][0].pop("surface")
            proof["proofs"][1]["product"] = "cursor"
            proof["proofs"][1]["unexpected_field"] = "drift"
            with installed_cache_oracle_root_policy(roots):
                findings = active_path_guard.installed_cache_proof_findings(
                    REPO_ROOT,
                    proof,
                    allowlist,
                )

        categories = {finding.category for finding in findings}
        self.assertLessEqual({"surface", "product", "malformed"}, categories)

    def test_plugin_bash_confinement_zero_bash_guard_allows_missing_optional_installed_cache_proof(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".plugin-bash-confinement-optional-proof-", dir=REPO_ROOT) as scan_root:
            scan_dir = Path(scan_root)
            (scan_dir / "README.md").write_text("Python runner only.\n", encoding="utf-8")
            case_file = scan_dir / "zero-bash-optional-proof-case.json"
            case_file.write_text(
                json.dumps(
                    {
                        "schema_version": "2.0",
                        "contract_id": "plugin-bash-confinement",
                        "cases": [
                            {
                                "case_id": "optional-proof-clean-root",
                                "scan_roots": [
                                    "speckit-pro",
                                    "scripts/build-plugin-payloads.py",
                                    "dist/claude/speckit-pro",
                                    "dist/codex/speckit-pro",
                                    "README.md",
                                ],
                                "require_installed_cache_proof": False,
                                "allowlist_file": "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/allowlist.json",
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            completed, response, stderr_records = run_runner(
                gate_request(
                    "active-path-guard",
                    "zero-bash-guard",
                    inputs={
                        "case_file": case_file.relative_to(REPO_ROOT).as_posix(),
                        "case_id": "optional-proof-clean-root",
                    },
                )
            )

        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        self.assertFalse(response["data"]["installed_cache_proof"]["required"])
        self.assertEqual(response["data"]["installed_cache_proof"]["proof_count"], 0)
        self.assertEqual(response["data"]["blocking_count"], 0)

    def test_plugin_bash_confinement_zero_bash_guard_blocks_physical_uppercase_script_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".plugin-bash-confinement-uppercase-", dir=REPO_ROOT) as scan_root:
            scan_dir = Path(scan_root)
            (scan_dir / "RUN.SH").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            case_file = scan_dir / "zero-bash-uppercase-case.json"
            case_file.write_text(
                json.dumps(
                    {
                        "schema_version": "2.0",
                        "contract_id": "plugin-bash-confinement",
                        "cases": [
                            {
                                "case_id": "physical-uppercase-script",
                                "scan_roots": [scan_dir.relative_to(REPO_ROOT).as_posix()],
                                "require_installed_cache_proof": False,
                                "allowlist_file": "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/allowlist.json",
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            completed, response, stderr_records = run_runner(
                gate_request(
                    "active-path-guard",
                    "zero-bash-guard",
                    inputs={
                        "case_file": case_file.relative_to(REPO_ROOT).as_posix(),
                        "case_id": "physical-uppercase-script",
                    },
                )
            )

        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assertEqual([diag["code"] for diag in stderr_records], ["zero_bash_guard_blocked"])
        self.assertIn("script_file", {finding["category"] for finding in response["data"]["findings"]})

    def assert_plugin_bash_confinement_contracts_match_fixtures(self, response: dict[str, Any]) -> None:
        request_schema = json.loads((PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR / "zero-bash-guard-request.schema.json").read_text(encoding="utf-8"))
        result_schema = json.loads((PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR / "zero-bash-guard-result.schema.json").read_text(encoding="utf-8"))
        proof_schema = json.loads((PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR / "installed-cache-proof.schema.json").read_text(encoding="utf-8"))
        allowlist_schema = json.loads((PLUGIN_BASH_CONFINEMENT_CONTRACT_DIR / "historical-allowlist-entry.schema.json").read_text(encoding="utf-8"))

        request = plugin_bash_confinement_fixture_request("zero-bash-guard")
        self.assertLessEqual(set(request_schema["required"]), set(request))
        self.assertEqual(request_schema["properties"]["operation"]["const"], request["operation"])
        self.assertEqual(request_schema["properties"]["mode"]["const"], request["mode"])
        input_schema = request_schema["properties"]["inputs"]
        self.assertLessEqual(set(input_schema["required"]), set(request["inputs"]))
        self.assertFalse(set(request["inputs"]) - set(input_schema["properties"]))

        self.assertIn(response["status"], result_schema["properties"]["status"]["enum"])
        data_schema = result_schema["properties"]["data"]
        self.assertLessEqual(set(data_schema["required"]), set(response["data"]))
        self.assertIsInstance(response["data"]["scan_roots"], list)
        for scan_root in response["data"]["scan_roots"]:
            self.assertIsInstance(scan_root, str)
        finding_schema = result_schema["$defs"]["finding"]
        for finding in response["data"]["findings"]:
            self.assertLessEqual(set(finding_schema["required"]), set(finding))
            self.assertFalse(set(finding) - set(finding_schema["properties"]))
            self.assertIn(finding["classification"], finding_schema["properties"]["classification"]["enum"])
            self.assertIn(finding["surface"], finding_schema["properties"]["surface"]["enum"])

        with materialized_installed_cache_oracle() as (_, roots):
            proof = installed_cache_oracle_proof(roots)
        self.assertLessEqual(set(proof_schema["required"]), set(proof))
        self.assertEqual({item["product"] for item in proof["proofs"]}, {"claude", "codex"})
        proof_item_schema = proof_schema["$defs"]["proof"]
        for item in proof["proofs"]:
            self.assertLessEqual(set(proof_item_schema["required"]), set(item))
            self.assertFalse(set(item) - set(proof_item_schema["properties"]))
            self.assertNotEqual(item["installed_root"], item["source_payload_root"])

        allowlist = json.loads((PLUGIN_BASH_CONFINEMENT_FIXTURE_DIR / "allowlist.json").read_text(encoding="utf-8"))
        entry_schema = allowlist_schema["$defs"]["entry"]
        for item in allowlist["entries"]:
            self.assertLessEqual(set(entry_schema["required"]), set(item))
            self.assertFalse(set(item) - set(entry_schema["properties"]))
            self.assertIn("categories", item)
            self.assertNotIn("category", item)

    def test_installed_release_payload_completeness_blocks_seeded_negative_cases(self) -> None:
        for case_id in ["missing-runner-file", "stale-metadata", "extra-file", "path-leak", "transform-mismatch"]:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "payload-gate",
                        "payload-completeness",
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/payload-completeness-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 1)
                self.assert_response(response, "expected_failure")
                self.assertEqual([diag["code"] for diag in stderr_records], ["payload_completeness_blocked"])
                self.assertTrue(response["data"]["gate"]["blocking"])
                self.assertTrue(
                    any(result["status"] == "fail" for result in response["data"]["payload_completeness"])
                )
                self.assert_payload_completeness_contract_subset(response["data"]["payload_completeness"])
                if case_id == "path-leak":
                    failed = [result for result in response["data"]["payload_completeness"] if result["status"] == "fail"]
                    self.assertEqual(len(failed), 1)
                    self.assertEqual(failed[0]["path_leaks"], ["../outside-cache.txt"])
                    self.assertFalse(any(".." in item["path"].split("/") for item in failed[0]["actual_files"]))

        for case_id in ["empty-surfaces", "invalid-surfaces"]:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "payload-gate",
                        "payload-completeness",
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/payload-completeness-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 2)
                self.assert_response(response, "input_error")
                self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_payload_surface_selection"])

    def test_installed_release_payload_completeness_apply_builds_runner_payloads_without_shell(self) -> None:
        from speckit_pro_runner.gates import payloads as payload_gate

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "dist"
            sentinel = output_root / "claude" / "speckit-pro" / "sentinel.txt"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_text("keep", encoding="utf-8")
            completed, response, stderr_records = run_runner(
                gate_request(
                    "payload-gate",
                    "payload-completeness",
                    mode="dry_run",
                    inputs={
                        "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/payload-completeness-cases.json",
                        "case_id": "current-committed-dist",
                        "output_root": output_root.as_posix(),
                    },
                )
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok")
            self.assertEqual(stderr_records, [])
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

        with tempfile.TemporaryDirectory() as tmp:
            output_root = str(Path(tmp) / "dist")
            request = gate_request(
                "payload-gate",
                "payload-completeness",
                mode="apply",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/payload-completeness-cases.json",
                    "case_id": "current-committed-dist",
                    "output_root": output_root,
                },
            )
            completed, response, stderr_records = run_runner(request)
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok")
            self.assertEqual(stderr_records, [])
            for surface in ["claude", "codex"]:
                payload_root = Path(output_root) / surface / "speckit-pro"
                self.assertTrue((payload_root / "speckit_pro_runner" / "__main__.py").is_file())
                self.assertTrue((payload_root / "speckit_pro_runner" / "speckit-pro-runner.manifest.json").is_file())
            for result in response["data"]["payload_completeness"]:
                self.assertEqual(result["status"], "pass")
                paths = {item["path"] for item in result["actual_files"]}
                self.assertIn("speckit_pro_runner/__main__.py", paths)
                self.assertIn("speckit_pro_runner/speckit-pro-runner.sha256", paths)

        with tempfile.TemporaryDirectory() as tmp:
            payload_root = Path(tmp) / "payload"
            for relative in ("scripts/install.sh", "scripts/install.bash", "scripts/install.zsh", "scripts/install.ps1", "scripts/install.bat", "scripts/install.cmd"):
                script = payload_root / relative
                script.parent.mkdir(parents=True, exist_ok=True)
                script.write_text("echo unsafe\n", encoding="utf-8")
            payload_gate.remove_payload_shell_scripts_installed_plugin(payload_root)
            for suffix in (".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd"):
                self.assertFalse([path for path in payload_root.rglob(f"*{suffix}")], suffix)
            extensionless = payload_root / "bin" / "install"
            extensionless.parent.mkdir(parents=True, exist_ok=True)
            extensionless.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            self.assertEqual(payload_gate.payload_script_file_count(payload_root, [{"path": "bin/install"}]), 1)
            suffixful = payload_root / "bin" / "install.zsh"
            suffixful.write_text("#!/usr/bin/env zsh\n", encoding="utf-8")
            self.assertEqual(payload_gate.payload_script_file_count(payload_root, [{"path": "bin/install.zsh"}]), 1)
            result = payload_gate.installed_plugin_payload_result(REPO_ROOT, "claude", payload_root, payload_root, {})
            self.assertEqual(result["script_file_count"], 2)
            self.assertEqual(result["status"], "fail")

    def test_installed_release_payload_completeness_current_dist_passes_after_runner_rebuild(self) -> None:
        response = self.assert_runner_ok(installed_release_fixture_request("payload-completeness"))
        self.assert_no_release_promotion_metadata(
            response,
            "tests/speckit-pro/unit/fixtures/installed-plugin-release/payload-completeness-cases.json",
        )
        self.assertEqual({item["payload_surface"] for item in response["data"]["payload_completeness"]}, {"claude", "codex"})
        by_surface = {item["payload_surface"]: item for item in response["data"]["payload_completeness"]}
        claude_status = next(item for item in by_surface["claude"]["actual_files"] if item["path"] == "skills/speckit-status/SKILL.md")
        codex_status = next(item for item in by_surface["codex"]["actual_files"] if item["path"] == "skills/speckit-status/SKILL.md")
        self.assertEqual(claude_status["source_path"], "speckit-pro/skills/speckit-status/SKILL.md")
        self.assertEqual(codex_status["source_path"], "speckit-pro/codex-skills/speckit-status/SKILL.md")
        for result in response["data"]["payload_completeness"]:
            self.assertEqual(result["status"], "pass")
            self.assertFalse(result["missing_paths"])
            self.assertFalse(result["extra_paths"])
            self.assertFalse(result["mismatched_paths"])
            self.assertFalse(result["path_leaks"])
        self.assert_payload_completeness_contract_subset(response["data"]["payload_completeness"])

    def test_installed_release_payload_completeness_detects_stale_runner_trust_metadata(self) -> None:
        from speckit_pro_runner.gates import payloads as payload_gate

        with tempfile.TemporaryDirectory() as tmp:
            dist_root = Path(tmp) / "dist"
            payload_gate.build_installed_plugin_payloads(REPO_ROOT, dist_root)
            payload_root = dist_root / "claude" / "speckit-pro"
            runner_file = payload_root / "speckit_pro_runner" / "__main__.py"
            runner_file.write_text(runner_file.read_text(encoding="utf-8") + "\n# stale trust metadata test\n", encoding="utf-8")

            mismatches = payload_gate.payload_trust_metadata_mismatches(payload_root)

        self.assertEqual(
            set(mismatches),
            {
                "speckit_pro_runner/speckit-pro-runner.manifest.json",
                "speckit_pro_runner/speckit-pro-runner.sha256",
            },
        )

    def test_installed_release_readiness_registration_and_workflow_are_live(self) -> None:
        request = installed_release_fixture_request("release-readiness")
        self.assertEqual(request["helper_id"], "release-readiness")
        self.assertEqual(request["operation"], "installed-release-readiness")
        self.assertEqual(request["mode"], "read_only")
        runner_request = installed_release_fixture_request("runner-invocation")
        self.assertEqual(runner_request["inputs"]["case_id"], "live-host-runtime-info")
        release_workflow = (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        for request_name in [
            "runner-invocation.json",
            "active-runtime-guard.json",
            "payload-completeness.json",
            "release-readiness.json",
        ]:
            self.assertIn(f"tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/{request_name}", release_workflow)

    def test_installed_release_install_health_repair_reports_safe_and_manual_outcomes(self) -> None:
        cases = installed_release_fixture_cases("install-health-repair")
        self.assertEqual(cases["schema_version"], "2.0")
        self.assertEqual(cases["contract_id"], "installed-plugin-release")
        self.assertLessEqual(
            {
                "ready",
                "trusted-missing",
                "trusted-missing-metadata",
                "trusted-stale",
                "unsafe-unknown",
                "unsafe-extra",
                "unsafe-mismatch",
                "unsafe-trust-root-change",
                "unsafe-out-of-cache",
                "broad-reinstall-rejected",
            },
            {case["case_id"] for case in cases["cases"]},
        )

        completed, response, stderr_records = run_runner(installed_release_fixture_request("install-health-repair"))
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        health = response["data"]["install_health_repair"]
        self.assertEqual(health["status"], "pass")
        self.assertTrue(health["repair_actions"])
        self.assertEqual(health["repair_actions"][0]["action_type"], "autoheal_refresh")
        self.assertTrue(health["repair_actions"][0]["digest_verified"])

        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        self.assertEqual(MUTATION_HELPERS["install-health-repair"].modes, ("read_only",))

        for case_id in [
            "trusted-missing-metadata",
            "unsafe-unknown",
            "unsafe-extra",
            "unsafe-mismatch",
            "unsafe-trust-root-change",
            "unsafe-out-of-cache",
        ]:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "install-health-repair",
                        "install-health-repair",
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/install-health-repair-cases.json",
                            "case_id": case_id,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 0)
                self.assert_response(response, "ok")
                self.assertEqual(stderr_records, [])
                health = response["data"]["install_health_repair"]
                self.assertEqual(health["status"], "manual_remediation_required")
                self.assertEqual(health["repair_actions"][0]["action_type"], "manual_remediation")
                self.assertTrue(health["repair_actions"][0]["manual_steps"])

        completed, response, stderr_records = run_runner(
            gate_request(
                "install-health-repair",
                "install-health-repair",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/installed-plugin-release/install-health-repair-cases.json",
                    "case_id": "broad-reinstall-rejected",
                },
            )
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assertEqual([diag["code"] for diag in stderr_records], ["install_health_repair_blocked"])

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
            (REPO_ROOT / "speckit-pro/.claude-plugin/plugin.json").read_text(encoding="utf-8")
        )["version"]
        expected_sources = {
            "speckit-pro/.claude-plugin/plugin.json",
            "speckit-pro/.codex-plugin/plugin.json",
            ".claude-plugin/marketplace.json",
            ".agents/plugins/marketplace.json",
            ".release-please-manifest.json",
            "speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json",
        }
        self.assertEqual(
            set(version_check["evidence"]),
            {f"{path}={expected_version}" for path in expected_sources},
        )
        self.assertTrue(all("script_file_count" in item for item in readiness["payload_results"]))
        self.assert_release_readiness_contract_subset(readiness)

    def test_installed_release_readiness_blocks_live_version_manifest_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_installed_release_tree(root)
            manifest_path = root / ".release-please-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["speckit-pro"] = "9.9.9"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            response = run_installed_release_readiness(repo_root=root)

        self.assert_response(response, "expected_failure")
        readiness = response["data"]["release_readiness"]
        version_check = next(check for check in readiness["checks"] if check["check_id"] == "version-sync")
        self.assertTrue(version_check["blocking"])
        self.assertIn(".release-please-manifest.json=9.9.9", version_check["evidence"])

    def test_installed_release_readiness_blocks_live_platform_payload_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_installed_release_tree(root)
            manifest_path = root / "dist/codex/speckit-pro/.codex-plugin/plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "9.9.9"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            response = run_installed_release_readiness(repo_root=root)

        self.assert_response(response, "expected_failure")
        readiness = response["data"]["release_readiness"]
        payload_check = next(check for check in readiness["checks"] if check["check_id"] == "payload-completeness")
        self.assertTrue(payload_check["blocking"])
        self.assertFalse(
            any("fixture" in evidence.lower() for check in readiness["checks"] for evidence in check["evidence"])
        )

    def test_run_default_suite_aggregates_success_stdout_stderr_and_exit_behavior(self) -> None:
        request = gate_request(
            "suite-gate",
            "run-default-suite",
            inputs={
                "suite": ["toolchain", "1", "4", "5", "7", "8"],
                "test_commands": {
                    "toolchain": successful_command("toolchain"),
                    "layer-1": successful_command("layer1"),
                    "layer-4": successful_command("layer4"),
                    "layer-5": successful_command("layer5"),
                    "layer-7": successful_command("layer7"),
                    "layer-8": successful_command("layer8"),
                },
            },
        )
        completed, response, stderr_records = run_runner(request)
        self.assertEqual(completed.returncode, 0)
        self.assert_stdout_json(completed)
        self.assert_response(response, "ok")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual(stderr_records, [])
        gate = response["data"]["gate"]
        self.assertEqual(gate["gate_id"], "suite-gate")
        self.assertEqual(gate["operation"], "run-default-suite")
        self.assertEqual(gate["gate_status"], "pass")
        self.assertTrue(gate["promoted"])
        self.assertFalse(gate["blocking"])
        summary = response["data"]["suite"]["summary"]
        self.assertEqual(summary, {"total": 6, "passed": 6, "failed": 0, "skipped": 0})
        results = response["data"]["suite"]["results"]
        self.assertEqual([result["command_id"] for result in results], ["toolchain", "layer-1", "layer-4", "layer-5", "layer-7", "layer-8"])
        for result in results:
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["exit_code"], 0)
            self.assertFalse(result["shell"])
            self.assertIsInstance(result["argv"], list)
            self.assertIn("stdout", result)
            self.assertIn("stderr", result)
            self.assertIn("stdout", result["stdout"]["text"])
            self.assertIn("stderr", result["stderr"]["text"])

    def test_default_suite_fixture_uses_python_authoritative_commands_without_shell_paths(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        request = fixture_request("run-default-suite")
        results = [
            suite_gate.command_spec(suite_gate.suite_item_to_command_id(item), request["inputs"], REPO_ROOT)
            for item in request["inputs"]["suite"]
        ]
        self.assertEqual(
            [result.command_id for result in results],
            ["toolchain", "layer-1", "layer-4", "layer-5", "layer-7", "layer-8"],
        )
        external_layer_argv = {
            "toolchain": [sys.executable, "tests/speckit-pro/check-toolchain.py", "--mode", "tests"],
            "layer-1": [sys.executable, "tests/speckit-pro/run-layer-scripts.py", "--layer", "1"],
            "layer-4": [sys.executable, "tests/speckit-pro/run-layer-scripts.py", "--layer", "4"],
            "layer-5": [sys.executable, "tests/speckit-pro/run-layer-scripts.py", "--layer", "5"],
            "layer-7": [sys.executable, "tests/speckit-pro/run-layer-scripts.py", "--layer", "7"],
            "layer-8": [sys.executable, "tests/speckit-pro/run-layer-scripts.py", "--layer", "8"],
        }
        for result in results:
            argv = list(result.argv)
            if result.command_id in external_layer_argv:
                self.assertEqual(argv, external_layer_argv[result.command_id])
                self.assertFalse(result.internal)
            else:
                self.assertEqual(argv, [sys.executable, "-m", "speckit_pro_runner"])
                self.assertTrue(result.internal)
            self.assertNotIn("bash", " ".join(argv).lower())
            self.assertNotIn("jq", " ".join(argv).lower())
            self.assertFalse(any(arg.endswith(".sh") for arg in argv))

    def test_layer_dispatcher_rejects_invalid_child_summaries(self) -> None:
        dispatcher = load_layer_script_dispatcher()
        test_path = REPO_ROOT / "tests" / "speckit-pro" / "run-layer-scripts.py"
        invalid_children = (
            ("exit-zero-missing-summary", 0, ""),
            ("wrong-label-only", 0, "nested-child: 1/1 passed\n"),
            ("duplicate-owned", 0, "run-layer-scripts: 1/1 passed\nrun-layer-scripts: 1/1 passed\n"),
            ("zero-discovery", 0, "run-layer-scripts: 0/0 passed\n"),
            ("exit-zero-partial", 0, "run-layer-scripts: 1/2 passed\n"),
            ("passed-exceeds-total", 0, "run-layer-scripts: 2/1 passed\n"),
            ("nonzero-all-pass", 1, "run-layer-scripts: 1/1 passed\n"),
        )
        for case_id, exit_code, stdout in invalid_children:
            with self.subTest(case_id=case_id):
                completed = subprocess.CompletedProcess([sys.executable, "child.py"], exit_code, stdout=stdout, stderr="")
                with patch.object(dispatcher.subprocess, "run", return_value=completed):
                    self.assertEqual(dispatcher.run_script_suite("layer", [test_path], REPO_ROOT), 1)

    def test_missing_executable_treats_windows_altsep_paths_as_repo_relative(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        original_altsep = suite_gate.os.altsep
        try:
            suite_gate.os.altsep = "/"
            self.assertFalse(suite_gate.missing_executable("tests/speckit-pro/run-layer-scripts.py", REPO_ROOT))
        finally:
            suite_gate.os.altsep = original_altsep

        dispatcher = load_layer_script_dispatcher()
        layer1_scripts = [self.repo_rel(path) for path in dispatcher.canonical_test_scripts(REPO_ROOT, "1")]
        layer4_scripts = [self.repo_rel(path) for path in dispatcher.canonical_test_scripts(REPO_ROOT, "4")]
        self.assertGreaterEqual(len(layer1_scripts), 20)
        self.assertGreaterEqual(len(layer4_scripts), 17)
        self.assertIn("tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.py", layer1_scripts)
        self.assertIn("tests/speckit-pro/layer1-structural/validate-release-workflow.py", layer1_scripts)
        manifest = json.loads((REPO_ROOT / "tests/speckit-pro/suite-manifest.json").read_text(encoding="utf-8"))
        manifest_layer4 = next(layer for layer in manifest["layers"] if layer["id"] == "4")
        self.assertEqual(layer4_scripts, [script["path"] for script in manifest_layer4["scripts"]])
        self.assertTrue(all(path.endswith(".py") for path in layer4_scripts))

    def test_default_suite_without_explicit_suite_uses_python_authoritative_default(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        requested = suite_gate.requested_suite({})
        self.assertEqual(requested, suite_gate.DEFAULT_SUITE)
        self.assertEqual(
            [suite_gate.suite_item_to_command_id(item) for item in requested],
            ["toolchain", "layer-1", "layer-4", "layer-5"],
        )

    def test_suite_manifest_is_single_source_of_truth_for_roster_and_dispatch(self) -> None:
        # The shipped gate's advertised roster and dispatch kinds equal the
        # suite manifest exactly.
        from speckit_pro_runner.gates import suite as suite_gate

        manifest = json.loads((REPO_ROOT / "tests/speckit-pro/suite-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], "1.0")
        layers = manifest["layers"]

        default_suite = tuple(layer["id"] for layer in layers if layer["default"])
        extended_suite = tuple(layer["id"] for layer in layers if not layer["live_only"])
        allowed = frozenset(layer["id"] for layer in layers if not layer["live_only"] and layer["id"] != "toolchain")
        # (1) The module roster derives solely from the manifest.
        self.assertEqual(suite_gate.DEFAULT_SUITE, default_suite)
        self.assertEqual(suite_gate.EXTENDED_SUITE, extended_suite)
        self.assertEqual(suite_gate.ALLOWED_LAYERS, allowed)
        self.assertIsNone(suite_gate.SUITE_MANIFEST_ERROR)

        loaded = suite_gate.load_suite_manifest(REPO_ROOT)
        self.assertEqual(suite_gate.manifest_default_suite(loaded), default_suite)
        self.assertEqual(suite_gate.manifest_extended_suite(loaded), extended_suite)
        self.assertEqual(suite_gate.manifest_allowed_layers(loaded), allowed)

        # (2) Manifest dispatch kinds match the gate's actual command routing.
        dispatch_by_id = {layer["id"]: layer["dispatch"] for layer in layers}
        for item in extended_suite:
            with self.subTest(layer=item):
                spec = suite_gate.default_command_spec(suite_gate.suite_item_to_command_id(item), {}, REPO_ROOT)
                self.assertNotIsInstance(spec, dict, item)
                if item == "toolchain":
                    self.assertFalse(spec.internal)
                    self.assertIn("check-toolchain.py", " ".join(spec.argv))
                elif dispatch_by_id[item] == "internal-check":
                    self.assertTrue(spec.internal)
                elif dispatch_by_id[item] == "python-module":
                    self.assertFalse(spec.internal)
                    self.assertIn("run-layer-scripts.py", " ".join(spec.argv))
                else:
                    self.fail(f"unexpected deterministic dispatch {dispatch_by_id[item]!r} for layer {item}")

        # (3) Manifest-integrity invariant (a): every scripts[].path resolves.
        for layer in layers:
            for script in layer["scripts"]:
                with self.subTest(path=script["path"]):
                    self.assertEqual(set(script), {"path", "label"})
                    self.assertTrue((REPO_ROOT / script["path"]).is_file(), script["path"])

        # (4) Manifest-integrity invariant (b): transitional Bash dispatch is
        # the only escape hatch permitted until PR 10; the current architecture
        # routes every layer via internal-check or a Python module, so none
        # remain.
        self.assertEqual([layer["id"] for layer in layers if layer["dispatch"] == "shell-legacy-transitional"], [])

    def assert_ported_python_layer(
        self,
        layer_id: str,
        expected_script: dict[str, str],
        summary: str,
    ) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        manifest = json.loads((REPO_ROOT / "tests/speckit-pro/suite-manifest.json").read_text(encoding="utf-8"))
        layer = next(item for item in manifest["layers"] if item["id"] == layer_id)

        self.assertEqual(layer["dispatch"], "python-module")
        self.assertEqual(layer["scripts"], [expected_script])
        spec = suite_gate.default_command_spec(f"layer-{layer_id}", {}, REPO_ROOT)
        self.assertNotIsInstance(spec, dict)
        self.assertFalse(spec.internal)
        self.assertIn("run-layer-scripts.py", " ".join(spec.argv))
        retired_check = f"check_layer{layer_id}"
        self.assertFalse(
            hasattr(suite_gate, retired_check),
            f"native {retired_check} must retire at the Layer-{layer_id} port boundary",
        )

        completed = subprocess.run(
            [sys.executable, "tests/speckit-pro/run-layer-scripts.py", "--layer", layer_id],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            env=runner_env(),
            shell=False,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr + completed.stdout)
        self.assertIn(summary, completed.stdout)
        self.assertIn(f"PASS {expected_script['path']}", completed.stdout)

    def test_layer7_replay_runners_use_ported_python_module_only(self) -> None:
        self.assert_ported_python_layer(
            "7",
            {
                "path": "tests/speckit-pro/layer7-integration/run-all-fixtures.py",
                "label": "run-all-fixtures",
            },
            "layer-7 integration fixtures",
        )

    def test_layer8_parity_runner_uses_ported_python_module_only(self) -> None:
        self.assert_ported_python_layer(
            "8",
            {
                "path": "tests/speckit-pro/layer8-parity/run-parity-fixtures.py",
                "label": "run-parity-fixtures",
            },
            "layer-8 parity fixtures",
        )

    def test_suite_manifest_loader_fails_closed_when_absent_or_malformed(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(suite_gate.SuiteManifestError):
                suite_gate.load_suite_manifest(Path(tmp))

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "tests" / "speckit-pro"
            target.mkdir(parents=True)
            (target / "suite-manifest.json").write_text("{ not valid json", encoding="utf-8")
            with self.assertRaises(suite_gate.SuiteManifestError):
                suite_gate.load_suite_manifest(Path(tmp))

    def test_run_suite_gate_fails_closed_when_manifest_unavailable(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        entry = SimpleNamespace(helper_id="suite-gate")
        request = SimpleNamespace(operation="run-default-suite", request_id="drift-fail-closed", inputs={"repo_root": "."})
        with patch.object(suite_gate, "SUITE_MANIFEST_ERROR", "simulated manifest loss"):
            result = suite_gate.run_suite_gate(entry, request)
        self.assertEqual(result["status"], "missing_prerequisite")
        self.assertEqual([diag["code"] for diag in result["diagnostics"]], ["suite_manifest_unavailable"])

    def test_unknown_gate_operation_rejects_deterministically(self) -> None:
        response = self.assert_input_error_code(
            gate_request("suite-gate", "not-a-gate"),
            "unknown_gate_operation",
        )
        details = response["diagnostics"][0]["details"]
        self.assertEqual(details["helper_id"], "suite-gate")
        self.assertEqual(details["operation"], "not-a-gate")
        self.assertEqual(details["known_operations"], sorted(details["known_operations"]))
        self.assertIn("run-default-suite", details["known_operations"])

    def test_gate_operation_mismatch_and_mode_validation_are_deterministic(self) -> None:
        mismatch = self.assert_input_error_code(
            gate_request("payload-gate", "run-default-suite"),
            "gate_operation_mismatch",
        )
        self.assertEqual(mismatch["diagnostics"][0]["details"]["expected_helper_id"], "suite-gate")

        unsupported = self.assert_input_error_code(
            gate_request("release-readiness", "validate-pr-title", mode="apply"),
            "unsupported_gate_mode",
        )
        self.assertEqual(unsupported["diagnostics"][0]["details"]["supported_modes"], ["read_only"])

    def test_run_layer_expected_failure_preserves_streams_and_exit_mapping(self) -> None:
        request = gate_request(
            "suite-gate",
            "run-layer",
            inputs={
                "layer": "4",
                "test_commands": {
                    "layer-4": failing_command("layer4", exit_code=1),
                },
            },
        )
        completed, response, stderr_records = run_runner(request)
        self.assert_stdout_json(completed)
        self.assert_response(response, "expected_failure")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["gate_expected_failure"])
        self.assertEqual([diag["code"] for diag in stderr_records], ["gate_expected_failure"])
        result = response["data"]["suite"]["results"][0]
        self.assertEqual(result["command_id"], "layer-4")
        self.assertEqual(result["exit_code"], 1)
        self.assertEqual(result["status"], "expected_failure")
        self.assertIn("layer4 stdout", result["stdout"]["text"])
        self.assertIn("layer4 stderr", result["stderr"]["text"])
        self.assertEqual(response["data"]["gate"]["gate_status"], "fail")

    def test_run_layer_missing_dispatcher_reports_missing_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            (Path(tmp) / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
            request = gate_request(
                "suite-gate",
                "run-layer",
                inputs={"layer": "1", "repo_root": tmp},
            )
            completed, response, stderr_records = run_runner(request)
        self.assert_stdout_json(completed)
        self.assert_response(response, "missing_prerequisite")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual([diag["code"] for diag in stderr_records], ["gate_missing_prerequisite"])
        result = response["data"]["suite"]["results"][0]
        self.assertEqual(result["command_id"], "layer-1")
        self.assertEqual(result["status"], "missing_prerequisite")
        self.assertEqual(result["exit_code"], 3)
        self.assertIn("tests/speckit-pro/run-layer-scripts.py", result["stderr"]["text"])

    def test_toolchain_integration_and_parity_suite_dispatch(self) -> None:
        cases = [
            ("run-toolchain-preflight", "toolchain"),
            ("run-integration-suite", "layer-7"),
            ("run-parity-suite", "layer-8"),
        ]
        for operation, command_id in cases:
            with self.subTest(operation=operation):
                request = gate_request(
                    "suite-gate",
                    operation,
                    inputs={"test_commands": {command_id: successful_command(command_id.replace("-", ""))}},
                )
                completed, response, stderr_records = run_runner(request)
                self.assert_stdout_json(completed)
                self.assert_response(response, "ok")
                self.assert_status_exit_mapping(completed, response)
                self.assertEqual(stderr_records, [])
                self.assertEqual(response["data"]["suite"]["results"][0]["command_id"], command_id)

    def test_unsafe_command_specs_are_rejected(self) -> None:
        unsafe_cases = [
            {"layer-1": "python -c 'print(1)'"},
            {"layer-1": {"argv": "python -c 'print(1)'"}},
            {"layer-1": {"argv": python_argv("print(1)"), "shell": True}},
            {"layer-1": {"argv": ["bash", "tests/speckit-pro/run-all.sh", "--layer", "1"]}},
            {"layer-1": {"argv": [sys.executable, "tests/speckit-pro/run-all.sh"]}},
            {"layer-1": {"argv": ["jq", "."]}},
        ]
        for commands in unsafe_cases:
            with self.subTest(commands=commands):
                response = self.assert_input_error_code(
                    gate_request("suite-gate", "run-layer", inputs={"layer": "1", "test_commands": commands}),
                    "unsafe_command_spec",
                )
                self.assertEqual(response["data"]["gate"]["operation"], "run-layer")

    def test_suite_commands_are_pinned_to_the_active_python_interpreter(self) -> None:
        from speckit_pro_runner.gates import suite as suite_gate

        default_spec = suite_gate.default_command_spec("layer-4", {}, REPO_ROOT)
        self.assertNotIsInstance(default_spec, dict)
        self.assertEqual(default_spec.argv[0], sys.executable)

        with tempfile.TemporaryDirectory() as temporary:
            foreign_python = Path(temporary) / ("python.exe" if os.name == "nt" else "python")
            foreign_python.write_bytes(b"")
            foreign_python.chmod(0o755)
            command = suite_gate.CommandSpec("foreign-python", (str(foreign_python), "-c", "print('unsafe')"))
            result = suite_gate.run_command(command, REPO_ROOT)

        self.assertEqual(result["status"], "input_error")
        self.assertEqual(result["exit_code"], 2)
        self.assertIn("active Python interpreter", result["stderr"]["text"])

    def test_gate_modules_reject_unknown_input_fields_before_dispatch(self) -> None:
        cases = (
            ("payload-gate", "build-test-payload-evidence", {"unexpected_input": True}),
            ("release-readiness", "installed-release-readiness", {"unexpected_input": True}),
            ("active-path-guard", "active-path-guard", {"unexpected_input": True}),
            ("suite-gate", "run-layer", {"layer": "unknown", "unexpected_input": True}),
        )
        for helper_id, operation, inputs in cases:
            with self.subTest(operation=operation):
                self.assert_input_error_code(
                    gate_request(helper_id, operation, inputs=inputs),
                    "unsupported_gate_inputs",
                )

    def test_payload_evidence_modes_are_fixture_bound_and_cutover_safe(self) -> None:
        completed, response, stderr_records = run_runner(fixture_request("test-payload-evidence"))
        self.assertEqual(completed.returncode, 0)
        self.assert_stdout_json(completed)
        self.assert_response(response, "ok")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual(stderr_records, [])
        evidence = response["data"]["payload_evidence"]
        self.assertEqual({item["payload_surface"] for item in evidence}, {"claude_test", "codex_test"})
        for item in evidence:
            self.assertEqual(item["mode"], "read_only")
            self.assertRegex(item["file_tree_hash"], r"^[a-f0-9]{64}$")
            self.assertTrue(item["files"])
            self.assertTrue(item["output_root"].startswith("tests/speckit-pro/unit/fixtures/runner-gates/"))

        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as tmp:
            output_root = self.repo_rel(Path(tmp) / "payload-output")
            dry_run_request = gate_request(
                "payload-gate",
                "build-test-payload-evidence",
                mode="dry_run",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/payload-evidence-cases.json",
                    "case_id": "claude-codex-test-payloads",
                    "output_root": output_root,
                },
            )
            completed, response, stderr_records = run_runner(dry_run_request)
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok")
            self.assertEqual(stderr_records, [])
            self.assertFalse((REPO_ROOT / output_root).exists())

            apply_request = dict(dry_run_request)
            apply_request["request_id"] = "test-build-test-payload-evidence-apply"
            apply_request["mode"] = "apply"
            completed, response, stderr_records = run_runner(apply_request)
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok")
            self.assertEqual(stderr_records, [])
            written = sorted(path.name for path in (REPO_ROOT / output_root).glob("*.json"))
            self.assertEqual(written, ["claude-test-payload-evidence.json", "codex-test-payload-evidence.json"])
            for item in response["data"]["payload_evidence"]:
                self.assertEqual(item["mode"], "apply")

    def test_payload_evidence_rejects_stale_generated_payloads(self) -> None:
        stale = gate_request(
            "payload-gate",
            "build-test-payload-evidence",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/payload-evidence-cases.json",
                "case_id": "stale-generated-files",
                "output_root": "tests/speckit-pro/unit/fixtures/runner-gates/generated/payload-evidence",
            },
        )
        completed, response, stderr_records = run_runner(stale)
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assertEqual([diag["code"] for diag in stderr_records], ["stale_generated_payload_evidence"])

    def test_payload_evidence_filename_and_crlf_normalization_are_safe(self) -> None:
        from speckit_pro_runner.gates import payloads as payload_gate

        self.assertEqual(payload_gate.payload_evidence_filename("../bad\\surface_name"), "surface-name-payload-evidence.json")
        self.assertNotIn("/", payload_gate.payload_evidence_filename("nested/path/../surface"))
        self.assertNotIn("..", payload_gate.payload_evidence_filename("nested/path/../surface"))
        self.assertEqual(
            payload_gate.normalized_content("one\ntwo\r\nthree\r", {"installed_files": "from_inventory_crlf"}),
            "one\r\ntwo\r\nthree\r\n",
        )

    def test_install_verification_uses_fake_home_roots_and_command_plans_only(self) -> None:
        response = self.assert_runner_ok(fixture_request("install-verification"))
        install = response["data"]["install_verification"]
        self.assertEqual(install["status"], "complete")
        self.assertTrue(install["fake_home"])
        self.assertTrue(install["stubbed_cli"])
        self.assertGreaterEqual(install["bundled_agent_count"], 1)
        self.assertEqual(install["missing_files"], [])
        self.assertEqual(install["checksum_mismatches"], [])
        self.assertFalse(install["native_uat_claimed"])

        dry_run = gate_request(
            "install-verification",
            "refresh-local-plugin-fixture",
            mode="dry_run",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/install-verification-cases.json",
                "case_id": "safe-repair-plan",
                "fake_home": True,
            },
        )
        response = self.assert_runner_ok(dry_run)
        install = response["data"]["install_verification"]
        self.assertEqual(install["status"], "safe_repair")
        self.assertTrue(install["safe_repairs"])
        for plan in install["command_plans"]:
            self.assert_no_shell_argv(plan["argv"])

        traversal = gate_request(
            "install-verification",
            "verify-install",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/install-verification-cases.json",
                "case_id": "traversal-rejection",
                "fake_home": True,
            },
        )
        self.assert_input_error_code(traversal, "fixture_install_root_refused")

    def test_install_verification_handles_windows_paths_spaces_and_line_endings(self) -> None:
        for case_id in ["windows-style-paths", "line-ending-normalization"]:
            with self.subTest(case_id=case_id):
                completed, response, stderr_records = run_runner(
                    gate_request(
                        "install-verification",
                        "verify-install",
                        inputs={
                            "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/install-verification-cases.json",
                            "case_id": case_id,
                            "fake_home": True,
                        },
                    )
                )
                self.assertEqual(completed.returncode, 0)
                self.assert_response(response, "ok")
                self.assertEqual(stderr_records, [])
                install = response["data"]["install_verification"]
                self.assertEqual(install["status"], "complete")
                self.assertTrue(install["install_root"].startswith("tests/speckit-pro/unit/fixtures/runner-gates/"))

    def test_validate_pr_title_reads_only_the_live_environment(self) -> None:
        request = gate_request(
            "release-readiness",
            "validate-pr-title",
            inputs={"title_env": "TITLE"},
        )
        completed, response, stderr_records = run_runner(
            request,
            extra_env={"TITLE": "fix(release): validate the current title"},
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_response(response, "ok")
        self.assertEqual(stderr_records, [])
        self.assert_no_release_promotion_metadata(response)
        self.assertEqual(response["data"]["pr_title"], "fix(release): validate the current title")

        completed, response, stderr_records = run_runner(
            request,
            extra_env={"TITLE": "invalid title"},
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assert_no_release_promotion_metadata(response)
        self.assertEqual([item["code"] for item in stderr_records], ["release_check_failed"])
        self.assertTrue(response["data"]["release_check"]["blocking"])

    def test_active_path_guard_blocks_active_findings_and_exit_1(self) -> None:
        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "active-path-guard",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/active-path-guard-cases.json",
                    "case_id": "blocking-active-patterns",
                },
            )
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_stdout_json(completed)
        self.assert_response(response, "expected_failure")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["active_path_guard_blocked"])
        self.assertEqual([diag["code"] for diag in stderr_records], ["active_path_guard_blocked"])
        self.assertEqual(response["data"]["gate"]["gate_status"], "fail")
        self.assertTrue(response["data"]["gate"]["blocking"])

        categories = {finding["category"] for finding in response["data"]["findings"]}
        self.assertLessEqual(
            {
                "bash",
                "script_file",
                "jq",
                "git_bash",
                "wsl",
                "powershell_helper",
                "shell_parsing",
                "shell_interpolation",
                "shell_true",
                "os_system",
                "command_string_subprocess",
            },
            categories,
        )
        self.assertEqual(response["data"]["blocking_count"], len(response["data"]["findings"]))
        self.assertEqual(response["data"]["classified_counts"]["blocking_active_gate"], response["data"]["blocking_count"])

    def test_active_path_guard_classifies_nonblocking_findings(self) -> None:
        completed, response, stderr_records = run_runner(
            gate_request(
                "active-path-guard",
                "active-path-guard",
                inputs={
                    "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/active-path-guard-cases.json",
                    "case_id": "nonblocking-classifications",
                },
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assert_stdout_json(completed)
        self.assert_response(response, "ok")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual(stderr_records, [])
        self.assertEqual(response["data"]["blocking_count"], 0)
        self.assertEqual(
            {finding["classification"] for finding in response["data"]["findings"]},
            {
                "archive_provenance",
                "temporary_parity_evidence",
                "consumer_spec_kit_helper",
                "generated_payload_mirror",
                "docs_out_of_scope",
                "ci_dispatch_glue",
                "installed_runtime_cutover_surface",
            },
        )

    def test_classify_shell_finding_blocks_active_gate_candidates(self) -> None:
        completed, response, stderr_records = run_runner(
            fixture_request("classify-shell-finding")
        )
        self.assertEqual(completed.returncode, 1)
        self.assert_stdout_json(completed)
        self.assert_response(response, "expected_failure")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual([diag["code"] for diag in stderr_records], ["active_path_guard_blocked"])
        self.assertGreaterEqual(response["data"]["blocking_count"], 1)
        self.assertEqual(response["data"]["findings"][0]["classification"], "blocking_active_gate")
        self.assertEqual(
            response["data"]["classified_counts"]["blocking_active_gate"],
            response["data"]["blocking_count"],
        )

    def test_workflow_dispatch_glue_is_only_allowed_for_direct_python_gate_dispatch(self) -> None:
        good = gate_request(
            "active-path-guard",
            "active-path-guard",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/active-path-guard-cases.json",
                "case_id": "workflow-dispatch-good",
            },
        )
        response = self.assert_runner_ok(good)
        self.assertEqual(response["data"]["blocking_count"], 0)
        self.assertEqual([finding["classification"] for finding in response["data"]["findings"]], ["ci_dispatch_glue"])

        bad = gate_request(
            "active-path-guard",
            "active-path-guard",
            inputs={
                "case_file": "tests/speckit-pro/unit/fixtures/runner-gates/active-path-guard-cases.json",
                "case_id": "workflow-dispatch-with-plugin-logic",
            },
        )
        completed, response, stderr_records = run_runner(bad)
        self.assertEqual(completed.returncode, 1)
        self.assert_response(response, "expected_failure")
        self.assertEqual([diag["code"] for diag in stderr_records], ["active_path_guard_blocked"])
        self.assertGreater(response["data"]["blocking_count"], 0)
        self.assertTrue(all(finding["classification"] == "blocking_active_gate" for finding in response["data"]["findings"]))

    def test_active_path_guard_request_fixture_scans_current_repo_clean(self) -> None:
        completed, response, stderr_records = run_runner(fixture_request("active-path-guard"))
        self.assertEqual(completed.returncode, 0)
        self.assert_stdout_json(completed)
        self.assert_response(response, "ok")
        self.assert_status_exit_mapping(completed, response)
        self.assertEqual(stderr_records, [])
        self.assertEqual(response["data"]["status"], "ok")
        self.assertEqual(response["data"]["blocking_count"], 0)
        self.assertGreater(sum(response["data"]["classified_counts"].values()), 0)

    def test_gate_implementations_avoid_shell_execution(self) -> None:
        for module in ["payloads.py", "release.py"]:
            with self.subTest(module=module):
                path = PLUGIN_ROOT / "speckit_pro_runner" / "gates" / module
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    if isinstance(node.func, ast.Attribute):
                        self.assertFalse(
                            node.func.attr == "system"
                            and isinstance(node.func.value, ast.Name)
                            and node.func.value.id == "os",
                            f"{module} must not use os.system",
                        )
                        if (
                            node.func.attr in {"run", "Popen", "call", "check_call", "check_output"}
                            and isinstance(node.func.value, ast.Name)
                            and node.func.value.id == "subprocess"
                        ):
                            for keyword in node.keywords:
                                self.assertFalse(
                                    keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True,
                                    f"{module} must not use shell=True",
                                )
                            if node.args:
                                self.assertFalse(
                                    isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str),
                                    f"{module} must not pass a command string to subprocess",
                                )

    def test_suite_implementation_uses_no_shell_true_os_system_or_command_string_subprocess(self) -> None:
        suite_path = PLUGIN_ROOT / "speckit_pro_runner" / "gates" / "suite.py"
        tree = ast.parse(suite_path.read_text(encoding="utf-8"), filename=suite_path.as_posix())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    self.assertFalse(
                        node.func.attr == "system"
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "os",
                        "suite.py must not use os.system",
                    )
                    if (
                        node.func.attr in {"run", "Popen", "call", "check_call", "check_output"}
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "subprocess"
                    ):
                        for keyword in node.keywords:
                            self.assertFalse(
                                keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True,
                                "suite.py must not use shell=True",
                            )
                        if node.args:
                            self.assertFalse(
                                isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str),
                                "suite.py must not pass a command string to subprocess",
                            )

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GateFoundationTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"test-speckit-pro-gates: {passed}/{total} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
