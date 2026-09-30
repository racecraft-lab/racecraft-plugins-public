"""The TBD pull-request body scaffold and the command-plan capture for the deferred emission helpers."""

from __future__ import annotations

from typing import Any

from ..envelope import diagnostic, response
from .mutation import empty_mutation, operation_records, run_mutation_helper


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


def ensure_final_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"
