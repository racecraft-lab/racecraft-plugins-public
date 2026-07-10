"""Runtime-info, preflight, helper, and fixture-only gate dispatch primitives."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath
from typing import Any

from . import (
    CONTRACT_VERSION,
    PYTHON_MINIMUM,
    RUNNER_CONTRACT_ID,
    RUNNER_NAME,
    RUNNER_VERSION,
    SELECTED_RUNTIME_NAME,
    SOURCE_CONTEXT,
)
from .envelope import diagnostic, response

CAPTURE_LIMIT_BYTES = 16 * 1024
MANIFEST_NAME = "speckit-pro-runner.manifest.json"
CHECKSUM_NAME = "speckit-pro-runner.sha256"


class MetadataFormatError(ValueError):
    """Raised when runner metadata exists but does not match the expected shape."""


def handle_request(request: Any) -> dict[str, Any]:
    if getattr(request, "helper_id", "runner") != "runner":
        from .gates.registry import dispatch_gate, is_gate_helper_id

        # Gate helper ids are registry-driven so US2 operations stay on the
        # same runner envelope without widening the base runner operation list.
        if is_gate_helper_id(request.helper_id):
            return dispatch_gate(request)

        from .helpers.registry import dispatch_helper

        return dispatch_helper(request)
    if request.operation == "runtime-info":
        return runtime_info(request.request_id, request.inputs)
    if request.operation == "preflight":
        return preflight(request.request_id, request.inputs)
    return response(
        "input_error",
        request_id=request.request_id,
        diagnostics=[diagnostic("invalid_envelope", "unsupported runner operation")],
    )


def runtime_info(request_id: str | None, inputs: dict[str, Any]) -> dict[str, Any]:
    fixture = inputs.get("fixture_category")
    if fixture == "typed_path":
        return handle_typed_path_fixture(request_id, inputs)
    if fixture == "subprocess":
        return handle_subprocess_fixture(request_id, inputs)

    report = build_report(inputs, check_metadata=False)
    return response("ok", request_id=request_id, data={"report": report})


def preflight(request_id: str | None, inputs: dict[str, Any]) -> dict[str, Any]:
    report = build_report(inputs, check_metadata=True)
    diagnostics: list[dict[str, Any]] = []

    python_record = report["prerequisites"]["python"]
    specify_record = report["prerequisites"]["specify"]
    metadata = report["metadata"]

    if python_record["status"] == "too_old":
        diagnostics.append(
            diagnostic(
                "python_too_old",
                "runner requires Python 3.11 or newer",
                details={"version": python_record.get("version")},
                remediation_summary="Run SpecKit Pro with Python 3.11 or newer.",
                remediation_actions=["Set SPECKIT_PRO_PYTHON to a Python 3.11+ executable.", "Retry preflight."],
            )
        )
    if report["paths"]["plugin_root"]["value"] == "":
        diagnostics.append(
            diagnostic(
                "plugin_root_missing",
                "runner could not locate a plugin manifest anchor",
                remediation_summary="Invoke the runner from a valid SpecKit Pro source checkout or installed plugin root.",
                remediation_actions=["Ensure .claude-plugin/plugin.json or .codex-plugin/plugin.json exists above the runner package."],
            )
        )
    if specify_record["status"] == "missing":
        diagnostics.append(
            diagnostic(
                "specify_missing",
                "official SpecKit specify command is missing or undiscoverable",
                remediation_summary="Install or expose the official SpecKit specify command.",
                remediation_actions=["Install SpecKit so specify is on PATH.", "Retry preflight from the same environment."],
            )
        )

    status = metadata["verification_status"]
    metadata_codes = {
        "missing_metadata": "runner_metadata_missing",
        "incomplete_metadata": "runner_metadata_incomplete",
        "mismatch": "runner_metadata_mismatch",
        "not_checked": "runner_metadata_not_checked",
    }
    if status != "verified":
        diagnostics.append(
            diagnostic(
                metadata_codes.get(status, "runner_metadata_not_checked"),
                "runner source metadata is not verified",
                details={"verification_status": status},
                remediation_summary="Refresh runner manifest and checksum metadata before claiming preflight readiness.",
                remediation_actions=["Regenerate SHA-256 records for runner-owned Python files.", "Retry preflight."],
            )
        )

    if diagnostics:
        return response("missing_prerequisite", request_id=request_id, data={"report": report}, diagnostics=diagnostics)
    return response("ok", request_id=request_id, data={"report": report})


def build_report(inputs: dict[str, Any], *, check_metadata: bool) -> dict[str, Any]:
    overrides = inputs.get("test_overrides", {})
    if not isinstance(overrides, dict):
        overrides = {}

    plugin_root = None if overrides.get("plugin_root") == "missing" else detect_plugin_root()
    package_dir = Path(__file__).resolve().parent

    python_version = str(overrides.get("python_version") or platform.python_version())
    python_tuple = parse_version_tuple(python_version)
    python_status = "available" if python_tuple >= PYTHON_MINIMUM else "too_old"

    specify_override = overrides.get("specify")
    if isinstance(specify_override, dict):
        specify_available = bool(specify_override.get("available"))
        specify_path = specify_override.get("path") or "specify"
        specify_version = specify_override.get("version")
    else:
        specify_path = shutil.which("specify")
        specify_available = specify_path is not None
        specify_version = None

    metadata = metadata_report(plugin_root, package_dir, check_metadata=check_metadata, overrides=overrides)

    return {
        "runner_name": RUNNER_NAME,
        "runner_contract_id": RUNNER_CONTRACT_ID,
        "selected_runtime_name": SELECTED_RUNTIME_NAME,
        "contract_version": CONTRACT_VERSION,
        "runner_version": RUNNER_VERSION,
        "python_version": python_version,
        "platform": platform.system().lower() or sys.platform,
        "architecture": platform.machine() or "unknown",
        "source_vs_installed_context": runtime_context(plugin_root),
        "paths": path_report(plugin_root, package_dir),
        "prerequisites": {
            "python": {
                "name": "python",
                "required": True,
                "status": python_status,
                "version": python_version,
                "path": sys.executable,
                "diagnostic_code": None if python_status == "available" else "python_too_old",
            },
            "specify": {
                "name": "specify",
                "required": True,
                "status": "available" if specify_available else "missing",
                "version": specify_version,
                "path": specify_path,
                "diagnostic_code": None if specify_available else "specify_missing",
            },
        },
        "metadata": metadata,
    }


def parse_version_tuple(version: str) -> tuple[int, int, int]:
    parts = []
    for part in version.split(".")[:3]:
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)  # type: ignore[return-value]


def detect_plugin_root() -> Path | None:
    for candidate in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
        if (candidate / ".claude-plugin" / "plugin.json").is_file() or (candidate / ".codex-plugin" / "plugin.json").is_file():
            return candidate
    return None


def runtime_context(plugin_root: Path | None) -> str:
    if plugin_root is not None and installed_payload_root(plugin_root):
        return "installed_payload"
    return SOURCE_CONTEXT


def installed_payload_root(plugin_root: Path) -> bool:
    has_claude_manifest = (plugin_root / ".claude-plugin" / "plugin.json").is_file()
    has_codex_manifest = (plugin_root / ".codex-plugin" / "plugin.json").is_file()
    if has_claude_manifest == has_codex_manifest:
        return False
    source_only_paths = (
        "codex-skills",
    )
    return not any((plugin_root / path).exists() for path in source_only_paths)


def typed_path(kind: str, value: str, display: str | None = None) -> dict[str, str]:
    return {"kind": kind, "value": value, "display": display or value}


def plugin_relative(plugin_root: Path | None, path: Path) -> str:
    if plugin_root is None:
        return ""
    return path.resolve().relative_to(plugin_root.resolve()).as_posix()


def path_report(plugin_root: Path | None, package_dir: Path) -> dict[str, dict[str, str]]:
    manifest = package_dir / MANIFEST_NAME
    checksum = package_dir / CHECKSUM_NAME
    return {
        "plugin_root": typed_path("plugin_relative", "." if plugin_root else "", "speckit-pro/"),
        "runner_package": typed_path("plugin_relative", plugin_relative(plugin_root, package_dir), "speckit_pro_runner/"),
        "manifest_file": typed_path("plugin_relative", plugin_relative(plugin_root, manifest), f"speckit_pro_runner/{MANIFEST_NAME}"),
        "checksum_file": typed_path("plugin_relative", plugin_relative(plugin_root, checksum), f"speckit_pro_runner/{CHECKSUM_NAME}"),
    }


def metadata_report(
    plugin_root: Path | None,
    package_dir: Path,
    *,
    check_metadata: bool,
    overrides: dict[str, Any],
) -> dict[str, Any]:
    manifest_path = package_dir / MANIFEST_NAME
    checksum_path = package_dir / CHECKSUM_NAME
    base = {
        "verification_status": "not_checked",
        "manifest": typed_path("plugin_relative", plugin_relative(plugin_root, manifest_path), f"speckit_pro_runner/{MANIFEST_NAME}"),
        "checksum": typed_path("plugin_relative", plugin_relative(plugin_root, checksum_path), f"speckit_pro_runner/{CHECKSUM_NAME}"),
        "runner_files": [],
    }
    override_status = overrides.get("metadata_status")
    if override_status in {"verified", "mismatch", "missing_metadata", "incomplete_metadata", "not_checked"}:
        base["verification_status"] = override_status
        return base
    if not check_metadata:
        return base
    if plugin_root is None or not manifest_path.is_file() or not checksum_path.is_file():
        base["verification_status"] = "missing_metadata"
        return base

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        checksum_records = parse_checksum_file(checksum_path)
    except (OSError, json.JSONDecodeError, MetadataFormatError):
        base["verification_status"] = "incomplete_metadata"
        return base

    source_files = runner_source_files(package_dir)
    expected_values = {plugin_relative(plugin_root, path): sha256_file(path) for path in source_files}
    manifest_records = manifest.get("runner_files")
    if not isinstance(manifest_records, list):
        base["verification_status"] = "incomplete_metadata"
        return base

    manifest_values: dict[str, str] = {}
    for record in manifest_records:
        if not isinstance(record, dict):
            base["verification_status"] = "incomplete_metadata"
            return base
        path_record = record.get("path")
        digest = record.get("sha256")
        if not isinstance(path_record, dict) or not isinstance(digest, str):
            base["verification_status"] = "incomplete_metadata"
            return base
        value = path_record.get("value")
        if not isinstance(value, str):
            base["verification_status"] = "incomplete_metadata"
            return base
        manifest_values[value] = digest

    if set(manifest_values) != set(expected_values) or set(checksum_records) != set(expected_values):
        base["verification_status"] = "incomplete_metadata"
    elif manifest_values != expected_values or checksum_records != expected_values:
        base["verification_status"] = "mismatch"
    else:
        base["verification_status"] = "verified"

    base["runner_files"] = [
        {"path": typed_path("plugin_relative", path, path), "sha256": digest}
        for path, digest in sorted(expected_values.items())
    ]
    return base


def runner_source_files(package_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in package_dir.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def parse_checksum_file(path: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=1)
        if len(parts) != 2:
            raise MetadataFormatError(f"checksum line {line_number} must contain digest and path")
        digest, rel = parts
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None or not rel.strip():
            raise MetadataFormatError(f"checksum line {line_number} is malformed")
        records[rel.strip()] = digest
    return records


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def handle_typed_path_fixture(request_id: str | None, inputs: dict[str, Any]) -> dict[str, Any]:
    path_obj = inputs.get("path")
    boundary = str(inputs.get("trust_boundary", "."))
    checked = validate_typed_path(path_obj, boundary=boundary)
    if checked["accepted"]:
        return response("ok", request_id=request_id, data={"fixture_result": checked})
    diag = diagnostic(
        "invalid_envelope",
        "typed path fixture was rejected",
        details={"reason": checked["reason"]},
        remediation_summary="Send typed path values that stay inside their declared boundary.",
        remediation_actions=["Use an object with kind, value, and display.", "Avoid traversal outside the declared boundary."],
    )
    return response("input_error", request_id=request_id, data={"fixture_result": checked}, diagnostics=[diag])


def validate_typed_path(path_obj: Any, *, boundary: str) -> dict[str, Any]:
    if not isinstance(path_obj, dict):
        return {"accepted": False, "reason": "path must be a typed object"}
    for field in ("kind", "value", "display"):
        if not isinstance(path_obj.get(field), str):
            return {"accepted": False, "reason": f"missing or invalid {field}"}
    if path_obj["kind"] not in {"plugin_relative", "repo_relative", "absolute"}:
        return {"accepted": False, "reason": "unsupported path kind"}

    raw_value = path_obj["value"]
    normalized = normalize_relative_path(raw_value)
    boundary_path = normalize_relative_path(boundary)
    escapes = path_obj["kind"] != "absolute" and escapes_boundary(normalized, boundary_path)
    if escapes:
        return {"accepted": False, "reason": "path escapes trust boundary", "path": path_obj, "normalized_value": normalized}
    return {"accepted": True, "path": path_obj, "normalized_value": normalized}


def normalize_relative_path(value: str) -> str:
    parts: list[str] = []
    for part in value.replace("\\", "/").split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts and parts[-1] != "..":
                parts.pop()
            else:
                parts.append(part)
        else:
            parts.append(part)
    return "." if not parts else PurePosixPath(*parts).as_posix()


def escapes_boundary(normalized: str, boundary: str) -> bool:
    if normalized == ".." or normalized.startswith("../"):
        return True
    if boundary in {"", "."}:
        return False
    return not (normalized == boundary or normalized.startswith(boundary.rstrip("/") + "/"))


def handle_subprocess_fixture(request_id: str | None, inputs: dict[str, Any]) -> dict[str, Any]:
    spec = inputs.get("subprocess")
    if not isinstance(spec, dict):
        diag = diagnostic("invalid_envelope", "subprocess fixture requires an object")
        return response("input_error", request_id=request_id, diagnostics=[diag])
    result = run_fixture_subprocess(spec)
    code = result.pop("_diagnostic_code")
    if code:
        diag = diagnostic(
            code,
            "fixture subprocess failed",
            details={"exit_code": result.get("exit_code"), "timed_out": result.get("timed_out")},
            remediation_summary="Inspect the fixture subprocess command and expected failure category.",
            remediation_actions=["Keep fixture subprocesses synthetic and bounded.", "Retry after correcting fixture inputs."],
        )
        return response("subprocess_failure", request_id=request_id, data={"subprocess": result}, diagnostics=[diag])
    return response("ok", request_id=request_id, data={"subprocess": result})


def run_fixture_subprocess(spec: dict[str, Any]) -> dict[str, Any]:
    argv = spec.get("argv")
    timeout = spec.get("timeout_seconds")
    stderr_is_failure = bool(spec.get("stderr_is_failure", False))
    if not isinstance(argv, list) or not all(isinstance(arg, str) for arg in argv):
        return invalid_subprocess_result("subprocess_nonzero", argv=[], timeout_seconds=1, stderr_is_failure=stderr_is_failure)
    if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 5:
        return invalid_subprocess_result("subprocess_nonzero", argv=argv, timeout_seconds=1, stderr_is_failure=stderr_is_failure)

    real_argv = fixture_python_argv(argv)
    if real_argv is None:
        return invalid_subprocess_result(
            "subprocess_nonzero",
            argv=argv,
            timeout_seconds=int(timeout),
            stderr_is_failure=stderr_is_failure,
        )
    started = time.monotonic()
    try:
        completed = subprocess.run(
            [sys.executable, *real_argv[1:]],
            capture_output=True,
            shell=False,
            timeout=timeout,
            check=False,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        stdout = output_capture(completed.stdout)
        stderr = output_capture(completed.stderr)
        code = None
        if completed.returncode != 0:
            code = "subprocess_nonzero"
        elif stderr_is_failure and stderr["byte_count"] > 0:
            code = "subprocess_stderr_only_failure"
        return {
            "argv": real_argv,
            "shell": False,
            "exit_code": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": False,
            "timeout_seconds": timeout,
            "duration_ms": duration_ms,
            "stderr_is_failure": stderr_is_failure,
            "_diagnostic_code": code,
        }
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        return {
            "argv": real_argv,
            "shell": False,
            "exit_code": None,
            "stdout": output_capture(exc.stdout or b""),
            "stderr": output_capture(exc.stderr or b""),
            "timed_out": True,
            "timeout_seconds": timeout,
            "duration_ms": duration_ms,
            "stderr_is_failure": stderr_is_failure,
            "_diagnostic_code": "subprocess_timeout",
        }


def fixture_python_argv(argv: list[str]) -> list[str] | None:
    executable = argv[0]
    if executable != "__PYTHON__" and not resolves_to_current_python(executable):
        return None
    return [
        sys.executable,
        *(sys.executable if arg == "__PYTHON__" else arg for arg in argv[1:]),
    ]


def resolves_to_current_python(executable: str) -> bool:
    if executable == sys.executable:
        return True
    resolved = shutil.which(executable)
    candidate = Path(resolved) if resolved is not None else Path(executable)
    try:
        return candidate.samefile(sys.executable)
    except OSError:
        return candidate.resolve(strict=False) == Path(sys.executable).resolve(strict=False)


def invalid_subprocess_result(
    code: str,
    *,
    argv: list[Any],
    timeout_seconds: int,
    stderr_is_failure: bool,
) -> dict[str, Any]:
    return {
        "argv": argv,
        "shell": False,
        "exit_code": 2,
        "stdout": output_capture(b""),
        "stderr": output_capture(b""),
        "timed_out": False,
        "timeout_seconds": timeout_seconds,
        "duration_ms": 0,
        "stderr_is_failure": stderr_is_failure,
        "_diagnostic_code": code,
    }


def output_capture(raw: bytes | str) -> dict[str, Any]:
    if isinstance(raw, str):
        raw_bytes = raw.encode("utf-8", errors="replace")
    else:
        raw_bytes = raw
    truncated = len(raw_bytes) > CAPTURE_LIMIT_BYTES
    bounded = raw_bytes[:CAPTURE_LIMIT_BYTES]
    return {
        "text": bounded.decode("utf-8", errors="replace"),
        "byte_count": len(raw_bytes),
        "limit_bytes": CAPTURE_LIMIT_BYTES,
        "truncated": truncated,
    }
