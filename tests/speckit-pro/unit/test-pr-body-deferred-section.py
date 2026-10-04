#!/usr/bin/env python3
"""The PR body a run emits opens with the "Deferred / not verified" section.

The section lists the human UAT the run deferred, is protected by the body
fingerprint, and is refused in draft mode or when an item is malformed.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
for entry in (PLUGIN_ROOT, REPO_ROOT / "tests" / "speckit-pro" / "lib"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from test_result import run_counted  # noqa: E402


def _packet_inputs(**overrides: object) -> dict[str, object]:
    inputs: dict[str, object] = {
        "packet_path": "specs/packet-999-packet/.process/pr-packets/packet-999.json",
        "source_feature_dir": "specs/packet-999-packet",
        "target": {"base_branch": "main", "head_branch": "agent/packet-999-packet"},
        "title_type": "feat",
        "title_scope": "packet-999",
        "title_description": "Generate reviewer packet",
        "changed_files": ["specs/packet-999-packet/spec.md"],
        "verification": ["unit suite passed"],
        "summary": "Adds a reviewer packet.",
        "how_to_uat": "No manual UAT is required for this fixture.",
        "known_gaps": ["Human UAT story 2 is not verified."],
        "non_goals": ["No live pull-request mutation."],
    }
    inputs.update(overrides)
    return inputs


class DeferredSectionInPrBodyTests(unittest.TestCase):
    ITEMS = [
        {"item": "UAT story 1: the report page loads", "reason": "It needs a person at a browser.",
         "finish": "Follow steps 1 to 3 of the UAT runbook."},
        {"item": "UAT story 2: the export opens in a spreadsheet app",
         "reason": "It needs a person to open the exported file.",
         "finish": "Follow steps 4 to 6 of the UAT runbook and record the result on the pull request."},
    ]

    def render(self, **overrides: object) -> dict[str, object]:
        from speckit_pro_runner.helpers.pr_packet import normalize_packet_input

        return normalize_packet_input(SimpleNamespace(inputs=_packet_inputs(**overrides)))

    def test_body_opens_with_the_deferred_section_and_still_validates(self) -> None:
        from speckit_pro_runner.helpers.read_only import validate_pr_packet_read_only

        rendered = self.render(deferred_items=self.ITEMS)
        self.assertNotIn("diagnostic", rendered, rendered)
        body = str(rendered["body"])
        headings = [line for line in body.splitlines() if line.startswith("#")]
        self.assertEqual(headings[:3], ["# feat(packet-999): Generate reviewer packet",
                                        "## Deferred / not verified", "## Summary"])
        section = body.split("## Deferred / not verified", 1)[1].split("## Summary", 1)[0]
        for item in self.ITEMS:
            for value in item.values():
                self.assertIn(value, section)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            packet = rendered["packet"]
            assert isinstance(packet, dict)
            for relative, content in ((packet["body_file"], body),
                                      (rendered["packet_path"], json.dumps(packet, indent=2) + "\n")):
                path = root / str(relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            (root / "speckit-pro/speckit_pro_runner").mkdir(parents=True)
            result = validate_pr_packet_read_only({"packet_path": rendered["packet_path"]}, root)
            verdict = json.loads(str(result["stdout"]))
            self.assertEqual((result["exit_code"], verdict["status"]), (0, "passed"), verdict)

    def test_the_section_is_protected_by_the_body_fingerprint(self) -> None:
        with_items = self.render(deferred_items=self.ITEMS)["packet"]
        other = self.render(deferred_items=[dict(self.ITEMS[0], reason="Different reason.")])["packet"]
        assert isinstance(with_items, dict) and isinstance(other, dict)
        self.assertNotEqual(with_items["protected_body_fingerprint"]["value"],
                            other["protected_body_fingerprint"]["value"])

    def test_no_deferred_items_leaves_the_body_unchanged(self) -> None:
        self.assertEqual(self.render()["body"], self.render(deferred_items=[])["body"])
        self.assertNotIn("Deferred / not verified", str(self.render()["body"]))

    def test_malformed_items_and_draft_mode_are_refused(self) -> None:
        for override in (
            {"deferred_items": [{"item": "T042", "reason": "veto"}]},
            {"deferred_items": "T042"},
            {"deferred_items": self.ITEMS, "mode": "draft"},
        ):
            with self.subTest(override=override):
                self.assertIn("diagnostic", self.render(**override))


class UnratifiedDefaultsInPrBodyTests(unittest.TestCase):
    FLAG = "Unratified quality-gate defaults: .specify/quality-gates.json is missing; ratify it."
    ITEM = {"item": "UAT story 1", "reason": "It needs a person.", "finish": "Follow the runbook."}

    def render(self, **overrides: object) -> dict[str, object]:
        from speckit_pro_runner.helpers.pr_packet import normalize_packet_input

        return normalize_packet_input(SimpleNamespace(inputs=_packet_inputs(**overrides)))

    def test_body_carries_the_flag_after_deferred_items_and_still_validates(self) -> None:
        from speckit_pro_runner.helpers.read_only import validate_pr_packet_read_only

        rendered = self.render(unratified_defaults=self.FLAG, deferred_items=[self.ITEM])
        self.assertNotIn("diagnostic", rendered, rendered)
        body = str(rendered["body"])
        headings = [line for line in body.splitlines() if line.startswith("#")]
        self.assertEqual(headings[1:4], ["## Deferred / not verified", "## Unratified quality-gate defaults",
                                         "## Summary"])
        self.assertIn(self.FLAG, body.split("## Unratified quality-gate defaults", 1)[1].split("## Summary", 1)[0])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            packet = rendered["packet"]
            assert isinstance(packet, dict)
            for relative, content in ((packet["body_file"], body),
                                      (rendered["packet_path"], json.dumps(packet, indent=2) + "\n")):
                path = root / str(relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            (root / "speckit-pro/speckit_pro_runner").mkdir(parents=True)
            result = validate_pr_packet_read_only({"packet_path": rendered["packet_path"]}, root)
            verdict = json.loads(str(result["stdout"]))
            self.assertEqual((result["exit_code"], verdict["status"]), (0, "passed"), verdict)

    def test_flag_is_protected_and_absent_input_leaves_the_body_unchanged(self) -> None:
        flagged = self.render(unratified_defaults=self.FLAG)["packet"]
        other = self.render(unratified_defaults=self.FLAG + " More.")["packet"]
        assert isinstance(flagged, dict) and isinstance(other, dict)
        self.assertNotEqual(flagged["protected_body_fingerprint"]["value"],
                            other["protected_body_fingerprint"]["value"])
        self.assertEqual(self.render()["body"], self.render(unratified_defaults=None)["body"])
        self.assertNotIn("Unratified", str(self.render()["body"]))

    def test_malformed_flag_and_draft_mode_are_refused(self) -> None:
        for override in ({"unratified_defaults": "two\nlines"}, {"unratified_defaults": ""},
                         {"unratified_defaults": 7}, {"unratified_defaults": self.FLAG, "mode": "draft"}):
            with self.subTest(override=override):
                self.assertIn("diagnostic", self.render(**override))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-pr-body-deferred-section"))
