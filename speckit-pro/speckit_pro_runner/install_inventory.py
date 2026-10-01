"""The fixture install inventory: where it lives and the one validated loader.

The doctor-preflight and doctor-repair helpers and the verify-install gate read the
same file. It lists fixture files, not a real install, so it lives with the test
fixtures and is read only from a source checkout.
"""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

from .envelope import diagnostic
from .trusted_io import repo_relative

FAKE_HOME_FIXTURE_ROOT = Path("tests") / "speckit-pro" / "unit" / "fixtures"
INSTALL_INVENTORY = FAKE_HOME_FIXTURE_ROOT / "install-inventory" / "install_inventory.json"


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


def normalize_install_inventory(raw: Any) -> dict[str, Any]:
    """`{"files": [...]}` with repo-relative paths, string content and digests, or a malformed_inventory diagnostic."""
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
        if not isinstance(path, str) or not path:
            return malformed_inventory("inventory file path must be repo-relative without traversal", index=index)
        normalized_path = path.replace("\\", "/")
        parts = PurePosixPath(normalized_path).parts
        if normalized_path.startswith("/") or any(part in {"", ".", ".."} for part in parts):
            return malformed_inventory("inventory file path must be repo-relative without traversal", index=index)
        if not isinstance(content, str):
            return malformed_inventory("inventory file content must be a string", index=index)
        if not isinstance(digest, str) or not digest:
            return malformed_inventory("inventory sha256 must be a string", index=index)
        normalized_files.append({"path": normalized_path, "content": content, "sha256": digest})
    return {"files": normalized_files}


def read_install_inventory(repo_root: Path) -> dict[str, Any]:
    """The committed fixture inventory, validated, or a malformed_inventory diagnostic."""
    inventory_path = repo_root / INSTALL_INVENTORY
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
    return normalize_install_inventory(raw)
