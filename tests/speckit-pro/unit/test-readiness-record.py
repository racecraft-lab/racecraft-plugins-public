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
import unittest.mock
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))

from host_skill_views import host_skill_root  # noqa: E402
from runner_invocation import assert_runner_response, run_runner  # noqa: E402
from test_result import run_counted  # noqa: E402

CALLER_ITEMS = ("plugin_payload", "project_integration", "github_auth", "mcp_servers", "typesafe_jev",
                "reviewability_report", "formal_methods")
# Built from parts so the repository privacy scan does not flag these deliberate leak samples.
HOME = "/" + "Users"
SCRATCH = "/private" + "/tmp"
GATES = {"schema_version": "1.0", "thresholds": {"complexity": 10, "crap": 30, "mutation_score_floor": 60}}


def observation(item: str, status: str = "verified", **extra: object) -> dict[str, object]:
    record: dict[str, object] = {"item": item, "status": status, "evidence_source": f"{item} probe"}
    if status == "verified":
        record["values"] = {"probe": "passed"}
        if item == "reviewability_report":
            record.update(files=[".specify/roadmap.md"], values={"spec_id": "TEST-001"})
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
        self.root.joinpath(".specify", "roadmap.md").write_text("TEST-001\n", encoding="utf-8")
        # An empty tool directory keeps every helper run off the real Docker daemon.
        self.tools = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()

    def record_path(self, host: str = "claude") -> Path:
        return self.root / ".specify" / "readiness" / f"{host}.json"

    def run_helper(self, observations: list[dict[str, object]], mode: str = "apply", **inputs: object) -> dict:
        completed, response, _ = run_runner(request(observations, mode, **inputs), cwd=self.root,
                                            extra_env={"PATH": str(self.tools)})
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

    def test_verified_items_require_fingerprints_and_reviewability_references(self) -> None:
        cases = [observation("plugin_payload", values={}),
                 observation("reviewability_report", files=[]),
                 observation("reviewability_report", values={"probe": "passed"}),
                 observation("reviewability_report", files=[".specify/missing.md"])]
        self.root.joinpath(".specify", "linked-report.md").symlink_to(self.root / ".specify" / "roadmap.md")
        cases.append(observation("reviewability_report", files=[".specify/linked-report.md"]))
        for supplied in cases:
            with self.subTest(observation=supplied):
                response = self.run_helper([supplied])
                assert_runner_response(self, response, "input_error", 2)
                self.assertFalse(self.record_path().exists())

        response = self.run_helper([observation("plugin_payload", values={"revision": "2.40.0"}),
                                    observation("reviewability_report", files=[".specify/roadmap.md"],
                                                values={"spec_id": "TEST-001"})])
        assert_runner_response(self, response, "ok", 0)

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
            "home path": "read " + HOME + "/someone/project/file",
            "tmp path": "wrote " + SCRATCH + "/claude-1/probe",
            "windows path": "C:\\" + "Users\\someone\\probe",
            "tilde path": "see ~/.config/tool",
            "single segment path": "see " + "/" + "tmp",
            "root path": "see " + "/",
            "unc path": "see " + chr(92) * 2 + "server" + chr(92) + "share",
            "native root path": "see " + chr(92) + "Windows" + chr(92) + "Temp",
            "code path": "read `" + "/" + "tmp`",
            "link path": "read [" + "/" + "tmp]",
            "angle path": "read <" + "/" + "tmp>",
            "quoted path": "read \u201c" + "/" + "tmp\u201d",
        }
        for label, text in leaks.items():
            with self.subTest(label):
                response = self.run_helper([observation("github_auth", evidence_source=text)])
                assert_runner_response(self, response, "input_error", 2)
                self.assertFalse(self.record_path().exists())
        for field in ("host_version", "plugin_revision", "execution_mode"):
            with self.subTest(field=field):
                _, response, _ = run_runner(request(self.all_verified(), **{field: HOME + "/someone/bin"}), cwd=self.root)
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

        with unittest.mock.patch("tempfile.gettempdir", side_effect=FileNotFoundError("no usable temporary directory")):
            item = readiness_record.observe_local_capability()
        self.assertEqual("unavailable", item["status"])
        self.assertTrue(item["action"])
        self.assertNotIn(str(self.root), json.dumps(item))

    def test_local_capability_is_unknown_when_owner_only_modes_are_unobservable(self) -> None:
        from speckit_pro_runner.helpers import readiness_record

        with unittest.mock.patch.object(readiness_record, "os", wraps=os) as platform:
            platform.name = "nt"
            item = readiness_record.observe_local_capability()
        self.assertEqual("unknown", item["status"])
        self.assertTrue(item["action"])
        self.assertIn("unobservable", item["evidence_source"])

    def test_scaffold_documents_the_exact_request_and_the_step_on_each_host(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                skill = (host_skill_root(host) / "speckit-scaffold-spec" / "SKILL.md").read_text(encoding="utf-8")
                rows = re.findall(r"\| `write-readiness-record` \| `apply` \| `(\{[^`]*\})`", skill)
                self.assertEqual(1, len(rows))
                documented = json.loads(rows[0])
                self.assertEqual({"host", "execution_mode", "plugin_revision", "observations"}, set(documented))
                self.assertEqual({"item", "status", "evidence_source", "values"}, set(documented["observations"][0]))
                step = skill.split("### 6.5 Write the Readiness Record", 1)[1].split("\n### ", 1)[0]
                field, source = re.findall(r"Set `plugin_revision` to the `([^`]+)` in\n`([^`]+)`\.", step)[0]
                relative = source.removeprefix("${CLAUDE_PLUGIN_ROOT}/").removeprefix("../../")
                metadata = json.loads((REPO_ROOT / "dist" / host / "speckit-pro" / relative).read_text(encoding="utf-8"))
                replay = request([observation("github_auth")], "dry_run", host=host, plugin_revision=metadata[field])
                for key in documented:
                    self.assertIn(key, replay["inputs"])
                _, response, _ = run_runner(replay, cwd=self.root)
                assert_runner_response(self, response, "ok", 0)
                self.assertIn(f"Set `host` to `{host}`", step)
                self.assertEqual(metadata[field], response["data"]["record"]["plugin_revision"])
                for item in (*CALLER_ITEMS,):
                    self.assertIn(f"`{item}`", step)

    def test_each_host_records_agent_repair_gaps_and_continues_to_the_writer(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                skill = (host_skill_root(host) / "speckit-scaffold-spec" / "SKILL.md").read_text(encoding="utf-8")
                setup = skill.split("### -0.5 ", 1)[1].split("### 0.", 1)[0]
                self.assertNotRegex(setup, r"\bSTOP\b")
                self.assertIn("`plugin_payload`", setup)
                self.assertIn("`unavailable`", setup)
                self.assertIn("continue", setup)
                self.assertIn("Step 6.5", setup)

    def test_each_host_requires_loaded_revision_evidence(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                skill = (host_skill_root(host) / "speckit-scaffold-spec" / "SKILL.md").read_text(encoding="utf-8")
                step = skill.split("### 6.5 Write the Readiness Record", 1)[1].split("\n### ", 1)[0]
                self.assertIn("loaded revision", step)
                self.assertIn("disk inventory alone", step)
                self.assertIn("record `unknown`", step)

    def test_each_host_requires_live_mcp_observations_after_configuration_preflight(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                skill = (host_skill_root(host) / "speckit-scaffold-spec" / "SKILL.md").read_text(encoding="utf-8")
                step = skill.split("### 6.5 Write the Readiness Record", 1)[1].split("\n### ", 1)[0]
                self.assertIn("bounded live", step)
                self.assertIn("configuration alone", step)
                self.assertIn("empty `inputs={}`", step)
                self.assertIn("record `unknown`", step)

    def test_slash_command_actions_pass_and_stray_actions_are_dropped(self) -> None:
        observations = self.all_verified()
        observations[0] = observation("plugin_payload", "unavailable",
                                      action="Run /speckit-pro:speckit-install, then rerun scaffold.")
        observations[1] = observation("project_integration", action=HOME + "/someone/stray")
        response = self.run_helper(observations)
        assert_runner_response(self, response, "ok", 0)
        items = response["data"]["record"]["items"]
        self.assertIn("/speckit-pro:speckit-install", items["plugin_payload"]["action"])
        self.assertNotIn("action", items["project_integration"])
        for action in ("Run `/speckit-pro:speckit-install`, then retry.", "Run \u201c/reload-plugins\u201d, then retry."):
            with self.subTest(action=action):
                response = self.run_helper([observation("plugin_payload", "unavailable", action=action)])
                assert_runner_response(self, response, "ok", 0)
                self.assertEqual(action, response["data"]["record"]["items"]["plugin_payload"]["action"])
        bad_mode = request(self.all_verified(), execution_mode="answer-file")
        _, response, _ = run_runner(bad_mode, cwd=self.root)
        assert_runner_response(self, response, "input_error", 2)

    def test_unreadable_files_are_not_reported_missing(self) -> None:
        outside = self.root / "target.txt"
        outside.write_text("x\n", encoding="utf-8")
        (self.root / ".specify" / "link.md").symlink_to(outside)
        response = self.run_helper([observation("project_integration", files=[".specify/link.md"])])
        prints = response["data"]["record"]["items"]["project_integration"]["fingerprints"]
        self.assertEqual("unreadable", prints["file:.specify/link.md"])

    def test_local_capability_reports_cleanup_failures_and_shared_directories(self) -> None:
        from speckit_pro_runner.helpers import readiness_record

        with unittest.mock.patch("os.unlink", side_effect=PermissionError("denied")):
            item = readiness_record.observe_local_capability()
        self.assertEqual("unavailable", item["status"])
        shared = self.root / "shared"
        shared.mkdir()
        shared.chmod(0o777)
        with unittest.mock.patch("tempfile.gettempdir", return_value=str(shared)):
            item = readiness_record.observe_local_capability()
        self.assertEqual("unavailable", item["status"])
        self.assertIn("world-writable", item["evidence_source"])
        shared.chmod(0o1777)
        with unittest.mock.patch("tempfile.gettempdir", return_value=str(shared)):
            self.assertEqual("verified", readiness_record.observe_local_capability()["status"])

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
            "specify directory link": lambda: (specify.joinpath("roadmap.md").unlink(missing_ok=True),
                                                specify.rmdir(), specify.symlink_to(outside)),
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


class FeasibilityTest(unittest.TestCase):
    """Scaffold's feasibility results for formal methods and verification Docker (ADR 0005)."""

    def setUp(self) -> None:
        ReadinessRecordTest.setUp(self)  # a project root and an empty tool directory that a script can fill
        self.tool_env = {"DOCKER_HOST": "unix:///run/docker.sock"}  # a developer's own endpoint must not leak in

    def record_items(self, observations: list[dict[str, object]] | None = None, mode: str = "dry_run") -> dict:
        observations = [observation(item) for item in CALLER_ITEMS] if observations is None else observations
        _, response, _ = run_runner(request(observations, mode), cwd=self.root,
                                    extra_env={"PATH": str(self.tools), **self.tool_env})
        return response["data"]["record"]["items"]

    def fake_docker(self, output: str, exit_code: int = 0, endpoint: str = "unix:///run/docker.sock") -> None:
        """A `docker` that answers `info` with `output` and `context inspect` with `endpoint`."""
        script = self.tools / "docker"
        body = f"import sys\nprint({endpoint!r} if sys.argv[1] == 'context' else {output!r})\nsys.exit({exit_code})\n"
        script.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
        script.chmod(0o755)

    def test_feasibility_is_recorded_for_both_features(self) -> None:
        self.fake_docker("linux/arm64")
        observations = [observation(item) for item in CALLER_ITEMS if item != "formal_methods"]
        observations.append(observation("formal_methods", evidence_source="design has a stateful protocol"))
        items = self.record_items(observations)
        self.assertEqual("verified", items["formal_methods"]["status"])
        self.assertEqual("verified", items["verification_docker"]["status"])
        self.assertEqual("design has a stateful protocol", items["formal_methods"]["evidence_source"])
        self.assertNotIn("action", items["verification_docker"])

    def test_formal_methods_not_observed_is_unknown_with_an_action(self) -> None:
        items = self.record_items([observation("github_auth")])
        self.assertEqual("unknown", items["formal_methods"]["status"])
        self.assertTrue(items["formal_methods"]["action"])

    def test_docker_fit_needs_a_linux_arm64_daemon(self) -> None:
        for reported, status in (("linux/arm64", "verified"), ("linux/aarch64", "verified"),
                                 ("linux/x86_64", "unavailable"), ("windows/arm64", "unavailable")):
            with self.subTest(reported=reported):
                self.fake_docker(reported)
                item = self.record_items()["verification_docker"]
                self.assertEqual(status, item["status"])
                self.assertEqual("action" in item, status == "unavailable")

    def test_docker_reached_over_the_network_is_not_a_local_fit(self) -> None:
        self.fake_docker("linux/arm64", endpoint="ssh://builder")
        self.assertEqual("unavailable", self.record_items()["verification_docker"]["status"])
        self.fake_docker("linux/arm64")
        self.tool_env["DOCKER_HOST"] = "tcp://builder:2375"
        self.assertEqual("unavailable", self.record_items()["verification_docker"]["status"])
        self.tool_env["DOCKER_HOST"] = "unix:///run/docker.sock"
        self.assertEqual("verified", self.record_items()["verification_docker"]["status"])

    def test_remote_docker_host_is_rejected_before_any_probe_runs(self) -> None:
        self.fake_docker("linux/arm64")
        calls = self.root / "docker-calls.txt"
        script = self.tools / "docker"
        script.write_text(f"#!{sys.executable}\nfrom pathlib import Path\nPath({str(calls)!r}).write_text('called')\nprint('linux/arm64')\n", encoding="utf-8")
        for endpoint in ("tcp://remote.example:2375", "ssh://remote.example"):
            self.tool_env["DOCKER_HOST"] = endpoint
            with self.subTest(endpoint=endpoint):
                item = self.record_items()["verification_docker"]
                self.assertEqual("unavailable", item["status"])
                self.assertTrue(item["action"])
                self.assertFalse(calls.exists(), "a remote Docker host must not be probed")

    def test_docker_without_a_daemon_or_cli_is_unavailable_with_an_action(self) -> None:
        item = self.record_items()["verification_docker"]
        self.assertEqual("unavailable", item["status"])
        self.assertIn("not installed", item["evidence_source"])
        self.assertTrue(item["action"])
        self.fake_docker("Cannot connect to the Docker daemon", exit_code=1)
        item = self.record_items()["verification_docker"]
        self.assertEqual("unavailable", item["status"])
        self.assertIn("daemon", item["evidence_source"])
        self.assertNotIn(str(self.tools), json.dumps(item))

    def test_scaffold_offers_both_features_on_each_host_with_their_recorded_results(self) -> None:
        questions = {"claude": "AskUserQuestion", "codex": "request_user_input"}
        for host, question in questions.items():
            skill = (host_skill_root(host) / "speckit-scaffold-spec" / "SKILL.md").read_text(encoding="utf-8")
            offer = skill.split("### 6.6 Offer Formal Methods and Verification Docker", 1)[1].split("\n### ", 1)[0]
            with self.subTest(host=host):
                self.assertIn("data.record.items.formal_methods", offer)
                self.assertIn("data.record.items.verification_docker", offer)
                self.assertIn("whatever its feasibility result", offer)
                self.assertIn("booleans; ask nothing", offer)
                self.assertIn(question, offer)
                self.assertNotIn(questions["codex" if host == "claude" else "claude"], offer)


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    return unittest.TestSuite([loader.loadTestsFromTestCase(case) for case in (ReadinessRecordTest, FeasibilityTest)])


def main() -> int:
    return run_counted(build_suite(), label="test-readiness-record")


if __name__ == "__main__":
    raise SystemExit(main())
