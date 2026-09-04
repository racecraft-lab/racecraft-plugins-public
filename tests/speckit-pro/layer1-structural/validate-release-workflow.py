#!/usr/bin/env python3
"""Validate the release workflow."""

from __future__ import annotations

import json
import posixpath
import re
import shlex
import sys
import unittest
from pathlib import Path

from workflow_yaml_sanity import yaml_syntax_sane as _yaml_syntax_sane

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "release.yml"
PR_CHECKS_WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "pr-checks.yml"
COMPOSER_FILE = REPO_ROOT / "scripts" / "compose-release-notes.py"
AUDIT_HELPER_FILE = REPO_ROOT / "scripts" / "audit-release-notes.py"
DISPATCH_HELPER_FILE = REPO_ROOT / "scripts" / "dispatch-release-pr-checks.py"
POLICY_FILE = REPO_ROOT / "scripts" / "release_note_policy.py"
REFRESH_HELPER_FILE = REPO_ROOT / "scripts" / "refresh-release-artifacts.py"
RESOLVER_FILE = REPO_ROOT / "scripts" / "resolve_release_prs.py"
RUNNER_REQUEST_HELPER_FILE = REPO_ROOT / "scripts" / "run-runner-requests.py"
SYNC_HELPER_FILE = REPO_ROOT / "scripts" / "sync_release_pr.py"
RELEASE_CONFIG_FILE = REPO_ROOT / "release-please-config.json"
CHECKOUT_PIN_RE = re.compile(r"actions/checkout@[0-9a-f]{40}")
UPLOAD_ARTIFACT_PIN_RE = re.compile(r"actions/upload-artifact@[0-9a-f]{40}")
DOWNLOAD_ARTIFACT_PIN_RE = re.compile(r"actions/download-artifact@[0-9a-f]{40}")
MAIN_PUSH_RE = re.compile(r"^\s*git push(\s|$).*(\s|\"|'|:|/)main(\s|\"|'|:|$)", re.MULTILINE)
RELEASE_NOTE_EVENTS = (
    "opened",
    "reopened",
    "synchronize",
    "edited",
    "labeled",
    "unlabeled",
    "ready_for_review",
)
RELEASE_PR_FOUND_CONDITION = "steps.release_prs.outputs.found == 'true'"
RELEASE_CREATED_CONDITION = "steps.release.outputs['speckit-pro--release_created'] == 'true'"
RUNNER_REQUEST_PREFIX = "python3 scripts/run-runner-requests.py"
TEST_PAYLOAD_EVIDENCE_REQUEST = (
    "tests/speckit-pro/unit/fixtures/runner-gates/requests/test-payload-evidence.json"
)
INSTALLED_PLUGIN_RELEASE_REQUESTS = (
    "tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/runner-invocation.json",
    "tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/active-runtime-guard.json",
    "tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/payload-completeness.json",
    "tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/release-readiness.json",
)


def _contains_all(text: str, needles: tuple[str, ...]) -> bool:
    return all(needle in text for needle in needles)


def _runner_request_command(request_files: tuple[str, ...]) -> str:
    return " ".join((RUNNER_REQUEST_PREFIX, *request_files))


def _mapping_block(text: str, key: str, indent: int) -> str:
    """Return one indentation-delimited YAML mapping block."""
    prefix = " " * indent
    match = re.search(rf"(?m)^{re.escape(prefix + key)}:\s*$", text)
    if match is None:
        return ""
    end = len(text)
    for candidate in re.finditer(rf"(?m)^{re.escape(prefix)}[A-Za-z0-9_-]+:\s*", text[match.end() :]):
        end = match.end() + candidate.start()
        break
    return text[match.start() : end]


def _permission_map(job_block: str) -> dict[str, str]:
    permissions = _mapping_block(job_block, "permissions", 4)
    return {
        match.group("name"): match.group("access")
        for match in re.finditer(
            r"(?m)^\s{6}(?P<name>[a-z-]+):\s*(?P<access>read|write|none)\s*$",
            permissions,
        )
    }


def _scalar_values(text: str, key: str, indent: int) -> list[str]:
    prefix = " " * indent
    return [
        match.group("value").strip()
        for match in re.finditer(
            rf"(?m)^{re.escape(prefix + key)}:[ \t]*(?P<value>[^\r\n]*)$",
            text,
        )
    ]


def _named_step_block(job_block: str, name: str) -> str:
    """Return one named workflow step, including its nested mappings."""
    match = re.search(rf"(?m)^      - name:\s*{re.escape(name)}\s*$", job_block)
    if match is None:
        return ""
    next_step = re.search(r"(?m)^      - ", job_block[match.end() :])
    end = len(job_block) if next_step is None else match.end() + next_step.start()
    return job_block[match.start() : end]


def _python_function_block(text: str, name: str) -> str:
    """Return one top-level Python function for structural contract checks."""
    match = re.search(rf"(?m)^def {re.escape(name)}\(", text)
    if match is None:
        return ""
    next_symbol = re.search(r"(?m)^(?:def|class) [A-Za-z_]", text[match.end() :])
    end = len(text) if next_symbol is None else match.end() + next_symbol.start()
    return text[match.start() : end]


def _inline_list(value: str) -> tuple[str, ...]:
    """Parse the workflow's intentionally simple inline event list."""
    if not value.startswith("[") or not value.endswith("]"):
        return ()
    return tuple(item.strip() for item in value[1:-1].split(",") if item.strip())


def _run_commands(text: str) -> list[str]:
    return [
        match.group("command").strip()
        for match in re.finditer(r"(?m)^\s+run:\s*(?P<command>[^\r\n]*)$", text)
    ]


def _is_thin_direct_dispatch(command: str) -> bool:
    """Accept one direct tool invocation and reject shell composition."""
    if not command or command in {"|", ">", "|-", ">-"}:
        return False
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return False
    if not tokens or tokens[0] not in {"corepack", "gh", "node", "pnpm", "python3"}:
        return False
    if any(token and set(token) <= set(";&|<>") for token in tokens):
        return False
    if any("$(" in token or "`" in token for token in tokens):
        return False
    return not any(token.endswith(".sh") for token in tokens)


class ValidateReleaseWorkflow(unittest.TestCase):
    def test_release_workflow(self) -> None:
        with self.subTest(msg="release.yml exists"):
            self.assertTrue(WORKFLOW_FILE.is_file(), f"file not found: {WORKFLOW_FILE}")

        content = WORKFLOW_FILE.read_text(encoding="utf-8") if WORKFLOW_FILE.is_file() else ""
        pr_checks_content = (
            PR_CHECKS_WORKFLOW_FILE.read_text(encoding="utf-8")
            if PR_CHECKS_WORKFLOW_FILE.is_file()
            else ""
        )
        composer_content = COMPOSER_FILE.read_text(encoding="utf-8") if COMPOSER_FILE.is_file() else ""
        audit_helper_content = (
            AUDIT_HELPER_FILE.read_text(encoding="utf-8") if AUDIT_HELPER_FILE.is_file() else ""
        )
        dispatch_helper_content = (
            DISPATCH_HELPER_FILE.read_text(encoding="utf-8")
            if DISPATCH_HELPER_FILE.is_file()
            else ""
        )
        policy_content = POLICY_FILE.read_text(encoding="utf-8") if POLICY_FILE.is_file() else ""
        refresh_helper_content = (
            REFRESH_HELPER_FILE.read_text(encoding="utf-8") if REFRESH_HELPER_FILE.is_file() else ""
        )
        resolver_content = RESOLVER_FILE.read_text(encoding="utf-8") if RESOLVER_FILE.is_file() else ""
        runner_request_helper_content = (
            RUNNER_REQUEST_HELPER_FILE.read_text(encoding="utf-8")
            if RUNNER_REQUEST_HELPER_FILE.is_file()
            else ""
        )
        sync_helper_content = SYNC_HELPER_FILE.read_text(encoding="utf-8") if SYNC_HELPER_FILE.is_file() else ""

        with self.subTest(msg="release workflow uses release-please"):
            self.assertIn("googleapis/release-please-action@v5", content)

        with self.subTest(msg="release workflow pins checkout actions"):
            self.assertEqual(4, len(CHECKOUT_PIN_RE.findall(content)), "release workflow pinned checkout count")

        release_job = _mapping_block(content, "release", 2)
        capture_job = _mapping_block(content, "capture-release-note-inputs", 2)
        composer_job = _mapping_block(content, "compose-release-notes", 2)
        capture_step = _named_step_block(capture_job, "Capture complete immutable release inputs")
        snapshot_upload_step = _named_step_block(capture_job, "Upload immutable release input snapshot")
        snapshot_download_step = _named_step_block(
            composer_job,
            "Download immutable release input snapshot",
        )
        compose_step = _named_step_block(composer_job, "Compose and verify public release notes")
        audit_upload_step = _named_step_block(composer_job, "Upload immutable release note audit")
        audit_record_step = _named_step_block(composer_job, "Record immutable audit artifact")

        with self.subTest(msg="release workflow can dispatch PR checks"):
            self.assertTrue(
                _contains_all(
                    content + dispatch_helper_content,
                    (
                        "actions: write",
                        "scripts/dispatch-release-pr-checks.py",
                        '"gh",',
                        '"workflow",',
                        '"run",',
                        '"pr-checks.yml",',
                        '"--ref",',
                        'f"pr_number={release_pr[\'number\']}"',
                        'f"pr_title={release_pr[\'title\']}"',
                        '"base_ref=main",',
                        "check=True",
                        "shell=False",
                    ),
                ),
                "expected release workflow to dispatch PR Checks for release-please PR branches",
            )

        with self.subTest(msg="release workflow resolves new or unchanged release PRs for payload sync"):
            self.assertTrue(
                _contains_all(
                    content,
                    (
                        'RELEASE_PRS: ${{ steps.release.outputs.prs }}',
                        "scripts/resolve_release_prs.py",
                        'RELEASE_PRS: ${{ steps.release_prs.outputs.prs }}',
                        "steps.release_prs.outputs.found == 'true'",
                        "scripts/dispatch-release-pr-checks.py",
                    ),
                ),
                "expected release workflow to normalize release-please output and reconcile unchanged open release PRs",
            )
            self.assertTrue(
                _contains_all(
                    dispatch_helper_content,
                    (
                        'item.get("headBranchName") or item.get("headRefName")',
                        "release PR resolver returned no metadata",
                        "parse_release_prs",
                    ),
                )
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
                        "Validate installed-plugin release gates",
                        "steps.release_prs.outputs.found == 'true'",
                        'RELEASE_PRS: ${{ steps.release_prs.outputs.prs }}',
                        "scripts/run-runner-requests.py",
                        "release-readiness.json",
                        "Dispatch PR Checks for release PRs",
                    ),
                ),
                "expected release workflow to validate release PR readiness before dispatching PR Checks",
            )
            self.assertTrue(
                RUNNER_REQUEST_HELPER_FILE.is_file()
                and _contains_all(
                    runner_request_helper_content,
                    (
                        "[sys.executable, \"-m\", \"speckit_pro_runner\"]",
                        "input=request_bytes",
                        "shell=False",
                        "if completed.returncode != 0:",
                    ),
                )
            )
            runner_steps = (
                (
                    "Validate installed-plugin release gates",
                    RELEASE_PR_FOUND_CONDITION,
                    INSTALLED_PLUGIN_RELEASE_REQUESTS,
                ),
                (
                    "Verify generated test payload evidence",
                    RELEASE_CREATED_CONDITION,
                    (TEST_PAYLOAD_EVIDENCE_REQUEST,),
                ),
                (
                    "Validate post-release installed-plugin gates",
                    RELEASE_CREATED_CONDITION,
                    INSTALLED_PLUGIN_RELEASE_REQUESTS,
                ),
            )
            expected_runner_commands: list[str] = []
            for step_name, condition, request_files in runner_steps:
                step = _named_step_block(release_job, step_name)
                expected_command = _runner_request_command(request_files)
                self.assertTrue(step, f"missing release workflow step: {step_name}")
                self.assertEqual([condition], _scalar_values(step, "if", 8))
                self.assertEqual([expected_command], _scalar_values(step, "run", 8))
                expected_runner_commands.append(expected_command)
            actual_runner_commands = [
                command
                for command in _run_commands(release_job)
                if command.startswith(RUNNER_REQUEST_PREFIX)
            ]
            self.assertEqual(expected_runner_commands, actual_runner_commands)

            ordered_pre_release_steps = (
                "Set up Node",
                "Sync generated artifacts onto the release PR",
                "Validate installed-plugin release gates",
                "Dispatch PR Checks for release PRs",
            )
            step_positions = [
                release_job.find(f"      - name: {step_name}")
                for step_name in ordered_pre_release_steps
            ]
            self.assertNotIn(-1, step_positions)
            self.assertEqual(sorted(step_positions), step_positions)
            for step_name in ordered_pre_release_steps:
                self.assertEqual(
                    [RELEASE_PR_FOUND_CONDITION],
                    _scalar_values(_named_step_block(release_job, step_name), "if", 8),
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
            merge_line = sync_helper_content.find('["git", "merge", "--no-edit", base_sha]')
            refresh_line = sync_helper_content.find('[sys.executable, "scripts/refresh-release-artifacts.py"]')
            self.assertTrue(
                "BASE_REF: main" in content
                and merge_line >= 0
                and refresh_line >= 0
                and merge_line < refresh_line,
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
            self.assertTrue(
                _contains_all(
                    content + refresh_helper_content,
                    (
                        "Verify release artifacts are consistent",
                        "scripts/refresh-release-artifacts.py --check",
                        "def check_release_artifacts(",
                        "tempfile.TemporaryDirectory",
                        "shutil.copytree",
                        "shell=False",
                        "Recovery Scenario 1",
                    ),
                ),
                "expected a non-mutating release artifact check after publishing",
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

        with self.subTest(msg="release note validation covers all seven pull request events"):
            pull_request_trigger = _mapping_block(pr_checks_content, "pull_request", 2)
            event_values = _scalar_values(pull_request_trigger, "types", 4)
            self.assertEqual(1, len(event_values), "expected one pull_request event list")
            self.assertEqual(RELEASE_NOTE_EVENTS, _inline_list(event_values[0]))

        with self.subTest(msg="release workflow defaults permissions to none"):
            self.assertRegex(content, r"(?m)^permissions:\s*\{\}\s*$")

        with self.subTest(msg="release job declares publishing permissions"):
            self.assertEqual(
                {"actions": "write", "contents": "write", "pull-requests": "write"},
                _permission_map(release_job),
            )

        with self.subTest(msg="release job exports raw component release inputs"):
            self.assertTrue(
                _contains_all(
                    release_job,
                    (
                        "release_created: ${{ steps.release.outputs['speckit-pro--release_created'] }}",
                        "tag_name: ${{ steps.release.outputs['speckit-pro--tag_name'] }}",
                        "body: ${{ steps.release.outputs['speckit-pro--body'] }}",
                    ),
                )
            )
            outputs_block = _mapping_block(release_job, "outputs", 4)
            self.assertNotIn("snapshot_", outputs_block)

        with self.subTest(msg="capture is an own read-only dependent job"):
            self.assertIn("capture-release-note-inputs:", capture_job)
            self.assertEqual(["release"], _scalar_values(capture_job, "needs", 4))
            self.assertEqual(
                ["${{ always() && needs.release.outputs.release_created == 'true' }}"],
                _scalar_values(capture_job, "if", 4),
            )
            self.assertEqual({"contents": "read"}, _permission_map(capture_job))
            self.assertTrue(
                _contains_all(
                    _mapping_block(capture_job, "outputs", 4),
                    (
                        "snapshot_artifact_id: ${{ steps.upload_release_snapshot.outputs['artifact-id'] }}",
                        "snapshot_artifact_digest: ${{ steps.upload_release_snapshot.outputs['artifact-digest'] }}",
                        "snapshot_artifact_url: ${{ steps.upload_release_snapshot.outputs['artifact-url'] }}",
                        "snapshot_sha256: ${{ steps.capture_snapshot.outputs.snapshot_sha256 }}",
                    ),
                )
            )
            self.assertNotIn("RELEASE_PLEASE_TOKEN", capture_job)
            self.assertNotIn("actions: write", capture_job)
            self.assertNotIn("pull-requests: write", capture_job)

        with self.subTest(msg="capture uploads complete canonical Compare and PR inputs"):
            self.assertEqual(2, len(UPLOAD_ARTIFACT_PIN_RE.findall(content)))
            self.assertLess(capture_job.find("actions/checkout@"), capture_job.find("--capture-snapshot"))
            self.assertTrue(
                _contains_all(
                    capture_step + snapshot_upload_step,
                    (
                        "GITHUB_TOKEN: ${{ github.token }}",
                        "GITHUB_REPOSITORY: ${{ github.repository }}",
                        "RELEASE_BODY: ${{ needs.release.outputs.body }}",
                        "RELEASE_TAG: ${{ needs.release.outputs.tag_name }}",
                        "python3 scripts/compose-release-notes.py --capture-snapshot ",
                        "--snapshot-output release-note-snapshot.json",
                        "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
                        "name: release-note-input-${{ github.run_id }}-${{ github.run_attempt }}",
                        "path: release-note-snapshot.json",
                        "if-no-files-found: error",
                        "retention-days: 90",
                    ),
                )
            )
            self.assertNotIn("overwrite: true", snapshot_upload_step)
            capture_function = _python_function_block(composer_content, "capture_release_input_snapshot")
            canonical_function = _python_function_block(composer_content, "canonical_snapshot_bytes")
            loader_function = _python_function_block(composer_content, "load_release_input_snapshot")
            self.assertTrue(
                _contains_all(
                    capture_function + canonical_function + loader_function,
                    (
                        'f"/repos/{client.repository}/compare/{base}...{head}"',
                        'f"/repos/{client.repository}/pulls/{commit.pr_number}"',
                        '"body": body',
                        '"labels": sorted(_label_names(pr))',
                        '"release_body": raw_body',
                        '"compare": compare',
                        '"pulls": pulls',
                        "raw != canonical_snapshot_bytes(value)",
                        "digest != expected_sha256",
                        "set(pulls_value) != expected_pull_keys",
                    ),
                )
            )

        with self.subTest(msg="composer audits all non-cancelled post-publication capture outcomes"):
            self.assertIn("compose-release-notes:", composer_job)
            self.assertEqual(
                ["[release, capture-release-note-inputs]"],
                _scalar_values(composer_job, "needs", 4),
            )
            self.assertEqual(
                [
                    "${{ always() && !cancelled() && "
                    "needs.release.outputs.release_created == 'true' }}"
                ],
                _scalar_values(composer_job, "if", 4),
            )
            self.assertNotIn("needs.release.result", composer_job)

        with self.subTest(msg="composer has exact minimum endpoint permissions"):
            self.assertEqual(
                {"contents": "write"},
                _permission_map(composer_job),
            )

        with self.subTest(msg="composer downloads the exact immutable snapshot by artifact id"):
            self.assertEqual(1, len(DOWNLOAD_ARTIFACT_PIN_RE.findall(content)))
            self.assertTrue(
                _contains_all(
                    snapshot_download_step,
                    (
                        "id: download_release_snapshot",
                        "if: ${{ always() && !cancelled() }}",
                        "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
                        "artifact-ids: ${{ needs.capture-release-note-inputs.outputs.snapshot_artifact_id }}",
                        "path: release-note-input",
                        "digest-mismatch: error",
                    ),
                )
            )

        with self.subTest(msg="composer audits capture download and digest failures"):
            self.assertTrue(
                _contains_all(
                    compose_step + audit_helper_content,
                    (
                        "if: ${{ always() && !cancelled() }}",
                        "CAPTURE_RESULT: ${{ needs.capture-release-note-inputs.result }}",
                        "EXPECTED_SNAPSHOT_SHA256: ${{ needs.capture-release-note-inputs.outputs.snapshot_sha256 }}",
                        "SNAPSHOT_ARTIFACT_DIGEST: ${{ needs.capture-release-note-inputs.outputs.snapshot_artifact_digest }}",
                        "SNAPSHOT_DOWNLOAD_OUTCOME: ${{ steps.download_release_snapshot.outcome }}",
                        "run: python3 scripts/audit-release-notes.py",
                        'FAILURE_OUTCOME = "release_note_composition_failed"',
                        '"capture_result": capture_result',
                        '"snapshot_download_outcome": download_outcome',
                        'if capture_result != "success":',
                        'if download_outcome != "success":',
                        'snapshot_sha256 != expected_sha256',
                        'snapshot["repository"] != environment["GITHUB_REPOSITORY"]',
                        '"compare_headers"',
                        '"release_body"',
                        '"pulls"',
                        'not re.fullmatch(r"[0-9a-f]{64}", artifact_digest)',
                        'except AuditFailure as error:',
                    ),
                )
            )
            self.assertNotIn("release_note_audit_failed", audit_helper_content)
            failure_branch = audit_helper_content.find("if completed.returncode != 0:")
            wrapper_fail = audit_helper_content.find("fail(message, completed.returncode)", failure_branch)
            forwarded_stderr = audit_helper_content.find("stderr.write(completed.stderr)")
            self.assertGreater(failure_branch, -1)
            self.assertGreater(wrapper_fail, failure_branch)
            self.assertGreater(forwarded_stderr, failure_branch)
            self.assertLess(wrapper_fail, forwarded_stderr)

        with self.subTest(msg="composer rejects highlights emptied by sanitization"):
            validation_function = _python_function_block(policy_content, "validate_release_note")
            compose_body_function = _python_function_block(composer_content, "compose_release_body")
            self.assertTrue(
                _contains_all(
                    validation_function + compose_body_function,
                    (
                        "extracted = extract_release_note(body)",
                        "if not sanitize_release_note(extracted):",
                        'return False, "release-note fence is empty after sanitization"',
                        "note = sanitize_release_note(extracted)",
                        "if extracted is not None and not note:",
                        "release-note block is empty after sanitization",
                        "if note is not None and not skipped:",
                    ),
                )
            )

        with self.subTest(msg="composer defends enclosing release-note fence boundaries"):
            opening_function = _python_function_block(policy_content, "_opening_fence")
            closing_function = _python_function_block(policy_content, "_is_closing_fence")
            extraction_function = _python_function_block(policy_content, "extract_release_note")
            self.assertTrue(
                _contains_all(
                    opening_function + closing_function + extraction_function,
                    (
                        "FENCE_RE.fullmatch(rest)",
                        "_strip_quote_prefix(line, opening.quote_depth)",
                        "re.escape(opening.character)",
                        "opening.length",
                        "_is_closing_fence(candidate, opening)",
                        'if opening.info == "release-note":',
                        "An unclosed enclosing fence owns the remainder of the document",
                        "index = close_index + 1",
                        "malformed or len(matches) != 1",
                    ),
                )
            )

        with self.subTest(msg="capture owns Compare and PR reads while compose does not refetch"):
            request_methods = re.findall(
                r'client\.request_json\(\s*"(?P<method>GET|PATCH|POST|PUT|DELETE)"',
                composer_content,
            )
            self.assertEqual(["GET", "GET", "GET", "PATCH"], request_methods)
            capture_function = _python_function_block(composer_content, "capture_release_input_snapshot")
            resolve_release_function = _python_function_block(composer_content, "_resolve_release")
            run_function = _python_function_block(composer_content, "run")
            self.assertIn("if not args.snapshot:", run_function)
            live_composition = run_function.split("if not args.snapshot:", 1)[1]
            self.assertTrue(
                _contains_all(
                    capture_function,
                    (
                        'f"/repos/{client.repository}/compare/{base}...{head}"',
                        'f"/repos/{client.repository}/pulls/{commit.pr_number}"',
                    ),
                )
            )
            self.assertTrue(
                _contains_all(
                    resolve_release_function + live_composition,
                    (
                        "load_release_input_snapshot(",
                        "_resolve_release(client, args.tag)",
                        'f"/repos/{client.repository}/releases/tags/{quoted_tag}"',
                        'f"/repos/{client.repository}/releases/{release_id}"',
                        '{"body": composed}',
                    ),
                )
            )
            self.assertNotIn("/compare/", live_composition)
            self.assertNotIn("/pulls/", live_composition)
            self.assertNotIn("capture_release_input_snapshot", live_composition)

        with self.subTest(msg="raw tag and body outputs flow only through capture environment"):
            self.assertNotIn("needs.release.outputs.body", composer_job)
            self.assertNotIn("needs.release.outputs.tag_name", composer_job)
            self.assertNotRegex(composer_job, r"RELEASE_BODY:\s*\$\{\{")
            self.assertIn("RELEASE_BODY: ${{ needs.release.outputs.body }}", capture_step)
            self.assertIn("RELEASE_TAG: ${{ needs.release.outputs.tag_name }}", capture_step)
            self.assertIn(
                'composer_environment["RELEASE_TAG"] = snapshot["tag"]',
                audit_helper_content,
            )
            self.assertNotIn('composer_environment["RELEASE_BODY"]', audit_helper_content)

        with self.subTest(msg="composer emits a verified digest-bound audit record"):
            self.assertTrue(
                _contains_all(
                    audit_helper_content,
                    (
                        '"release_note_composed_and_verified"',
                        'published_body.startswith("## Highlights\\n\\n")',
                        'published_body.count(marker) != 1',
                        "payload.endswith(expected_suffix)",
                        '"body_byte_count"',
                        '"commit_count"',
                        '"snapshot_byte_count"',
                        'composer_result["body_sha256"] != published_body_sha256',
                        'composer_result["body_byte_count"] != len(published_body.encode())',
                        'composer_result["snapshot_payload_sha256"] != sha256(payload.encode())',
                        'composer_result["snapshot_source_sha256"] != snapshot_sha256',
                        'snapshot_byte_count != len(snapshot_bytes)',
                        '"release_body_sha256": published_body_sha256',
                        'output.write(f"audit_sha256={digest}\\n")',
                        'output.write(f"release_body_sha256={audit[\'release_body_sha256\']}\\n")',
                    ),
                )
            )

        with self.subTest(msg="composer uploads and summarizes an immutable audit artifact"):
            self.assertTrue(
                _contains_all(
                    audit_upload_step + audit_record_step + audit_helper_content,
                    (
                        "if: ${{ always() }}",
                        "name: release-note-audit-${{ github.run_id }}-${{ github.run_attempt }}",
                        "path: release-note-audit.json",
                        "if-no-files-found: error",
                        "AUDIT_ARTIFACT_DIGEST: ${{ steps.upload_release_audit.outputs['artifact-digest'] }}",
                        "AUDIT_ARTIFACT_ID: ${{ steps.upload_release_audit.outputs['artifact-id'] }}",
                        "AUDIT_ARTIFACT_URL: ${{ steps.upload_release_audit.outputs['artifact-url'] }}",
                        "run: python3 scripts/audit-release-notes.py --record-artifact",
                        "Immutable audit artifact",
                    ),
                )
            )
            self.assertNotIn("overwrite: true", audit_upload_step)

        with self.subTest(msg="composer invokes Python without elevated release token"):
            self.assertIn(
                '[sys.executable, str(composer_path), "--snapshot", str(snapshot_path)]',
                audit_helper_content,
            )
            self.assertIn("shell=False", audit_helper_content)
            self.assertIn("EXPECTED_SNAPSHOT_SHA256:", compose_step)
            self.assertIn("GITHUB_TOKEN: ${{ github.token }}", compose_step)
            self.assertNotIn("actions: write", composer_job)
            self.assertNotIn("pull-requests: write", composer_job)
            self.assertNotIn("pull-requests: read", composer_job)
            self.assertNotIn("RELEASE_PLEASE_TOKEN", composer_job)

        with self.subTest(msg="release.yml is valid YAML"):
            tab_indented_step = "name: Invalid\njobs:\n\tbuild:\n\t  runs-on: ubuntu-latest\n"
            valid_nested_step = """\
name: Valid
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Publish
        run: echo valid
"""
            under_indented_step = """\
name: Invalid
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Publish
      run: echo invalid
"""
            self.assertFalse(
                _yaml_syntax_sane(tab_indented_step),
                "stdlib YAML sanity check accepted a tab-indented workflow line",
            )
            self.assertTrue(
                _yaml_syntax_sane(valid_nested_step),
                "stdlib YAML sanity check rejected a valid nested workflow step",
            )
            self.assertFalse(
                _yaml_syntax_sane(under_indented_step),
                "stdlib YAML sanity check accepted an under-indented step child",
            )
            self.assertTrue(_yaml_syntax_sane(content), "release.yml failed YAML syntax validation")
            run_commands = _run_commands(content)
            self.assertTrue(run_commands, "release workflow has no direct dispatch steps")
            self.assertTrue(
                all(_is_thin_direct_dispatch(command) for command in run_commands),
                f"release workflow contains shell logic or a non-direct dispatch: {run_commands}",
            )
            self.assertTrue(
                _is_thin_direct_dispatch("gh pr view 123 --jq '.number | tostring'"),
                "GitHub CLI --jq must not be treated as an external jq command",
            )
            self.assertFalse(_is_thin_direct_dispatch("jq -r .number input.json"))
            self.assertFalse(_is_thin_direct_dispatch("python3 helper.py && echo unsafe"))
            self.assertFalse(_is_thin_direct_dispatch("python3 helper.py > result.json"))
            self.assertFalse(_is_thin_direct_dispatch("python3 - <<'PY'"))
            self.assertFalse(_is_thin_direct_dispatch("if python3 helper.py; then exit 1; fi"))
            self.assertFalse(_is_thin_direct_dispatch("python3 legacy.sh"))

        with self.subTest(msg="release-please-config.json exists"):
            self.assertTrue(RELEASE_CONFIG_FILE.is_file(), f"file not found: {RELEASE_CONFIG_FILE}")

        with self.subTest(msg="release-please extra-files never pre-bump proof-covered trees"):
            forbidden: list[str] = []
            if RELEASE_CONFIG_FILE.is_file():
                config = json.loads(RELEASE_CONFIG_FILE.read_text(encoding="utf-8"))
                for package in (config.get("packages") or {}).values():
                    if not isinstance(package, dict):
                        continue
                    for entry in package.get("extra-files") or []:
                        raw = entry.get("path", "") if isinstance(entry, dict) else str(entry)
                        normalized = posixpath.normpath(raw.lstrip("/")).lstrip("./")
                        if (
                            normalized == "dist"
                            or normalized.startswith("dist/")
                            or "installed-cache" in normalized
                        ):
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
