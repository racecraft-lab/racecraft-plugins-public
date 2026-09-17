"""Prove complete bounded Codex fixture reads from controller-owned witnesses.

The native command and output remain subject evidence.  The witness mapping is
trusted preparation evidence retained by the controller.  This module performs
no filesystem access and never accepts a subject-supplied witness or cached
proof. The only metadata envelope it reads is attached by the controller after
raw normalization and is revalidated before every proof.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import re
import shlex
from typing import Mapping

from native_eval_catalog import _relative_path


_SCHEMA = "native-eval-fixture-read-proof/v1"
_CONTROLLER_KEY = "controller_fixture_read_witnesses"
_CONTROLLER_AUTHORITY = "controller-staged-fixtures"
_RESERVED_METADATA = frozenset({"fixture_read_proofs", "fixture_read_witnesses"})
_SHELLS = frozenset({"sh", "bash", "zsh", "/bin/sh", "/bin/bash", "/bin/zsh"})
_SED = frozenset({"sed", "/bin/sed", "/usr/bin/sed"})
_WC = frozenset({"wc", "/usr/bin/wc"})
_SED_RANGE = re.compile(r"1,([1-9][0-9]{0,8})p")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_WC_HEADER = re.compile(r"[ \t]*([0-9]{1,9})[ \t]+(.+)")


class FixtureReadProofError(ValueError):
    """Trusted proof inputs or normalized native evidence are malformed."""


@dataclass(frozen=True)
class _Witness:
    path: str
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class _Read:
    path: str
    end_line: int
    kind: str


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FixtureReadProofError(message)


def _path(value: object, label: str) -> str | None:
    try:
        path = _relative_path(value, label).as_posix()
    except ValueError:
        return None
    if path != path.strip() or any(character in path for character in "*?[]{}~$&();|<>`"):
        return None
    return path


def _witnesses(value: Mapping[str, object]) -> dict[str, _Witness]:
    _require(isinstance(value, Mapping), "fixture read witnesses must be a mapping")
    result: dict[str, _Witness] = {}
    for raw_path, raw in value.items():
        path = _path(raw_path, "fixture read witness path")
        _require(path is not None and path == raw_path,
                 "fixture read witness path is not canonical")
        _require(isinstance(raw, Mapping) and set(raw) == {"bytes", "sha256"},
                 f"fixture read witness {path} has a malformed schema")
        byte_count, digest = raw["bytes"], raw["sha256"]
        _require(type(byte_count) is int and byte_count >= 0,
                 f"fixture read witness {path} has an invalid byte count")
        _require(isinstance(digest, str) and _SHA256.fullmatch(digest) is not None,
                 f"fixture read witness {path} has an invalid sha256")
        result[path] = _Witness(path, byte_count, digest)
    return result


def validate_fixture_read_witnesses(
    value: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    """Validate and copy the controller's immutable path/size/digest map."""
    return {
        path: {"bytes": item.byte_count, "sha256": item.sha256}
        for path, item in _witnesses(value).items()
    }


def bind_controller_fixture_read_witnesses(
    observation: object,
    fixture_read_witnesses: Mapping[str, object],
) -> dict[str, object]:
    """Return a copy with validated controller witnesses bound for grading."""
    _require(isinstance(observation, Mapping), "native observation must be a mapping")
    metadata = observation.get("native_metadata")
    _require(metadata is None or isinstance(metadata, Mapping),
             "native observation metadata is malformed")
    _require(not isinstance(metadata, Mapping) or _CONTROLLER_KEY not in metadata,
             "native observation already contains reserved controller fixture-read metadata")
    validated = validate_fixture_read_witnesses(fixture_read_witnesses)
    result = copy.deepcopy(dict(observation))
    result_metadata = copy.deepcopy(dict(metadata or {}))
    result_metadata[_CONTROLLER_KEY] = {
        "authority": _CONTROLLER_AUTHORITY,
        "witnesses": validated,
    }
    result["native_metadata"] = result_metadata
    return result


def bound_fixture_read_witnesses(observation: object) -> dict[str, dict[str, object]] | None:
    """Read the exact controller envelope, rejecting malformed lookalikes."""
    _require(isinstance(observation, Mapping), "native observation must be a mapping")
    metadata = observation.get("native_metadata")
    _require(metadata is None or isinstance(metadata, Mapping),
             "native observation metadata is malformed")
    if not isinstance(metadata, Mapping) or _CONTROLLER_KEY not in metadata:
        return None
    envelope = metadata[_CONTROLLER_KEY]
    _require(isinstance(envelope, Mapping)
             and set(envelope) == {"authority", "witnesses"}
             and envelope.get("authority") == _CONTROLLER_AUTHORITY,
             "controller fixture-read witness envelope is malformed")
    return validate_fixture_read_witnesses(envelope.get("witnesses"))


def _tokens(command: str) -> list[str] | None:
    if (not command.strip()
            or any(ord(character) < 32 or character in ";|<>`" for character in command)
            or "$" in command):
        return None
    try:
        return shlex.split(command, comments=False, posix=True)
    except ValueError:
        return None


def _sed(tokens: list[str]) -> tuple[str, int] | None:
    if not tokens or tokens[0] not in _SED or len(tokens) not in {4, 5} or tokens[1] != "-n":
        return None
    if len(tokens) == 5:
        if tokens[3] != "--":
            return None
        expression, operand = tokens[2], tokens[4]
    else:
        expression, operand = tokens[2], tokens[3]
    match = _SED_RANGE.fullmatch(expression)
    path = _path(operand, "bounded sed path")
    if match is None or path is None or (len(tokens) == 4 and operand.startswith("-")):
        return None
    return path, int(match.group(1))


def _wc(tokens: list[str]) -> str | None:
    if not tokens or tokens[0] not in _WC:
        return None
    if len(tokens) == 3 and tokens[1] == "-l":
        operand = tokens[2]
        option_terminated = False
    elif len(tokens) == 4 and tokens[1:3] == ["-l", "--"]:
        operand = tokens[3]
        option_terminated = True
    else:
        return None
    if not option_terminated and operand.startswith("-"):
        return None
    return _path(operand, "wc path")


def _read(command: object) -> _Read | None:
    if not isinstance(command, str):
        return None
    outer = _tokens(command)
    if outer is None:
        return None
    if len(outer) == 3 and outer[0] in _SHELLS and outer[1] == "-c":
        nested = outer[2]
        if (any(ord(character) < 32 or character in ";|<>`" for character in nested)
                or "$" in nested):
            return None
        try:
            tokens = shlex.split(nested, comments=False, posix=True)
        except ValueError:
            return None
        if tokens.count("&&") == 1:
            split = tokens.index("&&")
            counted = _wc(tokens[:split])
            read = _sed(tokens[split + 1:])
            if counted is None or read is None or counted != read[0]:
                return None
            return _Read(read[0], read[1], "count_then_bounded_sed")
        direct = _sed(tokens)
    else:
        direct = _sed(outer)
    return _Read(direct[0], direct[1], "bounded_sed") if direct is not None else None


def _body(output: str, read: _Read) -> tuple[str, int] | None:
    if read.kind == "bounded_sed":
        return output, output.count("\n")
    header, separator, body = output.partition("\n")
    if not separator:
        return None
    matched = _WC_HEADER.fullmatch(header)
    newlines = body.count("\n")
    if (matched is None or matched.group(2) != read.path
            or int(matched.group(1)) != newlines):
        return None
    return body, newlines


def fixture_read_accesses(
    observation: object,
    fixture_read_witnesses: Mapping[str, object],
) -> list[dict[str, object]]:
    """Return only complete bounded reads proven against trusted fixture bytes.

    A partial, failed, unsupported, or mismatched attempt produces no access
    record.  Malformed controller inputs and reserved proof metadata are errors.
    The input observation is never mutated.
    """
    _require(isinstance(observation, Mapping), "native observation must be a mapping")
    calls = observation.get("tool_calls")
    _require(isinstance(calls, list) and all(isinstance(call, Mapping) for call in calls),
             "native observation tool_calls are malformed")
    metadata = observation.get("native_metadata")
    _require(metadata is None or isinstance(metadata, Mapping),
             "native observation metadata is malformed")
    if isinstance(metadata, Mapping) and _RESERVED_METADATA.intersection(metadata):
        raise FixtureReadProofError("observation contains reserved fixture-read metadata")
    trusted = _witnesses(fixture_read_witnesses)

    accesses: list[dict[str, object]] = []
    for index, call in enumerate(calls):
        supplied = call.get("input")
        if (call.get("name") != "command_execution" or call.get("success") is not True
                or not isinstance(supplied, Mapping) or set(supplied) != {"command"}):
            continue
        read = _read(supplied.get("command"))
        witness = trusted.get(read.path) if read is not None else None
        output = call.get("output")
        if witness is None or not isinstance(output, str):
            continue
        derived = _body(output, read)
        if derived is None:
            continue
        body, wc_newlines = derived
        try:
            encoded = body.encode("utf-8", errors="strict")
        except UnicodeError:
            continue
        logical_lines = wc_newlines + (1 if encoded and not encoded.endswith(b"\n") else 0)
        if (read.end_line < logical_lines or len(encoded) != witness.byte_count
                or hashlib.sha256(encoded).hexdigest() != witness.sha256):
            continue
        accesses.append({
            "operation": "read_file",
            "path": read.path,
            "tool_call_index": index,
            "provenance": {
                "schema_version": _SCHEMA,
                "kind": read.kind,
                "bytes": witness.byte_count,
                "sha256": witness.sha256,
                "start_line": 1,
                "end_line": read.end_line,
                "logical_lines": logical_lines,
                "newline_count": wc_newlines,
                "count_header_verified": read.kind == "count_then_bounded_sed",
            },
        })
    return accesses


__all__ = [
    "FixtureReadProofError",
    "bind_controller_fixture_read_witnesses",
    "bound_fixture_read_witnesses",
    "fixture_read_accesses",
    "validate_fixture_read_witnesses",
]
