"""Checklist verification evidence shared by application, dispatch and G4.

This owner is separate from the proposal helper so G4 can read evidence without
importing the helper registry or consensus dispatcher. Receipts bind the original
domain list to verified shared-artifact digests; marker counts alone cannot pass G4.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .atomic_write import (open_safe_parent_fd, snapshot_write_target,
                           snapshot_write_target_fd, write_file_atomic)
from .canonical_json import canonical_bytes
from .strict_input import require_fields, require_text

ARTIFACTS = ("spec.md", "plan.md")
SCHEMA = "checklist-coverage/v1"


def coverage_path(feature: Path) -> Path:
    return feature / ".process" / "checklist-edits" / "coverage.json"


def read_coverage(root: Path, feature: Path) -> dict[str, Any]:
    snapshot = snapshot_write_target(coverage_path(feature), root)
    if not snapshot["exists"]:
        raise ValueError("checklist verification evidence is missing")
    data = require_fields(json.loads(snapshot["content"]),
                          {"schema_version", "domains", "verified_baseline"}, "checklist coverage")
    domains = data["domains"]
    if data["schema_version"] != SCHEMA or not isinstance(domains, list) or not domains:
        raise ValueError("invalid checklist coverage evidence")
    names = [require_text(name, "coverage domain") for name in domains]
    if len(set(names)) != len(names):
        raise ValueError("coverage domains must be unique")
    return data


def save_coverage(root: Path, feature: Path, domains: list[str], baseline: dict[str, str] | None = None) -> None:
    """Start pending coverage, or attest a complete verify pass over the original domains."""
    if baseline is not None and read_coverage(root, feature)["domains"] != domains:
        raise ValueError("verification must cover every original domain in order")
    path = coverage_path(feature)
    opened = open_safe_parent_fd(path, root, create=True)
    if opened is None:
        raise ValueError("coverage directory is unavailable")
    os.close(opened[0])
    write_file_atomic(path.parent / ".gitignore", "*\n", trust_root=root)
    data = {"schema_version": SCHEMA, "domains": domains, "verified_baseline": baseline}
    write_file_atomic(path, canonical_bytes(data).decode("utf-8"), trust_root=root)


def coverage_problem(root: Path, feature: Path) -> str | None:
    """Missing, malformed or stale verification evidence blocks completion."""
    try:
        data = read_coverage(root, feature)
        baseline = require_fields(data["verified_baseline"], set(ARTIFACTS), "verified baseline")
        opened = open_safe_parent_fd(feature / ARTIFACTS[0], root, create=False)
        if opened is None:
            raise ValueError("shared artifacts are missing")
        try:
            for name in ARTIFACTS:
                snapshot = snapshot_write_target_fd(opened[0], name)
                if not snapshot["exists"] or snapshot["digest"] != baseline[name]:
                    return "shared artifacts changed since the complete checklist verify pass"
        finally:
            os.close(opened[0])
    except (OSError, ValueError, TypeError) as error:
        return str(error)
    return None
