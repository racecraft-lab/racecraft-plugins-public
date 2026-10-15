"""Recorded planning revisions shared by both hosts; no protected authority claim."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ..atomic_write import snapshot_write_target, write_bytes_atomic
from ..canonical_json import canonical_bytes
from ..formal.primitives import CATALOG_PATH
from ..quality_gates import SHIPPED_DEFAULTS
from ..strict_input import next_fence, require_fields, require_text, unique_object
from ..task_execution import owned_path, task_definitions
from ..trusted_io import trusted_tree_snapshot
from .execution_requests import Refusal, run_contained_helper

# Inventory roots are runner-owned, never a caller-selected subset. Feature additions
# are authoritative unless explicitly classified as execution outputs here.
PROJECT_INPUTS = (".specify/memory", ".specify/templates", ".specify/extensions", ".specify/presets",
                  ".specify/quality-gates.json", ".specify/config.json", ".specify/extensions.yml",
                  ".specify/scripts", CATALOG_PATH, "AGENTS.md")
RUNTIME = {"artifacts", "plan-approvals", ".process", "autopilot-state.json", "task-results.json",
           "execution-control.json", "verification-record.json"}
EXECUTION_SECTIONS = {"Implementation Progress", "Feedback Sweep Log"}


def captured(root: Path, relative: str) -> bytes:
    entry = trusted_tree_snapshot(root / owned_path(relative, root), root)[Path()]
    if isinstance(entry[1], bytes):
        return entry[1]
    raise ValueError(f"planning input must be a readable file: {relative}")


def normalized(name: str, content: bytes, workflow: str) -> bytes:
    if name.endswith("/tasks.md"):
        return task_definitions(content.decode("utf-8")).encode("utf-8")
    if name != workflow:
        return content
    kept, skipping = [], 0
    fence = None
    for line in content.decode("utf-8").splitlines(keepends=True):
        heading = None if fence else re.match(r"^(#{1,6}) +(.+?)\s*$", line)
        fence = next_fence(fence, line)
        if heading and skipping and len(heading[1]) <= skipping:
            skipping = 0
        if heading and heading[2] in EXECUTION_SECTIONS:
            skipping = len(heading[1])
        if not skipping and (fence or not re.match(r"^\| \*\*(Stage|Draft PR)\*\* \|", line)):
            # Checked spelling is equivalent; checked and unchecked choices are not.
            kept.append(line if fence else re.sub(r"^(\s*-\s+\[)[xX](\])", r"\1x\2", line))
    return "".join(kept).encode("utf-8")


def planning_manifest(root: Path, feature: str, workflow: str) -> dict[str, Any]:
    feature = owned_path(feature, root)
    workflow = owned_path(workflow, root)
    files: dict[str, bytes | None] = {}
    for base in (feature, *PROJECT_INPUTS):
        path = root / base
        if not path.exists():
            files[base] = None
            continue
        if not path.is_dir():
            files[base] = captured(root, base)
            continue
        for relative, (_, content) in trusted_tree_snapshot(path, root).items():
            if content is not None and relative.parts[0] not in RUNTIME:
                files[(path / relative).relative_to(root).as_posix()] = content
    for name in ("spec.md", "plan.md", "tasks.md"):
        files[feature + "/" + name] = captured(root, feature + "/" + name)
    sidecar = feature + "/.process/task-execution.json"
    files[sidecar] = captured(root, sidecar) if (root / sidecar).exists() else None
    files[workflow] = captured(root, workflow)
    catalog_content = files.get(CATALOG_PATH)
    if catalog_content is not None:
        catalog = json.loads(catalog_content, object_pairs_hook=unique_object)
        for model in catalog["models"].values():
            for name in model["inputs"]:
                files[name] = captured(root, name)
    hashes = {name: hashlib.sha256(normalized(name, content, workflow)).hexdigest()
                if content is not None else None for name, content in sorted(files.items())}
    manifest = {"schema_version": "planning-manifest/v1", "files": hashes, "verification_defaults": SHIPPED_DEFAULTS}
    return {"manifest": manifest, "manifest_digest": hashlib.sha256(canonical_bytes(manifest)).hexdigest()}


def evidence(root: Path, reference: str) -> dict[str, str]:
    return {"reference": owned_path(reference, root), "sha256": hashlib.sha256(captured(root, reference)).hexdigest()}


def checked_findings(root: Path, feature: str, findings: Any, revision: str) -> dict[str, Any]:
    inventory = json.loads(captured(root, feature + "/planning-findings.json"), object_pairs_hook=unique_object)
    if not isinstance(inventory, dict) or not isinstance(findings, dict) or set(inventory) != set(findings):
        raise ValueError("findings must cover exactly the authoritative planning-findings.json inventory")
    for identity, requests in inventory.items():
        require_text(identity, "finding identity")
        if not isinstance(requests, list) or not requests or len(set(requests)) != len(requests):
            raise ValueError(f"{identity}: requests must be unique non-empty strings")
        for request in requests:
            require_text(request, identity + " request")
        finding = require_fields(findings[identity], {"requests", "correction", "check"}, identity)
        require_text(finding["correction"], identity + " correction")
        check = require_fields(finding["check"], {"status", "manifest_digest", "reference"}, identity + " check")
        if finding["requests"] != requests or check["status"] != "passed" or check["manifest_digest"] != revision:
            raise ValueError(f"{identity}: missing correction or passing check for the final revision")
        evidence(root, check["reference"])
    return findings


def approval_record(root: Path, feature: str, approval: Any, binding: dict[str, Any]) -> dict[str, Any]:
    record = require_fields(approval, {"repository", "planning_run", "repair_runs", "source_commit", "canary_issued",
                                      "supersedes", "superseded_by", "withdrawn_by", "reviewed_evidence", "confirmation", "findings"}, "approval")
    for key in ("repository", "planning_run", "source_commit"):
        require_text(record[key], key)
    if not re.fullmatch(r"[0-9a-f]{40}", record["source_commit"]):
        raise ValueError("source_commit must identify the reviewed source revision")
    if record["canary_issued"] is not False or record["superseded_by"] is not None or record["withdrawn_by"] is not None:
        raise ValueError("production approval refuses canary-issued, superseded or withdrawn records")
    if not isinstance(record["repair_runs"], list):
        raise ValueError("repair_runs must be a list")
    for run in record["repair_runs"]:
        require_text(run, "repair run")
    confirmation = require_fields(record["confirmation"], {"reference", "manifest_digest", "decision", "approver", "time"}, "confirmation")
    for key in ("approver", "time"):
        require_text(confirmation[key], "confirmation " + key)
    if datetime.fromisoformat(confirmation["time"].replace("Z", "+00:00")).tzinfo is None:
        raise ValueError("confirmation time requires an explicit timezone")
    if confirmation["decision"] != "approve" or confirmation["manifest_digest"] != binding["manifest_digest"]:
        raise ValueError("confirmation must explicitly approve the final manifest_digest")
    supplied = json.loads(captured(root, confirmation["reference"]), object_pairs_hook=unique_object)
    if supplied != {k: v for k, v in confirmation.items() if k != "reference"}:
        raise ValueError("confirmation reference does not match the recorded decision")
    refs = record["reviewed_evidence"]
    if not isinstance(refs, list) or not refs or len(set(refs)) != len(refs):
        raise ValueError("reviewed_evidence requires unique repository-relative references")
    reviewed = [evidence(root, ref) for ref in refs]
    reviewed.append(evidence(root, confirmation["reference"]))
    if record["supersedes"] is not None:
        evidence(root, record["supersedes"])
    findings = checked_findings(root, feature, record["findings"], binding["manifest_digest"])
    reviewed.extend(evidence(root, finding["check"]["reference"]) for finding in findings.values())
    return {**record, **binding, "schema_version": "plan-approval/v1", "assurance": "recorded",
            "feature_dir": feature, "evidence": reviewed, "findings": findings}


def refuse_superseded(root: Path, path: str) -> None:
    for _, content in trusted_tree_snapshot((root / path).parent, root).values():
        if content is not None:
            peer = json.loads(content, object_pairs_hook=unique_object)
            if not isinstance(peer, dict) or peer.get("supersedes") == path:
                raise ValueError("approval has a subsequent supersession or unreadable history; return to plan review")


def planning_approval(root: Path, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    action = inputs.get("action")
    required = {"feature_dir", "workflow_file", "action"} | ({"approval"} if action == "record" else set())
    fields = require_fields({k: v for k, v in inputs.items() if k != "repo_root"}, required, "planning approval inputs")
    feature = owned_path(fields["feature_dir"], root)
    binding = planning_manifest(root, feature, fields["workflow_file"])
    if action == "manifest" and mode == "read_only":
        return {**binding, "writes_state": False}
    path = feature + "/plan-approvals/" + binding["manifest_digest"] + ".json"
    target = root / path
    snapshot = snapshot_write_target(target, root)
    if action == "verify" and mode == "read_only":
        refuse_superseded(root, path)
        stored = json.loads(captured(root, path), object_pairs_hook=unique_object)
        computed = {"manifest", "manifest_digest", "schema_version", "assurance", "feature_dir", "evidence"}
        candidate = {k: v for k, v in stored.items() if k not in computed}
        record = approval_record(root, feature, candidate, binding)
        if record != stored:
            raise ValueError("record bindings or reviewed evidence changed; return to plan review")
    elif action == "record" and mode in {"dry_run", "apply"}:
        record = approval_record(root, feature, fields["approval"], binding)
        if target.exists() and json.loads(captured(root, path)) != record:
            raise ValueError("approval already exists; preserve the original decision")
        if mode == "apply":
            write_bytes_atomic(target, canonical_bytes(record) + b"\n", trust_root=root, expected_snapshot=snapshot)
    else:
        raise ValueError("use manifest/verify in read_only, or record in dry_run/apply")
    return {"record": record, "record_path": path, "writes_state": mode == "apply"}


def run_planning_approval_helper(entry: Any, request: Any) -> dict[str, Any]:
    return run_contained_helper(entry, request, planning_approval, Refusal(
        "invalid_planning_approval", "Correct the named planning approval field and return to plan review.",
        ["Repair the planning inputs or review evidence.", "Retry planning-approval."]))
