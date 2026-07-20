#!/usr/bin/env python3
"""Public capability evidence API and command-line entry point for G56R-002."""

from __future__ import annotations

import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from codex_capability_cli import *

__all__ = [name for name in globals() if not name.startswith("__")]


if __name__ == "__main__":
    raise SystemExit(main())
