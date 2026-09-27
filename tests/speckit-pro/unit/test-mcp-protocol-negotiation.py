#!/usr/bin/env python3
"""The stdio brokers negotiate the MCP protocol version instead of echoing it."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Callable
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
sys.path[:0] = [str(PLUGIN_ROOT), str(REPO_ROOT / "tests/speckit-pro/lib")]

from speckit_pro_runner import author_broker, research_broker, sweep_broker  # noqa: E402
from speckit_pro_runner.mcp_protocol import (  # noqa: E402
    LATEST_PROTOCOL_VERSION,
    SUPPORTED_PROTOCOL_VERSIONS,
)
from test_result import run_counted  # noqa: E402

BROKERS: dict[str, Callable[[Any], dict[str, Any] | None]] = {
    "author": author_broker.handle_message,
    "research": research_broker.handle_message,
    "sweep": sweep_broker.handle_message,
}
# Versions the installed hosts send today: Claude Code 2.1.283 supports
# 2024-10-07 through 2025-11-25; Codex 0.156 can request 2026-07-28.
HOST_REQUESTED_VERSIONS = ("2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25")


def negotiated(handle: Callable[[Any], dict[str, Any] | None], params: Any) -> Any:
    reply = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": params})
    assert reply is not None
    return reply["result"]["protocolVersion"]


class ProtocolNegotiation(unittest.TestCase):
    def test_a_supported_version_is_echoed(self) -> None:
        for name, handle in BROKERS.items():
            for version in HOST_REQUESTED_VERSIONS:
                with self.subTest(broker=name, version=version):
                    self.assertEqual(version, negotiated(handle, {"protocolVersion": version}))

    def test_an_unsupported_version_gets_the_latest_supported_one(self) -> None:
        for name, handle in BROKERS.items():
            for version in ("2026-07-28", "1999-01-01", "", 20250618):
                with self.subTest(broker=name, version=version):
                    self.assertEqual(LATEST_PROTOCOL_VERSION, negotiated(handle, {"protocolVersion": version}))

    def test_missing_params_get_the_latest_supported_version(self) -> None:
        for name, handle in BROKERS.items():
            for params in ({}, None, "not an object"):
                with self.subTest(broker=name, params=params):
                    self.assertEqual(LATEST_PROTOCOL_VERSION, negotiated(handle, params))

    def test_the_latest_version_is_supported(self) -> None:
        self.assertIn(LATEST_PROTOCOL_VERSION, SUPPORTED_PROTOCOL_VERSIONS)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProtocolNegotiation)
    raise SystemExit(run_counted(suite, label="test-mcp-protocol-negotiation"))
