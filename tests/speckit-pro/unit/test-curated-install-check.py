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
import unittest.mock as mock

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

    def test_normal_abort_with_absent_or_empty_registry_has_no_refusal_failures(self):
        for entry in EXTENSIONS:
            for state in ("absent", "empty"):
                with self.scenario(entry=entry["id"], state=state) as project:
                    (project / ".specify").mkdir()
                    if state == "empty":
                        (project / ".specify/extensions").mkdir()
                    self.assertEqual(self.check_result(entry, project), [])


class CuratedInstallWorkflowTests(CuratedInstallCase):
    def test_main_reports_missing_cli_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as raw:
            result = subprocess.run(
                [sys.executable, str(check.__file__)], cwd=REPO_ROOT,
                env={**os.environ, "PATH": raw}, capture_output=True, text=True,
                timeout=30, shell=False, check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stderr,
            f"FAIL specify is missing against the pinned {check.spec_kit_pin.PINNED_VERSION}\n",
        )
        self.assertIn("run-curated-install-check: 0/6 passed", result.stdout)

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


class RegistryMutationTests(CuratedInstallCase):
    def test_in_place_artifact_creation_during_enumeration_is_not_absence(self):
        real_listdir = os.listdir
        for entry in EXTENSIONS:
            with self.scenario(entry=entry["id"]) as project:
                registry = project / ".specify/extensions"
                registry.mkdir(parents=True)

                def mutate(descriptor):
                    names = real_listdir(descriptor)
                    (registry / (entry["id"] + ".partial")).write_text("artifact", encoding="utf-8")
                    return names

                with mock.patch.object(check.os, "listdir", side_effect=mutate):
                    self.assertTrue(self.check_result(entry, project))


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


class RegistryDescriptorTests(CuratedInstallCase):
    """Every descriptor registry_entries opens is closed on every exit path."""

    @staticmethod
    def open_descriptors():
        return len(os.listdir("/dev/fd"))

    def test_inspection_closes_every_descriptor_it_opens(self):
        real_listdir = os.listdir
        extension = next(entry for entry in ENTRIES if entry["kind"] == "extension")
        preset = next(entry for entry in ENTRIES if entry["kind"] == "preset")
        for case in ("missing-specify", "missing-registry", "listing", "mutated", "failed-inspection"):
            with self.scenario(case=case) as project:
                kind, entry_id = extension["kind"], None
                if case != "missing-specify":
                    (project / ".specify").mkdir()
                if case not in ("missing-registry", "missing-specify"):
                    (project / check.REGISTRY_DIRS[kind]).mkdir(parents=True)
                if case == "mutated":
                    kind, entry_id = preset["kind"], preset["id"]
                    (project / check.REGISTRY_DIRS[kind] / entry_id).mkdir(parents=True)
                before = self.open_descriptors()
                if case == "mutated":
                    def mutate(descriptor):
                        (project / ".specify").rename(project / ".specify-old")
                        return real_listdir(descriptor)

                    with mock.patch.object(check.os, "listdir", side_effect=mutate):
                        self.assertIsNone(check.registry_entries(project, kind, entry_id))
                elif case == "failed-inspection":
                    with mock.patch.object(check.os, "listdir", side_effect=OSError("cannot list")):
                        self.assertIsNone(check.registry_entries(project, kind, entry_id))
                else:
                    check.registry_entries(project, kind, entry_id)
                self.assertEqual(self.open_descriptors(), before)


class CompletedInstallTests(CuratedInstallCase):
    """Neither an aborted install nor the legacy opt-in supplies owner acceptance."""

    def run_main(self, args=(), *, init_exit=0, register=True, preset_ok=True):
        installs = []

        def specify(argv, project):
            if argv[:1] == ["preset"]:
                if preset_ok:
                    (project / ".specify/presets" / argv[2]).mkdir(parents=True)
                return subprocess.CompletedProcess([], 0 if preset_ok else 1, "", "")
            if argv[:1] == ["extension"]:
                return subprocess.CompletedProcess([], 1, check.TRUST_PROMPT, "")
            installs.append(argv)
            if register:
                extension = argv[argv.index("--extension") + 1]
                entry = next(entry for entry in EXTENSIONS if entry["archive_url"] == extension)
                (project / ".specify/extensions" / entry["id"]).mkdir(parents=True)
            return subprocess.CompletedProcess([], init_exit, "", "")

        def setup(project):
            (project / ".specify").mkdir(exist_ok=True)
            return []

        def init_project(project, extra=()):
            (project / ".specify").mkdir(exist_ok=True)
            if not extra:
                return []
            return [] if specify(["init", "--here", *extra], project).returncode == 0 else ["setup failed"]

        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(check, "fresh_project", side_effect=setup), mock.patch.object(
            check, "init_project", side_effect=init_project
        ), mock.patch.object(check, "specify", side_effect=specify), mock.patch.object(
            check, "archive_declares_id", return_value=True
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            status = check.main(list(args))
        return status, stdout.getvalue(), stderr.getvalue(), installs

    def test_default_run_reports_every_extension_unproven_and_never_zero(self):
        status, stdout, stderr, installs = self.run_main()
        self.assertEqual(status, 2)
        self.assertIn("1/6 passed", stdout)
        self.assertIn("5 unproven", stdout)
        for entry in EXTENSIONS:
            self.assertIn(f"UNPROVEN extension {entry['id']}: needs operator confirmation", stderr)
        self.assertEqual(installs, [])

    def test_legacy_opt_in_fails_closed_without_attempting_installs(self):
        status, stdout, stderr, installs = self.run_main(["--trust-pinned-archives"])
        self.assertEqual(status, 1)
        self.assertIn("1/6 passed", stdout)
        for entry in EXTENSIONS:
            self.assertIn(f"FAIL extension {entry['id']}: completed install is unproven; owner-run acceptance is required", stderr)
        self.assertEqual(installs, [])

    def test_opted_in_run_fails_when_the_install_is_not_registered(self):
        for label, options in (("unregistered", {"register": False}), ("nonzero", {"init_exit": 1})):
            with self.subTest(case=label):
                status, stdout, stderr, _ = self.run_main(["--trust-pinned-archives"], **options)
                self.assertEqual(status, 1)
                self.assertIn("1/6 passed", stdout)
                for entry in EXTENSIONS:
                    self.assertIn(f"FAIL extension {entry['id']}:", stderr)

    def test_a_failed_preset_is_a_failure_not_unproven(self):
        status, _, stderr, _ = self.run_main(preset_ok=False)
        self.assertEqual(status, 1)
        self.assertIn("FAIL preset", stderr)


class CompletedInstallEvidenceTests(CuratedInstallCase):
    """A successful init and leftover artifacts cannot certify a completed install."""

    def assert_completion_unproven(self, variant):
        for entry in EXTENSIONS:
            with self.scenario(entry=entry["id"], variant=variant) as project:
                target = project / ".specify/extensions" / entry["id"]
                target.mkdir(parents=True)
                registry = target.parent / ".registry"
                data = {"extensions": {entry["id"]: {"enabled": True}}}
                if variant == "empty-mapping":
                    data["extensions"] = {}
                elif variant == "different-id":
                    data["extensions"] = {"different-extension": {"enabled": True}}
                elif variant == "disabled":
                    data["extensions"][entry["id"]]["enabled"] = False
                if variant != "absent-registry":
                    registry.write_text("{" if variant == "malformed-registry" else json.dumps(data), encoding="utf-8")
                if variant != "missing-manifest":
                    declared = "different-extension" if variant == "wrong-manifest-id" else entry["id"]
                    (target / "extension.yml").write_text(f'extension:\n  id: {declared}\n', encoding="utf-8")
                # Model init's successful exit without trusting its artifacts. No CLI runs.
                with mock.patch.object(check.tempfile, "TemporaryDirectory") as temporary, mock.patch.object(
                    check, "init_project", return_value=[]
                ):
                    temporary.return_value.__enter__.return_value = str(project)
                    self.assertEqual(check.check_completed_install(entry), [
                        f"extension {entry['id']}: completed install is unproven; owner-run acceptance is required"
                    ])

    def test_absent_registry_cannot_certify_completion(self):
        self.assert_completion_unproven("absent-registry")

    def test_malformed_registry_cannot_certify_completion(self):
        self.assert_completion_unproven("malformed-registry")

    def test_empty_registry_mapping_cannot_certify_completion(self):
        self.assert_completion_unproven("empty-mapping")

    def test_different_registry_id_cannot_certify_completion(self):
        self.assert_completion_unproven("different-id")

    def test_disabled_registry_entry_cannot_certify_completion(self):
        self.assert_completion_unproven("disabled")

    def test_missing_manifest_cannot_certify_completion(self):
        self.assert_completion_unproven("missing-manifest")

    def test_wrong_manifest_id_cannot_certify_completion(self):
        self.assert_completion_unproven("wrong-manifest-id")

    def test_apparently_valid_artifacts_are_not_owner_acceptance(self):
        self.assert_completion_unproven("apparently-valid")

    def test_completion_check_never_attempts_an_install(self):
        for entry in EXTENSIONS:
            with self.subTest(entry=entry["id"]), mock.patch.object(check, "init_project", return_value=[]) as init, mock.patch.object(
                check, "specify"
            ) as specify:
                self.assertTrue(check.check_completed_install(entry))
                init.assert_not_called()
                specify.assert_not_called()


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
