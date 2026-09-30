#!/usr/bin/env python3
"""Focused Layer 4 tests for the PR Checks Python helpers."""

from __future__ import annotations

import contextlib
import hashlib
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
# Fake file only: run_actionlint's subprocess is mocked in these tests.
ACTIONLINT_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pr-checks" / "actionlint"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


from script_loader import load_script as load_module_from_path  # noqa: E402


def load_script(module_name: str, script_name: str) -> ModuleType:
    script_path = REPO_ROOT / "scripts" / script_name
    return load_module_from_path(module_name, script_path)


ACTIONLINT = load_script("pr_checks_install_actionlint", "install-actionlint.py")
DOCS = load_script("pr_checks_classify_docs", "classify-docs-validation.py")
RESULTS = load_script("pr_checks_results", "check-pr-workflow-results.py")
MATRIX = load_script("pr_checks_matrix", "emit-plugin-matrix.py")
GO_MODULE = load_script("pr_checks_go_module", "check-go-module.py")
LINT = load_script("pr_checks_python_lint", "run-python-lint.py")
SUPERSEDED = load_script("pr_checks_superseded_run", "superseded_run.py")


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
            executable = ACTIONLINT_FIXTURE
            self.assertFalse(executable.resolve().is_relative_to(root.resolve()))
            self.assertEqual(executable.read_bytes(), b"binary\n")
            self.assertTrue(os.access(executable, os.X_OK))
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
            executable = ACTIONLINT_FIXTURE
            self.assertFalse(executable.resolve().is_relative_to(root.resolve()))
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

    @unittest.skipIf(os.name == "nt", "POSIX executable permission check")
    def test_run_rejects_nonexecutable_file_before_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            executable = root / "actionlint"
            executable.write_bytes(ACTIONLINT_FIXTURE.read_bytes())
            executable.chmod(0o644)
            with mock.patch.object(ACTIONLINT.subprocess, "run") as runner:
                with self.assertRaisesRegex(ACTIONLINT.ActionlintError, "is not executable"):
                    ACTIONLINT.run_actionlint(executable, root)
                runner.assert_not_called()


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
            "scripts/changed_files.py", "scripts/classify-docs-validation.py",
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
        with mock.patch.object(DOCS._changed_files.subprocess, "run", runner):
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


class DeployDocsTriggerTests(unittest.TestCase):
    def test_deploy_trigger_paths_are_classified_as_docs_affecting(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "deploy-docs.yml").read_text(encoding="utf-8")
        block = workflow.split("    paths:\n", 1)[1].split("  workflow_dispatch:", 1)[0]
        entries = [line.strip()[2:].strip('"') for line in block.splitlines() if line.strip().startswith("- ")]
        self.assertGreater(len(entries), 10)
        for entry in entries:
            sample = entry.removeprefix("!").replace("**", "sample")
            with self.subTest(entry=entry):
                # The classifier is the stricter list: a path the deploy trigger
                # excludes (fixtures, parity) still needs PR docs validation,
                # because the generated test reference lists those files.
                self.assertTrue(DOCS.classify_changed_files([sample]).should_validate_docs, sample)


class WorkflowResultsHelperTests(unittest.TestCase):
    def test_success_and_skipped_results_pass(self) -> None:
        self.assertEqual(
            "Plugin tests passed or were skipped (result: success); "
            "artifacts consistent (result: success); "
            "Go module checks passed or were skipped (result: success).",
            RESULTS.check_workflow_results("success", "success", "success", "success"),
        )
        self.assertEqual(
            "Plugin tests passed or were skipped (result: skipped); "
            "artifacts consistent (result: skipped); "
            "Go module checks passed or were skipped (result: skipped).",
            RESULTS.check_workflow_results("success", "skipped", "skipped", "skipped"),
        )

    def test_detect_failure_and_cancellation_fail_first(self) -> None:
        for result in ("failure", "cancelled"):
            with self.subTest(result=result):
                with self.assertRaisesRegex(
                    RESULTS.WorkflowResultError,
                    rf"Detect job did not succeed \(result: {result}\)\. Workflow is broken\.",
                ):
                    RESULTS.check_workflow_results(result, "skipped", "skipped", "skipped")

    def test_test_failure_and_cancellation_fail(self) -> None:
        for result in ("failure", "cancelled"):
            with self.subTest(result=result):
                with self.assertRaisesRegex(
                    RESULTS.WorkflowResultError,
                    rf"Plugin tests failed or were cancelled \(result: {result}\)\.",
                ):
                    RESULTS.check_workflow_results("success", result, "success", "success")

    def test_artifact_failure_and_cancellation_fail(self) -> None:
        for result in ("failure", "cancelled"):
            with self.subTest(result=result):
                with self.assertRaisesRegex(
                    RESULTS.WorkflowResultError,
                    rf"Generated artifacts drift from source \(result: {result}\)\.",
                ):
                    RESULTS.check_workflow_results("success", "success", result, "success")

    def test_go_failure_cancellation_and_missing_result_fail(self) -> None:
        for result in ("failure", "cancelled", ""):
            with self.subTest(result=result):
                with self.assertRaisesRegex(
                    RESULTS.WorkflowResultError,
                    rf"Go module checks failed or were cancelled \(result: {result}\)\.",
                ):
                    RESULTS.check_workflow_results("success", "success", "success", result)

    def test_detect_skipped_preserves_existing_truth_table(self) -> None:
        message = RESULTS.check_workflow_results("skipped", "skipped", "skipped", "skipped")
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
                    "GO_RESULT": "success",
                },
            ),
            contextlib.redirect_stderr(stderr),
        ):
            return_code = RESULTS.main([], superseded=lambda: None)
        self.assertEqual(1, return_code)
        self.assertEqual(
            "::error::Plugin tests failed or were cancelled (result: cancelled).\n",
            stderr.getvalue(),
        )


HEAD_SHA = "a" * 40


def fetch_with(runs: list[dict], current: dict | None = None):
    """Fake the two Actions API reads; record each requested path."""
    requested: list[str] = []
    current = current or {"id": 100, "workflow_id": 9, "head_sha": HEAD_SHA}
    listing = f"/repos/owner/repo/actions/workflows/9/runs?head_sha={HEAD_SHA}&event=pull_request&per_page=100"

    def fetch(path: str) -> dict:
        requested.append(path)
        if path in {"/repos/owner/repo/actions/runs/100", listing}:
            return current if path.endswith("/100") else {"workflow_runs": runs}
        raise AssertionError(f"unexpected path {path}")

    return fetch, requested


def run_row(run_id: object, **overrides: object) -> dict:
    return {"id": run_id, "head_sha": HEAD_SHA, "workflow_id": 9, "event": "pull_request", **overrides}


class SupersededRunLookupTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.event = Path(temporary.name) / "event.json"
        self.event.write_text(json.dumps({"pull_request": {"head": {"sha": HEAD_SHA}}}), encoding="utf-8")
        self.env = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_REPOSITORY": "owner/repo",
                    "GITHUB_RUN_ID": "100", "GITHUB_EVENT_PATH": str(self.event)}

    def test_newer_run_of_the_same_workflow_and_commit_supersedes(self) -> None:
        fetch, requested = fetch_with([run_row(100), run_row(104), run_row(102)])
        self.assertEqual(102, SUPERSEDED.newer_run_id(self.env, fetch))
        self.assertEqual(2, len(requested))
        self.assertIn("superseded by run 102 for the same head commit",
                      SUPERSEDED.superseded_notice(self.env, fetch))
        rows = [run_row(99), run_row(101, head_sha="b" * 40), run_row(102, workflow_id=8),
                run_row(103, event="workflow_dispatch"), run_row("104")]
        self.assertIsNone(SUPERSEDED.newer_run_id(self.env, fetch_with(rows)[0]))

    def test_missing_inputs_never_reach_the_api(self) -> None:
        def fetch(path: str) -> dict:
            raise AssertionError("API must not be called")

        cases = [("GITHUB_EVENT_NAME", "workflow_dispatch"), ("GITHUB_REPOSITORY", ""),
                 ("GITHUB_RUN_ID", "abc"), ("GITHUB_EVENT_PATH", str(self.event) + ".missing")]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                self.assertIsNone(SUPERSEDED.newer_run_id({**self.env, key: value}, fetch))
        for payload in ({"pull_request": {"head": {"sha": "not-a-sha"}}}, {"pull_request": None}, []):
            with self.subTest(payload=payload):
                self.event.write_text(json.dumps(payload), encoding="utf-8")
                self.assertIsNone(SUPERSEDED.newer_run_id(self.env, fetch))
        self.assertIsNone(SUPERSEDED.newer_run_id(self.env))

    def test_api_errors_and_mismatched_runs_fail_closed(self) -> None:
        def broken(error: Exception):
            def fetch(path: str) -> dict:
                raise error
            return fetch

        for error in (OSError("offline"), ValueError("bad json"), KeyError("id")):
            with self.subTest(error=type(error).__name__):
                self.assertIsNone(SUPERSEDED.newer_run_id(self.env, broken(error)))
        for current in (
            {"id": 100, "workflow_id": 9, "head_sha": "b" * 40},
            {"id": 101, "workflow_id": 9, "head_sha": HEAD_SHA},
            {"id": 100, "workflow_id": "9", "head_sha": HEAD_SHA},
            {"id": 100, "head_sha": HEAD_SHA},
        ):
            with self.subTest(current=current):
                fetch, _requested = fetch_with([run_row(105)], current)
                self.assertIsNone(SUPERSEDED.newer_run_id(self.env, fetch))
        fetch = fetch_with([])[0]
        self.assertIsNone(SUPERSEDED.superseded_notice(self.env, fetch))


class SupersededVerdictTests(unittest.TestCase):
    def test_main_passes_a_cancelled_run_only_when_a_newer_run_supersedes_it(self) -> None:
        results = {"DETECT_RESULT": "success", "ARTIFACT_RESULT": "success", "GO_RESULT": "success"}
        cases = (
            ("cancelled", "superseded by run 7", 0),
            ("cancelled", None, 1),
            ("failure", "superseded by run 7", 1),
        )
        for test_result, notice, expected in cases:
            with self.subTest(test_result=test_result, notice=notice):
                stdout, stderr = io.StringIO(), io.StringIO()
                calls: list[str] = []

                def superseded(notice: str | None = notice) -> str | None:
                    calls.append("asked")
                    return notice

                with (
                    mock.patch.dict(os.environ, {**results, "TEST_RESULT": test_result}),
                    contextlib.redirect_stdout(stdout),
                    contextlib.redirect_stderr(stderr),
                ):
                    self.assertEqual(expected, RESULTS.main([], superseded=superseded))
                self.assertEqual(calls, ["asked"] if test_result == "cancelled" else [])
                if expected == 0:
                    self.assertEqual("::notice::superseded by run 7\n", stdout.getvalue())
                else:
                    self.assertIn("::error::Plugin tests failed", stderr.getvalue())


class PythonLintHelperTests(unittest.TestCase):
    def completed(self, argv, **_kwargs):
        self.calls.append(list(argv))
        return subprocess.CompletedProcess(argv, self.returncode)

    def setUp(self) -> None:
        self.calls: list[list[str]] = []
        self.returncode = 0

    def test_install_pins_the_tool_version_with_pip(self) -> None:
        self.assertEqual(0, LINT.main(["install", "ruff"], run=self.completed))
        self.assertEqual(
            [[sys.executable, "-m", "pip", "install", f"ruff=={LINT.PINNED_VERSIONS['ruff']}"]],
            self.calls,
        )

    def test_run_passes_extra_arguments_and_returns_the_tool_exit_code(self) -> None:
        self.returncode = 3
        pinned = LINT.PINNED_VERSIONS["ruff"]
        result = LINT.main(
            ["run", "ruff", "--output-format", "github"],
            run=self.completed,
            version_of=lambda _tool: pinned,
        )
        self.assertEqual(3, result)
        self.assertEqual(
            [[sys.executable, "-m", "ruff", "check", "--no-cache", "--output-format", "github"]],
            self.calls,
        )

    def test_run_refuses_a_missing_or_unpinned_tool_before_running_it(self) -> None:
        def missing(tool: str) -> str:
            raise LINT.metadata.PackageNotFoundError(tool)

        for version_of, message in (
            (missing, "mypy is not installed"),
            (lambda _tool: "0.0.1", "mypy 0.0.1 is installed, but the pinned version is"),
        ):
            with self.subTest(message=message):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    result = LINT.main(["run", "mypy"], run=self.completed, version_of=version_of)
                self.assertEqual(1, result)
                self.assertIn(message, stderr.getvalue())
        self.assertEqual([], self.calls)


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


class GoModuleHelperTests(unittest.TestCase):
    def test_module_wrapper_and_workflow_changes_run_go(self) -> None:
        for changed in (
            ["typesafe-jev/cmd/evaluate/main.go"],
            ["typesafe-jev/go.mod"],
            ["README.md", "scripts/check-go-module.py"],
            ["scripts/changed_files.py"], [".github/workflows/pr-checks.yml"],
        ):
            with self.subTest(changed=changed):
                self.assertTrue(GO_MODULE.go_module_changed(changed))

    def test_other_changes_skip_go(self) -> None:
        for changed in (
            [],
            ["speckit-pro/README.md", "scripts/check-pr-workflow-results.py"],
            ["typesafe-jev-notes.md", "docs/typesafe-jev/guide.md"],
        ):
            with self.subTest(changed=changed):
                self.assertFalse(GO_MODULE.go_module_changed(changed))

    def test_detect_appends_run_go(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "github-output"
            output_path.write_text("existing=value\n", encoding="utf-8")
            with (
                mock.patch.object(
                    GO_MODULE, "changed_files_for_base", return_value=("typesafe-jev/go.sum",)
                ),
                mock.patch.dict(os.environ, {"BASE_REF": "main", "GITHUB_OUTPUT": str(output_path)}),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                return_code = GO_MODULE.main(["detect"])
            content = output_path.read_text(encoding="utf-8")
        self.assertEqual(0, return_code)
        self.assertEqual("existing=value\nrun_go=true\n", content)

    def test_missing_base_ref_fails(self) -> None:
        stderr = io.StringIO()
        with (
            mock.patch.dict(os.environ, {"BASE_REF": "", "GITHUB_OUTPUT": ""}),
            contextlib.redirect_stderr(stderr),
        ):
            return_code = GO_MODULE.main(["detect"])
        self.assertEqual(1, return_code)
        self.assertEqual("::error::Go module check failed: BASE_REF is not set\n", stderr.getvalue())

    def test_unknown_mode_fails(self) -> None:
        for argv in ([], ["lint"], ["check", "extra"]):
            with self.subTest(argv=argv):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    return_code = GO_MODULE.main(argv)
                self.assertEqual(1, return_code)
                self.assertIn("usage: check-go-module.py detect|check", stderr.getvalue())

    def test_failed_go_tool_raises_with_its_argv(self) -> None:
        completed = subprocess.CompletedProcess(["go", "vet", "./..."], 1, stdout="", stderr="vet: boom\n")
        with (
            mock.patch.object(GO_MODULE.subprocess, "run", return_value=completed) as run,
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            with self.assertRaisesRegex(GO_MODULE.GoModuleCheckError, r"go vet \./\.\.\. failed with exit code 1"):
                GO_MODULE.run_go("vet", "./...")
        self.assertEqual(["go", "vet", "./..."], run.call_args.args[0])
        self.assertIs(False, run.call_args.kwargs["shell"])
        self.assertEqual(GO_MODULE.REPO_ROOT / "typesafe-jev", run.call_args.kwargs["cwd"])

    def test_missing_go_tool_is_reported(self) -> None:
        with (
            mock.patch.object(GO_MODULE.subprocess, "run", side_effect=FileNotFoundError("gofmt")),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            with self.assertRaisesRegex(GO_MODULE.GoModuleCheckError, r"unable to run gofmt"):
                GO_MODULE.run_gofmt("-l", ".")

    def test_unformatted_files_fail_the_check(self) -> None:
        with (
            mock.patch.object(GO_MODULE, "run_go", return_value="") as run_go,
            mock.patch.object(GO_MODULE, "run_gofmt", return_value="cmd/evaluate/main.go\n") as run_gofmt,
        ):
            with self.assertRaisesRegex(GO_MODULE.GoModuleCheckError, r"gofmt would reformat: cmd/evaluate/main\.go"):
                GO_MODULE.check()
        self.assertEqual([mock.call("mod", "verify")], run_go.call_args_list)
        run_gofmt.assert_called_once_with("-l", ".")


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for test_case in (
        ActionlintHelperTests,
        DocsClassificationHelperTests,
        DeployDocsTriggerTests,
        WorkflowResultsHelperTests,
        SupersededRunLookupTests,
        SupersededVerdictTests,
        PluginMatrixHelperTests,
        GoModuleHelperTests,
    ):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-pr-checks-helpers")


if __name__ == "__main__":
    raise SystemExit(main())
