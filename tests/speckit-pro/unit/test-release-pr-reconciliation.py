#!/usr/bin/env python3
"""Regression coverage for unchanged release PR reconciliation."""

from __future__ import annotations

import importlib.util
import io
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


resolver = load_module("resolve_release_prs", REPO_ROOT / "scripts" / "resolve_release_prs.py")
lifecycle = load_module(
    "release_pr_lifecycle",
    REPO_ROOT / "scripts" / "release-pr-lifecycle.py",
)
refresh = load_module("refresh_release_artifacts", REPO_ROOT / "scripts" / "refresh-release-artifacts.py")
sync = load_module("sync_release_pr", REPO_ROOT / "scripts" / "sync_release_pr.py")
dispatch = load_module(
    "dispatch_release_pr_checks",
    REPO_ROOT / "scripts" / "dispatch-release-pr-checks.py",
)
audit = load_module("audit_release_notes", REPO_ROOT / "scripts" / "audit-release-notes.py")
runner_requests = load_module(
    "run_runner_requests",
    REPO_ROOT / "scripts" / "run-runner-requests.py",
)


RELEASE_PR = {
    "number": 302,
    "title": "release",
    "headBranchName": "release-please--branches--main--components--speckit-pro",
}


class ConflictingMergeRunner:
    """Fake runner whose base merge conflicts on the supplied paths."""

    def __init__(self, conflicted: list[str]) -> None:
        self.commands: list[list[str]] = []
        self.conflicted = conflicted
        self.fetch_heads = iter(["release-head", "main-head"])

    def run(self, argv, _cwd) -> None:
        command = list(argv)
        self.commands.append(command)
        if command == ["git", "merge", "--no-edit", "main-head"]:
            raise sync.SyncError("command failed (1): git merge --no-edit main-head")

    def output(self, argv, _cwd) -> str:
        command = list(argv)
        self.commands.append(command)
        if command == ["git", "rev-parse", "FETCH_HEAD"]:
            return next(self.fetch_heads)
        if command == ["git", "diff", "--name-only", "--diff-filter=U"]:
            return "\n".join(self.conflicted)
        if command == ["git", "status", "--porcelain"]:
            return " M generated-file"
        if command == ["git", "rev-parse", "HEAD"]:
            return "reconciled-head"
        raise AssertionError(command)


class ReleasePrReconciliationTests(unittest.TestCase):
    def test_action_output_takes_precedence(self) -> None:
        created = [{"number": 302, "title": "release", "headBranchName": "release-please--branches--main--components--speckit-pro"}]
        unrelated = [{"number": 99, "title": "other", "headRefName": "feature/not-release", "baseRefName": "main"}]
        self.assertEqual(resolver.resolve_release_prs(created, unrelated, "main")[0]["number"], 302)

    def test_unchanged_open_release_pr_is_discovered(self) -> None:
        open_prs = [
            {"number": 9, "title": "other", "headRefName": "feature/other", "baseRefName": "main"},
            {"number": 302, "title": "release", "headRefName": "release-please--branches--main--components--speckit-pro", "baseRefName": "main"},
            {"number": 303, "title": "fork", "headRefName": "release-please--branches--main--components--fork", "baseRefName": "main", "isCrossRepository": True},
            {"number": 7, "title": "wrong base", "headRefName": "release-please--branches--dev--components--speckit-pro", "baseRefName": "dev"},
        ]
        self.assertEqual(
            resolver.resolve_release_prs([], open_prs, "main"),
            [{"number": 302, "title": "release", "headBranchName": "release-please--branches--main--components--speckit-pro"}],
        )

    def test_no_open_release_pr_is_a_clean_noop(self) -> None:
        self.assertEqual(resolver.resolve_release_prs([], [], "main"), [])

    def test_unsafe_action_branch_is_rejected(self) -> None:
        with self.assertRaises(resolver.ResolutionError):
            resolver.resolve_release_prs(
                [{"number": 302, "title": "release", "headBranchName": "feature/not-release"}],
                [],
                "main",
            )

    def test_sync_merges_base_before_refresh_and_pushes(self) -> None:
        class FakeRunner:
            def __init__(self) -> None:
                self.commands: list[list[str]] = []
                self.fetch_heads = iter(["release-head", "main-head"])

            def run(self, argv, _cwd) -> None:
                self.commands.append(list(argv))

            def output(self, argv, _cwd) -> str:
                command = list(argv)
                self.commands.append(command)
                if command == ["git", "rev-parse", "FETCH_HEAD"]:
                    return next(self.fetch_heads)
                if command == ["git", "status", "--porcelain"]:
                    return " M generated-file"
                if command == ["git", "rev-parse", "HEAD"]:
                    return "reconciled-head"
                raise AssertionError(command)

        runner = FakeRunner()
        sync.sync_release_branch(
            REPO_ROOT,
            {"number": 302, "title": "release", "headBranchName": "release-please--branches--main--components--speckit-pro"},
            "main",
            runner,
        )
        merge_index = runner.commands.index(["git", "merge", "--no-edit", "main-head"])
        refresh_index = runner.commands.index([sync.sys.executable, "scripts/refresh-release-artifacts.py"])
        docs_index = runner.commands.index(["pnpm", "--dir", "docs-site", "reference:generate"])
        push_index = runner.commands.index(["git", "push", "origin", "HEAD:release-please--branches--main--components--speckit-pro"])
        self.assertLess(merge_index, refresh_index)
        self.assertLess(refresh_index, docs_index)
        self.assertLess(docs_index, push_index)

    def test_regenerated_artifact_conflicts_resolve_to_base_and_continue(self) -> None:
        conflicted = [
            "dist/claude/speckit-pro/.claude-plugin/plugin.json",
            "speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256",
        ]
        runner = ConflictingMergeRunner(conflicted)
        sync.sync_release_branch(REPO_ROOT, RELEASE_PR, "main", runner)

        for path in conflicted:
            self.assertIn(["git", "checkout", "--theirs", "--", path], runner.commands)
            self.assertIn(["git", "add", "--", path], runner.commands)
        commit_index = runner.commands.index(["git", "commit", "--no-edit"])
        refresh_index = runner.commands.index(
            [sync.sys.executable, "scripts/refresh-release-artifacts.py"]
        )
        push_index = runner.commands.index(
            ["git", "push", "origin", f"HEAD:{RELEASE_PR['headBranchName']}"]
        )
        self.assertLess(commit_index, refresh_index)
        self.assertLess(refresh_index, push_index)

    def test_conflict_outside_regenerated_artifacts_fails_the_sync(self) -> None:
        runner = ConflictingMergeRunner(
            [
                "dist/claude/speckit-pro/.claude-plugin/plugin.json",
                "speckit-pro/speckit_pro_runner/__main__.py",
            ]
        )
        with self.assertRaises(sync.SyncError) as caught:
            sync.sync_release_branch(REPO_ROOT, RELEASE_PR, "main", runner)

        self.assertIn("speckit-pro/speckit_pro_runner/__main__.py", str(caught.exception))
        # The regenerated sibling must not be resolved away on the strength of a
        # real conflict sharing the same merge.
        self.assertNotIn(["git", "commit", "--no-edit"], runner.commands)

    def test_merge_failure_without_a_conflicted_path_keeps_the_git_diagnostic(self) -> None:
        runner = ConflictingMergeRunner([])
        with self.assertRaises(sync.SyncError) as caught:
            sync.sync_release_branch(REPO_ROOT, RELEASE_PR, "main", runner)
        message = str(caught.exception)
        self.assertIn("git merge --no-edit main-head", message)
        self.assertIn("no conflicted path was reported", message)

    def test_regenerated_artifact_paths_track_the_refresh_script(self) -> None:
        paths = sync.regenerated_artifact_paths(REPO_ROOT)
        self.assertEqual(paths, tuple(refresh.CHECK_WORKTREE_PATHS))
        for path in (
            "dist/claude/speckit-pro/.claude-plugin/plugin.json",
            "speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256",
        ):
            self.assertTrue(sync.is_regenerated_artifact(path, paths), path)
        for path in (
            "speckit-pro/gate-evidence/installed-cache-proof.json",
            "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/oracle.json",
            "speckit-pro/speckit_pro_runner/__main__.py",
            "distribution/notes.md",
        ):
            self.assertFalse(sync.is_regenerated_artifact(path, paths), path)


class ReleasePrDispatchTests(unittest.TestCase):
    def test_dispatch_validates_metadata_and_invokes_gh_with_argv(self) -> None:
        calls: list[tuple[list[str], dict]] = []

        def fake_run(argv, **kwargs):
            calls.append((list(argv), kwargs))
            return subprocess.CompletedProcess(argv, 0)

        release_prs = dispatch.parse_release_prs(
            json.dumps(
                [
                    {
                        "headBranchName": "release-please--branches--main--components--speckit-pro",
                        "number": 302,
                        "title": "chore(main): release speckit-pro 2.19.0",
                    }
                ]
            )
        )
        dispatch.dispatch_release_pr_checks(release_prs, run=fake_run)

        self.assertEqual(1, len(calls))
        argv, kwargs = calls[0]
        self.assertEqual(
            [
                "gh",
                "workflow",
                "run",
                "pr-checks.yml",
                "--ref",
                "release-please--branches--main--components--speckit-pro",
                "-f",
                "pr_number=302",
                "-f",
                "pr_title=chore(main): release speckit-pro 2.19.0",
                "-f",
                "base_ref=main",
            ],
            argv,
        )
        self.assertEqual({"check": True, "shell": False}, kwargs)

    def test_dispatch_rejects_malformed_empty_and_incomplete_metadata(self) -> None:
        invalid_values = (
            "{not-json",
            "{}",
            "[]",
            '[{"number":302,"title":"release"}]',
            '[{"headBranchName":"bad branch","number":302,"title":"release"}]',
            '[{"headBranchName":"release/main","number":"nope","title":"release"}]',
            '[{"headBranchName":"release/main","number":302,"title":"bad\\ntitle"}]',
        )
        for raw in invalid_values:
            with self.subTest(raw=raw), self.assertRaises(dispatch.DispatchError):
                dispatch.parse_release_prs(raw)

    def test_dispatch_stops_and_reports_child_failure_with_parent_status(self) -> None:
        calls: list[list[str]] = []

        def failing_run(argv, **_kwargs):
            calls.append(list(argv))
            raise subprocess.CalledProcessError(17, argv)

        environment = {
            "RELEASE_PRS": json.dumps(
                [
                    {"headRefName": "release/one", "number": 1, "title": "release one"},
                    {"headRefName": "release/two", "number": 2, "title": "release two"},
                ]
            )
        }
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            returncode = dispatch.main(environment, run=failing_run)

        self.assertEqual(1, returncode)
        self.assertEqual(1, len(calls))
        self.assertIn("PR #1", stderr.getvalue())
        self.assertIn("child exit 17", stderr.getvalue())


class ReleasePrLifecycleTests(unittest.TestCase):
    class FakeRunner:
        def __init__(self, draft_states: dict[int, bool]) -> None:
            self.draft_states = draft_states
            self.commands: list[list[str]] = []

        def output(self, argv) -> str:
            command = list(argv)
            self.commands.append(command)
            number = int(command[3])
            return json.dumps({"isDraft": self.draft_states[number]})

        def run(self, argv) -> None:
            self.commands.append(list(argv))

    def test_existing_release_pr_is_held_draft_idempotently(self) -> None:
        release_prs = [
            {
                "number": 342,
                "title": "release",
                "headBranchName": "release-please--branches--main--components--speckit-pro",
            },
            {
                "number": 343,
                "title": "release",
                "headBranchName": "release-please--branches--main--components--other",
            },
        ]
        runner = self.FakeRunner({342: False, 343: True})

        lifecycle.set_draft_state(release_prs, draft=True, runner=runner)

        self.assertIn(["gh", "pr", "ready", "342", "--undo"], runner.commands)
        self.assertNotIn(["gh", "pr", "ready", "343", "--undo"], runner.commands)

    def test_synchronized_release_pr_is_marked_ready(self) -> None:
        runner = self.FakeRunner({342: True})
        release_prs = lifecycle.lifecycle_targets(
            json.dumps(
                [
                    {
                        "number": 342,
                        "title": "release",
                        "headBranchName": "release-please--branches--main--components--speckit-pro",
                    }
                ]
            ),
            "main",
            fetch_open=lambda _base_ref: self.fail("action metadata must avoid an open-PR query"),
        )

        lifecycle.set_draft_state(release_prs, draft=False, runner=runner)

        self.assertIn(["gh", "pr", "ready", "342"], runner.commands)

    def test_ready_without_release_metadata_fails_closed(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            return_code = lifecycle.main(
                ["ready"],
                {"BASE_REF": "main", "RELEASE_PRS": "[]"},
                runner=self.FakeRunner({}),
                fetch_open=lambda _base_ref: [],
            )

        self.assertEqual(1, return_code)
        self.assertIn("release PR resolver returned no metadata", stderr.getvalue())

    def test_release_workflow_holds_review_until_artifact_sync(self) -> None:
        config = json.loads((REPO_ROOT / "release-please-config.json").read_text(encoding="utf-8"))
        workflow = (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        container = (REPO_ROOT / ".github/workflows/container-preflight.yml").read_text(encoding="utf-8")

        self.assertIs(config["draft-pull-request"], True)
        ordered_markers = (
            "Hold existing release PRs as draft",
            "id: release",
            "Sync generated artifacts onto the release PR",
            "Validate installed-plugin release gates",
            "Mark synchronized release PRs ready for review",
            "Dispatch PR Checks for release PRs",
        )
        positions = [workflow.find(marker) for marker in ordered_markers]
        self.assertNotIn(-1, positions)
        self.assertEqual(sorted(positions), positions)
        self.assertIn("python3 scripts/release-pr-lifecycle.py hold", workflow)
        self.assertIn("python3 scripts/release-pr-lifecycle.py ready", workflow)
        self.assertIn(
            "PR_DRAFT: ${{ github.event_name == 'pull_request' && "
            "github.event.pull_request.draft || false }}",
            container,
        )


class RunnerRequestDispatchTests(unittest.TestCase):
    def test_runner_requests_preserve_order_bytes_and_python_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            request_dir = repo_root / "requests"
            request_dir.mkdir()
            first = request_dir / "first.json"
            second = request_dir / "second.json"
            first.write_bytes(b'{"request_id":"first"}\n')
            second.write_bytes(b'{"request_id":"second"}\n')
            calls: list[tuple[list[str], dict]] = []

            def fake_run(argv, **kwargs):
                calls.append((list(argv), kwargs))
                return subprocess.CompletedProcess(argv, 0)

            returncode = runner_requests.run_runner_requests(
                repo_root,
                ["requests/first.json", "requests/second.json"],
                run=fake_run,
                environment={"PATH": "/test/bin"},
            )

        self.assertEqual(0, returncode)
        self.assertEqual([b'{"request_id":"first"}\n', b'{"request_id":"second"}\n'], [call[1]["input"] for call in calls])
        for argv, kwargs in calls:
            self.assertEqual([sys.executable, "-m", "speckit_pro_runner"], argv)
            self.assertEqual(str(repo_root.resolve()), kwargs["cwd"])
            self.assertEqual(str(repo_root.resolve() / "speckit-pro"), kwargs["env"]["PYTHONPATH"])
            self.assertEqual("1", kwargs["env"]["PYTHONDONTWRITEBYTECODE"])
            self.assertFalse(kwargs["shell"])
            self.assertFalse(kwargs["check"])

    def test_runner_requests_stop_on_first_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            for name in ("first.json", "second.json", "third.json"):
                (repo_root / name).write_text("{}\n", encoding="utf-8")
            calls: list[bytes] = []

            def fake_run(argv, **kwargs):
                calls.append(kwargs["input"])
                return subprocess.CompletedProcess(argv, 9 if len(calls) == 2 else 0)

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                returncode = runner_requests.run_runner_requests(
                    repo_root,
                    ["first.json", "second.json", "third.json"],
                    run=fake_run,
                )

        self.assertEqual(9, returncode)
        self.assertEqual(2, len(calls))
        self.assertIn("second.json", stderr.getvalue())

    def test_runner_requests_normalize_signal_status_and_stop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            for name in ("first.json", "second.json"):
                (repo_root / name).write_text("{}\n", encoding="utf-8")
            calls: list[bytes] = []

            def signal_run(argv, **kwargs):
                calls.append(kwargs["input"])
                return subprocess.CompletedProcess(argv, -signal.SIGTERM)

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                returncode = runner_requests.run_runner_requests(
                    repo_root,
                    ["first.json", "second.json"],
                    run=signal_run,
                )

        self.assertEqual(128 + signal.SIGTERM, returncode)
        self.assertEqual(1, len(calls))
        self.assertIn(f"signal {signal.SIGTERM}; exit {128 + signal.SIGTERM}", stderr.getvalue())

    def test_runner_requests_fail_closed_for_missing_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                returncode = runner_requests.run_runner_requests(
                    Path(tmp),
                    ["missing.json"],
                    run=lambda *_args, **_kwargs: self.fail("runner must not execute"),
                )
        self.assertEqual(1, returncode)
        self.assertIn("missing.json", stderr.getvalue())


class ReleaseNoteAuditTests(unittest.TestCase):
    REPOSITORY = "racecraft-lab/racecraft-plugins-public"
    TAG = "speckit-pro-v2.19.0"

    def make_case(self, root: Path) -> tuple[dict[str, str], bytes, dict]:
        composer_path = root / "scripts" / "compose-release-notes.py"
        composer_path.parent.mkdir(parents=True)
        composer_path.write_text("# deterministic composer fixture\n", encoding="utf-8")
        snapshot = {
            "compare": {"commits": []},
            "compare_headers": {},
            "previous_tag": "speckit-pro-v2.18.0",
            "pulls": {},
            "release_body": "raw release body",
            "repository": self.REPOSITORY,
            "schema_version": 1,
            "tag": self.TAG,
        }
        snapshot_bytes = (json.dumps(snapshot, sort_keys=True, separators=(",", ":")) + "\n").encode()
        snapshot_path = root / "release-note-input" / "release-note-snapshot.json"
        snapshot_path.parent.mkdir()
        snapshot_path.write_bytes(snapshot_bytes)
        environment = {
            "CAPTURE_RESULT": "success",
            "EXPECTED_SNAPSHOT_SHA256": hashlib.sha256(snapshot_bytes).hexdigest(),
            "GITHUB_API_URL": "https://api.github.test",
            "GITHUB_OUTPUT": str(root / "github-output.txt"),
            "GITHUB_REPOSITORY": self.REPOSITORY,
            "GITHUB_STEP_SUMMARY": str(root / "summary.md"),
            "GITHUB_TOKEN": "test-token",
            "SNAPSHOT_ARTIFACT_DIGEST": "a" * 64,
            "SNAPSHOT_ARTIFACT_ID": "456",
            "SNAPSHOT_ARTIFACT_URL": "https://github.test/artifacts/456",
            "SNAPSHOT_DOWNLOAD_OUTCOME": "success",
            "WORKFLOW_RUN_ATTEMPT": "2",
            "WORKFLOW_RUN_ID": "123",
        }
        return environment, snapshot_bytes, snapshot

    def composer_success(self, snapshot_bytes: bytes, snapshot: dict) -> tuple[dict, dict]:
        payload = "## Highlights\n\nA useful change\n\n## Commit appendix\n\n" + snapshot["release_body"]
        published_body = payload + "\n\n<!-- release-note-composer-snapshot:v1 test -->"
        result = {
            "body_byte_count": len(published_body.encode()),
            "body_sha256": hashlib.sha256(published_body.encode()).hexdigest(),
            "commit_count": 1,
            "outcome": "release_note_composed",
            "previous_tag": snapshot["previous_tag"],
            "pull_request_count": 1,
            "release_id": 789,
            "snapshot_byte_count": len(snapshot_bytes),
            "snapshot_payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "snapshot_reused": False,
            "snapshot_source_sha256": hashlib.sha256(snapshot_bytes).hexdigest(),
            "tag": snapshot["tag"],
        }
        release = {"id": 789, "tag_name": snapshot["tag"], "body": published_body}
        return result, release

    def _assert_acquisition_failure(
        self,
        environment_key: str,
        expected_message: str,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            environment, _snapshot_bytes, _snapshot = self.make_case(root)
            environment[environment_key] = "failure"
            calls = {"composer": 0, "api": 0}

            def unexpected_composer(argv, **_kwargs):
                calls["composer"] += 1
                return subprocess.CompletedProcess(argv, 99, stdout="", stderr="unexpected")

            def unexpected_api(*_args, **_kwargs):
                calls["api"] += 1
                raise AssertionError("release API must not run")

            stdout = io.StringIO()
            stderr = io.StringIO()
            returncode = audit.audit_release_notes(
                root,
                environment,
                run=unexpected_composer,
                urlopen=unexpected_api,
                stdout=stdout,
                stderr=stderr,
            )
            audit_bytes = (root / "release-note-audit.json").read_bytes()
            output = (root / "github-output.txt").read_text(encoding="utf-8")
            summary = (root / "summary.md").read_text(encoding="utf-8")

        expected_record = {
            "capture_result": environment["CAPTURE_RESULT"],
            "composer_run_attempt": 2,
            "error": expected_message,
            "outcome": audit.FAILURE_OUTCOME,
            "schema_version": 1,
            "snapshot_download_outcome": environment["SNAPSHOT_DOWNLOAD_OUTCOME"],
            "workflow_run_id": 123,
        }
        expected_audit = (
            json.dumps(expected_record, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        expected_digest = hashlib.sha256(expected_audit).hexdigest()
        self.assertEqual(1, returncode)
        self.assertEqual({"composer": 0, "api": 0}, calls)
        self.assertEqual(expected_audit, audit_bytes)
        self.assertEqual(f"audit_sha256={expected_digest}\n", output)
        self.assertEqual(
            "### Release note composition failed\n\n"
            f"- Audit SHA-256: `{expected_digest}`\n"
            f"- Reason: `{expected_message}`\n",
            summary,
        )
        self.assertEqual("", stdout.getvalue())
        self.assertEqual(
            json.dumps(
                {"error": expected_message, "outcome": audit.FAILURE_OUTCOME},
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            stderr.getvalue(),
        )

    def test_audit_records_capture_result_failure_without_composer_or_api(self) -> None:
        self._assert_acquisition_failure(
            "CAPTURE_RESULT",
            "release input capture did not succeed: failure",
        )

    def test_audit_records_snapshot_download_failure_without_composer_or_api(self) -> None:
        self._assert_acquisition_failure(
            "SNAPSHOT_DOWNLOAD_OUTCOME",
            "release snapshot download did not succeed: failure",
        )

    def test_audit_rejects_snapshot_digest_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            environment, _snapshot_bytes, _snapshot = self.make_case(root)
            environment["EXPECTED_SNAPSHOT_SHA256"] = "0" * 64
            returncode = audit.audit_release_notes(
                root,
                environment,
                run=lambda *_args, **_kwargs: self.fail("composer must not run"),
                urlopen=lambda *_args, **_kwargs: self.fail("API must not run"),
                stderr=io.StringIO(),
            )
            record = json.loads((root / "release-note-audit.json").read_text(encoding="utf-8"))
            output = (root / "github-output.txt").read_text(encoding="utf-8")
            summary = (root / "summary.md").read_text(encoding="utf-8")

        self.assertEqual(1, returncode)
        self.assertEqual("release snapshot SHA-256 mismatch", record["error"])
        self.assertEqual("release_note_composition_failed", record["outcome"])
        self.assertIn("audit_sha256=", output)
        self.assertNotIn("release_body_sha256=", output)
        self.assertIn("### Release note composition failed", summary)
        self.assertIn("release snapshot SHA-256 mismatch", summary)

    def test_audit_rejects_missing_artifact_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            environment, _snapshot_bytes, _snapshot = self.make_case(root)
            environment["SNAPSHOT_ARTIFACT_ID"] = ""
            environment["SNAPSHOT_ARTIFACT_DIGEST"] = ""
            returncode = audit.audit_release_notes(
                root,
                environment,
                run=lambda *_args, **_kwargs: self.fail("composer must not run"),
                urlopen=lambda *_args, **_kwargs: self.fail("API must not run"),
                stderr=io.StringIO(),
            )
            record = json.loads((root / "release-note-audit.json").read_text(encoding="utf-8"))

        self.assertEqual(1, returncode)
        self.assertEqual("release snapshot artifact metadata is invalid", record["error"])

    def test_audit_preserves_composer_failure_diagnostics_and_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            environment, _snapshot_bytes, _snapshot = self.make_case(root)

            def failing_composer(argv, **_kwargs):
                diagnostic = json.dumps(
                    {"error": "invalid release note", "outcome": "release_note_composition_failed"},
                    sort_keys=True,
                    separators=(",", ":"),
                )
                return subprocess.CompletedProcess(argv, 7, stdout="", stderr=diagnostic)

            returncode = audit.audit_release_notes(
                root,
                environment,
                run=failing_composer,
                urlopen=lambda *_args, **_kwargs: self.fail("API must not run"),
                stderr=io.StringIO(),
            )
            record = json.loads((root / "release-note-audit.json").read_text(encoding="utf-8"))

        self.assertEqual(7, returncode)
        self.assertEqual("release-note composer failed: invalid release note", record["error"])
        self.assertEqual(7, record["composer_returncode"])
        self.assertEqual(hashlib.sha256(failing_composer([],).stderr.encode()).hexdigest(), record["composer_diagnostic_sha256"])

    def test_audit_fails_closed_when_release_api_verification_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            environment, snapshot_bytes, snapshot = self.make_case(root)
            composer_result, _release = self.composer_success(snapshot_bytes, snapshot)

            def successful_composer(argv, **_kwargs):
                return subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout=json.dumps(composer_result, sort_keys=True, separators=(",", ":")),
                    stderr="",
                )

            returncode = audit.audit_release_notes(
                root,
                environment,
                run=successful_composer,
                urlopen=lambda *_args, **_kwargs: (_ for _ in ()).throw(urllib.error.URLError("offline")),
                stdout=io.StringIO(),
                stderr=io.StringIO(),
            )
            record = json.loads((root / "release-note-audit.json").read_text(encoding="utf-8"))

        self.assertEqual(1, returncode)
        self.assertIn("release note audit raised URLError", record["error"])
        self.assertEqual("release_note_composition_failed", record["outcome"])

    def test_audit_success_emits_exact_record_outputs_and_summary(self) -> None:
        class Response:
            def __init__(self, release: dict) -> None:
                self.release = release

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self) -> bytes:
                return json.dumps(self.release).encode()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            environment, snapshot_bytes, snapshot = self.make_case(root)
            composer_result, release = self.composer_success(snapshot_bytes, snapshot)

            def successful_composer(argv, **kwargs):
                self.assertEqual(
                    [sys.executable, str(root / "scripts" / "compose-release-notes.py"), "--snapshot", str(root / "release-note-input" / "release-note-snapshot.json")],
                    argv,
                )
                self.assertFalse(kwargs["shell"])
                return subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout=json.dumps(composer_result, sort_keys=True, separators=(",", ":")),
                    stderr="",
                )

            returncode = audit.audit_release_notes(
                root,
                environment,
                run=successful_composer,
                urlopen=lambda *_args, **_kwargs: Response(release),
                stdout=io.StringIO(),
                stderr=io.StringIO(),
            )
            audit_bytes = (root / "release-note-audit.json").read_bytes()
            record = json.loads(audit_bytes)
            output = (root / "github-output.txt").read_text(encoding="utf-8")
            summary = (root / "summary.md").read_text(encoding="utf-8")

        expected_keys = {
            "body_byte_count",
            "capture_result",
            "commit_count",
            "composer_returncode",
            "composer_run_attempt",
            "composer_sha256",
            "outcome",
            "previous_tag",
            "pull_request_count",
            "raw_release_body_sha256",
            "release_body_sha256",
            "release_id",
            "schema_version",
            "snapshot",
            "snapshot_byte_count",
            "snapshot_download_outcome",
            "snapshot_payload_sha256",
            "snapshot_reused",
            "snapshot_source_sha256",
            "tag",
            "workflow_run_id",
        }
        self.assertEqual(0, returncode)
        self.assertEqual(expected_keys, set(record))
        self.assertEqual("release_note_composed_and_verified", record["outcome"])
        self.assertEqual(
            (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode(),
            audit_bytes,
        )
        self.assertIn(f"audit_sha256={hashlib.sha256(audit_bytes).hexdigest()}\n", output)
        self.assertIn(f"release_body_sha256={record['release_body_sha256']}\n", output)
        self.assertIn("### Release note audit", summary)
        self.assertIn(environment["SNAPSHOT_ARTIFACT_URL"], summary)

    def test_audit_artifact_record_preserves_json_and_summary_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            environment = {
                "AUDIT_ARTIFACT_DIGEST": "b" * 64,
                "AUDIT_ARTIFACT_ID": "987",
                "AUDIT_ARTIFACT_URL": "https://github.test/artifacts/987",
                "GITHUB_STEP_SUMMARY": str(root / "summary.md"),
            }
            stdout = io.StringIO()
            returncode = audit.record_audit_artifact(environment, stdout=stdout)
            summary = (root / "summary.md").read_text(encoding="utf-8")

        self.assertEqual(0, returncode)
        self.assertEqual(
            {
                "artifact_digest": "b" * 64,
                "artifact_id": 987,
                "artifact_url": "https://github.test/artifacts/987",
                "outcome": "release_note_audit_published",
            },
            json.loads(stdout.getvalue()),
        )
        self.assertIn("### Immutable audit artifact", summary)
        self.assertIn("Artifact id: `987`", summary)


class RefreshReleaseArtifactsCheckTests(unittest.TestCase):
    def make_repo(self, root: Path) -> None:
        script = root / "scripts" / "refresh-release-artifacts.py"
        script.parent.mkdir(parents=True)
        script.write_text("# refresh fixture\n", encoding="utf-8")
        (root / "generated.txt").write_text("current\n", encoding="utf-8")

    @staticmethod
    def snapshot(root: Path) -> dict[str, str]:
        return refresh.snapshot_tree(root)

    def test_check_mode_reports_clean_isolated_regeneration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_repo(root)
            calls: list[tuple[list[str], dict]] = []

            def fake_run(argv, **kwargs):
                calls.append((list(argv), kwargs))
                if argv[0] == "git":
                    return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
                return subprocess.CompletedProcess(argv, 0, stdout="already consistent\n", stderr="")

            stdout = io.StringIO()
            returncode = refresh.check_release_artifacts(root, run=fake_run, stdout=stdout)

        self.assertEqual(0, returncode)
        self.assertIn("match the source tree", stdout.getvalue())
        refresh_calls = [call for call in calls if call[0][0] == sys.executable]
        git_calls = [call[0] for call in calls if call[0][0] == "git"]
        self.assertEqual(1, len(refresh_calls))
        self.assertEqual([sys.executable, "scripts/refresh-release-artifacts.py"], refresh_calls[0][0])
        self.assertFalse(refresh_calls[0][1]["shell"])
        self.assertIn(["git", "init", "--quiet"], git_calls)
        self.assertIn(["git", "add", "--all"], git_calls)

    def test_check_mode_excludes_ignored_local_files_from_isolated_git_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_repo(root)
            (root / ".gitignore").write_text("ignored-local.sh\n", encoding="utf-8")
            (root / "ignored-local.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            (root / "scripts" / "refresh-release-artifacts.py").write_text(
                "import subprocess\n"
                "result = subprocess.run(\n"
                "    ['git', 'ls-files', '--error-unmatch', 'ignored-local.sh'],\n"
                "    capture_output=True,\n"
                "    check=False,\n"
                ")\n"
                "raise SystemExit(1 if result.returncode == 0 else 0)\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=root,
                check=True,
                shell=False,
                capture_output=True,
            )

            stderr = io.StringIO()
            returncode = refresh.check_release_artifacts(root, stderr=stderr)

        self.assertEqual(0, returncode, stderr.getvalue())

    def test_snapshot_tree_excludes_local_worktrees(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_repo(root)
            nested = root / ".worktrees" / "local"
            nested.mkdir(parents=True)
            (nested / "unrelated.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")

            snapshot = refresh.snapshot_tree(root)

        self.assertNotIn(".worktrees/local/unrelated.sh", snapshot)

    def test_check_mode_runs_a_real_isolated_copy_without_source_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_repo(root)
            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=root,
                check=True,
                shell=False,
                capture_output=True,
            )
            before = self.snapshot(root)
            stdout = io.StringIO()
            stderr = io.StringIO()

            returncode = refresh.check_release_artifacts(
                root,
                stdout=stdout,
                stderr=stderr,
            )
            after = self.snapshot(root)

        self.assertEqual(0, returncode, stderr.getvalue())
        self.assertEqual(before, after)
        self.assertEqual("Generated release artifacts match the source tree.\n", stdout.getvalue())
        self.assertEqual("", stderr.getvalue())

    @unittest.skipIf(os.name == "nt", "POSIX mode and symlink records are not portable to Windows")
    def test_snapshot_tree_records_file_modes_content_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_repo(root)
            generated = root / "generated.txt"
            generated.chmod(0o640)
            (root / "generated-link").symlink_to("generated.txt")

            before = refresh.snapshot_tree(root)
            generated.chmod(0o750)
            after = refresh.snapshot_tree(root)

        self.assertEqual(
            "file:0640:" + hashlib.sha256(b"current\n").hexdigest(),
            before["generated.txt"],
        )
        self.assertEqual("link:generated.txt", before["generated-link"])
        self.assertEqual(["M generated.txt"], refresh.compare_snapshots(before, after))

    @unittest.skipIf(os.name == "nt", "POSIX executable-mode drift is not portable to Windows")
    def test_check_mode_reports_executable_mode_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_repo(root)
            (root / "generated.txt").chmod(0o644)

            def mode_drift_run(argv, **kwargs):
                if argv[0] == "git":
                    return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
                (Path(kwargs["cwd"]) / "generated.txt").chmod(0o755)
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            stderr = io.StringIO()
            returncode = refresh.check_release_artifacts(
                root,
                run=mode_drift_run,
                stderr=stderr,
            )

        self.assertEqual(1, returncode)
        self.assertIn("M generated.txt", stderr.getvalue())

    def test_default_mode_still_uses_the_mutating_refresh_path(self) -> None:
        with (
            mock.patch.object(refresh, "refresh_release_artifacts", return_value=0) as mutate,
            mock.patch.object(refresh, "check_release_artifacts", return_value=0) as check,
        ):
            returncode = refresh.main([])

        self.assertEqual(0, returncode)
        mutate.assert_called_once_with(REPO_ROOT)
        check.assert_not_called()

    def test_check_mode_reports_actionable_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_repo(root)

            def fake_run(argv, **kwargs):
                if argv[0] == "git":
                    return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
                (Path(kwargs["cwd"]) / "generated.txt").write_text("drifted\n", encoding="utf-8")
                return subprocess.CompletedProcess(argv, 0, stdout="refreshed\n", stderr="")

            stderr = io.StringIO()
            returncode = refresh.check_release_artifacts(root, run=fake_run, stderr=stderr)

        self.assertEqual(1, returncode)
        self.assertIn("Run scripts/refresh-release-artifacts.py", stderr.getvalue())
        self.assertIn("M generated.txt", stderr.getvalue())

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_repo(root)
            calls = 0

            def dirty_status(argv, **_kwargs):
                nonlocal calls
                calls += 1
                return subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout=" M dist/claude/speckit-pro/manifest.json\n",
                    stderr="",
                )

            stderr = io.StringIO()
            returncode = refresh.check_release_artifacts(root, run=dirty_status, stderr=stderr)

        self.assertEqual(1, returncode)
        self.assertEqual(1, calls)
        self.assertIn("dist/claude/speckit-pro/manifest.json", stderr.getvalue())

    def test_check_mode_propagates_subprocess_and_copy_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_repo(root)

            def failing_run(argv, **_kwargs):
                if argv[0] == "git":
                    return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
                return subprocess.CompletedProcess(argv, 11, stdout="partial\n", stderr="failed\n")

            stderr = io.StringIO()
            returncode = refresh.check_release_artifacts(
                root,
                run=failing_run,
                stdout=io.StringIO(),
                stderr=stderr,
            )
            self.assertEqual(11, returncode)
            self.assertIn("failed", stderr.getvalue())

            stderr = io.StringIO()
            with mock.patch.object(refresh.shutil, "copytree", side_effect=OSError("copy failed")):
                returncode = refresh.check_release_artifacts(root, run=failing_run, stderr=stderr)
            self.assertEqual(1, returncode)
            self.assertIn("copy failed", stderr.getvalue())

    def test_check_mode_never_mutates_tracked_or_untracked_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_repo(root)
            (root / "untracked.txt").write_text("keep me\n", encoding="utf-8")
            before = self.snapshot(root)

            def mutating_isolated_run(argv, **kwargs):
                if argv[0] == "git":
                    return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
                isolated = Path(kwargs["cwd"])
                (isolated / "generated.txt").unlink()
                (isolated / "new-generated.txt").write_text("new\n", encoding="utf-8")
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            returncode = refresh.check_release_artifacts(
                root,
                run=mutating_isolated_run,
                stderr=io.StringIO(),
            )
            after = self.snapshot(root)

        self.assertEqual(1, returncode)
        self.assertEqual(before, after)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    print(f"test-release-pr-reconciliation: {total - failed}/{total} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
