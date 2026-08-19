"""Shared helpers for structural validation scripts."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path


# Keywords whose value is itself a schema, a list of schemas, or a mapping of
# names to schemas. Walking only these avoids mistaking a ``const`` payload or a
# property named after a keyword for a schema node.
_SCHEMA_MAP_KEYWORDS = ("properties", "$defs", "patternProperties")
_SCHEMA_KEYWORDS = ("items", "not", "if", "then", "else", "additionalProperties", "propertyNames", "contains")
_SCHEMA_LIST_KEYWORDS = ("allOf", "anyOf", "oneOf", "prefixItems")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_subschemas(schema: object) -> Iterator[dict[str, object]]:
    """Yield every schema node in a JSON Schema document, the root included."""
    stack: list[object] = [schema]
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        yield node
        for keyword in _SCHEMA_MAP_KEYWORDS:
            container = node.get(keyword)
            if isinstance(container, dict):
                stack.extend(container.values())
        for keyword in _SCHEMA_KEYWORDS:
            stack.append(node.get(keyword))
        for keyword in _SCHEMA_LIST_KEYWORDS:
            branch = node.get(keyword)
            if isinstance(branch, list):
                stack.extend(branch)


def open_object_nodes(schema: object) -> list[list[str]]:
    """Member lists of every object node that fails to close its member set."""
    return [
        sorted(node.get("properties", {}))
        for node in iter_subschemas(schema)
        if node.get("type") == "object" and node.get("additionalProperties") is not False
    ]


def declared_refs(schema: object) -> list[str]:
    return sorted({
        node["$ref"] for node in iter_subschemas(schema) if isinstance(node.get("$ref"), str)
    })


def field_exists(data: object, dotted: str) -> bool:
    """Walk ``a.b.c`` keys without raising."""
    current = data
    try:
        for key in dotted.split("."):
            current = current[key]  # type: ignore[index]
    except (KeyError, TypeError, IndexError):
        return False
    return True


def nested(data: object, *keys: object) -> object | None:
    """Return ``data[k0][k1]...`` or ``None`` if any hop is missing."""
    current = data
    try:
        for key in keys:
            current = current[key]  # type: ignore[index]
    except (KeyError, TypeError, IndexError):
        return None
    return current


def frontmatter(lines: list[str]) -> str:
    """Lines between the first and second ``---`` fence, exclusive."""
    out: list[str] = []
    fences = 0
    for line in lines:
        if line == "---":
            fences += 1
            if fences == 1:
                continue
            if fences == 2:
                break
        elif fences == 1:
            out.append(line)
    return "\n".join(out)


def body(lines: list[str]) -> str:
    """Everything after the second ``---`` fence."""
    out: list[str] = []
    fences = 0
    found = False
    for line in lines:
        if line == "---":
            fences += 1
            if fences == 2:
                found = True
                continue
        if found:
            out.append(line)
    return "\n".join(out)


COMMAND_KEYS = ("command", "commandWindows", "command_windows")


def declared_hook_commands(data: object) -> list[str]:
    """Every non-empty command string declared under any hook event, at any depth.

    Event names are never hard-coded: the walk visits every value under the
    top-level ``hooks`` map, so a newly registered event is covered the day it
    lands rather than the day someone remembers to extend a list. Codex's
    Windows override keys count as commands too.
    """
    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key in COMMAND_KEYS:
                value = node.get(key)
                if isinstance(value, str) and value.strip():
                    found.append(f"{key}={value}")
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data.get("hooks") if isinstance(data, dict) else None)
    return found
