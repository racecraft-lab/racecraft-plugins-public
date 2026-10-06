"""The one owner of the shipped reviewability preset: its id, priority, locations and install command.

This repository keeps the preset where it installs it for itself, under `.specify/presets/`. The
payload build copies that directory to `presets/` in each host payload, and install, upgrade and
scaffold add it to a project with the `specify preset add` arguments built here, so no skill
restates a path or a priority.
"""

from __future__ import annotations

from pathlib import Path

PRESET_ID = "speckit-pro-reviewability"
# Lower resolves first. Core templates sit at the default 10, so the preset outranks them.
PRIORITY = 5
# Repository-relative source, and the payload-relative directory the build copies it to.
SOURCE_PATH = Path(".specify") / "presets" / PRESET_ID
PAYLOAD_PATH = Path("presets") / PRESET_ID


def shipped_dir() -> Path:
    """The preset directory: the payload copy when installed, the repository source otherwise."""
    plugin_root = Path(__file__).resolve().parents[1]
    payload = plugin_root / PAYLOAD_PATH
    return payload if payload.is_dir() else plugin_root.parent / SOURCE_PATH


def add_args() -> list[str]:
    """Arguments that follow the verified Spec Kit executable to install the shipped preset.

    Empty when no preset manifest is found, so a caller never runs a command that would fail on a
    missing directory.
    """
    source = shipped_dir()
    if not (source / "preset.yml").is_file():
        return []
    return ["preset", "add", "--dev", str(source), "--priority", str(PRIORITY)]
