"""Runner request/response envelope primitives."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any

from . import CONTRACT_VERSION

STATUS_EXIT_CODES = {
    "ok": 0,
    "expected_failure": 1,
    "input_error": 2,
    "missing_prerequisite": 3,
    "subprocess_failure": 4,
    "internal_failure": 5,
}

REQUIRED_FIELDS = ("schema_version", "helper_id", "operation", "mode", "inputs")
ALLOWED_FIELDS = set(REQUIRED_FIELDS) | {"request_id", "answer_format"}
COMPACT_ANSWER_LIMIT_BYTES = 16 * 1024
ANSWER_FORMATS = ("compact", "detailed")
SUPPORTED_RUNNER_OPERATIONS = {"preflight", "runtime-info"}
SUPPORTED_HELPER_MODES = {"read_only", "dry_run", "apply"}


@dataclass(frozen=True)
class RunnerRequest:
    request_id: str | None
    helper_id: str
    operation: str
    mode: str
    inputs: dict[str, Any]
    answer_format: str = "detailed"


def remediation(summary: str, actions: list[str], deferred_to: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"summary": summary, "actions": actions[:3]}
    if deferred_to:
        value["deferred_to"] = deferred_to
    return value


def diagnostic(
    code: str,
    message: str,
    *,
    severity: str = "error",
    details: dict[str, Any] | None = None,
    remediation_summary: str | None = None,
    remediation_actions: list[str] | None = None,
    deferred_to: str | None = None,
) -> dict[str, Any]:
    diag: dict[str, Any] = {
        "severity": severity,
        "source": "runner",
        "code": code,
        "message": message[:240],
        "remediation": remediation(
            remediation_summary or "Resolve the reported runner prerequisite or request issue.",
            remediation_actions or ["Inspect the diagnostic code and retry with a corrected request."],
            deferred_to,
        ),
    }
    if details:
        diag["details"] = details
    return diag


def is_diagnostic(value: Any) -> bool:
    return isinstance(value, dict) and value.get("source") == "runner" and "code" in value


def response(
    status: str,
    *,
    request_id: str | None = None,
    data: dict[str, Any] | None = None,
    diagnostics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": CONTRACT_VERSION,
        "status": status,
        "exit_code": STATUS_EXIT_CODES[status],
        "legacy_exit_code": None,
        "diagnostics": diagnostics or [],
        "data": data or {},
    }
    if request_id:
        body["request_id"] = request_id
    return body


def input_error(code: str, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
    diag = diagnostic(
        code,
        message,
        details=details,
        remediation_summary="Send a valid SpecKit runner request envelope.",
        remediation_actions=[
            "Use schema_version 1.0, a known helper_id, mode read_only, and an object inputs field.",
            "Retry with a supported runner or read-only helper operation.",
        ],
    )
    return response("input_error", diagnostics=[diag])


def invalid_request_fields(parsed: dict[str, Any]) -> list[str]:
    fields = set(parsed) - ALLOWED_FIELDS
    if parsed.get("answer_format", "detailed") not in ANSWER_FORMATS:
        fields.add("answer_format")
    return sorted(fields)


def compact_decision_data(data: dict[str, Any]) -> dict[str, Any]:
    """Keep decision fields, omitting only replay metadata and duplicate stdout."""
    omitted = {"argv", "stdin_request", "authoritative_command", "invocation_contract"}
    if data.get("stdout_json") is not None:
        omitted.add("stdout")
    result = {key: value for key, value in data.items() if key not in omitted}
    if isinstance(result.get("result"), dict):
        result["result"] = compact_decision_data(result["result"])
    return result


def answer_next_action(body: dict[str, Any]) -> str:
    data = body.get("data", {})
    for payload in (body, data, data.get("stdout_json", {})):
        if isinstance(payload, dict):
            for field in ("next_action", "action"):
                action = payload.get(field)
                if isinstance(action, str) and action.strip():
                    return action
    for diag in body.get("diagnostics", []):
        actions = diag.get("remediation", {}).get("actions", [])
        if actions and isinstance(actions[0], str):
            return actions[0]
    return ("Use the returned decision and dispatch inputs." if body["status"] == "ok"
            else "Stop and resolve the returned diagnostic before continuing.")


def answer_response(request: Any, body: dict[str, Any], *, limit_bytes: int = COMPACT_ANSWER_LIMIT_BYTES) -> dict[str, Any]:
    """One capped root interface for every helper, including gates and mutations."""
    if getattr(request, "answer_format", "detailed") != "compact":
        return body
    answer = {**body, "data": compact_decision_data(body.get("data", {})),
              "next_action": answer_next_action(body)}
    # emit_response writes the JSON plus one newline and repeats diagnostics on stderr.
    records = [answer, *answer.get("diagnostics", [])]
    size = sum(len(json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")) + 1
               for record in records)
    if size <= limit_bytes:
        return answer
    action = "Stop; reconcile the existing helper result through phase-local work without repeating the helper."
    refused = response("internal_failure", data={"helper_status": body["status"],
                       "helper_exit_code": body["exit_code"], "answer_limit_bytes": limit_bytes},
                       diagnostics=[diagnostic("compact_answer_overflow", "helper answer exceeded the root size cap",
                                              remediation_actions=[action])])
    refused["next_action"] = action
    return refused


def parse_request(raw_stdin: str) -> tuple[RunnerRequest | None, dict[str, Any] | None]:
    try:
        parsed = json.loads(raw_stdin)
    except json.JSONDecodeError as exc:
        return None, input_error(
            "invalid_json",
            "stdin did not contain a valid JSON document",
            details={"line": exc.lineno, "column": exc.colno},
        )

    if not isinstance(parsed, dict):
        return None, input_error("invalid_envelope", "request envelope must be a JSON object")

    missing = [field for field in REQUIRED_FIELDS if field not in parsed]
    if missing:
        return None, input_error(
            "missing_required_field",
            "request envelope is missing required fields",
            details={"missing": missing},
        )

    if parsed.get("schema_version") != CONTRACT_VERSION:
        return None, input_error(
            "unsupported_schema_version",
            "request schema_version is not supported by this runner",
            details={"schema_version": parsed.get("schema_version")},
        )

    extra = invalid_request_fields(parsed)
    helper_id = parsed.get("helper_id")
    operation = parsed.get("operation")
    mode = parsed.get("mode")
    inputs = parsed.get("inputs")
    runner_request = helper_id == "runner"
    operation_is_string = isinstance(operation, str)
    mode_is_string = isinstance(mode, str)
    invalid = (
        extra
        or not isinstance(helper_id, str)
        or helper_id == ""
        or not operation_is_string
        or operation == ""
        or not mode_is_string
        or (runner_request and operation_is_string and operation not in SUPPORTED_RUNNER_OPERATIONS)
        or (runner_request and mode != "read_only")
        or ((not runner_request) and mode_is_string and mode not in SUPPORTED_HELPER_MODES)
        or not isinstance(inputs, dict)
        or ("request_id" in parsed and not isinstance(parsed.get("request_id"), str))
    )
    if invalid:
        details: dict[str, Any] = {}
        if extra:
            details["unexpected_fields"] = extra
        if runner_request and operation_is_string and operation not in SUPPORTED_RUNNER_OPERATIONS:
            details["operation"] = operation
        if runner_request and mode != "read_only":
            details["mode"] = mode
        if (not runner_request) and (not mode_is_string or mode not in SUPPORTED_HELPER_MODES):
            details["mode"] = mode
        return None, input_error("invalid_envelope", "request envelope has unsupported field values", details=details)

    return RunnerRequest(
        request_id=parsed.get("request_id"),
        helper_id=helper_id,
        operation=operation,
        mode=mode,
        inputs=inputs,
        answer_format=parsed.get("answer_format", "detailed"),
    ), None


def emit_response(body: dict[str, Any]) -> int:
    for diag in body.get("diagnostics", []):
        print(json.dumps(diag, sort_keys=True, separators=(",", ":")), file=sys.stderr)
    print(json.dumps(body, sort_keys=True, separators=(",", ":")))
    return int(body["exit_code"])
