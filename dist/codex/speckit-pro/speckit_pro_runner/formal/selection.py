"""Parse the workflow-owned selection without discovering or activating tools."""

from __future__ import annotations

import json
import re
from typing import Any

from ..strict_input import SelectionError, next_fence, require_fields, require_text, unique_object

SCHEMA_VERSION = "1.0"
STATUSES = ("none", "deferred", "enabled")
ORIGINS = ("new", "existing")
EVIDENCE_LEVELS = ("model", "model_and_trace")
IDENTIFIER = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")


def validate_model_selection(value: Any) -> dict[str, str]:
    model = require_fields(value, {"id", "behavior", "origin", "evidence"}, "selected model")
    for key in model:
        require_text(model[key], f"model.{key}")
    if not IDENTIFIER.fullmatch(model["id"]):
        raise SelectionError("model.id must be a lowercase hyphenated identifier")
    if model["origin"] not in ORIGINS:
        raise SelectionError(f"model.origin must be one of {ORIGINS}")
    if model["evidence"] not in EVIDENCE_LEVELS:
        raise SelectionError(f"model.evidence must be one of {EVIDENCE_LEVELS}")
    return dict(model)


def validate_selection(value: Any) -> dict[str, Any]:
    record = require_fields(value, {"schema_version", "status", "rationale", "models"}, "formal selection")
    if record["schema_version"] != SCHEMA_VERSION:
        raise SelectionError(f"formal selection schema_version must be {SCHEMA_VERSION}")
    if record["status"] not in STATUSES:
        raise SelectionError(f"formal selection status must be one of {STATUSES}")
    require_text(record["rationale"], "formal selection rationale")
    if not isinstance(record["models"], list):
        raise SelectionError("formal selection models must be an array")
    models = [validate_model_selection(model) for model in record["models"]]
    ids = [model["id"] for model in models]
    if len(ids) != len(set(ids)):
        raise SelectionError("selected model IDs must be unique")
    if record["status"] == "enabled" and not models:
        raise SelectionError("enabled formal selection needs at least one selected model")
    if record["status"] == "none" and models:
        raise SelectionError("none formal selection cannot contain selected models")
    return {**record, "models": models}


def selection_from_workflow(text: str) -> dict[str, Any]:
    """Read one JSON block in one top-level Formal Methods section.

    Legacy absence alone means disabled. A present but empty/invalid section is
    an error, so unfinished scaffold substitutions cannot bypass a checkpoint.
    Ignore headings inside Markdown fences, which may contain phase prompts.
    """
    sections = formal_sections(text)
    if not sections:
        return {"schema_version": SCHEMA_VERSION, "status": "none", "rationale": "Legacy workflow has no formal selection.", "models": []}
    if len(sections) != 1:
        raise SelectionError("workflow must have only one Formal Methods section")
    blocks = re.findall(r"(?ms)^ {0,3}```json\s*\n(.*?)^ {0,3}```\s*$", "\n".join(sections[0]))
    if len(blocks) != 1:
        raise SelectionError("Formal Methods must contain exactly one fenced JSON selection")
    try:
        return validate_selection(json.loads(blocks[0], object_pairs_hook=unique_object))
    except (json.JSONDecodeError, RecursionError) as exc:
        raise SelectionError(f"invalid formal selection JSON: {exc}") from exc


def formal_sections(text: str) -> list[list[str]]:
    """Collect selection sections, excluding headings inside phase prompt fences."""
    sections: list[list[str]] = []
    current: list[str] | None = None
    fence: str | None = None
    for line in text.splitlines():
        if fence is None and re.match(r"^##\s+", line):
            current = [] if line.strip() == "## Formal Methods" else None
            if current is not None:
                sections.append(current)
        if current is not None:
            current.append(line)
        fence = next_fence(fence, line)
    return sections
