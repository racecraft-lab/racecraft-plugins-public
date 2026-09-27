"""MCP protocol versions the stdio brokers speak."""

from __future__ import annotations

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
