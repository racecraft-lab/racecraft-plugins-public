#!/usr/bin/env python3
"""Validate that a Codex autopilot workflow/state pair keeps every phase visible."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
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

TASK_LINE_RE = re.compile(r"^- \[[ xX]\] (T[0-9]+)\b")
UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
WINDOWS_ABSOLUTE_PATH_RE = re.compile(r"^[A-Za-z]:")
MAX_REPO_FILE_BYTES = 32 * 1024 * 1024
HAS_DESCRIPTOR_RELATIVE_IO = (
    os.name != "nt"
    and bool(getattr(os, "O_NOFOLLOW", 0))
    and os.open in os.supports_dir_fd
    and os.stat in os.supports_dir_fd
    and os.stat in os.supports_follow_symlinks
)
SUPPORTED_MARKER_PLAN_VERSIONS = frozenset({"pr-marker-plan.v1", "pr-marker-plan.v2"})
MARKER_PLAN_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "contracts" / "pr-marker-plan.schema.json"
CHANGED_FILE_MANIFEST_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "contracts" / "changed-file-manifest.schema.json"
)
VERIFICATION_REPORT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "contracts" / "verification-report.schema.json"
)
MARKER_PLAN_STATUSES = frozenset({
    "planned", "checkpointing", "emission_ready", "emitting", "emitted",
    "collapsed", "stale", "invalid",
})
COMPLETE_CHECKPOINT_STRING_FIELDS = (
    "evidence_path",
    "checkpoint_evidence_sha",
    "checkpoint_evidence_commit_sha",
    "verification_evidence_path",
    "verification_evidence_sha",
    "commit_sha",
    "head_sha",
    "completed_at",
    "summary",
)
COMPLETE_CHECKPOINT_LIST_FIELDS = (
    "completed_task_ids", "required_verification_gate_ids", "validation",
)
COMPLETE_CHECKPOINT_OBJECT_FIELDS = ("freshness",)
PHASE_VERIFICATION_GATE_ALIASES = {
    "independent_critical_high_review": "independent_review",
}
PHASE_DIRECT_EVIDENCE_BINDINGS = {
    "baseline_commit": ("implementation_baseline_sha", "clean_collection_baseline_sha"),
    "candidate_freeze_id": ("candidate_freeze_id",),
    "capability_fixture_digest": ("capability_fixture_digest",),
    "checkpoint": ("implementation_checkpoint_sha",),
    "implementation_commit": ("implementation_checkpoint_sha",),
    "replay_digest": ("replay_digest",),
    "superseded_checkpoint": ("superseded_checkpoint_sha",),
    "telemetry_profile_id": ("telemetry_profile_id",),
    "treatment_fixture_digest": ("treatment_fixture_digest",),
    "treatment_contract_digest": ("treatment_contract_digest",),
}
PHASE_RESULT_PROJECTION_FIELDS = frozenset({
    "completed_at",
    "completed_task_ids",
    "evidence_finalization_scope",
    "implementation_completed_at",
    "independent_review_chat_id",
    "independent_review_findings",
    "marker_id",
    "pending_task_ids",
    "reviewability",
    "runtime_capability_snapshot_id",
    "status",
    "surface_matrix_id",
    "tasks_completed",
    "tasks_total",
    "updated_at",
})
WORKFLOW_CHECKPOINT_CLAIM_RE = re.compile(
    r"(?m)^-\s+(?:Implementation checkpoint|Current remediation source head)\s+\[([a-z0-9][a-z0-9_-]*)\]:\s+`([0-9a-f]{40})`\s*$"
)
WORKFLOW_SUPERSEDED_CHECKPOINT_CLAIM_RE = re.compile(
    r"(?m)^-\s+Superseded marker checkpoint\s+\[([a-z0-9][a-z0-9_-]*)\]:\s+`([0-9a-f]{40})`\s*$"
)
WORKFLOW_UNSCOPED_CHECKPOINT_CLAIM_RE = re.compile(
    r"(?m)^-\s+(?:Implementation checkpoint|Current remediation source head|Superseded marker checkpoint):\s+`[0-9a-f]{40}`\s*$"
)
WORKFLOW_FINGERPRINT_FIELDS = (
    ("Feature spec", "feature_spec_sha"),
    ("Plan-declared scope", "plan_declared_scope_sha"),
    ("Tasks", "tasks_sha"),
    ("Reviewability evidence", "reviewability_sha"),
    ("Hazard route", "hazard_route_sha"),
    ("Changed-file manifest", "changed_file_manifest_sha"),
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


def _strict_json_loads(value: str | bytes) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = item
        return result

    def reject_non_finite_constant(constant: str) -> None:
        raise ValueError(f"non-finite JSON number is not allowed: {constant}")

    return json.loads(
        value,
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_non_finite_constant,
    )


def load_state(path: Path) -> dict[str, Any]:
    try:
        state = _strict_json_loads(read_text(path))
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
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
    visible_text = _visible_markdown(text)
    visible_lines = [line.strip() for line in visible_text.splitlines()]
    table_rows = [
        line for line in visible_lines if line.startswith("|") and line.endswith("|")
    ]
    table_cells = {
        cell.strip()
        for row in table_rows
        for cell in row[1:-1].split("|")
    }
    missing_sections = [
        section
        for section in WORKFLOW_SECTIONS
        if not any(
            line.startswith(section) if section.endswith(":") else line == section
            for line in visible_lines
        )
    ]
    missing_tokens = [
        token for token in WORKFLOW_TOKENS
        if not any(row.startswith(token) for row in table_rows)
    ]
    missing_post_items = [post for post in POST_STEPS if post not in table_cells]
    return {
        "missing_workflow_sections": missing_sections,
        "missing_workflow_tokens": missing_tokens,
        "missing_workflow_post_items": missing_post_items,
    }


_RAW_HTML_BLOCK_STARTS: tuple[tuple[re.Pattern[str], re.Pattern[str] | None], ...] = (
    (re.compile(r"^[ \t]{0,3}<(script|pre|style|textarea)(?:[ \t>]|$)", re.IGNORECASE), None),
    (re.compile(r"^[ \t]{0,3}<\?"), re.compile(r"\?>")),
    (re.compile(r"^[ \t]{0,3}<![A-Z]"), re.compile(r">")),
    (re.compile(r"^[ \t]{0,3}<!\[CDATA\["), re.compile(r"\]\]>")),
    (
        re.compile(
            r"^[ \t]{0,3}</?(?:address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:[ \t/>]|$)",
            re.IGNORECASE,
        ),
        re.compile(r"^$"),
    ),
    (
        re.compile(
            r"^[ \t]{0,3}(?:</[A-Za-z][A-Za-z0-9-]*[ \t]*>|<[A-Za-z][A-Za-z0-9-]*(?:[ \t]+[^<>]*)?[ \t]*/?>)[ \t]*$"
        ),
        re.compile(r"^$"),
    ),
)


def _raw_html_block_end(line: str) -> re.Pattern[str] | None | bool:
    for start, end in _RAW_HTML_BLOCK_STARTS:
        match = start.search(line)
        if match is None:
            continue
        if match.lastindex and match.group(1):
            return re.compile(rf"</{re.escape(match.group(1))}[ \t]*>", re.IGNORECASE)
        return end
    return False


def _visible_markdown(text: str) -> str:
    """Return Markdown outside comments, code blocks, and raw HTML blocks."""
    visible_lines: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    in_html_comment = False
    raw_html_end: re.Pattern[str] | None | bool = False
    for raw_line in text.splitlines():
        if raw_html_end is not False:
            if raw_html_end is None or raw_html_end.search(raw_line):
                raw_html_end = False
            continue
        if fence_character is not None:
            closing_fence = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})[ \t]*$", raw_line)
            if (
                closing_fence
                and closing_fence.group(1)[0] == fence_character
                and len(closing_fence.group(1)) >= fence_length
            ):
                fence_character = None
                fence_length = 0
            continue

        line_parts: list[str] = []
        offset = 0
        while offset < len(raw_line):
            if in_html_comment:
                comment_end = raw_line.find("-->", offset)
                if comment_end < 0:
                    offset = len(raw_line)
                    break
                in_html_comment = False
                offset = comment_end + 3
                continue
            comment_start = raw_line.find("<!--", offset)
            if comment_start < 0:
                line_parts.append(raw_line[offset:])
                break
            line_parts.append(raw_line[offset:comment_start])
            in_html_comment = True
            offset = comment_start + 4
        line = "".join(line_parts)
        if re.match(r"^(?: {4}| {0,3}\t)", line):
            continue
        raw_html_end = _raw_html_block_end(line)
        if raw_html_end is not False:
            if raw_html_end is not None and raw_html_end.search(line):
                raw_html_end = False
            continue
        if fence_character is None:
            opening_fence = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})", line)
            if opening_fence:
                fence_character = opening_fence.group(1)[0]
                fence_length = len(opening_fence.group(1))
                continue
            visible_lines.append(line)
    return "\n".join(visible_lines)


def validate_workflow_checkpoint_bindings(
    text: str, state: dict[str, Any],
) -> dict[str, list[str]]:
    errors: list[str] = []
    marker_plan = state.get("pr_marker_plan")
    if not isinstance(marker_plan, dict):
        return {"workflow_checkpoint_errors": errors}
    markers = marker_plan.get("markers")
    if not isinstance(markers, list):
        return {"workflow_checkpoint_errors": errors}

    visible_text = _visible_markdown(text)
    expected: dict[str, str | None] = {}
    expected_superseded: dict[str, str] = {}
    for marker in markers:
        if not isinstance(marker, dict) or not isinstance(marker.get("id"), str):
            continue
        checkpoint = marker.get("implementation_checkpoint")
        commit_sha = checkpoint.get("commit_sha") if isinstance(checkpoint, dict) else None
        expected[marker["id"]] = (
            commit_sha
            if isinstance(commit_sha, str) and re.fullmatch(r"[0-9a-f]{40}", commit_sha)
            else None
        )
        superseded_sha = (
            checkpoint.get("superseded_commit_sha")
            if isinstance(checkpoint, dict)
            else None
        )
        if isinstance(superseded_sha, str) and re.fullmatch(r"[0-9a-f]{40}", superseded_sha):
            expected_superseded[marker["id"]] = superseded_sha
    strict_contract = marker_plan.get("schema_version") == "pr-marker-plan.v2"
    if not strict_contract and not any(expected.values()):
        return {"workflow_checkpoint_errors": errors}

    checkpoint_claims = WORKFLOW_CHECKPOINT_CLAIM_RE.findall(visible_text)
    for marker_id, claimed_sha in checkpoint_claims:
        if expected.get(marker_id) != claimed_sha:
            errors.append(
                f"workflow checkpoint claim for marker {marker_id!r} does not match its pr_marker_plan commit_sha"
            )
    for marker_id, claimed_sha in WORKFLOW_SUPERSEDED_CHECKPOINT_CLAIM_RE.findall(visible_text):
        if expected_superseded.get(marker_id) != claimed_sha:
            errors.append(
                f"workflow superseded checkpoint claim for marker {marker_id!r} does not match its pr_marker_plan superseded_commit_sha"
            )
    if WORKFLOW_UNSCOPED_CHECKPOINT_CLAIM_RE.search(visible_text):
        errors.append("workflow checkpoint claims must name their marker")
    if strict_contract:
        for marker_id in expected:
            claim_count = sum(
                claimed_marker_id == marker_id
                for claimed_marker_id, _claimed_sha in checkpoint_claims
            )
            if claim_count != 1:
                errors.append(
                    f"workflow must contain exactly one current checkpoint claim for marker {marker_id!r}"
                )

    section_token = "## PR Marker Plan Evidence"
    section_count = len(re.findall(r"(?m)^## PR Marker Plan Evidence\s*$", visible_text))
    if strict_contract and section_count != 1:
        errors.append("workflow must contain exactly one PR Marker Plan Evidence section")
    if section_count == 1:
        section = visible_text.split(section_token, 1)[1].split("\n## ", 1)[0]
        fingerprint_statuses = re.findall(
            r"(?m)^-\s+Fingerprint status:\s*([^\n]+?)\s*$", section,
        )
        if strict_contract and any(
            status.casefold() == "current" for status in fingerprint_statuses
        ):
            if fingerprint_statuses != ["Current"]:
                errors.append(
                    "workflow PR Marker Plan Evidence must contain exactly one exact "
                    "Fingerprint status: Current claim"
                )
            source_fingerprint = marker_plan.get("source_fingerprint")
            if not isinstance(source_fingerprint, dict):
                errors.append(
                    "workflow Current fingerprint claim requires "
                    "pr_marker_plan.source_fingerprint"
                )
            else:
                fingerprint_rows: dict[str, list[str]] = {
                    label: [] for label, _field in WORKFLOW_FINGERPRINT_FIELDS
                }
                for line in section.splitlines():
                    if not line.startswith("|") or not line.endswith("|"):
                        continue
                    cells = [cell.strip() for cell in line[1:-1].split("|")]
                    if len(cells) != 2 or cells[0] not in fingerprint_rows:
                        continue
                    fingerprint_rows[cells[0]].append(cells[1].strip("` "))
                for label, field in WORKFLOW_FINGERPRINT_FIELDS:
                    expected_value = source_fingerprint.get(field)
                    if fingerprint_rows[label] != [expected_value]:
                        errors.append(
                            f"workflow Current fingerprint {label!r} does not exactly "
                            f"match pr_marker_plan.source_fingerprint.{field}"
                        )
        marker_row_counts = {marker_id: 0 for marker_id in expected}
        for line in section.splitlines():
            if not line.startswith("|") or not line.endswith("|"):
                continue
            cells = [cell.strip() for cell in line[1:-1].split("|")]
            if len(cells) < 5:
                continue
            marker_id = cells[1].strip("` ")
            if marker_id not in expected:
                continue
            marker_row_counts[marker_id] += 1
            checkpoint_shas = set(re.findall(r"\b[0-9a-f]{40}\b", cells[4]))
            expected_sha = expected[marker_id]
            if expected_sha is None or expected_sha not in checkpoint_shas:
                expected_binding = (
                    expected_sha
                    if expected_sha is not None
                    else "its pr_marker_plan commit_sha"
                )
                errors.append(
                    f"workflow PR Marker Plan Evidence marker {marker_id!r} checkpoint does not bind {expected_binding}"
                )
        for marker_id, row_count in marker_row_counts.items():
            if row_count != 1:
                errors.append(
                    f"workflow PR Marker Plan Evidence must contain exactly one row for marker {marker_id!r}"
                )
    return {"workflow_checkpoint_errors": errors}


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


def _pending_value_paths(value: Any, path: str) -> list[str]:
    if isinstance(value, str):
        return [path] if "pending" in value.casefold() else []
    if isinstance(value, list):
        paths: list[str] = []
        for index, item in enumerate(value):
            paths.extend(_pending_value_paths(item, f"{path}[{index}]"))
        return paths
    if isinstance(value, dict):
        paths = []
        for key, item in value.items():
            paths.extend(_pending_value_paths(item, f"{path}.{key}"))
        return paths
    return []


def _repository_root(path: Path) -> Path | None:
    for candidate in (path.parent, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _repo_file(repo_root: Path, raw_path: object) -> Path | None:
    if not _is_normalized_repo_path(raw_path):
        return None
    relative = Path(str(raw_path))
    resolved = (repo_root / relative).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return resolved


def _stable_file_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        metadata.st_nlink,
    )


def _stable_directory_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
    )


def _normalized_absolute_path(path: Path) -> str:
    return os.path.normcase(os.path.abspath(path))


def _windows_final_path_from_descriptor(descriptor: int) -> Path:
    try:
        import ctypes
        import msvcrt
        from ctypes import wintypes
    except ImportError as exc:  # pragma: no cover - available on supported Windows Python
        raise OSError("repository file handle inspection is unavailable") from exc
    get_final_path = ctypes.WinDLL("kernel32", use_last_error=True).GetFinalPathNameByHandleW
    get_final_path.argtypes = [
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    get_final_path.restype = wintypes.DWORD
    handle = wintypes.HANDLE(msvcrt.get_osfhandle(descriptor))
    required = get_final_path(handle, None, 0, 0)
    if required == 0:
        raise OSError("repository file handle could not be resolved")
    buffer = ctypes.create_unicode_buffer(required + 1)
    written = get_final_path(handle, buffer, len(buffer), 0)
    if written == 0 or written >= len(buffer):
        raise OSError("repository file handle could not be resolved")
    value = buffer.value
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return Path(value)


def _repo_path_snapshot(
    source: Path,
    root: Path,
    relative: Path,
) -> tuple[tuple[int, ...], list[tuple[int, ...]], os.stat_result, Path]:
    canonical_root = root.resolve(strict=True)
    canonical_source = source.resolve(strict=True)
    if _normalized_absolute_path(canonical_root) != _normalized_absolute_path(root):
        raise OSError("repository root must be a real directory")
    if _normalized_absolute_path(canonical_source) != _normalized_absolute_path(source):
        raise OSError("repository file path must not contain symlinks")
    canonical_source.relative_to(canonical_root)
    root_metadata = os.stat(root, follow_symlinks=False)
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise OSError("repository root must be a real directory")
    directory_identities: list[tuple[int, ...]] = []
    current = root
    for component in relative.parts[:-1]:
        current /= component
        metadata = os.stat(current, follow_symlinks=False)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise OSError("repository path components must be real directories")
        directory_identities.append(_stable_directory_identity(metadata))
    pathname = os.stat(source, follow_symlinks=False)
    if not stat.S_ISREG(pathname.st_mode) or stat.S_ISLNK(pathname.st_mode):
        raise OSError("repository file must be a regular non-symlink file")
    return (
        _stable_directory_identity(root_metadata),
        directory_identities,
        pathname,
        canonical_source,
    )


def _read_repo_file_by_handle(
    source: Path,
    root: Path,
    relative: Path,
    max_bytes: int,
) -> bytes:
    root_identity, directory_identities, pathname_before, canonical_source = (
        _repo_path_snapshot(source, root, relative)
    )
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_NOINHERIT", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor = os.open(source, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError("repository file must be regular")
        if _stable_file_identity(pathname_before) != _stable_file_identity(before):
            raise OSError("repository file changed before it was opened")
        if os.name == "nt" and (
            _normalized_absolute_path(_windows_final_path_from_descriptor(descriptor))
            != _normalized_absolute_path(canonical_source)
        ):
            raise OSError("repository file handle escaped its approved path")
        if before.st_size > max_bytes:
            raise OSError("repository file exceeds the maximum size")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise OSError("repository file exceeds the maximum size")
        after = os.fstat(descriptor)
        if _stable_file_identity(after) != _stable_file_identity(before) or total != after.st_size:
            raise OSError("repository file changed while it was being read")
        current_root, current_directories, current_pathname, current_canonical = (
            _repo_path_snapshot(source, root, relative)
        )
        if (
            current_root != root_identity
            or current_directories != directory_identities
            or _stable_file_identity(current_pathname) != _stable_file_identity(after)
            or _normalized_absolute_path(current_canonical)
            != _normalized_absolute_path(canonical_source)
        ):
            raise OSError("repository file path changed while it was being read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _read_repo_file_by_descriptor(
    source: Path,
    root: Path,
    relative: Path,
    max_bytes: int,
) -> bytes:
    nofollow = os.O_NOFOLLOW
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | nofollow
        | getattr(os, "O_DIRECTORY", 0)
    )
    file_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | nofollow
        | getattr(os, "O_NONBLOCK", 0)
    )
    directory_descriptors: list[int] = []
    directory_identities: list[tuple[int, ...]] = []
    descriptor: int | None = None
    try:
        root_before = os.stat(root, follow_symlinks=False)
        if not stat.S_ISDIR(root_before.st_mode):
            raise OSError("repository root must be a real directory")
        root_descriptor = os.open(root, directory_flags)
        directory_descriptors.append(root_descriptor)
        root_open = os.fstat(root_descriptor)
        if _stable_directory_identity(root_before) != _stable_directory_identity(root_open):
            raise OSError("repository root changed before it was opened")
        directory_identities.append(_stable_directory_identity(root_open))
        parent_descriptor = root_descriptor
        for component in relative.parts[:-1]:
            component_before = os.stat(
                component,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            if not stat.S_ISDIR(component_before.st_mode):
                raise OSError("repository path components must be real directories")
            child_descriptor = os.open(
                component,
                directory_flags,
                dir_fd=parent_descriptor,
            )
            child_open = os.fstat(child_descriptor)
            if _stable_directory_identity(component_before) != _stable_directory_identity(child_open):
                os.close(child_descriptor)
                raise OSError("repository directory changed before it was opened")
            directory_descriptors.append(child_descriptor)
            directory_identities.append(_stable_directory_identity(child_open))
            parent_descriptor = child_descriptor
        filename = relative.parts[-1]
        pathname_before = os.stat(
            filename,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if not stat.S_ISREG(pathname_before.st_mode):
            raise OSError("repository file must be a regular non-symlink file")
        descriptor = os.open(filename, file_flags, dir_fd=parent_descriptor)
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or _stable_file_identity(pathname_before) != _stable_file_identity(before)
        ):
            raise OSError("repository file changed before it was opened")
        if before.st_size > max_bytes:
            raise OSError("repository file exceeds the maximum size")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise OSError("repository file exceeds the maximum size")
        after = os.fstat(descriptor)
        current = os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
        if (
            _stable_file_identity(after) != _stable_file_identity(before)
            or _stable_file_identity(current) != _stable_file_identity(after)
            or total != after.st_size
        ):
            raise OSError("repository file changed while it was being read")
        verifier_descriptors: list[int] = []
        try:
            root_current = os.stat(root, follow_symlinks=False)
            verifier = os.open(root, directory_flags)
            verifier_descriptors.append(verifier)
            if (
                _stable_directory_identity(root_current) != directory_identities[0]
                or _stable_directory_identity(os.fstat(verifier)) != directory_identities[0]
            ):
                raise OSError("repository root changed while it was being read")
            for component, expected_identity in zip(
                relative.parts[:-1],
                directory_identities[1:],
            ):
                next_descriptor = os.open(component, directory_flags, dir_fd=verifier)
                verifier_descriptors.append(next_descriptor)
                if _stable_directory_identity(os.fstat(next_descriptor)) != expected_identity:
                    raise OSError("repository directory changed while it was being read")
                verifier = next_descriptor
            current_path = os.stat(filename, dir_fd=verifier, follow_symlinks=False)
            if _stable_file_identity(current_path) != _stable_file_identity(after):
                raise OSError("repository file path changed while it was being read")
        finally:
            for verifier_descriptor in reversed(verifier_descriptors):
                os.close(verifier_descriptor)
        return b"".join(chunks)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        for directory_descriptor in reversed(directory_descriptors):
            os.close(directory_descriptor)


def _read_repo_bytes(
    repo_root: Path,
    raw_path: object,
    *,
    max_bytes: int = MAX_REPO_FILE_BYTES,
) -> bytes | None:
    if not _is_normalized_repo_path(raw_path):
        return None
    root = Path(os.path.abspath(repo_root))
    relative = Path(*PurePosixPath(str(raw_path)).parts)
    source = root / relative
    try:
        if HAS_DESCRIPTOR_RELATIVE_IO:
            return _read_repo_file_by_descriptor(source, root, relative, max_bytes)
        return _read_repo_file_by_handle(source, root, relative, max_bytes)
    except (OSError, RuntimeError, ValueError):
        return None


def _sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _string_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        return None
    return value


def _is_normalized_repo_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    if value.startswith("/") or WINDOWS_ABSOLUTE_PATH_RE.match(value):
        return False
    path = PurePosixPath(value)
    return path.as_posix() == value and all(part not in {"", ".", ".."} for part in path.parts)


def _is_utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not UTC_TIMESTAMP_RE.fullmatch(value):
        return False
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == value


def _timestamp_errors(value: object, prefix: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else key
            if key.endswith("_at") and item is not None and not _is_utc_timestamp(item):
                errors.append(f"{child} must be an RFC 3339 UTC timestamp")
            errors.extend(_timestamp_errors(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_timestamp_errors(item, f"{prefix}[{index}]"))
    return errors


def _marker_plan_version_errors(marker_plan: object) -> list[str]:
    if marker_plan is None:
        return []
    if not isinstance(marker_plan, dict):
        return ["pr_marker_plan must be an object"]
    version = marker_plan.get("schema_version")
    if version not in SUPPORTED_MARKER_PLAN_VERSIONS:
        return ["pr_marker_plan.schema_version must be pr-marker-plan.v1 or pr-marker-plan.v2"]
    return []


def _json_values_equal(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return type(left) is type(right) and left == right


def _json_schema_type_matches(value: object, expected: object) -> bool:
    expected_types = expected if isinstance(expected, list) else [expected]
    checks = {
        "array": lambda candidate: isinstance(candidate, list),
        "boolean": lambda candidate: isinstance(candidate, bool),
        "integer": lambda candidate: isinstance(candidate, int) and not isinstance(candidate, bool),
        "null": lambda candidate: candidate is None,
        "number": lambda candidate: isinstance(candidate, (int, float)) and not isinstance(candidate, bool),
        "object": lambda candidate: isinstance(candidate, dict),
        "string": lambda candidate: isinstance(candidate, str),
    }
    return any(
        isinstance(name, str) and name in checks and checks[name](value)
        for name in expected_types
    )


def _resolve_schema_reference(root: dict[str, Any], reference: object) -> object | None:
    if not isinstance(reference, str) or not reference.startswith("#/"):
        return None
    resolved: object = root
    for token in reference[2:].split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(resolved, dict) or key not in resolved:
            return None
        resolved = resolved[key]
    return resolved


def _json_schema_matches(value: object, schema: object, root: dict[str, Any]) -> bool:
    return not _json_schema_errors(value, schema, root, "candidate")


def _json_schema_errors(
    value: object,
    schema: object,
    root: dict[str, Any],
    path: str,
) -> list[str]:
    if schema is True:
        return []
    if schema is False or not isinstance(schema, dict):
        return [f"{path} is rejected by schema"]

    errors: list[str] = []
    if "$ref" in schema:
        resolved = _resolve_schema_reference(root, schema["$ref"])
        if resolved is None:
            errors.append(f"{path} uses an unresolved schema reference")
        else:
            errors.extend(_json_schema_errors(value, resolved, root, path))

    for branch in schema.get("allOf", ()) if isinstance(schema.get("allOf"), list) else ():
        errors.extend(_json_schema_errors(value, branch, root, path))
    any_of = schema.get("anyOf")
    if isinstance(any_of, list) and not any(
        _json_schema_matches(value, branch, root) for branch in any_of
    ):
        errors.append(f"{path} does not match any allowed schema shape")
    one_of = schema.get("oneOf")
    if isinstance(one_of, list) and sum(
        _json_schema_matches(value, branch, root) for branch in one_of
    ) != 1:
        errors.append(f"{path} does not match exactly one allowed schema shape")
    negated = schema.get("not")
    if isinstance(negated, dict) and _json_schema_matches(value, negated, root):
        errors.append(f"{path} matches a prohibited schema shape")
    condition = schema.get("if")
    if isinstance(condition, dict):
        branch = schema.get("then") if _json_schema_matches(value, condition, root) else schema.get("else")
        if branch is not None:
            errors.extend(_json_schema_errors(value, branch, root, path))

    if "const" in schema and not _json_values_equal(value, schema["const"]):
        errors.append(f"{path} does not match its schema constant")
    enum = schema.get("enum")
    if isinstance(enum, list) and not any(_json_values_equal(value, item) for item in enum):
        errors.append(f"{path} is outside its schema enum")
    expected_type = schema.get("type")
    if expected_type is not None and not _json_schema_type_matches(value, expected_type):
        errors.append(f"{path} has the wrong schema type")
        return errors

    if isinstance(value, str):
        minimum_length = schema.get("minLength")
        if isinstance(minimum_length, int) and len(value) < minimum_length:
            errors.append(f"{path} is shorter than allowed")
        pattern = schema.get("pattern")
        if isinstance(pattern, str):
            try:
                matched = re.search(pattern, value) is not None
            except re.error:
                matched = False
            if not matched:
                errors.append(f"{path} does not match its schema pattern")
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isinstance(schema.get("minimum"), (int, float))
        and value < schema["minimum"]
    ):
        errors.append(f"{path} is below its schema minimum")
    if isinstance(value, list):
        minimum_items = schema.get("minItems")
        if isinstance(minimum_items, int) and len(value) < minimum_items:
            errors.append(f"{path} has too few items")
        maximum_items = schema.get("maxItems")
        if isinstance(maximum_items, int) and len(value) > maximum_items:
            errors.append(f"{path} has too many items")
        if schema.get("uniqueItems") is True:
            try:
                serialized = [
                    json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False)
                    for item in value
                ]
            except (RecursionError, TypeError, ValueError) as exc:
                raise ValidationError(
                    f"could not safely compare unique JSON values at {path}"
                ) from exc
            if len(set(serialized)) != len(serialized):
                errors.append(f"{path} must contain unique items")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                errors.extend(_json_schema_errors(item, item_schema, root, f"{path}[{index}]"))
        contains = schema.get("contains")
        if contains is not None and not any(
            _json_schema_matches(item, contains, root) for item in value
        ):
            errors.append(f"{path} does not contain a required schema item")
    if isinstance(value, dict):
        required = schema.get("required") if isinstance(schema.get("required"), list) else []
        missing = sorted(
            key for key in required if isinstance(key, str) and key not in value
        )
        if missing:
            errors.append(f"{path} is missing required fields: {', '.join(missing)}")
        minimum_properties = schema.get("minProperties")
        if isinstance(minimum_properties, int) and len(value) < minimum_properties:
            errors.append(f"{path} has too few properties")
        properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        for key, child_schema in properties.items():
            if key in value:
                errors.extend(
                    _json_schema_errors(value[key], child_schema, root, f"{path}.{key}")
                )
        additional = schema.get("additionalProperties")
        extra = sorted(str(key) for key in value.keys() - properties.keys())
        if additional is False and extra:
            errors.append(f"{path} has unsupported fields: {', '.join(extra)}")
        elif isinstance(additional, dict):
            for key in value.keys() - properties.keys():
                errors.extend(
                    _json_schema_errors(value[key], additional, root, f"{path}.{key}")
                )
    return errors


def _marker_plan_shape_errors(
    marker_plan: object,
    schema: dict[str, Any] | None = None,
) -> list[str]:
    if not isinstance(marker_plan, dict) or marker_plan.get("schema_version") != "pr-marker-plan.v2":
        return []
    if schema is None:
        try:
            schema = _strict_json_loads(read_text(MARKER_PLAN_SCHEMA_PATH))
        except (json.JSONDecodeError, ValueError):
            return ["canonical pr-marker-plan schema is malformed"]
    if not isinstance(schema, dict):
        return ["canonical pr-marker-plan schema root must be an object"]
    return _json_schema_errors(marker_plan, schema, schema, "pr_marker_plan")


def _marker_tasks_sha_text(tasks_text: str, task_ids: set[str]) -> str | None:
    selected: list[str] = []
    found: set[str] = set()
    for line in tasks_text.splitlines():
        match = TASK_LINE_RE.match(line)
        if match and match.group(1) in task_ids:
            selected.append(line)
            found.add(match.group(1))
    if found != task_ids:
        return None
    return _sha256_bytes(("\n".join(selected) + "\n").encode("utf-8"))


def _git_env() -> dict[str, str]:
    return {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"}


def _git_file_at_commit(repo_root: Path, commit_sha: object, relative_path: str) -> bytes | None:
    if not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        return None
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{commit_sha}:{relative_path}"],
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else None


def _canonical_schema(
    schema_path: Path,
    label: str,
    *,
    repo_root: Path | None = None,
    expected_head_commit: str | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Load a canonical schema from the authorized head when one is supplied."""
    errors: list[str] = []
    schema_bytes: bytes | None = None
    exact_head = (
        repo_root is not None
        and isinstance(expected_head_commit, str)
        and re.fullmatch(r"[0-9a-f]{40}", expected_head_commit) is not None
    )
    if exact_head:
        try:
            schema_ref = schema_path.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            return None, [f"canonical {label} schema is outside the authorized repository"]
        schema_bytes = _git_file_at_commit(repo_root, expected_head_commit, schema_ref)
        if schema_bytes is None:
            return None, [f"canonical {label} schema is absent from the authorized PR head"]
        try:
            worktree_schema_bytes = schema_path.read_bytes()
        except OSError:
            worktree_schema_bytes = None
        if worktree_schema_bytes != schema_bytes:
            errors.append(f"canonical {label} schema differs from the authorized PR head")
    else:
        try:
            schema_bytes = schema_path.read_bytes()
        except OSError:
            schema_bytes = None
    try:
        schema = (
            _strict_json_loads(schema_bytes.decode("utf-8"))
            if schema_bytes is not None
            else None
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        schema = None
    if not isinstance(schema, dict):
        errors.append(f"canonical {label} schema is malformed")
        return None, errors
    return schema, errors


def _authorized_workflow_text(
    workflow: Path,
    state_path: Path,
    state: dict[str, Any],
    expected_head_commit: str | None,
) -> tuple[str, list[str]]:
    worktree_text = read_text(workflow)
    marker_plan = state.get("pr_marker_plan")
    if not (
        isinstance(marker_plan, dict)
        and marker_plan.get("schema_version") == "pr-marker-plan.v2"
    ):
        return worktree_text, []
    if expected_head_commit is None:
        return worktree_text, []
    repo_root = _repository_root(state_path)
    if repo_root is None:
        return worktree_text, ["workflow repository root is unavailable"]
    if not isinstance(expected_head_commit, str) or not re.fullmatch(
        r"[0-9a-f]{40}", expected_head_commit
    ):
        return worktree_text, [
            "pr-marker-plan.v2 workflow validation requires external expected_head_commit authority"
        ]
    try:
        workflow_ref = workflow.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return worktree_text, ["workflow file is outside the authorized repository"]
    if not _is_normalized_repo_path(workflow_ref):
        return worktree_text, ["workflow file reference is not repository-relative"]
    state_workflow_ref = state.get("workflow_file")
    if not _is_normalized_repo_path(state_workflow_ref):
        return worktree_text, [
            "autopilot state workflow_file is not a normalized repository-relative path"
        ]
    if state_workflow_ref != workflow_ref:
        return worktree_text, [
            "supplied workflow does not match autopilot state workflow_file authority"
        ]
    committed_bytes = _git_file_at_commit(repo_root, expected_head_commit, workflow_ref)
    if committed_bytes is None:
        return worktree_text, ["workflow is absent from the authorized PR head"]
    try:
        committed_text = committed_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return worktree_text, ["workflow at the authorized PR head is not UTF-8"]
    try:
        worktree_bytes = workflow.read_bytes()
    except OSError:
        worktree_bytes = None
    errors = []
    if worktree_bytes != committed_bytes:
        errors.append("workflow differs from the authorized PR head")
    return committed_text, errors


def _phase_evidence_owner(
    phase_field: str,
    evidence: dict[str, Any],
) -> tuple[str | None, Any]:
    candidates: list[tuple[str, Any, bool]] = []
    direct_fields = PHASE_DIRECT_EVIDENCE_BINDINGS.get(phase_field, ())
    for field in direct_fields:
        if field in evidence:
            candidates.append(
                (f"checkpoint_evidence.{field}", evidence[field], True)
            )
    if phase_field in evidence and phase_field not in direct_fields:
        candidates.append(
            (f"checkpoint_evidence.{phase_field}", evidence[phase_field], False)
        )

    evidence_gate_ids = [
        gate_id
        for gate_id, projected_field in PHASE_VERIFICATION_GATE_ALIASES.items()
        if projected_field == phase_field
    ]
    evidence_gate_ids.append(phase_field)
    for container_name in ("verification", "verification_details"):
        container = evidence.get(container_name)
        if not isinstance(container, dict):
            continue
        for gate_id in evidence_gate_ids:
            if gate_id not in container:
                continue
            value = container[gate_id]
            if isinstance(value, dict):
                value = value.get("evidence")
            candidates.append(
                (f"checkpoint_evidence.{container_name}.{gate_id}", value, True)
            )
    if len(candidates) != 1:
        return ("multiple" if candidates else None), None
    owner, value, permitted = candidates[0]
    return (owner, value) if permitted else (None, None)


def _git_commit_exists(repo_root: Path, commit_sha: object) -> bool:
    if not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        return False
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e", f"{commit_sha}^{{commit}}"],
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    return completed.returncode == 0


def _git_commit_is_ancestor(repo_root: Path, ancestor_sha: str, descendant_sha: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", ancestor_sha, descendant_sha],
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    return completed.returncode == 0


def _git_commit_is_ancestor_of_head(repo_root: Path, commit_sha: str) -> bool:
    return _git_commit_is_ancestor(repo_root, commit_sha, "HEAD")


def _git_path_introduction_commit(
    repo_root: Path, path: object, head_sha: object,
) -> str | None:
    if (
        not _is_normalized_repo_path(path)
        or not isinstance(head_sha, str)
        or not re.fullmatch(r"[0-9a-f]{40}", head_sha)
    ):
        return None
    completed = subprocess.run(
        [
            "git", "-C", str(repo_root), "log", "--diff-filter=A", "--format=%H",
            "--reverse", head_sha, "--", path,
        ],
        text=True,
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        return None
    commits = [line for line in completed.stdout.splitlines() if line]
    return commits[0] if commits else None


def _git_tree_entries(repo_root: Path, commit_sha: object) -> dict[str, str] | None:
    if not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        return None
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "ls-tree", "-r", "-z", "--full-tree", commit_sha],
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        return None
    entries: dict[str, str] = {}
    for raw_record in completed.stdout.split(b"\0"):
        if not raw_record:
            continue
        try:
            raw_identity, raw_path = raw_record.split(b"\t", 1)
            identity = raw_identity.decode("ascii")
            path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError):
            return None
        if path in entries:
            return None
        entries[path] = identity
    return entries


def _load_json_bytes(value: bytes | None) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        parsed = _strict_json_loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def validate_changed_file_manifest(
    state: dict[str, Any],
    state_path: Path,
    *,
    expected_base_commit: str | None = None,
    expected_head_commit: str | None = None,
) -> dict[str, list[str]]:
    marker_plan = state.get("pr_marker_plan")
    repo_root = _repository_root(state_path)
    resolved_head = (
        subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--verify", "HEAD^{commit}"],
            text=True,
            capture_output=True,
            env=_git_env(),
            shell=False,
            check=False,
        )
        if repo_root
        else None
    )
    current_head = (
        resolved_head.stdout.strip()
        if resolved_head is not None and resolved_head.returncode == 0
        else None
    )
    authority_head = (
        expected_head_commit
        if isinstance(expected_head_commit, str)
        and re.fullmatch(r"[0-9a-f]{40}", expected_head_commit)
        else current_head
    )
    state_ref: str | None = None
    committed_state_bytes: bytes | None = None
    committed_state: dict[str, Any] | None = None
    if repo_root and isinstance(authority_head, str):
        try:
            state_ref = state_path.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            state_ref = None
        if state_ref and _is_normalized_repo_path(state_ref):
            committed_state_bytes = _git_file_at_commit(repo_root, authority_head, state_ref)
            committed_state = _load_json_bytes(committed_state_bytes)
    committed_marker_plan = (
        committed_state.get("pr_marker_plan") if isinstance(committed_state, dict) else None
    )
    strict_contract = any(
        isinstance(candidate, dict)
        and candidate.get("schema_version") == "pr-marker-plan.v2"
        for candidate in (marker_plan, committed_marker_plan)
    )
    authority_errors: list[str] = []
    if strict_contract:
        if committed_state_bytes is None or committed_state is None:
            authority_errors.append(
                "autopilot state is absent or invalid at the authorized PR head"
            )
        else:
            try:
                worktree_state_bytes = state_path.read_bytes()
            except OSError:
                worktree_state_bytes = None
            if worktree_state_bytes != committed_state_bytes:
                authority_errors.append(
                    "autopilot state differs from the authorized PR head"
                )
    manifest_ref = state.get("changed_file_manifest")
    if manifest_ref is None:
        if strict_contract:
            return {
                "changed_file_manifest_errors": [
                    "pr-marker-plan.v2 requires a changed_file_manifest reference",
                ],
            }
        return {"changed_file_manifest_errors": []}
    if not _is_normalized_repo_path(manifest_ref):
        return {"changed_file_manifest_errors": ["changed-file manifest reference is invalid"]}
    if repo_root is None:
        return {"changed_file_manifest_errors": ["repository root is unavailable"]}
    worktree_manifest_bytes = _read_repo_bytes(repo_root, manifest_ref)
    manifest = _load_json_bytes(worktree_manifest_bytes)
    if manifest is None:
        return {"changed_file_manifest_errors": ["changed-file manifest is missing or invalid"]}
    if strict_contract:
        committed_manifest_bytes = (
            _git_file_at_commit(repo_root, authority_head, manifest_ref)
            if isinstance(authority_head, str)
            else None
        )
        if committed_manifest_bytes is None:
            authority_errors.append(
                "changed-file manifest is absent from the authorized PR head"
            )
        elif worktree_manifest_bytes != committed_manifest_bytes:
            authority_errors.append(
                "changed-file manifest differs from the authorized PR head"
            )
    manifest_schema, manifest_schema_errors = _canonical_schema(
        CHANGED_FILE_MANIFEST_SCHEMA_PATH,
        "changed-file manifest",
        repo_root=repo_root if strict_contract else None,
        expected_head_commit=expected_head_commit if strict_contract else None,
    )
    authority_errors.extend(manifest_schema_errors)
    if manifest_schema is None:
        return {"changed_file_manifest_errors": authority_errors}
    schema_errors = _json_schema_errors(
        manifest,
        manifest_schema,
        manifest_schema,
        "changed_file_manifest",
    )
    expected_feature_id = state.get("spec_id")
    marker_feature_id = marker_plan.get("feature_id") if isinstance(marker_plan, dict) else None
    identity_errors: list[str] = []
    if not isinstance(expected_feature_id, str) or not expected_feature_id:
        identity_errors.append("autopilot state spec_id is invalid")
    if manifest.get("feature_id") != expected_feature_id:
        identity_errors.append("changed-file manifest feature_id does not match state authority")
    if manifest.get("feature_id") != marker_feature_id:
        identity_errors.append("changed-file manifest feature_id does not match marker-plan authority")
    if manifest.get("comparison_ref") != "HEAD":
        identity_errors.append("changed-file manifest comparison_ref must be HEAD")
    if schema_errors or identity_errors:
        return {
            "changed_file_manifest_errors": [
                *authority_errors,
                *(f"changed-file manifest schema: {error}" for error in schema_errors),
                *identity_errors,
            ],
        }
    base_commit = manifest.get("base_commit")
    entries = manifest.get("files")
    if not isinstance(base_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", base_commit):
        return {"changed_file_manifest_errors": ["changed-file manifest base_commit is invalid"]}
    if not isinstance(entries, list):
        return {"changed_file_manifest_errors": ["changed-file manifest files must be an array"]}
    base_errors: list[str] = []
    if strict_contract:
        if not isinstance(expected_base_commit, str) or not re.fullmatch(
            r"[0-9a-f]{40}", expected_base_commit
        ):
            base_errors.append(
                "pr-marker-plan.v2 changed-file manifest requires external expected_base_commit authority"
            )
        elif base_commit != expected_base_commit:
            base_errors.append(
                "changed-file manifest base_commit does not match external PR base authority"
            )
        if not isinstance(expected_head_commit, str) or not re.fullmatch(
            r"[0-9a-f]{40}", expected_head_commit
        ):
            base_errors.append(
                "pr-marker-plan.v2 changed-file manifest requires external expected_head_commit authority"
            )
        declared_base = state.get("changed_file_manifest_base_commit")
        if not isinstance(declared_base, str) or not re.fullmatch(r"[0-9a-f]{40}", declared_base):
            base_errors.append("pr-marker-plan.v2 requires changed_file_manifest_base_commit")
        elif declared_base != base_commit:
            base_errors.append("changed-file manifest base_commit does not match state authority")
    comparison_commit = expected_head_commit if strict_contract else "HEAD"
    if strict_contract and current_head != expected_head_commit:
        base_errors.append("repository HEAD does not match external PR head authority")
    if not _git_commit_exists(repo_root, base_commit):
        base_errors.append("changed-file manifest base_commit is not an existing commit")
    elif not isinstance(comparison_commit, str) or not _git_commit_exists(
        repo_root, comparison_commit
    ):
        base_errors.append("external PR head authority is not an existing commit")
    elif not _git_commit_is_ancestor(repo_root, base_commit, comparison_commit):
        base_errors.append("changed-file manifest base_commit is not an ancestor of the authorized head")
    if base_errors:
        return {"changed_file_manifest_errors": [*authority_errors, *base_errors]}

    declared: dict[str, tuple[str, str | None]] = {}
    expected_owners: dict[str, set[str]] = {}
    expected_source_owners: dict[str, set[str]] = {}
    rename_sources: set[str] = set()
    structural_errors: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            structural_errors.append(f"files[{index}] must be an object")
            continue
        path = entry.get("path")
        operation = entry.get("operation")
        if not _is_normalized_repo_path(path) or path in declared:
            structural_errors.append(f"files[{index}].path is invalid, unsafe, or duplicated")
            continue
        if operation not in {"NEW", "MODIFIED", "DELETED", "RENAMED"}:
            structural_errors.append(f"files[{index}].operation is invalid")
            continue
        if entry.get("category") not in {
            "generated_artifact", "implementation", "plugin_source", "process", "research", "test",
        }:
            structural_errors.append(f"files[{index}].category is invalid")
        if entry.get("provenance") not in {"authored", "generated"}:
            structural_errors.append(f"files[{index}].provenance is invalid")
        marker_ids = entry.get("marker_ids")
        marker_values = _string_list(marker_ids)
        if marker_values is None or len(marker_values) != 1:
            structural_errors.append(f"files[{index}].marker_ids must contain exactly one marker owner")
        source_path = entry.get("source_path")
        if operation == "RENAMED":
            if (
                not _is_normalized_repo_path(source_path)
                or source_path == path
                or source_path in rename_sources
            ):
                structural_errors.append(
                    f"files[{index}].source_path is invalid, unsafe, duplicated, or unchanged"
                )
            else:
                rename_sources.add(source_path)
                expected_source_owners[source_path] = set(marker_values or ())
        elif source_path is not None:
            structural_errors.append(f"files[{index}].source_path is only valid for RENAMED")
        declared[path] = (operation, source_path if isinstance(source_path, str) else None)
        expected_owners[path] = set(marker_values or ())
    if rename_sources & set(declared):
        structural_errors.append("changed-file manifest rename source paths overlap destination paths")
    if structural_errors:
        return {
            "changed_file_manifest_errors": [*authority_errors, *structural_errors]
        }

    completed = subprocess.run(
        [
            "git", "-C", str(repo_root),
            "-c", "diff.renames=true",
            "-c", "diff.renameLimit=0",
            "diff", "--no-ext-diff", "--find-renames=50%",
            "--ignore-submodules=none", "--name-status",
            f"{base_commit}..{comparison_commit}",
        ],
        text=True,
        capture_output=True,
        env=_git_env(),
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        return {"changed_file_manifest_errors": ["git diff for changed-file manifest failed"]}
    observed: dict[str, tuple[str, str | None]] = {}
    status_map = {"A": "NEW", "M": "MODIFIED", "D": "DELETED"}
    for line in completed.stdout.splitlines():
        fields = line.split("\t")
        status = fields[0]
        if status.startswith("R") and len(fields) == 3:
            observed[fields[2]] = ("RENAMED", fields[1])
        elif status[:1] in status_map and len(fields) == 2:
            observed[fields[1]] = (status_map[status[:1]], None)
        else:
            return {"changed_file_manifest_errors": [f"unsupported git diff record: {line}"]}
    errors = list(authority_errors)
    if declared != observed:
        errors.append(
            f"declared changed-file manifest does not match {base_commit}..{comparison_commit}"
        )

    if worktree_manifest_bytes is None:
        return {"changed_file_manifest_errors": ["changed-file manifest is missing or invalid"]}
    expected_manifest_sha = _sha256_bytes(worktree_manifest_bytes)
    current_fingerprint = state.get("current_source_fingerprint")
    plan_fingerprint = marker_plan.get("source_fingerprint") if isinstance(marker_plan, dict) else None
    for label, fingerprint in (
        ("current_source_fingerprint", current_fingerprint),
        ("pr_marker_plan.source_fingerprint", plan_fingerprint),
    ):
        if not isinstance(fingerprint, dict) or fingerprint.get("changed_file_manifest_sha") != expected_manifest_sha:
            errors.append(f"{label}.changed_file_manifest_sha does not match the changed-file manifest")
    if isinstance(current_fingerprint, dict) and isinstance(plan_fingerprint, dict):
        if current_fingerprint != plan_fingerprint:
            errors.append("current and marker-plan source fingerprints do not match")

    markers = marker_plan.get("markers") if isinstance(marker_plan, dict) else None
    if not isinstance(markers, list):
        errors.append("changed-file manifest requires pr_marker_plan.markers")
        return {"changed_file_manifest_errors": errors}
    marker_operations: dict[str, tuple[str, str | None]] = {}
    actual_owners: dict[str, set[str]] = {}
    actual_source_owners: dict[str, set[str]] = {}
    declared_marker_ids = {
        marker.get("id") for marker in markers
        if isinstance(marker, dict) and isinstance(marker.get("id"), str)
    }
    for path, owners in expected_owners.items():
        if not owners <= declared_marker_ids:
            errors.append(f"changed-file manifest marker owner for {path} is not declared")
    for marker_index, marker in enumerate(markers):
        if not isinstance(marker, dict) or not isinstance(marker.get("id"), str):
            errors.append(f"pr_marker_plan.markers[{marker_index}] is invalid")
            continue
        marker_id = marker["id"]
        marker_files = marker.get("declared_files")
        if not isinstance(marker_files, list):
            errors.append(f"pr_marker_plan.markers[{marker_index}].declared_files must be an array")
            continue
        seen_marker_paths: set[str] = set()
        for file_index, record in enumerate(marker_files):
            if not isinstance(record, dict):
                errors.append(
                    f"pr_marker_plan.markers[{marker_index}].declared_files[{file_index}] must be an object"
                )
                continue
            path = record.get("path")
            operation = record.get("operation")
            source_path = record.get("source_path")
            if not isinstance(path, str) or not path or path in seen_marker_paths:
                errors.append(
                    f"pr_marker_plan.markers[{marker_index}].declared_files[{file_index}].path is invalid or duplicated"
                )
                continue
            seen_marker_paths.add(path)
            operation_record = (
                operation,
                source_path if isinstance(source_path, str) else None,
            )
            if operation_record != declared.get(path):
                errors.append(
                    f"pr_marker_plan marker {marker_id} operation/source for {path} does not match changed-file manifest"
                )
            if path in marker_operations and marker_operations[path] != operation_record:
                errors.append(f"pr_marker_plan declared operation conflict for {path}")
            marker_operations[path] = operation_record
            actual_owners.setdefault(path, set()).add(marker_id)
            if operation == "RENAMED" and isinstance(source_path, str):
                actual_source_owners.setdefault(source_path, set()).add(marker_id)
    if set(marker_operations) != set(declared):
        errors.append("pr_marker_plan declared_files union does not match changed-file manifest")
    for path, owners in expected_owners.items():
        if actual_owners.get(path, set()) != owners:
            errors.append(f"pr_marker_plan marker ownership for {path} does not match changed-file manifest")
    if set(actual_source_owners) != set(expected_source_owners):
        errors.append("pr_marker_plan rename source union does not match changed-file manifest")
    for source_path, owners in expected_source_owners.items():
        if actual_source_owners.get(source_path, set()) != owners:
            errors.append(
                f"pr_marker_plan marker ownership for rename source {source_path} does not match changed-file manifest"
            )
    if strict_contract:
        authorized_tree = _git_tree_entries(repo_root, comparison_commit)
        if authorized_tree is None:
            errors.append("authorized PR head tree is unavailable for checkpoint content binding")
        else:
            verified_trees: dict[str, dict[str, str] | None] = {}
            for marker_index, marker in enumerate(markers):
                if not isinstance(marker, dict):
                    continue
                checkpoint = marker.get("implementation_checkpoint")
                if not isinstance(checkpoint, dict) or checkpoint.get("status") != "complete":
                    continue
                marker_id = marker.get("id")
                verified_commit = checkpoint.get("commit_sha")
                if isinstance(verified_commit, str) and verified_commit not in verified_trees:
                    verified_trees[verified_commit] = _git_tree_entries(repo_root, verified_commit)
                verified_tree = (
                    verified_trees.get(verified_commit)
                    if isinstance(verified_commit, str)
                    else None
                )
                if verified_tree is None:
                    errors.append(
                        f"completed marker {marker_id or marker_index} verified commit tree is unavailable"
                    )
                    continue
                carrier_paths = {
                    path
                    for path in (
                        state_ref,
                        state.get("workflow_file"),
                        manifest_ref,
                        checkpoint.get("evidence_path"),
                        checkpoint.get("verification_evidence_path"),
                    )
                    if isinstance(path, str)
                }
                corrections = checkpoint.get("corrections")
                if isinstance(corrections, list):
                    carrier_paths.update(
                        correction.get("evidence_path")
                        for correction in corrections
                        if isinstance(correction, dict)
                        and isinstance(correction.get("evidence_path"), str)
                    )
                marker_files = marker.get("declared_files")
                if not isinstance(marker_files, list):
                    continue
                for record in marker_files:
                    if not isinstance(record, dict):
                        continue
                    path = record.get("path")
                    if not isinstance(path, str) or path in carrier_paths:
                        continue
                    if verified_tree.get(path) != authorized_tree.get(path):
                        errors.append(
                            f"completed marker {marker_id or marker_index} file {path} differs from its verified commit"
                        )
                    source_path = record.get("source_path")
                    if (
                        record.get("operation") == "RENAMED"
                        and isinstance(source_path, str)
                        and source_path not in carrier_paths
                        and verified_tree.get(source_path) != authorized_tree.get(source_path)
                    ):
                        errors.append(
                            f"completed marker {marker_id or marker_index} rename source {source_path} differs from its verified commit"
                        )
    return {"changed_file_manifest_errors": errors}


def validate_projection_integrity(
    state: dict[str, Any],
    steps: list[PlanStep],
    state_path: Path,
    *,
    expected_head_commit: str | None = None,
) -> dict[str, list[str]]:
    phase_results = state.get("phase_results")
    marker_plan = state.get("pr_marker_plan")
    completed_phase_pending_fields: list[str] = []
    projection_status_errors: list[str] = []
    checkpoint_evidence_errors: list[str] = []
    checkpoint_source_fingerprint_errors: list[str] = []
    checkpoint_file_errors: list[str] = []
    emission_mapping_errors: list[str] = []
    marker_plan_status_errors: list[str] = []
    repo_root = _repository_root(state_path)
    feature_dir = state.get("feature_dir")
    tasks_ref = f"{feature_dir}/tasks.md" if isinstance(feature_dir, str) else None
    current_tasks_bytes = (
        _read_repo_bytes(repo_root, tasks_ref)
        if repo_root is not None and tasks_ref is not None
        else None
    )
    try:
        current_tasks_text = (
            current_tasks_bytes.decode("utf-8")
            if current_tasks_bytes is not None
            else None
        )
    except UnicodeDecodeError:
        current_tasks_text = None
    current_tasks_sha = (
        _sha256_bytes(current_tasks_bytes)
        if current_tasks_bytes is not None
        else None
    )
    strict_contract = (
        isinstance(marker_plan, dict)
        and marker_plan.get("schema_version") == "pr-marker-plan.v2"
    )
    marker_plan_status_errors.extend(_marker_plan_version_errors(marker_plan))
    marker_plan_schema: dict[str, Any] | None = None
    verification_report_schema: dict[str, Any] | None = None
    if strict_contract:
        marker_plan_schema, marker_schema_errors = _canonical_schema(
            MARKER_PLAN_SCHEMA_PATH,
            "pr-marker-plan",
            repo_root=repo_root,
            expected_head_commit=expected_head_commit,
        )
        marker_plan_status_errors.extend(marker_schema_errors)
        if marker_plan_schema is not None:
            marker_plan_status_errors.extend(
                _marker_plan_shape_errors(marker_plan, marker_plan_schema)
            )
        verification_report_schema, verification_schema_errors = _canonical_schema(
            VERIFICATION_REPORT_SCHEMA_PATH,
            "verification report",
            repo_root=repo_root,
            expected_head_commit=expected_head_commit,
        )
        checkpoint_evidence_errors.extend(verification_schema_errors)
    else:
        marker_plan_status_errors.extend(_marker_plan_shape_errors(marker_plan))

    plan_status = marker_plan.get("status") if isinstance(marker_plan, dict) else None
    diagnostic_warnings = {
        "stale": ("MARKER_PLAN_STALE", {"warning", "error"}),
        "invalid": ("MARKER_PLAN_INVALID", {"error"}),
    }
    if plan_status in diagnostic_warnings:
        marker_plan_status_errors.append(
            f"pr_marker_plan.status {plan_status} is a correctness stop"
        )
        if strict_contract:
            code, severities = diagnostic_warnings[plan_status]
            warnings = marker_plan.get("warnings")
            if not isinstance(warnings, list) or not any(
                isinstance(warning, dict)
                and warning.get("code") == code
                and warning.get("severity") in severities
                for warning in warnings
            ):
                marker_plan_status_errors.append(
                    f"pr_marker_plan.status {plan_status} requires diagnostic warning {code}"
                )

    checkpoint_evidence_schema: dict[str, Any] | None = None
    if strict_contract and repo_root:
        if not _is_normalized_repo_path(feature_dir):
            checkpoint_evidence_errors.append(
                "pr-marker-plan.v2 checkpoint evidence requires a normalized feature_dir"
            )
        else:
            checkpoint_schema_ref = (
                f"{feature_dir}/contracts/marker-checkpoint.schema.json"
            )
            committed_schema_bytes = _git_file_at_commit(
                repo_root, expected_head_commit, checkpoint_schema_ref,
            )
            worktree_schema_bytes = _read_repo_bytes(repo_root, checkpoint_schema_ref)
            if committed_schema_bytes is None:
                checkpoint_evidence_errors.append(
                    "checkpoint evidence schema is absent from the authorized PR head"
                )
            else:
                if worktree_schema_bytes != committed_schema_bytes:
                    checkpoint_file_errors.append(
                        "checkpoint evidence schema differs from the authorized PR head"
                    )
                checkpoint_evidence_schema = _load_json_bytes(committed_schema_bytes)
                if checkpoint_evidence_schema is None:
                    checkpoint_evidence_errors.append(
                        "checkpoint evidence schema at the authorized PR head is malformed"
                    )

    markers = marker_plan.get("markers") if isinstance(marker_plan, dict) else None
    declared_marker_ids = {
        marker.get("id")
        for marker in markers or []
        if isinstance(marker, dict)
        and isinstance(marker.get("id"), str)
        and marker["id"]
    }
    phases = phase_results if isinstance(phase_results, dict) else {}
    phases_by_marker: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for phase_name, raw_result in phases.items():
        if not isinstance(phase_name, str) or not isinstance(raw_result, dict):
            continue
        phase_marker_id = raw_result.get("marker_id")
        if isinstance(phase_marker_id, str) and phase_marker_id:
            phases_by_marker.setdefault(phase_marker_id, []).append(
                (phase_name, raw_result)
            )
        if strict_contract and phase_name.startswith("Phase 7: Implement"):
            if not isinstance(phase_marker_id, str) or not phase_marker_id:
                marker_plan_status_errors.append(
                    f"phase_results[{phase_name}] must declare exactly one marker_id"
                )
            elif phase_marker_id not in declared_marker_ids:
                marker_plan_status_errors.append(
                    f"phase_results[{phase_name}] marker_id {phase_marker_id!r} is not declared by pr_marker_plan"
                )
        result_status = raw_result.get("status")
        matching_steps = [step for step in steps if step.step == phase_name or step.step.startswith(f"{phase_name} (")]
        if result_status in {"completed", "in_progress", "pending", "checkpointing"} and matching_steps:
            expected_plan_status = "completed" if result_status == "completed" else result_status
            if matching_steps[0].status != expected_plan_status:
                projection_status_errors.append(
                    f"plan[{matching_steps[0].step}]={matching_steps[0].status!r} "
                    f"does not match phase_results[{phase_name}].status={result_status!r}"
                )
        if result_status == "completed":
            completed_phase_pending_fields.extend(
                _pending_value_paths(raw_result, f"phase_results.{phase_name}")
            )

    if isinstance(markers, list):
        if strict_contract:
            marker_plan_status_errors.extend(_timestamp_errors(marker_plan, "pr_marker_plan"))
        seen_marker_ids: set[str] = set()
        seen_review_orders: set[int] = set()
        task_owners: dict[str, str] = {}
        file_owners: dict[str, str] = {}
        for index, raw_marker in enumerate(markers):
            if not isinstance(raw_marker, dict):
                continue
            marker_id = raw_marker.get("id")
            if not isinstance(marker_id, str) or not marker_id:
                marker_plan_status_errors.append(f"pr_marker_plan.markers[{index}].id is invalid")
                marker_id = f"marker[{index}]"
            elif marker_id in seen_marker_ids:
                marker_plan_status_errors.append(f"pr_marker_plan marker id {marker_id!r} is duplicated")
            else:
                seen_marker_ids.add(marker_id)
            review_order = raw_marker.get("review_order")
            if not isinstance(review_order, int) or isinstance(review_order, bool) or review_order < 1:
                marker_plan_status_errors.append(
                    f"pr_marker_plan.markers[{index}].review_order is invalid"
                )
            elif review_order in seen_review_orders:
                marker_plan_status_errors.append(
                    f"pr_marker_plan review_order {review_order} is duplicated"
                )
            else:
                seen_review_orders.add(review_order)
            if (
                isinstance(review_order, int)
                and not isinstance(review_order, bool)
                and review_order >= 1
                and review_order != index + 1
            ):
                marker_plan_status_errors.append(
                    f"pr_marker_plan.markers[{index}].review_order must equal its "
                    f"contiguous marker array position {index + 1}"
                )

            source_boundary = raw_marker.get("source_boundary")
            story_id = source_boundary.get("story_id") if isinstance(source_boundary, dict) else None
            kind = raw_marker.get("kind")
            parent_marker_id = raw_marker.get("parent_marker_id")
            expected_identity: tuple[str, object, object] | None = None
            if kind == "user_story" and isinstance(story_id, int):
                expected_identity = (f"us{story_id}", story_id, None)
            elif kind == "user_story_part" and isinstance(story_id, int):
                if not isinstance(marker_id, str) or not re.fullmatch(fr"us{story_id}-part[0-9]+", marker_id):
                    marker_plan_status_errors.append(
                        f"pr_marker_plan.markers[{index}] user_story_part id does not match story_id {story_id}"
                    )
                if parent_marker_id != f"us{story_id}":
                    marker_plan_status_errors.append(
                        f"pr_marker_plan.markers[{index}] user_story_part parent does not match story_id {story_id}"
                    )
            elif kind == "foundation":
                expected_identity = ("foundation", None, None)
            elif kind == "full_spec":
                expected_identity = ("full-spec", None, None)
            elif kind == "polish":
                expected_identity = ("polish", None, None)
            else:
                marker_plan_status_errors.append(
                    f"pr_marker_plan.markers[{index}] kind/story_id combination is invalid"
                )
            if expected_identity is not None:
                expected_id, expected_story_id, expected_parent = expected_identity
                if marker_id != expected_id or story_id != expected_story_id or parent_marker_id != expected_parent:
                    marker_plan_status_errors.append(
                        f"pr_marker_plan.markers[{index}] id, kind, story_id, and parent_marker_id are inconsistent"
                    )

            task_values = _string_list(raw_marker.get("task_ids"))
            folded_values = _string_list(raw_marker.get("folded_polish_task_ids"))
            if task_values is not None and len(set(task_values)) != len(task_values):
                marker_plan_status_errors.append(
                    f"pr_marker_plan.markers[{index}].task_ids contains duplicates"
                )
            if folded_values is not None and len(set(folded_values)) != len(folded_values):
                marker_plan_status_errors.append(
                    f"pr_marker_plan.markers[{index}].folded_polish_task_ids contains duplicates"
                )
            for task_id in (task_values or []) + (folded_values or []):
                owner = task_owners.get(task_id)
                if owner is not None:
                    marker_plan_status_errors.append(
                        f"pr_marker_plan task {task_id!r} is owned by both {owner!r} and {marker_id!r}"
                    )
                else:
                    task_owners[task_id] = marker_id

            declared_files = raw_marker.get("declared_files")
            if isinstance(declared_files, list):
                for file_index, record in enumerate(declared_files):
                    path = record.get("path") if isinstance(record, dict) else None
                    operation = record.get("operation") if isinstance(record, dict) else None
                    source_path = record.get("source_path") if isinstance(record, dict) else None
                    if strict_contract and (
                        not _is_normalized_repo_path(path)
                        or repo_root and _repo_file(repo_root, path) is None
                    ):
                        marker_plan_status_errors.append(
                            f"pr_marker_plan.markers[{index}].declared_files[{file_index}].path is not a normalized repository-relative path"
                        )
                        continue
                    owned_paths = [("file", path)]
                    if operation == "RENAMED":
                        if strict_contract and (
                            not _is_normalized_repo_path(source_path)
                            or source_path == path
                            or repo_root and _repo_file(repo_root, source_path) is None
                        ):
                            marker_plan_status_errors.append(
                                f"pr_marker_plan.markers[{index}].declared_files[{file_index}].source_path is not a normalized repository-relative rename source"
                            )
                            continue
                        owned_paths.append(("rename source", source_path))
                    elif source_path is not None:
                        marker_plan_status_errors.append(
                            f"pr_marker_plan.markers[{index}].declared_files[{file_index}].source_path is only valid for RENAMED"
                        )
                    for path_kind, owned_path in owned_paths:
                        owner = file_owners.get(owned_path)
                        if owner is not None:
                            marker_plan_status_errors.append(
                                f"pr_marker_plan {path_kind} {owned_path!r} is owned by both {owner!r} and {marker_id!r}"
                            )
                        else:
                            file_owners[owned_path] = marker_id

            reviewability = raw_marker.get("reviewability")
            if strict_contract and isinstance(reviewability, dict) and "evidence_path" in reviewability:
                evidence_path_value = reviewability.get("evidence_path")
                if not _is_normalized_repo_path(evidence_path_value) or repo_root and _repo_file(repo_root, evidence_path_value) is None:
                    marker_plan_status_errors.append(
                        f"pr_marker_plan.markers[{index}].reviewability.evidence_path is not a normalized repository-relative path"
                    )
            checkpoint = raw_marker.get("implementation_checkpoint")
            if isinstance(checkpoint, dict):
                checkpoint_status = checkpoint.get("status")
                pending_phase_claims = [
                    (phase_name, phase_field)
                    for phase_name, phase_result in phases_by_marker.get(marker_id, [])
                    for phase_field in phase_result
                    if phase_field not in PHASE_RESULT_PROJECTION_FIELDS
                ]
                if strict_contract and checkpoint_status == "pending" and pending_phase_claims:
                    if not _is_normalized_repo_path(checkpoint.get("evidence_path")):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] pending checkpoint with phase claims requires evidence_path"
                        )
                    if not isinstance(checkpoint.get("commit_sha"), str) or not re.fullmatch(
                        r"[0-9a-f]{40}", checkpoint["commit_sha"]
                    ):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] pending checkpoint with phase claims requires commit_sha"
                        )
                for path_field in ("evidence_path", "verification_evidence_path") if strict_contract else ():
                    path_value = checkpoint.get(path_field)
                    if path_value is not None and (
                        not _is_normalized_repo_path(path_value)
                        or repo_root and _repo_file(repo_root, path_value) is None
                    ):
                        checkpoint_file_errors.append(
                            f"pr_marker_plan.markers[{index}].implementation_checkpoint.{path_field} is not a normalized repository-relative path"
                        )
                if checkpoint_status == "complete" and strict_contract:
                    for required in COMPLETE_CHECKPOINT_STRING_FIELDS:
                        if not isinstance(checkpoint.get(required), str) or not checkpoint[required].strip():
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.{required}"
                            )
                    for required in COMPLETE_CHECKPOINT_LIST_FIELDS:
                        value = checkpoint.get(required)
                        if (
                            not isinstance(value, list)
                            or not value
                            or not all(isinstance(item, str) and item for item in value)
                            or len(set(value)) != len(value)
                        ):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.{required}"
                            )
                    for required in COMPLETE_CHECKPOINT_OBJECT_FIELDS:
                        if not isinstance(checkpoint.get(required), dict):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.{required}"
                            )
                    task_ids = _string_list(raw_marker.get("task_ids"))
                    folded_task_ids = _string_list(raw_marker.get("folded_polish_task_ids"))
                    expected_tasks = set(task_ids or ()) | set(folded_task_ids or ())
                    completed_tasks = _string_list(checkpoint.get("completed_task_ids"))
                    if task_ids is None or folded_task_ids is None:
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] marker task coverage"
                        )
                    elif completed_tasks is not None and set(completed_tasks) != expected_tasks:
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}].implementation_checkpoint.completed_task_ids coverage"
                        )
                    if checkpoint.get("commit_sha") != checkpoint.get("head_sha"):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}].implementation_checkpoint commit/head mismatch"
                        )
                    reviewability = raw_marker.get("reviewability")
                    reviewed_head = reviewability.get("head_sha") if isinstance(reviewability, dict) else None
                    if reviewed_head != checkpoint.get("head_sha"):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] checkpoint/reviewability head mismatch"
                        )
                    if repo_root:
                        committed_verification_bytes: bytes | None = None
                        evidence_commit_sha = checkpoint.get("checkpoint_evidence_commit_sha")
                        claimed_commit_sha = checkpoint.get("commit_sha")
                        if not _git_commit_exists(repo_root, evidence_commit_sha):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.checkpoint_evidence_commit_sha is not an existing commit"
                            )
                        elif not _git_commit_is_ancestor_of_head(repo_root, evidence_commit_sha):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.checkpoint_evidence_commit_sha is not an ancestor of HEAD"
                            )
                        elif (
                            _git_commit_exists(repo_root, claimed_commit_sha)
                            and not _git_commit_is_ancestor(
                                repo_root, claimed_commit_sha, evidence_commit_sha,
                            )
                        ):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}] implementation commit is not an ancestor of evidence commit"
                            )
                        evidence_ref = checkpoint.get("evidence_path")
                        verification_ref = checkpoint.get("verification_evidence_path")
                        worktree_evidence_bytes = _read_repo_bytes(
                            repo_root,
                            evidence_ref,
                        )
                        worktree_verification_bytes = _read_repo_bytes(
                            repo_root,
                            verification_ref,
                        )
                        for required, worktree_bytes in (
                            ("evidence_path", worktree_evidence_bytes),
                            ("verification_evidence_path", worktree_verification_bytes),
                        ):
                            if worktree_bytes is None:
                                checkpoint_file_errors.append(
                                    f"pr_marker_plan.markers[{index}].implementation_checkpoint.{required}"
                                )
                        if evidence_ref == verification_ref:
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}] checkpoint and verification evidence paths must differ"
                            )
                        committed_evidence_bytes = (
                            _git_file_at_commit(
                                repo_root,
                                checkpoint.get("checkpoint_evidence_commit_sha"),
                                evidence_ref,
                            )
                            if isinstance(evidence_ref, str)
                            else None
                        )
                        if committed_evidence_bytes is None:
                            checkpoint_file_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.checkpoint_evidence_commit_sha"
                            )
                        else:
                            expected_evidence_sha = _sha256_bytes(committed_evidence_bytes)
                            if checkpoint.get("checkpoint_evidence_sha") != expected_evidence_sha:
                                checkpoint_file_errors.append(
                                    f"pr_marker_plan.markers[{index}].implementation_checkpoint.checkpoint_evidence_sha"
                                )
                            if worktree_evidence_bytes != committed_evidence_bytes:
                                checkpoint_file_errors.append(
                                    f"pr_marker_plan.markers[{index}].implementation_checkpoint immutable evidence differs from checkpoint commit"
                                )
                        committed_verification_bytes = (
                            _git_file_at_commit(
                                repo_root,
                                checkpoint.get("checkpoint_evidence_commit_sha"),
                                verification_ref,
                            )
                            if isinstance(verification_ref, str)
                            else None
                        )
                        if committed_verification_bytes is None:
                            checkpoint_file_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint verification evidence is absent from checkpoint commit"
                            )
                        else:
                            expected_verification_sha = _sha256_bytes(committed_verification_bytes)
                            if checkpoint.get("verification_evidence_sha") != expected_verification_sha:
                                checkpoint_file_errors.append(
                                    f"pr_marker_plan.markers[{index}].implementation_checkpoint.verification_evidence_sha"
                                )
                            if worktree_verification_bytes != committed_verification_bytes:
                                checkpoint_file_errors.append(
                                    f"pr_marker_plan.markers[{index}].implementation_checkpoint immutable verification evidence differs from checkpoint commit"
                                )

                pending_authority_fields = (
                    "checkpoint_evidence_sha",
                    "checkpoint_evidence_commit_sha",
                    "verification_evidence_path",
                    "verification_evidence_sha",
                )
                if (
                    checkpoint_status == "pending"
                    and strict_contract
                    and repo_root
                    and any(field in checkpoint for field in pending_authority_fields)
                ):
                    evidence_commit_sha = checkpoint.get("checkpoint_evidence_commit_sha")
                    claimed_commit_sha = checkpoint.get("commit_sha")
                    evidence_ref = checkpoint.get("evidence_path")
                    verification_ref = checkpoint.get("verification_evidence_path")
                    if not _git_commit_exists(repo_root, evidence_commit_sha):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}].implementation_checkpoint.checkpoint_evidence_commit_sha is not an existing commit"
                        )
                    elif not (
                        isinstance(expected_head_commit, str)
                        and _git_commit_is_ancestor(
                            repo_root, evidence_commit_sha, expected_head_commit,
                        )
                    ):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}].implementation_checkpoint.checkpoint_evidence_commit_sha is not an ancestor of the authorized PR head"
                        )
                    elif (
                        _git_commit_exists(repo_root, claimed_commit_sha)
                        and not _git_commit_is_ancestor(
                            repo_root, claimed_commit_sha, evidence_commit_sha,
                        )
                    ):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] implementation commit is not an ancestor of evidence commit"
                        )
                    if evidence_ref == verification_ref:
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] checkpoint and verification evidence paths must differ"
                        )
                    committed_pending_evidence = (
                        _git_file_at_commit(repo_root, evidence_commit_sha, evidence_ref)
                        if isinstance(evidence_ref, str)
                        else None
                    )
                    authorized_pending_evidence = (
                        _git_file_at_commit(repo_root, expected_head_commit, evidence_ref)
                        if isinstance(evidence_ref, str)
                        else None
                    )
                    worktree_pending_evidence = _read_repo_bytes(repo_root, evidence_ref)
                    if committed_pending_evidence is None:
                        checkpoint_file_errors.append(
                            f"pr_marker_plan.markers[{index}].implementation_checkpoint.checkpoint_evidence_commit_sha"
                        )
                    else:
                        if checkpoint.get("checkpoint_evidence_sha") != _sha256_bytes(
                            committed_pending_evidence
                        ):
                            checkpoint_file_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.checkpoint_evidence_sha"
                            )
                        if authorized_pending_evidence != committed_pending_evidence:
                            checkpoint_file_errors.append(
                                f"pr_marker_plan.markers[{index}] pending checkpoint evidence differs from checkpoint commit"
                            )
                        if worktree_pending_evidence != committed_pending_evidence:
                            checkpoint_file_errors.append(
                                f"pr_marker_plan.markers[{index}] pending checkpoint evidence worktree differs from checkpoint commit"
                            )
                    committed_pending_verification = (
                        _git_file_at_commit(repo_root, evidence_commit_sha, verification_ref)
                        if isinstance(verification_ref, str)
                        else None
                    )
                    authorized_pending_verification = (
                        _git_file_at_commit(repo_root, expected_head_commit, verification_ref)
                        if isinstance(verification_ref, str)
                        else None
                    )
                    worktree_pending_verification = _read_repo_bytes(
                        repo_root,
                        verification_ref,
                    )
                    if committed_pending_verification is None:
                        checkpoint_file_errors.append(
                            f"pr_marker_plan.markers[{index}].implementation_checkpoint verification evidence is absent from checkpoint commit"
                        )
                    else:
                        if checkpoint.get("verification_evidence_sha") != _sha256_bytes(
                            committed_pending_verification
                        ):
                            checkpoint_file_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.verification_evidence_sha"
                            )
                        if authorized_pending_verification != committed_pending_verification:
                            checkpoint_file_errors.append(
                                f"pr_marker_plan.markers[{index}] pending verification evidence differs from checkpoint commit"
                            )
                        if worktree_pending_verification != committed_pending_verification:
                            checkpoint_file_errors.append(
                                f"pr_marker_plan.markers[{index}] pending verification evidence worktree differs from checkpoint commit"
                            )

                evidence_ref = checkpoint.get("evidence_path")
                authorized_evidence_bytes: bytes | None = None
                if strict_contract and repo_root and isinstance(evidence_ref, str):
                    authorized_evidence_bytes = _git_file_at_commit(
                        repo_root, expected_head_commit, evidence_ref,
                    )
                    if authorized_evidence_bytes is None:
                        checkpoint_file_errors.append(
                            f"pr_marker_plan.markers[{index}] checkpoint evidence is absent from the authorized PR head"
                        )
                    else:
                        if _read_repo_bytes(repo_root, evidence_ref) != authorized_evidence_bytes:
                            checkpoint_file_errors.append(
                                f"pr_marker_plan.markers[{index}] checkpoint evidence differs from the authorized PR head"
                            )
                immutable_evidence_bytes = (
                    _git_file_at_commit(
                        repo_root,
                        checkpoint.get("checkpoint_evidence_commit_sha"),
                        evidence_ref,
                    )
                    if checkpoint_status == "complete"
                    and repo_root
                    and isinstance(evidence_ref, str)
                    else None
                )
                evidence = _load_json_bytes(
                    authorized_evidence_bytes
                    if strict_contract
                    else immutable_evidence_bytes
                )
                if checkpoint_status != "complete" and not strict_contract:
                    evidence = _load_json_bytes(
                        _read_repo_bytes(repo_root, evidence_ref)
                        if repo_root is not None
                        else None
                    )
                if (
                    strict_contract
                    and repo_root is not None
                    and expected_head_commit is not None
                    and isinstance(evidence_ref, str)
                    and not isinstance(evidence, dict)
                ):
                    checkpoint_evidence_errors.append(
                        f"pr_marker_plan.markers[{index}] checkpoint evidence must be a JSON object"
                    )
                projection_evidence = evidence
                if strict_contract and isinstance(evidence, dict):
                    if checkpoint_evidence_schema is not None:
                        checkpoint_evidence_errors.extend(
                            f"pr_marker_plan.markers[{index}] checkpoint evidence schema: {error}"
                            for error in _json_schema_errors(
                                evidence,
                                checkpoint_evidence_schema,
                                checkpoint_evidence_schema,
                                "checkpoint_evidence",
                            )
                        )
                    superseded_evidence = checkpoint.get("superseded_evidence")
                    if (
                        superseded_evidence is not None
                        and checkpoint.get("corrections") is not None
                    ):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}].implementation_checkpoint must not declare both corrections and superseded_evidence"
                        )
                    correction_authority = (
                        superseded_evidence
                        if isinstance(superseded_evidence, dict)
                        else checkpoint
                    )
                    corrections = correction_authority.get("corrections")
                    correction_prefix = (
                        f"{feature_dir}/.process/checkpoint-corrections/{marker_id}-"
                    )
                    authorized_tree = _git_tree_entries(
                        repo_root, expected_head_commit,
                    ) if repo_root is not None else None
                    discovered_corrections = sorted(
                        path
                        for path in authorized_tree or {}
                        if path.startswith(correction_prefix)
                        and re.fullmatch(
                            rf"{re.escape(correction_prefix)}[0-9]{{3}}\.json",
                            path,
                        )
                    )
                    declared_corrections = (
                        [
                            correction.get("evidence_path")
                            for correction in corrections
                            if isinstance(correction, dict)
                        ]
                        if isinstance(corrections, list)
                        else []
                    )
                    if discovered_corrections != declared_corrections:
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] checkpoint correction state does not cover the authorized append-only correction files"
                        )
                    correction_projection_evidence = json.loads(json.dumps(evidence))
                    if superseded_evidence is not None:
                        prefix = (
                            f"pr_marker_plan.markers[{index}].implementation_checkpoint."
                            "superseded_evidence"
                        )
                        if not isinstance(superseded_evidence, dict):
                            checkpoint_evidence_errors.append(
                                f"{prefix} must be an object"
                            )
                        elif repo_root is not None:
                            superseded_path = superseded_evidence.get("evidence_path")
                            superseded_commit = superseded_evidence.get(
                                "checkpoint_evidence_commit_sha"
                            )
                            superseded_sha = superseded_evidence.get(
                                "checkpoint_evidence_sha"
                            )
                            superseded_implementation = superseded_evidence.get(
                                "implementation_checkpoint_sha"
                            )
                            committed_superseded = (
                                _git_file_at_commit(
                                    repo_root, superseded_commit, superseded_path,
                                )
                                if isinstance(superseded_path, str)
                                else None
                            )
                            authorized_superseded = (
                                _git_file_at_commit(
                                    repo_root, expected_head_commit, superseded_path,
                                )
                                if isinstance(superseded_path, str)
                                else None
                            )
                            if (
                                not _is_normalized_repo_path(superseded_path)
                                or superseded_path == evidence_ref
                            ):
                                checkpoint_file_errors.append(
                                    f"{prefix}.evidence_path is invalid or current"
                                )
                            if not _git_commit_exists(repo_root, superseded_commit):
                                checkpoint_evidence_errors.append(
                                    f"{prefix}.checkpoint_evidence_commit_sha is not an existing commit"
                                )
                            elif not (
                                isinstance(expected_head_commit, str)
                                and _git_commit_is_ancestor(
                                    repo_root, superseded_commit, expected_head_commit,
                                )
                            ):
                                checkpoint_evidence_errors.append(
                                    f"{prefix}.checkpoint_evidence_commit_sha is not an ancestor of the authorized PR head"
                                )
                            if not _git_commit_exists(
                                repo_root, superseded_implementation,
                            ):
                                checkpoint_evidence_errors.append(
                                    f"{prefix}.implementation_checkpoint_sha is not an existing commit"
                                )
                            elif (
                                isinstance(superseded_commit, str)
                                and not _git_commit_is_ancestor(
                                    repo_root,
                                    superseded_implementation,
                                    superseded_commit,
                                )
                            ):
                                checkpoint_evidence_errors.append(
                                    f"{prefix}.implementation_checkpoint_sha is not an ancestor of its evidence commit"
                                )
                            current_evidence_commit = checkpoint.get(
                                "checkpoint_evidence_commit_sha"
                            )
                            if (
                                isinstance(current_evidence_commit, str)
                                and isinstance(superseded_commit, str)
                                and _git_commit_exists(repo_root, current_evidence_commit)
                                and not _git_commit_is_ancestor(
                                    repo_root, superseded_commit, current_evidence_commit,
                                )
                            ):
                                checkpoint_evidence_errors.append(
                                    f"{prefix} does not precede the current checkpoint evidence"
                                )
                            if committed_superseded is None:
                                checkpoint_file_errors.append(
                                    f"{prefix} evidence is absent from its evidence commit"
                                )
                            else:
                                if superseded_sha != _sha256_bytes(committed_superseded):
                                    checkpoint_file_errors.append(
                                        f"{prefix}.checkpoint_evidence_sha"
                                    )
                                if authorized_superseded != committed_superseded:
                                    checkpoint_file_errors.append(
                                        f"{prefix} differs from the authorized PR head"
                                    )
                                if _read_repo_bytes(repo_root, superseded_path) != committed_superseded:
                                    checkpoint_file_errors.append(
                                        f"{prefix} worktree bytes differ from its evidence commit"
                                    )
                                parsed_superseded = _load_json_bytes(
                                    committed_superseded
                                )
                                if not isinstance(parsed_superseded, dict):
                                    checkpoint_evidence_errors.append(
                                        f"{prefix} evidence must be a JSON object"
                                    )
                                else:
                                    correction_projection_evidence = parsed_superseded
                                    if checkpoint_evidence_schema is not None:
                                        superseded_schema_errors = _json_schema_errors(
                                            parsed_superseded,
                                            checkpoint_evidence_schema,
                                            checkpoint_evidence_schema,
                                            "superseded_checkpoint_evidence",
                                        )
                                        checkpoint_evidence_errors.extend(
                                            f"{prefix} schema: {error}"
                                            for error in superseded_schema_errors
                                        )
                                    if (
                                        parsed_superseded.get("feature_id")
                                        != marker_plan.get("feature_id")
                                        or parsed_superseded.get("marker_id")
                                        != marker_id
                                        or parsed_superseded.get("status") != "complete"
                                        or parsed_superseded.get(
                                            "implementation_checkpoint_sha"
                                        )
                                        != superseded_implementation
                                    ):
                                        checkpoint_evidence_errors.append(
                                            f"{prefix} identity does not match marker state"
                                        )
                    if checkpoint_status == "complete" and corrections is not None:
                        if (
                            not isinstance(corrections, list)
                            or superseded_evidence is None and not corrections
                        ):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.corrections must be a non-empty array"
                            )
                        elif repo_root is not None:
                            previous_path = correction_authority.get("evidence_path")
                            previous_commit = correction_authority.get(
                                "checkpoint_evidence_commit_sha"
                            )
                            previous_sha = correction_authority.get(
                                "checkpoint_evidence_sha"
                            )
                            correction_paths: set[str] = set()
                            correction_schema = {
                                "$ref": "#/$defs/checkpoint_correction_record"
                            }
                            for correction_index, correction in enumerate(corrections):
                                prefix = (
                                    f"pr_marker_plan.markers[{index}].implementation_checkpoint."
                                    f"corrections[{correction_index}]"
                                )
                                if not isinstance(correction, dict):
                                    checkpoint_evidence_errors.append(
                                        f"{prefix} must be an object"
                                    )
                                    continue
                                correction_valid = True
                                if correction.get("sequence") != correction_index + 1:
                                    checkpoint_evidence_errors.append(
                                        f"{prefix}.sequence must be append-only and contiguous"
                                    )
                                    correction_valid = False
                                supersedes = (
                                    correction.get("supersedes_evidence_path"),
                                    correction.get("supersedes_evidence_commit_sha"),
                                    correction.get("supersedes_evidence_sha"),
                                )
                                if supersedes != (
                                    previous_path, previous_commit, previous_sha,
                                ):
                                    checkpoint_evidence_errors.append(
                                        f"{prefix} does not supersede the previous authorized checkpoint evidence"
                                    )
                                    correction_valid = False
                                correction_path = correction.get("evidence_path")
                                correction_commit = correction.get(
                                    "checkpoint_evidence_commit_sha"
                                )
                                correction_sha = correction.get(
                                    "checkpoint_evidence_sha"
                                )
                                if (
                                    not _is_normalized_repo_path(correction_path)
                                    or correction_path
                                    != f"{correction_prefix}{correction_index + 1:03d}.json"
                                    or correction_path == previous_path
                                    or correction_path in correction_paths
                                ):
                                    checkpoint_file_errors.append(
                                        f"{prefix}.evidence_path is invalid or reused"
                                    )
                                    correction_valid = False
                                else:
                                    correction_paths.add(correction_path)
                                if not _git_commit_exists(repo_root, correction_commit):
                                    checkpoint_evidence_errors.append(
                                        f"{prefix}.checkpoint_evidence_commit_sha is not an existing commit"
                                    )
                                    correction_valid = False
                                introduction_commit = _git_path_introduction_commit(
                                    repo_root, correction_path, expected_head_commit,
                                )
                                if introduction_commit != correction_commit:
                                    checkpoint_evidence_errors.append(
                                        f"{prefix}.checkpoint_evidence_commit_sha is not the immutable path-introduction commit"
                                    )
                                    correction_valid = False
                                elif not (
                                    isinstance(expected_head_commit, str)
                                    and _git_commit_is_ancestor(
                                        repo_root, correction_commit, expected_head_commit,
                                    )
                                ):
                                    checkpoint_evidence_errors.append(
                                        f"{prefix}.checkpoint_evidence_commit_sha is not an ancestor of the authorized PR head"
                                    )
                                    correction_valid = False
                                elif (
                                    isinstance(previous_commit, str)
                                    and not _git_commit_is_ancestor(
                                        repo_root, previous_commit, correction_commit,
                                    )
                                ):
                                    checkpoint_evidence_errors.append(
                                        f"{prefix} does not descend from the superseded evidence commit"
                                    )
                                    correction_valid = False
                                committed_correction = (
                                    _git_file_at_commit(
                                        repo_root, correction_commit, correction_path,
                                    )
                                    if isinstance(correction_path, str)
                                    else None
                                )
                                authorized_correction = (
                                    _git_file_at_commit(
                                        repo_root, expected_head_commit, correction_path,
                                    )
                                    if isinstance(correction_path, str)
                                    else None
                                )
                                worktree_correction = _read_repo_bytes(
                                    repo_root,
                                    correction_path,
                                )
                                if committed_correction is None:
                                    checkpoint_file_errors.append(
                                        f"{prefix} evidence is absent from its correction commit"
                                    )
                                    correction_valid = False
                                else:
                                    if correction_sha != _sha256_bytes(
                                        committed_correction
                                    ):
                                        checkpoint_file_errors.append(
                                            f"{prefix}.checkpoint_evidence_sha"
                                        )
                                        correction_valid = False
                                    if authorized_correction != committed_correction:
                                        checkpoint_file_errors.append(
                                            f"{prefix} differs from the authorized PR head"
                                        )
                                        correction_valid = False
                                    if worktree_correction != committed_correction:
                                        checkpoint_file_errors.append(
                                            f"{prefix} worktree bytes differ from its correction commit"
                                        )
                                        correction_valid = False
                                correction_record = _load_json_bytes(
                                    committed_correction
                                )
                                if not isinstance(correction_record, dict):
                                    checkpoint_evidence_errors.append(
                                        f"{prefix} evidence must be a JSON object"
                                    )
                                    correction_valid = False
                                elif checkpoint_evidence_schema is not None:
                                    correction_schema_errors = _json_schema_errors(
                                        correction_record,
                                        correction_schema,
                                        checkpoint_evidence_schema,
                                        "checkpoint_correction",
                                    )
                                    checkpoint_evidence_errors.extend(
                                        f"{prefix} schema: {error}"
                                        for error in correction_schema_errors
                                    )
                                    correction_valid = (
                                        correction_valid
                                        and not correction_schema_errors
                                    )
                                if isinstance(correction_record, dict):
                                    record_authority = (
                                        correction_record.get(
                                            "supersedes_evidence_path"
                                        ),
                                        correction_record.get(
                                            "supersedes_evidence_commit_sha"
                                        ),
                                        correction_record.get(
                                            "supersedes_evidence_sha"
                                        ),
                                    )
                                    if (
                                        correction_record.get("feature_id")
                                        != marker_plan.get("feature_id")
                                        or correction_record.get("marker_id")
                                        != marker_id
                                        or correction_record.get("sequence")
                                        != correction_index + 1
                                        or record_authority != supersedes
                                    ):
                                        checkpoint_evidence_errors.append(
                                            f"{prefix} evidence authority does not match marker state"
                                        )
                                        correction_valid = False
                                if correction_valid and isinstance(
                                    correction_record, dict
                                ):
                                    removals = correction_record.get(
                                        "remove_evidence_owners"
                                    )
                                    for removal in removals or []:
                                        container_name, field_name = removal.split(".", 1)
                                        container = correction_projection_evidence.get(
                                            container_name
                                        )
                                        if (
                                            not isinstance(container, dict)
                                            or field_name not in container
                                        ):
                                            checkpoint_evidence_errors.append(
                                                f"{prefix} removes a missing evidence owner {removal!r}"
                                            )
                                            correction_valid = False
                                            break
                                        del container[field_name]
                                previous_path = correction_path
                                previous_commit = correction_commit
                                previous_sha = correction_sha
                            if superseded_evidence is None:
                                projection_evidence = correction_projection_evidence
                            elif (
                                isinstance(previous_commit, str)
                                and isinstance(
                                    checkpoint.get("checkpoint_evidence_commit_sha"),
                                    str,
                                )
                                and not _git_commit_is_ancestor(
                                    repo_root,
                                    previous_commit,
                                    checkpoint["checkpoint_evidence_commit_sha"],
                                )
                            ):
                                checkpoint_evidence_errors.append(
                                    f"pr_marker_plan.markers[{index}].implementation_checkpoint.superseded_evidence correction chain does not precede the current checkpoint evidence"
                                )
                    if evidence.get("status") != checkpoint_status:
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] checkpoint evidence status does not match checkpoint status"
                        )
                    claimed_commit = checkpoint.get("commit_sha")
                    if claimed_commit != evidence.get("implementation_checkpoint_sha"):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] checkpoint commit_sha does not match checkpoint evidence implementation_checkpoint_sha"
                        )
                    if repo_root is not None:
                        if not _git_commit_exists(repo_root, claimed_commit):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}] checkpoint commit_sha is not an existing commit"
                            )
                        elif not (
                            isinstance(expected_head_commit, str)
                            and re.fullmatch(r"[0-9a-f]{40}", expected_head_commit)
                            and _git_commit_is_ancestor(
                                repo_root, claimed_commit, expected_head_commit,
                            )
                        ):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}] checkpoint commit_sha is not an ancestor of the authorized PR head"
                            )
                    for phase_name, phase_result in phases_by_marker.get(marker_id, []):
                        for phase_field, phase_value in phase_result.items():
                            if phase_field in PHASE_RESULT_PROJECTION_FIELDS:
                                continue
                            owner, evidence_value = _phase_evidence_owner(
                                phase_field, projection_evidence,
                            )
                            if owner is None:
                                checkpoint_evidence_errors.append(
                                    f"pr_marker_plan.markers[{index}] phase_results[{phase_name}] {phase_field} has no checkpoint evidence owner"
                                )
                            elif owner == "multiple":
                                checkpoint_evidence_errors.append(
                                    f"pr_marker_plan.markers[{index}] phase_results[{phase_name}] {phase_field} has multiple checkpoint evidence owners"
                                )
                            elif not _json_values_equal(phase_value, evidence_value):
                                checkpoint_evidence_errors.append(
                                    f"pr_marker_plan.markers[{index}] phase_results[{phase_name}] {phase_field} does not match checkpoint evidence"
                                )
                if checkpoint_status == "complete" and strict_contract and repo_root:
                    claimed_commit = checkpoint.get("commit_sha")
                    verification_report = _load_json_bytes(committed_verification_bytes)
                    if not isinstance(verification_report, dict):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] verification report must be a JSON object"
                        )
                    elif verification_report_schema is not None:
                        checkpoint_evidence_errors.extend(
                            f"pr_marker_plan.markers[{index}] verification report schema: {error}"
                            for error in _json_schema_errors(
                                verification_report,
                                verification_report_schema,
                                verification_report_schema,
                                "verification_report",
                            )
                        )
                    if not isinstance(evidence, dict):
                        checkpoint_evidence_errors.append(
                            f"pr_marker_plan.markers[{index}] checkpoint evidence must be a JSON object"
                        )
                    else:
                        expected_feature_id = marker_plan.get("feature_id") if isinstance(marker_plan, dict) else None
                        required_gate_ids = _string_list(
                            checkpoint.get("required_verification_gate_ids")
                        )
                        evidence_gate_ids = _string_list(
                            evidence.get("required_verification_gate_ids")
                        )
                        verification = evidence.get("verification")
                        report_gate_ids = (
                            _string_list(verification_report.get("required_gate_ids"))
                            if isinstance(verification_report, dict)
                            else None
                        )
                        report_results = (
                            verification_report.get("results")
                            if isinstance(verification_report, dict)
                            else None
                        )
                        gate_sets_match = (
                            required_gate_ids is not None
                            and evidence_gate_ids is not None
                            and len(required_gate_ids) == len(set(required_gate_ids))
                            and len(evidence_gate_ids) == len(set(evidence_gate_ids))
                            and set(required_gate_ids) == set(evidence_gate_ids)
                            and isinstance(verification, dict)
                            and set(verification) == set(required_gate_ids)
                        )
                        passing_results = (
                            gate_sets_match
                            and all(
                                isinstance(result, dict)
                                and set(result) == {"status", "evidence"}
                                and result.get("status") == "pass"
                                and isinstance(result.get("evidence"), str)
                                and bool(result["evidence"].strip())
                                for result in verification.values()
                            )
                        )
                        report_gate_sets_match = (
                            gate_sets_match
                            and report_gate_ids is not None
                            and required_gate_ids == evidence_gate_ids == report_gate_ids
                            and isinstance(report_results, dict)
                            and set(report_results) == set(required_gate_ids)
                        )
                        report_passing_results = (
                            report_gate_sets_match
                            and all(
                                isinstance(result, dict)
                                and set(result) == {"status", "evidence"}
                                and result.get("status") == "pass"
                                and isinstance(result.get("evidence"), str)
                                and bool(result["evidence"].strip())
                                for result in report_results.values()
                            )
                        )
                        report_results_match = (
                            report_passing_results
                            and report_results == verification
                        )
                        evidence_checks = {
                            "schema_version": evidence.get("schema_version") == "marker-checkpoint.v1",
                            "feature_id": evidence.get("feature_id") == expected_feature_id,
                            "marker_id": evidence.get("marker_id") == marker_id,
                            "status": evidence.get("status") == "complete",
                            "completed_at": _is_utc_timestamp(evidence.get("completed_at")),
                            "tasks_sha": (
                                isinstance(evidence.get("tasks_sha"), str)
                                and re.fullmatch(r"sha256:[0-9a-f]{64}", evidence["tasks_sha"]) is not None
                            ),
                            "source_fingerprint_status": evidence.get("source_fingerprint_status") == "current",
                            "verification_evidence_sha": (
                                committed_verification_bytes is not None
                                and evidence.get("verification_evidence_sha")
                                == checkpoint.get("verification_evidence_sha")
                                == _sha256_bytes(committed_verification_bytes)
                            ),
                            "required_verification_gate_ids": gate_sets_match,
                            "verification": passing_results,
                        }
                        checkpoint_evidence_errors.extend(
                            f"pr_marker_plan.markers[{index}] checkpoint evidence {field} is invalid"
                            for field, passed in evidence_checks.items() if not passed
                        )
                        verification_report_checks = {
                            "schema_version": (
                                isinstance(verification_report, dict)
                                and verification_report.get("schema_version")
                                == "verification-report.v1"
                            ),
                            "feature_id": (
                                isinstance(verification_report, dict)
                                and verification_report.get("feature_id") == expected_feature_id
                            ),
                            "marker_id": (
                                isinstance(verification_report, dict)
                                and verification_report.get("marker_id") == marker_id
                            ),
                            "status": (
                                isinstance(verification_report, dict)
                                and verification_report.get("status") == "pass"
                            ),
                            "generated_at": (
                                isinstance(verification_report, dict)
                                and _is_utc_timestamp(verification_report.get("generated_at"))
                            ),
                            "verified_commit_sha": (
                                isinstance(verification_report, dict)
                                and verification_report.get("verified_commit_sha")
                                == claimed_commit
                            ),
                            "required_gate_ids": report_gate_sets_match,
                            "results": report_results_match,
                        }
                        checkpoint_evidence_errors.extend(
                            f"pr_marker_plan.markers[{index}] verification report {field} is invalid"
                            for field, passed in verification_report_checks.items() if not passed
                        )
                        if evidence.get("implementation_checkpoint_sha") != claimed_commit:
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}] checkpoint/evidence implementation commit mismatch"
                            )
                    if repo_root:
                        if not _git_commit_exists(repo_root, claimed_commit):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.commit_sha is not an existing commit"
                            )
                        elif not _git_commit_is_ancestor_of_head(repo_root, claimed_commit):
                            checkpoint_evidence_errors.append(
                                f"pr_marker_plan.markers[{index}].implementation_checkpoint.commit_sha is not an ancestor of HEAD"
                            )
                if (
                    strict_contract
                    and evidence is not None
                    and current_tasks_text is not None
                    and current_tasks_sha
                ):
                    primary_task_values = _string_list(raw_marker.get("task_ids"))
                    folded_task_values = _string_list(raw_marker.get("folded_polish_task_ids"))
                    marker_task_values = (
                        [*primary_task_values, *folded_task_values]
                        if primary_task_values is not None and folded_task_values is not None
                        else None
                    )
                    marker_task_ids = set(marker_task_values or ())
                    evidence_task_values = _string_list(evidence.get("task_ids"))
                    freshness = checkpoint.get("freshness") if checkpoint_status == "complete" else evidence
                    freshness = freshness if isinstance(freshness, dict) else {}
                    expected_current_marker_sha = (
                        _marker_tasks_sha_text(current_tasks_text, marker_task_ids)
                        if marker_task_values is not None
                        else None
                    )
                    feature_tasks_path = f"{feature_dir}/tasks.md"
                    checkpoint_tasks_bytes = (
                        _git_file_at_commit(
                            repo_root,
                            evidence.get("implementation_checkpoint_sha"),
                            feature_tasks_path,
                        )
                        if repo_root and isinstance(feature_dir, str)
                        else None
                    )
                    try:
                        checkpoint_tasks_text = checkpoint_tasks_bytes.decode("utf-8") if checkpoint_tasks_bytes else None
                    except UnicodeDecodeError:
                        checkpoint_tasks_text = None
                    expected_checkpoint_marker_sha = (
                        _marker_tasks_sha_text(checkpoint_tasks_text, marker_task_ids)
                        if checkpoint_tasks_text is not None and marker_task_values is not None
                        else None
                    )
                    checkpoint_tasks_sha = (
                        _sha256_bytes(checkpoint_tasks_bytes) if checkpoint_tasks_bytes is not None else None
                    )
                    checks = {
                        "marker_id": evidence.get("marker_id") == marker_id,
                        "task_ids": (
                            marker_task_values is not None
                            and evidence_task_values is not None
                            and set(evidence_task_values) == marker_task_ids
                        ),
                        "tasks_sha": evidence.get("tasks_sha") == checkpoint_tasks_sha,
                        "source_fingerprint_contract": freshness.get("source_fingerprint_contract") == "marker-task-lines.v2",
                        "source_fingerprint_status": freshness.get("source_fingerprint_status") == "current_marker_scope",
                        "tasks_sha_scope": freshness.get("tasks_sha_scope") == "checkpoint_time_whole_file",
                        "current_tasks_sha": freshness.get("current_tasks_sha") == current_tasks_sha,
                        "checkpoint_marker_tasks_sha": (
                            freshness.get("checkpoint_marker_tasks_sha") == expected_checkpoint_marker_sha
                        ),
                        "current_marker_tasks_sha": (
                            freshness.get("current_marker_tasks_sha") == expected_current_marker_sha
                        ),
                        "marker_scope_unchanged": (
                            expected_checkpoint_marker_sha is not None
                            and expected_checkpoint_marker_sha == expected_current_marker_sha
                        ),
                    }
                    checkpoint_source_fingerprint_errors.extend(
                        f"pr_marker_plan.markers[{index}] checkpoint {field}"
                        for field, passed in checks.items() if not passed
                    )
                matching_phases = [
                    (phase_name, result)
                    for phase_name, result in phases.items()
                    if isinstance(result, dict) and result.get("marker_id") == marker_id
                ]
                for phase_name, result in matching_phases:
                    phase_complete = result.get("status") == "completed"
                    checkpoint_complete = checkpoint_status == "complete"
                    if phase_complete != checkpoint_complete:
                        projection_status_errors.append(
                            f"marker {marker_id!r} checkpoint={checkpoint_status!r} "
                            f"does not match phase_results[{phase_name}].status={result.get('status')!r}"
                        )

            emission = raw_marker.get("emission_mapping")
            if strict_contract and isinstance(emission, dict):
                emission_status = emission.get("status")
                required_fields: tuple[str, ...] = ()
                if emission_status == "marker_split":
                    required_fields = ("packet_path",)
                elif emission_status == "emitted":
                    required_fields = ("packet_path", "pr_number", "pr_url")
                for required in required_fields:
                    value = emission.get(required)
                    if value is None or isinstance(value, str) and not value.strip():
                        emission_mapping_errors.append(
                            f"pr_marker_plan.markers[{index}].emission_mapping.{required}"
                        )
                packet_path = emission.get("packet_path")
                if packet_path is not None and (
                    not _is_normalized_repo_path(packet_path)
                    or repo_root and _repo_file(repo_root, packet_path) is None
                ):
                    emission_mapping_errors.append(
                        f"pr_marker_plan.markers[{index}].emission_mapping.packet_path is not a normalized repository-relative path"
                    )
                if emission_status != "emitted":
                    for field in ("pr_number", "pr_url"):
                        if field in emission:
                            emission_mapping_errors.append(
                                f"pr_marker_plan.markers[{index}].emission_mapping.{field} is only valid after emission"
                            )
                if emission_status in {"marker_split", "emitted", "hazard_collapsed"}:
                    if not isinstance(checkpoint, dict) or checkpoint.get("status") != "complete":
                        emission_mapping_errors.append(
                            f"pr_marker_plan.markers[{index}] emission requires a complete checkpoint"
                        )

        status_constraints = {
            "planned": ({"pending"}, {"pending"}),
            "checkpointing": ({"pending", "complete"}, {"pending"}),
            "emission_ready": ({"complete"}, {"pending", "marker_split"}),
            "emitting": ({"complete"}, {"pending", "marker_split", "emitted"}),
            "emitted": ({"complete"}, {"emitted"}),
            "collapsed": ({"complete"}, {"hazard_collapsed"}),
            "stale": ({"pending", "complete"}, {"pending", "marker_split", "emitted", "hazard_collapsed"}),
            "invalid": ({"pending", "complete"}, {"pending", "marker_split", "emitted", "hazard_collapsed"}),
        }
        if strict_contract and plan_status in status_constraints:
            allowed_checkpoints, allowed_emissions = status_constraints[plan_status]
            for index, raw_marker in enumerate(markers):
                checkpoint = raw_marker.get("implementation_checkpoint") if isinstance(raw_marker, dict) else None
                emission = raw_marker.get("emission_mapping") if isinstance(raw_marker, dict) else None
                checkpoint_status = checkpoint.get("status") if isinstance(checkpoint, dict) else None
                emission_status = emission.get("status") if isinstance(emission, dict) else None
                if checkpoint_status not in allowed_checkpoints:
                    marker_plan_status_errors.append(
                        f"pr_marker_plan.status {plan_status} rejects marker {index} checkpoint {checkpoint_status!r}"
                    )
                if emission_status not in allowed_emissions:
                    marker_plan_status_errors.append(
                        f"pr_marker_plan.status {plan_status} rejects marker {index} emission {emission_status!r}"
                    )
            if plan_status == "emitting":
                emission_statuses = {
                    raw_marker.get("emission_mapping", {}).get("status")
                    for raw_marker in markers
                    if isinstance(raw_marker, dict) and isinstance(raw_marker.get("emission_mapping"), dict)
                }
                if "emitted" not in emission_statuses or emission_statuses <= {"emitted"}:
                    marker_plan_status_errors.append(
                        "pr_marker_plan.status emitting requires both emitted and unfinished marker mappings"
                    )
    return {
        "completed_phase_pending_fields": completed_phase_pending_fields,
        "projection_status_errors": projection_status_errors,
        "checkpoint_evidence_errors": checkpoint_evidence_errors,
        "checkpoint_source_fingerprint_errors": checkpoint_source_fingerprint_errors,
        "checkpoint_file_errors": checkpoint_file_errors,
        "emission_mapping_errors": emission_mapping_errors,
        "marker_plan_status_errors": marker_plan_status_errors,
    }


def build_report(
    workflow: Path,
    state: Path,
    *,
    expected_base_commit: str | None = None,
    expected_head_commit: str | None = None,
) -> dict[str, Any]:
    state_data = load_state(state)
    workflow_text, workflow_authority_errors = _authorized_workflow_text(
        workflow, state, state_data, expected_head_commit,
    )
    plan_steps = extract_plan_steps(state_data)

    workflow_result = validate_workflow(workflow_text)
    workflow_checkpoint_result = validate_workflow_checkpoint_bindings(
        workflow_text, state_data,
    )
    workflow_checkpoint_result["workflow_checkpoint_errors"].extend(
        workflow_authority_errors
    )
    state_result = validate_state(plan_steps)
    projection_result = validate_projection_integrity(
        state_data,
        plan_steps,
        state,
        expected_head_commit=expected_head_commit,
    )
    manifest_result = validate_changed_file_manifest(
        state_data,
        state,
        expected_base_commit=expected_base_commit,
        expected_head_commit=expected_head_commit,
    )
    problems = {
        **workflow_result,
        **workflow_checkpoint_result,
        **state_result,
        **projection_result,
        **manifest_result,
    }
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
    parser.add_argument(
        "--expected-base-commit",
        help="live PR baseRefOid authority required when pr-marker-plan.v2 uses a changed-file manifest",
    )
    parser.add_argument(
        "--expected-head-commit",
        help="live PR headRefOid authority required when pr-marker-plan.v2 uses a changed-file manifest",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(
            args.workflow,
            args.state,
            expected_base_commit=args.expected_base_commit,
            expected_head_commit=args.expected_head_commit,
        )
    except ValidationError as exc:
        print(json.dumps({"status": "input_error", "code": exc.code, "message": str(exc)}, sort_keys=True))
        return 2

    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
