"""Each host's skill tree as it ships, for harnesses that stage skills.

Shared skill files carry host blocks, so neither `speckit-pro/skills` nor
`speckit-pro/codex-skills` is what a host loads. A harness asks for the
rendered tree instead. It is built once per process with the same renderer
the payload build uses, under the name `skills` that both payloads use, so
relative links resolve as they do once installed. It is removed at exit.
"""

from __future__ import annotations

import atexit
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3] / "speckit-pro"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from speckit_pro_runner.host_skills import render_host_skills  # noqa: E402

_RENDERED: dict[tuple[Path, str], Path] = {}


def host_skill_root(host: str, plugin_root: Path = PLUGIN_ROOT) -> Path:
    """The rendered skill tree `host` loads from `plugin_root`'s source."""
    key = (plugin_root.resolve(), host)
    if key not in _RENDERED:
        # Not tempfile.mkdtemp: harness tests script that call's results, and a
        # view built on the side must not consume one.
        temporary = Path(tempfile.gettempdir()).resolve() / f"speckit-{host}-skills-{uuid.uuid4().hex}"
        temporary.mkdir(mode=0o700)
        atexit.register(shutil.rmtree, temporary, ignore_errors=True)
        root = temporary / "skills"
        render_host_skills(key[0], host, root)
        _RENDERED[key] = root
    return _RENDERED[key]


def rendered_skill_source(host: str, skill: str, plugin_root: Path = PLUGIN_ROOT) -> Path:
    """`skill`'s SKILL.md as `host` loads it.

    A Claude harness may also measure a Codex-only skill, so Claude falls back
    to the Codex view; Codex reads only its own.
    """
    for view in ("claude", "codex") if host == "claude" else ("codex",):
        path = host_skill_root(view, plugin_root) / skill / "SKILL.md"
        if path.is_file():
            return path
    raise ValueError(f"skill not found for requested skill {skill!r}")
