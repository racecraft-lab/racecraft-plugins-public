"""Fail-closed answers for the public unattended scaffold path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..envelope import response
from ..strict_input import SelectionError, require_fields, require_text, unique_object

INTERVIEW_KEYS = frozenset({
    "goals", "non_goals", "module_interface_deltas", "terms",
    "verification_gates", "design_tree", "open_questions",
})
OFFER_KEYS = frozenset({"quality_gate_confirmation", "formal_methods", "verification_docker", "continue_to_planning"})
ANSWER_KEYS = INTERVIEW_KEYS | OFFER_KEYS | {"bootstrap_commands"}


def read_answers(inputs: dict[str, Any]) -> dict[str, Any]:
    require_fields(inputs, {"answers_file", "spec_id"}, "scaffold-answers inputs")
    name = require_text(inputs["answers_file"], "answers_file")
    path = Path(name)
    root = Path.cwd().resolve()
    if path.is_absolute() or not (root / path).resolve().is_relative_to(root):
        raise SelectionError("answers_file must stay inside the task checkout")
    document = json.loads((root / path).read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    require_fields(document, {"schema_version", "spec_id", "answers"}, "answers file")
    if document["schema_version"] != "scaffold-answers/v1":
        raise SelectionError("schema_version must be scaffold-answers/v1")
    spec_id = require_text(inputs["spec_id"], "spec_id")
    if document["spec_id"] != spec_id:
        raise SelectionError("spec_id does not match the scaffold invocation")
    answers = require_fields(document["answers"], set(ANSWER_KEYS), "answers")
    for key in sorted(INTERVIEW_KEYS):
        text = require_text(answers[key], key)
        if text.strip().lower() in {"unknown", "tbd", "?"}:
            raise SelectionError(f"{key}: unknown answer")
    for key in sorted(OFFER_KEYS):
        if type(answers[key]) is not bool:
            raise SelectionError(f"{key} must be an explicit boolean answer")
    commands = answers["bootstrap_commands"]
    if not isinstance(commands, list):
        raise SelectionError("bootstrap_commands must be a list of explicitly approved commands")
    for command in commands:
        require_text(command, "bootstrap_commands entry")
    return answers


def run_scaffold_answers_helper(entry: Any, request: Any) -> dict[str, Any]:
    try:
        answers = read_answers(request.inputs)
    except (OSError, ValueError) as exc:
        return response("expected_failure", request_id=request.request_id, data={
            "verdict": "stop", "problems": [str(exc)], "questions_allowed": False,
        })
    return response("ok", request_id=request.request_id, data={
        "verdict": "proceed", "answers": answers, "questions_allowed": False,
    })
