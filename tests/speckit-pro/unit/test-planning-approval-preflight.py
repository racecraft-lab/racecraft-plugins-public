#!/usr/bin/env python3
"""Canonical navigation preflight through the planning-approval request seam."""
import re
import runpy
import unittest
from pathlib import Path

fixture = runpy.run_path(str(Path(__file__).with_name("test-planning-approval.py")))
NavigationFixture = fixture["NavigationFixture"]
render_spec_index = fixture["render_spec_index"]
render_feature_spec_index = fixture["render_feature_spec_index"]
run_counted = fixture["run_counted"]
SOURCE = Path(__file__).resolve().parents[3]
RUNNERS = (SOURCE / "speckit-pro", *(SOURCE / "dist" / host / "speckit-pro" for host in ("claude", "codex")))


class MapAssertions(NavigationFixture):
    def withoutGeneratedBlocks(self, text):
        return re.sub(r"<!-- GENERATED:(\w+):START[^\n]*\n.*?<!-- GENERATED:\1:END -->\r?\n",
                      "", text, flags=re.DOTALL)

    def assertFreshMapRefused(self, text):
        self.map_path.write_text(text)
        approval = self.approval()
        original = self.map_path.read_bytes()
        self.assertNotEqual(render_feature_spec_index(self.root, "specs/demo", text), text)
        for runner in RUNNERS:
            self.runner_root = runner
            for mode in ("dry_run", "apply"):
                with self.subTest(runner=runner.relative_to(SOURCE).as_posix(), mode=mode):
                    self.assertRefused(self.call("record", mode, approval=approval), "regenerate")
                    self.assertEqual(self.map_path.read_bytes(), original)
                    self.assertFalse((self.feature / "plan-approvals").exists())

    def assertMapRoundTrip(self):
        original = self.map_path.read_bytes() if self.map_path.exists() else None
        for runner in RUNNERS:
            with self.subTest(runner=runner.relative_to(SOURCE).as_posix()):
                self.runner_root = runner
                if original is not None:
                    self.map_path.write_bytes(original)
                approval = self.approval()
                self.assertEqual(self.call("record", "dry_run", approval=approval)["status"], "ok")
                recorded = self.call("record", "apply", approval=approval)
                self.assertEqual(recorded["status"], "ok", recorded)
                self.assertEqual(self.call("verify")["status"], "ok")
                (self.root / recorded["data"]["record_path"]).unlink()
                (self.feature / "plan-approvals").rmdir()
        if original is not None:
            self.map_path.write_bytes(original)


class NavigationPreflightTest(MapAssertions):
    def test_record_refuses_removing_all_generated_pairs(self):
        text = self.withoutGeneratedBlocks(self.original)
        self.assertNotIn("<!-- GENERATED:", text)
        self.assertFreshMapRefused(text)

    def test_record_refuses_altering_every_generated_sentinel(self):
        self.assertFreshMapRefused(self.original.replace("GENERATED:", "GENRATED:"))

    def test_record_refuses_lowercase_generated_sentinels(self):
        self.assertFreshMapRefused(self.original.replace("GENERATED:", "generated:"))

    def test_record_refuses_spaced_generated_sentinels(self):
        self.assertFreshMapRefused(self.original.replace("GENERATED:", "GENERATED :"))

    def test_record_refuses_missing_marker_lines_with_retained_bodies(self):
        text = "".join(line for line in self.original.splitlines(keepends=True) if "<!-- GENERATED:" not in line)
        self.assertFreshMapRefused(text)

    def test_partial_layout_binds_removal_then_refuses_last_pair_removal(self):
        self.approval()
        self.map_path.write_text(render_spec_index(self.root)[0][0].rendered)
        self.captureNavigation()
        for zone, block in self.blocks.items():
            with self.subTest(zone=zone):
                partial = self.original.replace(block, "")
                self.map_path.write_text(partial)
                approval = self.approval()
                self.assertNotEqual(approval["confirmation"]["manifest_digest"], self.binding["manifest_digest"])
                self.assertEqual(render_feature_spec_index(self.root, "specs/demo", partial), partial)
                self.assertMapRoundTrip()
                remaining = self.withoutGeneratedBlocks(partial)
                self.assertFreshMapRefused(remaining)

    def test_missing_map_is_optional_but_recreated_markerless_map_is_checked(self):
        self.map_path.unlink(missing_ok=False)
        self.assertMapRoundTrip()
        self.assertFalse(self.map_path.exists())
        self.assertFreshMapRefused("---\nstructureVersion: 1\n---\n# Recreated map\n")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NavigationPreflightTest)
    raise SystemExit(run_counted(suite, label="test-planning-approval-preflight"))
