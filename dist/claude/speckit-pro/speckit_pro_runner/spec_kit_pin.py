"""The one owner of the pinned Spec Kit CLI: version, commit, install argv and the version comparison.

Skills, CI and the prerequisite check read the pin from here. Bumping it is a reviewed
change that must pass the canary on both hosts.
"""

from __future__ import annotations

import re

PINNED_VERSION = "1.1.0"
# Tag v1.1.0 of github/spec-kit. PyPI lacked 1.1.0, so the install names the commit.
PINNED_COMMIT = "f1d3a4f8337ebbd3ae22760a9c12e3352b93a175"
PINNED_SOURCE = f"git+https://github.com/github/spec-kit.git@{PINNED_COMMIT}"
INSTALL_ARGV = ["uv", "tool", "install", "specify-cli", "--force", "--from", PINNED_SOURCE]

_CLI_VERSION_ROW = re.compile(r"CLI Version\s+(\S+)")
_RELEASE = re.compile(r"(\d+)\.(\d+)\.(\d+)\Z")


def parse_cli_version(output: str) -> str | None:
    """The version from `specify version` output, or None when the row is absent."""
    found = _CLI_VERSION_ROW.search(output)
    return found.group(1) if found else None


def version_status(installed: str | None, *, cli_found: bool) -> str:
    """One of missing, unreadable, older, newer or match, against the pin.

    A version that is not a plain release (a dev or local build) is unreadable, because it
    cannot be placed exactly against the pin.
    """
    if not cli_found:
        return "missing"
    release = _RELEASE.match(installed) if installed else None
    if release is None:
        return "unreadable"
    installed_parts = tuple(int(part) for part in release.groups())
    pinned_parts = tuple(int(part) for part in PINNED_VERSION.split("."))
    if installed_parts == pinned_parts:
        return "match"
    return "older" if installed_parts < pinned_parts else "newer"
