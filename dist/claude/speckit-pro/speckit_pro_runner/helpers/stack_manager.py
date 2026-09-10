"""Read-only qualification and command planning for existing-PR gh-stack linking."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from ..envelope import diagnostic, response

BRANCH = re.compile(r"(?!-)(?!.*\.\.)(?!.*//)[A-Za-z0-9._/-]{1,255}\Z")
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
QUALIFIED_VERSION = "0.1.1"


def probe(root: Path, argv: list[str]) -> dict[str, Any]:
    """Only invoke the two named CLIs; callers supply fixed read-only operations."""
    try:
        if argv[0] == "git":
            result = subprocess.run(["git", *argv[1:]], cwd=root, capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL, shell=False)
        elif argv[0] == "gh":
            result = subprocess.run(["gh", *argv[1:]], cwd=root, capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL, shell=False)
        else:
            raise ValueError("unknown manager probe")
        return {"argv": argv, "exit_status": result.returncode, "stdout_tail": result.stdout.strip(), "stderr_tail": result.stderr[-2048:].strip()}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"argv": argv, "exit_status": None, "stdout_tail": "", "stderr_tail": str(exc)}


def topology_inputs(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not 2 <= len(value) <= 50:
        raise ValueError("topology must contain 2 to 50 owned slices in review order")
    branches, slices = set(), set()
    for order, row in enumerate(value, 1):
        if not isinstance(row, dict) or set(row) - {"review_order", "slice_id", "branch", "base_branch", "pr_url"}:
            raise ValueError("invalid topology row fields")
        if row.get("review_order") != order or not isinstance(row.get("slice_id"), str) or not BRANCH.fullmatch(row["slice_id"]):
            raise ValueError("topology requires ordered, named slice ownership")
        for key in ("branch", "base_branch"):
            if not isinstance(row.get(key), str) or not BRANCH.fullmatch(row[key]):
                raise ValueError("invalid topology branch")
        if row["branch"] in branches or row["slice_id"] in slices or row["branch"] == row["base_branch"]:
            raise ValueError("topology contains duplicate ownership or a cycle")
        branches.add(row["branch"])
        slices.add(row["slice_id"])
    return [{**row, "status": "planned"} for row in value]


def initial_decision(topology: list[dict[str, Any]]) -> dict[str, Any]:
    reason = "Use packet-owned explicit PR management until both optional capabilities qualify"
    return {"schema_version": "stack-manager-decision.v1", "phase": "emission", "operation": "detect",
            "selected_manager": "explicit-gh", "reason": reason, "fallback_reason": reason, "fallback_allowed": True,
            "mutation_boundary": {"status": "none", "first_mutating_command_id": None, "fallback_after_boundary_allowed": False},
            "gh_stack": {"available": False, "supported": False, "reason": reason, "version": None,
                         "version_supported": False, "repo_enabled": False, "support_status": "missing", "invocation": [],
                         "skill_available": False, "skill_path": None, "skill_sha256": None},
            "read_only_proof": {"argv": ["gh", "stack", "--version"], "exit_status": None, "parsed": False, "matched_expected_topology": False},
            "topology_compatibility": {"compatible": False, "source": "pr-marker-plan", "mismatch_reason": "not inspected",
                                       "expected_order": [row["branch"] for row in topology], "observed_order": []},
            "command_plan": [{"id": "validate-packets", "action": "detect", "manager": "explicit-gh", "argv": ["gh", "stack", "--version"],
                              "mutates": False, "mutation_boundary": False, "preconditions": ["packet-owned PR metadata and validation"], "reason": reason}],
            "topology": {"pre_mutation": topology, "post_mutation": []}}


def fallback(decision: dict[str, Any], reason: str, status: str = "ambiguous") -> dict[str, Any]:
    decision.update(reason=reason, fallback_reason=reason)
    decision["gh_stack"].update(reason=reason, supported=False, support_status=status)
    return decision


def recovery_decision(root: Path, path: str) -> dict[str, Any] | None:
    if not isinstance(path, str) or not re.fullmatch(r"(?:specs/[^/]+/\.process/|docs/ai/specs/\.process/)[A-Za-z0-9._/-]+", path):
        raise ValueError("previous_decision must use the existing process evidence path contract")
    source = (root / path).resolve(strict=True)
    if not source.is_relative_to(root):
        raise ValueError("previous_decision must be inside WORKFLOW_ROOT")
    previous = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(previous, dict) or previous.get("schema_version") != "stack-manager-decision.v1":
        raise ValueError("invalid previous stack-manager decision")
    boundary = previous.get("mutation_boundary", {}).get("status")
    if boundary in ("none", "planned"):
        return None
    if boundary not in ("attempted", "partial_mutation", "partial_mutation_unknown"):
        raise ValueError("missing or invalid prior mutation boundary")
    if previous.get("selected_manager") not in ("gh-stack", "blocked"):
        raise ValueError("prior mutation must be reconciled through its recorded manager")
    reason = "Reconcile prior gh-stack mutation through the installed skill before retrying or switching managers"
    previous.update(selected_manager="blocked", reason=reason, fallback_allowed=False)
    previous["mutation_boundary"].update(status="partial_mutation_unknown", fallback_after_boundary_allowed=False)
    failed = {"command_id": "link-stack", "action": "link_stack", "manager": "gh-stack", "argv": ["gh", "stack", "link"],
              "mutates": True, "mutation_boundary": True, "started_at": "unknown", "finished_at": None, "exit_status": None,
              "stdout_tail": "", "stderr_tail": "Interrupted or failed mutation; consult the command log", "side_effect_class": "partial_mutation_unknown",
              "evidence_path": path}
    previous["recovery"] = {"status": "blocked", "reason": reason, "fallback_allowed": False, "selected_manager": "gh-stack",
                            "failed_operation": (previous.get("recovery") or {}).get("failed_operation", failed), "mutation_boundary": previous["mutation_boundary"],
                            "pre_mutation_topology": previous.get("topology", {}).get("pre_mutation", []),
                            "observed_post_failure_topology": previous.get("topology", {}).get("post_mutation", []),
                            "prior_successful_prs": previous.get("topology", {}).get("post_mutation", []),
                            "next_resume_boundary": "read-only remote topology reconciliation", "retry_policy": "reuse verified existing PR identities; never recreate PRs",
                            "blocked_event_id": "stack-manager-recovery", "resume_preflight": ["read installed gh-stack skill", "verify existing PR URLs and remote stack membership"],
                            "stale_result_policy": "remain_blocked", "evidence_paths": [path]}
    previous["command_plan"] = [{"id": "recover-stack", "action": "block", "manager": "gh-stack", "argv": ["gh", "stack", "view", "--json"],
                                  "mutates": False, "mutation_boundary": False, "preconditions": [reason], "reason": reason}]
    return previous


def qualify_tools(root: Path, skill: Any, decision: dict[str, Any]) -> bool:
    capability = decision["gh_stack"]
    path = Path(skill).expanduser() if isinstance(skill, str) and skill else None
    if path is None or path.name != "SKILL.md" or not path.is_file():
        fallback(decision, "The gh-stack skill is unavailable", "missing")
        return False
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or not re.search(r"(?m)^name:\s*gh-stack\s*$", text.split("---", 2)[1]):
        fallback(decision, "The supplied skill is not a gh-stack skill", "missing")
        return False
    capability.update(skill_available=True, skill_path=str(path.resolve()), skill_sha256=hashlib.sha256(text.encode()).hexdigest())
    version = probe(root, ["gh", "stack", "--version"])
    capability["invocation"].append(version["argv"])
    capability["available"] = version["exit_status"] == 0
    match = re.search(r"\b(\d+\.\d+\.\d+)\b", version["stdout_tail"])
    capability["version"] = match[1] if match else None
    capability["version_supported"] = capability["available"] and capability["version"] == QUALIFIED_VERSION
    if not capability["version_supported"]:
        fallback(decision, "gh-stack CLI is missing or its version is outside the qualified profile", "unsupported_version" if capability["available"] else "missing")
        return False
    help_result = probe(root, ["gh", "stack", "link", "--help"])
    capability["invocation"].append(help_result["argv"])
    if help_result["exit_status"] != 0 or not all(s in help_result["stdout_tail"] for s in ("gh stack link", "PR URLs", "--remote", "--base")):
        fallback(decision, "Installed gh-stack does not expose qualified existing-PR linking", "unsupported_version")
        return False
    return True


def qualify_repository(root: Path, repository: str, remote: str, decision: dict[str, Any]) -> bool:
    origin = probe(root, ["git", "remote", "get-url", remote])
    allowed = {f"https://github.com/{repository}", f"https://github.com/{repository}.git", f"git@github.com:{repository}.git"}
    if origin["exit_status"] != 0 or origin["stdout_tail"] not in allowed:
        fallback(decision, "Remote does not match the supported GitHub.com repository profile")
        return False
    repo_result = probe(root, ["gh", "api", f"repos/{repository}"])
    repo = json.loads(repo_result["stdout_tail"]) if repo_result["exit_status"] == 0 else {}
    if not isinstance(repo, dict) or repo.get("full_name") != repository or repo.get("archived") is not False or repo.get("fork") is not False or repo.get("permissions", {}).get("push") is not True:
        fallback(decision, "Repository ownership, write access, or topology is outside the qualified profile")
        return False
    proof = probe(root, ["gh", "api", f"repos/{repository}/stacks?per_page=1"])
    parsed = proof["exit_status"] == 0 and isinstance(json.loads(proof["stdout_tail"]), list)
    decision["read_only_proof"] = {**proof, "stdout_tail": proof["stdout_tail"][-2048:], "parsed": parsed, "matched_expected_topology": False}
    decision["gh_stack"]["repo_enabled"] = parsed
    if not parsed:
        fallback(decision, "Repository Stacks API is unavailable", "read_only_proof_failed")
    return parsed


def qualify_pr(root: Path, repository: str, row: dict[str, Any]) -> bool:
    match = re.fullmatch(rf"https://github\.com/{re.escape(repository)}/pull/([1-9][0-9]*)", row["pr_url"])
    if not match:
        return False
    result = probe(root, ["gh", "api", f"repos/{repository}/pulls/{match[1]}"])
    pr = json.loads(result["stdout_tail"]) if result["exit_status"] == 0 else {}
    if not isinstance(pr, dict) or pr.get("html_url") != row["pr_url"] or pr.get("state") != "open":
        return False
    if any(pr.get(side, {}).get("repo", {}).get("full_name") != repository for side in ("base", "head")):
        return False
    if pr["head"].get("ref") != row["branch"] or pr["base"].get("ref") != row["base_branch"] or pr["head"].get("sha") != row["head_sha"]:
        return False
    row.update(pr_number=int(match[1]), status="verified")
    return True


def qualify_topology(root: Path, repository: str, decision: dict[str, Any]) -> bool:
    previous = None
    for row in decision["topology"]["pre_mutation"]:
        if previous is not None and row["base_branch"] != previous:
            return False
        previous = row["branch"]
        head = probe(root, ["git", "rev-parse", "--verify", f"refs/heads/{row['branch']}^{{commit}}"])
        ancestry = probe(root, ["git", "merge-base", "--is-ancestor", row["base_branch"], row["branch"]])
        if head["exit_status"] != 0 or not re.fullmatch(r"[0-9a-f]{40,64}", head["stdout_tail"]) or ancestry["exit_status"] != 0:
            return False
        row["head_sha"] = head["stdout_tail"]
        if row.get("pr_url") and not qualify_pr(root, repository, row):
            return False
    decision["topology_compatibility"].update(compatible=True, mismatch_reason=None, observed_order=decision["topology_compatibility"]["expected_order"])
    decision["read_only_proof"]["matched_expected_topology"] = True
    return True


def detect(inputs: dict[str, Any]) -> dict[str, Any]:
    if set(inputs) - {"repo_root", "repository", "remote", "topology", "skill_path", "preference", "previous_decision"}:
        raise ValueError("unknown stack-manager input; arbitrary commands are not accepted")
    root = Path(inputs["repo_root"]).resolve(strict=True)
    repository, remote = inputs["repository"], inputs.get("remote", "origin")
    if not REPOSITORY.fullmatch(repository) or not BRANCH.fullmatch(remote):
        raise ValueError("invalid repository or remote")
    preference = inputs.get("preference", "auto")
    if preference not in ("auto", "explicit-gh"):
        raise ValueError("preference must be auto or explicit-gh")
    if inputs.get("previous_decision"):
        recovery = recovery_decision(root, inputs["previous_decision"])
        if recovery is not None:
            return recovery
    decision = initial_decision(topology_inputs(inputs["topology"]))
    if preference == "explicit-gh":
        return fallback(decision, "Operator selected current packet-owned PR management")
    try:
        if not qualify_tools(root, inputs.get("skill_path"), decision) or not qualify_repository(root, repository, remote, decision):
            return decision
        if not qualify_topology(root, repository, decision):
            return fallback(decision, "Branch or PR topology does not match the owned layer plan", "topology_incompatible")
    except (ValueError, KeyError, TypeError, AttributeError):
        return fallback(decision, "Capability or topology response was malformed", "read_only_proof_failed")
    decision.update(selected_manager="gh-stack", reason="CLI, skill, repository, and ordered topology qualify", fallback_reason=None)
    decision["gh_stack"].update(supported=True, support_status="supported", reason=decision["reason"])
    rows = decision["topology"]["pre_mutation"]
    if all(row.get("pr_url") for row in rows):
        decision["operation"] = "link"
        decision["mutation_boundary"].update(status="planned", first_mutating_command_id="link-stack")
        decision["command_plan"] = [{"id": "link-stack", "action": "link_stack", "manager": "gh-stack",
                                      "argv": ["gh", "stack", "link", "--remote", remote, "--base", rows[0]["base_branch"], *[r["pr_url"] for r in rows]],
                                      "mutates": True, "mutation_boundary": True, "preconditions": ["persist decision and attempted boundary", "current packet validation and release-readiness", "unchanged verified PR identities"],
                                      "reason": "Link verified existing PRs in declared order; preserve packet-owned titles and bodies"}]
    else:
        decision["command_plan"][0]["reason"] = "Create or refresh missing PRs through validated packet commands, persist identities, then rerun detection"
    return decision


def run_stack_manager_helper(entry: Any, request: Any) -> dict[str, Any]:
    try:
        if request.mode != "dry_run":
            raise ValueError("stack-manager selection is read-only; only dry_run is supported")
        decision = detect(request.inputs)
        return response("expected_failure" if decision["selected_manager"] == "blocked" else "ok", request_id=request.request_id,
                        data={"helper_id": entry.helper_id, "writes_state": False, "decision": decision})
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return response("input_error", request_id=request.request_id, data={"helper_id": entry.helper_id, "writes_state": False},
                        diagnostics=[diagnostic("stack_manager_configuration", str(exc))])
