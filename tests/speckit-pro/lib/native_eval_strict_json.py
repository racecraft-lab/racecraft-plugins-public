"""One strict JSON contract and receipt helpers shared by the native eval modules.

Strict JSON rejects duplicate object keys, the non-standard ``NaN`` and
``Infinity`` constants, malformed text, invalid UTF-8, and nesting deep enough
to exhaust the parser. Every failure surfaces as the caller-supplied error
class. This module imports no other native eval module so any of them can use
it, and the fixture scripts staged beside it can import it standalone.
"""

from __future__ import annotations

import json
from typing import Any, Mapping


class _StrictJSONDefect(ValueError):
    """Internal marker for a duplicate key or non-standard constant."""


_DECODE_FAILURES = (
    json.JSONDecodeError, _StrictJSONDefect, TypeError, UnicodeError, RecursionError,
)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _StrictJSONDefect(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_constant(token: str) -> Any:
    raise _StrictJSONDefect(f"invalid JSON constant: {token}")


def _text(value: str | bytes | bytearray) -> str:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="strict")
    if not isinstance(value, str):
        raise TypeError("JSON input must be text or bytes")
    return value


def _failure(error: type[Exception], label: str | None, exc: BaseException) -> Exception:
    reason = str(exc) if isinstance(exc, _StrictJSONDefect) else f"malformed JSON: {exc}"
    if isinstance(exc, RecursionError):
        reason = "malformed JSON: nesting is too deep"
    return error(f"{label}: {reason}" if label else reason)


def decoder() -> json.JSONDecoder:
    """Return a strict decoder for ``raw_decode`` scans; defects raise ``ValueError``."""

    return json.JSONDecoder(object_pairs_hook=_unique_object, parse_constant=_reject_constant)


def loads(
    value: str | bytes | bytearray, *, error: type[Exception] = ValueError,
    label: str | None = None,
) -> Any:
    """Parse strict JSON, raising ``error`` for any defect."""

    try:
        return json.loads(
            _text(value), object_pairs_hook=_unique_object, parse_constant=_reject_constant,
        )
    except _DECODE_FAILURES as exc:
        raise _failure(error, label, exc) from exc


def stream(
    value: str, *, error: type[Exception] = ValueError, label: str | None = None,
) -> list[Any]:
    """Parse zero or more whitespace-separated strict JSON values."""

    scanner = decoder()
    values: list[Any] = []
    position = 0
    try:
        text = _text(value)
        while True:
            while position < len(text) and text[position].isspace():
                position += 1
            if position == len(text):
                return values
            item, position = scanner.raw_decode(text, position)
            values.append(item)
    except _DECODE_FAILURES as exc:
        raise _failure(error, label, exc) from exc


def strict_equal(left: Any, right: Any) -> bool:
    """Compare JSON values by exact type, key set, and list order."""

    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            strict_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            strict_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    return bool(left == right)


def canonical_bytes(value: object) -> bytes:
    """Encode one JSON value canonically for hashing."""

    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def output_text(output: object, *, error: type[Exception], message: str) -> str:
    """Join a command output that is text or a list of text parts."""

    if isinstance(output, str):
        return output
    if not (isinstance(output, list) and all(
        isinstance(item, Mapping) and item.get("type") == "text"
        and isinstance(item.get("text"), str) for item in output
    )):
        raise error(message)
    return "".join(str(item["text"]) for item in output)


def attach_receipt(
    observation: dict[str, Any], rows: list[Mapping[str, object]], *, key: str,
    schema: str, authority: str, error: type[Exception],
) -> None:
    """Attach one controller receipt to native metadata, exactly once."""

    metadata = observation.get("native_metadata")
    if not isinstance(metadata, dict) or key in metadata:
        raise error(f"native {key} observation metadata is malformed")
    metadata[key] = {
        "schema": schema, "authority": authority, "checks": [dict(row) for row in rows],
    }
