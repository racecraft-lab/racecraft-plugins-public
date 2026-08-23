#!/usr/bin/env python3
"""Subprocess exit-code contract tests for the version-gated MOC lints.

Port of ``test-moc-lint-exit-codes.sh`` (XPLAT-010 T045). The non-root
count-parity baseline is pinned at TOTAL: 36.
"""

from __future__ import annotations

import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ORPHAN = REPO_ROOT / "tests" / "speckit-pro" / "layer1-structural" / "validate-moc-orphan.py"
STALE = REPO_ROOT / "tests" / "speckit-pro" / "layer1-structural" / "validate-moc-stale-index.py"
STALE_RUNTIME_SYMLINK = (
    REPO_ROOT
    / "tests"
    / "speckit-pro"
    / "layer1-structural"
    / "fixtures"
    / "moc"
    / "stale"
    / "stale-broken-symlink"
    / "broken-link.md"
)

LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


def run_lint(script: Path, root: Path | None = None) -> subprocess.CompletedProcess[str]:
    argv = [sys.executable, str(script)]
    if root is not None:
        argv.append(str(root))
    return subprocess.run(
        argv,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )


def chmod_tree(root: Path, mode: int) -> None:
    if not root.exists():
        return
    for path in sorted(root.rglob("*"), reverse=True):
        try:
            path.chmod(mode)
        except OSError:
            pass
    try:
        root.chmod(mode)
    except OSError:
        pass


def _write_spec(root: Path, name: str, content: str) -> Path:
    spec_dir = root / name
    spec_dir.mkdir(parents=True)
    (spec_dir / "SPEC-MOC.md").write_text(textwrap.dedent(content), encoding="utf-8")
    return spec_dir


def make_gated_spec(root: Path, name: str) -> Path:
    spec_dir = _write_spec(
        root,
        name,
        f"""\
            ---
            up: "[parent](roadmap.md)"
            related: []
            status: ""
            rank:
            spec_id: "{name}"
            structureVersion: 1
            ---
            # {name}
            """,
    )
    (spec_dir / "roadmap.md").write_text("# roadmap\n", encoding="utf-8")
    return spec_dir


def make_dangling_spec(root: Path, name: str) -> Path:
    return _write_spec(
        root,
        name,
        f"""\
            ---
            up: "[parent](no-such-roadmap.md)"
            related: []
            status: ""
            rank:
            spec_id: "{name}"
            structureVersion: 1
            ---
            # {name} - dangling up link
            """,
    )


def make_orphan_violation_spec(root: Path, name: str) -> Path:
    return _write_spec(
        root,
        name,
        f"""\
            ---
            related: []
            status: ""
            rank:
            spec_id: "{name}"
            structureVersion: 1
            ---
            # {name} - missing up
            """,
    )


def make_legacy_spec(root: Path, name: str) -> Path:
    return _write_spec(
        root,
        name,
        f"""\
            ---
            up: "[parent](does-not-exist.md)"
            spec_id: "{name}"
            ---
            # {name} - legacy, no version gate

            A dangling [body link](also-missing.md) and a [[wikilink]] are ignored
            because this spec is not version-gated.
            """,
    )


def force_stale_mode_b_internal_error() -> subprocess.CompletedProcess[str]:
    code = textwrap.dedent(
        f"""\
        import importlib.util
        import pathlib
        import sys

        module_path = pathlib.Path({str(STALE)!r})
        spec = importlib.util.spec_from_file_location("validate_moc_stale_index_forced", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        def boom(*_args, **_kwargs):
            raise RuntimeError("forced run_counted failure")

        module.run_counted = boom
        raise SystemExit(module.main())
        """
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )


def force_orphan_scan_root_internal_error(root: Path) -> subprocess.CompletedProcess[str]:
    code = textwrap.dedent(
        f"""\
        import importlib.util
        import pathlib
        import sys

        module_path = pathlib.Path({str(ORPHAN)!r})
        scan_root = pathlib.Path({str(root)!r})
        spec = importlib.util.spec_from_file_location("validate_moc_orphan_forced", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        def boom(_root):
            raise PermissionError("forced unreadable root")

        module.scan_root = boom
        raise SystemExit(module.main([str(scan_root)]))
        """
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )


def force_stale_scan_root_internal_error(root: Path) -> subprocess.CompletedProcess[str]:
    code = textwrap.dedent(
        f"""\
        import importlib.util
        import pathlib
        import sys

        module_path = pathlib.Path({str(STALE)!r})
        scan_root = pathlib.Path({str(root)!r})
        spec = importlib.util.spec_from_file_location("validate_moc_stale_index_forced_root", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        def boom(_root, *, emit=False):
            raise PermissionError("forced unreadable root")

        module.scan_root = boom
        sys.argv = [str(module_path), str(scan_root)]
        raise SystemExit(module.main())
        """
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )


def force_unreadable_marker(script: Path, root: Path) -> subprocess.CompletedProcess[str]:
    if script == ORPHAN:
        entrypoint = "module.main([str(scan_root)])"
        argv_patch = ""
    else:
        entrypoint = "module.main()"
        argv_patch = "        sys.argv = [str(module_path), str(scan_root)]\n"
    code = textwrap.dedent(
        f"""\
        import importlib.util
        import os
        import pathlib
        import sys

        module_path = pathlib.Path({str(script)!r})
        scan_root = pathlib.Path({str(root)!r})
        marker = scan_root / "unreadable-spec" / "SPEC-MOC.md"
        spec = importlib.util.spec_from_file_location("forced_unreadable_marker", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        real_access = module.os.access

        def fake_access(path, mode):
            candidate = pathlib.Path(path)
            if candidate == marker:
                return False
            return real_access(path, mode)

        module.os.access = fake_access
{argv_patch}        raise SystemExit({entrypoint})
        """
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )


class MocLintExitCodeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.work = Path(self._tmp.name)

    def tearDown(self) -> None:
        chmod_tree(self.work, stat.S_IRWXU)
        self._tmp.cleanup()
        if STALE_RUNTIME_SYMLINK.exists() or STALE_RUNTIME_SYMLINK.is_symlink():
            STALE_RUNTIME_SYMLINK.unlink()

    def test_moc_lint_exit_codes(self) -> None:
        root_a = self.work / "a"
        make_gated_spec(root_a, "gated-spec")

        unreadable_root_orphan = self.work / "internal-orphan"
        unreadable_root_orphan.mkdir()
        with self.subTest(msg="orphan: forced unreadable scan root -> exit 2"):
            result = force_orphan_scan_root_internal_error(unreadable_root_orphan)
            self.assertEqual(result.returncode, 2, result.stderr)
        with self.subTest(msg="orphan: internal-error exit (2) is distinct from content-violation exit (1)"):
            self.assertNotEqual(result.returncode, 1)

        unreadable_root_stale = self.work / "internal-stale"
        unreadable_root_stale.mkdir()
        with self.subTest(msg="stale-index: forced unreadable scan root -> exit 2"):
            result = force_stale_scan_root_internal_error(unreadable_root_stale)
            self.assertEqual(result.returncode, 2, result.stderr)
        with self.subTest(msg="stale-index: internal-error exit (2) is distinct from content-violation exit (1)"):
            self.assertNotEqual(result.returncode, 1)

        root_b = self.work / "b"
        make_gated_spec(root_b, "unreadable-spec")

        with self.subTest(msg="orphan: unreadable marker -> exit 0 (no content violation)"):
            result = force_unreadable_marker(ORPHAN, root_b)
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.subTest(msg="orphan: unreadable marker -> stderr carries a warning"):
            self.assertIn("unreadable marker", result.stderr)
        with self.subTest(msg="orphan: unreadable marker -> no VIOLATION on stdout"):
            self.assertNotIn("VIOLATION", result.stdout)

        with self.subTest(msg="stale-index: unreadable marker -> exit 0 (no content violation)"):
            result = force_unreadable_marker(STALE, root_b)
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.subTest(msg="stale-index: unreadable marker -> stderr carries a warning"):
            self.assertIn("unreadable marker", result.stderr)
        with self.subTest(msg="stale-index: unreadable marker -> no VIOLATION on stdout"):
            self.assertNotIn("VIOLATION", result.stdout)

        nonexistent = self.work / "does-not-exist-root"
        with self.subTest(msg="orphan: nonexistent scan root -> exit 0"):
            self.assertEqual(run_lint(ORPHAN, nonexistent).returncode, 0)
        with self.subTest(msg="stale-index: nonexistent scan root -> exit 0"):
            self.assertEqual(run_lint(STALE, nonexistent).returncode, 0)

        empty_root = self.work / "empty"
        empty_root.mkdir()
        with self.subTest(msg="orphan: empty scan root -> exit 0"):
            self.assertEqual(run_lint(ORPHAN, empty_root).returncode, 0)
        with self.subTest(msg="stale-index: empty scan root -> exit 0"):
            self.assertEqual(run_lint(STALE, empty_root).returncode, 0)

        markerless_root = self.work / "markerless"
        (markerless_root / "spec-without-marker").mkdir(parents=True)
        (markerless_root / "spec-without-marker" / "README.md").write_text("# just a readme\n", encoding="utf-8")
        with self.subTest(msg="orphan: markerless tree (no SPEC-MOC.md) -> exit 0"):
            self.assertEqual(run_lint(ORPHAN, markerless_root).returncode, 0)
        with self.subTest(msg="stale-index: markerless tree (no SPEC-MOC.md) -> exit 0"):
            self.assertEqual(run_lint(STALE, markerless_root).returncode, 0)

        root_d = self.work / "d"
        make_legacy_spec(root_d, "legacy-spec")
        with self.subTest(msg="orphan: non-gated marker with broken body -> exit 0 (skipped before read)"):
            result = run_lint(ORPHAN, root_d)
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.subTest(msg="orphan: non-gated marker -> no VIOLATION emitted"):
            self.assertNotIn("VIOLATION", result.stdout)
        with self.subTest(msg="stale-index: non-gated marker with broken body -> exit 0 (skipped before read)"):
            result = run_lint(STALE, root_d)
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.subTest(msg="stale-index: non-gated marker -> no VIOLATION emitted"):
            self.assertNotIn("VIOLATION", result.stdout)

        root_e_orphan = self.work / "e-orphan"
        make_orphan_violation_spec(root_e_orphan, "orphan-missing-up")
        with self.subTest(msg="orphan: content violation -> exit 1"):
            result = run_lint(ORPHAN, root_e_orphan)
            self.assertEqual(result.returncode, 1, result.stderr)
        with self.subTest(msg="orphan: content violation -> path + rule on STDOUT"):
            self.assertIn("VIOLATION", result.stdout)
        with self.subTest(msg="orphan: content violation -> offending path named on STDOUT"):
            self.assertIn("orphan-missing-up/SPEC-MOC.md", result.stdout)
        with self.subTest(msg="orphan: content violation -> nothing on STDERR (no internal-error line)"):
            self.assertNotIn("internal failure", result.stderr)

        root_e_stale = self.work / "e-stale"
        make_dangling_spec(root_e_stale, "stale-dangling")
        with self.subTest(msg="stale-index: content violation -> exit 1"):
            result = run_lint(STALE, root_e_stale)
            self.assertEqual(result.returncode, 1, result.stderr)
        with self.subTest(msg="stale-index: content violation -> path + rule on STDOUT"):
            self.assertIn("VIOLATION", result.stdout)
        with self.subTest(msg="stale-index: content violation -> the unresolved link named on STDOUT"):
            self.assertIn("no-such-roadmap.md", result.stdout)
        with self.subTest(msg="stale-index: content violation -> nothing on STDERR (no internal-error line)"):
            self.assertNotIn("internal failure", result.stderr)

        root_e_interr_orphan = self.work / "e-interr-orphan"
        root_e_interr_orphan.mkdir()
        with self.subTest(msg="orphan: internal error -> exit 2 (not 1)"):
            result = force_orphan_scan_root_internal_error(root_e_interr_orphan)
            self.assertEqual(result.returncode, 2, result.stderr)
        with self.subTest(msg="orphan: internal error -> message on STDERR"):
            self.assertIn("internal failure", result.stderr)
        with self.subTest(msg="orphan: internal error -> NO VIOLATION on STDOUT (classes not conflated)"):
            self.assertNotIn("VIOLATION", result.stdout)

        root_e_interr_stale = self.work / "e-interr-stale"
        root_e_interr_stale.mkdir()
        with self.subTest(msg="stale-index: internal error -> exit 2 (not 1)"):
            result = force_stale_scan_root_internal_error(root_e_interr_stale)
            self.assertEqual(result.returncode, 2, result.stderr)
        with self.subTest(msg="stale-index: internal error -> message on STDERR"):
            self.assertIn("internal failure", result.stderr)
        with self.subTest(msg="stale-index: internal error -> NO VIOLATION on STDOUT (classes not conflated)"):
            self.assertNotIn("VIOLATION", result.stdout)

        if STALE_RUNTIME_SYMLINK.exists() or STALE_RUNTIME_SYMLINK.is_symlink():
            STALE_RUNTIME_SYMLINK.unlink()
        with self.subTest(msg="stale-index: Mode-B internal error (no arg) -> exit 2"):
            result = force_stale_mode_b_internal_error()
            self.assertEqual(result.returncode, 2, result.stderr)
        with self.subTest(msg="stale-index: Mode-B internal error -> runtime broken symlink cleaned up (tree left clean)"):
            self.assertFalse(STALE_RUNTIME_SYMLINK.is_symlink())


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MocLintExitCodeTests)
    return run_counted(suite, label="test-moc-lint-exit-codes")


if __name__ == "__main__":
    raise SystemExit(main())
