#!/usr/bin/env python3
"""Parse historical VERBOSE PASS/FAIL output into a frozen parity baseline.

Each shell-to-Python port in XPLAT-010 commits one count-parity baseline per
invocation mode. The final predecessor captures are complete, so executable
capture support is retired at T097. This module retains the deterministic
parser and renderer used by the test library: it keeps only lines matching
``^\\s*(.+?)\\s\\.\\.\\.\\s(PASS|FAIL)$`` (discarding all other, possibly
interleaved, subprocess stdout), and writes the frozen format to
``tests/speckit-pro/parity/bash-to-python/<script>-baseline.txt``:

    NNN <verbatim runtime name>   (one per executed _pass/_fail, in order)
    TOTAL: <N>

Names are parsed **verbatim** from frozen runtime output — never reconstructed
from predecessor source text. Parsing fails loud on an empty name rather than
inventing a positional placeholder (count-parity contract §1/§2, research §D6).
"""

from __future__ import annotations

import os
import platform
import re
from pathlib import Path

# The single frozen parse filter (Clarifications Session 1, S1-Q4).
VERBOSE_LINE = re.compile(r"^\s*(.+?)\s\.\.\.\s(PASS|FAIL)$")

class BaselineError(Exception):
    """Raised on a malformed capture (empty/stale name, missing script, root env)."""


def baseline_inventory(path: Path) -> list[str]:
    names: list[str] = []
    total: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("TOTAL: "):
            total = int(line.removeprefix("TOTAL: "))
            continue
        _ordinal, name = line.split(" ", 1)
        names.append(name)
    if total != len(names):
        raise AssertionError(f"baseline TOTAL {total} does not match {len(names)} names")
    return names


def parse_verbose_lines(text: str) -> list[tuple[str, str]]:
    """Return ``[(name, outcome)]`` for every VERBOSE PASS/FAIL line, in order.

    Non-matching lines (progress text, summaries, interleaved detail) are
    discarded. A matched line whose name is empty/whitespace fails loud.
    """
    results: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = VERBOSE_LINE.match(line)
        if match is None:
            continue
        name = match.group(1).strip()
        outcome = match.group(2)
        if not name:
            raise BaselineError(f"empty check name on PASS/FAIL line: {line!r}")
        results.append((name, outcome))
    return results


def render_baseline(results: list[tuple[str, str]]) -> str:
    """Render the frozen ``NNN <name>`` + ``TOTAL: <N>`` baseline text."""
    lines = [f"{index:03d} {name}" for index, (name, _outcome) in enumerate(results, start=1)]
    lines.append(f"TOTAL: {len(results)}")
    return "\n".join(lines) + "\n"


def capture_environment() -> dict[str, object]:
    """Record the pinned capture environment (must be non-root, matching CI).

    A root-vs-non-root capture can diverge (e.g. 31 vs 36 assertions for
    ``test-moc-lint-exit-codes.sh``), so the environment is recorded and the
    capture refuses to run as root.
    """
    is_root = hasattr(os, "geteuid") and os.geteuid() == 0
    return {
        "is_root": bool(is_root),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }
