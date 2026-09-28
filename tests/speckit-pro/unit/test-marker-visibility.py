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
            self.assertEqual(3, len(gaps["details"]))
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
            self.assertEqual(3, len(counts["details"]))
            self.assertTrue(all("`[NEEDS CLARIFICATION: code]`" not in detail for detail in counts["details"]))
            for gate in ("G1", "G2"):
                payload = json.loads(read_only.validate_gate({**inputs, "gate": gate}, root)["stdout"])
                self.assertEqual(counts["spec"], payload["markers"])
                self.assertEqual(3, len(payload["details"]))
            g3 = json.loads(read_only.validate_gate({**inputs, "gate": "G3"}, root)["stdout"])
            self.assertIn("NC:1", g3["reason"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MarkerVisibilityTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"test-marker-visibility: {passed}/{total} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
