"""Render each host's skill tree from one authored source.

`skills/` holds every shared skill file. Text that differs by host sits in
host blocks (see `host_parity`), so a host's copy is the shared tree with the
other host's blocks removed. `codex-skills/` holds only what Codex has and
Claude does not: whole Codex-only files, plus the overlays not yet merged into
their shared file. The payload build and the eval harnesses both render
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
# Codex overlays not yet merged into their shared file as host blocks. A merge
# removes its entry; a new overlay, or an entry whose file is gone, fails the
# artifact refresh.
UNMERGED_CODEX_OVERLAYS = frozenset({
    "speckit-archive-cleanup/SKILL.md",
    "speckit-autopilot/SKILL.md",
    "speckit-autopilot/references/error-recovery-codex.md",
    "speckit-autopilot/references/phase-execution-codex.md",
    "speckit-autopilot/references/post-implementation-codex.md",
    "speckit-autopilot/references/prerequisites-codex.md",
    "speckit-autopilot/references/task-list-canonical-codex.md",
    "speckit-autopilot/references/workflow-file-protocol-codex.md",
    "speckit-install/SKILL.md",
    "speckit-resolve-pr/SKILL.md",
    "speckit-scaffold-spec/SKILL.md",
    "speckit-status/SKILL.md",
    "speckit-upgrade/SKILL.md",
})
CODEX_SKILL_GUARD = "## Codex Skill-Selection Guard"


def codex_skill_overlay_errors(plugin_root: Path) -> list[str]:
    """Name each codex-skills/ file that is neither Codex-only nor a listed overlay."""
    root = plugin_root / "codex-skills"
    present = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    errors = [
        f"codex-skills/{relative} overlays a shared skill file; merge it into skills/ as host blocks"
        for relative in sorted(present)
        if not CODEX_ONLY_SKILL_FILE.fullmatch(relative) and relative not in UNMERGED_CODEX_OVERLAYS
    ]
    errors += [
        f"codex-skills/{relative} is listed as an unmerged overlay but does not exist"
        for relative in sorted(UNMERGED_CODEX_OVERLAYS - present)
    ]
    return errors


def strip_codex_guard(skill_file: Path) -> None:
    """Drop an unmerged Claude skill's pointer to its Codex overlay."""
    lines = skill_file.read_text(encoding="utf-8").splitlines(keepends=True)
    output: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index].rstrip("\n") == CODEX_SKILL_GUARD:
            index += 1
            while index < len(lines) and not lines[index].startswith("## "):
                index += 1
            continue
        output.append(lines[index])
        index += 1
    skill_file.write_text("".join(output), encoding="utf-8")


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
        return
    for skill_file in destination.glob("*/SKILL.md"):
        strip_codex_guard(skill_file)
