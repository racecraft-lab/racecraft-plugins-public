"""Check at run start that every gate's required escalation is in the preflight inventory.

A gate that can fail for want of an authorization (data egress, a privileged
command, an interactive login, a write outside the writable roots) must have
that need collected by the Phase 6.5 Autonomy Boundary Preflight, so the
operator is asked at run start, as a chat reply, and not at the end. This
read-only helper names each gate need that no inventoried action covers. A
need is covered only by an action with the same category and the same exact
target. It fails closed and never writes a file.

Given a repository root, it also reads the root agent instruction files and
adds each declared pre-PR command that sends data off the machine (a
dependency audit named in a code span or a fenced code line) as a required
gate. Its need is `external_side_effect` with the exact command as the target.

With `writable_roots` it also requires an inventory action for the private
autonomy-record directory and for each `write_paths` entry that lies outside
those roots, so a sandbox denial on either surfaces at run start. Each missing
`external_side_effect` need is returned as a `policy_classes` entry, the input
`render-egress-authorization` takes as `derived_classes`, so the standing
policy covers it and no gate needs a mid-run approval.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response

# The autonomy-boundary schema's action categories; a test pins the two together.
CATEGORIES = ("outside_writable_roots", "privileged_command", "interactive_authentication", "external_side_effect")
ALLOWED_INPUTS = frozenset({"repo_root", "gates", "inventory_actions", "writable_roots", "write_paths"})
# Root agent instruction files, read in this order; the first file to declare a command is its source.
INSTRUCTION_FILES = ("AGENTS.md", "CLAUDE.md")
# Dependency audits send dependency metadata to a registry or advisory service.
EGRESS_COMMAND = re.compile(r"(?:(?:npm|pnpm|bun)\s+audit|yarn\s+(?:npm\s+)?audit|pip-audit|cargo\s+audit"
                            r"|bundle(?:\s+|-)audit)(?:\s.*)?")
GIT_TIMEOUT_SECONDS = 30
RECORD_GATE = "run-start: private autonomy record"
ROOT_GATE = "run-start: workflow root"
CODE_SPAN = re.compile(r"`([^`\n]+)`")
FENCE = re.compile(r"\s*(?:```|~~~)")


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


def _code_lines(text: str) -> list[str]:
    """Inline code spans and fenced code lines, in document order."""
    found: list[str] = []
    fenced = False
    for line in text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
        elif fenced:
            found.append(line)
        else:
            found.extend(CODE_SPAN.findall(line))
    return found


def declared_commands(root: Path) -> list[dict[str, str]]:
    """Egress-needing commands the root agent instruction files declare; unreadable files fail closed."""
    sources: dict[str, str] = {}
    for name in INSTRUCTION_FILES:
        path = root / name
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise ValueError(f"{name} is unreadable, so its declared pre-PR commands are unknown") from error
        for line in _code_lines(text):
            command = " ".join(line.strip().removeprefix("$ ").split())
            if EGRESS_COMMAND.fullmatch(command):
                sources.setdefault(command, name)
    return [{"command": command, "source": sources[command]} for command in sorted(sources)]


def _paths(value: Any, field: str) -> list[Path]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list of absolute paths")
    paths: list[Path] = []
    for index, raw in enumerate(value):
        text = _text(raw, f"{field}[{index}]")
        if not Path(text).is_absolute():
            raise ValueError(f"{field}[{index}] must be an absolute path")
        paths.append(Path(text).resolve())
    return paths


def private_record_dir(root: Path) -> Path:
    """Where the private autonomy record lives: inside the git common directory, shared by every worktree."""
    try:
        done = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-common-dir"], text=True,
                              capture_output=True, shell=False, check=False, timeout=GIT_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError("git could not report the common directory, so the private record path is unknown") from error
    if done.returncode != 0 or not done.stdout.strip():
        raise ValueError("git could not report the common directory, so the private record path is unknown")
    return (root / done.stdout.strip()).resolve() / "speckit-pro" / "autonomy-boundary"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def derived_policy_classes(missing: list[dict[str, str]], declared: list[dict[str, str]]) -> list[dict[str, str]]:
    """One standing-policy class per missing external_side_effect need, in order."""
    audits = {item["command"] for item in declared}
    classes: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in missing:
        if item["category"] != "external_side_effect":
            continue
        class_id = base = "gate-" + _slug(item["gate"])
        suffix = 1
        while class_id in seen:
            suffix += 1
            class_id = f"{base}-{suffix}"
        seen.add(class_id)
        if item["target"] in audits:
            entry = {"class_id": class_id, "gate": item["gate"],
                     "target": f"the registry or advisory service that `{item['target']}` contacts",
                     "effect": "dependency names and versions sent for a dependency audit",
                     "probe": item["target"]}
        else:
            entry = {"class_id": class_id, "gate": item["gate"], "target": item["target"],
                     "effect": f"repository content that `{item['command']}` sends when the gate runs"}
        classes.append(entry)
    return classes


def gate_preflight_coverage(inputs: Any, root: Path | None = None) -> dict[str, Any]:
    """Which gate needs the inventory covers; raises ValueError on malformed evidence.

    With `root`, each declared pre-PR egress command joins the gates as a required need.
    """
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
    required: list[tuple[str, str, str, str]] = []
    for index, raw in enumerate(gates):
        if not isinstance(raw, dict) or set(raw) != {"gate", "command", "needs"} or not isinstance(raw["needs"], list):
            raise ValueError(f"gates[{index}] must have exactly gate, command, and a needs list")
        gate = _text(raw["gate"], f"gates[{index}].gate")
        command = _text(raw["command"], f"gates[{index}].command")
        required.extend((gate, command, *_need(need, f"gates[{index}].needs[{need_index}]"))
                        for need_index, need in enumerate(raw["needs"]))
    declared = declared_commands(root) if root is not None else []
    for item in declared:
        need = ("external_side_effect", item["command"])
        if not any((category, target) == need for _, _, category, target in required):
            required.append((f"pre-PR: {item['command']}", item["command"], *need))
    private_dir: Path | None = None
    if "writable_roots" in inputs:
        if root is None:
            raise ValueError("writable_roots needs a repository root")
        writable = _paths(inputs["writable_roots"], "writable_roots")
        private_dir = private_record_dir(root)
        surfaces = [(RECORD_GATE, "write the private autonomy record", private_dir)]
        surfaces += [(ROOT_GATE, "write the workflow files", path)
                     for path in _paths(inputs.get("write_paths", []), "write_paths")]
        for gate, command, path in surfaces:
            if not any(path.is_relative_to(base) for base in writable):
                required.append((gate, command, "outside_writable_roots", str(path)))
    elif "write_paths" in inputs:
        raise ValueError("write_paths needs writable_roots")
    missing: list[dict[str, str]] = []
    covering: dict[str, list[str]] = {}
    for gate, command, category, target in required:
        if (category, target) in inventory:
            covering.setdefault(gate, []).extend(inventory[(category, target)])
        else:
            missing.append({"gate": gate, "command": command, "category": category, "target": target})
    return {"covered": not missing, "missing": missing, "covering_actions": covering,
            "declared_commands": declared, "policy_classes": derived_policy_classes(missing, declared),
            "private_record_dir": str(private_dir) if private_dir is not None else None, "writes_state": False}


def run_gate_preflight_coverage_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Runner helper entry point: a gap is an expected failure, never a pass."""
    from .read_only import resolve_repo_root

    root = resolve_repo_root(request.inputs if isinstance(request.inputs, dict) else {})
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    try:
        data = gate_preflight_coverage(request.inputs, root)
    except ValueError as error:
        return response(
            "input_error",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "invalid_input",
                    str(error),
                    remediation_summary="Pass every gate with its command and its needs, and the preflight "
                    + "inventory's actions with their category and target. Keep the root agent instruction "
                    + "files readable UTF-8.",
                    remediation_actions=["Correct the named input.", "Rerun check-gate-preflight-coverage."],
                )
            ],
        )
    data.update(helper_id=entry.helper_id, operation=entry.operation)
    return response("ok" if data["covered"] else "expected_failure", request_id=request.request_id, data=data)
