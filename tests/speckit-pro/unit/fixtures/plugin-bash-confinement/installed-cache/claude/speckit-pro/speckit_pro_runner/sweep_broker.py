"""Python 3.11 standard-library stdio MCP server for isolated sweep agents."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from .sweep_isolation import (
    ARTIFACT_ALLOWLIST,
    BROKER_ERROR_CODES,
    BROKER_TOOL_NAMES,
    CLASS_VALUES,
    IsolationViolation,
    MAX_ANCHOR_BYTES,
    MAX_FINDING_BYTES,
    MAX_REASON_BYTES,
    MAX_REPLACEMENT_BYTES,
    PERSPECTIVES,
    ReceiptViolation,
    SchemaViolation,
    SweepSession,
)


SERVER_INFO = {"name": "speckit-pro-sweep-broker", "version": "1.0.0"}


def _broker_error_code(exc: Exception) -> str:
    message = str(exc).casefold()
    markers = (
        ("comment does not match", "comment_mismatch"),
        ("submit_result requires exactly one result object", "submit_shape"),
        ("closed vocabulary", "classifier_class"),
        ("target does not match", "classifier_target"),
        ("reason is not", "classifier_reason"),
        ("fields do not match", "schema_fields"),
        ("evidence citation", "evidence_path"),
        ("perspective does not match", "perspective_mismatch"),
        ("synthesis", "synthesis_consistency"),
    )
    for marker, code in markers:
        if marker in message:
            return code
    if isinstance(exc, ReceiptViolation):
        return "receipt_violation"
    if isinstance(exc, IsolationViolation):
        return "isolation_violation"
    return "schema_validation"


def _context(arguments: dict[str, Any]) -> tuple[SweepSession, str, str, str | None, dict[str, Any]]:
    supplied = dict(arguments)
    capability = os.environ.get("SPECKIT_SWEEP_CAPABILITY")
    if not isinstance(capability, str) or not capability:
        raise ReceiptViolation("broker process capability is required")
    state_root_value = os.environ.get("SPECKIT_SWEEP_STATE_ROOT")
    state_root = Path(state_root_value) if state_root_value else None
    session, binding = SweepSession.from_capability(capability, state_root=state_root)
    return (
        session,
        binding["comment_id"],
        binding["stage"],
        binding.get("perspective"),
        supplied,
    )


def _tool_schema(properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties or {},
        "required": required or [],
        "additionalProperties": False,
    }


RESULT_RECORD_SCHEMAS = (
    {
        "type": "object",
        "properties": {
            "comment_id": {"type": "string", "minLength": 1, "maxLength": 256},
            "class": {"type": "string", "enum": list(CLASS_VALUES)},
            "target": {
                "anyOf": [
                    {"type": "string", "enum": list(ARTIFACT_ALLOWLIST)},
                    {"type": "null"},
                ]
            },
            "reason": {
                "type": "string",
                "minLength": 1,
                "maxLength": MAX_REASON_BYTES,
                "pattern": r"^[^|\r\n]+$",
            },
        },
        "required": ["comment_id", "class", "target", "reason"],
        "additionalProperties": False,
    },
    {
        "type": "object",
        "properties": {
            "comment_id": {"type": "string", "minLength": 1, "maxLength": 256},
            "perspective": {"type": "string", "enum": list(PERSPECTIVES)},
            "finding": {"type": "string", "minLength": 1, "maxLength": MAX_FINDING_BYTES},
            "evidence": {
                "type": "array",
                "maxItems": 32,
                "items": {"type": "string", "minLength": 1, "maxLength": 1_024},
            },
            "escape_hatch": {"type": "boolean"},
        },
        "required": ["comment_id", "perspective", "finding", "evidence", "escape_hatch"],
        "additionalProperties": False,
    },
    {
        "type": "object",
        "properties": {
            "comment_id": {"type": "string", "minLength": 1, "maxLength": 256},
            "outcome": {"type": "string", "enum": ["resolved", "human_review"]},
            "agreement": {
                "anyOf": [
                    {"type": "string", "enum": ["3/3", "2/3"]},
                    {"type": "null"},
                ]
            },
            "basis": {
                "anyOf": [
                    {
                        "type": "string",
                        "enum": ["all_disagree", "escape_unresolved", "analyst_failed"],
                    },
                    {"type": "null"},
                ]
            },
            "edit": {
                "anyOf": [
                    {
                        "type": "object",
                        "properties": {
                            "file": {"type": "string", "enum": list(ARTIFACT_ALLOWLIST)},
                            "anchor": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": MAX_ANCHOR_BYTES,
                            },
                            "replacement": {
                                "type": "string",
                                "maxLength": MAX_REPLACEMENT_BYTES,
                            },
                        },
                        "required": ["file", "anchor", "replacement"],
                        "additionalProperties": False,
                    },
                    {"type": "null"},
                ]
            },
        },
        "required": ["comment_id", "outcome", "agreement", "basis", "edit"],
        "additionalProperties": False,
    },
)


TOOLS = (
    {
        "name": "snapshot_list",
        "description": "List bounded regular UTF-8 blobs in the frozen, credential-filtered Git snapshot.",
        "inputSchema": _tool_schema({"prefix": {"type": "string", "maxLength": 512}}),
    },
    {
        "name": "snapshot_read",
        "description": "Read a bounded range from one path exposed by the frozen Git snapshot.",
        "inputSchema": _tool_schema(
            {
                "path": {"type": "string", "minLength": 1, "maxLength": 1_024},
                "start_line": {"type": "integer", "minimum": 1},
                "end_line": {"type": "integer", "minimum": 1},
            },
            ["path"],
        ),
    },
    {
        "name": "snapshot_search",
        "description": "Search snapshot text using a bounded literal string, never a regex.",
        "inputSchema": _tool_schema(
            {
                "literal": {"type": "string", "minLength": 1, "maxLength": 512},
                "prefix": {"type": "string", "maxLength": 512},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 50},
            },
            ["literal"],
        ),
    },
    {
        "name": "review_comment",
        "description": "Return the configured bounded reviewer-data block inside the isolated model process.",
        "inputSchema": _tool_schema(),
    },
    {
        "name": "consensus_inputs",
        "description": "Return accepted private classifier or perspective records for the configured stage.",
        "inputSchema": _tool_schema(),
    },
    {
        "name": "submit_result",
        "description": "Validate and privately store one exact stage record; returns only an opaque receipt.",
        "inputSchema": _tool_schema({"result": {"oneOf": list(RESULT_RECORD_SCHEMAS)}}, ["result"]),
    },
)


if tuple(tool["name"] for tool in TOOLS) != BROKER_TOOL_NAMES:
    raise RuntimeError("broker tool manifest drift")


def call_tool(name: str, arguments: Any) -> Any:
    if name not in BROKER_TOOL_NAMES or not isinstance(arguments, dict):
        raise IsolationViolation("unknown broker tool or malformed arguments")
    session, comment_id, stage, perspective, supplied = _context(arguments)
    if name == "snapshot_list":
        if set(supplied) - {"prefix"}:
            raise IsolationViolation("snapshot_list received unknown fields")
        return session.snapshot().list(supplied.get("prefix", ""))
    if name == "snapshot_read":
        if set(supplied) - {"path", "start_line", "end_line"} or "path" not in supplied:
            raise IsolationViolation("snapshot_read fields are malformed")
        return session.snapshot().read(
            supplied["path"],
            start_line=supplied.get("start_line"),
            end_line=supplied.get("end_line"),
        )
    if name == "snapshot_search":
        if set(supplied) - {"literal", "prefix", "max_results"} or "literal" not in supplied:
            raise IsolationViolation("snapshot_search fields are malformed")
        return session.snapshot().search(
            supplied["literal"],
            prefix=supplied.get("prefix", ""),
            max_results=supplied.get("max_results", 50),
        )
    if name == "review_comment":
        if supplied:
            raise IsolationViolation("review_comment accepts no stage-specific fields")
        return session.review_comment(comment_id)
    if name == "consensus_inputs":
        if supplied:
            raise IsolationViolation("consensus_inputs accepts no stage-specific fields")
        return session.consensus_inputs(comment_id, stage=stage)
    if set(supplied) != {"result"}:
        raise IsolationViolation("submit_result requires exactly one result object")
    if not isinstance(supplied["result"], dict) or supplied["result"].get("comment_id") != comment_id:
        raise IsolationViolation("result comment does not match the model-call capability")
    return session.submit_result(stage, supplied["result"], perspective=perspective)


def _response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle_message(message: Any) -> dict[str, Any] | None:
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return _error(None, -32600, "invalid request")
    request_id = message.get("id")
    method = message.get("method")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        requested = message.get("params", {}).get("protocolVersion", "2024-11-05")
        return _response(
            request_id,
            {
                "protocolVersion": requested,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
            },
        )
    if method == "ping":
        return _response(request_id, {})
    if method == "tools/list":
        return _response(request_id, {"tools": list(TOOLS)})
    if method == "tools/call":
        params = message.get("params")
        if not isinstance(params, dict):
            return _error(request_id, -32602, "invalid tool parameters")
        try:
            result = call_tool(params.get("name"), params.get("arguments", {}))
        except (IsolationViolation, ReceiptViolation, SchemaViolation) as exc:
            code = _broker_error_code(exc)
            capability = os.environ.get("SPECKIT_SWEEP_CAPABILITY")
            state_root_value = os.environ.get("SPECKIT_SWEEP_STATE_ROOT")
            try:
                session, _binding = SweepSession.from_capability(
                    capability or "", state_root=Path(state_root_value) if state_root_value else None
                )
                session.record_broker_error(code)
            except (IsolationViolation, ReceiptViolation, SchemaViolation, OSError):
                pass
            return _response(
                request_id,
                {
                    "isError": True,
                    "content": [{"type": "text", "text": f"broker_error:{code}"}],
                    "structuredContent": {"error_code": code},
                },
            )
        text = result if isinstance(result, str) else json.dumps(result, sort_keys=True, separators=(",", ":"))
        return _response(request_id, {"content": [{"type": "text", "text": text}]})
    return _error(request_id, -32601, "method not found")


def main() -> int:
    if sys.version_info < (3, 11):
        print("feedback sweep broker requires Python 3.11 or newer", file=sys.stderr)
        return 2
    for raw_line in sys.stdin.buffer:
        try:
            message = json.loads(raw_line)
            reply = handle_message(message)
        except (UnicodeDecodeError, json.JSONDecodeError):
            reply = _error(None, -32700, "parse error")
        if reply is not None:
            sys.stdout.write(json.dumps(reply, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
