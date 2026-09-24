#!/usr/bin/env python3
"""Launch the evaluate MCP server for a plugin-installed client.

The plugin cannot be fully self-contained: this server is a compiled Go
binary, and committing four platform builds to git would bloat the repository
and still need a fifth for anyone else. So the plugin ships this launcher and
the binary is installed once, separately.

Everything this writes for a human goes to stderr. Stdout belongs to the MCP
protocol, and a single stray line on it is a frame the client cannot parse.
"""

from __future__ import annotations

import os
import sys


def _home() -> str:
    return os.environ.get("HOME", "")


def _default(name: str, value: str) -> str:
    """Set name to value only when it is unset or empty, like sh's ${name:=value}."""
    if not os.environ.get(name):
        os.environ[name] = value
    return os.environ[name]


def main() -> int:
    binary = os.environ.get("EVALUATE_BIN") or os.path.join(
        _home(), ".local", "libexec", "racecraft-jev", "evaluate"
    )

    if not (os.path.isfile(binary) and os.access(binary, os.X_OK)):
        install_dir = os.path.dirname(binary)
        print(
            f"evaluate: no server binary at {binary}\n"
            "\n"
            "Install it once, then reconnect this MCP server. From the\n"
            "typesafe-jev directory of a source checkout:\n"
            "\n"
            f"  mkdir -p {install_dir}\n"
            f"  go build -trimpath -o {binary} ./cmd/evaluate\n"
            "\n"
            "Set EVALUATE_BIN to override the path.",
            file=sys.stderr,
        )
        return 1

    # Defaults the plugin can supply without the client having to expand
    # anything in its own config. An explicit value in the client's environment
    # still wins, because _default only assigns when the variable is unset or
    # empty. Each backend has its own key file, named after it, so neither is
    # handed the other's key.
    keys = os.path.join(_home(), ".config", "racecraft-jev")
    if (os.environ.get("JEV_PROVIDER") or "typesafe") == "openrouter":
        key_file = _default("JEV_API_KEY_FILE", os.path.join(keys, "openrouter.key"))
    else:
        key_file = _default("JEV_API_KEY_FILE", os.path.join(keys, "typesafe.key"))

    # The fallback is opt-in: only a configured JEV_FALLBACK_PROVIDER gets a key
    # file default, and the server validates the name.
    fallback = os.environ.get("JEV_FALLBACK_PROVIDER")
    if fallback:
        _default("JEV_FALLBACK_API_KEY_FILE", os.path.join(keys, f"{fallback}.key"))
    fallback_key_file = os.environ.get("JEV_FALLBACK_API_KEY_FILE", "")

    # A key file is the documented path, but an operator may use the provider's
    # environment variable instead. Only warn when nothing is available, and
    # never print a value.
    if (
        not os.path.isfile(key_file)
        and not (fallback_key_file and os.path.isfile(fallback_key_file))
        and not os.environ.get("OPENROUTER_API_KEY")
        and not os.environ.get("TYPESAFE_API_KEY")
    ):
        print(f"evaluate: no credential yet; expected a key file at {key_file}", file=sys.stderr)
        print("evaluate: see docs/openrouter.md for how to create it", file=sys.stderr)
        # Not fatal: the server reports the same thing with a better message,
        # and failing here would hide it.

    # exec, not a child process: the client signals this process directly, and
    # an extra process in between would swallow the termination it sends.
    sys.stderr.flush()
    os.execv(binary, [binary, "mcp"])
    return 1  # unreachable: execv replaces this process or raises


if __name__ == "__main__":
    raise SystemExit(main())
