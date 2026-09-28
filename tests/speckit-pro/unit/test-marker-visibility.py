#!/usr/bin/env python3
"""Marker counts agree across gates and the read-only helper."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "speckit-pro"))
from speckit_pro_runner.helpers import read_only  # noqa: E402

CASES = Path(__file__).parent / "fixtures" / "marker-visibility" / "cases.json"


class MarkerVisibilityTests(unittest.TestCase):
    def test_visible_gap_tags_match_g4_and_count_modes(self) -> None:
        case = json.loads(CASES.read_text())["gaps"]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            feature = root / "specs" / "001-demo"
            (feature / "checklists").mkdir(parents=True)
            (feature / "spec.md").write_text(case["spec"])
            (feature / "plan.md").write_text(case["plan"])
            (feature / "checklists" / "review.md").write_text(case["checklist"])
            inputs = {"feature_dir": "specs/001-demo"}
            gaps = json.loads(read_only.count_markers({**inputs, "type": "gaps"}, root)["stdout"])
            all_markers = json.loads(read_only.count_markers({**inputs, "type": "all"}, root)["stdout"])
            g4 = json.loads(read_only.validate_gate({**inputs, "gate": "G4"}, root)["stdout"])
            self.assertEqual(case["expected"], {key: gaps[key] for key in case["expected"]})
            self.assertEqual(gaps["total"], all_markers["gaps"])
            self.assertEqual(gaps["total"], g4["markers"])
            self.assertEqual(case["spec"].count("[HIGH]"), all_markers["high"])
            self.assertEqual(gaps["total"], len(gaps["details"]))
            self.assertTrue(all("`[Gap]`" not in detail for detail in gaps["details"]))

    def test_visible_clarifications_match_gates_and_count_modes(self) -> None:
        case = json.loads(CASES.read_text())["clarifications"]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            feature = root / "specs" / "001-demo"
            feature.mkdir(parents=True)
            (feature / "spec.md").write_text(case["spec"])
            (feature / "plan.md").write_text(case["plan"])
            inputs = {"feature_dir": "specs/001-demo"}
            counts = json.loads(read_only.count_markers({**inputs, "type": "clarifications"}, root)["stdout"])
            all_markers = json.loads(read_only.count_markers({**inputs, "type": "all"}, root)["stdout"])
            self.assertEqual(case["expected"], {key: counts[key] for key in case["expected"]})
            self.assertEqual(counts["total"], all_markers["clarifications"])
            self.assertEqual(counts["total"], len(counts["details"]))
            self.assertTrue(all("`[NEEDS CLARIFICATION: code]`" not in detail for detail in counts["details"]))
            for gate in ("G1", "G2"):
                payload = json.loads(read_only.validate_gate({**inputs, "gate": gate}, root)["stdout"])
                self.assertEqual(counts["spec"], payload["markers"])
                self.assertEqual(3, len(payload["details"]))
            g3 = json.loads(read_only.validate_gate({**inputs, "gate": "G3"}, root)["stdout"])
            self.assertIn("NC:1", g3["reason"])


    def test_list_continuations_and_nested_tags_do_not_hide_real_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            feature = root / "specs" / "001-demo"
            (feature / "checklists").mkdir(parents=True)
            (feature / "spec.md").write_text(
                "- [ ] Parent\n"
                "    [NEEDS CLARIFICATION: is [Option] required?]\n"
                "\n"
                "      [NEEDS CLARIFICATION: hidden code]\n"
            )
            (feature / "plan.md").write_text("Plan is ready.\n")
            (feature / "checklists" / "review.md").write_text(
                "- [ ] Parent\n"
                "    - [ ] Nested item [Gap]\n"
                "[outer [Gap] prose] is not a tag.\n"
                "\n"
                "    [Gap] in code\n"
            )
            (feature / "checklists" / "notes.txt").write_text("[Gap] in a non-checklist file\n")
            inputs = {"feature_dir": "specs/001-demo"}
            gaps = json.loads(read_only.count_markers({**inputs, "type": "gaps"}, root)["stdout"])
            self.assertEqual(1, gaps["total"])
            self.assertEqual(1, len(gaps["details"]))
            self.assertIn("review.md", gaps["details"][0])
            g4 = json.loads(read_only.validate_gate({**inputs, "gate": "G4"}, root)["stdout"])
            self.assertEqual((False, 1), (g4["pass"], g4["markers"]))
            self.assertEqual(1, len(g4["details"]))
            clarifications = json.loads(read_only.count_markers({**inputs, "type": "clarifications"}, root)["stdout"])
            self.assertEqual(1, clarifications["total"])
            self.assertEqual(1, len(clarifications["details"]))
            for gate in ("G1", "G2"):
                payload = json.loads(read_only.validate_gate({**inputs, "gate": gate}, root)["stdout"])
                self.assertEqual((False, 1), (payload["pass"], payload["markers"]))



    def test_quoted_and_list_fences_hide_code_but_keep_visible_nested_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            feature = root / "specs" / "001-demo"
            (feature / "checklists").mkdir(parents=True)
            (feature / "spec.md").write_text(
                "> ```md\n> [NEEDS CLARIFICATION: quoted code]\n> ```\n"
                "> visible [NEEDS CLARIFICATION: quoted prose]\n"
            )
            (feature / "plan.md").write_text("Plan is ready.\n")
            (feature / "checklists" / "review.md").write_text(
                "- [ ] Parent\n"
                "  ```md\n  [Gap] in fenced code\n  ```\n"
                "    - [ ] Nested [Gap] in prose\n"
            )
            inputs = {"feature_dir": "specs/001-demo"}
            gaps = json.loads(read_only.count_markers({**inputs, "type": "gaps"}, root)["stdout"])
            clarifications = json.loads(read_only.count_markers({**inputs, "type": "clarifications"}, root)["stdout"])
            self.assertEqual((1, 1), (gaps["total"], clarifications["total"]))
            self.assertEqual(1, len(gaps["details"]))
            self.assertEqual(1, len(clarifications["details"]))


    def test_container_boundaries_and_inline_spans_preserve_visible_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            feature = root / "specs" / "001-demo"
            (feature / "checklists").mkdir(parents=True)
            (feature / "spec.md").write_text("Spec is ready.\n")
            (feature / "plan.md").write_text("Plan is ready.\n")
            (feature / "checklists" / "review.md").write_text(
                "```text\n> [Gap] literal fenced code\n```\n"
                "- ```text\n  [Gap] list-item code\n  ```\n"
                "> ```text\n> [Gap] quoted code\n"
                "[Gap] after quote\n"
                "- item\n  ```text\n  [Gap] list code\n"
                "[Gap] after list\n"
                "> - item\n>\n>     [Gap] quoted continuation\n"
                "- parent\n  - child\n  [Gap] outer continuation\n"
                "# Heading\n    [Gap] indented code\n"
                "`multiline\n[Gap] in code span\n`\n"
                "\`[Gap] escaped opener`\n"
            )
            result = json.loads(read_only.count_markers(
                {"feature_dir": "specs/001-demo", "type": "gaps"}, root
            )["stdout"])
            self.assertEqual(5, result["total"], result["details"])
            self.assertEqual(result["total"], len(result["details"]))
            g4 = json.loads(read_only.validate_gate(
                {"feature_dir": "specs/001-demo", "gate": "G4"}, root
            )["stdout"])
            self.assertEqual((False, 5), (g4["pass"], g4["markers"]))

    def test_nested_containers_hide_code_and_keep_visible_markers(self) -> None:
        cases = (
            ("- ```text\n  [Gap] list-item code\n  ```\n", 0, None),
            ("- item\n  > ```text\n  > [Gap] code\n  > ```\n"
             "    [Gap] continuation\n", 1, 5),
            ("> - item\n>   > nested quote\n>     [Gap] visible list prose\n", 1, 3),
            ("- parent\n  - child\n    > ```text\n    > [Gap] code\n"
             "    > ```\n", 0, None),
        )
        for markdown, expected_count, expected_line in cases:
            with self.subTest(markdown=markdown), tempfile.TemporaryDirectory() as temp:
                root = Path(temp).resolve()
                feature = root / "specs" / "001-demo"
                (feature / "checklists").mkdir(parents=True)
                (feature / "spec.md").write_text("Spec is ready.\n")
                (feature / "plan.md").write_text("Plan is ready.\n")
                (feature / "checklists" / "review.md").write_text(markdown)
                gaps = json.loads(read_only.count_markers(
                    {"feature_dir": "specs/001-demo", "type": "gaps"}, root
                )["stdout"])
                self.assertEqual(expected_count, gaps["total"], gaps["details"])
                self.assertEqual(expected_count, len(gaps["details"]))
                if expected_line is not None:
                    self.assertIn(f":{expected_line}:", gaps["details"][0])

    def test_g4_missing_required_artifact_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            feature = root / "specs" / "001-demo"
            feature.mkdir(parents=True)
            inputs = {"feature_dir": "specs/001-demo", "gate": "G4"}
            for missing in ("spec.md", "plan.md"):
                result = read_only.validate_gate(inputs, root)
                payload = json.loads(result["stdout"])
                self.assertEqual(1, result["exit_code"])
                self.assertFalse(payload["pass"])
                self.assertIn(missing, payload["reason"])
                (feature / missing).write_text("Present.\n")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MarkerVisibilityTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"test-marker-visibility: {passed}/{total} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
