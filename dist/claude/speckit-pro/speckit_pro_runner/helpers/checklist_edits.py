"""Checklist check-and-propose (ADR 0018, decision P5): executors propose, the runner applies.

A checklist domain executor returns its gaps and proposed edits and writes neither
`spec.md` nor `plan.md`. This helper is the only writer of both during the phase.
`read_only` returns the digests of the two files, taken before the executors run.
`dry_run` and `apply` refuse when either digest has moved, which means an executor
wrote an artifact. Otherwise they apply the proposals one domain at a time in the
workflow's domain order, under one lock, so no two writes touch the files at once.
A domain whose edit does not match exactly once applies none of its edits and is
reported as a conflict; later domains still run. Every listed domain needs a proposal,
which is empty when it found no gaps, so a missing return is refused rather than read
as a clean domain. `dry_run` with no domains and no proposals only compares the digests,
which is how the orchestrator checks that a verify run wrote nothing.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from collections.abc import Callable
from contextlib import nullcontext
from functools import partial
from pathlib import Path
from typing import Any

from ..atomic_write import write_bytes_atomic
from ..envelope import diagnostic, response
from ..execution_control import confined_path, durable_json, exclusive_ledger, workflow_process_directory
from ..strict_input import SelectionError, require_fields, require_text
from ..trusted_io import trusted_bytes
from .execution_requests import Refusal, run_contained_helper

SCHEMA_VERSION = "checklist-edits/v1"
ARTIFACTS = ("spec.md", "plan.md")
MAX_TEXT = 20000


class ArtifactChanged(Exception):
    """An artifact differs from the baseline taken before the executors ran."""

    def __init__(self, changed: list[str]) -> None:
        super().__init__(f"{', '.join(changed)} changed since the baseline")
        self.changed = changed


@dataclass
class ApplyInterrupted(Exception):
    """A write failed after earlier domains reached disk; `applied` names them."""

    domain: str
    applied: list[str]


def checked_proposal(value: Any) -> tuple[str, list[str], list[dict[str, str]]]:
    """One domain's proposal as (domain, gap ids, edits); anything outside the contract raises."""
    item = require_fields(value, {"domain", "gaps", "edits"}, "proposal")
    if not isinstance(item["gaps"], list) or not isinstance(item["edits"], list):
        raise SelectionError("proposal: gaps and edits must be lists")
    gaps = []
    for raw in item["gaps"]:
        gap = require_fields(raw, {"id", "description"}, "gap")
        require_text(gap["description"], "gap description")
        gaps.append(require_text(gap["id"], "gap id"))
    if len(set(gaps)) != len(gaps):
        raise SelectionError("proposal: gap ids must be unique")
    edits = []
    for raw in item["edits"]:
        edit = require_fields(raw, {"gap", "file", "find", "replace"}, "edit")
        if edit["gap"] not in gaps:
            raise SelectionError("edit: gap must name a gap in this proposal")
        if edit["file"] not in ARTIFACTS:
            raise SelectionError(f"edit: file must be one of {list(ARTIFACTS)}")
        require_text(edit["find"], "find")
        if not isinstance(edit["replace"], str) or max(len(edit["find"]), len(edit["replace"])) > MAX_TEXT:
            raise SelectionError(f"edit: find and replace are text of at most {MAX_TEXT} characters")
        edits.append({key: edit[key] for key in ("gap", "file", "find", "replace")})
    return require_text(item["domain"], "domain"), gaps, edits


def checked_request(request: dict[str, Any]) -> tuple[list[str], dict[str, str], dict[str, tuple[list[str], list[dict[str, str]]]]]:
    """The ordered domains, the baseline digests and the proposals keyed by domain."""
    domains = request["domains"]
    if not isinstance(domains, list) or any(not isinstance(name, str) or not name.strip() for name in domains):
        raise SelectionError("domains must be a list of domain names")
    if len(set(domains)) != len(domains):
        raise SelectionError("domains must be unique")
    baseline = require_fields(request["baseline"], set(ARTIFACTS), "baseline")
    if not isinstance(request["proposals"], list):
        raise SelectionError("proposals must be a list")
    proposals: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    for raw in request["proposals"]:
        domain, gaps, edits = checked_proposal(raw)
        if domain not in domains or domain in proposals:
            raise SelectionError(f"proposal: {domain!r} is not a listed domain or has more than one proposal")
        proposals[domain] = (gaps, edits)
    missing = [name for name in domains if name not in proposals]
    if missing:
        raise SelectionError(f"every listed domain needs a proposal, empty when it found no gaps; missing {missing}")
    return domains, {name: require_text(baseline[name], "baseline digest") for name in ARTIFACTS}, proposals


def apply_domain(texts: dict[str, str], edits: list[dict[str, str]]) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Apply one domain's edits in order; a conflict discards all of them and returns the texts unchanged."""
    work = dict(texts)
    conflicts = []
    for edit in edits:
        count = work[edit["file"]].count(edit["find"])
        if count == 1:
            work[edit["file"]] = work[edit["file"]].replace(edit["find"], edit["replace"], 1)
        else:
            reason = "find text not found" if count == 0 else f"find text matches {count} times"
            conflicts.append({"gap": edit["gap"], "file": edit["file"], "reason": reason})
    return (texts if conflicts else work), conflicts


def read_artifacts(root: Path, feature: Path) -> dict[str, bytes]:
    contents = {}
    for name in ARTIFACTS:
        content = trusted_bytes(feature / name, root)
        if content is None:
            raise SelectionError(f"{name} must be an existing file in feature_dir")
        contents[name] = content
    return contents


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def write_changed(root: Path, feature: Path, before: dict[str, str], after: dict[str, str]) -> None:
    for name in ARTIFACTS:
        if after[name] != before[name]:
            write_bytes_atomic(feature / name, after[name].encode("utf-8"), trust_root=root)


def apply_proposals(texts: dict[str, str], domains: list[str], proposals: dict[str, tuple[list[str], list[dict[str, str]]]],
                    write: Callable[[dict[str, str], dict[str, str]], None] | None) -> list[dict[str, Any]]:
    """One row per proposed domain, in domain order; `write` puts each domain's result on disk before the next starts."""
    rows: list[dict[str, Any]] = []
    for domain in domains:
        gaps, edits = proposals[domain]
        updated, conflicts = apply_domain(texts, edits)
        if write is not None:
            try:
                write(texts, updated)
            except OSError as error:
                raise ApplyInterrupted(domain, [row["domain"] for row in rows if row["status"] == "applied"]) from error
        texts = updated
        rows.append({"domain": domain, "gaps": len(gaps), "status": "conflict" if conflicts else "applied",
                     "edits_applied": 0 if conflicts else len(edits), "conflicts": conflicts,
                     "unproposed_gaps": [gap for gap in gaps if all(edit["gap"] != gap for edit in edits)]})
    return rows


def checklist_edits(root: Path, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    """Snapshot (read_only), plan (dry_run) or apply (apply) one batch of domain proposals."""
    fields = {"workflow_file", "feature_dir"} | (set() if mode == "read_only" else {"domains", "baseline", "proposals"})
    request = require_fields({key: value for key, value in inputs.items() if key != "repo_root"}, fields, "inputs")
    workflow = require_text(request["workflow_file"], "workflow_file")
    if not confined_path(root, workflow).is_file():
        raise SelectionError("workflow_file must be an existing contained file")
    feature = confined_path(root, require_text(request["feature_dir"], "feature_dir"))
    if mode == "read_only":
        return {"baseline": {name: digest(content) for name, content in read_artifacts(root, feature).items()},
                "writes_state": False}
    domains, baseline, proposals = checked_request(request)
    link = workflow_process_directory(workflow).joinpath("checklist-edits", "applied.json").as_posix()
    record = confined_path(root, link)
    # The baseline is checked under the lock, so no writer can slip in between the check and the first write.
    with exclusive_ledger(record) if mode == "apply" else nullcontext():
        contents = read_artifacts(root, feature)
        changed = [name for name in ARTIFACTS if digest(contents[name]) != baseline[name]]
        if changed:
            raise ArtifactChanged(changed)
        texts = {name: content.decode("utf-8") for name, content in contents.items()}
        write = partial(write_changed, root, feature) if mode == "apply" else None
        rows = apply_proposals(texts, domains, proposals, write)
        if mode == "apply":
            durable_json(record, {"schema_version": SCHEMA_VERSION, "domains": rows})
    return {"order": [row["domain"] for row in rows if row["status"] == "applied"], "domains": rows, "link": link,
            "writes_state": mode == "apply"}


REFUSAL = Refusal(
    "invalid_checklist_edits_request",
    "Send the workflow file, the feature directory and, to apply, the domains, baseline and proposals.",
    ["Correct the named field or file.", "Take a fresh baseline with read_only, then rerun checklist-edits."],
)


def run_checklist_edits_helper(entry: Any, request: Any) -> dict[str, Any]:
    try:
        return run_contained_helper(entry, request, checklist_edits, REFUSAL)
    except ApplyInterrupted as error:
        refusal = diagnostic(
            "apply_interrupted",
            f"writing {error.domain!r} failed after {len(error.applied)} domain(s) were applied; spec.md and plan.md hold them.",
            remediation_summary="Restore spec.md and plan.md from version control before retrying.",
            remediation_actions=["Restore both files, then take a fresh baseline with read_only.",
                                 "Redispatch the domains; the retry would otherwise report an executor write."],
        )
        return response("expected_failure", request_id=request.request_id,
                        data={"applied": error.applied, "failed": error.domain}, diagnostics=[refusal])
    except ArtifactChanged as error:
        refusal = diagnostic(
            "artifact_changed_during_check",
            f"{error}; a checklist executor wrote a planning artifact, and nothing was applied.",
            remediation_summary="Executors propose edits and never write spec.md or plan.md.",
            remediation_actions=["Review the unexpected change in the named file.",
                                 "Take a fresh baseline with read_only and redispatch the domains."],
        )
        return response("expected_failure", request_id=request.request_id, data={"changed": error.changed}, diagnostics=[refusal])
