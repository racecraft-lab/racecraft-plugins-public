"""Strict input parsing shared by the runner: field checks, unique JSON keys, fence tracking."""

from __future__ import annotations

import re
from typing import Any
from unicodedata import category

# Controls, format characters (bidirectional and zero-width) and line or paragraph separators hide what a reader sees.
HIDDEN_CATEGORIES = frozenset({"Cc", "Cf", "Zl", "Zp"})


class SelectionError(ValueError):
    """An explicit selection is malformed; it must never become disabled."""


def require_fields(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    """Reject missing and unknown fields, including misspelled safety settings."""
    if not isinstance(value, dict):
        raise SelectionError(f"{label} must be an object")
    missing = fields - value.keys()
    extra = value.keys() - fields
    if missing or extra:
        raise SelectionError(f"{label}: missing fields {sorted(missing)}; unknown fields {sorted(extra, key=str)}")
    return value


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SelectionError(f"{label} must be a non-empty string")
    return value


def has_hidden_characters(text: str, *, keep: str = "") -> bool:
    """True when `text` holds a control, format or line separator character other than those in `keep`."""
    return any(char not in keep and category(char) in HIDDEN_CATEGORIES for char in text)


def next_fence(fence: str | None, line: str) -> str | None:
    marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
    if marker is None:
        return fence
    token, suffix = marker.groups()
    if fence is None:
        return token
    if token[0] == fence[0] and len(token) >= len(fence) and not suffix.strip():
        return None
    return fence


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    if len(result) != len(pairs):
        raise SelectionError("duplicate JSON keys are not permitted")
    return result
