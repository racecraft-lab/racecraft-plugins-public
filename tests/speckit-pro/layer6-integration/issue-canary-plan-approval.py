#!/usr/bin/env python3
"""Canary-only test issuer: records a canary-issued plan approval from the scripted reviewer.

Test tooling, never shipped. It works only in a host home the canary provisioned; production
verifiers refuse the record it writes (ADR 0016, ADR 0017). Nothing is signed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "speckit-pro"))
from scripted_plan_reviewer import scripted_approval
from runner_invocation import run_runner
from speckit_pro_runner.canary_trust import MARKER_NAME, MARKER_TEXT


def request(root: Path, home: Path, mode: str, **inputs: object) -> dict:
    body = dict(schema_version="1.0", helper_id="planning-approval", operation="planning-approval", mode=mode, inputs=inputs)
    reply = run_runner(body, cwd=root, extra_env={"HOME": str(home)})[1]
    if reply.get("status") != "ok":
        raise SystemExit(f"canary issuer: {json.dumps(reply.get('diagnostics', reply))}")
    return reply["data"]


def issue(root: Path, home: Path, feature_dir: str, workflow_file: str, repository: str, source_commit: str) -> str:
    """Record the scripted reviewer's approval as canary-issued; returns the record path."""
    inputs = {"feature_dir": feature_dir, "workflow_file": workflow_file}
    digest = request(root, home, "read_only", action="manifest", **inputs)["manifest_digest"]
    approval = scripted_approval(root, feature_dir, digest, repository, source_commit)
    return request(root, home, "apply", action="record", approval=approval, **inputs)["record_path"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, required=True, help="the canary's isolated host home")
    parser.add_argument("--provision", action="store_true", help="mark --home as a canary home first")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--feature-dir", required=True)
    parser.add_argument("--workflow-file", required=True)
    parser.add_argument("--repository", required=True, help="owner/name as spelled in the origin URL")
    parser.add_argument("--source-commit", help="the reviewed commit; default: HEAD of --root")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    commit = args.source_commit or subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                                                  capture_output=True, text=True, check=True).stdout.strip()
    if args.provision:
        args.home.mkdir(parents=True, exist_ok=True)
        (args.home / MARKER_NAME).write_text(MARKER_TEXT, encoding="utf-8")
    print(issue(root, args.home, args.feature_dir, args.workflow_file, args.repository, commit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
