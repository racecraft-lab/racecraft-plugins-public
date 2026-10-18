"""Repository instruction review policy shared by validation and regeneration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REVIEW_INVENTORY = Path(__file__).resolve().parents[1] / "tests/speckit-pro/unit/fixtures/codex-spawn-instruction-inventory.json"
SKILL_INVENTORY_CHUNK_SIZE = 50


def read_surface(path: Path) -> str:
    """Decode strictly: an unreadable file fails the gate instead of being skipped."""
    try:
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise AssertionError(f"unreadable dispatch surface: {path.name}: {error}") from error


def review_inventory_document(agents: dict[str, str], skills: dict[str, str]) -> dict[str, dict[str, str]]:
    """Represent the complete reviewed inventory in bounded, ordered skill chunks."""
    entries = sorted(skills.items())
    inventory = {"agents": agents}
    for start in range(0, len(entries), SKILL_INVENTORY_CHUNK_SIZE):
        chunk = start // SKILL_INVENTORY_CHUNK_SIZE + 1
        inventory[f"skills-{chunk}"] = dict(entries[start:start + SKILL_INVENTORY_CHUNK_SIZE])
    return inventory


def read_review_inventory(path: Path = REVIEW_INVENTORY) -> dict[str, dict[str, str]]:
    """Read and validate every chunk before exposing the reviewed path-to-hash maps."""
    try:
        manifest = json.loads(read_surface(path))
        if not isinstance(manifest, dict):
            raise ValueError("invalid inventory fixture manifest")
        agents = manifest.get("agents")
        chunk_names = {name for name in manifest if isinstance(name, str) and name.startswith("skills-")}
        expected_names = {f"skills-{index}" for index in range(1, len(chunk_names) + 1)}
        if (
            not isinstance(agents, dict)
            or not agents
            or not all(isinstance(name, str) and isinstance(digest, str) for name, digest in agents.items())
            or not chunk_names
            or chunk_names != expected_names
            or set(manifest) != {"agents", *chunk_names}
        ):
            raise ValueError("invalid inventory fixture manifest")
        skills: dict[str, str] = {}
        for name in (f"skills-{index}" for index in range(1, len(chunk_names) + 1)):
            part = manifest[name]
            if (
                not isinstance(part, dict)
                or not part
                or not all(isinstance(path, str) and isinstance(digest, str) for path, digest in part.items())
                or skills.keys() & part.keys()
            ):
                raise ValueError("invalid or repeated inventory fixture entries")
            skills.update(part)
        if not skills:
            raise ValueError("empty skills inventory")
        return {"agents": agents, "skills": skills}
    except (AssertionError, OSError, ValueError, KeyError, TypeError) as error:
        raise AssertionError("unreadable instruction review inventory") from error


def instruction_paths(root: Path) -> list[Path]:
    """Walk one complete tree; linked and missing surfaces have no review."""
    if not root.is_dir() or root.is_symlink():
        raise AssertionError("missing or linked instruction root")
    paths = sorted(root.rglob("*"))
    for path in paths:
        if path.is_symlink():
            raise AssertionError(f"unreviewed instruction symlink: {path.relative_to(root)}")
    return [path for path in paths if path.is_file()]


def instruction_inventory(root: Path) -> dict[str, str]:
    """Bind every instruction byte to its path, without classifying its prose.

    Any file can carry instructions regardless of its extension or directory.
    """
    records = {
        path.relative_to(root).as_posix(): hashlib.sha256(read_surface(path).encode("utf-8")).hexdigest()
        for path in instruction_paths(root)
    }
    if not records:
        raise AssertionError("instruction inventory matched nothing")
    return records
