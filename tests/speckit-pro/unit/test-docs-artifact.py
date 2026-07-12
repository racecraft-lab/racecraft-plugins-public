#!/usr/bin/env python3
"""Focused contracts for the docs artifact workflow helper."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "docs-artifact.py"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


def load_helper():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("docs_artifact", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load docs artifact helper: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


DOCS_ARTIFACT = load_helper()


class DocsArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="docs-artifact-")
        self.temp_root = Path(self._tmp.name).resolve()
        self.repo = self.temp_root / "repo"
        self.docs_site = self.repo / "docs-site"
        self.artifact = self.docs_site / "dist"
        self.docs_site.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_prepare_removes_existing_artifact(self) -> None:
        (self.artifact / "nested").mkdir(parents=True)
        (self.artifact / "nested" / "index.html").write_text("docs", encoding="utf-8")

        resolved = DOCS_ARTIFACT.prepare_artifact(self.repo, "docs-site/dist")

        self.assertEqual(resolved, self.artifact)
        self.assertFalse(self.artifact.exists())

    def test_prepare_allows_missing_artifact(self) -> None:
        resolved = DOCS_ARTIFACT.prepare_artifact(self.repo, "docs-site/dist")

        self.assertEqual(resolved, self.artifact)
        self.assertFalse(self.artifact.exists())

    def test_verify_accepts_non_empty_artifact(self) -> None:
        self.artifact.mkdir()
        (self.artifact / "index.html").write_text("docs", encoding="utf-8")

        resolved = DOCS_ARTIFACT.verify_artifact(self.repo, "docs-site/dist")

        self.assertEqual(resolved, self.artifact)

    def test_verify_rejects_missing_artifact(self) -> None:
        with self.assertRaisesRegex(DOCS_ARTIFACT.ArtifactError, "missing after validation"):
            DOCS_ARTIFACT.verify_artifact(self.repo, "docs-site/dist")

    def test_verify_rejects_empty_artifact(self) -> None:
        self.artifact.mkdir()

        with self.assertRaisesRegex(DOCS_ARTIFACT.ArtifactError, "empty after validation"):
            DOCS_ARTIFACT.verify_artifact(self.repo, "docs-site/dist")

    def test_prepare_rejects_repository_root(self) -> None:
        with self.assertRaisesRegex(DOCS_ARTIFACT.ArtifactError, "repository root"):
            DOCS_ARTIFACT.prepare_artifact(self.repo, ".")

    def test_prepare_rejects_other_internal_directories(self) -> None:
        for relative in (".github", "docs-site", "scripts"):
            with self.subTest(relative=relative):
                target = self.repo / relative
                target.mkdir(parents=True, exist_ok=True)
                with self.assertRaisesRegex(DOCS_ARTIFACT.ArtifactError, "only 'docs-site/dist' is allowed"):
                    DOCS_ARTIFACT.prepare_artifact(self.repo, relative)
                self.assertTrue(target.is_dir())

    def test_prepare_rejects_parent_traversal(self) -> None:
        with self.assertRaisesRegex(DOCS_ARTIFACT.ArtifactError, "path segments are not allowed"):
            DOCS_ARTIFACT.prepare_artifact(self.repo, "../outside")

    def test_prepare_rejects_absolute_outside_path(self) -> None:
        outside = self.temp_root / "outside"
        outside.mkdir()

        with self.assertRaisesRegex(DOCS_ARTIFACT.ArtifactError, "outside repository"):
            DOCS_ARTIFACT.prepare_artifact(self.repo, outside)
        self.assertTrue(outside.is_dir())

    def test_prepare_rejects_symlink_target(self) -> None:
        outside = self.temp_root / "outside"
        outside.mkdir()
        self.artifact.symlink_to(outside, target_is_directory=True)

        with self.assertRaisesRegex(DOCS_ARTIFACT.ArtifactError, "symlink traversal"):
            DOCS_ARTIFACT.prepare_artifact(self.repo, "docs-site/dist")
        self.assertTrue(outside.is_dir())

    def test_prepare_rejects_symlink_parent_escape(self) -> None:
        outside = self.temp_root / "outside"
        outside.mkdir()
        self.docs_site.rmdir()
        self.docs_site.symlink_to(outside, target_is_directory=True)

        with self.assertRaisesRegex(DOCS_ARTIFACT.ArtifactError, "symlink traversal"):
            DOCS_ARTIFACT.prepare_artifact(self.repo, "docs-site/dist")
        self.assertTrue(outside.is_dir())

    def test_prepare_rejects_file_target(self) -> None:
        self.artifact.write_text("not a directory", encoding="utf-8")

        with self.assertRaisesRegex(DOCS_ARTIFACT.ArtifactError, "not a directory"):
            DOCS_ARTIFACT.prepare_artifact(self.repo, "docs-site/dist")
        self.assertTrue(self.artifact.is_file())

    def test_prepare_does_not_delete_adjacent_paths(self) -> None:
        self.artifact.mkdir()
        (self.artifact / "stale.html").write_text("stale", encoding="utf-8")
        sibling = self.docs_site / "keep.txt"
        sibling.write_text("keep", encoding="utf-8")
        other = self.repo / "other-output"
        other.mkdir()
        (other / "keep.txt").write_text("keep", encoding="utf-8")

        DOCS_ARTIFACT.prepare_artifact(self.repo, "docs-site/dist")

        self.assertFalse(self.artifact.exists())
        self.assertEqual(sibling.read_text(encoding="utf-8"), "keep")
        self.assertEqual((other / "keep.txt").read_text(encoding="utf-8"), "keep")

    def test_verify_rejects_descendant_symlink(self) -> None:
        self.artifact.mkdir()
        outside = self.docs_site / "outside.html"
        outside.write_text("private", encoding="utf-8")
        link = self.artifact / "leak.html"
        try:
            link.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")

        with self.assertRaisesRegex(DOCS_ARTIFACT.ArtifactError, "contains a symbolic link"):
            DOCS_ARTIFACT.verify_artifact(self.repo, "docs-site/dist")

    def test_verify_rejects_descendant_hard_link(self) -> None:
        self.artifact.mkdir()
        source = self.docs_site / "outside.html"
        source.write_text("private", encoding="utf-8")
        link = self.artifact / "leak.html"
        try:
            os.link(source, link)
        except OSError as exc:
            self.skipTest(f"hard-link creation unavailable: {exc}")

        with self.assertRaisesRegex(DOCS_ARTIFACT.ArtifactError, "contains a hard-linked file"):
            DOCS_ARTIFACT.verify_artifact(self.repo, "docs-site/dist")

    def test_verify_rejects_special_file(self) -> None:
        self.artifact.mkdir()
        fifo = self.artifact / "stream"
        try:
            os.mkfifo(fifo)
        except (AttributeError, OSError) as exc:
            self.skipTest(f"FIFO creation unavailable: {exc}")

        with self.assertRaisesRegex(DOCS_ARTIFACT.ArtifactError, "contains a special file"):
            DOCS_ARTIFACT.verify_artifact(self.repo, "docs-site/dist")

    def test_cli_failure_emits_actionable_github_annotation(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            returncode = DOCS_ARTIFACT.main(["verify", "docs-site/dist"], repo_root=self.repo)

        annotation = stderr.getvalue()
        self.assertEqual(returncode, 1)
        self.assertTrue(annotation.startswith("::error title=Docs artifact::"), annotation)
        self.assertIn("missing after validation", annotation)
        self.assertIn("Run the docs validation step", annotation)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(DocsArtifactTests)


def main() -> int:
    return run_counted(build_suite(), label="test-docs-artifact")


if __name__ == "__main__":
    raise SystemExit(main())
