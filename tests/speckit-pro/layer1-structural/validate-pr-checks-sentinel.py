#!/usr/bin/env python3
"""`validate-plugins` sentinel-job validation (port of validate-pr-checks-sentinel.sh).

XPLAT-010 count-parity port (T032, US2). The module imports only the Python
3.11+ standard library; YAML validation intentionally preserves the predecessor's
optional PyYAML/Ruby subprocess delegation described below.
Verifies ``.github/workflows/pr-checks.yml`` defines the ``validate-plugins``
sentinel with the correct triggers, dispatch inputs, Python-runner gate steps,
and sentinel logic, then folds a glob of every ``.github/workflows/*.yml`` into a
single "valid YAML" outcome. Every former ``assert_*``/``_pass``/``_fail``
execution maps to one counted ``subTest`` unit; names reproduced verbatim via
``subTest(msg=...)`` for a 1:1 baseline match.

YAML validity (check 28): the bash predecessor validated each workflow via
``python3 -c "import yaml,…"`` with a ``ruby`` fallback. The port keeps its own
module stdlib-only and reproduces that exact mechanism through ``subprocess``
(argv list, ``shell=False``) — no new runtime dependency, identical pass/fail
folding. ``python3``/``ruby`` are outside the bash-scoped confinement vocabulary.

PR 5 later updates this ported validator for the CI dispatch swap (tasks T049).

PR 5 extends the ported validator for the docs-toolchain CI dispatch swap.

Baseline: ``tests/speckit-pro/parity/bash-to-python/validate-pr-checks-sentinel-baseline.txt``
(TOTAL: 30).
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "pr-checks.yml"
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
     ["Report docs toolchain", "run-toolchain-preflight-docs.json"]),
    ("absent", "docs validation does not dispatch bash toolchain check",
     ["bash tests/speckit-pro/check-toolchain.sh --mode docs"]),
    ("all", "sentinel checks detect_result for failure", ["detect_result"]),
    ("all", "sentinel checks test_result for success or skipped", ["test_result"]),
    ("all", "sentinel exits 0 on success or skipped", ['"success" || "$test_result" == "skipped"']),
    ("all", "sentinel exits 1 on detect failure", ['"failure"']),
    ("all", "sentinel exits 1 on detect cancellation", ['"cancelled"']),
]


def _yaml_valid(path: Path) -> bool:
    """Mirror the bash python-yaml-then-ruby validity check for one workflow file."""
    content = path.read_bytes()
    py = subprocess.run(
        [sys.executable, "-c", "import yaml, sys; yaml.safe_load(sys.stdin)"],
        input=content,
        capture_output=True,
        shell=False,
        check=False,
    )
    if py.returncode == 0:
        return True
    try:
        rb = subprocess.run(
            ["ruby", "-e", "require 'yaml'; YAML.load_file(ARGV.fetch(0))", str(path)],
            capture_output=True,
            shell=False,
            check=False,
        )
    except FileNotFoundError:
        return False
    return rb.returncode == 0


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
            failures = [p.name for p in sorted(WORKFLOWS_DIR.glob("*.yml")) if not _yaml_valid(p)]
            self.assertEqual([], failures, f"GitHub workflow YAML syntax validation failed for: {failures}")


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidatePrChecksSentinel)


def main() -> int:
    return run_counted(build_suite(), label="validate-pr-checks-sentinel")


if __name__ == "__main__":
    raise SystemExit(main())
