"""Shared helpers for structural validation scripts."""

from __future__ import annotations


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
