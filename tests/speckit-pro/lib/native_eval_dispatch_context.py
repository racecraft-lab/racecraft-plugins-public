"""Opaque proof of exact trusted context in a native subagent dispatch.

The controller supplies the actual native dispatch message, trusted fixture
texts, and the preceding actual G3 response.  Fixture matching removes outer
whitespace from each trusted text and otherwise requires exact full-text
containment.  Embedded JSON is decoded structurally and compared type-strictly.

This helper does not prove where the G3 response came from, command/dispatch/
return ordering, return consumption, or behavior.  Those are executor and
grader integration responsibilities.  It never returns raw evidence text.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Mapping

from native_eval_catalog import _unique_object


MAX_MESSAGE_BYTES = 256 * 1024
MAX_CONTEXTS = 16
MAX_CONTEXT_BYTES = 64 * 1024
MAX_CONTEXT_TOTAL_BYTES = 256 * 1024
MAX_PRECEDING_JSON_BYTES = 128 * 1024
MAX_JSON_CANDIDATES = 256
MAX_JSON_DEPTH = 128

_CONTEXT_ID = re.compile(r"[a-z0-9][a-z0-9._-]*")


class DispatchContextProofError(ValueError):
    """Trusted configuration is malformed or a qualification bound was exhausted."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DispatchContextProofError(message)


def _contexts(value: Mapping[str, str]) -> dict[str, str]:
    _require(isinstance(value, Mapping), "contexts must be a mapping")
    _require(1 <= len(value) <= MAX_CONTEXTS,
             f"contexts must contain from 1 through {MAX_CONTEXTS} entries")
    result: dict[str, str] = {}
    total = 0
    for context_id, raw_text in value.items():
        _require(isinstance(context_id, str) and _CONTEXT_ID.fullmatch(context_id) is not None,
                 "context id is not canonical")
        _require(isinstance(raw_text, str), f"context {context_id} must be text")
        text = raw_text.strip()
        _require(bool(text), f"context {context_id} must be nonempty after outer whitespace removal")
        try:
            encoded = text.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise DispatchContextProofError(
                f"context {context_id} is not strict UTF-8"
            ) from exc
        _require(len(encoded) <= MAX_CONTEXT_BYTES,
                 f"context {context_id} exceeds the byte bound")
        total += len(encoded)
        _require(total <= MAX_CONTEXT_TOTAL_BYTES, "contexts exceed the total byte bound")
        result[context_id] = text
    return result


def _strict_json_value(value: object, label: str) -> None:
    pending: list[tuple[object, int]] = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        _require(depth <= MAX_JSON_DEPTH, f"{label} exceeds the JSON depth bound")
        if item is None or type(item) in {bool, int, str}:
            continue
        if type(item) is float:
            _require(math.isfinite(item), f"{label} contains a non-finite number")
            continue
        if type(item) is list:
            pending.extend((child, depth + 1) for child in item)
            continue
        if type(item) is dict:
            _require(all(isinstance(key, str) for key in item),
                     f"{label} contains a non-text object key")
            pending.extend((child, depth + 1) for child in item.values())
            continue
        raise DispatchContextProofError(f"{label} is not a strict JSON value")


def _preceding(value: object) -> object:
    _strict_json_value(value, "preceding G3 response")
    _require(type(value) in {dict, list},
             "preceding G3 response must be a JSON object or array")
    try:
        encoded = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise DispatchContextProofError("preceding G3 response is not strict JSON") from exc
    _require(len(encoded) <= MAX_PRECEDING_JSON_BYTES,
             "preceding G3 response exceeds the byte bound")
    return value


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _json_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        if left.keys() != right.keys():  # type: ignore[union-attr]
            return False
        return all(_json_equal(left[key], right[key]) for key in left)  # type: ignore[index,union-attr]
    if type(left) is list:
        return len(left) == len(right) and all(  # type: ignore[arg-type]
            _json_equal(left_item, right_item)
            for left_item, right_item in zip(left, right)  # type: ignore[arg-type]
        )
    return left == right


def _contains_complete_json(message: str, expected: object) -> bool:
    starts = [index for index, character in enumerate(message) if character in "{["]
    _require(len(starts) <= MAX_JSON_CANDIDATES,
             "dispatch message exceeds the JSON candidate bound")
    decoder = json.JSONDecoder(
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )
    for start in starts:
        try:
            candidate, _end = decoder.raw_decode(message, start)
        except (json.JSONDecodeError, ValueError):
            continue
        except RecursionError as exc:
            raise DispatchContextProofError("embedded JSON exceeds the parser depth bound") from exc
        try:
            _strict_json_value(candidate, "embedded JSON candidate")
        except DispatchContextProofError as exc:
            if "depth bound" in str(exc):
                raise
            continue
        if _json_equal(candidate, expected):
            return True
    return False


def qualify_native_dispatch_context(
    message: str,
    contexts: Mapping[str, str],
    preceding_g3_response: object,
) -> dict[str, object]:
    """Return privacy-preserving exact-context observations for one dispatch."""
    _require(isinstance(message, str), "dispatch message must be text")
    try:
        encoded = message.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise DispatchContextProofError("dispatch message is not strict UTF-8") from exc
    _require(len(encoded) <= MAX_MESSAGE_BYTES, "dispatch message exceeds the byte bound")
    trusted = _contexts(contexts)
    preceding = _preceding(preceding_g3_response)
    observed = sorted(
        context_id for context_id, text in trusted.items() if text in message
    )
    return {
        "message_sha256": hashlib.sha256(encoded).hexdigest(),
        "message_bytes": len(encoded),
        "observed_context_ids": observed,
        "complete_preceding_json_found": _contains_complete_json(message, preceding),
    }


__all__ = [
    "DispatchContextProofError",
    "MAX_CONTEXTS",
    "MAX_CONTEXT_BYTES",
    "MAX_CONTEXT_TOTAL_BYTES",
    "MAX_JSON_CANDIDATES",
    "MAX_JSON_DEPTH",
    "MAX_MESSAGE_BYTES",
    "MAX_PRECEDING_JSON_BYTES",
    "qualify_native_dispatch_context",
]
