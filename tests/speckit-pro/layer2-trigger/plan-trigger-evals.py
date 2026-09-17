#!/usr/bin/env python3
"""Print a provider-free launch selection; this command never runs providers."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LAYER = Path(__file__).resolve().parent
sys.path.insert(0, str(LAYER.parent / "lib"))
from trigger_inventory import InventoryError, load_inventory, plan_inventory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("full", "pr-core", "pilot"), default="full")
    parser.add_argument("--inventory", type=Path, default=LAYER / "case-inventory.json")
    parser.add_argument("--changed-skill", action="append", default=[])
    parser.add_argument("--changed-path", action="append", default=[])
    args = parser.parse_args()
    try:
        result = plan_inventory(load_inventory(args.inventory), args.inventory.parent, args.scope, changed_skills=args.changed_skill, changed_paths=args.changed_path, inventory_path=args.inventory)
    except (InventoryError, OSError, ValueError) as error:
        print(json.dumps({"schema_version": "trigger-selection/v1", "valid": False, "error": str(error)}))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
