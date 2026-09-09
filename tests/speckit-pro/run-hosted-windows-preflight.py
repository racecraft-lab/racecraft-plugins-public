#!/usr/bin/env python3
"""Run the hosted Windows Spec Kit and runner preflight with durable evidence."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
IMMUTABLE_SPEC_KIT_REF_RE = re.compile(
    r"git\+https://github\.com/github/spec-kit\.git@[0-9a-f]{40}"
)
NORMALIZED_VERSION_PATTERN = r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?"
EXPECTED_VERSION_RE = re.compile(rf"v?(?P<version>{NORMALIZED_VERSION_PATTERN})")
SPECIFY_CLI_VERSION_RE = re.compile(
    rf"\bCLI\s+Version\s+v?(?P<version>{NORMALIZED_VERSION_PATTERN})(?![0-9A-Za-z.-])"
)
RESPONSE_STATUS_EXIT_CODES = {
    "ok": 0,
    "expected_failure": 1,
    "input_error": 2,
    "missing_prerequisite": 3,
    "subprocess_failure": 4,
    "internal_failure": 5,
}
RESPONSE_REQUIRED_FIELDS = {
    "schema_version",
    "status",
    "exit_code",
    "legacy_exit_code",
    "diagnostics",
    "data",
}
ROLE_ARCHITECTURE_FAMILIES = {
    "windows-x64": "x64",
    "windows-arm64": "arm64",
}
SUBPROCESS_TIMEOUT_SECONDS = 300
SUBPROCESS_TIMEOUT_EXIT_CODE = 124
SPECIFY_VERSION_CODE = (
    "import sys; from specify_cli import main; "
    "sys.argv = ['specify', 'version']; raise SystemExit(main())"
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def _run_command(
    name: str,
    command: list[str],
    evidence_dir: Path,
    env: dict[str, str],
    *,
    input_payload: dict[str, Any] | None = None,
    stdout_name: str | None = None,
) -> int:
    stdout_path = evidence_dir / (stdout_name or f"{name}.stdout.txt")
    stderr_path = evidence_dir / f"{name}.stderr.txt"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    encoded_input = None
    if input_payload is not None:
        encoded_input = (json.dumps(input_payload, separators=(",", ":")) + "\n").encode("utf-8")

    try:
        with stdout_path.open("wb") as stdout_stream, stderr_path.open("wb") as stderr_stream:
            try:
                completed = subprocess.run(
                    [sys.executable, *command[1:]],
                    cwd=REPO_ROOT,
                    env=env,
                    input=encoded_input,
                    stdout=stdout_stream,
                    stderr=stderr_stream,
                    check=False,
                    shell=False,
                    timeout=SUBPROCESS_TIMEOUT_SECONDS,
                )
                return_code = completed.returncode
            except subprocess.TimeoutExpired:
                return_code = SUBPROCESS_TIMEOUT_EXIT_CODE
                stderr_stream.write(
                    (
                        "TimeoutExpired: command exceeded "
                        f"{SUBPROCESS_TIMEOUT_SECONDS} seconds\n"
                    ).encode("utf-8")
                )
                _write_json(
                    evidence_dir / f"{name}.timeout.json",
                    {
                        "schema_version": "1.0",
                        "status": "timeout",
                        "command_name": name,
                        "timeout_seconds": SUBPROCESS_TIMEOUT_SECONDS,
                        "exit_code": SUBPROCESS_TIMEOUT_EXIT_CODE,
                    },
                )
    except OSError as exc:
        stderr_path.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        return_code = 127

    (evidence_dir / f"{name}.exit-code.txt").write_text(
        f"{return_code}\n", encoding="utf-8"
    )
    return return_code


def _normalized_expected_version(value: str) -> str:
    match = EXPECTED_VERSION_RE.fullmatch(value.strip())
    return match.group("version") if match is not None else ""


def _installed_spec_kit_version(output: str) -> str:
    match = SPECIFY_CLI_VERSION_RE.search(output)
    return match.group("version") if match is not None else ""


def _architecture_family(machine: str) -> str:
    normalized = machine.strip().lower().replace("-", "_")
    if normalized in {"amd64", "x64", "x86_64"}:
        return "x64"
    if normalized in {"aarch64", "arm64"}:
        return "arm64"
    return ""


def _architecture_details() -> tuple[str, str, str, bool]:
    host_architecture = platform.machine()
    process_architecture = (
        os.environ.get("PROCESSOR_ARCHITECTURE", "").strip() or host_architecture
    )
    native_architecture = (
        os.environ.get("PROCESSOR_ARCHITEW6432", "").strip() or host_architecture
    )
    process_family = _architecture_family(process_architecture)
    native_family = _architecture_family(native_architecture)
    emulated = bool(
        process_family and native_family and process_family != native_family
    )
    return host_architecture, process_architecture, native_architecture, emulated


def _response_details(path: Path) -> tuple[bool, str, list[str], str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False, "", [], ""
    if not isinstance(payload, dict) or not RESPONSE_REQUIRED_FIELDS.issubset(payload):
        return False, "", [], ""

    status = payload.get("status")
    exit_code = payload.get("exit_code")
    diagnostics = payload.get("diagnostics")
    data = payload.get("data")
    legacy_exit_code = payload.get("legacy_exit_code")
    envelope_valid = all(
        (
            payload.get("schema_version") == "1.0",
            isinstance(status, str) and status in RESPONSE_STATUS_EXIT_CODES,
            type(exit_code) is int,
            isinstance(status, str)
            and status in RESPONSE_STATUS_EXIT_CODES
            and exit_code == RESPONSE_STATUS_EXIT_CODES[status],
            legacy_exit_code is None or type(legacy_exit_code) is int,
            isinstance(diagnostics, list),
            isinstance(data, dict),
        )
    )
    if not envelope_valid:
        return False, "", [], ""

    diagnostic_codes = []
    for diagnostic in diagnostics:
        if not isinstance(diagnostic, dict):
            return False, "", [], ""
        if isinstance(diagnostic.get("code"), str):
            diagnostic_codes.append(diagnostic["code"])

    verification_status = ""
    report = data.get("report")
    if isinstance(report, dict):
        metadata = report.get("metadata")
        if isinstance(metadata, dict) and isinstance(metadata.get("verification_status"), str):
            verification_status = metadata["verification_status"]

    return True, status, diagnostic_codes, verification_status


def _finish(evidence_dir: Path, summary: dict[str, Any], status: str) -> int:
    summary["status"] = status
    _write_json(evidence_dir / "summary.json", summary)
    return 0 if status == "pass" else 1


def _run(args: argparse.Namespace) -> int:
    evidence_dir = args.evidence_dir.resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    host_platform = platform.system()
    (
        host_architecture,
        process_architecture,
        native_architecture,
        architecture_emulated,
    ) = _architecture_details()
    architecture_family = _architecture_family(process_architecture)
    expected_architecture_family = ROLE_ARCHITECTURE_FAMILIES[args.role]
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "role": args.role,
        "available": True,
        "enabled": True,
        "checkout": "success",
        "interpreter_candidate": os.environ.get("PREFLIGHT_INTERPRETER_CANDIDATE", ""),
        "interpreter": sys.executable,
        "python_version": platform.python_version(),
        "platform": host_platform,
        "architecture": process_architecture,
        "architecture_family": architecture_family,
        "architecture_family_expected": expected_architecture_family,
        "architecture_emulated": architecture_emulated,
        "host_architecture": host_architecture,
        "native_architecture": native_architecture,
        "pipx_version_expected": args.pipx_version,
        "spec_kit_version_expected": args.spec_kit_version,
        "spec_kit_git_ref": args.spec_kit_ref,
        "native_installed_uat": False,
    }

    if sys.version_info < (3, 11):
        summary["error"] = "python_3_11_required"
        return _finish(evidence_dir, summary, "fail")
    if host_platform != "Windows":
        summary["error"] = "host_platform_not_windows"
        return _finish(evidence_dir, summary, "fail")
    if architecture_family != expected_architecture_family:
        summary["error"] = "role_architecture_mismatch"
        return _finish(evidence_dir, summary, "fail")
    if IMMUTABLE_SPEC_KIT_REF_RE.fullmatch(args.spec_kit_ref) is None:
        summary["error"] = "spec_kit_ref_not_immutable"
        return _finish(evidence_dir, summary, "fail")

    child_env = os.environ.copy()
    child_env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUTF8": "1",
            "PYTHONPATH": str(REPO_ROOT / "speckit-pro"),
        }
    )

    pipx_root = evidence_dir.parent / f"{args.role}-pipx"
    pipx_bin_dir = pipx_root / "bin"
    child_env.update(
        {
            "PIPX_HOME": str(pipx_root / "home"),
            "PIPX_BIN_DIR": str(pipx_bin_dir),
            "PIPX_MAN_DIR": str(pipx_root / "man"),
            "PIPX_DEFAULT_PYTHON": sys.executable,
            "PATH": os.pathsep.join([str(pipx_bin_dir), child_env.get("PATH", "")]),
        }
    )
    pipx_bin_dir.mkdir(parents=True, exist_ok=True)

    pipx_probe_exit = _run_command(
        "pipx-probe",
        [sys.executable, "-m", "pipx", "--version"],
        evidence_dir,
        child_env,
    )
    pipx_probe_version = _read_text(evidence_dir / "pipx-probe.stdout.txt")
    summary.update(
        {
            "pipx_probe_exit": pipx_probe_exit,
            "pipx_probe_version": pipx_probe_version,
        }
    )

    if pipx_probe_exit == SUBPROCESS_TIMEOUT_EXIT_CODE:
        summary["error"] = "subprocess_timeout"
        summary["timed_out_command"] = "pipx-probe"
        return _finish(evidence_dir, summary, "fail")

    if pipx_probe_exit != 0 or pipx_probe_version != args.pipx_version:
        pipx_bootstrap_exit = _run_command(
            "pipx-bootstrap",
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                "--user",
                f"pipx=={args.pipx_version}",
            ],
            evidence_dir,
            child_env,
        )
        summary["pipx_bootstrap_exit"] = pipx_bootstrap_exit
        if pipx_bootstrap_exit != 0:
            return _finish(evidence_dir, summary, "fail")

        pipx_verify_exit = _run_command(
            "pipx-verify",
            [sys.executable, "-m", "pipx", "--version"],
            evidence_dir,
            child_env,
        )
        pipx_effective_version = _read_text(evidence_dir / "pipx-verify.stdout.txt")
        summary.update(
            {
                "pipx_verify_exit": pipx_verify_exit,
                "pipx_effective_version": pipx_effective_version,
            }
        )
        if pipx_verify_exit != 0 or pipx_effective_version != args.pipx_version:
            return _finish(evidence_dir, summary, "fail")
    else:
        summary["pipx_effective_version"] = pipx_probe_version

    spec_kit_install_exit = _run_command(
        "spec-kit-install",
        [
            sys.executable,
            "-m",
            "pipx",
            "install",
            "--force",
            "--python",
            sys.executable,
            args.spec_kit_ref,
        ],
        evidence_dir,
        child_env,
    )
    summary["spec_kit_install_exit"] = spec_kit_install_exit
    if spec_kit_install_exit != 0:
        return _finish(evidence_dir, summary, "fail")

    specify_command = shutil.which("specify", path=child_env["PATH"])
    summary["specify_command"] = specify_command or ""
    if specify_command is None:
        summary["error"] = "specify_command_missing"
        return _finish(evidence_dir, summary, "fail")

    github_path = os.environ.get("GITHUB_PATH")
    if github_path:
        with Path(github_path).open("a", encoding="utf-8", newline="\n") as path_stream:
            path_stream.write(f"{pipx_bin_dir}\n")

    specify_site_packages = (
        pipx_root / "home" / "venvs" / "specify-cli" / "Lib" / "site-packages"
    )
    specify_env = child_env.copy()
    specify_env["PYTHONPATH"] = os.pathsep.join(
        [str(specify_site_packages), child_env["PYTHONPATH"]]
    )
    summary["specify_site_packages"] = str(specify_site_packages)

    specify_version_exit = _run_command(
        "specify-version",
        [sys.executable, "-c", SPECIFY_VERSION_CODE],
        evidence_dir,
        specify_env,
        stdout_name="specify-version.txt",
    )
    specify_version_output = _read_text(evidence_dir / "specify-version.txt")
    expected_numeric_version = _normalized_expected_version(args.spec_kit_version)
    installed_spec_kit_version = _installed_spec_kit_version(specify_version_output)
    specify_version_compatible = (
        bool(expected_numeric_version)
        and installed_spec_kit_version == expected_numeric_version
    )
    summary.update(
        {
            "specify_version_exit": specify_version_exit,
            "specify_version_installed": installed_spec_kit_version,
            "specify_version_compatible": specify_version_compatible,
        }
    )

    runner_command = [sys.executable, "-m", "speckit_pro_runner"]
    runtime_info_exit = _run_command(
        "runtime-info",
        runner_command,
        evidence_dir,
        child_env,
        input_payload={
            "schema_version": "1.0",
            "request_id": f"hosted-windows-{args.role}-runtime-info",
            "helper_id": "runner",
            "operation": "runtime-info",
            "mode": "read_only",
            "inputs": {},
        },
        stdout_name="runtime-info.json",
    )
    preflight_exit = _run_command(
        "preflight",
        runner_command,
        evidence_dir,
        child_env,
        input_payload={
            "schema_version": "1.0",
            "request_id": f"hosted-windows-{args.role}-preflight",
            "helper_id": "runner",
            "operation": "preflight",
            "mode": "read_only",
            "inputs": {},
        },
        stdout_name="preflight.json",
    )

    runtime_envelope_valid, runtime_status, runtime_diagnostics, _ = _response_details(
        evidence_dir / "runtime-info.json"
    )
    (
        preflight_envelope_valid,
        preflight_status,
        preflight_diagnostics,
        preflight_metadata_status,
    ) = _response_details(evidence_dir / "preflight.json")
    summary.update(
        {
            "runtime_info_exit": runtime_info_exit,
            "runtime_info_envelope_valid": runtime_envelope_valid,
            "runtime_info_status": runtime_status,
            "runtime_info_diagnostics": runtime_diagnostics,
            "preflight_exit": preflight_exit,
            "preflight_envelope_valid": preflight_envelope_valid,
            "preflight_status": preflight_status,
            "preflight_diagnostics": preflight_diagnostics,
            "preflight_metadata_status": preflight_metadata_status,
        }
    )

    if runtime_diagnostics:
        print(f"runtime-info diagnostics: {', '.join(runtime_diagnostics)}")
    if preflight_diagnostics:
        print(f"preflight diagnostics: {', '.join(preflight_diagnostics)}")
    if "runner_metadata_mismatch" in preflight_diagnostics:
        print(
            "::warning title=Runner metadata refresh required::Refresh the parent-owned "
            "runner manifest and checksum generation before re-running hosted preflight."
        )

    passed = all(
        (
            specify_version_exit == 0,
            specify_version_compatible,
            runtime_info_exit == 0,
            runtime_envelope_valid,
            runtime_status == "ok",
            preflight_exit == 0,
            preflight_envelope_valid,
            preflight_status == "ok",
            preflight_metadata_status == "verified",
        )
    )
    return _finish(evidence_dir, summary, "pass" if passed else "fail")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=("windows-x64", "windows-arm64"), required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--pipx-version", required=True)
    parser.add_argument("--spec-kit-version", required=True)
    parser.add_argument("--spec-kit-ref", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return _run(args)
    except Exception as exc:  # pragma: no cover - hosted fail-safe
        args.evidence_dir.mkdir(parents=True, exist_ok=True)
        (args.evidence_dir / "helper-error.txt").write_text(
            f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
        )
        _write_json(
            args.evidence_dir / "summary.json",
            {
                "schema_version": "1.0",
                "role": args.role,
                "available": True,
                "enabled": True,
                "checkout": "success",
                "spec_kit_version_expected": args.spec_kit_version,
                "spec_kit_git_ref": args.spec_kit_ref,
                "status": "fail",
                "error": "hosted_preflight_helper_failed",
                "error_type": type(exc).__name__,
                "native_installed_uat": False,
            },
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
