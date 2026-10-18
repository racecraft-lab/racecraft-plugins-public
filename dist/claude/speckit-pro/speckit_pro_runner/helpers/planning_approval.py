"""Recorded planning revisions shared by both hosts; no protected authority claim."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from ..atomic_write import snapshot_write_target, write_bytes_atomic
from ..canonical_json import canonical_bytes
from ..formal.evidence import CHECKPOINT_ROWS, read_checkpoint, record_path
from ..formal.primitives import CATALOG_PATH
from ..quality_gates import SHIPPED_DEFAULTS
from ..strict_input import next_fence, require_fields, require_text, unique_object
from ..task_execution import owned_path, path_key, task_definitions
from ..trusted_io import trusted_tree_snapshot
from ..workflow_stage import AUTOPILOT_PLANNING_PREDICATE_PHASES, AUTOPILOT_STAGES, AUTOPILOT_STATUS_VALUES, normalize_status
from ..sweep_export import SWEEP_LOG_HEADING, sweep_table_cells
from .read_only import (SPEC_INDEX_CANONICAL_STARTS, SPEC_INDEX_LEGACY_STARTS, SPEC_INDEX_ENDS,
                        SpecIndexRenderError, render_feature_spec_index, spec_index_is_gated,
                        spec_index_progress)
from .execution_requests import Refusal, run_contained_helper

# Inventory roots are runner-owned, never a caller-selected subset. Feature additions
# are authoritative unless explicitly classified as execution outputs here.
PROJECT_INPUTS = (".specify/memory", ".specify/templates", ".specify/extensions", ".specify/presets",
                  ".specify/quality-gates.json", ".specify/config.json", ".specify/extensions.yml",
                  ".specify/scripts", CATALOG_PATH, "AGENTS.md")
RUNTIME = {"artifacts", "plan-approvals", ".process", "autopilot-state.json", "task-results.json",
           "execution-control.json", "verification-record.json"}


def captured(root: Path, relative: str) -> bytes:
    entry = trusted_tree_snapshot(root / owned_path(relative, root), root)[Path()]
    if isinstance(entry[1], bytes):
        return entry[1]
    raise ValueError(f"planning input must be a readable file: {relative}")


@dataclass(frozen=True)
class ProgressWrite:
    """One protocol write: its locations, typed cells, and optional scaffold."""
    scopes: tuple[tuple[str, ...], ...]
    row: str = ""
    cells: tuple[tuple[int, str], ...] = ()
    width: int = 0
    omit_row: bool = False
    scaffold: tuple[str, ...] = ()
    checkbox: bool = False
    lines: tuple[str, ...] = ()
    key_index: int = 0


OVERVIEW = (("Workflow Overview",),)
BASIC = (("Specification Context", "Basic Information"), ("Basic Information",))
IMPLEMENT = (("Phase 7: Implement", "Implementation Progress"), ("Implementation Progress",))
POST = (("Post-Implementation Checklist",),)
QUALITY = (("Prerequisites", "Quality Gates"), ("Quality Gates",))
LESSONS = (("Lessons Learned",), *(("Lessons Learned", title) for title in
           ("What Worked Well", "Challenges Encountered", "Patterns to Reuse")))
PHASE_NAMES = (*AUTOPILOT_PLANNING_PREDICATE_PHASES, "Implement", "Post")
FIELD_PATTERNS = {
    "phase": "(?:" + "|".join(re.escape(value) for value in AUTOPILOT_STATUS_VALUES) + ")",
    "count": r"[0-9]*(?:/[0-9]+)?",
    "stage": "(?:" + "|".join(AUTOPILOT_STAGES) + ")",
    "pr": r"\[#[0-9]+\]\(https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/[0-9]+\)(?: — [0-9]+ of [0-9]+ artifacts missing)?",
    "result": r"(?:pass|fail|off|not run|n/a: no source files changed|<!-- pass / fail / n/a: no source files changed -->)?",
    "gate:Decision": r"deferred-to-review",
    "gate:Reviewer-owned items": r"[0-9]+ of [0-9]+ unticked across [0-9]+ checklist files",
    "gate:[Gap] markers": r"[0-9]+ \(blocking through G4\)",
    "comment": r"(?:IC|PRRC)_[A-Za-z0-9_=-]+",
    "surface": r"(?:review thread|conversation|review_thread|pr_conversation)",
    "author": r"(?:[A-Za-z0-9-]+|author unresolved)",
    "class": r"(?:amended|answered|deferred|no action)",
    "disposition": r"(?:Applied the accepted feedback to (?:spec|plan|tasks|research|data-model|quickstart)\.md\.|Recorded as answered; no artifact amendment was required\.|Recorded and not acted on because the requested target is outside the allowed artifact set\.|Recorded; no actionable artifact change was identified\.)",
    "categories": r"(?:\[(?:codebase|spec-context|domain|security)\](?:, )?)+",
    "round": r"[123](?:→[23])?",
    "outcome": r"(?:3/3|2/3|escape-hatch|\[ROUND 3\])",
    "resolution": r"(?:Scope deferred)?",
    "analysts": r"(?:All|(?:codebase-analyst|spec-context-analyst|domain-researcher)(?:, (?:codebase-analyst|spec-context-analyst|domain-researcher))*)",
    "commit": r"(?:[a-f0-9]{7,40})?",
    "checkpoint": r"(?:Pending|`[a-f0-9]{40}`)",
}
# One owned table for every Implement write named by the protocol. Summaries are
# accepted only at their listed locations; typed cell rules coexist with them.
PROGRESS_WRITES = {
    "overview-status": ProgressWrite(OVERVIEW, "(?:" + "|".join(PHASE_NAMES) + ")", ((2, "phase"),), 4),
    "overview-summary": ProgressWrite(OVERVIEW),
    "stage": ProgressWrite(BASIC, r"\*\*Stage\*\*", ((1, "stage"),), 2, True),
    "draft-pr": ProgressWrite(BASIC, r"\*\*Draft PR\*\*", ((1, "pr"),), 2, True),
    "implement-checklist-gate": ProgressWrite((("Phase 7: Implement", "Implement Checklist Gate"),),
        r"(?:Decision|Reviewer-owned items|\[Gap\] markers)", ((1, "gate"),), 2, True,
        ("### Implement Checklist Gate", "| Field | Value |")),
    "implementation-progress": ProgressWrite(IMPLEMENT, r".+", ((1, "count"), (2, "count")), 4, checkbox=True),
    "files-generated": ProgressWrite((("Phase 7: Implement", "Files Generated"), ("Files Generated",)), checkbox=True),
    "post-checklist": ProgressWrite(POST, r"Post: .+", ((1, "phase"), (2, "evidence")), 3),
    "success-criteria": ProgressWrite((("Success Criteria",), ("Specification Context", "Success Criteria Summary")), checkbox=True),
    "prerequisites-baseline": ProgressWrite((("Prerequisites",),)),
    "constitution-final": ProgressWrite((("Prerequisites", "Constitution Validation"),)),
    "quality-final": ProgressWrite(QUALITY, r"(?:COMPLEXITY|MUTATION|DEPENDENCY_RULES|DEPENDENCY_AUDIT)", ((6, "result"),), 7),
    "quality-hardener": ProgressWrite(QUALITY),
    "formal-checkpoints": ProgressWrite((("Formal Checkpoints",),), "(?:" + "|".join(CHECKPOINT_ROWS.values()) + ")",
        ((1, "formal"), (2, "formal-evidence")), 3),
    "lessons": ProgressWrite(LESSONS, scaffold=("-",)),
    "feedback-sweep": ProgressWrite(((SWEEP_LOG_HEADING,),), r"[0-9]+",
        ((1, "comment"), (2, "surface"), (3, "author"), (4, "class"), (5, "disposition"), (6, "commit"), (7, "count")), 8, True, scaffold=(
        "## Feedback Sweep Log", "### Feedback Sweep Log", "| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |")),
    "consensus-sweep": ProgressWrite((("Consensus Resolution Log",),), "Sweep",
        ((0, "count"), (2, "comment"), (3, "categories"), (4, "round"), (5, "outcome"), (6, "resolution"), (7, "analysts")), 8, True,
        ("## Consensus Resolution Log", "### Consensus Resolution Log", "| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |"), key_index=1),
    "notes-gap": ProgressWrite(IMPLEMENT),
    "review-followup": ProgressWrite(IMPLEMENT),
    "fallback": ProgressWrite(IMPLEMENT),
    "deferral": ProgressWrite(IMPLEMENT),
    "interpretation": ProgressWrite(IMPLEMENT),
    "plugin-drift": ProgressWrite(IMPLEMENT),
    "marker-checkpoint": ProgressWrite((("PR Marker Plan",), ("PR Marker Plan Evidence",)), r"[0-9]+", ((4, "checkpoint"),), 5,
        lines=(r"- Implementation checkpoint \[[a-z0-9][a-z0-9_-]*\]: `[a-f0-9]{40}`",)),
    "post-integration": ProgressWrite(POST),
    "terms-lint": ProgressWrite(POST),
    "uat-outcome": ProgressWrite(POST),
    "pr-emission": ProgressWrite(POST),
    "spec-map-status": ProgressWrite(()),
    "spec-map-navigation": ProgressWrite(()),
}


def execution_reference(value: str) -> bool:
    """Only relative execution-output paths, never free-form evidence prose."""
    return bool(re.fullmatch(r"(?:[A-Za-z0-9_.-]+/)*\.process/[A-Za-z0-9_./-]+", value)
                and ".." not in value.split("/") and "//" not in value)


def progress_scope(rule: ProgressWrite, scope: tuple[str, ...]) -> bool:
    """Match a declared heading path beneath any document-level parents."""
    return any(scope[-len(target):] == target for target in rule.scopes)


def summary_field(field: str, value: str) -> bool:
    if field == "status":
        return value in {item.casefold().replace(" ", "_") for item in AUTOPILOT_STATUS_VALUES} | {
            "pass", "fail", "unknown", "unavailable", "failed-open", "not_run", "deferred", "waived"}
    if field == "evidence":
        return execution_reference(value)
    if field == "digest":
        return bool(re.fullmatch(r"sha256:[a-f0-9]{64}", value))
    if field in {"count", "tests", "iterations", "score", "floor"}:
        return bool(re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value))
    return False


def progress_summary(text: str, scope: tuple[str, ...]) -> str:
    prefix, marker, value = text.rpartition("Progress: ")
    if not marker:
        return text
    key, *fields = value.strip().split("; ")
    rule = PROGRESS_WRITES.get(key)
    parts = [field.partition("=") for field in fields]
    if rule is None or not progress_scope(rule, scope) or not parts:
        return text
    if len({part[0] for part in parts}) != len(parts) or not all(
        separator and summary_field(field, value) for field, separator, value in parts
    ):
        return text
    if prefix.strip() in ("", "-"):
        # Keep an empty Markdown cell distinct from the table's outer pipes.
        return " "
    return prefix[:-2] + text[len(text.rstrip()):] if prefix.endswith("; ") else text


def progress_cell(kind: str, cell: str, label: str, root: Path, workflow: str) -> bool:
    if kind == "evidence":
        return not cell or execution_reference(cell)
    if kind == "formal":
        checkpoint = next(key for key, value in CHECKPOINT_ROWS.items() if value == label)
        records = [read_checkpoint(root, workflow, checkpoint + suffix) for suffix in ("", "-waiver")]
        return cell == "disabled" or (re.fullmatch(r"[a-z_]+", cell) is not None and
            any(record is not None and record.get("verdict") == cell for record in records))
    if kind == "formal-evidence":
        checkpoint = next(key for key, value in CHECKPOINT_ROWS.items() if value == label)
        return cell == "No selected model" or cell in {
            record_path(root, workflow, checkpoint + suffix).relative_to(root).as_posix()
            for suffix in ("", "-waiver")}
    if kind == "gate":
        return not cell or re.fullmatch(FIELD_PATTERNS["gate:" + label], cell) is not None
    return re.fullmatch(FIELD_PATTERNS[kind], cell) is not None


def progress_row(line: str, rule: ProgressWrite, root: Path, workflow: str) -> str:
    cells = sweep_table_cells(line)
    if len(cells) != rule.width or re.fullmatch(rule.row, cells[rule.key_index]) is None:
        return line
    values = [progress_cell(kind, cells[index], cells[0], root, workflow) for index, kind in rule.cells]
    if rule.omit_row and all(values):
        return ""
    for (index, _), progress in zip(rule.cells, values, strict=True):
        if progress:
            cells[index] = ""
    return "| " + " | ".join(cells) + " |"


def _progress_table_scaffold(line: str, neighbors: tuple[str, str], rules: list[ProgressWrite]) -> bool:
    """A complete owned header/delimiter pair is one typed execution write."""
    headers = [sweep_table_cells(item) for rule in rules for item in rule.scaffold if item.startswith("|")]
    for header, separator in ((neighbors[0], line), (line, neighbors[1])):
        cells = sweep_table_cells(header)
        delimiters = sweep_table_cells(separator)
        if header.startswith("|") and separator.startswith("|") and cells in headers and len(cells) == len(delimiters) and all(
            re.fullmatch(r"-{3,}", cell) for cell in delimiters
        ):
            return True
    return False


def progress_scaffold(line: str, rules: list[ProgressWrite], neighbors: tuple[str, str] = ("", "")) -> bool:
    if _progress_table_scaffold(line, neighbors, rules):
        return True
    stripped = line.strip()
    if any(stripped == item or item.startswith("#") and
           re.fullmatch(r"#{1,6} " + re.escape(item.lstrip("# ")), stripped)
           for rule in rules for item in rule.scaffold if not item.startswith("|")):
        return True
    if any(re.fullmatch(pattern, line.strip()) for rule in rules for pattern in rule.lines):
        return True
    return False


def hardener_progress(line: str, scope: tuple[str, ...]) -> str:
    if not progress_scope(PROGRESS_WRITES["quality-hardener"], scope) or not line.startswith("**Hardener:**"):
        return line
    value, separator, suffix = line.removeprefix("**Hardener:**").strip().partition(" <!--")
    value = "" if value == "not run" else progress_summary(value, scope).strip()
    return "**Hardener:** " + value + separator + suffix


def progress_line(line: str, scope: tuple[str, ...], root: Path, workflow: str,
                  neighbors: tuple[str, str] = ("", "")) -> str:
    rules = [rule for rule in PROGRESS_WRITES.values() if progress_scope(rule, scope)]
    if progress_scaffold(line, rules, neighbors):
        return ""
    line = "|".join(progress_summary(cell, scope) for cell in line.split("|"))
    line = hardener_progress(line, scope)
    for rule in rules:
        if rule.row and line.startswith("|"):
            line = progress_row(line, rule, root, workflow)
    if any(rule.checkbox for rule in rules):
        return re.sub(r"^(\s*-\s+\[)[ xX](\])", r"\1 \2", line)
    return re.sub(r"^(\s*-\s+\[)[xX](\])", r"\1x\2", line)


def workflow_content(content: bytes, root: Path, workflow: str) -> bytes:
    kept: list[tuple[tuple[str, ...], str]] = []
    sections: list[tuple[int, str]] = []
    fence = None
    lines = ["", *content.decode("utf-8").splitlines(keepends=True), ""]
    for index, line in enumerate(lines[1:-1], 1):
        was_fenced = fence is not None
        heading = None if fence else re.match(r"^(#{1,6}) +(.+?)\s*$", line)
        fence = next_fence(fence, line)
        if heading:
            sections = [(level, title) for level, title in sections if level < len(heading[1])]
            sections.append((len(heading[1]), heading[2]))
        scope = tuple(title for _, title in sections)
        result = line if was_fenced or fence else progress_line(
            line.rstrip("\r\n"), scope, root, workflow, (lines[index - 1], lines[index + 1]))
        if result.strip() or was_fenced or fence:
            kept.append((scope, result.rstrip() if not (was_fenced or fence) else result))
    return canonical_bytes(kept)


def spec_map_status(match: re.Match[str]) -> str:
    value = match[2].rstrip()
    if normalize_status(value) == "missing-state":
        return match[0]
    return match[1] + '""' + match[2][len(value):] + match[3]


# Only BACKLINKS may omit bounded runtime filenames. PRS is free-form data:
# even a list of individually plain tokens can assemble unreviewed instructions.
# Bind the entire PRS block instead of inferring trust from rendered Markdown.
# Underscores are literal only inside ASCII words in backlink labels.
NAVIGATION_COMPONENT = r"(?:[A-Za-z0-9.+-]|(?<=[A-Za-z0-9])_+(?=[A-Za-z0-9]))+"
NAVIGATION_TOKEN = rf"(?:PR#-?[0-9]+|{NAVIGATION_COMPONENT}(?:/{NAVIGATION_COMPONENT})*)"


def navigation_progress(line: str, zone: str) -> bool:
    """A bounded generated backlink; all other generated content stays bound."""
    # Canonical renderers escape labels and quote destinations before this check.
    line = unquote(unescape(line))
    return zone == "backlinks" and "www." not in line.casefold() and re.fullmatch(rf"- \[({NAVIGATION_TOKEN})\]\(\1\)", line) is not None


def map_navigation(content: str, expected: dict[str, tuple[str, ...]]) -> bytes:
    """Project exact generated bodies; preserve marker identity, placement and untyped rows."""
    starts = {value: key for source in (SPEC_INDEX_CANONICAL_STARTS, SPEC_INDEX_LEGACY_STARTS)
              for key, value in source.items()}
    raw_lines = content.splitlines(keepends=True)
    seen = set()
    fence = None
    kept = []
    index = 0
    while index < len(raw_lines):
        raw = raw_lines[index]
        was_fenced = fence is not None
        fence = next_fence(fence, raw)
        zone = starts.get(raw.rstrip("\r\n"))
        if zone is None:
            kept.append(raw)
            index += 1
            continue
        if was_fenced or fence:
            return canonical_bytes({"raw": content})
        newline = "\r\n" if raw.endswith("\r\n") else "\n"
        block = [raw, *(line + newline for line in expected[zone]), SPEC_INDEX_ENDS[zone] + newline]
        if zone in seen or raw_lines[index:index + len(block)] != block:
            return canonical_bytes({"raw": content})
        seen.add(zone)
        kept.extend((raw, *(line for line in block[1:-1] if not navigation_progress(line.rstrip("\r\n"), zone)), block[-1]))
        index += len(block)
    return canonical_bytes({"projected": kept})


def spec_map_content(content: bytes, root: Path, feature: str) -> bytes:
    text = content.decode("utf-8")
    frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?=\r?\n|\Z)", text, re.DOTALL)
    if frontmatter is not None:
        normalized_frontmatter = re.sub(r"(?m)^(status:[ \t]*)([^\r\n#]*)(.*)$", spec_map_status, frontmatter[1])
        text = text[:frontmatter.start(1)] + normalized_frontmatter + text[frontmatter.end(1):]
    try:
        expected = spec_index_progress(root, feature) if "<!-- GENERATED:" in text else {}
    except SpecIndexRenderError as error:
        raise ValueError(str(error)) from error
    return map_navigation(text, expected)


def normalized(name: str, content: bytes, workflow: str, feature: str, root: Path) -> bytes:
    if name.endswith("/tasks.md"):
        return task_definitions(content.decode("utf-8")).encode("utf-8")
    if name == workflow:
        return workflow_content(content, root, workflow)
    if name == feature + "/SPEC-MOC.md":
        return spec_map_content(content, root, feature)
    return content


def planning_tree(root: Path, base: str) -> dict[str, bytes | None]:
    path = root / base
    if not path.exists():
        return {base: None}
    if not path.is_dir():
        return {base: captured(root, base)}
    return {(path / relative).relative_to(root).as_posix(): content
            for relative, (_, content) in trusted_tree_snapshot(path, root).items()
            if content is not None and relative.parts[0] not in RUNTIME}


def planning_manifest(root: Path, feature: str, workflow: str) -> dict[str, Any]:
    feature = owned_path(feature, root)
    workflow = owned_path(workflow, root)
    files = {name: content for base in (feature, *PROJECT_INPUTS)
             for name, content in planning_tree(root, base).items()}
    for name in ("spec.md", "plan.md", "tasks.md"):
        files[feature + "/" + name] = captured(root, feature + "/" + name)
    sidecar = feature + "/.process/task-execution.json"
    files[sidecar] = captured(root, sidecar) if (root / sidecar).exists() else None
    files[workflow] = captured(root, workflow)
    catalog_content = files.get(CATALOG_PATH)
    if catalog_content is not None:
        catalog = json.loads(catalog_content, object_pairs_hook=unique_object)
        for model in catalog["models"].values():
            for name in model["inputs"]:
                files[name] = captured(root, name)
    hashes = {name: hashlib.sha256(normalized(name, content, workflow, feature, root)).hexdigest()
                if content is not None else None for name, content in sorted(files.items())}
    manifest = {"schema_version": "planning-manifest/v1", "files": hashes, "verification_defaults": SHIPPED_DEFAULTS}
    return {"manifest": manifest, "manifest_digest": hashlib.sha256(canonical_bytes(manifest)).hexdigest()}


def evidence(root: Path, reference: str) -> dict[str, str]:
    return {"reference": owned_path(reference, root), "sha256": hashlib.sha256(captured(root, reference)).hexdigest()}


def checked_findings(root: Path, feature: str, findings: Any, revision: str) -> dict[str, Any]:
    inventory = json.loads(captured(root, feature + "/planning-findings.json"), object_pairs_hook=unique_object)
    if not isinstance(inventory, dict) or not isinstance(findings, dict) or set(inventory) != set(findings):
        raise ValueError("findings must cover exactly the authoritative planning-findings.json inventory")
    for identity, requests in inventory.items():
        require_text(identity, "finding identity")
        if not isinstance(requests, list) or not requests or len(set(requests)) != len(requests):
            raise ValueError(f"{identity}: requests must be unique non-empty strings")
        for request in requests:
            require_text(request, identity + " request")
        finding = require_fields(findings[identity], {"requests", "correction", "check"}, identity)
        require_text(finding["correction"], identity + " correction")
        check = require_fields(finding["check"], {"status", "manifest_digest", "reference"}, identity + " check")
        if finding["requests"] != requests or check["status"] != "passed" or check["manifest_digest"] != revision:
            raise ValueError(f"{identity}: missing correction or passing check for the final revision")
        evidence(root, check["reference"])
    return findings


def approval_record(root: Path, feature: str, approval: Any, binding: dict[str, Any]) -> dict[str, Any]:
    record = require_fields(approval, {"repository", "planning_run", "repair_runs", "source_commit", "canary_issued",
                                      "supersedes", "superseded_by", "withdrawn_by", "reviewed_evidence", "confirmation", "findings"}, "approval")
    for key in ("repository", "planning_run", "source_commit"):
        require_text(record[key], key)
    if not re.fullmatch(r"[0-9a-f]{40}", record["source_commit"]):
        raise ValueError("source_commit must identify the reviewed source revision")
    if record["canary_issued"] is not False or record["superseded_by"] is not None or record["withdrawn_by"] is not None:
        raise ValueError("production approval refuses canary-issued, superseded or withdrawn records")
    if not isinstance(record["repair_runs"], list):
        raise ValueError("repair_runs must be a list")
    for run in record["repair_runs"]:
        require_text(run, "repair run")
    confirmation = require_fields(record["confirmation"], {"reference", "manifest_digest", "decision", "approver", "time"}, "confirmation")
    for key in ("approver", "time"):
        require_text(confirmation[key], "confirmation " + key)
    if datetime.fromisoformat(confirmation["time"].replace("Z", "+00:00")).tzinfo is None:
        raise ValueError("confirmation time requires an explicit timezone")
    if confirmation["decision"] != "approve" or confirmation["manifest_digest"] != binding["manifest_digest"]:
        raise ValueError("confirmation must explicitly approve the final manifest_digest")
    supplied = json.loads(captured(root, confirmation["reference"]), object_pairs_hook=unique_object)
    if supplied != {k: v for k, v in confirmation.items() if k != "reference"}:
        raise ValueError("confirmation reference does not match the recorded decision")
    refs = record["reviewed_evidence"]
    if not isinstance(refs, list) or not refs or len(set(refs)) != len(refs):
        raise ValueError("reviewed_evidence requires unique repository-relative references")
    reviewed = [evidence(root, ref) for ref in refs]
    reviewed.append(evidence(root, confirmation["reference"]))
    if record["supersedes"] is not None:
        record["supersedes"] = evidence(root, record["supersedes"])["reference"]
    findings = checked_findings(root, feature, record["findings"], binding["manifest_digest"])
    reviewed.extend(evidence(root, finding["check"]["reference"]) for finding in findings.values())
    return {**record, **binding, "schema_version": "plan-approval/v1", "assurance": "recorded",
            "feature_dir": feature, "evidence": reviewed, "findings": findings}


def refuse_superseded(root: Path, path: str) -> None:
    path = owned_path(path, root)
    for _, content in trusted_tree_snapshot((root / path).parent, root).values():
        if content is not None:
            peer = json.loads(content, object_pairs_hook=unique_object)
            if not isinstance(peer, dict) or (peer.get("supersedes") is not None
                                             and path_key(owned_path(peer["supersedes"], root)) == path_key(path)):
                raise ValueError("approval has a subsequent supersession or unreadable history; return to plan review")


def approval_map_snapshot(root: Path, feature: str) -> tuple[Path, dict[str, Any]] | None:
    """Refuse stale generated maps before publishing a decision or changing files."""
    map_path = root / feature / "SPEC-MOC.md"
    map_snapshot = snapshot_write_target(map_path, root)
    original = map_snapshot["content"]
    if not isinstance(original, bytes):
        return None
    text = original.decode("utf-8")
    if not spec_index_is_gated(text) and "<!-- GENERATED:" not in text:
        return None
    message = "regenerate navigation after creating evidence and confirmation files; rebuild and confirm the manifest before recording"
    try:
        rendered = render_feature_spec_index(root, feature, text).encode("utf-8")
    except SpecIndexRenderError as error:
        raise ValueError(message) from error
    projection = json.loads(map_navigation(text, spec_index_progress(root, feature)))
    if rendered != original or "raw" in projection:
        raise ValueError(message)
    return map_path, map_snapshot


def write_approval(root: Path, target: Path, record: dict[str, Any], snapshot: dict[str, Any],
                   map_state: tuple[Path, dict[str, Any]] | None) -> None:
    """Publish the decision and refresh its preflighted canonical feature map."""
    write_bytes_atomic(target, canonical_bytes(record) + b"\n", trust_root=root, expected_snapshot=snapshot)
    if map_state is not None:
        map_path, map_snapshot = map_state
        original = map_snapshot["content"]
        try:
            refreshed = render_feature_spec_index(root, record["feature_dir"], original.decode("utf-8")).encode("utf-8")
            if refreshed != original:
                write_bytes_atomic(map_path, refreshed, trust_root=root, expected_snapshot=map_snapshot)
        except (SpecIndexRenderError, OSError) as error:
            raise ValueError("approval record was written; map refresh failed; regenerate navigation before verification") from error


def planning_approval(root: Path, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    action = inputs.get("action")
    required = {"feature_dir", "workflow_file", "action"} | ({"approval"} if action == "record" else set())
    fields = require_fields({k: v for k, v in inputs.items() if k != "repo_root"}, required, "planning approval inputs")
    feature = owned_path(fields["feature_dir"], root)
    binding = planning_manifest(root, feature, fields["workflow_file"])
    if action == "manifest" and mode == "read_only":
        return {**binding, "writes_state": False}
    path = feature + "/plan-approvals/" + binding["manifest_digest"] + ".json"
    target = root / path
    snapshot = snapshot_write_target(target, root)
    if action == "verify" and mode == "read_only":
        refuse_superseded(root, path)
        stored = json.loads(captured(root, path), object_pairs_hook=unique_object)
        computed = {"manifest", "manifest_digest", "schema_version", "assurance", "feature_dir", "evidence"}
        candidate = {k: v for k, v in stored.items() if k not in computed}
        record = approval_record(root, feature, candidate, binding)
        if record != stored:
            raise ValueError("record bindings or reviewed evidence changed; return to plan review")
    elif action == "record" and mode in {"dry_run", "apply"}:
        map_state = approval_map_snapshot(root, feature)
        record = approval_record(root, feature, fields["approval"], binding)
        if target.exists() and json.loads(captured(root, path)) != record:
            raise ValueError("approval already exists; preserve the original decision")
        if mode == "apply":
            write_approval(root, target, record, snapshot, map_state)
    else:
        raise ValueError("use manifest/verify in read_only, or record in dry_run/apply")
    return {"record": record, "record_path": path, "writes_state": mode == "apply"}


run_planning_approval_helper = partial(
    run_contained_helper,
    work=planning_approval,
    refusal=Refusal(
        "invalid_planning_approval",
        "Correct the named planning approval field and return to plan review.",
        ["Repair the planning inputs or review evidence.", "Retry planning-approval."],
    ),
)
