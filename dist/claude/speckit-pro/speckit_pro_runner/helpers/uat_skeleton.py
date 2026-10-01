"""Render the UAT runbook skeleton for a spec."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from .mutation import run_mutation_helper
from .pr_emission import ensure_final_newline, input_error
from .read_only import (
    find_repo_root,
    path_stays_in_trust_boundary,
    repo_relative,
    resolve_input_path,
    trusted_text,
)

UAT_PAYLOAD_ROOT = Path(__file__).resolve().parents[2]
UAT_TEMPLATE_PATH = (
    UAT_PAYLOAD_ROOT
    / "skills"
    / "speckit-autopilot"
    / "templates"
    / "uat-runbook-template.md"
)
UAT_COMMAND_KEYS = (
    "BUILD",
    "TYPECHECK",
    "LINT",
    "LINT_FIX",
    "UNIT_TEST",
    "INTEGRATION_TEST",
    "SINGLE_FILE_INTEGRATION",
)


def generate_uat_skeleton(entry: Any, request: Any) -> dict[str, Any]:
    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        return input_error(request, "could not locate repository root for UAT generation")

    spec_path_raw = request.inputs.get("spec_path")
    output_path_raw = request.inputs.get("output_path")
    workflow_path_raw = request.inputs.get("workflow_file")
    if not isinstance(spec_path_raw, str) or not spec_path_raw:
        return input_error(request, "spec_path is required")
    if not isinstance(output_path_raw, str) or not output_path_raw:
        return input_error(request, "output_path is required")
    if workflow_path_raw is not None and (not isinstance(workflow_path_raw, str) or not workflow_path_raw):
        return input_error(request, "workflow_file must be a non-empty string when provided")

    spec_path = resolve_input_path(spec_path_raw, repo_root)
    output_path = resolve_input_path(output_path_raw, repo_root)
    if not path_stays_in_trust_boundary(spec_path, repo_root):
        return input_error(request, "spec_path escapes the repository trust boundary")
    if not path_stays_in_trust_boundary(output_path, repo_root):
        return input_error(request, "output_path escapes the repository trust boundary")

    spec_text = trusted_text(spec_path, repo_root)
    if spec_text is None:
        return input_error(request, "spec_path must name a readable file inside the repository")

    workflow_path: Path | None = None
    workflow_text: str | None = None
    if isinstance(workflow_path_raw, str):
        workflow_path = resolve_input_path(workflow_path_raw, repo_root)
        if not path_stays_in_trust_boundary(workflow_path, repo_root):
            return input_error(request, "workflow_file escapes the repository trust boundary")
        workflow_text = trusted_text(workflow_path, repo_root)

    plan_path = spec_path.parent / "plan.md"
    plan_text = trusted_text(plan_path, repo_root)
    project_commands = request.inputs.get("project_commands")
    if not isinstance(project_commands, dict):
        project_commands = {}
    elif not all(isinstance(key, str) and isinstance(value, str) for key, value in project_commands.items()):
        return input_error(request, "project_commands must map string command names to string values")

    template = trusted_text(UAT_TEMPLATE_PATH, UAT_PAYLOAD_ROOT)
    if template is None:
        return input_error(request, "the installed UAT runbook template is unavailable")

    content, duplicate_requirement_ids = render_uat_runbook(
        template,
        spec_text=spec_text,
        spec_id=spec_path.parent.name,
        spec_source=repo_relative(spec_path, repo_root),
        workflow_text=workflow_text,
        plan_text=plan_text,
        project_commands=project_commands,
    )
    fingerprints = {
        "spec": source_fingerprint(spec_path, spec_text, repo_root),
    }
    if workflow_path is not None and workflow_text is not None:
        fingerprints["workflow"] = source_fingerprint(workflow_path, workflow_text, repo_root)
    if plan_text is not None:
        fingerprints["plan"] = source_fingerprint(plan_path, plan_text, repo_root)

    operation = {
        "operation_id": "generate-uat-skeleton",
        "kind": "write_file",
        "target": output_path_raw,
        "content": content,
        "source_fingerprints": fingerprints,
    }
    return run_mutation_helper(
        entry,
        request,
        operations=[operation],
        extra_data={
            "spec_path": repo_relative(spec_path, repo_root),
            "output_path": repo_relative(output_path, repo_root),
            "story_count": len(user_story_titles(spec_text)),
            "duplicate_requirement_ids": duplicate_requirement_ids,
        },
    )


def render_uat_runbook(
    template: str,
    *,
    spec_text: str,
    spec_id: str,
    spec_source: str,
    workflow_text: str | None,
    plan_text: str | None,
    project_commands: dict[str, str],
) -> tuple[str, list[str]]:
    stories = user_story_titles(spec_text)
    duplicate_ids: list[str] = []
    header_note = ""
    if stories:
        per_story = "\n\n".join(
            f"### {title}\n\n- [ ] Walk this story end to end and confirm the observable behavior the spec promises."
            for title in stories
        )
        matrix_rows = ["| Story | Acceptance test |", "|-------|-----------------|"]
        matrix_rows.extend(f"| {title} | see the Per-Story Acceptance Tests block above |" for title in stories)
        fr_matrix = "\n".join(matrix_rows)
    else:
        header_note = "> This spec has no user stories; tests are keyed by FR/SC."
        requirements = dedupe_requirement_ids(
            extract_heading_section(spec_text, "Functional Requirements", preserve_blanks=True),
            duplicate_ids,
        )
        outcomes = dedupe_requirement_ids(
            extract_heading_section(spec_text, "Measurable Outcomes", preserve_blanks=True),
            duplicate_ids,
        )
        per_story = "\n\n".join(
            (
                "### FR-keyed Acceptance Tests\n\n"
                + annotate_clarifications(requirements or "No functional requirements found in spec.md"),
                "### SC-keyed Acceptance Tests\n\n"
                + annotate_clarifications(outcomes or "No measurable outcomes found in spec.md"),
            )
        )
        fr_matrix = "_No user stories — see the FR-keyed and SC-keyed Acceptance Tests above._"

    edge_cases = extract_heading_section(spec_text, "Edge Cases", preserve_blanks=True)
    negative_path = annotate_clarifications(edge_cases) if edge_cases.strip() else "No edge cases identified in spec.md"
    rollback = extract_heading_section(spec_text, "Rollback", limit=40)
    if not rollback and plan_text is not None:
        rollback = extract_heading_section(plan_text, "Rollback", limit=40)
    if not rollback:
        rollback = "git revert <SHA>; see plan.md for data-migration considerations"

    rendered = strip_template_provenance(template)
    replacements = {
        "SPEC_ID": spec_id,
        "BRANCH": spec_id,
        "PR_PLACEHOLDER": "Pending until PR is opened",
        "SPEC_TIMESTAMP": spec_source,
        "HEADER_NOTE": header_note,
        "ENV_SETUP": format_uat_project_commands(project_commands),
        "PER_STORY": per_story,
        "FR_MATRIX": fr_matrix,
        "NEGATIVE_PATH": negative_path,
        "ROLLBACK": rollback,
    }
    for token, value in replacements.items():
        rendered = rendered.replace("{{" + token + "}}", value)
    return ensure_final_newline(rendered), duplicate_ids


def user_story_titles(text: str) -> list[str]:
    return [
        match.group(1).strip()
        for line in text.splitlines()
        if (match := re.match(r"^###\s+(User Story\s+\d+.*)$", line)) is not None
    ]


def extract_heading_section(
    text: str,
    heading: str,
    *,
    preserve_blanks: bool = False,
    limit: int | None = None,
) -> str:
    lines = text.splitlines()
    captured: list[str] = []
    active_level: int | None = None
    for line in lines:
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match is not None:
            level = len(match.group(1))
            title = match.group(2).strip()
            if active_level is None and title.casefold() == heading.casefold():
                active_level = level
                continue
            if active_level is not None and level <= active_level:
                break
        if active_level is not None:
            if preserve_blanks or line.strip():
                captured.append(line)
            if limit is not None and len(captured) >= limit:
                break
    return "\n".join(captured).strip()


def dedupe_requirement_ids(text: str, duplicate_ids: list[str]) -> str:
    seen: set[str] = set()
    output: list[str] = []
    dropping = False
    for line in text.splitlines():
        requirement = re.match(r"^\s*-\s+\*\*([A-Z]+-\d+)\*\*", line)
        if requirement is not None:
            requirement_id = requirement.group(1)
            dropping = requirement_id in seen
            if dropping:
                duplicate_ids.append(requirement_id)
            seen.add(requirement_id)
            if not dropping:
                output.append(line)
            continue
        if re.match(r"^\s*-\s+", line) or re.match(r"^#{1,6}\s+", line):
            dropping = False
        if not dropping:
            output.append(line)
    return "\n".join(output).strip()


def annotate_clarifications(text: str) -> str:
    return "\n".join(
        line + "  **WARN:** unresolved clarification" if "NEEDS CLARIFICATION" in line else line
        for line in text.splitlines()
    )


def format_uat_project_commands(commands: dict[str, str]) -> str:
    placeholder = "<unknown — autopilot did not pass PROJECT_COMMANDS>"
    rows = ["| Command | Value |", "|---------|-------|"]
    for key in UAT_COMMAND_KEYS:
        value = commands.get(key)
        if value == "N/A":
            rendered = "_not available for this project_"
        elif not value:
            rendered = placeholder
        else:
            rendered = f"`{value}`"
        rows.append(f"| {key} | {rendered} |")
    return "\n".join(rows)


def strip_template_provenance(template: str) -> str:
    if template.startswith("<!--") and "-->" in template:
        template = template.split("-->", 1)[1]
    return template.lstrip("\n")


def source_fingerprint(path: Path, text: str, repo_root: Path) -> dict[str, Any]:
    encoded = text.encode("utf-8")
    return {
        "path": repo_relative(path, repo_root),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "size_bytes": len(encoded),
    }
