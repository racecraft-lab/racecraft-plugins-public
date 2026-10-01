"""Render each host's skill tree from one authored source.

`skills/` holds every shared skill file. Text that differs by host sits in
host blocks (see `host_parity`), so a host's copy is the shared tree with the
other host's blocks removed. `codex-skills/` holds only whole files that Codex
has and Claude does not. The payload build and the eval harnesses both render
through `render_host_skills`, so they see the same bytes.
"""

from __future__ import annotations

import re
import shutil
from collections.abc import Iterable
from pathlib import Path

from .host_parity import emit_host


# Codex skill files with no Claude twin. These are host deltas by design and
# stay in codex-skills/.
CODEX_ONLY_SKILL_FILE = re.compile(
    r"install/.+|[^/]+/agents/openai\.yaml|speckit-autopilot/references/(?:preview|sweep)-prompts/.+"
)


def codex_skill_overlay_errors(plugin_root: Path) -> list[str]:
    """Name each codex-skills/ file that is not Codex-only."""
    root = plugin_root / "codex-skills"
    return [
        f"codex-skills/{relative} overlays a shared skill file; merge it into skills/ as host blocks"
        for relative in sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
        if not CODEX_ONLY_SKILL_FILE.fullmatch(relative)
    ]


def emit_host_files(paths: Iterable[Path], host: str) -> None:
    """Rewrite each copied source as `host` sees it, without the other host's blocks."""
    for path in paths:
        text = path.read_text(encoding="utf-8")
        emitted = emit_host(text, host)
        if emitted != text:
            path.write_text(emitted, encoding="utf-8")


def render_host_skills(plugin_root: Path, host: str, destination: Path) -> None:
    """Write `host`'s skill tree to `destination` from the authored source."""
    shutil.copytree(
        plugin_root / "skills", destination, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    emit_host_files(destination.rglob("*.md"), host)
    if host == "codex":
        shutil.copytree(plugin_root / "codex-skills", destination, dirs_exist_ok=True)
