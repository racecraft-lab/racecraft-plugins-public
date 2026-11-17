"""Path helpers shared by runner modules."""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
from pathlib import Path


MANIFEST_NAME = "speckit-pro-runner.manifest.json"


def detect_plugin_root() -> Path | None:
    for candidate in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
        if (candidate / ".claude-plugin" / "plugin.json").is_file() or (candidate / ".codex-plugin" / "plugin.json").is_file():
            return candidate
    return None


def runner_source_files(package_dir: Path) -> list[Path]:
    """List every runner file the trust manifest covers.

    This is the one roster: the refresh script and the payload gates call it.
    It holds all Python modules and every JSON file the runner loads at run
    time, except the manifest itself.
    """
    return sorted(
        path
        for pattern in ("*.py", "*.json")
        for path in package_dir.rglob(pattern)
        if "__pycache__" not in path.parts and path.is_file() and path.name != MANIFEST_NAME
    )


def find_repo_root(start: Path) -> Path | None:
    candidates = [start, *start.parents] if start.is_dir() else [start.parent, *start.parent.parents]
    for candidate in candidates:
        if (candidate / "speckit-pro" / "speckit_pro_runner").is_dir() and (candidate / "tests" / "speckit-pro").is_dir():
            return candidate.resolve(strict=False)
    return None


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def parse_version_tuple(version: str) -> tuple[int, int, int]:
    """The first three dotted parts as integers; a missing or non-numeric part reads as 0."""
    parts = []
    for part in version.split(".")[:3]:
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)  # type: ignore[return-value]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolves_to_current_python(executable: str, *, relative_to: Path | None = None) -> bool:
    if executable == sys.executable:
        return True

    path = Path(executable)
    has_path_separator = os.sep in executable or (os.altsep is not None and os.altsep in executable)
    if path.is_absolute():
        candidate = path
    elif relative_to is not None and has_path_separator:
        candidate = relative_to / path
    else:
        resolved = shutil.which(executable)
        if resolved is None:
            if relative_to is not None:
                return False
            candidate = path
        else:
            candidate = Path(resolved)

    try:
        return candidate.samefile(sys.executable)
    except OSError:
        return candidate.resolve(strict=False) == Path(sys.executable).resolve(strict=False)
