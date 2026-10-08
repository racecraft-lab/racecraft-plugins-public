#!/usr/bin/env python3
"""Curated install verification rejects incomplete or redirected installation evidence."""

from __future__ import annotations

import ast
import errno
import hashlib
import importlib.util
import json
import io
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from itertools import product
from datetime import datetime, timezone
from pathlib import Path
import unittest.mock as mock

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tests" / "speckit-pro" / "lib"))
from script_loader import load_script  # noqa: E402
from test_result import run_counted  # noqa: E402
from isolated_child import BASE_KEYS, run_python  # noqa: E402
from descriptor_observer import record_open_descriptors  # noqa: E402

VERIFIER = REPO_ROOT / "tests/speckit-pro/run-curated-install-check.py"
check = load_script("curated_install_check", VERIFIER)
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


def create_completion_evidence(entry, project, variant):
    """Materialize successful-init leftovers without treating them as acceptance."""
    target = project / check.REGISTRY_DIRS[entry["kind"]] / entry["id"]
    target.mkdir(parents=True)
    mapping = entry["kind"] + "s"
    records = {
        "empty-mapping": {},
        "different-id": {"different-entry": {"enabled": True}},
        "disabled": {entry["id"]: {"enabled": False}},
    }
    data = {mapping: records.get(variant, {entry["id"]: {"enabled": True}})}
    if variant != "absent-registry":
        (target.parent / ".registry").write_text("{" if variant == "malformed-registry" else json.dumps(data), encoding="utf-8")
    if variant != "missing-manifest":
        declared = "different-entry" if variant == "wrong-manifest-id" else entry["id"]
        (target / check.MANIFEST_NAMES[entry["kind"]]).write_text(f'{entry["kind"]}:\n  id: {declared}\n', encoding="utf-8")


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
    def test_late_preset_replacement_cannot_certify_completion(self):
        entry = next(entry for entry in ENTRIES if entry["kind"] == "preset")
        real_stat = os.stat
        for shape, trust in product(("file", "directory", "empty-directory-link"), (False, True)):
            with self.scenario(shape=shape, trust=trust) as project:
                target = project / ".specify/presets" / entry["id"]
                target.mkdir(parents=True)

                def replace_after_snapshot(path, *args, **kwargs):
                    info = real_stat(path, *args, **kwargs)
                    if path == project / ".specify":
                        target.rename(target.parent / "previous")
                        create_artifact(target, shape)
                    return info

                with mock.patch.object(check, "specify", return_value=subprocess.CompletedProcess([], 0, "", "")), mock.patch.object(
                    check.os, "stat", side_effect=replace_after_snapshot
                ):
                    self.assertEqual(check.entry_result(entry, project, trust), ("unproven", []))

    def test_preset_artifacts_are_unproven_not_completed(self):
        entry = next(entry for entry in ENTRIES if entry["kind"] == "preset")
        variants = ("absent-registry", "malformed-registry", "empty-mapping", "different-id", "disabled", "missing-manifest", "wrong-manifest-id")
        for variant, trust in product(variants, (False, True)):
            with self.scenario(variant=variant, trust=trust) as project:
                create_completion_evidence(entry, project, variant)
                with mock.patch.object(check, "specify", return_value=subprocess.CompletedProcess([], 0, "", "")):
                    self.assertEqual(check.entry_result(entry, project, trust), ("unproven", []))

    def test_main_reports_missing_cli_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as raw:
            result = run_python([str(check.__file__)], env_extra={"PATH": raw}, timeout=30)
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
        self.assertIn("0/6 passed", stdout.getvalue())
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

    def run_main(self, args=(), *, preset_ok=True):
        installs = []

        def specify(argv, project):
            if argv[:1] == ["preset"]:
                if preset_ok:
                    (project / ".specify/presets" / argv[2]).mkdir(parents=True)
                return subprocess.CompletedProcess([], 0 if preset_ok else 1, "", "")
            if argv[:1] == ["extension"]:
                return subprocess.CompletedProcess([], 1, check.TRUST_PROMPT, "")
            installs.append(argv)
            return subprocess.CompletedProcess([], 0, "", "")

        def setup(project):
            (project / ".specify").mkdir(exist_ok=True)
            return []

        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(check, "fresh_project", side_effect=setup), mock.patch.object(
            check, "specify", side_effect=specify
        ), mock.patch.object(
            check, "archive_declares_id", return_value=True
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            status = check.main(list(args))
        return status, stdout.getvalue(), stderr.getvalue(), installs

    def assert_no_completion_claim(self, status, stdout, installs, expected_status):
        self.assertEqual(status, expected_status)
        self.assertIn("0/6 passed", stdout)
        self.assertEqual(installs, [])

    def assert_probe_state(self, legacy):
        args, expected_status, prefix, message = (
            (["--trust-pinned-archives"], 1, "FAIL", "completed install is unproven; owner-run acceptance is required")
            if legacy else ([], 2, "UNPROVEN", "needs operator confirmation")
        )
        status, stdout, stderr, installs = self.run_main(args)
        self.assert_no_completion_claim(status, stdout, installs, expected_status)
        for entry in EXTENSIONS:
            self.assertIn(f"{prefix} extension {entry['id']}: {message}", stderr)
        self.assertIn("UNPROVEN preset claude-ask-questions: needs owner-run acceptance", stderr)
        if not legacy:
            self.assertIn("6 unproven", stdout)

    def test_default_run_reports_every_extension_unproven_and_never_zero(self):
        self.assert_probe_state(False)

    def test_legacy_opt_in_fails_closed_without_attempting_installs(self):
        self.assert_probe_state(True)

    def test_legacy_opt_in_never_uses_init_results(self):
        for result in ([], ["setup failed"]):
            with self.subTest(result=result), mock.patch.object(check, "init_project", return_value=result) as init:
                status, stdout, stderr, _ = self.run_main(["--trust-pinned-archives"])
                self.assertEqual(status, 1)
                self.assertIn("0/6 passed", stdout)
                for entry in EXTENSIONS:
                    self.assertIn(f"FAIL extension {entry['id']}:", stderr)
                init.assert_not_called()

    def test_a_failed_preset_is_a_failure_not_unproven(self):
        status, _, stderr, _ = self.run_main(preset_ok=False)
        self.assertEqual(status, 1)
        self.assertIn("FAIL preset", stderr)


class CompletedInstallEvidenceTests(CuratedInstallCase):
    """A successful init and leftover artifacts cannot certify a completed install."""

    def assert_completion_unproven(self, variant):
        for entry in EXTENSIONS:
            with self.scenario(entry=entry["id"], variant=variant) as project:
                create_completion_evidence(entry, project, variant)
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


HOSTILE_PYTHON_ENV = ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONSAFEPATH")
# Spec Kit v1.1.0 reads GITHUB_TOKEN/GH_TOKEN (authentication/github_http.py); its urllib openers
# (authentication/http.py build_opener) read the *_proxy family and OpenSSL's SSL_CERT_FILE/SSL_CERT_DIR.
PINNED_NETWORK_KEYS = ("GH_TOKEN", "GITHUB_TOKEN", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy",
                       "https_proxy", "no_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR")


class ChildEnvironmentTests(unittest.TestCase):
    """No child the check or its tests start inherits the parent's Python environment."""

    def test_inherited_pythonpath_cannot_forge_the_missing_cli_result(self):
        """A PYTHONPATH json.py that prints the expected missing-CLI result never runs."""
        with tempfile.TemporaryDirectory() as raw:
            marker = Path(raw) / "marker"
            stderr = f"FAIL specify is missing against the pinned {check.spec_kit_pin.PINNED_VERSION}\n"
            (Path(raw) / "json.py").write_text(
                f"import os, sys\nopen({str(marker)!r}, 'a').write('json')\n"
                f"sys.stderr.write({stderr!r})\nsys.stdout.write('run-curated-install-check: 0/6 passed\\n')\n"
                "sys.stdout.flush()\nsys.stderr.flush()\nos._exit(1)\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"PYTHONPATH": raw}):
                outcome = unittest.TextTestRunner(stream=io.StringIO()).run(
                    CuratedInstallWorkflowTests("test_main_reports_missing_cli_without_a_traceback"))
            self.assertFalse(marker.exists(), "inherited PYTHONPATH module executed")
            self.assertTrue(outcome.wasSuccessful(), outcome.failures + outcome.errors)

    def test_network_keys_are_exactly_those_the_pinned_cli_reads(self):
        """spec-kit v1.1.0 reads GitHub tokens itself; its urllib openers read the proxy and OpenSSL CA variables."""
        self.assertEqual(sorted(check.NETWORK_KEYS), sorted(PINNED_NETWORK_KEYS))

    def test_specify_and_git_children_get_exactly_the_minimal_environment(self):
        unconsumed = ("REQUESTS_CA_BUNDLE", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "ALL_PROXY",
                      "all_proxy", "UNRELATED_SECRET", "SPECKIT_CATALOG_URL")
        parent = {key: "/hostile" for key in (*HOSTILE_PYTHON_ENV, *unconsumed)}
        parent |= {key: "kept-" + key for key in (*BASE_KEYS, *PINNED_NETWORK_KEYS)}
        with (tempfile.TemporaryDirectory() as raw, mock.patch.dict(os.environ, parent, clear=True),
              mock.patch.object(check.subprocess, "run",
                                return_value=subprocess.CompletedProcess([], 1, "", "")) as run):
            check.specify(["--version"], Path(raw))
            check.init_project(Path(raw))
        self.assertEqual([call.args[0][0] for call in run.call_args_list], ["specify", "git"])
        expected = {"specify": {key: "kept-" + key for key in (*BASE_KEYS, *PINNED_NETWORK_KEYS)} | {"NO_COLOR": "1"},
                    "git": {key: "kept-" + key for key in BASE_KEYS}}
        for call in run.call_args_list:
            with self.subTest(child=call.args[0][0]):
                self.assertEqual(call.kwargs["env"], expected[call.args[0][0]])


# Spec Kit v1.1.0's canonical events (events/__init__.py L73-80); a test may make a fixture manifest declare one.
EVENTS = ("session_start", "pre_tool_use", "post_tool_use", "session_end", "user_prompt_submit", "stop")
EVENT_DECLARATIONS: dict[str, str] = {}


def yaml_scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value) if isinstance(value, int) else json.dumps(value)


def emit_list(items, pad, indent):
    lines = []
    for element in items:
        if isinstance(element, dict):
            first, *rest = emit_yaml(element, indent + 2)
            lines += [f"{pad}- {first.lstrip()}", *rest]
        else:
            lines.append(f"{pad}- {yaml_scalar(element)}")
    return lines


def emit_yaml(value, indent=0):
    """Block YAML in yaml.dump's layout (list items under a key at the key's indent)."""
    pad, lines = " " * indent, []
    for key, item in value.items():
        if isinstance(item, dict) and item:
            lines += [f"{pad}{key}:", *emit_yaml(item, indent + 2)]
        elif isinstance(item, list) and item:
            lines += [f"{pad}{key}:", *emit_list(item, pad, indent)]
        else:
            lines.append(f"{pad}{key}: " + ("{}" if item == {} else "[]" if item == [] else yaml_scalar(item)))
    return lines


def yaml_bytes(doc, tail=b""):
    """`doc` as block YAML, then `tail` (raw YAML appended after it)."""
    return "\n".join(emit_yaml(doc)).encode() + b"\n" + tail


def fixture_doc(entry):
    """A pinned manifest shaped like the curated ones: payload, aliases, hooks and a nested version."""
    entry_id, kind = entry["id"], entry["kind"]
    if kind == "preset":
        return {"schema_version": "1.0",
                "preset": {"id": entry_id, "name": entry_id, "version": "1.0.0", "description": "fixture"},
                "requires": {"speckit_version": ">=0.6.0"},
                "provides": {"templates": [{"type": "command", "name": name, "file": f"commands/{name}.md",
                                            "replaces": name} for name in ("speckit.clarify", "speckit.checklist")]}}
    command = f"speckit.{entry_id}.run"
    return {"schema_version": "1.0",
            "extension": {"id": entry_id, "name": entry_id, "version": "1.0.0", "description": "fixture"},
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {"commands": [{"name": command, "file": "commands/run.md", "aliases": [f"speckit.{entry_id}"]}],
                         "scripts": [{"name": "run.sh", "file": "scripts/bash/run.sh", "executable": True}],
                         "config": [{"name": f"{entry_id}-config.yml", "template": "config-template.yml"}]},
            "hooks": {"after_implement": {"command": command, "optional": True, "prompt": "Run it?",
                                          "description": "fixture hook", "condition": None}},
            "defaults": {"version": "2.0.0"}} | (
        {"events": {EVENT_DECLARATIONS[entry_id]: {"command": command, "matcher": "Bash", "timeout": 30}}}
        if entry_id in EVENT_DECLARATIONS else {})


def commands(doc, kind):
    """Each command name the manifest declares (aliases too) with its file."""
    if kind == "preset":
        return {item["name"]: item["file"] for item in doc["provides"]["templates"]}
    return {name: item["file"] for item in doc["provides"]["commands"] for name in [item["name"], *item["aliases"]]}


def fixture_archive(entry):
    """The pinned archive's files below its top directory."""
    doc = fixture_doc(entry)
    payload, _names = check.declared(doc, entry["kind"])
    return {check.MANIFEST_NAMES[entry["kind"]]: yaml_bytes(doc), "README.md": b"readme\n",
            **{path: f"payload {entry['id']} {path}\n".encode() for path in payload}}


PINNED_ARGS = check.install_args
HOOK_FIELDS = {"extension": "other", "command": "speckit.other.run", "enabled": False, "optional": False,
               "priority": 5, "prompt": "Altered?", "description": "altered", "condition": "env.X is set"}
DEFECTS = ("declined", "no-registry", "malformed-registry", "other-id", "disabled", "catalog-source",
           "registry-hash", "registry-version", "priority-999", "stale-timestamp", "manifest-differs",
           "manifest-symlink", "manifest-hardlink", "payload-missing", "payload-differs", "registered-empty",
           "skill-missing", "skill-foreign", "skill-body-source", "skill-no-frontmatter", "skill-no-metadata",
           "skill-top-level-source", "skill-duplicate-metadata", "skill-duplicate-source", "skill-unclosed")
EXTENSION_DEFECTS = ("not-listed", "duplicate-installed", "hooks-absent", *(f"hook-{field}" for field in HOOK_FIELDS))
EXIT_CODES = (1, 37, -signal.SIGTERM, -signal.SIGINT, -signal.SIGKILL)


def install_record(entry, doc, manifest, defect):
    """The registry entry v1.1.0 writes for a --from install (extensions/__init__.py L3128-3146,
    presets/_manager.py L416-424; installed_at from registry add(), L832-843), one field wrong for a defect."""
    names = list(commands(doc, entry["kind"]))
    record = {"version": "1.0.0", "source": "local", "manifest_hash": "sha256:" + hashlib.sha256(manifest).hexdigest(),
              "enabled": True, "priority": 10, "registered_commands": {"claude": names}, "registered_skills": [],
              "installed_at": datetime.now(timezone.utc).isoformat()}
    wrong = {"catalog-source": ("source", {"kind": "catalog", "catalog": "default"}), "disabled": ("enabled", False),
             "registry-hash": ("manifest_hash", "sha256:" + hashlib.sha256(b"other").hexdigest()),
             "registry-version": ("version", "2.0.0"), "priority-999": ("priority", 999),
             "stale-timestamp": ("installed_at", "2020-01-01T00:00:00+00:00"),
             "registered-empty": ("registered_commands", {})}
    if defect in wrong:
        record[wrong[defect][0]] = wrong[defect][1]
    return record


def register(base, kind, entry_id, record, defect):
    registry_path = base / ".registry"
    try:  # v1.1.0 _load (L763-791) starts fresh from an absent or malformed registry
        registry = json.loads(registry_path.read_text())
    except (FileNotFoundError, ValueError):
        registry = {"schema_version": "1.0", check.REGISTRY_KEYS[kind]: {}}
    if defect != "no-registry":
        registry[check.REGISTRY_KEYS[kind]]["other" if defect == "other-id" else entry_id] = record
    registry_path.write_text("{not json" if defect == "malformed-registry" else json.dumps(registry, indent=2))


def skill_text(entry, file, defect, first):
    """SKILL.md as v1.1.0 writes it (agents.py L425-490; `<kind>:<id>` from the extension and preset
    skill writers), or one ownership spoof: cr1274h High and Daybreak F1274-c0db0694."""
    own = f"{entry['id']}:{file}" if first else f"{entry['kind']}:{entry['id']}"
    head = "name: fixture\ndescription: 'Fixture: a command'\n"
    meta = "metadata:\n  author: fixture\n  source: {}\n".format
    spoof = f"\n# Skill\n\nsource: {own}\n"
    return {
        "skill-foreign": f"---\n{head}{meta('other:commands/run.md')}---\n\n# Skill\n",
        "skill-body-source": f"---\n{head}{meta('other:commands/run.md')}---\n{spoof}",
        "skill-no-frontmatter": f"# Skill\n{spoof}",
        "skill-no-metadata": f"---\n{head}---\n{spoof}",
        "skill-top-level-source": f"---\n{head}source: {own}\n{meta('other:commands/run.md')}---\n{spoof}",
        "skill-duplicate-metadata": f"---\n{head}{meta('other:commands/run.md')}{meta(own)}---\n",
        "skill-duplicate-source": f"---\n{head}{meta('other:commands/run.md')}  source: {own}\n---\n",
        "skill-unclosed": f"---\n{head}{meta(own)}\n# Skill\n",
    }.get(defect if first else None, f"---\n{head}{meta(own)}user-invocable: true\n---\n\n# Skill\n")


def write_skills(project, entry, doc, defect):
    """SKILL.md per command and alias in .claude/skills (agents.py L579-594, L929-1012)."""
    for index, (name, file) in enumerate(commands(doc, entry["kind"]).items()):
        if defect == "skill-missing" and index == 0:
            continue
        skill = project / ".claude" / "skills" / check.skill_name(name)
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(skill_text(entry, file, defect, index == 0), encoding="utf-8")


def write_configuration(project, entry, doc, defect):
    """extensions.yml as register_extension and register_hooks leave it (L5724-5741, L5817-5905)."""
    config_path = project / ".specify" / "extensions.yml"
    config = check.read_yaml(config_path.read_bytes()) if config_path.exists() else {"installed": [], "hooks": {}}
    if defect != "not-listed":
        config["installed"].append(entry["id"])
    for event, hooks in check.expected_hooks(doc, entry["id"]).items():
        if defect == "hooks-absent":
            continue
        if defect and defect.startswith("hook-"):
            hooks = [{**hook, defect[5:]: HOOK_FIELDS[defect[5:]]} for hook in hooks]
        config["hooks"].setdefault(event, []).extend(hooks)
    config_path.write_bytes(yaml_bytes(config, b"installed: []\n" if defect == "duplicate-installed" else b""))


def v110_install(project, entry, defect=None):
    """What Spec Kit v1.1.0 leaves after `<kind> add <id> --from <url>`, optionally missing one piece.

    The archive is copied to .specify/<kind>s/<id> (extensions/__init__.py L2544, L2992;
    presets/_manager.py L400-404) and registered in .specify/<kind>s/.registry (L747-750,
    presets/_registry.py L12-25); commands become skills in .claude/skills; an extension is listed
    and its hooks registered in .specify/extensions.yml.
    """
    if defect == "declined":
        return
    kind, entry_id = entry["kind"], entry["id"]
    files = fixture_archive(entry)
    doc = fixture_doc(entry)
    base = project / check.REGISTRY_DIRS[kind]
    home = base / entry_id
    for path, data in files.items():
        if defect == "payload-missing" and path == check.declared(doc, kind)[0][0]:
            continue
        target = home / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"tampered\n" if defect == "payload-differs" and path == check.declared(doc, kind)[0][0]
                           else data)
    manifest = files[check.MANIFEST_NAMES[kind]]
    target = home / check.MANIFEST_NAMES[kind]
    if defect == "manifest-differs":
        manifest = manifest + b"# altered after the pin\n"
        target.write_bytes(manifest)
    elif defect in ("manifest-symlink", "manifest-hardlink"):
        target.rename(base / f"{entry_id}.held")
        (target.symlink_to if defect == "manifest-symlink" else lambda source: os.link(source, target))(
            base / f"{entry_id}.held")
    register(base, kind, entry_id, install_record(entry, doc, manifest, defect), defect)
    write_skills(project, entry, doc, defect)
    if kind == "extension":
        write_configuration(project, entry, doc, defect)


def called_from_checker():
    """Whether the innermost non-mock caller is the checker, so attack hooks spare tempdir cleanup."""
    frame = sys._getframe(1)
    while frame is not None and frame.f_globals.get("__name__") in ("unittest.mock", __name__):
        frame = frame.f_back
    return frame is not None and frame.f_globals.get("__name__") == check.__name__


def run_acceptance(shape=None, **case):
    """Run --owner-acceptance against a fake v1.1.0 CLI; returns exit code, statuses, calls, setup mock, output.

    `case` may set defects ({id: defect}), interactive, archive (pinned_archive side effect),
    start_error (raised when specify starts), exit_code, planted (ids whose full evidence exists
    before their install), after_install(project, entry) and open_hook(real_open, holder) -> os.open.
    """
    calls, holder = [], []

    def setup(project):
        project = Path(project)
        holder.append(project)
        (project / ".specify").mkdir()  # what `specify init --integration claude` leaves, core skills included
        for core in ("speckit-clarify", "speckit-checklist", "speckit-implement"):
            (project / ".claude" / "skills" / core).mkdir(parents=True)
            (project / ".claude" / "skills" / core / "SKILL.md").write_text(
                f"---\nname: {core}\nmetadata:\n  source: templates/commands/{core}.md\n---\n", encoding="utf-8")
        for entry in ENTRIES:
            if entry["id"] in case.get("planted", ()):
                v110_install(project, entry)
        return []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        if case.get("start_error") is not None:
            raise case["start_error"]
        entry = next(entry for entry in ENTRIES if argv[1:4] == [entry["kind"], "add", entry["id"]])
        if argv[1:] != PINNED_ARGS(entry):
            return subprocess.CompletedProcess(argv, 1)  # v1.1.0 refuses a bare add as discovery-only
        v110_install(Path(kwargs["cwd"]), entry, case.get("defects", {}).get(entry["id"]))
        if case.get("after_install"):
            case["after_install"](Path(kwargs["cwd"]), entry)
        return subprocess.CompletedProcess(argv, case.get("exit_code", 0))

    def archive(url):
        return fixture_archive(next(entry for entry in ENTRIES if entry["archive_url"] == url))

    real_open = os.open
    hook = case["open_hook"](real_open, holder) if "open_hook" in case else real_open
    stdout = io.StringIO()
    with (mock.patch.object(check, "interactive", return_value=case.get("interactive", True)),
          mock.patch.object(check, "fresh_project", side_effect=setup) as fresh,
          mock.patch.object(check.os, "open", side_effect=hook),
          mock.patch.object(check, "pinned_archive", side_effect=case.get("archive", archive)),
          mock.patch.object(check.subprocess, "run", side_effect=fake_run),
          mock.patch.object(check, "install_args", shape or check.install_args),
          redirect_stdout(stdout), redirect_stderr(io.StringIO())):
        code = check.main(["--owner-acceptance"])
    statuses = {line.split()[2].rstrip(":"): line.split()[0] for line in stdout.getvalue().splitlines()
                if line.split()[:1] in (["INSTALLED"], ["FAILED"], ["NOT-RUN"])}
    return code, statuses, calls, fresh, stdout.getvalue()


TARGET = ENTRIES[0]


def foreign_tree(project):
    """A complete, valid install of TARGET outside the project's own .specify."""
    foreign = project / ".foreign"
    if not (foreign / ".specify").exists():
        (foreign / ".claude" / "skills").mkdir(parents=True)
        v110_install(foreign, TARGET)
    return foreign / ".specify"


def move_in(project, entry):
    """After TARGET's install, a foreign tree is moved in place of .specify."""
    if entry is TARGET:
        foreign = foreign_tree(project)
        os.rename(project / ".specify", project / ".specify-moved-out")
        os.rename(foreign, project / ".specify")


def swap_per_open(real_open, holder):
    """Each checker open under .specify sees the foreign tree, which is put back after the open."""
    def hooked(path, flags, *args, **kwargs):
        name = os.fspath(path)
        if not (holder and called_from_checker() and (name == ".specify" or "/.specify/" in name)):
            return real_open(path, flags, *args, **kwargs)
        project = holder[0]
        foreign = foreign_tree(project)
        os.rename(project / ".specify", project / ".specify-real")
        os.rename(foreign, project / ".specify")
        try:
            return real_open(path, flags, *args, **kwargs)
        finally:
            os.rename(project / ".specify", foreign)
            os.rename(project / ".specify-real", project / ".specify")
    return hooked


def on_later_open(change):
    """Change TARGET's registry when a file read after it (manifest, then skill) is opened."""
    def factory(real_open, holder):
        def hooked(path, flags, *args, **kwargs):
            registry = holder[0] / check.REGISTRY_DIRS[TARGET["kind"]] / ".registry" if holder else None
            if (registry and called_from_checker() and registry.exists()
                    and os.fspath(path).endswith((check.MANIFEST_NAMES[TARGET["kind"]], "SKILL.md"))):
                change(registry)
            return real_open(path, flags, *args, **kwargs)
        return hooked
    return factory


def rewrite(registry):
    registry.write_text(registry.read_text() + " ")


class OwnerAcceptanceTests(unittest.TestCase):
    """--owner-acceptance hands each install to the operator's terminal, then demands on-disk evidence."""

    PRE_CHANGE = staticmethod(lambda entry: [entry["kind"], "add", entry["id"]])

    def test_pre_change_shape_is_red_and_pinned_shape_is_green(self):
        code, statuses, _calls, _fresh, output = run_acceptance(shape=self.PRE_CHANGE)
        self.assertEqual((code, set(statuses.values()), len(statuses)), (1, {"FAILED"}, len(ENTRIES)), output)
        self.assertIn(f"0/{len(ENTRIES)} installed", output)
        code, statuses, _calls, _fresh, output = run_acceptance()
        self.assertEqual((code, set(statuses.values()), len(statuses)), (0, {"INSTALLED"}, len(ENTRIES)), output)
        self.assertIn(f"{len(ENTRIES)}/{len(ENTRIES)} installed", output)
        self.assertIn("match the pinned archive", output)

    def test_each_install_inherits_the_terminal_and_never_bypasses_the_prompt(self):
        _code, _statuses, calls, _fresh, _output = run_acceptance()
        self.assertEqual([argv for argv, _kwargs in calls], [["specify", *check.install_args(entry)] for entry in ENTRIES])
        allowed = {*BASE_KEYS, *check.NETWORK_KEYS, *check.TERMINAL_KEYS}
        for argv, kwargs in calls:
            with self.subTest(argv=argv[1:4]):
                self.assertFalse({"stdin", "stdout", "stderr", "input", "capture_output"} & set(kwargs), kwargs)
                self.assertNotIn("--trust-extension-urls", argv)
                self.assertLessEqual(set(kwargs["env"]), allowed)

    def test_each_missing_piece_of_evidence_fails_only_its_entry(self):
        """Daybreak F1274-d655dfdc and the earlier evidence grid: one wrong piece fails its entry."""
        for entry, defect in product(ENTRIES, (*DEFECTS, *EXTENSION_DEFECTS)):
            if defect in EXTENSION_DEFECTS and entry["kind"] != "extension":
                continue
            with self.subTest(entry=entry["id"], defect=defect):
                code, statuses, _calls, _fresh, output = run_acceptance(defects={entry["id"]: defect})
                self.assertEqual(code, 1, output)
                self.assertEqual(statuses.pop(entry["id"]), "FAILED", output)
                if defect not in ("malformed-registry", "duplicate-installed"):  # these hide later same-kind entries
                    self.assertEqual(set(statuses.values()), {"INSTALLED"}, output)

    def test_a_failed_or_killed_install_is_never_certified(self):
        """Daybreak F1274-86cae5d5: a nonzero or signal exit fails every entry despite matching evidence."""
        for code in EXIT_CODES:
            with self.subTest(exit_code=code):
                exit_code, statuses, _calls, _fresh, output = run_acceptance(exit_code=code)
                self.assertEqual((exit_code, set(statuses.values())), (1, {"FAILED"}), output)
                self.assertIn("signal" if code < 0 else f"exited {code}", output)

    def test_evidence_not_bound_to_this_runs_install_fails_its_entry(self):
        """cr1274g Medium and Daybreak F1274-37d435c0: planted, redirected, torn or late-changed evidence."""
        target = TARGET
        scenarios = {
            "planted-before-install": {"planted": {target["id"]}, "defects": {target["id"]: "declined"}},
            "moved-in-foreign-tree": {"after_install": move_in},
            "foreign-tree-swapped-per-open": {"defects": {target["id"]: "declined"}, "open_hook": swap_per_open},
            "registry-gone-after-read": {"open_hook": on_later_open(
                lambda registry: registry.rename(registry.with_name(".registry-gone")))},
            "registry-rewritten-after-read": {"open_hook": on_later_open(rewrite)},
        }
        for name, case in scenarios.items():
            with self.subTest(scenario=name):
                code, statuses, _calls, _fresh, output = run_acceptance(**case)
                self.assertEqual((code, statuses.get(target["id"])), (1, "FAILED"), output)



class Hung(BaseException):
    """Raised by `deadline` inside a blocked call; not an Exception, so the checker cannot swallow it."""


@contextmanager
def deadline(seconds):
    def expire(*_args):
        raise Hung
    previous = signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def fifo_at(relative):
    """At the last install, replace the node at `relative` with a FIFO that nobody writes."""
    def later(project, entry):
        if entry is ENTRIES[-1]:
            path = project / relative
            shutil.rmtree(path) if path.is_dir() else path.unlink()
            os.mkfifo(path)
    return later


class OwnerAcceptanceScopeTests(unittest.TestCase):
    """--owner-acceptance certifies only what its evidence covers."""

    def test_a_fifo_at_any_evidence_path_fails_its_entry_without_blocking(self):
        """cr1274j Medium: no evidence open may wait on a FIFO; the run reports `failed` instead of hanging."""
        home = f"{check.REGISTRY_DIRS[TARGET['kind']]}/{TARGET['id']}"
        skill = ".claude/skills/" + check.skill_name(f"speckit.{TARGET['id']}.run")
        paths = {"manifest": f"{home}/{check.MANIFEST_NAMES[TARGET['kind']]}", "payload": f"{home}/commands/run.md",
                 "registry": f"{check.REGISTRY_DIRS[TARGET['kind']]}/.registry", "skill": f"{skill}/SKILL.md",
                 "configuration": ".specify/extensions.yml", "skill-directory": skill}
        for name, relative in paths.items():
            with self.subTest(fifo=name):
                try:
                    with deadline(5):
                        code, statuses, _calls, _fresh, output = run_acceptance(after_install=fifo_at(relative))
                except Hung:
                    self.fail(f"owner acceptance blocked on a FIFO at {relative}")
                self.assertEqual((code, statuses.get(TARGET["id"])), (1, "FAILED"), output)

    def test_a_later_install_that_breaks_an_earlier_entry_fails_it(self):
        """cr1274i High: only the tree after the last install is certified, so a later install's damage counts."""
        home = Path(check.REGISTRY_DIRS[TARGET["kind"]]) / TARGET["id"]
        damage = {
            "manifest": lambda project: (project / home / check.MANIFEST_NAMES[TARGET["kind"]]).write_text("destroyed\n"),
            "registry-entry": lambda project: register(project / home.parent, TARGET["kind"], TARGET["id"],
                                                       {"enabled": False}, None),
            "skill": lambda project: (project / ".claude/skills" / check.skill_name(f"speckit.{TARGET['id']}.run")
                                      / "SKILL.md").write_text(skill_text(TARGET, "commands/run.md", "skill-foreign", True)),
            "hooks": lambda project: (project / ".specify/extensions.yml").write_bytes(
                yaml_bytes({**check.read_yaml((project / ".specify/extensions.yml").read_bytes()), "hooks": {}})),
        }
        for name, change in damage.items():
            with self.subTest(damaged=name):
                def later(project, entry, change=change):
                    if entry is ENTRIES[-1]:
                        change(project)
                code, statuses, _calls, _fresh, output = run_acceptance(after_install=later)
                self.assertEqual((code, statuses.get(TARGET["id"])), (1, "FAILED"), output)

    def test_an_entry_declaring_events_is_never_certified(self):
        """Daybreak F1274-ec6eb5b5: manifest events become native hooks and a dispatcher outside this evidence."""
        for entry, event in product(EXTENSIONS, EVENTS):
            with self.subTest(entry=entry["id"], event=event), mock.patch.dict(EVENT_DECLARATIONS, {entry["id"]: event}):
                code, statuses, _calls, _fresh, output = run_acceptance()
                self.assertEqual((code, statuses.pop(entry["id"])), (1, "FAILED"), output)
                self.assertIn("declares Spec Kit events", output)
                self.assertEqual(set(statuses.values()), {"INSTALLED"}, output)


class OwnerAcceptanceGuardTests(unittest.TestCase):
    """--owner-acceptance runs nothing it cannot verify, and stays apart from the legacy option."""

    def test_without_a_terminal_nothing_runs(self):
        code, statuses, calls, fresh, output = run_acceptance(interactive=False)
        self.assertEqual((code, set(statuses.values()), calls), (1, {"NOT-RUN"}, []), output)
        fresh.assert_not_called()
        self.assertIn("interactive terminal", output)

    def test_unavailable_archive_or_cli_is_not_run(self):
        def unavailable(url):
            raise OSError("offline")
        for case in ({"archive": unavailable}, {"start_error": FileNotFoundError("specify")}):
            with self.subTest(case=next(iter(case))):
                code, statuses, calls, _fresh, output = run_acceptance(**case)
                self.assertEqual((code, set(statuses.values())), (1, {"NOT-RUN"}), output)
                self.assertEqual(len(calls), 0 if "archive" in case else len(ENTRIES))

    def test_owner_acceptance_and_legacy_option_are_exclusive(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            check.main(["--owner-acceptance", "--trust-pinned-archives"])
        self.assertEqual(raised.exception.code, 2)


class OwnerAcceptanceDescriptorTests(unittest.TestCase):
    def test_project_descriptor_closes_on_every_acceptance_exit(self):
        tempfile.gettempdir()  # Initialize tempdir discovery before recording project opens.
        installed = [("installed", [])]
        cases = (
            ("success", None, None),
            ("setup-refusal", "fresh_project", ["setup failed"]),
            ("binding-refusal", "bind_project", check.EvidenceError("missing directory")),
            ("setup-exception", "fresh_project", RuntimeError("setup")),
            ("binding-exception", "bind_project", RuntimeError("binding")),
            ("install-exception", "accept_entry", RuntimeError("install")),
            ("final-exception", "final_evidence", RuntimeError("final pass")),
        )
        for name, phase, outcome in cases:
            with self.subTest(exit=name):
                with (record_open_descriptors() as roots,
                      mock.patch.object(check, "fresh_project", return_value=[]) as setup,
                      mock.patch.object(check, "bind_project", return_value={}) as binding,
                      mock.patch.object(check, "accept_entry", return_value=installed[0]) as install,
                      mock.patch.object(check, "final_evidence", return_value=installed) as final):
                    if phase:
                        target = {"fresh_project": setup, "bind_project": binding,
                                  "accept_entry": install, "final_evidence": final}[phase]
                        if isinstance(outcome, Exception):
                            target.side_effect = outcome
                        else:
                            target.return_value = outcome
                    if isinstance(outcome, RuntimeError):
                        with self.assertRaises(RuntimeError):
                            check.run_acceptance([TARGET])
                    else:
                        result = check.run_acceptance([TARGET])
                        self.assertEqual(result[0][0], "installed" if phase is None else "not-run")
                self.assertTrue(roots)
                for descriptor in roots:
                    with self.subTest(descriptor=descriptor):
                        with self.assertRaises(OSError) as raised:
                            os.fstat(descriptor)
                        self.assertEqual(raised.exception.errno, errno.EBADF)


class YamlReaderTests(unittest.TestCase):
    """cr1274h Medium: the evidence reader is standard library only, reads what PyYAML reads for the
    shapes Spec Kit v1.1.0 writes, and refuses the rest, duplicate keys included."""

    DUMPED = """\
schema_version: "1.0"  # a pinned manifest's layout
provides:
  commands:
    - name: "speckit.cleanup.run"
      aliases: ["speckit.cleanup", 'x, y']

installed:
- review
hooks:
  after_implement:
  - extension: review
    enabled: true
    optional: off
    priority: 10
    prompt: Converged? Run verify-tasks in a fresh session as the final gate before
      opening a PR
    description: 'It''s folded: a quoted value that also runs past the eighty column
      limit'
    condition: null
    empty:
    escaped: "tab\\there \\"quoted\\""
"""

    def test_reads_spec_kit_layouts(self):
        hook = {"extension": "review", "enabled": True, "optional": False, "priority": 10,
                "prompt": "Converged? Run verify-tasks in a fresh session as the final gate before opening a PR",
                "description": "It's folded: a quoted value that also runs past the eighty column limit",
                "condition": None, "empty": None, "escaped": 'tab\there "quoted"'}
        self.assertEqual(check.read_yaml(self.DUMPED.encode()), {
            "schema_version": "1.0",
            "provides": {"commands": [{"name": "speckit.cleanup.run", "aliases": ["speckit.cleanup", "x, y"]}]},
            "installed": ["review"], "hooks": {"after_implement": [hook]}})

    def test_character_ranges_remain_escaped_for_analysis(self):
        # Static analyzers must receive escaped endpoints, not decoded Unicode literals.
        with mock.patch.object(check.re, "search", wraps=check.re.search) as search:
            self.assertEqual(check.read_yaml(b'a: text\n'), {"a": "text"})
        self.assertTrue(search.call_args_list[0].args[0].isascii())

    def test_character_range_boundaries(self):
        allowed = (0x20, 0x21, 0x7E, 0xA0, 0xD7FF, 0xE000, 0xFFFD, 0x10000, 0x10FFFF)
        refused = (0, 8, 9, 0xD, 0x1F, 0x7F, 0x85, 0x9F, 0x2028, 0x2029, 0xFFFE, 0xFFFF)
        for codepoint in allowed:
            with self.subTest(allowed=codepoint):
                value = chr(codepoint)
                self.assertEqual(check.read_yaml(f'a: "{value}"\n'.encode()), {"a": value})
        for codepoint in refused:
            with self.subTest(refused=codepoint), self.assertRaises(check.EvidenceError):
                check.read_yaml(f'a: "{chr(codepoint)}"\n'.encode())

    def test_refuses_what_it_cannot_read_exactly(self):
        refused = {
            "duplicate key": "a: 1\na: 2\n", "nested duplicate": "a:\n  b: 1\n  b: 1\n",
            "duplicate in a list item": "- a: 1\n  a: 1\n", "anchor": "a: &x 1\n", "alias": "a: *x\n",
            "tag": "a: !!str 1\n", "block scalar": "a: |\n  text\n", "folded block scalar": "a: >\n  text\n",
            "multi-line double quote": 'a: "one\n  two"\n', "blank line inside a value": "a: one\n\n  two\n",
            "tab": "a:\t1\n", "carriage return": "a: 1\r\nb: 2\r\n", "float": "a: 1.5\n",
            "timestamp": "a: 2024-01-01\n", "octal": "a: 012\n", "non-string key": "on: 1\n",
            "document marker": "---\na: 1\n", "flow mapping": "a: {b: 1}\n", "unclosed quote": "a: 'open\n", "hex escape": 'a: "\\x41"\n',
            "stray indentation": "a:\n    b: 1\n  c: 2\n", "mapping in a plain scalar": "a: b: c\n",
        }
        for name, text in refused.items():
            with self.subTest(name=name), self.assertRaises(check.EvidenceError):
                check.read_yaml(text.encode())

    def test_imports_only_the_standard_library_and_this_repository(self):
        """A clean `python3 -I -S` (CI's interpreter) can run the verifier: no import, even a deferred one,
        reaches a third-party package."""
        tree = ast.parse(VERIFIER.read_text(encoding="utf-8"))
        names = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        names |= {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        for name in sorted({name.split(".")[0] for name in names} - set(sys.stdlib_module_names)):
            with self.subTest(module=name):
                spec = importlib.util.find_spec(name)
                self.assertTrue(spec and spec.origin and Path(spec.origin).resolve().is_relative_to(REPO_ROOT), spec)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-curated-install-check"))
