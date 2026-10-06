#!/usr/bin/env python3
"""Scaffold roadmap freshness: the checkout's roadmap is compared with the remote default branch.

A stale checkout must stop scaffold with a named cause and both revisions, before
any roadmap parsing or gate runs. The helper is exercised against real throwaway
Git repositories so the fetch, the default-branch lookup and the blob comparison
all run for real.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
import unittest.mock

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "speckit-pro"), str(REPO / "tests/speckit-pro/lib")]
from speckit_pro_runner.helpers.registry import HELPERS, dispatch_helper  # noqa: E402
from test_result import run_counted  # noqa: E402

HELPER_ID = "check-roadmap-freshness"
ROADMAP = "docs/ai/technical-roadmap.md"
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Fixture",
    "GIT_AUTHOR_EMAIL": "fixture" + chr(64) + "example.test",
    "GIT_COMMITTER_NAME": "Fixture",
    "GIT_COMMITTER_EMAIL": "fixture" + chr(64) + "example.test",
}


def git(cwd: Path, *args: str) -> str:
    env = {**os.environ, **GIT_ENV}
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=env, check=True)
    return done.stdout.strip()


def commit_roadmap(root: Path, text: str) -> str:
    path = root / ROADMAP
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    git(root, "add", ROADMAP)
    git(root, "commit", "-q", "-m", "roadmap")
    return git(root, "rev-parse", "HEAD")


def patch_environ(values: dict[str, str]):
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)

    def restore() -> None:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    return restore


class RoadmapFreshnessTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name).resolve()
        self.bare = base / "remote.git"
        self.session = base / "session"
        self.author = base / "author"
        self.addCleanup(patch_environ(GIT_ENV))
        git(base, "init", "-q", "--bare", "-b", "main", str(self.bare))
        git(base, "clone", "-q", str(self.bare), str(self.author))
        git(self.author, "checkout", "-q", "-b", "main")
        self.first = commit_roadmap(self.author, "SPEC-001 nine production files\n")
        git(self.author, "push", "-q", "origin", "main")
        git(base, "clone", "-q", str(self.bare), str(self.session))
        (self.session / ".specify").mkdir()
        previous = Path.cwd()
        os.chdir(self.session)
        self.addCleanup(os.chdir, previous)

    def advance_remote(self, text: str) -> str:
        sha = commit_roadmap(self.author, text)
        git(self.author, "push", "-q", "origin", "main")
        return sha

    def check(self, **inputs: object) -> dict[str, object]:
        request = SimpleNamespace(
            helper_id=HELPER_ID,
            operation=HELPER_ID,
            request_id="roadmap-freshness-test",
            mode="read_only",
            inputs={"roadmap_path": ROADMAP, **inputs},
        )
        # Model a protected Git installation at the OS permission boundary:
        # root CI owns system binaries, which the hardened probe rightly rejects.
        # Keep path validation, subprocesses, fetches and blob comparisons real.
        native_access = os.access
        with unittest.mock.patch("speckit_pro_runner.cli_probe.os.geteuid", return_value=-1), \
             unittest.mock.patch("speckit_pro_runner.cli_probe.os.access", side_effect=lambda path, mode, **options:
                                 False if mode == os.W_OK else native_access(path, mode, **options)):
            return dispatch_helper(request)

    def test_request_fixture_replays_the_registered_read_only_operation(self) -> None:
        fixture = REPO / "tests/speckit-pro/unit/fixtures/read-only-helpers/requests" / f"{HELPER_ID}.json"
        request = json.loads(fixture.read_text(encoding="utf-8"))
        registered = HELPERS[HELPER_ID]
        self.assertEqual((registered.helper_id, registered.operation, "read_only"), (request["helper_id"], request["operation"], request["mode"]))

    def test_checkout_behind_remote_roadmap_stops_with_both_revisions(self) -> None:
        remote = self.advance_remote("SPEC-001 six production files\n")
        result = self.check()
        self.assertEqual("expected_failure", result["status"], result)
        data = result["data"]
        self.assertFalse(data["writes_state"])
        self.assertEqual("stop", data["verdict"])
        self.assertEqual("stale", data["freshness_status"])
        self.assertEqual("checkout_behind_remote", data["cause"])
        self.assertEqual(self.first, data["checkout_revision"])
        self.assertEqual(remote, data["remote_revision"])
        self.assertEqual("origin", data["remote"])
        self.assertEqual("main", data["default_branch"])
        self.assertNotIn("base_revision", data)
        for text in (self.first, remote, "origin/main", ROADMAP):
            self.assertIn(text, data["stop_message"])

    def test_matching_roadmap_proceeds_and_names_the_base_revision(self) -> None:
        result = self.check()
        self.assertEqual("ok", result["status"], result)
        data = result["data"]
        self.assertEqual(("proceed", "current", None), (data["verdict"], data["freshness_status"], data["cause"]))
        self.assertEqual(self.first, data["base_revision"])
        self.assertEqual(data["checkout_roadmap_blob"], data["remote_roadmap_blob"])

    def test_checkout_behind_with_unchanged_roadmap_proceeds_from_the_remote_revision(self) -> None:
        (self.author / "other.txt").write_text("unrelated\n", encoding="utf-8")
        git(self.author, "add", "other.txt")
        git(self.author, "commit", "-q", "-m", "unrelated")
        git(self.author, "push", "-q", "origin", "main")
        remote = git(self.author, "rev-parse", "HEAD")
        data = self.check()["data"]
        self.assertEqual("proceed", data["verdict"])
        self.assertEqual(remote, data["base_revision"])
        self.assertNotEqual(data["checkout_revision"], data["base_revision"])

    def test_locally_edited_roadmap_stops_as_a_diverged_roadmap(self) -> None:
        (self.session / ROADMAP).write_text("SPEC-001 edited locally\n", encoding="utf-8")
        result = self.check()
        self.assertEqual("expected_failure", result["status"], result)
        data = result["data"]
        self.assertEqual(
            ("stop", "stale", "roadmap_differs_from_remote"),
            (data["verdict"], data["freshness_status"], data["cause"]),
        )
        self.assertEqual(self.first, data["remote_revision"])

    def test_roadmap_absent_on_the_remote_default_branch_stops(self) -> None:
        (self.session / "docs/ai/other-roadmap.md").write_text("not pushed\n", encoding="utf-8")
        data = self.check(roadmap_path="docs/ai/other-roadmap.md")["data"]
        self.assertEqual(
            ("stop", "stale", "roadmap_missing_on_remote_default"),
            (data["verdict"], data["freshness_status"], data["cause"]),
        )

    def test_unreachable_remote_is_unverified_and_stops(self) -> None:
        git(self.session, "remote", "set-url", "origin", str(self.bare.parent / "missing.git"))
        result = self.check()
        self.assertEqual("expected_failure", result["status"], result)
        data = result["data"]
        self.assertEqual(
            ("stop", "unverified", "remote_unreachable"),
            (data["verdict"], data["freshness_status"], data["cause"]),
        )

    def test_no_remote_is_unverified_and_stops(self) -> None:
        git(self.session, "remote", "remove", "origin")
        data = self.check()["data"]
        self.assertEqual(
            ("stop", "unverified", "no_remote"),
            (data["verdict"], data["freshness_status"], data["cause"]),
        )

    def test_bad_inputs_are_input_errors(self) -> None:
        for inputs in (
            {"roadmap_path": ""},
            {"roadmap_path": "../outside.md"},
            {"roadmap_path": 7},
            {"roadmap_path": "docs/ai/missing.md"},
            {"surprise": True},
        ):
            with self.subTest(inputs=inputs):
                self.assertEqual("input_error", self.check(**inputs)["status"])


if __name__ == "__main__":
    sys.exit(
        run_counted(
            unittest.defaultTestLoader.loadTestsFromTestCase(RoadmapFreshnessTests),
            label="test-roadmap-freshness",
        )
    )
