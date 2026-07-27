#!/usr/bin/env python3
"""Contracts for the single shipped canonical agent materializer.

The materializer lives in plugin source at
``speckit-pro/speckit_pro_runner/materializer.py`` and is the only
materialization contract in the repository (FR-006). It owns the exact rendered
destination bytes and the instruction/configuration digests, so these checks
exercise the shipped module directly rather than a harness copy.

The proof discipline these cases pin (FR-008):

* the content hash is SHA-256 over the destination file's exact UTF-8 bytes read
  back **from disk after write** — never from an in-memory render buffer;
* no normalization, re-serialization, newline translation, trailing-newline
  insertion, or key reordering may sit between the bytes and the digest, so six
  drift classes that parsed-field equivalence cannot see each change the hash;
* the destination path is verified **separately** and is absent from the digest
  preimage, so identical content at a different path hashes identically;
* equivalence between the installed-plugin branch and the materialized-byte
  branch is bounded to the keys the plugin loader honors, so a definition
  declaring ``hooks``, ``mcpServers``, or ``permissionMode`` cannot be proved by
  the materialization branch at all.

Every check is offline and writes only into a temporary directory.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LIB_DIR = TEST_ROOT / "lib"
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
for _path in (LIB_DIR, PLUGIN_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from test_result import run_counted  # noqa: E402

try:  # T029/T030 deliverable — absent until the shipped materializer lands.
    from speckit_pro_runner import materializer  # type: ignore[attr-defined]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    materializer = None  # type: ignore[assignment]


# The frontmatter keys a parsed-field comparison would treat as the definition.
# Anything outside this set is an "unknown key" such a comparison never sees.
HONORED_KEYS = ("name", "description", "model", "tools")

BASE_DEFINITION = (
    "---\n"
    "name: calibration-probe\n"
    "description: Runs a disposable préflight objective\n"
    "model: sonnet\n"
    "tools: Read, Grep\n"
    "---\n"
    "\n"
    "Run the bound objective and report the result.\n"
)


def top_level_pairs(frontmatter_text: str) -> list[tuple[str, str]]:
    """Top-level ``key: value`` pairs, ignoring comments and nested lines."""
    pairs: list[tuple[str, str]] = []
    for line in frontmatter_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        if line[:1].isspace() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        pairs.append((key.strip(), value.strip()))
    return pairs


def parsed_fields(source_text: str) -> dict[str, str]:
    """The lenient equivalence oracle FR-008 forbids as proof.

    It normalizes exactly what a parsed-field comparison normalizes away: key
    order (a dict is unordered), surrounding whitespace, comment lines, keys the
    loader does not honor, line endings (``splitlines``), and Unicode encoding
    form. The body is folded in the same way. Any drift this oracle calls equal
    while the byte hash calls different is a drift a parsed comparison would
    have missed.
    """
    frontmatter, body = source_text.replace("\r\n", "\n").split("---\n", 2)[1:3]
    fields = {
        key: unicodedata.normalize("NFC", value)
        for key, value in top_level_pairs(frontmatter)
        if key in HONORED_KEYS
    }
    fields["<body>"] = unicodedata.normalize("NFC", " ".join(body.split()))
    return fields


def drift_variants() -> dict[str, str]:
    """One source variant per drift class, each parsed-equivalent to the base."""
    return {
        "key_order": (
            "---\n"
            "description: Runs a disposable préflight objective\n"
            "name: calibration-probe\n"
            "tools: Read, Grep\n"
            "model: sonnet\n"
            "---\n"
            "\n"
            "Run the bound objective and report the result.\n"
        ),
        "whitespace": BASE_DEFINITION.replace("name: calibration-probe", "name:   calibration-probe  "),
        "comments": BASE_DEFINITION.replace("name:", "# pinned by the frozen role corpus\nname:", 1),
        "unknown_keys": BASE_DEFINITION.replace("model: sonnet", "model: sonnet\ncolor: blue", 1),
        "line_endings": BASE_DEFINITION.replace("\n", "\r\n"),
        "encoding": unicodedata.normalize("NFD", BASE_DEFINITION),
    }


def definition_with(key: str) -> str:
    """The base definition plus one key the plugin loader silently ignores."""
    return BASE_DEFINITION.replace("model: sonnet", f"model: sonnet\n{key}: inherit", 1)


class CanonicalMaterializerTests(unittest.TestCase):
    """One shipped materializer owns the destination bytes and their proof."""

    def setUp(self) -> None:
        if materializer is None:  # pragma: no cover - pre-implementation guard
            self.fail("speckit_pro_runner.materializer is not importable from plugin source")
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)
        self.addCleanup(self._temporary.cleanup)

    def materialize(self, source_text: str, name: str = "agent.md", **kwargs: object):
        destination = self.root / name
        options = {
            "loader_scope": materializer.LOADER_SCOPE_PROJECT,
            "proof_branch": materializer.PROOF_BRANCH_MATERIALIZED_BYTES,
        }
        options.update(kwargs)
        return materializer.materialize(source_text, destination=destination, **options)

    def test_the_recorded_hash_is_reproduced_from_the_bytes_on_disk(self) -> None:
        record = self.materialize(BASE_DEFINITION)

        self.assertEqual(record.proof.preimage_source, materializer.DESTINATION_FILE_BYTES)
        self.assertEqual(
            record.proof.content_hash,
            "sha256:" + hashlib.sha256(record.destination.read_bytes()).hexdigest(),
        )
        self.assertEqual(record.destination.read_bytes(), BASE_DEFINITION.encode("utf-8"))
        self.assertEqual(record.proof.byte_length, len(BASE_DEFINITION.encode("utf-8")))
        materializer.verify_content_hash_proof(record.proof, destination=record.destination)

    def test_a_tampered_destination_file_fails_reverification(self) -> None:
        record = self.materialize(BASE_DEFINITION)
        record.destination.write_bytes(BASE_DEFINITION.encode("utf-8") + b" ")

        with self.assertRaises(materializer.MaterializationError):
            materializer.verify_content_hash_proof(record.proof, destination=record.destination)

    def test_every_drift_class_parsed_equivalence_misses_changes_the_hash(self) -> None:
        base = self.materialize(BASE_DEFINITION, "base.md")

        for drift_class, variant in drift_variants().items():
            with self.subTest(msg=drift_class):
                record = self.materialize(variant, f"{drift_class}.md")
                self.assertEqual(
                    parsed_fields(variant),
                    parsed_fields(BASE_DEFINITION),
                    "the variant must be indistinguishable to parsed-field equivalence",
                )
                self.assertNotEqual(record.proof.content_hash, base.proof.content_hash)
                self.assertNotEqual(record.materialization_id, base.materialization_id)

    def test_a_hash_taken_from_the_render_buffer_is_rejected_as_proof(self) -> None:
        record = self.materialize(BASE_DEFINITION)
        buffer_proof = materializer.ContentHashProof(
            content_hash=record.proof.content_hash,
            preimage_source=materializer.RENDER_BUFFER,
            byte_length=record.proof.byte_length,
        )

        self.assertNotIn(materializer.RENDER_BUFFER, materializer.ACCEPTED_PREIMAGE_SOURCES)
        with self.assertRaises(materializer.MaterializationError):
            materializer.verify_content_hash_proof(buffer_proof, destination=record.destination)

    def test_identical_content_at_a_different_path_hashes_identically(self) -> None:
        here = self.materialize(BASE_DEFINITION, "here.md")
        nested = self.root / "scope" / "there.md"
        nested.parent.mkdir(parents=True)
        there = materializer.materialize(
            BASE_DEFINITION,
            destination=nested,
            loader_scope=materializer.LOADER_SCOPE_USER,
            proof_branch=materializer.PROOF_BRANCH_MATERIALIZED_BYTES,
        )

        self.assertNotEqual(here.destination, there.destination)
        self.assertEqual(here.proof.content_hash, there.proof.content_hash)
        self.assertEqual(here.materialization_id, there.materialization_id)

        materializer.verify_destination_path(here, expected=here.destination)
        with self.assertRaises(materializer.MaterializationError):
            materializer.verify_destination_path(here, expected=there.destination)

    def test_a_definition_declaring_a_loader_ignored_key_is_barred_from_the_materialization_branch(self) -> None:
        self.assertEqual(
            tuple(materializer.PLUGIN_IGNORED_KEYS),
            ("hooks", "mcpServers", "permissionMode"),
        )

        for key in materializer.PLUGIN_IGNORED_KEYS:
            with self.subTest(msg=key):
                source = definition_with(key)
                self.assertEqual(materializer.ignored_keys_declared(source), (key,))
                with self.assertRaises(materializer.MaterializationError):
                    self.materialize(source, f"{key}.md")

                served = self.materialize(
                    source,
                    f"{key}-installed.md",
                    loader_scope=materializer.LOADER_SCOPE_PLUGIN,
                    proof_branch=materializer.PROOF_BRANCH_INSTALLED_POLICY,
                )
                self.assertEqual(served.proof_branch, materializer.PROOF_BRANCH_INSTALLED_POLICY)

    def test_the_treatment_record_carries_the_served_branch_and_loader_scope(self) -> None:
        record = self.materialize(
            BASE_DEFINITION,
            loader_scope=materializer.LOADER_SCOPE_PLUGIN,
            proof_branch=materializer.PROOF_BRANCH_INSTALLED_POLICY,
        )
        fields = materializer.treatment_record_fields(record)

        self.assertEqual(fields["proof_branch"], materializer.PROOF_BRANCH_INSTALLED_POLICY)
        self.assertEqual(fields["loader_scope"], materializer.LOADER_SCOPE_PLUGIN)
        self.assertEqual(fields["equivalence_scope"], materializer.BOUNDED_EQUIVALENCE_SCOPE)
        self.assertIs(fields["equivalence_bounded"], True)
        self.assertEqual(fields["materialization_id"], record.materialization_id)
        self.assertNotIn("destination", fields)

    def test_the_instruction_and_configuration_digests_split_body_from_frontmatter(self) -> None:
        record = self.materialize(BASE_DEFINITION)
        frontmatter, body = materializer.split_definition(BASE_DEFINITION)

        self.assertEqual(
            record.instruction_hash,
            "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            record.configuration_hash,
            "sha256:" + hashlib.sha256(frontmatter.encode("utf-8")).hexdigest(),
        )
        self.assertNotEqual(record.instruction_hash, record.configuration_hash)
        self.assertIn("name: calibration-probe", frontmatter)
        self.assertNotIn("name: calibration-probe", body)

    def test_the_shipped_module_never_reaches_back_into_the_test_tree(self) -> None:
        source = (PLUGIN_ROOT / "speckit_pro_runner" / "materializer.py").read_text(encoding="utf-8")

        self.assertNotIn("tests/speckit-pro", source)
        self.assertNotIn("layer6-efficiency", source)

    def test_the_module_loads_by_path_without_a_registered_module_entry(self) -> None:
        """The plugin-shaped resolution proof loads the file by path alone.

        An installed plugin cache is imported that way — no package on
        ``sys.path``, no ``sys.modules`` entry. Anything in the module that
        resolves its own module namespace at import time (a ``dataclass`` under
        postponed annotations, for one) breaks only in this layout, so the shape
        is exercised here rather than trusted.
        """
        spec = importlib.util.spec_from_file_location(
            "materializer_plugin_shaped", PLUGIN_ROOT / "speckit_pro_runner" / "materializer.py"
        )
        module = importlib.util.module_from_spec(spec)
        self.assertNotIn(spec.name, sys.modules)
        spec.loader.exec_module(module)

        record = module.materialize(
            BASE_DEFINITION,
            destination=self.root / "path-loaded.md",
            loader_scope=module.LOADER_SCOPE_PLUGIN,
            proof_branch=module.PROOF_BRANCH_INSTALLED_POLICY,
        )
        module.verify_content_hash_proof(record.proof, destination=record.destination)
        self.assertEqual(
            record.proof.content_hash,
            "sha256:" + hashlib.sha256(BASE_DEFINITION.encode("utf-8")).hexdigest(),
        )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CanonicalMaterializerTests)
    raise SystemExit(run_counted(suite, label="test-canonical-agent-materializer"))
