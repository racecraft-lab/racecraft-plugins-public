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
PHASE_EXECUTION_GUIDES = ("skills/speckit-autopilot/references/phase-execution.md",
                          "codex-skills/speckit-autopilot/references/phase-execution-codex.md")
EXECUTION_EFFICIENCY_GUIDE = "skills/speckit-autopilot/references/execution-efficiency.md"


def guide_text(relative: str) -> str:
    """One shipped plugin file with its whitespace collapsed, so a phrase matches across wrapped lines."""
    return " ".join((PLUGIN_ROOT / relative).read_text(encoding="utf-8").split())


def host_source(relative: str, host: str) -> str:
    """One authored plugin file as `host` receives it, without the other host's blocks."""
    return emit_host((PLUGIN_ROOT / relative).read_text(encoding="utf-8"), host)


def assert_guides_say(test: unittest.TestCase, guides: Iterable[str], present: Iterable[str],
                      absent: Iterable[str] = ()) -> None:
    """Each guide carries every `present` phrase and none of the `absent` ones."""
    present, absent = tuple(present), tuple(absent)
    for relative in guides:
        with test.subTest(guide=relative):
            text = guide_text(relative)
            for phrase in present:
                test.assertIn(phrase, text)
            for phrase in absent:
                test.assertNotIn(phrase, text)


class GuidePhrases(NamedTuple):
    """Phrases a guide must carry and phrases it must not."""

    present: tuple[str, ...]
    absent: tuple[str, ...] = ()


def assert_guides_document(test: unittest.TestCase, shared: GuidePhrases, host: GuidePhrases,
                           hosts: Iterable[str] = PHASE_EXECUTION_GUIDES) -> None:
    """The shared execution-efficiency guide and each host guide carry the phrases that document one allowance."""
    assert_guides_say(test, (EXECUTION_EFFICIENCY_GUIDE,), *shared)
    assert_guides_say(test, hosts, *host)
