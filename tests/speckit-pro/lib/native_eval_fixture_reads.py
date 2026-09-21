"""Prove complete Codex fixture reads from controller-owned witnesses.

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
_PROJECT_ARTIFACTS = "project_artifacts"
_RESERVED_METADATA = frozenset({
    "fixture_read_proofs", "fixture_read_witnesses", "project_artifact_search_scope",
})
_SHELLS = frozenset({"sh", "bash", "zsh", "/bin/sh", "/bin/bash", "/bin/zsh"})
_CAT = frozenset({"cat", "/bin/cat"})
_JQ = frozenset({"jq", "/usr/bin/jq", "/opt/homebrew/bin/jq"})
_NL = frozenset({"nl", "/usr/bin/nl"})
_SED = frozenset({"sed", "/bin/sed", "/usr/bin/sed"})
_WC = frozenset({"wc", "/usr/bin/wc"})
_SED_RANGE = re.compile(r"1,(\$|[1-9][0-9]{0,8})p")
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
    end_line: int | None
    kind: str


def _project_artifacts(value: object) -> tuple[str, ...]:
    _require(isinstance(value, list) and all(isinstance(item, str) for item in value),
             "controller project-artifact scope is malformed")
    paths = tuple(_path(item, "controller project-artifact path") for item in value)
    _require(all(path is not None for path in paths) and list(paths) == sorted(set(paths)),
             "controller project-artifact scope is not canonical")
    return tuple(path for path in paths if path is not None)


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
        _PROJECT_ARTIFACTS: sorted(validated),
    }
    result["native_metadata"] = result_metadata
    return result


def _bound_controller_envelope(
    observation: object,
) -> tuple[dict[str, dict[str, object]], Mapping[str, object]] | None:
    _require(isinstance(observation, Mapping), "native observation must be a mapping")
    metadata = observation.get("native_metadata")
    _require(metadata is None or isinstance(metadata, Mapping),
             "native observation metadata is malformed")
    if not isinstance(metadata, Mapping) or _CONTROLLER_KEY not in metadata:
        return None
    envelope = metadata[_CONTROLLER_KEY]
    _require(isinstance(envelope, Mapping)
             and set(envelope) in (
                 {"authority", "witnesses"},
                 {"authority", "witnesses", _PROJECT_ARTIFACTS},
             )
             and envelope.get("authority") == _CONTROLLER_AUTHORITY,
             "controller fixture-read witness envelope is malformed")
    return validate_fixture_read_witnesses(envelope.get("witnesses")), envelope


def bound_fixture_read_witnesses(observation: object) -> dict[str, dict[str, object]] | None:
    """Read the exact controller envelope, rejecting malformed lookalikes."""
    bound = _bound_controller_envelope(observation)
    return None if bound is None else bound[0]


def bound_project_artifact_paths(observation: object) -> tuple[str, ...] | None:
    """Return the controller-owned project fixture scope, excluding injected runtime files."""
    bound = _bound_controller_envelope(observation)
    if bound is None:
        return None
    witnesses, envelope = bound
    if _PROJECT_ARTIFACTS not in envelope:
        # Compatibility for retained captures written before the explicit scope
        # field: the controller's fixture witness map was already exhaustive for
        # authored scenario inputs and excluded injected runtime payloads.
        return tuple(sorted(witnesses))
    paths = _project_artifacts(envelope[_PROJECT_ARTIFACTS])
    _require(set(witnesses) <= set(paths),
             "controller project-artifact scope omits a witnessed fixture")
    return paths


def _tokens(command: str) -> list[str] | None:
    if (not command.strip()
            or any(ord(character) < 32 or character in ";|<>`" for character in command)):
        return None
    try:
        return shlex.split(command, comments=False, posix=True)
    except ValueError:
        return None


def _sed(tokens: list[str]) -> tuple[str, int | None] | None:
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
    return path, None if match.group(1) == "$" else int(match.group(1))


def _single_operand(
    tokens: list[str], executables: frozenset[str], prefixes: tuple[tuple[str, ...], ...],
    label: str,
) -> str | None:
    if len(tokens) < 2 or tokens[0] not in executables:
        return None
    prefix = tuple(tokens[1:-1])
    if prefix not in prefixes:
        return None
    operand = tokens[-1]
    if operand == "-" or (prefix[-1:] != ("--",) and operand.startswith("-")):
        return None
    return _path(operand, label)


def _wc(tokens: list[str]) -> str | None:
    return _single_operand(tokens, _WC, (("-l",), ("-l", "--")), "wc path")


def _cat(tokens: list[str]) -> str | None:
    return _single_operand(tokens, _CAT, ((), ("--",)), "cat path")


def _jq_identity(tokens: list[str]) -> str | None:
    if not tokens or tokens[0] not in _JQ:
        return None
    if len(tokens) == 3:
        expression, operand = tokens[1], tokens[2]
    elif len(tokens) == 4 and tokens[1] == "--":
        expression, operand = tokens[2], tokens[3]
    else:
        return None
    return _path(operand, "jq identity path") if expression == "." else None


def _nl_full(tokens: list[str]) -> str | None:
    if not tokens or tokens[0] not in _NL:
        return None
    if len(tokens) == 2:
        operand = tokens[1]
    elif len(tokens) == 3 and tokens[1] == "-ba":
        operand = tokens[2]
    elif len(tokens) == 3 and tokens[1] == "--":
        operand = tokens[2]
    elif len(tokens) == 4 and tokens[1:3] == ["-ba", "--"]:
        operand = tokens[3]
    else:
        return None
    return _path(operand, "nl path")


def _shell_body(command: object) -> str | None:
    if (not isinstance(command, str) or not command.strip()
            or any(ord(character) < 32 and character not in "\n\t" for character in command)
            or "`" in command or "$(" in command or "${" in command):
        return None
    try:
        outer = shlex.split(command, comments=False, posix=True)
    except ValueError:
        return None
    if outer and outer[0] in _SHELLS:
        return outer[2] if len(outer) == 3 and outer[1] == "-c" else None
    return command


def _sequence_tokens(command: object) -> list[list[str]] | None:
    """Lex only safe sequential shell forms; retain a single allowed pipeline."""
    body = _shell_body(command)
    if body is None:
        return None
    lexer = shlex.shlex(body, posix=True, punctuation_chars=";&|<>")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return None
    segments: list[list[str]] = [[]]
    for token in tokens:
        if token in {"&&", ";"}:
            if not segments[-1]:
                return None
            segments.append([])
        elif token in {"&", "||", "<", ">", "<<", ">>"}:
            return None
        else:
            segments[-1].append(token)
    return segments if segments and segments[-1] else None


def _safe_find_projection(tokens: list[str]) -> bool:
    if "|" in tokens:
        separator = tokens.index("|")
        if tokens[separator + 1:] != ["sort"] or "|" in tokens[separator + 1:]:
            return False
        tokens = tokens[:separator]
    if len(tokens) < 5 or tokens[0] not in {"find", "/usr/bin/find"}:
        return False
    try:
        root = _path(tokens[1], "find root")
    except FixtureReadProofError:
        return False
    if root is None:
        return False
    options = tokens[2:]
    if options[-3:] != ["-type", "f", "-print"]:
        return False
    options = options[:-3]
    return not options or (
        len(options) == 2 and options[0] == "-maxdepth"
        and options[1].isdigit() and int(options[1]) >= 0
    )


def _literal_heading(tokens: list[str]) -> bool:
    if not tokens or tokens[0] not in {"printf", "/usr/bin/printf"}:
        return False
    if len(tokens) == 2:
        return "%" not in tokens[1]
    return len(tokens) == 3 and tokens[1] == "%s\\n" and "%" not in tokens[2]


def _sequence_projection(tokens: list[str]) -> _Read | bool | None:
    sed = _sed(tokens)
    if sed is not None:
        return _Read(sed[0], sed[1], "unbounded_sed" if sed[1] is None else "bounded_sed")
    path = _cat(tokens)
    if path is not None:
        return _Read(path, None, "cat")
    path = _jq_identity(tokens)
    if path is not None:
        return _Read(path, None, "jq_identity")
    path = _nl_full(tokens)
    if path is not None:
        return _Read(path, None, "nl_full")
    if _literal_heading(tokens) or _safe_find_projection(tokens):
        return False
    return None


def _read_sequence(command: object) -> list[_Read] | None:
    segments = _sequence_tokens(command)
    if segments is None:
        return None
    reads: list[_Read] = []
    for tokens in segments:
        projected = _sequence_projection(tokens)
        if projected is None:
            return None
        if isinstance(projected, _Read):
            reads.append(projected)
    return reads or None


def codex_unbounded_read_paths(command: object) -> tuple[str, ...]:
    """Return exact paths only when the whole command is a safe full-read projection."""
    reads = _read_sequence(command)
    if reads is None:
        return ()
    return tuple(read.path for read in reads if read.end_line is None)


def _read(command: object) -> _Read | None:
    if not isinstance(command, str):
        return None
    outer = _tokens(command)
    if outer is None:
        return None
    if len(outer) == 3 and outer[0] in _SHELLS and outer[1] == "-c":
        nested = outer[2]
        if any(ord(character) < 32 or character in ";|<>`" for character in nested):
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
            return _Read(
                read[0], read[1],
                "count_then_unbounded_sed" if read[1] is None else "count_then_bounded_sed",
            )
        direct = _sed(tokens)
    else:
        direct = _sed(outer)
    if direct is None:
        return None
    return _Read(
        direct[0], direct[1], "unbounded_sed" if direct[1] is None else "bounded_sed",
    )


def _body(output: str, read: _Read) -> tuple[str, int] | None:
    if read.kind in {"bounded_sed", "unbounded_sed"}:
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


def _witness_body(output: str, witness: _Witness) -> bytes | None:
    """Locate exact controller-authenticated fixture bytes in a compound projection."""
    try:
        encoded = output.encode("utf-8", errors="strict")
    except UnicodeError:
        return None
    if witness.byte_count > len(encoded):
        return None
    for start in range(len(encoded) - witness.byte_count + 1):
        candidate = encoded[start:start + witness.byte_count]
        if hashlib.sha256(candidate).hexdigest() == witness.sha256:
            return candidate
    return None


def _verified_projection(
    output: str, projected: _Read, read_count: int, witness: _Witness,
) -> tuple[bytes, int, int] | None:
    if read_count != 1:
        return None
    encoded = _witness_body(output, witness)
    if encoded is None:
        return None
    newlines = encoded.count(b"\n")
    logical_lines = newlines + (1 if encoded and not encoded.endswith(b"\n") else 0)
    if ((projected.end_line is not None and projected.end_line < logical_lines)
            or len(encoded) != witness.byte_count
            or hashlib.sha256(encoded).hexdigest() != witness.sha256):
        return None
    return encoded, newlines, logical_lines


def _projection_access(
    projected: _Read, witness: _Witness, index: int, verified: tuple[bytes, int, int],
) -> dict[str, object]:
    _, newlines, logical_lines = verified
    return {
        "operation": "read_file",
        "path": projected.path,
        "tool_call_index": index,
        "provenance": {
            "schema_version": _SCHEMA,
            "kind": f"compound_{projected.kind}",
            "bytes": witness.byte_count,
            "sha256": witness.sha256,
            "start_line": 1,
            "end_line": projected.end_line if projected.end_line is not None else logical_lines,
            "logical_lines": logical_lines,
            "newline_count": newlines,
            "count_header_verified": projected.kind.startswith("count_then_"),
        },
    }


def _fixture_call_accesses(
    index: int, call: Mapping[str, object], trusted: Mapping[str, _Witness],
) -> list[dict[str, object]]:
    supplied, output = call.get("input"), call.get("output")
    if (call.get("name") != "command_execution" or call.get("success") is not True
            or not isinstance(supplied, Mapping) or set(supplied) != {"command"}
            or not isinstance(output, str)):
        return []
    command = supplied.get("command")
    if _read(command) is not None:
        return []
    reads = _read_sequence(command) or []
    accesses: list[dict[str, object]] = []
    for projected in reads:
        witness = trusted.get(projected.path)
        if witness is None:
            continue
        verified = _verified_projection(output, projected, len(reads), witness)
        if verified is not None:
            accesses.append(_projection_access(projected, witness, index, verified))
    return accesses


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
        if ((read.end_line is not None and read.end_line < logical_lines)
                or len(encoded) != witness.byte_count
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
                "end_line": read.end_line if read.end_line is not None else logical_lines,
                "logical_lines": logical_lines,
                "newline_count": wc_newlines,
                "count_header_verified": read.kind.startswith("count_then_"),
            },
        })
    return accesses


_legacy_fixture_read_accesses = fixture_read_accesses


def _fixture_read_accesses_with_compound(
    observation: object,
    fixture_read_witnesses: Mapping[str, object],
) -> list[dict[str, object]]:
    legacy = _legacy_fixture_read_accesses(observation, fixture_read_witnesses)
    calls = observation.get("tool_calls") if isinstance(observation, Mapping) else None
    if not isinstance(calls, list):
        return legacy
    trusted = _witnesses(fixture_read_witnesses)
    return legacy + [
        access
        for index, call in enumerate(calls)
        if isinstance(call, Mapping)
        for access in _fixture_call_accesses(index, call, trusted)
    ]


fixture_read_accesses = _fixture_read_accesses_with_compound


__all__ = [
    "FixtureReadProofError",
    "bind_controller_fixture_read_witnesses",
    "bound_fixture_read_witnesses",
    "bound_project_artifact_paths",
    "codex_unbounded_read_paths",
    "fixture_read_accesses",
    "validate_fixture_read_witnesses",
]
