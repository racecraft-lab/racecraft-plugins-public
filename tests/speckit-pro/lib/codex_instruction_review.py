"""Repository-only instruction review policy shared by proof and regeneration."""

from __future__ import annotations

import hashlib
from pathlib import Path

REVIEW_INVENTORY = Path(__file__).resolve().parents[1] / "unit/fixtures/codex-spawn-instruction-inventory.json"


def read_surface(path: Path) -> str:
    """Decode strictly: an unreadable file fails the gate instead of being skipped."""
    try:
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise AssertionError(f"unreadable dispatch surface: {path.name}: {error}") from error


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
