"""Controller-bound native verification record and emission-pointer contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Any, Callable, Mapping


CHECK_FIELDS = frozenset({"workflow_file", "command_id", "pointer_path", "reusable"})
POINTER_SCHEMA = "native-eval-verification-pointer/v1"
RECEIPT_SCHEMA = "native-eval-controller-verification/v1"
RECEIPT_AUTHORITY = "controller-bound-retained-native-evidence"
_HEX_32 = re.compile(r"[a-f0-9]{32}")
_SHA256 = re.compile(r"[a-f0-9]{64}")
_COMMAND_ID = re.compile(r"[A-Z][A-Z0-9_]*")


class VerificationError(ValueError):
    """Raised when native verification evidence cannot be authenticated."""


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def _path(value: object, label: str) -> str:
    _need(isinstance(value, str) and bool(value) and "\\" not in value,
          f"{label} is malformed")
    path = PurePosixPath(value)
    _need(not path.is_absolute() and path.as_posix() == value
          and all(part not in {"", ".", ".."} for part in path.parts),
          f"{label} is malformed")
    return value


def validate_check(check: Mapping[str, object], label: str) -> None:
    """Validate the exact catalog fields for one verification-pointer check."""

    _path(check.get("workflow_file"), f"{label} workflow_file")
    _path(check.get("pointer_path"), f"{label} pointer_path")
    command_id = check.get("command_id")
    _need(isinstance(command_id, str) and _COMMAND_ID.fullmatch(command_id) is not None,
          f"{label} command_id is malformed")
    _need(type(check.get("reusable")) is bool, f"{label} reusable must be boolean")


def verification_checks(case: Mapping[str, object]) -> list[Mapping[str, object]]:
    checks = case.get("checks")
    if not isinstance(checks, list):
        raise VerificationError("native case checks are malformed")
    return [check for check in checks if isinstance(check, Mapping)
            and check.get("type") == "native_verification_pointer"]


def pointer_artifacts(case: Mapping[str, object]) -> tuple[str, ...]:
    """Return the configured subject-emission pointers that must be captured."""

    result = []
    for check in verification_checks(case):
        validate_check(check, "native_verification_pointer check")
        path = str(check["pointer_path"])
        if path not in result:
            result.append(path)
    return tuple(result)


def record_directories(case: Mapping[str, object]) -> tuple[str, ...]:
    """Return confined dynamic record directories implied by workflow files."""

    result = []
    for check in verification_checks(case):
        validate_check(check, "native_verification_pointer check")
        directory = (PurePosixPath(str(check["workflow_file"])).parent
                     / ".process" / "verification").as_posix()
        if directory not in result:
            result.append(directory)
    return tuple(result)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise VerificationError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _loads(text: str | bytes, label: str) -> Any:
    try:
        return json.loads(
            text, object_pairs_hook=_unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                VerificationError(f"invalid JSON constant: {token}")),
        )
    except (UnicodeError, json.JSONDecodeError, VerificationError, RecursionError) as exc:
        raise VerificationError(f"{label} is malformed JSON") from exc


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


def _output_text(output: object) -> str:
    if isinstance(output, str):
        return output
    _need(isinstance(output, list) and all(
        isinstance(item, Mapping) and item.get("type") == "text"
        and isinstance(item.get("text"), str) for item in output
    ), "native verification output is malformed")
    return "".join(str(item["text"]) for item in output)


def _json_stream(output: object) -> list[object]:
    text = _output_text(output)
    decoder = json.JSONDecoder(
        object_pairs_hook=_unique_object,
        parse_constant=lambda token: (_ for _ in ()).throw(
            VerificationError(f"invalid JSON constant: {token}")),
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
    except (json.JSONDecodeError, VerificationError, RecursionError) as exc:
        raise VerificationError("native verification output is truncated or malformed") from exc
    return values


def parse_runner_result(output: object) -> dict[str, Any]:
    """Parse one genuine runner response from an already-authenticated command."""

    candidates = []
    for value in _json_stream(output):
        data = value.get("data") if isinstance(value, Mapping) else None
        if isinstance(data, Mapping) and data.get("helper_id") == "execute-verification" \
                and data.get("operation") == "execute-verification" \
                and data.get("mode") == "apply":
            candidates.append(value)
    _need(len(candidates) == 1, "native verification response is missing or ambiguous")
    response = candidates[0]
    _need(response.get("schema_version") == "1.0" and response.get("status") == "ok"
          and type(response.get("exit_code")) is int and response["exit_code"] == 0
          and response.get("diagnostics") == [],
          "native verification response did not succeed")
    data = response["data"]
    record = data.get("record")
    required_record = {
        "schema_version", "execution_id", "command_id", "workflow_file",
        "snapshot_sha256", "exit_code", "completed", "inputs_unchanged",
        "snapshot_unchanged", "isolation_mode",
    }
    _need(isinstance(record, Mapping) and required_record <= set(record),
          "native verification response record is malformed")
    execution_id = record.get("execution_id")
    workflow = _path(record.get("workflow_file"), "native verification workflow_file")
    command_id = record.get("command_id")
    snapshot = record.get("snapshot_sha256")
    isolation = record.get("isolation_mode")
    _need(isinstance(execution_id, str) and _HEX_32.fullmatch(execution_id) is not None,
          "native verification execution_id is malformed")
    _need(isinstance(command_id, str) and _COMMAND_ID.fullmatch(command_id) is not None,
          "native verification command_id is malformed")
    _need(isinstance(snapshot, str) and _SHA256.fullmatch(snapshot) is not None,
          "native verification snapshot_sha256 is malformed")
    _need(isinstance(isolation, str) and bool(isolation),
          "native verification isolation_mode is malformed")
    _need(type(record.get("exit_code")) is int and record["exit_code"] == 0
          and record.get("completed") is True and record.get("inputs_unchanged") is True
          and record.get("snapshot_unchanged") is True,
          "native verification record did not complete successfully")
    reusable = data.get("reusable")
    _need(type(reusable) is bool and type(data.get("rerun_required")) is bool,
          "native verification reuse status is malformed")
    record_path = data.get("record_path")
    expected_path = (PurePosixPath(workflow).parent / ".process" / "verification"
                     / f"{execution_id}.json").as_posix()
    _need(record_path == expected_path, "native verification record path is inconsistent")
    encoded = json.dumps(
        response, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    return {
        "response_sha256": hashlib.sha256(encoded).hexdigest(),
        "response_bytes": len(encoded), "record_path": record_path,
        "record": dict(record), "workflow_file": workflow, "command_id": command_id,
        "execution_id": execution_id, "snapshot_sha256": snapshot,
        "reusable": reusable, "isolation_mode": isolation,
    }


def bind_result(
    check: Mapping[str, object], invocation: Mapping[str, object],
    read_record: Callable[[str], bytes],
) -> dict[str, Any]:
    """Bind an authenticated native command result to its retained record bytes."""

    validate_check(check, "native_verification_pointer check")
    _need(invocation.get("authority") == "protected-native-runner"
          and invocation.get("success") is True,
          "native verification command authority is missing")
    call_id = invocation.get("call_id")
    call_index = invocation.get("tool_call_index")
    _need(isinstance(call_id, str) and bool(call_id)
          and type(call_index) is int and call_index >= 0,
          "native verification command identity is malformed")
    result = parse_runner_result(invocation.get("output"))
    record_bytes = read_record(result["record_path"])
    _need(isinstance(record_bytes, bytes) and bool(record_bytes),
          "native verification record bytes are missing")
    record = _loads(record_bytes, "native verification record")
    _need(_strict_equal(record, result["record"]),
          "native verification response is not bound to current record bytes")
    return {
        "check_id": check.get("id"),
        "call": {
            "id": call_id, "tool_call_index": call_index,
            "response_sha256": result["response_sha256"],
            "response_bytes": result["response_bytes"],
        },
        "actual": {
            "workflow_file": result["workflow_file"],
            "record_path": result["record_path"],
            "record_sha256": hashlib.sha256(record_bytes).hexdigest(),
            "record_bytes": len(record_bytes),
            "execution_id": result["execution_id"],
            "command_id": result["command_id"],
            "snapshot_sha256": result["snapshot_sha256"],
            "reusable": result["reusable"],
            "isolation_mode": result["isolation_mode"],
        },
    }


def attach_receipt(observation: dict[str, Any], rows: list[Mapping[str, object]]) -> None:
    metadata = observation.get("native_metadata")
    _need(isinstance(metadata, dict) and "controller_verification" not in metadata,
          "native verification observation metadata is malformed")
    metadata["controller_verification"] = {
        "schema": RECEIPT_SCHEMA, "authority": RECEIPT_AUTHORITY,
        "checks": [dict(row) for row in rows],
    }


def _receipt_row(check: Mapping[str, object], observation: Mapping[str, object]) -> Mapping[str, object]:
    metadata = observation.get("native_metadata")
    receipt = metadata.get("controller_verification") if isinstance(metadata, Mapping) else None
    _need(isinstance(receipt, Mapping) and set(receipt) == {"schema", "authority", "checks"}
          and receipt.get("schema") == RECEIPT_SCHEMA
          and receipt.get("authority") == RECEIPT_AUTHORITY,
          "controller verification evidence is missing or malformed")
    rows = receipt.get("checks")
    matches = [row for row in rows or [] if isinstance(row, Mapping)
               and row.get("check_id") == check.get("id")]
    _need(isinstance(rows, list) and len(matches) == 1,
          "controller verification evidence is missing or ambiguous")
    row = matches[0]
    _need(set(row) == {"check_id", "call", "actual"},
          "controller verification check evidence is malformed")
    call, actual = row.get("call"), row.get("actual")
    _need(isinstance(call, Mapping)
          and set(call) == {"id", "tool_call_index", "response_sha256", "response_bytes"}
          and isinstance(call.get("id"), str) and bool(call["id"])
          and type(call.get("tool_call_index")) is int and call["tool_call_index"] >= 0
          and isinstance(call.get("response_sha256"), str)
          and _SHA256.fullmatch(call["response_sha256"]) is not None
          and type(call.get("response_bytes")) is int and call["response_bytes"] > 0,
          "controller verification command evidence is malformed")
    fields = {
        "workflow_file", "record_path", "record_sha256", "record_bytes",
        "execution_id", "command_id", "snapshot_sha256", "reusable", "isolation_mode",
    }
    _need(isinstance(actual, Mapping) and set(actual) == fields,
          "controller verification result evidence is malformed")
    _path(actual.get("workflow_file"), "controller verification workflow_file")
    _path(actual.get("record_path"), "controller verification record_path")
    _need(isinstance(actual.get("record_sha256"), str)
          and _SHA256.fullmatch(actual["record_sha256"]) is not None
          and type(actual.get("record_bytes")) is int and actual["record_bytes"] > 0
          and isinstance(actual.get("execution_id"), str)
          and _HEX_32.fullmatch(actual["execution_id"]) is not None
          and isinstance(actual.get("command_id"), str)
          and _COMMAND_ID.fullmatch(actual["command_id"]) is not None
          and isinstance(actual.get("snapshot_sha256"), str)
          and _SHA256.fullmatch(actual["snapshot_sha256"]) is not None
          and type(actual.get("reusable")) is bool
          and isinstance(actual.get("isolation_mode"), str) and bool(actual["isolation_mode"]),
          "controller verification result evidence is malformed")
    return row


def _pointer(text: object) -> Mapping[str, object]:
    _need(isinstance(text, str), "verification pointer artifact is missing")
    value = _loads(text, "verification pointer artifact")
    fields = {
        "schema_version", "record_path", "record_sha256", "execution_id",
        "command_id", "snapshot_sha256", "reusable", "isolation_mode",
    }
    _need(isinstance(value, Mapping) and set(value) == fields
          and value.get("schema_version") == POINTER_SCHEMA,
          "verification pointer artifact has the wrong schema")
    _path(value.get("record_path"), "verification pointer record_path")
    _need(isinstance(value.get("record_sha256"), str)
          and _SHA256.fullmatch(value["record_sha256"]) is not None
          and isinstance(value.get("execution_id"), str)
          and _HEX_32.fullmatch(value["execution_id"]) is not None
          and isinstance(value.get("command_id"), str)
          and _COMMAND_ID.fullmatch(value["command_id"]) is not None
          and isinstance(value.get("snapshot_sha256"), str)
          and _SHA256.fullmatch(value["snapshot_sha256"]) is not None
          and type(value.get("reusable")) is bool
          and isinstance(value.get("isolation_mode"), str) and bool(value["isolation_mode"]),
          "verification pointer artifact fields are malformed")
    return value


def grade_pointer(
    check: Mapping[str, object], observation: Mapping[str, object],
) -> tuple[str, str]:
    """Grade a subject pointer against controller-bound native verification evidence."""

    try:
        validate_check(check, "native_verification_pointer check")
        row = _receipt_row(check, observation)
    except VerificationError as exc:
        return "invalid", str(exc)
    actual = row["actual"]
    mismatches = []
    for key in ("workflow_file", "command_id", "reusable"):
        if type(actual[key]) is not type(check[key]) or actual[key] != check[key]:
            mismatches.append(key)
    if actual["isolation_mode"] == "copy_only" and actual["reusable"] is not False:
        mismatches.append("copy_only reuse status")
    artifacts = observation.get("artifacts")
    try:
        pointer = _pointer(artifacts.get(check["pointer_path"])
                           if isinstance(artifacts, Mapping) else None)
    except VerificationError as exc:
        return "fail", str(exc)
    expected_pointer = {
        "schema_version": POINTER_SCHEMA,
        **{key: actual[key] for key in (
            "record_path", "record_sha256", "execution_id", "command_id",
            "snapshot_sha256", "reusable", "isolation_mode",
        )},
    }
    if not _strict_equal(pointer, expected_pointer):
        mismatches.append("pointer binding")
    if mismatches:
        return "fail", "native verification differed at: " + ", ".join(mismatches)
    return "pass", "emission pointer matched the controller-bound native verification record"


__all__ = (
    "CHECK_FIELDS", "VerificationError", "attach_receipt", "bind_result",
    "grade_pointer", "pointer_artifacts", "record_directories", "validate_check",
    "verification_checks",
)
