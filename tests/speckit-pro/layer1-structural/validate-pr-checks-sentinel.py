#!/usr/bin/env python3
"""`validate-plugins` sentinel-job validation (port of validate-pr-checks-sentinel.sh).

XPLAT-010 count-parity port (T032, US2). The module imports only the Python
3.11+ standard library; YAML validation intentionally preserves the predecessor's
optional PyYAML/Ruby subprocess delegation described below.
Verifies ``.github/workflows/pr-checks.yml`` defines the ``validate-plugins``
sentinel with the correct triggers, dispatch inputs, Python-runner gate steps,
and sentinel logic. XPLAT-010 PR 11 extends the same structural boundary to
``container-preflight.yml``: always-triggered PR reporting, lightweight change
detection, conditional heavy jobs, stable Linux required-check sentinels,
configured Windows availability, and always-run evidence uploads. The validator
then folds every ``.github/workflows/*.yml`` into one "valid YAML" outcome.

YAML syntax: the shell predecessor used optional non-stdlib YAML parsers
(``python -c import yaml`` or Ruby). This port is intentionally stdlib-only per
XPLAT-010, so it applies a conservative GitHub-workflow YAML sanity check that
guards indentation, mapping/sequence structure, and block-scalar boundaries
without adding PyYAML/Ruby as runtime dependencies.

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
CONTAINER_WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "container-preflight.yml"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

CHECKOUT_PIN_RE = re.compile(r"uses: actions/checkout@[0-9a-f]{40}")

TITLE_LITERAL = "TITLE: ${{ github.event_name == 'pull_request' && github.event.pull_request.title || inputs.pr_title }}"
BASE_REF_LITERAL = "BASE_REF: ${{ github.event_name == 'pull_request' && github.base_ref || inputs.base_ref }}"

# Ordered check table (1:1 with the frozen baseline). Each entry is
# ``(kind, name, payload)`` and emits exactly one counted subTest, in order:
#   "all"    -> every substring in payload must be present in CONTENT
#   "absent" -> every substring in payload must be absent from CONTENT
CONTENT_CHECKS: list[tuple[str, str, list[str]]] = [
    # Checks 1-4 (exists, job defined, job name, checkout regex) are emitted as
    # explicit subTests before this table; it resumes at check 5, in order.
    ("all", "title validation uses Python release-readiness gate",
     ["release-readiness-live-github.json", "python3 -m speckit_pro_runner"]),
    ("all", "title validation supplies title and base evidence", [TITLE_LITERAL, BASE_REF_LITERAL]),
    ("all", "workflow validation job is defined", ["validate-workflows:"]),
    ("all", "workflow validation installs pinned actionlint", [
        'ACTIONLINT_VERSION: "1.7.12"',
        'ACTIONLINT_SHA256: "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"',
        "https://github.com/rhysd/actionlint/releases/download/v",
        "sha256sum -c",
    ]),
    ("all", "workflow validation runs actionlint over all workflows",
     ['"${RUNNER_TEMP}/actionlint" .github/workflows/*.yml']),
    ("all", "Python-gated plugin matrix is emitted",
     ["Emit Python-gated plugin matrix", 'plugins=["speckit-pro"]']),
    ("all", "workflow_dispatch trigger is defined", ["workflow_dispatch:"]),
    ("all", "dispatched PR checks identify the PR number",
     ['run-name: "PR Checks #', "inputs.pr_number"]),
    ("all", "workflow_dispatch accepts PR check inputs", ["pr_number:", "pr_title:", "base_ref:"]),
    ("all", "detect supports dispatched release PR checks", [
        "github.event_name == 'workflow_dispatch' || github.event.pull_request.draft == false",
        "github.event_name == 'pull_request' && github.base_ref || inputs.base_ref",
    ]),
    ("all", "title validation supports dispatched release PR checks",
     ["github.event_name == 'pull_request' && github.event.pull_request.title || inputs.pr_title"]),
    ("all", "sentinel depends on detect, test, and artifact-consistency jobs",
     ["needs: [detect, test, artifact-consistency]"]),
    ("all", "sentinel checks the artifact-consistency result",
     ['artifact_result="${{ needs.artifact-consistency.result }}"']),
    ("all", "sentinel runs if: always()", ["if: always()"]),
    ("all", "sentinel has permissions: {}", ["permissions: {}"]),
    ("absent", "latest jq job is deferred", ["test-latest-jq:", "latest_jq_result"]),
    ("all", "test job dispatches runner toolchain gate",
     ["run-toolchain-preflight.json", 'PYTHONPATH="${PLUGIN}" python3 -m speckit_pro_runner']),
    ("all", "test job dispatches runner default suite gate",
     ["run-default-suite.json", 'PYTHONPATH="${PLUGIN}" python3 -m speckit_pro_runner']),
    ("all", "docs validation dispatches runner toolchain preflight",
     ["Report docs toolchain",
      "run-toolchain-preflight-docs.json"]),
    ("absent", "docs validation does not dispatch bash toolchain check",
     ["bash tests/speckit-pro/check-toolchain.sh --mode docs"]),
    ("all", "sentinel checks detect_result for failure", ["detect_result"]),
    ("all", "sentinel checks test_result for success or skipped", ["test_result"]),
    ("all", "sentinel exits 0 on success or skipped", ['"success" || "$test_result" == "skipped"']),
    ("all", "sentinel exits 1 on detect failure", ['"failure"']),
    ("all", "sentinel exits 1 on detect cancellation", ['"cancelled"']),
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
    "installed-plugin-release/requests/release-readiness.json",
)

EXPECTED_PERMISSIONS = {
    "changes": "contents: read",
    "linux-amd64-preflight": "contents: read",
    "linux-arm64-preflight": "contents: read",
    "windows-availability": "{}",
    "windows-x64-smoke": "contents: read",
    "windows-arm64-smoke": "contents: read",
    "linux-amd64": "{}",
    "linux-arm64": "{}",
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
        for kind, name, needles in CONTENT_CHECKS:
            with self.subTest(msg=name):
                if kind == "all":
                    missing = [n for n in needles if n not in content]
                    self.assertEqual([], missing, f"missing expected content: {missing}")
                else:  # "absent"
                    present = [n for n in needles if n in content]
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
            for path in ("speckit-pro/speckit_pro_runner/", "tests/speckit-pro/", ".github/workflows/"):
                self.assertIn(path, block)

        with self.subTest(msg="Linux amd64 heavy preflight is job-level conditional"):
            block = _job_block(content, "linux-amd64-preflight")
            self.assertIn("needs.changes.outputs.run_preflight == 'true'", block)
            self.assertIn("container:", block)

        with self.subTest(msg="Linux arm64 heavy preflight is job-level conditional"):
            block = _job_block(content, "linux-arm64-preflight")
            self.assertIn("needs.changes.outputs.run_preflight == 'true'", block)
            self.assertIn("runs-on: ubuntu-24.04-arm", block)
            self.assertIn("container:", block)

        with self.subTest(msg="Linux amd64 runs current Python gate entrypoints"):
            block = _job_block(content, "linux-amd64-preflight")
            self.assertIn("python3 -m speckit_pro_runner", block)
            for request in LINUX_REQUESTS:
                self.assertIn(request, block)

        with self.subTest(msg="Linux arm64 runs current Python gate entrypoints"):
            block = _job_block(content, "linux-arm64-preflight")
            self.assertIn("python3 -m speckit_pro_runner", block)
            for request in LINUX_REQUESTS:
                self.assertIn(request, block)

        with self.subTest(msg="Linux amd64 required check is an always sentinel"):
            block = _job_block(content, "linux-amd64")
            self.assertIn("name: container-preflight-linux-amd64", block)
            self.assertIn("if: always()", block)
            self.assertIn("needs.linux-amd64-preflight.result", block)
            for condition in (
                '[[ "$CHANGES_RESULT" != "success" ]]',
                '[[ "$RUN_PREFLIGHT" == "true" && "$PREFLIGHT_RESULT" != "success" ]]',
                '[[ "$RUN_PREFLIGHT" != "true" && "$PREFLIGHT_RESULT" != "skipped" ]]',
            ):
                self.assertIn(condition, block)
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
            for condition in (
                '[[ "$CHANGES_RESULT" != "success" ]]',
                '[[ "$RUN_PREFLIGHT" == "true" && "$PREFLIGHT_RESULT" != "success" ]]',
                '[[ "$RUN_PREFLIGHT" != "true" && "$PREFLIGHT_RESULT" != "skipped" ]]',
            ):
                self.assertIn(condition, block)

        with self.subTest(msg="Windows availability is configured on an Ubuntu control job"):
            block = _job_block(content, "windows-availability")
            self.assertIn("runs-on: ubuntu-latest", block)
            self.assertIn("XPLAT_WINDOWS_X64_ENABLED", block)
            self.assertIn("XPLAT_WINDOWS_ARM64_ENABLED", block)
            self.assertNotIn("XPLAT_WINDOWS_ARM64_AVAILABLE", block)
            self.assertEqual(1, trigger_block.count("default: true"))
            self.assertEqual(1, trigger_block.count("default: false"))
            for label in ("windows-2025", "windows-11-arm"):
                self.assertIn(f'"runner_label":"{label}"', block)
            self.assertIn('"hosted_label_status":"stable"', block)
            self.assertIn('"hosted_label_status":"public_preview"', block)
            self.assertEqual(2, block.count('"available":true'))
            self.assertIn('x64_source="stable_label_default"', block)
            self.assertIn('arm64_source="public_preview_default"', block)
            self.assertIn('arm64_enabled="false"', block)
            self.assertEqual(2, block.count('source="repository_variable_disable"'))
            self.assertIn('"$x64_enabled" "$x64_source"', block)
            self.assertIn('"$arm64_enabled" "$arm64_source"', block)
            self.assertLess(
                block.index('if [[ "$EVENT_NAME" == "workflow_dispatch" ]]'),
                block.index('if [[ "$REPO_X64_ENABLED" == "false" ]]'),
            )
            self.assertIn("windows_x64_enabled", trigger_block)
            self.assertIn("windows_arm64_enabled", trigger_block)

        with self.subTest(msg="Windows x64 smoke is advisory and conditionally queued"):
            block = _job_block(content, "windows-x64-smoke")
            self.assertIn("continue-on-error: true", block)
            self.assertIn("needs.windows-availability.outputs.x64_enabled == 'true'", block)
            self.assertIn("runs-on: windows-2025", block)

        with self.subTest(msg="Windows ARM64 smoke is advisory and conditionally queued"):
            block = _job_block(content, "windows-arm64-smoke")
            self.assertIn("continue-on-error: true", block)
            self.assertIn("needs.windows-availability.outputs.arm64_enabled == 'true'", block)
            self.assertIn("runs-on: windows-11-arm", block)

        with self.subTest(msg="Windows smoke runs interpreter discovery runtime-info and preflight"):
            for job_id in ("windows-x64-smoke", "windows-arm64-smoke"):
                block = _job_block(content, job_id)
                candidates = ('name = "py -V:3"', 'name = "py -3"', 'name = "python"', 'name = "python3"')
                positions = [block.find(candidate) for candidate in candidates]
                self.assertTrue(all(position >= 0 for position in positions))
                self.assertEqual(sorted(positions), positions, "Python discovery order drifted")
                self.assertIn("[int]$version.minor -ge 11", block)
                self.assertIn("missing-python-3.11", block)
                self.assertIn('operation = "runtime-info"', block)
                self.assertIn('operation = "preflight"', block)
                self.assertIn("runtime-info.stderr.txt", block)
                self.assertIn("preflight.stderr.txt", block)
                self.assertIn("1> $runtimeStdout 2> $runtimeStderr", block)
                self.assertIn("1> $preflightStdout 2> $preflightStderr", block)
                self.assertIn('$env:PYTHONUTF8 = "1"', block)
                self.assertNotIn("2>&1", block)
                self.assertNotIn("1> (Join-Path", block)

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
            for job_id, expected_count in EXPECTED_UPLOAD_COUNTS.items():
                block = _job_block(content, job_id)
                upload_steps = [
                    step
                    for step in re.split(r"(?m)(?=^      - name: )", block)
                    if "actions/upload-artifact@v7" in step
                ]
                if len(upload_steps) != expected_count or any(
                    "if: always()" not in step
                    or "continue-on-error: true" not in step
                    or "if-no-files-found: error" not in step
                    for step in upload_steps
                ):
                    failures.append(job_id)
            self.assertEqual([], failures, f"jobs with incorrect evidence uploads: {failures}")

        with self.subTest(msg="evidence uploads cannot mask or flip role verdicts"):
            upload_count = sum(EXPECTED_UPLOAD_COUNTS.values())
            self.assertEqual(upload_count, content.count("uses: actions/upload-artifact@v7"))
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
