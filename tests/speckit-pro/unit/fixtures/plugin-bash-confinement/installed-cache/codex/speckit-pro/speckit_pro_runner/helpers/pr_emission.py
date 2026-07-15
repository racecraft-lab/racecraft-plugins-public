"""PR body, packet, and command-planning helpers."""

from __future__ import annotations

import json
import hashlib
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from ..envelope import diagnostic, response
from .mutation import dirty_worktree_diagnostic, empty_mutation, operation_records, run_mutation_helper
from .read_only import (
    find_repo_root,
    is_relative_to,
    load_pr_packet_schema,
    pr_packet_schema_failures,
    protected_body_sha256,
    resolve_input_path,
    trusted_dir_exists,
    trusted_file_exists,
)


PR_PACKET_INPUT_FIELDS = frozenset(
    "base_branch base_ref how_to_review how_to_uat known_gaps packet_id release_note scope_evidence "
    "source_feature_dir source_markers summary title_description title_scope title_type uat_runbook uat_source "
    "verification_evidence what_changed why_it_matters".split()
)
_PACKET_REQUIRED = PR_PACKET_INPUT_FIELDS - {"release_note"}
_HEADINGS = (
    "Summary",
    "What Changed",
    "Why It Matters",
    "How To Review",
    "How To UAT",
    "Verification",
    "Scope",
    "Known Gaps",
)
_EDITABLE = tuple(
    {
        "field_id": field_id,
        "heading": heading,
        "start_marker": f"<!-- speckit-pro-editable:{field_id}:start -->",
        "end_marker": f"<!-- speckit-pro-editable:{field_id}:end -->",
    }
    for field_id, heading in (
        ("summary", "Summary"),
        ("what_changed", "What Changed"),
        ("why_it_matters", "Why It Matters"),
    )
)
_TITLE_TYPES = {"feat", "fix", "chore", "docs", "refactor", "test"}
_PATH = re.compile(r"^[A-Za-z0-9._-][A-Za-z0-9._/-]*$")
_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
_SCOPE = re.compile(r"^(?:[a-z][a-z0-9-]*|[A-Z]+-[A-Z0-9][A-Z0-9-]*)$")
_SHA_LIKE = re.compile(r"^[0-9a-fA-F]{7,64}$")


def run_pr_emission_helper(entry: Any, request: Any) -> dict[str, Any]:
    if request.helper_id == "generate-pr-body":
        return generate_pr_body(entry, request)
    if request.helper_id == "pr-packet-output":
        return generate_pr_packet(entry, request)
    if request.helper_id in {"multi-pr-emission", "restack", "detect-stack-manager-plan"}:
        return plan_commands(entry, request)
    return generated_output(entry, request)


def generate_pr_body(entry: Any, request: Any) -> dict[str, Any]:
    output_path = request.inputs.get("output_path")
    title = request.inputs.get("title")
    sections = request.inputs.get("sections", [])
    if not isinstance(output_path, str) or not output_path:
        return input_error(request, "output_path is required")
    if not isinstance(title, str) or not title:
        return input_error(request, "title is required")
    if not isinstance(sections, list) or not all(isinstance(section, str) and section for section in sections):
        return input_error(request, "sections must be an array of non-empty strings")

    operation = {
        "operation_id": "generate-pr-body",
        "kind": "write_file",
        "target": output_path,
        "content": build_pr_body(title, sections),
    }
    return run_mutation_helper(entry, request, operations=[operation])


def generate_pr_packet(entry: Any, request: Any) -> dict[str, Any]:
    invalid = _packet_input_failure(request.inputs)
    if invalid:
        return input_error(request, invalid[0], details=invalid[1])
    inputs = request.inputs
    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        return response(
            "missing_prerequisite",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "missing_prerequisite",
                    "could not locate repository root for PR packet output",
                    remediation_summary="Run packet generation from a SpecKit project root.",
                    remediation_actions=["Change to the repository root.", "Retry the structured request."],
                )
            ],
        )

    feature_dir = inputs["source_feature_dir"]
    feature_path = resolve_input_path(feature_dir, repo_root)
    uat_path = resolve_input_path(inputs["uat_source"], repo_root)
    if not is_relative_to(feature_path, repo_root) or not is_relative_to(uat_path, repo_root):
        return input_error(request, "packet evidence paths must stay inside the repository")
    prefix = f"{feature_dir}/.process/pr-packets/{inputs['packet_id']}"
    body_path, packet_path = f"{prefix}.md", f"{prefix}.json"
    validation_path = f"{prefix}/validation.json"
    git_base_ref = (
        f"refs/remotes/origin/{inputs['base_branch']}"
        if inputs["base_ref"].startswith("origin/")
        else f"refs/heads/{inputs['base_branch']}"
    )
    output_paths = [resolve_input_path(body_path, repo_root), resolve_input_path(packet_path, repo_root)]
    if any(path.is_symlink() for path in output_paths):
        return input_error(request, "pr-packet-output refuses symlink output paths")
    output_exists = [path.exists() for path in output_paths]
    if any(output_exists):
        return _existing_packet_output(entry, request, body_path, packet_path, output_paths)
    dirty = dirty_worktree_diagnostic(inputs, repo_root)
    if dirty is not None:
        dirty = diagnostic(
            dirty["code"],
            "pr-packet-output requires a clean worktree in both dry_run and apply modes because packet scope is derived from committed base...HEAD evidence",
            details=dirty.get("details"),
            remediation_summary="Restore a clean committed worktree before packet planning or generation.",
            remediation_actions=[
                "Commit or stash unrelated changes and remove untracked files.",
                "Retry dry_run or apply only after git status is clean.",
            ],
        )
        mutation = empty_mutation(request.mode)
        mutation["mutation_status"] = "blocked"
        mutation["dirty_worktree"] = dirty["code"] == "dirty_worktree"
        return response(
            "expected_failure",
            request_id=request.request_id,
            data={
                "helper_id": entry.helper_id,
                "operation": entry.operation,
                "mode": request.mode,
                "promotion_status": entry.promotion_status,
                "comparison_mode": entry.comparison_mode,
                "writes_state": False,
                "mutation": mutation,
            },
            diagnostics=[dirty],
        )
    evidence_paths = [
        feature_path / "spec.md",
        uat_path,
        *[resolve_input_path(item["source"], repo_root) for item in inputs["verification_evidence"]],
        *[resolve_input_path(item["source"], repo_root) for item in inputs["source_markers"]],
    ]
    if request.mode == "apply" and (
        not trusted_dir_exists(feature_path, repo_root)
        or any(not trusted_file_exists(path, repo_root) for path in evidence_paths)
    ):
        return input_error(
            request,
            "packet apply requires readable trusted spec, UAT, verification, and marker sources",
            details={"source_feature_dir": feature_dir},
        )
    git_context, git_error = _git_packet_context(repo_root, git_base_ref)
    if git_error:
        return input_error(request, "packet git context is unavailable", details={"git_error": git_error})
    assert git_context is not None
    head_branch = git_context["head_branch"]
    if head_branch == inputs["base_branch"]:
        return input_error(
            request,
            "packet head branch must differ from its base branch",
            details={"head_branch": head_branch, "base_branch": inputs["base_branch"]},
        )
    changed_files = git_context["changed_files"]
    changed_files = sorted({*changed_files, body_path, packet_path})
    unsafe = [path for path in changed_files if not _safe_path(path)]
    if unsafe:
        return input_error(request, "git diff contains packet-unsafe paths", details={"changed_files": unsafe[:5]})

    title = f"{inputs['title_type']}({inputs['title_scope']}): {inputs['title_description']}"
    body = _render_packet_body(inputs, packet_path, changed_files)
    packet = _packet_record(
        inputs,
        body_path,
        validation_path,
        head_branch,
        title,
        body,
        changed_files,
        git_context,
    )
    schema, schema_error = load_pr_packet_schema()
    if schema is None:
        return response(
            "missing_prerequisite",
            request_id=request.request_id,
            diagnostics=[diagnostic("missing_prerequisite", schema_error or "PR packet schema is unavailable")],
        )
    failures = pr_packet_schema_failures(packet, schema)
    if failures:
        return input_error(request, "derived PR packet violates its schema", details={"failures": failures[:8]})

    operations = [
        {
            "operation_id": "pr-packet-output:body",
            "kind": "write_file",
            "target": body_path,
            "content": body,
            "expected_absent": True,
        },
        {
            "operation_id": "pr-packet-output:packet",
            "kind": "write_file",
            "target": packet_path,
            "content": json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            "expected_absent": True,
        },
    ]
    return run_mutation_helper(
        entry,
        request,
        operations=operations,
        extra_data={
            "body_file": body_path,
            "changed_file_count": len(changed_files),
            "generated_title": title,
            "packet_id": inputs["packet_id"],
            "packet_path": packet_path,
            "validation_result_path": validation_path,
        },
    )


def _packet_input_failure(inputs: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    extra = sorted(set(inputs) - PR_PACKET_INPUT_FIELDS)
    missing = sorted(_PACKET_REQUIRED - set(inputs))
    if extra or missing:
        return "pr-packet-output fields do not match its contract", {"unexpected_fields": extra, "missing_fields": missing}
    feature_dir, packet_id = inputs["source_feature_dir"], inputs["packet_id"]
    if not isinstance(feature_dir, str) or re.fullmatch(r"specs/[A-Za-z0-9][A-Za-z0-9._-]*", feature_dir) is None:
        return "source_feature_dir must match specs/<feature>", {"field": "source_feature_dir"}
    if not isinstance(packet_id, str) or re.fullmatch(r"[a-z0-9][a-z0-9._-]*", packet_id) is None:
        return "packet_id must be a lowercase safe token", {"field": "packet_id"}

    strings = (
        "base_branch",
        "base_ref",
        "how_to_uat",
        "summary",
        "title_description",
        "title_scope",
        "title_type",
        "uat_runbook",
        "uat_source",
        "why_it_matters",
    )
    bad_string = next((field for field in strings if not isinstance(inputs[field], str) or not inputs[field].strip()), None)
    if bad_string:
        return "packet string inputs must be non-empty", {"field": bad_string}
    if inputs["title_type"] not in _TITLE_TYPES or _SCOPE.fullmatch(inputs["title_scope"]) is None:
        return "packet title type or scope is unsupported", {"field": "title"}
    scope_match = re.match(r"^([A-Za-z][A-Za-z0-9]*-[A-Za-z0-9]+)(?:-|$)", PurePosixPath(feature_dir).name)
    if scope_match is None or inputs["title_scope"].casefold() != scope_match.group(1).casefold():
        return "title_scope must match the feature identifier", {"field": "title_scope"}
    if len(inputs["title_description"]) < 8:
        return "title_description must be a public action phrase", {"field": "title_description"}
    if "\n" in inputs["title_description"] or "\r" in inputs["title_description"]:
        return "title_description must be a single line", {"field": "title_description"}
    if not _safe_ref(inputs["base_ref"]) or not _safe_ref(inputs["base_branch"]):
        return "base_ref and base_branch must be safe git refs", {"field": "base_ref"}
    if _SHA_LIKE.fullmatch(inputs["base_branch"]) or _SHA_LIKE.fullmatch(inputs["base_ref"].removeprefix("origin/")):
        return "base_ref and base_branch must identify a branch, not an object ID", {"field": "base_ref"}
    if not _base_ref_matches(inputs["base_ref"], inputs["base_branch"]):
        return "base_ref must be <base_branch> or origin/<base_branch>", {"field": "base_ref"}
    if not _safe_path(inputs["uat_source"]):
        return "uat_source must be a safe repo-relative path", {"field": "uat_source"}

    for field in ("what_changed", "how_to_review", "known_gaps"):
        if not _string_list(inputs[field]):
            return "packet prose arrays must contain non-empty single lines", {"field": field}
    scope = inputs["scope_evidence"]
    if not isinstance(scope, dict) or set(scope) != {"reviewable_loc", "production_files", "budget_result", "non_goals"}:
        return "scope_evidence fields do not match the contract", {"field": "scope_evidence"}
    if not _string_list(scope["non_goals"]):
        return "scope_evidence.non_goals must contain non-empty single lines", {"field": "scope_evidence.non_goals"}
    if not _record_list(inputs["verification_evidence"], {"kind", "source", "summary"}, {"result"}):
        return "verification_evidence records are invalid", {"field": "verification_evidence"}
    if not _record_list(inputs["source_markers"], {"marker_id", "rendered_text", "source"}, set()):
        return "source_markers records are invalid", {"field": "source_markers"}
    evidence_sources = [item["source"] for item in inputs["verification_evidence"] + inputs["source_markers"]]
    if any(not _safe_path(source) for source in evidence_sources):
        return "verification and marker sources must be repo-relative paths", {"field": "source"}
    release_note = inputs.get("release_note")
    if inputs["title_type"] in {"feat", "fix"} and (not isinstance(release_note, str) or not release_note.strip()):
        return "feat and fix packets require release_note", {"field": "release_note"}
    if release_note is not None and (not isinstance(release_note, str) or not release_note.strip()):
        return "release_note must be a non-empty string when provided", {"field": "release_note"}

    prose = {key: inputs[key] for key in ("summary", "what_changed", "why_it_matters", "how_to_review", "how_to_uat", "uat_runbook", "verification_evidence", "scope_evidence", "known_gaps", "source_markers")}
    if release_note is not None:
        prose["release_note"] = release_note
    if any(_reserved_markdown(value) for value in _strings(prose)):
        return "packet prose contains reserved Markdown", {"field": "prose"}
    return None


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.strip() and "\n" not in item and "\r" not in item for item in value
    )


def _record_list(value: Any, required: set[str], optional: set[str]) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(record, dict)
        and required <= set(record) <= required | optional
        and all(isinstance(item, str) and item.strip() and "\n" not in item and "\r" not in item for item in record.values())
        for record in value
    )


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for child in value.values() for item in _strings(child)]
    if isinstance(value, list):
        return [item for child in value for item in _strings(child)]
    return []


def _reserved_markdown(value: str) -> bool:
    return "<!-- speckit-pro" in value or "```" in value or any(re.match(r"^#{1,2}\s+", line) for line in value.splitlines())


def _safe_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and "\\" not in value and _PATH.fullmatch(value) is not None and not path.is_absolute() and ".." not in path.parts


def _safe_ref(value: str) -> bool:
    return _REF.fullmatch(value) is not None and ".." not in value and "//" not in value and not value.endswith(("/", "."))


def _base_ref_matches(base_ref: str, base_branch: str) -> bool:
    return base_ref in {base_branch, f"origin/{base_branch}"}


def _existing_packet_output(
    entry: Any,
    request: Any,
    body_path: str,
    packet_path: str,
    output_paths: list[Path],
) -> dict[str, Any]:
    body_exists, packet_exists = (path.is_file() for path in output_paths)
    complete = body_exists and packet_exists
    mutation = empty_mutation(request.mode)
    mutation["mutation_status"] = "blocked"
    code = "existing_pr_packet_output" if complete else "partial_pr_packet_output"
    actions = [
        "Inspect and remove both existing body and packet artifacts; never authorize reuse.",
        "If either artifact is tracked, commit its deletion before regeneration.",
        "Restore a clean committed worktree, then retry pr-packet-output with the grounded request.",
    ]
    diag = diagnostic(
        code,
        "PR packet output already exists and cannot be reused or overwritten"
        if complete
        else "PR packet output is incomplete and cannot be reused or overwritten",
        details={
            "body_file": body_path,
            "body_exists": body_exists,
            "packet_path": packet_path,
            "packet_exists": packet_exists,
        },
        remediation_summary="Remove all existing packet artifacts and commit any tracked deletion before clean regeneration.",
        remediation_actions=actions,
    )
    return response(
        "expected_failure",
        request_id=request.request_id,
        data={
            "helper_id": entry.helper_id,
            "operation": entry.operation,
            "mode": request.mode,
            "promotion_status": entry.promotion_status,
            "comparison_mode": entry.comparison_mode,
            "writes_state": False,
            "body_file": body_path,
            "packet_path": packet_path,
            "mutation": mutation,
        },
        diagnostics=[diag],
    )


def _git_packet_context(
    repo_root: Path, base_ref: str
) -> tuple[dict[str, Any] | None, str | None]:
    def run(command: list[str]) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", "-C", str(repo_root), *command],
            capture_output=True,
            shell=False,
            check=False,
            timeout=30,
        )

    try:
        initial = [
            run(["symbolic-ref", "--quiet", "--short", "HEAD"]),
            run(["rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}"]),
            run(["rev-parse", "--verify", "--quiet", "HEAD^{commit}"]),
        ]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, type(exc).__name__
    if any(result.returncode != 0 for result in initial):
        return None, "detached_head_or_undiffable_base"
    try:
        branch = initial[0].stdout.decode("utf-8", errors="strict").strip()
        base_sha = initial[1].stdout.decode("ascii", errors="strict").strip()
        source_head_sha = initial[2].stdout.decode("ascii", errors="strict").strip()
    except UnicodeDecodeError:
        return None, "unsupported_git_metadata_encoding"
    if not _safe_ref(branch):
        return None, "unsafe_head_branch"

    try:
        diff_results = [
            run(["diff", "--name-only", "-z", f"{base_sha}...{source_head_sha}", "--"]),
            run(["diff", "--binary", "--full-index", f"{base_sha}...{source_head_sha}", "--"]),
        ]
        final = [
            run(["symbolic-ref", "--quiet", "--short", "HEAD"]),
            run(["rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}"]),
            run(["rev-parse", "--verify", "--quiet", "HEAD^{commit}"]),
        ]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, type(exc).__name__
    if any(result.returncode != 0 for result in (*diff_results, *final)):
        return None, "git_refs_changed_during_packet_generation"
    try:
        changed_files = [
            path
            for path in diff_results[0].stdout.decode("utf-8", errors="strict").split("\0")
            if path
        ]
        final_values = (
            final[0].stdout.decode("utf-8", errors="strict").strip(),
            final[1].stdout.decode("ascii", errors="strict").strip(),
            final[2].stdout.decode("ascii", errors="strict").strip(),
        )
    except UnicodeDecodeError:
        return None, "unsupported_git_path_encoding"
    if final_values != (branch, base_sha, source_head_sha):
        return None, "git_refs_changed_during_packet_generation"
    return {
        "base_ref": base_ref,
        "base_sha": base_sha,
        "source_head_sha": source_head_sha,
        "source_diff_sha256": hashlib.sha256(diff_results[1].stdout).hexdigest(),
        "head_branch": branch,
        "changed_files": changed_files,
    }, None


def _render_packet_body(inputs: dict[str, Any], packet_path: str, changed_files: list[str]) -> str:
    scope = inputs["scope_evidence"]
    evidence = [
        f"- {item['summary']} Source: {item['source']}." + (f" Result: {item['result']}." if item.get("result") else "")
        for item in inputs["verification_evidence"]
    ]
    evidence.extend(marker["rendered_text"] for marker in inputs["source_markers"])
    lines = [f"<!-- speckit-pro-review-packet-source: {packet_path} -->", ""]
    for heading, content, editable in (
        ("Summary", [inputs["summary"].strip()], "summary"),
        ("What Changed", [f"- {item}" for item in inputs["what_changed"]], "what_changed"),
        ("Why It Matters", [inputs["why_it_matters"].strip()], "why_it_matters"),
    ):
        lines.extend([f"## {heading}", "", f"<!-- speckit-pro-editable:{editable}:start -->", *content, f"<!-- speckit-pro-editable:{editable}:end -->", ""])
    lines.extend(
        [
            "## How To Review",
            "",
            *[f"{index}. {item}" for index, item in enumerate(inputs["how_to_review"], 1)],
            "",
            "## How To UAT",
            "",
            inputs["how_to_uat"].strip(),
            "",
            "## UAT Runbook",
            "",
            inputs["uat_runbook"].strip(),
            "",
            "## Verification",
            "",
            *evidence,
            "",
            "## Scope",
            "",
            f"- Reviewable LOC: {scope['reviewable_loc']}",
            f"- Production files: {scope['production_files']}",
            f"- Total files: {len(changed_files)}",
            f"- Budget result: {scope['budget_result']}",
            "- Changed files:",
            *[f"  - `{path}`" for path in changed_files],
            "- Non-goals:",
            *[f"  - {item}" for item in scope["non_goals"]],
            "",
            "## Known Gaps",
            "",
            *[f"- {item}" for item in inputs["known_gaps"]],
        ]
    )
    if inputs.get("release_note"):
        lines.extend(["", "```release-note", inputs["release_note"].strip(), "```"])
    return "\n".join(lines).rstrip() + "\n"


def _packet_record(
    inputs: dict[str, Any],
    body_path: str,
    validation_path: str,
    head_branch: str,
    title: str,
    body: str,
    changed_files: list[str],
    git_context: dict[str, Any],
) -> dict[str, Any]:
    feature_dir, scope = inputs["source_feature_dir"], inputs["scope_evidence"]
    return {
        "schema_version": "1.1.0",
        "packet_id": inputs["packet_id"],
        "mode": "single",
        "target": {"base_branch": inputs["base_branch"], "head_branch": head_branch},
        "source_revision": {
            "base_ref": git_context["base_ref"],
            "base_sha": git_context["base_sha"],
            "source_head_sha": git_context["source_head_sha"],
            "source_diff_fingerprint": {
                "algorithm": "sha256",
                "value": git_context["source_diff_sha256"],
                "normalization": "git diff --binary --full-index <base-sha>...<source-head-sha> -- at packet generation",
            },
        },
        "source_feature_dir": feature_dir,
        "generated_title": {
            "value": title,
            "type": inputs["title_type"],
            "scope": inputs["title_scope"],
            "description": inputs["title_description"],
            "source_evidence": {
                "kind": "feature_spec",
                "source": f"{feature_dir}/spec.md",
                "summary": "Feature title and requested action define the public PR title.",
            },
            "rejected_candidates": [
                {"value": PurePosixPath(feature_dir).name, "reason": "Feature directories are evidence, not titles."},
                {"value": head_branch, "reason": "Branch names are target metadata, not title descriptions."},
            ],
        },
        "body_file": body_path,
        "required_headings": list(_HEADINGS),
        "verification_evidence": inputs["verification_evidence"],
        "scope_evidence": {
            "reviewable_loc": scope["reviewable_loc"],
            "production_files": scope["production_files"],
            "total_files": len(changed_files),
            "budget_result": scope["budget_result"],
            "changed_files": changed_files,
            "non_goals": scope["non_goals"],
        },
        "uat": {
            "how_to_uat": inputs["how_to_uat"],
            "uat_runbook_heading": "## UAT Runbook",
            "uat_source": inputs["uat_source"],
        },
        "source_markers": inputs["source_markers"],
        "editable_fields": [dict(field) for field in _EDITABLE],
        "protected_body_fingerprint": {
            "algorithm": "sha256",
            "value": protected_body_sha256(body),
            "normalization_profile": "whole_body_v2",
            "normalization": "entire rendered body from first line through EOF; LF; trailing whitespace trimmed; final newline ensured; declared editable bodies elided before sha256.",
            "elided_fields": ["summary", "what_changed", "why_it_matters"],
        },
        "validation_result_path": validation_path,
    }


def generated_output(entry: Any, request: Any) -> dict[str, Any]:
    output_path = request.inputs.get("output_path")
    content = request.inputs.get("content")
    if isinstance(output_path, str) and output_path and isinstance(content, str):
        operation = {
            "operation_id": entry.helper_id,
            "kind": "write_file",
            "target": output_path,
            "content": content,
        }
        return run_mutation_helper(entry, request, operations=[operation])

    operations = request.inputs.get("operations")
    if isinstance(operations, list):
        return run_mutation_helper(entry, request)

    return run_mutation_helper(
        entry,
        request,
        operations=[
            {
                "operation_id": entry.helper_id,
                "kind": "command_plan",
                "command": ["python", "-m", "speckit_pro_runner", entry.helper_id],
            }
        ],
    )


def plan_commands(entry: Any, request: Any) -> dict[str, Any]:
    commands = request.inputs.get("commands", [])
    if commands is None:
        commands = []
    if not isinstance(commands, list):
        return input_error(request, "commands must be an array")
    operations: list[dict[str, Any]] = []
    for index, command in enumerate(commands):
        if not isinstance(command, list) or not all(isinstance(part, str) and part for part in command):
            return input_error(request, "each command must be a non-empty string array", details={"command_index": index})
        operations.append({"operation_id": f"{entry.helper_id}:{index + 1}", "kind": "command_plan", "command": command})

    if request.mode == "apply":
        mutation = empty_mutation(request.mode)
        mutation["planned_operations"] = operation_records(operations)
        mutation["mutation_status"] = "blocked"
        diag = diagnostic(
            "deferred_live_mutation",
            "command-plan apply mode is deferred until the active PR-emission cutover",
            details={"helper_id": entry.helper_id, "active_cutover": False},
            remediation_summary="Use dry_run for command planning; execute live PR operations outside the runner until cutover.",
            remediation_actions=["Switch to dry_run.", "Use the existing GitHub PR path for live PR work."],
            deferred_to="XPLAT-007/XPLAT-008",
        )
        return response(
            "expected_failure",
            request_id=request.request_id,
            data={
                "helper_id": entry.helper_id,
                "operation": entry.operation,
                "mode": request.mode,
                "promotion_status": entry.promotion_status,
                "comparison_mode": entry.comparison_mode,
                "writes_state": False,
                "mutation": mutation,
            },
            diagnostics=[diag],
        )

    result = run_mutation_helper(entry, request, operations=operations)
    data = result.get("data")
    if isinstance(data, dict):
        mutation = data.get("mutation")
        if isinstance(mutation, dict):
            mutation["live_mutation"] = False
            if not operations:
                mutation["mutation_status"] = "no_op"
    return result


def build_pr_body(title: str, sections: list[str]) -> str:
    parts = [f"# {title}", ""]
    for section in sections:
        parts.extend([f"## {section}", "", "TBD", ""])
    return "\n".join(parts).rstrip() + "\n"


def input_error(request: Any, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
    diag = diagnostic(
        "invalid_input",
        message,
        details=details,
        remediation_summary="Send the helper-specific PR emission input fields.",
        remediation_actions=["Inspect the mutation helper fixture manifest.", "Retry with normalized fields."],
    )
    return response("input_error", request_id=request.request_id, diagnostics=[diag])
