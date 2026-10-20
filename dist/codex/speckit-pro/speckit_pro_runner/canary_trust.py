"""Where a canary-issued plan approval is trusted: only a host home the canary marked (ADR 0016)."""
from __future__ import annotations

from pathlib import Path

MARKER_NAME = ".speckit-pro-canary-home"
MARKER_TEXT = "canary-home/v1\n"


def canary_home_trusted(home: Path | None = None) -> bool:
    """True only when this host home carries the canary's exact marker. A default install never has one."""
    try:
        return ((home or Path.home()) / MARKER_NAME).read_text(encoding="utf-8") == MARKER_TEXT
    except (OSError, RuntimeError, ValueError):
        return False
