"""Path helpers shared by runner gate modules."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


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
