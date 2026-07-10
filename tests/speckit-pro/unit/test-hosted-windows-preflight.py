#!/usr/bin/env python3
"""Behavioral tests for the hosted Windows preflight helper."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
HELPER_PATH = REPO_ROOT / "tests" / "speckit-pro" / "run-hosted-windows-preflight.py"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


def load_helper():
    spec = importlib.util.spec_from_file_location("run_hosted_windows_preflight", HELPER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


helper = load_helper()
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
                mock.patch.dict(helper.os.environ, environment, clear=True),
            ):
                return_code = helper._run(args)
            summary = json.loads(
                (evidence_dir / "summary.json").read_text(encoding="utf-8")
            )
        return return_code, summary, command_mock

    def test_success_requires_exact_version_and_valid_ok_envelopes(self) -> None:
        return_code, summary, _ = self.run_scenario(HostedPreflightScenario())
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


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        HostedWindowsPreflightTests
    )
    return run_counted(suite, label="test-hosted-windows-preflight")


if __name__ == "__main__":
    raise SystemExit(main())
