#!/usr/bin/env python3
"""Curated install verification rejects incomplete or redirected installation evidence."""

from __future__ import annotations

import json
import io
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from itertools import product
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tests" / "speckit-pro" / "lib"))
from script_loader import load_script  # noqa: E402
from test_result import run_counted  # noqa: E402

check = load_script("curated_install_check", REPO_ROOT / "tests/speckit-pro/run-curated-install-check.py")
ENTRIES = json.loads(check.CURATED_SET.read_text(encoding="utf-8"))["entries"]
EXTENSIONS = [entry for entry in ENTRIES if entry["kind"] == "extension"]


def create_artifact(target, shape):
    """Create the actual filesystem object used by an adversarial case."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if shape == "file":
        target.write_text("artifact", encoding="utf-8")
        return
    if shape == "directory":
        target.mkdir()
        return
    source = target.parent / "source"
    if shape == "empty-directory-link":
        source.mkdir()
    if shape in ("symlink", "hard-link"):
        source.write_text("artifact", encoding="utf-8")
    if shape == "hard-link":
        os.link(source, target)
        return
    target.symlink_to(source, target_is_directory=True)


class CuratedInstallCheckTests(unittest.TestCase):
    def check_result(self, entry, project, code=1, output=check.TRUST_PROMPT):
        parent = project / ".specify"
        if not parent.exists() and not parent.is_symlink():
            parent.mkdir()
        result = subprocess.CompletedProcess([], code, output, "")
        with mock.patch.object(check, "specify", return_value=result), mock.patch.object(
            check, "archive_declares_id", return_value=True
        ):
            return check.check_entry(entry, project)

    def test_zero_exit_is_not_a_verified_noninteractive_abort(self):
        for entry in EXTENSIONS:
            with self.subTest(entry=entry["id"]), tempfile.TemporaryDirectory() as raw:
                self.assertTrue(self.check_result(entry, Path(raw), code=0))

    def test_signal_exit_is_not_a_verified_noninteractive_abort(self):
        for entry in EXTENSIONS:
            for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGKILL):
                with self.subTest(entry=entry["id"], signum=signum), tempfile.TemporaryDirectory() as raw:
                    self.assertTrue(self.check_result(entry, Path(raw), code=-signum))

    def test_partial_sibling_artifacts_are_not_an_empty_installation(self):
        for entry in EXTENSIONS:
            for shape in ("file", "directory", "renamed-target"):
                with self.subTest(entry=entry["id"], shape=shape), tempfile.TemporaryDirectory() as raw:
                    project = Path(raw)
                    registry = project / ".specify/extensions"
                    registry.mkdir(parents=True)
                    target = registry / (entry["id"] + ".partial")
                    if shape == "file":
                        target.write_text("partial", encoding="utf-8")
                    elif shape == "directory":
                        target.mkdir()
                    else:
                        installed = registry / entry["id"]
                        installed.mkdir()
                        installed.rename(target)
                    self.assertTrue(self.check_result(entry, project))

    def test_dangling_exact_target_is_not_absent(self):
        for entry in EXTENSIONS:
            with self.subTest(entry=entry["id"]), tempfile.TemporaryDirectory() as raw:
                project = Path(raw)
                registry = project / ".specify/extensions"
                registry.mkdir(parents=True)
                (registry / entry["id"]).symlink_to("missing")
                self.assertTrue(self.check_result(entry, project))

    def test_exact_and_sibling_links_and_hard_links_are_artifacts(self):
        shapes = ("directory", "file", "symlink", "dangling-link", "hard-link")
        for entry, exact, shape in product(EXTENSIONS, (True, False), shapes):
            with self.subTest(entry=entry["id"], exact=exact, shape=shape), tempfile.TemporaryDirectory() as raw:
                project = Path(raw)
                name = entry["id"] if exact else ".partial"
                create_artifact(project / ".specify/extensions" / name, shape)
                self.assertTrue(self.check_result(entry, project))

    def test_registry_and_parent_redirects_cannot_prove_absence(self):
        components = (".specify", ".specify/extensions")
        shapes = ("file", "empty-directory-link", "dangling-link")
        for entry, component, shape in product(EXTENSIONS, components, shapes):
            with self.subTest(entry=entry["id"], component=component, shape=shape), tempfile.TemporaryDirectory() as raw:
                project = Path(raw)
                create_artifact(project / component, shape)
                self.assertTrue(self.check_result(entry, project))

    def test_inspection_errors_are_not_absence(self):
        for entry in EXTENSIONS:
            for error in (PermissionError, OSError):
                with self.subTest(entry=entry["id"], error=error.__name__), tempfile.TemporaryDirectory() as raw:
                    project = Path(raw)
                    (project / ".specify/extensions").mkdir(parents=True)
                    with mock.patch.object(check.os, "listdir", side_effect=error("cannot inspect")):
                        self.assertTrue(self.check_result(entry, project))

    def test_normal_abort_with_absent_or_empty_registry_passes(self):
        for entry in EXTENSIONS:
            for state in ("absent", "empty"):
                with self.subTest(entry=entry["id"], state=state), tempfile.TemporaryDirectory() as raw:
                    project = Path(raw)
                    (project / ".specify").mkdir()
                    if state == "empty":
                        (project / ".specify/extensions").mkdir()
                    self.assertEqual(self.check_result(entry, project), [])

    def test_prompt_discovery_refusal_and_archive_identity_still_fail_closed(self):
        for entry in EXTENSIONS:
            with self.subTest(entry=entry["id"]), tempfile.TemporaryDirectory() as raw:
                project = Path(raw)
                self.assertTrue(self.check_result(entry, project, output=""))
                self.assertTrue(self.check_result(entry, project, output=check.TRUST_PROMPT + check.DISCOVERY_ONLY))
                with mock.patch.object(check, "specify", return_value=subprocess.CompletedProcess([], 1, check.TRUST_PROMPT, "")), mock.patch.object(
                    check, "archive_declares_id", return_value=False
                ):
                    self.assertTrue(check.check_entry(entry, project))

    def test_main_reports_each_invalid_extension_as_failed(self):
        def setup(project):
            (project / ".specify").mkdir()
            return []

        def specify(args, project):
            if args[0] == "preset":
                (project / ".specify/presets" / args[2]).mkdir(parents=True)
            return subprocess.CompletedProcess([], 0, check.TRUST_PROMPT, "")

        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(check, "fresh_project", side_effect=setup), mock.patch.object(
            check, "specify", side_effect=specify
        ), mock.patch.object(check, "archive_declares_id", return_value=True), redirect_stdout(stdout), redirect_stderr(stderr):
            status = check.main([])
        self.assertEqual(status, 1)
        self.assertIn("1/6 passed", stdout.getvalue())
        for entry in EXTENSIONS:
            self.assertIn(f"FAIL extension {entry['id']}:", stderr.getvalue())

    def test_preset_requires_a_real_directory_not_any_resolving_path(self):
        entry = next(entry for entry in ENTRIES if entry["kind"] == "preset")
        for shape in ("file", "empty-directory-link", "dangling-link"):
            with self.subTest(shape=shape), tempfile.TemporaryDirectory() as raw:
                project = Path(raw)
                create_artifact(project / ".specify/presets" / entry["id"], shape)
                self.assertTrue(self.check_result(entry, project, code=0))

    def test_preset_success_requires_zero_exit_and_unredirected_parents(self):
        entry = next(entry for entry in ENTRIES if entry["kind"] == "preset")
        for code in (0, 1, -signal.SIGTERM):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as raw:
                project = Path(raw)
                (project / ".specify/presets" / entry["id"]).mkdir(parents=True)
                failures = self.check_result(entry, project, code=code)
                self.assertEqual(bool(failures), code != 0)
        for component in (".specify", ".specify/presets"):
            with self.subTest(component=component), tempfile.TemporaryDirectory() as raw:
                project = Path(raw)
                target = project / component
                target.parent.mkdir(parents=True, exist_ok=True)
                source = project / "redirect"
                suffix = "presets" if component == ".specify" else "."
                (source / suffix / entry["id"]).mkdir(parents=True)
                target.symlink_to(source, target_is_directory=True)
                self.assertTrue(self.check_result(entry, project, code=0))


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-curated-install-check"))
