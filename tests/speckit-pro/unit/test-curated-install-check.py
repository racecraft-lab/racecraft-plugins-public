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
from contextlib import contextmanager, redirect_stderr, redirect_stdout
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


class CuratedInstallCase(unittest.TestCase):
    @contextmanager
    def scenario(self, **variants):
        """Give each variant a fresh project and its own counted assertion."""
        with self.subTest(**variants), tempfile.TemporaryDirectory() as raw:
            yield Path(raw)

    def check_result(self, entry, project, code=1, output=check.TRUST_PROMPT):
        parent = project / ".specify"
        if not parent.exists() and not parent.is_symlink():
            parent.mkdir()
        result = subprocess.CompletedProcess([], code, output, "")
        with mock.patch.object(check, "specify", return_value=result), mock.patch.object(
            check, "archive_declares_id", return_value=True
        ):
            return check.check_entry(entry, project)

    def assert_artifact_rejected(self, entry, relative, shape):
        with self.scenario(entry=entry["id"], path=relative, shape=shape) as project:
            create_artifact(project / relative, shape)
            self.assertTrue(self.check_result(entry, project))


class ExtensionExitTests(CuratedInstallCase):
    def test_zero_exit_is_not_a_verified_noninteractive_abort(self):
        for entry in EXTENSIONS:
            with self.scenario(entry=entry["id"]) as project:
                self.assertTrue(self.check_result(entry, project, code=0))

    def test_signal_exit_is_not_a_verified_noninteractive_abort(self):
        for entry in EXTENSIONS:
            for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGKILL):
                with self.scenario(entry=entry["id"], signum=signum) as project:
                    self.assertTrue(self.check_result(entry, project, code=-signum))


class ExtensionArtifactTests(CuratedInstallCase):
    def test_partial_sibling_artifacts_are_not_an_empty_installation(self):
        for entry in EXTENSIONS:
            for shape in ("file", "directory", "renamed-target"):
                with self.scenario(entry=entry["id"], shape=shape) as project:
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
            with self.scenario(entry=entry["id"]) as project:
                registry = project / ".specify/extensions"
                registry.mkdir(parents=True)
                (registry / entry["id"]).symlink_to("missing")
                self.assertTrue(self.check_result(entry, project))

    def test_exact_and_sibling_links_and_hard_links_are_artifacts(self):
        shapes = ("directory", "file", "symlink", "dangling-link", "hard-link")
        for entry, exact, shape in product(EXTENSIONS, (True, False), shapes):
            name = entry["id"] if exact else ".partial"
            self.assert_artifact_rejected(entry, ".specify/extensions/" + name, shape)

    def test_registry_and_parent_redirects_cannot_prove_absence(self):
        components = (".specify", ".specify/extensions")
        shapes = ("file", "empty-directory-link", "dangling-link")
        for entry, component, shape in product(EXTENSIONS, components, shapes):
            self.assert_artifact_rejected(entry, component, shape)

    def test_inspection_errors_are_not_absence(self):
        for entry, operation, error in product(EXTENSIONS, ("listdir", "fstat"), (PermissionError, OSError)):
            with self.scenario(entry=entry["id"], operation=operation, error=error.__name__) as project:
                (project / ".specify/extensions").mkdir(parents=True)
                with mock.patch.object(check.os, operation, side_effect=error("cannot inspect")):
                    self.assertTrue(self.check_result(entry, project))

    def test_normal_abort_with_absent_or_empty_registry_passes(self):
        for entry in EXTENSIONS:
            for state in ("absent", "empty"):
                with self.scenario(entry=entry["id"], state=state) as project:
                    (project / ".specify").mkdir()
                    if state == "empty":
                        (project / ".specify/extensions").mkdir()
                    self.assertEqual(self.check_result(entry, project), [])


class CuratedInstallWorkflowTests(CuratedInstallCase):
    def test_prompt_discovery_refusal_and_archive_identity_still_fail_closed(self):
        for entry in EXTENSIONS:
            with self.scenario(entry=entry["id"]) as project:
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
            with self.scenario(shape=shape) as project:
                create_artifact(project / ".specify/presets" / entry["id"], shape)
                self.assertTrue(self.check_result(entry, project, code=0))

    def test_preset_success_requires_zero_exit_and_unredirected_parents(self):
        entry = next(entry for entry in ENTRIES if entry["kind"] == "preset")
        for code in (0, 1, -signal.SIGTERM):
            with self.scenario(code=code) as project:
                (project / ".specify/presets" / entry["id"]).mkdir(parents=True)
                failures = self.check_result(entry, project, code=code)
                self.assertEqual(bool(failures), code != 0)
        for component in (".specify", ".specify/presets"):
            with self.scenario(component=component) as project:
                target = project / component
                target.parent.mkdir(parents=True, exist_ok=True)
                source = project / "redirect"
                suffix = "presets" if component == ".specify" else "."
                (source / suffix / entry["id"]).mkdir(parents=True)
                target.symlink_to(source, target_is_directory=True)
                self.assertTrue(self.check_result(entry, project, code=0))


class RegistryBindingTests(CuratedInstallCase):
    def test_registry_and_parent_swaps_after_open_cannot_hide_artifacts(self):
        real_listdir = os.listdir
        for entry, component, replacement in product(
            ENTRIES, ("parent", "registry"), ("directory", "symlink")
        ):
            with self.scenario(entry=entry["id"], component=component, replacement=replacement) as project:
                registry = project / check.REGISTRY_DIRS[entry["kind"]]
                registry.mkdir(parents=True)
                if entry["kind"] == "preset":
                    (registry / entry["id"]).mkdir()

                def swap(descriptor):
                    target = project / ".specify" if component == "parent" else registry
                    target.rename(target.with_name(target.name + "-old"))
                    source = project / "replacement"
                    source.mkdir()
                    if replacement == "symlink":
                        target.symlink_to(source, target_is_directory=True)
                    else:
                        source.rename(target)
                    registry.mkdir(exist_ok=True)
                    (registry / (entry["id"] + ".partial")).write_text("artifact", encoding="utf-8")
                    return real_listdir(descriptor)

                with mock.patch.object(check.os, "listdir", side_effect=swap):
                    self.assertTrue(self.check_result(entry, project, code=0 if entry["kind"] == "preset" else 1))

    def test_preset_target_swap_cannot_preserve_success(self):
        entry = next(entry for entry in ENTRIES if entry["kind"] == "preset")
        real_listdir = os.listdir
        for shape in ("file", "directory", "empty-directory-link"):
            with self.scenario(shape=shape) as project:
                target = project / ".specify/presets" / entry["id"]
                target.mkdir(parents=True)

                def swap(descriptor):
                    target.rename(target.with_name(target.name + "-old"))
                    create_artifact(target, shape)
                    return real_listdir(descriptor)

                with mock.patch.object(check.os, "listdir", side_effect=swap):
                    self.assertTrue(self.check_result(entry, project, code=0))

    def test_missing_registry_cannot_hide_a_parent_swap(self):
        real_open = os.open
        for entry in EXTENSIONS:
            with self.scenario(entry=entry["id"]) as project:
                (project / ".specify").mkdir()

                def swap(path, flags, **kwargs):
                    descriptor = real_open(path, flags, **kwargs)
                    if path == project / ".specify":
                        path.rename(project / ".specify-old")
                        registry = project / ".specify/extensions"
                        registry.mkdir(parents=True)
                        (registry / ".partial").write_text("artifact", encoding="utf-8")
                    return descriptor

                with mock.patch.object(check.os, "open", side_effect=swap):
                    self.assertTrue(self.check_result(entry, project))


class CuratedRosterTests(CuratedInstallCase):
    def test_empty_roster_cannot_pass_without_checking_any_entry(self):
        with self.scenario(roster="empty") as project:
            roster = project / "curated.json"
            roster.write_text('{"entries": []}', encoding="utf-8")
            with mock.patch.object(check, "fresh_project", return_value=[]), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(check.main(["--curated-set", str(roster)]), 1)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-curated-install-check"))
