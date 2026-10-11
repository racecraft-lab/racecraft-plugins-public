#!/usr/bin/env python3
"""Launch the adjacent installed runner without changing the caller's cwd."""

import runpy
import sys
from pathlib import Path


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    runpy.run_module("speckit_pro_runner", run_name="__main__", alter_sys=True)
