"""Runtime-info, preflight, and helper dispatch primitives."""

from __future__ import annotations

import json
import platform
import re
import shutil
import sys
from pathlib import Path
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
from .path_utils import sha256_file

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
    retired_inputs = sorted({"fixture_category", "test_overrides"} & request.inputs.keys())
    if retired_inputs:
        return response(
            "input_error",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "invalid_envelope",
                    "runner inputs contain retired test-only fields",
                    details={"unexpected_inputs": retired_inputs},
                    remediation_summary="Send only runtime context needed by the selected runner operation.",
                    remediation_actions=["Remove fixture_category and test_overrides from runner inputs.", "Retry the request."],
                )
            ],
        )
    if request.operation == "runtime-info":
        return runtime_info(request.request_id, request.inputs)
    if request.operation == "preflight":
        return preflight(request.request_id, request.inputs)
    return response(
        "input_error",
        request_id=request.request_id,
        diagnostics=[diagnostic("invalid_envelope", "unsupported runner operation")],
    )


def runtime_info(request_id: str | None, _inputs: dict[str, Any]) -> dict[str, Any]:
    report = build_report(check_metadata=False)
    return response("ok", request_id=request_id, data={"report": report})


def preflight(request_id: str | None, _inputs: dict[str, Any]) -> dict[str, Any]:
    report = build_report(check_metadata=True)
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


def build_report(*, check_metadata: bool) -> dict[str, Any]:
    plugin_root = detect_plugin_root()
    package_dir = Path(__file__).resolve().parent

    python_version = platform.python_version()
    python_tuple = parse_version_tuple(python_version)
    python_status = "available" if python_tuple >= PYTHON_MINIMUM else "too_old"

    specify_path = shutil.which("specify")
    specify_available = specify_path is not None

    metadata = metadata_report(plugin_root, package_dir, check_metadata=check_metadata)

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
                "version": None,
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
) -> dict[str, Any]:
    manifest_path = package_dir / MANIFEST_NAME
    checksum_path = package_dir / CHECKSUM_NAME
    base = {
        "verification_status": "not_checked",
        "manifest": typed_path("plugin_relative", plugin_relative(plugin_root, manifest_path), f"speckit_pro_runner/{MANIFEST_NAME}"),
        "checksum": typed_path("plugin_relative", plugin_relative(plugin_root, checksum_path), f"speckit_pro_runner/{CHECKSUM_NAME}"),
        "runner_files": [],
    }
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
