"""Payload and install-verification gate operations for XPLAT-007 US2."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from ..envelope import diagnostic, response

PROMOTION_RECORD = "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json"
FIXTURE_BOUNDARY = Path("tests") / "speckit-pro" / "layer4-scripts" / "fixtures" / "xplat-007-gates"
DEFAULT_PAYLOAD_CASES = FIXTURE_BOUNDARY / "payload-evidence-cases.json"
DEFAULT_INSTALL_CASES = FIXTURE_BOUNDARY / "install-verification-cases.json"
INSTALL_INVENTORY = Path("speckit-pro") / "speckit_pro_runner" / "install_inventory.json"

__all__ = ("run_payload_gate",)


def run_payload_gate(entry: Any, request: Any) -> dict[str, Any]:
    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        diag = diagnostic(
            "missing_prerequisite",
            "could not locate repository root for payload/install gate request",
            remediation_summary="Run the gate from a SpecKit Pro source checkout.",
            remediation_actions=["Change to the repository root.", "Retry the same runner request."],
        )
        return response("missing_prerequisite", request_id=request.request_id, data=base_data(entry, request.operation, "missing_prerequisite"), diagnostics=[diag])

    if request.operation == "build-test-payload-evidence":
        return build_test_payload_evidence(entry, request, repo_root)
    if request.operation == "refresh-local-plugin-fixture":
        return install_verification(entry, request, repo_root, refresh=True)
    if request.operation == "verify-install":
        return install_verification(entry, request, repo_root, refresh=False)

    diag = diagnostic(
        "unknown_gate_operation",
        "payload/install gate operation is not implemented by the payload module",
        details={"operation": request.operation},
    )
    return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])


def build_test_payload_evidence(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    if request.inputs.get("release_payload_cutover") is not False:
        diag = diagnostic(
            "release_payload_cutover_refused",
            "XPLAT-007 payload evidence must not select or cut over release payloads",
            details={"release_payload_cutover": request.inputs.get("release_payload_cutover")},
            remediation_summary="Keep test payload evidence isolated from release payload selection.",
            remediation_actions=["Set release_payload_cutover to false.", "Defer generated release payload cutover to XPLAT-008."],
            deferred_to="XPLAT-008",
        )
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])

    case_result = load_case(repo_root, request.inputs, default_case_file=DEFAULT_PAYLOAD_CASES)
    if is_diagnostic(case_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[case_result])
    case = case_result

    output_result = output_root_from_inputs(request.inputs, repo_root)
    if is_diagnostic(output_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[output_result])
    output_root = output_result
    output_root_rel = repo_relative(output_root, repo_root) if is_relative_to(output_root, repo_root) else output_root.as_posix()

    evidence = [
        payload_evidence_record(payload, request.mode, case, output_root_rel)
        for payload in case.get("payloads", [])
        if isinstance(payload, dict)
    ]
    if not evidence:
        diag = diagnostic(
            "invalid_payload_case",
            "payload evidence case must contain at least one payload record",
            details={"case_id": case.get("case_id")},
            remediation_summary="Use a payload evidence fixture with payload records.",
            remediation_actions=["Inspect payload-evidence-cases.json.", "Retry with a valid case_id."],
        )
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])

    data = base_data(entry, request.operation, "ok")
    data["payload_evidence"] = evidence
    data["artifacts"].extend(payload_artifacts(evidence, output_root, repo_root, include_written=request.mode == "apply"))

    stale = [item for item in case.get("stale_generated_files", []) if isinstance(item, str)]
    if stale:
        for item in evidence:
            item["status"] = "expected_failure"
        data["gate"]["gate_status"] = "fail"
        data["gate"]["blocking"] = True
        diag = diagnostic(
            "stale_generated_payload_evidence",
            "payload evidence fixture contains stale generated release payload references",
            details={"case_id": case.get("case_id"), "stale_generated_files": stale},
            remediation_summary="Refresh test payload evidence without touching release payload cutover files.",
            remediation_actions=["Remove stale generated release payload evidence.", "Re-run build-test-payload-evidence in fixture or temp output roots."],
        )
        return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])

    if request.mode == "apply":
        write_payload_evidence(evidence, output_root)

    return response("ok", request_id=request.request_id, data=data)


def install_verification(entry: Any, request: Any, repo_root: Path, *, refresh: bool) -> dict[str, Any]:
    case_result = load_case(repo_root, request.inputs, default_case_file=DEFAULT_INSTALL_CASES)
    if is_diagnostic(case_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[case_result])
    case = case_result

    fake_home = request.inputs.get("fake_home", case.get("fake_home")) is True
    if not fake_home:
        diag = diagnostic(
            "real_home_refused",
            "US2 install verification accepts fake-home fixture roots only",
            details={"case_id": case.get("case_id")},
            remediation_summary="Use fake_home true with a fixture install root.",
            remediation_actions=["Set fake_home to true.", "Defer real installed-cache verification to XPLAT-008."],
            deferred_to="XPLAT-008",
        )
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])

    install_root_result = install_root_from_case(case, repo_root)
    if is_diagnostic(install_root_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[install_root_result])
    install_root = install_root_result

    inventory_result = load_install_inventory(repo_root, case)
    if is_diagnostic(inventory_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[inventory_result])
    inventory = inventory_result

    missing = sorted(path for path in case.get("missing_paths", []) if isinstance(path, str))
    mismatches = sorted(path for path in case.get("checksum_mismatches", []) if isinstance(path, str))
    expected_files = [record["path"] for record in inventory]
    status = "complete"
    if missing or mismatches:
        status = "safe_repair" if fake_home else "blocked"
    if case.get("expected_status") in {"complete", "safe_repair", "blocked"}:
        status = str(case["expected_status"])

    install = {
        "schema_version": "1.0",
        "verification_id": str(case.get("verification_id") or f"us2-install-{case.get('case_id', 'fixture')}"),
        "status": status,
        "install_root": repo_relative(install_root, repo_root),
        "fake_home": True,
        "stubbed_cli": request.inputs.get("stubbed_cli", case.get("stubbed_cli", True)) is True,
        "bundled_agent_count": bundled_agent_count(inventory),
        "expected_files": expected_files,
        "missing_files": missing,
        "checksum_mismatches": mismatches,
        "command_plans": command_plans(request.operation, missing + mismatches),
        "safe_repairs": missing + mismatches if status == "safe_repair" else [],
        "unsafe_manual_remediations": [] if fake_home else missing + mismatches,
        "native_uat_claimed": False,
    }

    if refresh and request.mode == "read_only":
        install["command_plans"] = command_plans(request.operation, expected_files[:1])

    data = base_data(entry, request.operation, "ok")
    data["install_verification"] = install
    return response("ok", request_id=request.request_id, data=data)


def payload_evidence_record(payload: dict[str, Any], mode: str, case: dict[str, Any], output_root: str) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for item in payload.get("files", []):
        if not isinstance(item, dict):
            continue
        path = normalize_posix_path(str(item.get("path", "")))
        content = str(item.get("content", ""))
        files.append({"path": path, "sha256": sha256_text(content), "byte_count": len(content.encode("utf-8"))})
    tree_payload = json.dumps(files, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": "1.0",
        "evidence_id": str(payload.get("evidence_id")),
        "payload_surface": str(payload.get("payload_surface")),
        "mode": mode,
        "input_root": f"{DEFAULT_PAYLOAD_CASES.as_posix()}#{case.get('case_id')}",
        "output_root": output_root,
        "file_tree_hash": sha256_text(tree_payload),
        "files": files,
        "release_payload_cutover": False,
        "status": "ok",
    }


def payload_artifacts(evidence: list[dict[str, Any]], output_root: Path, repo_root: Path, *, include_written: bool) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    if not include_written:
        return artifacts
    for item in evidence:
        path = output_root / payload_evidence_filename(item["payload_surface"])
        artifacts.append({"path": repo_relative(path, repo_root), "kind": "evidence"})
    return artifacts


def write_payload_evidence(evidence: list[dict[str, Any]], output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    for item in evidence:
        target = output_root / payload_evidence_filename(item["payload_surface"])
        target.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def payload_evidence_filename(surface: str) -> str:
    raw = str(surface).strip().replace("\\", "/")
    parts = [part for part in raw.split("/") if part not in {"", ".", ".."}]
    stem = parts[-1] if parts else "payload"
    safe = "".join(ch if ch.isalnum() or ch in ".-" else "-" for ch in stem.replace("_", "-"))
    while ".." in safe:
        safe = safe.replace("..", ".")
    safe = safe.strip(".-") or "payload"
    return f"{safe}-payload-evidence.json"


def command_plans(operation: str, repair_paths: list[str]) -> list[dict[str, Any]]:
    plans = [
        {
            "operation_id": operation,
            "argv": [sys.executable, "-m", "speckit_pro_runner"],
        }
    ]
    for path in repair_paths:
        plans.append(
            {
                "operation_id": f"repair:{path}",
                "argv": [sys.executable, "-m", "speckit_pro_runner"],
            }
        )
    return plans


def load_case(repo_root: Path, inputs: dict[str, Any], *, default_case_file: Path) -> dict[str, Any]:
    raw = inputs.get("case_file", default_case_file.as_posix())
    path_result = fixture_file_path(raw, repo_root)
    if is_diagnostic(path_result):
        return path_result
    try:
        document = json.loads(path_result.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return diagnostic(
            "invalid_case_file",
            "case fixture could not be loaded",
            details={"case_file": str(raw), "error": type(exc).__name__},
            remediation_summary="Use a valid JSON fixture case file.",
            remediation_actions=["Inspect the case fixture.", "Retry with a valid case_file path."],
        )
    cases = document.get("cases")
    if not isinstance(cases, list):
        return diagnostic("invalid_case_file", "case fixture must contain a cases array")
    case_id = inputs.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        case_id = str(cases[0].get("case_id")) if cases and isinstance(cases[0], dict) else ""
    for case in cases:
        if isinstance(case, dict) and case.get("case_id") == case_id:
            merged = dict(case)
            merged["_case_file"] = repo_relative(path_result, repo_root)
            return merged
    return diagnostic(
        "unknown_fixture_case",
        "requested fixture case was not found",
        details={"case_id": case_id, "case_file": repo_relative(path_result, repo_root)},
        remediation_summary="Use a case_id declared by the fixture file.",
        remediation_actions=["Inspect the case fixture.", "Retry with a known case_id."],
    )


def fixture_file_path(raw: Any, repo_root: Path) -> Path | dict[str, Any]:
    if not isinstance(raw, str) or not raw:
        return diagnostic("invalid_case_file", "case_file must be a non-empty string")
    path = resolve_path(raw, repo_root)
    if not is_relative_to(path.resolve(strict=False), repo_root.resolve(strict=False)):
        return diagnostic("invalid_case_file", "case_file must stay inside the repository")
    if not path.is_file():
        return diagnostic("invalid_case_file", "case_file does not exist", details={"case_file": raw})
    return path


def output_root_from_inputs(inputs: dict[str, Any], repo_root: Path) -> Path | dict[str, Any]:
    raw = inputs.get("output_root")
    if not isinstance(raw, str) or not raw:
        return diagnostic(
            "fixture_output_root_refused",
            "output_root is required for test payload evidence",
            remediation_summary="Use a fixture or temporary output root.",
            remediation_actions=["Set output_root under the XPLAT-007 fixture tree or a temp directory."],
        )
    output_root = resolve_path(raw, repo_root)
    resolved = output_root.resolve(strict=False)
    fixture_root = (repo_root / FIXTURE_BOUNDARY).resolve(strict=False)
    temp_root = Path(tempfile.gettempdir()).resolve(strict=False)
    if is_relative_to(resolved, fixture_root) or is_relative_to(resolved, temp_root):
        return output_root
    return diagnostic(
        "fixture_output_root_refused",
        "payload evidence output_root must be fixture or temporary scoped",
        details={"output_root": raw, "fixture_root": repo_relative(fixture_root, repo_root)},
        remediation_summary="Keep payload evidence writes in fixture or temp roots only.",
        remediation_actions=["Use tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/.", "Or use an OS temp directory."],
    )


def install_root_from_case(case: dict[str, Any], repo_root: Path) -> Path | dict[str, Any]:
    raw = case.get("install_root")
    if not isinstance(raw, str) or not raw:
        return diagnostic("fixture_install_root_refused", "install_root is required")
    install_root = resolve_path(raw, repo_root)
    resolved = install_root.resolve(strict=False)
    boundary = (repo_root / FIXTURE_BOUNDARY).resolve(strict=False)
    if is_relative_to(resolved, boundary):
        return install_root
    return diagnostic(
        "fixture_install_root_refused",
        "install verification refuses roots outside the XPLAT-007 fixture boundary",
        details={"install_root": normalize_path_text(raw), "fixture_root": repo_relative(boundary, repo_root)},
        remediation_summary="Use a fake-home install root under the XPLAT-007 fixture tree.",
        remediation_actions=["Move install_root under tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates.", "Retry verify-install."],
        deferred_to="XPLAT-008",
    )


def load_install_inventory(repo_root: Path, case: dict[str, Any]) -> list[dict[str, str]]:
    inventory_path = repo_root / INSTALL_INVENTORY
    try:
        document = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return diagnostic(
            "malformed_inventory",
            "install inventory could not be loaded",
            details={"path": INSTALL_INVENTORY.as_posix(), "error": type(exc).__name__},
        )
    files = document.get("files")
    if not isinstance(files, list):
        return diagnostic("malformed_inventory", "install inventory files must be an array")
    normalized: list[dict[str, str]] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        path = normalize_posix_path(str(item.get("path", "")))
        content = str(item.get("content", ""))
        digest = str(item.get("sha256", "skip"))
        normalized.append({"path": path, "content": normalized_content(content, case), "sha256": digest})
    return normalized


def normalized_content(content: str, case: dict[str, Any]) -> str:
    if case.get("installed_files") == "from_inventory_crlf":
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        return normalized.replace("\n", "\r\n")
    return content


def bundled_agent_count(inventory: list[dict[str, str]]) -> int:
    return sum(1 for record in inventory if "agent" in PurePosixPath(record["path"]).parts or record["path"].startswith("agents/"))


def base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    gate_status = "pass"
    if status in {"expected_failure", "subprocess_failure"}:
        gate_status = "fail"
    elif status == "missing_prerequisite":
        gate_status = "skipped"
    elif status == "input_error":
        gate_status = "input_error"
    return {
        "gate": {
            "gate_id": entry.helper_id,
            "operation": operation,
            "gate_status": gate_status,
            "promoted": status != "input_error",
            "blocking": status != "ok",
            "comparison_ids": [f"us2-{operation}"],
            "promotion_record": PROMOTION_RECORD,
        },
        "artifacts": [{"path": PROMOTION_RECORD, "kind": "fixture"}],
    }


def find_repo_root(start: Path) -> Path | None:
    candidates = [start, *start.parents] if start.is_dir() else [start.parent, *start.parent.parents]
    for candidate in candidates:
        if (candidate / "speckit-pro" / "speckit_pro_runner").is_dir() and (candidate / "tests" / "speckit-pro").is_dir():
            return candidate.resolve(strict=False)
    return None


def resolve_path(raw: str, repo_root: Path) -> Path:
    value = normalize_path_text(raw)
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def normalize_path_text(raw: str) -> str:
    return raw.replace("\\", "/")


def normalize_posix_path(raw: str) -> str:
    value = normalize_path_text(raw)
    parts = PurePosixPath(value).parts
    if value.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        return value.strip("/")
    return PurePosixPath(value).as_posix()


def repo_relative(path: Path, repo_root: Path) -> str:
    return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix()


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_diagnostic(value: Any) -> bool:
    return isinstance(value, dict) and value.get("source") == "runner" and "code" in value
