#!/usr/bin/env python3
"""`validate-plugins` sentinel-job validation (port of validate-pr-checks-sentinel.sh).

XPLAT-010 count-parity port (T032, US2). Python 3.11+ standard library only.
Verifies ``.github/workflows/pr-checks.yml`` defines the ``validate-plugins``
sentinel with the correct triggers, dispatch inputs, Python-runner gate steps,
and sentinel logic. XPLAT-010 PR 11 extends the same structural boundary to
``container-preflight.yml``: always-triggered PR reporting, lightweight change
detection, conditional heavy jobs, stable Linux required-check sentinels,
configured Windows availability, and always-run evidence uploads. The validator
then folds every ``.github/workflows/*.yml`` into one "valid YAML" outcome.

YAML syntax: the deleted shell predecessor optionally probed non-stdlib YAML
parsers (``python -c import yaml`` or Ruby) when they happened to be installed.
This port does not invoke those probes. It keeps the current runtime stdlib-only
by applying a conservative GitHub-workflow YAML sanity check that guards
indentation, mapping/sequence structure, and block-scalar boundaries without
adding PyYAML/Ruby as runtime dependencies.

PR 5 updated this ported validator for the CI dispatch swap (task T049); PR 11
adds the container-preflight contract checks (task T106).

Baseline: ``tests/speckit-pro/parity/bash-to-python/validate-pr-checks-sentinel-baseline.txt``
(TOTAL: 49).
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

from workflow_yaml_sanity import yaml_syntax_sane as _yaml_syntax_sane

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "pr-checks.yml"
ACTIONLINT_HELPER_FILE = REPO_ROOT / "scripts" / "install-actionlint.py"
DOCS_CLASSIFIER_FILE = REPO_ROOT / "scripts" / "classify-docs-validation.py"
RESULTS_HELPER_FILE = REPO_ROOT / "scripts" / "check-pr-workflow-results.py"
MATRIX_HELPER_FILE = REPO_ROOT / "scripts" / "emit-plugin-matrix.py"
CONTAINER_WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "container-preflight.yml"
WINDOWS_PREFLIGHT_HELPER_FILE = REPO_ROOT / "tests" / "speckit-pro" / "run-hosted-windows-preflight.py"
CONTAINER_DISPATCH_HELPER_FILE = REPO_ROOT / "tests" / "speckit-pro" / "run-container-preflight.py"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

CHECKOUT_PIN_RE = re.compile(r"uses: actions/checkout@[0-9a-f]{40}")
UPLOAD_ARTIFACT_PIN = "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
SETUP_PYTHON_PIN = "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405"
HOSTED_PYTHON_VERSION = 'HOSTED_PYTHON_VERSION: "3.13.14"'
CONTAINER_IMAGE_PIN = (
    "python:3.11.15-bookworm@sha256:"
    "b7ae8a4dcc0ab327e333c5e46a3eaa6c1b0ff585bed77e01cd6de4be1325837e"
)
CONTAINER_DISPATCH = (
    'run: import runpy; runpy.run_path("tests/speckit-pro/'
    'run-container-preflight.py", run_name="__main__")'
)
SPEC_KIT_VERSION_PIN = "SPEC_KIT_VERSION: v0.8.13"
SPEC_KIT_REF_PIN = (
    "SPEC_KIT_GIT_REF: git+https://github.com/github/spec-kit.git@"
    "b2314680fce898e0a9151b37ad2535d810c93eef"
)
UNIQUE_ARTIFACT_SUFFIX = "-${{ github.run_id }}-${{ github.run_attempt }}"

TITLE_LITERAL = "TITLE: ${{ github.event_name == 'pull_request' && github.event.pull_request.title || inputs.pr_title }}"
BASE_REF_LITERAL = "BASE_REF: ${{ github.event_name == 'pull_request' && github.base_ref || inputs.base_ref }}"

# Ordered check table (1:1 with the frozen baseline). Each entry is
# ``(source, kind, name, payload)`` and emits exactly one counted subTest, in order:
#   "workflow" -> inspect only ``pr-checks.yml``
#   "combined" -> inspect the workflow plus its four Python helper sources
#   "all"    -> every substring in payload must be present in CONTENT
#   "absent" -> every substring in payload must be absent from CONTENT
CONTENT_CHECKS: list[tuple[str, str, str, list[str]]] = [
    # Checks 1-4 (exists, job defined, job name, checkout regex) are emitted as
    # explicit subTests before this table; it resumes at check 5, in order.
    ("workflow", "all", "title validation uses Python release-readiness gate",
     ["release-readiness-live-github.json", "python3 -m speckit_pro_runner"]),
    ("workflow", "all", "title validation supplies title and base evidence", [TITLE_LITERAL, BASE_REF_LITERAL]),
    ("workflow", "all", "workflow validation job is defined", ["validate-workflows:"]),
    ("combined", "all", "workflow validation installs pinned actionlint", [
        'ACTIONLINT_VERSION: "1.7.12"',
        'ACTIONLINT_SHA256: "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"',
        "run: python3 scripts/install-actionlint.py install",
        "https://github.com/rhysd/actionlint/releases/download/",
        "verify_sha256(archive_path, pinned_sha256)",
    ]),
    ("combined", "all", "workflow validation runs actionlint over all workflows", [
        "run: python3 scripts/install-actionlint.py run",
        'workflows_directory.glob("*.yml")',
        "shell=False",
    ]),
    ("combined", "all", "Python-gated plugin matrix is emitted", [
        "Emit Python-gated plugin matrix",
        "run: python3 scripts/emit-plugin-matrix.py",
        'PLUGINS = ("speckit-pro",)',
    ]),
    ("workflow", "all", "workflow_dispatch trigger is defined", ["workflow_dispatch:"]),
    ("workflow", "all", "dispatched PR checks identify the PR number",
     ['run-name: "PR Checks #', "inputs.pr_number"]),
    ("workflow", "all", "workflow_dispatch accepts PR check inputs", ["pr_number:", "pr_title:", "base_ref:"]),
    ("workflow", "all", "detect supports dispatched release PR checks", [
        "github.event_name == 'workflow_dispatch' || github.event.pull_request.draft == false",
        "github.event_name == 'pull_request' && github.base_ref || inputs.base_ref",
    ]),
    ("workflow", "all", "title validation supports dispatched release PR checks",
     ["github.event_name == 'pull_request' && github.event.pull_request.title || inputs.pr_title"]),
    ("workflow", "all", "sentinel depends on detect, test, and artifact-consistency jobs",
     ["needs: [detect, test, artifact-consistency]"]),
    ("workflow", "all", "sentinel checks the artifact-consistency result", [
        "ARTIFACT_RESULT: ${{ needs.artifact-consistency.result }}",
        "run: python3 scripts/check-pr-workflow-results.py",
    ]),
    ("workflow", "all", "sentinel runs if: always()", ["if: always()"]),
    ("workflow", "all", "sentinel has only checkout read permission", [
        "validate-plugins:",
        "contents: read",
    ]),
    ("workflow", "absent", "latest jq job is deferred", ["test-latest-jq:", "latest_jq_result"]),
    ("workflow", "all", "test job dispatches runner toolchain gate",
     ["run-toolchain-preflight.json", 'PYTHONPATH="${PLUGIN}" python3 -m speckit_pro_runner']),
    ("workflow", "all", "test job dispatches runner default suite gate",
     ["run-default-suite.json", 'PYTHONPATH="${PLUGIN}" python3 -m speckit_pro_runner']),
    ("workflow", "all", "docs validation dispatches runner toolchain preflight",
     ["Report docs toolchain",
      "run-toolchain-preflight-docs.json"]),
    ("workflow", "absent", "docs validation does not dispatch bash toolchain check",
     ["bash tests/speckit-pro/check-toolchain.sh --mode docs"]),
    ("combined", "all", "sentinel checks detect_result for failure", [
        "DETECT_RESULT: ${{ needs.detect.result }}",
        'detect_result in {"failure", "cancelled"}',
    ]),
    ("combined", "all", "sentinel checks test_result for success or skipped", [
        "TEST_RESULT: ${{ needs.test.result }}",
        'test_result not in {"success", "skipped"}',
    ]),
    ("combined", "all", "sentinel exits 0 on success or skipped", [
        "Plugin tests passed or were skipped",
        'artifact_result not in {"success", "skipped"}',
    ]),
    ("combined", "all", "sentinel exits 1 on detect failure", ['"failure"']),
    ("combined", "all", "sentinel exits 1 on detect cancellation", ['"cancelled"']),
]

CONTAINER_JOBS = (
    "changes",
    "linux-amd64-preflight",
    "linux-arm64-preflight",
    "windows-availability",
    "windows-x64-smoke",
    "windows-arm64-smoke",
    "linux-amd64",
    "linux-arm64",
)

LINUX_REQUESTS = (
    "run-toolchain-preflight.json",
    "run-default-suite.json",
    "repository-bash-confinement/requests/repo-bash-confinement.json",
    "runner-gates/requests/release-readiness.json",
    "installed-plugin-release/requests/runner-invocation.json",
    "installed-plugin-release/requests/active-runtime-guard.json",
    "installed-plugin-release/requests/payload-completeness.json",
    "installed-plugin-release/requests/release-readiness.json",
)

EXPECTED_PERMISSIONS = {
    "changes": "contents: read",
    "linux-amd64-preflight": "contents: read",
    "linux-arm64-preflight": "contents: read",
    "windows-availability": "contents: read",
    "windows-x64-smoke": "contents: read",
    "windows-arm64-smoke": "contents: read",
    "linux-amd64": "contents: read",
    "linux-arm64": "contents: read",
}

EXPECTED_UPLOAD_COUNTS = {
    "changes": 1,
    "linux-amd64-preflight": 1,
    "linux-arm64-preflight": 1,
    "windows-availability": 2,
    "windows-x64-smoke": 1,
    "windows-arm64-smoke": 1,
    "linux-amd64": 1,
    "linux-arm64": 1,
}


def _job_block(content: str, job_id: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(job_id)}:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)",
        content,
    )
    return match.group("body") if match else ""


def _yaml_valid(path: Path) -> bool:
    return _yaml_syntax_sane(path.read_text(encoding="utf-8"))


def _required_sentinel_passes(changes: str, run_preflight: str, heavy: str) -> bool:
    if changes != "success":
        return False
    if run_preflight == "true":
        return heavy == "success"
    return heavy == "skipped"


class ValidatePrChecksSentinel(unittest.TestCase):
    def test_sentinel(self) -> None:
        with self.subTest(msg="pr-checks.yml exists"):
            self.assertTrue(WORKFLOW_FILE.is_file(), f"file not found: {WORKFLOW_FILE}")

        content = WORKFLOW_FILE.read_text(encoding="utf-8") if WORKFLOW_FILE.is_file() else ""
        helper_files = (
            ACTIONLINT_HELPER_FILE,
            DOCS_CLASSIFIER_FILE,
            RESULTS_HELPER_FILE,
            MATRIX_HELPER_FILE,
        )
        helper_contents = {
            path: path.read_text(encoding="utf-8") if path.is_file() else ""
            for path in helper_files
        }
        sources = {
            "workflow": content,
            "combined": "\n".join((content, *helper_contents.values())),
        }

        with self.subTest(msg="validate-plugins job is defined"):
            self.assertIn("validate-plugins:", content)
        with self.subTest(msg="validate-plugins has name: validate-plugins"):
            self.assertIn("name: validate-plugins", content)

        with self.subTest(msg="title validation checks out repository history"):
            self.assertTrue(
                CHECKOUT_PIN_RE.search(content) is not None and "fetch-depth: 0" in content,
                "expected validate-pr-title to checkout repository history before inspecting changed files",
            )

        # Remaining substring/absence checks, in frozen baseline order.
        for source, kind, name, needles in CONTENT_CHECKS:
            with self.subTest(msg=name):
                selected_content = sources[source]
                if kind == "all":
                    missing = [n for n in needles if n not in selected_content]
                    self.assertEqual([], missing, f"missing expected content: {missing}")
                else:  # "absent"
                    present = [n for n in needles if n in selected_content]
                    self.assertEqual([], present, f"unexpected content present: {present}")

        with self.subTest(msg="all GitHub workflow files are valid YAML"):
            valid_nested_step = """\
name: Valid
jobs:
  probe:
    runs-on: ubuntu-latest
    steps:
      - name: Probe
        run: echo valid
"""
            under_indented_step = """\
name: Invalid
jobs:
  probe:
    runs-on: ubuntu-latest
    steps:
      - name: Probe
      run: echo invalid
"""
            malformed = "name: Invalid\njobs:\n  probe:\n    runs-on: [ubuntu-latest\n"
            self.assertTrue(
                _yaml_syntax_sane(valid_nested_step),
                "stdlib YAML sanity check rejected a valid nested workflow step",
            )
            self.assertFalse(
                _yaml_syntax_sane(under_indented_step),
                "stdlib YAML sanity check accepted an under-indented step child",
            )
            self.assertFalse(
                _yaml_syntax_sane(malformed),
                "stdlib YAML sanity check accepted an unterminated flow sequence",
            )
            failures = [p.name for p in sorted(WORKFLOWS_DIR.glob("*.yml")) if not _yaml_valid(p)]
            self.assertEqual([], failures, f"GitHub workflow YAML syntax validation failed for: {failures}")

            missing_helpers = [str(path.relative_to(REPO_ROOT)) for path in helper_files if not path.is_file()]
            self.assertEqual([], missing_helpers, f"PR Checks helper files are missing: {missing_helpers}")
            for path, helper_content in helper_contents.items():
                compile(helper_content, str(path), "exec")
                self.assertNotIn("shell=True", helper_content)

            self.assertIn(
                "run: PYTHONDONTWRITEBYTECODE=1 python3 "
                "scripts/refresh-release-artifacts.py --check",
                content,
            )
            self.assertIn("run: python3 scripts/classify-docs-validation.py", content)
            self.assertNotRegex(content, r"(?m)^\s*run:\s*[|>]\s*$")
            self.assertNotRegex(
                content,
                r"(?mi)^\s*shell:\s*(?:sh|bash|zsh|pwsh|powershell)\s*$",
            )
            self.assertNotRegex(content, r"(?i)(?:^|[\s\"'=])[^\s\"']+\.(?:sh|bash|zsh)\b")
            direct_jq = re.compile(r"(?<![\w-])jq(?![\w-])")
            self.assertNotRegex(content, direct_jq)
            self.assertIsNone(direct_jq.search("gh pr view 123 --jq .title"))
            self.assertIsNotNone(direct_jq.search("jq -r .title result.json"))

            run_commands = re.findall(r"(?m)^\s+run:\s*([^\n]+)$", content)
            self.assertTrue(run_commands)
            for command in run_commands:
                for shell_token in ("|", "&", ";", "<<", ">", "$(", "<(", "`", "*"):
                    self.assertNotIn(shell_token, command, f"shell logic in run command: {command}")
                match = re.match(
                    r"^(?:[A-Z_][A-Z0-9_]*=(?:\"[^\"]*\"|'[^']*'|\S+)\s+)*"
                    r"(?P<executable>\S+)",
                    command,
                )
                self.assertIsNotNone(match, f"unable to classify run command: {command}")
                executable = match.group("executable") if match else ""
                self.assertIn(
                    executable,
                    {"python", "python3", "node", "pnpm", "corepack"},
                    f"run command is not a thin Python/Node/pnpm dispatch: {command}",
                )

            sentinel_block = _job_block(content, "validate-plugins")
            self.assertRegex(sentinel_block, r"(?m)^    permissions:\n      contents: read$")
            self.assertIn("persist-credentials: false", sentinel_block)

            actionlint_content = helper_contents[ACTIONLINT_HELPER_FILE]
            self.assertNotIn("extractall(", actionlint_content)
            self.assertNotIn("archive.extract(", actionlint_content)
            self.assertIn("archive.extractfile(member)", actionlint_content)
            self.assertIn("sorted_workflow_files", actionlint_content)
            self.assertIn("shell=False", actionlint_content)

            docs_content = helper_contents[DOCS_CLASSIFIER_FILE]
            self.assertIn('["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"]', docs_content)
            for output_name in (
                "should_validate_docs",
                "validation_mode",
                "rendered_docs",
                "generated_reference",
                "docs_contract",
            ):
                self.assertIn(output_name, docs_content)

            self.assertNotIn("git add -A", content)
            self.assertNotIn("sha256sum", content)
            self.assertNotIn("curl ", content)
            self.assertNotIn("tar ", content)

    def test_container_preflight(self) -> None:
        with self.subTest(msg="container-preflight.yml exists"):
            self.assertTrue(
                CONTAINER_WORKFLOW_FILE.is_file(),
                f"file not found: {CONTAINER_WORKFLOW_FILE}",
            )

        content = (
            CONTAINER_WORKFLOW_FILE.read_text(encoding="utf-8")
            if CONTAINER_WORKFLOW_FILE.is_file()
            else ""
        )
        dispatch_content = (
            CONTAINER_DISPATCH_HELPER_FILE.read_text(encoding="utf-8")
            if CONTAINER_DISPATCH_HELPER_FILE.is_file()
            else ""
        )
        trigger_block = content.split("permissions:", 1)[0]

        with self.subTest(msg="container preflight always reports on pull requests"):
            self.assertIn("pull_request:", trigger_block)
            self.assertNotIn("paths:", trigger_block)

        with self.subTest(msg="container preflight supports manual dispatch"):
            self.assertIn("workflow_dispatch:", trigger_block)

        with self.subTest(msg="container preflight has workflow permissions empty"):
            self.assertRegex(content, r"(?m)^permissions: \{\}$")

        with self.subTest(msg="change detector owns the heavy preflight decision"):
            block = _job_block(content, "changes")
            self.assertIn("run_preflight:", block)
            self.assertIn("steps.changes.outputs.run_preflight", block)
            self.assertIn("fetch-depth: 0", block)
            self.assertIn("persist-credentials: false", block)
            self.assertIn("PREFLIGHT_OPERATION: detect-changes", block)
            self.assertIn("shell: python", block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertTrue(
                CONTAINER_DISPATCH_HELPER_FILE.is_file(),
                f"file not found: {CONTAINER_DISPATCH_HELPER_FILE}",
            )
            compile(dispatch_content, str(CONTAINER_DISPATCH_HELPER_FILE), "exec")
            self.assertIn('["merge-base", base_sha, head_sha]', dispatch_content)
            self.assertIn('["diff", "--no-renames", "--name-only", merge_base, head_sha]', dispatch_content)
            self.assertIn("merge-base.txt", dispatch_content)
            for path in ("speckit-pro/speckit_pro_runner/", "tests/speckit-pro/", ".github/workflows/"):
                self.assertIn(path, dispatch_content)

        with self.subTest(msg="Linux amd64 heavy preflight is job-level conditional"):
            block = _job_block(content, "linux-amd64-preflight")
            self.assertIn("needs.changes.outputs.run_preflight == 'true'", block)
            self.assertIn("container:", block)
            self.assertIn(f"image: {CONTAINER_IMAGE_PIN}", block)
            self.assertIn("runs-on: ubuntu-24.04", block)
            self.assertIn("4d216ad3beb5b697c4049071c82fc375acb8abad", content)
            self.assertIn("the job userland is Debian", content)
            self.assertNotIn(SETUP_PYTHON_PIN, block)
            self.assertNotIn("apt-get", block)
            self.assertIn("id: checkout", block)
            self.assertIn("persist-credentials: false", block)
            self.assertIn("if: steps.checkout.outcome == 'success'", block)
            self.assertIn("PREFLIGHT_OPERATION: linux-gates", block)
            self.assertIn("PREFLIGHT_ROLE: linux-amd64", block)
            self.assertIn("shell: python", block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertIn("EVIDENCE_DIR: /tmp/container-preflight-linux-amd64", block)
            self.assertIn("path: ${{ env.EVIDENCE_DIR }}", block)
            self.assertNotIn("RUNNER_TEMP", block)
            self.assertNotIn("${{ runner.temp }}", block)
            self.assertNotIn("- name: Checkout repository\n        if: always()", block)

        with self.subTest(msg="Linux arm64 heavy preflight is job-level conditional"):
            block = _job_block(content, "linux-arm64-preflight")
            self.assertIn("needs.changes.outputs.run_preflight == 'true'", block)
            self.assertIn("runs-on: ubuntu-24.04-arm", block)
            self.assertIn("container:", block)
            self.assertIn(f"image: {CONTAINER_IMAGE_PIN}", block)
            self.assertNotIn(SETUP_PYTHON_PIN, block)
            self.assertNotIn("apt-get", block)
            self.assertIn("id: checkout", block)
            self.assertIn("persist-credentials: false", block)
            self.assertIn("if: steps.checkout.outcome == 'success'", block)
            self.assertIn("PREFLIGHT_OPERATION: linux-gates", block)
            self.assertIn("PREFLIGHT_ROLE: linux-arm64", block)
            self.assertIn("shell: python", block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertIn("EVIDENCE_DIR: /tmp/container-preflight-linux-arm64", block)
            self.assertIn("path: ${{ env.EVIDENCE_DIR }}", block)
            self.assertNotIn("RUNNER_TEMP", block)
            self.assertNotIn("${{ runner.temp }}", block)
            self.assertNotIn("- name: Checkout repository\n        if: always()", block)

        with self.subTest(msg="Linux amd64 runs current Python gate entrypoints"):
            block = _job_block(content, "linux-amd64-preflight")
            self.assertIn("PREFLIGHT_ROLE: linux-amd64", block)
            self.assertIn('[sys.executable, "-m", "speckit_pro_runner"]', dispatch_content)
            for request in LINUX_REQUESTS:
                self.assertIn(request, dispatch_content)
            request_positions = [dispatch_content.index(request) for request in LINUX_REQUESTS]
            self.assertEqual(request_positions, sorted(request_positions))
            self.assertIn('child_env["SPECKIT_SKIP_TOOLCHAIN_CHECK"] = "1"', dispatch_content)

        with self.subTest(msg="Linux arm64 runs current Python gate entrypoints"):
            block = _job_block(content, "linux-arm64-preflight")
            self.assertIn("PREFLIGHT_ROLE: linux-arm64", block)
            self.assertIn('[sys.executable, "-m", "speckit_pro_runner"]', dispatch_content)
            for request in LINUX_REQUESTS:
                self.assertIn(request, dispatch_content)
            self.assertIn('"container_userland": "Debian Bookworm"', dispatch_content)

        with self.subTest(msg="Linux amd64 required check is an always sentinel"):
            block = _job_block(content, "linux-amd64")
            self.assertIn("name: container-preflight-linux-amd64", block)
            self.assertIn("if: always()", block)
            self.assertIn("needs.linux-amd64-preflight.result", block)
            self.assertIn("PREFLIGHT_OPERATION: sentinel", block)
            self.assertIn("PREFLIGHT_ROLE: linux-amd64-required", block)
            self.assertIn("shell: python", block)
            self.assertIn(CONTAINER_DISPATCH, block)
            for condition in (
                'if changes_result != "success":',
                'if run_preflight == "true":',
                'return heavy_result == "success"',
                'return run_preflight == "false" and heavy_result == "skipped"',
            ):
                self.assertIn(condition, dispatch_content)
            self.assertEqual(
                [True, False, False, True, False, False, False],
                [
                    _required_sentinel_passes("success", "true", "success"),
                    _required_sentinel_passes("success", "true", "failure"),
                    _required_sentinel_passes("success", "true", "cancelled"),
                    _required_sentinel_passes("success", "false", "skipped"),
                    _required_sentinel_passes("success", "false", "success"),
                    _required_sentinel_passes("failure", "true", "success"),
                    _required_sentinel_passes("cancelled", "false", "skipped"),
                ],
            )

        with self.subTest(msg="Linux arm64 required check is an always sentinel"):
            block = _job_block(content, "linux-arm64")
            self.assertIn("name: container-preflight-linux-arm64", block)
            self.assertIn("if: always()", block)
            self.assertIn("needs.linux-arm64-preflight.result", block)
            self.assertIn("PREFLIGHT_OPERATION: sentinel", block)
            self.assertIn("PREFLIGHT_ROLE: linux-arm64-required", block)
            self.assertIn("shell: python", block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertIn('"verdict": "pass" if passed else "fail"', dispatch_content)

        with self.subTest(msg="Windows availability is configured on an Ubuntu control job"):
            block = _job_block(content, "windows-availability")
            self.assertIn("runs-on: ubuntu-latest", block)
            self.assertIn("XPLAT_WINDOWS_X64_ENABLED", block)
            self.assertIn("XPLAT_WINDOWS_ARM64_ENABLED", block)
            self.assertNotIn("XPLAT_WINDOWS_ARM64_AVAILABLE", block)
            self.assertIn(SETUP_PYTHON_PIN, block)
            self.assertIn("persist-credentials: false", block)
            self.assertIn("PREFLIGHT_OPERATION: windows-availability", block)
            self.assertIn("shell: python", block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertEqual(1, trigger_block.count("default: true"))
            self.assertEqual(1, trigger_block.count("default: false"))
            for label in ("windows-2025", "windows-11-arm"):
                self.assertIn(f'"runner_label": "{label}"', dispatch_content)
            self.assertIn('"hosted_label_status": "stable"', dispatch_content)
            self.assertIn('"hosted_label_status": "public_preview"', dispatch_content)
            self.assertIn('"available": True', dispatch_content)
            self.assertIn('x64_source = "stable_label_default"', dispatch_content)
            self.assertIn('arm64_source = "public_preview_default"', dispatch_content)
            self.assertIn('arm64_enabled = "false"', dispatch_content)
            self.assertEqual(2, dispatch_content.count('= "repository_variable_disable"'))
            self.assertIn('"x64_enabled": x64_enabled', dispatch_content)
            self.assertIn('"arm64_enabled": arm64_enabled', dispatch_content)
            self.assertLess(
                dispatch_content.index('if event_name == "workflow_dispatch":'),
                dispatch_content.index('if repo_x64 == "false":'),
            )
            self.assertIn("windows_x64_enabled", trigger_block)
            self.assertIn("windows_arm64_enabled", trigger_block)

        with self.subTest(msg="Windows x64 smoke is advisory and conditionally queued"):
            block = _job_block(content, "windows-x64-smoke")
            self.assertIn("continue-on-error: true", block)
            self.assertIn("needs.windows-availability.outputs.x64_enabled == 'true'", block)
            self.assertIn("runs-on: windows-2025", block)
            self.assertIn(SETUP_PYTHON_PIN, block)
            self.assertIn("python-version: ${{ env.HOSTED_PYTHON_VERSION }}", block)
            self.assertIn("id: checkout", block)
            self.assertIn("persist-credentials: false", block)
            self.assertIn("if: always() && steps.checkout.outcome == 'success'", block)
            self.assertIn("PREFLIGHT_OPERATION: windows-smoke", block)
            self.assertIn("PREFLIGHT_ROLE: windows-x64", block)
            self.assertIn("shell: python", block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertNotIn("- name: Checkout repository\n        if: always()", block)

        with self.subTest(msg="Windows ARM64 smoke is advisory and conditionally queued"):
            block = _job_block(content, "windows-arm64-smoke")
            self.assertIn("continue-on-error: true", block)
            self.assertIn("needs.windows-availability.outputs.arm64_enabled == 'true'", block)
            self.assertIn("runs-on: windows-11-arm", block)
            self.assertIn(SETUP_PYTHON_PIN, block)
            self.assertIn("python-version: ${{ env.HOSTED_PYTHON_VERSION }}", block)
            self.assertIn("id: checkout", block)
            self.assertIn("persist-credentials: false", block)
            self.assertIn("if: always() && steps.checkout.outcome == 'success'", block)
            self.assertIn("PREFLIGHT_OPERATION: windows-smoke", block)
            self.assertIn("PREFLIGHT_ROLE: windows-arm64", block)
            self.assertIn("shell: python", block)
            self.assertIn(CONTAINER_DISPATCH, block)
            self.assertNotIn("- name: Checkout repository\n        if: always()", block)

        with self.subTest(msg="Windows smoke runs interpreter discovery runtime-info and preflight"):
            self.assertTrue(
                WINDOWS_PREFLIGHT_HELPER_FILE.is_file(),
                f"file not found: {WINDOWS_PREFLIGHT_HELPER_FILE}",
            )
            helper_content = (
                WINDOWS_PREFLIGHT_HELPER_FILE.read_text(encoding="utf-8")
                if WINDOWS_PREFLIGHT_HELPER_FILE.is_file()
                else ""
            )
            compile(helper_content, str(WINDOWS_PREFLIGHT_HELPER_FILE), "exec")
            for expected in (
                '"operation": "runtime-info"',
                '"operation": "preflight"',
                "runtime-info.json",
                "preflight.json",
                "specify-version.txt",
                "specify_version_compatible",
                "runtime_info_diagnostics",
                "preflight_diagnostics",
                "preflight_metadata_status",
                "runner_metadata_mismatch",
                "IMMUTABLE_SPEC_KIT_REF_RE",
                'f"pipx=={args.pipx_version}"',
                "shell=False",
            ):
                self.assertIn(expected, helper_content)
            self.assertIn(HOSTED_PYTHON_VERSION, content)
            self.assertIn(SETUP_PYTHON_PIN, content)
            self.assertIn("3.13.14-27320626148", content)
            self.assertIn('PIPX_VERSION: "1.15.0"', content)
            self.assertIn(SPEC_KIT_VERSION_PIN, content)
            self.assertIn(SPEC_KIT_REF_PIN, content)
            self.assertNotIn("spec-kit.git@v0.8.13", content)
            for job_id in ("windows-x64-smoke", "windows-arm64-smoke"):
                block = _job_block(content, job_id)
                self.assertIn(SETUP_PYTHON_PIN, block)
                self.assertNotIn("PREFLIGHT_INTERPRETER_CANDIDATE", block)
                self.assertIn("PREFLIGHT_OPERATION: windows-smoke", block)
                self.assertIn(CONTAINER_DISPATCH, block)
                self.assertNotIn("-m pipx", block)
                self.assertNotIn('operation = "runtime-info"', block)
                self.assertNotIn('operation = "preflight"', block)
                self.assertNotIn("specifyCommand", block)
            candidates = ('"py -V:3"', '"py -3"', '"python"', '"python3"')
            candidate_positions = [dispatch_content.index(candidate) for candidate in candidates]
            self.assertEqual(candidate_positions, sorted(candidate_positions))
            self.assertIn("interpreter-probes.json", dispatch_content)
            self.assertIn("architecture_emulated", dispatch_content)
            self.assertIn('child_env["PREFLIGHT_INTERPRETER_CANDIDATE"] = selected', dispatch_content)
            for expected in (
                "run-hosted-windows-preflight.py",
                '"--pipx-version"',
                '"--spec-kit-version"',
                '"--spec-kit-ref"',
            ):
                self.assertIn(expected, dispatch_content)

        with self.subTest(msg="every container preflight job declares minimal permissions"):
            failures = []
            for job_id, expected in EXPECTED_PERMISSIONS.items():
                block = _job_block(content, job_id)
                if expected == "{}":
                    valid = re.search(r"(?m)^    permissions: \{\}$", block) is not None
                else:
                    valid = re.search(
                        rf"(?m)^    permissions:\n      {re.escape(expected)}$",
                        block,
                    ) is not None
                if not valid or re.search(r"(?m)^\s+[A-Za-z-]+: write$", block):
                    failures.append(job_id)
            self.assertEqual([], failures, f"jobs with incorrect permissions: {failures}")

        with self.subTest(msg="every container preflight job uploads evidence with always semantics"):
            failures = []
            artifact_names = []
            for job_id, expected_count in EXPECTED_UPLOAD_COUNTS.items():
                block = _job_block(content, job_id)
                upload_steps = [
                    step
                    for step in re.split(r"(?m)(?=^      - name: )", block)
                    if UPLOAD_ARTIFACT_PIN in step
                ]
                artifact_names.extend(
                    match.group(1)
                    for step in upload_steps
                    if (match := re.search(r"(?m)^\s+name: (container-preflight-[^\n]+)$", step))
                )
                if len(upload_steps) != expected_count or any(
                    "if: always()" not in step
                    or "continue-on-error: true" not in step
                    or "if-no-files-found: error" not in step
                    or UNIQUE_ARTIFACT_SUFFIX not in step
                    or "overwrite: true" in step
                    for step in upload_steps
                ):
                    failures.append(job_id)
            self.assertEqual([], failures, f"jobs with incorrect evidence uploads: {failures}")
            self.assertEqual(sum(EXPECTED_UPLOAD_COUNTS.values()), len(artifact_names))
            self.assertEqual(len(artifact_names), len(set(artifact_names)))

        with self.subTest(msg="evidence uploads cannot mask or flip role verdicts"):
            upload_count = sum(EXPECTED_UPLOAD_COUNTS.values())
            self.assertEqual(upload_count, content.count(f"uses: {UPLOAD_ARTIFACT_PIN}"))
            self.assertEqual(6, content.count(f"uses: {SETUP_PYTHON_PIN}"))
            self.assertEqual(6, content.count("# v6.2.0"))
            self.assertEqual(2, content.count(f"image: {CONTAINER_IMAGE_PIN}"))
            action_refs = re.findall(r"(?m)^\s+uses: ([^\s]+)", content)
            self.assertTrue(action_refs)
            self.assertTrue(all(re.search(r"@[0-9a-f]{40}$", ref) for ref in action_refs))
            self.assertEqual(
                upload_count + 2,
                content.count("continue-on-error: true"),
                "only nine upload steps and two Windows advisory jobs may continue on error",
            )

        with self.subTest(msg="container preflight dispatches no repo-local shell helper"):
            self.assertIsNone(
                re.search(r"(?i)(?:scripts|tests|speckit-pro)/[^\s\"']+\.(?:sh|bash|zsh|ps1|bat|cmd)\b", content)
            )
            self.assertNotRegex(content, r"(?i)(?<![\w-])jq(?![\w-])")
            self.assertNotRegex(content, r"(?m)^\s*shell:\s*(?:bash|pwsh)\s*$")
            self.assertNotIn("apt-get", content)
            self.assertNotIn("run: |", content)
            self.assertNotIn("$(", content)
            self.assertEqual(len(CONTAINER_JOBS), content.count("shell: python"))
            self.assertEqual(len(CONTAINER_JOBS), content.count(CONTAINER_DISPATCH))
            self.assertIn("shell=False", dispatch_content)
            self.assertNotIn("shell=True", dispatch_content)

def build_suite() -> unittest.TestSuite:
    return unittest.TestSuite(
        [
            ValidatePrChecksSentinel("test_sentinel"),
            ValidatePrChecksSentinel("test_container_preflight"),
        ]
    )


def main() -> int:
    return run_counted(build_suite(), label="validate-pr-checks-sentinel")


if __name__ == "__main__":
    raise SystemExit(main())
