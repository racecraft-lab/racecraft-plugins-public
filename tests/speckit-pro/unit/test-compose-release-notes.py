#!/usr/bin/env python3
"""Focused contracts for the deterministic GitHub Release notes composer."""

from __future__ import annotations

import ast
import contextlib
import functools
import hashlib
import http.client
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "compose-release-notes.py"
PR_TEMPLATE = REPO_ROOT / ".github" / "pull_request_template.md"
QUICKSTART_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "release-notes" / "quickstart.json"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

RAW_BODY = """## [2.19.0](https://github.com/racecraft-lab/racecraft-plugins-public/compare/speckit-pro-v2.18.0...speckit-pro-v2.19.0) (2026-07-09)

### Features

* add public release highlights ([#101](https://github.com/racecraft-lab/racecraft-plugins-public/issues/101))
"""
REPOSITORY = "racecraft-lab/racecraft-plugins-public"
TAG = "speckit-pro-v2.19.0"
PREVIOUS_TAG = "speckit-pro-v2.18.0"


def inventory_check(test):  # type: ignore[no-untyped-def]
    """Give a non-loop unittest method one stable parity-inventory name."""
    @functools.wraps(test)
    def wrapped(self):  # type: ignore[no-untyped-def]
        name = test.__name__.removeprefix("test_").replace("_", " ")
        with self.subTest(msg=name):
            test(self)

    return wrapped


def load_composer():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("compose_release_notes", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load composer: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


COMPOSER = load_composer()


def compare_payload(*subjects: str, total_commits: int | None = None) -> dict:
    commits = [
        {"sha": f"sha-{index}", "commit": {"message": subject}}
        for index, subject in enumerate(subjects, start=1)
    ]
    return {
        "status": "ahead",
        "total_commits": len(commits) if total_commits is None else total_commits,
        "commits": commits,
    }


def pull(title: str, body: str = "", *labels: str) -> dict:
    return {
        "title": title,
        "body": body,
        "labels": [{"name": label} for label in labels],
    }


def release_snapshot(
    compare: dict,
    pulls: dict[str | int, dict],
    *,
    release_body: str = RAW_BODY,
    compare_headers: dict | None = None,
) -> dict:
    normalized_pulls = {
        str(number): {
            "body": metadata.get("body") or "",
            "labels": sorted(COMPOSER._label_names(metadata)),
        }
        for number, metadata in pulls.items()
    }
    return {
        "compare": compare,
        "compare_headers": compare_headers or {},
        "previous_tag": PREVIOUS_TAG,
        "pulls": normalized_pulls,
        "release_body": release_body,
        "repository": REPOSITORY,
        "schema_version": 1,
        "tag": TAG,
    }


def canonical_snapshot_bytes(snapshot: dict) -> bytes:
    return (json.dumps(snapshot, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def resign_persisted_payload(body: str) -> str:
    marker_index = body.rfind("\n\n<!-- release-note-composer-snapshot:v1 ")
    if marker_index < 0:
        raise AssertionError("persisted body has no snapshot marker")
    payload = body[:marker_index]
    marker = body[marker_index:]
    before_digest, separator, digest_and_suffix = marker.partition("payload_sha256=")
    _old_digest, suffix_separator, suffix = digest_and_suffix.partition(" ")
    if not separator or not suffix_separator:
        raise AssertionError("persisted body has no payload digest field")
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{payload}{before_digest}{separator}{digest}{suffix_separator}{suffix}"


def run_fixture(fixture: dict) -> subprocess.CompletedProcess[str]:
    snapshot = release_snapshot(
        fixture.get("compare", {}),
        fixture.get("pulls", {}),
        release_body=fixture.get("release_body", RAW_BODY),
        compare_headers=fixture.get("compare_headers", {}),
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        fixture_path = Path(tmp_dir) / "fixture.json"
        fixture_path.write_bytes(canonical_snapshot_bytes(snapshot))
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--tag",
                "speckit-pro-v2.19.0",
                "--dry-run",
                "--fixture",
                str(fixture_path),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )


def run_validation(*, title: str, body: str = "", labels: tuple[str, ...] = (), draft: bool = False) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.update(
        {
            "PR_TITLE": title,
            "PR_BODY": body,
            "PR_LABELS_JSON": json.dumps(labels),
            "PR_DRAFT": str(draft).lower(),
        }
    )
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--validate-pr"],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


class ComposeReleaseNotesTests(unittest.TestCase):
    @inventory_check
    def test_previous_tag_and_compare_discovery(self) -> None:
        self.assertEqual(
            COMPOSER.parse_previous_tag(RAW_BODY, "speckit-pro-v2.19.0"),
            "speckit-pro-v2.18.0",
        )
        commits = COMPOSER.discover_commits(
            compare_payload(
                "feat(scope)!: Add public highlights (#101)\n\nDetails",
                "docs: Clarify installation (#102)",
            ),
            {},
        )
        self.assertEqual([commit.pr_number for commit in commits], [101, 102])
        self.assertEqual([commit.kind for commit in commits], ["feat", "docs"])
        self.assertEqual(commits[0].subject, "feat(scope)!: Add public highlights (#101)")

    @inventory_check
    def test_merge_commit_ranges_resolve_prs_and_skip_inner_commits(self) -> None:
        commits = COMPOSER.discover_commits(
            compare_payload(
                "feat(autopilot): harden durable marker planning",
                "docs(release): record composition coverage",
                "Merge pull request #314 from racecraft-lab/xplat-010-review/03-us1"
                "\n\nfeat(xplat-010): replace Bash suite orchestration with Python",
                "Merge pull request #326 from racecraft-lab/xplat-010-review/15-release-contract"
                "\n\nfeat(xplat-010): validate consumer release-note blocks",
                "Merge pull request #331 from racecraft-lab/docs-constitution-python",
                "fix(tooling): complete repository Bash cleanup (#337)",
            ),
            {},
        )
        self.assertEqual([commit.pr_number for commit in commits], [314, 326, 331, 337])
        self.assertEqual([commit.kind for commit in commits], ["feat", "feat", "", "fix"])
        self.assertEqual(
            commits[0].subject,
            "feat(xplat-010): replace Bash suite orchestration with Python",
        )

        body = COMPOSER.compose_release_body(
            RAW_BODY,
            commits,
            {
                314: pull(
                    "feat(xplat-010): replace Bash suite orchestration with Python",
                    "```release-note\nThe test suite now runs on Python alone.\n```",
                ),
                326: pull("feat(xplat-010): validate consumer release-note blocks"),
                331: pull("docs(constitution): align governance with Python tooling"),
                337: pull("fix(tooling): complete repository Bash cleanup"),
            },
            compare_commit_count=6,
        )
        self.assertIn("- The test suite now runs on Python alone.", body)
        self.assertIn("- validate consumer release-note blocks", body)
        self.assertIn("- complete repository Bash cleanup", body)
        self.assertNotIn("Merge pull request", body.split("## Commit appendix")[0])

        with self.assertRaisesRegex(COMPOSER.CompositionError, "resolved no pull requests"):
            COMPOSER.discover_commits(
                compare_payload("feat(autopilot): harden durable marker planning"),
                {},
            )

    @inventory_check
    def test_compare_commit_count_survives_pull_request_deduplication(self) -> None:
        commits = COMPOSER.discover_commits(
            compare_payload(
                "feat: Add release notes (#101)",
                "fix: Polish release notes (#101)",
            ),
            {},
        )
        self.assertEqual(len(commits), 1)

        body = COMPOSER.compose_release_body(
            RAW_BODY,
            commits,
            {101: pull("feat: Add release notes")},
            compare_commit_count=2,
        )
        self.assertIn(" compare_commit_count=2 -->", body)

        snapshot = COMPOSER.load_persisted_snapshot(body, RAW_BODY)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.compare_commit_count, 2)

    @inventory_check
    def test_sanitized_empty_block_fails_composition(self) -> None:
        body = """```release-note
&lt;img src=x&gt; !&#91;tracking&#93;(https://example.test/pixel.png)
```
"""
        commits = COMPOSER.discover_commits(compare_payload("feat: Add release notes (#101)"), {})
        with self.assertRaisesRegex(COMPOSER.CompositionError, "empty after sanitization"):
            COMPOSER.compose_release_body(
                RAW_BODY,
                commits,
                {101: pull("feat: Mutable fallback", body)},
                compare_commit_count=1,
            )

    @inventory_check
    def test_highlights_harvest_every_pr_and_apply_fallbacks(self) -> None:
        commits = COMPOSER.discover_commits(
            compare_payload(
                "feat: Add composer (#101)",
                "fix(core): Repair fallback (#102)",
                "docs: Explain release notes (#103)",
                "chore: Internal-only cleanup (#104)",
            ),
            {},
        )
        pulls = {
            101: pull("feat: Add composer", "```release-note\nReadable composer notes.\n```"),
            102: pull("fix(core): Repair fallback"),
            103: pull("docs: Explain release notes", "~~~release-note\nDocs are easier to navigate.\n~~~"),
            104: pull(
                "chore: Internal-only cleanup",
                "```release-note\nThis must be omitted.\n```",
                "release-note/skip",
            ),
        }
        body = COMPOSER.compose_release_body(
            RAW_BODY,
            commits,
            pulls,
            compare_commit_count=4,
        )
        self.assertTrue(body.startswith("## Highlights\n\n"))
        self.assertIn("- Readable composer notes.", body)
        self.assertIn("- Repair fallback", body)
        self.assertIn("- Docs are easier to navigate.", body)
        self.assertNotIn("This must be omitted.", body)
        snapshot = COMPOSER.load_persisted_snapshot(body, RAW_BODY)
        self.assertIsNotNone(snapshot)
        self.assertTrue(snapshot.payload.endswith(RAW_BODY))
        self.assertEqual(body.count("## Commit appendix"), 1)

    @inventory_check
    def test_partial_fallback_uses_sanitized_immutable_subject(self) -> None:
        commits = COMPOSER.discover_commits(
            compare_payload(
                "feat: # &lt;strong&gt;Stable subject&lt;/strong&gt; "
                "!&#91;leak&#93;(https://example.test/leak.png) (#101)",
                "docs: Consumer documentation (#102)",
            ),
            {},
        )
        body = COMPOSER.compose_release_body(
            RAW_BODY,
            commits,
            {
                101: pull(
                    "feat: # <strong>Mutable title</strong> ![other](https://example.test/other.png)"
                ),
                102: pull("docs: Consumer documentation", "```release-note\nReadable docs.\n```"),
            },
            compare_commit_count=2,
        )

        self.assertIn("- \\# Stable subject", body)
        self.assertNotIn("Mutable title", body)
        self.assertNotIn("<strong>", body)
        self.assertNotIn("![", body)
        self.assertNotIn("leak.png", body)

    def test_fallback_subject_caps_249_250_251_character_boundaries(self) -> None:
        for length in (249, 250, 251):
            with self.subTest(msg=f"fallback subject length {length}"):
                subject_text = "x" * length
                commits = COMPOSER.discover_commits(
                    compare_payload(f"feat: {subject_text} (#101)"),
                    {},
                )
                body = COMPOSER.compose_release_body(
                    RAW_BODY,
                    commits,
                    {101: pull("feat: Mutable title")},
                    compare_commit_count=1,
                )
                payload = COMPOSER.load_persisted_snapshot(body, RAW_BODY).payload
                highlight = payload.split("## Highlights\n\n- ", 1)[1].split("\n\n## Commit appendix", 1)[0]
                expected = subject_text if length <= 250 else f"{'x' * 247}..."
                self.assertEqual(highlight, expected)
                self.assertEqual(len(highlight), min(length, 250))

    @inventory_check
    def test_zero_blocks_degrade_all_non_skipped_subjects(self) -> None:
        commits = COMPOSER.discover_commits(
            compare_payload("feat: Add feature (#101)", "docs: Explain feature (#102)"),
            {},
        )
        body = COMPOSER.compose_release_body(
            RAW_BODY,
            commits,
            {
                101: pull("feat: Add feature"),
                102: pull("docs: Explain feature"),
            },
            compare_commit_count=2,
        )
        self.assertIn("- Add feature", body)
        self.assertIn("- Explain feature", body)

    @inventory_check
    def test_zero_blocks_use_sanitized_immutable_commit_subjects(self) -> None:
        commits = COMPOSER.discover_commits(
            compare_payload(
                "feat: &lt;strong&gt;Stable feature&lt;/strong&gt; "
                "!&#91;secret&#93;(https://example.test/leak.png) (#101)",
                "docs: Stable documentation (#102)",
            ),
            {},
        )
        first = COMPOSER.compose_release_body(
            RAW_BODY,
            commits,
            {
                101: pull("feat: First mutable title"),
                102: pull("docs: First mutable docs title"),
            },
            compare_commit_count=2,
        )
        second = COMPOSER.compose_release_body(
            RAW_BODY,
            commits,
            {
                101: pull("feat: Second mutable title"),
                102: pull("docs: Second mutable docs title"),
            },
            compare_commit_count=2,
        )

        self.assertEqual(first, second)
        self.assertIn("- Stable feature", first)
        self.assertIn("- Stable documentation", first)
        self.assertNotIn("mutable", first.lower())
        self.assertNotIn("![", first)
        self.assertNotIn("leak.png", first)

    @inventory_check
    def test_composition_is_idempotent_from_raw_body_only(self) -> None:
        commits = COMPOSER.discover_commits(compare_payload("feat: Add composer (#101)"), {})
        pulls = {101: pull("feat: Add composer", "```release-note\nReadable notes.\n```")}
        first = COMPOSER.compose_release_body(
            RAW_BODY,
            commits,
            pulls,
            compare_commit_count=1,
        )
        second = COMPOSER.compose_release_body(
            RAW_BODY,
            commits,
            pulls,
            compare_commit_count=1,
        )
        self.assertEqual(first, second)
        self.assertEqual(first.count(RAW_BODY), 1)
        self.assertNotIn("#999", first.split("## Commit appendix", 1)[0])
        snapshot = COMPOSER.load_persisted_snapshot(first, RAW_BODY)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.compare_commit_count, 1)
        self.assertEqual(snapshot.body_sha256, hashlib.sha256(first.encode("utf-8")).hexdigest())
        self.assertIn(snapshot.payload_sha256, first)

        tampered = first.replace("Readable notes.", "Tampered notes.", 1)
        with self.assertRaisesRegex(COMPOSER.CompositionError, "digest"):
            COMPOSER.load_persisted_snapshot(tampered, RAW_BODY)

        marker_index = first.rfind("\n\n<!-- release-note-composer-snapshot:v1 ")
        duplicated_marker = first[:marker_index] + first[marker_index:] + first[marker_index:]
        with self.assertRaisesRegex(COMPOSER.CompositionError, "unique"):
            COMPOSER.load_persisted_snapshot(duplicated_marker, RAW_BODY)

    @inventory_check
    def test_dry_run_uses_offline_json_fixture(self) -> None:
        fixture = {
            "release_body": RAW_BODY,
            "compare": compare_payload("feat: Add composer (#101)"),
            "compare_headers": {},
            "pulls": {
                "101": pull("feat: Add composer", "```release-note\nReadable notes.\n```")
            },
        }
        first = run_fixture(fixture)
        second = run_fixture(fixture)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout.encode(), second.stdout.encode())
        self.assertTrue(first.stdout.startswith("## Highlights\n\n- Readable notes."))
        snapshot = COMPOSER.load_persisted_snapshot(first.stdout, RAW_BODY)
        self.assertIsNotNone(snapshot)
        self.assertTrue(snapshot.payload.endswith(RAW_BODY))
        self.assertEqual(first.stderr, "")

        quickstart = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--tag",
                "speckit-pro-v2.19.0",
                "--dry-run",
                "--fixture",
                str(QUICKSTART_FIXTURE),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(quickstart.returncode, 0, quickstart.stderr)
        self.assertTrue(quickstart.stdout.startswith("## Highlights\n\n- GitHub Releases now open"))
        self.assertIn("## Commit appendix\n", quickstart.stdout)
        self.assertNotIn("tracking", quickstart.stdout)
        self.assertIsNotNone(COMPOSER.load_persisted_snapshot(quickstart.stdout, RAW_BODY))

    @inventory_check
    def test_canonical_snapshot_loader_verifies_bytes_schema_and_digest(self) -> None:
        snapshot_value = release_snapshot(
            compare_payload("feat: Add composer (#101)"),
            {101: pull("ignored title", "```release-note\nReadable notes.\n```")},
        )
        encoded = canonical_snapshot_bytes(snapshot_value)
        digest = hashlib.sha256(encoded).hexdigest()
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "snapshot.json"
            path.write_bytes(encoded)
            loaded = COMPOSER.load_release_input_snapshot(
                str(path),
                expected_sha256=digest,
                expected_repository=REPOSITORY,
                expected_tag=TAG,
            )
            self.assertEqual(loaded.sha256, digest)
            self.assertEqual(loaded.raw_body, RAW_BODY)
            self.assertEqual(loaded.previous_tag, PREVIOUS_TAG)
            self.assertEqual([commit.pr_number for commit in loaded.commits], [101])
            self.assertEqual(loaded.pulls[101]["labels"], [])

            path.write_text(json.dumps(snapshot_value, indent=2), encoding="utf-8")
            with self.assertRaisesRegex(COMPOSER.CompositionError, "canonical"):
                COMPOSER.load_release_input_snapshot(str(path), expected_sha256=digest)

            path.write_bytes(encoded)
            with self.assertRaisesRegex(COMPOSER.CompositionError, "digest"):
                COMPOSER.load_release_input_snapshot(str(path), expected_sha256="0" * 64)

    @inventory_check
    def test_capture_mode_writes_complete_canonical_snapshot(self) -> None:
        class FakeClient:
            instances: list["FakeClient"] = []

            def __init__(self, repository: str, token: str, **_kwargs: object) -> None:
                self.repository = repository
                self.token = token
                self.calls: list[tuple[str, str, object]] = []
                self.__class__.instances.append(self)

            def request_json(self, method: str, path: str, payload=None):  # type: ignore[no-untyped-def]
                self.calls.append((method, path, payload))
                if "/compare/" in path:
                    return compare_payload("feat: Stable subject (#101)"), {}
                if path.endswith("/pulls/101"):
                    return pull(
                        "mutable title must not be captured",
                        "```release-note\nCaptured note.\n```",
                        "z-label",
                        "a-label",
                    ), {}
                raise AssertionError(f"unexpected request: {method} {path}")

        environment = {
            "RELEASE_BODY": RAW_BODY,
            "GITHUB_REPOSITORY": REPOSITORY,
            "GITHUB_TOKEN": "built-in-token",
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "release-note-snapshot.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.object(COMPOSER, "GitHubClient", FakeClient),
                mock.patch.dict(COMPOSER.os.environ, environment, clear=True),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                returncode = COMPOSER.run(
                    [
                        "--tag",
                        TAG,
                        "--capture-snapshot",
                        "--snapshot-output",
                        str(output_path),
                    ]
                )

            self.assertEqual(returncode, 0, stderr.getvalue())
            snapshot_bytes = output_path.read_bytes()
            snapshot_value = json.loads(snapshot_bytes)
            self.assertEqual(snapshot_bytes, canonical_snapshot_bytes(snapshot_value))
            self.assertEqual(set(snapshot_value["pulls"]["101"]), {"body", "labels"})
            self.assertEqual(snapshot_value["pulls"]["101"]["labels"], ["a-label", "z-label"])
            self.assertNotIn("mutable title", snapshot_bytes.decode())
            result = json.loads(stdout.getvalue())
            self.assertEqual(result["snapshot_sha256"], hashlib.sha256(snapshot_bytes).hexdigest())
            self.assertEqual(result["commit_count"], 1)
            self.assertEqual(result["pull_request_count"], 1)

    @inventory_check
    def test_pr_template_seeds_one_empty_release_note_fence(self) -> None:
        template = PR_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("## Release note\n", template)
        self.assertEqual(template.count("```release-note"), 1)
        self.assertIsNone(COMPOSER.extract_release_note(template))

    def test_required_check_fails_feat_fix_without_exactly_one_nonempty_block(self) -> None:
        bodies = (
            "",
            "```release-note\n\n```",
            "```release-note\nOne\n```\n```release-note\nTwo\n```",
            "````release-note\nShort close\n```",
        )
        for title in ("feat: Add release notes", "fix(core)!: Repair release notes"):
            for index, body in enumerate(bodies, start=1):
                with self.subTest(msg=f"{title} missing-note case {index}"):
                    completed = run_validation(title=title, body=body)
                    self.assertEqual(completed.returncode, 1)
                    self.assertIn("release_note_validation_failed", completed.stderr)
                    self.assertEqual(completed.stdout, "")

    def test_required_check_accepts_valid_skip_draft_nonreleasable_and_autorelease_cases(self) -> None:
        cases = (
            {"title": "feat: Add notes", "body": "```release-note\nReadable notes.\n```"},
            {"title": "fix: Internal fix", "labels": ("release-note/skip",)},
            {"title": "feat: Draft work", "draft": True},
            {"title": "docs: Explain notes"},
            {"title": "feat: Release automation", "labels": ("autorelease: pending",)},
            {"title": "chore(main): release speckit-pro 2.19.0"},
        )
        for index, case in enumerate(cases, start=1):
            with self.subTest(msg=f"accept required-check case {index}: {case['title']}"):
                completed = run_validation(**case)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("release_note_validation_passed", completed.stdout)
                self.assertEqual(completed.stderr, "")

    @inventory_check
    def test_required_check_rejects_malformed_env_without_shell_execution(self) -> None:
        environment = os.environ.copy()
        environment.update(
            {
                "PR_TITLE": "feat: $(touch should-not-run)",
                "PR_BODY": "```release-note\nSafe literal $(touch should-not-run).\n```",
                "PR_LABELS_JSON": "not-json",
                "PR_DRAFT": "false",
            }
        )
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--validate-pr"],
            cwd=REPO_ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("release_note_composition_failed", completed.stderr)
        self.assertFalse((REPO_ROOT / "should-not-run").exists())

    def test_dry_run_fails_loud_on_under_enumeration_and_unresolved_pr(self) -> None:
        cases = {
            "truncated": {
                "release_body": RAW_BODY,
                "compare": compare_payload("feat: Add composer (#101)", total_commits=2),
                "pulls": {"101": pull("feat: Add composer")},
            },
            "paginated": {
                "release_body": RAW_BODY,
                "compare": compare_payload("feat: Add composer (#101)"),
                "compare_headers": {"Link": '<https://api.github.test/next>; rel="next"'},
                "pulls": {"101": pull("feat: Add composer")},
            },
            "missing-suffix": {
                "release_body": RAW_BODY,
                "compare": compare_payload("feat: Add composer"),
                "pulls": {},
            },
            "unresolved-pr": {
                "release_body": RAW_BODY,
                "compare": compare_payload("feat: Add composer (#101)"),
                "pulls": {},
            },
            "compare-http-error": {
                "release_body": RAW_BODY,
                "compare": {},
                "pulls": {"101": pull("feat: Add composer")},
            },
        }
        for name, fixture in cases.items():
            with self.subTest(msg=f"dry-run failure: {name}"):
                completed = run_fixture(fixture)
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(completed.stderr.count("release_note_composition_failed"), 1)
                self.assertEqual(completed.stdout, "")

    @inventory_check
    def test_compare_api_accepts_250_commits_and_rejects_251(self) -> None:
        subjects_250 = tuple(f"docs: Commit {number} (#{number})" for number in range(1, 251))
        commits = COMPOSER.discover_commits(compare_payload(*subjects_250), {})
        self.assertEqual(len(commits), 250)

        subjects_251 = subjects_250 + ("docs: Commit 251 (#251)",)
        with self.assertRaisesRegex(COMPOSER.CompositionError, "250"):
            COMPOSER.discover_commits(compare_payload(*subjects_251), {})

        with self.assertRaisesRegex(COMPOSER.CompositionError, "truncated"):
            COMPOSER.discover_commits(
                compare_payload(*subjects_250, total_commits=251),
                {},
            )

    def test_http_and_transient_failures_have_no_in_process_retry(self) -> None:
        failures = [
            urllib.error.HTTPError("https://api.github.test", status, "failed", {}, io.BytesIO(b"{}"))
            for status in (403, 429, 500)
        ]
        failures.append(urllib.error.URLError("temporary DNS failure"))
        for failure in failures:
            with self.subTest(msg=f"transport failure: {type(failure).__name__}:{getattr(failure, 'code', None)}"):
                client = COMPOSER.GitHubClient("racecraft-lab/repo", "token")
                with mock.patch.object(COMPOSER.urllib.request, "urlopen", side_effect=failure) as urlopen:
                    with self.assertRaises(COMPOSER.CompositionError):
                        client.request_json("GET", "/repos/racecraft-lab/repo/compare/a...b")
                urlopen.assert_called_once()

    @inventory_check
    def test_incomplete_http_read_is_a_single_fail_loud_transport_error(self) -> None:
        response = mock.MagicMock()
        response.__enter__.return_value.read.side_effect = http.client.IncompleteRead(
            b'{"partial":',
            10,
        )
        client = COMPOSER.GitHubClient("racecraft-lab/repo", "token")
        with mock.patch.object(COMPOSER.urllib.request, "urlopen", return_value=response) as urlopen:
            with self.assertRaisesRegex(COMPOSER.CompositionError, "transport error"):
                client.request_json("GET", "/repos/racecraft-lab/repo/compare/a...b")
        urlopen.assert_called_once()

    @inventory_check
    def test_live_path_resolves_release_by_tag_then_patches_audited_raw_body_appendix(self) -> None:
        class FakeClient:
            instances: list["FakeClient"] = []

            def __init__(self, repository: str, token: str, **_kwargs: object) -> None:
                self.repository = repository
                self.token = token
                self.calls: list[tuple[str, str, object]] = []
                self.__class__.instances.append(self)

            def request_json(self, method: str, path: str, payload=None):  # type: ignore[no-untyped-def]
                self.calls.append((method, path, payload))
                if "/releases/tags/" in path:
                    return {"id": 777, "body": RAW_BODY}, {}
                if path.endswith("/releases/777") and method == "PATCH":
                    return {"id": 777}, {}
                if "/compare/" in path or "/pulls/" in path:
                    raise AssertionError("composer re-fetched mutable Compare/PR metadata")
                raise AssertionError(f"unexpected request: {method} {path}")

        stdout = io.StringIO()
        stderr = io.StringIO()
        snapshot_value = release_snapshot(
            compare_payload("feat: Add composer (#101)"),
            {101: pull("ignored title", "```release-note\nReadable notes.\n```")},
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_path = Path(tmp_dir) / "snapshot.json"
            snapshot_bytes = canonical_snapshot_bytes(snapshot_value)
            snapshot_path.write_bytes(snapshot_bytes)
            environment = {
                "EXPECTED_SNAPSHOT_SHA256": hashlib.sha256(snapshot_bytes).hexdigest(),
                "GITHUB_REPOSITORY": REPOSITORY,
                "GITHUB_TOKEN": "built-in-token",
                "RELEASE_NOTES_SNAPSHOT": str(snapshot_path),
            }
            with (
                mock.patch.object(COMPOSER, "GitHubClient", FakeClient),
                mock.patch.dict(COMPOSER.os.environ, environment, clear=True),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                returncode = COMPOSER.run(["--tag", TAG])

        self.assertEqual(returncode, 0, stderr.getvalue())
        client = FakeClient.instances[-1]
        self.assertEqual(
            [(method, path) for method, path, _payload in client.calls],
            [
                ("GET", "/repos/racecraft-lab/racecraft-plugins-public/releases/tags/speckit-pro-v2.19.0"),
                ("PATCH", "/repos/racecraft-lab/racecraft-plugins-public/releases/777"),
            ],
        )
        patch_body = client.calls[-1][2]["body"]
        snapshot = COMPOSER.load_persisted_snapshot(patch_body, RAW_BODY)
        self.assertIsNotNone(snapshot)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["outcome"], "release_note_composed")
        self.assertEqual(result["body_sha256"], hashlib.sha256(patch_body.encode("utf-8")).hexdigest())
        self.assertEqual(result["body_byte_count"], len(patch_body.encode("utf-8")))
        self.assertEqual(result["commit_count"], 1)
        self.assertEqual(result["snapshot_byte_count"], len(snapshot_bytes))
        self.assertEqual(result["snapshot_payload_sha256"], snapshot.payload_sha256)
        self.assertEqual(result["snapshot_source_sha256"], hashlib.sha256(snapshot_bytes).hexdigest())
        self.assertFalse(result["snapshot_reused"])
        self.assertEqual(stderr.getvalue(), "")

    @inventory_check
    def test_live_rerun_reuses_persisted_snapshot_despite_mutable_pr_metadata(self) -> None:
        class FakeClient:
            release_body = RAW_BODY
            mutable_remote_pull = pull("feat: First title", "```release-note\nFirst note.\n```")
            instances: list["FakeClient"] = []
            patched_bodies: list[str] = []

            def __init__(self, repository: str, token: str, **_kwargs: object) -> None:
                self.repository = repository
                self.token = token
                self.calls: list[tuple[str, str, object]] = []
                self.__class__.instances.append(self)

            def request_json(self, method: str, path: str, payload=None):  # type: ignore[no-untyped-def]
                self.calls.append((method, path, payload))
                if "/releases/tags/" in path:
                    return {"id": 777, "body": self.__class__.release_body}, {}
                if path.endswith("/releases/777") and method == "PATCH":
                    body = payload["body"]
                    self.__class__.release_body = body
                    self.__class__.patched_bodies.append(body)
                    return {"id": 777}, {}
                if "/compare/" in path or "/pulls/" in path:
                    raise AssertionError("composer re-fetched mutable Compare/PR metadata")
                raise AssertionError(f"unexpected request: {method} {path}")

        snapshot_value = release_snapshot(
            compare_payload("feat: Stable commit subject (#101)"),
            {101: pull("ignored title", "```release-note\nFirst note.\n```")},
        )
        outputs: list[dict] = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_path = Path(tmp_dir) / "snapshot.json"
            snapshot_bytes = canonical_snapshot_bytes(snapshot_value)
            snapshot_path.write_bytes(snapshot_bytes)
            environment = {
                "EXPECTED_SNAPSHOT_SHA256": hashlib.sha256(snapshot_bytes).hexdigest(),
                "GITHUB_REPOSITORY": REPOSITORY,
                "GITHUB_TOKEN": "built-in-token",
                "RELEASE_NOTES_SNAPSHOT": str(snapshot_path),
            }
            with mock.patch.object(COMPOSER, "GitHubClient", FakeClient), mock.patch.dict(
                COMPOSER.os.environ,
                environment,
                clear=True,
            ):
                for mutable_pull in (
                    pull("feat: First title", "```release-note\nFirst note.\n```"),
                    pull("feat: Mutated title", "```release-note\nMutated note.\n```"),
                ):
                    FakeClient.mutable_remote_pull = mutable_pull
                    stdout = io.StringIO()
                    stderr = io.StringIO()
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        returncode = COMPOSER.run(["--tag", TAG])
                    self.assertEqual(returncode, 0, stderr.getvalue())
                    outputs.append(json.loads(stdout.getvalue()))

        self.assertEqual(FakeClient.patched_bodies[0], FakeClient.patched_bodies[1])
        self.assertIn("First note.", FakeClient.patched_bodies[1])
        self.assertNotIn("Mutated note.", FakeClient.patched_bodies[1])
        self.assertFalse(outputs[0]["snapshot_reused"])
        self.assertTrue(outputs[1]["snapshot_reused"])
        self.assertEqual(
            [(method, path) for method, path, _payload in FakeClient.instances[-1].calls],
            [
                ("GET", "/repos/racecraft-lab/racecraft-plugins-public/releases/tags/speckit-pro-v2.19.0"),
                ("PATCH", "/repos/racecraft-lab/racecraft-plugins-public/releases/777"),
            ],
        )

    @inventory_check
    def test_live_reuse_rejects_tampered_payload_with_recomputed_digest(self) -> None:
        snapshot_value = release_snapshot(
            compare_payload("feat: Stable commit subject (#101)"),
            {101: pull("ignored title", "```release-note\nCanonical note.\n```")},
        )
        snapshot_bytes = canonical_snapshot_bytes(snapshot_value)
        snapshot_sha256 = hashlib.sha256(snapshot_bytes).hexdigest()
        canonical_body = COMPOSER.compose_release_body(
            RAW_BODY,
            COMPOSER.discover_commits(snapshot_value["compare"], {}),
            {101: snapshot_value["pulls"]["101"]},
            compare_commit_count=1,
            source_sha256=snapshot_sha256,
        )
        tampered_body = canonical_body.replace("Canonical note.", "Attacker-controlled note.", 1)
        resigned_body = resign_persisted_payload(tampered_body)
        self.assertIn(f"source_sha256={snapshot_sha256}", resigned_body)
        self.assertNotEqual(canonical_body, resigned_body)

        class FakeClient:
            calls: list[tuple[str, str, object]] = []

            def __init__(self, repository: str, token: str, **_kwargs: object) -> None:
                self.repository = repository
                self.token = token

            def request_json(self, method: str, path: str, payload=None):  # type: ignore[no-untyped-def]
                self.__class__.calls.append((method, path, payload))
                if "/releases/tags/" in path:
                    return {"id": 777, "body": resigned_body}, {}
                if path.endswith("/releases/777") and method == "PATCH":
                    return {"id": 777}, {}
                raise AssertionError(f"unexpected request: {method} {path}")

        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_path = Path(tmp_dir) / "snapshot.json"
            snapshot_path.write_bytes(snapshot_bytes)
            environment = {
                "EXPECTED_SNAPSHOT_SHA256": snapshot_sha256,
                "GITHUB_REPOSITORY": REPOSITORY,
                "GITHUB_TOKEN": "built-in-token",
                "RELEASE_NOTES_SNAPSHOT": str(snapshot_path),
            }
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.object(COMPOSER, "GitHubClient", FakeClient),
                mock.patch.dict(COMPOSER.os.environ, environment, clear=True),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                returncode = COMPOSER.run(["--tag", TAG])

        self.assertEqual(returncode, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue().count("release_note_composition_failed"), 1)
        self.assertIn("canonical", stderr.getvalue())
        self.assertEqual(
            [(method, path) for method, path, _payload in FakeClient.calls],
            [("GET", "/repos/racecraft-lab/racecraft-plugins-public/releases/tags/speckit-pro-v2.19.0")],
        )

    @inventory_check
    def test_failed_patch_rerun_recomposes_identical_bytes_from_same_snapshot(self) -> None:
        class FakeClient:
            patch_attempts = 0
            attempted_bodies: list[str] = []
            mutable_remote_pull = pull("feat: First title", "```release-note\nFirst note.\n```")

            def __init__(self, repository: str, token: str, **_kwargs: object) -> None:
                self.repository = repository
                self.token = token
                self.calls: list[tuple[str, str, object]] = []

            def request_json(self, method: str, path: str, payload=None):  # type: ignore[no-untyped-def]
                self.calls.append((method, path, payload))
                if "/releases/tags/" in path:
                    return {"id": 777, "body": RAW_BODY}, {}
                if path.endswith("/releases/777") and method == "PATCH":
                    self.__class__.patch_attempts += 1
                    self.__class__.attempted_bodies.append(payload["body"])
                    if self.__class__.patch_attempts == 1:
                        raise COMPOSER.CompositionError("simulated PATCH transport failure")
                    return {"id": 777}, {}
                if "/compare/" in path or "/pulls/" in path:
                    raise AssertionError("composer re-fetched mutable Compare/PR metadata")
                raise AssertionError(f"unexpected request: {method} {path}")

        snapshot_value = release_snapshot(
            compare_payload("feat: Stable commit subject (#101)"),
            {101: pull("ignored title", "```release-note\nCaptured first note.\n```")},
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_path = Path(tmp_dir) / "snapshot.json"
            snapshot_bytes = canonical_snapshot_bytes(snapshot_value)
            snapshot_path.write_bytes(snapshot_bytes)
            environment = {
                "EXPECTED_SNAPSHOT_SHA256": hashlib.sha256(snapshot_bytes).hexdigest(),
                "GITHUB_REPOSITORY": REPOSITORY,
                "GITHUB_TOKEN": "built-in-token",
                "RELEASE_NOTES_SNAPSHOT": str(snapshot_path),
            }
            with mock.patch.object(COMPOSER, "GitHubClient", FakeClient), mock.patch.dict(
                COMPOSER.os.environ,
                environment,
                clear=True,
            ):
                first_stdout = io.StringIO()
                first_stderr = io.StringIO()
                with contextlib.redirect_stdout(first_stdout), contextlib.redirect_stderr(first_stderr):
                    first_returncode = COMPOSER.run(["--tag", TAG])

                FakeClient.mutable_remote_pull = pull(
                    "feat: Mutated title",
                    "```release-note\nMutated remote note.\n```",
                )
                second_stdout = io.StringIO()
                second_stderr = io.StringIO()
                with contextlib.redirect_stdout(second_stdout), contextlib.redirect_stderr(second_stderr):
                    second_returncode = COMPOSER.run(["--tag", TAG])

        self.assertEqual(first_returncode, 1)
        self.assertEqual(first_stdout.getvalue(), "")
        self.assertEqual(first_stderr.getvalue().count("release_note_composition_failed"), 1)
        self.assertEqual(second_returncode, 0, second_stderr.getvalue())
        self.assertEqual(FakeClient.attempted_bodies[0], FakeClient.attempted_bodies[1])
        self.assertIn("Captured first note.", FakeClient.attempted_bodies[1])
        self.assertNotIn("Mutated remote note.", FakeClient.attempted_bodies[1])
        self.assertFalse(json.loads(second_stdout.getvalue())["snapshot_reused"])

    @inventory_check
    def test_networking_and_dependencies_stay_stdlib_only(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        self.assertIn("urllib", imports)
        self.assertTrue({"requests", "httpx", "openai", "subprocess"}.isdisjoint(imports))


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ComposeReleaseNotesTests)


def main() -> int:
    return run_counted(build_suite(), label="test-compose-release-notes")


if __name__ == "__main__":
    raise SystemExit(main())
