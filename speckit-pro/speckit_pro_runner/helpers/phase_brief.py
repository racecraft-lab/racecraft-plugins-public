"""Host-neutral planning dispatch facts; gate execution and stop policy stay separate."""

from __future__ import annotations

import re
from pathlib import Path, PureWindowsPath
from typing import Any
from unicodedata import category

from ..envelope import diagnostic, response
from ..strict_input import require_fields, require_text

PHASES = {
    "Specify": ("phase-executor", "G1", ()),
    "Clarify": ("clarify-executor", "G2", ("spec.md",)),
    "Plan": ("phase-executor", "G3", ("spec.md",)),
    "Checklist": ("checklist-executor", "G4", ("spec.md", "plan.md", "checklists/")),
    "Tasks": ("phase-executor", "G5", ("spec.md", "plan.md", "research.md", "data-model.md", "contracts/", "quickstart.md")),
    "Analyze": ("analyze-executor", "G6", ("spec.md", "plan.md", "tasks.md", "checklists/")),
}
REFERENCES = Path(__file__).resolve().parents[2] / "skills" / "speckit-autopilot" / "references"
EXECUTOR_SLICES = (
    ("capability-discovery.md", ("Capability Categories", "Discovery Step", "Research Broker Rule", "Selection Rule", "Capability Boundaries by Role",
                                 "Fallback Rule", "Evidence Output", "Inventory Disclosure")),
    ("grounding.md", ("G1 \u2014 Ground every external claim", "G2 \u2014 Abstain when nothing grounds it",
                      "G3 \u2014 Separate grounded fact from inference", "G4 \u2014 Cite in the evidence note")),
    ("consensus-protocol.md", ("Category tags", "Security Keywords")),
)
SLICE_PHASES = frozenset({"Clarify", "Checklist", "Analyze"})
PROMPT_SECTIONS = {"Clarify": "Clarify Prompts", "Checklist": "Step 2: Run Enriched Checklist Prompts"}


def brief_path(value: Any, label: str) -> str:
    """Validate path text without filesystem access, with portable separators."""
    text = require_text(value, label)
    if any(category(char) in {"Cc", "Zl", "Zp"} for char in text):
        raise ValueError(f"{label} must not contain control characters or line separators")
    path = PureWindowsPath(text)
    if ".." in path.parts:
        raise ValueError(f"{label} must not contain parent traversal segments")
    if label == "feature_dir" and path.anchor:
        raise ValueError("feature_dir must be relative to the workflow root")
    return text


def reference_section(name: str, heading: str) -> str:
    """Return one reference section verbatim: its heading line through the line before the next heading of equal or higher level."""
    try:
        lines = (REFERENCES / name).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"references/{name}: cannot read section {heading!r}") from exc
    start: int | None = None
    level = 0
    fence = ""
    for index, line in enumerate(lines):
        # CommonMark 0.31.2, sections 4.2 and 4.5. Nested fence-like lines
        # are content unless they close the active delimiter and run length.
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip(" \t"):
                fence = ""
            continue
        if marker and (marker[1][0] == "~" or "`" not in marker[2]):
            fence = marker[1]
            continue
        title = re.match(r"^ {0,3}(#{1,6})(?:[ \t]+(.*)|$)", line)
        if title is None:
            continue
        marks = len(title[1])
        text = re.sub(r"[ \t]+#+[ \t]*$", "", title[2] or "").strip(" \t")
        if start is None:
            if text == heading:
                start, level = index, marks
        elif marks <= level:
            return "\n".join(lines[start:index]).rstrip()
    # CommonMark consumes to EOF for an unclosed fence. A packaged reference
    # must instead fail closed rather than dispatch an ambiguous section tail.
    if fence:
        raise ValueError(f"references/{name}: unclosed fence in section {heading!r}")
    if start is None:
        raise ValueError(f"references/{name} has no section {heading!r}")
    return "\n".join(lines[start:]).rstrip()


def phase_slices(phase: str) -> list[str]:
    """Reference excerpts the phase's executor needs, in a closed per-phase order."""
    return [reference_section(name, heading) for name, headings in (EXECUTOR_SLICES if phase in SLICE_PHASES else ()) for heading in headings]


def brief_data(phase: str, workflow: str, feature: str) -> dict[str, Any]:
    """Assemble one validated phase's brief; raises when a packaged reference is unreadable."""
    agent, gate, artifacts = PHASES[phase]
    skill = None if phase == "Clarify" else f"speckit-{phase.lower()}"
    instruction = f"Run the {skill} skill with:" if skill else "Prepare a Clarify Question Set for:"
    return {
        "schema_version": "phase-brief/v1", "phase": phase, "agent": agent,
        "inputs": {"workflow_file": workflow, "feature_dir": feature,
                   "prompt_section": PROMPT_SECTIONS.get(phase, phase + " Prompt"), "instruction": instruction,
                   "skill": skill},
        "readable_files": [workflow, ".specify/memory/constitution.md", ".specify/extensions.yml"] + [feature + "/" + name for name in artifacts],
        "gate": gate, "slices": phase_slices(phase), "waves": [], "model": None, "hooks": [],
    }


def run_phase_brief_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Return phase-brief/v1 dispatch data; gate and stop decisions stay separate.

    The closed request inputs are phase, workflow_file and feature_dir strings.
    Paths reject parent segments and controls; feature_dir is workflow-root
    relative, workflow_file may be absolute. This is lexical validation only:
    no files are opened, symlinks resolved or read permissions enforced.
    Successful data has exactly these fields. Records have only the named keys;
    a wave dispatch's inputs is an open JSON object for its prompt arguments.

    schema_version: str, the literal "phase-brief/v1".
    phase: str, one of Specify, Clarify, Plan, Checklist, Tasks, Analyze.
    agent: str, host-neutral installed executor role, without a namespace.
    inputs: {workflow_file: str, feature_dir: str, prompt_section: str,
        instruction: str, skill: str | null}; workflow context, verbatim prompt
        heading and dispatch prefix. skill is a bare skill id, null for Clarify;
        hosts add their invocation syntax. feature_dir loses trailing slashes.
    readable_files: list[str], ordered phase input paths when present, relative
        to the workflow root unless absolute; a trailing slash means contents.
        Loaded command instructions, templates and scripts remain implicit.
    gate: str, G1 through G6 for the parent's separate validate-gate request.
    slices: list[str], ordered reference excerpts, each a section copied
        verbatim from the plugin's own references, for the orchestrator to
        insert into the dispatch prompt; never paths to whole references.
        Clarify, Checklist and Analyze carry discovery, grounding and
        category-tag sections; the other phases return [].
    waves: list[list[{agent: str, inputs: object, model: ModelSelection}]],
        ordered sequential waves;
        each inner list contains concurrent dispatches, with a host-neutral
        role, JSON prompt inputs and its own model selection per dispatch;
        [] until #1183. ModelSelection has the same shape as model below.
    model: null | {claude: {model: str, effort: str},
        codex: {model: str, effort: str}}, host-specific dispatch configuration;
        applies to the top-level agent only, never every wave member;
        null preserves installed agent defaults until #1184. Claude consumes
        model per call and keeps effort in the agent; Codex consumes both.
    hooks: list[{extension: str, command: str}], ordered optional extension
        command ids to run once after the phase and record in decisions;
        mandatory hooks belong to loaded commands; [] until #1188.

    Empty reserved fields activate no new behavior. Input errors return no data.
    """
    try:
        inputs = require_fields(request.inputs, {"phase", "workflow_file", "feature_dir"}, "phase-brief inputs")
        phase = require_text(inputs["phase"], "phase")
        workflow = brief_path(inputs["workflow_file"], "workflow_file")
        feature = brief_path(inputs["feature_dir"], "feature_dir").rstrip("/")
        if not feature:
            raise ValueError("feature_dir must name a directory")
        if phase not in PHASES:
            raise ValueError("phase must be Specify, Clarify, Plan, Checklist, Tasks or Analyze")
    except ValueError as exc:
        return response("input_error", request_id=request.request_id,
                        diagnostics=[diagnostic("invalid_phase_brief", str(exc))])
    try:
        data = brief_data(phase, workflow, feature)
    except (OSError, ValueError) as exc:
        return response("internal_failure", request_id=request.request_id,
                        diagnostics=[diagnostic("phase_brief_slices_unavailable", str(exc))])
    return response("ok", request_id=request.request_id, data=data)
