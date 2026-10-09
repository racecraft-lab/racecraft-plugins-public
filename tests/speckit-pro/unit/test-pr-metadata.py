#!/usr/bin/env python3
"""Regression coverage for authenticated manual PR metadata checks."""

from __future__ import annotations

import copy
import io
import json
import tempfile
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from script_loader import load_script  # noqa: E402
from test_result import run_counted  # noqa: E402


dispatch = load_script(
    "metadata_release_dispatch", REPO_ROOT / "scripts" / "dispatch-release-pr-checks.py"
)


class ManualMetadataDispatchTests(unittest.TestCase):
    def test_release_dispatch_supplies_only_the_pr_number(self) -> None:
        run = mock.Mock()

        dispatch.dispatch_release_pr_checks(
            [{"branch": "release-branch", "number": "302", "title": "stale title"}],
            run=run,
        )

        self.assertEqual(
            [
                "gh", "workflow", "run", "pr-metadata.yml", "--ref",
                "release-branch", "-f", "pr_number=302",
            ],
            run.call_args_list[1].args[0],
        )


class LiveMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.metadata = load_script("pr_metadata", REPO_ROOT / "scripts" / "pr_metadata.py")
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "output"
        self.environment = {
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REPOSITORY": "example/project",
            "GITHUB_REF": "refs/heads/release-branch",
            "GITHUB_SHA": "a" * 40,
            "PR_NUMBER": "302",
            "GH_TOKEN": "test-token",
            "GITHUB_API_URL": "https://api.github.com",
            "GITHUB_OUTPUT": str(self.output),
            "PR_TITLE": "forged title",
            "PR_BODY": "forged body",
        }
        self.pr = {
            "number": 302,
            "state": "open",
            "base": {"repo": {"full_name": "example/project"}},
            "head": {
                "ref": "release-branch",
                "sha": "a" * 40,
                "repo": {"full_name": "example/project", "fork": False},
            },
            "title": "fix(ci): use live metadata",
            "body": "Live release note",
            "labels": [{"name": "release-note/skip"}],
            "draft": False,
        }

    def invoke(self, pr=None, environment=None):
        paths: list[str] = []

        def fetch(path):
            paths.append(path)
            return self.pr if pr is None else pr

        with redirect_stderr(io.StringIO()) as errors:
            status = self.metadata.main(
                self.environment if environment is None else environment, fetch=fetch
            )
        return status, paths, errors.getvalue()

    def test_reads_actual_metadata_from_the_pull_request_endpoint(self) -> None:
        status, paths, errors = self.invoke()
        self.assertEqual((0, ["/repos/example/project/pulls/302"], ""), (status, paths, errors))
        self.assertEqual(
            {
                "title": "fix(ci): use live metadata",
                "body": "Live release note",
                "labels": ["release-note/skip"],
                "draft": False,
            },
            json.loads(self.output.read_text().removeprefix("metadata=")),
        )

    def test_rejects_each_live_identity_mismatch_before_emitting_metadata(self) -> None:
        mutations = [
            (("number",), 303),
            (("base", "repo", "full_name"), "other/project"),
            (("head", "repo", "full_name"), "fork/project"),
            (("head", "repo", "fork"), True),
            (("head", "ref"), "different-branch"),
            (("head", "sha"), "b" * 40),
            (("state",), "closed"),
        ]
        for keys, value in mutations:
            with self.subTest(field=".".join(keys), value=value):
                pr = copy.deepcopy(self.pr)
                field = pr
                for key in keys[:-1]:
                    field = field[key]
                field[keys[-1]] = value
                self.output.write_text("existing=preserved\n")
                status, paths, errors = self.invoke(pr)
                self.assertEqual(1, status)
                self.assertEqual(["/repos/example/project/pulls/302"], paths)
                self.assertTrue(errors)
                self.assertEqual("existing=preserved\n", self.output.read_text())

    def test_rejects_tag_and_missing_or_malformed_dispatch_identity_before_api(self) -> None:
        mutations = [
            ("GITHUB_REF", "refs/tags/release-branch"),
            ("GITHUB_REF", "release-branch"),
            ("GITHUB_REF", "refs/heads/"),
            ("GITHUB_SHA", "short-sha"),
            ("GITHUB_SHA", ""),
            ("GITHUB_REPOSITORY", "../project"),
            ("GITHUB_REPOSITORY", ""),
            ("PR_NUMBER", "0"),
            ("PR_NUMBER", "302/../303"),
            ("PR_NUMBER", ""),
            ("GITHUB_EVENT_NAME", "pull_request"),
        ]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                env = dict(self.environment, **{key: value})
                status, paths, errors = self.invoke(environment=env)
                self.assertEqual(1, status)
                self.assertEqual([], paths)
                self.assertTrue(errors)
                self.assertFalse(self.output.exists())

    def test_rejects_malformed_live_metadata_without_outputs(self) -> None:
        mutations = [
            ("title", None), ("title", ""), ("title", 123),
            ("body", False), ("body", 123),
            ("draft", None), ("draft", "false"),
            ("labels", {}), ("labels", [{"name": None}]),
            ("labels", [{"name": ""}]),
        ]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                pr = dict(self.pr, **{key: value})
                status, _paths, errors = self.invoke(pr)
                self.assertEqual(1, status)
                self.assertTrue(errors)
                self.assertFalse(self.output.exists())

    def test_draft_and_null_body_are_taken_from_api(self) -> None:
        pr = dict(self.pr, draft=True, body=None, labels=[])
        self.assertEqual(0, self.invoke(pr)[0])
        self.assertEqual(
            {"title": "fix(ci): use live metadata", "body": "", "labels": [], "draft": True},
            json.loads(self.output.read_text().removeprefix("metadata=")),
        )

    def test_output_escaping_round_trips_untrusted_text_without_new_output_keys(self) -> None:
        text = "note\r\nmetadata=forged\nEOF\n\u2028\x00${{ secrets.TOKEN }}"
        pr = dict(self.pr, title=text, body=text, labels=[{"name": text}])
        self.assertEqual(0, self.invoke(pr)[0])
        lines = self.output.read_text().splitlines()
        self.assertEqual(1, len(lines))
        self.assertEqual("metadata", lines[0].split("=", 1)[0])
        self.assertEqual(
            {"title": text, "body": text, "labels": [text], "draft": False},
            json.loads(lines[0].removeprefix("metadata=")),
        )

    def test_api_failures_and_missing_evidence_fail_closed(self) -> None:
        def failed_fetch(path):
            raise OSError("API unavailable")

        with redirect_stderr(io.StringIO()):
            self.assertEqual(1, self.metadata.main(self.environment, fetch=failed_fetch))
        self.assertFalse(self.output.exists())
        for field in self.pr:
            with self.subTest(missing=field):
                pr = dict(self.pr)
                del pr[field]
                self.assertEqual(1, self.invoke(pr)[0])
                self.assertFalse(self.output.exists())
        for pr in ([], "invalid", 42, {}):
            with self.subTest(response=pr):
                self.assertEqual(1, self.invoke(pr)[0])
                self.assertFalse(self.output.exists())


class MetadataWorkflowTests(unittest.TestCase):
    def test_manual_jobs_authenticate_before_validating_and_use_distinct_contexts(self) -> None:
        content = (REPO_ROOT / ".github" / "workflows" / "pr-metadata.yml").read_text()
        inputs = content.split("    inputs:\n", 1)[1].split("\n# Top-level:", 1)[0]
        self.assertIn("      pr_number:", inputs)
        self.assertNotIn("      pr_title:", inputs)
        self.assertNotIn("      pr_body:", inputs)
        for job, validator in (
            ("validate-pr-title", "Check PR title"),
            ("validate-release-note", "Validate release note block"),
        ):
            with self.subTest(job=job):
                block = content.split(f"  {job}:\n", 1)[1].split("\n  #", 1)[0]
                self.assertIn(f"'manual-{job}' || '{job}'", block)
                self.assertIn("pull-requests: read", block)
                self.assertLess(block.index("run: python3 scripts/pr_metadata.py"), block.index(validator))
                self.assertIn("PR_NUMBER: '${{ inputs.pr_number }}'", block)
                self.assertIn("fromJSON(steps.metadata.outputs.metadata).draft == false", block)
                self.assertIn("fromJSON(steps.metadata.outputs.metadata).title", block)
        self.assertIn("fromJSON(steps.metadata.outputs.metadata).body", content)
        self.assertIn("toJSON(fromJSON(steps.metadata.outputs.metadata).labels)", content)
        self.assertNotIn("inputs.pr_title", content)
        self.assertNotIn("inputs.pr_body", content)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-pr-metadata"))
