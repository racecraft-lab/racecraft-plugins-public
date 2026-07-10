#!/usr/bin/env python3
"""Extract, sanitize, and validate consumer-facing release-note content."""

from __future__ import annotations

import html
import json
import os
import re
import urllib.parse
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Mapping

MAX_NOTE_CHARS = 2_000
MAX_FALLBACK_CHARS = 250
TRUNCATION_MARKER = "\n\n[release note truncated at 2,000 characters]"
SKIP_LABEL = "release-note/skip"
MARKUP_BOUNDARY = "\x00"

TRAILING_PR_RE = re.compile(r"\(#(?P<number>[1-9][0-9]*)\)[ \t]*$")
CONVENTIONAL_PREFIX_RE = re.compile(
    r"^(?P<kind>[A-Za-z][A-Za-z0-9-]*)(?:\([^\r\n)]+\))?!?:[ \t]*"
)
FENCE_RE = re.compile(
    r"^(?P<indent> {0,3})"
    r"(?:(?P<marker>[-+*]|[0-9]{1,9}[.)])(?P<marker_space>[ \t]+))?"
    r"(?P<fence>`{3,}|~{3,})(?P<info>[^\r\n]*)$"
)
BLOCKQUOTE_RE = re.compile(r"^(?P<prefix>(?:>[ \t]?)+)")
BULLET_LIST_RE = re.compile(r"^(?P<marker>[-+*])(?=[ \t]+)")
ORDERED_LIST_RE = re.compile(r"^(?P<number>[0-9]{1,9})(?P<delimiter>[.)])(?=[ \t]+)")
ATX_HEADING_RE = re.compile(r"^(?P<marker>#{1,6})(?=[ \t]|$)")


class CompositionError(RuntimeError):
    """A fail-loud release-note composition error."""


@dataclass(frozen=True)
class DiscoveredCommit:
    """One compare commit and its required trailing pull request reference."""

    pr_number: int
    subject: str
    kind: str


@dataclass(frozen=True)
class _FenceOpening:
    character: str
    length: int
    quote_depth: int
    body_indent: int
    container_indent: int
    info: str


@dataclass(frozen=True)
class _InlineLink:
    label: str
    destination: str
    end: int


class _RawHtmlStripper(HTMLParser):
    """Keep text while dropping raw HTML markup and tag attributes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, _tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        self.parts.append(MARKUP_BOUNDARY)

    def handle_startendtag(self, _tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        self.parts.append(MARKUP_BOUNDARY)

    def handle_endtag(self, _tag: str) -> None:
        self.parts.append(MARKUP_BOUNDARY)

    def handle_comment(self, _data: str) -> None:
        self.parts.append(MARKUP_BOUNDARY)

    def handle_decl(self, _decl: str) -> None:
        self.parts.append(MARKUP_BOUNDARY)

    def unknown_decl(self, _data: str) -> None:
        self.parts.append(MARKUP_BOUNDARY)

    def handle_pi(self, _data: str) -> None:
        self.parts.append(MARKUP_BOUNDARY)


def _strip_quote_prefix(line: str, depth: int | None = None) -> tuple[str, int] | None:
    rest = line
    count = 0
    while depth is None or count < depth:
        match = re.match(r"^ {0,3}>[ \t]?", rest)
        if match is None:
            break
        rest = rest[match.end() :]
        count += 1
    if depth is not None and count != depth:
        if line.strip() == "":
            return "", count
        return None
    return rest, count


def _opening_fence(line: str) -> _FenceOpening | None:
    quoted = _strip_quote_prefix(line)
    if quoted is None:
        return None
    rest, quote_depth = quoted
    match = FENCE_RE.fullmatch(rest)
    if match is None:
        return None
    fence = match.group("fence")
    info = match.group("info").strip(" \t")
    if fence[0] == "`" and "`" in info:
        return None
    marker = match.group("marker") or ""
    marker_space = match.group("marker_space") or ""
    body_indent = len(match.group("indent")) + len(marker) + len(marker_space)
    container_indent = body_indent if marker else 0
    return _FenceOpening(
        fence[0],
        len(fence),
        quote_depth,
        body_indent,
        container_indent,
        info,
    )


def _container_content(line: str, opening: _FenceOpening) -> str | None:
    quoted = _strip_quote_prefix(line, opening.quote_depth)
    if quoted is None:
        return None
    rest, _depth = quoted
    leading_spaces = len(rest) - len(rest.lstrip(" "))
    if opening.container_indent and leading_spaces < opening.container_indent:
        return "" if not rest.strip() else None
    removable = min(opening.body_indent, leading_spaces)
    return rest[removable:]


def _is_closing_fence(line: str, opening: _FenceOpening) -> bool:
    quoted = _strip_quote_prefix(line, opening.quote_depth)
    if quoted is None:
        return False
    content, _depth = quoted
    leading_spaces = len(content) - len(content.lstrip(" "))
    if leading_spaces < opening.container_indent:
        return False
    content = content[opening.container_indent :]
    match = re.fullmatch(rf" {{0,3}}({re.escape(opening.character)}{{{opening.length},}})[ \t]*", content)
    return match is not None


def extract_release_note(pr_body: str) -> str | None:
    """Return one top-level release-note fence body, or missing on ambiguity."""
    lines = pr_body.splitlines()
    matches: list[str] = []
    malformed = False
    index = 0
    while index < len(lines):
        opening = _opening_fence(lines[index])
        if opening is None:
            index += 1
            continue

        body_lines: list[str] = []
        close_index: int | None = None
        for candidate_index in range(index + 1, len(lines)):
            candidate = lines[candidate_index]
            if _is_closing_fence(candidate, opening):
                close_index = candidate_index
                break
            content = _container_content(candidate, opening)
            if content is None:
                if opening.info == "release-note":
                    malformed = True
                break
            body_lines.append(content)
        if close_index is None:
            if opening.info == "release-note":
                malformed = True
            # An unclosed enclosing fence owns the remainder of the document;
            # never reinterpret a nested example as a release-note block.
            break
        if opening.info == "release-note":
            matches.append("\n".join(body_lines).strip())
        index = close_index + 1

    if malformed or len(matches) != 1 or not matches[0].strip():
        return None
    return matches[0]


def _decode_html_entities(text: str) -> str:
    """Decode nested entities before unsafe-construct recognition."""
    decoded = text
    for _attempt in range(16):
        candidate = html.unescape(decoded)
        if candidate == decoded:
            break
        decoded = candidate
    return decoded


def _remove_markup_boundaries(text: str) -> str:
    """Drop parser sentinels before image recognition runs."""
    return text.replace(MARKUP_BOUNDARY, "")


def _strip_raw_html(text: str) -> str:
    parser = _RawHtmlStripper()
    try:
        parser.feed(text)
        parser.close()
    except Exception as error:  # HTMLParser can surface malformed entity edge cases.
        raise CompositionError(f"release note HTML parsing failed: {error}") from error
    return _remove_markup_boundaries("".join(parser.parts))


def _escape_markers(text: str, marker: str) -> str:
    return text.replace(marker, f"\\{marker}")


def _thematic_break_marker(line: str) -> str | None:
    compact = line.replace(" ", "").replace("\t", "")
    if len(compact) >= 3 and compact[0] in "-*_" and compact == compact[0] * len(compact):
        return compact[0]
    return None


def _neutralize_block_structure(line: str) -> str:
    """Render one prose line without permitting Markdown block structure."""
    line = line.strip(" \t")
    if not line:
        return ""

    blockquote = BLOCKQUOTE_RE.match(line)
    if blockquote is not None:
        prefix = blockquote.group("prefix")
        return _escape_markers(prefix, ">") + line[blockquote.end() :]

    thematic_marker = _thematic_break_marker(line)
    if thematic_marker is not None:
        return _escape_markers(line, thematic_marker)
    setext = re.fullmatch(r"(?P<marker>=+|-+)", line)
    if setext is not None:
        return _escape_markers(line, setext.group("marker")[0])

    ordered = ORDERED_LIST_RE.match(line)
    if ordered is not None:
        return (
            f"{ordered.group('number')}\\{ordered.group('delimiter')}"
            f"{line[ordered.end():]}"
        )
    bullet = BULLET_LIST_RE.match(line)
    if bullet is not None:
        return f"\\{bullet.group('marker')}{line[bullet.end():]}"
    heading = ATX_HEADING_RE.match(line)
    if heading is not None:
        return _escape_markers(heading.group("marker"), "#") + line[heading.end() :]
    return line


def _balanced_markdown_end(text: str, start: int, opening: str, closing: str) -> int | None:
    """Return the closing delimiter index for one balanced inline construct."""
    depth = 1
    index = start + 1
    while index < len(text):
        character = text[index]
        if character == "\\" and index + 1 < len(text):
            index += 2
            continue
        if character == opening:
            depth += 1
        elif character == closing:
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _plain_link_label(label: str) -> bool:
    if not label.strip():
        return False
    forbidden = "[]\\`~|$"
    return not any(character in forbidden or ord(character) < 32 or ord(character) == 127 for character in label)


def _validated_http_url(destination: str) -> bool:
    if not destination or any(
        character.isspace()
        or ord(character) < 32
        or ord(character) == 127
        or character in "\\<>`|"
        for character in destination
    ):
        return False
    if re.match(r"(?i)^https?://", destination) is None:
        return False
    try:
        parsed = urllib.parse.urlsplit(destination)
        hostname = parsed.hostname
        _port = parsed.port
    except ValueError:
        return False
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc) and hostname is not None


def _escape_inline_fragment(text: str) -> str:
    escaped: list[str] = []
    for character in text:
        if character in "\\`~|$[]":
            escaped.append("\\")
        escaped.append(character)
    return "".join(escaped)


def _sanitize_inline_markdown(line: str) -> str:
    """Keep emphasis and validated inline links; render other inline syntax inert."""
    parts: list[str] = []
    index = 0
    while index < len(line):
        character = line[index]
        if character == "[":
            label_end = _balanced_markdown_end(line, index, "[", "]")
            if label_end is None:
                parts.append(_escape_inline_fragment(line[index:]))
                break
            if label_end + 1 >= len(line) or line[label_end + 1] != "(":
                parts.append(_escape_inline_fragment(line[index : label_end + 1]))
                index = label_end + 1
                continue
            destination_end = _balanced_markdown_end(line, label_end + 1, "(", ")")
            if destination_end is None:
                parts.append(_escape_inline_fragment(line[index:]))
                break
            link = _InlineLink(
                label=line[index + 1 : label_end],
                destination=line[label_end + 2 : destination_end],
                end=destination_end + 1,
            )
            if _plain_link_label(link.label) and _validated_http_url(link.destination):
                parts.append(line[index : link.end])
            else:
                parts.append(_escape_inline_fragment(link.label))
            index = link.end
            continue
        elif character == "]":
            parts.append("\\]")
        elif character in "\\`~|$":
            parts.append(f"\\{character}")
        else:
            parts.append(character)
        index += 1
    return "".join(parts)


def _escape_html_text(text: str) -> str:
    """Escape characters that can begin HTML while retaining inert prose `>`."""
    return text.replace("&", "&amp;").replace("<", "&lt;")


def _image_markdown_end(text: str, start: int) -> int | None:
    """Return the exclusive end of one complete inline Markdown image."""
    index = start + 2
    alt_depth = 1
    while index < len(text):
        if text[index] == "\\" and index + 1 < len(text):
            index += 2
            continue
        if text[index] == "[":
            alt_depth += 1
        elif text[index] == "]":
            alt_depth -= 1
            if alt_depth == 0:
                break
        index += 1
    else:
        return None

    if index + 1 >= len(text) or text[index + 1] != "(":
        return None

    depth = 1
    index += 2
    while index < len(text):
        if text[index] == "\\" and index + 1 < len(text):
            index += 2
            continue
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return None


def _strip_image_markdown(text: str) -> str:
    """Remove complete inline images without consuming malformed constructs."""
    parts: list[str] = []
    cursor = 0
    while cursor < len(text):
        start = text.find("![", cursor)
        if start < 0:
            parts.append(text[cursor:])
            break

        end = _image_markdown_end(text, start)
        if end is None:
            parts.append(text[cursor : start + 2])
            cursor = start + 2
            continue

        parts.append(text[cursor:start])
        previous = text[start - 1] if start > 0 else ""
        following = text[end] if end < len(text) else ""
        if previous and following and not previous.isspace() and not following.isspace():
            parts.append(" ")
        cursor = end
    return "".join(parts)


def sanitize_release_note(note: str) -> str:
    """Strip unsafe public-body constructs and enforce the 2,000-char cap."""
    decoded = _decode_html_entities(note.replace(MARKUP_BOUNDARY, " "))
    without_html = _strip_raw_html(decoded)
    without_images = _strip_image_markdown(without_html)
    sanitized_lines = []
    for line in without_images.splitlines():
        inline = _sanitize_inline_markdown(line.strip(" \t"))
        block_safe = _neutralize_block_structure(inline)
        sanitized_lines.append(_escape_html_text(block_safe))
    sanitized = "\n".join(sanitized_lines).strip()
    if len(sanitized) > MAX_NOTE_CHARS:
        sanitized = sanitized[: MAX_NOTE_CHARS - len(TRUNCATION_MARKER)] + TRUNCATION_MARKER
    return sanitized


def deprefix_title(title: str) -> str:
    """Remove a conventional prefix and trailing squash PR marker."""
    without_pr = TRAILING_PR_RE.sub("", title.strip()).rstrip()
    return CONVENTIONAL_PREFIX_RE.sub("", without_pr, count=1).strip()


def sanitize_fallback_subject(subject: str) -> str:
    """Render one immutable Compare subject within the fallback ceiling."""
    without_pr = TRAILING_PR_RE.sub("", subject.strip()).rstrip()
    fallback = CONVENTIONAL_PREFIX_RE.sub("", without_pr, count=1).strip()
    if not fallback:
        fallback = without_pr
    sanitized = sanitize_release_note(fallback)
    if not sanitized:
        raise CompositionError("compare commit subject fallback is empty after sanitization")
    if len(sanitized) > MAX_FALLBACK_CHARS:
        sanitized = sanitized[: MAX_FALLBACK_CHARS - 3] + "..."
    return sanitized


def _label_names(pr: Mapping[str, object]) -> set[str]:
    labels = pr.get("labels", [])
    if not isinstance(labels, list):
        raise CompositionError("pull request labels are not a list")
    names: set[str] = set()
    for label in labels:
        if isinstance(label, str):
            names.add(label)
        elif isinstance(label, dict) and isinstance(label.get("name"), str):
            names.add(label["name"])
    return names


def validate_release_note(
    title: str,
    body: str,
    labels: set[str],
    *,
    draft: bool,
) -> tuple[bool, str]:
    """Apply the required-check contract to one pull request."""
    if draft:
        return True, "draft pull request"
    if any(label.startswith("autorelease:") for label in labels):
        return True, "release-please pull request"
    prefix = CONVENTIONAL_PREFIX_RE.match(title.strip())
    kind = prefix.group("kind").lower() if prefix else ""
    if kind not in {"feat", "fix"}:
        return True, "non-releasable conventional-commit type"
    if SKIP_LABEL in labels:
        return True, f"{SKIP_LABEL} exemption"
    if not deprefix_title(title):
        return False, "feat/fix pull request title is empty after normalization"
    extracted = extract_release_note(body)
    if extracted is None:
        return False, "feat/fix pull requests require exactly one non-empty release-note fence"
    if not sanitize_release_note(extracted):
        return False, "release-note fence is empty after sanitization"
    return True, "valid release-note fence"


def _validation_inputs_from_environment() -> tuple[str, str, set[str], bool]:
    title = os.environ.get("PR_TITLE", "")
    if not title.strip():
        raise CompositionError("PR_TITLE is required for --validate-pr")
    body = os.environ.get("PR_BODY", "")
    raw_labels = os.environ.get("PR_LABELS_JSON", "[]")
    try:
        labels_value = json.loads(raw_labels)
    except json.JSONDecodeError as error:
        raise CompositionError("PR_LABELS_JSON must be a JSON array") from error
    if not isinstance(labels_value, list) or not all(isinstance(label, str) for label in labels_value):
        raise CompositionError("PR_LABELS_JSON must be a JSON array of strings")
    draft_value = os.environ.get("PR_DRAFT", "false").strip().lower()
    if draft_value not in {"true", "false"}:
        raise CompositionError("PR_DRAFT must be true or false")
    return title, body, set(labels_value), draft_value == "true"


__all__ = (
    "CompositionError",
    "CONVENTIONAL_PREFIX_RE",
    "DiscoveredCommit",
    "MAX_FALLBACK_CHARS",
    "MAX_NOTE_CHARS",
    "SKIP_LABEL",
    "TRAILING_PR_RE",
    "TRUNCATION_MARKER",
    "deprefix_title",
    "extract_release_note",
    "sanitize_fallback_subject",
    "sanitize_release_note",
    "validate_release_note",
)
