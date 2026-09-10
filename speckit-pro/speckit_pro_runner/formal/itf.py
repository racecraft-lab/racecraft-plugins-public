"""Strict ITF values and lossless TLA+ literals for observed finite traces."""

from __future__ import annotations

import json
import re
from typing import Any

from .catalog import FormalError, operator


def literal(value: Any, depth: int = 0) -> str:
    if depth > 32:
        raise FormalError("malformed_trace", "ITF values exceed the supported nesting depth")
    if type(value) is bool:
        return "TRUE" if value else "FALSE"
    if isinstance(value, str):
        if any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise FormalError("unsupported", "Trace strings must contain printable Unicode characters")
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "<<" + ", ".join(literal(v, depth + 1) for v in value) + ">>"
    if not isinstance(value, dict) or not value:
        raise FormalError("malformed_trace", "ITF values cannot be null, JSON numbers, or empty records; encode all integers as #bigint")
    if "#bigint" in value:
        text = value["#bigint"]
        if set(value) != {"#bigint"} or not isinstance(text, str) or not re.fullmatch(r"-?(?:0|[1-9][0-9]{0,999})", text):
            raise FormalError("malformed_trace", "ITF #bigint must contain one canonical decimal string of at most 1000 digits")
        return str(int(text))
    if set(value) == {"#tup"} and isinstance(value["#tup"], list):
        return literal(value["#tup"], depth + 1)
    if set(value) == {"#set"} and isinstance(value["#set"], list):
        return "{" + ", ".join(sorted(set(literal(v, depth + 1) for v in value["#set"]))) + "}"
    if set(value) == {"#map"} and isinstance(value["#map"], list):
        return map_literal(value["#map"], depth)
    if any(key.startswith("#") for key in value):
        raise FormalError("unsupported", "Unsupported ITF value tag")
    if set(value) == {"tag", "value"}:
        raise FormalError("unsupported", "ITF variants need a separately qualified adapter; they are not ordinary records")
    fields = [operator(key) + " |-> " + literal(v, depth + 1) for key, v in sorted(value.items())]
    return "[" + ", ".join(fields) + "]"


def map_literal(pairs: list[Any], depth: int) -> str:
    rendered = {}
    for pair in pairs:
        if not isinstance(pair, list) or len(pair) != 2:
            raise FormalError("malformed_trace", "ITF #map entries must be key/value pairs")
        key = literal(pair[0], depth + 1)
        if key in rendered:
            raise FormalError("malformed_trace", "ITF #map contains duplicate keys")
        rendered[key] = literal(pair[1], depth + 1)
    if not rendered:
        return "[x \\in {} |-> x]"
    return "(" + " @@ ".join(f"({key} :> {value})" for key, value in sorted(rendered.items())) + ")"


def states(trace: Any, projection: dict[str, str], actions: dict[str, str], limit: int) -> list[dict[str, Any]]:
    if not isinstance(trace, dict) or set(trace) - {"#meta", "vars", "states", "params"}:
        raise FormalError("malformed_trace", "Expected a finite ITF trace; loop/counterexample replays are not implementation evidence")
    variables = list(projection.values())
    declared = trace.get("vars")
    if not isinstance(declared, list) or any(not isinstance(v, str) for v in declared) or sorted(declared) != sorted(variables):
        raise FormalError("mismatched_trace", "ITF variables must exactly match the declared state projection")
    if trace.get("params", []) != []:
        raise FormalError("unsupported", "Observed trace parameters must remain in the approved native model configuration")
    rows = trace.get("states")
    if not isinstance(rows, list) or not 2 <= len(rows) <= limit:
        raise FormalError("malformed_trace", "A trace must include an initial state and at least one observed transition within max_states")
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {*variables, "#meta"}:
            raise FormalError("malformed_trace", "Each trace state must contain every projected variable and metadata only")
        meta = row["#meta"]
        if not isinstance(meta, dict) or type(meta.get("index")) is not int or meta["index"] != index:
            raise FormalError("malformed_trace", "Trace indices must be consecutive from zero")
        if index == 0 and meta.get("action") is not None or index > 0 and meta.get("action") not in actions:
            raise FormalError("mismatched_trace", "Every observed transition must name one declared action; the initial state has no action")
        for name in variables:
            literal(row[name])
    return rows
