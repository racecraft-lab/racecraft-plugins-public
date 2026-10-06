"""The one owner of the shipped reviewability preset: its id, priority, locations and install command.

This repository keeps the preset where it installs it for itself, under `.specify/presets/`. The
payload build copies that directory to `presets/` in each host payload, and install, upgrade and
scaffold add it to a project with the `specify preset add` arguments built here, so no skill
restates a path or a priority.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .canonical_json import canonical_bytes
from .trusted_io import trusted_tree_snapshot

PRESET_ID = "speckit-pro-reviewability"
# Lower resolves first. Core templates sit at the default 10, so the preset outranks them.
PRIORITY = 5
# Repository-relative source, and the payload-relative directory the build copies it to.
SOURCE_PATH = Path(".specify") / "presets" / PRESET_ID
PAYLOAD_PATH = Path("presets") / PRESET_ID
# Exact preset trees from the plugin's legacy setup releases, not registry identity claims.
LEGACY_FINGERPRINTS = frozenset({
    "d24a346c0c0926295a648cbca7680dac3ae656501bbb28b983cd9d99168c400d",  # dcd1208a
    "4e25fcc06fd1c825a92485575d8f455a9f747f7461a1818ced7900851709d9b5",  # 9d4b9486
    "4e205d4a2ddf31908af998d95d5373d3e938e9204f65a9b56ddb4f388728c906",  # 8b59fe55
    "29816d6a894dc789c141e47923725b95150f17568d26e8e570c848fb5c5edc64",  # b57e2992
    "b4accfeccd50ac731f0213f99482a01a8f24069abf287e07837af0d974e57c5c",  # cef3ed26
    "2d77d420bba7e13aa9ad557c582b3338d7f82a49c7c94ff84a708f3a5a685f90",  # 4e595989
})


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
    if (isinstance(entry, dict) and entry.get("enabled") is True
            and type(entry.get("priority")) is int and entry["priority"] in (PRIORITY, 10)
            and entry.get("registered_commands", {}) == {}
            and entry.get("registered_skills", []) in ([], {})
            and (installed == expected or content_fingerprint(installed) in LEGACY_FINGERPRINTS)):
        return {
            "id": PRESET_ID, "status": "upgrade", "add_args": [],
            "upgrade_args": ["preset", "update", PRESET_ID, *args[2:]],
        }
    if isinstance(presets, dict) and PRESET_ID in presets:
        # Spec Kit rejects add while this registration remains, even without files.
        return {
            "id": PRESET_ID, "status": "unavailable", "add_args": [],
            "reason": (
                f"Preset {PRESET_ID} is registered but does not match the shipped preset. "
                f"Repair the registration with specify preset remove {PRESET_ID}, then retry."
            ),
        }
    return {"id": PRESET_ID, "status": "missing", "add_args": args}


def content_fingerprint(content: dict[Path, bytes | None]) -> str:
    """Bind every relative path, directory and byte to a known legacy tree."""
    tree = {path.as_posix(): data.hex() if data is not None else None
            for path, data in content.items()}
    return hashlib.sha256(canonical_bytes(tree)).hexdigest()
