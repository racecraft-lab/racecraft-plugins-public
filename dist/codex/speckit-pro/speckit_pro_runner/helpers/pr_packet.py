"""Normalize, build, and validate the reviewer PR packet and its body."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from ..trusted_io import path_stays_in_trust_boundary, resolve_input_path, trusted_text
from ..pr_contract import (
    DEFERRED_ITEM_FIELDS,
    PACKET_SLUG,
    SOURCE_FEATURE_PATTERN,
    canonical_packet_paths,
    packet_path_parts,
    PACKET_TITLE_SCOPE_PATTERN,
    PACKET_TITLE_VALUE_PATTERN,
    TITLE_TYPES,
    is_one_line,
)
from .mutation import run_mutation_helper
from .pr_emission import ensure_final_newline
from .read_only import (
    find_repo_root,
    fenced_markdown_lines,
    load_pr_packet_schema,
    normalize_display,
    packet_body_structure_failures,
    protected_body_sha256,
    pr_packet_schema_failures,
    validate_pr_packet_read_only,
    workflow_phase65_verdict,
)

# A run that finished with deferred items opens its top PR body with this section.
DEFERRED_HEADING = "Deferred / not verified"


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

    # Resolved before the evidence normalizers because draft mode relaxes what they
    # accept. Left below them, a draft packet dies in input normalization before the
    # gate is ever reached.
    if "mode_name" in inputs:
        return invalid_packet_input(
            "inputs.mode is the packet mode field; remove inputs.mode_name and set inputs.mode to single, split, or draft",
            field="mode_name",
        )
    mode = inputs.get("mode")
    if mode is None:
        mode = "single"
    elif mode not in {"single", "split", "draft"}:
        return invalid_packet_input("mode must be single, split, or draft when provided", field="mode")

    release_note = inputs.get("release_note")
    if "release_note" in inputs:
        if not isinstance(release_note, str) or not release_note.strip():
            return invalid_packet_input("release_note must be a nonblank Markdown string", field="release_note")
        if any(re.match(r"^[ \t]*(?:`{3,}|~{3,})", line) for line in release_note.splitlines()):
            return invalid_packet_input("release_note must be unfenced Markdown", field="release_note")

    deferred_items = normalize_deferred_items(inputs.get("deferred_items"), mode)
    if isinstance(deferred_items, dict):
        return deferred_items

    scope_evidence = normalize_scope_evidence(inputs, mode)
    if isinstance(scope_evidence, dict) and "diagnostic" in scope_evidence:
        return scope_evidence

    verification_evidence = normalize_evidence_list(
        inputs.get("verification_evidence"),
        fallback=inputs.get("verification"),
        default_kind="verification",
        default_source="validation",
        mode=mode,
    )
    if isinstance(verification_evidence, dict) and "diagnostic" in verification_evidence:
        return verification_evidence

    source_markers = normalize_source_markers(inputs.get("source_markers"), packet_id, generated_title["value"], source_feature_dir)
    if isinstance(source_markers, dict) and "diagnostic" in source_markers:
        return source_markers

    # A draft body carries no UAT section, so it declares neither the runbook heading
    # nor the fallback prose that would describe one.
    uat = {
        "how_to_uat": "" if mode == "draft" else markdown_block(inputs.get("how_to_uat"), "No manual UAT runbook was provided; use verification evidence for this PR."),
        "uat_runbook_heading": "" if mode == "draft" else "## UAT Runbook",
        "uat_source": str(inputs.get("uat_source") or "packet-input"),
    }

    verdict: str | None = None
    if mode != "draft":
        workflow_raw = inputs.get("workflow_file")
        if not isinstance(workflow_raw, str) or not workflow_raw.strip():
            return invalid_packet_input("workflow_file is required for final packets", field="workflow_file")
        repo_root = find_repo_root(Path.cwd())
        if repo_root is None:
            return invalid_packet_input("repository root is unavailable", field="workflow_file")
        workflow_path = resolve_input_path(workflow_raw, repo_root)
        if not path_stays_in_trust_boundary(workflow_path, repo_root):
            return invalid_packet_input("workflow_file escapes the repository", field="workflow_file")
        workflow_text = trusted_text(workflow_path, repo_root)
        verdict = workflow_phase65_verdict(workflow_text) if workflow_text is not None else None
        if verdict is None:
            return invalid_packet_input("workflow_file must record one valid Phase 6.5 Verdict", field="workflow_file")

    body = inputs.get("body")
    if isinstance(body, str) and body.strip():
        rendered_body = ensure_final_newline(body)
    elif mode == "draft":
        return invalid_packet_input(
            "a draft packet requires inputs.body: the orchestrator composes the draft body, so no builder runs",
            field="body",
        )
    else:
        rendered_body = build_packet_body(
            generated_title["value"],
            summary=markdown_block(inputs.get("summary"), "Generated SpecKit Pro review packet."),
            what_changed=markdown_list(inputs.get("what_changed"), ["See changed-file scope evidence in the packet."]),
            why_it_matters=markdown_block(inputs.get("why_it_matters"), "This prepares the completed SpecKit work for review."),
            how_to_review=markdown_list(inputs.get("how_to_review"), ["Review the changed files and verification evidence in order."]),
            how_to_uat=uat["how_to_uat"],
            uat_heading=uat["uat_runbook_heading"],
            verification=markdown_list(inputs.get("verification"), [item["summary"] for item in verification_evidence]),
            scope=markdown_list(inputs.get("scope"), scope_evidence["changed_files"]),
            known_gaps=markdown_list(inputs.get("known_gaps"), ["No known gaps for this PR."]),
            deferred_items=deferred_items,
        )
    if verdict is not None:
        rendered_body = with_current_phase65_verdict(rendered_body, verdict)
        if rendered_body is None:
            return invalid_packet_input("body must contain one Verification section", field="body")
    if deferred_items and first_section_heading(rendered_body) != DEFERRED_HEADING:
        return invalid_packet_input(
            f"a body for a run with deferred items must open with the ## {DEFERRED_HEADING} section",
            field="body",
        )

    if mode != "draft" and release_note is not None:
        # An enclosing fence owns its literal examples, as in the host parser.
        body_lines = rendered_body.splitlines()
        line_index = 0
        last_section_heading = ""
        while line_index < len(body_lines):
            line = body_lines[line_index]
            quote_depth = 0
            while quote := re.match(r"^ {0,3}>[ \t]?", line):
                line = line[quote.end():]
                quote_depth += 1
            opening = re.fullmatch(
                r"(?P<indent> {0,3})(?:(?P<marker>[-+*]|[0-9]{1,9}[.)])(?P<space>[ \t]+))?"
                r"(?P<fence>`{3,}|~{3,})(?P<info>[^\r\n]*)",
                line,
            )
            if opening is None or (opening["fence"][0] == "`" and "`" in opening["info"]):
                if quote_depth == 0 and body_lines[line_index].startswith("## "):
                    last_section_heading = body_lines[line_index]
                line_index += 1
                continue
            if opening["info"].strip(" \t") == "release-note":
                return invalid_packet_input("body already contains a release-note fence", field="body")
            container_indent = (
                len(opening["indent"]) + len(opening["marker"]) + len(opening["space"])
                if opening["marker"] else 0
            )
            close_index = None
            for probe in range(line_index + 1, len(body_lines)):
                line = body_lines[probe]
                stripped_quotes = 0
                while stripped_quotes < quote_depth and (quote := re.match(r"^ {0,3}>[ \t]?", line)):
                    line = line[quote.end():]
                    stripped_quotes += 1
                if stripped_quotes != quote_depth and line.strip():
                    break
                leading_spaces = len(line) - len(line.lstrip(" "))
                content = line[container_indent:] if leading_spaces >= container_indent else line
                if leading_spaces >= container_indent and re.fullmatch(
                    rf" {{0,3}}{re.escape(opening['fence'][0])}{{{len(opening['fence'])},}}[ \t]*",
                    content,
                ):
                    close_index = probe
                    break
                if leading_spaces < container_indent and line.strip():
                    break
            if close_index is None:
                return invalid_packet_input("body contains an unclosed fence that would enclose the supplied release note", field="body")
            line_index = close_index + 1
        heading = "\n" if last_section_heading == "## Release note" else "\n## Release note\n\n"
        rendered_body = (
            ensure_final_newline(rendered_body) + heading + "```release-note\n"
            + f"<!-- speckit-pro-editable:release_note:start -->\n{release_note}\n"
            + "<!-- speckit-pro-editable:release_note:end -->\n```\n"
        )

    body_failures = packet_body_structure_failures(
        {
            "generated_title": generated_title,
            "required_headings": required_headings(mode),
            "editable_fields": editable_fields(mode, has_release_note=release_note is not None),
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
        "required_headings": required_headings(mode),
        "verification_evidence": verification_evidence,
        "scope_evidence": scope_evidence,
        "uat": uat,
        "source_markers": source_markers,
        "editable_fields": editable_fields(mode, has_release_note=release_note is not None),
        "protected_body_fingerprint": {
            "algorithm": "sha256",
            "value": fingerprint,
            "normalization": "LF line endings; trailing whitespace trimmed; final newline ensured; editable block bodies replaced by <elided:field_id> before sha256.",
            "elided_fields": [field["field_id"] for field in editable_fields(mode, has_release_note=release_note is not None)],
        },
        "validation_result_path": validation_result_path,
    }
    if mode != "draft" and release_note is not None:
        packet["release_note"] = release_note
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





def required_headings(mode: str) -> list[str]:
    if mode == "draft":
        return ["Artifacts", "Resume"]
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


def title_shape_matches(scope: str, value: str | None = None) -> bool:
    """True when `scope`, and `value` if given, fit the shapes the PR-title gate accepts."""
    if re.fullmatch(PACKET_TITLE_SCOPE_PATTERN, scope) is None:
        return False
    return value is None or re.fullmatch(PACKET_TITLE_VALUE_PATTERN, value) is not None


def generated_title_shape_failure(raw: dict[str, Any]) -> dict[str, Any] | None:
    """The diagnostic for a supplied generated_title with wrong keys, non-string fields, or a title the gate rejects."""
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
    if not title_shape_matches(raw["scope"], raw["value"]):
        return invalid_packet_input(
            "generated_title must read <type>(<lowercase-scope>): <description>, the shape the PR-title gate accepts",
            field="generated_title",
        )
    return None


def normalize_generated_title(inputs: dict[str, Any]) -> dict[str, Any]:
    raw = inputs.get("generated_title")
    if isinstance(raw, dict):
        malformed = generated_title_shape_failure(raw)
        if malformed is not None:
            return malformed
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
    if not title_shape_matches(title_scope):
        return invalid_packet_input(
            "title_scope must be lowercase letters, digits, and hyphens, as the PR-title gate requires",
            field="title_scope",
        )
    if not isinstance(title_description, str) or len(title_description) < 8:
        return invalid_packet_input("title_description must be at least 8 characters", field="title_description")
    if not isinstance(title_type, str) or title_type not in TITLE_TYPES:
        return invalid_packet_input("title_type must be a supported conventional commit type", field="title_type")
    value = f"{title_type}({title_scope}): {title_description}"
    return {
        "value": value,
        "type": title_type,
        "scope": title_scope,
        "description": title_description,
        "source_evidence": {
            "kind": "workflow",
            "source": str(inputs.get("title_source") or "autopilot-state"),
            "summary": "Title generated from active SpecKit workflow evidence.",
        },
        "rejected_candidates": list_of_objects(inputs.get("rejected_title_candidates")),
    }


def normalize_scope_evidence(inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    # Draft mode permits an empty changed_files: the plan-stage boundary has produced
    # no diff yet. non_goals stays non-empty in every mode.
    allow_empty = mode == "draft"
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
        if not isinstance(changed_files, list) or not (changed_files or allow_empty) or not all(isinstance(item, str) and item for item in changed_files):
            return invalid_packet_input("scope_evidence.changed_files must be a non-empty string array", field="scope_evidence.changed_files")
        non_goals = raw.get("non_goals")
        if not isinstance(non_goals, list) or not non_goals or not all(isinstance(item, str) and item for item in non_goals):
            return invalid_packet_input("scope_evidence.non_goals must be a non-empty string array", field="scope_evidence.non_goals")
        extra = sorted(set(raw) - set(required))
        if extra:
            return invalid_packet_input("scope_evidence contains unsupported fields", field="scope_evidence", details={"fields": extra})
        return raw
    changed_files = inputs.get("changed_files")
    if not isinstance(changed_files, list) or not (changed_files or allow_empty) or not all(isinstance(item, str) and item for item in changed_files):
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


def normalize_evidence_list(raw: Any, *, fallback: Any, default_kind: str, default_source: str, mode: str) -> list[dict[str, str]] | dict[str, Any]:
    # Draft mode permits an empty list, but not an absent one: the plan-stage boundary
    # has produced no verification evidence yet, and says so explicitly.
    if isinstance(raw, list) and (raw or mode == "draft"):
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
    uat_heading: str,
    verification: str,
    scope: str,
    known_gaps: str,
    deferred_items: list[dict[str, str]] | None = None,
) -> str:
    parts = [f"# {title}", ""]
    if deferred_items:
        parts.extend([
            f"## {DEFERRED_HEADING}",
            "",
            "The run finished with these items deferred. They are not verified.",
            "",
            *(f"- **{item['item']}**: {item['reason']} To finish it: {item['finish']}" for item in deferred_items),
            "",
        ])
    parts += [
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
        uat_heading,
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



def with_current_phase65_verdict(body: str, verdict: str) -> str | None:
    """Replace a stale Verification verdict before fingerprinting final bodies."""
    lines = body.splitlines()
    fenced = fenced_markdown_lines(lines)
    starts = [index for index, line in enumerate(lines)
              if index not in fenced and line == "## Verification"]
    if len(starts) != 1:
        return None
    start = starts[0]
    end = next((index for index in range(start + 1, len(lines))
                if index not in fenced and lines[index].startswith("## ")), len(lines))
    verdict_label = re.compile(r"Phase[ \t]+6\.5[ \t]+Verdict\b", re.IGNORECASE)
    if any(verdict_label.search(line) for line in (*lines[:start + 1], *lines[end:])):
        return None
    kept = [line for line in lines[start + 1:end] if not verdict_label.search(line)]
    while kept and not kept[0].strip():
        kept.pop(0)
    lines[start + 1:end] = ["", f"Phase 6.5 Verdict: {verdict}", "", *kept]
    return ensure_final_newline("\n".join(lines))


def normalize_deferred_items(raw: Any, mode: str) -> list[dict[str, str]] | dict[str, Any]:
    """The run's deferred items, each with its reason and what finishes it; empty when absent."""
    if raw is None:
        return []
    if not isinstance(raw, list) or not all(
        isinstance(item, dict) and set(item) == set(DEFERRED_ITEM_FIELDS)
        and all(isinstance(item[key], str) and is_one_line(item[key]) for key in item)
        for item in raw
    ):
        return invalid_packet_input(
            "deferred_items must list objects with one-line item, reason, and finish text",
            field="deferred_items",
        )
    if raw and mode == "draft":
        return invalid_packet_input("a draft body carries no deferred items", field="deferred_items")
    return [{key: item[key].strip() for key in DEFERRED_ITEM_FIELDS} for item in raw]


def first_section_heading(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("## "):
            return line[3:].strip()
    return None


def editable_fields(mode: str, *, has_release_note: bool = False) -> list[dict[str, str]]:
    if mode == "draft":
        # A draft body encloses no editable prose.
        return []
    fields = [
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
    if has_release_note:
        fields.append({
            "field_id": "release_note",
            "heading": "Release note",
            "start_marker": "<!-- speckit-pro-editable:release_note:start -->",
            "end_marker": "<!-- speckit-pro-editable:release_note:end -->",
        })
    return fields


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
            remediation_summary="Correct the named PR packet input.",
            remediation_actions=[
                "Use inputs.mode for single, split, or draft; include packet_path, source_feature_dir, target, title_type, title_scope, and title_description.",
                "Use verification_evidence records from the plugin-root-relative skills/speckit-autopilot/contracts/pr-packet.schema.json; an explicit empty array is valid for draft packets.",
            ],
        )
    }
