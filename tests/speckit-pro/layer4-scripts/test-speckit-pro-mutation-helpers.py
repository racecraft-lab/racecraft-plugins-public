#!/usr/bin/env python3
"""Stdlib-only tests for XPLAT-006 mutation-capable runner helpers."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "mutation-helpers"
SPEC_DIR = REPO_ROOT / "specs" / "xplat-006-mutation-install-pr-emission-helper-port"
REQUEST_SCHEMA = SPEC_DIR / "contracts" / "mutation-helper-request.schema.json"
RESULT_SCHEMA = SPEC_DIR / "contracts" / "mutation-helper-result.schema.json"
PROMOTION_SCHEMA = SPEC_DIR / "contracts" / "helper-promotion-record.schema.json"

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
) -> tuple[subprocess.CompletedProcess[str], dict[str, object], list[dict[str, object]]]:
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(request) if not isinstance(request, str) else request,
        text=True,
        capture_output=True,
        cwd=cwd,
        env=runner_env(),
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
            self.assertNotEqual(record["promotion_status"], "python_authoritative")
            if record["promotion_status"] in {"deferred", "out_of_scope"}:
                self.assertEqual(record["authoritative_command"], "")
            else:
                self.assertTrue(command_stdin_fixture(record["authoritative_command"]).is_file())
            promotion = record["promotion"]
            for required in promotion_schema["required"]:
                self.assertIn(required, promotion)
            self.assertEqual(promotion["helper_id"], record["helper_id"])
            self.assertIn(promotion["promotion_status"], promotion_schema["properties"]["promotion_status"]["enum"])

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
            install_root = git_root / "tests" / "speckit-pro" / "layer4-scripts" / "fixtures" / "fake-home"
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
            install_root = git_root / "tests" / "speckit-pro" / "layer4-scripts" / "fixtures" / "fake-home"
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
            install_root = git_root / "tests" / "speckit-pro" / "layer4-scripts" / "fixtures" / "fake-home"
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
            self.assertFalse((git_root / "tests" / "speckit-pro" / "layer4-scripts" / "fixtures" / "escaped.md").exists())

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
            self.assertEqual([diag["code"] for diag in stderr_records], ["deferred_live_mutation"])
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "blocked")
            self.assertEqual(mutation["applied_operations"], [])
            self.assertFalse(mutation["live_mutation"])

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
            self.assertIn(record["promotion_status"], {"golden_only", "bash_compared", "deferred", "out_of_scope"})
            self.assertIn("rollback", record)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MutationHelperTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"test-speckit-pro-mutation-helpers: {passed}/{total} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
