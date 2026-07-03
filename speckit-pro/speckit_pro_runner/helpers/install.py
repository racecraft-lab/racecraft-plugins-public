"""Install inventory doctor and repair helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from .mutation import resolve_candidate_path, run_mutation_helper, validate_target_path
from .read_only import find_repo_root, repo_relative

INVENTORY_NAME = "install_inventory.json"


def run_install_helper(entry: Any, request: Any) -> dict[str, Any]:
    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        return response(
            "missing_prerequisite",
            request_id=request.request_id,
            diagnostics=[diagnostic("missing_prerequisite", "could not locate repository root for install helper request")],
        )

    install_root_result = install_root_from_inputs(request.inputs, repo_root)
    if isinstance(install_root_result, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[install_root_result])
    install_root = install_root_result

    inventory_result = inventory_from_inputs(request.inputs, repo_root)
    if is_diagnostic(inventory_result):
        return response("input_error", request_id=request.request_id, diagnostics=[inventory_result])
    inventory = inventory_result

    doctor = doctor_report(install_root, inventory, repo_root, fake_home=bool(request.inputs.get("fake_home")))

    if request.helper_id == "doctor-preflight":
        return response(
            "ok",
            request_id=request.request_id,
            data={
                "helper_id": entry.helper_id,
                "operation": entry.operation,
                "mode": request.mode,
                "promotion_status": entry.promotion_status,
                "comparison_mode": entry.comparison_mode,
                "writes_state": False,
                "doctor": doctor,
            },
        )

    if request.helper_id == "doctor-repair" and request.inputs.get("fake_home") is not True:
        diag = diagnostic(
            "real_home_refused",
            "doctor-repair refuses to mutate a non-fixture home/install root",
            details={"install_root": repo_relative(install_root, repo_root)},
            remediation_summary="Run repair only against a fake-home fixture until active cutover.",
            remediation_actions=["Set fake_home true for tests.", "Use read-only doctor-preflight for real installs."],
        )
        return response("input_error", request_id=request.request_id, data={"doctor": doctor}, diagnostics=[diag])

    repair_ops = [
        {
            "operation_id": f"repair:{record['path']}",
            "kind": "write_file",
            "target": (install_root / record["path"]).relative_to(repo_root).as_posix(),
            "content": record["content"],
        }
        for record in inventory["files"]
        if record["path"] in doctor["missing_files"] or record["path"] in doctor["checksum_mismatches"]
    ]
    return run_mutation_helper(entry, request, operations=repair_ops, extra_data={"doctor": doctor})


def install_root_from_inputs(inputs: dict[str, Any], repo_root: Path) -> Path | dict[str, Any]:
    raw = inputs.get("install_root")
    if not isinstance(raw, str) or not raw:
        return diagnostic(
            "invalid_input",
            "install_root is required",
            details={"field": "install_root"},
            remediation_summary="Send a repo-relative fake install root for fixture-backed repair.",
            remediation_actions=["Set install_root to a directory inside the repo fixture tree."],
        )
    path_diag = validate_target_path(f"{raw}/.speckit-pro-install-probe", repo_root)
    if path_diag is not None:
        return path_diag
    return resolve_candidate_path(raw, repo_root)


def inventory_from_inputs(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    raw = inputs.get("inventory")
    if raw is None:
        inventory_path = repo_root / "speckit-pro" / "speckit_pro_runner" / INVENTORY_NAME
        try:
            raw = json.loads(inventory_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return diagnostic(
                "malformed_inventory",
                "install inventory could not be loaded",
                details={"path": repo_relative(inventory_path, repo_root), "error": type(exc).__name__},
                remediation_summary="Refresh the committed install inventory.",
                remediation_actions=["Regenerate install_inventory.json.", "Retry doctor-preflight."],
            )
    if not isinstance(raw, dict):
        return malformed_inventory("inventory must be an object")
    files = raw.get("files")
    if not isinstance(files, list):
        return malformed_inventory("inventory.files must be an array")
    normalized_files: list[dict[str, str]] = []
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            return malformed_inventory("inventory file records must be objects", index=index)
        path = item.get("path")
        content = item.get("content")
        digest = item.get("sha256", "skip")
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in Path(path).parts:
            return malformed_inventory("inventory file path must be repo-relative without traversal", index=index)
        if not isinstance(content, str):
            return malformed_inventory("inventory file content must be a string", index=index)
        if not isinstance(digest, str) or not digest:
            return malformed_inventory("inventory sha256 must be a string", index=index)
        normalized_files.append({"path": path.replace("\\", "/"), "content": content, "sha256": digest})
    return {"files": normalized_files}


def malformed_inventory(message: str, *, index: int | None = None) -> dict[str, Any]:
    details: dict[str, Any] = {}
    if index is not None:
        details["file_index"] = index
    return diagnostic(
        "malformed_inventory",
        message,
        details=details,
        remediation_summary="Use the committed install inventory schema.",
        remediation_actions=["Inspect install_inventory.json.", "Retry with files containing path, content, and sha256."],
    )


def doctor_report(install_root: Path, inventory: dict[str, Any], repo_root: Path, *, fake_home: bool) -> dict[str, Any]:
    missing: list[str] = []
    mismatches: list[str] = []
    for record in inventory["files"]:
        target = install_root / record["path"]
        if not target.is_file():
            missing.append(record["path"])
            continue
        digest = record["sha256"]
        if digest != "skip" and sha256_text(target.read_text(encoding="utf-8", errors="replace")) != digest:
            mismatches.append(record["path"])

    status = "complete"
    if missing or mismatches:
        status = "safe_repair" if fake_home else "blocked"
    return {
        "status": status,
        "install_root": repo_relative(install_root, repo_root),
        "fake_home": fake_home,
        "missing_files": missing,
        "checksum_mismatches": mismatches,
        "safe_repairs": missing + mismatches if fake_home else [],
        "unsafe_manual_remediations": [] if fake_home else missing + mismatches,
        "blocked": bool((missing or mismatches) and not fake_home),
        "inventory_file_count": len(inventory["files"]),
    }


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_diagnostic(value: Any) -> bool:
    return isinstance(value, dict) and value.get("source") == "runner" and "code" in value
