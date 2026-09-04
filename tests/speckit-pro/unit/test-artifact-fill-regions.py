#!/usr/bin/env python3
"""Fill markers and registered export coverage for gallery templates."""

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
for root in (REPO_ROOT / "speckit-pro", REPO_ROOT / "tests" / "speckit-pro" / "lib"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from speckit_pro_runner.helpers.read_only import SWEEP_EXPORT_REGISTRY  # noqa: E402
from test_result import run_counted  # noqa: E402


MARKER = re.compile(r"<!--\s*FILL:([a-z0-9-]+):(START|END)\s*-->")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def shipped_ids() -> tuple[str, ...]:
    return tuple(row[0] for row in json.loads(read(ORACLE)) if row[1] == "shipped")


def expected_exports() -> set[tuple[str, str]]:
    return {
        (identifier, kind)
        for identifier, status, kinds, *_rest in json.loads(read(ORACLE))
        if status == "shipped"
        for kind in kinds
    }


def fill_regions(value: str) -> list[tuple[str, int, int, str]]:
    open_slots: dict[str, tuple[int, int]] = {}
    regions: list[tuple[str, int, int, str]] = []
    for match in MARKER.finditer(value):
        slot, edge = match.groups()
        if edge == "START":
            if open_slots:
                raise ValueError("nested or duplicate fill start")
            open_slots[slot] = (match.start(), match.end())
        else:
            if slot not in open_slots:
                raise ValueError("orphan fill end")
            start, body_start = open_slots.pop(slot)
            regions.append((slot, start, match.end(), value[body_start:match.start()]))
    if open_slots:
        raise ValueError("unclosed fill start")
    return regions


def replace_fill(value: str, slot: str, authored: str) -> str:
    start = f"<!-- FILL:{slot}:START -->"
    end = f"<!-- FILL:{slot}:END -->"
    before, remainder = value.split(start, 1)
    _sample, after = remainder.split(end, 1)
    return f"{before}{start}{authored}{end}{after}"


class ArtifactFillRegionTests(unittest.TestCase):
    def test_every_shipped_template_has_ordered_distinct_nonempty_regions(self) -> None:
        for identifier in shipped_ids():
            with self.subTest(identifier=identifier):
                value = read(TEMPLATES / f"{identifier}.html")
                regions = fill_regions(value)
                self.assertTrue(regions)
                self.assertEqual(len({slot for slot, _start, _end, _body in regions}), len(regions))
                self.assertTrue(all(body.strip() for _slot, _start, _end, body in regions))
                self.assertEqual(len({body for _slot, _start, _end, body in regions}), len(regions))

    def test_fill_replacement_keeps_markers_and_everything_outside_the_slot(self) -> None:
        value = read(TEMPLATES / "implementation-plan.html")
        slot, start, end, sample = next(region for region in fill_regions(value) if region[0] == "feature-header")
        authored = (
            '<p class="eyebrow"><span id="feature-id">RSE-707</span> · draft pull request</p>'
            '<h1 id="feature-name">Independent authoring proof</h1><p class="lede">Prepared independently.</p>'
        )
        filled = replace_fill(value, slot, authored)
        filled_region = next(body for name, _start, _end, body in fill_regions(filled) if name == slot)
        self.assertEqual(value[:start], filled[:start])
        self.assertEqual(value[end:], filled[filled.index(f"<!-- FILL:{slot}:END -->") + len(f"<!-- FILL:{slot}:END -->"):])
        self.assertIn(authored, filled)
        self.assertNotIn("NIMBUS-101", filled_region)
        self.assertNotIn("Offline Draft Sync", filled_region)
        self.assertNotIn("sample content", filled_region)
        self.assertNotIn(sample, filled_region)
        self.assertEqual(1, filled_region.count('id="feature-id"'))
        self.assertEqual(1, filled_region.count('id="feature-name"'))
        self.assertEqual(1, filled.count("<h1"))
        self.assertEqual(1, filled.count(f"<!-- FILL:{slot}:START -->"))
        self.assertEqual(1, filled.count(f"<!-- FILL:{slot}:END -->"))

    def test_registry_covers_exactly_the_manifest_exports_for_shipped_templates(self) -> None:
        entries = json.loads(read(GALLERY / "manifest.json"))["templates"]
        manifest_exports = {
            (entry["id"], kind)
            for entry in entries
            if entry["status"] == "shipped"
            for kind in entry["exports"]
        }
        registry_exports = {
            (entry.template_id, entry.kind)
            for entry in SWEEP_EXPORT_REGISTRY
            if entry.template_id and entry.kind in {"prompt", "markdown"}
        }
        self.assertEqual(expected_exports(), manifest_exports)
        self.assertEqual(expected_exports(), registry_exports)
        self.assertEqual(17, len(expected_exports()))
        self.assertNotEqual(
            expected_exports(),
            {pair for pair in expected_exports() if pair[0] != "implementation-plan"},
        )

    def test_marker_helper_rejects_a_missing_end_marker(self) -> None:
        value = read(TEMPLATES / "implementation-plan.html")
        self.assertRaises(ValueError, fill_regions, value.replace("<!-- FILL:feature-header:END -->", "", 1))


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(ArtifactFillRegionTests), label="test-artifact-fill-regions"))
