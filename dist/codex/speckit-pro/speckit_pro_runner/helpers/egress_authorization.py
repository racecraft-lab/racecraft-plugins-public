"""Render the Phase 6.5 egress authorization the operator reviews and sends.

Codex's automatic approval reviewer trusts user and developer messages, not
skill or plugin text, and approves data egress only when the transcript names
the payload and the destination. This read-only helper turns the preflight's
recorded data-egress actions into two texts for the operator: a paste-ready
authorization message and an `auto_review.extra_policy` fragment for the
operator's own Codex config. It renders only what it is given and never
writes a file.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from ..envelope import diagnostic, response

ALLOWED_INPUTS = frozenset({"repository", "default_branch", "actions"})
ACTION_FIELDS = frozenset({"action_id", "target", "effect", "purpose"})
ACTION_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
CONTROL_CHARACTER = re.compile(r"[\x00-\x1f\x7f]")


class _InvalidInput(ValueError):
    pass


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _InvalidInput(f"{field} must be a non-empty string")
    if CONTROL_CHARACTER.search(value):
        raise _InvalidInput(f"{field} must be one line with no control characters")
    return value.strip()


def _actions(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise _InvalidInput("actions must be a non-empty list")
    actions: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw in enumerate(value):
        if not isinstance(raw, dict):
            raise _InvalidInput(f"actions[{index}] must be an object")
        unknown = sorted(set(raw) - ACTION_FIELDS)
        if unknown:
            raise _InvalidInput(f"actions[{index}] has unknown fields: {', '.join(unknown)}")
        action_id = _text(raw.get("action_id"), f"actions[{index}].action_id")
        if not ACTION_ID.match(action_id):
            raise _InvalidInput(f"actions[{index}].action_id must match {ACTION_ID.pattern}")
        if action_id in seen:
            raise _InvalidInput(f"actions[{index}].action_id repeats {action_id}")
        seen.add(action_id)
        action = {
            "action_id": action_id,
            "target": _text(raw.get("target"), f"actions[{index}].target"),
            "effect": _text(raw.get("effect"), f"actions[{index}].effect"),
        }
        purpose = raw.get("purpose")
        action["purpose"] = action_id if purpose is None else _text(purpose, f"actions[{index}].purpose")
        actions.append(action)
    return actions


def _exclusions(default_branch: str) -> list[str]:
    items = [
        "edit autonomy-boundary files, their schema, or their recorded digests",
        "edit AGENTS.md or any file under .codex/",
        f"push to the default branch ({default_branch})",
        "force push, or push with --mirror",
        "add, remove, or change a git remote",
    ]
    return [f"- {item}{';' if index < len(items) - 1 else '.'}" for index, item in enumerate(items)]


def render_authorization_message(repository: str, default_branch: str, actions: list[dict[str, str]]) -> str:
    lines = [
        f"I authorize this SpecKit Pro autopilot run in {repository} to perform only these data-egress actions:",
        "",
    ]
    for action in actions:
        lines.append(
            f"- {action['action_id']}: Send {action['effect']} from {repository} "
            f"to {action['target']} for {action['purpose']}."
        )
    lines.extend(["", "It covers no other destination or data class, and it never authorizes a request to:"])
    lines.extend(_exclusions(default_branch))
    return "\n".join(lines) + "\n"


def _toml_multiline_basic(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def render_extra_policy_fragment(repository: str, default_branch: str, actions: list[dict[str, str]]) -> str:
    body = [
        f"Repository scope: this policy applies only to SpecKit Pro autopilot runs in {repository}.",
        "The operator has approved these data-egress actions for those runs:",
    ]
    for action in actions:
        body.append(f"- Send {action['effect']} from {repository} to {action['target']}.")
    body.append("Any other destination or data class still needs an explicit user message naming it.")
    body.append("This policy never approves a request to:")
    body.extend(_exclusions(default_branch))
    escaped = "\n".join(_toml_multiline_basic(line) for line in body)
    return "[auto_review]\nextra_policy = \"\"\"\n" + escaped + "\n\"\"\"\n"


def run_egress_authorization_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Runner helper entry point: read-only text rendering, no file access."""
    inputs = request.inputs
    try:
        unknown = sorted(set(inputs) - ALLOWED_INPUTS)
        if unknown:
            raise _InvalidInput(f"unknown inputs: {', '.join(unknown)}")
        repository = _text(inputs.get("repository"), "repository")
        default_branch = _text(inputs.get("default_branch"), "default_branch")
        actions = _actions(inputs.get("actions"))
    except _InvalidInput as error:
        return response(
            "input_error",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "invalid_input",
                    str(error),
                    remediation_summary="Pass the repository, its default branch, and every recorded data-egress action.",
                    remediation_actions=[
                        "Give each action a unique action_id, a one-line target, and a one-line effect.",
                        "Retry the request.",
                    ],
                )
            ],
        )
    message = render_authorization_message(repository, default_branch, actions)
    digest = "sha256:" + hashlib.sha256(message.encode("utf-8")).hexdigest()
    return response(
        "ok",
        request_id=request.request_id,
        data={
            "helper_id": entry.helper_id,
            "writes_state": False,
            "action_ids": [action["action_id"] for action in actions],
            "authorization_message": message,
            "authorization_message_sha256": digest,
            "extra_policy_fragment": render_extra_policy_fragment(repository, default_branch, actions),
        },
    )
