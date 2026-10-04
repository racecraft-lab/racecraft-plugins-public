#!/usr/bin/env python3
"""Scaffold's readiness record writer (ADR 0008): items, fingerprints, modes, privacy."""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))

from host_skill_views import host_skill_root  # noqa: E402
from runner_invocation import assert_runner_response, run_runner  # noqa: E402
from test_result import run_counted  # noqa: E402

CALLER_ITEMS = ("plugin_payload", "project_integration", "github_auth", "mcp_servers", "typesafe_jev",
                "reviewability_report")
GATES = {"schema_version": "1.0", "thresholds": {"complexity": 10, "crap": 30, "mutation_score_floor": 60}}


def observation(item: str, status: str = "verified", **extra: object) -> dict[str, object]:
    record: dict[str, object] = {"item": item, "status": status, "evidence_source": f"{item} probe"}
    if status in {"unavailable", "unknown"}:
        record["action"] = f"Fix {item}, then rerun scaffold."
    record.update(extra)
    return record


def request(observations: list[dict[str, object]], mode: str = "apply", **inputs: object) -> dict[str, object]:
    body = {"host": "claude", "host_version": "2.1.0", "execution_mode": "interactive",
            "plugin_revision": "2.40.0", "observations": observations, **inputs}
    return {"schema_version": "1.0", "request_id": "test-readiness", "helper_id": "write-readiness-record",
            "operation": "write-readiness-record", "mode": mode, "inputs": body}


class ReadinessRecordTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.root.joinpath(".specify").mkdir()

    def record_path(self, host: str = "claude") -> Path:
        return self.root / ".specify" / "readiness" / f"{host}.json"

    def run_helper(self, observations: list[dict[str, object]], mode: str = "apply", **inputs: object) -> dict:
        completed, response, _ = run_runner(request(observations, mode, **inputs), cwd=self.root)
        self.assertIn(completed.returncode, (0, 1, 2, 3), completed.stderr)
        return response

    def all_verified(self) -> list[dict[str, object]]:
        return [observation(item) for item in CALLER_ITEMS]

    def test_writer_records_verified_unavailable_and_unknown_items_with_fingerprints(self) -> None:
        (self.root / ".specify" / "constitution.md").write_text("principles\n", encoding="utf-8")
        observations = [
            observation("plugin_payload", values={"revision": "2.40.0"}),
            observation("project_integration", files=[".specify/constitution.md", ".specify/missing.md"]),
            observation("github_auth", "unavailable"),
            observation("mcp_servers", "unknown"),
            observation("typesafe_jev", "not_applicable"),
            observation("reviewability_report"),
        ]
        response = self.run_helper(observations)
        assert_runner_response(self, response, "ok", 0)
        self.assertEqual(".specify/readiness/claude.json", response["data"]["record_path"])
        record = json.loads(self.record_path().read_text(encoding="utf-8"))
        self.assertEqual(response["data"]["record"], record)
        self.assertEqual("readiness-record/v1", record["schema_version"])
        for key in ("binding", "host", "host_version", "execution_mode", "plugin_revision", "observed_at"):
            self.assertIn(key, record)
        items = record["items"]
        self.assertEqual({"verified", "unavailable", "unknown", "not_applicable"}, {i["status"] for i in items.values()})
        self.assertEqual("Fix github_auth, then rerun scaffold.", items["github_auth"]["action"])
        self.assertNotIn("action", items["plugin_payload"])
        for item in items.values():
            self.assertTrue(item["evidence_source"])
            self.assertTrue(item["observed_at"])
        prints = items["project_integration"]["fingerprints"]
        self.assertRegex(prints["file:.specify/constitution.md"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual("missing", prints["file:.specify/missing.md"])
        self.assertRegex(items["plugin_payload"]["fingerprints"]["value:revision"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual({}, items["github_auth"]["fingerprints"])

    def test_declined_fix_still_finishes_and_no_overall_verdict_exists(self) -> None:
        observations = self.all_verified()
        observations[2] = observation("github_auth", "unavailable", evidence_source="user declined the sign-in fix",
                                      action="Run the host sign-in command, then rerun scaffold.")
        response = self.run_helper(observations)
        assert_runner_response(self, response, "ok", 0)
        record = json.loads(self.record_path().read_text(encoding="utf-8"))
        self.assertEqual("unavailable", record["items"]["github_auth"]["status"])
        for forbidden in ("ready", "verdict", "overall", "status"):
            self.assertNotIn(forbidden, record)

    def test_missing_caller_items_are_recorded_unknown_with_an_action(self) -> None:
        response = self.run_helper([observation("github_auth")])
        assert_runner_response(self, response, "ok", 0)
        items = json.loads(self.record_path().read_text(encoding="utf-8"))["items"]
        for item in set(CALLER_ITEMS) - {"github_auth"}:
            self.assertEqual("unknown", items[item]["status"])
            self.assertTrue(items[item]["action"])

    def test_malformed_observations_write_nothing(self) -> None:
        cases = {
            "no action": [{"item": "github_auth", "status": "unavailable", "evidence_source": "probe"}],
            "bad status": [observation("github_auth", "ready")],
            "unknown item": [observation("overall_ready")],
            "helper-owned item": [observation("local_capability")],
            "duplicate": [observation("github_auth"), observation("github_auth")],
            "absolute fingerprint path": [observation("project_integration", files=["/etc/hosts"])],
            "escaping fingerprint path": [observation("project_integration", files=["../outside"])],
        }
        for label, observations in cases.items():
            with self.subTest(label):
                response = self.run_helper(observations)
                assert_runner_response(self, response, "input_error", 2)
                self.assertFalse(self.record_path().exists())
        bad_host = request(self.all_verified())
        bad_host["inputs"]["host"] = "gemini"
        _, response, _ = run_runner(bad_host, cwd=self.root)
        assert_runner_response(self, response, "input_error", 2)

    def test_dry_run_returns_the_record_without_writing(self) -> None:
        response = self.run_helper(self.all_verified(), mode="dry_run")
        assert_runner_response(self, response, "ok", 0)
        self.assertEqual("claude", response["data"]["record"]["host"])
        self.assertFalse(response["data"]["writes_state"])
        self.assertFalse(self.record_path().parent.exists())

    def test_record_and_directory_modes_under_umask_077_and_a_loose_umask(self) -> None:
        for umask in (0o077, 0o000):
            with self.subTest(umask=oct(umask)):
                old = os.umask(umask)
                try:
                    response = self.run_helper(self.all_verified())
                finally:
                    os.umask(old)
                assert_runner_response(self, response, "ok", 0)
                directory = self.record_path().parent
                self.assertEqual(0o600, stat.S_IMODE(self.record_path().stat().st_mode))
                self.assertEqual(0o700, stat.S_IMODE(directory.stat().st_mode))
                self.assertEqual([], [p.name for p in directory.iterdir() if p.name.endswith(".tmp")])
                self.assertEqual("verified", response["data"]["record"]["items"]["local_capability"]["status"])

    def test_record_is_git_ignored_in_every_worktree(self) -> None:
        self.run_helper(self.all_verified())
        self.assertEqual("*\n", (self.record_path().parent / ".gitignore").read_text(encoding="utf-8"))

    def test_record_holds_no_credential_or_absolute_local_path(self) -> None:
        leaks = {
            "github token": "gh auth ok ghp_" + "a1" * 19,
            "bearer": "Authorization: Bearer abcdefghijklmnopqrstuvwxyz0123456789",
            "home path": "read /Users/someone/project/file",
            "tmp path": "wrote /private/tmp/claude-1/probe",
            "windows path": "C:\\Users\\someone\\probe",
            "tilde path": "see ~/.config/tool",
        }
        for label, text in leaks.items():
            with self.subTest(label):
                response = self.run_helper([observation("github_auth", evidence_source=text)])
                assert_runner_response(self, response, "input_error", 2)
                self.assertFalse(self.record_path().exists())
        for field in ("host_version", "plugin_revision", "execution_mode"):
            with self.subTest(field=field):
                _, response, _ = run_runner(request(self.all_verified(), **{field: "/Users/someone/bin"}), cwd=self.root)
                assert_runner_response(self, response, "input_error", 2)
        self.run_helper(self.all_verified())
        text = self.record_path().read_text(encoding="utf-8")
        self.assertNotIn(str(self.root), text)
        self.assertNotIn(tempfile.gettempdir(), text)

    def test_quality_gates_source_is_a_file_digest_or_defaults_with_the_reason(self) -> None:
        def quality() -> dict:
            response = self.run_helper(self.all_verified())
            return response["data"]["record"]["items"]["quality_gates"]

        missing = quality()
        self.assertEqual("unavailable", missing["status"])
        self.assertIn("shipped defaults", missing["evidence_source"])
        self.assertIn("missing", missing["evidence_source"])
        self.assertTrue(missing["action"])
        gates = self.root / ".specify" / "quality-gates.json"
        gates.write_text('{"schema_version": "2"}', encoding="utf-8")
        invalid = quality()
        self.assertEqual("unavailable", invalid["status"])
        self.assertIn("schema_version", invalid["evidence_source"])
        gates.write_text(json.dumps(GATES), encoding="utf-8")
        valid = quality()
        self.assertEqual("verified", valid["status"])
        self.assertRegex(valid["fingerprints"]["file:.specify/quality-gates.json"], r"^sha256:[0-9a-f]{64}$")
        self.assertNotIn("action", valid)

    def test_local_capability_is_unavailable_when_temporary_storage_fails(self) -> None:
        from speckit_pro_runner.helpers import readiness_record

        with mock.patch("tempfile.gettempdir", side_effect=FileNotFoundError("no usable temporary directory")):
            item = readiness_record.observe_local_capability()
        self.assertEqual("unavailable", item["status"])
        self.assertTrue(item["action"])
        self.assertNotIn(str(self.root), json.dumps(item))

    def test_scaffold_documents_the_exact_request_and_the_step_on_each_host(self) -> None:
        manifests = {"claude": ".claude-plugin/plugin.json", "codex": ".codex-plugin/plugin.json"}
        for host, manifest in manifests.items():
            with self.subTest(host=host):
                skill = (host_skill_root(host) / "speckit-scaffold-spec" / "SKILL.md").read_text(encoding="utf-8")
                rows = re.findall(r"\| `write-readiness-record` \| `apply` \| `(\{[^`]*\})`", skill)
                self.assertEqual(1, len(rows))
                documented = json.loads(rows[0])
                self.assertEqual({"host", "execution_mode", "plugin_revision", "observations"}, set(documented))
                self.assertEqual({"item", "status", "evidence_source"}, set(documented["observations"][0]))
                replay = request([observation("github_auth")], "dry_run", host=host)
                for key in documented:
                    self.assertIn(key, replay["inputs"])
                _, response, _ = run_runner(replay, cwd=self.root)
                assert_runner_response(self, response, "ok", 0)
                step = skill.split("### 6.5 Write the Readiness Record", 1)[1].split("\n### ", 1)[0]
                self.assertIn(f"Set `host` to `{host}`", step)
                self.assertIn(manifest, step)
                self.assertTrue((REPO_ROOT / "speckit-pro" / manifest).is_file())
                for item in (*CALLER_ITEMS,):
                    self.assertIn(f"`{item}`", step)

    def test_write_refuses_a_planted_symlink_and_leaves_the_outside_untouched(self) -> None:
        outside = Path(tempfile.mkdtemp(dir=self.root.parent, prefix="outside-")).resolve()
        self.addCleanup(lambda: shutil.rmtree(outside, ignore_errors=True))
        secret = outside / "victim.txt"
        secret.write_text("keep\n", encoding="utf-8")
        specify = self.root / ".specify"
        readiness = specify / "readiness"
        plants = {
            "gitignore file link": lambda: (readiness.mkdir(), (readiness / ".gitignore").symlink_to(secret)),
            "record file link": lambda: (readiness.mkdir(), (readiness / "claude.json").symlink_to(secret)),
            "readiness directory link": lambda: readiness.symlink_to(outside),
            "specify directory link": lambda: (specify.rmdir(), specify.symlink_to(outside)),
        }
        for label, plant in plants.items():
            with self.subTest(label):
                plant()
                response = self.run_helper(self.all_verified())
                if specify.is_symlink():
                    # Project discovery refuses a .specify link that leaves the project.
                    assert_runner_response(self, response, "missing_prerequisite", 3)
                else:
                    assert_runner_response(self, response, "expected_failure", 1)
                    self.assertEqual("write_failure", response["diagnostics"][0]["code"])
                    self.assertIn("unsafe", response["diagnostics"][0]["message"])
                self.assertEqual("keep\n", secret.read_text(encoding="utf-8"))
                self.assertEqual(["victim.txt"], sorted(p.name for p in outside.iterdir()))
                if specify.is_symlink():
                    specify.unlink()
                    specify.mkdir()
                elif readiness.is_symlink():
                    readiness.unlink()
                else:
                    shutil.rmtree(readiness, ignore_errors=True)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ReadinessRecordTest)


def main() -> int:
    return run_counted(build_suite(), label="test-readiness-record")


if __name__ == "__main__":
    raise SystemExit(main())
