#!/usr/bin/env python3
"""Behavioral tests for the hosted Windows preflight helper."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
HELPER_PATH = REPO_ROOT / "tests" / "speckit-pro" / "run-hosted-windows-preflight.py"
DISPATCH_HELPER_PATH = REPO_ROOT / "tests" / "speckit-pro" / "run-container-preflight.py"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


def load_helper(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


helper = load_helper("run_hosted_windows_preflight", HELPER_PATH)
dispatch_helper = load_helper("run_container_preflight", DISPATCH_HELPER_PATH)
IMMUTABLE_SPEC_KIT_REF = (
    "git+https://github.com/github/spec-kit.git@"
    "b2314680fce898e0a9151b37ad2535d810c93eef"
)


def runner_envelope(
    status: str = "ok",
    *,
    include_metadata: bool = False,
    verification_status: str = "verified",
) -> dict[str, object]:
    exit_codes = {
        "ok": 0,
        "expected_failure": 1,
        "input_error": 2,
        "missing_prerequisite": 3,
        "subprocess_failure": 4,
        "internal_failure": 5,
    }
    data: dict[str, object] = {}
    if include_metadata:
        data = {
            "report": {
                "metadata": {"verification_status": verification_status},
            }
        }
    return {
        "schema_version": "1.0",
        "status": status,
        "exit_code": exit_codes[status],
        "legacy_exit_code": None,
        "diagnostics": [],
        "data": data,
    }


class HostedPreflightScenario:
    def __init__(self) -> None:
        self.specify_version = "0.8.13"
        self.runtime_response: dict[str, object] | str = runner_envelope()
        self.preflight_response: dict[str, object] | str = runner_envelope(
            include_metadata=True
        )
        self.exit_codes: dict[str, int] = {}

    def run_command(
        self,
        name: str,
        command: list[str],
        evidence_dir: Path,
        env: dict[str, str],
        *,
        input_payload: dict[str, object] | None = None,
        stdout_name: str | None = None,
    ) -> int:
        del command, env, input_payload
        output_path = evidence_dir / (stdout_name or f"{name}.stdout.txt")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if name == "pipx-probe":
            output = "1.15.0\n"
        elif name == "specify-version":
            output = f"CLI Version    {self.specify_version}\nPython    3.11.9\n"
        elif name == "runtime-info":
            output = self._response_text(self.runtime_response)
        elif name == "preflight":
            output = self._response_text(self.preflight_response)
        else:
            output = ""
        output_path.write_text(output, encoding="utf-8")
        return_code = self.exit_codes.get(name, 0)
        (evidence_dir / f"{name}.exit-code.txt").write_text(
            f"{return_code}\n", encoding="utf-8"
        )
        return return_code

    @staticmethod
    def _response_text(response: dict[str, object] | str) -> str:
        if isinstance(response, str):
            return response
        return json.dumps(response, separators=(",", ":")) + "\n"


class HostedWindowsPreflightTests(unittest.TestCase):
    def run_scenario(
        self,
        scenario: HostedPreflightScenario,
        *,
        spec_kit_ref: str = IMMUTABLE_SPEC_KIT_REF,
        role: str = "windows-x64",
        platform_name: str = "Windows",
        architecture: str = "AMD64",
        process_architecture: str | None = None,
        native_architecture: str | None = None,
        actual_python_version: str = "3.13.14",
    ) -> tuple[int, dict[str, object], mock.Mock]:
        with tempfile.TemporaryDirectory() as temporary:
            evidence_dir = Path(temporary) / "evidence"
            environment = {}
            if process_architecture is not None:
                environment["PROCESSOR_ARCHITECTURE"] = process_architecture
            if native_architecture is not None:
                environment["PROCESSOR_ARCHITEW6432"] = native_architecture
            args = argparse.Namespace(
                role=role,
                evidence_dir=evidence_dir,
                pipx_version="1.15.0",
                spec_kit_version="v0.8.13",
                spec_kit_ref=spec_kit_ref,
            )
            command_mock = mock.Mock(side_effect=scenario.run_command)
            with (
                mock.patch.object(helper, "_run_command", command_mock),
                mock.patch.object(helper.shutil, "which", return_value="C:/pipx/specify.exe"),
                mock.patch.object(helper.platform, "system", return_value=platform_name),
                mock.patch.object(helper.platform, "machine", return_value=architecture),
                mock.patch.object(
                    helper.platform,
                    "python_version",
                    return_value=actual_python_version,
                ),
                mock.patch.dict(helper.os.environ, environment, clear=True),
            ):
                return_code = helper._run(args)
            summary = json.loads(
                (evidence_dir / "summary.json").read_text(encoding="utf-8")
            )
        return return_code, summary, command_mock

    def test_success_requires_exact_version_and_valid_ok_envelopes(self) -> None:
        return_code, summary, command_mock = self.run_scenario(HostedPreflightScenario())
        self.assertEqual(return_code, 0)
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["specify_version_installed"], "0.8.13")
        self.assertTrue(summary["runtime_info_envelope_valid"])
        self.assertTrue(summary["preflight_envelope_valid"])
        self.assertEqual(summary["runtime_info_status"], "ok")
        self.assertEqual(summary["preflight_status"], "ok")
        self.assertEqual(summary["preflight_metadata_status"], "verified")
        self.assertEqual(summary["platform"], "Windows")
        self.assertEqual(summary["architecture_family"], "x64")
        self.assertEqual(summary["python_version"], "3.13.14")
        specify_call = next(
            call for call in command_mock.call_args_list if call.args[0] == "specify-version"
        )
        self.assertEqual(
            specify_call.args[1],
            [sys.executable, "-c", helper.SPECIFY_VERSION_CODE],
        )
        specify_pythonpath = specify_call.args[3]["PYTHONPATH"].split(os.pathsep)
        self.assertEqual(
            Path(specify_pythonpath[0]).parts[-6:],
            (
                "windows-x64-pipx",
                "home",
                "venvs",
                "specify-cli",
                "Lib",
                "site-packages",
            ),
        )

    def test_non_windows_platform_is_rejected_before_subprocesses(self) -> None:
        return_code, summary, command_mock = self.run_scenario(
            HostedPreflightScenario(),
            platform_name="Linux",
        )
        self.assertEqual(return_code, 1)
        self.assertEqual(summary["status"], "fail")
        self.assertEqual(summary["error"], "host_platform_not_windows")
        command_mock.assert_not_called()

    def test_native_arm64_matches_windows_arm64_role(self) -> None:
        return_code, summary, _ = self.run_scenario(
            HostedPreflightScenario(),
            role="windows-arm64",
            architecture="ARM64",
        )
        self.assertEqual(return_code, 0)
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["architecture_family"], "arm64")
        self.assertEqual(summary["architecture_family_expected"], "arm64")

    def test_emulated_x64_is_rejected_for_windows_arm64_role(self) -> None:
        return_code, summary, command_mock = self.run_scenario(
            HostedPreflightScenario(),
            role="windows-arm64",
            architecture="ARM64",
            process_architecture="AMD64",
            native_architecture="ARM64",
        )
        self.assertEqual(return_code, 1)
        self.assertEqual(summary["status"], "fail")
        self.assertEqual(summary["error"], "role_architecture_mismatch")
        self.assertEqual(summary["architecture"], "AMD64")
        self.assertEqual(summary["architecture_family"], "x64")
        self.assertEqual(summary["architecture_family_expected"], "arm64")
        self.assertTrue(summary["architecture_emulated"])
        self.assertEqual(summary["host_architecture"], "ARM64")
        self.assertEqual(summary["native_architecture"], "ARM64")
        command_mock.assert_not_called()

    def test_native_arm64_is_rejected_for_windows_x64_role(self) -> None:
        return_code, summary, command_mock = self.run_scenario(
            HostedPreflightScenario(),
            architecture="ARM64",
        )
        self.assertEqual(return_code, 1)
        self.assertEqual(summary["status"], "fail")
        self.assertEqual(summary["error"], "role_architecture_mismatch")
        self.assertEqual(summary["architecture_family"], "arm64")
        self.assertEqual(summary["architecture_family_expected"], "x64")
        command_mock.assert_not_called()

    def test_malformed_runner_json_fails_closed(self) -> None:
        scenario = HostedPreflightScenario()
        scenario.runtime_response = "{not-json\n"
        return_code, summary, _ = self.run_scenario(scenario)
        self.assertEqual(return_code, 1)
        self.assertEqual(summary["status"], "fail")
        self.assertFalse(summary["runtime_info_envelope_valid"])
        self.assertEqual(summary["runtime_info_status"], "")

    def test_longer_version_does_not_match_expected_version_by_substring(self) -> None:
        scenario = HostedPreflightScenario()
        scenario.specify_version = "0.8.130"
        return_code, summary, _ = self.run_scenario(scenario)
        self.assertEqual(return_code, 1)
        self.assertEqual(summary["specify_version_installed"], "0.8.130")
        self.assertFalse(summary["specify_version_compatible"])

    def test_mutable_spec_kit_ref_is_rejected_before_subprocesses(self) -> None:
        return_code, summary, command_mock = self.run_scenario(
            HostedPreflightScenario(),
            spec_kit_ref="git+https://github.com/github/spec-kit.git@v0.8.13",
        )
        self.assertEqual(return_code, 1)
        self.assertEqual(summary["error"], "spec_kit_ref_not_immutable")
        command_mock.assert_not_called()

    def test_subprocess_failure_fails_closed(self) -> None:
        scenario = HostedPreflightScenario()
        scenario.exit_codes["runtime-info"] = 4
        return_code, summary, _ = self.run_scenario(scenario)
        self.assertEqual(return_code, 1)
        self.assertEqual(summary["runtime_info_exit"], 4)
        self.assertEqual(summary["status"], "fail")

    def test_specify_version_executes_installed_module_with_active_python(self) -> None:
        command = [sys.executable, "-c", helper.SPECIFY_VERSION_CODE]
        with tempfile.TemporaryDirectory() as temporary:
            evidence_dir = Path(temporary) / "evidence"
            with mock.patch.object(
                helper.subprocess,
                "run",
                return_value=mock.Mock(returncode=0),
            ) as run_mock:
                exit_code = helper._run_command(
                    "specify-version",
                    command,
                    evidence_dir,
                    {"PATH": "C:/pipx"},
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(run_mock.call_args.args[0], command)
        self.assertFalse(run_mock.call_args.kwargs["shell"])

    def test_subprocess_timeout_writes_bounded_fail_closed_evidence(self) -> None:
        command = ["fake-command", "--version"]
        with tempfile.TemporaryDirectory() as temporary:
            evidence_dir = Path(temporary) / "evidence"
            timeout = helper.subprocess.TimeoutExpired(
                command,
                helper.SUBPROCESS_TIMEOUT_SECONDS,
            )
            with mock.patch.object(
                helper.subprocess,
                "run",
                side_effect=timeout,
            ) as run_mock:
                exit_code = helper._run_command(
                    "timed-command",
                    command,
                    evidence_dir,
                    {},
                )

            timeout_evidence = json.loads(
                (evidence_dir / "timed-command.timeout.json").read_text(
                    encoding="utf-8"
                )
            )
            recorded_exit = (evidence_dir / "timed-command.exit-code.txt").read_text(
                encoding="utf-8"
            )
            stderr = (evidence_dir / "timed-command.stderr.txt").read_text(
                encoding="utf-8"
            )

        self.assertEqual(exit_code, helper.SUBPROCESS_TIMEOUT_EXIT_CODE)
        self.assertEqual(recorded_exit, f"{helper.SUBPROCESS_TIMEOUT_EXIT_CODE}\n")
        self.assertEqual(timeout_evidence["status"], "timeout")
        self.assertEqual(timeout_evidence["command_name"], "timed-command")
        self.assertEqual(
            timeout_evidence["timeout_seconds"],
            helper.SUBPROCESS_TIMEOUT_SECONDS,
        )
        self.assertEqual(
            timeout_evidence["exit_code"],
            helper.SUBPROCESS_TIMEOUT_EXIT_CODE,
        )
        self.assertIn("TimeoutExpired", stderr)
        self.assertEqual(
            run_mock.call_args.kwargs["timeout"],
            helper.SUBPROCESS_TIMEOUT_SECONDS,
        )

    def test_pipx_probe_timeout_does_not_fall_back_to_bootstrap(self) -> None:
        scenario = HostedPreflightScenario()
        scenario.exit_codes["pipx-probe"] = helper.SUBPROCESS_TIMEOUT_EXIT_CODE
        return_code, summary, command_mock = self.run_scenario(scenario)
        self.assertEqual(return_code, 1)
        self.assertEqual(summary["status"], "fail")
        self.assertEqual(summary["error"], "subprocess_timeout")
        self.assertEqual(summary["timed_out_command"], "pipx-probe")
        self.assertEqual(command_mock.call_count, 1)

    def test_non_ok_response_status_fails_even_with_zero_process_exit(self) -> None:
        scenario = HostedPreflightScenario()
        scenario.preflight_response = runner_envelope(
            "expected_failure", include_metadata=True
        )
        return_code, summary, _ = self.run_scenario(scenario)
        self.assertEqual(return_code, 1)
        self.assertTrue(summary["preflight_envelope_valid"])
        self.assertEqual(summary["preflight_status"], "expected_failure")
        self.assertEqual(summary["preflight_exit"], 0)

    def test_unverified_preflight_metadata_fails_with_valid_ok_envelope(self) -> None:
        scenario = HostedPreflightScenario()
        scenario.preflight_response = runner_envelope(
            include_metadata=True,
            verification_status="unverified",
        )
        return_code, summary, _ = self.run_scenario(scenario)
        self.assertEqual(return_code, 1)
        self.assertEqual(summary["status"], "fail")
        self.assertTrue(summary["preflight_envelope_valid"])
        self.assertEqual(summary["preflight_status"], "ok")
        self.assertEqual(summary["preflight_metadata_status"], "unverified")

    def test_missing_preflight_metadata_fails_with_valid_ok_envelope(self) -> None:
        scenario = HostedPreflightScenario()
        scenario.preflight_response = runner_envelope()
        return_code, summary, _ = self.run_scenario(scenario)
        self.assertEqual(return_code, 1)
        self.assertEqual(summary["status"], "fail")
        self.assertTrue(summary["preflight_envelope_valid"])
        self.assertEqual(summary["preflight_status"], "ok")
        self.assertEqual(summary["preflight_metadata_status"], "")

    def test_structurally_invalid_response_envelope_fails_closed(self) -> None:
        scenario = HostedPreflightScenario()
        invalid_response = runner_envelope()
        del invalid_response["diagnostics"]
        scenario.runtime_response = invalid_response
        return_code, summary, _ = self.run_scenario(scenario)
        self.assertEqual(return_code, 1)
        self.assertFalse(summary["runtime_info_envelope_valid"])
        self.assertEqual(summary["status"], "fail")


class ContainerPreflightDispatchTests(unittest.TestCase):
    def run_pull_change_detection(
        self,
        diff_output: str,
        *,
        draft: bool = False,
    ) -> tuple[int, dict[str, object], str, list[mock._Call]]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence_dir = root / "evidence"
            output_path = root / "github-output.txt"
            base_sha = "a" * 40
            head_sha = "b" * 40
            merge_base = "c" * 40
            environment = {
                "EVIDENCE_DIR": str(evidence_dir),
                "GITHUB_OUTPUT": str(output_path),
                "EVENT_NAME": "pull_request",
                "PR_DRAFT": str(draft).lower(),
                "BASE_SHA": base_sha,
                "HEAD_SHA": head_sha,
            }
            with (
                mock.patch.dict(os.environ, environment, clear=True),
                mock.patch.object(
                    dispatch_helper.platform,
                    "python_version",
                    return_value=dispatch_helper.HOSTED_PYTHON_VERSION,
                ),
                mock.patch.object(
                    dispatch_helper,
                    "_run_git",
                    side_effect=[f"{merge_base}\n", diff_output],
                ) as git_mock,
            ):
                return_code = dispatch_helper._detect_changes()

            result = json.loads(
                (evidence_dir / "result.json").read_text(encoding="utf-8")
            )
            changed_files = (evidence_dir / "changed-files.txt").read_text(
                encoding="utf-8"
            )
            calls = list(git_mock.call_args_list)
        return return_code, result, changed_files, calls

    def test_manual_change_detection_always_selects_heavy_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output_path = root / "github-output.txt"
            environment = {
                "PREFLIGHT_OPERATION": "detect-changes",
                "EVIDENCE_DIR": str(root / "evidence"),
                "GITHUB_OUTPUT": str(output_path),
                "EVENT_NAME": "workflow_dispatch",
            }
            with (
                mock.patch.dict(os.environ, environment, clear=True),
                mock.patch.object(
                    dispatch_helper.platform,
                    "python_version",
                    return_value=dispatch_helper.HOSTED_PYTHON_VERSION,
                ),
                mock.patch.object(dispatch_helper, "_run_git") as git_mock,
            ):
                return_code = dispatch_helper._detect_changes()

            result = json.loads(
                (root / "evidence" / "result.json").read_text(encoding="utf-8")
            )
            outputs = output_path.read_text(encoding="utf-8")

        self.assertEqual(return_code, 0)
        self.assertEqual(result["run_preflight"], "true")
        self.assertEqual(result["reason"], "manual_dispatch")
        self.assertIn("run_preflight=true\n", outputs)
        self.assertIn("reason=manual_dispatch\n", outputs)
        git_mock.assert_not_called()

    def test_pull_request_change_detection_uses_merge_base_and_internal_prefixes(self) -> None:
        return_code, result, changed_files, calls = self.run_pull_change_detection(
            "docs/readme.md\ntests/speckit-pro/unit/test-example.py\n"
        )

        self.assertEqual(return_code, 0)
        self.assertEqual(result["run_preflight"], "true")
        self.assertEqual(result["reason"], "preflight_surface_changed")
        self.assertIn("tests/speckit-pro/unit/test-example.py", changed_files)
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            calls[0].args[1][0],
            "merge-base",
        )
        self.assertEqual(
            calls[1].args[1][0:3],
            ["diff", "--no-renames", "--name-only"],
        )

    def test_draft_pull_request_defers_heavy_preflight_without_git_diff(self) -> None:
        return_code, result, changed_files, calls = self.run_pull_change_detection(
            "tests/speckit-pro/unit/test-example.py\n",
            draft=True,
        )

        self.assertEqual(return_code, 0)
        self.assertEqual(result["run_preflight"], "false")
        self.assertEqual(result["reason"], "draft_pull_request")
        self.assertEqual(changed_files, "draft_pull_request\n")
        self.assertEqual(calls, [])

    def test_rename_out_of_preflight_surface_still_runs_heavy_jobs(self) -> None:
        return_code, result, changed_files, _ = self.run_pull_change_detection(
            "tests/speckit-pro/unit/test-removed.py\ndocs/test-removed.py\n"
        )
        self.assertEqual(return_code, 0)
        self.assertEqual(result["run_preflight"], "true")
        self.assertEqual(result["reason"], "preflight_surface_changed")
        self.assertIn("tests/speckit-pro/unit/test-removed.py", changed_files)

    def test_deletion_only_on_preflight_surface_still_runs_heavy_jobs(self) -> None:
        return_code, result, changed_files, _ = self.run_pull_change_detection(
            "speckit-pro/speckit_pro_runner/removed.py\n"
        )
        self.assertEqual(return_code, 0)
        self.assertEqual(result["run_preflight"], "true")
        self.assertIn("speckit-pro/speckit_pro_runner/removed.py", changed_files)

    def test_docs_only_change_skips_heavy_jobs(self) -> None:
        return_code, result, changed_files, _ = self.run_pull_change_detection(
            "README.md\ndocs-site/src/content/docs/install/index.md\n"
        )
        self.assertEqual(return_code, 0)
        self.assertEqual(result["run_preflight"], "false")
        self.assertEqual(result["reason"], "unrelated_change")
        self.assertIn("docs-site/src/content/docs/install/index.md", changed_files)

    def test_windows_availability_preserves_defaults_and_authoritative_disables(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output_path = root / "github-output.txt"
            environment = {
                "EVIDENCE_DIR": str(root / "evidence"),
                "GITHUB_OUTPUT": str(output_path),
                "EVENT_NAME": "workflow_dispatch",
                "DISPATCH_X64_ENABLED": "true",
                "DISPATCH_ARM64_ENABLED": "true",
                "REPO_X64_ENABLED": "false",
                "REPO_ARM64_ENABLED": "false",
            }
            with (
                mock.patch.dict(os.environ, environment, clear=True),
                mock.patch.object(
                    dispatch_helper.platform,
                    "python_version",
                    return_value=dispatch_helper.HOSTED_PYTHON_VERSION,
                ),
            ):
                return_code = dispatch_helper._windows_availability()

            x64 = json.loads(
                (root / "evidence" / "x64" / "availability.json").read_text(
                    encoding="utf-8"
                )
            )
            arm64 = json.loads(
                (root / "evidence" / "arm64" / "availability.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(return_code, 0)
        self.assertFalse(x64["enabled"])
        self.assertFalse(arm64["enabled"])
        self.assertEqual(x64["source"], "repository_variable_disable")
        self.assertEqual(arm64["source"], "repository_variable_disable")
        self.assertEqual(x64["hosted_label_status"], "stable")
        self.assertEqual(arm64["hosted_label_status"], "public_preview")

    def test_required_sentinel_truth_table_fails_closed(self) -> None:
        verdict = dispatch_helper._required_sentinel_passes
        self.assertEqual(
            [True, False, False, True, False, False, False],
            [
                verdict("success", "true", "success"),
                verdict("success", "true", "failure"),
                verdict("success", "true", "cancelled"),
                verdict("success", "false", "skipped"),
                verdict("success", "false", "success"),
                verdict("failure", "true", "success"),
                verdict("cancelled", "false", "skipped"),
            ],
        )

    def test_required_sentinel_writes_stable_verdict_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence_dir = Path(temporary) / "evidence"
            environment = {
                "EVIDENCE_DIR": str(evidence_dir),
                "PREFLIGHT_ROLE": "linux-arm64-required",
                "CHANGES_RESULT": "success",
                "RUN_PREFLIGHT": "false",
                "PREFLIGHT_RESULT": "skipped",
            }
            with (
                mock.patch.dict(os.environ, environment, clear=True),
                mock.patch.object(
                    dispatch_helper.platform,
                    "python_version",
                    return_value=dispatch_helper.HOSTED_PYTHON_VERSION,
                ),
            ):
                return_code = dispatch_helper._sentinel()
            result = json.loads(
                (evidence_dir / "result.json").read_text(encoding="utf-8")
            )

        self.assertEqual(return_code, 0)
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["heavy_result"], "skipped")

    def test_linux_dispatch_checks_native_architecture_and_runs_exact_gate_requests(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence_dir = Path(temporary) / "evidence"
            environment = {
                "EVIDENCE_DIR": str(evidence_dir),
                "PREFLIGHT_ROLE": "linux-arm64",
            }
            git_result = SimpleNamespace(
                returncode=0,
                stdout="git version 2.50.1\n",
                stderr="",
            )
            with (
                mock.patch.dict(os.environ, environment, clear=True),
                mock.patch.object(dispatch_helper.platform, "system", return_value="Linux"),
                mock.patch.object(dispatch_helper.platform, "machine", return_value="aarch64"),
                mock.patch.object(
                    dispatch_helper.platform,
                    "python_version",
                    return_value=dispatch_helper.LINUX_PYTHON_VERSION,
                ),
                mock.patch.object(dispatch_helper.shutil, "which", return_value="/usr/bin/git"),
                mock.patch.object(dispatch_helper.subprocess, "run", return_value=git_result),
                mock.patch.object(
                    dispatch_helper,
                    "_run_runner_request",
                    return_value=0,
                ) as runner_mock,
            ):
                return_code = dispatch_helper._linux_gates()

            summary = json.loads(
                (evidence_dir / "summary.json").read_text(encoding="utf-8")
            )

        self.assertEqual(return_code, 0)
        self.assertEqual(summary["architecture_family"], "arm64")
        self.assertEqual(summary["architecture_family_expected"], "arm64")
        self.assertEqual(summary["container_userland"], "Debian Bookworm")
        self.assertEqual(summary["entrypoints"], "success")
        self.assertEqual(runner_mock.call_count, len(dispatch_helper.LINUX_REQUESTS))
        request_names = [call.args[0] for call in runner_mock.call_args_list]
        self.assertEqual(
            request_names,
            [
                "toolchain",
                "default-suite",
                "repository-bash-confinement",
                "installed-plugin-runner-invocation",
                "installed-plugin-active-runtime-guard",
                "installed-plugin-payload-completeness",
                "installed-plugin-release-readiness",
            ],
        )
        self.assertEqual(request_names, [item[0] for item in dispatch_helper.LINUX_REQUESTS])
        self.assertTrue(runner_mock.call_args_list[1].kwargs["skip_toolchain"])
        self.assertTrue(
            all(
                call.args[1].is_file()
                for call in runner_mock.call_args_list
            )
        )

    def test_linux_dispatch_rejects_architecture_mismatch_before_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence_dir = Path(temporary) / "evidence"
            environment = {
                "EVIDENCE_DIR": str(evidence_dir),
                "PREFLIGHT_ROLE": "linux-arm64",
            }
            git_result = SimpleNamespace(returncode=0, stdout="git version 2.50.1\n", stderr="")
            with (
                mock.patch.dict(os.environ, environment, clear=True),
                mock.patch.object(dispatch_helper.platform, "system", return_value="Linux"),
                mock.patch.object(dispatch_helper.platform, "machine", return_value="x86_64"),
                mock.patch.object(
                    dispatch_helper.platform,
                    "python_version",
                    return_value=dispatch_helper.LINUX_PYTHON_VERSION,
                ),
                mock.patch.object(dispatch_helper.shutil, "which", return_value="/usr/bin/git"),
                mock.patch.object(dispatch_helper.subprocess, "run", return_value=git_result),
                mock.patch.object(dispatch_helper, "_run_runner_request") as runner_mock,
            ):
                return_code = dispatch_helper._linux_gates()

        self.assertEqual(return_code, 1)
        runner_mock.assert_not_called()

    def test_runner_request_scopes_safe_directory_to_child_process(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo_root = root / 'repo with "quotes"'
            request_path = root / "request.json"
            evidence_dir = root / "evidence"
            request_path.write_text("{}\n", encoding="utf-8")
            completed = SimpleNamespace(returncode=0)
            environment = {"GIT_CONFIG_GLOBAL": str(root / "parent.config")}
            with (
                mock.patch.dict(os.environ, environment, clear=True),
                mock.patch.object(dispatch_helper, "REPO_ROOT", repo_root),
                mock.patch.object(
                    dispatch_helper.subprocess,
                    "run",
                    return_value=completed,
                ) as run_mock,
            ):
                return_code = dispatch_helper._run_runner_request(
                    "repository-bash-confinement",
                    request_path,
                    evidence_dir,
                    skip_toolchain=False,
                )
                child_env = run_mock.call_args.kwargs["env"]
                git_config_path = Path(child_env["GIT_CONFIG_GLOBAL"])
                git_config_text = git_config_path.read_text(encoding="utf-8")
                parent_git_config = os.environ["GIT_CONFIG_GLOBAL"]

        self.assertEqual(return_code, 0)
        self.assertEqual(
            git_config_path,
            evidence_dir / "git-safe-directory.config",
        )
        self.assertEqual(
            git_config_text,
            "[safe]\n"
            f"\tdirectory = {json.dumps(str(repo_root.resolve()), ensure_ascii=False)}\n",
        )
        self.assertEqual(parent_git_config, str(root / "parent.config"))
        self.assertEqual(run_mock.call_args.kwargs["cwd"], repo_root)
        self.assertFalse(run_mock.call_args.kwargs["shell"])

    def test_windows_interpreter_probes_are_ordered_and_select_active_native_python(self) -> None:
        commands: list[list[str]] = []

        def run_probe(command: list[str], **_kwargs: object) -> SimpleNamespace:
            commands.append(command)
            if command[:2] == ["py", "-V:3"]:
                version = (3, 13, 14)
                process_architecture = "AMD64"
                native_architecture = "ARM64"
            elif command[:2] == ["py", "-3"]:
                version = (3, 10, 14)
                process_architecture = "ARM64"
                native_architecture = "ARM64"
            elif command[0] == "python":
                version = (3, 13, 14)
                process_architecture = "ARM64"
                native_architecture = "ARM64"
            else:
                version = (3, 12, 11)
                process_architecture = "ARM64"
                native_architecture = "ARM64"
            stdout = json.dumps(
                {
                    "major": version[0],
                    "minor": version[1],
                    "micro": version[2],
                    "executable": f"C:/Python/{command[0]}.exe",
                    "machine": "ARM64",
                    "processor_architecture": process_architecture,
                    "processor_architew6432": native_architecture,
                },
                separators=(",", ":"),
            )
            return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

        with tempfile.TemporaryDirectory() as temporary:
            evidence_dir = Path(temporary) / "evidence"
            with (
                mock.patch.object(
                    dispatch_helper.shutil,
                    "which",
                    side_effect=lambda name: f"C:/Windows/{name}.exe",
                ),
                mock.patch.object(
                    dispatch_helper.subprocess,
                    "run",
                    side_effect=run_probe,
                ),
                mock.patch.object(
                    dispatch_helper.sys,
                    "executable",
                    "C:/Python/python.exe",
                ),
            ):
                selected, records = dispatch_helper._probe_interpreters(
                    "windows-arm64",
                    evidence_dir,
                )
            aggregate = json.loads(
                (evidence_dir / "interpreter-probes.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(selected["candidate"], "python")
        self.assertEqual(selected["interpreter"], "C:/Python/python.exe")
        self.assertEqual(
            [record["candidate"] for record in records],
            list(dispatch_helper.INTERPRETER_CANDIDATES),
        )
        self.assertEqual(
            [command[:2] for command in commands],
            [["py", "-V:3"], ["py", "-3"], ["python", "-c"], ["python3", "-c"]],
        )
        self.assertFalse(records[0]["supported"])
        self.assertTrue(records[0]["architecture_emulated"])
        self.assertFalse(records[1]["supported"])
        self.assertTrue(records[2]["selected"])
        self.assertTrue(records[3]["supported"])
        self.assertEqual(aggregate, records)

    def test_windows_smoke_fails_closed_when_no_direct_interpreter_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence_dir = Path(temporary) / "evidence"
            environment = {
                "EVIDENCE_DIR": str(evidence_dir),
                "PREFLIGHT_ROLE": "windows-x64",
                "PIPX_VERSION": "1.15.0",
                "SPEC_KIT_VERSION": "v0.8.13",
                "SPEC_KIT_GIT_REF": IMMUTABLE_SPEC_KIT_REF,
            }
            with (
                mock.patch.dict(os.environ, environment, clear=True),
                mock.patch.object(
                    dispatch_helper.platform,
                    "python_version",
                    return_value=dispatch_helper.HOSTED_PYTHON_VERSION,
                ),
                mock.patch.object(dispatch_helper.shutil, "which", return_value=None),
                mock.patch.object(dispatch_helper.subprocess, "run") as run_mock,
            ):
                return_code = dispatch_helper._windows_smoke()
            summary = json.loads(
                (evidence_dir / "summary.json").read_text(encoding="utf-8")
            )
            probes = json.loads(
                (evidence_dir / "interpreter-probes.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(return_code, 1)
        self.assertEqual(summary["interpreter"], "missing-compatible-python-3.11")
        self.assertEqual(summary["probe_count"], 4)
        self.assertEqual([item["status"] for item in probes], ["missing"] * 4)
        run_mock.assert_not_called()

    def test_windows_smoke_dispatches_selected_direct_interpreter_with_exact_pins(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = {
                "EVIDENCE_DIR": str(Path(temporary) / "evidence"),
                "PREFLIGHT_ROLE": "windows-arm64",
                "PIPX_VERSION": "1.15.0",
                "SPEC_KIT_VERSION": "v0.8.13",
                "SPEC_KIT_GIT_REF": IMMUTABLE_SPEC_KIT_REF,
            }
            completed = SimpleNamespace(returncode=0)
            probe_records = [
                {
                    "candidate": "py -3",
                    "interpreter": "C:/hostedtoolcache/Python/3.14.6/python.exe",
                    "supported": True,
                    "selected": True,
                }
            ]
            with (
                mock.patch.dict(os.environ, environment, clear=True),
                mock.patch.object(
                    dispatch_helper.platform,
                    "python_version",
                    return_value=dispatch_helper.HOSTED_PYTHON_VERSION,
                ),
                mock.patch.object(
                    dispatch_helper,
                    "_probe_interpreters",
                    return_value=(probe_records[0], probe_records),
                ),
                mock.patch.object(
                    dispatch_helper,
                    "_run_selected_windows_helper",
                    return_value=completed,
                ) as dispatch_mock,
            ):
                return_code = dispatch_helper._windows_smoke()

        self.assertEqual(return_code, 0)
        interpreter, arguments, child_env = dispatch_mock.call_args.args
        self.assertEqual(
            interpreter,
            "C:/hostedtoolcache/Python/3.14.6/python.exe",
        )
        self.assertEqual(
            Path(arguments[0]),
            DISPATCH_HELPER_PATH.parent / "run-hosted-windows-preflight.py",
        )
        self.assertIn("--spec-kit-ref", arguments)
        self.assertIn(IMMUTABLE_SPEC_KIT_REF, arguments)
        self.assertEqual(child_env["PREFLIGHT_INTERPRETER_CANDIDATE"], "py -3")

    def test_windows_helper_dispatch_does_not_reresolve_selected_launcher(self) -> None:
        completed = SimpleNamespace(returncode=0)
        interpreter = "C:/hostedtoolcache/Python/3.14.6/python.exe"
        arguments = ["run-hosted-windows-preflight.py", "--role", "windows-x64"]
        child_env = {"PREFLIGHT_INTERPRETER_CANDIDATE": "py -V:3"}
        with mock.patch.object(
            dispatch_helper.subprocess,
            "run",
            return_value=completed,
        ) as run_mock, mock.patch.object(
            dispatch_helper.sys,
            "executable",
            interpreter,
        ):
            result = dispatch_helper._run_selected_windows_helper(
                interpreter, arguments, child_env
            )

        self.assertIs(result, completed)
        self.assertEqual(
            run_mock.call_args.args[0],
            [interpreter, *arguments],
        )
        self.assertEqual(run_mock.call_args.kwargs["env"], child_env)
        self.assertFalse(run_mock.call_args.kwargs["shell"])

    def test_windows_helper_dispatch_rejects_a_different_probed_interpreter(self) -> None:
        with (
            mock.patch.object(
                dispatch_helper.sys,
                "executable",
                "C:/hostedtoolcache/Python/3.13.14/python.exe",
            ),
            mock.patch.object(dispatch_helper.subprocess, "run") as run_mock,
        ):
            with self.assertRaisesRegex(
                dispatch_helper.PreflightError,
                "does not match the active Python",
            ):
                dispatch_helper._run_selected_windows_helper(
                    "C:/hostedtoolcache/Python/3.14.6/python.exe",
                    ["run-hosted-windows-preflight.py"],
                    {},
                )

        run_mock.assert_not_called()

    def test_dispatch_helper_uses_argv_subprocesses_and_current_runner_module(self) -> None:
        content = DISPATCH_HELPER_PATH.read_text(encoding="utf-8")
        compile(content, str(DISPATCH_HELPER_PATH), "exec")
        self.assertIn('[sys.executable, "-m", "speckit_pro_runner"]', content)
        self.assertIn("shell=False", content)
        self.assertNotIn("shell=True", content)
        for candidate in dispatch_helper.INTERPRETER_CANDIDATES:
            self.assertIn(f'"{candidate}"', content)
        for name, request, _ in dispatch_helper.LINUX_REQUESTS:
            self.assertIn(name, content)
            self.assertTrue((REPO_ROOT / request).is_file())


def main() -> int:
    suite = unittest.TestSuite(
        [
            unittest.defaultTestLoader.loadTestsFromTestCase(
                HostedWindowsPreflightTests
            ),
            unittest.defaultTestLoader.loadTestsFromTestCase(
                ContainerPreflightDispatchTests
            ),
        ]
    )
    return run_counted(suite, label="test-hosted-windows-preflight")


if __name__ == "__main__":
    raise SystemExit(main())
