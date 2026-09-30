"""Leaf helpers every formal module may import: errors, confined paths, strict JSON, bounded values."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from ..strict_input import SelectionError, require_text, unique_object

CATALOG_PATH = ".specify/formal-methods.json"
RUNS_PATH = ".specify/formal-runs"
EVIDENCE_PATH = ".specify/formal-evidence"
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


class FormalError(ValueError):
    def __init__(self, verdict: str, message: str):
        super().__init__(message)
        self.verdict = verdict


def confined(root: Path, value: str, *, durable: bool = False) -> Path:
    require_text(value, "path")
    path = Path(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise SelectionError(f"path must be relative to WORKFLOW_ROOT: {value}")
    result = (root / path).resolve()
    if not result.is_relative_to(root.resolve()) or any(p.casefold() == ".git" for p in path.parts):
        raise SelectionError(f"path leaves the workflow's permitted files: {value}")
    canonical = result.relative_to(root.resolve()).as_posix()
    if durable and (canonical.split("/")[0] == "specs" or canonical.startswith((RUNS_PATH, EVIDENCE_PATH, ".specify/formal-traces"))):
        raise SelectionError(f"model inputs must survive archival and exclude run results: {value}")
    return result


def reject_nonfinite(value: str) -> Any:
    raise SelectionError(f"non-finite JSON number is invalid: {value}")


def read_json(path: Path) -> Any:
    if path.stat().st_size > 1_048_576:
        raise SelectionError(f"JSON input exceeds 1 MiB: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object, parse_constant=reject_nonfinite)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def bounded_integer(value: Any, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise SelectionError(f"{label} must be an integer from {low} to {high}")
    return value


def operator(value: Any) -> str:
    if not isinstance(value, str) or not NAME.fullmatch(value):
        raise SelectionError("operator names must be TLA+ identifiers")
    return value


def atomic_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".formal-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(record, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
