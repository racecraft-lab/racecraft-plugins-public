"""Controller-bound native runner request/result grading contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Any, Mapping


CHECK_FIELDS = frozenset({
    "request_path", "helper_id", "operation", "mode", "expected_status",
    "expected_exit_code", "stdout_field_path", "expected_stdout_value",
    "response_field_path",
})
RECEIPT_SCHEMA = "native-eval-controller-runner-result/v1"
RECEIPT_AUTHORITY = "controller-bound-retained-native-evidence"
_STABLE_ID = re.compile(r"[a-z0-9][a-z0-9._-]*")
_STATUS_EXIT = {
    "ok": 0,
    "expected_failure": 1,
    "input_error": 2,
    "missing_prerequisite": 3,
    "subprocess_failure": 4,
    "internal_failure": 5,
}


class RunnerResultError(ValueError):
    """Raised when native runner evidence cannot be authenticated."""


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise RunnerResultError(message)


def _path(value: object, label: str) -> str:
    _need(isinstance(value, str) and bool(value) and "\\" not in value,
          f"{label} is malformed")
    path = PurePosixPath(value)
    _need(not path.is_absolute() and path.as_posix() == value
          and all(part not in {"", ".", ".."} for part in path.parts),
          f"{label} is malformed")
    return value


def _field_path(value: object, label: str) -> list[str]:
    _need(isinstance(value, list) and 1 <= len(value) <= 16
          and all(isinstance(part, str) and bool(part) for part in value),
          f"{label} is malformed")
    return value


def _json_value(value: object, label: str) -> None:
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise RunnerResultError(f"{label} is not a JSON value") from exc


def validate_check(check: Mapping[str, object], label: str) -> None:
    """Validate one deterministic native runner result check."""

    _path(check.get("request_path"), f"{label} request_path")
    for field in ("helper_id", "operation"):
        value = check.get(field)
        _need(isinstance(value, str) and _STABLE_ID.fullmatch(value) is not None,
              f"{label} {field} is malformed")
    _need(check.get("mode") == "read_only", f"{label} mode must be read_only")
    status = check.get("expected_status")
    exit_code = check.get("expected_exit_code")
    _need(isinstance(status, str) and status in _STATUS_EXIT,
          f"{label} expected_status is malformed")
    _need(type(exit_code) is int and exit_code == _STATUS_EXIT[status],
          f"{label} expected_exit_code contradicts expected_status")
    _field_path(check.get("stdout_field_path"), f"{label} stdout_field_path")
    _field_path(check.get("response_field_path"), f"{label} response_field_path")
    _json_value(check.get("expected_stdout_value"), f"{label} expected_stdout_value")


def runner_checks(case: Mapping[str, object]) -> list[Mapping[str, object]]:
    checks = case.get("checks")
    if not isinstance(checks, list):
        raise RunnerResultError("native case checks are malformed")
    return [check for check in checks if isinstance(check, Mapping)
            and check.get("type") == "native_runner_result"]


def request_paths(case: Mapping[str, object]) -> tuple[str, ...]:
    result = []
    for check in runner_checks(case):
        validate_check(check, "native_runner_result check")
        path = str(check["request_path"])
        if path not in result:
            result.append(path)
    return tuple(result)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RunnerResultError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _loads(value: str | bytes, label: str) -> Any:
    try:
        return json.loads(
            value, object_pairs_hook=_unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                RunnerResultError(f"invalid JSON constant: {token}")),
        )
    except (UnicodeError, json.JSONDecodeError, RunnerResultError, RecursionError) as exc:
        raise RunnerResultError(f"{label} is malformed JSON") from exc


def _strict_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _strict_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _strict_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def _output_text(output: object) -> str:
    if isinstance(output, str):
        return output
    _need(isinstance(output, list) and all(
        isinstance(item, Mapping) and item.get("type") == "text"
        and isinstance(item.get("text"), str) for item in output
    ), "native runner output is malformed")
    return "".join(str(item["text"]) for item in output)


def _json_stream(output: object, label: str) -> list[object]:
    text = _output_text(output)
    decoder = json.JSONDecoder(
        object_pairs_hook=_unique_object,
        parse_constant=lambda token: (_ for _ in ()).throw(
            RunnerResultError(f"invalid JSON constant: {token}")),
    )
    values: list[object] = []
    position = 0
    try:
        while position < len(text):
            while position < len(text) and text[position].isspace():
                position += 1
            if position == len(text):
                break
            value, position = decoder.raw_decode(text, position)
            values.append(value)
    except (json.JSONDecodeError, RunnerResultError, RecursionError) as exc:
        raise RunnerResultError(f"{label} is truncated or malformed") from exc
    return values


def _request(request_bytes: bytes, check: Mapping[str, object]) -> dict[str, Any]:
    _need(isinstance(request_bytes, bytes) and bool(request_bytes),
          "controller-staged runner request bytes are missing")
    request = _loads(request_bytes, "controller-staged runner request")
    fields = {"schema_version", "request_id", "helper_id", "operation", "mode", "inputs"}
    _need(isinstance(request, dict) and set(request) == fields
          and request.get("schema_version") == "1.0"
          and isinstance(request.get("request_id"), str) and bool(request["request_id"])
          and isinstance(request.get("inputs"), dict),
          "controller-staged runner request has the wrong schema")
    for field in ("helper_id", "operation", "mode"):
        _need(request.get(field) == check.get(field),
              f"controller-staged runner request {field} contradicts its check")
    return request


def _capture(value: object, label: str) -> Mapping[str, object]:
    fields = {"text", "byte_count", "limit_bytes", "truncated"}
    _need(isinstance(value, Mapping) and set(value) == fields
          and isinstance(value.get("text"), str)
          and type(value.get("byte_count")) is int and value["byte_count"] >= 0
          and type(value.get("limit_bytes")) is int and value["limit_bytes"] > 0
          and type(value.get("truncated")) is bool,
          f"native runner {label} capture is malformed")
    encoded = value["text"].encode("utf-8", errors="strict")
    _need(value["truncated"] is False and value["byte_count"] == len(encoded)
          and value["byte_count"] <= value["limit_bytes"],
          f"native runner {label} capture is incomplete")
    return value


def parse_runner_response(output: object, request: Mapping[str, object]) -> dict[str, Any]:
    """Parse one complete native runner response bound to one staged request."""

    values = _json_stream(output, "native runner output")
    _need(len(values) == 1 and isinstance(values[0], dict),
          "native runner response is missing or ambiguous")
    response = values[0]
    fields = {
        "schema_version", "status", "exit_code", "legacy_exit_code",
        "diagnostics", "data", "request_id",
    }
    status = response.get("status")
    _need(set(response) == fields and response.get("schema_version") == "1.0"
          and isinstance(status, str) and status in _STATUS_EXIT
          and type(response.get("exit_code")) is int
          and response["exit_code"] == _STATUS_EXIT[status]
          and response.get("legacy_exit_code") is None
          and isinstance(response.get("diagnostics"), list)
          and isinstance(response.get("data"), dict)
          and response.get("request_id") == request.get("request_id"),
          "native runner response has the wrong schema")
    data = response["data"]
    required = {
        "helper_id", "operation", "mode", "executed_in_process", "stdin_mode",
        "stdin_request", "shell", "exit_code", "stdout", "stderr", "timed_out",
        "writes_state", "stdout_json",
    }
    _need(required <= set(data)
          and data.get("helper_id") == request.get("helper_id")
          and data.get("operation") == request.get("operation")
          and data.get("mode") == request.get("mode")
          and data.get("executed_in_process") is True
          and data.get("stdin_mode") == "single_json_request"
          and data.get("shell") is False
          and type(data.get("exit_code")) is int
          and data["exit_code"] == response["exit_code"]
          and data.get("timed_out") is False
          and data.get("writes_state") is False,
          "native runner result data is malformed")
    expected_stdin = {key: value for key, value in request.items() if key != "request_id"}
    _need(_strict_equal(data.get("stdin_request"), expected_stdin),
          "native runner response did not consume the staged request")
    stdout = _capture(data["stdout"], "stdout")
    _capture(data["stderr"], "stderr")
    stdout_json = _loads(stdout["text"], "native runner stdout")
    _need(_strict_equal(stdout_json, data.get("stdout_json")),
          "native runner stdout_json contradicts captured stdout")
    encoded = _canonical_bytes(response)
    return {
        "response": response,
        "response_sha256": hashlib.sha256(encoded).hexdigest(),
        "response_bytes": len(encoded),
        "status": status,
        "exit_code": response["exit_code"],
        "stdout_json": stdout_json,
    }


def bind_result(
    check: Mapping[str, object], invocation: Mapping[str, object], request_bytes: bytes,
) -> dict[str, Any]:
    """Bind one authenticated root command to staged request bytes and its response."""

    validate_check(check, "native_runner_result check")
    _need(invocation.get("authority") == "protected-native-runner",
          "native runner command authority is missing")
    call_id = invocation.get("call_id")
    call_index = invocation.get("tool_call_index")
    success = invocation.get("success")
    native_exit = invocation.get("native_exit_code")
    _need(isinstance(call_id, str) and bool(call_id)
          and type(call_index) is int and call_index >= 0
          and type(success) is bool
          and (native_exit is None or type(native_exit) is int),
          "native runner command identity is malformed")
    _need(invocation.get("request_path") == check.get("request_path"),
          "native runner command used the wrong request path")
    request = _request(request_bytes, check)
    parsed = parse_runner_response(invocation.get("output"), request)
    if native_exit is None:
        _need(success is (parsed["exit_code"] == 0),
              "native runner success state contradicts its response")
    else:
        _need(native_exit == parsed["exit_code"]
              and success is (native_exit == 0),
              "native runner exit evidence contradicts its response")
    try:
        request_raw_text = request_bytes.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise RunnerResultError("controller-staged runner request is not UTF-8") from exc
    canonical_request = _canonical_bytes(request)
    request_sha = hashlib.sha256(request_bytes).hexdigest()
    return {
        "check_id": check.get("id"),
        "call": {
            "id": call_id, "tool_call_index": call_index,
            "success": success, "native_exit_code": native_exit,
        },
        "actual": {
            "request_path": check["request_path"],
            "request_sha256": request_sha, "request_bytes": len(request_bytes),
            "request_raw_text": request_raw_text,
            "request_canonical_sha256": hashlib.sha256(canonical_request).hexdigest(),
            "request_canonical_bytes": len(canonical_request),
            "request": request,
            "response_sha256": parsed["response_sha256"],
            "response_bytes": parsed["response_bytes"],
            "response": parsed["response"],
            "status": parsed["status"], "exit_code": parsed["exit_code"],
            "stdout_json": parsed["stdout_json"],
        },
    }


def attach_receipt(observation: dict[str, Any], rows: list[Mapping[str, object]]) -> None:
    metadata = observation.get("native_metadata")
    _need(isinstance(metadata, dict) and "controller_runner_results" not in metadata,
          "native runner observation metadata is malformed")
    metadata["controller_runner_results"] = {
        "schema": RECEIPT_SCHEMA, "authority": RECEIPT_AUTHORITY,
        "checks": [dict(row) for row in rows],
    }


def _lookup(value: object, path: object, label: str) -> object:
    parts = _field_path(path, label)
    current = value
    for part in parts:
        _need(isinstance(current, Mapping) and part in current,
              f"{label} was not present")
        current = current[part]
    return current


def _receipt_request(
    actual: Mapping[str, object], check: Mapping[str, object],
) -> dict[str, Any]:
    request_raw = actual["request_raw_text"].encode("utf-8", errors="strict")
    _need(len(request_raw) == actual["request_bytes"]
          and hashlib.sha256(request_raw).hexdigest() == actual["request_sha256"],
          "controller runner raw request evidence changed")
    request = _request(request_raw, check)
    _need(_strict_equal(request, actual["request"]),
          "controller runner request projection changed")
    request_canonical = _canonical_bytes(request)
    _need(len(request_canonical) == actual["request_canonical_bytes"]
          and hashlib.sha256(request_canonical).hexdigest()
          == actual["request_canonical_sha256"],
          "controller runner canonical request evidence changed")
    return request


def _receipt_row(check: Mapping[str, object], observation: Mapping[str, object]) -> Mapping[str, object]:
    metadata = observation.get("native_metadata")
    receipt = metadata.get("controller_runner_results") if isinstance(metadata, Mapping) else None
    _need(isinstance(receipt, Mapping) and set(receipt) == {"schema", "authority", "checks"}
          and receipt.get("schema") == RECEIPT_SCHEMA
          and receipt.get("authority") == RECEIPT_AUTHORITY
          and isinstance(receipt.get("checks"), list),
          "controller runner result evidence is missing or malformed")
    rows = receipt["checks"]
    matches = [row for row in rows if isinstance(row, Mapping)
               and row.get("check_id") == check.get("id")]
    _need(len(matches) == 1, "controller runner result evidence is missing or ambiguous")
    row = matches[0]
    _need(set(row) == {"check_id", "call", "actual"}
          and isinstance(row.get("call"), Mapping)
          and isinstance(row.get("actual"), Mapping),
          "controller runner result evidence is malformed")
    call, actual = row["call"], row["actual"]
    _need(set(call) == {"id", "tool_call_index", "success", "native_exit_code"}
          and isinstance(call.get("id"), str) and bool(call["id"])
          and type(call.get("tool_call_index")) is int and call["tool_call_index"] >= 0
          and type(call.get("success")) is bool
          and (call.get("native_exit_code") is None
               or type(call["native_exit_code"]) is int),
          "controller runner command evidence is malformed")
    fields = {
        "request_path", "request_sha256", "request_bytes", "request_raw_text",
        "request_canonical_sha256", "request_canonical_bytes", "request",
        "response_sha256", "response_bytes", "response", "status", "exit_code",
        "stdout_json",
    }
    _need(set(actual) == fields and _path(actual.get("request_path"), "runner request path")
          and isinstance(actual.get("request_sha256"), str)
          and re.fullmatch(r"[a-f0-9]{64}", actual["request_sha256"]) is not None
          and type(actual.get("request_bytes")) is int and actual["request_bytes"] > 0
          and isinstance(actual.get("request_raw_text"), str)
          and isinstance(actual.get("request_canonical_sha256"), str)
          and re.fullmatch(r"[a-f0-9]{64}", actual["request_canonical_sha256"])
          is not None
          and type(actual.get("request_canonical_bytes")) is int
          and actual["request_canonical_bytes"] > 0
          and isinstance(actual.get("response_sha256"), str)
          and re.fullmatch(r"[a-f0-9]{64}", actual["response_sha256"]) is not None
          and type(actual.get("response_bytes")) is int and actual["response_bytes"] > 0
          and isinstance(actual.get("request"), Mapping)
          and isinstance(actual.get("response"), Mapping)
          and isinstance(actual.get("status"), str)
          and type(actual.get("exit_code")) is int,
          "controller runner result evidence is malformed")
    encoded = _canonical_bytes(actual["response"])
    _need(len(encoded) == actual["response_bytes"]
          and hashlib.sha256(encoded).hexdigest() == actual["response_sha256"],
          "controller runner response evidence changed")
    request = _receipt_request(actual, check)
    parsed = parse_runner_response(encoded.decode("utf-8"), request)
    _need(parsed["status"] == actual["status"]
          and parsed["exit_code"] == actual["exit_code"]
          and _strict_equal(parsed["stdout_json"], actual["stdout_json"]),
          "controller runner result projection changed")
    native_exit = call["native_exit_code"]
    _need((native_exit is None or native_exit == actual["exit_code"])
          and call["success"] is (actual["exit_code"] == 0),
          "controller runner command result changed")
    return row


def grade_result(
    check: Mapping[str, object], observation: Mapping[str, object],
) -> tuple[str, str]:
    """Grade the expected outcome and exact subject report against controller evidence."""

    try:
        validate_check(check, "native_runner_result check")
        row = _receipt_row(check, observation)
    except (RunnerResultError, TypeError, ValueError) as exc:
        return "invalid", str(exc)
    actual = row["actual"]
    mismatches = []
    for field, expected in (
        ("status", check["expected_status"]),
        ("exit_code", check["expected_exit_code"]),
        ("request_path", check["request_path"]),
    ):
        if not _strict_equal(actual[field], expected):
            mismatches.append(field)
    try:
        stdout_value = _lookup(
            actual["stdout_json"], check["stdout_field_path"], "runner stdout field",
        )
        if not _strict_equal(stdout_value, check["expected_stdout_value"]):
            mismatches.append("stdout outcome")
    except RunnerResultError:
        mismatches.append("stdout outcome")
    try:
        final_values = _json_stream(observation.get("final_text"), "subject final response")
        _need(len(final_values) == 1 and isinstance(final_values[0], Mapping),
              "subject final response is not one JSON object")
        reported = _lookup(
            final_values[0], check["response_field_path"], "reported runner response",
        )
        if not _strict_equal(reported, actual["response"]):
            mismatches.append("reported response binding")
    except RunnerResultError:
        mismatches.append("reported response binding")
    if mismatches:
        return "fail", "native runner result differed at: " + ", ".join(mismatches)
    return "pass", "reported response matched the controller-bound native runner result"


__all__ = (
    "CHECK_FIELDS", "RunnerResultError", "attach_receipt", "bind_result",
    "grade_result", "parse_runner_response", "request_paths", "runner_checks",
    "validate_check",
)
