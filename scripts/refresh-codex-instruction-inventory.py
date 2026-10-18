#!/usr/bin/env python3
"""Refresh repository proof data after reviewing Codex instruction changes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tests/speckit-pro/lib"))

from codex_instruction_review import REVIEW_INVENTORY, instruction_inventory  # noqa: E402
from host_skill_views import host_skill_root  # noqa: E402


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    inventory = {
        "skills": instruction_inventory(host_skill_root("codex")),
        "agents": instruction_inventory(REPO_ROOT / "speckit-pro/codex-agents"),
    }
    REVIEW_INVENTORY.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Wrote instruction inventory. Review source changes and the inventory diff together.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
