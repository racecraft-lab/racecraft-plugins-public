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

from .trusted_io import trusted_tree_snapshot

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
    try:
        payload.lstat()
    except FileNotFoundError:
        return plugin_root.parent / SOURCE_PATH
    return payload


def add_args(source: Path) -> list[str]:
    """Arguments for a shipped source whose snapshot has already been validated."""
    return ["preset", "add", "--dev", str(source), "--priority", str(PRIORITY)]


def state(root: Path, repo_root: Path) -> dict[str, Any]:
    """Authenticate registry and preset bytes from one coherent project tree capture.

    The trusted plugin tree is the content authority, not project registry claims or
    resolver-valid YAML. Unsafe evidence stops installation rather than following links.
    """
    result: dict[str, Any] = {"id": PRESET_ID, "status": "unavailable", "add_args": []}
    source = shipped_dir()
    try:
        shipped = trusted_tree_snapshot(source, Path(source.anchor))
    except OSError:
        return result
    if shipped.get(Path("preset.yml"), (0, None))[1] is None:
        return result
    args = add_args(source)
    try:
        project = trusted_tree_snapshot(root / ".specify/presets", repo_root)
    except FileNotFoundError:
        project = {}
    except OSError:
        return result
    registry = project.get(Path(".registry"), (0, None))[1]
    return classify_snapshot(project, shipped, registry, args)


def classify_snapshot(
    project: dict[Path, tuple[int, bytes | None]], shipped: dict[Path, tuple[int, bytes | None]],
    registry: bytes | None, args: list[str],
) -> dict[str, Any]:
    """The installed decision requires an enabled priority entry and exact shipped content."""
    try:
        document = json.loads(registry or b"")
    except (ValueError, UnicodeDecodeError):
        document = {}
    presets = document.get("presets") if isinstance(document, dict) else None
    entry = presets.get(PRESET_ID) if isinstance(presets, dict) else None
    registered = (isinstance(entry, dict) and entry.get("enabled") is True
                  and type(entry.get("priority")) is int and entry["priority"] == PRIORITY)
    installed = {path.relative_to(PRESET_ID): content for path, (_, content) in project.items()
                 if path.parts and path.parts[0] == PRESET_ID}
    expected = {path: content for path, (_, content) in shipped.items()}
    if registered and installed == expected:
        return {"id": PRESET_ID, "status": "installed", "add_args": []}
    return {"id": PRESET_ID, "status": "missing", "add_args": args}
