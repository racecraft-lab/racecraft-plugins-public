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
        self.assertEqual(actor["fixture"]["root"], ".")
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
            self.assertEqual(
                stage.target_skill,
                stage.workspace / ".agents" / "skills" / "speckit-autopilot" / "SKILL.md",
            )
            self.assertEqual(
                self.runner.sha256_file(stage.target_skill),
                self.runner.sha256_file(stage.plugin_root / "skills" / "speckit-autopilot" / "SKILL.md"),
            )
            self.assertEqual(json.loads(stage.mcp_config.read_text(encoding="utf-8")), {"mcpServers": {}})
            self.assertTrue((stage.workspace / self.case("codex", "speckit-autopilot", 2)["fixture_root"] / "tasks.md").is_file())
            self.assertFalse((stage.workspace / "PROVENANCE.json").exists())

    def test_autopilot_fixture_resolves_at_the_unchanged_prompt_path(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as temporary:
                case = self.case(host, "speckit-autopilot", 2)
                actor = self.runner.build_actor_input(REPO_ROOT, case)
                self.assertIn(case["fixture_root"], actor["prompt"])
                self.assertEqual(actor["fixture"]["root"], case["fixture_destination"])
                stage = self.runner.stage_case(REPO_ROOT, case, Path(temporary))
                staged_tasks = stage.workspace / case["fixture_root"] / "tasks.md"
                self.assertTrue(staged_tasks.is_file())
                self.assertEqual(
                    staged_tasks.read_bytes(),
                    (self.runner.fixture_path(REPO_ROOT, case) / "tasks.md").read_bytes(),
                )
                self.assertFalse((stage.workspace / "tasks.md").exists())

    def test_codex_staged_g7_helper_reads_the_prompt_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            case = self.case("codex", "speckit-autopilot", 2)
            stage = self.runner.stage_case(REPO_ROOT, case, Path(temporary))
            request = {
                "schema_version": "1.0",
                "request_id": "staged-g7",
                "helper_id": "validate-gate",
                "operation": "validate-gate",
                "mode": "read_only",
                "inputs": {"gate": "G7", "feature_dir": case["fixture_root"]},
            }
            result = subprocess.run(
                [sys.executable, "-m", "speckit_pro_runner"],
                input=json.dumps(request),
                text=True,
                capture_output=True,
                cwd=stage.workspace,
                env={**os.environ, "PYTHONPATH": str(stage.runtime_root)},
                check=False,
            )
            envelope = json.loads(result.stdout)
            data = envelope["data"]["stdout_json"]
            self.assertEqual(data["gate"], "G7")
            self.assertIs(data["pass"], False)
            self.assertEqual(data["total"], 85)
            self.assertEqual(data["done"], 84)
            self.assertEqual(data["markers"], 1)
            self.assertEqual(data["reason"], "1 of 85 tasks incomplete")

    def test_fixture_destination_rejects_workspace_escape(self) -> None:
        for destination in ("../outside", "/outside"):
            with self.subTest(destination=destination), tempfile.TemporaryDirectory() as temporary:
                case = {**self.case("codex", "speckit-autopilot", 2), "fixture_destination": destination}
                with self.assertRaises(self.runner.EvidenceError):
                    self.runner.stage_case(REPO_ROOT, case, Path(temporary))
                self.assertEqual(list(Path(temporary).iterdir()), [])

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
        self.assertEqual(observation["specify_version"], "1.0.1")
        help_path = fixture / observation["version_specific_command_help"]
        help_capture = json.loads(help_path.read_text(encoding="utf-8"))
        self.assertEqual(help_capture["specify_version"], observation["specify_version"])
        self.assertEqual(help_capture["executable_sha256"], provenance["cli_help_capture"]["executable_sha256"])
        self.assertEqual(self.runner.sha256_file(help_path), provenance["cli_help_capture"]["file_sha256"])
        self.assertEqual(
            [item["arguments"] for item in help_capture["commands"]],
            [["--version"], ["--help"], ["extension", "--help"], ["extension", "add", "--help"]],
        )
        for item in help_capture["commands"]:
            self.assertEqual(item["exit_code"], 0)
            self.assertEqual(self.runner.sha256_bytes(item["stdout"].encode()), item["stdout_sha256"])
            self.assertEqual(self.runner.sha256_bytes(item["stderr"].encode()), item["stderr_sha256"])
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
            self.assertEqual(
                (stage.workspace / observation["version_specific_command_help"]).read_bytes(),
                help_path.read_bytes(),
            )

    def test_codex_command_is_ephemeral_read_only_and_isolates_the_staged_target(self) -> None:
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
        self.assertIn("--ignore-user-config", command)
        self.assertNotIn("--ignore-rules", command)
        self.assertEqual(command.count("--disable"), 3)
        self.assertEqual(
            [command[index + 1] for index, item in enumerate(command) if item == "--disable"],
            ["plugins", "hooks", "apps"],
        )
        self.assertIn("skills.bundled.enabled=false", command)
        self.assertIn("mcp_servers={}", command)
        skill_config = next(item for item in command if item.startswith("skills.config=["))
        self.assertNotIn(str(stage.target_skill), skill_config)
        self.assertIn(str(stage.workspace / ".agents" / "skills" / "speckit-coach" / "SKILL.md"), skill_config)
        self.assertNotIn("dangerously", joined)

    def test_codex_deny_list_keeps_only_the_runtime_target_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            host_root = root / "host-skills"
            host_skill = host_root / "host-only" / "SKILL.md"
            host_skill.parent.mkdir(parents=True)
            host_skill.write_text("---\nname: host-only\n---\n", encoding="utf-8")
            stage = self.runner.stage_case(
                REPO_ROOT,
                self.case("codex", "speckit-autopilot", 2),
                root / "stage",
            )
            with mock.patch.object(
                self.runner.codex_trigger_evals,
                "skill_source_roots",
                return_value=(host_root,),
            ):
                disabled = self.runner.enumerate_non_target_skills(stage)
                command = self.runner.build_command(
                    self.case("codex", "speckit-autopilot", 2),
                    stage,
                    Path("/bin/codex"),
                    "model-id",
                    "low",
                    disabled,
                )
        self.assertNotIn(stage.target_skill.resolve(), disabled)
        self.assertIn(host_skill.resolve(), disabled)
        self.assertIn(
            (stage.workspace / ".agents" / "skills" / "speckit-coach" / "SKILL.md").resolve(),
            disabled,
        )
        skill_config = next(item for item in command if item.startswith("skills.config=["))
        self.assertIn(str(host_skill.resolve()), skill_config)
        self.assertIn(
            str((stage.workspace / ".agents" / "skills" / "speckit-coach" / "SKILL.md").resolve()),
            skill_config,
        )

    def test_claude_coach_command_is_restricted_to_read_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            case = self.case("claude", "speckit-coach", 8)
            stage = self.runner.stage_case(REPO_ROOT, case, Path(temporary))
            command = self.runner.build_command(case, stage, Path("/bin/claude"), "model-id", None)
        joined = " ".join(command)
        for value in ("--restricted", "--permission-mode", "dontAsk", "--permission-prompts", "none"):
            self.assertIn(value, command)
        self.assertIn("Skill,Read,Glob,Grep", command)
        self.assertIn("--strict-mcp-config", command)
        self.assertEqual(command[command.index("--mcp-config") + 1], str(stage.mcp_config))
        settings = json.loads(command[command.index("--settings") + 1])
        self.assertIs(settings["disableClaudeAiConnectors"], True)
        self.assertIs(settings["disableBundledSkills"], True)
        self.assertEqual(settings["skillOverrides"], {"doctor": "off"})
        self.assertIn("--no-chrome", command)
        self.assertEqual(command[command.index("--add-dir") + 1], str(stage.plugin_root))
        self.assertEqual(command[command.index("--plugin-dir") + 1], str(stage.plugin_root))
        self.assertNotIn("--bare", command)
        self.assertNotIn("dangerously", joined)

    def test_claude_policy_preserves_full_staging_and_denies_every_sibling(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            case = self.case("claude", "speckit-coach", 8)
            stage = self.runner.stage_case(REPO_ROOT, case, Path(temporary))
            before = self.runner.snapshot_tree(stage.plugin_root)
            policy = self.runner.claude_skill_policy(case, stage)
            command = self.runner.build_command(case, stage, Path("/bin/claude"), "model-id", None)
            self.assertEqual(before, self.runner.snapshot_tree(stage.plugin_root))
            self.assertEqual(before, self.runner.snapshot_tree(REPO_ROOT / "dist" / "claude" / "speckit-pro"))
            for relative in (
                "skills/speckit-autopilot/SKILL.md",
                "skills/speckit-autopilot/references/capability-discovery.md",
                "skills/speckit-autopilot/references/grounding.md",
                "scripts/curated-set.json",
            ):
                self.assertIn(relative, before)
            expected = sorted(f"speckit-pro:{path.name}" for path in (stage.plugin_root / "skills").iterdir())
        self.assertEqual(policy["expected_skills"], expected)
        self.assertEqual(policy["target_skill"], "speckit-pro:speckit-coach")
        settings = policy["settings"]
        self.assertEqual(json.loads(command[command.index("--settings") + 1]), settings)
        self.assertEqual(settings["permissions"]["allow"], ["Skill(speckit-pro:speckit-coach)", "Skill(speckit-pro:speckit-coach *)"])
        denied = [*sorted(set(expected) - {policy["target_skill"]}), "init", "security-review"]
        self.assertEqual(settings["permissions"]["deny"], [rule for name in denied for rule in (f"Skill({name})", f"Skill({name} *)")])

    def test_claude_policy_rejects_ambiguous_staged_names_and_target(self) -> None:
        for mutation in ("namespace", "name", "duplicate-name", "missing-entry", "target", "custom-path"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                case = self.case("claude", "speckit-coach", 8)
                stage = self.runner.stage_case(REPO_ROOT, case, Path(temporary))
                manifest_path = stage.plugin_root / ".claude-plugin" / "plugin.json"
                if mutation in {"namespace", "custom-path"}:
                    manifest = json.loads(manifest_path.read_text())
                    manifest["name" if mutation == "namespace" else "skills"] = "unexpected"
                    manifest_path.write_text(json.dumps(manifest))
                elif mutation == "name":
                    stage.target_skill.write_text("---\nname: other-name\n---\n")
                elif mutation == "duplicate-name":
                    stage.target_skill.write_text("---\nname: speckit-coach\nname: speckit-coach\n---\n")
                elif mutation == "missing-entry":
                    (stage.plugin_root / "skills" / "missing-entry").mkdir()
                else:
                    case = {**case, "invocation": "/speckit-pro:absent"}
                with self.assertRaises(self.runner.EvidenceError):
                    self.runner.claude_skill_policy(case, stage)

    def claude_evidence(self):
        case = self.case("claude", "speckit-coach", 8)
        with tempfile.TemporaryDirectory() as temporary:
            stage = self.runner.stage_case(REPO_ROOT, case, Path(temporary))
            policy = self.runner.claude_skill_policy(case, stage)
        parsed = {
            "available_tools": case["allowed_tools"],
            "plugins": [{"name": "speckit-pro"}],
            "resolved_model": "model-id",
            "available_skills": policy["expected_skills"],
            "tool_trace": [{"type": "tool_use", "id": "target", "name": "Skill", "input": {"skill": policy["target_skill"], "args": "help"}}],
            "completed_tool_use_ids": ["target"],
        }
        return case, policy, parsed

    def test_claude_exact_bound_skill_inventory_is_required(self) -> None:
        case, policy, parsed = self.claude_evidence()
        self.runner.require_provider_evidence(case, parsed, policy)
        with self.assertRaisesRegex(self.runner.EvidenceError, "bound.*policy"):
            self.runner.require_provider_evidence(case, parsed)
        for inventory in (None, [], [*policy["expected_skills"], "code-review"], policy["expected_skills"][1:], [*policy["expected_skills"], policy["target_skill"]], [*policy["expected_skills"], {}]):
            with self.subTest(inventory=inventory), self.assertRaisesRegex(self.runner.EvidenceError, "skill catalog"):
                self.runner.require_provider_evidence(case, {**parsed, "available_skills": inventory}, policy)

    def test_claude_rejects_every_non_target_skill_attempt_even_if_denied(self) -> None:
        case, policy, parsed = self.claude_evidence()
        for name in ("code-review", "speckit-pro:speckit-autopilot", "init", "security-review", "speckit-coach", None):
            for completed in (False, True):
                with self.subTest(name=name, completed=completed):
                    extra = {"type": "tool_use", "id": "extra", "name": "Skill", "input": {"skill": name}}
                    contaminated = {**parsed, "tool_trace": [*parsed["tool_trace"], extra], "completed_tool_use_ids": ["target", "extra"] if completed else ["target"]}
                    with self.assertRaisesRegex(self.runner.EvidenceError, "non-target Skill attempt"):
                        self.runner.require_provider_evidence(case, contaminated, policy)

    def test_claude_manifest_retains_policy_and_rejected_provider_inventory(self) -> None:
        case, policy, parsed = self.claude_evidence()
        for contaminated in (False, True):
            with self.subTest(contaminated=contaminated), tempfile.TemporaryDirectory() as temporary:
                evidence = Path(temporary) / "evidence"
                observed = {**parsed, "available_skills": [*parsed["available_skills"], "code-review"]} if contaminated else parsed
                with (
                    mock.patch.object(self.runner, "require_source_identity"),
                    mock.patch.object(self.runner, "probe_cli_version", return_value="test-cli"),
                    mock.patch.object(self.runner, "build_process_env", return_value={}),
                    mock.patch.object(self.runner, "capture_process", return_value={"status": "completed_ungraded", "stdout": "synthetic", "stderr": ""}) as capture,
                    mock.patch.object(self.runner, "parse_events", return_value=observed),
                ):
                    result = self.runner.main([
                        "--host", "claude", "--skill", case["skill"], "--eval-id", str(case["eval_id"]),
                        "--source-commit", "test-commit", "--source-tree", "test-tree", "--model", "model-id",
                        "--cli", sys.executable, "--evidence-dir", str(evidence), "--execute",
                    ])
                manifest = json.loads((evidence / "manifest.json").read_text())
                self.assertEqual(result, 1 if contaminated else 0)
                self.assertEqual(manifest["status"], "provider_evidence_error" if contaminated else "completed_ungraded")
                self.assertEqual(manifest["claude_skill_policy"], policy)
                self.assertEqual(manifest["provider_evidence"]["available_skills"], observed["available_skills"])
                command = capture.call_args.args[1]
                self.assertEqual(json.loads(command[command.index("--settings") + 1]), policy["settings"])
                self.assertEqual(manifest["semantic_grade"], "not_performed")

    def test_claude_stage_change_stops_before_provider_launch(self) -> None:
        original_build = self.runner.build_command

        def change_after_assembly(case, stage, *args):
            command = original_build(case, stage, *args)
            stage.target_skill.write_text(stage.target_skill.read_text() + "\nchanged\n")
            return command

        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary) / "evidence"
            with (
                mock.patch.object(self.runner, "require_source_identity"),
                mock.patch.object(self.runner, "probe_cli_version", return_value="test-cli"),
                mock.patch.object(self.runner, "build_command", side_effect=change_after_assembly),
                mock.patch.object(self.runner, "capture_process") as capture,
            ):
                result = self.runner.main([
                    "--host", "claude", "--skill", "speckit-coach", "--eval-id", "8",
                    "--source-commit", "test-commit", "--source-tree", "test-tree", "--model", "model-id",
                    "--cli", sys.executable, "--evidence-dir", str(evidence), "--execute",
                ])
            capture.assert_not_called()
            self.assertEqual(result, 1)
            manifest = json.loads((evidence / "manifest.json").read_text())
            self.assertIn("changed after command assembly", manifest["error"])

    def test_claude_autopilot_launch_is_held_without_safe_command_confinement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            case = self.case("claude", "speckit-autopilot", 2)
            stage = self.runner.stage_case(REPO_ROOT, case, Path(temporary))
            with self.assertRaises(self.runner.HeldLaunch):
                self.runner.build_command(case, stage, Path("/bin/claude"), "model-id", None)

    def test_process_capture_writes_exact_bytes_before_strict_decode_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cli = Path(temporary) / "claude"
            cli.write_text(
                f"#!{sys.executable}\nimport sys\nsys.stdout.buffer.write(b'\\xff')\n",
                encoding="utf-8",
            )
            cli.chmod(0o755)
            evidence = Path(temporary) / "evidence"
            with mock.patch.object(self.runner.shutil, "which", return_value=str(cli)):
                result = self.runner.capture_process(
                    "claude", [str(cli)], b"prompt", evidence, Path(temporary), os.environ.copy(), 5
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
            cli = Path(temporary) / "claude"
            cli.write_text("placeholder\n", encoding="utf-8")
            evidence = Path(temporary) / "evidence"
            with (
                mock.patch.object(self.runner.shutil, "which", return_value=str(cli)),
                mock.patch.object(self.runner.subprocess, "Popen", return_value=process) as popen,
                mock.patch.object(self.runner.os, "killpg") as killpg,
            ):
                result = self.runner.capture_process(
                    "claude", [str(cli)], b"prompt", evidence, Path(temporary), {}, 1
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
        case, policy, _ = self.claude_evidence()
        valid = "\n".join(
            json.dumps(item)
            for item in (
                {
                    "type": "system",
                    "subtype": "init",
                    "model": "resolved-model",
                    "plugins": [{"name": "speckit-pro"}],
                    "tools": ["Skill", "Read", "Glob", "Grep"],
                    "skills": policy["expected_skills"],
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
        self.assertEqual(parsed["available_skills"], policy["expected_skills"])
        self.runner.require_provider_evidence(case, parsed, policy)
        contaminated = {**parsed, "available_tools": [*parsed["available_tools"], "mcp__global__write"]}
        with self.assertRaisesRegex(self.runner.EvidenceError, "unexpected tools"):
            self.runner.require_provider_evidence(case, contaminated, policy)
        with self.assertRaises(self.runner.EvidenceError):
            self.runner.parse_events("claude", json.dumps({"type": "result", "is_error": False}))

    def test_required_provider_tool_and_plugin_evidence_fail_loud(self) -> None:
        claude_case, policy, parsed = self.claude_evidence()
        with self.assertRaises(self.runner.EvidenceError):
            self.runner.require_provider_evidence(
                claude_case,
                {**parsed, "available_tools": ["Skill", "Read"], "plugins": []},
                policy,
            )
        with self.assertRaisesRegex(self.runner.EvidenceError, "successful exact Skill invocation"):
            self.runner.require_provider_evidence(
                claude_case,
                {
                    **parsed,
                    "completed_tool_use_ids": [],
                },
                policy,
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
        with mock.patch.object(self.runner.shutil, "which", return_value=sys.executable):
            self.assertTrue(self.runner.probe_cli_version("claude", Path(sys.executable)).startswith("Python "))
        with tempfile.TemporaryDirectory() as temporary:
            empty = Path(temporary) / "empty-version"
            empty.write_text(f"#!{sys.executable}\n", encoding="utf-8")
            empty.chmod(0o755)
            with mock.patch.object(self.runner.shutil, "which", return_value=str(empty)):
                with self.assertRaises(self.runner.EvidenceError):
                    self.runner.probe_cli_version("claude", empty)

    def test_host_cli_must_still_match_the_fixed_host_executable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            resolved = Path(temporary) / "claude"
            requested = Path(temporary) / "other-cli"
            for path in (resolved, requested):
                path.write_text("placeholder\n", encoding="utf-8")
            with mock.patch.object(self.runner.shutil, "which", return_value=str(resolved)):
                with self.assertRaisesRegex(self.runner.EvidenceError, "changed"):
                    self.runner.probe_cli_version("claude", requested)
                result = self.runner.capture_process(
                    "claude", [str(requested)], b"", Path(temporary) / "evidence", Path(temporary), {}, 1
                )
        self.assertEqual(result["status"], "launch_error")
        self.assertIn("changed", result["error"])

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
