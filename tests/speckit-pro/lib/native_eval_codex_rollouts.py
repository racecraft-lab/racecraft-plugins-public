"""Fail-closed supplements for Codex behavior omitted by exec JSONL.

Codex 0.154's exec JSON event processor does not emit every native thread item.
This module reads durable native rollouts after execution.  Nested supplements
cover only dispatches and child-owned tool calls; root tool calls stay under the
exec JSONL authority.  Skill-injection supplements separately qualify Codex's
native, internally rendered selected-skill instructions for one root turn.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any, Mapping

from native_eval_catalog import _is_json_value, _unique_object
from trigger_evidence import write_json_once


SCHEMA = "codex-native-rollout-supplement/v1"
COLLECTION_SCHEMA = "codex-native-rollout-collection/v1"
SKILL_INJECTION_SCHEMA = "codex-native-skill-injection/v1"
SKILL_INJECTION_COLLECTION_SCHEMA = "codex-native-skill-injection-collection/v1"
MAX_CHILDREN = 32
MAX_EVENTS_PER_ROLLOUT = 20_000
MAX_ROLLOUT_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_SCAN_ENTRIES = 100_000
MAX_SCAN_DEPTH = 3
MAX_DISPATCH_ITEM_MARKERS = 64
MAX_POST_TERMINAL_COMPLETIONS = 8

_THREAD_ID_PATTERN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_SKILL_NAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]*")
_PLUGIN_NAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]*")
_TOOL_TYPES = frozenset({"CommandExecution", "FileChange", "McpToolCall",
                         "CollabAgentToolCall", "WebSearch"})
_FAILURE_EVENTS = frozenset({"error", "task_failed", "turn_aborted", "turn_failed"})
_SKILL_CONTENT_KIND = "skills.selected_skill_instructions"
_PROMPT_CONTENT_KIND = "user.text"
_DISPATCH_ITEM_MARKER = re.compile(r"\[\[native-eval-item:([a-z0-9][a-z0-9._-]*)\]\]")
_FILE_CHANGE_KINDS = frozenset({"add", "update", "delete"})
_EXEC_ITEM_ID_PATTERN = re.compile(
    r"exec-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)
_EXEC_WRAPPER_PATTERN = re.compile(
    r"const (?P<binding>[A-Za-z_][A-Za-z0-9_]*) = await tools\.exec_command\("
    r"(?P<arguments>\{.*\})\);\s*text\((?:(?P=binding)\.output|"
    r"JSON\.stringify\((?P=binding)\))\);\s*",
    re.DOTALL,
)
_EXEC_ARGUMENTS_PATTERN = re.compile(
    r"\{\s*(?:\"cmd\"|cmd)\s*:\s*(?P<cmd>\"(?:\\.|[^\"\\])*\")\s*,"
    r"\s*(?:\"workdir\"|workdir)\s*:\s*(?P<workdir>\"(?:\\.|[^\"\\])*\")\s*,"
    r"\s*(?:\"yield_time_ms\"|yield_time_ms)\s*:\s*(?P<yield>[0-9]+)\s*,"
    r"\s*(?:\"max_output_tokens\"|max_output_tokens)\s*:\s*(?P<output>[0-9]+)\s*\}",
    re.DOTALL,
)
_WRITE_STDIN_WRAPPER_PATTERN = re.compile(
    r"const (?P<binding>[A-Za-z_][A-Za-z0-9_]*) = await tools\.write_stdin\("
    r"(?P<arguments>\{.*\})\);\s*text\(JSON\.stringify\((?P=binding)\)\);\s*",
    re.DOTALL,
)
_WRITE_STDIN_ARGUMENTS_PATTERN = re.compile(
    r"\{\s*(?:\"session_id\"|session_id)\s*:\s*(?P<session>[0-9]+)\s*,"
    r"\s*(?:\"chars\"|chars)\s*:\s*(?P<chars>\"(?:\\.|[^\"\\])*\")\s*,"
    r"\s*(?:\"yield_time_ms\"|yield_time_ms)\s*:\s*(?P<yield>[0-9]+)\s*,"
    r"\s*(?:\"max_output_tokens\"|max_output_tokens)\s*:\s*(?P<output>[0-9]+)\s*\}",
    re.DOTALL,
)
_ABORTED_POLL_PATTERN = re.compile(r"aborted by user after [0-9]+(?:\.[0-9]+)?s")


class NativeRolloutError(ValueError):
    """Base class for rollout evidence that cannot yet establish a result."""


class NativeRolloutPending(NativeRolloutError):
    """A referenced native rollout has not been durably published yet."""

    def __init__(self, thread_id: str):
        self.thread_id = thread_id
        super().__init__(f"native rollout is pending: {thread_id}")


class NativeRolloutIncomplete(NativeRolloutError):
    """A complete rollout lacks evidence required by the selected evaluation."""


class NativeRolloutInvalid(NativeRolloutError):
    """Native rollout bytes or ownership relationships cannot be trusted."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise NativeRolloutInvalid(message)


def _validated_thread_id(value: object, label: str) -> str:
    _require(isinstance(value, str) and _THREAD_ID_PATTERN.fullmatch(value) is not None,
             f"invalid {label}")
    return value


def _validated_plugin_name(value: object | None) -> str | None:
    _require(value is None or isinstance(value, str)
             and _PLUGIN_NAME_PATTERN.fullmatch(value) is not None,
             "plugin name is not canonical")
    return value


def _nonempty(value: object, label: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"invalid {label}")
    return value


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-JSON constant: {value}")


def _loads(value: str, label: str) -> Any:
    try:
        result = json.loads(value, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (TypeError, ValueError) as exc:
        raise NativeRolloutInvalid(f"malformed {label}: {exc}") from exc
    _require(_is_json_value(result), f"malformed {label}")
    return result


def _parse_jsonl(thread_id: str, raw: bytes | str) -> tuple[list[dict[str, Any]], bytes]:
    if isinstance(raw, str):
        encoded = raw.encode("utf-8")
    else:
        _require(isinstance(raw, bytes), f"rollout {thread_id} must be bytes or text")
        encoded = raw
    _require(0 < len(encoded) <= MAX_ROLLOUT_BYTES, f"rollout {thread_id} has invalid size")
    try:
        text = encoded.decode("utf-8")
    except UnicodeError as exc:
        raise NativeRolloutInvalid(f"rollout {thread_id} is not UTF-8") from exc
    _require(encoded.endswith(b"\n"), f"rollout {thread_id} may be truncated")
    lines = text.splitlines()
    _require(bool(lines) and len(lines) <= MAX_EVENTS_PER_ROLLOUT,
             f"rollout {thread_id} exceeds event bounds")
    _require(all(bool(item.strip()) for item in lines), f"rollout {thread_id} contains a blank record")
    records: list[dict[str, Any]] = []
    for number, item in enumerate(lines, 1):
        record = _loads(item, f"rollout {thread_id} record {number}")
        _require(isinstance(record, dict), f"rollout {thread_id} record {number} is not an object")
        _nonempty(record.get("type"), f"rollout {thread_id} record {number} type")
        payload = record.get("payload")
        _require(isinstance(payload, dict), f"rollout {thread_id} record {number} has no payload")
        records.append(record)
    return records, encoded


def _session_metadata(records: list[dict[str, Any]], thread_id: str,
                      ancestors: set[str]) -> dict[str, Any]:
    session_records = [record["payload"] for record in records if record["type"] == "session_meta"]
    matching = [payload for payload in session_records if payload.get("id") == thread_id]
    _require(len(matching) == 1, f"rollout {thread_id} must contain one matching session metadata record")
    for payload in session_records:
        identity = _validated_thread_id(payload.get("id"), "session metadata thread id")
        _require(identity == thread_id or identity in ancestors,
                 f"rollout {thread_id} contains unrelated session metadata")
    metadata = matching[0]
    for field in ("cwd", "cli_version", "model_provider"):
        _nonempty(metadata.get(field), f"rollout {thread_id} {field}")
    return metadata


def _payload(record: dict[str, Any], record_type: str) -> dict[str, Any] | None:
    payload = record["payload"]
    return payload if record["type"] == "event_msg" and payload.get("type") == record_type else None


def _exec_arguments(source: object) -> dict[str, Any] | None:
    if not isinstance(source, str) or (
        wrapper := _EXEC_WRAPPER_PATTERN.fullmatch(source)
    ) is None:
        return None
    encoded = wrapper.group("arguments")
    if (native := _EXEC_ARGUMENTS_PATTERN.fullmatch(encoded)) is None:
        arguments = _loads(encoded, "native exec invocation")
    else:
        arguments = {
            "cmd": _loads(native.group("cmd"), "native exec command"),
            "workdir": _loads(native.group("workdir"), "native exec workdir"),
            "yield_time_ms": int(native.group("yield")),
            "max_output_tokens": int(native.group("output")),
        }
    _require(isinstance(arguments, dict), "native exec invocation is not an object")
    _require(set(arguments) == {"cmd", "workdir", "yield_time_ms", "max_output_tokens"},
             "native exec invocation has unexpected arguments")
    return arguments


def _write_stdin_arguments(source: object) -> dict[str, Any] | None:
    if not isinstance(source, str) or (
        wrapper := _WRITE_STDIN_WRAPPER_PATTERN.fullmatch(source)
    ) is None:
        return None
    encoded = wrapper.group("arguments")
    native = _WRITE_STDIN_ARGUMENTS_PATTERN.fullmatch(encoded)
    _require(native is not None, "native write_stdin invocation is malformed")
    return {
        "session_id": int(native.group("session")),
        "chars": _loads(native.group("chars"), "native write_stdin chars"),
        "yield_time_ms": int(native.group("yield")),
        "max_output_tokens": int(native.group("output")),
    }


def _tool_response(
    records: list[dict[str, Any]], turn_id: str, terminal_index: int,
    call_id: str, invocation_index: int, label: str,
) -> tuple[int, dict[str, Any]]:
    outputs = [
        (index, record["payload"])
        for index, record in enumerate(records[:terminal_index])
        if record["type"] == "response_item"
        and record["payload"].get("type") == "custom_tool_call_output"
        and record["payload"].get("call_id") == call_id
    ]
    _require(len(outputs) == 1 and invocation_index < outputs[0][0] < terminal_index,
             f"{label} has no unique pre-terminal tool response")
    output_index, output = outputs[0]
    output_id = _nonempty(output.get("id"), f"{label} response item id")
    _require(sum(
        1 for record in records[:terminal_index]
        if record["type"] == "response_item"
        and record["payload"].get("type") == "custom_tool_call_output"
        and record["payload"].get("id") == output_id
    ) == 1, f"{label} response identity is duplicated")
    passthrough = output.get("internal_chat_message_metadata_passthrough")
    _require(isinstance(passthrough, dict) and passthrough.get("turn_id") == turn_id,
             f"{label} tool response crossed turns")
    return output_index, output


def _running_session_id(output: object) -> int | None:
    _require(isinstance(output, list) and all(
        isinstance(block, dict) and block.get("type") == "input_text"
        and isinstance(block.get("text"), str)
        for block in output
    ), "post-terminal command tool response is malformed")
    sessions = []
    for block in output:
        try:
            value = json.loads(block["text"])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and set(value) == {
            "chunk_id", "wall_time_seconds", "session_id",
            "original_token_count", "output",
        }:
            sessions.append(value)
    _require(len(sessions) <= 1,
             "post-terminal command tool response has ambiguous sessions")
    if not sessions:
        return None
    session = sessions[0]
    session_id = session.get("session_id")
    _require(type(session_id) is int and session_id > 0
             and isinstance(session.get("chunk_id"), str)
             and bool(session["chunk_id"])
             and type(session.get("original_token_count")) is int
             and session["original_token_count"] >= 0
             and isinstance(session.get("wall_time_seconds"), (int, float))
             and not isinstance(session["wall_time_seconds"], bool)
             and session["wall_time_seconds"] >= 0
             and isinstance(session.get("output"), str),
             "post-terminal command running-session response is invalid")
    return session_id


def _session_polls(
    records: list[dict[str, Any]], turn_id: str, terminal_index: int,
    response_index: int, session_id: int,
) -> list[dict[str, Any]]:
    polls = []
    for index, record in enumerate(records[response_index + 1:terminal_index],
                                   response_index + 1):
        payload = record["payload"]
        if record["type"] != "response_item" \
                or payload.get("type") != "custom_tool_call" \
                or payload.get("name") != "exec" \
                or payload.get("status") != "completed":
            continue
        passthrough = payload.get("internal_chat_message_metadata_passthrough")
        if not isinstance(passthrough, dict) or passthrough.get("turn_id") != turn_id:
            continue
        source = payload.get("input")
        arguments = _write_stdin_arguments(source)
        if arguments is None:
            _require(not isinstance(source, str) or "tools.write_stdin(" not in source,
                     "native write_stdin invocation is malformed")
            continue
        _require(arguments["session_id"] == session_id,
                 "native write_stdin poll changed session identity")
        _require(arguments["chars"] == ""
                 and arguments["yield_time_ms"] > 0
                 and arguments["max_output_tokens"] > 0,
                 "native write_stdin invocation arguments are invalid")
        call_id = _nonempty(payload.get("call_id"), "native write_stdin call id")
        invocation_id = _nonempty(payload.get("id"), "native write_stdin item id")
        _require(sum(
            1 for candidate in records[:terminal_index]
            if candidate["type"] == "response_item"
            and candidate["payload"].get("type") == "custom_tool_call"
            and (candidate["payload"].get("call_id") == call_id
                 or candidate["payload"].get("id") == invocation_id)
        ) == 1, "native write_stdin invocation identity is duplicated")
        output_index, output = _tool_response(
            records, turn_id, terminal_index, call_id, index,
            "native write_stdin invocation",
        )
        polls.append({
            "call_id": call_id,
            "invocation_id": invocation_id,
            "response_id": output["id"],
            "invocation_record_index": index,
            "tool_response_record_index": output_index,
            "output": output.get("output"),
        })
    _require(len(polls) <= MAX_POST_TERMINAL_COMPLETIONS,
             "post-terminal command has too many native session polls")
    if polls:
        for poll in polls[:-1]:
            _require(_running_session_id(poll["output"]) == session_id,
                     "native write_stdin poll changed session identity")
        _require(isinstance(polls[-1]["output"], str)
                 and _ABORTED_POLL_PATTERN.fullmatch(polls[-1]["output"]) is not None,
                 "native write_stdin terminal poll was not interrupted")
    return polls


def _exec_invocation(
    records: list[dict[str, Any]], turn_id: str,
    terminal_index: int, command: list[str], cwd: str, process_id: str,
) -> dict[str, Any]:
    matches: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
    for index, record in enumerate(records[:terminal_index]):
        payload = record["payload"]
        if record["type"] != "response_item" or payload.get("type") != "custom_tool_call":
            continue
        if payload.get("name") != "exec" or payload.get("status") != "completed":
            continue
        passthrough = payload.get("internal_chat_message_metadata_passthrough")
        if not isinstance(passthrough, dict) or passthrough.get("turn_id") != turn_id:
            continue
        arguments = _exec_arguments(payload.get("input"))
        if arguments is None:
            continue
        request_command = _nonempty(arguments.get("cmd"), "native exec invocation command")
        request_cwd = _canonical_workspace(arguments.get("workdir"))
        _require(type(arguments.get("yield_time_ms")) is int
                 and arguments["yield_time_ms"] > 0,
                 "native exec invocation yield time is invalid")
        _require(type(arguments.get("max_output_tokens")) is int
                 and arguments["max_output_tokens"] > 0,
                 "native exec invocation output bound is invalid")
        if command == ["/bin/zsh", "-c", request_command] and cwd == f"file://{request_cwd}":
            matches.append((index, payload, arguments))
    _require(len(matches) == 1, "post-terminal command has no unique native exec invocation")
    invocation_index, invocation, arguments = matches[0]
    call_id = _nonempty(invocation.get("call_id"), "native exec invocation call id")
    invocation_id = _nonempty(invocation.get("id"), "native exec invocation item id")
    _require(sum(
        1 for record in records[:terminal_index]
        if record["type"] == "response_item"
        and record["payload"].get("type") == "custom_tool_call"
        and (record["payload"].get("call_id") == call_id
             or record["payload"].get("id") == invocation_id)
    ) == 1, "post-terminal command invocation identity is duplicated")
    output_index, output = _tool_response(
        records, turn_id, terminal_index, call_id, invocation_index,
        "post-terminal command",
    )
    output_id = output["id"]
    session_id = _running_session_id(output.get("output"))
    polls: list[dict[str, Any]] = []
    if session_id is not None:
        _require(process_id == str(session_id),
                 "post-terminal command process does not match native session")
        polls = _session_polls(
            records, turn_id, terminal_index, output_index, session_id,
        )
    return {
        "call_id": call_id,
        "invocation_id": invocation_id,
        "response_id": output_id,
        "invocation_record_index": invocation_index,
        "tool_response_record_index": output_index,
        "command": arguments["cmd"],
        "cwd": arguments["workdir"],
        "session_id": session_id,
        "polls": polls,
    }


def _post_terminal_completions(
    records: list[dict[str, Any]], thread_id: str, turn_id: str,
    terminal_index: int,
) -> list[dict[str, Any]]:
    suffix = records[terminal_index + 1:]
    if not suffix:
        return []
    _require(len(suffix) <= MAX_POST_TERMINAL_COMPLETIONS,
             f"rollout {thread_id} contains too many post-terminal records")
    terminal = records[terminal_index]
    terminal_payload = _payload(terminal, "task_complete")
    if terminal_payload is None and terminal["type"] == "event_msg" \
            and terminal["payload"].get("type") == "turn_aborted":
        terminal_payload = terminal["payload"]
    _require(terminal_payload is not None, "post-terminal commands have no task terminal")
    terminal_completed = terminal_payload.get("completed_at")
    _require(type(terminal_completed) is int,
             "post-terminal command terminal timing is unavailable")
    terminal_ms = terminal_completed * 1000
    terminal_ordinal = terminal.get("ordinal")
    _require(type(terminal_ordinal) is int,
             "post-terminal command terminal ordinal is unavailable")
    item_identities = [
        candidate["id"]
        for candidate_record in records
        if (candidate_payload := _payload(candidate_record, "item_completed")) is not None
        and isinstance((candidate := candidate_payload.get("item")), dict)
        and isinstance(candidate.get("id"), str)
    ]
    completions: list[dict[str, Any]] = []
    unique: dict[str, set[str]] = {
        "item": set(), "call": set(), "invocation": set(), "response": set(),
    }
    for offset, record in enumerate(suffix, 1):
        index = terminal_index + offset
        payload = _payload(record, "item_completed")
        _require(payload is not None, f"rollout {thread_id} has invalid post-terminal work")
        _require(payload.get("thread_id") == thread_id and payload.get("turn_id") == turn_id,
                 f"rollout {thread_id} post-terminal command crossed thread or turn")
        item = payload.get("item")
        _require(isinstance(item, dict) and item.get("type") == "CommandExecution",
                 f"rollout {thread_id} post-terminal item is not a command completion")
        item_id = _nonempty(item.get("id"), "post-terminal command item id")
        _require(_EXEC_ITEM_ID_PATTERN.fullmatch(item_id) is not None,
                 "post-terminal command item id is not canonical")
        _require(item_identities.count(item_id) == 1,
                 f"rollout {thread_id} repeats post-terminal command item {item_id}")
        command = item.get("command")
        _require(isinstance(command, list) and len(command) == 3
                 and command[:2] == ["/bin/zsh", "-c"]
                 and isinstance(command[2], str) and bool(command[2]),
                 "post-terminal native command is malformed")
        cwd = _nonempty(item.get("cwd"), "post-terminal native command cwd")
        _require(item.get("source") == "unified_exec_startup",
                 "post-terminal native command source is invalid")
        _require(item.get("status") == "completed",
                 "post-terminal native command did not complete")
        _require(type(item.get("exit_code")) is int and item["exit_code"] == 0,
                 "post-terminal native command did not exit successfully")
        process_id = _nonempty(item.get("process_id"),
                               "post-terminal native command process id")
        _require(process_id.isdigit() and int(process_id) > 0,
                 "post-terminal native command process id is invalid")
        started, completed = payload.get("started_at_ms"), payload.get("completed_at_ms")
        _require(type(started) is int and type(completed) is int,
                 "post-terminal command lifecycle timing is unavailable")
        _require(0 <= started < terminal_ms <= completed,
                 "post-terminal command lifecycle timing is invalid")
        completion_ordinal = record.get("ordinal")
        _require(type(completion_ordinal) is int
                 and completion_ordinal == terminal_ordinal + offset,
                 "post-terminal command ordinal correlation is invalid")
        invocation = _exec_invocation(
            records, turn_id, terminal_index, command, cwd, process_id,
        )
        identities = {
            "item": item_id,
            "call": invocation["call_id"],
            "invocation": invocation["invocation_id"],
            "response": invocation["response_id"],
        }
        for kind, identity in identities.items():
            _require(identity not in unique[kind],
                     f"post-terminal command {kind} identity is not injective")
            unique[kind].add(identity)
        completions.append({
            "schema": "codex-post-terminal-command-completion/v2",
            "model_observed": False,
            "thread_id": thread_id,
            "turn_id": turn_id,
            "item_id": item_id,
            "call_id": invocation["call_id"],
            "invocation_id": invocation["invocation_id"],
            "response_id": invocation["response_id"],
            "process_id": process_id,
            "command": invocation["command"],
            "cwd": invocation["cwd"],
            "source": "unified_exec_startup",
            "status": "completed",
            "exit_code": 0,
            "started_at_ms": started,
            "terminal_completed_at_ms": terminal_ms,
            "completed_at_ms": completed,
            "terminal_record_index": terminal_index,
            "completion_record_index": index,
            "terminal_ordinal": terminal_ordinal,
            "completion_ordinal": completion_ordinal,
            "invocation_record_index": invocation["invocation_record_index"],
            "tool_response_record_index": invocation["tool_response_record_index"],
            "native_session_id": invocation["session_id"],
            "native_session_polls": invocation["polls"],
        })
    return completions


def _reject_unfinished_exec(
    records: list[dict[str, Any]], thread_id: str, turn_ids: set[str],
) -> None:
    for record in records:
        payload = record["payload"]
        if record["type"] == "response_item" \
                and payload.get("type") == "custom_tool_call" \
                and payload.get("name") == "exec":
            passthrough = payload.get("internal_chat_message_metadata_passthrough")
            if isinstance(passthrough, dict) and passthrough.get("turn_id") in turn_ids:
                _require(payload.get("status") == "completed",
                         f"rollout {thread_id} contains an unfinished exec invocation")
        item = payload.get("item") if payload.get("type") == "item_completed" else None
        if payload.get("thread_id") == thread_id \
                and isinstance(item, dict) \
                and item.get("type") == "CommandExecution":
            _require(item.get("status") != "in_progress",
                     f"rollout {thread_id} contains an unfinished command item")


def _scoped_turn_events(
    records: list[dict[str, Any]], thread_id: str,
) -> dict[str, list[int]]:
    scoped: dict[str, list[int]] = {}
    for index, record in enumerate(records):
        payload = record["payload"]
        if payload.get("thread_id") == thread_id:
            if payload.get("turn_id") is None:
                _require(record["type"] == "event_msg"
                         and payload.get("type") == "thread_settings_applied",
                         f"rollout {thread_id} has an unbound thread event")
                continue
            turn_id = _nonempty(payload.get("turn_id"), f"rollout {thread_id} scoped turn id")
            scoped.setdefault(turn_id, []).append(index)
    _require(bool(scoped), f"rollout {thread_id} contains no thread-owned events")
    return scoped


def _validated_interruption(
    records: list[dict[str, Any]], thread_id: str, turn_ids: set[str], allowed: bool,
) -> tuple[int, list[tuple[int, dict[str, Any]]]]:
    interruptions = [
        (index, record["payload"])
        for index, record in enumerate(records)
        if record["type"] == "event_msg"
        and record["payload"].get("type") == "turn_aborted"
        and record["payload"].get("turn_id") in turn_ids
    ]
    if allowed:
        _require(len(interruptions) == 1,
                 f"rollout {thread_id} does not have one interrupted terminal")
        interrupted_index, interrupted_payload = interruptions[0]
        _require(interrupted_payload.get("reason") == "interrupted",
                 f"rollout {thread_id} has an invalid interruption reason")
        started_at = interrupted_payload.get("started_at")
        completed_at = interrupted_payload.get("completed_at")
        duration_ms = interrupted_payload.get("duration_ms")
        _require(type(started_at) is int and type(completed_at) is int
                 and type(duration_ms) is int and duration_ms >= 0
                 and 0 <= started_at <= completed_at,
                 f"rollout {thread_id} has invalid interruption timing")
        return interrupted_index, interruptions
    return -1, interruptions


def _validate_failure_events(
    records: list[dict[str, Any]], thread_id: str, interrupted_index: int,
) -> None:
    for index, record in enumerate(records):
        if record["type"] != "event_msg" \
                or record["payload"].get("type") not in _FAILURE_EVENTS:
            continue
        _require(index == interrupted_index,
                 f"rollout {thread_id} contains a native error event")


def _terminal_index(
    records: list[dict[str, Any]], thread_id: str, turn_id: str,
    interruptions: list[tuple[int, dict[str, Any]]],
) -> tuple[int, int, list[int]]:
    starts = [index for index, record in enumerate(records)
              if (value := _payload(record, "task_started")) is not None
              and value.get("turn_id") == turn_id]
    completes = [index for index, record in enumerate(records)
                 if (value := _payload(record, "task_complete")) is not None
                 and value.get("turn_id") == turn_id]
    aborts = [index for index, payload in interruptions
              if payload.get("turn_id") == turn_id]
    _require(len(starts) == 1
             and ((len(completes) == 1 and not aborts)
                  or (not completes and len(aborts) == 1)),
             f"rollout {thread_id} does not have one terminal pair for turn {turn_id}")
    return starts[0], completes[0] if completes else aborts[0], aborts


def _validate_turn_failure_evidence(
    records: list[dict[str, Any]], thread_id: str, turn_id: str,
    interrupted_index: int, aborts: list[int],
) -> None:
    for record in records:
        payload = record["payload"]
        if payload.get("turn_id") == turn_id or payload.get("thread_id") == thread_id:
            _require(payload.get("type") not in _FAILURE_EVENTS
                     or record is records[interrupted_index],
                     f"rollout {thread_id} contains a failed turn")
    if not aborts:
        return
    final_messages = [
        record for record in records
        if record["payload"].get("thread_id") == thread_id
        and record["payload"].get("turn_id") == turn_id
        and isinstance(record["payload"].get("item"), dict)
        and record["payload"]["item"].get("type") == "AgentMessage"
        and record["payload"]["item"].get("phase") != "commentary"
    ]
    _require(not final_messages,
             f"rollout {thread_id} interruption conflicts with a final message")


def _validate_terminal_state(
    records: list[dict[str, Any]], thread_id: str, *,
    allow_post_terminal_completion: bool = False,
    allow_interrupted: bool = False,
) -> tuple[list[str], list[dict[str, Any]]]:
    scoped = _scoped_turn_events(records, thread_id)
    interrupted_index, interruptions = _validated_interruption(
        records, thread_id, set(scoped), allow_interrupted,
    )
    _validate_failure_events(records, thread_id, interrupted_index)
    _reject_unfinished_exec(records, thread_id, set(scoped))
    terminals: dict[str, int] = {}
    for turn_id, indexes in scoped.items():
        start, terminal, aborts = _terminal_index(
            records, thread_id, turn_id, interruptions,
        )
        terminals[turn_id] = terminal
        _require(start < min(indexes),
                 f"rollout {thread_id} has invalid terminal ordering")
        _validate_turn_failure_evidence(
            records, thread_id, turn_id, interrupted_index, aborts,
        )
    last_turn, terminal_index = max(terminals.items(), key=lambda item: item[1])
    completions: list[dict[str, Any]] = []
    if allow_post_terminal_completion:
        completions = _post_terminal_completions(records, thread_id, last_turn, terminal_index)
    allowed_indexes = {value["completion_record_index"] for value in completions}
    for turn_id, indexes in scoped.items():
        before_terminal = [index for index in indexes if index not in allowed_indexes]
        _require(bool(before_terminal) and max(before_terminal) < terminals[turn_id],
                 f"rollout {thread_id} has invalid terminal ordering")
    return list(scoped), completions


def _validate_terminal(records: list[dict[str, Any]], thread_id: str) -> list[str]:
    return _validate_terminal_state(records, thread_id)[0]


def _terminal_failure(records: list[dict[str, Any]], thread_id: str,
                      turn_ids: set[str]) -> dict[str, Any] | None:
    """Return a hash-bound native task-complete error for the latest owned turn."""
    terminals = [(index, record) for index, record in enumerate(records)
                 if (payload := _payload(record, "task_complete")) is not None
                 and payload.get("turn_id") in turn_ids]
    _require(bool(terminals), f"rollout {thread_id} has no owned terminal result")
    index, terminal = max(terminals, key=lambda item: item[0])
    payload = terminal["payload"]
    error = payload.get("error")
    if error is None:
        return None
    _require(isinstance(error, dict), f"rollout {thread_id} terminal error is malformed")
    message = _nonempty(error.get("message"), f"rollout {thread_id} terminal error message")
    code = error.get("codex_error_info")
    _require(isinstance(code, str) and bool(code.strip()),
             f"rollout {thread_id} terminal error code is malformed")
    last_message = payload.get("last_agent_message")
    _require(last_message is None,
             f"rollout {thread_id} terminal error conflicts with a final message")
    encoded = message.encode("utf-8", errors="strict")
    timestamp = _nonempty(terminal.get("timestamp"),
                          f"rollout {thread_id} terminal timestamp")
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise NativeRolloutInvalid(
            f"rollout {thread_id} terminal timestamp is malformed"
        ) from exc
    _require(parsed.tzinfo is not None,
             f"rollout {thread_id} terminal timestamp lacks a timezone")
    return {
        "schema": "codex-native-terminal-failure/v1",
        "turn_id": payload["turn_id"],
        "native_event_index": index,
        "timestamp": timestamp,
        "codex_error_info": code,
        "message_sha256": hashlib.sha256(encoded).hexdigest(),
        "message_bytes": len(encoded),
    }


def _interruption_failure(records: list[dict[str, Any]], thread_id: str,
                          turn_ids: set[str]) -> dict[str, Any]:
    """Return a hash-bound failure for one natively interrupted owned turn."""
    terminals = [(index, record) for index, record in enumerate(records)
                 if record["type"] == "event_msg"
                 and record["payload"].get("type") == "turn_aborted"
                 and record["payload"].get("turn_id") in turn_ids]
    _require(len(terminals) == 1,
             f"rollout {thread_id} does not have one interrupted terminal")
    index, terminal = terminals[0]
    payload = terminal["payload"]
    _require(payload.get("reason") == "interrupted",
             f"rollout {thread_id} has an invalid interruption reason")
    encoded = b"interrupted"
    timestamp = _nonempty(terminal.get("timestamp"),
                          f"rollout {thread_id} interruption timestamp")
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise NativeRolloutInvalid(
            f"rollout {thread_id} interruption timestamp is malformed"
        ) from exc
    _require(parsed.tzinfo is not None,
             f"rollout {thread_id} interruption timestamp lacks a timezone")
    return {
        "schema": "codex-native-terminal-failure/v1",
        "turn_id": payload["turn_id"],
        "native_event_index": index,
        "timestamp": timestamp,
        "codex_error_info": "interrupted",
        "message_sha256": hashlib.sha256(encoded).hexdigest(),
        "message_bytes": len(encoded),
    }


def _function_calls(records: list[dict[str, Any]], call_id: str) -> list[dict[str, Any]]:
    return [record["payload"] for record in records
            if record["type"] == "response_item"
            and record["payload"].get("type") == "function_call"
            and record["payload"].get("call_id") == call_id]


def _validate_interruption_binding(
    records: list[dict[str, Any]], *, child_id: str, agent_path: str,
    task_name: str | None, parent_turn_id: str, activity_id: str,
    activity_index: int,
) -> None:
    calls = [
        (index, record["payload"])
        for index, record in enumerate(records)
        if record["type"] == "response_item"
        and record["payload"].get("type") == "function_call"
        and record["payload"].get("call_id") == activity_id
    ]
    _require(len(calls) == 1,
             f"subagent {child_id} does not join one interrupt_agent call")
    call_index, call = calls[0]
    _require(call_index < activity_index
             and call.get("namespace") == "collaboration"
             and call.get("name") == "interrupt_agent",
             f"subagent {child_id} has an invalid interrupt_agent call")
    passthrough = call.get("internal_chat_message_metadata_passthrough")
    _require(isinstance(passthrough, dict)
             and passthrough.get("turn_id") == parent_turn_id,
             f"subagent {child_id} interrupt_agent call crossed turns")
    arguments = call.get("arguments")
    _require(isinstance(arguments, str), "interrupt_agent arguments are not serialized JSON")
    parsed = _loads(arguments, "interrupt_agent arguments")
    targets = {child_id, agent_path}
    if task_name is not None:
        targets.add(task_name)
    _require(isinstance(parsed, dict) and set(parsed) == {"target"}
             and parsed.get("target") in targets,
             f"subagent {child_id} interrupt_agent target is inconsistent")
    outputs = [
        (index, record["payload"])
        for index, record in enumerate(records)
        if record["type"] == "response_item"
        and record["payload"].get("type") == "function_call_output"
        and record["payload"].get("call_id") == activity_id
    ]
    _require(len(outputs) == 1 and activity_index < outputs[0][0],
             f"subagent {child_id} interrupt_agent result is missing or out of order")
    output = outputs[0][1]
    passthrough = output.get("internal_chat_message_metadata_passthrough")
    _require(isinstance(passthrough, dict)
             and passthrough.get("turn_id") == parent_turn_id,
             f"subagent {child_id} interrupt_agent result crossed turns")
    result = output.get("output")
    _require(isinstance(result, str)
             and _loads(result, "interrupt_agent result") == {"previous_status": "running"},
             f"subagent {child_id} interrupt_agent result is invalid")


def _opaque(value: object) -> dict[str, Any]:
    _require(_is_json_value(value), "spawn task input is not strict JSON")
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return {"kind": "opaque", "sha256": hashlib.sha256(encoded).hexdigest(), "bytes": len(encoded)}


def _timestamp_ns(value: object, label: str) -> int:
    _require(isinstance(value, str), f"{label} timestamp is missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise NativeRolloutInvalid(f"{label} timestamp is malformed") from exc
    _require(parsed.tzinfo is not None, f"{label} timestamp lacks a timezone")
    return int(parsed.timestamp() * 1_000_000_000)


def _dispatch_item_attribution(value: object) -> dict[str, Any]:
    task_input = _opaque(value)
    markers = _DISPATCH_ITEM_MARKER.findall(value) if isinstance(value, str) else []
    return {
        "task_input": task_input,
        "observed_item_ids": markers[:MAX_DISPATCH_ITEM_MARKERS],
        "observed_marker_count": len(markers),
        "markers_truncated": len(markers) > MAX_DISPATCH_ITEM_MARKERS,
    }


def _canonical_workspace(value: object) -> str:
    text = _nonempty(value, "expected cwd")
    parsed = PurePosixPath(text)
    _require(parsed.is_absolute() and text != "/" and parsed.as_posix() == text
             and all(part not in {"", ".", ".."} for part in parsed.parts[1:]),
             "expected cwd must be a canonical absolute POSIX path")
    return text


def _skill_witnesses(value: Mapping[str, object]) -> dict[str, dict[str, Any]]:
    _require(isinstance(value, Mapping) and bool(value),
             "skill injection witnesses must be a nonempty mapping")
    result: dict[str, dict[str, Any]] = {}
    paths: set[str] = set()
    for name, raw in value.items():
        _require(isinstance(name, str) and _SKILL_NAME_PATTERN.fullmatch(name) is not None,
                 "skill injection witness name is not canonical")
        _require(isinstance(raw, Mapping)
                 and set(raw) == {"path", "text", "bytes", "sha256"},
                 f"skill injection witness {name} has a malformed schema")
        path, body = raw["path"], raw["text"]
        byte_count, digest = raw["bytes"], raw["sha256"]
        _require(path == f".agents/skills/{name}/SKILL.md" and path not in paths,
                 f"skill injection witness {name} path is not canonical or unique")
        _require(isinstance(body, str) and bool(body),
                 f"skill injection witness {name} body is empty or malformed")
        try:
            encoded = body.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise NativeRolloutInvalid(
                f"skill injection witness {name} body is not strict UTF-8"
            ) from exc
        _require(type(byte_count) is int and byte_count == len(encoded),
                 f"skill injection witness {name} byte count does not match")
        expected_digest = hashlib.sha256(encoded).hexdigest()
        _require(isinstance(digest, str) and digest == expected_digest,
                 f"skill injection witness {name} sha256 does not match")
        paths.add(path)
        result[name] = {"path": path, "text": body, "bytes": byte_count, "sha256": digest}
    return result


def _content_kinds(payload: Mapping[str, Any]) -> object:
    metadata = payload.get("internal_chat_message_metadata_passthrough")
    return metadata.get("content_item_kinds") if isinstance(metadata, Mapping) else None


def _contains_text(payload: Mapping[str, Any], text: str) -> bool:
    content = payload.get("content")
    return isinstance(content, list) and any(
        isinstance(item, Mapping) and item.get("text") == text for item in content
    )


def _looks_like_skill_injection(payload: Mapping[str, Any]) -> bool:
    kinds = _content_kinds(payload)
    if isinstance(kinds, list) and _SKILL_CONTENT_KIND in kinds:
        return True
    content = payload.get("content")
    return isinstance(content, list) and any(
        isinstance(item, Mapping) and isinstance(item.get("text"), str)
        and item["text"].startswith("<skill>")
        for item in content
    )


def _bound_user_message(payload: Mapping[str, Any], kind: str, label: str) -> tuple[str, str]:
    _require(payload.get("type") == "message" and payload.get("role") == "user",
             f"{label} is not a native user message")
    content = payload.get("content")
    _require(isinstance(content, list) and len(content) == 1
             and isinstance(content[0], Mapping)
             and content[0].get("type") == "input_text"
             and isinstance(content[0].get("text"), str),
             f"{label} content is malformed")
    metadata = payload.get("internal_chat_message_metadata_passthrough")
    _require(isinstance(metadata, Mapping), f"{label} metadata is missing")
    _require(metadata.get("content_item_kinds") == [kind],
             f"{label} classification is malformed")
    turn_id = _validated_thread_id(metadata.get("turn_id"), f"{label} turn id")
    message_id = payload.get("id")
    _require(message_id is None or isinstance(message_id, str) and bool(message_id.strip()),
             f"{label} optional message id is malformed")
    return content[0]["text"], turn_id


def _rendered_skill(name: str, witness: Mapping[str, Any], cwd: str,
                    plugin_name: str | None) -> str:
    native_path = f"{cwd}/{witness['path']}"
    native_name = f"{plugin_name}:{name}" if plugin_name is not None else name
    return (f"<skill>\n<name>{native_name}</name>\n<path>{native_path}</path>\n"
            f"{witness['text']}\n</skill>")


def _prompt_binding(records: list[dict[str, Any]], root_thread_id: str,
                    prompt: str) -> tuple[int, str, int]:
    terminal_turns = set(_validate_terminal(records, root_thread_id))
    candidates = [(index, record["payload"]) for index, record in enumerate(records)
                  if record["type"] == "response_item"
                  and _contains_text(record["payload"], prompt)]
    _require(len(candidates) == 1,
             "root rollout must contain one exact expected prompt message")
    prompt_index, payload = candidates[0]
    prompt_text, turn_id = _bound_user_message(payload, _PROMPT_CONTENT_KIND,
                                                "expected prompt")
    _require(prompt_text == prompt and turn_id in terminal_turns,
             "expected prompt is not bound to a completed root turn")
    starts = [index for index, record in enumerate(records)
              if (value := _payload(record, "task_started")) is not None
              and value.get("turn_id") == turn_id]
    completes = [index for index, record in enumerate(records)
                 if (value := _payload(record, "task_complete")) is not None
                 and value.get("turn_id") == turn_id]
    _require(len(starts) == 1 and len(completes) == 1
             and starts[0] < prompt_index < completes[0],
             "expected prompt has invalid terminal ordering")
    return prompt_index, turn_id, completes[0]


def _injection_evidence(index: int, payload: Mapping[str, Any], text: str,
                        name: str, witness: Mapping[str, Any], cwd: str) -> dict[str, Any]:
    rendered_bytes = text.encode("utf-8", errors="strict")
    result = {
        "record_index": index,
        "skill": name,
        "path": witness["path"],
        "native_path": f"{cwd}/{witness['path']}",
        "content_kind": _SKILL_CONTENT_KIND,
        "source_bytes": witness["bytes"],
        "source_sha256": witness["sha256"],
        "rendered_bytes": len(rendered_bytes),
        "rendered_sha256": hashlib.sha256(rendered_bytes).hexdigest(),
    }
    if payload.get("id") is not None:
        result["message_id"] = payload["id"]
    return result


def _qualified_injections(records: list[dict[str, Any]], prompt_index: int,
                          turn_id: str, complete_index: int, cwd: str,
                          witnesses: Mapping[str, Mapping[str, Any]],
                          plugin_name: str | None) -> list[dict[str, Any]]:
    rendered = {name: _rendered_skill(name, witness, cwd, plugin_name)
                for name, witness in witnesses.items()}
    result = []
    seen_skills: set[str] = set()
    seen_message_ids: set[str] = set()
    for index, record in enumerate(records):
        if index == prompt_index or record["type"] != "response_item":
            continue
        payload = record["payload"]
        if not _looks_like_skill_injection(payload):
            continue
        text, injection_turn = _bound_user_message(
            payload, _SKILL_CONTENT_KIND, "selected-skill injection"
        )
        if injection_turn != turn_id:
            continue
        _require(prompt_index < index < complete_index,
                 "selected-skill injection has invalid turn ordering")
        matches = [name for name, expected in rendered.items() if text == expected]
        _require(len(matches) == 1,
                 "selected-skill injection does not exactly match one staged skill")
        name = matches[0]
        _require(name not in seen_skills, "duplicate selected-skill activation")
        message_id = payload.get("id")
        _require(message_id is None or message_id not in seen_message_ids,
                 "duplicate selected-skill message identity")
        result.append(_injection_evidence(
            index, payload, text, name, witnesses[name], cwd
        ))
        seen_skills.add(name)
        if message_id is not None:
            seen_message_ids.add(message_id)
    return result


def parse_native_skill_injections(
    root_thread_id: str,
    raw: bytes | str,
    *,
    expected_cwd: str,
    expected_prompt: str,
    skill_witnesses: Mapping[str, object],
    plugin_name: str | None = None,
) -> dict[str, Any]:
    """Qualify exact native selected-skill instructions for one root prompt turn.

    A missing injection is a valid no-activation observation.  Distinct exact
    staged siblings are valid evidence and are returned in rollout order for
    the shared selection grader to judge.  Malformed, duplicated, or non-staged
    native injection evidence is invalid rather than interpreted from prose or reads.
    """
    root_thread_id = _validated_thread_id(root_thread_id, "root thread id")
    cwd = _canonical_workspace(expected_cwd)
    prompt = _nonempty(expected_prompt, "expected prompt")
    plugin_name = _validated_plugin_name(plugin_name)
    try:
        prompt_bytes = prompt.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise NativeRolloutInvalid("expected prompt is not strict UTF-8") from exc
    witnesses = _skill_witnesses(skill_witnesses)
    records, encoded = _parse_jsonl(root_thread_id, raw)
    metadata = _session_metadata(records, root_thread_id, set())
    _require(metadata.get("source") == "exec", "root rollout is not a native exec session")
    _require(metadata.get("session_id") == root_thread_id
             and metadata.get("thread_source") == "user",
             "root rollout session identity is inconsistent")
    _require(metadata.get("cwd") == cwd, "root rollout crossed the expected cwd")
    prompt_index, turn_id, complete_index = _prompt_binding(
        records, root_thread_id, prompt
    )
    injections = _qualified_injections(
        records, prompt_index, turn_id, complete_index, cwd, witnesses, plugin_name
    )

    activations = [item["skill"] for item in injections]
    return {
        "schema": SKILL_INJECTION_SCHEMA,
        "root_thread_id": root_thread_id,
        "cwd": cwd,
        "turn_id": turn_id,
        "scope": "root-selected-skill-instructions",
        "authority": "native-rollout",
        "status": "qualified" if activations else "not_observed",
        "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
        "raw_sha256": hashlib.sha256(encoded).hexdigest(),
        "activations": activations,
        "injections": injections,
        "evidence_bound": (
            "Exact complete native selected-skill rendering, root source, cwd, prompt, "
            "turn, and terminal ordering; no prose or visible-read inference."
        ),
    }


def _subagent_activities(
    records: list[dict[str, Any]], parent_id: str,
) -> tuple[
    dict[str, tuple[dict[str, Any], int, str]],
    dict[str, list[tuple[str, dict[str, Any], int, str]]],
]:
    started: dict[str, tuple[dict[str, Any], int, str]] = {}
    terminals: dict[str, list[tuple[str, dict[str, Any], int, str]]] = {}
    for index, record in enumerate(records):
        payload = _payload(record, "item_completed")
        if payload is None or payload.get("thread_id") != parent_id:
            continue
        item = payload.get("item")
        _require(isinstance(item, dict), f"rollout {parent_id} has a malformed completed item")
        if item.get("type") != "SubAgentActivity":
            continue
        child_id = _validated_thread_id(item.get("agent_thread_id"), "subagent thread id")
        path = _nonempty(item.get("agent_path"), "subagent path")
        turn_id = _validated_thread_id(payload.get("turn_id"), "subagent parent turn id")
        kind = item.get("kind")
        if kind == "interacted":
            continue
        _require(kind in {"started", "completed", "interrupted"},
                 "unknown subagent activity kind")
        if kind == "started":
            _require(child_id not in started, f"duplicate started activity for {child_id}")
            started[child_id] = (item, index, turn_id)
        else:
            terminals.setdefault(child_id, []).append((kind, item, index, turn_id))
    _require(set(terminals).issubset(started),
             f"rollout {parent_id} has unmatched subagent completion activity")
    return started, terminals


def _followup_chain(
    records: list[dict[str, Any]], *, parent_id: str, child_id: str, agent_path: str,
    task_name: str | None, parent_turn_id: str, start_index: int,
    terminals: list[tuple[str, dict[str, Any], int, str]],
) -> list[dict[str, Any]]:
    terminal_ids = [
        _nonempty(item.get("id"), "subagent completion event id")
        for _, item, _, _ in terminals
    ]
    _require(len(set(terminal_ids)) == len(terminal_ids),
             f"subagent {child_id} repeats a completion event identity")
    for _, item, index, turn_id in terminals:
        _require(start_index < index and item.get("agent_path") == agent_path
                 and turn_id == parent_turn_id,
                 f"subagent {child_id} activity does not bind to one path and order")
    if len(terminals) <= 1:
        return []
    _require(all(kind == "completed" for kind, _, _, _ in terminals),
             f"subagent {child_id} has conflicting subagent terminal activity")
    targets = {child_id, agent_path}
    if task_name is not None:
        targets.add(task_name)
    calls = []
    for index, record in enumerate(records):
        payload = record["payload"]
        if record["type"] != "response_item" \
                or payload.get("type") != "function_call" \
                or payload.get("namespace") != "collaboration" \
                or payload.get("name") != "followup_task":
            continue
        parsed = _loads(payload.get("arguments"), "followup_task arguments")
        _require(isinstance(parsed, dict) and set(parsed) == {"target", "message"},
                 "followup_task arguments are incomplete")
        if parsed.get("target") in targets:
            calls.append((index, payload, parsed))
    _require(len(calls) == len(terminals) - 1,
             f"subagent {child_id} repeated completion lacks a unique followup_task")
    result = []
    for position, (call_index, call, parsed) in enumerate(calls):
        previous_index = terminals[position][2]
        next_index = terminals[position + 1][2]
        call_id = _nonempty(call.get("call_id"), "followup_task call id")
        metadata = call.get("internal_chat_message_metadata_passthrough")
        _require(previous_index < call_index < next_index
                 and isinstance(metadata, dict)
                 and metadata.get("turn_id") == parent_turn_id,
                 f"subagent {child_id} followup_task call is out of order")
        interactions = []
        for interaction_index, candidate in enumerate(records):
            candidate_payload = _payload(candidate, "item_completed")
            item = candidate_payload.get("item") if candidate_payload is not None else None
            if candidate_payload is not None \
                    and candidate_payload.get("thread_id") == parent_id \
                    and isinstance(item, dict) \
                    and item.get("type") == "SubAgentActivity" \
                    and item.get("kind") == "interacted" \
                    and item.get("id") == call_id:
                interactions.append((interaction_index, candidate_payload, item))
        _require(len(interactions) == 1,
                 f"subagent {child_id} followup_task has no unique interacted activity")
        interaction_index, interaction_payload, interaction = interactions[0]
        outputs = [
            (index, record["payload"])
            for index, record in enumerate(records)
            if record["type"] == "response_item"
            and record["payload"].get("type") == "function_call_output"
            and record["payload"].get("call_id") == call_id
        ]
        _require(len(outputs) == 1,
                 f"subagent {child_id} followup_task has no unique result")
        output_index, output = outputs[0]
        output_metadata = output.get("internal_chat_message_metadata_passthrough")
        _require(call_index < interaction_index < output_index < next_index
                 and interaction_payload.get("turn_id") == parent_turn_id
                 and interaction.get("agent_thread_id") == child_id
                 and interaction.get("agent_path") == agent_path
                 and isinstance(output_metadata, dict)
                 and output_metadata.get("turn_id") == parent_turn_id
                 and output.get("output") == "",
                 f"subagent {child_id} followup_task lifecycle is inconsistent")
        result.append({
            "call_id": call_id,
            "native_name": "followup_task",
            "target": parsed["target"],
            "task_input": _opaque(parsed["message"]),
            "prior_completed_native_event_id": terminal_ids[position],
            "prior_completed_native_event_index": previous_index,
            "call_record_index": call_index,
            "interaction_record_index": interaction_index,
            "result_record_index": output_index,
            "completed_native_event_id": _nonempty(
                terminals[position + 1][1].get("id"),
                "subagent completion event id",
            ),
            "completed_native_event_index": next_index,
        })
    return result


def _discover_dispatches(records: list[dict[str, Any]], parent_id: str,
                          parent_depth: int, capture_dispatch_item_markers: bool) \
        -> list[dict[str, Any]]:
    _require(type(capture_dispatch_item_markers) is bool,
             "capture_dispatch_item_markers must be boolean")
    started, terminals = _subagent_activities(records, parent_id)
    dispatches = []
    for child_id, (start, start_index, start_turn) in sorted(
            started.items(), key=lambda pair: pair[1][1]):
        activities = terminals.get(child_id, [])
        call_id = _nonempty(start.get("id"), "subagent spawn call id")
        calls = _function_calls(records, call_id)
        _require(len(calls) == 1, f"subagent {child_id} does not join one native function call")
        call = calls[0]
        _require(call.get("namespace") == "collaboration" and call.get("name") == "spawn_agent",
                 f"subagent {child_id} did not originate from spawn_agent")
        arguments = call.get("arguments")
        _require(isinstance(arguments, str), "spawn_agent arguments are not serialized JSON")
        parsed = _loads(arguments, "spawn_agent arguments")
        _require(isinstance(parsed, dict) and "message" in parsed, "spawn_agent arguments are incomplete")
        role = parsed.get("agent_type")
        task_name = parsed.get("task_name")
        fork_turns = parsed.get("fork_turns")
        _require(role is None or isinstance(role, str) and bool(role.strip()), "invalid spawn_agent role")
        _require(task_name is None or isinstance(task_name, str) and bool(task_name.strip()),
                 "invalid spawn_agent task name")
        _require(fork_turns is None or isinstance(fork_turns, str) and bool(fork_turns.strip()),
                 "invalid spawn_agent fork_turns")
        followups = _followup_chain(
            records, parent_id=parent_id, child_id=child_id,
            agent_path=start["agent_path"], task_name=task_name,
            parent_turn_id=start_turn, start_index=start_index,
            terminals=activities,
        )
        if not activities:
            finish_id = None
            finish_index = None
            completion_source = "child-task-complete-error"
            terminal_kind = None
        else:
            terminal_kind, finish, finish_index, _ = activities[-1]
            finish_id = _nonempty(finish.get("id"), "subagent completion event id")
            completion_source = (
                "parent-subagent-activity" if terminal_kind == "completed"
                else "parent-subagent-interrupted"
            )
        if terminal_kind == "interrupted":
            _validate_interruption_binding(
                records, child_id=child_id, agent_path=start["agent_path"],
                task_name=task_name, parent_turn_id=start_turn,
                activity_id=finish_id, activity_index=finish_index,
            )
        dispatch = {
            "id": call_id,
            "name": "spawn_agent",
            "namespace": "collaboration",
            "parent_thread_id": parent_id,
            "child_thread_id": child_id,
            "agent_path": start["agent_path"],
            "depth": parent_depth + 1,
            "role": role,
            "role_source": "function_call" if role is not None else None,
            "task_name": task_name,
            "fork_turns": fork_turns,
            "task_input": _opaque(parsed["message"]),
            "followup_turns": followups,
            "turn_completions": [
                {
                    "kind": kind,
                    "id": _nonempty(item.get("id"), "subagent completion event id"),
                    "native_event_index": index,
                }
                for kind, item, index, _ in activities
            ],
            "status": "completed" if terminal_kind == "completed" else "pending",
            "parent_turn_id": start_turn,
            "native_event_index": start_index,
            "completed_native_event_id": finish_id,
            "completed_native_event_index": finish_index,
            "completion_source": completion_source,
        }
        if capture_dispatch_item_markers:
            dispatch["item_attribution"] = _dispatch_item_attribution(parsed["message"])
        dispatches.append(dispatch)
    return dispatches


def _parent_agent_path(agent_path: object) -> str:
    text = _nonempty(agent_path, "subagent path")
    parsed = PurePosixPath(text)
    _require(parsed.is_absolute() and parsed.as_posix() == text
             and parsed.parts[:2] == ("/", "root") and len(parsed.parts) >= 3
             and all(part not in {"", ".", ".."} for part in parsed.parts[1:]),
             "subagent path is not a canonical native agent path")
    return parsed.parent.as_posix()


def _delivery_boundary(dispatch: Mapping[str, Any]) -> int:
    completion = dispatch.get("completed_native_event_index")
    if type(completion) is int and completion >= 0:
        return completion
    _require(dispatch.get("status") == "failed"
             and dispatch.get("completion_source") == "child-task-complete-error",
             "subagent completion index is invalid")
    started = dispatch.get("native_event_index")
    _require(type(started) is int and started >= 0,
             "subagent start index is invalid")
    return started


def _first_delivery_boundary(dispatch: Mapping[str, Any]) -> int:
    completions = dispatch.get("turn_completions")
    if isinstance(completions, list) and completions:
        first = completions[0]
        if isinstance(first, Mapping) and type(first.get("native_event_index")) is int \
                and first["native_event_index"] >= 0:
            return first["native_event_index"]
    return _delivery_boundary(dispatch)


def _delivery_bindings(dispatches: list[dict[str, Any]]) \
        -> tuple[dict[str, dict[str, Any]], set[str], int]:
    by_author: dict[str, dict[str, Any]] = {}
    recipients: set[str] = set()
    completions = []
    for dispatch in dispatches:
        author = _nonempty(dispatch.get("agent_path"), "delivery author path")
        _require(author not in by_author, "subagent delivery author path is ambiguous")
        completion = _first_delivery_boundary(dispatch)
        by_author[author] = dispatch
        recipients.add(_parent_agent_path(author))
        completions.append(completion)
    return by_author, recipients, min(completions, default=0)


def _interim_ciphertext(
    payload: Mapping[str, Any], dispatch: Mapping[str, Any],
) -> str | None:
    author = dispatch["agent_path"]
    recipient = _parent_agent_path(author)
    content = payload.get("content")
    if not (
        isinstance(content, list) and len(content) == 2
        and isinstance(content[0], dict)
        and set(content[0]) == {"type", "text"}
        and content[0].get("type") == "input_text"
        and isinstance(content[1], dict)
        and set(content[1]) == {"type", "encrypted_content"}
        and content[1].get("type") == "encrypted_content"
        and isinstance(content[1].get("encrypted_content"), str)
        and bool(content[1]["encrypted_content"])
    ):
        return None
    expected = (
        f"Message Type: MESSAGE\nTask name: {recipient}\n"
        f"Sender: {author}\nPayload:\n"
    )
    if content[0].get("text") != expected:
        return None
    metadata = payload.get("internal_chat_message_metadata_passthrough")
    _require(payload.get("recipient") == recipient,
             f"subagent {author} interim delivery has conflicting ownership")
    _require(isinstance(metadata, dict)
             and metadata.get("turn_id") == dispatch.get("parent_turn_id"),
             f"subagent {author} interim delivery has the wrong turn")
    _nonempty(payload.get("id"), "interim delivery message id")
    return content[1]["encrypted_content"]


def _child_interim_sends(
    records: list[dict[str, Any]], dispatch: Mapping[str, Any],
) -> list[dict[str, Any]]:
    child_id = dispatch["child_thread_id"]
    parent_id = dispatch["parent_thread_id"]
    target = _parent_agent_path(dispatch["agent_path"])
    result: list[dict[str, Any]] = []
    identities: set[str] = set()
    ciphertexts: set[str] = set()
    for index, record in enumerate(records):
        payload = record["payload"]
        if (record["type"] != "response_item" or payload.get("type") != "function_call"
                or payload.get("namespace") != "collaboration"
                or payload.get("name") != "send_message"):
            continue
        parsed = _loads(payload.get("arguments"), "native send_message arguments")
        _require(isinstance(parsed, dict) and set(parsed) == {"target", "message"},
                 "native send_message arguments are incomplete")
        if parsed.get("target") != target:
            continue
        ciphertext = _nonempty(parsed.get("message"), "native send_message ciphertext")
        call_id = _nonempty(payload.get("call_id"), "native send_message call id")
        _require(call_id not in identities, "native send_message call id is duplicated")
        _require(ciphertext not in ciphertexts, "native send_message ciphertext is replayed")
        metadata = payload.get("internal_chat_message_metadata_passthrough")
        _require(isinstance(metadata, dict), "native send_message turn metadata is missing")
        turn_id = _validated_thread_id(metadata.get("turn_id"), "native send_message turn id")
        interactions = []
        for interaction_index, candidate in enumerate(records):
            candidate_payload = _payload(candidate, "item_completed")
            if candidate_payload is None or candidate_payload.get("thread_id") != child_id:
                continue
            item = candidate_payload.get("item")
            if (isinstance(item, dict) and item.get("type") == "SubAgentActivity"
                    and item.get("kind") == "interacted" and item.get("id") == call_id):
                interactions.append((interaction_index, candidate_payload, item))
        _require(len(interactions) == 1,
                 "native send_message has no unique interacted activity")
        interaction_index, interaction_payload, interaction = interactions[0]
        _require(index < interaction_index,
                 "native send_message interacted activity is out of order")
        _require(interaction_payload.get("turn_id") == turn_id,
                 "native send_message interacted activity crossed turns")
        _require(interaction.get("agent_thread_id") == parent_id
                 and interaction.get("agent_path") == target,
                 "native send_message interacted activity has the wrong parent")
        encoded = ciphertext.encode("utf-8", errors="strict")
        result.append({
            "call_id": call_id,
            "child_thread_id": child_id,
            "child_turn_id": turn_id,
            "target": target,
            "ciphertext": ciphertext,
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "bytes": len(encoded),
            "call_record_index": index,
            "interaction_record_index": interaction_index,
        })
        identities.add(call_id)
        ciphertexts.add(ciphertext)
    return result


def _causal_interim_deliveries(
    parent_records: list[dict[str, Any]], child_records: list[dict[str, Any]],
    dispatch: Mapping[str, Any],
) -> tuple[set[int], list[dict[str, Any]]]:
    sends = _child_interim_sends(child_records, dispatch)
    received = []
    author = dispatch["agent_path"]
    for index, record in enumerate(parent_records):
        payload = record["payload"]
        if (record["type"] != "response_item" or payload.get("type") != "agent_message"
                or payload.get("author") != author
                or index <= dispatch["native_event_index"]):
            continue
        ciphertext = _interim_ciphertext(payload, dispatch)
        if ciphertext is not None:
            received.append((index, payload, ciphertext))
    _require(len(received) == len(sends),
             f"subagent {author} interim deliveries are not one-to-one")
    consumed: set[int] = set()
    evidence = []
    used_calls: set[str] = set()
    for index, payload, ciphertext in received:
        matches = [value for value in sends if value["ciphertext"] == ciphertext]
        _require(len(matches) == 1,
                 f"subagent {author} interim delivery has no unique causal send")
        send = matches[0]
        _require(send["call_id"] not in used_calls,
                 f"subagent {author} interim delivery replays one causal send")
        message_id = _nonempty(payload.get("id"), "interim delivery message id")
        evidence.append({
            "schema": "codex-native-interim-delivery/v1",
            "message_id": message_id,
            "sha256": send["sha256"],
            "bytes": send["bytes"],
            "author": author,
            "recipient": send["target"],
            "parent_turn_id": dispatch["parent_turn_id"],
            "child_thread_id": send["child_thread_id"],
            "child_turn_id": send["child_turn_id"],
            "call_id": send["call_id"],
            "call_record_index": send["call_record_index"],
            "interaction_record_index": send["interaction_record_index"],
            "delivery_record_index": index,
        })
        consumed.add(index)
        used_calls.add(send["call_id"])
    _require(len(used_calls) == len(sends),
             f"subagent {author} has an unconsumed causal interim send")
    return consumed, evidence


def _delivery_candidates(records: list[dict[str, Any]],
                         by_author: Mapping[str, Mapping[str, Any]],
                         recipients: set[str], earliest_completion: int,
                         interim_indexes: set[int]) \
        -> dict[str, list[tuple[int, dict[str, Any]]]]:
    candidates: dict[str, list[tuple[int, dict[str, Any]]]] = {
        author: [] for author in by_author
    }
    for index, record in enumerate(records):
        payload = record["payload"]
        if (record["type"] != "response_item" or payload.get("type") != "agent_message"):
            continue
        author = payload.get("author")
        if author in by_author:
            dispatch = by_author[author]
            if (index > _first_delivery_boundary(dispatch)
                    and index not in interim_indexes):
                candidates[author].append((index, payload))
            continue
        recipient = payload.get("recipient")
        if (index > earliest_completion and isinstance(author, str)
                and isinstance(recipient, str) and recipient in recipients
                and PurePosixPath(author).parent.as_posix() == recipient):
            raise NativeRolloutInvalid("parent delivery has an unknown direct child author")
    return candidates


def _delivery_evidence(payload: Mapping[str, Any], index: int,
                       dispatch: Mapping[str, Any]) -> dict[str, Any]:
    author = dispatch["agent_path"]
    recipient = _parent_agent_path(author)
    _require(payload.get("recipient") == recipient,
             f"subagent {author} parent delivery has conflicting ownership")
    metadata = payload.get("internal_chat_message_metadata_passthrough")
    _require(isinstance(metadata, dict)
             and metadata.get("turn_id") == dispatch.get("parent_turn_id"),
             f"subagent {author} parent delivery has the wrong turn")
    content = payload.get("content")
    _require(isinstance(content, list) and len(content) == 1
             and isinstance(content[0], dict) and content[0].get("type") == "input_text"
             and set(content[0]) == {"type", "text"},
             f"subagent {author} parent delivery content is ambiguous")
    text = _nonempty(content[0].get("text"), "parent delivery text")
    try:
        encoded = text.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise NativeRolloutInvalid("parent delivery text is not strict UTF-8") from exc
    message_id = payload.get("id")
    _require(message_id is None or isinstance(message_id, str) and bool(message_id.strip()),
             "parent delivery message id is invalid")
    return {
        "message_id": message_id,
        "text": text,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "bytes": len(encoded),
        "author": author,
        "recipient": recipient,
        "turn_id": dispatch["parent_turn_id"],
        "native_event_index": index,
    }


def _completed_turn_deliveries(
    matches: list[tuple[int, dict[str, Any]]], dispatch: dict[str, Any], required: bool,
) -> list[dict[str, Any]]:
    completions = dispatch.get("turn_completions")
    followups = dispatch.get("followup_turns")
    _require(isinstance(completions, list) and completions
             and isinstance(followups, list)
             and len(followups) + 1 == len(completions),
             "subagent completed-turn delivery lifecycle is malformed")
    if not matches and not required:
        return []
    if len(matches) < len(completions):
        raise NativeRolloutIncomplete(
            f"subagent {dispatch['agent_path']} has no native parent delivery"
        )
    _require(len(matches) == len(completions),
             f"subagent {dispatch['agent_path']} has duplicate parent deliveries")
    deliveries = []
    for position, completion in enumerate(completions):
        _require(isinstance(completion, Mapping)
                 and completion.get("kind") == "completed"
                 and type(completion.get("native_event_index")) is int,
                 "subagent completed-turn evidence is malformed")
        lower = completion["native_event_index"]
        upper = followups[position]["call_record_index"] \
            if position < len(followups) else len(matches) + max(
                (index for index, _ in matches), default=0,
            ) + 1
        owned = [(index, payload) for index, payload in matches if lower < index < upper]
        _require(len(owned) == 1,
                 f"subagent {dispatch['agent_path']} parent delivery crossed followup turns")
        deliveries.append(_delivery_evidence(owned[0][1], owned[0][0], dispatch))
    return deliveries


def _causal_interim_by_child(
    records: list[dict[str, Any]], dispatches: list[dict[str, Any]],
    child_records: Mapping[str, list[dict[str, Any]]] | None,
) -> tuple[set[int], dict[str, list[dict[str, Any]]]]:
    interim_indexes: set[int] = set()
    interim_by_child: dict[str, list[dict[str, Any]]] = {}
    if child_records is None:
        return interim_indexes, interim_by_child
    for dispatch in dispatches:
        child_id = dispatch["child_thread_id"]
        _require(child_id in child_records,
                 f"subagent {dispatch['agent_path']} lacks a causal child rollout")
        indexes, evidence = _causal_interim_deliveries(
            records, child_records[child_id], dispatch,
        )
        _require(interim_indexes.isdisjoint(indexes),
                 "interim delivery record is reused across subagents")
        interim_indexes.update(indexes)
        interim_by_child[child_id] = evidence
    return interim_indexes, interim_by_child


def _bind_parent_delivery(
    dispatch: dict[str, Any], matches: list[tuple[int, dict[str, Any]]],
    interim: list[dict[str, Any]], required: bool, seen_message_ids: set[str],
) -> dict[str, Any] | None:
    author = dispatch["agent_path"]
    if dispatch.get("completion_source") == "parent-subagent-interrupted":
        _require(dispatch.get("status") == "failed"
                 and isinstance(dispatch.get("terminal_failure"), Mapping),
                 f"subagent {author} interruption proof is malformed")
        _require(not matches,
                 f"subagent {author} interruption conflicts with a parent delivery")
        return None
    completions = dispatch.get("turn_completions")
    if isinstance(completions, list) and completions:
        deliveries = _completed_turn_deliveries(matches, dispatch, required)
        dispatch["turn_deliveries"] = deliveries
        for position, evidence in enumerate(deliveries):
            message_id = evidence["message_id"]
            _require(message_id is None or message_id not in seen_message_ids,
                     "parent delivery message id is duplicated")
            if message_id is not None:
                seen_message_ids.add(message_id)
            if position < len(dispatch["followup_turns"]):
                dispatch["followup_turns"][position]["delivery"] = deliveries[position + 1]
        if not deliveries:
            return None
        _require(not interim or interim[-1]["delivery_record_index"]
                 < deliveries[0]["native_event_index"],
                 f"subagent {author} interim delivery occurred after its final answer")
        return deliveries[0]
    _require(len(matches) <= 1, f"subagent {author} has duplicate parent deliveries")
    if not matches:
        if required:
            raise NativeRolloutIncomplete(f"subagent {author} has no native parent delivery")
        return None
    index, payload = matches[0]
    _require(not interim or interim[-1]["delivery_record_index"] < index,
             f"subagent {author} interim delivery occurred after its final answer")
    evidence = _delivery_evidence(payload, index, dispatch)
    message_id = evidence["message_id"]
    _require(message_id is None or message_id not in seen_message_ids,
             "parent delivery message id is duplicated")
    if message_id is not None:
        seen_message_ids.add(message_id)
    return evidence


def _parent_deliveries(
    records: list[dict[str, Any]], dispatches: list[dict[str, Any]], required: bool,
    child_records: Mapping[str, list[dict[str, Any]]] | None = None,
) -> dict[str, dict[str, Any] | None]:
    by_author, recipients, earliest = _delivery_bindings(dispatches)
    interim_indexes, interim_by_child = _causal_interim_by_child(
        records, dispatches, child_records,
    )
    candidates = _delivery_candidates(
        records, by_author, recipients, earliest, interim_indexes,
    )

    result: dict[str, dict[str, Any] | None] = {}
    seen_message_ids: set[str] = set()
    seen_interim_digests: set[str] = set()
    for author, dispatch in by_author.items():
        child_id = dispatch["child_thread_id"]
        interim = interim_by_child.get(child_id, [])
        dispatch["interim_deliveries"] = interim
        for value in interim:
            _require(value["message_id"] not in seen_message_ids,
                     "interim delivery message id is duplicated")
            _require(value["sha256"] not in seen_interim_digests,
                     "interim delivery ciphertext is replayed")
            seen_message_ids.add(value["message_id"])
            seen_interim_digests.add(value["sha256"])
        matches = candidates[author]
        result[child_id] = _bind_parent_delivery(
            dispatch, matches, interim, required, seen_message_ids,
        )
    return result


def _usage(records: list[dict[str, Any]], thread_id: str,
           turn_ids: set[str]) -> dict[str, int]:
    required = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                "output_tokens", "reasoning_output_tokens", "total_tokens")
    found = []
    for record in records:
        payload = record["payload"]
        if record["type"] != "token_usage_record" or payload.get("thread_id") != thread_id:
            continue
        _require(payload.get("turn_id") in turn_ids, f"rollout {thread_id} usage has an unknown turn")
        usage = payload.get("thread_token_usage")
        _require(isinstance(usage, dict), f"rollout {thread_id} usage is malformed")
        normalized = {}
        for key in required:
            value = usage.get(key)
            _require(type(value) is int and value >= 0, f"rollout {thread_id} usage {key} is invalid")
            normalized[key] = value
        _require(normalized["total_tokens"] == normalized["input_tokens"] + normalized["output_tokens"],
                 f"rollout {thread_id} total usage is inconsistent")
        found.append(normalized)
    _require(bool(found), f"rollout {thread_id} contains no native usage")
    return found[-1]


def _turn_metadata(records: list[dict[str, Any]], thread_id: str,
                   turn_ids: set[str], cwd: str) -> dict[str, Any]:
    contexts = [record["payload"] for record in records
                if record["type"] == "turn_context" and record["payload"].get("turn_id") in turn_ids]
    _require(bool(contexts), f"rollout {thread_id} contains no matching turn context")
    for context in contexts:
        _require(context.get("cwd") == cwd, f"rollout {thread_id} turn context crossed case cwd")
        _nonempty(context.get("model"), f"rollout {thread_id} model")
    return {"model": contexts[-1]["model"], "turn_ids": sorted(turn_ids),
            "usage_scope": "cumulative-thread"}


def _normalized_file_changes(value: object) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    if isinstance(value, list):
        _require(bool(value), "native file change is empty")
        entries = []
        for change in value:
            _require(isinstance(change, Mapping), "native file change entry is malformed")
            _require(set(change) == {"path", "kind"},
                     "native file change entry is ambiguous")
            entries.append((change.get("path"), change.get("kind")))
    elif isinstance(value, Mapping):
        _require(bool(value), "native file change is empty")
        entries = []
        for path, metadata in value.items():
            _require(isinstance(metadata, Mapping),
                     "native file change metadata is malformed")
            kind = metadata.get("type")
            _require(isinstance(kind, str) and kind in _FILE_CHANGE_KINDS,
                     "native file change type is unknown")
            if kind in {"add", "delete"}:
                _require(set(metadata) == {"type", "content"}
                         and isinstance(metadata.get("content"), str),
                         f"native file change {kind} metadata is malformed")
            else:
                move_path = metadata.get("move_path")
                _require(set(metadata) == {"type", "unified_diff", "move_path"}
                         and isinstance(metadata.get("unified_diff"), str)
                         and (move_path is None or isinstance(move_path, str)
                              and bool(move_path.strip())),
                         "native file change update metadata is malformed")
            entries.append((path, kind))
    else:
        raise NativeRolloutInvalid("native file change is malformed")

    for path, kind in entries:
        _require(isinstance(path, str) and bool(path.strip()),
                 "native file change path is malformed")
        _require(path not in seen_paths, "native file change path is duplicated")
        _require(isinstance(kind, str) and kind in _FILE_CHANGE_KINDS,
                 "native file change kind is unknown")
        seen_paths.add(path)
        normalized.append({"path": path, "kind": kind})
    return normalized


def _tool_call(item: dict[str, Any], thread_id: str, index: int) -> dict[str, Any]:
    native_type = item["type"]
    if native_type == "CommandExecution":
        name, namespace = "command_execution", "codex"
        input_keys = ("command", "cwd", "parsed_cmd", "source")
        output_keys = ("stdout", "stderr", "aggregated_output", "formatted_output", "exit_code", "duration")
        command = item.get("command")
        _require(isinstance(command, str) and bool(command.strip())
                 or isinstance(command, list) and bool(command)
                 and all(isinstance(part, str) and bool(part) for part in command),
                 "native command is malformed")
        for key in ("stdout", "stderr", "aggregated_output", "formatted_output"):
            _require(key not in item or isinstance(item[key], str), f"native command {key} is malformed")
    elif native_type == "FileChange":
        name, namespace = "file_change", "codex"
        input_keys, output_keys = ("changes",), ()
        normalized_changes = _normalized_file_changes(item.get("changes"))
    elif native_type == "WebSearch":
        name, namespace = "web_search", "codex"
        input_keys, output_keys = ("query", "action"), ()
        _nonempty(item.get("query"), "native web search query")
    elif native_type == "McpToolCall":
        name = _nonempty(item.get("tool"), "native MCP tool name")
        namespace = _nonempty(item.get("server"), "native MCP server")
        input_keys, output_keys = ("arguments",), ("result", "error")
        _require(isinstance(item.get("arguments"), dict), "native MCP arguments are malformed")
    else:
        name = _nonempty(item.get("tool"), "native collaboration operation")
        namespace = "collaboration"
        input_keys = ("sender_thread_id", "receiver_thread_ids", "prompt")
        output_keys = ("agents_states",)
        _validated_thread_id(item.get("sender_thread_id"), "native collaboration sender")
        receivers = item.get("receiver_thread_ids")
        _require(isinstance(receivers, list), "native collaboration receivers are malformed")
        for receiver in receivers:
            _validated_thread_id(receiver, "native collaboration receiver")
    raw_status = item.get("status", "completed" if native_type == "WebSearch" else None)
    status = _nonempty(raw_status, "native tool status")
    _require(status in {"in_progress", "completed", "failed", "declined", "interrupted"},
             "unknown native tool status")
    exit_code = item.get("exit_code")
    _require(exit_code is None or type(exit_code) is int, "native command exit code is invalid")
    success = status == "completed" and (native_type != "CommandExecution" or exit_code == 0)
    return {
        "id": _nonempty(item.get("id"), "native tool item id"),
        "name": name,
        "namespace": namespace,
        "native_type": native_type,
        "thread_id": thread_id,
        "input": ({"changes": normalized_changes} if native_type == "FileChange" else
                  {key: item[key] for key in input_keys if key in item}),
        "output": {key: item[key] for key in output_keys if key in item},
        "status": status,
        "success": success,
        "native_event_index": index,
    }


def _child_tools(
    records: list[dict[str, Any]], thread_id: str,
    post_terminal_completions: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    result = []
    identities: set[str] = set()
    drained = {value["item_id"] for value in post_terminal_completions or []}
    consumed: set[str] = set()
    for index, record in enumerate(records):
        payload = _payload(record, "item_completed")
        if payload is None or payload.get("thread_id") != thread_id:
            continue
        item = payload.get("item")
        _require(isinstance(item, dict), f"rollout {thread_id} has a malformed completed item")
        native_type = _nonempty(item.get("type"), f"rollout {thread_id} completed item type")
        _nonempty(item.get("id"), f"rollout {thread_id} completed item id")
        if native_type not in _TOOL_TYPES:
            continue
        call = _tool_call(item, thread_id, index)
        _require(call["id"] not in identities, f"rollout {thread_id} repeats native item {call['id']}")
        identities.add(call["id"])
        if call["id"] in drained:
            call["model_observed"] = False
            call["post_terminal_completion"] = True
            call["success"] = False
            consumed.add(call["id"])
        result.append(call)
    _require(consumed == drained,
             f"rollout {thread_id} did not project every post-terminal completion exactly once")
    return result


def _plan_repair_commands(
    records: list[dict[str, Any]], root_thread_id: str,
    post_terminal: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    drained = {value["item_id"] for value in post_terminal}
    consumed: set[str] = set()
    commands: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        payload = _payload(record, "item_completed")
        if payload is None or payload.get("thread_id") != root_thread_id:
            continue
        item = payload.get("item")
        if not isinstance(item, dict) or item.get("type") != "CommandExecution":
            continue
        call = _tool_call(item, root_thread_id, index)
        started, completed = payload.get("started_at_ms"), payload.get("completed_at_ms")
        _require(type(started) is int and type(completed) is int
                 and 0 <= started <= completed,
                 "Plan-repair command lifecycle timing is unavailable")
        command = {
            "id": call["id"],
            "turn_id": payload.get("turn_id"),
            "record_index": index,
            "started_at_ns": started * 1_000_000,
            "completed_at_ns": completed * 1_000_000,
            "input": call["input"],
            "output": call["output"],
            "status": call["status"],
            "success": call["success"],
        }
        if call["id"] in drained:
            command.update({
                "model_observed": False,
                "post_terminal_completion": True,
                "success": False,
            })
            consumed.add(call["id"])
        commands.append(command)
    _require(consumed == drained,
             "Plan-repair trace did not consume every post-terminal completion")
    return commands


def _authenticated_tree_threads(
    root_thread_id: str, raw_by_thread: Mapping[str, bytes | str],
    validated_tree: Mapping[str, Any],
) -> tuple[Mapping[str, Any], list[str], dict[str, Mapping[str, Any]]]:
    raw_hashes = validated_tree.get("raw_sha256")
    children = validated_tree.get("children")
    _require(validated_tree.get("schema") == SCHEMA
             and validated_tree.get("root_thread_id") == root_thread_id
             and isinstance(raw_hashes, Mapping)
             and isinstance(children, list)
             and all(isinstance(child, Mapping) for child in children),
             "authenticated command tree is malformed")
    thread_order = [root_thread_id]
    child_by_thread: dict[str, Mapping[str, Any]] = {}
    for child in children:
        thread_id = _validated_thread_id(
            child.get("thread_id"), "authenticated command child thread id",
        )
        _require(thread_id not in child_by_thread and thread_id != root_thread_id,
                 "authenticated command child identities are ambiguous")
        child_by_thread[thread_id] = child
        thread_order.append(thread_id)
    _require(set(raw_by_thread) == set(thread_order) == set(raw_hashes),
             "authenticated command rollout set disagrees with validated tree")
    return raw_hashes, thread_order, child_by_thread


def _authenticated_rollout_commands(
    thread_id: str, raw: bytes | str, expected_sha256: object,
    validated_metadata: object, validated_tools: object,
) -> list[dict[str, Any]]:
    records, encoded = _parse_jsonl(thread_id, raw)
    digest = hashlib.sha256(encoded).hexdigest()
    _require(expected_sha256 == digest,
             f"authenticated command rollout {thread_id} is not hash-bound")
    post_terminal: list[dict[str, Any]] = []
    if isinstance(validated_metadata, Mapping):
        candidate = validated_metadata.get("post_terminal_completions")
        if candidate is not None:
            _require(isinstance(candidate, list)
                     and all(isinstance(item, dict) for item in candidate),
                     f"authenticated command rollout {thread_id} has malformed completions")
            post_terminal = candidate
    calls = _child_tools(records, thread_id, post_terminal)
    if validated_tools is not None:
        _require(validated_tools == calls,
                 f"authenticated command rollout {thread_id} disagrees with validated tools")
    commands = []
    for call in calls:
        if call["name"] != "command_execution":
            continue
        command = {
            "id": call["id"], "thread_id": thread_id,
            "cwd": call["input"].get("cwd"), "raw_sha256": digest,
            "native_event_index": call["native_event_index"],
            "input": call["input"], "output": call["output"],
            "status": call["status"], "success": call["success"],
        }
        command.update({key: call[key] for key in (
            "model_observed", "post_terminal_completion",
        ) if key in call})
        commands.append(command)
    return commands


def _authenticated_command_trace(
    root_thread_id: str, raw_by_thread: Mapping[str, bytes | str],
    validated_tree: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Project every hash-bound root/child command from one validated tree."""

    raw_hashes, thread_order, child_by_thread = _authenticated_tree_threads(
        root_thread_id, raw_by_thread, validated_tree,
    )

    commands: list[dict[str, Any]] = []
    identities: set[tuple[str, str]] = set()
    for thread_id in thread_order:
        if thread_id == root_thread_id:
            metadata = validated_tree.get("native_metadata")
            tools = None
        else:
            child = child_by_thread[thread_id]
            metadata, tools = child.get("native_metadata"), child.get("tool_calls")
        for command in _authenticated_rollout_commands(
            thread_id, raw_by_thread[thread_id], raw_hashes.get(thread_id), metadata, tools,
        ):
            identity = (thread_id, command["id"])
            _require(identity not in identities,
                     "authenticated command identities are ambiguous")
            identities.add(identity)
            commands.append(command)
    return commands


def _validated_plan_repair_dispatches(
    dispatches: list[dict[str, Any]], validated_dispatches: object,
) -> list[dict[str, Any]]:
    if validated_dispatches is None:
        return dispatches
    _require(isinstance(validated_dispatches, list)
             and all(isinstance(item, Mapping) for item in validated_dispatches),
             "Plan-repair validated dispatches are malformed")
    by_id = {item.get("id"): item for item in validated_dispatches}
    _require(None not in by_id and len(by_id) == len(validated_dispatches)
             and set(by_id) == {item["id"] for item in dispatches},
             "Plan-repair validated dispatch identities disagree")
    identity_fields = (
        "id", "parent_thread_id", "child_thread_id", "agent_path",
        "parent_turn_id", "native_event_index", "completed_native_event_id",
        "completed_native_event_index", "completion_source",
    )
    bound = []
    for dispatch in dispatches:
        validated = by_id[dispatch["id"]]
        _require(all(validated.get(field) == dispatch.get(field)
                     for field in identity_fields),
                 "Plan-repair validated dispatch binding disagrees")
        status = validated.get("status")
        _require(status in {"completed", "failed"},
                 "Plan-repair validated dispatch status is malformed")
        if dispatch["completion_source"] in {
            "child-task-complete-error", "parent-subagent-interrupted",
        }:
            _require(status == "failed"
                     and isinstance(validated.get("terminal_failure"), Mapping),
                     "Plan-repair failed dispatch proof is malformed")
        bound.append({**dispatch, "status": status})
    return bound


def _plan_repair_dispatch_trace(
    records: list[dict[str, Any]], dispatch: Mapping[str, Any],
    deliveries: Mapping[str, dict[str, Any] | None],
) -> dict[str, Any]:
    call_id = dispatch["id"]
    matches = [
        (index, record) for index, record in enumerate(records)
        if record["type"] == "response_item"
        and record["payload"].get("type") == "function_call"
        and record["payload"].get("call_id") == call_id
    ]
    _require(len(matches) == 1, "Plan-repair dispatch invocation is ambiguous")
    call_index, call_record = matches[0]
    arguments = call_record["payload"].get("arguments")
    _require(isinstance(arguments, str), "Plan-repair dispatch arguments are malformed")
    parsed = _loads(arguments, "Plan-repair dispatch arguments")
    message = parsed.get("message") if isinstance(parsed, dict) else None
    _require(isinstance(message, str), "Plan-repair dispatch message is not text")
    delivery = deliveries.get(dispatch["child_thread_id"])
    _require(isinstance(delivery, dict), "Plan-repair dispatch has no parent delivery")
    delivery_index = delivery.get("native_event_index")
    _require(type(delivery_index) is int and 0 <= delivery_index < len(records),
             "Plan-repair delivery index is malformed")
    return {
        "id": call_id,
        "role": dispatch.get("role"),
        "message": message,
        "task_input": _opaque(message),
        "invoked_at_ns": _timestamp_ns(
            call_record.get("timestamp"), "Plan-repair dispatch invocation",
        ),
        "returned_at_ns": _timestamp_ns(
            records[delivery_index].get("timestamp"), "Plan-repair dispatch return",
        ),
        "function_record_index": call_index,
        "delivery_record_index": delivery_index,
    }


def _plan_repair_deliveries(
    records: list[dict[str, Any]], dispatches: list[dict[str, Any]],
    validated_dispatches: object,
) -> dict[str, dict[str, Any] | None]:
    if validated_dispatches is None:
        return _parent_deliveries(records, dispatches, True)
    _require(isinstance(validated_dispatches, list)
             and all(isinstance(item, Mapping) for item in validated_dispatches),
             "Plan-repair validated dispatches are malformed")
    by_id = {item.get("id"): item for item in validated_dispatches}
    deliveries: dict[str, dict[str, Any] | None] = {}
    for dispatch in dispatches:
        validated = by_id.get(dispatch["id"])
        delivery = validated.get("delivery") if isinstance(validated, Mapping) else None
        _require(isinstance(delivery, Mapping),
                 "Plan-repair validated dispatch has no parent delivery")
        index = delivery.get("native_event_index")
        _require(type(index) is int and 0 <= index < len(records),
                 "Plan-repair validated delivery index is malformed")
        record = records[index]
        _require(record["type"] == "response_item"
                 and record["payload"].get("type") == "agent_message",
                 "Plan-repair validated delivery record is malformed")
        observed = _delivery_evidence(record["payload"], index, dispatch)
        _require(dict(delivery) == observed,
                 "Plan-repair validated delivery binding disagrees")
        deliveries[dispatch["child_thread_id"]] = observed
    return deliveries


def _plan_repair_validated_inputs(
    value: object,
) -> tuple[object, tuple[Mapping[str, bytes | str], Mapping[str, Any]] | None]:
    if not isinstance(value, Mapping):
        return value, None
    _require(set(value) == {"dispatches", "authenticated_tree"},
             "Plan-repair validated evidence bundle is malformed")
    authenticated = value["authenticated_tree"]
    _require(isinstance(authenticated, tuple) and len(authenticated) == 2
             and isinstance(authenticated[0], Mapping)
             and isinstance(authenticated[1], Mapping),
             "authenticated command inputs are malformed")
    return value["dispatches"], authenticated


def _attach_authenticated_commands(
    result: dict[str, Any], root_thread_id: str, encoded: bytes,
    post_terminal: list[dict[str, Any]],
    authenticated_tree: tuple[Mapping[str, bytes | str], Mapping[str, Any]] | None,
) -> None:
    if authenticated_tree is None:
        validated_tree = {
            "schema": SCHEMA, "root_thread_id": root_thread_id,
            "raw_sha256": {root_thread_id: result["raw_sha256"]},
            "dispatches": [], "children": [],
        }
        if post_terminal:
            validated_tree["native_metadata"] = {
                "post_terminal_completions": post_terminal,
                "rollout_raw_sha256": result["raw_sha256"],
            }
        raw_by_thread = {root_thread_id: encoded}
    else:
        raw_by_thread, validated_tree = authenticated_tree
        _require(root_thread_id in raw_by_thread,
                 "authenticated command inputs omitted the root rollout")
        _root_records, root_encoded = _parse_jsonl(
            root_thread_id, raw_by_thread[root_thread_id],
        )
        _require(root_encoded == encoded,
                 "authenticated command root bytes disagree")
    result["authenticated_commands"] = _authenticated_command_trace(
        root_thread_id, raw_by_thread, validated_tree,
    )


def extract_native_plan_repair_trace(
    root_thread_id: str, raw: bytes | str, *,
    validated_dispatches: object = None,
) -> dict[str, Any]:
    """Return ephemeral root command/dispatch facts needed for Plan-repair proof.

    Raw dispatch text is returned only to the controller caller so it can be
    reduced by ``native_eval_dispatch_context``.  It is deliberately absent
    from the persisted native rollout supplement.
    """
    root_thread_id = _validated_thread_id(root_thread_id, "root thread id")
    records, encoded = _parse_jsonl(root_thread_id, raw)
    metadata = _session_metadata(records, root_thread_id, set())
    _require(metadata.get("source") == "exec"
             and metadata.get("session_id") == root_thread_id
             and metadata.get("thread_source") == "user",
             "Plan-repair root rollout session identity is inconsistent")
    _, post_terminal = _validate_terminal_state(
        records, root_thread_id, allow_post_terminal_completion=True,
    )
    commands = _plan_repair_commands(records, root_thread_id, post_terminal)

    validated_dispatches, authenticated_tree = _plan_repair_validated_inputs(
        validated_dispatches,
    )
    dispatches = _validated_plan_repair_dispatches(
        _discover_dispatches(records, root_thread_id, 0, False),
        validated_dispatches,
    )
    returned_dispatches = [
        dispatch for dispatch in dispatches
        if dispatch["completion_source"] != "parent-subagent-interrupted"
    ]
    deliveries = _plan_repair_deliveries(
        records, returned_dispatches, validated_dispatches,
    )
    result_dispatches = [
        _plan_repair_dispatch_trace(records, dispatch, deliveries)
        for dispatch in returned_dispatches
    ]
    result = {
        "schema": "codex-native-plan-repair-trace/v1",
        "root_thread_id": root_thread_id,
        "raw_sha256": hashlib.sha256(encoded).hexdigest(),
        "commands": commands,
        "dispatches": result_dispatches,
    }
    _attach_authenticated_commands(
        result, root_thread_id, encoded, post_terminal, authenticated_tree,
    )
    if post_terminal:
        result["post_terminal_completions"] = post_terminal
    return result


def _native_child_rollout(
    dispatch: dict[str, Any], parent_id: str, parent_depth: int,
    ancestors: set[str], parsed: Mapping[str, list[dict[str, Any]]],
    encoded: Mapping[str, bytes], cwd: str, seen: set[str],
) -> tuple[str, set[str], dict[str, Any]]:
    child_id = dispatch["child_thread_id"]
    _require(
        child_id not in seen,
        f"native rollout tree contains a cycle or duplicate child {child_id}",
    )
    _require(len(seen) <= MAX_CHILDREN, "native rollout tree exceeds child bounds")
    if child_id not in parsed:
        raise NativeRolloutPending(child_id)
    child_ancestors = ancestors | {parent_id}
    child_meta = _session_metadata(parsed[child_id], child_id, child_ancestors)
    source = child_meta.get("source")
    _require(isinstance(source, dict),
             f"child rollout {child_id} lacks native spawn metadata")
    subagent = source.get("subagent")
    spawn = subagent.get("thread_spawn") if isinstance(subagent, dict) else None
    _require(isinstance(spawn, dict),
             f"child rollout {child_id} lacks thread_spawn metadata")
    _require(spawn.get("parent_thread_id") == parent_id,
             f"child rollout {child_id} has the wrong parent")
    _require(child_meta.get("session_id") == parent_id
             and child_meta.get("thread_source") == "subagent",
             f"child rollout {child_id} session identity has the wrong parent")
    _require(spawn.get("depth") == parent_depth + 1,
             f"child rollout {child_id} has the wrong depth")
    _require(spawn.get("agent_path") == dispatch["agent_path"],
             f"child rollout {child_id} has the wrong agent path")
    _require(child_meta.get("cwd") == cwd,
             f"child rollout {child_id} crossed the case cwd")
    source_role = spawn.get("agent_role")
    _require(source_role is None or isinstance(source_role, str) and bool(source_role.strip()),
             f"child rollout {child_id} has an invalid native role")
    if dispatch["role"] is not None and source_role is not None:
        _require(dispatch["role"] == source_role,
                 f"child rollout {child_id} role disagrees with spawn call")
    elif dispatch["role"] is None and source_role is not None:
        dispatch["role"] = source_role
        dispatch["role_source"] = "session_meta"
    interrupted = dispatch["completion_source"] == "parent-subagent-interrupted"
    child_turn_ids, child_post_terminal = _validate_terminal_state(
        parsed[child_id], child_id, allow_post_terminal_completion=True,
        allow_interrupted=interrupted,
    )
    turn_ids = set(child_turn_ids)
    failure = (_interruption_failure(parsed[child_id], child_id, turn_ids)
               if interrupted else _terminal_failure(parsed[child_id], child_id, turn_ids))
    if dispatch["completion_source"] == "child-task-complete-error":
        _require(failure is not None,
                 f"rollout {parent_id} has unmatched subagent activity")
    dispatch["status"] = "failed" if failure is not None else "completed"
    if failure is not None:
        dispatch["terminal_failure"] = failure
    native_metadata = _turn_metadata(parsed[child_id], child_id, turn_ids, cwd)
    native_metadata.update({"cli_version": child_meta["cli_version"],
                            "model_provider": child_meta["model_provider"], "cwd": cwd})
    if failure is not None:
        native_metadata["terminal_failure"] = failure
    if child_post_terminal:
        native_metadata["post_terminal_completions"] = child_post_terminal
        native_metadata["rollout_raw_sha256"] = hashlib.sha256(encoded[child_id]).hexdigest()
    return child_id, child_ancestors, {
        "thread_id": child_id,
        "parent_thread_id": parent_id,
        "depth": parent_depth + 1,
        "agent_path": dispatch["agent_path"],
        "terminal": dispatch["status"],
        "tool_calls": _child_tools(parsed[child_id], child_id, child_post_terminal),
        "usage": _usage(parsed[child_id], child_id, turn_ids),
        "native_metadata": native_metadata,
    }


def parse_native_tree(root_thread_id: str, raw_by_thread: Mapping[str, bytes | str], *,
                      require_delivery: bool = False,
                      allow_root_only: bool = False,
                      capture_dispatch_item_markers: bool = False) -> dict[str, Any]:
    """Normalize one complete, native Codex rollout tree as nested-only evidence."""
    root_thread_id = _validated_thread_id(root_thread_id, "root thread id")
    _require(isinstance(raw_by_thread, Mapping), "raw_by_thread must be a mapping")
    for key in raw_by_thread:
        _validated_thread_id(key, "raw rollout thread id")
    if root_thread_id not in raw_by_thread:
        raise NativeRolloutPending(root_thread_id)
    parsed: dict[str, list[dict[str, Any]]] = {}
    encoded: dict[str, bytes] = {}
    total_bytes = 0
    for thread_id, value in raw_by_thread.items():
        parsed[thread_id], encoded[thread_id] = _parse_jsonl(thread_id, value)
        total_bytes += len(encoded[thread_id])
        _require(total_bytes <= MAX_TOTAL_BYTES, "native rollout tree exceeds byte bounds")

    root_meta = _session_metadata(parsed[root_thread_id], root_thread_id, set())
    _require(root_meta.get("source") == "exec", "root rollout is not a native exec session")
    _require(root_meta.get("session_id") == root_thread_id and root_meta.get("thread_source") == "user",
             "root rollout session identity is inconsistent")
    _require(type(require_delivery) is bool, "require_delivery must be boolean")
    _require(type(allow_root_only) is bool, "allow_root_only must be boolean")
    _require(type(capture_dispatch_item_markers) is bool,
             "capture_dispatch_item_markers must be boolean")
    root_turn_ids, root_post_terminal = _validate_terminal_state(
        parsed[root_thread_id], root_thread_id,
        allow_post_terminal_completion=True,
    )
    _require(_terminal_failure(parsed[root_thread_id], root_thread_id,
                               set(root_turn_ids)) is None,
             "root rollout ended with a native terminal error")
    cwd = root_meta["cwd"]
    queue: list[tuple[str, int, set[str]]] = [(root_thread_id, 0, set())]
    seen = {root_thread_id}
    dispatches: list[dict[str, Any]] = []
    children: list[dict[str, Any]] = []
    while queue:
        parent_id, parent_depth, ancestors = queue.pop(0)
        parent_records = parsed[parent_id]
        parent_dispatches = _discover_dispatches(
            parent_records, parent_id, parent_depth, capture_dispatch_item_markers,
        )
        for dispatch in parent_dispatches:
            child_id, child_ancestors, child = _native_child_rollout(
                dispatch, parent_id, parent_depth, ancestors, parsed, encoded, cwd, seen,
            )
            children.append(child)
            seen.add(child_id)
            dispatches.append(dispatch)
            queue.append((child_id, parent_depth + 1, child_ancestors))
        deliveries = _parent_deliveries(
            parent_records, parent_dispatches, require_delivery, parsed,
        )
        for dispatch in parent_dispatches:
            dispatch["delivery"] = deliveries[dispatch["child_thread_id"]]

    _require(set(parsed) == seen, "raw_by_thread contains an unreferenced native rollout")
    _require(bool(dispatches) or allow_root_only,
             "root rollout contains no trusted nested dispatch")
    for order, dispatch in enumerate(dispatches, 1):
        dispatch["order"] = order
    result = {
        "schema": SCHEMA,
        "root_thread_id": root_thread_id,
        "scope": "nested-rollouts-only",
        "authority": "native-rollout",
        "merge_policy": "merge-explicit-native-item-ids-or-replace-one-authority",
        "root_tool_calls_included": False,
        "raw_sha256": {thread_id: hashlib.sha256(encoded[thread_id]).hexdigest()
                       for thread_id in sorted(encoded)},
        "dispatches": dispatches,
        "children": children,
    }
    if root_post_terminal:
        result["native_metadata"] = {
            "post_terminal_completions": root_post_terminal,
            "rollout_raw_sha256": hashlib.sha256(encoded[root_thread_id]).hexdigest(),
        }
    return result


def _rollout_name(thread_id: str) -> re.Pattern[str]:
    return re.compile(r"rollout-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}(?:\.\d+)?-"
                      + re.escape(thread_id) + r"\.jsonl")


def _find_rollout(sessions_root: Path, thread_id: str) -> Path:
    pattern = _rollout_name(thread_id)
    matches: list[Path] = []
    stack = [(sessions_root, 0)]
    scanned = 0
    while stack:
        directory, depth = stack.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise NativeRolloutInvalid(f"cannot scan native sessions directory: {exc}") from exc
        for entry in entries:
            scanned += 1
            _require(scanned <= MAX_SCAN_ENTRIES, "native session scan exceeds entry bounds")
            if entry.is_symlink():
                _require(pattern.fullmatch(entry.name) is None,
                         f"native rollout {thread_id} is a symlink")
                continue
            if entry.is_file(follow_symlinks=False) and pattern.fullmatch(entry.name):
                matches.append(Path(entry.path))
            elif depth < MAX_SCAN_DEPTH and entry.is_dir(follow_symlinks=False):
                stack.append((Path(entry.path), depth + 1))
    if not matches:
        raise NativeRolloutPending(thread_id)
    _require(len(matches) == 1, f"multiple exact native rollouts found for {thread_id}")
    return matches[0]


def _read_stable(path: Path, thread_id: str, sessions_root: Path) -> bytes:
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise NativeRolloutInvalid(f"cannot resolve native rollout {thread_id}: {exc}") from exc
    _require(resolved.is_relative_to(sessions_root), f"native rollout {thread_id} escaped sessions root")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise NativeRolloutInvalid(f"cannot open native rollout {thread_id}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        _require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= MAX_ROLLOUT_BYTES,
                 f"native rollout {thread_id} has invalid file type or size")
        chunks = []
        remaining = MAX_ROLLOUT_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        value = b"".join(chunks)
        _require(len(value) <= MAX_ROLLOUT_BYTES, f"native rollout {thread_id} exceeds byte bounds")
        after = os.fstat(descriptor)
        stable = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        _require(all(getattr(before, key) == getattr(after, key) for key in stable),
                 f"native rollout {thread_id} changed while being read")
        current = os.stat(path, follow_symlinks=False)
        _require(stat.S_ISREG(current.st_mode)
                 and (current.st_dev, current.st_ino) == (after.st_dev, after.st_ino)
                 and path.resolve(strict=True) == resolved,
                 f"native rollout {thread_id} changed identity while being read")
        return value
    except OSError as exc:
        raise NativeRolloutInvalid(f"cannot verify native rollout {thread_id}: {exc}") from exc
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_raw(path: Path, value: bytes) -> dict[str, Any]:
    try:
        with path.open("xb") as stream:
            written = stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
            _require(written == len(value) and os.fstat(stream.fileno()).st_size == len(value),
                     "native rollout evidence write was incomplete")
    except OSError as exc:
        raise NativeRolloutInvalid(f"cannot publish native rollout evidence: {exc}") from exc
    return {"path": path.name, "sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value)}


def collect_native_tree(root_thread_id: str, sessions_root: Path,
                        destination_dir: Path, *, require_delivery: bool = False,
                        allow_root_only: bool = False,
                        capture_dispatch_item_markers: bool = False) -> dict[str, Any]:
    """Collect exact native rollouts into a new immutable attempt-owned directory."""
    root_thread_id = _validated_thread_id(root_thread_id, "root thread id")
    sessions = Path(sessions_root).absolute()
    _require(sessions.is_dir() and not sessions.is_symlink(), "native sessions root is not a directory")
    try:
        sessions = sessions.resolve(strict=True)
    except OSError as exc:
        raise NativeRolloutInvalid(f"cannot resolve native sessions root: {exc}") from exc

    raw_by_thread: dict[str, bytes] = {}
    pending = root_thread_id
    observation = None
    while observation is None:
        _require(pending not in raw_by_thread, f"native rollout discovery cycled at {pending}")
        source = _find_rollout(sessions, pending)
        raw_by_thread[pending] = _read_stable(source, pending, sessions)
        try:
            observation = parse_native_tree(
                root_thread_id, raw_by_thread, require_delivery=require_delivery,
                allow_root_only=allow_root_only,
                capture_dispatch_item_markers=capture_dispatch_item_markers,
            )
        except NativeRolloutPending as exc:
            pending = exc.thread_id

    destination = Path(destination_dir).absolute()
    _require(not destination.exists() and not destination.is_symlink(),
             "native rollout destination must be new")
    destination_parent = destination.parent
    try:
        destination_parent.mkdir(parents=True, exist_ok=True)
        parent_resolved = destination_parent.resolve(strict=True)
        destination = parent_resolved / destination.name
        _require(not destination.is_relative_to(sessions),
                 "native rollout destination must be outside the sessions root")
        destination.mkdir(mode=0o700)
    except OSError as exc:
        raise NativeRolloutInvalid(f"cannot create native rollout destination: {exc}") from exc

    evidence = {}
    for thread_id in sorted(raw_by_thread):
        ref = _write_raw(destination / f"rollout-{thread_id}.jsonl", raw_by_thread[thread_id])
        _require(ref["sha256"] == observation["raw_sha256"][thread_id],
                 f"copied native rollout {thread_id} changed digest")
        evidence[thread_id] = ref
    try:
        write_json_once(destination / "supplement.json", observation)
        with (destination / "supplement.json").open("rb") as stream:
            os.fsync(stream.fileno())
        _fsync_directory(destination)
        _fsync_directory(destination.parent)
    except (OSError, FileExistsError) as exc:
        raise NativeRolloutInvalid(f"cannot publish native rollout supplement: {exc}") from exc
    return {
        "schema": COLLECTION_SCHEMA,
        "root_thread_id": root_thread_id,
        "evidence": evidence,
        "supplement": observation,
        "supplement_path": "supplement.json",
    }


def collect_native_skill_injections(
    root_thread_id: str,
    sessions_root: Path,
    destination_dir: Path,
    *,
    expected_cwd: str,
    expected_prompt: str,
    skill_witnesses: Mapping[str, object],
    plugin_name: str | None = None,
) -> dict[str, Any]:
    """Collect and qualify one exact root rollout in an immutable directory."""
    root_thread_id = _validated_thread_id(root_thread_id, "root thread id")
    sessions = Path(sessions_root).absolute()
    _require(sessions.is_dir() and not sessions.is_symlink(),
             "native sessions root is not a directory")
    try:
        sessions = sessions.resolve(strict=True)
    except OSError as exc:
        raise NativeRolloutInvalid(f"cannot resolve native sessions root: {exc}") from exc

    source = _find_rollout(sessions, root_thread_id)
    raw = _read_stable(source, root_thread_id, sessions)
    observation = parse_native_skill_injections(
        root_thread_id,
        raw,
        expected_cwd=expected_cwd,
        expected_prompt=expected_prompt,
        skill_witnesses=skill_witnesses,
        plugin_name=plugin_name,
    )

    destination = Path(destination_dir).absolute()
    _require(not destination.exists() and not destination.is_symlink(),
             "native rollout destination must be new")
    destination_parent = destination.parent
    try:
        destination_parent.mkdir(parents=True, exist_ok=True)
        parent_resolved = destination_parent.resolve(strict=True)
        destination = parent_resolved / destination.name
        _require(not destination.is_relative_to(sessions),
                 "native rollout destination must be outside the sessions root")
        destination.mkdir(mode=0o700)
    except OSError as exc:
        raise NativeRolloutInvalid(f"cannot create native rollout destination: {exc}") from exc

    ref = _write_raw(destination / f"rollout-{root_thread_id}.jsonl", raw)
    _require(ref["sha256"] == observation["raw_sha256"],
             "copied native skill-injection rollout changed digest")
    evidence = {root_thread_id: ref}
    try:
        write_json_once(destination / "supplement.json", observation)
        with (destination / "supplement.json").open("rb") as stream:
            os.fsync(stream.fileno())
        _fsync_directory(destination)
        _fsync_directory(destination.parent)
    except (OSError, FileExistsError) as exc:
        raise NativeRolloutInvalid(f"cannot publish native rollout supplement: {exc}") from exc
    return {
        "schema": SKILL_INJECTION_COLLECTION_SCHEMA,
        "root_thread_id": root_thread_id,
        "evidence": evidence,
        "supplement": observation,
        "supplement_path": "supplement.json",
    }
