"""Shared reads of the shipped guide prose for tests that pin what the guides say."""

from __future__ import annotations

import sys
import unittest
from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple

PLUGIN_ROOT = Path(__file__).resolve().parents[3] / "speckit-pro"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from speckit_pro_runner.host_parity import emit_host  # noqa: E402
# A guide is a plugin-relative path, or a (path, host) pair naming the host whose view is read.
Guide = str | tuple[str, str]
PHASE_EXECUTION = "skills/speckit-autopilot/references/phase-execution.md"
PHASE_EXECUTION_GUIDES: tuple[Guide, ...] = ((PHASE_EXECUTION, "claude"), (PHASE_EXECUTION, "codex"))
EXECUTION_EFFICIENCY_GUIDE = "skills/speckit-autopilot/references/execution-efficiency.md"


def host_source(relative: str, host: str | None = None) -> str:
    """One authored plugin file; with `host`, as that host receives it, without the other host's blocks."""
    text = (PLUGIN_ROOT / relative).read_text(encoding="utf-8")
    return text if host is None else emit_host(text, host)


def guide_text(relative: str, host: str | None = None) -> str:
    """One shipped plugin file with its whitespace collapsed, so a phrase matches across wrapped lines."""
    return " ".join(host_source(relative, host).split())


def guide_view(guide: Guide) -> str:
    """`guide_text` for a plain path or a (path, host) pair."""
    return guide_text(guide) if isinstance(guide, str) else guide_text(*guide)


def host_guides(relative: str) -> tuple[Guide, Guide]:
    """One shared file as each host receives it."""
    return ((relative, "claude"), (relative, "codex"))


def assert_guides_say(test: unittest.TestCase, guides: Iterable[Guide], present: Iterable[str],
                      absent: Iterable[str] = ()) -> None:
    """Each guide carries every `present` phrase and none of the `absent` ones."""
    present, absent = tuple(present), tuple(absent)
    for guide in guides:
        relative, host = (guide, None) if isinstance(guide, str) else guide
        with test.subTest(guide=relative, host=host):
            text = guide_text(relative, host)
            for phrase in present:
                test.assertIn(phrase, text)
            for phrase in absent:
                test.assertNotIn(phrase, text)


class GuidePhrases(NamedTuple):
    """Phrases a guide must carry and phrases it must not."""

    present: tuple[str, ...]
    absent: tuple[str, ...] = ()


def assert_guides_document(test: unittest.TestCase, shared: GuidePhrases, host: GuidePhrases,
                           hosts: Iterable[Guide] = PHASE_EXECUTION_GUIDES) -> None:
    """The shared execution-efficiency guide and each host guide carry the phrases that document one allowance."""
    assert_guides_say(test, (EXECUTION_EFFICIENCY_GUIDE,), *shared)
    assert_guides_say(test, hosts, *host)
