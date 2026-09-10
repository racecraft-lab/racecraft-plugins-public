"""Content-bound checkpoint records kept outside model authoring inputs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from .catalog import EVIDENCE_PATH, confined, digest, read_json
from .selection import SelectionError, next_fence, selection_from_workflow

CHECKPOINT_ROWS = {"plan": "Plan model authoring and G3", "planning": "Planning reconciliation", "final": "Final model and optional trace checks", "post": "Post integration"}


def record_path(root: Path, workflow: str, checkpoint: str) -> Path:
    key = hashlib.sha256(workflow.encode()).hexdigest()[:16]
    return confined(root, f"{EVIDENCE_PATH}/{key}/{checkpoint}.json")


def fingerprint(root: Path, selection: dict[str, Any], models: dict[str, Any], identities: dict[str, Any], spec: str, plan: str) -> str:
    paths = {spec, plan}
    for item in models.values():
        paths.update(item["model"]["inputs"])
    files = {name: digest(confined(root, name)) for name in sorted(paths)}
    engine = {path.name: digest(path) for path in sorted(Path(__file__).parent.glob("*.py"))}
    material = {"selection": selection, "models": models, "files": files, "checkers": identities, "engine": engine}
    return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def atomic_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".formal-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(record, stream, sort_keys=True, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def checkpoint_section(text: str) -> tuple[list[str], list[int], int]:
    lines = text.splitlines()
    active: list[int] = []
    fence = None
    found = False
    collecting = False
    end = len(lines)
    for index, line in enumerate(lines):
        if fence is None and re.match(r"^#{1,2}\s+", line):
            if collecting:
                end = index
            collecting = line.strip() == "## Formal Checkpoints"
            if collecting:
                if found:
                    raise SelectionError("workflow must have only one Formal Checkpoints section")
                found = True
        if collecting and fence is None:
            active.append(index)
        fence = next_fence(fence, line)
    return lines, active, end


def write_checkpoint(root: Path, workflow: str, checkpoint: str, record: dict[str, Any], writes: dict[str, bool] | None = None) -> None:
    path = record_path(root, workflow, checkpoint)
    atomic_record(path, record)
    if writes is not None:
        writes["writes_state"] = True
    workflow_path = confined(root, workflow)
    text = workflow_path.read_text(encoding="utf-8")
    row = f"| {CHECKPOINT_ROWS[checkpoint]} | {record['verdict']} | {path.relative_to(root).as_posix()} |"
    lines, active, end = checkpoint_section(text)
    matches = [index for index in active if lines[index].startswith(f"| {CHECKPOINT_ROWS[checkpoint]} |")]
    if len(matches) > 1:
        raise SelectionError("duplicate formal checkpoint row")
    if matches:
        lines[matches[0]] = row
    elif any(lines[index] == "| Checkpoint | Status | Evidence |" for index in active):
        table_rows = [index for index in active if lines[index].startswith("|")]
        lines.insert(table_rows[-1] + 1, row)
    else:
        header = [] if active else ["", "## Formal Checkpoints"]
        lines[end:end] = [*header, "", "| Checkpoint | Status | Evidence |", "|---|---|---|", row, ""]
    workflow_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def checkpoint_signal(text: str) -> dict[str, Any]:
    """A text-only prerequisite; runtime freshness additionally verifies the record."""
    try:
        selection = selection_from_workflow(text)
        lines, active, _ = checkpoint_section(text)
    except ValueError:
        return {"required": True, "complete": False, "verdict": "invalid_configuration"}
    if selection["status"] != "enabled":
        return {"required": False, "complete": True, "verdict": "disabled"}
    passed = any(lines[index].startswith("| Plan model authoring and G3 | pass |") for index in active)
    return {"required": True, "complete": passed, "verdict": "recorded_pass" if passed else "pending"}


def read_checkpoint(root: Path, workflow: str, checkpoint: str = "plan") -> dict[str, Any] | None:
    path = record_path(root, workflow, checkpoint)
    return read_json(path) if path.is_file() else None
