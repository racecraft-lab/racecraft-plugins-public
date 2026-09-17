"""Qualify Codex skill activations from exact staged SKILL.md reads.

The public Codex exec stream has no typed skill-activation event.  For an
explicitly requested functional skill, a complete successful read of the
frozen staged body is the observable consultation evidence.  This module does
not infer activation from the prompt, final prose, or generic shell activity.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import os
from pathlib import PurePosixPath
import re
import shlex
from typing import Any, Mapping


_SKILL_NAME = re.compile(r"[a-z0-9][a-z0-9._-]*")
_SED_RANGE = re.compile(r"([1-9][0-9]*),([1-9][0-9]*)p")
_SHELLS = frozenset({"bash", "sh", "zsh"})
_SCHEMA = "codex-skill-read-qualification/v1"
_EVIDENCE_BOUND = (
    "Complete frozen SKILL.md content consultation corroborates an explicit "
    "skill invocation; it is not a secret or typed internal Codex activation event."
)


class SkillReadQualificationError(ValueError):
    """Trusted witness configuration or normalized observation is malformed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SkillReadQualificationError(message)


@dataclass(frozen=True)
class _Witness:
    name: str
    path: str
    text: str
    byte_count: int
    sha256: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class _ReadCommand:
    path: str
    operation: str
    start: int | None = None
    end: int | None = None


def _workspace(value: str | os.PathLike[str]) -> str:
    try:
        text = os.fspath(value)
    except TypeError as exc:
        raise SkillReadQualificationError("workspace_root must be a path") from exc
    _require(isinstance(text, str) and bool(text), "workspace_root must be nonempty text")
    parsed = PurePosixPath(text)
    _require(parsed.is_absolute() and parsed.as_posix() == text and text != "/"
             and all(part not in {"", ".", ".."} for part in parsed.parts[1:]),
             "workspace_root must be a canonical absolute POSIX path")
    return text


def _witnesses(value: Mapping[str, object]) -> dict[str, _Witness]:
    _require(isinstance(value, Mapping) and bool(value), "skill read witnesses must be a nonempty mapping")
    result: dict[str, _Witness] = {}
    paths: set[str] = set()
    for name, raw in value.items():
        _require(isinstance(name, str) and _SKILL_NAME.fullmatch(name) is not None,
                 "skill read witness name is not canonical")
        _require(isinstance(raw, Mapping)
                 and set(raw) == {"path", "text", "bytes", "sha256"},
                 f"skill read witness {name} has a malformed schema")
        path, text = raw["path"], raw["text"]
        byte_count, digest = raw["bytes"], raw["sha256"]
        expected_path = f".agents/skills/{name}/SKILL.md"
        _require(isinstance(path, str) and path == expected_path,
                 f"skill read witness {name} path is not canonical")
        _require(path not in paths, "skill read witness paths are duplicated")
        _require(isinstance(text, str) and bool(text),
                 f"skill read witness {name} text is empty or malformed")
        try:
            encoded = text.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise SkillReadQualificationError(
                f"skill read witness {name} text is not strict UTF-8"
            ) from exc
        _require(type(byte_count) is int and byte_count == len(encoded),
                 f"skill read witness {name} byte count does not match")
        expected_digest = hashlib.sha256(encoded).hexdigest()
        _require(isinstance(digest, str) and digest == expected_digest,
                 f"skill read witness {name} sha256 does not match")
        paths.add(path)
        result[name] = _Witness(
            name=name, path=path, text=text, byte_count=byte_count,
            sha256=digest, lines=tuple(text.splitlines(keepends=True)),
        )
    return result


def _tokens(command: str) -> list[str] | None:
    try:
        outer = shlex.split(command)
        if len(outer) == 3 and PurePosixPath(outer[0]).name in _SHELLS and outer[1] == "-c":
            return shlex.split(outer[2])
        return outer
    except ValueError:
        return None


def _read_command(command: str) -> _ReadCommand | None:
    tokens = _tokens(command)
    if tokens is None or not tokens:
        return None
    executable = tokens[0]
    if executable == "cat":
        if len(tokens) == 2:
            return _ReadCommand(tokens[1], "cat")
        if len(tokens) == 3 and tokens[1] == "--":
            return _ReadCommand(tokens[2], "cat")
        return None
    if executable != "sed" or len(tokens) not in {4, 5} or tokens[1] != "-n":
        return None
    if len(tokens) == 5:
        if tokens[3] != "--":
            return None
        expression, path = tokens[2], tokens[4]
    else:
        expression, path = tokens[2], tokens[3]
    matched = _SED_RANGE.fullmatch(expression)
    if matched is None:
        return None
    start, end = (int(part) for part in matched.groups())
    if start > end:
        return None
    return _ReadCommand(path, "sed", start, end)


def _match_witness(path: str, workspace: str,
                   witnesses: Mapping[str, _Witness]) -> _Witness | None:
    matches = [
        witness for witness in witnesses.values()
        if path in {witness.path, f"{workspace}/{witness.path}"}
    ]
    return matches[0] if len(matches) == 1 else None


def _looks_like_skill_path(path: str) -> bool:
    return path.endswith("/SKILL.md") or path == "SKILL.md" or ".agents/skills/" in path


def _interval_and_output(read: _ReadCommand, witness: _Witness) -> tuple[int, int, str] | None:
    final_line = len(witness.lines)
    if read.operation == "cat":
        return 1, final_line, witness.text
    _require(read.start is not None and read.end is not None, "internal sed range is malformed")
    if read.start > final_line:
        return None
    end = min(read.end, final_line)
    return read.start, end, "".join(witness.lines[read.start - 1:end])


def _merged(intervals: list[tuple[int, int]]) -> list[list[int]]:
    merged: list[list[int]] = []
    for start, end in sorted(set(intervals)):
        if not merged or start > merged[-1][1] + 1:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return merged


def _call_label(call: Mapping[str, object], index: int) -> dict[str, object]:
    identity = call.get("id")
    return {
        "call_index": index,
        **({"call_id": identity} if isinstance(identity, str) and identity else {}),
    }


def qualify_codex_skill_reads(
    observation: Mapping[str, Any],
    witnesses: Mapping[str, object],
    workspace_root: str | os.PathLike[str],
) -> dict[str, Any]:
    """Return a copy whose activations come only from complete exact skill reads.

    Witnesses are trusted preparation evidence.  The qualifier performs no
    filesystem access and accepts only lexical matches to their frozen paths.
    All original tool calls remain unchanged in the returned observation.
    """
    _require(isinstance(observation, Mapping), "Codex observation must be a mapping")
    calls = observation.get("tool_calls")
    _require(isinstance(calls, list) and all(isinstance(call, Mapping) for call in calls),
             "Codex observation tool_calls are malformed")
    workspace = _workspace(workspace_root)
    trusted = _witnesses(witnesses)

    reads: dict[str, list[dict[str, object]]] = {name: [] for name in trusted}
    rejected: list[dict[str, object]] = []
    exact_paths = {
        candidate
        for witness in trusted.values()
        for candidate in (witness.path, f"{workspace}/{witness.path}")
    }

    for index, call in enumerate(calls):
        if call.get("name") != "command_execution":
            continue
        supplied = call.get("input")
        command = supplied.get("command") if isinstance(supplied, Mapping) else None
        if not isinstance(command, str) or not command:
            continue
        parsed = _read_command(command)
        if parsed is None:
            if any(path in command for path in exact_paths):
                rejected.append({**_call_label(call, index), "reason": "unsupported_command"})
            continue
        witness = _match_witness(parsed.path, workspace, trusted)
        if witness is None:
            if _looks_like_skill_path(parsed.path):
                rejected.append({**_call_label(call, index), "reason": "unbound_skill_path"})
            continue
        if call.get("success") is not True:
            rejected.append({**_call_label(call, index), "skill": witness.name,
                             "reason": "unsuccessful_read"})
            continue
        interval = _interval_and_output(parsed, witness)
        output = call.get("output")
        if interval is None or not isinstance(output, str) or output != interval[2]:
            rejected.append({**_call_label(call, index), "skill": witness.name,
                             "reason": "output_mismatch"})
            continue
        start, end, _expected = interval
        reads[witness.name].append({
            **_call_label(call, index),
            "operation": parsed.operation,
            "start_line": start,
            "end_line": end,
        })

    consultations: list[dict[str, object]] = []
    complete: list[tuple[int, str]] = []
    for name, evidence in reads.items():
        if not evidence:
            continue
        witness = trusted[name]
        coverage = _merged([
            (int(item["start_line"]), int(item["end_line"])) for item in evidence
        ])
        is_complete = coverage == [[1, len(witness.lines)]]
        consultations.append({
            "skill": name,
            "path": witness.path,
            "bytes": witness.byte_count,
            "sha256": witness.sha256,
            "status": "complete" if is_complete else "partial",
            "coverage": coverage,
            "reads": evidence,
        })
        if is_complete:
            complete.append((min(int(item["call_index"]) for item in evidence), name))

    activations = [name for _index, name in sorted(complete)]
    status = (
        "qualified" if activations
        else "partial" if consultations
        else "rejected" if rejected
        else "not_observed"
    )
    result = copy.deepcopy(dict(observation))
    result["activations"] = activations
    metadata = result.get("native_metadata")
    _require(metadata is None or isinstance(metadata, Mapping),
             "Codex observation native_metadata is malformed")
    native_metadata = copy.deepcopy(dict(metadata or {}))
    native_metadata["codex_skill_reads"] = {
        "schema_version": _SCHEMA,
        "status": status,
        "evidence_bound": _EVIDENCE_BOUND,
        "workspace_root": workspace,
        "activations": list(activations),
        "consultations": consultations,
        "rejected_attempts": rejected,
    }
    result["native_metadata"] = native_metadata
    return result


__all__ = ["SkillReadQualificationError", "qualify_codex_skill_reads"]
