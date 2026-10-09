"""Descriptor-bound artifact page publication (ADR 0019).

The runner performs every artifact-directory operation itself. It never hands a
checked pathname to another actor, so no check can be separated from its use.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
import stat
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..atomic_write import (AtomicWriteInterrupted, install_checked, snapshot_write_target_fd,
                            write_target_matches_snapshot)
from ..envelope import diagnostic, response
from ..strict_input import require_text
from ..trusted_io import resolve_repo_root, trusted_bytes, trusted_open_directory
from . import artifact_selection

INPUTS = frozenset({"repo_root", "plan_file", "research_file", "design_concept_file", "entry_id", "content"})
SELECTION_INPUTS = ("repo_root", "plan_file", "research_file", "design_concept_file")
REGION = re.compile(r"<!-- FILL:([a-z0-9-]+):START -->(.*?)<!-- FILL:\1:END -->", re.DOTALL)
MARKER = re.compile(r"<!-- FILL:([a-z0-9-]+):(START|END) -->")
BANNERS = ('class="sample-notice"', 'class="notice"', 'class="note"')
DIRECTORY = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


class PublicationRefused(OSError):
    """The page was not published, or was withdrawn, because its object binding broke."""

    def __init__(self, message: str, *, retained_page: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.retained_page = retained_page


def page_content(inputs: dict[str, Any], entry_id: str) -> bytes:
    """Validate the exact bytes that will be published, not a file another actor wrote."""
    content = require_text(inputs.get("content"), "content")
    template_bytes = trusted_bytes(artifact_selection.GALLERY / "templates" / f"{entry_id}.html",
                                   artifact_selection.GALLERY)
    if template_bytes is None:
        raise ValueError("the shipped template is unreadable")
    template = template_bytes.decode("utf-8")
    if MARKER.findall(content) != MARKER.findall(template):
        raise ValueError("content must keep every template FILL marker exactly once and in order")
    expected = REGION.findall(template)
    regions = REGION.findall(content)
    if [name for name, _ in regions] != [name for name, _ in expected]:
        raise ValueError("content must fill exactly the template's declared slots")
    if any(filled == sample for (_, filled), (_, sample) in zip(regions, expected, strict=True)):
        raise ValueError("content leaves a template slot unfilled")
    if any(banner in content for banner in BANNERS):
        raise ValueError("content still carries a sample banner")
    return content.encode("utf-8")


def identity(entry: os.stat_result) -> tuple[int, int]:
    return entry.st_dev, entry.st_ino


def open_artifacts(root: Path, feature: Path, *, create: bool) -> int | None:
    """Walk from the repository root without following any link; None when unbound."""
    parent = trusted_open_directory(root / feature, root)
    if parent is None:
        return None
    try:
        if create:
            try:
                os.mkdir("artifacts", 0o777, dir_fd=parent)
            except FileExistsError:
                # Existing entries still undergo the no-follow directory open below.
                pass
        return os.open("artifacts", DIRECTORY, dir_fd=parent)
    except OSError:
        return None
    finally:
        os.close(parent)


def still_bound(directory: int, root: Path, feature: Path) -> bool:
    """The held directory must still be the one its repository path names."""
    current = open_artifacts(root, feature, create=False)
    if current is None:
        return False
    try:
        return identity(os.fstat(current)) == identity(os.fstat(directory))
    finally:
        os.close(current)


def owned_entry(directory: int, name: str, owned: os.stat_result, *, single_link: bool = True) -> bool:
    try:
        entry = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return (stat.S_ISREG(entry.st_mode) and identity(entry) == identity(owned)
            and (not single_link or entry.st_nlink == 1))


def withdraw(directory: int, name: str, owned: os.stat_result) -> None:
    """Remove only the object this run created; a substituted entry is left alone."""
    try:
        entry = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return
    if identity(entry) == identity(owned):
        os.unlink(name, dir_fd=directory)


def read_back(directory: int, name: str, owned: os.stat_result, content: bytes) -> None:
    fd = os.open(name, os.O_RDONLY | NOFOLLOW | getattr(os, "O_NONBLOCK", 0), dir_fd=directory)
    try:
        entry = os.fstat(fd)
        if not stat.S_ISREG(entry.st_mode) or identity(entry) != identity(owned) or entry.st_nlink != 1:
            raise PublicationRefused("the published page is not the object this run wrote")
        chunks = []
        while chunk := os.read(fd, 1024 * 1024):
            chunks.append(chunk)
        if b"".join(chunks) != content:
            raise PublicationRefused("the published page does not hold the bytes this run wrote")
    finally:
        os.close(fd)


def write_page(fd: int, content: bytes) -> None:
    """Finish the temporary page before it can displace an existing page."""
    view = memoryview(content)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise PublicationRefused("the temporary page write made no progress")
        view = view[written:]
    os.fsync(fd)


def restore_page(directory: int, temporary: str, name: str, previous: dict[str, Any], owned: os.stat_result) -> None:
    """Restore the displaced entry through the same held directory, without following links."""
    if not write_target_matches_snapshot(snapshot_write_target_fd(directory, temporary), previous):
        raise PublicationRefused("the displaced page changed; restoration was refused")
    current = snapshot_write_target_fd(directory, name)
    if current["identity"] is None or current["identity"][:2] != identity(owned):
        raise PublicationRefused(f"the final page changed; the previous page is kept as {temporary}")
    install_checked(directory, temporary, name, current)
    if not write_target_matches_snapshot(snapshot_write_target_fd(directory, name), previous):
        raise PublicationRefused("the previous page could not be confirmed after restoration")
    withdraw(directory, temporary, owned)


@dataclass
class PagePublication:
    """The entries owned or retained by one publication through a held directory."""

    directory: int
    temporary: str
    name: str
    previous: dict[str, Any]
    owned: os.stat_result | None = None
    installed: bool = False

    def recover(self, error: BaseException) -> None:
        if isinstance(error, AtomicWriteInterrupted):
            # The shared installer keeps a competing entry when its own rollback fails.
            return
        if self.owned is None:
            return
        if not (self.installed and self.previous["exists"]):
            withdraw(self.directory, self.name if self.installed else self.temporary, self.owned)
            return
        if not owned_entry(self.directory, self.name, self.owned, single_link=False):
            raise PublicationRefused(f"the final page changed; the previous page is kept as {self.temporary}") from error
        restore_page(self.directory, self.temporary, self.name, self.previous, self.owned)


def retained_receipt(state: PagePublication, root: Path, feature: Path) -> dict[str, Any] | None:
    """A retained-page receipt requires fresh identity, bytes, and canonical-directory evidence."""
    try:
        if not state.previous["exists"] or not still_bound(state.directory, root, feature):
            return None
        current = snapshot_write_target_fd(state.directory, state.name)
        if write_target_matches_snapshot(current, state.previous):
            return {"sha256": current["digest"], "bytes": len(current["content"])}
    except OSError:
        return None  # Unreadable evidence cannot certify that a previous page survived.
    return None


def publish(root: Path, feature: Path, name: str, content: bytes) -> None:
    """Retain the displaced page until publication and verification have finished."""
    directory = open_artifacts(root, feature, create=True)
    if directory is None:
        raise PublicationRefused("the artifact directory cannot be opened without following links")
    try:
        temporary = f".artifact-author-{Path(name).stem}.{secrets.token_hex(8)}.tmp"
        state = PagePublication(directory, temporary, name, snapshot_write_target_fd(directory, name))
        try:
            with ExitStack() as stack:
                fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | NOFOLLOW, 0o644, dir_fd=directory)
                stack.callback(os.close, fd)
                owned = state.owned = os.fstat(fd)
                write_page(fd, content)
                if not owned_entry(directory, temporary, owned):
                    raise PublicationRefused("the temporary page is not the object this run created")
                install_checked(directory, temporary, name, state.previous)
                state.installed = True
                if not state.previous["exists"]:
                    os.unlink(temporary, dir_fd=directory)
                read_back(directory, name, owned, content)
                if not still_bound(directory, root, feature):
                    raise PublicationRefused("the artifact directory moved during publication")
            if state.previous["exists"]:
                os.unlink(temporary, dir_fd=directory)
        except BaseException as error:
            state.recover(error)
            if isinstance(error, (OSError, NotImplementedError)):
                raise PublicationRefused(str(error), retained_page=retained_receipt(state, root, feature)) from error
            raise
    finally:
        os.close(directory)


def run_artifact_publication_helper(entry: Any, request: Any) -> dict[str, Any]:
    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    inputs = request.inputs
    try:
        if set(inputs) - INPUTS:
            raise ValueError("publish-artifact-page received unknown inputs")
        entry_id = require_text(inputs.get("entry_id"), "entry_id")
        selection = artifact_selection.select_artifact_pages(
            {field: inputs[field] for field in SELECTION_INPUTS if field in inputs}, root)
        if entry_id not in selection["selected_pages"]:
            raise ValueError("entry_id is not a page the runner selected for these planning inputs")
        content = page_content(inputs, entry_id)
    except artifact_selection.INPUT_ERRORS as error:
        return response("input_error", request_id=request.request_id, diagnostics=[diagnostic(
            "artifact_publication_invalid", str(error),
            remediation_summary="Report this page as a gap; the pull request still opens.",
            remediation_actions=["Correct the rendered page or the planning inputs.", "Retry publication."],
        )])
    data: dict[str, Any] = {"helper_id": entry.helper_id, "operation": entry.operation, "mode": request.mode,
                            "writes_state": False, "entry_id": entry_id,
                            "output_path": selection["output_paths"][entry_id],
                            "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
    if request.mode == "apply":
        try:
            publish(root, Path(inputs["plan_file"]).parent, f"{entry_id}.html", content)
        except (OSError, NotImplementedError) as error:  # no dir_fd support refuses rather than falls back
            if isinstance(error, PublicationRefused) and error.retained_page is not None:
                data["retained_page"] = error.retained_page
            return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diagnostic(
                "artifact_publication_refused", f"the page was not published: {error}",
                remediation_summary="Report this page as a gap; the pull request still opens.",
                remediation_actions=["Leave the artifact directory alone.", "Report the diagnostic in the gap."],
            )])
        data["writes_state"] = True
    return response("ok", request_id=request.request_id, data=data)
