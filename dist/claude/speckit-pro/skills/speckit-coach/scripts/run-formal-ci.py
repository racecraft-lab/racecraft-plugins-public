#!/usr/bin/env python3
"""Run an explicit formal checkpoint through the installed runner contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

PLUGIN_ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--checkpoint", choices=("plan", "planning", "final", "post"), required=True)
    parser.add_argument("--state")
    args = parser.parse_args()
    sys.path.insert(0, str(PLUGIN_ROOT))
    from speckit_pro_runner.formal.process import runtime_environment
    inputs = {"repo_root": str(args.repo_root.resolve()), "workflow_file": args.workflow, "spec_file": args.spec,
              "plan_file": args.plan, "checkpoint": args.checkpoint}
    if args.state:
        inputs["state_file"] = args.state
    request = {"schema_version": "1.0", "helper_id": "formal-check", "operation": "formal-check", "mode": "apply", "inputs": inputs}
    env = runtime_environment()
    env["PYTHONPATH"] = str(PLUGIN_ROOT)
    result = subprocess.run([sys.executable, "-m", "speckit_pro_runner"], input=json.dumps(request), capture_output=True,
                            text=True, cwd=PLUGIN_ROOT, env=env, check=False)
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    try:
        verdict = json.loads(result.stdout).get("data", {}).get("verdict")
    except ValueError:
        return 1
    return 0 if result.returncode == 0 and verdict in {"pass", "disabled"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
