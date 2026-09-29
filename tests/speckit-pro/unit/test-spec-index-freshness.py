#!/usr/bin/env python3
"""Git-index membership and release refresh regressions for generated spec maps."""

from __future__ import annotations

import importlib.util
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_ROOT = REPO_ROOT / "tests" / "speckit-pro" / "lib"
FIXTURE = Path(__file__).parent / "fixtures" / "spec-index-freshness" / "historical-stale-index.md"
HOME_FIXTURE = (
    REPO_ROOT
    / "tests"
    / "speckit-pro"
    / "layer1-structural"
    / "fixtures"
    / "spec-index"
    / "roadmap-moc"
    / "docs"
    / "ai"
    / "specs"
    / "myproject-roadmap-MOC.md"
)
sys.path[:0] = [str(PLUGIN_ROOT), str(LIB_ROOT)]
from speckit_pro_runner.helpers.read_only import render_spec_index  # noqa: E402
from test_result import run_counted  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "refresh_release_artifacts_freshness", REPO_ROOT / "scripts" / "refresh-release-artifacts.py"
)
assert spec and spec.loader
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)


class SpecIndexFreshnessTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="spec-index-freshness-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.spec_dir = self.root / "specs" / "art-007-draft-pr-emission"
        self.spec_dir.mkdir(parents=True)
        shutil.copyfile(FIXTURE, self.spec_dir / "SPEC-MOC.md")
        (self.spec_dir / "spec.md").write_text("# Tracked spec\n", encoding="utf-8")
        subprocess.run(["git", "init", "--quiet"], cwd=self.root, check=True, capture_output=True)
        self.stage("specs/art-007-draft-pr-emission/SPEC-MOC.md", "specs/art-007-draft-pr-emission/spec.md")

    def stage(self, *paths: str) -> None:
        subprocess.run(["git", "add", "--", *paths], cwd=self.root, check=True, capture_output=True)

    def generated(self, suffix: str) -> str:
        records, present = render_spec_index(self.root)
        self.assertTrue(present)
        return next(record.rendered for record in records if record.path.name == suffix)

    def test_untracked_nested_file_is_absent_from_backlinks(self) -> None:
        nested = self.spec_dir / "contracts" / "local-only.md"
        nested.parent.mkdir()
        nested.write_text("# Local draft\n", encoding="utf-8")
        generated = self.generated("SPEC-MOC.md")
        self.assertIn("- [spec.md](spec.md)", generated)
        self.assertNotIn("local-only.md", generated)

    def test_staged_nested_addition_is_eligible_for_backlinks(self) -> None:
        nested = self.spec_dir / "contracts" / "staged.md"
        nested.parent.mkdir()
        nested.write_text("# Staged contract\n", encoding="utf-8")
        self.stage(nested.relative_to(self.root).as_posix())
        self.assertIn("- [contracts/staged.md](contracts/staged.md)", self.generated("SPEC-MOC.md"))

    def test_untracked_spec_does_not_enter_tracked_roadmap_home(self) -> None:
        home = self.root / "docs" / "ai" / "specs" / "myproject-roadmap-MOC.md"
        home.parent.mkdir(parents=True)
        shutil.copyfile(HOME_FIXTURE, home)
        self.stage(home.relative_to(self.root).as_posix())
        candidate = self.root / "specs" / "prsg-999-local"
        candidate.mkdir()
        (candidate / "SPEC-MOC.md").write_text(
            '---\nup: "[home](../../docs/ai/specs/myproject-roadmap-MOC.md)"\n'
            'spec_id: "PRSG-999"\nstructureVersion: 1\n---\n# Local candidate\n',
            encoding="utf-8",
        )
        self.assertNotIn("PRSG-999", self.generated("myproject-roadmap-MOC.md"))
        self.stage("specs/prsg-999-local/SPEC-MOC.md")
        self.assertIn("PRSG-999", self.generated("myproject-roadmap-MOC.md"))

    def test_plain_release_refresh_repairs_historical_stale_index(self) -> None:
        from speckit_pro_runner.gates import payloads

        shutil.copytree(
            PLUGIN_ROOT / "speckit_pro_runner",
            self.root / "speckit-pro" / "speckit_pro_runner",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        moc = self.spec_dir / "SPEC-MOC.md"
        stale = moc.read_text(encoding="utf-8")
        self.assertIn("- [.process/manual-uat.md](.process/manual-uat.md)", stale)
        with (
            mock.patch.object(refresh, "refresh_runner_trust_metadata", return_value=[]),
            mock.patch.object(payloads, "build_installed_plugin_payloads"),
            mock.patch.object(refresh, "sync_marketplace_versions", return_value=[]),
        ):
            self.assertEqual(0, refresh.refresh_release_artifacts(self.root))
        repaired = moc.read_text(encoding="utf-8")
        self.assertNotEqual(stale, repaired)
        self.assertNotIn("- [.process/manual-uat.md](.process/manual-uat.md)", repaired)
        self.assertIn("- [spec.md](spec.md)", repaired)

    def test_isolated_check_names_stale_map_and_preserves_source_index_membership(self) -> None:
        script = self.root / "scripts" / "refresh-release-artifacts.py"
        script.parent.mkdir()
        script.write_text(
            "import sys\n"
            f"sys.path.insert(0, {str(PLUGIN_ROOT)!r})\n"
            "from speckit_pro_runner.helpers.read_only import render_spec_index\n"
            "from pathlib import Path\n"
            "for record in render_spec_index(Path.cwd())[0]:\n"
            "    if record.changed:\n"
            "        record.path.write_text(record.rendered, encoding='utf-8')\n",
            encoding="utf-8",
        )
        self.stage("scripts/refresh-release-artifacts.py")
        local = self.spec_dir / "contracts" / "local-only.md"
        local.parent.mkdir()
        local.write_text("# Untracked draft\n", encoding="utf-8")

        def source_status_clean(argv, **kwargs):
            if argv[:2] == ["git", "status"]:
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
            return subprocess.run(argv, **kwargs)

        errors = io.StringIO()
        self.assertEqual(
            1, refresh.check_release_artifacts(self.root, run=source_status_clean, stderr=errors)
        )
        self.assertIn("M specs/art-007-draft-pr-emission/SPEC-MOC.md", errors.getvalue())
        self.assertIn("manual-uat.md", (self.spec_dir / "SPEC-MOC.md").read_text())

        moc = self.spec_dir / "SPEC-MOC.md"
        moc.write_text(self.generated("SPEC-MOC.md"), encoding="utf-8")
        self.stage("specs/art-007-draft-pr-emission/SPEC-MOC.md")
        errors = io.StringIO()
        self.assertEqual(
            0, refresh.check_release_artifacts(self.root, run=source_status_clean, stderr=errors),
            errors.getvalue(),
        )
        self.assertNotIn("local-only.md", moc.read_text())

        staged = self.spec_dir / "contracts" / "staged.md"
        staged.write_text("# Staged\n", encoding="utf-8")
        self.stage("specs/art-007-draft-pr-emission/contracts/staged.md")
        errors = io.StringIO()
        self.assertEqual(
            1, refresh.check_release_artifacts(self.root, run=source_status_clean, stderr=errors)
        )
        self.assertIn("M specs/art-007-draft-pr-emission/SPEC-MOC.md", errors.getvalue())
        moc.write_text(self.generated("SPEC-MOC.md"), encoding="utf-8")
        self.stage("specs/art-007-draft-pr-emission/SPEC-MOC.md")
        self.assertEqual(
            0, refresh.check_release_artifacts(self.root, run=source_status_clean, stderr=io.StringIO())
        )

        literal = self.spec_dir / "contracts" / "[draft].md"
        literal.write_text("# Tracked literal name\n", encoding="utf-8")
        ambiguous = self.spec_dir / "contracts" / "d.md"
        ambiguous.write_text("# Untracked pathspec match\n", encoding="utf-8")
        subprocess.run(
            ["git", "--literal-pathspecs", "add", "--", literal.relative_to(self.root).as_posix()],
            cwd=self.root, check=True, capture_output=True,
        )
        moc.write_text(self.generated("SPEC-MOC.md"), encoding="utf-8")
        self.stage("specs/art-007-draft-pr-emission/SPEC-MOC.md")
        errors = io.StringIO()
        self.assertEqual(
            0, refresh.check_release_artifacts(self.root, run=source_status_clean, stderr=errors),
            errors.getvalue(),
        )
        self.assertIn("[draft].md", moc.read_text())
        self.assertNotIn("[d.md]", moc.read_text())


def main() -> int:
    return run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(SpecIndexFreshnessTests),
        label="test-spec-index-freshness",
    )


if __name__ == "__main__":
    raise SystemExit(main())
