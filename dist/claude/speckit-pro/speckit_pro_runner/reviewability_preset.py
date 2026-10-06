"""The one owner of the shipped reviewability preset: its id, priority, locations and install command.

This repository keeps the preset where it installs it for itself, under `.specify/presets/`. The
payload build copies that directory to `presets/` in each host payload, and install, upgrade and
scaffold add it to a project with the `specify preset add` arguments built here, so no skill
restates a path or a priority.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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


def state(registry: str, manifest_exists: bool) -> dict[str, Any]:
    """Classify trusted project evidence and supply the command when installation is needed."""
    state: dict[str, Any] = {"id": PRESET_ID, "status": "installed", "add_args": []}
    try:
        document = json.loads(registry)
    except ValueError:
        document = None
    presets = document.get("presets") if isinstance(document, dict) else None
    registered = isinstance(presets, dict) and PRESET_ID in presets
    if registered and manifest_exists:
        return state
    state["add_args"] = add_args()
    state["status"] = "missing" if state["add_args"] else "unavailable"
    return state
