#!/usr/bin/env python3
"""Small source-contract checks for the standalone artifact gallery."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GALLERY = REPO_ROOT / "speckit-pro" / "artifact-gallery"
TEMPLATES = GALLERY / "templates"
ORACLE = Path(__file__).with_name("fixtures") / "artifact-gallery" / "catalog.json"
LIB = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from test_result import run_counted  # noqa: E402


POLICY = (
    "default-src 'none'; base-uri 'none'; form-action 'none'; object-src 'none'; "
    "frame-src 'none'; connect-src 'none'; worker-src 'none'; script-src 'unsafe-inline'; "
    "style-src 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src data: https://fonts.gstatic.com; img-src data:"
)
HEAD_MARKERS = ("<!-- GALLERY-HEAD:START -->", "<!-- GALLERY-HEAD:END -->")
BRAND_MARKERS = ("/* BRAND-KIT:START */", "/* BRAND-KIT:END */")
PLANNED = {"uat-walkthrough", "architecture-viewer"}
def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def region(value: str, markers: tuple[str, str]) -> str:
    start, end = markers
    if value.count(start) != 1 or value.count(end) != 1:
        raise AssertionError(f"expected one {start} region")
    begin = value.index(start)
    finish = value.index(end, begin) + len(end)
    return value[begin:finish]


def catalog() -> list[tuple[object, ...]]:
    return [tuple(row) for row in json.loads(read(ORACLE))]


def catalog_errors(entries: list[dict[str, object]], template_ids: set[str]) -> list[str]:
    expected = catalog()
    pairs = [(entry["id"], entry["status"]) for entry in entries]
    shipped = {identifier for identifier, status, *_rest in expected if status == "shipped"}
    return [
        message
        for message, actual, wanted in (
            ("manifest rows", pairs, [row[:2] for row in expected]),
            ("template ids", template_ids, shipped),
            ("planned row", {entry["id"] for entry in entries if entry["status"] == "planned"}, PLANNED),
        )
        if actual != wanted
    ]


def document_errors(value: str, entry: dict[str, object]) -> list[str]:
    errors: list[str] = []
    canonical_head = region(read(GALLERY / "theme-toggle.html"), HEAD_MARKERS)
    canonical_brand = region(read(GALLERY / "brand-kit.css"), BRAND_MARKERS)
    if value.count(canonical_brand) != 1 or value.count(canonical_head) != 1:
        errors.append("canonical blocks")
    head = re.search(r"<head\b[^>]*>(.*?)</head>", value, re.IGNORECASE | re.DOTALL)
    prefix = head.group(1).split(canonical_head, 1)[0] if head and canonical_head in head.group(1) else ""
    if not re.fullmatch(
        r"\s*<meta\b[^>]*\bcharset\s*=\s*(['\"])?utf-8\1?[^>]*>\s*", prefix, re.IGNORECASE
    ):
        errors.append("CSP head position")
    if not re.search(
        rf"{re.escape(HEAD_MARKERS[0])}\s*<meta http-equiv=\"Content-Security-Policy\" content=\"{re.escape(POLICY)}\">",
        canonical_head,
    ):
        errors.append("CSP policy")
    source = entry["source"]
    if source["origin"] == "upstream" and not all(
        token in value
        for token in ("Upstream repository: anthropics/html-effectiveness", source["file"], "License: MIT")
    ):
        errors.append("attribution")
    return errors


class ArtifactGalleryTests(unittest.TestCase):
    def test_frozen_catalog_maps_every_manifest_row_and_file(self) -> None:
        expected = catalog()
        entries = json.loads(read(GALLERY / "manifest.json"))["templates"]
        shipped = [row for row in expected if row[1] == "shipped"]
        planned = [row for row in expected if row[1] == "planned"]
        self.assertEqual(22, len(expected))
        self.assertEqual(20, len(shipped))
        self.assertEqual(2, len(planned))
        self.assertEqual(PLANNED, {row[0] for row in planned})
        self.assertEqual(len({row[0] for row in expected}), 22)
        self.assertEqual([], catalog_errors(entries, {path.stem for path in TEMPLATES.glob("*.html")}))

    def test_shipped_documents_preserve_the_compact_standalone_contract(self) -> None:
        entries = {entry["id"]: entry for entry in json.loads(read(GALLERY / "manifest.json"))["templates"]}
        self.assertIn("MIT License", read(GALLERY / "UPSTREAM-NOTICE.md"))
        for identifier, status, *_rest in catalog():
            if status == "shipped":
                with self.subTest(identifier=identifier):
                    self.assertEqual([], document_errors(read(TEMPLATES / f"{identifier}.html"), entries[identifier]))

    def test_compact_guards_reject_catalog_and_document_drift(self) -> None:
        entries = json.loads(read(GALLERY / "manifest.json"))["templates"]
        entry = entries[0]
        document = read(TEMPLATES / "implementation-plan.html")
        remaining = [item for item in entries if item["id"] != "implementation-plan"]
        remaining_files = {path.stem for path in TEMPLATES.glob("*.html")} - {"implementation-plan"}
        self.assertIn("manifest rows", catalog_errors(remaining, remaining_files))
        self.assertIn("template ids", catalog_errors(remaining, remaining_files))
        self.assertIn("canonical blocks", document_errors(document.replace("worker-src 'none'; ", "", 1), entry))


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(ArtifactGalleryTests), label="test-artifact-gallery"))
