#!/usr/bin/env python3
"""Stdlib-only tests for XPLAT-006 mutation-capable runner helpers."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "mutation-helpers"
CONTRACT_DIR = FIXTURE_DIR / "contracts"
REQUEST_SCHEMA = CONTRACT_DIR / "mutation-helper-request.schema.json"
RESULT_SCHEMA = CONTRACT_DIR / "mutation-helper-result.schema.json"
PROMOTION_SCHEMA = CONTRACT_DIR / "helper-promotion-record.schema.json"

if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


def runner_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(PLUGIN_ROOT) if not existing else f"{PLUGIN_ROOT}{os.pathsep}{existing}"
    return env


def helper_request(
    helper_id: str,
    *,
    operation: str | None = None,
    mode: str = "dry_run",
    inputs: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "request_id": f"test-{helper_id}-{mode}",
        "helper_id": helper_id,
        "operation": operation or helper_id,
        "mode": mode,
        "inputs": inputs or {},
    }


def run_runner(
    request: object,
    *,
    cwd: Path = REPO_ROOT,
    env_overrides: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, object], list[dict[str, object]]]:
    env = runner_env()
    if env_overrides:
        env.update(env_overrides)
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(request) if not isinstance(request, str) else request,
        text=True,
        capture_output=True,
        cwd=cwd,
        env=env,
        shell=False,
        check=False,
    )
    response = json.loads(completed.stdout) if completed.stdout.strip() else {}
    stderr_records = [json.loads(line) for line in completed.stderr.splitlines() if line.strip()]
    return completed, response, stderr_records


def command_stdin_fixture(command: str) -> Path:
    if "<" not in command:
        raise AssertionError(f"authoritative_command must include a stdin fixture: {command}")
    stdin_path = command.split("<", 1)[1].strip()
    if not stdin_path or any(char.isspace() for char in stdin_path):
        raise AssertionError(f"authoritative_command must use one stdin fixture path: {command}")
    return REPO_ROOT / stdin_path


class MutationHelperTests(unittest.TestCase):
    def assert_response(self, response: dict[str, object], status: str, exit_code: int) -> None:
        self.assertEqual(response["schema_version"], "1.0")
        self.assertEqual(response["status"], status)
        self.assertEqual(response["exit_code"], exit_code)
        self.assertIsNone(response["legacy_exit_code"])
        self.assertIsInstance(response["diagnostics"], list)
        self.assertIsInstance(response["data"], dict)

    def test_install_subprocess_dispatch_preserves_selected_python_candidate(self) -> None:
        from speckit_pro_runner.helpers import install

        cases = [
            ("py -V:3", ["py", "-3", "-m", "speckit_pro_runner"], ["py", "-3", "-m", "speckit_pro_runner"]),
            ("python3", ["python3", "-m", "speckit_pro_runner"], ["python3", "-m", "speckit_pro_runner"]),
            ("python", ["python", "-m", "speckit_pro_runner"], ["python", "-m", "speckit_pro_runner"]),
        ]
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="{}", stderr="")

        for selected_candidate, argv, expected_argv in cases:
            with self.subTest(selected_candidate=selected_candidate):
                with patch.object(install.subprocess, "run", return_value=completed) as mocked_run:
                    result = install.run_python_runner_subprocess(
                        argv,
                        selected_candidate=selected_candidate,
                        input_text="{}",
                        cwd=REPO_ROOT,
                    )

                self.assertIs(result, completed)
                self.assertEqual(mocked_run.call_args.args[0], expected_argv)
                self.assertIs(mocked_run.call_args.kwargs["shell"], False)

    def temp_repo_path(self, name: str) -> tuple[tempfile.TemporaryDirectory[str], Path, str]:
        tmp = tempfile.TemporaryDirectory(dir=FIXTURE_DIR)
        path = Path(tmp.name) / name
        return tmp, path, path.relative_to(REPO_ROOT).as_posix()

    def temp_clean_git_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        self.run_git(root, "init", "--quiet")
        self.run_git(root, "config", "user.email", "git@github.com")
        self.run_git(root, "config", "user.name", "XPLAT Tests")
        self.run_git(root, "config", "commit.gpgsign", "false")
        (root / ".gitkeep").write_text("fixture\n", encoding="utf-8")
        marker = root / "speckit-pro" / "speckit_pro_runner"
        marker.mkdir(parents=True)
        (marker / ".gitkeep").write_text("runner marker\n", encoding="utf-8")
        self.run_git(root, "add", ".gitkeep")
        self.run_git(root, "add", "speckit-pro/speckit_pro_runner/.gitkeep")
        self.run_git(root, "commit", "--quiet", "-m", "init")
        return tmp, root

    def run_git(self, cwd: Path, *args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )

    def pr_packet_inputs(self, base_ref: str, *, feature_dir: str = "specs/g56r-001-packet-fixture") -> dict[str, object]:
        return {
            "source_feature_dir": feature_dir,
            "packet_id": "single-review",
            "base_ref": base_ref,
            "base_branch": base_ref,
            "title_type": "docs",
            "title_scope": "g56r-001",
            "title_description": "Publish candidate route baseline",
            "summary": "Publish the grounded candidate route baseline for reviewer handoff.",
            "what_changed": [
                "Added candidate route evidence.",
                "Prepared one schema-valid single PR packet.",
            ],
            "why_it_matters": "Reviewers receive one deterministic handoff instead of reconstructing packet metadata.",
            "how_to_review": [
                "Review the feature specification and changed-file scope.",
                "Confirm the body fingerprint with the read-only validator.",
            ],
            "how_to_uat": "Run the focused packet output and read-only validation tests.",
            "uat_runbook": "No manual product flow is required; the focused runner tests are the acceptance path.",
            "uat_source": f"{feature_dir}/quickstart.md",
            "verification_evidence": [
                {
                    "kind": "unit_test",
                    "source": f"{feature_dir}/quickstart.md",
                    "summary": "The packet output acceptance path passed.",
                    "result": "passed",
                }
            ],
            "scope_evidence": {
                "reviewable_loc": 12,
                "production_files": 0,
                "budget_result": "within_budget",
                "non_goals": [
                    "Split packet output remains deferred.",
                    "Write-mode packet validation remains deferred.",
                ],
            },
            "known_gaps": ["No known gaps for the single packet handoff."],
            "source_markers": [
                {
                    "marker_id": "feature-spec",
                    "rendered_text": "Source: the feature specification defines this reviewer handoff.",
                    "source": f"{feature_dir}/spec.md",
                }
            ],
        }

    def assert_schema_contract_response(self, response: dict[str, object], result_schema: dict[str, object]) -> None:
        self.assertIn(response["status"], result_schema["properties"]["status"]["enum"])
        self.assertIsInstance(response["diagnostics"], list)
        diagnostic_schema = result_schema["$defs"]["diagnostic"]
        for diag in response["diagnostics"]:
            self.assertIsInstance(diag, dict)
            for required in diagnostic_schema["required"]:
                self.assertIn(required, diag)
            self.assertEqual(diag["source"], "runner")
        mutation = response["data"].get("mutation")
        if mutation is None:
            return
        mutation_schema = result_schema["$defs"]["mutation"]
        for required in mutation_schema["required"]:
            self.assertIn(required, mutation)
        self.assertIn(mutation["mutation_status"], mutation_schema["properties"]["mutation_status"]["enum"])
        self.assertIsInstance(mutation["dirty_worktree"], bool)
        operation_schema = result_schema["$defs"]["operation_record"]
        for field in ["planned_operations", "applied_operations", "skipped_operations", "no_op_operations"]:
            for operation in mutation[field]:
                self.assertIn(operation["kind"], operation_schema["properties"]["kind"]["enum"])
                if operation["kind"] == "write_file":
                    self.assertIn("target", operation)
                    self.assertNotIn("command", operation)
                if operation["kind"] == "command_plan":
                    self.assertIn("command", operation)
                    self.assertNotIn("target", operation)

    def test_mutation_registry_lists_promoted_contracts_without_cutover(self) -> None:
        promotion_schema = json.loads(PROMOTION_SCHEMA.read_text(encoding="utf-8"))
        completed, response, stderr_records = run_runner(
            helper_request("mutation-registry-dispatch", operation="mutation-registry-dispatch", mode="read_only")
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        data = response["data"]
        helper_ids = [record["helper_id"] for record in data["helpers"]]
        self.assertIn("doctor-preflight", helper_ids)
        self.assertIn("generate-pr-body", helper_ids)
        self.assertIn("relocate-process-artifacts", helper_ids)
        self.assertEqual(data["active_cutover"], False)
        self.assertEqual(data["mode"], "mutation")
        for record in data["helpers"]:
            self.assertNotIn("script", record)
            self.assertNotEqual(record["promotion_status"], "python_authoritative")
            active_record = {key: value for key, value in record.items() if key != "inactive_provenance"}
            self.assertNotIn(".sh", json.dumps(active_record, sort_keys=True))
            if record["promotion_status"] in {"deferred", "out_of_scope"}:
                self.assertEqual(record["authoritative_command"], "")
            else:
                self.assertTrue(command_stdin_fixture(record["authoritative_command"]).is_file())
            promotion = record["promotion"]
            for required in promotion_schema["required"]:
                self.assertIn(required, promotion)
            self.assertEqual(promotion["helper_id"], record["helper_id"])
            self.assertIn(promotion["promotion_status"], promotion_schema["properties"]["promotion_status"]["enum"])
        prior_scripts = {
            record["helper_id"]: record.get("inactive_provenance", {}).get("prior_script")
            for record in data["helpers"]
        }
        self.assertIsNone(prior_scripts["install-codex-agents"])
        install_record = next(record for record in data["helpers"] if record["helper_id"] == "install-codex-agents")
        self.assertEqual(install_record["promotion"]["bash_reference_ids"], ["install-codex-agents"])
        self.assertEqual(prior_scripts["install-curated-set"], "speckit-pro/scripts/install-curated-set.sh")
        self.assertEqual(prior_scripts["generate-pr-body"], "speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh")
        self.assertEqual(prior_scripts["multi-pr-emission"], "speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh")
        rollbacks = {
            record["helper_id"]: record["promotion"]["rollback"]
            for record in data["helpers"]
        }
        self.assertEqual(
            rollbacks["install-codex-agents"],
            "Retry in dry_run mode and preserve the previous same-named Codex agent files before applying again.",
        )
        self.assertEqual(
            rollbacks["install-curated-set"],
            "Keep install-curated-set deferred until a Python runner implementation is promoted.",
        )
        self.assertEqual(
            rollbacks["generate-pr-body"],
            "Retry the registered generate-pr-body operation in dry_run mode before applying again.",
        )
        self.assertEqual(
            rollbacks["multi-pr-emission"],
            "Keep live PR mutation deferred; use the registered multi-pr-emission operation only for command-plan capture.",
        )

    def test_unpromoted_helpers_fail_closed_before_dispatch_in_all_mutation_modes(self) -> None:
        cases = [
            (
                "install-curated-set",
                "deferred",
                {
                    "operations": [
                        {
                            "operation_id": "adversarial-generic-write",
                            "kind": "write_file",
                            "target": "generated/adversarial.md",
                            "content": "generic dispatch must not write\n",
                        }
                    ]
                },
            ),
            (
                "generate-uat-skeleton",
                "deferred",
                {
                    "output_path": "generated/adversarial.md",
                    "content": "PR-emission dispatch must not write\n",
                },
            ),
            (
                "detect-stack-manager-plan",
                "out_of_scope",
                {
                    "commands": [["gh", "pr", "create"]],
                    "output_path": "generated/adversarial.md",
                    "content": "out-of-scope dispatch must not write\n",
                },
            ),
        ]

        for helper_id, promotion_status, inputs in cases:
            for mode in ("dry_run", "apply"):
                with self.subTest(helper_id=helper_id, mode=mode):
                    tmp, git_root = self.temp_clean_git_repo()
                    with tmp:
                        target = git_root / "generated" / "adversarial.md"
                        completed, response, stderr_records = run_runner(
                            helper_request(helper_id, mode=mode, inputs=inputs),
                            cwd=git_root,
                        )

                        self.assertEqual(completed.returncode, 1)
                        self.assert_response(response, "expected_failure", 1)
                        self.assertEqual([diag["code"] for diag in stderr_records], ["helper_not_promoted"])
                        self.assertEqual(response["data"]["promotion_status"], promotion_status)
                        self.assertFalse(response["data"]["writes_state"])
                        mutation = response["data"]["mutation"]
                        self.assertEqual(mutation["mode"], mode)
                        self.assertEqual(mutation["mutation_status"], "blocked")
                        self.assertEqual(mutation["planned_operations"], [])
                        self.assertEqual(mutation["applied_operations"], [])
                        self.assertEqual(mutation["planned_paths"], [])
                        self.assertEqual(mutation["touched_paths"], [])
                        self.assertFalse(mutation["live_mutation"])
                        self.assertFalse(target.exists())

    def test_install_codex_agents_refreshes_stale_files_and_preserves_unrelated_agents(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            stale = destination / "analyze-executor.toml"
            unrelated = destination / "user-owned-agent.toml"
            stale.write_text("stale\n", encoding="utf-8")
            unrelated.write_text("user owned\n", encoding="utf-8")
            inputs = {"destination": ".codex/agents", "model": "gpt-5.5"}

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            self.assertEqual(response["data"]["mutation"]["mutation_status"], "planned")
            self.assertEqual(len(response["data"]["mutation"]["planned_operations"]), 10)
            self.assertEqual(stale.read_text(encoding="utf-8"), "stale\n")

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            self.assertEqual(response["data"]["mutation"]["mutation_status"], "applied")
            self.assertTrue(response["data"]["writes_state"])
            self.assertTrue(response["data"]["restart_required"])
            self.assertEqual(response["data"]["verification"]["status"], "verified")
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "user owned\n")
            for source in sorted((PLUGIN_ROOT / "codex-agents").glob("*.toml")):
                self.assertEqual((destination / source.name).read_bytes(), source.read_bytes())

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "no_op")
            self.assertEqual(mutation["planned_operations"], [])
            self.assertEqual(len(mutation["no_op_operations"]), 10)
            self.assertFalse(response["data"]["restart_required"])

    def test_install_codex_agents_defaults_to_fake_user_home_without_touching_real_home(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as home_tmp:
            fake_home = Path(home_tmp).resolve()
            destination = fake_home / ".codex" / "agents"
            destination.mkdir(parents=True)
            unrelated = destination / "user-owned-agent.toml"
            unrelated.write_bytes(b"user owned\n")
            env = {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs={"model": "gpt-5.5"}),
                cwd=git_root,
                env_overrides=env,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            self.assertEqual(response["data"]["destination"], destination.as_posix())
            self.assertTrue(response["data"]["restart_required"])
            self.assertEqual(unrelated.read_bytes(), b"user owned\n")
            for source in sorted((PLUGIN_ROOT / "codex-agents").glob("*.toml")):
                self.assertEqual((destination / source.name).read_bytes(), source.read_bytes())

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs={"model": "gpt-5.5"}),
                cwd=git_root,
                env_overrides=env,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assertEqual(response["data"]["mutation"]["mutation_status"], "no_op")
            self.assertFalse(response["data"]["restart_required"])

    def test_install_codex_agents_applies_strict_gpt_5_4_destination_rewrite(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            completed, response, stderr_records = run_runner(
                helper_request(
                    "install-codex-agents",
                    mode="apply",
                    inputs={"destination": ".codex/agents", "model": "gpt-5.4"},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            destination = (git_root / ".codex" / "agents").resolve()
            spark = (destination / "autopilot-fast-helper.toml").read_text(encoding="utf-8")
            self.assertIn('model = "gpt-5.3-codex-spark"', spark)
            for target in sorted(destination.glob("*.toml")):
                if target.name == "autopilot-fast-helper.toml":
                    continue
                self.assertIn('model = "gpt-5.4"', target.read_text(encoding="utf-8"), target.name)

    def test_install_codex_agents_rejects_invalid_model_and_incomplete_source_before_writes(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            destination = (git_root / ".codex" / "agents").resolve()
            completed, response, stderr_records = run_runner(
                helper_request(
                    "install-codex-agents",
                    mode="apply",
                    inputs={"destination": ".codex/agents", "model": "unsupported"},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_codex_model"])
            self.assertFalse(destination.exists())

        with tempfile.TemporaryDirectory() as source_tmp:
            fake_plugin = Path(source_tmp) / "speckit-pro"
            shutil.copytree(PLUGIN_ROOT / "codex-agents", fake_plugin / "codex-agents")
            (fake_plugin / "codex-agents" / "uat-runbook-author.toml").unlink()
            request = SimpleNamespace(
                request_id="test-incomplete-codex-agent-source",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="dry_run",
                inputs={"destination": ".codex/agents", "model": "gpt-5.5"},
            )
            from speckit_pro_runner.helpers import install
            from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

            with patch.object(install, "codex_plugin_root", return_value=fake_plugin):
                response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            self.assertEqual(response["status"], "input_error")
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["incomplete_agent_bundle"])

        with tempfile.TemporaryDirectory() as source_tmp:
            fake_plugin = Path(source_tmp) / "speckit-pro"
            shutil.copytree(PLUGIN_ROOT / "codex-agents", fake_plugin / "codex-agents")
            analyze = fake_plugin / "codex-agents" / "analyze-executor.toml"
            analyze.write_text(
                analyze.read_text(encoding="utf-8").replace('model = "gpt-5.5"', "model = 'gpt-5.5'", 1),
                encoding="utf-8",
            )
            request = SimpleNamespace(
                request_id="test-noncanonical-codex-agent-model",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="dry_run",
                inputs={"destination": ".codex/agents", "model": "gpt-5.4"},
            )
            from speckit_pro_runner.helpers import install
            from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

            with patch.object(install, "codex_plugin_root", return_value=fake_plugin):
                response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            self.assertEqual(response["status"], "input_error")
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["unsafe_agent_bundle"])

    def test_install_codex_agents_rolls_back_failed_batch(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            destination = destination.resolve()
            stale = destination / "analyze-executor.toml"
            unrelated = destination / "user-owned-agent.toml"
            stale.write_bytes(b"stale\xff\n")
            stale.chmod(0o640)
            unrelated.write_bytes(b"user owned\n")
            request = SimpleNamespace(
                request_id="test-codex-agent-rollback",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs={"destination": ".codex/agents", "model": "gpt-5.5"},
            )
            from speckit_pro_runner.helpers import install
            from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

            real_write = install.write_codex_agent_atomic

            def fail_second_write(
                target: Path,
                content: bytes,
                target_dir: Path,
                identity: tuple[int, int] | None,
                *,
                mode: int | None = None,
            ) -> None:
                if target.name == "autopilot-fast-helper.toml":
                    raise OSError("injected test failure")
                real_write(target, content, target_dir, identity, mode=mode)

            with (
                patch.object(install, "codex_agent_destination", return_value=destination),
                patch.object(install, "write_codex_agent_atomic", side_effect=fail_second_write),
            ):
                response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)

            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["codex_agent_install_failed"])
            self.assertTrue(response["data"]["rollback_succeeded"])
            self.assertFalse(response["data"]["writes_state"])
            self.assertFalse(response["data"]["restart_required"])
            self.assertEqual(stale.read_bytes(), b"stale\xff\n")
            self.assertEqual(stale.stat().st_mode & 0o7777, 0o640)
            self.assertEqual(unrelated.read_bytes(), b"user owned\n")
            self.assertEqual(sorted(path.name for path in destination.glob("*.toml")), ["analyze-executor.toml", "user-owned-agent.toml"])

    def test_install_codex_agents_mode_restore_fails_closed_without_fchmod(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            from speckit_pro_runner.helpers import install

            identity = install.codex_agent_destination_identity(destination)
            with patch.object(install.os, "fchmod", None):
                with self.assertRaisesRegex(OSError, "descriptor-based mode restoration"):
                    install.write_codex_agent_atomic(
                        target,
                        b"restored\n",
                        destination,
                        identity,
                        mode=0o640,
                    )

            self.assertFalse(target.exists())
            self.assertEqual(list(destination.iterdir()), [])

    def test_install_codex_agents_snapshot_uses_open_descriptor_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp).resolve() / "analyze-executor.toml"
            target.write_bytes(b"existing\n")
            target.chmod(0o600)
            from speckit_pro_runner.helpers import install

            real_open = install.os.open

            def chmod_after_open(path: object, flags: int) -> int:
                descriptor = real_open(path, flags)
                Path(path).chmod(0o640)
                return descriptor

            with patch.object(install.os, "open", side_effect=chmod_after_open):
                state = install.codex_agent_previous_state(target)

            self.assertIsNotNone(state)
            assert state is not None
            self.assertEqual(state[0], b"existing\n")
            self.assertEqual(state[1] & 0o7777, 0o640)

    def test_install_codex_agents_rollback_never_chmods_swapped_symlink_target(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as outside_tmp:
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            destination = destination.resolve()
            stale = destination / "analyze-executor.toml"
            stale.write_bytes(b"stale\n")
            stale.chmod(0o640)
            outside = Path(outside_tmp).resolve() / "outside.toml"
            outside.write_bytes(b"outside\n")
            outside.chmod(0o600)
            outside_mode = outside.stat().st_mode & 0o7777
            request = SimpleNamespace(
                request_id="test-codex-agent-rollback-symlink-swap",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs={"destination": ".codex/agents", "model": "gpt-5.5"},
            )
            from speckit_pro_runner.helpers import install
            from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

            real_replace = install.os.replace
            replace_count = 0

            def swap_after_rollback_replace(source: object, target: object) -> None:
                nonlocal replace_count
                real_replace(source, target)
                replace_count += 1
                if replace_count == 2:
                    target_path = Path(target)
                    target_path.unlink()
                    target_path.symlink_to(outside)

            real_write = install.write_codex_agent_atomic

            def fail_second_write(
                target: Path,
                content: bytes,
                target_dir: Path,
                identity: tuple[int, int] | None,
                *,
                mode: int | None = None,
            ) -> None:
                if target.name == "autopilot-fast-helper.toml":
                    raise OSError("injected test failure")
                real_write(target, content, target_dir, identity, mode=mode)

            with (
                patch.object(install, "codex_agent_destination", return_value=destination),
                patch.object(install, "write_codex_agent_atomic", side_effect=fail_second_write),
                patch.object(install.os, "replace", side_effect=swap_after_rollback_replace),
            ):
                response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)

            self.assert_response(response, "expected_failure", 1)
            self.assertFalse(response["data"]["rollback_succeeded"])
            self.assertTrue(response["data"]["writes_state"])
            self.assertTrue(response["data"]["restart_required"])
            self.assertEqual(outside.read_bytes(), b"outside\n")
            self.assertEqual(outside.stat().st_mode & 0o7777, outside_mode)

    def test_install_codex_agents_rejects_non_codex_and_symlink_destinations(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            completed, response, stderr_records = run_runner(
                helper_request(
                    "install-codex-agents",
                    mode="apply",
                    inputs={"destination": "agents", "model": "gpt-5.5"},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_destination"])
            self.assertFalse((git_root / "agents").exists())

            with tempfile.TemporaryDirectory() as outside:
                codex_dir = git_root / ".codex"
                try:
                    codex_dir.symlink_to(Path(outside), target_is_directory=True)
                except OSError:
                    self.skipTest("symlink creation is unavailable")
                completed, response, stderr_records = run_runner(
                    helper_request(
                        "install-codex-agents",
                        mode="apply",
                        inputs={"destination": ".codex/agents", "model": "gpt-5.5"},
                    ),
                    cwd=git_root,
                )
                self.assertEqual(completed.returncode, 2)
                self.assert_response(response, "input_error", 2)
                self.assertEqual([diag["code"] for diag in stderr_records], ["unsafe_agent_destination"])
                self.assertEqual(list(Path(outside).iterdir()), [])

    def test_install_codex_agents_rejects_managed_leaf_symlink_before_writes(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as outside_tmp:
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            outside = Path(outside_tmp) / "outside.toml"
            outside.write_bytes(b"outside\xff\n")
            try:
                (destination / "analyze-executor.toml").symlink_to(outside)
            except OSError:
                self.skipTest("symlink creation is unavailable")

            completed, response, stderr_records = run_runner(
                helper_request(
                    "install-codex-agents",
                    mode="apply",
                    inputs={"destination": ".codex/agents", "model": "gpt-5.5"},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["unsafe_agent_destination"])
            self.assertEqual(outside.read_bytes(), b"outside\xff\n")
            self.assertEqual(sorted(path.name for path in destination.iterdir()), ["analyze-executor.toml"])

    def test_install_codex_agents_blocks_destination_identity_change(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            destination = destination.resolve()
            request = SimpleNamespace(
                request_id="test-codex-agent-destination-race",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs={"destination": ".codex/agents", "model": "gpt-5.5"},
            )
            from speckit_pro_runner.helpers import install
            from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

            real_identity = install.codex_agent_destination_identity(destination)
            identities = iter((real_identity, (real_identity[0], real_identity[1] + 1)))
            with (
                patch.object(install, "codex_agent_destination", return_value=destination),
                patch.object(install, "codex_agent_destination_identity", side_effect=lambda _path: next(identities)),
            ):
                response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)

            self.assert_response(response, "expected_failure", 1)
            self.assertTrue(response["data"]["rollback_succeeded"])
            self.assertFalse(response["data"]["writes_state"])
            self.assertEqual(list(destination.iterdir()), [])

    def test_dry_run_reports_planned_write_without_mutating(self) -> None:
        tmp, target, rel = self.temp_repo_path("dry-run-output.json")
        with tmp:
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    inputs={
                        "operations": [
                            {
                                "operation_id": "write-json",
                                "kind": "write_file",
                                "target": rel,
                                "content": "{\"ok\":true}\n",
                            }
                        ]
                    },
                )
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mode"], "dry_run")
            self.assertEqual(mutation["mutation_status"], "planned")
            self.assertEqual(len(mutation["planned_operations"]), 1)
            self.assertEqual(mutation["applied_operations"], [])
            self.assertFalse(target.exists())

    def test_apply_writes_complete_file_with_final_newline(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            target = git_root / "generated" / "apply-output.md"
            rel = "generated/apply-output.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "operations": [
                            {
                                "operation_id": "write-md",
                                "kind": "write_file",
                                "target": rel,
                                "content": "# Generated\n",
                            }
                        ]
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            self.assertEqual(target.read_text(encoding="utf-8"), "# Generated\n")
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "applied")
            self.assertEqual(len(mutation["applied_operations"]), 1)
            self.assertEqual(mutation["touched_paths"], [rel])

    def test_apply_rejects_dirty_worktree_without_touching_target(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            (git_root / "untracked.txt").write_text("dirty\n", encoding="utf-8")
            target = git_root / "generated" / "dirty-output.md"
            rel = "generated/dirty-output.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "operations": [{"operation_id": "dirty", "kind": "write_file", "target": rel, "content": "dirty\n"}],
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["dirty_worktree"])
            self.assertEqual(response["data"]["mutation"]["dirty_worktree"], True)
            self.assertFalse(target.exists())

    def test_apply_rejects_when_git_status_cannot_prove_clean_worktree(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            target = git_root / "generated" / "status-error.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "test_overrides": {"git_status_error": True},
                        "operations": [
                            {
                                "operation_id": "status-error",
                                "kind": "write_file",
                                "target": "generated/status-error.md",
                                "content": "blocked\n",
                            }
                        ],
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["git_status_unavailable"])
            self.assertEqual(response["data"]["mutation"]["dirty_worktree"], False)
            self.assertFalse(target.exists())

    def test_apply_no_op_succeeds_without_touching_dirty_worktree(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            (git_root / "untracked.txt").write_text("dirty\n", encoding="utf-8")
            completed, response, stderr_records = run_runner(
                helper_request("mutation-foundation", mode="apply", inputs={"operations": []}),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "no_op")
            self.assertEqual(mutation["applied_operations"], [])
            self.assertEqual(mutation["touched_paths"], [])
            self.assertFalse(mutation["dirty_worktree"])

    def test_path_escape_and_symlink_targets_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as outside, tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as inside:
            outside_path = Path(outside) / "outside.md"
            outside_path.write_text("outside\n", encoding="utf-8")
            link = Path(inside) / "escape.md"
            try:
                link.symlink_to(outside_path)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            rel = link.relative_to(REPO_ROOT).as_posix()
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={"operations": [{"operation_id": "escape", "kind": "write_file", "target": rel, "content": "x\n"}]},
                )
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_path"])

            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "operations": [
                            {
                                "operation_id": "absolute-escape",
                                "kind": "write_file",
                                "target": str(outside_path),
                                "content": "x\n",
                            }
                        ]
                    },
                )
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_path"])

    def test_preflight_rejects_parent_file_before_apply_writes(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            parent_file = git_root / "parent-is-file"
            parent_file.write_text("not a directory\n", encoding="utf-8")
            target = parent_file / "child.md"
            rel = "parent-is-file/child.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={"operations": [{"operation_id": "write-failure", "kind": "write_file", "target": rel, "content": "x\n"}]},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_path"])
            self.assertFalse(target.exists())

    def test_batch_write_conflicts_are_rejected_before_apply_writes(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            parent = git_root / "generated" / "parent.md"
            child = parent / "child.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "operations": [
                            {
                                "operation_id": "parent",
                                "kind": "write_file",
                                "target": "generated/parent.md",
                                "content": "parent\n",
                            },
                            {
                                "operation_id": "child",
                                "kind": "write_file",
                                "target": "generated/parent.md/child.md",
                                "content": "child\n",
                            },
                        ]
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["conflicting_operations"])
            self.assertFalse(parent.exists())
            self.assertFalse(child.exists())

    def test_partial_failure_reports_applied_operation_and_manual_remediation(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            first = git_root / "first.md"
            second = git_root / "second.md"
            first_rel = "first.md"
            second_rel = "second.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "simulate_failure_after": 1,
                        "operations": [
                            {"operation_id": "first", "kind": "write_file", "target": first_rel, "content": "first\n"},
                            {"operation_id": "second", "kind": "write_file", "target": second_rel, "content": "second\n"},
                        ],
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["partial_failure"])
            mutation = response["data"]["mutation"]
            self.assertEqual([op["operation_id"] for op in mutation["applied_operations"]], ["first"])
            self.assertEqual(mutation["failure_operation"]["operation_id"], "second")
            self.assertTrue(mutation["manual_remediation"])
            self.assertTrue(first.exists())
            self.assertFalse(second.exists())

    def test_doctor_preflight_detects_missing_files_and_repair_uses_fake_home(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            install_root = git_root / "tests" / "speckit-pro" / "unit" / "fixtures" / "fake-home"
            root_rel = install_root.relative_to(git_root).as_posix()
            inventory = {
                "files": [
                    {"path": "agents/a.md", "content": "agent\n", "sha256": "skip"},
                    {"path": "runner/runner.py", "content": "runner\n", "sha256": "skip"},
                ]
            }
            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-preflight",
                    mode="read_only",
                    inputs={"install_root": root_rel, "inventory": inventory, "fake_home": True},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            doctor = response["data"]["doctor"]
            self.assertEqual(doctor["status"], "safe_repair")
            self.assertEqual(len(doctor["missing_files"]), 2)

            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-repair",
                    mode="apply",
                    inputs={"install_root": root_rel, "inventory": inventory, "fake_home": True},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            self.assertTrue((install_root / "agents" / "a.md").is_file())
            self.assertTrue((install_root / "runner" / "runner.py").is_file())

            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-preflight",
                    mode="read_only",
                    inputs={"install_root": root_rel, "inventory": inventory, "fake_home": True},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            self.assertEqual(response["data"]["doctor"]["status"], "complete")

            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-preflight",
                    mode="read_only",
                    inputs={"install_root": root_rel, "inventory": {"files": "bad"}, "fake_home": True},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["malformed_inventory"])

    def test_doctor_repair_refuses_non_fake_home(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            install_root = git_root / "tests" / "speckit-pro" / "unit" / "fixtures" / "fake-home"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-repair",
                    mode="apply",
                    inputs={"install_root": install_root.relative_to(git_root).as_posix(), "inventory": {"files": []}},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["real_home_refused"])

    def test_doctor_repair_rejects_fake_home_outside_fixture_boundary(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-repair",
                    mode="apply",
                    inputs={"install_root": "speckit-pro", "inventory": {"files": []}, "fake_home": True},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["fake_home_boundary_refused"])

    def test_doctor_repair_rejects_backslash_traversal_inventory_path(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            install_root = git_root / "tests" / "speckit-pro" / "unit" / "fixtures" / "fake-home"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-repair",
                    mode="apply",
                    inputs={
                        "install_root": install_root.relative_to(git_root).as_posix(),
                        "inventory": {
                            "files": [
                                {
                                    "path": "..\\escaped.md",
                                    "content": "escape\n",
                                    "sha256": "skip",
                                }
                            ]
                        },
                        "fake_home": True,
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["malformed_inventory"])
            self.assertFalse((git_root / "tests" / "speckit-pro" / "unit" / "fixtures" / "escaped.md").exists())

    def test_pr_emission_apply_writes_generated_body_and_command_plans_do_not_execute_gh(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            target = git_root / "generated" / "pr-body.md"
            rel = "generated/pr-body.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "generate-pr-body",
                    mode="apply",
                    inputs={"output_path": rel, "title": "feat(XPLAT-006): helper port", "sections": ["Summary", "Verification"]},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            text = target.read_text(encoding="utf-8")
            self.assertIn("# feat(XPLAT-006): helper port", text)
            self.assertTrue(text.endswith("\n"))

            completed, response, stderr_records = run_runner(
                helper_request(
                    "multi-pr-emission",
                    inputs={"commands": [["gh", "pr", "create", "--draft"]], "live_mutation_approved": False},
                )
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "planned")
            self.assertEqual(mutation["applied_operations"], [])
            self.assertFalse(mutation["live_mutation"])

            completed, response, stderr_records = run_runner(
                helper_request(
                    "multi-pr-emission",
                    mode="apply",
                    inputs={"commands": [["gh", "pr", "create", "--draft"]], "live_mutation_approved": True},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["deferred_live_mutation"])
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "blocked")
            self.assertEqual(mutation["applied_operations"], [])
            self.assertFalse(mutation["live_mutation"])

            completed, response, stderr_records = run_runner(
                helper_request("generate-uat-skeleton", mode="apply", inputs={}),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["helper_not_promoted"])
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "blocked")
            self.assertEqual(mutation["applied_operations"], [])
            self.assertFalse(mutation["live_mutation"])

    def test_pr_packet_output_derives_single_body_and_packet_then_passes_read_only_validation(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            base_ref = "integration-base"
            self.run_git(git_root, "branch", base_ref)
            self.run_git(git_root, "checkout", "--quiet", "-b", "packet-feature")
            feature_dir = "specs/g56r-001-packet-fixture"
            feature = git_root / feature_dir
            feature.mkdir(parents=True)
            (feature / "spec.md").write_text("# Feature Specification: Candidate Route Baseline\n", encoding="utf-8")
            (feature / "quickstart.md").write_text("# Quickstart\n\nRun focused tests.\n", encoding="utf-8")
            (git_root / "candidate.json").write_text('{"candidate":"route"}\n', encoding="utf-8")
            self.run_git(git_root, "add", feature_dir, "candidate.json")
            self.run_git(git_root, "commit", "--quiet", "-m", "docs(g56r-001): add packet fixture")

            inputs = self.pr_packet_inputs(base_ref, feature_dir=feature_dir)
            missing_source = {**inputs, "verification_evidence": [{**inputs["verification_evidence"][0], "source": "docs/missing.md"}]}
            completed, blocked, stderr_records = run_runner(
                helper_request("pr-packet-output", mode="apply", inputs=missing_source),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(blocked, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_input"])

            completed, dry_run, stderr_records = run_runner(
                helper_request("pr-packet-output", mode="dry_run", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assert_response(dry_run, "ok", 0)
            self.assertEqual(stderr_records, [])
            required_trailer = dry_run["data"]["required_source_commit_trailer"]
            self.assertEqual(
                required_trailer,
                f"SpecKit-Pro-Protected-Body-SHA256: {dry_run['data']['protected_body_fingerprint']}",
            )
            completed, unauthorized_apply, stderr_records = run_runner(
                helper_request("pr-packet-output", mode="apply", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 3)
            self.assert_response(unauthorized_apply, "missing_prerequisite", 3)
            self.assertEqual(
                [diag["code"] for diag in stderr_records],
                ["protected_body_authorization_missing"],
            )
            self.assertFalse((git_root / unauthorized_apply["data"]["body_file"]).exists())
            self.assertFalse((git_root / unauthorized_apply["data"]["packet_path"]).exists())
            self.run_git(
                git_root,
                "commit",
                "--quiet",
                "--allow-empty",
                "-m",
                "chore(g56r-001): authorize review packet body",
                "-m",
                required_trailer,
            )
            completed, authorized_dry_run, stderr_records = run_runner(
                helper_request("pr-packet-output", mode="dry_run", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                authorized_dry_run["data"]["protected_body_fingerprint"],
                dry_run["data"]["protected_body_fingerprint"],
            )

            completed, response, stderr_records = run_runner(
                helper_request("pr-packet-output", mode="apply", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "applied")
            self.assertEqual(
                [operation["operation_id"] for operation in mutation["planned_operations"]],
                ["pr-packet-output:body", "pr-packet-output:packet"],
            )
            self.assertEqual(mutation["applied_operations"], mutation["planned_operations"])

            packet_path = git_root / str(response["data"]["packet_path"])
            body_path = git_root / str(response["data"]["body_file"])
            self.assertTrue(packet_path.is_file())
            self.assertTrue(body_path.is_file())
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            body = body_path.read_text(encoding="utf-8")
            self.assertEqual(packet["mode"], "single")
            self.assertEqual(packet["schema_version"], "1.1.0")
            self.assertRegex(packet["source_revision"]["base_sha"], r"^[0-9a-f]{40,64}$")
            self.assertRegex(packet["source_revision"]["source_head_sha"], r"^[0-9a-f]{40,64}$")
            self.assertRegex(
                packet["source_revision"]["source_diff_fingerprint"]["value"],
                r"^[0-9a-f]{64}$",
            )
            self.assertEqual(
                packet["protected_body_fingerprint"]["normalization_profile"],
                "whole_body_v2",
            )
            self.assertNotIn("split_slice", packet)
            self.assertEqual(packet["generated_title"]["value"], "docs(g56r-001): Publish candidate route baseline")
            self.assertEqual(packet["body_file"], body_path.relative_to(git_root).as_posix())
            self.assertEqual(packet["scope_evidence"]["total_files"], len(packet["scope_evidence"]["changed_files"]))
            self.assertIn(packet_path.relative_to(git_root).as_posix(), packet["scope_evidence"]["changed_files"])
            self.assertIn(body_path.relative_to(git_root).as_posix(), packet["scope_evidence"]["changed_files"])
            for heading in packet["required_headings"]:
                self.assertIn(f"## {heading}\n", body)
            self.assertIn(packet["source_markers"][0]["rendered_text"], body)
            self.assertTrue(body.endswith("\n"))
            self.assertTrue(packet_path.read_text(encoding="utf-8").endswith("\n"))

            completed, uncommitted_validation, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    operation="validate-pr-packet-read-only",
                    mode="read_only",
                    inputs={"packet_path": packet_path.relative_to(git_root).as_posix()},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn(
                "source.packet_commit",
                {failure["rule"] for failure in uncommitted_validation["data"]["stdout_json"]["failures"]},
            )

            self.run_git(git_root, "add", body_path.relative_to(git_root).as_posix(), packet_path.relative_to(git_root).as_posix())
            self.run_git(git_root, "commit", "--quiet", "-m", "docs(g56r-001): add review packet")
            completed, validation, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    operation="validate-pr-packet-read-only",
                    mode="read_only",
                    inputs={"packet_path": packet_path.relative_to(git_root).as_posix()},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assert_response(validation, "ok", 0)
            self.assertEqual(stderr_records, [])
            self.assertEqual(validation["data"]["stdout_json"]["status"], "passed")
            self.assertFalse(validation["data"]["stdout_json"]["pr_blocked"])
            self.assertFalse(validation["data"]["writes_state"])

            packet_text = packet_path.read_text(encoding="utf-8")
            downgraded = json.loads(packet_text)
            downgraded["schema_version"] = "1.0.0"
            packet_path.write_text(json.dumps(downgraded, indent=2) + "\n", encoding="utf-8")
            completed, downgrade_validation, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    operation="validate-pr-packet-read-only",
                    mode="read_only",
                    inputs={"packet_path": packet_path.relative_to(git_root).as_posix()},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(downgrade_validation, "expected_failure", 1)
            self.assertTrue(downgrade_validation["data"]["stdout_json"]["pr_blocked"])
            self.assertIn(
                "source.legacy_unbound",
                {failure["rule"] for failure in downgrade_validation["data"]["stdout_json"]["failures"]},
            )

            missing_profile = json.loads(packet_text)
            missing_profile["protected_body_fingerprint"].pop("normalization_profile")
            packet_path.write_text(json.dumps(missing_profile, indent=2) + "\n", encoding="utf-8")
            completed, profile_validation, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    operation="validate-pr-packet-read-only",
                    mode="read_only",
                    inputs={"packet_path": packet_path.relative_to(git_root).as_posix()},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(profile_validation, "expected_failure", 1)
            profile_failures = profile_validation["data"]["stdout_json"]["failures"]
            self.assertTrue(profile_validation["data"]["stdout_json"]["pr_blocked"])
            self.assertTrue(
                any(
                    failure["rule"] == "packet.schema.required"
                    and failure["field"] == "protected_body_fingerprint.normalization_profile"
                    for failure in profile_failures
                ),
                profile_failures,
            )
            packet_path.write_text(packet_text, encoding="utf-8")

            body_before = body_path.read_text(encoding="utf-8")
            packet_before = packet_path.read_text(encoding="utf-8")
            mismatched_base = json.loads(packet_before)
            mismatched_base["target"]["base_branch"] = "release"
            packet_path.write_text(json.dumps(mismatched_base, indent=2) + "\n", encoding="utf-8")
            completed, base_validation, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    operation="validate-pr-packet-read-only",
                    mode="read_only",
                    inputs={"packet_path": packet_path.relative_to(git_root).as_posix()},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn(
                "source.base_branch",
                {failure["rule"] for failure in base_validation["data"]["stdout_json"]["failures"]},
            )
            packet_path.write_text(packet_before, encoding="utf-8")

            from speckit_pro_runner.helpers.read_only import protected_body_sha256

            tampered_body = body_before.replace(
                "No known gaps for the single packet handoff.",
                "Protected packet prose was changed.",
            )
            tampered_packet = json.loads(packet_before)
            tampered_packet["protected_body_fingerprint"]["value"] = protected_body_sha256(tampered_body)
            body_path.write_text(tampered_body, encoding="utf-8")
            packet_path.write_text(json.dumps(tampered_packet, indent=2) + "\n", encoding="utf-8")
            completed, tampered_validation, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    operation="validate-pr-packet-read-only",
                    mode="read_only",
                    inputs={"packet_path": packet_path.relative_to(git_root).as_posix()},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            tampered_rules = {
                failure["rule"] for failure in tampered_validation["data"]["stdout_json"]["failures"]
            }
            self.assertIn("source.worktree", tampered_rules)
            self.assertNotIn("body.protected_fingerprint", tampered_rules)
            body_path.write_text(body_before, encoding="utf-8")
            packet_path.write_text(packet_before, encoding="utf-8")

            body_path.write_text(tampered_body, encoding="utf-8")
            packet_path.write_text(json.dumps(tampered_packet, indent=2) + "\n", encoding="utf-8")
            self.run_git(
                git_root,
                "add",
                body_path.relative_to(git_root).as_posix(),
                packet_path.relative_to(git_root).as_posix(),
            )
            self.run_git(git_root, "commit", "--quiet", "--amend", "--no-edit")
            completed, committed_tamper_validation, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    operation="validate-pr-packet-read-only",
                    mode="read_only",
                    inputs={"packet_path": packet_path.relative_to(git_root).as_posix()},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            committed_tamper_rules = {
                failure["rule"]
                for failure in committed_tamper_validation["data"]["stdout_json"]["failures"]
            }
            self.assertIn("source.body_authorization", committed_tamper_rules)
            self.assertNotIn("source.worktree", committed_tamper_rules)
            self.assertNotIn("body.protected_fingerprint", committed_tamper_rules)
            body_path.write_text(body_before, encoding="utf-8")
            packet_path.write_text(packet_before, encoding="utf-8")
            self.run_git(
                git_root,
                "add",
                body_path.relative_to(git_root).as_posix(),
                packet_path.relative_to(git_root).as_posix(),
            )
            self.run_git(git_root, "commit", "--quiet", "--amend", "--no-edit")

            completed, existing_response, stderr_records = run_runner(
                helper_request("pr-packet-output", mode="apply", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(existing_response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["existing_pr_packet_output"])
            self.assertTrue(stderr_records[0]["details"]["body_exists"])
            self.assertTrue(stderr_records[0]["details"]["packet_exists"])
            self.assertIn("never authorize reuse", stderr_records[0]["remediation"]["actions"][0])
            self.assertEqual(body_path.read_text(encoding="utf-8"), body_before)
            self.assertEqual(packet_path.read_text(encoding="utf-8"), packet_before)

            candidate = git_root / "candidate.json"
            candidate.write_text('{"candidate":"route-updated"}\n', encoding="utf-8")
            self.run_git(git_root, "add", candidate.relative_to(git_root).as_posix())
            self.run_git(git_root, "commit", "--quiet", "-m", "docs(g56r-001): update existing route")

            completed, stale_validation, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    operation="validate-pr-packet-read-only",
                    mode="read_only",
                    inputs={"packet_path": packet_path.relative_to(git_root).as_posix()},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(stale_validation, "expected_failure", 1)
            self.assertTrue(stale_validation["data"]["stdout_json"]["pr_blocked"])
            stale_rules = {
                failure["rule"]
                for failure in stale_validation["data"]["stdout_json"]["failures"]
            }
            self.assertIn("source.post_generation_change", stale_rules)

            completed, later_existing, stderr_records = run_runner(
                helper_request("pr-packet-output", mode="apply", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(later_existing, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["existing_pr_packet_output"])
            self.assertIn("never authorize reuse", stderr_records[0]["remediation"]["actions"][0])
            self.assertEqual(body_path.read_text(encoding="utf-8"), body_before)
            self.assertEqual(packet_path.read_text(encoding="utf-8"), packet_before)

    def test_pr_packet_output_rejects_unsafe_or_unsupported_inputs_before_writes(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            base_ref = "integration-base"
            self.run_git(git_root, "branch", base_ref)
            self.run_git(git_root, "checkout", "--quiet", "-b", "packet-feature")
            baseline = self.pr_packet_inputs(base_ref)
            self.run_git(git_root, "update-ref", "refs/remotes/origin/integration-base", "integration-base")
            origin_inputs = {**baseline, "base_ref": "origin/integration-base"}
            completed, response, stderr_records = run_runner(
                helper_request("pr-packet-output", inputs=origin_inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])

            cases = {
                "raw output injection": {**baseline, "output_path": "generated/unsafe.json"},
                "feature traversal": {**baseline, "source_feature_dir": "specs/../outside"},
                "scope mismatch": {**baseline, "title_scope": "spec-998"},
                "base mismatch": {**baseline, "base_branch": "develop"},
                "multiline title": {**baseline, "title_description": "Publish candidate route baseline\n"},
                "unsupported remote": {**baseline, "base_ref": "upstream/integration-base"},
                "full local ref": {**baseline, "base_ref": "refs/heads/integration-base"},
                "sha object target": {**baseline, "base_ref": "deadbeef", "base_branch": "deadbeef"},
                "same head and base": {
                    **baseline,
                    "base_ref": "packet-feature",
                    "base_branch": "packet-feature",
                },
                "missing verification": {**baseline, "verification_evidence": []},
                "unsafe evidence source": {
                    **baseline,
                    "source_markers": [
                        {
                            "marker_id": "unsafe",
                            "rendered_text": "Source: unsafe.",
                            "source": "../outside.md",
                        }
                    ],
                },
                "split mode injection": {**baseline, "mode": "split"},
            }
            for name, inputs in cases.items():
                with self.subTest(msg=name):
                    completed, response, stderr_records = run_runner(
                        helper_request("pr-packet-output", inputs=inputs),
                        cwd=git_root,
                    )
                    self.assertEqual(completed.returncode, 2)
                    self.assert_response(response, "input_error", 2)
                    self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_input"])
                    self.assertFalse((git_root / "generated" / "unsafe.json").exists())
                    self.assertFalse((git_root / "specs" / "g56r-001-packet-fixture" / ".process").exists())

            dirty = git_root / "dirty.txt"
            dirty.write_text("untracked\n", encoding="utf-8")
            completed, response, stderr_records = run_runner(
                helper_request("pr-packet-output", inputs=baseline),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["dirty_worktree"])
            self.assertIn("both dry_run and apply modes", stderr_records[0]["message"])
            self.assertIn("committed base...HEAD evidence", stderr_records[0]["message"])
            self.assertEqual(response["data"]["mutation"]["mutation_status"], "blocked")
            self.assertNotIn("changed_file_count", response["data"])
            dirty.unlink()

            existing = git_root / "specs" / "g56r-001-packet-fixture" / ".process" / "pr-packets" / "single-review.md"
            existing.parent.mkdir(parents=True)
            existing.write_text("existing packet body\n", encoding="utf-8")
            self.run_git(git_root, "add", existing.relative_to(git_root).as_posix())
            self.run_git(git_root, "commit", "--quiet", "-m", "test: add existing packet body")
            completed, response, stderr_records = run_runner(
                helper_request("pr-packet-output", inputs=baseline),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["partial_pr_packet_output"])
            self.assertEqual(stderr_records[0]["details"]["body_exists"], True)
            self.assertEqual(stderr_records[0]["details"]["packet_exists"], False)
            self.assertEqual(existing.read_text(encoding="utf-8"), "existing packet body\n")
            self.assertFalse(existing.with_suffix(".json").exists())

    @unittest.skipUnless(os.name == "posix", "descriptor-relative race test requires POSIX")
    def test_atomic_expected_absent_write_never_clobbers_concurrent_winner(self) -> None:
        from speckit_pro_runner.helpers import mutation

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "packet.json"
            original_link = mutation.os.link

            def install_competitor(
                source: str,
                destination: str,
                *,
                src_dir_fd: int | None = None,
                dst_dir_fd: int | None = None,
                follow_symlinks: bool = True,
            ) -> None:
                target.write_text("concurrent winner\n", encoding="utf-8")
                original_link(
                    source,
                    destination,
                    src_dir_fd=src_dir_fd,
                    dst_dir_fd=dst_dir_fd,
                    follow_symlinks=follow_symlinks,
                )

            with patch.object(mutation.os, "link", side_effect=install_competitor):
                with self.assertRaises(FileExistsError):
                    mutation.write_file_atomic(
                        target,
                        "generated packet\n",
                        trust_root=root,
                        expected_absent=True,
                    )
            self.assertEqual(target.read_text(encoding="utf-8"), "concurrent winner\n")

    @unittest.skipUnless(os.name == "posix", "descriptor-relative durability test requires POSIX")
    def test_committed_write_is_reported_when_directory_fsync_fails(self) -> None:
        from speckit_pro_runner.helpers import mutation
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            target = git_root / "generated" / "packet.json"
            operation = {
                "operation_id": "committed-before-fsync",
                "kind": "write_file",
                "target": "generated/packet.json",
                "content": "{}\n",
                "expected_absent": True,
            }
            request = SimpleNamespace(
                request_id="test-committed-before-fsync",
                helper_id="mutation-foundation",
                operation="mutation-foundation",
                mode="apply",
                inputs={},
            )
            real_fsync = mutation.os.fsync
            fsync_calls = 0

            def fail_directory_fsync(fd: int) -> None:
                nonlocal fsync_calls
                fsync_calls += 1
                if fsync_calls == 2:
                    raise OSError("injected directory fsync failure")
                real_fsync(fd)

            with (
                patch.object(mutation, "find_repo_root", return_value=git_root),
                patch.object(mutation.os, "fsync", side_effect=fail_directory_fsync),
            ):
                response = mutation.run_mutation_helper(
                    MUTATION_HELPERS["mutation-foundation"],
                    request,
                    operations=[operation],
                )

            self.assert_response(response, "expected_failure", 1)
            self.assertTrue(target.is_file())
            result = response["data"]["mutation"]
            self.assertEqual(result["mutation_status"], "partial_failure")
            self.assertEqual(result["applied_operations"][0]["operation_id"], operation["operation_id"])
            self.assertEqual(result["touched_paths"], [operation["target"]])
            self.assertTrue(response["diagnostics"][0]["details"]["write_committed"])

    def test_apply_reports_secure_write_prerequisite_before_mutation(self) -> None:
        from speckit_pro_runner.helpers import mutation
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            request = SimpleNamespace(
                request_id="test-secure-write-prerequisite",
                helper_id="mutation-foundation",
                operation="mutation-foundation",
                mode="apply",
                inputs={},
            )
            with (
                patch.object(mutation, "find_repo_root", return_value=git_root),
                patch.object(mutation, "SECURE_DIR_FD_WRITES", False),
            ):
                response = mutation.run_mutation_helper(
                    MUTATION_HELPERS["mutation-foundation"],
                    request,
                    operations=[
                        {
                            "operation_id": "blocked-write",
                            "kind": "write_file",
                            "target": "generated/blocked.md",
                            "content": "blocked\n",
                        }
                    ],
                )

            self.assert_response(response, "missing_prerequisite", 3)
            self.assertEqual(response["diagnostics"][0]["code"], "secure_atomic_writes_unavailable")
            self.assertFalse((git_root / "generated" / "blocked.md").exists())

    def test_packet_git_context_uses_captured_revisions_and_rejects_non_utf8_paths(self) -> None:
        from speckit_pro_runner.helpers import pr_emission

        branch = b"packet-feature\n"
        base_sha = b"a" * 40 + b"\n"
        head_sha = b"b" * 40 + b"\n"

        def completed(stdout: bytes) -> subprocess.CompletedProcess[bytes]:
            return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr=b"")

        stable_results = [
            completed(branch),
            completed(base_sha),
            completed(head_sha),
            completed(b"candidate.json\0"),
            completed(b"binary diff"),
            completed(b"chore: authorize packet\n"),
            completed(branch),
            completed(base_sha),
            completed(head_sha),
        ]
        with patch.object(pr_emission.subprocess, "run", side_effect=stable_results) as mocked_run:
            context, error = pr_emission._git_packet_context(Path("/repo"), "refs/heads/main")
        self.assertIsNone(error)
        self.assertEqual(context["changed_files"], ["candidate.json"])
        expected_range = f"{'a' * 40}...{'b' * 40}"
        self.assertIn(expected_range, mocked_run.call_args_list[3].args[0])
        self.assertIn(expected_range, mocked_run.call_args_list[4].args[0])

        invalid_path_results = [
            completed(branch),
            completed(base_sha),
            completed(head_sha),
            completed(b"invalid-\xff.json\0"),
            completed(b"binary diff"),
            completed(b"chore: authorize packet\n"),
            completed(branch),
            completed(base_sha),
            completed(head_sha),
        ]
        with patch.object(pr_emission.subprocess, "run", side_effect=invalid_path_results):
            context, error = pr_emission._git_packet_context(Path("/repo"), "refs/heads/main")
        self.assertIsNone(context)
        self.assertEqual(error, "unsupported_git_path_encoding")

    @unittest.skipUnless(os.name == "posix", "descriptor-relative race test requires POSIX")
    def test_atomic_mutation_write_blocks_parent_swap_before_temporary_write(self) -> None:
        from speckit_pro_runner.helpers import mutation

        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "root"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            target = root / "generated" / "packet.json"
            original_mkdir = os.mkdir

            def swap_parent(path: str, mode: int = 0o777, *, dir_fd: int | None = None) -> None:
                original_mkdir(path, mode, dir_fd=dir_fd)
                generated = root / "generated"
                generated.rename(root / "displaced")
                generated.symlink_to(outside, target_is_directory=True)

            with patch.object(mutation.os, "mkdir", side_effect=swap_parent):
                with self.assertRaises(OSError):
                    mutation.write_file_atomic(target, "{}\n", trust_root=root)
            self.assertFalse(target.exists())
            self.assertEqual(list(outside.iterdir()), [])
            self.assertEqual(list((root / "displaced").iterdir()), [])

    def test_contract_schemas_match_runner_fixture_envelopes(self) -> None:
        request_schema = json.loads(REQUEST_SCHEMA.read_text(encoding="utf-8"))
        result_schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            request_schema["required"],
            ["schema_version", "helper_id", "operation", "mode", "inputs"],
        )
        self.assertNotIn("boundary_context", request_schema["properties"])
        self.assertNotIn("approval_evidence", request_schema["properties"])
        self.assertEqual(
            set(request_schema["properties"]["mode"]["enum"]),
            {"read_only", "dry_run", "apply"},
        )

        allowed_request_fields = set(request_schema["properties"])
        for fixture_path in sorted((FIXTURE_DIR / "requests").glob("*.json")):
            request = json.loads(fixture_path.read_text(encoding="utf-8"))
            self.assertFalse(set(request) - allowed_request_fields, fixture_path.name)
            for required in request_schema["required"]:
                self.assertIn(required, request, fixture_path.name)
            self.assertIn(request["mode"], request_schema["properties"]["mode"]["enum"])
            completed, response, stderr_records = run_runner(request)
            self.assertEqual(completed.returncode, response["exit_code"])
            self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])
            self.assert_schema_contract_response(response, result_schema)

    def test_fixture_manifests_cover_mutation_helpers(self) -> None:
        fixture_manifest = json.loads((FIXTURE_DIR / "fixture-manifest.json").read_text(encoding="utf-8"))
        promotion_records = json.loads((FIXTURE_DIR / "promotion-records.json").read_text(encoding="utf-8"))
        promotion_schema = json.loads(PROMOTION_SCHEMA.read_text(encoding="utf-8"))
        promotion_fields = set(promotion_schema["properties"])
        self.assertGreaterEqual(len(fixture_manifest["helpers"]), 6)
        self.assertGreaterEqual(len(promotion_records["helpers"]), 6)
        for record in fixture_manifest["helpers"]:
            self.assertIn("helper_id", record)
            self.assertIn("modes", record)
            self.assertIn("failure_classes", record)
            self.assertIn("authoritative_command", record)
            fixture_path = command_stdin_fixture(record["authoritative_command"])
            self.assertTrue(fixture_path.is_file(), record["authoritative_command"])
            request = json.loads(fixture_path.read_text(encoding="utf-8"))
            self.assertEqual(request["helper_id"], record["helper_id"])
            self.assertEqual(request["operation"], record["operation"])
            self.assertIn(request["mode"], record["modes"])
            completed, response, stderr_records = run_runner(request)
            self.assertEqual(completed.returncode, response["exit_code"])
            self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])
        for record in promotion_records["helpers"]:
            self.assertFalse(set(record) - promotion_fields, record["helper_id"])
            for required in promotion_schema["required"]:
                self.assertIn(required, record)
            self.assertIn(record["promotion_status"], {"golden_only", "bash_compared", "deferred", "out_of_scope"})
            self.assertIn("rollback", record)
            self.assertNotIn(".sh", record["rollback"])
            self.assertNotIn("scripts authoritative", record["rollback"].lower())


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MutationHelperTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"test-speckit-pro-mutation-helpers: {passed}/{total} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
