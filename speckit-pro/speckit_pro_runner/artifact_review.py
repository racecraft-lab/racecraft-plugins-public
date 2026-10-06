"""Read-only evidence for artifact delivery; browser observation belongs to the parent."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any

from .strict_input import next_fence, require_fields, require_text, unique_object

HEADING = "## Artifact Review Handoff"
GALLERY = Path(__file__).resolve().parents[1] / "artifact-gallery"
PREVIEW_STATUSES = ("pending", "verified", "unavailable", "denied")
BROKERED_PREVIEW_VERDICTS = ("verified", "unavailable", "denied")
OBSERVER = "artifact-preview-observer"
# What the readiness record says about the host (ADR 0019); only `unavailable` is evidence of no surface.
PREVIEW_SURFACES = ("available", "unavailable", "unknown")
NO_SURFACE_NOTE = "preview unavailable: the readiness record shows no preview surface"
# The broker stamps observed_at itself; allow only ordinary clock skew beyond now.
OBSERVATION_CLOCK_SKEW = timedelta(minutes=5)
FILL_MARKER = re.compile(rb"<!--\s*FILL:([a-z0-9-]+):(START|END)\s*-->")
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


def _fill_skeleton(value: bytes) -> tuple[tuple[str, ...], tuple[bytes, ...], tuple[bytes, ...]]:
    matches = list(FILL_MARKER.finditer(value))
    if len(matches) % 2:
        raise ValueError("artifact template has an unmatched fill marker")
    slots: list[str] = []
    static: list[bytes] = []
    fills: list[bytes] = []
    cursor = 0
    for index in range(0, len(matches), 2):
        start, end = matches[index], matches[index + 1]
        if start.group(2) != b"START" or end.group(2) != b"END" or start.group(1) != end.group(1):
            raise ValueError("artifact template has an invalid fill marker")
        slots.append(start.group(1).decode("ascii"))
        static.append(value[cursor:start.end()])
        fills.append(value[start.end():end.start()])
        cursor = end.start()
    static.append(value[cursor:])
    return tuple(slots), tuple(static), tuple(fills)


# Tags and attributes are judged by a parser: escaped planning text holds no raw "<",
# so every tag in a fill is author structure the parser can see. The two patterns
# below only reject constructs where Python's parser and a browser disagree.
# Unicode \s on purpose: Python 3.11 closes a comment at "--" + any Unicode space + ">".
_UNPARSEABLE_FILL = re.compile(r"<!(?!--)|<\?|<!---?>|--!>|--\s+>")
# A browser ends these elements at their own end tag even where a parser sees an attribute value.
# Browsers fold tag names over ASCII only, so every case-insensitive match here is re.ASCII.
_RAW_TEXT_START = re.compile(
    r"<(title|textarea|noscript|xmp|noembed|noframes|plaintext|script|style|iframe)(?=[\t\n\f\r />])",
    re.IGNORECASE | re.ASCII,
)
_ACTIVE_ELEMENTS = frozenset({
    "script", "style", "iframe", "frame", "frameset", "object", "embed", "applet", "base", "meta", "link", "portal",
})
_URL_ATTRIBUTES = frozenset({"href", "xlink:href", "src", "srcset", "action", "formaction", "poster", "data", "background", "cite"})
_URL_IGNORED = "".join(chr(code) for code in range(0x21))
_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def _script_url(value: str) -> bool:
    """Browsers drop tabs and newlines and trim C0 controls before reading a URL scheme."""
    url = re.sub(r"[\t\n\r]", "", value).strip(_URL_IGNORED).translate(_ASCII_LOWER)
    if url.startswith("data:"):
        return not url.startswith(("data:image/", "data:font/"))
    return url.startswith(("javascript:", "vbscript:"))


class _FillMarkup(HTMLParser):
    """Collects active content in one fill region; build it with convert_charrefs=False so "&lt;" stays text."""

    findings: list[str]
    start_positions: set[tuple[int, int]]

    def reset(self) -> None:
        super().reset()
        self.findings = []
        self.start_positions = set()

    def set_cdata_mode(self, *args: object, **kwargs: object) -> None:
        """Never hide text from inspection: raw-text rules differ inside SVG and across Python versions."""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.start_positions.add(self.getpos())
        if tag in _ACTIVE_ELEMENTS:
            self.findings.append(f"<{tag}> element")
        for name, value in attrs:
            if name.startswith("on") or name == "srcdoc":
                self.findings.append(f"{name} attribute")
            elif name in _URL_ATTRIBUTES and value is not None and _script_url(value):
                self.findings.append(f"script URL in {name}")
            elif name == "attributename" and value is not None:
                target = value.translate(_ASCII_LOWER)
                if target in ("href", "xlink:href") or target.startswith("on"):
                    self.findings.append("animated link or event attribute")

    def handle_data(self, data: str) -> None:
        if "<" in data:
            self.findings.append("unescaped <")


def _raw_text_holds_markup(text: str, start_positions: set[tuple[int, int]]) -> bool:
    """A raw-text element is inert only when it closes in the same region with no "<" before its end tag."""
    for start in _RAW_TEXT_START.finditer(text):
        position = (text.count("\n", 0, start.start()) + 1, start.start() - text.rfind("\n", 0, start.start()) - 1)
        # Tag-shaped text inside a parsed comment or attribute is not an element.
        if position not in start_positions:
            continue
        following = text.find("<", start.end())
        end = re.compile(rf"</{start.group(1)}[\t\n\f\r />]", re.IGNORECASE | re.ASCII)
        if following < 0 or not end.match(text, following):
            return True
    return False


def _active_content(fill: bytes) -> list[str]:
    text = fill.decode("utf-8", errors="replace")
    findings = ["markup declaration or nonstandard comment"] if _UNPARSEABLE_FILL.search(text) else []
    parser = _FillMarkup(convert_charrefs=False)
    parser.feed(text)
    if _raw_text_holds_markup(text, parser.start_positions):
        findings.append("raw-text element holding markup")
    if "<" in parser.rawdata:
        findings.append("unterminated markup")
    return findings + parser.findings


def _generation_provenance(page: dict[str, Any], root: Path, read_file: FileReader) -> None:
    template = read_file(GALLERY / f"templates/{page['id']}.html", GALLERY)
    artifact = read_file(root / page["path"], root)
    if template is None or artifact is None:
        raise ValueError(f"artifact preview provenance is unreadable: {page['id']}")
    template_slots, template_static, _template_fills = _fill_skeleton(template)
    artifact_slots, artifact_static, artifact_fills = _fill_skeleton(artifact)
    if template_slots != artifact_slots or template_static != artifact_static:
        raise ValueError(f"artifact preview is not a trusted fill of its template: {page['id']}")
    for slot, fill in zip(artifact_slots, artifact_fills, strict=True):
        findings = _active_content(fill)
        if findings:
            raise ValueError(f"artifact fill carries active content: {page['id']} region {slot}: {', '.join(findings)}")


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
    require_fields(value, {"kind", "verdict", "artifact_sha256", "observed_at"}, "brokered preview observation")
    if value["kind"] != "brokered":
        raise ValueError("only a brokered preview observation can verify a preview")
    if value["verdict"] not in BROKERED_PREVIEW_VERDICTS:
        raise ValueError("brokered preview verdict is outside the closed vocabulary")
    _hash(value["artifact_sha256"], "observation.artifact_sha256")
    require_text(value["observed_at"], "observation.observed_at")
    observed_at = datetime.fromisoformat(value["observed_at"])
    if observed_at.tzinfo is None:
        raise ValueError("brokered preview observation must include a timezone")
    if observed_at > datetime.now(timezone.utc) + OBSERVATION_CLOCK_SKEW:
        raise ValueError("brokered preview observation time is in the future")


def _preview(page: dict[str, Any]) -> None:
    preview = require_fields(page["preview"], {"status", "blocker", "observation"}, "preview")
    if preview["status"] not in PREVIEW_STATUSES:
        raise ValueError(f"preview.status must be one of {PREVIEW_STATUSES}")
    observation = preview["observation"]
    if observation is not None:
        _observation(observation)
        if observation["verdict"] != preview["status"]:
            raise ValueError("brokered preview verdict does not match preview status")
    if preview["status"] == "pending" and observation is not None:
        raise ValueError("pending preview cannot carry brokered evidence")
    if preview["status"] != "verified":
        require_text(preview["blocker"], "unverified preview blocker")
        return
    if observation is None or preview["blocker"] is not None:
        raise ValueError("verified preview requires brokered evidence and no blocker")
    title = " ".join(page["expected_title"].split())
    content = " ".join(page["expected_content"].split())
    if content in title:
        raise ValueError("feature body content must be distinct from the title")
    if observation["artifact_sha256"] != page["sha256"]:
        raise ValueError("brokered preview artifact digest does not match the generated page")


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


def _page_preview(page: dict[str, Any], generation_current: bool, preview_surface: str) -> dict[str, Any]:
    """Retain denials and require current broker evidence for terminal unavailability.

    With no preview surface no observer can add evidence, so a current page that is not
    verified or denied ends as `unavailable` without one.
    """
    preview = page["preview"]
    result = {"id": page["id"], "path": page["path"], "status": preview["status"], "blocker": preview["blocker"]}
    if not generation_current:
        if preview["status"] != "denied":
            result.update(status="pending", blocker="Generation inputs or artifact bytes changed; revalidate generation")
    elif preview_surface == "unavailable" and preview["status"] in ("pending", "unavailable"):
        result.update(status="unavailable", blocker=NO_SURFACE_NOTE)
    elif preview["status"] == "unavailable":
        observation = preview["observation"]
        if observation is None or observation["artifact_sha256"] != page["sha256"]:
            result.update(status="pending")
    return result


def _page_results(record: dict[str, Any], root: Path, read_file: FileReader,
                  preview_surface: str) -> tuple[list[dict[str, Any]], list[str], bool]:
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
        if current:
            _generation_provenance(page, root, read_file)
        fresh = fresh and current
        pages.append(_page_preview(page, inputs_current and current, preview_surface))
    return pages, gaps, fresh


def review_handoff(text: str, root: Path, read_file: FileReader, preview_surface: str = "unknown") -> dict[str, Any]:
    """Classify current evidence without opening browsers, writing, or deleting artifacts.

    `observer_dispatches` names the pages that still need one observer each: none without a
    preview surface, and none until stale pages are regenerated.
    """
    if preview_surface not in PREVIEW_SURFACES:
        raise ValueError(f"preview_surface must be one of {PREVIEW_SURFACES}")
    value = record_from_workflow(text)
    if value is None:
        return {"status": "absent", "resume_action": "none", "reuse_artifacts": False}
    record = _record(value)
    _selection(record, read_file)
    pages, gaps, fresh = _page_results(record, root, read_file, preview_surface)
    verified = sum(page["status"] == "verified" for page in pages)
    delivered = sum(page["status"] in ("verified", "unavailable") for page in pages)
    if not pages:
        status = "not_applicable"
    elif not fresh or delivered != len(pages):
        status = "pending"
    elif verified == len(pages):
        status = "verified"
    else:
        status = "unavailable"
    dispatches = [page["id"] for page in pages if fresh and page["status"] == "pending"]
    return {
        "status": status, "resume_action": "generate" if not fresh else "preview" if status == "pending" else "none",
        "reuse_artifacts": fresh, "feature_dir": record["feature_dir"], "generated": len(pages),
        "verified": verified, "pages": pages, "generation_gaps": gaps, "generation_error": record["generation_error"],
        "observer": OBSERVER if dispatches else None, "observer_dispatches": dispatches,
        **({"preview_note": NO_SURFACE_NOTE} if preview_surface == "unavailable" and pages and fresh else {}),
    }
