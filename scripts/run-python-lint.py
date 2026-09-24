#!/usr/bin/env python3
"""Install and run the pinned Python lint tools for the PR Checks lint jobs.

Ruff (pyflakes F rules, scoped by ruff.toml) and mypy (the mypy.ini allowlist)
are dev-only CI tools, never runtime dependencies. Their versions are pinned
here so the workflow and local runs use the same ones. Install into a virtual
environment locally; the system Python may refuse pip installs.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Callable, Sequence
from importlib import metadata
from typing import Any

PINNED_VERSIONS = {"ruff": "0.16.8", "mypy": "2.3.1"}
TOOL_ARGUMENTS = {"ruff": ("check", "--no-cache"), "mypy": ()}


class LintToolError(RuntimeError):
    """The requested lint tool is missing or not at its pinned version."""


def install_command(tool: str) -> list[str]:
    return [sys.executable, "-m", "pip", "install", f"{tool}=={PINNED_VERSIONS[tool]}"]


def run_command(tool: str, extra_arguments: Sequence[str]) -> list[str]:
    return [sys.executable, "-m", tool, *TOOL_ARGUMENTS[tool], *extra_arguments]


def require_pinned_version(
    tool: str,
    version_of: Callable[[str], str] = metadata.version,
) -> None:
    pinned = PINNED_VERSIONS[tool]
    try:
        installed = version_of(tool)
    except metadata.PackageNotFoundError as error:
        raise LintToolError(
            f"{tool} is not installed; run python3 scripts/run-python-lint.py install {tool}"
        ) from error
    if installed != pinned:
        raise LintToolError(f"{tool} {installed} is installed, but the pinned version is {pinned}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    install = commands.add_parser("install", help="pip install the pinned tool version")
    install.add_argument("tool", choices=sorted(PINNED_VERSIONS))
    run = commands.add_parser("run", help="run the tool at its pinned version")
    run.add_argument("tool", choices=sorted(PINNED_VERSIONS))
    run.add_argument("extra_arguments", nargs=argparse.REMAINDER)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    run: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
    version_of: Callable[[str], str] = metadata.version,
) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "install":
            return int(run(install_command(args.tool), check=False, shell=False).returncode)
        require_pinned_version(args.tool, version_of)
        return int(run(run_command(args.tool, args.extra_arguments), check=False, shell=False).returncode)
    except LintToolError as error:
        print(f"::error::{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
