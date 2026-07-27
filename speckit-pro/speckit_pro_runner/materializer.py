"""The single canonical agent materialization contract.

This module owns the exact rendered destination bytes of an agent definition and
the instruction/configuration digests derived from them. It is the only
materializer in the repository: evaluation evidence and resolver behavior both
read it, and no parsed-only or evaluation-side copy exists.

**The proof is the bytes on disk.** ``materialize`` writes the source text
verbatim as UTF-8, reads the destination file back, and hashes what it read.
Nothing sits between the file and the digest — no normalization, no
re-serialization, no newline translation, no trailing-newline insertion, no key
reordering. A digest taken from the in-memory render buffer is not accepted as
proof, because a buffer cannot witness what actually reached the destination.

**The destination path is verified separately.** It is deliberately absent from
the digest preimage, so identical content at two different paths hashes
identically and path identity is a distinct check rather than a hidden term
inside the content hash.

**Equivalence between loader branches is bounded, not full.** A plugin-loaded
agent definition silently ignores the ``hooks``, ``mcpServers``, and
``permissionMode`` frontmatter keys and inherits the parent session's permission
mode, while the identical bytes loaded from project or user scope honor all
three. A content hash cannot see that difference by construction — the bytes are
identical and only the loader's interpretation differs. So a definition
declaring any of those three keys cannot be proved by the materialization
branch, and every record carries the branch that served the run, the loader
scope, and the fact that the equivalence claim is bounded to loader-honored
keys.

**No shipped caller yet, and that is deliberate.** Today the only importers are
repository-only: the Layer 6 evaluation runner and this module's unit tests. The
shipped consumers arrive in CAR-006 (route-policy manifest, frontmatter drift
gate, and session preflight), which is named for this module. It lives here now
rather than under ``tests/`` because relocating a payload-affecting module later
means running the generated-artifact regeneration twice, and because a second
materializer implementation is forbidden — CAR-003 design concept Q4 and research
R-001 record both decisions. A reviewer noticing "shipped code with no consumer"
has read the tree correctly; the answer is that the consumer is scheduled, not
missing.

Python 3.11+ standard library only.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import NamedTuple

__all__ = (
    "ACCEPTED_PREIMAGE_SOURCES",
    "BOUNDED_EQUIVALENCE_SCOPE",
    "ContentHashProof",
    "DESTINATION_FILE_BYTES",
    "FRONTMATTER_DELIMITER",
    "LOADER_SCOPES",
    "LOADER_SCOPE_PLUGIN",
    "LOADER_SCOPE_PROJECT",
    "LOADER_SCOPE_USER",
    "Materialization",
    "MaterializationError",
    "PLUGIN_IGNORED_KEYS",
    "PROOF_BRANCHES",
    "PROOF_BRANCH_INSTALLED_POLICY",
    "PROOF_BRANCH_MATERIALIZED_BYTES",
    "RENDER_BUFFER",
    "content_hash_from_destination",
    "declared_top_level_keys",
    "ignored_keys_declared",
    "materialize",
    "split_definition",
    "treatment_record_fields",
    "verify_content_hash_proof",
    "verify_destination_path",
)

FRONTMATTER_DELIMITER = "---"

# Where a definition was loaded from. The plugin scope is the installed-policy
# branch; project and user scope honor the keys the plugin loader ignores.
LOADER_SCOPE_PLUGIN = "plugin"
LOADER_SCOPE_PROJECT = "project"
LOADER_SCOPE_USER = "user"
LOADER_SCOPES = (LOADER_SCOPE_PLUGIN, LOADER_SCOPE_PROJECT, LOADER_SCOPE_USER)

# How a requested-route treatment record was proved.
PROOF_BRANCH_INSTALLED_POLICY = "installed_policy"
PROOF_BRANCH_MATERIALIZED_BYTES = "materialized_bytes"
PROOF_BRANCHES = (PROOF_BRANCH_INSTALLED_POLICY, PROOF_BRANCH_MATERIALIZED_BYTES)

# Frontmatter keys the plugin loader silently ignores. A definition declaring
# one of these applies different controls under different loader scopes from
# identical bytes, so the materialization branch cannot prove it.
PLUGIN_IGNORED_KEYS = ("hooks", "mcpServers", "permissionMode")

# The only preimage a content-hash proof may be computed from.
DESTINATION_FILE_BYTES = "destination_file_bytes"
RENDER_BUFFER = "render_buffer"
ACCEPTED_PREIMAGE_SOURCES = frozenset({DESTINATION_FILE_BYTES})

BOUNDED_EQUIVALENCE_SCOPE = "loader_honored_keys"


class MaterializationError(ValueError):
    """A materialization or its proof failed closed."""


class ContentHashProof(NamedTuple):
    """A content hash and the preimage it was taken from."""

    content_hash: str
    preimage_source: str
    byte_length: int


class Materialization(NamedTuple):
    """One materialized agent definition and its proof."""

    destination: Path
    proof: ContentHashProof
    instruction_hash: str
    configuration_hash: str
    materialization_id: str
    loader_scope: str
    proof_branch: str
    equivalence_scope: str = BOUNDED_EQUIVALENCE_SCOPE


def _digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def split_definition(source_text: str) -> tuple[str, str]:
    """Split a definition into its frontmatter block and its instruction body.

    The split decides only where the configuration ends and the instruction
    begins; it never rewrites either side, so both digests stay byte-faithful to
    the source.
    """
    if not source_text.startswith(FRONTMATTER_DELIMITER):
        raise MaterializationError("agent definition must open with a frontmatter delimiter")
    lines = source_text.splitlines(keepends=True)
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_DELIMITER:
            return "".join(lines[1:index]), "".join(lines[index + 1 :])
    raise MaterializationError("agent definition frontmatter is not terminated")


def declared_top_level_keys(frontmatter_text: str) -> tuple[str, ...]:
    """The top-level keys a frontmatter block declares, in declaration order."""
    keys: list[str] = []
    for line in frontmatter_text.splitlines():
        if not line or line[:1].isspace():
            continue
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("-"):
            continue
        key, separator, _ = line.partition(":")
        if separator and key.strip():
            keys.append(key.strip())
    return tuple(keys)


def ignored_keys_declared(source_text: str) -> tuple[str, ...]:
    """Which loader-ignored keys the definition declares, if any."""
    frontmatter, _ = split_definition(source_text)
    declared = set(declared_top_level_keys(frontmatter))
    return tuple(key for key in PLUGIN_IGNORED_KEYS if key in declared)


def content_hash_from_destination(destination: Path) -> ContentHashProof:
    """SHA-256 over the destination file's exact bytes, read back from disk."""
    raw = Path(destination).read_bytes()
    return ContentHashProof(
        content_hash=_digest(raw),
        preimage_source=DESTINATION_FILE_BYTES,
        byte_length=len(raw),
    )


def verify_content_hash_proof(proof: ContentHashProof, *, destination: Path) -> None:
    """Fail closed unless the proof still matches the bytes on disk."""
    if proof.preimage_source not in ACCEPTED_PREIMAGE_SOURCES:
        raise MaterializationError(
            f"content-hash proof preimage {proof.preimage_source!r} is not the destination file bytes"
        )
    observed = content_hash_from_destination(destination)
    if observed.content_hash != proof.content_hash or observed.byte_length != proof.byte_length:
        raise MaterializationError("destination bytes do not reproduce the recorded content hash")


def verify_destination_path(materialization: Materialization, *, expected: Path) -> None:
    """Verify the destination path separately from the content hash."""
    if Path(materialization.destination) != Path(expected):
        raise MaterializationError("materialized destination path does not match the expected path")


def materialize(
    source_text: str,
    *,
    destination: Path,
    loader_scope: str,
    proof_branch: str,
) -> Materialization:
    """Write a definition verbatim and prove it from the bytes it left on disk."""
    if loader_scope not in LOADER_SCOPES:
        raise MaterializationError(f"unknown loader scope {loader_scope!r}")
    if proof_branch not in PROOF_BRANCHES:
        raise MaterializationError(f"unknown proof branch {proof_branch!r}")

    frontmatter, body = split_definition(source_text)
    if proof_branch == PROOF_BRANCH_MATERIALIZED_BYTES:
        ignored = ignored_keys_declared(source_text)
        if ignored:
            raise MaterializationError(
                "the materialization branch cannot prove a definition declaring loader-ignored keys: "
                + ", ".join(ignored)
            )

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source_text.encode("utf-8"))

    proof = content_hash_from_destination(destination)
    instruction_hash = _digest(body.encode("utf-8"))
    configuration_hash = _digest(frontmatter.encode("utf-8"))
    return Materialization(
        destination=destination,
        proof=proof,
        instruction_hash=instruction_hash,
        configuration_hash=configuration_hash,
        # Path-free by construction: the destination is verified separately.
        materialization_id=_digest(
            "\n".join((proof.content_hash, instruction_hash, configuration_hash)).encode("utf-8")
        ),
        loader_scope=loader_scope,
        proof_branch=proof_branch,
    )


def treatment_record_fields(materialization: Materialization) -> dict[str, object]:
    """The materialization fields a treatment record carries.

    The destination path is excluded: it is operator-local and is verified
    separately by ``verify_destination_path``.
    """
    return {
        "materialization_id": materialization.materialization_id,
        "content_hash": materialization.proof.content_hash,
        "content_hash_preimage_source": materialization.proof.preimage_source,
        "instruction_hash": materialization.instruction_hash,
        "configuration_hash": materialization.configuration_hash,
        "proof_branch": materialization.proof_branch,
        "loader_scope": materialization.loader_scope,
        "equivalence_scope": materialization.equivalence_scope,
        "equivalence_bounded": True,
    }
