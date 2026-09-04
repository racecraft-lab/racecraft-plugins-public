#!/usr/bin/env python3
"""Build platform-specific SpecKit Pro install payloads."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    runner_root = repo_root / "speckit-pro"
    sys.path.insert(0, str(runner_root))

    from speckit_pro_runner.gates.payloads import build_installed_plugin_payloads

    dist_root = repo_root / "dist"
    build_installed_plugin_payloads(repo_root, dist_root)
    print("Built dist/claude/speckit-pro")
    print("Built dist/codex/speckit-pro")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
