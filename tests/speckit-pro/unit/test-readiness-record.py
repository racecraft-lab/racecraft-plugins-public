#!/usr/bin/env python3
"""Scaffold's readiness record writer (ADR 0008): items, fingerprints, modes, privacy."""

from __future__ import annotations

import json
import copy
import os
import re
import shutil
import stat
import subprocess
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

from speckit_pro_runner.helpers import readiness_record  # noqa: E402
from host_skill_views import host_skill_root  # noqa: E402
from readiness_case import readiness_request  # noqa: E402
from runner_invocation import assert_runner_response, run_runner  # noqa: E402
from test_result import run_counted  # noqa: E402

CALLER_ITEMS = ("plugin_payload", "project_integration", "github_auth", "mcp_servers", "typesafe_jev",
                "reviewability_report", "formal_methods", "preview_surface")
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
    return readiness_request(observations, mode=mode, **{"host_version": "2.1.0", **inputs})


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

    @unittest.mock.patch.object(readiness_record.cli_probe, "probe", return_value={"exit_status": 0, "stdout_tail": "2.1.0"})
    def test_preview_surface_reads_back_as_a_closed_answer(self, _probe) -> None:
        for status, surface in (("verified", "available"), ("unavailable", "unavailable"),
                                ("unknown", "unknown"), ("not_applicable", "unknown")):
            with self.subTest(status=status):
                response = self.run_helper([observation("preview_surface", status, values={"probe": "observed"})])
                assert_runner_response(self, response, "ok", 0)
                self.assertEqual(surface, readiness_record.preview_surface(self.root, "claude"))
        self.assertEqual("unknown", readiness_record.preview_surface(self.root, "codex"))

    def test_preview_surface_is_unknown_unless_a_current_record_vouches_for_it(self) -> None:
        self.run_helper([observation("preview_surface", "unavailable")])
        path = self.record_path()
        good = json.loads(path.read_text(encoding="utf-8"))
        broken = {"unparseable": "{", "not an object": "[]", "other schema": {**good, "schema_version": "readiness-record/v0"},
                  "other host": {**good, "host": "codex"}, "other worktree": {**good, "binding": {"worktree": "sha256:0"}},
                  "no item": {**good, "items": {}}, "items list": {**good, "items": []}, "bad status": {**good, "items": {"preview_surface": {"status": "ready"}}}}
        for label, content in broken.items():
            with self.subTest(label):
                path.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
                self.assertEqual("unknown", readiness_record.preview_surface(self.root, "claude"))
        path.unlink()
        self.assertEqual("unknown", readiness_record.preview_surface(self.root, "claude"))

    @unittest.mock.patch.object(readiness_record.cli_probe, "probe", return_value={"exit_status": 0, "stdout_tail": "2.1.0"})
    def test_preview_surface_is_unknown_when_the_item_evidence_is_malformed_or_stale(self, _probe) -> None:
        (self.root / ".specify" / "surface.md").write_text("headless\n", encoding="utf-8")
        self.run_helper([observation("preview_surface", "unavailable", files=[".specify/surface.md"])])
        path = self.record_path()
        good = json.loads(path.read_text(encoding="utf-8"))
        item = good["items"]["preview_surface"]
        verified = {key: value for key, value in item.items() if key != "action"} | {"status": "verified"}
        shapes = {"status only": {"status": "unavailable"},
                  **{f"no {key}": {k: v for k, v in item.items() if k != key} for key in item if key != "status"},
                  "extra key": {**item, "note": "trust me"}, "empty evidence": {**item, "evidence_source": ""},
                  "evidence not text": {**item, "evidence_source": ["probe"]},
                  "evidence with a path": {**item, "evidence_source": HOME + "/someone/surface"},
                  "observed_at not a time": {**item, "observed_at": "yesterday"},
                  "fingerprints list": {**item, "fingerprints": []},
                  "fingerprint not text": {**item, "fingerprints": {"value:surface": 1}},
                  "fingerprint key": {**item, "fingerprints": {"surface": "sha256:" + "0" * 64}},
                  "fingerprint path escapes": {**item, "fingerprints": {"file:../surface.md": "missing"}},
                  "empty action": {**item, "action": " "},
                  "verified with an action": {**verified, "action": "Nothing."},
                  "verified without a digest": {**verified, "fingerprints": {}}}
        broken = {label: {**good, "items": {**good["items"], "preview_surface": shape}} for label, shape in shapes.items()}
        broken["binding fields only"] = {key: good[key] for key in ("schema_version", "binding", "host")} | {
            "items": {"preview_surface": item}}
        broken["record observed_at"] = {**good, "observed_at": None}
        for label, content in broken.items():
            with self.subTest(label):
                path.write_text(json.dumps(content), encoding="utf-8")
                self.assertEqual("unknown", readiness_record.preview_surface(self.root, "claude"))
        path.write_text(json.dumps(good), encoding="utf-8")
        self.assertEqual("unavailable", readiness_record.preview_surface(self.root, "claude"))
        (self.root / ".specify" / "surface.md").write_text("a preview pane now\n", encoding="utf-8")
        self.assertEqual("unknown", readiness_record.preview_surface(self.root, "claude"))

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

    def test_credential_shaped_value_names_are_refused_without_writing(self) -> None:
        credential_name = "ghp_" + "a1" * 18
        response = self.run_helper([observation("plugin_payload", values={credential_name: "passed"})])
        self.assertEqual("input_error", response["status"])
        assert_runner_response(self, response, "input_error", 2)
        self.assertFalse(self.record_path().exists())
        self.assertNotIn(credential_name, json.dumps(response))

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

    def test_slash_command_exemptions_require_exact_tokens(self) -> None:
        from speckit_pro_runner.helpers.readiness_values import clean_text
        from speckit_pro_runner.strict_input import SelectionError

        for command in ("/mcp", "/hooks", "/plugin", "/reload-plugins"):
            for template in ("Run {}", "Run `{}`, then retry.", "Run “{}”, then retry.", "Run {} to inspect."):
                action = template.format(command)
                self.assertEqual(action, clean_text(action, "action"))
            for suffix in (".json", ":x", ".d", "/private", "-extra", "_extra"):
                with self.subTest(command=command, suffix=suffix):
                    with self.assertRaises(SelectionError):
                        clean_text(f"Run {command}{suffix}", "action")

    def test_slash_command_punctuation_cannot_hide_a_path_suffix(self) -> None:
        from speckit_pro_runner.helpers.readiness_values import clean_text
        from speckit_pro_runner.strict_input import SelectionError

        for command in ("/mcp", "/hooks", "/plugin", "/reload-plugins",
                        "/speckit-pro:speckit-install", "/speckit-pro:speckit-scaffold-spec"):
            for punctuation in ('`', '"', '\u201d', '\u2019', ',', ';', ')', '`,', '\u201d,', '.', ':', ']', '}'):
                for suffix in ("private/data", ".json"):
                    with self.subTest(command=command, punctuation=punctuation, suffix=suffix):
                        with self.assertRaises(SelectionError):
                            clean_text(f"Run {command}{punctuation}{suffix}", "action")
            for ending in ("", ".", "`.", ").", " to inspect.", "\u00a0to inspect.", "`, then retry.", "\u201d, then retry."):
                with self.subTest(command=command, ending=ending):
                    action = f"Run {command}{ending}"
                    self.assertEqual(action, clean_text(action, "action"))

    def test_readiness_text_rejects_controls_and_bidirectional_formatting(self) -> None:
        from speckit_pro_runner.helpers.readiness_values import clean_text
        from speckit_pro_runner.strict_input import SelectionError

        characters = (*map(chr, range(32)), *map(chr, range(127, 160)),
                      "\u2028", "\u2029", "\u061c", "\u200e", "\u200f",
                      *map(chr, range(0x202A, 0x202F)), *map(chr, range(0x2066, 0x206A)))
        for character in characters:
            for template in ("{}probe", "probe{}result", "probe{}"):
                with self.subTest(character=ascii(character), template=template):
                    with self.assertRaises(SelectionError):
                        clean_text(template.format(character), "evidence_source")
        for text in ("MCP probe passed", "\u00e9tat v\u00e9rifi\u00e9", "\u0646\u062c\u062d \u0627\u0644\u0641\u062d\u0635"):
            with self.subTest(text=text):
                self.assertEqual(text, clean_text(text, "evidence_source"))

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


class PreviewEvidenceSecurityTest(unittest.TestCase):
    """The reader must fail closed on the entire snapshot, on both supported hosts."""

    def setUp(self) -> None:
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.root.joinpath(".specify").mkdir()
        self.root.joinpath("surface.txt").write_text("no preview tools")
        self.directory = self.root / ".specify/readiness"
        self.directory.mkdir()
        self.records = {}
        with unittest.mock.patch.object(readiness_record.shutil, "which", return_value=None):
            for host in ("claude", "codex"):
                inputs = request([observation("preview_surface", "unavailable", files=["surface.txt"])],
                                 host=host)["inputs"]
                self.records[host] = readiness_record.build_record(inputs, self.root)
        self.probe = readiness_record.cli_probe.probe
        self.enterContext(unittest.mock.patch.object(readiness_record.cli_probe, "probe", return_value={
            "exit_status": 0, "stdout_tail": "2.1.0", "stderr_tail": ""}))

    def assert_unknown(self, change) -> None:
        for host, good in self.records.items():
            with self.subTest(host=host):
                record = copy.deepcopy(good)
                change(record)
                (self.directory / f"{host}.json").write_text(json.dumps(record))
                self.assertEqual("unknown", readiness_record.preview_surface(self.root, host))

    def test_complete_current_records_for_both_hosts(self) -> None:
        for host, record in self.records.items():
            with self.subTest(host=host):
                (self.directory / f"{host}.json").write_text(json.dumps(record))
                self.assertEqual("unavailable", readiness_record.preview_surface(self.root, host))

    def test_preview_surface_only_inventory(self) -> None:
        self.assert_unknown(lambda record: record.update(items={"preview_surface": record["items"]["preview_surface"]}))

    def test_malformed_sibling_item(self) -> None:
        for name in self.records["claude"]["items"]:
            if name != "preview_surface":
                with self.subTest(item=name):
                    self.assert_unknown(lambda record: record["items"].update({name: {"status": "unknown"}}))

    def test_invalid_execution_mode(self) -> None:
        self.assert_unknown(lambda record: record.update(execution_mode="headless"))

    def test_non_text_host_version(self) -> None:
        self.assert_unknown(lambda record: record.update(host_version=["2.1.0"]))

    def test_non_text_plugin_revision(self) -> None:
        self.assert_unknown(lambda record: record.update(plugin_revision={"version": "2.40.0"}))

    def test_impossible_record_timestamp(self) -> None:
        for time in ("2026-02-30T00:00:00Z", "2026-10-05T25:00:00Z", "0000-01-01T00:00:00Z"):
            with self.subTest(time=time):
                self.assert_unknown(lambda record: record.update(observed_at=time))

    def test_impossible_item_timestamp(self) -> None:
        for name in self.records["claude"]["items"]:
            with self.subTest(item=name):
                self.assert_unknown(lambda record: record["items"][name].update(observed_at="2026-13-05T00:00:00Z"))

    def test_non_digest_value_fingerprint(self) -> None:
        for name in self.records["claude"]["items"]:
            for value in ("trust me", "sha256:xyz", "sha256:" + "g" * 64):
                with self.subTest(item=name, value=value):
                    self.assert_unknown(lambda record: record["items"][name].update(fingerprints={"value:probe": value}))

    def test_duplicate_json_keys(self) -> None:
        for host, record in self.records.items():
            text = json.dumps(record)
            for key, value in (("host", host), ("status", "unavailable"), ("file:surface.txt", record["items"]["preview_surface"]["fingerprints"]["file:surface.txt"])):
                with self.subTest(host=host, key=key):
                    field = json.dumps(key) + ": " + json.dumps(value)
                    (self.directory / f"{host}.json").write_text(text.replace(field, field + ", " + field, 1))
                    self.assertEqual("unknown", readiness_record.preview_surface(self.root, host))

    def test_stale_host_version(self) -> None:
        self.assert_unknown(lambda record: record.update(host_version="1.0.0"))

    def test_stale_plugin_revision(self) -> None:
        self.assert_unknown(lambda record: record.update(plugin_revision="1.0.0"))

    def test_empty_preview_fingerprints(self) -> None:
        self.assert_unknown(lambda record: record["items"]["preview_surface"].update(fingerprints={}))

    def test_missing_file_fingerprint_sentinel(self) -> None:
        self.assert_unknown(lambda record: record["items"]["preview_surface"].update(fingerprints={"file:absent": "missing"}))

    def test_unreadable_symlink_fingerprint_sentinel(self) -> None:
        (self.root / "linked").symlink_to(self.root / "surface.txt")
        self.assert_unknown(lambda record: record["items"]["preview_surface"].update(fingerprints={"file:linked": "unreadable"}))

    def test_deeply_nested_json(self) -> None:
        for host, good in self.records.items():
            with self.subTest(host=host):
                text = json.dumps(good)[:-1] + ', "extra": ' + "[" * 2000 + "0" + "]" * 2000 + "}"
                (self.directory / f"{host}.json").write_text(text)
                self.assertEqual("unknown", readiness_record.preview_surface(self.root, host))

    def test_oversized_flat_json(self) -> None:
        for host, good in self.records.items():
            with self.subTest(host=host):
                (self.directory / f"{host}.json").write_text(json.dumps(good) + " " * (1024 * 1024))
                self.assertEqual("unknown", readiness_record.preview_surface(self.root, host))

    def test_repeated_normalized_file_aliases(self) -> None:
        prints = {"file:" + "./" * n + "surface.txt": readiness_record.digest(b"no preview tools") for n in range(100)}
        self.assert_unknown(lambda record: record["items"]["preview_surface"].update(fingerprints=prints))

    def test_other_inventory_and_item_fields(self) -> None:
        for name in self.records["claude"]["items"]:
            for field, value in (("status", []), ("evidence_source", {}), ("fingerprints", []), ("action", "")):
                with self.subTest(item=name, field=field):
                    self.assert_unknown(lambda record: record["items"][name].update({field: value}))
        self.assert_unknown(lambda record: record["items"].update(extra=record["items"]["preview_surface"]))

    def test_stale_sibling_file_and_preview_rename(self) -> None:
        self.assert_unknown(lambda record: record["items"]["github_auth"].update(fingerprints={"file:surface.txt": "sha256:" + "0" * 64}))
        (self.root / "surface.txt").rename(self.root / "renamed.txt")
        self.assert_unknown(lambda record: None)

    def test_record_and_evidence_symlinks(self) -> None:
        for host, record in self.records.items():
            with self.subTest(host=host):
                (self.root / "record.json").write_text(json.dumps(record))
                (self.directory / f"{host}.json").symlink_to(self.root / "record.json")
                self.assertEqual("unknown", readiness_record.preview_surface(self.root, host))
                (self.directory / f"{host}.json").unlink()
        (self.root / "surface.txt").unlink()
        (self.root / "surface.txt").symlink_to(self.root / "record.json")
        self.assert_unknown(lambda record: None)

    def test_unobservable_or_failed_host_version(self) -> None:
        self.assert_unknown(lambda record: record.update(host_version=None))
        for result in ({"exit_status": None, "stdout_tail": ""}, {"exit_status": 1, "stdout_tail": "2.1.0"},
                       {"exit_status": 0, "stdout_tail": "unparseable"}):
            with self.subTest(result=result), unittest.mock.patch.object(readiness_record.cli_probe, "probe", return_value=result):
                self.assert_unknown(lambda record: None)

    def test_current_host_cli_version_formats(self) -> None:
        for host, text in (("claude", "2.1.0 (Claude Code)"), ("codex", "codex-cli 2.1.0")):
            with self.subTest(host=host), unittest.mock.patch.object(readiness_record.cli_probe, "probe", return_value={"exit_status": 0, "stdout_tail": text}):
                (self.directory / f"{host}.json").write_text(json.dumps(self.records[host]))
                self.assertEqual("unavailable", readiness_record.preview_surface(self.root, host))

    def test_file_fingerprint_budget(self) -> None:
        (self.root / "surface.txt").write_bytes(b"a" * (1024 * 1024 + 1))
        prints = {"file:surface.txt": readiness_record.digest((self.root / "surface.txt").read_bytes())}
        self.assert_unknown(lambda record: record["items"]["preview_surface"].update(fingerprints=prints))
        for n in range(65):
            (self.root / f"evidence{n}").write_bytes(b"small")
        prints = {f"file:evidence{n}": readiness_record.digest(b"small") for n in range(65)}
        self.assert_unknown(lambda record: record["items"]["preview_surface"].update(fingerprints=prints))

    def test_duplicate_file_evidence_is_read_once(self) -> None:
        record = copy.deepcopy(self.records["claude"])
        record["items"]["github_auth"]["fingerprints"] = record["items"]["preview_surface"]["fingerprints"]
        (self.directory / "claude.json").write_text(json.dumps(record))
        with unittest.mock.patch.object(readiness_record, "fingerprint_file", wraps=readiness_record.fingerprint_file) as read:
            self.assertEqual("unavailable", readiness_record.preview_surface(self.root, "claude"))
            self.assertEqual(1, sum(call.args[1].as_posix() == "surface.txt" for call in read.call_args_list))

    def test_host_probe_is_limited_to_version(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host), unittest.mock.patch.object(readiness_record.cli_probe.subprocess, "run") as run:
                run.return_value = unittest.mock.Mock(returncode=0, stdout="2.1.0", stderr="")
                self.assertEqual(0, self.probe(self.root, [host, "--version"], allowed=(host,), timeout=1)["exit_status"])
                self.assertEqual([host, "--version"], run.call_args.args[0])
                run.reset_mock()
                self.assertIsNone(self.probe(self.root, [host, "exec"], allowed=(host,), timeout=1)["exit_status"])
                run.assert_not_called()

    def test_record_reader_stops_at_byte_limit(self) -> None:
        (self.directory / "claude.json").write_bytes(b" " * (2 * 1024 * 1024))
        with unittest.mock.patch.object(readiness_record.os, "read", wraps=os.read) as read:
            self.assertEqual("unknown", readiness_record.preview_surface(self.root, "claude"))
            self.assertLessEqual(sum(call.args[1] for call in read.call_args_list), 1024 * 1024 + 1)

    def test_invalid_file_fingerprint_text(self) -> None:
        for name in self.records["claude"]["items"]:
            for path in ("bad\x00path", "bad\npath", "bad\ud800path", " padded "):
                with self.subTest(item=name, path=repr(path)):
                    self.assert_unknown(lambda record: record["items"][name].update(fingerprints={f"file:{path}": "missing"}))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO evidence requires POSIX")
    def test_fifo_record_and_fingerprint_do_not_block(self) -> None:
        code = "from pathlib import Path; from speckit_pro_runner.helpers.readiness_record import preview_surface; import sys; print(preview_surface(Path(sys.argv[1]), sys.argv[2]))"
        environment = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "speckit-pro")}
        for host, good in self.records.items():
            path = self.directory / f"{host}.json"
            for variant in ("record", "preview_surface", "github_auth"):
                with self.subTest(host=host, variant=variant):
                    if variant == "record":
                        os.mkfifo(path)
                    else:
                        record = copy.deepcopy(good)
                        record["items"][variant]["fingerprints"] = {"file:pipe": readiness_record.digest(b"no tools")}
                        path.write_text(json.dumps(record))
                        os.mkfifo(self.root / "pipe")
                    try:
                        result = subprocess.run([sys.executable, "-c", code, str(self.root), host], env=environment,
                                                capture_output=True, text=True, timeout=2, check=False)
                        self.assertEqual((0, "unknown"), (result.returncode, result.stdout.strip()), result.stderr)
                    finally:
                        path.unlink()
                        if variant != "record":
                            (self.root / "pipe").unlink()


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
    return unittest.TestSuite([loader.loadTestsFromTestCase(case) for case in (
        ReadinessRecordTest, PreviewEvidenceSecurityTest, FeasibilityTest)])


def main() -> int:
    return run_counted(build_suite(), label="test-readiness-record")


if __name__ == "__main__":
    raise SystemExit(main())
