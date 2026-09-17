"""Shared deterministic grading for normalized native-evaluation observations."""

from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Any

from native_eval_catalog import _is_json_value, _unique_object
from native_eval_capture import file_accesses, file_search_results
from native_eval_catalog import _validate_file_search_check
from native_eval_git_grading import grade_final_state as _native_git_final_state
from native_eval_runner_result import grade_result as _native_runner_result
from native_eval_verification import grade_pointer as _native_verification_pointer


_OBSERVATION_FIELDS = {"completed", "error", "final_text", "activations", "tool_calls", "artifacts", "usage"}
_OBSERVATION_OPTIONAL_FIELDS = {"native_metadata"}
_TOOL_FIELDS = {"name", "input", "success"}
_TOOL_OPTIONAL_FIELDS = {"id", "parent_id", "position", "output"}
_DISPATCH_ITEM_MARKER = re.compile(r"\[\[native-eval-item:([a-z0-9][a-z0-9._-]*)\]\]")
_STABLE_ID = re.compile(r"[a-z0-9][a-z0-9._-]*")
_MAX_DISPATCH_ITEM_MARKERS = 64


def _result(status: str, checks: list[dict[str, str]]) -> dict[str, object]:
    return {"status": status, "checks": checks}


def _invalid(case: object, reason: str) -> dict[str, object]:
    checks = case.get("checks", []) if isinstance(case, dict) else []
    checks = checks if isinstance(checks, list) else []
    rows = [
        {"id": check.get("id", "<unknown>"), "verdict": "invalid", "reason": reason}
        for check in checks if isinstance(check, dict)
    ]
    if not rows:
        rows = [{"id": "<observation>", "verdict": "invalid", "reason": reason}]
    return _result("invalid", rows)


def _canonical_path(value: object) -> bool:
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and value == path.as_posix() and all(part not in {"", ".", ".."} for part in path.parts)


def _validate_tool_call(call: object) -> str | None:
    if not isinstance(call, dict) or not _TOOL_FIELDS <= set(call) or not set(call) <= _TOOL_FIELDS | _TOOL_OPTIONAL_FIELDS:
        return "observation contains a malformed tool call"
    if not isinstance(call["name"], str) or not call["name"].strip() or type(call["success"]) is not bool:
        return "observation contains invalid tool call fields"
    if not _is_json_value(call["input"]):
        return "observation contains a non-JSON tool input"
    if "output" in call and not _is_json_value(call["output"]):
        return "observation contains a non-JSON tool output"
    if "id" in call and (not isinstance(call["id"], str) or not call["id"].strip()):
        return "observation contains an invalid tool call id"
    if "parent_id" in call and call["parent_id"] is not None and (
        not isinstance(call["parent_id"], str) or not call["parent_id"].strip()
    ):
        return "observation contains an invalid tool call parent_id"
    if "position" in call and (type(call["position"]) is not int or call["position"] < 0):
        return "observation contains an invalid tool call position"
    return None


def _validate_observation_shape(observation: object) -> str | None:
    if not isinstance(observation, dict) or not _OBSERVATION_FIELDS <= set(observation) \
            or not set(observation) <= _OBSERVATION_FIELDS | _OBSERVATION_OPTIONAL_FIELDS:
        return "observation does not match the normalized evidence shape"
    if type(observation["completed"]) is not bool:
        return "observation completed must be boolean"
    error = observation["error"]
    if error is not None and (not isinstance(error, str) or not error.strip()):
        return "observation error must be null or nonempty text"
    if not isinstance(observation["final_text"], str):
        return "observation final_text must be text"
    activations = observation["activations"]
    if not isinstance(activations, list) or not all(isinstance(item, str) and bool(item.strip()) for item in activations):
        return "observation activations must be a list of canonical names"
    if not isinstance(observation["tool_calls"], list):
        return "observation tool_calls must be a list"
    artifacts = observation["artifacts"]
    if not isinstance(artifacts, dict) or not all(_canonical_path(path) and isinstance(text, str) for path, text in artifacts.items()):
        return "observation artifacts must map canonical relative paths to text"
    if not isinstance(observation["usage"], dict) or not _is_json_value(observation["usage"]):
        return "observation usage must be a JSON object"
    if "native_metadata" in observation and (
        not isinstance(observation["native_metadata"], dict)
        or not _is_json_value(observation["native_metadata"])
    ):
        return "observation native_metadata must be a JSON object"
    return None


def _validate_observation(observation: object) -> str | None:
    malformed = _validate_observation_shape(observation)
    if malformed is not None:
        return malformed
    if observation["completed"] is not True:
        return "native observation is incomplete"
    if observation["error"] is not None:
        return "native observation contains an execution error"
    for call in observation["tool_calls"]:
        malformed = _validate_tool_call(call)
        if malformed is not None:
            return malformed
    return None


def _validate_semantic_verdicts(case: dict[str, Any], verdicts: object) -> str | None:
    semantic_ids = {check["id"] for check in case["checks"] if check.get("type") == "semantic"}
    if verdicts is None:
        return None
    if not isinstance(verdicts, dict) or set(verdicts) != semantic_ids:
        return "semantic verdict ids must exactly match semantic checks"
    for check_id, verdict in verdicts.items():
        if not isinstance(verdict, dict) or set(verdict) != {"passed", "evidence"}:
            return f"semantic verdict {check_id} is malformed"
        if type(verdict["passed"]) is not bool:
            return f"semantic verdict {check_id} passed must be an actual boolean"
        evidence = verdict["evidence"]
        if not isinstance(evidence, list) or not evidence or not all(isinstance(item, str) and bool(item.strip()) for item in evidence):
            return f"semantic verdict {check_id} requires nonempty evidence references"
    return None


def _check_row(check: dict[str, Any], verdict: str, reason: str) -> dict[str, str]:
    return {"id": check["id"], "verdict": verdict, "reason": reason}


def _selection(check: dict[str, Any], observation: dict[str, Any]) -> tuple[str, str]:
    actual = observation["activations"]
    if len(actual) != len(set(actual)):
        return "fail", "an activation was reported more than once"
    expected = set(check["expected"])
    declared = expected | set(check["allowed_extra"])
    missing = expected - set(actual)
    undeclared = set(actual) - declared
    if missing or undeclared:
        return "fail", f"selection mismatch: missing={sorted(missing)}, undeclared={sorted(undeclared)}"
    return "pass", "all required activations occurred and no undeclared activation occurred"


def _text(check: dict[str, Any], observation: dict[str, Any]) -> tuple[str, str]:
    source = check["source"]
    if source == "final_text":
        text = observation["final_text"]
    elif source not in observation["artifacts"]:
        return "fail", f"required text artifact is missing: {source}"
    else:
        text = observation["artifacts"][source]
    try:
        matched = re.search(check["pattern"], text) is not None
    except re.error as exc:
        return "invalid", f"catalog text pattern is invalid: {exc}"
    return ("pass", "text matched the declared pattern") if matched else ("fail", "text did not match the declared pattern")


def _file_exists(check: dict[str, Any], observation: dict[str, Any]) -> tuple[str, str]:
    actual = check["path"] in observation["artifacts"]
    expected = check["exists"]
    if type(expected) is not bool:
        return "invalid", "catalog file existence expectation is not boolean"
    return ("pass", "artifact presence matched") if actual is expected else ("fail", "artifact presence did not match")


def _strict_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_strict_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(_strict_equal(a, b) for a, b in zip(left, right))
    return left == right


def _strict_json(text: str) -> object:
    return json.loads(
        text,
        object_pairs_hook=_unique_object,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"invalid constant {token}")
        ),
    )


def _json_field(check: dict[str, Any], observation: dict[str, Any]) -> tuple[str, str]:
    path = check["path"]
    if path not in observation["artifacts"]:
        return "fail", f"required JSON artifact is missing: {path}"
    try:
        value = _strict_json(observation["artifacts"][path])
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        return "fail", f"artifact is not strict JSON: {exc}"
    try:
        for part in check["field_path"]:
            if type(part) is int:
                if not isinstance(value, list):
                    raise KeyError(part)
                value = value[part]
            else:
                if not isinstance(value, dict):
                    raise KeyError(part)
                value = value[part]
    except (KeyError, IndexError, TypeError):
        return "fail", "declared JSON field is absent"
    if _strict_equal(value, check["expected"]):
        return "pass", "JSON field matched with strict type equality"
    if any(_strict_equal(value, alternative) for alternative in check.get("alternatives", [])):
        return "pass", "JSON field matched an explicitly accepted value with strict type equality"
    return "fail", "JSON field value or type did not match"


def _response_json_field(
    check: dict[str, Any], observation: dict[str, Any], host: str | None,
) -> tuple[str, str]:
    if host not in {"claude", "codex"}:
        return "invalid", "response JSON field requires a trusted subject host"
    field_path = check.get("field_path")
    expected_by_host = check.get("expected_by_host")
    if not isinstance(field_path, list) or not field_path \
            or not all(
                isinstance(part, str) and bool(part)
                or type(part) is int and part >= 0
                for part in field_path
            ) \
            or not isinstance(expected_by_host, dict) \
            or set(expected_by_host) != {"claude", "codex"} \
            or not all(_is_json_value(value) for value in expected_by_host.values()):
        return "invalid", "catalog response JSON field check is malformed"
    try:
        value = _strict_json(observation["final_text"])
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        return "fail", f"final response is not strict JSON: {exc}"
    try:
        for part in field_path:
            if type(part) is int:
                if not isinstance(value, list):
                    raise KeyError(part)
                value = value[part]
            else:
                if not isinstance(value, dict):
                    raise KeyError(part)
                value = value[part]
    except (KeyError, IndexError, TypeError):
        return "fail", "declared response JSON field is absent"
    if _strict_equal(value, expected_by_host[host]):
        return "pass", "response JSON field matched the trusted host expectation with strict type equality"
    return "fail", "response JSON field value or type did not match the trusted host expectation"


def _input_text(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _tool_used(check: dict[str, Any], observation: dict[str, Any]) -> tuple[str, str]:
    include_failed = check.get("include_failed", False)
    if type(include_failed) is not bool:
        return "invalid", "catalog tool include_failed must be boolean"
    matches = [
        call for call in observation["tool_calls"]
        if call["name"] == check["name"] and (include_failed or call["success"] is True)
    ]
    if "input_regex" in check:
        try:
            matches = [call for call in matches if re.search(check["input_regex"], _input_text(call["input"])) is not None]
        except re.error as exc:
            return "invalid", f"catalog tool input pattern is invalid: {exc}"
    count = len(matches)
    if type(check.get("min")) is not int or type(check.get("max")) is not int:
        return "invalid", "catalog tool count bounds are malformed"
    description = "tool calls" if include_failed else "successful tool calls"
    if check["min"] <= count <= check["max"]:
        return "pass", f"observed {count} matching {description}"
    return "fail", f"observed {count} matching {description} outside declared bounds"


def _tool_order(check: dict[str, Any], observation: dict[str, Any]) -> tuple[str, str]:
    calls = [call["name"] for call in observation["tool_calls"] if call["success"] is True]
    before = [index for index, name in enumerate(calls) if name == check["before"]]
    after = [index for index, name in enumerate(calls) if name == check["after"]]
    if before and after and min(before) < max(after):
        return "pass", "successful tool calls occurred in the declared order"
    return "fail", "successful tool calls did not occur in the declared order"


def _causal_source_matches(metadata: dict[str, Any], record: dict[str, Any],
                           *, completion: bool) -> bool:
    call_id = record["call_id"]
    if record.get("authority") == "claude-tool-result":
        source = metadata.get("claude_tool_results")
        if not isinstance(source, list):
            return False
        matches = [item for item in source if isinstance(item, dict)
                   and item.get("tool_call_index") == record["tool_call_index"]
                   and item.get("id") == call_id]
        return len(matches) == 1 and completion and (
            matches[0].get("tool_result_position") == record["completion_index"]
            and matches[0].get("output_sha256") == record["content_sha256"]
            and matches[0].get("output_bytes") == record["content_bytes"]
        )
    if record.get("authority") == "codex-parent-delivery":
        supplement = metadata.get("nested_rollout")
        dispatches = supplement.get("dispatches") if isinstance(supplement, dict) else None
        if not isinstance(dispatches, list):
            return False
        matches = [item.get("delivery") for item in dispatches if isinstance(item, dict)
                   and item.get("id") == call_id]
        return len(matches) == 1 and isinstance(matches[0], dict) and completion and (
            matches[0].get("native_event_index") == record["completion_index"]
            and matches[0].get("turn_id") == record["native_turn"]
            and matches[0].get("sha256") == record["content_sha256"]
            and matches[0].get("bytes") == record["content_bytes"]
        )
    if completion:
        return False
    merge = metadata.get("nested_merge")
    events = merge.get("events") if isinstance(merge, dict) else None
    if not isinstance(events, list):
        return record.get("native_stream") == "claude-main" \
            and record.get("native_turn") is None \
            and record.get("native_event_index") is not None
    matches = [event for event in events if isinstance(event, dict)
               and event.get("id") == call_id]
    return len(matches) == 1 and (
        matches[0].get("thread_id") == record["native_stream"]
        and matches[0].get("turn_id") == record["native_turn"]
        and matches[0].get("native_event_index") == record["native_event_index"]
    )


def _returned_content(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_returned_content(item) for item in value)
    if isinstance(value, dict):
        return value.get("type") == "text" and _returned_content(value.get("text"))
    return False


def _native_change_paths(call: dict[str, Any], metadata: dict[str, Any]) -> list[str] | None:
    name = call.get("name")
    if name not in {"Write", "Edit", "file_change"}:
        return []
    inputs = call.get("input")
    if not isinstance(inputs, dict):
        return None
    if name in {"Write", "Edit"}:
        values = [inputs.get("file_path")]
    else:
        changes = inputs.get("changes")
        if not isinstance(changes, list) or not changes:
            return None
        values = [item.get("path") if isinstance(item, dict) else None for item in changes]
    cwd = metadata.get("cwd")
    paths = []
    for value in values:
        if not isinstance(value, str) or not value or "\\" in value:
            return None
        candidate = PurePosixPath(value)
        if candidate.is_absolute():
            if not isinstance(cwd, str) or not PurePosixPath(cwd).is_absolute():
                return None
            try:
                candidate = candidate.relative_to(PurePosixPath(cwd))
            except ValueError:
                return None
        rendered = candidate.as_posix()
        if not _canonical_path(rendered):
            return None
        paths.append(rendered)
    if len(paths) != len(set(paths)):
        return None
    return paths


def _subagent_returns_before_parent_file_change(
    check: dict[str, Any], observation: dict[str, Any],
) -> tuple[str, str]:
    path = check.get("path")
    if not _canonical_path(path):
        return "invalid", "catalog subagent return-order path is malformed"
    metadata = observation.get("native_metadata")
    receipt = metadata.get("subagent_return_order") if isinstance(metadata, dict) else None
    if not isinstance(receipt, dict) or receipt.get("schema") != "native-subagent-return-order/v1" \
            or receipt.get("scope") != "direct-root-only" \
            or set(receipt) != {"schema", "scope", "returns", "parent_file_changes"}:
        return "invalid", "native subagent return-order evidence is missing or malformed"
    returns, changes = receipt.get("returns"), receipt.get("parent_file_changes")
    if not isinstance(returns, list) or not all(isinstance(item, dict) for item in returns) \
            or not isinstance(changes, list) or not all(isinstance(item, dict) for item in changes):
        return "invalid", "native subagent return-order evidence lists are malformed"
    calls = observation["tool_calls"]
    direct = [index for index, call in enumerate(calls)
              if call["name"] == "subagent" and call.get("parent_id") is None]
    if not direct:
        return "fail", "no direct-root native subagent was observed"
    return_fields = {"tool_call_index", "call_id", "authority", "native_stream", "native_turn",
                     "completion_index", "content_sha256", "content_bytes", "content_nonempty"}
    change_fields = {"tool_call_index", "call_id", "native_stream", "native_turn",
                     "native_event_index", "paths"}
    return_indexes = [item.get("tool_call_index") for item in returns]
    change_indexes = [item.get("tool_call_index") for item in changes]
    structured = [index for index, call in enumerate(calls)
                  if call["name"] in {"Write", "Edit", "file_change"}
                  and call.get("parent_id") is None]
    if set(return_indexes) != set(direct) or len(return_indexes) != len(set(return_indexes)) \
            or set(change_indexes) != set(structured) or len(change_indexes) != len(set(change_indexes)):
        return "invalid", "native causal evidence does not cover exact direct-root calls"
    for item in returns:
        index = item.get("tool_call_index")
        call = calls[index] if type(index) is int and 0 <= index < len(calls) else None
        if set(item) != return_fields or not isinstance(call, dict) \
                or item.get("call_id") != call.get("id") \
                or not isinstance(item.get("native_stream"), str) or not item["native_stream"] \
                or type(item.get("completion_index")) is not int or item["completion_index"] < 0 \
                or not isinstance(item.get("content_sha256"), str) \
                or len(item["content_sha256"]) != 64 \
                or type(item.get("content_bytes")) is not int or item["content_bytes"] < 0 \
                or type(item.get("content_nonempty")) is not bool \
                or not _causal_source_matches(metadata, item, completion=True):
            return "invalid", "native subagent completion evidence is inconsistent"
        if item["authority"] == "claude-tool-result":
            try:
                encoded = json.dumps(call.get("output"), ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode("utf-8")
            except (TypeError, ValueError, UnicodeError):
                return "invalid", "Claude subagent result is not strict JSON"
            if hashlib.sha256(encoded).hexdigest() != item["content_sha256"] \
                    or len(encoded) != item["content_bytes"]:
                return "invalid", "Claude subagent result content hash is inconsistent"
            if item["content_nonempty"] != _returned_content(call.get("output")):
                return "invalid", "Claude subagent result nonempty evidence is inconsistent"
    for item in changes:
        index = item.get("tool_call_index")
        call = calls[index] if type(index) is int and 0 <= index < len(calls) else None
        paths = item.get("paths")
        actual_paths = _native_change_paths(call, metadata) if isinstance(call, dict) else None
        if set(item) != change_fields or not isinstance(call, dict) \
                or item.get("call_id") != call.get("id") \
                or not isinstance(item.get("native_stream"), str) or not item["native_stream"] \
                or type(item.get("native_event_index")) is not int or item["native_event_index"] < 0 \
                or not isinstance(paths, list) or not paths \
                or any(not _canonical_path(value) for value in paths) or len(paths) != len(set(paths)) \
                or actual_paths != paths \
                or not _causal_source_matches(metadata, item, completion=False):
            return "invalid", "native parent file-change evidence is inconsistent"
        if item["native_stream"] == "claude-main" \
                and item["native_event_index"] != call.get("position"):
            return "invalid", "Claude parent file-change index is inconsistent"
    if any(not calls[index]["success"] for index in direct):
        return "fail", "a direct-root native subagent did not complete successfully"
    if any(not item["content_nonempty"] for item in returns):
        return "invalid", "a direct-root native subagent lacks a supported nonempty result"
    matching = [item for item in changes if path in item["paths"] and calls[item["tool_call_index"]]["success"]]
    if not matching:
        return "fail", f"no direct-root structured file change affected {path}"
    for returned in returns:
        same_turn = [item for item in matching
                     if item["native_stream"] == returned["native_stream"]
                     and item["native_turn"] == returned["native_turn"]]
        if not same_turn:
            return "invalid", "subagent return and parent action are not in one native turn"
        first = min(item["native_event_index"] for item in same_turn)
        if returned["completion_index"] >= first:
            return "fail", "a parent file change preceded a direct-root subagent return"
    return "pass", "all direct-root native subagent returns preceded the parent file change"


def _subagent_role(call: dict[str, Any]) -> tuple[str | None, str | None]:
    inputs = call.get("input")
    if not isinstance(inputs, dict):
        return None, "native subagent input is malformed"
    fields = [key for key in ("subagent_type", "role", "agent_type") if key in inputs]
    if len(fields) != 1:
        return None, "native subagent role evidence is missing or ambiguous"
    role = inputs[fields[0]]
    if not isinstance(role, str) or not role.strip():
        return None, "native subagent role evidence is malformed"
    return role, None


def _role_name(value: str) -> str:
    return value.removeprefix("speckit-pro:")


def _dispatch_message_proof(value: object) -> dict[str, object]:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    markers = _DISPATCH_ITEM_MARKER.findall(value) if isinstance(value, str) else []
    return {
        "observed_item_ids": markers[:_MAX_DISPATCH_ITEM_MARKERS],
        "observed_marker_count": len(markers),
        "markers_truncated": len(markers) > _MAX_DISPATCH_ITEM_MARKERS,
        "message_sha256": hashlib.sha256(encoded).hexdigest(),
        "message_bytes": len(encoded),
    }


def _codex_dispatch_message_proof(
    call: dict[str, Any], metadata: dict[str, Any],
) -> dict[str, object] | None:
    supplement = metadata.get("nested_rollout")
    dispatches = supplement.get("dispatches") if isinstance(supplement, dict) else None
    if not isinstance(dispatches, list) or not all(isinstance(item, dict) for item in dispatches):
        return None
    matches = [item for item in dispatches if item.get("id") == call.get("id")]
    if len(matches) > 1:
        return None
    if not matches:
        inputs = call.get("input")
        return _dispatch_message_proof(inputs.get("message") if isinstance(inputs, dict) else None)
    dispatch = matches[0]
    proof = dispatch.get("item_attribution")
    if not isinstance(proof, dict) or set(proof) != {
        "task_input", "observed_item_ids", "observed_marker_count", "markers_truncated",
    }:
        return None
    opaque = proof.get("task_input") if isinstance(proof, dict) else None
    markers = proof.get("observed_item_ids") if isinstance(proof, dict) else None
    count = proof.get("observed_marker_count") if isinstance(proof, dict) else None
    truncated = proof.get("markers_truncated") if isinstance(proof, dict) else None
    if not isinstance(opaque, dict) or set(opaque) != {"kind", "sha256", "bytes"} \
            or opaque.get("kind") != "opaque" or opaque != dispatch.get("task_input") \
            or not isinstance(opaque.get("sha256"), str) \
            or re.fullmatch(r"[a-f0-9]{64}", opaque["sha256"]) is None \
            or type(opaque.get("bytes")) is not int or opaque["bytes"] < 0 \
            or not isinstance(markers, list) \
            or any(not isinstance(item, str) or _STABLE_ID.fullmatch(item) is None for item in markers) \
            or type(count) is not int or count < 0 or type(truncated) is not bool \
            or len(markers) != min(count, _MAX_DISPATCH_ITEM_MARKERS) \
            or truncated is not (count > _MAX_DISPATCH_ITEM_MARKERS):
        return None
    return {
        "observed_item_ids": markers, "observed_marker_count": count,
        "markers_truncated": truncated, "message_sha256": opaque["sha256"],
        "message_bytes": opaque["bytes"],
    }


def _dispatch_attributions(
    observation: dict[str, Any], host: str,
) -> tuple[dict[int, dict[str, Any]] | None, str | None]:
    metadata = observation.get("native_metadata")
    receipt = metadata.get("native_subagent_dispatch_attribution") \
        if isinstance(metadata, dict) else None
    if not isinstance(receipt, dict) or set(receipt) != {"schema", "authority", "calls"} \
            or receipt.get("schema") != "native-subagent-dispatch-attribution/v1" \
            or receipt.get("authority") != "controller-bound-native-trace" \
            or not isinstance(receipt.get("calls"), list):
        return None, "native subagent dispatch attribution receipt is missing or malformed"
    entries = receipt["calls"]
    calls = observation["tool_calls"]
    subagent_indexes = [index for index, call in enumerate(calls) if call["name"] == "subagent"]
    by_index: dict[int, dict[str, Any]] = {}
    fields = {
        "tool_call_index", "call_id", "observed_item_ids", "observed_marker_count",
        "markers_truncated", "message_sha256", "message_bytes",
    }
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != fields:
            return None, "native subagent dispatch attribution entry is malformed"
        index = entry.get("tool_call_index")
        if type(index) is not int or index in by_index or index not in subagent_indexes:
            return None, "native subagent dispatch attribution indexes are inconsistent"
        call = calls[index]
        markers = entry.get("observed_item_ids")
        count = entry.get("observed_marker_count")
        truncated = entry.get("markers_truncated")
        if entry.get("call_id") != call.get("id") \
                or not isinstance(markers, list) \
                or any(not isinstance(item, str) or _STABLE_ID.fullmatch(item) is None for item in markers) \
                or type(count) is not int or count < 0 or type(truncated) is not bool \
                or len(markers) != min(count, _MAX_DISPATCH_ITEM_MARKERS) \
                or truncated is not (count > _MAX_DISPATCH_ITEM_MARKERS) \
                or not isinstance(entry.get("message_sha256"), str) \
                or re.fullmatch(r"[a-f0-9]{64}", entry["message_sha256"]) is None \
                or type(entry.get("message_bytes")) is not int or entry["message_bytes"] < 0:
            return None, "native subagent dispatch attribution entry is inconsistent"
        if host == "claude":
            inputs = call.get("input")
            expected = _dispatch_message_proof(
                inputs.get("prompt") if isinstance(inputs, dict) else None
            )
        else:
            expected = _codex_dispatch_message_proof(call, metadata)
        if expected is None or any(entry[key] != value for key, value in expected.items()):
            return None, "native subagent dispatch attribution conflicts with native evidence"
        by_index[index] = entry
    if set(by_index) != set(subagent_indexes):
        return None, "native subagent dispatch attribution omitted a dispatch"
    return by_index, None


def _dispatch_returns(
    observation: dict[str, Any], host: str,
) -> str | None:
    calls = observation["tool_calls"]
    required = {
        index for index, call in enumerate(calls)
        if call["name"] == "subagent" and call.get("parent_id") is None
        and call.get("success") is True
    }
    metadata = observation.get("native_metadata")
    receipt = metadata.get("subagent_return_order") if isinstance(metadata, dict) else None
    if not isinstance(receipt, dict) or set(receipt) != {
        "schema", "scope", "returns", "parent_file_changes",
    } or receipt.get("schema") != "native-subagent-return-order/v1" \
            or receipt.get("scope") != "direct-root-only" \
            or not isinstance(receipt.get("returns"), list) \
            or not isinstance(receipt.get("parent_file_changes"), list):
        return "native subagent return receipt is missing or malformed"
    returns = receipt["returns"]
    by_index = {item.get("tool_call_index"): item for item in returns if isinstance(item, dict)}
    if len(by_index) != len(returns) or set(by_index) != required:
        return "native subagent return receipt does not exactly bind successful root dispatches"
    codex_dispatches = None
    if host == "codex":
        supplement = metadata.get("nested_rollout")
        codex_dispatches = supplement.get("dispatches") if isinstance(supplement, dict) else None
        if not isinstance(codex_dispatches, list):
            return "Codex native subagent return evidence is missing"
    fields = {
        "tool_call_index", "call_id", "authority", "native_stream", "native_turn",
        "completion_index", "content_sha256", "content_bytes", "content_nonempty",
    }
    for index in sorted(required):
        item, call = by_index[index], calls[index]
        if set(item) != fields or item.get("call_id") != call.get("id") \
                or item.get("content_nonempty") is not True \
                or type(item.get("content_bytes")) is not int or item["content_bytes"] <= 0 \
                or not isinstance(item.get("content_sha256"), str) \
                or re.fullmatch(r"[a-f0-9]{64}", item["content_sha256"]) is None \
                or type(item.get("completion_index")) is not int or item["completion_index"] < 0:
            return "native subagent return receipt entry is malformed"
        if not _causal_source_matches(metadata, item, completion=True):
            return "native subagent return receipt conflicts with its retained source"
        if host == "claude":
            encoded = json.dumps(call.get("output"), sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False, allow_nan=False).encode("utf-8")
            if item.get("authority") != "claude-tool-result" \
                    or item.get("native_stream") != "claude-main" \
                    or item.get("content_sha256") != hashlib.sha256(encoded).hexdigest() \
                    or item.get("content_bytes") != len(encoded):
                return "Claude subagent return receipt conflicts with its tool result"
        else:
            matches = [dispatch for dispatch in codex_dispatches
                       if isinstance(dispatch, dict) and dispatch.get("id") == call.get("id")]
            delivery = matches[0].get("delivery") if len(matches) == 1 else None
            if not isinstance(delivery, dict) \
                    or item.get("authority") != "codex-parent-delivery" \
                    or item.get("native_stream") != metadata["nested_rollout"].get("root_thread_id") \
                    or item.get("native_turn") != delivery.get("turn_id") \
                    or item.get("completion_index") != delivery.get("native_event_index") \
                    or item.get("content_sha256") != delivery.get("sha256") \
                    or item.get("content_bytes") != delivery.get("bytes"):
                return "Codex subagent return receipt conflicts with native parent delivery"
    return None


def _native_subagent_dispatch(
    check: dict[str, Any], observation: dict[str, Any], host: str | None,
) -> tuple[str, str]:
    if host not in {"claude", "codex"}:
        return "invalid", "native subagent dispatch requires a trusted subject host"
    expected = check.get("expected")
    forbidden = check.get("forbidden_roles")
    if not isinstance(expected, list) or not expected or not isinstance(forbidden, list):
        return "invalid", "catalog native subagent dispatch is malformed"
    expected_pairs = []
    for item in expected:
        if not isinstance(item, dict) or set(item) != {"item_id", "role"} \
                or any(not isinstance(item[key], str) or _STABLE_ID.fullmatch(item[key]) is None
                       for key in ("item_id", "role")):
            return "invalid", "catalog native subagent dispatch is malformed"
        expected_pairs.append((item["item_id"], item["role"]))
    if len(expected_pairs) != len(set(expected_pairs)) \
            or any(not isinstance(role, str) or _STABLE_ID.fullmatch(role) is None for role in forbidden) \
            or len(forbidden) != len(set(forbidden)) \
            or not set(forbidden).isdisjoint(role for _item, role in expected_pairs):
        return "invalid", "catalog native subagent dispatch is malformed"
    attributions, error = _dispatch_attributions(observation, host)
    if error is not None:
        return "invalid", error
    return_error = _dispatch_returns(observation, host)
    if return_error is not None:
        return "invalid", return_error
    actual_pairs = []
    problems = []
    forbidden_set = set(forbidden)
    for index, call in enumerate(observation["tool_calls"]):
        if call["name"] != "subagent":
            continue
        role, role_error = _subagent_role(call)
        if role_error is not None:
            return "invalid", role_error
        role = _role_name(role)
        proof = attributions[index]
        markers = proof["observed_item_ids"]
        if proof["markers_truncated"] or proof["observed_marker_count"] != 1:
            problems.append(f"dispatch {index} did not contain exactly one item marker")
        else:
            actual_pairs.append((markers[0], role))
        if role in forbidden_set:
            problems.append(f"dispatch {index} attempted forbidden role {role}")
        if call.get("parent_id") is not None:
            problems.append(f"dispatch {index} was nested instead of parent-owned")
        if call.get("success") is not True:
            problems.append(f"dispatch {index} did not complete successfully")
    if sorted(actual_pairs) != sorted(expected_pairs):
        problems.append(
            f"dispatch pairs mismatch: expected={sorted(expected_pairs)}, actual={sorted(actual_pairs)}"
        )
    if problems:
        return "fail", "; ".join(problems)
    return "pass", "exact parent-owned native dispatches completed and returned for every item-role pair"


def _native_plan_repair_context(
    check: dict[str, Any], observation: dict[str, Any], host: str | None,
) -> tuple[str, str]:
    if host not in {"claude", "codex"}:
        return "invalid", "native Plan-repair context requires a trusted subject host"
    contexts = check.get("contexts")
    request_path = check.get("g3_request_path")
    role = check.get("executor_role")
    maximum = check.get("max_repairs")
    terminal = check.get("terminal_outcome")
    if not isinstance(contexts, dict) or not contexts \
            or any(_STABLE_ID.fullmatch(key) is None or not _canonical_path(path)
                   for key, path in contexts.items()
                   if isinstance(key, str) and isinstance(path, str)) \
            or not all(isinstance(key, str) and isinstance(path, str)
                       for key, path in contexts.items()) \
            or not _canonical_path(request_path) \
            or not isinstance(role, str) or _STABLE_ID.fullmatch(role) is None \
            or type(maximum) is not int or maximum != 2 \
            or terminal not in {"pass", "unresolved"}:
        return "invalid", "catalog native Plan-repair context check is malformed"
    metadata = observation.get("native_metadata")
    receipt = metadata.get("native_plan_repair_context") if isinstance(metadata, dict) else None
    if not isinstance(receipt, dict) or set(receipt) != {"schema", "authority", "checks"} \
            or receipt.get("schema") != "native-plan-repair-context/v1" \
            or receipt.get("authority") != "controller-bound-retained-native-evidence" \
            or not isinstance(receipt.get("checks"), list):
        return "invalid", "native Plan-repair context receipt is missing or malformed"
    matches = [item for item in receipt["checks"] if isinstance(item, dict)
               and item.get("check_id") == check.get("id")]
    if len(matches) != 1 or set(matches[0]) != {"check_id", "commands", "dispatches"}:
        return "invalid", "native Plan-repair context receipt does not bind its check"
    commands, dispatches = matches[0]["commands"], matches[0]["dispatches"]
    if not isinstance(commands, list) or not isinstance(dispatches, list):
        return "invalid", "native Plan-repair context receipt entries are malformed"
    calls = observation["tool_calls"]
    command_fields = {
        "tool_call_index", "call_id", "started", "completed",
        "response_sha256", "response_bytes", "passed",
    }
    dispatch_fields = {
        "tool_call_index", "call_id", "role", "started", "returned",
        "preceding_g3_call_id", "rerun_g3_call_id", "context_proof",
        "opaque_task_input", "return_bound",
    }
    seen_calls: set[str] = set()
    for item in commands:
        if not isinstance(item, dict) or set(item) != command_fields:
            return "invalid", "native Plan-repair command receipt is malformed"
        index, call_id = item["tool_call_index"], item["call_id"]
        expected_name = "Bash" if host == "claude" else "command_execution"
        if type(index) is not int or not (0 <= index < len(calls)) \
                or call_id != calls[index].get("id") or calls[index].get("name") != expected_name \
                or calls[index].get("parent_id") is not None \
                or not isinstance(call_id, str) or call_id in seen_calls \
                or type(item["started"]) is not int or type(item["completed"]) is not int \
                or item["started"] > item["completed"] \
                or not isinstance(item["response_sha256"], str) \
                or re.fullmatch(r"[a-f0-9]{64}", item["response_sha256"]) is None \
                or type(item["response_bytes"]) is not int or item["response_bytes"] <= 0 \
                or type(item["passed"]) is not bool:
            return "invalid", "native Plan-repair command receipt conflicts with native calls"
        seen_calls.add(call_id)
    direct = [index for index, call in enumerate(calls)
              if call.get("name") == "subagent" and call.get("parent_id") is None]
    if len(dispatches) != len(direct):
        return "fail", "Plan-repair dispatch count does not match root native dispatches"
    expected_context_ids = sorted(contexts)
    for item in dispatches:
        if not isinstance(item, dict) or set(item) != dispatch_fields:
            return "invalid", "native Plan-repair dispatch receipt is malformed"
        index, call_id, proof = item["tool_call_index"], item["call_id"], item["context_proof"]
        if type(index) is not int or index not in direct or call_id != calls[index].get("id") \
                or type(item["started"]) is not int or type(item["returned"]) is not int \
                or item["started"] > item["returned"] \
                or not isinstance(proof, dict) or set(proof) != {
                    "message_sha256", "message_bytes", "observed_context_ids",
                    "complete_preceding_json_found",
                } or not isinstance(proof.get("message_sha256"), str) \
                or re.fullmatch(r"[a-f0-9]{64}", proof["message_sha256"]) is None \
                or type(proof.get("message_bytes")) is not int or proof["message_bytes"] < 0 \
                or not isinstance(proof.get("observed_context_ids"), list) \
                or type(proof.get("complete_preceding_json_found")) is not bool:
            return "invalid", "native Plan-repair dispatch receipt conflicts with native calls"
    return_error = _dispatch_returns(observation, host)
    if return_error is not None:
        return "invalid", return_error
    if not 1 <= len(dispatches) <= maximum or len(commands) != len(dispatches) + 1:
        return "fail", "Plan-repair did not perform one initial G3 run and one rerun per completed repair"
    if commands[0]["passed"] is not False:
        return "fail", "Plan-repair did not begin from an actual failed G3 result"
    if any(command["passed"] is True for command in commands[:-1]):
        return "fail", "Plan-repair continued after G3 had already passed"
    expected_terminal = terminal == "pass"
    if commands[-1]["passed"] is not expected_terminal:
        return "fail", f"Plan-repair terminal G3 outcome did not remain {terminal}"
    for index, dispatch in enumerate(dispatches):
        previous, rerun = commands[index], commands[index + 1]
        proof = dispatch["context_proof"]
        actual_role = dispatch["role"]
        if host == "claude" and isinstance(actual_role, str):
            actual_role = _role_name(actual_role)
        if actual_role != role or dispatch["return_bound"] is not True \
                or calls[dispatch["tool_call_index"]].get("success") is not True:
            return "fail", "Plan-repair used the wrong executor or lacked a completed native return"
        if proof["observed_context_ids"] != expected_context_ids \
                or proof["complete_preceding_json_found"] is not True:
            return "fail", "Plan-repair executor dispatch omitted trusted context or the complete preceding G3 result"
        if dispatch["preceding_g3_call_id"] != previous["call_id"] \
                or dispatch["rerun_g3_call_id"] != rerun["call_id"] \
                or not (previous["completed"] < dispatch["started"]
                        <= dispatch["returned"] < rerun["started"]):
            return "fail", "Plan-repair G3, dispatch, return, and rerun order is not causal"
    return "pass", "every completed Plan repair received exact trusted context and its immediately preceding G3 result before one authoritative rerun"


def _synthesis_source_paths(case: dict[str, Any]) -> list[str] | None:
    paths = [
        check.get("path") for check in case.get("checks", [])
        if isinstance(check, dict) and check.get("type") == "file_access"
    ]
    if not paths or any(not _canonical_path(path) for path in paths) or len(paths) != len(set(paths)):
        return None
    return paths


def _source_reads_precede(
    case: dict[str, Any], observation: dict[str, Any], action_index: int, native_name: str,
) -> tuple[str, str] | None:
    paths = _synthesis_source_paths(case)
    if paths is None:
        return "invalid", "catalog synthesis source-read checks are missing or malformed"
    accesses = file_accesses(observation)
    for path in paths:
        matches = [
            item for item in accesses
            if item.get("path") == path
            and type(item.get("tool_call_index")) is int
            and item["tool_call_index"] < action_index
            and observation["tool_calls"][item["tool_call_index"]].get("name") == native_name
            and observation["tool_calls"][item["tool_call_index"]].get("parent_id") is None
        ]
        if not matches:
            return "fail", f"no parent-owned exact read of {path} preceded native synthesis"
    return None


def _synthesis_dispatches(observation: dict[str, Any]) -> tuple[list[int], str | None]:
    synthesizers: list[int] = []
    for index, call in enumerate(observation["tool_calls"]):
        if call["name"] != "subagent":
            continue
        role, error = _subagent_role(call)
        if error is not None:
            return [], error
        if _role_name(role) == "consensus-synthesizer":
            synthesizers.append(index)
    return synthesizers, None


def _claude_synthesis_mechanism(
    path: str, observation: dict[str, Any], case: dict[str, Any], synthesizers: list[int],
) -> tuple[str, str]:
    if len(synthesizers) > 1:
        return "invalid", "Claude synthesis dispatch evidence is duplicated or ambiguous"
    if not synthesizers:
        return "fail", "Claude must complete exactly one consensus-synthesizer subagent"
    synthesis_index = synthesizers[0]
    synthesis_call = observation["tool_calls"][synthesis_index]
    if synthesis_call.get("parent_id") is not None:
        return "invalid", "Claude consensus-synthesizer is not a supported direct-root dispatch"
    if synthesis_call["success"] is not True:
        return "fail", "Claude consensus-synthesizer did not complete successfully"
    reads = _source_reads_precede(case, observation, synthesis_index, "Read")
    if reads is not None:
        return reads
    causal = _subagent_returns_before_parent_file_change({"path": path}, observation)
    if causal[0] != "pass":
        return causal
    metadata = observation.get("native_metadata")
    receipt = metadata.get("subagent_return_order") if isinstance(metadata, dict) else None
    returns = receipt.get("returns") if isinstance(receipt, dict) else None
    matching = [item for item in returns if isinstance(item, dict)
                and item.get("tool_call_index") == synthesis_index] if isinstance(returns, list) else []
    if len(matching) != 1 or matching[0].get("authority") != "claude-tool-result":
        return "invalid", "Claude synthesizer completion is not bound to a native tool result"
    return "pass", "Claude synthesizer returned before the parent wrote the declared artifact"


def _codex_synthesis_mechanism(
    path: str, observation: dict[str, Any], case: dict[str, Any], synthesizers: list[int],
) -> tuple[str, str]:
    if synthesizers:
        return "fail", "Codex parent-session synthesis must not dispatch a consensus-synthesizer child"
    matching_changes: list[int] = []
    for index, call in enumerate(observation["tool_calls"]):
        if call["name"] != "file_change":
            continue
        paths = _native_change_paths(call, observation.get("native_metadata", {}))
        if paths is None:
            return "invalid", "Codex structured file-change evidence is malformed"
        if path in paths and call.get("parent_id") is None and call["success"] is True:
            matching_changes.append(index)
    if len(matching_changes) > 1:
        return "invalid", "Codex parent-session artifact changes are duplicated or ambiguous"
    if not matching_changes:
        return "fail", "Codex parent session must complete exactly one structured change to the declared artifact"
    reads = _source_reads_precede(case, observation, matching_changes[0], "command_execution")
    if reads is not None:
        return reads
    return "pass", "Codex parent session read the declared sources before writing the declared artifact"


def _native_synthesis_mechanism(
    check: dict[str, Any], observation: dict[str, Any], case: dict[str, Any], host: str | None,
) -> tuple[str, str]:
    path = check.get("artifact_path")
    expected = {
        "claude": {"mode": "dedicated_subagent", "role": "speckit-pro:consensus-synthesizer"},
        "codex": {"mode": "parent_session", "role": None},
    }
    if not _canonical_path(path) or check.get("per_host") != expected:
        return "invalid", "catalog native synthesis mechanism is malformed"
    if host not in expected:
        return "invalid", "native synthesis mechanism requires a trusted subject host"
    synthesizers, error = _synthesis_dispatches(observation)
    if error is not None:
        return "invalid", error
    if host == "claude":
        return _claude_synthesis_mechanism(path, observation, case, synthesizers)
    return _codex_synthesis_mechanism(path, observation, case, synthesizers)


def _file_access(check: dict[str, Any], observation: dict[str, Any]) -> tuple[str, str]:
    if check.get("operation") != "read_file" or not _canonical_path(check.get("path")):
        return "invalid", "catalog file access check is malformed"
    matched = any(
        access["operation"] == "read_file" and access["path"] == check["path"]
        for access in file_accesses(observation)
    )
    if matched:
        return "pass", f"observed a successful exact-path unbounded read operation for {check['path']}"
    return "fail", f"no supported successful exact-path unbounded read operation for {check['path']} was observed"


def _file_search(check: dict[str, Any], observation: dict[str, Any], host: str) -> tuple[str, str]:
    try:
        _validate_file_search_check(check, "direct-grade", str(check.get("id")))
    except (ValueError, TypeError):
        return "invalid", "catalog file search check is malformed"
    matched = any(
        row["pattern"] == check["pattern"] and row["paths"] == sorted(check["matches"])
        for row in file_search_results(observation, host=host)
    )
    if matched:
        return "pass", "observed the complete recursive search and exact expected matches"
    return "fail", "no supported complete recursive search established the expected matches"


def _grade_check(
    check: dict[str, Any],
    observation: dict[str, Any],
    semantic_verdicts: dict[str, Any] | None,
    case: dict[str, Any],
    host: str | None,
) -> dict[str, str]:
    graders = {
        "selection": _selection,
        "text": _text,
        "file_exists": _file_exists,
        "json_field": _json_field,
        "tool_used": _tool_used,
        "tool_order": _tool_order,
        "subagent_returns_before_parent_file_change": _subagent_returns_before_parent_file_change,
        "file_access": _file_access,
        "native_git_final_state": _native_git_final_state,
        "native_verification_pointer": _native_verification_pointer,
        "native_runner_result": _native_runner_result,
    }
    check_type = check.get("type")
    if check_type == "file_search":
        verdict, reason = _file_search(check, observation, host)
        return _check_row(check, verdict, reason)
    if check_type == "semantic":
        if semantic_verdicts is None:
            return _check_row(check, "needs_judge", "semantic check has no reviewed verdict")
        verdict = semantic_verdicts[check["id"]]
        if verdict["passed"]:
            return _check_row(check, "pass", f"semantic verdict passed with evidence: {', '.join(verdict['evidence'])}")
        return _check_row(check, "fail", f"semantic verdict failed with evidence: {', '.join(verdict['evidence'])}")
    if check_type == "response_json_field":
        try:
            verdict, reason = _response_json_field(check, observation, host)
        except (KeyError, TypeError, ValueError) as exc:
            verdict, reason = "invalid", f"catalog check is malformed: {exc}"
        return _check_row(check, verdict, reason)
    if check_type == "native_synthesis_mechanism":
        try:
            verdict, reason = _native_synthesis_mechanism(check, observation, case, host)
        except (KeyError, TypeError, ValueError) as exc:
            verdict, reason = "invalid", f"catalog check is malformed: {exc}"
        return _check_row(check, verdict, reason)
    if check_type == "native_subagent_dispatch":
        try:
            verdict, reason = _native_subagent_dispatch(check, observation, host)
        except (KeyError, TypeError, ValueError) as exc:
            verdict, reason = "invalid", f"catalog check is malformed: {exc}"
        return _check_row(check, verdict, reason)
    if check_type == "native_plan_repair_context":
        try:
            verdict, reason = _native_plan_repair_context(check, observation, host)
        except (KeyError, TypeError, ValueError) as exc:
            verdict, reason = "invalid", f"catalog check is malformed: {exc}"
        return _check_row(check, verdict, reason)
    grader = graders.get(check_type)
    if grader is None:
        return _check_row(check, "invalid", "catalog check type is unknown")
    try:
        verdict, reason = grader(check, observation)
    except (KeyError, TypeError, ValueError) as exc:
        verdict, reason = "invalid", f"catalog check is malformed: {exc}"
    return _check_row(check, verdict, reason)


def grade_observation(
    case: dict[str, Any],
    observation: dict[str, Any],
    semantic_verdicts: dict[str, Any] | None = None,
    *,
    host: str | None = None,
) -> dict[str, object]:
    """Grade one normalized observation without launching or comparing providers."""
    if not isinstance(case, dict) or not isinstance(case.get("checks"), list) or not case["checks"]:
        return _invalid(case, "case has no gradeable checks")
    requirements = case.get("requirements")
    if not isinstance(requirements, list) or not requirements or any(
        not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]
        for item in requirements
    ):
        return _invalid(case, "case requirements are malformed")
    requirement_ids = {item["id"] for item in requirements}
    if len(requirement_ids) != len(requirements) or any(
        not isinstance(check, dict)
        or not isinstance(check.get("id"), str) or not check["id"]
        or not isinstance(check.get("requirement"), str)
        or check.get("requirement") not in requirement_ids
        for check in case["checks"]
    ):
        return _invalid(case, "case requirements or check references are malformed")
    if len({check["id"] for check in case["checks"]}) != len(case["checks"]) \
            or {check["requirement"] for check in case["checks"]} != requirement_ids:
        return _invalid(case, "case has duplicate checks or uncovered requirements")
    if any(check.get("type") in {
        "native_synthesis_mechanism", "native_subagent_dispatch",
        "native_plan_repair_context", "response_json_field", "file_search",
    }
           for check in case["checks"]) \
            and host not in {"claude", "codex"}:
        return _invalid(case, "native host-specific grading requires a trusted subject host")
    observation_error = _validate_observation(observation)
    if observation_error is not None:
        return _invalid(case, observation_error)
    verdict_error = _validate_semantic_verdicts(case, semantic_verdicts)
    if verdict_error is not None:
        return _invalid(case, verdict_error)
    rows = [_grade_check(check, observation, semantic_verdicts, case, host) for check in case["checks"]]
    verdicts = {row["verdict"] for row in rows}
    if "invalid" in verdicts:
        status = "invalid"
    elif "fail" in verdicts:
        status = "fail"
    elif "needs_judge" in verdicts:
        status = "needs_judge"
    else:
        status = "pass"
    return _result(status, rows)


__all__ = ("grade_observation",)
