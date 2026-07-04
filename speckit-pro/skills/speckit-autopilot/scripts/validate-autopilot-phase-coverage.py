#!/usr/bin/env python3
"""Validate that a Codex autopilot workflow/state pair keeps every phase visible."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


WORKFLOW_SECTIONS = (
    "## Phase 1: Specify",
    "## Phase 2: Clarify",
    "## Phase 3: Plan",
    "## Phase 4: Domain Checklists",
    "## Phase 5: Tasks",
    "## Phase 6: Analyze",
    "## Phase 6.5:",
    "## Phase 7: Implement",
    "## Post-Implementation Checklist",
)

WORKFLOW_TOKENS = (
    "| Confidence Gate | G6.5 |",
    "| Post |",
    "| G6.5 |",
)

STATE_PREFIXES = (
    "Archive Sweep:",
    "Phase 0: Prerequisites",
    "Phase 1: Specify",
    "Phase 2: Clarify",
    "Phase 3: Plan",
    "Phase 4: Checklist",
    "Phase 5: Tasks",
    "Phase 6: Analyze",
    "Phase 6.5: Confidence Gate",
    "Phase 7: Implement",
)

POST_STEPS = (
    "Post: Doctor Extension Check",
    "Post: Verify Implementation",
    "Post: Verify Tasks Phantom Check",
    "Post: Code Review",
    "Post: Integration Suite",
    "Post: Reviewability Diff Gate",
    "Post: Self-Review",
    "Post: UAT Runbook Generation",
    "Post: PR Body Generation",
    "Post: PR Creation",
    "Post: Review Remediation",
    "Post: Retrospective",
)

ORDERED_STATE_CHECKPOINTS = (
    "Archive Sweep:",
    "Phase 0: Prerequisites",
    "Phase 1: Specify",
    "Phase 2: Clarify",
    "Phase 3: Plan",
    "Phase 4: Checklist",
    "Phase 5: Tasks",
    "Phase 6: Analyze",
    "Phase 6.5: Confidence Gate",
    "Phase 7: Implement",
    "Post: Doctor Extension Check",
    "Post: Retrospective",
)


@dataclass(frozen=True)
class PlanStep:
    step: str
    status: str | None


class ValidationError(Exception):
    def __init__(self, message: str, code: str = "input_error") -> None:
        super().__init__(message)
        self.code = code


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"could not read file: {path}: {exc}") from exc


def load_state(path: Path) -> dict[str, Any]:
    try:
        state = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid state JSON: {path}: {exc}") from exc
    if not isinstance(state, dict):
        raise ValidationError("autopilot state must be a JSON object")
    return state


def extract_plan_steps(state: dict[str, Any]) -> list[PlanStep]:
    raw_plan = state.get("plan")
    if not isinstance(raw_plan, list):
        raise ValidationError("autopilot state must contain a plan array")
    steps: list[PlanStep] = []
    for index, item in enumerate(raw_plan):
        if not isinstance(item, dict):
            raise ValidationError(f"plan item {index} must be an object")
        step = item.get("step")
        if not isinstance(step, str) or not step.strip():
            raise ValidationError(f"plan item {index} must contain a non-empty step")
        status = item.get("status")
        if status is not None and not isinstance(status, str):
            raise ValidationError(f"plan item {index} status must be a string when present")
        steps.append(PlanStep(step=step, status=status))
    return steps


def first_index_with_prefix(steps: list[str], prefix: str) -> int | None:
    for index, step in enumerate(steps):
        if step.startswith(prefix):
            return index
    return None


def first_index_exact(steps: list[str], value: str) -> int | None:
    for index, step in enumerate(steps):
        if step == value:
            return index
    return None


def validate_workflow(text: str) -> dict[str, list[str]]:
    missing_sections = [section for section in WORKFLOW_SECTIONS if section not in text]
    missing_tokens = [token for token in WORKFLOW_TOKENS if token not in text]
    missing_post_items = [post for post in POST_STEPS if post not in text]
    return {
        "missing_workflow_sections": missing_sections,
        "missing_workflow_tokens": missing_tokens,
        "missing_workflow_post_items": missing_post_items,
    }


def validate_state(steps: list[PlanStep]) -> dict[str, list[str]]:
    names = [step.step for step in steps]
    missing_prefixes = [prefix for prefix in STATE_PREFIXES if first_index_with_prefix(names, prefix) is None]
    missing_posts = [post for post in POST_STEPS if first_index_exact(names, post) is None]

    duplicate_steps: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name in seen and name not in duplicate_steps:
            duplicate_steps.append(name)
        seen.add(name)

    order_errors: list[str] = []
    last_index = -1
    for checkpoint in ORDERED_STATE_CHECKPOINTS:
        if checkpoint.startswith("Post:"):
            index = first_index_exact(names, checkpoint)
        else:
            index = first_index_with_prefix(names, checkpoint)
        if index is None:
            continue
        if index < last_index:
            order_errors.append(checkpoint)
        last_index = max(last_index, index)

    in_progress = [step.step for step in steps if step.status == "in_progress"]
    in_progress_errors: list[str] = []
    if len(in_progress) > 1:
        in_progress_errors = in_progress

    return {
        "missing_state_prefixes": missing_prefixes,
        "missing_state_post_items": missing_posts,
        "duplicate_state_steps": duplicate_steps,
        "state_order_errors": order_errors,
        "in_progress_errors": in_progress_errors,
    }


def build_report(workflow: Path, state: Path) -> dict[str, Any]:
    workflow_text = read_text(workflow)
    state_data = load_state(state)
    plan_steps = extract_plan_steps(state_data)

    workflow_result = validate_workflow(workflow_text)
    state_result = validate_state(plan_steps)
    problems = {**workflow_result, **state_result}
    passed = all(not values for values in problems.values())

    return {
        "status": "pass" if passed else "fail",
        "workflow_file": str(workflow),
        "state_file": str(state),
        "plan_step_count": len(plan_steps),
        **problems,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", required=True, type=Path, help="Autopilot workflow markdown file")
    parser.add_argument("--state", required=True, type=Path, help="autopilot-state.json file")
    args = parser.parse_args(argv)

    try:
        report = build_report(args.workflow, args.state)
    except ValidationError as exc:
        print(json.dumps({"status": "input_error", "code": exc.code, "message": str(exc)}, sort_keys=True))
        return 2

    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
