#!/usr/bin/env python3
"""Conservative stdlib-only YAML structure checks for GitHub workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CollectionKind = Literal["mapping", "sequence"]
BLOCK_SCALARS = {"|", ">", "|-", ">-", "|+", ">+"}


@dataclass(frozen=True)
class _Collection:
    indent: int
    kind: CollectionKind


@dataclass(frozen=True)
class _NestedValue:
    parent_indent: int
    kind: CollectionKind | None


def _split_mapping(text: str) -> tuple[str, str] | None:
    """Split a block mapping entry at a YAML-significant colon."""
    quote: str | None = None
    escaped = False
    flow: list[str] = []
    pairs = {"]": "[", "}": "{"}

    for index, char in enumerate(text):
        if quote == '"':
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if quote == "'":
            if char == quote:
                if index + 1 < len(text) and text[index + 1] == quote:
                    continue
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
        elif char in "[{":
            flow.append(char)
        elif char in "]}":
            if not flow or flow.pop() != pairs[char]:
                return None
        elif char == ":" and not flow and (index + 1 == len(text) or text[index + 1].isspace()):
            return text[:index], text[index + 1 :]
    return None


def _strip_comment(text: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(text):
        if quote == '"':
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif quote == "'":
            if char == quote:
                if index + 1 < len(text) and text[index + 1] == quote:
                    continue
                quote = None
        elif char in {'"', "'"}:
            quote = char
        elif char == "#" and (index == 0 or text[index - 1].isspace()):
            return text[:index].rstrip()
    return text.rstrip()


def _scalar_sane(text: str) -> bool:
    """Reject unterminated quotes and flow collections in a scalar value."""
    text = _strip_comment(text)
    quote: str | None = None
    escaped = False
    flow: list[str] = []
    pairs = {"]": "[", "}": "{"}

    for index, char in enumerate(text):
        if quote == '"':
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if quote == "'":
            if char == quote:
                if index + 1 < len(text) and text[index + 1] == quote:
                    continue
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
        elif char in "[{":
            flow.append(char)
        elif char in "]}":
            if not flow or flow.pop() != pairs[char]:
                return False
    return quote is None and not flow and not escaped


def yaml_syntax_sane(text: str) -> bool:
    """Check the indentation and scalar surface used by GitHub workflow YAML."""
    collections: list[_Collection] = []
    nested_value: _NestedValue | None = None
    block_parent_indent: int | None = None

    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue

        leading = raw_line[: len(raw_line) - len(raw_line.lstrip(" \t"))]
        if "\t" in leading:
            return False
        indent = len(leading)

        if block_parent_indent is not None:
            if indent > block_parent_indent:
                continue
            block_parent_indent = None

        stripped = raw_line[indent:]
        if stripped.startswith("#"):
            continue
        if stripped in {"---", "..."}:
            if indent != 0:
                return False
            continue

        is_sequence = stripped == "-" or stripped.startswith("- ")
        line_kind: CollectionKind = "sequence" if is_sequence else "mapping"

        while collections and indent < collections[-1].indent:
            collections.pop()
        if not collections:
            if indent != 0 or line_kind != "mapping":
                return False
            collections.append(_Collection(indent, line_kind))
        elif indent == collections[-1].indent:
            if line_kind != collections[-1].kind:
                return False
        else:
            if nested_value is None or nested_value.parent_indent != collections[-1].indent:
                return False
            if nested_value.kind is not None and line_kind != nested_value.kind:
                return False
            collections.append(_Collection(indent, line_kind))

        nested_value = None
        item = stripped[1:].lstrip() if is_sequence else stripped
        if is_sequence and not item:
            nested_value = _NestedValue(indent, None)
            continue

        mapping = _split_mapping(item)
        if mapping is None:
            if not is_sequence or not _scalar_sane(item):
                return False
            continue

        key, value = mapping
        if not key.strip() or not _scalar_sane(value):
            return False

        scalar = _strip_comment(value).strip()
        if scalar in BLOCK_SCALARS:
            block_parent_indent = indent
        elif not scalar:
            nested_value = _NestedValue(indent, None)
        elif is_sequence:
            nested_value = _NestedValue(indent, "mapping")

    return True


__all__ = ("yaml_syntax_sane",)
