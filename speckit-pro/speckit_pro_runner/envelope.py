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
ALLOWED_FIELDS = set(REQUIRED_FIELDS) | {"request_id"}
SUPPORTED_RUNNER_OPERATIONS = {"preflight", "runtime-info"}


@dataclass(frozen=True)
class RunnerRequest:
    request_id: str | None
    helper_id: str
    operation: str
    mode: str
    inputs: dict[str, Any]


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

    extra = sorted(set(parsed) - ALLOWED_FIELDS)
    helper_id = parsed.get("helper_id")
    operation = parsed.get("operation")
    mode = parsed.get("mode")
    inputs = parsed.get("inputs")
    invalid = (
        extra
        or not isinstance(helper_id, str)
        or helper_id == ""
        or not isinstance(operation, str)
        or operation == ""
        or (helper_id == "runner" and operation not in SUPPORTED_RUNNER_OPERATIONS)
        or mode != "read_only"
        or not isinstance(inputs, dict)
        or ("request_id" in parsed and not isinstance(parsed.get("request_id"), str))
    )
    if invalid:
        details: dict[str, Any] = {}
        if extra:
            details["unexpected_fields"] = extra
        if helper_id == "runner" and operation not in SUPPORTED_RUNNER_OPERATIONS:
            details["operation"] = operation
        if mode != "read_only":
            details["mode"] = mode
        return None, input_error("invalid_envelope", "request envelope has unsupported field values", details=details)

    return RunnerRequest(
        request_id=parsed.get("request_id"),
        helper_id=helper_id,
        operation=operation,
        mode=mode,
        inputs=inputs,
    ), None


def emit_response(body: dict[str, Any]) -> int:
    for diag in body.get("diagnostics", []):
        print(json.dumps(diag, sort_keys=True, separators=(",", ":")), file=sys.stderr)
    print(json.dumps(body, sort_keys=True, separators=(",", ":")))
    return int(body["exit_code"])
