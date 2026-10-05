"""Deterministic draft gallery selection; authoring remains fail-open (ADR 0019)."""

from __future__ import annotations

from collections.abc import Iterator
import json
import re
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from ..json_schema import json_schema_failures
from ..strict_input import next_fence, require_text, unique_object
from ..trusted_io import resolve_repo_root, trusted_bytes, validate_path_value
from .read_only import declared_file_entries

GALLERY = Path(__file__).resolve().parents[2] / "artifact-gallery"
INPUTS = frozenset({"repo_root", "plan_file", "research_file", "design_concept_file", "candidate_paths"})
INPUT_ERRORS = (ValueError, KeyError, TypeError, OSError, RuntimeError)
ALTERNATIVES_TITLE = re.compile(r"Alternatives(?: considered| offered)?\s*:?", re.IGNORECASE)
ALTERNATIVES_FIELD = re.compile(r"^\*\*Alternatives(?: considered| offered)?\s*:?\*\*\s*:?\s*(.*)$", re.IGNORECASE)
HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
EMPTY_ALTERNATIVE = re.compile(r"^(?:none\b|no alternatives\b|n/a\b|not applicable\b|tbd\b|todo\b|<|"
                               r"\[(?:TODO|TBD|NEEDS CLARIFICATION)\]$)", re.IGNORECASE)
TEXT = {"type": "string", "minLength": 1}
ENTRY_FIELDS = {
    "id": {**TEXT, "pattern": r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"},
    "category": TEXT, "title": TEXT, "when_to_use": TEXT,
    "stage": {"enum": ["draft-pr", "final-pr", "ad-hoc"]},
    "status": {"enum": ["shipped", "planned"]},
    "trigger": {"oneOf": [
        {"type": "object", "properties": {"always": {"const": True}},
         "required": ["always"], "additionalProperties": False},
        {"type": "object", "properties": {"any_of": {
            "type": "array", "minItems": 1, "uniqueItems": True, "items": TEXT}},
         "required": ["any_of"], "additionalProperties": False},
    ]},
    "source": {"type": "object", "properties": {"origin": {"enum": ["upstream", "repository"]}, "file": TEXT},
               "required": ["origin"], "additionalProperties": False,
               "if": {"properties": {"origin": {"const": "upstream"}}}, "then": {"required": ["file"]}},
    "exports": {"type": "array", "uniqueItems": True, "items": TEXT},
}
MANIFEST_FIELDS = {
    "schema_version": {"const": "1.0"},
    "signals": {"type": "array", "minItems": 1, "uniqueItems": True, "items": TEXT},
    "export_kinds": {"type": "array", "minItems": 1, "uniqueItems": True, "items": TEXT},
    "templates": {"type": "array", "minItems": 1, "items": {
        "type": "object", "properties": ENTRY_FIELDS, "required": list(ENTRY_FIELDS), "additionalProperties": False}},
}
MANIFEST_SCHEMA = {"type": "object", "properties": MANIFEST_FIELDS,
                   "required": list(MANIFEST_FIELDS), "additionalProperties": False}


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
        if EMPTY_ALTERNATIVE.match(candidate):
            active_level = 0
        if active_level and candidate:
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


def artifact_output_path(raw: str, root: Path, directory: Path) -> str:
    """Resolve only direct artifact children, with no symlinked component."""
    relative = Path(require_text(raw, "artifact output path"))
    if relative.is_absolute() or ".." in relative.parts or "\\" in raw or "\x00" in raw:
        raise ValueError("artifact output path must be repository-relative without traversal")
    if relative.parent != directory:
        raise ValueError("artifact output path must be inside the feature artifacts directory")
    if any((root / Path(*relative.parts[:count])).is_symlink() for count in range(1, len(relative.parts) + 1)):
        raise ValueError("artifact output path contains a symlinked component")
    candidate = (root / relative).resolve()
    if candidate.parent != (root / directory).resolve():
        raise ValueError("artifact output path escapes the feature artifacts directory")
    return relative.as_posix()


def draft_gallery_entries(content: bytes) -> list[dict[str, Any]]:
    """Validate the routing contract before any entry can suppress or select a page."""
    manifest = json.loads(content, object_pairs_hook=unique_object)
    failures = json_schema_failures(manifest, MANIFEST_SCHEMA, MANIFEST_SCHEMA, "gallery manifest")
    if failures:
        raise ValueError(f"gallery manifest is malformed: {failures[0]['field']}: {failures[0]['message']}")
    entries = manifest["templates"]
    if len({entry["id"] for entry in entries}) != len(entries):
        raise ValueError("gallery manifest contains duplicate entry ids")
    for entry in entries:
        if set(entry["trigger"].get("any_of", [])) - set(manifest["signals"]):
            raise ValueError("gallery manifest trigger contains unknown signals")
        if set(entry["exports"]) - set(manifest["export_kinds"]):
            raise ValueError("gallery manifest entry contains unknown exports")
    drafts = [entry for entry in entries if entry["status"] == "shipped" and entry["stage"] == "draft-pr"]
    if not any(entry["trigger"].get("always") is True for entry in drafts):
        raise ValueError("gallery manifest has no always-selected draft pages")
    return drafts


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
    entries = draft_gallery_entries(content)
    selected = [entry["id"] for entry in entries
                if entry["trigger"].get("always") is True
                or signals.intersection(entry["trigger"].get("any_of", []))]
    directory = Path(inputs["plan_file"]).parent / "artifacts"
    paths = {identifier: artifact_output_path(str(directory / f"{identifier}.html"), root, directory)
             for identifier in selected}
    candidates = inputs.get("candidate_paths", list(paths.values()))
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidate_paths must be a non-empty list of artifact output paths")
    checked = [artifact_output_path(path, root, directory) for path in candidates]
    return {"selected_pages": selected, "output_paths": paths, "checked_paths": checked,
            "signals": sorted(signals), "writes_state": False}


def run_artifact_selection_helper(entry: Any, request: Any) -> dict[str, Any]:
    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    try:
        data = select_artifact_pages(request.inputs, root)
    except INPUT_ERRORS as error:
        return response("input_error", request_id=request.request_id, diagnostics=[diagnostic(
            "artifact_selection_invalid", str(error),
            remediation_summary="Correct the planning inputs or record a whole-set artifact gap.",
            remediation_actions=["Retry selection with readable planning files and the shipped gallery."],
        )])
    return response("ok", request_id=request.request_id, data=data)
