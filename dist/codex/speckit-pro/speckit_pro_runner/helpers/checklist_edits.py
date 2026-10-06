"""Checklist check-and-propose (ADR 0018, decision P5): executors propose, the runner applies.

A checklist domain executor returns its gaps and proposed edits and writes neither
`spec.md` nor `plan.md`. This helper is the only writer of both during the phase.
`read_only` returns the digests of the two files, taken before the executors run.
`dry_run` and `apply` refuse when either digest has moved, which means an executor
wrote an artifact. Otherwise they apply the proposals one domain at a time in the
workflow's domain order, under one lock on the feature directory, so no two writes
touch the files at once, whichever workflow file names the feature. Each write
replaces its file only while the directory and the file are still the ones this run
read or last wrote, and swaps it in so a change made after that check is put back,
never overwritten. After acting, a fresh walk from the repository root confirms the
canonical paths hold what this run wrote; only then is the result `ok`.
A domain whose edit does not match exactly once applies none of its edits and is
reported as a conflict; later domains still run. Every listed domain needs a proposal,
which is empty when it found no gaps, so a missing return is refused rather than read
as a clean domain. `dry_run` with no domains and no proposals only compares the digests,
which is how the orchestrator checks that a verify run wrote nothing. Once a write
has started, any failure reports what reached disk instead of a refusal.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Any

from ..atomic_write import (AtomicSwapUnavailable, WritePreconditionChanged, file_identity, open_safe_parent_fd, snapshot_write_target_fd,
                            write_bytes_atomic, write_file_atomic, write_target_matches_snapshot)
from ..canonical_json import canonical_bytes
from ..envelope import diagnostic, response
from ..execution_control import confined_path, ignore_owned_directory, workflow_process_directory
from ..strict_input import SelectionError, has_hidden_characters, require_fields, require_text
from ..sweep_isolation import secret_matches
from .execution_requests import Refusal, run_contained_helper

SCHEMA_VERSION = "checklist-edits/v1"
ARTIFACTS = ("spec.md", "plan.md")
MAX_TEXT = 20000
# Markdown keeps its tabs and line breaks; every other control, format or separator character is refused.
EDIT_TEXT_KEEPS = "\t\n\r"


class CanonicalMismatch(ValueError):
    """After acting, a canonical path no longer holds what this run wrote there."""


class SwapUnavailable(Exception):
    """The first write found no atomic swap on this filesystem; nothing was written."""

    def __init__(self, artifact: str) -> None:
        super().__init__(f"this filesystem cannot swap {artifact} atomically")
        self.artifact = artifact


class ArtifactChanged(Exception):
    """An artifact differs from the baseline taken before the executors ran."""

    def __init__(self, changed: list[str]) -> None:
        super().__init__(f"{', '.join(changed)} changed since the baseline")
        self.changed = changed


@dataclass
class Progress:
    """What this apply has put on disk, so a failure after a write reports the truth."""

    applied: list[str] = field(default_factory=list)
    step: str = ""
    partial: list[str] = field(default_factory=list)
    record: dict[str, Any] | None = None
    record_published: bool = False
    moved: list[str] = field(default_factory=list)

    @property
    def started(self) -> bool:
        return bool(self.step)


@dataclass
class ApplyInterrupted(Exception):
    """A step failed after the apply began writing; the fields say what is on disk."""

    progress: Progress
    record_written: bool | None
    reason: str


def checked_text(value: Any, label: str, *, keep: str = "") -> str:
    """Bounded text that hides nothing from a reader: no control, format or separator character outside `keep`."""
    if not isinstance(value, str) or len(value) > MAX_TEXT:
        raise SelectionError(f"{label} must be text of at most {MAX_TEXT} characters")
    if has_hidden_characters(value, keep=keep):
        raise SelectionError(f"{label} must not contain control, format or line separator characters")
    return value


def checked_proposal(value: Any) -> tuple[str, list[str], list[dict[str, str]]]:
    """One domain's proposal as (domain, gap ids, edits); anything outside the contract raises."""
    item = require_fields(value, {"domain", "gaps", "edits"}, "proposal")
    if not isinstance(item["gaps"], list) or not isinstance(item["edits"], list):
        raise SelectionError("proposal: gaps and edits must be lists")
    gaps = []
    for raw in item["gaps"]:
        gap = require_fields(raw, {"id", "description"}, "gap")
        require_text(gap["description"], "gap description")
        gaps.append(checked_text(require_text(gap["id"], "gap id"), "gap id"))
    if len(set(gaps)) != len(gaps):
        raise SelectionError("proposal: gap ids must be unique")
    edits = []
    for raw in item["edits"]:
        edit = require_fields(raw, {"gap", "file", "find", "replace"}, "edit")
        if edit["gap"] not in gaps:
            raise SelectionError("edit: gap must name a gap in this proposal")
        if edit["file"] not in ARTIFACTS:
            raise SelectionError(f"edit: file must be one of {list(ARTIFACTS)}")
        checked_text(require_text(edit["find"], "find"), "edit find", keep=EDIT_TEXT_KEEPS)
        if secret_matches(checked_text(edit["replace"], "edit replace", keep=EDIT_TEXT_KEEPS)):
            raise SelectionError("edit replace looks like a credential; planning artifacts never store one")
        edits.append({key: edit[key] for key in ("gap", "file", "find", "replace")})
    return checked_text(require_text(item["domain"], "domain"), "domain"), gaps, edits


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
            before = work[edit["file"]]
            work[edit["file"]] = before.replace(edit["find"], edit["replace"], 1)
            # Check the lines as written, not just the replace text: edits can complete a credential together.
            if any(secret_matches(line) for line in set(work[edit["file"]].splitlines()) - set(before.splitlines())):
                conflicts.append({"gap": edit["gap"], "file": edit["file"], "reason": "edits would write credential-shaped text"})
        else:
            reason = "find text not found" if count == 0 else f"find text matches {count} times"
            conflicts.append({"gap": edit["gap"], "file": edit["file"], "reason": reason})
    return (texts if conflicts else work), conflicts


@contextmanager
def held_feature(root: Path, feature: Path, *, exclusive: bool) -> Iterator[int]:
    """The feature directory's descriptor, locked when `exclusive`, so every path that names it shares one lock."""
    opened = open_safe_parent_fd(feature / ARTIFACTS[0], root, create=False)
    if opened is None:
        raise SelectionError("feature_dir must be an existing contained directory")
    directory = opened[0]
    try:
        if exclusive:
            try:
                import fcntl  # POSIX only; importing it at module level would break the registry elsewhere.
            except ImportError as error:
                raise SelectionError("checklist-edits needs POSIX file locks to apply or check proposals") from error
            try:
                fcntl.flock(directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise SelectionError("another checklist-edits run holds this feature; retry after it finishes") from error
        yield directory
    finally:
        os.close(directory)


def read_artifacts(directory: int) -> dict[str, dict[str, Any]]:
    """Each artifact's snapshot, read without following links: content, digest, mode and file identity."""
    snapshots = {}
    for name in ARTIFACTS:
        snapshot = snapshot_write_target_fd(directory, name)
        if not snapshot["exists"]:
            raise SelectionError(f"{name} must be an existing file in feature_dir")
        snapshots[name] = snapshot
    return snapshots


def changed_since(snapshots: dict[str, dict[str, Any]], baseline: dict[str, str]) -> list[str]:
    return [name for name in ARTIFACTS if snapshots[name]["digest"] != baseline[name]]


def write_changed(root: Path, feature: Path, expected: dict[str, Any], progress: Progress,
                  before: dict[str, str], after: dict[str, str]) -> None:
    """Write each changed artifact only while it and its directory are still what this run last saw."""
    for name in ARTIFACTS:
        if after[name] == before[name]:
            continue
        try:
            written = write_bytes_atomic(feature / name, after[name].encode("utf-8"), trust_root=root,
                                         expected_snapshot={**expected[name], "parent": expected["directory"]})
        except AtomicSwapUnavailable as error:
            # A platform limit, not a competing writer; after a write it is an interruption like any other.
            if not (progress.applied or progress.partial):
                raise SwapUnavailable(name) from error
            raise
        except WritePreconditionChanged as error:
            if not (progress.applied or progress.partial):
                raise ArtifactChanged([name]) from error
            raise
        expected[name] = {"exists": True, "digest": written["digest"], "mode": written["mode"], "identity": written["identity"]}
        progress.partial.append(name)


def apply_proposals(texts: dict[str, str], domains: list[str], proposals: dict[str, tuple[list[str], list[dict[str, str]]]],
                    write: Callable[[dict[str, str], dict[str, str]], None] | None, progress: Progress) -> list[dict[str, Any]]:
    """One row per proposed domain, in domain order; `write` puts each domain's result on disk before the next starts."""
    rows: list[dict[str, Any]] = []
    for domain in domains:
        gaps, edits = proposals[domain]
        updated, conflicts = apply_domain(texts, edits)
        if write is not None:
            progress.step, progress.partial = domain, []
            write(texts, updated)
            if not conflicts:
                progress.applied.append(domain)
            progress.partial = []
        texts = updated
        rows.append({"domain": domain, "gaps": len(gaps), "status": "conflict" if conflicts else "applied",
                     "edits_applied": 0 if conflicts else len(edits), "conflicts": conflicts,
                     "unproposed_gaps": [gap for gap in gaps if all(edit["gap"] != gap for edit in edits)]})
    return rows


def entry_state(root: Path, path: Path) -> tuple[tuple[int, int], dict[str, Any]] | None:
    """The identity of `path`'s directory and the entry's snapshot, reached by a fresh no-follow walk from `root`."""
    opened = open_safe_parent_fd(path, root, create=False)
    if opened is None:
        return None
    with ExitStack() as cleanup:
        cleanup.callback(os.close, opened[0])
        return file_identity(os.fstat(opened[0])), snapshot_write_target_fd(opened[0], opened[1])


def canonical_mismatches(root: Path, expected: dict[str, tuple[Path, tuple[int, int], dict[str, Any]]]) -> list[str]:
    """The labels whose canonical path no longer holds the expected entry, in the expected directory."""
    moved = []
    for label, (path, directory, snapshot) in expected.items():
        try:
            state = entry_state(root, path)
        except OSError:
            state = None
        if state is None or state[0] != directory or not write_target_matches_snapshot(state[1], snapshot):
            moved.append(label)
    return moved


def record_on_disk(root: Path, record: Path, value: dict[str, Any] | None) -> bool | None:
    """Whether the intended record is canonical; an unreadable entry is unknown, not absent."""
    if value is None:
        return False
    try:
        state = entry_state(root, record)
    except (OSError, ValueError):
        return None
    if state is None or not state[1]["exists"]:
        return False
    try:
        return json.loads(state[1]["content"]) == value
    except ValueError:
        return False


def checklist_edits(root: Path, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    """Snapshot (read_only), plan (dry_run) or apply (apply) one batch of domain proposals."""
    fields = {"workflow_file", "feature_dir"} | (set() if mode == "read_only" else {"domains", "baseline", "proposals"})
    request = require_fields({key: value for key, value in inputs.items() if key != "repo_root"}, fields, "inputs")
    workflow = require_text(request["workflow_file"], "workflow_file")
    if not confined_path(root, workflow).is_file():
        raise SelectionError("workflow_file must be an existing contained file")
    feature = confined_path(root, require_text(request["feature_dir"], "feature_dir"))
    if mode == "read_only":
        with held_feature(root, feature, exclusive=False) as directory:
            return {"baseline": {name: snapshot["digest"] for name, snapshot in read_artifacts(directory).items()},
                    "writes_state": False}
    domains, baseline, proposals = checked_request(request)
    link = workflow_process_directory(workflow).joinpath("checklist-edits", "applied.json").as_posix()
    record = confined_path(root, link)
    progress = Progress()
    try:
        rows = locked_apply(root, feature, record, mode, (domains, baseline, proposals), progress)
    except (OSError, ValueError) as error:
        if not progress.started:
            raise
        written = progress.record is not None and record_on_disk(root, record, progress.record)
        raise ApplyInterrupted(progress, written, str(error)) from error
    return {"order": [row["domain"] for row in rows if row["status"] == "applied"], "domains": rows, "link": link,
            "writes_state": mode == "apply"}


def confirm(root: Path, expected: dict[str, tuple[Path, tuple[int, int], dict[str, Any]]], progress: Progress) -> None:
    """Raise unless every canonical path still holds what this run wrote or read there."""
    progress.moved = canonical_mismatches(root, expected)
    if progress.moved:
        raise CanonicalMismatch(f"could not confirm the canonical path holds what this run wrote: {', '.join(progress.moved)}")


def locked_apply(root: Path, feature: Path, record: Path, mode: str,
                 checked: tuple[list[str], dict[str, str], dict[str, tuple[list[str], list[dict[str, str]]]]],
                 progress: Progress) -> list[dict[str, Any]]:
    """Under the feature lock: check the baseline, apply each domain, publish the record, then confirm the canonical tree holds them."""
    domains, baseline, proposals = checked
    if mode == "apply":
        ignore_owned_directory(record.parent)  # a broken record directory refuses before any write
    with held_feature(root, feature, exclusive=True) as directory:
        snapshots = read_artifacts(directory)
        changed = changed_since(snapshots, baseline)
        if changed:
            raise ArtifactChanged(changed)
        texts = {name: snapshot["content"].decode("utf-8") for name, snapshot in snapshots.items()}
        expected: dict[str, Any] = {name: {key: snapshots[name][key] for key in ("exists", "digest", "mode", "identity")}
                                    for name in ARTIFACTS}
        expected["directory"] = file_identity(os.fstat(directory))
        record_before = entry_state(root, record) if mode == "apply" else None
        if mode == "apply" and record_before is None:
            raise SelectionError("the application record directory must exist and stay link-free")
        write = partial(write_changed, root, feature, expected, progress) if mode == "apply" else None
        rows = apply_proposals(texts, domains, proposals, write, progress)
        # Verify after acting: a check before a write can always be raced, the canonical tree afterwards cannot lie.
        artifacts = {name: (feature / name, expected["directory"], expected[name]) for name in ARTIFACTS}
        if mode == "dry_run":
            changed = canonical_mismatches(root, artifacts)
            if changed:
                raise ArtifactChanged(changed)
            return rows
        progress.step = "verification"
        confirm(root, artifacts, progress)
        if record_before is None:  # refused above; this narrows the type
            raise CanonicalMismatch("the application record directory was not captured")
        progress.step, progress.record = "application record", {"schema_version": SCHEMA_VERSION, "domains": rows}
        published = write_file_atomic(record, canonical_bytes(progress.record).decode("utf-8"), trust_root=root,
                                      expected_snapshot={**record_before[1], "parent": record_before[0]})
        progress.record_published = True
        progress.step = "verification"
        confirm(root, {**artifacts, record.name: (record, record_before[0], {"exists": True, **published})}, progress)
        progress.step = "lock release"
    return rows


REFUSAL = Refusal(
    "invalid_checklist_edits_request",
    "Send the workflow file, the feature directory and, to apply, the domains, baseline and proposals.",
    ["Correct the named field or file.", "Take a fresh baseline with read_only, then rerun checklist-edits."],
)


def run_checklist_edits_helper(entry: Any, request: Any) -> dict[str, Any]:
    try:
        return run_contained_helper(entry, request, checklist_edits, REFUSAL)
    except ApplyInterrupted as error:
        progress = error.progress
        partial_note = f" and {', '.join(progress.partial)} of {progress.step!r}" if progress.partial else ""
        record_note = {True: "present", False: "absent or different", None: "state unknown"}[error.record_written]
        if progress.record_published:
            record_note += " (publication completed)"
        refusal = diagnostic(
            "apply_interrupted",
            f"{progress.step!r} failed ({error.reason}) after the apply began writing; on disk: "
            f"{len(progress.applied)} applied domain(s){partial_note}; application record "
            f"{record_note}.",
            remediation_summary="Restore spec.md and plan.md from version control before retrying.",
            remediation_actions=["Restore both files, then take a fresh baseline with read_only.",
                                 "Redispatch the domains; the retry would otherwise report an executor write."],
        )
        return response("expected_failure", request_id=request.request_id,
                        data={"applied": progress.applied, "failed": progress.step, "partial": progress.partial,
                              "moved": progress.moved, "record_written": error.record_written}, diagnostics=[refusal])
    except SwapUnavailable as error:
        refusal = diagnostic(
            "atomic_swap_unavailable",
            f"{error}, so checklist-edits cannot replace it without risking a lost competing change; nothing was applied.",
            remediation_summary="Apply from a local filesystem with atomic rename swaps; retrying on this one fails the same way.",
            remediation_actions=["Move the checkout to a local APFS, ext4, XFS, Btrfs or tmpfs volume, not exFAT, SMB, NFS or FUSE.",
                                 "Take a fresh baseline with read_only there and apply the same proposals."],
        )
        return response("expected_failure", request_id=request.request_id,
                        data={"applied": [], "artifact": error.artifact}, diagnostics=[refusal])
    except ArtifactChanged as error:
        refusal = diagnostic(
            "artifact_changed_during_check",
            f"{error}; another writer (an executor or a second run) changed a planning artifact, and nothing was applied.",
            remediation_summary="Executors propose edits and never write spec.md or plan.md.",
            remediation_actions=["Review the unexpected change in the named file.",
                                 "Take a fresh baseline with read_only and redispatch the domains."],
        )
        return response("expected_failure", request_id=request.request_id, data={"changed": error.changed}, diagnostics=[refusal])
