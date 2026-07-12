#!/usr/bin/env python3
"""Emit the static Python-gated plugin matrix for PR Checks."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path


PLUGINS = ("speckit-pro",)


class PluginMatrixError(RuntimeError):
    """Raised when the plugin matrix cannot be emitted."""


def append_plugin_matrix(output_path: Path) -> str:
    encoded = json.dumps(list(PLUGINS), separators=(",", ":"))
    try:
        with output_path.open("a", encoding="utf-8", newline="\n") as output:
            output.write(f"plugins={encoded}\n")
    except OSError as error:
        raise PluginMatrixError(f"unable to append GITHUB_OUTPUT: {error}") from error
    return encoded


def main(argv: Sequence[str] | None = None) -> int:
    if argv:
        print("::error::emit-plugin-matrix.py does not accept arguments", file=sys.stderr)
        return 1
    output_value = os.environ.get("GITHUB_OUTPUT", "")
    if not output_value:
        print("::error::GITHUB_OUTPUT is not set", file=sys.stderr)
        return 1
    try:
        encoded = append_plugin_matrix(Path(output_value))
    except PluginMatrixError as error:
        print(f"::error::{error}", file=sys.stderr)
        return 1
    print(f"Python-gated plugin matrix: {encoded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
