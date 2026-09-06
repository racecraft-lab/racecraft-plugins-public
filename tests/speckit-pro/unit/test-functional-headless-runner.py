#!/usr/bin/env python3
"""Deterministic security and evidence contracts for the Layer 3 H runner."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
RUNNER_PATH = TESTS_ROOT / "layer3-functional" / "run-headless-evals.py"
SHARED_LIB = TESTS_ROOT / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from test_result import run_counted  # noqa: E402


def import_runner():
    spec = importlib.util.spec_from_file_location("functional_headless_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FunctionalHeadlessRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = import_runner()
        cls.catalog = cls.runner.load_case_catalog(REPO_ROOT)

    def case(self, host: str, skill: str, eval_id: int):
        return self.runner.find_case(self.catalog, host, skill, eval_id)

    def test_catalog_is_the_bounded_h0_roster_without_rubrics(self) -> None:
        identities = {
            (item["host"], item["skill"], item["eval_id"])
            for item in self.catalog["cases"]
        }
        self.assertEqual(
            identities,
            {
                ("claude", "speckit-autopilot", 2),
                ("codex", "speckit-autopilot", 2),
                ("claude", "speckit-coach", 8),
                ("codex", "speckit-coach", 8),
            },
        )
        serialized = json.dumps(self.catalog).lower()
        self.assertNotIn("expectation", serialized)
        self.assertNotIn("expected_output", serialized)

    def test_actor_input_excludes_rubric_and_comparison_labels(self) -> None:
        actor = self.runner.build_actor_input(REPO_ROOT, self.case("codex", "speckit-coach", 8))
        self.assertEqual(set(actor), {"prompt", "fixture", "skill"})
        serialized = json.dumps(actor).lower()
        self.assertNotIn("expectation", serialized)
        self.assertNotIn("expected_output", serialized)
        self.assertNotIn("baseline", serialized)
        self.assertNotIn("final", serialized)

    def test_stage_copies_complete_rendered_distribution_and_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            stage = self.runner.stage_case(
                REPO_ROOT,
                self.case("codex", "speckit-autopilot", 2),
                Path(temporary),
            )
            self.assertTrue((stage.plugin_root / ".codex-plugin" / "plugin.json").is_file())
            self.assertTrue((stage.plugin_root / "speckit_pro_runner" / "__main__.py").is_file())
            self.assertTrue((stage.plugin_root / "skills" / "speckit-autopilot" / "references").is_dir())
            self.assertTrue((stage.workspace / ".agents" / "skills" / "speckit-autopilot" / "SKILL.md").is_file())
            self.assertTrue((stage.workspace / ".agents" / "skills" / "speckit-coach" / "SKILL.md").is_file())
            self.assertTrue((stage.workspace / "speckit-pro" / "speckit_pro_runner" / "__main__.py").is_file())
            self.assertEqual(stage.runtime_root, stage.workspace / "speckit-pro")
            self.assertTrue((stage.workspace / "tasks.md").is_file())
            self.assertFalse((stage.workspace / "PROVENANCE.json").exists())

    def test_coach_fixture_has_two_grounded_purposes_without_command_invention(self) -> None:
        fixture = (
            TESTS_ROOT
            / "layer3-functional"
            / "fixtures"
            / "headless"
            / "coach-installed-project"
        )
        provenance = json.loads((fixture / "PROVENANCE.json").read_text(encoding="utf-8"))
        manifests = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((fixture / ".specify" / "extensions").glob("*/manifest.json"))
        ]
        self.assertEqual({item["id"] for item in manifests}, {"review", "verify"})
        self.assertTrue(all(item["description"] and item["commands"] == [] for item in manifests))
        self.assertIn("not evidence of the current community catalog", " ".join(provenance["limitations"]))
        observation = json.loads((fixture / "installed-cli-observation.json").read_text(encoding="utf-8"))
        self.assertIsNone(observation["version_specific_command_help"])
        coach_case = self.case("claude", "speckit-coach", 8)
        note = coach_case["fixture_note"].lower()
        for leaked_cue in ("two requested", "unavailable", "unverified", "do not invent"):
            self.assertNotIn(leaked_cue, note)
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary)
            digest = self.runner.retain_fixture_provenance(REPO_ROOT, coach_case, evidence)
            self.assertEqual(digest, self.runner.sha256_file(evidence / "fixture-provenance.json"))
        with tempfile.TemporaryDirectory() as temporary:
            stage = self.runner.stage_case(REPO_ROOT, coach_case, Path(temporary))
            self.assertFalse((stage.workspace / "PROVENANCE.json").exists())
            self.assertTrue((stage.workspace / ".specify" / "extensions.yml").is_file())

    def test_codex_command_is_ephemeral_read_only_and_keeps_user_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            case = self.case("codex", "speckit-autopilot", 2)
            stage = self.runner.stage_case(REPO_ROOT, case, Path(temporary))
            command = self.runner.build_command(case, stage, Path("/bin/codex"), "model-id", "low")
        joined = " ".join(command)
        self.assertIn("--json", command)
        self.assertIn("--ephemeral", command)
        self.assertIn("read-only", command)
        self.assertIn("model-id", command)
        self.assertIn('shell_environment_policy.inherit="none"', command)
        self.assertTrue(any(item.startswith("shell_environment_policy.set=") for item in command))
        self.assertNotIn("--ignore-user-config", command)
        self.assertNotIn("--ignore-rules", command)
        self.assertNotIn("dangerously", joined)

    def test_claude_coach_command_is_restricted_to_read_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            case = self.case("claude", "speckit-coach", 8)
            stage = self.runner.stage_case(REPO_ROOT, case, Path(temporary))
            command = self.runner.build_command(case, stage, Path("/bin/claude"), "model-id", None)
        joined = " ".join(command)
        for value in ("--restricted", "--permission-mode", "dontAsk", "--permission-prompts", "none"):
            self.assertIn(value, command)
        self.assertIn("Skill,Read,Glob,Grep", command)
        self.assertEqual(command[command.index("--add-dir") + 1], str(stage.plugin_root))
        self.assertEqual(command[command.index("--plugin-dir") + 1], str(stage.plugin_root))
        self.assertNotIn("--bare", command)
        self.assertNotIn("dangerously", joined)

    def test_claude_autopilot_launch_is_held_without_safe_command_confinement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            case = self.case("claude", "speckit-autopilot", 2)
            stage = self.runner.stage_case(REPO_ROOT, case, Path(temporary))
            with self.assertRaises(self.runner.HeldLaunch):
                self.runner.build_command(case, stage, Path("/bin/claude"), "model-id", None)

    def test_process_capture_writes_exact_bytes_before_strict_decode_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary) / "evidence"
            result = self.runner.capture_process(
                [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'\\xff')"],
                b"prompt",
                evidence,
                Path(temporary),
                os.environ.copy(),
                5,
            )
            self.assertEqual((evidence / "stdout.bin").read_bytes(), b"\xff")
            self.assertEqual(result["status"], "output_decode_error")
            self.assertEqual(result["stdout_sha256"], self.runner.sha256_bytes(b"\xff"))

    def test_timeout_kills_process_group_and_preserves_timeout_over_decode_error(self) -> None:
        process = mock.Mock(pid=31415, returncode=-9)
        process.communicate.side_effect = [
            subprocess.TimeoutExpired(["actor"], 1, output=b"partial", stderr=b""),
            (b"\xff", b"timed out"),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary) / "evidence"
            with mock.patch.object(self.runner.subprocess, "Popen", return_value=process) as popen:
                with mock.patch.object(self.runner.os, "killpg") as killpg:
                    result = self.runner.capture_process(
                        ["actor"], b"prompt", evidence, Path(temporary), {}, 1
                    )
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        killpg.assert_called_once_with(31415, signal.SIGKILL)
        self.assertEqual(result["status"], "timeout")
        self.assertIn("decode_error", result)
        self.assertEqual(result["stdout_sha256"], self.runner.sha256_bytes(b"\xff"))

    def test_live_collection_holds_without_posix_process_group_termination(self) -> None:
        self.runner.require_execution_platform("posix")
        with self.assertRaises(self.runner.HeldLaunch):
            self.runner.require_execution_platform("nt")

    def test_codex_lifecycle_parser_requires_order_and_one_terminal(self) -> None:
        valid = "\n".join(
            json.dumps(item)
            for item in (
                {"type": "thread.started", "thread_id": "t"},
                {"type": "turn.started"},
                {"type": "item.completed", "item": {"type": "command_execution", "command": "pwd"}},
                {"type": "turn.completed", "usage": {}},
            )
        )
        parsed = self.runner.parse_events("codex", valid)
        self.assertEqual(parsed["terminal_type"], "turn.completed")
        self.assertEqual(len(parsed["tool_trace"]), 1)
        with self.assertRaises(self.runner.EvidenceError):
            self.runner.parse_events("codex", valid + "\n" + json.dumps({"type": "turn.completed"}))
        failed = "\n".join(
            json.dumps(item)
            for item in (
                {"type": "thread.started", "thread_id": "t"},
                {"type": "turn.started"},
                {"type": "item.completed", "item": {"type": "error", "message": "failed"}},
                {"type": "turn.completed", "usage": {}},
            )
        )
        with self.assertRaises(self.runner.EvidenceError):
            self.runner.parse_events("codex", failed)

    def test_claude_lifecycle_parser_records_only_provider_resolved_model(self) -> None:
        valid = "\n".join(
            json.dumps(item)
            for item in (
                {
                    "type": "system",
                    "subtype": "init",
                    "model": "resolved-model",
                    "plugins": [{"name": "speckit-pro"}],
                    "tools": ["Skill", "Read"],
                },
                {
                    "type": "assistant",
                    "message": {"content": [{
                        "type": "tool_use",
                        "id": "skill-1",
                        "name": "Skill",
                        "input": {"skill": "speckit-pro:speckit-coach", "args": ""},
                    }]},
                },
                {
                    "type": "user",
                    "message": {"content": [{
                        "type": "tool_result",
                        "tool_use_id": "skill-1",
                        "content": "loaded",
                    }]},
                },
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {}}]}},
                {"type": "result", "subtype": "success", "is_error": False},
            )
        )
        parsed = self.runner.parse_events("claude", valid)
        self.assertEqual(parsed["resolved_model"], "resolved-model")
        self.assertEqual(parsed["terminal_type"], "result")
        self.assertEqual(parsed["completed_tool_use_ids"], ["skill-1"])
        self.runner.require_provider_evidence(self.case("claude", "speckit-coach", 8), parsed)
        with self.assertRaises(self.runner.EvidenceError):
            self.runner.parse_events("claude", json.dumps({"type": "result", "is_error": False}))

    def test_required_provider_tool_and_plugin_evidence_fail_loud(self) -> None:
        claude_case = self.case("claude", "speckit-coach", 8)
        with self.assertRaises(self.runner.EvidenceError):
            self.runner.require_provider_evidence(
                claude_case,
                {"available_tools": ["Skill", "Read"], "plugins": [], "resolved_model": "model"},
            )
        with self.assertRaises(self.runner.EvidenceError):
            self.runner.require_provider_evidence(
                claude_case,
                {
                    "available_tools": ["Skill", "Read"],
                    "plugins": [{"name": "speckit-pro"}],
                    "resolved_model": "model",
                    "tool_trace": [{
                        "type": "tool_use",
                        "id": "skill-1",
                        "name": "Skill",
                        "input": {"skill": "speckit-pro:speckit-coach"},
                    }],
                    "completed_tool_use_ids": [],
                },
            )
        codex_case = self.case("codex", "speckit-autopilot", 2)
        with self.assertRaises(self.runner.EvidenceError):
            self.runner.require_provider_evidence(codex_case, {"tool_trace": []})

    def test_source_identity_rejects_wrong_commit_or_tree(self) -> None:
        commit, tree = self.runner.git_identity(REPO_ROOT)
        self.runner.require_source_identity(REPO_ROOT, commit, tree)
        with self.assertRaises(self.runner.EvidenceError):
            self.runner.require_source_identity(REPO_ROOT, "0" * 40, tree)
        with self.assertRaises(self.runner.EvidenceError):
            self.runner.require_source_identity(REPO_ROOT, commit, "0" * 40)

    def test_tree_snapshot_detects_any_workspace_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "one.txt").write_text("before", encoding="utf-8")
            before = self.runner.snapshot_tree(root)
            (root / "one.txt").write_text("after", encoding="utf-8")
            self.assertNotEqual(before, self.runner.snapshot_tree(root))

    def test_cleanup_failure_has_distinct_status(self) -> None:
        self.assertEqual(
            self.runner.final_status("completed_ungraded", "could not remove stage"),
            "cleanup_error",
        )
        self.assertEqual(self.runner.final_status("process_error", None), "process_error")

    def test_opaque_case_id_is_uuid_and_contains_no_case_semantics(self) -> None:
        opaque = self.runner.new_opaque_id()
        self.assertRegex(opaque, r"^[0-9a-f]{32}$")
        self.assertNotIn("coach", opaque)
        self.assertNotIn("autopilot", opaque)

    def test_process_environment_preserves_home_and_rejects_api_key_override(self) -> None:
        incoming = {"HOME": "/saved/home", "CODEX_HOME": "/saved/codex", "PATH": "/bin"}
        built = self.runner.build_process_env(incoming, Path("/plugin"))
        self.assertEqual(built["HOME"], incoming["HOME"])
        self.assertEqual(built["CODEX_HOME"], incoming["CODEX_HOME"])
        self.assertNotIn("auth.json", RUNNER_PATH.read_text(encoding="utf-8"))
        with self.assertRaises(self.runner.EvidenceError):
            self.runner.build_process_env({**incoming, "OPENAI_API_KEY": "present"}, Path("/plugin"))

    def test_cli_version_probe_fails_loud_on_missing_version(self) -> None:
        self.assertTrue(self.runner.probe_cli_version(Path(sys.executable)).startswith("Python "))
        with tempfile.TemporaryDirectory() as temporary:
            empty = Path(temporary) / "empty-version"
            empty.write_text(f"#!{sys.executable}\n", encoding="utf-8")
            empty.chmod(0o755)
            with self.assertRaises(self.runner.EvidenceError):
                self.runner.probe_cli_version(empty)

    def test_unit_owner_is_enrolled_in_layer_four_manifest(self) -> None:
        manifest = json.loads((TESTS_ROOT / "suite-manifest.json").read_text(encoding="utf-8"))
        layer = next(item for item in manifest["layers"] if item["id"] == "4")
        matches = [
            item for item in layer["scripts"]
            if item["path"] == "tests/speckit-pro/unit/test-functional-headless-runner.py"
        ]
        self.assertEqual(
            matches,
            [{
                "path": "tests/speckit-pro/unit/test-functional-headless-runner.py",
                "label": "test-functional-headless-runner",
            }],
        )


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FunctionalHeadlessRunnerTests)
    return run_counted(suite, label="test-functional-headless-runner")


if __name__ == "__main__":
    raise SystemExit(main())
