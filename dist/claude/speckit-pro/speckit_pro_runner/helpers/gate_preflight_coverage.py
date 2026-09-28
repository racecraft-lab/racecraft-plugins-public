"""Check at run start that every gate's required escalation is in the preflight inventory.

A gate that can fail for want of an authorization (data egress, a privileged
command, an interactive login, a write outside the writable roots) must have
that need collected by the Phase 6.5 Autonomy Boundary Preflight, so the
operator is asked at run start, as a chat reply, and not at the end. This
read-only helper names each gate need that no inventoried action covers. A
need is covered only by an action with the same category and the same exact
target. It fails closed and never reads or writes a file.
"""

from __future__ import annotations

from typing import Any

from ..envelope import diagnostic, response

# The autonomy-boundary schema's action categories; a test pins the two together.
CATEGORIES = ("outside_writable_roots", "privileged_command", "interactive_authentication", "external_side_effect")
ALLOWED_INPUTS = frozenset({"repo_root", "gates", "inventory_actions"})


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _need(raw: Any, field: str) -> tuple[str, str]:
    if not isinstance(raw, dict) or not {"category", "target"} <= set(raw):
        raise ValueError(f"{field} must have a category and a target")
    category = _text(raw["category"], f"{field}.category")
    if category not in CATEGORIES:
        raise ValueError(f"{field}.category must be one of: {', '.join(CATEGORIES)}")
    return category, _text(raw["target"], f"{field}.target")


def gate_preflight_coverage(inputs: Any) -> dict[str, Any]:
    """Which gate needs the inventory covers; raises ValueError on malformed evidence."""
    if not isinstance(inputs, dict):
        raise ValueError("inputs must be an object")
    unknown = sorted(set(inputs) - ALLOWED_INPUTS)
    if unknown:
        raise ValueError(f"unknown inputs: {', '.join(unknown)}")
    gates = inputs.get("gates")
    if not isinstance(gates, list) or not gates:
        raise ValueError("gates must list every gate the run will execute")
    actions = inputs.get("inventory_actions")
    if not isinstance(actions, list):
        raise ValueError("inventory_actions must list the preflight inventory's actions")
    inventory: dict[tuple[str, str], list[str]] = {}
    for index, raw in enumerate(actions):
        key = _need(raw, f"inventory_actions[{index}]")
        inventory.setdefault(key, []).append(_text(raw.get("action_id"), f"inventory_actions[{index}].action_id"))
    missing: list[dict[str, str]] = []
    covering: dict[str, list[str]] = {}
    for index, raw in enumerate(gates):
        if not isinstance(raw, dict) or set(raw) != {"gate", "command", "needs"} or not isinstance(raw["needs"], list):
            raise ValueError(f"gates[{index}] must have exactly gate, command, and a needs list")
        gate = _text(raw["gate"], f"gates[{index}].gate")
        command = _text(raw["command"], f"gates[{index}].command")
        for need_index, need in enumerate(raw["needs"]):
            category, target = _need(need, f"gates[{index}].needs[{need_index}]")
            if (category, target) in inventory:
                covering.setdefault(gate, []).extend(inventory[(category, target)])
            else:
                missing.append({"gate": gate, "command": command, "category": category, "target": target})
    return {"covered": not missing, "missing": missing, "covering_actions": covering, "writes_state": False}


def run_gate_preflight_coverage_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Runner helper entry point: a gap is an expected failure, never a pass."""
    try:
        data = gate_preflight_coverage(request.inputs)
    except ValueError as error:
        return response(
            "input_error",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "invalid_input",
                    str(error),
                    remediation_summary="Pass every gate with its command and its needs, and the preflight "
                    + "inventory's actions with their category and target.",
                    remediation_actions=["Correct the named input.", "Rerun check-gate-preflight-coverage."],
                )
            ],
        )
    data.update(helper_id=entry.helper_id, operation=entry.operation)
    return response("ok" if data["covered"] else "expected_failure", request_id=request.request_id, data=data)
