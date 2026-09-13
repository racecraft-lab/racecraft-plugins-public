#!/usr/bin/env python3
"""Run a separately approved, bounded native trigger campaign."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from trigger_campaign_execution import CampaignRequest, qualify_pilot, reconcile_campaign, run_campaign
from trigger_comparison import read_json


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--launch-budget", type=int)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--baseline-description", type=Path)
    parser.add_argument("--candidate-description", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--pilot-evidence", type=Path)
    parser.add_argument("--qualify-pilot", type=Path, help="Replay a completed 48-launch pilot without provider access")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--reconcile", action="store_true", help="Inspect owned processes and retained artifacts without any native launches")
    args = parser.parse_args(argv)
    try:
        if args.qualify_pilot:
            profile = qualify_pilot(args.qualify_pilot)
            print(json.dumps({"qualified": True, **vars(profile)}, indent=2))
            return 0
        if any(getattr(args, name) is None for name in ("manifest", "approval", "launch_budget", "inventory", "candidate_description", "output_dir")):
            parser.error("execution requires manifest, approval, launch-budget, inventory, candidate-description and output-dir")
        manifest = read_json(args.manifest)
        descriptions = {"candidate": args.candidate_description}
        if "baseline" in manifest.get("arms", []):
            if args.baseline_description is None:
                parser.error("baseline arm requires --baseline-description")
            descriptions["baseline"] = args.baseline_description
        request = CampaignRequest(manifest, read_json(args.approval), args.launch_budget,
            args.inventory.resolve(), {arm: path.resolve() for arm, path in descriptions.items()},
            args.output_dir.resolve(), args.workers, args.pilot_evidence, args.timeout)
        result = reconcile_campaign(request) if args.reconcile else run_campaign(request)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(json.dumps({"complete": False, "qualification": False, "exit_code": 2, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
