"""PR body, packet, and command-planning helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from .mutation import (
    empty_mutation,
    operation_records,
    run_mutation_helper,
)
from .read_only import (
    find_repo_root,
    load_pr_packet_schema,
    normalize_display,
    packet_body_structure_failures,
    protected_body_sha256,
    pr_packet_schema_failures,
    validate_pr_packet_read_only,
)


PACKET_SLUG = r"[a-z0-9][a-z0-9._-]*"
SOURCE_FEATURE_PATTERN = re.compile(rf"^specs/(?P<feature>{PACKET_SLUG})$")
PACKET_PATH_PATTERN = re.compile(
    rf"^(?P<source_feature_dir>specs/{PACKET_SLUG})/\.process/pr-packets/(?P<packet_id>{PACKET_SLUG})\.json$"
)


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
    packet_input = normalize_packet_write_input(request)
    if isinstance(packet_input, dict) and "diagnostic" in packet_input:
        return response("input_error", request_id=request.request_id, diagnostics=[packet_input["diagnostic"]])

    packet_path = packet_input["packet_path"]
    validation_result_path = packet_input["validation_result_path"]
    packet_id = packet_input["packet_id"]
    validation_result = validation_result_placeholder(packet_id, validation_result_path)
    validation_source = "dry_run_plan"

    if request.mode == "apply":
        validation = current_packet_validation(packet_path)
        if isinstance(validation, dict) and "diagnostic" in validation:
            return response("expected_failure", request_id=request.request_id, diagnostics=[validation["diagnostic"]])
        validation_result = validation
        validation_source = "validate-pr-packet-read-only"

    operation = {
        "operation_id": "validate-pr-packet-write:validation",
        "kind": "write_file",
        "target": validation_result_path,
        "content": pretty_json(validation_result),
        "source_fingerprints": validation_result.get("source_fingerprints"),
    }
    return run_mutation_helper(
        entry,
        request,
        operations=[operation],
        extra_data={
            "packet_path": packet_path,
            "validation_result_path": validation_result_path,
            "packet_id": packet_id,
            "validation_source": validation_source,
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
    packet_parts = packet_path_parts(packet_path)
    if packet_parts is None:
        return invalid_packet_input(
            "packet_path must match specs/<feature>/.process/pr-packets/<packet-id>.json",
            field="packet_path",
        )
    if not isinstance(source_feature_dir, str) or SOURCE_FEATURE_PATTERN.fullmatch(source_feature_dir) is None:
        return invalid_packet_input("source_feature_dir must match specs/<feature>", field="source_feature_dir")
    if source_feature_dir != packet_parts["source_feature_dir"]:
        return invalid_packet_input("packet_path and source_feature_dir must refer to the same feature", field="packet_path")

    packet_id = inputs.get("packet_id")
    if packet_id is None:
        packet_id = packet_parts["packet_id"]
    if not isinstance(packet_id, str) or not re.fullmatch(PACKET_SLUG, packet_id):
        return invalid_packet_input("packet_id must be lowercase alphanumeric with dot, dash, or underscore separators", field="packet_id")
    if packet_id != packet_parts["packet_id"]:
        return invalid_packet_input("packet_id must match the packet_path filename", field="packet_id")

    canonical_paths = canonical_packet_paths(source_feature_dir, packet_id)
    body_file = inputs.get("body_file") or canonical_paths["body_file"]
    validation_result_path = inputs.get("validation_result_path") or canonical_paths["validation_result_path"]
    if body_file != canonical_paths["body_file"]:
        return invalid_packet_input(
            "body_file must be the canonical packet-owned body path",
            field="body_file",
            details={"expected": canonical_paths["body_file"]},
        )
    if validation_result_path != canonical_paths["validation_result_path"]:
        return invalid_packet_input(
            "validation_result_path must be the canonical packet-owned validation path",
            field="validation_result_path",
            details={"expected": canonical_paths["validation_result_path"]},
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

    mode = inputs.get("mode")
    if mode is None:
        mode = "single"
    elif mode not in {"single", "split"}:
        return invalid_packet_input("mode must be single or split when provided", field="mode")

    uat = {
        "how_to_uat": markdown_block(inputs.get("how_to_uat"), "No manual UAT runbook was provided; use verification evidence for this PR."),
        "uat_runbook_heading": "## UAT Runbook",
        "uat_source": str(inputs.get("uat_source") or "packet-input"),
    }

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
            how_to_uat=uat["how_to_uat"],
            verification=markdown_list(inputs.get("verification"), [item["summary"] for item in verification_evidence]),
            scope=markdown_list(inputs.get("scope"), scope_evidence["changed_files"]),
            known_gaps=markdown_list(inputs.get("known_gaps"), ["No known gaps for this PR."]),
        )

    body_failures = packet_body_structure_failures(
        {
            "generated_title": generated_title,
            "required_headings": required_headings(),
            "editable_fields": editable_fields(),
            "uat": uat,
        },
        rendered_body,
    )
    if body_failures:
        return invalid_packet_input(
            "body must contain the generated H1 title, required headings, and balanced editable markers",
            field="body",
            details={"failures": body_failures},
        )

    fingerprint = protected_body_sha256(rendered_body)

    packet: dict[str, Any] = {
        "schema_version": "1.0.0",
        "packet_id": packet_id,
        "mode": mode,
        "target": {"base_branch": base_branch, "head_branch": head_branch},
        "source_feature_dir": source_feature_dir,
        "generated_title": generated_title,
        "body_file": body_file,
        "required_headings": required_headings(),
        "verification_evidence": verification_evidence,
        "scope_evidence": scope_evidence,
        "uat": uat,
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

    schema_failures = generated_packet_schema_failures(packet)
    if schema_failures:
        return invalid_packet_input(
            "constructed packet does not satisfy the PR packet schema",
            field="packet",
            details={"failures": schema_failures},
        )

    return {
        "packet": packet,
        "body": rendered_body,
        "packet_path": packet_path,
    }


def normalize_packet_write_input(request: Any) -> dict[str, Any]:
    packet_path = request.inputs.get("packet_path")
    packet_parts = packet_path_parts(packet_path)
    if packet_parts is None:
        return invalid_packet_input(
            "packet_path must match specs/<feature>/.process/pr-packets/<packet-id>.json",
            field="packet_path",
        )
    canonical_paths = canonical_packet_paths(packet_parts["source_feature_dir"], packet_parts["packet_id"])
    validation_result_path = request.inputs.get("validation_result_path") or canonical_paths["validation_result_path"]
    if validation_result_path != canonical_paths["validation_result_path"]:
        return invalid_packet_input(
            "validation_result_path must be the canonical packet-owned validation path",
            field="validation_result_path",
            details={"expected": canonical_paths["validation_result_path"]},
        )
    return {
        "packet_path": packet_path,
        "packet_id": packet_parts["packet_id"],
        "validation_result_path": validation_result_path,
    }


def packet_path_parts(packet_path: Any) -> dict[str, str] | None:
    if not isinstance(packet_path, str):
        return None
    match = PACKET_PATH_PATTERN.fullmatch(packet_path)
    if match is None:
        return None
    return {"source_feature_dir": match.group("source_feature_dir"), "packet_id": match.group("packet_id")}


def canonical_packet_paths(source_feature_dir: str, packet_id: str) -> dict[str, str]:
    return {
        "packet_path": f"{source_feature_dir}/.process/pr-packets/{packet_id}.json",
        "body_file": f"{source_feature_dir}/.process/pr-packets/{packet_id}/body.md",
        "validation_result_path": f"{source_feature_dir}/.process/pr-packets/{packet_id}/validation.json",
    }


def required_headings() -> list[str]:
    return [
        "Summary",
        "What Changed",
        "Why It Matters",
        "How To Review",
        "How To UAT",
        "Verification",
        "Scope",
        "Known Gaps",
    ]


def current_packet_validation(packet_path: str) -> dict[str, Any]:
    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        return {
            "diagnostic": diagnostic(
                "missing_prerequisite",
                "could not locate repository root for PR packet validation write",
                details={"cwd": normalize_display(Path.cwd())},
                remediation_summary="Retry from a SpecKit Pro source checkout.",
                remediation_actions=["Run the request from the repository root.", "Verify speckit_pro_runner exists."],
            )
        }
    result = validate_pr_packet_read_only({"packet_path": packet_path}, repo_root)
    try:
        validation_result = json.loads(str(result.get("stdout") or ""))
    except json.JSONDecodeError:
        validation_result = None
    if result.get("exit_code") != 0 or not isinstance(validation_result, dict):
        return {
            "diagnostic": diagnostic(
                "packet_validation_failed",
                "validate-pr-packet-write refused to persist a packet that does not currently pass read-only validation",
                details={
                    "packet_path": packet_path,
                    "exit_code": result.get("exit_code"),
                    "stderr": str(result.get("stderr") or "").strip(),
                },
                remediation_summary="Regenerate or repair the packet and body, then retry validation persistence.",
                remediation_actions=[
                    "Run validate-pr-packet-read-only for the packet.",
                    "Fix the reported packet validation failures.",
                    "Retry validate-pr-packet-write from a clean worktree.",
                ],
            )
        }

    expected = normalize_packet_write_input(
        type("PacketWriteRequest", (), {"inputs": {"packet_path": packet_path}})()
    )
    if isinstance(expected, dict) and "diagnostic" in expected:
        return expected
    failures: list[str] = []
    if validation_result.get("status") != "passed":
        failures.append("status")
    if validation_result.get("pr_blocked") is not False:
        failures.append("pr_blocked")
    if validation_result.get("packet_id") != expected["packet_id"]:
        failures.append("packet_id")
    if validation_result.get("validation_result_path") not in {None, expected["validation_result_path"]}:
        failures.append("validation_result_path")
    if validation_result.get("body_file") not in {None, canonical_packet_paths(expected["packet_path"].rsplit("/.process/", 1)[0], expected["packet_id"])["body_file"]}:
        failures.append("body_file")
    if failures:
        return {
            "diagnostic": diagnostic(
                "packet_validation_failed",
                "current packet validation result does not match the packet write target",
                details={"packet_path": packet_path, "fields": failures},
                remediation_summary="Regenerate the packet and rerun validation before persisting.",
                remediation_actions=["Retry pr-packet-output.", "Run validate-pr-packet-write again."],
            )
        }
    return validation_result


def validation_result_placeholder(packet_id: str, validation_result_path: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "error_class": "dry_run",
        "exit_code": 0,
        "stderr_line": "",
        "packet_id": packet_id,
        "mode": None,
        "target": None,
        "status": "planned",
        "title_value": None,
        "body_file": None,
        "rule_outcomes": [],
        "pr_blocked": True,
        "failures": [],
        "remediation_evidence": ["dry_run only; apply mode reruns validate-pr-packet-read-only before writing"],
        "validation_result_path": validation_result_path,
    }


def generated_packet_schema_failures(packet: dict[str, Any]) -> list[dict[str, Any]]:
    schema, schema_error = load_pr_packet_schema()
    if schema is None:
        return [{"rule": "input.schema", "field": "packet", "message": schema_error or "PR packet schema is unavailable."}]
    return pr_packet_schema_failures(packet, schema)


def normalize_generated_title(inputs: dict[str, Any]) -> dict[str, Any]:
    raw = inputs.get("generated_title")
    if isinstance(raw, dict):
        required = ["value", "type", "scope", "description", "source_evidence", "rejected_candidates"]
        missing = [field for field in required if field not in raw]
        if missing:
            return invalid_packet_input("generated_title is missing required fields", field="generated_title", details={"missing": missing})
        extra = sorted(set(raw) - set(required))
        if extra:
            return invalid_packet_input("generated_title contains unsupported fields", field="generated_title", details={"fields": extra})
        invalid = validate_string_fields(raw, ["value", "type", "scope", "description"])
        if invalid:
            return invalid_packet_input("generated_title contains invalid string fields", field="generated_title", details={"fields": invalid})
        source_evidence = normalize_evidence_record(raw.get("source_evidence"), field="generated_title.source_evidence")
        if isinstance(source_evidence, dict) and "diagnostic" in source_evidence:
            return source_evidence
        rejected_candidates = raw.get("rejected_candidates")
        if not isinstance(rejected_candidates, list) or any(
            not isinstance(item, dict)
            or validate_string_fields(item, ["value", "reason"])
            or set(item) - {"value", "reason"}
            for item in rejected_candidates
        ):
            return invalid_packet_input(
                "generated_title.rejected_candidates must be objects with value and reason strings",
                field="generated_title.rejected_candidates",
            )
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
        required = ["reviewable_loc", "production_files", "total_files", "budget_result", "changed_files", "non_goals"]
        missing = [field for field in required if field not in raw]
        if missing:
            return invalid_packet_input("scope_evidence is missing required fields", field="scope_evidence", details={"missing": missing})
        invalid_ints = [
            field
            for field in ("reviewable_loc", "production_files", "total_files")
            if not isinstance(raw.get(field), int) or raw.get(field) < 0
        ]
        if invalid_ints:
            return invalid_packet_input("scope_evidence count fields must be non-negative integers", field="scope_evidence", details={"fields": invalid_ints})
        if raw.get("budget_result") not in {"within_budget", "warning", "blocked", "exception"}:
            return invalid_packet_input("scope_evidence.budget_result is invalid", field="scope_evidence.budget_result")
        changed_files = raw.get("changed_files")
        if not isinstance(changed_files, list) or not changed_files or not all(isinstance(item, str) and item for item in changed_files):
            return invalid_packet_input("scope_evidence.changed_files must be a non-empty string array", field="scope_evidence.changed_files")
        non_goals = raw.get("non_goals")
        if not isinstance(non_goals, list) or not non_goals or not all(isinstance(item, str) and item for item in non_goals):
            return invalid_packet_input("scope_evidence.non_goals must be a non-empty string array", field="scope_evidence.non_goals")
        extra = sorted(set(raw) - set(required))
        if extra:
            return invalid_packet_input("scope_evidence contains unsupported fields", field="scope_evidence", details={"fields": extra})
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
    if isinstance(raw, list) and raw:
        normalized: list[dict[str, str]] = []
        for index, item in enumerate(raw):
            evidence = normalize_evidence_record(item, field=f"verification_evidence[{index}]")
            if isinstance(evidence, dict) and "diagnostic" in evidence:
                return evidence
            normalized.append(evidence)
        return normalized
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
    if isinstance(raw, list) and raw:
        normalized: list[dict[str, str]] = []
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                return invalid_packet_input("source_markers entries must be objects", field=f"source_markers[{index}]")
            invalid = validate_string_fields(item, ["marker_id", "rendered_text", "source"])
            if invalid:
                return invalid_packet_input("source_markers entries require marker_id, rendered_text, and source strings", field=f"source_markers[{index}]", details={"fields": invalid})
            extra = sorted(set(item) - {"marker_id", "rendered_text", "source"})
            if extra:
                return invalid_packet_input("source_markers entries contain unsupported fields", field=f"source_markers[{index}]", details={"fields": extra})
            normalized.append({"marker_id": item["marker_id"], "rendered_text": item["rendered_text"], "source": item["source"]})
        return normalized
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
        "## UAT Runbook",
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


def normalize_evidence_record(raw: Any, *, field: str) -> dict[str, str] | dict[str, Any]:
    if not isinstance(raw, dict):
        return invalid_packet_input("evidence records must be objects", field=field)
    invalid = validate_string_fields(raw, ["kind", "source", "summary"])
    if invalid:
        return invalid_packet_input("evidence records require kind, source, and summary strings", field=field, details={"fields": invalid})
    result = raw.get("result")
    if result is not None and not isinstance(result, str):
        return invalid_packet_input("evidence result must be a string when provided", field=f"{field}.result")
    extra = sorted(set(raw) - {"kind", "source", "summary", "result"})
    if extra:
        return invalid_packet_input("evidence records contain unsupported fields", field=field, details={"fields": extra})
    normalized = {"kind": raw["kind"], "source": raw["source"], "summary": raw["summary"]}
    if isinstance(result, str):
        normalized["result"] = result
    return normalized


def validate_string_fields(record: dict[str, Any], fields: list[str]) -> list[str]:
    return [field for field in fields if not isinstance(record.get(field), str) or not record.get(field)]


def int_value(raw: Any, fallback: int) -> int:
    return raw if isinstance(raw, int) and raw >= 0 else fallback


def ensure_final_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def pretty_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


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
