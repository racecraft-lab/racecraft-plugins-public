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
from native_eval_fixture_reads import bound_fixture_read_witnesses, fixture_read_accesses


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
    if len(tokens) == 3 and tokens[1] == "--":
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
        command = inputs["command"]
        tokens = _codex_tokens(command)
        if tokens and tokens[0] in _CODEX_SHELLS:
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
    else:
        return None
    try:
        _search_glob(pattern)
    except ValueError:
        return None
    return pattern


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


def file_search_results(observation: object, *, host: str) -> list[dict[str, object]]:
    """Derive complete root-recursive search results, never absence from prose.

    Only native Glob and a single unbounded find invocation qualify. Pipelines,
    redirection, login shells, depth limits, failed calls, malformed output and
    outside-root paths and child calls with unbound working directories do not.
    Glob additionally requires its native structured
    result to affirm complete, untruncated matching counts. Results include runtime files: filtering a native
    catalog out of a project search requires a separate controller-owned scope.
    This function deliberately does not hide any path or claim that discovery
    implies file contents were read.
    """
    if not isinstance(observation, dict) or not isinstance(observation.get("tool_calls"), list):
        return []
    metadata = observation.get("native_metadata")
    cwd = metadata.get("cwd") if isinstance(metadata, dict) else None
    results = []
    for index, call in enumerate(observation["tool_calls"]):
        if not isinstance(call, dict):
            continue
        pattern = _search_query(call, host, cwd)
        if pattern is None:
            continue
        paths = _search_paths(call.get("output"), pattern, host, cwd)
        if paths is not None and (host != "claude" or _complete_glob_result(metadata, index, call, pattern, paths)):
            results.append({"pattern": pattern, "paths": paths, "tool_call_index": index})
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
    for position, event in enumerate(events):
        parent = event.get("parent_tool_use_id")
        if parent is None:
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


def _claude_lifecycle(events: list[dict[str, Any]]) -> int:
    starts = [i for i, event in enumerate(events) if event["type"] == "system"
              and event.get("subtype") == "init" and event.get("parent_tool_use_id") is None]
    ends = [i for i, event in enumerate(events) if event["type"] == "result"
            and event.get("parent_tool_use_id") is None]
    if not starts or not ends or starts[0] != 0 or ends[-1] != len(events) - 1 or len(starts) != len(ends):
        raise CaptureError("Claude lifecycle is missing, duplicated, or out of order")
    if any(start >= end for start, end in zip(starts, ends)):
        raise CaptureError("Claude result precedes its initialization")
    if len(starts) > 1:
        lifecycle = [events[i] for i in sorted(starts + ends)]
        session = events[0].get("session_id")
        identities = [event.get("uuid") for event in lifecycle]
        if (not isinstance(session, str) or not session
                or any(event.get("session_id") != session for event in lifecycle)
                or any(not isinstance(identity, str) or not identity for identity in identities)
                or len(set(identities)) != len(identities)):
            raise CaptureError("Claude continuation has mismatched session or duplicate event identity")
        for index in starts[1:]:
            if any(events[index].get(key) != events[0].get(key) for key in ("model", "cwd", "plugins")):
                raise CaptureError("Claude continuation changed its runtime identity")
    for index in ends:
        terminal = events[index]
        if terminal.get("is_error") is not False or terminal.get("subtype") != "success":
            raise CaptureError("Claude native run failed: " + str(terminal.get("result", terminal.get("errors", "unknown error"))))
        _observation(terminal, terminal.get("result"))
        _claude_tree_usage(terminal)
    if any(event["type"] == "error" for event in events):
        raise CaptureError("Claude capture includes a native error event")
    return len(ends)


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


def _claude(events: list[dict[str, Any]], namespace: str) -> dict[str, Any]:
    prelude, runtime = _claude_hook_prelude(events)
    native_turns = _claude_lifecycle(runtime)
    terminal = runtime[-1]
    result = _observation(terminal, terminal.get("result"))
    result["tool_calls"], completions = _claude_calls(runtime)
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
    result["native_metadata"]["claude_tool_results"] = completions
    result["native_metadata"].update(native_turns=native_turns, last_turn_usage=result["usage"],
                                     usage_scope="main-loop-last-turn")
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
