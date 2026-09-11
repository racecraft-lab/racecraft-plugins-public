"""Read-only evidence for artifact delivery; browser observation belongs to the parent."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from .formal.selection import next_fence, require_fields, require_text, unique_object

HEADING = "## Artifact Review Handoff"
GALLERY = Path(__file__).resolve().parents[1] / "artifact-gallery"
PREVIEW_STATUSES = ("pending", "verified", "unavailable", "denied")
FileReader = Callable[[Path, Path], bytes | None]


def _comment_line(line: str, inside: bool) -> tuple[str, bool]:
    visible = ""
    while line:
        before, marker, after = line.partition("-->" if inside else "<!--")
        if not inside:
            visible += before
        if not marker:
            break
        inside = not inside
        line = after
    return visible, inside


def _review_blocks(text: str) -> tuple[int, list[str]]:
    """Only a top-level JSON fence in the live section can supply evidence."""
    headings = 0
    selected = False
    blocks: list[str] = []
    body: list[str] | None = None
    fence = None
    comment = False
    for line in text.splitlines():
        if fence is None:
            line, comment = _comment_line(line, comment)
            if re.match(r"^ {0,3}#{1,2}\s+", line):
                selected = line.strip() == HEADING
                headings += int(selected)
            body = [] if selected and line.strip() == "```json" else None
        closing = fence is not None and next_fence(fence, line) is None
        if body is not None and closing:
            blocks.append("\n".join(body))
            body = None
        elif body is not None and fence is not None:
            body.append(line)
        fence = next_fence(fence, line)
    return headings, blocks


def record_from_workflow(text: str) -> dict[str, Any] | None:
    """A present but malformed record cannot be treated as legacy absence."""
    headings, blocks = _review_blocks(text)
    if headings == 0:
        return None
    if headings != 1 or len(blocks) != 1:
        raise ValueError("artifact review requires one section with one top-level JSON record")
    try:
        record = json.JSONDecoder(object_pairs_hook=unique_object).decode(blocks[0])
    except RecursionError as exc:
        raise ValueError("artifact review JSON nesting exceeds the parser limit") from exc
    if not isinstance(record, dict):
        raise ValueError("artifact review record must be an object")
    return record


def _hash(value: Any, label: str, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise ValueError(f"{label} must be a SHA-256 hex digest")


def _relative(value: Any) -> str:
    require_text(value, "artifact review path")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or ".." in path.parts or "\\" in value or ":" in value:
        raise ValueError("artifact review paths must be canonical relative paths")
    if any(part.casefold() == ".git" for part in path.parts):
        raise ValueError("artifact review paths cannot name git metadata")
    return value


def _current_hash(root: Path, relative: str, read_file: FileReader) -> str | None:
    path = root / relative
    if path.resolve() != root.resolve() / relative:
        raise ValueError(f"artifact review path is not canonical within its root: {relative}")
    content = read_file(path, root)
    if content is None:
        if path.exists():
            raise ValueError(f"artifact review file is unreadable: {relative}")
        return None
    return hashlib.sha256(content).hexdigest()


def _observation(value: Any) -> None:
    require_fields(value, {"kind", "title", "body_text", "route", "reference", "observed_at"}, "rendered observation")
    if value["kind"] != "rendered":
        raise ValueError("only a rendered observation can verify a preview")
    for key in ("title", "body_text"):
        if not isinstance(value[key], str):
            raise ValueError(f"observation.{key} must be text")
    for key in ("route", "reference", "observed_at"):
        require_text(value[key], f"observation.{key}")
    if datetime.fromisoformat(value["observed_at"]).tzinfo is None:
        raise ValueError("rendered observation must include a timezone")


def _preview(page: dict[str, Any]) -> None:
    preview = require_fields(page["preview"], {"status", "blocker", "observation"}, "preview")
    if preview["status"] not in PREVIEW_STATUSES:
        raise ValueError(f"preview.status must be one of {PREVIEW_STATUSES}")
    observation = preview["observation"]
    if observation is not None:
        _observation(observation)
    if preview["status"] != "verified":
        require_text(preview["blocker"], "unverified preview blocker")
        return
    if observation is None or preview["blocker"] is not None:
        raise ValueError("verified preview requires rendered evidence and no blocker")
    title = " ".join(page["expected_title"].split())
    content = " ".join(page["expected_content"].split())
    if content in title:
        raise ValueError("feature body content must be distinct from the title")
    if " ".join(observation["title"].split()) != title:
        raise ValueError("rendered title does not match the expected page")
    if content not in " ".join(observation["body_text"].split()):
        raise ValueError("rendered body does not contain the expected feature content")


def _page(page: Any, feature: str) -> None:
    if not isinstance(page, dict) or not isinstance(page.get("id"), str):
        raise ValueError("artifact page must carry an id")
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", page["id"]):
        raise ValueError("invalid artifact id")
    if page.get("generation") == "gap":
        require_fields(page, {"id", "generation", "reason"}, "generation gap")
        require_text(page["reason"], "generation gap reason")
        return
    require_fields(page, {"id", "generation", "path", "sha256", "expected_title", "expected_content", "preview"}, "generated page")
    if page["generation"] != "generated":
        raise ValueError("generation must be generated or gap")
    if _relative(page["path"]) != f"{feature}/artifacts/{page['id']}.html":
        raise ValueError("artifact path does not match its feature and id")
    _hash(page["sha256"], "artifact.sha256")
    require_text(page["expected_title"], "expected title")
    require_text(page["expected_content"], "expected feature body content")
    _preview(page)


def _inputs(inputs: Any, feature: str) -> None:
    required = {f"{feature}/{name}.md" for name in ("spec", "plan", "tasks")}
    if not isinstance(inputs, dict) or not required <= inputs.keys():
        raise ValueError("artifact review must fingerprint spec, plan, and tasks")
    for path, digest in inputs.items():
        _relative(path)
        if path not in required and not re.fullmatch(r"docs/ai/specs/\.process/[^/]+-design-concept\.md", path):
            raise ValueError("artifact review input is not a planning input")
        _hash(digest, f"input {path}", optional=path not in required)


def _outcomes(record: dict[str, Any]) -> None:
    if not isinstance(record["pages"], list) or not isinstance(record["template_hashes"], dict):
        raise ValueError("artifact review requires pages and template_hashes")
    ids = []
    for page in record["pages"]:
        _page(page, record["feature_dir"])
        ids.append(page["id"])
    if len(ids) != len(set(ids)) or set(ids) != record["template_hashes"].keys():
        raise ValueError("artifact ids must be unique and match template_hashes")
    for identifier, digest in record["template_hashes"].items():
        _hash(digest, f"template {identifier}", optional=True)
    if any(page["generation"] == "generated" and record["template_hashes"][page["id"]] is None for page in record["pages"]):
        raise ValueError("generated page requires its template fingerprint")
    if record["generation_error"] is not None:
        require_text(record["generation_error"], "generation_error")
        if ids:
            raise ValueError("whole-set generation error cannot claim page outcomes")
    elif not ids:
        raise ValueError("empty page outcomes require a whole-set generation error")


def _record(value: Any) -> dict[str, Any]:
    record = require_fields(value, {"schema_version", "feature_dir", "input_hashes", "manifest_sha256", "template_hashes", "generation_error", "pages"}, "artifact review")
    if record["schema_version"] != "1.0":
        raise ValueError("unsupported artifact review schema_version")
    feature = _relative(record["feature_dir"])
    if not re.fullmatch(r"specs/[^/]+", feature):
        raise ValueError("artifact review feature_dir must be specs/<feature>")
    _inputs(record["input_hashes"], feature)
    _hash(record["manifest_sha256"], "manifest_sha256")
    _outcomes(record)
    return record


def _inputs_current(record: dict[str, Any], root: Path, read_file: FileReader) -> bool:
    inputs = [_current_hash(root, path, read_file) == digest for path, digest in record["input_hashes"].items()]
    inputs.append(_current_hash(GALLERY, "manifest.json", read_file) == record["manifest_sha256"])
    for identifier, digest in record["template_hashes"].items():
        inputs.append(_current_hash(GALLERY, f"templates/{identifier}.html", read_file) == digest)
    return all(inputs)


def _selection(record: dict[str, Any], read_file: FileReader) -> None:
    """The parent records the author's selection; it cannot omit always-selected pages."""
    content = read_file(GALLERY / "manifest.json", GALLERY)
    if content is None or hashlib.sha256(content).hexdigest() != record["manifest_sha256"]:
        return  # A changed gallery is stale input, not a malformed historical record.
    entries = [entry for entry in json.loads(content)["templates"] if entry["stage"] == "draft-pr"]
    ids = {page["id"] for page in record["pages"]}
    mandatory = {entry["id"] for entry in entries if entry["trigger"].get("always")}
    if record["generation_error"] is None and not mandatory <= ids:
        raise ValueError("artifact review omits an always-selected page")
    if not ids <= {entry["id"] for entry in entries}:
        raise ValueError("artifact review includes a non-draft artifact")


def _page_results(record: dict[str, Any], root: Path, read_file: FileReader) -> tuple[list[dict[str, Any]], list[str], bool]:
    inputs_current = _inputs_current(record, root, read_file)
    fresh = inputs_current
    pages = []
    gaps = []
    for page in record["pages"]:
        path = f"{record['feature_dir']}/artifacts/{page['id']}.html"
        digest = _current_hash(root, path, read_file)
        if page["generation"] == "gap":
            gaps.append(page["id"])
            fresh = fresh and digest is None
            continue
        current = digest == page["sha256"]
        fresh = fresh and current
        preview = page["preview"]
        result = {"id": page["id"], "path": path, "status": preview["status"], "blocker": preview["blocker"]}
        if not inputs_current or not current:
            if preview["status"] != "denied":
                result.update(status="pending", blocker="Generation inputs or artifact bytes changed; revalidate generation")
        pages.append(result)
    return pages, gaps, fresh


def review_handoff(text: str, root: Path, read_file: FileReader) -> dict[str, Any]:
    """Classify current evidence without opening browsers, writing, or deleting artifacts."""
    value = record_from_workflow(text)
    if value is None:
        return {"status": "absent", "resume_action": "none", "reuse_artifacts": False}
    record = _record(value)
    _selection(record, read_file)
    pages, gaps, fresh = _page_results(record, root, read_file)
    verified = sum(page["status"] == "verified" for page in pages)
    status = "not_applicable" if not pages else "pending" if not fresh or verified != len(pages) else "verified"
    return {
        "status": status, "resume_action": "generate" if not fresh else "preview" if status == "pending" else "none",
        "reuse_artifacts": fresh, "feature_dir": record["feature_dir"], "generated": len(pages),
        "verified": verified, "pages": pages, "generation_gaps": gaps, "generation_error": record["generation_error"],
    }
