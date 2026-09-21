"""Normalize native evidence without treating prose or an exit code as success.

This module reads captured events only. It does not launch agents, load user
configuration, follow artifact paths, or turn parser replay into live evidence.
"""
from __future__ import annotations

import hashlib
import fnmatch
import json
from pathlib import PurePosixPath
import re
import shlex
from typing import Any, Mapping

from native_eval_catalog import _relative_path, _search_glob, _unique_object
from native_eval_fixture_reads import (
    bound_fixture_read_witnesses,
    bound_project_artifact_paths,
    codex_unbounded_read_paths,
    fixture_read_accesses,
)


class CaptureError(ValueError):
    """The capture does not establish a complete, interpretable native run."""


def _canonical_relative_file(value: object) -> str | None:
    try:
        return _relative_path(value, "native file access path").as_posix()
    except ValueError:
        return None


def _absolute_posix_path(value: object) -> PurePosixPath | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if (not path.is_absolute() or value != path.as_posix()
            or any(part in {"", ".", ".."} for part in path.parts[1:])):
        return None
    return path


def _claude_read_path(call: Mapping[str, Any], cwd: object) -> str | None:
    if call.get("name") != "Read" or call.get("success") is not True:
        return None
    inputs = call.get("input")
    if not isinstance(inputs, dict) or set(inputs) != {"file_path"}:
        return None
    value = inputs["file_path"]
    if not isinstance(value, str):
        return None
    target = PurePosixPath(value)
    if not target.is_absolute():
        return _canonical_relative_file(value)
    target = _absolute_posix_path(value)
    base = _absolute_posix_path(cwd)
    if target is None or base is None:
        return None
    try:
        relative = target.relative_to(base)
    except ValueError:
        return None
    return _canonical_relative_file(relative.as_posix())


_CODEX_SHELLS = frozenset({"sh", "bash", "zsh", "/bin/sh", "/bin/bash", "/bin/zsh"})
_CODEX_CAT = frozenset({"cat", "/bin/cat"})
_CODEX_SED = frozenset({"sed", "/bin/sed", "/usr/bin/sed"})
_CODEX_WC = frozenset({"wc", "/usr/bin/wc"})


def _safe_codex_operand(value: str, *, option_terminated: bool) -> str | None:
    if value == "-" or (not option_terminated and value.startswith("-")) or any(
        character in value for character in "*?[]{}~$"
    ):
        return None
    return _canonical_relative_file(value)


def _codex_tokens(command: object) -> list[str] | None:
    if not isinstance(command, str) or not command.strip() or any(
        ord(character) < 32 or character in ";&|<>`" for character in command
    ) or "$(" in command or "${" in command:
        return None
    try:
        return shlex.split(command, comments=False, posix=True)
    except ValueError:
        return None


def _codex_cat_path(tokens: list[str], command: str) -> str | None:
    if not tokens or tokens[0] not in _CODEX_CAT or "$" in command:
        return None
    if len(tokens) == 2:
        return _safe_codex_operand(tokens[1], option_terminated=False)
    if len(tokens) == 3 and tokens[1] == "--" and tokens[2] != "-":
        return _safe_codex_operand(tokens[2], option_terminated=True)
    return None


def _codex_sed_path(tokens: list[str], command: str) -> str | None:
    if (not tokens or tokens[0] not in _CODEX_SED or command.count("$") != 1
            or "'1,$p'" not in command):
        return None
    if len(tokens) == 4 and tokens[1:3] == ["-n", "1,$p"]:
        return _safe_codex_operand(tokens[3], option_terminated=False)
    if len(tokens) == 5 and tokens[1:4] == ["-n", "1,$p", "--"]:
        return _safe_codex_operand(tokens[4], option_terminated=True)
    return None


def _codex_count_then_sed_path(command: object) -> str | None:
    if (not isinstance(command, str) or not command.strip()
            or any(ord(character) < 32 or character in ";|<>`" for character in command)
            or "$(" in command or "${" in command or command.count("$") != 1):
        return None
    try:
        outer = shlex.split(command, comments=False, posix=True)
    except ValueError:
        return None
    if len(outer) != 3 or outer[0] not in _CODEX_SHELLS or outer[1] != "-c":
        return None
    nested = outer[2]
    if (nested.count("&&") != 1
            or any(ord(character) < 32 or character in ";|<>`" for character in nested)
            or "$(" in nested or "${" in nested):
        return None
    try:
        tokens = shlex.split(nested, comments=False, posix=True)
    except ValueError:
        return None
    if (len(tokens) != 8 or tokens[0] not in _CODEX_WC or tokens[1] != "-l"
            or tokens[3] != "&&"):
        return None
    counted = _safe_codex_operand(tokens[2], option_terminated=False)
    read = _codex_sed_path(tokens[4:], nested)
    return read if counted is not None and read == counted else None


def _codex_read_paths(command: object) -> list[str]:
    counted_read = _codex_count_then_sed_path(command)
    if counted_read is not None:
        return [counted_read]
    projected = codex_unbounded_read_paths(command)
    if projected:
        return list(projected)
    tokens = _codex_tokens(command)
    if tokens is None or not isinstance(command, str):
        return []
    if len(tokens) == 3 and tokens[0] in _CODEX_SHELLS and tokens[1] == "-c":
        # Only cat remains unambiguous through one shell wrapper. A full sed
        # range contains '$', whose expansion depends on the wrapper quoting.
        nested = _codex_tokens(tokens[2])
        path = _codex_cat_path(nested or [], tokens[2])
    else:
        path = _codex_cat_path(tokens, command) or _codex_sed_path(tokens, command)
    return [path] if path is not None else []


_CODEX_RG = frozenset({"rg", "/usr/bin/rg", "/opt/homebrew/bin/rg"})
_INJECTED_RUNTIME_ROOTS = frozenset({".agents", ".codex/agents", ".codex-trigger-runtime"})


def _unwrapped_codex_tokens(command: object) -> list[str] | None:
    tokens = _codex_tokens(command)
    if not tokens or tokens[0] not in _CODEX_SHELLS:
        return tokens
    return _codex_tokens(tokens[2]) if len(tokens) == 3 and tokens[1] == "-c" else None


def _consume_rg_glob(arguments: list[str]) -> tuple[str | None, list[str]] | None:
    token, remaining = arguments[0], arguments[1:]
    if token == "--hidden":
        return None, remaining
    if token in {"-g", "--glob"} and remaining:
        return remaining[0], remaining[1:]
    if token.startswith("--glob="):
        return token.removeprefix("--glob="), remaining
    return None


def _canonical_rg_glob(glob: str) -> tuple[bool, str] | None:
    if (not glob or glob == "!" or "\\" in glob or glob.startswith("/")
            or ".." in PurePosixPath(glob).parts or glob.startswith("!!")):
        return None
    return (True, glob[1:]) if glob.startswith("!") and len(glob) > 1 else (False, glob)


def _rg_globs(tokens: list[str]) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    arguments = tokens[2:]
    if arguments[-1:] == ["."]:
        arguments = arguments[:-1]
    includes: list[str] = []
    excludes: list[str] = []
    while arguments:
        consumed = _consume_rg_glob(arguments)
        if consumed is None:
            return None
        glob, arguments = consumed
        if glob is None:
            continue
        canonical = _canonical_rg_glob(glob)
        if canonical is None:
            return None
        excluded, pattern = canonical
        (excludes if excluded else includes).append(pattern)
    return (tuple(includes), tuple(excludes)) if includes else None


def _rg_files_query(command: object) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    """Parse one side-effect-free, root-recursive ``rg --files`` projection."""
    tokens = _unwrapped_codex_tokens(command)
    if not tokens or tokens[0] not in _CODEX_RG or tokens[1:2] != ["--files"]:
        return None
    return _rg_globs(tokens)


def _rg_matches(path: str, pattern: str) -> bool:
    if "/" in pattern:
        return fnmatch.fnmatchcase(path, pattern)
    return fnmatch.fnmatchcase(PurePosixPath(path).name, pattern)


def _scoped_rg_result(
    output: object,
    includes: tuple[str, ...],
    excludes: tuple[str, ...],
    project_artifacts: tuple[str, ...],
) -> list[str] | None:
    if not isinstance(output, str):
        return None
    selected = sorted(
        path for path in project_artifacts
        if any(_rg_matches(path, pattern) for pattern in includes)
        and not any(_rg_matches(path, pattern) for pattern in excludes)
    )
    observed: list[str] = []
    for value in output.splitlines():
        if value.startswith("./"):
            value = value[2:]
        path = _canonical_relative_file(value)
        if path is None:
            return None
        if any(path == root or path.startswith(root + "/") for root in _INJECTED_RUNTIME_ROOTS):
            continue
        if path not in project_artifacts:
            return None
        observed.append(path)
    if len(set(observed)) != len(observed) or sorted(observed) != selected:
        return None
    return selected


def file_accesses(
    observation: object,
    *,
    fixture_read_witnesses: Mapping[str, object] | None = None,
) -> list[dict[str, object]]:
    """Derive successful exact-path read-operation evidence.

    Unbounded native operations prove only a successful exact-path operation;
    their output may still be truncated. Bounded Codex sed operations qualify
    only when their exact output matches explicit controller-owned byte-count
    and sha256 witnesses. Subject-supplied native metadata is never a witness.
    Claude provenance requires the unaliased native ``Read`` name; callers that
    apply tool aliases must derive these facts from an unaliased observation.
    """
    if not isinstance(observation, dict) or not isinstance(observation.get("tool_calls"), list):
        return []
    metadata = observation.get("native_metadata")
    cwd = metadata.get("cwd") if isinstance(metadata, dict) else None
    accesses: list[dict[str, object]] = []
    for index, call in enumerate(observation["tool_calls"]):
        if not isinstance(call, dict) or call.get("success") is not True:
            continue
        paths: list[str] = []
        claude_path = _claude_read_path(call, cwd)
        if claude_path is not None:
            paths = [claude_path]
        elif call.get("name") == "command_execution" and isinstance(call.get("input"), dict):
            paths = _codex_read_paths(call["input"].get("command"))
        accesses.extend({
            "operation": "read_file", "path": path, "tool_call_index": index,
        } for path in paths)
    bound_witnesses = bound_fixture_read_witnesses(observation)
    if fixture_read_witnesses is not None and bound_witnesses is not None:
        raise CaptureError("fixture read witnesses have multiple authorities")
    trusted_witnesses = fixture_read_witnesses if fixture_read_witnesses is not None else bound_witnesses
    if trusted_witnesses is not None:
        accesses.extend(fixture_read_accesses(observation, trusted_witnesses))
    return accesses


def _events(raw: str) -> list[dict[str, Any]]:
    events = []
    for number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(
                line,
                object_pairs_hook=_unique_object,
                parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"invalid constant {token}")),
            )
        except (json.JSONDecodeError, ValueError) as exc:
            raise CaptureError(f"invalid JSONL at line {number}") from exc
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise CaptureError(f"invalid native event at line {number}")
        events.append(event)
    if not events:
        raise CaptureError("empty native capture")
    return events


def _usage(terminal: Mapping[str, Any]) -> dict[str, Any]:
    usage = terminal.get("usage")
    if not isinstance(usage, dict):
        raise CaptureError("terminal event omitted usage")
    for key, value in usage.items():
        if key.endswith("tokens") and (type(value) is not int or value < 0):
            raise CaptureError(f"invalid native usage field: {key}")
    for key in ("input_tokens", "output_tokens"):
        if key not in usage:
            raise CaptureError(f"missing native usage field: {key}")
    return dict(usage)


def _observation(terminal: Mapping[str, Any], text: str) -> dict[str, Any]:
    if not isinstance(text, str):
        raise CaptureError("native final response is not text")
    return {"completed": True, "error": None, "final_text": text,
            "activations": [], "tool_calls": [], "artifacts": {}, "usage": _usage(terminal)}


def _search_query(call: Mapping[str, Any], host: str, cwd: object) -> str | None:
    inputs = call.get("input")
    if (not isinstance(inputs, dict) or call.get("success") is not True
            or call.get("parent_id") is not None):
        return None
    if host == "claude":
        if (call.get("name") != "Glob" or not {"pattern"} <= inputs.keys() <= {"pattern", "path"}
                or _absolute_posix_path(cwd) is None
                or not isinstance(inputs.get("path", "."), str)
                or inputs.get("path", ".") not in {".", cwd}):
            return None
        pattern = inputs["pattern"]
    elif host == "codex" and call.get("name") == "command_execution" and set(inputs) == {"command"}:
        pattern = _codex_find_pattern(inputs["command"])
        if pattern is None:
            return None
    else:
        return None
    try:
        _search_glob(pattern)
    except ValueError:
        return None
    return pattern


def _codex_find_pattern(command: object, *, allow_shell: bool = True) -> str | None:
    """Parse one exact, unbounded Codex ``find`` command into its glob."""
    tokens = _codex_tokens(command)
    if allow_shell and tokens and tokens[0] in _CODEX_SHELLS:
        if len(tokens) != 3 or tokens[1] != "-c":
            return None
        command = tokens[2]
        tokens = _codex_tokens(command)
    if tokens is None or not isinstance(command, str):
        return None
    matched = re.fullmatch(
        r"""(?:find|/usr/bin/find) \. -type f -name (['"])([A-Za-z0-9*?_.-]+)\1 -print""",
        command,
    )
    if matched is None:
        return None
    pattern = "**/" + matched[2]
    try:
        _search_glob(pattern)
    except ValueError:
        return None
    return pattern


def _codex_compound_empty_lines(call: Mapping[str, Any]) -> list[str]:
    """Return exact newline-separated find commands from one empty Codex call."""
    inputs = call.get("input")
    signature = (
        call.get("name"), call.get("success"), call.get("parent_id"), call.get("output")
    )
    if signature != ("command_execution", True, None, ""):
        return []
    if not isinstance(inputs, dict) or set(inputs) != {"command"}:
        return []
    command = inputs["command"]
    if not isinstance(command, str) or "\r" in command:
        return []
    try:
        outer = shlex.split(command, comments=False, posix=True)
    except ValueError:
        return []
    if len(outer) != 3 or outer[0] not in _CODEX_SHELLS or outer[1] != "-c":
        return []
    lines = outer[2].split("\n")
    return lines if len(lines) >= 2 and all(line and line == line.strip() for line in lines) else []


def _codex_compound_empty_searches(
    call: Mapping[str, Any], index: int,
) -> list[dict[str, object]]:
    """Project newline-separated exact finds only when all returned no matches."""
    patterns = [_codex_find_pattern(line, allow_shell=False) for line in _codex_compound_empty_lines(call)]
    if not patterns or None in patterns or len(patterns) != len(set(patterns)):
        return []
    return [
        {"pattern": pattern, "paths": [], "tool_call_index": index}
        for pattern in patterns
    ]


def _search_paths(output: object, pattern: str, host: str, cwd: object) -> list[str] | None:
    if not isinstance(output, str):
        return None
    if output == ("No files found" if host == "claude" else ""):
        return []
    if not output:
        return None
    paths = []
    for value in output.splitlines():
        if value.startswith("/"):
            absolute, root = _absolute_posix_path(value), _absolute_posix_path(cwd)
            if absolute is None or root is None or not absolute.is_relative_to(root):
                return None
            value = absolute.relative_to(root).as_posix()
        elif value.startswith("./"):
            value = value[2:]
        canonical = _canonical_relative_file(value)
        if canonical is None or not fnmatch.fnmatchcase(PurePosixPath(canonical).name, pattern[3:]):
            return None
        paths.append(canonical)
    return sorted(paths) if len(set(paths)) == len(paths) else None


def _complete_glob_result(metadata: object, index: int, call: dict, pattern: str, paths: list) -> bool:
    if not isinstance(metadata, dict) or not isinstance(metadata.get("claude_tool_results"), list):
        return False
    records = [
        row for row in metadata["claude_tool_results"]
        if isinstance(row, dict) and row.get("tool_call_index") == index
        and row.get("id") == call.get("id") and row.get("native_name") == "Glob"
    ]
    if len(records) != 1:
        return False
    result = records[0].get("glob_result")
    if not isinstance(result, dict):
        return False
    names = result.get("filenames")
    if (not isinstance(names, list) or not all(isinstance(name, str) for name in names)
            or result.get("truncated") is not False or result.get("countIsComplete") is not True
            or type(result.get("numFiles")) is not int or result["numFiles"] != len(names)
            or type(result.get("totalMatches")) is not int or result["totalMatches"] != len(names)):
        return False
    output = "\n".join(names) if names else "No files found"
    return _search_paths(output, pattern, "claude", metadata.get("cwd")) == paths


def _scoped_rg_row(
    call: dict[str, object], index: int, project_artifacts: tuple[str, ...] | None,
) -> dict[str, object] | None:
    supplied = call.get("input")
    if (project_artifacts is None or call.get("name") != "command_execution"
            or call.get("success") is not True or call.get("parent_id") is not None
            or not isinstance(supplied, dict) or set(supplied) != {"command"}):
        return None
    query = _rg_files_query(supplied["command"])
    if query is None:
        return None
    includes, excludes = query
    paths = _scoped_rg_result(call.get("output"), includes, excludes, project_artifacts)
    if paths is None:
        return None
    return {
        "patterns": list(includes),
        "excluded_patterns": list(excludes),
        "paths": paths,
        "project_artifacts": list(project_artifacts),
        "scope": "controller-project-artifacts",
        "tool_call_index": index,
    }


def _legacy_search_row(
    call: dict[str, object], index: int, host: str, cwd: object, metadata: object,
) -> dict[str, object] | None:
    pattern = _search_query(call, host, cwd)
    if pattern is None:
        return None
    paths = _search_paths(call.get("output"), pattern, host, cwd)
    if paths is None or (
        host == "claude" and not _complete_glob_result(metadata, index, call, pattern, paths)
    ):
        return None
    return {"pattern": pattern, "paths": paths, "tool_call_index": index}


def _file_search_rows(
    call: dict[str, object], index: int, host: str, cwd: object,
    metadata: object, project_artifacts: tuple[str, ...] | None,
) -> list[dict[str, object]]:
    if host == "codex":
        compound = _codex_compound_empty_searches(call, index)
        if compound:
            return compound
        row = _scoped_rg_row(call, index, project_artifacts)
    else:
        row = None
    row = row or _legacy_search_row(call, index, host, cwd, metadata)
    return [row] if row is not None else []


def file_search_results(observation: object, *, host: str) -> list[dict[str, object]]:
    """Derive complete root-recursive search results, never absence from prose.

    Only native Glob and a single unbounded find invocation qualify. Pipelines,
    redirection, login shells, depth limits, failed calls, malformed output and
    outside-root paths and child calls with unbound working directories do not.
    Glob additionally requires its native structured result to affirm complete,
    untruncated matching counts. Legacy results include runtime files. A Codex
    ``rg --files`` projection is accepted only when a controller-bound authored
    project scope proves its complete result; exact injected runtime roots are
    ignored in that scope.
    This function deliberately does not hide any path or claim that discovery
    implies file contents were read.
    """
    if not isinstance(observation, dict) or not isinstance(observation.get("tool_calls"), list):
        return []
    metadata = observation.get("native_metadata")
    cwd = metadata.get("cwd") if isinstance(metadata, dict) else None
    project_artifacts = bound_project_artifact_paths(observation)
    results: list[dict[str, object]] = []
    for index, call in enumerate(observation["tool_calls"]):
        if isinstance(call, dict):
            results.extend(_file_search_rows(call, index, host, cwd, metadata, project_artifacts))
    return results


def _claude_blocks(events: list[dict[str, Any]]):
    for position, event in enumerate(events):
        if event["type"] not in {"assistant", "user"}:
            continue
        message = event.get("message")
        if not isinstance(message, dict):
            raise CaptureError("Claude message is malformed")
        if "content" not in message:
            raise CaptureError("Claude message omitted content")
        content = message["content"]
        if not isinstance(content, list) or any(not isinstance(block, dict) for block in content):
            raise CaptureError("Claude message content is malformed")
        for block in content:
            yield position, event, block


def _claude_tool_progress(
    events: list[dict[str, Any]], calls: Mapping[str, Mapping[str, Any]],
    results: Mapping[str, Mapping[str, Any]],
) -> None:
    progress_ids: set[str] = set()
    for position, event in enumerate(events):
        if event.get("type") != "tool_progress":
            continue
        parent = event.get("parent_tool_use_id")
        progress_id = event.get("tool_use_id")
        elapsed = event.get("elapsed_time_seconds")
        owner = calls.get(parent) if isinstance(parent, str) else None
        owner_result = results.get(parent) if isinstance(parent, str) else None
        if (not isinstance(parent, str) or not parent or owner is None
                or owner_result is None or owner["position"] >= position
                or owner_result["position"] <= position
                or event.get("tool_name") != owner["name"]
                or event.get("heartbeat") is not True
                or type(elapsed) is not int or elapsed <= 0
                or not isinstance(progress_id, str)
                or re.fullmatch(re.escape(parent) + r"-heartbeat-[0-9]+", progress_id) is None
                or progress_id in progress_ids):
            raise CaptureError("Claude tool progress identity is invalid")
        progress_ids.add(progress_id)


def _claude_calls(events: list[dict[str, Any]]) \
        -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    calls: dict[str, dict[str, Any]] = {}
    results: dict[str, dict[str, Any]] = {}
    for position, event, block in _claude_blocks(events):
        if block.get("type") == "tool_use":
            identity, name = block.get("id"), block.get("name")
            if event["type"] != "assistant" or not isinstance(identity, str) or not identity or identity in calls:
                raise CaptureError("Claude tool invocation identity is invalid or duplicated")
            if not isinstance(name, str) or not name or not isinstance(block.get("input"), dict):
                raise CaptureError("Claude tool invocation is malformed")
            calls[identity] = {"id": identity, "name": name, "input": block["input"],
                               "position": position, "parent_id": event.get("parent_tool_use_id")}
        elif block.get("type") == "tool_result":
            identity = block.get("tool_use_id")
            if event["type"] != "user" or identity not in calls or identity in results:
                raise CaptureError("Claude tool result is orphaned or duplicated")
            if "is_error" in block and type(block["is_error"]) is not bool:
                raise CaptureError("Claude tool error flag is not boolean")
            results[identity] = {"block": block, "position": position, "native_result": event.get("tool_use_result"),
                                 "parent_id": event.get("parent_tool_use_id")}
    if calls.keys() != results.keys():
        raise CaptureError("Claude capture has unfinished tool invocations")
    _claude_tool_progress(events, calls, results)
    for position, event in enumerate(events):
        parent = event.get("parent_tool_use_id")
        if parent is None or event.get("type") == "tool_progress":
            continue
        owner = calls.get(parent)
        if (not isinstance(parent, str) or not parent or owner is None
                or owner["name"] != "Agent" or owner["position"] >= position):
            raise CaptureError("Claude event has an invalid parent tool identity")
    completion_evidence = []
    for call_index, (identity, call) in enumerate(calls.items()):
        result = results[identity]
        if result["parent_id"] != call["parent_id"] or result["position"] <= call["position"]:
            raise CaptureError("Claude tool result has mismatched ownership")
        block = result["block"]
        call["success"] = not block.get("is_error", False)
        call["output"] = block.get("content", "")
        try:
            encoded = json.dumps(call["output"], ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":"), allow_nan=False).encode("utf-8")
        except (TypeError, ValueError, UnicodeError) as exc:
            raise CaptureError("Claude tool result content is not strict JSON") from exc
        completion_evidence.append({
            "tool_call_index": call_index,
            "id": identity,
            "native_name": call["name"],
            "tool_use_position": call["position"],
            "tool_result_position": result["position"],
            "output_sha256": hashlib.sha256(encoded).hexdigest(),
            "output_bytes": len(encoded),
        })
        if call["name"] == "Glob" and isinstance(result["native_result"], dict):
            completion_evidence[-1]["glob_result"] = {
                key: result["native_result"].get(key)
                for key in ("filenames", "numFiles", "truncated", "totalMatches", "countIsComplete")
            }
    return list(calls.values()), completion_evidence


def _claude_hook_prelude(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Allow exactly one successful SessionStart hook pair before stream init.

    The documented stream lifecycle begins at ``init``.  Captured Claude Code
    2.1.272 plugin runs can prepend this paired hook metadata, which is retained
    as evidence but is never treated as agent work.
    """
    init_index = next((index for index, event in enumerate(events) if event["type"] == "system"
                       and event.get("subtype") == "init" and event.get("parent_tool_use_id") is None), None)
    if init_index in (None, 0):
        return [], events
    prelude, runtime = events[:init_index], events[init_index:]
    if len(prelude) != 2:
        raise CaptureError("Claude pre-init events are not a single hook pair")
    started, response = prelude
    if not all(event.get("type") == "system" and event.get("parent_tool_use_id") is None for event in prelude):
        raise CaptureError("Claude hook prelude contains agent work or nested events")
    if started.get("subtype") != "hook_started" or response.get("subtype") != "hook_response":
        raise CaptureError("Claude hook prelude is orphaned, duplicated, or unknown")
    session = started.get("session_id")
    identities = [started.get("uuid"), response.get("uuid")]
    if (not isinstance(session, str) or not session
            or response.get("session_id") != session or runtime[0].get("session_id") != session
            or any(not isinstance(identity, str) or not identity for identity in identities)
            or len(set(identities)) != len(identities)):
        raise CaptureError("Claude hook prelude has mismatched session or identity")
    for key in ("hook_id", "hook_name", "hook_event"):
        if (not isinstance(started.get(key), str) or not started[key]
                or response.get(key) != started[key]):
            raise CaptureError("Claude hook prelude metadata is mismatched")
    if started["hook_event"] != "SessionStart":
        raise CaptureError("Claude hook prelude is not a SessionStart hook")
    if (response.get("outcome") != "success" or response.get("exit_code") != 0
            or response.get("is_error", False) is not False
            or any(not isinstance(response.get(key), str) for key in ("output", "stdout", "stderr"))):
        raise CaptureError("Claude hook prelude did not complete successfully")
    init_identity = runtime[0].get("uuid")
    if isinstance(init_identity, str) and init_identity in identities:
        raise CaptureError("Claude hook prelude duplicated initialization identity")
    return prelude, runtime


def _claude_cleanup_epilogue(
    events: list[dict[str, Any]], prelude: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Separate the exact root-task cleanup emitted after a successful result."""
    results = [index for index, event in enumerate(events)
               if event["type"] == "result" and event.get("parent_tool_use_id") is None]
    if not results or results[-1] == len(events) - 1:
        return events, []

    result_index = results[-1]
    runtime, cleanup = events[:result_index + 1], events[result_index + 1:]
    expected = ("background_tasks_changed", "task_updated", "task_notification")
    if (len(cleanup) != len(expected)
            or tuple(event.get("subtype") for event in cleanup) != expected
            or any(event.get("type") != "system"
                   or event.get("parent_tool_use_id") is not None for event in cleanup)):
        raise CaptureError("Claude post-result events are not the root cleanup epilogue")

    init, terminal = runtime[0], runtime[-1]
    session = init.get("session_id")
    if (not isinstance(session, str) or not session
            or terminal.get("session_id") != session
            or any(event.get("session_id") != session for event in cleanup)):
        raise CaptureError("Claude cleanup epilogue has mismatched session identity")

    identities = [event.get("uuid") for event in cleanup]
    prior_identities = {
        event.get("uuid") for event in [*prelude, *runtime]
        if isinstance(event.get("uuid"), str)
    }
    if (any(not isinstance(identity, str) or not identity for identity in identities)
            or len(set(identities)) != len(identities)
            or not set(identities).isdisjoint(prior_identities)):
        raise CaptureError("Claude cleanup epilogue has missing or duplicate event identity")

    changed, updated, notification = cleanup
    if changed.get("tasks") != []:
        raise CaptureError("Claude cleanup epilogue did not empty the background task set")
    task_id = notification.get("task_id")
    tool_use_id = notification.get("tool_use_id")
    if (not isinstance(task_id, str) or not task_id
            or not isinstance(tool_use_id, str) or not tool_use_id
            or updated.get("task_id") != task_id):
        raise CaptureError("Claude cleanup epilogue has mismatched task or tool identity")
    patch = updated.get("patch")
    if (not isinstance(patch, dict) or set(patch) != {"status", "end_time"}
            or patch.get("status") != "killed"
            or type(patch.get("end_time")) is not int or patch["end_time"] < 0
            or notification.get("status") != "stopped"
            or not isinstance(notification.get("output_file"), str)
            or not notification["output_file"].startswith("/")
            or not isinstance(notification.get("summary"), str)
            or not notification["summary"]):
        raise CaptureError("Claude cleanup epilogue is malformed")

    starts = [
        (index, event) for index, event in enumerate(runtime[:-1])
        if event.get("subtype") == "task_started"
        and (event.get("task_id") == task_id or event.get("tool_use_id") == tool_use_id)
    ]
    if len(starts) != 1:
        raise CaptureError("Claude cleanup epilogue is not bound to one prior task")
    start_index, started = starts[0]
    if (started.get("type") != "system" or started.get("parent_tool_use_id") is not None
            or started.get("session_id") != session or started.get("task_id") != task_id
            or started.get("tool_use_id") != tool_use_id
            or not isinstance(started.get("description"), str) or not started["description"]
            or notification["summary"] != started["description"]):
        raise CaptureError("Claude cleanup epilogue does not match its prior task start")

    tool_uses = [
        (position, block) for position, _event, block in _claude_blocks(runtime[:start_index])
        if block.get("type") == "tool_use" and block.get("id") == tool_use_id
    ]
    if len(tool_uses) != 1:
        raise CaptureError("Claude cleanup task is not bound to one prior tool use")

    terminal_statuses = {"completed", "failed", "killed", "stopped"}
    for event in runtime[start_index + 1:-1]:
        if event.get("type") != "system" or event.get("session_id") != session:
            continue
        subtype = event.get("subtype")
        if subtype == "task_updated" and event.get("task_id") == task_id:
            task_patch = event.get("patch")
            if not isinstance(task_patch, dict):
                raise CaptureError("Claude cleanup task update is malformed")
            if task_patch.get("status") in terminal_statuses:
                raise CaptureError("Claude cleanup task was already terminal before the result")
        elif subtype == "task_notification" and event.get("task_id") == task_id:
            if event.get("status") in terminal_statuses:
                raise CaptureError("Claude cleanup task was already terminal before the result")
        elif subtype == "background_tasks_changed":
            tasks = event.get("tasks")
            if (not isinstance(tasks, list)
                    or not any(isinstance(task, dict) and task.get("task_id") == task_id
                               for task in tasks)):
                raise CaptureError("Claude cleanup task was not active before the result")
    return runtime, cleanup


def _claude_backgrounded_bash_result_position(
    events: list[dict[str, Any]], *, start_index: int, bridge_start: int,
    session: str, task_id: str, tool_use_id: str, output_file: str,
) -> int:
    results = [
        (position, event, block)
        for position, event, block in _claude_blocks(events[start_index + 1:bridge_start])
        if block.get("type") == "tool_result" and block.get("tool_use_id") == tool_use_id
    ]
    if len(results) != 1:
        raise CaptureError("Claude backgrounded Bash continuation has no unique tool result")
    relative_position, result_event, result_block = results[0]
    native_result = result_event.get("tool_use_result")
    expected_native_fields = {
        "stdout", "stderr", "interrupted", "isImage", "noOutputExpected",
        "backgroundTaskId", "timedOutAfterMs",
    }
    content = result_block.get("content")
    if (result_event.get("session_id") != session
            or result_event.get("parent_tool_use_id") is not None
            or result_block.get("is_error") is not False
            or not isinstance(content, str)
            or f"(ID: {task_id})" not in content
            or output_file not in content
            or not isinstance(native_result, dict)
            or set(native_result) != expected_native_fields
            or native_result.get("backgroundTaskId") != task_id
            or type(native_result.get("timedOutAfterMs")) is not int
            or native_result["timedOutAfterMs"] <= 0
            or native_result.get("interrupted") is not False
            or native_result.get("isImage") is not False
            or native_result.get("noOutputExpected") is not False
            or not isinstance(native_result.get("stdout"), str)
            or not isinstance(native_result.get("stderr"), str)):
        raise CaptureError("Claude backgrounded Bash tool result is malformed")
    return start_index + 1 + relative_position


def _claude_continuation_task_type(
    events: list[dict[str, Any]], *, start_index: int, bridge_start: int,
    session: str, started: dict[str, Any], tool_use: dict[str, Any],
    notification: dict[str, Any], terminal_status: Any,
) -> str | None:
    tool_input = tool_use.get("input")
    if tool_use.get("name") == "Agent":
        if (started.get("is_backgrounded") is not True
                or not isinstance(tool_input, dict)
                or tool_input.get(
                    "run_in_background", started.get("task_type") == "local_agent",
                ) is not True
                or terminal_status != "completed"
                or notification.get("status") != "completed"):
            raise CaptureError("Claude continuation task was not launched as a background Agent")
        return None
    if tool_use.get("name") != "Bash":
        raise CaptureError("Claude continuation task used an unsupported native tool")

    task_id = started["task_id"]
    tool_use_id = started["tool_use_id"]
    if (started.get("is_backgrounded") is not False
            or started.get("task_type") != "local_bash"
            or terminal_status not in {"completed", "failed"}
            or notification.get("status") != terminal_status):
        raise CaptureError("Claude backgrounded Bash continuation is malformed")
    result_position = _claude_backgrounded_bash_result_position(
        events, start_index=start_index, bridge_start=bridge_start,
        session=session, task_id=task_id, tool_use_id=tool_use_id,
        output_file=notification["output_file"],
    )
    active_positions = []
    backgrounded_positions = []
    for position in range(start_index + 1, bridge_start):
        event = events[position]
        if event.get("type") != "system" or event.get("session_id") != session:
            continue
        subtype = event.get("subtype")
        if subtype == "background_tasks_changed":
            tasks = event.get("tasks")
            if (not isinstance(tasks, list)
                    or any(not isinstance(task, dict) for task in tasks)):
                raise CaptureError("Claude backgrounded Bash task set is malformed")
            matching = [task for task in tasks if task.get("task_id") == task_id]
            if matching:
                if (len(matching) != 1
                        or matching[0].get("task_type") != "local_bash"
                        or matching[0].get("description") != started["description"]):
                    raise CaptureError("Claude backgrounded Bash task set is mismatched")
                active_positions.append(position)
        elif subtype == "task_updated" and event.get("task_id") == task_id:
            if event.get("patch") != {"is_backgrounded": True}:
                raise CaptureError("Claude backgrounded Bash update is malformed")
            backgrounded_positions.append(position)
        elif subtype == "task_notification" and event.get("task_id") == task_id:
            raise CaptureError("Claude backgrounded Bash completed before its bridge")
    if (len(backgrounded_positions) != 1 or not active_positions
            or not (start_index < active_positions[0] < backgrounded_positions[0]
                    < result_position < bridge_start)):
        raise CaptureError("Claude backgrounded Bash lifecycle is incomplete or reordered")
    return "local_bash"


def _claude_continuation_records(
    events: list[dict[str, Any]], *, prior_init_index: int, init_index: int,
) -> tuple[list[int], list[dict[str, Any]]]:
    if init_index < 3:
        raise CaptureError("Claude continuation omitted its completion bridge")
    expected = ("background_tasks_changed", "task_updated", "task_notification")
    candidates = [
        list(range(position, position + 3))
        for position in range(prior_init_index + 1, init_index - 2)
        if tuple(events[index].get("subtype") for index in range(position, position + 3))
        == expected
        and all(events[index].get("type") == "system"
                and events[index].get("parent_tool_use_id") is None
                for index in range(position, position + 3))
    ]
    if len(candidates) != 1:
        raise CaptureError("Claude continuation bridge is missing, reordered, or not root-owned")
    positions = candidates[0]
    return positions, [events[position] for position in positions]


def _claude_continuation_task_shape(
    events: list[dict[str, Any]], *, prior_init_index: int,
    bridge: list[dict[str, Any]],
) -> tuple[str, str, str, Any]:
    changed, updated, notification = bridge
    session = events[prior_init_index].get("session_id")
    if any(event.get("session_id") != session for event in bridge):
        raise CaptureError("Claude continuation bridge has a foreign session")
    task_id = notification.get("task_id")
    tool_use_id = notification.get("tool_use_id")
    remaining = changed.get("tasks")
    if (not isinstance(remaining, list)
            or not all(isinstance(item, dict)
                       and isinstance(item.get("task_id"), str) and item["task_id"]
                       and isinstance(item.get("task_type"), str) and item["task_type"]
                       and isinstance(item.get("description"), str) and item["description"]
                       for item in remaining)
            or len({item["task_id"] for item in remaining}) != len(remaining)
            or task_id in {item["task_id"] for item in remaining}):
        raise CaptureError("Claude continuation bridge has a malformed remaining task set")
    patch = updated.get("patch")
    if (not isinstance(task_id, str) or not task_id
            or not isinstance(tool_use_id, str) or not tool_use_id
            or updated.get("task_id") != task_id
            or not isinstance(patch, dict) or set(patch) != {"status", "end_time"}
            or type(patch.get("end_time")) is not int or patch["end_time"] < 0
            or not isinstance(notification.get("output_file"), str)
            or not notification["output_file"].startswith("/")
            or not isinstance(notification.get("summary"), str)
            or not notification["summary"]):
        raise CaptureError("Claude continuation bridge is malformed")
    return session, task_id, tool_use_id, patch.get("status")


def _claude_continuation_suffix(
    events: list[dict[str, Any]], *, bridge_end: int, init_index: int, session: str,
) -> None:
    trailing = events[bridge_end + 1:init_index]
    for event in trailing:
        if event.get("session_id") != session:
            raise CaptureError("Claude continuation suffix has a foreign session")
        if event.get("parent_tool_use_id") is not None:
            continue
        if event.get("type") == "system" and event.get("subtype") in {
            "task_progress", "thinking_tokens",
        }:
            continue
        content = event.get("message", {}).get("content") \
            if isinstance(event.get("message"), dict) else None
        if (event.get("type") == "assistant" and isinstance(content, list)
                and content and all(isinstance(block, dict)
                                    and block.get("type") in {"text", "thinking"}
                                    for block in content)):
            continue
        raise CaptureError("Claude continuation suffix contains root work")


def _claude_continuation_prior_launch(
    events: list[dict[str, Any]], *, bridge_start: int, session: str,
    task_id: str, tool_use_id: str, notification: dict[str, Any],
    terminal_status: Any,
) -> str | None:
    segment = events[:bridge_start]
    starts = [
        (offset, event) for offset, event in enumerate(segment)
        if event.get("type") == "system" and event.get("subtype") == "task_started"
        and (event.get("task_id") == task_id or event.get("tool_use_id") == tool_use_id)
    ]
    if len(starts) != 1:
        raise CaptureError("Claude continuation bridge is not bound to one prior task")
    start_index, started = starts[0]
    if (started.get("parent_tool_use_id") is not None
            or started.get("session_id") != session
            or started.get("task_id") != task_id
            or started.get("tool_use_id") != tool_use_id
            or not isinstance(started.get("description"), str)
            or not started["description"]):
        raise CaptureError("Claude continuation bridge does not match its prior task start")
    tool_uses = [
        (position, block) for position, _event, block in _claude_blocks(
            events[:start_index]
        ) if block.get("type") == "tool_use" and block.get("id") == tool_use_id
    ]
    if len(tool_uses) != 1:
        raise CaptureError("Claude continuation task is not bound to one prior tool use")
    _tool_position, tool_use = tool_uses[0]
    task_type = _claude_continuation_task_type(
        events, start_index=start_index, bridge_start=bridge_start, session=session,
        started=started, tool_use=tool_use, notification=notification,
        terminal_status=terminal_status,
    )

    terminal_statuses = {"completed", "failed", "killed", "stopped"}
    for event in events[start_index + 1:bridge_start]:
        if event.get("type") != "system" or event.get("session_id") != session:
            continue
        if event.get("subtype") == "task_updated" and event.get("task_id") == task_id:
            update = event.get("patch")
            if not isinstance(update, dict):
                raise CaptureError("Claude continuation task update is malformed")
            if update.get("status") in terminal_statuses:
                raise CaptureError("Claude continuation task was already terminal")
        elif (event.get("subtype") == "task_notification"
              and event.get("task_id") == task_id
              and event.get("status") in terminal_statuses):
            raise CaptureError("Claude continuation task was already terminal")
    return task_type


def _claude_continuation_bridge(
    events: list[dict[str, Any]], *, turn: int, init_index: int,
    prior_init_index: int,
) -> dict[str, Any]:
    """Validate the observed background-task bridge into one resumed root turn."""
    positions, bridge = _claude_continuation_records(
        events, prior_init_index=prior_init_index, init_index=init_index,
    )
    session, task_id, tool_use_id, terminal_status = _claude_continuation_task_shape(
        events, prior_init_index=prior_init_index, bridge=bridge,
    )
    _claude_continuation_suffix(
        events, bridge_end=positions[-1], init_index=init_index, session=session,
    )
    task_type = _claude_continuation_prior_launch(
        events, bridge_start=positions[0], session=session, task_id=task_id,
        tool_use_id=tool_use_id, notification=bridge[-1],
        terminal_status=terminal_status,
    )

    record = {
        "from_turn": turn - 1,
        "to_turn": turn,
        "positions": positions,
        "task_id": task_id,
        "tool_use_id": tool_use_id,
        "records": bridge,
    }
    if task_type == "local_bash":
        record.update(task_type=task_type, terminal_status=terminal_status)
    return record


def claude_continuation_layout(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate Claude root turns and return their ordered, evidence-bound layout."""
    starts = [i for i, event in enumerate(events) if event["type"] == "system"
              and event.get("subtype") == "init" and event.get("parent_tool_use_id") is None]
    ends = [i for i, event in enumerate(events) if event["type"] == "result"
            and event.get("parent_tool_use_id") is None]
    if not starts or not ends or starts[0] != 0 or ends[-1] != len(events) - 1 or len(starts) != len(ends):
        raise CaptureError("Claude lifecycle is missing, duplicated, or out of order")
    if any(start >= end for start, end in zip(starts, ends)):
        raise CaptureError("Claude result precedes its initialization")
    bridges: list[dict[str, Any]] = []
    if len(starts) > 1:
        if ends != list(range(ends[0], len(events))):
            raise CaptureError("Claude continuation results are not one contiguous suffix")
        indexes = [events[index].get("result_index") for index in ends]
        if any(type(value) is not int for value in indexes) or indexes != list(range(len(ends))):
            raise CaptureError("Claude continuation result indexes are invalid")
        if any(events[index].get("origin") != {"kind": "task-notification"}
               for index in ends[1:]):
            raise CaptureError("Claude continuation result origin is not a task notification")
        identities = [event.get("uuid") for event in events]
        if (any(not isinstance(identity, str) or not identity for identity in identities)
                or len(set(identities)) != len(identities)):
            raise CaptureError("Claude continuation has missing or duplicate event identity")

        session = events[0].get("session_id")
        if (not isinstance(session, str) or not session
                or any(event.get("session_id") != session
                       for event in [events[index] for index in starts + ends])):
            raise CaptureError("Claude continuation has a mismatched session")
        canonical_init = {key: value for key, value in events[starts[0]].items() if key != "uuid"}
        for turn, index in enumerate(starts[1:], 1):
            resumed = {key: value for key, value in events[index].items() if key != "uuid"}
            if resumed != canonical_init:
                raise CaptureError("Claude continuation changed its initialization record")
            bridges.append(_claude_continuation_bridge(
                events, turn=turn, init_index=index, prior_init_index=starts[turn - 1],
            ))
    for index in ends:
        terminal = events[index]
        if terminal.get("is_error") is not False or terminal.get("subtype") != "success":
            raise CaptureError("Claude native run failed: " + str(terminal.get("result", terminal.get("errors", "unknown error"))))
        _observation(terminal, terminal.get("result"))
        _claude_tree_usage(terminal)
    if any(event["type"] == "error" for event in events):
        raise CaptureError("Claude capture includes a native error event")
    turns = []
    for turn, (start, end) in enumerate(zip(starts, ends)):
        terminal = events[end]
        turns.append({
            "turn_index": turn,
            "init_position": start,
            "init_uuid": events[start].get("uuid"),
            "result_position": end,
            "result_uuid": terminal.get("uuid"),
            "result_index": terminal.get("result_index"),
            "origin": terminal.get("origin"),
        })
    return {"turns": turns, "bridges": bridges}


def _claude_tree_usage(terminal: Mapping[str, Any]) -> dict[str, int] | None:
    # Native modelUsage is cumulative, including subagents. Never sum result
    # events: streaming continuations repeat the same whole-call totals.
    models = terminal.get("modelUsage")
    if models is None:
        return None
    if not isinstance(models, dict) or not models:
        raise CaptureError("Claude cumulative model usage is malformed")
    totals = dict.fromkeys(("input_tokens", "output_tokens", "cached_input_tokens",
                           "cache_creation_input_tokens", "reasoning_output_tokens"), 0)
    for usage in models.values():
        if not isinstance(usage, dict):
            raise CaptureError("Claude model usage entry is malformed")
        fields = ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens")
        for key in (*fields, "thinkingTokens"):
            value = usage.get(key, 0 if key == "thinkingTokens" else None)
            if type(value) is not int or value < 0:
                raise CaptureError(f"invalid Claude cumulative usage field: {key}")
        totals["input_tokens"] += usage["inputTokens"] + usage["cacheReadInputTokens"] + usage["cacheCreationInputTokens"]
        totals["output_tokens"] += usage["outputTokens"]
        totals["cached_input_tokens"] += usage["cacheReadInputTokens"]
        totals["cache_creation_input_tokens"] += usage["cacheCreationInputTokens"]
        totals["reasoning_output_tokens"] += usage.get("thinkingTokens", 0)
    return totals


def _bind_claude_backgrounded_bash_outcomes(
    calls: list[dict[str, Any]], bridges: list[dict[str, Any]],
) -> None:
    outcomes = {
        bridge["tool_use_id"]: bridge["terminal_status"]
        for bridge in bridges if bridge.get("task_type") == "local_bash"
    }
    for call in calls:
        if call["id"] not in outcomes:
            continue
        if call["name"] != "Bash":
            raise CaptureError("Claude background task outcome changed native tool identity")
        call["success"] = outcomes[call["id"]] == "completed"


def _claude(events: list[dict[str, Any]], namespace: str) -> dict[str, Any]:
    prelude, runtime = _claude_hook_prelude(events)
    runtime, cleanup = _claude_cleanup_epilogue(runtime, prelude)
    lifecycle = claude_continuation_layout(runtime)
    terminal = runtime[-1]
    result = _observation(terminal, terminal.get("result"))
    result["tool_calls"], completions = _claude_calls(runtime)
    _bind_claude_backgrounded_bash_outcomes(result["tool_calls"], lifecycle["bridges"])
    prefix = namespace + ":"
    for call in result["tool_calls"]:
        if call["name"] == "Skill" and call["success"]:
            skill = call["input"].get("skill")
            if not isinstance(skill, str) or not skill.strip():
                raise CaptureError("completed Skill invocation omitted its target")
            result["activations"].append(skill[len(prefix):] if skill.startswith(prefix) else skill)
    result["native_metadata"] = {
        key: runtime[0].get(key) for key in ("model", "cwd", "plugins", "tools", "skills")
    }
    if prelude:
        result["native_metadata"]["hook_prelude"] = prelude
    if cleanup:
        result["native_metadata"]["cleanup_epilogue"] = cleanup
    result["native_metadata"]["claude_tool_results"] = completions
    result["native_metadata"].update(
        native_turns=len(lifecycle["turns"]), claude_turns=lifecycle["turns"],
        continuation_bridges=lifecycle["bridges"], last_turn_usage=result["usage"],
        usage_scope="main-loop-last-turn",
    )
    tree_usage = _claude_tree_usage(terminal)
    if tree_usage is not None:
        result["usage"] = tree_usage
        result["native_metadata"]["usage_scope"] = "cumulative-agent-tree"
    return result


_CODEX_ITEMS = {"agent_message", "reasoning", "command_execution", "file_change",
                "mcp_tool_call", "collab_tool_call", "web_search", "todo_list", "error"}


def _codex_items(events: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    started: dict[str, dict[str, Any]] = {}
    completed: dict[str, tuple[int, dict[str, Any]]] = {}
    for position, event in enumerate(events):
        if not event["type"].startswith("item."):
            continue
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") not in _CODEX_ITEMS:
            raise CaptureError("unsupported Codex item type")
        identity = item.get("id")
        if not isinstance(identity, str) or not identity or item["type"] == "error":
            raise CaptureError("invalid or failed Codex item")
        if event["type"] == "item.started":
            if identity in started or identity in completed:
                raise CaptureError("duplicate Codex item start")
            started[identity] = item
        elif event["type"] == "item.completed":
            if identity in completed:
                raise CaptureError("duplicate Codex completed item")
            if identity in started and started[identity]["type"] != item["type"]:
                raise CaptureError("Codex item changed type during execution")
            if (identity in started and item["type"] == "collab_tool_call"
                    and started[identity].get("tool") != item.get("tool")):
                raise CaptureError("Codex collaboration changed operation during execution")
            completed[identity] = (position, item)
        elif (identity not in started or identity in completed
              or started[identity]["type"] != item["type"]):
            raise CaptureError("Codex item update outside its lifetime")
    if started.keys() - completed.keys():
        raise CaptureError("Codex capture has unfinished items")
    return list(completed.values())


def _codex_call(position: int, item: dict[str, Any]) -> dict[str, Any]:
    kind = item["type"]
    name = kind
    if kind == "command_execution":
        successful = item.get("status") == "completed" and type(item.get("exit_code")) is int and item["exit_code"] == 0
        inputs, output = {"command": item.get("command")}, item.get("aggregated_output", "")
    else:
        if kind == "collab_tool_call":
            operation = item.get("tool")
            if not isinstance(operation, str) or not operation:
                raise CaptureError("Codex collaboration omitted its operation")
            name = operation
        successful = item.get("status") == "completed" and not item.get("error")
        inputs = {key: value for key, value in item.items() if key not in {"id", "type", "status", "result", "error"}}
        output = item.get("result", item.get("error", ""))
    return {"id": item["id"], "name": name, "input": inputs, "output": output,
            "success": successful, "position": position, "parent_id": item.get("parent_id")}


def _codex(events: list[dict[str, Any]], markers: Mapping[str, str]) -> dict[str, Any]:
    types = [event["type"] for event in events]
    allowed = {"thread.started", "turn.started", "turn.completed", "item.started", "item.updated", "item.completed"}
    if any(kind not in allowed for kind in types):
        raise CaptureError("Codex capture includes a failed or unsupported lifecycle event")
    if types[:2] != ["thread.started", "turn.started"] or types[-1] != "turn.completed":
        raise CaptureError("Codex lifecycle is missing or out of order")
    if any(types.count(kind) != 1 for kind in ("thread.started", "turn.started", "turn.completed")):
        raise CaptureError("duplicate Codex lifecycle event")
    items = _codex_items(events)
    messages = []
    for _, item in items:
        if item["type"] != "agent_message":
            continue
        if not isinstance(item.get("text"), str):
            raise CaptureError("Codex agent message is malformed")
        messages.append(item["text"])
    if not messages:
        raise CaptureError("Codex capture omitted its final response")
    result = _observation(events[-1], messages[-1])
    for position, item in items:
        if item["type"] not in {"agent_message", "reasoning", "todo_list"}:
            result["tool_calls"].append(_codex_call(position, item))
    for line in result["final_text"].splitlines():
        marker = line.strip()
        if marker in markers:
            result["activations"].append(markers[marker])
        elif marker.startswith("CODEX_SKILL_FIRED:"):
            raise CaptureError("Codex returned an unmapped selection marker")
    result["native_metadata"] = {"thread_id": events[0].get("thread_id"), "model": None,
                                 "model_evidence": "not emitted by native JSONL; use pinned launch identity"}
    return result


def normalize_trace(host: str, raw: str, *, skill_markers: Mapping[str, str] | None = None,
                    namespace: str = "speckit-pro", tool_aliases: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Return a completed observation or reject untrustworthy native evidence.

    Marker and alias maps must come from the validated staged runtime, never
    inferred from an agent's prose. Artifact content is attached by the executor
    after it has verified termination and confined the declared output paths.
    """
    events = _events(raw)
    if host == "claude":
        result = _claude(events, namespace)
    elif host == "codex":
        result = _codex(events, skill_markers or {})
    else:
        raise CaptureError(f"unsupported native host: {host}")
    ambiguous_codex_kinds = {"command_execution", "file_change", "mcp_tool_call", "web_search"}
    for call in result["tool_calls"]:
        if host == "codex" and call["name"] in ambiguous_codex_kinds:
            continue
        alias = (tool_aliases or {}).get(call["name"], call["name"])
        if not isinstance(alias, str) or not alias:
            raise CaptureError("native tool alias is invalid")
        call["name"] = alias
    return result
