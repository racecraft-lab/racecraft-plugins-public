"""Deterministic draft gallery selection; authoring remains fail-open (ADR 0019)."""

from __future__ import annotations

from collections.abc import Iterator
import json
import re
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from ..strict_input import next_fence, require_text
from ..trusted_io import resolve_repo_root, trusted_bytes, validate_path_value
from .read_only import declared_file_entries

GALLERY = Path(__file__).resolve().parents[2] / "artifact-gallery"
INPUTS = frozenset({"repo_root", "plan_file", "research_file", "design_concept_file"})
ALTERNATIVES_TITLE = re.compile(r"Alternatives(?: considered| offered)?\s*:?", re.IGNORECASE)
ALTERNATIVES_FIELD = re.compile(r"^\*\*Alternatives(?: considered| offered)?\s*:?\*\*\s*:?\s*(.*)$", re.IGNORECASE)
HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
EMPTY_ALTERNATIVE = re.compile(r"^(?:none\b|no alternatives\b|n/a\b|not applicable\b|tbd\b|todo\b|<|"
                               r"\[(?:TODO|TBD|NEEDS CLARIFICATION)\]$)", re.IGNORECASE)


def planning_lines(text: str) -> Iterator[str]:
    """Planning records exclude fenced examples from both selection signals."""
    fence: str | None = None
    for raw in text.splitlines():
        previous = fence
        fence = next_fence(fence, raw)
        if previous is None and fence is None:
            yield raw


def records_alternatives(text: str) -> bool:
    """Recognize populated alternatives headings or bold fields, outside examples."""
    active_level = 0
    for raw in planning_lines(text):
        line = raw.strip()
        heading = HEADING.match(line)
        if heading and ALTERNATIVES_TITLE.fullmatch(heading.group(2)):
            active_level = len(heading.group(1))
            continue
        label = ALTERNATIVES_FIELD.match(line)
        if label:
            active_level = 7
            line = label.group(1)
        elif line.startswith("**") or (heading and len(heading.group(1)) <= active_level):
            active_level = 0
        candidate = line.lstrip("-* `").strip()
        if active_level and candidate and not EMPTY_ALTERNATIVE.match(candidate):
            return True
    return False


def planning_text(inputs: dict[str, Any], field: str, root: Path, *, required: bool = False) -> str:
    """Omitted optional inputs are absent evidence; supplied unreadable files are errors."""
    if field not in inputs and not required:
        return ""
    raw = require_text(inputs.get(field), field)
    if validate_path_value("select-artifact-pages", field, raw, root) is not None:
        raise ValueError(f"{field} escapes the repository boundary")
    content = trusted_bytes(root / raw, root)
    if content is None:
        raise ValueError(f"{field} is unreadable")
    return content.decode("utf-8")


def select_artifact_pages(inputs: dict[str, Any], root: Path) -> dict[str, Any]:
    if set(inputs) - INPUTS:
        raise ValueError("select-artifact-pages received unknown inputs")
    plan = "\n".join(planning_lines(planning_text(inputs, "plan_file", root, required=True)))
    signals = {"brownfield_change"} if any(status == "MODIFIED" for status, _ in declared_file_entries(plan)) else set()
    alternatives = [planning_text(inputs, field, root) for field in ("research_file", "design_concept_file")]
    if any(records_alternatives(text) for text in alternatives):
        signals.add("competing_approaches")
    content = trusted_bytes(GALLERY / "manifest.json", GALLERY)
    if content is None:
        raise ValueError("gallery manifest is unreadable")
    entries = json.loads(content)["templates"]
    selected = [entry["id"] for entry in entries
                if entry["status"] == "shipped" and entry["stage"] == "draft-pr"
                and (entry["trigger"].get("always") is True
                     or signals.intersection(entry["trigger"].get("any_of", [])))]
    return {"selected_pages": selected, "signals": sorted(signals), "writes_state": False}


def run_artifact_selection_helper(entry: Any, request: Any) -> dict[str, Any]:
    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    try:
        data = select_artifact_pages(request.inputs, root)
    except (ValueError, KeyError, TypeError) as error:
        return response("input_error", request_id=request.request_id, diagnostics=[diagnostic(
            "artifact_selection_invalid", str(error),
            remediation_summary="Correct the planning inputs or record a whole-set artifact gap.",
            remediation_actions=["Retry selection with readable planning files and the shipped gallery."],
        )])
    return response("ok", request_id=request.request_id, data=data)
