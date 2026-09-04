#!/usr/bin/env python3
"""Dispatch container preflight roles with durable evidence."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
HOSTED_PYTHON_VERSION = "3.13.14"
LINUX_PYTHON_VERSION = "3.11.15"
LINUX_CONTAINER_IMAGE = (
    "python:3.11.15-bookworm@sha256:"
    "b7ae8a4dcc0ab327e333c5e46a3eaa6c1b0ff585bed77e01cd6de4be1325837e"
)
LINUX_CONTAINER_SOURCE = (
    "https://github.com/docker-library/python/tree/"
    "4d216ad3beb5b697c4049071c82fc375acb8abad/3.11/bookworm"
)
WINDOWS_HELPER = REPO_ROOT / "tests" / "speckit-pro" / "run-hosted-windows-preflight.py"
RUNNER_TIMEOUT_SECONDS = 1800
WINDOWS_TIMEOUT_SECONDS = 3600
WINDOWS_ROLE_ARCHITECTURES = {
    "windows-x64": "amd64",
    "windows-arm64": "arm64",
}
INTERPRETER_CANDIDATES = (
    "py -V:3",
    "py -3",
    "python",
    "python3",
)
INTERPRETER_PROBE_CODE = (
    "import json,os,platform,sys;"
    "print(json.dumps({"
    "'major':sys.version_info.major,"
    "'minor':sys.version_info.minor,"
    "'micro':sys.version_info.micro,"
    "'executable':sys.executable,"
    "'machine':platform.machine(),"
    "'processor_architecture':os.environ.get('PROCESSOR_ARCHITECTURE',''),"
    "'processor_architew6432':os.environ.get('PROCESSOR_ARCHITEW6432','')"
    "},separators=(',',':')))"
)

HEAVY_PATH_PREFIXES = (
    "speckit-pro/speckit_pro_runner/",
    "tests/speckit-pro/",
    ".github/workflows/",
)
LINUX_ROLE_ARCHITECTURES = {
    "linux-amd64": "amd64",
    "linux-arm64": "arm64",
}
LINUX_REQUESTS = (
    (
        "toolchain",
        "tests/speckit-pro/unit/fixtures/runner-gates/requests/run-toolchain-preflight.json",
        False,
    ),
    (
        "default-suite",
        "tests/speckit-pro/unit/fixtures/runner-gates/requests/run-default-suite.json",
        True,
    ),
    (
        "repository-bash-confinement",
        "tests/speckit-pro/unit/fixtures/repository-bash-confinement/requests/repo-bash-confinement.json",
        False,
    ),
    (
        "installed-plugin-runner-invocation",
        "tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/runner-invocation.json",
        False,
    ),
    (
        "installed-plugin-active-runtime-guard",
        "tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/active-runtime-guard.json",
        False,
    ),
    (
        "installed-plugin-payload-completeness",
        "tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/payload-completeness.json",
        False,
    ),
    (
        "installed-plugin-release-readiness",
        "tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/release-readiness.json",
        False,
    ),
)


class PreflightError(RuntimeError):
    """A fail-closed preflight dispatch error."""


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise PreflightError(f"required environment variable is empty: {name}")
    return value


def _evidence_dir() -> Path:
    return Path(_required_env("EVIDENCE_DIR")).resolve()


def _append_outputs(values: dict[str, str]) -> None:
    output_path = Path(_required_env("GITHUB_OUTPUT"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8", newline="\n") as stream:
        for key, value in values.items():
            stream.write(f"{key}={value}\n")


def _require_python_version(expected: str) -> None:
    actual = platform.python_version()
    if actual != expected:
        raise PreflightError(
            f"expected Python {expected}, found {actual} at {sys.executable}"
        )


def _architecture_family(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_")
    if normalized in {"amd64", "x64", "x86_64"}:
        return "amd64"
    if normalized in {"aarch64", "arm64"}:
        return "arm64"
    return ""


def _run_git(
    name: str,
    arguments: list[str],
    evidence_dir: Path,
) -> str:
    command = ["git", *arguments]
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _write_text(
            evidence_dir / f"{name}.stderr.txt",
            f"{type(exc).__name__}: {exc}\n",
        )
        _write_text(evidence_dir / f"{name}.exit-code.txt", "124\n")
        raise PreflightError(f"{name} failed before completion") from exc

    _write_text(evidence_dir / f"{name}.stderr.txt", completed.stderr)
    _write_text(evidence_dir / f"{name}.exit-code.txt", f"{completed.returncode}\n")
    if completed.returncode != 0:
        raise PreflightError(
            f"{name} exited with status {completed.returncode}"
        )
    return completed.stdout


def _detect_changes() -> int:
    _require_python_version(HOSTED_PYTHON_VERSION)
    evidence_dir = _evidence_dir()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    event_name = _required_env("EVENT_NAME")
    merge_base = ""

    if event_name == "workflow_dispatch":
        changed_files = ["workflow_dispatch"]
        run_preflight = True
        reason = "manual_dispatch"
    elif event_name == "pull_request" and os.environ.get("PR_DRAFT", "").strip().lower() == "true":
        changed_files = ["draft_pull_request"]
        run_preflight = False
        reason = "draft_pull_request"
    elif event_name == "pull_request":
        base_sha = _required_env("BASE_SHA")
        head_sha = _required_env("HEAD_SHA")
        merge_base = _run_git(
            "git-merge-base",
            ["merge-base", base_sha, head_sha],
            evidence_dir,
        ).strip()
        if not merge_base:
            raise PreflightError("git merge-base returned an empty revision")
        _write_text(evidence_dir / "merge-base.txt", f"{merge_base}\n")
        changed_files = [
            line
            for line in _run_git(
                "git-diff",
                ["diff", "--no-renames", "--name-only", merge_base, head_sha],
                evidence_dir,
            ).splitlines()
            if line
        ]
        run_preflight = any(
            path.startswith(HEAVY_PATH_PREFIXES) for path in changed_files
        )
        reason = "preflight_surface_changed" if run_preflight else "unrelated_change"
    else:
        raise PreflightError(f"unsupported event: {event_name}")

    _write_text(
        evidence_dir / "changed-files.txt",
        "".join(f"{path}\n" for path in changed_files),
    )
    run_preflight_text = str(run_preflight).lower()
    _append_outputs(
        {
            "run_preflight": run_preflight_text,
            "reason": reason,
        }
    )
    _write_json(
        evidence_dir / "result.json",
        {
            "schema_version": "1.0",
            "role": "change-detection",
            "outcome": "success",
            "run_preflight": run_preflight_text,
            "reason": reason,
            "merge_base": merge_base,
            "python_version": platform.python_version(),
        },
    )
    return 0


def _run_runner_request(
    name: str,
    request_path: Path,
    evidence_dir: Path,
    *,
    skip_toolchain: bool,
) -> int:
    command = [sys.executable, "-m", "speckit_pro_runner"]
    git_config_path = evidence_dir / "git-safe-directory.config"
    _write_text(
        git_config_path,
        "[safe]\n"
        f"\tdirectory = {json.dumps(str(REPO_ROOT.resolve()), ensure_ascii=False)}\n",
    )
    child_env = os.environ.copy()
    child_env.update(
        {
            "GIT_CONFIG_GLOBAL": str(git_config_path),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUTF8": "1",
            "PYTHONPATH": str(REPO_ROOT / "speckit-pro"),
        }
    )
    if skip_toolchain:
        child_env["SPECKIT_SKIP_TOOLCHAIN_CHECK"] = "1"
    else:
        child_env.pop("SPECKIT_SKIP_TOOLCHAIN_CHECK", None)

    stdout_path = evidence_dir / f"{name}.json"
    stderr_path = evidence_dir / f"{name}.stderr.txt"
    try:
        request_body = request_path.read_bytes()
        with stdout_path.open("wb") as stdout_stream, stderr_path.open("wb") as stderr_stream:
            try:
                completed = subprocess.run(
                    command,
                    cwd=REPO_ROOT,
                    env=child_env,
                    input=request_body,
                    stdout=stdout_stream,
                    stderr=stderr_stream,
                    check=False,
                    shell=False,
                    timeout=RUNNER_TIMEOUT_SECONDS,
                )
                return_code = completed.returncode
            except subprocess.TimeoutExpired:
                return_code = 124
                stderr_stream.write(
                    f"TimeoutExpired: exceeded {RUNNER_TIMEOUT_SECONDS} seconds\n".encode(
                        "utf-8"
                    )
                )
    except OSError as exc:
        _write_text(stderr_path, f"{type(exc).__name__}: {exc}\n")
        return_code = 127

    _write_text(evidence_dir / f"{name}.exit-code.txt", f"{return_code}\n")
    return return_code


def _linux_gates() -> int:
    evidence_dir = _evidence_dir()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    role = _required_env("PREFLIGHT_ROLE")
    if role not in LINUX_ROLE_ARCHITECTURES:
        raise PreflightError(f"unsupported Linux role: {role}")

    actual_architecture = platform.machine()
    actual_family = _architecture_family(actual_architecture)
    expected_family = LINUX_ROLE_ARCHITECTURES[role]
    git_path = shutil.which("git")
    git_exit = 127
    git_version = ""
    if git_path:
        try:
            completed = subprocess.run(
                [git_path, "--version"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=30,
            )
            git_exit = completed.returncode
            git_version = completed.stdout.strip()
            _write_text(evidence_dir / "git-version.stderr.txt", completed.stderr)
        except (OSError, subprocess.TimeoutExpired) as exc:
            _write_text(
                evidence_dir / "git-version.stderr.txt",
                f"{type(exc).__name__}: {exc}\n",
            )

    prerequisites_ok = all(
        (
            platform.system() == "Linux",
            platform.python_version() == LINUX_PYTHON_VERSION,
            actual_family == expected_family,
            bool(git_path),
            git_exit == 0,
        )
    )
    _write_json(
        evidence_dir / "prerequisites.json",
        {
            "schema_version": "1.0",
            "role": role,
            "platform": platform.system(),
            "architecture": actual_architecture,
            "architecture_family": actual_family,
            "architecture_family_expected": expected_family,
            "python": sys.executable,
            "python_version": platform.python_version(),
            "python_version_expected": LINUX_PYTHON_VERSION,
            "git": git_path or "",
            "git_version": git_version,
            "container_image": LINUX_CONTAINER_IMAGE,
            "container_source": LINUX_CONTAINER_SOURCE,
            "status": "pass" if prerequisites_ok else "fail",
        },
    )

    entrypoint_results: dict[str, int] = {}
    if prerequisites_ok:
        for name, relative_request, skip_toolchain in LINUX_REQUESTS:
            entrypoint_results[name] = _run_runner_request(
                name,
                REPO_ROOT / relative_request,
                evidence_dir,
                skip_toolchain=skip_toolchain,
            )

    entrypoints_ok = prerequisites_ok and all(
        return_code == 0 for return_code in entrypoint_results.values()
    )
    _write_json(
        evidence_dir / "summary.json",
        {
            "schema_version": "1.0",
            "role": role,
            "architecture": actual_architecture,
            "architecture_family": actual_family,
            "architecture_family_expected": expected_family,
            "container_userland": "Debian Bookworm",
            "python_version": platform.python_version(),
            "prerequisites": "success" if prerequisites_ok else "failure",
            "checkout": "success",
            "entrypoints": "success" if entrypoints_ok else "failure",
            "entrypoint_exit_codes": entrypoint_results,
            "native_installed_uat": False,
        },
    )
    return 0 if entrypoints_ok else 1


def _valid_bool(value: str) -> bool:
    return value in {"true", "false"}


def _windows_availability() -> int:
    _require_python_version(HOSTED_PYTHON_VERSION)
    evidence_dir = _evidence_dir()
    x64_dir = evidence_dir / "x64"
    arm64_dir = evidence_dir / "arm64"
    x64_dir.mkdir(parents=True, exist_ok=True)
    arm64_dir.mkdir(parents=True, exist_ok=True)

    event_name = _required_env("EVENT_NAME")
    dispatch_x64 = os.environ.get("DISPATCH_X64_ENABLED", "").strip().lower()
    dispatch_arm64 = os.environ.get("DISPATCH_ARM64_ENABLED", "").strip().lower()
    repo_x64 = os.environ.get("REPO_X64_ENABLED", "").strip().lower()
    repo_arm64 = os.environ.get("REPO_ARM64_ENABLED", "").strip().lower()

    x64_enabled = "true"
    arm64_enabled = "false"
    x64_source = "stable_label_default"
    arm64_source = "public_preview_default"
    if event_name == "workflow_dispatch":
        x64_enabled = dispatch_x64 if _valid_bool(dispatch_x64) else "true"
        arm64_enabled = dispatch_arm64 if _valid_bool(dispatch_arm64) else "false"
        x64_source = "workflow_dispatch_input"
        arm64_source = "workflow_dispatch_input"
    elif event_name == "pull_request":
        if _valid_bool(repo_x64):
            x64_enabled = repo_x64
            x64_source = "repository_variable"
        if _valid_bool(repo_arm64):
            arm64_enabled = repo_arm64
            arm64_source = "repository_variable"
    else:
        raise PreflightError(f"unsupported event: {event_name}")

    if repo_x64 == "false":
        x64_enabled = "false"
        x64_source = "repository_variable_disable"
    if repo_arm64 == "false":
        arm64_enabled = "false"
        arm64_source = "repository_variable_disable"

    _append_outputs(
        {
            "x64_enabled": x64_enabled,
            "arm64_enabled": arm64_enabled,
        }
    )
    common = {
        "schema_version": "1.0",
        "available": True,
        "availability_kind": "github_hosted_runner_reference",
        "native_installed_uat": False,
        "python_version": platform.python_version(),
    }
    _write_json(
        x64_dir / "availability.json",
        {
            **common,
            "role": "windows-x64",
            "runner_label": "windows-2025",
            "hosted_label_status": "stable",
            "enabled": x64_enabled == "true",
            "source": x64_source,
        },
    )
    _write_json(
        arm64_dir / "availability.json",
        {
            **common,
            "role": "windows-arm64",
            "runner_label": "windows-11-arm",
            "hosted_label_status": "public_preview",
            "enabled": arm64_enabled == "true",
            "source": arm64_source,
        },
    )
    return 0


def _interpreter_slug(candidate: str) -> str:
    return {
        "py -V:3": "py-V-3",
        "py -3": "py-3",
        "python": "python",
        "python3": "python3",
    }[candidate]


def _probe_interpreter(
    candidate: str,
    expected_architecture: str,
    evidence_dir: Path,
) -> dict[str, Any]:
    slug = _interpreter_slug(candidate)
    executable_name = "py" if candidate.startswith("py ") else candidate
    executable_path = shutil.which(executable_name)
    record: dict[str, Any] = {
        "candidate": candidate,
        "command": executable_path or "",
        "exit_code": 127,
        "supported": False,
        "selected": False,
        "status": "missing",
    }
    stdout_path = evidence_dir / f"probe-{slug}.json"
    stderr_path = evidence_dir / f"probe-{slug}.stderr.txt"
    exit_path = evidence_dir / f"probe-{slug}.exit-code.txt"
    if executable_path is None:
        _write_text(stdout_path, "")
        _write_text(stderr_path, f"{executable_name} was not found on PATH\n")
        _write_text(exit_path, "127\n")
        return record

    try:
        if candidate == "py -V:3":
            completed = subprocess.run(
                ["py", "-V:3", "-c", INTERPRETER_PROBE_CODE],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=120,
            )
        elif candidate == "py -3":
            completed = subprocess.run(
                ["py", "-3", "-c", INTERPRETER_PROBE_CODE],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=120,
            )
        elif candidate == "python":
            completed = subprocess.run(
                ["python", "-c", INTERPRETER_PROBE_CODE],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=120,
            )
        elif candidate == "python3":
            completed = subprocess.run(
                ["python3", "-c", INTERPRETER_PROBE_CODE],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=120,
            )
        else:
            raise PreflightError(f"unsupported interpreter candidate: {candidate}")
    except (OSError, subprocess.TimeoutExpired) as exc:
        _write_text(stdout_path, "")
        _write_text(stderr_path, f"{type(exc).__name__}: {exc}\n")
        _write_text(exit_path, "124\n")
        record.update(
            {
                "exit_code": 124,
                "status": "probe_error",
                "error_type": type(exc).__name__,
            }
        )
        return record

    _write_text(stdout_path, completed.stdout)
    _write_text(stderr_path, completed.stderr)
    _write_text(exit_path, f"{completed.returncode}\n")
    record["exit_code"] = completed.returncode
    if completed.returncode != 0:
        record["status"] = "probe_failed"
        return record

    try:
        payload = json.loads(completed.stdout)
    except (TypeError, json.JSONDecodeError):
        record["status"] = "invalid_probe"
        return record
    if not isinstance(payload, dict):
        record["status"] = "invalid_probe"
        return record

    major = payload.get("major")
    minor = payload.get("minor")
    micro = payload.get("micro")
    version_supported = (
        type(major) is int
        and type(minor) is int
        and type(micro) is int
        and (major > 3 or (major == 3 and minor >= 11))
    )
    machine = str(payload.get("machine") or "")
    process_architecture = str(
        payload.get("processor_architecture") or machine
    )
    native_architecture = str(
        payload.get("processor_architew6432") or machine
    )
    process_family = _architecture_family(process_architecture)
    native_family = _architecture_family(native_architecture)
    architecture_emulated = bool(
        process_family and native_family and process_family != native_family
    )
    architecture_supported = all(
        (
            process_family == expected_architecture,
            native_family == expected_architecture,
            not architecture_emulated,
        )
    )
    interpreter = str(payload.get("executable") or "")
    supported = version_supported and architecture_supported and bool(interpreter)
    record.update(
        {
            "status": "supported" if supported else "rejected",
            "supported": supported,
            "version": (
                f"{major}.{minor}.{micro}"
                if all(type(item) is int for item in (major, minor, micro))
                else ""
            ),
            "interpreter": interpreter,
            "architecture": process_architecture,
            "architecture_family": process_family,
            "native_architecture": native_architecture,
            "native_architecture_family": native_family,
            "architecture_family_expected": expected_architecture,
            "architecture_emulated": architecture_emulated,
        }
    )
    return record


def _probe_interpreters(
    role: str,
    evidence_dir: Path,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    expected_architecture = WINDOWS_ROLE_ARCHITECTURES[role]
    records = [
        _probe_interpreter(candidate, expected_architecture, evidence_dir)
        for candidate in INTERPRETER_CANDIDATES
    ]
    selected = next(
        (
            record
            for record in records
            if record["supported"]
            and _same_executable(str(record["interpreter"]), sys.executable)
        ),
        None,
    )
    for record in records:
        record["selected"] = record is selected
    _write_json(evidence_dir / "interpreter-probes.json", records)
    return selected, records


def _same_executable(left: str, right: str) -> bool:
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(
        os.path.abspath(right)
    )


def _run_selected_windows_helper(
    interpreter: str,
    arguments: list[str],
    child_env: dict[str, str],
) -> subprocess.CompletedProcess[Any]:
    if not _same_executable(interpreter, sys.executable):
        raise PreflightError("probed interpreter does not match the active Python")
    return subprocess.run(
        [sys.executable, *arguments],
        cwd=REPO_ROOT,
        env=child_env,
        check=False,
        shell=False,
        timeout=WINDOWS_TIMEOUT_SECONDS,
    )


def _windows_smoke() -> int:
    _require_python_version(HOSTED_PYTHON_VERSION)
    role = _required_env("PREFLIGHT_ROLE")
    if role not in WINDOWS_ROLE_ARCHITECTURES:
        raise PreflightError(f"unsupported Windows role: {role}")
    evidence_dir = _evidence_dir()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    selected_record, probe_records = _probe_interpreters(role, evidence_dir)
    if selected_record is None:
        _write_json(
            evidence_dir / "summary.json",
            {
                "schema_version": "1.0",
                "role": role,
                "available": True,
                "enabled": True,
                "interpreter": "missing-compatible-python-3.11",
                "interpreter_candidates": list(INTERPRETER_CANDIDATES),
                "probe_count": len(probe_records),
                "spec_kit_version_expected": _required_env("SPEC_KIT_VERSION"),
                "spec_kit_git_ref": _required_env("SPEC_KIT_GIT_REF"),
                "status": "fail",
                "native_installed_uat": False,
            },
        )
        return 1

    arguments = [
        str(WINDOWS_HELPER),
        "--role",
        role,
        "--evidence-dir",
        str(evidence_dir),
        "--pipx-version",
        _required_env("PIPX_VERSION"),
        "--spec-kit-version",
        _required_env("SPEC_KIT_VERSION"),
        "--spec-kit-ref",
        _required_env("SPEC_KIT_GIT_REF"),
    ]
    child_env = os.environ.copy()
    selected_candidate = str(selected_record["candidate"])
    selected_interpreter = str(selected_record["interpreter"])
    child_env["PREFLIGHT_INTERPRETER_CANDIDATE"] = selected_candidate
    try:
        completed = _run_selected_windows_helper(
            selected_interpreter,
            arguments,
            child_env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _write_text(
            evidence_dir / "dispatch-error.txt",
            f"{type(exc).__name__}: {exc}\n",
        )
        _write_json(
            evidence_dir / "summary.json",
            {
                "schema_version": "1.0",
                "role": role,
                "status": "fail",
                "error": "windows_helper_dispatch_failed",
                "interpreter_candidate": selected_candidate,
                "interpreter": selected_interpreter,
                "native_installed_uat": False,
            },
        )
        return 1
    return completed.returncode


def _required_sentinel_passes(
    changes_result: str,
    run_preflight: str,
    heavy_result: str,
) -> bool:
    if changes_result != "success":
        return False
    if run_preflight == "true":
        return heavy_result == "success"
    return run_preflight == "false" and heavy_result == "skipped"


def _sentinel() -> int:
    _require_python_version(HOSTED_PYTHON_VERSION)
    evidence_dir = _evidence_dir()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    role = _required_env("PREFLIGHT_ROLE")
    if role not in {"linux-amd64-required", "linux-arm64-required"}:
        raise PreflightError(f"unsupported sentinel role: {role}")
    changes_result = _required_env("CHANGES_RESULT")
    run_preflight = os.environ.get("RUN_PREFLIGHT", "").strip()
    heavy_result = _required_env("PREFLIGHT_RESULT")
    passed = _required_sentinel_passes(
        changes_result,
        run_preflight,
        heavy_result,
    )
    _write_json(
        evidence_dir / "result.json",
        {
            "schema_version": "1.0",
            "role": role,
            "changes_result": changes_result,
            "run_preflight": run_preflight,
            "heavy_result": heavy_result,
            "verdict": "pass" if passed else "fail",
            "python_version": platform.python_version(),
            "native_installed_uat": False,
        },
    )
    return 0 if passed else 1


OPERATIONS: dict[str, Callable[[], int]] = {
    "detect-changes": _detect_changes,
    "linux-gates": _linux_gates,
    "windows-availability": _windows_availability,
    "windows-smoke": _windows_smoke,
    "sentinel": _sentinel,
}


def _write_dispatch_failure(operation: str, exc: Exception) -> None:
    raw_evidence_dir = os.environ.get("EVIDENCE_DIR", "").strip()
    if not raw_evidence_dir:
        return
    evidence_dir = Path(raw_evidence_dir).resolve()
    payload = {
        "schema_version": "1.0",
        "operation": operation,
        "status": "fail",
        "error": "container_preflight_dispatch_failed",
        "error_type": type(exc).__name__,
        "message": str(exc),
        "native_installed_uat": False,
    }
    if operation == "windows-availability":
        for architecture in ("x64", "arm64"):
            _write_json(evidence_dir / architecture / "dispatch-error.json", payload)
    else:
        _write_json(evidence_dir / "dispatch-error.json", payload)


def main() -> int:
    operation = os.environ.get("PREFLIGHT_OPERATION", "").strip()
    try:
        handler = OPERATIONS.get(operation)
        if handler is None:
            raise PreflightError(f"unsupported operation: {operation or '<empty>'}")
        return handler()
    except Exception as exc:  # pragma: no cover - hosted fail-safe
        _write_dispatch_failure(operation, exc)
        print(f"container preflight {operation or '<empty>'} failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
