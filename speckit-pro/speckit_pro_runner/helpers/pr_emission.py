"""PR body, packet, and command-planning helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from .mutation import (
    empty_mutation,
    operation_record,
    operation_records,
    resolve_candidate_path,
    run_mutation_helper,
    validate_target_path,
    write_file_atomic,
)
from .read_only import find_repo_root, normalize_display, packet_result, protected_body_sha256, repo_relative


def run_pr_emission_helper(entry: Any, request: Any) -> dict[str, Any]:
    if request.helper_id == "generate-pr-body":
        return generate_pr_body(entry, request)
    if request.helper_id == "pr-packet-output":
        return generate_pr_packet(entry, request)
    if request.helper_id == "validate-pr-packet-write":
        return validate_pr_packet_write(entry, request)
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

    body = build_pr_body(title, sections)
    operation = {
        "operation_id": "generate-pr-body",
        "kind": "write_file",
        "target": output_path,
        "content": body,
    }
    return run_mutation_helper(entry, request, operations=[operation])


def generate_pr_packet(entry: Any, request: Any) -> dict[str, Any]:
    packet_input = normalize_packet_input(request)
    if isinstance(packet_input, dict) and "diagnostic" in packet_input:
        return response("input_error", request_id=request.request_id, diagnostics=[packet_input["diagnostic"]])

    packet = packet_input["packet"]
    body = packet_input["body"]
    validation = packet_input["validation"]
    packet_path = packet_input["packet_path"]
    body_file = packet["body_file"]
    validation_result_path = packet["validation_result_path"]

    operations = [
        {
            "operation_id": "pr-packet-output:body",
            "kind": "write_file",
            "target": body_file,
            "content": body,
        },
        {
            "operation_id": "pr-packet-output:packet",
            "kind": "write_file",
            "target": packet_path,
            "content": pretty_json(packet),
        },
        {
            "operation_id": "pr-packet-output:validation",
            "kind": "write_file",
            "target": validation_result_path,
            "content": pretty_json(validation),
        },
    ]
    return run_mutation_helper(
        entry,
        request,
        operations=operations,
        extra_data={
            "packet_id": packet["packet_id"],
            "packet_path": packet_path,
            "body_file": body_file,
            "validation_result_path": validation_result_path,
            "generated_title": packet["generated_title"]["value"],
        },
    )


def validate_pr_packet_write(entry: Any, request: Any) -> dict[str, Any]:
    packet_path = request.inputs.get("packet_path")
    validation_result = request.inputs.get("validation_result")
    validation_result_path = request.inputs.get("validation_result_path")
    if not isinstance(packet_path, str) or not packet_path:
        return input_error(request, "packet_path is required")
    if not isinstance(validation_result, dict):
        return input_error(request, "validation_result must be an object produced by validate-pr-packet-read-only")
    if not isinstance(validation_result_path, str) or not re.fullmatch(
        r"specs/[^/]+/\.process/pr-packets/[^/]+/validation\.json",
        validation_result_path,
    ):
        return input_error(
            request,
            "validation_result_path must match specs/<feature>/.process/pr-packets/<packet-id>/validation.json",
        )
    if validation_result.get("status") != "passed" or validation_result.get("pr_blocked") is not False:
        return input_error(request, "validation_result must be a passing, unblocked PR packet validation result")

    operation = {
        "operation_id": "validate-pr-packet-write:validation",
        "kind": "write_file",
        "target": validation_result_path,
        "content": pretty_json(validation_result),
    }
    return run_validation_write(
        entry,
        request,
        operation,
        {
            "packet_path": packet_path,
            "validation_result_path": validation_result_path,
            "packet_id": validation_result.get("packet_id"),
        },
    )


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


def normalize_packet_input(request: Any) -> dict[str, Any]:
    inputs = request.inputs
    packet_path = inputs.get("packet_path")
    source_feature_dir = inputs.get("source_feature_dir")
    if not isinstance(packet_path, str) or not re.fullmatch(
        r"specs/[^/]+/\.process/pr-packets/[a-z0-9][a-z0-9._-]*\.json",
        packet_path,
    ):
        return invalid_packet_input(
            "packet_path must match specs/<feature>/.process/pr-packets/<packet-id>.json",
            field="packet_path",
        )
    if not isinstance(source_feature_dir, str) or not re.fullmatch(r"specs/[^/]+", source_feature_dir):
        return invalid_packet_input("source_feature_dir must match specs/<feature>", field="source_feature_dir")

    packet_id = inputs.get("packet_id")
    if packet_id is None:
        packet_id = packet_path.rsplit("/", 1)[1].removesuffix(".json")
    if not isinstance(packet_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", packet_id):
        return invalid_packet_input("packet_id must be lowercase alphanumeric with dot, dash, or underscore separators", field="packet_id")

    body_file = inputs.get("body_file") or f"{source_feature_dir}/.process/pr-packets/{packet_id}/body.md"
    validation_result_path = inputs.get("validation_result_path") or f"{source_feature_dir}/.process/pr-packets/{packet_id}/validation.json"
    if not isinstance(body_file, str) or not body_file.endswith(".md"):
        return invalid_packet_input("body_file must be a repo-relative markdown path", field="body_file")
    if not isinstance(validation_result_path, str) or not re.fullmatch(
        r"specs/[^/]+/\.process/pr-packets/[^/]+/validation\.json",
        validation_result_path,
    ):
        return invalid_packet_input(
            "validation_result_path must match specs/<feature>/.process/pr-packets/<packet-id>/validation.json",
            field="validation_result_path",
        )

    target = inputs.get("target")
    if not isinstance(target, dict):
        return invalid_packet_input("target must include base_branch and head_branch", field="target")
    base_branch = target.get("base_branch")
    head_branch = target.get("head_branch")
    if not isinstance(base_branch, str) or not base_branch or not isinstance(head_branch, str) or not head_branch:
        return invalid_packet_input("target.base_branch and target.head_branch are required", field="target")

    generated_title = normalize_generated_title(inputs)
    if isinstance(generated_title, dict) and "diagnostic" in generated_title:
        return generated_title

    scope_evidence = normalize_scope_evidence(inputs)
    if isinstance(scope_evidence, dict) and "diagnostic" in scope_evidence:
        return scope_evidence

    verification_evidence = normalize_evidence_list(
        inputs.get("verification_evidence"),
        fallback=inputs.get("verification"),
        default_kind="verification",
        default_source="validation",
    )
    if isinstance(verification_evidence, dict) and "diagnostic" in verification_evidence:
        return verification_evidence

    source_markers = normalize_source_markers(inputs.get("source_markers"), packet_id, generated_title["value"], source_feature_dir)
    if isinstance(source_markers, dict) and "diagnostic" in source_markers:
        return source_markers

    body = inputs.get("body")
    if isinstance(body, str) and body.strip():
        rendered_body = ensure_final_newline(body)
    else:
        rendered_body = build_packet_body(
            generated_title["value"],
            summary=markdown_block(inputs.get("summary"), "Generated SpecKit Pro review packet."),
            what_changed=markdown_list(inputs.get("what_changed"), ["See changed-file scope evidence in the packet."]),
            why_it_matters=markdown_block(inputs.get("why_it_matters"), "This prepares the completed SpecKit work for review."),
            how_to_review=markdown_list(inputs.get("how_to_review"), ["Review the changed files and verification evidence in order."]),
            how_to_uat=markdown_block(inputs.get("how_to_uat"), "No manual UAT runbook was provided; use verification evidence for this PR."),
            verification=markdown_list(inputs.get("verification"), [item["summary"] for item in verification_evidence]),
            scope=markdown_list(inputs.get("scope"), scope_evidence["changed_files"]),
            known_gaps=markdown_list(inputs.get("known_gaps"), ["No known gaps for this PR."]),
        )

    fingerprint = protected_body_sha256(rendered_body)
    validation = packet_result(
        "passed",
        "none",
        0,
        packet_id,
        inputs.get("mode") if inputs.get("mode") in {"single", "split"} else "single",
        generated_title["value"],
        body_file,
        validation_result_path,
        False,
        "",
        [],
        [],
        {"base_branch": base_branch, "head_branch": head_branch},
    )

    packet: dict[str, Any] = {
        "schema_version": "1.0.0",
        "packet_id": packet_id,
        "mode": inputs.get("mode") if inputs.get("mode") in {"single", "split"} else "single",
        "target": {"base_branch": base_branch, "head_branch": head_branch},
        "source_feature_dir": source_feature_dir,
        "generated_title": generated_title,
        "body_file": body_file,
        "required_headings": [
            "Summary",
            "What Changed",
            "Why It Matters",
            "How To Review",
            "How To UAT",
            "Verification",
            "Scope",
            "Known Gaps",
        ],
        "verification_evidence": verification_evidence,
        "scope_evidence": scope_evidence,
        "uat": {
            "how_to_uat": markdown_block(inputs.get("how_to_uat"), "No manual UAT runbook was provided; use verification evidence for this PR."),
            "uat_runbook_heading": "## UAT Runbook",
            "uat_source": str(inputs.get("uat_source") or "packet-input"),
        },
        "source_markers": source_markers,
        "editable_fields": editable_fields(),
        "protected_body_fingerprint": {
            "algorithm": "sha256",
            "value": fingerprint,
            "normalization": "LF line endings; trailing whitespace trimmed; final newline ensured; editable block bodies replaced by <elided:field_id> before sha256.",
            "elided_fields": ["summary", "what_changed", "why_it_matters"],
        },
        "validation_result_path": validation_result_path,
    }
    if packet["mode"] == "split":
        split_slice = inputs.get("split_slice")
        if not isinstance(split_slice, dict):
            return invalid_packet_input("split_slice is required when mode is split", field="split_slice")
        packet["split_slice"] = split_slice

    return {
        "packet": packet,
        "body": rendered_body,
        "validation": validation,
        "packet_path": packet_path,
    }


def normalize_generated_title(inputs: dict[str, Any]) -> dict[str, Any]:
    raw = inputs.get("generated_title")
    if isinstance(raw, dict):
        required = ["value", "type", "scope", "description", "source_evidence", "rejected_candidates"]
        missing = [field for field in required if field not in raw]
        if missing:
            return invalid_packet_input("generated_title is missing required fields", field="generated_title", details={"missing": missing})
        return raw

    title_type = inputs.get("title_type") or "feat"
    title_scope = inputs.get("title_scope")
    title_description = inputs.get("title_description")
    if not isinstance(title_scope, str) or not title_scope:
        return invalid_packet_input("title_scope is required when generated_title is omitted", field="title_scope")
    if not isinstance(title_description, str) or len(title_description) < 8:
        return invalid_packet_input("title_description must be at least 8 characters", field="title_description")
    if not isinstance(title_type, str) or title_type not in {"feat", "fix", "chore", "docs", "refactor", "test"}:
        return invalid_packet_input("title_type must be a supported conventional commit type", field="title_type")
    description = title_description[0].upper() + title_description[1:]
    value = f"{title_type}({title_scope}): {description}"
    return {
        "value": value,
        "type": title_type,
        "scope": title_scope,
        "description": description,
        "source_evidence": {
            "kind": "workflow",
            "source": str(inputs.get("title_source") or "autopilot-state"),
            "summary": "Title generated from active SpecKit workflow evidence.",
        },
        "rejected_candidates": list_of_objects(inputs.get("rejected_title_candidates")),
    }


def normalize_scope_evidence(inputs: dict[str, Any]) -> dict[str, Any]:
    raw = inputs.get("scope_evidence")
    if isinstance(raw, dict):
        return raw
    changed_files = inputs.get("changed_files")
    if not isinstance(changed_files, list) or not changed_files or not all(isinstance(item, str) and item for item in changed_files):
        return invalid_packet_input("changed_files must be a non-empty array when scope_evidence is omitted", field="changed_files")
    non_goals = inputs.get("non_goals")
    if not isinstance(non_goals, list) or not non_goals or not all(isinstance(item, str) and item for item in non_goals):
        non_goals = ["No runtime, dependency, or generated payload changes unless listed in changed_files."]
    return {
        "reviewable_loc": int_value(inputs.get("reviewable_loc"), 0),
        "production_files": int_value(inputs.get("production_files"), 0),
        "total_files": int_value(inputs.get("total_files"), len(changed_files)),
        "budget_result": str(inputs.get("budget_result") or "within_budget"),
        "changed_files": changed_files,
        "non_goals": non_goals,
    }


def normalize_evidence_list(raw: Any, *, fallback: Any, default_kind: str, default_source: str) -> list[dict[str, str]] | dict[str, Any]:
    if isinstance(raw, list) and raw and all(isinstance(item, dict) for item in raw):
        return raw
    lines = string_lines(fallback)
    if not lines:
        return invalid_packet_input("verification_evidence or verification must contain at least one item", field="verification_evidence")
    return [
        {
            "kind": default_kind,
            "source": default_source,
            "summary": line,
            "result": "pass",
        }
        for line in lines
    ]


def normalize_source_markers(raw: Any, packet_id: str, title: str, source_feature_dir: str) -> list[dict[str, str]] | dict[str, Any]:
    if isinstance(raw, list) and raw and all(isinstance(item, dict) for item in raw):
        return raw
    return [{"marker_id": packet_id, "rendered_text": title, "source": source_feature_dir}]


def build_packet_body(
    title: str,
    *,
    summary: str,
    what_changed: str,
    why_it_matters: str,
    how_to_review: str,
    how_to_uat: str,
    verification: str,
    scope: str,
    known_gaps: str,
) -> str:
    parts = [
        f"# {title}",
        "",
        "## Summary",
        "",
        "<!-- speckit-pro-editable:summary:start -->",
        summary,
        "<!-- speckit-pro-editable:summary:end -->",
        "",
        "## What Changed",
        "",
        "<!-- speckit-pro-editable:what_changed:start -->",
        what_changed,
        "<!-- speckit-pro-editable:what_changed:end -->",
        "",
        "## Why It Matters",
        "",
        "<!-- speckit-pro-editable:why_it_matters:start -->",
        why_it_matters,
        "<!-- speckit-pro-editable:why_it_matters:end -->",
        "",
        "## How To Review",
        "",
        how_to_review,
        "",
        "## How To UAT",
        "",
        how_to_uat,
        "",
        "## Verification",
        "",
        verification,
        "",
        "## Scope",
        "",
        scope,
        "",
        "## Known Gaps",
        "",
        known_gaps,
        "",
    ]
    return "\n".join(parts)


def editable_fields() -> list[dict[str, str]]:
    return [
        {
            "field_id": "summary",
            "heading": "Summary",
            "start_marker": "<!-- speckit-pro-editable:summary:start -->",
            "end_marker": "<!-- speckit-pro-editable:summary:end -->",
        },
        {
            "field_id": "what_changed",
            "heading": "What Changed",
            "start_marker": "<!-- speckit-pro-editable:what_changed:start -->",
            "end_marker": "<!-- speckit-pro-editable:what_changed:end -->",
        },
        {
            "field_id": "why_it_matters",
            "heading": "Why It Matters",
            "start_marker": "<!-- speckit-pro-editable:why_it_matters:start -->",
            "end_marker": "<!-- speckit-pro-editable:why_it_matters:end -->",
        },
    ]


def markdown_block(raw: Any, fallback: str) -> str:
    lines = string_lines(raw)
    return "\n".join(lines) if lines else fallback


def markdown_list(raw: Any, fallback: list[str]) -> str:
    lines = string_lines(raw) or fallback
    return "\n".join(f"- {line}" for line in lines)


def string_lines(raw: Any) -> list[str]:
    if isinstance(raw, str) and raw.strip():
        return [line.strip() for line in raw.splitlines() if line.strip()]
    if isinstance(raw, list):
        return [item.strip() for item in raw if isinstance(item, str) and item.strip()]
    return []


def list_of_objects(raw: Any) -> list[dict[str, str]]:
    if isinstance(raw, list) and all(isinstance(item, dict) for item in raw):
        return raw
    return []


def int_value(raw: Any, fallback: int) -> int:
    return raw if isinstance(raw, int) and raw >= 0 else fallback


def ensure_final_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def pretty_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def run_validation_write(entry: Any, request: Any, operation: dict[str, Any], extra_data: dict[str, Any]) -> dict[str, Any]:
    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        return response(
            "missing_prerequisite",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "missing_prerequisite",
                    "could not locate repository root for PR packet validation write",
                    details={"cwd": normalize_display(Path.cwd())},
                    remediation_summary="Retry from a SpecKit Pro source checkout.",
                    remediation_actions=["Run the request from the repository root.", "Verify speckit_pro_runner exists."],
                )
            ],
        )

    mutation = empty_mutation(request.mode)
    mutation["planned_operations"] = operation_records([operation])
    target = resolve_candidate_path(operation["target"], repo_root)
    mutation["planned_paths"] = [repo_relative(target, repo_root)]
    data = {
        "helper_id": entry.helper_id,
        "operation": entry.operation,
        "mode": request.mode,
        "promotion_status": entry.promotion_status,
        "comparison_mode": entry.comparison_mode,
        "writes_state": False,
        "mutation": mutation,
        **extra_data,
    }

    path_diag = validate_target_path(operation["target"], repo_root)
    if path_diag is not None:
        return response("input_error", request_id=request.request_id, data=data, diagnostics=[path_diag])

    if request.mode == "dry_run":
        mutation["mutation_status"] = "planned"
        return response("ok", request_id=request.request_id, data=data)

    try:
        write_file_atomic(target, str(operation["content"]))
    except OSError as exc:
        mutation["mutation_status"] = "blocked"
        mutation["failure_operation"] = operation_record(operation)
        mutation["manual_remediation"] = [
            "Inspect the validation_result_path parent directory.",
            "Retry validate-pr-packet-write after the packet path is stable.",
        ]
        diag = diagnostic(
            "write_failure",
            "validate-pr-packet-write could not persist the validation result",
            details={"helper_id": entry.helper_id, "target": repo_relative(target, repo_root), "error": type(exc).__name__},
            remediation_summary="Fix the validation result path or reconcile the packet artifacts before retrying.",
            remediation_actions=mutation["manual_remediation"],
        )
        return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])

    mutation["mutation_status"] = "applied"
    mutation["applied_operations"].append(operation_record(operation))
    mutation["touched_paths"].append(repo_relative(target, repo_root))
    data["writes_state"] = True
    return response("ok", request_id=request.request_id, data=data)


def invalid_packet_input(message: str, *, field: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    extra = {"field": field}
    if details:
        extra.update(details)
    return {
        "diagnostic": diagnostic(
            "invalid_input",
            message,
            details=extra,
            remediation_summary="Send the required PR packet fields.",
            remediation_actions=["Retry with packet_path, source_feature_dir, target, title, scope, and verification evidence."],
        )
    }


def input_error(request: Any, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
    diag = diagnostic(
        "invalid_input",
        message,
        details=details,
        remediation_summary="Send the helper-specific PR emission input fields.",
        remediation_actions=["Inspect the mutation helper fixture manifest.", "Retry with normalized fields."],
    )
    return response("input_error", request_id=request.request_id, diagnostics=[diag])
