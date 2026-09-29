"""Shared scan, classification, and response path for the v1.0 and v2.0 guards.

The v1.0 active-path guard and the v2.0 installed-runtime guard run the same
scan. A GuardPolicy carries every difference between them, so a fix to the
scan reaches both guards.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from ...envelope import diagnostic, response
from .common import (
    CONTAINER_PREFLIGHT_WORKFLOW,
    FORBIDDEN_CONTENT_PATTERNS,
    FORBIDDEN_PATTERNS,
    RawFinding,
    SourceFile,
    add_finding,
    bounded_findings,
    classified_counts,
    direct_dispatch_line,
    is_direct_python_gate_dispatch,
    is_hook_matcher_line,
    line_context,
    line_number_for_offset,
    normalize_path,
    workflow_context_for_line,
    workflow_run_contexts,
)


@dataclass(frozen=True)
class GuardPolicy:
    """Everything that differs between the v1.0 and v2.0 guards."""

    schema_version: str
    contract_id: str | None
    blocking_classification: str
    bound_findings: bool
    base_data: Callable[[Any, str, str], dict[str, Any]]
    active_role: Callable[[str], str]
    classify: Callable[[str, str, str, str, str], str]
    remediations: Mapping[str, str]
    default_remediation: str
    # (path) -> (pattern, reason) when the path is a prohibited script file.
    script_file: Callable[[str], tuple[str, str] | None]
    # True: a line pattern with no workflow context uses the line's context
    # window; False: it uses the bare line.
    line_context_window: bool
    # (path, line) -> True when the bare line is the context, overriding the rest.
    bare_line_context: Callable[[str, str], bool]
    blocked_code: str
    blocked_message: str
    blocked_summary: str
    blocked_actions: tuple[str, ...]


@dataclass(frozen=True)
class Hit:
    line: int | None
    category: str
    pattern: str
    reason: str
    context: str


def remediation(policy: GuardPolicy, classification: str) -> str:
    return policy.remediations.get(classification, policy.default_remediation)


def classify_hit(policy: GuardPolicy, path: str, source_kind: str, hit: Hit) -> RawFinding:
    classification = policy.classify(path, hit.category, hit.pattern, hit.context, source_kind)
    return RawFinding(
        path=path,
        line=hit.line,
        category=hit.category,
        pattern=hit.pattern[:120],
        reason=hit.reason,
        active_role=policy.active_role(path),
        classification=classification,
        remediation=remediation(policy, classification),
    )


def scan_with_policy(policy: GuardPolicy, sources: list[SourceFile]) -> list[RawFinding]:
    findings: list[RawFinding] = []
    seen: set[tuple[str, int | None, str, str]] = set()
    for source in sources:
        path = normalize_path(source.path)
        for hit in source_hits(policy, path, source.content):
            add_finding(findings, seen, classify_hit(policy, path, source.source_kind, hit))
    return findings


@dataclass(frozen=True)
class ScanText:
    path: str
    content: str
    lines: list[str]
    workflow_contexts: list[tuple[int, int, str]]

    @classmethod
    def of(cls, path: str, content: str) -> ScanText:
        contexts = workflow_run_contexts(content) if path.startswith(".github/workflows/") else []
        return cls(path, content, content.splitlines(), contexts)


def source_hits(policy: GuardPolicy, path: str, content: str) -> Iterator[Hit]:
    text = ScanText.of(path, content)
    script = policy.script_file(path)
    if script is not None:
        yield Hit(1, "script_file", script[0], script[1], content)
    if path.startswith(".github/workflows/") and is_direct_python_gate_dispatch(content):
        yield Hit(direct_dispatch_line(content), "bash", "run: python -m speckit_pro_runner", "workflow shell dispatches a Python gate", content)
    for category, pattern, reason in FORBIDDEN_CONTENT_PATTERNS:
        for match in pattern.finditer(content):
            number = line_number_for_offset(content, match.start())
            context = workflow_context_for_line(text.workflow_contexts, number) or line_context(text.lines, number)
            yield Hit(number, category, match.group(0), reason, content if path == CONTAINER_PREFLIGHT_WORKFLOW else context)
    yield from line_hits(policy, text)


def line_hits(policy: GuardPolicy, text: ScanText) -> Iterator[Hit]:
    for number, line in enumerate(text.lines, start=1):
        if skipped_line(text.path, line):
            continue
        for category, pattern, reason in FORBIDDEN_PATTERNS:
            match = pattern.search(line)
            if match is not None:
                yield Hit(number, category, match.group(0), reason, line_hit_context(policy, text, number))


def skipped_line(path: str, line: str) -> bool:
    stripped = line.strip()
    return not stripped or (stripped.startswith("#") and not path.endswith(".md")) or is_hook_matcher_line(path, line)


def line_hit_context(policy: GuardPolicy, text: ScanText, number: int) -> str:
    line = text.lines[number - 1]
    if policy.bare_line_context(text.path, line):
        return line
    if text.path == CONTAINER_PREFLIGHT_WORKFLOW:
        return text.content
    fallback = line_context(text.lines, number) if policy.line_context_window else line
    return workflow_context_for_line(text.workflow_contexts, number) or fallback


def policy_guard_response(policy: GuardPolicy, entry: Any, request: Any, findings: list[RawFinding]) -> dict[str, Any]:
    blocking = [finding for finding in findings if finding.classification == policy.blocking_classification]
    status = "expected_failure" if blocking else "ok"
    data = policy.base_data(entry, request.operation, status)
    data.update(response_fields(policy, status, blocking, findings))
    if not blocking:
        return response("ok", request_id=request.request_id, data=data)

    diag = diagnostic(
        policy.blocked_code,
        policy.blocked_message,
        details={
            "blocking_count": len(blocking),
            "categories": sorted({finding.category for finding in blocking}),
            "paths": sorted({finding.path for finding in blocking})[:20],
        },
        remediation_summary=policy.blocked_summary,
        remediation_actions=list(policy.blocked_actions),
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def response_fields(policy: GuardPolicy, status: str, blocking: list[RawFinding], findings: list[RawFinding]) -> dict[str, Any]:
    fields: dict[str, Any] = {"schema_version": policy.schema_version}
    if policy.contract_id is not None:
        fields["contract_id"] = policy.contract_id
    fields.update({"status": status, "blocking_count": len(blocking), "classified_counts": classified_counts(findings)})
    if not policy.bound_findings:
        fields["findings"] = [finding.as_record() for finding in findings]
        return fields
    returned = bounded_findings(findings)
    fields["findings"] = [finding.as_record() for finding in returned]
    fields["total_finding_count"] = len(findings)
    fields["truncated_finding_count"] = max(0, len(findings) - len(returned))
    return fields
