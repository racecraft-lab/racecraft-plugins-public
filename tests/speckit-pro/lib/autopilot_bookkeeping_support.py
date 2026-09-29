"""Shared fixtures for the autopilot bookkeeping and guidance tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent
TEST_DIR = LIB_DIR.parent / "unit"
REPO_ROOT = TEST_DIR.parents[2]

from guide_text import guide_text
from script_loader import load_script

PHRASES = json.loads(
    (TEST_DIR / "fixtures" / "autopilot-guidance" / "bookkeeping-guard-phrases.json").read_text(encoding="utf-8")
)


SKILL_SCRIPTS = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "scripts"


VALIDATOR = SKILL_SCRIPTS / "validate-autopilot-phase-coverage.py"


CLAUDE_AUTOPILOT_SKILL = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "SKILL.md"


CODEX_AUTOPILOT_SKILL = REPO_ROOT / "speckit-pro" / "codex-skills" / "speckit-autopilot" / "SKILL.md"


def _load(path: Path, name: str):
    return load_script(name, path)


validator = _load(VALIDATOR, "speckit_autopilot_phase_coverage_under_test")


def workflow(*rows: tuple[str, str], body: str = "") -> str:
    """A minimal workflow document with the given (phase, status) overview rows."""
    lines = ["# Workflow", "", "## Workflow Overview", "", "| Phase | Command | Status | Notes |", "|---|---|---|---|"]
    lines.extend(f"| {phase} | `/speckit-x` | {status} | |" for phase, status in rows)
    lines.extend(["", body])
    return "\n".join(lines)


def _planning_fingerprints(root: Path) -> dict:
    feature = root / "specs" / "demo"
    feature.mkdir(parents=True)
    planning_fingerprints = {}
    for label, content in (("plan_md", b"# Plan\n"), ("tasks_md", b"# Tasks\n")):
        path = feature / ("plan.md" if label == "plan_md" else "tasks.md")
        path.write_bytes(content)
        planning_fingerprints[label] = {
            "path": path.relative_to(root).as_posix(),
            "sha256": validator._sha256_bytes(content),
            "size_bytes": len(content),
        }
    return planning_fingerprints


def _current_execution_boundary(root: Path) -> dict:
    return {
        "execution_environment": "local",
        "sandbox_mode": "workspace-write",
        "approval_reviewer": "auto_review",
        "writable_roots": [str(root)],
    }


def _execution_boundary(root: Path) -> dict:
    execution_scope = _current_execution_boundary(root)
    execution_boundary = {
        **execution_scope,
        "summary": "Repository writes are direct; system writes require approval.",
        "sha256": validator._canonical_json_sha256(execution_scope),
    }
    return execution_boundary


def _autonomy_action(execution_sha256: str) -> dict:
    action_scope = {
        "category": "privileged_command",
        "command_or_tool": "sudo install reviewed payload",
        "target": "/opt/redline",
        "effect": "persistent system-wide runtime installation",
        "execution_boundary_sha256": execution_sha256,
    }
    scope_sha256 = validator._canonical_json_sha256(action_scope)
    return {
        "action_id": "install-runtime",
        **action_scope,
        "scope_sha256": scope_sha256,
        "disposition": "ready",
        "authorization": {
            "status": "explicit_user",
            "evidence": "user approved the exact target and lasting effect",
            "scope_sha256": scope_sha256,
        },
    }


def _autonomy_boundary_state(root: Path) -> dict:
    execution_boundary = _execution_boundary(root)
    return {
        "status": "in_progress",
        "stage": "implement",
        "plan": [
            {"step": "Phase 6.5: Confidence Gate", "status": "completed"},
            {"step": "Phase 7: Implement", "status": "pending"},
        ],
        "autonomy_boundary": {
            "schema_version": "autonomy-boundary.v1",
            "status": "ready",
            "planning_fingerprints": _planning_fingerprints(root),
            "execution_boundary": execution_boundary,
            "actions": [_autonomy_action(execution_boundary["sha256"])],
        },
    }


def _autonomy_errors(state: dict, root: Path) -> list[str]:
    return validator.validate_autonomy_boundary(
        state,
        root,
        current_execution_boundary=_current_execution_boundary(root),
        require_boundary=True,
    )["autonomy_boundary_errors"]


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class _CodexGuides(unittest.TestCase):
    """The Codex skill, phase guide, and prerequisites, whitespace-flattened for phrase checks."""

    HOST_SKILL = CODEX_AUTOPILOT_SKILL
    PREREQUISITES = "prerequisites-codex.md"
    PHASE = "phase-execution-codex.md"
    # attribute -> (guide attribute, start heading, end heading)
    SECTIONS: dict[str, tuple[str, str, str]] = {}
    # attribute -> extra guide, relative to the plugin root
    GUIDES: dict[str, str] = {}

    def setUp(self) -> None:
        references = self.HOST_SKILL.parent / "references"
        self.skill = _flat(self.HOST_SKILL)
        self.phase = _flat(references / self.PHASE)
        self.prerequisites = _flat(references / self.PREREQUISITES)
        for name, (source, start, end) in self.SECTIONS.items():
            setattr(self, name, _section(getattr(self, source), start, end))
        for name, relative in self.GUIDES.items():
            setattr(self, name, guide_text(relative))


def _section_after(case: unittest.TestCase, phase: str, marker: str, heading: str, next_heading: str) -> str:
    """The `heading` section of a phase guide, asserted to sit after `marker`."""
    section = _section(phase, heading, next_heading)
    case.assertLess(phase.index(marker), phase.index(section))
    return section


def _claude_reference(name: str) -> str:
    return _flat(CLAUDE_AUTOPILOT_SKILL.parent / "references" / name)


def _codex_reference(name: str) -> str:
    return _flat(CODEX_AUTOPILOT_SKILL.parent / "references" / name)


def _section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    return text[start : text.index(next_heading, start + len(heading))]


def _assert_phrases(case: unittest.TestCase, text: str, phrases: tuple[str, ...]) -> None:
    for phrase in phrases:
        case.assertIn(phrase, text)


def _assert_absent(case: unittest.TestCase, text: str, phrases: tuple[str, ...]) -> None:
    for phrase in phrases:
        case.assertNotIn(phrase, text)


BLOCKED_ACTION_HEADING = "Blocked Actions Mid-Run: Fall Back or Defer, Never Stop"


SKILL_DIR = "skills/speckit-autopilot/"


CODEX_SKILL_DIR = "codex-skills/speckit-autopilot/"
