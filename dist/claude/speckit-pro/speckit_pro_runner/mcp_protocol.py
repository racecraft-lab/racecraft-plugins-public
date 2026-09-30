"""The stdio MCP loop the capability brokers share.

Each broker supplies its tools, a call handler, and an error mapper; this module
owns version negotiation, the JSON-RPC envelope, and the stdin/stdout loop, so
the three brokers cannot drift apart on framing or error shape.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

SUPPORTED_PROTOCOL_VERSIONS: tuple[str, ...] = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
# Versions are ISO dates, so the latest sorts last regardless of list order.
LATEST_PROTOCOL_VERSION = max(SUPPORTED_PROTOCOL_VERSIONS)


def negotiate_protocol_version(params: Any) -> str:
    """Echo a supported requested version, else answer with the latest one.

    The MCP lifecycle requires a server to return the requested version only
    when it supports it, and otherwise another version it supports.
    """
    requested = params.get("protocolVersion") if isinstance(params, dict) else None
    if isinstance(requested, str) and requested in SUPPORTED_PROTOCOL_VERSIONS:
        return requested
    return LATEST_PROTOCOL_VERSION


@dataclass(frozen=True)
class ToolServer:
    """One broker's tools and the two callbacks the shared loop needs.

    ``error_code`` maps a failed call to a closed broker error code. Returning
    ``None`` lets the exception propagate, for a broker that treats an
    unexpected failure as fatal rather than reportable.
    """

    server_info: Mapping[str, str]
    tools: Sequence[Mapping[str, Any]]
    call_tool: Callable[[Any, Any], Any]
    error_code: Callable[[Exception], str | None]


def _response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _tool_call(server: ToolServer, request_id: Any, params: Any) -> dict[str, Any]:
    if not isinstance(params, dict):
        return _error(request_id, -32602, "invalid tool parameters")
    try:
        result = server.call_tool(params.get("name"), params.get("arguments", {}))
    except Exception as exc:  # noqa: BLE001 - the broker's mapper decides; None re-raises
        code = server.error_code(exc)
        if code is None:
            raise
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


def handle_message(server: ToolServer, message: Any) -> dict[str, Any] | None:
    """Answer one JSON-RPC message; a notification returns ``None``."""
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return _error(None, -32600, "invalid request")
    request_id = message.get("id")
    method = message.get("method")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return _response(
            request_id,
            {
                "protocolVersion": negotiate_protocol_version(message.get("params")),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": dict(server.server_info),
            },
        )
    if method == "ping":
        return _response(request_id, {})
    if method == "tools/list":
        return _response(request_id, {"tools": list(server.tools)})
    if method == "tools/call":
        return _tool_call(server, request_id, message.get("params"))
    return _error(request_id, -32601, "method not found")


def serve(handle: Callable[[Any], dict[str, Any] | None], *, label: str) -> int:
    """Run the stdio loop, one JSON-RPC message per line, until stdin closes."""
    if sys.version_info < (3, 11):
        print(f"{label} requires Python 3.11 or newer", file=sys.stderr)
        return 2
    for raw_line in sys.stdin.buffer:
        try:
            reply = handle(json.loads(raw_line))
        except (UnicodeDecodeError, json.JSONDecodeError):
            reply = _error(None, -32700, "parse error")
        if reply is not None:
            sys.stdout.write(json.dumps(reply, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0
