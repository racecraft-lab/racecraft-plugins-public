"""Check the native configuration contract before a checker can override it."""

from __future__ import annotations

import re
from typing import Any

from .catalog import FormalError

TOKEN = re.compile(r'\(\*|\*\)|\\\*[^\n]*|"(?:\\.|[^"\\])*"|[A-Za-z_][A-Za-z0-9_]*')
DIRECTIVES = frozenset("INIT NEXT SPECIFICATION CONSTANT CONSTANTS INVARIANT INVARIANTS PROPERTY PROPERTIES CONSTRAINT CONSTRAINTS ACTION_CONSTRAINT ACTION_CONSTRAINTS SYMMETRY VIEW ALIAS POSTCONDITION CHECK_DEADLOCK".split())


def identifiers(text: str) -> list[str]:
    depth = 0
    words = []
    for match in TOKEN.finditer(text):
        token = match.group()
        if token == "(*":
            depth += 1
        elif token == "*)":
            depth -= 1
        elif depth == 0 and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
            words.append(token)
        if depth < 0:
            raise FormalError("invalid_model", "unmatched native configuration comment")
    if depth:
        raise FormalError("invalid_model", "unterminated native configuration comment")
    return words


def sections(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    current = ""
    for word in identifiers(text):
        if word in DIRECTIVES:
            current = word
            if word in result:
                raise FormalError("invalid_model", f"duplicate configuration directive: {word}")
            result[word] = []
        else:
            result.setdefault(current, []).append(word)
    return result


def validate_apalache(model: dict[str, Any], text: str) -> None:
    directives = sections(text)
    ignored = set(directives) - {"INIT", "NEXT", "CONSTANT", "CONSTANTS", "INVARIANT", "INVARIANTS", "PROPERTY", "PROPERTIES", "CHECK_DEADLOCK"}
    if ignored:
        raise FormalError("unsupported", "Apalache integration requires explicit INIT/NEXT and supported directives; reconcile these settings or use TLC: " + ", ".join(sorted(ignored)))
    for directive in ("INIT", "NEXT"):
        if directives.get(directive) != [model[directive.lower()]]:
            raise FormalError("invalid_model", f"native {directive} must agree with the model catalog")
    for singular, plural, kind in (("INVARIANT", "INVARIANTS", "invariant"), ("PROPERTY", "PROPERTIES", "temporal")):
        configured = directives.get(singular, []) + directives.get(plural, [])
        selected = [name for name, prop in model["properties"].items() if prop["kind"] == kind]
        if configured and sorted(configured) != sorted(selected):
            raise FormalError("invalid_model", f"native {plural} must agree with the complete catalog property mapping")
