"""PR body, packet, and command-planning helpers."""

from __future__ import annotations

from typing import Any

from ..envelope import diagnostic, response
from .mutation import run_mutation_helper


def run_pr_emission_helper(entry: Any, request: Any) -> dict[str, Any]:
    if request.helper_id == "generate-pr-body":
        return generate_pr_body(entry, request)
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

    if request.mode == "apply" and request.inputs.get("live_mutation_approved") is not True:
        diag = diagnostic(
            "approval_required",
            "live PR command emission requires explicit approval",
            details={"helper_id": entry.helper_id},
            remediation_summary="Use dry_run for command planning unless live mutation has been explicitly approved.",
            remediation_actions=["Switch to dry_run.", "Provide live_mutation_approved true only for approved live runs."],
        )
        return response("expected_failure", request_id=request.request_id, diagnostics=[diag])

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
