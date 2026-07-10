#!/usr/bin/env python3
"""Sync plugin versions from plugin.json to marketplace.json."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


MARKETPLACES = (
    (Path(".claude-plugin/marketplace.json"), Path(".claude-plugin/plugin.json")),
    (Path(".agents/plugins/marketplace.json"), Path(".codex-plugin/plugin.json")),
)
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class FatalError(Exception):
    """Fatal sync error."""


def reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_nonfinite)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise FatalError(f"Error: {path.as_posix()} contains invalid JSON.") from exc


def source_path(entry: dict[str, Any]) -> str:
    source = entry.get("source")
    if isinstance(source, str):
        return source
    if isinstance(source, dict):
        path = source.get("path")
        return path if isinstance(path, str) else ""
    return ""


def plugin_name(entry: dict[str, Any], index: int) -> str:
    name = entry.get("name")
    return str(name) if isinstance(name, str) and name else f"index {index}"


def read_manifest_version(path: Path) -> str:
    if not path.is_file():
        raise FatalError(f"Error: Plugin file not found: {path.as_posix()} (referenced by marketplace entry).")
    manifest = load_json(path)
    if not isinstance(manifest, dict):
        raise FatalError(f"Error: {path.as_posix()} contains invalid JSON.")
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        raise FatalError(f"Error: No 'version' field in {path.as_posix()}.")
    if SEMVER_RE.fullmatch(version) is None:
        raise FatalError(f"Error: Invalid semver in {path.as_posix()}: '{version}'. Expected format: X.Y.Z")
    return version


def sync_marketplace(marketplace: Path, manifest_rel: Path) -> int:
    if not marketplace.is_file():
        return 0

    data = load_json(marketplace)
    if not isinstance(data, dict):
        raise FatalError(f"Error: {marketplace.as_posix()} contains invalid JSON.")

    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        if "plugins" in data:
            raise FatalError(f"Error: {marketplace.as_posix()} has a 'plugins' field but it is not an array.")
        raise FatalError(f"Error: {marketplace.as_posix()} does not contain a 'plugins' array.")

    if not plugins:
        print(f"Info: No plugins in {marketplace.as_posix()} -- nothing to sync.", file=sys.stderr)
        return 0

    changes: list[str] = []
    for index, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            raise FatalError(f"Error: Plugin entry at index {index} is not an object.")

        source_field = source_path(entry)
        if not source_field:
            raise FatalError(
                f"Error: Plugin entry '{plugin_name(entry, index)}' (index {index}) is missing the 'source' field or source.path."
            )

        if not source_field.startswith("./"):
            print(f"Info: Skipping non-relative source '{source_field}' (index {index}).", file=sys.stderr)
            continue

        plugin_dir = source_field[2:]
        if not plugin_dir:
            raise FatalError(f"Error: Source path '{source_field}' (index {index}) must identify a plugin directory.")
        if ".." in plugin_dir:
            raise FatalError(f"Error: Source path '{source_field}' (index {index}) contains illegal '..' segments.")

        plugin_json = Path(plugin_dir) / manifest_rel
        try:
            version = read_manifest_version(plugin_json)
        except FatalError as exc:
            message = str(exc)
            if "referenced by marketplace entry" in message:
                raise FatalError(
                    f"Error: Plugin file not found: {plugin_json.as_posix()} (referenced by marketplace entry at index {index})."
                ) from exc
            raise

        current = entry.get("version")
        current_version = current if isinstance(current, str) else ""
        entry["version"] = version
        if current_version != version:
            changes.append(f"synced {plugin_dir}: {current_version or '<none>'} -> {version}")

    if changes:
        try:
            rendered = json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
            marketplace.write_text(rendered, encoding="utf-8")
        except (OSError, ValueError) as exc:
            raise FatalError(f"Error: failed to write {marketplace.as_posix()}.") from exc
        for change in changes:
            print(change)
    return len(changes)


def main() -> int:
    if not any(marketplace.is_file() for marketplace, _manifest in MARKETPLACES):
        print("Error: no supported marketplace.json found. Run this script from the repository root.", file=sys.stderr)
        return 1

    try:
        for marketplace, manifest_rel in MARKETPLACES:
            sync_marketplace(marketplace, manifest_rel)
    except FatalError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
