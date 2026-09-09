#!/usr/bin/env python3
"""Focused Layer 4 tests for the PR Checks Python helpers."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


def load_script(module_name: str, script_name: str) -> ModuleType:
    script_path = REPO_ROOT / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper: {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ACTIONLINT = load_script("pr_checks_install_actionlint", "install-actionlint.py")
DOCS = load_script("pr_checks_classify_docs", "classify-docs-validation.py")
RESULTS = load_script("pr_checks_results", "check-pr-workflow-results.py")
MATRIX = load_script("pr_checks_matrix", "emit-plugin-matrix.py")


def make_archive(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, content in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            member.mode = 0o644
            archive.addfile(member, io.BytesIO(content))
    return buffer.getvalue()


class ActionlintHelperTests(unittest.TestCase):
    def test_install_downloads_verified_member_with_executable_mode(self) -> None:
        archive_bytes = make_archive(
            {
                "README.md": b"actionlint release\n",
                "actionlint": b"binary-content\n",
            }
        )
        expected_sha256 = hashlib.sha256(archive_bytes).hexdigest()
        observed: dict[str, object] = {}

        def opener(request: object, *, timeout: int) -> io.BytesIO:
            observed["url"] = request.full_url  # type: ignore[attr-defined]
            observed["timeout"] = timeout
            return io.BytesIO(archive_bytes)

        with tempfile.TemporaryDirectory() as temporary_directory:
            install_directory = Path(temporary_directory)
            installed = ACTIONLINT.install_actionlint(
                "1.7.12",
                expected_sha256,
                install_directory,
                opener=opener,
            )

            self.assertEqual(b"binary-content\n", installed.read_bytes())
            self.assertEqual(0o755, stat.S_IMODE(installed.stat().st_mode))
            self.assertEqual(install_directory / "actionlint", installed)

        self.assertEqual(
            "https://github.com/rhysd/actionlint/releases/download/"
            "v1.7.12/actionlint_1.7.12_linux_amd64.tar.gz",
            observed["url"],
        )
        self.assertEqual(ACTIONLINT.DOWNLOAD_TIMEOUT_SECONDS, observed["timeout"])

    def test_install_rejects_checksum_mismatch_before_extraction(self) -> None:
        archive_bytes = make_archive({"actionlint": b"binary-content\n"})

        with tempfile.TemporaryDirectory() as temporary_directory:
            install_directory = Path(temporary_directory)
            with self.assertRaisesRegex(ACTIONLINT.ActionlintError, "checksum mismatch"):
                ACTIONLINT.install_actionlint(
                    "1.7.12",
                    "0" * 64,
                    install_directory,
                    opener=lambda *_args, **_kwargs: io.BytesIO(archive_bytes),
                )
            self.assertFalse((install_directory / "actionlint").exists())

    def test_extract_rejects_unsafe_archive_members(self) -> None:
        archive_bytes = make_archive(
            {
                "actionlint": b"binary-content\n",
                "../outside": b"unsafe\n",
            }
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            root = base / "inside"
            root.mkdir()
            archive_path = root / "actionlint.tar.gz"
            archive_path.write_bytes(archive_bytes)
            with self.assertRaisesRegex(ACTIONLINT.ActionlintError, "unsafe members"):
                ACTIONLINT.extract_actionlint(archive_path, root / "actionlint")
            self.assertFalse((root / "actionlint").exists())
            self.assertFalse((base / "outside").exists())

    def test_extract_rejects_archive_without_exact_expected_member(self) -> None:
        archive_bytes = make_archive({"bin/actionlint": b"binary-content\n"})
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            archive_path = root / "actionlint.tar.gz"
            archive_path.write_bytes(archive_bytes)
            with self.assertRaisesRegex(
                ACTIONLINT.ActionlintError,
                "exactly one top-level actionlint member",
            ):
                ACTIONLINT.extract_actionlint(archive_path, root / "actionlint")

    def test_run_uses_deterministically_sorted_workflow_argv(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            executable = root / "bin" / "actionlint"
            executable.parent.mkdir()
            executable.write_bytes(b"binary\n")
            executable.chmod(0o755)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "z-last.yml").write_text("name: Z\n", encoding="utf-8")
            (workflows / "a-first.yml").write_text("name: A\n", encoding="utf-8")
            (workflows / "ignored.yaml").write_text("name: Ignored\n", encoding="utf-8")
            runner = mock.Mock(
                return_value=subprocess.CompletedProcess(["actionlint"], 0)
            )

            with mock.patch.object(ACTIONLINT.subprocess, "run", runner):
                ACTIONLINT.run_actionlint(executable, workflows)

        argv = runner.call_args.args[0]
        self.assertEqual("actionlint", argv[0])
        self.assertEqual(
            [str(workflows / "a-first.yml"), str(workflows / "z-last.yml")],
            argv[1:],
        )
        self.assertFalse(any("*" in argument for argument in argv))
        self.assertIs(runner.call_args.kwargs["shell"], False)
        self.assertIs(runner.call_args.kwargs["check"], True)
        self.assertEqual(
            str(executable.parent),
            runner.call_args.kwargs["env"]["PATH"].split(os.pathsep, 1)[0],
        )

    def test_run_reports_subprocess_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            executable = root / "actionlint"
            executable.write_bytes(b"binary\n")
            executable.chmod(0o755)
            workflows = root / "workflows"
            workflows.mkdir()
            (workflows / "pr-checks.yml").write_text("name: PR Checks\n", encoding="utf-8")
            runner = mock.Mock(
                side_effect=subprocess.CalledProcessError(7, ["actionlint"])
            )

            with self.assertRaisesRegex(
                ACTIONLINT.ActionlintError,
                "actionlint failed with exit code 7",
            ):
                with mock.patch.object(ACTIONLINT.subprocess, "run", runner):
                    ACTIONLINT.run_actionlint(executable, workflows)


class DocsClassificationHelperTests(unittest.TestCase):
    def test_docs_validation_runs_the_dedicated_gallery_project(self) -> None:
        scripts = json.loads((REPO_ROOT / "docs-site" / "package.json").read_text(encoding="utf-8"))["scripts"]
        self.assertEqual("playwright test --config playwright.gallery.config.mjs", scripts["validate:gallery"])
        self.assertIn("&& pnpm validate:gallery", scripts["validate"])

    def test_full_mode_for_rendered_docs(self) -> None:
        classification = DOCS.classify_changed_files(
            ["docs-site/src/content/docs/reference/index.md"]
        )
        self.assertEqual("full", classification.validation_mode)
        self.assertTrue(classification.rendered_docs)
        self.assertFalse(classification.generated_reference)
        self.assertFalse(classification.docs_contract)

    def test_full_mode_for_docs_contract(self) -> None:
        for file_path in (
            ".github/workflows/pr-checks.yml",
            "scripts/classify-docs-validation.py",
            "scripts/docs-artifact.py",
        ):
            with self.subTest(file_path=file_path):
                classification = DOCS.classify_changed_files([file_path])
                self.assertEqual("full", classification.validation_mode)
                self.assertFalse(classification.rendered_docs)
                self.assertEqual(file_path.startswith("scripts/"), classification.generated_reference)
                self.assertTrue(classification.docs_contract)

    def test_full_mode_for_gallery_contract(self) -> None:
        classification = DOCS.classify_changed_files(
            ["speckit-pro/artifact-gallery/templates/implementation-plan.html"]
        )
        self.assertEqual("full", classification.validation_mode)
        self.assertTrue(classification.docs_contract)

    def test_reference_mode_for_generated_reference_source(self) -> None:
        classification = DOCS.classify_changed_files(
            ["speckit-pro/skills/speckit-coach/SKILL.md"]
        )
        self.assertEqual("reference", classification.validation_mode)
        self.assertFalse(classification.rendered_docs)
        self.assertTrue(classification.generated_reference)
        self.assertFalse(classification.docs_contract)
        self.assertEqual("true", classification.output_fields()["should_validate_docs"])

    def test_skip_mode_for_plugin_only_change(self) -> None:
        classification = DOCS.classify_changed_files(
            ["speckit-pro/commands/autopilot.md"]
        )
        self.assertEqual("skip", classification.validation_mode)
        self.assertFalse(classification.should_validate_docs)
        self.assertEqual(
            {
                "should_validate_docs": "false",
                "validation_mode": "skip",
                "rendered_docs": "false",
                "generated_reference": "false",
                "docs_contract": "false",
            },
            classification.output_fields(),
        )

    def test_path_boundaries_do_not_match_prefix_lookalikes(self) -> None:
        classification = DOCS.classify_changed_files(
            [
                "docs-site-old/src/index.md",
                "scripts-old/helper.py",
                "tests/speckit-pro-old/test.py",
                "speckit-pro/skills-old/SKILL.md",
                ".specify/integrations-old/provider.md",
                "dist/codex-old/manifest.json",
            ]
        )
        self.assertEqual("skip", classification.validation_mode)
        self.assertFalse(classification.rendered_docs)
        self.assertFalse(classification.generated_reference)
        self.assertFalse(classification.docs_contract)

    def test_manifest_readme_and_integration_patterns_match_original_contract(self) -> None:
        for file_path in (
            "speckit-pro/.claude-plugin/plugin.json",
            "plugin/README.md",
            ".specify/integrations/provider/nested.md",
        ):
            with self.subTest(file_path=file_path):
                classification = DOCS.classify_changed_files([file_path])
                self.assertEqual("reference", classification.validation_mode)
                self.assertTrue(classification.generated_reference)

    def test_changed_files_use_argument_array_subprocess(self) -> None:
        runner = mock.Mock(
            return_value=subprocess.CompletedProcess(
                ["git"],
                0,
                stdout="scripts/a.py\nREADME.md\n",
                stderr="",
            )
        )
        with mock.patch.object(DOCS.subprocess, "run", runner):
            changed_files = DOCS.changed_files_for_base(
                "main",
                repo_root=REPO_ROOT,
            )
        self.assertEqual(("scripts/a.py", "README.md"), changed_files)
        self.assertEqual(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            runner.call_args.args[0],
        )
        self.assertEqual(REPO_ROOT, runner.call_args.kwargs["cwd"])
        self.assertIs(runner.call_args.kwargs["shell"], False)
        self.assertIs(runner.call_args.kwargs["check"], True)

    def test_github_output_is_appended_in_contract_order(self) -> None:
        classification = DOCS.classify_changed_files(["scripts/helper.py"])
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "github-output"
            output_path.write_text("existing=value\n", encoding="utf-8")
            DOCS.append_github_output(output_path, classification.output_fields())
            content = output_path.read_text(encoding="utf-8")
        self.assertEqual(
            "existing=value\n"
            "should_validate_docs=true\n"
            "validation_mode=reference\n"
            "rendered_docs=false\n"
            "generated_reference=true\n"
            "docs_contract=false\n",
            content,
        )


class WorkflowResultsHelperTests(unittest.TestCase):
    def test_success_and_skipped_results_pass(self) -> None:
        self.assertEqual(
            "Plugin tests passed or were skipped (result: success); "
            "artifacts consistent (result: success).",
            RESULTS.check_workflow_results("success", "success", "success"),
        )
        self.assertEqual(
            "Plugin tests passed or were skipped (result: skipped); "
            "artifacts consistent (result: skipped).",
            RESULTS.check_workflow_results("success", "skipped", "skipped"),
        )

    def test_detect_failure_and_cancellation_fail_first(self) -> None:
        for result in ("failure", "cancelled"):
            with self.subTest(result=result):
                with self.assertRaisesRegex(
                    RESULTS.WorkflowResultError,
                    rf"Detect job did not succeed \(result: {result}\)\. Workflow is broken\.",
                ):
                    RESULTS.check_workflow_results(result, "skipped", "skipped")

    def test_test_failure_and_cancellation_fail(self) -> None:
        for result in ("failure", "cancelled"):
            with self.subTest(result=result):
                with self.assertRaisesRegex(
                    RESULTS.WorkflowResultError,
                    rf"Plugin tests failed or were cancelled \(result: {result}\)\.",
                ):
                    RESULTS.check_workflow_results("success", result, "success")

    def test_artifact_failure_and_cancellation_fail(self) -> None:
        for result in ("failure", "cancelled"):
            with self.subTest(result=result):
                with self.assertRaisesRegex(
                    RESULTS.WorkflowResultError,
                    rf"Generated artifacts drift from source \(result: {result}\)\.",
                ):
                    RESULTS.check_workflow_results("success", "success", result)

    def test_detect_skipped_preserves_existing_truth_table(self) -> None:
        message = RESULTS.check_workflow_results("skipped", "skipped", "skipped")
        self.assertIn("Plugin tests passed or were skipped", message)

    def test_main_emits_exact_github_error_message(self) -> None:
        stderr = io.StringIO()
        with (
            mock.patch.dict(
                os.environ,
                {
                    "DETECT_RESULT": "success",
                    "TEST_RESULT": "cancelled",
                    "ARTIFACT_RESULT": "success",
                },
            ),
            contextlib.redirect_stderr(stderr),
        ):
            return_code = RESULTS.main([])
        self.assertEqual(1, return_code)
        self.assertEqual(
            "::error::Plugin tests failed or were cancelled (result: cancelled).\n",
            stderr.getvalue(),
        )


class PluginMatrixHelperTests(unittest.TestCase):
    def test_static_matrix_appends_exact_compact_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "github-output"
            output_path.write_text("existing=value\n", encoding="utf-8")
            encoded = MATRIX.append_plugin_matrix(output_path)
            content = output_path.read_text(encoding="utf-8")
        self.assertEqual('["speckit-pro"]', encoded)
        self.assertEqual(
            'existing=value\nplugins=["speckit-pro"]\n',
            content,
        )


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for test_case in (
        ActionlintHelperTests,
        DocsClassificationHelperTests,
        WorkflowResultsHelperTests,
        PluginMatrixHelperTests,
    ):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-pr-checks-helpers")


if __name__ == "__main__":
    raise SystemExit(main())
