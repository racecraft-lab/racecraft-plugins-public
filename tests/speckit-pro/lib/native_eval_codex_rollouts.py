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

_THREAD_ID_PATTERN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_SKILL_NAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]*")
_PLUGIN_NAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]*")
_TOOL_TYPES = frozenset({"CommandExecution", "FileChange", "McpToolCall",
                         "CollabAgentToolCall", "WebSearch"})
_FAILURE_EVENTS = frozenset({"error", "task_failed", "turn_aborted", "turn_failed"})
_SKILL_CONTENT_KIND = "skills.selected_skill_instructions"
_PROMPT_CONTENT_KIND = "user.text"
_DISPATCH_ITEM_MARKER = re.compile(r"\[\[native-eval-item:([a-z0-9][a-z0-9._-]*)\]\]")


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


def _validate_terminal(records: list[dict[str, Any]], thread_id: str) -> list[str]:
    for record in records:
        _require(not (record["type"] == "event_msg"
                      and record["payload"].get("type") in _FAILURE_EVENTS),
                 f"rollout {thread_id} contains a native error event")
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
            if record["type"] == "event_msg":
                _require(payload.get("type") not in _FAILURE_EVENTS,
                         f"rollout {thread_id} contains a terminal error")
    _require(bool(scoped), f"rollout {thread_id} contains no thread-owned events")
    for turn_id, indexes in scoped.items():
        starts = [index for index, record in enumerate(records)
                  if (value := _payload(record, "task_started")) is not None
                  and value.get("turn_id") == turn_id]
        completes = [index for index, record in enumerate(records)
                     if (value := _payload(record, "task_complete")) is not None
                     and value.get("turn_id") == turn_id]
        _require(len(starts) == 1 and len(completes) == 1,
                 f"rollout {thread_id} does not have one terminal pair for turn {turn_id}")
        _require(starts[0] < min(indexes) <= max(indexes) < completes[0],
                 f"rollout {thread_id} has invalid terminal ordering")
        for record in records:
            payload = record["payload"]
            if (payload.get("turn_id") == turn_id or payload.get("thread_id") == thread_id):
                _require(payload.get("type") not in _FAILURE_EVENTS,
                         f"rollout {thread_id} contains a failed turn")
    return list(scoped)


def _function_calls(records: list[dict[str, Any]], call_id: str) -> list[dict[str, Any]]:
    return [record["payload"] for record in records
            if record["type"] == "response_item"
            and record["payload"].get("type") == "function_call"
            and record["payload"].get("call_id") == call_id]


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


def _discover_dispatches(records: list[dict[str, Any]], parent_id: str,
                          parent_depth: int, capture_dispatch_item_markers: bool) \
        -> list[dict[str, Any]]:
    _require(type(capture_dispatch_item_markers) is bool,
             "capture_dispatch_item_markers must be boolean")
    started: dict[str, tuple[dict[str, Any], int, str]] = {}
    completed: dict[str, tuple[dict[str, Any], int, str]] = {}
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
        _require(kind in {"started", "completed"}, "unknown subagent activity kind")
        target = started if kind == "started" else completed
        _require(child_id not in target, f"duplicate {kind} activity for {child_id}")
        target[child_id] = (item, index, turn_id)
    _require(set(started) == set(completed), f"rollout {parent_id} has unmatched subagent activity")
    dispatches = []
    for child_id, (start, start_index, start_turn) in sorted(
            started.items(), key=lambda pair: pair[1][1]):
        finish, finish_index, finish_turn = completed[child_id]
        _require(start_index < finish_index and start["agent_path"] == finish["agent_path"]
                 and start_turn == finish_turn,
                 f"subagent {child_id} activity does not bind to one path and order")
        finish_id = _nonempty(finish.get("id"), "subagent completion event id")
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
            "status": "completed",
            "parent_turn_id": start_turn,
            "native_event_index": start_index,
            "completed_native_event_id": finish_id,
            "completed_native_event_index": finish_index,
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


def _delivery_bindings(dispatches: list[dict[str, Any]]) \
        -> tuple[dict[str, dict[str, Any]], set[str], int]:
    by_author: dict[str, dict[str, Any]] = {}
    recipients: set[str] = set()
    completions = []
    for dispatch in dispatches:
        author = _nonempty(dispatch.get("agent_path"), "delivery author path")
        _require(author not in by_author, "subagent delivery author path is ambiguous")
        completion = dispatch.get("completed_native_event_index")
        _require(type(completion) is int and completion >= 0,
                 "subagent completion index is invalid")
        by_author[author] = dispatch
        recipients.add(_parent_agent_path(author))
        completions.append(completion)
    return by_author, recipients, min(completions, default=0)


def _delivery_candidates(records: list[dict[str, Any]],
                         by_author: Mapping[str, Mapping[str, Any]],
                         recipients: set[str], earliest_completion: int) \
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
            if index > dispatch["completed_native_event_index"]:
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
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "bytes": len(encoded),
        "author": author,
        "recipient": recipient,
        "turn_id": dispatch["parent_turn_id"],
        "native_event_index": index,
    }


def _parent_deliveries(records: list[dict[str, Any]], dispatches: list[dict[str, Any]],
                       required: bool) -> dict[str, dict[str, Any] | None]:
    by_author, recipients, earliest = _delivery_bindings(dispatches)
    candidates = _delivery_candidates(records, by_author, recipients, earliest)

    result: dict[str, dict[str, Any] | None] = {}
    seen_message_ids: set[str] = set()
    for author, dispatch in by_author.items():
        matches = candidates[author]
        _require(len(matches) <= 1, f"subagent {author} has duplicate parent deliveries")
        if not matches:
            if required:
                raise NativeRolloutIncomplete(f"subagent {author} has no native parent delivery")
            result[dispatch["child_thread_id"]] = None
            continue
        index, payload = matches[0]
        evidence = _delivery_evidence(payload, index, dispatch)
        message_id = evidence["message_id"]
        _require(message_id is None or message_id not in seen_message_ids,
                 "parent delivery message id is duplicated")
        if message_id is not None:
            seen_message_ids.add(message_id)
        result[dispatch["child_thread_id"]] = evidence
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
        _require(isinstance(item.get("changes"), list), "native file change is malformed")
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
        "input": {key: item[key] for key in input_keys if key in item},
        "output": {key: item[key] for key in output_keys if key in item},
        "status": status,
        "success": success,
        "native_event_index": index,
    }


def _child_tools(records: list[dict[str, Any]], thread_id: str) -> list[dict[str, Any]]:
    result = []
    identities: set[str] = set()
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
        result.append(call)
    return result


def extract_native_plan_repair_trace(
    root_thread_id: str, raw: bytes | str,
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
    _validate_terminal(records, root_thread_id)

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
        commands.append({
            "id": call["id"],
            "turn_id": payload.get("turn_id"),
            "record_index": index,
            "started_at_ns": started * 1_000_000,
            "completed_at_ns": completed * 1_000_000,
            "input": call["input"],
            "output": call["output"],
            "status": call["status"],
            "success": call["success"],
        })

    dispatches = _discover_dispatches(records, root_thread_id, 0, False)
    deliveries = _parent_deliveries(records, dispatches, True)
    result_dispatches: list[dict[str, Any]] = []
    for dispatch in dispatches:
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
        result_dispatches.append({
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
        })
    return {
        "schema": "codex-native-plan-repair-trace/v1",
        "root_thread_id": root_thread_id,
        "raw_sha256": hashlib.sha256(encoded).hexdigest(),
        "commands": commands,
        "dispatches": result_dispatches,
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
    _validate_terminal(parsed[root_thread_id], root_thread_id)
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
            child_id = dispatch["child_thread_id"]
            _require(child_id not in seen, f"native rollout tree contains a cycle or duplicate child {child_id}")
            _require(len(seen) <= MAX_CHILDREN, "native rollout tree exceeds child bounds")
            if child_id not in parsed:
                raise NativeRolloutPending(child_id)
            child_ancestors = ancestors | {parent_id}
            child_meta = _session_metadata(parsed[child_id], child_id, child_ancestors)
            source = child_meta.get("source")
            _require(isinstance(source, dict), f"child rollout {child_id} lacks native spawn metadata")
            spawn = source.get("subagent", {}).get("thread_spawn") if isinstance(source.get("subagent"), dict) else None
            _require(isinstance(spawn, dict), f"child rollout {child_id} lacks thread_spawn metadata")
            _require(spawn.get("parent_thread_id") == parent_id,
                     f"child rollout {child_id} has the wrong parent")
            _require(child_meta.get("session_id") == parent_id
                     and child_meta.get("thread_source") == "subagent",
                     f"child rollout {child_id} session identity has the wrong parent")
            _require(spawn.get("depth") == parent_depth + 1,
                     f"child rollout {child_id} has the wrong depth")
            _require(spawn.get("agent_path") == dispatch["agent_path"],
                     f"child rollout {child_id} has the wrong agent path")
            _require(child_meta.get("cwd") == cwd, f"child rollout {child_id} crossed the case cwd")
            source_role = spawn.get("agent_role")
            _require(source_role is None or isinstance(source_role, str) and bool(source_role.strip()),
                     f"child rollout {child_id} has an invalid native role")
            if dispatch["role"] is not None and source_role is not None:
                _require(dispatch["role"] == source_role,
                         f"child rollout {child_id} role disagrees with spawn call")
            elif dispatch["role"] is None and source_role is not None:
                dispatch["role"] = source_role
                dispatch["role_source"] = "session_meta"
            turn_ids = set(_validate_terminal(parsed[child_id], child_id))
            native_metadata = _turn_metadata(parsed[child_id], child_id, turn_ids, cwd)
            native_metadata.update({"cli_version": child_meta["cli_version"],
                                    "model_provider": child_meta["model_provider"], "cwd": cwd})
            children.append({
                "thread_id": child_id,
                "parent_thread_id": parent_id,
                "depth": parent_depth + 1,
                "agent_path": dispatch["agent_path"],
                "terminal": "completed",
                "tool_calls": _child_tools(parsed[child_id], child_id),
                "usage": _usage(parsed[child_id], child_id, turn_ids),
                "native_metadata": native_metadata,
            })
            seen.add(child_id)
            dispatches.append(dispatch)
            queue.append((child_id, parent_depth + 1, child_ancestors))
        deliveries = _parent_deliveries(parent_records, parent_dispatches, require_delivery)
        for dispatch in parent_dispatches:
            dispatch["delivery"] = deliveries[dispatch["child_thread_id"]]

    _require(set(parsed) == seen, "raw_by_thread contains an unreferenced native rollout")
    _require(bool(dispatches) or allow_root_only,
             "root rollout contains no trusted nested dispatch")
    for order, dispatch in enumerate(dispatches, 1):
        dispatch["order"] = order
    return {
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
