#!/usr/bin/env python3
"""Launch the evaluate MCP server for a plugin-installed client.

The plugin cannot be fully self-contained: this server is a compiled Go
binary, and committing four platform builds to git would bloat the repository
and still need a fifth for anyone else. So the plugin ships this launcher and
the binary is installed once, separately.

When the binary is installed, the launcher replaces itself with
`evaluate mcp --plugin-defaults`. That server reads the plugin's key-file
defaults and, when no credential source is configured at all, serves setup
instructions with no tools instead of refusing to start. A credential that is
configured but broken still refuses, and names the fix.

When the binary is missing, or on Windows, where no release build ships yet,
the launcher itself serves a minimal stand-in with no tools whose instructions
say how to set Jev up. A user without a TypeSafe or OpenRouter key, or without
the binary, then sees a connected server that explains itself rather than a
failed one.

The launcher never opens a key file or reads a key, and it starts no other
process: it either serves the stand-in or execs the binary.

Everything this writes for a human goes to stderr. Stdout belongs to the MCP
protocol, and a single stray line on it is a frame the client cannot parse.
"""

from __future__ import annotations

import json
import os
import shlex
import sys

KEY_DIRECTORY = os.path.join("~", ".config", "racecraft-jev")
INSTALLER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install_evaluate.py")
SETUP_TEXT = (
    "Jev is not set up on this machine, so this server offers no tools.\n"
    "To enable the evaluate tool:\n"
    f"1. Install the evaluate binary that matches this plugin: python3 {shlex.quote(INSTALLER)}\n"
    f"2. Put a TypeSafe key in {KEY_DIRECTORY}/typesafe.key, or an OpenRouter key in "
    f"{KEY_DIRECTORY}/openrouter.key, readable only by you (chmod 600).\n"
    "3. Reconnect this MCP server.\n"
    "Until then, make any judgment yourself in the ordinary way."
)
# Newest first. An unknown version from the client is answered with the newest
# one here, which the client may accept or refuse.
PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")


def _say(message: str) -> None:
    print(f"evaluate: {message}", file=sys.stderr, flush=True)


def resolve_binary() -> str:
    """Return the binary path: EVALUATE_BIN, else the installer's default.

    A leading ~ in EVALUATE_BIN is expanded, as the installer does, so both
    resolve the same file.
    """
    explicit = os.environ.get("EVALUATE_BIN")
    if explicit:
        return os.path.expanduser(explicit)
    return os.path.join(os.path.expanduser("~"), ".local", "libexec", "racecraft-jev", "evaluate")


def is_executable(path: str) -> bool:
    return os.path.isfile(path) and os.access(path, os.X_OK)


def _reply(message_id: object, result: object = None, error: dict | None = None) -> dict:
    reply: dict = {"jsonrpc": "2.0", "id": message_id}
    if error is not None:
        reply["error"] = error
    else:
        reply["result"] = result
    return reply


def _handle(message: object, instructions: str) -> dict | None:
    if not isinstance(message, dict):
        return _reply(None, error={"code": -32600, "message": "Invalid Request"})
    method = message.get("method")
    if "id" not in message:
        return None  # a notification: nothing to answer
    message_id = message["id"]
    if method == "initialize":
        params = message.get("params") or {}
        requested = params.get("protocolVersion") if isinstance(params, dict) else None
        version = requested if requested in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0]
        return _reply(
            message_id,
            {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "evaluate", "version": "unconfigured"},
                "instructions": instructions,
            },
        )
    if method == "ping":
        return _reply(message_id, {})
    if method == "tools/list":
        return _reply(message_id, {"tools": []})
    if method == "tools/call":
        return _reply(
            message_id,
            {"content": [{"type": "text", "text": instructions}], "isError": True},
        )
    return _reply(message_id, error={"code": -32601, "message": "Method not found"})


def serve_unconfigured(reason: str) -> int:
    """Serve the stand-in MCP server over stdio until the client disconnects."""
    _say(f"{reason}; serving setup instructions with no tools")
    instructions = f"{reason}.\n{SETUP_TEXT}"
    for raw in sys.stdin.buffer:
        line = raw.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            reply: object = _reply(None, error={"code": -32700, "message": "Parse error"})
        else:
            if isinstance(message, list):
                replies = [r for r in (_handle(m, instructions) for m in message) if r is not None]
                reply = replies or None
            else:
                reply = _handle(message, instructions)
        if reply is not None:
            sys.stdout.write(json.dumps(reply, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


def main() -> int:
    if os.name == "nt":
        return serve_unconfigured("evaluate has no Windows release build yet")
    binary = resolve_binary()
    if not is_executable(binary):
        return serve_unconfigured(f"the evaluate binary is not installed at {binary}")
    # exec, not a child process: the client signals this process directly, and
    # an extra process in between would swallow the termination it sends.
    sys.stderr.flush()
    os.execv(binary, [binary, "mcp", "--plugin-defaults"])
    return 1  # unreachable: execv replaces this process or raises


if __name__ == "__main__":
    raise SystemExit(main())
