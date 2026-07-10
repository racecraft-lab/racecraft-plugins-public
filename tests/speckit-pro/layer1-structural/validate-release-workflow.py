#!/usr/bin/env python3
"""Release workflow structural validation (port of validate-release-workflow.sh).

XPLAT-010 count-parity port (T034, US2). Python 3.11+ standard library only.
Verifies ``.github/workflows/release.yml`` keeps release-please on the PR-backed
payload/marketplace sync path, dispatches PR Checks for release PR branches, and
does not bypass required checks or push generated changes directly to ``main``.
Every former ``assert_*``/``_pass``/``_fail`` execution maps to one counted
``subTest`` unit; names are reproduced verbatim via ``subTest(msg=...)`` for a
1:1 baseline match.

YAML syntax: the shell predecessor used optional non-stdlib YAML parsers
(``python -c import yaml`` or Ruby). This port is intentionally stdlib-only per
XPLAT-010, so it applies a conservative GitHub-workflow YAML sanity check that
guards indentation, mapping/sequence structure, and block-scalar boundaries
without adding PyYAML/Ruby as runtime dependencies.

Baseline: ``tests/speckit-pro/parity/xplat-010/validate-release-workflow-baseline.txt``
(TOTAL: 24).
"""

from __future__ import annotations

import json
import posixpath
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "release.yml"
RESOLVER_FILE = REPO_ROOT / "scripts" / "resolve_release_prs.py"
SYNC_HELPER_FILE = REPO_ROOT / "scripts" / "sync_release_pr.py"
RELEASE_CONFIG_FILE = REPO_ROOT / "release-please-config.json"
CHECKOUT_PIN_RE = re.compile(r"actions/checkout@[0-9a-f]{40}")
MAIN_PUSH_RE = re.compile(r"^\s*git push(\s|$).*(\s|\"|'|:|/)main(\s|\"|'|:|$)", re.MULTILINE)


def _contains_all(text: str, needles: tuple[str, ...]) -> bool:
    return all(needle in text for needle in needles)


def _yaml_syntax_sane(text: str) -> bool:
    """Validate the workflow's YAML surface without a non-stdlib YAML parser.

    This is not a general YAML loader. It catches the syntax regressions this
    structural test is meant to catch: tabs in indentation, non-mapping top-level
    lines, empty mapping keys, unterminated quote/bracket pairs on scalar lines,
    and malformed sequence items. Literal block bodies are skipped until the
    indentation returns to the parent mapping level.
    """
    block_parent_indent: int | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indentation = raw_line[: len(raw_line) - len(raw_line.lstrip())]
        if "\t" in indentation:
            return False
        leading = raw_line[: len(raw_line) - len(raw_line.lstrip(" "))]
        indent = len(leading)
        if block_parent_indent is not None:
            if indent > block_parent_indent:
                continue
            block_parent_indent = None

        stripped = raw_line.strip()
        if stripped.startswith("- "):
            item = stripped[2:].strip()
            if not item:
                continue
            if ":" not in item:
                return False
            key, value = item.split(":", 1)
        else:
            if ":" not in stripped:
                return False
            key, value = stripped.split(":", 1)

        if not key.strip():
            return False
        scalar = value.strip()
        if scalar in {"|", ">", "|-", ">-", "|+", ">+"}:
            block_parent_indent = indent
        if scalar.count("[") != scalar.count("]"):
            return False
        if scalar.count("{") != scalar.count("}"):
            return False
        if scalar.startswith(("'", '"')) and not scalar.endswith(scalar[0]):
            return False
    return True


class ValidateReleaseWorkflow(unittest.TestCase):
    def test_release_workflow(self) -> None:
        with self.subTest(msg="release.yml exists"):
            self.assertTrue(WORKFLOW_FILE.is_file(), f"file not found: {WORKFLOW_FILE}")

        content = WORKFLOW_FILE.read_text(encoding="utf-8") if WORKFLOW_FILE.is_file() else ""

        with self.subTest(msg="release workflow uses release-please"):
            self.assertIn("googleapis/release-please-action@v5", content)

        with self.subTest(msg="release workflow pins checkout actions"):
            self.assertEqual(2, len(CHECKOUT_PIN_RE.findall(content)), "release workflow pinned checkout count")

        with self.subTest(msg="release workflow can dispatch PR checks"):
            self.assertTrue(
                _contains_all(
                    content,
                    (
                        "actions: write",
                        '"gh",',
                        '"workflow",',
                        '"run",',
                        '"pr-checks.yml",',
                        '"--ref",',
                        '"pr_number=" + number',
                        '"pr_title=" + title',
                        '"base_ref=main"',
                    ),
                ),
                "expected release workflow to dispatch PR Checks for release-please PR branches",
            )

        resolver_content = RESOLVER_FILE.read_text(encoding="utf-8") if RESOLVER_FILE.is_file() else ""
        sync_helper_content = SYNC_HELPER_FILE.read_text(encoding="utf-8") if SYNC_HELPER_FILE.is_file() else ""

        with self.subTest(msg="release workflow resolves new or unchanged release PRs for payload sync"):
            self.assertTrue(
                _contains_all(
                    content,
                    (
                        'RELEASE_PRS: ${{ steps.release.outputs.prs }}',
                        "scripts/resolve_release_prs.py",
                        'RELEASE_PRS: ${{ steps.release_prs.outputs.prs }}',
                        "steps.release_prs.outputs.found == 'true'",
                        'release_pr.get("headBranchName") or release_pr.get("headRefName") or ""',
                        "release PR resolver returned no metadata",
                    ),
                ),
                "expected release workflow to normalize release-please output and reconcile unchanged open release PRs",
            )

        with self.subTest(msg="release PR resolver discovers unchanged open Release Please branches"):
            self.assertTrue(
                RESOLVER_FILE.is_file()
                and _contains_all(
                    resolver_content,
                    ('"gh",', '"pr",', '"list",', "release-please--branches--", "headRefName"),
                ),
                "expected resolver fallback to list and filter existing open Release Please PRs",
            )

        with self.subTest(msg="release reconciliation is not gated only on prs_created"):
            self.assertNotIn(
                "steps.release.outputs.prs_created == 'true'",
                content,
                "unchanged open release PRs must reconcile even when release-please reports prs_created=false",
            )

        with self.subTest(msg="release workflow does not depend on pending release labels for payload sync"):
            self.assertNotIn(
                '--label "autorelease: pending"',
                content,
                "release PR payload sync must not depend on a just-created label query",
            )

        with self.subTest(msg="release workflow validates release PR readiness before dispatch"):
            self.assertTrue(
                _contains_all(
                    content,
                    (
                        "Validate release PR readiness",
                        "steps.release_prs.outputs.found == 'true'",
                        'RELEASE_PRS: ${{ steps.release_prs.outputs.prs }}',
                        "release-readiness.json",
                        "Dispatch PR Checks for release PRs",
                    ),
                ),
                "expected release workflow to validate release PR readiness before dispatching PR Checks",
            )

        with self.subTest(msg="release workflow verifies generated test payload evidence"):
            self.assertIn("test-payload-evidence.json", content)

        with self.subTest(msg="release workflow syncs generated artifacts on the release PR"):
            self.assertTrue(
                "scripts/sync_release_pr.py" in content
                and "Sync generated artifacts onto the release PR" in content
                and "bash scripts/sync-marketplace-versions.sh" not in content
                and SYNC_HELPER_FILE.is_file()
                and "scripts/refresh-release-artifacts.py" in sync_helper_content,
                "expected release workflow to refresh generated artifacts via the Python refresh script on the release PR",
            )

        with self.subTest(msg="release workflow sync checks out the release PR branch with the release token"):
            self.assertTrue(
                'token: ${{ secrets.RELEASE_PLEASE_TOKEN || github.token }}' in content
                and "scripts/sync_release_pr.py" in content
                and '["git", "checkout", "-B", branch, remote_branch_sha]' in sync_helper_content,
                "expected release workflow to check out the release PR branch using the release token",
            )

        with self.subTest(msg="release workflow merges current main before regenerating an existing release PR"):
            merge_index = sync_helper_content.find('["git", "merge", "--no-edit", base_sha]')
            refresh_index = sync_helper_content.find('[sys.executable, "scripts/refresh-release-artifacts.py"]')
            self.assertTrue(
                "BASE_REF: main" in content
                and merge_index >= 0
                and refresh_index >= 0
                and merge_index < refresh_index,
                "expected release branch to merge current main before artifact refresh",
            )

        with self.subTest(msg="release workflow pushes main-only reconciliation changes"):
            self.assertTrue(
                _contains_all(
                    sync_helper_content,
                    (
                        '["git", "rev-parse", "FETCH_HEAD"]',
                        "if head_sha == remote_branch_sha:",
                        '["git", "push", "origin", f"HEAD:{branch}"]',
                    ),
                ),
                "expected workflow to push when merging main changed the release branch even if generated files were already current",
            )

        with self.subTest(msg="release workflow guards the artifact sync commit with a dirty check"):
            self.assertTrue(
                '["git", "status", "--porcelain"]' in sync_helper_content
                and "chore(release): sync generated artifacts for release" in sync_helper_content,
                "expected release workflow to commit the artifact sync only when the tree is dirty",
            )

        with self.subTest(msg="release workflow regenerates the docs reference on sync"):
            self.assertIn("pnpm --dir docs-site reference:generate", content)

        with self.subTest(msg="release workflow verifies release artifacts are consistent after publishing"):
            self.assertIn(
                "Verify release artifacts are consistent",
                content,
                "expected release workflow to verify dist/marketplace/docs-reference consistency after a release",
            )

        with self.subTest(msg="release workflow opens NO follow-up payload/marketplace sync PR"):
            self.assertFalse(
                "gh pr create --base main" in content or "release/sync-speckit-pro-v" in content,
                "release workflow must NOT open a follow-up sync PR; the release PR's payload-sync step already commits dist, marketplace versions, and the docs reference",
            )

        with self.subTest(msg="release workflow sync commit does not skip required PR checks"):
            self.assertNotIn("[skip ci]", content)

        with self.subTest(msg="release workflow does not direct-push generated sync changes to main"):
            self.assertIsNone(
                MAIN_PUSH_RE.search(content),
                "release workflow must not push generated sync changes directly to main",
            )

        with self.subTest(msg="release workflow main-push regex catches common protected-branch pushes"):
            samples = (
                "git push origin main",
                "git push origin HEAD:main",
                "git push --force origin HEAD:main",
                "git push origin refs/heads/main",
            )
            missed = [sample for sample in samples if MAIN_PUSH_RE.search(sample) is None]
            self.assertEqual([], missed, f"main-push regex missed: {missed}")

        with self.subTest(msg="release.yml is valid YAML"):
            tab_indented_step = "name: Invalid\njobs:\n\tbuild:\n\t  runs-on: ubuntu-latest\n"
            self.assertFalse(
                _yaml_syntax_sane(tab_indented_step),
                "stdlib YAML sanity check accepted a tab-indented workflow line",
            )
            self.assertTrue(_yaml_syntax_sane(content), "release.yml failed YAML syntax validation")

        with self.subTest(msg="release-please-config.json exists"):
            self.assertTrue(RELEASE_CONFIG_FILE.is_file(), f"file not found: {RELEASE_CONFIG_FILE}")

        with self.subTest(msg="release-please extra-files never pre-bump proof-covered trees"):
            config = json.loads(RELEASE_CONFIG_FILE.read_text(encoding="utf-8")) if RELEASE_CONFIG_FILE.is_file() else {}
            forbidden: list[str] = []
            for package in (config.get("packages") or {}).values():
                if not isinstance(package, dict):
                    continue
                for entry in package.get("extra-files") or []:
                    raw = entry.get("path", "") if isinstance(entry, dict) else str(entry)
                    normalized = posixpath.normpath(raw.lstrip("/")).lstrip("./")
                    if normalized == "dist" or normalized.startswith("dist/") or "installed-cache" in normalized:
                        forbidden.append(raw)
            self.assertEqual(
                [],
                forbidden,
                "release-please extra-files must not target dist/** payloads or installed-cache fixtures; scripts/refresh-release-artifacts.py owns those trees",
            )


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateReleaseWorkflow)


def main() -> int:
    return run_counted(build_suite(), label="validate-release-workflow")


if __name__ == "__main__":
    raise SystemExit(main())
