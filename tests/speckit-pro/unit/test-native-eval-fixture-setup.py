#!/usr/bin/env python3
"""Focused contracts for explicit Git feature-overlay deletions."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tests" / "speckit-pro" / "lib"))

from native_eval_fixture_setup import _apply_feature_deletions, materialize_workspace  # noqa: E402


class NativeEvalFixtureSetupTests(unittest.TestCase):
    def plan(self, source_root: Path, *, deletion: str) -> dict[str, object]:
        payload = b"baseline workflow\n"
        (source_root / "workflow.fixture").write_bytes(payload)
        return {
            "schema_version": "native-eval-fixtures/v2",
            "source_root": str(source_root),
            "fixtures": [],
            "git_repository": {
                "recipe": "baseline-feature-origin-main/v1",
                "baseline": [{
                    "source": "workflow.fixture",
                    "destination": "docs/ai/specs/SPEC-021-workflow.md",
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }],
                "feature_deletions": [deletion],
                "worktrees": [{
                    "path": ".worktrees/spec-021",
                    "branch": "scenario/spec-021",
                    "revision": "baseline",
                }],
            },
        }

    def test_deletion_only_overlay_is_external_only_and_deterministic(self) -> None:
        receipts = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            plan = self.plan(source, deletion="docs/ai/specs/SPEC-021-workflow.md")
            for name in ("first", "second"):
                workspace = root / name
                workspace.mkdir()
                receipt = materialize_workspace(plan, workspace)
                self.assertFalse((workspace / "docs/ai/specs/SPEC-021-workflow.md").exists())
                self.assertEqual(
                    (workspace / ".worktrees/spec-021/docs/ai/specs/SPEC-021-workflow.md").read_text(),
                    "baseline workflow\n",
                )
                receipts.append(receipt["git_repository"])
        for field in ("baseline_commit", "baseline_tree", "feature_commit", "feature_tree"):
            self.assertEqual(receipts[0][field], receipts[1][field], field)

    def test_feature_deletions_fail_closed_on_unsafe_or_unknown_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            for deletion, message in (
                ("../outside", "canonical relative path"),
                (".git/config", "reserved runtime path"),
                ("docs/ai/specs/missing.md", "exact baseline file"),
            ):
                workspace = root / deletion.replace("/", "-").replace("..", "parent")
                workspace.mkdir()
                with self.assertRaisesRegex(ValueError, message):
                    materialize_workspace(self.plan(source, deletion=deletion), workspace)

    def test_feature_deletion_never_follows_leaf_or_parent_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / "outside"
            outside.write_text("keep\n", encoding="utf-8")
            leaf = root / "leaf"
            leaf.symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "not a regular file"):
                _apply_feature_deletions(root, [PurePosixPath("leaf")])
            self.assertEqual(outside.read_text(encoding="utf-8"), "keep\n")

            linked_parent = root / "linked"
            linked_parent.symlink_to(root)
            with self.assertRaisesRegex(ValueError, "parent is a symlink"):
                _apply_feature_deletions(root, [PurePosixPath("linked/outside")])
            self.assertEqual(outside.read_text(encoding="utf-8"), "keep\n")


if __name__ == "__main__":
    unittest.main()
