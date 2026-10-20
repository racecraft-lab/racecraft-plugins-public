"""A scripted plan reviewer: answers the plan-review interview with fixed approvals, no human."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EVIDENCE = "artifacts/canary-review.txt"
CONFIRMATION = "artifacts/canary-confirmation.json"
APPROVER = "scripted-reviewer"
CORRECTION = "Scripted reviewer: the planning corrections for this finding are in the reviewed revision."


def scripted_approval(root: Path, feature_dir: str, digest: str, repository: str, source_commit: str) -> dict[str, Any]:
    """The approval object that confirms `digest` and passes every finding in the feature's inventory."""
    feature = root / feature_dir
    inventory = json.loads((feature / "planning-findings.json").read_text(encoding="utf-8"))
    (feature / EVIDENCE).parent.mkdir(parents=True, exist_ok=True)
    (feature / EVIDENCE).write_text("Scripted review of the planning bundle.\n", encoding="utf-8")
    evidence = f"{feature_dir}/{EVIDENCE}"
    confirmation = {"manifest_digest": digest, "decision": "approve", "approver": APPROVER, "time": "2026-01-01T00:00:00Z"}
    (feature / CONFIRMATION).write_text(json.dumps(confirmation), encoding="utf-8")
    return {
        "repository": repository, "planning_run": "canary-plan", "repair_runs": [], "source_commit": source_commit,
        "canary_issued": True, "supersedes": None, "superseded_by": None, "withdrawn_by": None,
        "reviewed_evidence": [evidence],
        "confirmation": {"reference": f"{feature_dir}/{CONFIRMATION}", **confirmation},
        "findings": {identity: {"requests": requests, "correction": CORRECTION,
                                "check": {"status": "passed", "manifest_digest": digest, "reference": evidence}}
                     for identity, requests in inventory.items()},
    }
